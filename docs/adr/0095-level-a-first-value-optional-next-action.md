# ADR-0095: Level A first-value handoffs may include an optional next action

- **Status:** Accepted
- **Date:** 2026-08-22
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** none. Per [CONVENTIONS § Cite upward, never downward](../CONVENTIONS.md#specs), an ADR does not cite specs; the affected specs carry the forward pointer instead.

## Context

Level A currently guarantees a verification step but forbids a `Next:` line.
Core installation needs a deterministic adaptation handoff because local scope
has no adaptation marker and hook execution can be disabled, untrusted,
unsupported, path-broken, or output-incompatible.

The existing `next-action` metadata and installer output already provide this
concept for Level B packs.

## Decision

**We will allow Level A first-value metadata to include an optional
`next-action`, printed after `Verify:`.**

Level B continues to require `next-action`. Level A packs without it and packs
without first-value metadata retain their current output. Handoff text remains
pack-owned metadata rather than a core-specific installer branch.

## Decision drivers

- Guarantee onboarding independently of runtime hooks.
- Keep installer behavior pack-agnostic.
- Reuse an existing bounded metadata field.
- Preserve existing packs and output when the field is absent.

## Consequences

**Positive:**

- Core repo and local installs can provide the same deterministic next action.
- No new manifest field or core-name conditional is needed.
- Hooks remain an optional convenience.

**Negative:**

- Two shipped specs require status-only partial-supersession pointers.
- Successful installs of packs adopting this field gain one stdout line.
- `next-action` is no longer exclusively a Level B field.

**Revisit if:** post-install actions need semantics that do not belong in the
first-value contract.

## Confirmation

- **Mode:** lint/CI
- **Signal:** first-value lint and installer tests cover Level A with and
  without `next-action`, plus unchanged Level B behavior.
- **Owner:** agentbundle maintainers

## Alternatives considered

**Hard-code core behavior in the installer.** Rejected because it couples
generic installation logic to one pack.

**Add a separate install-manifest field.** Rejected because it duplicates the
existing bounded `next-action` concept and expands the schema.

**Rely on documentation or hooks alone.** Rejected because neither guarantees
an effective post-install handoff.
