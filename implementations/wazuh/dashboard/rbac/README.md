# Role-based access model for the PDP compliance dashboard

Status: **live-tested 2026-09-24, partially working, rolled back.** See
`release/runtime-validation/dashboard/RBAC_EVIDENCE_2026-09-24.md`.
`pdp_dashboard_viewer` (read-only) is confirmed correct. `pdp_dashboard_editor`
is **not yet correct**: `crud` on `.kibana`/`.kibana_*` does not grant
working access to the Dashboards saved-objects application layer (neither
read nor write worked via the real `/api/saved_objects/...` path) —
plain index-level permissions on the alias/concrete `.kibana*` index are
not sufficient; some additional Dashboards-specific permission is
missing. Do not re-apply this config to a live environment until that gap
is resolved and retested.

## Model

Two roles, both least-privilege relative to Wazuh's own defaults (which
otherwise only offer `admin` full access or the built-in `kibana_read_only`
with no data-index scoping):

| Role | Read `pdp-*` data | Write `pdp-*` data | Edit dashboards/visualizations |
|---|---|---|---|
| `pdp_dashboard_viewer` | Yes | No | No |
| `pdp_dashboard_editor` | Yes | No | Yes |

Neither role can write to `pdp-evidence-*`, `pdp-assessment-*`, or
`pdp-findings-*` under any circumstance. Those indices are populated only
by the pipeline (`tools/evidence/register_evidence.py`,
`tools/assessment/assess_controls.py`, `tools/findings/generate_findings.py`)
via the `admin`/service credentials used for ingestion. A dashboard user
being able to edit a *visualization* must never translate into being able
to edit the *evidence* it's built from -- that would let a viewer of the
compliance posture also quietly alter the record the posture is based on.
Neither role has any access to Wazuh's own SIEM indices
(`wazuh-alerts-*`, `wazuh-monitoring-*`, etc.) -- a compliance stakeholder
using this dashboard has no legitimate need for raw security-event access
scoped beyond what the PDP dashboard itself surfaces.

Files:
- `roles.yml` -- the two role definitions (`pdp_dashboard_viewer`, `pdp_dashboard_editor`).
- `roles_mapping.yml` -- maps backend roles `pdp_viewer`/`pdp_editor` to them, plus maps `pdp_viewer` to the built-in `kibana_read_only` role as defense in depth.

Both are **additive snippets** meant to be appended to the target Wazuh
Indexer's existing `/etc/wazuh-indexer/opensearch-security/roles.yml` and
`roles_mapping.yml` -- never used to replace those files, which already
contain Wazuh's own required reserved roles.

## Applying this

1. Back up the three security config files first:
   ```bash
   sudo cp /etc/wazuh-indexer/opensearch-security/roles.yml{,.bak}
   sudo cp /etc/wazuh-indexer/opensearch-security/roles_mapping.yml{,.bak}
   sudo cp /etc/wazuh-indexer/opensearch-security/internal_users.yml{,.bak}
   ```
2. Append the contents of `roles.yml` and `roles_mapping.yml` (this
   directory) to the corresponding live files.
3. Create a test user for each role in `internal_users.yml`. Generate a
   password hash with the indexer's own bundled tool (requires its
   bundled JDK on `JAVA_HOME`/`OPENSEARCH_JAVA_HOME`, since it does not
   ship on `PATH` by default):
   ```bash
   sudo env OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk \
     /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p '<a-fresh-test-password>'
   ```
   Then add, e.g.:
   ```yaml
   pdp_viewer_test:
     hash: "<hash output>"
     reserved: false
     backend_roles:
     - "pdp_viewer"
     description: "PDP RBAC test user - dashboard viewer"

   pdp_editor_test:
     hash: "<hash output>"
     reserved: false
     backend_roles:
     - "pdp_editor"
     description: "PDP RBAC test user - dashboard editor"
   ```
4. Apply with `securityadmin.sh` (this reloads the security config
   cluster-wide; it does not require restarting the indexer):
   ```bash
   sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh \
     -cd /etc/wazuh-indexer/opensearch-security/ \
     -icl -key /etc/wazuh-indexer/certs/admin-key.pem \
     -cert /etc/wazuh-indexer/certs/admin.pem \
     -cacert /etc/wazuh-indexer/certs/root-ca.pem \
     -h 127.0.0.1 -p 9200 -nhnv
   ```

## Test procedure

Verify each new role does exactly what it should and nothing more --
against the real indexer, with real `pdp-*` documents already indexed
(see `INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`):

```bash
# Viewer: read on pdp-* must succeed
curl -k -u pdp_viewer_test:<password> \
  "https://<indexer-host>:9200/pdp-evidence-*/_search?size=1"
# -> expect 200

# Viewer: write to pdp-* must be denied
curl -k -u pdp_viewer_test:<password> -X POST \
  "https://<indexer-host>:9200/pdp-evidence-test/_doc" -d '{"x":1}' -H 'Content-Type: application/json'
# -> expect 403

# Viewer: write to .kibana (saving a visualization) must be denied
curl -k -u pdp_viewer_test:<password> -X POST \
  "https://<indexer-host>:9200/.kibana/_doc" -d '{"x":1}' -H 'Content-Type: application/json'
# -> expect 403

# Editor: read on pdp-* must succeed
curl -k -u pdp_editor_test:<password> \
  "https://<indexer-host>:9200/pdp-evidence-*/_search?size=1"
# -> expect 200

# Editor: write to pdp-* must still be denied (evidence is pipeline-managed)
curl -k -u pdp_editor_test:<password> -X POST \
  "https://<indexer-host>:9200/pdp-evidence-test/_doc" -d '{"x":1}' -H 'Content-Type: application/json'
# -> expect 403

# Editor: write to .kibana (saving a visualization) must succeed
curl -k -u pdp_editor_test:<password> -X POST \
  "https://<indexer-host>:9200/.kibana/_doc" -d '{"x":1}' -H 'Content-Type: application/json'
# -> expect 200/201
```

Delete any test document written by the last check afterward.

## Scope and limitations

- This model assumes multitenancy is disabled
  (`PDP_MULTITENANCY_ENABLED=false`, the framework's default -- see
  `release/runtime-validation/dashboard/validate_real_import.py`), so
  saved objects live in the single global `.kibana*` index rather than a
  per-tenant index. If multitenancy is enabled, `tenant_permissions`
  must additionally be granted for whichever tenant holds the PDP
  dashboard.
- Field-level security (masking specific fields within `pdp-*` documents,
  e.g. hiding `pdp.asset_id` from a viewer role) was not designed here --
  the current model is index-level only. Add `fls`/`masked_fields` to
  `roles.yml` if a future requirement needs that.
- No SSO/external identity provider integration was tested; roles are
  assigned via `backend_roles` on internal users. Mapping an external
  IdP's group claim to `pdp_viewer`/`pdp_editor` backend roles is
  supported by OpenSearch Security but out of scope for this pass.
