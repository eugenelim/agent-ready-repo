# TDD stub generation — turning a TDD-mode AC into a compilable red test

Loaded on demand from `work-loop` PLAN's *Design tests up front* step, in
**full mode** only, for **TDD-mode tasks** only. Goal-based and manual-QA tasks
generate no stub — they record `no stub (mode)` in their `Tests:` subsection and
move on. Light mode's lean path runs none of this.

This reference turns the loop's existing "write construction tests up front"
obligation from behaviour-restating *prose* into exact, executable test code in
`plan.md`'s per-task `Tests:` subsection. A stub is an executable claim that
fails; a prose mirror of the acceptance criterion is not. The payoff is timing:
a vague or untestable criterion shows up mechanically during PLAN, without
leaving an intentionally failing file in the repository.

## Lifecycle

PLAN stores the exact stub code in `plan.md` and validates its syntax and red
from disposable scratch. The plan records the code, its AC mapping, and the
validation result; it does not write into the repository's test tree. A
`spec-plan` run ends after approval, and spec-plan writes no repository test
file. Put plainly: spec-plan writes no repository test file. In code mode, only
after the engine enters `CODE-IMPLEMENTATION` does
EXECUTE materialize the approved block unchanged at the real test path, verify
byte identity, and prove the intended red. Production changes then drive the
test green, deferred assertions and edge cases are completed, and refactoring
holds the test fixed as its safety net.

For byte identity, the payload is the fenced code lines, excluding the fence
delimiter, with their line endings preserved and exactly one terminal newline.
A blank payload line immediately before the closing fence is extra code, not
the file-ending newline. Reject it instead of relying on Markdown rendering.

This is one owner — the loop — progressing across its own phases, not a second
test-design tool with a handoff.

Generation is **single-pass with one bounded syntax-correction pass** — never an
iterate-to-coverage retry loop. A gap goes back to the spec author as a sharper
PLAN, not into a regenerate loop.

## Legal PLAN dispositions

There are exactly two dispositions for a TDD task. For an already-grounded
callable seam or coherent TDD task family, write one compilable red
contract-surface assertion (`stub: true`); it need not encode the finished
edge-case matrix. When the callable seam can only be discovered during
implementation, record `no stub (implementation-discovered)` plus the discovery
predicate, constraint, required outcome, and verification mode. Do not invent a
helper, fixture, module, or symbol to manufacture a stub.
The record must name the `discovery predicate` and the later `proof obligation`.

## What a stub is — the stub-fullness rule

> A stub is **as much of the real failing test as the AC and contract honestly
> determine** — a *full* assertion where the AC pins exact behaviour, a
> *contract-surface (shape)* assertion otherwise. **Never less than a compiling
> assertion on the contract surface; never a bare `TODO`.**

"Stub" means a **compilable-but-failing test**, not a test double / fake
dependency. It is a floor, not a licence to write half a test:

- **Write the full failing test when the AC pins exact behaviour.** That is
  just classic TDD red, and it is preferred. *"Rejects an empty name with a
  `ValidationError`"* → assert exactly that.
- **Write a shape assertion when the AC fixes only the observable shape** and
  the exact value becomes knowable only once the code exists. *"Returns 201
  with the created order's id"* → assert the status and the *presence/type* of
  the id, with a placeholder for the value. Asserting a full value you cannot
  yet know is over-specification — the same trap `plan.md` construction tests
  avoid (revisable if they pin an internal detail the plan later changes).

This maps onto the contract-vs-construction split: the **contract-level**
assertion (status, shape — durable) is the exact stub code proved during PLAN;
the **construction-level** detail (exact values, edge cases — revisable) is
built out in EXECUTE, *before* the refactor step (which holds the tests fixed).

**Earning a red — assert the behaviour whose *absence* the stub must catch.**
A *positive-contract* AC ("X is produced / detected / returned") goes genuinely
red against a not-yet-written implementation — these make the strongest stubs.
A *pure-exclusion or invariant* AC ("malformed input is rejected", "the exit
code is unchanged") is trivially satisfied by an implementation that does
nothing, so on its own it cannot go red. Pair it with the positive case that
makes it falsifiable: assert that detection/handling *fires* on a real input,
then assert the exclusion/invariant alongside. A stub that passes against an
empty implementation is not yet a red test.

## The five phases

### 1. Parse

Read the inputs the stub is derived from:

- the spec's **Testing Strategy** — which ACs are TDD-mode (those are the only
  ones you stub);
- each TDD-mode task's **`Tests:` entry** in `plan.md` — the construction-test
  intent you are making compilable;
- the **`Contract:`** file if the spec names one (its types/operations are what
  the stub imports and asserts against). If the spec names no contract, fall
  back to the component names in the plan's `## Design (LLD)`.

For each TDD-mode AC, name the test function after the criterion. If you cannot
even name the function because the AC is too abstract to type a test against, that
**is** the under-specification signal: surface it as a finding ("AC N is not
concrete enough to stub") and sharpen the spec, rather than writing a hollow
`TODO`-test.

If the criterion is concrete but its verification mode does not admit a stub,
record `no stub (mode)` with the reason. That branch is not a licence to leave
an abstract criterion unsharpened, and it does not add prose in place of the
stub. A hard *surface* is not that branch: an out-of-process surface still
stubs the nearest in-process contract (see Validate).

### 2. Resolve stack

Detect the test framework, assertion library, and test-path convention so the
stub is framework-appropriate, mirroring how `new-spec` resolves the
implementation stack:

- **When a reference architecture doc is present**, conform to the framework it
  names — don't invent a parallel one.
- **Otherwise, detect from the repo**: lockfiles / manifests and existing test
  files (see the detection recipe below).
- **Elicit, don't invent.** When detection is ambiguous or the repo is
  greenfield, **ask** which framework to target. An invented framework is worse
  than one asked question.

### 3. Generate

Write one exact stub **code block per plan task** (the grouping default), with
one **test function per AC**, named from the criterion and importing the
contract types (or placeholders where the contract is thin). Apply the
stub-fullness rule above: a full red assertion where the AC pins behaviour, a
shape assertion with a placeholder otherwise. Never a bare `TODO`, and do not
create the repository test file during PLAN.

#### Stub marker convention (defined once)

Every stub block and its plan entry carry two halves of one marker, so a reader
(and the EXECUTE step) can identify the approved source before and after
materialization:

1. **In the plan-contained code block** — a comment on the test (or its header)
   of the form `# STUB: AC<n>` (or `// STUB: AC<n>` in brace-comment
   languages), naming the acceptance criterion the function pins. The same
   comment is present when EXECUTE copies the block into the test file. Use the
   stack's line-comment token; the `STUB:` keyword and the `AC<n>` reference
   are fixed.
2. **In `plan.md`** — the test function name plus its AC identifier and a
   `stub: true` field in that task's `Tests:` subsection. This is the `Tests:`
   entry, not a prose restatement of the behaviour.

Everywhere else that refers to "the stub marker" means exactly this pair.

### 4. Validate

Copy the code block to disposable scratch outside the repository test tree.
Run **one** language-appropriate syntax/compile pass. Run the execution or
collection pass that proves the intended red only in a bounded harness that
denies network access, applies a timeout, confines filesystem reads to the
repository and declared test dependencies, and confines writes to disposable
scratch plus explicitly declared test-harness side effects. Then allow **one**
bounded correction pass — no retry loop:

| Language     | Compile / collect check          |
| ------------ | -------------------------------- |
| TypeScript   | `tsc --noEmit`                   |
| Python       | `python -m py_compile` (or `pytest --collect-only`) |
| Java         | `javac`                          |
| Go           | `go build` / `go vet`            |

A stub that compiles has a typed, parseable signature against the AC surface;
the intended red proves the assertion is not vacuous. Record both results in
the plan and remove the disposable copy. Neither result authorizes a repository
test file during PLAN.

**Fail closed at plan approval.** If stack detection, compilation, or intended-
red validation fails, surface the exact failure and block plan approval. When
the required execution isolation is unavailable, a compile-only diagnostic is
allowed, but record the isolation downgrade and do not treat it as validated or
approvable. Proceed without a validated stub only when the obligation honestly
qualifies for `no stub (implementation-discovered)` and records its discovery
predicate and proof obligation; do not invent a third draft-stub disposition.
Where an AC's true surface is only reachable out-of-process (a CLI exit code,
say), assert the nearest in-process data contract and record the out-of-process
assertion as a deferred assertion for the full test — again, never a bare
`TODO`.

### 5. Record

Keep each exact code block and its stub reference — test function name plus AC
identifier — in the task's `Tests:` subsection in `plan.md`, flagged with the
`stub: true` field from the marker convention above. This replaces a prose
descriptor. An obligation without a stub records `no stub (mode)` and its
reason, not more prose. No repository test file exists yet; the coverage signal
is the set of `Tests:` subsections plus a one-line covered / uncovered /
`no stub (mode)` tally rolled into the spec's Testing Strategy. There is no
`coverage-matrix.md`.

## Worked example — Python / pytest

AC under test: *"`create_order` returns a 201 response whose body carries the
created order's id."* The id's value isn't knowable until the handler exists, so
this is a **shape** assertion with a placeholder for the value — paired with a
positive assertion (a 201 is actually produced) so the stub goes red against an
absent handler.

```python
# STUB: AC3 — create_order returns 201 with the created order id
# Stored and validated in PLAN's T<n> Tests: subsection. The status and
# the *presence* of an id are the durable contract surface (asserted now); the
# exact id value is construction-level detail (built out in EXECUTE green).
import pytest

from orders.api import create_order            # imported from the Contract / LLD
from orders.models import OrderRequest


def test_create_order_returns_201_with_order_id():
    resp = create_order(OrderRequest(item="widget", qty=1))

    assert resp.status_code == 201               # full assertion — AC pins this
    body = resp.json()
    assert "id" in body                          # shape: the id must be present
    assert isinstance(body["id"], str)           # ... and is a string id
    # value is construction-level — filled in EXECUTE once the handler assigns it
    EXPECTED_ID_PREFIX = "ord_"                   # placeholder for the real scheme
    assert body["id"].startswith(EXPECTED_ID_PREFIX)
```

Against an absent `create_order`, the import (or the call) fails — the stub is
**red**. It compiles under `python -m py_compile` (or collects under
`pytest --collect-only`), proving the AC was concrete enough to type a test
against. In `plan.md`, the task records:

```
Tests:
- test_create_order_returns_201_with_order_id (AC3)
  stub: true
```

## Stack-agnostic detection recipe

Detect the framework from the repo's own signals before generating — and elicit
when they conflict or are absent:

| Signal                                   | Likely framework / convention        |
| ---------------------------------------- | ------------------------------------ |
| `package.json` dev-deps `jest`/`vitest`  | Jest / Vitest; `*.test.ts` alongside src |
| `pyproject.toml` / `pytest.ini` / `tox`  | pytest; `tests/` or `test_*.py`      |
| `pom.xml` / `build.gradle` + surefire    | JUnit; `src/test/java/...`           |
| `*_test.go` files, `go.mod`              | Go `testing`; `_test.go` siblings    |
| `Cargo.toml`, `#[cfg(test)]` modules     | Rust `#[test]`; in-file test modules |

- Mirror the **existing tests'** location and naming rather than imposing a new
  layout.
- For an interface-bearing spec, import from the `Contract:` artifact so the
  stub's types track the contract; otherwise lean on the plan's `## Design
  (LLD)` component names.
- **Greenfield or ambiguous → ask.** Never guess a framework into the plan.

## Boundaries

- **Complements `quality-engineer`, doesn't replace it.** Different timing and
  inputs: exact stub code is authored and proved **in PLAN** from spec +
  contract, then materialized after `CODE-IMPLEMENTATION`; `quality-engineer`'s
  test-author mode reviews **after** implementation, from code + spec. Both can
  coexist on one spec.
- **No new artifact, no new gate.** Stubs ride the existing per-task `Tests:`
  subsections and the existing plan-approval / pre-EXECUTE-review flow.
- **Full-mode, TDD-tasks-only.** Goal-based and manual-QA tasks, and all of
  light mode, generate nothing here.
