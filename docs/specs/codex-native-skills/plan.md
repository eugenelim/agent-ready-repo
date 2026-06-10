# Plan: codex-native-skills

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Nine tasks across four surfaces:

- **Contract + seed** (T1): flip the two contract files and edit the
  seed `AGENTS.md` together. These three artifacts encode the legacy
  delimiter pair; `make build-check` is the drift gate that keeps
  them in sync.
- **Codex adapter** (T2, T3, T4): T2 lands the migration-strip
  step as a pure-function unit (repurposing `_splice_managed_block`
  to empty the legacy region and then delete the empty delimiter
  pair) with no integration wiring. T3 lands the new
  `direct-directory` branch in `codex.py` **additively** — adding
  the new mode dispatch and tests while keeping the
  managed-block path intact, so the green-bar is reachable
  incrementally. T4 then removes the managed-block path,
  integrates T2's strip into the install flow, removes the five
  obsolete tests, and flips the stale `assertIn` in
  `test_self_host_check.py`. The T3/T4 split keeps each task to a
  reviewable PR size and isolates the breaking change to T4.
- **Multi-pack uniform entry point + shared cleanup** (T5, T6, T7):
  T5 introduces `project_packs(pack_paths, ...)` shims on
  `claude_code.py` and `kiro.py` and routes `self_host.py` through
  them. T6 introduces the shared `sweep_orphans` helper as a
  TDD-driven new module. T7 wires the helper into all three
  adapters' `project_packs` so the orphan sweep fires after every
  multi-pack call.
- **Spec amendment + self-host + linter** (T8, T9): T8 amends
  `distribution-adapters/spec.md` per RFC-0009 § Adapter contract
  change. T9 regenerates `dist/`, lands the changelog entry, and
  extends `tools/lint-agents-md.py` with the legacy-delimiter
  warning.

The T2 → T3 → T4 ordering matters: T2's strip mechanism is tested
standalone (text-only fixtures, no filesystem) before T3 wires the
new direct-directory branch into `codex.py`. T4 is then the
breaking change — managed-block path goes away, strip integrates
into the install path, obsolete tests removed.

T5 and T6 are independent of T1-T4 and of each other (both declare
`Depends on: none`). The work-loop's supervisor mode can fan them
out in parallel if the executor wants.

Riskiest part is T7 — wiring the orphan sweep into three adapters
without breaking any existing test. The sweep must observe the
**union of source skill names across all packs in the current
`project_packs` call** (not per-pack, or a pack shipping a subset
would orphan-clean the others). T7's tests pin this with a
two-pack fixture (AC20).

The Codex-only flip is feature-complete after T4 lands; the
cross-cutting cleanup (T5-T7) is the RFC-0009 § Failure modes
commitment.

## Constraints

- [RFC-0009](../../rfc/0009-codex-native-skills.md) — drives
  every decision; specific sections cited inline.
- [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  — adapter contract structure; the `mode` enum
  (`direct-directory`, `direct-file`, `managed-block-inline`,
  `merge-json`, `dropped`) is extensible by design.
- [RFC-0005](../../rfc/0005-user-scope-hook-support.md) — precedent
  for the same change shape: flip an
  `[[adapter.<name>.projection]]` entry, shrink the adapter,
  update touching tests, regenerate `dist/`.
- [`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md)
  — stdlib-only commitment; the orphan-sweep helper uses `shutil`
  + `pathlib` + `set`.
- [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  — projection-table source-of-truth for the four reference
  adapters; T8 amends.
- [`docs/specs/self-hosting/spec.md`](../self-hosting/spec.md)
  — `make build-check` is the drift gate this spec relies on
  for AC2, AC15, AC28.

## Construction tests

Most construction tests live under **Tasks** below (per-task
`Tests:` subsections). This section covers cross-cutting tests
only.

**Integration tests:**

- **Self-host build smoke** (touches T1, T3, T4, T7, T9):
  `make build-check` runs the self-host projection against the
  full core pack and exits clean. Every
  `dist/codex/.agents/skills/<name>/SKILL.md` is present (AC29
  spot-check via `packs/core/.apm/skills/*/` enumeration). The
  cross-cutting gate catches drift between contract files, seed
  AGENTS.md, adapter code, and projection output.
- **Two-pack orphan sweep across all three adapters** (touches T5,
  T6, T7): the AC20 regression guard. Single
  `project_packs([pack_a, pack_b], ...)` against each adapter
  with `pack_a.skills = {a, b}` and `pack_b.skills = {b, c}`
  projects `{a, b, c}`; then `project_packs([pack_a], ...)` alone
  against the same `output_root` keeps `{a, b}` and removes `c`.
  This is the load-bearing regression test for the
  per-pack-vs-union concern named in the Approach.

**Manual verification:** none. Every behaviour is contract-shape,
projection-shape, or self-host-build-shape; no UI; no end-to-end
UX flow.

## Tasks

### T1: Flip contract files and clean the seed AGENTS.md

**Depends on:** none

**Verification mode:** TDD (drift tests + schema tests) +
goal-based check (`make build-check`).

**Tests:** (test file:
`packages/agentbundle/agentbundle/build/tests/test_contract.py`,
new test class `TestCodexSkillDirectDirectory`)

- *Schema test*: `docs/contracts/adapter.toml` parses cleanly,
  the Codex `skill` projection has `mode = "direct-directory"`,
  `target-path = ".agents/skills/"`, `on-conflict =
  "prompt-then-preserve"`, and no
  `managed-block-delimiter-start` / `-end` keys. [AC1]
- *Drift test*: `docs/contracts/adapter.toml` and
  `packages/agentbundle/agentbundle/_data/adapter.toml` produce
  byte-identical bytes when read. [AC2]
- *Seed test*:
  `packs/core/seeds/AGENTS.md` contains neither
  `<!-- agent-skills:start -->` nor `<!-- agent-skills:end -->`.
  [AC15]
- *Goal-based*: `make build-check` exits clean. [AC28]

**Approach:**

- Edit `docs/contracts/adapter.toml` — the
  `[[adapter.codex.projection]]` block starting at line 208
  (header) with body at lines 209-214 (verified:
  `primitive = "skill"` at line 209,
  `managed-block-delimiter-end` at line 213). Rewrite to the
  new `direct-directory` shape per AC1.
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml`
  — the same block at the same line range (the file is
  byte-identical to the canonical contract today; AC2
  preserves that).
- Edit `packs/core/seeds/AGENTS.md` lines 113-114 to remove the
  empty delimiter pair.
- Add the schema test and the drift test to
  `test_contract.py` (verify path; create if absent under the
  build tests root).

**Done when:** all listed tests pass; `make build-check` clean.

---

### T2: Migration strip — text-only mechanism (no projection wiring yet)

**Depends on:** none

**Verification mode:** TDD.

**Tests:** (test file:
`packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py`,
new test class `TestMigrationStripPureFunction`)

- *Happy path*: a fixture `AGENTS.md` string containing
  `<!-- agent-skills:start -->\n- **a** — desc-a\n- **b** — desc-b\n<!-- agent-skills:end -->\n`
  with outside-delimiter prose before and after, passed through
  `_strip_legacy_skill_block`, returns a string with neither
  delimiter literal and with the outside-delimiter prose
  preserved byte-for-byte. [AC11]
- *Already-clean*: a fixture `AGENTS.md` string with no
  delimiters returns byte-identical through the strip. [AC12]
- *Idempotent*: running the strip twice on the same input
  returns the same result as running it once. [AC13]
- *Non-list content lost*: a fixture string with sentinel prose
  (e.g. `"<<HAND-EDITED-PRESERVE-ME>>"`) *between* the
  delimiters, after one strip, no longer contains the sentinel.
  [AC14]
- *Retention contract — symbol exists*: a test imports
  `_splice_managed_block` from `agentbundle.build.adapters.codex`;
  the import resolves without error. [AC23(i)]
- *Retention contract — call observed*: a test patches
  `codex._splice_managed_block` with
  `unittest.mock.patch.object(codex, "_splice_managed_block",
  wraps=codex._splice_managed_block)`, calls
  `_strip_legacy_skill_block(input)` with input containing both
  delimiter literals, and asserts the patched callable's
  `call_count == 1`. The `wraps=` argument lets the real
  function still run so the strip behaviour is unchanged.
  [AC23(ii)]

**Approach:**

- Add a new private function in `codex.py`,
  `_strip_legacy_skill_block(text: str) -> str`, that:
  1. If neither delimiter is in `text`, return `text` unchanged
     (already-clean).
  2. If both delimiters are present, call
     `_splice_managed_block(text, start, end, "")` to splice
     empty content between the delimiters.
  3. Then remove the now-empty
     `<!-- agent-skills:start -->\n<!-- agent-skills:end -->\n`
     literal (and any single-line concatenation variant) from
     the result.
- Hardcode the legacy delimiter literals
  (`<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`)
  inside `codex.py` for the migration window. Do **not** re-add
  them to the contract.
- New test class in `test_adapter_codex.py` exercising the five
  cases as pure-function tests (no filesystem).

**Done when:** all five strip tests pass; `_splice_managed_block`
is unchanged in implementation and still defended by the
retention test.

---

### T3: Add `direct-directory` branch in codex.py (additive — managed-block path intact)

**Depends on:** T1

**Verification mode:** TDD.

**Tests:** (test file:
`packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py`,
new test class `TestDirectDirectoryProjection`)

- *Byte-equal projection*: project the
  `fixtures/codex-native/two-skill/` fixture pack through
  `codex.project_packs([pack], contract, tmp_path)`; for every
  file (`flat/SKILL.md`, `nested/SKILL.md`, `nested/scripts/run.sh`,
  `nested/references/notes.md`), the projected
  `tmp_path/.agents/skills/<name>/<path>` has
  `read_bytes()` equal to the source. [AC3, AC4]
- *Symlink pass-through*: project the
  `fixtures/codex-native/symlinked/` fixture;
  `os.path.islink(tmp_path/.agents/skills/linker/references/shared.md)`
  is true; `os.readlink(...)` returns `../assets/shared.md`.
  [AC5]
- *Same-name last-wins (Codex)*: project the same-name fixture
  pair `[pack_a, pack_b]`; assert the projected
  `same-name/SKILL.md` contains `PACK_B_SENTINEL` and not
  `PACK_A_SENTINEL`. Reverse the order and assert the inverse.
  [AC6 — Codex case]
- *Managed-block path still works*: the existing
  `_project_managed_block` and `_extract_description` are
  retained in this task; existing tests
  (`test_skill_description_appears_in_managed_block`,
  `test_outside_block_preserved`, etc.) continue to pass. The
  legacy contract entry's removal in T1 means the
  `managed-block-inline` branch is no longer reached for
  `skill` — but the code is still importable and unit-testable
  (existing tests construct the contract dict in-memory).

**Approach:**

- In `codex.py:project_packs`, add a `direct-directory` branch
  to the mode dispatch (currently lines 49-55, between the
  `managed-block-inline` and `direct-file` branches):
  ```python
  elif mode == "direct-directory":
      target_dir = output_root / rule["target-path"].rstrip("/")
      target_dir.mkdir(parents=True, exist_ok=True)
      for source_dir in source_dirs:
          for entry in sorted(source_dir.iterdir()):
              if entry.is_dir():
                  destination = target_dir / entry.name
                  if destination.exists():
                      shutil.rmtree(destination)
                  shutil.copytree(entry, destination, symlinks=True)
  ```
  Shape matches `claude_code.py:_project_direct_directory`
  (lines 63-72) and `kiro.py:_project_direct_directory`
  (lines 303-309). Same-name last-wins falls out naturally from
  iteration order (`source_dirs` is in `pack_paths` order; the
  later pack's `rmtree` + `copytree` overwrites the earlier
  pack's projection of the same name).
- Keep `_project_managed_block`, `_extract_description`, and
  `_splice_managed_block` intact in this task. Their removal is
  T4.
- Create the four fixture packs under
  `packages/agentbundle/agentbundle/build/tests/fixtures/codex-native/`:
  `two-skill/`, `symlinked/`, `pack-a/`, `pack-b/`. Each pack
  carries `.apm/skills/<name>/SKILL.md` (with frontmatter so
  description-extraction tests still pass under the
  managed-block branch that's about to be removed).

**Done when:** new `TestDirectDirectoryProjection` tests pass;
all existing tests in `test_adapter_codex.py` still pass;
`make build-check` clean. (The branch is reachable only via the
new contract entry from T1; the managed-block branch is
dead-code-but-not-removed.)

---

### T4: Remove managed-block path; integrate migration strip; flip stale assertion

**Depends on:** T2, T3

**Verification mode:** TDD.

**Tests:** (extend
`test_adapter_codex.py`'s `TestDirectDirectoryProjection`;
edit `test_self_host_check.py`)

- *Migration strip integrated — happy path*: place the
  `fixtures/codex-native/agents-md/populated.md` content at
  `<tmp_path>/AGENTS.md`, then call
  `codex.project_packs([pack], contract, tmp_path)`. The
  resulting file contains neither legacy delimiter; outside
  prose preserved. [AC10, AC11]
- *Migration strip integrated — already-clean*: place
  `clean.md` content at `<tmp_path>/AGENTS.md`; after
  `project_packs`, the file is byte-identical to the input.
  [AC12]
- *Migration strip integrated — idempotent*: call
  `project_packs` twice in sequence against an `<output_root>`
  whose `AGENTS.md` originally contained the legacy block; the
  file after the second call equals the file after the first
  call byte-for-byte. [AC13]
- *Migration strip integrated — non-list content lost*: place
  `hand-edited.md` content (with a sentinel between the
  delimiters) at `<tmp_path>/AGENTS.md`; after `project_packs`,
  the sentinel substring is not present. [AC14]
- *Five obsolete tests are gone* (AC24):
  `test_skill_description_appears_in_managed_block`,
  `test_outside_block_preserved`, `test_idempotent`,
  `test_project_packs_aggregates_skills_before_splicing`,
  `test_security.py::test_skill_description_with_end_marker_is_rejected`.
- *`test_self_host_check.py`* asserts
  `assertNotIn("<!-- agent-skills:start -->", text)` against
  the projected output. [AC26]
- *Repo sweep*: a `grep -r "agent-skills:start" packages/
  packs/ docs/contracts/ tools/` outside of `codex.py` and
  `docs/rfc/` returns zero hits. (Acceptable hits: `codex.py`
  carries the literals as constants; `docs/rfc/` keeps them as
  historical context.)
- *Retained tests still pass* (AC25): the four named tests
  pass unchanged.

**Approach:**

- In `codex.py:project_packs`, before the primitive-dispatch
  loop, call the migration strip on `output_root / "AGENTS.md"`
  if it exists. AC10 pins this is the project-root AGENTS.md —
  the same file `self_host._compose_agents_md` writes:
  ```python
  agents_md = output_root / "AGENTS.md"
  if agents_md.exists():
      original = agents_md.read_text(encoding="utf-8")
      stripped = _strip_legacy_skill_block(original)
      if stripped != original:
          agents_md.write_text(stripped, encoding="utf-8")
  ```
  The `if stripped != original` guard preserves AC12's
  byte-identity for the already-clean case (no spurious mtime
  bump).
- Delete `_project_managed_block` and `_extract_description`.
  Retain `_splice_managed_block` (called by
  `_strip_legacy_skill_block` — defended by T2's AC23 test).
  Remove the `managed-block-inline` branch from the dispatch in
  `project_packs`.
- Delete the five obsolete tests per AC24.
- Flip `test_self_host_check.py`'s `assertIn` at the current
  line 364 (verify line after T3's edits) to `assertNotIn`.
- Walk the `grep` output and remove any other stale references
  outside the documented exceptions.

**Done when:** all integration tests pass; the five obsolete
tests are gone; the `grep` sweep is clean;
`_project_managed_block` and `_extract_description` are gone;
`_splice_managed_block` remains; `make build-check` clean.

---

### T5: Add `project_packs` to claude_code and kiro; route self_host through it

**Depends on:** none

**Verification mode:** TDD.

**Tests:** (extend `test_adapter_claude_code.py`,
`test_adapter_kiro.py`; new test in
`test_self_host_check.py` or its sibling for the orchestrator
routing)

- *`claude_code.project_packs` exists*: a multi-pack call
  iterates `pack_paths` in order, projecting each pack via the
  existing `project()`. Test: two packs, each shipping one
  skill; both skills exist at the projected target after one
  call. [AC7]
- *`kiro.project_packs` exists*: same shape as above against
  the Kiro target. [AC7]
- *`claude_code.project(pack)` delegates*: calling
  `project(pack)` produces the same output as
  `project_packs([pack])`. Asserts the single-pack wrapper
  remains functional. [AC9]
- *`kiro.project(pack)` delegates*: same. [AC9]
- *Same-name last-wins (claude_code, kiro)*: project the
  same-name fixture pair through each of the two adapters'
  `project_packs`; assert the AC6 last-wins rule holds for
  both. [AC6 — claude-code and kiro cases]
- *`self_host.py` routes through `project_packs`*: a
  **mock-based invocation test** patches the per-adapter
  `project_packs` attribute on each module in `SELF_HOST_ADAPTERS`
  (`claude_code` and `codex` only — kiro is excluded from self-host
  per AC8) and runs the self-host entry point; the test asserts
  each patched mock was called exactly once with
  `[pack.path for pack in packs]` as the first positional arg. A
  source-text assertion is rejected because a refactor that
  preserved the contract but changed the call shape (helper, comp.
  expression) would break the source-text grep without breaking
  behaviour. [AC8]

**Approach:**

- In `claude_code.py`, add at module level:
  ```python
  def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
      for pack_path in pack_paths:
          project(pack_path, contract, output_root)
      # Orphan sweep wires in via T7; this task's body is the
      # iteration shim only.
  ```
  Same shape in `kiro.py`.
- In `self_host.py` (currently lines 185-198), replace the
  per-pack inner loop with a `project_packs` call. `SELF_HOST_ADAPTERS`
  (`self_host.py:70` — `("claude-code", "codex")`) is the routing
  allow-list and is **not** widened by this spec; kiro stays out of
  self-host per AC8. **Reuse the existing module-keyed `registry`**
  in
  `packages/agentbundle/agentbundle/build/adapters/__init__.py:24-29`
  (`{"claude_code": claude_code, "kiro": kiro, ...}` — Python
  module names) — do NOT add a third dict. The existing
  `ADAPTERS` mapping (`{"claude-code": claude_code.project, ...}`)
  stays untouched because `commands/render.py:52,134` reaches
  into its keys. Concrete shape:
  ```python
  from agentbundle.build.adapters import ADAPTERS, registry, codex

  for adapter_name in ADAPTERS:  # hyphenated contract name (iteration unchanged)
      if adapter_name not in contract["adapter"]:
          continue
      if adapter_name not in SELF_HOST_ADAPTERS:
          continue
      if adapter_name == "codex":
          # Codex still routes through _compose_agents_md.
          continue
      adapter_module = registry[adapter_name.replace("-", "_")]
      adapter_module.project_packs(
          [pack.path for pack in packs], contract, output_root,
      )
  ```
  The `adapter_name.replace("-", "_")` step bridges the
  hyphenated → underscored convention between `ADAPTERS` and
  `registry`. Audit:
  `grep -rn "ADAPTERS\b\|registry\b" packages/ tools/` before
  T5 lands; per AC9 the audit is recorded in the PR
  description.
- The single-pack `project()` functions in `claude_code.py` and
  `kiro.py` are retained as one-liners that call
  `project_packs([pack_path], ...)`. Existing callers of
  `claude_code.project(pack_path, ...)` and
  `kiro.project(pack_path, ...)` continue to work unchanged.
  Known in-tree callers as of 2026-05-25:
  (1) `self_host.py` (refactored by this task);
  (2) `packages/agentbundle/agentbundle/commands/install.py:1114,1116`
  (`_rewrite_user_scope_hook_paths` invokes them against a tempdir
  for hook-path rewriting). Caller (2) stays on the single-pack
  wrapper and is not refactored. Pre-T5 verification fires the two
  `rg` sweeps from AC9; any new caller surfaced is enumerated in
  the PR.

**Done when:** all listed tests pass; `self_host.py` routes all
three adapters through `project_packs`; existing `project()`
single-pack signatures still work for callers (if any) outside
`self_host.py`; `make build-check` clean.

---

### T6: Shared `sweep_orphans` helper (TDD; no adapter wiring yet)

**Depends on:** none

**Verification mode:** TDD.

**Tests:** (new test file:
`packages/agentbundle/agentbundle/build/tests/test_direct_directory_cleanup.py`)

- *Removes orphan directory*: `target_dir` containing `{a/, b/, c/}`
  with `expected_names = {"a", "c"}` results in `b/` removed,
  `a/` and `c/` retained. [AC16, mechanism of AC17-AC19]
- *No-op on full match*: `target_dir` containing `{a/, b/}`
  with `expected_names = {"a", "b"}` has the same contents
  after the sweep.
- *No-op on missing target*: `sweep_orphans(<nonexistent path>, ...)`
  returns without raising. [AC16]
- *Ignores root files*: `target_dir` containing a directory
  `a/` not in `expected_names` and a file `README.md` at the
  root, after `sweep_orphans(target_dir, set())`, has the file
  unchanged and `a/` removed. [AC16]
- *Symlink-safe sweep*: a `target_dir` with a
  symlink-to-directory `b -> <external_path>`,
  `expected_names = {"a"}` removes the symlink entry `b`
  (`Path.unlink`) but leaves `<external_path>` intact. The test
  asserts `not (target_dir / "b").exists()` (after the sweep)
  and `external_path.exists()` (still there). [AC21]

**Approach:**

- Create
  `packages/agentbundle/agentbundle/build/projections/direct_directory.py`
  with the single function `sweep_orphans`:
  ```python
  from pathlib import Path
  import shutil


  def sweep_orphans(target_dir: Path, expected_names: set[str]) -> None:
      if not target_dir.exists():
          return
      for entry in target_dir.iterdir():
          if entry.is_symlink():
              if entry.name not in expected_names:
                  entry.unlink()
              continue
          if not entry.is_dir():
              continue
          if entry.name not in expected_names:
              shutil.rmtree(entry)
  ```
- New test file
  `test_direct_directory_cleanup.py` exercising the five cases
  above. Use `tmp_path` fixtures; build the symlink with
  `Path.symlink_to(external_dir, target_is_directory=True)`.

**Done when:** all five tests pass; the module is stdlib-only;
no other helpers are added to the module (per the spec's
`Never do` boundary).

---

### T7: Wire `sweep_orphans` into all three `direct-directory` adapters

**Depends on:** T3, T5, T6

**Verification mode:** TDD.

**Tests:** (extend
`test_adapter_codex.py`, `test_adapter_claude_code.py`,
`test_adapter_kiro.py`)

- *Codex orphan sweep*: two-stage projection per AC17 —
  `codex.project_packs([three-skill])` then
  `codex.project_packs([two-skill-shrink])` against the same
  `output_root` — leaves `<output_root>/.agents/skills/` with
  exactly `{a, c}`. [AC17]
- *Claude Code orphan sweep*: same fixture pair, target
  `<output_root>/.claude/skills/`. [AC18]
- *Kiro orphan sweep*: same fixture pair, target
  `<output_root>/.kiro/skills/`. [AC19]
- *Two-pack union — all three adapters*: a single
  `project_packs([pack_a, pack_b], ...)` against each adapter
  with `pack_a.skills = {a, b}` and `pack_b.skills = {b, c}`
  projects all three names; then `project_packs([pack_a], ...)`
  alone keeps `{a, b}` (b surviving because pack_a still ships
  it) and removes `c`. Parameterised across all three adapters.
  [AC20]
- *Symlink-safe sweep at the adapter level*: a fixture where
  the projected target dir is pre-seeded with a symlink-to-
  external-directory whose name is not in the source set; the
  symlink is removed but the external target survives.
  Exercised against the Codex output dir (the other two
  delegate to the same helper, so one adapter-level fixture
  covers the wire-up). [AC21]

**Approach:**

- **Wiring shape per adapter.** Codex's `project_packs`
  already has `source_dirs` and `target_dir` in scope at the
  primitive-dispatch level (codex.py lines 41-44 pre-change,
  and the new `direct-directory` branch from T3); the sweep
  call slots into that branch directly.
  `claude_code.project_packs` and `kiro.project_packs` (added
  in T5) iterate per-pack `project()` and have no `source_dirs`
  or `target_dir` in scope after the loop returns — those locals
  live inside each per-pack `project()` call. T7 reconstructs
  both from `pack_paths` + `contract` + the adapter's own
  contract block:
  ```python
  from pathlib import Path
  from agentbundle.build.projections.direct_directory import sweep_orphans

  _ADAPTER_NAME = "claude-code"   # or "kiro" in kiro.py


  def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
      adapter_block = contract["adapter"][_ADAPTER_NAME]
      for entry in adapter_block.get("projection", []):
          if entry["primitive"] == "skill" and entry["mode"] == "direct-directory":
              return output_root / entry["target-path"].rstrip("/")
      return None


  def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
      for pack_path in pack_paths:
          project(pack_path, contract, output_root)
      target_dir = _skill_direct_directory_target(contract, output_root)
      if target_dir is None:
          return
      skill_source_path = contract["primitive"]["skill"]["source-path"].rstrip("/")
      source_dirs = [
          pack_path / skill_source_path
          for pack_path in pack_paths
      ]
      source_dirs = [source_dir for source_dir in source_dirs if source_dir.exists()]
      expected_names = {
          entry.name
          for source_dir in source_dirs
          for entry in source_dir.iterdir()
          if entry.is_dir()
      }
      sweep_orphans(target_dir, expected_names)
  ```
  In `codex.py`, the same logic sits **inside** the
  `direct-directory` branch of the primitive-dispatch (where
  `source_dirs`, `rule`, and `target_dir` are already in
  scope); no helper required, because the data is already
  built. Codex's call:
  ```python
  expected_names = {
      entry.name
      for source_dir in source_dirs
      for entry in source_dir.iterdir()
      if entry.is_dir()
  }
  sweep_orphans(target_dir, expected_names)
  ```
- **The sweep is bound to the `skill` primitive only** (per the
  spec's `Never do` boundary). Wire it only inside the `skill`
  primitive's `direct-directory` branch — not as a generic
  every-`direct-directory` post-pass. The `_skill_direct_directory_target`
  helper guards this by name: it explicitly checks
  `entry["primitive"] == "skill"`.
- **Deliberate duplication of `_skill_direct_directory_target`
  across `claude_code.py` and `kiro.py`.** The spec's `Never do`
  boundary forbids expanding `projections/direct_directory.py`
  beyond `sweep_orphans`, so consolidating the target-resolution
  helper into a shared module is barred. The two copies must stay
  in lockstep; each one carries a single-line cross-reference
  comment pointing at its sibling
  (`# Mirror of kiro.py:_skill_direct_directory_target; keep in
  sync.` in `claude_code.py`, inverse in `kiro.py`) so a future
  maintainer touching one sees the other. A shared helper is a
  future RFC, not this spec.
- **Why the helper, not refactor of `project()`.** Refactoring
  `claude_code.project()` / `kiro.project()` to return their
  per-pack `source_dirs` / `target_dir` would broaden the
  blast radius (their signatures change; other callers may
  break). The helper approach keeps `project()` unchanged and
  isolates the multi-pack union calculation to `project_packs`,
  which is the new surface this spec owns.

**Done when:** all listed orphan-sweep tests pass; all prior
adapter tests still pass; the two-pack-union regression test
(AC20) passes for all three adapters; `make build-check` clean.

---

### T8: Amend `docs/specs/distribution-adapters/spec.md` per RFC-0009

**Depends on:** T1, T4, T7

**Verification mode:** goal-based check (grep + `make build-check`)
plus reviewer pass.

**Tests:**

- *Projection table* — locate by adapter name to avoid
  false positives if any other adapter still uses
  `managed-block-inline`:
  `rg -n "codex.*(skill|managed-block|direct-directory)|^\| .*codex" docs/specs/distribution-adapters/spec.md`,
  or read the table by section heading directly. Updated to
  show Codex `skill` as `direct-directory` with target
  `.agents/skills/`.
- *Uniform multi-pack entry-point invariant subsection* added
  documenting: every `direct-directory` adapter exposes
  `project_packs(pack_paths, contract, output_root)`;
  `self_host.py` routes through it. **Concrete assertion**:
  `rg -n "project_packs\(pack_paths" docs/specs/distribution-adapters/spec.md`
  returns ≥ 1 hit; `rg -n "Uniform multi-pack" docs/specs/distribution-adapters/spec.md`
  returns ≥ 1 hit (subsection heading).
- *Orphan-cleanup invariant subsection* added (or existing
  `direct-directory` mode subsection extended) documenting:
  every `direct-directory` projection of `skill` runs a
  post-projection orphan sweep that removes child directories
  not in the union of source skill names across the call's
  pack list. **Concrete assertion**:
  `rg -n "sweep_orphans|orphan sweep|orphan-cleanup" docs/specs/distribution-adapters/spec.md`
  returns ≥ 1 hit; the surrounding paragraph names the
  "union of source skill names across the call's pack list"
  invariant (verified by `rg -n "union of source skill names"`).
- *Symlink-pass-through invariant* cited explicitly under the
  `direct-directory` mode description (with reference to
  `shutil.copytree(..., symlinks=True)` semantics). Concrete
  assertion: `rg -n "symlinks=True" docs/specs/distribution-adapters/spec.md`
  returns ≥ 1 hit.
- *Cites RFC-0009* by section name (`§ Adapter contract change`,
  `§ Failure modes`). Concrete assertion: both literal section
  names appear in the file
  (`rg -n "RFC-0009" docs/specs/distribution-adapters/spec.md`
  returns hits including the two section names).
- *`make build-check` clean.* [AC27, AC28]

**Approach:**

- Edit `docs/specs/distribution-adapters/spec.md` directly
  (the spec itself is per-instance, not a projected file).
- Update the projection table; add the uniform-entry-point,
  orphan-cleanup, and symlink-pass-through invariants; add the
  RFC-0009 citation.
- Per spec drift discipline, this spec amendment lands in the
  same PR as the implementation; the
  `distribution-adapters/spec.md` adversarial review fires on
  that amendment-bearing PR's work-loop, not on this planning
  run.

**Done when:** the spec amendment is committed; gates clean;
the projection table reflects the new Codex shape; the three
invariants are documented.

---

### T9: Regenerate `dist/`, changelog entry, linter warning

**Depends on:** T1, T4, T7, T8

**Verification mode:** goal-based check (`make build-check`,
grep, dist enumeration) plus a unit test for the linter
extension.

**Tests:**

- *`make build-check` clean* end-to-end. [AC28]
- *Dist enumeration*: a test iterates
  `packs/core/.apm/skills/*/` and asserts each corresponding
  `dist/codex/.agents/skills/<name>/SKILL.md` exists with
  bytes equal to the source. Spot-check sentinels: `work-loop`,
  `new-spec`, `new-rfc`, `new-adr`. [AC29]
- *No legacy managed block in dist*:
  `grep -r "agent-skills:start" dist/` returns zero hits.
- *Changelog entry present at `docs/product/changelog.md`*:
  the file contains an entry naming RFC-0009, the migration-
  strip rollout window (released N; strip removed in N+1), and
  the `_splice_managed_block` removal target release. [AC30]
- *Linter warning*: a unit test against `lint-agents-md.py`
  passes a synthetic projected `AGENTS.md` (containing
  `<!-- agent-skills:start -->`) and a synthetic contract
  declaring Codex `skill` as `direct-directory`, then asserts
  the linter emits a warning naming the offending file. The
  linter's exit code is unchanged for warnings (verify the
  existing contract). [AC31]

**Approach:**

- Run `make build-self` (or the equivalent dist-regeneration
  recipe) and commit the resulting `dist/` changes.
- Add the changelog entry to `docs/product/changelog.md`
  naming RFC-0009, the rollout window (concrete release
  numbers picked during EXECUTE), and the
  `_splice_managed_block` removal target. The release
  numbering convention is established by the existing entries
  in that file; match the convention.
- Extend `tools/lint-agents-md.py` with a new check function
  that:
  1. Reads the adapter contract via the existing pathway the
     linter uses (or `tomllib` if the linter doesn't read
     contracts today).
  2. If the Codex `skill` projection is `direct-directory`
     and the projected `AGENTS.md` contains
     `<!-- agent-skills:start -->`, emit a warning naming the
     file path.
  3. Routes the warning through the existing `warn(msg)` closure
     defined inside `main()` at `tools/lint-agents-md.py:53` —
     `warn()` prints to stderr without incrementing `fail`, so
     the linter's exit code stays 0. The new check is added
     **inline inside `main()`** adjacent to the existing
     `note(...)` checks (rule 10d / 10e at lines 241-268 are the
     reference shape); a top-level helper is not introduced,
     matching the established linter idiom. No new exit-code
     channel invented.

- **T9 linter unit test shape**: the check lives inside `main()`,
  so the test is a **CLI subprocess invocation**, not a direct
  function call. Pin the test as: write the synthetic
  `AGENTS.md` (containing `<!-- agent-skills:start -->`) and the
  synthetic adapter contract (declaring Codex `skill` as
  `direct-directory`) to `tmp_path`; invoke `lint-agents-md.py`
  via `subprocess.run([sys.executable, "tools/lint-agents-md.py"], cwd=tmp_path, capture_output=True)`;
  assert the return code is 0 (warning, not failure) and that
  the stderr stream contains both the `⚠` warn marker and the
  offending file path.
- Unit test for the linter goes alongside the existing linter
  tests (verify path during EXECUTE — likely `tools/tests/` or
  a fixture-based test under
  `packages/agentbundle/agentbundle/build/tests/`).

**Done when:** `make build-check` clean; dist enumeration test
passes; `grep` sweep clean; changelog entry present; linter
warning test passes.

---

## Rollout

This spec ships through nine tasks. The work-loop's supervisor
mode can fan out T2, T5, T6 in parallel during EXECUTE (all
declare `Depends on: none` or independent dependencies); the
others serialise on their declared dependencies.

The contract flip in T1 + the seed edit + T4's managed-block
removal are the breaking change for Codex users: their projected
`AGENTS.md` loses the managed block, and their
`.agents/skills/<name>/SKILL.md` gains the full body.

**Migration window.** The migration-strip step (T2 mechanism +
T4 integration) runs unconditionally on every install for one
minor release after the post-flip release. In the release
after, the strip mechanism (`_strip_legacy_skill_block`) and
`_splice_managed_block` are removed; adopters who haven't run an
intervening install carry their stale managed block forever
(documented limitation, per RFC-0009 § Drawbacks).
`_splice_managed_block` removal is a follow-on PR tracked in
the changelog entry (T9) against the next-minor milestone.

**No flag-gated rollout.** The contract change is the gate.
Adopters who upgrade to the post-flip CLI version get the new
behaviour automatically. Adopters who don't upgrade keep the
old behaviour — Codex users on the old CLI continue to receive
the managed-block teaser. This is fine: RFC-0009 § Drawbacks
records the one-minor-release migration window as deliberate.

**Adopter-visible change.** On the first install after the
upgrade, the adopter sees their `AGENTS.md` lose the empty
managed block (or a populated one, if they hadn't pruned it).
The change is narrow (delimiter region only) and matches
RFC-0009 § Migration path's promise.

## Risks

Implementation risks the executing agent should watch:

- **Cross-pack orphan-sweep miscalculation** (T7). If
  `expected_names` is computed per-pack instead of as the union
  across the call's pack list, projecting from a pack that ships
  a subset of the previous run's skills will orphan-clean
  another pack's skills. Mitigation: the AC20 two-pack-union
  regression test is the explicit guard; if it fails, the
  calculation is wrong.
- **Self-host `dist/` regeneration churn** (T9). Every skill in
  every pack now ships through `direct-directory`; the
  `dist/codex/` tree grows substantially. Mitigation: T9's
  `dist` regeneration is part of the gated PR; a reviewer
  scanning the diff will see the new tree and can sanity-check
  the size delta.
- **`make build-check` drift between contract files** (T1).
  The two contract files (`docs/contracts/adapter.toml` and
  `_data/adapter.toml`) drift silently if edited out-of-sync.
  Mitigation: T1's drift test catches this at the file-bytes
  level, not just by schema parsing.
- **`_splice_managed_block` retention drift** (T4 onward). The
  helper is retained for the migration window. A future
  refactor noticing it has no direct test coverage might
  remove it prematurely. Mitigation: AC23's retention contract
  test pins the helper's call site via
  `_strip_legacy_skill_block`; a removal that breaks the
  contract is now a test failure, not an invisible regression.
- **Linter contract for warnings** (T9). The linter's
  exit-code contract for warnings vs. failures is not pinned
  in this plan. Mitigation: T9's approach step verifies the
  existing convention before adding the new check.

Design-level risks (hand-edited managed-block content
destruction; the one-minor-release migration window leaving
adopters who skip a release with stale blocks) are recorded in
RFC-0009 § Drawbacks and § Failure modes; this plan does not
restate them.

## Changelog

- 2026-06-10: follow-up correction after the self-hosting change restored
  Codex to `SELF_HOST_ADAPTERS`. The 2026-05-25 course-correction entry
  below records what shipped with this spec at the time; the current
  contract is that self-host drift-gates Codex `.agents/skills/`,
  `.codex/agents/`, and `.codex/hooks.json` alongside Claude Code.
- 2026-05-25: initial plan, drafted from RFC-0009 (Draft status).
  Pinned the author's leans on Unresolved Q2 (deterministic
  last-wins, all three adapters), Q3 (shared cleanup across
  three adapters), Q4 (unconditional migration strip). Q1
  (enterprise-deployment fallback) noted as out of scope and
  deferred to the RFC's reviewer surface.
- 2026-05-25: post-spec-mode-review revision. Split original
  T3 into T3 (additive direct-directory branch) + T4 (remove
  managed-block path, integrate strip, flip stale assertion,
  grep sweep) so each task is one PR. Added T5
  (`project_packs` shims for claude_code and kiro plus
  `self_host.py` routing) because the cross-cutting orphan
  sweep cannot wire into single-pack adapter entry points.
  Renumbered downstream tasks. Pinned AC line-numbers and
  fixture shapes; pinned changelog path
  (`docs/product/changelog.md`); committed to the linter
  warning (AC31) without hedging; added retention test (AC23)
  for `_splice_managed_block`; pruned design risks from the
  Risks section.
- 2026-05-25: round-2 spec-mode review revision. Fixed T7
  Approach to reconstruct `source_dirs` and `target_dir` from
  `pack_paths` + `contract` for claude_code/kiro (they don't
  live at `project_packs` scope after the per-pack iteration
  returns); rewrote AC23's retention test to use
  `unittest.mock.patch.object(..., wraps=...)` instead of the
  tautological same-output assertion; pinned the `ADAPTERS`
  dispatch-table refactor as `getattr`-on-module (the smaller
  diff); added the dual-behaviour note to AC10 (strip is a
  no-op in self-host, real in adopter installs); broadened
  AC9's grep to also enumerate `ADAPTERS` reach-ins;
  anchored T8's projection-table grep to the Codex row; fixed
  T1's line-range citation.
- 2026-05-25: round-3 spec-mode review revision. Reviewer
  returned clean with one surfaced nit: T5's
  `ADAPTER_MODULES` dict duplicated the existing
  module-keyed `registry` in `adapters/__init__.py:24-29`
  (different key conventions — hyphenated vs. underscored).
  Rewrote T5 Approach to reuse `registry` via
  `adapter_name.replace("-", "_")` instead of introducing a
  third dict. No new ACs needed; the change is internal to
  T5's Approach.
- 2026-05-25: post-review seed adapter-neutralisation. The user
  flagged that `packs/core/seeds/AGENTS.md` mentions `.claude/skills/`
  and `.claude/agents/` in three places — references that ship to
  every adopter (via `agentbundle scaffold`) and read as wrong for
  Codex (whose skills live at `.agents/skills/`) and Kiro (`.kiro/skills/`).
  Pre-existing issue made visible by RFC-0009 because Codex now has
  a real distinct surface. Fixed in three small edits: (a) "the
  content belongs in `docs/`, `.claude/skills/`, …" → "…in `docs/`,
  a skill, …"; (b) the source-of-truth-table row for `<repeating
  task>` names the file (`SKILL.md`) instead of the directory,
  noting "your IDE handles discovery"; (c) the "Specialist
  subagents" section header names the adapter contract directly —
  Claude Code only; Codex and Copilot drop the `agent` primitive.
  No new adapter-templating mechanism introduced; the seed is now
  adapter-neutral by content.
- 2026-05-25: post-review course correction. User flagged that
  with Codex's `skill` projection growing from a tiny managed
  block to a full body tree, leaving `codex` in
  `SELF_HOST_ADAPTERS` would mirror every skill into the working
  tree (`.agents/skills/`) alongside `.claude/skills/` — pure
  maintainer overload, and the project's stance is "we never want
  maintainer overload." Narrowed `SELF_HOST_ADAPTERS` to
  `("claude-code",)`. Removed the `codex.project_packs` call from
  `_compose_agents_md` (now a no-op for AGENTS.md anyway under the
  direct-directory contract). Removed the unreachable
  `if adapter_name == "codex"` branch from `_project_all_adapters`.
  `.agents/` gitignored. AC8, AC10, and the
  `distribution-adapters/spec.md` amendment updated to reflect the
  narrower self-host surface. Codex correctness is gated by unit
  tests + AC29 tempdir projection (already in place). Test
  `test_self_host_composes_agents_body_codex_block_and_footer`
  was changed for that now-superseded narrowing; the 2026-06-10
  follow-up entry above restores `.agents/skills/` to self-host and
  replaces the old codex-mock call_count == 0 pin.
- 2026-05-25: round-5 review revision. Reviewer surfaced two
  concerns + one nit; addressed all. (1) AC9 extended to
  enumerate the three test callers at
  `tests/unit/test_pipeline_phase_order.py:168,228,229` so the
  spec's "known callers" list matches the world it claims.
  (2) T9 Approach pinned: the new linter check is added inline
  inside `main()` (not as a top-level function) because
  `warn()` is a closure of `main()` capturing `nonlocal fail`;
  the T9 unit test is now pinned as a `subprocess.run` CLI
  invocation asserting on exit code and stderr. (3) Line-number
  citations in AC8 (`self_host.py:70`, `self_host.py:266`)
  replaced with constant-name citations for line-drift
  resistance.
- 2026-05-25: round-4 (pre-EXECUTE confirmation) review
  revision. Reviewer surfaced two blockers and three
  high-priority concerns; addressed all five in spec.md and
  plan.md. (1) AC8 narrowed: `SELF_HOST_ADAPTERS` excludes
  `kiro` (`self_host.py:70`), so self-host routes only
  `claude-code` and `codex` through `project_packs`;
  `kiro.project_packs` exists per AC7/AC19 but is not invoked
  from self-host. (2) AC9 enumerates the
  `commands/install.py:1114,1116` callers of single-pack
  `kiro.project` / `claude_code.project` as known callers that
  stay on the retained wrapper; grep rewritten as `rg`.
  (3) T5 routing test committed to mock-based (not source-text).
  (4) T7 helper duplication named as deliberate with sibling
  cross-reference comments. (5) T8 concrete `rg` assertions
  added for each invariant subsection. (6) T9 wires through
  the existing `warn()` helper at `lint-agents-md.py:53`
  rather than inventing a warning channel. Concern 6 (T3-T4
  dead-code interregnum if landed in separate PRs) is moot
  because this work-loop session lands all nine tasks in a
  single PR — recorded here for future maintainers reading the
  plan offline.
