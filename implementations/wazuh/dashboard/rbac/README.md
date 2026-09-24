# Role-based access model for the PDP compliance dashboard

Status: **v1 live-tested 2026-09-24, editor gap found, rolled back. v2
(this version) revised based on research, not yet live-tested.** See
`release/runtime-validation/dashboard/RBAC_EVIDENCE_2026-09-24.md` for the
v1 test and root-cause research; re-test v2 per the procedure below
before marking this validated in `release/PRE_1_0_CHECKLIST.md`.

## What v1 got wrong, and why (root cause)

v1 granted `pdp_dashboard_viewer`/`pdp_dashboard_editor` `cluster_composite_ops_ro`
(read-only composite cluster ops) and, for the editor, plain `"crud"` on
`.kibana*`. Live testing found the editor could not read or write saved
objects via the real Dashboards API (`/api/saved_objects/...`, port 443)
at all, and the viewer — which had no `.kibana*` grant whatsoever in
v1 — could never have opened the dashboard either.

Comparing against OpenSearch Security's own authoritative reference role,
[`kibana_user`](https://github.com/opensearch-project/security/blob/main/src/main/resources/static_config/static_roles.yml)
(the role the project itself documents as "the minimum permissions for a
kibana user"):

```yaml
kibana_user:
  cluster_permissions:
    - "cluster_composite_ops"          # read-WRITE, not the _ro variant
  index_permissions:
    - index_patterns: [".kibana", ".kibana-6", ".kibana_*", ...]
      allowed_actions: ["delete", "index", "manage", "read", "indices_all"]
```

Two likely gaps in v1, in order of suspected impact:

1. **`cluster_composite_ops_ro` instead of `cluster_composite_ops`.**
   Wazuh/OpenSearch Dashboards' saved-objects backend appears to route
   requests through composite operations (`_bulk`/`_msearch`) even for
   single-object reads and writes. The `_ro` variant only allows
   *read* composite ops, so any write through the Dashboards API would
   be blocked at the cluster-permission level regardless of index-level
   permissions — while a *direct*, non-Dashboards write straight to the
   concrete `.kibana_1` index (as tested in
   `RBAC_EVIDENCE_2026-09-24.md`) succeeded, because a plain single-document
   `POST .../_doc` is not a composite operation and doesn't need this
   permission at all.
2. **`"crud"` instead of `["delete","index","manage","read"]` (or
   `"indices_all"`) on `.kibana*`.** `"crud"` may not include index-admin
   actions (`manage`) that the Dashboards backend needs for certain
   saved-objects operations (e.g. checking/updating the `.kibana` index's
   own mapping).

v2 (this version) narrows toward the reference role rather than adopting
it wholesale, to stay closer to least privilege:

- Both roles now use `cluster_composite_ops` (not `_ro`).
- `pdp_dashboard_viewer` now has a **read-only** grant on
  `.kibana`/`.kibana_*` (`["read", "indices:admin/mappings/get"]`) so it
  can actually open the dashboard — this was simply missing in v1.
- `pdp_dashboard_editor`'s `.kibana`/`.kibana_*` actions widened from
  `"crud"` to the reference role's explicit
  `["delete","index","manage","read"]`. The reference role's very broad
  `"indices_all"` catch-all was deliberately not adopted; add it as a
  fallback only if this narrower set is retested and still found
  insufficient.

**This has not been live-tested yet.** Treat it as an informed hypothesis
grounded in the OpenSearch Security project's own reference
implementation, not a confirmed fix, until retested.

## Model

Two roles, both least-privilege relative to Wazuh's own defaults (which
otherwise only offer `admin` full access or the built-in `kibana_read_only`
with no data-index scoping):

| Role | Read `pdp-*` data | Write `pdp-*` data | View dashboard/visualizations | Edit dashboards/visualizations |
|---|---|---|---|---|
| `pdp_dashboard_viewer` | Yes | No | Yes | No |
| `pdp_dashboard_editor` | Yes | No | Yes | Yes |

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
   sudo env OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk \
     /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh \
     -cd /etc/wazuh-indexer/opensearch-security/ \
     -icl -key /etc/wazuh-indexer/certs/admin-key.pem \
     -cert /etc/wazuh-indexer/certs/admin.pem \
     -cacert /etc/wazuh-indexer/certs/root-ca.pem \
     -h 127.0.0.1 -p 9200 -nhnv
   ```

## Test procedure

Test through the **real access paths** — index-level checks against port
9200 for the data-protection half (the more safety-critical property:
nobody but the pipeline can write PDP data), and the real Dashboards
saved-objects API on port 443 for the view/edit half, since that is what
an actual dashboard user goes through (the v1 test's direct
`.kibana`/port-9200 write check for the editor passed the wrong layer and
is why the v1 gap wasn't caught earlier). Run with real `pdp-*` documents
already indexed (see `INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`).

```bash
# --- Data-protection checks (port 9200, index-level) ---

# Viewer: read on pdp-* must succeed
curl -k -u pdp_viewer_test:<password> \
  "https://<indexer-host>:9200/pdp-evidence-*/_search?size=1"
# -> expect 200

# Viewer: write to pdp-* must be denied
curl -k -u pdp_viewer_test:<password> -X POST \
  "https://<indexer-host>:9200/pdp-evidence-test/_doc" -d '{"schema_version":"0.8"}' -H 'Content-Type: application/json'
# -> expect 403

# Editor: read on pdp-* must succeed
curl -k -u pdp_editor_test:<password> \
  "https://<indexer-host>:9200/pdp-evidence-*/_search?size=1"
# -> expect 200

# Editor: write to pdp-* must still be denied (evidence is pipeline-managed)
curl -k -u pdp_editor_test:<password> -X POST \
  "https://<indexer-host>:9200/pdp-evidence-test/_doc" -d '{"schema_version":"0.8"}' -H 'Content-Type: application/json'
# -> expect 403

# --- Dashboard application checks (port 443, real saved-objects API) ---

# Viewer: can open/view the dashboard
curl -k -u pdp_viewer_test:<password> \
  "https://<dashboard-host>:443/api/saved_objects/_find?type=dashboard&search=PDP&search_fields=title"
# -> expect 200 with the PDP dashboard in the results

# Viewer: cannot create/save a visualization
curl -k -u pdp_viewer_test:<password> -H 'osd-xsrf: true' -H 'Content-Type: application/json' \
  -X POST "https://<dashboard-host>:443/api/saved_objects/visualization/pdp-rbac-test-viz" \
  -d '{"attributes":{"title":"pdp-rbac-test-viz"}}'
# -> expect 403

# Editor: can open/view the dashboard
curl -k -u pdp_editor_test:<password> \
  "https://<dashboard-host>:443/api/saved_objects/_find?type=dashboard&search=PDP&search_fields=title"
# -> expect 200 with the PDP dashboard in the results

# Editor: can create/save a visualization
curl -k -u pdp_editor_test:<password> -H 'osd-xsrf: true' -H 'Content-Type: application/json' \
  -X POST "https://<dashboard-host>:443/api/saved_objects/visualization/pdp-rbac-test-viz" \
  -d '{"attributes":{"title":"pdp-rbac-test-viz"}}'
# -> expect 200/201
```

Delete any test document/visualization written by the last checks
afterward (`DELETE /api/saved_objects/visualization/pdp-rbac-test-viz`
with editor or admin credentials).

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
