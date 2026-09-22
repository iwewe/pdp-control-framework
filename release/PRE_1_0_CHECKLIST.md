# Pre-1.0 Release Validation Checklist

Target release: **1.0.0**

## A. Legal layer

- [ ] UU 27/2022 legal mapping reviewed against authoritative text.
- [ ] Article/paragraph references independently checked.
- [ ] Constitutional Court Decision 151/PUU-XXII/2024 note reviewed.
- [ ] No control text claims more than the legal source supports.
- [ ] Legal summaries are clearly identified as framework interpretations.
- [ ] Any implementing regulations/guidance required for 1.0 scope are documented.

## B. Control architecture

- [ ] Every `PDP-*` control has at least one legal requirement mapping.
- [ ] Every `REQ-*` requirement maps to at least one PDP control.
- [ ] Control IDs are stable and unique.
- [ ] Assessment method/result semantics are consistent.
- [ ] `NOT_APPLICABLE` requires justification.
- [ ] No engineering score is described as a legal compliance score.

## C. Processing / applicability

- [ ] Processing Activity model reviewed.
- [ ] Asset model reviewed.
- [ ] Control Profile composition tested with at least three realistic examples.
- [ ] High-risk processing profile reviewed.
- [ ] Security monitoring platform dogfooding example completed.

## D. Wazuh implementation

- [ ] Target Wazuh version pinned in compatibility matrix.
- [ ] Manager/indexer/dashboard version compatibility verified.
- [ ] All custom rule IDs unique and within project-reserved range.
- [ ] SCA YAML executes successfully.
- [ ] Authentication fixtures validated with real `wazuh-logtest`.
- [ ] FIM fixtures validated on Ubuntu 24.04.
- [ ] Telemetry-health rules adapted to actual Wazuh events.
- [ ] pgAudit decoder validated against real PostgreSQL 17 + pgAudit output.
- [ ] PostgreSQL correlation rule tested in one logtest session.
- [ ] Centralized `agent.conf` accepted by Wazuh.
- [ ] No implementation test remains incorrectly marked as validated.

## E. Evidence / assessment

- [ ] Evidence JSON Schema validated.
- [ ] Assessment JSON Schema validated.
- [ ] Finding JSON Schema validated.
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

- [ ] `validate_structure.py` passes.
- [ ] `validate_fixtures.py` passes.
- [ ] schema validation passes.
- [ ] coverage report generation passes.
- [ ] duplicate IDs fail CI.
- [ ] broken legal/control/test references fail CI.
- [ ] generated runtime results excluded from Git.
- [ ] README quick start updated.
- [ ] CONTRIBUTING.md added.
- [ ] SECURITY.md added.
- [ ] LICENSE selected.
- [ ] release changelog generated.

## H. 1.0 release gate

Release **must not** be tagged `1.0.0` until all mandatory items above are complete or an explicit release exception is documented and approved.
