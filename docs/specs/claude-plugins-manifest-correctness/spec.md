# Spec: Claude-plugins manifest correctness

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0072](../../adr/0072-derived-plugin-manifest-mirrors-upstream-schema.md)
- **Contract:** `contracts/plugin-manifest.derived.schema.json`, `contracts/plugin-manifest.schema.json`, `contracts/marketplace-entry.schema.json` (new, T0)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who runs `/plugin marketplace add eugenelim/agent-ready-repo` and
installs a pack gets that pack's skills, agents, and commands. Today they get an
empty plugin: the install reports success and delivers nothing.

Two independent defects cause it, each sufficient on its own. A third condition
let both ship undetected: **no gate validates a marketplace plugin entry.** The
derived-manifest schema never sees a `source` object — `build/main.py:545-546`
pops `source` and `category` before `validate_derived_plugin_manifest_dict` — and
`catalogue_tooling/verify.py:594` validates only per-pack `plugin.json` under
`dist/claude-plugins`, checking `marketplace.json` for nothing but a stray `hooks`
key. The proof is on disk: every entry in `.claude-plugin/marketplace.json`
carries `category`, which the derived schema forbids under
`additionalProperties: false`. If entries were validated, all 21 would fail today.

So the fix is three-part: close the validation gap, correct the source shape, and
correct the component layout.

## Boundaries

### Always do

- Fix the generators, then regenerate with `make build-self`.
- Route component writes through the blessed projection helpers —
  `_project_direct_directory` for `skill`, `_project_direct_file` for `agent` and
  `command` — under the `_assert_under(per_pack_output, output_dir)` already
  applied at `build/main.py:498`. Never relocate an already-written tree with
  `shutil.move`/`copytree`, which bypasses the symlink guards K-0002 records.
- Verify against the real `claude` CLI in a throwaway `CLAUDE_CONFIG_DIR`.

### Ask first

- Changing `_DIST_BRANCH`, the dist-branch publishing model, or **repository
  settings** (branch protection, environments) — these are actions outside the
  diff and need the owner.
- Changing what packs contain, as opposed to where their files land.

### Never do

- Delete or weaken a regression test to make a gate pass. Tests pinning the old
  shape are re-pinned, not removed.
- Hand-edit `.claude-plugin/marketplace.json` or projected output.
- Widen `additionalProperties: false` on any manifest schema to make the new
  shape validate.
- Publish to `claude-plugins-dist` by hand. CI owns that on merge to `main`.
- **Add a third-party dependency to `agentbundle`.** `pyproject.toml:10`
  `dependencies = []` is the contract, and the validator is `build/validate.py`.
  This rail exists because the PLAN stubs reached for `jsonschema` — present on
  the author's machine, absent from CI — and four assertions became silent skips.

## Acceptance Criteria

- [x] **AC1 — Valid plugin source type.** `derive_projectable_subset`
  (`build/main.py:199`) emits
  `{"source": "git-subdir", "url": ..., "path": ..., "ref": ...}`; `branch` and
  `directory` appear in no emitted manifest. `url` is
  `https://github.com/<owner>/<name>.git`. An `http://` repository link **raises**
  — `_GITHUB_URL_RE` (`build/main.py:49-51`) is `^https?://` today and matches
  one. Tightening the regex alone is insufficient: a non-matching link currently
  yields *no `source` key at all* (pinned by `test_source_absent_for_non_github_url`,
  `test_marketplace_manifest_regression.py:150`), so tightening would convert a
  silent upgrade into a silent omission. An explicit `http://github.com/...`
  branch raises, distinct from the non-GitHub-host branch which stays silent.

- [x] **AC2 — Components at plugin root.** On the claude-plugins route each pack
  projects skills to `<pack>/skills/<name>/`, agents to `<pack>/agents/<name>.md`,
  commands to `<pack>/commands/<name>.md`, and emits no
  `<pack>/.claude/skills|agents|commands`. Hook wiring
  (`<pack>/.claude/settings.local.json`, the `merge-json` projection) is out of
  scope and unchanged.

- [x] **AC3 — Non-plugins projections unchanged, including their deletions.**
  Scoped per *projection*, not per consumer, because two consumers emit both
  routes. `build/self_host.py` (via `project_packs`, `:323`) and
  `commands/pack_evals.py` emit byte-identical output. For their skill
  projection, both the orphan-sweep target (`_skill_direct_directory_target`,
  `claude_code.py:65`) and the installed-name scan (`_installed_skill_names`,
  `:74-98`, called from `_sweep_skill_orphans`, `:101-115`) still resolve to
  `.claude/skills/` — asserted by planting a decoy `<root>/skills/decoy/` and
  showing a **non-plugins** build leaves it. Two consumers are explicitly *not*
  byte-identical: `commands/render.py` filters `DEFAULT_RECIPES` by adapter, and
  `commands/install.py --emit-install-routes` calls `render_pack` (`:1030-1033`)
  which runs `per-pack-claude-plugin`; both emit the claude-plugins route, whose
  output changes by design under AC2.

- [x] **AC4 — Both marketplace writers corrected.** The corrected shape is
  emitted by both writers, asserted on each writer's output rather than on the
  shared helper: the dist aggregation in `build/main.py`, and
  `self_host._aggregate_marketplace` (`self_host.py:602`, calling
  `derive_projectable_subset` at `:632`), which writes the root
  `.claude-plugin/marketplace.json` that adopters actually add.

- [x] **AC5 — Marketplace envelope preserved.** The **dist** `marketplace.json`
  still carries top-level `name`, `owner`, and `description` after `repo` leaves
  the source object, derived from the parsed clone URL — `build/main.py:705-717`
  currently splits `src["repo"]` to produce them. The self-host writer takes
  these as parameters (`self_host.py:605-607`) and is unaffected.

- [x] **AC6 — Source readers verified.** The three genuine readers of a plugin
  `source` object enumerated in `plan.md` are each shown shape-agnostic or
  updated. A bare `grep '"source"'` does not discharge this: `source` is an
  unrelated catalogue concept in `config.py`, `user_config.py`,
  `commands/upgrade.py`, and `commands/list_installed.py`.

- [x] **AC7 — Old shape unpinnable.** No assertion in the suite requires
  `source.source == "github"`, `source.repo`, `source.branch`, or
  `source.directory`. Corrected assertions fail against the pre-fix generator.

- [x] **AC8 — Manifest contracts corrected, all five copies.**
  `contracts/plugin-manifest.derived.schema.json`,
  `contracts/plugin-manifest.schema.json`, and their byte-equality-gated twins
  under `packages/agentbundle/agentbundle/_data/` accept the `git-subdir` source
  and no longer permit `branch`/`directory`; `additionalProperties: false` is
  retained.

  The **fifth** copy is the marketplace-entry schema AC9 introduces: it needs a
  `_data/` twin of its own, because `verify.py:599-605` resolves schemas through
  `_read_bundled`, which reads `agentbundle/_data/` first (`build/main.py:70-85`),
  and `pyproject.toml:41` ships `_data/*` into the wheel. It gets a byte-equality
  gate beside `tests/unit/test_contract_v0_3_schema.py:601-617`.

  The source object requires **at least one** of `ref` or `sha` — a
  payload pinning neither silently fetches the default branch, which is the
  original defect; a payload carrying both stays legal, as upstream allows.
  This is expressed with the `if`/`then`/`else` trio, **not `oneOf`**:
  `build/validate.py:23-28` lists `oneOf`/`anyOf`/`allOf` as "Unsupported by
  design" and warns "the validator does not silently expand", and that validator
  is what both real gates use (`build/main.py:31`, `verify.py:600`). A `oneOf`
  here would be silently ignored by the gate while passing a `jsonschema`-based
  test — the same class of defect this spec exists to fix. The tightening is
  recorded as a named exception in ADR-0072. `url` is constrained to
  `^https://github\.com/[^/]+/[^/]+\.git$` and `path` to `^[a-z0-9][a-z0-9-]*$`.

- [x] **AC9 — Marketplace entries are actually validated, on both paths.** A
  **marketplace-entry schema** (the derived schema, plus `source` *required* and
  `category` permitted) validates every `plugins[]` entry in **both** the dist
  `marketplace.json` and the root `.claude-plugin/marketplace.json`. A single
  schema cannot serve both artifacts: `plugin.json` must not carry `source`
  (`build/main.py:545-546` pops it), while a marketplace entry must require it.
  Negative test on each path proves a malformed `source` fails CI. This is the
  criterion that closes the gap; without it the schema work gates nothing.

- [ ] **AC10 — Reserved plugin-root names (forward-looking).** (deferred: plugin-root-name-collision-guard) The claude-plugins
  recipe fails the build if a non-projection write would land on a projected
  component directory. The reserved set is derived from the three claude-code
  component `target-path`s, **not** from `PRIMITIVE_DIRS` (`build/main.py:93`),
  which is the five *source* dir names and would over-reserve `hooks/` and
  `hook-wiring/`. This is explicitly a guard against a future collision, not a
  live defect: the recipe copies only `.claude-plugin/`, `pack.toml`, `README.md`,
  `seeds/` plus the projections (`build/main.py:504-584`), `seeds/` lands at
  `<pack>/seeds/` (`:582-584`), and no pack ships a top-level `skills/` today.

- [x] **AC13 — Layout consumers reconciled.** Every *operative* artifact asserting
  the old `claude-plugins/<pack>/.claude/...` layout is corrected in this PR,
  enumerated in `plan.md`: three assertions in
  `test_install_adapt_chain.py::test_install_marker_records_new_companions`
  (`:87,98,110`) and the docstring example at `commands/upgrade.py:1667`.

  **The shipped spec is superseded, not edited.**
  `docs/specs/claude-plugins-publish-and-discover/spec.md:46` AC3 asserts the
  published branch contains `.claude/skills/`, and that spec is
  `Status: Shipped` → Frozen per `docs/CONVENTIONS.md:103` ("Immutable history.
  Status fields can change…, bodies cannot"). AGENTS.md's drift rule governs
  *living* specs. Rewriting it would also falsify a verification record — the AC
  ends *"(Verified via `gh api` during T6 bootstrap.)"*, an observation that did
  happen and was true then. So: leave that body intact and record the
  supersession here. **This spec's AC2 supersedes the layout claim in
  `claude-plugins-publish-and-discover` AC3**; a dated one-line erratum under that
  spec's header points back here.

- [x] **AC11 — End-to-end install verified.** With a throwaway
  `CLAUDE_CONFIG_DIR` and a marketplace built from locally regenerated output,
  `claude plugin install core@<marketplace>` then `claude plugin details` reports
  **Skills ≥ 13** and **Agents ≥ 4** for `core`. The client reports commands under
  Skills — `conventions-check` appeared there in the pre-spec run — so 13 is
  12 skills + 1 command, and there is no separate Commands field to assert.
  Observed output, the client version, and the actual field list are recorded in
  `plan.md`.

- [x] **AC12 — Adopter-facing docs and changelog.** Docs showing the marketplace
  entry shape or pack layout are updated, including
  `docs/architecture/pack-manifest.md`'s derived-key table (which omits `source`
  and mistypes `author` as a string). Existing adopters are told to run
  `claude plugin marketplace update` and reinstall. A `docs/product/changelog.md`
  entry lands in this PR.

## Testing Strategy

- **AC1, AC4, AC5, AC7, AC8** — TDD. Assertions on `derive_projectable_subset`
  and on each writer's emitted payload; schema tests asserting both
  accept-correct and reject-malformed, including an `http://` input case.
- **AC2, AC3, AC10** — TDD. Per-route projection paths, plus the decoy-survival
  test for sweep confinement.
- **AC9** — TDD. Negative test on each of the two marketplace paths.
- **AC6, AC12, AC13** — goal-based check; enumeration and diffs recorded in the
  plan. AC13's artifact is an unfiltered sweep over operative paths —
  `grep -rn 'claude-plugins/[a-z-]*/\.claude/skills' packages/ docs/specs/` — with
  zero hits outside the frozen-spec body and the historical-narrative rows the
  plan's table marks **leave**.
- **AC11** — visual / manual QA against the real `claude` CLI. This is the
  criterion that proves the feature. The unit gates cannot substitute: the
  pre-fix manifest passed `claude plugin validate` and installed "successfully"
  while delivering nothing.

## Assumptions

1. **`git-subdir` is the correct source type**, verified empirically — it fetched
   the right subtree where `github` + `branch`/`directory` fell back to the
   default branch at repo root.
2. **Plugin-root component directories are required**, verified empirically:
   `git-subdir` alone gave Skills 0 / Agents 0; after moving components to the
   plugin root, Skills 13 / Agents 4 / Hooks 1.
3. **The `plugin.json` manifest-key override is not viable** — `"skills"`
   resolved, `"agents"` rejected a directory and reported 0 given a file list.
4. **A mutable `ref` is accepted, not an oversight.** `sha` pinning is infeasible:
   the dist commit does not exist at build time and `marketplace.json` lives on
   the branch it would pin. Integrity therefore rests on branch protection for
   `claude-plugins-dist`, which **does not exist today** and is sequenced in the
   plan's Rollout as a precondition, not silently assumed.
5. **Org-marketplace work is out of scope.** It additionally requires a private
   marketplace repository. `git-subdir` at a public target is a precondition for
   that path, not a completion of it.
6. **Relationship to `claude-clean-room-plugin-smoke`** (`workspace.toml`
   `[backlog].open`): AC11 narrows it to a CLI round-trip on one pack. The slug
   stays open for graphical-client and multi-pack coverage.
