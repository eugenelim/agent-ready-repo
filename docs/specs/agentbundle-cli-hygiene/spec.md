# Spec: agentbundle CLI-hygiene sweep

- **Status:** Shipped
- **Mode:** full (risk triggers: public-interface change; destructive/irreversible operation; security boundary — file deletion)

Follow-up to merged PR #374 (which removed `agentbundle upgrade --to` and
added a derive-version-from-catalogue + interactive-confirm flow). This sweep
applies the same critical lens to the rest of the `agentbundle` CLI surface:
the mutating verbs that lack a preview/confirm, and two dead `--scope` flags.

## Objective

Bring the remaining `agentbundle` CLI verbs up to the safety bar PR #374 set
for `upgrade`: every mutating verb previews and confirms before it writes or
deletes, and dead flags are removed. Specifically:

1. `uninstall` gains `--dry-run`, `--yes`, and an interactive confirmation —
   today it is the only mutating verb with no preview, and it `os.remove`s
   every Tier-1 file immediately.
2. `install --force` confirms (listing the paths) before its destructive
   cleanup — today the cleanup (`rmtree` of `claude-plugins/<pack>` and
   `apm/<pack>`, plus orphan `unlink`) runs with no preview, and `--force` is
   mutex with `--dry-run`, so the deletion is unpreviewable.
3. `install` gains `--yes` and turns its already-installed "use 'upgrade'"
   refusal into an interactive offer that runs the upgrade on confirmation.
4. The dead `--scope` flags on `reconcile` (single legal value `user`, also the
   default) and `list-targets` (parsed but never read) are dropped.

The confirmation / non-TTY-refuse / `--yes` mechanics are factored out of
`commands/upgrade.py` into a shared `commands/_common.py` helper and reused.

## Acceptance Criteria

### `uninstall` preview + confirm

- [x] **AC1** — `uninstall --dry-run` previews the per-file plan (one line per
  recorded file: `remove tier-1 <path>` for files whose on-disk SHA matches the
  recorded SHA, `keep tier-2 <path>` for adopter-edited / SHA-mismatched files)
  plus a one-line summary, and writes nothing: no file removed, no state
  rewrite, no hook-wiring unproject, no empty-dir prune. Exits 0.
- [x] **AC2** — `uninstall` without `--dry-run` and without `--yes`, on an
  interactive TTY, prompts before the first `os.remove`; declining (anything
  other than `y`/`yes`, including EOF) aborts with a stderr message and writes
  nothing (exit 1).
- [x] **AC3** — `uninstall --yes` proceeds without reading stdin (never calls
  `input()`).
- [x] **AC4** — `uninstall` on a non-TTY stdin without `--yes` refuses with a
  stderr message naming `--yes`, never blocks on `input()`, and writes nothing
  (exit 1). `--dry-run` short-circuits this refusal (a dry run writes nothing,
  so it is safe non-interactively without `--yes`).
- [x] **AC5** — the remove/keep decision shown by `--dry-run` and the prompt's
  file counts are computed by the same Tier-1/Tier-2 classification the real
  removal uses; a real `uninstall --yes` removes exactly the files `--dry-run`
  labelled `remove` and preserves byte-for-byte exactly those labelled `keep`
  (the existing Tier-2 preservation contract is unchanged). The execution pass
  acts on the classification pass's recorded decisions — it does **not** re-hash
  between the preview/prompt and the `os.remove` — so the bytes shown are the
  bytes removed (the Tier-1 SHA is captured once, at classification time; the
  confirm-reading window is not re-checked, matching the no-divergence property
  the preview promises).

### `install --force` confirm

- [x] **AC6** — when `install --force` would delete on-disk paths, it lists what
  it will remove on stderr and confirms before deleting. The listed unit is the
  actual deletion unit: for the dist-tree branch, the subtree roots
  (`claude-plugins/<pack>`, `apm/<pack>`) that `shutil.rmtree` removes (not an
  rglob file list that could diverge from what `rmtree` actually takes); for the
  orphan branch, the exact files to be `unlink`ed. The confirm gates the **whole
  destructive block atomically** — for the dist-tree branch that is the `rmtree`
  **and** the in-memory `repo_state.packs.pop` **and** the `.agentbundle-state.toml`
  rewrite — so declining returns 1 having mutated neither disk files, nor the
  state file, nor in-memory state (the confirm sits before the first mutation).
- [x] **AC7** — `install --force --yes` performs the cleanup without reading
  stdin; `install --force` on a non-TTY stdin without `--yes` refuses (names
  `--yes`) and exits 1 with **zero** filesystem deletions — the subtree / orphan
  files still exist on disk after the refusal (the refuse is the first
  side-effecting gate, reached before any `rmtree` / `unlink`).
- [x] **AC8** — `install --force` that does NOT trigger a destructive cleanup
  (e.g. the cross-scope-conflict bypass, where nothing on disk is deleted) does
  not prompt — behaviour is unchanged from today.
- [x] **AC9** — `--dry-run` remains mutex with `--force` (the existing refusal
  is kept); the confirm is the preview mechanism for `--force`.

### `install` → `upgrade` offer

- [x] **AC10** — `install` gains `--yes` (defaults False), accepted by argparse.
- [x] **AC11** — `install` of a pack already installed at the requested scope,
  on an interactive TTY without `--yes`, offers to run `upgrade` instead;
  confirming runs the whole-pack upgrade against the same catalogue/scope and
  returns its exit code. The handoff passes the **concrete** install-resolved
  scope (never `None`) so `upgrade`'s own multi-scope disambiguator is a no-op.
- [x] **AC12** — `install --yes` of a pack already installed at the requested
  scope runs the upgrade without prompting (the handoff calls `upgrade.run` with
  `yes=True`, since the install-side offer is the confirmation).
- [x] **AC13** — `install` of an already-installed pack on a non-TTY stdin
  without `--yes` (the existing behaviour for CI) still refuses with a stderr
  message containing `already installed at <scope>` and `use 'upgrade' to
  change version`, and exits 1 — no silent upgrade. `install --dry-run` of an
  already-installed pack keeps the same refusal (no offer, no prompt).
- [x] **AC14** — the offer applies to the single-pack `install` path only; the
  profile/batch path's already-installed handling (skip already-installed packs
  before calling `run`, per `docs/specs/pack-profiles/spec.md` AC6 / RFC-0034)
  is unchanged and still never emits the "use 'upgrade'" line
  (`test_install_profile.py` pins `"use 'upgrade'" not in err`).

### Dead-flag removal

- [x] **AC15** — `reconcile` no longer registers `--scope`; `reconcile` (no
  flag) runs the user-scope report exactly as before, and `reconcile --scope
  user` now refuses with the documented `unknown flag for reconcile: --scope`.
- [x] **AC16** — `list-targets` no longer registers `--scope`; `list-targets`
  output is unchanged, and `list-targets --scope user` refuses with
  `unknown flag for list-targets: --scope`.

### Shared mechanics

- [x] **AC17** — the confirm/refuse/`--yes` *decision* (yes→proceed; non-TTY→
  refuse; TTY→prompt; `y`/`yes`→proceed, else→abort; EOF→abort) lives in one
  helper in `commands/_common.py`, used by `uninstall`, `install --force`, the
  `install`→`upgrade` offer, and `upgrade` (refactored to call it). Command-
  specific pre/post messaging (e.g. `upgrade`'s already-current "re-applying"
  notice in its `--yes`/`--dry-run` branch, and the per-branch path listing for
  `install --force`) stays at the call site, which passes the
  `question`/`refuse_message`/`abort_message` strings — so the exact stderr
  strings every existing test pins are preserved.

## Boundaries

### Always do

- Route every write/delete through the existing `safety.write_jailed` /
  path-jail and Tier classification — the confirm/preview sits *in front of*
  those, never replaces them.
- Preserve the exact stderr substrings existing tests assert (notably
  `already installed at <scope>` + `use 'upgrade' to change version`, and the
  Tier-2 "keeping adopter-edited file" preservation contract).

### Ask first

- Any change to the upgrade target-resolution or Tier-classification logic
  itself (this sweep is about preview/confirm and flag hygiene, not re-deriving
  what gets written).

### Never do

- Do not allow `--dry-run --force` on `install` (kept mutex; the confirm is the
  preview for `--force`).
- Do not add a `--apply` mode to `reconcile` (it stays read-only).
- Do not change the Tier-1/2/3 file-safety contract or what `uninstall` /
  `install` actually remove.
- Do not extend the install→upgrade offer to the profile/batch path.

## Testing Strategy

- Unit (argparse surface): `--yes` on `install` defaults False and is accepted;
  `--scope` removed from `reconcile` and `list-targets` (rejected with the
  documented stderr); existing `--scope`-accepted set drops `list-targets`.
- Integration (`uninstall`): dry-run previews + writes nothing; TTY confirm
  accept/decline/EOF; `--yes` skips prompt; non-TTY refuses; remove/keep parity
  with the real run.
- Integration (`install --force`): destructive cleanup confirms + lists paths;
  `--yes` skips; non-TTY refuses + deletes nothing; non-destructive `--force`
  does not prompt.
- Integration (`install`→`upgrade`): TTY offer accept runs upgrade; `--yes`
  runs upgrade; non-TTY + no `--yes` keeps the refusal; dry-run keeps refusal;
  profile path unchanged.
- Confirm-helper TTY/non-TTY/EOF behaviour is exercised through the four call
  sites; `upgrade`'s existing confirm tests continue to pass unchanged.

## Assumptions

- **Verified** — `install --yes` semantics: `--yes` answers yes to both the
  force-cleanup confirm and the upgrade offer (one flag, two confirm sites).
  This makes `install --yes` on an already-installed pack run an upgrade rather
  than no-op-refuse; this is the intended "make it so" semantic and is
  documented in the changelog.
- **Verified** — the force-confirm is placed inside the destructive branches of
  `_classify_pre_rfc0012_state`, so `--force` used purely as a cross-scope
  bypass (no on-disk deletion) does not prompt; only the rmtree/unlink paths do.
- **Verified** — the install→upgrade handoff constructs an `upgrade` args
  namespace carrying the full attribute set `upgrade.run` reads: `pack`,
  `catalogue` (the install catalogue), `root` (= `install.output`), `scope` (the
  **concrete** install-resolved scope, never `None`), `yes=True` (the install
  offer is the confirmation), `dry_run=False`, all five primitive flags
  (`skill`/`agent`/`hook`/`seed`/`command`) set `None` (whole-pack), and
  `_user_config` threaded through (so adapter resolution matches a direct
  `upgrade` invocation). It calls `upgrade.run` and returns that exit code.

### Backward-compatibility note

- `install --force` used purely as a **cross-scope-conflict bypass** (no on-disk
  deletion) is unchanged — it does not prompt and runs non-interactively as
  before (AC8). But `install --force` that would **delete** files (the
  pre-RFC-0012 dist-tree cleanup or orphan cleanup) now refuses on a non-TTY
  stdin without `--yes`, where previously it deleted unattended. CI that relies
  on the deleting form of `--force` must add `--yes`. This is the intended
  safety hardening (it mirrors `upgrade`'s non-TTY posture from PR #374) and is
  called out in the changelog.

## Declined / deferred

- **Extracting the multi-scope disambiguator block** (duplicated across
  `uninstall` / `upgrade` / `diff`) into `_common` — *deferred* (backlog anchor
  `scope-disambiguator-extraction`). The shared part (read both state files +
  the identical "installed at multiple scopes" refusal) is real, but each
  command's downstream diverges sharply (root rebind + `user_prefixes`;
  `allowed_prefixes` + recorded adapter; `pack_state` for the render-shape pick),
  so a helper leaves most of each block behind and pulls `diff` — otherwise
  untouched by this sweep — into the blast radius of a security-sensitive
  (path-jail) refactor for a marginal net line change.
- **Symlink confinement of the `--force` destructive scans** — *deferred*
  (backlog anchor `force-cleanup-symlink-confinement`). `_scan_dist_tree_artifacts`
  uses `base.rglob("*")` and the cleanup uses `shutil.rmtree(subtree)` — neither
  uses the `os.walk(followlinks=False)` + per-entry symlink-skip convention the
  pack-content walks elsewhere follow. Pre-existing (not introduced by this
  sweep); listing the subtree root as the deletion unit (AC6) avoids *widening*
  the divergence, but adopting the no-follow convention is a separate hardening.

## Changelog

- `agentbundle uninstall` gains `--dry-run` / `--yes` + a confirmation.
- `agentbundle install --force` confirms (lists paths) before destructive
  cleanup; `install` gains `--yes` and offers to upgrade an already-installed
  pack.
- `agentbundle reconcile` / `list-targets` drop their dead `--scope` flag.
