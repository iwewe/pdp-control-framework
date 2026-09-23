# Retest Workflow

**Status:** Current architecture document (2026-09-23), part of 0.10.0-rc2.

This describes the operational retest workflow referenced by
`framework/models/FINDING_EXCEPTION_REMEDIATION_MODEL.md` section 5
("Lifecycle" — `Finding -> Remediation -> Retest`) and by
`tools/findings/generate_findings.py`'s own docstring ("PASS => do not
auto-close existing findings without explicit remediation/retest
workflow"). It was written and verified against the actual tool behavior
during the 2026-09-23 lab-validation pass (see
`release/runtime-validation/wazuh-4.14.7/API_HARNESS_EVIDENCE_2026-09-23.md`).

## Why retest is manual, not automatic

`tools/findings/generate_findings.py` only ever **creates** findings (on
`FAIL`); it never closes or updates an existing one, even when a later
assessment for the same control shows `PASS`. This is deliberate: a
single passing test run is not sufficient evidence that a remediation
actually fixed the underlying issue rather than, for example, a flaky
collector or a temporarily-correct configuration that will drift back.
Closing a finding is a decision a human makes after reviewing retest
evidence, not something the tooling decides on its own.

## Workflow

1. **Remediation reaches its target date, or its `status` becomes
   `DONE`** (per `framework/models/FINDING_EXCEPTION_REMEDIATION_MODEL.md`
   section 4's `remediation.action`/`remediation.target_date`).
2. **Re-run the same test** that originally produced the failing
   evidence — `remediation.validation.test_id` names it. Use whichever
   transport originally produced the evidence:
   - CLI: `sudo /var/ossec/bin/wazuh-logtest -v < <fixture>` (see
     `implementations/wazuh/tests/scripts/run_wazuh_logtest.sh`), or
   - API: `python3 implementations/wazuh/tests/harness/run_api_logtest.py`
     (produces normalized evidence directly in
     `implementations/wazuh/tests/results/`).
3. **Re-run the assessment aggregator:**
   `python3 tools/assessment/assess_controls.py`. It reads every
   `*.evidence.json` currently in `implementations/wazuh/tests/results/`
   (old and new together — clear stale evidence out of that directory
   first if you want the assessment to reflect only the retest), and
   applies the same conservative precedence used for the original
   assessment:
   - any evidence with `source.collector_health != HEALTHY` forces
     `REVIEW`, regardless of the test result (confirmed 2026-09-23: a
     `PASS` result with a `DEGRADED` collector still produces `REVIEW`,
     never a silent `PASS`);
   - any `ERROR`/`REVIEW` among the results forces `REVIEW`;
   - any `FAIL` forces `FAIL`;
   - only if every result is `PASS` does the control assessment become
     `PASS`.
4. **Interpret the new assessment:**
   - **`PASS`** — the retest supports closing the finding. A human
     reviews the assessment (`runtime/assessments/<control>.assessment.json`)
     and the finding together, then manually updates the finding's
     `status` to `RESOLVED` and `updated_at`, and sets
     `remediation.status` to `DONE`. This step is intentionally not
     automated by `generate_findings.py`.
   - **`FAIL`** — the remediation did not resolve the issue.
     `remediation.status` stays `IN_PROGRESS` (or moves to a
     project-defined `BLOCKED`/`FAILED` state); the finding stays `OPEN`.
     Re-running `tools/findings/generate_findings.py` will not create a
     *second* finding for the same control from this data model as
     written — findings are control-keyed per assessment run, so tie a
     retest's continued failure back to the *existing* finding by
     `assessment_id`, not a new one.
   - **`REVIEW`** — the retest itself is inconclusive (collector
     unhealthy, or a test errored). Fix the collector/test execution
     problem and retest again before drawing any conclusion; do not
     treat `REVIEW` as evidence either for or against closing the finding.
5. **If the finding is under an active exception instead of a
   remediation** (`framework/models/FINDING_EXCEPTION_REMEDIATION_MODEL.md`
   section 3), retest is not required to close it — the exception's own
   `expires_at` governs, and expiry should trigger a fresh assessment
   rather than an automatic re-open.

## What is verified vs. what is still a documentation-only step

Verified by real execution on 2026-09-23 (see
`release/runtime-validation/wazuh-4.14.7/API_HARNESS_EVIDENCE_2026-09-23.md`):
steps 2 and 3 above, including the collector-health precedence rule.

**Not automated (by design, per the anti-false-compliance principle
above):** the finding-closure decision in step 4. There is no
`close_finding.py` or similar tool; closing a finding is a manual edit
until/unless the project decides to build that automation with explicit
human-approval gating.
