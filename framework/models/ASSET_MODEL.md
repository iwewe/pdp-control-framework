# Asset and System Model

**Status:** Draft v0.3

## 1. Purpose

Assets link technology-neutral PDP controls to actual infrastructure.

An asset is not inherently "PDP compliant". It becomes relevant because it supports one or more Processing Activities.

```text
Processing Activity
      |
      +------ Asset
      |          |
      |          +-- Wazuh Agent
      |          +-- Cloud Resource
      |          +-- Database
      |          +-- Application
      |
      +------ Processor / SaaS
```

## 2. Asset Object

```yaml
id: ASSET-DB-001

name: hr-db-01

asset_type: database_server

owner:
  organizational_unit: IT
  technical_owner: Infrastructure Team

processing_activities:
  - PA-001

data_context:
  personal_data: true
  specific_personal_data: true

criticality:
  confidentiality: high
  integrity: high
  availability: medium

environment: production

location:
  logical: internal_datacenter

technology:
  os: Ubuntu
  database: PostgreSQL

monitoring:
  wazuh:
    enabled: true
    agent_id: "014"
  database_audit:
    enabled: true

evidence_sources:
  - ES-WAZUH-014
  - ES-PG-AUDIT-001
```

## 3. Asset Types

Suggested canonical values:

- endpoint
- server
- database_server
- application
- storage
- backup
- network_device
- security_device
- cloud_resource
- saas_service
- mobile_device
- physical_archive
- integration
- external_processor

## 4. Criticality

Use separate dimensions:

```text
Confidentiality
Integrity
Availability
```

Recommended scale:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Do not infer criticality solely from CVSS or asset exposure.

## 5. Data Context

An asset can support multiple Processing Activities.

Therefore avoid:

```yaml
contains_personal_data: yes
```

as the only classification.

Prefer:

```yaml
processing_activities:
  - PA-001
  - PA-008
```

The Processing Activity provides the legal and data context.

## 6. Technical Identifier Mapping

Keep product identifiers separate:

```yaml
technical_identifiers:
  wazuh_agent_id: "014"
  hostname: hr-db-01
  cloud_resource_id: null
  cmdb_id: CI-8821
```

Changing a Wazuh agent ID must not change the stable PDP asset ID.

## 7. Asset Lifecycle

```text
DISCOVERED
  -> REGISTERED
  -> IN_SCOPE
  -> MONITORED
  -> RETIRED
```

When an asset is retired, evidence retention rules still apply.
