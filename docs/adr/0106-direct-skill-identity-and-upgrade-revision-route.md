# ADR-0106: Direct skill identity and upgrade revision route

- **Status:** Accepted
- **Date:** 2026-09-08
- **Decision-makers:** eugenelim
- **Related:** [RFC-0098](../rfc/0098-direct-skill-repository-installation.md) D4, D5, and D6

## Decision summary

- **Decision:** collision identity is `(source-kind, ref-stripped stored source,
  source-path)`. Revision and digest describe a version of that identity.
- **Decision:** `upgrade --skill <name> --source <source>` is the only route that
  moves a commit-pinned direct-skill row to another revision.
- **Decision:** the earlier old-capability re-derivation clause is replaced by
  the direct-upgrade capability decision: read the installed declaration only
  after binding its bytes to the row's recorded digest, then fail closed when
  that prior surface cannot be inspected.
- **Because:** RFC-0098 D4 makes revision changes upgrade-only, while D6 closes
  the published selector grammar without enumerating the source override needed
  to move a fixed commit. The prior capability clause did not define an
  integrity-bound source for the old declaration.
- **Applies to:** direct manifestless-skill collision checks and standalone
  direct-skill upgrades.
- **Tradeoff accepted:** repository spelling remains part of identity. A `.git`
  suffix or owner/repository case difference denotes a different identity even
  when acquisition would reach the same upstream bytes.
- **Revisit if:** a stored-source migration introduces a versioned canonical
  repository identity, or direct upgrade gains an explicit capability
  re-consent flow.

## Context

RFC-0098 D4 defines direct identity as `(source-kind, canonical source,
source-path)`, keeps revision and digest outside that identity, and permits them
to change only through upgrade. The installed row retains the requested source
spelling, including its ref, while acquisition separately resolves that request
to a commit.

For a row pinned to a full or abbreviated commit SHA, re-resolving the recorded
source is a fixed point. D4 nevertheless requires the upgrade route to be able
to move the row, and D6 presents a closed CLI grammar that does not enumerate a
revision override. The missing choice must therefore be recorded explicitly.

The installed projection is adopter-writable, so it cannot be trusted as
capability history merely because it occupies the expected path. A new revision
could otherwise be pre-written there and compared with itself, turning a
capability widening into an apparent no-op.

## Decision

### Identity uses stored spelling with only the ref removed

The collision identity is `(source-kind, ref-stripped stored source,
source-path)`. For `git+https`, ref stripping removes the trailing `@<ref>` from
the stored source. A local path is compared whole.

This decision deliberately does **not** use `canonicalize_source`. That helper
lowercases URL scheme and network location and resolves schemeless values from
the process working directory, transformations the stored direct-source value
did not necessarily pass through. The D4 canonical-source element is therefore
realized here as the stored direct-source spelling with only its revision
component removed.

No other normalization applies. A `.git` suffix and repository case remain as
stored, so two spellings of one upstream are two identities. The terminating
remediation for such a collision is remove-then-install.

### `--source` is the commit-pinned movement route

`upgrade --skill <name> --source <source>` is the only route that moves a row
whose stored `ref_kind` is `sha` or `abbreviated-sha`. It is also admitted for a
named ref because stored tags and branches cannot be distinguished from their
spelling alone.

The override may change only the ref-stripped source element after the selected
row's `source-kind` and `source-path` establish identity. A different repository
refuses. This satisfies D4's rule that revision changes happen only through
upgrade while extending D6's closed grammar with the one argument required to
make that route reachable for a fixed commit.

### Prior capabilities are integrity-bound before parsing

Direct upgrade reads the prior capability declaration from the installed
projection only after hashing the confined `SKILL.md` bytes and matching them
to the row's recorded file digest. The digest check precedes metadata parsing.
Missing, unreadable, malformed, unsafe, or digest-mismatched prior bytes produce
an unknown prior surface, and upgrade refuses rather than treating it as
unchanged.

This direct-upgrade capability decision replaces the earlier requirement to
re-derive old capability data from the projection without specifying an
integrity binding. No new state field is introduced; RFC-0098 D4's state schema
remains unchanged.

## Consequences

- A different ref of the same stored repository spelling remains the same
  identity and routes to standalone upgrade instead of becoming a second
  installable source.
- Repository respelling is intentionally not repaired in place. Remove-then-
  install is required for `.git` or case spelling changes.
- Commit-pinned rows can move without weakening D4's upgrade-only revision rule.
- Adopter-writable projection bytes cannot silently establish their own trusted
  capability history.
- An uninspectable prior declaration fails closed, so availability is traded
  for preserving the capability-consent boundary.

## Alternatives considered

- **Use `canonicalize_source` for identity.** Rejected because it adds URL and
  working-directory transformations that are not part of the stored identity
  contract and would make collisions depend on process context.
- **Treat each ref as a separate identity.** Rejected because D4 states that
  revision describes a version of an identity and may change only through
  upgrade.
- **Re-resolve commit-pinned rows without `--source`.** Rejected because a SHA
  re-resolves to itself and cannot express the wanted revision.
- **Trust the projected capability declaration by path.** Rejected because the
  adopter can modify that file; without the recorded-digest comparison, the new
  revision can be mistaken for the old consented surface.

## Confirmation

Identity tests distinguish local paths containing `@`, remote refs, `.git`
spellings, and repository case. Upgrade tests move full-SHA, abbreviated-SHA,
and named-ref rows through `--source`, reject another repository, and prove the
capability read checks the recorded digest before parsing. Integration coverage
also proves that an uninspectable prior surface refuses without writing.

## References

- [RFC-0098 D4](../rfc/0098-direct-skill-repository-installation.md#d4--manifestless-identity-and-lifecycle)
  — direct identity, provenance, and the upgrade-only revision rule.
- [RFC-0098 D5](../rfc/0098-direct-skill-repository-installation.md#d5--shared-deterministic-admissibility-gate)
  — the capability declarations and fail-closed admissibility boundary.
- [RFC-0098 D6](../rfc/0098-direct-skill-repository-installation.md#d6--cli-selection-preview-and-receipts)
  — the closed standalone-skill CLI grammar and selector semantics.
