# ADR-0003: Four-broker contract for credentialed skills; in-process shim + adapter-root subprocess as the two v1 transports

- **Status:** Accepted
- **Date:** 2026-05-26
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0013](../rfc/0013-credential-broker-contract.md), [RFC-0006](../rfc/0006-skill-secrets-storage.md), [RFC-0004](../rfc/0004-install-scope-per-pack.md), [RFC-0011](../rfc/0011-pack-allowed-adapters.md), [`credential-broker-contract` spec](../specs/credential-broker-contract/spec.md), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md)

## Context

[RFC-0006](../rfc/0006-skill-secrets-storage.md) gave credentialed skills a three-tier resolver (env → OS keychain → 0600 dotfile floor) inside the `agentbundle` PyPI package (`agentbundle.credentials`, `agentbundle.creds.loader`). Two years of use surfaced three load-bearing problems:

1. **Portability.** Every credentialed skill carries an implicit `pip install agentbundle` step. Out-of-tree adopters who ship their own packs inherit the dependency whether they want it or not.
2. **SSO mismatch.** The three-tier model has no shape for session cookies — corporate SSO produces a cookie + TTL + refresh trajectory that doesn't fit "static token at one of three tiers."
3. **Lint conflation.** `tools/lint-credentialed-skills.sh` mixes security invariants (Don't-block presence, argv ban) with resolver-implementation details (dotfile substring). The two surfaces want to evolve independently.

[RFC-0013](../rfc/0013-credential-broker-contract.md) proposed a four-broker contract keyed on `metadata.auth` in skill frontmatter, plus a separate `credential-brokers` user-scope pack that ships the resolver as a build-pipeline-projected sibling file (in-process for static tokens) plus an adapter-root subprocess at `~/.agentbundle/bin/sso-broker.py` (for SSO cookies). The shape of the decision had several open axes the team needed to pin before any implementation PR could land — most importantly *which* brokers, *how many* transports, and *where* the broker code lives relative to the consumer skills.

## Decision

We adopted **four broker ids keyed on `metadata.auth`** with **two transports in v1**:

> Every credentialed skill declares `metadata.auth: <broker-id>` in its `SKILL.md` frontmatter. The four broker ids are `env` / `cli` / `creds` / `sso-cookie`. Broker-agnostic security invariants apply to every credentialed primitive regardless of broker (Don't-block presence, argv ban, never-logged, corporate-network env propagation); broker-specific lint extensions layer on top. Two transports ship in v1: an **in-process Python shim** (`credentials_shim.py` + per-platform Tier-2 backends, projected into each consumer's `scripts/` by the build pipeline) for `creds`; an **adapter-root subprocess** (`sso-broker.py` at `~/.agentbundle/bin/`, projected by a new build-pipeline primitive class) for `sso-cookie`. The catalogue contributes lint and naming convention only for `env` and `cli`.

Six derived rules pin the model concretely:

- **Naming.** The pack is `credential-brokers` (user-scope, declares `allowed-scopes = ["user", "repo"]` and `allowed-adapters = ["claude-code", "kiro", "codex"]`). The single LLM-cooperative exception is the `credential-setup` skill bundled in the same pack — its `description:` carries the verbatim phrase *"interactive, user-invoked, do not auto-run"* to keep the LLM from auto-running it.
- **Two new build-pipeline primitive classes.** `shared-libs/` projects `packs/<pack>/.apm/shared-libs/*.py` byte-identically into the `scripts/` of every skill in any pack declaring `metadata.auth: creds`. `adapter-root-bins/` projects `packs/<pack>/.apm/adapter-root-bins/*.py` to `$HOME/.agentbundle/bin/<basename>.py` at user scope (`<repo>/.agentbundle/bin/<basename>.py` at repo scope), mode `0o755` on POSIX.
- **Path-jail compliance.** Every projection target lives under the v0.7 contract's `allowed-prefixes` for the three named adapters. No PATH manipulation by the build pipeline. Consumers resolve the SSO broker via `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"` — one canonical path independent of adapter.
- **Drift gate.** `make build-check` errors on three drift outcomes (modified / missing / orphaned projected copies) with stderr naming the regeneration command; `make build-self` is the idempotent projector that resolves all three. Inter-pack basename collisions in `shared-libs/` are a hard-error at projection time.
- **Sequencing.** The `agentbundle.credentials` removal lands in the **last** PR of the migration sequence, after every in-tree consumer has migrated. The package release that performs the removal bumps `agentbundle` from `0.1.x` to `0.2.0`; intermediate PRs do not bump the minor. Adopters pin to `agentbundle < 0.2` until they migrate.
- **Contract bump.** `[contract] version` bumps `0.6 → 0.7` in `packages/agentbundle/agentbundle/_data/adapter.toml` and the mirror at `docs/contracts/adapter.toml`; the header comment names RFC-0013 alongside existing RFC pointers. `allowed-prefixes.user` for `claude-code`, `kiro`, and `codex` each carry `.agentbundle/` (already in place from prior contract versions — the bump is governance record-keeping, not a literal prefix-list change).

## Consequences

**Positive:**

- Out-of-tree adopters install `credential-brokers` as a user-scope pack; their credentialed skills resolve secrets without `pip install agentbundle`. The package becomes a CLI / build-pipeline / contract-tooling library, not a runtime dependency of consumer skills.
- SSO consumers get a first-class shape (`auth: sso-cookie`) instead of bolting cookie-jar handling onto a three-tier loader that wasn't designed for it.
- Lint and security invariants split cleanly: the broker-agnostic contract covers every credentialed primitive (Don't-block presence, argv ban, no plaintext dotfile reads); broker-specific AST walks (sibling-shim import for `creds`; per-`<NAMESPACE>_<KEY>` env read for `env`; canonical broker-path subprocess for `sso-cookie`) layer on top without conflation.
- The architectural rule from RFC-0006 — *skills don't hold credentials; primitives do* — is preserved structurally rather than degraded to prose: cleartext for static tokens never crosses an LLM-visible boundary; SSO cookie values stay inside the broker subprocess and the consumer subprocess; brokers are not LLM-auto-discoverable (they're not under any adapter's skills directory; the single setup-skill exception is named explicitly).

**Negative:**

- Two more build-pipeline primitive classes (`shared-libs/`, `adapter-root-bins/`) — more surface for the drift gate and more test cases for the projector. The risk is concentrated in `shared-libs/`'s many-to-many fan-out (one source → N consumers' `scripts/`); the drift gate's three-outcome distinction (modified / missing / orphaned) is the mitigation.
- The `agentbundle.credentials` removal is a forward-only break inside the 0.x window once `credential-brokers` publishes. Adopters who don't migrate before the 0.2.0 release pin to `agentbundle < 0.2`.
- Playwright is a runtime dependency of `sso-broker.py` (not of the `agentbundle` package). Corporate environments that gate `pip install` need to install it out-of-band; the broker carries an import-guard with a pinned stderr install instruction.

**Neutral / to revisit:**

- MCP-server transport for any broker is deferred (v1 is subprocess + in-process only). Additive evolution per RFC-0013 § 8 if a downstream consumer needs it.
- `sso-pat-mint` and similar OAuth/PAT-derived broker shapes are deferred until a concrete consumer surfaces.

## Alternatives considered

The numbering follows RFC-0013 § *Alternatives considered* for traceability. This ADR records the rejection of alternatives **B / D / E / F / G / H / I / J**; alternatives A and C are recorded in the RFC body and not re-litigated here.

- **(B) Add a `sso-cookie` broker only; keep `agentbundle.credentials` as the PyPI-shipped loader.** Solves the SSO mismatch without addressing portability or lint conflation. *Rejected:* leaves two of the three load-bearing problems unsolved; the migration cost is similar (consumer skills change shape either way) but the value-prop is partial.

- **(D) Single broker — collapse `env` / `cli` / `creds` / `sso-cookie` to one polymorphic `creds` broker.** Fewer broker ids, more polymorphism inside the loader. *Rejected:* the four brokers have different security invariants (argv ban applies uniformly; dotfile reads apply only to `creds`; canonical-path subprocess applies only to `sso-cookie`); collapsing them forces every lint check to be conditional and obscures the structural difference.

- **(E) Skip the `env` broker — require keychain-backed resolution always.** Forces every credentialed skill through Tier 2. *Rejected:* env-only credentials are a legitimate floor for adopters whose threat model permits process env (CI runners, ephemeral containers); the catalogue contributes lint and convention for `env` even though there's no runtime resolver.

- **(F) Pack bundling — `credential-brokers` is a meta-pack depending on `atlassian` and `converters`.** Couples the broker pack to its consumers. *Rejected:* the broker pack must ship at user scope independent of any consumer pack; meta-pack coupling defeats the portability goal.

- **(G) Subprocess broker for `creds` (the original v1 of this RFC).** Every `auth: creds` skill subprocess-invokes a broker at `~/.agentbundle/bin/creds-broker.py`. *Rejected:* the wrap-and-leak shape RFC-0006 § 5 explicitly refused — cleartext static tokens crossing a process boundary for no security gain over in-process resolution. The in-process shim is the floor.

- **(H) Ship the brokers as skills inside `<skills-dir>/`.** Every broker is itself a skill the LLM can discover and invoke. *Rejected:* the LLM auto-discovering a credential broker is exactly the threat model the brokers exist to prevent; brokers live at adapter-root (`~/.agentbundle/bin/`) or as projected sibling files in consumer `scripts/`, never as standalone skills. The single exception is the `credential-setup` skill — its LLM-cooperative discipline is named explicitly in the pack manifest description.

- **(I) Ship `credentials_shim` as a PyPI package consumers import.** Same shape as today's `agentbundle.credentials` but smaller package. *Rejected:* same portability problem (consumer carries an implicit `pip install`); the build-pipeline projection model produces a byte-identical sibling file with no PyPI dependency.

- **(J) Land the `agentbundle.credentials` removal as a follow-up to the new pack.** Two resolvers ship concurrently for some window. *Rejected:* the "two resolvers concurrently" shape produces drift the gate can't diagnose (which one is authoritative? does a consumer that imports from both still pass tests?); the sequencing rule — cleanup last, after every consumer migrates — keeps exactly one resolver authoritative throughout.

## References

- [RFC-0013 — Credential broker contract](../rfc/0013-credential-broker-contract.md)
- [RFC-0006 — Skill secrets storage](../rfc/0006-skill-secrets-storage.md) (the architectural rule and the Win32 error matrix this contract inherits verbatim)
- [`credential-broker-contract` spec](../specs/credential-broker-contract/spec.md) (the construction; 48 ACs across 15 tasks)
- [Migration guide for v0.6 → v0.7 pack adopters](../guides/how-to/v06-to-v07-pack-upgrade.md)
- [Add a credentialed skill — broker-first walkthrough](../guides/how-to/add-a-credentialed-skill.md)
