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
