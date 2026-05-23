# Plan: distribution-adapters

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Build inside-out, from data to pipeline. First land the **scaffolds and
schemas** (T1a) — `packages/agentbundle/` package layout, `pyproject.toml`,
the shared build-pipeline scaffolds (`build/__init__.py`, `build/contract.py`,
`build/adapters/__init__.py`, `build/validate.py`, and the fixtures-layout
convention), plus `adapter.schema.json` for the adapter contract. Then populate
the **contract data** (T1b) — every (primitive, adapter) pair in
`adapter.toml`, plus the `kiro-agent-frontmatter-v0.9` mapping and the
Copilot `frontmatter-default`. Then land the **sibling schemas** (T1c) —
`pack.schema.json` and `plugin-manifest.schema.json`. Splitting T1 into
three keeps each commit reviewable and lets T2–T5 enter supervisor mode
as soon as T1b lands.

Then land the **four reference adapters** in parallel — each is a
self-contained pure-stdlib Python module that takes a primitive (from a
pack's `.apm/`) plus the adapter's projection rules (from the contract) and
emits the projected output. The adapters share nothing but the contract;
they can be built independently. Finally, land the **build pipeline** that
wires recipes, pack discovery, adapter dispatch, marketplace aggregation,
and self-host mode together — including the `make build --check` round-trip
diff. The riskiest part is the contract's shape: get the projection-mode
enum, the (primitive, adapter) pair enumeration, and the `on-conflict` table
right *before* writing any adapter, or every adapter re-derives them.

## Constraints

- **RFC-0001** — [Bundle distribution by adapter spec + ecosystem build
  pipeline](../../rfc/0001-bundle-distribution-by-adapter-spec.md). The
  contract path, the seven projection modes, the four reference adapters,
  the five primitive types (`skill`, `agent`, `hook-body`, `hook-wiring`,
  `command`), the Tier-1/2/3 model, the per-mode `on-conflict` defaults,
  and three of the six recipe types all come from there. Open question Q1
  (Kiro hook wiring schema) stays at `degraded-info-log` per the RFC.
- **RFC-0002** — [Self-hosting](../../rfc/0002-self-hosting.md) consumes
  this spec's `make build --check` gate and supplies the other three
  recipe types (`per-pack-overlay`, `composite-agents-md`,
  `composite-marketplace`). We define the command surface and the
  six-recipe set; RFC-0002's spec wires the CI gate and authors the
  composite self-host recipe content.
- **RFC-0003** — [Adapter contract publication + reference CLI](../../rfc/0003-spec-and-cli.md)
  consumes the contract this spec produces and imports
  `agentbundle.build` as a library (no `sys.path` tricks, no fork). The
  CLI is `packages/agentbundle/`'s public surface; this spec ships the
  build module under the same package.
- **RFC-0004** — [Install-scope dimension](../../rfc/0004-install-scope-per-pack.md).
  Bumps `[contract] version` 0.1 → 0.2 and
  `.agent-ready-state.toml` `schema-version` 0.1 → 0.2; adds the
  `[scope]` table on adapter contracts, the `[pack.install]` table on
  `pack.toml`, the three user-scope refusal rails (seeds, hooks,
  marker), the scope-keyed state file, and the path-jail-per-scope
  rule. Tasks T10–T14 below implement the contract / schema / build-
  side; the sibling `agent-spec-cli` spec implements the CLI surface
  (`--scope` flag, dual-state-file walking, refuse-and-explain at
  v0.1 write, `installed: <pack> @ <scope>` output).
- **CONVENTIONS.md** — Profile B+ work-loop discipline applies. Tests
  before approach; `Depends on:` on every task; verification mode
  named per task.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`
subsections). This top-level section is only for cross-cutting tests that
span tasks.

**Integration tests:**
- **End-to-end `make build`** (verifies Acceptance Criterion 7).
  Drives the full pipeline against the four reference fixture packs
  under `packages/agentbundle/agentbundle/build/tests/fixtures/packs/`
  on a clean checkout in a temp dir; asserts the `dist/apm/<pack>/`
  and `dist/claude-plugins/<pack>/` shapes and a single
  `marketplace.json`. Production-pack migration (a top-level `packs/`)
  is out of scope here per spec AC #7 — RFC-0001's F-dist follow-on
  ships it. Lives at
  `packages/agentbundle/agentbundle/build/tests/test_end_to_end_build.py`.
  **Authored by T8**; T7 reads it as a regression check but does not author it.
- **End-to-end `make build --check`** (verifies Acceptance Criterion 10).
  Runs the self-host dry-run against the current source tree; asserts
  exit zero on a clean tree; mutates one source file in a temp checkout
  and asserts non-zero exit with a per-file drift listing. Lives at
  `packages/agentbundle/agentbundle/build/tests/test_self_host_check.py`.
  **Authored by T7**; T8 imports it as a regression gate. Comparison-rule
  unit tests (LF normalisation, mode-bit comparison, symlink-via-lstat)
  are owned by sibling spec `self-hosting` — this file imports them as a
  regression gate rather than duplicating them.

**Manual verification:** none — both the build and the self-host gate
have machine-checkable goal artifacts.

## Tasks

The work-breakdown. Tasks are sized so each one is a coherent commit or PR.
**Phrase each task as a verifiable goal, not a procedure.** The task name
*is* the success criterion: *"Add validation"* → *"All invalid-input tests
pass"*; *"Refactor X"* → *"Tests for X green before and after; public
surface unchanged"*. **Within each task, `Tests:` comes before `Approach:`** —
tests drive implementation, not the other way around. Use red-green-refactor
with separate commits when the change is non-trivial.

**Every task must declare `Depends on:` explicitly** — list prior task IDs
or `none`. Don't omit the field; "obvious from order" is the failure mode
that hides serial-by-default thinking. `none` is a valid and common answer.

### T1a: Package scaffolds + adapter-contract `adapter.schema.json` + stdlib validator

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- `python -c "import agentbundle.build"` succeeds from a clean checkout
  (the `packages/agentbundle/` layout resolves under default `PYTHONPATH`
  or via editable install).
- `validate.py` accepts a minimal hand-rolled JSON-Schema document and
  rejects a malformed one covering each of the supported keywords:
  `type` (`object`, `array`, `string`, `integer`, `boolean`), `enum`,
  `required`, `pattern`, and `items` for arrays.
- A draft `adapter.schema.json` (object + enum + required) loads without error;
  a mutated copy (unknown `mode` enum member; missing `required` field)
  is rejected by `validate.py`.

**Approach:**
- Lay down `packages/agentbundle/` with `pyproject.toml` (stdlib-only,
  empty `dependencies = []`, sets `name = "agentbundle"` and the package
  layout). `packages/agentbundle/agentbundle/__init__.py` is the
  importable root.
- Scaffold the build module:
  - `packages/agentbundle/agentbundle/build/__init__.py` (exports
    `main` so `python -m agentbundle.build` works).
  - `packages/agentbundle/agentbundle/build/__main__.py` — argparse
    scaffold. `main()` configures a top-level parser with `--help`
    and an `argparse` subparser dispatch. **`validate <path>`
    subcommand lands here in T1a** (loads the contract at `<path>`
    via `tomllib`, validates against `adapter.schema.json`, exits 0 on valid
    and 1 on invalid with a one-line stderr message). T1b's
    Done-when invokes this subcommand against `adapter.toml`.
    Other subcommands (build, recipe dispatch, `--self`, `--check`,
    `--scaffold`) land in T6–T8.
  - `packages/agentbundle/agentbundle/build/contract.py` — the
    contract loader that adapters import (parses TOML via `tomllib`,
    returns typed dicts; no validation logic, that's `validate.py`).
  - `packages/agentbundle/agentbundle/build/adapters/__init__.py`
    (registry stub; adapters land in T2–T5).
  - `packages/agentbundle/agentbundle/build/validate.py` — the
    stdlib JSON-Schema subset validator. **Subset commitment:**
    `type` (object/array/string/integer/boolean), `enum`, `required`,
    `pattern` (via `re`), `items`, plus `properties` and
    `additionalProperties` for object recursion (load-bearing — every
    shipped schema relies on them). No `$ref`, no `oneOf`/`anyOf`, no
    format keywords. Documented in this Approach so reviewers know
    not to ask for more. Spec AC #6 names the same subset.
  - `packages/agentbundle/agentbundle/build/tests/fixtures/README.md`
    — fixture layout convention (one pack per subdirectory under
    `fixtures/packs/`, named for the test it serves).
- Author `docs/contracts/adapter.schema.json` (JSON-Schema-shaped,
  validated by `validate.py`) defining `[contract]`, `[primitive.*]`,
  `[adapter.<target>]` with `[[adapter.<target>.projection]]` array,
  `[frontmatter-mapping.*]`, `[frontmatter-default.*]`.
- Add `tools/build/build.py` as a thin shim:
  ```python
  from agentbundle.build import main
  main()
  ```

**Done when:** `python -m agentbundle.build --help` exits zero;
`python -m agentbundle.build validate --help` exits zero (the
subparser is wired); `validate.py`'s test file passes; `adapter.schema.json`
loads under `validate.py` against itself.

---

### T1b: Populate `adapter.toml` with every (primitive × adapter) pair

**Depends on:** T1a

**Verification mode:** TDD.

**Tests:**
- Loading `docs/contracts/adapter.toml` with `tomllib` and
  validating against `adapter.schema.json` returns no errors (verifies AC 1).
- Every (5 primitives × 4 adapters) = 20 pairs appears in the contract
  as a `[[adapter.<target>.projection]]` table; the test enumerates the
  expected set and asserts no missing pair, no extra.
- The `mode` enum in `adapter.schema.json` contains exactly the seven RFC-0001
  modes; a contract entry with any other mode value is rejected
  (verifies AC 2).
- Every `[[adapter.<t>.projection]]` table in `adapter.toml` carries
  an `on-conflict` value drawn from the legal set
  (`prompt-then-preserve`, `prompt-then-overwrite`,
  `preserve-outside-block`, `merge-managed-key-only`,
  `overwrite-without-prompt`) — and matches the per-mode default
  unless explicitly overridden (verifies AC 2).
- The `hook-wiring` primitive's `source-path` is
  `.apm/hook-wiring/` (one TOML file per hook listing the `[hooks]`
  entries to merge into `.claude/settings.local.json` for Claude
  Code's `merge-json` mode).
- The `command` primitive's `source-path` is `.apm/commands/`; the
  Claude Code projection is `direct-file` to `.claude/commands/`;
  Copilot / Codex / Kiro projections are `dropped`.
- `frontmatter-mapping` table for `kiro-agent-frontmatter-v0.9`
  validates against the schema; a `frontmatter-default` table for
  Copilot's `applyTo: "**"` validates and is structurally distinct
  from `frontmatter-mapping` (mapping = rewrite rules, default =
  inject when missing).

**Approach:**
- Populate `docs/contracts/adapter.toml`:
  - `[primitive.skill]`, `[primitive.agent]`, `[primitive.hook-body]`,
    `[primitive.hook-wiring]`, `[primitive.command]` — each with its
    `source-path`.
  - Four `[adapter.<target>]` blocks, each with five
    `[[adapter.<target>.projection]]` entries (one per primitive).
    Per the spec's projection table.
  - `[frontmatter-mapping.kiro-agent-frontmatter-v0.9]` table.
  - `[frontmatter-default.copilot-instruction]` table.
- Author `packages/agentbundle/agentbundle/build/tests/test_contract.py`
  — the contract-validation test suite.

**Done when:** `python -m agentbundle.build validate
docs/contracts/adapter.toml` exits zero, and every test
in `test_contract.py` passes.

---

### T1c: `pack.schema.json` + `plugin-manifest.schema.json`

**Depends on:** T1a

**Verification mode:** TDD.

**Tests:**
- `pack.schema.json` accepts an example `pack.toml` modeled on
  RFC-0001's `governance-extras` recommended-on-core example
  (verifies AC 3).
- `pack.schema.json` rejects a `pack.toml` missing `[pack]`.
- `pack.schema.json` rejects a `pack.toml` whose `[pack.adaptation]
  infer-from` value is a non-string (shape-only check; the semantic
  set of legal values lives in the `adapt-to-project` skill, out of
  scope here).
- `pack.schema.json` accepts a `pack.toml` *without* a
  `[pack.dependencies.required]` array — the field is optional
  (negative-case companion: missing-optional ≠ malformed).
- `pack.schema.json` accepts a `pack.toml` whose `[pack.seeds]`
  entries are relative-path strings (e.g. `"AGENTS.md"`,
  `"docs/CHARTER.md"`), and rejects one whose `[pack.seeds]` entry
  is an absolute path (e.g. `"/etc/foo"`) or a non-string (e.g. an
  inline table). Verifies the `[pack.seeds]` shape clause of AC 3.
- `plugin-manifest.schema.json` accepts a minimal hand-authored
  `.claude-plugin/plugin.json` (verifies AC 4).

**Approach:**
- Author `docs/contracts/pack.schema.json` capturing the
  `[pack]`, `[pack.dependencies]` (with `required`/`recommended`/
  `conflicts` arrays of `{catalogue, pack, version}` objects),
  `[pack.adaptation]` (substitutions + augmentation-points), and
  `[pack.seeds]` tables.
- Author `docs/contracts/plugin-manifest.schema.json` for
  `.claude-plugin/plugin.json`.
- Author the new tests in two **new** files —
  `packages/agentbundle/agentbundle/build/tests/test_pack_schema.py` and
  `test_plugin_manifest_schema.py`. **Do not extend `test_contract.py`**
  — that file is owned by T1b; touching it from T1c would create a merge
  conflict between parallel-dispatched T1b and T1c worktrees (the work-loop
  treats merge conflicts as "tasks weren't actually independent" and
  forces re-plan). Two new files keeps the file-owner boundary clean.

**Done when:** all schema-validation tests pass.

---

### T2: Claude Code adapter projects every primitive to its declared output

**Depends on:** T1b

**Verification mode:** TDD (per spec's Testing Strategy — per-adapter
projection rules).

**Tests:**
- A `skill` primitive at `packs/<p>/.apm/skills/foo/` projects to
  `.claude/skills/foo/` with full directory preservation
  (`direct-directory` mode).
- An `agent` primitive at `packs/<p>/.apm/agents/bar.md` projects to
  `.claude/agents/bar.md` (`direct-file`); frontmatter passes through
  unchanged (Claude-Code-shape is the source shape).
- A `hook-body` primitive at `packs/<p>/.apm/hooks/baz.sh` projects to
  `tools/hooks/baz.sh` (`direct-file`); the `.sh` extension is
  preserved byte-for-byte.
- A `hook-body` primitive at `packs/<p>/.apm/hooks/baz.py` projects to
  `tools/hooks/baz.py` (`direct-file`); the `.py` extension is
  preserved byte-for-byte. No conversion between extensions.
- A `hook-wiring` primitive at `packs/<p>/.apm/hook-wiring/baz.toml`
  merges under the `hooks` key of `.claude/settings.local.json`
  (`merge-json`) and never touches other keys (on-conflict
  `merge-managed-key-only`).
- A `command` primitive at `packs/<p>/.apm/commands/qux.md` projects
  to `.claude/commands/qux.md` (`direct-file`).
- Idempotence: running the adapter twice against the same fixture
  produces byte-identical output for both `direct-file` and
  `merge-json` projections (the `settings.local.json` merge is
  deterministic).

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/claude_code.py` —
  single module exporting `project(pack_path, contract, output_root)`.
  Reads the `claude-code` adapter block, iterates source primitives,
  copies or merges per rule.
- `packages/agentbundle/agentbundle/build/tests/test_adapter_claude_code.py`
  drives it against fixture packs under
  `packages/agentbundle/agentbundle/build/tests/fixtures/`.

**Done when:** every test in `test_adapter_claude_code.py` is green
and the adapter reads its rules only from the contract (no hardcoded
paths).

---

### T3: Kiro adapter projects skills, agents (with frontmatter mapping), and degrades hook wiring

**Depends on:** T1b

**Verification mode:** TDD.

**Tests:**
- A `skill` primitive projects to `.kiro/skills/<name>/`
  (`direct-directory`).
- An `agent` primitive's frontmatter is rewritten via the
  `kiro-agent-frontmatter-v0.9` mapping from the contract (no
  hardcoded mapping in Python); `tools` field normalized via the
  declared `normalize = "to-list"` rule.
- A `hook-wiring` primitive in `degraded-info-log` mode emits an
  `[info]` log line at build time to stderr and writes no file.
- A `hook-body` primitive projects to `tools/hooks/<name>.{sh,py}`
  (extension preserved; consistent across adapters per RFC §
  Per-IDE adapter contracts).
- A `command` primitive is `dropped` (no output file, no warning).

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/kiro.py`.
  Frontmatter rewrite reads the named mapping table from the contract;
  the adapter has no per-target field dictionary.
- `packages/agentbundle/agentbundle/build/tests/test_adapter_kiro.py`
  drives it; one fixture pack carries `hook-wiring` to exercise the
  degraded path.

**Done when:** every test in `test_adapter_kiro.py` is green.

---

### T4: Copilot adapter projects skills to per-file instructions and drops subagents

**Depends on:** T1b

**Verification mode:** TDD.

**Tests:**
- A `skill` primitive projects to
  `.github/instructions/<name>.instructions.md`
  (`instruction-file` mode) with the default `applyTo: "**"`
  frontmatter from the contract's `frontmatter-default` table.
- An `agent` primitive in `dropped` mode produces no output file and
  no warning (it's an explicit no-op).
- A `hook-body` primitive projects to `tools/hooks/<name>.{sh,py}`
  (extension preserved); `hook-wiring` is `dropped`; `command` is
  `dropped`.

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/copilot.py`.
  Default frontmatter comes from the contract's `frontmatter-default`
  table — adapter does not hardcode `applyTo`.
- `packages/agentbundle/agentbundle/build/tests/test_adapter_copilot.py`.

**Done when:** every test in `test_adapter_copilot.py` is green.

---

### T5: Codex adapter inlines skill descriptions into a managed block in AGENTS.md

**Depends on:** T1b

**Verification mode:** TDD.

**Tests:**
- A `skill` primitive's description appears between
  `<!-- agent-skills:start -->` and `<!-- agent-skills:end -->` in
  the projected `AGENTS.md` (`managed-block-inline` mode).
- Content *outside* the managed block in a pre-existing `AGENTS.md`
  is preserved byte-for-byte (`preserve-outside-block` on-conflict).
- `agent`, `hook-wiring`, and `command` primitives in `dropped` mode
  produce no output.
- A `hook-body` primitive projects to `tools/hooks/<name>.{sh,py}`
  (`direct-file`; extension preserved). Codex matches the cross-adapter
  hook-body convention.
- Re-running the adapter is idempotent: the block content stabilizes
  on the second run (byte-identical output).

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/codex.py`. Delimiter
  strings come from the contract's `managed-block-delimiter-start` /
  `-end` fields.
- `packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py`.

**Done when:** every test in `test_adapter_codex.py` is green.

---

### T6: Build pipeline reads recipes and dispatches per-pack rendering

**Depends on:** T2, T3, T4, T5

**Verification mode:** Goal-based for the artifact-shape tests
(each recipe's output directory exists and matches the expected layout);
TDD for the recipe loader's unit invariants (unknown adapter target
raises; unknown recipe type raises; pack-internal name collisions are
rejected).

**Tests:**
- Goal: `python -m agentbundle.build --recipe per-pack-claude-plugin`
  against a single-pack fixture produces a `dist/claude-plugins/<pack>/`
  directory containing the pack's hand-authored
  `.claude-plugin/plugin.json` (copied unmodified from the fixture's
  `<pack>/.claude-plugin/plugin.json`) and the projected `.apm/`
  content. Verifies AC 4's "copies unmodified" half (the schema half
  is verified by T1c).
- Goal: `python -m agentbundle.build --recipe per-pack-apm-package`
  produces `dist/apm/<pack>/` with a generated `apm.yml` derived from
  `pack.toml`.
- Goal: `python -m agentbundle.build --recipe marketplace` aggregates
  every rendered per-pack plugin under `dist/claude-plugins/*/` into a
  single `dist/claude-plugins/marketplace.json`.
- Unit: pack-internal name collision (two skills, agents, hooks,
  hook-wiring files, or commands with the same local name inside one
  pack) is rejected by a pre-render validation step with non-zero exit
  and a stderr message naming both paths (verifies AC 9 — the rule is
  pipeline-level, not per-adapter).
- Unit: unknown recipe name → non-zero exit + stderr message.
  Triggered by passing `--recipe bogus-recipe` on the command line
  (no fixture file needed).
- Unit: unknown adapter target in a recipe → non-zero exit + stderr.
  Triggered by a hand-rolled fixture recipe at
  `packages/agentbundle/agentbundle/build/tests/fixtures/recipes/bogus-target.toml`
  whose `target = "bogus"` value isn't in the contract's adapter set;
  the test loads this recipe explicitly. Defensive — protects against
  future hand-edits of shipped recipes.
- Goal (RFC-0002 recipe — `per-pack-overlay`): loading
  `per-pack-overlay.toml` against a fixture pack produces an overlay
  description naming the pack's `.apm/` content and `seeds/` list as
  the units to be projected into the working tree. Asserts expansion
  shape, not on-disk overlay (T7 owns the on-disk side).
- Goal (RFC-0002 recipe — `composite-agents-md`): loading
  `composite-agents-md.toml` against two fixture packs each carrying
  a `seeds/AGENTS.fragment.md` produces a composed `AGENTS.md`
  description whose body concatenates both fragments in declared
  order. Asserts expansion shape.
- Goal (RFC-0002 recipe — `composite-marketplace`): loading
  `composite-marketplace.toml` against three fixture per-pack
  `.claude-plugin/plugin.json` files produces a composite
  marketplace description enumerating all three. Asserts expansion
  shape; distinct from the `marketplace` recipe's aggregation goal
  above (RFC-0001's recipe aggregates rendered output;
  `composite-marketplace` composes the self-host marketplace).
- Goal (empty-pack edge case): a fixture pack missing one or more
  `.apm/<primitive>/` directories (e.g. `governance-extras` with no
  `command/`) drives the pipeline to emit no error and no output for
  the absent primitives — adapters skip the missing directory
  silently rather than failing.

**Approach:**
- `packages/agentbundle/agentbundle/build/main.py` (or extend
  `__init__.py`) — recipe loader (TOML), pack discovery via glob
  `packs/*/`, adapter dispatch keyed by `[recipe.adapter] target`.
- `packages/agentbundle/agentbundle/build/recipes/per-pack-claude-plugin.toml`,
  `per-pack-apm-package.toml`, `marketplace.toml`,
  `per-pack-overlay.toml`, `composite-agents-md.toml`,
  `composite-marketplace.toml` — the six enumerated recipe types.
  (T7 exercises the self-host trio; T6 lands the recipe files.)
- `packages/agentbundle/agentbundle/build/tests/test_pipeline.py`
  covers the dispatcher's unit invariants and the artifact-shape goals.

**Done when:** all three RFC-0001 recipes round-trip against fixture
packs; the three RFC-0002 recipe files land and have unit tests
verifying their expansion shape; the empty-pack edge case passes; the
unknown-recipe path exits non-zero.

---

### T7: `make build --self` writes to working tree; `--dry-run` emits a diff against on-disk

**Depends on:** T6

**Verification mode:** Goal-based check (the artifact diff against the
working tree is the verification artifact).

**Tests:**
- Goal: on a clean source tree, the self-host dry-run produces zero
  diff lines and exits zero.
- Goal: after mutating one source file in a temp checkout, the dry-run
  exits non-zero and the stderr names that file's projected path with
  the per-file drift.
- Goal: the dry-run never modifies the working tree (verified by
  comparing `git status` before and after).
- Goal (marker resolution): a fixture source file containing
  `<adapt:project-name>` plus a fixture `.adapt-discovery.toml`
  mapping `project-name = "demo"` makes `make build --self` (not
  `--dry-run`) project a file containing the literal string `demo`
  — markers are resolved during `--self` writes. Counter-test: plain
  `make build` (no `--self`) against the same fixture copies the
  marker through unchanged. Verifies the `<adapt:NAME>` clause of
  the new `make build --self` AC.
- Unit (TDD): `--self` writes use each adapter's *declared* on-conflict
  mode (e.g. `merge-managed-key-only` for Claude Code's
  `settings.local.json`); `--force` bypasses the dirty-tree refusal
  only — it never overrides the per-adapter on-conflict policy.
- Goal: `make build --self` against a dirty fixture worktree exits
  non-zero with stderr naming the refusal; the same command with
  `--force` proceeds. The test constructs the dirty worktree via
  `tempfile.TemporaryDirectory()` initialised as `git init`, with the
  fixture pack copied in, one tracked file `git add`/`git commit`-ed,
  then modified in place so `git status --porcelain` is non-empty.
  The build CLI's dirty-tree detection shells out to `git status
  --porcelain` against the working tree it would project into.
  Verifies the dirty-tree refusal clause of AC #11.

**Approach:**
- Add `--self`, `--dry-run`, and `--force` flags to the build CLI
  (`agentbundle.build`).
- Self-host mode renders to a `tempfile.TemporaryDirectory()` and
  diffs against the repo's on-disk projection paths
  (`.claude/skills/`, `.claude/agents/`, `tools/hooks/`,
  `AGENTS.md`, `.claude/commands/`). The diff output names per-file
  drift one line at a time.
- `--self` is the *one authorised mode* that runs `<adapt:NAME>`
  marker resolution as a final build step (per spec Boundaries §
  Never do). **T7 ships the substitution pass itself** — load
  `.adapt-discovery.toml` via `tomllib`, walk rendered output, and
  `str.replace('<adapt:NAME>', value)` per key/value pair. T7 does
  *not* implement the materialisation of `.adapt-discovery.toml`
  from this repo's concrete values; that lives in `adapt-to-project`
  (out of scope here). The fixture for the marker-resolution test
  ships a hand-authored `.adapt-discovery.toml` so T7's consumer
  path is exercised without the producer.
- Author `packages/agentbundle/agentbundle/build/tests/test_self_host_check.py`
  — the cross-cutting self-host integration test. T8 imports this
  file as a regression gate; T7 owns it.
- Comparison-rule unit tests (LF normalisation, mode-bit comparison,
  symlink-via-lstat) are owned by sibling spec `self-hosting`; this
  task imports them as a regression gate, doesn't duplicate. The
  dry-run diff in this task uses whatever comparison rules
  `self-hosting` defines for its detector.

**Done when:** test cases above pass; `git status` shows no changes
after `python -m agentbundle.build --self --dry-run`. The
marker-resolution test and the real-write `--self` cases each run in
a temp checkout that's discarded after assertion, so the working
tree's `git status` is unaffected.

---

### T8: `Makefile` exposes the seven subcommands and `make build --check` rounds-trip green

**Depends on:** T6, T7

**Verification mode:** Goal-based check (per spec's Testing Strategy —
end-to-end build).

**Tests:**
- Goal: `make build` on the four reference packs produces the
  expected directory shape (verifies AC 7) — the integration test
  at `packages/agentbundle/agentbundle/build/tests/test_end_to_end_build.py`
  is the verification artifact. **T8 authors this file.**
- Goal: `make build --check` exits zero on the clean tree (verifies
  AC 10) — imports `test_self_host_check.py` (authored by T7) as a
  regression gate.
- Goal: plain `make build` (no flags, no `PACK=`, no `RECIPE=`)
  produces only `dist/apm/<pack>/`, `dist/claude-plugins/<pack>/`,
  and `dist/claude-plugins/marketplace.json`; the working tree is
  byte-identical before and after (verified by `git status
  --porcelain` returning the same content). The three self-host
  recipes (`per-pack-overlay`, `composite-agents-md`,
  `composite-marketplace`) are *not* invoked. Verifies the new
  default-recipe AC.
- `make build PACK=core` limits output to the `core` pack only.
- `make build RECIPE=per-pack-claude-plugin` runs that recipe across
  all packs.
- `make build --scaffold OUTPUT=<tmp>` drops the `core` pack's
  `seeds/` into the named output directory.
- Unknown subcommand or flag → non-zero exit with stderr.

**Approach:**
- Author `Makefile` targets that shell out to `python3 -m
  agentbundle.build` with the matching flags. The Makefile is the
  thin user surface; argument parsing happens in `agentbundle.build`.
- Extend the build CLI arg parser with `--check`, `--scaffold`,
  `PACK=`, `RECIPE=` (Make-style passthrough).
- Author `packages/agentbundle/agentbundle/build/tests/test_end_to_end_build.py`
  — drives the full pipeline against four reference fixture packs at
  `packages/agentbundle/agentbundle/build/tests/fixtures/packs/{core,governance-extras,user-guide-diataxis,monorepo-extras}/`.
  These fixtures ship with this spec (one `.apm/skills/<one>/`,
  one `pack.toml`, and one hand-authored `.claude-plugin/plugin.json`
  each — minimal but realistic). **Materialisation of production
  packs in a top-level `packs/` directory is out of scope** per
  spec AC #7's amended wording (the migration is RFC-0001's F-dist
  follow-on). The fixtures exercise the contract end-to-end without
  pulling in the broader pack-migration work.

**Done when:** `make build && make build --check` exits zero on the
clean tree; mutating a source file makes `make build --check` exit
non-zero.

---

### T9: Stdlib-only enforcement and no-new-top-level audit

**Depends on:** T1a (the enforcement lands with the package scaffolds)

**Verification mode:** Goal-based check (per spec's Boundaries — Never do
floor).

**Tests:**
- Goal: a `pre-pr.sh` hook runs the stdlib-import audit against
  `packages/agentbundle/agentbundle/build/` and exits non-zero on any
  non-stdlib import. **The stderr message names the offending file
  and line** (e.g. `agentbundle/build/foo.py:3: non-stdlib import 'yaml'`)
  so the failure is actionable, matching the analogous "stderr message
  naming both paths" in AC 9. The CI workflow runs the same hook. A
  wrong `import yaml` surfaces in the offending PR — *not* at
  end-of-stream. (Verifies AC 5.)
- Goal: the no-new-top-level audit runs as part of `pre-pr.sh`:
  `comm -23 <(git ls-tree -d --name-only HEAD | sort) <(git ls-tree
  -d --name-only "$(git merge-base HEAD main)" | sort)` returns empty
  (verifies the no-new-top-level AC). The `-d` flag scopes the audit
  to directories so new root-level files like `Makefile` don't trip
  it. The comparison is against the merge-base so the audit stays
  correct after a merge from main into the feature branch (a plain
  `main` comparison would silently pass in that case). `dist/` is
  git-ignored and doesn't count. Both inputs are sorted because
  `comm` requires sorted input.

**Approach:**
- Author `tools/lint-build.sh` with two checks: the stdlib-import
  audit (walks every `.py` under
  `packages/agentbundle/agentbundle/build/` **except**
  `packages/agentbundle/agentbundle/build/tests/fixtures/` — fixture
  files are test data and may include realistic hook payloads that
  import third-party packages; pipeline code is the only thing the
  stdlib-only rule binds — parses imports, asserts every top-level
  package is in `sys.stdlib_module_names`) and the top-level-directory
  audit (uses `git ls-tree -d --name-only` against the merge-base of
  HEAD and main, per amended AC #12 — `-d` scopes to directories so
  new root-level files like `Makefile` don't trip the check).
- Wire `tools/lint-build.sh` into `pre-pr.sh` (an existing hook in
  this repo) so it runs on every PR. Same script runs in CI.
- Authoring this task at T1a-time (rather than after T6/T7/T8) means
  any stray non-stdlib import in T2–T8 surfaces in that PR.

**Done when:** `tools/lint-build.sh` exits zero on a clean tree;
introducing a non-stdlib import in a fixture file makes it exit
non-zero.

---

### T10: `adapter.schema.json` + `adapter.toml` gain `[scope]` table; `[contract] version` 0.1 → 0.2

**Depends on:** none (additive against T1a/T1b output; touches the
contract files only).

**Verification mode:** TDD.

**Tests:**
- `adapter.schema.json` accepts a `[scope]` block declaring
  `repo = "."`, `user = "~"`, and
  `allowed-prefixes.user = [".claude/", ".agent-ready/"]`; rejects
  `allowed-prefixes.user` values of `["/"]`, `[""]`, `["../"]`,
  `[".."]`, `["no-trailing-slash"]`, `["/begins-with-slash/"]`, and
  `[]` (one assertion per case, named for readability). Verifies the
  `[scope]` half of new AC #14.
- `docs/contracts/adapter.toml` loads with
  `[contract] version = "0.2"` and the
  `[adapter."claude-code".scope]` block above (two prefixes:
  `.claude/` and `.agent-ready/`); validates against the
  updated schema.
- The other three reference adapters (`kiro`, `copilot`, `codex`)
  omit `[scope]` — the schema accepts them as repo-only (omitting
  `[scope]` is legal and means "repo only" per § *Install-scope
  dimension*).

**Approach:**
- Extend `docs/contracts/adapter.schema.json`:
  - At each `[adapter.<name>]` block, add an optional `scope` property
    of type object with required keys `repo` and `user` (both
    strings) and an optional `allowed-prefixes` property whose values
    are non-empty arrays of strings.
  - Encode the per-string constraints — non-empty, no leading `/`,
    not `"/"`, no `..` segment, trailing `/` — in a `pattern` keyword
    on each array's `items`. The validator's regex subset is enough
    (T1a's commitment: `pattern` is supported).
- Bump `[contract] version` in `adapter.toml` from `"0.1"` to `"0.2"`.
  Add `[adapter."claude-code".scope]` as shown in § *Install-scope
  dimension*.
- New tests land in
  `packages/agentbundle/agentbundle/build/tests/test_contract_scope.py`
  (a new file — avoids merge churn against the existing
  `test_contract.py` which T1b owns).

**Done when:** schema tests green; the v0.2 contract validates against
the v0.2 schema.

---

### T11: `pack.schema.json` requires `[pack.install]` under contract v0.2

**Depends on:** none (additive; touches the schema and its tests).

**Verification mode:** TDD.

**Tests:**
- A v0.2 pack (declares `[pack.adapter-contract] version = "0.2"`)
  with no `[pack.install]` table is rejected.
- A v0.2 pack with `[pack.install] default-scope = "repo",
  allowed-scopes = ["repo"]` is accepted.
- A v0.2 pack with `[pack.install] default-scope = "user",
  allowed-scopes = ["repo"]` is rejected by the
  `default-scope ∈ allowed-scopes` invariant.
- A v0.2 pack omitting `allowed-scopes` (only `default-scope`
  declared) is accepted with the implied
  `allowed-scopes = [default-scope]` — verified by reading the parsed
  result and asserting the default landed.
- A v0.1 pack (declares `[pack.adapter-contract] version = "0.1"` or
  omits the field) without `[pack.install]` is accepted (legacy).
- A v0.1 pack carrying a stray `[pack.install]` table is accepted —
  the table is ignored at CLI consumption time (per § *Install-scope
  dimension* — implied defaults apply uniformly to all v0.1 packs).

**Approach:**
- Extend `docs/contracts/pack.schema.json` with two jsonschema
  `if`/`then` blocks under `[pack]`:
  1. `if [pack.adapter-contract] version == "0.2" then require
     [pack.install]`.
  2. `if [pack.install] is present then require default-scope and
     enforce default-scope ∈ allowed-scopes`.
- New tests at
  `packages/agentbundle/agentbundle/build/tests/test_pack_schema_install.py`.
  Do not extend `test_pack_schema.py` (owned by T1c — same merge-
  conflict reasoning as T1c's two-new-files rule).

**Done when:** all six test rows green.

---

### T12: `validate` runs the three user-scope refusal rails (A/B/C)

**Depends on:** T10, T11.

**Verification mode:** TDD.

**Tests:**
- *Rail A — seeds.* A fixture pack containing a non-empty `seeds/`
  directory and declaring `"user" ∈ allowed-scopes` is rejected by
  `agentbundle validate` with stderr naming the pack and the
  `seeds/` path. A counter-fixture (same pack with `seeds/` empty,
  or with `allowed-scopes = ["repo"]`) is accepted.
- *Rail B — hooks.* A fixture pack containing
  `.apm/hooks/<name>.sh` (a `hook-body` primitive) and declaring
  `"user" ∈ allowed-scopes` is rejected with stderr naming the pack
  and the hook path. Same for a pack with
  `.apm/hook-wiring/<name>.toml`. A counter-fixture without hook
  primitives is accepted.
- *Rail C — markers.* A fixture pack containing a primitive file
  with `<adapt:PROJECT_NAME>` somewhere in its bytes and declaring
  `"user" ∈ allowed-scopes` is rejected with stderr naming the pack
  and the first offending file path. The grep must match
  `<adapt:[A-Z_][A-Z0-9_]*>` only — `<adapt:lowercase>` and
  `<ADAPT:NAME>` (wrong prefix) are not matches. A counter-fixture
  with the same marker in a `seeds/` file (not a primitive) is
  accepted (Rail A already refused user-scope above; Rail C's input
  excludes `seeds/`).
- *Repo-only packs are not inspected by Rail C.* A pack declaring
  `allowed-scopes = ["repo"]` with `<adapt:NAME>` markers in
  `.apm/skills/` is accepted by `validate` (the rail's scope clause
  fires only when `"user" ∈ allowed-scopes`). Verifies the *Scope of
  the rail* clause in § *Install-scope dimension*.
- *Binary files skipped.* A pack carrying a non-UTF-8 file under
  `.apm/skills/` (constructed via raw bytes in the fixture) is
  accepted by Rail C — non-UTF-8 files are skipped silently.

**Approach:**
- Add a new module
  `packages/agentbundle/agentbundle/build/scope_rails.py` exporting
  `check_seeds(pack_path, allowed_scopes) -> Result`,
  `check_hooks(pack_manifest, allowed_scopes) -> Result`, and
  `check_markers(pack_path, allowed_scopes) -> Result`. Each returns
  `Ok` or `Refused(pack, offender_path)`. The marker grep walks
  `.apm/skills/`, `.apm/agents/`, `.apm/commands/` recursively, opens
  each file with `errors="strict"` and catches `UnicodeDecodeError`
  to skip non-UTF-8.
- Wire `validate` (in `agentbundle/build/__main__.py`) to call all
  three rails after schema validation. The CLI's `install` subcommand
  re-runs the same module against resolved pack content (the wiring
  lives in sibling spec's task T19 — *Dual-scope install conflict +
  `--force` + `installed:` output* — which carries the install-time
  rail re-check explicitly in its dependency list).
- New tests at
  `packages/agentbundle/agentbundle/build/tests/test_scope_rails.py`.

**Done when:** every test row above is green; `agentbundle validate`
runs the three rails sequentially and reports the first offender per
rail.

---

### T13: `.agent-ready-state.toml` schema v0.2 + `init-state --migrate` writer

**Depends on:** T10 (the contract bump is the trigger for the state-
file bump).

**Verification mode:** TDD.

**Tests:**
- *Read v0.1.* `agentbundle.config.load_state` reads a
  `schema-version = "0.1"` fixture file and returns all entries with
  an implicit `scope = "repo"` column on every `[pack.<name>]` entry
  (no migration forced at read).
- *Refuse v0.1 write.* Any write-capable invocation against the v0.1
  fixture (the helper is called by `install`, `uninstall`, `upgrade`,
  `init-state`) exits non-zero with stderr `state file at <path> is
  schema-version 0.1; run 'agentbundle init-state --migrate' first`.
  The test parametrises over the four write-capable invocations.
- *Migrate v0.1 → v0.2.* `agentbundle init-state --migrate` against
  the v0.1 fixture rewrites the file to v0.2: every `[pack.<name>]`
  gains `scope = "repo"`; `schema-version` flips to `"0.2"`; all
  other fields are byte-identical to the v0.1 originals.
- *Migrate is idempotent.* Running `init-state --migrate` twice
  against the same v0.2 file is a no-op (byte-identical output, exit
  zero).
- *User-scope state file location.* When a write resolves to user
  scope, the state file is `~/.agent-ready/state.toml` (a namespaced
  dot-directory under `$HOME`, not a bare `~/.agent-ready-state.toml`).
  The directory is created with `0o700` permissions if absent. Test
  asserts the resolved path and the permissions bit.

**Approach:**
- Extend `agentbundle.config.load_state` to branch on
  `schema-version`: read 0.1 with implicit-repo-scope; read 0.2 with
  explicit `scope` column.
- Add `agentbundle.config.save_state` and route every write through
  the refuse-and-explain when `schema-version` on disk is `"0.1"`.
  The refuse-and-explain message is shared across `install`,
  `uninstall`, `upgrade`, and (when called on an existing file)
  `init-state` without `--migrate`.
- Implement `init-state --migrate` in
  `agentbundle.commands.init_state` (the existing module from sibling
  spec T10): when `--migrate` is passed, read the v0.1 file, augment
  each `[pack.<name>]` with `scope = "repo"`, set
  `schema-version = "0.2"`, write atomically (tmp + `os.replace`).
- User-scope state-file directory creation lives in
  `agentbundle.safety.user_state_path()` (a helper that returns the
  resolved path and ensures the dot-directory exists).
- New tests at
  `packages/agentbundle/tests/test_state_v02.py` (under the CLI tests
  tree — state-file handling is consumed by CLI subcommands).

**Done when:** every test row above green; an adopter running
`init-state --migrate` against a v0.1 file gets a parseable v0.2 file
on disk and subsequent writes proceed.

---

### T14: Four shipped packs gain explicit `[pack.install]` + bump `[pack.adapter-contract] version` to `"0.2"`

**Depends on:** T10, T11 (the schema must accept the new shape
before the packs adopt it).

**Verification mode:** Goal-based check.

**Tests:**
- Goal: every `packs/{core,governance-extras,monorepo-extras,user-guide-diataxis}/pack.toml`
  parses with `tomllib` and validates against the updated
  `pack.schema.json` — `[pack.adapter-contract] version = "0.2"`,
  `[pack.install] default-scope = "repo"`,
  `[pack.install] allowed-scopes = ["repo"]`.
- Goal: `agentbundle validate packs/<pack>` exits zero for each of
  the four shipped packs against the v0.2 schema. The Rails A/B/C
  checks fire harmlessly — every shipped pack declares
  `allowed-scopes = ["repo"]`, so Rail C's scope clause never fires
  (the rail's input is empty by construction), Rail A passes
  trivially (the packs do carry `seeds/`, but `allowed-scopes` is
  `["repo"]`), and Rail B passes trivially (the `core` pack carries
  hooks, but `allowed-scopes` is `["repo"]`).

**Approach:**
- Edit each of the four `pack.toml` files to add the two stanzas
  exactly:
  ```toml
  [pack.adapter-contract]
  version = "0.2"

  [pack.install]
  default-scope = "repo"
  allowed-scopes = ["repo"]
  ```
- The values are written even though both are the built-in defaults
  (per new AC) — adopters reading the TOML see the constraint
  declared, not implied.
- No code change in this task — purely metadata.

**Done when:** all four packs validate against the v0.2 schema;
`agentbundle validate packs/<pack>` exits zero for each.

---

## Rollout

The pipeline ships once, behind no flag — it's developer tooling, not
runtime behavior. The first `make build` run produces `dist/` (added
to `.gitignore` as part of T6); CI starts running `make build --check`
once RFC-0002's spec wires it in. Reversible: removing
`packages/agentbundle/agentbundle/build/`,
`docs/contracts/`, and the `tools/build/build.py` shim
rolls everything back; no adopter has consumed an artifact yet (the
catalogue isn't published until follow-on work).

## Risks

- **JSON-Schema validation in stdlib.** Python's stdlib doesn't ship a
  draft-2020-12 validator. **Resolved:** T1a commits to a defined
  stdlib-only subset (object, array, string, integer, boolean, enum,
  required, pattern, items) and ships `validate.py` against that
  subset. Spec AC #6 names the same subset. No "fallback to type
  checks" — the subset is the contract.
- **Idempotence of `managed-block-inline`** *and* **`merge-json`**.
  Codex's inline-block mode and Claude Code's `settings.local.json`
  merge must converge in one run; otherwise `make build --check`
  oscillates on a clean tree. T5 and T2 both pin idempotence with
  byte-identical-output tests; if either fails, the relevant
  serialisation needs deterministic ordering (alpha by skill name for
  Codex; sorted JSON key order for Claude Code).
- **Frontmatter mapping for Kiro is the most fragile adapter rule.**
  Mapping table lives in the contract, but the adapter still has to
  apply it correctly across skill files with varying frontmatter
  shapes. T3's tests cover the documented mapping; surprises in
  real source primitives surface during T8's end-to-end run.
- **Production packs are out of scope.** This spec ships the pipeline
  and the fixtures it tests against; the migration of this repo's
  content into a top-level `packs/` directory is RFC-0001's F-dist
  follow-on. T8's end-to-end test runs against fixture packs at
  `packages/agentbundle/agentbundle/build/tests/fixtures/packs/`. When
  the F-dist migration lands, `make build` will pick up `packs/`
  alongside the fixtures with no pipeline change required (pack
  discovery is a glob).

## Changelog

- 2026-05-22: initial plan.
- 2026-05-22: incorporated adversarial review (CC1–CC6, B1–B6, C7–C15,
  N16–N20). T1 split into T1a/T1b/T1c; build code moved to
  `packages/agentbundle/agentbundle/build/`; `command` primitive added;
  Tier model and `.agent-ready-state.toml` schema pinned in spec;
  recipe set enumerated; T9 hoisted to run as a pre-PR hook.
- 2026-05-22: fix-pass 2 (3 Blockers, 9 Concerns, 3 Nits + cross-spec
  coordination patches A/B/C). Aligned validator subset between spec
  AC #6 and plan T1a; folded `validate <path>` subparser into T1a;
  added numbered ACs for `make build --self` and the six-recipe set;
  weakened `infer-from` schema check to shape-only; added `[pack.seeds]`
  schema test pair; added T6 tests for RFC-0002 recipes and the
  empty-pack edge case; added T7 marker-resolution test; ceded
  comparison-rule unit tests to sibling `self-hosting`; fixed
  `comm -23` to sort inputs.
- 2026-05-22: pre-EXECUTE review pass 2 (2 Blockers, 4 Concerns).
  Hardened the no-new-top-level audit to `git ls-tree -d` (directories
  only) so the new root-level `Makefile` doesn't trip the check.
  Synced AC #12 with T9 (both now name the `-d` + merge-base form).
  Replaced the lingering `packs/` reference in § Construction tests
  with the fixture-pack path. Added an AC and a T8 test pinning the
  default-recipe behaviour (plain `make build` excludes the
  self-host trio; working tree unchanged after the run). Scoped
  T9's import audit to exclude `tests/fixtures/` so realistic hook
  fixtures don't trip the stdlib-only rule against pipeline code.
  Pinned T7's dirty-tree fixture construction (`tempfile` + `git
  init`) so the AC #11 refusal test is feasible.
- 2026-05-22: pre-EXECUTE review pass 1 (3 Blockers, 8 Concerns, 4 Nits).
  Resolved `packs/` contradiction by amending AC #7 to point at
  fixture packs and explicitly scoping out the production-pack
  migration. Pinned the Tier model as schema-only in this spec
  (lifecycle behaviour lives in sibling `self-hosting` and RFC-0003's
  CLI). Added § "Projection modes (defined)" so AC #2's enum is
  defined-by-reference inside this spec. Added § "Default-recipe
  behaviour" pinning plain `make build` to the three RFC-0001 recipes
  (RFC-0002 recipes fire only under `--self`). Extended AC #11 to
  require a dirty-tree refusal test and named T7 as the owner of the
  `<adapt:NAME>` substitution pass (`.adapt-discovery.toml`
  materialisation stays with `adapt-to-project`). Renamed T7 to
  reflect the dual scope (`--self` writes; `--dry-run` diffs).
  Locked T1c to new test files (no extension of `test_contract.py`,
  which would conflict with parallel-dispatched T1b). Added T9
  stderr file:line requirement and pinned the no-new-top-level audit
  to `git merge-base HEAD main` so the check survives merges from
  main. Cited AC 4 in T6's first goal test. Updated the Risks section
  to reflect the new scope.
- 2026-05-22: adapter contract files moved from
  `docs/specs/adapter-contract/` to `docs/contracts/` with
  `<name>.schema.json` filenames (`adapter.toml`, `adapter.schema.json`,
  `pack.schema.json`, `plugin-manifest.schema.json`). Paths and
  bare-filename references updated; field semantics unchanged. See
  [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments).
- 2026-05-23: v0.2 amendment per
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md). Spec grows
  the § *Install-scope dimension* section pinning the scope enum,
  the `[scope]` table on the adapter contract, the `[pack.install]`
  table on `pack.toml`, the three contract-level user-scope refusal
  rails (seeds / hooks / marker), the path-jail per scope, the
  state-file v0.2 schema with explicit `scope` column, and the
  `init-state --migrate` refuse-and-explain. Five new ACs appended
  (#14 adapter.toml + adapter.schema.json `[scope]`; #15
  pack.schema.json `[pack.install]`; #16 validate Rails A/B/C; #17
  state-file v0.2 + `init-state --migrate`; #18 four shipped packs
  declare `[pack.install]`). Boundaries gain
  scope-rail enforcement + `~`-expansion refusal + the no-`global`
  + no-silent-rewrite + no-user-scope-hook-bearing-pack rules.
  Plan tasks T10 (adapter.schema.json + adapter.toml gain `[scope]`
  + version bump), T11 (pack.schema.json requires `[pack.install]`
  under v0.2 with cross-field invariant), T12 (validate runs Rails
  A/B/C), T13 (state-file v0.2 + `init-state --migrate`), T14
  (four shipped packs adopt the new metadata) added. CLI surface
  (the `--scope` flag, dual-state-file walking, `installed: <pack>
  @ <scope>` output) is owned by the sibling
  [`agent-spec-cli`](../agent-spec-cli/spec.md) spec's amendment.
