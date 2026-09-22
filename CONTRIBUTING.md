# Contributing

Thank you for contributing to PDP Control Framework.

## Contribution types

Contributions may affect different layers:

- legal mapping (`LR-*`)
- control semantics (`PDP-*`)
- generic requirements (`REQ-*`)
- control profiles
- event taxonomy
- Wazuh tests/rules/SCA/decoders
- schemas
- documentation
- fixtures and validation

## Required discipline

Do not map a product-specific test directly to a statute.

Use:

```text
Legal Source -> LR -> PDP Control -> REQ -> Test
```

Legal interpretation changes require explicit review.

## Pull requests

A PR should state:

- layer changed,
- IDs changed/added,
- traceability impact,
- backward-compatibility impact,
- validation performed,
- whether legal/privacy review is required.

Implementation tests should not be promoted to `LAB_VALIDATED` without reproducible lab evidence.

## IDs

Never reuse retired IDs for a different meaning.

## Language

Technical findings must not be worded as automatic legal violations.
