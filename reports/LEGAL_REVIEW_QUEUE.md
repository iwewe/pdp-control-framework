# Legal / Manual Review Queue

> Engineering traceability tooling: identifies which legal requirements have no Wazuh technical coverage and therefore need a human/legal reviewer, and tracks whether each has been looked at. It does not determine the correct legal answer for any item -- see `implementations/wazuh/dashboard/UI_POSITIONING.md` section 7.D.

**32** legal requirements currently need manual/legal review (of 64 total; see `reports/COVERAGE_REPORT.md` for the full traceability picture).

Status is tracked in `framework/legal/review/LEGAL_REVIEW_QUEUE_STATUS.yml` -- edit that file directly to record review progress; re-running the generator never overwrites it.

## Summary

- NOT_REVIEWED: **32**
- IN_PROGRESS: **0**
- REVIEWED: **0**

## Vulnerable data subjects (children / persons with disabilities) (7)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-025-01 | 25(1) | Pengendali Data Pribadi | Pemrosesan Data Pribadi anak diselenggarakan secara khusus. | NOT_REVIEWED |
| LR-025-02 | 25(2) | Pengendali Data Pribadi | Pemrosesan Data Pribadi anak wajib mendapat persetujuan orang tua dan/atau wali sesuai peraturan perundang-undangan. | NOT_REVIEWED |
| LR-026-01 | 26(1) | Pengendali Data Pribadi | Pemrosesan Data Pribadi penyandang disabilitas diselenggarakan secara khusus. | NOT_REVIEWED |
| LR-026-02 | 26(2) | Pengendali Data Pribadi | Pemrosesan Data Pribadi penyandang disabilitas dilakukan melalui komunikasi dengan cara tertentu sesuai peraturan perundang-undangan. | NOT_REVIEWED |
| LR-026-03 | 26(3) | Pengendali Data Pribadi | Pemrosesan Data Pribadi penyandang disabilitas wajib mendapat persetujuan penyandang disabilitas dan/atau walinya sesuai peraturan perundang-undangan. | NOT_REVIEWED |
| LR-041-03 | 41(3) | Pengendali Data Pribadi | Pengendali wajib memberitahukan kepada Subjek Data bahwa penundaan dan pembatasan pemrosesan telah dilaksanakan. | NOT_REVIEWED |
| LR-054-02 | 54(2) | Pejabat/Petugas Fungsi Pelindungan Data Pribadi | Dalam melaksanakan tugasnya, fungsi Pelindungan Data Pribadi memperhatikan risiko pemrosesan dengan mempertimbangkan sifat, ruang lingkup, konteks, dan tujuan pemrosesan. | NOT_REVIEWED |

## DPIA sufficiency (1)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-034-01 | 34(1) | Pengendali Data Pribadi | Pengendali wajib melakukan penilaian dampak Pelindungan Data Pribadi jika pemrosesan memiliki potensi risiko tinggi terhadap Subjek Data. | NOT_REVIEWED |

## DPO applicability (3)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-053-01 | 53(1) | Pengendali Data Pribadi dan Prosesor Data Pribadi | Pengendali dan Prosesor wajib menunjuk pejabat/petugas fungsi Pelindungan Data Pribadi apabila salah satu kondisi pemicu yang berlaku terpenuhi, dengan Pasal 53 ayat (1) huruf b dibaca sesuai Putusan MK 151/PUU-XXII/2024. | NOT_REVIEWED |
| LR-053-02 | 53(2) | Pengendali Data Pribadi dan Prosesor Data Pribadi | Pejabat/petugas fungsi Pelindungan Data Pribadi ditunjuk berdasarkan profesionalitas, pengetahuan hukum dan praktik Pelindungan Data Pribadi, serta kemampuan memenuhi tugas. | NOT_REVIEWED |
| LR-054-01 | 54(1) | Pejabat/Petugas Fungsi Pelindungan Data Pribadi | Fungsi Pelindungan Data Pribadi paling sedikit menginformasikan/memberi saran, memantau dan memastikan kepatuhan, memberi saran mengenai DPIA dan memantau kinerja, serta berkoordinasi dan menjadi narahubung isu pemrosesan. | NOT_REVIEWED |

## Data subject rights timelines (access / correction / restriction / withdrawal) (7)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-030-01 | 30(1) | Pengendali Data Pribadi | Pengendali wajib memperbarui dan/atau memperbaiki kesalahan/ketidakakuratan paling lambat 3 x 24 jam sejak menerima permintaan. | NOT_REVIEWED |
| LR-030-02 | 30(2) | Pengendali Data Pribadi | Pengendali wajib memberitahukan hasil pembaruan dan/atau perbaikan kepada Subjek Data. | NOT_REVIEWED |
| LR-032-02 | 32(2) | Pengendali Data Pribadi | Akses wajib diberikan paling lambat 3 x 24 jam sejak permintaan akses diterima. | NOT_REVIEWED |
| LR-033-01 | 33 | Pengendali Data Pribadi | Pengendali wajib menolak akses perubahan Data Pribadi dalam kondisi yang ditetapkan UU, termasuk risiko terhadap keamanan/kesehatan, pengungkapan Data Pribadi orang lain, dan kepentingan pertahanan/keamanan nasional. | NOT_REVIEWED |
| LR-040-02 | 40(2) | Pengendali Data Pribadi | Penghentian pemrosesan setelah penarikan persetujuan dilakukan paling lambat 3 x 24 jam sejak permintaan diterima. | NOT_REVIEWED |
| LR-041-01 | 41(1) | Pengendali Data Pribadi | Pengendali wajib melakukan penundaan dan pembatasan pemrosesan, sebagian atau seluruhnya, paling lambat 3 x 24 jam sejak menerima permintaan. | NOT_REVIEWED |
| LR-041-02 | 41(2) | Pengendali Data Pribadi | Penundaan dan pembatasan pemrosesan tunduk pada pengecualian yang secara khusus ditetapkan dalam Pasal 41 ayat (2). | NOT_REVIEWED |

## Consent validity (10)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-020-02 | 20(2) | Pengendali Data Pribadi | Dasar pemrosesan harus sesuai dengan salah satu dasar yang diakui UU: persetujuan eksplisit, perjanjian, kewajiban hukum, kepentingan vital, kepentingan umum/pelayanan publik/kewenangan, dan/atau kepentingan sah dengan penyeimbangan kepentingan. | NOT_REVIEWED |
| LR-021-01 | 21(1) | Pengendali Data Pribadi | Jika pemrosesan didasarkan pada persetujuan, Pengendali wajib memberikan informasi yang diwajibkan mengenai legalitas, tujuan, jenis/relevansi data, retensi, rincian informasi, jangka waktu pemrosesan, dan hak Subjek Data. | NOT_REVIEWED |
| LR-021-02 | 21(2) | Pengendali Data Pribadi | Jika informasi persetujuan berubah, Pengendali wajib memberitahukan perubahan kepada Subjek Data sebelum perubahan tersebut terjadi. | NOT_REVIEWED |
| LR-022-01 | 22(1) | Pengendali Data Pribadi | Persetujuan pemrosesan dilakukan secara tertulis atau terekam dan dapat disampaikan secara elektronik atau nonelektronik. | NOT_REVIEWED |
| LR-022-02 | 22(4) | Pengendali Data Pribadi | Jika permintaan persetujuan memuat tujuan lain, permintaan tersebut harus dapat dibedakan secara jelas, mudah dipahami dan diakses, serta menggunakan bahasa sederhana dan jelas. | NOT_REVIEWED |
| LR-022-03 | 22(5) | Pengendali Data Pribadi | Persetujuan yang tidak memenuhi ketentuan bentuk dan pemisahan tujuan yang diwajibkan UU batal demi hukum. | NOT_REVIEWED |
| LR-023-01 | 23 | Pengendali Data Pribadi | Klausul perjanjian yang meminta pemrosesan Data Pribadi tanpa persetujuan sah secara eksplisit dari Subjek Data batal demi hukum. | NOT_REVIEWED |
| LR-024-01 | 24 | Pengendali Data Pribadi | Dalam melakukan pemrosesan, Pengendali wajib dapat menunjukkan bukti persetujuan yang diberikan Subjek Data. | NOT_REVIEWED |
| LR-040-01 | 40(1) | Pengendali Data Pribadi | Pengendali wajib menghentikan pemrosesan ketika Subjek Data menarik kembali persetujuan. | NOT_REVIEWED |
| LR-051-02 | 51(5) | Prosesor Data Pribadi | Prosesor wajib memperoleh persetujuan tertulis Pengendali sebelum melibatkan Prosesor lain. | NOT_REVIEWED |

## Lawful basis (3)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-020-01 | 20(1) | Pengendali Data Pribadi | Pengendali wajib memiliki dasar pemrosesan Data Pribadi. | NOT_REVIEWED |
| LR-027-01 | 27 | Pengendali Data Pribadi | Pengendali wajib melakukan pemrosesan secara terbatas dan spesifik, sah secara hukum, dan transparan. | NOT_REVIEWED |
| LR-028-01 | 28 | Pengendali Data Pribadi | Pengendali wajib melakukan pemrosesan sesuai dengan tujuan pemrosesan Data Pribadi. | NOT_REVIEWED |

## Other legal/manual review (1)

| LR | Article | Actor | Summary | Status |
|---|---:|---|---|---|
| LR-034-02 | 34(2) | Pengendali Data Pribadi | Kategori pemrosesan berpotensi risiko tinggi mencakup keputusan otomatis berdampak signifikan, Data Pribadi spesifik, skala besar, evaluasi/penskoran/pemantauan sistematis, pencocokan/penggabungan data, teknologi baru, dan/atau pemrosesan yang membatasi hak. | NOT_REVIEWED |
