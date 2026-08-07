# Example — a feature intent that becomes a brief (app scale)

> **This is an example, not a schema.** It demonstrates the *shape* of an
> app-scale feature intent and how its leaf becomes an ordinary `core` brief.
> Your intent will look different; copy the *moves*, not the wording.

A solo developer on a single-repo SaaS app runs `frame-intent`. Intake infers
**Scale: app** (one repo, app code present) and asks greenfield/brownfield — the
login flow already exists, so **Maturity: brownfield**.

## The intent

```
# Intent: cut password-reset support load with self-serve reset

- **Slug:** self-serve-password-reset
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield

## Outcome
- Input (steerable): % of reset requests completed without an agent
- Outcome (lagging): password-reset support tickets per week
- Guardrail: account-takeover rate must not rise

## Opportunity
Users who forget their password today email support and wait hours. The job:
"get back into my account right now, on my own, without feeling unsafe."

## Assumptions
- Users will trust an emailed reset link enough to use it (riskiest — desirability)
- The existing mailer can deliver a tokenised link within seconds

## Decomposition
- (leaf — becomes the brief below)
```

## De-risking it

`de-risk-intent` triages reversibility: shipping behind a flag to 5% of users is
a **two-way door**, so it picks `prototype-led` — build a thin reset flow for an
internal cohort and watch completion. The predeclared kill condition (qualitative
bar, low traffic): *"proceed only if ≥ 4 of 6 test users complete reset unaided
and none report feeling unsafe."* The cohort hits 5 of 6 → **survived**.

## The leaf becomes a brief

Because Scale is **app** and this is a single feature, `decompose-intent`'s leaf
*is* a `core` brief — no new fields, no slicing. It lands at
`docs/product/briefs/self-serve-password-reset.md` with the same Outcome,
Success metrics (from the input/lagging/guardrail), Scope/Non-goals, and an
Appetite, and `receive-brief` → `new-spec` → `work-loop` carry it to delivery.
The detailed reset-token contract is pinned at the spec stage, not here.
