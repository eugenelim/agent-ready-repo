# Spec: codex-native-skills

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0009](../../rfc/0009-codex-native-skills.md)
  — sole driving RFC. Touches [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (modifies the adapter contract this RFC introduced) and amends
  [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  (Codex `skill` projection table entry, multi-pack adapter entry
  point, orphan-cleanup invariant for `direct-directory` adapters).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Migrate the Codex adapter's `skill` projection from
`managed-block-inline` (inlined one-line descriptions in `AGENTS.md`)
to `direct-directory` (full skill bodies at
`.agents/skills/<name>/SKILL.md`), so Codex users receive the same
workflow content Claude Code and Kiro users already do. The migration
is contract + adapter + cross-cutting cleanup + tests in one spec,
with four invariants pinned alongside the flip:

1. **Byte-equal projection.** Every file under
   `<pack>/.apm/skills/<name>/` projects to
   `<out>/.agents/skills/<name>/` with the same bytes. The full body
   — frontmatter, instructions, scripts, references — reaches Codex
   unchanged.
2. **One-shot migration strip.** On the first install after migration,
   if the projected `AGENTS.md` contains the legacy
   `<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`
   delimiter pair, the adapter strips the entire delimiter region —
   delimiters and any content between them — in place, before doing
   any `direct-directory` projection. A second install finds no
   delimiters and is a no-op. The seed at
   `packs/core/seeds/AGENTS.md` is edited in the same task so
   `make build-self` cannot re-inject the empty block.
3. **Uniform multi-pack entry point.** All three `direct-directory`
   adapters (`codex`, `claude-code`, `kiro`) expose
   `project_packs(pack_paths: list[Path], contract, output_root)` as
   their canonical orchestrator-facing entry point. Codex's existing
   `project_packs` keeps its shape; `claude_code` and `kiro` gain
   thin shims that iterate per-pack `project()` and own the
   multi-pack post-pass (orphan sweep). `self_host.py` and any other
   caller routes through `project_packs` for all three.
4. **Cross-adapter orphan-skill cleanup.** A new shared helper
   sweeps each adapter's projected skill directory
   (`<out>/.agents/skills/`, `<out>/.claude/skills/`,
   `<out>/.kiro/skills/`) after every `project_packs` call, deleting
   any `<name>/` directory not in the union of source skill names
   across the call's pack list. The sweep is bound to the `skill`
   primitive only — other `direct-directory` projections opt in
   explicitly, never automatically.

Same-name collisions across packs resolve **deterministic last-wins**
uniformly across all three adapters: pack source order as supplied to
`project_packs(pack_paths, ...)` by the caller; the last pack's
`<name>` overwrites earlier packs'. The rule is a contract because
all three adapters share the multi-pack entry point after this spec
ships.

Success looks like:

- Two fixture packs declaring a same-named skill, projected through
  any of the three adapters in a known order, produce a projected
  `<name>/SKILL.md` byte-equal to the **last-supplied** pack's
  source. Reversing the order reverses the winner.
- A fixture `AGENTS.md` containing the legacy managed block becomes,
  after one install through Codex, an `AGENTS.md` with no
  delimiters and with all outside-delimiter content preserved
  verbatim. A second install is a no-op.
- After projecting a pack with skills `{a, b, c}` then re-projecting
  with skills `{a, c}` (same `output_root`), `<out>/.agents/skills/b/`,
  `<out>/.claude/skills/b/`, and `<out>/.kiro/skills/b/` are gone.
- `make build-check` exits clean. `dist/codex/.agents/skills/<name>/SKILL.md`
  exists for every skill the core pack ships.

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires
human sign-off before proceeding; *Never do* is a hard rule, even
under time pressure.

### Always do

- **Run the gates** (`make build-check`) before declaring any task
  done. Self-hosted files mean unintended drift between
  `packs/<P>/seeds/` and `<repo>/` shows up here.
- **Use `shutil.copytree(..., symlinks=True)`** for every
  `direct-directory` projection — Codex's new branch and the
  existing Claude Code / Kiro paths. The symlink-pass-through is
  the path-traversal-safety invariant; never resolve a symlink to
  its target at projection time.
- **Edit `packs/core/seeds/AGENTS.md` and the runtime contract
  (`packages/agentbundle/agentbundle/_data/adapter.toml`) in the same
  task as `docs/contracts/adapter.toml`.** All three files reference
  the legacy delimiter pair; drift between them breaks
  `make build-check`.
- **Cite RFC-0009 by section name in the sibling spec amendment.**
  The `distribution-adapters/spec.md` amendment (T8) references
  RFC-0009 § Adapter contract change and § Failure modes so the
  durable rationale stays discoverable.
- **Update this spec when implementation diverges.** The contract
  is here; drift is a bug.

### Ask first

- **Removing `_splice_managed_block` from `codex.py` before the
  next minor release** (target 0.5 per `plan.md` Rollout). RFC-0009
  § Adapter implementation change pins one-minor-release retention.
  Removing the helper earlier changes the migration window for
  adopters mid-upgrade.
- **Changing the same-name collision resolution from
  deterministic last-wins to anything else** (install-time error,
  first-wins, silent overwrite without a pinned rule). The lean is
  recorded in RFC-0009 Unresolved Q2 and committed to in this spec;
  flipping it changes adopter behaviour and the Kiro-agent
  precedent comparison.
- **Touching the Kiro-agent collision precedent at
  `install.py:1201`.** Out of scope for this spec; RFC-0009 § Failure
  modes records "fix Kiro in a follow-on if the reviewer wants
  consistency." Touching it here changes the blast radius.
- **Renaming the shared cleanup helper's public surface** after T6
  ships. Three adapters import it; a rename is a cross-cutting
  change that needs a fresh review.
- **Changing the `project_packs(pack_paths, ...)` signature on any
  adapter** after T5 ships. `self_host.py` and any future
  orchestrator-style caller binds to this shape; an arg-order or
  return-type change is a contract amendment.

### Never do

- **No new top-level dependency.** Stdlib-only Python per the
  existing `agent-spec-cli/spec.md` constraint; the helper is built
  with `shutil` + `pathlib` + `set`.
- **No new top-level directory.** All new code lives under
  `packages/agentbundle/agentbundle/build/`; all new tests under
  `packages/agentbundle/agentbundle/build/tests/`.
- **No new `mode` enum value in the adapter contract.** Codex's
  `skill` entry flips to the existing `direct-directory` mode.
  RFC-0009 § Adapter contract change is explicit on this.
- **No expanding
  `packages/agentbundle/agentbundle/build/projections/direct_directory.py`
  beyond `sweep_orphans` in this spec.** Other helpers wait for a
  second caller or a fresh RFC. The module's surface today is a
  single function.
- **No applying `sweep_orphans` unconditionally to every
  `direct-directory` projection.** Opt-in per primitive; bound to
  `skill` in this PR. If a future primitive wants the sweep, it
  declares the opt-in explicitly.
- **No projection-time symlink dereferencing.** The orphan-cleanup
  sweep removes symlinks via `Path.unlink()` (which removes the
  symlink itself), never via traversal of the link target.
  `shutil.rmtree` is reserved for directories the adapter itself
  just created — never invoked against an entry whose `is_symlink()`
  is true.
- **No restoration of the legacy managed block once stripped.** The
  one-shot strip is destructive by design (RFC-0009 § Failure modes:
  hand-edited content between legacy delimiters is lost). Adopters
  who broke the documented "edit outside the block" rule lose that
  content; adding a `--keep-legacy-codex-block` flag is out of scope
  per RFC-0009 Unresolved Q4 (author's lean: unconditional).
- **No support for both surfaces.** The managed block is gone after
  T4 lands; the adapter does not regenerate it in parallel with
  `.agents/skills/`. RFC-0009 § Migration path rejects the dual-
  surface alternative.
- **No live writes to the developer's home directory from tests or
  CI.** Every test that exercises projection runs against
  `tmp_path`-scoped output roots.

## Testing Strategy

Two verification modes mapped per Objective behaviour:

- **TDD** for every behaviour with a compressible invariant — the
  byte-equal projection, the migration strip (happy path,
  already-clean, idempotent, non-list-content-lost), the symlink
  pass-through invariant, the same-name-collision deterministic
  last-wins rule (all three adapters), the multi-pack
  `project_packs` shims on `claude_code` and `kiro`, and the
  orphan-cleanup sweep (per-adapter for all three). Construction
  tests live in
  `packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py`,
  `test_adapter_claude_code.py`, `test_adapter_kiro.py`, and a new
  `test_direct_directory_cleanup.py` for the shared helper.
- **Goal-based check** for the contract-flip and self-host gates —
  `make build-check` exits clean (drift detection between
  `docs/contracts/adapter.toml`, `_data/adapter.toml`, and the seed
  AGENTS.md); `dist/codex/.agents/skills/<name>/SKILL.md` exists for
  every fixture skill after a self-host build.
- **Visual / manual QA** is **not** used for this spec — no UI, no
  end-to-end UX flow. Every behaviour in the Objective is
  expressible as a contract assertion, a byte-equality check, or a
  self-host build invariant.

**Fixture inputs** the construction tests rely on:

- A **two-skill** fixture pack `fixtures/codex-native/two-skill/`:
  one skill `flat/` with only `SKILL.md`; one skill `nested/` with
  `SKILL.md` + `scripts/run.sh` + `references/notes.md`. Used for
  AC4's byte-equal projection (one flat skill, one with
  subdirectories — covers both file-at-root and file-in-subdir
  cases).
- A **symlinked-body** fixture pack `fixtures/codex-native/symlinked/`:
  one skill `linker/` containing `SKILL.md` plus a relative symlink
  `references/shared.md -> ../assets/shared.md`. Used for AC5.
- A **two-pack same-name** fixture pair
  `fixtures/codex-native/pack-a/` and `pack-b/`, both shipping a
  skill named `same-name` with distinguishable `SKILL.md` body
  text (e.g., `pack-a` body contains `PACK_A_SENTINEL`; `pack-b`
  body contains `PACK_B_SENTINEL`). Used for AC6.
- A **shrink** fixture pair `fixtures/codex-native/three-skill/`
  (skills `{a, b, c}`) and `two-skill-shrink/` (skills `{a, c}`).
  Used for the orphan-sweep ACs (AC15, AC16, AC17) across all
  three adapters.
- Three `AGENTS.md` text fixtures
  (`fixtures/codex-native/agents-md/{populated,clean,hand-edited}.md`)
  for the migration strip: (populated) legacy delimiters + a list
  of `- **<name>** — ...` lines + outside-delimiter prose;
  (clean) no delimiters; (hand-edited) legacy delimiters + a
  recognisable sentinel string between them.

Every Acceptance Criterion maps to at least one construction test.

## Acceptance Criteria

Contract surface:

- [x] **AC1.** `docs/contracts/adapter.toml` and
      `packages/agentbundle/agentbundle/_data/adapter.toml` declare
      the Codex `skill` projection as
      `mode = "direct-directory"`,
      `target-path = ".agents/skills/"`,
      `on-conflict = "prompt-then-preserve"`. The legacy
      `managed-block-delimiter-start` / `-end` keys are removed from
      the Codex `skill` entry only (the contract schema retains the
      keys; they remain valid on entries with `mode = "managed-block-inline"`).
- [x] **AC2.** `docs/contracts/adapter.toml` and
      `packages/agentbundle/agentbundle/_data/adapter.toml` are
      byte-identical after T1 lands (preserves the pre-existing
      invariant; verified `diff -q` exit 0 in the tree as of 2026-05-25).

Adapter behaviour — Codex `direct-directory` projection:

- [x] **AC3.** `codex.project_packs(pack_paths, contract, output_root)`
      dispatches the `skill` primitive through a new
      `direct-directory` branch. Each skill at
      `<pack>/.apm/skills/<name>/` projects to
      `<output_root>/.agents/skills/<name>/`, with every file under
      the skill directory copied through.
- [x] **AC4.** **Byte-equal projection.** For every file in the
      `fixtures/codex-native/two-skill/` fixture (one flat skill,
      one with `scripts/run.sh` and `references/notes.md`
      subdirectories), the projected file at
      `<output_root>/.agents/skills/<name>/<path>` is byte-equal to
      the source. Asserted by `Path.read_bytes()` comparison.
      Non-negotiable per RFC-0009 § Tests.
- [x] **AC5.** **Symlink pass-through.** Against the
      `fixtures/codex-native/symlinked/` fixture, the projected
      `<output_root>/.agents/skills/linker/references/shared.md` is a
      symlink (`os.path.islink(...)` is true) and
      `os.readlink(...)` equals `../assets/shared.md` (the source
      link target string, byte-for-byte). Confirms
      `shutil.copytree(..., symlinks=True)` semantics.
- [x] **AC6.** **Same-name collision — deterministic last-wins,
      uniformly across all three adapters.** For each adapter in
      `{codex, claude-code, kiro}`, when `project_packs([pack_a, pack_b], ...)`
      is called against the same-name fixture pair, the projected
      `same-name/SKILL.md` contains `PACK_B_SENTINEL` (from
      `pack_b`'s body) and **not** `PACK_A_SENTINEL`. The test
      reverses the order (`[pack_b, pack_a]`) and asserts the
      projected file contains `PACK_A_SENTINEL` and not
      `PACK_B_SENTINEL`. One parameterised test per adapter.

Multi-pack adapter entry point:

- [x] **AC7.** `claude_code.project_packs(pack_paths, contract, output_root)`
      and `kiro.project_packs(pack_paths, contract, output_root)`
      exist as canonical multi-pack entry points. Each iterates
      `pack_paths` in order, calling the existing per-pack
      `project(pack_path, contract, output_root)`, then runs the
      post-projection orphan sweep (AC15-AC17).
- [x] **AC8.** `packages/agentbundle/agentbundle/build/self_host.py`
      routes the adapters in its `SELF_HOST_ADAPTERS` allow-list —
      narrowed by this spec at ship time to `("claude-code",)` — through
      `project_packs([pack.path for pack in packs], contract,
      output_root)`. The legacy per-pack loop is removed. **Both
      Codex and Kiro are out of scope for self-host's working-tree
      projection.** Before RFC-0009, Codex was in the allow-list
      because its `managed-block-inline` contribution was a tiny
      AGENTS.md splice; once Codex flipped to `direct-directory`,
      self-host would carry a full duplicate of every skill body
      under `<repo>/.agents/skills/` — maintainer-overload that the
      project rejects on sight. Codex correctness is gated by
      adapter unit tests + the AC29 tempdir projection test rather
      than by self-host's working-tree drift gate; Codex adopters
      get `.agents/skills/` via `agentbundle install` exactly as
      before. `codex.project_packs` and `kiro.project_packs` still
      exist per AC7 and are verified at the unit level (AC6, AC17,
      AC19, AC20). `.agents/` and `.kiro/` are gitignored. Expanding
      `SELF_HOST_ADAPTERS` is a separate decision.
      **Correction 2026-06-10:** that separate decision landed in the
      self-hosting follow-up. Current self-host again includes Codex,
      and `.agents/skills/`, `.codex/agents/`, and `.codex/hooks.json`
      are drift-gated repo projections rather than ignored tempdir-only
      checks. Kiro remains out of scope for self-host.
- [x] **AC9.** `claude_code.project(pack_path, ...)` and
      `kiro.project(pack_path, ...)` are retained as single-pack
      convenience wrappers that delegate to `project_packs([pack_path], ...)`.
      Existing callers continue to work without edits. The known
      in-tree callers as of 2026-05-25 are:
      (a) `packages/agentbundle/agentbundle/build/self_host.py`
      (refactored by AC8); (b)
      `packages/agentbundle/agentbundle/commands/install.py:1114,1116`
      — `kiro.project(pack_dir, contract, out)` and
      `claude_code.project(pack_dir, contract, out)` invoked against
      a tempdir inside `_rewrite_user_scope_hook_paths`; this caller
      stays on the single-pack `project()` wrapper and is not
      refactored by this spec;
      (c) `packages/agentbundle/tests/unit/test_pipeline_phase_order.py`
      lines 168 (`kiro.project(pack, _load_contract(), out)`), 228
      (`kiro.project(pack_kiro, contract, out)`), and 229
      (`claude_code.project(pack_cc, contract, out)`) — unit tests
      that exercise the single-pack signature directly. Retained
      `project()` wrapper behaviour makes them no-op-correct; no
      edits required. Pre-T5 verification is **two `rg` sweeps** (`ripgrep` handles `\b` and alternation uniformly
      across BSD/GNU):
      `rg -n "claude_code\.project\b|kiro\.project\b" packages/ tools/`
      (per-adapter `project` callers) and
      `rg -n "ADAPTERS\[|from agentbundle.build.adapters import ADAPTERS" packages/ tools/`
      (dispatch-table reach-ins). Any caller surfaced by the sweeps
      outside (a) and (b) above is enumerated in the PR description
      with its adaptation plan.

Migration strip — Codex-specific:

- [x] **AC10.** **Strip target is `<output_root>/AGENTS.md`** — the
      project-root AGENTS.md the Codex adapter is invoked against
      (whatever orchestrator runs it). The strip is hardcoded in
      `codex.py` for the migration window; no contract entry, no
      target-path indirection. **Production-coverage gap, named for
      the next maintainer.** No live production call-site in this PR
      exercises the strip against a real legacy `AGENTS.md`. Codex
      is no longer in `SELF_HOST_ADAPTERS` (per AC8), so self-host
      never invokes the Codex adapter. `commands/install.py` does
      not call `codex.project()` either. The strip is therefore
      exercised only by the construction tests in this PR
      (AC11-AC14). When the install flow gains a Codex pathway
      (tracked as a roadmap item against the next minor release),
      the strip will see real adopter `AGENTS.md` files carrying
      the legacy block. Removing the strip before that pathway
      exists would be safe today; keeping it now preserves the
      migration contract without requiring a follow-on PR. The
      retention test (AC23) and integration tests guard against
      silent regression while the live call-site is wired.
- [x] **AC11.** **Happy path.** A fixture `AGENTS.md` containing
      `<!-- agent-skills:start -->\n- **a** — ...\n- **b** — ...\n<!-- agent-skills:end -->\n`
      surrounded by outside-delimiter prose, after one Codex
      `project_packs` call, has: (a) no `<!-- agent-skills:start -->`
      substring; (b) no `<!-- agent-skills:end -->` substring; (c)
      all outside-delimiter prose preserved verbatim, byte-for-byte.
- [x] **AC12.** **Already-clean.** A fixture `AGENTS.md` with no
      delimiters is byte-identical after a Codex `project_packs`
      call — the strip step is a no-op when there is nothing to
      strip. Asserted at both the pure-function and integration
      layers.
- [x] **AC13.** **Idempotent.** Two consecutive `project_packs`
      calls against an `<output_root>` whose `AGENTS.md` originally
      contained the legacy block produce a byte-identical
      `AGENTS.md` after the second call (compared to after the
      first). The second call is a pure no-op on that file.
- [x] **AC14.** **Non-list content between delimiters is lost
      (explicit).** After one `project_packs` call against the
      `hand-edited.md` fixture (which contains a sentinel string
      between the delimiters), the projected `<output_root>/AGENTS.md`
      does not contain the sentinel substring. Asserted at both
      the pure-function and integration layers (the integration
      assertion guards against future refactors moving the strip
      after the skill projection by accident).

Seed cleanup:

- [x] **AC15.** `packs/core/seeds/AGENTS.md` no longer contains
      the `<!-- agent-skills:start -->` or `<!-- agent-skills:end -->`
      literals after T1 lands. `make build-check` clean after the
      seed edit.

Orphan-skill cleanup — shared across `direct-directory` adapters:

- [x] **AC16.** A new module
      `packages/agentbundle/agentbundle/build/projections/direct_directory.py`
      exposes `sweep_orphans(target_dir: Path, expected_names: set[str]) -> None`.
      The function deletes every immediate-child entry of
      `target_dir` whose `name` is not in `expected_names`, with
      one rule: symlinks are removed via `Path.unlink()` (never
      followed); non-symlink directories are removed via
      `shutil.rmtree(<entry>)`; non-directory non-symlink entries
      (regular files at the target-dir root) are not touched. The
      function is a no-op when `target_dir` does not exist.
- [x] **AC17.** **Codex orphan sweep.** A two-stage projection
      against the same `<output_root>`: first
      `codex.project_packs([three-skill])` (skills `{a, b, c}`),
      then `codex.project_packs([two-skill-shrink])` (skills `{a, c}`),
      leaves `<output_root>/.agents/skills/` containing exactly
      `{a, c}`. `b/` is gone.
- [x] **AC18.** **Claude Code orphan sweep.** Same fixture, same
      assertion against `<output_root>/.claude/skills/` via
      `claude_code.project_packs(...)`.
- [x] **AC19.** **Kiro orphan sweep.** Same fixture, same
      assertion against `<output_root>/.kiro/skills/` via
      `kiro.project_packs(...)`.
- [x] **AC20.** **Two-pack union (cross-pack regression guard).**
      For each of the three adapters, a single
      `project_packs([pack_a, pack_b], ...)` call with
      `pack_a.skills = {a, b}` and `pack_b.skills = {b, c}`
      projects exactly `{a, b, c}` (b surviving because the union
      includes it). Then `project_packs([pack_a], ...)` alone
      against the same `output_root` leaves `{a, b}` present
      (b surviving because pack_a still ships it) and removes
      `c`. Guards against per-pack-instead-of-union sweep
      miscalculation.
- [x] **AC21.** **Symlink-safe sweep.** A `target_dir` containing
      a symlink-to-directory named `b -> /tmp/<external>/` with
      `expected_names = {"a"}` removes the symlink (the entry `b`
      under `target_dir`) but leaves `/tmp/<external>/` intact.
      Asserted with `not (target_dir / "b").exists()` after the
      sweep, and `external_path.exists()` still true.

Removed surface and retention:

- [x] **AC22.** `_project_managed_block` (codex.py lines 66-112
      in the pre-change state) is removed in T4;
      `_extract_description` (codex.py lines 115-132 pre-change) is
      removed in T4; `_splice_managed_block` (codex.py lines 135-149
      pre-change) is **retained** as the implementation engine of
      the migration strip until the post-strip release removes it.
- [x] **AC23.** **Retention is defended by a direct test, not a
      tautology.** Two assertions, both in
      `test_adapter_codex.py`:
      (i) `from agentbundle.build.adapters.codex import _splice_managed_block`
      resolves — the symbol exists.
      (ii) Calling `_strip_legacy_skill_block(input)` against
      input containing the legacy delimiter pair invokes
      `_splice_managed_block` exactly once. Implemented with
      `unittest.mock.patch.object(codex, "_splice_managed_block", wraps=codex._splice_managed_block)`
      so the patched callable both records the call and runs the
      real implementation. A future refactor that inlines the
      splice and deletes `_splice_managed_block` breaks
      assertion (i); a refactor that keeps the symbol but stops
      calling it breaks assertion (ii). Either is a real
      retention signal, unlike a same-output-as-implementation
      check which would pass for both correct and incorrect
      removals.
- [x] **AC24.** Five managed-block-specific tests are removed in T4:
      `test_adapter_codex.py::test_skill_description_appears_in_managed_block`,
      `test_outside_block_preserved`, `test_idempotent`,
      `test_project_packs_aggregates_skills_before_splicing`, and
      `test_security.py::test_skill_description_with_end_marker_is_rejected`.
      No analogue post-migration.
- [x] **AC25.** **Retained tests still pass.** Named tests
      (line ranges intentionally omitted — they go stale on
      reformat):
      `tests/unit/test_pipeline_phase_order.py::test_codex_project_iterates_in_phase_order`,
      `tests/unit/test_list_targets_cmd.py` (Codex test cases
      therein), `tests/unit/test_render.py::test_list_adapters_matches_runtime_registry`,
      and `tests/integration/test_zipapp.py` (Codex CLI smoke
      case). Pass unchanged.
- [x] **AC26.** `test_self_host_check.py`'s assertion that
      `<!-- agent-skills:start -->` appears in projected output
      (currently at line 364, pre-change) is flipped to
      `assertNotIn`.

Spec amendment:

- [x] **AC27.** `docs/specs/distribution-adapters/spec.md` is
      amended to reflect: the Codex `skill` projection table entry
      flipped to `direct-directory`; the new uniform multi-pack
      `project_packs` entry point invariant across all three
      `direct-directory` adapters; the new orphan-cleanup invariant
      on `direct-directory` `skill` projections; the
      symlink-pass-through invariant cited explicitly. Amendment
      cites RFC-0009 by section name.

Self-host, linter, and verification:

- [x] **AC28.** `make build-check` exits clean with all changes
      applied — no drift between `packs/<P>/seeds/` and `<repo>/`,
      no drift between contract files, no drift between `dist/` and
      its expected projection.
- [x] **AC29.** `dist/codex/.agents/skills/<name>/SKILL.md` exists
      for every skill the core pack ships. Asserted by a test that
      iterates `packs/core/.apm/skills/*/` and checks each
      projected file exists at the expected `dist/codex/` path.
      Spot-check sentinel: `work-loop`, `new-spec`, `new-rfc`, and
      `new-adr` are explicitly present.
- [x] **AC30.** Changelog entry at `docs/product/changelog.md`
      records RFC-0009's contract change, the migration-strip
      rollout window (released N; strip removed in N+1), and the
      `_splice_managed_block` removal target release.
- [x] **AC31.** `tools/lint-agents-md.py` emits a warning when
      `<!-- agent-skills:start -->` is present in a projected
      `AGENTS.md` whose Codex `skill` projection contract entry
      declares `mode = "direct-directory"`. Linter exit code is
      unchanged (warning, not failure); the warning text names the
      offending file. Verified by a unit test against a synthetic
      fixture.

## Changelog

- 2026-05-31: Status reconciled to Shipped; ACs checked against the
  merged implementation (retroactive — implementation landed in prior
  PRs). All 31 ACs evidenced as satisfied; no deferrals.
