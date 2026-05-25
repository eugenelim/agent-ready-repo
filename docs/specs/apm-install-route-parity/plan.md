# Plan: apm-install-route-parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike
> the spec, this document is allowed to change as you learn. When
> it changes substantially (a different approach, not just a
> re-ordering), note why in the changelog at the bottom.

## Approach

The shape of the change is **template-additive-first,
contract-second, pipeline-third, sibling-spec-fourth,
tests-throughout.** Authoring order:

1. **Land the writer-template additions (T1).** Amend
   `packages/agentbundle/templates/install-marker.py` to add the
   `--install-route` flag (argparse, two-choice
   `{claude-plugins, apm}`, `required=True`, no default), the
   data-directory portability shim
   (precedence: `${CLAUDE_PLUGIN_DATA}` → `${PLUGIN_ROOT}/.data`
   → `${CURSOR_PLUGIN_ROOT}/.data` → exit 0), the APM scope
   detection path (`pathlib.Path(__file__).resolve()` containment
   against cwd / `$HOME`), and the route-flag-driven branch
   selection between the existing `_detect_origin` path (used
   under `--install-route claude-plugins`) and the new
   projected-path mechanism (used under `--install-route apm`).
   Authoring the writer changes first means the build pipeline
   has something concrete to project; the construction tests
   live alongside the template in
   `packages/agentbundle/tests/integration/test_apm_install_route.py`.
2. **Bump the contract (T2).** Edit
   `docs/contracts/adapter.toml` to v0.5 with `"apm"` appended
   to the `install-routes` array on
   `[adapter."claude-code"]`; edit
   `docs/contracts/adapter.schema.json` to accept `"apm"` on
   the enum of `install-routes` items. Schema-level changes are
   small and isolated; landing them now lets every later task
   assert against the schema without re-rebasing.
3. **Extend the marker schema's permitted values (T3).** Amend
   `docs/specs/adapt-to-project/spec.md`
   § *.adapt-install-marker.toml schema* to extend the
   `install-route` field's permitted-values list from
   `{"cli", "claude-plugins"}` to
   `{"cli", "claude-plugins", "apm"}`. Tests pin round-trip
   parsing of a v0.5-shape marker through `tomllib` and through
   the core pack's session-start `_pack_names_from_marker`
   helper.
4. **Wire the APM build derivation (T4).** Amend the build
   pipeline (the same `_run_per_pack`-region in
   `packages/agentbundle/agentbundle/build/main.py` that
   `claude-plugins-install-route` T4 already amended for the
   claude-plugins projection) to additionally:
   (a) project the canonical writer template byte-identically
   into `dist/apm/<pack>/.apm/hooks/install-marker.py`;
   (b) synthesise
   `dist/apm/<pack>/.apm/hooks/install-marker.json` carrying the
   `SessionStart` block with the canonical command `python3
   "${PLUGIN_ROOT}/.apm/hooks/install-marker.py"
   --install-route apm`;
   (c) project `pack.toml` byte-identically (already done by
   `claude-plugins-install-route` T4 for the claude-plugins
   projection; the APM projection mirrors that copy).
   Plus: amend the claude-plugins projection's existing
   `hooks.SessionStart` command-string emission to append
   `--install-route claude-plugins`. Goal-based check: diff the
   produced trees against fixtures.
5. **Author the APM integration tests (T5).** Author
   `packages/agentbundle/tests/integration/test_apm_install_route.py`
   covering the eight RFC-0010 / spec-AC12-named scenarios
   (two first-install, two scope-refusal, one lockfile-replay,
   four per-target characterisation). The tests run the writer
   in subprocess against a fixture-controlled environment
   quintet plus the writer's own projected location.
6. **Amend `adapt-to-project` skill body (T6).** Add the
   `apm_modules/` cache walk to the existing proactive cache-scan
   step (added by `claude-plugins-install-route` T6). Three grep
   tests in
   `packages/agentbundle/tests/skills/test_adapt_skill_body.py`
   pin the new behaviour (per AC13).
7. **Amend `adapt-to-project` spec ACs (T7).** Add AC27
   (APM-route stale-entry drop-on-read). Pin the contract with
   one grep on the SKILL.md body (added in T6) and a Changelog
   line on the parent spec.
8. **Amend `distribution-adapters` spec (T8).** Add the
   APM-route conformance suite reference (one new AC, recipe-row
   extension, two Changelog lines: one for the v0.4 → v0.5
   contract bump, one for the new AC).
9. **Wire the self-host drift gate extensions (T9).** Amend
   `make build-check` (the existing self-host gate from
   `claude-plugins-install-route` T9) to additionally iterate
   the APM-projected writer copies. The vendored
   `_emit_basic_string` parity check is unchanged — it runs once
   per build-check invocation and covers the APM projection
   transitively.
10. **Amend the `claude-plugins-install-route` precedent spec
    (T10).** Update its AC1 import allow-list to include
    `argparse`; update its AC9 hook command literal to include
    `--install-route claude-plugins`; Changelog entry recording
    the in-PR amendment.
11. **Land the manual-QA matrix rows (T11).** Add three rows to
    `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` per
    AC17.
12. **Land the per-pack README disclosure (T12).** Add a
    one-paragraph disclosure to at least `packs/core/README.md`
    naming the four HookIntegrator-covered targets and the three
    no-hook targets with the manual-fallback gesture (per
    AC18).

**Riskiest part: per-target data-directory token-name
uncertainty for Copilot and Gemini.** APM's HookIntegrator
rewrites `${PLUGIN_ROOT}` to per-target tokens
(`${CLAUDE_PLUGIN_ROOT}`, `${CURSOR_PLUGIN_ROOT}`, …), but the
Copilot and Gemini equivalents are not documented at PR time.
The writer's data-directory portability shim (AC3) handles the
three known tokens; if APM ships Copilot and Gemini with new
per-target tokens (e.g. `${COPILOT_PLUGIN_ROOT}`,
`${GEMINI_PLUGIN_ROOT}`), the shim needs a one-line addition
per new token. This is a *contract-shape* risk — the spec
ships AC12 (e) with one mechanically-tested target (Claude
Code) and three deferred to AC17's manual-QA matrix per
Concern 8's resolution. **Secondary risk: T1's
projected-path scope detection.** Symlink resolution on both
sides (`.resolve()` on `__file__` AND on `cwd` / `home`) is
load-bearing — APM caches can be symlinked into the project
tree (e.g. by a developer juggling multiple APM installs);
case (d) is the rail. AC4 case (e) (first-branch-wins
precedence guard: writer under `$HOME` but not cwd, with cwd
nested under `$HOME` → `marker_scope = "user"`) is the
load-bearing precedence case. Construction tests for T1 live
in `packages/agentbundle/tests/integration/test_apm_install_route.py`.

**Why TDD dominates T1, T5, T6, T9.** The writer is a pure
function from environment + disk + own-path +
`${CLAUDE_PLUGIN_ROOT}/pack.toml` (or its APM equivalent) →
marker file state + hash file state + stderr lines + exit
code. Every behaviour in the spec's Acceptance Criteria is
expressible as a single subprocess invocation with a
controlled environment quintet and a controlled projected-path.
The writer ships into adopter caches on every APM install of
every pack — the testing rigor must match the blast radius. T6
(skill body) is TDD-grep-pinned for the same reason
`claude-plugins-install-route` T6 was: there's no programmatic
skill-execution harness in v1. T9 (drift gate) is TDD because
the gate's correctness *is* the rail.

## Constraints

- [RFC-0010](../../rfc/0010-apm-install-route-parity.md) is the
  canonical proposal; this plan is its implementation. Any
  deviation from RFC-0010's *Proposal § Who writes the marker*,
  *§ Scope mapping*, *§ Pack-level declarations*,
  *§ Multi-tool semantics*, *§ Contract impact*,
  *§ Migration path* is a spec amendment, not a plan revision.
- [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
  and [`docs/specs/claude-plugins-install-route/spec.md`](../claude-plugins-install-route/spec.md)
  are the immediate precedent — every Always-do / Never-do
  rail this plan inherits is documented there. Any contradiction
  between this plan and that one is a bug in this plan.
- [`docs/specs/adapt-to-project/spec.md`](../adapt-to-project/spec.md)
  is the install-marker schema authority — schema changes land
  there, not here. This spec amends that spec; it does not
  redefine the schema.
- [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  is the adapter contract authority — contract-shape changes
  land there, not here. This spec amends that spec; it does not
  redefine the contract.
- Stdlib-only Python carries forward from
  `claude-plugins-install-route` / RFC-0008. AC1's import
  allow-list grows by exactly one entry (`argparse`); any other
  addition requires a spec amendment.
- No new top-level directory. The template path
  (`packages/agentbundle/templates/`) is unchanged from
  `claude-plugins-install-route` T1. The integration tests live
  under `packages/agentbundle/tests/integration/`, reusing the
  existing directory. The structural-change trigger does **not**
  fire for this plan — confirmed during PLAN against the four
  conditions in the work-loop skill.

## Construction tests

Per-task tests are under each Task below in `Tests:`
subsections. Cross-cutting tests (here):

**Integration tests:**
- `packages/agentbundle/tests/integration/test_apm_install_route.py`
  — owns the APM-route writer's end-to-end test surface. T5
  ships every test in this file; AC12's explicitly-named tests
  (`test_first_install_end_to_end_core_project_scope`,
  `test_first_install_end_to_end_converters_user_scope`,
  `test_refuse_repo_only_pack_at_user_scope`,
  `test_refuse_user_only_pack_at_project_scope`,
  `test_lockfile_replay_replaces_entry`,
  `test_per_target_characterisation_claude_code`) live here.
  The Copilot / Cursor / Gemini per-target tests are
  **intentionally absent** — their data-directory tokens are
  unconfirmed at PR time; first-firing behaviour ships as
  AC17's manual-QA matrix rows (`verification = transcript`)
  instead. T8's amended sibling spec references this file by
  path for the APM-route conformance suite case list.
- `packages/agentbundle/tests/integration/test_build_derivation_apm.py`
  — owns the build-pipeline APM-derivation diff test (T4 /
  AC11). Mirrors the existing
  `test_build_derivation_claude_plugins.py` from
  `claude-plugins-install-route` T4.

The proactive cache-scan idempotence under the APM extension
(AC13) is grep-pinned in T6, not integration-tested — there is
no programmatic skill-execution harness in v1 (carries forward
from `claude-plugins-install-route` AC25). End-to-end
verification lands as a manual-QA matrix row in T11.

**Manual verification:**
- `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` — the
  three RFC-0010 Q6 / spec-AC17 close-trigger rows land in T11
  (apm install of `core` at project scope; apm install -g of
  `converters` at user scope; APM per-target characterisation
  for Copilot, Cursor, Gemini). All transcripts are deferred
  per the matrix's `verification = transcript` deferral
  pattern.

## Tasks

The work-breakdown. Each task is a verifiable goal; `Tests:`
comes before `Approach:`; every task states `Depends on:`
explicitly.

### T1: Writer template gains `--install-route` flag, data-directory portability shim, and APM scope detection

**Depends on:** none

**Verification mode:** TDD.

**Tests:** (every test in this list belongs in
`packages/agentbundle/tests/integration/test_apm_install_route.py`
and runs the writer in subprocess against a fixture-controlled
environment quintet — `${CLAUDE_PLUGIN_DATA}`, `${PLUGIN_ROOT}`,
`${CURSOR_PLUGIN_ROOT}`, `${HOME}`, plus the writer's own
projected location.)

- `test_writer_imports_argparse_only_added_to_allowlist` (AC1).
  `grep -E '^(import|from) '
  packages/agentbundle/templates/install-marker.py` produces
  exactly the post-edit module set `{argparse, datetime,
  hashlib, json, os, pathlib, re, sys, tempfile, tomllib}`
  (the writer-file ground truth from the spec's AC1, plus
  `argparse`). Any other module — present or absent —
  fails the test. The docstring update naming this spec
  alongside the precedent spec is verified informally by T1
  Approach, not by a separate AC1 test.
- `test_install_route_flag_claude_plugins_records_claude_plugins`
  (AC2 a). Invoke with `--install-route claude-plugins` against
  a claude-plugins-shaped environment; marker entry carries
  `install-route = "claude-plugins"`.
- `test_install_route_flag_apm_records_apm` (AC2 b). Invoke
  with `--install-route apm` against an APM-shaped environment
  (writer projected under cwd; `${PLUGIN_ROOT}` set;
  `${CLAUDE_PLUGIN_DATA}` unset); marker entry carries
  `install-route = "apm"`.
- `test_install_route_flag_invalid_fails_fast` (AC2 c).
  Invoke with `--install-route foo`; writer exits non-zero;
  stderr contains `argparse`'s usage message; no marker write,
  no hash file write.
- `test_install_route_flag_absent_fails_fast` (AC2 d). Invoke
  with no `--install-route` flag at all (e.g. just the writer
  with a claude-plugins-shaped or APM-shaped environment);
  `argparse` exits non-zero with the "the following arguments
  are required: --install-route" message; no marker write, no
  hash file write. This is the rail that catches a build-
  pipeline regression that omits the flag from the projected
  `install-marker.json`'s `command` field.
- `test_data_dir_resolves_claude_plugin_data_when_set` (AC3 a).
  `${CLAUDE_PLUGIN_DATA}=${tmp_path}/data`; resolved hash-file
  path is `${tmp_path}/data/pack-manifest-hash`.
- `test_data_dir_resolves_plugin_root_data_when_only_plugin_root_set`
  (AC3 b). `${PLUGIN_ROOT}=${tmp_path}/plug`,
  `${CLAUDE_PLUGIN_DATA}` unset; resolved hash-file path is
  `${tmp_path}/plug/.data/pack-manifest-hash`.
- `test_data_dir_resolves_cursor_plugin_root_data_when_only_cursor_set`
  (AC3 c). `${CURSOR_PLUGIN_ROOT}=${tmp_path}/curs`,
  others unset; resolved hash-file path is
  `${tmp_path}/curs/.data/pack-manifest-hash`.
- `test_data_dir_unresolvable_exits_zero_no_writes` (AC3 d).
  All four data-dir tokens unset; writer exits 0, no marker
  file on disk, no hash file on disk, no `.data/` directory
  creation. (Empty-string values also unset, sub-asserted by
  setting `PLUGIN_ROOT=""` and checking the same outcome.)
- `test_data_dir_created_when_absent` (AC3 e). `${PLUGIN_ROOT}`
  set to a path whose `.data/` subdirectory does not yet
  exist; after the writer runs, `.data/` exists and contains
  `pack-manifest-hash`. Verifies the
  `mkdir(parents=True, exist_ok=True)` rail.
- `test_data_dir_claude_plugin_data_wins_when_all_set` (AC3 f,
  precedence pin). All three tokens set simultaneously
  (`${CLAUDE_PLUGIN_DATA}=.../cpd`, `${PLUGIN_ROOT}=.../pr`,
  `${CURSOR_PLUGIN_ROOT}=.../cpr`); resolved hash-file path
  must be `.../cpd/pack-manifest-hash`. A reversed-precedence
  bug (e.g. `cpr_data or cpd or pr/.data`) would pass cases
  (a)-(e) but fail this test.
- `test_data_dir_plugin_root_wins_over_cursor_plugin_root` (AC3
  g, precedence pin). `${PLUGIN_ROOT}` and
  `${CURSOR_PLUGIN_ROOT}` both set, `${CLAUDE_PLUGIN_DATA}`
  unset; resolved hash-file path must be `${PLUGIN_ROOT}/.data/pack-manifest-hash`
  (not `${CURSOR_PLUGIN_ROOT}/.data/...`). Closes the second
  adjacent pair of the precedence chain.
- `test_apm_scope_writer_under_cwd_nested_under_home_is_repo`
  (AC4 a, first-branch-wins precedence test). Fixture: `${HOME} =
  ${tmp_path}/home`, cwd set to `${tmp_path}/home/proj`,
  fixture pack at `${tmp_path}/home/proj/apm_modules/<pack>/`;
  writer projected at the fixture path; `marker_scope = "repo"`;
  marker file at
  `${tmp_path}/home/proj/.adapt-install-marker.toml`. The
  nested-home structure pins that a buggy `_apm_detect_scope`
  that checked home before cwd would have silently flipped
  this case to user-scope.
- `test_apm_scope_writer_under_home_is_user` (AC4 b). Fixture
  pack at `${tmp_path}/home/.apm/apm_modules/<pack>/`;
  `${HOME}=${tmp_path}/home`; writer projected at the fixture
  path; `marker_scope = "user"`; marker file at
  `${tmp_path}/home/.agentbundle/.adapt-install-marker.toml`.
- `test_apm_scope_writer_under_neither_exits_zero` (AC4 c).
  Writer projected at a path under neither cwd nor `$HOME`;
  exit 0, no marker write, no hash file write.
- `test_apm_scope_resolves_symlinks_on_both_sides` (AC4 d).
  Writer reached via a symlink (`${tmp_path}/repo/cache-link`
  → `${tmp_path}/repo/apm_modules/<pack>/`); `.resolve()` on
  both sides yields containment; `marker_scope = "repo"`.
- `test_apm_scope_writer_under_home_but_not_cwd_picks_user`
  (AC4 e, home-branch coverage when writer is outside cwd).
  `${HOME}=${tmp_path}/home`, `cwd = ${tmp_path}/home/proj`,
  writer projected at `${tmp_path}/home/.apm/apm_modules/<pack>/`
  (under `$HOME` but **not** under cwd). Expected outcome:
  `marker_scope = "user"`. Coverage rationale: asserts the
  home-detection branch fires when the cwd branch doesn't —
  orthogonal to case (a)'s precedence guard. (Case (a) is
  the precedence test; this case is *not* — both check
  orders yield `"user"` here because cwd-containment fails
  for both.)
- `test_apm_refuse_repo_only_pack_at_user_scope` (AC5 a).
  Writer projected under `$HOME`; pack's `[pack.install]
  allowed-scopes = ["repo"]`; stderr carries the refusal-and-
  warn line with `detected install scope user`; exit 0; no
  marker, no hash file write.
- `test_apm_refuse_user_only_pack_at_project_scope` (AC5 b).
  Writer projected under cwd; pack's `[pack.install]
  allowed-scopes = ["user"]`; stderr carries the refusal-and-
  warn line with `detected install scope repo`; exit 0; no
  marker, no hash file write.
- `test_route_flag_dispatches_claude_plugins_scope_detection`
  (AC6 a). `--install-route claude-plugins` plus a fixture
  with `${CLAUDE_PROJECT_DIR}` set, an `enabledPlugins` file
  declaring the pack, AND writer projected under cwd; the
  resulting marker scope matches the `_detect_origin` /
  `_marker_scope` collapse (not the APM mechanism's output).
- `test_route_flag_dispatches_apm_scope_detection` (AC6 b).
  `--install-route apm` plus a fixture with
  `${CLAUDE_PROJECT_DIR}` set AND an `enabledPlugins` file
  AND writer projected under cwd; the resulting marker scope
  matches the projected-path mechanism's output (not the
  `_detect_origin` path).

**Approach:**

- Amend
  `packages/agentbundle/templates/install-marker.py` `main`
  (currently around lines 634-680 per the existing file)
  to:
  - **Parse `--install-route` first.** Replace direct
    `os.environ.get` reads of `CLAUDE_PLUGIN_ROOT` /
    `CLAUDE_PLUGIN_DATA` with an `argparse` step that consumes
    `argv[1:]`. Parser:
    ```python
    parser = argparse.ArgumentParser(prog="install-marker")
    parser.add_argument(
        "--install-route",
        choices=["claude-plugins", "apm"],
        required=True,
    )
    args = parser.parse_args(argv[1:])
    ```
    The `parse_args` call's failure modes — non-zero exit on
    (a) invalid choice (AC2 c rail) and (b) flag absence
    (AC2 d rail) — are both inherited from `argparse` for free
    by setting `required=True`. No default; `"cli"` is not a
    valid choice (the CLI route uses
    `_append_install_marker` directly).
  - **Branch on `args.install_route`.** Two cases:
    - `"claude-plugins"` → unchanged from today: read
      `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` /
      `HOME` / `CLAUDE_PROJECT_DIR` from env; invoke
      `_detect_origin` / `_marker_scope`. Hard-coded
      `install-route = "claude-plugins"` on the marker entry
      → replaced by `args.install_route` (same value, but
      surfaced through the flag).
    - `"apm"` → new code path. Read `CLAUDE_PLUGIN_ROOT`
      (if set; APM populates it at Claude Code targets),
      `PLUGIN_ROOT` (if set; APM's generic token), and
      `CURSOR_PLUGIN_ROOT` (if set; APM at Cursor target).
      Resolve data directory via `_resolve_data_dir(env)` —
      new helper returning the resolved `pathlib.Path` or
      `None` on no-match (exit 0). Resolve pack root by
      preferring `CLAUDE_PLUGIN_ROOT`, then `PLUGIN_ROOT`,
      then `CURSOR_PLUGIN_ROOT` (same precedence as
      data-dir but without the `.data` suffix — the pack
      root *is* the token's value). Detect scope via
      `_apm_detect_scope(writer_path, cwd, home)` — new
      helper returning `"repo"`, `"user"`, or `None` (exit 0).
      `allowed-scopes` refusal rail and marker write are
      identical to the claude-plugins path past scope
      detection.
- **New helpers landed in the same file** (single source of
  truth; no new module):
  ```python
  def _resolve_data_dir(env: dict[str, str]) -> pathlib.Path | None:
      """Resolve hash-file directory per the AC3 precedence."""
      cpd = env.get("CLAUDE_PLUGIN_DATA", "")
      if cpd:
          return pathlib.Path(cpd)
      pr = env.get("PLUGIN_ROOT", "")
      if pr:
          return pathlib.Path(pr) / ".data"
      cpr = env.get("CURSOR_PLUGIN_ROOT", "")
      if cpr:
          return pathlib.Path(cpr) / ".data"
      return None

  def _apm_detect_scope(
      writer_path: pathlib.Path,
      cwd: pathlib.Path,
      home: pathlib.Path,
  ) -> typing.Literal["repo", "user"] | None:
      """Detect scope by writer's resolved path containment."""
      wp = writer_path.resolve()
      cwd_r = cwd.resolve()
      home_r = home.resolve()
      try:
          if wp.is_relative_to(cwd_r):
              return "repo"
      except ValueError:
          pass
      try:
          if wp.is_relative_to(home_r):
              return "user"
      except ValueError:
          pass
      return None
  ```
  Note: `pathlib.Path.is_relative_to` is stdlib from Python
  3.9; the existing writer already targets Python 3.11+
  (`tomllib` is 3.11). If the writer's claimed Python floor
  is lower somewhere, the implementer uses the `parents`-based
  fallback (`return wp == cwd_r or cwd_r in wp.parents`). Pre-
  EXECUTE the implementer confirms the writer's claimed
  minimum Python version (`grep -n 'python_requires\|requires-python'
  packages/agentbundle/pyproject.toml`); single-line change
  either way.
- **Docstring update.** Add the second spec path to the
  module docstring. Keep the existing "Environment variables
  consumed" enumeration; add a parallel APM block listing
  `PLUGIN_ROOT` and `CURSOR_PLUGIN_ROOT` (optional, APM-route
  only). Add an "`--install-route` flag" section.
- **Build the fixture pack roots inline as `tmp_path`-rooted
  directories** with hand-authored `pack.toml` and
  `enabledPlugins` settings JSONs (the latter only used by
  the `claude-plugins` branch tests). The AC6 branch tests
  set up *both* sets of fixtures to verify the dispatch is
  flag-driven, not env-driven.
- **Each test invokes the writer as**
  `subprocess.run([sys.executable,
  "packages/agentbundle/templates/install-marker.py",
  "--install-route", "apm"], env=..., cwd=...,
  capture_output=True, check=False)` so failures surface the
  writer's own stderr unmodified. Tests that exercise the
  writer's own path (`__file__`) symlink it into the fixture
  pack root via `os.symlink` so `Path(__file__).resolve()`
  yields the fixture-resident path.

**Done when:** every test in this task's `Tests:` list is
green; `grep -E '^(import|from) '
packages/agentbundle/templates/install-marker.py` shows a
module set that is the post-edit allow-list (existing minus
nothing plus `argparse`); the existing
`claude-plugins-install-route` integration tests still pass
unmodified (the writer's claude-plugins code path is
behaviour-preserving past the argparse-prefix).

---

### T2: Contract bump to v0.5 and schema acceptance land in `docs/contracts/`

**Depends on:** none

**Verification mode:** TDD (schema validation) + goal-based
(file content).

**Tests:**
- `test_contract_version_is_v05` (AC9). `tomllib.loads` of
  `docs/contracts/adapter.toml` returns
  `{"contract": {"version": "0.5", ...}}`.
- `test_claude_code_install_routes_includes_apm` (AC9).
  `contract["adapter"]["claude-code"]["install-routes"] ==
  ["cli", "claude-plugins", "apm"]`.
- `test_other_adapters_have_no_install_routes` (AC9). Kiro,
  Copilot, Codex blocks continue not to declare
  `install-routes` (the field is per-adapter optional,
  default `["cli"]`).
- `test_adapter_schema_accepts_apm_enum_value` (AC9). The
  validator (per
  `packages/agentbundle/agentbundle/build/validate.py`)
  accepts the v0.5 contract with `"apm"` on the enum; a
  mutation removing the enum entirely is rejected; a
  mutation with `"foo"` (not in the enum) is rejected.

**Approach:**
- Edit `docs/contracts/adapter.toml`:
  - `[contract] version = "0.4"` → `"0.5"`.
  - Under `[adapter."claude-code"]`, amend the
    `install-routes` array from `["cli", "claude-plugins"]` to
    `["cli", "claude-plugins", "apm"]`. The existing one-line
    `#`-prefixed TOML comment naming RFC-0008 + spec
    `claude-plugins-install-route` gets a second comment
    line naming RFC-0010 + spec `apm-install-route-parity`.
  - Add `RFC-0010 (apm install route, v0.5)` to the header
    comment block enumerating RFC references.
- Edit `docs/contracts/adapter.schema.json` to extend the
  `install-routes` items' enum from
  `["cli", "claude-plugins"]` to
  `["cli", "claude-plugins", "apm"]`. No other schema
  changes (the `not` / `oneOf` discipline pinned by
  `claude-plugins-install-route` T2 still applies — the
  validator only consumes `additionalProperties: false` +
  explicit property lists, which the install-routes shape
  already conforms to via its enum).
- Update existing contract tests in
  `packages/agentbundle/agentbundle/build/tests/test_contract.py`
  for the v0.5 shape; mirror the prior v0.3→v0.4 update.

**Done when:** the four tests are green;
`tomllib.loads(open("docs/contracts/adapter.toml").read())`
returns `version == "0.5"`; the existing test suite under
`packages/agentbundle/agentbundle/build/tests/` is green.

---

### T3: Marker schema permitted-values list gains `"apm"` in `adapt-to-project/spec.md`

**Depends on:** T2 (the contract must accept the value before
the schema documents it as permitted).

**Verification mode:** Goal-based check (schema-block edit) +
TDD (round-trip parse).

**Tests:**
- `test_v05_marker_with_install_route_apm_parses_cleanly`
  (AC10). Pre-seeds a marker file containing
  `name` / `version` / `installed-at` /
  `install-route = "apm"` and verifies:
  (a) `tomllib` parses it cleanly;
  (b) the existing `_pack_names_from_marker` helper in
  `packs/core/.apm/hooks/session-start.py` returns the pack
  name unchanged.
- `test_v05_marker_three_route_values_all_parse` (AC10).
  Pre-seeds three markers in one file —
  `install-route = "cli"`, `"claude-plugins"`, `"apm"` —
  and asserts all three entries' pack names surface through
  `_pack_names_from_marker`.
- `test_v03_shaped_marker_without_install_route_field_parses_as_cli`
  (AC10, v0.3 back-compat rail). Pre-seeds a marker with
  `name` / `version` / `installed-at` only — no
  `install-route` field — and verifies: (a) `tomllib` parses
  it cleanly; (b) `_pack_names_from_marker` returns the pack
  name unchanged; (c) any reader that consults
  `install-route` treats absence as `"cli"` per
  `claude-plugins-install-route` AC12's back-compat rail.

**Approach:**
- Amend
  `docs/specs/adapt-to-project/spec.md`
  § *.adapt-install-marker.toml schema* (the schema block
  amended by `claude-plugins-install-route` T3) to extend the
  `install-route` field's permitted-values enumeration from
  `"cli" | "claude-plugins"` to
  `"cli" | "claude-plugins" | "apm"`. Documentation of the
  read-side default (`"cli"` when absent) stays unchanged.
- Add a Changelog entry on the parent spec:
  `- 2026-05-25: install-route permitted-values extended to
  include "apm" per docs/specs/apm-install-route-parity/spec.md.`

**Done when:** the two tests are green; the
`adapt-to-project` spec carries the amended permitted-values
list and the Changelog line.

---

### T4: Build pipeline derives APM artifacts; claude-plugins hook command bumps to pass the flag

**Depends on:** T1 (template's argparse must accept the flag
before the pipeline emits it), T2 (adapter contract must accept
the new enum value), T3 (marker schema's permitted-values list
must admit `"apm"` before any pack emits a marker carrying it
— soft dependency at runtime but a documentation rail this PR's
spec graph requires).

**Verification mode:** Goal-based check.

**Tests:** (every test in this list belongs in
`packages/agentbundle/tests/integration/test_build_derivation_apm.py`.)

- `test_apm_derivation_projects_install_marker_py` (AC11 b).
  Diff `dist/apm/<pack>/.apm/hooks/install-marker.py`
  against
  `packages/agentbundle/templates/install-marker.py`
  byte-for-byte; identical.
- `test_apm_derivation_projects_pack_toml` (AC11 c). Diff
  `dist/apm/<pack>/pack.toml` against
  `packs/<pack>/pack.toml` byte-for-byte; identical.
- `test_apm_derivation_synthesises_install_marker_json` (AC7
  + AC11 a). The derived JSON loads cleanly and contains the
  exact shape from AC7 (one `SessionStart` entry, one
  inner-hook entry with `type = "command"`, `command =
  "python3 \"${PLUGIN_ROOT}/.apm/hooks/install-marker.py\"
  --install-route apm"`, `timeout = 10`).
- `test_apm_derivation_hook_command_shlex_quoting` (AC7
  sub-assertion). Substituting a synthetic `PLUGIN_ROOT`
  containing a space (`/tmp/with space/root`) into the
  command string and `shlex.split`-ing it yields exactly
  `["python3", "/tmp/with space/root/.apm/hooks/install-marker.py",
  "--install-route", "apm"]`.
- `test_claude_plugins_hook_command_now_passes_flag` (AC8).
  After T4 runs `make build`, the derived
  `dist/claude-plugins/<pack>/.claude-plugin/plugin.json`'s
  `hooks.SessionStart[0].hooks[0].command` equals (when
  read out of JSON) `python3
  "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"
  --install-route claude-plugins`. The existing fixture
  diff updates to match. **This test belongs in
  `packages/agentbundle/tests/integration/test_build_derivation_claude_plugins.py`**
  (the precedent-spec's existing test home — asserting on a
  claude-plugins-side projection), *not* in
  `test_build_derivation_apm.py`. T4's plan-test list
  references it from the APM plan for traceability against
  AC8 only; the test code lives in the claude-plugins file.
- `test_make_build_check_passes_post_migration` (AC11 +
  AC16 a). `make build-check` exits zero after T4 lands.
- `test_apm_derivation_idempotent` — `make build` twice in
  a row produces byte-identical output at the APM
  projection.

**Approach:**
- **Reuse the `_read_bundled`-shaped helper** from
  `claude-plugins-install-route` T4 — the same canonical-
  source-path resolver
  (`importlib.resources.files("agentbundle").joinpath("_data/install-marker.py")`
  with filesystem fallback) covers both the claude-plugins
  and APM projections. If the existing helper is named
  differently or lives at a slightly different path,
  pre-EXECUTE the implementer reads
  `packages/agentbundle/agentbundle/build/main.py:53-70`
  region to confirm. The `_data/` copy is synced from the
  `templates/` copy by the existing `make build-self` /
  `make build-check` self-host machinery — already in
  place from the claude-plugins work.
- Amend
  `packages/agentbundle/agentbundle/build/main.py`
  `_run_per_pack` (region amended by
  `claude-plugins-install-route` T4) to, after the existing
  claude-plugins derivation block:
  - **APM derivation block.** For each pack, into
    `per_pack_output_apm = dist/apm/<pack>/`:
    - `mkdir -p .apm/hooks/`;
    - copy `pack.toml` from `pack.path / "pack.toml"`
      (already copied for claude-plugins; reuse the same
      bytes — read once, write twice);
    - copy the writer template via the same `_read_bundled`
      helper to `.apm/hooks/install-marker.py`;
    - synthesise `.apm/hooks/install-marker.json` from a
      Python dict literal serialised with `json.dumps(...,
      indent=2)` + trailing newline; the `command` string
      is a literal Python string (no f-string substitution
      against an environment — the `${PLUGIN_ROOT}` token
      is APM's, evaluated at runtime, not Python's at build
      time).
  - **Claude-plugins hook command bump.** In the existing
    claude-plugins synthesis block, change the `command`
    string from
    `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py"`
    to
    `python3 "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py" --install-route claude-plugins`.
    The existing fixture under
    `packages/agentbundle/agentbundle/build/tests/fixtures/derived/<pack>/`
    is regenerated to match.
- Add a fixture under
  `packages/agentbundle/agentbundle/build/tests/fixtures/derived-apm/<pack>/`
  capturing the expected APM-derived shape for the
  first-consumer pack (`core`); the diff test compares
  against it.

**Done when:** the six tests in this task's `Tests:` list
are green; `make build && diff -r
dist/apm/core/.apm/hooks/install-marker.py
packages/agentbundle/templates/install-marker.py` shows zero
diff; `make build-check` exits zero.

---

### T5: APM-route integration tests cover the five RFC-0010-named scenarios (six tests; scope-refusal scenario gets two tests, one per direction)

**Depends on:** T1 (writer's APM code path must already
exist), T4 (build pipeline must already produce the
projected artifacts for the per-target characterisation
tests).

**Verification mode:** TDD.

**Tests:** (live in
`packages/agentbundle/tests/integration/test_apm_install_route.py`,
co-resident with the T1 tests. **The T1 tests are unit-shaped
against the writer's individual rails** (one rail per test —
scope detection, data-dir resolution, refusal); **the T5 tests
are full-pack-staging end-to-end shapes** that exercise the
writer against a realistic `apm_modules/`-shaped fixture
layout, with the full pack metadata round-tripping through
`tomllib`. T1 catches a rail-level regression; T5 catches an
integration-level regression where the rails interact (e.g.
a fixture-pack `pack.toml` whose `[pack.install]`
`allowed-scopes` reads correctly through one route but
silently bypasses validation through another). The two
layers do not duplicate assertions; they assert *different*
things against the same code path.)

- `test_first_install_end_to_end_core_project_scope` (AC12
  a). Simulate an `apm install agent-ready-repo/core` at
  project scope: stage the projected pack at
  `${tmp_path}/repo/apm_modules/core/`; invoke the writer
  with `--install-route apm`, cwd set to
  `${tmp_path}/repo`, `${PLUGIN_ROOT}=${tmp_path}/repo/apm_modules/core`;
  assert the marker file at
  `${tmp_path}/repo/.adapt-install-marker.toml` contains a
  `[[packs-installed]]` entry with `name = "core"`,
  `install-route = "apm"`, and a well-formed
  `installed-at` (round-trips as `datetime.datetime` under
  `tomllib`).
- `test_first_install_end_to_end_converters_user_scope`
  (AC12 b). Simulate an `apm install -g
  agent-ready-repo/converters`: stage at
  `${tmp_path}/home/.apm/apm_modules/converters/`;
  `${HOME}=${tmp_path}/home`; assert marker at
  `${tmp_path}/home/.agentbundle/.adapt-install-marker.toml`
  with `install-route = "apm"`.
- `test_refuse_repo_only_pack_at_user_scope` (AC12 c +
  AC5 a). (Some overlap with T1's
  `test_apm_refuse_repo_only_pack_at_user_scope`; this
  end-to-end test stages a realistic apm_modules/ layout
  under `$HOME` and asserts the no-marker / no-hash
  outcome.)
- `test_refuse_user_only_pack_at_project_scope` (AC12 c +
  AC5 b). End-to-end mirror of T1's project-scope refusal
  case.
- `test_lockfile_replay_replaces_entry` (AC12 d). Pre-seed
  the target marker file with an entry for
  `name = "core"`, `version = "0.1.0"`, `install-route =
  "apm"`; stage a pack root whose `pack.toml` declares
  version `0.2.0`; run the writer with `--install-route apm`;
  assert the resulting marker file has exactly one entry
  for `name = "core"` with `version = "0.2.0"`. Mirrors
  `claude-plugins-install-route` AC8's plugin-upgrade
  replace semantics; RFC-0010 §Unresolved questions Q4
  inherits the replace lean from RFC-0008 Q3.
- `test_per_target_characterisation_claude_code` (AC12 e,
  AC4 b mirror). Writer projected under
  `${tmp_path}/.../claude_code_cache/.../apm_modules/<pack>/`
  with `${CLAUDE_PLUGIN_ROOT}` set (APM's Claude-Code
  target rewrites `${PLUGIN_ROOT}` to this); marker write
  succeeds. **Copilot / Cursor / Gemini per-target tests
  are intentionally absent** — their data-directory tokens
  are unconfirmed at PR time and a skipped-in-CI test is not
  honest coverage per Concern 8 of the review. Their
  first-firing behaviour is captured by AC17's manual-QA
  matrix row (`verification = transcript`), gated on
  adopter-availability rather than this PR.

**Approach:**
- Reuse the `pack_root_factory` fixture pattern from
  `claude-plugins-install-route` T1 — staging directories
  with hand-authored `pack.toml`, `pack.toml`'s
  `[pack.install] allowed-scopes`, and the writer copy
  in place. The APM mock is just *"project the writer
  template into the fixture and set the right env
  tokens"*.
- Each test runs the writer as `subprocess.run([
  sys.executable,
  "<projected-writer-path>", "--install-route", "apm"],
  env=..., cwd=..., capture_output=True, check=False)`.
  The projected writer path is the symlink/copy under the
  fixture pack root, not the source template — this
  exercises the `pathlib.Path(__file__).resolve()`
  scope-detection rail.
- Per-target tests stage the writer under a fixture path
  resembling the target's APM cache layout (per APM's
  reference docs at install time). When the target's
  exact cache path shape is documented (e.g. Cursor uses
  `~/.cursor/extensions/.../`), the fixture matches; when
  not, the fixture uses a synthetic layout and the test
  documents the assumption in a `# Note:` comment so
  RFC-0010 §Drawbacks's characterisation follow-up can
  refine.

**Done when:** every test in this task's `Tests:` list is
green or explicitly skipped with a documented reason; the
five RFC-0010-named scenarios (per AC12) have at least one
green test each.

---

### T6: `adapt-to-project` skill body extends proactive cache scan to walk `apm_modules/`

**Depends on:** T3 (the marker-schema permitted-values
extension must be documented before the skill body cites
the new route).

**Verification mode:** TDD (grep-pinned).

**Tests:** (live in
`packages/agentbundle/tests/skills/test_adapt_skill_body.py`,
the existing skill-body test home from
`claude-plugins-install-route` T6.)

- `test_skill_body_names_apm_cache_scan_heading` (AC13
  grep #3). Asserts the literal phrase `APM cache scan`
  appears verbatim (case- and punctuation-sensitive).
- `test_skill_body_names_apm_project_cache_path` (AC13
  grep #1). Asserts `./apm_modules/` appears verbatim.
- `test_skill_body_names_apm_user_cache_path` (AC13
  grep #2). Asserts `~/.apm/apm_modules/` appears verbatim.
- `test_skill_body_preserves_idempotence_clause` —
  regression guard from
  `claude-plugins-install-route` AC15 grep #4. Asserts the
  literal phrase `if a marker entry is present, do not
  synthesise a second adaptation` still appears (the
  proactive cache-scan branch's dedupe rule covers BOTH
  the claude-plugins and APM caches; this regression
  guard pins that the T6 edit did not drop it).
- `test_skill_body_apm_stale_entry_drop_grep` (AC14 / AC27
  grep). Asserts the literal phrase
  `apm_modules` appears within the stale-entry-drop
  paragraph (the existing stale-entry-drop body, edited by
  T7, gains an APM-specific clause that the SKILL.md
  grep-pins).

**Approach:**
- Amend
  `packs/core/.apm/skills/adapt-to-project/SKILL.md`
  Pre-flight section's proactive-cache-scan step (added
  by `claude-plugins-install-route` T6 around the
  numbered-list region) to extend the scanned cache
  directories. Wording must carry the three grep-pinned
  literals verbatim — *don't paraphrase any of them*:
  > **APM cache scan.** In addition to the Claude-plugins
  > cache walk above, scan `./apm_modules/` (project scope)
  > and `~/.apm/apm_modules/` (user scope) for pack roots
  > — directories containing both `pack.toml` and an
  > `.apm/hooks/install-marker.py` projection. For each
  > cache-resident pack with **no** `[[packs-installed]]`
  > entry at either scope's marker file naming that pack,
  > treat the pack as a fresh install: prepend a synthetic
  > install-marker entry to the session-internal proposal
  > queue (with `install-route = "apm"`) and run
  > class-1/2/3/4 inline. The idempotence rule from the
  > Claude-plugins scan applies unchanged — *if a marker
  > entry is present, do not synthesise a second
  > adaptation*. This closes the active case of
  > [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
  > for adopters whose APM-routed install of a Claude
  > Code target hit the first-session quirk.
- T7 adds the APM-specific clause to the stale-entry-drop
  paragraph (already present from
  `claude-plugins-install-route` T6); T6 leaves the
  stale-entry-drop wording in place but adds an APM
  bullet under it pointing at the `apm_modules/` cache
  directories.

**Done when:** the five tests in T6's `Tests:` list are
green; the
`claude-plugins-install-route` skill-body grep tests
(AC15 greps #1–#4 per that spec) continue to pass
(regression guard — the T6 edit must not drop the
Claude-plugins cache literals).

---

### T7: `adapt-to-project` spec gains AC27 (APM-route stale-entry drop-on-read)

**Depends on:** T6 (the skill body must carry the APM
cache walk before the AC pins it as a contract surface).

**Verification mode:** Goal-based check (literal AC header
present; Changelog line present). The behaviour itself is
pinned by T6's grep set, T3's marker-schema tests, and the
manual-QA matrix row from T11.

**Tests:**
- `test_adapt_spec_has_ac27_apm_stale_entry_drop` (AC14).
  `grep -E '^- \[ \] \*\*AC27' docs/specs/adapt-to-project/spec.md`
  returns one match.
- `test_adapt_spec_changelog_names_this_spec` (AC14).
  `docs/specs/adapt-to-project/spec.md` Changelog
  contains a dated entry whose body includes the literal
  path `docs/specs/apm-install-route-parity/spec.md`.

**Approach:**
- Amend `docs/specs/adapt-to-project/spec.md` Acceptance
  Criteria section to add AC27 at the end (numbered to
  extend the existing AC26 from
  `claude-plugins-install-route`). The full text is in
  this spec's AC14 — copy verbatim into the parent spec.
- Add a Changelog line referencing this spec by path:
  `- 2026-05-25: AC27 added per docs/specs/apm-install-route-parity/spec.md — stale-entry drop-on-read for install-route = "apm" entries.`
- Add an APM-specific clause to the existing
  stale-entry-drop SKILL.md paragraph (added by
  `claude-plugins-install-route` T6) so AC14's grep on
  `apm_modules` (T6 `test_skill_body_apm_stale_entry_drop_grep`)
  passes.

**Done when:** the two tests are green; the parent
`adapt-to-project` spec has AC27 and the Changelog line;
the SKILL.md stale-entry-drop paragraph names
`apm_modules/`.

---

### T8: `distribution-adapters` spec amendment — APM-route conformance suite reference, recipe-row extension, two Changelog lines

**Depends on:** T2 (the contract version must already be
v0.5).

**Verification mode:** Goal-based check.

**Tests:**
- `test_distribution_adapters_changelog_names_this_spec`
  (AC15). `docs/specs/distribution-adapters/spec.md`
  Changelog contains `apm-install-route-parity` by path.
- `test_distribution_adapters_changelog_names_v05_bump`
  (AC15). Changelog contains a dated entry naming the
  v0.4 → v0.5 contract bump.
- `test_distribution_adapters_has_apm_conformance_ac`
  (AC15). `grep -c 'apm-route conformance'` (or whatever
  exact phrase the new AC uses; pre-EXECUTE the implementer
  picks the canonical phrasing and updates this test's
  literal) returns ≥ 1.
- `test_distribution_adapters_names_apm_test_file_by_path`
  (AC15). `grep -c 'packages/agentbundle/tests/integration/test_apm_install_route.py'
  docs/specs/distribution-adapters/spec.md` returns ≥ 1.
  Closes the iteration-3 cross-spec path-reference gap —
  the sibling spec must actually carry the literal path,
  not just a paraphrase.

**Approach:**
- Append one new AC to
  `docs/specs/distribution-adapters/spec.md` Acceptance
  Criteria section:
  - **AC<N+1> (APM-route conformance cases; per-target
    coverage matrix).** The adapter contract
    (`docs/contracts/adapter.toml`) declares `"apm"` on
    `[adapter."claude-code"].install-routes` per RFC-0010 /
    spec `apm-install-route-parity`. The conformance suite
    ships a *marker presence* and a *scope refusal* case
    for the APM route alongside the existing claude-plugins
    cases; the per-route fixtures live in
    `packages/agentbundle/tests/integration/test_apm_install_route.py`.
    The APM *marker presence* case is asserted on
    session 2 or later at Claude Code targets (per the
    `#10997` caveat); at other HookIntegrator-covered
    targets (Copilot, Cursor, Gemini), the per-target
    first-session behaviour is recorded by the
    characterisation tests in `test_apm_install_route.py`.
    The conformance suite enumerates the four covered
    HookIntegrator targets and the three uncovered ones
    (Codex, OpenCode, Windsurf), with the
    `agentbundle adapt --scope <project|user>` manual-
    fallback gesture documented per uncovered target.
- Extend or annotate the `per-pack-apm-package` row in
  the § *Recipe set* table to name the install-marker
  artifact derivation alongside the existing recipe
  output. The row already cites
  `dist/apm/<pack>/`; add a one-line note pointing at
  `.apm/hooks/install-marker.{json,py}` and this spec by
  path.
- Add two Changelog lines:
  - `- 2026-05-25: contract bumps v0.4 → v0.5 per docs/specs/apm-install-route-parity/spec.md — "apm" appended to install-routes on [adapter."claude-code"].`
  - `- 2026-05-25: APM-route conformance AC added per docs/specs/apm-install-route-parity/spec.md — conformance suite ships marker-presence and scope-refusal cases for the APM route; four-of-seven HookIntegrator coverage documented.`

**Done when:** the three tests are green.

---

### T9: `make build-check` drift gate covers the APM-projected writer

**Depends on:** T4 (the APM derivation must already be
producing the projected writer).

**Verification mode:** TDD.

**Tests:**
- `test_make_build_check_fails_on_apm_writer_drift` (AC16
  a). Mutate one byte in a derived
  `dist/apm/<pack>/.apm/hooks/install-marker.py` copy in
  a `tmp_path`-rooted shadow tree; run the drift check
  against it; assert non-zero exit and stderr naming the
  diverged pack and path.
- `test_make_build_check_passes_on_clean_apm_tree` (AC16
  a). Run the drift check against the actual `dist/apm/`
  tree after `make build`; assert exit zero.
- `test_make_build_check_emit_basic_string_parity_unchanged`
  (AC16 b regression guard). The vendored
  `_emit_basic_string` parity check from
  `claude-plugins-install-route` AC20 (b) continues to
  pass against the unmodified template; the check runs
  once per build-check invocation regardless of route.
  (No new corpus extension; this test pins that T9 did
  not accidentally break the existing check.)

**Approach:**
- `make build-check` invokes
  `python3 -m agentbundle.build check` (per the existing
  Makefile target from
  `claude-plugins-install-route` T9). The check logic
  lives in
  `packages/agentbundle/agentbundle/build/self_host.py`'s
  `check`-mode entrypoint (pre-EXECUTE the implementer
  confirms the symbol per the
  `claude-plugins-install-route` T9 Approach pattern). T9
  amends that entrypoint with one new mechanical
  assertion:
  - **APM writer-template drift**: for every
    `dist/apm/<pack>/.apm/hooks/install-marker.py`
    produced by `make build`, assert
    `hashlib.sha256(open(path, 'rb').read()).hexdigest()`
    equals
    `hashlib.sha256(open(packages/agentbundle/templates/install-marker.py, 'rb').read()).hexdigest()`.
    Drift fails the check with a one-line stderr naming
    the diverged pack and path.
- The existing claude-plugins drift check
  (`dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
  byte-identity with the template) continues to bind; T9
  adds the APM analogue. The vendored
  `_emit_basic_string` parity check runs once and
  continues to apply.

**Done when:** the three tests in this task's Tests list
are green; `make build-check` against the post-migration
tree exits zero; the red-team byte-mutation fixture
causes `make build-check` to exit non-zero with the
matching stderr.

---

### T10: Precedent spec amendments — `claude-plugins-install-route` AC1 / AC9 updates and Changelog entry

**Depends on:** T1 (the import allow-list growth must be
in place before the precedent spec records it).

**Verification mode:** Goal-based check.

**Tests:**
- `test_precedent_spec_ac1_allowlist_includes_argparse` —
  grep `claude-plugins-install-route/spec.md` for `argparse`
  in the AC1 allow-list region; one match.
- `test_precedent_spec_ac9_hook_command_includes_flag` —
  grep `claude-plugins-install-route/spec.md` AC9 region
  for `--install-route claude-plugins`; one match.
- `test_precedent_spec_ac9_shlex_token_list_includes_flag` —
  grep `claude-plugins-install-route/spec.md` AC9's
  `shlex.split` expected-token-list region for the literal
  substring `"--install-route", "claude-plugins"` (the two
  new tokens at the tail of the expected token list); one
  match. The precedent AC9 was written against the v0.4
  literal and its `shlex.split` expected list ended at
  `install-marker.py"]`; this test pins that T10's amend
  extends the expected list, not just the command-string
  literal.
- `test_precedent_spec_changelog_names_this_spec` — grep
  `claude-plugins-install-route/spec.md` Changelog for
  literal path `docs/specs/apm-install-route-parity/spec.md`;
  one match.

**Approach:**
- Amend `docs/specs/claude-plugins-install-route/spec.md`:
  - AC1: extend the allow-list enumeration to include
    `argparse` (one entry added). The AC's text already
    says "any addition requires spec amendment" — this
    PR *is* the amendment.
  - AC9: extend the literal hook-command string to
    include `--install-route claude-plugins` at the end.
    The existing `shlex.split` sub-assertion's expected
    token list grows by `["--install-route", "claude-plugins"]`.
  - Changelog: add a dated entry naming this spec by
    path: `- 2026-05-25: AC1 allow-list extended to admit
    argparse; AC9 hook command extended with --install-route
    claude-plugins. Both per docs/specs/apm-install-route-parity/spec.md.`

**Done when:** the three tests are green.

---

### T11: Manual-QA matrix gains three RFC-0010-driven rows

**Depends on:** T4 (the APM-derivation rows describe artifacts
T4 produces) and T6 (the proactive-cache-scan idempotence row
describes the skill behaviour T6 lands). T1 is a soft semantic
dependency — the manual-QA matrix row text describes live-install
behaviour that T1's unit tests model — but there is no hard
ordering edge. T2, T3, T5, T7, T8, T9, T10, T12 have no
dependency relationship to T11's row text.

**Verification mode:** Goal-based check (the row shape; the
transcripts themselves are deferred).

**Tests:**
- `test_manual_qa_matrix_has_apm_core_row` (AC17 a).
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
  contains a row naming `apm install of core at project
  scope`.
- `test_manual_qa_matrix_has_apm_converters_row` (AC17 b).
  Same file contains a row naming `apm install -g of
  converters at user scope`.
- `test_manual_qa_matrix_has_apm_per_target_row` (AC17 c).
  Same file contains a row naming `APM per-target
  characterisation`.
- `test_manual_qa_matrix_apm_rows_carry_verification_transcript`
  (AC17). All three new rows declare
  `verification = transcript`.

**Approach:**
- Append the three rows to
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
  per its existing row shape. Rows (a) and (b) name
  RFC-0010 Q6 as the close-trigger; row (c) names
  RFC-0010 §Drawbacks *APM-target hook-firing matrix
  uncharacterised* as the trigger and the matrix's first
  three transcripts (one per Copilot / Cursor / Gemini
  target) as the close criterion.

**Done when:** the four tests are green.

---

### T12: Per-pack README disclosure for the four-of-seven HookIntegrator coverage

**Depends on:** T4 (the APM derivation produces the
artifacts the README describes).

**Verification mode:** Goal-based check.

**Tests:**
- `test_core_readme_discloses_apm_manual_fallback` (AC18).
  `packs/core/README.md` (if present) or
  `packs/core/.apm/README.md` (if used in lieu) contains
  the literal phrase `agentbundle adapt --scope`.
- `test_core_readme_names_four_covered_targets` (AC18).
  Same file contains the literal phrases `Claude Code`,
  `Copilot`, `Cursor`, `Gemini` within the APM disclosure
  paragraph.
- `test_core_readme_names_three_uncovered_targets` (AC18).
  Same file contains the literal phrases `Codex`,
  `OpenCode`, `Windsurf` within the same paragraph.

**Approach:**
- Add one paragraph to `packs/core/README.md` (or create
  the file if absent) under a heading like
  *Install routes and adaptation*. The paragraph names
  the four HookIntegrator-covered targets where the
  install→adapt chain fires automatically and the three
  uncovered targets where the adopter runs
  `agentbundle adapt --scope <project|user>` once after
  install. The phrasing mirrors RFC-0008's
  claude-plugins README disclosure pattern (RFC-0008
  §Drawbacks *Writer ships executable Python*).
- Other packs (`converters`, plus any future pack) get
  the same disclosure in a follow-up PR — implementer's
  judgement, not gated by this task. The floor is
  `packs/core/README.md` because `core` is the
  first-consumer pack per RFC-0010 Q6.

**Done when:** the three tests are green.

---

## Rollout

The change ships in a single PR per RFC-0010. The PR's
`installed:` rail is the existing `make build && make
build-check` + the new integration tests under
`packages/agentbundle/tests/integration/`. Adopters consume
the change via:

- **APM-route adopters.** The next `apm install` of any
  pack from this catalogue (per `apm.yml`) into a
  HookIntegrator-covered target (Claude Code, Copilot,
  Cursor, Gemini) includes the derived
  `.apm/hooks/install-marker.{json,py}`; the
  `SessionStart` hook fires on session 2 at Claude Code
  targets (per the `#10997` caveat; first-session
  behaviour at the other three targets is characterised
  per AC12 (e) and the manual-QA matrix). Codex,
  OpenCode, and Windsurf adopters run the manual
  `agentbundle adapt --scope <project|user>` gesture per
  the README disclosure (T12).
- **Claude-plugins-route adopters.** Existing markers
  written before this PR remain valid (read-side back-compat
  per `claude-plugins-install-route` AC12 — absent
  `install-route` is treated as `"cli"`). On the write side,
  the writer template and the projected `install-marker.json`
  command are coupled by `make build`: a refreshed writer
  always ships next to a refreshed command. The
  `--install-route` flag is `required=True`; an adopter whose
  cache somehow holds a refreshed writer with a stale command
  line gets a fast-failing `argparse` error on the next
  `SessionStart` rather than a silent mis-route — that's the
  chosen failure mode, not a regression.
- **CLI-route adopters.** No behaviour change beyond the
  v0.5 contract version bump (existing CLI markers
  continue to carry `install-route = "cli"` per
  `claude-plugins-install-route` AC13).
- **Self-hosting adopters.** `make build-check` is a CI
  gate; the post-migration tree passes the gate on first
  commit (T9's drift check + T4's idempotence test).

Reversibility: every code change is contained to
`packages/agentbundle/`, `docs/contracts/`, `docs/specs/`,
`packs/core/.apm/skills/adapt-to-project/SKILL.md`, and
`packs/core/README.md`. Reverting the PR restores the v0.4
contract version, the prior `plugin.json` projection (without
the `--install-route claude-plugins` flag), the prior writer
template (without `argparse`), the prior skill body, and the
prior README. Because the writer template and the projected
`install-marker.json` command are coupled at projection time
by `make build`, the revert restores both in lockstep — no
mismatched state between cached writer and cached command. The marker
schema gains one permitted-values entry (`"apm"`) —
reverting drops the entry's acceptability but does not
corrupt existing markers (`install-route = "apm"` markers
written before the revert would parse as unknown strings;
the reader's contract is `claude-plugins-install-route`
AC12 which treats absence as `"cli"` — explicit `"apm"`
values would not be silently dropped, just unrecognised).

## Risks

- **APM lands install-time lifecycle hooks while this PR
  is in review.** Migration is mechanical: drop the
  `SessionStart` entry from the derived
  `install-marker.json`, replace with whatever upstream
  hook shape APM publishes, drop the data-directory
  resolution shim from the writer (a `postInstall`-shaped
  hook gets the env from APM at install time, not from a
  target tool's session). The conformance suite case for
  *marker presence* stays unchanged; the *session 2 or
  later* caveat on the Claude Code target disappears.
  Reopen RFC-0010 for that amendment.
- **APM upstream changes `apm_modules/` cache layout.** The
  proactive cache-scan branch (T6) walks `./apm_modules/`
  and `~/.apm/apm_modules/`. If APM relocates the cache
  (e.g. `apm_packages/` or a hash-prefixed layout), the
  skill body's grep-pinned literals (AC13) need updating
  in lockstep. Mitigation: the literals are pinned to a
  versioned APM directory layout per
  [APM's `apm install` reference](https://microsoft.github.io/apm/reference/cli/install/);
  any future relocation would be a documented breaking
  change in APM, surfaced before the skill body breaks
  silently.
- **APM `apm-policy.yml` rejects the writer.** RFC-0010
  §Unresolved questions Q8 names this risk; mitigation is
  per-pack README disclosure (T12) and per-organisation
  policy carve-outs adopters apply themselves. If review
  still rejects, the writer's existence is unaffected
  (the bundle ships under CLI and Claude-plugins routes
  regardless); only APM-routed installs at policy-
  enforcing orgs are at risk, and those orgs whitelist
  the marker-write paths explicitly.
- **`#10997` lands and Claude Code's first-session
  semantics change.** Per
  `claude-plugins-install-route` Risks. Both routes
  benefit; no spec amendment required.
- **Per-target token names (Copilot, Gemini) drift in
  APM's docs.** AC12 (e)'s single per-target test
  (Claude Code) assumes the documented
  `${CLAUDE_PLUGIN_ROOT}` token; the three deferred-via-
  AC17 targets (Copilot, Cursor, Gemini) accept their
  token names as they're discovered by the per-target
  characterisation matrix. If APM renames `${PLUGIN_ROOT}`
  to per-tool variants (e.g. `${COPILOT_PLUGIN_ROOT}`),
  the writer's data-directory resolution shim (AC3) needs
  the rename in lockstep. Mitigation: the precedence is
  fixed, not the token names — adding a token to the
  resolution shim is a one-line change per token.

## Changelog

- 2026-05-25: initial plan against
  [`spec.md`](spec.md) / RFC-0010.
- 2026-05-25: pre-EXECUTE adversarial-review reconciliation —
  (i) T4 `Depends on:` now includes T3 (schema permitted-values
  must admit `"apm"` before any pack emits a marker carrying
  it — Blocker 2); (ii) T1 Tests rewritten: dropped the
  default-flag test, added the required-flag-absent test, and
  the AC4 (e) test renamed/refactored to
  `test_apm_scope_writer_under_home_but_not_cwd_picks_user`
  with the genuinely-load-bearing nested-scope fixture
  (Blocker 1); (iii) T1 Tests' docstring assertion dropped
  per AC1 contract-surface demotion (Concern 12); (iv) T5
  Tests' Copilot/Cursor/Gemini per-target tests removed in
  favour of AC17 manual-QA matrix rows (Concern 8); (v)
  Approach §"Riskiest part" rewritten — per-target token-name
  uncertainty is the primary risk; symlink resolution demoted
  to secondary (Nit 16); (vi) T5 Tests preamble names the
  T1-vs-T5 layer boundary explicitly so the two layers assert
  different things (Concern 13); (vii) T11 `Depends on:`
  named the actual edges (T4, T6) rather than "T1 through T10"
  (Nit 17).
- 2026-05-25: pre-EXECUTE adversarial-review iteration 2
  reconciliation — (i) T1 Approach's `argparse` parser block
  rewritten to `choices=["claude-plugins", "apm"]`,
  `required=True`, no default; dead `"cli"` branch in the
  `args.install_route` switch deleted; spec / plan
  contradiction from iteration 1 closed — Blocker 1, Concern
  4, Concern 8; (ii) Rollout's Claude-plugins-route adopter
  paragraph rewritten to acknowledge that writer-template
  refresh and `install-marker.json` command refresh are
  coupled at projection time by `make build`; iteration-1
  "default preserves back-compat" claim dropped — Blocker 2;
  (iii) Reversibility paragraph rewritten to drop the same
  default-back-compat claim and explain the lockstep revert
  — Blocker 2; (iv) Construction-tests integration-tests
  block updated: the three deferred-via-AC17 tests
  (`test_per_target_characterisation_copilot/cursor/gemini`)
  dropped from the list — Concerns 5 & 6; (v) T1 test
  `test_apm_scope_writer_under_cwd_is_repo` renamed and
  refixtured to
  `test_apm_scope_writer_under_cwd_nested_under_home_is_repo`
  so AC4's first-branch-wins rule is genuinely realised
  — Concern 7; (vi) T10 gained a fourth test
  `test_precedent_spec_ac9_shlex_token_list_includes_flag`
  so the precedent's `shlex.split` expected-token list
  cannot drift past the v0.5 hook command — Concern 10;
  (vii) Risks "per-target token names drift" paragraph
  reworded to describe AC12 (e) as a single Claude Code
  test rather than plural — Nit 13; (viii) T11 `Depends on:`
  acknowledges T1 as a soft semantic dependency rather than
  claiming all other tasks are unrelated — Nit 14.
- 2026-05-25: pre-EXECUTE adversarial-review iteration 3
  reconciliation — (i) T1 test
  `test_apm_scope_writer_under_home_but_not_cwd_picks_user`
  re-labelled in its docstring: case (e) is home-branch
  coverage when writer is outside cwd, not a precedence
  guard (case (a) is the actual precedence test) — Concern
  1; (ii) T1 Tests added
  `test_data_dir_claude_plugin_data_wins_when_all_set`
  (AC3 f, full-stack precedence pin) and
  `test_data_dir_plugin_root_wins_over_cursor_plugin_root`
  (AC3 g, second adjacent-pair pin) — Concern 2;
  (iii) T4 plan-test list note added clarifying that
  `test_claude_plugins_hook_command_now_passes_flag` is
  filed in `test_build_derivation_claude_plugins.py` (the
  precedent's existing test home, asserting a claude-
  plugins-side projection), not the APM test file
  — Concern 3; (iv) T8 gained
  `test_distribution_adapters_names_apm_test_file_by_path`
  greping for the literal path of the APM test file in
  the sibling spec — Nit 6.
- 2026-05-25: pre-EXECUTE adversarial-review iteration 4
  reconciliation — (i) Approach §1 rewritten: `--install-route`
  is two-choice `{claude-plugins, apm}`, `required=True`, no
  default; iteration-1's required-flag flip had left stale
  "three-choice, default `claude-plugins`" prose at the top of
  the plan an implementer reads first — Concern 2; (ii) T3
  Tests list gained
  `test_v03_shaped_marker_without_install_route_field_parses_as_cli`
  pinning the absence-defaults-to-`"cli"` back-compat rail per
  AC10's v0.3-era marker clause — Concern 3; (iii) T1 plan-
  test parenthetical for `test_apm_scope_writer_under_cwd_
  nested_under_home_is_repo` changed from "first-branch-wins
  mirror" to "first-branch-wins precedence test" — Nit 4.
