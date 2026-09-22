# Legal Source Review Coverage - 0.10.0-rc2

**Review date:** 22 September 2026  
**Scope:** Articles 20-56 of UU No. 27 Tahun 2022, plus Constitutional Court Decision 151/PUU-XXII/2024.  
**Review type:** authoritative-text source review for compliance engineering.  
**External legal counsel review:** **not performed**.

## Authoritative sources

1. UU No. 27 Tahun 2022 official PDF (BPK legal database):  
   https://peraturan.bpk.go.id/Download/224884/UU%20Nomor%2027%20Tahun%202022.pdf

2. Constitutional Court Decision 151/PUU-XXII/2024, decided 30 July 2025:  
   https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024

## Result

The legal mapping has been reviewed article-by-article against the official statutory text.

- Previous LR entries: **46**
- Reviewed LR entries: **64**
- Newly explicit LR entries: **18**
- Removed LR IDs: **0**
- Source review state: **SOURCE_VERIFIED**
- Counsel/legal-opinion state: **NOT_PERFORMED**

## Material corrections

### Article 35 citation corrected

The previous mapping treated Article 35 as paragraph `(1)` and `(2)`.
The statute has no numbered paragraphs in Article 35; it contains letters **a** and **b**.

The framework now records:

- `LR-035-01` -> Article 35 letter a
- `LR-035-02` -> Article 35 letter b

### Missing legal conditions added

The review added explicit mapping for:

- Article 21(2): notification before changed consent information takes effect
- Article 22(4)-(5): presentation/validity conditions for consent
- Article 23: contractual clause validity
- Article 25(1) and 25(2): special child-data processing and parent/guardian consent
- Article 26(1)-(3): special disability-data processing, communication, and consent
- Article 29(2): verification duty
- Article 30(2): notification of correction/update result
- Article 32(2): 3 x 24-hour access deadline
- Article 33: mandatory refusal conditions
- Article 39(2): reliable, secure, responsible electronic security system
- Article 41(2)-(3): restriction exceptions and notification
- Article 48(1)-(4): corporate-change notification/lifecycle duties
- Article 54(2): risk-aware performance of PDP function

### Article 34 language corrected

Article 34(2) is now represented as statutory **high-risk applicability criteria**, rather than phrasing it as an independently worded duty to "identify" risk.

### Article 52 made exact

The mapping now explicitly states the controller duties that Article 52 applies to processors:
Articles 29, 31, 35, 36, 37, 38, and 39.

### Article 53 incorporates Constitutional Court interpretation

The original statutory text joins conditions in Article 53(1)(b)-(c) with `dan`.
Putusan MK 151/PUU-XXII/2024 states that the word `dan` in Article 53(1)(b) has no binding force unless interpreted as **`dan/atau`**.

The framework therefore retains the original statute as source while recording the binding Constitutional Court interpretation separately.

### Article 46 breach concept

The framework retains the statutory 3 x 24-hour notification requirement and records the explanation that a "kegagalan Pelindungan Data Pribadi" concerns confidentiality, integrity, and availability failures, including unauthorized destruction, loss, alteration, disclosure, or access.

## Requirement types

The LR layer now distinguishes:

- `obligation`
- `obligation_with_conditions`
- `validity_condition`
- `applicability_criteria`
- `applicability_exception`
- `responsibility_rule`

This prevents an exception or legal consequence from being incorrectly treated as a normal technical control.

## Added IDs

- LR-021-02
- LR-022-02
- LR-022-03
- LR-023-01
- LR-025-02
- LR-026-02
- LR-026-03
- LR-029-02
- LR-030-02
- LR-032-02
- LR-033-01
- LR-039-02
- LR-041-02
- LR-041-03
- LR-048-02
- LR-048-03
- LR-048-04
- LR-054-02

## Release interpretation

`SOURCE_VERIFIED` means the framework summary was checked against authoritative legal text.

It does **not** mean:

- formal legal opinion,
- regulator approval,
- certification of compliance,
- external-counsel sign-off.

For a public `1.0` release, an independent Indonesian privacy-law review remains recommended.
