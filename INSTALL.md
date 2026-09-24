# Installation Guide

This is the step-by-step path from a bare Wazuh 4.14.7 stack to a
running PDP Control Framework 1.0.0 deployment: manager-side rules,
decoders and SCA policy; agent-side configuration; PostgreSQL/pgAudit
telemetry; Indexer templates; the compliance Dashboard; and its RBAC.

Every step below was exercised on a real Wazuh 4.14.7 lab
(`release/RELEASE_READINESS_1.0.0.yml`, `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`).
The automation scripts introduced here wrap that same tested content and
those same tested scripts — they do not add new untested deployment
logic.

## 0. Compatibility target

See `release/compatibility/COMPATIBILITY_MATRIX.yml` for the full,
versioned list. Summary:

| Component | Target version |
|---|---|
| Wazuh manager/indexer/dashboard | 4.14.7 (identical patch level across all three) |
| Wazuh agent | 4.14.7 (or older, never newer than the manager) |
| Ubuntu | 24.04 LTS |
| PostgreSQL | 17 |
| pgAudit | 17.x matching PostgreSQL 17 |
| Python (for this repo's scripts) | 3.12 |

## 1. Install base Wazuh

Installing Wazuh itself (manager, indexer, dashboard) is out of scope
for this framework — follow the
[official Wazuh 4.14 installation guide](https://documentation.wazuh.com/current/installation-guide/index.html).
An all-in-one single-host install (as used for this framework's own lab
validation) or a distributed install both work; the steps below are the
same either way, just against different hostnames.

Once Wazuh is installed and reachable, get this repository onto the
manager host (and the indexer host, if separate):

```bash
git clone https://github.com/iwewe/pdp-control-framework.git
cd pdp-control-framework
```

For the credentialed scripts in steps 4-5, also set up a Python
environment with this repo's dependencies (on whichever host runs them
— does not have to be the Wazuh hosts themselves, as long as it can
reach the Indexer on port 9200 and the Dashboard on port 443):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 2. Deploy manager-side content: rules, decoders, SCA policy

Run on the Wazuh manager, as root:

```bash
sudo bash implementations/wazuh/install.sh --local-sca
```

This copies `implementations/wazuh/rules/pdp_*.xml` to
`/var/ossec/etc/rules/`, `implementations/wazuh/decoders/pdp_pgaudit.xml`
to `/var/ossec/etc/decoders/`, and (with `--local-sca`) the SCA policy to
`/var/ossec/etc/shared/default/pdp_linux_baseline.yml`. Any file it
would overwrite is backed up first with a timestamp suffix. It restarts
`wazuh-manager` at the end (skip with `--no-restart` if you want to
batch this with the manual step below first).

Run `--dry-run` first to preview every change with no side effects:

```bash
bash implementations/wazuh/install.sh --local-sca --dry-run
```

**One manual step this script deliberately does not automate:** add the
SCA policy reference to `ossec.conf`'s `<sca><policies>` block (the
script prints the exact snippet to add). This is not automated because
an invalid `ossec.conf` edit can silently disable unrelated config in
the same file — confirmed for real during this framework's own lab
validation with an invalid `<syscollector>` element (see
`implementations/wazuh/DEPLOYMENT.md`).

```xml
<sca>
  <policies>
    <policy enabled="yes">/var/ossec/etc/shared/default/pdp_linux_baseline.yml</policy>
  </policies>
</sca>
```

Restart `wazuh-manager` after this edit if you used `--no-restart` above.

### Centralized distribution to multiple agents instead

If you have more than one endpoint to cover, use agent groups instead of
(or in addition to) the local SCA entry above:

```bash
sudo bash implementations/wazuh/install.sh --agent-groups
```

This creates the `pdp-linux-baseline` and `pdp-database` agent groups
and populates their shared `agent.conf`/SCA policy files. Before
assigning real agents, replace the `SET_ME` placeholder label values in
`implementations/wazuh/shared/pdp-linux-baseline/agent.conf` (in the
repository, then re-run this script — never hand-edit the copy under
`/var/ossec/etc/shared/`, see `docs/REPOSITORY_LAYOUT.md` "Authority
model"). Full details, including the required
`sca.remote_commands=1` per-agent setting: `implementations/wazuh/DEPLOYMENT.md` section 2.

## 3. Enroll agents

Standard Wazuh agent installation and enrollment
(`documentation.wazuh.com`) — out of scope for this framework. Once an
agent is enrolled, assign it to the groups from step 2 if you're using
centralized distribution:

```bash
/var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline
# a database host is typically in both groups:
/var/ossec/bin/agent_groups -a -i <agent_id> -g pdp-linux-baseline,pdp-database
```

## 4. Configure PostgreSQL + pgAudit (database hosts only)

On each PostgreSQL 17 host in scope:

```bash
sudo -u postgres psql -f implementations/wazuh/postgresql/pgaudit-setup.sql
```

Apply the settings in
`implementations/wazuh/postgresql/postgresql-pdp.conf.example` to
`postgresql.conf` (review them against your own processing activity and
logging policy first — they are a privacy-aware starting point, not a
one-size-fits-all default; see the file's own comments and
`implementations/wazuh/postgresql/POSTGRESQL_AUDIT_PROFILE.yml`), then
restart PostgreSQL.

Point a Wazuh `<localfile>` block at the resulting log so the manager or
agent actually ingests it, e.g. in that host's `ossec.conf`:

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/postgresql/postgresql-17-main.log</location>
</localfile>
```

The decoder/rule matching itself was validated against real
`wazuh-logtest` fixture log lines (`implementations/wazuh/tests/fixtures/postgresql/`),
not yet against a live `<localfile>` tail of a real running PostgreSQL
instance — confirm decoding end to end on your own host after this step.

## 5. Install Indexer templates and the Dashboard

From a host that can reach the Indexer (port 9200) and Dashboard (port
443) — this can be run remotely, it doesn't have to be the Wazuh hosts
themselves:

```bash
cp .env.example .env
# edit .env: fill in PDP_INDEXER_URL/USER/PASSWORD and PDP_DASHBOARD_URL/USER/PASSWORD
set -a; source .env; set +a
bash implementations/wazuh/dashboard/install_indexer_dashboard.sh
```

This installs the three `pdp-*` index templates, (re)generates the full
8-panel dashboard NDJSON from `DASHBOARD_SPEC.yml`, imports it via the
real saved-objects API, and verifies both. Check
`release/runtime-validation/dashboard/RESULT.json` afterward for
`"overall": "PASS"`.

To confirm the dashboard actually renders (not just that the API calls
succeed), open it in a browser — see
`implementations/wazuh/DEPLOYMENT.md` section 5 for exact steps
(URL, credential lookup, navigation).

**Before any later `wazuh-dashboard` restart or upgrade,** back up saved
objects first — see `implementations/wazuh/DEPLOYMENT.md` section 4;
saved objects are not guaranteed to survive the first restart after a
package upgrade.

## 6. Install dashboard RBAC (viewer / editor roles)

Run on the Wazuh Indexer host, as root:

```bash
sudo bash implementations/wazuh/dashboard/rbac/apply_rbac.sh
```

This YAML-merges `pdp_dashboard_viewer`/`pdp_dashboard_editor` into the
live `roles.yml`/`roles_mapping.yml` (backing both up first, and safe to
re-run), then reloads via `securityadmin.sh`. It prints the remaining
manual step — creating internal users and their password hashes, which
stays interactive by design (this script never creates secrets). Full
background (why v1/v2 failed, root cause, and the post-install test
procedure to confirm it works end to end): `implementations/wazuh/dashboard/rbac/README.md`.

Use `--dry-run` first, and non-default paths if your indexer install
differs from the standard package layout:

```bash
bash implementations/wazuh/dashboard/rbac/apply_rbac.sh --dry-run
```

## 7. Verify

- `python3 tools/validation/validate_structure.py`
- `python3 implementations/wazuh/tests/scripts/validate_fixtures.py`
- On the manager: `/var/ossec/bin/agent_control -i <agent_id>` shows the
  agent connected and (if using agent groups) the group applied.
- `release/runtime-validation/dashboard/RESULT.json`: `"overall": "PASS"`.
- Dashboard RBAC test procedure: `implementations/wazuh/dashboard/rbac/README.md` "Test procedure".
- Open the dashboard in a browser: `implementations/wazuh/DEPLOYMENT.md` section 5.

For what was already validated in the reference lab and what remains
explicitly out of scope (SSO/external identity provider integration),
see `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` and
`release/RELEASE_READINESS_1.0.0.yml`.
