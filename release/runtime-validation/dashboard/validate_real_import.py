#!/usr/bin/env python3
"""
Real indexer + dashboard import validation.

Environment:
  PDP_INDEXER_URL=https://127.0.0.1:9200
  PDP_INDEXER_USER=admin
  PDP_INDEXER_PASSWORD=...
  PDP_DASHBOARD_URL=https://127.0.0.1:443
  PDP_DASHBOARD_USER=admin
  PDP_DASHBOARD_PASSWORD=...
  PDP_VERIFY_TLS=false
  PDP_SECURITY_TENANT=global

This script performs actual API calls and writes RESULT.json.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, os, sys, requests, uuid

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
OUT=ROOT/"release/runtime-validation/dashboard/RESULT.json"
IDX=ROOT/"implementations/wazuh/indexer/templates"
NDJSON=ROOT/"implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson"

INDEXER=os.getenv("PDP_INDEXER_URL","https://127.0.0.1:9200").rstrip("/")
IUSER=os.getenv("PDP_INDEXER_USER")
IPASS=os.getenv("PDP_INDEXER_PASSWORD")
DASH=os.getenv("PDP_DASHBOARD_URL","https://127.0.0.1").rstrip("/")
DUSER=os.getenv("PDP_DASHBOARD_USER")
DPASS=os.getenv("PDP_DASHBOARD_PASSWORD")
VERIFY=os.getenv("PDP_VERIFY_TLS","false").lower()=="true"
TENANT=os.getenv("PDP_SECURITY_TENANT","global")

required=[IUSER,IPASS,DUSER,DPASS]
if not all(required):
    print("Missing indexer/dashboard credentials in environment",file=sys.stderr)
    sys.exit(2)

if not VERIFY:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

r={
    "framework_version":"0.10.0-rc2",
    "run_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    "checks":[],
    "overall":"FAIL"
}

def check(name, ok, detail=None):
    r["checks"].append({"check":name,"status":"PASS" if ok else "FAIL","detail":detail})
    return ok

isess=requests.Session()
isess.verify=VERIFY
isess.auth=(IUSER,IPASS)

dsess=requests.Session()
dsess.verify=VERIFY
dsess.auth=(DUSER,DPASS)
dheaders={"osd-xsrf":"true","securitytenant":TENANT}

# 1. Indexer reachable
resp=isess.get(INDEXER+"/",timeout=20)
check("indexer_reachable",resp.ok,resp.text[:1000])

# 2. Install templates
for f in sorted(IDX.glob("pdp-*-template.json")):
    name=f.stem
    doc=json.loads(f.read_text(encoding="utf-8"))
    rr=isess.put(f"{INDEXER}/_index_template/{name}",json=doc,timeout=20)
    check("template:"+name,rr.ok,rr.text[:1000])

suffix=uuid.uuid4().hex[:8]
indices={
    "pdp-evidence":f"pdp-evidence-validation-{suffix}",
    "pdp-assessment":f"pdp-assessment-validation-{suffix}",
    "pdp-findings":f"pdp-findings-validation-{suffix}"
}
created=[]

# 3. Create temporary indices, verifying templates are accepted
for kind,index in indices.items():
    rr=isess.put(f"{INDEXER}/{index}",timeout=20)
    ok=rr.ok
    check("create_index:"+index,ok,rr.text[:1000])
    if ok: created.append(index)

# 4. Dashboard saved-object import
files={"file":("pdp-dashboard-shell.ndjson",NDJSON.read_bytes(),"application/ndjson")}
rr=dsess.post(
    DASH+"/api/saved_objects/_import?overwrite=true",
    headers=dheaders,files=files,timeout=30
)
try:
    data=rr.json()
except Exception:
    data={"raw":rr.text}
import_ok=rr.ok and bool(data.get("success"))
check("saved_objects_import",import_ok,data)

# 5. Verify objects can be found
for typ,title in [
    ("index-pattern","pdp-evidence-*"),
    ("index-pattern","pdp-assessment-*"),
    ("index-pattern","pdp-findings-*"),
    ("dashboard","PDP Continuous Control Dashboard")
]:
    rr=dsess.get(
        DASH+"/api/saved_objects/_find",
        headers={"securitytenant":TENANT},
        params={"type":typ,"search":title,"search_fields":"title"},
        timeout=20
    )
    try: data=rr.json()
    except Exception: data={"raw":rr.text}
    found=rr.ok and data.get("total",0)>=1
    check("saved_object_find:"+typ+":"+title,found,data)

# 6. Cleanup validation indices
for index in created:
    rr=isess.delete(f"{INDEXER}/{index}",timeout=20)
    check("cleanup_index:"+index,rr.ok,rr.text[:1000])

r["overall"]="PASS" if all(x["status"]=="PASS" for x in r["checks"]) else "FAIL"
OUT.write_text(json.dumps(r,indent=2),encoding="utf-8")
print(json.dumps(r,indent=2))
sys.exit(0 if r["overall"]=="PASS" else 1)
