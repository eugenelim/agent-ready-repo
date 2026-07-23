# Spec: projection-dry-run-governance-seeds

- **Status:** Shipped
- **Owner:** eugenelim
- **Constrained by:** [`projection-dry-run`](../projection-dry-run/spec.md) — Never-do: "Fork, reimplement, or special-case the tier-classification logic."

Mode: full (structural — extracts pure classify function; extends dry-run output)

## Objective

`agentbundle install --dry-run --scope repo` previews the rendered adapter
projection but silently omits the governance seeds (AGENTS.md, docs/CHARTER.md,
docs/CONVENTIONS.md, and the other files under `packs/<pack>/seeds/`) that a real
repo-scope install delivers via `deliver_seeds`. An adopter reading the preview
plan cannot tell which governance documents would be created or whose edits would
be preserved as companions.

The fix has two parts: (1) extract `deliver_seeds`' classification logic into a
pure function `_classify_seeds(seeds_dir, root)` that returns what a real delivery
would do without performing any write; and (2) call `_classify_seeds` from the
`--dry-run` branch in `install.run` so the plan output includes seed entries in
the same `<action> <tier> <path>` format as the projection entries.

The predecessor spec (`projection-dry-run`) forbids forking the classifier. This
spec satisfies that constraint: `deliver_seeds` is refactored to call
`_classify_seeds` internally, so one piece of classification code serves both the
real delivery path and the dry-run preview path.

## Acceptance Criteria

- [x] AC1: A pure function `_classify_seeds(seeds_dir: Path, root: Path) -> list[SeedDelivery]`
  exists in `packages/agentbundle/agentbundle/commands/_common.py`. It performs
  no writes. It walks `seeds_dir` with the same symlink-skip and
  composition-fragment logic as the current `deliver_seeds`, reads each seed's
  bytes (composing `AGENTS.md` from body+footer when the footer fragment is
  present), and returns `SeedDelivery` records with `action` set to `"wrote"`
  (absent on disk), `"skipped"` (byte-identical), or `"companion"` (differs — Tier-2).
- [x] AC2: `deliver_seeds` calls `_classify_seeds` internally and drives writes
  from its result. The real install and scaffold delivery paths produce byte-for-byte
  identical outcomes — no behaviour change.
- [x] AC3: `install --dry-run --scope repo` includes seed files in the plan output.
  Each seed is printed on a separate line using the existing `format_plan_line`
  formatter: `create` + `tier-1` for an absent seed; `companion` + `tier-2` +
  `<path> -> <companion>` for a user-edited seed. Byte-identical seeds (`"skipped"`)
  produce no plan line.
- [x] AC4: The `summarize_plan` count at the end of the dry-run output includes
  seed files. The count matches `create` + `companion` seed entries added to the
  existing projection entries.
- [x] AC5: Running `install --dry-run --scope repo` writes nothing — no seed file,
  no `.upstream.<ext>` companion, no `.agentbundle-state.toml`, no install marker.
  The no-write invariant from `projection-dry-run` AC6 extends to seeds.
- [x] AC6: All existing dry-run integration tests in
  `tests/integration/test_install_cmd.py`, `tests/integration/test_install_seed_delivery.py`,
  and `tests/unit/test_scaffold_cmd.py` pass unchanged. (`test_scaffold_cmd.py` exercises the
  symlink-skip security invariant that `_classify_seeds` must preserve.)
- [x] AC7: A unit test for `_classify_seeds` covers:
  (a) seed absent on disk → `action == "wrote"`;
  (b) seed byte-identical on disk → `action == "skipped"`;
  (c) seed differs on disk → `action == "companion"` with the correct `companion_relpath`;
  (d) `AGENTS.md` classified against composed bytes (body+footer), not raw seed bytes;
  (e) `_agents-footer.md` excluded from the returned list;
  (f) a symlinked seed file inside `seeds_dir` is not returned (symlink-skip invariant);
  (g) a symlinked subdirectory inside `seeds_dir` is not descended into (symlink-skip invariant);
  (h) calling `_classify_seeds(seeds_dir, root)` against a real `seeds_dir` and an empty `root`
  writes nothing under `root` — the no-write invariant is verified by asserting `root` directory
  is unchanged after the call.
- [x] AC8: A new integration test asserts that the stdout plan for a fresh
  `install --dry-run --scope repo` includes at least `AGENTS.md`, `docs/CHARTER.md`,
  and `docs/CONVENTIONS.md` as `create tier-1` lines, and that the tree is
  byte-identical before and after (AC5 regression guard specific to seeds).
- [x] AC9: `deliver_seeds` returns the full `list[SeedDelivery]` from `_classify_seeds`
  unchanged — including `"skipped"` records. An existing state-recording test (or a new
  test added alongside AC7) asserts that a byte-identical seed (`action == "skipped"`)
  is still recorded in the install state `files` map after `deliver_seeds` completes. This
  ensures the Tier-2 companion safety is not silently dropped for seeds that were
  already present byte-identically.

## Boundaries

### Always do

- Keep `_classify_seeds` strictly read-only: read `seeds_dir` and `root`, return
  `SeedDelivery` records, never touch the filesystem under `root`.
- Call `_classify_seeds` from both `deliver_seeds` (real path) and the `--dry-run`
  branch in `install.run` (preview path) — one classifier, two callers.
- Reuse the existing `format_plan_line` and `summarize_plan` formatters for seed
  plan lines. Verb mapping: `"wrote"` → `"create"` + `"tier-1"`;
  `"companion"` → `"companion"` + `"tier-2"`; `"skipped"` → no line.
- Guard the dry-run seed preview on `plan.scope == "repo"` and `seeds_dir.is_dir()`,
  mirroring the real delivery guard at `install.py:1118`.

### Never do

- Write anything under `--dry-run`: no seed file, no `.upstream.<ext>` companion,
  no state entry, no install marker.
- Add a separate or parallel classification logic for seeds under `--dry-run`.
  That would be the "forking" the predecessor spec forbids. `_classify_seeds`
  must be the one source of truth for how seeds are classified, used identically
  by both paths.
- Change the observable behaviour of a non-`--dry-run` install, scaffold, or any
  other write-path command.
- Extend `--dry-run` to `scaffold` in this spec — out of scope.
- Add `deliver_seeds` calls to `upgrade --dry-run` — seeds are a first-install-only
  concern; `upgrade` never calls `deliver_seeds` today and must not start.
- Add a new top-level directory or a new runtime dependency.

### Ask first

- Adding `--dry-run` to `scaffold` (a future follow-on; separate spec).
- Changing the `SeedDelivery` action vocabulary (`"wrote"` / `"skipped"` /
  `"companion"`) — any rename would break both paths that consume it.

## Testing Strategy

- **`_classify_seeds` unit test (AC7): TDD.** Write
  `tests/unit/test_common_classify_seeds.py` before implementing the function.
  Stub a temporary `seeds_dir` with: one seed absent from `root` (expects `"wrote"`),
  one seed byte-identical on disk (expects `"skipped"`), one seed differing on disk
  (expects `"companion"` with correct companion path). A case exercises AGENTS.md
  composition (footer fragment present → composed bytes used for comparison).
  A case confirms `_agents-footer.md` is excluded from the returned list.
- **`deliver_seeds` regression (AC2, AC6): goal-based.** The existing
  `tests/integration/test_install_seed_delivery.py` tests must pass without
  modification after the refactor. Passing the existing suite is the bar.
- **Dry-run seed preview integration (AC3, AC4, AC5, AC8): TDD.** Extend
  `tests/integration/test_install_cmd.py`. Three cases: fresh-install preview shows
  seeds as `create tier-1`; user-edited seed shows `companion tier-2` with no
  companion written; byte-identical seed produces no plan line.

## Assumptions

- Technical: Seed relpaths (files under `seeds/` in a pack, delivered to repo root or
  `docs/`) are disjoint from adapter-projection relpaths (files under `packs/<pack>/`
  projected to `.claude/`, `tools/`, etc.). The two file sets do not overlap, so a seed
  path never duplicates a projection path in the dry-run plan, and `summarize_plan` counts
  them without double-counting. (Verified: grep of seed relpaths (`AGENTS.md`,
  `docs/CHARTER.md`, `docs/CONVENTIONS.md`) against projection target paths confirms no
  intersection in the current pack set.)
- Technical: `deliver_seeds` in `_common.py` (lines 80–146) is a combined
  classify+write function; no `_classify_seeds` exists today (read 2026-07-23).
- Technical: the dry-run branch in `install.py` (lines 929–950) returns before
  Step 9, so seeds are never previewed today (read 2026-07-23).
- Technical: seeds are only delivered at repo scope, guarded by
  `plan.scope == "repo"` at `install.py:1118` (read 2026-07-23).
- Technical: `upgrade.py` never calls `deliver_seeds` — seeds are install-only
  (grep confirmed 2026-07-23).
- Technical: `scaffold.py` calls `deliver_seeds` directly; refactoring its
  internals leaves scaffold's behaviour unchanged (`scaffold.py:56`, read 2026-07-23).
- Technical: `safety.companion_path` is a pure path computation — no writes
  (`safety.py:127`, read 2026-07-23).
- Technical: `SeedDelivery.action` values (`"wrote"`, `"skipped"`, `"companion"`)
  map cleanly to the plan verb set; `"overwrite"` does not exist in the seeds model
  (source: `_common.py:80–146`, read 2026-07-23).

## Tasks

### T1 — Extract `_classify_seeds` and refactor `deliver_seeds`

**Depends on:** none

Write unit tests for `_classify_seeds` first (TDD, AC7). Then:

- Add `_classify_seeds(seeds_dir: Path, root: Path) -> list[SeedDelivery]` above
  `deliver_seeds` in `_common.py`. Copy the walk loop, symlink skip, fragment
  exclusion, composition, and three-way comparison — but omit all write calls.
  For the `"companion"` case, compute `companion_relpath` via
  `safety.companion_path(Path(relpath)).as_posix()`.
- Refactor `deliver_seeds` to call `_classify_seeds(seeds_dir, root)` and
  drive writes from the returned list: `"wrote"` → `write_jailed`; `"companion"` →
  `write_companion`; `"skipped"` → no-op. Return the full list (including `"skipped"` records) to the caller.

**Done when:** unit tests pass; `test_install_seed_delivery.py` and
`test_scaffold_cmd.py` pass unchanged.

### T2 — Extend `install --dry-run` to preview seeds

**Depends on:** T1

Write integration tests first (TDD, AC3/AC5/AC8). Then add seed preview to
`install.run`'s dry-run branch (around line 929), guarded by
`plan.scope == "repo"` and `seeds_dir.is_dir()`. For each record from
`_classify_seeds`, skip `"skipped"`, emit `format_plan_line` for `"wrote"` and
`"companion"`, append the verb to `actions`.

**Done when:** new integration tests pass; existing dry-run tests pass unchanged.

## Changelog

- 2026-07-23: Implemented and shipped — `_classify_seeds` extracted from `deliver_seeds`; `deliver_seeds` refactored to call it; seed preview added to `install --dry-run`. All ACs pass.

## Declined

- Seed preview for `scaffold --dry-run` — `scaffold` currently has no `--dry-run`
  flag; separate feature, separate spec.
- `"skipped"` plan lines for seeds — projection dry-run already omits no-op
  files; consistent silence is cleaner.
- Seed preview in `upgrade --dry-run` — seeds are not re-delivered at upgrade
  time; if upgrade ever gains seed delivery, that spec should add the preview.
