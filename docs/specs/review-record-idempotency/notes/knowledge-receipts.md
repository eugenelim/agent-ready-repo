# Project-knowledge capture receipts

Closes the reusable-learning durable output. Captured at the `plan-locked` gate
against `plan.md`; each observation is `pending` until distillation, which is the
producer's own terminal gate and not this contract's to force.

| Kind | Capture id | Partition |
| --- | --- | --- |
| antipattern | `kco-202609-f31d655370836b28df962261a7c27df23140ea46524a19074774b4e733954524` | `observations/antipattern/2026-09.jsonl` |
| gotcha | `kco-202609-68c2d3cd46ebf3a5936104fe9fc4e908afff51012b8e0be22d449d28d85963fd` | `observations/gotcha/2026-09.jsonl` |
| pattern | `kco-202609-8820a0f123150bb5319e442fce8b2c1a45a547df2d08fbb35d90439c917426ea` | `observations/pattern/2026-09.jsonl` |

## What was captured

- **A test whose window moves with the file can be satisfied by editing the
  file.** A shipped-instruction check keyed on a fixed six-line window was turned
  green by adding two comment lines above the statement, which pushed the
  governing transition out of range. The property went unverified and the change
  was reported as the check earning its place. Key such a check on an enclosing
  structural boundary and assert a non-vacuity floor.
- **Python's `$` and `\d` make an identifier regex fail open.** `$` matches before
  a trailing newline and `\d` accepts Unicode decimal digits, so `x:1`, `x:1\n`
  and `x:01` all pass and compare unequal — three spellings of one identity, each
  recording separately.
- **Moving a guard from shell syntax to prose silently drops it.** A retry cap
  carried only by an `&&` stopped being enforced when the statement was split for
  an unrelated reason.

The capture interface took four attempts: the request is one observation on
stdin, not a list and not `--artifact`, and the caller must omit the five fields
the producer profile fills deterministically.

## The pinned anchor is older than the file it names

All three observations carry the same source anchor: `plan.md` at
`f8d8b8e3…`, 27303 bytes. That is the plan as it stood at `plan-locked`. One
commit has touched `plan.md` since — `219e92290`, which renumbered task anchors
after a task was removed and rewrote the *Open findings* section — so `plan.md`
is now `5de9c046…`, 26729 bytes. Anyone resolving the anchor against the working
tree gets a mismatch.

This is recorded rather than re-captured, deliberately. The anchor's job is to
say which text the observation was drawn from, and each of the three
observations still describes what was true of that text; re-pointing them at the
current file would assert they were learned from a plan that did not exist yet.
The observations are `pending`, so distillation resolves the anchor through git
history: `git show ecb19736:docs/specs/review-record-idempotency/plan.md` is the
27303-byte text that hashes to `f8d8b8e3…`.
