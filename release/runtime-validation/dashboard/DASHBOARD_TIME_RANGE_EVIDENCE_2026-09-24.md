# Dashboard Time-Range Bug — Found and Fixed, 2026-09-24

Found on the same real Wazuh 4.14.7 lab used throughout this project
(manager + Wazuh Indexer/Dashboard 4.14.7, Ubuntu 24.04.4 LTS), after
1.0.0 was tagged, while smoke-testing the dashboard with 31 synthetic
`pdp-*` documents (25 initial + 6 supplement, spread across
2026-08-27 through 2026-09-26 so every panel's grouping field had full
enum coverage — see the two `gen_*` scripts used to build them,
not committed to the repository since they are one-off test-data
generators, not framework content).

## Symptom

All 8 panels rendered **"No results found"** in a real browser, even
though:

- the underlying data existed and every aggregation returned correct,
  non-empty buckets when queried directly against the Indexer
  (confirmed via raw `_search` calls for panels 1, 2, 3, 6, 7 before
  this fix),
- the saved-objects import reported `"overall": "PASS"`,
- the index patterns' field discovery (`/api/index_patterns/_fields_for_wildcard`)
  correctly listed every field the panels aggregate on, including
  `@timestamp`.

## Root cause

Every panel is built against one of the three index patterns
(`implementations/wazuh/dashboard/generate_dashboard_ndjson.py`), and
all three set `timeFieldName: "@timestamp"`. In OpenSearch Dashboards,
**any** panel tied to a time-based index pattern is filtered by the
dashboard's global time-range picker, regardless of whether that panel
is itself a timeseries visualization — this applies to the pie, bar,
and table panels (2, 3, 4, 5, 6, 8) just as much as the one actual
timeseries panel (7).

The dashboard's saved object had `"timeRestore": false` and no
`timeFrom`/`timeTo`, so opening it inherited whatever the viewer's
*own* global time-picker default was — on this lab, the advanced
setting `timepicker:timeDefaults` was `{"from":"now-24h","to":"now"}`.
The synthetic test data (like most real evidence in a running
deployment) spans well outside a 24-hour window, so almost none of it
was visible.

Confirmed directly against the Indexer:

```json
// GET pdp-evidence-*,pdp-assessment-*,pdp-findings-*/_search
// {"aggs":{"minmax":{"stats":{"field":"@timestamp"}}}}
{"min_as_string": "2026-08-27T09:55:56.726Z", "max_as_string": "2026-09-26T15:21:40.930Z"}
```

vs. the active default range of `now-24h` to `now` (lab time at
diagnosis: 2026-09-24T11:07 UTC) — almost the entire dataset fell
outside it.

## Fix

`implementations/wazuh/dashboard/generate_dashboard_ndjson.py`'s
dashboard object now sets:

```python
"timeRestore": True,
"timeFrom": "now-90d",
"timeTo": "now+7d",
```

so the dashboard shows its full working data set on open, independent
of the viewer's own time-picker default. Regenerated
`implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson`
and re-imported via `implementations/wazuh/dashboard/install_indexer_dashboard.sh`
against the real lab; the saved dashboard object now confirmed carrying
`timeRestore: true, timeFrom: now-90d, timeTo: now+7d`.

## Known caveat: browser URL state can still override this

`timeRestore` only takes effect on a **fresh** navigation to the
dashboard. OpenSearch Dashboards persists the active time range in the
browser URL's `_g` query parameter; if a browser tab already has the
dashboard open (or bookmarked) with an explicit old time range in that
URL, that URL state takes precedence over the saved object's
`timeRestore`/`timeFrom`/`timeTo`, and a plain page refresh (F5) will
not clear it.

This is exactly what was still observed after the fix was deployed:
querying the Indexer directly with the new `now-90d`/`now+7d` bounds
confirmed all 8 panels' data was present and correct, but the
already-open browser tab still showed "No results found" until the
time range was set manually or the dashboard was re-opened fresh from
the Dashboards listing page (menu ☰ → **Dashboards** → click **"PDP
Continuous Control Dashboard"** again, rather than reusing an
already-open tab). Documented as an operator note in
`implementations/wazuh/DEPLOYMENT.md` section 5, since anyone verifying
the dashboard in a browser they already had open will hit this.

## Verification

```json
// GET pdp-assessment-*/_search, filtered to @timestamp in [now-90d, now+7d]
{"hits":{"total":{"value":11}}, "aggregations":{"result":{"buckets":[
  {"key":"REVIEW","doc_count":5},{"key":"PASS","doc_count":3},
  {"key":"FAIL","doc_count":2},{"key":"NOT_APPLICABLE","doc_count":1}
]}}}
```

Matches the full assessment document count (11 of 12; the one
unmatched document is `ASM-example-001`, an earlier example predating
the `@timestamp` indexing convention introduced by
`tools/export/export_bulk_ndjson.py` — expected, not a defect).
