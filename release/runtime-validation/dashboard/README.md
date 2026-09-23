# Dashboard / Index Import Validation

This is the real runtime gate for:

- `pdp-evidence-*`
- `pdp-assessment-*`
- `pdp-findings-*`
- OpenSearch Dashboards/Wazuh Dashboard saved-object import

OpenSearch Dashboards exposes `/api/saved_objects/_import` and requires the `osd-xsrf` header. A HTTP 200 alone is not enough: the response `success` field must be checked.

## Run

```bash
export PDP_INDEXER_URL=https://127.0.0.1:9200
export PDP_INDEXER_USER=admin
export PDP_INDEXER_PASSWORD='...'

export PDP_DASHBOARD_URL=https://127.0.0.1
export PDP_DASHBOARD_USER=admin
export PDP_DASHBOARD_PASSWORD='...'

export PDP_VERIFY_TLS=false
export PDP_SECURITY_TENANT=global
# Only set to true if the target's opensearch_dashboards.yml has
# opensearch_security.multitenancy.enabled: true (Wazuh's default is
# false -- see implementations/wazuh/DEPLOYMENT.md section 4).
export PDP_MULTITENANCY_ENABLED=false

python3 release/runtime-validation/dashboard/validate_real_import.py
```

The script:

1. connects to the real indexer,
2. installs the three PDP index templates,
3. creates temporary matching indices,
4. imports the dashboard NDJSON,
5. verifies the saved index patterns and dashboard are discoverable,
6. deletes validation indices,
7. writes `RESULT.json`.

## Dashboard content

`pdp-dashboard-shell.ndjson` (filename kept for compatibility with
`validate_real_import.py`'s path constant) now contains the full
eight-panel dashboard built from
`implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`: 3 index patterns, 8
classic (vislib/table) visualizations — one per `PDP-DASH-00N` entry in
the spec — and the dashboard itself wiring them into a 2-column, 4-row
layout. Built and import-tested against a real Wazuh 4.14.7 Dashboard,
2026-09-23 — see
`release/runtime-validation/dashboard/DASHBOARD_PANELS_EVIDENCE_2026-09-23.md`.

If the spec in `DASHBOARD_SPEC.yml` changes, regenerate the NDJSON to
match (there is no automated generator committed yet; the current file
was built with a one-off script during that validation pass) and re-run
this import gate against the target.
