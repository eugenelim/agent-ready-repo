# Spec and plan: label-trim-helper

## Result

This change does **not** trigger a shared-substrate preservation expansion. A shared-substrate expansion is the extra consumer map and preservation criteria `new-spec` requires when a change touches something many generic readers see. The `references/shared-substrate-preservation.md` predicate names "a private helper with a single caller" as a non-firing case, settled by one reference search. That search over the whole working tree finds `_trim_label` only at its definition (`evals/files/isolated_helper.py:4`) and its one call inside `render_label` (`evals/files/isolated_helper.py:9`). The test file imports only the public `render_label` (`evals/files/test_isolated_helper.py:1`). The helper belongs to no model, registry, graph, index, schema, namespace, or collection that a generic operation observes. So the ordinary step-3 anchors apply, and the plan has no consumer map and no extra preservation criteria. AC-0003 keeps the single-caller fact true after the refactor.

The spec and plan are drafted at `Status: Draft` / `Drafting`:

- `/tmp/c3-graded/work-isolated-private-change-does-not-expand-preservation-proof-head/docs/specs/label-trim-helper/spec.md`
- `/tmp/c3-graded/work-isolated-private-change-does-not-expand-preservation-proof-head/docs/specs/label-trim-helper/plan.md`

## Assumption checkpoint (step 3)

```
probe #1: python3 -I explore-grounding.py --root . --phase discovery evals/files/isolated_helper.py
  surfaces present: none · absent: .adapt-discovery.toml, .adapt-pending.md, .adapt-install-marker.toml, AGENTS.md, docs/architecture/reference.md
  git unavailable: tracked-set and co-change probes degrade
  scoped rules: none found · path refs: none found
  phrase pins: unavailable (too little signal) · gates: unavailable (no runner file found)
probe #2: grep -rn "_trim_label" .   -> isolated_helper.py:4 (def), isolated_helper.py:9 (call); no other hit
probe #3: base-revision outputs of render_label, via direct import (python3 -I)
  '  ready  '->'<ready>'  'ready'->'<ready>'  ''->'<>'  '   '->'<>'  '\tready\n'->'<ready>'
  ' a  b '->'<a  b>'  '\xa0ready　'->'<ready>'  signature: (label: str) -> str
probe #4: existing test_render_label_trims_outer_whitespace called directly -> pass
probe #5: python3 -c "import pytest" -> ModuleNotFoundError
```

ASSUMPTIONS I'M MAKING:

## Verified
- Technical: `_trim_label` has exactly one caller, `render_label`, and no other reference (probe #2)
- Technical: the helper is not a member of any generically observed substrate, so the preservation predicate does not fire (evals/files/isolated_helper.py, 9 lines)
- Technical: runtime is Python 3.15.0; current `render_label` behavior is `str.strip()` plus angle brackets (probe #3)
- Technical: no code-intelligence provider is exposed, so grounding uses the repository-native baseline only (task statement; probe #1)
- Process: no `AGENTS.md`, adapt-to-project discovery surface, ADR, RFC, or runner exists in the supplied tree (probe #1)

## Unverified
- Product: the concrete refactor (rename, inline, or rewrite) is not named in the request.
- Technical: no test runner is installed (probe #5), and no project gate is declared.
- Process: who approves the spec and signs off on Agent Rules is not recorded anywhere in the supplied tree.

Highest-stakes item: the single-caller fact, because it alone decides that no preservation expansion is needed. The procedure says to wait for a human here. Per the task, I assume these three Unverified items are accepted as open and continue. Shape `mixed`, pruned to two LLD sub-sections, is also assumed rather than confirmed.

## Gates and review status

- Contract-item alignment lint (step 8): pass, 0 findings, 1 spec checked. Rule 9 (stale assertion) did not run, because the tree has no git history (`--no-since`).
- Cheapest disconfirming evidence (step 5a): the existing test passes on the base revision, and the AC-0001 expected values match the base output (probe #3 and #4). Neither disconfirms the plan.
- Shaping review (step 6): `BLOCKED: spec shaping review — independent route unavailable`. This evaluation limits me to two directories, and a dispatched reviewer would not stay inside them. The spec stays at `Draft`.
- Adversarial review (step 7): not run for the same reason. No finding-adjudicator round exists.
- Human approval: not sought. Both reviews above must pass first.

Remaining before approval: run the shaping and adversarial reviews, name the concrete refactor, and name the test runner. Two reminders from step 8: keep one canonical home for each fact, and keep the spec body in present tense.

---

## spec.md

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
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

Maintainers of `evals/files/isolated_helper.py` get a cleaner private
`_trim_label` helper without any caller seeing a difference. Success is that
`render_label` returns exactly the string the base revision returns for every
input in the characterization set below.

## What Changes

- The body or name of the private helper `_trim_label` is restructured — `evals/files/isolated_helper.py`.
- A characterization test pins `render_label` output for a fixed input set — next to `evals/files/test_isolated_helper.py`.

## Durable Outputs

none — the change is a behavior-preserving edit to a private helper with one
caller. It alters no user-facing promise, product truth, architecture,
decision, interface, operation, procedure, or release record, so no lasting
record needs to be created or updated.

## Agent Rules

### Always do

- Keep `render_label(label: str) -> str` importable from `isolated_helper` with the same signature.
- Run the characterization test against the base revision before the refactor and keep it green after.

### Ask first

- Any change to `render_label` output, including for whitespace kinds outside the characterization set.
- Making the helper public, or calling it from a second site.

### Never do

- Import or call the private helper from any file other than `evals/files/isolated_helper.py`.
- Add a dependency, module, or file beyond the characterization test.
- Edit the expected values in a characterization test to match new output.

## Testing Strategy

- **Output preservation (AC-0001):** TDD, as a characterization test. Its expected values are literals taken from the base revision, so a behavior drift reds it.
- **Public surface (AC-0002):** goal-based check that imports `render_label` and compares its signature. A signature check is the cheapest oracle that fails on a broken call contract.
- **Privacy of the helper (AC-0003):** goal-based check, one reference search. It keeps true the one fact that makes this a single-caller change.

## Acceptance Criteria

- [ ] **AC-0001.** `render_label` returns, for each input, the base-revision value: `"  ready  "` → `"<ready>"`, `"ready"` → `"<ready>"`, `""` → `"<>"`, `"   "` → `"<>"`, `"\tready\n"` → `"<ready>"`, `" a  b "` → `"<a  b>"`, `"\u00a0ready\u3000"` → `"<ready>"`.
- [ ] **AC-0002.** `inspect.signature(isolated_helper.render_label)` equals `(label: str) -> str`.
- [ ] **AC-0003.** a search of the repository for the private helper's name finds only its definition and its one call inside `render_label`, both in `evals/files/isolated_helper.py`.

## Follow-ons

none

## Assumptions

- Product: the concrete refactor (rename, inline, or rewrite of `_trim_label`) is not named in the request — it changes only task T2's local method, not any criterion (settled by: the requester).
- Technical: no test runner is installed in the working environment (`import pytest` fails) — the characterization test is proven by direct import until a runner is available (settled by: the repository owner, by naming the runner and gate).

---

## plan.md

# Plan: label-trim-helper

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** none — non-structural. No `AGENTS.md`, architecture source, runner, or CI file exists in the supplied tree; the only anchors are `evals/files/isolated_helper.py` and `evals/files/test_isolated_helper.py`.

## Approach

Pin current behavior first, then refactor. T1 adds a characterization test
whose expected values come from the base revision. T2 changes the helper and
must leave T1 green. The riskiest part is a rewrite that changes which
whitespace is stripped; AC-0001's Unicode inputs catch that.

## Constraints

- No ADR or RFC governs this file.
- No runner or lint gate is declared in the supplied tree, so the gate is the characterization test plus the reference search.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| none (see spec § Durable Outputs) | — | — | — |

## Design (LLD)

### Design decisions

- No shared-substrate preservation expansion. The predicate in `new-spec` `references/shared-substrate-preservation.md` does not fire: the change is a private helper with a single caller. One reference search for `_trim_label` over the whole working tree found only the definition (`evals/files/isolated_helper.py:4`) and the one caller (`evals/files/isolated_helper.py:9`). The helper is not a member of any model, registry, graph, index, schema, namespace, or collection that a generic operation observes. So there is no consumer map and no extra preservation criteria. The test file imports only `render_label` (`evals/files/test_isolated_helper.py:1`). Rests on: AC-0003 staying true. Traces to: AC-0003.

Owned by: T2
- The expected side of every characterization case is a literal taken from the base revision, not computed by the code under test. Traces to: AC-0001.

Owned by: T1

### Behavior & rules

- `render_label(label)` returns `"<" + stripped + ">"`, where "stripped" uses Python `str.strip()` semantics: Unicode whitespace at both ends is removed, inner whitespace is kept. Traces to: AC-0001.

Owned by: T1, T2
- The refactor method is `implementation-discovered`: whichever form T2 takes must keep T1 green and AC-0003 true. Kill condition: if no form keeps both, stop and ask.

Owned by: T2

## Tasks

### T1: Characterization test pins `render_label` output on the base revision

**Depends on:** none

**Touches:** evals/files/test_isolated_helper.py

**Tests:**
- AC-0001: one parametrized case per input, in `evals/files/test_isolated_helper.py`, calling the public `render_label` seam (never the private helper). Mode: TDD (characterization) — it must pass on the unmodified base revision.
- AC-0002: one case comparing `str(inspect.signature(render_label))` to `"(label: str) -> str"`. Mode: goal-based.

**Done when:** T1's tests pass against the unmodified `isolated_helper.py`.

### T2: Private helper refactored with T1 still green

**Depends on:** T1

**Touches:** evals/files/isolated_helper.py

**Tests:**
- AC-0001, AC-0002: T1's suite, unchanged, rerun after the edit.
- AC-0003: `grep -rn "<helper name>" .` from the repository root lists exactly two hits, both in `evals/files/isolated_helper.py`. Mode: goal-based.

**Done when:** T1's suite passes after the edit and the AC-0003 search returns exactly those two hits.

## Rollout

Pure local logic. No flag, infrastructure, external system, or sequencing.
Rollback is reverting the commit.

## Risks

- A rewrite using `str.strip(" ")` or a hand-written ASCII whitespace set would drop tab, newline, or Unicode-space stripping; AC-0001 covers tab, newline, NBSP, and ideographic space.

## Changelog
