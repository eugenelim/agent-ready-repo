# Plan: sender-bounds-its-configuration-read

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/transport.py` —
  `_resolve_bounded` is this package's existing answer to a blocking call that
  accepts no timeout: run it on a daemon worker, join with a deadline, abandon
  the worker and raise. Its tests are
  `packages/jsonl-otlp-exporter/tests/unit/test_transport.py`. The second
  analogue is `_Watchdog` in the same module, which bounds an operation the
  caller cannot interrupt by acting on the resource rather than the call — read
  and rejected here, because a descriptor has no equivalent of closing a socket
  out from under a blocked reader on every platform.
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py` is the module
  under change and `packages/jsonl-otlp-exporter/tests/unit/test_config.py` its
  construction path. Named uncertainty: no repository precedent bounds a
  *filesystem* read, only a network one, so the idiom is reused and its
  difference — a worker left blocked holds an open descriptor until the process
  exits — is stated rather than assumed away.

## Approach

Two independent repairs in one module, sequenced so each lands with its own
proof before the next touches the file. The contract amendment comes first,
because both repairs are changes to what the published criteria promise and a
repair landing ahead of its criterion would have nothing to be measured against.

Nothing here adds a public surface, and that is a decision rather than an
observation: the deadline plumbing and the bound's constant are both private, so
the spec's `Ask first` entry on new public surface is not engaged and needs no
sign-off. `read_config_file` keeps its signature, `__all__` keeps its members,
`MAX_CONFIG_BYTES` keeps its value, no `ConfigRefused` message is reworded, and
the run clock keeps its origin. Two refusal messages are added, each for a fact
no existing message states: T2 adds one naming a size that changed across the
read, and T3 adds one naming the acquisition bound.

## Constraints

- Standard library only at runtime.
- No criterion added to `docs/specs/jsonl-otlp-exporter/spec.md` may name a
  consumer, product, repository or catalogue.
- No existing `ConfigRefused` message text changes. The module raises at ten
  sites and the escaping control walks nine of them; rewording one obliges
  walking every site individually rather than letting one case carry another's
  coverage.
- `config.py` must not import from `transport.py`. The bounded-call idiom is
  reused by shape, not by import: `transport` pulls in `socket` and
  `http.client`, and a configuration reader that cannot be read without the
  transport is a layering inversion in a package whose whole point is that the
  off-by-default path opens no socket.

## Construction tests

Both repairs are TDD. Each new case is proven red against the unrepaired build
before the repair lands, and the observed reds go in the verification ledger.

The ceiling cases are one construction test with several arms, because no arm is
the criterion alone. The acquisition bound is driven through substituted calls —
the open and the read separately, since AC-0002's subject is the whole
acquisition path — because the property is that a blocked acquisition ends, not
that a number exists. Which arms exist is pinned in each task's `Tests` block;
this section says why they have that shape, and deliberately does not restate the
set.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `README-pypi.md` `## Limits` | T4 | AC-0004 green | Renders on PyPI |
| `CHANGELOG.md` `## 0.2.0 — unreleased` | T4 | AC-0004 green | Tag matches `pyproject` |
| `notes/verification-ledger.md` | T2, T3 | An observed red for every case T2's and T3's `Tests` blocks pin | Ledger present, with one entry per pinned case |

## Design (LLD)

### Design decisions

**The ceiling is decided on the read, with the sample kept.** The reader asks
for `MAX_CONFIG_BYTES + 1` bytes and refuses when it gets more than
`MAX_CONFIG_BYTES`. The existing sampled-size check stays ahead of it — it is
the cheap refusal for a file that is already oversized, and it is what keeps an
enormous file from being read at all — and the existing short-read check stays
behind it. Three checks, in that order, each catching what the others cannot:
the sample catches a file oversized before the open, the overflow catches a file
that grows between the sample and the read, and the short read catches a read
that returned less than the sample promised.

The buffer alone leaves one residue, and it is closed rather than accepted. If
the file grows but the single `read(2)` returns only the sampled 65,536 bytes,
the length matches the sample and the prefix would be accepted — the exact
fail-open this delivery exists to remove, arriving by a different route. So the
size is re-sampled on the same descriptor after the read, and a size that
changed across the read is refused. That is one `fstat` and one comparison, it
needs no loop, and it makes the criterion and the `Never do` boundary true
rather than nearly true. A read loop was the other candidate and is not taken:
it trades a rare accept for an unbounded loop over a file a writer can keep
extending, which is a worse bound than the one it repairs.

Order matters and is load-bearing. The re-sample runs **before** the short-read
comparison, so a grown file gets the message that names growth rather than the
length-mismatch message, whose wording — "read returned N of M bytes" — reads as
a truncation when the real event is the opposite. Keeping that message for
genuine short reads is also why it needs no rewording, which the `Ask first`
entry would otherwise have engaged.

What the re-sample does not establish is that the content was not rewritten in
place at the same length. That is a different question from the registered
defect and no criterion claims it.

**The acquisition bound runs the I/O on an abandonable worker.** `O_NONBLOCK`
does not bound `read(2)` on a regular file and `open(2)` on a hard-mounted share
can block before any flag applies, so the deadline has to be reachable from a
thread that is not the one blocked. The open, the descriptor checks and the read
all run on one daemon worker; the caller joins with the deadline and raises
`ConfigRefused` when the worker is still alive. An abandoned worker holds one
open descriptor until the process exits, which is strictly better than
inheriting its stall — the same trade `_resolve_bounded` already makes.

The bound covers acquisition as a whole, not a file at a time, so a second
configuration file cannot double the time a caller waits. It is established
before the first `open`, because the open is one of the calls that can block.

**5 seconds, and where it comes from.** It is a responsiveness bound traded
against slow storage, not a bound no correct invocation can reach. A local read
of at most 64 KiB per file completes three orders of magnitude inside it, so the
ordinary case has enormous headroom; a genuinely slow mount can legitimately
exceed it, and the Risks entry below records that the value — not the origin —
is what to revisit if an adopter reports a legitimate refusal. What it buys is
that an unresponsive path fails inside the attention of the person who ran the
command instead of hanging. It is not derived from
`REQUEST_TIMEOUT_SECONDS` or `RUN_TIMEOUT_SECONDS`: those measure from the first
destination resolution, which happens after this I/O is finished, so there is no
ordering relation to preserve and reusing either value would import an origin
that does not apply.

### Interfaces & contracts

The published surface does not change. `read_config_file` keeps its exact
signature and `__all__` keeps its exact members.

The deadline is plumbed privately: a module-private reader takes an absolute
monotonic instant, `read_config_file` calls it having established its own from
the private `_CONFIG_TIMEOUT_SECONDS`, and `resolve_telemetry` establishes one
instant and passes the same one down both scopes. That is what makes the bound
cover acquisition rather than a file, and it is also what keeps a direct caller
of the public function bounded by default.

The constant stays private deliberately. The README states the bound as a
behaviour an adopter can hit, which is what an adopter needs; exporting the
symbol would add a public name to a published package for no caller, and the
spec's `Ask first` entry exists to stop exactly that happening by accident.

### Failure, edge cases & resilience

- A worker that raises transports its exception to the caller's thread
  unchanged, so every existing refusal keeps its own message and its own site.
- A deadline that has already passed when acquisition begins refuses without
  starting a worker.
- The bound does not apply to parsing: `tomllib` over at most 64 KiB already in
  memory cannot block on I/O, and moving the parse onto the worker would put a
  refusal's message on a thread the caller has abandoned.

### Quality attributes (NFRs)

Configuration acquisition: bounded at 5 seconds from its own start, enforced by
an abandonable worker. Stated as AC-0077 in the capability contract.

## Tasks

### T1: Amend the capability contract

**Depends on:** none

**Touches:** `docs/specs/jsonl-otlp-exporter/spec.md`,
`docs/specs/jsonl-otlp-exporter/plan.md`

**Tests:**
- `no stub (goal-based)` — the outcome is a document state, and
  `lint-contract-item-alignment.py` is the check.
- Verifies AC-0003. `python3 .claude/skills/new-spec/scripts/lint-contract-item-alignment.py docs/specs/jsonl-otlp-exporter` exits 0.

**Approach:**
- Rewrite AC-0056 to cover both configuration-file arguments and to decide the
  refusal on the complete file, keeping the accepted-at-exactly-64-KiB side
  explicit.
- Add AC-0077 for the acquisition bound, stating 5 seconds, its origin — the
  start of acquisition, before the first file is opened, because the open can
  block too — the input that makes it fire, and why it is not a reuse of AC-0040
  or AC-0055. That criterion is the canonical home of the value; this delivery's
  AC-0003 requires it and nothing else restates the number.
- Add AC-0077 to verification group VI-0007, which already owns AC-0056, and
  extend that group's prose with why the ceiling pair needs both arms and why
  asserting the bound's value is not asserting the bound.
- Add task T10 to `docs/specs/jsonl-otlp-exporter/plan.md` so AC-0077 has an
  owning task entry in the plan that serves its spec, following the T9
  precedent that exists for the same reason. T10 carries `no stub
  (implementation-discovered)`, the same record T9 carries and for the same
  reason: the seam it changes is decided by its implementation.
- Bring that spec's TDD-stub census back into agreement with the contract it
  describes. The census is **already wrong before this delivery touches it**: it
  states 72 criteria and the spec holds 75, because the three criteria the
  previous delivery added went into VI-0014 and into neither of the census's two
  buckets, and it names four TDD plan tasks while T9 also carries `no stub
  (implementation-discovered)`. Repairing only the increment this delivery adds
  would leave a contract statement that is wrong by three; the amendment touches
  that exact paragraph, so it repairs the whole statement. After the amendment
  the arithmetic is 76 criteria: 59 under `no stub (implementation-discovered)`
  in the nine groups the census already names, 3 in VI-0014, and 14 goal-based
  or manual QA.

**Done when:** the alignment lint exits 0 over
`docs/specs/jsonl-otlp-exporter`, both criteria read as AC-0003 describes, and
the census's counts sum to the number of criteria the spec actually holds.

### T2: Decide the size ceiling on the complete file

**Depends on:** T1

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_config.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cli.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_two_scope_config.py`,
`docs/specs/sender-bounds-its-configuration-read/notes/verification-ledger.md`

**Tests:**
- `no stub (implementation-discovered)` — the seam is `read_config_file`'s
  existing read block; the discovery predicate is that a case which samples the
  file at exactly `MAX_CONFIG_BYTES` and appends before the read is accepted by
  the unrepaired build. Proof obligation: each new case observed red before the
  repair, and the neighbouring non-growing case observed green both before and
  after, recorded in the ledger.
- Verifies AC-0001, and the amended AC-0056 in the capability contract.
- Three arms, in `test_config.py`, over the reader: growth that the read sees
  (appended through a second descriptor between the `fstat` and the `read`);
  growth that a short read hides (a substituted read returning a ceiling-length
  prefix of an already-longer file); and a file at exactly the ceiling that does
  not grow, which must still parse. A case at 65,535 or 65,537 bytes, or one that
  grows a file below the ceiling, exercises none of these branches and
  substitutes for none of them.
- One arm in `test_cli.py` drives the command with a growing configuration file
  and asserts exit 1 and that the transport seam is never constructed. AC-0001
  contracts "nothing sent and exit 1", which no reader-level unit can observe.
- The added refusal message takes its own arm in
  `test_two_scope_config.py::test_every_refusal_escapes_a_hostile_path`, which
  walks every site `config.py` raises at. The arm asserts it reached *its own*
  message, and is mutated individually: an arm that can be satisfied by another
  site's message is how a control covering one site of ten last shipped here.

**Approach:**
- Read `MAX_CONFIG_BYTES + 1` bytes.
- Re-sample the size on the same descriptor after the read and refuse a size that
  changed across it, placed before the existing short-read comparison so a grown
  file gets the message that names growth.
- Leave every existing refusal message unchanged; the one added message names a
  fact none of them states.

**Done when:** all four arms pass, each new arm is observed red against the
unrepaired read, and `python3 -m pytest packages/jsonl-otlp-exporter/` is green.

### T3: Bound configuration acquisition

**Depends on:** T2

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_config.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_two_scope_config.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cli.py`,
`docs/specs/sender-bounds-its-configuration-read/notes/verification-ledger.md`

**Tests:**
- `no stub (implementation-discovered)` — which function carries the worker is
  decided by the implementation. The discovery predicate is that a substituted
  `os.open`, `os.fstat` or `os.read` which does not return leaves the unrepaired
  call blocked; the proof obligation is each case observed as a hang against the
  unrepaired build, under a harness timeout so the observation itself terminates.
- Three substitution cases, one per blocking syscall on the acquisition path:
  the open, the descriptor proof and the read. They are separate syscalls, and a
  build that moves only some of them onto the worker passes a case written for
  the ones it moved while an unresponsive mount still hangs it on the rest —
  `fstat` on an open descriptor can block on attribute revalidation just as the
  read can. AC-0002's subject is the whole acquisition path, so each is pinned
  here rather than left to the Approach, where nothing gates it.
- Verifies AC-0002, and AC-0077 in the capability contract.
- The substituted read blocks on an event the test sets in teardown, so the
  abandoned worker ends with the case rather than outliving the session.
- A second case drives `resolve_telemetry` with two files and one blocking read,
  asserting the refusal arrives inside the bound rather than after two of them.
- A third case drives the command itself, asserting exit 1 and a diagnostic on
  stderr rather than a hang, which is the outcome an adopter sees.
- The added refusal message takes its own arm in the escaping control alongside
  T2's, asserting it reached its own message, and is mutated individually.

**Approach:**
- Run the open, the descriptor checks and the read on a daemon worker; join with
  an absolute monotonic deadline; raise `ConfigRefused` naming the bound when the
  worker is still alive; re-raise the worker's own exception otherwise.
- Establish the deadline in `resolve_telemetry` and pass it down both scopes
  through module-private plumbing; `read_config_file` keeps its signature and
  establishes its own deadline from the private constant when called directly.

**Done when:** a blocking open, a blocking descriptor proof and a blocking read
each end the call with its refusal, each case is observed against the unrepaired
build as a hang, and `python3 -m pytest packages/jsonl-otlp-exporter/` is green.

### T4: Published surface and registration

**Depends on:** T3

**Touches:** `packages/jsonl-otlp-exporter/README-pypi.md`,
`packages/jsonl-otlp-exporter/CHANGELOG.md`, `workspace.toml`

**Tests:**
- `no stub (goal-based)` — presence and structure are mechanical.
- Verifies AC-0004. `grep` for the acquisition bound in the README `## Limits`
  table; **two separate** greps within the `## 0.2.0 — unreleased` changelog
  section, one per behaviour change, since a single grep for the acquisition
  bound passes with the exact-ceiling change unrecorded; and `! grep -q` for each
  of the two slugs in `workspace.toml`.
- Also owns the whole-package regression the spec's Testing Strategy contracts,
  so those commands have a task that gates them.

**Approach:**
- Add the configuration-acquisition row to the README limits table, next to the
  single-request and whole-run rows it is deliberately separate from.
- Record both behaviour changes under `## 0.2.0 — unreleased`, which is the
  correct section because nothing has been published.
- Remove both registered slugs and their comments from `[backlog].open`.

**Done when:** all three greps find their text, neither slug appears in
`workspace.toml`, `lint-spec-status.py` reports no dangling deferral anchor, and
the whole-package regression is green in this order:
`python3 -m pytest packages/jsonl-otlp-exporter/` (never with `-q`, which doubles
the package's own `addopts` and suppresses the count),
`python3 -m pytest tests/roster/ -q`,
`python3 tools/test-lint-pack-test-boundary.py`, and
`python3 packages/jsonl-otlp-exporter/tests/wiring_sweep.py` run **against the
merge base first** and then against the change, with no survivor in the second
run that is absent from the first.

## Rollout

Behaviour change on an unreleased distribution, so there is no migration. A file
exactly at the ceiling that grows during the read starts being refused, and a
configuration path that cannot be read within 5 seconds starts being refused;
both were previously an accept and a hang respectively. Reversal is reverting the
two commits, since neither adds a flag or a persisted format.

## Risks

- **The abandoned worker holds a descriptor.** A bounded-out acquisition leaves
  one open descriptor until the process exits. The command exits 1 immediately
  after, so the window is the length of one refusal message; the alternative is
  inheriting the stall.
- **The re-sample does not see an in-place rewrite.** A writer that replaces the
  content at the same length is invisible to a size comparison. That is a
  different question from the registered defect, no criterion claims it, and
  closing it would need a lock this command has no way to take.
- **5 seconds could be too short on a slow but working mount.** It is three
  orders of magnitude above a local read; if an adopter reports a legitimate
  refusal, the value is the thing to revisit and the origin stays correct.

## Changelog

- 2026-09-17 — Authored to repair two defects the
  `telemetry-sender-owns-its-configuration` delivery registered and excluded,
  both behaviour changes on a published command and so out of that delivery's
  bundled-fixes tiers.
