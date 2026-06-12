# TDD stub generation — turning a TDD-mode AC into a compilable red test

Loaded on demand from `work-loop` PLAN's *Design tests up front* step, in
**full mode** only, for **TDD-mode tasks** only. Goal-based and manual-QA tasks
generate no stub — they record `no stub (mode)` in their `Tests:` subsection and
move on. Light mode's lean path runs none of this.

This reference turns the loop's existing "write construction tests up front"
obligation from *prose* into a **compilable, validated red stub** in
`plan.md`'s per-task `Tests:` subsection. The payoff is timing: a vague or
untestable acceptance criterion shows up **mechanically at PLAN** — the moment
you cannot type a test against it — instead of as a surprise mid-EXECUTE, the
most expensive place to discover an AC is under-specified. The stub is consumed
unchanged by EXECUTE's red step; usually the red test is then already written.

This is one owner — the loop — progressing across its own phases, not a second
test-design tool with a handoff. The full progression is the existing
red-green-refactor with the red step pulled forward and made compilable:

> **red stub (PLAN) → green (EXECUTE) → complete the stub's deferred
> assertions and edge cases (EXECUTE) → refactor with the tests as the safety
> net (EXECUTE).**

Generation is **single-pass with one bounded syntax-correction pass** — never an
iterate-to-coverage retry loop. A gap goes back to the spec author as a sharper
PLAN, not into a regenerate loop.

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
assertion (status, shape — durable) is the red stub written now; the
**construction-level** detail (exact values, edge cases — revisable) is built
out in EXECUTE, *before* the refactor step (which holds the tests fixed).

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
- each TDD-mode task's **`Tests:` prose** in `plan.md` — the construction-test
  intent you are making compilable;
- the **`Contract:`** file if the spec names one (its types/operations are what
  the stub imports and asserts against). If the spec names no contract, fall
  back to the component names in the plan's `## Design (LLD)`.

For each TDD-mode AC, name the test function after the criterion. If you cannot
even name the function — the AC is too abstract to type a test against — that
**is** the under-specification signal: surface it as a finding ("AC N is not
concrete enough to stub") and sharpen the spec, rather than writing a hollow
`TODO`-test.

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

One stub **file per plan task** (the grouping default), one **test function per
AC**, named from the criterion, importing the contract types (or placeholders
where the contract is thin). Apply the stub-fullness rule above: a full red
assertion where the AC pins behaviour, a shape assertion with a placeholder
otherwise. Never a bare `TODO`.

#### Stub marker convention (defined once)

Every stubbed test and its plan entry carry two halves of one marker, so a
reader (and the EXECUTE step) can tell a pre-written red stub from a hand-rolled
test:

1. **In the test file** — a comment on the test (or the file header) of the
   form `# STUB: AC<n>` (or `// STUB: AC<n>` in brace-comment languages),
   naming the acceptance criterion the function pins. Use your stack's line-
   comment token; the `STUB:` keyword and the `AC<n>` reference are the fixed
   parts.
2. **In `plan.md`** — a `stub: true` field in that task's `Tests:` subsection,
   so the plan records that the construction test was materialised as a
   compilable stub (vs. left as prose). A task that degraded (see Validate)
   records `stub: draft (uncompiled)` with the reason instead.

Everywhere else that refers to "the stub marker" means exactly this pair.

### 4. Validate

Run **one** language-appropriate syntax/compile pass, then **one** bounded
correction pass — no retry loop:

| Language     | Compile / collect check          |
| ------------ | -------------------------------- |
| TypeScript   | `tsc --noEmit`                   |
| Python       | `python -m py_compile` (or `pytest --collect-only`) |
| Java         | `javac`                          |
| Go           | `go build` / `go vet`            |

A stub that compiles has a typed, parseable signature against the AC surface —
that compile **is** the mechanical proof the AC is concrete enough to test.

**Degrade, never block.** If stack detection fails or an unusual test setup
breaks the compile check, emit the stub as `draft (uncompiled)` with the reason
noted in its `Tests:` subsection, and **surface** it. The coverage/testability
signal survives even when compilation doesn't. A non-compiling stub is a signal
for the human and the adversarial reviewer at the plan gate — it does **not**
block the plan (the plan gate runs no compiler; it reads the surfaced result).
Where an AC's true surface is only reachable out-of-process (a CLI exit code,
say), assert the nearest in-process data contract and record the out-of-process
assertion as a deferred assertion for the full test — again, never a bare
`TODO`.

### 5. Record

Write each stub into its task's `Tests:` subsection in `plan.md`, flagged with
the `stub: true` field from the marker convention above. No separate file — the
coverage signal is the set of `Tests:` subsections plus a one-line covered /
uncovered / `no stub (mode)` tally rolled into the spec's Testing Strategy.
There is no `coverage-matrix.md`.

## Worked example — Python / pytest

AC under test: *"`create_order` returns a 201 response whose body carries the
created order's id."* The id's value isn't knowable until the handler exists, so
this is a **shape** assertion with a placeholder for the value — paired with a
positive assertion (a 201 is actually produced) so the stub goes red against an
absent handler.

```python
# STUB: AC3 — create_order returns 201 with the created order id
# Generated at PLAN; lives in plan.md's T<n> Tests: subsection. The status and
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
- test_create_order_returns_201_with_order_id — asserts 201 + id shape (AC3)
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
  inputs: stubs are generated **in PLAN** from spec + contract, *before* code;
  `quality-engineer`'s test-author mode reviews **after** implementation, from
  code + spec. Both can coexist on one spec.
- **No new artifact, no new gate.** Stubs ride the existing per-task `Tests:`
  subsections and the existing plan-approval / pre-EXECUTE-review flow.
- **Full-mode, TDD-tasks-only.** Goal-based and manual-QA tasks, and all of
  light mode, generate nothing here.
