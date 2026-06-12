# Plan: cursor-full-parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A net-new distribution adapter built almost entirely from existing parts. The shape: add a
`[adapter.cursor]` block to the contract (dual-copy), write `cursor.py` against it reusing the
four existing projection modes, register and dispatch it, then prove it with a focused test
module and a full-package pytest run. The riskiest part is **not** the projection — every
primitive maps mechanically — but the two places the build code can't be purely declarative:
the agent `readonly` derivation and the hook-wiring event remap + `version` key. Both follow the
kiro_ide precedent of keeping the contract *mode* generic (`direct-file` / `merge-json`) while
dispatching to a Cursor-specific inline helper. The second risk is the contract version bump:
a `"0.10"→"0.11"` change ripples to stale version assertions in CI-ungated test roots and may
expose the latent lexical version-compare at `install.py:2779` — so the plan ends with a
mandatory full `pytest packages/agentbundle/` hand-run, not just `make build-check`.

Order of operations: contract first (so the adapter has something to read), then the adapter
module, then registration + install dispatch (so it's selectable), then tests, then the
version-bump sweep, then CI + docs. Everything lands in one PR per the spec's atomicity note.

## Constraints

- **RFC-0026 / ADR-0015** — the five decisions, the projection table, the agent frontmatter
  mapping, the hook-event map, the no-new-mode / no-schema-change / distribution-only
  commitments. The plan implements these verbatim except the hook-event-map source-key spelling
  (PascalCase, not `agentSpawn` — recorded as the spec's erratum).
- **ADR-0013 / `copilot-full-parity`** — the full-parity, documented-tool-degradation template.
- **ADR-0012 / RFC-0022 / `kiro_ide.py`** — the `.md`-agent + frontmatter-mapping + inline
  `_project_agent_as_md` shape, reused directly.
- **RFC-0004 atomicity** — contract + adapter + registration + tests in one PR.
- **AGENTS.md "keeping changes minimal"** — no new top-level dir, no new dependency, no new mode,
  no new CLI flag, no `_rewrite_cursor_user_scope_paths`.

## Construction tests

**Integration tests:** beyond the per-task unit tests, one dispatch-level test (T3) confirms
`install --adapter cursor` is accepted at both scopes (neither render dispatcher raises). No
live-Cursor end-to-end test is in scope — no shipped test depends on the real tool (the RFC §
Evidence smoke is a follow-on a maintainer may run; tracked in the spec).

**Manual verification:** none required for merge; an optional live-Cursor smoke (drop the
generated `core` `.cursor/` tree into a Cursor workspace) is noted in `docs/backlog.md` as a
follow-on, mirroring the copilot AC23 pattern but **not** gating this PR.

## Design (LLD)

Shape: **integration** — wiring catalogue primitives into Cursor's `.cursor/*` layout. Stack:
Python 3 stdlib only (`shutil`, `json`, `tomllib`, `pathlib`), inside the existing
`agentbundle.build` package; no new dependency. Sub-sections below are the integration set
(dependencies & integration, interfaces & contracts, failure & resilience) plus design decisions.

### Design decisions

- **Inline agent + hook-wiring helpers, generic contract modes.** The contract declares
  `agent → direct-file` and `hook-wiring → merge-json`; `cursor.py` dispatches both to
  Cursor-specific inline functions (`_project_agent_as_md`, `_project_hooks_json`) rather than the
  shared `direct_file` / `merge_json` projections, because the readonly derivation and the
  event-remap + `version` key can't be expressed declaratively. *Rejected:* a new
  `cursor-agent-md` / `cursor-hooks-json` mode pair (the Copilot route) — adds enum surface every
  other adapter carries for no gain, and RFC-0026 explicitly forbids a new mode. Traces to: AC2,
  AC6, AC8, AC10 · no contracts/ (internal adapter contract).
- **Same-prefix scope, no rewrite.** `allowed-prefixes.{repo,user}` are both `[".cursor/",
  ".agentbundle/"]`; the install dispatch for cursor is a plain `cursor.project()` at both scopes
  (the codex branch), and user-scope rooting at `~` is the generic mechanism. *Rejected:* a
  `_rewrite_cursor_user_scope_paths` (the Copilot route) — wrong, since Cursor's prefix doesn't
  change between scopes. Traces to: AC3, AC14 · Open Q1.
- **Conservative readonly predicate.** `readonly: true` only on a *declared* tools list with zero
  mutating tools; absent list ⇒ omitted. *Rejected:* an explicit reviewer-name allowlist (brittle)
  and a Bash-disqualifies rule (would wrongly strip the reviewers' `readonly`). Traces to: AC9 ·
  Open Q2.
- **Fail-open-with-log event drop.** Unmapped hook events are logged and skipped, not raised —
  RFC decision 4, the no-silent-caps rule. *Rejected:* Copilot's fail-closed raise. Traces to:
  AC10.

### Interfaces & contracts

The only "interface" is the internal `[adapter.cursor]` block in `adapter.toml` (dual-copy to
`docs/contracts/adapter.toml`) — projection array, scope table, frontmatter mapping, and the
`hook-event-map` inline table. No external REST/event/RPC contract. Consumed by `cursor.py`
(projection), `adapters/__init__.py` (registration), `install.py` (dispatch),
`shipped_adapters_from_contract()` (advertisement). Traces to: AC1–AC5, AC12–AC14.

### Failure, edge cases & resilience

- Absent source dir for a primitive → skip (no crash), per the kiro_ide iterator.
- Agent with no `tools:` → `readonly` omitted (not `false`, not `true`).
- Agent with no `name:` → derive from filename.
- Pre-existing `.cursor/hooks.json` → merge under managed key, preserve foreign keys/events.
- Unmapped hook event → drop + log line, continue.
- Empty hook-wiring (no source dir, or all events unmapped) → no `hooks.json` written
  (`_project_hooks_json` returns early on empty `incoming`), matching the shared `merge_json`
  precedent. Traces to: AC10, AC11.

### Dependencies & integration

Integrates with: the build pipeline's `PHASE_ORDER`, the kiro/kiro_ide frontmatter helpers
(duplicated, not imported across privates per convention), the install render dispatchers, and
the contract loader. No external system. The contract bump couples to every test root asserting
`"0.10"` (T5) and to the latent `install.py` version-compare (T5 risk). Traces to: AC14, AC18,
AC19.

## Tasks

### T1: Contract block + scope + frontmatter mapping + version bump (dual-copy)

**Depends on:** none

**Tests:**
- `test_contract_files_byte_identical` (existing) stays green — both `_data/` and
  `docs/contracts/` copies edited identically. (AC1a)
- Existing `adapter.toml` schema-validation test passes with the new block (no schema change). (AC1)
- A new assertion (in T4's module) reads `[adapter.cursor]` and confirms the projection entries,
  scope prefixes, and mapping exist as specified. (AC2–AC4)

**Approach:**
- In `packages/agentbundle/agentbundle/_data/adapter.toml`: bump `[contract] version` `"0.10"→"0.11"`;
  add a header-comment line naming this spec / RFC-0026.
- Add `[[adapter.cursor.projection]]` array entries for the five standard primitives only:
  `skill` (direct-directory `.cursor/skills/`), `agent` (direct-file `.cursor/agents/` +
  `frontmatter-mapping = "cursor-agent-frontmatter-v0.11"`), `hook-body` (direct-file
  `.cursor/hooks/`), `hook-wiring` (merge-json `.cursor/hooks.json`, managed-key `hooks`,
  on-conflict `merge-managed-key-only`, + `hook-event-map` inline table), `command` (direct-file
  `.cursor/commands/`).
- Declare `kiro-ide-hook` as `mode = "dropped"` in the **table form**
  `[adapter.cursor.projections.kiro-ide-hook]` — **not** the array. The schema's array
  `primitive` enum admits only the five standard primitives (verified
  `adapter.schema.json:34–37`); declaring `kiro-ide-hook` in the array red-fails
  `test_contract_validates_against_schema`. kiro-ide (`adapter.toml:316`) and kiro-cli (`:399`)
  set the table-form precedent.
- Add `[adapter.cursor.scope]` with `repo="."`, `user="~"`, both `allowed-prefixes` `[".cursor/",
  ".agentbundle/"]`.
- Add `[frontmatter-mapping."cursor-agent-frontmatter-v0.11"]` with `name`/`description`/`model`
  identity renames; no `tools`, no `values` maps.
- Copy the entire edited file byte-for-byte to `docs/contracts/adapter.toml`.
- **Note:** `adapter.schema.json` is *not* edited — verify all four modes + five primitives are
  already enumerated (AC1) before assuming so.

**Done when:** `tomllib.loads` of both copies shows `version == "0.11"` and the `cursor` block;
`test_contract_files_byte_identical` and the schema-validation test are green.

### T2: `cursor.py` adapter module

**Depends on:** T1

**Tests:** (all in `test_adapter_cursor.py`, authored in T4 but driving this task)
- skill/command/hook-body land at `.cursor/{skills,commands,hooks}/`. (AC7)
- agent `.md` shape: frontmatter has `name`/`description`/`model`/`readonly`, no `tools`. (AC8)
- readonly predicate every arm (reviewers/retrieval → true; implementer → omitted; no-tools →
  omitted). (AC9)
- hook-wiring → one `.cursor/hooks.json`, `version==1`, event remap, `{"command":…}` handler. (AC10)
- non-destructive merge into a seeded `hooks.json`. (AC11)
- unmapped event → dropped + log, no exception. (AC10)
- `kiro-ide-hook` → nothing emitted. (AC2)

**Approach:**
- Model the module skeleton on `kiro_ide.py`: `project()` → `project_packs()` → `_project_single()`,
  iterating `_iter_primitives(contract)` in `PHASE_ORDER`, reading the `[adapter.cursor]` block.
- `direct-directory` (skill) and `direct-file` (command, hook-body) reuse the existing
  `direct_directory` / a local `_project_direct_file` (copy the kiro/copilot shape).
- agent (`direct-file` + mapping) → inline `_project_agent_as_md`: split frontmatter (reuse the
  kiro `_split_frontmatter`/`_parse_frontmatter` shape), apply the mapping, derive `readonly` via
  `_is_readonly(tools_list)` = `tools declared and not (set(tools) & {Edit,Write,MultiEdit,NotebookEdit})`,
  drop `tools`, serialise frontmatter + body (kiro_ide `_serialize_frontmatter_md` shape **with a
  `bool` branch added** — the borrowed serialiser's `else` renders Python `True`/`False`; the
  Cursor copy must emit lower-cased `true`/`false` so `readonly` is valid YAML/JSON). AC9's test
  asserts the literal `readonly: true` bytes.
- hook-wiring (`merge-json`) → inline `_project_hooks_json`: read every `*.toml`, for each
  `[[hooks.<Event>]]` translate `<Event>` via the contract `hook-event-map` (drop+log unmapped),
  flatten inner handlers to `{"command": <cmd>}`, build `{"version":1,"hooks":{…}}`, merge under
  the managed key into any existing target (preserve foreign keys), write `indent=2` + newline.
- Use a module-level logger / `print(..., file=sys.stderr)` consistent with kiro_ide's build-time
  log style for the unmapped-event drop.

**Done when:** all T4 tests for these behaviours pass against the real `core`/`research` packs.

**Touches:** packages/agentbundle/agentbundle/build/adapters/cursor.py

### T3: Register `cursor` + install dispatch branches

**Depends on:** T2

**Tests:**
- `shipped_adapters_from_contract()` includes `"cursor"`. (AC13)
- `ADAPTERS["cursor"]` and `registry["cursor"]` resolve. (AC12)
- dispatch test: `_render_for_repo_scope` and `_render_for_user_scope` for a cursor-targeted pack
  do not raise `no … projection wired for adapter 'cursor'`. (AC14)
- `"cursor" not in SELF_HOST_ADAPTERS`. (AC15)

**Approach:**
- `adapters/__init__.py`: import `cursor`; add `"cursor": cursor.project` to `ADAPTERS` and
  `"cursor": cursor` to `registry`.
- `commands/install.py`: add `cursor` to the adapter imports in both `_render_for_user_scope` and
  `_render_for_repo_scope`; add an `elif target_adapter == "cursor": cursor.project(pack_dir,
  contract, out)` branch in each (mirror the codex branch — no rewrite).
- Do **not** touch `SELF_HOST_ADAPTERS`, `cli.py`, `scope.py`, or
  `_adapter_supports_user_scope_hook_wiring` (cursor = codex shape: repo-scope hook-wiring only).

**Done when:** the dispatch test and the registry/contract assertions are green.

**Touches:** packages/agentbundle/agentbundle/build/adapters/__init__.py, packages/agentbundle/agentbundle/commands/install.py

### T4: `test_adapter_cursor.py`

**Depends on:** T1 (contract), T2 (module)

**Tests:** this task *is* the test module — see T2's test list plus the contract-block
assertions (AC2–AC5) and the no-self-host assertion (AC15).

**Approach:**
- Model on `test_adapter_kiro_ide.py` + `test_adapter_copilot.py`: `load_contract` from
  `docs/contracts/adapter.toml`, seed fixture packs under `tempfile.TemporaryDirectory`, call
  `cursor.project`, assert on-disk shape and `json.loads` of `hooks.json`.
- Include readonly-predicate fixtures for each arm using the real shipped tool sets, and a seeded
  pre-existing `hooks.json` for the non-destructive-merge test.
- Add a `test_contract_version_is_0_11` and a `test_existing_adapters_unchanged`-style guard if not
  better covered by T5's contract tests (avoid duplication — defer to existing `test_contract.py`
  where it already asserts version).

**Done when:** `pytest packages/agentbundle/agentbundle/build/tests/test_adapter_cursor.py` exits 0.

**Touches:** packages/agentbundle/agentbundle/build/tests/test_adapter_cursor.py

### T5: Version-bump sweep + full-package pytest green

**Depends on:** T1

**Tests:**
- `pytest packages/agentbundle/` exits 0 (all roots, including CI-ungated). (AC18, AC24)
- The `install.py:2779` version-compare outcome is recorded (latent-OK or fixed-with-test). (AC19)

**Approach:**
- Grep all `"0.10"` literals; for each, decide: contract-version assertion → bump to `"0.11"`
  (`test_contract.py:441/449`, `test_adapter_kiro_ide.py` version test, `test_adapter_copilot.py`,
  and any in the CI-only `tests/unit` / `tests/integration` roots); intentional other-version pin
  (`test_contract_v08.py`, `test_shipped_packs_v08_declarations.py`) → leave.
- Run `pytest packages/agentbundle/` and triage every failure. If a failure traces to the lexical
  `contract_version >= "0.7"` at `install.py:2779` (i.e. `"0.11"` mis-compares), replace it with a
  tuple-comparing helper (`_version_at_least(version, "0.7")`) **and** add a focused regression test
  pinning `"0.11" >= "0.7"` and `"0.8" >= "0.7"`; otherwise record in the Changelog that the check
  stays latent (Step-5 fallback yields the same `DEFAULT_ADAPTER`).
- Re-run until green.

**Done when:** `pytest packages/agentbundle/` exits 0 and the version-compare disposition is in the
Changelog.

### T6: CI wiring for the cursor adapter test

**Depends on:** T4

**Tests:**
- `build-check.yml` names `test_adapter_cursor.py` in an explicit step (the suite gates). (AC17)

**Approach:**
- Add the cursor adapter test path to the appropriate pytest step in
  `.github/workflows/build-check.yml`, following the existing explicit per-path wiring pattern
  (the build/tests adapter suite step, or a new step mirroring it).

**Done when:** the workflow file references the test path; `pre-pr.py` / yaml-lint pass.

**Touches:** .github/workflows/build-check.yml

### T7: Docs — distribution-adapters changelog, AGENTS.md, backlog

**Depends on:** T1

**Tests:**
- Goal-based: `docs/specs/distribution-adapters/spec.md` has a v0.10→v0.11 entry naming cursor. (AC21)
- Goal-based: root `AGENTS.md` Cursor line is accurate (manual read). (AC20)
- `make build-self FORCE=1` → clean `git status` (cursor out of self-host). (AC22)

**Approach:**
- Add the distribution-adapters Changelog entry (new cursor adapter, five primitives, dropped
  kiro-ide-hook, no-mode/no-schema-change).
- Read the root `AGENTS.md` Cursor-reader sentence; update only if it now misleads (Cursor now has a
  native projection, not only incidental AGENTS.md reading).
- Add/refresh a `docs/backlog.md` `cursor-full-parity` section: the optional live-Cursor smoke
  follow-on, the model-alias-map follow-on, and (if T5 left it latent) the version-compare-helper
  follow-on.
- Run `make build-self FORCE=1` and confirm clean tree.

**Done when:** the three docs land and `make build-self FORCE=1` leaves a clean tree.

**Touches:** docs/specs/distribution-adapters/spec.md, AGENTS.md, docs/backlog.md

## Rollout

- **Delivery:** additive, big-bang within one PR. No flag — a new adapter is inert until a pack
  declares `allowed-adapters = [… "cursor"]` or an adopter passes `--adapter cursor`. Fully
  reversible (revert the PR); no data migration, no published event.
- **Infrastructure:** none.
- **External-system integration:** none required to ship; the generated `.cursor/` artifacts are
  consumed by Cursor at the adopter's site, not by this repo's CI.
- **Deployment sequencing:** contract (T1) before adapter (T2) before dispatch (T3) before the
  version sweep (T5) — all in one commit series, one PR.

## Risks

- **Contract-bump ripple (high-likelihood, low-severity).** Stale `"0.10"` assertions in CI-ungated
  roots red-fail only on a hand-run, not `make build-check`. Mitigated by T5's explicit full-pytest
  gate. (Memory: "Contract-bump test traps".)
- **Latent lexical version-compare (low-likelihood, contained).** `install.py:2779` mis-compares
  `"0.11"` but is masked by the Step-5 fallback. T5 triages and either fixes-with-test or records
  latent. Surfacing it as a fix needs a regression test (Memory: "RFC code-precondition earns a test").
- **`kiro-ide-hook` array-vs-table form.** The schema's `projection`-array `primitive` enum may
  exclude `kiro-ide-hook`; if validation rejects it in the array, T1 moves it to the `projections`
  table form (kiro-cli precedent). Caught by the T1 schema-validation test.
- **Self-host accidental inclusion.** Forgetting decision 5 would project a `.cursor/` tree into this
  repo. T7's `make build-self FORCE=1` clean-tree check + the `"cursor" not in SELF_HOST_ADAPTERS`
  assertion (AC15) guard it.

## Changelog

- 2026-06-11: initial plan. Tasks T1–T7, single PR. Both RFC open questions resolved in the spec
  spike (no-rewrite same-prefix scope; conservative readonly predicate); hook-event-map keyed on
  PascalCase source names (erratum vs RFC-0026, recorded in spec).
