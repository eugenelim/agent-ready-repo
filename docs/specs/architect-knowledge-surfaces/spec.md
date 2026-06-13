# Spec: architect-knowledge-surfaces

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A solution architect using the `architect-design` skill inside an enterprise
today gets a design shaped only by what they type into the chat — the skill
has no way to consult the organisation's own knowledge (the living application
landscape, the mandated standards, the approved patterns, the decisions
already taken, the work in flight). When that enterprise *has* wired a
knowledge-retrieval surface into the agent's environment — an MCP knowledge
tool, an internal CLI, an in-repo doc set — the skill should notice and use
it, so the design is grounded in the organisation's reality instead of the
architect's recall. When no such surface exists, the skill must behave exactly
as it does today, only more honestly: it asks the user for the missing context
and lowers the confidence of any proposal that leaned on knowledge it could
not verify. The mechanism must be **distribution-agnostic** — the skill ships
to many IDEs/CLIs and cannot know an adopter's knowledge topology — and
**zero-cost when unused**, so the full taxonomy loads only once a surface is
actually detected.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Detect knowledge surfaces **harness-agnostically** — from the tools/CLIs the
  session actually exposes — and name no concrete tool or CLI in the skill or
  reference.
- **Degrade gracefully** when no surface is present: ask the user for the
  missing context and lower the confidence of any proposal that depended on it,
  reusing the skill's existing compose-with-`research`/degrade-if-absent wording.
- Keep the `architect-design/SKILL.md` addition frugal (a single conditional
  step); put the substance in the progressive-disclosure reference.
- Bump the architect pack version, add a changelog entry, and run
  `make build-self` so `marketplace.json` reflects the bump.

### Ask first

- Extending the consult step to `architect-review` or `architect-diagram`
  (deferred: architect-review-diagram-knowledge-surfaces).
- Introducing any declared registry, shared-config file, or `~/.agentbundle`
  lookup for knowledge surfaces.
- Any edit to `docs/CONVENTIONS.md` or `docs/CHARTER.md` (would require an RFC).

### Never do

- Ship an enterprise knowledge server, RAG index, or any retrieval *engine* —
  that is runtime infrastructure, out of charter. We ship *awareness*, not a
  backend.
- Read shared user-global state (`~/.agentbundle/…`) from the skill — it breaks
  skill isolation.
- Create a cross-pack shared artifact, or make `architect` depend on another
  pack (the rejected Route B). The reference lives inside the architect pack.
- Add a new dependency, a new module boundary, or a new top-level directory.
- Edit `architect-review/SKILL.md` or `architect-diagram/SKILL.md` in this PR
  (the T2 `git diff` check enforces this; the extension is deferred above).
- Edit projected paths directly (this repo is self-hosting; edit `packs/…`
  source, then `make build-self`).

## Testing Strategy

- **Reference + SKILL.md content** — *goal-based check*. The artifacts are
  prose; correctness is verified by the lint/build gates (`lint-skill-spec`,
  `lint-packs`, `lint-agent-artifacts`, `validate`, `build`, `pytest`) plus a
  `grep` proving no concrete tool/CLI name was hardcoded. A unit test would
  only assert what the linter already proves.
- **Marketplace drift** — *goal-based check*. `make build-self` runs clean and
  `marketplace.json` shows architect at the new version; `git status` shows no
  stray artifacts (`__pycache__`).
- **Detection behaviour** — *manual QA*, two halves, both recorded in the plan
  (T5). (1) A **real structural check**: `make build` projects the change and
  the projected `SKILL.md` + reference are byte-identical to source — what an
  adopter install delivers. (2) A **decision-logic walkthrough**: an independent
  agent executes the step against a fixed driver across present / absent /
  sensitive scenarios. **Harness limitation, stated honestly:** this session
  can't inject a *live* mock MCP knowledge tool, so per-scenario tool presence is
  *described* (a simulation of the branch logic), not a live MCP detection. A
  true temp-install-with-live-mock run is a deferred enhancement
  (`live-mock-mcp-detection-qa` in `docs/backlog.md`).

## Acceptance Criteria

- [x] A new reference `packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md`
  exists and carries the 8-area MECE taxonomy — (1) business domain & meaning,
  (2) current landscape, (3) interfaces & contracts, (4) operational reality,
  (5) constraints & standards, (6) patterns & references, (7) decisions &
  rationale, (8) in-flight & roadmap — each with the question it answers and a
  design-lens consult trigger.
- [x] The reference documents the MECE organising axis (modality × space) so a
  reader can see why the eight don't overlap, and names the one adjacency seam
  (areas 2/3/4 as three facets of "the current system").
- [x] **Harness-agnostic detection** (grep- + read-verified): the reference
  describes discovering retrieval surfaces from the session's available
  tools/CLIs (tool search where the harness defers tools; the loaded tool list
  otherwise), contains **no hardcoded tool/CLI names**, **excludes public web
  search** as an internal surface, and requires the skill to **name the detected
  surface (or "none")** so detection is auditable rather than self-attested.
- [x] **Degradation rules** (per-clause manual QA in T5): the reference states,
  and the SKILL.md step honours, that with no surface the skill (a) asks the
  user for the missing context and lowers confidence, (b) never fabricates
  landscape/standards/in-flight facts, and (c) treats sensitive or read-only
  sources as ask-before-quoting. Each clause records an observed result in T5.
  Additionally, on the **present** path a single unconfirmed source is carried
  at lowered confidence (reference states this; read-verified in T1).
- [x] `architect-design/SKILL.md` gains a single **conditional** procedure step
  that detects a surface, loads the reference **only when one is detected**
  (progressive disclosure), and applies the degrade rule otherwise; the step
  names no concrete tool.
- [x] The SKILL.md step reuses the existing compose-with-`research` /
  degrade-if-absent framing rather than inventing a parallel mechanism.
- [x] No registry, no shared-config file, no `~/.agentbundle` read, no new
  dependency, and no cross-pack shared artifact are introduced (verified by
  diff inspection). (Sibling SKILL.md non-edits are a Boundary, enforced by the
  T2 `git diff` check, not an acceptance criterion.)
- [x] The architect pack's `[pack]` version specifically (not the unrelated
  `[contract] version`) is bumped `0.2.0 → 0.3.0` in both
  `packs/architect/pack.toml` and `packs/architect/.claude-plugin/plugin.json`.
- [x] `docs/product/changelog.md` `[Unreleased]` has an entry describing the
  new awareness behaviour.
- [x] `make build-self` has been run; `marketplace.json` reflects architect
  `0.3.0`; `git status` shows no stray/untracked artifacts.
- [x] All gates green: `lint-skill-spec`, `lint-packs`, `lint-agent-artifacts`,
  `validate`, `build`, `pytest`.
- [x] Detection QA recorded against a **fixed driver** in two halves: (1)
  **structural (real)** — projected `SKILL.md` + reference byte-identical to
  source; (2) **decision-logic walkthrough** by an independent agent —
  surface-present cites the area the surface answers; surface-absent emits an
  explicit ask + lowered-confidence + no fabrication; sensitive-surface asks
  before quoting. Live mock-MCP detection is *simulated* (harness limitation),
  logged as a deferred enhancement (`live-mock-mcp-detection-qa`).

## Assumptions

- Technical: architect is v0.2.0 (source: `packs/architect/pack.toml`).
- Technical: architect is a user-scope-default pack, not projected into this
  repo's `.claude/` tree; `SELF_HOST_PACKS = {core, governance-extras,
  user-guide-diataxis}` (source: `packages/agentbundle/agentbundle/build/self_host.py:95`).
- Technical: a version bump drifts top-level `marketplace.json` (aggregation
  ignores the self-host filter); `make build-self` refreshes it and build-check
  red-fails until it is run (source: `SELF_HOST_PACKS` at `self_host.py:95`;
  `_aggregate_marketplace` ignores the filter at `self_host.py:494` + prior
  learning).
- Technical: the SKILL.md hard lint cap is 1000 body lines, not 100;
  architect-design was at 99 lines pre-change and is 110 after the step
  insertion — still far under the 1000 hard cap; "~100" is an authoring
  discipline, not a gate (source: `tools/lint-skill-spec.py:490`).
- Technical: `architect-design` already loads references on demand, so a
  progressive-disclosure reference fits the established pattern (source:
  `packs/architect/.apm/skills/architect-design/SKILL.md`).
- Technical: the research pack already enumerates "retrieval-shaped MCP tools
  registered in the session" — the detection precedent (source:
  `packs/research/.apm/skills/research/SKILL.md`, `references/retriever-interface.md`).
- Process: changelog `[Unreleased]` is the home for user-visible skill changes
  (source: `docs/product/changelog.md:18`).
- Process: no RFC — the doctrine lives in the skill reference, not
  CONVENTIONS/CHARTER (source: user confirmation 2026-06-13).
- Product: detection is permissive + harness-agnostic + degrade-and-lower-
  confidence; the taxonomy has 8 areas with a design lens; version target is
  0.3.0; verification may use a temp install (source: user confirmation
  2026-06-13).
