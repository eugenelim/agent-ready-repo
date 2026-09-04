# Brief: phase-selected policy reaches each authoring agent

- **Slug:** `phase-scoped-policy-delivery`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft
- **Source / provenance:** Repository-origin capability 3 from
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
- **Parent intent:**
  [`docs/product/intents/cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

For `claude-code` and `codex`, a dispatched spec author or implementer receives
the policy families selected for the current work-loop phase. One shared,
phase-keyed delivery path extends the repository's existing module-selection
pattern; it does not introduce a host hook or a second policy mechanism.

This brief owns the parent's **Teach** layer. The parent owns the three-layer
architecture and lifecycle placement, so this brief relies on its
[`Where the lifecycle holds, and where it breaks`](../intents/cross-adapter-behavior-enforcement.md#where-the-lifecycle-holds-and-where-it-breaks)
table rather than repeating them.

## Success metrics

- For every supported `engine-state.json.state`, the same registry produces a
  deterministic ordered set of policy-family identifiers on `claude-code` and
  `codex`.
- A dispatched spec-author or implementer brief contains the complete teaching
  payload and family identifiers selected for that phase.
- An unknown phase, unknown family, ambiguous enforcement tier, missing module,
  or duplicate family fails before dispatch.
- The two tested adapters project byte-equivalent policy data from the same
  skill source. No result is claimed for an untested host.

## Scope / Non-goals

**In scope**

- A policy-family registry carried inside a skill directory.
- Selection keyed first by `engine-state.json.state`.
- Ordered module loading and inlining into the dispatched `spec-author` and
  `implementer` briefs.
- A delivery record containing the selected family identifiers and the exact
  teaching payload identity needed by
  [`policy-arrival-validator.md`](policy-arrival-validator.md).
- Projection and behavior tests for `claude-code` and `codex` only.
- An adopter guide for declaring, classifying, and troubleshooting a
  phase-scoped family.

**Non-goals**

- Creating the `spec-author` agent or universal sequential implementer
  dispatch. Those are capabilities 2 and 1 in the parent decomposition.
- Deciding whether a policy was obeyed. That belongs to
  [`policy-arrival-validator.md`](policy-arrival-validator.md) for precise
  predicates and to later calibrated evaluation for semantic residue.
- A model judge, finding adjudication, or multi-adapter eval runner.
- Hooks, host-native prompt interception, or a new distribution primitive.
- Cursor, Copilot, Gemini, Kiro, or any other host. They are later probes.
- `Shape:`, task verification mode, or task flavour as policy-selection keys.
- A hard per-criterion word budget.

## Current delivery contract

The current mechanism is **`Module index → select matching reference → inline
into the subagent brief`**. It is prose-directed, not mechanical. The
`operational-safety` instructions tell the orchestrator to detect failure
modes, load matching modules, and inline their contents into a
`quality-engineer` brief; `cloud-implementation-craft` uses the same steps for
an implementer brief
([cited](../../../packs/core/.apm/skills/operational-safety/SKILL.md#L45)).
The module index is a deterministic table, but an agent applies it and composes
the brief. No executable dispatcher performs that selection or insertion.
The measured repository trace records both precedents and their consumers in
[`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md#1-existing-inlining-precedents).

`engine-state.json.state` is the only current phase signal recorded as
tool-written data. Its legal FSM values are declared in
[`state-schema.md`](../../../packs/core/.apm/skills/work-loop/references/state-schema.md#fields-in-engine-statejson-phase-1).
`Shape:` is author-selected spec metadata; verification mode and task flavour
are selected or inferred in prose. A measured search found no mechanical reader
for any of them:

```text
rg -n "Shape:|verification mode|TDD|goal-based|visual/manual|infra/deploy|task flavour|task flavor" \
  packs/core/.apm/skills/work-loop/scripts
# exit 1: no matches
```

Skills are the available carrier because every adapter copies a skill directory
byte-for-byte, while projection fans the same pack source to each host
([cited](../../architecture/skill-and-pack-format.md#L28)).
`evals/evals.json` already travels inside the optional, projected `evals/`
directory
([cited](../../architecture/pack-layout.md#L161)). A new
top-level `policies/` directory is not neutral: `CAT-S004` warns on any
top-level skill subdirectory outside `scripts`, `references`, `assets`, and
`evals`
([measured](../../../packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py#L39),
[warning site](../../../packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py#L549)).

## Delivery data contract

The delivery record is the binding between this brief and the validator. For
one dispatch it must identify:

- the `engine-state.json.state` value used for selection;
- the ordered, unique policy-family identifiers selected by that value;
- each family's binary tier, `precise` or `advisory`;
- the module identity and digest used as teaching text; and
- the digest of the assembled brief that is handed to the dispatch seam.

The record does not claim that a model followed the teaching. It lets the next
capability prove that every selected family arrived and later received a
verdict.

**The registry contract and the tier model are the parent's, not this brief's.**
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md)
owns the policy-family schema, the precise-versus-advisory rule, and the tier
model. This brief owns the **selector and the delivery integration** and cites
that contract; it does not define a second registry.

## Proposed slices
**D1's selector also covers the light path, where there is no engine state.**
`engine-state.json.state` is the phase key whenever a loop exists. Direct-light
creates none, so D1 admits a single reserved `DIRECT-LIGHT` selection token for
that case. It stays deterministic — a constant, not an inference — and it keeps
selection in one owner rather than giving the light path its own mechanism.
Without it `universal-implementer-dispatch`'s U2 would require phase-selected
policy that nothing selects.

**The order is selection, then assembly, then validation, then the second
envelope — and nothing depends backward.** An earlier cut had D1 emit the digest
that `policy-arrival-validator`'s V1 checks while assembly lived in D2 and D3,
which themselves waited on V1; that is a backward dependency and no spec could
satisfy it.

| Step | Owner | Produces |
| --- | --- | --- |
| Selection and the record format | D1 | which families a phase selects, and the shape of the delivery record |
| Assembly and digest emission | D2 | the assembled brief for the spec author, and the digest over what was included |
| Validation | V1, in `policy-arrival-validator` | that every selected family appears, against D2's digest |
| Second envelope | D3 | the same assembly for the implementer, reusing the validated contract |

So the chain is D1 → D2 → V1 → D3. **Neither brief delivers as a unit**, and a
slice cut must follow that order rather than assume brief-atomic delivery.


No slice is confirmed and no spec is authored. Each AC number below is a
**ceiling and a stall threshold, never a floor**. A spec author stops below the
ceiling when the feature is already atomic and testable; reaching it triggers a
split or an explicit owner decision.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | The phase-policy registry and deterministic selector, producing the delivery record above from `engine-state.json.state` | the work-loop policy-delivery boundary, with registry data in its blessed `references/` tree and one selector in `scripts/` | table-driven tests cover every legal FSM state, reject malformed or duplicate families, and prove identical registry bytes and selected identifiers in built `claude-code` and `codex` projections | `guides/core/reference/phase-scoped-policy-delivery.md` | 8 | none |
| D2 | Spec-author delivery — inline D1's selected teaching into the spec-author dispatch brief and pass the exact assembled artifact to the arrival gate | the `spec-author` dispatch envelope created by S1 | an end-to-end fixture enters a `SPEC-PLAN-*` state, dispatches on each tested adapter, and proves the validated brief contains exactly D1's selected ordered family set | `guides/core/reference/phase-scoped-policy-delivery.md` | 7 | after D1 and S1 |
| D3 | Implementer delivery — inline D1's selected teaching into every sequential implementer brief and pass the exact assembled artifact to the arrival gate | the work-loop sequential implementer-dispatch envelope created by capability 1 | an end-to-end fixture enters each implementation-bearing state, dispatches on each tested adapter, and proves no selected family is dropped, duplicated, or substituted | `guides/core/reference/phase-scoped-policy-delivery.md` | 7 | after V1 and capability 1 |

D1 changes adopter-visible policy declaration and diagnostics, so it names the
guide. D2 and D3 change which policy an adopter's authoring agent receives and
cite the same guide rather than creating phase-specific duplicates.

## Constraints / Appetite

The appetite is one shared registry and selector plus two thin dispatch
integrations. A host-specific registry, a second selection language, or a new
primitive exceeds it and returns to shaping.

- Policy data stays in a blessed skill subdirectory. A top-level `policies/`
  directory is rejected because it warns under `CAT-S004`.
- `engine-state.json.state` is the phase key. Other attributes may be added only
  after they become declared, tool-written data with a mechanical reader.
- Every family is declared `precise` or `advisory`; no intermediate blocking
  tier exists.
- The first implementation and all claims cover `claude-code` and `codex` only.
- Delivery remains progressive: only phase-selected modules enter a brief.
- Rejected: a hard per-criterion word budget because semantic atomicity and
  testability own criterion shape. The rejection is already recorded in the
  product brief, RFC, authoring skill, and a ticked Shipped criterion
  ([cited evidence](agent-authoring-input-quality.md#L134),
  [`RFC-0099`](../../rfc/0099-cut-before-adding-and-artifact-shaping.md#L901),
  [`new-spec`](../../../packs/core/.apm/skills/new-spec/SKILL.md#L505),
  [`shaping-review-contracts`](../../specs/shaping-review-contracts/spec.md#L230)).

## Assumptions / Risks

- **The dispatch seam can pass the same validated bytes it records.** If the
  host API accepts only reconstructed prompt fields, a delivery-record digest
  can prove assembly but not handoff identity.
- **The shared registry remains portable.** Adapter-specific prompt rewriting
  could make byte identity impossible even when family coverage is equivalent;
  the contract must distinguish source-data identity from host envelope syntax.
- **Phase is sufficient for the first policy cut.** If a family needs task
  semantics that are not tool-written, it stays advisory or out of the first
  registry rather than acquiring a prose-selected blocking branch.
- **The two prerequisite agents preserve one envelope contract.** If
  capability 1 or 2 creates incompatible dispatch inputs, D2 and D3 stop being
  thin integrations.

## Ready gaps (Draft only)

- **Open — D3's end-to-end fixture surface is not chosen.** The envelope
  premise of the former blocker here is **discharged**: U1 shipped the
  sequential implementer envelope in `d7cf1b741` —
  `work-loop/SKILL.md` lines 403-404 declare sequential `implementer` dispatch,
  `implementer.md` carries the two execution roots and the pre-write refusal,
  and
  [`sequential-implementer-dispatch/spec.md`](../../specs/sequential-implementer-dispatch/spec.md)
  is `Shipped`. Amended 2026-09-04: this bullet previously read "capability 1
  has not supplied the sequential implementer envelope", which the shipped
  slice falsified. What remains genuinely open is D3's own fixture surface, and
  the `capability 1 → U1` gating token at the D3 slice row above, which
  [`universal-implementer-dispatch.md`](universal-implementer-dispatch.md)
  lines 301-305 record as owed to this brief's owner.
- **BLOCKER — S1 has not supplied the spec-author envelope.** D2 cannot name
  its final callable surface until
  [`spec-author-agent.md`](spec-author-agent.md) S1 lands. Amended from
  "capability 2" on 2026-09-03: what D2 consumes is the *envelope*, which is
  S1's deliverable, and gating on the whole capability made D2 appear to wait
  on S2 as well. This matches the slice-granular precedent that brief already
  set for its own U1 gate, and the same `capability N → slice` amendment
  [`universal-implementer-dispatch.md`](universal-implementer-dispatch.md)
  records as owed for D3.

  **A second edge remains, and it does reach S2.** D2's Verification column
  names a fixture that "enters a `SPEC-PLAN-*` state" and dispatches from it.
  Entering a `SPEC-PLAN-*` engine state and dispatching there is S2's
  deliverable, not S1's — S1 is the `new-spec` dispatch site and touches
  nothing under `work-loop/`. So D2's *envelope* dependency is S1 and its
  *end-to-end fixture* dependency is S2. Narrowing the gating token does not
  settle the fixture, and this brief's owner owes that decision before D2 is
  confirmed: either the fixture is re-scoped to what S1 can exercise, or D2's
  gating admits S2 for the fixture alone.
- **Open — the registry schema and exact files under the work-loop skill's
  blessed `references/` tree are not chosen.** No policy-family registry exists
  in runtime sources. Search:

  ```text
  rg -n "policy[_ -]famil|phase[_ -]polic|selected[_ -]famil|policy[_ -]verdict" \
    packs/core/.apm packages/agentbundle/agentbundle tools \
    -g '*.py' -g '*.json' -g '*.toml' -g '*.md'
  # exit 1: no matches
  ```

- **Open — the initial phase-to-family map is not selected.** The parent names
  candidate decompositions, but it does not authorize which families enter the
  first registry or classify each one.
- **Open — the dispatch API's exact byte handoff is not established.** D2 and
  D3 need a construction test showing that the artifact validated by V1 is the
  brief sent to the subagent, not a nearby copy.
- Ready also requires a revision-bound clean shaping review and the owner's
  explicit confirmation. Both remain outstanding.

## Rabbit holes

- Do not build a second router for each adapter. Projection differences are
  fixtures around one source registry.
- Do not infer phase from headings, task prose, filenames, or agent role when
  `engine-state.json.state` exists.
- Do not put every policy into every brief to make coverage easy. That removes
  phase scoping and defeats progressive disclosure.
- Do not treat a delivery record as proof of compliance. It proves what was
  selected and assembled; the validator owns arrival and verdict checks.
- Do not use a host hook to compensate for a missing dispatch envelope.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent:
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  capability 3 in its Decomposition.
- Repository inventory:
  [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).
- Research basis for the family-level enforcement unit and precise/advisory
  boundary:
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).
