#!/usr/bin/env bash
# PDP Control Framework -- full harvest-to-index pipeline, safe to run
# unattended on a schedule (see implementations/wazuh/systemd/).
#
# Harvest evidence (SCA + custom-rule alerts) -> aggregate assessments
# -> generate/update findings -> export -> bulk-index. Safe to re-run
# on a schedule: assessment_id/finding_id are deterministic
# (ASM-<control_id> / FIND-<control_id>), so a bulk "index" action
# upserts the same document instead of accumulating a duplicate every
# cycle -- no delete-then-reindex dance needed. Evidence documents are
# likewise deterministic (keyed by the source alert's own unique id),
# so re-harvesting the same alerts is a no-op, not a duplicate.
#
# Requires PDP_INDEXER_URL/USER/PASSWORD in the environment (see
# .env.example) -- source .env before running this manually, or set
# them in the systemd unit's Environment/EnvironmentFile for scheduled
# runs (see implementations/wazuh/systemd/pdp-harvest.service).
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
cd "$ROOT"

for var in PDP_INDEXER_URL PDP_INDEXER_USER PDP_INDEXER_PASSWORD; do
  if [ -z "${!var:-}" ]; then
    echo "Missing required environment variable: $var" >&2
    exit 2
  fi
done

SINCE="${PDP_HARVEST_SINCE:-1h}"

echo "==> Harvesting SCA evidence (--since $SINCE)"
python3 tools/evidence/harvest_sca_evidence.py --since "$SINCE"

echo "==> Harvesting custom-rule evidence (--since $SINCE)"
python3 tools/evidence/harvest_wazuh_rule_evidence.py --since "$SINCE"

echo "==> Aggregating control assessments"
python3 tools/assessment/assess_controls.py >/dev/null

echo "==> Generating/updating findings"
python3 tools/findings/generate_findings.py >/dev/null

echo "==> Registering evidence (local retention/integrity record, not indexed)"
python3 tools/evidence/register_evidence.py >/dev/null

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for kind in evidence assessment finding; do
  echo "==> Exporting $kind"
  python3 tools/export/export_bulk_ndjson.py --kind "$kind" --output "$TMP_DIR/${kind}.ndjson"
done

for kind in evidence assessment finding; do
  echo "==> Indexing $kind"
  curl -sk -u "${PDP_INDEXER_USER}:${PDP_INDEXER_PASSWORD}" \
    -H 'Content-Type: application/x-ndjson' \
    -X POST "${PDP_INDEXER_URL}/_bulk" \
    --data-binary "@$TMP_DIR/${kind}.ndjson" \
    | python3 -c "
import json, sys
d = json.load(sys.stdin)
if d.get('errors'):
    print('ERRORS in bulk index response:', file=sys.stderr)
    for item in d['items']:
        op = item.get('index', {})
        if op.get('status', 200) >= 300:
            print(' -', op.get('_id'), op.get('error'), file=sys.stderr)
    sys.exit(1)
print(f\"  {len(d['items'])} documents indexed, errors: {d['errors']}\")
"
done

echo "Done."
