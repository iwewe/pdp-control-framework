# 1.0.0 - First stable release

## Completed

This release finishes the validation work started in the 0.10.0-rc2
release-readiness pass (see `release/CHANGELOG_0.10.0-rc2.md` for that
much larger body of work — the legal-source re-review, the real Wazuh
4.14.7 runtime validation, and the initial dashboard/index import
gate). 1.0.0 closes the remaining gaps identified after that pass:

- **SCA check-ID collision audit**: `implementations/wazuh/sca/pdp_linux_baseline.yml`'s
  check IDs (910001-910006) audited against the full range of all
  ~70 Wazuh-bundled vendor SCA policies (1000-40165). No collision.
- **RBAC under `opensearch_security.multitenancy.enabled: true`**: the
  live-tested `pdp_dashboard_viewer`/`pdp_dashboard_editor` roles
  (`implementations/wazuh/dashboard/rbac/roles.yml`) retested with
  multitenancy enabled; all 6 checks passed unchanged, then reverted to
  the framework default (disabled).
- **Document-volume behavior**: 1,166 synthetic evidence/assessment/finding
  documents indexed across the three `pdp-*` indices; index templates
  and dashboard-panel-style aggregations both correct and fast (<50ms).
- **Saved-object persistence across a plain restart**: confirmed safe
  across 2 restart cycles with no package upgrade involved, narrowing
  the previously documented restart data-loss risk specifically to the
  upgrade path (`implementations/wazuh/DEPLOYMENT.md` section 4).
- **Dashboard browser rendering**: the automated pass could only verify
  the 8 panels' aggregations via the saved-objects/search APIs, not an
  actual browser session (blocked by lab-host RAM headroom for a
  headless browser). The project owner opened the dashboard directly in
  their own browser (steps in `implementations/wazuh/DEPLOYMENT.md`
  section 5) and confirmed it renders correctly.

Full evidence: `release/runtime-validation/dashboard/ADDITIONAL_VALIDATION_2026-09-24.md`
and the `SCA_EVIDENCE_2026-09-23.md` addendum.

## Release exception recorded, not a defect

The project owner explicitly decided, 2026-09-24, to proceed to 1.0
without an independent external legal counsel review and without an
independent re-check for enacted implementing regulations (Peraturan
Pemerintah), treating the completed authoritative-text review
(`framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md`) as
sufficient current legal guidance for this release. See
`framework/legal/review/LEGAL_REVIEW_STATUS.yml` and
`release/PRE_1_0_CHECKLIST.md` section H "Documented release
exceptions" for the formal record. This is scoped to this release only.

## Deliberately out of scope

SSO/external identity provider integration for the RBAC backend roles
(see `implementations/wazuh/dashboard/rbac/README.md` "Scope and
limitations").

## Release metadata

- `VERSION`: `0.10.0-rc2` -> `1.0.0`
- `FRAMEWORK_MANIFEST.yml`: `status` `RELEASE_CANDIDATE` -> `RELEASED`;
  `release_requirements.real_wazuh_4_14_7_runtime_validation_complete`
  and `real_dashboard_import_validation_complete` flipped to `true`.
- `release/compatibility/COMPATIBILITY_MATRIX.yml`: all lab-validated
  targets (Wazuh central components/agent, Ubuntu, PostgreSQL, pgAudit)
  promoted from `TARGET` to `LAB_VALIDATED`.
- `release/RELEASE_READINESS_0.10.0-rc2.yml` renamed to
  `release/RELEASE_READINESS_1.0.0.yml`.
