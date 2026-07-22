# Spec: m5-tracker-guides

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (P4 · Intake edges — tracker guide slice)
- **Brief:** none
- **Contract:** none
- **Shape:** docs

Mode: light (no risk trigger fired)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship two cross-cutting guide artifacts that help adopters navigate the tracker
brief-intake landscape:

1. **Decision tree** (`choose-a-tracker-integration.md`) — a how-to guide that
   answers "which tracker skill should I use?" for the five intake paths: no
   tracker, GitHub Milestone, Linear Issue/Project, Jira epic, and Jira Align
   Feature.
2. **Vocabulary mapping table** (`tracker-vocabulary.md`) — a reference doc that
   maps the same conceptual levels (brief, spec) to the corresponding object in
   each tracker, plus the skill-to-skill routing table.

Both live in `docs/guides/_shared/` because they span multiple packs (`github`,
`linear`, `atlassian`, `core`) — no single pack guide is the right home.

## Acceptance Criteria

- [x] **AC1.** `docs/guides/_shared/how-to/choose-a-tracker-integration.md`
  exists and covers all five intake paths with prerequisites and links to the
  per-tracker how-to guide where one exists: no tracker (`author-brief`), GitHub
  Milestone (`github-brief-intake`), Linear Issue/Project (`linear-brief-intake`),
  Jira epic (`jira-brief-intake`), Jira Align Feature (`jira-align-brief-intake`).
  A decision table is the entry point.
- [x] **AC2.** `docs/guides/_shared/reference/tracker-vocabulary.md` exists with
  (a) a cross-tracker vocabulary table mapping canonical brief/spec levels to each
  tracker's objects (GitHub, Linear, Jira, Jira Align, none), and (b) the
  brief-intake skill routing table (tracker → skill → pack).
- [x] **AC3.** `docs/guides/_shared/how-to/README.md` lists
  `choose-a-tracker-integration.md` with a one-line description.
- [x] **AC4.** `docs/guides/_shared/reference/README.md` lists
  `tracker-vocabulary.md` with a one-line description.
- [x] **AC5.** `docs/guides/README.md` Shared guides section references both new
  guides by name.
- [x] **AC6.** `docs/product/changelog.md` `[Unreleased]` entry records the new
  guides.

## Testing Strategy

Pure docs — no executable logic.

- **Content correctness: goal-based check.** Each guide file exists at the correct
  path. All five intake paths appear in AC1's decision guide. Both sub-tables
  (vocabulary + skill routing) appear in AC2's reference. Verified by `grep` and
  `ls`.
- **Doc-drift: goal-based check.** `_shared/how-to/README.md`,
  `_shared/reference/README.md`, and `docs/guides/README.md` all name the new
  files. Verified by `grep`.

## Assumptions

- Technical: The five intake paths (no tracker, GitHub, Linear, Jira, Jira Align)
  are the complete set of brief-intake adapters that have shipped as of this spec.
  No other tracker pack is in the shipped list. (probe: workspace.toml shipped
  list, 2026-07-22)
- Technical: `jira-brief-intake` ships in the `atlassian` pack (not a separate
  pack); `jira-align-brief-intake` also ships in `atlassian`. (probe:
  `packs/atlassian/.apm/skills/`, 2026-07-22)
- Technical: The `_shared/how-to/` and `_shared/reference/` directories exist and
  accept new files without restructuring. (probe: `ls docs/guides/_shared/`,
  2026-07-22)
- Process: Phase-slice doctrine: this spec ships both guides in a single PR — no
  terminal doc wave. (source: workspace.toml P4 header)
- Product: `docs/guides/_shared/` is the correct location for cross-pack guides
  that span `github`, `linear`, `atlassian`, and `core`. (source: `_shared/README.md`,
  which defines it as the home for cross-cutting guides)
