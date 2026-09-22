#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, uuid

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
EVID=ROOT/"implementations"/"wazuh"/"tests"/"results"
OUT=ROOT/"runtime"/"registry"
OUT.mkdir(parents=True,exist_ok=True)

def now():
    return datetime.now(timezone.utc)

items=[]
for p in EVID.glob("*.evidence.json"):
    raw=p.read_bytes()
    ev=json.loads(raw)
    ts=now()
    reg={
        "schema_version":"0.9",
        "registry_id":"REG-"+str(uuid.uuid4()),
        "evidence_id":ev["evidence_id"],
        "index":"pdp-evidence-"+ts.strftime("%Y.%m"),
        "document_id":ev["evidence_id"],
        "state":"ACTIVE",
        "registered_at":ts.isoformat().replace("+00:00","Z"),
        "retention_until":(ts+timedelta(days=365)).isoformat().replace("+00:00","Z"),
        "integrity_hash":"sha256:"+hashlib.sha256(raw).hexdigest(),
        "source_ref":ev["source"].get("source_ref"),
        "processing_activity_ids":ev["scope"]["processing_activity_ids"],
        "asset_ids":ev["scope"]["asset_ids"],
        "control_ids":ev["traceability"]["controls"],
        "legal_requirement_ids":ev["traceability"]["legal_requirements"]
    }
    (OUT/f"{reg['registry_id']}.registry.json").write_text(json.dumps(reg,indent=2),encoding="utf-8")
    items.append(reg)

(OUT/"SUMMARY.json").write_text(json.dumps(items,indent=2),encoding="utf-8")
print(json.dumps(items,indent=2))
