# Engineering Specification v0.5

## 1. Purpose

Version 0.5 moves the project from architecture into implementable control engineering.

Three new concepts are normative candidates:

1. **Control Profiles** — reusable baselines selected by processing/asset context.
2. **PDP Event Taxonomy** — normalized event semantics independent of Wazuh.
3. **Expanded Wazuh Test Catalogue** — implementation-specific tests mapped to generic requirements.

## 2. Applicability Pipeline

```text
Processing Activity
      |
      +-- role
      +-- data categories
      +-- risk
      +-- transfer
      +-- processor state
      +-- assets
      |
      v
Profile Selection
      |
      v
Generic Requirements
      |
      v
Implementation Tests
      |
      v
Evidence
```

Profiles never replace legal analysis.

## 3. Profile Composition

Profiles may be additive.

Example:

```text
PA-001 Employee Management
      |
      +-- PDP-PROFILE-BASELINE
      +-- PDP-PROFILE-HIGH-RISK
      |
ASSET-DB-001
      |
      +-- PDP-PROFILE-DATABASE
```

The effective requirement set is the union of applicable profiles, then adjusted by documented legal/applicability review.

## 4. Event Normalization

Raw events differ by platform:

```text
Linux auth.log
Windows Event Log
PostgreSQL audit
Cloud IAM log
```

The framework should normalize relevant observations into PDP event categories:

```text
raw event
   -> decoder/parser
   -> technical detection
   -> PDP event category
   -> control/test/evidence relation
```

Example:

```text
10 failed SSH logins
    ->
WZ-RUL-AUTH-001
    ->
PDP-EVT-AUTH-001
    ->
REQ-MON-001
    ->
PDP-ACC-003 / PDP-INC-001
```

The category remains a security/privacy event, not a legal violation.

## 5. Severity Model

Do not use a single number for everything.

Recommended dimensions:

```text
technical_severity
privacy_impact
asset_criticality
confidence
legal_review_state
```

Example:

```yaml
technical_severity: HIGH
privacy_impact: HIGH
asset_criticality: CRITICAL
confidence: MEDIUM
legal_review_state: NOT_REVIEWED
```

This avoids treating a Wazuh alert level as a legal severity score.

## 6. PDP Context Enrichment

Recommended low-sensitivity context:

```text
pdp.asset_id
pdp.processing_activity_id
pdp.profile
pdp.data_classification
pdp.asset_criticality
pdp.environment
pdp.organization_role
```

Avoid embedding raw Personal Data.

## 7. Evidence Health Gate

Before a continuous control can return PASS:

```text
test condition satisfied
AND
evidence source healthy
AND
required coverage threshold met
AND
evidence freshness acceptable
```

Otherwise:

```text
REVIEW or ERROR
```

This is a core anti-false-compliance rule.

## 8. Database Profile Boundary

Wazuh can collect database audit logs, but database-specific controls generally require the database to emit suitable audit telemetry.

Therefore a database control may depend on:

```text
Database-native audit configuration
    +
Wazuh collection
    +
Wazuh rule/correlation
```

Wazuh is not assumed to create all audit evidence by itself.

## 9. Security Monitoring as a PDP Processing Activity

The Wazuh platform itself should be registered as a Processing Activity, for example:

```yaml
id: PA-SEC-001
name: Security Monitoring and Incident Detection

purpose:
  - cybersecurity_monitoring
  - incident_detection
  - incident_response

data_subjects:
  - employees
  - contractors
  - system_users

data:
  - username
  - device_identifier
  - IP_address
  - authentication_metadata
  - security_activity_metadata
```

This allows the framework to assess the monitoring platform under the same PDP principles it helps monitor.

## 10. Engineering Release Gates

Before a Wazuh test becomes normative:

```text
DRAFT_DESIGN
  ->
LAB_VALIDATED
  ->
PLATFORM_VALIDATED
  ->
DOCUMENTED
  ->
REVIEWED
  ->
NORMATIVE
```

A test SHOULD include:

- supported Wazuh version
- supported OS/platform
- prerequisites
- exact configuration
- expected output
- negative test
- error state test
- evidence fields
- rollback/remediation
- privacy notes

## 11. Next Implementation Artifacts

The next code-producing phase should create:

```text
implementations/wazuh/
  sca/
    pdp_linux_baseline.yml

  rules/
    pdp_authentication.xml
    pdp_privileged_access.xml
    pdp_fim.xml
    pdp_telemetry_health.xml

  shared/
    agent.conf.example

  tests/
    fixtures/
    validation/
```

These files should be generated only after each draft test is checked against a real Wazuh lab.
