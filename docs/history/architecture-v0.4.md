# Architecture v0.4

## Canonical Chain

```text
┌────────────────────────────┐
│ Legal Source               │
│ UU 27/2022 / Court / Regs  │
└─────────────┬──────────────┘
              v
┌────────────────────────────┐
│ Legal Requirement (LR-*)   │
└─────────────┬──────────────┘
              v
┌────────────────────────────┐
│ PDP Control (PDP-*)        │
└─────────────┬──────────────┘
              v
┌────────────────────────────┐
│ Generic Requirement        │
│ REQ-IAM / CFG / LOG / ...  │
└──────┬─────────────────────┘
       │
       +-------------------+
       v                   v
┌───────────────┐   ┌──────────────────┐
│ Manual / Docs │   │ Wazuh Profile    │
└───────────────┘   └────────┬─────────┘
                             v
                    ┌──────────────────┐
                    │ Wazuh Test       │
                    │ WZ-SCA/RUL/FIM…  │
                    └────────┬─────────┘
                             v
                    ┌──────────────────┐
                    │ Evidence         │
                    └────────┬─────────┘
                             v
                    ┌──────────────────┐
                    │ Finding          │
                    └────────┬─────────┘
                             v
                 Remediation / Exception
```

## Why the Generic Requirement Layer Matters

Without it:

```text
PDP-ACC-003 -> disable SSH root
```

This incorrectly equates a legal-derived control with a Linux-specific implementation.

With the requirement layer:

```text
PDP-ACC-003
   |
   +-- REQ-IAM-001 Authentication Control
   +-- REQ-IAM-002 Privileged Access Control
   +-- REQ-MON-001 Authentication Monitoring
   |
   +-- Wazuh/Linux implementation
   +-- Windows implementation
   +-- Cloud IAM implementation
   +-- Database implementation
```

The control remains stable while implementations evolve.

## Core Object Relations

```text
Organization
  |
  +-- Processing Activity
        |
        +-- Legal Requirements
        +-- PDP Controls
        +-- Generic Requirements
        |
        +-- Assets
              |
              +-- Evidence Sources
              +-- Implementation Profiles
              +-- Tests
              +-- Evidence
              +-- Findings
```

## Data Direction

Legal meaning flows downward:

```text
LAW -> LR -> CONTROL -> REQUIREMENT -> TEST
```

Evidence flows upward:

```text
EVIDENCE -> TEST RESULT -> REQUIREMENT SUPPORT -> CONTROL ASSESSMENT
```

A legal conclusion does not flow automatically upward. Human/legal review remains a separate governed step.
