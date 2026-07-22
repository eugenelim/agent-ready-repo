# Spec: portfolio-first-run-pilot-architect

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Amendment #4 — cross-pack first-value overlay; `portfolio-pack-first-value-contract` spec — the `[pack.first-value]` fields it authored for the architect pack are the contract this spec verifies and closes
- **Brief:** none
- **Discovery:** none
- **Contract:** `packs/architect/pack.toml` `[pack.first-value]`
- **Shape:** documentation

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The architect pack's `[pack.first-value]` contract declares a no-terminal first-run path for a non-technical user (local/no-credential archetype, the simplest pilot risk profile). That contract is currently unproven: the `tutorial` field is absent, and no transcript confirms the `starter-prompt` produces the `expected-result`.

This spec closes that gap by authoring a first-session tutorial, running the path against a real codebase, and recording the transcript as evidence. The tutorial becomes the value pointed to by the `tutorial` field in the contract. Evidence from the run drives any skill changes needed; absent evidence, no changes are made.

The architect pilot establishes the baseline pattern (local, no credentials, non-technical) that the figma and governance-extras pilots extend.

## Boundaries

### Always do

- Author the tutorial at `docs/guides/architect/tutorials/architect-first-session.md`, using the contract fields (`starter-task`, `starter-prompt`, `expected-result`, `recovery`, `next-action`) from `packs/architect/pack.toml` `[pack.first-value]` as the authoritative source.
- Use the `starter-prompt` verbatim in the tutorial — no paraphrase, no `<placeholder>` tokens.
- Keep the tutorial terminal-free: no bash commands, no `git` invocations, no file-path strings the user must type, no prerequisite that conflicts with `prerequisites = []` in the contract.
- Record the transcript at `docs/specs/portfolio-first-run-pilot-architect/notes/transcript.md`. Record which skill actually fired and what it produced — not what was expected to happen. If the path does not complete, document the reproducible blocker with enough evidence for a second evaluator to reproduce it.
- Wire `tutorial = "docs/guides/architect/tutorials/architect-first-session.md"` in `packs/architect/pack.toml` `[pack.first-value]` once the tutorial file exists and the transcript confirms the path (or confirms a known-honest grading).
- Bump the architect pack version (patch — this change is catalogue-internal; the tutorial path and the `tutorial` field are not projected to adopter installs) and add a changelog entry when `pack.toml` changes.
- Also bump `packs/architect/.claude-plugin/plugin.json` version to match any `pack.toml` version change.
- Run `make build-self FORCE=1` after any `pack.toml` or skill edit.
- Run `python3 tools/lint-first-value-contract.py --root .` before declaring done.

### Ask first

- Any skill change not directly supported by transcript evidence. Surface the finding (what happened vs. what the contract claimed would happen) and the proposed fix before implementing.
- Any change to the contract fields (`starter-task`, `starter-prompt`, `expected-result`, `recovery`, `next-action`) in `pack.toml`. These were authored in the first-value-contract PR; changing them here requires confirmation.
- If the transcript shows the `starter-prompt` routes through `adapt-to-project` (core pack) rather than an architect pack skill: surface whether the tutorial should describe that route honestly, or whether the contract fields need correcting, before wiring the `tutorial` field.

### Never do

- Add terminal commands or file-path syntax the user must type to the tutorial.
- Make skill changes not grounded in transcript evidence — "only evidence-led skill changes."
- Add a new architect skill or new skill module boundary; evidence-led changes are edits to existing files only.
- Leave the `tutorial` field absent in the final PR — its absence is the gap this spec exists to close.
- Carry the `starter-prompt` verbatim in any authored/projected user-facing file other than the tutorial and `pack.toml`. Exception: the pilot transcript (`notes/transcript.md`) is an evidence record, not a user-facing artifact — it must record the exact input prompt observed (preserves the spirit of portfolio-pack-first-value-contract AC6 while satisfying AC5's transcript requirement).

## Testing Strategy

**Visual / manual QA (pilot run):** paste the `starter-prompt` into a Claude Code session in a repo with the architect pack installed, observe which skill fires and what it produces, and record the result. The transcript is the evidence record. If the agent does not produce the `expected-result`, that is a finding, not a silence. Equivalent method: trigger-analysis against installed skill descriptions (to determine which skill would fire) plus a subagent dispatched with only the starter-prompt and repo path (no pilot or work-loop context). The subagent is equivalent to a fresh user session: it has the same installed skills, the same codebase, and no prior context. This method was used for this pilot — Step 1 via trigger-analysis, Step 2 via subagent dispatch.

**Goal-based (lint and build):** `python3 tools/lint-first-value-contract.py --root .` exits 0; `make build-check` exits 0; `tutorial` path resolves on disk.

No TDD. The tutorial is prose; the pack.toml field update has no behavioral logic. Conditional skill changes are individually goal-based verified by re-running the path after each change.

Note on "plain language accessible to a non-technical user" (AC1d) and section coverage (AC1b): both are manual QA checks that run at the end of T1 (before the pilot transcript exists). Record the assessment in `docs/specs/portfolio-first-run-pilot-architect/notes/tutorial-review.md`. Heuristic for AC1d: no code blocks, no unexplained abbreviations, average sentence ≤ 20 words, no assumption the reader knows what a SKILL.md or design doc is.

## Acceptance Criteria

### AC1 — Tutorial authored

- [x] `docs/guides/architect/tutorials/architect-first-session.md` exists.
- [x] The tutorial covers, in order: (a) install verification — ask the agent a question and confirm it responds with architectural context, matching the contract's `verification` field; (b) the exact `starter-prompt` from the contract, presented as copy-ready text; (c) what the user will see, matching the `expected-result` field; (d) recovery, matching the `recovery` field; (e) next action, matching the `next-action` field.
- [x] The tutorial contains no bash commands, no `git` invocations, no file-path syntax the user must type manually, and no prerequisite that conflicts with `prerequisites = []` in the contract.
- [x] The tutorial is written in plain language accessible to a non-technical user.

### AC2 — Tutorial linked from README

- [x] `docs/guides/architect/README.md` has a link to `tutorials/architect-first-session.md` in its Tutorials section.

### AC3 — Tutorial field wired

- [x] `packs/architect/pack.toml` `[pack.first-value]` has `tutorial = "docs/guides/architect/tutorials/architect-first-session.md"`.
- [x] The architect pack version is bumped (patch) from `0.13.2` in `pack.toml`.
- [x] `packs/architect/.claude-plugin/plugin.json` version matches the bumped `pack.toml` version.
- [x] `docs/product/changelog.md` `[Unreleased]` has an entry for the tutorial addition.
- [x] `make build-self FORCE=1` exits 0 after the `pack.toml` edit.

### AC4 — Parity check passes

- [x] `python3 tools/lint-first-value-contract.py --root .` exits 0.
- [x] `make build-check` exits 0.

### AC5 — Transcript recorded

- [x] `docs/specs/portfolio-first-run-pilot-architect/notes/transcript.md` exists.
- [x] The transcript records: the session setup (packs installed, codebase used), the input prompt, which skill fired, what the agent produced, whether the `expected-result` was reached, and any deviation from contract.
- [x] If the path completed via an architect pack skill: the transcript shows the agent produced the expected architecture artifact, with a parity assessment against the `expected-result` field. (n/a — architect skill was not the observed route; AC met vacuously)
- [x] If the path completed via a non-architect skill (e.g., `adapt-to-project` from core): the transcript names which skill fired, confirms the `expected-result` was still produced, and notes the "ask first" finding for human review — the tutorial and contract fields may need updating to reflect the honest routing. (n/a — non-architect skill was not the observed route; AC met vacuously)
- [x] If the path completed via direct model reasoning (no skill fired): the transcript records which skills were checked, that none matched the prompt, and confirms the `expected-result` was still produced; the tutorial describes the no-skill path honestly. (observed route — see notes/transcript.md Finding 1)
- [x] If the path did not complete: the transcript names the reproducible blocker with enough detail for a second evaluator to reproduce it. The spec is not Shipped until either the path completes or the contract is updated to reflect an honest grading (e.g., `surfaces` narrowed, `expected-result` corrected). (n/a — path completed; AC met vacuously)

### AC6 — Evidence-led skill changes documented

- [x] `docs/specs/portfolio-first-run-pilot-architect/notes/skill-changes.md` exists.
- [x] If no skill changes were made: the file states "No skill changes — transcript confirmed the path works as specified."
- [x] If skill changes were made: the file states what changed, why (citing the specific transcript deviation), and confirms `make build-check` and `python3 tools/lint-skill-spec.py` passed after each change. (n/a — no skill changes were made; AC met vacuously)

## Assumptions

1. The architect pack is installed at `user` scope in the Claude Code session used for the pilot. A fresh `agentbundle install architect --scope user` is the expected pre-condition; `prerequisites = []` means no additional configuration is required.
2. The `starter-prompt` invokes a skill that produces `docs/architecture/reference.md` — the contract's `expected-result`. Pre-execution inspection suggests `adapt-to-project` (core pack) is the most likely trigger, since that is the only installed skill that creates `reference.md` and its trigger includes "propose reference architecture." The pilot observes which skill actually fires; the tutorial and contract are updated to match evidence if Assumption 2 is wrong.
3. Core pack is installed alongside architect in the pilot session (it is a default self-host pack and is typically installed). The `prerequisites = []` field in the contract may need updating if the pilot shows core is a practical prerequisite for the `expected-result`.
4. The pilot run uses a real codebase with settled architecture decisions (this repo, florence-v1, or equivalent) — the pilot needs a real codebase, not a toy one.
5. The existing `create-your-reference-architecture.md` tutorial covers a different path (`adapt-to-project` + arc42 template, route-by-route). The new tutorial is additive; no change to the existing tutorial is needed.
6. Architect pack version is `0.13.2` — confirmed 2026-07-22 from `packs/architect/pack.toml`.
7. The `tutorial` field value (`docs/guides/architect/tutorials/architect-first-session.md`) is a catalogue-internal path: it exists only in this repo and is resolved relative to the catalogue root by `lint-first-value-contract.py`. It is not projected to adopter installs (consistent with `[pack.first-value]` being catalogue-internal per portfolio-pack-first-value-contract Boundaries). This pilot sets the convention.

## Changelog

<!-- Add an entry under [Unreleased] in docs/product/changelog.md when this
     spec is implemented. Format: feature bullet, one line. -->
