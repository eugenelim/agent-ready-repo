# Deliverable: label-trim-refactor spec and plan

## Result

The change does **not** trigger a shared-substrate preservation expansion. `_trim_label` is a private helper with a single caller, which is the reference's first named exception. One reference search over the whole supplied tree found it only at its definition (`evals/files/isolated_helper.py:4`) and its one call inside `render_label` (`evals/files/isolated_helper.py:9`). So the ordinary step-3 anchors apply, and the plan builds no consumer map and no extra preservation criteria.

Files written in the working directory:

- `docs/specs/label-trim-refactor/spec.md` (Status: Draft)
- `docs/specs/label-trim-refactor/plan.md` (Status: Drafting)

## Why the predicate does not fire

- The predicate fires only when the change becomes a member of a model, registry, graph, index, schema, namespace, or collection that generic operations observe without opt-in.
- `_trim_label` belongs to no such structure. The only shared container it sits in is the module namespace. The module has no `__all__`, and `from isolated_helper import *` skips underscore names, so no generic import path observes it.
- The one importer in the tree, `evals/files/test_isolated_helper.py`, imports only `render_label`.
- No code-intelligence provider is installed. The exception needs only one reference search, so the repository-native search settles it without a provider.
- The determination holds only while the helper keeps one caller and stays unexported. The spec puts any change to that under Ask first, and plan task T2 re-runs the reference search as a scope guard.

## Assumption checkpoint (step 3)

Probe #1 (read-only, run on the unmodified base with `python3 -I -B`, Python 3.15.0):

```
'  ready  ' -> '<ready>'
'ready' -> '<ready>'
'' -> '<>'
'   ' -> '<>'
'\t a b \n' -> '<a b>'
'\xa0x\u2003' -> '<x>'
'<x>' -> '<<x>>'
__all__ defined: False
existing test_render_label_trims_outer_whitespace: passed
```

```
ASSUMPTIONS I'M MAKING:

## Verified
- Technical: `_trim_label` has exactly one caller, `render_label` (grep -rn "_trim_label" over the tree: 2 hits, isolated_helper.py:4 and :9)
- Technical: the module's public names are exactly `render_label`, and it has no `__all__` (probe #1 above)
- Technical: `render_label` strips Unicode whitespace too, such as U+00A0 and U+2003 (probe #1 above)
- Technical: the existing test passes on the base (probe #1 above: called directly)
- Process: no AGENTS.md, ADR, RFC, manifest, or runner governs the tree (repository-grounding discovery run: scoped rules, path refs none found; gates unavailable, no runner file; git unavailable)

## Unverified
- Product: the refactor's target shape (rename, inline, typing, docstring, other) is not stated
- Technical: no test runner or gate command is declared, and pytest presence was not checked
```

Assumed sign-off, since this run cannot wait for a human: the refactor is behavior-neutral, and its exact shape is left to T2's local method. Highest-stakes item: the single-caller fact, because the whole no-expansion determination rests on it. Both Unverified items stay in the spec's `## Assumptions`.

## Grounding and checks

- `repository-grounding` discovery over both fixture files: no governing files, no path references, phrase pins and gates unavailable (input missing, not a clean result), git unavailable. Its path-reference probe misses the bare-name import `from isolated_helper import ...`, so the grep above is the reference search the determination relies on.
- Step 5a spike (throwaway, not committed): all 7 planned AC-0001 cases and the AC-0002 public-name check pass on the base.
- `lint-contract-item-alignment.py --no-since`: pass, 0 findings. Blind spot: rule 9 (reworded-criterion check) did not run, because the tree has no git base.

## Review status

- Shaping review (step 6): `BLOCKED: spec shaping review — independent route unavailable`. This evaluation confines work to two directories, so no isolated reviewer was dispatched. The spec stays `Draft`.
- Adversarial review (step 7): a matching `adversarial-reviewer` is installed in the projection but was not run, for the same reason. Approval should not be sought until both reviews return clean.
- Reminder (step 8): keep one home per fact, and keep the spec body in present tense. When implementation diverges, fix the spec in the same change.

---

## spec.md

# Spec: label-trim-refactor

- **Status:** Draft
- **Owner:** <owner-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

A maintainer of `evals/files/isolated_helper.py` gets a cleaner private
`_trim_label` helper without any caller seeing a difference. Success means
`render_label` returns the same string as the base revision for every input in
the characterization set, and the module's public names stay exactly
`render_label`.

## What Changes

- The body of the private helper `_trim_label` is refactored — `evals/files/isolated_helper.py`.
- Characterization tests pin `render_label` output taken from the base revision — `evals/files/test_isolated_helper.py`.
- No other file, caller, export, or dependency moves.

## Durable Outputs

none — the change is a behavior-neutral edit to a private helper with one
caller. It makes no user-facing promise, changes no interface, and the tree has
no architecture, guide, or changelog surface for it to keep current. The
characterization tests are the only lasting evidence, and they live with the
code. Retention class: local-only, in this working directory.

## Agent Rules

### Always do

- Take every expected value in the characterization tests from the base revision's `render_label` output, not from the refactored code.
- Keep `_trim_label` private (leading underscore) with `render_label` as its only caller.
- Keep `test_render_label_trims_outer_whitespace` byte-for-byte unchanged and passing.

### Ask first

- Any change that gives `_trim_label` a second caller, exports it, or lists it in an `__all__`; that reopens the shared-substrate preservation determination.
- Any change to what `render_label` returns for any input, including which characters count as whitespace.

### Never do

- Add a new module, package, file outside `evals/files/`, or third-party dependency.
- Change the signature or public name of `render_label`.
- Edit an existing assertion to make a refactor pass.

## Testing Strategy

- **Characterization (AC-0001).** TDD: the output of a pure function over a fixed input set is a compressible invariant, so a parametrized unit test with base-revision expected values reds on any behavior drift.
- **Public surface (AC-0002).** Goal-based check: one import-and-list probe of the module's non-underscore names decides it directly.

## Acceptance Criteria

- [ ] **AC-0001.** `render_label` returns exactly these values, taken from the base revision: `"  ready  "` → `"<ready>"`, `"ready"` → `"<ready>"`, `""` → `"<>"`, `"   "` → `"<>"`, `"\t a b \n"` → `"<a b>"`, `"\u00a0x\u2003"` → `"<x>"`, `"<x>"` → `"<<x>>"`.
- [ ] **AC-0002.** The names in `isolated_helper` that do not start with an underscore are exactly `{"render_label"}`, and the module defines no `__all__`.

## Follow-ons

none

## Assumptions

- Product: the requested refactor shape is not stated (rename, inline, typing, docstring, or other) — it changes only T2's local method, unless it adds a caller or export, which reopens the preservation determination (settled by: requester).
- Technical: no test runner or gate is declared in the tree, and `pytest` presence was not established — T1 and T2 may need a stated command to run the suite (settled by: requester or repository owner).

---

## plan.md

# Plan: label-trim-refactor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** none — non-structural. The only anchors are `evals/files/isolated_helper.py` (definition line 4, sole call site line 9) and `evals/files/test_isolated_helper.py` (one test). No `AGENTS.md`, architecture source, manifest, or runner file exists in the tree.

## Approach

Pin current behavior first, then refactor. T1 adds characterization tests that
pass on the unmodified base. T2 refactors `_trim_label` and must leave T1's
suite green. The riskiest part is a quiet whitespace change: `str.strip()` with
no argument also strips Unicode whitespace such as U+00A0 and U+2003, so a
refactor to `strip(" ")` or a regex on `\s` with different flags would change
output. AC-0001 includes those inputs for that reason.

## Constraints

- No ADR or RFC governs this tree.
- Shared-substrate preservation (`new-spec` `references/shared-substrate-preservation.md`) does not fire; see Design decisions. Ordinary step-3 anchors apply, and no consumer map or extra preservation criteria are built.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| none (spec § Durable Outputs) | T1, T2 | characterization tests in `evals/files/test_isolated_helper.py` | T1 and T2 `Done when` observed green |

## Design (LLD)

### Design decisions

- **Preservation predicate does not fire.** `_trim_label` is a private helper with a single caller. One reference search over every file in the tree for `_trim_label` (before this spec existed) found only its definition (`isolated_helper.py:4`) and its one call inside `render_label` (`isolated_helper.py:9`). It is not a member of a model, registry, graph, index, schema, or collection that generic operations read. The module namespace is the only shared container it sits in, and `from isolated_helper import *` skips underscore names because the module defines no `__all__`. Rests on: the helper keeps one caller and stays unexported; T2's reference search guards that.
- **No code-intelligence provider.** None is installed, so the determination rests on repository-native search alone. That is sufficient here: the exception needs one reference search, not a provider.
- **Expected values come from the base revision.** They were recorded by running `render_label` on the unmodified file, so the oracle cannot drift with the implementation. Rests on: T1 is committed before T2 touches the helper.
Traces to: AC-0001, AC-0002.

Owned by: T1, T2

## Tasks

### T1: Characterization tests for render_label are green on the base revision

**Depends on:** none

**Touches:** evals/files/test_isolated_helper.py

**Tests:**
- AC-0001: one parametrized test in `evals/files/test_isolated_helper.py` over the seven input/output pairs, calling `render_label` at its public import. TDD mode.
- AC-0002: one test that lists `isolated_helper`'s non-underscore names and asserts they equal `{"render_label"}` and that `__all__` is absent. Goal-based mode.
- `test_render_label_trims_outer_whitespace` stays byte-for-byte unchanged.

**Done when:** every `Tests:` item above passes against the unmodified `isolated_helper.py`.

### T2: Refactored _trim_label keeps the T1 suite green

**Depends on:** T1

**Touches:** evals/files/isolated_helper.py

**Tests:**
- AC-0001, AC-0002: the full T1 suite, unchanged, passes after the refactor.
- Scope guard for the preservation determination: a reference search for `_trim_label` across every `*.py` file in the tree finds exactly the definition and one call inside `render_label`. Any other hit stops the task and goes to Ask first.

**Done when:** the T1 suite is green on the refactored file, `evals/files/test_isolated_helper.py` has the same SHA-256 as at T1's completion (the tree has no git), and the `*.py` reference search returns exactly two hits.

## Rollout

Pure-logic, local change: no flag, infrastructure, external system, or
deployment sequencing. Rollback is reverting T2.

## Risks

- A Unicode-whitespace regression from a narrower strip; covered by AC-0001's U+00A0 and U+2003 inputs.

## Changelog
