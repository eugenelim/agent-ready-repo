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
0 in the current projection). The agent definition a host dispatches is loaded
once per session, so a projection regenerated mid-session does not change what a
subagent runs. The bytes on disk carry the new contract — verified by direct
read — and the pack suites assert it at 138 passing cases.

**What the observation does establish:** the pre-change contract behaves exactly
as ADR-0108 describes it, which is why the decision was taken. Ten findings and
ten `Fix:` lines on a 24-line intent, including a request to add a boundary
section and unresolved-questions section to an artifact whose only job was to
name a bet, is the failure mode the split exists to end.

### Observations 2 and 3

Not recorded. Both would have been dispatched against the same stale
definition, so neither could produce evidence about the shipped contract. Two
dispatches were started before the staleness was diagnosed; their results are
disregarded for the same reason and are not evidence for or against this change.

### Route to closing these three criteria

A session started after `8d20edb9a` loads the new definitions. The three
dispatches then re-run unchanged against the same two fixtures — the scratch
malformed intent, recreated from the description above, and
`docs/product/intents/cut-before-adding-solution-ladder.md` with RFC-0099 as its
supplied parent. Until that run is recorded here, the three observed-behavior
criteria stay unchecked and `spec.md` stays `Implementing`.
