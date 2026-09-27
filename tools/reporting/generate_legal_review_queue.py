#!/usr/bin/env python3
"""
Legal/manual review queue.

reports/COVERAGE_REPORT.json already counts legal requirements with
NO_TECHNICAL_COVERAGE (currently 32 of 64) -- but as a single number,
not a queue anyone can work through. UI_POSITIONING.md section 7.D
("Review Queue") specifically calls out this category: lawful basis,
consent validity, DPIA sufficiency, DPO applicability, cross-border
transfer, breach legal-notification, and similar areas that are
inherently not Wazuh-testable and need a human/legal reviewer.

This script:
  1. Classifies each NO_TECHNICAL_COVERAGE legal requirement into a
     review category, from its actor/requirement_summary text.
  2. Merges the result into framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml,
     a hand-maintained worksheet: adds newly-appearing requirement_ids
     with status NOT_REVIEWED, and NEVER overwrites an existing entry
     -- a reviewer's status/reviewer/notes for an item already in the
     file are never touched by re-running this script. An item that
     later gains technical coverage is left in the file (marked
     stale=true in the generated report) rather than silently deleted,
     so review history is never lost.
  3. Writes reports/LEGAL_REVIEW_QUEUE.md, grouped by category, showing
     current status from the worksheet.

This is engineering traceability tooling, not a legal opinion: it
identifies WHICH requirements need a human/legal reviewer and tracks
WHETHER they have been looked at, not what the correct legal answer is.
"""
from pathlib import Path
import yaml
import json
import collections


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
STATUS_PATH = ROOT / "framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml"
OUT_MD = ROOT / "reports/LEGAL_REVIEW_QUEUE.md"

legal = yaml.safe_load((ROOT / "framework/legal/LEGAL_MAPPING.yml").read_text(encoding="utf-8"))
controls = yaml.safe_load((ROOT / "framework/controls/CONTROL_CATALOGUE.yml").read_text(encoding="utf-8"))
reqs = yaml.safe_load((ROOT / "framework/requirements/CONTROL_REQUIREMENTS.yml").read_text(encoding="utf-8"))
tests = yaml.safe_load((ROOT / "implementations/wazuh/WAZUH_TEST_CATALOGUE.yml").read_text(encoding="utf-8"))

legal_by_id = {x["id"]: x for x in legal["requirements"]}

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


# Category classification, in priority order (first match wins).
# Keyword lists are Indonesian, matching framework/legal/LEGAL_MAPPING.yml's
# requirement_summary text (the framework's own bahasa).
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


queue_items = []
for lr in legal["requirements"]:
    if technical_coverage(lr) != "NO_TECHNICAL_COVERAGE":
        continue
    queue_items.append({
        "legal_requirement_id": lr["id"],
        "article": lr["legal_source"].get("article"),
        "paragraph": lr["legal_source"].get("paragraph"),
        "actor": lr.get("actor"),
        "requirement_summary": lr.get("requirement_summary"),
        "category": classify(lr),
    })

# --- merge into the hand-maintained status worksheet, never overwriting
# an existing reviewer's entry ---
if STATUS_PATH.exists():
    status_doc = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8")) or {}
else:
    status_doc = {}

items_status = status_doc.setdefault("items", {})
current_ids = {item["legal_requirement_id"] for item in queue_items}

added = []
for item in queue_items:
    lrid = item["legal_requirement_id"]
    if lrid not in items_status:
        items_status[lrid] = {
            "status": "NOT_REVIEWED",
            "reviewer": None,
            "reviewed_at": None,
            "notes": None,
        }
        added.append(lrid)

# Never delete an entry whose requirement later gained coverage --
# review history for it stays, just marked stale in the generated report.
stale_ids = sorted(set(items_status.keys()) - current_ids)

status_doc["metadata"] = {
    "description": (
        "Hand-maintained legal/manual review worksheet for legal requirements "
        "with NO_TECHNICAL_COVERAGE (see reports/LEGAL_REVIEW_QUEUE.md). "
        "Edit status/reviewer/reviewed_at/notes per item; "
        "tools/reporting/generate_legal_review_queue.py only ever adds new "
        "items here, never overwrites or deletes an existing one."
    ),
    "valid_status_values": ["NOT_REVIEWED", "IN_PROGRESS", "REVIEWED"],
}

STATUS_PATH.write_text(
    yaml.safe_dump(status_doc, sort_keys=False, allow_unicode=True, default_flow_style=False),
    encoding="utf-8",
)

if added:
    print(f"Added {len(added)} new item(s) to {STATUS_PATH.relative_to(ROOT)}: {added}")
if stale_ids:
    print(f"{len(stale_ids)} item(s) in the worksheet no longer lack technical coverage "
          f"(kept, marked stale): {stale_ids}")

# --- report ---
by_category = collections.defaultdict(list)
for item in queue_items:
    by_category[item["category"]].append(item)

lines = []
lines.append("# Legal / Manual Review Queue")
lines.append("")
lines.append(
    "> Engineering traceability tooling: identifies which legal requirements "
    "have no Wazuh technical coverage and therefore need a human/legal "
    "reviewer, and tracks whether each has been looked at. It does not "
    "determine the correct legal answer for any item -- see "
    "`implementations/wazuh/dashboard/UI_POSITIONING.md` section 7.D."
)
lines.append("")
lines.append(f"**{len(queue_items)}** legal requirements currently need manual/legal review "
             f"(of 64 total; see `reports/COVERAGE_REPORT.md` for the full traceability picture).")
lines.append("")
lines.append("Status is tracked in `framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml` -- "
              "edit that file directly to record review progress; re-running the "
              "generator never overwrites it.")
lines.append("")

status_counts = collections.Counter(
    items_status.get(item["legal_requirement_id"], {}).get("status", "NOT_REVIEWED")
    for item in queue_items
)
lines.append("## Summary")
lines.append("")
lines.append(f"- NOT_REVIEWED: **{status_counts['NOT_REVIEWED']}**")
lines.append(f"- IN_PROGRESS: **{status_counts['IN_PROGRESS']}**")
lines.append(f"- REVIEWED: **{status_counts['REVIEWED']}**")
lines.append("")

for category in [c for c, _ in CATEGORIES] + ["Other legal/manual review"]:
    items = by_category.get(category)
    if not items:
        continue
    lines.append(f"## {category} ({len(items)})")
    lines.append("")
    lines.append("| LR | Article | Actor | Summary | Status |")
    lines.append("|---|---:|---|---|---|")
    for item in sorted(items, key=lambda x: x["legal_requirement_id"]):
        article = str(item["article"])
        if item["paragraph"] is not None:
            article += f"({item['paragraph']})"
        st = items_status.get(item["legal_requirement_id"], {}).get("status", "NOT_REVIEWED")
        lines.append(
            f"| {item['legal_requirement_id']} | {article} | {item['actor']} | "
            f"{item['requirement_summary']} | {st} |"
        )
    lines.append("")

if stale_ids:
    lines.append("## Stale entries (now have technical coverage, kept for history)")
    lines.append("")
    for lrid in stale_ids:
        lines.append(f"- {lrid}: {items_status[lrid].get('status')}")
    lines.append("")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT_MD.relative_to(ROOT)} ({len(queue_items)} items)")
