# Spec: jsonl-otlp-exporter-resume

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0115](../../adr/0115-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the public surface is two CLI flags and one stdout line, specified inline below
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.
>
> **This contract is capability-scoped.** No criterion below may name a specific
> consumer, product, repository or catalogue, for the reason
> [`../jsonl-otlp-exporter/spec.md`](../jsonl-otlp-exporter/spec.md) records: the
> distribution is published, and a public package whose contract names its first
> consumer forces the second consumer to amend a shipped criterion rather than
> add a file.

## Objective

A caller that runs `jsonl-otlp-export` repeatedly against a growing JSONL file
sends each record once rather than re-sending the whole history on every run.

The position is the caller's to keep. A run reads from a **cursor** the caller
supplies and prints the cursor the next run should start from; whoever invokes
the sender stores that value between runs. This is the external-offset-store
shape: the sender stays a generic JSONL-to-OTLP command that writes no durable
state of its own, and the lifecycle of the stored position belongs to the
process that owns the lifecycle of the input file.

The cursor is opaque to the caller. It is a JSON object pairing the byte offset
with the input file's device and inode numbers, because a byte offset alone is
valid only for one file identity — carried across a rotation it lands in the
middle of an unrelated record. The caller stores the object and hands it back
without reading inside it, so a later field costs no interface change.

Criterion identifiers here are local to this spec. The parent spec
[`../jsonl-otlp-exporter/spec.md`](../jsonl-otlp-exporter/spec.md) has its own
`AC-0001`, and the two sets do not share a namespace.

What the sender can check about a supplied cursor is its shape, its file
identity, and that its offset falls on a record boundary. What it cannot check is
whether that boundary is the *right* one: a cursor pointing at a valid boundary
further into the file makes the run skip the records in between, and no property
of the file distinguishes that from a correct resume. Choosing which cursor to
hand back is the caller's responsibility, and it is the reason the cursor is
opaque — a caller that never opens it has nothing to get wrong.

Two behaviours a reader will look for and not find, because they are deliberate:
a run under bare `--follow` never ends, so it prints no cursor; and a run that
prints no cursor leaves the caller holding the cursor it already had, which
re-sends the records in between. That is the correct outcome under the parent
contract's at-least-once delivery, which pairs with the dedup attribute set of
its AC-0023.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — two new flags on a published CLI | `packages/jsonl-otlp-exporter/README-pypi.md` | spec owner | The resume contract, the two flags, and the caller's obligation to store the cursor are documented | AC-0021 green; renders on PyPI |
| Release history | Applicable — a published distribution gains public surface | `packages/jsonl-otlp-exporter/CHANGELOG.md` | release workflow | Both flags named under the existing unreleased `## 0.1.0` entry, with no version bump: 0.1.0 has not shipped, so this surface is part of the first release rather than an addition to a released one | Tag matches `pyproject.toml` |
| Interface compatibility | Applicable — the cursor is a stored value read by a later version | `packages/jsonl-otlp-exporter/README-pypi.md` | spec owner | The cursor's `v` field and what a version other than 1 means are stated | AC-0021 green |
| Decision rationale | Applicable — reset policy, `partialSuccess` disposition and the concurrency boundary are owner decisions a later reader will otherwise re-litigate | `docs/specs/jsonl-otlp-exporter-resume/notes/decisions.md` | spec owner | Each decision recorded with the alternative it beat | File present and each decision names its rejected alternative |
| Current architecture | Not applicable — no module boundary, dependency or data flow changes; the reader gains a start offset and the sender gains a return value | — | — | — | — |
| Maintainer procedure | Not applicable — the package's test and release commands are unchanged | — | — | — | — |

## Boundaries

### Always do

- Read the input file and nothing else. The cursor arrives as an argument and
  leaves on stdout.
- Pair a byte offset with the device and inode numbers of the descriptor the run
  actually read, never with the pathname it was given.
- On an identity change or a shrink below the offset, read from byte 0 and say so
  on stderr.
- Advance the reported offset only past records the run either had accepted or
  deliberately declined to send.
- Treat a `--from-cursor` argument as untrusted: bound its length before parsing
  it, refuse anything that is not the exact object shape, and prove its offset
  lands on a record boundary before seeking to it.

### Ask first

- Reporting the cursor on stdout unconditionally rather than under a flag.
- Advancing the offset past records a receiver rejected through
  `partialSuccess`.
- Any coordination between concurrent callers sharing one stored cursor.
- Resetting to the end of the file rather than to byte 0 on a rotation.

### Never do

- Write a checkpoint, position file, lock file, or any other durable state. The
  parent contract forbids it and resume does not earn an exception.
- Write to, truncate, replace or otherwise modify the input file.
- Begin reading part-way through a record.
- Exit 0 for a run that read lines and found none valid, or for one that reset
  to byte 0 and found none. The carve-out in AC-0033 is for a run that read no
  line at all because its cursor was already at the end.
- Silently restart from byte 0 for a cursor that is merely malformed, or for one
  whose identity matches but whose offset is misaligned. Byte 0 is the answer to
  a rotation, not to a bad argument.
- Import or require `agentbundle`, or any other runtime dependency.

## Testing Strategy

**TDD stub dispositions.** Five plan tasks are TDD: T1, T2, T3, T4 and T5. All
five carry validated stubs, because every module they assert against already
exists and ships — which is the one material difference from the parent plan,
whose zero-stub count followed from the package not existing at plan approval.
T6 carries `no stub (goal-based)` naming its mode and the reason.

Across the 33 criteria: **32** are covered by a validated stub (VI-0001 through
VI-0006, VI-0008 and VI-0009); **1** is goal-based and takes no stub (VI-0007). Every criterion
appears in exactly one group.

- **VI-0001 — the cursor's shape and its channel (AC-0001, AC-0022, AC-0002,
  AC-0003):** TDD. Each is one invocation and one observed stream. AC-0001 is
  asserted only on a run that opened its input and ran to completion, because
  that is the run it now describes. AC-0003 takes
  its own case driven by a fixture that replaces the path after the open, because
  a build that stats the pathname to fill the cursor passes AC-0022 and reports an
  identity for a file it never read.
- **VI-0002 — what the offset means (AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0009, AC-0010):** TDD over a seam in front of the transport, so each
  response shape is a fixture. These six are a single decision procedure and are
  asserted as one: AC-0004 and AC-0005 have mutually exclusive antecedents, and
  AC-0006 is the base case AC-0005 leaves undefined when no batch was accepted.
  AC-0005 is the criterion the feature turns on and is asserted with an accepted
  batch *following* a refused one, which is the case that separates "the last
  accepted batch" from "the longest accepted prefix" — a build that tracks a
  high-water mark passes every single-failure case and loses the records between.
  AC-0004's enumerated set is asserted member by member, including the
  over-ceiling record, which is driven by lowering the ceiling rather than by
  constructing an 8 MiB fixture. AC-0010 takes a second fixture whose final line is
  both unterminated and over the line-length ceiling, because the reader discards
  an over-length line's bytes as it reads them and an accounting that advances on
  that discard reports a position inside the line; a short partial line never
  reaches that path. AC-0009 is asserted over the offset reported by
  every case in this group rather than by its own fixture: it is the invariant
  that makes a resumed read safe, so sampling it once would leave the other cases
  free to violate it.
- **VI-0003 — resuming, the boundary check, and the two resets (AC-0011,
  AC-0030, AC-0012, AC-0023, AC-0013, AC-0024, AC-0014):** TDD. AC-0030's
  fixture supplies a matching identity and an offset one byte inside a record,
  and asserts a refusal rather than a reset — a build that folds the misaligned
  case into AC-0012's reset passes every other case here and silently re-sends
  the whole file. Each reset splits its read behaviour from its
  diagnostic, because a build that computes the reset and then ignores it fails
  only the first, and a build that resets silently fails only the second. AC-0012
  is asserted at the command, not only at the function that computes it: its
  fixture replaces the input with a new inode carrying different records and
  asserts the records of the *new* file are sent, which is what proves the
  computed zero reaches the reader. AC-0014 pins that an invocation omitting the
  flag is unchanged, and is the only check that a caller upgrading the package
  sees no new behaviour.
- **VI-0004 — refusing a bad cursor (AC-0015, AC-0016, AC-0025, AC-0026,
  AC-0028):** TDD, five criteria. Every parse case is a string argument, so it runs
  with no file and no network. AC-0015 is asserted on the *reason* for the
  refusal, using an argument that is over the byte bound and otherwise
  conforming — an integer `offset` of several thousand digits — because a fixture
  padded with an extra member is refused on shape by a build that never checks
  length at all. AC-0025 asserts the transport seam is never constructed, which
  separates refusing before sending from refusing after. AC-0026 is
  asserted at both endpoint states, because the parent contract's AC-0033 carve-out
  is what makes one status correct for both and a build that honours the
  unqualified reading returns 0 for the unconfigured one.
- **VI-0005 — bounds, completeness, and the absent write surface (AC-0017,
  AC-0029, AC-0032, AC-0018, AC-0031):** TDD. AC-0032 is asserted by appending
  records to a file already sent, resuming from the reported cursor, and
  requiring exactly the appended records on the wire — the positive assertion the
  contract lacked. The round-trip case over an *unchanged* file asserts only that
  nothing is re-sent, which a build that sends nothing at all also satisfies. Its
  three exclusions are not re-asserted here: AC-0010 and AC-0004 already own
  them, and a second case over the same fixtures would pin one behaviour in two
  places. AC-0031 walks the distribution's syntax tree, so it fails on a
  write surface that exists but was not exercised, which AC-0018 cannot see. AC-0017 and AC-0029 are both asserted against a writer
  appending during the run rather than by reading the budget arithmetic, because
  the arithmetic is what is suspected: the bound exists so one-shot terminates,
  and an off-by-one that leaves the budget open is invisible to a static read.
  They are separate criteria because the reset path computes its ceiling from a
  different starting offset, and a build that subtracts the cursor's offset
  unconditionally passes AC-0017 and hangs on AC-0029. AC-0018 captures its
  baseline before the first run of the sequence, not between runs, because a
  checkpoint written by the first run would otherwise be inside the baseline.
- **VI-0006 — stdout stays empty when nothing was read (AC-0019, AC-0020):**
  TDD. Each state is one invocation and one observed stream. AC-0020 raises
  `KeyboardInterrupt` from inside the send loop, which is where SIGINT arrives,
  and asserts stdout is empty — the assertion is about a stream, so it does not
  need a real signal to be faithful. AC-0019 is asserted for each of its six exit
  reasons rather than sampled, because the reasons return from six different
  points and a build that prints the cursor at one of them passes a sampled
  check. Every case passes `--report-cursor`, since without it AC-0002 already
  requires an empty stdout and the case would prove nothing.
- **VI-0008 — a resumed run with nothing new (AC-0033, AC-0034):** TDD, added
  by the amendment recorded in the verification ledger. Asserted as a round trip
  through the assembled command — send, take the reported cursor, resume against
  the unchanged file — because that is the sequence a repeated caller performs
  and the only one in which the condition arises. The pair is asserted
  separately from the exit status a run over an all-invalid input returns, which
  must stay 1: a build that widens the carve-out to any empty send passes
  AC-0033 and silently converts a genuine failure into success.
- **VI-0009 — which runs report a cursor (AC-0035, and AC-0001's exit-1 half):**
  TDD, added by the second amendment. Both halves of AC-0001 are asserted, not
  just the passing one: a run that read lines and emitted no record exits 1 and
  must still print its cursor, and a run refused on the boundary check must print
  nothing. A suite that only ever checks the exit-0 path admits a build that
  prints the cursor on success alone, which is the shape review found.
- **VI-0007 — the published contract (AC-0021):** goal-based check over the
  authored file. Presence and structure are mechanical; wording is not asserted.

## Acceptance Criteria

A batch is **accepted** when the receiver answered a 2xx status and the response
carried no non-empty `partialSuccess`. A batch is **issued** when a request
carrying it was sent at all; the run's time bounds can stop a batch the reader
produced from ever being issued.

- [x] **AC-0001.** Under `--report-cursor`, a run that reached its send loop
  writes exactly one line to stdout, whether it then exits 0 or 1. Reaching the
  send loop is the condition, not the exit status: a run refused on its cursor
  after the input was opened has read nothing and has no offset it can honestly
  report, and AC-0035 owns that case. An exit status of 1 does not by itself
  excuse the line — a run that read lines and emitted no record still reports
  where it got to.
- [x] **AC-0035.** Under `--report-cursor`, a run refused on its `--from-cursor`
  after the input file was opened — the AC-0030 boundary refusal, the only
  refusal that needs the descriptor — writes no byte to stdout. There is no
  cursor it could print: the supplied offset is the one being refused, and byte 0
  would instruct the caller to re-send the whole file.
- [x] **AC-0022.** That line parses as a JSON object whose members are `"v"`
  equal to the integer 1, `"offset"` an integer, `"device"` an integer, and
  `"inode"` an integer, and no other member.
- [x] **AC-0002.** With `--report-cursor` absent, the command writes no byte to
  stdout.
- [x] **AC-0003.** A reported `device` and `inode` equal the device and inode
  numbers of the file the run's input descriptor referred to. Replacing the
  pathname with a different file after the open does not change them.

- [x] **AC-0004.** In a run where every batch the reader produced was issued and
  accepted, the reported `offset` is the reader's consumed position at the moment
  the run stopped pulling records. That position is past every line the reader
  consumed which no batch covered: a line skipped for exceeding the line-length
  ceiling, for not parsing as JSON, for a top-level value that is not an object,
  or for a timestamp the active profile does not admit, and a record declined
  because its encoded form alone exceeds the request-body ceiling.
- [x] **AC-0005.** In a run where any batch the reader produced was not both
  issued and accepted, the reported `offset` is the position immediately after
  the terminating newline of the last line of the last batch in the unbroken
  sequence of accepted batches beginning at the run's first batch.
- [x] **AC-0006.** In a run whose first batch was issued and not accepted, or was
  produced and never issued, the reported `offset` equals the offset the run
  began reading from. This is the case AC-0005 leaves undefined, because its
  unbroken sequence of accepted batches is empty.
- [x] **AC-0007.** A response carrying a non-empty `partialSuccess` is not an
  acceptance: the reported `offset` stops before the first byte of the first line
  of the batch that response answered.
- [x] **AC-0009.** Every reported `offset` is either the offset the run began
  reading from, or a position whose immediately preceding byte in the input file
  is a newline.
- [x] **AC-0010.** A final line carrying no terminating newline is not consumed,
  and the reported `offset` is no greater than the byte position of that line's
  first byte.

A supplied cursor takes exactly one of four routes, and the four criteria below
carry mutually exclusive preconditions rather than a precedence rule, so no run
matches two. An identity that differs is a rotation and resets, whatever its offset says —
the offset describes a file that is no longer there, so comparing it to the new
file's size would be meaningless. The other three routes all require a matching
identity: an offset past the file's end is a truncation and resets; an in-range
offset that does not sit on a record boundary is a corrupt or forged cursor and
is refused; anything left is honoured.

- [x] **AC-0011.** Given a `--from-cursor` whose `device` and `inode` equal the
  opened input file's, whose `offset` is not greater than that file's size at
  open, and whose `offset` is either 0 or a position whose immediately preceding
  byte in that file is a newline, the run's first read of the input begins at
  that `offset`, and no record lying wholly before it is sent.
- [x] **AC-0012.** Given a `--from-cursor` whose `device` or `inode` differs from
  the opened input file's, the run reads from byte 0.
- [x] **AC-0023.** Given a `--from-cursor` whose `device` or `inode` differs from
  the opened input file's, the run writes a line to stderr naming that the
  input's identity changed and the offset was reset.
- [x] **AC-0013.** Given a `--from-cursor` whose `device` and `inode` equal the
  opened input file's and whose `offset` is greater than that file's size at
  open, the run reads from byte 0.
- [x] **AC-0024.** Given a `--from-cursor` whose `device` and `inode` equal the
  opened input file's and whose `offset` is greater than that file's size at
  open, the run writes a line to stderr naming that the input shrank below the
  offset and the offset was reset.
- [x] **AC-0030.** Given a `--from-cursor` whose `device` and `inode` equal the
  opened input file's, whose `offset` is not greater than that file's size at
  open, and whose `offset` is neither 0 nor a position whose immediately
  preceding byte in that file is a newline, the run is refused: it sends nothing
  and exits 1. The preceding byte is read from the descriptor
  `--input` was opened on, never by reopening the path. This is a refusal and not
  a reset to byte 0, because a matching identity with a misaligned offset is a
  corrupted or forged cursor rather than the rotation AC-0012 describes.
- [x] **AC-0014.** With no `--from-cursor`, the run reads from byte 0.

- [x] **AC-0015.** A `--from-cursor` argument whose UTF-8 encoding exceeds 4096
  bytes is refused on that length, before it is parsed as JSON. This is the bound
  that fires first because it is measured on the raw argument before any parse:
  the object AC-0022 defines carries four integers and never approaches 4096
  bytes, so no value a conforming caller stores reaches it.
- [x] **AC-0016.** A `--from-cursor` argument within AC-0015's bound is refused
  when it does not parse as JSON, is not a JSON object, is an object whose member
  names differ from AC-0022's set, carries a `v` other than the integer 1,
  carries an `offset`, `device` or `inode` that is not a JSON integer, carries
  a negative `offset`, or raises any exception while being decoded.
- [x] **AC-0025.** A run whose `--from-cursor` was refused sends nothing.
- [x] **AC-0026.** A run whose `--from-cursor` was refused exits 1, whether or
  not an endpoint resolves.
- [x] **AC-0028.** A run whose `--from-cursor` was refused writes a line to
  stderr naming the refusal, whether or not an endpoint resolves.

- [x] **AC-0017.** Resumed from a cursor honoured under AC-0011 at offset N, with
  no mode flag, against an input file whose size at open is S, the run reads at
  most S − N bytes from the input and exits without waiting for further lines,
  including while a writer appends to that file throughout the run.
- [x] **AC-0029.** Resumed from a cursor that AC-0012 or AC-0013 reset, with no
  mode flag, against an input file whose size at open is S, the run reads at most
  S bytes from the input and exits without waiting for further lines, including
  while a writer appends to that file throughout the run.
- [x] **AC-0032.** In a run with no mode flag where every batch was accepted,
  every newline-terminated line lying wholly between the offset the run began
  reading from and the input file's size at open is sent, unless it yields no
  record the active profile admits or its encoded form alone exceeds the
  request-body ceiling. This is the completeness half of AC-0017 and AC-0029:
  those two bound only how *much* is read, so a run that reads nothing and exits
  satisfies both while losing every pending record. The three exclusions are the
  cases other criteria deliberately do not send — AC-0010 forbids consuming an
  unterminated final line, and AC-0004's enumerated set names the skipped line
  and the over-ceiling record.

- [x] **AC-0018.** Across every run of a resume sequence given both
  `--from-cursor` and `--report-cursor`, the set of regular files under `--root`,
  and each one's content and modification time, is unchanged from before the
  first run of that sequence.

- [x] **AC-0031.** No module in the distribution opens a path for writing,
  creates or removes a path, or takes a file lock. Asserted by parsing every
  `.py` file at or below the package directory and requiring all four of:

  1. No call named `open` other than `os.open` carries a mode containing `w`,
     `a`, `x` or `+`, whether that mode is passed positionally or as `mode=`. A
     mode that is not a literal is itself a failure: the distribution has no
     reason to compute one, and admitting it would let `"w" + "b"` through.
  2. No call to `os.open` names `O_WRONLY`, `O_RDWR`, `O_CREAT`, `O_APPEND` or
     `O_TRUNC` in its flags. `os.open` is excluded from the rule above because
     its second argument is flags, not a mode, and reading it as one reports
     every read-only open in this package as a failure.
  3. No identifier from this closed set is called: `write_text`, `write_bytes`,
     `mkdir`, `makedirs`, `touch`, `mkstemp`, `mkdtemp`, `NamedTemporaryFile`,
     `TemporaryFile`, `TemporaryDirectory`, `lockf`, `flock`, `locking`. Nor is
     any of `write`, `writelines`, `pwrite`, `rename`, `replace`, `remove`,
     `unlink`, `rmdir`, `truncate`, `ftruncate`, `symlink`, `link`, `chmod`,
     `dup2`, `copy`, `copyfile`, `copytree`, `move` called on an attribute chain
     whose root name is `os`, `shutil`, `tempfile`, `pathlib` or `Path`. The
     root is resolved through calls and subscripts, so `Path(p).replace(q)`
     roots at `Path` and is caught while `text.replace(a, b)` roots at `text` and
     is not.
  4. The distribution imports none of `fcntl`, `msvcrt`, `shutil`, `tempfile`,
     `sqlite3`, `dbm` or `shelve`.

The second list is root-qualified and the first is not, which is where the
  check stops: `str.replace` and a stream's `.write` are ordinary, and a syntax
  tree cannot tell them from `os.replace` and `os.write` without inferring the
  receiver's type, so a write reached through a local name bound to a writable
  object is not caught. Neither is one reached through an alias, a dynamic
  attribute lookup, or a C extension. AC-0018 is the other half, and each sees
  what the other cannot.

- [x] **AC-0019.** A run that exits before opening its input file writes no byte
  to stdout, whether it exited because no endpoint is configured, because its
  `--from-cursor` was refused, or because its configuration, profile, input path
  or endpoint was refused.
- [x] **AC-0020.** A run interrupted by SIGINT writes no byte to stdout.

- [x] **AC-0033.** A run with no mode flag that began reading from a non-zero
  offset honoured under AC-0011 and consumed no line exits 0. The parent
  contract's AC-0039 exits 1 when no line yields a valid record, and its
  predicate cannot separate *every line was invalid* from *there was no line*.
  Before resume those were nearly the same condition; with a cursor at the end
  of the input they are opposites, and the second is the normal state of a
  repeated run.
- [x] **AC-0034.** That run writes a line to stderr naming that no record lay
  past the cursor. It is a distinct criterion from AC-0033 because a build that
  returns the right status while still reporting invalid lines misleads the
  operator about what happened, and a build that reports correctly while exiting
  1 breaks the caller; the two fail independently.

- [x] **AC-0021.** `README-pypi.md` contains a level-2 heading `## Resuming a
  run`, and the section under it contains each of the literal strings
  `--from-cursor`, `--report-cursor`, `the caller stores the cursor`, and
  `at-least-once`.

## Retired identifiers

<!-- Identity is append-only: a retired identifier is never reused. Entries are
     bare identifiers; the narrative belongs above, not on the entry line. -->

AC-0008 was retired 2026-09-15 during pre-EXECUTE review. It required the
reported offset to advance past a record declined for exceeding the request-body
ceiling, and it stated that unconditionally — so for a run whose first batch was
refused and whose last record was over the ceiling, it demanded an advance while
AC-0005 and AC-0006 demanded the starting offset. The obligation is not missing:
it is a member of AC-0004's enumerated set, which scopes it to the runs where
advancing is safe. Retired rather than reworded because an offset rule that
holds only on a clean run belongs inside the clean-run criterion.

AC-0027 was retired 2026-09-15 during pre-EXECUTE review. It split the refused
cursor's exit status by endpoint state, exiting 0 when no endpoint resolved, in
order to honour the parent contract's AC-0033 as it was then worded. The owner
instead amended AC-0033, which is where the defect was: the unqualified
criterion also forbade the `--config` and `--profile` refusals the package
shipped with in #1293. With that carve-out in place a refused argument exits 1
at both endpoint states, so AC-0026 alone decides it and a second criterion
would only encode the contradiction.

- AC-0008
- AC-0027

## Follow-ons

- spec owner: [`../jsonl-otlp-exporter/spec.md`](../jsonl-otlp-exporter/spec.md)
  — that spec sits at `Approved` with 72 of 72 criteria unticked although the
  package shipped in #1293, and nothing registers it in `workspace.toml`, so
  nothing pins that status. Verifying and closing it is separate work and is
  deliberately not folded in here: ticking 72 criteria this change did not
  verify would be the exact defect the criteria exist to prevent.

- spec owner: `packs/core` `SessionEnd`/`SessionStart` hook pair — the consumer
  that stores the cursor between runs and invokes the sender automatically. It
  depends on this spec; this spec does not depend on it, and per the
  capability-scoped rule no criterion above names it.

- spec owner: the stub validator described in
  [`plan.md`](plan.md)'s `## Stub validation` is a session script, not a
  repository tool. It found four defects across two rounds that prose review had
  not, so it is worth promoting to `tools/` — which obliges a test beside it per
  [`packages/AGENTS.md`](../../../packages/AGENTS.md)'s test-home table, and that
  is why it is not promoted here.

- spec owner: under `--follow` and `--for`, neither completeness nor the
  nothing-new exit status is stated. AC-0032 and AC-0033 both cover one-shot
  only, and the parent contract's AC-0039 exception is scoped to match them, so
  a bounded follow run that finds nothing new still exits 1. That is the same
  wart AC-0033 removes from the one-shot path, left in place deliberately: the
  fix needs a duration floor this spec has no basis for choosing, and widening
  the exception without one would make a `--for 0` run that legitimately sends
  nothing indistinguishable from a real failure. AC-0032
  covers one-shot only. A time-bounded run's completeness cannot be stated
  without a duration this spec has no basis for choosing: `--for 0` legitimately
  sends nothing, and any positive floor would be a number invented to satisfy the
  criterion rather than derived from anything. So a mode-flagged run that sends
  nothing and reports its starting offset is not forbidden here. It is also not
  silent — the reported cursor still obeys AC-0004 and AC-0005, so the caller
  resumes from where the run actually got to and loses no records, only time.

- spec owner: a poison batch stalls the cursor. A batch the receiver keeps
  refusing through `partialSuccess` is never accepted, so AC-0007 holds the
  offset before it on every subsequent run and the accepted prefix in front of
  it is re-sent each time. Exit 1 and the parent contract's rejected-record count
  on stderr are the signal; the operator's remedy is to advance the stored offset
  by hand. Automatic skip-past-poison is deliberately out of scope, because a
  sender that advances past records it could not deliver loses them with no
  record that they were lost.

- spec owner: concurrent callers double-send. Two processes resuming from one
  stored cursor both read the same range and both send it. This is the caller's
  to prevent: the sender owns no state, so it can hold no lock, and a lock file
  is precisely the durable write surface the design excludes. At-least-once
  delivery and the dedup attribute set of the parent contract's AC-0023 already
  make the duplicate tolerable.

## Assumptions

- Technical: pairing a byte offset with the inode and resetting on an `st_ino`
  change or `st_size < offset` is precedented in this repository for this exact
  problem (source: `packages/agentbundle/agentbundle/workspace_mcp.py:447-450`,
  read 2026-09-15). This spec adds `st_dev` to that pairing because the exporter
  already holds a validated descriptor, so one `fstat` yields both numbers.
- Technical: the sender's one-shot pass is bounded at the size the descriptor
  had when it was opened, and that bound is what makes the parent contract's
  AC-0020 true against a fast writer (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/source.py:217-220`, read
  2026-09-15). AC-0017 exists because that arithmetic has to change.
- Technical: the command writes every diagnostic to stderr and nothing to
  stdout today (source: `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/`,
  every `print` call passes `file=stream`, read 2026-09-15). This is why the
  cursor can take stdout as a clean machine channel.
- Technical: the parent contract's `### Exit codes` table already claims exit 1
  for a "usage error, configuration error", so a refused cursor needs no new row
  (source: `../jsonl-otlp-exporter/spec.md:61`, read 2026-09-15). Its AC-0033 did
  need amending: as written it required exit 0 with no endpoint resolvable
  unconditionally, which `cli.py` has contradicted for `--config` and
  `--profile` since #1293 (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py:75-81`, read
  2026-09-15). The carve-out is recorded on AC-0033 itself and in
  `notes/decisions.md` § 6.
- Process: `lint-spec-status.py` invariant (ii) requires every criterion to be
  `[x]` when a spec's header status changes to `Shipped` in the diff against the
  base ref (source: `.claude/skills/work-loop/scripts/lint-spec-status.py:27-32`,
  read 2026-09-15). This is why resume is a sibling spec rather than an
  amendment to a spec carrying 72 unticked criteria.
- Product: the cursor is reported under a flag rather than unconditionally,
  because an unconditional stdout line is a behaviour change to an already
  published CLI and is not reversible once shipped (source: owner decision
  2026-09-15, recorded in `notes/decisions.md`).
- Product: the reset policy is byte 0 rather than end-of-file, because losing
  every record written before the sender next ran is the failure this feature
  exists to prevent, while the duplicate a reset risks is already declared
  tolerable (source: owner decision 2026-09-15, recorded in
  `notes/decisions.md`).
