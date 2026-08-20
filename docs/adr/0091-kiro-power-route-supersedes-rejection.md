# ADR-0091: A Kiro Power route is justified: superseding the Kiro-route rejection only

- **Status:** Accepted
- **Date:** 2026-08-20
- **Decision-makers:** eugenelim
- **Consulted:** adversarial review (independent, three rounds to convergence)
- **Supersedes:** **rejected alternative (2) only** of [ADR-0004](0004-repo-scope-per-adapter-projection.md) — its rejection of a per-IDE plugin install route for Kiro. Every other part of ADR-0004, including its actual decision that per-IDE direct writes are the repo-scope install default, stands unchanged.
- **Related:** [RFC-0092](../rfc/0092-first-class-distribution-routes.md) D3 (the accepted proposal this records), [RFC-0012](../rfc/0012-repo-scope-per-adapter-projection.md) alternative 2 (the same rejection in its originating RFC, corrected there by Errata), [ADR-0090](0090-distribution-routes-separate-from-runtime-adapters.md) (the route layer this route lives in), [RFC-0022](../rfc/0022-kiro-adapter-split.md) (the Kiro IDE/CLI adapter split, intact)

## Decision summary

- **Decision:** A Kiro Power route is justified, as a **route profile** that shares the portable Agent Plugin artifact rather than emitting a package of its own. This supersedes only the rejected alternative (2) in ADR-0004.
- **Because:** that rejection rested on a specific factual premise — "Kiro Powers has no documented install verb" — and Kiro has since documented Powers with git and local import plus a Powers marketplace.
- **Applies to:** the `kiro-power` route profile and the published Kiro support claims; no runtime adapter changes.
- **Tradeoff accepted:** the route is a **partial** one — it delivers runtime components but cannot trigger project adaptation or install seeds, and saying so makes the published Kiro row less flattering.
- **Revisit if:** Kiro documents a Power-install or Power-session lifecycle event (the route stops being partial), or Kiro's required manifest fields diverge from what `pack.toml` can derive.

## Context

ADR-0004 and [RFC-0012](../rfc/0012-repo-scope-per-adapter-projection.md) both rejected building a per-IDE plugin install route for Kiro, in the same words and for the same reason: *"Kiro has no programmatic plugin-install API to integrate with — its extension model is Open VSX (VS Code extensions, not skill content) and Kiro Powers has no documented install verb. Building a route for which no upstream consumer exists is premature."*

That was correct when written, and it was researched — RFC-0012 cites `kiro.dev/docs/editor/extension-registry/`. The premise has since expired. Kiro's current first-party documentation describes a **Power** as an Agent Plugin plus an optional `dev.kiro/` extension directory, imported from GitHub or a local folder, activated by manifest `keywords`, with a Powers marketplace and one-click installation. The rejection's load-bearing fact — no documented install verb — no longer holds.

Two constraints shape *how far* this goes:

- A Kiro Power is a conforming Agent Plugin plus one directory. Emitting a separate `dist/kiro-powers/` tree would duplicate an entire package to gain that directory.
- Kiro documents no Power-install event and no Power-packaged hook contract. `dev.kiro/` documents steering files only. So the route can deliver components, and cannot run the repository's install-to-adapt chain or install adopter-owned seeds.

Kiro also **rewrites MCP server names on install** (`supabase-local` becomes `power-supabase-supabase-local`), so a canonical server name is not the installed name.

## Decision drivers

- **Is the rejection's premise still true?** It is not; that alone reopens the question but does not settle it.
- **Does the target have a materially distinct package contract?** No — it shares the portable artifact. Its marketplace, admission rules, and activation semantics *are* its own.
- **Can the route honestly claim the repository's differentiating capability?** No. Whether it can be described honestly as partial decides whether it may ship at all.
- **Bytes duplicated per directory gained.** One directory does not justify a second package.

## Decision

**Kiro is supported as a `kiro-power` route profile over the portable `agent-plugin` artifact, and the rejection of a Kiro route in ADR-0004 alternative (2) is superseded — that clause only.**

The profile shares the portable package's bytes and owns everything genuinely its own: admission validation against Kiro's stricter required-field set (`version`, `description`, `author`, and `keywords` all mandatory, against portable v1's `$schema` and `name`), `keywords`-driven activation semantics, its marketplace and submission projection, the `dev.kiro/` extension directory, and its own runtime-verification record. A route profile is a first-class route with a shared package layout, not a lesser one.

The route is published as **`components-only`**: no project adaptation, no seed installation, stated as `unsupported` rather than as a caveat.

## Consequences

**Positive.** Kiro adopters get skills and MCP through a first-party-documented import path, at the cost of one extension directory over a package the portable route already builds. The expired premise is corrected in the record rather than silently worked around.

**Negative, honestly.** The route cannot do the thing that distinguishes this repository's packs — repository-aware adaptation — and the published Kiro row must say so. `dev.kiro/steering/` has no source in `.apm/` today, so projecting steering would mean new canonical authoring surface; the route therefore ships with an empty extension point and no invented content. Nothing may depend on a canonical MCP server name surviving installation.

**Revisit if:** Kiro documents a Power-install or Power-session lifecycle event, at which point adaptation and seed parity are re-evaluated and the `components-only` claim is retired; or Kiro's required manifest fields drift beyond what `pack.toml` can derive, at which point admission validation, not the package, is what changes.

## Confirmation

- **Mode:** reviewer-checked, escalating to lint/CI when the route ships
- **Signal:** the published support matrix shows Kiro as `components-only` with adaptation and seeds `unsupported`, and no Kiro row claims `runtime-verified` until a recorded manual test names the Kiro version, surface, and OS. No route may be promoted to a verified claim on documentation alone.
- **Owner:** eugenelim

## Alternatives considered

1. **Keep the rejection — no Kiro Power route at all.** The status quo, and a real governance option rather than a straw one; ADR-0004 and RFC-0012 chose it once already. *Rejected:* its stated premise has expired, and the package a Kiro route needs is a byproduct of the portable route being built regardless.
2. **Emit a separate `dist/kiro-powers/` package.** *Rejected:* a Power is a conforming Agent Plugin plus `dev.kiro/`, so this duplicates the whole package to gain one directory — one output per product, which [RFC-0092](../rfc/0092-first-class-distribution-routes.md) rejects as a justification.
3. **Treat Kiro as fully supported once the package loads.** *Rejected:* it would claim adaptation and seed behaviour the route provably cannot deliver, which is the specific dishonesty the route/claim separation exists to prevent.

## References

- [RFC-0092](../rfc/0092-first-class-distribution-routes.md) D3 and P5 — the route-profile design, the projection matrix, and the partial-route claim vocabulary.
- Kiro first-party Powers documentation (create, install), retrieved 2026-08-19; documentation-verified, not runtime-verified.
