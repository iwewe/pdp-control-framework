# PDP Compliance Operating Model

**Status:** Current architecture document (introduced in draft v0.3, part of 0.10.0-rc2)

## 1. End-to-End Model

```text
                     LEGAL LAYER
                         |
               +---------+---------+
               |                   |
          Legal Source        Court / Regulation
               |                   |
               +---------+---------+
                         |
                 Legal Requirement
                         |
                         v
                   PDP Control
                         |
        +----------------+----------------+
        |                                 |
        v                                 v
Processing Activity                  Control Test
        |                                 |
        v                                 v
     Assets ------------------------> Evidence
        |                                 |
        +----------------+----------------+
                         |
                         v
                      Finding
                         |
              +----------+----------+
              |                     |
         Remediation             Exception
              |                     |
              +----------+----------+
                         |
                         v
                       Retest
```

## 2. Governance Roles

Suggested framework roles:

### Framework Maintainer
Maintains control semantics, schemas, repository versioning, and mappings.

### Legal Reviewer
Reviews legal requirement interpretation and legal applicability.

### Privacy Reviewer
Reviews processing activities, DPIA, subject rights, consent and privacy governance.

### Control Owner
Owns implementation of a specific control or control family.

### Technical Owner
Owns systems/assets and remediation.

### Evidence Owner
Ensures evidence sources remain available, reliable and retained.

### Auditor / Independent Reviewer
Validates assessment and evidence independently where required.

## 3. Review Triggers

Framework-level review:

- amendment of UU PDP
- Constitutional Court decision
- new implementing regulation
- authoritative regulator guidance
- material jurisprudence

Processing-level reassessment:

- new purpose
- new data type
- new processor
- cross-border transfer
- high-risk technology
- architecture change
- serious incident
- major control failure

## 4. States

### Processing Activity
`DRAFT`, `REVIEW`, `ACTIVE`, `REASSESS`, `SUSPENDED`, `TERMINATED`

### Control Assessment
`PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`

### Evidence Source
`ACTIVE`, `DEGRADED`, `MISSING`, `RETIRED`

### Finding
`OPEN`, `IN_PROGRESS`, `RISK_ACCEPTED`, `RESOLVED`, `CLOSED`

### Exception
`PROPOSED`, `ACTIVE`, `EXPIRED`, `REVOKED`

## 5. Wazuh Boundary

Wazuh enters at the Test and Evidence layers.

```text
Wazuh SHOULD:
- collect
- detect
- test
- timestamp
- correlate
- preserve technical observations

Wazuh SHOULD NOT:
- select lawful basis
- decide consent validity
- decide legal applicability
- issue legal compliance certification
- decide whether cross-border safeguards are legally adequate
```

This boundary protects the framework from becoming product-specific or legally over-assertive.
