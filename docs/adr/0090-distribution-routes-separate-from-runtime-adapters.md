# ADR-0090: Distribution routes are a layer separate from runtime adapters

- **Status:** Accepted
- **Date:** 2026-08-20
- **Decision-makers:** eugenelim
- **Consulted:** adversarial review (independent, three rounds to convergence), security review, fresh-reader review
- **Supersedes:** none
- **Related:** [RFC-0092](../rfc/0092-first-class-distribution-routes.md) (the accepted proposal this records), [RFC-0001](../rfc/0001-bundle-distribution-by-adapter-spec.md) (the adapter contract this extends), [RFC-0008](../rfc/0008-claude-plugins-install-route-parity.md), [RFC-0010](../rfc/0010-apm-install-route-parity.md), [ADR-0021](0021-pack-manifest-source-of-truth-and-scoped-identity.md), [ADR-0072](0072-derived-plugin-manifest-mirrors-upstream-schema.md), [ADR-0079](0079-executable-plugin-branch-publisher-identity.md)

## Decision summary

- **Decision:** Packaging a pack for an external plugin ecosystem is a **distribution route**, a first-class concept owned separately from a **runtime adapter**. Routes are declared in their own canonical contract; `install-routes` stops being a field of `[adapter."claude-code"]`.
- **Because:** a vendor-neutral route (`apm`) is currently modelled as a property of one vendor's adapter, and the build has to route around its own abstraction to make that work.
- **Applies to:** `contracts/`, the build recipes and their dispatch, and every present and future package output.
- **Tradeoff accepted:** one more concept a contributor must learn before touching the build, and a third hand-written route lands before the generic registry removes the duplication.
- **Revisit if:** the route contract's six fields still contain `unknown` after three real routes exist, or an external consumer turns out to read `contracts/adapter.toml` as public configuration.

## Context

Two external packages already ship — a Claude Code plugin and an APM package — and they work. What the repository lacks is a *name* for what they are, and three places in the source pay for that:

- `contracts/adapter.toml:188` declares `install-routes = ["cli", "claude-plugins", "apm"]` inside `[adapter."claude-code"]`. `apm` is a vendor-neutral package format, yet it is modelled as a property of one runtime adapter; the contract comment concedes that "Kiro, Copilot, and Codex do not declare install-routes."
- `packages/agentbundle/agentbundle/build/main.py:669` short-circuits past the adapter table entirely for `adapter == "apm"`, because APM is not an adapter and the code knows it. There is no layer for it to be instead.
- `packages/agentbundle/agentbundle/build/main.py:741` has the Claude plugin route rewriting projection rows from `target-path`/`mode` to `plugin-target-path`/`plugin-mode` — a packaging concern reaching into the runtime contract and editing it mid-build.

The constraint that forced the decision now rather than later: three further package formats became buildable against first-party documentation at once (portable Agent Plugins 1.0.0 with vendorable schemas, a native Codex plugin package, and Kiro Powers). Each additional route makes the mis-ownership more expensive, and `install-routes` carries a closed enum in `contracts/adapter.schema.json:255` plus two contract tests — one pinning Claude's exact list, one asserting no other adapter carries the field — so the cost is enumerable rather than vague.

## Decision drivers

- **Ownership correctness.** A vendor-neutral concept must not be a child of one vendor's adapter.
- **Cost of the next route.** Adding a route should not require editing an unrelated adapter's contract row.
- **No premature abstraction.** Four of six candidate routes have undocumented lifecycle and consent semantics; a registry built today would encode `unknown` as authoritative field names.
- **Published-output stability.** The Claude marketplace promise is one-way and must not break.

## Decision

**A distribution route is a first-class concept, declared in its own canonical contract, and a runtime adapter is a separate concept; both consume the same normalized pack model and neither depends on the other.**

- A route is declared in `contracts/distribution-routes.toml` with six fields: identity, package layout, manifest projector, component-capability map, marketplace projector, and lifecycle trigger.
- `install-routes` moves there from `[adapter."claude-code"]`. A route may *name* an adapter projector, but is no longer owned by one.
- The **route contract** (data) and the **route registry** (generic dispatch code) are separate deliverables in separate phases. Declaring routes in a contract does not require a generic engine to consume them; a minimal route resolver suffices at first, and route rendering stays named, route-specific code until three real routes exist.

## Consequences

**Positive.** The `apm` route stops being a Claude-adapter child. Route logic stops mutating adapter contract rows. A new package format is added by declaring a route rather than by editing another vendor's contract. Runtime adapters and distribution routes become independently reviewable.

**Negative, honestly.** A contributor must learn the route/adapter distinction before touching the build. The generic registry is deferred, so a third route is hand-written first and duplication temporarily increases before it decreases. The published support matrix becomes *less* flattering, because several cells turn into `unknown` or partial-support claims where prose previously implied more.

**Migration cost, enumerated rather than assumed.** The `install-routes` move touches: the closed enum in `contracts/adapter.schema.json:255`; the byte-identical bundled copy under `packages/agentbundle/agentbundle/_data/` held by `tools/catalogue/check_contract_parity.py`; the two contract tests at `packages/agentbundle/tests/build_pipeline/test_contract.py:478` and `:487` — the second of which asserts no other adapter carries the field and must therefore be rewritten rather than deleted; the marker's `--install-route` values and the generated hook commands that pass them; route-name strings in install state; and the public route documentation. Published output does not change.

**Revisit if:** the route contract's six fields still contain `unknown` after three real routes exist (the registry extraction would then be permanently wrong, not merely early), or an external consumer is found to read `contracts/adapter.toml` as public configuration (the `apm` re-parenting would then be a breaking change requiring an alias and a deprecation window).

## Confirmation

- **Mode:** lint/CI
- **Signal:** golden fixtures pin the Claude and APM package outputs byte-for-byte across the contract move, so "published output unchanged" is a testable claim rather than an intention; `tools/catalogue/check_contract_parity.py` keeps the canonical and bundled contracts identical; the rewritten contract test asserts route ownership lives in the route contract and not on an adapter.
- **Owner:** eugenelim

## Alternatives considered

1. **Do nothing — keep adding route branches inside the Claude adapter.** Cheapest today. *Rejected:* the cost is per-route and recurring, and three routes are now buildable; `apm` stays mis-parented and every new route re-touches `main.py:669` and `:741`.
2. **Build the full generic route registry now.** The intuitive design, and RFC-0092's original brief. *Rejected on spike evidence:* a drafted six-field registry was stress-tested against all six candidate routes and argued against itself — for `agent-plugin`, `codex-plugin`, `kiro-power`, and `copilot-plugin` it would hold placeholders, and a registry that encodes `unknown` as a named field obscures missing contract acquisition instead of removing special cases.
3. **Model package formats as a second kind of adapter.** *Rejected:* "adapter" already means a runtime target with scope and projection rules in this repository; reusing the word for a thing with a different lifecycle would make both harder to reason about.
4. **Make portable Agent Plugins the only output, with extensions for everything else.** *Rejected on the specification's own direction:* portable v1 excludes hooks, agents, commands, rules, and LSP, and its 1.1.0 working draft explicitly keeps excluding them pending format convergence. Claude users would lose eight of the nine canonical component kinds.

## References

- [RFC-0092](../rfc/0092-first-class-distribution-routes.md) — the accepted proposal, including the full option analysis, the component projection matrix, the threat model, and the phased rollout.
- Evidence cited above was verified against the tree at `b9f85230`.
