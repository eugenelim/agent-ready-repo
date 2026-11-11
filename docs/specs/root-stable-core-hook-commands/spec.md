# Spec: core hooks start from any directory below the repository root

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (changes the command string that an agent host executes, and edits the protected `packages/agentbundle/**` hook projection if the root token lives in the adapter)
- **Constrained by:** none
- **Brief:** brief:adapter-hook-context-output-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Someone who installs `core` into a repository and starts Claude Code or Codex in a subdirectory still gets the `session-start` and `work-loop-check` hooks to run. Both hooks keep their current plain-text output.

## What Changes

- The command string of the two core hook-wiring sources — `packs/core/.apm/hook-wiring/session-start.toml` and `work-loop-check.toml`, which both run `python tools/hooks/<name>.py` relative to the working directory — resolves the repository root.
- The `claude-code` and `codex` hook projections (`packages/agentbundle/agentbundle/build/adapters/claude_code.py`, `codex.py`) write that root-stable form, if the open question below resolves to the adapter.
- The self-hosted `.codex/hooks.json` is regenerated, and the adapter tests that pin the old command string are updated.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable: the installed command changes | `packs/core` changelog entry and version bump | eugenelim | One entry naming both hooks | Entry present |
| Interface compatibility | Applicable: adopters' existing installs keep the old command until upgrade | the hook-wiring comment block in `session-start.toml`, which currently says root resolution is tracked as follow-on work | eugenelim | Comment names this spec | Comment updated |
| User promise | Not applicable | none | none | none | none |

## Agent Rules

### Always do

- Keep the hook body's output byte-identical on Claude Code and Codex.
- Quote the root path so a repository path with a space works.
- Run the projected command, not only the source string, in the tests.

### Ask first

- Any change to the Copilot, Cursor, Gemini CLI, or Kiro projections; they are another slice's scope.
- Any new dependency or helper executable.

### Never do

- Never use a form that needs a POSIX shell where the host runs commands without one, unless the Windows question below records that host as unsupported.
- Never fall back to the working directory when the root cannot be resolved; fail visibly.

## Testing Strategy

- **TDD** for the projected command string: a unit assertion per adapter on the exact text.
- **Goal-based** for behaviour: a test runs each projected command with the working directory set to a repository subdirectory and checks that the hook body runs and exits 0. This is hermetic; no host client is needed.
- A real Claude Code or Codex run is manual and non-blocking.

## Acceptance Criteria

- [ ] With the working directory at `docs/` inside a fixture repository, the projected `session-start` command for Claude Code runs the hook body and exits 0.
- [ ] The same holds for the projected `work-loop-check` command for Claude Code.
- [ ] The same holds for both commands as projected for Codex.
- [ ] With the working directory at the repository root, all four commands still run the hook body and exit 0.
- [ ] A fixture repository whose path contains a space passes the four checks above.
- [ ] `session-start` output on the Claude Code and Codex projections equals the output of the current command byte for byte.
- [ ] The Copilot, Cursor, Gemini CLI, and Kiro projections of both hooks equal their committed golden output.
- [ ] When the repository root cannot be resolved, the command exits non-zero with a message on stderr.

## Follow-ons

- eugenelim: [`adapter-hook-context-output-delivery`](../../product/briefs/adapter-hook-context-output-delivery.md) slices H2 and H3 — per-runtime context output and the Kiro v1 schema.

## Assumptions

- Technical: where the root token lives. Default: the adapter projection substitutes it, because Claude Code documents `${CLAUDE_PROJECT_DIR}` (hook adapter audit) and Codex guidance prefers git-root resolution, so one source string cannot serve both (settled by: eugenelim). If wrong: the source command string carries a shell snippet and the engine is untouched.
- Technical: the Codex root form and its Windows behaviour. Default: first task of the plan re-reads Codex's hook documentation and records the revision; until then the POSIX form is specified and a Windows limitation is stated in the guide (settled by: the documentation read).
- Defaulted: Engine-Change-RFC: the trailer names the RFC that governs hook projection, which the plan identifies from earlier hook-adapter commits (settled by: eugenelim).
