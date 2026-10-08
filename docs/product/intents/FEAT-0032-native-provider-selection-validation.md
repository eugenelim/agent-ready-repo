# Native-provider selection validation

- **Slug:** `native-provider-selection-validation`
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:optional-code-intelligence-composition
- **Shaping-reviewed:** 2026-10-08
- **De-risked:** 2026-10-04
- **Decomposed:** 2026-10-04 spec
- **Governed by:** [RFC-0079](../../rfc/0079-codebase-context-pack.md)

## Outcome

- **Input (steerable):** Three maintainers or adopters in at least two live host
  and provider environments attempt the six-question routing exercise with
  RFC-0079's golden-example vocabulary withheld.
- **Outcome (lagging):** Maintainers know whether semantic task-fit selection
  works independently across native provider shapes or whether CAP-0011 must be
  reframed around a narrower composition contract.
- **Guardrail:** A provider-fit question cannot pass through unexplained
  repository-native fallback, and no result is converted into a provider schema,
  delivery mandate, or claim that graph-assisted review is more effective.

## Opportunity

- **Functional job:** Decide whether exposed provider information is enough for
  people and agents to choose a suitable native action, reject a poor fit, and
  carry material evidence limits without coaching.
- **Emotional job:** Know the provider-neutral bet survived contact with live
  environments rather than only a document exercise shaped by its authors.
- **Social job:** Give the capability owner falsifiable evidence for retaining,
  narrowing, or rejecting the native-shape assumption.
- **Struggling moment:** The construction exercise clears every scenario, but
  baseline fallback and RFC-derived vocabulary may have made success easier than
  independent use will be.

## Boundary

This feature owns the blind exercise, result record, and survive/reframe/kill
recommendation for CAP-0011's native-shape assumption. It uses the parent
intent's predeclared question set and adversarially tightened validation hook.

It does not implement a provider integration, compare code-review outcomes,
select a preferred vendor, require participant credentials or private repository
content, or weaken the parent boundary when a result is inconvenient.

## Assumptions

- **Riskiest assumption:** A small blind exercise with three participants across
  two live environments can support a bounded next decision by the parent owner
  instead of merely generating observations that can be rationalized afterward.
  Passing this exercise does not establish selection reliability across other
  users, repositories, or provider shapes.
- The exercise can withhold golden-example vocabulary while giving participants
  enough ordinary tool metadata to act safely.
- The same six questions remain representative enough to compare against the
  construction result without turning the test into provider trivia.
- **Knowledge surface:** CAP-0011's predeclared construction exercise,
  adversarial review hook, RFC-0079, and live tool metadata supplied within each
  participant's authorized environment.

## De-risking

- **Door:** two-way for the exercise, with a `validate-first` override because
  its recorded conclusion can reshape a capability that several owners may
  later rely on.
- **Prototype approach:** `validate-first`. Test the protocol's decision logic
  with synthetic result sets before spending participant time or treating a
  live result as evidence.
- **What would have to be true:** The predeclared scoring rules must distinguish
  independent native selection from unexplained fallback and RFC vocabulary
  recall, while mapping every result to one disposition class — survive, do not
  survive unchanged, or inconclusive — without post-hoc threshold changes.
- **Test target:** The riskiest assumption named above.
- **Kill condition (predeclared 2026-10-04):** Kill or redesign this validation
  feature if the parent hook cannot assign each synthetic result below to one
  unambiguous disposition class without changing its thresholds after seeing
  the result, or if a valid run requires participant credentials, private
  repository content, or a shared provider schema.
- **Probe:** Apply the parent hook unchanged to four synthetic result sets that
  exercise its pass line and its three important failure modes.

| Synthetic result | Required disposition |
| --- | --- |
| At least two of three participants independently clear at least five questions; provider-fit choices are explained; two live shapes are covered; no counted answer invents a shared provider contract | Survive the parent assumption within the tested coverage |
| Two participants clear five questions only by using unexplained baseline fallback on provider-fit cases | Do not survive unchanged; reframe or kill native-shape selection through the parent owner |
| Participants succeed only after receiving RFC or golden-example vocabulary | Do not survive unchanged; reframe or kill independent selection through the parent owner |
| The run reaches only one provider shape or ordinary metadata is unavailable | Inconclusive; repair environment coverage and rerun without weakening the line |

- **Result:** These four synthetic results map to one action under the predeclared
  parent hook. The decision does not need provider payload normalization,
  participant secrets, or private source; it needs only authorized native tool
  metadata, the question-level observations, and environment coverage.
- **Evidence class:** Protocol construction. It shows that the exercise can
  falsify the bet and refuse inadequate coverage; only the live activity can
  supply adoption evidence.
- **Verdict:** **Survived.** The validation is decision-capable on paper and
  retains a genuine failure path. Its substantive verdict remains
  `to-validate` until the participant exercise runs.
- **Reviews (2026-10-08):** Independent intent-mode shaping and adversarial
  dispatches completed against Git blob
  `91cab3382eeba48d3ffa9f00e1ee4ea8715fa51f`. Shaping returned no `MALFORMED`
  token; the advisory assumption review returned no question or validation hook.
  The review date and this receipt are nonmaterial updates after review.
  Human confirmation of acceptance was given on 2026-10-08 after review;
  the local Ruff and mypy gates passed before the status transition.

```yaml validation_hook
assumption: A three-participant blind exercise across two live environments supports a bounded next decision by the parent owner without claiming reliability beyond the tested coverage.
kill_condition: Kill or redesign the validation if the live result cannot be classified by the predeclared parent thresholds, if environment coverage is mistaken for participant failure, or if running it requires provider-schema normalization, participant credentials, or private repository content.
activity: Run the already specified blind six-question exercise with three maintainers or adopters across at least two authorized host and provider environments, retain question-level choices and explanations, and classify the result with the synthetic decision table before interpreting it.
```

## Decomposition

**One slice, `native-provider-selection-validation`,** projected to `new-spec`
as a delivery contract. It needs one spec/plan pair: the spec freezes the blind
protocol, thresholds, evidence shape, and disposition rules; the plan prepares
and runs that protocol, with humans performing the live sessions.

### Why one slice

- Splitting protocol design from the result record would let thresholds or
  evidence rules move after results are visible. They are one falsifiable unit.
- Participant recruitment and live facilitation are execution inputs, not
  separate product features. `plan-validation` may scaffold the human-facing
  instrument inside the delivery plan, but it does not replace the governing
  spec.
- Provider-specific integrations and review-effectiveness measurement remain
  outside this feature.

### Delivery contract

- **Outcome:** A blind six-question exercise with three maintainers or adopters
  across at least two authorized host and provider environments produces a
  durable, question-level result that classifies the parent native-shape
  assumption as survive, do not survive unchanged, or inconclusive under rules
  fixed before the sessions.
- **Success evidence:** The protocol withholds RFC and golden-example
  vocabulary; distinguishes task-fit native selection from unexplained
  fallback; records a material evidence limit for counted provider-fit cases;
  refuses inadequate environment coverage; and maps the result through the
  predeclared disposition table without threshold changes.
- **In scope:** The participant brief, six-question instrument, environment and
  authorization preflight, observation and scoring form, result record,
  synthesis procedure, and routing of the disposition to CAP-0011's owner.
- **Non-goals:** Running an implementation project, selecting a vendor,
  comparing review outcomes, normalizing provider interfaces, collecting
  credentials or private repository content, or letting the result amend the
  parent without owner action.
- **Dependencies:** RFC-0079, CAP-0011's construction exercise and
  validation hook, three consenting participants, and two authorized live
  environments. Missing participants or environment coverage makes execution
  inconclusive; it does not weaken the thresholds.
- **Design context:** `plan-validation` owns the human-facing test scaffold and
  transcript synthesis frame. A human runs each session. The spec owns the
  invariant protocol and decision boundary so the validation cannot grade
  itself after seeing results.
- **Delivery answers:** The [spec](../../specs/native-provider-selection-validation/spec.md)
  owns the result destination, minimized record, environment-versus-participant
  distinction, and separate parent-owner decision. Its linked plan owns execution.
- **Provenance:** This de-risked intent, CAP-0011's predeclared hook and
  adversarial caveat, and RFC-0079.

## Unresolved questions

- Can three consenting participants and the required live environments be
  secured without answer coaching or prohibited data? The human facilitator
  resolves this before sessions; inadequate coverage is inconclusive.
- Can a second reader reproduce scoring from the minimized observations alone?
  The delivery spec requires that check before the result is owner-routed.
- What should change in CAP-0011 after the result? Its owner decides from the
  recorded evidence, including prior RFC familiarity and the coverage limits.

## Projection

The existing [delivery spec](../../specs/native-provider-selection-validation/spec.md)
owns the frozen protocol, evidence rules, and disposition thresholds. Continue
through its linked plan when delivery is authorized; this intent's acceptance
does not authorize participant recruitment or live-environment access.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
- **Revision:** `fe8a1fde266b83e23ea961a5cdd5f4fcbfb090be`
- **Authority:** eugenelim, parent capability owner
