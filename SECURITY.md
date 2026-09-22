# Security Policy

## Reporting security issues

Do not open a public issue containing:

- credentials,
- secrets,
- exploitable production details,
- Personal Data,
- live incident evidence.

Use the repository owner's private security-reporting channel once configured.

## Test data

All repository fixtures must use synthetic data.

Do not commit:

- production logs containing Personal Data,
- database dumps,
- access tokens,
- private keys,
- real usernames where avoidable,
- real incident victim information.

## Wazuh content

Custom detection content can affect production security monitoring.

All rule/SCA/decoder changes should be lab-tested before deployment.
