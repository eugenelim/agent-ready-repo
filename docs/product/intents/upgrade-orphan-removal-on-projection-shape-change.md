# Upgrade orphan removal on projection-shape change

- **Slug:** `upgrade-orphan-removal-on-projection-shape-change`
- **Level:** feature
- **Status:** Accepted
- **Owner:** eugenelim


## Outcome

AgentBundle upgrade removes previously owned files that are absent from the newly computed projection, so adapter projection-shape changes do not leave stale artifacts.

## Boundary

- Limit deletion to files recorded as owned by the prior install state and absent from the new whole-pack projection.
- Preserve foreign and shared files, enforce the existing install-root confinement boundary, and keep uninstall plus reinstall as the workaround until this ships.
- Do not change recorded adapter identity or Kiro alias semantics.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- **Authority, answered:** the gate checks only that an `Engine-Change-RFC:` trailer is present. Earlier commits to `commands/upgrade.py` cite RFC-0008 and RFC-0098, and RFC-0022 governs the Kiro split this defect comes from. The spec cites the one that governs the upgrade contract it amends. No follow-on RFC is needed.
- **Ordering, proposed:** compute the new projection, write it, then remove each previously owned file that is absent from it and still inside the install root. If a write fails, remove nothing. Foreign and shared files, symlinks, and out-of-root paths are never removed.

## Projection

- Shape a dedicated full-mode delivery spec after the RFC-authority question is resolved; require deletion-confinement tests and security review.

## Opportunity

A legacy Kiro JSON install upgraded through the alias path writes the new Markdown projection but leaves the previously owned JSON artifact behind.

## Assumptions

- The expected-failure Kiro upgrade case remains the regression anchor until the replacement spec deliberately converts it to a passing test.


## Readiness

- **Route:** `new-spec`, full mode, security review.
- **Verified 2026-11-05:** `test_legacy_kiro_upgrade_orphans_stale_json_known_limitation` in `packages/agentbundle/tests/integration/test_upgrade_user_hooks.py` still runs as an expected failure (`x`). Upgrade unprojects removed hook-wiring rows only; it does not remove other owned files.
- **First slice and agent-only proof:** convert that test to a passing one, and add deletion-confinement tests (foreign file, shared file, symlink, path outside the root, failed write).
- **Size:** one to two sessions.

## Source

- Mode: repo-origin
- Locator: docs/specs/kiro-install-alias-parity/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
