# ADR-0131: Visual-target confirmation is an explicit state, and selection never implies it

- **Status:** Accepted
- **Date:** 2026-09-29
- **Areas:** experience, packaging
- **Reversibility:** medium
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0130 (the conditional, gap-routed design-to-build handoff — this record decides the precondition of that handoff's top rung); ADR-0128 (one `design-system` skill resolves project values — the rung below the one decided here); RFC-0071 (Digital Experience Doctrine — the cross-pack thread this continues)

## Decision summary

- **Decision:** We will record a visual target's disposition in one closed frontmatter field, `visual_target`, whose values are `none`, `unconfirmed`, and `confirmed`; the `approved-visual-target` rung binds composition only when that field reads `confirmed`, and an artifact without the field reads `unconfirmed`.
- **Because:** the downstream rung already requires a recorded human confirmation, and no field recorded one — so the requirement was met by reading prose and inferring, which is the failure the rung exists to prevent.
- **Applies to:** the direction artifact at `<output_dir>/direction/<slug>.md` and the three skills that name the rung — `creative-direction`, `design-system`, and `frontend-engineering`; it does not change the `status` field's vocabulary or either pack's skill inventory.
- **Tradeoff accepted:** every direction artifact written before this record reads `unconfirmed` and loses any top-rung binding it previously had by inference.
- **Revisit if:** an adopter needs to distinguish more than three dispositions, or a confirmation needs to bind an axis beyond composition, proportion, and spatial relationship.

## Context

The frontend pack's authority precedence puts `approved-visual-target` at the
top and states its precondition as `recorded-human-confirmation`. The direction
artifact that would carry that confirmation has an `## Approved visual target`
section recording the target's identity and boundaries — what it binds, what is
merely illustrative, what may adapt responsively — and nothing recording whether
a human confirmed it.

The artifact's one lifecycle field is `status`, whose values are `proposed` and
`selected`. The template documents `selected` as meaning a human confirmed the
direction. A direction and its visual target are different objects: a human can
select a direction whose target section names a reference image nobody approved
as binding, and `converge` records a delegated choice as delegated while still
writing a selected direction.

So a build resolving the top rung had two ways to reach it, and both were
inference: read `status: selected` and treat it as covering the target, or read
the target section's prose and judge that it sounded approved. Neither is a
recorded confirmation, and the rung's own precondition could not be checked.

The same skill carries a second, unrelated contradiction at the same seam. The
route table says the `inherit` route runs `frame` "scoped to the new element
against the existing goals — no fresh interrogation, no divergence, no visual
step". The shared `frame` operation it routes to says, without qualification,
"Run the interrogation". A route promising no interrogation and an operation
instructing one cannot both be followed.

## Decision

`visual_target` is a frontmatter key on the direction artifact with exactly
three values:

| Value | Meaning |
| --- | --- |
| `none` | The direction has no visual target. |
| `unconfirmed` | A target is present and no human confirmed it as composition authority. |
| `confirmed` | A human confirmed the target as composition authority. |

The field is frontmatter rather than a body line because frontmatter is where
the artifact already carries machine-read lifecycle state. The body's
`## Approved visual target` section keeps the target's identity and boundaries
and gains a `**Confirmation record:**` line carrying the confirmation's date and
where it was recorded — provenance, not a second copy of the state.

An artifact without the field reads `unconfirmed`. That is the fail-closed
answer, and it is also the only reading that is correct without migrating
artifacts that predate the field: the shipped handoff read already takes the
frontmatter as found and requires only `type:`.

Confirmation binds composition, proportion, and spatial relationships. It
supplies no colour, typography, spacing, radius, depth, or motion value; those
resolve from the rung below, as they already did.

Confirmation is a record that a human approved a target as authority. It is not
a claim that an image was inspected or measured, and it admits no
image-analysis, browser, or design-tool dependency.

The rung's condition is now a named frontmatter value, which reverses a standing
rule that a rung condition must be a property the consuming pack defines and
that an upstream template's value is an illustration rather than the condition.
That rule protected against a condition drifting when another pack edits its
template. We accept the reversal because the alternative is the defect this
record exists to remove: a condition no consumer can check, satisfied by reading
prose. The drift risk is paid for directly — a cross-tree assertion compares the
values the template declares against the values the consuming surfaces name, so
a rename on either side fails rather than passing silently. The field is
adopter-writable in the artifact the adopter controls, exactly as the `type:`
marker the same read already keys on.

Separately, the `frame` operation's interrogation instruction is scoped so it
does not apply on the `inherit` route. That route scopes the new element against
existing goals and axis commitments, runs no fresh interrogation, does not
diverge or visualize, and writes no second direction document — which is what
the route table already said.

## Decision drivers

- A precondition a consumer cannot check is not a precondition.
- The two objects being conflated — a direction and its visual target — have
  different approvers and different consequences, so one field cannot carry both.
- Artifacts written before a schema change must stay correct without migration.
- The repository's own corpus is evidence, not a hypothetical. Four files sit
  under `docs/design/direction/`, and the handoff read admits three of them as
  direction artifacts — `token-verification.md` carries `type: design-system`,
  so the `type:` rule skips it. All three admitted artifacts read `unconfirmed`
  under this decision, and none of the four carries the template's `proposed` or
  `selected` vocabulary at all: one has no `status` key, two carry
  `status: active`, and the skipped one carries `status: invalidated`.

## Consequences

Good: a build can check the top rung's precondition mechanically, and the check
reds when an artifact does not carry the state. The conflation between selecting
a direction and confirming its target becomes a test rather than a reading.

Bad: every existing direction artifact loses any top-rung binding it had by
inference, and an adopter who wants that binding back must record the
confirmation explicitly.

Neutral: the `status` field is unchanged, so nothing that reads it moves.

## Alternatives considered

**Widen the `status` enum to carry target confirmation.** Rejected: it
re-couples the two decisions this record exists to separate, and it would make
every existing `selected` artifact ambiguous rather than merely unconfirmed.

**A body-only `**Disposition:**` line.** Rejected: it puts machine-read state
beside the prose describing the target, where a reader cannot tell which one a
consumer obeys, and it leaves the state unreadable from frontmatter where the
artifact's other lifecycle state lives.

**A sidecar file recording confirmations.** Rejected: it adds a second artifact
to the handoff read for one field, and the read path's slot rules would have to
grow to reach it.

**Migrate existing artifacts to carry the field.** Rejected as a larger change
than the one it avoids: the corpus already diverges from the template in more
fields than this one, so migration is its own project and the absent-field rule
makes it unnecessary for correctness.

## Confirmation

The `frontend-engineering` pack's visual-authority suite asserts the rung's
`requires` cell names `visual_target: confirmed`, and that the new rule table's
`absent-field` row reads `unconfirmed` and its `states` row enumerates the three
values. A closed retired-phrase sweep over that pack's export tree and over its
public guide asserts the superseded prose reading is gone rather than merely
outvoted by the new one. A `tests/roster/` assertion compares the values
declared in the template against those named on both consuming surfaces, so a
rename on one side reds. The `creative-direction` contract suite asserts the
template's field and closed set, that `converge` gates compositional
commitments on the confirmed reading, and that the `frame` operation's
interrogation instruction is scoped away from `inherit`. Recorded eval cases
carry the rung each disposition resolves to.
