# Real Eight-Panel Dashboard Build Evidence — 2026-09-23

**Target:** Wazuh Dashboard 4.14.7 (same lab host as every prior phase).
**Source of truth:** `implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`
(8 `PDP-DASH-00N` panel definitions, unchanged by this work).

## What was built

`implementations/wazuh/dashboard/generate_dashboard_ndjson.py` — a new,
committed generator (not a one-off script) that reads
`DASHBOARD_SPEC.yml` and produces
`implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson`
containing:

- 3 `index-pattern` objects (`pdp-evidence-*`, `pdp-assessment-*`,
  `pdp-findings-*` — unchanged from the previous shell-only version).
- 8 `visualization` objects, one per spec panel, dispatched by the
  panel's `type` field:
  - `metric+distribution` / `bar` → classic vislib `histogram`.
  - `pie` → classic vislib `pie`.
  - `table` → classic `table` (nested `terms` aggregations per bucket
    field; `PDP-DASH-005`'s `coverage.coverage_percent` bucket is instead
    mapped to an `avg` metric, since it is a continuous field, not a
    discrete category).
  - `timeseries` → classic `line` (`date_histogram` on the panel's
    `time_field` with a `terms` split series).
  - Each panel's `filter` (where present, e.g. `PDP-DASH-003`'s
    `status: OPEN OR status: IN_PROGRESS`) is carried into the
    visualization's own KQL query, not applied only at the dashboard
    level.
- 1 `dashboard` object wiring all 8 visualizations into a 2-column,
  4-row grid (`w:24 h:15` per panel), with `panelRefName`/`references`
  resolving correctly (verified — see below).

This regenerated file is used **in place of** the previous empty-shell
NDJSON (same filename, so
`release/runtime-validation/dashboard/validate_real_import.py`'s path
constant did not need to change).

## Real-runtime validation performed

1. **Import:** `POST /api/saved_objects/_import?overwrite=true` with the
   generated NDJSON against the real Wazuh Dashboard —
   `"successCount": 12, "success": true`, all 12 objects (3 index
   patterns + 8 visualizations + 1 dashboard).
2. **Reference integrity on the live object:** fetched the dashboard back
   via `GET /api/saved_objects/dashboard/pdp-continuous-control-dashboard`
   and confirmed all 8 `panelsJSON` entries have a matching `references`
   entry resolving to the correct visualization ID, with the expected
   grid coordinates (2 columns × 4 rows).
3. **Aggregation correctness against the real indices:** ran each panel's
   underlying OpenSearch aggregation directly against
   `pdp-evidence-*`/`pdp-assessment-*`/`pdp-findings-*` (which held the
   one example document per index left in place from the prior phase) to
   confirm none of the eight aggregation definitions error against the
   real field mappings in `implementations/wazuh/indexer/templates/`:

   | Panel | Aggregation tested | Result |
   |---|---|---|
   | PDP-DASH-001 | `terms(result)` on `pdp-assessment-*` | `PASS: 1` |
   | PDP-DASH-002 | `terms(evidence_health)` | empty buckets (field not set on the one example doc — not an error) |
   | PDP-DASH-003 | `terms(severity)` filtered `status: OPEN OR IN_PROGRESS` | `HIGH: 1` |
   | PDP-DASH-004 | nested `terms` × 4 (processing activity → control → severity → status) | resolves 4 levels deep correctly |
   | PDP-DASH-005 | `avg(coverage.coverage_percent)` filtered `result: REVIEW` | `null` (no doc matches the filter — correct, not an error) |
   | PDP-DASH-006 | `terms(quality.level)` on `pdp-evidence-*` | `Q3: 1` |
   | PDP-DASH-007 | `date_histogram(@timestamp)` + `terms(event.taxonomy_ids)` | executes without error |
   | PDP-DASH-008 | `terms(test.id)` + `terms(traceability.requirements)` | executes without error |

4. **Reproducibility:** confirmed re-running
   `generate_dashboard_ndjson.py` against the current
   `DASHBOARD_SPEC.yml` reproduces byte-for-byte the same aggregation
   definitions, references, and panel grid as the version that was
   actually import-tested above (only the human-readable `description`
   text differs cosmetically, since the generator sources it from the
   spec's own `notes`/`principle` fields rather than a hand-written
   string used during initial testing). A CI step
   (`.github/workflows/validate.yml`, "Validate dashboard NDJSON is
   reproducible from DASHBOARD_SPEC.yml") now enforces this on every
   push: regenerate and fail if the committed file drifts from the spec.

## What this does NOT validate

- Actual browser rendering of each chart (Discover/Dashboard app were not
  driven via a real browser in this session; verification was via the
  saved-objects and search APIs). The classic visualization types used
  (`histogram`, `pie`, `table`, `line`) are all backed by plugins
  confirmed enabled in this install's `wazuh-dashboard` startup log
  (`visTypeVislib`, `visTypeTable`, `visTypeTimeseries`, ...).
- Behavior once each index holds a realistic volume of documents (all
  aggregations were exercised against exactly one document per index).
- The dashboard saved-objects persistence risk documented earlier in
  `INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md` (Finding 3) applies equally
  to this fuller version — back it up before any `wazuh-dashboard`
  restart/upgrade per `implementations/wazuh/DEPLOYMENT.md` section 4.
