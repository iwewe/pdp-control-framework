#!/usr/bin/env python3
"""
Static fixture validator for PDP Control Framework.

This script does NOT replace wazuh-logtest.
It verifies fixture shape and the project's pgAudit parsing contract so CI can
catch accidental fixture/schema regressions without requiring a Wazuh runtime.
"""
from pathlib import Path
import re, sys, yaml

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
FIX = ROOT / "implementations" / "wazuh" / "tests" / "fixtures"
EXPECTED = ROOT / "implementations" / "wazuh" / "tests" / "expected" / "EXPECTED_RESULTS.yml"

PGAUDIT = re.compile(
    r"AUDIT:\s+(SESSION|OBJECT),([0-9]+),([0-9]+),([A-Z_]+),"
    r"([A-Z ]+),([^,]*),([^,]*),(.*)$"
)

data = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
errors = []

for case in data["fixtures"]:
    path = FIX / case["file"]
    if not path.exists():
        errors.append(f"missing fixture: {case['file']}")
        continue
    lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not lines:
        errors.append(f"empty fixture: {case['file']}")
        continue

    if case["file"].startswith("postgresql/"):
        for n, line in enumerate(lines, 1):
            m = PGAUDIT.search(line)
            if not m:
                errors.append(f"pgAudit fixture parse failure: {case['file']} line {n}")
                continue
            fields = {
                "pdp.audit_type":m.group(1),
                "pdp.statement_id":m.group(2),
                "pdp.substatement_id":m.group(3),
                "pdp.audit_class":m.group(4),
                "pdp.command":m.group(5),
                "pdp.object_type":m.group(6),
                "pdp.object_name":m.group(7),
                "pdp.audit_detail":m.group(8)
            }
            for k,v in case.get("expected_fields",{}).items():
                if fields.get(k) != str(v):
                    errors.append(
                        f"{case['file']}: expected {k}={v!r}, got {fields.get(k)!r}"
                    )

    if case.get("session_required") and len(lines) < 2:
        errors.append(f"correlation fixture must have multiple lines: {case['file']}")

if errors:
    print("FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("OK")
print(f"Validated {len(data['fixtures'])} fixture definitions.")
