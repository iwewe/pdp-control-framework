#!/usr/bin/env python3
"""
PDP Control Framework v0.8 Wazuh logtest harness.

Requires:
  pip install requests pyyaml jsonschema

Environment:
  WAZUH_API_URL=https://127.0.0.1:55000
  WAZUH_API_USER=...
  WAZUH_API_PASSWORD=...
  PDP_ASSET_ID=ASSET-LAB-001
  PDP_PROCESSING_ACTIVITY_ID=PA-LAB-001

The script uses the Wazuh Server API /logtest endpoint because it returns
structured JSON including output.rule, decoder, agent, full_log and session token.
"""
from pathlib import Path
from datetime import datetime, timezone
import os, sys, uuid, json, yaml, requests

def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")

ROOT = find_repo_root(Path(__file__).parent)
FIX = ROOT / "implementations" / "wazuh" / "tests" / "fixtures"
CFG = ROOT / "implementations" / "wazuh" / "tests" / "harness" / "HARNESS.yml"
MAP = ROOT / "assessment" / "WAZUH_EVIDENCE_MAPPING.yml"
OUT = ROOT / "implementations" / "wazuh" / "tests" / "results"

API = os.getenv("WAZUH_API_URL","https://127.0.0.1:55000").rstrip("/")
USER = os.getenv("WAZUH_API_USER")
PASSWORD = os.getenv("WAZUH_API_PASSWORD")
VERIFY = os.getenv("WAZUH_API_VERIFY_TLS","false").lower() == "true"
ASSET = os.getenv("PDP_ASSET_ID","ASSET-LAB-001")
PA = os.getenv("PDP_PROCESSING_ACTIVITY_ID","PA-LAB-001")

if not USER or not PASSWORD:
    print("WAZUH_API_USER and WAZUH_API_PASSWORD are required", file=sys.stderr)
    sys.exit(2)

cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
mapping = yaml.safe_load(MAP.read_text(encoding="utf-8"))["tests"]
OUT.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.verify = VERIFY
if not VERIFY:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = session.post(
    f"{API}/security/user/authenticate?raw=true",
    auth=(USER,PASSWORD),
    timeout=30
)
auth.raise_for_status()
token = auth.text.strip().strip('"')
headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def call_logtest(event, case, session_token=None):
    payload={
        "event":event,
        "log_format":case.get("log_format",cfg["defaults"]["log_format"]),
        "location":case.get("location",cfg["defaults"]["location"])
    }
    if session_token:
        payload["token"]=session_token
    r=session.put(f"{API}/logtest?wait_for_complete=true",headers=headers,json=payload,timeout=60)
    r.raise_for_status()
    return r.json()

all_evidence=[]
summary=[]

for case in cfg["cases"]:
    fixture=FIX / case["fixture"]
    lines=[x for x in fixture.read_text(encoding="utf-8").splitlines() if x.strip()]
    session_token=None
    last=None

    for line in lines:
        response=call_logtest(line,case,session_token)
        data=response.get("data",{})
        if case.get("session_required"):
            session_token=data.get("token",session_token)
        last=response

    output=((last or {}).get("data",{}).get("output") or {})
    rule=output.get("rule") or {}
    observed_rule=rule.get("id")
    try:
        observed_rule=int(observed_rule) if observed_rule is not None else None
    except Exception:
        pass

    expected_rule=case["expected"].get("rule_id")
    result="PASS" if observed_rule == expected_rule else "FAIL"
    if not output:
        result="ERROR"

    tid=case["test_id"]
    m=mapping.get(tid,{"traceability":{"requirements":[],"controls":[],"legal_requirements":[]},"event_categories":[]})
    ev_id="EV-"+str(uuid.uuid4())

    evidence={
        "schema_version":"0.8",
        "evidence_id":ev_id,
        "source":{
            "type":"wazuh_logtest",
            "system":"Wazuh",
            "version":None,
            "source_ref":case["id"],
            "collector_health":"HEALTHY" if output else "DEGRADED"
        },
        "observed_at":output.get("timestamp") or now(),
        "collected_at":now(),
        "scope":{
            "processing_activity_ids":[PA],
            "asset_ids":[ASSET],
            "environment":"lab",
            "organization_role":None
        },
        "test":{
            "id":tid,
            "engine":m.get("engine","log_analysis"),
            "fixture":case["fixture"],
            "expected_rule_id":expected_rule,
            "observed_rule_id":observed_rule,
            "decoder":output.get("decoder")
        },
        "result":result,
        "traceability":m.get("traceability",{"requirements":[],"controls":[],"legal_requirements":[]}),
        "event":{
            "taxonomy_ids":m.get("event_categories",[]),
            "technical_severity":"UNKNOWN",
            "privacy_impact":"UNKNOWN",
            "confidence":"HIGH" if result=="PASS" else "MEDIUM",
            "raw_reference":output.get("id")
        },
        "quality":{
            "level":cfg["defaults"]["evidence_quality"],
            "freshness":"FRESH",
            "integrity":"UNVERIFIED",
            "coverage_percent":100.0
        },
        "payload":{
            "rule_level":rule.get("level"),
            "rule_description":rule.get("description"),
            "rule_groups":rule.get("groups",[]),
            "location":output.get("location"),
            "agent":output.get("agent"),
            "manager":output.get("manager")
        },
        "review":{
            "state":"UNREVIEWED",
            "reviewer":None,
            "notes":"Synthetic lab evidence; no production Personal Data should be present."
        }
    }
    all_evidence.append(evidence)
    summary.append({"case":case["id"],"test_id":tid,"result":result,"expected_rule":expected_rule,"observed_rule":observed_rule})

    (OUT/f"{case['id']}.evidence.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")

    if session_token:
        try:
            session.delete(f"{API}/logtest/sessions/{session_token}",headers=headers,timeout=30)
        except Exception:
            pass

(OUT/"SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

fails=[x for x in summary if x["result"]!="PASS"]
print(json.dumps(summary,indent=2))
sys.exit(1 if fails else 0)
