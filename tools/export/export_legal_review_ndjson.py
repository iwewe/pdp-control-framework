#!/usr/bin/env python3
"""
Create OpenSearch Bulk API NDJSON for the legal/manual review queue
(framework/schemas/legal-review-item.schema.json), from
framework/legal/LEGAL_MAPPING.yml and
framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml.

Unlike tools/export/export_bulk_ndjson.py's evidence/assessment/finding
export, this is a single, non-time-series registry index
(pdp-legal-review, no monthly suffix): each document is upserted in
place by legal_requirement_id (used as the Bulk API _id) as review
status changes, not accumulated over time.

This does not send data anywhere.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, collections, yaml


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
STATUS_PATH = ROOT / "framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml"

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()

legal = yaml.safe_load((ROOT / "framework/legal/LEGAL_MAPPING.yml").read_text(encoding="utf-8"))
controls = yaml.safe_load((ROOT / "framework/controls/CONTROL_CATALOGUE.yml").read_text(encoding="utf-8"))
reqs = yaml.safe_load((ROOT / "framework/requirements/CONTROL_REQUIREMENTS.yml").read_text(encoding="utf-8"))
tests = yaml.safe_load((ROOT / "implementations/wazuh/WAZUH_TEST_CATALOGUE.yml").read_text(encoding="utf-8"))
status_doc = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8")) or {}
items_status = status_doc.get("items", {})

control_to_reqs = collections.defaultdict(set)
for r in reqs["requirements"]:
    for c in r.get("supports_controls", []):
        control_to_reqs[c].add(r["id"])

req_to_tests = collections.defaultdict(set)
control_to_tests = collections.defaultdict(set)
for t in tests["tests"]:
    for r in t.get("requirements", []):
        req_to_tests[r].add(t["id"])
    for c in t.get("controls", []):
        control_to_tests[c].add(t["id"])


def technical_coverage(lr):
    mapped_controls = lr.get("mapped_controls", [])
    mapped_reqs = {r for c in mapped_controls for r in control_to_reqs.get(c, set())}
    mapped_tests = ({t for c in mapped_controls for t in control_to_tests.get(c, set())}
                     | {t for r in mapped_reqs for t in req_to_tests.get(r, set())})
    if mapped_tests:
        return "TECHNICAL_TEST_COVERAGE"
    if mapped_reqs:
        return "REQUIREMENT_ONLY"
    return "NO_TECHNICAL_COVERAGE"


# Keep in sync with tools/reporting/generate_legal_review_queue.py.
CATEGORIES = [
    ("Vulnerable data subjects (children / persons with disabilities)",
     ["anak", "disabilitas"]),
    ("DPIA sufficiency",
     ["penilaian dampak"]),
    ("DPO applicability",
     ["pejabat/petugas", "fungsi pelindungan data pribadi"]),
    ("Cross-border transfer",
     ["transfer", "pengiriman data", "luar negeri", "lintas batas", "negara lain"]),
    ("Breach legal-notification",
     ["pemberitahuan kegagalan", "kebocoran", "insiden keamanan"]),
    ("Data subject rights timelines (access / correction / restriction / withdrawal)",
     ["3 x 24 jam", "akses wajib", "menolak akses", "pembaruan", "penundaan", "pembatasan", "penarikan"]),
    ("Consent validity",
     ["persetujuan"]),
    ("Lawful basis",
     ["dasar pemrosesan", "dasar hukum", "sah secara hukum", "tujuan pemrosesan"]),
]


def classify(lr):
    actor = (lr.get("actor") or "").lower()
    summary = (lr.get("requirement_summary") or "").lower()
    text = actor + " " + summary
    for category, keywords in CATEGORIES:
        if any(k in text for k in keywords):
            return category
    return "Other legal/manual review"


now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
index = "pdp-legal-review"

lines = []
count = 0
for lr in legal["requirements"]:
    if technical_coverage(lr) != "NO_TECHNICAL_COVERAGE":
        continue
    lrid = lr["id"]
    st = items_status.get(lrid, {"status": "NOT_REVIEWED", "reviewer": None, "reviewed_at": None, "notes": None})
    doc = {
        "@timestamp": st.get("reviewed_at") or now,
        "schema_version": "1.0",
        "legal_requirement_id": lrid,
        "article": lr["legal_source"].get("article"),
        "paragraph": lr["legal_source"].get("paragraph"),
        "actor": lr.get("actor"),
        "requirement_summary": lr.get("requirement_summary"),
        "category": classify(lr),
        "status": st.get("status", "NOT_REVIEWED"),
        "reviewer": st.get("reviewer"),
        "reviewed_at": st.get("reviewed_at"),
        "notes": st.get("notes"),
    }
    meta = {"index": {"_index": index, "_id": lrid}}
    lines.append(json.dumps(meta, separators=(",", ":")))
    lines.append(json.dumps(doc, separators=(",", ":"), ensure_ascii=False))
    count += 1

Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {count} documents to {args.output} (index: {index})")
