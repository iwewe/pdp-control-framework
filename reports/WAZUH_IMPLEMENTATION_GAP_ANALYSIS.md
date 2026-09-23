# Wazuh Implementation Gap Analysis

**Framework version reviewed:** 0.10.0-rc2
**Review date:** 2026-09-22 (original), updated 2026-09-23 with real lab
evidence
**Scope:** `implementations/wazuh/` content (rules, decoders, SCA policy, agent
configuration, PostgreSQL audit profile, indexer/dashboard artifacts) and the
associated release-readiness status files.

> This report is an engineering gap analysis for real-world Wazuh deployment.
> It is not a legal compliance assessment and does not replace the project's
> own release gates in `release/RELEASE_GATES.yml` and
> `release/PRE_1_0_CHECKLIST.md`.

## Summary

**Update 2026-09-23:** a real Wazuh 4.14.7 + PostgreSQL 17.11 + pgAudit 17.1
lab (Ubuntu 24.04.4 LTS) is now up, and every remaining phase — authentication,
PostgreSQL, privileged access, FIM, SCA, centralized `agent.conf`
distribution to a genuinely separate enrolled agent, and real Wazuh
Indexer/Dashboard import — has now been exercised against it. See Sections
2-5 below and `release/runtime-validation/`. This found and fixed six real
defects that static validation and CI schema validation could not catch
(the pgAudit decoder; two in the FIM rules; an invalid `<syscollector>`
element that silently broke an entire `agent.conf`; six schema-required
fields missing across all three OpenSearch index templates, which meant no
genuinely valid evidence/assessment/finding document could ever be
indexed; and a `securitytenant` header bug in the dashboard-import
script), plus one non-blocking design limitation in the privileged-access
rule. One defect remains **unresolved**: the SCA policy produces zero
usable results when distributed via a centralized agent group (only as a
local per-endpoint policy, which does work).

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

## 4. Agent-group deployment bugs (2026-09-23) — one fixed, one unresolved

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

**Unresolved (severity: high for this specific deployment path):** once
the above was fixed, `implementations/wazuh/sca/pdp_linux_baseline.yml`
loaded correctly via the group but produced **zero usable results** — all
6 checks evaluated to `not applicable`. Every check uses a `c:<command>`
rule, and Wazuh disables remote command execution by default
(`sca.remote_commands=0`) for any SCA policy delivered via centralized
configuration, as a guardrail against a compromised manager pushing
arbitrary commands to agents. Setting `sca.remote_commands=1` in
`local_internal_options.conf` — tried on both the agent and the manager,
each with a full daemon stop+start confirmed via a fresh non-zombie
process — did not change the outcome across 4 separate restart cycles,
verified against the authoritative `sca_check` table in the manager's
per-agent database (not just log messages, which stopped showing the
"disabled" warning without the underlying behavior actually changing —
likely Wazuh's own repeated-message log suppression).

**Practical effect:** `pdp_linux_baseline.yml` currently only produces
real results as a **local** policy in each endpoint's own `ossec.conf`
(as validated in Section "SCA_EVIDENCE" below / `SCA_EVIDENCE_2026-09-23.md`).
It cannot currently be distributed via an agent group and evaluate
anything. `implementations/wazuh/DEPLOYMENT.md` has been corrected to stop
recommending group-based SCA distribution until this is resolved (either
by finding the correct mechanism to enable `sca.remote_commands` for a
managed fleet, or by redesigning the checks to avoid `c:` commands where a
file-content check can substitute).

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

## 6. Other operational gaps for a real deployment

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

## 7. Suggested priority order

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
   **Still open:** telemetry-health (110301) has no fixture yet; the API
   `/logtest` harness (`run_api_logtest.py`) itself has not been run yet
   either (CLI was used directly instead).
4. ~~Execute the SCA policy on a real Ubuntu 24.04 agent and confirm ID
   uniqueness and check results.~~ **DONE 2026-09-23** (local policy) — see
   `release/runtime-validation/wazuh-4.14.7/SCA_EVIDENCE_2026-09-23.md`.
   All 6 checks ran correctly with no ID collision against the vendor
   policy. Also now tested against a genuinely separate enrolled agent
   (Section 4 above) — **found the policy does not work at all via
   centralized/group distribution** (`sca.remote_commands`), which
   remains unresolved.
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
   through 2026-09-23); continue this discipline for any future validation
   work, per the project's own promotion rule
   (`release/compatibility/COMPATIBILITY_MATRIX.yml`: *"No platform is
   marked SUPPORTED before reproducible lab evidence exists."*).
7. ~~Build and import the complete eight-panel dashboard.~~ **DONE
   2026-09-23** — see
   `release/runtime-validation/dashboard/DASHBOARD_PANELS_EVIDENCE_2026-09-23.md`
   and the new `implementations/wazuh/dashboard/generate_dashboard_ndjson.py`.
   All 8 panels' aggregations confirmed to execute against the real index
   mappings; not confirmed in an actual browser rendering session.
8. Remaining after this pass: telemetry-health fixtures, the unresolved
   `sca.remote_commands` centralized-SCA blocker (Section 4), and a
   role-based access control model for the dashboard.
