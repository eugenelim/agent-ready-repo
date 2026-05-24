# Plan: user-scope-hooks

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Thirteen tasks across two surfaces (T8 split into T8a/T8b/T8c —
state schema bump, install/uninstall, upgrade reconciliation):

- **Contract surface** (T1–T4): amend `adapter.toml`, the adapter
  contract schema, `pack.schema.json`, and the `hook-wiring` TOML
  schema. These land first because every later task depends on the
  schema accepting the new shapes.
- **Build pipeline + projection** (T5–T7): implement the
  scope-conditional `target` resolver, the `user-merge-json` mode
  for Claude Code, the `merge-into-agent-json` mode for Kiro, and
  the build-pipeline phase-order invariant.
- **CLI surface** (T8a–T9): state-schema bump and migration
  (T8a); install/uninstall threading with `--force-merge` (T8b);
  upgrade reconciliation including `attach-to-agent` rename
  (T8c); `reconcile --scope user` read-only reporter (T9).
- **Spec amendments** (T10–T11): the two follow-on spec edits
  RFC-0005 names, citing this spec's ACs.

Riskiest part is the build-pipeline ordering invariant (T7): every
existing test that runs the pipeline must still pass, and a new
test must prove the ordering is enforced (not just observed). The
implementation is small (a single sort key on the projection
iterator) but the regression surface is wide.

The Claude-Code-only design is feature-complete after T8b; Kiro
support lands incrementally through T6 (Kiro mode), T7 (pipeline
ordering), T8c (upgrade reconciliation including
`attach-to-agent` rename), and T9 (reconcile reporter walking
Kiro agent files). The plan does not bundle adapters into a
single mega-task — each adapter's tests can run independently.

## Constraints

- [RFC-0005](../../rfc/0005-user-scope-hook-support.md) — drives
  every decision in this plan; specific sections cited inline.
- [RFC-0004](../../rfc/0004-install-scope-per-pack.md) —
  state-schema migration shape (refuse-and-explain on stale
  schema-version), path-jail per scope, scope-conditional CLI
  surface.
- [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  — pack source-tree layout (`.apm/hooks/`, `.apm/hook-wiring/`,
  `.apm/agents/`); five-primitive projection table.
- [`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md)
  — stdlib-only commitment; refuse-and-explain shape for stale
  state-file schema; existing `--force` flag binding rule.
- [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)
  — Rail B (user-scope hook refusal); skill-directory walk
  determinism rule (`sorted(os.walk(...))`).

## Construction tests

Most construction tests live under **Tasks** below (per-task
`Tests:` subsections). This section covers cross-cutting tests
only.

**Integration tests:**

- **Fixture-pack end-to-end** (touches T5, T6, T7, T8, T9): each
  fixture pack under `tests/fixtures/packs/` runs through
  `install` → `reconcile` (clean) → `uninstall` → `reconcile`
  (clean) against a `tmp_path` `$HOME`. Each fixture exercises a
  different RFC-0005 path (Claude Code user; Kiro repo; Kiro user;
  cross-adapter; malformed negatives).
- **Phase-order invariant** (touches T6, T7): an integration test
  instruments the build pipeline to record the order of primitive
  projections, then asserts the order matches
  `hook-body` → `agent` → `hook-wiring` → `command` → `skill` for
  every fixture pack carrying multiple primitive types.
- **State-schema migration round-trip** (touches T2, T8): a v0.2
  state file from RFC-0004's fixtures migrates to v0.3
  cleanly, then a v0.3 reader sees its absent-default fields
  resolving correctly (`adapter` → `claude-code`).

**Manual verification:** none. Every behavior is contract-shape or
pipeline-shape; no UI; no end-to-end UX flow.

## Tasks

### T1: Adapter contract schema accepts scope-conditional projections, `agent-event-vocabulary`, and Kiro `[scope]` table

**Depends on:** none

**Tests:** (test file:
`packages/agentbundle/tests/unit/test_contract_v0_3_schema.py`)

- *Schema accepts* `target = ".kiro/hooks/<name>.{sh,py}"` (bare
  string, repo-only shorthand). [AC4]
- *Schema accepts* `target.repo = "..."` + `target.user = "..."`
  table form. [AC4]
- *Schema refuses* mixing bare string `target` with `target.user`
  table form in the same projection entry.
- *Schema accepts* `mode = "merge-into-agent-json"` plus
  `agent-event-vocabulary = [...]` of strings. [AC2]
- *Schema accepts* `[adapter.kiro.scope]` with `allowed-prefixes.user
  = [".kiro/", ".agent-ready/"]`; refuses `["/"]`, `[""]`,
  `["../"]` (existing Rail-A constraints from RFC-0004 carry
  forward). [AC1]
- *Schema accepts* `[pack.install] user-scope-hooks = true`; refuses
  non-boolean. [AC5]

**Approach:**

- Edit `packages/agentbundle/agentbundle/_data/adapter.schema.json`
  (or equivalent — verify the path) to add the new fields and
  type unions.
- Edit `packages/agentbundle/agentbundle/_data/pack.schema.json` to
  add `user-scope-hooks` boolean to `[pack.install]`.
- New unit test file
  `packages/agentbundle/tests/unit/test_contract_v0_3_schema.py`
  exercising each schema acceptance / refusal case.
- Bump contract `version = "0.3"` in
  `packages/agentbundle/agentbundle/_data/adapter.toml`. [AC7]

**Done when:** all schema tests pass; `make build-check` clean.

---

### T2: Hook-wiring TOML schema accepts optional `attach-to-agent`; pack-validate refuses Kiro-targeted wiring without it

**Depends on:** T1

**Tests:** (all inline-TOML unit tests in
`packages/agentbundle/tests/unit/test_validate_attach_to_agent.py`;
no file-on-disk fixtures — those land in T3 and exercise the same
rails via the integration path)

- *Schema accepts* `.apm/hook-wiring/<name>.toml` with an optional
  top-level `attach-to-agent` string field. [AC6]
- *Validate refuses* a Kiro-targeted pack (constructed in-memory)
  whose wiring TOML omits `attach-to-agent` with the exact
  RFC-0005 text
  `pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection`.
  [AC6]
- *Validate refuses* a Kiro-targeted pack whose `attach-to-agent`
  names an agent the same pack does not ship (no
  `.apm/agents/<name>.md` of that name). [AC6]
- *Validate accepts* a Claude-Code-only pack with `attach-to-agent`
  present — the field is ignored, not refused. [AC6]

**Approach:**

- Add the field to the wiring TOML schema (locate the schema; if
  inline in a Python validator, lift to a JSON-schema file under
  `_data/`).
- Add a validate-time rail in
  `packages/agentbundle/agentbundle/validate.py` (or equivalent)
  that fires only when `kiro` is in the resolved target adapter
  set.
- Unit tests construct pack-shaped dicts in memory and call the
  validator directly — no file-on-disk fixtures.

**Done when:** all inline-TOML validate rails pass.

---

### T3: Fixture packs land under `tests/fixtures/packs/`

**Depends on:** T1, T2

**Tests:** (test file:
`packages/agentbundle/tests/integration/test_fixtures_validate.py`)

- *Each well-formed fixture pack passes* `agentbundle validate`
  against its declared adapters via the file-on-disk integration
  path (separate from T2's in-memory unit tests). [AC28]
- *Each malformed fixture refuses* with the same error text T2's
  unit tests already verified — this is integration coverage that
  the on-disk pack-loading code path also reaches the same
  validate rails. One test per refusal class. [AC6, AC28]
- *Presence check*: tests assert fixture packs exist at their
  declared paths. [AC28]

**Approach:**

- Create `tests/fixtures/packs/cc-user-hooks/` with
  `pack.toml` (`user-scope-hooks = true`, `allowed-scopes = ["user"]`),
  `.apm/hooks/on-prompt.sh`, `.apm/hook-wiring/on-prompt.toml`
  (`[[hooks.UserPromptSubmit]] command = "..."`).
- Create `tests/fixtures/packs/kiro-repo-hooks/` with `pack.toml`,
  `.apm/agents/reviewer.md`, `.apm/hooks/on-spawn.sh`,
  `.apm/hook-wiring/on-spawn.toml` (`attach-to-agent = "reviewer"`,
  `[[hooks.agentSpawn]] command = "..."`).
- Create `tests/fixtures/packs/kiro-user-hooks/` (variant of repo
  fixture with `user-scope-hooks = true`).
- Create negative fixtures:
  `malformed-kiro-missing-attach/`,
  `malformed-kiro-pascal-events/`,
  `malformed-kiro-unknown-agent/`.
- **Hook body shape and mode.** Every fixture hook body is a
  trivial stub: `#!/bin/sh\nexit 0` for `.sh`, or
  `#!/usr/bin/env python3\nimport sys; sys.exit(0)` for `.py`.
  Files are committed with mode `0755`. Tests assert the mode bit
  is preserved through projection (some CI checkouts on platforms
  with restrictive umasks strip +x; if so, a fixture-loader
  helper re-applies it before exercising AC18).

(Cross-adapter coverage falls out for free — the existing build
pipeline projects every pack against every reference adapter; the
Kiro fixtures also exercise the Claude-Code-ignores-`attach-to-agent`
path. No dedicated cross-adapter fixture needed.)

**Done when:** all six fixtures present; presence tests + the
negative-validate tests from T2 pass against them.

---

### T4: Scope-conditional `target` resolver

**Depends on:** T1

**Tests:** (test file:
`packages/agentbundle/tests/unit/test_target_resolver.py`)

- *Resolver returns* the bare-string `target` when no scope-map is
  declared (legacy path). [internal: AC3/AC4 building block]
- *Resolver returns* `target.repo` when invoked with `scope =
  "repo"` and a scope-map declaration. [AC3, AC4]
- *Resolver returns* `target.user` when invoked with `scope =
  "user"`. [AC3, AC4]
- *Resolver refuses* when the requested scope's target is missing
  from a scope-map declaration. [internal]
- *Resolver substitutes* `<attach-to-agent>` placeholder when a
  per-wiring-entry agent name is provided (for
  `merge-into-agent-json`). [AC15, AC18]

**Approach:**

- New module
  `packages/agentbundle/agentbundle/build/target_resolver.py`
  implementing `resolve_target(adapter_projection, scope,
  attach_to_agent=None) -> str`. Returns `str` rather than `Path`:
  pipeline consumers (T5/T6) own scope-root resolution (`.` vs `~`)
  and `<name>` / `<pack>` placeholder substitution; the resolver
  stays a pure-string utility with no filesystem dependency.
- New unit test file
  `packages/agentbundle/tests/unit/test_target_resolver.py`.

**Done when:** resolver unit tests pass; pure function with no
side effects.

---

### T5: `user-merge-json` mode implementation (Claude Code user scope)

**Depends on:** T3 (fixture packs), T4

**Tests:**

- *Merge into empty file* writes `hooks.<event>` arrays with
  `id`-tagged entries; no other top-level keys appear. [AC8]
- *Reinstall same version* produces byte-for-byte identical file.
  [AC9]
- *Install second pack overlapping event* appends; first pack's
  entries unmoved; both IDs present. [AC10]
- *Uninstall removes only owned entries*; surviving entries
  position-preserved; empty arrays removed. [AC11]
- *Adopter hand-edited collision* refuses install with RFC-0005
  text; `--force-merge` adopts. [AC12]
- *Unparseable JSON* refuses non-zero, file unchanged. [AC13]
- *Wrong-type `hooks` or `hooks.<event>`* refuses with
  `<key-path> has unexpected shape`. [AC14]
- *Auto-init absent `hooks`* writes `hooks = {}` then
  `hooks.<event> = []` then appends.
- *Atomic write* (read-modify-write with `Path.replace()`).

**Approach:**

- New module
  `packages/agentbundle/agentbundle/build/projections/user_merge_json.py`
  with `project(...)` and `unproject(...)` (uninstall) functions.
- The id synthesis lives in a shared helper
  (`packages/agentbundle/agentbundle/build/projections/hook_id.py`)
  used by both `user-merge-json` and `merge-into-agent-json`.
- Tests under
  `packages/agentbundle/tests/unit/test_user_merge_json.py` and
  one fixture-pack integration test under
  `packages/agentbundle/tests/integration/test_cc_user_hooks_fixture.py`.

**Done when:** all listed unit tests + fixture integration test
pass against the `cc-user-hooks` fixture; `$HOME` set to
`tmp_path`.

---

### T6: `merge-into-agent-json` mode implementation (Kiro repo + user scope)

**Depends on:** T3 (fixture packs), T4, T5 (for the shared `hook_id.py` helper)

**Tests:**

- *Merge into pack-owned agent JSON* writes `hooks.<event>` arrays
  with `id`-tagged entries; other keys in the agent JSON
  (`name`, `description`, etc.) are untouched. [AC15]
- *Reinstall same version* byte-for-byte no-op.
- *Adapter table lookup* picks `agent-event-vocabulary` from the
  adapter projection.
- *Validate refuses cross-vocabulary events* (PascalCase events
  against Kiro) with the
  `not in adapter ... agent-event-vocabulary` text. [AC17]
- *Validate accepts arbitrary events against Claude Code*: a
  wiring TOML carrying any event-name string (including
  Kiro-vocabulary `userPromptSubmit`, novel names) passes
  `validate` against the Claude Code adapter, because Claude
  Code's projection declares no `agent-event-vocabulary`. The
  per-adapter vocabulary gate fires only when the adapter
  declares the field. [AC17b]
- *User-scope projection writes* to `<tmp_HOME>/.kiro/agents/<agent>.json`;
  running `sh -c "$command"` from an arbitrary cwd exits 0 (the
  fixture's hook body is a `#!/bin/sh\nexit 0` stub installed with
  mode 0755). The path representation in `command` is not
  asserted — the test observes dispatchability, not encoding.
  [AC18]
- *Uninstall removes wiring-owned entries from agent JSON*; agent
  file itself remains until the `direct-file` projection's
  uninstall runs. [AC19]
- *Missing agent file at merge time* refuses with the
  `internal: <agent-file> missing` text (pipeline-ordering
  violation; this case is reachable only via test instrumentation).
- *Unparseable agent JSON or wrong-shape `hooks`* refuses (same
  refusal shape as `user-merge-json`).

**Approach:**

- New module
  `packages/agentbundle/agentbundle/build/projections/merge_into_agent_json.py`.
- Reuses `hook_id.py` from T5.
- Tests under
  `packages/agentbundle/tests/unit/test_merge_into_agent_json.py`
  and fixture-pack integration tests under
  `packages/agentbundle/tests/integration/test_kiro_repo_hooks_fixture.py`
  and `test_kiro_user_hooks_fixture.py`.

**Done when:** unit + integration tests pass against the
`kiro-repo-hooks` and `kiro-user-hooks` fixtures.

---

### T7: Build-pipeline phase order invariant

**Depends on:** T5, T6

**Tests:**

- *Phase-order assertion*: instrument the pipeline iterator with a
  recorder; for every fixture pack with multiple primitive types,
  assert the recorded order is
  `hook-body` → `agent` → `hook-wiring` → `command` → `skill`. [AC16]
- *Regression-protection*: identify and pin the existing
  pipeline integration tests that touch **multiple primitives in
  the same pack** — these are the load-bearing ones for
  ordering. At minimum: every test under
  `packages/agentbundle/agentbundle/build/tests/` whose fixture
  pack ships ≥ 2 of `{agent, hook-body, hook-wiring, command,
  skill}`. Add a docstring marker
  (`# phase-order regression: multi-primitive pack`) to each so
  the inventory is checkable. Assert every marked test passes
  with the new sort applied. A test that doesn't touch multiple
  primitives can't regress on ordering and doesn't need pinning.
- *Cross-pack independence*: a build run over two packs (one Kiro
  agent + wiring, one Claude Code wiring) finishes each pack's
  phases independently — no pack's wiring runs against another
  pack's agent file (regression test for the cross-pack-ordering
  drawback in RFC-0005). [AC16, internal]

**Approach:**

- Locate the pipeline iterator (likely
  `packages/agentbundle/agentbundle/build/pipeline.py` —
  verify); add a stable sort by primitive-type with the declared
  order.
- Sort within a pack only; cross-pack independence preserved by
  outer iteration.
- New unit test file
  `packages/agentbundle/tests/unit/test_pipeline_phase_order.py`.

**Done when:** phase-order test passes; all prior integration
tests pass unchanged.

---

### T8a: State schema bumps to v0.3 with migration

**Depends on:** T1

**Boundary:** the v0.2 → v0.3 migration semantics live in this
task's Approach; the spec's *Ask first* boundary holds — pause and
confirm with the human before deviating from header-only-additive
(e.g., per-row backfill).

**Tests:**

- *State-schema read-time default*: v0.3 reader against a row
  with absent `adapter` resolves it as `claude-code`. [AC21]
- *State-schema read-time default for `target-file`*: a v0.3
  reader against a Claude Code row with absent `target-file`
  resolves it as `~/.claude/settings.json` (the adapter's
  scope-default target). For Kiro rows, `target-file` is required.
- *Write against v0.2 state file* refuses with the RFC-0004
  refuse-and-explain text. [AC22]
- *`init-state --migrate` v0.2 → v0.3* rewrites only the
  `schema-version` line; no per-row backfill. [AC21]
- *Round-trip*: a v0.2 fixture state file from RFC-0004's
  fixtures migrates to v0.3 and reads back identically except
  for the version line. [cross-cutting integration test]

**Approach:**

- Edit `packages/agentbundle/agentbundle/state.py` (or
  equivalent) to bump schema, add optional `adapter`, optional
  `target-file`, optional `hook-wiring-owned` table.
- Implement the v0.2 → v0.3 migrate step in `init-state
  --migrate`.
- New unit tests in
  `packages/agentbundle/tests/unit/test_state_v0_3_schema.py`.

**Done when:** schema/migration tests + cross-cutting round-trip
pass.

---

### T8b: Install / uninstall thread user-scope hook handling; `--force-merge` flag

**Depends on:** T5, T6, T7, T8a

**Tests:**

- *Install --scope user* against `cc-user-hooks` fixture writes
  state with `hook-wiring-owned` rows; `adapter` field absent
  (defaulted). [AC20, AC23]
- *Install --scope user* against `kiro-user-hooks` fixture writes
  state with `adapter = "kiro"` and `target-file =
  ".kiro/agents/<agent>.json"` per row. [AC20, AC23]
- *Install --scope user* against a pack without `user-scope-hooks`
  refuses at validate with Rail B's existing text. [AC24]
- *Install --scope user* against an adapter without working
  user-scope mode refuses with RFC-0005 text. [AC25]
- *Uninstall reads `hook-wiring-owned`* and removes only owned
  entries from the right target file (one test per adapter shape).
  [AC11, AC19]
- *`--force-merge` flag*: bound to `install`, scope `user`,
  Claude Code only — refused elsewhere with `unknown flag for <verb>`
  or scope-mismatch text. [AC12]

**Approach:**

- Edit `packages/agentbundle/agentbundle/cli.py` to add
  `--force-merge` flag, route hook-wiring projection through the
  T5/T6 modes, write `hook-wiring-owned` state rows on install,
  read them on uninstall.
- New integration tests under
  `packages/agentbundle/tests/integration/test_install_user_hooks.py`
  and `test_uninstall_user_hooks.py`.

**Done when:** install + uninstall scenarios for both adapters at
user scope pass.

---

### T8c: Upgrade reconciliation including `attach-to-agent` rename

**Depends on:** T8b

**Tests:**

- *Upgrade in place* (same version, same wiring): a no-op on the
  target file; state unchanged. [AC9]
- *Upgrade adds a new hook entry*: state grows by one
  `hook-wiring-owned` row; target file appended.
- *Upgrade removes a hook entry*: state row removed; target file
  entry removed.
- *Upgrade renames `attach-to-agent`* (Kiro): walks the OLD
  `target-file` to remove orphan entries, walks the NEW
  `target-file` to add the new entries; state updated with the new
  `target-file`. After upgrade, `reconcile --scope user` reports
  no orphans. [AC19b]
- *Upgrade adds an agent the pack didn't have*: same shape as
  rename, no old-file walk required.
- *Upgrade removes an agent the pack had*: the agent file gets
  removed via the agent primitive's uninstall; the `hook-wiring-owned`
  rows pointing at it are also removed.

**Approach:**

- Extend `upgrade` in `cli.py` (or its supporting module) to
  compute the symmetric difference between old-state and new-pack
  `hook-wiring-owned` shape, dispatch removals/additions per
  `target-file`.
- New integration tests under
  `packages/agentbundle/tests/integration/test_upgrade_user_hooks.py`
  and `test_upgrade_attach_to_agent.py`.

**Done when:** all upgrade scenarios pass; `reconcile` reports
clean after each.

---

### T9: `reconcile --scope user` read-only reporter subcommand

**Depends on:** T8b

**Tests:** (test file:
`packages/agentbundle/tests/integration/test_reconcile.py`)

- *Walks both adapters' target files*: reads
  `~/.claude/settings.json` and every Kiro agent JSON named in
  user-scope state. [AC26]
- *Reports orphan type A* (file claims own, state doesn't know):
  inject a synthetic `id`-tagged entry into the settings file
  outside state; reconcile reports it as orphan-in-file. [AC26]
- *Reports orphan type B* (state claims own, file doesn't have):
  remove an entry from the settings file outside state; reconcile
  reports it as orphan-in-state. [AC26]
- *Output grouped by adapter*: two adapters' orphans appear under
  separate headings. [AC26]
- *Read-only*: no `--apply` flag exists; the subcommand never
  writes. (Test: snapshot the target files before and after a
  reconcile run and assert byte-for-byte identical.) [AC26]
- *`reconcile --apply` is rejected* by argparse with the standard
  "unrecognized argument" exit code (argparse default); the
  subcommand's parser does not register `--apply`. [AC26]
- *Empty case*: a clean install produces an "all clean" output
  with no orphans. [AC26]

**Approach:**

- New module
  `packages/agentbundle/agentbundle/commands/reconcile.py` (matches
  the existing per-command layout under `commands/`; the subcommand
  is registered in `cli.py`).
- Tests under
  `packages/agentbundle/tests/integration/test_reconcile.py`.

**Done when:** all reconcile scenarios pass; snapshot assertion
holds.

---

### T10: Amend `docs/specs/distribution-adapters/spec.md` per RFC-0005

**Depends on:** T1, T2, T3

**Tests:**

- *Spec includes a `merge-into-agent-json` subsection* with the
  merge / idempotency / failure-mode rules from RFC-0005.
- *Spec includes a `user-merge-json` subsection* (Claude Code
  user-scope).
- *Projection table* (lines 179–180 today) updated to show Kiro
  `hook-wiring` as `merge-into-agent-json` and add the
  scope-conditional Claude Code rows.
- *Rail B text* updated to the conditional form (lift on
  `user-scope-hooks` + working mode).
- *Spec amendment cites RFC-0005 sections by name.*
- *`make build-check` clean* (self-host pipeline picks up the
  spec change without drift).

**Approach:**

- Edit `docs/specs/distribution-adapters/spec.md` directly (not a
  seed — the spec itself is per-instance).
- Update projection table; add new mode subsections; rewrite Rail B
  to the conditional form; add `agent-event-vocabulary` field
  documentation; add the build-pipeline phase order to the
  pipeline spec.

**Done when:** spec amendment merged; `make build-check` clean;
adversarial-reviewer clean against the amendment (subagent
invocation in the amendment PR's work-loop, not this one).

---

### T11: Amend `docs/specs/agent-spec-cli/spec.md` per RFC-0005

**Depends on:** T8a, T8b, T8c, T9

**Tests:**

- *Spec includes documentation* of `--force-merge` (binding rule,
  Claude Code user-scope only, orthogonal to `--force`).
- *Spec includes documentation* of `reconcile --scope user` as a
  read-only reporter.
- *Spec documents the v0.3 state-schema migration shape* and the
  `[[installed]]` field additions.
- *Refuse-and-explain text* for unparseable settings files and
  wrong-shape `hooks` keys spelled out.
- *`make build-check` clean.*

**Approach:**

- Edit `docs/specs/agent-spec-cli/spec.md` directly.
- Add `--force-merge` to the CLI surface table; add `reconcile`
  subcommand entry; document state schema v0.3; cite RFC-0005
  sections.

**Done when:** spec amendment merged; gates clean;
adversarial-reviewer clean against the amendment (separate PR).

## Rollout

This spec ships through thirteen PRs (one per task — T8 split
into T8a/T8b/T8c). No production behavior changes ship before all
thirteen land — the user-scope hook support is gated on the v0.3
contract bump in T1, the schema acceptances in T2, and the CLI
threading in T8b. Adopters of v0.2
CLI continue to install at repo scope without hook-wiring being
projected to Kiro (it stays `degraded-info-log` for them); they
cannot install hook-bearing packs at user scope (Rail B refuses).
The v0.3 CLI is the cutover.

No flag-gated rollout; the v0.3 contract bump is the gate. Adopters
upgrade the CLI to v0.3 to opt into the new behavior; until they
do, the v0.2 path is unchanged.

**Adopter cutover gesture.** The cutover for an existing adopter is
`agentbundle init-state --migrate`. Until they run it, every
`install` / `uninstall` / `upgrade` against the v0.3 CLI refuses
with the v0.2 stale-schema text (AC22). This is the
refuse-and-explain shape RFC-0004 established; the v0.3 CLI does
not silently rewrite v0.2 state files. Adopters mid-upgrade —
v0.3 binary in `$PATH` but v0.2 state file on disk — see the
refusal and run the migrate command.

## Risks

- **Phase-order invariant might break an existing
  cross-primitive interaction we don't know about** (T7). The
  regression-protection test is the mitigation; if a hidden
  dependency surfaces, the plan changes (back to PLAN).
- **The shared `hook_id.py` helper might land too coupled to Claude
  Code's semantics** (T5/T6). Synthesizing `<pack>:<basename>` is
  the same shape for both adapters today but the helper should
  not assume that. If T6 ends up needing a different id form for
  Kiro, that's a re-plan.
- **State-schema v0.2 → v0.3 migration is the second migration
  adopters run in two RFCs.** RFC-0005 already records the
  drawback; the implementation has to be airtight (T8). Mitigation:
  the cross-cutting migration round-trip integration test runs
  against actual v0.2 fixtures from RFC-0004 to confirm no
  regression.
- **Fixture-pack design lock-in** (T3). The fixtures are
  load-bearing across T5–T9. If T5 discovers that the fixture's
  shape is wrong, fixing it cascades. Mitigation: keep fixture
  packs minimal — just the primitives each test exercises, no
  extras.

- **Fixture-pack tests verify file-shape, not runtime dispatch.**
  Tests confirm the merged `~/.claude/settings.json` and the
  merged `.kiro/agents/<agent>.json` have the right *shape* —
  `id`-tagged entries under the right event keys — but never
  load Claude Code or Kiro and observe the hook actually firing.
  RFC-0005 already records two drawbacks against unverified
  runtime assumptions (the `id`-as-tag behaviour and Kiro's
  `hooks` field). A contract-shape regression in either runtime
  would not be caught by these tests. **Accepted residual risk** —
  the spec's Testing Strategy explicitly declares no manual QA
  for this work (no UI, no end-to-end UX flow), so this risk is
  not mitigated by an artifact this PR produces. It is revisited
  if an adopter reports a runtime divergence; the recovery shape
  would be a targeted fix-and-amendment PR with the discovered
  symptom recorded in `notes/`.

## Changelog

- 2026-05-24: initial plan, drafted from RFC-0005 (and its
  Kiro-inclusion amendment) immediately after both RFC PRs merged.
