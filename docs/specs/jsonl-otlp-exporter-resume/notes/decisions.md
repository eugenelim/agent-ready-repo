# Resume: the owner decisions

Each entry names the alternative it beat, so a later reader does not re-open a
settled question. Decided 2026-09-15 by the spec owner. Decision 6 was added
during pre-EXECUTE review, when a reviewer found the collision it settles.

## 1. The cursor pairs the offset with a device and inode, and is opaque

A byte offset is valid for exactly one file identity. Carried across a rotation
it lands at an arbitrary byte of an unrelated file, which is a record boundary
only by luck.

`packages/agentbundle/agentbundle/workspace_mcp.py:447-450` already solves this
for the same problem shape — it pairs its offset with `st_ino` and resets when
`st_ino` changes or `st_size < offset`. That shape is reused rather than
reinvented.

`st_dev` is added to the pairing. Inode numbers are unique per filesystem, not
per machine, and a path that moves between filesystems can present a colliding
inode. The exporter already holds a validated descriptor by the time it needs
these numbers, so one `os.fstat` yields both and the stronger identity is free.

**Rejected: a bare integer offset.** It cannot express identity, so the caller
would have to store and compare the identity itself — which is the caller
learning the sender's internals.

**Rejected: a transparent `--from-offset N --from-inode I` flag pair.** It
publishes the pairing as interface, so adding a third component later is a
breaking change. The opaque object absorbs a new field silently.

## 2. Reset policy is earliest — byte 0

On an identity change or a shrink below the offset, the run reads from byte 0.
This is `auto.offset.reset=earliest`, and it matches the bridge cited above.

The objection is that earliest means an exporter re-sends history after a
rotation. It does not, and the reason is worth stating because it is the whole
basis of the decision: after a rotation, byte 0 is the start of the *new* file,
and the old history is no longer at that path at all. After a truncate-in-place,
the bytes at 0 are likewise new content. Neither case re-reads the old records.

The cost is real only for a writer that truncates and then rewrites records it
had already written. That produces duplicates, and the parent contract already
declares delivery at-least-once with a dedup attribute set (its VI-0009 /
AC-0023), so a consumer has the means to drop them.

**Rejected: latest — reset to the current end of file.** It silently drops every
record written between the rotation and the sender's next run. Losing telemetry
without saying so is the failure this feature exists to prevent, and it trades a
tolerable duplicate for an untraceable gap.

## 3. A non-empty `partialSuccess` is not an acceptance

One offset cannot express "records 3 and 7 of this batch were rejected". So the
batch is treated as unaccepted: the reported offset stops before its first line,
and the run exits 1 as the parent contract's AC-0054 already requires.

The consequence is stated in the spec's Follow-ons rather than left to be
discovered: a batch the receiver keeps refusing on content is never accepted, so
the offset never passes it and every later run re-sends the accepted prefix in
front of it. Exit 1 plus the rejected-record count on stderr (parent AC-0036) is
the signal, and the operator's remedy is to advance the stored offset by hand.

**Rejected: advance past the batch.** It loses the rejected records, and loses
them with no durable record that they were lost — the offset that moved past
them is indistinguishable from an offset that moved past accepted records. A
visible stall is recoverable; silent data loss is not.

## 4. Concurrency is the caller's problem

Two processes resuming from one stored cursor read the same range and both send
it.

The sender owns no state, so there is nothing for it to lock. Adding a lock file
would create exactly the durable write surface this design exists to avoid, and
it would also be the wrong place: the contention is over the caller's stored
cursor, which the sender never sees between runs.

At-least-once delivery plus the parent contract's dedup attribute set already
make the duplicate tolerable, so the cost of not solving this is bounded.

**Rejected: an advisory lock on the input file.** The sender must not modify the
input (parent AC-0061), and a lock on the input constrains the *producer* — the
process appending records — which is not the process being coordinated.

## 5. The cursor is reported under a flag, not unconditionally

`--report-cursor` prints one JSON line to stdout. Without it, stdout stays
empty.

Today the command writes every diagnostic to stderr and nothing to stdout, which
is what makes stdout a clean machine channel for this value. The temptation was
to use it unconditionally and save the caller a flag.

**Rejected: print the cursor unconditionally.** It is a behaviour change to an
already published CLI, it reaches any existing consumer that redirects stdout,
and it cannot be taken back once shipped. A flag costs one argument and can
become unconditional in a later version; the reverse is not available.

## 6. A refused cursor exits 1 at both endpoint states, and the parent's AC-0033 was amended

A malformed `--from-cursor` with no endpoint configured collided with the parent
contract's AC-0033, which read simply "With no endpoint resolvable from any
source, the command exits 0."

The collision was not this feature's. `cli.py` reads `--config` while resolving
the endpoint and validates a supplied `--profile` before the endpoint check, so
a refused `--config` or `--profile` has exited 1 with no endpoint configured
since the package shipped in #1293. The unqualified criterion forbade that.

So AC-0033 carries a carve-out naming all three arguments, and a refused cursor
exits 1 at both endpoint states. Off-by-default is untouched: a refused argument
sends nothing, and AC-0033 was only ever about the exit status.

**Rejected: split the cursor's exit status by endpoint state.** It was drafted as
AC-0027 and retired. Exiting 0 for a broken cursor when no endpoint resolves
honours AC-0033's letter while leaving the `--config` and `--profile` divergence
in place, and it makes a dry run — the documented way to check your arguments
before enabling sending — silently report success for a cursor that cannot work.

**Rejected: leave AC-0033 alone and record the contradiction.** A spec that
knowingly contradicts a binding sibling criterion is a defect a later reviewer
finds again, and the owner's direction was explicit: a spec that got it wrong is
a historical record, not a constraint.
