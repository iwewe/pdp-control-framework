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

## Conclusion (v1 test)

- `implementations/wazuh/dashboard/rbac/roles.yml`'s **`pdp_dashboard_viewer`
  role is confirmed correct** for its intended purpose (read `pdp-*`,
  cannot write anything) — the read-only index-level tests all passed.
  (Its inability to actually *open the dashboard* was a separate,
  previously-unnoticed gap — see the research below.)
- **`pdp_dashboard_editor`'s dashboard-editing half is not yet correct.**
  Raw `crud` on `.kibana*`/`.kibana`/`.kibana_*` does not grant working
  access to the Dashboards saved-objects application layer, for either
  read or write.
- **Do not re-apply this RBAC config to a live environment as-is.** Treat
  `pdp_dashboard_editor` as still in design, not validated.

## Root-cause research (2026-09-24, later same day, research only — no server changes)

Compared the v1 role definitions against OpenSearch Security's own
authoritative reference role,
[`kibana_user`](https://github.com/opensearch-project/security/blob/main/src/main/resources/static_config/static_roles.yml)
(the project's own "minimum permissions for a kibana user" role):

```yaml
kibana_user:
  cluster_permissions:
    - "cluster_composite_ops"          # read-WRITE, not the _ro variant
  index_permissions:
    - index_patterns: [".kibana", ".kibana-6", ".kibana_*", ...]
      allowed_actions: ["delete", "index", "manage", "read", "indices_all"]
```

Two concrete differences from v1, most likely in order of impact:

1. **v1 used `cluster_composite_ops_ro`** (read-only composite cluster
   ops) for both roles; the reference role uses the write-capable
   `cluster_composite_ops`. Wazuh/OpenSearch Dashboards' saved-objects
   backend appears to route requests through composite operations
   (`_bulk`/`_msearch`) even for single-object reads/writes — the `_ro`
   variant cannot satisfy a write via that path, which is consistent with
   why a *direct* single-document write straight to the concrete
   `.kibana_1` index (not a composite op, and not going through the
   Dashboards backend at all) succeeded in the v1 test while the
   equivalent write through `/api/saved_objects/...` did not.
2. **v1 granted only `"crud"`** on `.kibana*` for the editor (and nothing
   at all for the viewer); the reference role grants
   `["delete","index","manage","read","indices_all"]`. `"manage"` in
   particular (index-admin actions) is absent from `"crud"` and may be
   needed for saved-objects operations that touch the `.kibana` index's
   own mapping/settings.

**v2 fix, applied to the repo files but not yet live-tested:**
`implementations/wazuh/dashboard/rbac/roles.yml` and `README.md` updated
to use `cluster_composite_ops` for both roles; the viewer now gets an
explicit read-only `.kibana`/`.kibana_*` grant (previously missing
entirely, meaning it likely could never have opened the dashboard either
— untested in the v1 pass since the only `.kibana` check for the viewer
was a write-deny test, which trivially passes whether or not read access
also exists); the editor's `.kibana`/`.kibana_*` actions widened to
`["delete","index","manage","read"]` (stopping short of the reference
role's very broad `"indices_all"`, to stay closer to least privilege as a
first attempt).

The README's test procedure was also corrected: the v1 procedure tested
the editor's `.kibana` write directly against port 9200, which is not the
access path a real dashboard user goes through and is why the gap wasn't
caught at design time. The revised procedure tests view/edit access
through the actual Dashboards saved-objects API (port 443) instead,
alongside the port-9200 index-level checks for the data-protection half.

**This v2 design has not been live-tested.** The next step is to repeat
the live-test procedure in `README.md` against the real lab and record
the result in a new dated evidence file before checking off
`release/PRE_1_0_CHECKLIST.md` section F's RBAC item.

See `release/PRE_1_0_CHECKLIST.md` section F for how this is reflected in
overall release status.
