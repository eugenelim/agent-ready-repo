# Verification ledger — intent-review-mandate-split

Execution observations. Not a second requirements record: the contract is
`spec.md` and the strategy is `plan.md`.

## T8 — observed reviewer behavior

**Blocked in this session.** The three observed-behavior criteria cannot be
satisfied here, for a reason outside the contract.

### What was dispatched

| Field | Value |
| --- | --- |
| Projected revision | `8d20edb9a` |
| `.claude/agents/shaping-reviewer.md` | `8b77355ddcbf303e605d0cd9a777cdba0e3cd5f18b07260524803ee2bc7786e6` |
| `.claude/agents/adversarial-reviewer.md` | `521e0248df11e1967d6ba3a33de4ba857ae34428ad8446675d7110f0554874a2` |
| Projection written | 2026-09-11 13:13:55 |
| Dispatch attempted | 2026-09-11, later the same session |

### Observation 1 — malformed intent, `shaping-reviewer` `intent` mode

Target: a scratch intent built to violate five conditions at once — a solution
as the statement, no non-goals, no assumption named as riskiest, children
overlapping on briefs, and `Owner: the team`.

**Expected:** `MALFORMED(owner)` alone, since the owner token suppresses the
other five.

**Observed:** `Result: Findings`, followed by ten severity-ordered findings,
each carrying a `Fix:`. No `MALFORMED` token was emitted.

**Diagnosis — not a contract defect.** The dispatched agent was running the
pre-change body. Its finding 8 reported "least-artifact projection absent",
and finding 3 reasoned from "core-only viability"; both phrases exist only in
the body at `origin/main` (1 occurrence each there, 0 in the current source and
0 in the current projection). Every on-disk copy carries the new contract —
`packs/core/.apm/agents/`, `.claude/agents/`, and `.codex/agents/`, 5
`MALFORMED` occurrences each — and no user-scope copy exists to shadow them, so
the stale body came from the host rather than from the filesystem. The pack
suites assert the new contract at 138 passing cases.

The exact caching rule is **not** established: in the same session an
`adversarial-reviewer` dispatch returned the new contract's output shapes. That
agent can read files, so "served fresh" and "read its own body" are
indistinguishable from its reply. What is established is that a mid-session
projection rewrite is not reliably what a dispatched subagent runs.

**What the observation does establish:** the pre-change contract behaves exactly
as ADR-0108 describes it, which is why the decision was taken. Ten findings and
ten `Fix:` lines on a 24-line intent, including a request to add a boundary
section and unresolved-questions section to an artifact whose only job was to
name a bet, is the failure mode the split exists to end.

### Observation 2 — well-formed intent, `shaping-reviewer` `intent` mode

Target: `docs/product/intents/cut-before-adding-solution-ladder.md`, with
RFC-0099 supplied as its parent.

**Expected:** empty output.

**Observed:** `Result: Findings`, ten findings with `Fix:` lines, and a
"Children question" section — another rubric item this change deleted. Same
stale definition as observation 1; not evidence about the shipped contract.

### Observation 3 — `adversarial-reviewer` `intent` mode

Target: the same intent and parent.

**Expected:** an open question with a named decider, or a validation hook
carrying a kill condition and its triggering activity, or empty.

**Observed:** exactly that, and nothing else. One open question naming the
RFC-0099 approver as decider, and one validation hook whose kill condition is
"across the next 10 real work-entry requests… two plausible first routes for the
same content" with ordinary intake traffic as the triggering activity. No
severity label, no `Fix:`, no clean sentinel, no third shape.

**Provenance is ambiguous, so this is not recorded as a passing observation.**
The dispatch prompt never described the two output shapes, so that vocabulary
came from the agent body — but this agent holds `Bash` and `Read` and used 16
tool calls, so it may have read its own new body from disk rather than been
served it by the host. A behavioural criterion cannot rest on a run whose
definition source is undetermined.

**What it does show:** the two output shapes are writable and useful on a real
intent. The open question it produced is substantive — see below.

### Finding raised by observation 3, for the owner

The adversarial intent dispatch asked whether the accepted boundary in
`docs/product/intents/cut-before-adding-solution-ladder.md` is "no additional
mode on `shaping-reviewer`" (which this change honours: still three modes) or
"no additional independent review gate per shaping artifact" (which it does not:
an intent may now pass two reviewers). The intent constrains the mode count at
`:118` and `:430-433` and says nothing about reviewer count. Decider named:
the RFC-0099 approver. Recorded here rather than resolved, because it is an
owner decision about an accepted boundary and not a defect in this change.

### Route to closing these three criteria

A session started after `8d20edb9a` loads the new definitions. The three
dispatches then re-run unchanged against the same two fixtures — the scratch
malformed intent, recreated from the description above, and
`docs/product/intents/cut-before-adding-solution-ladder.md` with RFC-0099 as its
supplied parent. Until that run is recorded here, the three observed-behavior
criteria stay unchecked and `spec.md` stays `Implementing`.
