# PDP Control Framework

A technology-neutral control framework derived from Indonesia's **UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi**, designed to translate legal obligations into auditable control objectives and evidence requirements.

The first implementation/evidence profile will target **Wazuh**.

## Current status

**Draft v0.1**

Core files:

- `PDP_CONTROL_FRAMEWORK.md` — framework architecture, methodology, assessment and evidence model.
- `CONTROL_CATALOGUE.yml` — initial machine-readable control catalogue covering the main controller/processor obligations in Articles 20–56.

## Key principle

```text
UU PDP
  -> legal requirement
  -> PDP control
  -> evidence requirement
  -> assessment
  -> implementation profile
       -> Wazuh
       -> other technologies
       -> manual audit
```

A Wazuh technical PASS is **not** equivalent to legal compliance.

## Legal baseline

Primary source:

- UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi
- https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/crc32/

Important interpretation:

- Constitutional Court Decision 151/PUU-XXII/2024, 30 July 2025, concerning Article 53(1)
- https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024

## Disclaimer

This repository is intended for compliance engineering and technical control mapping. It does not constitute legal advice or certification of compliance.


## Draft v0.2 architecture additions

The framework now includes a formal traceability and assessment layer:

- `framework/legal/LEGAL_MAPPING.yml` — legal requirement IDs (`LR-*`) mapped to stable controls.
- `docs/architecture/traceability-model.md` — separation of law, requirement, control, test, and evidence.
- `docs/architecture/assessment-methodology.md` — assessment method/result rules and evidence validation.
- `docs/architecture/applicability-model.md` — processing-context and control-applicability model.
- `evidence/evidence-types.yml` — evidence classes, quality levels, and common attributes.

The intended relationship is:

```text
Law -> Legal Requirement -> PDP Control -> Test -> Evidence -> Implementation Profile
```


## Draft v0.3 operating-model additions

Version 0.3 introduces the operational objects needed before a Wazuh implementation profile can be considered robust:

- `model/PROCESSING_ACTIVITY_MODEL.md`
- `model/ASSET_MODEL.md`
- `model/EVIDENCE_PROVENANCE_MODEL.md`
- `model/CONTROL_TEST_MODEL.md`
- `model/FINDING_EXCEPTION_REMEDIATION_MODEL.md`
- `docs/architecture/compliance-operating-model.md`
- `examples/processing-activity.example.yml`

The architecture now separates:

```text
Law -> Legal Requirement -> Control
                             |
Processing Activity -> Asset + Test -> Evidence -> Finding -> Remediation
```

Wazuh starts at the **Test/Evidence** boundary and inherits legal context from the control and processing activity rather than encoding legal conclusions in individual rules.


## Draft v0.4 requirement and Wazuh profile layer

Version 0.4 adds the missing abstraction between controls and tools:

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

Version 0.5 adds:

- `framework/profiles/CONTROL_PROFILES.yml`
- `framework/taxonomy/PDP_EVENT_TAXONOMY.yml`
- expanded `implementations/wazuh/WAZUH_TEST_CATALOGUE.yml`
- `docs/history/engineering-spec-v0.5.md`
- `examples/profile-application.example.yml`

The project can now resolve:

```text
Processing Context
-> Applicable Profile(s)
-> Generic Requirements
-> Wazuh Tests
-> Evidence
-> Findings
```

Tests remain draft engineering specifications until validated against a real Wazuh lab.


## Draft v0.6 executable Wazuh package

Version 0.6 introduces the first executable/draft Wazuh artifacts:

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

All implementation content remains `LAB_VALIDATION_REQUIRED`. Repository-level YAML/XML structure is validated, but real Wazuh behavior must be tested with `wazuh-logtest`, SCA execution, and endpoint fixtures before promotion to normative status.


## Draft v0.7 PostgreSQL audit and lab fixtures

Version 0.7 adds:

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

Version 0.8 adds:

- `framework/schemas/evidence.schema.json`
- `framework/schemas/control-assessment.schema.json`
- `tools/assessment/WAZUH_EVIDENCE_MAPPING.yml`
- `implementations/wazuh/tests/harness/HARNESS.yml`
- `implementations/wazuh/tests/harness/run_api_logtest.py`
- `tools/validation/validate_evidence.py`
- `tools/assessment/assess_controls.py`
- `examples/evidence.example.json`
- `docs/history/v0.8-evidence-normalization.md`

The preferred automated lab interface is now the Wazuh Server API `/logtest`, because it returns structured JSON and supports session tokens required for correlation tests.

Normalized evidence is intentionally implementation-neutral and can later be produced by Wazuh, IAM, database, cloud, manual, or documentary assessment engines.


## Draft v0.9 findings, registry, and dashboard model

Version 0.9 adds:

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

The pre-1.0 release candidate adds release governance and measurable traceability:

- `FRAMEWORK_MANIFEST.yml`
- `release/compatibility/COMPATIBILITY_MATRIX.yml`
- `docs/architecture/LIFECYCLE_RETENTION_POLICY.md`
- `release/PRE_1_0_CHECKLIST.md`
- `release/RELEASE_GATES.yml`
- `reports/COVERAGE_REPORT.md`
- `reports/COVERAGE_REPORT.json`
- `CONTRIBUTING.md`
- `SECURITY.md`

Current engineering traceability report:

```text
Legal requirements total: 46
With Wazuh test coverage: 19
Generic requirement only: 8
No technical coverage: 19
```

These are engineering coverage counts, not legal compliance scores.


## Final repository organization

The implementation-neutral source of truth lives under `framework/`. Product integrations live under `implementations/`; executable project tooling lives under `tools/`; release gates and runtime validation live under `release/`. See `docs/REPOSITORY_LAYOUT.md`.
