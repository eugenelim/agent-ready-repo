# Code-intelligence golden composition example

- **Slug:** `code-intelligence-golden-composition-example`
- **Status:** Fulfilled
- **Accepted:** 2026-10-08 by eugenelim at closeout: shaping-reviewed and de-risked 2026-10-04, its spec approved for build and delivered in PR #1517.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:optional-code-intelligence-composition
- **Shaping-reviewed:** 2026-10-04
- **De-risked:** 2026-10-04
- **Decomposed:** 2026-10-04 spec
- **Governed by:** [RFC-0079](../../rfc/0079-codebase-context-pack.md)
- **Fulfilled:** 2026-10-08 eugenelim: spec code-intelligence-golden-composition-example Shipped in 46e064fc6 (#1517); verified on main: references/composition-example.md, pack 0.1.4 in pack.toml and plugin.json, changelog [code-intelligence][0.1.4], SKILL.md/README/how-to route to the example. The five-reader validation hook was not run and stays with the CAP-0011 owner.

## Outcome

- **Input (steerable):** Worked composition examples and evaluations that show
  the `code-intelligence` pack contributing native provider evidence, carrying
  its own limits, and degrading to a labelled repository-native baseline.
- **Outcome (lagging):** Core inquiry owners and future providers have a
  concrete reference for optional composition without mistaking Wicked Estate,
  its commands, or its current investigation patterns for the contract.
- **Guardrail:** Provider-specific commands, prerequisites, evidence fields,
  and pattern evolution remain owned by the optional pack; Core gains no engine,
  required runtime dependency, or copied provider protocol.

## Opportunity

- **Functional job:** See one end-to-end example of how a real provider improves
  a repository question while its absence and evidence limits remain honest.
- **Emotional job:** Feel confident the provider-neutral doctrine is buildable
  rather than an abstraction that hides all difficult integration details.
- **Social job:** Give provider and Core maintainers a shared example they can
  critique without making that example normative for other tools.
- **Struggling moment:** A doctrine with no complete worked example invites each
  downstream owner to interpret optional composition differently, while a
  provider-specific example can accidentally harden into a universal contract.

## Boundary

This feature owns the golden example in the `code-intelligence` pack, including
its native capability mapping, absence path, evidence caveats, and pack-local
evaluations that demonstrate contribution to grounding or exploration.

It does not standardize Wicked Estate's interface, move its mapping into Core,
close RFC-0104's retirement question, make the current five patterns exhaustive,
or stand in for a materially different provider shape or blind adopter test.

## Assumptions

- **Riskiest assumption:** Maintainers can learn the provider-neutral
  composition boundary from one concrete provider example without copying its
  commands, fields, prerequisites, or five current patterns into Core or other
  providers.
- The pack retains standalone value while demonstrating use through a Core
  inquiry seam.
- Pack-local tests can assert native provider details while Core-level tests
  stay outcome-focused.
- **Knowledge surface:** CAP-0011, RFC-0079, RFC-0104, and the shipped
  `code-intelligence` skill, capability map, evidence guide, and evaluations.

## De-risking

- **Door:** two-way. The example and its pack-local evaluations are reversible
  documentation and test assets; they do not change another provider's
  interface.
- **Prototype approach:** `prototype-led`. The shipped `code-intelligence`
  skill is the prototype: test whether its existing provider-specific parts can
  be wrapped by an explicit composition story without extracting a universal
  interface.
- **What would have to be true:** The example must show enough native detail to
  be useful, mark every provider-owned prerequisite and evidence limit, include
  both contribution and fallback, and state the reusable Core outcome without
  presenting any Wicked Estate shape as normative.
- **Test target:** The riskiest assumption named above.
- **Kill condition (predeclared 2026-10-04):** Kill the golden-example feature
  or replace it with multiple contrasting examples if a complete worked path
  cannot keep the binary/index preflight, commands, capability map, evidence
  fields, gaps, and investigation patterns pack-local; if it cannot show both a
  task-fit contribution and an absent or poor-fit fallback; or if describing the
  reusable outcome requires copying a Wicked Estate interface into Core.
- **Probe:** Audit the existing skill, capability map, evidence guide, gaps
  assessment, preflight, and fallback against that separation, then sketch the
  smallest end-to-end composition path using only their current ownership.
- **Result:** The existing pack already keeps its binary and index prerequisites,
  exact commands, five patterns, capability map, graph evidence semantics,
  known gaps, and repository-native fallback together. Core needs only the
  provider-neutral inquiry outcome and trust boundary. A worked path can cite
  those pack-owned details for a task-fit case and show the same Core inquiry
  completing through labelled fallback when the pack is absent or unsuitable.
- **Evidence class:** Construction against shipped pack artifacts. It proves
  separation is possible, not that a cold reader will avoid treating the
  example as the universal contract.
- **Verdict:** **Survived.** One concrete example can remain pack-local and
  nonnormative. Whether readers generalize correctly remains `to-validate`.
- **Reviews (2026-10-04):** Independent shaping and adversarial reviews were
  rerun after decomposition and were clean. Only this updated receipt was added
  after the final review.

```yaml validation_hook
assumption: Maintainers can learn the provider-neutral composition boundary from one concrete provider example without copying its provider-specific shapes into Core or other providers.
kill_condition: Replace the single golden example with contrasting examples or another teaching form if fewer than four of five cold readers correctly separate the Core-owned outcome and safety rules from the pack-owned prerequisites, commands, evidence fields, and investigation patterns, or if any reader concludes that another provider must emulate Wicked Estate to compose.
activity: Give five maintainers the worked example without RFC coaching. Ask each to mark which elements Core owns, which the provider owns, what happens when the provider is absent or unsuitable, and how a materially different provider could contribute natively.
```

## Decomposition

**One slice, `code-intelligence-golden-composition-example`,** projected to
`new-spec` as a delivery contract. The worked example and the pack-local
evaluations that keep it honest are one shippable teaching surface, so they
need one spec/plan pair.

### Why one slice

- An example without evaluations can silently become normative; evaluations
  without the complete worked path have no teaching surface to protect. They
  ship together.
- Documentation, native capability mapping, absence behavior, and evidence
  caveats are views of the same provider-owned example, not component slices.
- A second provider example is not cut now. Add one only if the cold-reader
  validation shows that a single golden example causes systematic
  over-generalization.

### Delivery contract

- **Outcome:** The optional `code-intelligence` pack demonstrates one complete
  provider-fit inquiry and one absent or poor-fit fallback against RFC-0079's
  outcome-level Core inquiry boundary, while a reader can tell which rules Core
  owns and which binary, index, commands, evidence fields, gaps, and
  investigation patterns remain Wicked Estate-specific.
- **Success evidence:** Pack-local evaluations exercise native prerequisites,
  invocation, evidence limits, and fallback; Core-level evaluation asserts only
  the provider-neutral outcome; the pack still works standalone; and no Core
  artifact copies Wicked Estate's interface or treats the five current patterns
  as exhaustive.
- **In scope:** The worked composition path, native capability mapping,
  provider-owned caveats and absence behavior, pack-local evaluations, and
  explicit labels separating example from contract.
- **Non-goals:** Standardizing Wicked Estate, moving its mapping into Core,
  closing RFC-0104's retirement question, proving review effectiveness, or
  representing every possible provider shape.
- **Dependencies:** Accepted RFC-0079, RFC-0104, and the shipped
  `code-intelligence` pack. FEAT-0029 and FEAT-0030 are not delivery
  prerequisites: pack-local fixtures can demonstrate the accepted outcome and
  absence boundary without pretending to be a production Core seam. A later
  delivered seam may reuse the example and evaluations.
- **Design context:** Provider-specific assertions belong in the optional
  pack's tests. Core assertions stay outcome-focused so another provider can
  compose without emulating Wicked Estate.
- **Questions for `new-spec`:** Which task-fit and poor-fit questions best
  expose the boundary; how a pack-local fixture represents only the accepted
  outcome rather than inventing a Core provider interface; and how the
  evaluation proves that removing the optional pack preserves Core's accepted
  outcome.
- **Provenance:** This de-risked intent, CAP-0011, Accepted RFC-0079, RFC-0104,
  and the shipped skill, capability map, evidence guide, gaps assessment, and
  evaluations in `packs/code-intelligence/`.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
- **Revision:** `working-tree-2026-10-04`
- **Authority:** eugenelim, parent capability owner
