# Assessment/Findings/Registry Tooling Validation — 2026-09-23

**Scope:** `tools/assessment/assess_controls.py`,
`tools/findings/generate_findings.py`, `tools/evidence/register_evidence.py`.
Unlike the rest of this validation pass, these tools have no Wazuh
dependency — they are pure Python logic operating on normalized JSON, so
this was run locally rather than against the lab host.

**Method:** 8 synthetic evidence documents were constructed by hand
(schema-validated against `framework/schemas/evidence.schema.json`
first), covering every branch of `assess_controls.py`'s precedence logic,
then run through the full `evidence -> assessment -> finding -> registry`
pipeline. No production or lab-derived data was used.

## Scenarios and results

| Synthetic control | Evidence results | `source.collector_health` | Assessment result | Correct? |
|---|---|---|---|---|
| `PDP-TEST-ALLPASS` | PASS, PASS | HEALTHY | `PASS` | Yes |
| `PDP-TEST-FAIL` | FAIL, PASS | HEALTHY | `FAIL` | Yes |
| `PDP-TEST-ERROR` | ERROR, PASS | HEALTHY | `REVIEW` | Yes |
| `PDP-TEST-REVIEW` | REVIEW | HEALTHY | `REVIEW` | Yes |
| `PDP-TEST-COLLECTORFAIL` | **PASS** | **DEGRADED** | `REVIEW` | **Yes — this is the critical case** |

The `PDP-TEST-COLLECTORFAIL` row is the one that matters most: a
technically-passing test result with an unhealthy collector still
produces `REVIEW`, not `PASS`. This confirms
`tools/assessment/assess_controls.py`'s "collector failure never silently
produces PASS" guarantee holds in practice, closing that item in
`release/PRE_1_0_CHECKLIST.md` section E.

All 5 generated `*.assessment.json` files validated successfully against
`framework/schemas/control-assessment.schema.json`.

## Finding generator

`tools/findings/generate_findings.py`, run against the 5 assessments
above, created **exactly one** finding — for `PDP-TEST-FAIL`
(`status: OPEN`, `severity: HIGH`) — and none for the `PASS`, `REVIEW`, or
the collector-degraded case, matching its documented conservative policy
("`FAIL` => create/update `OPEN` finding; `REVIEW`/`PASS` => no automatic
finding"). The generated finding validated successfully against
`framework/schemas/finding.schema.json`.

## Evidence registry

`tools/evidence/register_evidence.py`, run against the same 8 synthetic
evidence documents, produced 8 registry entries (one per evidence
document, each with a `sha256:`-prefixed integrity hash of the original
evidence file and a computed `retention_until`). All 8 validated
successfully against `framework/schemas/evidence-registry.schema.json`.

## No bugs found

Unlike the Wazuh-integration phases of this validation pass, this round
found no defects — `assess_controls.py`, `generate_findings.py`, and
`register_evidence.py` all behaved exactly as documented on first real
test against schema-valid input.

## Retest workflow

The operational retest procedure (re-run the failing test, re-run the
assessment aggregator, and when a finding may be manually closed) was
previously only sketched as a diagram label. It is now documented in
`docs/architecture/retest-workflow.md`, grounded in the verified tool
behavior above — including the explicit design decision that
`generate_findings.py` never auto-closes a finding even when a later
assessment shows `PASS`, so closing one is always a human decision after
reviewing retest evidence.

## Cleanup

All synthetic evidence/assessment/finding/registry files used for this
test were removed afterward
(`implementations/wazuh/tests/results/CASE-TEST-*.evidence.json`,
`runtime/assessments/PDP-TEST-*.assessment.json`, `runtime/findings/`,
`runtime/registry/`) — both directories are already excluded from Git by
`.gitignore`, so no cleanup of tracked files was needed.
