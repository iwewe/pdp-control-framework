# Real Wazuh Indexer + Dashboard Import Evidence — 2026-09-23

**Target:** Wazuh Indexer 4.14.7 (OpenSearch 7.10.2-compatible API) + Wazuh
Dashboard 4.14.7, same lab host used for all prior phases (`hansip`,
Ubuntu 24.04.4 LTS).

**Method:** `release/runtime-validation/dashboard/validate_real_import.py`,
run against the real indexer/dashboard with the `admin` credentials
generated at install time (`~/wazuh-install-files.tar` →
`wazuh-passwords.txt`, extracted server-side and never printed to a
terminal transcript).

## Finding 1 (blocking, fixed) — `securitytenant` header breaks every request when multitenancy is disabled

The script's first run failed every dashboard-side check:

```
"error": {
  "message": "no permissions for [indices:data/write/bulk[s]] and User
  [name=admin, backend_roles=[admin], requestedTenant=global]"
}
```

...even though `admin` is mapped to the `all_access` reserved role (full
access to everything, confirmed via
`/etc/wazuh-indexer/opensearch-security/roles_mapping.yml`). The actual
cause: `/etc/wazuh-dashboard/opensearch_dashboards.yml` has
`opensearch_security.multitenancy.enabled: false` — multitenancy is off by
default on a fresh Wazuh install. The script was unconditionally sending a
`securitytenant: global` header on every request; the security plugin does
not expect that header when multitenancy is disabled, and misinterprets it
as a request for a tenant-scoped index the (admin) user has no explicit
tenant grant for.

**Fix:** confirmed via raw `curl` first (omitting the header fixed both
read and write calls immediately), then updated
`release/runtime-validation/dashboard/validate_real_import.py` to only
send `securitytenant` when a new `PDP_MULTITENANCY_ENABLED=true` env var is
set (default `false`). `.env.example` documents this.

## Finding 2 (blocking, fixed) — all three index templates were missing schema-required fields

Before touching the dashboard issue, indexing an actual schema-valid
example document into `pdp-evidence-*` was rejected:

```
"error": {"type": "strict_dynamic_mapping_exception",
  "reason": "mapping set to strict, dynamic introduction of [observed_at]
  within [_doc] is not allowed"}
```

`observed_at` is a **required** field in `framework/schemas/evidence.schema.json`
and is present in `examples/evidence.example.json` — a document that
already passes JSON Schema validation in CI
(`tools/validation/validate_evidence.py`) — yet the real OpenSearch index
template did not map it at all. A systematic comparison of all three
schemas against all three templates found:

| Template | Schema-defined fields missing from the mapping |
|---|---|
| `pdp-evidence-template.json` | `observed_at`, `collected_at`, `event.raw_reference`, `review.reviewer`, `review.notes`, `payload` (entirely unmapped) |
| `pdp-assessment-template.json` | `notes` |
| `pdp-findings-template.json` | `notes` |

Under `dynamic: strict`, every one of these caused a hard rejection the
moment a real, schema-conformant document included the field — meaning
**no genuinely valid evidence document could ever be indexed** before this
fix, despite CI's schema validation passing.

**Fix:**
- Added `observed_at`, `collected_at` (`date`), `event.raw_reference`
  (`keyword`), `review.reviewer` (`keyword`), `review.notes` (`text`) to
  `pdp-evidence-template.json`.
- Mapped `payload` as `{"type": "object", "enabled": false}` rather than
  enumerating sub-fields: `framework/schemas/evidence.schema.json` marks
  `payload` as `additionalProperties: true` by design ("Normalized,
  minimized technical evidence" whose shape varies per evidence-producing
  engine — Wazuh, IAM, database, manual, etc., per
  `docs/architecture/compliance-operating-model.md`). `enabled: false`
  stores the field verbatim (retrievable in `_source`) without indexing
  its arbitrary sub-fields or triggering `dynamic: strict` on them.
- Added `notes` (`text`) to `pdp-assessment-template.json` and
  `pdp-findings-template.json`.
- Bumped each template's `_meta.version` from `0.9.0-draft` to `0.10.0-rc2`.

Re-verified with a script that recursively flattens each JSON Schema's
`properties` and diffs against each template's mapping keys: zero missing
fields remain (`payload` intentionally excluded from the comparison, being
by-design schema-free).

## Verification after both fixes

`python3 release/runtime-validation/dashboard/validate_real_import.py`
(with `PDP_MULTITENANCY_ENABLED=false`, matching this lab's real config)
now reports **`"overall": "PASS"`** across every check:

- Indexer reachable.
- All 3 index templates accepted (`{"acknowledged":true}`).
- 3 temporary indices created against those templates.
- Dashboard saved-objects import: `successCount: 4` (3 index patterns +
  1 dashboard), `success: true`.
- All 4 saved objects discoverable via `_find`.
- Temporary indices cleaned up.

In addition, real schema-conformant example documents were indexed
directly (not just empty temp indices from the script) to prove the
*content*, not just the index creation, now works:

| Document | Index | Result |
|---|---|---|
| `examples/evidence.example.json` (unmodified) | `pdp-evidence-000001` | `"result":"created"` |
| `examples/finding.example.json` (unmodified) | `pdp-findings-000001` | `"result":"created"` |
| synthetic minimal valid assessment doc (no committed example exists yet — see `release/PRE_1_0_CHECKLIST.md` section E) | `pdp-assessment-000001` | `"result":"created"` |

`dynamic: strict` was re-confirmed still working correctly after the
fixes: a document with a genuinely unknown field
(`this_field_does_not_exist`) was still rejected with
`strict_dynamic_mapping_exception`, so the fix closed real gaps without
loosening the schema enforcement.

All manually-created test indices/documents above were deleted after
verification; the script's own temporary indices self-clean.

## What this validates

- All three index templates are now genuinely complete and accept real,
  schema-conformant documents from every layer (evidence, assessment,
  finding), not just syntactically-valid-but-incomplete ones.
- The dashboard saved-objects shell (3 index patterns + the empty
  8-panel-ready dashboard) is now actually imported into this lab's real
  Wazuh Dashboard and discoverable via the saved-objects API.
- `dynamic: strict` enforcement still rejects genuinely unexpected fields.

## What this does NOT yet validate

- The complete eight-panel dashboard (`implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`)
  — only the empty shell (`panelsJSON: "[]"`) was imported; building the
  real panels is a separate, larger design task.
- Role-based access control for the dashboard (not attempted; this lab
  used the `admin` superuser throughout).
- Behavior with `opensearch_security.multitenancy.enabled: true` (this
  lab's install has it disabled, which is Wazuh's own default).
