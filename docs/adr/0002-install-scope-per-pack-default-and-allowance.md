# ADR-0002: Install-scope is a per-pack default + allowance, not a per-item or adopter-only choice

- **Status:** Accepted
- **Date:** 2026-05-23
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0004](../rfc/0004-install-scope-per-pack.md), [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md), [`distribution-adapters` spec](../specs/distribution-adapters/spec.md), [`agent-spec-cli` spec](../specs/agent-spec-cli/spec.md)

## Context

[RFC-0004](../rfc/0004-install-scope-per-pack.md) added a **scope** dimension (`repo` | `user`) to the adapter contract. The dimension exists so a future cross-project pack can ship at user scope cleanly; no user-scope pack lands in this RFC. The value-prop is the dimension itself.

The shape of the dimension has four orthogonal axes:

1. **Where does the scope value live?** Pack metadata, CLI invocation, adapter hardcode, or somewhere else.
2. **Who picks the value?** Pack author, adopter, both, or neither.
3. **Is the scope per pack or per primitive?** The pack as an atomic unit, or each skill/agent/command individually.
4. **What's the discovery surface?** Pack authors and third-party catalogues need a uniform refusal contract for malformed packs.

Each axis admits multiple positions. The team needed to pick one combination and pin it before the contract bump landed; partial answers leave the CLI's `--scope` semantics under-specified and force every consumer (the four reference adapters, third-party catalogue indexers, `agentbundle validate`, the `adapt-to-project` skill) to re-derive the rule.

## Decision

We adopted the **per-pack default + allowance** model:

> A pack's `pack.toml` declares both a `default-scope` (the scope used when the adopter passes no `--scope`) and an `allowed-scopes` set (the scopes the pack permits). The CLI's `--scope` flag overrides the default within the declared set; a value outside `allowed-scopes` is refused with stderr naming the pack and the declared set.

Three derived rules pin the model concretely:

- **Precedence:** CLI flag > pack `default-scope` > built-in `repo`.
- **Granularity:** A pack installs at one scope; every primitive in that pack lives at that scope. No per-item override.
- **Discovery:** The `default-scope ∈ allowed-scopes` invariant is enforced in `pack.schema.json` via a jsonschema `if`/`then` block, so catalogue indexers, third-party validators, and `agentbundle validate` all refuse a malformed pack identically — without having to import CLI code.

The four shipped packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`) all declare `allowed-scopes = ["repo"]`; the dimension lands ahead of any user-scope consumer.

## Consequences

**Positive:**

- Pack authors express scope intent **once**, in `pack.toml` — adopters don't re-derive it per install.
- Catalogue indexers and third-party validators read the contract identically to the CLI; no per-tool discovery code.
- `--force` semantics fit cleanly: an adopter can install at both scopes when their workflow demands it, without the pack author having to anticipate every combination.
- The dimension lands without a consumer; mechanics (path-jail, state file, `~`-expansion, `recommends` cross-scope) are settled before the first user-scope pack rides them.

**Negative:**

- Two more required fields on `pack.toml` for v0.2 packs (`default-scope`, `allowed-scopes`). The v0.1 legacy path keeps existing packs installable, but v0.2 publishers must opt in deliberately.
- State-file count doubles when a pack is installed at both scopes (`<repo>/.agent-ready-state.toml` and `~/.agent-ready/state.toml`). Cross-scope upgrades become per-scope, per-verb.
- Hook-shaped primitives are forbidden at user scope until a follow-up RFC designs the user-scope hook-wiring merge story. This is a real constraint for any future user-scope pack carrying hooks; not a constraint on anything shipping today.

**Neutral / to revisit:**

- `global` (system-wide) scope is deliberately absent. No adapter has a system-wide root, and adding it later is a one-line schema bump against the already-versioned contract.
- `[pack.install]` could grow more fields in future (`requires-confirmation`, etc.) — out of scope for v0.2.

## Alternatives considered

The numbering follows RFC-0004 § *Alternatives considered* for traceability. This ADR explicitly records the rejection of alternatives **2, 3, 7, and 8**; the other rejections (1, 4, 5, 6) are recorded in the RFC body and not re-litigated here.

- **(2) Per-item scope (override per skill / agent within a pack).** Maximally flexible but multiplies state-file bookkeeping by the cardinality of primitives in a pack, breaks "install/uninstall is atomic per pack," and asks the pack author to make a scoping decision they're unlikely to get right for every adopter. *Rejected:* an item that belongs at a different scope should be its own pack.

- **(3) Adopter-only scope (no pack default).** Adopter passes `--scope` every time. Forces every adopter to re-derive a decision the pack author already knows the answer to. *Rejected:* the pack author is closest to the content; making them declare the default is a one-line cost that saves every adopter from re-deriving it.

- **(7) Hardcode the four shipped pack names in the CLI as repo-only.** Avoids the `allowed-scopes` field entirely; the CLI would refuse user-scope installs for the four names. *Rejected:* pack constraints belong with the pack, not in the CLI; third-party catalogues need the same declarative shape; the reviewer / scaffold / validate rails all need pack-author intent in the file, not in CLI source.

- **(8) Land the dimension *with* the first user-scope pack, not ahead of it.** Cheaper in PR count. *Rejected:* scope mechanics are non-trivial (path-jail, state-file location, `~`-expansion, projection forks, `recommends` interaction, backward compat) and landing them under the pressure of a concurrent pack means corners cut. The named consumer becomes a one-day PR once this RFC is in.

## References

- [RFC-0004 — Install-scope dimension](../rfc/0004-install-scope-per-pack.md)
- [`distribution-adapters` spec § Install-scope dimension (contract v0.2)](../specs/distribution-adapters/spec.md)
- [`agent-spec-cli` spec § Install-scope dimension (CLI surface, contract v0.2)](../specs/agent-spec-cli/spec.md)
- [Migration guide for third-party pack authors](../guides/how-to/v01-to-v02-pack-upgrade.md)
