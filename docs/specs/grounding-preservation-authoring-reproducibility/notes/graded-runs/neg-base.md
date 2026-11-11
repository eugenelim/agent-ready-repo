## Summary

I wrote a Draft spec and plan under `docs/specs/trim-label-inline/`. They cover inlining `_trim_label` into `render_label` without changing any output.

**Verdict: the shared-substrate preservation expansion does not fire.**
- A reference search for `_trim_label` across `/tmp/gpar-base-neg/work` found exactly 2 hits: the definition at `evals/files/isolated_helper.py:4` and its only caller at `evals/files/isolated_helper.py:9`.
- The test file only imports `render_label`.
- That is the reference's "private helper with a single caller" exclusion. The helper also belongs to no model, registry, graph, index, schema, namespace or collection.
- So I built no consumer map and added no preservation criteria. The ordinary step-3 anchors apply.
- No code-intelligence provider was used. The repository-native baseline settled the question.

**Evidence I gathered (`new-spec` step 3):**
- **Grounding inquiry:** the `repository-grounding` discovery run exited 0. It found no scoped rules, no path references and no runner gates. It found no surfaces either: there is no `AGENTS.md`, no adapt files and no architecture reference. Git is unavailable, so the phrase-pin and gates probes reported "unavailable".
- **Base-revision probe (read-only):** I called the unrefactored `render_label` on six inputs, and those outputs are the values in AC-0001. Python is 3.15.0, and `pytest` is not installed.
- **Spike (step 5a):** an inlined `label.strip()` body, run in memory, matched all 6 inputs.
- **Lint:** `lint-contract-item-alignment.py` found 0 findings. Its stale-assertion rule did not run because I passed `--no-since` (there is no git).

**What I would have asked a human, and the default I took:**
1. **Is inlining the refactor you want?** The alternatives are a rename or a reshaped helper. I chose inlining because it removes a layer, which the behavior-pin rule needs.
2. **Which test runner should the plan use?** No manifest names one, and I assumed `pytest`.

Both questions are recorded as open items in the spec's Assumptions.

**Gates not run:**
- The shaping review (step 6) is blocked: `BLOCKED: spec shaping review — independent route unavailable` (subagents were not allowed). The spec stays at `Draft`.
- The spec-mode adversarial review (step 7) was not dispatched for the same reason.
- I made no edits to the fixture code or tests.

## docs/specs/trim-label-inline/spec.md

```markdown
# Spec: Inline the private label-trim helper

- **Status:** Draft
- **Owner:** unassigned
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A maintainer of `evals/files/isolated_helper.py` reads `render_label` without
following a one-use indirection, because the trim step sits inline in the only
function that uses it. Every caller of `render_label` gets the same string for
every input that it got before the refactor.

## What Changes

- The private helper `_trim_label` is removed, and its trim step is inlined
  into `render_label` — `evals/files/isolated_helper.py`.
- A behavior pin covering a fixed input set is added beside the existing test —
  `evals/files/test_isolated_helper.py`.

## Durable Outputs

No durable output applies. The change is internal to one module with one
private helper and one caller. It alters no user promise, product truth,
architecture boundary, decision, interface, operation, maintainer procedure,
or release record. The repository has no `AGENTS.md`, architecture reference,
or documentation surface that names this module.

Retention class for this spec and plan: PR-only. The PR reviewer is the only
required reader. The merged test file is the stable evidence owner after
closeout.

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| none | No role applies; see the rationale above | none | none | none | none |

## Agent Rules

### Always do

- Keep `render_label` importable as `from isolated_helper import render_label`
  with the signature `(label: str) -> str`.
- Pin `render_label`'s output on the unrefactored code before moving any
  structure, and keep that pin green after each step.
- Keep the existing test `test_render_label_trims_outer_whitespace` unedited.

### Ask first

- Any change to which characters are trimmed, or to the angle-bracket wrapping.
- Keeping a named trim helper instead of inlining it, or giving it a second
  caller. A second caller makes the helper shared, and the change then needs a
  fresh shared-substrate preservation check.

### Never do

- Add a new dependency, module, or file outside the two fixture files.
- Add a public name (one without a leading underscore) to
  `isolated_helper`.
- Edit the expected values in the behavior pin to match refactored output.

## Testing Strategy

- **AC-0001 — Behavior pin.** The refactor must preserve output, so the pin is
  taken on the unrefactored code and must stay green after it; a unit test
  over a fixed input table is the surface.
- **AC-0002 — Behavior pin.** The import path and signature are what the
  existing test and any caller bind to; an `inspect.signature` check plus the
  existing import is the surface.
- **AC-0003 — Goal-based check.** The module's public surface is a name set,
  checked by one assertion over the module namespace.
- **AC-0004 — Goal-based check.** Removal of the helper is a structural fact,
  checked by a search of the two fixture files.

## Acceptance Criteria

- [ ] **AC-0001.** `render_label` returns, for each input in this table, the
  output the unrefactored module returns:

  | Input (Python literal) | Output |
  | --- | --- |
  | `"  ready  "` | `"<ready>"` |
  | `"ready"` | `"<ready>"` |
  | `""` | `"<>"` |
  | `" \t\nx\n "` | `"<x>"` |
  | `"a b"` | `"<a b>"` |
  | `" ready "` | `"<ready>"` |

- [ ] **AC-0002.** `isolated_helper.render_label` is importable by that name
  and its signature is `(label: str) -> str`.
- [ ] **AC-0003.** The set of names in `isolated_helper` that do not start with
  an underscore is exactly `{"render_label"}`.
- [ ] **AC-0004.** The identifier `_trim_label` occurs in neither
  `evals/files/isolated_helper.py` nor `evals/files/test_isolated_helper.py`.

## Follow-ons

none

## Assumptions

- Product: whether inlining is the refactor the requester wants, rather than a
  rename or a reshaped helper — it would change AC-0004 and the T2 task
  (settled by: the requester).
- Technical: no manifest or runner names a test tool, and `pytest` is not
  installed in the authoring environment — the plan's `Done when` commands
  assume `pytest` (settled by: the maintainer naming the test runner).
```

## docs/specs/trim-label-inline/plan.md

```markdown
# Plan: Inline the private label-trim helper

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** none — non-structural. The repository has no
  `AGENTS.md`, architecture reference, manifest, or runner file. The construction
  path is `evals/files/test_isolated_helper.py`, which imports
  `render_label` directly.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in `docs/specs/trim-label-inline/notes/verification-ledger.md`.

## Approach

Pin first, then restructure. T1 adds a behavior pin to the existing test file
and proves it green on the unrefactored module. T2 inlines the trim step into
`render_label`, deletes `_trim_label`, and keeps the pin green. The riskiest
part is a quiet change in trimmed characters, such as `strip(" ")` in place of
`strip()`; the Unicode-whitespace row in the pin catches it.

## Constraints

- No ADR or RFC governs these files.
- `work-loop` PLAN step 7 behavior-pin discipline applies: pin green on the
  base first, keep it green after each step, and revert a restructure that
  removes no layer.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| none (spec rationale: internal one-caller helper) | T1, T2 | `evals/files/test_isolated_helper.py` green | close-work confirms the spec's `none` rationale still holds |

## Design (LLD)

### Design decisions

Traces to: AC-0001, AC-0004.

- **Inline rather than rename or reshape.** `_trim_label` has one caller and
  does one call, so inlining removes a layer, which the behavior-pin discipline
  requires of a restructure. It rests on this assumption: no other code calls
  the helper.
- **Shared-substrate preservation does not fire.** The change touches a private
  helper with a single caller. A reference search for `_trim_label` across the
  repository found exactly two hits: the definition at
  `evals/files/isolated_helper.py:4` and its only caller at
  `evals/files/isolated_helper.py:9`. The test file does not reference it. The
  helper is not a member of any model, registry, graph, index, schema,
  namespace, or collection that generic operations observe, so no consumer map
  or extra preservation criteria apply. If T2 finds a second caller, stop and
  take the "Ask first" route in the spec.
- **Pin values come from the base revision.** The table in AC-0001 was produced
  by calling the unrefactored `render_label`. A read-only spike also ran an
  inlined `label.strip()` body over the same six inputs, and all six matched.

Owned by: T1, T2.

## Tasks

### T1: Behavior pin green on the unrefactored module

**Depends on:** none

**Touches:** evals/files/test_isolated_helper.py

**Tests:**
- Behavior pin. A parametrized test in `evals/files/test_isolated_helper.py`
  drives `render_label` over the six-row input table and compares each result
  with the literal expected string. Covers AC-0001.
- Behavior pin. An assertion compares `str(inspect.signature(render_label))`
  with `"(label: str) -> str"`. Covers AC-0002.
- Goal-based. An assertion compares the set of non-underscore names in
  `vars(isolated_helper)` with `{"render_label"}`. Covers AC-0003.

**Done when:** every test in T1's `Tests:` passes against the unrefactored
`evals/files/isolated_helper.py` under `pytest evals/files`, and
`test_render_label_trims_outer_whitespace` is unedited.

### T2: Helper inlined with the pin still green

**Depends on:** T1

**Touches:** evals/files/isolated_helper.py

**Tests:**
- Behavior pin. T1's tests, unchanged, pass against the refactored module.
  Covers AC-0001, AC-0002, AC-0003.
- Goal-based. `grep -n "_trim_label" evals/files/isolated_helper.py
  evals/files/test_isolated_helper.py` prints nothing and exits 1. Covers
  AC-0004.

**Done when:** `pytest evals/files` passes and the `grep` in T2's `Tests:`
exits 1.

## Rollout

Pure-logic change: no flag, infrastructure, external system, or sequencing.
Reverting the T2 commit restores the helper.

## Risks

- The trim semantics could drift if the inlined call changes its argument. The
  Unicode-whitespace row in the pin is the check.

## Changelog
```
