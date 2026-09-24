#!/usr/bin/env bash
# PDP Control Framework -- Wazuh manager-side installer.
#
# Deploys the manager-side artifacts this repository owns: custom
# rules/decoders, and (optionally) the SCA policy as either a local
# manager-side entry or a centralized agent-group overlay. Run this ON
# the Wazuh manager host, with this repository checked out or copied
# there first (e.g. `git clone https://github.com/iwewe/pdp-control-framework`).
#
# What this script deliberately does NOT automate:
#   - editing ossec.conf's <sca><policies> block (a malformed edit can
#     silently disable unrelated config in the same file -- see the
#     <syscollector> warning in implementations/wazuh/DEPLOYMENT.md for
#     a real example of this failure mode)
#   - per-agent sca.remote_commands=1 in local_internal_options.conf
#   - indexer index templates / dashboard import / RBAC (separate
#     credentialed steps -- see implementations/wazuh/dashboard/
#     install_indexer_dashboard.sh and dashboard/rbac/apply_rbac.sh)
#   - PostgreSQL/pgAudit configuration (see implementations/wazuh/postgresql/)
#
# See implementations/wazuh/DEPLOYMENT.md and INSTALL.md for full context.
set -eu

usage() {
  cat <<'USAGE'
Usage: install.sh [--ossec-path PATH] [--local-sca] [--agent-groups] [--no-restart] [--dry-run]

  --ossec-path PATH  Wazuh install path (default: /var/ossec)
  --local-sca        Also install the SCA policy for a LOCAL <sca><policies>
                      entry on this manager (copies to
                      $OSSEC_PATH/etc/shared/default/pdp_linux_baseline.yml,
                      matching release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md).
                      Still requires a manual ossec.conf edit -- see the
                      printed instructions.
  --agent-groups     Create/populate the pdp-linux-baseline and pdp-database
                      centralized agent groups (agent.conf overlays + SCA
                      policy in the group's shared directory).
  --no-restart       Skip the wazuh-manager restart at the end.
  --dry-run          Print what would be done without changing anything.
USAGE
}

OSSEC_PATH="/var/ossec"
DO_LOCAL_SCA=0
DO_AGENT_GROUPS=0
DO_RESTART=1
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --ossec-path) OSSEC_PATH="$2"; shift 2 ;;
    --local-sca) DO_LOCAL_SCA=1; shift ;;
    --agent-groups) DO_AGENT_GROUPS=1; shift ;;
    --no-restart) DO_RESTART=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
# implementations/wazuh/install.sh -> ROOT is the repository root
ROOT="$(CDPATH= cd -- "$ROOT/.." && pwd)"

if [ "$DRY_RUN" -eq 0 ] && [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo) -- writes under $OSSEC_PATH/etc/." >&2
  exit 2
fi

if [ ! -d "$OSSEC_PATH" ]; then
  echo "Wazuh install path not found: $OSSEC_PATH" >&2
  exit 2
fi

TS="$(date +%Y%m%d%H%M%S)"

backup_and_copy() {
  src="$1"; destdir="$2"
  base="$(basename "$src")"
  if [ "$DRY_RUN" -eq 1 ]; then
    if [ -e "$destdir/$base" ]; then
      echo "[dry-run] would back up $destdir/$base -> $destdir/$base.bak-$TS"
    fi
    echo "[dry-run] would copy $src -> $destdir/$base"
    return 0
  fi
  mkdir -p "$destdir"
  if [ -e "$destdir/$base" ]; then
    cp -p "$destdir/$base" "$destdir/$base.bak-$TS"
  fi
  cp "$src" "$destdir/$base"
}

echo "==> Deploying rules to $OSSEC_PATH/etc/rules"
for f in "$ROOT"/implementations/wazuh/rules/pdp_*.xml; do
  backup_and_copy "$f" "$OSSEC_PATH/etc/rules"
done

echo "==> Deploying decoders to $OSSEC_PATH/etc/decoders"
for f in "$ROOT"/implementations/wazuh/decoders/pdp_*.xml; do
  backup_and_copy "$f" "$OSSEC_PATH/etc/decoders"
done

if [ "$DO_LOCAL_SCA" -eq 1 ]; then
  echo "==> Deploying SCA policy for a local <sca><policies> entry"
  backup_and_copy "$ROOT/implementations/wazuh/sca/pdp_linux_baseline.yml" \
    "$OSSEC_PATH/etc/shared/default"
fi

if [ "$DO_AGENT_GROUPS" -eq 1 ]; then
  AGENT_GROUPS_BIN="$OSSEC_PATH/bin/agent_groups"
  if [ "$DRY_RUN" -eq 0 ] && [ ! -x "$AGENT_GROUPS_BIN" ]; then
    echo "agent_groups binary not found at $AGENT_GROUPS_BIN -- skipping agent-group setup" >&2
  else
    for group in pdp-linux-baseline pdp-database; do
      echo "==> Ensuring agent group: $group"
      if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] would run: $AGENT_GROUPS_BIN -a -g $group"
      else
        "$AGENT_GROUPS_BIN" -a -g "$group" >/dev/null 2>&1 || true  # already exists is fine
      fi
    done

    echo "==> Deploying pdp-linux-baseline/agent.conf"
    backup_and_copy "$ROOT/implementations/wazuh/shared/pdp-linux-baseline/agent.conf" \
      "$OSSEC_PATH/etc/shared/pdp-linux-baseline"

    echo "==> Deploying pdp_linux_baseline.yml SCA policy into the pdp-linux-baseline group"
    backup_and_copy "$ROOT/implementations/wazuh/sca/pdp_linux_baseline.yml" \
      "$OSSEC_PATH/etc/shared/pdp-linux-baseline"

    echo "==> Deploying pdp-database/agent.conf"
    backup_and_copy "$ROOT/implementations/wazuh/shared/pdp-database/agent.conf" \
      "$OSSEC_PATH/etc/shared/pdp-database"

    cat <<'NOTE'

Reminder before assigning real agents to these groups:
  1. Replace the SET_ME placeholder label values in
     implementations/wazuh/shared/pdp-linux-baseline/agent.conf (already
     copied above) with real per-asset values -- do this in the
     repository and re-run this script, do not hand-edit the copy on
     the manager (see docs/REPOSITORY_LAYOUT.md "Authority model").
  2. Assign agents to the groups, e.g.:
       /var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline
       /var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline,pdp-database
  3. Each receiving agent also needs sca.remote_commands=1 in its own
     local_internal_options.conf for the SCA policy's c: checks to run
     -- see implementations/wazuh/DEPLOYMENT.md section 2.
NOTE
  fi
fi

cat <<NOTE

==> Manual step required: SCA policy reference in ossec.conf

Add the SCA policy reference to the relevant <sca><policies> block:

  <sca>
    <policies>
      <policy enabled="yes">$OSSEC_PATH/etc/shared/default/pdp_linux_baseline.yml</policy>
    </policies>
  </sca>

(For centralized/agent-group distribution, this instead goes in the
group's own agent.conf, which implementations/wazuh/shared/pdp-linux-baseline/agent.conf
already includes referencing $OSSEC_PATH/etc/shared/pdp_linux_baseline.yml.)

This is intentionally not automated by this script -- an invalid
ossec.conf edit silently disables unrelated config in the same file
(see implementations/wazuh/DEPLOYMENT.md's <syscollector> warning for a
real example of this failure mode).
NOTE

if [ "$DO_RESTART" -eq 1 ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] would run: systemctl restart wazuh-manager"
  else
    echo "==> Restarting wazuh-manager"
    systemctl restart wazuh-manager
  fi
else
  echo "==> Skipping wazuh-manager restart (--no-restart). Restart manually after editing ossec.conf."
fi

echo "Done."
