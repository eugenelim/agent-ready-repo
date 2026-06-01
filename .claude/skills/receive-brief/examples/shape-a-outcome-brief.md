# Brief: Self-service password reset

> **This is an example, not a schema.** It demonstrates **Shape A** — a
> no-stories *outcome* brief, where spec boundaries are derived from the
> Outcome and Scope and coverage is spec-granular. The fields and the Spec map
> show the expected shape; copy the structure, not the content. Your real brief
> may have fewer or more sections — the `receive-brief` skill elicits what's
> missing rather than rejecting a brief for not matching this exactly.

- **Slug:** `self-service-password-reset`
- **Received:** 2026-05-18
- **Owner:** platform team
- **Epic:** ACME-2231 <!-- this slice is part of a larger "reduce support load" epic tracked in the company tracker; we own only the password-reset portion -->

## Outcome

Users who forget their password can't get back in without filing a support
ticket, and password-reset tickets are the single largest category in the
support queue. We want a user to reset their own password end to end — request
a reset, verify by email, set a new password — without any human in the loop.

## Success metrics

- Password-reset support tickets down 60% within one quarter of launch.
- 90% of reset attempts complete without contacting support.
- Median time from "forgot password" to "logged in again" under 5 minutes.

## Scope / Non-goals

**In scope:**

- Email-based reset request and verification.
- Setting a new password that meets the existing password policy.
- Rate-limiting and basic abuse protection on the reset endpoint.

**Non-goals:**

- SMS or authenticator-app recovery (a later brief may add these).
- Changing the password policy itself.
- Admin-initiated resets (already covered by the admin console).

## Appetite

A few weeks, not a quarter. If the verification flow turns out to need a new
identity provider integration, that's a separate brief — flag it, don't absorb
it here.

## Spec map

<!-- No stories (Shape A): one row per derived spec, coverage is spec-granular.
The Status column is auto-derived by the coverage lint from each spec's own
Status field — shown here filled in so you can see the rolled-up shape. This
brief is NOT yet delivered: account-lockout-recovery is still Implementing. -->

| Spec | Status |
| --- | --- |
| `password-reset-request` | Shipped |
| `password-reset-verification` | Shipped |
| `account-lockout-recovery` | Implementing |
