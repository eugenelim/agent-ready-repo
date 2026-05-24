# Spec: wire-session-start-hook

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0001 (adapter contract), RFC-0004 (scope dimension at v0.2). The v0.3 forks introduced by RFC-0005 are explicitly out of scope here.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

After an adopter runs `agentbundle install core` into a fresh tree, opening a
Claude Code session in that tree primes the agent with the contents of
`docs/knowledge/patterns.jsonl` automatically — no hand-editing of
`.claude/settings.local.json`. Today the README at `tools/hooks/README.md`
asks adopters to paste a JSON snippet by hand; that's the gap. The hook
body (`packs/core/.apm/hooks/session-start.py`) already ships and projects
to `tools/hooks/session-start.py` on install; the missing piece is the
**wiring** that binds it to Claude Code's `SessionStart` lifecycle event
at repo scope.

## Non-goals

Out of scope, *intentionally*:

- **Kiro support.** Neither Kiro IDE nor Kiro CLI has a session-start
  lifecycle event. The architecturally-correct Kiro primitive for "make
  this content persistently visible to the agent" is `steering`, which
  the adapter contract does not model today. Kiro support belongs in
  its own spec that introduces the `steering` primitive. **This PR
  ships zero Kiro-targeted fields** — no `attach-to-agent`, no
  Kiro-vocabulary events, no v0.3 forward-looking declarations under
  `packs/core/.apm/`. The parallel Kiro spec owns the entire Kiro
  surface.
- **`pre-pr.py` wiring.** Claude Code has no PR-open lifecycle event;
  the closest event (`Stop`) fires after every agent turn, wrong
  semantics for "before PR." Remains a manual / git-hook command.
- **User-scope hook-wiring.** Blocked on RFC-0005 T5/T7. Repo-scope only.
- **Other adapters** (Codex, Copilot). Their adapters drop or do not
  ship hook-wiring projections.

## Boundaries

### Always do

- Edit the pack upstream (`packs/core/seeds/...` and `packs/core/.apm/...`)
  and run `make build-self` to project. Treat projected paths as
  read-only artifacts.
- Model new `hook-wiring/*.toml` files on the live merge-json shape that
  `packages/agentbundle/agentbundle/build/adapters/claude_code.py:84-109`
  actually consumes: a top-level `[hooks.<EventName>]` array of tables
  with `command` and `matcher`.
- Verify behavior with a construction test that installs a synthetic
  minimal pack into a tmp dir and asserts the merged
  `.claude/settings.local.json` contains the binding.

### Ask first

- Modifying `packages/agentbundle/agentbundle/_data/adapter.toml`,
  `pack.schema.json`, or anything in `packages/agentbundle/agentbundle/build/`.
  None of those need to change for v0.2 hook-wiring to work.
- Touching `self_host.py`'s `EXCLUDED_PATTERNS`. `.claude/settings.local.json`
  is excluded by design; the spec accepts that and doesn't try to
  project the settings file through `make build-self`.

### Never do

- **Edit projected paths directly.** The repo self-hosts `packs/core/`,
  which means `docs/CONVENTIONS.md`, `tools/hooks/session-start.py`,
  `.claude/agents/*`, `.claude/skills/*`, and any `.claude/*` artifacts
  are projection outputs. Edits must land in the pack upstream and flow
  through `make build-self`. (Structural rail.)
- **Bump `packs/core/pack.toml`'s `[pack.adapter-contract] version`
  past `0.2` in this PR.** v0.2 is the pipeline-of-record; the v0.3
  table at `_data/adapter.toml:88-93` is forward-looking metadata
  only. Bumping to v0.3 would trigger the `_kiro_target_adapters`
  heuristic at `validate.py:328-366` and the event-vocabulary rail,
  re-opening the Kiro design conversation this spec explicitly defers.
  (Structural rail.)
- **Use the v0.3 `[adapter."claude-code".projections.hook-wiring]`
  table** as the consumer for any code path this PR adds or touches.
  The legacy `[[adapter."claude-code".projection]]` array at
  `_data/adapter.toml:64-69` is the pipeline-of-record.
- **Add `pre-pr.py` wiring to Claude Code's `Stop` event.** `Stop`
  fires after every agent turn — wrong semantics for "before PR opens."
- **Introduce a new adapter, a new primitive, a new on-conflict mode,
  or a new wiring-TOML field** (e.g. `allowed-adapters`, `id` at
  repo scope, `attach-to-agent`). The TOML stays minimal — `command`
  and `matcher` under `[hooks.<EventName>]`. Nothing else.

## Testing Strategy

Three modes, mapped to the spec's outcomes:

- **TDD (logic — the wiring contract).** A new construction test under
  `packages/agentbundle/tests/integration/` stages a synthetic minimal
  pack and runs `install.run(...)`, then asserts the projected
  `.claude/settings.local.json` JSON contains a `hooks.SessionStart`
  entry whose nested `hooks[].command` is `python tools/hooks/session-start.py`.
  TDD because the assertion compresses an invariant: "any v0.2 pack
  that ships this wiring TOML, installed at repo scope, produces this
  settings shape." The test fails red without the wiring TOML in place.
- **Goal-based (the projection pipeline).** `make build-self` exits 0
  after the seed edits; `git diff` shows the prose change on the
  projected `docs/CONVENTIONS.md` mirrors the seed edit. The wiring
  TOML itself does **not** produce any projected-file diff under
  `make build-self` (it lands inside `packs/core/.apm/`, which is in
  `EXCLUDED_PATTERNS`); that's expected and `make build-self` clean
  is the gate.
- **Goal-based (regression).** `tools/test-all.sh` and
  `python tools/hooks/pre-pr.py` exit 0. The targeted upgrade-fixture
  tests (`test_upgrade_cmd.py`, `test_install_cmd.py`,
  `test_tier_invariants.py`) continue to pass after the legacy-fixture
  rewrite, including any new projected-file rows that the rewrite
  introduces into `render_pack`'s output.

No manual QA mode — the change has no UX surface; the artifact is a
config file.

## Acceptance Criteria

- [ ] **AC1.** After `agentbundle install core` (at **repo scope**) into
      a fresh adopter tree with no pre-existing
      `.claude/settings.local.json`, that file is written with
      `data["hooks"]["SessionStart"]` containing exactly one outer entry
      that has no `matcher` field (or an empty one) and whose inner
      `hooks` array contains exactly one element with
      `type = "command"` and `command = "python tools/hooks/session-start.py"`.
      This is Claude Code's documented nested-shape SessionStart schema
      (per [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)
      and the existing audit snippet at `tools/hooks/README.md:99-111`).
- [ ] **AC1a (brownfield).** When `.claude/settings.local.json` pre-exists
      and the adopter has edited it (its SHA does not match the
      install state's recorded SHA), the install pipeline writes a
      `.claude/settings.local.json.upstream` companion via
      `safety.write_companion` per the documented Tier-2 path in
      `packages/agentbundle/agentbundle/commands/install.py:537-548`. The
      live file is **not** overwritten; the adopter must reconcile.
      This is the documented `on-conflict = "merge-managed-key-only"`
      posture from `_data/adapter.toml:69`, and it predates this spec —
      this AC pins that the spec does not change that behavior.
- [ ] **AC2.** `tools/hooks/session-start.py` still lands at that path
      post-install (the `hook-body` projection is unchanged).
- [ ] **AC3.** `tools/hooks/pre-pr.py` still lands at that path post-install
      and is **not** wired to any Claude Code lifecycle event. It remains
      a manual / git-hook command, as documented today.
- [ ] **AC4.** The following test files continue to pass with no
      modification beyond what AC5 requires:
      `packages/agentbundle/tests/integration/test_install_cmd.py`,
      `test_upgrade_cmd.py`, `test_uninstall_cmd.py`,
      `test_tier_invariants.py`, `test_install_dual_scope.py`.
- [ ] **AC5.** Legacy upgrade-catalogue fixtures at
      `packages/agentbundle/tests/fixtures/upgrade/catalogue_v{1,2,3}/packs/core/.apm/hook-wiring/pre-commit.toml`
      use the live `[[hooks.PreToolUse]]` shape. The `command` string
      is the static stub `"true"` (not `$HOOK_BODY_PATH`) — these
      fixtures test SHA tracking across upgrade versions, not live
      hook firing, and the stub makes that intent explicit. The
      `matcher = "Bash|Edit"` substring assertion at
      `test_upgrade_cmd.py:319` continues to hold against the
      rewritten v2 fixture. **Any new `.claude/settings.local.json`
      row that the rewrite introduces into `render_pack`'s output
      must round-trip cleanly through `test_upgrade_cmd.py`'s
      byte-comparison checks** (the rewrite stays equally honored
      by `render_pack` and `install` because both share the same
      `_project_merge_json` code path).
- [ ] **AC6.** `tools/hooks/README.md § Wiring → Claude Code` reframes
      the JSON snippet as audit reference (post-fact documentation of
      what the install pipeline writes), not as an adopter instruction
      to paste by hand. The introductory line that today reads
      "Add to your project-local `.claude/settings.json` (gitignored)"
      is corrected to name `.claude/settings.local.json` (the actual
      target per `_data/adapter.toml:67`; the current README path is a
      pre-existing bug). The `pre-pr.py` paragraph is unchanged.
- [ ] **AC7.** `packs/core/seeds/docs/CONVENTIONS.md` (the pack upstream)
      reframes the two affected paragraphs — the enforcement-triplet
      "wiring is consumer-specific" sentence and the Profile-C
      "session-start hook is wired in the consumer's `.claude/settings.json`"
      sentence — to state that session-start lands wired automatically,
      while `pre-pr` stays consumer-wired because it's not an
      agent-lifecycle event.
- [ ] **AC8.** `make build-self` exits 0 after the seed edits; the
      projected `docs/CONVENTIONS.md` mirrors AC7's seed edit. The
      wiring TOML itself produces **no projected-file diff** in the
      workspace tree (`.claude/settings.local.json` is excluded by
      `self_host.py:248`; `tools/**` is excluded by line 269). The
      seed is the only place the prose is hand-edited.
- [ ] **AC9.** A new construction test under
      `packages/agentbundle/tests/integration/` stages a minimal
      synthetic pack inside a tmp catalogue, runs `install.run(...)`,
      and asserts that the produced `.claude/settings.local.json`
      contains `data["hooks"]["SessionStart"][0]["hooks"][0]["command"]`
      equal to the literal string `python tools/hooks/session-start.py`.
      The test must fail red if `packs/core/.apm/hook-wiring/session-start.toml`
      is absent or its TOML produces a different shape on disk.
- [ ] **AC10.** A smoke check against the **real** `packs/core/`: a
      small pytest under `packages/agentbundle/tests/integration/`
      runs `install.run(...)` with the real `packs/core/` directory
      as the catalogue source, into `tmp_path`. Parses the produced
      `.claude/settings.local.json`. Asserts
      `data["hooks"]["SessionStart"][0]["hooks"][0]["command"] ==
      "python tools/hooks/session-start.py"`. This guards against the
      synthetic-pack test passing while core's actual wiring is broken
      by an unrelated change.
