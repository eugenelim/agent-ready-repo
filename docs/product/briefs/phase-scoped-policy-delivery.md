# Brief: phase-selected policy reaches each authoring agent

- **Slug:** `phase-scoped-policy-delivery`
- **Received:** 2026-09-03
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Ready
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

- For every supported selection key — every legal `engine-state.json.state`
  value and every reserved constant token — the same registry produces a
  deterministic ordered set of policy-family identifiers.
- A dispatched spec-author or implementer brief contains the complete teaching
  payload and family identifiers selected for that phase.
- An unknown phase, unknown family, ambiguous enforcement tier, missing module,
  or duplicate family fails before dispatch.
- For the same selection key, the *selected identifier set* is identical in the
  built `claude-code` and `codex` projections. No result is claimed for an
  untested host. Byte-equivalence of the registry file itself is not the metric:
  every adapter copies a skill directory byte-for-byte
  ([cited](../../architecture/skill-and-pack-format.md#L49)), so an empty or
  wrong registry would satisfy that already.

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
- A hard per-criterion word budget; § "Constraints / Appetite" is the single
  home for that rejection and carries its evidence.

## Current delivery contract

The current mechanism is **`Module index → select matching reference → inline
into the subagent brief`**. It is prose-directed, not mechanical. The
`operational-safety` instructions tell the orchestrator to detect failure
modes, load matching modules, and inline their contents into a
`quality-engineer` brief; `cloud-implementation-craft` uses the same steps for
an implementer brief
([cited](../../../packs/core/.apm/skills/operational-safety/SKILL.md#L51)).
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
([cited](../../architecture/skill-and-pack-format.md#L49)).
`evals/evals.json` already travels inside the optional, projected `evals/`
directory
([cited](../../architecture/pack-layout.md#L168)). A new
top-level `policies/` directory is not neutral: `CAT-S004` warns on any
top-level skill subdirectory outside `scripts`, `references`, `assets`, and
`evals`
([measured](../../../packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py#L42),
[warning site](../../../packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py#L549)).

## Delivery data contract

The delivery record is the binding between this brief and the validator. For
one dispatch it must identify:

| Field | Populated by |
| --- | --- |
| the selection key used — an `engine-state.json.state` value or a reserved constant token | D1, at selection time |
| the ordered, unique policy-family identifiers selected by that key | D1, at selection time |
| each family's binary tier, `precise` or `advisory` | D1, at selection time |
| the module identity and digest used as teaching text | D1, at selection time |
| the digest of the assembled brief handed to the dispatch seam | D2 for the spec author, D3 for the implementer, at assembly time |

**D1 fixes the whole schema but populates only the selection-time fields.** The
assembled-brief digest is a declared field that D1 leaves unpopulated, because
assembly is D2's and D3's. A D1 that had to emit that digest would need assembly,
which is the backward dependency § "Proposed slices" rules out — and D1 would not
be independently shippable.

The record does not claim that a model followed the teaching. It lets the next
capability prove that every selected family arrived and later received a
verdict.

**Who owns what, stated once.** The parent
([`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md))
owns the **tier semantics** — that every family is `precise` or `advisory`, that
a family blocks only when precise, and the conditions under which a semantic
residue may ever block. **D1 owns the family-record schema, family identity, and
registry versioning**, because the parent contains no schema: it lists "Which
policy families ship first, and which tier does each fall into?" among its
§ "Unresolved questions". A D1 spec author sent to the parent for a registry
contract would find an open question, not a contract. There is still only one
registry; D1 is its owner and cites the parent for tiers.

**An amendment is owed sideways, to the validator brief.** Splitting
ownership this way supersedes
[`policy-arrival-validator.md`](policy-arrival-validator.md)'s "The registry
contract and the tier model are the parent's; the selector and delivery are
`phase-scoped-policy-delivery`'s." Left as-is, a V1 spec author would go to the
parent for a registry contract and find only an open question. That brief already
half-agrees with the split — its § "Scope / Non-goals" → In scope names "the
family registry that `phase-scoped-policy-delivery`'s D1 owns" — so the
correction makes it internally consistent. It is owed before V1 is confirmed, and it does not bear on D1, which
owns the schema under either reading.

**A further amendment is owed upward, to the parent.** Its § "Unresolved questions"
also asks whether a `policies/` directory extends the blessed skill layout. This
brief answers it in § "Constraints / Appetite" on a `CAT-S004` measurement, so
the parent's open question should be closed against that answer rather than left
to contradict it.

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
| Selection and the record schema | D1 | which families a selection key selects, the whole delivery-record schema, and every selection-time field of it |
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
| D1 | The phase-policy registry and deterministic selector, fixing the delivery-record schema above and populating its selection-time fields from a selection key | the work-loop policy-delivery boundary, with registry data in its blessed `references/` tree and one selector in `scripts/` | table-driven tests cover every legal FSM state **and every reserved selection token**, reject malformed or duplicate families, and prove an identical selected identifier set in built `claude-code` and `codex` projections | `guides/core/reference/phase-scoped-policy-delivery.md` | 9 (raised from 8 by owner decision 2026-09-03) | none |
| D2 | Spec-author delivery — inline D1's selected teaching into the spec-author dispatch brief and pass the exact assembled artifact to the arrival gate | the `spec-author` dispatch envelope created by [`spec-author-agent.md`](spec-author-agent.md) | an end-to-end fixture enters a `SPEC-PLAN-*` state, dispatches on each tested adapter, and proves the validated brief contains exactly D1's selected ordered family set | `guides/core/reference/phase-scoped-policy-delivery.md` | 7 | after D1 and S1 |
| D3 | Implementer delivery — inline D1's selected teaching into every sequential implementer brief and pass the exact assembled artifact to the arrival gate | the work-loop sequential implementer-dispatch envelope created by [`universal-implementer-dispatch.md`](universal-implementer-dispatch.md) | an end-to-end fixture enters each implementation-bearing state, dispatches on each tested adapter, and proves no selected family is dropped, duplicated, or substituted | `guides/core/reference/phase-scoped-policy-delivery.md` | 7 | after V1 and U1 |

D1 changes adopter-visible policy declaration and diagnostics, so it names the
guide. D2 and D3 change which policy an adopter's authoring agent receives and
cite the same guide rather than creating phase-specific duplicates.

**Gating names a slice, never a capability.** A capability is a whole sibling
brief, so "after capability 1" reads as "after every slice of
`universal-implementer-dispatch`" — which includes U2, and U2 gates on D3. The
two briefs then appear to block each other although nothing real does, because
D3 needs only the *envelope*. That phantom deadlock was measured and recorded by
the sibling, under a § "Proposed slices" sub-heading titled **"Reconciliation
obligation, owed before U2 is confirmed and not before U1"**, which names the
amendment as this brief's to make: the gating "must be amended from
`capability 1` to `U1`".

That obligation reached `main` with U1, in the PR #1220 merge `d7cf1b741`
(2026-09-03), so the paragraph is readable in
[`universal-implementer-dispatch.md`](universal-implementer-dispatch.md) on this
checkout.

Settled 2026-09-03, and the wording above is that amendment:

- **D3 gates on U1**, the slice that delivers the sequential implementer
  envelope, matching the precedent already set by `spec-author-agent.md`'s S1
  ("after **U1** defines the shared envelope contract"). It does not gate on U2,
  U3, or the sibling brief as a whole.
- **D2 gates on S1**, the slice that creates the `spec-author` envelope D2
  inlines into. It does *not* gate on S2. D2's fixture "enters a `SPEC-PLAN-*`
  state", and `spec-author-agent.md` § "Proposed slices" settles that boundary by
  request kind rather than by caller: "S1 handles a create request from any
  caller, **including work-loop's first drafting entry**, and S2 handles only a
  repair request carrying sustained findings." Work-loop's first drafting entry
  is in `SPEC-PLAN-DRAFTING`, so S1 alone satisfies D2's fixture. Gating on S2
  would pull sustained-finding repair into D2's prerequisites for no reason — a
  softer instance of the same phantom deadlock.

## Constraints / Appetite

The appetite is one shared registry and selector plus two thin dispatch
integrations. A host-specific registry, a second selection language, or a new
primitive exceeds it and returns to shaping.

- Policy data stays in a blessed skill subdirectory. A top-level `policies/`
  directory is rejected because it warns under `CAT-S004`.
- The selection key is `engine-state.json.state`, plus a closed set of reserved
  constant tokens for paths that create no engine state — `DIRECT-LIGHT` is the
  only member today. A reserved token is a declared constant, never an inference
  from prose. Any *other* attribute may be added only after it becomes declared,
  tool-written data with a mechanical reader.
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
- **The two envelope-defining slices preserve one envelope contract.** If U1 or
  S1 creates incompatible dispatch inputs, D2 and D3 stop being thin
  integrations. The prerequisites are those slices, not the sibling briefs whole;
  the parent intent's § "Where the lifecycle holds, and where it breaks" states
  its blockers at capability granularity by design, and that table describes the
  lifecycle rather than setting this brief's gating.

## Ready gaps

- **Closed 2026-09-03 — Ready.** A revision-bound clean shaping review and the
  owner's explicit Ready confirmation are both on the record. The review ran one
  finding round of ten findings, four of them blocking, then two scoped
  verification passes. The blocking four were: D1's row requiring D2's assembled
  digest, which would have made D1 unshippable alone; D2 gated on S2 where S1
  suffices; the capability-level wording left standing in § "Assumptions /
  Risks"; and a Ready gap recorded `Closed` on evidence that was unreachable at
  the time. The base then advanced to `d7cf1b741`, and a final pass returned
  `Clean` bound to this revision.
- **Closed for the envelope 2026-09-03 — U1 supplied it, and it is on `main`.**
  `docs/specs/sequential-implementer-dispatch/spec.md` is `Status: Shipped` and
  `universal-implementer-dispatch.md` § "Spec map" carries its row, both reached
  `main` in the PR #1220 merge `d7cf1b741`. D3 can now name its callable surface
  against a shipped contract instead of guessing at one.

  **Partially, not wholly.** U1 shipped; U3 (extraction) and U2 (direct-light
  verdict dispatch) have not. D3 needs neither: U3 only relocates prose inside
  `work-loop`, and U2 is the light path, which D3 does not cover — that gap is
  the separate open recorded below. So D3's only remaining prerequisite is V1.

  This entry replaces the former "capability 1" blocker, which named the sibling
  brief whole and so also waited on U2; see § "Proposed slices". D1 is unaffected
  either way — it gates on nothing.

  **D3 inherits the envelope's delivery mechanism; it does not invent one.**
  `packs/core/.apm/agents/implementer.md` and the U1 spec own the two execution
  roots, the one-commit-owner-per-root rule, and the refusal on an incomplete
  brief; D3 cites them rather than restating them. The one fact that shapes D3's
  design: **craft reaches the agent inlined as prompt text.** No agent in
  `packs/core` holds the Skill tool and the same reference projects to a
  different path per adapter, so a dispatched agent cannot construct a path to a
  skill reference — the controller resolves and inlines. D3's "inline D1's
  selected teaching" uses that shipped mechanism.
- **BLOCKER for D2 only — S1 has not supplied the `spec-author` envelope.**
  `spec-author-agent.md` is `Draft` with no confirmed slice, so D2 cannot name
  its final callable surface or end-to-end fixture. D1 and D3 do not wait on it.
- **Open, owed before D3 is confirmed — D3's scope does not yet cover the
  direct-light verdict brief.** D3 is scoped to "every sequential **implementer**
  brief", verified against "each implementation-bearing state". The light path
  creates no engine state and its dispatched agent is not an implementer, which
  is why D1 reserves `DIRECT-LIGHT`. `universal-implementer-dispatch.md` records
  the same gap from the consuming side and leaves two options open: widen D3, or
  let U2 own light-path assembly. Neither is chosen, and neither bears on D1.
- **Open — the registry schema and exact files under the work-loop skill's
  blessed `references/` tree are not chosen.** No policy-family registry exists
  in runtime sources. Search:

  ```text
  rg -n "policy[_ -]famil|phase[_ -]polic|selected[_ -]famil|policy[_ -]verdict" \
    packs/core/.apm packages/agentbundle/agentbundle tools \
    -g '*.py' -g '*.json' -g '*.toml' -g '*.md'
  # exit 1: no matches
  ```

- **Open, decided at D1's slice confirmation — the initial phase-to-family map
  is not selected.** The parent names candidate decompositions but authorizes no
  family list. The candidates are not open-ended:
  [`guidance-activation-measurement.md`](guidance-activation-measurement.md)
  § "Scope / Non-goals" → "The local stratum — six named rules" carries a
  **floor measured 2026-09-02** that already names each rule's canonical home and
  whether it is gradable — `work-intake` public routing precedence, the
  observable-outcome rule, `new-spec` step 5a, the razor's bounded-search rung,
  repository anchoring, and cognitive-load simplification. D1 selects its initial
  families from that measured set and classifies each `precise` or `advisory`
  under the parent's tier semantics.

  D1 takes no dependency on that brief's M1 slice. M1 owns finalising that
  table's *locator* and *gradability* columns, and the same section binds
  membership independently: the
  six rules are "a floor M1 may not silently drop", and a rule that proves
  ungradable is an owner escalation rather than a substitution. So M1 can change
  how a rule is measured but not which rules are in the floor, and D1's registry
  is a *delivery* list that may diverge from the *measurement* corpus in any case.
- **Open — the dispatch API's exact byte handoff is not established.** D2 and
  D3 need a construction test showing that the artifact validated by V1 is the
  brief sent to the subagent, not a nearby copy.
The three Opens above are spec-time decisions, not Ready blockers. A Ready brief
may carry them; `author-delivery-brief`'s canonical Ready gate is the six
semantic fields, and the Spec map may be empty.

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
| phase-policy-registry-and-selector | Draft |

[`phase-policy-registry-and-selector`](../../specs/phase-policy-registry-and-selector/spec.md)
delivers D1. The Status column is auto-derived — do not hand-edit it. D2 and D3
are unconfirmed and have no spec.

## Provenance

- Parent intent:
  [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
  capability 3 in its Decomposition.
- Repository inventory:
  [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).
- Research basis for the family-level enforcement unit and precise/advisory
  boundary:
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).
