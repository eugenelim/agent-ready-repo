# Spec: product-engineering-knowledge-surfaces

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

A product person using the `frame-intent` skill inside an enterprise today
shapes an intent — an outcome plus the opportunity behind it — from nothing
but what they type into the chat. The skill has no way to consult the
organisation's own knowledge: what the domain terms and business rules
actually *mean*, what work is already *in flight* against the same outcome,
what the *current landscape* looks like in a brownfield, how the real system
*behaves* in production. When an enterprise *has* wired a knowledge-retrieval
surface into the agent's environment — an MCP knowledge tool, an internal CLI,
an in-repo doc set — `frame-intent` should notice and consult it through a
**problem-framing lens**, so the intent is grounded in the organisation's
reality instead of the framer's recall (avoiding a duplicate bet on work
already underway, or an opportunity framed on a misread of the domain). When
no such surface exists, the skill must behave exactly as it does today, only
more honestly: it asks the user for the missing context and lowers the
confidence of any assumption that leaned on knowledge it could not verify. The
mechanism must be **distribution-agnostic** — the skill ships to many IDEs/CLIs
and cannot know an adopter's knowledge topology — and **zero-cost when unused**,
so the taxonomy loads only once a surface is actually detected.

This is the deliberate **product-engineering counterpart** of the
`architect-design` knowledge-surface awareness (spec
`architect-knowledge-surfaces`, PR #297). It shares the mechanism but changes
the lens: architect asks the *design* questions of the organisation;
`frame-intent` asks the *problem-framing* questions. The taxonomy here is a
**strict subset** of architect's eight areas — the four that bear on framing a
problem — and deliberately omits the four solution-design areas so
product-engineering does not drift into solution space.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Detect knowledge surfaces **harness-agnostically** — from the tools/CLIs the
  session actually exposes — and name no concrete tool or CLI in the skill or
  reference.
- **Degrade gracefully** when no surface is present: ask the user for the
  missing context and lower the confidence of any assumption that depended on
  it, using a **compose-if-present / degrade-if-absent** framing.
- Keep the taxonomy a **strict subset** of architect's eight areas — areas (1)
  business domain & meaning, (2) current landscape, (4) operational reality,
  (8) in-flight & roadmap — under a problem-framing lens, and keep the
  shared-canonical-core anchor note (naming the architect reference as the
  canonical definition) so the two copies don't diverge.
- Wire the **current-landscape** area (2) into the existing brownfield maturity
  gate in `frame-intent/references/current-state-inputs.md` (it is the
  brownfield-only area).
- Keep the `frame-intent/SKILL.md` addition frugal (a single conditional step);
  put the substance in the progressive-disclosure reference.
- Bump the product-engineering pack version, add a changelog entry, and run
  `make build-self` so `marketplace.json` reflects the bump.

### Ask first

- Extending the consult step to `de-risk-intent` or `decompose-intent`.
- Introducing any declared registry, shared-config file, or `~/.agentbundle`
  lookup for knowledge surfaces.
- Any edit to `docs/CONVENTIONS.md` or `docs/CHARTER.md` (would require an RFC).
- Editing the `value-stream-meta-repo` spec/plan (a separate, now-Shipped spec
  that bumped this pack to 0.2.0 in #298); coordinate the version instead.

### Never do

- Include any of the four solution-design areas — (3) interfaces & contracts,
  (5) constraints & standards, (6) patterns & references, (7) decisions &
  rationale — in the product-engineering reference. Those are the architect
  (design) lens; including them would drift product-engineering into solution
  space.
- Ship an enterprise knowledge server, RAG index, or any retrieval *engine* —
  that is runtime infrastructure, out of charter. We ship *awareness*, not a
  backend.
- Read shared user-global state (`~/.agentbundle/…`) from the skill — it breaks
  skill isolation.
- Create a cross-pack shared artifact, or make `product-engineering` depend on
  another pack (the rejected Route B). The reference lives inside the
  product-engineering pack — duplicate the shared core, don't share a file.
- Add a new dependency, a new module boundary, or a new top-level directory.
- Edit `de-risk-intent/SKILL.md` or `decompose-intent/SKILL.md` in this PR (the
  T2 `git diff` check enforces this; the extension is deferred above).
- Claim a `research`-compose precedent that `frame-intent` does not have:
  `frame-intent` does not compose with `research` today, so the framing is the
  generic compose-if-present / degrade-if-absent, not "as the skill already
  does when `research` is absent."
- Edit projected paths directly (this repo is self-hosting; edit `packs/…`
  source, then `make build-self`).

## Testing Strategy

- **Reference + SKILL.md content** — *goal-based check*. The artifacts are
  prose; correctness is verified by the lint/build gates (`lint-skill-spec`,
  `lint-packs`, `lint-agent-artifacts`, `validate`, `build`, `pytest`) plus a
  `grep` proving no concrete tool/CLI name was hardcoded.
- **Maturity-gate wiring** — *goal-based check*. `current-state-inputs.md`
  names the current-landscape area as the brownfield knowledge-surface input;
  verified by read + `grep` for the cross-reference to the new reference.
- **Marketplace drift** — *goal-based check*. `make build-self` runs clean and
  `.claude-plugin/marketplace.json` shows product-engineering at `0.3.0`;
  `git status` shows no stray artifacts (`__pycache__`).
- **Detection behaviour** — *manual QA*, two halves, both recorded in the plan
  (T5). (1) A **real structural check**: `make build` projects the change and
  the projected `SKILL.md` + reference are byte-identical to source — what an
  adopter install delivers. (2) A **decision-logic walkthrough**: an independent
  agent executes the step against a fixed driver across present / absent /
  sensitive / brownfield scenarios. **Harness limitation, stated honestly:** this
  session can't inject a *live* mock MCP knowledge tool, so per-scenario tool
  presence is *described* (a simulation of the branch logic), not a live MCP
  detection — the same deferred enhancement architect logged
  (`live-mock-mcp-detection-qa` in `docs/backlog.md`).

## Acceptance Criteria

- [x] A new reference
  `packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md`
  exists and carries the **four-area problem-framing subset** of architect's
  taxonomy — (1) business domain & meaning [PRIMARY], (8) in-flight & roadmap
  [PRIMARY], (2) current landscape [brownfield-only], (4) operational reality
  [light] — each with the question it answers and a **problem-framing** consult
  trigger.
- [x] The reference **explicitly omits** the four solution-design areas
  (3 interfaces & contracts, 5 constraints & standards, 6 patterns &
  references, 7 decisions & rationale) and says **why** (those are the
  architect/design lens; product-engineering stays in problem space).
- [x] The reference carries the **shared-canonical-core anchor note**: it states
  that the full eight-area taxonomy and the modality×space axis are the shared
  canonical core defined canonically in the architect reference, that this copy
  is the problem-framing *projection* of that core, and that only the area
  selection, the consult triggers, and the lens paragraph differ — so the two
  copies don't diverge. It also shows where the four selected areas sit on the
  modality×space axis and names the one adjacency seam it retains (areas 2 and 4
  as two facets of "the current system").
- [x] **Harness-agnostic detection** (grep- + read-verified): the reference
  describes discovering retrieval surfaces from the session's available
  tools/CLIs (tool search where the harness defers tools; the loaded tool list
  otherwise), contains **no hardcoded tool/CLI names**, **excludes public web
  search** as an internal surface, and requires the skill to **name the detected
  surface (or "none")** so detection is auditable rather than self-attested.
- [x] **Degradation rules** (per-clause manual QA in T5): the reference states,
  and the SKILL.md step honours, that with no surface the skill (a) asks the
  user for the missing context and lowers confidence — routing the
  lowered-confidence marker into the **intent's `Assumptions`** (and lowering
  confidence on the outcome/opportunity it leaned on), (b) never fabricates
  domain/landscape/in-flight facts, and (c) treats sensitive or read-only
  sources as ask-before-quoting. Additionally, on the **present** path a single
  unconfirmed source is carried at lowered confidence (reference states this;
  read-verified in T1).
- [x] `frame-intent/SKILL.md` gains a single **conditional** procedure step that
  detects a surface, loads the reference **only when one is detected**
  (progressive disclosure), and applies the degrade rule otherwise; the step
  names no concrete tool and uses the generic compose-if-present /
  degrade-if-absent framing (not a `research`-compose claim).
- [x] `frame-intent/references/current-state-inputs.md` wires the
  **current-landscape** area (2) into the existing **brownfield** maturity gate
  — in brownfield, when a surface is present, consult the current-landscape area;
  when absent, ask + degrade — without changing the greenfield behaviour (skip).
- [x] No registry, no shared-config file, no `~/.agentbundle` read, no new
  dependency, and no cross-pack shared artifact are introduced (verified by
  diff inspection). The four solution-design areas (3/5/6/7) do not appear.
  (Sibling SKILL.md non-edits — `de-risk-intent`, `decompose-intent` — are a
  Boundary, enforced by the T2 `git diff` check, not an acceptance criterion.)
- [x] The product-engineering pack's `[pack]` version specifically (not the
  unrelated `[pack.adapter-contract] version`) is bumped `0.2.1 → 0.3.0` in both
  `packs/product-engineering/pack.toml` and
  `packs/product-engineering/.claude-plugin/plugin.json`, preserving #300's
  enriched metadata fields (`readme`/`display_name`/`license`/`categories`/`keywords`).
  (Base is 0.2.1: `value-stream-meta-repo` shipped 0.2.0 in #298, then #300
  patch-bumped to 0.2.1 for the enriched-manifest metadata; this knowledge-surfaces
  feature takes the next minor, 0.3.0. The spec was authored against 0.1.0 and
  rebased forward through #298/#299/#300; the 0.3.0 target held — see Assumptions.)
- [x] `docs/product/changelog.md` `[Unreleased]` has an entry describing the
  new awareness behaviour.
- [x] `make build-self` has been run; `.claude-plugin/marketplace.json` reflects
  product-engineering `0.3.0`; `git status` shows no stray/untracked artifacts.
- [x] All gates green: `lint-skill-spec`, `lint-packs`, `lint-agent-artifacts`,
  `validate`, `build`, `pytest` (marketplace-aggregation suites by path).
- [x] Detection QA recorded against a **fixed driver** in two halves: (1)
  **structural (real)** — projected `SKILL.md` + reference byte-identical to
  source; (2) **decision-logic walkthrough** by an independent agent —
  surface-present cites the area the surface answers; surface-absent emits an
  explicit ask + lowered-confidence + no fabrication; sensitive-surface asks
  before quoting; brownfield-with-surface consults the current-landscape area.
  Live mock-MCP detection is *simulated* (harness limitation), logged as the
  existing deferred enhancement (`live-mock-mcp-detection-qa`).
- [x] **(Post-review follow-up, owner-requested.)** A stdlib parity lint
  `tools/lint-knowledge-surface-parity.py` (+ paired self-test
  `tools/test-lint-knowledge-surface-parity.py`) guards **every copy** of the
  shared taxonomy core against silent drift: it asserts the canonical
  `architect-design` reference carries areas {1..8}, that each copy carries
  exactly its declared set (`architect-review` the full {1..8}, `frame-intent` the
  subset {1,2,4,8}), and that every shared area's **name + question it answers**
  is byte-identical to the canonical. Both are wired into `make build-check` (via
  `tools/pre-pr-catalogue.py`) and pass.
- [x] **(Post-review follow-up, owner-requested.)** The detection audit home is
  pinned, not prose-only: the intent template's `## Assumptions` gains an optional
  `Knowledge surface:` line, and — symmetrically — architect's Stage-0
  `concept.md` gains an optional "Knowledge surface" section. Editing architect's
  shipped asset bumps the architect pack `0.4.1 → 0.4.2` (pack.toml +
  plugin.json + changelog + `marketplace.json`).
- [x] **(Per the agent skill spec — relocation done upstream by #300.)** The
  `Knowledge surface:` audit-home line is added to the intent template at its
  skill-asset home,
  `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`.
  PR #300 (enriched-pack-manifest) already relocated both the intent and rollup
  templates from `seeds/` into the owning skills' `assets/` (the pack now carries
  no `seeds/`); this PR therefore pins the audit home on the asset #300 produced
  rather than performing the move itself.

## Assumptions

- Technical: product-engineering is at `[pack]` version 0.2.1 — #298 shipped the
  value-stream 0.2.0 bump, then #300 (enriched-pack-manifest) patch-bumped to
  0.2.1 and added enriched `pack.toml` metadata (`readme`/`display_name`/`license`/
  `categories`/`keywords`) (source: `packs/product-engineering/pack.toml`,
  `.claude-plugin/plugin.json`). This spec was authored against 0.1.0 and rebased
  forward through #298/#299/#300; the bump is now `0.2.1 → 0.3.0`.
- Technical: product-engineering is a user-scope-default pack, not in
  `SELF_HOST_PACKS = {core, governance-extras, user-guide-diataxis}`, so it is
  not projected into this repo's `.claude/` tree; the only working-tree
  projection effect of the bump is `marketplace.json` (source:
  `packages/agentbundle/agentbundle/build/self_host.py:95`).
- Technical: a version bump drifts top-level `.claude-plugin/marketplace.json`
  (all-packs aggregation ignores the self-host filter); `make build-self`
  refreshes it and build-check red-fails until it is run (source:
  `self_host.py:95` + prior learning).
- Technical: `frame-intent` does **not** compose with `research` and has no
  existing degrade/lower-confidence wording, so the framing must be the generic
  compose-if-present / degrade-if-absent, not architect's "as the skill already
  does when `research` is absent" (source: `grep` over
  `packs/product-engineering/` 2026-06-13).
- Technical: the intent template's `## Assumptions` section is the home for
  lowered-confidence markers (no separate Open Questions field); `de-risk-intent`
  consumes Assumptions (source:
  `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`
  — #300 relocated the template from `seeds/` to the skill's `assets/` per the
  agent skill spec; this PR pins the `Knowledge surface:` audit-home line on that
  asset).
- Technical: the current-landscape area (2) wires to the existing greenfield/
  brownfield maturity gate resolved at intake (source:
  `packs/product-engineering/.apm/skills/frame-intent/references/current-state-inputs.md`,
  `frame-intent/SKILL.md` step 1).
- Technical: the SKILL.md hard lint cap is 1000 body lines (warn at 500);
  `frame-intent` is ~75 body lines, so a single-step insertion stays far under
  cap (source: `tools/lint-skill-spec.py:490`).
- Process: changelog `[Unreleased]` is the home for user-visible skill changes;
  no RFC — the doctrine lives in the skill reference, mirroring the architect
  spec (source: `architect-knowledge-surfaces/spec.md`, owner direction).
- Product: the taxonomy is a strict four-area subset under a problem-framing
  lens (areas 1/8 PRIMARY, 2 brownfield-only, 4 light); areas 3/5/6/7 are
  deliberately omitted as solution-design; Route B (shared file) rejected, the
  reference is product-engineering-local; harness-agnostic detection with three
  honesty rails and three degrade clauses identical to architect (source: owner
  direction 2026-06-13).
- Process/version: target version is 0.3.0 for product-engineering. The pack's
  base advanced under this branch — #298 (value-stream 0.2.0), then #300
  (enriched-manifest 0.2.1); each rebase re-derived the base while the 0.3.0
  target held — a clean minor, no collision. The now-Shipped `value-stream-meta-repo`
  and `enriched-pack-manifest` work is left untouched (source: user confirmation
  2026-06-13; rebases onto #298/#299/#300).
- Process: post-review, the owner asked to build the two quality-engineer
  follow-ups now (the cross-copy parity gate + the audit-home template pins). The
  symmetric architect concept pin pulled the architect pack into this PR with a
  `0.4.1 → 0.4.2` bump (architect was 0.4.0 at #299, patch-bumped to 0.4.1 by
  #300's enriched-manifest sweep) — a deliberate, owner-requested scope
  expansion beyond the original product-engineering-only Boundaries (source: user
  instruction 2026-06-13).
- Technical: the architect reference's lens paragraph already reserves the
  problem-framing ("business domain first") projection for product-engineering,
  so the strict-subset claim is anchored, not invented (source:
  `packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md:11-16`).
