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

python3 release/runtime-validation/dashboard/validate_real_import.py
```

The script:

1. connects to the real indexer,
2. installs the three PDP index templates,
3. creates temporary matching indices,
4. imports the dashboard shell NDJSON,
5. verifies the saved index patterns and dashboard are discoverable,
6. deletes validation indices,
7. writes `RESULT.json`.

## Dashboard shell versus final dashboard

`pdp-dashboard-shell.ndjson` validates saved-object compatibility and index-pattern import.

The full eight-panel design is still defined by:

```text
implementations/wazuh/dashboard/DASHBOARD_SPEC.yml
```

For 1.0, build the eight panels on the target 4.14.7 dashboard, export them with related objects, commit the resulting NDJSON, and run this import gate against that export.
