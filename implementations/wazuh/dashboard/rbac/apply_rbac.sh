#!/usr/bin/env bash
# PDP Control Framework -- apply the pdp_dashboard_viewer/editor RBAC
# roles to a Wazuh Indexer's OpenSearch Security config.
#
# Run this ON the Wazuh Indexer host (it needs to read/write
# /etc/wazuh-indexer/opensearch-security/ and run securityadmin.sh).
#
# What this script does:
#   1. Backs up roles.yml and roles_mapping.yml with a timestamp.
#   2. YAML-merges roles.yml / roles_mapping.yml (this directory) into
#      the live files -- a proper merge, not a blind text append, so
#      re-running this script is safe (idempotent).
#   3. Runs securityadmin.sh to reload (does not require restarting the
#      indexer).
#
# What this script deliberately does NOT do:
#   - create internal users / generate password hashes. That is a
#     secret-creation step and stays manual and interactive -- see the
#     printed instructions at the end, and implementations/wazuh/dashboard/rbac/README.md.
#
# See implementations/wazuh/dashboard/rbac/README.md for the full v1->v2->v3
# design history and the live test procedure to run afterward.
set -eu

usage() {
  cat <<'USAGE'
Usage: apply_rbac.sh [--security-config PATH] [--java-home PATH]
                      [--tools PATH] [--certs PATH] [--dry-run]

  --security-config PATH  Default: /etc/wazuh-indexer/opensearch-security
  --java-home PATH        Default: /usr/share/wazuh-indexer/jdk
  --tools PATH            Default: /usr/share/wazuh-indexer/plugins/opensearch-security/tools
  --certs PATH            Default: /etc/wazuh-indexer/certs
  --dry-run               Print what would be done without changing anything
USAGE
}

SEC_CONFIG="/etc/wazuh-indexer/opensearch-security"
JAVA_HOME_PATH="/usr/share/wazuh-indexer/jdk"
TOOLS_PATH="/usr/share/wazuh-indexer/plugins/opensearch-security/tools"
CERTS_PATH="/etc/wazuh-indexer/certs"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --security-config) SEC_CONFIG="$2"; shift 2 ;;
    --java-home) JAVA_HOME_PATH="$2"; shift 2 ;;
    --tools) TOOLS_PATH="$2"; shift 2 ;;
    --certs) CERTS_PATH="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ "$DRY_RUN" -eq 0 ] && [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) -- writes under $SEC_CONFIG and runs securityadmin.sh." >&2
  exit 2
fi

if [ ! -d "$SEC_CONFIG" ]; then
  echo "OpenSearch Security config directory not found: $SEC_CONFIG" >&2
  exit 2
fi

TS="$(date +%Y%m%d%H%M%S)"

merge_yaml() {
  snippet="$1"; live="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] would back up $live -> $live.bak-$TS"
    echo "[dry-run] would merge keys from $snippet into $live"
    return 0
  fi
  cp -p "$live" "$live.bak-$TS"
  python3 - "$snippet" "$live" <<'PY'
import sys
import yaml

snippet_path, live_path = sys.argv[1], sys.argv[2]

with open(snippet_path, encoding="utf-8") as f:
    snippet = yaml.safe_load(f) or {}
with open(live_path, encoding="utf-8") as f:
    live = yaml.safe_load(f) or {}

overwritten = [k for k in snippet if k in live]
live.update(snippet)

with open(live_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(live, f, default_flow_style=False, sort_keys=False)

if overwritten:
    print(f"  merged into {live_path} (replaced existing keys: {overwritten})")
else:
    print(f"  merged into {live_path} (added keys: {list(snippet)})")
PY
}

echo "==> Merging roles.yml"
merge_yaml "$HERE/roles.yml" "$SEC_CONFIG/roles.yml"

echo "==> Merging roles_mapping.yml"
merge_yaml "$HERE/roles_mapping.yml" "$SEC_CONFIG/roles_mapping.yml"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would run securityadmin.sh to reload"
else
  echo "==> Reloading security config with securityadmin.sh"
  env OPENSEARCH_JAVA_HOME="$JAVA_HOME_PATH" \
    "$TOOLS_PATH/securityadmin.sh" \
    -cd "$SEC_CONFIG" \
    -icl -key "$CERTS_PATH/admin-key.pem" \
    -cert "$CERTS_PATH/admin.pem" \
    -cacert "$CERTS_PATH/root-ca.pem" \
    -h 127.0.0.1 -p 9200 -nhnv
fi

cat <<'NOTE'

==> Manual step required: create internal users for the new roles

Password/hash creation is not automated by this script. For each real
user, generate a hash and add them to internal_users.yml's
backend_roles ("pdp_viewer" or "pdp_editor"), e.g.:

  sudo cp /etc/wazuh-indexer/opensearch-security/internal_users.yml{,.bak}
  sudo env OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk \
    /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p '<a-fresh-password>'
  # then add the resulting hash under internal_users.yml, backend_roles: ["pdp_viewer"] or ["pdp_editor"]
  # then re-run securityadmin.sh to reload internal_users.yml too.

See implementations/wazuh/dashboard/rbac/README.md for the full test
procedure to confirm the roles work end to end afterward.
NOTE

echo "Done."
