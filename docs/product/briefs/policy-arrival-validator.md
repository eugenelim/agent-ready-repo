# Brief: every selected policy has a recorded verdict

- **Slug:** `policy-arrival-validator`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft
- **Source / provenance:** Repository-origin capability 4 from
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
- **Parent intent:**
  [`docs/product/intents/cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

Before a spec author, an implementer, or a direct-light verdict dispatch
begins, a deterministic gate proves that the exact brief sent for dispatch
contains every policy family selected by
[`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md). After the
agent acts, the same validation boundary requires one verdict for every
selected family. Missing or malformed coverage is an error; only a precise
family's deterministic compliance predicate may block for non-compliance.

This brief owns the parent's **Check** layer. It cites the parent's
[`three-layer shape`](../intents/cross-adapter-behavior-enforcement.md#outcome)
and the delivery brief's data contract rather than restating either.

## Success metrics

- Every selected family has exactly one verdict in a valid output artifact;
  zero missing, duplicate, or unknown family identifiers are accepted.
- A selected family's teaching digest is present in the exact assembled brief
  before dispatch, or dispatch stops with an `ERROR` result.
- A precise-family predicate failure blocks with a stable family identifier and
  diagnostic; an advisory-family finding never changes the gate exit status.
- Malformed delivery records, briefs, verdict artifacts, and predicate results
  fail closed at one validator boundary.
- The same fixtures pass against built `claude-code` and `codex` projections.
  No result is claimed for another host.

## Scope / Non-goals

**In scope**

- A policy-brief artifact kind and a policy-verdict artifact kind at the
  existing review-artifact validation boundary.
- Pre-dispatch arrival checks against the delivery record's selected family
  identifiers, module digests, and assembled-brief digest.
- Post-action coverage checks requiring one verdict for every selected family.
- Deterministic compliance predicates for families explicitly classified
  `precise`.
- Consuming the family registry that `phase-scoped-policy-delivery`'s D1 owns
  and the family contract the parent intent owns. **This brief defines no
  registry.** It reads required-teaching and compliance metadata from D1 and
  owns only the validation integration.
- `ERROR` severity for malformed artifacts, missing arrival, missing verdicts,
  and precise-family violations.
- Gate-chain integration and tests for `claude-code` and `codex` only.

**Non-goals**

- Selecting policy families or assembling their teaching text. Capability 3
  owns both in
  [`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md).
- Creating the `spec-author` or universal implementer dispatch envelopes.
- Forcing a model to reason correctly or treating a recorded verdict as proof
  of sound judgment.
- Blocking on stylistic or otherwise semantic predicates.
- Model judges, calibration infrastructure, disputed-finding adjudication, or
  the multi-adapter eval runner.
- Host hooks or validation claims for Cursor, Copilot, Gemini, Kiro, or any
  other untested host.
- A hard per-criterion word budget.

## Existing validator boundary

Nothing currently records or checks that a selected module reached a dispatched
agent's brief. The repository inventory establishes that absence in
[`Can module arrival be checked?`](../research/phase-scoped-policy-delivery.md#3-can-module-arrival-be-checked).
The confirming searches are:

```text
rg -n "inlined.{0,40}(brief|prompt)|brief.{0,40}inlined|prompt.{0,40}module|selected modules.{0,40}brief" \
  packs/core/tests packages/agentbundle/tests tools .github
# exit 1: no matches

rg -n "developer_instructions|\bprompt\b|\bbrief\b" \
  packs/core/.apm/skills/work-loop/scripts/loop-cohort.py \
  packs/core/.apm/skills/work-loop/scripts/loop-engine.py \
  packs/core/.apm/skills/work-loop/scripts/_loop_guards.py
# exit 1: no matches
```

`review-artifact.py` is the existing safe artifact boundary. It derives a
closed path from orchestrator metadata; admits only `raw`, `adjudication`, and
`evidence`; rejects unsafe, linked, oversized, unstable, or non-UTF-8 input;
and returns only size and SHA-256 on success
([size and kinds](../../../packs/core/.apm/skills/work-loop/scripts/review-artifact.py#L20),
[safe open](../../../packs/core/.apm/skills/work-loop/scripts/review-artifact.py#L208),
[validation](../../../packs/core/.apm/skills/work-loop/scripts/review-artifact.py#L225)).
It validates artifact kinds but does not yet parse a brief or policy verdict.

## Enforcement shape

The validator follows `CAT-L031`: required teaching is data, executable
prohibitions are data, both are checked in one place, and every violation is
`Severity.ERROR`. The precedent keeps broker-specific teaching in
`_CS_REQUIRED_PHRASES_BY_BROKER`, banned argv names in `_CS_BANNED_FLAGS`, and
applies both inside `_check_credentialed_skills`
([constants](../../../packages/agentbundle/agentbundle/catalogue_tooling/lint.py#L784),
[single check](../../../packages/agentbundle/agentbundle/catalogue_tooling/lint.py#L1978)).

The enforceable guarantee is **coverage**:

- Arrival coverage: each family selected in the delivery record has its exact
  teaching identity in the brief artifact whose digest is dispatched.
- Verdict coverage: each selected family has exactly one verdict; extras,
  omissions, duplicates, and malformed verdicts are errors regardless of
  family tier.
- Compliance: only a `precise` family's registered deterministic predicate may
  turn a non-compliant verdict into a blocking error. An `advisory` family's
  verdict is recorded but cannot block.

A family is `precise` or `advisory`, never between them. The stylistic emphasis
density predicate is the measured warning: it blocked **405 of 1,477 governed
files, 27.4%**, against a **0.4% per-family budget**. This is a cited count, not
a new measurement; the grounding command is:

```text
rg -n "405 of 1,477|0.4% per-family budget" \
  docs/product/briefs/agent-authoring-input-quality.md
# lines 283-284
```

The source and its policy consequence are retained in
[`agent-authoring-input-quality.md`](agent-authoring-input-quality.md#the-rubric-is-a-deliverable-not-content-here).

## What counts as arrival

**Arrival is decided on canonical framed module bytes, not on a prose match.**
V1 cannot assert that "the teaching is present" without an equivalence rule, or
the check is undecidable and a near-miss substitution passes. So D2 emits each
included family as a canonically framed block with a recorded digest, and V1
compares digests rather than text. Its fixtures must exercise **substitution** —
a family replaced by a paraphrase fails, and a family reordered or re-indented
passes — because a check that cannot distinguish those two proves nothing.

**This brief owns validation integration only.** The registry contract and the
tier model are the parent's; the selector and delivery are
`phase-scoped-policy-delivery`'s. V1 and V2 read those and define no family
registry of their own.

## Proposed slices
**This brief does not deliver as a unit, and the order is D1 → D2 → V1 → D3.**
D1 selects and fixes the record format, D2 assembles the spec-author brief and
emits the framed digest, V1 validates that digest, and D3 then reuses the
validated contract for the implementer. V1 cannot precede D2, because there is
no digest to validate until assembly exists.


No slice is confirmed and no spec is authored. Each AC number below is a
**ceiling and a stall threshold, never a floor**. A smaller complete contract
stops early; a draft that reaches the ceiling must split or obtain an explicit
owner decision.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | Arrival and verdict coverage — add policy artifacts to the safe artifact boundary, validate the exact dispatched brief, and require one verdict per selected family | `packs/core/.apm/skills/work-loop/scripts/review-artifact.py` as the single validation boundary | construction tests reject every unsafe-artifact case already covered plus wrong brief digest, missing teaching, missing/duplicate/unknown verdicts, and prove a complete advisory-only run exits cleanly on built `claude-code` and `codex` projections | `guides/core/reference/phase-scoped-policy-delivery.md` | 10 | after D2 emits the framed digest; end-to-end dispatch proof also waits on capabilities 1 and 2 |
| V2 | Precise-family compliance — dispatch registered deterministic predicates from the same boundary while advisory findings remain non-blocking | the precise-predicate branch of `review-artifact.py`, with predicate metadata cited from D1's registry | one positive and one negative fixture per admitted precise family; mutation cases prove an advisory family cannot acquire blocking behavior and an unregistered or non-boolean predicate result fails closed | `guides/core/reference/phase-scoped-policy-delivery.md` | 8 | after V1 and owner confirmation of at least one precise family |

Both slices change adopter-visible gate results and artifact diagnostics, so
both cite the delivery guide. V2 cites V1's artifact contract and does not
create a second validator.

## Constraints / Appetite

The appetite is one extension of the existing safe artifact boundary, not a
new validation service. If safe validation cannot remain in one place, the
capability returns to shaping.

- Required teaching and compliance metadata are co-located as data, following
  the `CAT-L031` precedent.
- Coverage errors use `ERROR` severity and fail closed.
- Precise-family compliance failures may block. Advisory-family findings may
  be recorded, displayed, and measured, but never block.
- The validator consumes the exact delivery record and assembled brief from
  [`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md); it may
  not reconstruct selection from phase prose.
- Existing `review-artifact.py` confinement, hard-link, size, stability, UTF-8,
  and quiet-diagnostic guarantees remain intact.
- The first implementation and all claims cover `claude-code` and `codex` only.
- Rejected: a hard per-criterion word budget because semantic atomicity and
  testability, not text length, determine whether an AC is valid. The four
  existing rejection sites are cited by the delivery brief under
  [`Constraints / Appetite`](phase-scoped-policy-delivery.md#constraints--appetite).

## Assumptions / Risks

- **A validated brief is the dispatched brief.** If the dispatch layer copies
  or rewrites the artifact after validation, arrival coverage becomes a
  preflight claim about the wrong bytes.
- **Family identity is stable.** Renaming a family between delivery and verdict
  production could look like both an omission and an extra unless the registry
  defines versioned identity.
- **A precise predicate stays closed over artifact data.** Filesystem,
  network, model, clock, or environment-dependent checks would make the result
  non-deterministic and therefore advisory.
- **One boundary can serve both moments without conflating them.** Arrival runs
  before dispatch; verdict coverage and compliance run after the agent acts.
  Both use the same parser and registry but distinct artifact kinds.
- **Stable diagnostics do not disclose untrusted artifact content.** Adding
  family identifiers must not weaken `review-artifact.py`'s quiet refusal
  contract.

## Ready gaps (Draft only)

- **BLOCKER — D1 has not fixed the delivery-record schema.** V1 cannot define
  its parser or fixtures until
  [`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md) resolves
  the registry and record-format gap.
- **BLOCKER — the final dispatch surfaces do not exist.** End-to-end proof that
  the validated bytes are the dispatched bytes waits on capabilities 1 and 2.
- **Open — no initial precise-family set is confirmed.** The parent and sibling
  brief name candidates, but no owner-approved registry maps a family to a
  closed predicate. V2 cannot be Ready without at least one such family or an
  explicit decision to defer V2.
- **Open — policy artifact filenames and bounded locations are not chosen.**
  `review-artifact.py` currently derives only review-report filenames from
  stage, reviewer role, and `raw | adjudication | evidence`; V1 must extend
  that closed grammar without admitting arbitrary paths.
- **Open — the stable `ERROR` diagnostic record is not specified.** The current
  validator returns `VALID` or `INVALID` plus fixed codes, while `CAT-L031`
  carries `Severity.ERROR`. The spec must select one schema that preserves
  quiet diagnostics and exposes severity without reflecting artifact content.
- Ready also requires a revision-bound clean shaping review and the owner's
  explicit confirmation. Both remain outstanding.

## Rabbit holes

- Do not parse agent prose to rediscover which families should have been
  selected. The delivery record is the external binding.
- Do not count a verdict artifact's existence as coverage. Coverage is set
  equality over the selected and emitted family identifiers.
- Do not let an advisory predicate change the process exit status through a
  default severity or aggregate threshold.
- Do not route deterministic violations through a model or the
  `finding-adjudicator`.
- Do not weaken `review-artifact.py` by accepting a caller-supplied artifact
  path.
- Do not claim that brief arrival proves policy obedience.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent:
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  capability 4 in its Decomposition.
- Delivery dependency:
  [`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md).
- Repository inventory:
  [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).
- Research basis for coverage, family-level enforcement, calibration, and
  abstention:
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).
