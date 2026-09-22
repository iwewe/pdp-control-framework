# Processing Activity Model

**Status:** Current normative model (introduced in draft v0.3, part of 0.10.0-rc2)

## 1. Purpose

The Processing Activity is the central operational object of the PDP Control Framework.

UU PDP obligations generally attach to a processing context, an actor, a purpose, and Personal Data being processed. A server, endpoint, or Wazuh agent is only a technical component supporting that processing activity.

Therefore the framework uses:

```text
Organization
    |
    +-- Role: Controller / Processor
    |
    v
Processing Activity
    |
    +-- Purpose
    +-- Lawful Basis
    +-- Data Subjects
    +-- Personal Data
    +-- Recipients
    +-- Transfers
    +-- Retention
    +-- Risks
    +-- Systems / Assets
    |
    v
Applicable Legal Requirements
    |
    v
Applicable PDP Controls
    |
    v
Evidence
```

## 2. Processing Activity Object

Recommended schema:

```yaml
id: PA-001

name:
  id: Manajemen Kepegawaian
  en: Employee Management

description:
  id: >
    Pemrosesan data pekerja untuk administrasi hubungan kerja,
    payroll, benefit, dan pengelolaan SDM.

organization_role:
  controller: true
  processor: false

owner:
  organizational_unit: Human Resources
  accountable_role: HR Manager

purpose:
  - employment_administration
  - payroll
  - employee_benefits

lawful_basis:
  - type: contract
    reference: employment_relationship
  - type: legal_obligation
    reference: applicable_employment_law

data_subjects:
  - employee
  - former_employee
  - job_candidate

personal_data:
  general:
    - name
    - address
    - phone
    - email
    - employee_identifier
    - bank_account
  specific:
    - health_information
    - biometric_data

sources:
  - data_subject
  - internal_system

recipients:
  - payroll_provider
  - insurance_provider

cross_border_transfer:
  enabled: false

retention:
  policy_id: RET-HR-001

processing_operations:
  - collection
  - storage
  - retrieval
  - use
  - transmission
  - deletion

automated_decision:
  enabled: false
  significant_effect: false

monitoring:
  regular_and_systematic: false
  large_scale: false

risk:
  classification: high
  dpia_required: REVIEW_REQUIRED

assets:
  - ASSET-HRIS-001
  - ASSET-DB-001
  - ASSET-BACKUP-001

applicability:
  legal_requirements: []
  controls: []

evidence_sources: []
```

## 3. Why This Object Matters

Without a Processing Activity object, technical monitoring produces isolated findings:

```text
host hr-db-01
failed login
CVE found
file changed
```

With Processing Activity context:

```text
host hr-db-01
    |
    v
PA-001 Employee Management
    |
    +-- contains specific Personal Data
    +-- risk = high
    +-- controller role
    |
    v
PDP-ACC-003
PDP-SEC-001
PDP-LOG-001
PDP-INC-001
```

The same technical event now has compliance context without turning the event itself into a legal conclusion.

## 4. Processing Activity Lifecycle

Recommended states:

```text
DRAFT
  |
  v
REVIEW
  |
  v
ACTIVE
  |
  +----> CHANGED ----> REASSESS
  |
  v
SUSPENDED
  |
  v
TERMINATED
  |
  v
RETENTION / DELETION / DESTRUCTION
```

Material changes SHOULD trigger re-assessment.

Examples:

- new category of Personal Data
- new purpose
- new processor
- cross-border transfer introduced
- large-scale monitoring introduced
- new automated decision-making
- new technology materially changes risk
- system architecture change
- serious Personal Data breach

## 5. Relationship to Record of Processing

The Processing Activity object can become the framework's technical representation of a record of processing activity.

It is not intended to prescribe the final legal format of organizational records.

## 6. Minimum Required Fields

For assessment readiness:

- id
- name
- organization role
- owner
- purpose
- lawful basis
- data subjects
- Personal Data categories
- processing operations
- assets
- retention reference
- transfer state
- risk state

If mandatory context is absent:

```text
ASSESSMENT_READINESS = INCOMPLETE
```

rather than automatically failing all controls.
