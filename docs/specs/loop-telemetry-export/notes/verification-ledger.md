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
