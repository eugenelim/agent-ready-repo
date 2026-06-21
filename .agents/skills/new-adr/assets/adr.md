# ADR-NNNN: <problem + chosen solution>

<!--
Title names the problem and the solution together, so the decision is legible
from the index alone — "Primary store for user activity: Postgres over DynamoDB",
not "Decision about the database". Keep the ADR-NNNN ordinal prefix.
-->

- **Status:** Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** YYYY-MM-DD
- **Decision-makers:** <github-handles who own the call>
- **Consulted:** <!-- whose input was sought, two-way; optional, delete if none -->
- **Informed:** <!-- who is kept up to date, one-way; optional, delete if none -->
- **Supersedes:** <!-- ADR-NNNN, or "none" -->
- **Related:** <!-- RFCs, other ADRs, specs -->

<!--
Status lifecycle: Proposed → Accepted, or Proposed → Rejected. An Accepted ADR
may later become Deprecated (the decision no longer applies and nothing replaces
it) or Superseded by ADR-NNNN (a specific later ADR replaces it). A Rejected ADR
is kept, never deleted — recording what we declined, and why, is the point. Once
Accepted, the body is frozen; only the Status line moves after that.
-->

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
-->

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

**Neutral / to revisit:**
- ...
-->

## Confirmation

<!--
OPTIONAL — delete this section if the decision isn't the kind you can verify.

How we will know the decision is actually being followed: a design review, an
architecture fitness test, a lint or CI check, a periodic audit. A decision
with no way to confirm conformance erodes silently as the code drifts away
from it.
-->

## Alternatives considered

<!--
What else did we look at? Why did we reject each? Even one sentence per
alternative is valuable — it tells future readers we *considered* the option
they're about to suggest. Where Decision drivers are listed above, reject each
alternative against one of them.
-->

## References

<!-- Links to discussions, prior art, benchmarks, RFCs. Optional. -->
