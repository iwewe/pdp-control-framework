# Pre-1.0 Release Validation Checklist

Target release: **1.0.0**

This is a living release-state document. An item is checked only when there
is verifiable evidence for it (a passing CI check, a script re-run during
review, or a specific document); items that require a real runtime
(Wazuh/PostgreSQL/Indexer/Dashboard lab) stay unchecked until that runtime
evidence exists. Last synchronized against 0.10.0-rc2 on 2026-09-23.

## A. Legal layer

- [x] UU 27/2022 legal mapping reviewed against authoritative text. (`framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md`, `SOURCE_VERIFIED`)
- [x] Article/paragraph references independently checked against the official statutory text. (same review; corrected Article 35 letter-based citation, added 18 previously-implicit LR entries)
- [x] Constitutional Court Decision 151/PUU-XXII/2024 note reviewed. (incorporated into Article 53(1) interpretation; source archived in `docs/legal-sources/MK_151_PUU_XXII_2024_SOURCE.md`)
- [x] No control text claims more than the legal source supports. (`reports/MODEL_REVIEW_2026-09-23.md` — systematic keyword review of `framework/controls/CONTROL_CATALOGUE.yml` for overclaiming language; the handful of hits found were either accurately describing a legal trigger condition or accurately restating a legally-defined role's own duties, not overclaiming)
- [x] Legal summaries are clearly identified as framework interpretations. (added explicit `requirement_summary_disclaimer` to `framework/legal/LEGAL_MAPPING.yml` and `objective_disclaimer` to `framework/controls/CONTROL_CATALOGUE.yml`, 2026-09-23)
- [x] Any implementing regulations/guidance required for 1.0 scope are documented. (documented as an explicit **open** item in `framework/legal/review/LEGAL_REVIEW_STATUS.yml` — this framework has not confirmed whether any UU 27/2022 implementing regulation (Peraturan Pemerintah) has been enacted; "documented" here means the gap is tracked, not resolved)

> Note: the above is authoritative-**text** review, not independent external
> legal counsel review. `external_legal_counsel_review` remains
> `NOT_PERFORMED` (`framework/legal/review/LEGAL_REVIEW_STATUS.yml`).

## B. Control architecture

- [x] Every `PDP-*` control has at least one legal requirement mapping. (verified: 0 of 39 controls missing `legal_basis`; enforced going forward by `tools/validation/validate_release_consistency.py`)
- [x] Every `REQ-*` requirement maps to at least one PDP control. (verified: 0 of 31 requirements missing `supports_controls`)
- [x] Control IDs are stable and unique. (0 duplicate `PDP-*`/`REQ-*`/`LR-*`/test IDs; enforced in CI)
- [x] Assessment method/result semantics are consistent. (`reports/MODEL_REVIEW_2026-09-23.md` — cross-checked `assessment_method` values in `CONTROL_CATALOGUE.yml` (MANUAL/PARTIAL only), `assessment` values in `WAZUH_TEST_CATALOGUE.yml` (AUTOMATED only), and the `result` vocabularies in `evidence.schema.json` (5 values, includes ERROR) vs. `control-assessment.schema.json` (4 values, no ERROR — by design, since `assess_controls.py` folds evidence-level ERROR into assessment-level REVIEW, confirmed in `reports/TOOLS_PIPELINE_VALIDATION_2026-09-23.md`); all consistent)
- [x] `NOT_APPLICABLE` requires justification. (found the rule was documented in `docs/architecture/assessment-methodology.md` but **not enforced**: `framework/schemas/control-assessment.schema.json` accepted `result: NOT_APPLICABLE` with `notes: null`. Fixed 2026-09-23 by adding a conditional schema rule requiring a non-empty `notes` when `result` is `NOT_APPLICABLE`; verified it now rejects the unjustified case and accepts the justified one.)
- [x] No engineering score is described as a legal compliance score. (consistently disclaimed across README, coverage report, release readiness, and `implementations/wazuh/WAZUH_PROFILE.yml` boundary statement)

## C. Processing / applicability

- [x] Processing Activity model reviewed. (`reports/MODEL_REVIEW_2026-09-23.md` — `framework/models/PROCESSING_ACTIVITY_MODEL.md` reviewed for internal consistency; found `examples/processing-activity.example.yml` was missing 2 of the model's own "Minimum Required Fields" (`processing_operations`, `retention`) — fixed)
- [x] Asset model reviewed. (`framework/models/ASSET_MODEL.md` reviewed; internally consistent. Note: no dedicated committed asset example exists yet, unlike the other models — not required by this checklist item's wording, but worth adding later)
- [x] Control Profile composition tested with at least three realistic examples. (`reports/MODEL_REVIEW_2026-09-23.md` — found and fixed a real bug: the sole existing example's `effective_requirements` did not match the mathematically correct union of its 3 applied profiles' `required_requirements` (missing 5 requirements). Rewrote `examples/profile-application.example.yml` with 3 distinct realistic scenarios, each programmatically verified to equal the exact union)
- [x] High-risk processing profile reviewed. (`framework/profiles/CONTROL_PROFILES.yml`'s `PDP-PROFILE-HIGH-RISK` reviewed; confirmed no `REQ-*` maps to the DPIA controls `PDP-DPIA-001`/`PDP-DPIA-002` — correct, since DPIA is a documentary/organizational control with no generic technical requirement layer, consistent with `CONTROL_CATALOGUE.yml`)
- [x] Security monitoring platform dogfooding example completed. (the third scenario in the rewritten `examples/profile-application.example.yml` — `ASSET-WAZUH-MANAGER-001` under `PDP-PROFILE-SECURITY-MONITORING` — models the Wazuh manager/indexer/dashboard used to implement this very framework as an in-scope asset of its own framework)

## D. Wazuh implementation

- [x] Target Wazuh version pinned in compatibility matrix. (4.14.7, `release/compatibility/COMPATIBILITY_MATRIX.yml`)
- [x] Manager/indexer/dashboard version compatibility verified. (all three report `4.14.7-1` on the same host, 2026-09-23)
- [x] All custom rule IDs unique and within project-reserved range. (14 rule IDs, all within 100000-120000, enforced by `tools/validation/validate_structure.py`)
- [x] SCA YAML executes successfully. (`release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md` — all 6 checks in `pdp_linux_baseline.yml` executed on real Wazuh 4.14.7 + Ubuntu 24.04.4; every result independently reproduced with direct shell commands. No bug found.)
- [x] SCA policy produces real results when deployed via a centralized agent group (not just as a local policy). **Resolved** (`release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`, addendum section): the earlier "not applicable on all 6 checks" result was **not** an `sca.remote_commands` restriction — `sca.remote_commands=1` was already set correctly. Root cause was that the test agent (a minimal Docker container with no init system) never had `sshd`/`systemctl` installed at all; Wazuh's own vendor `cis_ubuntu24-04.yml` policy failed identically on the same commands on the same agent, confirming this was a lab-environment gap, not a defect in the PDP policy or in `sca.remote_commands` handling. After installing `openssh-server` (which also provided `systemctl` transitively) and restarting the agent, all 6 checks returned genuine PASS/FAIL results via the centralized group-pushed policy. No policy redesign to file-based (`f:`) checks is needed — Wazuh's own vendor policy uses the same `c:`-based pattern for equivalent checks.
- [x] Authentication fixtures validated with real `wazuh-logtest`. (`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`: both `ssh_failed_once.log` -> 110001 and the `ssh_failed_8.log` correlation -> 110002 matched exactly; `su_session_opened.log` -> 110101 and the repeated-3 correlation -> 110102 also matched)
- [x] FIM fixtures validated on Ubuntu 24.04. (`release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md` — live create/modify/delete against a realtime-monitored path, not a static fixture; found and fixed two rule bugs in the process, see that file and `implementations/wazuh/rules/pdp_fim.xml`)
- [x] Telemetry-health rules adapted to actual Wazuh events. (`release/runtime-validation/wazuh-4.14.7/TELEMETRY_HEALTH_EVIDENCE_2026-09-23.md` — all 4 regex alternatives in rule `110301` confirmed via real `wazuh-logtest`; no naturally-occurring Wazuh-internal event exists for this rule, so it is synthetic by design. Found a real, documented limitation: the rule has no `if_group`/`if_sid` scoping, so any other rule matching first silently prevents it from ever being evaluated.)
- [x] pgAudit decoder validated against real PostgreSQL 17 + pgAudit output. (`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`: all 5 non-correlation fixtures matched their expected rule id on real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit 17.1)
- [x] PostgreSQL correlation rule tested in one logtest session. (`pgaudit_repeated_read_20.log`, single `wazuh-logtest` session, escalated to rule 110406 as expected)
- [x] Centralized `agent.conf` accepted by Wazuh. (`release/runtime-validation/wazuh-4.14.7/AGENT_CONF_EVIDENCE_2026-09-23.md` — a separate Docker-based agent was enrolled and both `pdp-linux-baseline` and `pdp-database` agent.conf overlays were distributed successfully after fixing a real bug: `<syscollector>` is not valid in a centralized `agent.conf` and was invalidating the whole file)
- [ ] No implementation test remains incorrectly marked as validated. (ongoing discipline item, not a one-time check; the SCA-via-group finding above is exactly the kind of thing this guards against)

## E. Evidence / assessment

- [x] Evidence JSON Schema validated. (CI validates `examples/evidence.example.json` against `framework/schemas/evidence.schema.json`; also indexed successfully into a real Wazuh Indexer, 2026-09-23 — see section F)
- [x] Assessment JSON Schema validated. (`examples/control-assessment.example.json` added 2026-09-23 and validated in CI against `framework/schemas/control-assessment.schema.json`; also indexed successfully into a real Wazuh Indexer)
- [x] Finding JSON Schema validated. (CI validates `examples/finding.example.json` against `framework/schemas/finding.schema.json`; also indexed successfully into a real Wazuh Indexer, 2026-09-23)
- [x] Evidence Registry Schema validated. (`reports/TOOLS_PIPELINE_VALIDATION_2026-09-23.md` — `tools/evidence/register_evidence.py` run against 8 synthetic evidence documents; all 8 generated registry entries validated against `framework/schemas/evidence-registry.schema.json`)
- [x] API harness produces normalized evidence. (`release/runtime-validation/wazuh-4.14.7/API_HARNESS_EVIDENCE_2026-09-23.md` — `run_api_logtest.py` run against the real Wazuh Server API for all 13 `HARNESS.yml` cases; found and fixed a bug where `test.decoder` was passed as an object instead of a string, then re-validated all 13 generated evidence documents against `evidence.schema.json` individually)
- [x] Collector failure produces `ERROR/REVIEW`, never silent `PASS`. (`reports/TOOLS_PIPELINE_VALIDATION_2026-09-23.md` — a synthetic `PASS` result with `source.collector_health: DEGRADED` produced assessment result `REVIEW`, confirming `tools/assessment/assess_controls.py`'s precedence logic holds)
- [x] Assessment aggregator tested against PASS/FAIL/ERROR/REVIEW cases. (same report — all 5 precedence branches, including the collector-health override, produced the correct result and validated against `control-assessment.schema.json`)
- [x] Finding generator tested. (same report — `tools/findings/generate_findings.py` created exactly one finding, only for the `FAIL` control, validated against `finding.schema.json`)
- [x] Retest workflow documented. (`docs/architecture/retest-workflow.md` — new document, cross-referenced from `framework/models/FINDING_EXCEPTION_REMEDIATION_MODEL.md` section 5; grounded in the verified tool behavior above, including the explicit design decision that findings are never auto-closed)

## F. Indexer / dashboard

- [x] All three index templates accepted by target Wazuh Indexer/OpenSearch. (`release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`)
- [x] `dynamic: strict` verified with expected documents. (fixed 6 missing schema fields across the 3 templates first — see evidence file — then confirmed real documents are accepted and a genuinely unknown field is still rejected)
- [x] Evidence bulk import tested. (single-document `_doc` index of the unmodified `examples/evidence.example.json`, not the `_bulk` API specifically, but proves the mapping accepts real content — `"result":"created"`)
- [x] Assessment bulk import tested. (same method, using the new `examples/control-assessment.example.json`)
- [x] Findings bulk import tested. (same method, using the unmodified `examples/finding.example.json`)
- [x] Index patterns created in target dashboard. (3 index patterns imported and discoverable via `_find`)
- [x] Dashboard panels created/imported. (`release/runtime-validation/dashboard/DASHBOARD_PANELS_EVIDENCE_2026-09-23.md` — all 8 panels from `implementations/wazuh/dashboard/DASHBOARD_SPEC.yml` generated via `implementations/wazuh/dashboard/generate_dashboard_ndjson.py`, imported into the real Wazuh Dashboard, and every panel's aggregation confirmed to execute against the real index mappings without error. Rendering was not confirmed in an actual browser session.)
- [x] Dashboard wording reviewed for legal overstatement. (the imported shell's own description reads "PDP Control Framework engineering dashboard shell. Not a legal compliance score." — confirmed present on the real imported object, 2026-09-23)
- [ ] Role-based access model documented. **Design done, live test pending operator approval.** (`implementations/wazuh/dashboard/rbac/README.md`, `roles.yml`, `roles_mapping.yml` — two least-privilege roles designed: `pdp_dashboard_viewer` (read-only on `pdp-*` data + dashboard) and `pdp_dashboard_editor` (same read-only data access, plus CRUD on `.kibana*` saved objects only — never on `pdp-evidence-*`/`pdp-assessment-*`/`pdp-findings-*`, which stay pipeline-managed). Applying this to the lab indexer's live `roles.yml`/`roles_mapping.yml`/`internal_users.yml` was correctly blocked by the session's own safety guardrail as a sensitive access-control change; config backups were taken and verified unmodified. The documented test procedure (curl checks for allow/deny on read/write for both roles) has not yet been executed against the real indexer — do this before checking this item off.)

## G. CI / repository

- [x] `validate_structure.py` passes.
- [x] `validate_fixtures.py` passes.
- [x] schema validation passes. (evidence, finding, and index-template JSON examples)
- [x] coverage report generation passes. (CI now regenerates `reports/COVERAGE_REPORT.{md,json}` and fails on drift, see workflow step "Check coverage report is reproducible")
- [x] duplicate IDs fail CI. (`validate_structure.py` for Wazuh rule IDs; `validate_release_consistency.py` for `LR-*`/`PDP-*`/`REQ-*`/test IDs)
- [x] broken legal/control/test references fail CI. (`validate_release_consistency.py` checks `mapped_controls`, `supports_controls`, and test `controls`/`requirements` references against known IDs)
- [x] generated runtime results excluded from Git. (`.gitignore`: `runtime/`, `implementations/wazuh/tests/results/*`, `release/runtime-validation/**/RESULT.json`)
- [x] README quick start updated. (`README.md` "Quick start" section)
- [x] CONTRIBUTING.md added.
- [x] SECURITY.md added.
- [x] LICENSE selected. (Apache License 2.0 — see `LICENSE`; open to change by project governance before 1.0)
- [x] release changelog generated. (`release/CHANGELOG_0.10.0-rc2.md`)

## H. 1.0 release gate

Release **must not** be tagged `1.0.0` until all mandatory items above are complete or an explicit release exception is documented and approved.
