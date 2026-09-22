# Wazuh Implementation and Evidence Profile

**Status:** Pre-1.0 Release Candidate (0.10.0-rc2). All content here is `STATIC_VALIDATED` only; see `reports/WAZUH_IMPLEMENTATION_GAP_ANALYSIS.md` for what real-runtime validation still requires, and `implementations/wazuh/DEPLOYMENT.md` for credential provisioning and agent-group rollout steps.

## 1. Role of Wazuh

Wazuh is not the PDP Control Framework. It is an implementation and evidence profile.

```text
UU PDP
  -> Legal Requirement
      -> PDP Control
          -> Generic Requirement
              -> Wazuh Test
                  -> Evidence
                      -> Finding
```

This prevents a Wazuh rule from becoming a legal interpretation.

## 2. Wazuh Capability Mapping

### Security Configuration Assessment (SCA)

Use for deterministic configuration observations such as:

- authentication configuration
- privileged access configuration
- audit settings
- firewall settings
- unnecessary services
- file/directory permission configuration
- cryptographic service configuration where observable

Custom PDP SCA content should be stored outside Wazuh's default ruleset path so upgrades do not overwrite it.

### File Integrity Monitoring (FIM)

Use for:

- critical configuration changes
- application configuration changes
- policy/config file changes
- selected Personal Data storage paths where monitoring metadata is appropriate
- deletion/change evidence

Do not indiscriminately collect file contents containing Personal Data.

### Log Analysis

Use for:

- authentication
- privilege use
- account lifecycle
- application activity
- database auditing
- processor/service logs
- incident timelines

Prefer collecting security-relevant metadata and audit events rather than duplicating Personal Data into the SIEM.

### Vulnerability Detection

Use for:

- software inventory correlation
- vulnerable package/application findings
- detection/remediation timestamps
- vulnerability state by asset

Vulnerability severity is not PDP legal severity.

### Agent Labels

Use for low-sensitivity context:

```xml
<label key="pdp.asset_id">ASSET-DB-001</label>
<label key="pdp.processing_activity_id">PA-001</label>
<label key="pdp.data_classification">specific</label>
<label key="pdp.criticality">high</label>
<label key="pdp.environment">production</label>
```

Do not place Personal Data itself into labels.

### Agent Groups

Recommended groups describe implementation profiles rather than legal conclusions:

```text
pdp-linux-baseline
pdp-database
pdp-high-criticality
pdp-production
pdp-processor-managed
```

Avoid:

```text
pdp-compliant
pdp-noncompliant
```

## 3. Wazuh Test Naming

```text
WZ-SCA-IAM-001
WZ-SCA-CFG-001

WZ-RUL-IAM-001
WZ-RUL-MON-001

WZ-FIM-INT-001

WZ-VUL-VUL-001

WZ-HLT-EVD-001
```

## 4. Result Semantics

A Wazuh test result is:

```text
PASS
FAIL
REVIEW
ERROR
NOT_APPLICABLE
```

`ERROR` is important. A broken collector must not become `PASS`.

Example:

```text
expected: PermitRootLogin == no
observed: no
result: PASS
```

versus:

```text
collector: unavailable
result: ERROR
control assessment: REVIEW
```

## 5. Telemetry Coverage

Continuous controls should define monitoring windows.

Example:

```yaml
coverage:
  window_days: 30
  expected_hours: 720
  observed_hours: 713
  percent: 99.03
```

A control assessment MAY require a threshold, for example 95% evidence coverage, but such thresholds are framework policy and not legal thresholds unless explicitly sourced.

## 6. Privacy of Monitoring

The monitoring system itself processes data and can create additional privacy risk.

Implementation guidance should therefore include:

- data minimization in logs
- redaction where possible
- access restriction to security logs
- log retention rules
- monitoring of administrator access to Wazuh
- avoidance of unnecessary collection of raw Personal Data
- separation of evidence metadata from business content

## 7. Evidence Export

Evidence exported from Wazuh should retain:

- source agent/asset
- processing activity context
- event/test timestamp
- test ID
- requirement ID
- control ID
- evidence quality
- collection health
- original Wazuh event reference where appropriate

## 8. Update Safety

Implementation content must be kept separately from Wazuh vendor files where Wazuh upgrades could overwrite changes.

Repository-controlled artifacts should be the source of truth for:

- custom SCA policies
- custom rules
- custom decoders
- dashboard definitions
- profile mappings

## 9. What Wazuh Does Not Cover Well

Primary evidence should normally come from other systems for:

- consent validity
- lawful basis
- privacy notices
- DPO appointment
- DPIA approval
- processor contract authorization
- subject-right response content
- legal adequacy of cross-border safeguards
- legal decision to notify a breach

Wazuh can still contribute timestamps, technical context, and operational evidence.
