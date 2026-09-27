#!/usr/bin/env python3
"""
Update one item in the Legal/Manual Review Queue worksheet
(framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml) without
hand-editing YAML, then regenerate reports/LEGAL_REVIEW_QUEUE.md so the
change is immediately visible.

This does not touch the dashboard's indexed copy (PDP-DASH-009) --
after using this, re-run tools/export/export_legal_review_ndjson.py
and bulk-index it (see implementations/wazuh/DEPLOYMENT.md section 7)
to push the update there too.

Examples:
  python3 tools/legal_review/mark_reviewed.py --id LR-020-01 \\
      --status IN_PROGRESS --reviewer "Jane Doe"

  python3 tools/legal_review/mark_reviewed.py --id LR-020-01 \\
      --status REVIEWED --reviewer "Jane Doe" \\
      --notes "Lawful basis documented in DPA section 3.2; consent flow reviewed."
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, subprocess, sys, yaml


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
STATUS_PATH = ROOT / "framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml"
VALID_STATUSES = ["NOT_REVIEWED", "IN_PROGRESS", "REVIEWED"]

parser = argparse.ArgumentParser()
parser.add_argument("--id", required=True, help="Legal requirement ID, e.g. LR-020-01")
parser.add_argument("--status", choices=VALID_STATUSES, required=True)
parser.add_argument("--reviewer", default=None)
parser.add_argument("--notes", default=None)
args = parser.parse_args()

if not STATUS_PATH.exists():
    print(f"{STATUS_PATH} does not exist yet -- run "
          f"tools/reporting/generate_legal_review_queue.py first.", file=sys.stderr)
    sys.exit(2)

status_doc = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8")) or {}
items = status_doc.setdefault("items", {})

if args.id not in items:
    print(f"'{args.id}' is not in the worksheet. Either it's not a legal requirement "
          f"with NO_TECHNICAL_COVERAGE, or the worksheet is stale -- run "
          f"tools/reporting/generate_legal_review_queue.py first.", file=sys.stderr)
    sys.exit(2)

entry = items[args.id]
entry["status"] = args.status
if args.reviewer is not None:
    entry["reviewer"] = args.reviewer
if args.notes is not None:
    entry["notes"] = args.notes
if args.status in ("IN_PROGRESS", "REVIEWED"):
    entry["reviewed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

STATUS_PATH.write_text(
    yaml.safe_dump(status_doc, sort_keys=False, allow_unicode=True, default_flow_style=False),
    encoding="utf-8",
)
print(f"Updated {args.id}: status={entry['status']}, reviewer={entry.get('reviewer')}")

result = subprocess.run(
    [sys.executable, str(ROOT / "tools/reporting/generate_legal_review_queue.py")],
    cwd=ROOT, capture_output=True, text=True,
)
print(result.stdout, end="")
if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

print("\nDashboard note: this only updated the worksheet/report. To push this status "
      "to PDP-DASH-009 on the real dashboard, also run "
      "tools/export/export_legal_review_ndjson.py and bulk-index the result -- see "
      "implementations/wazuh/DEPLOYMENT.md section 7.")
