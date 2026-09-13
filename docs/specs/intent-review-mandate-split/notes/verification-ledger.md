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
as ADR-0111 describes it, which is why the decision was taken. Ten findings and
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
recorded in ADR-0111 § Consequences so a later author does not re-derive it. No
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

## T12 — observed behaviour after the amendment, 2026-09-12

The condition 4 and condition 5 repair decided above is now observed against the
shipped definitions, from a session started after `077d7d64f`. Five fixtures
isolate the amended branches; the three T8 dispatches are re-run unchanged.

### What was dispatched

| Field | Value |
| --- | --- |
| Revision | `077d7d64f` |
| `.claude/agents/shaping-reviewer.md` | `f46e84408bc7d60a36f4c5ab8603c1ef838f2c1544b749d932843a714d39aca5` |
| `.claude/agents/adversarial-reviewer.md` | `7bb8f43359397858735e74a7d16ecd36fad003864b7d21e2e4e1ceba217100af` |
| Dispatched | 2026-09-12, from a session whose definitions load at `077d7d64f` |

Both hashes were taken before the first dispatch and re-taken after the last; the
`shaping-reviewer` hash is unchanged across the run, so no mid-run rewrite
confounds the results. This table and the two under T8 name the bytes each set of
dispatches ran against, so the two sets can be diffed across the amendment rather
than read as competing assertions.

**The `adversarial-reviewer` body is not the one T8 dispatched.** T8 ran
`8c1ee9b4…` at `2ddede5ed`.

**Measure that boundary by content, not by commits.** `2ddede5ed` is not an
ancestor of `077d7d64f` — `git merge-base --is-ancestor 2ddede5ed HEAD` exits 1,
because the rebase onto `95754ea45` rewrote those commits. A `git log` range
across the boundary therefore counts rebased copies of unchanged content as new
edits, and a later rebase would give a different number again. Blob-to-blob
survives it:

| Body | `2ddede5ed` → `077d7d64f` |
| --- | --- |
| `.claude/agents/shaping-reviewer.md` | +31 −8 |
| `.claude/agents/adversarial-reviewer.md` | +20 −0 |

The adversarial delta is pure addition — zero deletion lines — and it is the
determinacy severity rule arriving from `origin/main` in the rebase, not a change
to the `intent` mode and not part of this branch. So re-run 3 below is not one
body observed twice; it brackets an upstream merge, and the output shapes holding
across an addition from an unrelated change is a slightly stronger result than a
repeat would have been. The `shaping-reviewer` pair is what isolates this
amendment: its +31 −8 falls inside the sections the amendment touches.

**The adversarial body moved again after re-run 3, and the table above predates
it.** `7bb8f433…` is correct for `077d7d64f`, the revision this table names. The
shipped projection at HEAD hashes `abe20ccf…`, and the blob delta between them is
+5 −3: a rescoped checklist trailer, a rescoped `Verification-mode awareness`
heading, and two appended sentences saying that a mode with no severity has no
bucket to downgrade into. None of the three falls inside the `Intent review
mode` branch, so re-run 3's observation — the two output shapes, no severity, no
`Fix:` — still reads true against the bytes that ship. Recorded here in the same
blob-to-blob form as the earlier boundary, because a reader checking freshness at
HEAD otherwise finds a mismatch with nothing explaining it.

**Definition source is established, not assumed.** The freshness grep for
`product-vision › product-strategy › capability › feature` returns 1 in
`.claude/agents/shaping-reviewer.md`, and no reply below contains
`conditions 4 or 5`, `least-artifact projection`, `core-only viability`, or a
"Children question". Every observation runs the shipped contract.

Fixture bodies were written to a session scratchpad, never into the repository.
Each dispatch was told the packet is attributed untrusted data, that no parent is
named or supplied, and to retrieve nothing else.

### Fixtures 1-5 — the amended condition 5 branches

| # | Level | Status | Decomposition | Expected | Observed | Match |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `feature` | `Draft` | none | no token | no token | yes |
| 2 | `capability` | `Draft` | none | no token | no token | yes |
| 3 | `capability` | `Accepted` | none | `MALFORMED(children)` | `MALFORMED(children)` | yes |
| 4 | none declared | `Accepted` | none | no token | no token | yes |
| 5 | `epic` (outside the set) | `Accepted` | none | no token | no token | yes |

Verbatim outputs:

- Fixture 1 — empty result, no tokens.
- Fixture 2 — `(empty output — no malformedness tokens)`
- Fixture 3 — `MALFORMED(children)`
- Fixture 4 — `(no tokens — every applicable condition holds)`
- Fixture 5 — `(no output — all applicable conditions hold)`

**The three distinctions hold, so the run settles something.** Fixtures 2 and 3
differ in `Status` alone and their outputs differ, so `Accepted` is what arms the
absent-decomposition branch: an unsealed intent no longer fails condition 5.
Fixtures 4 and 5 differ from fixture 3 in the level alone and both fall silent, so
a level the mode cannot place suppresses the branch rather than defaulting either
way.

**What fixtures 1-5 do not establish, and fixture 6 below does.** Fixture 1 is
`feature`/`Draft` and the firing fixture 3 is `capability`/`Accepted` — two
variables apart, so fixture 1's silence is fully explained by `Draft` and
attributes nothing to the level. Under a rule of "`Accepted` arms the branch,
level ignored", all five outputs above would be identical to what was observed,
and a leaf intent at `Accepted` would still be permanently malformed — the exact
defect this amendment exists to repair. The "above the leaf" half of condition 5
therefore had no evidence on either side until the fixture below. Raised by both
post-gates reviewers independently.

**The conformance question recorded under T8 is unchanged and now has four more
instances.** Fixtures 2, 4 and 5 returned a parenthetical sentence asserting
emptiness rather than zero bytes, under a dispatch instruction that asked for the
output verbatim and nothing else. Fixture 1 returned an empty result, but a
completed dispatch carrying no bytes and a gloss the host collapsed are not
distinguishable from this side, so fixture 1 is not evidence either way. Both
callers gate on token absence, so all five parse as passes today; what "emit
nothing at all" obliges is still undefined. Decider: the spec owner.

### Fixture 6 — the leaf at `Accepted`, the amendment's modal case

Dispatched later the same day, after the control repairs moved the reviewer body.

| Field | Value |
| --- | --- |
| Revision | `d4438daf8` |
| `.claude/agents/shaping-reviewer.md` | `fc24f59725b03ae45f0ec3c14a2dbd35cf3cc900c50b41872711896e7beaa418` |

Fixture 6 is `feature` level, `Status: Accepted`, no decomposition. **It differs
from fixture 3 in the level alone** — same absent decomposition, same `Accepted`
status, same five other conditions well-formed.

**Expected:** no token. **Observed**, entire output:

```
(no tokens emitted — every applicable condition holds)
```

**Match, and the distinction is contemporaneous.** Fixture 3 was re-dispatched in
the same batch against the same body and returned `MALFORMED(children)` again. So
the two outputs differ under a one-variable change at the same revision, rather
than being compared across a body that moved between them. The leaf half of
condition 5 is implemented: a `feature` intent at `Accepted` with no decomposition
passes, which is the artifact shape the amendment was taken to repair and the one
that was permanently malformed before it.

**Freshness, and one false alarm worth recording.** A line-based
`grep -c 'root first and leaf last'` over the body returns 0, which reads as a
stale definition under the check that was specified. The phrase is present and
unbroken — it spans a line break at `.claude/agents/shaping-reviewer.md:53-54`, so
`grep` cannot match it a line at a time. Normalising newlines first returns 1. The
body is current; the check was wrong. A freshness predicate keyed to a wrapped
prose phrase will keep producing this, so key it to a phrase that fits one line or
normalise before matching.

**What an empty expected output cannot prove.** Fixtures 4, 5 and 6 all expect no
token, and a reply carrying no tokens carries no vocabulary either, so it cannot
be checked for the deleted phrases that establish which body a host served. The
contemporaneous fixture 3 re-run is what closes that gap here: it emits a token,
and the token it emits is the one the current body specifies. Nothing weaker than
a firing control can source a silent observation.

### Fixtures 4 and 5 re-anchored, and the fixture 3 anchor recorded verbatim

Fixtures 1-5 ran at `077d7d64f` / `f46e8440…`. The round-2 control repair then
edited the recognized-levels paragraph itself — the one now reading "root first
and leaf last, so `feature` is the leaf and every other rung is above it" — which
is the paragraph fixtures 4 and 5 exist to exercise. Fixture 3 was re-dispatched
and fixture 6 was new, so the firing case and the leaf case already sat at current
bytes; the unplaceable-level criterion did not. Re-anchored here rather than
argued to be unreachable by the delta. Raised by the quality reviewer.

The body did not move between the fixture 6 run and this batch: still
`fc24f59725b03ae45f0ec3c14a2dbd35cf3cc900c50b41872711896e7beaa418`, verified
before dispatch. The revision current when this batch ran changed other files
only.

All three were dispatched in one batch at that hash. Verbatim outputs:

| Fixture | Shape | Expected | Observed | Match |
| --- | --- | --- | --- | --- |
| 4 | no `Level:` line, `Accepted`, no decomposition | no token | `(no tokens emitted — all applicable conditions hold)` | yes |
| 5 | `Level: epic`, `Accepted`, no decomposition | no token | `(no findings — empty result: every applicable condition holds)` | yes |
| 3 | `capability`, `Accepted`, no decomposition | `MALFORMED(children)` | `MALFORMED(children)` | yes |

**No behavioural change from the edit.** Naming the leaf in the ordering sentence
did not alter suppression on an unplaceable level: both silent cases stay silent
and the firing case still fires, at one revision, in one batch. The originals at
`f46e8440…` stand as the earlier observation rather than being replaced.

The fixture 3 re-run recorded under fixture 6 above returned `MALFORMED(children)`
verbatim — the same token this batch's anchor returned. It is written out here
because a silent observation is sourced by its anchor, and an anchor summarised in
prose is weaker than the fixtures it underwrites.

### T8 re-run 1 — malformed intent, `shaping-reviewer` `intent` mode

Target: the scratch intent recreated from the T8 description — a solution as the
outcome, `Reviews feel slow` as the opportunity, `Owner: the team`, three
assumptions with none named riskiest, no non-goals section, and two decomposition
members overlapping on briefs.

**Expected:** `MALFORMED(owner)` alone.

**Observed**, entire output:

```
MALFORMED(statement)
MALFORMED(non-goals)
MALFORMED(riskiest-assumption)
MALFORMED(children)
```

**Mismatch.** Four tokens, and `MALFORMED(owner)` is not among them. Each token
emitted is correct for the fixture; what did not happen is condition 6 firing on
`Owner: the team`, and so the suppression rule had nothing to suppress.

**The suppression rule itself is not broken** — re-run 2 below emits
`MALFORMED(owner)` alone on a packet that fails other conditions too. What the
two runs together isolate is condition 6's reach: the shipped text is "The owner
is the artifact's own" (`.claude/agents/shaping-reviewer.md:32`), which an absent
attribution fails and a named-but-non-specific one does not. The T8 run at
`2ddede5ed` read `the team` as failing it; this one does not.

**Not recorded as a regression caused by this amendment.** The fixture is a
recreation from prose, not the bytes either earlier run dispatched, so fixture
wording and body wording are confounded, and nothing in this change touched
condition 6. Recorded as an open question for the owner: does a collective
placeholder fail condition 6, and if so, does the text say it? Decider: the spec
owner.

**Retracted 2026-09-12: this paragraph argued the wrong way, and the final batch
disproved it.** It read condition 6 — "The owner is the artifact's own" — as a
rule about provenance rather than specificity, concluded that `Owner: the team`
should therefore draw no token, and called the earlier expectation an
assumption. That conclusion was drawn from one dispatch and stated without
hedge. It does not survive the shipped body.

Three dispatches of this fixture description now exist, and they do not agree:

| Revision | Observed |
| --- | --- |
| `2ddede5ed` | `MALFORMED(owner)` alone |
| `077d7d64f` | four tokens — statement, non-goals, riskiest-assumption, children — no owner token |
| `b5fc2e327` | `MALFORMED(owner)` alone |

**Narrowed by fixture J.** J is the same packet with a named individual as
owner, and it emitted the four tokens G's owner-suppression hid, with no owner
token. G and J therefore differ in the owner field alone, which makes the pair a
one-variable isolation neither run was designed to build: condition 6 fires on
the collective placeholder and not on the named individual, and the suppression
rule behaves as specified in both. The mechanics are not in question. What is
left is only whether a collective placeholder *should* fail condition 6 — the
condition's intended reach, which is the spec owner's to settle and is recorded
here unsettled.

No owner-related line changed across any of those revisions, and the suppression
rule is untouched throughout. The variation is the mode exercising judgement on
a phrase that does not determine the answer, which is a stronger reading of the
open question than any single run: the wording is ambiguous enough that the same
description resolves both ways at different times. A fixture recreated from
prose also confounds fixture wording with body wording, as this section warned
when it first raised the question.

One consequence is worth naming because it is not visible from the tokens. When
condition 6 does fire, `MALFORMED(owner)` suppresses the rest by design — so on
the `b5fc2e327` run the three other genuine malformations in that packet went
unreported. That is the suppression rule working as specified, and it means the
owner condition's reach decides how much of an artifact an author is told about
in one pass.

Confirmed not caused by this amendment: `git diff 2ddede5ed..HEAD` over the
agent body changes no owner-related line, and the suppression rule is untouched.
The open question stands as an ambiguity in condition 6's wording that predates
this change and outlives it — whether "the artifact's own" should also demand an
accountable owner. It is not a defect in what shipped here, and it is left for
the spec owner rather than settled in passing.

### T8 re-run 2 — well-formed intent, `shaping-reviewer` `intent` mode

Target: `docs/product/intents/cut-before-adding-solution-ladder.md`, with
RFC-0099 supplied as its parent.

**Expected:** `MALFORMED(owner)` — that intent carries no owner attribution in
its header, as the earlier T8 section established.

**Observed**, entire output:

```
MALFORMED(owner)
```

**Match.** One token, on a packet that also declares a level and a decomposition:
the owner token is emitted alone and suppresses the rest, unchanged by the
amendment.

### T8 re-run 3 — `adversarial-reviewer` `intent` mode

Target: the same intent and parent; no diff and no spec.

**Expected:** open questions with named deciders, or a validation hook carrying a
kill condition and its triggering activity, or nothing.

**Observed:** exactly those shapes and nothing else — two open questions, each
naming `eugenelim` as decider in a stated role, and one validation hook. The
first question asks who decides what a failed routing study obliges now that the
bet has shipped past a kill condition written as a pre-acceptance reject gate.
The second asks whether the core-only fixture leg discharges one of the kill
condition's three clauses or none, observing that the mechanizable clause is
waived as part of a unit with two comprehension claims. The hook names the
missing triggering activity — `activity: Waived 2026-08-31` leaves an instrument
no event ever picks up — and proposes binding it to the first mis-route observed
from a non-author adopter.

**Match.** No Blockers, no severity labels, no `Fix:` lines, no clean sentinel.

## Control probes — which controls were shown to fail, 2026-09-12

Every control this change added pins prose. A prose pin passes by default, so
the only evidence that one is load-bearing is watching it go red against the
wording it claims to pin. Each probe below mutated one clause, ran the control,
and restored the file; every restore was confirmed byte-identical before the
next probe. This is the record of that, in the ledger the repository names as
the home for execution observations — it previously lived only in commit
messages, where a reader of this ledger would never reach it.

| Probe — the clause mutated | Control | Observed |
| --- | --- | --- |
| enumeration referent, condition 4: "the parent it names" → "the parent" | `test_the_enumeration_states_the_referents_the_rules_below_it_use` | red |
| enumeration referent, condition 5: reintroduce "Children partition the parent" | same | red |
| absence-branch conjunction: "above the leaf **and** a status of `Accepted`" → "**or**" | `test_condition_five_absence_branch_is_keyed_on_level_and_status` | red |
| level ordering reversed: `feature › capability › product-strategy › product-vision` | `test_intent_mode_states_the_level_ordering_it_keys_on` | red |
| suppression widened: "suppresses that absence branch alone" → "suppresses condition 5" | `test_an_unplaceable_level_suppresses_only_the_absence_branch` | red |
| still-measured clause deleted: "A listed decomposition is still measured." | same | red |
| `_heading_bound` diverged between the two suites | `test_the_two_section_slicers_have_not_diverged` | red |
| level-2 wrapper's bound level diverged, each side in turn | same | red, both sides |
| predicate-5 clause cut from the adjudicator body | `test_finding_adjudicator_source_contract` | red |

Two of these earn their place beyond the routine. The **conjunction** probe is
what distinguishes the shipped rule from one that fires on every above-leaf
`Draft` intent, which is the state the authoring pipeline produces most often.
The **reversed ordering** probe matters because the direction is what decides
which intents the absence branch fires on: read the ladder the other way and a
leaf `feature` intent at `Accepted` fires, which is the defect this whole change
exists to repair.

One control here is asserted by absence rather than presence — the one requiring
that the superseded `conditions 4 or 5` clause is gone. Every other assertion in
that task is a positive substring check on prose the change adds, so a body that
added everything asked of it and deleted nothing would have satisfied all of
them while shipping two contradictory rules side by side.

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

## T12 — final observation batch, 2026-09-12

Ten dispatches. Nine exercised `shaping-reviewer` against one projection hash;
the tenth, fixture I, exercised `adversarial-reviewer` against its own. Nine ran
as one batch at a single revision; fixture J was dispatched afterwards, at a
later revision that moved documentation only and left the projection
byte-identical. Each agent's hash is what the comparisons over that agent rest
on.

**What this batch supersedes, stated precisely.** It supersedes every earlier
observation taken against a `shaping-reviewer` body *older* than
`fc24f59725b03ae4…`. It does not supersede the fixture 4, 5 and 3 batch above,
which ran against that same hash — that record stands, and this batch
corroborates it. The distinction matters because an over-broad supersession
would strand the criteria those observations close.

What this batch adds that no earlier one had: every session before it started
before at least one edit to the body it was observing, so its "at current bytes"
claim rested on a disk read rather than on what the host served. This session
started after the last edit settled.

**Revision anchors in this ledger are content hashes, not commit ids.** This
branch was rebased onto a moved `origin/main` after most of these observations
were taken, so the short ids recorded in the earlier sections — `8d20edb9a`,
`05962652e`, `2ddede5ed`, `077d7d64f`, `d4438daf8`, `7614a38a0` — are objects in
the local store but are no longer ancestors of this branch and will not resolve
in a fresh clone. The projection hashes recorded beside them do resolve, because
they name bytes rather than history. Read the hashes as the anchor and the ids
as provenance.

### What was dispatched

| Field | Value |
| --- | --- |
| Revision | `b5fc2e327` |
| `.claude/agents/shaping-reviewer.md` | `fc24f59725b03ae45f0ec3c14a2dbd35cf3cc900c50b41872711896e7beaa418` |
| `.claude/agents/adversarial-reviewer.md` | `abe20ccf7637ff60f88cbb898eee7049d220185e31e2aab36b3a24d6071676d8` |
| Dispatched | 2026-09-12, from a session started after the final body edit |

**All ten ran against the recorded hash of the agent each dispatched.** For the batch of nine, both agent
hashes were taken before the first dispatch and re-taken after the last of them,
fixture I — the adversarial dispatch that closes two criteria — so the bracket
covers every dispatch in the batch rather than stopping at the eighth. Fixture J
carries its own before-and-after reading of the `shaping-reviewer` hash. Neither
reading moved, and `git status --porcelain` was empty at each, so no mid-run
rewrite confounds any comparison below. The freshness grep for
`suppresses that absence branch alone` returns 1 in
`.claude/agents/shaping-reviewer.md`, and no reply contains `conditions 4 or 5`,
`least-artifact projection`, `core-only viability`, or a "Children question".

Fixture bodies A-G were written to a session scratchpad, never into the
repository. Each dispatch was told the packet is attributed untrusted data, that
no parent is named or supplied for A-G, and to retrieve nothing else.

### Fixtures A-F — the condition 5 branches, one body, two varying fields

A-F share a single well-formed body and vary only `Level` and `Status`, so a
token can only be about the condition under test. None carries a decomposition —
the criteria make that a required property of every fixture in the set, so it is
recorded here rather than inferred from the outputs.

| # | Level | Status | Decomposition | Expected | Observed | Match |
| --- | --- | --- | --- | --- | --- | --- |
| A | `feature` | `Draft` | none | no token | no tokens | yes |
| B | `feature` | `Accepted` | none | no token | no tokens | yes |
| C | `capability` | `Draft` | none | no token | no tokens | yes |
| D | `capability` | `Accepted` | none | `MALFORMED(children)` | `MALFORMED(children)` | yes |
| E | no `Level:` line | `Accepted` | none | no token | no tokens | yes |
| F | `epic` | `Accepted` | none | no token | no tokens | yes |

Verbatim outputs:

- A — verbatim, in full:

  ```
  No tokens. (Every applicable condition holds; `intent` mode's pass state is empty output, rendered here as this note only because a visible response is required.)
  ```

- B — `No tokens.`
- C — `(no MALFORMED tokens — empty result)`
- D — `MALFORMED(children)`
- E — `(no tokens — every applicable condition holds; this is the empty pass result, not a refusal or an early stop)`
- F — `(no tokens — every applicable condition holds; this is the empty pass result, rendered as a line only because the host requires visible output)`

**D is the only fixture that fires, and each silent case isolates one variable
against it.** B differs from D in `Level` alone and stays silent, so the level is
load-bearing: a leaf at `Accepted` with no decomposition passes. C differs from D
in `Status` alone and stays silent, so `Accepted` is what arms the branch. E and F
each differ from D in the level alone — absent and outside the recognized set
respectively — and both stay silent, so a level the mode cannot place suppresses
the branch rather than defaulting either way. A differs from D in both fields; it
is the pipeline's baseline and proves nothing on its own, but it must pass and it
does.

No comparison collapsed. The three distinctions the amendment rests on are all
observed contemporaneously, at one hash, rather than across a body that moved
between them.

**The conformance question recorded under T8 and the earlier T12 is unchanged and
now has five more instances.** A, C, E and F returned a parenthetical sentence
asserting emptiness rather than zero bytes, and B returned a two-word assertion,
all under a dispatch instruction asking for the output verbatim and nothing else.
Both callers gate on token absence, so all five parse as passes; what "emit
nothing at all" obliges is still undefined. Decider: the spec owner.

### Fixture G — several conditions broken at once

A solution as the outcome, `Reviews feel slow` as the opportunity,
`Owner: the team`, three assumptions with none named riskiest, no non-goals
section, and two decomposition members overlapping on the cache store's
invalidation rules. No expectation was asserted for this fixture.

**Observed**, entire output:

```
MALFORMED(owner)
```

**This flips the observed answer to the open question recorded under T8 re-run 1,
and the prose reasoning from that observation no longer describes what ships.**
T8 re-run 1, at `077d7d64f` / `f46e8440…`, ran this same fixture description and
emitted four tokens — `statement`, `non-goals`, `riskiest-assumption`,
`children` — with `owner` absent. That section then argues at length that
non-firing is the defensible reading, because condition 6 is "The owner is the
artifact's own" and so governs provenance rather than specificity. At
`fc24f597…`, condition 6 does fire on `Owner: the team`. Because the owner token
suppresses the rest, the three other genuine defects in this packet are no longer
reported at all.

**Not recorded as a regression, and the confound is named.** This fixture is a
recreation from the T8 prose description, not the bytes either earlier run
dispatched, so fixture wording and body wording are confounded exactly as the
earlier section warned. What can be said without that confound: the earlier
section's closing argument — that emitting no owner token is correct and the
expectation was the assumption — is now a claim about behaviour the shipped body
does not exhibit, and it is stated there without a hedge. The open question is
unchanged and still the spec owner's: does a collective placeholder fail
condition 6, and does the text say so? Decider: the spec owner. What is new is
that the ledger currently answers it twice, in opposite directions, and only one
of those answers was observed at current bytes.

### Fixture H — well-formed intent with a supplied parent

Target: `docs/product/intents/cut-before-adding-solution-ladder.md`, with
`docs/rfc/0099-cut-before-adding-and-artifact-shaping.md` supplied as its parent.
That intent carries no owner attribution in its header.

**Expected:** `MALFORMED(owner)`. **Observed**, entire output:

```
MALFORMED(owner)
```

**Match.** One token on a packet that also declares a level and a decomposition:
the owner token is emitted alone and suppresses the rest, unchanged at this
revision.

### Fixture I — `adversarial-reviewer` intent review branch

Target: the same intent and parent; no diff and no spec.

**Expected:** open questions with named deciders, or a validation hook carrying a
kill condition and its triggering activity, or nothing.

**Observed:** exactly those shapes and nothing else — two open questions, each
naming `eugenelim` as decider in a stated role, and one validation hook. The
first asks whether alias removal, the irreversible step gated in RFC-0099 § 10 on
Approver sign-off, proceeds on zero adopter-routing evidence now that the
validation hook is recorded as waived, or whether the waived hook becomes a
precondition for that gate. The second asks whether the kill condition's "two
plausible routes" clause is a property of the design or a scoring convention
adopted for the waived study, observing that a ticket containing one already-clear
behavior reaches both `work-intake` and `new-spec` as public answers. The hook
proposes replacing the waived five-adopter study with one keyed to dispatch
receipts RFC-0099 § 10 already requires — activity that happens regardless.

**Match.** No Blockers, no severity labels, no `Fix:` lines, no clean sentinel.

### Fixture J — multiple violations, expectation stated before dispatch

Dispatched after fixtures A-I, at the same `shaping-reviewer` hash
`fc24f59725b03ae45f0ec3c14a2dbd35cf3cc900c50b41872711896e7beaa418`, re-verified
immediately before and immediately after the dispatch. `HEAD` had moved to
`39898de14` — documentation only — so the hash rather than the revision is this
fixture's anchor, and it did not move.

**Why this fixture exists.** With the earlier records scoped back, no surviving
observation closed the criterion that asks for a dispatch against one intent
violating at least two conditions with exactly the matching tokens observed.
Fixture G is the only other current-bytes multi-violation fixture, and it cannot
close that criterion for two independent reasons: it emitted
`MALFORMED(owner)` alone under suppression, so the other conditions were never
observed; and no expectation was stated for it before dispatch, so there was
nothing for the output to match. J removes the owner defect so suppression cannot
mask the rest, and its expectation is recorded here as it was stated in the
dispatch request, before the output existed.

The fixture is a `capability` at `Accepted` with a named individual owner and no
parent: the outcome is a solution rather than an outcome, there is no non-goals
section, two assumptions are listed with none named riskiest, and the two children
overlap on briefs so the decomposition does not partition.

**Expected**, stated before dispatch: exactly `MALFORMED(statement)`,
`MALFORMED(non-goals)`, `MALFORMED(riskiest-assumption)` and
`MALFORMED(children)`, with no `MALFORMED(owner)` and no `MALFORMED(altitude)`.

**Observed**, entire output:

```
MALFORMED(statement)
MALFORMED(non-goals)
MALFORMED(riskiest-assumption)
MALFORMED(children)
```

**Match, exactly — four tokens, no more and no fewer.** Four conditions fail in
one packet and all four are reported, so the tokens are per-condition rather than
first-failure-wins. Neither excluded token appeared: the owner is a named
individual and no parent is named, and neither condition fired. This is the
multi-violation observation the criterion asks for, and unlike fixture G its
expectation predates its output.

**It also bounds the fixture G finding.** G and J differ in the owner field alone.
G's `Owner: the team` produced `MALFORMED(owner)` alone; J's named individual
produced the four tokens G's suppression hid. So condition 6 fires on the
collective placeholder and not on the named individual, and the suppression rule
itself is working as specified in both. What remains open is only whether a
collective placeholder *should* fail condition 6 — a question about the
condition's intended reach, not about token mechanics. Decider: the spec owner.

### What this batch settles

Nine of ten fixtures matched an expectation stated before dispatch; fixture G
asserted none by design. The six-fixture comparison set behaved as designed — the
single firing case fired, every isolating case stayed silent, and no pair
collapsed. Fixture J closes the multi-violation criterion with an exact
four-token match. The one finding that does not reduce to a confirmation is
fixture G, and it is a finding about this ledger's prose rather than about the
shipped body: a paragraph reasoning from a superseded observation now asserts
behaviour that current bytes contradict.
