# Spec: architect-design-reviewer

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0032, ADR-0023
- **Brief:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship a read-only, forked-context `design-reviewer` subagent in the architect
pack that supplies the convergence loop's *preferred* fresh-context reviewer
rung (RFC-0032). A solution architect — or `architect-design`'s convergence
loop — dispatches it to critique a design doc, diagram, or architecture
artifact **independently**: seeded with the artifact + the agreed concept +
the constraints, never the authoring chain-of-thought, so it cannot mark its
own homework. It returns a one-line verdict plus severity-tagged and
mechanical/judgment-tagged findings, and it **cannot edit the design** (its
tools are read-only). It reuses the `architect-review` methodology — both the
verdict-critique mode and the well-architected risk-register mode — coexists
with the `architect-review` skill (neither replaces the other), and degrades
gracefully: the convergence loop never hard-depends on it.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the agent self-contained in a single `.md` under
  `packs/architect/.apm/agents/` — agents bundle no `references/` directory.
- Reuse `architect-review`'s verdict scheme, severity glossary, and
  mechanical/judgment taxonomy where inlined; carry a one-line note that
  `architect-review`'s `references/` hold the fuller genre rubrics where the
  skill is co-installed (the pack's standing duplication-over-DRY discipline).
- Edit `packs/architect/.apm/` source, then `make build-self` to refresh
  `marketplace.json`; bump the pack version and add a changelog entry.

### Ask first

- Any change to the pack's `[pack.adapter-contract] version` (currently 0.10).
- Modifying `architect-review`'s own rubric reference files (vs. inlining a
  condensed copy in the agent).
- Wiring the agent into the core `work-loop`'s default gate sequence.

### Never do

- No new dependency; no new top-level directory.
- Don't give the agent `Edit`/`Write`/`Bash` tools — read-only is the contract.
- Don't retire or change the `architect-review` skill's behavior.
- Don't make `architect-design`'s convergence loop a *hard* dependency on the
  agent — it must degrade to the existing ladder when the agent is absent.
- Don't edit projected paths directly (e.g. `.claude/`, `dist/`); edit the
  `.apm/` source and build.

## Testing Strategy

This feature is markdown primitives + governance docs + build mechanics; there
is no logic with a compressible invariant, so verification is **goal-based**
(one-liner greps, lint, build) plus the package **pytest** suite as the
integration surface. No TDD-mode tasks.

- **Agent frontmatter + read-only tools (AC1, AC5): goal-based** — `grep` the
  frontmatter keys/values and confirm `tools:` is exactly `Read, Grep, Glob`;
  **`lint-packs` green** is the structural gate (its `_check_agent_metadata`
  walks `packs/*/.apm/agents/` and enforces the 1024-char cap).
  `lint-agent-artifacts.py` walks the projected `.claude/agents/`, which
  architect is not projected into here, so it does not exercise this agent —
  don't count its pass as evidence for this agent's frontmatter.
- **Agent body anchors (AC2–AC4): goal-based** — `grep` for the required
  anchors (verdict labels, severity glyphs, mechanical/judgment tokens,
  genre-routing list, the "never the authoring chain-of-thought" and
  findings-only-output clauses). Why: the contract is the presence of these
  prose anchors.
- **Convergence-loop rung, README revision, guides (AC6–AC8): goal-based** —
  `grep` the edited prose for the new rung + the revised exclusion + the
  guide mentions; `lint-packs` green. Why: prose edits verified by their
  observable presence.
- **Version bump + marketplace drift (AC9): goal-based** — `make build-self`,
  then `git status` clean and the drift gate green. Why: the build is the
  mechanical contract.
- **Cross-adapter projection (AC10): goal-based, exercised across the adapter
  boundary** — a durable, re-runnable assertion (extended contract/adapter test
  or a committed one-liner over a freshly built `dist/`) names architect +
  `design-reviewer` across all seven routes; manual `dist/` inspection is a
  supplement only. Why: `dist/` is gitignored, so the check of record must be
  committed and re-runnable.
- **ADR (AC11) + changelog (AC12): goal-based** — files exist with correct
  status/section and resolve from the RFC follow-on + this spec.
- **Suite green + inventory assertions (AC13): goal-based, integration** —
  full `packages/agentbundle` pytest + `validate` + `build` green; the
  pre-named candidate assertions (`test_plugin_manifest_schema.py`,
  `test_contract.py`, `test_adapter_{codex,cursor}.py`, the
  `test_multi_pack_install.py` architect scenarios) are checked and updated if
  red.

## Acceptance Criteria

- [x] `packs/architect/.apm/agents/design-reviewer.md` exists; frontmatter
  declares `name: design-reviewer`, `tools: Read, Grep, Glob`, `model: opus`,
  and a `description` within the lint length cap that triggers on an
  independent critique of a design artifact.
- [x] The agent body is **self-contained**: it inlines the verdict scheme
  (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT), the severity
  glossary (🟥 blocker / 🟧 major / 🟨 minor / ⚪ nit), the mechanical/judgment
  taxonomy, and genre routing for the artifact types (design doc, C4, sequence,
  state, ER, generic), and carries a one-line note pointing at
  `architect-review`'s `references/` as the fuller rubric source where the
  skill is co-installed. At authoring time the inlined verdict labels, severity
  glyphs, and the 🔧/🧭 taxonomy are confirmed **byte-faithful** to
  `architect-review/SKILL.md` and `references/rubric-well-architected.md` (a
  one-time diff recorded in T1) — anchor-presence alone does not prove the
  inlined semantics match the skill.
- [x] The agent body covers **both** `architect-review` modes — the verdict
  critique and the well-architected risk-register (each finding tagged
  🔧 mechanical / 🧭 judgment).
- [x] The agent body codifies **reviewer-independence**: it states it must be
  seeded with the artifact + concept + constraints and **never the authoring
  chain-of-thought**, that it flags but never rewrites the design, and that it
  returns the **findings block only** (no methodology recap or narration),
  matching the core reviewers' output contract.
- [x] The agent's `tools:` is exactly `Read, Grep, Glob` — no `Edit`, `Write`,
  or `Bash`.
- [x] `packs/architect/.apm/skills/architect-design/references/convergence-loop.md`
  § *Where the review comes from* gains a rung naming the `design-reviewer`
  agent as the rung-1 (fresh-context) source when installed, degrading to the
  existing `architect-review`-installed / embedded-self-check ladder otherwise;
  the loop's soft-dependency wording is preserved.
- [x] `packs/architect/README.md` revises the exclusion that currently reads
  (substring match, the sentence wraps two lines) *"Code-side reviewers cover
  code; design-side review is a skill, not a subagent."* and documents the
  shipped `design-reviewer` subagent.
- [x] `docs/guides/architect/how-to/review-an-architecture-artifact.md` and
  `docs/guides/architect/README.md` mention the `design-reviewer` subagent as
  the independent (fresh-context) review option alongside the in-thread skill.
- [x] Pack version bumped `0.5.3` → `0.6.0` in `packs/architect/pack.toml`
  **and** `packs/architect/.claude-plugin/plugin.json`; `marketplace.json`
  refreshed via `make build-self`; working tree clean.
- [x] The agent projects across all seven of architect's `allowed-adapters`.
  Verification of record is **durable and re-runnable**: a contract/adapter-test
  assertion (or an explicit committed goal-based one-liner run against a freshly
  built `dist/`) that names architect + `design-reviewer` across all seven
  routes and fails if a future adapter change drops it. A manual `dist/`
  inspection is allowed only as a supplement, never as the sole evidence
  (`dist/` is gitignored). This is where RFC-0032's deferred `kiro-cli`
  install-confirmation lands.
- [x] `docs/adr/<NNNN>-*.md` records the charter-ceiling interpretation
  (RFC-0032 decision 2 — "three reviewers is the ceiling" scopes the core
  code-review lenses, not opt-in design-side review), status Accepted, linked
  from RFC-0032's follow-on artifacts and this spec's `Constrained by`.
- [x] `docs/product/changelog.md` `[Unreleased] → Added` carries an entry for
  the `design-reviewer` subagent.
- [x] Full `packages/agentbundle` pytest, `lint-packs`, `lint-agent-artifacts`,
  `validate`, and `build` are green. The candidate assertions that could see
  architect's first agent — pre-identified by grep — are checked and updated if
  red: `test_plugin_manifest_schema.py`, `test_contract.py`,
  `test_adapter_{codex,cursor}.py`, and the `test_multi_pack_install.py`
  architect scenarios (the last use `>= {…}` membership, so are expected to
  stay green). "Green suite" is only a valid signal because these targets were
  named up front, not discovered by absence.

## Assumptions

- Technical: Agents ship as a flat single `.md` under `.apm/agents/` with no
  bundled `references/` dir, so the agent must inline its rubric (source:
  `packages/agentbundle/agentbundle/build/adapters/*.py` read `.apm/agents/<name>.md`).
- Technical: `plugin.json` does not declare agents — the build discovers them
  from `.apm/agents/` (source: `packs/research/.claude-plugin/plugin.json`
  ships no agents array yet research ships two subagents).
- Technical: Architect is not projected into this repo's `.claude/`; the agent
  lands only in `packs/architect/.apm/agents/` + `marketplace.json` via build
  (source: `ls .claude/agents` shows only the four core agents).
- Technical: The adapter-contract version stays 0.10 — agents have been
  admitted since v0.7 (source: `test_shipped_packs_v08_declarations.py:24`
  comment; architect not in `V08_PACKS`).
- Technical: All seven of architect's `allowed-adapters` project the agent
  primitive at user scope (source: RFC-0032 § Evidence spike, per adapter
  module).
- Technical: `model: opus` matches the core reviewers (source:
  `packs/core/.apm/agents/adversarial-reviewer.md:5`).
- Process: Constrained by RFC-0032, Accepted 2026-06-14; its follow-on names a
  co-landed ADR for the charter-ceiling reading (source:
  `docs/rfc/0032-architect-design-reviewer-subagent.md`).
- Process: User-visible agent prose changes need a `docs/product/changelog.md`
  `[Unreleased]` entry in the same PR (source: changelog header + repo
  convention).
- Process: Edit `.apm/` source then `make build-self`; a version bump on a
  non-projected pack drifts `marketplace.json` (source: build-check drift gate
  behavior, prior PRs).
- Product: The agent covers both `architect-review` modes; the ADR co-lands in
  this PR; the architect guides are updated in this PR (source: user
  confirmation 2026-06-14).
