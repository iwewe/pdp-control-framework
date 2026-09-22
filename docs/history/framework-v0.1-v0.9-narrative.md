# Framework Evolution Narrative — v0.1 through v0.9

> This is the version-by-version narrative that previously lived in the
> repository's `README.md`. It has been moved here so the README can stay a
> current-state entrypoint (see `docs/REPOSITORY_LAYOUT.md`: "`docs/history/`
> preserves design evolution without being the current source of truth").
> For the version-specific design docs referenced below, see the other files
> in this directory. For current status, see `README.md` and
> `FRAMEWORK_MANIFEST.yml`.

## Draft v0.1 — initial control catalogue

Core files:

- `PDP_CONTROL_FRAMEWORK.md` — framework architecture, methodology, assessment and evidence model.
- `CONTROL_CATALOGUE.yml` — initial machine-readable control catalogue covering the main controller/processor obligations in Articles 20-56.

## Draft v0.2 architecture additions

The framework added a formal traceability and assessment layer:

- `framework/legal/LEGAL_MAPPING.yml` — legal requirement IDs (`LR-*`) mapped to stable controls.
- `docs/architecture/traceability-model.md` — separation of law, requirement, control, test, and evidence.
- `docs/architecture/assessment-methodology.md` — assessment method/result rules and evidence validation.
- `docs/architecture/applicability-model.md` — processing-context and control-applicability model.
- `evidence/evidence-types.yml` — evidence classes, quality levels, and common attributes (later moved to `framework/evidence/EVIDENCE_TYPES.yml`).

The intended relationship:

```text
Law -> Legal Requirement -> PDP Control -> Test -> Evidence -> Implementation Profile
```

## Draft v0.3 operating-model additions

Version 0.3 introduced the operational objects needed before a Wazuh implementation profile could be considered robust:

- `model/PROCESSING_ACTIVITY_MODEL.md`
- `model/ASSET_MODEL.md`
- `model/EVIDENCE_PROVENANCE_MODEL.md`
- `model/CONTROL_TEST_MODEL.md`
- `model/FINDING_EXCEPTION_REMEDIATION_MODEL.md`
- `docs/architecture/compliance-operating-model.md`
- `examples/processing-activity.example.yml`

(These `model/*` files were later moved to `framework/models/`.)

The architecture then separated:

```text
Law -> Legal Requirement -> Control
                             |
Processing Activity -> Asset + Test -> Evidence -> Finding -> Remediation
```

Wazuh starts at the **Test/Evidence** boundary and inherits legal context from the control and processing activity rather than encoding legal conclusions in individual rules.

## Draft v0.4 requirement and Wazuh profile layer

Version 0.4 added the missing abstraction between controls and tools:

- `framework/requirements/CONTROL_REQUIREMENTS.yml` — technology-neutral technical/operational requirements.
- `implementations/wazuh/WAZUH_PROFILE.yml` — maps generic requirements to Wazuh capabilities.
- `implementations/wazuh/WAZUH_TEST_CATALOGUE.yml` — initial product-specific test model.
- `implementations/wazuh/README.md` — implementation boundary and engineering guidance.
- `docs/history/architecture-v0.4.md` — canonical architecture.

Canonical chain:

```text
Law
-> Legal Requirement
-> PDP Control
-> Generic Requirement
-> Implementation-specific Test
-> Evidence
-> Finding
-> Remediation / Exception
```

## Draft v0.5 engineering-profile additions

Version 0.5 added:

- `framework/profiles/CONTROL_PROFILES.yml`
- `framework/taxonomy/PDP_EVENT_TAXONOMY.yml`
- expanded `implementations/wazuh/WAZUH_TEST_CATALOGUE.yml`
- `docs/history/engineering-spec-v0.5.md`
- `examples/profile-application.example.yml`

The project could then resolve:

```text
Processing Context
-> Applicable Profile(s)
-> Generic Requirements
-> Wazuh Tests
-> Evidence
-> Findings
```

## Draft v0.6 executable Wazuh package

Version 0.6 introduced the first executable/draft Wazuh artifacts:

- `implementations/wazuh/sca/pdp_linux_baseline.yml`
- `implementations/wazuh/rules/pdp_authentication.xml`
- `implementations/wazuh/rules/pdp_privileged_access.xml`
- `implementations/wazuh/rules/pdp_fim.xml`
- `implementations/wazuh/rules/pdp_telemetry_health.xml`
- `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
- `implementations/wazuh/shared/pdp-database/agent.conf`
- `implementations/wazuh/manifests/TRACEABILITY.yml`
- `docs/history/wazuh-lab-validation-v0.6.md`
- `tools/validation/validate_structure.py`

All implementation content remained `LAB_VALIDATION_REQUIRED`. Repository-level YAML/XML structure was validated, but real Wazuh behavior still needed to be tested with `wazuh-logtest`, SCA execution, and endpoint fixtures before promotion to normative status — a status that, as of 0.10.0-rc2, remains outstanding (see `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`).

## Draft v0.7 PostgreSQL audit and lab fixtures

Version 0.7 added:

- `implementations/wazuh/postgresql/POSTGRESQL_AUDIT_PROFILE.yml`
- `implementations/wazuh/postgresql/postgresql-pdp.conf.example`
- `implementations/wazuh/postgresql/pgaudit-setup.sql`
- `implementations/wazuh/decoders/pdp_pgaudit.xml`
- `implementations/wazuh/rules/pdp_postgresql.xml`
- reusable synthetic `wazuh-logtest` fixtures
- `EXPECTED_RESULTS.yml`
- static fixture validation
- a Wazuh lab runner
- GitHub Actions static validation
- `docs/history/v0.7-postgresql-lab.md`

The PostgreSQL baseline is privacy-aware by default: pgAudit parameters and statement bodies are not logged unless an explicit processing/risk decision requires them.

## Draft v0.8 test harness and evidence normalization

Version 0.8 added:

- `framework/schemas/evidence.schema.json`
- `framework/schemas/control-assessment.schema.json`
- `tools/assessment/WAZUH_EVIDENCE_MAPPING.yml`
- `implementations/wazuh/tests/harness/HARNESS.yml`
- `implementations/wazuh/tests/harness/run_api_logtest.py`
- `tools/validation/validate_evidence.py`
- `tools/assessment/assess_controls.py`
- `examples/evidence.example.json`
- `docs/history/v0.8-evidence-normalization.md`

The preferred automated lab interface became the Wazuh Server API `/logtest`, because it returns structured JSON and supports session tokens required for correlation tests.

Normalized evidence is intentionally implementation-neutral and can later be produced by Wazuh, IAM, database, cloud, manual, or documentary assessment engines.

## Draft v0.9 findings, registry, and dashboard model

Version 0.9 added:

- `framework/schemas/finding.schema.json`
- `framework/schemas/evidence-registry.schema.json`
- `tools/evidence/register_evidence.py`
- `tools/findings/generate_findings.py`
- `tools/export/export_bulk_ndjson.py`
- `implementations/wazuh/indexer/templates/pdp-evidence-template.json`
- `implementations/wazuh/indexer/templates/pdp-assessment-template.json`
- `implementations/wazuh/indexer/templates/pdp-findings-template.json`
- `implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`
- `docs/history/v0.9-findings-dashboard.md`

Recommended runtime indices:

```text
pdp-evidence-*
pdp-assessment-*
pdp-findings-*
```

These indices intentionally remain separate from `wazuh-alerts-*`.

## Pre-1.0 — 0.10.0-rc1

The pre-1.0 release candidate added release governance and measurable traceability:

- `FRAMEWORK_MANIFEST.yml`
- `release/compatibility/COMPATIBILITY_MATRIX.yml`
- `docs/architecture/LIFECYCLE_RETENTION_POLICY.md`
- `release/PRE_1_0_CHECKLIST.md`
- `release/RELEASE_GATES.yml`
- `reports/COVERAGE_REPORT.md`
- `reports/COVERAGE_REPORT.json`
- `CONTRIBUTING.md`
- `SECURITY.md`

Engineering traceability report at rc1:

```text
Legal requirements total: 46
With Wazuh test coverage: 19
Generic requirement only: 8
No technical coverage: 19
```

## Pre-1.0 — 0.10.0-rc2

See `release/CHANGELOG_0.10.0-rc2.md` and `framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md` for the rc2 release-readiness pass (authoritative legal-source re-review that grew the legal requirement count from 46 to 64, static dashboard/import package, and version-pinned Wazuh 4.14.7 runtime validation runner).
