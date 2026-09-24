# PDP Control Framework

A technology-neutral control framework derived from Indonesia's **UU No. 27
Tahun 2022 tentang Pelindungan Data Pribadi**, designed to translate legal
obligations into auditable control objectives and evidence requirements. The
first implementation/evidence profile targets **Wazuh**.

> This repository is intended for compliance engineering and technical
> control mapping. It does not constitute legal advice or certification of
> compliance. A Wazuh technical PASS is **not** equivalent to legal
> compliance.

## Current status

**Version:** 1.0.0 — **first stable release** (`FRAMEWORK_MANIFEST.yml`)

See `release/PRE_1_0_CHECKLIST.md`, `release/RELEASE_READINESS_1.0.0.yml`,
and `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` for what was validated
and what remains deliberately out of scope, and the status tables below
for a snapshot.

For the version-by-version design history (v0.1 through v0.9), see
`docs/history/`, starting with
[`docs/history/framework-v0.1-v0.9-narrative.md`](docs/history/framework-v0.1-v0.9-narrative.md).

## Architecture

The framework deliberately separates legal meaning from technical
implementation:

```text
Law
-> Legal Requirement (LR-*)
-> PDP Control (PDP-*)
-> Generic Requirement (REQ-*)
-> Implementation Profile (Wazuh, ...)
-> Test
-> Evidence
-> Assessment
-> Finding
-> Remediation / Exception
-> Retest
-> Dashboard
```

Wazuh starts at the Test/Evidence boundary and inherits legal context from
the control rather than encoding legal conclusions in individual rules. See
`PDP_CONTROL_FRAMEWORK.md` for the full methodology and
`docs/architecture/` for current design documents.

## Repository layout

```text
pdp-control-framework/
├── framework/           # normative, product-neutral source of truth
├── implementations/     # product adapters; currently Wazuh
├── tools/                # executable project tooling (assessment, evidence,
│                          #   findings, validation, reporting, export)
├── docs/
│   ├── architecture/     # current design documentation
│   ├── history/          # versioned design notes, not current source of truth
│   └── legal-sources/    # preserved snapshots of primary legal sources
├── examples/             # synthetic examples only
├── reports/              # reproducible committed engineering reports
└── release/              # release gates, compatibility matrix, runtime validation
```

Full detail: `docs/REPOSITORY_LAYOUT.md`.

## Quick start

```bash
pip install -r requirements-dev.txt

# Validate repository structure, ID references, and duplicate rule IDs
python tools/validation/validate_structure.py

# Validate PostgreSQL/pgAudit fixture shape against the decoder's parsing contract
python implementations/wazuh/tests/scripts/validate_fixtures.py

# Regenerate the engineering coverage report
python tools/reporting/generate_coverage_report.py
```

This is the same sequence CI runs on every push/PR
(`.github/workflows/validate.yml`).

## Legal baseline

Primary source:

- UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi
- https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/crc32/

Binding interpretation:

- Constitutional Court Decision 151/PUU-XXII/2024, 30 July 2025, concerning Article 53(1)
- https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024

Preserved snapshots of both sources (retrieved 2026-09-22, including the
official Constitutional Court decision PDF) are archived in
`docs/legal-sources/`. Review status: authoritative-text review is
`SOURCE_VERIFIED`; independent external legal counsel review and an
independent implementing-regulations re-check are recorded as an
explicit, scoped project-owner exception for this release, not a
pending blocker (`framework/legal/review/LEGAL_REVIEW_STATUS.yml`,
`release/PRE_1_0_CHECKLIST.md` section H).

## Wazuh implementation status

All Wazuh content (rules, decoders, SCA policy, agent configuration, index
templates, dashboard) is validated both statically (CI: well-formed
XML/YAML/JSON, unique rule IDs, schema-valid examples) and against a real
Wazuh 4.14.7 lab (manager/agent, PostgreSQL 17 + pgAudit, Indexer,
Dashboard).

| Area | Status |
|---|---|
| Static repository validation | PASS (CI) |
| Wazuh 4.14.7 manager/agent runtime | LAB_VALIDATED |
| PostgreSQL 17 + pgAudit real decoding | LAB_VALIDATED |
| Wazuh Indexer template import | LAB_VALIDATED |
| Wazuh Dashboard saved-object import + RBAC | LAB_VALIDATED |

Full detail and evidence links: `release/RELEASE_READINESS_1.0.0.yml`,
`reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`, and
`release/compatibility/COMPATIBILITY_MATRIX.yml` (`promotion_rule`: no
platform is marked `SUPPORTED` before reproducible lab evidence exists —
this release's targets are `LAB_VALIDATED`, one step below `SUPPORTED`,
which still implies broader multi-environment production confidence
beyond a single lab pass).

## Current coverage

Engineering traceability coverage, **not** a legal compliance score
(`reports/COVERAGE_REPORT.md`, regenerated by
`tools/reporting/generate_coverage_report.py`):

- Legal requirements: **64**
- With Wazuh test coverage: **24**
- Generic requirement only: **8**
- No technical coverage: **32**

Many UU PDP obligations (lawful basis, validity of consent, DPO
applicability, DPIA conclusions, cross-border adequacy, data-subject notice
content) are expected to remain `MANUAL` / `DOCUMENTARY` / `ORGANIZATIONAL`
rather than Wazuh-testable — the goal is 100% *explained* coverage per
legal requirement, not 100% Wazuh coverage.

## Contributing

See `CONTRIBUTING.md` for contribution layers, ID discipline, and pull
request expectations. See `SECURITY.md` to report a security issue.
