# Plan: greenfield-inception

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **additive to `core`** and lands as a single PR (RFC-0004
atomicity, matching the prior `core`-touching specs). It adds **one orchestrating
skill** and composes machinery that already ships — no new artifact type, no new
code, no new dependency. Three surfaces:

1. **A new skill** — `init-project` under `packs/core/.apm/skills/`, the
   greenfield twin of `adapt-to-project`: trigger gate → value gate over fed-in
   discovery → foundation (ADR + `reference.md`) → walking skeleton → handoff. It
   *references* `research`, the brief, `reference.md` authoring (the arc42 asset),
   `new-spec`, and `work-loop`; it does not restate their procedures.
2. **A CONVENTIONS seed amendment** — document the **two front-doors** (greenfield
   `init-project` / brownfield `adapt-to-project`) and where each enters the loop.
3. **Three adopter guides** — a tutorial, a how-to, and an explanation under
   `docs/guides/`, authored via `new-guide` (which lives in this catalogue repo's
   `user-guide-diataxis` pack), then `make build-self` + `make build-check`.

The riskiest part is **scope discipline in the skill prose**: `init-project` must
*orchestrate, not reinvent*. The temptation is to restate `new-spec`/`work-loop`
steps or to drift toward an autonomous generator; the spec's Boundaries and the
skill's anti-patterns pin it to composition + the trigger gate. There is **no TDD
surface** — the skill is an LLM workflow over already-tested pieces, so
verification is goal-based (lint + file presence + projection) and manual QA
(walking the flow). All edits are additive; nothing is removed or renamed, so the
37+ prior specs and the existing front-door stay valid.

## Constraints

- **RFC-0021** — Decisions 1 (new `init-project` flow, not an `adapt-to-project`
  extension), 2 (value-gate-over-fed-in-discovery → foundation → walking skeleton
  → handoff; fluid-not-waterfall; scoped handoffs), 3 (trigger gate), 4
  (compose-not-autogenerate), and Open Question 1 (author the skeleton spec, hand
  the build to `work-loop`).
- **ADR-0011** — the greenfield-front-door decision, the compose-not-generate
  engine choice, discovery-fed-in-not-owned, and the resolved Open Question 1 (D6).
- **ADR-0010 / RFC-0020** — the foundation step authors `reference.md` from the
  arc42 template asset (the greenfield population path D4 names); core stays
  stack-neutral.
- **ADR-0009 / RFC-0019** — the value gate emits the first **brief**; the handoff
  feeds the plan-owned LLD loop.
- **Charter Principle 1 (Universal):** the skill is stack-agnostic — no stack baked
  in; the stack decision is the adopter's, recorded in their ADR + `reference.md`.
- **Compose-around-core:** `core` imports no code from another pack; `init-project`
  composes other skills by reference, not import.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

**Integration tests:** none beyond per-task tests — there is no new code to
integration-test; the end-to-end gate is `make build-check` green after
`make build-self` projects the new skill (T3).
**Manual verification:** walk a worked greenfield scenario through the documented
`init-project` flow (trigger gate → value gate → foundation → walking skeleton →
handoff) and confirm the documented behavior matches — recorded in the
implementing PR. This scenario is **independent of the tutorial guide** (T4): the
guide's accuracy is itself an AC, so verifying the skill against the guide would
only prove internal consistency, not correctness. Use a concrete scenario that
exercises the trigger gate **both ways** (a throwaway script → skip; a real
multi-component service → continue).

## Design (LLD)

Shape is **mixed** but this feature is a skill + a doc amendment + guides — it has
no data model, no interface surface, and no component graph of its own. The
design reduces to two sub-sections; the rest are pruned.

### Design decisions

- **Compose, don't generate.** `init-project` orchestrates already-shipped skills;
  it adds no autonomous-agent engine. *Alternative rejected:* a multi-agent
  generator (RFC-0021 D4 / AP2 survivorship-bias). Traces to: AC "anti-patterns
  decline the autonomous generator", AC "no cross-pack import" · contracts/: none.
- **Trigger gate first.** The flow self-excludes throwaways before any work.
  *Alternative rejected:* always-run (friction) / never-run (yolo). Traces to: AC
  "trigger gate as first step" · contracts/: none.
- **Author the skeleton spec, hand the build to `work-loop`** (Open Q1 / ADR-0011
  D6). `init-project` orchestrates; `work-loop` executes. *Alternative rejected:*
  `init-project` builds the skeleton itself (duplicates `work-loop`). Traces to: AC
  "walking-skeleton step" · contracts/: none.
- **Discovery fed in, not owned.** The value gate consumes a discovery shape from
  one of three sources. *Alternative rejected:* `init-project` performs research
  (bloats the flow, crosses the `research` pack's boundary). Traces to: AC "consume
  fed-in discovery" · contracts/: none.

### Dependencies & integration

The skill composes, by reference (never import):
- `research` pack `research` skill — upstream discovery producer (one of three
  feed sources).
- the **brief** layer + `receive-brief` (RFC-0019) — the value gate's output and an
  alternate discovery feed.
- the arc42 `reference.md` template asset at
  `packs/core/.apm/skills/adapt-to-project/assets/reference.md` (RFC-0020) — the
  foundation step's authoring source.
- `new-spec` — authors the walking-skeleton spec.
- `work-loop` — builds the walking skeleton and runs the downstream loop.

Coupling is documentation-level only: `init-project` names these skills and points
at the asset; it adds no code edge, so the soft ordering dependency (those specs
shipped first) is the only sequencing constraint, and it is already satisfied.

## Tasks

### T1: `init-project` skill authored (trigger gate → value gate → foundation → walking skeleton → handoff)

**Depends on:** none
**Touches:** packs/core/.apm/skills/init-project/**

**Tests:**
- Goal-based: `packs/core/.apm/skills/init-project/SKILL.md` exists with
  frontmatter that passes `tools/lint-skill-spec.py`. *(verifies AC: skill ships)*
- Goal-based: the SKILL.md procedure documents, in order, the five stages —
  trigger gate (first) / value gate over fed-in discovery (emits the brief) /
  foundation (ADR + `reference.md` from the arc42 asset) / walking skeleton
  (authored via `new-spec`, built via `work-loop`) / handoff to the normal loop.
  *(verifies ACs: trigger gate, fed-in discovery, value gate, foundation, walking
  skeleton, handoff)*
- Goal-based: the SKILL.md documents the fluid-not-waterfall posture and scoped
  handoffs. *(verifies AC: fluid + scoped handoffs)*
- Goal-based: the SKILL.md anti-patterns decline the autonomous multi-agent
  generator and forbid forcing the flow onto throwaways. *(verifies AC:
  anti-patterns)*
- Goal-based: no new top-level directory; the skill references other skills/assets
  rather than importing code. *(verifies AC: no new top-level dir / no cross-pack
  import)*
- Manual QA: the documented flow, walked against a worked greenfield scenario
  **independent of the T4 tutorial** that exercises the trigger gate both ways
  (a throwaway script → skip; a real multi-component service → continue, then a
  brief, a foundation, and a skeleton handoff), produces sensible results
  (recorded in the PR). *(verifies Testing Strategy: workflow behavior)*

**Approach:**
- Write the skill prose modelled on `adapt-to-project` / `receive-brief` shape:
  frontmatter (name, trigger description that fires on "start a new project",
  "greenfield init", "idea to repo"; do-NOT-use for an existing repo → point to
  `adapt-to-project`), a numbered procedure for the five stages, an anti-patterns
  section, and a "when this skill is wrong" note.
- For each stage, **reference** the composed skill/asset (`research`, the brief /
  `receive-brief`, the arc42 `reference.md` asset, `new-spec`, `work-loop`) and
  state the scoped handoff into the next stage — do not duplicate their procedures.
- Make the trigger gate the explicit first step with a worked yes/no example
  (throwaway script → skip; real stack decisions → continue).

**Done when:** the skill file passes `lint-skill-spec.py`, documents all five
stages + the fluid/scoped posture + the two anti-patterns, and the manual-QA walk
is recorded.

### T2: `CONVENTIONS.md` seed amendment — the two front-doors

**Depends on:** none
**Touches:** packs/core/seeds/docs/CONVENTIONS.md

**Tests:**
- Goal-based: the `CONVENTIONS.md` seed documents the two front-doors (greenfield
  `init-project` / brownfield `adapt-to-project`) and where each enters the loop.
  *(verifies AC: CONVENTIONS amendment)*

**Approach:**
- Edit the pack-source seed `packs/core/seeds/docs/CONVENTIONS.md` (not the
  projected `docs/CONVENTIONS.md` — `build-self` projects it). Add a short
  front-doors note in the how-we-work section: brownfield enters via
  `adapt-to-project`, greenfield via `init-project`; both converge on
  `brief → reference.md → spec → LLD → work-loop`.
- Keep it tight (CONVENTIONS is process); reference the skills, don't restate them.

**Done when:** the seed documents both front-doors and the projection re-renders
cleanly in T3.

### T3: `make build-self` projection + `make build-check` green

**Depends on:** T1, T2
**Touches:** dist/**, .claude/**, AGENTS.md

**Tests:**
- Goal-based: `make build-self` projects the new core skill + the CONVENTIONS seed
  cleanly; `git status` shows no unexpected reverts (guard against projection-only
  drift). *(verifies AC: build-self projects cleanly)*
- Goal-based: `make build-check` is green end to end. *(verifies AC: build-check
  green)*

**Approach:**
- Run `make build-self`, inspect `git status` for unexpected reverts to projected
  paths (a prior projection-only edit can be silently reverted), run
  `make build-check`. Resolve any projection drift in this PR.

**Done when:** both targets succeed and the projection is consistent.

### T4: Adopter guides authored via `new-guide`

**Depends on:** T1
**Touches:** docs/guides/**

**Tests:**
- Goal-based: three guide files exist under `docs/guides/` at their Diátaxis paths
  — a tutorial ("From idea to a walking skeleton"), a how-to ("Decide and record
  your foundation during inception"), and an explanation ("Why a walking skeleton
  beats a throwaway prototype"). *(verifies AC: guide files exist)*
- Manual QA: each reads accurately against the shipped skill (recorded in the PR).
  *(verifies AC: guides read accurately)*

**Approach:**
- `new-guide` lives in the non-core `user-guide-diataxis` pack — this task runs **in
  this catalogue repo**, where that pack is installed; it is not a capability
  `core` ships to adopters. Scaffold each quadrant via `new-guide` and write the
  tutorial (idea → walking skeleton end to end), the how-to (decide + record the
  foundation: the ADR + `reference.md`), and the explanation (walking skeleton vs.
  throwaway prototype; the value gate).
- The tutorial is written *from* the shipped skill; its accuracy is verified
  separately from the skill's behavior (the T1 manual-QA scenario is independent of
  it — see Construction tests) so the two checks don't collapse into one document.

**Done when:** the three guide files exist and read accurately against the
implementation.

## Rollout

Additive, single PR, no runtime behavior change for existing adopters — a brand-new
repo only gets the flow if the adopter runs `init-project`, and the trigger gate
sends throwaways straight to scaffolding. Nothing is removed or renamed, so prior
specs, the existing `adapt-to-project` front-door, and the build loop stay valid.
Reversible: removing the skill + the CONVENTIONS note + the guides leaves
everything else untouched. No infrastructure, no external-system integration, no
deployment sequencing — a pure additive skill + doc change.

## Risks

- **The skill drifts into restating composed skills or toward an autonomous
  generator.** Mitigation: the spec's Boundaries + the skill's anti-patterns pin it
  to compose-by-reference; T1's goal-based checks assert the anti-patterns are
  present.
- **The trigger gate is too vague to apply consistently.** Mitigation: T1 ships a
  worked yes/no example; the gate is the explicit first step, not buried.
- **CONVENTIONS edit ripples through the self-host projection.** Mitigation:
  additive-only; T3 runs `build-self` and guards against projection-only reverts
  before the PR opens (a known failure mode in this repo).
- **The walking skeleton decays into the throwaway it replaces.** Mitigation: the
  spec mandates it is authored as a real spec and built through `work-loop` (held
  to the feature contract), and the explanation guide (T4) makes the distinction
  explicit.

## Changelog

- 2026-06-01: initial plan (drafted from RFC-0021 + ADR-0011).
