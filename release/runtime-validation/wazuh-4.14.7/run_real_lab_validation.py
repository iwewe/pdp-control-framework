#!/usr/bin/env python3
"""
Real Wazuh 4.14.7 runtime validation runner.

Run ON the Wazuh manager after the repository has been copied/cloned there.

This runner:
- verifies manager version via `wazuh-logtest -V`
- validates custom rules/decoder by executing real `wazuh-logtest`
- runs fixture assertions
- writes machine-readable validation evidence

It does not claim success unless the real Wazuh binary returns the expected rule IDs.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, os, re, shutil, subprocess, sys, tempfile, yaml

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
WAZUH = Path(os.getenv("WAZUH_HOME","/var/ossec"))
LOGTEST = WAZUH/"bin/wazuh-logtest"
RESULT = ROOT/"release/runtime-validation/wazuh-4.14.7/RESULT.json"
EXPECTED = ROOT/"implementations/wazuh/tests/expected/EXPECTED_RESULTS.yml"
FIX = ROOT/"implementations/wazuh/tests/fixtures"

TARGET_VERSION="4.14.7"

def run(cmd, input_text=None):
    return subprocess.run(
        cmd, input=input_text, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False
    )

result={
    "framework_version":"1.0.0",
    "target_wazuh_version":TARGET_VERSION,
    "run_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    "checks":[],
    "overall":"FAIL"
}

if not LOGTEST.exists():
    result["checks"].append({"check":"wazuh_logtest_exists","status":"FAIL","detail":str(LOGTEST)})
    RESULT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(2)

ver=run([str(LOGTEST),"-V"])
result["version_output"]=ver.stdout
version_ok=TARGET_VERSION in ver.stdout
result["checks"].append({
    "check":"wazuh_version",
    "status":"PASS" if version_ok else "FAIL",
    "detail":ver.stdout.strip()
})
if not version_ok:
    RESULT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1)

# This runner expects the custom content to already be installed.
# Copying into production paths is deliberately not automatic.
custom_expected=[
    WAZUH/"etc/decoders/pdp_pgaudit.xml",
    WAZUH/"etc/rules/pdp_authentication.xml",
    WAZUH/"etc/rules/pdp_privileged_access.xml",
    WAZUH/"etc/rules/pdp_fim.xml",
    WAZUH/"etc/rules/pdp_telemetry_health.xml",
    WAZUH/"etc/rules/pdp_postgresql.xml",
]
missing=[str(p) for p in custom_expected if not p.exists()]
result["checks"].append({
    "check":"custom_content_installed",
    "status":"PASS" if not missing else "FAIL",
    "missing":missing
})
if missing:
    RESULT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1)

expected=yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
cases=[]
for case in expected["fixtures"]:
    path=FIX/case["file"]
    lines=[x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    proc=run([str(LOGTEST),"-v"], input_text="\n".join(lines)+"\n")
    text=proc.stdout

    # Wazuh verbose output commonly prints id: 'NNNNNN' or id: NNNNN.
    observed=[int(x) for x in re.findall(r"\bid:\s*'?(\d+)'?",text)]
    exp=case.get("expected_rule_id")
    ok=exp in observed if exp is not None else proc.returncode == 0

    cases.append({
        "fixture":case["file"],
        "expected_rule_id":exp,
        "observed_rule_ids":observed,
        "returncode":proc.returncode,
        "status":"PASS" if ok else "FAIL",
        "output_tail":"\n".join(text.splitlines()[-60:])
    })

result["fixture_results"]=cases
all_cases=all(x["status"]=="PASS" for x in cases)
result["checks"].append({
    "check":"fixture_logtest",
    "status":"PASS" if all_cases else "FAIL",
    "passed":sum(x["status"]=="PASS" for x in cases),
    "total":len(cases)
})
result["overall"]="PASS" if all(
    x["status"]=="PASS" for x in result["checks"]
) else "FAIL"

RESULT.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
sys.exit(0 if result["overall"]=="PASS" else 1)
