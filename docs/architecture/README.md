# Architecture

How the code is *currently* organized. Not why (that's in
[`../adr/`](../adr/)) and not what we want (that's in
[`../rfc/`](../rfc/)) — **what is**.

- [`overview.md`](overview.md) — the map of the monorepo. What's in
  `packages/`, `tools/`, `packs/`, and how they relate. Read this first.
- [`catalogue.md`](catalogue.md) — what a catalogue *is* on disk, how
  `agentbundle` resolves one (the four-layer chain), and how to point it
  at your own. The starting point for standing up your own catalogue.
- [`skill-and-pack-format.md`](skill-and-pack-format.md) — the format map:
  the agentskills.io skill standard we conform to, the pack envelope that
  wraps it, and the projection that fans it out to every agent.
- [`pack-layout.md`](pack-layout.md) — the canonical shape of a single
  pack: `pack.toml`, `.claude-plugin/`, `.apm/<primitive>/`, `seeds/`.
  What each directory contains and how the bundler reads it.
- [`pack-manifest.md`](pack-manifest.md) — `pack.toml` as the single
  source of truth for pack metadata, and how the build projects a lossy
  subset into each route's manifest and the catalogue listing.
- [`agentbundle.md`](agentbundle.md) — the `agentbundle` Python package:
  CLI verbs, bundler internals (recipes → adapters → projections), the
  adapter contract, and the install→adapt chain.
- [`security.md`](security.md) — the security-review posture: all enforced frameworks
  (OWASP Top 10:2025 through OWASP Agentic Skills Top 10 v1.0), the three-bucket
  delegation model, Module index routing, and the shift-left secure-design pass.
- [`credentials.md`](credentials.md) — the credential-loading subsystem:
  three-tier storage, the `credbroker` library resolver (RFC-0023, which
  replaced the build-projected `credentials_shim` of RFC-0013),
  the four-broker contract (`creds` / `env` / `cli` / `sso-cookie`),
  the credentialed-primitive model, and the substring trap.

Add one more `<subsystem>.md` whenever a non-trivial subsystem grows up
that doesn't fit cleanly under an existing page. Each describes the
structure, the entry points, and links to the ADRs that explain why.

Architecture docs are the *rolled-up snapshot* — the answer to "what
does this codebase look like today" without replaying ADR history.
Lifecycle: living. Update whenever the layout or major dependencies
change.

Note for contributors: the bundle's source-of-truth split (skills,
agents, hooks, commands, hook-wiring, and pack seeds all live under
`packs/<pack>/`) is described in
[`../CONVENTIONS.md` § Pack source-of-truth split](../CONVENTIONS.md#pack-source-of-truth-split).
Anything in this directory documents the *projected* layout adopters
end up with; the pack-side authoring rules are in CONVENTIONS.
