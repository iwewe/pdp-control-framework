#!/usr/bin/env bash
set -eu

WAZUH_LOGTEST="${WAZUH_LOGTEST:-/var/ossec/bin/wazuh-logtest}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../../.." && pwd)"
FIX="$ROOT/implementations/wazuh/tests/fixtures"

if [ ! -x "$WAZUH_LOGTEST" ]; then
  echo "wazuh-logtest not found at $WAZUH_LOGTEST" >&2
  exit 2
fi

run_single() {
  file="$1"
  expectation="$2"
  echo "==> $file :: $expectation"
  "$WAZUH_LOGTEST" -v < "$FIX/$file"
}

run_single "postgresql/pgaudit_role_create.log" "rule 110402"
run_single "postgresql/pgaudit_ddl_alter_table.log" "rule 110403"
run_single "postgresql/pgaudit_write_update.log" "rule 110404"
run_single "postgresql/pgaudit_read_select.log" "rule 110405"

echo "==> Correlation fixture: PostgreSQL repeated reads"
"$WAZUH_LOGTEST" -v < "$FIX/postgresql/pgaudit_repeated_read_20.log"

echo "==> Authentication fixture"
"$WAZUH_LOGTEST" -v < "$FIX/authentication/ssh_failed_once.log"

echo "==> Authentication correlation fixture"
"$WAZUH_LOGTEST" -v < "$FIX/authentication/ssh_failed_8.log"
