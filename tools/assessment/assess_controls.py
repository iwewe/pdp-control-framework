#!/usr/bin/env python3
"""
Draft continuous-control assessment aggregator.
Consumes normalized evidence and applies conservative anti-false-compliance logic.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, yaml, uuid, collections

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
RESULTS=ROOT/"implementations"/"wazuh"/"tests"/"results"
OUT=ROOT/"runtime"/"assessments"
OUT.mkdir(parents=True,exist_ok=True)

evidence=[]
for p in RESULTS.glob("*.evidence.json"):
    evidence.append(json.loads(p.read_text(encoding="utf-8")))

by_control=collections.defaultdict(list)
for ev in evidence:
    for ctl in ev["traceability"]["controls"]:
        by_control[ctl].append(ev)

summaries=[]
for control, items in sorted(by_control.items()):
    results=[x["result"] for x in items]
    health=[x["source"]["collector_health"] for x in items]
    ids=[x["evidence_id"] for x in items]

    # Conservative precedence:
    # evidence-source problems prevent PASS;
    # test ERROR/REVIEW cause REVIEW;
    # a FAIL causes FAIL;
    # otherwise all PASS => PASS.
    if any(h != "HEALTHY" for h in health):
        result="REVIEW"
        ev_health="DEGRADED"
    elif "ERROR" in results or "REVIEW" in results:
        result="REVIEW"
        ev_health="INSUFFICIENT"
    elif "FAIL" in results:
        result="FAIL"
        ev_health="SUFFICIENT"
    elif results and all(x=="PASS" for x in results):
        result="PASS"
        ev_health="SUFFICIENT"
    else:
        result="REVIEW"
        ev_health="UNKNOWN"

    passed=results.count("PASS")
    failed=results.count("FAIL")
    error=results.count("ERROR")
    review=results.count("REVIEW")
    pct=(passed/len(results)*100.0) if results else None

    pa=(items[0]["scope"]["processing_activity_ids"][0]
        if items and items[0]["scope"]["processing_activity_ids"] else "UNKNOWN")

    summary={
        "schema_version":"0.8",
        "assessment_id":"ASM-"+str(uuid.uuid4()),
        "control_id":control,
        "scope":{
            "processing_activity_id":pa,
            "asset_ids":sorted({a for e in items for a in e["scope"]["asset_ids"]}),
            "period_start":None,
            "period_end":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        },
        "method":"PARTIAL",
        "result":result,
        "evidence":ids,
        "evidence_health":ev_health,
        "coverage":{
            "required_tests":len(results),
            "passed_tests":passed,
            "failed_tests":failed,
            "error_tests":error,
            "review_tests":review,
            "coverage_percent":pct
        },
        "notes":"Engineering control assessment only; not a legal compliance conclusion."
    }
    summaries.append(summary)
    (OUT/f"{control}.assessment.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

(OUT/"SUMMARY.json").write_text(json.dumps(summaries,indent=2),encoding="utf-8")
print(json.dumps(summaries,indent=2))
