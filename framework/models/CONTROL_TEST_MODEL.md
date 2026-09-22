# Control Test Model

**Status:** Draft v0.3

## 1. Separation

```text
CONTROL
  describes the objective

TEST
  describes how an aspect of the objective is evaluated

EVIDENCE
  is the observed input/output supporting the test
```

One control can have many tests.

One test can produce many evidence items over time.

## 2. Test Object

```yaml
id: WZ-SCA-ACC-001

profile: wazuh
control_id:
  - PDP-ACC-003

title:
  en: SSH root login is disabled

scope:
  asset_types:
    - server
  operating_system:
    - linux

method:
  type: automated
  engine: wazuh_sca

expected:
  condition: PermitRootLogin == "no"

evidence:
  expected_type: configuration_observation
  minimum_quality: Q3

result_mapping:
  matched: PASS
  not_matched: FAIL
  not_collected: REVIEW
```

## 3. Naming

Recommended prefixes:

```text
WZ-SCA-*   Wazuh SCA
WZ-RUL-*   Wazuh rule/detection
WZ-FIM-*   Wazuh FIM
WZ-VUL-*   Wazuh vulnerability
MAN-*      Manual assessment procedure
DOC-*      Documentary review
```

The test ID is implementation-specific. The control ID is not.

## 4. Test Coverage

Expose engineering metrics:

- number of controls with tests
- number of applicable controls with automated tests
- evidence-source coverage
- telemetry coverage
- stale evidence count

Do not call these metrics "UU PDP compliance percentage".

Preferred terminology:

```text
Control Coverage
Automated Test Coverage
Evidence Coverage
Continuous Monitoring Coverage
```
