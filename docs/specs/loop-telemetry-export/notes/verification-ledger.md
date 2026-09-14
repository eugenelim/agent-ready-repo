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
