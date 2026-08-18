# RFC-0088 — front-door service-worker landscape probe

**Status: EXPLORATORY. Not a promoted arm, not a manifest member, and not part of
any round's evidence.** It is recorded because it materially narrows a residual
round 11 left open, and because a reader who finds that residual should find this
alongside it rather than re-running the work.

## Why it exists

Round 11's amended D/item 6 requires the profile's persisted service-worker
storage to be purged and registration blocked for the session. Round 11 measured
the *cost shape* of that requirement as a taxonomy — a flow with no worker and a
flow that merely registers one both survive suppression; only a sign-in path that
genuinely **depends** on a worker breaks — and recorded plainly that it could not
say which class real destinations fall into. That was named a landscape question,
not a fixture question.

This probe answers part of it.

## What was measured

Three public enterprise front doors, addressed by **role** rather than by product,
because the finding generalises by role:

| Role | Registers a worker | Renders with workers allowed | Renders with workers blocked | Reading |
| --- | --- | --- | --- | --- |
| **Sign-in surface** — an enterprise identity provider's sign-in page | no | yes | yes, unchanged | **Authentication does not need a service worker** |
| **Webmail surface** — a high-volume enterprise mail front door | attempts one | yes | yes, **byte-identical** | Present, **not load-bearing** |
| **Collaboration surface** — a real-time collaboration front door | yes | yes | **no — collapses to a stub** | **LOAD-BEARING** |

The suppression mechanism demonstrably works against real properties: registrations
drop to zero and each blocked arm logs a refusal.

## The three readings, in order of how much they matter

**1. Authentication itself does not depend on a service worker.** The sign-in
surface registers none and renders identically with workers blocked. This is the
scenario that could have invalidated D/item 6 outright — the fear that suppressing
workers breaks the very sign-in the pilot exists to protect. It does not.

**2. A mail surface is the "present but idle" class**, which round 11's taxonomy
predicted and this confirms against a real product: it attempts a registration and
renders byte-identically without it, same interactive element counts. The
requirement costs this class nothing.

**3. A real-time collaboration surface is load-bearing** and does not survive
suppression. This is the class round 11 identified as expensive, and it exists in
the wild.

## The design consequence

**A global worker block is the wrong shape.** Suppression should be
**destination-scoped**, which is the axis decision C already chose for egress. A
destination policy that already decides *where* a session may talk is the natural
place to decide *whether a worker may run there*, rather than a separate global
switch that must be all-or-nothing across surfaces with opposite needs.

That is a proposed amendment, not a decision. It is recorded in the RFC's open
questions.

## Limits — and one instrument that is not trustworthy

- **Unauthenticated front doors only.** Whether the *post-authentication*
  silent-SSO path — a device-bound refresh credential persisted in the browser
  profile — needs a worker is **not measured**, because it requires credentials the
  security preconditions forbid. The sign-in surface carrying no worker is strong
  evidence the authentication step does not, but it is evidence, not proof. This
  probe **bounds** the residual; it does not close it.
- **The registration count is timing-sensitive and must not be quoted.** The
  webmail surface reported one registration in one run and zero in another, purely
  on observation timing. The readings that were stable across runs are the *refusal
  signal* under block and the *render equality*, and those are what the table above
  rests on. A round that promoted the count as a fact would be publishing an
  artifact of its own wait loop.
- A single point in time; these front doors ship continuously.
- Run with the signed, MDM-provisioned system browser — the runtime a real adopter
  pack requires, because only it reaches the OS keychain for the device-compliance
  certificate — against a fresh synthetic profile, with nothing submitted.

## Privacy

No URI is persisted anywhere in the probe artifact: no landing URL, redirect,
worker scope, domain, page text, or title. Target endpoints and the browser binary
are supplied through the environment by the caller and are not written to the
fixture or the artifact. What survives is a role label chosen by the fixture,
booleans, and counts. Verified by scanning the artifact for any URI and for vendor
or product names: none present.
