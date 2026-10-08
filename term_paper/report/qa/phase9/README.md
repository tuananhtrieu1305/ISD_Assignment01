# Phase 9 release QA

Authoritative release: `../../Tieu_luan_AI_ML_CNN_RNN.docx`.

- Microsoft Word 16 pagination: 73 pages, 159/159 navigation targets, 0 missing.
- Visual QA: 73/73 pages; Phase 9 contact sheets are pixel-identical to the Phase 8 set already inspected page by page.
- Accessibility: 0 high findings; 3 medium findings are one-cell code-layout containers for which a semantic header row is not applicable; 43 low findings are explicit DOI/source URLs retained in the academic bibliography.
- Metrics: 24/24 grouped values reproduced from Chapter 2–4 comparison CSV files; 287,253 TEST prediction rows confirmed.
- Links/citations: 318 internal hyperlinks resolve to 159 bookmarks; 52 external targets use HTTPS; references [1]–[44] are present.
- Review/privacy: 0 comments, 0 tracked changes, no custom properties or revision IDs; author metadata is retained, Office identity/build comment removed.
- Regression: Phase 4–7 verifiers and Phase 0 source invariant pass. Phase 3 has 20/20 unit tests pass; its legacy text rule rejects required dataset URLs and is superseded by Phase 7/9 link validation.
- Renderer note: the installed `artifact-tool` build collapses native Word table columns even on minimal fixtures. The artifact-tool render was still executed; authoritative visual QA uses Microsoft Word PDF output so editable native tables remain intact.

The machine-readable release decision is in `release_audit.json`.
