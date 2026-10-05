# Optional code intelligence composition

- **Slug:** `optional-code-intelligence-composition`
- **Level:** capability
- **Owner:** eugenelim
- **Status:** Draft
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none
- **De-risked:** 2026-10-04
- **Decomposed:** 2026-10-04 children
- **Governed by:** [RFC-0079](../../rfc/0079-codebase-context-pack.md)

## Outcome

- **Input (steerable):** The share of repository inquiry surfaces that can
  prove both their existing no-provider path and an attributed provider-assisted
  path, including at least two materially different native provider shapes
  across the capability.
- **Outcome (lagging):** Ongoing development can use the best code evidence
  exposed in the active environment for grounding, debugging, review,
  implementation, and other repository questions without making Core depend on
  a provider or pushing provider mechanics into every consuming workflow.
- **Guardrail:** Core still installs and completes its existing outcomes alone;
  no common provider schema, mandatory tool, fixed investigation taxonomy, or
  code-intelligence phase enters `work-loop`, spec authoring, or another main
  flow; existing authority, acceptance, privacy, and security bars do not fall.

## Opportunity

Catalogue maintainers and development agents need to use stronger repository
evidence when it is already available while keeping the portable operating
model useful in environments where it is absent, unsuitable, or unsafe to call.

- **Functional job:** Answer the repository question in front of me with the
  strongest permitted evidence available, without learning or reimplementing
  each provider's discovery, invocation, fallback, and evidence rules in every
  workflow.
- **Emotional job:** Feel confident that richer code understanding improves the
  work when it helps but cannot quietly become a prerequisite or overstate what
  a derived index knows.
- **Social job:** Be seen by adopters and reviewers as using repository evidence
  consistently and transparently across different hosts and tool ecosystems.
- **Struggling moment:** When a code-intelligence capability is present, a
  workflow either ignores useful evidence or grows a one-off integration; when
  it is absent, that integration can turn an optional accelerator into a hidden
  failure mode.

## Boundary

This capability owns the evolution of Core's existing repository-grounding and
exploration seams so their owners can discover and use suitable, already
exposed code-intelligence capabilities through native provider interfaces. It
owns the shared absence, attribution, trust, data-minimization, confinement, and
heterogeneous-provider validation posture needed to keep that composition
portable. The optional `code-intelligence` pack is the golden example and an
evaluation case, not the provider contract.

It does not select, install, authenticate, register, index, refresh, or require
a provider. It does not define a provider schema, broker, registry, fixed
capability vocabulary, investigation taxonomy, or delivery sequence. It does
not move provider concerns into `work-loop`, spec authoring, or consuming
workflows; replace repository-native inquiry; absorb the existing
`grounding-probe-extensions`, `repository-grounding-preservation`,
`internal-repo-topology`, or `code-graph-review-benchmark` outcomes; or claim
that graph assistance improves review before the benchmark establishes it.

## Assumptions

- **Riskiest assumption:** Provider descriptions and active host surfaces expose
  enough meaning for inquiry owners to make bounded, task-fit choices and
  preserve material evidence limits without a catalogue-defined schema. If
  this is false, native-shape composition becomes unreliable or recreates the
  common broker and provider contract this capability is meant to avoid.
- Existing grounding and exploration owners can be identified precisely enough
  to compose optional evidence without creating a new central router.
- At least two materially different provider shapes can improve suitable
  inquiries while preserving an equivalent no-provider outcome and acceptance
  bar.
- Code intelligence can contribute to agentic development loops through their
  existing repository questions, not only to standalone code archaeology.
- Downstream owners can keep provider-specific mechanics local while sharing
  outcome-level absence, evidence, and safety expectations.
- **Knowledge surface:** In-repository product, RFC, ADR, and work-queue corpus,
  especially RFC-0079, RFC-0104, ADR-0037, ADR-0097,
  `repository-grounding-preservation`, `grounding-probe-extensions`, and
  `code-graph-review-benchmark`. No separate enterprise knowledge surface was
  detected. This framing uses the current repository state and does not claim
  adopter validation.

## De-risking

- **Door:** one-way. Several independently owned Core surfaces and adopter
  integrations may rely on the resulting ownership and trust boundary, making
  a later reversal costly even though each individual integration is optional.
- **Prototype approach:** `validate-first`.
- **What would have to be true:** Native provider descriptions must expose
  enough task meaning and material limits for an inquiry owner to choose a
  relevant action, preserve a no-provider baseline, and explain the evidence
  without a catalogue-defined provider schema.
- **Test target:** The riskiest assumption named above.
- **Kill condition (predeclared 2026-10-04):** Kill or reframe native-shape
  composition if fewer than five of six representative repository questions
  can select either a suitable provider action or the repository-native
  baseline using only exposed provider information, or if the exercise cannot
  cover at least two materially different provider shapes without inventing a
  shared request, result, capability, provenance, or freshness schema.
- **Probe:** Six-question construction exercise using the golden example's
  shipped Wicked Estate CLI description, the editor-native definition,
  reference, and call-hierarchy capabilities documented by LSP and VS Code, and
  the repository-native baseline. The questions deliberately include both
  provider-fit and provider-misfit cases.

| Repository question | Selection from exposed information | Material limit carried forward | Shared provider schema needed? |
| --- | --- | --- | --- |
| Where is this symbol defined? | Use an exposed editor/LSP definition provider; otherwise read/search the repository | Returned locations do not establish completeness or authority | No |
| What directly calls this function? | Use an exposed LSP incoming-call or reference capability for a local answer; use the baseline when neither is exposed | Dynamic dispatch and unresolved language edges may be absent; verify load-bearing callers in source | No |
| What is the transitive blast radius and where was resolution incomplete? | Use Wicked Estate `blast-radius`, whose native result advertises unresolved, truncation, depth, and node-cap limits | The result is a floor when any limit is non-zero or reached | No |
| Is there a dependency path from symbol A to symbol B? | Use Wicked Estate `path`, whose native hops expose edge kind, confidence, provenance, and search bounds | `found: false` proves absence only when resolution and bounds are clean | No |
| Which repository instruction or decision owns this file? | Reject code intelligence for the authority claim and use effective repository guidance and decision records | Derived structure cannot establish normative ownership | No |
| Which files historically change together? | Reject the exposed symbol/navigation surfaces and use bounded Git history | Co-change is historical correlation, not a resolved dependency | No |

- **Result:** Six of six questions produced a defensible provider action or
  deliberate baseline choice. Two materially different provider shapes — a
  provider-specific graph CLI and editor/LSP capabilities — contributed without
  a common request, result, capability, provenance, or freshness schema. The
  common behavior stayed in the inquiry: attribution, caveat preservation,
  authority checks, and fallback.
- **Evidence class:** Construction and desk feasibility against shipped and
  official provider descriptions. This is not adopter validation; the
  validation hook below remains `to-validate`.
- **Verdict:** **Survived.** The result clears the predeclared five-of-six line
  at six of six and covers two native provider shapes without an invented
  provider contract. CAP-0011 may be decomposed for further shaping while the
  adoption and independent-selection claim remains subject to the real-world
  hook. RFC-0079 was accepted on 2026-10-04, so the children may now project
  delivery contracts without that projection approving or sequencing delivery.
- **Adversarial review (2026-10-04):** The construction probe was primed by
  RFC-0079 and can clear a question through the baseline even when an exposed
  provider should be task-fit. That does not undo the feasibility result or
  permit a post-hoc change to its kill condition. It prevents the result from
  counting as independent-selection or adoption evidence and tightens the
  unrun hook below.

```yaml validation_hook
assumption: Native provider descriptions expose enough meaning for inquiry owners to make bounded, task-fit choices and preserve material evidence limits without a catalogue-defined schema.
kill_condition: Kill or reframe if fewer than two of three participants independently clear at least five of six questions, if provider-fit questions pass mainly through unexplained repository-native fallback, or if participants need RFC-0079's golden-example vocabulary to identify the native action and its material evidence limits.
activity: Ask three Core maintainers or adopters in at least two live host and provider environments to route the same six questions with RFC-0079's examples withheld. Count a provider-fit question only when the participant independently selects an exposed native provider action or explains why it is unsuitable, carries a material evidence limit, and invents no shared provider contract.
```

## Decomposition

```text
CAP-0011 Optional code intelligence composition
├─ FEAT-0029 Optional intelligence in repository grounding
├─ FEAT-0030 Optional intelligence in repository exploration
├─ FEAT-0031 Code-intelligence golden composition example
└─ FEAT-0032 Native-provider selection validation
```

1. [FEAT-0029](FEAT-0029-optional-intelligence-grounding-composition.md)
   owns the independently useful grounding outcome: optional provider evidence
   may strengthen a repository constraint inquiry without changing its
   report-never-decide baseline.
2. [FEAT-0030](FEAT-0030-optional-intelligence-exploration-composition.md)
   owns the independently useful exploration outcome: development activities
   may ask richer repository questions without gaining provider ceremony.
3. [FEAT-0031](FEAT-0031-code-intelligence-golden-composition-example.md)
   owns the worked provider-specific example and its pack-local evaluations.
4. [FEAT-0032](FEAT-0032-native-provider-selection-validation.md) owns the
   blind live validation that can still reframe or kill the native-shape bet.

### Decomposition decisions

- Grounding and exploration are separate children because they answer different
  repository jobs, have different evidence authorities, and can ship and be
  tested independently. This is a value cut, not a Core component split.
- The golden example stays separate because provider commands and evidence
  mechanics belong to the optional pack, not to either Core seam.
- Live selection validation stays separate from implementation so a failed
  result can reshape the parent without being rationalized by sunk delivery.
- `grounding-probe-extensions`, `repository-grounding-preservation`,
  `internal-repo-topology`, and `code-graph-review-benchmark` remain independent
  work. None becomes a child or a prerequisite by implication.
- Each child has decomposed to one delivery contract for `new-spec`. The parent
  remains decomposed to children rather than pointing directly at those specs.
- The children are intentionally unranked. RFC-0079 is Accepted, but neither
  this tree nor the RFC's conceptual map prescribes delivery order.
- RFC acceptance settles the governing architecture; it does not automatically
  accept this product intent. CAP-0011 remains Draft until its owner makes that
  separate lifecycle decision.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0079-codebase-context-pack.md`
- **Revision:** `working-tree-2026-10-04`
- **Authority:** eugenelim, RFC author and capability owner
