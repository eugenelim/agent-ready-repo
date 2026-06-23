# Plan: upgrade — derive target version, confirm interactively

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is local to two files plus their tests, then docs. In `cli.py`,
the `upgrade` subparser drops `--to` and gains `--yes`. In
`commands/upgrade.py`, `run()` stops reading `args.to_version`: after the pack
manifest and current state are both loaded, it derives the target version from
the resolved `pack.toml` `[pack] version`, captures the `from` version from
state, and — unless `--yes` or `--dry-run` — confirms interactively before the
write loop. The write loop, Tier contract, path-jail, and hook-wiring
reconciliation are untouched; only the version *source*, a confirmation gate,
and the recap string change.

The riskiest part is the test surface: the `upgrade` command is exercised by
several integration tests that pass `to_version=` into a `SimpleNamespace`.
Those helpers and call sites are updated to drop `to_version` and default
`yes=True` (so existing tests don't block on `input()`), while new tests cover
the derive / confirm / refuse / `--yes` / non-TTY / missing-version paths.

## Constraints

- No ADR/RFC governs the `upgrade` CLI surface; this is a repo-owned package
  change. The multi-scope disambiguator (RFC-0004) and Tier-1/2/3 write
  contract are *not* modified — the change rides entirely above them.
- CLAUDE.md "add a flag only when a second caller needs to differ": `--yes` is
  justified by a real second caller — non-interactive / CI use, which cannot
  answer a prompt. `--to` fails that test (no second behavior) and is removed.

## Construction tests

**Integration tests:** covered per-task below (all `upgrade` behavior is
exercised through `run()` / `build_parser`).
**Manual verification (performed 2026-06-23, real built CLI against the
`tests/fixtures/upgrade` catalogues):**

```
$ agentbundle upgrade --pack core <catalogue_v2> --root <repo> --yes
upgraded: core @ repo 0.1.0 -> 0.2.0                 # exit 0

$ agentbundle upgrade --pack core <catalogue_v2> --root <repo> --yes   # again
upgrade: core is already at 0.2.0; re-applying
upgraded: core @ repo 0.2.0 -> 0.2.0                 # exit 0

$ agentbundle upgrade --pack core <catalogue_v2> --root <repo>         # non-TTY, no --yes
upgrade: refusing to upgrade core from 0.2.0 to 0.2.0 without confirmation;
pass --yes to upgrade non-interactively               # exit 1, nothing written
```

The interactive decline path (`y/N` → non-affirmative → `aborted; no changes
made`) is exercised by `test_confirmation_decline_writes_nothing` (a real TTY
can't be simulated in a shell pipe, which is non-TTY and hits the refusal).

## Design (LLD)

### Design decisions
- Target version = resolved `pack.toml` `[pack] version`; no resolver, no
  history store (git refs are the history). Traces to: AC1, AC8.
- Confirmation reads `builtins.input` only when `sys.stdin.isatty()` and not
  `--yes`/`--dry-run`; non-TTY without `--yes` refuses rather than blocking.
  `run()` reads the new flag as `getattr(args, "yes", False)` (mirroring the
  existing `getattr(args, "dry_run", False)` at `upgrade.py:370`) so direct
  `Namespace`/`SimpleNamespace` callers that don't set `yes` default to
  prompting, never an `AttributeError`. Traces to: AC3–AC6, AC9.
- `from` version captured *before* state is mutated: whole-pack →
  `installed_version`; per-primitive → `primitive_versions[ptype][name]` if
  recorded, else `installed_version`. Traces to: AC2, AC7.

### Failure, edge cases & resilience
- Missing `[pack] version` in the resolved catalogue → non-zero with a
  catalogue-pointing message, before any prompt or write. This is a *new*
  check: `check_spec_version_gate` (`upgrade.py:185`) reads only
  `[pack.adapter-contract] version`, so a pack with `[pack]` but no `version`
  passes the gate and must be caught at derivation. Traces to: AC8.
- The per-file `from-pack-version` metadata written into `pack_state.files`
  (`upgrade.py:441,455`) keeps recording the *target* version (the derived
  `to_version`); the version-source change does not alter that field's
  semantics, nor the Tier contract, path-jail, or hook-wiring reconciliation.
  Traces to: AC7.
- `EOFError` on `input()` (piped empty stdin reaching the prompt) → treated as
  a non-affirmative reply. Traces to: AC3.

## Tasks

### T1: `upgrade` parser drops `--to`, gains `--yes`

**Depends on:** none

**Tests:**
- Unit: `build_parser` parses `upgrade --pack core <catalogue>` with no `--to`
  and no error; the resulting namespace has no `to_version`. (AC7)
- Unit: `upgrade --pack core --yes <catalogue>` sets `args.yes is True`;
  default is `False`. (AC5)
- Unit: `upgrade --pack core --to 0.2.0 <catalogue>` now errors (unknown
  argument), proving the flag is gone. (AC7)
- Unit: `upgrade --pack core --skill a --agent b <catalogue>` errors (mutually
  exclusive), proving the primitive-flag group rejects two at once. (AC12)
- Update `tests/unit/test_cli_scope_flags.py` and
  `tests/unit/test_cli_path_normalisation.py` to drop `--to 0.2.0` from the
  `upgrade` argv fixtures.

**Approach:**
- In `cli.py` upgrade subparser: delete the `--to` `add_argument`; add
  `sp.add_argument("--yes", action="store_true", help="Skip the upgrade
  confirmation prompt (for non-interactive use).")`.
- Move the five `--skill`/`--agent`/`--hook`/`--seed`/`--command` arguments
  into `sp.add_mutually_exclusive_group()` so argparse rejects two at once
  (closes the silent-take-first footgun at `upgrade.py:152-157`). This is the
  one approved same-command ride-along beyond the version/confirm change.

**Done when:** the four parser unit tests pass and the two updated argv
fixtures still pass.

### T2: `run()` derives the version, confirms, and shows `from → to`

**Depends on:** T1

**Tests:** (in `tests/integration/test_upgrade_cmd.py` unless noted)
- Whole-pack upgrade with no `to_version` arg upgrades to the catalogue's
  declared version; `state.installed_version == "0.2.0"`. (AC1)
- Recap line matches `upgraded: core @ repo 0.1.0 -> 0.2.0`. (AC2)
- Per-primitive recap matches `upgraded: core <ptype>/<name> @ repo <from> ->
  0.2.0`, with `from` = recorded primitive override when present else
  `installed_version`. (AC2, AC7)
- Decline (`input` monkeypatched to return `"n"`, `isatty` → True): exit
  non-zero, `state.installed_version` unchanged, stdout/stderr include
  `aborted; no changes made`, no projected file rewritten. (AC3)
- Accept (`input` → `"  YES "`, `isatty` → True): exit 0, upgrade applied. (AC4)
- `--yes` (`yes=True`, `isatty` → False): exit 0, `input` never called
  (monkeypatch raises if called). (AC5)
- Non-TTY refusal (`yes=False`, `isatty` → False): exit non-zero, message
  names `--yes`, nothing written, `input` never called. (AC6)
- Missing `[pack] version`: build a `tmp_path` catalogue with a `pack.toml`
  lacking `version`, install a normal pack, then upgrade against it → exit
  non-zero with a catalogue-pointing message. (AC8)
- `--dry-run` with no `to_version` and `isatty` → True: plan printed, `input`
  never called, no write, exit 0. (AC9)
- EOFError at the prompt (`input` monkeypatched to raise `EOFError`, `isatty` →
  True): treated as decline — exit non-zero, nothing written. (AC3)
- Already-current: install 0.2.0 then upgrade against the same 0.2.0 catalogue —
  `--yes` path states `is already at 0.2.0` on stderr and re-applies (rc 0);
  interactive path's prompt contains `already at 0.2.0` and `Re-apply`. (AC13)

**Test migration is assertion-aware, not mechanical kwarg removal.** Removing
`--to` means the target is *derived* from each fixture's `[pack] version`, so
any test that today passes a `to_version=` that differs from its fixture's
declared version (it only "worked" because `--to` was unvalidated) breaks at
*assertion* time, not collection. For **every** `to_version=` / `--to` call
site, check the fixture's `[pack] version` and reconcile: drop the kwarg, add
`yes=True`, and align the version assertion to the derived value (or bump the
fixture's `[pack] version` to the intended target). Known mismatches to
reconcile (verified, not exhaustive — grep `to_version=` and `"--to"` and
re-check each):
  - `test_install_dual_scope.py:279,365` — `PACK_TOML_BOTH` declares
    `version = "0.1.0"` but the test passes `to_version="0.2.0"` and asserts
    `installed_version == "0.2.0"`; derivation yields `0.1.0`. Bump the fixture
    to `0.2.0` (it is the upgrade target the test intends) **or** assert
    `"0.1.0"`.
  - `test_upgrade_user_hooks.py:91,148,196` and
    `test_upgrade_attach_to_agent.py:94` — fixtures stay `0.1.0` across the
    catalogue mutation but pass `to_version="0.2.0"`; assertions key on
    hook-wiring/agent JSON, not version, so align to the derived `0.1.0` (or
    bump the mutated fixture).
  - `test_version_gate_matrix.py:158` — passes `to_version="0.2"` against an
    adapter-contract-gated fixture; the spec-version gate fires before
    derivation, so this stays a refusal test — just drop the kwarg.
  - `test_install_user_scope_allowed_adapters.py:165` (`to_version="0.1.0"`),
    `test_tier_invariants.py:215`, `test_state_v01_refuse_write.py:106` — drop
    the kwarg and confirm the derived version matches the assertion (or that
    the test returns before version matters, e.g. the v0.1 refuse-write path).
  - `test_install_repo_scope_per_adapter.py:377` — argv `--to 0.1.0` against
    `REPO_ROOT`, whose real `packs/core/pack.toml` `[pack] version` is now
    `0.4.14`, so derivation yields `0.4.14`; drop `--to` (no version assertion
    follows, so it just proceeds). Its sibling at `:511` reads
    `installed_version` from state for the `--to` value and is already
    bump-safe — just drop the `--to` there too.
  - Helpers: update `_args_upgrade` (`test_upgrade_cmd.py:33`) and
    `_upgrade_args` (`test_upgrade_user_hooks.py:49`) to drop `to_version` and
    add `yes: bool = True`; update the inline `SimpleNamespace` upgrade callers
    in `test_install_dual_scope.py` and
    `test_install_user_scope_allowed_adapters.py` likewise.

**Approach:**
- In `upgrade.py:run()`, remove `to_version = args.to_version`. After
  `pack_state` is resolved, compute `from_version` (whole-pack vs
  per-primitive), derive `to_version` from `pack_toml["pack"]["version"]`
  (error non-zero if absent/non-str), then if not `args.yes` and not
  `dry_run`: refuse on non-TTY, else prompt and require `y`/`yes`.
- Thread `from_version` into the two recap `print` lines.
- Ride-along (bundled fix, same file/concern): update the `upgrade.py` module
  docstring and `run()` docstring — remove the `args.to_version` "required, from
  `--to`" line from the `run()` `Args:` block and add an `args.yes` line, and
  reword the module docstring's "Update `PackState.installed_version` to
  `args.to_version`" to describe derivation from `pack_toml["pack"]["version"]`.

**Done when:** all new and updated tests in the listed files pass under
`python -m pytest packages/agentbundle/tests/`.

### T3: docs — PyPI README, root README Quick Start, CHANGELOG

**Depends on:** T2

**Tests:** goal-based — `grep` confirms the README shows no `--to` and shows
`--yes`; manual QA (build + run) per Construction tests above.

**Approach:**
- `packages/agentbundle/README.md`: rewrite the `upgrade` example to drop
  `--to`, show the confirmation + `--yes`, and the `from → to` recap. (AC10)
- Root `README.md`: add a concise **Quick start** section near the top with the
  most common commands — install `core` at repo scope, install a pack at user
  scope, and upgrade. (AC11)
- `packages/agentbundle/CHANGELOG.md`: add an `[Unreleased]` entry under
  `Changed` (breaking: `--to` removed) and `Added` (`--yes`).

**Done when:** `grep -c -- '--to' packages/agentbundle/README.md` is 0 in the
upgrade section, the root README renders a Quick start block, and the manual
e2e run is recorded in the PR.

## Rollout

Pure CLI change, no infra. Breaking: scripts calling `agentbundle upgrade
--pack X --to V <cat>` must drop `--to` and add `--yes` for non-interactive
use. Rollback is a straight revert. Ships with an agentbundle version bump at
release time (surfaced as a release decision, not in this PR's scope unless
asked).

## Risks

- The `upgrade` test surface is wide; a missed `to_version=` call site fails
  loudly at collection (unexpected kwarg) rather than silently — acceptable.
- The first interactive prompt in this CLI: the non-TTY guard is the load-
  bearing safety so CI never hangs. Covered by AC6.

## Changelog

- 2026-06-23: initial plan.
