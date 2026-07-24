# Expected-behavior transcript: propose-catalogue-pack

This document captures the `propose-catalogue-pack` flow end-to-end: the sample
pack proposal used as input, the additivity + fit test the skill performs, the
expected scaffold output on pass, and the RFC template the skill would emit. Use
this as the reference document when running AC6's live QA session.

---

## Sample pack proposal

**Proposed area:** A `desk-research` extension pack — `research-synthesis` — for
a pack that takes completed desk-research project artifacts (raw notes, source
annotations, theme clusters) and produces structured synthesis deliverables:
executive summary, insight map, and hypothesis registry.

**Submitted by:** An operator proposing to extend the existing research capability
with a structured synthesis step that the current `desk-research` pack does not cover.

---

## Additivity + fit test

`propose-catalogue-pack` tests the proposed area against two gates before scaffolding:

### Gate 1 — Additivity check

**Question:** Does the proposed pack area add capability that no existing pack
covers?

**Evaluation against local CHARTER:**
- `desk-research` covers: project-start, digest, synthesize, check skills. The
  `desk-research-project-synthesize` skill already produces a synthesis artifact.
- **Potential overlap:** The proposed `research-synthesis` pack's core job
  ("produce structured synthesis deliverables from desk-research artifacts")
  overlaps with `desk-research-project-synthesize`.

**Expected skill output (overlap found):**

```
Additivity check: FAIL — potential overlap detected.

The proposed `research-synthesis` pack's primary capability (synthesizing
desk-research artifacts into structured deliverables) overlaps with:

  desk-research / desk-research-project-synthesize
  Description: "Use to synthesize findings from a completed desk-research project
  into a structured output..."

Before proposing a new pack, assess whether the desired capability belongs as:
  (a) An extension of `desk-research-project-synthesize` (new output format or
      structured deliverable type added to an existing skill).
  (b) A new skill within the existing `desk-research` pack (additive capability
      with a distinct activation surface).
  (c) A genuinely separate pack (only if the capability requires its own
      lifecycle, dependencies, or scope that the existing pack cannot accommodate).

Recommendation: discuss with the operator whether option (a) or (b) satisfies
the need before proposing a new pack. A new pack is the right answer only when
the existing pack genuinely cannot accommodate the capability.

Proceeding would create redundant activation surfaces. Aborting.
```

---

### Alternative input: proposal that passes additivity

**Revised proposed area:** A `diagramming` pack — skills for producing architecture
diagrams, sequence diagrams, ER diagrams, and state machine diagrams from structured
descriptions. Covers: `diagram-architecture`, `diagram-sequence`, `diagram-erd`,
`diagram-state-machine`.

**Additivity check against local CHARTER:**
- No existing pack covers diagramming-as-a-primary-skill. `architect-design` and
  `architect-review` reference diagrams but do not produce them. The `mermaid-renderer`
  skill (if present) renders pre-written Mermaid syntax but does not author diagrams
  from descriptions.
- **No overlap detected.** Additive.

### Gate 2 — Fit check (four CHARTER principles)

The four principles tested (from `docs/CHARTER.md § Principles`):

1. **Universal across tech stacks.** Does the pack work for any adopter, regardless
   of framework or language? (Opt-in accelerator packs are allowed to be tech-
   stack-specific — they clear the remaining three instead of this one.)
   Result: PASS — diagramming from text descriptions is not tied to any language or
   framework. The output is Mermaid syntax (text), renderable anywhere.

2. **Substantive, not duplicative.** Does it add what no existing pack already covers?
   (This is also the additivity gate — the two checks are the same question.)
   Result: PASS — no existing pack produces architecture, sequence, ER, or state
   machine diagrams from structured descriptions. Confirmed in Gate 1 above.

3. **A habit, not a tool.** Does it capture a way of working, not a piece of
   infrastructure?
   Result: PASS — diagramming during architecture and design work is a recurring
   professional habit, not a one-off tooling script.

4. **Used often enough to stick.** Is it reached for regularly, not once a year?
   Result: PASS — teams routinely produce diagrams during system design, API design,
   incident post-mortems, and onboarding. Diagram generation is a frequent enough
   act to be worth a repeatable skill surface.

**Fit check: PASS.** All four canonical CHARTER principles satisfied.

---

## Expected scaffold output (on pass)

```
Additivity check: PASS — no overlap with existing packs.
Fit check: PASS — all four CHARTER principles satisfied.

Scaffolding pack shell: packs/diagramming/

Created:
  packs/diagramming/pack.toml
  packs/diagramming/README.md
  packs/diagramming/.claude-plugin/plugin.json
  packs/diagramming/.apm/skills/diagram-architecture/SKILL.md
  packs/diagramming/.apm/skills/diagram-sequence/SKILL.md
  packs/diagramming/.apm/skills/diagram-erd/SKILL.md
  packs/diagramming/.apm/skills/diagram-state-machine/SKILL.md

Each SKILL.md contains a placeholder body with the activation surface and
boundaries fields to fill in. See the craft checklist at
.claude/skills/README.md § Authoring skills before filling in skill bodies.

Next steps:
  1. Fill in each skill's SKILL.md body per the craft checklist.
  2. Add the pack to build/recipes/self-host.toml [recipe.packs].include.
  3. Run `make build-self` to project the pack into adapter-specific locations.
  4. Review the proposed RFC below and accept or revise before opening.

Offering hand-off to RFC authoring (not auto-invoking). Reply "yes, emit RFC" to
produce the RFC, or handle RFC authoring separately.
```

---

## RFC template the skill would emit (on "yes, emit RFC")

```markdown
# RFC-XXXX: diagramming pack

- **Status:** Draft
- **Author:** <operator>
- **Date:** 2026-07-24

## Problem

No existing pack produces architecture, sequence, ER, or state machine diagrams
from structured descriptions. `architect-design` and `architect-review` reference
diagrams but do not author them. The `mermaid-renderer` skill renders pre-written
syntax but does not author diagrams from operator intent.

## Proposal

Add a `diagramming` pack with four skills:

| Skill | Activation surface |
|---|---|
| `diagram-architecture` | C4, component, deployment, or container diagram from a system description |
| `diagram-sequence` | Sequence or interaction diagram from a described flow |
| `diagram-erd` | Entity-relationship diagram from a described data model |
| `diagram-state-machine` | State machine or statechart from described states and transitions |

Output format: Mermaid syntax (primary), with PlantUML as an alternate on request.

## Additivity + fit evidence

- **Additivity:** No existing pack covers this concern. Checked against all
  installed packs — no activation-surface overlap.
- **Single authoritative source:** diagramming from descriptions is fully owned by
  this pack.
- **Operator-centric value:** architecture documentation is core operator work.
- **Adoptable independently:** requires only `core`. No credential broker required.
- **Testable:** output is text; verifiable in a QA session without live infrastructure.

## Candidates for initial primitive inventory

| Candidate | Proposed verdict | Destination skill |
|---|---|---|
| diagram-architecture | assimilate | diagram-architecture |
| diagram-sequence | assimilate | diagram-sequence |
| diagram-erd | assimilate | diagram-erd |
| diagram-state-machine | assimilate | diagram-state-machine |

## Open questions

- [ ] D1: Should PlantUML be a primary output format alongside Mermaid, or a
  secondary option only?
- [ ] D2: Should the pack depend on `core` only, or is a `mermaid-renderer`
  dependency appropriate for the render step?

## Acceptance criteria

- [ ] Pack shell scaffolded under `packs/diagramming/`.
- [ ] Four skills authored per craft checklist; activation surfaces disjoint.
- [ ] `lint-packs` and `validate` pass; `build-self --dry-run` succeeds.
- [ ] QA session exercises each skill against a sample input.
```
