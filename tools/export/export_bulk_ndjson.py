#!/usr/bin/env python3
"""
Create OpenSearch Bulk API NDJSON from normalized framework objects.
This does not send data anywhere.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, argparse

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)

parser=argparse.ArgumentParser()
parser.add_argument("--kind",choices=["evidence","assessment","finding"],required=True)
parser.add_argument("--output",required=True)
args=parser.parse_args()

if args.kind=="evidence":
    src=ROOT/"implementations"/"wazuh"/"tests"/"results"
    files=src.glob("*.evidence.json")
    prefix="pdp-evidence"
    id_field="evidence_id"
elif args.kind=="assessment":
    src=ROOT/"runtime"/"assessments"
    files=src.glob("*.assessment.json")
    prefix="pdp-assessment"
    id_field="assessment_id"
else:
    src=ROOT/"runtime"/"findings"
    files=src.glob("*.finding.json")
    prefix="pdp-findings"
    id_field="finding_id"

now=datetime.now(timezone.utc)
index=f"{prefix}-{now.strftime('%Y.%m')}"

out=Path(args.output)
with out.open("w",encoding="utf-8") as fh:
    count=0
    for p in files:
        doc=json.loads(p.read_text(encoding="utf-8"))
        if args.kind=="evidence":
            ts=doc.get("observed_at")
        elif args.kind=="assessment":
            ts=doc.get("scope",{}).get("period_end")
        else:
            ts=doc.get("updated_at") or doc.get("created_at")
        doc["@timestamp"]=ts or now.isoformat().replace("+00:00","Z")
        meta={"index":{"_index":index,"_id":doc[id_field]}}
        fh.write(json.dumps(meta,separators=(",",":"))+"\n")
        fh.write(json.dumps(doc,separators=(",",":"))+"\n")
        count+=1

print(f"Wrote {count} documents to {out}")
