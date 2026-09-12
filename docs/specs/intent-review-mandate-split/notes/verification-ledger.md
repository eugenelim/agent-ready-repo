# Verification ledger — intent-review-mandate-split

Execution observations. Not a second requirements record: the contract is
`spec.md` and the strategy is `plan.md`.

## T8 — observed reviewer behavior

> **Discharged 2026-09-11 by the run recorded below.** The blockage described in
> this section was real and is kept as the record of why: a host serves the agent
> definition loaded at session start, so the session that wrote the change could
> not observe it. A later session did. Read this section as history and the
> `## T8 — observed reviewer behavior, 2026-09-11` section as the current state.

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
as ADR-0109 describes it, which is why the decision was taken. Ten findings and
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
the RFC-0099 approver.

**Resolved 2026-09-11 by the named decider: mode-scoped.** The boundary means
what it says, the optional advisory read gates nothing, and the boundary after
it already admits the adversarial reviewer as an extra read. The reading is
recorded in ADR-0109 § Consequences so a later author does not re-derive it. No
change to this spec or its implementation followed.

This is the mode's first real output, and it worked: an open question with a
named decider, raised on an accepted boundary that five shaping rounds and three
adversarial rounds over the same artifacts had not surfaced, answered by its
decider in one exchange, and closed without a code change.

### A Codex route was investigated and does not work

`codex exec` (codex-cli 0.153.4) cannot dispatch a projected agent: it has no
`--agent` flag, `codex agents` only browses sessions, and `.codex/config.toml`
treats `.codex/agents` as a write path for authoring rather than a dispatch
registry. Those `.toml` definitions are consumed by the interactive TUI and the
app-server. The projection carrying the new contract and Codex being
authenticated were both confirmed; neither establishes that a headless run can
name the agent, and that third fact is the one the route depended on.

Passing the agent's `developer_instructions` as a prompt preamble was rejected:
it exercises a different runtime and is not evidence about the shipped agent.

### Route to closing these three criteria

A session started after `8d20edb9a` loads the new definitions. The three
dispatches then re-run unchanged against the same two fixtures — the scratch
malformed intent, recreated from the description above, and
`docs/product/intents/cut-before-adding-solution-ladder.md` with RFC-0099 as its
supplied parent. Until that run is recorded here, the three observed-behavior
criteria stay unchecked and `spec.md` stays `Implementing`.

## T8 — observed reviewer behavior, 2026-09-11

The three criteria left open above are now observed against the shipped
definitions, from a session started after `05962652e`. Four further probes were
run to interpret the results.

### What was dispatched

| Field | Value |
| --- | --- |
| Revision | `2ddede5ed` |
| `.claude/agents/shaping-reviewer.md` | `f515419b02a3d1ea8b0c45b5cf999600a134c3b241fdf56e9521bc36ab88d3d8` |
| `.claude/agents/adversarial-reviewer.md` | `8c1ee9b4e1bc449b96db7a053580726460ae6f96962d8cf3d3e2857245f47a63` |
| Dispatched | 2026-09-11, from a session whose definitions load at `2ddede5ed` |

**Definition source is established, not assumed.** No reply cites
`least-artifact projection`, `core-only viability`, or a "Children question" —
the three phrases this change deleted, and the phrases that voided the earlier
attempt. Every observation below runs the shipped contract.

### Observation 1 — malformed intent, `shaping-reviewer` `intent` mode

Target: a scratch intent recreated from the description in the earlier T8
section, not the byte-identical file that section dispatched. Its exact shape:
a solution as the outcome, an opportunity that is a complaint ("Reviews feel
slow"), `Owner: the team`, assumptions listed but none named as riskiest, and
two children overlapping on briefs. It carries no non-goals section.

**Expected:** `MALFORMED(owner)` alone.

**Observed**, entire output:

```
MALFORMED(owner)
```

**Match.** One token, not five: the owner token suppresses the other five as the
contract requires. No severity, no `Fix:`, no clean sentinel.

### Observation 2 — well-formed intent, `shaping-reviewer` `intent` mode

Target: `docs/product/intents/cut-before-adding-solution-ladder.md`, with
RFC-0099 supplied as its parent.

**Expected:** empty output.

**Observed**, entire output:

```
MALFORMED(owner)
```

**Mismatch — caused by fixture selection, not by the contract.** That intent
carries no owner attribution in its header: lines 1-6 are the title, then
`Status`, `Level`, `Scale`, `Maturity`. A case-insensitive search for `owner`
over the file hits only body prose — lines 11, 38, 87, 123-124, 153, 174, 187,
phrases like "one correct owner" and "existing review owners" — and never a
header attribution. The token is what the shipped condition should emit. The
target was not a well-formed intent.

Corroboration from a second, independently dispatched agent: observation 3's
adversarial run wrote, unprompted, "Decider: the intent owner — which the intent
does not name". Two reviewers read the same absence.

A conforming fixture was then run as observation 2b.

### Observation 2b — well-formed intent built to the six conditions

Target: a scratch `feature` intent — owner named, outcome not a solution,
non-goals present, riskiest assumption named, two children partitioning its
parent's two members with no overlap and no gap — with its `capability` parent
supplied in the same packet. Conditions 4 and 5 are exercised positively rather
than vacuously.

**Expected:** empty output.

**Observed**, entire output:

```
(no tokens emitted — all six conditions hold)
```

**Pass on substance.** No `MALFORMED` token, so the contract held on a packet
built to satisfy all six conditions. See the conformance question below for what
this output is not.

### Conformance question — "nothing at all" is not defined

The observation 2b output is not empty. It is a parenthetical sentence asserting
emptiness, emitted under a dispatch instruction that said to return empty if the
contract said empty.

This parses correctly today: both callers gate on token absence, not on
byte-emptiness, and `intake-intent` treats a completed dispatch carrying no
`MALFORMED` token as the pass. What is undefined is whether a gloss conforms.
The reviewer's own contract says "emit nothing at all", the observed behavior
deviates from that text, and nothing tells a future caller which reading binds.

Recorded as a conformance question, not as a pass and not as a failure. Decider:
the spec owner.

### Observation 3 — `adversarial-reviewer` `intent` mode

Target: `docs/product/intents/cut-before-adding-solution-ladder.md` with
RFC-0099 supplied as its parent; no diff and no spec.

**Expected:** an open question with a named decider, or a validation hook
carrying a kill condition and its triggering activity, or nothing.

**Observed:** exactly those shapes and nothing else — two open questions, each
naming its decider, and one validation hook. The first question asks what
re-opens the routing study waived on 2026-08-31, deciding at the first eligible
release under RFC-0099 §10. The second asks what instrument reads the lagging
outcome, observing that the intent names no baseline or counter for
artifacts-per-outcome while the bet itself adds an agent, a skill, two aliases,
and a delivery transition. The hook binds its kill condition to `invoked_alias`
receipts from real adopter traffic at the removal gate, not to fixtures.

**Match.** No Blockers, no severity labels, no `Fix:`.

### Structural absence is handled two ways, and one of them blocks real work

A condition the packet cannot settle emits its token, so absent evidence fails
closed. That is right for a missing packet. It is a different thing from an
absence that is structural: a root intent has no parent by construction, and a
leaf intent has no children. Three probes separate the two readings.

**Probe on a `capability` with no parent supplied** — two tokens,
`MALFORMED(altitude)` and `MALFORMED(children)`. Indeterminate, and recorded
only as a datapoint: a capability legitimately has a parent, and the fixture
named two children while supplying neither, so both tokens are equally explained
by missing evidence. This probe cannot separate the readings, which is why the
two below were built.

**Probe A — root.** A `product-vision` with no `Parent intent:` field at all, two
decomposition members, neither supplied. Observed, entire output:

```
MALFORMED(children)
```

No altitude token. On a root whose parent cannot exist, the reviewer reads the
structural absence as inapplicable and condition 4 passes. The children token is
the named-but-unsupplied evidence gap, so this probe does not test the leaf.

*Instrument disclosure: this dispatch said to emit zero characters rather than a
sentence describing emptiness, so it cannot speak to the conformance question
above. That question rests on observation 2b alone.*

**Probe B — leaf.** A `feature` with its parent named **and supplied in the
packet**, and no Decomposition section at all. Observed, entire output:

```
MALFORMED(children)
```

**One token, not two: altitude passed on the supplied parent.** That is what
makes this an isolation rather than another conflated result — the only
unsettled condition was children, and there was no evidence gap to close,
because a leaf has no decomposition to supply. The token still fired.

*Instrument disclosure: same zero-characters instruction as probe A; it cannot
speak to the conformance question either.*

**What the three establish.** One contract handles structural absence two
different ways:

| Condition | Structural absence | Result | What it needs |
| --- | --- | --- | --- |
| 4, parent | root has no parent by construction | read as inapplicable — passes | a sentence: the text does not require what the reviewer already does |
| 5, children | leaf has no children by construction | read as a failure — cannot pass | a fix before ship: every leaf intent is permanently malformed |

Condition 5 is a defect that blocks real work: under the current text there is no
packet a leaf can present that makes it pass, and a leaf feature intent is the
most common shape the reviewer will see. Condition 4 is correct behavior on
ambiguous text — the reviewer already does the right thing, but nothing in the
prose requires it, so a later reading could go the other way.

Raised for the owner. Neither is recorded as a reviewer defect against T8: the
three T8 criteria are observed above and matched.

### Owner decision, 2026-09-11 — condition 5 is repaired before this ships

The scope owner was shown probe B and the two-row disposition table above, and
chose to repair condition 5 before merge rather than ship it and follow on. The
decision was taken on the measured finding, not on a general caution: a leaf
intent is the modal shape this reviewer sees, and no packet a leaf can present
makes condition 5 pass.

Condition 4 is repaired in the same change, for the opposite reason. The
reviewer already treats a root's absent parent as inapplicable, so nothing about
its behavior changes; what changes is that the contract now says so, which is
what stops a later reading from going the other way.

This decision amends the approved acceptance-criteria set, so it runs through
the controlled amendment path rather than an edit to a sealed contract. This
section is the authority reference that transition cites.

## Concurrent-editing incident, 2026-09-11 — diagnosed

Paragraphs disappeared from this change's files three times while the session
was between commits, and one transient state reached a commit.

**Cause: this session's own `quality-engineer` subagent, running mutation
tests.** That reviewer holds `Bash`, and the brief it was given described the
session's own mutation technique — remove the sentence a control pins, run the
suite, restore. Each observed "deletion" was the middle of that cycle. It was
confirmed by watching one paragraph restore itself while a different one
disappeared, a rolling sequence through exactly the paragraphs this change's
assertions pin. An earlier entry here attributed the edits to an unknown writer;
that was wrong, and the attribution is now established.

| # | File | Transient state observed |
| --- | --- | --- |
| 1 | `packs/core/.apm/skills/intake-intent/SKILL.md` | the `MALFORMED`-token revision rule, `Draft`-blocking rule, materiality list, and nonmaterial carve-out |
| 2 | `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` | the independence fallback and `unavailable` receipt |
| 3 | `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` | the `## Optional adversarial read` heading, then its advisory paragraph |

**The real defect was mine.** A `git add -A` issued before reading `git status`
staged transient state #2 into a commit. The commit was amended after
`test_frame_intent_review_contract_preserves_independence_and_authority` failed,
so no broken state remains in history.

**What this establishes about the tests.** Every transient deletion failed the
assertion pinning it — three for three, across two packs. That is independent
evidence the pins are load-bearing, obtained by a reviewer probing them rather
than by the author asserting they work.

**Operating rule while a `Bash`-holding reviewer is running.** Do not commit.
The tree is not yours alone; a mid-mutation read looks exactly like corruption,
and `git add -A` will capture it. Stage named paths, read `git status` first,
and wait for the reviewer to finish before creating any commit.
