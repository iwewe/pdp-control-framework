#!/usr/bin/env bash
# PDP Control Framework -- Wazuh Indexer templates + Dashboard install.
#
# Thin wrapper around two already-reviewed, real-runtime-tested scripts:
#   1. generate_dashboard_ndjson.py -- (re)builds the full 8-panel
#      dashboard NDJSON from DASHBOARD_SPEC.yml.
#   2. release/runtime-validation/dashboard/validate_real_import.py --
#      installs the three pdp-* index templates and imports the
#      dashboard NDJSON via the real saved-objects API, then verifies
#      both. This is the same script used for the 1.0.0 lab validation
#      pass (release/RELEASE_READINESS_1.0.0.yml); it only cleans up
#      its own temporary validation indices, never the installed
#      templates or the imported dashboard.
#
# Requires network access to the Indexer (port 9200) and Dashboard
# (port 443) from wherever this runs, and Python deps from
# requirements-dev.txt (PyYAML, requests).
#
# Credentials are read from the environment, never from a file
# committed to Git -- copy .env.example to .env, fill in real values,
# and load it first:
#
#   set -a; source .env; set +a
#   bash implementations/wazuh/dashboard/install_indexer_dashboard.sh
#
# See implementations/wazuh/DEPLOYMENT.md and INSTALL.md for full context.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"

for var in PDP_INDEXER_USER PDP_INDEXER_PASSWORD PDP_DASHBOARD_USER PDP_DASHBOARD_PASSWORD; do
  if [ -z "${!var:-}" ]; then
    echo "Missing required environment variable: $var" >&2
    echo "Copy .env.example to .env, fill in real values, and: set -a; source .env; set +a" >&2
    exit 2
  fi
done

echo "==> Regenerating the 8-panel dashboard NDJSON from DASHBOARD_SPEC.yml"
python3 "$ROOT/implementations/wazuh/dashboard/generate_dashboard_ndjson.py"

echo "==> Installing index templates and importing the dashboard"
python3 "$ROOT/release/runtime-validation/dashboard/validate_real_import.py"

echo
echo "Done. RESULT.json written to release/runtime-validation/dashboard/RESULT.json -- check \"overall\": \"PASS\"."
echo "Next: implementations/wazuh/dashboard/rbac/apply_rbac.sh to install viewer/editor RBAC roles."
