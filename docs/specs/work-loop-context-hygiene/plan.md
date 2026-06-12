# Plan: work-loop-context-hygiene

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure prose/contract subtraction across four canonical source files (three
reviewer agents + the work-loop `SKILL.md`), then one
projection step. The riskiest part is *not* breaking the verification surfaces
while removing tokens — so each edit is additive-of-instruction /
subtractive-of-resident-tokens, never a change to a gate, a verb, or the
finding format the parser reads.

Order of operations: (T1) tighten the three reviewer agents' `### Output
format` — the agent-side change, smallest blast radius, and it's what makes the
orchestrator-side eviction worth doing; (T2) the orchestrator-side distillation
in the work-loop `SKILL.md` REVIEW section; (T3) the context-hygiene section in
the same `SKILL.md`. T3 depends on T2 because both edit `SKILL.md` — doing them
as one continuous pass on that file avoids a same-file conflict and keeps the
diff legible. Then (T4) `make build-self` + the full gate sweep as a single verification
task. All edits live under `packs/core/.apm/`; nothing under `.claude/` is
hand-edited.

The testing story is goal-based grep assertions for the prose changes, with
`tools/test-loop-cohort.sh` as the regression floor proving the finding format
the parser depends on is untouched.

## Constraints

- No ADR/RFC governs this change; skill-behavior edits ship via normal
  spec+PR. RFC-gating applies only to `docs/CONVENTIONS.md` / `docs/CHARTER.md`
  canonical wording (CLAUDE.md, project memory).
- The `risk-triggers` block in `SKILL.md` (~57-77) must stay byte-identical
  across the four canonical copies named in its `risk-triggers:start` comment
  — an acceptance criterion of the `work-loop-light-mode` spec. No task touches
  it.
- The reviewer finding format is a parser contract (`loop-cohort.py
  parse_findings`); tasks tighten *around* it, never *it*.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

**Integration tests:** `tools/test-loop-cohort.sh` (review-record parse,
fingerprint-canonical, rotation, clean, reject-unparseable) — the regression
floor that proves the finding format stayed parseable after T1. CI-only (not in
`make build-check`), so run it by hand.
**Manual verification:** none.

## Design (LLD)

### Design decisions

- **Anchor the orchestrator-side change in the REVIEW section, not the shared
  EXECUTE dispatch bullet.** `SKILL.md:331` ("Merge results in your own
  context") is shared by implementer *and* reviewer fan-out; editing it risks
  the implementer semantics. The eviction guidance lands in the REVIEW
  review-record paragraph (~428-445) and the reviewer fan-out paragraph
  (~466-470), which are reviewer-only. Traces to: AC1, AC2.
- **Eviction is safe because the record is externalized.** The instruction
  frames the on-disk report + `state.json` fingerprints as the durable record,
  mirroring the repo's existing externalized-memory model. Traces to: AC2.
- **Agent-agnostic, capability-based phrasing.** The skill projects to Cursor,
  Codex, Gemini CLI, Copilot, Kiro — so the section names no Claude-Code tool
  (no "Explore"); it uses the existing "where your agent supports delegated
  subagents" / "select a subagent matching …" template, and every lever has a
  **portable floor** that works with no subagent runtime (most adapters can't
  spawn one mid-session). Traces to: AC5, AC11.
- **Evidence-ranked order — reference-reads first.** Transcript analysis of a
  real adapter session showed whole-file reads were ~30% of the window and beat
  subagent/reviewer-report cost ~6:1, so reference-read reduction leads, then
  compaction, then narrowest-gate. Traces to: AC5.
- **Compaction lever is invariant-anchored, not command-enumerated.** Name
  `/compact` as the Claude Code instance, state the "because" (spec/plan/state/
  backlog are the externalized memory), and cross-reference the Unattended-loops
  section / "your agent's own facility" — rather than enumerating each adapter's
  command (a drift-prone matrix the repo deliberately avoids) or a bare hedge.
  Traces to: AC6.
- **Reduce, never lossily transform (guardrail).** A closing line forbids
  summarize-on-read / strip / RAG-chunk on the edit/review path: `Edit` needs
  exact-byte `old_string` and line numbers anchor findings, so lossy
  read-compaction fails silent. Skeleton maps are orientation-only. Traces to:
  AC11.
- **Keep the section inline and lean (≤ ~25 lines).** Three floored levers + a
  guardrail is tight enough to inline; if it bloats past that, detail moves to
  `references/`, consistent with the change's own goal. Traces to: AC5, AC10.

## Tasks

### T1: Reviewer agents return only the findings block — no methodology recap

**Depends on:** none

**Touches:** packs/core/.apm/agents/adversarial-reviewer.md, packs/core/.apm/agents/security-reviewer.md, packs/core/.apm/agents/quality-engineer.md

**Tests:**
- Goal-based: `grep` each of the three agent files for the new "only the
  findings block / no methodology recap, scope summary, or process narration"
  instruction in/adjacent to `### Output format` (verifies AC3).
- Goal-based: confirm the finding-format code block
  (`**N. <title>.** `path:line`. … Fix: …`) is byte-unchanged in all three
  files via diff against `origin/main` (verifies AC4, format half).
- Regression: `tools/test-loop-cohort.sh` stays green (verifies AC4, parser
  half).

**Approach:**
- In each agent's `### Output format` section, after the finding-format block,
  add/extend the closing instruction so it mandates returning *only* the
  findings block (or the Clean line) with no pre-findings methodology recap,
  scope summary, or process narration. (A "keep it distilled" phrasing may
  reference the small distilled-summary shape as descriptive guidance — it is
  not a checkable token bound and no AC asserts a number.)
- Bring `quality-engineer.md` up to parity with the "no praise padding" phrasing
  the other two already carry.
- Do not touch the finding-format code block itself.

**Done when:** the three greps match the new instruction, the finding-format
diff against `origin/main` is empty, and `tools/test-loop-cohort.sh` passes.

### T2: Orchestrator drops resident report text after `review record`

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:**
- Goal-based: `grep` the REVIEW section for the eviction instruction (drop the
  resident report after `review record`; re-read a finding from the on-disk
  report only when a FIX needs its detail) (verifies AC1).
- Goal-based: `grep` for the durable-record framing (on-disk report +
  `state.json` fingerprints; next pass regenerates findings) and confirm the
  reviewer fan-out paragraph no longer implies full-report retention across FIX
  (verifies AC2).

**Approach:**
- In the REVIEW review-record paragraph (~428-445), after the `review record`
  command, add a sentence: once findings are recorded, drop the full report
  text from resident context; when a FIX needs a finding's detail, re-read it
  from the on-disk report rather than holding the prose resident. State why
  it's safe: the on-disk report + fingerprints are the durable record and the
  next REVIEW pass regenerates the current findings.
- Adjust the reviewer fan-out paragraph (~466-470) so "group findings by
  severity yourself" is followed by evict-the-prose-keep-the-fingerprints,
  removing any implication the merged report stays resident across iterations.
- Leave the shared EXECUTE dispatch bullet (`:331`) structurally intact (it
  serves implementer fan-out too).

**Done when:** both greps match and a re-read of the REVIEW section confirms no
remaining instruction to hold the full report across FIX iterations.

### T3: Add the context-hygiene section to work-loop SKILL.md

**Depends on:** T2 (both edit `SKILL.md`; T3 follows T2 to avoid a same-file conflict)

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:**
- Goal-based: section exists and names exactly three levers in evidence-ranked
  order, each a "do this, because" with an explicit portable floor (verifies
  AC5).
- Goal-based: the compaction lever names `/compact` as the Claude instance,
  states the externalized-memory "because," and cross-references the
  Unattended-loops section / "your agent's own facility" (verifies AC6).
- Goal-based: the section is agent-agnostic (`grep -i "explore"` finds no
  tool-name reference) and carries the "reduce, never lossily transform"
  guardrail (verifies AC11).
- Goal-based: section is ≤ ~25 lines in `SKILL.md` (verifies AC10).

**Approach:**
- Add a concise `## Context hygiene` section adjacent to the Unattended-loops
  section it cross-references, without disturbing the `risk-triggers` block.
  One-line intro (power orthogonal to resident tokens; three levers, each with
  a no-subagent floor), then three evidence-ranked bullets:
  1. **Reference-reads (biggest lever):** reading an existing implementation
     just to mirror it is the largest single window draw — where the agent
     supports delegated subagents, hand it to a read-only one returning a
     distilled summary (the "select a subagent matching …" facility REVIEW
     uses). *Floor:* targeted line ranges, not whole files; never re-read a
     resident file.
  2. Compact at task boundaries with a "preserve plan, open findings,
     decisions" hint — safe because `spec.md` + `plan.md` + `state.json` +
     `backlog.md` are the externalized memory. `/compact` in Claude Code;
     elsewhere the agent's own facility / fresh-session mode (Unattended
     loops). *Floor:* re-read plan + open findings from disk, let the old
     transcript age out.
  3. During FIX, run the narrowest gate that covers the fix; the full GATES
     suite still runs before REVIEW/finish.
- Close with a one-paragraph **"reduce, never lossily transform" guardrail**:
  `Edit` needs exact-byte `old_string` and line numbers anchor findings, so
  lossy read-compaction fails silent; skeleton repo-maps are orientation-only.
- Keep agent-agnostic — no Claude-Code tool names except the labeled `/compact`
  instance.

**Done when:** the section renders three evidence-ranked levers (reference-reads
first) each with a floor, the compaction lever is invariant-anchored +
cross-referenced, the guardrail is present, no "Explore"-style tool name
appears, and the line count is within budget.

### T4: Project and verify — build-self + full gate sweep

**Depends on:** T1, T2, T3

**Touches:** .claude/skills/work-loop/SKILL.md, .claude/agents/*.md (generated),
docs/product/changelog.md (user-visible-change entry, per CONVENTIONS § Pull
requests + the changelog's own maintenance note)

**Tests:**
- Goal-based: `make build-self` exits 0; `git status` shows only the intended
  `packs/core/.apm/` edits and their projected `.claude/` counterparts, no
  unexpected reverts (verifies AC7).
- Goal-based: `lint-packs`, `tools/lint-agent-artifacts.py`, and
  `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` (scans all
  specs; reports `spec metadata clean`) pass (verifies AC8).
- Goal-based: grep-equality of the `risk-triggers` block across its four
  canonical copies holds; `git diff origin/main -- docs/CONVENTIONS.md
  docs/CHARTER.md` is empty (verifies AC9).
- Regression: `tools/test-loop-cohort.sh` and the `agentbundle` package pytest
  suite pass (catch any projection/drift fallout).

**Approach:**
- Run `make build-self`; inspect `git status` for reverts (per the
  build-self-undoes-projection-only-edits gotcha).
- Clear any stray `__pycache__` under `packs/` and `.claude/` before the drift
  check (per the pycache-breaks-build-check gotcha).
- Run the lint + test sweep listed above by hand.

**Done when:** projection is clean, all listed gates pass, and the
`risk-triggers` grep-equality + CONVENTIONS/CHARTER no-diff checks hold.

## Rollout

Pure prose/contract change to a shipped pack primitive. Delivery is the merge
itself; reversible by revert. No infrastructure, no external-system
integration. Deployment sequencing: source edits (T1-T3) before projection
(T4) — enforced by the `Depends on:` DAG.

## Risks

- **Projection drift / silent revert.** A prior PR that edited only a projected
  path could be reverted by `make build-self`; mitigated by the explicit
  `git status` inspection in T4.
- **Over-trimming the reviewer contract.** Tightening too aggressively could
  read as discouraging the *double-read* discipline the adversarial-reviewer
  mandates. Mitigation: the tightening targets pre-findings *narration* only;
  the methodology the reviewer *performs* is unchanged, only what it *prints*.
- **Section bloat.** The context-hygiene section could grow past budget;
  mitigation is the ≤ ~14-line cap with overflow to `references/` (AC10).

## Changelog

- 2026-06-11: initial plan.
