# Plan: agentbundle CLI-hygiene sweep

One PR. The `agentbundle 0.6.0 → 0.7.0` release is cut separately after merge;
this plan does NOT bump the version.

## Trio

- **Files touched**: `commands/_common.py` (new confirm helper),
  `commands/uninstall.py`, `commands/install.py`, `commands/upgrade.py`
  (refactor to the helper), `commands/reconcile.py`, `commands/list_targets.py`,
  `cli.py` (flags + docstring); tests under `tests/`; `docs/product/changelog.md`;
  `docs/backlog.md`.
- **Done when**: all ACs pass via `python -m pytest packages/agentbundle/tests/`;
  the four CLI verbs exercised end-to-end (real argparse invocation) for the new
  preview/confirm paths; existing string-pinning tests unchanged.
- **Not changing**: Tier-1/2/3 file-safety, upgrade target resolution,
  `reconcile` read-only posture, the profile/batch install path, the
  `--dry-run`/`--force` mutex.

**Declined temptations**: (1) extracting the multi-scope disambiguator into
`_common` — declined/deferred (see spec § Declined; divergent downstreams + pulls
`diff` into a path-jail refactor). (2) a generic `--dry-run` plan abstraction for
uninstall's remove/keep verbs — declining; `format_plan_line` is reused as-is and
uninstall prints its own one-line summary (its verbs differ from
install/upgrade's create/overwrite/companion, so `summarize_plan` doesn't fit).
(3) adding `--dry-run --force` preview to install — declining; confirm is the
preview, mutex kept.

## Task 1 — shared confirm helper in `_common.py`

`confirm_or_refuse(*, yes, question, refuse_message, abort_message) -> bool`:
returns True to proceed; on `yes` returns True without touching stdin; on
non-TTY prints `refuse_message` to stderr and returns False; on TTY reads
`input(question)` (EOF → ""), returns True only for `y`/`yes` (case-insensitive,
stripped), else prints `abort_message` and returns False. Caller owns the
`--dry-run` short-circuit (dry-run returns before calling).

- **Verification mode**: TDD.
- **Tests** (`tests/unit/test_confirm_helper.py`): yes→True no input; non-TTY→
  False + refuse_message on stderr; TTY "y"/"yes"/"  YES "→True; TTY "n"/""→False
  + abort_message; EOF→False.
- **Approach**: pure-stdlib helper; `sys.stdin.isatty()` + `input()`.

## Task 2 — refactor `upgrade.py` to the helper

Replace upgrade's inline confirm block (the `not yes and not dry_run` branch)
with a `confirm_or_refuse` call, preserving the exact `already_current` prompt
wording, the refuse message, and the `"upgrade: aborted; no changes made"`
abort message. The `already_current` "is already at … ; re-applying" stderr in
the `--yes`/`--dry-run` branch stays inline.

- **Verification mode**: goal-based (existing `test_upgrade_cmd.py` confirm
  tests are the contract — they must stay green unchanged).
- **Tests**: existing `test_upgrade_cmd.py::test_confirmation_*`,
  `test_yes_skips_prompt`, `test_non_tty_without_yes_refuses`,
  `test_dry_run_no_prompt_no_write`.
- **Depends on**: Task 1.

## Task 3 — `uninstall` dry-run + confirm

Restructure `uninstall.run` into a classification pass (build an ordered
`decisions: list[(relpath, "remove"|"keep")]`, printing jail/prefix
"refusing to touch" warnings as today, skipping absent files), then:
`--dry-run` → print `format_plan_line` per decision + one-line summary, return 0;
else `confirm_or_refuse` (skip on `--yes`); else the execution pass
(os.remove for `remove`, "keeping adopter-edited file" warning for `keep`),
then the existing hook-wiring unproject + prune + state write + summary.

- **Verification mode**: visual/manual QA (CLI) + integration tests.
- **Tests** (`test_uninstall_cmd.py`): update `_run_uninstall` to default
  `yes=True`, add `dry_run` param; add dry-run-writes-nothing, TTY accept/decline/
  EOF, `--yes`-no-input, non-TTY-refuses, remove/keep-parity.
- **Manual QA**: run `python -m agentbundle uninstall --pack <p> --dry-run` and
  the real confirm against a temp install; record stdout/exit.
- **Depends on**: Task 1.

## Task 4 — `install --force` confirm + `--yes` flag + upgrade offer

(a) Add `--yes` to install argparse (cli.py). (b) In `_classify_pre_rfc0012_state`,
thread `yes: bool`; in each `if force:` destructive branch, `confirm_or_refuse`
**before the first mutation** (decline → return 1, nothing deleted/popped/rewritten).
Dist-tree branch: list the subtree roots (`claude-plugins/<pack>`, `apm/<pack>`)
that exist — the actual `rmtree` unit — and gate the rmtree + `packs.pop` + state
rewrite atomically. Orphan branch: list the exact files, gate the `unlink` loop.
(c) In Step 4a (already-installed-at-requested-scope), keep the non-TTY/dry-run
refusal (message preserves `already installed at <scope>` + `use 'upgrade' to
change version`) but on TTY-without-`--yes` offer to upgrade, and on `--yes` run
upgrade. The handoff (`_offer_upgrade` helper) builds an upgrade namespace with
the FULL attribute set `upgrade.run` reads — `pack`, `catalogue`, `root`
(=`args.output`), `scope` (concrete `requested_scope`, never None), `yes=True`,
`dry_run=False`, `skill=agent=hook=seed=command=None`, `_user_config` threaded —
and returns `upgrade.run(ns)`.

- **Verification mode**: visual/manual QA (CLI) + integration tests.
- **Tests**: `test_install_inband_detection.py::test_b_force_cleans_*` +
  `test_install_orphan_reshape.py` + `test_orphan_cleanup_respects_foreign_state.py`
  pass `--yes`/`yes=True`; new tests for force-confirm-lists-paths,
  non-TTY-refuse-with-**zero-deletions** (assert subtree/orphans still on disk),
  offer-accept-runs-upgrade, `--yes`-runs-upgrade, non-TTY-keeps-refusal,
  dry-run-keeps-refusal.
- **Manual QA**: real argparse invocation of the offer + force confirm.
- **Depends on**: Task 1.

## Task 5 — drop dead `--scope` flags

Remove `--scope` from `reconcile` and `list-targets` in cli.py; remove the dead
`cli_scope != "user"` refusal in `reconcile.run`; update the cli.py module
docstring (RFC-0004 surface list) to drop `list-targets` and note `reconcile`.

- **Verification mode**: goal-based + unit.
- **Tests**: `test_cli_scope_flags.py` — move `list-targets` from accepted →
  rejected, add `reconcile`, fix the "six subcommands" docstring/count; assert
  `reconcile`/`list-targets` reject `--scope`. `test_reconcile.py` /
  `test_list_targets_cmd.py` unchanged in behaviour.
- **Depends on**: none (independent of Tasks 1–4).

## Task 6 — changelog + backlog

`docs/product/changelog.md` `[Unreleased]`: add the three bullets. `docs/backlog.md`:
record the deferred scope-disambiguator extraction.

- **Verification mode**: goal-based (CI changelog warn).
- **Depends on**: Tasks 3–5 (describes their shipped behaviour).
