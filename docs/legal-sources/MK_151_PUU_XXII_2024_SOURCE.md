# Source Snapshot: Putusan MK Nomor 151/PUU-XXII/2024

**Requested source URL:** https://www.mkri.id/perkara/persidangan/putusan?jenis=PUU&page=1&perPage=50&search=151%2FPUU-XXII%2F2024
**Retrieval attempted:** 2026-09-22
**Retrieval result:** **HTTP 403 Forbidden** — the `mkri.id` case-search/listing
page blocks automated fetches (confirmed with two independent methods: an
AI-assisted fetch tool and a direct `curl` request with a standard browser
user agent). This is a page-access limitation on the source site, not a
framework defect.

## What was preserved instead

Because the requested URL is a search/listing page (not the decision itself)
and could not be fetched, the actual decision document was located and
preserved directly:

- **Official decision PDF:** https://s.mkri.id/public/content/persidangan/putusan/putusan_mkri_12970_1753859809.pdf
- **Local preserved copy:** [`putusan-mkri-151-PUU-XXII-2024.pdf`](./putusan-mkri-151-PUU-XXII-2024.pdf) (SHA-256: `6dbbdb8092625df850707a86592e240379c4edb7a28cb98b99ff8ac077815e47`)

Automated text extraction from this PDF was attempted but is **unreliable**:
the document uses embedded/subset fonts that do not decode cleanly to plain
text with the tooling available in this environment (no `poppler-utils` /
PDF-library access). Rather than publish a garbled or partially-guessed
transcript of a legal decision, this snapshot instead records verified
metadata corroborated from the Constitutional Court's own announcement and an
independent legal-publishing source, alongside the preserved original PDF as
the authoritative reference for anyone reading the full text.

## Verified case metadata

| Field | Value | Source |
|---|---|---|
| Case number | 151/PUU-XXII/2024 | mkri.id (case filename), corroborating sources below |
| Decision date | 30 July 2025 (Wednesday) | https://www.mkri.id/berita/mk:-data-pribadi-warga-wajib-dilindungi-negara-secara-maksimal-23553 |
| Subject matter | Judicial review (uji materi) of Article 53 paragraph (1) of UU No. 27 Tahun 2022 (UU PDP) against the 1945 Constitution | https://www.hukumonline.com/berita/a/lindungi-maksimal-data-pribadi--mk-tegaskan-kata-dan-dalam-pasal-53-uu-pdp-inkonstitusional-lt688a2dc5c249f/ |
| Result | Permohonan dikabulkan (petition granted) | Same as above |

## Amar putusan (operative ruling) as corroborated by secondary sources

The Constitutional Court declared that the word **"dan"** ("and") in Article
53 paragraph (1) letter b of UU No. 27 Tahun 2022 is conditionally contrary
to the 1945 Constitution and has no binding legal force **unless** it is
read as **"dan/atau"** ("and/or"). This turns the conjunctive condition in
Article 53(1)(b)-(c) into a disjunctive one: the obligation it qualifies
applies when *any one* of the listed conditions is met, not only when *all*
are met simultaneously.

This is consistent with, and directly corroborates, the interpretation
already recorded in
[`framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md`](../../framework/legal/review/LEGAL_SOURCE_REVIEW_0.10.0-rc2.md)
(section "Article 53 incorporates Constitutional Court interpretation") and
reflected in control `PDP-DPO-001` in
[`framework/controls/CONTROL_CATALOGUE.yml`](../../framework/controls/CONTROL_CATALOGUE.yml).

## Corroborating sources consulted

- https://www.mkri.id/berita/mk:-data-pribadi-warga-wajib-dilindungi-negara-secara-maksimal-23553 (Constitutional Court's own press release)
- https://www.hukumonline.com/berita/a/lindungi-maksimal-data-pribadi--mk-tegaskan-kata-dan-dalam-pasal-53-uu-pdp-inkonstitusional-lt688a2dc5c249f/
- https://www.hukumonline.com/pusatdata/detail/lt688acd3a86274/putusan-mahkamah-konstitusi-nomor-151-puu-xxii-2024/

## Caveat

This snapshot does not constitute an independent legal review. Per
`framework/legal/review/LEGAL_REVIEW_STATUS.yml`,
`external_legal_counsel_review` remains `NOT_PERFORMED`. Readers requiring
the exact operative text should read the preserved PDF directly or the
official `mkri.id` publication.
