# Close-time work-item branch

Load when a DECIDE-pass scratch note names a defect and the [Capture](../SKILL.md#capture)
table routes it past the `project-knowledge` route. `SKILL.md` owns the
routing table itself; this file owns what each of its other rows requires.

## Blocked

A defect is blocked when it cannot be finished this session for one of four
reasons: it needs a **decision** nobody present can make, an **instrument**
not available in this session, **elapsed time** (a deploy, a wait on an
external actor), or a **dependency** on other work that has not landed. Any
other reason is not blocked — it is either ready now or it fails the razor.

## What a work-item capture must carry

Every captured item states, in plain language:

- **The statement** — the item in one line.
- **Its shape** — a `defect` (a specific wrong behavior in a named artifact),
  a `question` (an unresolved question whose deliverable is an answer), or a
  `decision` (a question whose deliverable is a durable decision record).
- **Its blocker** — one of the four named above.
- **The finished state** — what done looks like. A location without this is
  a locator, not an item; it is not ready to capture.
- **The necessity rationale** — what was considered and rejected as
  sufficient instead of capturing this.

A `defect` also states how to reproduce it, or what was observed and what was
intended. A `question` names who or what can answer it. A `decision` names at
least one reason it needs a durable record rather than an in-session call:
that it is architecturally significant, expensive to reverse, or constrains
work beyond the one that raised it.

## The razor

Before capturing, ask the same question this repository already asks before
adding anything: does an existing artifact already cover this? An item an
existing artifact already covers, or one that supplies no discriminator, no
finished state, and no rationale, is not necessary work — it fails the razor
and is refused rather than captured.

## Refused, non-silently

A refusal is never a silent drop. The author is told which item was refused
and why, in one line naming the defect: it is not written, and it is not
retried automatically. Correct the item and re-submit it once; a second
refusal of the same item stands for the rest of the close.
