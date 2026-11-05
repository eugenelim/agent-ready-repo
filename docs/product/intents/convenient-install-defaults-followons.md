# Convenient install default-source integrity

- **Slug:** `convenient-install-defaults-followons`
- **Level:** feature
- **Status:** Accepted
- **Owner:** eugenelim


## Outcome

The packaged default catalogue route (layer 5 of the source chain in `source_defaults.py`) resolves mutable main to an immutable commit SHA and verifies that the fetched archive bytes correspond to the recorded source identity before installing executable agent content.

## Boundary

- Preserve RFC-0046 and ADR-0036 source precedence, editable-install discovery, and the no-repository-source and no-current-directory rules.
- Limit this outcome to the existing default catalogue route; direct skill sources retain their RFC-0098 and ADR-0100 contract.
- Reuse established bounded, credential-free GitHub acquisition controls instead of introducing a second transport or verification stack.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- **Authority, answered:** RFC-0046 governs the default chain. The `Engine-Change-RFC:` gate only checks that a trailer is present, and earlier `source_defaults.py` commits cite RFC-0085. No follow-on RFC is needed.
- **Primitive, answered:** `direct_source_acquisition.acquire_git_https_archive` already acquires a credential-free GitHub archive with bounds and a redirect allow-list, and `_read_revision` reads the 40-hex commit SHA GitHub writes into the archive's pax header. The default route should reuse it instead of the plain `catalogue.py` fetch.
- **Design choice for the spec review:** resolve `main` once at install time, record that SHA, and refuse an archive whose pax SHA differs. The alternative, pinning a SHA in `install-defaults.toml` at release time, is stricter but leaves adopters on stale packs until they upgrade the CLI. The spec states the choice and its trade-off.

## Projection

- Resolve the RFC-authority question, then shape a security-reviewed full-mode delivery spec with mutable-ref, archive-mismatch, redirect, and rollback tests.

## Opportunity

The packaged layer-4 default currently acquires executable catalogue content from a mutable unauthenticated repository tip without a post-acquisition identity check.

## Assumptions

- The exact finish line in the frozen specification remains authoritative: resolve main to a full commit SHA and verify the fetched archive digest.


## Readiness

- **Route:** `new-spec`, full mode, security review. The change is on the acquisition path of executable agent content.
- **Verified 2026-11-05:** `read_packaged_default()` returns `git+https://github.com/eugenelim/agent-ready-repo` from `_data/install-defaults.toml`, and `catalogue.resolve_git_ref` maps a bare `git+https` source to `main` with no SHA check.
- **First slice and agent-only proof:** route the default through the direct-source acquirer, with tests against the local fixture server in `packages/agentbundle/tests/_direct_acquisition.py` for a moved ref, an archive SHA mismatch, a redirect off the allow-list, and rollback on failure. No live network.
- **Size:** one to two sessions.

## Source

- Mode: repo-origin
- Locator: docs/specs/convenient-install-defaults/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
