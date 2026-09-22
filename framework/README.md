# Framework Source of Truth

This directory contains the stable, implementation-neutral PDP Control Framework source.

Canonical chain:

```text
Legal Requirement -> PDP Control -> Generic Requirement -> Control Profile
```

Product-specific implementation content must live under `implementations/` and must not redefine legal meaning.

Subdirectories:

- `legal/` authoritative legal requirement mapping and source review
- `controls/` PDP control catalogue
- `requirements/` technology-neutral requirements
- `profiles/` reusable applicability/control profiles
- `taxonomy/` normalized PDP-relevant technical event taxonomy
- `models/` processing, asset, test, evidence, finding models
- `schemas/` machine-readable runtime object schemas
- `evidence/` evidence type definitions
