# access-control — authorization, object- & function-level

> **Loaded when:** the change adds or alters an endpoint, handler, RPC, or any
> code path that reads or mutates a resource on behalf of a caller.
> **Standards:** OWASP Top 10:2025 A01 (Broken Access Control) · OWASP API
> Security Top 10:2023 (API1 BOLA, API3 BOPLA, API5 BFLA) · ASVS 5.0 V4
> (Access Control) · Proactive Controls 2024 C1 (Enforce Access Controls).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, ask whether the spec names the access rule **as an acceptance
criterion** at the right depth: not "users can only see their own orders" in
prose, but a criterion stating *which* identity is checked, *where* the check
sits relative to the side effect, and what an out-of-scope caller receives
(404 vs 403). A boundary with no AC for authz is the highest-leverage
spec-stage finding (Proactive Controls 2024 C1; ASVS 5.0 V4.1).

## Implementation checks

- `reason` **Who is allowed to call this?** For every new/changed
  endpoint/handler/RPC, name the identity and the guard. A mutating operation
  with no `requireAuth`-equivalent before the side effect is a Blocker.
- `reason` **Object-level (BOLA / IDOR).** A caller passing `id=B` while
  authenticated as A must be rejected — the row is fetched *scoped to the
  caller*, not fetched-then-checked-then-maybe-leaked.
- `reason` **Function-level (BFLA).** Admin/privileged routes must verify the
  *role*, not merely authentication. A regular user reaching an admin verb by
  guessing the path is the classic miss.
- `reason` **Check-before-effect ordering.** The authorization decision must
  precede the mutation/read it guards; a check after the side effect is
  decorative.
- `reason` **Mass assignment / property-level (BOPLA).** Binding a request
  body straight onto a model lets a caller set fields they shouldn't
  (`isAdmin`, `ownerId`). Confirm an allowlist of writable fields.
- `hybrid` **Missing-guard coverage.** A linter/SAST route-auth rule can list
  unguarded routes; you judge whether each *should* be public.

## Established-helper bypass

Most repos centralize authz in one place — a policy/guard middleware, a
`can(actor, action, resource)` helper, a decorator. Resolve the repo's
sanctioned authorization helper (AGENTS.md blessed list → CONVENTIONS /
installed context → grep for the de-facto guard) and flag any handler that
hand-rolls an inline `if user.id == ...` check instead of calling it —
ad-hoc checks drift out of sync with the policy the helper centralizes.
