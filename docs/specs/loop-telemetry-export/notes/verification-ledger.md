# Verification ledger — loop-telemetry-export

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## T6 — the two approved stubs, and what their mutations proved

Both stubs were materialized from `plan.md` unchanged and confirmed **collected**
before being trusted: `--collect-only` went from 48 to 50. A stub that is never
collected passes by not existing, and the suite gives no signal for it.

AC-0046 earned the recorded red exactly — `KeyError: 'schema'`. AC-0047 is green
at HEAD by design: it preserves a property that already holds, so its
non-vacuity comes from mutation rather than from absence.

| Reverted | Control that failed |
| --- | --- |
| the `"schema": 1` key in `pending_data` | AC-0046 |
| replay path retro-stamping (`pending["schema"] = 1`) | AC-0047 |
| replay path rewriting any other field (`pending["spec"] = …`) | AC-0047 |

The third case is why AC-0047 asserts `replayed == legacy` and not merely that
the key is absent: a build that rewrote every other field passes a key-absence
check. Suite after the change: 45 passed, 5 skipped.

## AC-0031 names four enumeration sites. Five are required.

**This is a contract observation for the owner, not a silent choice.**

AC-0031 requires the package to appear in the root `pythonpath`, mypy's `files`,
the `Makefile` test-suite invocations, and the pip-audit build-system leg, *"so
its tests and type checks are run by this repository's gates."* All four were
added. Measured immediately afterwards, the package's suite still did not run:

```
ModuleNotFoundError: No module named 'jsonl_otlp_exporter'
Interrupted: 8 errors during collection
```

The cause is stated in the root `pyproject.toml`'s own comment: each
`packages/*/` suite carries its own `[tool.pytest.ini_options]`, which is the
nearer configfile for its own run, so the root `pythonpath` never reaches it.
The entry that does reach it is the `PYTHONPATH` assignment at `Makefile:11` —
a fifth literal list, and the one `packages/agentbundle` and
`packages/credbroker` already rely on.

Measured three ways, same invocation, only the path differing:

| `PYTHONPATH` | Result |
| --- | --- |
| unset | 8 collection errors |
| `agentbundle:credbroker` (the pre-change value) | 8 collection errors |
| `agentbundle:credbroker:jsonl-otlp-exporter` | **278 passed, 1 skipped** |

The fifth site was added, because the criterion's purpose clause is not
satisfied without it and its letter does not forbid it — AC-0031 says the
package *appears in* those four, not that it appears nowhere else. If the
intended reading is that exactly four sites are in scope, AC-0031 needs the
words, and that is a contract amendment rather than a code change.

**The plan's own Risks section predicted this class and undercounted it**: "The
gate enumeration is four separate literal lists. Adding the package to three of
four leaves a hole that `make test` reports green." There are five, and adding
it to four left exactly that hole.

## T4's `Touches` omits the file its `Tests` field requires

T4's `Tests:` field requires that each enumeration site "is read and asserted".
Its `Touches:` field names only `pyproject.toml` and `Makefile`. Both fields are
pinned, and they cannot both be satisfied: the assertion needs a file to live in.

The construction test was written at `tools/test_gate_enumeration.py` and its
invocation added to the `Makefile`, which is within `Touches`. Recorded here
rather than corrected in `plan.md`, because `schedule` has persisted the plan
and correcting it in phase would need a contract amendment.

`tools/` has **no blanket `pytest tools/` run** — every tools test is named
explicitly in the Makefile, so a test file added without its invocation line
would never execute. The invocation was verified to sit inside the
`run-test-suite` define that `make test` expands, not merely somewhere in the
file.

All five assertions were mutation-proved by reverting each site in turn; each
killed its own control, and no other. Sources restored by editing.

## The mypy site AC-0031 names is not the one the gate reads

**A sixth site, and the one that mattered most.**

AC-0031 requires the package in "mypy's `files`". It was added, and
`make lint-mypy` went on reporting *"Success: no issues found in **139** source
files"* -- the same count as before the change. The package was not checked at
all.

`tools/lint-mypy.py` carries its own `TYPED_PACKAGES` list and passes it to mypy
as **positional arguments**, which override `files` from the config file. So the
criterion's named site is inert for the gate that runs.

Proved by running the same config two ways:

| Invocation | Result |
| --- | --- |
| `mypy --config-file pyproject.toml` (config `files` only) | 146 files, **1 error** |
| `mypy --config-file pyproject.toml <positional packages>` (what the gate does) | 139 files, clean |

Adding the package to `tools/lint-mypy.py` took the gate to 146 files and
surfaced a **real pre-existing defect** that had never been type-checked:
`source.py`'s reader is annotated `Iterator[dict[str, Any]]` but yields the
`IDLE` sentinel to signal that it has caught up.

Repairing it walked three surfaces, and the first two attempts were each a
partial repair of the same kind this ledger's sibling records six times:

1. widening the producer's return type moved the error to `cli.py`, because
   `batch_records` was annotated `Iterable[Mapping[str, Any]]`;
2. widening that parameter moved the error into `batch_records` itself, because
   `record is IDLE` does not narrow a union for a type checker even though the
   `continue` beneath it makes the code correct;
3. `isinstance(record, _Idle)` narrows, and is equivalent here because `_Idle`
   has exactly one instance.

No behaviour changed: the suite is 278 passed, 1 skipped before and after.
`make lint-mypy` is now clean at 146 files.

**The annotation defect is in `jsonl-otlp-exporter`, which is owned by a
different spec.** It is repaired here rather than routed, because T4 cannot be
"done" while the gate it adds is red, and the fix is an annotation correction
with no behaviour change. Flagged for that spec's owner.

Both mypy sites are asserted in `tools/test_gate_enumeration.py`: the criterion's
named one, and the one with teeth. The first carries a docstring saying plainly
that it can hold while the gate checks nothing, so a future reader does not
mistake it for coverage.

## T4's reachability probe

`Done when` asks for a deliberate failing test inside the package to be
*reported*, proving the suite is reached rather than merely listed. A failing
test was added to `packages/jsonl-otlp-exporter/tests/unit/`, the package's
invocation run with the Makefile's own `PYTHONPATH`, and the failure was
reported by name with a non-zero exit. The probe file was then removed.

Worth stating because the alternative failure is silent: a suite that is listed
but unreachable reports nothing at all, which reads exactly like a suite with no
failures.

## A measured count that differs from the brief

The exporter's suite is **279 tests** (278 passed, 1 skipped), not the 410 the
task brief stated. Recorded so the next reader measures rather than inherits the
number.

## T3 — the first reader of a dormant schema, and two things worth recording

`[[pack.runtime-dependencies]]` has been in `pack.schema.json` with no reader.
T3 writes the first one, so its reporting shape was set here: `CAT-L032` at
`Severity.INFO`, naming the package, the word "optional", the word
"unsatisfied", and the owning pack. INFO is what keeps the exit code 0 — an
unsatisfied *optional* dependency is not a lint failure.

Detection is `importlib.metadata.distribution()`, in-process. Nothing is
acquired, and the schema is not widened toward acquisition: `workspace.toml`
carries a registered backlog item to open a separate RFC for registry-acquired
dependencies, and a trust or lifecycle policy belongs there.

**AC-0039's third conjunct needed a control, not a comment.** "Invoking no
package manager" is unobservable by absence — a test that simply does not see a
subprocess proves nothing. The test patches `subprocess.Popen` and `os.system`
to raise, so the assertion fails if the lint ever shells out. Proved by
inserting `subprocess.run(["pip", "--version"])` into the check: the sentinel
fired before pip launched.

Four mutations, each killing its own control:

| Reverted | Control that failed |
| --- | --- |
| the `_check_optional_runtime_dependencies()` call | the report assertion |
| `Severity.INFO` → `Severity.ERROR` | the exit-status assertion (`1 == 0`) |
| a deliberate `subprocess.run(["pip", …])` | the process-launch sentinel |
| the `pack.toml` declaration block | the report assertion |

The fourth was added here: the worker proved the reader and the severity but not
the declaration, and without it `packs/core/pack.toml` — half of T3's `Touches`
— had no control at all.

**The test makes the absence deterministic rather than inheriting it.** The
distribution genuinely is not installed in this environment, so the assertion
would pass either way today; monkeypatching `distribution` to raise only for
this package means the test does not silently become vacuous the day someone
installs it.

**An environment caveat for anyone re-running AC-0039 by hand.** A bare
`agentbundle catalogue lint` does not exercise this worktree: the editable
install on this machine points at the primary checkout. Under `pytest` the root
`pyproject.toml`'s `pythonpath` puts this worktree's `packages/agentbundle`
first, which is why the test is the trustworthy route and a bare invocation is
not. The install was deliberately left pointing at the primary checkout.

**One reported failure did not reproduce.** The worker reported the lint unit
file as "88 passed, 1 unrelated environment failure" — a `PermissionError` from
`Path.rmdir()`. Re-run here: **89 passed**, no failure. It was the worker
sandbox refusing a filesystem operation, not a repository defect, which is why
a worker's gate report is reconciled rather than accepted.

## T2 — the merge was computed and then discarded

The worker built the per-setting resolver correctly and proved it with eight
mutations. Its tests still did not verify AC-0041, because they asserted the
resolver's `settings` dict and the `--config` choice — an intermediate and a
consequence — rather than the property the criterion names: **the documented
invocation** resolves each setting.

What that missed, traced through the sender:

- `--config` names ONE file, and `config.py` reads exactly one key from it:
  `[telemetry].endpoint`.
- `service_name` never comes from the config file at all. `cli.py` takes it from
  `--service-name`, defaulting to the profile stem.
- The resolver rendered no `--service-name`.

So when the user file won the endpoint, the repository's `service_name` was
merged, asserted in the dict, and then dropped: the sender would have used the
profile stem while the resolver reported the repository's value. Every test
passed.

Repaired by rendering each merged non-endpoint setting as its own flag, and the
control now asserts the *invocation*: with the endpoint coming from the user
file, `--service-name` must still carry the repository's value.

**A setting the sender cannot receive is now refused, not dropped.** A
`[telemetry]` key with no flag and no config route would otherwise be silently
inert — the adopter believes they configured something that does nothing, and
these settings decide where data is sent, so the quiet failure is open rather
than closed. The error names the offending key and the deliverable set. **This is
a contract reading, recorded for the owner:** AC-0041 says each setting resolves
from one scope or the other and says nothing about a setting that can resolve
nowhere. Refusing is the reading taken; if silent tolerance is wanted, the
criterion needs the words.

Five mutations, each killing its own control:

| Reverted | Control that failed |
| --- | --- |
| per-setting merge → whole-file-wins | the precedence test |
| precedence reversed (user wins) | the precedence test |
| the merged-setting flag rendering | the invocation test |
| the undeliverable-setting refusal | the refusal test |
| `--input` no longer under `.loop-run` | the arguments test (AC-0043) |

The second is the one the plan warned would matter most: `desk-research` reads
the user file first, telemetry reads the repository file first, and nothing about
the code makes the direction obvious.

**Every rendered flag was checked against the real emitter.** `--input`,
`--root`, `--config`, `--profile` and `--service-name` all exist in the sender's
argument parser. A documented invocation naming a flag the sender does not have
would fail only when someone ran it.

**The guide-index gate does not fail.** The worker could not run the three guide
checks and reported that rather than guessing. Run here: `validate-guides` OK
(225 checked), `check-guide-index` OK (21 packs), `lint-guide-titles` OK (231
files).

## A worktree collision, and why it is recorded here

Mid-T2 a peer session ran `git checkout -b` in this shared worktree, moving HEAD
off this branch for about three minutes. No work was lost — the five commits were
safe on the branch, and untracked files survive a checkout.

The cost was not lost work but **trustworthy-looking wrong numbers**:
`make lint-mypy` reported 140 source files instead of 146, and
`tools/test_gate_enumeration.py` reported "no tests ran". Both read exactly like
a regression in the work under test. The count was chased rather than accepted,
which is the only reason it was diagnosed as an absent tree rather than a defect.

Worth recording because the lesson generalises past this incident: a gate whose
denominator moved reports a smaller number, not an error. `147` after T2 — 146
plus the new module — is what confirmed the tree was whole again.

## T1 — the profile, and a TOML trap the test caught

The three approved stub assertions were materialized, confirmed collected, and
earned the recorded red: all three `FileNotFoundError` on the profile path.

**The allowlist is derived, not typed.** It is generated from a line the engine
actually emits, minus the four routed fields, and the test re-derives it the same
way. Measured: 14 emitted keys − 4 routed = **10 allowlisted**
(`awaiting_input`, `budgets`, `event`, `from`, `phase_s`, `phase_started_at`,
`schema`, `spec`, `to`, `waived`). `schema` is there because T6 shipped first,
which is exactly why T1 depends on it.

**A `[severity_map]` table header silently captured the two keys below it.** The
first profile wrote `[severity_map]` as a section, which made `identity` and
`allowlist` members of that table rather than top-level keys. Two of the three
assertions failed immediately. An inline `severity_map = { success = 9, failure
= 17 }` fixes it, and a comment on the line says why the header form is wrong —
the next person to add a key under it would reintroduce the bug.

Five mutations, each killing its own control:

| Reverted | Control that failed |
| --- | --- |
| `success = 9` → `10` (the plan's own recorded proof) | the pinned-pairs test |
| a key removed from the allowlist | the allowlist test |
| a key added that the engine never emits | the allowlist test |
| `timestamp_field` no longer `at` | the field-declaration test |
| `identity` drops `seq` | the field-declaration test |

The third matters as much as the second: the assertion is set equality, so the
allowlist cannot drift in either direction.

**One deviation from byte-identical stub materialization.** Ruff's `I001`
rejected the stub's import block ordering. The names were sorted and a comment
records it. No assertion changed; only the order of five imported names.

## AC-0044 — the live round trip, 2026-09-13

`otel/opentelemetry-collector-contrib:0.160.0` under Colima, an `otlp` receiver
on 4318 with `file` and `debug` (detailed) exporters. The invocation was built by
`telemetry_layout.resolve()` — the documented one — not hand-assembled, so this
exercises T2's wiring and T1's profile together.

| Emitted from a real line | Reached | Observed |
| --- | --- | --- |
| `at` = `2026-09-14T03:54:48Z` | `Timestamp` | `2026-09-14 03:54:48 +0000 UTC` |
| `result` = `success` | `SeverityNumber` | `Info(9)`, `SeverityText: success` |
| `run_id` | attribute | `Str(a8c153b4-…)` |
| `seq` = `27` | attribute | `Int(27)` |

All **10** allowlisted keys arrived, including `schema`, and **nothing outside
the allowlist appeared**. The unmapped-severity report reached stderr in the
shape the decision intended: `severity value None is not in the profile's
severity_map; 21 record(s) sent without a severity`.

Three things cost time and are worth recording:

- **`localhost` resolved to `::1` and was refused.** The container publishes on
  `0.0.0.0` and `[::]`, but only `127.0.0.1` accepted a connection from the host
  under Colima. The endpoint must name the IPv4 loopback explicitly.
- **The Collector image is distroless and `/tmp` does not exist in it**, so a
  `file` exporter pointed there fails the whole pipeline at startup with
  `open /tmp/records.json: no such file or directory`. Colima also does not share
  `/private/tmp`, so a bind mount from the session scratch directory fails with
  `not a directory`. A gitignored path inside the worktree works for both.
- **My own readback instrument was wrong before the product was.** `Timestamp:`
  matched inside `ObservedTimestamp:`, which reported `1970-01-01` and looked
  exactly like a dropped timestamp. Anchoring the pattern to line start showed
  the real value had been correct all along. The instrument was verified before
  its verdict was believed, which is the only reason this is a footnote rather
  than a bug report.

**A stated limit.** The sender is not pip-installed here, so the run used
`python3 -m jsonl_otlp_exporter.cli`, which is the same `main` the
`jsonl-otlp-export` console script points at. The console script itself was
exercised under the sender's own AC-0014, not here.

## T7 — a corpus recorded, not authored, and where its tests live

**Both halves of the corpus are real.** The versioned half was driven through
`loop-engine.py` at this build; the legacy half is lines this repository actually
emitted before `schema` shipped. 17 records: 11 versioned, 6 legacy, 10 distinct
events, and all three `result` values including `null`. A hand-written corpus can
only contain shapes someone thought of, and a schema validated against one passes
by construction.

**`schema` is optional and constrained only when present.** A replayed
pre-versioning record is appended unchanged (AC-0047), so a schema that *required*
the key would reject a line the engine still legitimately writes. Mutation M5
makes it required and the legacy-record control fails, which is what stops that
reading being lost.

**`True` is in the rejection set on purpose.** Python treats `bool` as a subclass
of `int`, so a validator checking with `isinstance` would accept `schema: true`.
JSON Schema's `integer` excludes it, and the test pins that rather than assuming
it. Eight bad values are checked: `0`, `-1`, `"1"`, `1.5`, `true`, `null`, `[]`,
`{}`.

Seven mutations, each killing its own control:

| Reverted | Control that failed |
| --- | --- |
| `$comment` stops naming the spec | AC-0053 |
| the `contracts/README.md` row | AC-0050 |
| `schema` left unconstrained | the eight rejection cases (AC-0049) |
| `at` dropped from `required` | the identity-field cases (AC-0049) |
| `schema` made mandatory | the legacy-record control |
| **the poller made to branch on `schema`** | AC-0052 |
| the corpus loses its legacy half | AC-0048's first half |

The sixth is the criterion's whole point: `_apply_event` was mutated to append
`-versioned` to the state when the key is present, and the comparison caught it.

**The AC-0052 control compares the two results to each other, never to a
literal.** A pinned expected output would still pass if both sides drifted
together, and the criterion is about the *difference*. A second test asserts the
comparison can fail at all, so a `_parsed_result` that returned a constant cannot
satisfy AC-0052 while observing nothing.

**A placement decision, recorded because the obvious home was wrong.**
`tests/roster/` is where this repository's other JSON Schema contract tests live
and where `jsonschema` is already imported — but **roster is not reached by `make
test`**. A roster test runs on a pull request only when `build-check.yml` names it
individually. The contract tests went into the agentbundle unit suite instead,
which runs every build. The plan named a home only for AC-0052's test, so this is
an unpinned choice; it is recorded rather than left implicit. `jsonschema>=4.0` is
already declared in `tools/requirements.txt`, so no dependency was added.

**One authoring error worth noting.** `_REPO` was first computed as
`parents[3]`, which from `packages/agentbundle/tests/unit/` is `packages/`, not
the repository root. Every path-reading test failed at once with a
`FileNotFoundError` naming the wrong path, so it was loud rather than silent —
but a test that had happened to find a file there would have pinned the wrong one.

## T5 — a literal string does not care about Markdown

**AC-0054's third string was introduced wrapped, and passed nothing.** Written as
`it **sends nothing until an endpoint is\nconfigured**`, the phrase reads
correctly to a person and is simply absent to a criterion that greps for it. The
check caught it immediately; a reviewer reading the rendered page would not have.
The test now says so in its docstring, and mutation M5 re-wraps a guide literal
to keep that lesson executable.

**AC-0051 is the only one of T5's criteria that prose cannot satisfy on its own.**
The integer in § 5.1 is compared against the key count of a line the engine
actually emits, so the sentence cannot drift from the envelope. It moved from
thirteen to fourteen when `schema` shipped, and mutation M1 puts it back to
thirteen to prove the comparison is live.

Six mutations, each killing its own control: the § 5.1 count, a retired claim
returning to § 2, § 2 losing its positive claim, a dead `agentbundle.md` anchor,
a wrapped guide literal, and a reserved exit code named in the guide.

**§ 10.4 needed no edit.** It said "this is why the event line carries a version"
while nothing carried one, and the earlier § 11 inventory listed it as stale.
T6 made the sentence true, so the repair was shipping the key, not changing the
prose. Worth recording because the inventory's own remedy would have been wrong.

**§ 5.1's internal contradiction is resolved.** Its second bullet said attempt
counts were not on the line while the third described `budgets` copying the retry
counters onto every line. The first now says what it meant: `result` reports one
transition's decision; the counters live in `budgets`.

## The spec asks for a row in an index that deliberately does not exist

**A contract observation for the owner, not a silent choice.**

The spec's Durable Outputs table names `docs/specs/README.md` with expected
evidence "Row in the active list" and closeout condition "Row present". That file
has a section headed **"Why there is no index"**, and it is explicit:

> Specs are discovered by listing this directory. There is no index table,
> because an index over a document corpus is generated from that corpus or it
> does not exist, and a spec index had no reader.

It cites **ADR-0112**, an accepted decision. Adding a row would recreate exactly
what that ADR removed, and would be the only such row in the file.

No row was added. Durable Outputs is working material under this spec's own
header — correctable in place without an amendment — but `spec.md` is frozen by
`approve-plan`'s hash mid-execution, so the correction is recorded here instead
of edited there. The owner's call: either that row leaves the table, or ADR-0112
is revisited. Nothing else in T5 depends on it.

## One pre-existing gate failure, confirmed rather than assumed

`docs/product/changelog.md` fails the readability threshold at 58.68. Measured
against `HEAD` before the entry was added: **58.62**. The entry moved it up, not
down. Not this delivery's to fix, and confirmed by measurement rather than by the
file-not-in-diff shortcut, because the file *is* in the diff.

## The wiring sweep reported fifteen defects and had run the wrong suite

`packages/jsonl-otlp-exporter/tests/wiring_sweep.py` was invoked from the
repository root. Every mutation came back `HUNG` — including
`help="the JSONL file to read"`, which cannot hang anything.

The cause is one missing argument. The sweep runs:

```python
subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-x"],
               capture_output=True, text=True, timeout=PER_RUN_SECONDS)
```

There is no `cwd=`, so the child inherits the caller's. From the repository root
`tests` is not the exporter's suite at all — it is `tests/conformance`,
`tests/fixtures` and `tests/roster`, the last of which is a hundred files. Every
run exceeded `PER_RUN_SECONDS`, and `TimeoutExpired` is classified `HUNG`.

Measured both ways:

| Invoked from | What `pytest tests` means | Result |
| --- | --- | --- |
| repository root | `tests/` — conformance, fixtures, roster | times out; every mutation reads `HUNG` |
| `packages/jsonl-otlp-exporter/` | the package's own suite | **~10 s**, 278 passed, 1 skipped |

**The failure mode is the dangerous one: a gate that reports defects rather than
an error.** Fifteen `HUNG` lines look like fifteen findings in the code under
test. Nothing in the output says "I ran a different suite". It was caught only
because a mutation that removes a `help=` string cannot plausibly hang a test
run — the *implausibility of the finding* was the signal, not the tooling.

**Killing the sweep left a mutation in the working tree.** `cli.py` was found
with `timeout=timeout` missing from its `HTTPSConnection` call — the mutation in
flight when the process died. Restored by editing the keyword back, then
confirmed byte-identical to `HEAD`. A sweep that mutates in place has no crash
safety, so the tree must be checked after any interruption; `git status` was
clean of everything except that one file, which is exactly how it would look if
the mutation had been a real edit.

It also writes `wiring-sweep-results.txt` into its working directory, which is
not gitignored at the repository root. Removed.

## An ADR ordinal collision silently invalidates a locked plan baseline

Found on the sibling spec and recorded here because **this plan carries the same
exposure**.

`jsonl-otlp-exporter`'s cohort refuses `schedule check-current`: its `plan.md` no
longer matches the baseline pinned at `schedule` time. The tool's own diagnosis —
"this baseline was pinned before canonical hashing landed" — is wrong. Three merge
commits touched that locked plan after the pin, and each changed the same
sentence, because the decision's ordinal was claimed upstream five times:

```
ADR-0111 -> ADR-0112 -> ADR-0114 -> ADR-0115
```

Every rename was a correctness fix that had to happen. Each one edited a plan
that was already frozen, and nothing warned at the time, because renaming was the
right thing to do.

**So the cost of an ordinal collision is not the rename. It is that a locked
baseline is invalidated by a correct edit, and the failure surfaces much later at
a transition, wearing a misleading explanation.**

`docs/specs/loop-telemetry-export/plan.md` cites `ADR-0115` at lines 46 and 86.
If that ordinal is claimed again upstream, this plan's baseline breaks exactly
the same way. Checked at this build: `docs/adr/` holds `0111` through `0115` with
**no duplicate ordinals**, so the citation resolves today.

The sibling run was deliberately **not** repaired, and the reasoning is worth
keeping. The printed recovery is cohort-only but it is a re-approval in substance:
it clears the retry counters and the stasis baseline that four implementation
review rounds produced, and `approve-plan` re-pins whatever is on disk. What it
buys is `DONE` written to `engine-state.json` and `state.json` — both untracked,
never committed. Destroying a four-round audit trail to make an untracked local
file say `DONE` is a bad trade, so that run stays at `CODE-IMPLEMENTATION` with
the whole account recorded in its own tracked ledger.

## The corrected sweep: 46 mutations, 30 caught, 1 hang, 15 survivors

Run from the package directory. The tree was verified byte-identical to `HEAD`
afterwards — a normally-exiting sweep does restore; only a killed one does not.

**The one hang is already documented.** `transport.py:496 daemon=True` — removing
it makes the suite hang rather than fail, which the sibling spec's ledger recorded
when the sweep was written. Expected, not new.

**Fifteen survivors, and ten of them have no behaviour to control.** `prog=`,
`description=` and eight `help=` strings change only `--help` output. `SKIP` does
not filter them, so the sibling ledger's "nine survivors" was a hand triage that
left no trace in the tool — which is why they had to be re-triaged here. Two more,
`frozen=True` on two dataclasses, are reasoned rather than tested immutability.

**Three are behavioural. Only one is a coverage gap, and that correction matters
more than the original finding.** Each was traced to source rather than inferred
from the survivor list:

| Survivor | Verdict | Evidence |
| --- | --- | --- |
| `cli.py:49 required=True` | **genuine gap** | dropping it still fails the run, but through whatever `open_input(None)` raises rather than as a usage error — the exit code happens to match while the observable is wrong |
| `cli.py:147 on_oversize=lambda …` | **unreachable by construction** | `test_cli.py:571 test_the_oversize_path_is_unreachable_through_the_cli` pins the *relationship* between AC-0018's 64 KiB line cap and AC-0019's 8 MiB body cap: one record reaches ~388 KiB, about twenty times under, so the singleton-refusal branch never fires from the command |
| `cli.py:155 best_effort=args.best_effort` | **redundant, not uncontrolled** | `cli.py:186` masks the status a second time (`if outcome.status != EXIT_OK and args.best_effort …`), so dropping the line-155 wiring changes no observable — the CLI mask converts the failure anyway |

So of 46 mutations and 15 survivors, **one** is a coverage gap. The other two have
explanations that are true at source and invisible in the sweep's output.

**"A survivor is a defect" is too strong, and this run is why.** A survivor is a
signal that something has no control; it does not say whether a control is
*possible* or *meaningful*. A dominated bound cannot be controlled behaviourally —
only its relationship can, which is what that test does. A redundant path should
be resolved rather than tested, because a control over it pins the redundancy in
place. Reading the raw list as fifteen defects, or even three, would have produced
two repairs that made the code worse.

**None is attributable to this delivery.** The only changes here to that package
are three annotation-only lines, at `source.py` hunks `@@41` and `@@196` and
`transport.py` hunks `@@205` and `@@223`; every survivor sits outside those
ranges. They are also out of contract: this spec states that the sender's own
behaviour belongs to `jsonl-otlp-exporter` and that duplicating it here would
create a second home that drifts. **Routed to that spec's owner, not repaired
here** — repairing would be scope expansion into a contract this one may not
specify.

## Review round 1 — 14 findings, 12 sustained, 2 refuted

Adversarial review and a separate neutral adjudication, both on Codex. Nine
sustained findings were repaired here; three require owner authority and are
surfaced rather than resolved (below).

**The disclosure section was factually wrong, and its own test passed.** The guide
said "What is never sent: anything not on that profile's allowlist." The sender's
`profile.py` says the opposite in as many words — `routed_fields` carries the
docstring "These reach their destination whether or not the allowlist names them."
`at`, `result`, `run_id` and `seq` are deliberately absent from the allowlist and
are always sent. AC-0020 checks three literal strings, all of which were present
while the prose around them was false. **A literal-string criterion cannot see a
wrong sentence.**

**An evidence line pinned to a moving ref falsified itself.** § 11 stated that
`git diff ec6b94f91..HEAD -- loop-engine.py` "is empty". True when written; false
four commits later, because this delivery's own T6 added `schema` to that file.
It now names two fixed commits, `ec6b94f91..f0a04a223`, and says why. The same
count drift left "these thirteen fields" in § 9 while § 5.1 said fourteen — the
partial-surface class again, on a number I had just changed.

**The printed invocation was unquoted.** The guide built a command from values
read out of two TOML files and told the reader to paste it into a shell. A
repository path containing a space breaks argument boundaries; a crafted value
in a repository-scope layout file could end one command and begin another. The
example now uses `shlex.join`, and a `subprocess` form that never builds a shell
command at all is offered as the better option.

**`agentbundle` was never bumped.** `telemetry_layout` is a new public module and
`CAT-L032` a new diagnostic, both in a package adopters install independently from
PyPI. Shipping `core` 2.25.27 against `agentbundle` 0.44.1 would leave the guide's
documented import unavailable. Bumped to 0.45.0 across both real version surfaces
with its own changelog entry; `build/lib/` is a gitignored artifact and was left
alone.

**Three controls could not fail, and the repairs were mutation-proved against the
exact gap each had:**

| Control | What it missed | Proof the repair closes it |
| --- | --- | --- |
| the mypy-gate assertion | searched the file's whole text, so a comment naming the path satisfied it | path moved into a comment → now fails |
| the poller non-vacuity test | proved only that *some other* event differs, so ignoring both target records stayed green | `_apply_event` made to ignore `gates-clean` → now fails |
| the exit-code control | recognised only prose like "exit 3", not a table row | `\| 3 \| refused \|` added to the guide → now fails |

**Two findings were refuted, and both refutations are load-bearing.** The schema's
permissiveness contradicts an architecture sentence, not AC-0048 or AC-0049 —
neither obliges the six descriptive fields. And the derivability research was
performed against the accepted base under a separate instruction that preceded
these seven tasks, so it is separate work sharing a branch rather than scope
expansion.

**Shipped pack content carried internal citations.** The profile named `ADR-0115`
and a `docs/architecture/` path, and the engine comment repeated the second; both
violate `packs/AGENTS.md`'s portability rule. Rewritten to state the rules
directly. A pre-existing citation at `loop-engine.py:1087` is outside this
delivery's hunks and was left.

## Contract amendment 1 — authorized by the owner, 2026-09-14

Three of round 1's sustained findings could not be answered by a ledger
disposition, because each concerns a **pinned** field of an approved artifact.
The owner was given the trade-off — ship with dispositions, amend properly, or
remove the behaviour that created the obligation — and chose to amend.

**What is being corrected, and why a disposition was not enough:**

| Finding | Pinned field | Why it must change |
| --- | --- | --- |
| B4 | T4 `Touches` | names only `pyproject.toml` and `Makefile`; delivery also required `tools/lint-mypy.py` and a construction test file, because AC-0031's four named sites do not achieve its own purpose clause |
| B5 | T5 `Touches` | names `docs/specs/README.md`, where ADR-0112 forbids the index row the durable-output table asks for; the obligation is impossible as written |
| B6 | spec acceptance criteria | `telemetry_layout.resolve()` refuses a `[telemetry]` setting the sender cannot receive — an observable refusal, which `docs/CONVENTIONS.md` lines 444-447 require to be an AC "when they're added to the code" |

`plan.md`'s own header is what decides B4 and B5: `Touches`, `Tests` and
`Done when` "are what a completion gate reads, and they are pinned". A ledger
entry records what happened; it cannot move a pinned field. B5 is the sharper
case — `spec.md`'s Durable Outputs row is working material and *could* have been
corrected in place, but T5's `Touches` is pinned and still carried the
prohibited file.

**The amendment was mechanically available here and would not have been on the
sibling spec.** `contract-amendment` refuses when a completed task has no
evidence binding; `completed_task_ids` is empty for this run, so that guard does
not fire. It is legal only from `CODE-IMPLEMENTATION`, so the route out of
`CODE-REVIEW` was `findings-remain` (seq 20), with round 3's twelve sustained
fingerprints recorded against that sequence first.

Cost accepted by the owner: the run returns to `SPEC-PLAN-DRAFTING` and walks
back up through both human approval gates, a re-approval and a re-schedule.
Review retry count stands at 3 of 5.

## Amendment review round 1 — the amendment repeated the defect it was fixing

One blocker, two concerns, all sustained.

**The blocker is the partial-surface class, inside the repair for it.** Amendment
1 removed the `docs/specs/README.md` obligation from T5's `Touches` and from
`spec.md`'s Durable Outputs table — and left it standing in `plan.md`'s own
**Durable-output map** at line 51, a third table carrying the same obligation.
Two surfaces out of three, in an amendment whose entire purpose was correcting an
impossible obligation. The walk was performed on the spec and on the task, and not
on the plan's own summary table.

**Two working-material claims still said "four".** The Repository anchors listed
four literal enumerations and the Risks section warned that "adding the package to
three of four leaves a hole". Six are required, and the risk is sharper than it was
written: two of the six are not surfaces AC-0031 names, so satisfying the criterion
literally is not sufficient. Both are working material under the plan's own header
and were corrected in place without a second amendment.

**AC-0055's control only proved half of what the criterion says.** The criterion
says "a `[telemetry]` setting"; the test only supplied an undeliverable setting
from the repository scope. The merge pulls a user value in whenever the repository
file omits the key, so the same refusal must hold from either side — and the user
file is the one this catalogue trusts less. A second case now covers it, and
narrowing the implementation to `set(repo_settings)` kills it.

## Amendment review round 2 — no blockers, and a fourth surface

Zero blockers, three concerns, one nit; all applied.

**The four-versus-six claim had a fourth surface.** Round 1 found it in the
Durable-output map; round 2 found it again in `spec.md`'s Assumptions source
list, which still cited the original four line references. Four surfaces of one
claim, found across two rounds, each round finding the ones the previous repair
missed. The claim is now stated once with its full enumeration in each of the
four places that carry it.

**One concern overstated its risk, and the mutation is why we know.** The
reviewer held that the AC-0055 controls "would remain green" if the sender grew
a route for the setting they use. Measured: adding `compression` to the
deliverable set **kills** both controls, because they expect a raise. The failure
is loud, not silent. What the concern gets right is that the failure would be
*confusing* — it looks like a broken criterion when it is stale test data. A
named assumption test now says so in its own failure message.

**T2's `no stub` record named an outcome it did not carry.** `spec.md` promises
that every no-stub record names its discovery predicate and proof obligation;
AC-0055 had been added to T2's `Tests` list but not to that record's required
outcome. Both now name the refusal, from either scope.

**AC-0055 carried its own provenance.** The amendment date and the fail-open
rationale sat inside the criterion, where they affect no gate. Moved out; the
criterion now states the obligation and nothing else.

## Amendment 1 was narrowed, because a completed task's section is frozen

`approve-plan` refused the full amendment:

```
approve-plan: completed task section changed: T2, T4
```

`validate_completed_task_sections` exists to "return a stable refusal when an
amended plan rewrites completed work", and both T2 and T4 were recorded complete
by the wave advances. **The amendment tried to rewrite the contract of work whose
acceptance had already been recorded, and the cohort is designed to refuse that.**

The only way to land it whole was `loop-cohort reset`, which deletes `state.json`:
three review rounds, three review retries, twelve current and seven previous
finding fingerprints — the baseline that detects a finding recurring across
rounds — the completed-task evidence, and the amendment history. That is the same
trade the sibling spec declined, and for the same reason: a reset is a
re-approval in substance, not a repair. **The owner chose to keep the audit trail
and narrow the amendment.**

What landed, and what did not:

| Correction | Outcome |
| --- | --- |
| T5's `Touches` loses `docs/specs/README.md` | **landed** — T5 was never completed |
| the Durable Outputs row becomes Not applicable | **landed** — working material |
| the plan's Durable-output map loses the same row | **landed** — not a pinned field |
| the four-versus-six count, in all four places | **landed** — working material |
| T4's `Touches` gains its two real surfaces | **withdrawn** — T4 is complete and frozen |
| AC-0055 for the undeliverable-setting refusal | **withdrawn** — a criterion needs a task entry, and its only honest home is T2, which is frozen |

T2 and T4 were restored to their pre-amendment bytes exactly, verified by
comparing each section's text against `fb24b7dd2`.

**The behaviour AC-0055 would have governed still ships and is still tested**, with
two controls covering both layout scopes and a third pinning the assumption they
rest on. What it lacks is a criterion. B4 and B6 therefore return to ledger
dispositions — recorded, evidenced, and visible to the next reader, which is what
this file is for.

**AC-0055 is listed as retired even though it was never approved.** The identifier
reached pushed history, so leaving it unlisted would let a future author reuse it.
Identity is append-only.

**The lesson is about ordering, not about the guard.** An amendment that corrects a
task's contract has to happen before that task's completion is recorded, or not at
all. By the time a defect in T4's `Touches` was visible — which took implementing
T4 to discover — T4 was already complete. A contract error found by doing the work
may be unfixable in the contract, and the honest response is to record it rather
than to destroy the record of how it was found.
