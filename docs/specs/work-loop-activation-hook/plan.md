# Plan: work-loop activation hook

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Pure pack content in `core`, no contract or adapter-code change. Three new source
files form the matched pair: a hook body (`work-loop-check.py`) and a
`UserPromptSubmit` `hook-wiring` (`work-loop-check.toml`) for the
hook-wiring-consuming adapters (Claude Code, Copilot, Cursor, Gemini, Codex), and
a standalone `kiro-ide-hook` (`work-loop-check.kiro.hook`, `promptSubmit` +
`askAgent`) for Kiro IDE — which drops hook-wiring and reads only `.kiro.hook`
files. The hook-wiring file is a structural clone of the proven `session-start.toml`
(differing only in event + command), which de-risks the cross-adapter projection.
The riskiest part is the kiro-ide-hook being the catalogue's *first*, so its
verification leans on (a) the `check_kiro_ide_hook` validate rail, already wired
into `build-check`, and (b) a focused projection test against the real `core`
pack. Finish with the version bump, changelog, README/description sync, and
`make build-self` to regenerate the committed `.codex/hooks.json` and
`tools/hooks/` projections.

## Constraints

- RFC-0005 (hook-body / hook-wiring forks), RFC-0022 (kiro-ide-hook activation).
- `session-start.toml` precedent: `core` hook-wiring carries no `attach-to-agent`
  and is therefore out of scope for kiro/kiro-cli (the agent-JSON-merge adapters).
- `SELF_HOST_ADAPTERS = ("claude-code", "codex")` — build-self does not emit
  kiro-ide; the `.kiro.hook` is source + test verified only.
- CONVENTIONS § version bump for non-cosmetic pack edits; changelog `[Unreleased]`.

## Construction tests

**Integration tests:** the kiro-ide-hook real-pack projection test (T3) spans the
projector + the real `core` pack source; see its `Tests:`.
**Manual verification:** none beyond the subprocess assertion in T3 (the body's
real invocation is gated by a test, not left to manual QA).

## Design (LLD)

### Design decisions

- **Two primitives, one intent.** The Claude side runs a `command` hook whose
  stdout is injected as context; the Kiro IDE side fires `askAgent` with an inline
  prompt. These are different mechanisms (Kiro IDE `runCommand` does *not* feed
  the agent), so the reminder text is duplicated by necessity rather than shared
  via a placeholder. Traces to: AC1–AC3.
- **Static reminder, no classification.** The body emits a fixed nudge; deciding
  triviality is the agent's job per the skill's "When this skill applies". Keeps
  the body input-free and off every security boundary. Traces to: AC1.
- **Event = `UserPromptSubmit` / `promptSubmit`** (per-prompt), the strongest
  "always activated" guarantee, chosen over `SessionStart`. Traces to: AC2, AC3.

### Interfaces & contracts

- `hook-wiring` primitive → `.apm/hook-wiring/` (adapter.toml:95). `kiro-ide-hook`
  primitive → `.apm/kiro-ide-hooks/` (adapter.toml:103). No contract file is
  edited; both are shipped primitives. Traces to: AC2, AC3.

## Tasks

### T1: hook body emits a work-loop reminder

**Depends on:** none

**Tests:**
- `python packs/core/.apm/hooks/work-loop-check.py` prints a non-empty reminder
  mentioning the work-loop skill and exits 0 (manual QA — real invocation, AC1).
- The script imports only stdlib and reads no stdin/env/files (inspection).

**Approach:**
- Write `packs/core/.apm/hooks/work-loop-check.py`: a `main()` that prints a
  concise (2–4 line) reminder to stdout and returns 0. Pure stdlib; no args.
- Header docstring notes the companion `.kiro.hook` carries the parallel prompt.

**Done when:** running the script prints the reminder and exits 0; stdout
recorded.

### T2: hook-wiring binds the body to UserPromptSubmit

**Depends on:** T1

**Tests:**
- After `make build-self`, `.codex/hooks.json` has a `UserPromptSubmit` entry
  whose command is `python tools/hooks/work-loop-check.py`, alongside the
  existing `SessionStart` (goal-based, AC6).
- `make validate` / `lint-packs` green (AC4).

**Approach:**
- Write `packs/core/.apm/hook-wiring/work-loop-check.toml` as a structural clone
  of `session-start.toml`: `[[hooks.UserPromptSubmit]]` with one
  `{ type = "command", command = "python tools/hooks/work-loop-check.py" }`. No
  `attach-to-agent`, no `id`. Update the header comment for the new event/command.

**Done when:** lint/validate pass and the wiring is present in source.

### T3: kiro-ide-hook for Kiro IDE + the focused CI-wired test

**Depends on:** T1, T2 (the test exercises the body and references the wiring)

**Tests:** (one new module, e.g. `packages/agentbundle/tests/unit/test_core_work_loop_hook.py`)
- `check_kiro_ide_hook(packs/core, …)` returns `None` (AC3/AC4 schema floor).
  Note: the rail IS reachable via the per-pack `agentbundle validate <pack>` CLI
  (`commands/validate.py:268`), but `make build-check` / `lint-packs` / the `make
  validate` target never run it against `core` — so this CI-wired test is the only
  thing that gates the rail here.
- Invoke `kiro_ide_hook.project()` with the **real on-disk contract values**:
  read `target.repo` from `docs/contracts/adapter.toml` via stdlib `tomllib`
  (`adapter."kiro-ide".projections."kiro-ide-hook".target.repo`) and pass it as
  the projector's `target_template`; do **not** retype the path or synthesise it
  like `test_kiro_ide_hook_e2e.py` (that fixture uses the wrong `<pack>/<name>`
  separator). Run against `packs/core`; assert output file
  `.kiro/hooks/core--work-loop-check.kiro.hook` with `when.type == "promptSubmit"`,
  `then.type == "askAgent"`, non-empty `then.prompt` (AC4b/AC5 path proof).
- `subprocess.run([sys.executable, "packs/core/.apm/hooks/work-loop-check.py"])`
  → returncode 0, non-empty stdout, stdout mentions `work-loop` (AC1).
- Both the body stdout and the `.kiro.hook` `then.prompt` mention `work-loop`
  (alignment floor).

**Approach:**
- Write `packs/core/.apm/kiro-ide-hooks/work-loop-check.kiro.hook`: JSON with
  `name`, `description`, `version: "1"`, `when: {type: promptSubmit}`,
  `then: {type: askAgent, prompt: <work-loop reminder>}`.
- Write the test module above; resolve repo root via `Path(__file__).parents[N]`
  as the sibling tests do.
- **Wire it into CI:** add an explicit step to `.github/workflows/build-check.yml`
  (`working-directory: packages/agentbundle`, `python -m pytest
  tests/unit/test_core_work_loop_hook.py`) — CI does not auto-discover pytest.

**Done when:** the focused module is green locally and a CI step invokes it.

### T4: version bump, changelog, doc/description sync

**Depends on:** T1, T2, T3

**Tests:**
- `pack.toml` and `plugin.json` versions match and are bumped from 0.4.9
  (inspection, AC7).
- `docs/product/changelog.md` has an `[Unreleased]` entry naming the hook (AC7).
- The `core` description (pack.toml + plugin.json) and `tools/hooks/README.md`
  name the new hook (AC8 doc-sync).

**Approach:**
- Bump `core` 0.4.9 → 0.4.10 in `pack.toml` and `.claude-plugin/plugin.json`.
- Update the `core` description (pack.toml + plugin.json) hook enumeration
  ("pre-pr + session-start hooks" → include the work-loop nudge).
- Add a `### work-loop-check.py` subsection to `tools/hooks/README.md` and fix
  its "Two … hooks" count → three. Check `packs/core/README.md`'s hook prose and
  sync only if it enumerates hooks.
- Add the changelog `[Unreleased]` entry.

**Done when:** versions/changelog/docs reflect the new hook.

### T5: build-self + verify clean tree

**Depends on:** T1, T2, T3, T4

**Tests:**
- `make build-self` succeeds; `git status` shows only intended files
  (`tools/hooks/work-loop-check.py`, `.codex/hooks.json`,
  `.claude-plugin/marketplace.json` reflecting core 0.4.10, plus the source +
  docs + test + CI wiring); no stray `__pycache__` or reverted projections
  (AC6, AC8). `.claude/settings.local.json` is gitignored and won't appear.
- `make build-check` green (AC8).

**Approach:**
- Run `make build-self`; inspect diff; confirm marketplace.json regenerated to
  0.4.10; clear any `__pycache__`; confirm against a clean expectation.

**Done when:** `build-check` green and `git status` clean of unintended changes.

## Rollout

Pure content addition; reversible by removing the three source files and the
version bump. No infra, no migration, no external system. Ships to adopters on
the next `core` pack release; lands in this repo's tree via `build-self` (Claude
+ Codex surfaces) at merge.

## Risks

- **Per-prompt noise.** The nudge fires every turn, including on trivial prompts.
  Mitigated by keeping it to 2–4 lines. Accepted per the product decision.
- **First kiro-ide-hook in the catalogue.** Mitigated by the validate rail
  (already in build-check) + the focused projection test.
- **New test not CI-wired** (memory: package tests gate only by explicit
  per-path wiring). Mitigated by extending an already-wired test module.

## Changelog

- 2026-06-19: initial plan.
