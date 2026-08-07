# JTBD job categories

The `intent` model frames the Opportunity section using Jobs-to-be-Done (JTBD)
theory. Every job falls into one of three tiers — **functional**, **emotional**,
and **social** — and a fourth complement, the **struggling moment**, names the
friction point where the current situation fails the job-holder today.

These definitions use the same vocabulary as `identify-opportunities` so that a
lightweight `frame-intent` intake pass and a full job-discovery run share a
common language.

## Functional job

What the user is **trying to accomplish** — the core task, outcome, or goal they
are pursuing, independent of any product or solution.

*Pattern:* help me [do something] so that [outcome].

*Example (account access):* get back into my account on my own without waiting
for a support queue — so I can keep working.

*Example (expense reporting):* reconcile my expense report before the monthly
close — so I do not have to chase approvals manually.

## Emotional job

How the user wants to **feel** during or after getting the functional job done —
or the feeling they want to avoid.

*Pattern:* feel [state] / not feel [state] while doing this.

*Example (account access):* feel in control of the situation, not at the mercy
of a support queue or a slow email link.

*Example (expense reporting):* feel confident the submission is correct, not
anxious about being flagged for an error.

## Social job

How the user wants to be **perceived by others** — colleagues, management, or
their broader community — while getting the job done.

*Pattern:* be seen as [perceived quality] by [audience].

*Example (account access):* be seen as self-sufficient and capable by my team,
not someone who can't get into their own tools.

*Example (expense reporting):* be seen as diligent and compliant by finance,
not someone who submits sloppy or late reports.

## Struggling moment

The **friction point** where the current situation fails the job-holder — the
gap between where they are now and where the job requires them to be. Describe
the observable moment where the pain bites, not a solution or a fix.

*Pattern:* when [situation], [what breaks or what the user cannot do].

*Example (account access):* when locked out of the account, the reset-link
email arrives minutes late after a failed login — so the user is stuck waiting
without any progress signal.

*Example (expense reporting):* when submitting expenses late, the approval chain
has already reset — so the submission sits in limbo until the next cycle.

---

## Going deeper

`frame-intent` elicits one primary entry per tier as a lightweight intake pass.
For full job discovery — surfacing every functional, emotional, and social job
behind an opportunity area, scoring each via the Ulwick opportunity formula, and producing a ranked
opportunity list — run `identify-opportunities`.
