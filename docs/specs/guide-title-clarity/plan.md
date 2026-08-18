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
navigation. No route is derived from the new wording. Traces to: AC1-AC10.

### Component / module decomposition

The source Markdown owns page wording, `guide-nav-baseline.toml` owns pinned
sidebar labels, and generated Starlight pages provide the emitted evidence —
including the route set, which no title change may alter. Traces to: AC1-AC10.

### Quality attributes (NFRs)

The four titles remain understandable in a five-second scan and introduce no
Major design finding against the approved directions. Traces to: AC11.

## Tasks

### T1: Title contract tests pin four changes and five controls

**Depends on:** none

**Touches:** tools/test_build_site_sidebar.py

**Tests:**
- TDD (`stub: true`): the four approved strings are the frontmatter `title:` of
  their four source files, compared EXACT and UN-NORMALISED — casing and
  punctuation preserved, YAML quoting not pinned (AC1-AC4).
- TDD (`stub: true`): each approved frontmatter title equals its body `# ` H1
  (AC5).
- TDD (`stub: true`): the five enumerated control titles are unchanged (AC7).
- TDD (`stub: true`): the four retired strings are absent from the four source
  files — and only those four files, since the strings legitimately persist as
  provenance elsewhere (AC8).
- TDD (`stub: true`): the sidebar ITEM label for all FOUR retitled pages equals
  the approved string, and the two de-baselined pages have no baseline entry
  backing that (AC6). All four, not just the de-baselined two: the other two
  never had a baseline entry, so nothing else in the module reaches them and a
  baseline entry pinning a retired label to either would regress the emitted
  sidebar silently.
- TDD (`stub: true`): no projected sidebar label anywhere in the real guide tree
  is one of the retired strings — tree-wide, not path-scoped, because a retired
  label reaching any item is the regression whichever page it lands on (AC6,
  AC8).
- TDD (`stub: true`): the pack index's link TEXT for the three retitled guides
  names the approved string (AC9). Nothing else in the repo compares Markdown
  link text against anything — `check-rendered-site-links.py` validates targets
  only — so without this, reverting a label fails nothing.

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
- Compare EXACT, UN-NORMALISED strings, not through
  `tools/lint-guide-titles.py`'s `normalise()`: that helper casefolds and strips
  punctuation, and three of the four decisions are substantially casing changes,
  so a normalised comparison would accept `Run A Frontend Audit`.
  Un-normalised is not the same as raw. Titles are read through
  `build_site._parse_frontmatter`, the parser the generator itself uses, so
  requoting `title: Run a frontend audit` as `title: "Run a frontend audit"`
  passes: the wording is the subject, the YAML quoting is not. An earlier
  revision took the raw right-hand side and would have failed on that requoting
  — `guide-metadata-completion` rewrites 125 guide frontmatter rows next, which
  is exactly when it would have misfired. `lint-guide-titles.py` keeps its existing job — the
  relational title↔H1 invariant — and gains no content registry, which would be a
  second unsynced source of truth against the frontmatter itself.
- The nine pinned strings exist in two places on purpose: the spec's acceptance
  criteria, which is what was approved, and `APPROVED_TITLES` / `CONTROL_TITLES`
  in the test, which is what fails when the tree drifts. A test that read the
  strings out of the spec would pass whenever both moved together, which is the
  drift worth catching. The two must be edited as a pair — the AC text and the
  dict are the same decision written twice, deliberately.
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
- Goal-based (`no stub (mode)`): run the title linter and T1's focused tests
  (AC1-AC9). T1 is what makes this a real gate rather than a one-time command —
  it pins the nine strings, the four retired strings, the two de-baselined
  labels, and the three pack-index link labels, and each was proven to fail on a
  seeded reversion.
- Superseded by T1: an earlier revision planned a `! grep -q` sweep for the
  retired strings here. `test_retired_title_strings_absent_from_the_four_sources`
  does that durably instead, over the same four paths and for the same reason —
  the retired wording legitimately persists as provenance elsewhere, enumerated
  once in AC8 rather than restated here (AC8).

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
- Leave the `IaC (Terraform)` sidebar GROUP label alone. It is pack identity from
  `packs/iac-terraform/pack.toml`'s `display_name`, mirrored to `site.toml` and
  `docs-site/src/sidebar-config.json`, and also rendered in the marketing
  catalogue and pack cards. AC6 scopes this spec to the ITEM label;
  `notes/render-review.md` records the resulting
  `IaC (Terraform) › Terraform and OpenTofu guides` reading and the deferral to
  `[backlog].open` as `iac-terraform-group-label-alignment`.

**Done when:** all source and navigation title contracts pass.

### T3: Emitted titles and routes remain coherent

**Depends on:** T2

**Touches:** docs/specs/guide-title-clarity/notes/route-baseline.txt (evidence only),
docs/specs/guide-title-clarity/notes/render-review.md (evidence only)

**Shipping metadata, owned by no single task above:** `docs/product/changelog.md`
(the release note this change owes its adopters), `docs/specs/README.md` (the
status row and AC count), and `workspace.toml` (the queue-to-shipped move plus the
`iac-terraform-group-label-alignment` deferral). Named here so a reviewer does not
have to infer why they appear in the diff.

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

- 2026-08-17 (third revision): renumbered every citation in this file against the
  explicit **AC1**-**AC11** labels the spec now carries. The two ACs added at
  spec-stage review shifted the rest by two, and this Changelog block was written
  under the old 8-AC numbering — the entry below is restated with the current
  numbers. Also implemented plan task T1, which the previous revision declared and
  did not ship.
- 2026-08-17: corrected at spec-stage review, before any code. AC11 arbitrated
  against the MARKETING site's "Precision authority" though all four pages render
  only on docs-site, whose direction is "Instrument-grade clarity" — and the brief
  bars aligning the two surfaces. AC7's "the five reviewed titles" and the four
  retired strings were recorded nowhere and recoverable only by git archaeology;
  both are now enumerated in the spec. AC6's sidebar half would have been
  tautological: relabelling a baseline entry passes a guard that loads the same
  file, so the entries are DELETED instead, which is what guides/AGENTS.md
  documents. AC6 is also scoped to the sidebar ITEM label, with the
  `IaC (Terraform)` GROUP label recorded as deliberately unchanged — it is pack
  identity from packs/iac-terraform/pack.toml and outside the approved four
  strings. Added an AC for the pack index's stale link text (AC9), a route
  baseline artifact for AC10, the mandated build order and approved widths for T3,
  raw-string comparison (not `normalise()`, which would accept a wrong casing),
  and the correct test homes. Scope unchanged: the four frozen strings and five
  controls are untouched.
- 2026-08-17: initial plan derived from the approved tech-site completion brief.
