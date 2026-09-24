# Wazuh Implementation Gap Analysis

**Framework version reviewed:** 1.0.0 (originally reviewed at 0.10.0-rc2)
**Review date:** 2026-09-22 (original), updated 2026-09-23 and 2026-09-24
with real lab evidence
**Scope:** `implementations/wazuh/` content (rules, decoders, SCA policy, agent
configuration, PostgreSQL audit profile, indexer/dashboard artifacts) and the
associated release-readiness status files.

> This report is an engineering gap analysis for real-world Wazuh deployment.
> It is not a legal compliance assessment and does not replace the project's
> own release gates in `release/RELEASE_GATES.yml` and
> `release/PRE_1_0_CHECKLIST.md`.

## Summary

**Update 2026-09-23/24:** a real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit
17.1 lab (Ubuntu 24.04.4 LTS) is now up, and every phase from the original
gap list — authentication, PostgreSQL, privileged access, FIM, SCA (both
local and centralized agent-group deployment), telemetry-health, the API
harness, the assessment/findings/registry tooling pipeline, real Wazuh
Indexer/Dashboard import including the complete eight-panel dashboard, and
dashboard RBAC — has now been exercised against it. See Sections 2-6 below
and `release/runtime-validation/`. This found and fixed real defects that
static validation and CI schema validation could not catch: the pgAudit
decoder; two FIM rule bugs; an invalid `<syscollector>` element that
silently broke an entire `agent.conf`; six schema-required fields missing
across all three OpenSearch index templates (meaning no genuinely valid
evidence/assessment/finding document could ever be indexed); a
`securitytenant` header bug in the dashboard-import script; a decoder-field
bug and a data-quality bug in the API harness path; a missing
`NOT_APPLICABLE`-requires-justification enforcement; and a control-profile
composition example that didn't match its own model's math — plus one
non-blocking design limitation in the privileged-access rule and a rule-
precedence limitation in the telemetry-health rule. What was initially
recorded as an unresolved SCA-via-agent-group blocker turned out to be a
lab-environment gap (missing `sshd`/`systemctl` in a minimal test
container), not a real defect — see Section 4.

**Every finding from this pass is now resolved.** The dashboard RBAC
"editor" role initially could not access dashboard saved objects at all
(Section 6); after two design iterations and a log-based root-cause
diagnosis (missing `tenant_permissions` for the `global_tenant` tenant —
required by OpenSearch Security's Kibana-multitenancy interceptor
regardless of the Dashboards-side `multitenancy.enabled` flag), both the
"viewer" and "editor" roles are now confirmed working end to end against
the real lab.

The Wazuh implementation profile is architecturally complete (rules, SCA
checks, decoders, agent configuration, index templates, dashboard shell all
exist and are internally consistent and traceable to controls/requirements).
Static validation (YAML/XML/JSON well-formedness, ID uniqueness, schema
conformance) passes in CI. The remainder of this document was originally
written when no real-runtime evidence existed at all; it is kept largely
as-is for historical record, with resolution notes added inline.

## 1. Gaps already acknowledged by the project

These are documented in the project's own status files and are restated here
for completeness:

| Area | File | Status |
|---|---|---|
| Wazuh 4.14.7 manager/agent runtime | `release/runtime-validation/wazuh-4.14.7/STATUS.yml` | `BLOCKED_NO_WAZUH_RUNTIME_IN_CURRENT_ENVIRONMENT` |
| Wazuh Indexer/Dashboard import | `release/runtime-validation/dashboard/STATUS.yml` | `BLOCKED_NO_WAZUH_INDEXER_DASHBOARD_RUNTIME_IN_CURRENT_ENVIRONMENT` |
| Compatibility matrix | `release/compatibility/COMPATIBILITY_MATRIX.yml` | `TARGET_MATRIX_NOT_FULLY_LAB_VALIDATED` |
| Pre-1.0 checklist sections D (Wazuh implementation) and F (Indexer/dashboard) | `release/PRE_1_0_CHECKLIST.md` | All items unchecked |

Required before promotion to `LAB_VALIDATED` (per
`release/runtime-validation/wazuh-4.14.7/STATUS.yml`):
manager reports v4.14.7, custom decoder loads, custom rules load, fixture
logtest matches expected rules, correlation fixtures pass in the same
session, `agent.conf` validation passes, SCA policy executes on an Ubuntu
24.04 test agent.

## 2. pgAudit decoder mismatch — FIXED and lab-confirmed (2026-09-23)

**Original severity: high — blocked the entire PostgreSQL audit pipeline as configured.**

**Status: RESOLVED.** The decoder was fixed on 2026-09-22 (Option 2 below)
and confirmed against a real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit 17.1
lab on 2026-09-23: all 5 non-correlation PostgreSQL fixtures and the
20-event correlation fixture matched their expected rule IDs exactly. See
`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`
for the full evidence and `release/runtime-validation/wazuh-4.14.7/STATUS.yml`
for current promotion status. The description below is kept as-is for
historical/diagnostic record of the original defect.

- `implementations/wazuh/postgresql/postgresql-pdp.conf.example` sets:
  ```
  log_destination = 'stderr'
  log_line_prefix = '%m [%p] %u@%d %r '
  ```
  A real PostgreSQL log line under this configuration looks like:
  ```
  2026-09-22 10:00:00.123 UTC [12345] postgres@mydb 10.0.0.1 LOG:  AUDIT: SESSION,4,1,READ,SELECT,TABLE,public.employee,<statement suppressed>,<not logged>,100
  ```
- `implementations/wazuh/decoders/pdp_pgaudit.xml` uses an **anchored**
  prematch: `<prematch type="pcre2">^AUDIT:\s+</prematch>`. This requires the
  line handed to the decoder to *start* with `AUDIT:`.
- `implementations/wazuh/shared/pdp-database/agent.conf` collects this file
  with `<log_format>syslog</log_format>`, but the file is not actual syslog
  output (no `<PRI>`, hostname, or program tag) — it is PostgreSQL's own
  `stderr` log format with `log_line_prefix`. Wazuh's syslog pre-decoder has
  no defined prefix to strip here, so the timestamp/pid/user prefix is
  expected to remain in `full_log`.
- The test fixtures in `implementations/wazuh/tests/fixtures/postgresql/*.log`
  are hand-written **without** the `log_line_prefix` (they start directly
  with `AUDIT: SESSION,...`), and
  `implementations/wazuh/tests/scripts/validate_fixtures.py` only matches a
  Python `re` pattern against these pre-stripped fixtures. This validates the
  parsing *contract*, not the actual decoder behavior against a realistic raw
  log line, so CI green does not indicate the decoder will work.

**Predicted result (before the fix):** the `pdp-pgaudit` decoder would fail
to match any real log line, so rules `110401`–`110406` (all PostgreSQL
audit/DDL/role/read-anomaly detections, supporting LR-031/LR-035/LR-047/
LR-052 per `framework/legal/LEGAL_MAPPING.yml`) would never fire. This was
confirmed *not* to happen after the fix — see the lab evidence linked above.

**Fix applied:** Option 2 below — the decoder's prematch/regex were changed
to search for `AUDIT:` anywhere in the line rather than anchoring at the
start, and fixtures were rewritten with a realistic `log_line_prefix`.

1. (not chosen) Change `postgresql-pdp.conf.example` to route through real
   syslog (`log_destination = 'syslog'`) so Wazuh's syslog parser strips the
   envelope before the decoder runs, or
2. **(chosen, lab-confirmed)** Rewrite `pdp-pgaudit`'s prematch/regex to
   tolerate the configured `log_line_prefix` (match `AUDIT:` anywhere in the
   line rather than anchored at the start), and update the fixtures to
   include a realistic prefix so `validate_fixtures.py` actually exercises
   this path.

## 3. FIM rule bugs found and fixed on real Wazuh (2026-09-23)

**Status: RESOLVED.** Live create/modify/delete testing against a real
Wazuh 4.14.7 manager (see
`release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md`)
found and fixed two real defects in `implementations/wazuh/rules/pdp_fim.xml`:

- **`110201` false-positived on scan housekeeping messages.** It used
  `<if_group>syscheck</if_group>`, but Wazuh's built-in rule `515`
  ("Ignoring scan messages", level 0) tags rootcheck/OpenSCAP/CIS-CAT/
  Azure-logs scan start/end messages with the `syscheck` group too (so they
  can be suppressed) — our rule re-alerted every one of them at level 7 with
  an empty file path. **Fixed** by anchoring on `<if_group>syscheck_file</if_group>`
  instead, which only the three real per-file event rules (`550`/`553`/`554`)
  carry.
- **`110202` never fired.** It checked `<field name="type">deleted</field>`,
  but the decoded alert has no `type` field at all — the real value is
  `syscheck.event` in the JSON output, and even the dotted-path field
  reference did not match in practice. **Fixed** by switching to
  `<decoded_as>syscheck_deleted</decoded_as>`, mirroring exactly how the
  built-in rule `553` itself identifies deletions.

A secondary, non-blocking finding was also confirmed for
`pdp_privileged_access.xml`: rule `110101`'s "sudo" regex keyword is
unreachable with Wazuh's default ruleset, because `sudo` command-execution
events never carry the `authentication_success` group the rule requires.
Only PAM session-open events (`su`, `sshd` login, etc.) reach it. See
`release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`
for the corresponding fixtures and result.

## 4. Agent-group deployment bugs (2026-09-23) — both resolved

A separate Wazuh 4.14.7 agent (Docker container, not the manager's own
local agent `000` used in Sections 2-3) was enrolled to test centralized
`agent.conf` distribution. Full evidence:
`release/runtime-validation/wazuh-4.14.7/AGENT_CONF_EVIDENCE_2026-09-23.md`.

**Fixed:** `implementations/wazuh/shared/pdp-linux-baseline/agent.conf`
contained a `<syscollector>` block. Wazuh 4.14.7 rejects `<syscollector>`
inside a centralized/shared `agent.conf`, and — critically — that single
invalid element invalidated the **entire** file: `<labels>`, `<syscheck>`,
and `<sca>` in the same file all silently stopped applying too, not just
syscollector. Removed the block; syscollector runs from each agent's local
default configuration regardless.

**Resolved (was misdiagnosed as `sca.remote_commands`, see
`SCA_EVIDENCE_2026-09-23.md` addendum):** once the above was fixed,
`implementations/wazuh/sca/pdp_linux_baseline.yml` loaded correctly via
the group but initially produced **zero usable results** — all 6 checks
evaluated to `not applicable`, with the SCA module logging
`sca.remote_commands` as disabled. `sca.remote_commands=1` was set and
this conclusion held across 4 restart cycles, checked against the
authoritative `sca_check` table — so the item was recorded as an
unresolved blocker. In a later pass on the same day, the "disabled"
message stopped appearing after re-testing on a freshly re-enrolled
agent, replaced by a different error: `"Invalid path or wrong permissions
to run command '<cmd>'"`. Direct inspection found the real cause: the
test agent (a minimal Docker container with no init system) never had
`sshd` or `systemctl` installed at all. Wazuh's own vendor
`cis_ubuntu24-04.yml` policy, already loaded on the same agent, failed
identically on the same commands, confirming this was a lab-environment
gap, not a defect in `sca.remote_commands` handling or in the PDP policy.
After installing `openssh-server` (which transitively provided
`systemctl`), all 6 checks returned genuine PASS/FAIL results via the
centralized group-pushed policy.

**Practical effect:** `pdp_linux_baseline.yml` works via centralized
agent-group distribution once `sca.remote_commands=1` is set on the
receiving agent and the checked commands actually exist on that host — no
policy redesign to file-based (`f:`) checks is needed.
`implementations/wazuh/DEPLOYMENT.md` reflects this corrected conclusion.

## 5. Indexer/Dashboard import bugs found and fixed (2026-09-23)

Full evidence:
`release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`.
Real Wazuh Indexer 4.14.7 + Wazuh Dashboard 4.14.7 on the same lab host.

**Fixed — three index templates were missing schema-required fields.**
Indexing the unmodified, CI-schema-valid `examples/evidence.example.json`
into `pdp-evidence-*` failed with
`strict_dynamic_mapping_exception: ... dynamic introduction of
[observed_at] ... is not allowed` — `observed_at` is a **required** field
in `framework/schemas/evidence.schema.json`, yet the OpenSearch mapping
never defined it. A systematic schema-vs-mapping diff found the same
pattern across all three templates: `pdp-evidence-template.json` was
missing `observed_at`, `collected_at`, `event.raw_reference`,
`review.reviewer`, `review.notes`, and the entire `payload` object;
`pdp-assessment-template.json` and `pdp-findings-template.json` were each
missing `notes`. Under `dynamic: strict`, this meant **no genuinely
schema-valid document from any of the three layers could ever be indexed**
before this fix, despite CI's JSON Schema validation passing the whole
time — the schema and the index mapping had silently drifted apart.
**Fixed** by adding the missing fields, and mapping `payload` as
`{"type":"object","enabled":false}` (stored, not indexed) since its schema
intentionally allows arbitrary sub-fields per evidence-producing engine.

**Fixed — the dashboard-import script sent an inappropriate tenant header.**
`release/runtime-validation/dashboard/validate_real_import.py` always sent
`securitytenant: global`, which fails every request — even as the
`admin`/`all_access` superuser — for the very common case where
`opensearch_security.multitenancy.enabled: false` (Wazuh's own default).
**Fixed** by adding `PDP_MULTITENANCY_ENABLED` (default `false`) to only
send that header when the target actually has multitenancy enabled.

After both fixes, the full script reports `"overall": "PASS"`, and real
schema-conformant documents (evidence, finding, and a newly added
`examples/control-assessment.example.json`) were indexed directly to prove
the mapping accepts real content, not just empty validation indices.
`dynamic: strict` was re-confirmed to still reject a genuinely unknown
field after the fix.

**Operational risk found (not a repository defect, no fix possible from
this side):** the imported dashboard/index-pattern objects were confirmed
present at 17:12 WIB, then found completely gone (`dashboard` count 0, no
`pdp-*` index patterns) after a `wazuh-dashboard` service restart at 17:38
WIB — following a `wazuh-dashboard` package upgrade (`4.14.5-1 ->
4.14.7-1`) earlier the same day. The `.kibana_1` index itself was not
recreated (same UUID before/after), so this was a saved-objects-level
loss, most likely tied to how OpenSearch Dashboards' migration step
(which runs on every process start) handles objects stamped with an older
app version's `migrationVersion`. Re-importing the same NDJSON restored
everything cleanly, twice. **Conclusion: custom Wazuh Dashboard saved
objects are not guaranteed to survive a dashboard restart/upgrade in this
environment** — anyone deploying the PDP dashboard shell (or building the
full eight-panel dashboard on top of it) needs a backup/reimport step as
part of routine Wazuh maintenance. See
`implementations/wazuh/DEPLOYMENT.md` section 4 for the guidance added as
a result.

## 6. Dashboard RBAC — resolved after three iterations (2026-09-24)

Full evidence: `release/runtime-validation/dashboard/RBAC_EVIDENCE_2026-09-24.md`.

The two-role model in `implementations/wazuh/dashboard/rbac/` (designed
2026-09-23) was live-tested against the real indexer/dashboard. Three
iterations were needed:

- **v1:** `pdp_dashboard_viewer` (read-only on `pdp-*` data) confirmed
  correct (3/3 index-level tests passed), but `pdp_dashboard_editor`
  could not read or write dashboard saved objects via the real
  `/api/saved_objects/...` path at all, despite a raw index-level `crud`
  grant on `.kibana`/`.kibana_1` (confirmed present via a successful
  direct write to the concrete index outside the Dashboards API). Ruled
  out glob-pattern mistakes and hardcoded system-index protection.
- **v2 (research, no server changes):** compared against OpenSearch
  Security's own reference `kibana_user` role
  (github.com/opensearch-project/security), which uses the write-capable
  `cluster_composite_ops` (not the `_ro` variant this design used) and
  `["delete","index","manage","read","indices_all"]` on `.kibana*`. Fixed
  both, narrower than the reference role's `indices_all`, plus a
  previously-unnoticed gap: the viewer had no `.kibana*` grant at all.
  **Deployed live and retested — still failed**, including now *read*
  access for both roles, not just write.
- **v3 (root cause found and fixed):** raised the OpenSearch Security
  plugin's own log level to `DEBUG` (a logging-verbosity change via
  `PUT _cluster/settings`, reverted immediately after diagnosis — not a
  permission change) and replayed the failing request. The log showed
  the actual cause directly: `WARN PrivilegesInterceptorImpl: Tenant
  global_tenant is not allowed for user <user>`. OpenSearch Security's
  Kibana-multitenancy interceptor intercepts *every* request touching a
  `.kibana*`-pattern index regardless of `opensearch_dashboards.yml`'s
  `multitenancy.enabled` flag (that flag only controls the Dashboards
  UI's tenant switcher). Neither v1 nor v2 declared any
  `tenant_permissions`; reserved/static roles like `kibana_user`
  apparently get the `global_tenant` implicitly, but a custom role must
  declare it explicitly. Added `tenant_permissions` (`kibana_all_read`
  for the viewer, `kibana_all_write` for the editor) to both roles.

**Result: all 8 test scenarios passed** (index-level read/write on
`pdp-*` for both roles, plus dashboard-open and save-a-visualization
checks via the real Dashboards API). A diagnostic attempt during the v1
investigation to temporarily widen a role to `"*"` to isolate the cause
was correctly blocked before reaching the server by the session's own
safety guardrail (too broad a grant for a live security role) — the fix
that actually worked came from log-based diagnosis instead, not broader
permission grants.

Test users, the test index, and the test visualization were deleted
after verification. The `pdp_dashboard_viewer`/`pdp_dashboard_editor`
roles and their backend-role mappings were deliberately left live as the
working, confirmed deliverable feature.

## 7. Other operational gaps for a real deployment

- ~~Credential provisioning is undocumented.~~ **RESOLVED** 2026-09-22:
  see `.env.example` and `implementations/wazuh/DEPLOYMENT.md` section 1.
- ~~`agent.conf` distribution is not documented.~~ **RESOLVED** 2026-09-22:
  see `implementations/wazuh/DEPLOYMENT.md` section 2.
- **SCA policy executed successfully, no collision observed (partially resolved 2026-09-23).**
  `implementations/wazuh/sca/pdp_linux_baseline.yml` (IDs `910001`-`910006`)
  ran alongside Wazuh's bundled `cis_ubuntu24-04.yml` policy on the real
  lab with no ID collision, and all 6 checks produced correct results
  (independently verified against actual system state) — see
  `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`.
  Still open: this has only been checked against one other policy (the
  vendor default); collision against other custom/third-party SCA content
  in a different target environment remains unverified.
- ~~No LICENSE file~~ **RESOLVED** 2026-09-22: `LICENSE` (Apache 2.0) added.
- **`release/PRE_1_0_CHECKLIST.md` sections E–G** (evidence/assessment,
  indexer/dashboard, CI/repository) remain mostly unchecked; section D
  (Wazuh implementation) is now partially checked based on real lab
  evidence from 2026-09-23 — see that file for current state. None of the
  remaining unchecked items should be assumed complete until verified.

## 8. Suggested priority order

1. ~~Stand up a Wazuh 4.14.7 + Wazuh Indexer/Dashboard + PostgreSQL 17 +
   pgAudit lab~~ **DONE 2026-09-23** (native install on Ubuntu 24.04.4 LTS,
   not Docker).
2. ~~Fix the pgAudit decoder/log-format mismatch described in Section 2~~
   **DONE 2026-09-22, lab-confirmed 2026-09-23.**
3. Run `wazuh-logtest` / the API `/logtest` harness against all rule
   groups. **Mostly done:** authentication (110001-110002), PostgreSQL
   (110401-110406), and privileged access (110101-110102) fixtures
   confirmed via `wazuh-logtest` CLI — see
   `release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`.
   FIM (110201-110202) confirmed via a live create/modify/delete test
   instead (fixtures don't apply to FIM — see
   `release/runtime-validation/wazuh-4.14.7/FIM_LIVE_EVIDENCE_2026-09-23.md`),
   which also found and fixed two real rule bugs (Section 3 above).
   ~~telemetry-health (110301) has no fixture yet~~ **DONE 2026-09-23** —
   see `release/runtime-validation/wazuh-4.14.7/TELEMETRY_HEALTH_EVIDENCE_2026-09-23.md`.
   All 4 regex alternatives confirmed via `wazuh-logtest`; found that the
   rule has no `if_group`/`if_sid` scoping, so it can be silently
   preempted by any other rule matching the same log line first (not a
   bug in the rule, but a real deployment consideration).
   ~~The API `/logtest` harness (`run_api_logtest.py`) itself has not
   been run yet~~ **DONE 2026-09-23** — see
   `release/runtime-validation/wazuh-4.14.7/API_HARNESS_EVIDENCE_2026-09-23.md`.
   All 13 `HARNESS.yml` cases PASS via the real API; found and fixed a
   bug where `test.decoder` was passed as an object instead of the
   string `evidence.schema.json` requires, then validated all 13
   generated evidence documents against the schema individually.
4. ~~Execute the SCA policy on a real Ubuntu 24.04 agent and confirm ID
   uniqueness and check results.~~ **DONE 2026-09-23** (local policy) — see
   `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`.
   All 6 checks ran correctly with no ID collision against the vendor
   policy. Also now tested against a genuinely separate enrolled agent
   (Section 4 above) — initially appeared not to work via centralized/
   group distribution, later found to be a lab-environment gap (missing
   `sshd`/`systemctl` on the minimal test container), not a real defect;
   resolved once those binaries were installed.
5. ~~Import the three index templates and the dashboard saved-objects
   NDJSON into a real Wazuh Indexer/Dashboard instance.~~ **DONE
   2026-09-23** — see
   `release/runtime-validation/dashboard/INDEXER_DASHBOARD_EVIDENCE_2026-09-23.md`.
   Found and fixed 6 missing schema-required fields across the three
   templates and a `securitytenant` header bug in the import script
   (Section 5 above).
6. ~~Update `release/runtime-validation/*/STATUS.yml`,
   `release/compatibility/COMPATIBILITY_MATRIX.yml`, and
   `release/PRE_1_0_CHECKLIST.md` to reflect what was actually validated~~
   **DONE, ongoing** — updated after every phase in this pass (2026-09-22
   through 2026-09-24); continue this discipline for any future validation
   work, per the project's own promotion rule
   (`release/compatibility/COMPATIBILITY_MATRIX.yml`: *"No platform is
   marked SUPPORTED before reproducible lab evidence exists."*).
7. ~~Build and import the complete eight-panel dashboard.~~ **DONE
   2026-09-23** — see
   `release/runtime-validation/dashboard/DASHBOARD_PANELS_EVIDENCE_2026-09-23.md`
   and the new `implementations/wazuh/dashboard/generate_dashboard_ndjson.py`.
   All 8 panels' aggregations confirmed to execute against the real index
   mappings. Actual browser rendering confirmed by the project owner
   2026-09-24 (see item 12 below).
8. ~~Design and live-test a role-based access control model for the
   dashboard.~~ **DONE 2026-09-24** — see
   `release/runtime-validation/dashboard/RBAC_EVIDENCE_2026-09-24.md`
   (Section 6 above). Both roles confirmed working end to end after
   three iterations (v1 found the gap, v2 partially addressed it, v3
   fixed the actual root cause via log-based diagnosis).
9. ~~Test RBAC with `opensearch_security.multitenancy.enabled: true`~~,
   ~~confirm indexing/aggregation behavior at realistic document volume~~,
   and ~~isolate whether saved objects survive a plain restart (no
   upgrade)~~. **All DONE 2026-09-24** — see
   `release/runtime-validation/dashboard/ADDITIONAL_VALIDATION_2026-09-24.md`.
   RBAC v3 unaffected by the multitenancy toggle either way; 1,166
   synthetic documents indexed and aggregated correctly in under 50ms;
   plain restarts (2 cycles, no upgrade) lost nothing, narrowing the
   known persistence risk to the upgrade path specifically.
10. Also audited SCA check-ID collision against all ~70 Wazuh-bundled
    vendor policies (not just the one tested alongside ours previously) —
    **DONE 2026-09-24**, see the `SCA_EVIDENCE_2026-09-23.md` addendum.
    Full bundled range 1000-40165, nowhere near our 910001-910006.
11. Remaining after this pass: SSO/external identity provider integration
    for the RBAC backend roles (deliberately deferred, see
    `implementations/wazuh/dashboard/rbac/README.md` "Scope and
    limitations").
12. Confirming the 8-panel dashboard actually renders in a real browser
    session was blocked in the automated pass — the lab host has too
    little RAM headroom, ~184Mi free, to safely install a headless
    browser, and the coordinating session's own sandbox lacks
    root/package-install access. **DONE 2026-09-24** — the project owner
    opened the dashboard directly in their own browser (steps in
    `implementations/wazuh/DEPLOYMENT.md` section 5) and confirmed it
    renders correctly.
13. Post-1.0.0: smoke-testing the dashboard with real synthetic
    `pdp-*` data (31 documents, spread across a month so every panel's
    grouping field had full enum coverage) surfaced a real bug — all 8
    panels showed "No results found" despite the data and aggregations
    being correct, because the dashboard's `timeRestore: false`
    inherited the viewer's own global time-picker default (this lab:
    last 24h) while every panel is time-filtered (all three index
    patterns set `timeFieldName: @timestamp`). **FIXED 2026-09-24** —
    `generate_dashboard_ndjson.py` now sets `timeRestore: true` with a
    wide `timeFrom`/`timeTo`; redeployed and reconfirmed against the
    real lab. See `release/runtime-validation/dashboard/DASHBOARD_TIME_RANGE_EVIDENCE_2026-09-24.md`,
    including a documented browser-URL-state caveat (an already-open
    tab can still show the old range after the fix, until reopened
    fresh).
