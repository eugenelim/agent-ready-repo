# Verification ledger — four-discipline-sequence (S6)

Execution evidence for the build run of 2026-09-11. Recorded here rather than in
the spec, because the spec states outcomes and this records what was observed.

## Membership check (AC-0005, AC-0006)

Run against the output of `make site-build`.

- **Collection multiset:** 20 slugs, read from `web/src/content/journeys/*.md`.
- **Rendered multiset:** 20 slugs, read from `build/journeys/index.html`.
- **Result: equal.** No slug missing, none duplicated.

Group split: 4 in the sequence, 3 in the supervised loops, **13 reaching the
page only through the collection-derived catch-all**.

## D1 — the 19-vs-20 discrepancy, resolved

The prior session's uncommitted sketch reported rendering 19 journeys. **The
collection holds 20, and all 20 render.** The sketch's count was simply wrong;
no journey is excluded, and every file carries a tagline. The construction test
asserts against `readdirSync` of the collection rather than a literal, so a
journey that silently stopped being collected would fail it — a literal `20`
would not.

## D3 — the observing seam, resolved and then confirmed empirically

The plan resolved D3 to "both membership criteria keep the built page, no
fixture needed for the criterion". That rested on a claim that had to be tested
rather than assumed: **that a journey file added to
`web/src/content/journeys/` survives `make site-build`**, which regenerates that
directory from `packs/*/JOURNEY.md`.

**Probed: it survives and renders.** A fixture was added, the site rebuilt, and
the fixture appeared on the page through the catch-all. Had it been wiped, D3's
resolution would have been wrong and AC-0006 would have needed the weaker
unit-level observer with both criteria reworded.

## Mutation proofs

Each mutation was applied to source, the site rebuilt, the suite run, and the
mutation then **restored by editing** — never by `git checkout`, `reset`, or
`stash`.

| Guard | Mutation | Observed |
| --- | --- | --- |
| AC-0003 — order lives in the markup | `<ol>` → `<ul>`, visual order unchanged | **Killed.** AC-0003 failed. 5 sibling cases also failed, because they locate the group by that selector — see the coupling note below |
| AC-0005 — no journey dropped or duplicated | excluded `atlassian` from the catch-all **and** duplicated `core` into the loops | **Killed, and this is the load-bearing proof.** The rendered card count stayed at **20**, so a length-only comparison would have *passed*. The multiset comparison failed. This is the only mutation shape that demonstrates why the criterion is specified on multisets rather than counts |
| AC-0006 — ungrouped journeys still render | catch-all replaced with a hardcoded list of the 13 production slugs, with a **novel** fixture slug present in the collection | **Killed.** The novel slug rendered 0 times. Novelty is load-bearing: a fixture reusing an existing slug would have been in the hardcoded list and the mutant would have passed |

**Coupling note, recorded rather than repaired.** Six of eight cases fail under
the AC-0003 mutation, because they locate the sequence group by
`ol.journeys-grid--ordered` and that selector stops matching. The guard is
killed either way, so the proof holds, but the failure is less specific than it
could be. Locating the group by its heading id would isolate AC-0003. Left as
is: the cases are correct, and changing every selector to make one mutation
tidier is churn, not correctness.

## Cold read (AC-0011)

Run by a fresh agent session given **only** the built page and
`guides/README.md`, explicitly barred from opening anything under `docs/` or any
file named `spec` or `plan`.

- Named the four in order: Desk Research → Product Strategy → Experience Design
  → Product Engineering. **Correct.**
- Quoted each handoff and the end state. **Correct.**
- Answered what stopping after step 2 leaves you holding. **Correct.**
- Confirmed the two surfaces agree on the order.

**AC-0011 passes.** The read also produced one finding, which was fixed rather
than filed: the handoff copy read `Hands on: <artifact>`, which the reader
judged ambiguous — "it says what you have hands on, not what it passes to the
next step". The copy now names the receiving discipline (`Hands Product
Strategy: …`), and the AC-0007 test was strengthened to assert that each of the
first three handoffs names the *next card's own heading*, so the ambiguity
cannot return.

## Gates

| Gate | Result |
| --- | --- |
| `python3 tools/validate_guides.py` | 0 |
| `python3 tools/lint-guide-titles.py` | 0 |
| `python3 tools/check-guide-index.py` | 0 |
| `make site-link-check` | 0 — 73,478 links across 289 pages, clean |
| `npm run test --prefix web` | 19 files, 156 tests passed |
| `python3 -m pytest tools/test_build_site_routing.py` | 94 passed |
| `lint-brief-coverage.py` | 0 |

## Prohibitions (AC-0015 to AC-0018)

- **AC-0015** — no image syntax in either edited surface. Verified by scan.
- **AC-0016** — the only `first value` string in the diff is the structural
  `**First value:**` path label that AC-0009 requires, which the Boundary rail
  explicitly exempts. No adopter-outcome claim.
- **AC-0017** — `git diff -- web/src/content/journeys/` is empty. The mutation
  fixture was added and removed inside the proof and left no trace.
- **AC-0018** — no route-equivalence text; neither plugin route is described on
  either surface.
