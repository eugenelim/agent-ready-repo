# Spec: work-loop activation hook

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0005 (hook-body / hook-wiring), RFC-0022 (kiro-ide-hook)
- **Brief:** none
- **Contract:** none (uses shipped `hook-wiring` + `kiro-ide-hook` primitives; no contract change)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent working in a repo that installed the `core` pack is reliably reminded,
on every prompt, to use the `work-loop` skill for non-trivial work — in **both
Claude Code and Kiro IDE**. Today the only lifecycle hook (`session-start`) never
mentions work-loop, and the hook surfaces diverge by tool: Claude Code (and
Copilot/Cursor/Gemini/Codex) consume `hook-wiring`, while **Kiro IDE drops
`hook-wiring` entirely** and reads only standalone `.kiro/hooks/*.kiro.hook`
files — of which the catalogue ships none. So any Claude-side nudge can never
reach Kiro IDE. Success: a matched pair of hook artifacts in `core` that emit the
same "consider work-loop for non-trivial work" nudge on each surface's
per-prompt event, so neither tool silently skips the loop.

## Boundaries

### Always do

- Mirror the existing `session-start` hook's shape for the `hook-wiring` side
  (no `attach-to-agent`, no `id`); change only the event (`UserPromptSubmit`)
  and the command. This is the proven-safe shape across every adapter `core`
  targets.
- Keep the Claude-side message (hook-body stdout) and the Kiro-IDE-side message
  (`then.prompt` of the `.kiro.hook`) semantically aligned — same instruction,
  adapted to each mechanism.
- Keep the hook body input-free: it prints a static reminder and reads no
  stdin, env, files, or network (so it crosses no security boundary).
- Bump the `core` pack version (`pack.toml` + `.claude-plugin/plugin.json`) and
  add a `docs/product/changelog.md` `[Unreleased]` entry.
- Run `make build-self` and verify the projected artifacts + a clean `git
  status` (only the intended files changed).

### Ask first

- Extending the `hook-wiring` to the Kiro **CLI** (`kiro`/`kiro-cli`) targets.
  That requires an `attach-to-agent` field the `session-start` precedent
  deliberately omits ("Kiro is out of scope here"); Kiro IDE — the requested
  target — is already covered by the `kiro-ide-hook`. Out of scope here.
- Changing the per-prompt cadence to per-session, or making the nudge
  configurable.

### Never do

- Edit the adapter contract (`docs/contracts/adapter.toml`) or any adapter's
  projection code. This feature is pure pack content over shipped primitives.
- Touch the existing `session-start` hook (body or wiring).
- Have the hook body parse untrusted input or attempt to *classify* prompt
  triviality — a hook can't do that reliably; the skill's own "When this skill
  applies" governs the judgment.

## Testing Strategy

The catalogue's standard gates do **not** cover this work for free:
`make validate` validates only the adapter contract schema, `lint-packs` checks
only skill/agent metadata, and CI does not auto-discover pytest — every test path
is hand-wired in `.github/workflows/build-check.yml`. So the `check_kiro_ide_hook`
rail and the projection only gate if a test invokes them and that test is wired
into CI explicitly. One focused pytest module, added to `build-check.yml` with an
explicit step, is therefore the real gate; it covers:

- **Schema correctness of the `.kiro.hook`** (required fields; `when.type` ∈
  `ide-event-vocabulary`; `then.type` ∈ `ide-action-vocabulary`): goal-based —
  the test calls `check_kiro_ide_hook(packs/core, …)` and asserts it returns
  `None`.
- **Kiro IDE end-to-end projection from the real `core` pack**: goal-based,
  integration surface — the test invokes the shipped `kiro_ide_hook.project()`
  with the **real on-disk contract values** against `packs/core` and asserts the
  output path `.kiro/hooks/core--work-loop-check.kiro.hook` and the
  `promptSubmit` / `askAgent` / non-empty `then.prompt` shape. This is the
  primary proof of the Kiro IDE path, since `build-self` (adapters `claude-code`
  + `codex` only) does not emit kiro-ide.
- **Hook body real invocation**: goal-based — the test runs `python
  packs/core/.apm/hooks/work-loop-check.py` via subprocess and asserts exit 0,
  non-empty stdout, and that the output mentions `work-loop`.
- **Message alignment**: goal-based — the test asserts both the body stdout and
  the `.kiro.hook` `then.prompt` mention `work-loop` (the only enforceable floor
  for the "keep semantically aligned" boundary).
- **Claude Code / Codex projection of the `hook-wiring`**: goal-based,
  exercised by running `make build-self` and asserting the `UserPromptSubmit`
  entry lands in `.codex/hooks.json` and `tools/hooks/work-loop-check.py` is
  projected.

## Acceptance Criteria

- [x] `packs/core/.apm/hooks/work-loop-check.py` exists, is pure-stdlib Python,
  prints a work-loop reminder of **≤ 6 lines** to stdout, reads no input
  (stdin/env/files/network), and exits 0.
- [x] `packs/core/.apm/hook-wiring/work-loop-check.toml` wires that body to the
  `UserPromptSubmit` event, structurally mirroring `session-start.toml` (no
  `attach-to-agent`, no `id`).
- [x] `packs/core/.apm/kiro-ide-hooks/work-loop-check.kiro.hook` is a valid
  kiro-ide-hook: `when.type` = `promptSubmit`, `then.type` = `askAgent`, with a
  `then.prompt` carrying the work-loop reminder.
- [x] A focused pytest module asserts: (a) `check_kiro_ide_hook(packs/core, …)`
  returns `None`; (b) the shipped projector produces
  `.kiro/hooks/core--work-loop-check.kiro.hook` with the `promptSubmit` /
  `askAgent` / non-empty `then.prompt` shape; (c) the hook body run via
  subprocess exits 0 with non-empty stdout; (d) both the body stdout and the
  `.kiro.hook` `then.prompt` mention `work-loop`. The module is wired into
  `.github/workflows/build-check.yml` as an explicit pytest step.
- [x] After `make build-self`, `.codex/hooks.json` contains the
  `UserPromptSubmit` wiring alongside the existing `SessionStart`, and
  `tools/hooks/work-loop-check.py` is present; `git status` shows only intended
  changes.
- [x] `core` pack version is bumped in both `pack.toml` and
  `.claude-plugin/plugin.json`; `.claude-plugin/marketplace.json` reflects the
  bumped `core` version after `make build-self`; `docs/product/changelog.md` has
  an `[Unreleased]` entry naming the hook.
- [x] Hook enumerations that would otherwise go stale are synced in the same PR:
  the `core` description (`pack.toml` + `plugin.json`) and `tools/hooks/README.md`
  name the new hook.
- [x] The CI-ungated fixtures that pin core's hook-wiring → kiro drop-warning
  contract (`test_install_event_dropped_wirings.py`,
  `test_validate_hook_wiring_per_file_compatibility.py`) are updated for the new
  `work-loop-check.toml` entry and wired into `build-check.yml`. (The adopter-
  visible `agentbundle validate core` info line now lists two dropped wirings;
  noted in the changelog.)
- [x] `make build-check` is green.

## Assumptions

- Technical: Kiro IDE loads `.kiro/hooks/**/*.kiro.hook` natively, and
  `kiro-ide` drops `hook-wiring`, so the IDE requires a `kiro-ide-hook` (source:
  probe — adapter.toml:330-364, ground-truth from extension.js, 2026-06-19).
- Technical: `UserPromptSubmit` is mapped by every adapter `core` targets —
  copilot (`userPromptSubmitted`), cursor (`beforeSubmitPrompt`), gemini
  (`BeforeAgent`), codex (verbatim merge-json) (source: probe —
  copilot_hooks_json.py, adapter.toml:602/689, 2026-06-19).
- Technical: `build-self` projects only `claude-code` + `codex`
  (`SELF_HOST_ADAPTERS`), so the kiro-ide-hook is source-only in this repo and
  proven by tests, not by a committed `.kiro/` artifact (source: probe —
  self_host.py:85, 2026-06-19).
- Technical: a `hook-wiring` without `attach-to-agent` is silently skipped for
  kiro/kiro-cli projection, and the validate rail only refuses it when
  kiro/kiro-cli is a target adapter — which `core` is not (source: probe —
  kiro.py:340-341, scope_rails.py:309-355, session-start.toml comment,
  2026-06-19).
- Product: per-prompt cadence, ships to adopters via `core` (source: user
  confirmation 2026-06-19).
