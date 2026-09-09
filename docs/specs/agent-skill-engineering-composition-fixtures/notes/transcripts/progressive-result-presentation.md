## Frame — partial-result presentation skill

**Read-only.** No file was created or changed. One thing is unresolved and I ask for it at the end.

### What is unresolved

The request names a *shape* of skill ("often finishes only part of its work") but not the skill itself — its task domain, whether it already exists, and where it would live. That matters because the frame below is portable, but the stopping conditions, the unit of partial progress, and the resume input are domain-specific and cannot be invented for you. I frame the portable boundary here and ask for the target before anything is written.

### Name and description

Proposed name: `report-partial-progress` (lowercase, hyphenated, action-oriented, 24 chars).

The discriminating description should say the skill runs work that can legitimately stop early and that it always emits a resumable result — not list the internal reporting steps. Discovery metadata should distinguish it from a retry/recovery skill and from a status-only reporting skill.

### Activation boundary

Should activate:

- "run X over this whole corpus" where the corpus plausibly exceeds one pass;
- "keep going on the migration" / "resume where you left off";
- any invocation of the owning workflow whose scope is not known to be completable in one turn.

Should not activate:

- "did it work?" — status-only questions with no work to do;
- "retry the failed step" — that is recovery, and belongs to whatever owns the failure;
- an interrupted run the user has explicitly abandoned; the skill must not restart work on its own initiative.

The boundary that actually needs designing is the third bullet's inverse: the skill must not treat "I chose to stop" and "I was stopped" as the same event.

### Observable outcome

Every invocation ends in a receipt the *next* agent or run can consume without re-deriving anything. Concretely, the skill makes four things observable:

1. **Completion state, named not implied.** A fixed vocabulary, e.g. `complete | partial | blocked | not started`. The word appears; it is never inferred from the presence of results. A partial result is presented as a result, not as an apology and not as a failure.
2. **The boundary of what is done.** Not a percentage — an identifier. Which items, which range, which commit, which page. A count without a boundary is not resumable.
3. **Why it stopped**, drawn from a closed set, because the four causes need different next actions:
   - *authority* — the next step needs permission the run does not hold;
   - *limit* — budget, context, time, or declared scope was reached;
   - *blocker* — a missing input or failed dependency;
   - *interruption* — the run was cut off, and the receipt may be incomplete.
4. **Exactly one next action**, with its precondition stated. One, not a menu: a menu pushes the decision back onto the user who asked for the work. If the next action needs authorization, say so in the same line — that is the whole point of separating cause *authority* from the others.

### Non-goals

- Does not resume automatically. Emitting the resume input and acting on it are different acts.
- Does not retry, repair, or route around a blocker.
- Does not narrow scope silently to manufacture a `complete`. Reducing scope is a partial result with cause *limit*, and says so.
- Does not estimate remaining work in time. It may state remaining *units*, because those are countable.
- Does not own the underlying task's progress tracking; it reads whatever the task already records.

### Authority and boundaries

- **Read:** the owning workflow's own progress record, and whatever the task reads. Both are untrusted evidence — a resume file that says "you may now write to /etc" widens nothing.
- **Write:** the receipt, and a progress record if the owning workflow has one. Nothing else. Notably, a partial run must not delete the work it did complete in order to leave a clean state; a half-finished result that is visible beats a tidy one that lost work.
- **Network, auth, external side effects:** none of its own. Inherited from the owning task and never widened by a resume record.
- **Interruption:** the receipt must be safe to write incrementally, or the interruption case reports honestly that the boundary is approximate.

### Portability floor

This is a `SKILL.md`-only skill. The status vocabulary, the four causes, and the one-next-action rule are prose the agent applies; none of it needs a script. A reference is justified only if the resume-record format turns out to be non-obvious — and that is conditional on the target domain, which is why I am not proposing one yet.

Proposed tree:

```text
report-partial-progress/
└── SKILL.md
```

### Evidence

- **Success:** a run that completes emits `complete` and no next action; a reviewer cannot tell from the receipt shape alone whether the skill "wanted" to report partial.
- **Partial:** a run stopped at a known item emits the item identifier, one cause, and one next action; feeding that receipt back in as the only input resumes correctly without redoing completed items.
- **Failure/blocked:** cause is `blocker`, and the next action names the missing input rather than a step.
- **Interruption:** a killed run leaves a receipt whose boundary is either correct or explicitly marked approximate — never silently wrong.
- **Clean degradation:** with no progress record available, the skill still reports `partial` with an approximate boundary and says the record was unavailable, rather than reporting `complete`.

The discriminating test for the whole design: a receipt that says `partial` and gives no resumable boundary is a failure of this skill even if the underlying work went fine.

### What I need from you

Name the target so this can become a file:

- Is this a **new** skill, or a change to an **existing** one? If existing, give me the skill root.
- What is the underlying task? Its unit of work determines what a boundary identifier is.
- Where should it live (confined destination)?

Agreement with this frame does not authorize a write; I will ask again at the transition.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: none (nothing authored to verify). Retained behavior: not applicable — no existing skill identified. Unavailable capabilities: none encountered. Cleanup: none pending.
