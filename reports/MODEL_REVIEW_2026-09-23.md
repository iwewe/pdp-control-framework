# Legal/Control/Model Review — 2026-09-23

**Scope:** `release/PRE_1_0_CHECKLIST.md` sections A (Legal layer, remaining
items), B (Control architecture, remaining items), C (Processing /
applicability, all items). This is a documentation/consistency review, not
a Wazuh runtime validation — no lab access was required.

## Section A — Legal layer

### No control text claims more than the legal source supports

Systematic keyword search across `framework/controls/CONTROL_CATALOGUE.yml`
for overclaiming language (`compliant`, `compliance`, `guarantee`,
`menjamin`, `legally`, `patuh`, `kepatuhan`, etc.) and separately for
stronger phrases (`fully compliant`, `satisfies UU`, `legally compliant`,
`proves compliance`). Every hit was reviewed manually:

- `PDP-RET-003`'s objective mentions "...when legally required" —
  describing the *statutory trigger condition* for destruction (Article
  44), not claiming the system itself achieves compliance.
- `PDP-DPO-003`'s title/objective ("Compliance monitoring by PDP
  function") describes the *DPO's own legally-defined job duty* per
  Article 54(1) using the law's own terminology for that role, not a
  claim that the framework or a technical control makes the organization
  compliant.

No genuine overclaiming found.

### Legal summaries are clearly identified as framework interpretations

`framework/legal/LEGAL_MAPPING.yml`'s `requirement_summary` fields are
condensed Indonesian paraphrases of statutory text, and
`framework/controls/CONTROL_CATALOGUE.yml`'s `objective` fields are the
framework's own interpretation of what a control should achieve — neither
file previously stated this explicitly. **Fixed** by adding
`metadata.requirement_summary_disclaimer` to `LEGAL_MAPPING.yml` and
`framework.objective_disclaimer` to `CONTROL_CATALOGUE.yml`, each pointing
back to the authoritative source for the exact statutory wording.

### Implementing regulations/guidance

UU No. 27 Tahun 2022 itself mandates implementing government regulations
within its transitional period. This review has no verified knowledge of
whether such a regulation has since been enacted (beyond this assistant's
knowledge cutoff, and not otherwise checked against a live authoritative
source in this pass). Rather than assume "none exists" or fabricate a
citation, this is recorded as an **explicit open item** in
`framework/legal/review/LEGAL_REVIEW_STATUS.yml`
(`implementing_regulations.status: NOT_REVIEWED`), so a future reviewer
checks the authoritative source before treating the legal mapping as
complete for 1.0.

## Section B — Control architecture

### Assessment method/result semantics are consistent

Cross-checked every place these vocabularies are used:

| Layer | Values found | Notes |
|---|---|---|
| `CONTROL_CATALOGUE.yml` `assessment_method` | `MANUAL`, `PARTIAL` | No control currently claims `AUTOMATED` — consistent, since a *control* (as opposed to a single test) almost always needs some documentary/organizational evidence too. |
| `WAZUH_TEST_CATALOGUE.yml` `assessment` | `AUTOMATED` | Consistent — individual Wazuh tests are automated by definition. |
| `evidence.schema.json` `result` enum | `PASS`/`FAIL`/`REVIEW`/`ERROR`/`NOT_APPLICABLE` (5) | Individual test outcome. |
| `control-assessment.schema.json` `result` enum | `PASS`/`FAIL`/`REVIEW`/`NOT_APPLICABLE` (4, no `ERROR`) | Aggregate control outcome. |

The 5-vs-4 difference is intentional, not a bug: `tools/assessment/assess_controls.py`
folds any evidence-level `ERROR` into an aggregate `REVIEW` (confirmed by
real execution in `reports/TOOLS_PIPELINE_VALIDATION_2026-09-23.md`) —
"the underlying test errored" is not a distinct *control*-level state,
it is one of the reasons a control needs human review.

### `NOT_APPLICABLE` requires justification — found unenforced, fixed

`docs/architecture/assessment-methodology.md` states "`NOT_APPLICABLE`
requires documented justification", but
`framework/schemas/control-assessment.schema.json` did not enforce this —
`result: NOT_APPLICABLE` with `notes: null` validated successfully.
**Fixed** by adding a conditional (`allOf`/`if`/`then`) rule: when
`result` is `NOT_APPLICABLE`, `notes` is now required and must be a
non-empty string. Verified directly:

```
NOT_APPLICABLE without notes -> rejected ("None is not of type 'string'")
NOT_APPLICABLE with notes    -> accepted
existing PASS example        -> still accepted (unaffected)
```

## Section C — Processing / applicability

### Processing Activity model

`framework/models/PROCESSING_ACTIVITY_MODEL.md` section 6 lists 13
"Minimum Required Fields" for assessment readiness. Checked
`examples/processing-activity.example.yml` against that list —
`processing_operations` and `retention` were both missing. **Fixed** by
adding them (matching the model's own recommended schema in section 2).

### Asset model

`framework/models/ASSET_MODEL.md` reviewed for internal consistency
(asset types, criticality dimensions, technical-identifier separation,
lifecycle states) — no issues found. Unlike the Processing Activity and
Profile models, there is no committed `examples/asset.example.yml`; not
required by this checklist item's literal wording, but worth adding in a
future pass.

### Control Profile composition — found and fixed a real composition bug

`examples/profile-application.example.yml` previously contained a single
scenario (3 profiles applied to one database asset) whose
`effective_requirements` list was checked programmatically against the
mathematically correct union of the 3 applied profiles'
`required_requirements` (per `framework/profiles/CONTROL_PROFILES.yml`).
**It did not match** — 5 requirements were missing
(`REQ-GOV-001`, `REQ-INV-001`, `REQ-INV-002`, `REQ-RET-001`, `REQ-RET-002`).

**Fixed** by rewriting the example with 3 distinct, realistic scenarios,
each with a programmatically-verified-correct `effective_requirements`:

1. `ASSET-DB-001` — `BASELINE` + `HIGH-RISK` + `DATABASE` (high-risk HR
   database).
2. `ASSET-PAYROLL-GATEWAY-001` — `BASELINE` + `PROCESSOR` (data forwarded
   to an external payroll processor).
3. `ASSET-WAZUH-MANAGER-001` — `BASELINE` + `SECURITY-MONITORING` (see
   dogfooding note below).

Verification script (union of each applied profile's
`required_requirements` vs. the example's `effective_requirements`):
all 3 scenarios `MATCH`.

### High-risk processing profile

`PDP-PROFILE-HIGH-RISK` reviewed: its `required_requirements` is a
superset of `PDP-PROFILE-BASELINE`'s plus risk-specific additions
(`REQ-CRY-001`/`002`, `REQ-AVL-001`/`002`, `REQ-INC-003`,
`REQ-RET-001`/`002`), and its own `notes` field already correctly
disclaims that the profile does not itself determine DPIA applicability.
Confirmed no `REQ-*` requirement maps to `PDP-DPIA-001`/`PDP-DPIA-002` —
correct, since DPIA is a documentary/organizational control with
`assessment_method: MANUAL` and Wazuh `applicability: NONE`/`MEDIUM` in
`CONTROL_CATALOGUE.yml`, not something a generic technical requirement
layer should claim to satisfy.

### Security monitoring platform dogfooding example

Scenario 3 above (`ASSET-WAZUH-MANAGER-001`) models the Wazuh
manager/indexer/dashboard used to *implement* this framework as an asset
*in scope of* this framework — because it itself processes user,
endpoint, and activity metadata, it is not exempt from its own controls.
Cross-referenced `implementations/wazuh/README.md` section "Privacy of
Monitoring" for the corresponding operational guidance.

## Bugs found and fixed in this review

1. `framework/schemas/control-assessment.schema.json` — `NOT_APPLICABLE`
   result was not required to carry a justification, contradicting
   documented methodology.
2. `examples/processing-activity.example.yml` — missing 2 of the
   Processing Activity model's own minimum required fields.
3. `examples/profile-application.example.yml` — `effective_requirements`
   did not match the correct union of applied profiles' requirements (5
   missing requirements).
4. 12 framework/implementation YAML files carried stale `version: 0.X.0-draft`
   markers not updated since their introduction, inconsistent with the
   current `0.10.0-rc2` framework version (the same class of drift fixed
   in `.md` files during the 2026-09-22 hardening pass, missed for
   `.yml` files at the time). Fixed by bumping `version` to `0.10.0-rc2`
   and preserving the original marker as `introduced_in_draft`.
