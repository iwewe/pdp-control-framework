# Assessment Methodology

**Status:** Current architecture document (introduced in draft v0.2, part of 0.10.0-rc2 `normative_core`)

## 1. Purpose

This methodology defines how a PDP control is assessed without converting technical observations into unsupported legal conclusions.

The basic chain is:

```text
Legal Requirement
    -> Control Objective
        -> Expected Evidence
            -> Evidence Observation
                -> Control Assessment
```

A legal conclusion is never inferred directly from a Wazuh alert.

## 2. Assessment Method vs Assessment Result

These are separate dimensions.

### Assessment Method

- `AUTOMATED`: the primary condition can be tested reliably using machine-readable evidence.
- `PARTIAL`: technical evidence can test part of the condition, but human review remains necessary.
- `MANUAL`: the core requirement depends on legal, governance, contractual, contextual, or human judgment.

### Assessment Result

- `PASS`: sufficient valid evidence supports the control objective for the assessed scope and period.
- `FAIL`: evidence demonstrates that the control objective is not met.
- `REVIEW`: evidence is incomplete, conflicting, expired, ambiguous, or requires human/legal judgment.
- `NOT_APPLICABLE`: applicability analysis demonstrates that the control does not apply to the assessed processing context.

`NOT_APPLICABLE` requires documented justification.

## 3. Do Not Collapse Legal and Technical Status

Example:

```text
PDP-ACC-003
Technical observation: SSH root login enabled
Technical test: FAIL
Control result: FAIL

PDP-DPO-001
Technical observation: none
Legal applicability: requires review
Control result: REVIEW
```

A technical scanner MUST NOT produce:

```text
"Organization is non-compliant with UU PDP"
```

The valid formulation is:

```text
"Control PDP-ACC-003 failed for asset srv-01 during this assessment."
```

## 4. Scope

Every assessment MUST identify:

- organization / controller / processor context
- processing activity
- system or asset scope
- Personal Data category
- assessment period
- applicable legal requirements
- applicable controls
- evidence sources

## 5. Evidence Validation

Evidence should be evaluated for:

1. **Relevance** — does it demonstrate the control objective?
2. **Scope** — does it cover the correct system/processing activity?
3. **Freshness** — is it valid for the assessment period?
4. **Integrity** — can it be trusted?
5. **Completeness** — are important sources missing?
6. **Attribution** — is source/owner identifiable?
7. **Repeatability** — can the test be reproduced?

## 6. Evidence Quality

Recommended quality scale:

| Level | Meaning |
|---|---|
| Q0 | No evidence |
| Q1 | Self-asserted / undocumented |
| Q2 | Documented but not independently verifiable |
| Q3 | Verifiable, timestamped evidence |
| Q4 | Continuously collected and integrity-protected/corroborated evidence |

A control can define a minimum acceptable evidence quality.

## 7. Continuous vs Point-in-Time Controls

### Point-in-time
Examples:
- DPO appointment
- transfer agreement
- DPIA approval

### Continuous
Examples:
- unauthorized-access monitoring
- vulnerability monitoring
- FIM
- privileged access monitoring

Wazuh is especially relevant for continuous controls.

## 8. Composite Controls

A control may depend on several tests.

Example:

```text
PDP-SEC-001
  T1 secure configuration
  T2 vulnerability status
  T3 security logging
  T4 integrity monitoring
```

Do not blindly calculate a legal compliance percentage from these tests.

The framework may expose:

- test coverage
- evidence coverage
- control coverage

but these are engineering metrics, not a legal compliance score.

## 9. Exceptions

An exception must include:

- affected control
- affected scope/assets
- business/legal rationale
- risk owner
- compensating control
- approval
- start date
- expiry/review date

An exception is not equivalent to `PASS`.

## 10. Review Roles

Recommended roles:

- `CONTROL_OWNER`
- `TECHNICAL_REVIEWER`
- `PRIVACY_REVIEWER`
- `LEGAL_REVIEWER`
- `AUDITOR`

The same person MAY perform multiple roles in small organizations, but the role should remain explicit in the evidence record.

## 11. Wazuh Assessment Boundary

Wazuh can provide:

- configuration observations
- endpoint and application telemetry
- FIM events
- vulnerability findings
- authentication and privilege events
- incident timelines
- technical evidence retention

Wazuh cannot independently establish:

- validity of consent
- legal basis appropriateness
- whether a transfer safeguard is legally adequate
- whether a DPIA conclusion is sufficient
- whether a DPO appointment legally applies
- whether notification is legally required in a specific case

Those conditions remain subject to human/legal assessment.
