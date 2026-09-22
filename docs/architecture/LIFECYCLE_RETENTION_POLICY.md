# Lifecycle and Retention Policy

**Status:** Pre-1.0 draft

## 1. Purpose

This policy governs framework-generated evidence, assessments, findings, exceptions, validation artifacts, and release metadata.

Retention values in this document are **framework defaults**, not statutory UU PDP retention periods.

## 2. Object lifecycle

### Evidence

```text
ACTIVE
  -> STALE
  -> SUPERSEDED
  -> RETIRED
```

Evidence may become stale because:

- freshness threshold exceeded,
- source/collector retired,
- asset scope changed,
- test definition changed,
- a newer evidence object supersedes it.

### Assessment

```text
DRAFT
  -> CURRENT
  -> SUPERSEDED
  -> ARCHIVED
```

### Finding

```text
OPEN
  -> IN_PROGRESS
  -> RISK_ACCEPTED
  -> RESOLVED
  -> CLOSED
```

`RESOLVED` means remediation/retest indicates the technical condition is corrected.
`CLOSED` requires workflow closure and should retain the historical evidence chain.

### Exception

```text
PROPOSED
  -> ACTIVE
  -> EXPIRED
  -> REVOKED
```

An active exception never converts a failed control into `PASS`.

## 3. Recommended default retention

| Object | Default | Rationale |
|---|---:|---|
| Normalized technical evidence | 365 days | Continuous control reconstruction |
| Control assessments | 730 days | Historical assessment comparison |
| Findings | Closure + 730 days | Remediation/audit history |
| Exceptions | Expiry/revocation + 730 days | Risk acceptance history |
| Lab validation results | Life of supported implementation + 365 days | Regression/support evidence |
| Release manifests | Indefinite | Framework provenance |

These defaults must be reviewed against organizational, contractual, sectoral, and legal requirements.

## 4. Data minimization

Framework indices should contain normalized evidence rather than raw business content.

Avoid storing by default:

- raw document contents,
- credentials,
- secrets,
- SQL parameter values,
- complete database rows,
- unnecessary personal identifiers,
- full logs when a source reference is sufficient.

## 5. Evidence integrity

Where practical, evidence registry entries should include:

```text
SHA-256
source reference
collection timestamp
scope
test ID
control ID
legal requirement traceability
```

## 6. Reassessment triggers

Reassessment is required when:

- processing purpose materially changes,
- a new Personal Data category is added,
- a new processor/subprocessor is introduced,
- cross-border transfer changes,
- critical infrastructure changes,
- major control failure occurs,
- material breach/incident occurs,
- legal source or authoritative interpretation changes,
- implementation test meaning changes.

## 7. Framework release retention

Release artifacts for tagged releases should never be rewritten.

Corrections should produce a new release/version.
