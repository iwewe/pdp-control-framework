# PDP Indexing Model

## Recommended indices

```text
pdp-evidence-YYYY.MM
pdp-assessment-YYYY.MM
pdp-findings-YYYY.MM
```

The index templates in this directory explicitly map fields used by the framework.

Wazuh documents that custom index patterns can be created and visualized in the dashboard. The framework intentionally uses dedicated PDP indices so compliance evidence is not mixed with `wazuh-alerts-*`.

Recommended index patterns:

```text
pdp-evidence-*
pdp-assessment-*
pdp-findings-*
```

Use `@timestamp` as the time field for framework-generated documents.

## Why separate indices

- different retention periods
- different access control
- distinct lifecycle
- reduced mapping collisions
- easier audit/export
- findings should remain usable after original alert rollover

## Privacy rule

Do not index raw `full_log` in PDP framework indices by default.

Keep only normalized/minimized evidence metadata and references to the original source where needed.
