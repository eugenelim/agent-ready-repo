# Plan: domain-anchor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/domain-anchor/SKILL.md` — plus its
projection through `make build-self`. There is no engine, no script, no contract
file (Charter Principle 3): the skill body is the producer, the agent following it
writes the artifact and its filename. The shape of the change is therefore "author
one skill body that wires two existing skills, defines a typed-artifact schema, and
carries the three-tier path-resolution doctrine," mirroring the
`research-typed-artifacts` and `research-project-start` precedents.

The riskiest part is **getting the wrapping seam right**: `research` applied mode
emits a `<topic-slug>-survey.md`, not a domain anchor (RFC-0048 note 03 / GAP-P4).
The skill must consume those findings and *re-shape* them into the typed artifact —
the survey is an input, not the output. The second-riskiest part is the **degrade
path**: with `research` / `decision-archaeology` absent the skill still has to
produce a useful artifact and be honest about what it could not ground.

Order of operations: author the SKILL.md body and its artifact schema (T1), wire
the three-tier resolution + marker (T2), wire the optional-dependency
detect-and-degrade (T3), then project and lint-verify (T4). T1–T3 all edit the same
single source file, so they are serial by construction; T4 depends on all of them.

## Constraints

- **RFC-0048 Decision 4** — the domain-anchor primitive: a typed artifact
  (real-activity grounding + best practice + naive-failure modes + MVP/appetite
  out-of-scope register), produced via `research` applied mode, with a brownfield
  current-system half via `decision-archaeology` + architecture extraction.
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
**Manual verification:** one real `domain-anchor` run against the RFC-0048
worked example (`example-assistant`), producing a single `domain-anchor.md` with
all three components (AC2) and the marker (AC6), recorded in the implementing PR.

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
  lint find the artifact by `type: domain-anchor` + canonical filename, so the path
  is free to move. Rejected: a fixed path (breaks the moment an adopter relays
  out). Traces to: AC6, AC7.
- **Standalone-useful; gate-enforcement deferred.** The skill produces on demand;
  the non-skippable "mandatory gate" property is the coordinator's (child 5).
  Traces to: AC9.

### Data & schema

The typed artifact `domain-anchor.md` — a markdown schema in the skill body, not a
serialized contract. Frontmatter + three top-level sections:

```markdown
---
type: domain-anchor
initiative: <initiative-slug>
brownfield: true | false
---

# Domain anchor — <initiative>

## Real-world activity            # AC2 · grounded by research applied mode (AC1)
- How the activity is really done (cadence/horizon, the real vs. planned gap, …)
- Best practice (cited, applied-mode confidence-tagged)
- Naive-design failure modes (the anti-pattern frame)

## Current system (brownfield)    # AC3 · omitted + noted when greenfield
- How the existing system does it (architecture extraction)
- Decision archaeology: rationale chain · alternatives · revival candidates

## Out-of-scope register          # AC4
- <excluded capability> — out because <appetite reason>

## Residual assumptions           # AC5 · what research could not ground
- <ungrounded finding> — surfaced for the human, not asserted
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
   reason.
5. **Resolve the write path** (three tiers) → create dir lazily → write
   `domain-anchor.md` with the marker. Surface ambiguity rather than guess.

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

### T1: author the SKILL.md body + typed-artifact schema

**Depends on:** none

**Tests:**
- `rg -F` asserts the body invokes `research` applied mode and states it
  consumes-and-shapes the findings (AC1).
- `rg -F` asserts the artifact schema names exactly the three components +
  residual-assumptions rule (AC2, AC4, AC5).
- `rg -F` asserts the greenfield-omits-the-brownfield-half rule (AC3).

**Approach:**
- Create `packs/product-engineering/.apm/skills/domain-anchor/SKILL.md` with
  frontmatter (`name`, `description` matching the activation contract) and the body
  sections: When to invoke · Wrapping research applied mode · The brownfield half ·
  The out-of-scope register · Residual assumptions · the artifact schema (from
  `## Design (LLD) § Data & schema`).
- Model the description on the PE-pack siblings (`frame-intent`, `decompose-intent`)
  for trigger phrasing and the do-NOT-use carve.

**Done when:** the three greps above are green and the body reads as a coherent
producer skill.

### T2: wire three-tier path resolution + the stable marker

**Depends on:** T1

**Tests:**
- `rg -F` asserts the body documents the ordered three tiers (config →
  `docs/discovery/<initiative>/domain-anchor.md` default → discover-by-marker) and
  lazy dir creation (AC7).
- `rg -F` asserts the canonical filename `domain-anchor.md` + frontmatter
  `type: domain-anchor` (AC6).
- A marker grep (`rg -F 'type: domain-anchor'`) against a fixture artifact written
  to a non-default path resolves it (AC6).

**Approach:**
- Add the "Where the artifact lives" section, modelled on
  `research-project-start` SKILL.md's resolve-or-default-or-elicit, with tier 3
  swapped to discover-by-marker (search the workspace for the canonical filename +
  `type:`); surface ambiguity (multiple/zero matches) rather than guessing.
- Point the config tier at the adopter's discovery base in `agentbundle-layout.toml`
  (RFC-0040 / ADR-0030 adopter-file `[<pack>]` mechanism — the discovery key, not the
  manifest-side `[pack.layout]` and not PE's `intents`/`rollups` table); reference
  that the exact key is deferred to the layout effort.

**Done when:** the resolution + marker greps are green and the fixture marker-search
resolves a non-default-path artifact.

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
- `make build-self` projects the new skill into `.claude/skills/` with no drift
  (AC10).
- `lint-packs` and `tools/lint-agent-artifacts.py` pass on the new skill (AC10).
- A grep asserts the body declares no hard coordinator / discovery-loop dependency,
  and the worked-example run below is driven without the coordinator (AC9).
- A real `domain-anchor` run against `example-assistant` produces a single
  `domain-anchor.md` with all three components (AC2) + the marker (AC6), recorded in
  the PR.

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
  domain anchor instead of an input to shape. Mitigation: AC1 + the Design-decisions
  "wrap, don't re-implement" entry + the explicit pipeline in State & control flow.
- **Marker drift** — the canonical filename / `type:` value diverges from what the
  (future) traceability lint and lenses expect. Mitigation: both are `Ask first`
  changes in the spec; the lint is child 4 and will resolve against this value.
- **Degrade path becomes a silent fabrication** — absent research, the agent
  invents grounding. Mitigation: AC8 + the `Never do` "no silent assertion" rule.
- **Default `docs/discovery/` home reads as net-new structure** — it is introduced
  by RFC-0048's layout note as a *resolved default*, not minted by this spec; the
  `Never do` "no new top-level directory" entry records that.

## Changelog

- 2026-06-25: initial plan.
