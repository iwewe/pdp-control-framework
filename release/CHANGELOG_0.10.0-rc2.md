# 0.10.0-rc2 - Release-readiness pass

## Completed

### Authoritative legal-source review

Articles 20-56 were re-reviewed against the official UU No. 27 Tahun 2022 PDF.

Legal Requirement entries changed from **46** to **64**.

Material corrections include Article 35 letter-based citation, missing consent/access/restriction requirements, Article 39(2), Article 48 detail, Article 52 exact cross-reference, Article 54(2), and the binding Constitutional Court interpretation of Article 53.

### Static dashboard/import package

Added:

- importable index-pattern/dashboard-shell NDJSON,
- real dashboard/indexer validation runner,
- machine-readable dashboard validation status.

### Real Wazuh gate

Added a version-pinned Wazuh 4.14.7 runtime validation runner.

## Still open for 1.0

- external/independent legal review if required by project governance,
- actual Wazuh 4.14.7 runtime execution,
- actual Wazuh Indexer/Dashboard import execution,
- export/import validation of the completed eight-panel dashboard.

## Current coverage

- Legal requirements: **64**
- With Wazuh technical-test coverage: **24**
- Generic-requirement-only: **8**
- No technical coverage: **32**

These are engineering coverage figures, not legal compliance percentages.
