I drafted a spec and plan for inlining the private helper `_trim_label`. **This does not trigger a shared-substrate preservation expansion.** The reference names "a private helper with a single caller" as an exception, and one repository-wide search settles it here:

- `_trim_label` appears only at its definition (`evals/files/isolated_helper.py:4`) and in its one caller, `render_label` (`evals/files/isolated_helper.py:9`).
- The test file imports only `render_label`.
- The module has no `__all__`, so a star import already skips the underscore name.

So the plan has no consumer map and the spec has no extra preservation criteria. The reasoning is recorded in the plan's Design decisions. The missing code-intelligence provider removes no evidence, because the search is repository-native.

## How I got there
- **Skill followed:** `new-spec`, plus its `references/shared-substrate-preservation.md`, which owns the fire-or-not decision.
- **Repository check:** the `repository-grounding` discovery run found no scoped rules, no path references, no runner file, and no git history. There is no `AGENTS.md`, and `adapt-to-project` is not installed.
- **Behavior probe:** a read-only check on the current code confirmed that `render_label(s) == f"<{s.strip()}>"` holds for all 7 frozen inputs, including two non-ASCII whitespace characters. The probe left a `__pycache__` folder, which I deleted.
- **Runtime:** `python3` is 3.15.0 and has no `pytest`.
- **Lint:** `lint-contract-item-alignment.py` passes with 0 findings. Its reworded-criterion rule did not run because there is no git base.

## Questions I would have asked
No human was available, so I took a default for each and recorded it in the spec's `## Assumptions`:
1. **What should the refactor do?** The request names no goal. I assumed inlining the helper. Keeping, renaming or rewriting it instead would replace AC-0002.
2. **Which environment runs the tests?** The system Python has no `pytest`, so the characterization test cannot run until one is chosen.

## Reviews
- **Shaping review:** `BLOCKED: spec shaping review — independent route unavailable`, because subagents are not allowed in this run.
- **Adversarial review:** skipped, since no subagent dispatch was allowed.
- **Status:** the spec stays `Draft` and the plan stays `Drafting`. Nothing has been approved.

## docs/specs/label-trim-helper/spec.md

```markdown
# Spec: label-trim-helper

- **Status:** Draft
- **Owner:** <github-handle>
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
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer of `evals/files/isolated_helper.py` gets a module where label trimming lives directly in `render_label`, with no one-line private wrapper to read past. Every caller of `render_label` sees exactly the output it saw before the refactor.

## What Changes

- The private helper `_trim_label` is inlined into its only caller, `render_label` — `evals/files/isolated_helper.py`
- A characterization test pins `render_label` output on a frozen case set — `evals/files/test_isolated_helper.py`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| none | No role applies. The change is internal to one module, alters no user-facing promise, product truth, architecture, decision, interface, operation, maintainer procedure, or release history, and teaches no reusable lesson. The repository has no `AGENTS.md`, architecture document, or changelog to refresh. | none | work-loop | Characterization test green before and after the change | `close-work` confirms the test exists and passes on the final revision |

This spec and plan are repository-durable records at `docs/specs/label-trim-helper/`, readable by every resuming session, reviewer, and gate that reads the repository. Their post-closeout evidence owner is the characterization test in `evals/files/test_isolated_helper.py`.

## Agent Rules

### Always do

- Run the characterization test green on the unmodified module before editing `isolated_helper.py`.
- Keep `render_label` importable as `from isolated_helper import render_label` with the signature `(label: str) -> str`.
- Give `render_label` a docstring and keep its type annotations, as the changed code.

### Ask first

- Keeping `_trim_label` (renamed or rewritten) instead of inlining it.
- Changing the trimming rule itself, such as trimming only ASCII whitespace or collapsing inner whitespace.
- Editing or deleting the existing test `test_render_label_trims_outer_whitespace`.

### Never do

- Add a dependency, a new module, or a new file outside `evals/files/` and this spec directory.
- Add a public name to `isolated_helper`, or an `__all__` that exports a private name.
- Change the output of `render_label` for any input.

## Testing Strategy

- **TDD, characterization (AC-0001)** — The behavior to preserve is a compressible invariant over string inputs, so a test written green against the base revision and kept green after the change is the oracle.
- **Goal-based check (AC-0002, AC-0003)** — Each is settled by one command: a name lookup on the imported module, and an import plus signature inspection through the supported import surface.

## Acceptance Criteria

- [ ] **AC-0001.** `render_label` returns, for each input in this frozen case set, the value the base revision returns: `"  ready  "` → `"<ready>"`, `"ready"` → `"<ready>"`, `""` → `"<>"`, `" "` → `"<>"`, `"\t\nx  "` → `"<x>"`, `"a b"` → `"<a b>"`, `"<x>"` → `"<<x>>"`. Allowed delta: none. A sustained review finding against this criterion contradicts it.
- [ ] **AC-0002.** The imported `isolated_helper` module has no attribute named `_trim_label`.
- [ ] **AC-0003.** `from isolated_helper import render_label` succeeds, and `inspect.signature(render_label)` is `(label: str) -> str`.

## Follow-ons

none

## Assumptions

- Product: the refactor's target shape is assumed to be inlining `_trim_label`, because the request names no goal — keeping, renaming, or rewriting the helper would replace AC-0002 (settled by: the requesting owner).
- Technical: the system `python3` (3.15.0) has no `pytest`, and the repository declares no test runner or environment — the characterization test cannot run until an environment with `pytest` is chosen (settled by: the repository owner).
```

## docs/specs/label-trim-helper/plan.md

```markdown
# Plan: label-trim-helper

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** none — non-structural. The repository holds two files, `evals/files/isolated_helper.py` and `evals/files/test_isolated_helper.py`, and no `AGENTS.md`, architecture source, manifest, or runner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/label-trim-helper/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Pin the current behavior first, then change the code under that pin. T1 adds a characterization test that passes on the unmodified module. T2 inlines `_trim_label` into `render_label` and keeps the T1 test and the existing test green. The only risk is a silent change to which characters count as whitespace, and the frozen case set includes non-ASCII whitespace to catch it.

## Constraints

- No ADR, RFC, or scoped guidance governs these paths. The grounding inquiry found no scoped rules, no path references, and no runner file.
- The system `python3` is 3.15.0 without `pytest`. Tests run from an environment that provides `pytest`; choosing it is an open item in the spec's Assumptions.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| none (see spec Durable Outputs) | T1, T2 | Characterization test in `evals/files/test_isolated_helper.py` | Test passes on the final revision |

## Design (LLD)

### Design decisions

- **Shared-substrate preservation does not fire.** One reference search for `_trim_label` across the whole repository finds only its definition (`evals/files/isolated_helper.py:4`) and its single caller (`evals/files/isolated_helper.py:9`). The test file imports only `render_label`. The module defines no `__all__`, so a star import already skips the underscore name. This is the reference's named exception, "a private helper with a single caller", so no consumer map or extra preservation criteria are built. Rests on: no consumer outside this repository imports the private name, which the underscore convention places outside the supported surface. Traces to: AC-0001, AC-0002.
- **Inline rather than keep the helper.** A one-line wrapper over `str.strip` with one caller adds a name and no meaning. Rests on: the owner confirming inlining as the goal (spec Assumptions).

Owned by: T2

### Behavior & rules

- Trimming is `str.strip()` with no argument, which strips all Unicode whitespace, not only ASCII. The inlined form must call the same method so `" "` and `" "` still strip. A read-only probe on the base revision confirmed that `render_label(s) == f"<{s.strip()}>"` for all seven AC-0001 inputs. Traces to: AC-0001.

Owned by: T1, T2

## Tasks

### T1: Characterization test green on the unmodified module

**Depends on:** none

**Touches:** evals/files/test_isolated_helper.py

**Tests:**
- AC-0001: a parametrized test in `evals/files/test_isolated_helper.py` over the seven frozen input/output pairs, calling `render_label` through `from isolated_helper import render_label`. Expected values are literals taken from the base revision, never computed from `str.strip` in the test. TDD mode, characterization variant: it must pass before any production edit.

**Done when:** the T1 test passes against the unmodified `isolated_helper.py`, recorded in the verification ledger.

### T2: Helper inlined with behavior unchanged

**Depends on:** T1

**Touches:** evals/files/isolated_helper.py

**Tests:**
- AC-0001: the T1 test and the existing `test_render_label_trims_outer_whitespace` stay green after the edit.
- AC-0002: goal-based — `python3 -I -c "import sys; sys.path.insert(0, 'evals/files'); import isolated_helper as m; assert not hasattr(m, '_trim_label')"` exits 0.
- AC-0003: goal-based — `python3 -I -c "import sys, inspect; sys.path.insert(0, 'evals/files'); from isolated_helper import render_label; assert str(inspect.signature(render_label)) == '(label: str) -> str'"` exits 0.

**Done when:** every check in this task's `Tests:` passes, recorded in the verification ledger.

## Rollout

Pure-logic change with no flag, infrastructure, external system, or deployment order. Rollback is reverting the T2 commit.

## Risks

- The test file imports `isolated_helper` by bare module name, so it depends on `pytest` placing `evals/files` on `sys.path`. Running from another directory or import mode can fail the import before any assertion runs.

## Changelog
```
