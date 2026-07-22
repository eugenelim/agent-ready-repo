# Plan: portfolio-first-run-pilot-architect

- **Status:** Done
**Mode:** full (risk trigger: potential structural change to architect pack skills based on pilot evidence; `tutorial` field addition touches the pack's public-facing first-value contract)

## Assumption trio

- **Files touched:** `docs/guides/architect/tutorials/architect-first-session.md` (new), `packs/architect/pack.toml` (`tutorial` field + version bump), `docs/guides/architect/README.md` (link), `docs/product/changelog.md` (entry), `notes/transcript.md` (new), `notes/skill-changes.md` (new); conditionally `packs/architect/.apm/skills/architect-design/SKILL.md` if transcript reveals a skill gap.
- **Tests that prove done:** `lint-first-value-contract.py --root .` exits 0; `make build-check` exits 0; transcript file exists with observed result recorded.
- **Not changing:** first-value contract fields in `pack.toml` (unless transcript proves them wrong); existing `create-your-reference-architecture.md` tutorial; any other pack's files.

## Declined patterns

- Tempted to update the existing `create-your-reference-architecture.md` to be terminal-free — declining; it covers the `adapt-to-project` route and serves a different audience goal. A separate spec if needed.
- Tempted to add a multi-surface QA matrix (multiple adapters, multiple repo types) — declining; the pilot is one representative run establishing the path works; the `surfaces = ["claude-code"]` declaration already scopes it.
- Tempted to add a `skill-changes.md` only if changes happen — declining; always creating it (even to say "none") keeps the AC checkable mechanically.

## Resolve-vs-surface disposition record

- **Transcript might show the path doesn't work** → resolve-with-referent: the "ask first" boundary plus AC5 handle this; the spec allows an honest "Limited" grading with a documented blocker. No surface needed.
- **Skill changes** → conditional on transcript; the "ask first" boundary guards this. No surface needed at spec time.
- **Contract field corrections** → "ask first" boundary guards this. No surface needed at spec time.

## Tasks

### T1 — Author the pilot tutorial

**Depends on:** none (can be drafted from contract fields without running the path)  
**Verification:** mixed (goal-based for file existence and no-terminal check; manual QA for section-coverage against AC1b and plain-language heuristic against AC1d — record the manual check in `notes/tutorial-review.md`)

**Tests:**
- `ls docs/guides/architect/tutorials/architect-first-session.md` exits 0
- `! grep -Eq '^\s*```bash|^\s*\$ |\bgit ' docs/guides/architect/tutorials/architect-first-session.md` exits 0 (no bash blocks, shell prompts, or git commands)
- `grep "Describe the architecture of this codebase and create a reference.md snapshot so I can guide future design decisions." docs/guides/architect/tutorials/architect-first-session.md` exits 0 (full verbatim starter-prompt present)

**Approach:**
1. Read `packs/architect/pack.toml` `[pack.first-value]` fields: `verification`, `starter-prompt`, `expected-result`, `recovery`, `next-action`.
2. Author `docs/guides/architect/tutorials/architect-first-session.md` with five sections in order: install verification, starter prompt, expected result, recovery, next action.
3. Write in plain language; no terminal commands; the `starter-prompt` field is quoted verbatim as copy-ready text.
4. Follow the `docs/guides/` soft-wrap rule: one logical line per paragraph, blank line between paragraphs.
5. After authoring, record a manual coverage check in `notes/tutorial-review.md` (created here, before the transcript exists) covering three AC criteria: (a) **AC1b** — confirm each of the five sections maps to its contract field (verification / starter-prompt / expected-result / recovery / next-action); (b) **AC1c** — confirm no file-path syntax the user must type (note: `reference.md` or `docs/architecture/reference.md` may appear as *output* in the tutorial; that's fine — the check is whether the user is asked to type a path); (c) **AC1d** — score against the plain-language heuristic (no code blocks, no unexplained abbreviations, average sentence ≤ 20 words).

---

### T2 — Run the pilot path and record the transcript

**Depends on:** T1 (tutorial exists as the structured walkthrough to follow)  
**Verification:** visual/manual QA (transcript records which skill fired and what the agent actually produced)

**Tests:**
- `docs/specs/portfolio-first-run-pilot-architect/notes/transcript.md` exists
- The transcript names the codebase used, the input prompt, which skill fired, and the agent's output
- If path completed: transcript records parity assessment against the `expected-result` field
- If path did not complete: transcript names a reproducible blocker

**Approach:**
1. Note the codebase context (this repo: agent-ready-repo / florence-v1).
2. Confirm the architect pack is installed at user scope: run `agentbundle list-installed --scope user` and confirm `architect` appears in the output (user-scope installs land in `~/.claude/`, not `.claude/` in the repo). Note which other skills are also installed.
3. Run the `starter-prompt` verbatim; observe which skill fires (check skill trigger matches); record the output.
4. Compare the output to the `expected-result` field.
5. Record the full exchange at `notes/transcript.md` using the template in the Design (LLD) section below.
6. If the path routes through a non-architect skill (e.g., `adapt-to-project`): note it as an "ask first" finding; do not silently proceed to wire the `tutorial` field without surfacing the routing.
7. If any skill behavior deviates from what the contract claims: note the specific deviation (do not silently reconcile).
8. If T2 shows the path routes differently or produces a different artifact than the tutorial describes: revise the tutorial to match the honest routing before proceeding to T3 (wiring). The tutorial must describe what actually happens, not what the contract predicted would happen.

---

### T3 — Wire the tutorial field and bump the pack version

**Depends on:** T1 (file must exist), T2 (transcript shows path works or honest grading established); **precondition:** if T2 triggered the ask-first finding (path routed through a non-architect skill), human confirmation of the honest-routing description must be obtained before this task proceeds — do not wire the `tutorial` field until the routing question is resolved  
**Verification:** goal-based

**Tests:**
- `grep 'tutorial.*architect-first-session' packs/architect/pack.toml` exits 0
- `grep '"version": "0.13.3"' packs/architect/.claude-plugin/plugin.json` exits 0
- `grep 'version = "0.13.3"' packs/architect/pack.toml` exits 0
- `make build-self FORCE=1` exits 0

**Approach:**
1. Edit `packs/architect/pack.toml` `[pack.first-value]`: add `tutorial = "docs/guides/architect/tutorials/architect-first-session.md"`.
2. Bump `[pack]` `version` from `0.13.2` to `0.13.3`.
3. Edit `packs/architect/.claude-plugin/plugin.json` to bump `"version"` from its current value to `"0.13.3"`.
4. Run `make build-self FORCE=1`.
5. Confirm `git status` shows the pack.toml and plugin.json changes survived build-self.

---

### T4 — Update architect README

**Depends on:** T1  
**Verification:** goal-based

**Tests:**
- `grep 'architect-first-session' docs/guides/architect/README.md` exits 0

**Approach:**
1. Edit `docs/guides/architect/README.md` Tutorials section: add a link to `tutorials/architect-first-session.md` with a one-line description ("Start here — the guided first session from install verification to your first architecture artifact.").
2. Check if README is projected (it's under `docs/guides/architect/README.md` — an AGENTS.local.md Manual path). Edit it directly; no build-self needed for README files under docs/guides/.

---

### T5 — Add changelog entry

**Depends on:** T3  
**Verification:** goal-based

**Tests:**
- `awk '/^## \[Unreleased\]/{f=1;next} /^## /{f=0} f && /(architect.*tutorial|tutorial.*architect)/{print; exit}' docs/product/changelog.md` produces output (entry is in the `## [Unreleased]` block)

**Approach:**
1. Add an entry under `## [Unreleased]` → `### Added` in `docs/product/changelog.md`, following the bold-lead Keep-a-Changelog format used by surrounding entries: `- **`architect-first-session.md` first-session tutorial (architect pack 0.13.3).** First-value guided tutorial for the no-terminal architecture path; wires the `tutorial` pointer in the pack's first-value contract.`

---

### T6 — Parity check

**Depends on:** T1, T3, T4, T5  
**Verification:** goal-based

**Tests:**
- `python3 tools/lint-first-value-contract.py --root .` exits 0
- `make build-check` exits 0

**Approach:**
1. Run `python3 tools/lint-first-value-contract.py --root .`.
2. If it exits non-zero, read the error and fix the root cause (missing field, bad path, etc.).
3. Run `make build-check`.
4. If it exits non-zero, follow the error message to the seed or source file and fix there.

---

### T7 — Document evidence-led skill changes (conditional)

**Depends on:** T2  
**Verification:** goal-based

**Tests:**
- `docs/specs/portfolio-first-run-pilot-architect/notes/skill-changes.md` exists
- If changes were made: `make build-check` and `python3 tools/lint-skill-spec.py` both exit 0

**Approach:**
1. Always create `notes/skill-changes.md`.
2. If T2 revealed no deviations: write "No skill changes — transcript confirmed the path works as specified."
3. If T2 revealed a deviation in an architect pack skill: surface to human first (per "ask first" boundary). On confirmation, apply the minimum targeted change to the skill source file under `packs/architect/.apm/skills/`. Edit the seed, run `make build-self FORCE=1`, then `python3 tools/lint-skill-spec.py`, then `make build-check`. Record what changed, why, and the gate results in `notes/skill-changes.md`.
4. If T2 revealed a gap in a non-architect skill (e.g., `adapt-to-project` in core): surface as an "ask first" finding and note in `notes/skill-changes.md` that the gap is deferred to a follow-up spec. Do not edit any file outside `packs/architect/` — that is out of scope for this pilot. Record the specific finding (skill, observed behavior, deviation from contract) so the follow-up spec can pick it up.

---

## Design (LLD)

### Tutorial structure

The tutorial is a single document at `docs/guides/architect/tutorials/architect-first-session.md`. It is a **tutorial** (learning by doing) in Diátaxis terms — not a how-to (which assumes task confidence) and not a reference.

Section order maps to the contract fields:

| Section | Content source |
|---|---|
| Intro (≤2 sentences) | The outcome: "By the end you'll have asked the agent to describe your codebase's architecture and have seen it produce a summary." |
| Step 1 — Verify the pack is working | `verification` field from `pack.toml` |
| Step 2 — Ask your first architecture question | `starter-prompt` field, verbatim, as copy-ready text |
| Step 3 — What you'll see | `expected-result` field |
| If it doesn't work | `recovery` field |
| What to do next | `next-action` field |

The tutorial has **no prerequisites section** (the contract says `prerequisites = []`; nothing to state). It assumes the pack is installed (the install path lives in `docs/guides/_shared/`; the tutorial need only say "with the architect pack installed").

### Pack.toml edit

Only two lines change in `[pack.first-value]`:
- Add: `tutorial = "docs/guides/architect/tutorials/architect-first-session.md"`

And in `[pack]`:
- Change: `version = "0.13.2"` → `version = "0.13.3"`

The `.claude-plugin/plugin.json` version field must match.

### Transcript format

```markdown
# Architect pilot transcript

**Date:** YYYY-MM-DD
**Pack version:** architect 0.13.3
**Surface:** claude-code
**Codebase:** <repo name + brief description>

## Setup

<confirm architect pack is installed; how installed>

## Step 1 — Verification

**Prompt:** <verification prompt>
**Response:** <summary of agent response; did it confirm architectural context?>
**Result:** ✓ pass | ✗ fail — <why>

## Step 2 — Starter prompt

**Prompt:** Describe the architecture of this codebase and create a reference.md snapshot so I can guide future design decisions.
**Response:** <summary of what the agent produced; file path if created>
**Result:** ✓ matches expected-result | ✗ deviation — <description>

## Parity assessment

**expected-result contract says:** "A docs/architecture/reference.md file with the codebase's key components and structural decisions described in plain language."
**Observed:** <what was actually produced>
**Assessment:** ✓ matches | ✗ deviates — <what's different>

## Findings

<list any skill behavior deviations; "none" if clean>
```
