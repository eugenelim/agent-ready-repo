# Verification ledger: install-to-ship-walkthrough

Execution observations for this spec. `spec.md` and `plan.md` are pinned in
substance from plan approval; everything produced by running the work lands here
(`docs/CONVENTIONS.md` § *A spec directory freezes as a unit, when the spec
ships*).

## Pre-approval spike — 2026-09-08

Purpose: retire the anchor-survival mechanism the entry links depend on, and
capture the accepted-base route set for AC12.

| Command | Exit | Result |
| --- | --- | --- |
| `npm ci --prefix web` | 0 | `web/node_modules` restored |
| `npm ci --prefix docs-site` | 0 | `docs-site/node_modules` restored |
| `python3 tools/build-site.py` | 0 | guides and pack pages generated into `docs-site/src/content/docs/` |
| `npm run build --prefix web` | 0 | marketing site emitted; repository `build/` cleaned first |
| `npm run build --prefix docs-site` | 0 | documentation site emitted into `build/docs/` |

Observations:

- Observed heading/id pairs in `build/docs/guides/index.html`:

  | Authored heading | Emitted id |
  | --- | --- |
  | `## Follow a path` | `follow-a-path` |
  | `### P1 · Adopt the catalogue — ~1 hour` | `p1--adopt-the-catalogue--1-hour` |
  | `### P4 · Decide together — ~1.5 hours` | `p4--decide-together--15-hours` |

  No general transformation rule is inferred from these. The doubled hyphens and
  the `1.5` → `15` collapse show the obvious "collapse non-alphanumeric runs to
  one hyphen" rule is wrong, so AC11's required id is an expectation confirmed
  against the built site at T5, not a derivation.
- 288 HTML files emitted under `build/`. The route list itself is the baseline;
  the count alone cannot detect one route swapped for another.

### `route-baseline.txt` provenance

`route-baseline.txt` holds those 288 routes, one per line, sorted, with no
header or comment lines — it is a plain set so a comparison needs no parser and
cannot disagree with one. It was produced from the build recorded above by
listing every emitted `*.html` path relative to `build/`. AC12 requires the
post-change emitted set to contain every line in it. Regenerate it only when a
route is deliberately retired through the route-change decision in `spec.md`
§ Boundaries — never to make a failing comparison pass.
- No authored page links to `#follow-a-path`. The emitted page's references are
  Starlight's own on-this-page navigation and heading permalink, both generated
  from the heading.

The spike tree was not committed; `.gitignore:66` ignores `build/`.

## Execution — 2026-09-09

T1 was discharged by the pre-approval spike above. T2–T4 were implemented by a
scoped Codex worker under a four-file allowlist; T5 is recorded here.

### Gates

| Command | Exit | Result |
| --- | --- | --- |
| `python3 tools/build-site.py` | 0 | generated |
| `npm run build --prefix web` | 0 | 50 pages |
| `npm run build --prefix docs-site` | 0 | 238 pages |
| `npm test --prefix web` | 0 | 145 passed across 18 files |
| `python3 -m pytest` over the 7 touched `tools/` suites | 0 | 170 passed |
| `make site-link-check` | 0 | 73,075 links across 288 pages, clean |
| `npm run test:e2e:gate --prefix web` | 0 | 182 passed |
| `git diff --check` | 0 | no whitespace errors |

The 13 walkthrough cases were confirmed **executed, not skipped**: a filtered run
reported `13 passed | 132 skipped`. The suite is
`describe.skipIf(!docsBuilt || !webBuilt)`, so a green run without that
confirmation would prove nothing.

### AC12 — route preservation

`comm -23 route-baseline.txt <emitted routes>` returned **0 lost routes**.
Baseline 288, after 288, none added.

### Mutation proofs

| Invariant | Mutation | Expected | Observed |
| --- | --- | --- | --- |
| AC6 binds successor text and target on one anchor | `Next: [P3 · Build it](#p3…)` → `[continue here](#p3…)` | AC6 fails | AC6 failed |
| AC14 keeps all four branch step links | deleted the `Build an org stack pack` step | AC14 fails | **passed first**, then failed after the fix below |

AC14's first result was a control that could not fail: Starlight renders a full
sidebar of guide links on every page, so a document-wide `href` scan was
satisfied by navigation chrome. A `sectionNodes()` helper now scopes AC7 and
AC14 to the branch section's own nodes, after which the mutation killed the
test. Both mutations were reverted by editing, never by `git checkout`.

### Adjacent defect found and fixed

`tools/test_documentation_entry_links.py::_slugify` collapsed each whitespace
run to a single hyphen, deriving `#p2-shape-what-to-build-3-hours` for
`### P2 · Shape what to build — ~3 hours`. Starlight's github-slugger drops the
punctuation and keeps the spaces that surrounded it, emitting
`id="p2--shape-what-to-build--3-hours"` — verified in
`build/docs/guides/index.html`. The suite's rule disagreed with the consuming
renderer and failed the new successor links. `_slugify` now emits one hyphen per
whitespace character. Reverting that single character reproduces the failure,
which is the proof the corrected rule is load-bearing.

### Flake, recorded rather than laundered

The first browser-gate run reported `1 failed / 181 passed`:
`quality-assertions.spec.ts › skip link ordering › skip link first passes`, with
`Test timeout of 30000ms exceeded while setting up "page"` — a fixture setup
timeout, not an assertion, on a route this slice does not touch. The same
contention produced `[vitest-pool] Timeout waiting for worker to respond` in an
earlier vitest run. Re-run in isolation: 2 passed. Full gate re-run: **182
passed, exit 0**.
