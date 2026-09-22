#!/usr/bin/env python3
from pathlib import Path
import yaml, json, collections

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)

legal = yaml.safe_load((ROOT/"framework/legal/LEGAL_MAPPING.yml").read_text(encoding="utf-8"))
controls = yaml.safe_load((ROOT/"framework/controls/CONTROL_CATALOGUE.yml").read_text(encoding="utf-8"))
reqs = yaml.safe_load((ROOT/"framework/requirements/CONTROL_REQUIREMENTS.yml").read_text(encoding="utf-8"))
tests = yaml.safe_load((ROOT/"implementations/wazuh/WAZUH_TEST_CATALOGUE.yml").read_text(encoding="utf-8"))

legal_by_id={x["id"]:x for x in legal["requirements"]}
control_by_id={x["id"]:x for x in controls["controls"]}
req_by_id={x["id"]:x for x in reqs["requirements"]}

control_to_reqs=collections.defaultdict(set)
for r in reqs["requirements"]:
    for c in r.get("supports_controls",[]):
        control_to_reqs[c].add(r["id"])

req_to_tests=collections.defaultdict(set)
control_to_tests=collections.defaultdict(set)
for t in tests["tests"]:
    for r in t.get("requirements",[]):
        req_to_tests[r].add(t["id"])
    for c in t.get("controls",[]):
        control_to_tests[c].add(t["id"])

rows=[]
for lr in legal["requirements"]:
    mapped_controls=lr.get("mapped_controls",[])
    mapped_reqs=sorted({r for c in mapped_controls for r in control_to_reqs.get(c,set())})
    mapped_tests=sorted({t for c in mapped_controls for t in control_to_tests.get(c,set())} |
                        {t for r in mapped_reqs for t in req_to_tests.get(r,set())})

    if mapped_tests:
        technical_coverage="TECHNICAL_TEST_COVERAGE"
    elif mapped_reqs:
        technical_coverage="REQUIREMENT_ONLY"
    else:
        technical_coverage="NO_TECHNICAL_COVERAGE"

    rows.append({
        "legal_requirement_id":lr["id"],
        "article":lr["legal_source"].get("article"),
        "paragraph":lr["legal_source"].get("paragraph"),
        "topic":lr.get("topic"),
        "controls":mapped_controls,
        "generic_requirements":mapped_reqs,
        "wazuh_tests":mapped_tests,
        "technical_coverage":technical_coverage
    })

summary=collections.Counter(x["technical_coverage"] for x in rows)
report={
    "framework_version":"0.10.0-rc1",
    "summary":{
        "legal_requirements_total":len(rows),
        "with_wazuh_test_coverage":summary["TECHNICAL_TEST_COVERAGE"],
        "with_generic_requirement_only":summary["REQUIREMENT_ONLY"],
        "without_technical_coverage":summary["NO_TECHNICAL_COVERAGE"]
    },
    "rows":rows
}

out_json=ROOT/"reports/COVERAGE_REPORT.json"
out_json.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")

lines=[]
lines.append("# Coverage Report")
lines.append("")
lines.append("**Framework version:** 0.10.0-rc1")
lines.append("")
lines.append("> This report measures engineering traceability/technical test coverage. It is not a legal compliance score.")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append(f"- Legal requirements: **{len(rows)}**")
lines.append(f"- With Wazuh test coverage: **{summary['TECHNICAL_TEST_COVERAGE']}**")
lines.append(f"- Generic requirement only: **{summary['REQUIREMENT_ONLY']}**")
lines.append(f"- No technical coverage: **{summary['NO_TECHNICAL_COVERAGE']}**")
lines.append("")
lines.append("| LR | Article | Topic | Controls | REQ | Wazuh tests | Coverage |")
lines.append("|---|---:|---|---|---:|---:|---|")
for x in rows:
    article=str(x["article"])
    if x["paragraph"] is not None:
        article += f"({x['paragraph']})"
    lines.append(
        f"| {x['legal_requirement_id']} | {article} | {x['topic']} | "
        f"{', '.join(x['controls']) or '-'} | {len(x['generic_requirements'])} | "
        f"{len(x['wazuh_tests'])} | {x['technical_coverage']} |"
    )
(ROOT/"reports/COVERAGE_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

print(json.dumps(report["summary"],indent=2))
