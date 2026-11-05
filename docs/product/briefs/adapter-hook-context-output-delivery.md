# Brief: a projected session-start hook starts from any directory and delivers its context

- **Slug:** `adapter-hook-context-output-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`adapter-hook-context-output`](../intents/adapter-hook-context-output.md) and the [hook adapter audit](../../specs/codex-hook-adaptation-handoff/hook-adapter-audit.md)
- **Parent intent:** intent:adapter-hook-context-output

## Outcome

After a repository install, the core hooks (`session-start` and `work-loop-check`) start from any directory below the repository root on Claude Code and Codex. The session-start nudge reaches Copilot, Cursor, and Gemini CLI through their documented output protocol. Claude Code and Codex keep plain stdout. Kiro receives the migrated v1 hook format; its nudge delivery is not claimed, and the installer's `Next:` action is the fallback.

## Success metrics

- Both repository hook commands (`.codex/hooks.json` runs `python tools/hooks/session-start.py` and `python tools/hooks/work-loop-check.py`, each relative to the working directory) resolve the repository root, so they run from a subdirectory.
- Copilot, Cursor, and Gemini CLI projections emit the JSON shape those clients read; Claude Code and Codex output is byte-identical to today's.
- Kiro IDE and CLI projections use the standalone v1 hook schema.

## Scope / Non-goals

In scope: root-stable commands, per-runtime context output, and the Kiro v1 migration, as the intent's Boundary lists.

Out of scope: the installer `Next:` handoff, the portable hook body's intent, the APM and Claude plugin routes, and non-hook adapter behaviour.

## Constraints / Appetite

Three slices, independent of each other. H3 goes last by preference because its change is widest, not because it waits on H1 or H2. The command-safety guardrail applies to every one, including a Windows-safe form of the root token.

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| H1 | Root-stable commands for both core hooks, `session-start` and `work-loop-check`, on Claude Code and Codex (`${CLAUDE_PROJECT_DIR}` or a git-root wrapper) | `hook-wiring/session-start.toml`, `hook-wiring/work-loop-check.toml`, `.codex/hooks.json` projection | Run the projected command from a subdirectory in a test; Windows-form unit test | None |
| H2 | Per-runtime context output for Copilot, Cursor, and Gemini CLI. First task: re-read each client's current hook-output documentation (last read 2026-08-22) and record the revision. | adapter projections and wrapper | Fixture per adapter parses as the documented JSON; Claude Code and Codex output unchanged | None |
| H3 | Kiro IDE and CLI hook projection on the standalone `.kiro/hooks/*.json` v1 schema. The only Kiro-specific hook today is `work-loop-check.kiro.hook`; core ships no Kiro session-start hook, so H3 migrates that one. | `kiro-ide-hooks` and the Kiro adapters | Schema fixtures; the superseded format is no longer emitted; installed-file ownership still tracked | None |

## Assumptions / Risks

- **Riskiest assumption:** Kiro documents no context channel for hook output. If that holds, the nudge on Kiro is stated as unverified and the installer's `Next:` action stays the fallback. If Kiro does document a channel, a follow-up intent adds it, since H3 migrates only the hook schema.
- Kiro IDE 1.x and CLI 3.x remain the target contract.

## Ready gaps (Draft only)

None.

## Rabbit holes

- Do not change the hook's meaning to fit one client's format.

## Manual residue (named, non-blocking)

- A real run of each client confirming the nudge appears. It raises a claim above `documentation-verified` and blocks nothing.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

Folds [`kiro-hook-schema-v1`](../intents/kiro-hook-schema-v1.md) and [`root-stable-hook-dispatch`](../intents/root-stable-hook-dispatch.md) into this one.
