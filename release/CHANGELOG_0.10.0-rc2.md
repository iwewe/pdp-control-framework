# 0.10.0-rc2 - Release-readiness pass

## Completed

### Authoritative legal-source review

Articles 20-56 were re-reviewed against the official UU No. 27 Tahun 2022 PDF.

Legal Requirement entries changed from **46** to **64**.

Material corrections include Article 35 letter-based citation, missing consent/access/restriction requirements, Article 39(2), Article 48 detail, Article 52 exact cross-reference, Article 54(2), and the binding Constitutional Court interpretation of Article 53.

### Static dashboard/import package

Added:

- importable index-pattern/dashboard-shell NDJSON,
- real dashboard/indexer validation runner,
- machine-readable dashboard validation status.

### Real Wazuh gate

Added a version-pinned Wazuh 4.14.7 runtime validation runner.

## Still open for 1.0

- external/independent legal review if required by project governance,
- actual Wazuh 4.14.7 runtime execution,
- actual Wazuh Indexer/Dashboard import execution,
- export/import validation of the completed eight-panel dashboard.

## Current coverage

- Legal requirements: **64**
- With Wazuh technical-test coverage: **24**
- Generic-requirement-only: **8**
- No technical coverage: **32**

These are engineering coverage figures, not legal compliance percentages.

## 2026-09-22 hardening pass (still 0.10.0-rc2)

Findings from a repository review (see `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`
and `pdp-check.txt`) were addressed without cutting a new version:

- **Fixed:** pgAudit decoder (`implementations/wazuh/decoders/pdp_pgaudit.xml`)
  was anchored to match only at the start of the raw log line, which would
  never match a real PostgreSQL log line carrying `log_line_prefix`. The
  decoder now matches `AUDIT:` anywhere in the line; fixtures were rewritten
  with a realistic prefix; `validate_fixtures.py` updated to match
  non-anchored. Still requires real-lab confirmation before promotion past
  `STATIC_VALIDATED`.
- **Fixed:** `implementations/wazuh/tests/harness/run_api_logtest.py`
  referenced a nonexistent path for `WAZUH_EVIDENCE_MAPPING.yml`
  (`assessment/...` instead of `tools/assessment/...`).
- **Fixed:** version-label drift — `reports/COVERAGE_REPORT.{md,json}`,
  `release/compatibility/COMPATIBILITY_MATRIX.yml`, and
  `release/RELEASE_GATES.yml` still said `0.10.0-rc1`. Coverage report
  generation now reads `VERSION` instead of a hardcoded string.
- **Added:** `tools/validation/validate_release_consistency.py` and a new CI
  step, enforcing version agreement across `VERSION`,
  `FRAMEWORK_MANIFEST.yml`, `RELEASE_GATES.yml`, `COMPATIBILITY_MATRIX.yml`,
  `COVERAGE_REPORT.json`, and the version-specific release-readiness file;
  manifest count consistency; duplicate-ID detection for `LR-*`/`PDP-*`/
  `REQ-*`/test IDs; and broken cross-reference detection.
- **Added:** a CI step that regenerates the coverage report and fails on
  drift (`git diff --exit-code reports/`).
- **Rewritten:** `README.md` to a current-state entrypoint; the v0.1-v0.9
  version narrative moved to `docs/history/framework-v0.1-v0.9-narrative.md`.
- **Corrected:** stale `Draft v0.1`/`Draft v0.2`/`Draft v0.3`/`Draft v0.4`
  status headers in `PDP_CONTROL_FRAMEWORK.md`, `implementations/wazuh/README.md`,
  and five `framework/models/*.md` / `docs/architecture/*.md` files.
- **Added:** `LICENSE` (Apache License 2.0), `.env.example`, and
  `implementations/wazuh/DEPLOYMENT.md` (credential provisioning,
  agent-group rollout, SCA ID-collision note).
- **Synchronized:** `release/PRE_1_0_CHECKLIST.md` against actual verified
  state instead of leaving every item unchecked.
- **Regenerated:** `release/SHA256SUMS.txt` via the new
  `release/generate_sha256sums.sh`, documented as a release/tag-time
  artifact rather than a continuously current-tree checksum.

## 2026-09-23 real Wazuh lab validation (still 0.10.0-rc2)

A real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit 17.1 lab (Ubuntu 24.04.4
LTS) was stood up and used to validate the rule/decoder work above against
actual runtime behavior, not just static checks:

- **Confirmed:** the 2026-09-22 pgAudit decoder fix works against a real
  PostgreSQL log pipeline — all 5 non-correlation PostgreSQL fixtures and
  the 20-event correlation fixture matched their expected rule IDs. See
  `release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`.
- **Added and confirmed:** two new fixtures for `pdp_privileged_access.xml`
  (`110101`/`110102`), both matching as expected, including the
  correlation case.
- **Found and fixed (`pdp_fim.xml`):**
  - `110201` used `if_group syscheck`, which the built-in rule `515` also
    applies to rootcheck/OpenSCAP/CIS-CAT/Azure-logs scan start/end
    housekeeping messages — a real false-positive source. Fixed to
    `if_group syscheck_file` (only genuine per-file add/modify/delete
    events).
  - `110202` checked a nonexistent `type` field and never fired. Fixed to
    `decoded_as syscheck_deleted`, matching how the built-in rule `553`
    itself identifies deletions.
  - Confirmed via a live create/modify/delete test (FIM cannot be fixtured
    through `wazuh-logtest` the way text-log rules can). See
    `release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md`.
- **Confirmed (non-blocking finding):** `110101`'s "sudo" regex keyword is
  unreachable with Wazuh's default ruleset — sudo command-execution events
  never carry the `authentication_success` group the rule requires; only
  PAM session-open events (`su`, `sshd` login, etc.) do.

Still open: telemetry-health fixtures, SCA policy execution, centralized
`agent.conf` distribution (no agent enrolled yet), and Indexer/Dashboard
import.

## 2026-09-23 (same day) — SCA policy validation

- **Confirmed:** `implementations/wazuh/sca/pdp_linux_baseline.yml` (checks
  `910001`-`910006`) executes correctly on real Wazuh 4.14.7 + Ubuntu
  24.04.4. The manager's local `<sca>` config had no `<policies>` entry
  for it (only the vendor `cis_ubuntu24-04.yml` was running), so one was
  added. All 6 checks produced a result, no ID collision with the vendor
  policy, and every result was independently reproduced with direct shell
  commands (`sshd -T`, `systemctl is-enabled ...`). No policy defects
  found. See `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`.

Still open: telemetry-health fixtures, centralized `agent.conf`
distribution to a separately enrolled agent, and Indexer/Dashboard import.

## 2026-09-23 (same day) — separate-agent enrollment and agent.conf distribution

A genuinely separate Wazuh 4.14.7 agent was enrolled (a Docker container
running `wazuh-agent`, not the manager's own local agent `000` used in
every prior test) to validate centralized configuration distribution:

- **Fixed:** `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
  contained a `<syscollector>` block. Wazuh 4.14.7 rejects `<syscollector>`
  inside a centralized/shared `agent.conf`, and critically, that single
  invalid element invalidated the *entire* file — `<labels>`,
  `<syscheck>`, and `<sca>` in the same file all silently stopped applying
  too. Removed the block (syscollector must be configured locally per
  agent instead).
- **Confirmed working after the fix:** both `pdp-linux-baseline/agent.conf`
  and `pdp-database/agent.conf` distribute cleanly via agent groups, with
  `syscheck` correctly monitoring the labeled directories on the agent.
- **Found, unresolved:** `pdp_linux_baseline.yml` produces zero usable
  results when distributed via a centralized agent group — every check
  uses a `c:<command>` rule, and Wazuh disables remote command execution
  by default (`sca.remote_commands=0`) for centrally-pushed SCA policies.
  Setting `sca.remote_commands=1` on both the agent and the manager (with
  full daemon restarts, verified via fresh non-zombie processes) did not
  resolve it, confirmed against the manager's authoritative `sca_check`
  database table across 4 restart cycles. `implementations/wazuh/DEPLOYMENT.md`
  now documents this and recommends local policy deployment instead until
  resolved.

Full evidence: `release/runtime-validation/wazuh-4.14.7/AGENT_CONF_EVIDENCE_2026-09-23.md`.

Still open: telemetry-health fixtures, the `sca.remote_commands` issue
above, and Wazuh Indexer/Dashboard import.

## 2026-09-23 (same day) — real Wazuh Indexer/Dashboard import

The final untested phase: real import against Wazuh Indexer 4.14.7 and
Wazuh Dashboard 4.14.7 on the same lab host.

- **Fixed:** all three OpenSearch index templates
  (`implementations/wazuh/indexer/templates/pdp-*-template.json`) were
  missing schema-required fields. Indexing the unmodified, CI-validated
  `examples/evidence.example.json` failed under `dynamic: strict` because
  `observed_at` — a **required** field in
  `framework/schemas/evidence.schema.json` — was never mapped. A full
  schema-vs-mapping diff found `pdp-evidence-template.json` was also
  missing `collected_at`, `event.raw_reference`, `review.reviewer`,
  `review.notes`, and the entire `payload` object; `pdp-assessment-` and
  `pdp-findings-template.json` were each missing `notes`. This meant *no*
  genuinely schema-valid document from any of the three layers could ever
  be indexed, despite CI's JSON Schema validation passing throughout.
  Fixed by adding the missing fields (`payload` mapped as
  `{"type":"object","enabled":false}`, since its schema intentionally
  allows arbitrary sub-fields per evidence-producing engine).
- **Fixed:** `release/runtime-validation/dashboard/validate_real_import.py`
  unconditionally sent a `securitytenant: global` header, which fails
  every dashboard request — even as the `admin`/`all_access` superuser —
  when `opensearch_security.multitenancy.enabled: false` (Wazuh's own
  default). Added `PDP_MULTITENANCY_ENABLED` (default `false`) to only
  send that header when actually needed.
- **Added:** `examples/control-assessment.example.json` plus a CI
  validation step, closing a previously-open gap (no example exercised
  `control-assessment.schema.json`).
- **Confirmed:** after both fixes, the full import script reports
  `"overall": "PASS"`; real evidence/assessment/finding example documents
  were indexed directly; `dynamic: strict` still correctly rejects a
  genuinely unknown field.

Full evidence: `release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`.

This closes every phase originally listed as open in
`reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` except: telemetry-health
fixtures, the unresolved `sca.remote_commands` centralized-SCA blocker,
the complete eight-panel dashboard (only the empty shell was imported),
and a dashboard role-based access control model.

## 2026-09-23 (same day) — dashboard saved objects found not to survive a restart

After the above was confirmed working, the imported dashboard/index
patterns were found completely gone shortly after a `wazuh-dashboard`
service restart that followed a `wazuh-dashboard` package upgrade
(`4.14.5-1 -> 4.14.7-1`) earlier the same day. The `.kibana_1` index
itself was not recreated (same UUID before/after) — a saved-objects-level
loss, not an index rebuild, most likely tied to how OpenSearch
Dashboards' migration step handles objects stamped with an older app
version's `migrationVersion`.

- **Confirmed as an operational risk, not a repository defect:**
  re-running `validate_real_import.py` restored everything immediately
  and cleanly.
- **Added:** `implementations/wazuh/DEPLOYMENT.md` section 4 —
  back up dashboard saved objects before any restart/upgrade, and how to
  verify/reimport afterward.
- **Left in place (intentionally, for verification):** the 3 example
  documents (evidence, finding, assessment) re-indexed into
  `pdp-evidence-000001`, `pdp-findings-000001`, `pdp-assessment-000001`
  so the dashboard/index patterns have visible sample data.

Full evidence: `release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`
(Finding 3).

## 2026-09-23 (same day) — full eight-panel dashboard built and imported

- **Added:** `implementations/wazuh/dashboard/generate_dashboard_ndjson.py`
  — a committed, spec-driven generator (not a one-off script) that reads
  `implementations/wazuh/dashboard/DASHBOARD_SPEC.yml` and produces
  `implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson`:
  3 index patterns, 8 classic OpenSearch Dashboards visualizations (one
  per `PDP-DASH-00N` panel — `histogram`/`pie`/`table`/`line` depending on
  the panel's `type`), and a dashboard wiring them into a 2-column,
  4-row grid.
- **Confirmed on real Wazuh 4.14.7 Dashboard:** import reports
  `successCount: 12`; the live dashboard object's 8 panels all resolve to
  their visualization via `references`; every panel's underlying
  aggregation was run directly against the real
  `pdp-evidence-*`/`pdp-assessment-*`/`pdp-findings-*` indices and none
  errored. Full evidence:
  `release/runtime-validation/dashboard/DASHBOARD_PANELS_EVIDENCE_2026-09-23.md`.
- **Added CI enforcement:** a new workflow step regenerates the NDJSON
  from the spec on every push and fails if it has drifted, plus a
  reference-integrity check (every `panelRefName` and saved-object
  `references` entry must resolve).
- Note: rendering was verified via the saved-objects/search APIs, not an
  actual browser session; the persistence risk documented in the prior
  entry (Finding 3) applies equally to this fuller dashboard — back it up
  before any `wazuh-dashboard` restart/upgrade.

This closes the last item from
`reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md`'s original priority list
except the unresolved `sca.remote_commands` centralized-SCA blocker and a
dashboard role-based access control model.

## 2026-09-23 (same day) — telemetry-health fixtures

- **Added:** 4 fixtures under
  `implementations/wazuh/tests/fixtures/telemetry_health/`, one per
  regex alternative in rule `110301`
  (`agent...disconnected`/`agent...inactive`/`collector...stopped`/
  `logging...stopped`). Confirmed via real `wazuh-logtest`.
- **Confirmed there is no naturally-occurring Wazuh-internal event for
  this rule** — agent connectivity is tracked internally in `wazuh-db`,
  not emitted as a decodable log line — so the fixtures are necessarily
  synthetic (this rule is a generic safety net for third-party collector
  logs, not a specific Wazuh event).
- **Found (not a bug):** the rule has no `if_group`/`if_sid`/`decoded_as`
  scoping. A first test attempt using an `audit:` syslog program tag was
  claimed instead by an unrelated built-in rule (`6100`, Solaris BSM,
  level 0) before `110301` was ever attempted. Documented as a real
  deployment consideration for anyone wiring third-party collector logs
  into this rule.

Full evidence: `release/runtime-validation/wazuh-4.14.7/TELEMETRY_HEALTH_EVIDENCE_2026-09-23.md`.

## 2026-09-23 (same day) — Wazuh Server API harness

First real run of `implementations/wazuh/tests/harness/run_api_logtest.py`
(every prior phase used the `wazuh-logtest` CLI directly instead), using
the `api_username: wazuh` credential from `wazuh-install-files.tar`.

- **Fixed:** the harness passed the Wazuh API's `decoder` response
  (an object, `{"name": "pdp-pgaudit", ...}`) straight into evidence
  `test.decoder`, which `framework/schemas/evidence.schema.json` requires
  to be a string or `null`. All 13 `HARNESS.yml` cases already reported
  `PASS` for rule matching, but every generated evidence document failed
  schema validation until this was fixed
  (`(output.get("decoder") or {}).get("name")`).
- **Fixed (latent, unrelated):**
  `tools/assessment/WAZUH_EVIDENCE_MAPPING.yml`'s `WZ-RUL-PG-005` entry
  had a legal-disclaimer sentence in `technical_priority` instead of a
  priority level. Not consumed by any script yet, so not previously
  active, but a real data-quality defect.
- **Confirmed:** after both fixes, all 13 cases PASS and all 13 generated
  evidence documents validate individually against
  `evidence.schema.json`.

Full evidence: `release/runtime-validation/wazuh-4.14.7/API_HARNESS_EVIDENCE_2026-09-23.md`.

This closes the API-harness item from `release/PRE_1_0_CHECKLIST.md`
section E.

## 2026-09-23 (same day) — assessment/findings/registry tooling validated, section E complete

Ran `tools/assessment/assess_controls.py`, `tools/findings/generate_findings.py`,
and `tools/evidence/register_evidence.py` for the first time against 8
hand-built, schema-valid synthetic evidence documents covering every
precedence branch (`PASS`, `FAIL`, `ERROR`, `REVIEW`, and — the critical
case — a `PASS` result with `source.collector_health: DEGRADED`).

- **Confirmed:** the collector-health case correctly produces `REVIEW`,
  never a silent `PASS` — closing "Collector failure produces
  `ERROR/REVIEW`, never silent `PASS`" and "Assessment aggregator tested
  against PASS/FAIL/ERROR/REVIEW cases".
- **Confirmed:** the finding generator created exactly one finding, only
  for the `FAIL` control, closing "Finding generator tested".
- **Confirmed:** all 5 assessments, the 1 finding, and all 8 registry
  entries validated against their respective schemas, closing "Evidence
  Registry Schema validated".
- **No bugs found** in any of the three tools.
- **Added:** `docs/architecture/retest-workflow.md` — the operational
  retest procedure was previously only a diagram label; now documented,
  grounded in the verified tool behavior, including the explicit design
  decision that findings are never auto-closed even on a later `PASS`.

Full evidence: `reports/TOOLS_PIPELINE_VALIDATION_2026-09-23.md`.

This completes every item in `release/PRE_1_0_CHECKLIST.md` section E
(Evidence / assessment).

## 2026-09-23 (same day) — legal/control/model review, sections A/B/C complete

A documentation and consistency review (no Wazuh lab required) covering
the remaining items in `release/PRE_1_0_CHECKLIST.md` sections A
(Legal layer), B (Control architecture), and C (Processing /
applicability).

- **Fixed:** `framework/schemas/control-assessment.schema.json` did not
  enforce `docs/architecture/assessment-methodology.md`'s documented rule
  that `NOT_APPLICABLE` requires a justification — `notes: null` was
  previously accepted. Added a conditional schema rule requiring a
  non-empty `notes` when `result` is `NOT_APPLICABLE`.
- **Fixed:** `examples/processing-activity.example.yml` was missing 2 of
  `framework/models/PROCESSING_ACTIVITY_MODEL.md`'s own "Minimum Required
  Fields" (`processing_operations`, `retention`).
- **Fixed:** `examples/profile-application.example.yml`'s
  `effective_requirements` did not match the mathematically correct union
  of its applied profiles' `required_requirements` (5 requirements were
  missing). Rewrote it with 3 distinct, programmatically-verified-correct
  scenarios, the third of which also serves as the "security monitoring
  platform dogfooding example" (the Wazuh manager/indexer/dashboard
  itself modeled as an in-scope asset).
- **Added:** explicit interpretation disclaimers to
  `framework/legal/LEGAL_MAPPING.yml` (`requirement_summary_disclaimer`)
  and `framework/controls/CONTROL_CATALOGUE.yml`
  (`objective_disclaimer`), and an explicit open item in
  `framework/legal/review/LEGAL_REVIEW_STATUS.yml` tracking that
  UU 27/2022 implementing regulations have not been confirmed/reviewed
  (documented as open, not assumed resolved).
- **Reviewed, no changes needed:** control-text overclaiming (none
  found), assessment method/result semantic consistency across all
  layers, the Asset model, and the High-Risk Processing profile.
- **Also fixed:** 12 framework/implementation `.yml` files carried stale
  `version: 0.X.0-draft` markers from when they were first introduced,
  the same class of drift already fixed in `.md` files during the
  2026-09-22 hardening pass. Bumped to `0.10.0-rc2`, preserving the
  original marker as `introduced_in_draft`.

Full evidence: `reports/MODEL_REVIEW_2026-09-23.md`. This completes every
item in sections A, B, and C except `external_legal_counsel_review`
(governance decision, out of engineering scope) and the implementing-
regulations gap (explicitly tracked as open, not resolved).

## 2026-09-24 — dashboard RBAC live test (found and safely rolled back one gap)

Live-tested `implementations/wazuh/dashboard/rbac/` (designed 2026-09-23,
not yet applied live) against the real Wazuh Indexer/Dashboard lab:

- Backed up the three live security config files, appended the
  `pdp_dashboard_viewer`/`pdp_dashboard_editor` roles, created two test
  users, and reloaded via `securityadmin.sh` (`Done with success`).
- **`pdp_dashboard_viewer` confirmed correct:** all 3 index-level tests
  (read `pdp-*` allowed, write `pdp-*` denied, write `.kibana` denied)
  passed exactly as designed.
- **`pdp_dashboard_editor` found not to work:** its `crud` grant on
  `.kibana`/`.kibana_1` does not grant working access to the Dashboards
  saved-objects application layer — neither read nor write succeeded via
  the real `/api/saved_objects/...` path (port 443), even though the raw
  index-level permission was confirmed present (a write to the concrete
  `.kibana_1` index succeeded when targeted directly at port 9200). Ruled
  out glob-pattern mistakes and hardcoded system-index protection as
  causes. A diagnostic attempt to temporarily widen the role to isolate
  the exact missing permission was correctly blocked before reaching the
  server by the session's own safety guardrail (too broad a grant for a
  live security role) — the gap was documented instead of chased further
  via broader live permission grants.
- **Rolled back cleanly:** restored all three security config files from
  backup, reloaded, and verified zero references to any PDP RBAC
  role/user remain live; deleted the temporary test index and local
  password files.

Full evidence: `release/runtime-validation/dashboard/RBAC_EVIDENCE_2026-09-24.md`.
`implementations/wazuh/dashboard/rbac/roles.yml`/`README.md` updated with
the finding. **Do not re-apply this RBAC config to a live environment
until the editor gap is resolved and retested.**

This was the last open item from `release/PRE_1_0_CHECKLIST.md` section F;
it remains partially open (viewer done, editor not).
