# Plan: frame-domain

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/frame-domain/SKILL.md` — plus its
projection through `make build-self`. There is no engine, no script, no contract
file (Charter Principle 3): the skill body is the producer, the agent following it
writes the artifacts and their filenames. The shape of the change is therefore "author
one skill body that wires two existing skills, defines two typed-artifact schemas, and
carries the three-tier path-resolution doctrine," mirroring the
`research-typed-artifacts` and `research-project-start` precedents.

The riskiest part is **getting the wrapping seam right**: `research` applied mode
emits a `<topic-slug>-survey.md`, not a Domain Framing artifact (RFC-0048 note 03 / GAP-P4).
The skill must consume those findings and *re-shape* them into the typed artifact —
the survey is an input, not the output. The second-riskiest part is the **degrade
path**: with `research` / `decision-archaeology` absent the skill still has to
produce useful artifacts and be honest about what it could not ground.

Order of operations: author the SKILL.md body and its two artifact schemas (T1), wire
the three-tier resolution + markers (T2), wire the optional-dependency
detect-and-degrade (T3), then project and lint-verify (T4). T1–T3 all edit the same
single source file, so they are serial by construction; T4 depends on all of them.

## Constraints

- **RFC-0048 Decision 4** — the frame-domain primitive: two typed artifacts —
  **Domain Framing** (real-activity grounding + best practice + naive-failure modes,
  produced via `research` applied mode, plus a brownfield current-system half via
  `decision-archaeology` + architecture extraction) and **Scope Boundary** (the
  MVP/appetite out-of-scope register).
- **RFC-0048 Decision 8 / progressive enhancement** — optional deps are Tier-1
  detect-and-degrade.
- **RFC-0048 note 08** — the config → default → discover-by-marker resolution and
  the stable marker (canonical filename + frontmatter `type:`).
- **RFC-0040 / ADR-0030** — the consolidated `agentbundle-layout.toml` adopter-file
  mechanism the config tier reads. **Note:** the read target is the adopter-file
  `[<pack>]` table, *not* the manifest-side `[pack.layout]` (which is the installer's
  default source); and `docs/discovery/` is a shared discovery-loop home, not
  `product-engineering`'s file-per-slug `intents`/`rollups` shape — so the precise
  config key is deferred to the cross-cutting layout effort (see spec § Ask first).
- **Charter Principle 3** — prompt-only; no runtime engine, script, or filename
  generator.
- **3-tier skill-prerequisite policy** — declare/detect/fail-clean for the optional
  `research` / `decision-archaeology` deps. There is no script, so there is no
  body-level `shutil.which`; for a prompt-only skill the detect primitive is **the
  agent checking its available-skills roster** — the same roster-check `new-spec`
  step 4b already relies on to decide whether an authoring skill is present.

## Construction tests

Most construction tests live per-task below. Cross-cutting:

**Integration tests:** none beyond per-task greps — the deliverable is one skill
body, not multi-module code.
**Manual verification:** one real `frame-domain` run against the RFC-0048
worked example (`example-assistant`), producing `domain-framing.md` (the two grounding
halves) and `scope-boundary.md` (the out-of-scope register) (AC2), each carrying its
marker (AC6), recorded in the implementing PR.

## Design (LLD)

`Shape: mixed`. Scaffolded sub-sections: Design decisions, Data & schema, State &
control flow, Dependencies & integration. The rest are pruned — there is no UI, no
service interface, no NFR-with-a-bar.

### Design decisions

- **One skill, in `product-engineering`, not a new pack.** The seat is product
  shaping; the worked example names it PE. Traces to: AC1, AC9.
- **Wrap, don't re-implement.** `research` applied mode and `decision-archaeology`
  are invoked as subroutines; the skill body only *shapes* their output into the
  typed artifact. Rejected: re-deriving retrieval inside the skill (duplicates the
  research pack, drifts). Traces to: AC1, AC3.
- **Marker, not path, is the contract.** Downstream lenses and the traceability
  lint find each artifact by its `type:` (`domain-framing` / `scope-boundary`) +
  canonical filename, so the path
  is free to move. Rejected: a fixed path (breaks the moment an adopter relays
  out). Traces to: AC6, AC7.
- **Standalone-useful; gate-enforcement deferred.** The skill produces on demand;
  the non-skippable "mandatory gate" property is the coordinator's (child 5).
  Traces to: AC9.

### Data & schema

Two typed artifacts — markdown schemas in the skill body, not serialized contracts.

**Domain Framing** — `domain-framing.md`. Frontmatter + two top-level component
sections plus the residual-assumptions section:

```markdown
---
type: domain-framing
initiative: <initiative-slug>
brownfield: true | false
---

# Domain framing — <initiative>

## Real-world activity            # AC2 · grounded by research applied mode (AC1)
- How the activity is really done (cadence/horizon, the real vs. planned gap, …)
- Best practice (cited, applied-mode confidence-tagged)
- Naive-design failure modes (the anti-pattern frame)

## Current system (brownfield)    # AC3 · omitted + noted when greenfield
- How the existing system does it (architecture extraction)
- Decision archaeology: rationale chain · alternatives · revival candidates

## Residual assumptions           # AC5 · what research could not ground
- <ungrounded finding> — surfaced for the human, not asserted
```

**Scope Boundary** — `scope-boundary.md`. Frontmatter + the MVP out-of-scope
register:

```markdown
---
type: scope-boundary
initiative: <initiative-slug>
---

# Scope boundary — <initiative>

## Out-of-scope register          # AC4 · the G1.5 scope-creep guard; brief inherits/refines at G3
- <excluded capability> — out because <appetite reason>
```

Traces to: AC2, AC3, AC4, AC5, AC6 · implements no `contracts/` file (prompt-only).

### State & control flow

The producer pipeline the skill body codifies:

1. Resolve the initiative + brownfield/greenfield read (frontmatter inputs).
2. **Real-world-activity half** — invoke `research` applied mode against the
   domain; consume the survey findings; shape into the *Real-world activity*
   section; carry the ungrounded residue to *Residual assumptions*.
3. **Current-system half** — if brownfield, invoke `decision-archaeology` +
   architecture extraction; shape into *Current system*. Else write the
   greenfield note and skip.
4. **Out-of-scope register** — bound the appetite; list each excluded capability +
   reason, into the *Scope Boundary* artifact.
5. **Resolve each write path** (three tiers) → create dir lazily → write
   `domain-framing.md` and `scope-boundary.md`, each with its marker. Surface
   ambiguity rather than guess.

Traces to: AC1, AC3, AC5, AC6, AC7.

### Dependencies & integration

- **`research` (applied mode)** — optional, detect-and-degrade. Present → grounds
  the real-world half; absent → best-effort grounding + flagged residue (AC8).
  Detection is the agent's roster-check (no script).
- **`decision-archaeology`** — optional, detect-and-degrade, brownfield only.
- **`agentbundle-layout.toml` discovery base** — the config tier (read-only; never
  written by this skill). The adopter-file `[<pack>]` mechanism (RFC-0040 /
  ADR-0030); the exact discovery key is the layout effort's to settle.

Traces to: AC1, AC3, AC7, AC8.

## Tasks

### T1: author the SKILL.md body + the two typed-artifact schemas

**Depends on:** none

**Tests:**
- `rg -F` asserts the body invokes `research` applied mode and states it
  consumes-and-shapes the findings (AC1).
- `rg -F` asserts the two artifact schemas name Domain Framing's two components, the
  Scope Boundary out-of-scope register, and the residual-assumptions rule (AC2, AC4, AC5).
- `rg -F` asserts the greenfield-omits-the-brownfield-half rule (AC3).

**Approach:**
- Create `packs/product-engineering/.apm/skills/frame-domain/SKILL.md` with
  frontmatter (`name`, `description` matching the activation contract) and the body
  sections: When to invoke · Wrapping research applied mode · The brownfield half ·
  The out-of-scope register · Residual assumptions · the two artifact schemas (from
  `## Design (LLD) § Data & schema`).
- Model the description on the PE-pack siblings (`frame-intent`, `decompose-intent`)
  for trigger phrasing and the do-NOT-use carve.

**Done when:** the three greps above are green and the body reads as a coherent
producer skill.

### T2: wire three-tier path resolution + the stable markers

**Depends on:** T1

**Tests:**
- `rg -F` asserts the body documents the ordered three tiers (config →
  `docs/discovery/<initiative>/domain-framing.md` and `…/scope-boundary.md`
  defaults → discover-by-marker) and
  lazy dir creation (AC7).
- `rg -F` asserts the canonical filenames `domain-framing.md` / `scope-boundary.md`
  + frontmatter `type: domain-framing` / `type: scope-boundary` (AC6).
- A marker grep (`rg -F 'type: domain-framing'`, `rg -F 'type: scope-boundary'`)
  against fixture artifacts written to a non-default path resolves them (AC6).

**Approach:**
- Add the "Where the artifacts live" section, modelled on
  `research-project-start` SKILL.md's resolve-or-default-or-elicit, with tier 3
  swapped to discover-by-marker (search the workspace for each canonical filename +
  `type:`); surface ambiguity (multiple/zero matches) rather than guessing.
- Point the config tier at the adopter's discovery base in `agentbundle-layout.toml`
  (RFC-0040 / ADR-0030 adopter-file `[<pack>]` mechanism — the discovery key, not the
  manifest-side `[pack.layout]` and not PE's `intents`/`rollups` table); reference
  that the exact key is deferred to the layout effort.

**Done when:** the resolution + marker greps are green and the fixture marker-search
resolves each artifact at a non-default path.

### T3: wire optional-dependency detect-and-degrade

**Depends on:** T2

**Tests:**
- `rg -F` asserts the body names the degrade path for absent `research` /
  `decision-archaeology` — name the gap, best-effort grounding, flag the residue
  (AC8).

**Approach:**
- Add the detect-and-degrade paragraph: detection is the agent reading whether the
  dependency skill is on its roster (no script, so no `shutil.which`); on absence,
  produce the artifact from best-effort grounding and route the ungrounded residue
  to *Residual assumptions*, never fabricating grounding or failing hard.

**Done when:** the degrade grep is green and the body is explicit that absence
degrades rather than blocks.

### T4: project, lint, and produce the worked-example artifact

**Depends on:** T1, T2, T3

**Tests:**
- `lint-packs` (source-side) validates the new skill's frontmatter / description /
  body shape (AC10); `validate` + `build` + the `packages/agentbundle` pack/contract
  tests stay green.
- `make build-self` stays drift-free. **`product-engineering` is a user-scope pack,
  *not* in this repo's self-host projection scope** (`_DEFAULT_SELF_HOST_PACKS` =
  core / governance-extras / user-guide-diataxis; no `recipes/self-host.toml`), so
  build-self does **not** project the skill into `.claude/skills/` —
  `tools/lint-agent-artifacts.py` covers the *projected* packs, not this one.
  *(Corrects the original T4 "build-self projects the new skill" wording — drift
  found and fixed in the implementing PR.)*
- A grep asserts the body declares no hard coordinator / discovery-loop dependency,
  and the worked-example run below is driven without the coordinator (AC9).
- A real `frame-domain` run against `example-assistant` produces `domain-framing.md`
  (the two grounding halves) and `scope-boundary.md` (the out-of-scope register) (AC2),
  each carrying its marker (AC6), recorded in the PR.

**Approach:**
- Run `make build-self`; confirm the projection and clean `git status` (no
  unexpected reverts to projected paths).
- Run both lint surfaces by hand (the local gate runs `lint-packs`; CI also runs
  the agent-artifact lint).
- Add the changelog `[Unreleased]` entry for the new skill (user-visible
  agent-artifact change).
- Confirm the `docs/specs/README.md` active-list row (added at spec authoring) is
  still present.

**Done when:** projection is drift-free, both lints pass, AC9's no-coordinator grep
is green, and the worked-example artifact is recorded.

## Rollout

Pure content change — a new prompt-only skill in an existing pack. No infra, no
flag, no migration, no external-system dependency. Delivery is the skill's
projection via `make build-self`; rollback is reverting the skill file. The only
sequencing constraint is internal (T1→T2→T3→T4, all on one source file). The
`product-engineering` pack version bump + PyPI/CHANGELOG handling is a release
decision surfaced at merge, per the package-release convention.

## Risks

- **Wrapping seam misread** — an implementer treats the `research` survey *as* the
  Domain Framing artifact instead of an input to shape. Mitigation: AC1 + the
  Design-decisions
  "wrap, don't re-implement" entry + the explicit pipeline in State & control flow.
- **Marker drift** — a canonical filename / `type:` value (`domain-framing` /
  `scope-boundary`) diverges from what the
  (future) traceability lint and lenses expect. Mitigation: both are `Ask first`
  changes in the spec; the lint is child 4 and will resolve against these values.
- **Degrade path becomes a silent fabrication** — absent research, the agent
  invents grounding. Mitigation: AC8 + the `Never do` "no silent assertion" rule.
- **Default `docs/discovery/` home reads as net-new structure** — it is introduced
  by RFC-0048's layout note as a *resolved default*, not minted by this spec; the
  `Never do` "no new top-level directory" entry records that.

## Changelog

- 2026-06-25: initial plan.
- 2026-06-27: renamed `domain-anchor` → `frame-domain`; split the single typed
  artifact into two — Domain Framing (`domain-framing.md`) and Scope Boundary
  (`scope-boundary.md`) — to match the restructured spec (RFC-0048 D4 + Amendments
  2026-06-26).
- 2026-06-29: implemented (T1–T4). Single skill authored at
  `packs/product-engineering/.apm/skills/frame-domain/SKILL.md` + a worked-example
  file. Corrected AC10 / T4: `product-engineering` is user-scope and out of the
  self-host projection scope, so `make build-self` does not project the skill —
  the gate is lint-packs + validate + build + pytest. Spec flipped to Shipped.
