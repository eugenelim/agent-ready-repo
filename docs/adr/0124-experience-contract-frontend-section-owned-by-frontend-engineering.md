# ADR-0124: The experience contract's frontend section is owned by `frontend-engineering`, not `core`

- **Status:** Accepted
- **Date:** 2026-09-22
- **Areas:** experience, packaging
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0057 (the pack promotion that moved the template file and deleted core's frontend skill — this record decides the section's owner label, which that one did not)

## Context

The Digital Experience Contract is a shared markdown template carried
byte-identically by four packs. Every `##` section in it names one owning
discipline in the form `## <Discipline> [owner: <pack>]`, and the contract's own
header comment makes that label operative: "each section is owned by one
discipline. Skills in that pack fill their section; skills in other packs may
READ all sections."

ADR-0057 promoted `frontend-engineering` from a `core` resident skill to a
first-class pack. Its D2 deleted `packs/core/.apm/skills/frontend-engineering/`
so that `core` claims no `frontend-engineering` relpath, and its D4 relocated the
contract template to `packs/frontend-engineering/.apm/skills/frontend-engineering/references/`.
It decided where the *file* lives. It did not decide what the *section's owner
label* says, and the label still reads `[owner: core]` in all four copies.

Two things follow from that gap. The label names a pack that has shipped no
frontend skill since ADR-0057, so the contract's ownership rule resolves to
nobody: there is no `core` skill that can fill the section. And the repository
already disagrees with itself — the ownership table in
`guides/core/explanation/digital-experience-contract.md` names
`frontend-engineering` for that row, while the contract it documents names
`core`.

The label cannot simply be corrected in place. `docs/specs/digital-experience-contract/spec.md`
is Shipped, and therefore frozen: one of its ticked acceptance criteria pins the
four discipline headings, `## Frontend Engineering [owner: core]` among them.
The repository's frozen-record convention permits exactly one mutable field on a
frozen record — `Status` — and requires a supersession pointer there to name an
ADR rather than the spec that implements the change. So changing the label
requires an ADR for that pointer to name.

## Decision

The Digital Experience Contract's Frontend Engineering section is owned by the
`frontend-engineering` pack.

- **D1:** The section heading in all four contract copies reads
  `## Frontend Engineering [owner: frontend-engineering]`.
- **D2:** The `frontend-engineering` pack is the only pack whose skills fill that
  section. Skills in the other three packs read it and, under the contract's
  graceful-capability-detection rule, mark a provisional entry
  `[provisional — frontend-engineering not installed]` rather than filling it.
- **D3:** This record supersedes, in part, the `digital-experience-contract`
  spec's ticked criterion that pins `[owner: core]` among the four discipline
  headings. That spec's `Status` line carries the pointer; its body is unchanged.

## Decision drivers

- **The label must name a pack that can act on it.** An owner label is a routing
  instruction, not a credit line; one that names a pack with no matching skill
  routes nowhere.
- **One statement of ownership, not two.** The guide and the contract already
  disagree, and a reader has no way to tell which is current.
- **The frozen record stays frozen.** Whatever mechanism corrects the label must
  not require editing a shipped spec's body.

## Consequences

**Positive:**

- The contract's ownership rule resolves for every section, so a skill reading
  the frontend section knows which pack to hand back to when it is empty.
- The guide's ownership table and the contract agree, removing a contradiction a
  reader currently has to arbitrate.
- The four copies stay byte-identical, so `check-contract-drift` continues to be
  the whole interface-compatibility gate.

**Negative:**

- An adopter running `core` without the `frontend-engineering` pack now sees a
  section owned by a pack they do not have. That is the honest outcome — the
  craft rules live in the pack, and ADR-0057 already accepted this tradeoff for
  the skill itself — but it is a visible degradation where the old label
  suggested `core` would cover it.
- The frozen `digital-experience-contract` spec now needs a reader to follow its
  `Status` pointer to learn that one of its ticked criteria no longer describes
  the shipped artifact.

**Revisit if:** `core` reacquires a frontend-engineering skill, which would make
`core` a viable owner again and reopen the choice ADR-0057 closed.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** the frontend section heading in
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`
  names `frontend-engineering`. One reading covers all four copies, because
  `check-contract-drift` fails the build-check chain on any byte difference
  between them.
- **Owner:** the `frontend-engineering` pack maintainer.

## Alternatives considered

- **Leave the label as `core`:** rejected against the first driver. Since
  ADR-0057 D2 there is no `core` frontend skill, so the ownership rule names a
  pack that cannot fill the section.
- **Edit the frozen spec's ticked criterion to name the new label:** rejected
  against the third driver. The convention forbids changing a frozen record's
  body, including by appending a line.
- **Fold the label change into ADR-0057 as an erratum:** rejected against the
  third driver as it applies to ADRs. ADR-0057 is Accepted and its prose is
  frozen; its `## Errata` section takes corrections of that record, not a new
  decision it never made. D4 placed the file; it said nothing about the label.
- **Drop the owner labels from the contract entirely:** rejected against the
  second driver. The labels are what the contract's cross-pack handoff rule
  reads; removing them would remove the mechanism rather than fix the value.

## References

- The contract template's own header comment, which makes the owner label
  operative rather than decorative.
- `guides/core/explanation/digital-experience-contract.md` § The ownership map,
  which already records `frontend-engineering` for this row.
