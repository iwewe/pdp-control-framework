# Evidence Provenance Model

**Status:** Current normative model (introduced in draft v0.3, part of 0.10.0-rc2)

## 1. Principle

A compliance evidence item must answer:

```text
What happened?
Where did the evidence come from?
Who/what produced it?
When was it produced?
What scope does it cover?
Can it be trusted?
Which control does it support?
```

## 2. Evidence Object

```yaml
id: EV-2026-000001

evidence_type: authentication_log
evidence_class: technical

source:
  system: wazuh
  source_id: ES-WAZUH-014
  collector: wazuh-agent
  collector_version: unknown

scope:
  processing_activities:
    - PA-001
  assets:
    - ASSET-DB-001
  controls:
    - PDP-ACC-003
    - PDP-LOG-001
  legal_requirements:
    - LR-039-01
    - LR-031-01

observed_at: 2026-09-22T10:30:00+07:00
collected_at: 2026-09-22T10:30:04+07:00

integrity:
  quality: Q4
  hash: null
  protected_storage: true

retention:
  policy_id: EVID-RET-001

review:
  status: UNREVIEWED
  reviewer: null
```

## 3. Evidence Source Registry

Evidence itself is ephemeral; source registration should be stable.

Example:

```yaml
id: ES-WAZUH-014

type: wazuh_agent

asset_id: ASSET-DB-001

source_system:
  name: Wazuh
  component: Agent

collection:
  continuous: true
  expected_interval: realtime

integrity_controls:
  transport_protected: true
  centralized_storage: true
```

## 4. Evidence Quality

Evidence quality is separate from control result.

```text
Q0 No evidence
Q1 Assertion only
Q2 Documented evidence
Q3 Verifiable timestamped evidence
Q4 Continuous/integrity-protected or corroborated evidence
```

A PASS supported only by Q1 evidence should normally be rejected or escalated to REVIEW.

## 5. Evidence Freshness

Controls MAY define evidence validity.

Example:

```yaml
freshness:
  max_age_days: 30
```

Continuous controls may instead define:

```yaml
coverage:
  minimum_percent: 95
  assessment_window_days: 30
```

## 6. Evidence Gaps

A missing source must be explicit:

```text
EXPECTED
  -> AVAILABLE
  -> STALE
  -> MISSING
  -> DEGRADED
```

This allows the framework to distinguish:

```text
"No security incidents detected"
```

from:

```text
"No telemetry was collected"
```

These are not equivalent.

## 7. Provenance and Chain of Custody

For normal compliance evidence, full forensic chain of custody may not be required.

For breach investigation evidence, stronger provenance SHOULD include:

- collection timestamp
- original source
- collector identity
- hash where appropriate
- transfer history
- reviewer
- retention location
- access history

The framework should support both compliance-grade and incident/forensic-grade evidence.
