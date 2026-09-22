# PDP Control Framework

**Status:** Draft v0.1  
**Primary legal source:** Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)  
**Jurisdiction:** Indonesia  
**Project model:** Technology-neutral control framework with pluggable implementation/evidence engines  
**Initial implementation target:** Wazuh

> This project is a compliance engineering framework, not legal advice and not a legal certification mechanism.

## 1. Purpose

PDP Control Framework translates legal obligations in Indonesia's personal data protection regime into structured control objectives, evidence requirements, assessment methods, and implementation guidance.

The framework deliberately separates:

1. **Legal requirement** — what the law requires.
2. **Control objective** — what an organization must achieve.
3. **Evidence requirement** — what demonstrates implementation.
4. **Assessment method** — how the control is evaluated.
5. **Implementation profile** — technologies or procedures that can implement or provide evidence for the control.

Wazuh is therefore **one implementation/evidence engine**, not the framework itself.

## 2. Design Principles

### 2.1 Legal-source-first
Every control must trace back to one or more legal provisions.

### 2.2 Technology-neutral core
Core controls must not depend on Wazuh, a specific SIEM, IAM product, cloud provider, or operating system.

### 2.3 Evidence-oriented
A control is not considered implemented merely because a policy exists. The framework distinguishes documentary, organizational, technical, and operational evidence.

### 2.4 No false legal-compliance claim
A technical PASS does not mean an organization is legally compliant with UU PDP as a whole.

The framework therefore distinguishes:

- **Control assessment result:** `PASS`, `FAIL`, `REVIEW`, `NOT_APPLICABLE`
- **Assessment method:** `AUTOMATED`, `PARTIAL`, `MANUAL`

### 2.5 Human governance
Controls involving lawful basis, proportionality, consent validity, data-subject rights, DPIA conclusions, DPO appointment, and cross-border transfer adequacy normally require human/legal review.

### 2.6 Extensible mappings
Controls may later be mapped to other frameworks without changing their identity, including:

- ISO/IEC 27001
- NIST Cybersecurity Framework
- CIS Controls
- GDPR
- sector-specific requirements

## 3. Legal Baseline

The initial legal baseline is:

- **UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi**
- Relevant Constitutional Court decisions affecting interpretation of the law

### 3.1 Constitutional Court update: Article 53

Decision **151/PUU-XXII/2024**, pronounced on **30 July 2025**, conditionally invalidated the word `dan` in Article 53(1)(b) unless interpreted as `dan/atau`.

Implementation profiles and organizational assessments MUST account for this interpretation when evaluating the obligation to appoint an officer/person performing the Personal Data Protection function.

## 4. Framework Layers

```text
LEGAL
  UU PDP / court interpretation
      |
      v
CONTROL
  control objective
      |
      v
ASSESSMENT
  automated / partial / manual
      |
      v
EVIDENCE
  documentary / organizational / technical / operational
      |
      v
IMPLEMENTATION
  Wazuh / IAM / database audit / cloud / manual audit / etc.
```

## 5. Control Domains

| Namespace | Domain | Purpose |
|---|---|---|
| PDP-GOV | Governance & Accountability | Organizational accountability and demonstrable compliance |
| PDP-LAW | Lawful Processing | Lawful basis and purpose limitation |
| PDP-CNS | Consent Management | Consent collection, proof, withdrawal |
| PDP-RGT | Data Subject Rights | Requests, access, correction, restriction |
| PDP-DATA | Data Quality & Processing Records | Accuracy, verification, records of processing |
| PDP-DPIA | Risk & Impact Assessment | High-risk processing assessment |
| PDP-SEC | Security Safeguards | Technical and operational safeguards |
| PDP-ACC | Access & Confidentiality | Unauthorized access prevention and confidentiality |
| PDP-LOG | Logging & Monitoring | Traceability and processing/activity monitoring |
| PDP-RET | Retention, Deletion & Destruction | Lifecycle termination and secure disposal |
| PDP-INC | Incident & Breach Management | Detection, evidence, notification and recovery |
| PDP-PRC | Processor & Third Party | Processor instruction and subprocessor governance |
| PDP-DPO | PDP Officer / Function | Appointment, capability and function |
| PDP-TRF | Data Transfer | Domestic and cross-border transfers |

## 6. Control Identity

A control identifier is stable and technology-neutral:

```text
PDP-<DOMAIN>-<NUMBER>
```

Example:

```text
PDP-SEC-001
PDP-INC-003
PDP-TRF-002
```

IDs MUST NOT encode Wazuh rule IDs or product-specific identifiers.

## 7. Control Schema

Each control SHOULD contain:

```yaml
id: PDP-SEC-001
title:
  id: Langkah teknis dan operasional
  en: Technical and operational safeguards

legal_basis:
  - instrument: UU-27-2022
    article: 35
    paragraph: 1

objective:
  id: >
    Organisasi menetapkan dan menerapkan langkah teknis dan
    operasional untuk melindungi Data Pribadi.
  en: >
    The organization establishes and implements technical and
    operational measures to protect Personal Data.

assessment_method: PARTIAL

evidence:
  documentary: []
  organizational: []
  technical: []
  operational: []

implementation_profiles:
  wazuh:
    applicability: HIGH
    capabilities:
      - sca
      - vulnerability-detection
      - log-analysis
      - fim
```

## 8. Assessment Model

### 8.1 Assessment method

**AUTOMATED**  
The primary control condition can be evaluated reliably by machine-readable evidence.

**PARTIAL**  
Automation can provide meaningful evidence, but human review is required for the complete control.

**MANUAL**  
The core legal or organizational condition cannot be reliably determined by technical monitoring alone.

### 8.2 Assessment result

**PASS** — sufficient evidence supports the control objective.  
**FAIL** — evidence shows the control objective is not met.  
**REVIEW** — evidence is incomplete, ambiguous, or requires human interpretation.  
**NOT_APPLICABLE** — documented scope analysis determines the control does not apply.

`NOT_APPLICABLE` MUST include justification.

## 9. Evidence Model

Evidence is classified into four categories.

### Documentary
Examples:
- privacy policy
- retention schedule
- processor agreement
- DPIA
- data-processing register
- consent record

### Organizational
Examples:
- role assignment
- DPO appointment
- approval record
- review record
- incident-response responsibility

### Technical
Examples:
- secure configuration
- authentication logs
- database audit logs
- vulnerability findings
- FIM events
- endpoint alerts
- network telemetry

### Operational
Examples:
- incident ticket
- restoration record
- notification timestamp
- deletion execution record
- access-review result

## 10. Relationship With Wazuh

Wazuh is initially treated as:

```text
Implementation Engine
+
Detection Engine
+
Evidence Collection Engine
+
Continuous Control Monitoring Engine
```

Possible Wazuh capability mapping:

| Capability | Framework use |
|---|---|
| SCA | Configuration and hardening evidence |
| FIM | Integrity/change evidence |
| Log Analysis | Authentication, privilege, application and database events |
| Vulnerability Detection | Exposure and remediation evidence |
| Active Response | Optional containment implementation |
| Agent Groups | PDP asset / processing profile classification |
| Custom Rules | PDP-specific detection |
| Dashboard / Index | Evidence visualization and control monitoring |

Wazuh MUST NOT determine legal conclusions that require legal or organizational interpretation.

## 11. Initial Legal Scope

Version 0.1 focuses on obligations relevant to controllers and processors, primarily Articles 20–56.

Priority groups:

1. Articles 20–33 — lawful basis, consent, transparency, accuracy, processing records and subject access.
2. Article 34 — Data Protection Impact Assessment.
3. Articles 35–39 — security, confidentiality, supervision and unauthorized access prevention.
4. Articles 40–45 — withdrawal, restriction, retention, deletion and destruction.
5. Articles 46–47 — breach notification and accountability.
6. Articles 51–52 — processor obligations.
7. Articles 53–54 — PDP officer/function.
8. Articles 55–56 — data transfers.

## 12. Repository Architecture

```text
pdp-control-framework/
├── README.md
├── PDP_CONTROL_FRAMEWORK.md
├── controls/
│   └── CONTROL_CATALOGUE.yml
├── legal/
│   ├── README.md
│   └── uu-27-2022/
├── mappings/
│   ├── README.md
│   └── uu27-2022.yml
├── evidence/
│   └── evidence-types.yml
├── implementations/
│   └── wazuh/
│       ├── README.md
│       ├── sca/
│       ├── rules/
│       ├── decoders/
│       └── dashboards/
└── docs/
    ├── methodology.md
    ├── limitations.md
    └── terminology.md
```

## 13. Future Crosswalk

A future mapping MAY connect a single PDP control to multiple external standards.

```text
PDP-SEC-xxx
   ├── UU PDP
   ├── ISO/IEC 27001
   ├── NIST CSF
   ├── CIS Controls
   └── GDPR
```

External-standard mappings are informative crosswalks and MUST NOT change the meaning of the PDP control.

## 14. Versioning

Recommended model:

- `0.x` — research/draft
- `1.0` — reviewed baseline
- major versions — control meaning or structure changes
- minor versions — new controls or mappings
- patch versions — corrections that do not alter control intent

Legal-source changes SHOULD trigger a documented framework review.

## 15. Current Limitations

- This draft has not undergone formal legal review.
- The framework does not certify legal compliance.
- Technical evidence does not replace organizational or legal evidence.
- Applicability depends on the organization's processing context.
- Secondary regulations and sector-specific rules may introduce additional obligations.
- Crosswalks to ISO/NIST/CIS/GDPR are not yet normative.

## 16. Authoritative Sources

- JDIH Kementerian Komunikasi dan Digital — UU No. 27 Tahun 2022
  - https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/crc32/
- Mahkamah Konstitusi — Putusan 151/PUU-XXII/2024
  - https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024

---

**Draft status:** This document is intended to become the normative architecture document for the repository.
