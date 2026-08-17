# Spec: guide-typed-asides-conversion

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs-site-design-refresh`](../docs-site-design-refresh/spec.md), [docs-site aesthetic direction](../docs-site-design-refresh/creative-direction.md), [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md), [`guides/AGENTS.md`](../../../guides/AGENTS.md)
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter scanning a published guide can distinguish supporting context,
helpful technique, likely pitfall, and severe hazard at a glance, while exact
quoted language retains quotation semantics. Every legacy guide blockquote has
an explicit classification; non-quotation callouts render through Starlight's
fixed aside types; and the catalogue authoring standard makes that distinction
the default for future guides without changing any guide's route or navigation.

This spec materializes the registered `guide-typed-asides-conversion`
follow-up. Its shipped `ini-002.work.shipped` register entry preserves the
historical problem, prescribed fix, scope, and prior decisions.

## Boundaries

### Always do

- Classify every contiguous legacy blockquote before changing its Markdown,
  recording enough evidence for a reviewer to reproduce the decision.
- Preserve the words, inline formatting, links, code, list order, and surrounding
  guide order when changing only the semantic container.
- Use only Starlight's `note`, `tip`, `caution`, and `danger` vocabulary,
  reserving `danger` for severe or irreversible harm.
- Keep the catalogue authoring standard and AgentBundle's bundled scaffold copy
  byte-identical, including the scaffold manifest and required patch-release
  metadata.
- Verify the cache-cleared emitted site, including representative light and dark
  pages, rather than accepting source-shape checks as sufficient.

### Ask first

- Any classification whose quotation status or severity remains ambiguous after
  reading the complete surrounding section.
- Any wording change beyond the minimum delimiter/title edit needed to express
  the classification.
- Any change to guide routes, titles, frontmatter, sidebar order, pagination,
  breadcrumbs, docs styling, or Starlight configuration.

### Never do

- Name the external review reference in a tracked file or Git artifact.
- Convert an attributed quotation, user/system utterance, sample transcript or
  output, or exact wording being demonstrated into an aside.
- Introduce another aside type, a custom callout component, a dependency, or a
  permanent conversion CLI.
- Align the docs palette to `web/`'s amber system or reopen the decision to
  proceed without `site-design-principles`.
- Rework the shipped landing orientation, pagination, breadcrumbs,
  summary/deck plumbing, inline-code treatment, marketing mobile work, CTA
  hierarchy, or drawer touch targets.

## Testing Strategy

**Classification integrity uses a goal-based construction check** over the
complete classification ledger. It proves every baseline block is visited
exactly once, every row has a terminal disposition and rationale, retained
quotations preserve their original content hash, and converted rows use one
allowed Starlight type. This check is necessary for coverage but is not treated
as proof of rendered behavior.

**Rendered behavior uses a built-output integration test** across every
published guide page. It resolves each ledger record to emitted HTML and checks
that quotations are blockquotes, converted records are the selected typed
asides, and every emitted aside has the expected semantic class, visible label,
and icon. Whole-site scans retain the existing 60-second timeout.

**Reader-visible quality uses browser QA** against the completed built tree. A
representative recovery page and a representative exact-wording page run in
light and dark at desktop and 375 px, with screenshots, overflow checks, and
axe serious/critical checks. Guide validation, title lint, link checks,
contrast, and repository policy gates protect the surrounding publication
contract.

**Documentation and release-handoff contracts use goal-based repository checks.** A
pure-stdlib test verifies the authoring-standard rule, fixed type table, and
selection examples in both canonical and bundled scaffold copies. The same
check fails until the changelog, spec index, package release metadata, and
workspace lifecycle agree: the canonical record appears exactly once in
`ini-002.work.shipped` and is absent from `backlog.open`, active work, and
queued work.

## Acceptance Criteria

- [x] **AC1 — Exhaustive classification.** A tracked ledger contains exactly
  one row for each of the 166 parser-visible contiguous blockquote blocks
  present at the approved baseline. Fenced-code lines beginning with `>` are
  excluded because Markdown renders them as code, not quotations. Every row
  records source path, original line, stable
  content identity, `quotation|note|tip|caution|danger`, a one-sentence
  rationale, and terminal status; no row remains pending or failed.
- [x] **AC2 — Genuine quotations remain quotations.** Every row classified
  `quotation` retains its original text and inline content in Markdown and
  renders as a `<blockquote>` on its published guide page, outside any
  Starlight aside.
- [x] **AC3 — Load-bearing blocks become typed asides.** Every non-quotation
  ledger row preserves its content and relative position, uses the selected
  `:::` aside type, and renders inside an
  `aside.starlight-aside--<type>` with a non-empty label and icon.
- [x] **AC4 — Classification semantics are consistent.** Context and scope use
  `note`; optional improvements use `tip`; pitfalls, limitations, recovery,
  and reversible risk use `caution`; only severe or irreversible harm uses
  `danger`. No alias or additional warning vocabulary appears.
- [x] **AC5 — Authoring standard.** The existing catalogue authoring standards
  reference defines genuine quotations by attribution/exact-wording semantics,
  makes typed asides the default for non-quotation emphasis, documents all four
  types, and includes concise selection examples.
- [x] **AC6 — Bundled standard ships in sync.** AgentBundle's catalogue
  scaffold copy of the authoring standard is byte-identical to the canonical
  guide, its manifest records the new digest, the package carries the required
  patch version and changelog/PyPI-description updates, and scaffold projection
  checks pass.
- [x] **AC7 — Published identity is stable.** Guide file paths, resolved routes,
  titles, frontmatter values, sidebar leaf order, current-page state,
  pagination targets, and breadcrumbs are byte-for-byte or structurally
  unchanged as appropriate.
- [x] **AC8 — Whole-site emitted regression.** A 60-second built-output scan
  finds no untracked guide blockquote, missing or duplicate ledger match,
  unknown aside type, source/built classification mismatch, missing aside
  label/icon, or ledger record absent from its emitted guide page.
- [x] **AC9 — Theme and accessibility floor.** Representative quotation and
  recovery-callout pages in light and dark show the expected semantic
  containers at 1440×900 and introduce no horizontal body overflow at 375 px;
  screenshots show distinct label/icon/tint treatment, and axe reports zero
  serious or critical violations.
- [x] **AC10 — Documentation gates.** Guide schema validation, guide-index
  coverage, `tools/lint-guide-titles.py`, documentation-entry links, rendered
  links, and docs contrast checks all pass.
- [x] **AC11 — Cache-cleared delivery.** After clearing
  `docs-site/.astro` and `docs-site/node_modules/.astro`, the canonical
  content sync, `web` build, `docs-site` build, rendered-output suite,
  aside browser journey, and relevant repository policy gates all exit zero.
- [x] **AC12 — Release handoff.** The product changelog records the
  reader-visible guide treatment, the spec index reflects the completed
  version-bump change, required package release metadata is present, and the
  registered backlog entry has moved into this batch's shipped work register;
  AgentBundle publication follows immediately after the batch lands.

## Assumptions

- Technical: the public guide corpus currently contains 189 Markdown files,
  with parser-visible blockquotes across 72 files and typed asides in three
  files; AC1 is the sole exact baseline-count anchor (source: fence-aware
  read-only `guides/**/*.md` inventory probe 2026-08-16).
- Technical: `guides/` is the public source and `tools/build-site.py`
  mirrors it into Starlight without requiring route changes (source:
  `guides/AGENTS.md`).
- Technical: Astro 7.1.0 and exact-pinned Starlight 0.41.4 are the rendering
  stack; Starlight's Markdown aside vocabulary is
  `note|tip|caution|danger` (source: `docs-site/package.json` and
  https://starlight.astro.build/guides/authoring-content/).
- Product: the docs surface's dominant goal is instrument-grade clarity while
  retaining the established cobalt/cool-neutral palette (source:
  `docs/specs/docs-site-design-refresh/creative-direction.md`).
- Product: this is a UI-shaped documentation-interface change with no
  machine-readable interface contract; the registered design-review finding
  and grounded aesthetic direction are sufficient design readiness (source:
  user confirmation 2026-08-15).
- Process: the work runs in full mode with separate spec and plan approval
  gates, emitted-site verification, and no Git ref mutation (source:
  `AGENTS.md`, `docs/CONVENTIONS.md`, and enterprise session constraints).
- Process: the existing authoring-standard destination is
  `guides/_shared/reference/catalogue-authoring-standards.md` (source:
  existing guide tree and user confirmation 2026-08-15).
- Process: that guide is projected into AgentBundle's bundled catalogue
  scaffold, so editing it triggers scaffold sync plus package Gate G release
  metadata (source: `tools/catalogue/sync_authoring_scaffold.py` and
  `packages/agentbundle/AGENTS.md`).
