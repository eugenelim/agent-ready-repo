# Plan: projection dry-run (`--dry-run` for `install` / `upgrade`)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Both commands already separate *computing what to write* from *writing it*:
`install` runs read-only Steps 1–8 (resolve → scope plan → render → path-jail
probe) and only writes in Step 9; `upgrade` renders then walks-and-writes.
`--dry-run` hooks the same seam in each: run the read-only work, classify every
file with the **existing** classifier (`_classify_for_install` / `safety.classify`),
print a per-file plan, and `return 0` *before* the first write — skipping, for
`install`, the marker / chained-adapt / `installed:` tail too.

The plan-line formatting (action + tier + target path, plus a summary) is shared
by both commands, so a single formatter lands in `commands/_common.py` and both
call it. This helper is justified up front because **two real callers exist
immediately** — it is not speculative reuse.

Order: `upgrade` first (smaller, single write loop — establishes the formatter +
test patterns), then `install` (more pre-flight to short-circuit cleanly), then
docs once the real output text is settled.

### The trio

- **Files touched:** `packages/agentbundle/agentbundle/cli.py` (add `--dry-run`
  to both subparsers); `commands/_common.py` (shared plan formatter);
  `commands/upgrade.py` + `commands/install.py` (dry-run branch before writes);
  `tests/integration/test_upgrade_cmd.py` + a new/existing install test module;
  `docs/guides/_shared/how-to/preview-install-or-upgrade.md` (new) +
  `docs/guides/_shared/reference/agentbundle.md` (flag listing); `docs/product/changelog.md`.
- **Tests that show "done":** integration tests asserting (a) target tree +
  state file + marker are byte-identical before/after a dry-run, (b) the stdout
  plan names action/tier/path including a Tier-2 companion line, (c) a pre-flight
  failure still exits non-zero with nothing written.
- **Not changing:** the tier-classification logic (reused verbatim); any
  non-dry-run behavior of install/upgrade; no `--json`, no interactive confirm,
  no other write verbs. No new top-level dir or dependency.

### Declined patterns

- Tempted to add a `--json` output mode now — **declining**; deferred to a second
  caller (spec Boundaries → Ask first).
- Tempted to fork a "dry-run classifier" so the preview can be richer than the
  real run — **declining**; one classifier, one source of truth (spec Never-do).
- Tempted to extend dry-run to `scaffold`/`adapt`/`init-state`/`uninstall` in the
  same PR — **declining**; out of v1 scope.
- Tempted to make `--dry-run` print to stderr (like the companion notice) —
  **declining**; the plan *is* the command's output here, so stdout (pipeable);
  stderr stays for diagnostics.

## Constraints

- Additive, read-only CLI flag; spec-level per CONVENTIONS §3 (no RFC).
- Must not regress the Tier-2 file-safety contract or `test_tier_invariants.py`.
- Reuse `_classify_for_install` / `safety.classify` — do not reimplement tiers.

## Construction tests

**Integration tests:** see per-task `Tests:`.
**Manual verification:** none (no TTY-only path; output is deterministic).

## Tasks

### T1: `agentbundle upgrade --dry-run` + shared plan formatter

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/cli.py, packages/agentbundle/agentbundle/commands/_common.py, packages/agentbundle/agentbundle/commands/upgrade.py, packages/agentbundle/tests/integration/test_upgrade_cmd.py

**Tests:** (TDD, write first)
- Dry-run upgrade over a Tier-2 collision (edit a projected file post-install):
  assert stdout plan contains the file with a `companion` action + Tier-2 label +
  `-> <path>.upstream.<ext>`, exit 0, and **no** companion / state change on disk
  (snapshot tree + `.agentbundle-state.toml` byte-identical before/after). [AC1, AC4, AC6]
- Dry-run upgrade with no edits: plan lists the projected files with `overwrite`/
  Tier-1 labels and target paths; exit 0; nothing written. [AC1, AC3]
- Per-primitive dry-run (`--dry-run --skill work-loop`): plan lists only that
  skill's files; nothing written; a `--dry-run --skill bogus` still exits non-zero
  (primitive-not-found passes through). [AC1]
- Formatter unit: `_common.format_plan_line(...)` renders the documented
  action/tier/path shape (and the `-> companion` suffix for Tier-2). [AC3]

**Approach:**
- Add `--dry-run` (store_true) to the `upgrade` subparser in `cli.py`.
- Add `format_plan_line` (+ a `summarize_plan` count helper) to `commands/_common.py`.
- In `upgrade.run`, after the projection is rendered and `work_projection` is
  built, if `args.dry_run`: for each `(relpath, content)` compute
  `safety.classify(...)` (same call the write loop uses), print a plan line, and
  `return 0` before the write loop — no state write, no hook-wiring reconciliation,
  no `upgraded:` recap.

**Done when:** the T1 tests pass; `agentbundle upgrade --dry-run …` prints the
plan and leaves the tree + state byte-identical.

### T2: `agentbundle install --dry-run`

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/cli.py, packages/agentbundle/agentbundle/commands/install.py, packages/agentbundle/tests/integration/test_install_cmd.py

**Tests:** (TDD)
- Dry-run fresh install: plan lists every projected file with `create`/Tier-1 +
  target path; exit 0; tree empty of projected files afterward, **no**
  `.agentbundle-state.toml`, **no** install marker written. [AC2, AC6]
- Dry-run re-install over an adopter-edited file: plan shows the `companion`/
  Tier-2 line; exit 0; no companion written. [AC2, AC4]
- **`--dry-run --force` is refused:** non-zero exit + stderr message; and over a
  pre-RFC-0012 dist-tree / seeded-orphan fixture (the case where Step 3c *would*
  `rmtree`/`unlink`/rewrite-state under `--force`), assert the subtree, orphan
  file, and state row are **all still present** afterward. This is the test that
  actually exercises the no-write invariant under stress. [AC8, AC6]
- **Step 3c refusal passthrough (no `--force`):** `--dry-run` over a
  pre-RFC-0012/orphan fixture exits non-zero with the same refusal the real run
  gives, writing nothing. [AC5]
- Pre-flight failure under dry-run (adapter-resolution refusal / path-jail-violating
  fixture): non-zero exit + stderr reason; nothing written. [AC5]

**Approach:**
- Add `--dry-run` to the `install` subparser in `cli.py`.
- **Refuse `--dry-run --force` early** (right after arg parsing in `install.run`,
  before Step 3c) with a non-zero exit and the message from the spec. This is what
  makes Step 3c read-only under `--dry-run`.
- In `install.run`, at the top of Step 9 (after Step 8's path-jail probe), if
  `args.dry_run`: walk each plan's projection, classify via `_classify_for_install`,
  print plan lines (per scope/adapter, showing the resolved target path), then
  `return 0` — skipping Steps 9–13 (writes, marker, chained adapt, `installed:`).
  Because `--force` is refused, Step 3c's read-only refusals (`return 1`) and
  Steps 1–8's other pre-flight refusals already short-circuit before Step 9,
  satisfying AC5 with no extra code.

**Done when:** the T2 tests pass — including the `--dry-run --force` refusal and
the Step-3c no-write stress test; `agentbundle install --dry-run …` previews the
plan and leaves tree + state + marker byte-identical.

### T3: Document the dry-run preview (how-to + reference)

**Depends on:** T1, T2

**Touches:** docs/guides/_shared/how-to/preview-install-or-upgrade.md, docs/guides/_shared/reference/agentbundle.md, docs/guides/_shared/how-to/README.md, docs/product/changelog.md

**Tests:** goal-based — one-liner checks (file exists, `grep` the flag name), not
a pytest module:
- `docs/guides/_shared/how-to/preview-install-or-upgrade.md` exists, is listed in
  `how-to/README.md`, and covers: when to use `--dry-run`, a real
  `agentbundle upgrade --dry-run …` invocation with paste-of-actual-output, how to
  read the action/tier/path lines, and the no-write guarantee. [AC7]
- `docs/guides/_shared/reference/agentbundle.md` lists `--dry-run` under both `install`
  and `upgrade`. [AC7]
- `docs/product/changelog.md` carries an Unreleased entry for the new flag.

**Approach:**
- Capture real `--dry-run` output (run the command) and paste the actual bytes
  into the how-to — do not reconstruct it.
- Cross-link the how-to to `upgrade-packs.md` and the file-safety explanation;
  don't restate the Tier model (link it).

**Done when:** the how-to and reference name the flag and the no-write guarantee;
the changelog entry is present.

## Risks

- `install.run` is large with several early-return pre-flight branches; the
  dry-run branch must sit *after* Step 8 so AC5's failure-passthrough is free, but
  *before* any Step 9 write. Mitigation: place the branch at the documented Step 9
  boundary and assert the no-write invariant in tests.

## Changelog

- 2026-06-11: initial plan.
