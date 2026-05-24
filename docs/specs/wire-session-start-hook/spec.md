# Spec: wire-session-start-hook

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0001 (adapter contract), RFC-0004 (scope dimension at v0.2). The v0.3 forks introduced by RFC-0005 are explicitly out of scope here.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

After an adopter runs `agentbundle install core` into a fresh tree, the
dist-tree it produces ships a Claude-plugin layout under
`<output>/claude-plugins/core/` whose `.claude/settings.local.json`
already contains the `SessionStart` binding that primes the agent with
the contents of `docs/knowledge/patterns.jsonl`. The adopter no longer
hand-pastes the JSON snippet documented at `tools/hooks/README.md`.
The hook body (`packs/core/.apm/hooks/session-start.py`) already ships
and projects to `<output>/claude-plugins/core/tools/hooks/session-start.py`
on install; the missing piece is the **wiring** that binds it to
Claude Code's `SessionStart` lifecycle event at repo scope. The same
wiring is also projected through self-host (`make build-self`) onto
this repo's flat workspace path `<workspace>/.claude/settings.local.json`
(gitignored); that's the bridge between the install-time AC1 and the
self-host AC8 — two projection surfaces, identical JSON body.

**Consumption precondition.** Claude Code reads the dist-tree's
`claude-plugins/<pack>/.claude/settings.local.json` only when the
adopter has *enrolled* the bundle as a plugin marketplace — i.e.
`.claude-plugin/marketplace.json` is discovered and the pack is
installed via `claude plugin install` (or the dev-mode equivalent).
Running Claude Code from a tree where the marketplace is **not**
enrolled does NOT pick up the binding; the file sits unread inside
`claude-plugins/<pack>/`. That enrollment flow is the
**install-via-plugin** route documented at
[code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference)
and is owned by the install→adapt chain (the `claude-plugins-install-route`
spec covers the marker-write parity gap for the Claude-plugins
route specifically; this spec assumes the marketplace mechanism
itself, not RFC-0008's marker work).

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
- **Adopters running Claude Code from the install-output tree without
  enrolling the marketplace.** That flow doesn't pick up the dist-tree
  binding; Claude Code only consumes `claude-plugins/<pack>/.claude/...`
  when the marketplace is enrolled. The install-via-plugin enrollment
  flow (and any marker-write parity around it) is owned by RFC-0008's
  `claude-plugins-install-route` spec, not this one.
- **Brownfield protection at the plugin cache path.** Once the
  marketplace is enrolled, the adopter's actual edit-target shifts to
  the per-user plugin cache (typically
  `~/.claude/plugins/cache/<marketplace>/<pack>/<version>/.claude/...`).
  AC1a's Tier-2 mechanism still fires at the dist-tree path, but the
  *user-facing* brownfield protection has shifted out from under this
  spec. Out of scope here; revisit when a future spec touches the
  plugin cache surface.

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
  `<target>/claude-plugins/<pack>/.claude/settings.local.json` contains
  the binding.

### Ask first

- Modifying `packages/agentbundle/agentbundle/_data/adapter.toml`,
  `pack.schema.json`, or anything in `packages/agentbundle/agentbundle/build/`.
  None of those need to change for v0.2 hook-wiring to work.
- Touching `self_host.py`'s `EXCLUDED_PATTERNS`. The flat-path
  `.claude/settings.local.json` is intentionally excluded from the
  `make build-check` unclassified-path enumeration (it IS projected
  by self-host's adapter pipeline; it's just gitignored, so it
  doesn't show as drift).

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
  pack and runs `install.run(...)`, then asserts the produced
  `<target>/claude-plugins/<pack>/.claude/settings.local.json` contains
  a `hooks.SessionStart` entry whose nested `hooks[].command` is
  `python tools/hooks/session-start.py`. The assertion compresses an
  invariant: "any v0.2 pack that ships this wiring TOML, installed at
  repo scope, produces this settings shape at the dist-tree path." Note:
  because the synthetic pack inlines the wiring TOML, this test acts as
  a self-contained contract test (always green when the wiring shape is
  correct); the red-before-green pivot lives in T7's smoke check
  against real `packs/core/`, which is red until T2 lands the wiring
  TOML in the real pack.
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
      a fresh adopter tree, the file
      `<output>/claude-plugins/core/.claude/settings.local.json` is
      written with `data["hooks"]["SessionStart"]` containing exactly
      one outer entry that has no `matcher` field (or an empty one) and
      whose inner `hooks` array contains exactly one element with
      `type = "command"` and `command = "python tools/hooks/session-start.py"`.
      This is Claude Code's documented nested-shape SessionStart schema
      (per [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)
      and the existing audit snippet at `tools/hooks/README.md:99-111`).
      The per-pack `claude-plugins/<pack>/` prefix is the dist-tree
      Claude-plugin layout `render_pack` produces at repo scope; Claude
      Code's plugin marketplace consumes it from there.
- [ ] **AC1a (brownfield).** When the dist-tree settings file
      (`<output>/claude-plugins/core/.claude/settings.local.json`)
      pre-exists and its SHA does not match the install state's
      recorded SHA, the install pipeline writes a
      `<output>/claude-plugins/core/.claude/settings.local.json.upstream`
      companion via `safety.write_companion` per the documented
      Tier-2 path. The producer of the dist-tree relpath is
      `agentbundle.render.render_pack` (called from
      `packages/agentbundle/agentbundle/commands/install.py:438`); the
      per-relpath Tier-2 classifier is `_classify_for_install`
      (dispatched at `install.py:537-548`; body at `install.py:1411`). The live file is **not** overwritten; the
      adopter must reconcile. This is the documented
      `on-conflict = "merge-managed-key-only"` posture from
      `_data/adapter.toml:69`, and it predates this spec — this AC
      pins that the spec does not change the *mechanism*. (For where
      the user-facing brownfield case has shifted to under
      marketplace enrollment, see Non-goals' plugin-cache carve-out.)
- [ ] **AC2.** The hook body still lands post-install at
      `<output>/claude-plugins/core/tools/hooks/session-start.py` (the
      `hook-body` projection is unchanged; the `tools/hooks/` segment
      stays the same, just nested under the dist-tree's
      `claude-plugins/<pack>/` prefix at repo scope).
- [ ] **AC3.** The `pre-pr.py` hook body still lands post-install at
      `<output>/claude-plugins/core/tools/hooks/pre-pr.py` and is **not**
      wired to any Claude Code lifecycle event. It remains a manual /
      git-hook command, as documented today.
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
      rewritten v2 fixture. **Any new
      `claude-plugins/core/.claude/settings.local.json` key that the
      rewrite introduces into `render_pack`'s output dict must
      round-trip cleanly through `test_upgrade_cmd.py`'s
      byte-comparison checks** (the rewrite stays equally honored
      by `render_pack` and `install` because both share the same
      `_project_merge_json` code path).
- [ ] **AC6.** `tools/hooks/README.md` two-surface reframe.
      (a) `## Wiring` umbrella intro (today: "The hooks are configured
      at the consumer side. The template does not ship a committed
      `.claude/settings.json` …") is qualified to acknowledge the
      session-start exception: the SessionStart binding for Claude Code
      *is* shipped pre-wired by the install pipeline; everything else
      under § Other tools and `pre-pr.py` stays consumer-side. The
      surviving umbrella prose must contain no sentence that flatly
      claims the template ships no committed Claude-Code wiring without
      naming the SessionStart exception in the same paragraph.
      (b) `### Claude Code` subsection reframes the JSON snippet as
      audit reference (post-fact documentation of what the install
      pipeline writes), not an adopter instruction to paste by hand.
      The introductory line that today reads "Add to your project-local
      `.claude/settings.json` (gitignored)" is removed (it was always
      wrong about the filename — the adapter writes
      `.claude/settings.local.json`, per `_data/adapter.toml:67`). The
      replacement prose names two surfaces explicitly: the
      install-via-`agentbundle` projection target
      (`<output>/claude-plugins/core/.claude/settings.local.json` —
      the dist-tree path the install pipeline writes; Claude Code's
      plugin marketplace ingests it, and the user-facing edit-target
      shifts to the per-user plugin cache post-enrollment, see
      Non-goals), and the self-host projection target
      (`<workspace>/.claude/settings.local.json` — the flat path
      `make build-self` produces in this repo, gitignored). The JSON
      snippet body itself is unchanged — it's the shape both
      projections write. The `pre-pr.py` paragraph is unchanged.
- [ ] **AC7.** `packs/core/seeds/docs/CONVENTIONS.md` (the pack upstream)
      reframes the two affected paragraphs — the enforcement-triplet
      "wiring is consumer-specific" sentence and the Profile-C
      "session-start hook is wired in the consumer's `.claude/settings.json`"
      sentence — to state that session-start lands wired automatically,
      while `pre-pr` stays consumer-wired because it's not an
      agent-lifecycle event.
- [ ] **AC8.** `make build-self` exits 0 after the seed edits; the
      projected `docs/CONVENTIONS.md` mirrors AC7's seed edit. The
      wiring TOML produces no `git status` drift: self-host's adapter
      pipeline (`_project_all_adapters` at
      `packages/agentbundle/agentbundle/build/self_host.py:178`) DOES
      write `<workspace>/.claude/settings.local.json` (flat path; same
      JSON the install-via-`agentbundle` dist-tree carries), but
      that file is gitignored (`.gitignore:18`) so `git status` stays
      clean. `EXCLUDED_PATTERNS` at `self_host.py:248` doesn't suppress
      the projection — it only removes the path from the
      unclassified-path enumeration consumed by `make build-check`.
      The seed is the only place the prose is hand-edited.
- [ ] **AC9.** A new construction test under
      `packages/agentbundle/tests/integration/` stages a minimal
      synthetic pack inside a tmp catalogue, runs `install.run(...)`,
      and asserts that the produced
      `<target>/claude-plugins/<pack-name>/.claude/settings.local.json`
      contains `data["hooks"]["SessionStart"][0]["hooks"][0]["command"]`
      equal to the literal string `python tools/hooks/session-start.py`.
      The test must fail red if the staged synthetic-pack wiring TOML
      is absent or its shape differs from the documented nested form.
      (The synthetic test inlines its own wiring TOML; the
      red-before-green pivot against the *real* `packs/core/...session-start.toml`
      lives in T7's smoke check — AC10.)
- [ ] **AC10.** A smoke check against the **real** `packs/core/`: a
      small pytest under `packages/agentbundle/tests/integration/`
      runs `install.run(...)` with the real `packs/core/` directory
      as the catalogue source, into `tmp_path`. Parses the produced
      `tmp_path/claude-plugins/core/.claude/settings.local.json`. Asserts
      `data["hooks"]["SessionStart"][0]["hooks"][0]["command"] ==
      "python tools/hooks/session-start.py"`. This guards against the
      synthetic-pack test passing while core's actual wiring is broken
      by an unrelated change.
