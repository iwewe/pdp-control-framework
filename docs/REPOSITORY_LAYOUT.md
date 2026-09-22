# Final GitHub Repository Layout

```text
pdp-control-framework/
├── README.md
├── PDP_CONTROL_FRAMEWORK.md
├── FRAMEWORK_MANIFEST.yml
├── VERSION
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── requirements-dev.txt
├── framework/                  # normative, product-neutral source of truth
│   ├── README.md
│   ├── legal/
│   ├── controls/
│   ├── requirements/
│   ├── profiles/
│   ├── taxonomy/
│   ├── models/
│   ├── evidence/
│   └── schemas/
├── implementations/            # product adapters; currently Wazuh
│   └── wazuh/
├── tools/                      # executable project tooling
│   ├── assessment/
│   ├── evidence/
│   ├── findings/
│   ├── validation/
│   ├── reporting/
│   └── export/
├── docs/
│   ├── architecture/           # current stable design documentation
│   ├── history/                # versioned design notes v0.4-v0.9
│   └── REPOSITORY_LAYOUT.md
├── examples/                   # synthetic examples only
├── reports/                    # reproducible committed engineering reports
├── release/
│   ├── compatibility/
│   └── runtime-validation/
├── runtime/                    # generated locally; git-ignored
└── .github/workflows/
```

## Commit policy

**Committed:** normative framework definitions, implementation source, synthetic fixtures, schemas, tooling, reproducible reports, release metadata, static status documents.

**Generated but ignored:** runtime evidence, assessments, findings, registry entries, runtime `RESULT.json`, local exports, credentials, caches.

## Authority model

1. `framework/` defines meaning.
2. `implementations/` implements that meaning for a product.
3. `tools/` evaluates and transforms framework/runtime data but is not normative.
4. `docs/architecture/` explains current architecture.
5. `docs/history/` preserves design evolution without being the current source of truth.
6. `release/` defines release gates and validation status.
