# Spec: projection dry-run (`--dry-run` for `install` / `upgrade`)

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none <!-- additive, read-only CLI flag; spec-level per CONVENTIONS §3 -->
- **Contract:** none <!-- the CLI surface is not tracked under contracts/<type>/; no REST/event/RPC interface -->
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Mode: full** — risk trigger: *public-interface change* (a new `--dry-run`
> flag adopters see on two CLI commands).

## Objective

An adopter about to run `agentbundle install` or `agentbundle upgrade` often
can't tell, in advance, what the command will do to their working tree — which
files it creates, which it overwrites, and which of their edits it preserves as
`.upstream.<ext>` companions. Today the only way to find out is to run it. This
feature adds a read-only `--dry-run` flag to both commands: it does everything a
real run does up to the moment of writing — resolves the catalogue, builds the
scope plan, renders the projection, and runs the path-jail pre-flight — then
prints a per-file plan (action + tier + target path) to stdout and stops,
touching nothing. Success: an adopter can preview exactly what *would* change and
where, trust that the preview wrote nothing, and then decide whether to run it
for real. Homebrew 6.0's "ask mode" is the external analog; this is the
read-only half of it (no in-CLI confirm-to-proceed — that stays out of scope).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep `--dry-run` strictly read-only: run the existing read-only pre-flight
  (resolve → build scope plan → render projection → path-jail probe), classify
  each file, report, and return — before any write site.
- Reuse the existing tier-classification functions verbatim — `_classify_for_install`
  for `install`, `safety.classify` for `upgrade` — so the preview's tiers cannot
  drift from what a real run would do.
- Print the plan to **stdout** (one line per file: action + tier + target path;
  Tier-2 lines also name the `.upstream.<ext>` companion path), followed by a
  summary count. Diagnostics and pre-flight failures go to **stderr**.
- Report a pre-flight failure honestly: if resolve / version-gate / adapter
  resolution / path-jail / pack-not-installed / pre-RFC-0012-or-orphan refusal
  would fail the read-only pre-flight, `--dry-run` surfaces it on stderr and exits
  non-zero, exactly as the real run would at that stage.
- Refuse `--dry-run --force` (install) up front with a clear non-zero message:
  `--force` performs destructive cleanup (install Step 3c's `rmtree` / orphan
  `unlink` / state rewrite) that a read-only preview must not do, so the
  combination is contradictory. A preview of *what `--force` would clean* is a
  separate future feature.

### Ask first

- Extending `--dry-run` to other write-capable verbs (`scaffold`, `adapt`,
  `init-state`, `uninstall`).
- Adding a machine-readable `--json` output mode.
- Turning the preview into an interactive "ask mode" that prompts to proceed,
  or making `--dry-run`-then-confirm the default.

### Never do

- Write **anything** under `--dry-run`: no projected file, no `.upstream.<ext>`
  companion, no `.agentbundle-state.toml`, no install marker; run no chained
  `adapt`; emit no `installed:` / `upgraded:` recap. This no-write invariant is
  the defining property of the feature.
- Fork, reimplement, or special-case the tier-classification logic — one source
  of truth, consumed by both the real and dry-run paths.
- Perform `--force`'s destructive cleanup (install Step 3c) under `--dry-run` —
  refuse the combination instead (see *Always do*), never silently skip *or*
  silently execute it.
- Change the behavior of a non-`--dry-run` `install` / `upgrade` in any way.
- Add a new top-level directory or a new runtime dependency.

## Testing Strategy

- **No-write invariant (AC1, AC2, AC6): TDD**, via **integration** tests against
  the upgrade/install fixtures — snapshot the target tree + `.agentbundle-state.toml`
  (+ install marker) before and after a `--dry-run`, assert byte-identical, and
  assert the absence of any `.upstream.<ext>` companion. The invariant only proves
  out across the full command, so it lives at the integration surface.
- **Plan content (AC3, AC4): TDD / integration** — assert the stdout plan names
  each file's action, tier, and target path; on a forced Tier-2 collision, assert
  the companion line appears and the exit code is 0.
- **Pre-flight-failure passthrough (AC5): goal-based**, exercised by an
  integration case (e.g. an unresolvable adapter or a path-jail-violating
  projection) — assert non-zero exit + stderr reason, still no writes.
- **Docs (AC7): goal-based** — the how-to exists at the right Diátaxis path,
  names the flag and the no-write guarantee; the CLI reference lists `--dry-run`.

## Acceptance Criteria

- [ ] `agentbundle upgrade --dry-run <pack> --to <v> <catalogue>` prints a
  per-file plan to stdout — each line naming an action (`create` / `overwrite` /
  `companion`), the tier, and the target relpath; Tier-2 lines also show
  `<path> -> <path>.upstream.<ext>` — and exits 0. **Nothing is written:** no
  projected file, no companion, no state, no hook-wiring change. A per-primitive
  preview (`--dry-run --skill <name>`, etc.) previews only that primitive's files;
  a primitive-not-found still exits non-zero (the pre-render refusal passes through).
- [ ] `agentbundle install --dry-run <pack> <catalogue>` prints the same shape of
  per-file plan to stdout and exits 0, **writing nothing** — no projected file,
  no companion, no `.agentbundle-state.toml`, no install marker — and running no
  chained `adapt` and emitting no `installed:` recap.
- [ ] The per-file plan uses stable, greppable tier labels and shows the resolved
  target path (the "where") for each file, for the scope/adapter the real run
  would target. (Dual-scope writes arise only under `--force`, which `--dry-run`
  refuses — see the `--dry-run --force` criterion below — so a preview targets a
  single scope.)
- [ ] A present Tier-2 collision does **not** change the exit code (still 0); the
  preview is informational. (`diff` remains the drift-gating verb.)
- [ ] When the read-only pre-flight itself would fail — catalogue resolve,
  spec-version gate, adapter-resolution refusal, path-jail violation, pack not
  installed (`upgrade`), or the pre-RFC-0012 / orphan refusal that install's
  Step 3c raises *without* `--force` — `--dry-run` reports it on stderr and exits
  non-zero, matching the real run at that stage, and still writes nothing.
- [ ] `agentbundle install --dry-run --force …` is refused up front with a
  non-zero exit and a stderr message explaining that `--force`'s destructive
  cleanup is incompatible with a read-only preview; **nothing is written** (no
  `rmtree`, no orphan `unlink`, no state rewrite). Previewing *what `--force`
  would clean* is explicitly deferred to a future feature.
- [ ] The no-write invariant is regression-guarded: an integration test asserts
  the target tree, state file, and install marker are byte-identical before and
  after a `--dry-run` of both `install` and `upgrade`.
- [ ] A Diátaxis **how-to** under `docs/guides/how-to/` documents previewing an
  install/upgrade with `--dry-run` (when to reach for it, how to read the plan
  output, the no-write guarantee), and the CLI **reference** page lists the
  `--dry-run` flag for both commands.

## Assumptions

- Technical: `install`'s main write chokepoint is Step 9 (`_classify_for_install`
  → `write_companion`/`write_jailed`); Steps 4–8 are read-only and include a
  path-jail probe of every projected file. **Caveat (found in spec review):**
  Step 3c (`_classify_pre_rfc0012_state`, `install.py:380, 1586–1785`) writes
  *only under `--force`* (`rmtree` / orphan `unlink` / state rewrite); *without*
  `--force` it is read-only (detects and refuses). Resolution: `--dry-run` refuses
  `--force`, so under `--dry-run` Step 3c is read-only and the dry-run return at
  the top of Step 9 writes nothing (source: `install.py:380, 781, 806–844,
  1586–1785`, read 2026-06-11).
- Technical: under `--emit-install-routes`, install renders the dist-tree shape
  (`render_pack`, `install.py:670`) and the Step 3c in-band detection
  short-circuits (documented at `install.py:~1620`: "the code path producing
  those files is `--emit-install-routes`, which short-circuits before this
  detection runs"); a `--dry-run` runs the same render, previewing the dist-tree
  projection the real run would emit, with no `--force` write concern on that path
  (source: `install.py:670, ~1620`, read 2026-06-11).
- Technical: `upgrade` renders the projection (read-only) then walks it applying
  `safety.classify` before writing — same dry-run insertion point; the
  per-primitive `work_projection` is built (and primitive-not-found refused) at
  `upgrade.py:345–353` before the walk at `upgrade.py:363` (`safety.classify` at
  364, `write_companion`/`write_jailed` at 374+), so a dry-run return after
  `work_projection` covers whole-pack and per-primitive alike (source:
  `upgrade.py:345–396`, read 2026-06-11).
- Technical: tier vocabulary is Tier-1 (create/overwrite) / Tier-2
  (companion-drop) / Tier-3 (untouched), returned by the existing classify
  functions (source: `safety.classify`, `_classify_for_install`, read 2026-06-11).
- Technical: `--dry-run` is the repo's established flag name (source:
  self-host build, `agentbundle/build/__init__.py:120`).
- Technical: `diff` is a post-hoc render-vs-disk drift check that exits 1 on
  drift — adjacent but not a pre-write plan (source: `commands/diff.py`).
- Technical: runtime is stdlib Python ≥3.11 (source: `packages/agentbundle/pyproject.toml`).
- Product: v1 covers `install` and `upgrade`; other write verbs (`scaffold`,
  `adapt`, `init-state`, `uninstall`) are out of scope (source: user confirmation 2026-06-11).
- Product: a successful preview exits 0 even with Tier-2 collisions present;
  non-zero only when the pre-flight itself would fail (source: user confirmation 2026-06-11).
- Product: human-readable plan to stdout in v1; `--json` deferred until a second
  caller needs it (source: user confirmation 2026-06-11).
- Process: an additive, read-only CLI flag inside the agentbundle package that
  changes no contract is spec-level, not RFC-level (source: `docs/CONVENTIONS.md`
  §3 "a new feature that fits cleanly within an existing package and doesn't
  change any interface — write a spec, not an RFC"; user confirmation 2026-06-11).
