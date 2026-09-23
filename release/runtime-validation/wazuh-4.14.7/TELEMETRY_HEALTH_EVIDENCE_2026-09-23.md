# Real wazuh-logtest Evidence — Telemetry Health (110301) — 2026-09-23

**Target:** Wazuh 4.14.7 (real manager, `hansip`)
**Rule:** `implementations/wazuh/rules/pdp_telemetry_health.xml`, rule `110301`
— a generic `<match>` rule with **no** `if_group`/`if_sid`/`decoded_as`
precondition, matching `(?i)(agent.*disconnected|agent.*inactive|
collector.*stopped|logging.*stopped)` against the raw `full_log` of any
event, regardless of source or decoder.

## Why there is no naturally-occurring real event to test against

Unlike authentication/PostgreSQL/privileged-access/FIM, Wazuh does not
generate an easily-triggerable, decodable log line for "agent
disconnected" by default: agent connectivity state is tracked internally
in `wazuh-db`'s agent table (confirmed via `agent_control -l` showing
`Disconnected` after stopping the test agent's daemons), not emitted as a
text line through the logcollector/decoder/rule text pipeline. `ossec.log`
and `alerts.json` were both checked after a real agent stop/reconnect
cycle and neither contained a matching event. This rule is a generic
safety net intended to catch this kind of wording from **third-party**
collectors/monitoring tools forwarding their own logs to Wazuh, not a
specific Wazuh-internal event — so its lab test is necessarily synthetic,
matching the four regex alternatives directly.

## Results

| Fixture | Regex alternative | Result |
|---|---|---|
| `telemetry_health/agent_disconnected.log` | `agent.*disconnected` | 110301 — PASS |
| `telemetry_health/agent_inactive.log` | `agent.*inactive` | 110301 — PASS |
| `telemetry_health/collector_stopped.log` | `collector.*stopped` | 110301 — PASS |
| `telemetry_health/logging_stopped.log` | `logging.*stopped` | 110301 — PASS (see finding below) |

## Finding — the rule's own coverage depends on no other rule matching first

The first attempt at the `logging_stopped` fixture used a syslog program
tag of `audit:` (`... audit: ERROR: Logging stopped due to disk full.`).
This did **not** fire `110301` — instead it matched built-in rule `6100`
("Solaris BSM Auditing messages grouped", `decoded_as solaris_bsm`,
level 0, `/var/ossec/ruleset/rules/0100-solaris_bsm_rules.xml`), and the
full debug trace (`wazuh-logtest -v`) showed `110301` was **never even
attempted** — Wazuh's rule engine stopped once `6100` matched. Re-running
with a non-colliding program tag (`pdp-lab-monitor:`) fired `110301`
correctly (see table above).

This is not a bug in `110301` — the rule and its regex work exactly as
written — but it is a real, confirmed limitation worth documenting: this
rule's `<match>` has no `if_group`/`if_sid` scoping, so **any** other
rule (including an unrelated, low-level, no-alert one from a completely
different product's ruleset) that happens to match the same log line
first will silently prevent `110301` from ever being evaluated. Anyone
wiring a real third-party collector's logs into Wazuh for this rule
should verify the collector's own log format does not collide with an
existing decoder/rule (the same class of issue found in
`release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md`
Finding 1, but there caused by an *intentional* broad `if_group`, whereas
here it is caused by having *no* scoping at all).

## What this validates

- All 4 documented regex alternatives in `pdp_telemetry_health.xml`
  correctly fire rule `110301` on real Wazuh 4.14.7, closing the last
  untested PDP rule family from
  `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`.
