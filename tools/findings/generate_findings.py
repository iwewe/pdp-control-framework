#!/usr/bin/env python3
"""
Generate findings from control assessments.

Conservative policy:
- FAIL => create/update OPEN finding
- REVIEW => no automatic legal finding; optionally create review queue item later
- PASS => do not auto-close existing findings without explicit remediation/retest workflow
"""
from pathlib import Path
from datetime import datetime, timezone
import json

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
ASSESS=ROOT/"runtime"/"assessments"
OUT=ROOT/"runtime"/"findings"
OUT.mkdir(parents=True,exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

created=[]

for p in ASSESS.glob("*.assessment.json"):
    asm=json.loads(p.read_text(encoding="utf-8"))
    if asm["result"]!="FAIL":
        continue

    # Deterministic (control_id, not a random uuid): at most one open
    # finding per control by design, so a scheduled re-run upserts the
    # same document instead of accumulating a duplicate every cycle --
    # same reasoning as assess_controls.py's assessment_id.
    finding_id="FIND-"+asm["control_id"]
    out=OUT/f"{finding_id}.finding.json"

    if out.exists():
        # Upsert, not overwrite: refresh only what re-running this
        # script can legitimately know changed (evidence/scope/assessment
        # linkage, updated_at). Never touch status/severity/owner/notes --
        # those are human-owned once a finding exists, matching this
        # script's own conservative policy above ("do not auto-close...
        # without explicit remediation/retest workflow"). A human closing
        # a finding must never be silently reopened just because the
        # control still fails on the next scheduled run.
        finding=json.loads(out.read_text(encoding="utf-8"))
        finding["scope"]={
            "processing_activity_id":asm["scope"]["processing_activity_id"],
            "asset_ids":asm["scope"].get("asset_ids",[])
        }
        finding["evidence"]=asm.get("evidence",[])
        finding["assessment_id"]=asm["assessment_id"]
        finding["updated_at"]=now()
    else:
        finding={
            "schema_version":"0.9",
            "finding_id":finding_id,
            "control_id":asm["control_id"],
            "scope":{
                "processing_activity_id":asm["scope"]["processing_activity_id"],
                "asset_ids":asm["scope"].get("asset_ids",[])
            },
            "status":"OPEN",
            "severity":"HIGH",
            "statement":f"Control {asm['control_id']} failed for the assessed scope.",
            "evidence":asm.get("evidence",[]),
            "assessment_id":asm["assessment_id"],
            "remediation_id":None,
            "exception_id":None,
            "created_at":now(),
            "updated_at":None,
            "owner":None,
            "risk_owner":None,
            "legal_review_state":"NOT_REVIEWED",
            "notes":"Engineering finding only; this is not a legal determination of UU PDP non-compliance."
        }

    out.write_text(json.dumps(finding,indent=2),encoding="utf-8")
    created.append(finding)

(OUT/"SUMMARY.json").write_text(json.dumps(created,indent=2),encoding="utf-8")
print(json.dumps(created,indent=2))
