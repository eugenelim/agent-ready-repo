# Plan: copilot-skills-and-web

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One PR, one contract version bump (`0.11` → `0.12`), two coupled changes:

1. **Skill flip (behaviour change).** Retarget copilot's `skill` primitive from
   `instruction-file` → `.github/instructions/` to the existing
   `direct-directory` shape → `.github/skills/`, the same passthrough four other
   adapters use for the canonical `.apm/skills/<name>/SKILL.md` source. Drop the
   now-orphaned `copilot-instruction` frontmatter-default and copilot's dead
   `_project_instruction_file`/frontmatter helpers. Update the scope prefixes
   (`.github/skills/` repo, `.copilot/skills/` user; drop the
   `instructions/` prefixes).
2. **Web correction (docs/comments-only, zero behaviour change).** `WebFetch`/
   `WebSearch` already pass through `copilot-agent-md` verbatim and Copilot
   resolves them to its `web` tool on CLI/app. Correct the false "no web tool /
   research degradation" wording in `copilot_agent_md.py` and the ~6 docs +
   pack-content sites; preserve the one true caveat (cloud agent lacks web).

Order of operations: governance errata first (anchors the reversal), then the
contract (the source the code reads), then code + pack content + tests in
lockstep, then `make build-self` to refresh `marketplace.json`, then the doc
blast radius. Riskiest part: the lexical version-compare tests
(`"0.10"`/`"0.12"`/`"0.8"`) and the byte-identical twin/schema drift gate — both
caught by the full package pytest run in both roots, which `make build-check`
does **not** run.

## Constraints

- **RFC-0024 / ADR-0013** chose `instruction-file` for the copilot `skill`
  (Decision 3) and recorded a web degradation (Open Q4). This PR reverses both;
  per the project's frozen-RFC rule the divergence is recorded as an
  Approver-signed `§ Errata` appended to each (vehicle (a), owner-confirmed
  2026-06-11). **Append, never rewrite.**
- **RFC-0009** is the flip-on-upstream-support precedent (a `dropped` primitive
  flipped to first-class when the tool gained native support); the same shape
  justifies the erratum vehicle over a fresh RFC.
- **RFC-0024 § Decision 7** — a contract bump is **not** an all-pack bump; only
  `research` + `core` move to the new level.
- **CONVENTIONS § 4** — spec metadata contract (status/ACs/backlog anchors),
  contract byte-identical twins.

## Construction tests

Most tests live per-task below. Cross-cutting:

**Integration tests:** `tests/integration/test_install_repo_scope_per_adapter.py`
and `test_multi_pack_install.py` must still pass with the new copilot skill
target (`.github/skills/` rather than `.github/instructions/`).
**Manual verification:** none — the source of truth is the official docs (no
live CLI re-probe, per spec § Never do). Doc-wording correctness is a
goal-based `grep` (T7).

## Design (LLD)

Shape: **integration** — wiring the copilot projection to Copilot's filesystem
layout. No new module/dependency; reuses the `direct-directory` projector.

### Design decisions
- **Reuse `direct-directory`, don't invent a mode.** Copilot's skill source is
  already canonical Claude `SKILL.md`, which Copilot accepts verbatim; the
  passthrough + symlink-defence + skill-bounded orphan-sweep in `codex.py` /
  `direct_directory.py` is the model. Rejected: a copilot-specific skill mode
  (no behaviour the shared one lacks). Traces to: AC4 · `docs/contracts/adapter.toml`.
- **Branch in single-pack `project()`, no `project_packs` refactor.** Copilot is
  installed per-pack (`install.py`) and is not self-hosted, so the multi-pack
  `project_packs` form codex uses for self-host is unnecessary here; mirror
  codex's `direct-directory` *branch* (one source_dir, skill-bounded sweep).
  Rejected: refactoring copilot to `project_packs` (scope creep, no caller needs
  it). Traces to: AC4.
- **Web change is comments+docs only.** Pass-through is already correct; adding a
  tool-name mapping would be wrong (spec § Never do). Traces to: AC5.

### Interfaces & contracts
- `docs/contracts/adapter.toml` + `_data/adapter.toml` twin — the copilot
  `skill` projection row, `[adapter.copilot.scope]` prefixes, `[contract]
  version`, and removal of `[frontmatter-default."copilot-instruction"]`. Both
  byte-identical; `adapter.schema.json` enum already contains `direct-directory`
  (no schema change expected — verify). Traces to: AC1, AC2, AC3.

### Failure, edge cases & resilience
- Re-projection idempotency: the orphan sweep must remove a skill dir that no
  longer exists in source (AC4 test). Symlink defence at the skill-root level is
  inherited from the shared projector.
- Lexical version compare: `test_contract_v07.py`/`v08.py` compare version
  strings; `"0.12"` must order after `"0.10"`/`"0.8"` correctly (AC3 test).

### Dependencies & integration
- External truth: the two official Copilot doc pages (skills, custom-agents)
  cited in spec § Assumptions. No new runtime dependency.

## Tasks

### T1: Governance errata anchor the reversal

**Depends on:** none

**Tests:**
- Goal-based: `docs/rfc/0024-copilot-subagent-projection.md` gains a `## Errata`
  section, Approver-signed (eugenelim), dated 2026-06-11, that (a) closes Open
  Q4 stating web is supported on CLI/app per the custom-agents docs and the
  Run-4 finding was confounded, and (b) records the skill-surface flip
  (instruction-file → first-class `SKILL.md`) citing the add-skills docs; no
  prior line of the RFC is modified (verify via `git diff` shows only additions
  below the existing content).
- Goal-based: `docs/adr/0013-copilot-full-parity-user-scope-adapter.md` gains a
  matching `## Errata` (same two corrections), append-only.
- `lint-spec-status.py` accepts the RFC/ADR status vocabulary unchanged.

**Approach:**
- Append a `## Errata` section to RFC-0024 below § Follow-on artifacts. Two
  entries: **E1 (Open Q4 closed)** and **E2 (skill-surface flip)**, each with the
  doc citation, the 2026-06-11 date, and `Signed-off: eugenelim (Approver)`.
- Append a parallel `## Errata` to ADR-0013.
- Cross-reference this spec (`docs/specs/copilot-skills-and-web/`) from both.

**Done when:** both errata appended (additions-only diff), each Approver-signed,
naming Open Q4 closure + the skill flip with doc citations.

### T2: Contract retargets copilot skill + bumps to v0.12

**Depends on:** T1

**Tests:**
- TDD: extend `build/tests/test_adapter_copilot.py` — copilot `skill` rule is
  `{mode: "direct-directory", target-path: ".github/skills/"}` with no
  `frontmatter-default`; assert `[frontmatter-default."copilot-instruction"]` is
  absent (AC1).
- TDD: `build/tests/test_contract_scope.py` — `allowed-prefixes.repo` contains
  `.github/skills/` and not `.github/instructions/`; `allowed-prefixes.user`
  contains `.copilot/skills/` and not `.copilot/instructions/` (AC2).
- TDD: version-pin update — the exact-value pins that go red on `0.11`→`0.12`:
  **build root** — `test_contract.py::test_contract_version_is_v05` (line ~448)
  and `test_adapter_kiro_ide.py::test_contract_version_is_0_9` (line ~141);
  **CI-only `tests/` root** — `test_contract_v0_3_schema.py:81`
  (`assertEqual(... version, "0.10")`; carries an in-file comment noting it was
  left stale once because this root isn't in `make build-check` — do not repeat
  that). All have **historical names**; update the asserted value/message/docstring
  to `"0.12"`, do **not** rename. `test_contract_v07.py`/`v08.py` use
  `assertGreaterEqual((0,8))` tuple compares and survive the bump (AC3).

**Approach:**
- Edit `docs/contracts/adapter.toml`: copilot `skill` projection block (lines
  ~412-417) → `mode = "direct-directory"`, `target-path = ".github/skills/"`,
  drop `frontmatter-default`; update the header comment block **including the
  now-false narration at line ~33 (`skill` gains `~/.copilot/instructions/`) and
  line ~446 (`skill` keeps its `instruction-file` mode)**; update the
  `[adapter.copilot.scope]` prefixes (lines ~450-460); remove
  `[frontmatter-default."copilot-instruction"]` (lines ~613-614); bump
  `[contract] version` to `"0.12"` with a dated comment referencing this spec.
- Mirror **byte-identical** into `packages/agentbundle/agentbundle/_data/adapter.toml`.
- Check `adapter.schema.json` (both copies) — `direct-directory` already in the
  enum; only edit if a removed key was schema-validated (expected: no change).
- Update the `[target.copilot]` comment in `docs/contracts/target-vocab.toml`
  (`.github/instructions/` → `.github/skills/`); the name-pattern/desc cap still
  apply. **Single-copy file** (read from `docs/contracts/` only, no `_data/`
  twin) — the byte-identical rule does not apply here (AC1).
- Update every other version-pin assertion the search surfaces.

**Done when:** both contract copies byte-identical, copilot skill is
`direct-directory`→`.github/skills/`, version `"0.12"`, the contract tests above
green.

### T3: Projection code follows the contract

**Depends on:** T2

**Tests:**
- TDD: the existing `test_adapter_copilot.py::test_skill_projects_with_applyTo_default`
  (line ~44, asserts `.github/instructions/foo.instructions.md` + `applyTo`
  frontmatter) is now **obsolete** — rewrite it (not "extend") to assert
  rendering a synthetic pack with `.apm/skills/<name>/SKILL.md` through
  `copilot.project` emits `.github/skills/<name>/SKILL.md` byte-equal, and a
  second projection after the source skill is removed sweeps the stale dir,
  bounded to the skill target (AC4).
- TDD: `tests/unit/test_copilot_agent_md.py` — an agent declaring
  `tools: Read, Grep, Glob, WebFetch, WebSearch` projects with no `ValueError`
  (regression, AC5); add an assertion that the module docstring no longer
  contains "no web tool"/"degradation" and does contain the corrected wording
  (or assert via a `grep`-style test).

**Approach:**
- `build/adapters/copilot.py`: replace the `instruction-file` branch with a
  `direct-directory` branch mirroring `codex.py` (copytree `symlinks=True`,
  skip symlink at skill-root, `rmtree`/`unlink` existing destination, then
  `sweep_orphans(target_dir, expected_names)` bounded to `skill`). Import
  `sweep_orphans` from `projections/direct_directory`. Remove
  `_project_instruction_file`, `_split_frontmatter`, `_parse_frontmatter`,
  `_emit_frontmatter` (now dead — confirm no other reference). Update the module
  docstring.
- `build/projections/copilot_agent_md.py`: correct the module docstring + the
  `_KNOWN_TOOLS` comment — `WebFetch`/`WebSearch` resolve to Copilot's `web`
  tool on CLI/app; the only non-coverage is the cloud agent. **No code change**
  (pass-through unchanged).
- `commands/install.py::_rewrite_copilot_user_scope_paths` — the `prefix_map`
  (lines ~2936-2940) is **hardcoded**, not contract-derived; add
  `".github/skills/": ".copilot/skills/"` and remove the now-dead
  `".github/instructions/"` entry, so user-scope skills rewrite to
  `~/.copilot/skills/` and pass the path-jail (AC2 ships broken without this).
  Also update the copilot orphan-scan KeyError-default list (~line 3113) from
  `[".github/instructions/"]` to the new skill prefix.

**Done when:** copilot skills emit `.github/skills/<name>/SKILL.md`, the agent
regression test passes, dead instruction-file code is gone, the web wording in
code comments is corrected, and a user-scope copilot install rewrites skills to
`~/.copilot/skills/`.

### T4: Pack content opts into v0.12 and drops the false degradation

**Depends on:** T2

**Tests:**
- Goal-based: `test_shipped_packs_v07_declarations.py` `EXPECTED_PACK_VERSIONS`
  has `research`/`core` = `"0.12"`; all other packs unchanged (AC6).
- Goal-based: `test_shipped_pack_manifests.py:84` — the `core` value-pin
  (`expected_version = "0.10" if pack_name == "core" else "0.8"`) moves `core`
  to `"0.12"`; `research` is **not** in that file's `ALL_SHIPPED_PACKS` tuple
  (only `core` + the three addon packs), so it needs no edit here (AC6).
- Goal-based: `grep` over `packs/research/` finds no Copilot web-degradation
  wording except cloud-agent-scoped caveats (AC7).

**Approach:**
- `packs/research/pack.toml`: `[pack.adapter-contract] version = "0.12"`; rewrite
  the long Copilot caveat comment (lines ~19-28) — retrieval subagents are
  web-capable on Copilot CLI/app; degraded only on the cloud agent.
- `packs/core/pack.toml`: `[pack.adapter-contract] version = "0.12"`.
- `packs/research/.apm/skills/research/SKILL.md` + `references/retriever-interface.md`:
  remove/correct any Copilot web-degradation note.
- `packs/research/.apm/agents/{evidence-retriever,source-extractor}.md`: confirm
  they still declare `WebFetch`/`WebSearch` and project clean (no edit expected
  unless they carry a degradation comment).

**Done when:** both packs at `"0.12"`, research content free of false
degradation wording, the pack-version and grep tests green.

### T5: Test suite is green in both roots

**Depends on:** T2, T3, T4

**Tests:** (this task *is* the test reconciliation — these existing tests go
**red** on the flip and must be rewritten, not merely extended)
- `tests/unit/test_copilot_user_scope_wiring.py` — rewrite the three
  instruction-file-pinned assertions: the repo-prefix list at line ~33
  (`[".github/instructions/", ...]` → `.github/skills/`), the user-prefix list
  ~45-49 and projection keys ~62-64 / ~94 (`.copilot/instructions/…instructions.md`
  → `.copilot/skills/<name>/SKILL.md`). Assert the new `.github/skills/` →
  `.copilot/skills/` rewrite (AC2).
- `tests/unit/test_safety_repo_scope_prefixes.py` + `test_safety_scan_per_pack_scoping.py`
  — `.github/skills/` admitted at repo scope, `.copilot/skills/` at user scope.
- `tests/integration/test_install_copilot_full_parity.py` — lines ~86/92-93
  (repo) and ~160-164 (user) assert `*.instructions.md` populated; rewrite to
  assert `.github/skills/<name>/SKILL.md` and `~/.copilot/skills/<name>/SKILL.md`.
  Also bump the in-fixture pack manifest `version = "0.10"` at line ~223 to
  `"0.12"`.
- `tests/integration/test_install_repo_scope_per_adapter.py` — copilot install
  lands skills at the new target.
- `tests/integration/test_multi_pack_install.py` — the `_skill_path` helper
  (~line 135) returns `.github/instructions/<skill>.instructions.md`; update to
  the `.github/skills/<name>/SKILL.md` shape, and reshape
  `test_copilot_orphan_scan_finds_hooks_but_not_instructions` (~line 449): its
  premise (flat `<primitive>.instructions.md` stem evades the scanner) no longer
  holds once skills are a `direct-directory` tree with a bounded sweep that
  **does** cover copilot — widen/rename per the test's own "fails loudly so the
  parametrization can be widened" note. AC4's bounded sweep is the new contract.

**Approach:**
- Run full pytest in `packages/agentbundle/agentbundle/build/tests/` and
  `packages/agentbundle/tests/`; fix every assertion that pinned the old skill
  target / contract version. Add the focused tests named in T3 if not already
  added there.
- Refresh stale version-label docstrings in surviving copilot property tests
  that still pass but read `v0.10` — notably `test_contract_v08.py::~244` ("at
  v0.10 … copilot projects 4 of 5 primitives") → `v0.12` (the assertion is
  unchanged; only the label is stale).

**Done when:** `python -m pytest` green in both roots; no skipped/xfailed copilot
assertion hides a stale target.

### T6: Self-host build refreshes marketplace without drift

**Depends on:** T2, T3, T4

**Tests:**
- Goal-based: after `make build-self`, `git status` shows only intended changes
  (regenerated `marketplace.json` + any projected pack content); no unexpected
  reverts to projected paths, nothing silently dropped under `build/` (verify
  `git ls-files` for any new file).
- Goal-based: `make build-check` green.

**Approach:**
- `make build-self`; inspect `git status` and `git diff marketplace.json`
  (version bumps for research/core). Clear stray `__pycache__` before any
  drift gate (known local trap). Confirm via a clean check.

**Done when:** `make build-check` green, `git status` clean of unintended
projection reverts.

### T7: Doc blast radius reconciled + prior spec updated

**Depends on:** T2, T3

**Tests:**
- Goal-based `grep`: across `docs/`, `AGENTS.local.md`, `README.md` no surviving
  assertion that copilot skills are `instruction-file`/`.github/instructions/`
  or that Copilot custom agents lack web — except cloud-agent-scoped caveats (AC8).
- `lint-spec-status.py` reports no drift; backlog anchor (if the deferred
  Copilot-web item is closed) resolves or is removed cleanly (AC8, AC11).

**Approach:**
- `docs/guides/_shared/reference/adapter-support.md` — correct **all** copilot
  skill/web assertions: the Copilot table row (Skill cell instruction-file →
  SKILL.md, Subagent cell + its status word), the dedicated no-web-tool caveat
  block (~lines 51-55), **and** the summary guidance line (~lines 71-72) that
  tells readers to plan around the no-web caveat. Custom agents get `web` on
  CLI/app; only the cloud agent lacks it.
- `docs/guides/research/reference/research-pack.md` — besides any web-degradation note,
  correct lines ~131-133 ("Available only on hosts that support subagent
  dispatch (Claude Code)"): Copilot CLI/app custom agents now support both
  subagent dispatch and web, so the host-support phrasing must include Copilot.
- `docs/guides/research/tutorials/research-first-session.md` — remove the Copilot
  web-degradation note.
- `docs/architecture/agentbundle.md` — instruction-file-for-skills mentions → SKILL.md.
- `AGENTS.local.md` — (a) the coverage-asymmetry block (~lines 252-258) is keyed
  to copilot's flat `.github/instructions/<primitive>.instructions.md` shape and
  is invalidated by the `direct-directory` flip + bounded sweep — correct it.
  (b) **Flag (don't necessarily fix):** the agent-primitive table row (~line 113)
  showing copilot `agent` = `dropped` is **pre-existing** drift from RFC-0024
  (different primitive, not this PR's concern) — note it in the PR description;
  bundle-fix only if trivially same-area.
- `docs/backlog.md` — resolve the deferred Copilot-web item under the
  `## copilot-full-parity` heading (~lines 392-394): mark the web bullet
  **resolved** (struck/annotated "resolved by copilot-skills-and-web") rather
  than deleting the heading, and confirm no surviving `(deferred:)` marker in any
  spec still points at it (a dangling-anchor would fail `lint-spec-status.py`).
- `docs/specs/distribution-adapters/spec.md` — projection table copilot skill
  cell (line ~206) **and** the `instruction-file` mode definition at lines ~74-75
  whose worked example is "e.g. Copilot's `applyTo`" (copilot no longer uses the
  mode). Frozen (Shipped) spec → swap the example to a non-copilot one or note
  copilot's drop in append style; do not rewrite history.
- `docs/specs/copilot-full-parity/spec.md` + `plan.md` — update the now-superseded
  ACs/caveats with a forward pointer to this spec (append, don't rewrite history).
- `docs/specs/README.md` — **(a)** add a `copilot-skills-and-web` entry to the
  active spec list (new-spec step 7), and **(b)** adjust the existing
  copilot-full-parity entry's "no web tool / documented-degradation" phrasing so
  the README index no longer asserts the now-false degradation. Both edits, same
  file.
- `README.md` / `docs/guides/_shared/reference/README.md` — only if they assert these
  specifics.
- Name any blast-radius file deliberately left untouched in the PR description.

**Done when:** the grep finds no stale assertion, prior spec carries the forward
pointer, `docs/specs/README.md` lists this spec, `lint-spec-status.py` clean.

## Rollout

Pure catalogue/contract change — no runtime infra, no flag, no migration. The
contract version bump is the cutover; reversible by reverting the PR. The only
deployment-sequencing note: contract + pack version bumps must land **atomically**
in this one PR (a pack at `"0.12"` against a `"0.10"` contract, or vice versa,
fails validation), and `make build-self` must run after the pack bumps so
`marketplace.json` is consistent at merge.

## Risks

- **Lexical version-compare regressions** (`"0.12"` vs `"0.8"`/`"0.10"`) — a
  known trap on every contract bump; mitigated by running the full package
  pytest in both roots, not just `make build-check`.
- **CI-ungated test roots** — package pytest is wired per-path in CI, not in
  `make build-check`; a stale assertion can pass locally and red-CI. Run both
  roots by hand (spec § Always do).
- **Drift gates** — byte-identical twin (contract + schema) and the projection
  drift gate; stray `__pycache__` can false-trip the self-host dry-run. Clean
  the tree before `build-self`.
- **Erratum vs follow-on RFC** — **reviewer-cleared (2026-06-11):** the spec-mode
  adversarial reviewer judged the skill flip decision-worthy but the
  Approver-signed append-only erratum the right vehicle (flip-on-upstream-support
  with RFC-0009 precedent, atomic + revertible). No standalone RFC; note the
  cleared decision in the PR description.

## Changelog

- 2026-06-11: initial plan.
- 2026-06-11: spec-mode review pass 2 — added the `install.py`
  `_rewrite_copilot_user_scope_paths` hardcoded `prefix_map` + orphan-scan
  default edit (T3; AC2 ships broken without it), enumerated the four
  instruction-file-pinned tests that go red on the flip (T5:
  `test_copilot_user_scope_wiring`, `test_install_copilot_full_parity`,
  `test_multi_pack_install` `_skill_path` + orphan-scan reshape), and three more
  doc sites (T7: `research-pack.md` host-support line, `AGENTS.local.md`
  coverage-asymmetry block, `distribution-adapters` `instruction-file` example).
- 2026-06-11: spec-mode review pass 3 (clean of Blockers) — added three more
  contract-version value-pins in the CI-only `tests/` root that go red on the
  bump: `test_contract_v0_3_schema.py:81` (T2), `test_shipped_pack_manifests.py:84`
  core pin (T4), `test_install_copilot_full_parity.py:223` fixture (T5).
