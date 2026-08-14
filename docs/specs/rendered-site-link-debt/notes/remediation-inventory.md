# Rendered-link remediation inventory

Verified on 2026-08-13 against the combined marketing and technical-docs
output in `build/`.

## Baseline reconciliation

The predecessor verification record reported 67 failures among 53,871
internal links across 263 pages. To make the drift comparison reproducible, the
recorded snapshot (`86764882391dd5c1aba60f1f0b21603c1cdabfa9`) was rebuilt in
an approved temporary directory and scanned with the new canonical checker.

| Crawl | Pages | Internal links | Broken targets |
| --- | ---: | ---: | ---: |
| Recorded predecessor crawl | 263 | 53,871 | 67 |
| Rebuilt recorded snapshot, canonical checker | 263 | 53,894 | 80 |
| Current pre-remediation build, canonical checker | 263 | 53,944 | 80 |
| Current remediated build, canonical checker | 263 | 53,887 | 0 |

The 13 additional failures in the canonical-checker replay are all links on
`primitives-fixture/index.html`, a generated page outside the predecessor
crawl's reported failure corpus. The remaining 67 are the recorded corpus.
The 23-link difference on the same historical output is therefore a crawler
scope/counting difference, not repository drift.

Using the same canonical checker on both repository snapshots produces the
same 80 source/href/target diagnostics: no failure was added, removed, or
retargeted between the recorded snapshot and the current pre-remediation
build. The current build contains 50 additional valid internal links. This
accounts separately for corpus drift and checker-scope drift instead of
forcing the historical count.

## Failure ownership and disposition

| Count | Class | Authored owner | Disposition |
| ---: | --- | --- | --- |
| 60 | Legacy guide links escaped one directory above the repository, so the guide projector could not turn repository-source links into GitHub URLs | 27 Markdown files under `guides/` | Remove one erroneous `../` segment at each authored link; projection now emits valid GitHub source URLs. |
| 3 | Root-relative guide routes omitted the configured Pages and docs bases | `guides/core/explanation/digital-experience-contract.md` | Use source-relative guide links; the projector emits base-qualified technical-doc routes. |
| 4 | Sibling pack-home links were emitted beneath the current pack route | `tools/build-site.py` | Emit `/agent-ready-repo/docs/packs/<slug>/`; pin the projection with a focused construction test. |
| 13 | Component-fixture actions and tabs referenced placeholder pages or absent fragments | `web/src/pages/primitives-fixture.astro` | Point actions to real emitted routes or meaningful fixture sections and add the corresponding section IDs. |

Three stale `README.md#install` occurrences in two guides are included in the
60-link class.
Because the current README no longer owns an Install fragment, their authored
targets now point to the published install page or the same guide's zipapp
fallback section. No allowlist, subtree exclusion, fragment bypass, or
generated-output-only edit was used.

## Closure proof

- `make site-build` completed the marketing build first and the technical-docs
  build second, producing 263 HTML pages in the combined tree.
- `python3 tools/check-rendered-site-links.py --build-dir build` exited 0 with
  `rendered-site-links: 53887 links across 263 pages; clean`.
- `python3 tools/test_build_site_link_rewrites.py` passed, including the new
  sibling pack-home projection case.
- `python3 tools/test_check_rendered_site_links.py` passed.
