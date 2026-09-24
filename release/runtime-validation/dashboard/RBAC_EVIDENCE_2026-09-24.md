# RBAC Live Test Evidence — 2026-09-24

**Target:** same Wazuh Indexer/Dashboard 4.14.7 lab as
`INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`.

**Outcome: the two-role design in `implementations/wazuh/dashboard/rbac/`
does not fully work as tested, and was rolled back.** This is a design
gap to fix, not a live-environment problem — the change was backed out
cleanly and the lab is back to its pre-test state.

## Method

Followed `implementations/wazuh/dashboard/rbac/README.md` exactly:
backed up the three live security config files (`roles.yml`,
`roles_mapping.yml`, `internal_users.yml`), appended the `roles.yml` /
`roles_mapping.yml` snippets, created two internal test users
(`pdp_viewer_test`, `pdp_editor_test`) with freshly generated random
passwords (never printed to any terminal transcript), and reloaded via
`securityadmin.sh` (`Done with success`).

## Results

### Index-level tests (README's documented test procedure, run against port 9200 directly)

| Test | Expected | Actual |
|---|---|---|
| Viewer read `pdp-*` | 200 | **200 — PASS** |
| Viewer write `pdp-*` | 403 | **403 — PASS** |
| Viewer write `.kibana` | 403 | **403 — PASS** |
| Editor read `pdp-*` | 200 | **200 — PASS** |
| Editor write `pdp-*` | 403 | **403 — PASS** |
| Editor write `.kibana` (alias) | 200/201 | **403 — FAIL** |

5 of 6 passed. The data-protection half of the design (nobody but the
pipeline can write `pdp-evidence-*`/`pdp-assessment-*`/`pdp-findings-*`,
under any role) works exactly as intended and is the more
safety-critical half.

### Investigating the `.kibana` write failure

- `.kibana` is an **alias** to a concrete index `.kibana_1`
  (`_cat/aliases` confirmed this). Writing directly to the concrete index
  `.kibana_1` as the editor passed the permission check (it then hit an
  unrelated `strict_dynamic_mapping_exception` from the test payload's
  bogus `x` field — meaning permission was actually granted, only the
  document shape was invalid). Writing to the alias `.kibana` failed with
  a `security_exception` both with the original `.kibana*` wildcard
  pattern and with an explicit non-wildcard `.kibana`/`.kibana_*` pair —
  ruling out a glob-matching mistake.
- Checked `plugins.security.system_indices.*` in `opensearch.yml`: `.kibana*`
  is **not** in the protected system-indices list, ruling out hardcoded
  system-index protection as the cause.
- Retested through the **real access path** a dashboard user actually
  uses — the Dashboard's own saved-objects API on port 443
  (`/api/saved_objects/...`), not a raw write to port 9200 — since that is
  how `release/runtime-validation/dashboard/validate_real_import.py`
  itself performs saved-object writes, and is what an actual editor would
  do through the UI. Result was the same failure, and additionally: **the
  editor role could not even *read* dashboards** via
  `/api/saved_objects/_find?type=dashboard` (403), despite having `crud`
  (which includes read) on `.kibana*`.
- This means the gap is not specific to the *write* action or to alias
  resolution — plain index-level `crud`/`read` permission on `.kibana*`
  is not sufficient for the Dashboards application layer to grant access
  at all. Wazuh/OpenSearch Dashboards likely requires an additional,
  Dashboards-specific permission (a cluster permission or action group
  beyond raw index CRUD) that this design did not include.
- One diagnostic attempt (temporarily widening the editor role's
  `.kibana`/`.kibana_*` permission to `"*"` to isolate whether this was an
  action-name gap) was **correctly blocked by the session's own safety
  guardrail** before it reached the server, since it would have granted
  overly broad access to a live security role. That path was not pursued
  further.

## Rollback

All three security config files were restored from the
`*.bak-20260924141631` backups taken at the start of this test, and
`securityadmin.sh` was re-run to reload the restored (original) config.
Confirmed: `pdp_viewer_test` credentials no longer authenticate (401), and
zero references to any PDP RBAC role/user remain in the live
`roles.yml`/`roles_mapping.yml`/`internal_users.yml`. The temporary test
index (`pdp-evidence-rbactest`) and local password files were deleted.
**The lab is back to exactly its pre-RBAC-test state.**

## Conclusion

- `implementations/wazuh/dashboard/rbac/roles.yml`'s **`pdp_dashboard_viewer`
  role is confirmed correct** for its intended purpose (read `pdp-*`,
  cannot write anything) — the read-only index-level tests all passed.
- **`pdp_dashboard_editor`'s dashboard-editing half is not yet correct.**
  Raw `crud` on `.kibana*`/`.kibana`/`.kibana_*` does not grant working
  access to the Dashboards saved-objects application layer, for either
  read or write. This needs further design research (likely an
  OpenSearch/Wazuh-Dashboards-specific cluster permission or action group
  is missing) before being retested live.
- **Do not re-apply this RBAC config to a live environment as-is.** Treat
  `pdp_dashboard_editor` as still in design, not validated.

See `release/PRE_1_0_CHECKLIST.md` section F for how this is reflected in
overall release status.
