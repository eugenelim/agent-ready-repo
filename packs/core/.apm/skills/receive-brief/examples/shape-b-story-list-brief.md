# Brief: Team billing portal

> **This is an example, not a schema.** It demonstrates **Shape B** — a
> *story-list* brief, where the brief carries user stories with ids and
> decomposition is *grouping stories into specs*. Coverage is story-granular:
> each satisfying acceptance criterion in a derived spec carries a
> `Satisfies: US-n` marker, and the Spec map gains a `Story` column. The fields
> and the Spec map show the expected shape; copy the structure, not the
> content. `receive-brief` elicits what's missing rather than rejecting a brief
> that doesn't match this exactly.

- **Slug:** `team-billing-portal`
- **Received:** 2026-05-20
- **Owner:** billing team
- **Epic:** <!-- none; this brief is self-contained, so the pointer is omitted -->

## Outcome

Team admins have no way to manage their own billing — they email us to change
plans, update payment methods, or download invoices, and every change is a
manual back-office task. We want admins to manage their team's billing
themselves from a portal, so billing changes stop being a support workflow.

## Success metrics

- 80% of plan changes and payment-method updates happen self-serve.
- Back-office billing tasks down 70% within two quarters.
- Invoice-download requests to support drop to near zero.

## Scope / Non-goals

**In scope:**

- View and change the team's plan.
- Add, update, and remove payment methods.
- Download past invoices as PDF.

**Non-goals:**

- Usage-based / metered billing (the current model is seat-based).
- Multi-currency support.
- Reselling or partner billing hierarchies.

## Appetite

About six weeks. The invoice PDF rendering is the riskiest piece — if it needs
a new rendering service, that's its own slice, surfaced for sign-off, not
silently folded in.

## User stories

- **US-1.** As a team admin, I want to see my current plan and change it, so
  that I can upgrade or downgrade without emailing support.
- **US-2.** As a team admin, I want to add and remove payment methods, so that
  billing keeps working when a card expires.
- **US-3.** As a team admin, I want to download past invoices as PDFs, so that
  I can submit them for expense reporting.

## Spec map

<!-- Story-list (Shape B): stories are grouped into specs; the `Story` column
links each row to the US-n it satisfies (the satisfying ACs inside each spec
carry a `Satisfies: US-n` marker). The Status column is auto-derived by the
coverage lint. This brief is NOT yet delivered: invoice-pdf-export is still
in Draft. -->

| Spec | Story | Status |
| --- | --- | --- |
| `billing-plan-management` | US-1 | Shipped |
| `payment-method-management` | US-2 | Implementing |
| `invoice-pdf-export` | US-3 | Draft |
