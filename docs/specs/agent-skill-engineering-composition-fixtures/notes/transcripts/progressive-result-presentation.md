Mode: frame
Write status: not authorized

## What is being framed

A skill whose normal outcome is partial: it does as much of the requested work
as its inputs, authority, or budget allow, then stops with work remaining. The
framing question you asked — how it presents the partial result and the next
action — is a contract question, so it belongs in the skill's completion
contract rather than in prose advice to the model.

The domain is not yet named (what the skill actually does, and why it truncates:
budget, authority, missing input, or upstream failure). That choice changes the
activation boundary and the evidence list below, so I have kept those generic
and marked where your answer plugs in. Everything else holds regardless.

## The partial-result contract

Make three things separately observable, in this order, every run:

1. **What was completed** — the exact unit of work finished, enumerated as
   concrete items (files, records, sections), not a percentage or a mood.
   "Processed 4 of 11 inputs" with the 4 named; never "mostly done".
2. **Why it stopped** — one stable reason drawn from a closed vocabulary the
   skill declares, so the reason is machine-checkable and the model cannot
   invent a new one under pressure. A useful starting set: `budget-exhausted`,
   `authority-required`, `input-missing`, `upstream-unavailable`,
   `interrupted`.
3. **The next action** — a single named action with the authority it needs and
   the state it resumes from. One action, not a menu; if several are genuinely
   open, that is itself the stop reason (`authority-required`) and the skill
   asks rather than picks.

Two rules keep this honest:

- **Partial is a first-class result, never a failure claim and never a
  completion claim.** The skill must not report success for the finished
  fragment nor discard it as a failure. A separate `status` field carrying
  `partial` prevents both readings collapsing into one.
- **Resumability is stated, not implied.** If the next action requires state
  that was not written down, the run is not resumable and the receipt says so.
  The remainder must be reconstructible from the receipt alone by a fresh
  session with no memory of this one.

A concrete receipt shape the skill can emit verbatim:

```text
status: partial
completed: &lt;enumerated units&gt;
remaining: &lt;enumerated units, or count with the boundary named&gt;
stopped_because: budget-exhausted | authority-required | input-missing | upstream-unavailable | interrupted
next_action: &lt;one named action&gt;
next_action_needs: &lt;authority, input, or confirmation required&gt;
resume_from: &lt;durable state, or "not resumable: &lt;what was lost&gt;"&gt;
```

## Activation boundary

Should activate:

- "Run this over the whole backlog and tell me where you got to."
- "Do as much of this as you can in one pass."
- "Continue from where the last run stopped."

Should not activate:

- "Finish all of it" as a demand for completeness — that is a scope negotiation,
  not a partial-result presentation, and the skill should not silently absorb it.
- A run that failed outright with nothing completed — that is an error path, not
  a partial result.
- Progress narration during a run. This skill governs the terminal report; a
  streaming progress indicator is a different concern.

## Observable outcome

A reader who sees only the final message can name what was done, what was not,
why, and the one thing to do next — and a fresh session can act on it without
re-deriving state.

## Boundaries

- Read and write are confined to the run's already-approved root; a partial
  result never widens it to reach the remainder.
- Stopping does not authorize cleanup. A partially written artifact is retained
  and named in the receipt, not deleted to make the result look tidy.
- The next action is proposed, never self-executed. `authority-required` in
  particular ends the run.
- No network, credential, or external-side-effect authority is implied by
  resumption.

## Evidence to hold

- Success: the fragment completed is correct on its own terms.
- Partial: the receipt's `remaining` plus `completed` accounts for the whole
  input, with no unit dropped or double-counted.
- Interruption: a run cut off mid-unit reports that unit as remaining, not
  completed.
- Clean degradation: no durable state to resume from still yields a receipt
  saying so explicitly, rather than a plausible-looking `resume_from`.

## Proposed name and file tree

`report-partial-result`

```text
report-partial-result/
  SKILL.md                       # trigger, the three-part contract, the receipt block
  references/stop-reasons.md     # closed vocabulary, one paragraph each, when to pick which
  references/resumability.md     # what must be durable for a fresh session to continue
```

The stop-reason vocabulary and the resumability rules are conditional detail —
needed only when a run actually stops short — so they belong in references, not
in `SKILL.md`.

## Non-goals

- Deciding how much work to attempt, or setting a budget.
- Retrying, resuming, or executing the next action.
- Progress narration during the run.
- Estimating time or effort remaining.
- Cleanup or rollback of partial artifacts.

## To resolve before this becomes a file

Name the skill's actual domain and its dominant truncation cause. That
determines whether the stop-reason vocabulary above is right, and whether
`resume_from` is a cursor, a diff, or a re-derivable query.

Files changed: none. Checks run: none — read-only framing, no candidate file was
resolved or read. Retained behavior: not applicable, no existing skill targeted.
Unavailable capabilities: none encountered. Cleanup: none required.

Agreement with this frame does not authorize a write.
