# ADR-0128: Project token values are resolved by routes inside `design-system`, not by a second skill

- **Status:** Accepted
- **Date:** 2026-09-27
- **Areas:** experience, packaging
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0071 (Digital Experience Doctrine — D3a asked for a separate `design-system-foundations` skill, which this record answers with routes instead); ADR-0052 (renamed `design-system-foundations` → `design-system`, the name this decision keeps); ADR-0024 / RFC-0033 (agnosticism guardrails — the "no universal defaults" half this decision preserves)

## Decision summary

- **Decision:** We will keep one `design-system` skill and give it four routes that carry project value resolution, instead of adding a second skill for the foundation half.
- **Because:** the capability RFC-0071 D3a wanted is a different *state* of one job — inheriting, extending, originating, or correcting a product's system — not a different job needing its own catalogue entry.
- **Applies to:** the `experience-design` pack's design-system surface and the token artifact at `<output_dir>/tokens/<slug>.md`; it does not change `token-architecture` in the `frontend-engineering` pack.
- **Tradeoff accepted:** RFC-0071 D3a's explicit instruction to keep taxonomy derivation and foundation implementation as separate skills with distinct triggers, outputs, and reviewers is not followed; one skill now carries both, and the separation survives only as routes inside it.
- **Revisit if:** the four routes stop fitting in one always-loaded control plane, or an adopter needs to install the foundation half without the derivation half.

## Context

Two accepted records disagree about this surface, and the disagreement has
already stalled work.

RFC-0071 D3a accepted a new `design-system-foundations` skill: a distinct
installable practice that takes a token taxonomy and establishes a working
foundation for a project, with taxonomy derivation and foundation
implementation kept as separate jobs. ADR-0052 D1 renamed
`design-system-foundations` to `design-system`, on the reasoning that
"-foundations" was a qualifier that added friction.

`docs/product/intents/xd-design-system-foundations.md` records the deadlock
directly: "Two accepted records disagree, and this intent cannot be delivered
until one of them gives way. That is a decision, not an implementation task."
It also records the live cost — because only one skill exists and its published
contract says it "does not implement token values", the implementation half has
no owner in the experience-design pack at all.

Three further facts were true when this was decided.

The upstream skill already assigns the job. `creative-direction` states in four
shipped places that colour, type, spacing, and motion values are
`design-system`'s to derive — in `references/refusals.md`,
`references/visualize.md`, and twice in its artifact template. The obligation
exists upstream and no skill discharges it.

The gap has a measured cost downstream. `frontend-engineering` ships a fallback
token block — a fixed spacing base, radius set, shadow recipe, and easing pair —
reached whenever no taxonomy and no incumbent system resolve values. A taxonomy
that refuses to resolve values is one of the two conditions that reaches it, so
the pack's own "no universal defaults" promise is spent in the build step
instead of kept in the design step.

The prohibition is enforced in the right place already.
`tools/lint-experience-agnostic.py` fails on any colour literal, dimension or
duration literal, ratio literal, or named easing curve in any Markdown file
under `packs/experience-design/`. It governs what the *pack ships*, and it
cannot see what a *run writes* into an adopter's output directory. The
mechanical floor therefore already draws the line between a universal default
and a project value; only the skill's prose conflated them.

## Decision

We will keep `design-system` as one skill and express the foundation half as
routes within it.

- **D1:** `design-system` remains a single registration in the
  `experience-design` pack under the name ADR-0052 gave it. No
  `design-system-foundations` skill is added, and no skill is added per
  design-system domain.
- **D2:** The separation RFC-0071 D3a asked for is preserved as four routes
  inside the one skill — `inherit`, `extend`, `originate`, and `refine` —
  selected by whether a coherent incumbent system exists and whether the work
  is a first derivation or a correction to a shipped one. The route names
  mirror `creative-direction`'s existing route vocabulary so the two skills in
  one craft sequence use one word for one concept.
- **D3:** The pack ships no design value. Nothing in a skill, reference,
  template, or eval carries a palette, typeface, type scale, spacing rhythm,
  radius, border, shadow, breakpoint, duration, or easing value. This half of
  the old "No values, ever" invariant is retained unchanged and stays
  mechanically enforced over the whole pack.
- **D4:** A run resolves project-specific values into the artifact it writes,
  for every system domain a stated project constraint, the approved direction,
  the incumbent system, or the named target surface's own platform convention
  gives it authority to fix. A domain no authority reaches is recorded
  unresolved with the missing authority named, and is not filled with a chosen
  value.
- **D5:** The artifact keeps its address `<output_dir>/tokens/<slug>.md` and
  its `type: token-taxonomy` frontmatter identity, because downstream reads
  match that literal.

## Decision drivers

- **Catalogue surface cost.** Every registration is discovery surface an
  adopter must route among; a second design-system skill doubles the routing
  question without adding a job.
- **One name per concept.** ADR-0052 removed `-foundations` precisely because
  the qualifier added friction; reinstating it would re-add the friction that
  record paid to remove.
- **Where the prohibition can be enforced.** A rule about what the pack ships
  has a mechanical gate; a rule about what a run writes does not. Splitting the
  invariant along that line makes both halves checkable.
- **Whether the states are jobs or modes.** Inheriting an incumbent system and
  originating one from a direction share an input, an output address, an
  authority model, and an accessibility floor. They differ in which of those
  the run may move.

## Consequences

**Positive:**

- The stalled `xd-design-system-foundations` intent has a resolution and can
  close without either accepted record being silently ignored.
- `creative-direction`'s four-place handoff finally lands somewhere, so a
  direction's values have a named owner.
- The "no universal defaults" promise moves from prose into the place a gate
  can hold it, and stops being spent in the build step's fallback block.
- A build agent reading a completed artifact no longer has to act as creative
  director for routine system-level visual decisions.

**Negative:**

- RFC-0071 D3a's stated requirement for distinct triggers, outputs, and
  reviewers is not met: the routes share one trigger surface, one output
  address, and one reviewer.
- One skill now carries more responsibility, so its always-loaded body has to
  stay a control plane by discipline rather than by the natural bound a second
  skill would have imposed.
- An adopter who wanted only the foundation half cannot install it separately.
- The four shipped `digital-experience-contract.md` copies that name
  `design-system-foundations` still resolve to nothing; this record does not
  repair them.

**Revisit if:** the four routes stop fitting in one always-loaded control
plane, or an adopter needs to install the foundation half without the
derivation half.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `tools/lint-experience-agnostic.py` stays clean over
  `packs/experience-design/`, proving D3; the pack-local `design-system`
  construction test pins the four routes, the authority model, and the
  unresolved-decision rule, proving D1, D2, and D4; the cross-pack handoff
  corpus test pins the artifact address and type, proving D5.
- **Owner:** Experience Design pack maintainers.

## Alternatives considered

- **Add `design-system-foundations` as RFC-0071 D3a specified.** Rejected
  against the "one name per concept" and "catalogue surface cost" drivers: it
  reverses ADR-0052 for a distinction that is a state of one job, and asks
  adopters to route between two skills that share an input, an output address,
  and an authority model.
- **Leave the contradiction open and ship only the value resolution.**
  Rejected against "where the prohibition can be enforced": the repository
  would then carry shipped behaviour contradicting an accepted RFC with nothing
  recording why, which is the failure the root guidance against silently
  resolving documented conflicts names.
- **Move value resolution to `token-architecture` in the frontend pack.**
  Rejected against "whether the states are jobs or modes": that skill designs a
  token *implementation* architecture for a chosen technology, while this job
  is deriving what the values should be from design authority, and must stay
  technology-agnostic to serve a design-only artifact.
- **Keep the taxonomy value-free and let the build resolve everything.** This
  is the status quo. Rejected against "where the prohibition can be enforced":
  it is the condition that reaches the frontend fallback block, so it does not
  avoid universal defaults — it relocates them to a surface with less design
  context.

## References

- `docs/product/intents/xd-design-system-foundations.md` — the deadlock record
  this decision resolves.
- `docs/specs/design-system-values/spec.md` — the delivery contract that
  implements D1 through D5.
