# Legal Source Preservation

This directory archives a snapshot of the two primary legal-source pages
cited in `README.md` and `framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md`,
so that the framework's legal traceability does not depend solely on the
availability of external government/court websites.

| File | Source page | Retrieved | Notes |
|---|---|---|---|
| `UU_27_2022_KOMDIGI_METADATA.md` | https://jdih.komdigi.go.id/produk_hukum/view/id/832/t/crc32/ | 2026-09-22 | Metadata page for UU No. 27 Tahun 2022. Statutory article text on this page is loaded dynamically per-article and was not captured; the page itself only serves as the metadata/index record. |
| `MK_151_PUU_XXII_2024_SOURCE.md` | https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024 | 2026-09-22 | The `mkri.id` search/listing page blocks automated fetches (HTTP 403). The official decision PDF was located instead and a local copy preserved in this directory. |
| `putusan-mkri-151-PUU-XXII-2024.pdf` | https://s.mkri.id/public/content/persidangan/putusan/putusan_mkri_12970_1753859809.pdf | 2026-09-22 | Preserved copy of the official Constitutional Court decision PDF. |

## Why this exists

`framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md` already records the
*result* of reviewing these sources (the article-by-article corrections and
the binding interpretation from the Constitutional Court decision). This
directory preserves the *source pages themselves* as evidence, independent of
whether the external sites remain reachable in the future.

This is an archival convenience, not a legal opinion, and does not replace
`external_legal_counsel_review` in `framework/legal/review/LEGAL_REVIEW_STATUS.yml`,
which remains `NOT_PERFORMED`.
