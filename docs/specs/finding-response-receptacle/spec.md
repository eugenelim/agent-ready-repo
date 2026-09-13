# Spec: Finding-response receptacle

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** docs/product/intents/review-response-protocol-across-reviewer-surfaces.md
- **Contract:** none
- **Shape:** data

## Objective

An author answering a sustained review finding can record *which* answer they
gave and *why*, in the record the review already produces.

A `review-verdict.v1` finding carries two optional fields beside its status: a
`response` naming the answer given, and a `reason` giving the ground for choosing
it. The work-loop's DECIDE step states the answers available to a sustained
finding, and states that a sustained finding does not by itself require an edit.

DECIDE states them as an ordered ladder in four axes — cut, route, fix, hold —
walked until one applies, then stopped. Cut leads because the repository already
governs code changes that way: cut before adding, take the first sufficient
option and stop. The order carries its own economy. Asking whether a claim needs
to exist is cheap; tracing a check's reach, resolving an owner, or locating a
generator is not, and spending that on a claim about to be deleted is the waste
that makes review rounds long.

Neither field can change what the record decides. `status` and
`effective_severity` alone determine a finding's contribution to the verdict
state, exactly as they do today. A record whose findings carry no `response` is
valid and always was.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Interface compatibility | `packs/core/.apm/skills/work-loop/references/review-verdict-record.md` | eugenelim | The two fields in the `findings[]` schema and the unchanged disposition table | An existing record without the fields still validates |
| Maintainer procedure | `packs/core/.apm/skills/work-loop/SKILL.md` DECIDE step | eugenelim, via `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md` | The answers named at the point of decision, pinned by a content test and carrying no criterion | An author reading DECIDE sees the alternatives to repair |
| Release history | `docs/product/changelog.md` | eugenelim | A `core` entry for the version this ships in | The entry names the added fields |

No architecture or operations output applies: this adds a field pair and prose to
an existing skill, and no runtime surface, boundary, or published interface
beyond the record schema itself.

## Boundaries

### Always do

- Keep the answers stated in one place inside the pack, because shipped pack
  content cannot cite this repository's internal records. State no count beside
  them: a number standing next to the set it enumerates drifts the moment the set
  moves.
- Bump `packs/core/pack.toml` and `.claude-plugin/plugin.json` together, and add
  the matching `docs/product/changelog.md` entry in the same change.

### Ask first

- Changing which answers are in the set, their names, or their order. Exercised
  once, on 2026-09-13, and recorded in
  [`notes/owner-decisions.md`](notes/owner-decisions.md).
- Giving either field any effect on verdict state, readiness, or scoring.
- Making either field required.

### Never do

- Add a new top-level directory or any new dependency.
- Let a missing, malformed, or unrecognised `response` or `reason` block, fail,
  downgrade, or score a review. The record may note it; nothing may gate on it.
- Change the disposition table's inputs. `status` and `effective_severity` remain
  the only fields that decide a finding's contribution.

## Testing Strategy

- **Field admission and vocabulary (AC-0001, AC-0002)** — TDD. A closed token set
  and a conditional required-field rule are compressible invariants, and each has
  an obvious disconfirming case.
- **Non-gating guarantee (AC-0003)** — TDD. No verdict state is computed by any
  script in this repository; the record is a prose schema an agent reads. The
  oracle is therefore structural: the named state-deciding regions must not
  mention either field, and the fields' own description must not touch `status`
  or `effective_severity`. It reds on the likeliest way gating would arrive; it
  does not and cannot prove none exists.
- **Backward compatibility (AC-0004)** — TDD. Pins the disposition table's rows
  and the optionality marking, so a change that makes either field load-bearing
  cannot land quietly.
- **Guidance placement (no criterion)** — TDD. The DECIDE step's statement of
  the answers ships as guidance, not as an obligation a completion gate
  reads. Naming them is one of the criteria carried verbatim in
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`
  under `## The deferred criteria, carried verbatim`; that intent gates promoting
  any of them back to a criterion while explicitly permitting the prose to ship. It is protected by a content assertion in the same suite,
  which is how this pack holds shipped prose that carries no criterion.

## Acceptance Criteria

- [x] **AC-0001.** A `findings[]` entry admits an optional `response` whose value
      is the token of an answer stated in the work-loop's DECIDE step, and the
      schema states
      that any other value is ignored with a note naming it, leaving the entry and
      the record valid.
- [x] **AC-0002.** The schema states that `response` and `reason` are recorded as
      a pair: a `response` without a non-empty `reason`, and a `reason` without a
      `response`, are each incomplete and ignored with a note, never rejected.
- [x] **AC-0003.** Neither `response` nor `reason` appears in the finding-
      disposition table, state precedence, or residual eligibility, and the
      schema's own description of the two fields derives or alters neither
      `status` nor `effective_severity`. This is a structural proxy over the
      named regions, not a proof that no gating exists anywhere.
- [x] **AC-0004.** The finding-disposition table's rows are unchanged by this
      change, and the schema marks both new fields optional.

## Follow-ons

- Carrying the same fields to the shaping surfaces, which produce findings a spec
  author answers and have no disposition record at all. Owner: eugenelim.
## Assumptions

- Technical: `findings[]` currently carries `{id, source_role, severity, effective_severity, citation, text, status}` with `status` one of four values (`packs/core/.apm/skills/work-loop/references/review-verdict-record.md:64-88`)
- Technical: the disposition table is authoritative and keys only on `status` and `effective_severity` (same file, `## Finding disposition`)
- Technical: core pack is at 2.25.18 (`packs/core/pack.toml:3`, `.claude-plugin/plugin.json:3`)
- Process: a non-cosmetic `.apm/**` change bumps both versions and updates the pack's eval harness (`packs/AGENTS.md`)
- Process: shipped pack content carries no internal-governance citations, so the answers are stated directly rather than cited (`packs/AGENTS.md`)
- Process: shipping this guidance is permitted while its criteria stay deferred — the owning intent gates promoting them to criteria, not authoring or shipping the prose (`docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`, `## Boundary`)
