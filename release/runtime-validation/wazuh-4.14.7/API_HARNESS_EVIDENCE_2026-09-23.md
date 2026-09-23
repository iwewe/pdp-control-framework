# Real Wazuh Server API Harness Evidence — 2026-09-23

**Target:** Wazuh 4.14.7 Server API (`https://127.0.0.1:55000`), same lab
host as every prior phase.
**Harness:** `implementations/wazuh/tests/harness/run_api_logtest.py` —
authenticates to `/security/user/authenticate`, then drives all 13 cases
in `implementations/wazuh/tests/harness/HARNESS.yml` through `PUT
/logtest`, producing one normalized evidence document per case in
`implementations/wazuh/tests/results/` (matching
`framework/schemas/evidence.schema.json`).

This is the first real run of this harness — every prior phase used the
`wazuh-logtest` CLI directly instead. Credentials
(`api_username: wazuh`) were extracted from
`~/wazuh-install-files.tar`'s `wazuh-passwords.txt` server-side and never
printed to a terminal transcript.

## Bug found and fixed — `test.decoder` was an object, not a string

The harness's first run completed with `"result": "PASS"` for all 13
cases (rule-matching logic was already correct), but the generated
evidence documents failed schema validation:

```
{'name': 'pdp-pgaudit'} is not of type 'string', 'null' @ ['test', 'decoder']
```

`framework/schemas/evidence.schema.json` requires `test.decoder` to be a
string or `null`. The Wazuh API's `/logtest` response returns `decoder` as
an object (`{"name": "pdp-pgaudit", "parent": "pdp-pgaudit"}`), and the
harness passed that object straight through
(`"decoder": output.get("decoder")`) instead of extracting the name.

**Fix:** `"decoder": (output.get("decoder") or {}).get("name")`.

## Verification after the fix

Re-ran the harness (fresh run, previous `results/` output cleared first):

- All 13 cases: `"result": "PASS"` (rule IDs matched expectations
  exactly, same as the CLI-based runs in
  `LOGTEST_EVIDENCE_2026-09-23.md`/`TELEMETRY_HEALTH_EVIDENCE_2026-09-23.md`).
- **All 13 generated evidence documents validated successfully** against
  `framework/schemas/evidence.schema.json` (`Draft202012Validator`,
  fetched and checked individually, not just spot-checked).
- Session-based correlation cases (`CASE-005`, `CASE-007`, `CASE-009`)
  correctly reused the same `/logtest` session token across all lines of
  their fixture and closed the session afterward
  (`DELETE /logtest/sessions/{token}`).

## What this validates

- The Wazuh Server API `/logtest` transport (`HARNESS.yml`'s "preferred"
  transport, over the `wazuh-logtest` CLI fallback used elsewhere in this
  lab pass) works end to end against a real Wazuh 4.14.7 server.
- The harness produces genuinely schema-valid, normalized evidence —
  closing the "API harness produces normalized evidence" item in
  `release/PRE_1_0_CHECKLIST.md` section E.
- Traceability (`requirements`/`controls`/`legal_requirements`) is
  correctly pulled from `tools/assessment/WAZUH_EVIDENCE_MAPPING.yml` for
  every test ID used across all rule families exercised in this lab pass
  (PostgreSQL, authentication, privileged access, telemetry health).

## Secondary finding — unrelated data-quality bug in `WAZUH_EVIDENCE_MAPPING.yml`

While reviewing the mapping file to confirm every `HARNESS.yml` test ID
resolves to a real entry, `WZ-RUL-PG-005`'s `default_event_context`
carried a legal-disclaimer sentence in its `technical_priority` field
instead of a priority level (`LOW`/`MEDIUM`/`HIGH`, as every sibling
entry uses):

```yaml
technical_priority: Potential exfiltration is not automatically a legally confirmed Personal Data breach.
```

This field is not currently consumed by any script in `tools/` (confirmed
via `grep -rn default_event_context tools/`), so it did not affect this
run's output, but is a real latent defect for whenever a consumer is
added. **Fixed** by setting `technical_priority: HIGH` (matching the
severity of every other `PDP-EVT-EXF-001`-adjacent entry) and moving the
disclaimer text to a YAML comment.
