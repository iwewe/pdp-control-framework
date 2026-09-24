# Additional Post-RBAC Validation — 2026-09-24

Follow-up validation of items left open after the RBAC v3 success
(`RBAC_EVIDENCE_2026-09-24.md`), on the same lab (Wazuh 4.14.7 manager +
Wazuh Indexer/Dashboard 4.14.7, Ubuntu 24.04.4 LTS).

## 1. Dashboard saved-objects persistence across a plain restart

Prior testing (`INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`) found saved
objects did not survive a `wazuh-dashboard` restart that followed a
package upgrade, but that test never isolated whether a restart *alone*
(no upgrade) also loses data.

**Method:** captured saved-object counts, ran `systemctl restart
wazuh-dashboard` twice in a row (no package changes), and re-checked.

| Check | Before | After restart #1 | After restart #2 |
|---|---|---|---|
| Dashboards | 1 | 1 | 1 |
| Index patterns | 13 | 13 | 13 |

**Result: no data loss.** A plain restart does not reproduce the
data-loss risk; it is specific to the upgrade path already documented in
`implementations/wazuh/DEPLOYMENT.md` section 4. No new mitigation
needed beyond what's already written there, but the guidance there is
now more precisely scoped ("back up before an upgrade", not "back up
before every restart").

## 2. Indexing/aggregation behavior at realistic document volume

Prior testing only ever indexed 1 document per index. Generated and bulk
loaded 1,166 schema-valid synthetic documents (500 evidence, 500
assessment, 166 findings — all validated against their JSON Schemas
before indexing) into temporary `pdp-*-volumetest` indices, matching the
same three index templates used in production.

- `_bulk` import: `"errors": false` for all three batches (500, 500, 166
  items) — the index templates accept realistic volume without mapping
  issues.
- Ran the actual aggregation shapes used by 3 of the 8 dashboard panels
  (`DASHBOARD_SPEC.yml` PDP-DASH-001, -003, -006) against this data:

  | Panel-style query | Result | Latency |
  |---|---|---|
  | Assessment result distribution (PDP-DASH-001) | PASS 288 / FAIL 109 / REVIEW 55 / NOT_APPLICABLE 49 (501 total) | 16ms |
  | Open findings by severity, filtered `status: OPEN,IN_PROGRESS` (PDP-DASH-003) | HIGH 33 / CRITICAL 31 / MEDIUM 28 / LOW 24 (116 total) | 47ms |
  | Evidence quality-level distribution (PDP-DASH-006) | Q3: 501 | 1ms |

All bucket counts summed correctly to the expected totals; latency stayed
well under 50ms even on this modest 3.8GB-RAM lab host. Temporary indices
deleted after verification.

## 3. RBAC behavior with `opensearch_security.multitenancy.enabled: true`

The v3 RBAC fix (`tenant_permissions` for `global_tenant`) was validated
with multitenancy **disabled** (the framework's documented default). This
tested it **enabled** instead, to confirm the fix isn't order-dependent
on that flag.

**Method:** backed up `opensearch_dashboards.yml`, flipped
`opensearch_security.multitenancy.enabled` to `true`, restarted
`wazuh-dashboard`, recreated two fresh test users (`pdp_viewer_test`,
`pdp_editor_test`), and repeated the full RBAC test matrix.

| Check | Result |
|---|---|
| Viewer opens dashboard, **no** tenant header (default tenant) | **200 — dashboard found** |
| Viewer opens dashboard, explicit `securitytenant: global` | **200 — PASS** |
| Viewer creates a visualization | **403 — PASS (denied, as designed)** |
| Editor opens dashboard, explicit `securitytenant: global` | **200 — PASS** |
| Editor creates a visualization | **200/201 — PASS** |
| Editor writes `pdp-*` data (port 9200) | **403 — PASS (denied, as designed)** |

**All 6 checks passed**, including the case with no explicit tenant
header at all — the `global_tenant` grant continues to work with
multitenancy on, with no additional configuration needed.

**Cleanup:** deleted the test visualization, removed the two test users,
and **reverted `opensearch_security.multitenancy.enabled` back to
`false`** (framework default) with a final restart, confirmed via a
before/after saved-object count check and an `admin` access sanity check.

## Conclusion

All three follow-up items are resolved:

- Plain-restart persistence: confirmed safe, risk scope narrowed to the
  upgrade path only.
- Volume behavior: confirmed correct and fast at ~1,000 documents across
  the three index types.
- Multitenancy-enabled RBAC: confirmed the v3 fix works unchanged with
  multitenancy on, not just off.

See `release/PRE_1_0_CHECKLIST.md` and
`release/runtime-validation/dashboard/STATUS.yml` for how this is
reflected in overall release status.
