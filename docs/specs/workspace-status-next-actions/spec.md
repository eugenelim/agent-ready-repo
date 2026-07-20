# Spec: workspace-status-next-actions

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (workspace.toml schema — queue resolution DAG drives choice derivation); `spec/spec-A-workspace-status-rename` (Shipped — dependency satisfied)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — skill prose modification; no API contract.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When workspace-status completes its orient output, it closes with a `### 6. Next-actions` section. The section is scannable: numbered choices, one line each, activation command inline. Choices are derived from the DAG already resolved in Step 2 — no re-parsing of `workspace.toml`. The section always has a minimum of one choice ("start new work"); it expands with up to four choices when queue state provides them, plus a parallel-session offer when ≥2 work items are unblocked.

When two or more work queue items are unblocked (parallel-ready), an ASCII dependency graph precedes the choices and a harness-appropriate parallel-session numbered choice appears. The graph shows which items can start concurrently and which are blocked, so the user can decide how to divide work across sessions. Up to four content choices plus a parallel-session offer share one numbered list (offer occupies a numbered slot).

Trigger phrases `"what's next"` and `"what should I work on"` remain routed to the full workspace-status orient — users arrive from different journey entry points and benefit from the full picture before seeing choices. Next-actions is the closing section of that full orient, not a separate entry point.

## Boundaries

### Always do

- Derive all choices from the DAG state already resolved in Step 2 — never re-read or re-parse `workspace.toml` inside Step 6.
- Open Step 6 with the explicit preamble "Using Step 2 DAG state only — do not re-read workspace.toml:" so the constraint is visible to the implementing agent.
- Surface the "start new work" choice as the final numbered item in every run, regardless of queue state.
- Render the ASCII graph before the numbered list whenever ≥2 unblocked work queue items exist.
- Detect the harness by checking whether `--bg` appears in `claude --help` output (not by exit code alone), and degrade to prose suggestion when the flag is absent or the check is unavailable.

### Ask first

- Raising the parallel-offer threshold above 2 (e.g. "show graph only when ≥3 items").
- Adding more than one "start new work" line (e.g. splitting `new-spec` vs `new-rfc` into separate numbered items).
- Changing the section heading from `### 6. Next-actions`.
- Extending harness detection to harnesses beyond Claude Code CLI, Conductor, and Omnigent.

### Never do

- Remove `"what's next"` or `"what should I work on"` from the SKILL.md frontmatter description trigger list.
- Add a Step that re-reads `workspace.toml` — Step 6 consumes Step 2's resolved state.
- Render a Mermaid diagram or any format requiring harness rendering; ASCII only.
- Call `claude --bg` or any spawn API on a harness where support is unconfirmed; degrade to prose instruction instead.
- Add a dependency on a new pack or external tool.

## Testing Strategy

Two verification modes apply; the skill is pure prose (no compiled code), so no TDD stubs:

- **Goal-based check (grep/diff):** structural and textual ACs — preamble text present (`grep`), `"what's next"` and `"what should I work on"` in frontmatter (`grep`), `### 6. Next-actions` before `## See also` (`grep`), no `workspace.toml` read instruction in Step 6 (`grep`).
- **Manual QA (prose-review):** behavioral rendering ACs — section presence, choice rendering and ordering, graph appearance, pack-absent note, parallel-offer branch. This skill has no executable artifact; verification is a structured prose walk against each fixture case: the reviewer reads Step 6 prose alongside the fixture state and asserts the described output matches the expected result. All five fixture cases (A-installed, A-absent, B×2 harness variants, C, D) were walked in this manner and passed.

Four fixtures cover the full decision tree:

- **Case A-installed — active spec + single unblocked queue item + active `shape` shaping item (pack available):** next-actions emits 4 numbered choices (active spec, queue item, shaping item with skill command, start new work); no graph.
- **Case A-absent — same but shaping entry is `type=research` and `desk-research` pack not installed:** Choice 3 line reads `"requires \`desk-research\` pack — install to work this item"` instead of a skill command.
- **Case B — no active spec, ≥2 unblocked queue items + 1 blocked item:** next-actions emits ASCII graph, then 3 items: parallel-session offer (first slot), first unblocked queue item, start new work; blocked item absent. Run Case B twice: once in Claude Code (verify `claude --bg` emitted), once with a stub `claude` script on `PATH` whose `--help` output omits `--bg` (verify prose suggestion emitted, no `claude --bg`).
- **Case C — queue empty, shaping queue empty:** next-actions emits 1 choice (start new work only).
- **Case D — all queue items blocked:** no graph (0 unblocked < 2), Choice 2 omitted; shaping and start-new-work choices present if applicable.

## Acceptance Criteria

- [x] `### 6. Next-actions` section appears at the close of every workspace-status run, replacing any implicit open-ended closing prose.
- [x] Step 6 opens with the preamble "Using Step 2 DAG state only — do not re-read workspace.toml:" (verifiable by grep on the SKILL.md).
- [x] Choice 1 (active spec): present as one line with `work-loop docs/specs/<slug>/` inline when `[work].active` is non-empty; omitted when empty.
- [x] Choice 2 (next unblocked work queue item): present as one line with `work-loop docs/specs/<slug>/` inline when `[work].queue` has ≥1 unblocked entry; uses first unblocked entry by queue order; omitted when none.
- [x] Choice 3 (next shaping item): present as one line with the appropriate skill command inline when a shaping item is actionable — active shaping entry first (excluding `type=signal`); then first unblocked ready entry if active is empty (also excluding `type=signal`), mirroring Step 3's exclusion of `signal` from "Ready to start." If the entry's required skill/pack is not installed, the line reads "requires `<pack-name>` pack" instead of the skill command (matching Step 4's existing note format). Omitted only when no actionable shaping entry exists.
- [x] "Start new work" choice: always present as the final numbered item, listing `new-spec` · `new-rfc` · `new-adr` · `queue-add` as inline options on one line.
- [x] ASCII dependency graph: rendered before the numbered choices when ≥2 unblocked work queue items exist; absent when <2. Graph shows each queue entry with `[ready]` or `[blocked by <slug>]` annotation (textual encoding of `needs` relationships; no drawn arrows required).
- [x] Parallel-session offer: a numbered choice, rendered when graph is present. On Claude Code CLI (Bash tool available and `--bg` appears in `claude --help` output): numbered choice emits `claude --bg "work-loop docs/specs/<slug>/"` for each parallel-ready root node. On all other harnesses or when the flag check is unavailable: prose suggestion with manual commands for each parallel-ready root node; no automated spawn attempted.
- [x] No workspace.toml re-read in Step 6 — choices derive exclusively from Step 2 DAG state. Verified by: (a) grep confirms the preamble text is present; (b) no instruction to open or parse `workspace.toml` appears in Step 6 prose.
- [x] Frontmatter unchanged: `"what's next"` and `"what should I work on"` remain in the SKILL.md description trigger list.

## Assumptions

- Technical: `spec-A-workspace-status-rename` is in `["ini-002".work].shipped` — blocking dependency satisfied (`workspace.toml`).
- Technical: workspace-status is a single `SKILL.md`; no compiled artefacts; change is prose-only (`.claude/skills/workspace-status/` directory listing).
- Technical: frontmatter trigger list includes `"what's next"` and `"what should I work on"` — these remain; next-actions is the closing block of workspace-status output, not a separate entry point (`SKILL.md` frontmatter, line 3).
- Technical: no explicit closing step exists in current SKILL.md — open-ended prose is implicit LLM behaviour; this spec adds an explicit Step 6 inserted before `## See also` under `## Procedure` (confirmed by reading SKILL.md structure).
- Technical: `claude --help` output includes a `--bg` flag entry when `--bg` is supported — this is the discriminating harness check (not exit code alone). Older Claude Code versions or non-Claude `claude` shims that lack `--bg` would not match.
- Technical: parallel session APIs — Claude Code CLI: `claude --bg "<task>"` confirmed (primary docs, code.claude.com); Conductor: UI-only workspace creation at the harness level, but Conductor sessions run the bundled `claude` binary which carries `--bg`, so the detection probe succeeds and the spawn path fires from within Conductor (changelog + research 2026-07-20 — enumerated as informational, not a harness-level gate); Omnigent: static-DAG orchestration only, not dynamic mid-run spawn (GitHub + research 2026-07-20); all other harnesses (Cursor, Kiro, Copilot, Air, Devin Desktop): no confirmed in-agent spawn API (research 2026-07-20).
- Technical: dependency graph format is ASCII — no Mermaid or rendered diagrams (user confirmation 2026-07-20).
- Product: "start new work" choice is surfaced in every run, not only when queue is empty (user confirmation 2026-07-20).
- Product: full-orient path preserved — trigger phrases route to workspace-status (which ends with next-actions); next-actions is not a standalone entry point (user confirmation 2026-07-20).
- Process: single-person change, no new ADR/RFC dependency, non-structural skill prose edit — light-mode work-loop per `AGENTS.md` risk triggers.
