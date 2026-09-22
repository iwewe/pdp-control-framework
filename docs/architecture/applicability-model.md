# Applicability Model

**Status:** Current architecture document (introduced in draft v0.2, part of 0.10.0-rc2 `normative_core`)

## 1. Why Applicability Exists

Not every control applies to every organization, system, or processing activity.

Applicability is evaluated before control testing.

```text
Processing Context
     |
     v
Legal Applicability
     |
     v
Control Applicability
     |
     v
Evidence Requirement
     |
     v
Assessment
```

## 2. Minimum Processing Context

An applicability record SHOULD include:

```yaml
processing_activity:
  id: PA-001
  name: Employee Management

role:
  controller: true
  processor: false

data_subjects:
  - employee

personal_data:
  general: true
  specific: true

scale:
  classification: medium

monitoring:
  regular_and_systematic: false

automated_decision:
  significant_effect: false

cross_border_transfer:
  enabled: false

children_data:
  processed: false

public_service:
  processing: false
```

## 3. Applicability States

- `APPLICABLE`
- `NOT_APPLICABLE`
- `CONDITIONAL`
- `REVIEW_REQUIRED`

## 4. Examples

### PDP-DPIA-002

If processing falls into Article 34 high-risk categories:

```text
APPLICABLE
```

Otherwise:

```text
CONDITIONAL / REVIEW_REQUIRED
```

### PDP-DPO-001

Evaluate Article 53 triggers while applying Constitutional Court Decision 151/PUU-XXII/2024.

The tool should ask for facts; it should not autonomously make a final legal judgment when the facts or interpretation are uncertain.

### PDP-TRF-002

If no cross-border transfer exists:

```text
NOT_APPLICABLE
```

with evidence supporting the assertion.

## 5. Asset vs Processing Applicability

A key design rule:

**UU PDP obligations attach to processing activities and organizational roles, not merely to servers.**

Therefore:

```text
Processing Activity
     |
     +-- application
     +-- database
     +-- server
     +-- endpoint
     +-- cloud service
     +-- processor
```

Wazuh agents and assets must eventually be linked back to a processing activity.

This avoids the incorrect model:

```text
agent = compliant / non-compliant
```

and enables the stronger model:

```text
asset -> supports processing activity -> relevant controls -> evidence
```

## 6. Recommended Future Object

```yaml
asset:
  id: ASSET-001
  wazuh_agent_id: "014"
  hostname: hr-db-01
  processing_activities:
    - PA-001
  data_classification:
    - personal
    - specific
  criticality: high
```

This object will later become the bridge between the technology-neutral framework and the Wazuh implementation profile.
