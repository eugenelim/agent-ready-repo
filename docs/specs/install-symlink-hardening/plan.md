# Plan: install-symlink-hardening

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `build/projections/direct_directory.py` (shared helper), the six adapters,
  `render.py` (`_collect_tree`), a new unit test, version + both changelogs,
  `workspace.toml`.

**What demonstrates done**
- New tests covering four symlink shapes and the install walk; full agentbundle
  suite; `make ci`.

**What I am NOT changing**
- `build/main.py`'s `.apm`/`seeds` copytrees — correct as they stand.
- `lint_packs.py` — the install-path gate stays in the backlog.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **`path-and-file` / CWE-59 (link following), CWE-22.** The primitive is a
  symlink whose *relpath* is innocent while its target is not, so every
  path-confinement check upstream passes. Two mitigations now: nothing writes a
  link into a projection, and nothing reads through one at collect time. Either
  alone would close the observed path; both is deliberate, because the two sit on
  different code paths (direct-directory adapters vs `.apm`/seeds copytrees).
- **`supply-chain`.** The threat actor is an untrusted catalogue, which is the
  documented model for the install path. First-party packs are unaffected — a
  claim that is measured (zero symlinks in `packs/`), not assumed.
- **Failure mode chosen.** Silently dropping a member is weaker than refusing the
  pack. That refusal is `lint_pack` gating, deliberately left as the sibling
  entry's remaining scope rather than bundled into a change that is already
  touching seven modules.
- **What this does not do.** It does not stop a malicious pack shipping
  *content*; it stops it shipping content it does not own.

## Declined patterns

- **Tempted:** keep the permissive rule and add traversal confinement to it, so
  "intra-skill cross-references" survive. **Declined:** measured — no pack has a
  symlink and `lint_packs` forbids them, so the capability is unreachable. Two
  rules to maintain, for a feature nothing uses, on a security boundary.
- **Tempted:** also "fix" `build/main.py`'s `symlinks=True` sites for
  consistency. **Declined:** they are correct. Dereferencing there would
  materialise the target into `dist/` — the very thing being prevented.
- **Tempted:** gate install-path `render_pack` with `lint_pack` in the same PR.
  **Declined:** a different mechanism with a different failure mode (refuse vs
  drop) and its own compatibility question. Left as the sibling entry's scope.

## Anchor-test sweep

- No test pinned the adapters' private callbacks by name; the new AC7 test is
  what pins the shared one going forward.
- `tests/roster/test_workspace_status_projection.py` pins the release surface —
  re-run after the version bump (passes).

## Verification log

- **AC1/AC2** six adapters import the shared `ignore_symlinks`; no private
  definition remains (AC7 test enforces).
- **AC3** measured: `find packs -type l` -> 0; `lint_packs.py:482` rejects symlinks.
- **AC4/AC6** 5 tests in `test_adapter_symlink_policy.py` green, covering absolute,
  relative, nested-relative and in-tree links plus the `_collect_tree` walk.
- **Full agentbundle suite** green (exit 0).
- **AC8** 0.36.0 -> 0.36.1; roster release-surface test passes.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips (session
  instruction prohibits subagent dispatch). Security reasoning applied inline above.
