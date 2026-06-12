# Plan: adapter-support-accuracy

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

<!-- Mode: light. Lean fill: Approach + Tasks. Constraints/Risks/Design(LLD)
omitted — a prose-only doc-accuracy fix has no LLD and no implementation risk
beyond getting a claim wrong, which the per-task goal-based checks cover. -->

## Approach

Pure documentation edits. The shape: verify each claim against the oracle, then
rewrite the prose. The oracle is `docs/contracts/adapter.toml` for the projection
facts (Kiro/Codex/Copilot primitive modes and targets) and the **live**
github/copilot-cli changelog + issues for the one empirical runtime claim (Copilot
repo-scope hooks) — the doc page recorded that as a runtime finding, so it must be
re-checked against upstream, not trusted. Riskiest part: the Copilot repo-hook
reframe (FIX 6), where the doc said "regressed" but the changelog shows trust/opt-in
gating; that task gates on the web re-verification (T4) and must not over-claim. The
testing story is goal-based throughout — each task's claim is checkable by reading
it against the contract / changelog, and the repo doc lints (`pre-pr-catalogue.py`,
`lint-spec-status.py`) bound the whole change.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.
**Manual verification:** the web re-verification of copilot-cli state (T4) — the
changelog versions and issue states are recorded in `spec.md` Assumptions and
`docs/backlog.md` so the finding is durable, not chat-only.

## Tasks

### T1: Kiro IDE hook claim reflects the contract's three-way split

**Depends on:** none
**Touches:** docs/guides/reference/adapter-support.md

**Tests:**
- Goal-based (AC1): the Kiro IDE Hook cell + caveat name all three — bodies project,
  `.kiro.hook` events project, agent-embedded wiring drops — and match `adapter.toml`
  `[adapter.kiro-ide]` (`grep -A2 'adapter.kiro-ide.projections.kiro-ide-hook'`).
- Goal-based (AC2): Tier remains `Partial` with the one-line justification present.

**Approach:**
- Rewrite the matrix Kiro IDE Hook cell to `bodies + .kiro.hook events; embedded wiring dropped`.
- Rewrite the "Kiro IDE — hook-wiring is dropped" caveat to the three-way split,
  citing RFC-0022 E2 (dropped `hooks` key) and the Q6 probe (kiro-ide-hook active).

**Done when:** the cell and caveat agree with the contract and each other; AC1+AC2 hold.

### T2: Kiro slash-command wording + universal-layer note

**Depends on:** none
**Touches:** docs/guides/reference/adapter-support.md

**Tests:**
- Goal-based (AC3): the slash caveat says "no standalone command-file primitive the
  catalogue projects" (not "no slash-command surface") and names the manual-trigger
  hook / `inclusion: manual` route; matches `command = dropped` for kiro adapters.
- Goal-based (AC4): the page states both Kiro targets read `AGENTS.md` via steering.

**Approach:**
- Reword the Kiro clause in the shared slash-command caveat.
- Fold the universal-layer half-line into the Kiro IDE caveat (covers CLI + IDE).

**Done when:** AC3 + AC4 hold.

### T3: Codex + Copilot slash-command clauses point at skills

**Depends on:** none
**Touches:** docs/guides/reference/adapter-support.md

**Tests:**
- Goal-based (AC5): Codex clause names skills (`.agents/skills/`) as the replacement;
  matches `adapter.toml` codex `skill` target.
- Goal-based (AC6): Copilot clause frames the drop as won't-fix-by-design
  (copilot-cli#618/#1113) with skills (`.github/instructions/`) as the replacement;
  matches `adapter.toml` copilot `command = dropped` + `skill` target.

**Approach:**
- Rewrite the shared slash-command caveat's Codex + Copilot clauses; clarify that
  what drops is the slash-invocation surface, not reusable prompt content.

**Done when:** AC5 + AC6 hold.

### T4: Copilot repo-scope hook caveat reframed against live upstream

**Depends on:** none

**Tests:**
- Manual (precondition): re-verify copilot-cli changelog + issues — latest version,
  repo `.github/hooks/` loading gating, issue states (#1503, #2540, #2076). Record
  in `spec.md` Assumptions.
- Goal-based (AC7): the caveat + matrix Hook cell say trust/prompt-mode-gated (cite
  changelog 1.0.8/1.0.41/1.0.51), cite open #1503, re-stamp 1.0.61, keep user-scope
  fires, and do not assert repo hooks definitely fire on 1.0.61.

**Approach:**
- Run the web re-verification first; only then rewrite the caveat + matrix cell.
- Drop closed #2076; confine plugin-scope #2540 to the backlog (T5).

**Done when:** AC7 holds and the framing matches the verified upstream state.

### T5: Blast radius corrected without falsifying history

**Depends on:** T4
**Touches:** docs/specs/copilot-full-parity/spec.md, docs/backlog.md

**Tests:**
- Goal-based (AC8): the `copilot-full-parity` T4 conclusion is reframed while the
  dated 1.0.60 observation (`spec.md` lines around the AC23/T4 record) is unchanged;
  the backlog follow-on records the 1.0.61 re-verification + #1503.
- Goal-based (AC9): `grep` of RFC-0022/ADR-0012 + RFC-0024/ADR-0013 shows none carry
  the corrected claims → no `§ Errata` added.

**Approach:**
- Edit only the forward-looking conclusion in the copilot spec's T4 paragraph.
- Update the backlog copilot-full-parity follow-on with the re-verification.
- Confirm frozen governance is clean (grep); record the finding in `spec.md` AC9.

**Done when:** AC8 + AC9 hold.

### T6: Bundled cell fix + gates green

**Depends on:** T1-T5

**Tests:**
- Goal-based (AC12): the Kiro CLI Hook cell reads `body + wiring`, matching
  `adapter.toml` `[adapter.kiro-cli.projections.hook-wiring]`.
- Goal-based (AC10): the Copilot Skill cell, Subagent cell, and no-web-tool caveat
  are byte-unchanged in the diff (ownership boundary held).
- Goal-based (AC11): `tools/pre-pr-catalogue.py` exits 0; `lint-spec-status.py`
  exits 0; no pycache drift; `git status` clean except intended files.

**Approach:**
- Bundled ride-along (same file/concern, surfaced by T1's caveat; AC12): Kiro CLI
  Hook cell `body` → `body + wiring` (kiro-cli retains `hook-wiring` per contract).
- Run the gates; address adversarial-reviewer findings.

**Done when:** AC10 + AC11 + AC12 hold; adversarial-reviewer returns no Blockers.

## Changelog

- 2026-06-11: initial plan, authored alongside the shipped implementation to make
  the PR self-documenting. Plan reflects the as-built work (Status: Done); tasks
  trace 1:1 to the spec's acceptance criteria.
