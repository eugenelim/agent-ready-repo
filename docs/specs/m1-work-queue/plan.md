# Plan: m1-work-queue

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two prose insertions into a single SKILL.md source file, then a build-self +
lint run. No executable code. No new files beyond the updated source.

**T1** inserts a "step 0" orientation block near the top of the work-loop
SKILL.md — before the `### 1. PLAN` heading — describing how to read
`workspace.toml`, what to surface, and the silent no-op when the file is
absent.

**T2** extends the end-of-session checklist (the `DECIDE` section's terminal
bullet list) with the workspace.toml edit instruction and the roadmap reminder,
each guarded by the same absent-file condition.

**T3** regenerates projected artifacts (`make build-self`) and runs all lint
surfaces to confirm projection correctness, content presence, and clean gates.

**T4** is a manual QA pass: run work-loop against a repo that has
`workspace.toml` (with `[work].active` populated) and one without, verify the
orientation block appears in the first case, is absent in the second, and that
the ship-step edit instruction surfaces correctly.

The riskiest part is the insertion location for step 0 — it must sit before
PLAN but after any mode-selection or orientation preamble, so the agent has
context before it writes the inline spec. The ship-step addition must not
silently move content into the wrong list (the end-of-session checklist vs. the
FIX phase). Both are caught by the manual QA pass.

## Constraints

- **RFC-0064 Batch 3 AC** — the single governing AC: step 0 read, ship-step
  write (active → shipped), roadmap reminder, and graceful degradation when
  absent.
- **RFC-0064 D4** — `workspace.toml` lives on `main`; skills edit it in the
  working directory and stage it with the spec PR.
- **No executable code as the feature mechanism** — prose in SKILL.md only
  (mirrors the light-mode spec's vehicle constraint from ADR-0014; this spec
  follows the same pattern).
- **`make build-self` is the regeneration path** — never edit `.claude/`
  directly.

## Construction tests

Most construction tests live under the tasks below.

**Cross-cutting manual verification:**
- With `workspace.toml` present and `["ini-002".work].active = ["spec/m1-work-queue"]`:
  run work-loop, observe step 0 output contains "Platform Core", "M1 · Workspace
  Foundation", and "spec/m1-work-queue".
- With `workspace.toml` absent: run work-loop, observe no step 0 block appears
  and PLAN begins immediately.
- At the ship step with `workspace.toml` present: verify the agent is instructed
  to move the path from `active` to `shipped` and surface the roadmap reminder.
- At the ship step with `workspace.toml` absent: verify no workspace.toml
  instruction appears and the checklist completes normally.

## Tasks

### T1: Insert step 0 workspace-read section into work-loop SKILL.md source

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`

**Tests:**
- Goal-based: `grep -c "step 0\|Workspace context\|workspace.toml" packs/core/.apm/skills/work-loop/SKILL.md` returns non-zero for each term (verifies AC 1)
- Goal-based: `grep -c "absent\|no.*error\|no-op" packs/core/.apm/skills/work-loop/SKILL.md` returns non-zero (verifies AC 2)
- Goal-based: the heading for `### 1. PLAN` still appears immediately after the new step 0 block — `grep -n "### 1. PLAN\|step 0" packs/core/.apm/skills/work-loop/SKILL.md` shows step 0 block lines precede the PLAN heading line (verifies AC 7 — existing structure unchanged)

**Approach:**
- Open `packs/core/.apm/skills/work-loop/SKILL.md`.
- Locate the line that introduces `### 1. PLAN — think before acting` (currently the first numbered step heading).
- Insert a new unnumbered section **immediately before** that heading with a title such as
  `### Step 0. Orientation — read workspace context` (or `### 0. Orientation`).
- The section body describes:
  1. Read `workspace.toml` from the working directory if present.
  2. Surface the active initiative name (`[<slug>].name`), milestone
     (`[<slug>].milestone`), and spec path from `[<slug>.work].active`
     (if non-empty) in a clearly labelled block.
  3. If `[<slug>.work].active` is empty, surface name and milestone only —
     no error.
  4. If `workspace.toml` is absent, skip this step entirely — PLAN begins
     immediately with no error, no diagnostic.
- Do not renumber the existing steps (they remain `### 1. PLAN`, `### 2.
  EXECUTE`, etc.).

**Done when:** The new section appears in the source before the PLAN heading;
the three grep checks above return non-zero; the file still parses cleanly
(no broken Markdown headings or tables).

---

### T2: Extend ship-step checklist with workspace.toml write + roadmap reminder

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`

**Tests:**
- Goal-based: `grep -c "active.*shipped\|shipped.*active\|\[work\]" packs/core/.apm/skills/work-loop/SKILL.md` returns non-zero (verifies AC 4)
- Goal-based: `grep -c "roadmap.md" packs/core/.apm/skills/work-loop/SKILL.md` returns non-zero (verifies AC 5)
- Goal-based: the absent-file guard appears within the same section as the workspace.toml edit instruction (verifies AC 6) — `grep -n "workspace.toml\|absent\|roadmap" packs/core/.apm/skills/work-loop/SKILL.md` shows the three terms clustered in the same 20-line region

**Approach:**
- Locate the end-of-session checklist bullet list inside `### 5. DECIDE — fix
  or finish` (the `Gates green and review clean → ready to ship` checklist).
- Append two new bullet points at the end of the checklist, **before** the
  Conventional commit format bullet, so they are part of the "refuse to
  declare done until every line is true" block:
  1. If `workspace.toml` is present and `[<slug>.work].active` contains the
     current spec path, edit `workspace.toml` in the working directory: move
     that path to `[<slug>.work].shipped` and stage the file as part of the
     shipping PR diff. If absent, skip.
  2. Surface a one-line reminder to update `docs/product/roadmap.md`.
- Ensure the light-mode parenthetical note (if present alongside the
  checklist) still holds — the workspace.toml bullet applies in both modes
  since the file's presence governs the behavior, not the loop mode.

**Done when:** Both new bullets appear in the end-of-session checklist; the
three grep checks above return non-zero; the existing checklist items are
unaltered (confirmed by re-reading the surrounding lines after the edit).

---

### T3: Regenerate projected artifacts and pass all gates

**Depends on:** T2

**Touches:** `.claude/skills/work-loop/SKILL.md`

**Tests:**
- Goal-based: `diff packs/core/.apm/skills/work-loop/SKILL.md .claude/skills/work-loop/SKILL.md` returns no output (verifies AC 8)
- Goal-based: `make build-check` exits 0 (verifies AC 9)
- Goal-based: `python tools/lint-agent-artifacts.py` exits 0 (verifies AC 9)
- Goal-based: `python tools/lint-agents-md.py` exits 0 (verifies AC 9)

**Approach:**
- Run `make build-self` from the repo root.
- Confirm the projected copy at `.claude/skills/work-loop/SKILL.md` now
  matches the source (`diff` returns no output).
- Run `make build-check` and confirm exit 0.
- Run `python tools/lint-agent-artifacts.py` and confirm exit 0.
- Run `python tools/lint-agents-md.py` and confirm exit 0.
- If any gate fails, fix the source and re-run build-self before
  proceeding to T4.

**Done when:** `diff` between source and projected copy is empty; all three
lint commands exit 0.

---

### T4: Manual QA — exercise skill with and without workspace.toml

**Depends on:** T3

**Touches:** none (read-only exercise of the built artifact)

**Tests:**
- Manual QA: run work-loop with `workspace.toml` present (containing
  `["ini-002".work].active = ["spec/m1-work-queue"]`) — observe orientation
  block surfaces "Platform Core", "M1 · Workspace Foundation",
  "spec/m1-work-queue" before PLAN (verifies AC 1)
- Manual QA: run work-loop with `workspace.toml` absent — observe no step 0
  block appears and PLAN begins immediately (verifies AC 2)
- Manual QA: run work-loop with `workspace.toml` present but `[work].active
  = []` — observe name and milestone only, no error (verifies AC 3)
- Manual QA: at ship step with `workspace.toml` present — observe the agent
  is instructed to move the spec path from `active` to `shipped` and to
  surface the roadmap.md reminder (verifies ACs 4 and 5)
- Manual QA: at ship step with `workspace.toml` absent — observe no
  workspace.toml instruction and normal checklist completion (verifies AC 6)

**Approach:**
- Exercise the `.claude/skills/work-loop/SKILL.md` skill end-to-end through
  each scenario listed in Tests above.
- Record the actual stdout / observed output for each scenario — assert on
  what was observed, not on internal state.
- Confirm no regression in existing step headings or anti-pattern list.

**Done when:** All five manual QA observations match the expected outcomes
above; the observed output is recorded in the PR description.

## Rollout

Pure prose change in a projected skill file. Ships as one PR. No infrastructure
dependency. Reversible — revert the source edit and re-run build-self. The only
irreversible side-effect is `workspace.toml` edits the skill instructs the agent
to make at ship time, but those are agent-triggered, not auto-run by the skill
file itself.

## Risks

- **Insertion at wrong location.** If step 0 lands inside the loop diagram
  ASCII art or inside a reference-section block, it will confuse agents reading
  the skill. Mitigated by T4 manual QA — verify PLAN is the first numbered
  step and step 0 precedes it cleanly.
- **Ship-step bullet added to FIX phase instead of DECIDE.** The DECIDE section
  has two distinct bullet lists (the routing list and the end-of-session
  checklist); adding to the wrong list changes semantics. Mitigated by T2's
  grep cluster check and T4 manual QA.
- **build-self silently fails for a non-work-loop file.** `make build-self`
  regenerates all projected artifacts; a failure in an unrelated pack could
  mask a successful work-loop update. Mitigated by the `diff` check in T3 that
  directly confirms the two work-loop files agree.

## Changelog

- 2026-07-18: initial plan
