# Resolve vs surface (`discovery-loop`)

The calibration reference for the [self-coverage gate](coverage-record.md)'s
coverage record. The loop reaches the right resolve-vs-surface call only about half
the time without a scaffold; an explicit rubric plus calibrated examples climbs
that rate. This is `discovery-loop`'s **own per-loop copy** — a distinct file from
`work-loop`'s, conforming to the **same cross-loop seam** RFC-0051 fixes, never
re-worded.

## The rubric

**Default to resolve.** Find the item's referent — practice, a standard, repo
precedent, an external system, or the spec/charter/intent. If one grounds the call,
resolve it and cite it. Confidence is not a referent.

**Surface only when a trigger fires:**

- **No referent** — novel/emergent territory no rule, precedent, or system decides.
- **Value origination** — the call is about what we *want* (the product's identity,
  the altitude bet, taste). The altitude/MVP bet is the canonical discovery
  surface: it is a value/scope call, surfaced at G1.5.
- **Irreversible + consequential** — a `one-way-door` `reversibility-class` with
  real blast radius. A *hard gate*: surface it however confident you are.
- **Value conflict** — two legitimate lenses point opposite ways (security says no,
  product says ship); adjudication needs the human at G2.
- **Failed referent** — the referent you reached for doesn't settle it, or says the
  opposite.

Blast radius, not topic, sets routing: the same question surfaces when
adopter-facing and irreversible, resolves when internal and cheap.

## Append-only

An example that stops holding earns a **new entry citing the old one** — never an
in-place edit, never a deletion — so the calibration history stays auditable. Each
entry is one read: the question, the routing (**resolve** / **surface**), the
referent or trigger, and the **tell** — the cue that should have fired.

## Examples (discovery-scoped)

- "Which product altitude — kitchen slice or whole household?" → **surface** (value
  origination, the altitude bet) at G1.5. *Tell: an altitude choice is what we
  *want*, not what a referent decides.*
- "How is this recurring-planning activity really done?" → **resolve** (referent:
  `frame-domain` wrapping `research` applied). *Tell: a domain fact is grounded, not
  guessed — and never asserted ungrounded.*
- "Does approved-learning need an audit-view screen?" → **resolve** (referent: the
  security lens's threat model over the journey). Not a human call once a lens
  grounds it.
- "Reject `cap.external-fulfillment` as over-scope?" → **resolve** (referent: the
  Scope Boundary out-of-scope register). The cascade is mechanical once the referent
  decides.
- "Ship this brief or hold for validation?" → **surface** the assumptions that are
  `to-validate` (only real users confirm them); **resolve** the `grounded` ones.
  *Tell: converged ≠ validated — desk-grounding is not a referent for user demand.*
- "A cascade would invalidate most of the matrix — auto-apply?" → **surface**
  (over the fan-out threshold; impact-before-blast). *Tell: a large blast radius is
  itself a surface trigger, however correct the edge-walk.*
- *Parent pre-decided the value calls → resolve, don't re-surface.* When every
  candidate surface item traces to a referent RFC-0053 / RFC-0048 already cited, the
  honest output is a recommendation, not a question. *Tell: a child must not
  re-litigate what the foundation settled.*
