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
- [ ] No control text claims more than the legal source supports.
- [ ] Legal summaries are clearly identified as framework interpretations.
- [ ] Any implementing regulations/guidance required for 1.0 scope are documented.

> Note: the above is authoritative-**text** review, not independent external
> legal counsel review. `external_legal_counsel_review` remains
> `NOT_PERFORMED` (`framework/legal/review/LEGAL_REVIEW_STATUS.yml`).

## B. Control architecture

- [x] Every `PDP-*` control has at least one legal requirement mapping. (verified: 0 of 39 controls missing `legal_basis`; enforced going forward by `tools/validation/validate_release_consistency.py`)
- [x] Every `REQ-*` requirement maps to at least one PDP control. (verified: 0 of 31 requirements missing `supports_controls`)
- [x] Control IDs are stable and unique. (0 duplicate `PDP-*`/`REQ-*`/`LR-*`/test IDs; enforced in CI)
- [ ] Assessment method/result semantics are consistent.
- [ ] `NOT_APPLICABLE` requires justification.
- [x] No engineering score is described as a legal compliance score. (consistently disclaimed across README, coverage report, release readiness, and `implementations/wazuh/WAZUH_PROFILE.yml` boundary statement)

## C. Processing / applicability

- [ ] Processing Activity model reviewed.
- [ ] Asset model reviewed.
- [ ] Control Profile composition tested with at least three realistic examples.
- [ ] High-risk processing profile reviewed.
- [ ] Security monitoring platform dogfooding example completed.

## D. Wazuh implementation

- [x] Target Wazuh version pinned in compatibility matrix. (4.14.7, `release/compatibility/COMPATIBILITY_MATRIX.yml`)
- [x] Manager/indexer/dashboard version compatibility verified. (all three report `4.14.7-1` on the same host, 2026-09-23)
- [x] All custom rule IDs unique and within project-reserved range. (14 rule IDs, all within 100000-120000, enforced by `tools/validation/validate_structure.py`)
- [x] SCA YAML executes successfully. (`release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md` — all 6 checks in `pdp_linux_baseline.yml` executed on real Wazuh 4.14.7 + Ubuntu 24.04.4; every result independently reproduced with direct shell commands. No bug found.)
- [x] Authentication fixtures validated with real `wazuh-logtest`. (`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`: both `ssh_failed_once.log` -> 110001 and the `ssh_failed_8.log` correlation -> 110002 matched exactly; `su_session_opened.log` -> 110101 and the repeated-3 correlation -> 110102 also matched)
- [x] FIM fixtures validated on Ubuntu 24.04. (`release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md` — live create/modify/delete against a realtime-monitored path, not a static fixture; found and fixed two rule bugs in the process, see that file and `implementations/wazuh/rules/pdp_fim.xml`)
- [ ] Telemetry-health rules adapted to actual Wazuh events.
- [x] pgAudit decoder validated against real PostgreSQL 17 + pgAudit output. (`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`: all 5 non-correlation fixtures matched their expected rule id on real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit 17.1)
- [x] PostgreSQL correlation rule tested in one logtest session. (`pgaudit_repeated_read_20.log`, single `wazuh-logtest` session, escalated to rule 110406 as expected)
- [ ] Centralized `agent.conf` accepted by Wazuh. (no agent enrolled in the lab yet)
- [ ] No implementation test remains incorrectly marked as validated.

## E. Evidence / assessment

- [x] Evidence JSON Schema validated. (CI validates `examples/evidence.example.json` against `framework/schemas/evidence.schema.json`)
- [ ] Assessment JSON Schema validated. (no example document exercises `framework/schemas/control-assessment.schema.json` yet)
- [x] Finding JSON Schema validated. (CI validates `examples/finding.example.json` against `framework/schemas/finding.schema.json`)
- [ ] Evidence Registry Schema validated.
- [ ] API harness produces normalized evidence.
- [ ] Collector failure produces `ERROR/REVIEW`, never silent `PASS`.
- [ ] Assessment aggregator tested against PASS/FAIL/ERROR/REVIEW cases.
- [ ] Finding generator tested.
- [ ] Retest workflow documented.

## F. Indexer / dashboard

- [ ] All three index templates accepted by target Wazuh Indexer/OpenSearch.
- [ ] `dynamic: strict` verified with expected documents.
- [ ] Evidence bulk import tested.
- [ ] Assessment bulk import tested.
- [ ] Findings bulk import tested.
- [ ] Index patterns created in target dashboard.
- [ ] Dashboard panels created/imported.
- [ ] Dashboard wording reviewed for legal overstatement.
- [ ] Role-based access model documented.

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
