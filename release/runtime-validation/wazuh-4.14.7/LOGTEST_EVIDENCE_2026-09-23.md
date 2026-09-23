# Real wazuh-logtest Evidence — 2026-09-23

**Target:** Wazuh 4.14.7 (real manager, not a mock/stub)
**Environment:** Ubuntu 24.04.4 LTS, PostgreSQL 17.11, pgAudit 17.1
**Method:** `sudo /var/ossec/bin/wazuh-logtest -v < <fixture file>`, one process
invocation per fixture (so correlation fixtures accumulate within a single
`wazuh-logtest` session, matching how `if_matched_sid`/`frequency`/
`same_field` rules require state).

This is the first real-runtime confirmation for the pgAudit decoder fix
described in `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` (section 2) and
`release/CHANGELOG_0.10.0-rc2.md` (2026-09-22 hardening pass): the decoder's
prematch/regex were changed from anchored (`^AUDIT:\s+`) to searching for
`AUDIT:` anywhere in the line, so they tolerate PostgreSQL's own
`log_line_prefix` ahead of the `AUDIT:` payload.

## Pre-flight

- `sudo /var/ossec/bin/wazuh-analysisd -t` — exit code 0, zero `ERROR` lines,
  no warnings referencing any `pdp_*` rule/decoder file or rule IDs
  110001-110406.
- `sudo /var/ossec/bin/wazuh-control restart` — all daemons restarted
  cleanly ("Completed."), no `pdp`-related errors.

## Results vs. `implementations/wazuh/tests/expected/EXPECTED_RESULTS.yml`

| Fixture | Expected rule | Observed rule | Decoder | Result |
|---|---|---|---|---|
| `postgresql/pgaudit_role_create.log` | 110402 | 110402 | `pdp-pgaudit` | PASS |
| `postgresql/pgaudit_ddl_alter_table.log` | 110403 | 110403 | `pdp-pgaudit` | PASS |
| `postgresql/pgaudit_write_update.log` | 110404 | 110404 | `pdp-pgaudit` | PASS |
| `postgresql/pgaudit_read_select.log` | 110405 | 110405 | `pdp-pgaudit` | PASS |
| `postgresql/pgaudit_read_payroll.log` | (READ family) | 110405 | `pdp-pgaudit` | PASS |
| `postgresql/pgaudit_repeated_read_20.log` (correlation, 20 events, same session) | 110406 | 110406 (on reaching the frequency/timeframe threshold; events 1-19 matched 110405 as expected) | `pdp-pgaudit` | PASS |
| `authentication/ssh_failed_once.log` | 110001 | 110001 | `sshd` (built-in) | PASS |
| `authentication/ssh_failed_8.log` (correlation, 8 events, same session) | 110002 | 110002 (events 1-7 matched 110001, 8th escalated to 110002) | `sshd` (built-in) | PASS |
| `privileged_access/su_session_opened.log` | 110101 | 110101 | `pam` (built-in) | PASS |
| `privileged_access/su_session_repeated_3.log` (correlation, 3 events, same session) | 110102 | 110102 (events 1-2 matched 110101, 3rd escalated to 110102) | `pam` (built-in) | PASS |

**9 of 9 fixture definitions in `EXPECTED_RESULTS.yml` that have an
`expected_rule_id`: 11/11 individual log lines produced the expected rule,
including all four correlation cases in a single logtest session.**

## Finding: rule 110101's "sudo" keyword is unreachable with the default ruleset

`pdp_privileged_access.xml` rule `110101` requires
`<if_group>authentication_success</if_group>` *and* a regex match on
`(sudo|su:|administrator|root)`. On this real Wazuh 4.14.7 install:

- A `sudo` command-execution log line (e.g.
  `sudo:    bagong : TTY=pts/0 ; PWD=/home/bagong ; USER=root ; COMMAND=/usr/bin/apt update`)
  matched Wazuh's built-in rule `5403` ("First time user executed sudo",
  `groups: ['syslog', 'sudo']`) — **not** `authentication_success`. Checking
  the built-in ruleset (`/var/ossec/ruleset/rules/0020-syslog_rules.xml`,
  rules `5400`-`5407`, the full sudo family) confirms none of them carry the
  `authentication_success` group. So `110101` **never fires on sudo command
  execution**, even though "sudo" is one of its regex keywords.
- A PAM session-open line (`su: pam_unix(su:session): session opened for
  user root by bagong(uid=1000)`) matches built-in rule `5501` ("PAM: Login
  session opened", `groups: [..., 'authentication_success', ...]`,
  `/var/ossec/ruleset/rules/0085-pam_rules.xml`), and the required text
  (`root`, `su:`) is present, so `110101` fires correctly.

**Practical effect:** `110101`/`110102` only detect privileged activity via
PAM session-open events (`su`, `sshd` login, etc.), not `sudo` command
execution specifically, despite the rule text implying otherwise. This does
not block anything (the rule still fires on real privileged-session
events), but the "sudo" keyword in the regex is effectively dead unless a
future change adds an `if_sid` branch on the sudo rule family (`5400`-
`5407`) directly, without requiring `authentication_success`.

## What this validates

- The pgAudit decoder fix is confirmed correct against a real PostgreSQL
  17 + pgAudit log pipeline, not just the static fixture-shape check in
  `implementations/wazuh/tests/scripts/validate_fixtures.py`.
- Rule families `110401-110406` (PostgreSQL audit/DDL/role/read-anomaly),
  `110001-110002` (authentication), and `110101-110102` (privileged
  access) load and fire correctly on Wazuh 4.14.7.
- Correlation rules (`if_matched_sid`/`frequency`/`timeframe`, and
  `same_field`) work as specified across multi-line fixtures, across three
  independent rule families.

## What this does NOT yet validate

- `pdp_fim.xml` (110201-110202) and `pdp_telemetry_health.xml` (110301)
  have no fixtures in `implementations/wazuh/tests/fixtures/` yet, so they
  were not exercised by this run. FIM in particular cannot be validated the
  same way `wazuh-logtest` validates text-log rules, since syscheck events
  reach `analysisd` through a different internal path than logcollector
  text decoding — it requires a live create/modify/delete test against a
  monitored path instead (see the manager's `<syscheck>` block in
  `/var/ossec/etc/ossec.conf`).
- SCA policy execution (`implementations/wazuh/sca/pdp_linux_baseline.yml`)
  on a real agent.
- Centralized `agent.conf` distribution/acceptance (no agent enrolled
  yet in this lab at the time of this run).
- Wazuh Indexer/Dashboard import.

See `release/PRE_1_0_CHECKLIST.md` section D for the up-to-date checklist
state.
