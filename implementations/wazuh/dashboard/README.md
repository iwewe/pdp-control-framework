# PDP Dashboard Design v0.9

Wazuh Dashboard supports creating custom visualizations and combining them into dashboards. Custom index patterns are also supported. citeturn495925search0turn495925search1

The framework dashboard intentionally uses three dedicated index patterns:

```text
pdp-evidence-*
pdp-assessment-*
pdp-findings-*
```

## Top-level view

```text
+------------------------------------------------------+
| PDP Continuous Control Dashboard                     |
+------------------------------------------------------+
| PASS | FAIL | REVIEW | N/A | Evidence Health         |
+------------------------------------------------------+
| Open Findings by Severity                            |
+------------------------------------------------------+
| Controls Requiring Review                            |
+------------------------------------------------------+
| Processing Activity | Control | State | Coverage      |
+------------------------------------------------------+
| Evidence Quality | Telemetry / Event Trend           |
+------------------------------------------------------+
```

## Important language

Use:

```text
Control Assessment State
Evidence Coverage
Evidence Health
Continuous Monitoring Coverage
Open Findings
```

Avoid:

```text
UU PDP compliance %
Legal compliance score
Article violation count
```

unless a separate authorized legal assessment explicitly produces that conclusion.

## Time range

All three index patterns set `@timestamp` as their time field, which
means **every** panel here — not just a timeseries one — is filtered by
the dashboard's active time-range picker, not just its own query. The
generated dashboard object (`generate_dashboard_ndjson.py`) sets
`timeRestore: true` with a wide default (`now-90d` to `now+7d`) so it
shows its full working data set on a fresh open, rather than silently
inheriting whatever the viewer's own global time-picker default is
(this framework found real data go missing in a real lab under exactly
this: an "all 8 panels empty" report that was actually just a `last
24h` default hiding a month of data — see
`release/runtime-validation/dashboard/DASHBOARD_TIME_RANGE_EVIDENCE_2026-09-24.md`).
Note that `timeRestore` only applies on a fresh navigation to the
dashboard; a browser tab already open with an explicit time range in
its URL keeps using that range even after a plain refresh.

## Recommended access model

Different users may require different privileges:

- Security operators: evidence and technical findings
- Privacy reviewers: assessment + processing context
- Legal reviewers: traceability and review queue
- Auditors: read-only evidence/assessment registry
- Administrators: index/dashboard management

This should be enforced using the indexer's role-based access controls in the deployment.
