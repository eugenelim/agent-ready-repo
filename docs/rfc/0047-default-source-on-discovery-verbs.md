# RFC-0047: Default the catalogue source on the discovery verbs (`list-packs` / `list-profiles`)

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-25
- **Related:** RFC-0046 + ADR-0036 (the four-layer source-resolution chain this RFC reuses unchanged; both named this as a follow-on), RFC-0031 (package-manager posture)

## The ask

- **Recommendation (BLUF):** Make `catalogue` **optional** (`nargs="?"`, default `None`) on `list-packs` and `list-profiles` too, resolving the omitted source through the **same** `resolve_default_source` four-layer chain RFC-0046 shipped for `install`/`upgrade`. No new resolver, no new layer — purely extend the existing `resolve_catalogue_uri(args)` wiring to the two query handlers. An explicit positional still passes through unchanged.
- **Why now (SCQA):**
  - *Situation* — RFC-0046 made the source default on `install`/`upgrade`; `list-packs`/`list-profiles` were deferred as a follow-on because "defaulting a *query* needs its own justification and must not silently fetch the upstream URL on a gateway-bound fork."
  - *Complication* — having `install --pack core` work bare while `list-packs` still demands the full URL is an asymmetry users hit immediately (you list a catalogue to decide what to install from it).
  - *Question* — can the deferral's one safety requirement ("must not silently fetch upstream on a gateway-bound fork") be met while defaulting the query verbs?

## Decision

Extend the RFC-0046 resolution to the two discovery verbs. `catalogue` becomes `nargs="?"` (default `None`) on `list-packs` and `list-profiles`; when omitted, each handler calls the existing `commands/_common.resolve_catalogue_uri(args)` before `resolve_catalogue`, exactly as `install`/`upgrade` do. The four-layer chain, its validation, and the editable-detection hardening are reused verbatim — this RFC adds no resolution logic.

## Why this is safe (the justification the deferral demanded)

The deferral's concrete requirement was: **a bare discovery query must not silently fetch the upstream URL on a gateway-bound fork.** The shipped design already satisfies it:

- A gateway-bound fork is an **editable install** (the blessed downstream path, RFC-0046). A bare `list-packs` on it resolves via **layer 3** (its own clone) → **no upstream fetch**.
- The only case that reaches layer 4 (the `git+https` upstream) on a bare query is a **non-editable wheel** install — i.e. the public PyPI user, for whom fetching the upstream catalogue is the *expected* behaviour and is identical to the bare `install` they already run.

So the editable-detection layer is exactly the control that makes query-defaulting safe; the deferral was conservatism pending this justification, not an unmet design gap.

## Residual / accepted

- On a **wheel** install, a bare `list-packs` now performs a network fetch where it previously errored with "catalogue required." This is surfaced, not silent (the same layer-4 `git+https` fetch a bare `install` performs), and is the symmetric, expected behaviour under the default-catalogue model RFC-0046 established. The unauthenticated-TOFU integrity residual is unchanged and still tracked by the separate integrity-pinning follow-on.

## Scope

- **In:** `catalogue` optional on `list-packs`/`list-profiles`; reuse of `resolve_catalogue_uri`.
- **Out:** integrity-pinning for the layer-4 fetch (still deferred — its own follow-on); any change to the resolver itself; the in-repo adapter override (its own RFC).

## Supersedes-in-part

ADR-0036's "the discovery verbs keep requiring an explicit catalogue (deferred)" — the query-defaulting edge is reopened and decided here; the layer-4 integrity edge stays deferred. ADR-0036 is annotated accordingly.
