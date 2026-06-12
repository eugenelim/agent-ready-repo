# Spec: work-loop-context-hygiene

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none <!-- the work-loop skill + reviewer agents are prose/behavioral contracts, not a contracts/<type>/ surface -->
- **Shape:** mixed <!-- prose-contract change spanning one skill + three agents; LLD pruned to Design decisions only -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A work-loop session keeps the loop's *power* — gates, the adversarial
iterate-to-Clean loop, fingerprint stasis detection, the quality-engineer
floor, the iteration cap — while shedding the *resident noise* that fills the
context window without adding verification value. An investigation found that
more than half of work-loop sessions exceed 150k resident context, and that
the noise (verbose reviewer prose held across FIX iterations, repeated
full-suite gate output, in-thread file dumps during PLAN) is orthogonal to the
durable record (the on-disk reviewer report, `state.json` fingerprints,
`plan.md`, `backlog.md`). This change is **subtraction-shaped**: it removes
resident tokens, not rigor. For the agent running the loop, the win is a
window that stays clear enough to reason well deep into a multi-loop spec —
with every verification surface that exists today still gating the result.
The 150k figure is *motivation*, not an acceptance bar: this is a
prose-contract change, so success is the levers existing and the verification
surfaces provably intact, not a measured token delta (see Testing Strategy).

Three coordinated changes, all in `packs/core/.apm/` canonical source:

1. **Reviewer-output distillation (orchestrator side)** — after
   `loop-cohort review record` writes fingerprints to `state.json`, the
   orchestrator does *not* keep the full reviewer report text resident; it
   re-reads a finding from the on-disk report only when a FIX needs its
   detail. The on-disk report + `state.json` fingerprints are the durable
   record, and the next REVIEW pass regenerates the current findings — which
   is what makes eviction safe.
2. **Reviewer contract tightening (agent side)** — the three reviewer agents
   return *only* the findings block (or `Clean — ready to commit.`), with no
   pre-findings methodology recap, scope summary, or process narration. The
   finding format itself is untouched.
3. **A context-hygiene section** in the work-loop skill codifying three
   usage-pattern levers in evidence-ranked order (reference-read reduction,
   task-boundary compaction, narrowest-gate-during-FIX), each a "do this,
   because" carrying a **portable floor** that needs no subagent runtime, plus
   a "reduce, never lossily transform" guardrail. Agent-agnostic throughout —
   no Claude-Code-specific tool is named except `/compact` as a labeled
   instance with a portable alternative.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit only canonical source under `packs/core/.apm/`, then run
  `make build-self` to project; verify `git status` shows no unexpected
  reverts to projected paths.
- Preserve every verification surface exactly: gates, the adversarial
  iterate-to-Clean loop, fingerprint stasis detection, the quality-engineer
  floor, and the iteration cap.
- Run the `agentbundle` package pytest suite and `tools/test-loop-cohort.sh`
  by hand on any change that trips a drift/lint gate — `make build-check`
  does not run package tests.

### Ask first

- Any change that would require editing `docs/CONVENTIONS.md` or
  `docs/CHARTER.md` canonical wording — those are RFC-gated. Stop and surface
  it as a decision rather than proceeding.
- Any change to the reviewer finding format
  (`**N. <title>.** `file:line`. … Fix: …`) that
  `loop-cohort.py parse_findings` depends on.

### Never do

- Edit `.claude/` or `.agents/` projected paths directly — they are generated
  by `make build-self`.
- Disturb the byte-identical `risk-triggers:start … risk-triggers:end` block
  (work-loop `SKILL.md` ~lines 57-77); grep-equality across its four canonical
  copies is an acceptance criterion of the `work-loop-light-mode` spec.
- Weaken, gate, or remove any verification behavior — this PR removes resident
  tokens only.
- Introduce a new top-level directory, module boundary, or dependency; this is
  a prose/contract subtraction, code-free apart from tests.

## Testing Strategy

The change is prose + a behavioral contract, so verification is **goal-based**
plus an existing-test **regression** floor — no new product logic, so no TDD,
and no UI, so no manual QA. By design there is **no token-count acceptance
criterion**: the 150k motivation in the Objective is not a measured bar, and
adding a brittle token assertion would be theatre. Success is the levers
present and every verification surface provably intact.

- **Orchestrator distillation (AC1, AC2): goal-based.** `grep` the work-loop
  `SKILL.md` REVIEW guidance for the eviction instruction (drop the resident
  report after `review record`; re-read a finding from the on-disk report only
  when a FIX needs it) and confirm the durable-record framing (on-disk report +
  fingerprints, next pass regenerates findings) is present. Prose behavior
  isn't unit-testable; the load-bearing invariant it relies on is covered by
  the regression floor below.
- **Reviewer contract tightening (AC3): goal-based.** `grep` all three reviewer
  agent files for the "only the findings block / no methodology recap" wording.
- **Finding-format invariant (AC4): regression.** `tools/test-loop-cohort.sh`
  pins `parse_findings` against the canonical finding format; it must stay
  green, proving the tightening did not disturb the format the parser reads.
  The sample report in that test is already findings-only, and the parser
  ignores any non-`**`-prefixed line — so this is a guard, not a new test.
- **Context-hygiene section (AC5, AC6, AC11): goal-based.** Confirm the section
  exists, names exactly three levers in evidence-ranked order (reference-reads
  first) each with a "because" and a portable floor, anchors the compaction
  lever to the externalized-memory invariant + cross-references Unattended
  loops, stays agent-agnostic (no "Explore"-style tool name; `grep` confirms
  absence), and carries the "reduce, never lossily transform" guardrail.
- **Projection + drift (AC7, AC8): goal-based.** `make build-self` projects
  cleanly; `git status` shows only intended source + projected-counterpart
  changes; `lint-packs`, `tools/lint-agent-artifacts.py`, and
  `.claude/skills/work-loop/scripts/lint-spec-status.py` pass.
- **Leanness + grep-equality (AC9, AC10): goal-based.** The context-hygiene
  section is tight (≤ ~25 lines in `SKILL.md`, else detail moves to
  `references/`); the `risk-triggers` block is byte-identical across its four
  canonical copies; `CONVENTIONS.md` / `CHARTER.md` canonical wording is
  unchanged.

## Acceptance Criteria

- [x] **AC1.** Work-loop `SKILL.md` REVIEW guidance instructs the orchestrator
  to drop the full reviewer report text from resident context after
  `loop-cohort review record`, re-reading an individual finding from the
  on-disk report when a FIX needs its detail rather than holding the full
  prose resident across iterations.
- [x] **AC2.** That same guidance names the durable record explicitly — the
  on-disk report plus `state.json` fingerprints — as the reason eviction is
  safe (the next REVIEW pass regenerates the current findings); the reviewer
  fan-out paragraph no longer implies the merged report is retained across FIX
  iterations. No AC asserts a pre-filtered "OPEN findings" on-disk artifact —
  none exists; OPEN-vs-resolved is the orchestrator's DECIDE-phase routing
  judgment.
- [x] **AC3.** Each of `adversarial-reviewer.md`, `security-reviewer.md`, and
  `quality-engineer.md` instructs the reviewer to return *only* the findings
  block (or `Clean — ready to commit.`), with no pre-findings methodology
  recap, scope summary, or process narration.
- [x] **AC4.** The reviewer finding format
  (`**N. <title>.** `path:line`. … Fix: …`) is unchanged in all three agent
  files, and `tools/test-loop-cohort.sh` (review-record parse, fingerprint,
  rotation, clean, reject-unparseable cases) passes.
- [x] **AC5.** Work-loop `SKILL.md` carries a context-hygiene section
  codifying exactly three levers in evidence-ranked order, each a "do this,
  because" with an explicit **portable floor** (a fallback that works with no
  subagent runtime): (i) **reference-reads first** — when reading an existing
  implementation only to mirror it, delegate that read to a read-only subagent
  *where the agent supports it*; floor = read targeted line ranges, not whole
  files, and never re-read a file already resident; (ii) compact at task
  boundaries in multi-loop specs, with an explicit "preserve plan, open
  findings, decisions" hint; floor = re-read plan + open findings from disk and
  let the old transcript age out; (iii) while iterating in FIX, run the
  narrowest gate that covers the fix — the full GATES suite still runs before
  REVIEW/finish, so the mechanical floor is re-asserted and the surface is not
  weakened.
- [x] **AC6.** The compaction lever is anchored to the externalized-memory
  invariant (`spec.md` + `plan.md` + `state.json` + `backlog.md` are the
  durable memory), names `/compact` as the Claude Code instance, and
  cross-references the Unattended-loops section / "your agent's own facility"
  for harnesses without an interactive compaction command — not a bare "use the
  equivalent" hedge.
- [x] **AC11.** The section is **agent-agnostic** — it names no
  Claude-Code-specific tool (no "Explore" or similar), using the capability
  template ("where your agent supports delegated subagents", "select a subagent
  matching …") instead; `/compact` is the sole named instance and is paired
  with a portable alternative. It carries an explicit **"reduce, never lossily
  transform" guardrail**: hygiene reduces *what you load*, never
  summarize-on-read / strip / RAG-chunk the bytes on the edit/review path,
  because `Edit` needs exact-byte `old_string` matches and line numbers anchor
  reviewer findings — so lossy read-compaction fails silent. Skeleton repo-maps
  are explicitly allowed for orientation only.
- [x] **AC7.** `make build-self` projects cleanly: `git status` shows only the
  intended `packs/core/.apm/` source edits and their projected `.claude/`
  counterparts, with no unexpected reverts.
- [x] **AC8.** Mechanical gates pass: `lint-packs`,
  `tools/lint-agent-artifacts.py` (projection), and
  `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` (the
  projected, runnable copy; canonical source
  `packs/core/.apm/skills/work-loop/scripts/`; it scans all specs and must
  report `spec metadata clean` with this spec present).
- [x] **AC9.** The `risk-triggers:start … risk-triggers:end` block is
  byte-identical across the four canonical copies named in the work-loop
  `SKILL.md` `risk-triggers:start` comment (the source-of-truth list), and
  their projected counterparts (`docs/CONVENTIONS.md`, the `.claude/` /
  `.agents/` `SKILL.md`) are unchanged; `CONVENTIONS.md` / `CHARTER.md`
  canonical wording is unchanged.
- [x] **AC10.** The context-hygiene section stays lean (≤ ~25 lines in
  `SKILL.md`); any detail beyond that lands in `references/`, consistent with
  this change's own goal.

## Assumptions

- Technical: `loop-cohort review record` (`cmd_review_record`) reads the
  reviewer report from an orchestrator-written `--report` disk path and
  persists only fingerprints to `state.json` (`finding_fingerprints` /
  `previous_finding_fingerprints` — opaque sha1, no finding text); the disk
  report + fingerprints are the durable record, so evicting resident report
  text is safe (source: `scripts/loop-cohort.py` `cmd_review_record`,
  `parse_findings`; `assets/state.json`).
- Technical: the finding-parse regex (`FINDING_LINE_RE`) matches only lines
  starting with `**N. …**` + a backtick citation and ignores all other lines,
  so removing pre-findings methodology recap cannot break parsing
  (source: `loop-cohort.py` `FINDING_LINE_RE` / `parse_findings`;
  `tools/test-loop-cohort.sh` review-record sample report).
- Technical: all three reviewer agents already carry a `### Output format`
  block with the identical finding shape + a `Clean — ready to commit.` line;
  adversarial + security already say "no praise padding," quality-engineer does
  not (source: `adversarial-reviewer.md`, `security-reviewer.md`,
  `quality-engineer.md` `### Output format` sections).
- Technical: `make build-self` projects the core pack;
  `.claude/skills/work-loop/SKILL.md` and `.claude/agents/*.md` are generated
  targets (source: repo read + project memory).
- Process: changing a shipped skill's *behavior* is a structural / published-
  interface change → full mode + `new-spec` first; skill edits ship via normal
  spec+PR, not RFC (RFC-gating applies to `CONVENTIONS.md` / `CHARTER.md`)
  (source: user direction 2026-06-11; CLAUDE.md risk triggers).
- Process: the adapter-neutral equivalent of `/compact` is the
  externalized-memory / fresh-session-per-iteration pattern already documented
  in the work-loop Unattended-loops section; the repo has no per-adapter
  in-session capability matrix and the convention is behavior-anchored skills,
  so anchoring the lever to the invariant + cross-referencing that section is
  preferred over a bare hedge (source: repo research 2026-06-11,
  `SKILL.md:608-635`, `docs/contracts/adapter.toml`; user confirmation
  2026-06-11).
- Product: the audience is the agent running the work-loop; success is a
  clearer resident window deep into a multi-loop spec with zero loss of
  verification behavior (source: user direction 2026-06-11).
