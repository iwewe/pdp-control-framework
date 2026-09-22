# Finding, Exception, and Remediation Model

**Status:** Current normative model (introduced in draft v0.3, part of 0.10.0-rc2)

## 1. Finding

A finding records a control-relevant observation.

```yaml
id: FIND-2026-0001

control_id: PDP-ACC-003
processing_activity_id: PA-001
asset_id: ASSET-DB-001

test_id: WZ-SCA-ACC-001

result: FAIL
severity: HIGH

observed_at: 2026-09-22T10:30:00+07:00

evidence:
  - EV-2026-000001

statement:
  id: Root login melalui SSH masih diizinkan.

status: OPEN

remediation:
  id: REM-2026-0001
```

## 2. Severity Is Not Legal Severity

Finding severity describes engineering/risk priority.

Do not use it to state:

```text
"serious violation of UU PDP"
```

unless that conclusion comes from an authorized legal assessment.

## 3. Exception

```yaml
id: EXC-2026-001

control_id: PDP-ACC-003
scope:
  assets:
    - ASSET-LEGACY-001

reason: >
  Legacy vendor dependency prevents immediate configuration change.

risk_owner: Head of IT

compensating_controls:
  - network_isolation
  - enhanced_monitoring

approved_at: 2026-09-01
expires_at: 2026-12-01

status: ACTIVE
```

An exception does not convert a failed control into PASS.

Possible presentation:

```text
Control: FAIL
Exception: ACTIVE
Residual risk: ACCEPTED
```

## 4. Remediation

```yaml
id: REM-2026-0001

finding_id: FIND-2026-0001

owner: Infrastructure Team

action:
  id: Nonaktifkan SSH root login.

target_date: 2026-09-30

status: IN_PROGRESS

validation:
  required: true
  test_id: WZ-SCA-ACC-001
```

## 5. Lifecycle

```text
Evidence
   |
   v
Test
   |
   +--> PASS
   |
   +--> FAIL
          |
          v
       Finding
          |
          +--> Remediation
          |
          +--> Exception
          |
          +--> Risk Acceptance
          |
          v
       Retest
```
