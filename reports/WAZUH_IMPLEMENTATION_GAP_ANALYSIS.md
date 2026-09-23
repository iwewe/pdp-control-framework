# Wazuh Implementation Gap Analysis

**Framework version reviewed:** 0.10.0-rc2
**Review date:** 2026-09-22
**Scope:** `implementations/wazuh/` content (rules, decoders, SCA policy, agent
configuration, PostgreSQL audit profile, indexer/dashboard artifacts) and the
associated release-readiness status files.

> This report is an engineering gap analysis for real-world Wazuh deployment.
> It is not a legal compliance assessment and does not replace the project's
> own release gates in `release/RELEASE_GATES.yml` and
> `release/PRE_1_0_CHECKLIST.md`.

## Summary

The Wazuh implementation profile is architecturally complete (rules, SCA
checks, decoders, agent configuration, index templates, dashboard shell all
exist and are internally consistent and traceable to controls/requirements),
but **none of it has been executed against a real Wazuh runtime**. Static
validation (YAML/XML/JSON well-formedness, ID uniqueness, schema conformance)
passes in CI; behavioral validation against a live manager, indexer, and
PostgreSQL instance has never run. One concrete defect was found during this
review that static validation cannot catch.

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

## 3. Other operational gaps for a real deployment

- **Credential provisioning is undocumented.** `run_api_logtest.py` and
  `validate_real_import.py` correctly read `WAZUH_API_USER`,
  `WAZUH_API_PASSWORD`, `PDP_INDEXER_PASSWORD`, `PDP_DASHBOARD_PASSWORD` from
  the environment (no hardcoded secrets), but there is no `.env.example` or
  CI/CD secrets-setup guidance describing how these should be provisioned in
  a real lab or pipeline.
- **`agent.conf` distribution is not documented.** The repo defines
  `implementations/wazuh/shared/pdp-linux-baseline/agent.conf` and
  `pdp-database/agent.conf`, and `docs`/`README` recommend agent groups
  (`pdp-linux-baseline`, `pdp-database`, `pdp-high-criticality`, etc.), but
  there is no script or instructions for pushing these into
  `/var/ossec/etc/shared/<group>/agent.conf` on a real manager.
- **SCA check-ID collision has not been checked against a real installation.**
  `implementations/wazuh/sca/pdp_linux_baseline.yml` uses IDs starting at
  `910001`; whether this collides with Wazuh's bundled SCA policies or other
  policies already present in a target environment has not been verified
  against an actual manager/agent.
- **No LICENSE file** in the repository — not a Wazuh-specific blocker, but
  relevant if this profile is meant to be reused or contributed to by others.
- **`release/PRE_1_0_CHECKLIST.md` sections D–G** (Wazuh implementation,
  evidence/assessment, indexer/dashboard, CI/repository) remain fully
  unchecked; none of their items should be assumed complete until explicitly
  verified.

## 4. Suggested priority order

1. ~~Stand up a Wazuh 4.14.7 + Wazuh Indexer/Dashboard + PostgreSQL 17 +
   pgAudit lab~~ **DONE 2026-09-23** (native install on Ubuntu 24.04.4 LTS,
   not Docker).
2. ~~Fix the pgAudit decoder/log-format mismatch described in Section 2~~
   **DONE 2026-09-22, lab-confirmed 2026-09-23.**
3. Run `wazuh-logtest` / the API `/logtest` harness against all rule
   groups. **Partially done:** authentication (110001-110002) and
   PostgreSQL (110401-110406) fixtures confirmed via `wazuh-logtest` CLI —
   see `release/runtime-validation/wazuh-4.14.7/LOGTEST_EVIDENCE_2026-09-23.md`.
   **Still open:** privileged access, FIM, and telemetry-health rule
   families have no fixtures yet, so they remain unexercised; the API
   `/logtest` harness (`run_api_logtest.py`) itself has not been run yet
   either (CLI was used directly instead).
4. Execute the SCA policy on a real Ubuntu 24.04 agent and confirm ID
   uniqueness and check results. **Still open.**
5. Import the three index templates and the dashboard saved-objects NDJSON
   into a real Wazuh Indexer/Dashboard instance. **Still open** (the lab's
   indexer/dashboard are running but have not yet been used for this).
6. Update `release/runtime-validation/*/STATUS.yml`,
   `release/compatibility/COMPATIBILITY_MATRIX.yml`, and
   `release/PRE_1_0_CHECKLIST.md` to reflect what was actually validated —
   do not mark items complete without reproducible lab evidence, per the
   project's own promotion rule (`release/compatibility/COMPATIBILITY_MATRIX.yml`:
   *"No platform is marked SUPPORTED before reproducible lab evidence
   exists."*).
