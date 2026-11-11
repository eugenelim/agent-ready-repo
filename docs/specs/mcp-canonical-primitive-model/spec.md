# Spec: MCP is a declared pack primitive that the build admits or refuses

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (protected `packages/agentbundle/**` and `contracts/`, and a security boundary: what an MCP server may execute)
- **Constrained by:** RFC-0092 (D5, D7, § P7)
- **Brief:** brief:canonical-mcp-install-parity-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** `contracts/distribution-routes.toml`, `contracts/distribution-routes.schema.json`, `contracts/adapter.toml`, `contracts/adapter.schema.json`
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

A maintainer can declare an MCP server in a pack and the build either accepts it into the pack model or refuses it with a named reason. No pack can declare MCP and have it silently dropped, because the build refuses any MCP declaration until direct install and route projection exist.

## What Changes

- The pack model gains an MCP source form and validation, built on the vendored portable schema `contracts/vendor/agent-plugins/1.0.0/mcp.schema.json`. No MCP primitive exists today: `PRIMITIVE_DIRS` in `build/main.py` lists five primitives and none is MCP.
- Admission rules from RFC-0092 § P7 run at build time: stdio servers, remote servers, and secret-bearing headers.
- Each route's `component-capabilities` gains an `mcp` row, written `dropped` on `apm`, `agent-plugin`, and `claude-plugins`. The route schema lists the nine capability keys as required with `additionalProperties: false`, so its three per-route blocks gain `mcp` too.
- The adapter contract gains a declaration of which adapters can hold MCP, recorded from client documentation as `documentation-verified`.
- A parity test asserts that every adapter declaring MCP and every route with a non-`dropped` MCP row has a projection. It runs over synthetic claimants here and is extended by the install and route slices.
- Until those slices land, the build and install refuse any pack that declares MCP.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable | `contracts/` files named above | eugenelim | Schema and TOML validate | Contract tests green |
| Current architecture | Applicable | `docs/architecture/distribution-routes.md` | eugenelim | Page names the MCP row and the refusal | Page updated |
| Release history | Applicable | agentbundle changelog and version bumps | eugenelim | One entry | Entry present |
| User promise | Not applicable: nothing user-visible ships until the install slice | none | none | none | none |

## Agent Rules

### Always do

- Cite RFC-0092 § P7 for admission rules; do not restate the lists.
- Treat the stdio clauses as stdio-only; a remote server has no `command`.
- Keep the primitive transport-first so a later acquisition descriptor can be added.

### Ask first

- Any change to RFC-0092 text, or a schema field that adds an install command.

### Never do

- Never rely on schema validity to protect credentials; a secret-bearing header is schema-valid.
- Never let a pack that declares MCP build successfully before the install and route slices land.

## Testing Strategy

- **TDD** with offline fixtures for each admission outcome; no network.
- **Goal-based** for contracts: the existing contract tests plus a test that the `mcp` row exists on all three routes.
- The parity test is TDD over synthetic claimants.

## Acceptance Criteria

- [ ] A pack declaring a stdio server whose command is a registry launcher named in RFC-0092 § P7 fails the build with a diagnostic naming the launcher rule.
- [ ] A pack declaring a stdio server whose command is a shell, a bare interpreter, or a PATH-resolved bare name fails the build with a diagnostic naming that rule.
- [ ] A pack declaring a remote server with a secret-bearing `Authorization` header fails the build with a diagnostic naming the secret rule.
- [ ] A pack declaring a `streamable-http` or `sse` server with no `command` passes the stdio clauses.
- [ ] A pack declaring any MCP server fails `agentbundle render` and `agentbundle install` with a message saying MCP projection is not yet available.
- [ ] `contracts/distribution-routes.toml` carries an `mcp` row, with status `dropped`, on each of `apm`, `agent-plugin`, and `claude-plugins`, and the contract validates.
- [ ] The parity test fails for a synthetic adapter that declares MCP with no projection.
- [ ] The parity test fails for a synthetic route with a non-`dropped` MCP row and no projection.
- [ ] Existing build output for all packs without MCP is byte-identical to the committed golden fixtures.

## Follow-ons

- eugenelim: [`canonical-mcp-install-parity-delivery`](../../product/briefs/canonical-mcp-install-parity-delivery.md) slices M2 and M3 — direct install, then `native` rows on `agent-plugin` and `claude-plugins`.

## Assumptions

- Technical: the authoring location and shape. Default: `packs/<pack>/.apm/mcp/<name>.json`, holding the vendored portable shape (settled by: eugenelim). If wrong: only the loader path changes.
- Technical: which adapters can hold MCP. Default: the plan records each from client documentation and leaves undocumented ones undeclared (settled by: the documentation read). If wrong: an adapter is added later without a schema change.
- Defaulted: Engine-Change-RFC: cite RFC-0092 (settled by: eugenelim).
- Defaulted: [FEAT-0020](../../product/intents/FEAT-0020-distribution-route-set-opening.md) is not a dependency. If it ships first, the three per-route schema edits above disappear and the `mcp` row is TOML only.
