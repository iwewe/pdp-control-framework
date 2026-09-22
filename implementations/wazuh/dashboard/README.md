# PDP Dashboard Design v0.9

Wazuh Dashboard supports creating custom visualizations and combining them into dashboards. Custom index patterns are also supported. citeturn495925search0turn495925search1

The framework dashboard intentionally uses three dedicated index patterns:

```text
pdp-evidence-*
pdp-assessment-*
pdp-findings-*
```

## Top-level view

```text
+------------------------------------------------------+
| PDP Continuous Control Dashboard                     |
+------------------------------------------------------+
| PASS | FAIL | REVIEW | N/A | Evidence Health         |
+------------------------------------------------------+
| Open Findings by Severity                            |
+------------------------------------------------------+
| Controls Requiring Review                            |
+------------------------------------------------------+
| Processing Activity | Control | State | Coverage      |
+------------------------------------------------------+
| Evidence Quality | Telemetry / Event Trend           |
+------------------------------------------------------+
```

## Important language

Use:

```text
Control Assessment State
Evidence Coverage
Evidence Health
Continuous Monitoring Coverage
Open Findings
```

Avoid:

```text
UU PDP compliance %
Legal compliance score
Article violation count
```

unless a separate authorized legal assessment explicitly produces that conclusion.

## Recommended access model

Different users may require different privileges:

- Security operators: evidence and technical findings
- Privacy reviewers: assessment + processing context
- Legal reviewers: traceability and review queue
- Auditors: read-only evidence/assessment registry
- Administrators: index/dashboard management

This should be enforced using the indexer's role-based access controls in the deployment.
