# ADR-NNNN: <problem + chosen solution>

<!--
Title names the problem and the solution together, so the decision is legible
from the index alone — "Primary store for user activity: Postgres over DynamoDB",
not "Decision about the database". Keep it short — it identifies the decision, it
does not encode the whole rationale (that lives in the Decision section). Keep
the ADR-NNNN ordinal prefix.
-->

<!--
Authoring: substitute every placeholder (text between < and >, or YYYY-MM-DD),
then delete all guidance comments (<!-- … --> blocks). The resulting record must
pass the ADR shape lint.
-->

<!--
Parse tiers — fields the shape lint checks:

  tier T1 (value checked): Status, Date, Areas, Reversibility, Supersedes,
    Supersedes in part, Superseded by, Superseded in part, numbered D-IDs in
    ## Decision, and Revisit if in ## Consequences. When ## Confirmation is
    present, Mode, Signal, and Owner are also tier T1.

  tier T1-unchecked (field present, value not validated): Related.

  tier T2 (presence and layout, wording not checked): ## Alternatives considered,
    when the section is present.

  tier T3 (not checked): all other prose — Context, Decision narrative,
    Consequences narrative, Decision summary, and Confirmation prose.
-->

- **Status:** Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded -->
- **Date:** YYYY-MM-DD
- **Areas:** <area-token> <!-- comma-separated lowercase tokens, 1–3; e.g., tooling, security -->
- **Reversibility:** <high|low>
- **Decision-makers:** <github-handles who own the call>
- **Consulted:** <!-- whose input was sought, two-way; optional, delete if none -->
- **Informed:** <!-- who is kept up to date, one-way; optional, delete if none -->
- **Supersedes:** none <!-- none, or: ADR-NNNN -->
- **Supersedes in part:** none <!-- none, or: ADR-NNNN D1; ADR-MMMM D2, D3 -->
- **Superseded by:** none <!-- none, or: ADR-NNNN -->
- **Superseded in part:** none <!-- none, or: ADR-NNNN D1 -->
- **Related:** <!-- suggested (tier T1-unchecked — not validated by the lint):
  RFC-NNNN (the proposal this records); ADR-NNNN (the gate it rests on — the
  motivating evidence, and the split between what a scanner catches and what
  a reviewer catches); ADR-NNNN / RFC-NNNN (the modes this reuses)

  Entries separated by ;. Each entry: a bare ordinal or a /-joined pair and
  never a Markdown link, followed by a parenthetical gloss naming the
  relationship, with an em dash before a secondary clause. No trailing period.
  Because a gloss may contain ; inside a quoted clause, entries are not
  recoverable by splitting on ; alone — this is why Related is not linted. -->

<!--
Lifecycle zones:

  Live — Status is Proposed: the decision is open for discussion.

  Attested — Status is Accepted or Rejected: the call is made; body is frozen;
    Status and supersession fields may still change.

  Frozen — Status is Deprecated or Superseded: body and metadata are stable; a
    meaning-preserving correction may be appended as a dated entry in ## Errata.

  Append-only — ## Errata is present: only new dated entries may be appended;
    no other text changes.
-->

## Decision summary

<!--
OPTIONAL — a first-screen TL;DR. Include it once the ADR is long enough that the
decision isn't visible on the first screen (a multi-line title, a paragraph of
metadata, a long Context push it down); delete it on a short ADR, where five
restated lines are pure redundancy.

Every line restates something the body already carries — Decision ← Decision
section, Because ← the winning driver, Tradeoff accepted ← Consequences,
Revisit if ← Consequences. The duplication is the point: it is the first-screen
retrieval surface, so a reader gets the answer before the argument. Keep it a
fixed five-line summary of single values — NOT a place to weigh options against
each other (that belongs in Alternatives, or in an RFC). Mirror `Revisit if:`
from Consequences here verbatim — restate it, don't diverge from it.
-->

- **Decision:** We will <the choice, one sentence>.
- **Because:** <the one winning driver>.
- **Applies to:** <scope / boundary of the decision>.
- **Tradeoff accepted:** <the main negative consequence>.
- **Revisit if:** <the trigger that should reopen this decision — restated from Consequences>.

## Context

<!--
The forces at play. What is the problem we're trying to solve? What constraints
are we operating under? What did we know at the time?

Be concrete. "We need a database" is not context. "We need to store ~10M
records of user activity, query them by user_id and time range, and we have
a team of two who know Postgres" is context.

Anything that isn't true today does not belong here. (If a constraint changes
later, that's a new ADR, not an edit.)
-->

## Decision

<!--
The decision, stated as a single declarative sentence at the top:

> We will use Postgres as the primary data store for user activity.

Then the elaboration: what specifically we will do, and any boundaries on the
decision (e.g., "this applies to user activity only, not to session data").

Number each binding constraint as a D-ID list item (tier T1 — checked):

  - **D1:** <first constraint>.
  - **D2:** <second constraint>.
  ...

D-IDs are numbered from D1 with no gaps or duplicates. Each is a permanent
address for that constraint; supersession fields cite D-IDs by this address.
-->

- **D1:** <first constraint>.

## Decision drivers

<!--
OPTIONAL — delete this section if the choice had no competing criteria worth
naming.

The criteria the decision was judged against — the forces that actually
discriminated between the options. Naming them here is what lets the
Alternatives section reject each option against a *stated* criterion rather
than an ad-hoc reason, and lets a future reader re-run the decision when one
of these drivers changes.

- ...
-->

## Consequences

<!--
What follows from this decision — both the good and the bad. Be honest about
the tradeoffs we accepted; this is the section that will save the next person
from re-litigating the choice.

Group as:

**Positive:**
- ...

**Negative:**
- ...

`Revisit if:` is the named trigger for reconsidering the decision — a new
constraint, a failed confirmation, changed platform support, a scale threshold.
This is its canonical home (Consequences is always present, so the trigger
survives deletion of the optional Decision summary); when a summary is present,
mirror this line into it verbatim. `Revisit if: stable — no foreseeable trigger`
is a valid explicit value for a decision that genuinely won't age.
-->

**Revisit if:** <the trigger that should reopen this decision, or `stable — no foreseeable trigger`>

## Confirmation

<!--
OPTIONAL — keep this section when the decision is the kind you can verify, or
when a reader would plausibly expect a conformance mechanism. How we will know
the decision is actually being followed: a decision with no way to confirm
conformance erodes silently as the code drifts away from it.

Prefer the explicit `Mode: none` form (with a one-line reason) over silently
deleting the section where a reader would expect a check — a non-checkable
residual should be visible, not hidden. Delete the section only for trivial
decisions where no one would expect one.
-->

- **Mode:** reviewer-checked <!-- reviewer-checked | lint/CI | architecture fitness test | periodic audit | none -->
- **Signal:** <what proves conformance>
- **Owner:** <who notices drift>

## Alternatives considered

<!--
What else did we look at? Why did we reject each? Even one sentence per
alternative is valuable — it tells future readers we *considered* the option
they're about to suggest. Where Decision drivers are listed above, reject each
alternative against one of them.
-->

- **<alternative>:** <reason for rejection>.

## References

<!-- Links to discussions, prior art, benchmarks, RFCs. Optional. -->
