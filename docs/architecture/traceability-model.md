# Traceability Model

## Core Rule

No implementation test should point directly to a statute without passing through a stable control.

```text
Legal Source
    |
Legal Requirement (LR)
    |
PDP Control
    |
Control Test
    |
Evidence
    |
Implementation
```

Example:

```text
UU 27/2022 Article 39(1)
        |
        v
LR-039-01
Prevent unauthorized access
        |
        +------------------+
        |                  |
        v                  v
PDP-ACC-003          PDP-LOG-001
        |                  |
        v                  v
WZ-SCA-ACC-001       WZ-RULE-ACC-001
        |                  |
        v                  v
sshd_config          auth/security events
```

## Why LR IDs Are Separate

A legal provision may:

- generate multiple controls,
- be amended,
- receive a court interpretation,
- have exceptions,
- be clarified by implementing regulation.

A stable control may also map to multiple legal requirements.

Therefore:

```text
Article != Control
Legal Requirement != Control
Control != Test
Test != Evidence
```

This separation is required for long-term maintainability.
