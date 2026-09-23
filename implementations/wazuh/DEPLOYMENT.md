# Wazuh Lab Deployment Guide

This document covers the two operational gaps identified during the
0.10.0-rc2 review that are not specific to any single control or rule:
credential provisioning for the validation scripts, and how to actually
distribute the `agent.conf` overlays under `implementations/wazuh/shared/`
to a real Wazuh manager. It is deployment guidance, not a control or a test
definition — see `implementations/wazuh/README.md` for the implementation
boundary and capability mapping.

## 1. Credential provisioning

The two real-runtime scripts in this repository read credentials from the
environment, never from a file committed to Git:

- `implementations/wazuh/tests/harness/run_api_logtest.py` — Wazuh Server
  API `/logtest` harness.
- `release/runtime-validation/dashboard/validate_real_import.py` — Wazuh
  Indexer/Dashboard import validation.

Steps:

1. Copy `.env.example` (repository root) to `.env`.
2. Fill in real values for your lab (API/indexer/dashboard URLs and
   credentials). `.env` is already excluded by `.gitignore` — do not remove
   that exclusion.
3. Load it into your shell before running a script, e.g.:
   ```bash
   set -a; source .env; set +a
   python implementations/wazuh/tests/harness/run_api_logtest.py
   ```
4. In CI or a shared runner, provide these as pipeline secrets rather than
   a checked-in file (e.g. GitHub Actions repository/environment secrets).
   Never echo secret values in logs; both scripts already avoid printing
   the password/token values themselves.

Neither script hardcodes a default user/password — both exit with an error
if the required variables are missing (see each script's `if not ... :
sys.exit(2)` guard), so a misconfigured environment fails loudly rather
than silently skipping validation.

## 2. Agent-group deployment

The repository defines two centralized configuration overlays:

- `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
- `implementations/wazuh/shared/pdp-database/agent.conf`

These correspond to the Wazuh manager's [centralized configuration / agent
groups](https://documentation.wazuh.com/current/user-manual/agents/centralized-configuration.html)
feature: each group's `agent.conf` lives under
`/var/ossec/etc/shared/<group>/agent.conf` on the manager and is pushed to
every agent assigned to that group.

Steps on the Wazuh manager:

```bash
# 1. Create the group (if it does not already exist)
/var/ossec/bin/agent_groups -a -g pdp-linux-baseline
/var/ossec/bin/agent_groups -a -g pdp-database

# 2. Copy the repository-controlled agent.conf into the group's shared directory
#    (repository content is the source of truth -- see docs/REPOSITORY_LAYOUT.md
#    "Authority model" -- do not hand-edit the file on the manager)
cp implementations/wazuh/shared/pdp-linux-baseline/agent.conf \
   /var/ossec/etc/shared/pdp-linux-baseline/agent.conf
cp implementations/wazuh/shared/pdp-database/agent.conf \
   /var/ossec/etc/shared/pdp-database/agent.conf

# pdp-linux-baseline/agent.conf references an SCA policy by an agent-side
# path (/var/ossec/etc/shared/pdp_linux_baseline.yml). That file must be
# pushed to the agent through the same shared-files mechanism, so it also
# needs to live in the group's directory on the manager:
cp implementations/wazuh/sca/pdp_linux_baseline.yml \
   /var/ossec/etc/shared/pdp-linux-baseline/pdp_linux_baseline.yml

# 3. Assign an agent to a group
/var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline
# a database host is typically in both groups (baseline + database overlay):
/var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline,pdp-database

# 4. Agents pick up the new shared configuration on their next check-in
#    interval, or immediately by restarting the agent:
systemctl restart wazuh-agent
```

> **Do not include a `<syscollector>` block in a group's `agent.conf`.**
> Confirmed on real Wazuh 4.14.7, 2026-09-23: Wazuh rejects `<syscollector>`
> inside a centralized/shared `agent.conf` ("Invalid element in the
> configuration: 'syscollector'"), and that single invalid element
> invalidates the **entire** `agent.conf` for that agent -- labels,
> syscheck, and SCA all silently stop applying too, not just syscollector.
> `implementations/wazuh/shared/pdp-linux-baseline/agent.conf` no longer
> includes it, for this reason. Configure syscollector locally in each
> agent's own `ossec.conf` instead.

> **The SCA policy does not currently work when distributed this way.**
> Confirmed on real Wazuh 4.14.7, 2026-09-23 (see
> `release/runtime-validation/wazuh-4.14.7/AGENT_CONF_EVIDENCE_2026-09-23.md`):
> every check in `pdp_linux_baseline.yml` uses a `c:<command>` rule, and
> Wazuh disables command execution by default (`sca.remote_commands=0`)
> for any SCA policy delivered via centralized/shared configuration, as a
> guardrail against a compromised manager pushing arbitrary commands to
> agents. Setting `sca.remote_commands=1` in `local_internal_options.conf`
> (tried on both the agent and the manager, with full daemon restarts) did
> **not** resolve this in this lab -- the policy's checks stayed
> `not applicable`. Until this is resolved, deploy `pdp_linux_baseline.yml`
> as a **local** policy in each endpoint's own `ossec.conf`
> `<sca><policies>` block instead (as validated in
> `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`),
> not via an agent group.

Before deploying, replace the placeholder label values in
`implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
(`pdp.environment`, `pdp.asset_id`, `pdp.processing_activity_id` — currently
`SET_ME`) with real values per asset, per
`implementations/wazuh/README.md` section "Agent Labels". Do not put
Personal Data itself into labels.

Verification:

```bash
# On the manager: confirm the group's merged configuration is well-formed
/var/ossec/bin/agent_groups -s -g pdp-linux-baseline

# On an agent: confirm it received the group's configuration
cat /var/ossec/etc/shared/ar.conf 2>/dev/null  # example; actual path may vary by version
/var/ossec/bin/agent_control -i <agent_id>
```

This step is required before the checklist item "Centralized `agent.conf`
accepted by Wazuh" in `release/PRE_1_0_CHECKLIST.md` (section D) can be
checked off.

## 3. SCA policy ID range

`implementations/wazuh/sca/pdp_linux_baseline.yml` uses check IDs starting
at `910001`. Before running it on a real manager/agent, confirm this range
does not collide with Wazuh's bundled SCA policies or any other custom SCA
content already deployed in the target environment (Wazuh does not enforce
global uniqueness of SCA check IDs across policies the way it does for rule
IDs). If a collision is found, renumber the PDP policy's checks rather than
the vendor policy's.

Also remember to reference the policy file explicitly under the target's
`<sca><policies>` block — placing it in `/var/ossec/etc/shared/<group>/`
alone does not make Wazuh load it. Confirmed on real Wazuh 4.14.7,
2026-09-23 (see `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`):
no collision was observed against the bundled `cis_ubuntu24-04.yml` policy,
and all 6 checks executed and produced correct results once the
`<policies>` entry was added.

That test was against a **local** `<sca><policies>` entry (the manager's
own `ossec.conf`). See section 2 above: the same policy distributed via an
agent **group's** `agent.conf` does not currently produce usable results at
all, because its checks rely on `c:` commands that Wazuh blocks by default
for centrally-pushed SCA policies.

## 4. Back up dashboard saved objects before restarting/upgrading Wazuh Dashboard

Confirmed on real Wazuh 4.14.7, 2026-09-23 (see
`release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`,
Finding 3): the imported PDP dashboard shell and its 3 index patterns were
silently lost after a `wazuh-dashboard` service restart that followed a
`wazuh-dashboard` package upgrade (`4.14.5-1 -> 4.14.7-1`) earlier the same
day. The underlying `.kibana_1` index was not recreated (same index UUID
before and after) — this was a saved-objects-level loss, most likely tied
to how OpenSearch Dashboards' migration step (which runs on every process
start) handled objects stamped with an older app version's
`migrationVersion`. Re-importing the same NDJSON immediately and cleanly
restored everything both times this was tested, so the repository content
itself is not at fault — but nothing guarantees custom saved objects
survive the next restart, especially the first one after a package
upgrade.

**Before restarting or upgrading `wazuh-dashboard`,** export the current
saved objects as a backup:

```bash
curl -sk -u admin:<password> \
  -H "osd-xsrf: true" \
  "https://<dashboard-host>/api/saved_objects/_export" \
  -H "Content-Type: application/json" \
  -d '{"type": ["index-pattern", "dashboard", "visualization", "search"]}' \
  -o dashboard-backup-$(date +%Y%m%d).ndjson
```

**After the restart/upgrade completes,** verify the PDP objects are still
present (`GET /api/saved_objects/_find?type=dashboard&search=PDP&search_fields=title`),
and if not, re-import them:

```bash
python3 release/runtime-validation/dashboard/validate_real_import.py
# or, to restore from your own backup instead of the repo's shell NDJSON:
curl -sk -u admin:<password> -H "osd-xsrf: true" \
  -F "file=@dashboard-backup-YYYYMMDD.ndjson;type=application/ndjson" \
  "https://<dashboard-host>/api/saved_objects/_import?overwrite=true"
```

If you build out the full eight-panel dashboard
(`implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`) or add your own
visualizations, back them up the same way — do not assume they survive a
future Wazuh upgrade unattended.
