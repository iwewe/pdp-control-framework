#!/usr/bin/env python3
"""
Harvest real evidence from Wazuh SCA alerts already indexed in
wazuh-alerts-* (the Wazuh Indexer's own alert index, not this
framework's pdp-* indices), and write it as normalized
evidence.schema.json-conformant documents to
implementations/wazuh/tests/results/*.evidence.json -- the same
location tools/assessment/assess_controls.py and
tools/evidence/register_evidence.py already read from.

Scope of this pass: SCA checks only (data.sca.type: "check" AND
data.sca.check.compliance.pdp_test exists -- i.e. this framework's own
checks, identified by carrying a pdp_test compliance tag, not Wazuh's
bundled CIS policies). Custom rule-based evidence (pdp_authentication.xml,
pdp_fim.xml, etc.) is NOT covered here -- those rules encode
traceability as rule *group* tags (pdp_req_*, pdp_control_*), a
different convention than SCA's native `compliance:` block, and need a
separate harvester.

Environment (same convention as release/runtime-validation/dashboard/validate_real_import.py):
  PDP_INDEXER_URL=https://127.0.0.1:9200
  PDP_INDEXER_USER=admin
  PDP_INDEXER_PASSWORD=...
  PDP_VERIFY_TLS=false

Usage:
  python3 tools/evidence/harvest_sca_evidence.py [--since 7d]
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, os, sys, requests, yaml


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
OUT_DIR = ROOT / "implementations" / "wazuh" / "tests" / "results"
MAPPING_PATH = ROOT / "tools" / "assessment" / "WAZUH_EVIDENCE_MAPPING.yml"

parser = argparse.ArgumentParser()
parser.add_argument("--since", default="7d", help="Lookback window, e.g. 7d, 24h (default: 7d)")
args = parser.parse_args()

INDEXER = os.getenv("PDP_INDEXER_URL", "https://127.0.0.1:9200").rstrip("/")
IUSER = os.getenv("PDP_INDEXER_USER")
IPASS = os.getenv("PDP_INDEXER_PASSWORD")
VERIFY = os.getenv("PDP_VERIFY_TLS", "false").lower() == "true"

if not IUSER or not IPASS:
    print("Missing PDP_INDEXER_USER/PDP_INDEXER_PASSWORD in environment", file=sys.stderr)
    sys.exit(2)

if not VERIFY:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mapping = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))["tests"]

sess = requests.Session()
sess.verify = VERIFY
sess.auth = (IUSER, IPASS)

query = {
    "size": 500,
    "query": {
        "bool": {
            "filter": [
                {"term": {"data.sca.type": "check"}},
                {"exists": {"field": "data.sca.check.compliance.pdp_test"}},
                {"range": {"@timestamp": {"gte": f"now-{args.since}"}}},
            ]
        }
    },
    "sort": [{"@timestamp": "asc"}],
}

resp = sess.post(f"{INDEXER}/wazuh-alerts-*/_search", json=query, timeout=30)
resp.raise_for_status()
hits = resp.json()["hits"]["hits"]

if not hits:
    print(f"No matching SCA alerts in the last {args.since}.")
    sys.exit(0)

OUT_DIR.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

RESULT_MAP = {"passed": "PASS", "failed": "FAIL"}

written = []
for h in hits:
    src = h["_source"]
    alert_id = h["_id"]
    agent = src.get("agent", {})
    rule = src.get("rule", {})
    sca = src.get("data", {}).get("sca", {})
    check = sca.get("check", {})

    pdp_test = check.get("compliance", {}).get("pdp_test", "")
    test_id = pdp_test.split(",")[0].strip() if pdp_test else None
    if not test_id:
        continue

    legal_requirements = mapping.get(test_id, {}).get("traceability", {}).get("legal_requirements", [])

    labels = agent.get("labels", {}).get("pdp", {})
    asset_id = labels.get("asset_id")
    pa_id = labels.get("processing_activity_id")
    if not asset_id or not pa_id:
        print(f"Skipping alert {alert_id}: agent {agent.get('id')}/{agent.get('name')} "
              f"is missing pdp.asset_id or pdp.processing_activity_id labels.", file=sys.stderr)
        continue

    check_id = check.get("id")
    result = RESULT_MAP.get(check.get("result"), "REVIEW")

    evidence_id = f"EV-SCA-{agent.get('id')}-{check_id}-{alert_id}"

    doc = {
        "schema_version": "0.8",
        "evidence_id": evidence_id,
        "source": {
            "type": "wazuh_sca",
            "system": "Wazuh",
            "version": None,
            "source_ref": alert_id,
            "collector_health": "HEALTHY",
        },
        "observed_at": src.get("@timestamp") or src.get("timestamp"),
        "collected_at": now,
        "scope": {
            "processing_activity_ids": [pa_id],
            "asset_ids": [asset_id],
            "environment": labels.get("environment"),
            "organization_role": None,
        },
        "test": {
            "id": test_id,
            "engine": "sca",
            "fixture": None,
            "expected_rule_id": int(check_id) if check_id else None,
            "observed_rule_id": int(check_id) if check_id else None,
            "decoder": "sca",
        },
        "result": result,
        "traceability": {
            "requirements": rule.get("pdp_requirement", []),
            "controls": rule.get("pdp_control", []),
            "legal_requirements": legal_requirements,
        },
        "quality": {
            "level": "Q3",
            "freshness": "FRESH",
            "integrity": "UNVERIFIED",
            "coverage_percent": None,
        },
        "review": {
            "state": "UNREVIEWED",
            "reviewer": None,
            "notes": f"Harvested automatically from real Wazuh SCA alert {alert_id} "
                     f"on agent {agent.get('id')}/{agent.get('name')}.",
        },
    }

    out_path = OUT_DIR / f"{evidence_id}.evidence.json"
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    written.append(evidence_id)

print(f"Wrote {len(written)} evidence documents to {OUT_DIR.relative_to(ROOT)}:")
for e in written:
    print(" -", e)
