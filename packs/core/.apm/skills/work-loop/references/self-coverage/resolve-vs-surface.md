# Resolve vs surface (`work-loop`)

The calibration reference for the
[self-coverage gate](../../SKILL.md#the-self-coverage-gate)'s disposition record. The
loop reaches the right resolve-vs-surface call only about half the time without a
scaffold; an explicit rubric plus calibrated examples climbs that rate. This is
`work-loop`'s own per-loop copy of the calibration examples.

## The rubric

**Default to resolve.** Find the item's referent — practice, a standard, repo
precedent, an external system, or the spec/charter. If one grounds the call, resolve
it and cite it. Confidence is not a referent.

**Surface only when a trigger fires:**

- **No referent** — novel/emergent territory no rule, precedent, or system decides
  (Cynefin's knowable-vs-emergent split).
- **Value origination** — the call is about what we *want* (identity, naming, taste).
- **Irreversible + consequential** — a one-way door with real blast radius. A *hard
  gate*: if it can't be cleanly undone and a wrong call is costly, surface it however
  confident you are. (Two-way doors resolve fast; one-way doors don't.)
- **Value conflict** — two legitimate referents point opposite ways; adjudication
  needs an authority the loop lacks.
- **Failed referent** — the referent you reached for doesn't settle it, or says the
  opposite.

Blast radius, not topic, sets routing: the same question surfaces when adopter-facing
and irreversible, resolves when internal and cheap.

## Append-only

An example that stops holding earns a **new entry citing the old one** — never an
in-place edit, never a deletion — so the calibration history stays auditable. (Same
discipline as `docs/knowledge/patterns.jsonl`, cited as precedent, not a contract this
file depends on; it needs no `docs/CONVENTIONS.md` edit to ship.) Each entry is one
read: the question, the routing (**resolve** / **surface**), the referent or trigger,
and the **tell** — the cue that should have fired.

## Examples

*(Non-exhaustive by design.)*

- "How is the backlog handled?" → **resolve** (referent: how product teams work).
  *Tell: should not have waited to be asked.*
- "Rejection/recovery transitions?" → **resolve** (referent: established checkpointer
  patterns). Not a judgment call.
- "Rename the **pack**?" → **surface** (adopter-facing identity, irreversible). "Name
  an **internal** library?" → **resolve** (cheaply changed). Same question, opposite
  routing. *Tell: ask who sees the name and how reversibly before calling it a value.*
- "Deploy the distributed system?" → **initially surfaced** (charter insufficient) →
  later **largely resolved** by a new reversibility model (autonomous on ephemeral
  envs; human only at prod/irreversible exits). *Tell: routing isn't static — a new
  model can convert a surface into a mostly-resolved call; re-run it.*
- *Parent pre-decided the value calls → resolve, don't re-surface.* When every
  candidate surface item traces to a referent the parent already cited, the honest
  output is a recommendation, not a question. *Tell: a child must not re-litigate what
  the foundation settled.*
- *A mechanism gap is groundable even when the precedent doesn't transfer verbatim.*
  When a cited precedent's *mechanism* doesn't fit, find the *property* it delivers and
  ground on that property's nearest in-repo referent. *Tell: don't escalate to the
  human just because the first precedent didn't transfer.*
- *A cited referent can say the reverse of what you claim.* Closing an item on a
  referent recalled from memory, when it actually says the opposite, is a failed
  referent. *Tell: quote the referent — don't paraphrase it from memory into agreement.*
- *Constraints are often context-scoped, not global.* Before treating a constraint as
  global, ask which context it was written for. *Tell: a cap for one loop's code-review
  may not bind another loop's design-time roster.*

*Appended by the `work-loop` self-coverage slice (spec `self-coverage-gate`):*

- *Don't fabricate an instance to satisfy a "both branches" check.* The conditional
  domain-grounding dogfood asked for a fire-branch instance, but this doctrine-only
  spec rests on **no ungrounded load-bearing domain claim** (its empirical claims are
  already referent-grounded → the *degrade* branch). → **resolve: record "fire branch
  has no honest instance here," don't manufacture one.** *Tell: when a "verify both
  branches" obligation meets an artifact that honestly exercises only one, recording
  the absence IS the pass — fabricating the other branch is the failure the check
  exists to catch.*
- *A contradiction between two of your own clauses is resolve-with-referent, not
  surface.* The spec said both "this PR seeds the reference" and "appends continue in
  the upstream source until accepted." → **resolve** (referent: the per-loop copy is a
  *distinct* file from the upstream source — this PR creates the former, the rule
  governs the latter).
  *Tell: when two clauses collide, check whether they name the same object before
  treating it as an open question.*
