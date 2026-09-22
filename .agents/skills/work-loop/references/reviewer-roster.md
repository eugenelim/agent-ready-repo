# Reviewer roster — the lens the default gives up

Load when selecting reviewers, or when weighing whether the default roster
gives up a lens this change needs. `SKILL.md` owns the roster table itself,
the per-role boundaries, and the definition of high-risk work; this reference
states what the default costs.

## What this costs, stated rather than implied

`adversarial-reviewer` is the default and covers correctness and scope. It does
**not** cover the rest: its own contract assigns testability, reliability,
observability, maintenance cost, and every test-strength judgment — mode fit,
tautology, mock shape, mirrors, and whether an artifact can actually fail —
exclusively to `quality-engineer`. Work tripping none of the high-risk
conditions therefore ships without that lens. That is a deliberate trade of the
lens for speed, not a claim some other reviewer picks it up; raise the work to
high-risk, or ask for the pass, when the trade is wrong.
