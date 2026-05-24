# Plan: wire-session-start-hook

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is small. The Claude Code adapter already implements the
merge-json hook-wiring projection
(`packages/agentbundle/agentbundle/build/adapters/claude_code.py:84-109`)
and the adapter contract already declares the rule (`_data/adapter.toml:64-69`)
at contract v0.2 — which is what core declares today (`packs/core/pack.toml:13`).
So the work is **adding the missing wiring TOML to the core pack**, **two
prose reframes**, **one legacy-fixture rewrite**, and **one new
construction test** to pin AC1, plus a **smoke check** against real core
to pin AC10.

Three touch zones:

1. **Pack source.** New file `packs/core/.apm/hook-wiring/session-start.toml`;
   seed edits under `packs/core/seeds/docs/CONVENTIONS.md`.
2. **Documentation.** Reframe `tools/hooks/README.md § Wiring → Claude Code`.
3. **Fixtures + tests.** Rewrite three legacy `pre-commit.toml` fixtures to
   live shape with a static `"true"` stub command; new construction test
   under `packages/agentbundle/tests/integration/`; smoke check against
   real core.

Order of operations: write the construction test first (red), then add the
wiring TOML (green), then the prose reframes, then `make build-self`, then
the legacy-fixture rewrite with its targeted regression check, then the
full-suite gate.

The riskiest part is the legacy-fixture rewrite. Two real concerns:

- The catalogue_v2 fixture carries a load-bearing substring assertion at
  `test_upgrade_cmd.py:319` (`matcher = "Bash|Edit"`). The rewrite must
  preserve that substring verbatim.
- The rewrite will introduce a new projected `.claude/settings.local.json`
  row into `render_pack`'s output for each fixture (the legacy
  `[hook] name/trigger/matcher` shape has no `hooks` key, so the
  merge-json adapter at `claude_code.py:94-95` returns early and writes
  nothing; the rewritten shape produces an actual settings file). The
  byte-comparison tests in `test_upgrade_cmd.py` iterate over every
  `render_pack` key, so they'll encounter this new row. Both
  `render_pack` and `install` go through the same `_project_merge_json`
  code path, so expected and actual will match — but the regression
  check must actually run, not just be promised.

## Pre-flight

Before T1 lands, run `make build-self` on the post-rebase branch state
and commit any projection drift in a **separate** PR (or in the first
commit of this branch, distinct from the spec's commits). This
guarantees the spec's commit shows only the spec's changes, not
unrelated drift accumulated since the last `make build-self` run.

## Constraints

- **Adapter contract version.** `packs/core/pack.toml:13` declares
  `version = "0.2"`. Stays at v0.2; no bump. v0.2 supports the
  merge-json hook-wiring projection already.
- **No adapter, schema, or build-code changes.** This is consumption
  of existing capability.
- **Self-host projection discipline.** The repo self-hosts `packs/core/`,
  so `docs/CONVENTIONS.md`, `tools/hooks/session-start.py`, and any
  projected `.claude/*` artifacts are generated. Edit upstream, then
  `make build-self`. This is the spec's `Never do` boundary.
- **`.claude/settings.local.json` is excluded from `make build-self`.**
  `self_host.py:248` lists it in `EXCLUDED_PATTERNS`, and
  `.gitignore:18` excludes it too. The wiring TOML's effect is only
  visible through `agentbundle install`'s projection — which is what
  the spec actually cares about. No edits to `EXCLUDED_PATTERNS`.

## Construction tests

Per-task tests live under each Task below.

**Integration tests (cross-cutting):** none beyond per-task tests; T1's
construction test is the integration check for AC1/AC9, and T7's smoke
check is the integration check for AC10.

**Manual verification:**
- Run `make build-self` from the repo root. Confirm `git status` shows
  exactly the prose edit on `docs/CONVENTIONS.md` (T4 → T5 projection)
  and nothing else under projected paths (`tools/hooks/*`,
  `.claude/*`, etc.).
- Run the targeted tests (`test_upgrade_cmd.py`, `test_install_cmd.py`,
  `test_tier_invariants.py`) end-to-end after T6 to confirm the
  byte-comparison checks survive the rewrite.

## Tasks

### T1: Add the construction test (red)

**Depends on:** none

**Tests** (TDD — red before green):
- The test itself is the construction test for AC1 and AC9. It will
  fail red until T2 lands the wiring TOML.

**Approach:**
- New file: `packages/agentbundle/tests/integration/test_install_session_start_wiring.py`.
- Stage a synthetic minimal pack inside a tmp catalogue:
  - `pack.toml` declaring `name = "test-core"`, `version = "0.1.0"`,
    `[pack.adapter-contract] version = "0.2"`, `[pack.install]
    default-scope = "repo"`, `allowed-scopes = ["repo"]`.
  - `.apm/hooks/session-start.py` — empty stub file (projection is
    direct-file; content doesn't matter for the wiring assertion).
  - `.apm/hook-wiring/session-start.toml` — the live Claude-Code-nested
    shape (see T2 for the canonical form):
    ```toml
    [[hooks.SessionStart]]
    hooks = [
      { type = "command", command = "python tools/hooks/session-start.py" },
    ]
    ```
- Run `install.run(argparse.Namespace(...))` against the catalogue,
  redirecting stdout/stderr (mirror the `_install` helper in
  `packages/agentbundle/tests/integration/test_install_dual_scope.py`).
- Assert `target/.claude/settings.local.json` exists.
- Parse the JSON; assert `len(data["hooks"]["SessionStart"]) == 1`;
  assert `data["hooks"]["SessionStart"][0]["hooks"][0]["type"] == "command"`;
  assert `data["hooks"]["SessionStart"][0]["hooks"][0]["command"] ==
  "python tools/hooks/session-start.py"`; assert the outer entry has no
  `matcher` (or it equals `""`) — this pins the "fires on all session
  types: startup / resume / clear" semantic and guards against a
  future TOML edit accidentally narrowing scope by adding
  `matcher = "startup"` to the outer entry:
  ```python
  outer = data["hooks"]["SessionStart"][0]
  assert outer.get("matcher", "") == ""
  ```

**Done when:** `pytest packages/agentbundle/tests/integration/test_install_session_start_wiring.py -v`
runs and fails on the JSON assertion (red); the failure message
clearly shows the missing key, not a parse or IO error.

---

### T2: Add the wiring TOML to core (green)

**Depends on:** T1

**Tests** (TDD — green flip):
- T1's construction test passes.
- `python -c "import tomllib; tomllib.loads(open('packs/core/.apm/hook-wiring/session-start.toml').read())"`
  exits 0.

**Approach:**
- Create `packs/core/.apm/hook-wiring/session-start.toml`:
  ```toml
  # Wires the session-start.py hook body (projected to
  # tools/hooks/session-start.py) to Claude Code's SessionStart event.
  # Merged into .claude/settings.local.json under the `hooks` key by
  # the merge-json adapter rule
  # (packages/agentbundle/agentbundle/build/adapters/claude_code.py:84-109).
  #
  # Shape: Claude Code's documented nested SessionStart schema
  # (code.claude.com/docs/en/hooks). Outer entry has no `matcher`
  # (fires on all session types: startup / resume / clear); inner
  # `hooks` array carries `type = "command"` and the command string.
  #
  # No `id` field: repo-scope merge-json does not consume it (the
  # field is a user-scope concern in _merge_user_scope_hook_wiring).
  # No `attach-to-agent`: that's a Kiro-only field, and Kiro is out
  # of scope (see spec.md § Non-goals).
  [[hooks.SessionStart]]
  hooks = [
    { type = "command", command = "python tools/hooks/session-start.py" },
  ]
  ```

**Done when:** the file exists, parses, T1's test goes green.

---

### T3: Reframe `tools/hooks/README.md § Wiring → Claude Code`

**Depends on:** T2

**Tests** (goal-based):
- `rg "Add to your project-local .claude/settings.json" tools/hooks/README.md`
  returns 0 matches (the adopter-imperative phrasing for session-start
  is gone).
- `rg "pre-pr.py is most useful as a manual or git-hook command" tools/hooks/README.md`
  returns 1 match (the `pre-pr.py` paragraph is unchanged).

**Approach:**
- Replace the imperative intro at `tools/hooks/README.md:97` ("Add to
  your project-local `.claude/settings.json` (gitignored)") with text
  stating that `agentbundle install core` writes this binding
  automatically into `.claude/settings.local.json` (NOT
  `.claude/settings.json` — the current README path is a pre-existing
  bug; the actual target per `_data/adapter.toml:67` is the `.local`
  variant). The JSON snippet below is reproduced for audit /
  verification.
- Keep the JSON snippet body itself unchanged — it already shows the
  nested shape Claude Code requires.
- Update the paragraph that follows the snippet so it makes clear the
  auto-wiring applies only to session-start.py; `pre-pr.py` remains a
  manual / git-hook command for the documented reason (no Claude Code
  lifecycle event matches PR-prep semantics).

**Done when:** both grep checks pass; the path reads `.local.json`
not `.json`; visual diff confirms the section reads as "we wrote this
for you; here's what landed" rather than "paste this." `pre-pr.py`
paragraph unchanged.

---

### T4: Reframe `packs/core/seeds/docs/CONVENTIONS.md` paragraphs

**Depends on:** T2

**Tests** (goal-based):
- `rg "wiring is consumer-specific" packs/core/seeds/docs/CONVENTIONS.md`
  returns 0 matches.
- `rg "wired in the consumer's .claude/settings.json" packs/core/seeds/docs/CONVENTIONS.md`
  returns 0 matches.
- After T5, `grep -A2 "wiring is consumer-specific" docs/CONVENTIONS.md`
  returns 0 matches (the projected output mirrors the seed edit).

**Approach:**
- Edit two paragraphs in `packs/core/seeds/docs/CONVENTIONS.md`:
  - The enforcement-triplet follow-up paragraph: the sentence "The
    template ships the script; it does **not** ship a committed
    `.claude/settings.json` — wiring is consumer-specific." Reframe
    to: session-start now wires automatically via the adapter
    contract's `hook-wiring` primitive on `agentbundle install core`;
    `pre-pr.py` stays consumer-wired because no Claude Code
    lifecycle event matches "before PR opens."
  - The Profile-C paragraph: "the `session-start` hook is wired in
    the consumer's `.claude/settings.json` per [`tools/hooks/README.md`]…
    The template ships the script, not the wiring." Reframe: the
    session-start hook lands wired automatically by
    `agentbundle install core`; the template ships both the script
    and the wiring.
- Do **not** edit `docs/CONVENTIONS.md` directly.

**Done when:** seed grep checks pass; T5's projected-output grep
check passes after build-self.

---

### T5: Run `make build-self` and verify the projection

**Depends on:** T2, T4

**Tests** (goal-based):
- `make build-self` exits 0.
- `git diff docs/CONVENTIONS.md` is non-empty and contains the T4
  prose change.
- `git status` shows no unexpected changes under projected paths
  (`tools/hooks/*`, `.claude/*`, `docs/architecture/*`, etc.). The
  wiring TOML's effect on `.claude/settings.local.json` is **not**
  visible here — that file is in `self_host.py:248`'s
  `EXCLUDED_PATTERNS` and is gitignored.

**Approach:**
- From the repo root: `make build-self`.
- `git status` and `git diff` against pre-build state.
- Confirm the diff is exactly the prose change on
  `docs/CONVENTIONS.md` (mirrored from T4's seed edit) and no other
  projected file changed.

**Done when:** `make build-self` exits 0; `git diff docs/CONVENTIONS.md`
reflects only the T4 seed edit; no other projected path has drifted.

---

### T6: Legacy fixture rewrite

**Depends on:** T5 (the regression check at the end of T6 runs against
a workspace that is in the post-`make build-self` state from T5;
sequencing T6 before T5 risks the regression test seeing pre-build
drift)

**Tests** (goal-based, regression):
- `pytest packages/agentbundle/tests/integration/test_upgrade_cmd.py
  packages/agentbundle/tests/integration/test_install_cmd.py
  packages/agentbundle/tests/integration/test_tier_invariants.py -v`
  all pass.
- `test_upgrade_cmd.py:319`'s `assert 'matcher = "Bash|Edit"' in contents`
  still holds against the rewritten v2 fixture.
- `test_whole_pack_upgrade_updates_version_and_content` (which iterates
  over every key in `v2_projection`) passes — the new
  `.claude/settings.local.json` row that the rewrite introduces into
  `render_pack`'s output round-trips byte-for-byte with the install
  output (both go through `_project_merge_json`).

**Approach:**
- Verify the test-suite grep is comprehensive:
  `rg '\[hook\]\s*$' packages/agentbundle/tests/`,
  `rg 'trigger\s*=\s*"' packages/agentbundle/tests/`,
  `rg 'name\s*=\s*"pre-commit"' packages/agentbundle/tests/` —
  expect matches only inside the three fixture files and their
  consumers (no additional shape-asserting tests).
- For each of:
  - `packages/agentbundle/tests/fixtures/upgrade/catalogue_v1/packs/core/.apm/hook-wiring/pre-commit.toml`
  - `packages/agentbundle/tests/fixtures/upgrade/catalogue_v2/packs/core/.apm/hook-wiring/pre-commit.toml`
  - `packages/agentbundle/tests/fixtures/upgrade/catalogue_v3/packs/core/.apm/hook-wiring/pre-commit.toml`

  Replace the legacy:
  ```toml
  [hook]
  name = "pre-commit"
  trigger = "PreToolUse"
  matcher = "<v>"
  ```
  with Claude Code's nested shape and a static stub command:
  ```toml
  # Test fixture for SHA-tracking across upgrade versions.
  # `command = "true"` is a static stub — these fixtures do not
  # exercise live hook firing; live wiring at repo scope passes the
  # `command` string through verbatim (no $HOOK_BODY_PATH substitution
  # at repo scope), so the stub keeps the intent explicit.
  [[hooks.PreToolUse]]
  matcher = "<v>"
  hooks = [
    { type = "command", command = "true" },
  ]
  ```
  where `<v>` is verbatim per fixture: v1 → `"Bash"`,
  v2 → `"Bash|Edit"`, v3 → `"Bash"`. The substring `matcher = "Bash|Edit"`
  appears verbatim in v2 — the load-bearing assertion at
  `test_upgrade_cmd.py:319` survives.
- Note on per-primitive `--hook pre-commit` upgrade behavior: the new
  `.claude/settings.local.json` row that the rewrite introduces into
  `render_pack`'s output falls into `non_prim_paths` in
  `test_per_primitive_upgrade_moves_only_matching_files`, because the
  filter heuristic checks path segments for `/hooks/pre-commit.` or
  `/hook-wiring/pre-commit.` — and the merged JSON path matches
  neither. The per-primitive upgrade leaves the file untouched
  (v1 content survives), and the byte-comparison checks pass
  trivially because `non_prim_before == non_prim_after` for that
  path. Verify after the rewrite.
- Run the three named test files; verify regression-free.
- If any test fails due to the new `.claude/settings.local.json` row
  the rewrite introduces (e.g. a `non_prim_after` capture that didn't
  account for it), update the test **only** by adding the new
  projection row to the expected set. If any change beyond
  "expected set grew by one key" appears necessary — **stop and
  Surface to the user per work-loop discipline** before proceeding.
  Do **not** rewrite assertion logic or weaken existing checks under
  the banner of "handling the new shape." Do **not** revert the
  fixture rewrite.

**Done when:** all three named test files pass; no other test breaks;
the substring assertion at `test_upgrade_cmd.py:319` continues to
hold; the new `.claude/settings.local.json` row produced by the
rewrite round-trips through the byte-comparison tests.

---

### T7: Full-suite regression + AC10 smoke check + PR description

**Depends on:** T1-T6

**Tests** (goal-based):
- `tools/test-all.sh` exits 0.
- `python tools/hooks/pre-pr.py` exits 0.
- `pytest packages/agentbundle/tests/ -v` exits 0.
- **AC10 smoke check:** run `agentbundle install core` against a tmp
  install root (in a one-shot pytest or a shell-script invocation);
  parse `.claude/settings.local.json`; assert
  `data["hooks"]["SessionStart"][0]["hooks"][0]["command"]` equals
  `python tools/hooks/session-start.py`.

**Approach:**
- Run the full local gate set.
- AC10 smoke: a new pytest at
  `packages/agentbundle/tests/integration/test_install_core_smoke.py`
  (one test, ~20 lines). Stage a tmp catalogue that contains the
  real `packs/core/` directory (either symlink it in or copy it),
  call `install.run(...)` into `tmp_path`, parse the produced
  `.claude/settings.local.json`, assert
  `data["hooks"]["SessionStart"][0]["hooks"][0]["command"] ==
  "python tools/hooks/session-start.py"`. Single assertion is
  enough — the synthetic-pack test in T1 is the more granular
  check; this smoke test guards against the real-core wiring breaking
  by an unrelated change.
- Draft a PR description noting:
  - Behavior change: session-start wires automatically on install.
  - Adopter brownfield path (AC1a): if `.claude/settings.local.json`
    is adopter-edited, install writes
    `.claude/settings.local.json.upstream` per Tier-2; adopter
    reconciles. This is existing behavior — not new in this PR.
  - Pack↔pack `SessionStart` collision: if another pack wires
    `SessionStart` and is installed before core, the merge-json
    adapter at `claude_code.py:101-103` replaces the existing
    `SessionStart` array via `dict.update()` (key-level merge, not
    array-concat). Today no other pack wires `SessionStart`, so this
    is latent. Documented; revisit if a second pack needs it.
  - Repo-scope uninstall does **not** remove the merged
    `SessionStart` entry from `.claude/settings.local.json`.
    `install.py:566-602` only populates `hook_wiring_owned` state
    rows at user scope; at repo scope there's no per-entry uninstall
    record. This is a documented limitation (out of scope to fix
    here); revisit if it becomes adopter-visible.
  - Deferred follow-ups (not in this PR): Kiro support (separate
    spec; needs `steering` primitive design), `pre-pr.py` wiring
    (separate behavior decision), user-scope hook-wiring (RFC-0005
    T5/T7 not landed).

**Done when:** all gates green; AC10 smoke pytest passes; PR
description complete and lists the three latent limitations (R1, R4,
R5 below) and the deferred follow-ups.

## Rollout

Ships as-is. No flag, no migration. Existing installs without the
wiring TOML pick it up on the next `agentbundle upgrade core`. Fresh
installs get it immediately. Behavior change is opt-out (adopters
can manually edit `.claude/settings.local.json` to remove the entry
if they want, but the next upgrade reasserts it — the projection is
the source of truth at the managed key).

## Risks

- **R1: Adopter has a pre-existing edited `.claude/settings.local.json`.**
  The install pipeline's Tier-2 classification at
  `packages/agentbundle/agentbundle/commands/install.py:537-548`
  writes the projection to `.claude/settings.local.json.upstream`
  (a companion file) rather than overwriting the live file. The
  adopter must reconcile by hand. This is the documented
  `on-conflict = "merge-managed-key-only"` posture in
  `_data/adapter.toml:69`. **Mitigation:** AC1a pins the behavior;
  T7's PR description names it explicitly so a brownfield adopter
  knows where to look.

- **R2: Legacy fixture rewrite breaks a non-obvious test.** A grep
  for `\[hook\]\s*$`, `trigger\s*=`, and `name\s*=\s*"pre-commit"`
  across the test suite turned up only the three fixtures and the
  load-bearing substring at `test_upgrade_cmd.py:319` (which survives
  the rewrite). The rewrite also introduces a new
  `.claude/settings.local.json` row into `render_pack`'s output that
  did not exist before — the byte-comparison tests in
  `test_upgrade_cmd.py` will now iterate over it. **Mitigation:**
  T6's regression check explicitly runs the byte-comparison tests
  and the AC10 smoke; T6's `Done when` requires both grep
  comprehensiveness and the targeted-test gate.

- **R3: Pre-flight projection drift.** See the **Pre-flight** section
  above — risk and mitigation are co-located there to avoid
  duplication.

- **R4: Pack↔pack `SessionStart` collision.** The merge-json
  adapter's `merged_hooks.update(incoming)` at
  `claude_code.py:101-103` is a key-level merge — if a second pack
  wires `SessionStart`, the second install wipes the first's array.
  Today no other pack wires `SessionStart`, so this is latent.
  **Mitigation:** documented in T7's PR description; revisit if a
  second pack appears.

- **R5: Repo-scope uninstall does not remove the merged `SessionStart`
  entry.** `packages/agentbundle/agentbundle/commands/install.py:566-602`
  only populates `hook_wiring_owned` state rows at user scope; at
  repo scope there's no per-entry uninstall record, so `uninstall
  core` leaves the `.claude/settings.local.json` entry behind.
  **Mitigation:** documented in T7's PR description; out of scope to
  fix here. Cross-reference: RFC-0005 T8b's `hook_wiring_owned`
  design at user scope would generalise cleanly to repo scope when
  a future spec wants it.

- **R6: Spec drift if Kiro work lands in parallel.** The parallel
  Kiro spec may want to add fields to `packs/core/.apm/hook-wiring/`
  TOMLs or change the contract. **Mitigation:** the spec's
  `Never do` rails fence this PR from any Kiro-targeted field;
  coordination between the two specs lives in their respective
  status flips (this spec's Approved → Implementing → Shipped
  before the Kiro spec touches anything in `packs/core/.apm/`).

## Changelog

- 2026-05-24: initial plan after spec sign-off (post-rebase from
  origin/main; legacy-fixture rewrite added per user request; Kiro
  scope deferred after Kiro IDE/CLI research clarified that the
  current adapter codes CLI-only semantics and the right Kiro
  primitive is `steering`, not `hook-wiring`, and steering isn't
  modeled in the contract today).
- 2026-05-24: revised after spec-mode adversarial review (round 1).
  Major changes: brownfield AC1a added; AC8/T5 corrected (settings
  file is in `EXCLUDED_PATTERNS` — `make build-self` does not project
  it); legacy fixture command string switched from `$HOOK_BODY_PATH`
  to the static stub `"true"` (the resolver doesn't fire at repo
  scope, so the placeholder was misleading); pre-flight projection
  drift step added; AC10 + T7 smoke check against real core added;
  Never-do gained two structural rails (no v0.3 contract bump for
  core, no v0.3 forward-looking-table consumer); R1 corrected to
  cite Tier-2 companion path; R4 and R5 added for pack↔pack
  collision and repo-scope uninstall gap.
- 2026-05-24: revised after spec-mode adversarial review (round 3).
  Concern: AC1's "no matcher on outer entry" clause wasn't pinned by
  any test — added matcher-absence assertion to T1. Nit: per-primitive
  upgrade's interaction with the new merged-JSON row in `non_prim_paths`
  documented in T6's Approach.
- 2026-05-24: revised after spec-mode adversarial review (round 2).
  Blocker: TOML shape must produce Claude Code's nested SessionStart
  schema (verified at code.claude.com/docs/en/hooks). T1's assertion
  and T2's TOML rewritten to `[[hooks.SessionStart]] hooks = [{type
  = "command", command = "..."}]`; AC1 and AC9 reworded to specify
  the nested shape unambiguously; T6's legacy fixture rewrite also
  switched to nested shape for consistency. T3 also fixes a
  pre-existing bug in the README (`.claude/settings.json` →
  `.claude/settings.local.json`). T6 `Depends on` corrected to T5;
  T6 escape hatch capped with a Surface gate. R3 collapsed to
  reference Pre-flight. install.py citations fully qualified.
