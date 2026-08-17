# Plan: guide-typed-asides-conversion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as we learn. When it changes substantially,
> the changelog records why.

## Approach

Enumerate the complete legacy blockquote cohort into a reviewable
classification ledger before changing guide content. Review each block in its
surrounding section, record `quotation|note|tip|caution|danger` plus a
rationale, and leave ambiguity visible as `failed` rather than guessing.
Once the ledger has no pending or failed rows, add the emitted-output
construction checks, convert only the classified non-quotations in bounded
guide cohorts, and update the existing authoring-standard reference. Finish
with the cache-cleared full build, whole-site rendered scan, and representative
light/dark browser inspection.

## Assumption trio

**Files I'll touch**

- `guides/**/*.md` files that contain ledger-classified non-quotation
  blockquotes, without renaming or moving them.
- `guides/_shared/reference/catalogue-authoring-standards.md` for the durable
  quotation-versus-aside rule.
- `docs/specs/guide-typed-asides-conversion/notes/blockquote-classification.jsonl`
  for the exhaustive review ledger.
- `web/src/test/rendered-output.test.ts` and
  `web/src/test/e2e/docs-asides.spec.ts` for emitted HTML and browser
  construction checks.
- `tools/test_guide_typed_asides.py` for classification-ledger,
  authoring-standard, package-projection, and release-handoff contract checks.
- `packages/agentbundle/agentbundle/_data/catalogue-scaffold/` plus
  `packages/agentbundle/{pyproject.toml,CHANGELOG.md,README-pypi.md}` and
  `packages/agentbundle/agentbundle/version.py` for the synchronized
  scaffold projection and AgentBundle patch-release metadata.
- `docs/product/changelog.md`, `docs/specs/README.md`, and this spec directory
  for release-handoff records; `workspace.toml` stays unchanged until
  publication-time closeout.

**What demonstrates done**

A terminal classification ledger satisfying AC1 and a cache-cleared full build
feed a 60-second built-output scan that resolves every row to its emitted
semantic container. The dedicated Playwright journey inspects a recovery page
and an exact-wording page at desktop and 375 px in both themes, emits
screenshots, and runs axe. The pure-stdlib contract test proves the authoring
standard, bundled scaffold, package release metadata, and release handoff.
Guide schema/index/title checks, rendered and authored link checks, contrast,
repository policy gates, and `git diff --check` complete the proof.

**What I am not changing**

Guide paths, routes, titles, frontmatter, legacy guide body prose beyond the
minimum aside delimiter/title edits, links, sidebar order, pagination,
breadcrumbs, `site.toml`, `guide-nav-baseline.toml`,
`tools/build-site.py`, docs CSS/palette, Starlight configuration,
dependencies, AgentBundle CLI behavior, `web/` production code, or
already-shipped site work. The required authoring-standard rule and examples
are the sole prose addition.

## Declined patterns

- **Global blockquote-to-aside rewrite.** Syntax cannot decide quotation
  semantics or severity; the ledger makes every judgment reviewable first.
- **Custom `warning`, `info`, or branded types.** Starlight's four fixed
  types are the approved interface.
- **Aside component or CSS restyle.** The pinned Starlight rendering and
  docs-specific palette already supply the semantic treatment.
- **Permanent conversion CLI or new parser dependency.** Enumeration is a
  one-time stdlib aid; the durable proof belongs in existing tests.
- **Wait for `site-design-principles`.** The registered decision and grounded
  docs aesthetic direction settle this surface.
- **Rewrite nearby guide prose while touching wrappers.** Content improvement
  would obscure the classification diff and requires separate scope.

## Constraints

- `workspace.toml [backlog].open` owns the historical problem, fix, scope, and
  prior decisions; this plan does not restate that brief.
- `docs-site-design-refresh`, its aesthetic direction, and
  `docs-site/AGENTS.md` govern the palette, accessibility floor, pinned
  Starlight contract, cache reset, and build order.
- `guides/AGENTS.md` governs public-guide ownership, frontmatter, routes,
  navigation, and title lint.
- `tools/catalogue/sync_authoring_scaffold.py` projects the authoring standard
  into AgentBundle package data and rewrites its digest manifest. Package Gate G
  therefore requires a patch bump; after rebasing onto AgentBundle `0.37.0`,
  this change uses `0.37.1`, matching
  `version.py`/`pyproject.toml`, a package changelog entry, a current
  `README-pypi.md`, and an `Engine-Change-RFC: ADR-0056` commit trailer. The
  trailer is a handoff requirement because this enterprise session cannot write
  commits or refs.
- Starlight 0.41.4 accepts only `note`, `tip`, `caution`, and `danger`
  Markdown asides. No dependency or renderer change is needed.
- No reference-architecture document exists; the established
  Markdown → `tools/build-site.py` → Astro/Starlight → `build/docs` stack is
  the implementation frame.
- No external review reference name appears in tracked content or Git
  artifacts.

## Construction tests

**Pure-stdlib contract test:** add `tools/test_guide_typed_asides.py`. Its T1
ledger cases read the AC1 baseline and fail on duplicate identities, missing
baseline coverage, `pending`/`failed` rows, missing rationales, malformed
content hashes, or classifications outside
`quotation|note|tip|caution|danger`. These ledger-only cases pass before any
wrapper conversion. T3 adds source-classification cases: for `quotation`, the
current Markdown content hash must equal the baseline hash; for a typed row,
the current aside body hash must equal the baseline hash and its fence type
must equal the ledger classification.

Its authoring-standard cases require the quotation definition, typed-aside
default, four canonical type names with their selection meanings, and examples
in both the canonical guide and byte-identical bundled scaffold copy. Its
release-handoff cases require matching package versions, the package
changelog and PyPI-description update, current spec-index status/AC count, the
product changelog entry, and native-TOML confirmation that `[backlog].open`
still contains this slug until publication-time closeout.

**Built-output integration:** extend
`web/src/test/rendered-output.test.ts` to read the ledger, reuse the guide
frontmatter/slug mapping, and resolve every record against `build/docs`.
For each `quotation` row its unique anchor must occur in one `<blockquote>`
outside an aside. For each typed row the anchor must occur in one
`aside.starlight-aside--<classification>`. A guide-only whole-site scan also
asserts one allowed type class, non-empty `.starlight-aside__title`, and one
`.starlight-aside__icon` for every emitted aside, with no untracked
blockquote or source/built count drift. These tests use the existing
`SCAN_TIMEOUT_MS = 60_000`.

**Browser integration:** add `web/src/test/e2e/docs-asides.spec.ts`. In
`light` and `dark`, it opens
`/agent-ready-repo/docs/guides/core/tutorials/start-a-new-project/` and
`/agent-ready-repo/docs/guides/product-documentation/how-to/author-product-docs/`
at 1440×900 and 375×812. It asserts the ledger-selected recovery aside exposes
its expected type class, visible title and icon, and a background/border
distinct from the page; the exact-wording example remains a blockquote and is
not inside an aside; body overflow is at most one pixel; and axe reports zero
serious or critical violations. It writes one screenshot per route/theme at
desktop for direct visual inspection.

## Acceptance commands

Install the two exact lockfile dependency trees only when absent:

```bash
npm ci --prefix web
npm ci --prefix docs-site
```

Run every acceptance command separately, in order, and read its exit code. The
first command is the required cache reset.

```bash
rm -rf docs-site/.astro docs-site/node_modules/.astro
python3 tools/catalogue/sync_authoring_scaffold.py --write
python3 tools/catalogue/sync_authoring_scaffold.py --check
python3 -m pytest tools/test_guide_typed_asides.py tools/test_scaffold_projection.py -q -p no:cacheprovider
python3 -m pytest packages/agentbundle/tests/integration/test_scaffold_projection.py -q -p no:cacheprovider
python3 tools/build-site.py
npm run build --prefix web
npm run build --prefix docs-site
npm test --prefix web
npm exec --prefix web -- playwright test --config web/playwright.config.ts docs-asides.spec.ts
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 tools/check-rendered-site-links.py --build-dir build
python3 tools/test_documentation_entry_links.py
python3 tools/check-docs-contrast.py
python3 tools/lint-agents-md.py
make build-check
git diff --check
```

After Playwright exits zero, inspect its four desktop route/theme screenshots
directly and record whether quotation, label, icon, tint, border, and surrounding
reading rhythm match the acceptance criteria.

## Design (LLD)

### Design decisions

- **Quotation boundary:** retain `>` only when the block reproduces an
  attributed quotation, user/system utterance, sample transcript/output, or
  exact wording whose quoted form is part of the example. A block that cannot
  answer “whose exact words/content are these?” is emphasis, not quotation.
  Traces to AC2, AC4.
- **Type selection:** `note` = context/scope; `tip` = optional improvement;
  `caution` = pitfall/limitation/recovery/reversible risk; `danger` =
  severe or irreversible harm. Traces to AC3–AC5.
- **Review ledger:** one JSON object per original block records
  `item`, `path`, `line`, `content_sha256`, `anchor`,
  `classification`, `status`, and `reason`. Content identity, not line
  number, survives wrapper edits. Traces to AC1, AC8.
- **Documentation contract:** revise the existing external-user reference page.
  The reader is a catalogue guide author deciding how to format secondary
  content; the result is one lookup rule and the four allowed types, with no
  new page, route, or journey. Canonical sources are Starlight's authoring
  contract, `guides/AGENTS.md`, and the rendered guide behavior. Traces to AC5.
- **Scaffold release coupling:** the canonical reference also ships through
  AgentBundle's catalogue scaffold, so the synchronized package-data copy and
  a patch release are part of this change rather than deferred drift. Traces to
  AC6.

### Component / module decomposition

`guides/**/*.md` remains the canonical content layer.
`tools/build-site.py` continues to mirror it without changes.
Starlight 0.41.4 parses `:::` fences into semantic aside markup.
`rendered-output.test.ts` owns the whole-site emitted contract, while the
dedicated Playwright journey owns theme, responsive, accessibility, and visual
evidence. The scaffold synchronizer owns the canonical-guide → package-data
copy and digest manifest. Traces to AC2–AC11.

### State & control flow

The classification pass enumerates all baseline blocks as `pending`. Reading
the complete surrounding section changes each row once to `done` with a
classification and rationale, or to `failed` with the ambiguity. Conversion
does not start while any row is pending or failed. A converted row is verified
first against current Markdown and then against its emitted page. Traces to
AC1–AC3, AC8.

### Behavior & rules

- Quotation status outranks visual prominence: exact words remain blockquotes
  even when a callout would be more visually prominent.
- Severity follows consequence, not tone. `danger` is not a stronger
  `caution`; it requires severe or irreversible harm.
- Wrapper conversion preserves content bytes after removing only blockquote
  prefixes and adding the aside delimiters/title.
- Existing typed asides remain valid if they use the fixed vocabulary; they do
  not need reclassification unless the ledger exposes a direct conflict.
- Authoring-standard examples use generic placeholders and name no external
  review reference.

Traces to AC2–AC5.

### Quality attributes (NFRs)

- **Reviewability:** every AC1 ledger decision is explicit and conversions land
  in bounded diff cohorts, with no hidden auto-classification.
- **Accessibility:** semantic labels/icons, hue-independent titles, zero
  serious/critical axe findings, and existing docs contrast gate. Traces to
  AC3, AC9–AC11.
- **Stability:** no route, navigation, frontmatter, palette, renderer, or
  dependency change. Traces to AC7.
- **Reproducibility:** cache-cleared canonical build and 60-second whole-site
  scan operate on emitted HTML. Traces to AC8, AC10, AC11.

## Tasks

### T1: Every legacy blockquote has a terminal, reviewable classification

**Depends on:** none

**Touches:** docs/specs/guide-typed-asides-conversion/notes/blockquote-classification.jsonl, tools/test_guide_typed_asides.py

**Tests:**

- Add the ledger-only pure-stdlib cases described in Construction tests, then
  enumerate the exact AC1 baseline with unique content identities and source
  anchors. These schema, coverage, and terminal-classification cases pass
  before wrapper conversion (AC1, AC4).
- Require zero duplicate, pending, or failed rows; sample each classification
  cohort against its complete surrounding section before conversion.

**Approach:**

- Use a throwaway pure-stdlib enumerator in approved temporary space to create
  the resumable baseline, then review each item and persist the audit result.
- Mark ambiguity `failed` and surface it; do not infer from keywords alone.

**Done when:** every AC1 baseline row is done, none is pending or failed, and
every row carries a classification and rationale.

### T2: Emitted-output regressions fail before guide conversion

**Depends on:** T1

**Touches:** web/src/test/rendered-output.test.ts, web/src/test/e2e/docs-asides.spec.ts

**Tests:**

- No stub (goal-based integration + browser QA). Add the exact ledger-to-built
  selectors, allowed-type/title/icon whole-site scan, representative
  route/theme assertions, screenshots, overflow check, and axe check described
  in Construction tests (AC2, AC3, AC8, AC9).
- Run against the unconverted source and record the expected failure: at least
  one ledger-classified callout still resolves to a blockquote (AC3).

**Approach:**

- Reuse the existing JSDOM walk, guide slug handling, and 60-second scan budget.
- Reuse the existing Playwright theme and axe helpers without changing global
  configuration.

**Done when:** the new tests compile and fail specifically because classified
callouts have not yet become typed emitted asides.

### T3: Classified callouts render as typed asides and quotations stay intact

**Depends on:** T1, T2

**Touches:** guides/**/*.md, guides/_shared/reference/catalogue-authoring-standards.md, packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md, packages/agentbundle/agentbundle/_data/catalogue-scaffold/manifest.json, packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md, packages/agentbundle/README-pypi.md

**Tests:**

- Add the pure-stdlib source-classification cases for quotation hashes and
  typed aside body/fence matches. Convert in bounded classification cohorts
  and run the ledger integrity check plus targeted built-output assertion after
  each cohort (AC1–AC5, AC8).
- Add and run the pure-stdlib authoring-standard contract cases to require the
  quotation rule, typed-aside default, fixed four-type table, and examples;
  run scaffold `--write` then `--check`, both scaffold projection tests, and
  package version/changelog/PyPI-description assertions (AC5, AC6).
- Run `tools/validate_guides.py`, `tools/check-guide-index.py`, and
  `tools/lint-guide-titles.py` to prove frontmatter/title/index contracts
  remain valid (AC7, AC10).
- Compare pre/post route, title, frontmatter, sidebar, pagination, and breadcrumb
  inventories through the existing rendered-output checks (AC7).

**Approach:**

- Apply only delimiter/title edits for ledger rows classified as typed asides.
- Leave `quotation` rows byte-identical and add the concise rule/type lookup
  to the existing authoring-standard reference.
- Synchronize the canonical standard into package data, bump AgentBundle
  to the Constraints-selected patch version, and update its changelog and PyPI
  description without changing CLI behavior.

**Done when:** ledger/source checks, authoring-standard checks, scaffold
projection checks, package release checks, and all emitted classification
assertions pass, with the guide identity inventory unchanged.

### T4: The cache-cleared published site passes its complete reader-facing gate

**Depends on:** T3

**Touches:** docs/product/changelog.md, docs/specs/README.md, docs/specs/guide-typed-asides-conversion/spec.md, docs/specs/guide-typed-asides-conversion/plan.md

**Tests:**

- Run the complete acceptance-command block in order and read every exit code;
  the full build starts only after both Astro cache directories are removed
  (AC1–AC12).
- Inspect the four desktop route/theme screenshots and record the visible
  quotation versus label/icon/tint treatment; confirm the mobile and axe
  assertions from the same journey (AC9).
- Add the pure-stdlib release-handoff case. It fails unless the product
  changelog, spec index status/AC count, package release metadata, and
  native-TOML presence of the still-open backlog entry agree (AC12).
- Confirm no tracked file or Git artifact names the external review reference,
  and `git diff --check` exits zero (boundaries, AC11).

**Approach:**

- Record the shipped guide treatment in the product changelog.
- Complete the spec/plan lifecycle fields and spec index for the version-bump
  change, but retain the backlog entry. Repository policy assigns its removal
  to a separate closeout after AgentBundle publication is confirmed.

**Done when:** AC1–AC12 are satisfied, every acceptance command exits zero, the
visual evidence is reviewed, and all warranted reviewers are clean.

## Rollout

This is an atomic static-content and bundled-scaffold publication. It adds no
infrastructure, runtime dependency, migration, feature flag, or external
integration. The implementation prepares the Constraints-selected AgentBundle
patch release, but this enterprise session does not commit, tag, or publish;
the handoff commit needs
`Engine-Change-RFC: ADR-0056`, and the normal post-merge release workflow tags
from `main`. Only after that publication is confirmed may a separate closeout
remove the registered backlog entry. Reverting the guide wrappers, tests,
ledger, canonical/bundled
standard, and release metadata restores the prior output; no data migration or
irreversible state exists.

## Risks

- **A prompt or sample output is mistaken for advice.** The exact-wording test
  and quotation-first rule keep attribution semantics dominant.
- **A caution is overstated as danger.** Consequence-based rationale is required
  for every row; danger without severe or irreversible harm fails review.
- **A large diff hides a missed file.** The AC1 content-identity ledger and
  zero-pending gate prove enumeration independently of the diff.
- **The canonical standard ships while the scaffold copy stays stale.** The
  sync writer, manifest check, package projection tests, and release metadata
  are one task and one gate sequence.
- **Markdown passes source checks but renders incorrectly.** Every ledger row is
  resolved against emitted HTML, and representative pages run in a browser.
- **Astro cache masks a conversion defect.** Both documented cache directories
  are removed before the acceptance build.
- **Whole-site scans flake under load.** The existing 60-second scan timeout is
  retained and every gate's direct exit code is read.

## Changelog

- 2026-08-16: Corrected AC1 to the parser-visible baseline defined by the spec
  after the lexical scan counted `>` lines inside fenced code examples.
- 2026-08-15: Initial full-mode plan materialized from the registered backlog
  item; fixed Starlight vocabulary and proceed-without-principles decision
  retained.
