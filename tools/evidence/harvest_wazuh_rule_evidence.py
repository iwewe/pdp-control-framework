#!/usr/bin/env python3
"""
Harvest real evidence from custom PDP Wazuh RULE alerts (authentication,
privileged access, FIM, telemetry health, PostgreSQL/pgAudit) already
indexed in wazuh-alerts-*, and write it as normalized
evidence.schema.json-conformant documents to
implementations/wazuh/tests/results/*.evidence.json -- the same
location harvest_sca_evidence.py, assess_controls.py, and
register_evidence.py already use.

Closes the gap harvest_sca_evidence.py's own docstring flagged: custom
rules (implementations/wazuh/rules/*.xml) encode traceability as rule
GROUP tags (pdp_req_<xxx>, pdp_control_<xxx>, pdp_evt_<xxx>), not SCA's
native `compliance:` block, so they needed a separate harvester.

--- Result semantics: alert fired means the DETECTION worked, not FAIL ---
This is the one genuinely non-obvious design decision here. These rules
are tests of monitoring/detection *capability*
(implementations/wazuh/WAZUH_TEST_CATALOGUE.yml's own
result_semantics.pass for e.g. WZ-RUL-AUTH-001 is literally "Repeated
authentication failures trigger a correlated alert"). When the alert
fires, that confirms the expected detection behavior occurred --
that's a PASS for this evidence item, not a FAIL. Whether the
underlying security event itself was routine or actually concerning is
a separate question for a human reviewer/finding, not this evidence
record's result field. So every document harvested here has
result: "PASS". A FAIL would mean "we expected this kind of event and
did NOT get an alert for it" -- not something observable from the
alert stream alone; that needs a different (absence-based) check, not
built here.

--- Deduplication / idempotency ---
Satisfies this without a separate fingerprint/hash step: evidence_id
is built from the alert's own OpenSearch _id (already a globally
unique, stable identifier for that exact event), so re-running this
harvester over the same alerts overwrites the same local files with
identical content rather than creating duplicates -- the same pattern
already used by harvest_sca_evidence.py.

Only rules carrying BOTH a pdp_req_* and a pdp_control_* group tag are
harvested; two real rules (110003 "successful authentication event
available for audit correlation", 110401 the generic pgAudit wrapper
rule) deliberately have no pdp_control_* tag and are skipped by this
filter alone, without needing a special case.

Environment (same convention as harvest_sca_evidence.py):
  PDP_INDEXER_URL=https://127.0.0.1:9200
  PDP_INDEXER_USER=admin
  PDP_INDEXER_PASSWORD=...
  PDP_VERIFY_TLS=false

Usage:
  python3 tools/evidence/harvest_wazuh_rule_evidence.py [--since 7d]
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, os, re, sys, requests, yaml


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
OUT_DIR = ROOT / "implementations" / "wazuh" / "tests" / "results"
MAPPING_PATH = ROOT / "tools" / "assessment" / "WAZUH_EVIDENCE_MAPPING.yml"

# Rule ID -> test ID, hand-verified against implementations/wazuh/rules/*.xml
# group tags and implementations/wazuh/WAZUH_TEST_CATALOGUE.yml titles.
# 110003 and 110401 are deliberately absent -- see module docstring.
RULE_TEST_MAP = {
    110001: "WZ-RUL-AUTH-001",  # authentication failure candidate
    110002: "WZ-RUL-AUTH-001",  # repeated authentication failures (correlation)
    110101: "WZ-RUL-AUTH-002",  # privileged authentication/elevation
    110102: "WZ-RUL-PRIV-001",  # repeated privileged activity
    110201: "WZ-FIM-INT-001",   # integrity event on monitored path
    110202: "WZ-FIM-RET-001",   # deletion on monitored path
    110301: "WZ-HLT-LOG-001",   # telemetry source unavailable/degraded
    110402: "WZ-RUL-PG-001",    # pgAudit ROLE
    110403: "WZ-RUL-PG-002",    # pgAudit DDL
    110404: "WZ-RUL-PG-003",    # pgAudit WRITE
    110405: "WZ-RUL-PG-004",    # pgAudit READ
    110406: "WZ-RUL-PG-005",    # high-frequency reads (exfiltration candidate)
}

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
                {"term": {"rule.groups": "pdp_event"}},
                {"terms": {"rule.id": [str(rid) for rid in RULE_TEST_MAP]}},
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
    print(f"No matching custom-rule alerts in the last {args.since}.")
    sys.exit(0)

OUT_DIR.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

TAG_RE = re.compile(r"^pdp_(req|control|evt)_(.+)$")


def tag_to_id(tag):
    """'pdp_req_mon_001' -> ('req', 'REQ-MON-001'); 'pdp_control_acc_003' ->
    ('control', 'PDP-ACC-003'); 'pdp_evt_int_001' -> ('evt', 'PDP-EVT-INT-001')."""
    m = TAG_RE.match(tag)
    if not m:
        return None
    kind, rest = m.groups()
    formatted = "-".join(rest.upper().split("_"))
    prefix = {"req": "REQ", "control": "PDP", "evt": "PDP-EVT"}[kind]
    return kind, f"{prefix}-{formatted}"


written = []
for h in hits:
    src = h["_source"]
    alert_id = h["_id"]
    agent = src.get("agent", {})
    rule = src.get("rule", {})
    decoder = src.get("decoder", {})

    rule_id = rule.get("id")
    try:
        rule_id_int = int(rule_id)
    except (TypeError, ValueError):
        continue
    test_id = RULE_TEST_MAP.get(rule_id_int)
    if not test_id:
        continue

    requirements, controls, taxonomy_ids = set(), set(), set()
    for tag in rule.get("groups", []):
        parsed = tag_to_id(tag)
        if not parsed:
            continue
        kind, value = parsed
        if kind == "req":
            requirements.add(value)
        elif kind == "control":
            controls.add(value)
        elif kind == "evt":
            taxonomy_ids.add(value)

    if not requirements or not controls:
        # Matches the module docstring's 110003/110401 case: no full
        # req+control tag pair, so nothing to attribute confidently.
        continue

    test_meta = mapping.get(test_id, {})
    legal_requirements = test_meta.get("traceability", {}).get("legal_requirements", [])
    engine = test_meta.get("engine", "log_analysis")
    technical_priority = None
    for ctx in test_meta.get("default_event_context", []):
        if ctx.get("taxonomy_id") in taxonomy_ids:
            technical_priority = ctx.get("technical_priority")
            break

    labels = agent.get("labels", {}).get("pdp", {})
    asset_id = labels.get("asset_id")
    pa_id = labels.get("processing_activity_id")
    if not asset_id or not pa_id:
        print(f"Skipping alert {alert_id}: agent {agent.get('id')}/{agent.get('name')} "
              f"is missing pdp.asset_id or pdp.processing_activity_id labels.", file=sys.stderr)
        continue

    evidence_id = f"EV-RUL-{agent.get('id')}-{rule_id}-{alert_id}"

    doc = {
        "schema_version": "0.8",
        "evidence_id": evidence_id,
        "source": {
            "type": "wazuh_alert",
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
            "engine": engine,
            "fixture": None,
            "expected_rule_id": rule_id_int,
            "observed_rule_id": rule_id_int,
            "decoder": decoder.get("name"),
        },
        # See module docstring: an alert firing confirms the detection
        # capability worked as expected -- that is this test's PASS
        # condition, not a security-event severity judgment.
        "result": "PASS",
        "traceability": {
            "requirements": sorted(requirements),
            "controls": sorted(controls),
            "legal_requirements": legal_requirements,
        },
        "event": {
            "taxonomy_ids": sorted(taxonomy_ids) if taxonomy_ids else [],
            "technical_severity": technical_priority or "UNKNOWN",
            "privacy_impact": "UNKNOWN",
            "confidence": "HIGH",
            "raw_reference": None,
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
            "notes": f"Harvested automatically from real Wazuh rule alert {alert_id} "
                     f"(rule {rule_id}) on agent {agent.get('id')}/{agent.get('name')}.",
        },
    }

    out_path = OUT_DIR / f"{evidence_id}.evidence.json"
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    written.append(evidence_id)

print(f"Wrote {len(written)} evidence documents to {OUT_DIR.relative_to(ROOT)}:")
for e in written:
    print(" -", e)
