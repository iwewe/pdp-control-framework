# PDP Controls in Wazuh Security Operations — UX, Architecture, and Compliance-Boundary Recommendation

Design reference provided by the project owner, 2026-09-27 (source:
`pdp-control.txt`), for how this framework could eventually be
surfaced as a native menu item inside the Wazuh UI's own **Security
Operations** area, alongside its existing PCI DSS / GDPR / HIPAA /
NIST 800-53 / TSC views — a step beyond the current standalone
imported dashboard (`DASHBOARD_SPEC.yml`). Recorded here as a design
reference, not yet built; see "Status against the current framework"
at the end of each section for what is already implemented vs. still
open.

## 1. Context

Positioning PDP Controls inside Wazuh's Security Operations menu makes
sense from a UX standpoint — the framework's technical evidence comes
from Wazuh telemetry. But it must never be positioned as if Wazuh
itself is issuing a legal verdict or compliance certification under UU
PDP. The framework is a **Compliance Engineering Framework + Control
Framework + Evidence Framework** — not a regulator, legal authority,
certification body, or legal compliance engine.

## 2. Recommended menu position

```
Security operations
├── IT Hygiene
├── PCI DSS
├── GDPR
├── HIPAA
├── NIST 800-53
├── TSC
└── PDP Controls
```

Recommended label: **PDP Controls**. Alternatives: "PDP Control
Framework", "PDP Engineering". Avoid the bare label **"PDP"** — too
generic, risks being read as an official/legal verdict on UU PDP
itself.

## 3. Why Security Operations is a good location

Wazuh's Security Operations function (log collection, authentication
monitoring, privilege monitoring, FIM, SCA, telemetry health,
vulnerability telemetry, PostgreSQL/pgAudit collection, continuous
monitoring) sits directly beneath this framework's own technical
layer:

```
Security Operations
        ↓
Technical Telemetry
        ↓
PDP Control Evidence
        ↓
Control Assessment
```

Security Operations is only *one* evidence source for PDP, and the
framework must keep showing that boundary rather than implying it's
the only one.

## 4. Legal / engineering boundary

```
UU PDP → Legal Requirement → PDP Control → Generic Requirement →
Technical Test → Evidence → Assessment → Finding / Review
```

Wazuh operates at Technical Test / Evidence / Continuous Monitoring
only. It must never be the engine that concludes "the organization
violated UU PDP" or "the organization is compliant with UU PDP":

```
Wazuh Event → Technical Evidence → Control Assessment →
Human / Legal Review (when needed)
```

**Wazuh PASS != legal compliance. Wazuh FAIL != automatic legal
violation.**

**Status against the current framework:** already the framework's
core design principle — see `implementations/wazuh/WAZUH_PROFILE.yml`
(`boundary_statement`) and every dashboard/report disclaimer added
throughout this project.

## 5. Menu naming recommendation

`Security operations → PDP Controls`. Clearer semantically, consistent
with a control-framework model, avoids implying Wazuh is a regulator
or that one dashboard is a legal compliance score, and leaves room for
other implementation profiles later.

## 6. Dashboard should not use a single compliance score

Avoid a single number like "PDP Compliance = 78%" or a
"Compliant/Non-Compliant" toggle — easily misread as a legal
compliance score. Use the engineering assessment results instead:
`PASS` / `FAIL` / `REVIEW` / `NOT_APPLICABLE`.

- **PASS** — required technical evidence for the control assessment is satisfied.
- **FAIL** — the control test produced evidence of failure.
- **REVIEW** — insufficient evidence, problematic telemetry, stale/missing evidence, or human judgment needed.
- **NOT_APPLICABLE** — the control doesn't apply to this processing activity/scope, with a documented justification.

**Status against the current framework:** already how this framework
works — `framework/schemas/control-assessment.schema.json`'s `result`
enum, and `PDP-DASH-001` ("Control Assessment State") on the real
dashboard. `README.md` already states this is "engineering traceability
coverage, not a legal compliance score."

## 7. Recommended PDP Controls dashboard areas

| Area | Purpose | Status against the current framework |
|---|---|---|
| A. Control Assessment State | PASS/FAIL/REVIEW/NOT_APPLICABLE overview | Implemented — `PDP-DASH-001` |
| B. Evidence Health | Evidence source condition | Implemented — `PDP-DASH-002` ("Evidence Health"), but with a **different enum** than recommended here (`SUFFICIENT/DEGRADED/INSUFFICIENT/UNKNOWN` vs. the `EXPECTED/AVAILABLE/DEGRADED/STALE/MISSING` proposed in this note). Not reconciled — would be a breaking schema change post-1.0.0; needs an explicit decision, not a silent change. See section 6.F below. |
| C. Findings (severity + lifecycle) | Operational remediation | Implemented — `PDP-DASH-003`/`PDP-DASH-004`, finding `status`/`severity` enums already match |
| D. Review Queue | Controls/findings needing manual, document, legal, or applicability review | Implemented — `PDP-DASH-005` ("Controls Requiring Review") filters `pdp-assessment-*` on `result: REVIEW` (assessment level); `PDP-DASH-004`'s `legal_review_state` bucket (finding level); and, for the specific example areas this section names (lawful basis, consent validity, DPIA, DPO applicability, ...), `tools/reporting/generate_legal_review_queue.py` / `reports/LEGAL_REVIEW_QUEUE.md` PLUS a 9th dashboard panel, `PDP-DASH-009` ("Legal / Manual Review Queue", `pdp-legal-review*` index, added 2026-09-27) — so a DPO can see this queue directly on the dashboard, not only in the repository. See "Implemented in this pass" below. |
| E. Technical Coverage | AUTOMATED/PARTIAL/MANUAL coverage, not a compliance percentage | Implemented — `framework/requirements/CONTROL_REQUIREMENTS.yml` coverage classification, `reports/COVERAGE_REPORT.md` |
| F. Evidence Quality | Q0-Q4 scale | Implemented — `PDP-DASH-006` ("Evidence Quality Distribution"), and the `quality.level` enum in `framework/schemas/evidence.schema.json` already matches this note's Q0-Q4 scale exactly |
| G. PDP Events Over Time | Technical event trend, explicitly not incident/breach count | Implemented — `PDP-DASH-007` |

## 8. Recommended disclaimer

> "Engineering control and evidence status. Not a legal compliance determination."
>
> ("Status ini merupakan hasil assessment kontrol dan evidence
> engineering, bukan penetapan kepatuhan hukum.")

Should appear on the dashboard, in documentation, and on any exported
report — not just buried in technical docs.

**Status against the current framework:** the dashboard's own
description field already carries an equivalent line ("Dashboard
reports engineering control/evidence state, not a legal compliance
score" — `implementations/wazuh/dashboard/generate_dashboard_ndjson.py`).
Added the exact bilingual wording from this note to `README.md` and
`implementations/wazuh/dashboard/README.md` in this pass, so it's
visible in both places a viewer is likely to look first, not only in
the dashboard UI itself.

## 9. PDP Controls page information architecture

```
PDP Controls
├── Overview
├── Controls
├── Evidence
├── Findings
├── Review Queue
├── Processing Activities
├── Assets
├── Technical Coverage
└── Traceability
```

**Status against the current framework:** the real dashboard is
currently one page of 8 (now 8, unchanged panel count — see below)
panels, not this multi-page IA. Building a full multi-page native
Wazuh UI plugin matching this structure is a larger undertaking than a
saved-objects dashboard and is out of scope for this pass; recorded
here for a future implementation profile.

## 10. Traceability view

```
PDP-ACC-002 → REQ-MON-002 → WZ-RUL-xxx → Evidence EV-xxx →
Processing Activity PA-xxx → Asset ASSET-xxx → Legal Requirement LR-xxx
```

**Status against the current framework:** implemented —
`PDP-DASH-008` ("Technical Traceability"), and the underlying data
model (`framework/schemas/*.json`, `implementations/wazuh/manifests/TRACEABILITY.yml`)
already carries this full chain.

## 11-12. Recommended user flow / example operational flow

Overview → control with FAIL/REVIEW → control detail → evidence detail
→ asset/processing activity → finding → remediation → retest.

**Status against the current framework:** the data model supports this
drill-down (shared IDs across evidence/assessment/finding documents),
but the dashboard doesn't yet implement clickable drill-through between
panels — a saved-search/drilldown feature of the dashboard app itself,
not yet configured on `implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson`.

## 13. Relation with other Wazuh compliance menu items

PDP Controls can sit visually at the same menu level as PCI
DSS/GDPR/HIPAA/NIST 800-53/TSC, but internally must stay:

```
PDP Control Framework → Wazuh Implementation Profile
```

not tightly coupled to Wazuh's own UI, so the framework can add other
implementation profiles later (IAM, Cloud, Database, Manual
Assessment) without Wazuh's UI being the only view of it.

**Status against the current framework:** already the framework's
design — see `FRAMEWORK_MANIFEST.yml`'s `implementation_profiles` list
(currently `[wazuh]`, designed to be extended) and
`docs/architecture/compliance-operating-model.md`.

## 14. Recommended terminology

**Use:** Control, Assessment, Evidence, Finding, Review, Coverage,
Technical Monitoring, Engineering Status.

**Avoid:** Certified, Legally Compliant, Compliant Organization,
Official PDP Score, Legal PASS, PDP Certification.

**Status against the current framework:** added as explicit
contributor guidance in `implementations/wazuh/dashboard/README.md`
in this pass (2026-09-27), so future dashboard/report authors don't
reintroduce this language.

## 15. Positioning statement

> "PDP Controls provides a technical control, evidence, and assessment
> view for the PDP Control Framework using Wazuh telemetry. It
> supports compliance engineering but does not constitute a legal
> compliance determination."
>
> ("PDP Controls menyediakan tampilan kontrol, evidence, dan assessment
> teknis untuk PDP Control Framework dengan memanfaatkan telemetry
> Wazuh. Fitur ini mendukung compliance engineering dan tidak
> merupakan penetapan kepatuhan hukum.")

Added to `README.md` in this pass.

## 16-18. Final recommendation / architectural principle / summary

```
LAW / REGULATION
      ↓
PDP CONTROL FRAMEWORK
      ↓
CONTROL + REQUIREMENT + EVIDENCE MODEL
      ↓
WAZUH IMPLEMENTATION PROFILE
      ↓
SECURITY OPERATIONS / PDP CONTROLS UI
```

Not `WAZUH → LEGAL COMPLIANCE ENGINE`. Never expose a single legal
compliance score, a compliant/non-compliant legal verdict, or an
automatic conclusion of UU PDP violation.

## Implemented in this pass (2026-09-27)

- `README.md`, `implementations/wazuh/dashboard/README.md`: added the
  bilingual positioning statement and disclaimer text verbatim from
  sections 8 and 15.
- `implementations/wazuh/dashboard/README.md`: added the recommended/avoid
  terminology list from section 14.
- `implementations/wazuh/dashboard/DASHBOARD_SPEC.yml`: added
  `legal_review_state` as a bucket on `PDP-DASH-004` ("Findings by
  Processing Activity"), so a finding pending legal review is visible
  directly in that table — the finding-level half of the "Review
  Queue" concept in section 7.D that the existing `PDP-DASH-005`
  panel didn't cover (that panel only surfaces assessment-level
  `result: REVIEW`, not finding-level `legal_review_state`).
  Regenerated and reconfirmed against the real lab.
- `tools/reporting/generate_legal_review_queue.py`,
  `reports/LEGAL_REVIEW_QUEUE.md`,
  `framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml` (added
  2026-09-27): a real, working queue for the specific areas section
  7.D names as needing human/legal review (lawful basis, consent
  validity, DPIA sufficiency, DPO applicability, and similar) — these
  have no Wazuh technical coverage at all (`NO_TECHNICAL_COVERAGE` in
  `reports/COVERAGE_REPORT.json`, 32 of 64 legal requirements), so they
  get a dedicated hand-maintained worksheet. The generator classifies
  each into a review category from its `requirement_summary` text and
  adds any newly-appearing requirement to the worksheet with status
  `NOT_REVIEWED`; it never overwrites or deletes an existing entry, so
  a reviewer's recorded progress (`status`/`reviewer`/`reviewed_at`/`notes`)
  always survives re-running it — confirmed with a round-trip test
  before this was committed.
- `framework/schemas/legal-review-item.schema.json`,
  `implementations/wazuh/indexer/templates/pdp-legal-review-template.json`,
  `tools/export/export_legal_review_ndjson.py`, and `PDP-DASH-009` on
  the dashboard itself (added 2026-09-27, same day): the queue is also
  indexed as its own `pdp-legal-review` registry (a single,
  non-time-series index — documents are upserted in place by
  `legal_requirement_id` as review status changes, unlike the
  append-only `pdp-evidence-*`/`pdp-assessment-*`/`pdp-findings-*`
  indices) and surfaced as a real dashboard panel, so a DPO or legal
  reviewer sees it directly on the dashboard rather than needing to
  read the repository. Confirmed live on the real lab: template
  installed, all 32 items indexed with 0 errors, panel and index
  pattern both discoverable, existing `pdp_dashboard_viewer`/`_editor`
  RBAC roles already cover it via their existing `pdp-*` index-pattern
  grant (no RBAC change needed).

## Explicitly NOT done in this pass — needs an explicit decision

**Evidence Health terminology** (section 7.B): this note recommends
`EXPECTED / AVAILABLE / DEGRADED / STALE / MISSING`. The framework's
actual `evidence_health` enum (`framework/schemas/control-assessment.schema.json`)
is `SUFFICIENT / DEGRADED / INSUFFICIENT / UNKNOWN`, already used by
real indexed data and the real `PDP-DASH-002` panel. Changing the enum
is a breaking schema change post-1.0.0 (existing indexed documents,
the index template, and every panel referencing `evidence_health`
would need to migrate together) and was not made silently here. If
this reconciliation is wanted, it should be scoped and versioned as
its own change.

A full multi-page native Wazuh UI IA (section 9) and clickable
panel-to-panel drill-through (sections 11-12) are recorded as future
work, not built in this pass.

## Addendum, 2026-09-27 — native "Compliance" card investigated and ruled out

The project owner asked whether "PDP Controls" could appear as an
option in Wazuh's own native per-agent **Compliance** card dropdown
(`/app/endpoints-summary#/agents?tab=welcome&agent=<id>`) — the same
card that already lists PCI DSS, GDPR, HIPAA, NIST 800-53, TSC. This
is a different, more specific ask than section 9's "full multi-page
native UI" (which is about a whole new top-level menu item); this one
is about extending an existing, compiled Wazuh UI element.

**Investigated directly on the real lab, not assumed:** the compliance
framework list is not driven by any configuration file.
`/etc/wazuh-indexer/opensearch_dashboards.yml` has no relevant key, and
no JSON manifest anywhere under
`/usr/share/wazuh-dashboard/plugins/wazuh/` registers the available
frameworks. The only related files found
(`common/compliance-requirements/{gdpr,hipaa,nist,pci,tsc}-requirements.js`)
are compiled server-side data consumed by the PDF **reporting**
feature (`server/lib/reporting/extended-information.js`) — mapping a
requirement code to its human-readable description for a report, not
the source of the dropdown itself. The dropdown's framework list is
compiled into the plugin's frontend bundle. Wazuh's rule schema also
has no `<pdp>` compliance tag slot at all — `<gdpr>`, `<hipaa>`,
`<pci_dss>`, `<nist_800_53>`, `<tsc>` are the fixed, built-in set; this
framework's own rules use a separate mechanism (group tags like
`pdp_req_mon_001`, plus the `compliance:` block on SCA checks), which
Wazuh's compliance-card code has no knowledge of.

**Conclusion: not attempted.** Making "PDP Controls" a real option in
that dropdown would require forking and patching
`wazuh-dashboard`'s own plugin source and shipping a custom-built
package — not a supported extension point, and something that would
need to be redone on every future Wazuh Dashboard upgrade. The
maintenance burden was judged not worth it against the alternative
already built: the standalone `PDP Continuous Control Dashboard`
(`implementations/wazuh/dashboard/`), reached through the ordinary,
upgrade-safe Dashboards app.

**Discoverability alternative considered, also not applied:**
OpenSearch Dashboards has a global `defaultRoute` advanced setting
(confirmed on this lab: currently `/app/wz-home`) that controls what
every user sees on login — setting it to the PDP dashboard's URL would
make it the landing page for anyone who logs in, including the SOC
team that also uses this same Wazuh instance for its ordinary security
operations work. Changing a shared, global setting to benefit one
stakeholder (the DPO) at the cost of disrupting everyone else's daily
workflow was judged the wrong trade-off, so this was **not applied**.

**Recommended path, deferred by the project owner for now:** create a
dedicated internal user for the DPO, scoped to the existing
`pdp_dashboard_viewer` role (`implementations/wazuh/dashboard/rbac/`,
live-tested end to end already — see `RBAC_EVIDENCE_2026-09-24.md`).
That gives the DPO their own login and lets them set their own browser
bookmark/default tab to the PDP dashboard URL, without touching any
setting shared with the SOC team. The project owner plans to define
this as part of a separate DPO onboarding SOP rather than create the
account ad hoc now; `implementations/wazuh/dashboard/rbac/README.md`
"Applying this" already documents the exact steps (create the
internal user, hash a password, assign the `pdp_viewer` backend role)
whenever that SOP is ready to use them.
