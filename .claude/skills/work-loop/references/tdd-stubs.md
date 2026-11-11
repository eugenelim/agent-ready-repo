# TDD red test — writing and proving the red at EXECUTE

Loaded on demand from `work-loop` PLAN's *Design tests up front* step and from
EXECUTE's TDD line, in **full mode** only, for **TDD-mode tasks** only. Every
mode in `work-loop` PLAN step 7 other than TDD (goal-based, visual / manual QA,
behavior pin, measurement, infra/deploy) writes no red test here. Light mode's
lean path runs none of this.

A red test is an executable claim that fails; a prose mirror of the acceptance
criterion is not. At PLAN, a TDD task's `Tests:` names the behavior, the
boundary it is checked at, and the verification mode. The red test itself is
written and proven red at EXECUTE, so a vague or untestable criterion shows up
when EXECUTE tries to write it, and the plan never holds test code that the
implementation then contradicts.

## Procedure at EXECUTE

1. Detect the stack (see the recipe below) and mirror the existing tests'
   location and naming.
2. Write the red test at the real test location, one test function per
   criterion, named from the criterion and importing the contract types (or the
   plan's `## Design (LLD)` component names where the contract is thin).
3. Run it. It fails for the intended reason before production code changes.
4. Where a spec exists, the red's command and failing output go to the
   verification ledger.
5. Production changes drive the test green, deferred assertions and edge cases
   are completed, and refactoring holds the test fixed as its safety net.

An import failure of the not-yet-written target counts as red. Any other
collection, import, or setup error, or a timeout, does not: fix it, then run
again. If you cannot name the test function because the criterion is too
abstract to type a test against, that is the under-specification signal: surface
it as a finding and sharpen the spec rather than writing a hollow `TODO` test.

A seam the plan cannot ground before code exists is recorded
`implementation-discovered` with its discovery predicate, constraint, required
outcome, and verification mode. When code grounds it, the controller writes the
grounding into the plan's `## Design (LLD)` as a working-plan edit. Do not invent a helper, fixture, module, path,
or symbol to manufacture a test.

## The `stub` fence — supervisor red-proof input

Where a supervisor run executes a TDD task, the task's `Tests:` carries a `stub`
fence, and the supervisor materializes it unchanged and proves it red before the
implementer attempt. The **controller**, never an implementer attempt, writes
that fence as a **task-start revision**: an edit to the task's `Tests:` made
after the previous request's result is reported and before the `next` that
issues the task's first request. The supervisor commits the edit as one in-envelope
`replan` with no approval request, issues `write-stub`, runs the fence in a
scratch copy of the committed tree, and commits the stub only when it is red;
only then does `implement-task` follow. The approved plan does not need to
carry the fence, so plan review never has to guess it.

**Make no plan edit while an attempt is open**
([`supervisor.md`](supervisor.md#the-open-attempt-rule--when-the-plan-may-change)).
An implementer attempt that adds or changes a fence in its result is refused, and
nothing from that result is committed. A
supervisor task without a fence gets no supervisor-observed red proof, and
EXECUTE's red-first rule still applies to it.

A fence uses the `stub` info string inside the task's `Tests:` subsection, with
the path, the command that runs it, and the exit codes that count as red:

````markdown
- **Tests:**
  - **VI-1:** the order handler returns 201 with an id.

    ```stub path=tests/test_orders.py run="python -m pytest -q {path}" red-exit=1
    from orders.api import create_order
    ...
    ```
````

- `path` is repository-relative, with no `.` or `..` segment, drive, or backslash.
- `run` is split into arguments like a shell would, but runs without one; `{path}`
  expands to the stub path. It runs from the root of a scratch copy of the
  committed tree, with the stub files added.
- `red-exit` lists the exit codes that count as red, comma-separated, default `1`.
  Any other exit, a timeout, or a collection or setup error is not red.
- For the `stub` fence, the payload is the fenced lines with the fence's own
  indentation removed, plus one terminal newline, and the file at `path` must
  match that byte identity. A blank line before the closing fence is refused,
  and a plan carrying `stub` fences uses LF line endings.

A task may carry several `stub` fences; each must be red. A fence the
supervisor refuses as `stub-not-red` is either made to fail for the intended
reason or removed, and the recovery has its own steps: the refusal closes the
`write-stub` attempt with nothing from it committed, the supervisor discards the
files the attempt left (a path it could not remove is named in `status` and
blocks every step until you remove it or restore it to `HEAD`), and the next
edit to the plan opens a `human-decision` carrying that edit's diff. A named
human confirms or declines those exact bytes; a confirmed edit is committed as
a `replan`, and a declined one is recorded and committed nowhere, so restore the
files to `HEAD` before the stub runs again.
[`supervisor.md`](supervisor.md) § *Recovering from a stub that is not red* has
the commands.

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
assertion (status, shape — durable) is the first red test;
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

## Worked example — Python / pytest

AC under test: *"`create_order` returns a 201 response whose body carries the
created order's id."* The id's value isn't knowable until the handler exists, so
this is a **shape** assertion with a placeholder for the value — paired with a
positive assertion (a 201 is actually produced) so the stub goes red against an
absent handler.

```python
# create_order returns 201 with the created order id.
# The status and the *presence* of an id are the durable contract surface
# (asserted now); the exact id value is construction-level detail (built out
# in EXECUTE green).
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

Against an absent `create_order`, the import fails: the target's import failure
is **red**, and the test collects once the module exists. At PLAN, the task's
`Tests:` records only the behavior, the boundary, and the mode:

```
Tests:
- Criterion 3: the handler returns 201 and an id, checked at the in-process handler
  boundary; TDD.
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
  inputs: the red test is written at EXECUTE, before production code, from spec +
  contract; `quality-engineer`'s test-author mode reviews **after**
  implementation, from code + spec. Both can coexist on one spec.
- **No new artifact, no new gate.** The red test lives in the repository test
  tree; the coverage signal is the set of `Tests:` subsections.
- **Full-mode, TDD-tasks-only.** Every mode in `work-loop` PLAN step 7 other
  than TDD, and all of light mode, writes nothing here.
