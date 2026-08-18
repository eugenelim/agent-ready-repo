# Plan: Guide title clarity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Pin the four approved strings and the five no-change controls in the existing
title-lint surface, update source headings and applicable navigation labels,
then build both sites and inspect the emitted title surfaces. Metadata absent
from these pages remains the responsibility of the dependent metadata spec.

## Constraints

- Follow `docs/design/principles/tech-site.md` and the existing platform
  aesthetic direction.
- Preserve paths, slugs, aliases, and link targets.
- Keep the change limited to the nine reviewed title decisions.

## Construction tests

**Integration tests:** full site generation, both Astro builds, title lint, and
combined rendered-link checking.

**Manual verification:** inspect the four emitted pages in navigation and
search/title contexts against the precision-authority design goal.

## Design (LLD)

### Design decisions

The source H1 is the canonical fallback title until metadata is present.
Navigation labels match the approved title where the page participates in
navigation. No route is derived from the new wording. Traces to: AC1-AC9.

### Component / module decomposition

The source Markdown owns page wording, `guide-nav-baseline.toml` owns pinned
sidebar labels, and generated Starlight pages provide the emitted evidence.
Traces to: AC1-AC9.

### Quality attributes (NFRs)

The four titles remain understandable in a five-second scan and introduce no
Major design finding against the approved directions. Traces to: AC11.

## Tasks

### T1: Title contract tests pin four changes and five controls

**Depends on:** none

**Touches:** tools/test_build_site_sidebar.py

**Tests:**
- TDD (`stub: true`): the four approved strings are the frontmatter `title:` of
  their four source files, compared as RAW strings (AC1-AC4).
- TDD (`stub: true`): each approved frontmatter title equals its body `# ` H1
  (AC5).
- TDD (`stub: true`): the five enumerated control titles are unchanged (AC7).
- TDD (`stub: true`): the four retired strings are absent from the four source
  files — and only those four files, since the strings legitimately persist as
  provenance elsewhere (AC8).
- TDD (`stub: true`): the sidebar item label for the two de-baselined pages
  resolves from the frontmatter title (AC6).

Shipped as five tests appended to `tools/test_build_site_sidebar.py`, over the
constants `APPROVED_TITLES`, `CONTROL_TITLES`, `DEBASELINED_SLUGS`, and
`RETIRED_STRINGS`. `tools/test_lint_guide_titles.py` is NOT touched: it is
already required CI and already owns the relational title↔H1 invariant, and the
`Touches:` line above previously named it on the mistaken assumption that the
control-title pins belonged beside its fixtures.

Falsification, run against the working tree and reverted (three reversions, all
caught): reverting one approved frontmatter title → 4 failures; reverting one
control title → 1 failure; restoring a deleted `guide-nav-baseline.toml` entry
for a de-baselined slug → 1 failure. An earlier draft of `CONTROL_TITLES`
guessed the five strings from memory and the suite caught it, which is the
behaviour these tests exist to provide.

**Approach:**
- Compare RAW strings, not through `tools/lint-guide-titles.py`'s `normalise()`:
  that helper casefolds and strips punctuation, and three of the four decisions
  are substantially casing changes, so a normalised comparison would accept
  `Run A Frontend Audit`. `lint-guide-titles.py` keeps its existing job — the
  relational title↔H1 invariant — and gains no content registry, which would be a
  second unsynced source of truth against the frontmatter itself.
- The nine pinned strings live in the spec's acceptance criteria; the tests
  reference that enumeration rather than restating it a second time.
- Navigation assertions go in `tools/test_build_site_sidebar.py`, which already
  makes real-tree sidebar assertions. NOT `tools/test_lint_guide_titles.py`: its
  own docstring declares it deliberately not a pytest module, with `_run_*` entry
  points pytest cannot collect.

**Done when:** the focused tests fail on the old four strings and protect the
five controls — demonstrated by the reverted-mutation runs recorded above, not
by the suite merely passing.

### T2: Source and navigation use the approved titles

**Depends on:** T1

**Touches:** guides/frontend-engineering/how-to/page-screen-contract.md, guides/frontend-engineering/how-to/run-an-audit.md, guides/frontend-engineering/tutorials/scaffold-a-component.md, guides/iac-terraform/README.md, guides/frontend-engineering/README.md, guide-nav-baseline.toml

**Tests:**
- Goal-based (`no stub (mode)`): run the title linter and the focused tests
  (AC1-AC8).
- Goal-based (`no stub (mode)`): `! grep -q` each retired string over exactly the
  four source paths — `! grep -q`, because `grep -c` exits 1 on no-match and CI
  would read success as failure. Path-scoped, because the retired strings
  legitimately persist as provenance in the changelogs, `workspace.toml`, and the
  lint fixtures (AC1-AC4).

**Approach:**
- Change each frontmatter `title:` and its body H1 together — a CI gate asserts
  they match, so moving one alone fails.
- DELETE the two `guide-nav-baseline.toml` entries that froze
  `Scaffold a Component` and `Run an Audit` rather than relabelling them. Both
  pages carry `title:`, and `guides/AGENTS.md` documents deletion as the
  deliberate act; relabelling would make the pair guard tautological.
  `page-screen-contract` and `iac-terraform/README` have no baseline entry, so
  nothing to remove there. Add no navigation entries.
- Update the three stale link labels in `guides/frontend-engineering/README.md` (AC9).
- Leave `site.toml`'s `IaC (Terraform)` group label alone (AC5 records why).

**Done when:** all source and navigation title contracts pass.

### T3: Emitted titles and routes remain coherent

**Depends on:** T2

**Touches:** docs/specs/guide-title-clarity/notes/route-baseline.txt (evidence only)

**Tests:**
- Goal-based (`no stub (mode)`): build in the mandated order — `tools/build-site.py`,
  then `npm run build --prefix web`, then `npm run build --prefix docs-site` — and
  assert the four emitted `<h1>` and `<title>` surfaces from the built HTML. These
  read files directly and launch NO browser (AC5).
- Goal-based (`no stub (mode)`): diff the emitted route set against the pre-change
  inventory captured in `notes/route-baseline.txt`, compared as MEMBERSHIP not
  count (a rename preserves a count), then run
  `tools/check-rendered-site-links.py --build-dir build` (AC10).
- Manual QA (`no stub (mode)`): a human reviewer reads the four titles in
  navigation and in the browser/search title at the brief's approved widths — 360,
  375, 390, 414, 1440 — in both docs themes, and records the observation and its
  severity in `notes/render-review.md`. The invariant: each title names the
  reader's job and is not truncated in the sidebar at the narrowest width (AC11).

**Approach:**
- Use emitted HTML as evidence rather than source-only assertions.
- Capture the route baseline BEFORE any edit; a post-change count cannot detect a
  rename.
- The manual pass runs in the real user environment with `HOME` intact. Playwright's
  Chromium resolves from `~/Library/Caches/ms-playwright`, so a fixture given a
  synthetic `HOME` loses the browser and reports passes without launching one — the
  emitted-title assertions above deliberately need no browser at all.
- Record screenshots only as temporary review evidence, never tracked output.

**Done when:** all four titles are correct in emitted behavior and every route
still resolves.

## Rollout

This is a content-only change on existing routes. Reversion restores the old
strings without migration; no alias or redirect changes.

## Risks

- A baseline label may drift from the source title.
- The later metadata backfill could reintroduce an old title unless it consumes
  this spec's approved strings.
- A route accidentally derived from title wording would break inbound links.

## Changelog

- 2026-08-17: corrected at spec-stage review, before any code. AC8 arbitrated
  against the MARKETING site's "Precision authority" though all four pages render
  only on docs-site, whose direction is "Instrument-grade clarity" — and the brief
  bars aligning the two surfaces. AC6's "the five reviewed titles" and the four
  retired strings were recorded nowhere and recoverable only by git archaeology;
  both are now enumerated in the spec. AC5's sidebar half would have been
  tautological: relabelling a baseline entry passes a guard that loads the same
  file, so the entries are DELETED instead, which is what guides/AGENTS.md
  documents. AC5 is also scoped to the sidebar ITEM label, with site.toml's
  `IaC (Terraform)` GROUP label recorded as deliberately unchanged — changing a
  declared guide group is Ask-first and outside the approved four strings. Added an
  AC for the pack index's stale link text, a route baseline artifact for AC7, the
  mandated build order and approved widths for T3, raw-string comparison (not
  `normalise()`, which would accept a wrong casing), and the correct test homes.
  Scope unchanged: the four frozen strings and five controls are untouched.
- 2026-08-17: initial plan derived from the approved tech-site completion brief.
