# Wazuh Lab Validation Guide — v0.6 Draft

## Status

`LAB_VALIDATION_REQUIRED`

The implementation artifacts in v0.6 are intentionally not marked normative until validated on a supported Wazuh lab.

## 1. Test topology

Recommended minimum lab:

```text
Wazuh Manager / Indexer / Dashboard
          |
          +-- Ubuntu 24.04 agent
          |
          +-- Ubuntu 24.04 PostgreSQL agent (optional)
```

## 2. Rule installation

Custom rules belong on the Wazuh manager under:

```text
/var/ossec/etc/rules/
```

Copy:

```text
pdp_authentication.xml
pdp_privileged_access.xml
pdp_fim.xml
pdp_telemetry_health.xml
```

Validate each file with:

```bash
xmllint --noout FILE.xml
```

Test representative log samples with:

```bash
/var/ossec/bin/wazuh-logtest
```

Restart manager only after validation:

```bash
systemctl restart wazuh-manager
```

## 3. SCA deployment

The custom SCA policy is:

```text
pdp_linux_baseline.yml
```

Place it in a manager group/shared location according to the Wazuh deployment model, then configure the group `agent.conf` to enable that policy.

Validate on a non-production agent first.

## 4. Centralized configuration

Suggested group layering:

```text
default
  +
pdp-linux-baseline
  +
pdp-database        (only for DB assets)
```

Because agents may belong to multiple groups, use groups as implementation overlays.

Replace all placeholder labels:

```text
SET_ME
```

before production use.

## 5. Required validation cases

### SCA

For every check validate:

```text
PASS case
FAIL case
NOT APPLICABLE / missing prerequisite
collector/command error
```

### Authentication

Generate:

```text
single failed login
repeated failed login
successful login
```

Confirm the custom rule chain does not create alert loops.

### FIM

Modify and delete a harmless test file in an approved monitored directory.

Confirm:

```text
creation/modification
deletion
path
timestamp
agent context
```

### Telemetry health

Stop a test agent or relevant log source and verify the chosen health signal in the actual Wazuh deployment.

The draft telemetry rule must be adapted to observed manager/agent health event formats before becoming normative.

## 6. Promotion gate

A test moves:

```text
DRAFT_DESIGN
-> LAB_VALIDATED
```

only after recording:

- Wazuh version
- OS version
- exact configuration
- input fixture
- expected result
- observed result
- evidence fields
- failure/error result
- reviewer
- validation date

## 7. Privacy validation

Before enabling broad FIM or log collection, verify that the configuration does not unnecessarily ingest:

- document contents
- secrets
- credentials
- raw Personal Data
- database query payloads containing Personal Data

Prefer security metadata and audit events.

## 8. Important boundary

A successful test means:

```text
the implementation-specific technical condition passed
```

It does not mean:

```text
the organization is compliant with UU PDP
```
