# Real FIM (File Integrity Monitoring) Evidence — 2026-09-23

**Target:** Wazuh 4.14.7 (real manager, agent `000`/local)
**Environment:** Ubuntu 24.04.4 LTS

## Why this is not a `wazuh-logtest` fixture

Unlike the authentication/PostgreSQL rule families
(`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`),
FIM (`pdp_fim.xml`, rules `110201`-`110202`) cannot be validated by feeding a
static text line into `wazuh-logtest`. Syscheck events reach `analysisd`
through a dedicated internal path (the local `wazuh-syscheckd` daemon
detects a real filesystem change and emits an internal message decoded by
built-in `syscheck_new_entry`/`syscheck_integrity_changed`/`syscheck_deleted`
decoders), not through the logcollector text-decoding pipeline that
`wazuh-logtest` exercises. Validating these rules requires a real
create/modify/delete against a monitored path.

## Method

The manager's default local `<syscheck>` config (`/var/ossec/etc/ossec.conf`)
only does a periodic/`scan_on_start` scan (every 12h, or at manager
restart) with no `realtime`/`whodata` directories — a full restart-based
scan turned out to just silently (re)establish its baseline rather than
alert on the diff (see "First attempt" below). To get a real, immediately
observable result, a temporary test directory was added, matching this
framework's own `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
pattern (`realtime="yes" whodata="yes"`):

```xml
<directories realtime="yes" whodata="yes">/etc/pdp-fim-test</directories>
```

This was added to the manager's local `ossec.conf`, the manager was
restarted once, and a file was created/modified/deleted inside
`/etc/pdp-fim-test`, with `/var/ossec/logs/alerts/alerts.json` checked
after each step. **The temporary directory and config line were removed
again after testing**, and the manager restarted a final time to restore
the environment to its pre-test state.

## First attempt (before realtime was added) — inconclusive, and a false positive found

Before adding the realtime test directory, a file was created directly
under the manager's existing periodic-scan path (`/etc/pdp-fim-test.conf`)
and the manager was restarted to trigger `scan_on_start`. This did **not**
produce a "file added" alert for the test file at all (confirmed later: the
file was present in `/var/ossec/queue/fim/db/fim.db`'s `file_entry` table,
so it *was* tracked, just never alerted — restart-triggered
`scan_on_start` appears to (re)baseline rather than diff-and-alert in this
configuration). It did, however, surface a real bug in the *original*
`pdp_fim.xml`:

**Finding 1 — `110201` false-positives on rootcheck/OpenSCAP/etc. housekeeping messages.**
The original rule used `<if_group>syscheck</if_group>` with no further
condition. Wazuh's built-in rule `515` ("Ignoring scan messages", level 0,
`/var/ossec/ruleset/rules/0015-ossec_rules.xml`) tags *all* scan
start/end housekeeping messages (rootcheck, syscheck, OpenSCAP, CIS-CAT,
Azure-logs) with group `rootcheck,syscheck,...` specifically so they can be
suppressed — but our rule re-alerted them at level 7 with a generated
description ("integrity event on monitored path - .", empty path) every
time *any* scan started or ended. Confirmed repeatedly in
`alerts.json` (`full_log: "Ending rootcheck scan."`, `decoder: rootcheck`,
matched by `110201`).

**Fix:** anchor on `<if_group>syscheck_file</if_group>` instead — only the
three real per-file event rules (`550` modified, `553` deleted, `554`
added, in the same `0015-ossec_rules.xml`) carry that group.

## Second attempt (with realtime FIM) — full validation

After the fix and after adding the temporary realtime test directory:

| Step | Alert rule | `syscheck.event` | Result |
|---|---|---|---|
| `echo v1 > .../final_check.txt` (create) | 110201 | `added` | PASS |
| `echo v2 >> .../final_check.txt` (modify) | 110201 | `modified` | PASS |
| `rm .../final_check.txt` (delete) | 110202 | `deleted` | PASS |

No false positives were observed after the `110201` fix (no further
rootcheck/scan-message alerts under rule `110201` after the fix was
deployed and the manager restarted).

**Finding 2 — `110202`'s field check used the wrong field name.**
The original rule checked `<field name="type">deleted</field>`. The actual
decoded alert for a deletion (confirmed from a live delete alert's full
JSON) carries the value under `syscheck.event` (`"syscheck":{"event":
"deleted", ...}`, `"decoder":{"name":"syscheck_deleted"}`) — there is no
`type` field on the alert at all, so `110202` never fired (the delete event
only ever matched the parent rule `110201`). A first fix attempt using
`<field name="syscheck.event">deleted</field>` (the JSON-nested path) also
did not fire; only switching to `<decoded_as>syscheck_deleted</decoded_as>`
(mirroring exactly how the built-in rule `553` itself identifies deletions)
worked. This is now the deployed and lab-confirmed form.

## Result

Both `pdp_fim.xml` rules now behave correctly on real Wazuh 4.14.7:
`110201` fires on genuine add/modify/delete events (and no longer on
scan-lifecycle noise), and `110202` correctly identifies the deletion case
specifically.

See `release/PRE_1_0_CHECKLIST.md` section D and
`reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` for how this is reflected in
overall release status.
