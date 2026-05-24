# Plan: claude-plugins-install-route

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the
> spec, this document is allowed to change as you learn. When it
> changes substantially (a different approach, not just a re-ordering),
> note why in the changelog at the bottom.

## Approach

The shape of the change is **template-first, contract-second,
pipeline-third, sibling-spec-fourth, tests-throughout.** Authoring
order:

1. **Land the writer template (T1).** Write
   `packages/agentbundle/templates/install-marker.py` against TDD
   construction tests that exercise it as a black box (subprocess +
   env quartet + disk). Authoring the writer first means the build
   pipeline has something concrete to project; trying to wire the
   pipeline first leaves nothing to verify.
2. **Bump the contract and schemas (T2).** Edit
   `docs/contracts/adapter.toml` to v0.4 with `install-routes`; edit
   `docs/contracts/adapter.schema.json` to accept the new key; edit
   `docs/contracts/plugin-manifest.schema.json` to accept the
   synthesised `hooks` block on the *derived* shape while keeping the
   *source* shape valid without `hooks`. Schema-level changes are
   small and isolated; landing them now lets every later task assert
   against the schemas without re-rebasing.
3. **Land the marker schema relaxation (T3).** Amend
   `docs/specs/adapt-to-project/spec.md` § *.adapt-install-marker.toml
   schema* to mark `unresolved-markers` and `new-companions`
   optional and to add the optional `install-route` field. Amend the
   CLI install path to emit `install-route = "cli"`. Tests pin
   round-trip parsing through `tomllib` and through the core pack's
   session-start `_pack_names_from_marker` helper.
4. **Wire the build pipeline (T4).** Amend
   `packages/agentbundle/agentbundle/build/adapters/claude_code.py`
   (or a sibling helper in
   `packages/agentbundle/agentbundle/build/main.py`'s
   `_run_per_pack`) to project `pack.toml` into the derived
   `.claude-plugin/`, ship `install-marker.py` from the template,
   and synthesise the `SessionStart` hook entry in `plugin.json`.
   Goal-based check: diff the produced tree against a fixture.
5. **Migrate hand-authored `plugin.json` files (T5).** Drop the
   `hooks` block from every source-tree `plugin.json` (none of them
   currently carry it — the check is that they remain free of it
   post-migration; the migration is the schema enforcement plus the
   build derivation, not a file rewrite). A schema test in T2 pins
   this.
6. **Amend `adapt-to-project` skill body (T6).** Add the proactive
   cache-scan branch to the Pre-flight section. Three grep tests in
   `tests/skills/test_adapt_skill_body.py` (the existing home for
   the AC1 grep set per the parent spec) pin the new behaviour.
7. **Amend `adapt-to-project` spec ACs (T7).** Add the three new
   Acceptance Criteria (read-side fallback, idempotence with
   marker-consume, stale-entry drop-on-read). Pin the idempotence
   clause with one new integration test; the other two are
   contract-shape gates that the skill body greps (T6) plus the
   marker-schema tests (T3) already verify.
8. **Amend `distribution-adapters` spec (T8).** Add the conformance
   suite reference (one new AC, one Changelog line). The fixture
   set lives in this spec's owned integration tests; the sibling
   spec references them by path.
9. **Wire the self-host drift gate (T9).** Amend `make build-check`
   to assert byte-identical writer projection across packs.
   Red-team fixture mutates one byte; the gate fails.
10. **Land the manual-QA matrix rows (T10).** Add two rows to
    `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
    with `verification = transcript`; the transcripts themselves
    are out-of-PR (RFC-0008 Q5 close trigger).

**Riskiest part: the build-pipeline derivation (T4).** The Claude
Code adapter today projects per-primitive (skills, agents,
hook-bodies, hook-wiring, commands) and the per-pack runner copies a
hand-authored `plugin.json` verbatim. Adding *synthesis* of a hook
block is a new concern for the adapter; the cleanest seam is to
extend `_run_per_pack` in `main.py` (which already copies the
manifest) rather than to fold synthesis into the adapter's
`project()` (which is per-primitive, not per-pack-manifest).
T4's Tests subsection pins both the artifact-on-disk shape and the
contract that synthesis is idempotent — re-running `make build`
produces byte-identical output.

**Why TDD dominates.** The writer is a pure function from
environment + disk + `${CLAUDE_PLUGIN_ROOT}/pack.toml` → marker file
state + hash file state + stderr lines + exit code. Every behaviour
in the spec's Acceptance Criteria is expressible as a single
subprocess invocation with a controlled environment quartet. The
writer ships into adopter caches on every install of every pack —
the testing rigor must match the blast radius.

## Constraints

- [RFC-0008](../../rfc/0008-claude-plugins-install-route-parity.md)
  is the canonical proposal; this plan is its implementation. Any
  deviation from RFC-0008's *Proposal § Who writes the marker*, *§
  Pack-level declarations*, *§ Contract impact*, *§ Migration path*
  is a spec amendment, not a plan revision.
- [`docs/specs/adapt-to-project/spec.md`](../adapt-to-project/spec.md)
  is the install-marker schema authority — schema changes land
  there, not here. This spec amends that spec; it does not
  redefine the schema.
- [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  is the adapter contract authority — contract-shape changes land
  there, not here. This spec amends that spec; it does not
  redefine the contract.
- Stdlib-only Python (carries from
  `distribution-adapters/spec.md` Never-do). No `requirements.txt`,
  no third-party imports, no vendored libraries.
- No new top-level directory. `packages/agentbundle/templates/` is
  a new module-adjacent surface peer of `_data/` and `tests/` —
  not a new package, not a new top-level directory. The structural
  trigger fires for **adversarial review** (per work-loop SKILL.md
  Pre-EXECUTE), not for an RFC.

## Construction tests

Per-task tests are under each Task below in `Tests:` subsections.
Cross-cutting tests (here):

**Integration tests:**
- `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
  — owns the writer's end-to-end test surface. T1 ships every
  test in this file; AC18's explicitly-named tests
  (`test_first_install_local_scope`,
  `test_first_install_project_scope`,
  `test_first_install_user_scope`, `test_warm_cache_skips_write`,
  the three `test_refuse_*_scope` cases,
  `test_plugin_upgrade_replaces_entry`,
  `test_reinstall_after_keep_data_uninstall`) live here too.
  T8's amended sibling spec references this file by path for
  the conformance suite case list.
- `packages/agentbundle/tests/integration/test_build_derivation_claude_plugins.py`
  — owns the build-pipeline derivation diff test (T4 / AC9).

The proactive cache-scan idempotence (AC25) is grep-pinned in
T6, not integration-tested — there is no programmatic
skill-execution harness in v1 per the spec's AC15 + AC25
discussion. End-to-end verification lands as a manual-QA matrix
row in T10.

**Manual verification:**
- `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` —
  the two RFC-0008 Q5 close-trigger rows land in T10
  (claude-plugins install of `core` at project scope;
  claude-plugins install of `converters` at user scope).
  A third row covers the AC25 idempotence behaviour
  (proactive cache scan with a marker entry already present;
  expected outcome: no double-adaptation). All three transcripts
  are deferred to a follow-up per the matrix's existing
  `verification = transcript` deferral pattern.

## Tasks

The work-breakdown. Each task is a verifiable goal; `Tests:` comes
before `Approach:`; every task states `Depends on:` explicitly.

### T1: Writer template lands at `packages/agentbundle/templates/install-marker.py` with green integration tests for AC1-AC8

**Depends on:** none

**Verification mode:** TDD.

**Tests:** (every test in this list belongs in
`packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
and runs the writer in subprocess against a fixture-controlled
environment quartet — `${CLAUDE_PLUGIN_ROOT}`,
`${CLAUDE_PLUGIN_DATA}`, `${HOME}`, `${CLAUDE_PROJECT_DIR}`.)

Each test below tags the AC(s) it satisfies in parentheses. The
explicit AC18 end-to-end names appear in italics under the matching
unit case so a reviewer can grep both surfaces from one list.

- `test_writer_is_stdlib_only` (AC1). `grep -E '^(import|from) '
  packages/agentbundle/templates/install-marker.py` produces a
  module set that is a subset of the hard-coded allow-list
  `{argparse, datetime, hashlib, json, os, pathlib, sys, tempfile,
  tomllib}`. Any other module fails the test.
- `test_writer_docstring_names_spec` (AC1). The module docstring
  contains the literal string
  `docs/specs/claude-plugins-install-route/spec.md`.
- `test_scope_local_opt_in_for_repo_only_pack_writes_repo_marker`
  (AC2 (a) + AC18 *test_first_install_local_scope*). Asserts the
  written marker carries `install-route = "claude-plugins"` and
  no `detected_origin` field (the field is internal to the
  writer; only the stderr message surfaces it).
- `test_scope_project_opt_in_for_repo_only_pack_writes_repo_marker`
  (AC2 (b) + AC18 *test_first_install_project_scope*). The
  regression guard for Blocker-1: comparing the collapsed
  `marker_scope = "repo"` against `allowed-scopes = ["repo"]`
  must accept, not refuse.
- `test_scope_user_opt_in_for_user_only_pack_writes_user_marker`
  (AC2 (c) + AC18 *test_first_install_user_scope*).
- `test_scope_precedence_local_beats_project_beats_user` (AC2 (d)).
  All three opt-ins set; written marker is repo-scope; the
  stderr (when any path emits it) names `local` as
  `detected_origin`.
- `test_scope_malformed_local_json_falls_through_to_project`
  (AC2 (e)).
- `test_scope_no_match_exits_zero_no_marker_no_hash` (AC2 (f)).
  The marker file is absent **and**
  `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` is absent after the
  exit.
- `test_scope_project_dir_unset_skips_project_and_local_checks`
  (AC2 (h)). With `${CLAUDE_PROJECT_DIR}` unset and user opt-in
  for a user-only pack, the writer writes the user-scope marker
  without raising.
- `test_refuse_repo_only_pack_at_user_scope` (AC3 (a) + AC18).
  Asserts the exact stderr line carries `detected install scope
  user`, exit 0, no marker write, no hash file.
- `test_refuse_user_only_pack_at_project_scope` (AC3 (b) + AC18).
  Stderr carries `detected install scope project`.
- `test_refuse_user_only_pack_at_local_scope` (AC3 (c) + AC18).
  Stderr carries `detected install scope local` — the
  origin-vocabulary regression guard from Concern 7.
- `test_atomic_rename_uses_os_replace_and_recovers_on_crash`
  (AC4). Uses a wrapper-script `sitecustomize.py` that
  monkeypatches `os.replace` to raise `RuntimeError` on the
  first call and pass through on subsequent calls. Asserts:
  (i) the prior marker file is byte-unchanged after the crash;
  (ii) the next writer invocation against the same target
  succeeds and the final marker file contains both the
  pre-crash entry and the post-recovery entry.
- `test_hash_file_not_written_when_marker_write_fails` (AC5).
  `monkeypatch` raises `PermissionError` from `os.replace`;
  asserts no hash file on disk; asserts the next invocation
  successfully writes both.
- `test_detection_cold_start_writes` (AC6 (a)). No hash file →
  writes both.
- `test_detection_keep_data_reinstall_writes` (AC6 (b) + AC18
  *test_reinstall_after_keep_data_uninstall*). Hash file present
  and matching, marker file absent → writes both.
- `test_detection_warm_cache_skips` (AC6 (c) + AC18
  *test_warm_cache_skips_write*). Hash file matches **and**
  marker has an entry → exit 0, no stderr, no writes.
- `test_two_writers_sequential_both_entries_present` (AC7). Both
  writers invoked sequentially in subprocess; the resulting
  marker file's `packs-installed` array contains both pack
  names.
- `test_cli_to_claude_plugins_handoff_preserves_datetime` (AC7
  sub-assertion). Pre-seed the target marker file by calling
  `agentbundle.commands.install._append_install_marker(...)`
  **in-process** (the function shape *is* the canonical TOML
  emitter — no subprocess, no fixture pack, no chain-adapt).
  Run the Claude-plugins writer against the seeded file.
  Assert: (a) both entries are present; (b) the pre-seeded
  CLI-shaped entry's `installed-at` round-trips through
  `tomllib.loads(...)` as a `datetime.datetime` (not a `str`)
  — the CLI loader at install.py:866-874 drops non-`datetime`
  `installed-at` entries, so the new writer must preserve the
  bare-datetime-literal shape on re-emission.
- `test_plugin_upgrade_replaces_entry_not_stacks` (AC8 + AC18
  *test_plugin_upgrade_replaces_entry*).

**Approach:**

- Author `packages/agentbundle/templates/install-marker.py` to
  this contract surface (the function shape is the test surface):
  - `main(argv: list[str]) -> int`. Reads
    `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` from
    `os.environ`. Returns exit code.
  - `_detect_origin() -> Optional[Literal["local", "project",
    "user"]]` — walks the three `enabledPlugins` files in
    precedence order; returns the most-specific origin scope on
    opt-in, `None` for fall-through. Used both for adopter-facing
    stderr messages and to derive the marker-scope.
  - `_marker_scope(origin: Literal["local", "project", "user"])
    -> Literal["repo", "user"]` — collapses `local` and `project`
    to `"repo"`, passes `user` through. The value returned here is
    what gets compared against `[pack.install] allowed-scopes`
    and what picks the marker-file location. This is the
    Blocker-1 rail surfaced explicitly so a future reader sees
    *why* the collapse exists.
  - `_pack_toml(plugin_root: Path) -> dict` — `tomllib.loads` the
    pack manifest.
  - `_manifest_hash(plugin_root: Path) -> str` — `hashlib.sha256`
    of the raw bytes of `pack.toml`.
  - `_marker_path(marker_scope: str, project_dir: Path | None,
    home: Path) -> Path` — returns
    `<project>/.adapt-install-marker.toml` for `repo`
    `marker_scope`, `<home>/.agent-ready/.adapt-install-marker.toml`
    for `user`.
  - `_should_fire(marker_path: Path, pack_name: str, plugin_data:
    Path, current_hash: str) -> bool` — implements the
    hash-diff-OR-entry-absent dual condition.
  - `_write_marker(marker_path: Path, entry: dict) -> None` —
    read-modify-write through `tempfile.NamedTemporaryFile(dir=
    marker_path.parent, delete=False)`; `os.replace` for the
    rename. Re-emits all entries with the new entry replacing
    any existing entry for the same pack name.
  - `_write_hash(plugin_data: Path, current_hash: str) -> None` —
    only called from `main` after `_write_marker` returns.
- **TOML emission shape (load-bearing — see Boundaries
  Always-do "Emit `installed-at` as a bare TOML offset-datetime
  literal").** The writer's marker-file emission mirrors
  `packages/agentbundle/agentbundle/commands/install.py:_append_install_marker`
  (lines 896-934) field-for-field:
  - `marker-schema-version = "0.1"` (basic string, quoted).
  - For each entry:
    - `name = "<pack>"` (basic string, escape `"` and `\` and
      refuse any control character `< 0x20 | == 0x7F`
      per the existing `_emit_basic_string` contract).
    - `version = "<semver>"` (basic string, same escaping).
    - `installed-at = YYYY-MM-DDTHH:MM:SSZ` — **bare TOML
      offset-datetime literal, no quotes**. Produced by
      `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`.
      The CLI loader at install.py:866-874 drops any entry
      whose `installed-at` is not a `datetime`; emitting a
      basic-string `"..."` would round-trip as `str` and get
      dropped on the next CLI invocation. This is the
      Blocker-3 rail.
    - `install-route = "claude-plugins"` (basic string, fixed
      literal — never adopter-derived).
    - `unresolved-markers = [...]` and `new-companions = [...]`
      are **omitted** (v0.4 relaxes them to optional; the
      writer has no visibility into the projected primitive
      tree).
  - The basic-string-emit primitive is **vendored inline** as a
    ~15-line function copied from
    `agentbundle.config._emit_basic_string` — clearly commented
    as a copy with the source path noted, so a future security
    fix at the source propagates here via the canonical
    template's single source-of-truth (the writer ships into
    adopter caches; importing `agentbundle` would require
    bundling the package or depending on its on-disk install,
    both of which violate stdlib-only).
- Build the fixture pack roots inline as `tmp_path`-rooted
  directories with hand-authored `pack.toml`, `plugin.json`, and
  `enabledPlugins` settings JSONs. Reuse a `pytest` fixture
  `pack_root_factory` that builds these in one call.
- Each test invokes the writer as
  `subprocess.run([sys.executable,
  "packages/agentbundle/templates/install-marker.py"], env=...,
  capture_output=True, check=False)` so failures surface the
  writer's own stderr unmodified.

**Done when:** every test in this task's `Tests:` list is green;
`grep -E '^(import|from) '
packages/agentbundle/templates/install-marker.py` shows a module
set that is a subset of the AC1 allow-list.

---

### T2: Contract bump to v0.4 and schema acceptances land in `docs/contracts/`

**Depends on:** none

**Verification mode:** TDD (schema validation) + goal-based
(file existence + `[contract] version` value).

**Tests:**
- `test_contract_version_is_v04` — `tomllib.loads` of
  `docs/contracts/adapter.toml` returns
  `{"contract": {"version": "0.4", ...}}`. AC11.
- `test_claude_code_install_routes_present` —
  `contract["adapter"]["claude-code"]["install-routes"] == ["cli",
  "claude-plugins"]`. AC11.
- `test_other_adapters_have_no_install_routes` — Kiro, Copilot,
  Codex blocks do not declare `install-routes`. AC11.
- `test_adapter_schema_accepts_install_routes` — round-trip
  validation: the existing
  `packages/agentbundle/agentbundle/build/validate.py` accepts the
  amended contract; a mutation removing `install-routes` from the
  schema is still accepted (the field is optional); a mutation
  whose value is `"cli"` (a string, not an array) is rejected.
  AC11.
- `test_source_plugin_manifest_schema_forbids_hooks` (AC10
  gate 1). The source-shape schema validates a manifest carrying
  only `name`/`version`/`description` and **rejects** any
  manifest carrying a `hooks` property. This is the Blocker-5
  rail: a single permissive schema cannot catch hand-authored
  drift.
- `test_derived_plugin_manifest_schema_accepts_synthesised_hooks`
  (AC10 gate 1). The sibling derived-shape schema validates a
  manifest carrying `name`/`version`/`description` + the
  synthesised `hooks.SessionStart` block.

**Approach:**
- Edit `docs/contracts/adapter.toml`:
  - `[contract] version = "0.3"` → `"0.4"`.
  - Under `[adapter."claude-code"]`, add the key
    `install-routes = ["cli", "claude-plugins"]`, preceded by
    a one-line `#`-prefixed TOML comment naming RFC-0008 and
    spec `claude-plugins-install-route`.
- Edit `docs/contracts/adapter.schema.json` to accept the new
  optional `install-routes` array on the `adapter.<name>` shape
  (items: enum of `"cli"` and `"claude-plugins"`; both ordered).
- **Schema split** (per AC10 gate 1). The validator
  (`packages/agentbundle/agentbundle/build/validate.py:22`)
  explicitly lists `not` / `oneOf` / `anyOf` / `allOf` as
  "Unsupported by design" — confirmed at PLAN time, no
  EXECUTE-time discovery needed. The schema-split rail uses
  `additionalProperties: false` + an explicit positive
  property list:
  - Amend `docs/contracts/plugin-manifest.schema.json` (the
    source-shape schema; the existing file) to add
    `"additionalProperties": false` and an explicit
    `properties` enumeration that includes `name`, `version`,
    `description`, `skills`, `agents` and **omits** `hooks`.
    A source-tree manifest carrying a `hooks` block fails
    validation because `hooks` is not in the property list and
    `additionalProperties: false` refuses unlisted keys. Keeps
    the existing `required: ["name", "version", "description"]`.
  - Create `docs/contracts/plugin-manifest.derived.schema.json`
    — the derived-shape schema. Identical to the source schema
    plus the optional `hooks` property of shape
    `{ "SessionStart": array<{"command": string}> }`, added to
    the `properties` enumeration (so `additionalProperties:
    false` still holds; the derived shape just permits one
    more key).
  - The build pipeline (T4) validates source-tree manifests
    against the source schema and derived-tree manifests
    against the derived schema.
- Update existing contract tests in
  `packages/agentbundle/agentbundle/build/tests/test_contract.py`
  and `test_plugin_manifest_schema.py` for the new shape.

**Done when:** every test in this task's `Tests:` list is
green; `tomllib.loads(open("docs/contracts/adapter.toml").read())`
returns `version == "0.4"`; the existing test suite under
`packages/agentbundle/agentbundle/build/tests/` is green.

---

### T3: Marker schema relaxation lands in `adapt-to-project/spec.md`; CLI install emits `install-route = "cli"`

**Depends on:** T2 (the schema must accept the new shape before
the CLI emits it).

**Verification mode:** TDD.

**Tests:**
- `test_cli_install_emits_install_route_cli` — runs `agentbundle
  install` against an existing fixture pack and asserts the
  written marker has `install-route = "cli"` on every entry.
  AC13.
- `test_v04_marker_omits_unresolved_markers_and_new_companions` —
  pre-seeds a marker file containing only
  `name` / `version` / `installed-at` / `install-route` and
  verifies (a) `tomllib` parses it cleanly; (b) the existing
  `_pack_names_from_marker` helper in
  `packs/core/.apm/hooks/session-start.py` returns the pack name
  unchanged. AC12, AC14.
- `test_v03_marker_still_parses_under_v04_reader` — pre-seeds a
  marker file in the v0.3 shape (no `install-route`) and asserts
  the reader treats it as `install-route = "cli"`. AC12.

**Approach:**
- Amend
  `docs/specs/adapt-to-project/spec.md` § *.adapt-install-marker.toml
  schema* (the schema block around lines 207-237):
  - Add `install-route = "cli" | "claude-plugins"` as an
    **optional** field on each `[[packs-installed]]` entry.
    Document the read-side default as `"cli"` when absent.
  - Mark `unresolved-markers` and `new-companions` as **optional**
    under v0.4. Document the read-side fallback (scan the
    projected primitive tree directly).
- Add a Changelog entry naming this spec by path:
  `- 2026-05-24: install-marker schema gains optional install-route field; unresolved-markers and new-companions marked optional per docs/specs/claude-plugins-install-route/spec.md.`
- Amend `packages/agentbundle/agentbundle/commands/install.py`
  `_append_install_marker` to emit `install-route = "cli"` on
  every entry. The change is a one-line insertion in the
  `lines.append(...)` loop around line 911.

**Done when:** the three tests are green; the existing
`agentbundle install` test suite is green; the `adapt-to-project`
spec carries the amended schema block and the Changelog line.

---

### T4: Build pipeline derives `pack.toml`, `install-marker.py`, and synthesises the `SessionStart` hook block

**Depends on:** T1 (template must exist before the pipeline can
project it), T2 (schema must accept the synthesised shape).

**Verification mode:** Goal-based check.

**Tests:**
- `test_derivation_projects_pack_toml` — AC9 (c). Diff
  `dist/claude-plugins/<pack>/pack.toml` against
  `packs/<pack>/pack.toml` byte-for-byte; identical.
- `test_derivation_projects_install_marker` — AC9 (b). Diff
  `dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
  against `packages/agentbundle/templates/install-marker.py`
  byte-for-byte; identical.
- `test_derivation_synthesises_hooks_block` — AC9 (a). The
  derived `plugin.json` carries
  `{"hooks": {"SessionStart": [{"command": "python3
  \"${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py\""}]}}`
  with the canonical command string.
- `test_derivation_preserves_source_fields` — AC9 (a). The
  derived `plugin.json`'s `name`, `version`, `description`
  match the source `plugin.json` exactly.
- `test_derivation_idempotent` — `make build` twice in a row
  produces byte-identical output.
- `test_make_build_check_passes_post_migration` — AC9. `make
  build-check` (the self-host drift gate) exits zero after the
  T4 migration lands.

**Approach:**
- **Canonical source path resolution.** The user-visible
  canonical path is
  `packages/agentbundle/templates/install-marker.py` (per AC1 of
  this spec and AC20's drift gate). For zipapp packaging
  reachability, the build pipeline imports the template via
  `importlib.resources.files("agentbundle").joinpath("_data/install-marker.py")`
  with a filesystem-relative fallback to
  `<repo>/packages/agentbundle/templates/install-marker.py`,
  matching the existing pattern in
  `packages/agentbundle/agentbundle/build/main.py:53-70`
  (`_read_bundled`). The `_data/` copy is **synced from the
  `templates/` copy by the existing `make build-self` /
  `make build-check` self-host machinery** (the same mechanism
  that already syncs `_data/adapter.toml`,
  `_data/pack.schema.json`, etc., from `docs/contracts/`). If
  the existing sync doesn't already cover `templates/`, T4
  extends it with one line under
  `packages/agentbundle/agentbundle/build/self_host.py` — pre-
  EXECUTE the implementer reads `self_host.py` to confirm which
  file the sync lives in and adjusts the task description if a
  different file is involved (single-line change either way).
- Amend `packages/agentbundle/agentbundle/build/main.py`
  `_run_per_pack` (lines 255-280) to:
  - After the existing `validate_plugin_manifest(plugin_manifest)`
    + `shutil.copy2(...)` block, **load the copied manifest as
    JSON, splice in the synthesised `hooks.SessionStart` block,
    and re-serialise** (`json.dumps(..., indent=2, sort_keys=False)
    + "\n"`, preserving the existing convention).
  - Also copy `pack.toml` from `pack.path / "pack.toml"` to
    `per_pack_output / "pack.toml"` (no transform).
  - Also copy the canonical writer template (resolved via the
    `_read_bundled`-shaped helper above) to `per_pack_output /
    ".claude-plugin" / "scripts" / "install-marker.py"`.
- Add a fixture under
  `packages/agentbundle/agentbundle/build/tests/fixtures/derived/<pack>/`
  capturing the expected derived shape for one pack; the diff
  test compares against it. The fixture is regenerable from the
  build; the goal-based test asserts no drift.

**Done when:** the six tests are green; `make build && diff -r
dist/claude-plugins/core/.claude-plugin/scripts
packages/agentbundle/templates/` shows zero diff against the
template; `make build-check` exits zero.

---

### T5: Hand-authored `plugin.json` files audited for the `hooks` block (schema gate prevents regression)

**Depends on:** T2 (schema must already accept both shapes).

**Verification mode:** Goal-based check.

**Tests:**
- `test_no_source_plugin_json_carries_hooks` — for each
  `packs/<pack>/.claude-plugin/plugin.json` in `packs/`, assert
  that `json.loads(...)` produces a dict whose `hooks` key is
  absent. AC10.
- `test_source_plugin_json_validates_against_schema` —
  every source-tree `plugin.json` validates against
  `docs/contracts/plugin-manifest.schema.json`. AC10.

**Approach:**
- Read every source-tree `packs/*/.claude-plugin/plugin.json`;
  confirm none currently declare `hooks` (the existing six all
  declare only `name`/`version`/`description`, so the migration
  is effectively a no-op — but the test pins the property
  forever).
- No file edits expected; if any pack carries a `hooks` block
  in source, this task's `Tests:` will fail and the operator
  removes the stale block before re-running.

**Done when:** both tests are green.

---

### T6: `adapt-to-project` skill body gains the proactive cache-scan branch with grep-pinned behaviour

**Depends on:** T3 (the marker-schema relaxation must be
documented before the skill body cites it).

**Verification mode:** TDD (grep-pinned).

**Tests:** (live in the existing skill-body test home —
`packages/agentbundle/tests/skills/test_adapt_skill_body.py`
or whatever path houses the AC1 grep set for the
adapt-to-project spec; the test_path follows the existing
convention.)

- `test_skill_body_names_proactive_cache_scan_heading` —
  AC15 grep #1. Asserts the literal heading `Proactive cache
  scan.` (case- and punctuation-sensitive) appears.
- `test_skill_body_names_cache_path` — AC15 grep #2. Asserts
  `~/.claude/plugins/cache/` appears verbatim.
- `test_skill_body_names_idempotence_clause` — AC15 grep #3.
  Asserts `do not double-adapt` appears verbatim.
- `test_skill_body_names_dedupe_rule` — AC15 grep #4. Asserts
  `if a marker entry is present, do not synthesise a second
  adaptation` appears verbatim (the operative dedupe rule the
  LLM reads — pinned at the spec level so a future SKILL.md
  rewrite cannot drift past it).
- `test_skill_body_names_stale_entry_drop` — AC26's grep
  (added by T7). Asserts `silently drops the entry` appears
  verbatim.
- `test_skill_body_preflight_section_carries_six_steps` —
  one new behavioural test: parses the Pre-flight section
  numbered list and asserts six numbered items (the existing
  five plus the new one). Catches a regression where someone
  accidentally drops one of the existing five while editing.

**Approach:**
- Amend
  `packs/core/.apm/skills/adapt-to-project/SKILL.md`
  Pre-flight section (around lines 33-85) to add a sixth
  numbered step. Wording must carry the five grep-pinned
  literals verbatim — *don't paraphrase any of them*:
  > **6. Proactive cache scan.** Scan
  > `~/.claude/plugins/cache/` and (if `${CLAUDE_PROJECT_DIR}`
  > is set) `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/` for
  > pack roots — directories containing both
  > `.claude-plugin/plugin.json` and `pack.toml`. For each
  > cache-resident pack with **no** `[[packs-installed]]` entry
  > at either scope's marker file naming that pack, treat the
  > pack as a fresh install: prepend a synthetic install-marker
  > entry to the session-internal proposal queue and run
  > class-1/2/3/4 inline. This closes the
  > [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
  > *active case* — an adopter who proactively runs
  > `/adapt-to-project` in session 1 before the
  > `SessionStart` writer fires.
  >
  > **Idempotence: do not double-adapt.** If a marker entry is
  > present, do not synthesise a second adaptation. When a
  > marker entry for the same pack is present at either scope,
  > the marker-consume path (step 3 above) owns the adaptation;
  > the proactive cache scan must not synthesise a second
  > entry for the same pack name in the same session.
  >
  > **Stale-entry drop-on-read.** When a `[[packs-installed]]`
  > entry's pack is no longer present in any cache directory
  > under `~/.claude/plugins/cache/` and not recorded in any
  > scope's state file, the skill silently drops the entry on
  > read — no nudge, no proposal queue entry. Stale entries
  > can survive uninstall of a Claude-plugins-routed pack
  > because the install→adapt chain has no uninstall hook
  > today (deferred per
  > [RFC-0008 §Unresolved questions Q2](../../rfc/0008-claude-plugins-install-route-parity.md#unresolved-questions)).

**Done when:** all six tests in T6's `Tests:` list are green
(four AC15 greps + the AC26 stale-entry-drop grep + the
behavioural six-steps test).

---

### T7: `adapt-to-project` spec ACs gain three new entries (read-side fallback, idempotence, stale-entry drop-on-read)

**Depends on:** T6 (the skill body's cache-scan behaviour must
be in place before the AC pins it as a contract surface).

**Verification mode:** Goal-based check (literal AC headers
present; Changelog line present). The behaviours themselves are
pinned by T6's grep set, T3's marker-schema tests, and the
manual-QA matrix rows added by T10 — T7 only edits the parent
spec's text.

**Tests:**
- `test_adapt_spec_has_ac24_read_side_fallback` — `grep -E
  '^- \[ \] \*\*AC24'
  docs/specs/adapt-to-project/spec.md` returns one match. AC16.
- `test_adapt_spec_has_ac25_proactive_cache_scan_idempotence` —
  same `grep` for `AC25`. AC16.
- `test_adapt_spec_has_ac26_stale_entry_drop_on_read` — same
  `grep` for `AC26`. AC16.
- `test_adapt_spec_changelog_names_this_spec` —
  `docs/specs/adapt-to-project/spec.md` Changelog contains a
  dated entry whose body includes the literal path
  `docs/specs/claude-plugins-install-route/spec.md`.

(Concern 14: the prior `^- \[ \] \*\*AC` count-based assertion
is brittle — checks on the literal AC numbers above are stable
across future PRs that flip other checkboxes.)

**Approach:**
- Amend `docs/specs/adapt-to-project/spec.md` Acceptance Criteria
  section to add three new ACs at the end (numbered to extend
  the existing AC23). The full text is in the spec file's
  AC16 — copy verbatim into the parent spec.
- Add a Changelog line referencing this spec by path:
  `- 2026-05-24: AC24/AC25/AC26 added per docs/specs/claude-plugins-install-route/spec.md — read-side fallback for v0.4 markers, proactive cache-scan idempotence, stale-entry drop-on-read.`
- AC26 (stale-entry drop-on-read) gains a SKILL.md body grep
  for one literal phrase (e.g., `silently drops the entry`); T6
  already adds the four other grep literals, this is a fifth.
  Update T6's `Tests:` list to include the fifth grep.

**Done when:** the four tests are green; the parent
`adapt-to-project` spec has three new ACs and the Changelog line.

---

### T8: `distribution-adapters` spec amendment — conformance suite reference + v0.4 Changelog line

**Depends on:** T2 (the contract version must already be v0.4).

**Verification mode:** Goal-based check.

**Tests:**
- `test_distribution_adapters_changelog_names_this_spec` —
  `docs/specs/distribution-adapters/spec.md` Changelog contains
  `claude-plugins-install-route` by path. AC17.
- `test_distribution_adapters_has_install_routes_ac` — `grep -c
  'install-routes'
  docs/specs/distribution-adapters/spec.md` returns ≥ 1 (the new
  AC body). AC17.

**Approach:**
- Append one new AC to
  `docs/specs/distribution-adapters/spec.md` Acceptance Criteria
  section:
  - **AC<N+1> (install-routes contract).** The adapter contract
    (`docs/contracts/adapter.toml`) declares `install-routes`
    on `[adapter."claude-code"]` per RFC-0008 / spec
    `claude-plugins-install-route`. The conformance suite ships
    a *marker presence* and a *scope refusal* case per declared
    install route; the per-route fixtures live in
    `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`.
    The Claude-plugins *marker presence* case is asserted on
    **session 2 or later** until upstream
    [`anthropics/claude-code#10997`](https://github.com/anthropics/claude-code/issues/10997)
    ships a fix.
- Add a Changelog line.

**Done when:** the two tests are green.

---

### T9: `make build-check` drift gate asserts byte-identical writer projection across packs

**Depends on:** T4 (the derivation must already be producing the
projected writer).

**Verification mode:** TDD.

**Tests:**
- `test_make_build_check_fails_on_writer_drift` — AC20. The
  test mutates one byte in a derived
  `dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
  copy in a `tmp_path`-rooted shadow tree, runs the drift
  check against it, asserts non-zero exit.
- `test_make_build_check_passes_on_clean_tree` — AC20. The
  test runs the drift check against the actual `dist/`
  tree after `make build`; exit zero.
- `test_make_build_check_catches_emit_basic_string_drift` —
  iteration-2 Concern 4. The test mutates the writer template's
  vendored `_emit_basic_string` (e.g., removes the control-char
  refusal) and asserts `make build-check` exits non-zero with
  the stderr naming the diverging input.
- `test_make_build_check_passes_emit_basic_string_parity_on_clean` —
  asserts the parity check passes against the unmodified
  template.

**Approach:**
- `make build-check` invokes
  `python3 -m agentbundle.build check` (per `Makefile`'s
  existing `build-check` target). The check logic lives in
  `packages/agentbundle/agentbundle/build/self_host.py`'s
  `check`-mode entrypoint (or the sibling `__main__.py`
  dispatch — pre-EXECUTE the implementer confirms the actual
  symbol; `grep -n 'def.*check\|cmd_check' packages/agentbundle/agentbundle/build/`).
  T9 amends that entrypoint with two new mechanical assertions:
  1. **Writer-template drift**: for every
     `dist/claude-plugins/<pack>/.claude-plugin/scripts/install-marker.py`
     produced by `make build`, assert
     `hashlib.sha256(open(path, 'rb').read()).hexdigest()` equals
     `hashlib.sha256(open(packages/agentbundle/templates/install-marker.py, 'rb').read()).hexdigest()`.
     Drift fails the check with a one-line stderr naming the
     diverged pack and path.
  2. **Source-shape plugin.json drift** (AC10 gate 2): for every
     `packs/*/.claude-plugin/plugin.json`, assert `"hooks" not in
     json.loads(open(path).read())`. A stray `hooks` block in
     source fails the check; this rail cannot be neutered by a
     schema edit (it's an in-Python assertion, not a schema
     validation).
  3. **Vendored `_emit_basic_string` parity** (Concern 4 from
     iteration-2 review). The writer template vendors a ~15-line
     copy of `agentbundle.config._emit_basic_string` (the
     basic-string-emit primitive that refuses control characters
     and escapes `"`/`\` to prevent TOML injection). Drift
     between the vendored copy and the source primitive
     re-opens the injection vector. The check imports
     `agentbundle.config._emit_basic_string` and applies it to
     a fixed corpus of test strings (control chars, quotes,
     backslashes, the empty string, a multi-byte unicode
     character); it then dynamically loads the writer template's
     `_emit_basic_string` from the file and applies it to the
     same corpus; asserts byte-identical output for every input.
     Drift fails the check with a one-line stderr naming the
     diverging input. This is the mechanical rail backing the
     spec's Never-do bullet on per-pack writer divergence at
     the *function* level (not just the file level).
- All three assertions emit one stderr line each on failure,
  naming the offending path / input; exit code 1 on any failure.

**Done when:** every test in this task's Tests list is green;
`make build-check` against the post-migration tree exits zero;
the red-team byte-mutation fixtures (both writer-drift and
`_emit_basic_string`-drift) cause `make build-check` to exit
non-zero with the matching stderr.

---

### T10: Manual-QA matrix gains three RFC-0008-driven rows

**Depends on:** T1 through T9 (the rows describe behaviour the
prior tasks must have shipped).

**Verification mode:** Goal-based check (the row shape; the
transcripts themselves are deferred).

**Tests:**
- `test_manual_qa_matrix_has_claude_plugins_core_row` —
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
  contains a row naming `claude-plugins install of core at
  project scope`. AC19.
- `test_manual_qa_matrix_has_claude_plugins_converters_row` —
  same file contains a row naming `claude-plugins install of
  converters at user scope`. AC19.
- `test_manual_qa_matrix_has_proactive_cache_scan_idempotence_row` —
  same file contains a row naming `proactive cache scan
  idempotence — marker entry present, no double-adapt`. The
  end-to-end pin for AC25.
- `test_manual_qa_matrix_rows_carry_verification_transcript` —
  all three new rows declare `verification = transcript`. AC19.

**Approach:**
- Append the three rows to
  `docs/specs/adapt-to-project/notes/manual-qa-matrix.md`
  per its existing row shape. Rows 1 and 2 name RFC-0008 Q5 as
  the close-trigger; row 3 names AC25 of this spec as the
  trigger and the parent `adapt-to-project` spec's new AC25 as
  the verification-source. All three ship with the transcript
  artifact deferred per the matrix's existing deferral pattern.

**Done when:** the four tests are green.

---

## Rollout

The change ships in a single PR per RFC-0008. The PR's
`installed:` rail is the existing `make build && make
build-check` + the new integration tests under
`packages/agentbundle/tests/integration/`. Adopters consume the
change via:

- **Claude-plugins route adopters.** The next `claude plugin
  install` of any pack from this catalogue includes the
  derived `.claude-plugin/scripts/install-marker.py`; the
  `SessionStart` hook fires on session 2 (per the upstream
  `#10997` caveat) and the adopter sees the same install→adapt
  nudge a CLI install would have produced.
- **CLI route adopters.** No behaviour change beyond the new
  `install-route = "cli"` field on `[[packs-installed]]`
  entries written by `agentbundle install`. Existing markers
  written before this PR remain valid (v0.4 readers treat the
  field's absence as `"cli"`).
- **Self-hosting adopters.** `make build-check` is a CI gate;
  the post-migration tree passes the gate on first commit.

Reversibility: every code change is contained to
`packages/agentbundle/`, `docs/contracts/`, `docs/specs/`, and
`packs/core/.apm/skills/adapt-to-project/SKILL.md`. Reverting
the PR restores the prior contract version, the prior
hand-authored `plugin.json` files (already match the source
shape this PR ships), and the prior skill body. The marker
schema gains optional fields — reverting drops those fields'
acceptability but does not corrupt existing markers (the
fields were optional, not required).

## Risks

- **`#10997` lands while this PR is in review.** Migration is
  mechanical: drop the `SessionStart` from the derived
  `plugin.json`, replace with `PostInstall` per the upstream
  hook shape, drop the `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`
  diff scaffolding from the writer. The conformance suite case
  for *marker presence* stays unchanged; the *session 2 or
  later* caveat on AC17 disappears. Reopen RFC-0008 for that
  amendment.
- **Marketplace review rejects the writer.** RFC-0008
  §Drawbacks names this risk; mitigation is to pre-disclose
  the write behaviour in each pack's README. If review still
  rejects, the writer's existence is unaffected (the bundle
  ships under the Claude-plugins route either way); only the
  Anthropic-curated marketplace distribution is at risk, and
  the bundle remains installable from any GitHub-marketplace
  source.
- **A pack's `pack.toml` shape changes after this PR.** The
  writer reads `[pack.install] allowed-scopes`; a future
  schema bump that renames or relocates the field breaks the
  refusal rail. Mitigation: AC11 of the parent
  `distribution-adapters` spec already requires
  `default-scope ∈ allowed-scopes` enforcement in
  `pack.schema.json` — the writer's reads are pinned to a
  schema surface that is already test-covered. Any future
  rename routes through a contract bump that this spec is
  named in the `Constrained by` set of.
- **Two writers race in a way the integration tests don't
  cover.** The integration tests run writers sequentially via
  subprocess. True concurrency (two `SessionStart` hooks
  firing in the same session, in different processes) would
  require the `os.replace` primitive's atomicity to be
  enforced by the OS, not by the test. Mitigation: the spec's
  Boundaries rail mandates `os.replace`; AC4's test is the
  best the writer can do in-process. A future task could add a
  `multiprocessing`-based concurrency test if the failure mode
  ever surfaces.

## Changelog

- 2026-05-24: initial plan against
  [`spec.md`](spec.md) / RFC-0008.
- 2026-05-24: pre-EXECUTE adversarial-review iteration 1
  reconciliation — T1 Tests list rewritten with explicit AC tags
  + AC18 end-to-end test names; T1 Approach pins `_detect_origin`
  / `_marker_scope` split (Blocker 1) and bare-datetime TOML
  emission (Blocker 3); T2 split `plugin-manifest.schema.json`
  into source + derived schemas (Blocker 5); T4 canonical
  source path resolved via the `_read_bundled` pattern
  (Concern 6); T7 verification mode demoted to goal-based with
  literal-AC-number assertions (Blocker 4 + Concern 14); T6
  gained two new grep tests for the dedupe rule and the
  stale-entry-drop rule (Blocker 4 propagation); T9 names the
  exact entrypoint file (Concern 6); T10 gained the
  cache-scan idempotence row (Blocker 4 end-to-end pin).
- 2026-05-24: pre-EXECUTE adversarial-review iteration 2
  reconciliation — T2 schema-split committed to
  `additionalProperties: false` + explicit property list
  (validator's `not` is "unsupported by design" per
  `validate.py:22`; resolved at PLAN time, not EXECUTE — Concern
  1); T1 CLI-handoff sub-assertion seeds via
  `_append_install_marker` in-process rather than a subprocess
  install path (Concern 2); T2 adapter.toml edit phrasing
  disambiguated (Concern 3); T9 gained a third drift gate —
  vendored `_emit_basic_string` parity against a fixed attack
  corpus (Concern 4); test renames + Done-when counts updated
  (Nits 5-7).
