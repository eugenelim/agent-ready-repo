# Plan: Priority header field

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/lint-graph-pointers.py` (preamble reader, confined walk, refusal codes, exit 0/1/2) and its suite `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py`; `tools/repo/build_gate_chain.py` (gate step wiring); `tests/roster/test_close_work_extraction_and_immediate_disposition.py::test_wave4_excludes_later_wave_and_history_rewrite_behaviour` (an AST guard that shipped source never names a token).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

One new standard-library script in `work-loop` is both the reader and the lint. It follows `lint-graph-pointers.py`'s shape, but walks the whole corpus rather than changed artifacts, because the check is cheap and has no base-ref to resolve. The gate chain runs it. Two roster tests hold the "never reads" rule and the documentation in step, and one `workspace-status` pack test holds the "never orders" rule. The riskiest part is AC-0007's fixture, which needs multi-member lists in two skills' output from one tree.

## Constraints

- RFC-0106 D3: a priority is a header field on the item and never a position in a shared list.
- FEAT-0034 § Owner decisions, 2026-10-25, item 1: no field means no priority; the field never decides readiness, dispatch, or order of work.
- `packs/core/.apm/skills/work-loop/SKILL.md`'s argless queued start selects the first `canonical.ready` item. This spec leaves that rule unchanged; list-and-ask belongs to `workspace-registry-retirement-delivery` slice 8, Dispatch from headers.
- ADR-0074: skill scripts use the standard library only.
- Root `AGENTS.md` § Security considerations: corpus reads go through the `file_safety` confinement helpers, here the co-located `_file_safety.py` copy `lint-graph-pointers.py` already loads.
- The brief's non-goals: no change to `navigate-intents`; tracker sync is CAP-0004's.
- `tests/AGENTS.md` § Roster steps and `tools/AGENTS.md`: each new roster file needs a named `build-check.yml` step above the bulk step, a `STEP_DISPOSITION` entry, and a phase-and-dependency axis entry in `tools/lint-ci-parity.py`.
- `packs/AGENTS.md` § Version bump rule, § Shipped pack content carries no internal-governance citations, and § Security and authoring rules (the eval-harness bullet).

## Construction tests

**Integration tests:** T3's invariance test drives both CLIs over one fixture tree.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility: the four documentation surfaces | T4 | `test_priority_field_documentation.py` passes | AC-0008 checked |
| Maintainer procedure: `work-loop` finish checklist | T4 | The bullet names the command and exit codes; the finish-checklist hash is re-pinned | Bullet present |
| Current product truth: inventory row | T1 | `test_workspace_retirement_inventory.py` passes | Row present, owner 4 |
| Release history | T5 | Changelog gate passes; `core` versions agree | Fragment present |
| Delivery membership | T5 | `lint-brief-coverage.py` lists the spec | Coverage lint passes |

## Design (LLD)

### Design decisions

- **One reader, one value set.** `PRIORITY_VALUES = ("urgent", "high", "medium", "low")` lives only in `lint-priority-field.py`. Docs and tests pin against it; no other module copies it. Traces to AC-0001, AC-0008.
- **Whole-corpus walk, not changed-artifact.** The corpus holds no priority line today, so a full walk exits 0 and catches an invalid value wherever it lands. Traces to AC-0005.
- **Preamble ends outside fences.** The reader uses the `depends-on-headers` Preamble rule, which skips fenced blocks, rather than `lint-graph-pointers.py`'s `_preamble`, which does not. That keeps one header grammar with the `workspace-status` engine. Traces to AC-0001.
- **The intent field reference row is `unconstrained`.** The parity test's tiers describe `intent_shape.py`, which does not validate the field; the row's description names the lint as the validator. Adding the field to `intent_shape.py` would be the second vocabulary copy the owner ruled out. Traces to AC-0008.
- **The guard matches the field name, not the word.** AC-0006 matches `Priority` case-sensitively as a whole word in string constants. Lower-case `priority` appears in unrelated docstrings and as a local variable in `workspace_status.py`, and `PriorityClass` in `_process_safety.py` is not a whole-word match. A probe on 2026-10-26 found no match in scope. Traces to AC-0006.
- **AC-0007 runs in one root.** Mutating the same tree keeps `workspace_root` and every path equal, so the whole `status` output can be compared byte for byte. Traces to AC-0007.

Owned by: T1, T3, T4

### Data & schema

- Field line: `- **Priority:** <value>`, read with the `depends-on-headers` Preamble and Field value rules.
- Carrier name grammars: as AC-0001 states; the intent, brief, and spec patterns equal `lint-graph-pointers.py`'s `_COLLECTION_NAME_RE` and `_SPEC_DIR_RE`, and the captured pattern equals the `captured-item-files` term.
- Walk order: carrier directories are walked and read one at a time, intents, then briefs (as `lint-graph-pointers.py`'s `_build_indexes` walks them), then captured items, then specs. Violations are held until every directory is read, so a later refusal leaves stdout empty.
- Refusal codes: `unsafe-artifact`, `resource-limit`, `invalid-utf8`, as `lint-graph-pointers.py` names them.

Owned by: T1

### Interfaces & contracts

- CLI: `lint-priority-field.py --root DIR`; exit 0 clean, 1 violations, 2 refusal. Violations on stdout as `<path>: <code>`; refusals on stderr.
- `read_priority(text: str) -> str | None`; raises `PriorityError(code)`.

Owned by: T1, T2

## Tasks

### T1 — The reader and lint pass their construction suite

**Depends on:** none
**Verification mode:** TDD
**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-priority-field.py`, `packs/core/tests/skills/work-loop/test_lint_priority_field.py`, `docs/specs/workspace-retirement/inventory.toml`

**Tests:**
- `test_lint_priority_field.py`, loading the script by path as `test_lint_graph_pointers.py` does, over `tmp_path` trees, calling `main(argv)` in-process:
  - AC-0001: each value on each carrier type is valid; absent and empty-after-comment lines give `None`; a line after the first `## ` or inside a preamble fence is ignored; backticks and a trailing comment are stripped; `High`, `p1`, `none`, and `urgent high` are invalid; a file named `_draft.md` in an intent directory, `Draft.md` in the captured directory, and a spec directory `foo_bar` are not read.
  - AC-0002: a duplicate gives `duplicate_priority`, including a duplicate with an invalid value; captured stdout is exactly one `<path>: <code>` line per violation and stderr is empty; exit codes 1 and 0.
  - AC-0003: `read_priority` returns each value and `None`, and raises `PriorityError` with each code; the CLI calls it once per carrier (monkeypatched spy).
  - AC-0004: a symlinked file, a symlinked carrier directory, a non-UTF-8 file, an oversized file, and a tree over `MAX_FILES` (bound monkeypatched low) each exit 2 with stderr exactly one `<code>: <path>` line; a tree with an invalid-value intent and a symlinked brief, so the intents directory is walked and read first and the briefs walk then refuses (a `read_priority` spy confirms it raised), exits 2 with empty stdout; an absent carrier directory exits 0.

**Done when:** the suite passes, and the inventory row passes `test_workspace_retirement_inventory.py`.

### T2 — The gate chain runs the lint on this repository

**Depends on:** T1
**Verification mode:** goal-based check
**Touches:** `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`, `.claude/skills/work-loop/scripts/lint-priority-field.py`, `.agents/skills/work-loop/scripts/lint-priority-field.py`

**Tests:**
- AC-0005: `build_gate_chain.py` gains `test-lint-priority-field` and `lint-priority-field` steps after the graph-pointer steps, running the projected `.claude` copy with `--root .`. `EXPECTED_SCRIPT_STEPS` in `tools/test_build_gate_chain.py` gains both paths at that position, and the argv test pins `["--root", "."]` for the lint step. `make build-self` writes the projected copies, and the projected script exits 0 on this repository.

**Done when:** `tools/test_build_gate_chain.py` passes and the projected lint exits 0 on this repository.

### T3 — Nothing that orders work reads or reacts to the field

**Depends on:** T1
**Verification mode:** TDD
**Touches:** `tests/roster/test_priority_field_never_read.py`, `packs/core/tests/skills/workspace-status/test_priority_field_invariance.py`

**Tests:**
- AC-0006: the roster test parses each module in scope with `ast` and asserts no `str` constant matches `\bPriority\b` or contains `lint-priority-field`. A self-check asserts the module set is non-empty and includes each `_data/` copy whose name matches a scoped module, `workspace_status_engine.py` among them.
- AC-0007: the pack test builds the fixture AC-0007 describes, reusing the `depends-on-headers` equivalence suite's tree builder where it fits. Legacy `shaping_queue` slug entries in `workspace.toml` fill `shaping.ready`; they name no file, so they carry no line. A spec whose `Depends on:` names an active spec fills `canonical.blocked`. The test runs `workspace_status.py` and `navigate_intents.py` through `main(argv)` with stdout captured. It asserts the list sizes AC-0007 requires before comparing, then compares as AC-0007 states.

**Done when:** both tests pass.

### T4 — Every documentation surface names the field the same way, and both roster tests are wired

**Depends on:** T3
**Verification mode:** goal-based check
**Touches:** `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `guides/product-engineering/reference/intent-fields-and-modes.md`, `packs/core/.apm/skills/work-intake/references/lifecycle-index.md`, `packs/core/.apm/skills/author-delivery-brief/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, the `.claude/skills/` and `.agents/skills/` copies of those four pack files, `tests/roster/test_priority_field_documentation.py`, `tools/test_workspace_status.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Tests:**
- AC-0008: the roster test imports `PRIORITY_VALUES` from the script and asserts each of the four surfaces holds the values in that order as one backticked, `, `-separated run, plus the phrases "no priority" and "never decides readiness, dispatch, or order of work".
- `test_intent_field_reference_parity.py` still passes with the new `unconstrained` row.
- The `work-loop` finish checklist names `lint-priority-field.py --root .` and its exit codes. `_WORK_LOOP_FINISH_HASH` in `tools/test_workspace_status.py` is re-pinned with a dated note in the existing style: the bullet runs a read-only lint, writes no `spec.md` field, and mutates no `workspace.toml` array, so the engine needs no edit.
- `build-check.yml` gains a named step for each of `test_priority_field_never_read.py` and `test_priority_field_documentation.py` above the bulk roster step. `tools/lint-ci-parity.py` gains a `LOCAL("test-after-build-check")` disposition for each and lists each beside `pytest graph-pointer authoring sources (roster-owned)` on its phase-and-dependency axis.

**Done when:** `test_priority_field_documentation.py`, `test_intent_field_reference_parity.py`, `tools/test_workspace_status.py`, and `tools/lint-ci-parity.py` pass.

### T5 — The release is recorded and the brief lists the spec

**Depends on:** T2, T3, T4
**Verification mode:** goal-based check
**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/.apm/skills/work-loop/evals/evals.json` and its `.claude/` and `.agents/` copies, `docs/product/changelog.d/`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `workspace.toml`

**Tests:**
- `core` moves one patch above its version on the base branch, equal in both files; a changelog fragment names the field and the lint; the changelog gate passes.
- `work-loop`'s eval harness gains one case: an argless start over two ready specs, the first marked `low` and the second `urgent`, selects the first `canonical.ready` item.
- The brief's Spec map lists `priority-header-field`, its `workspace.toml` entry moves with the spec's status, and `lint-brief-coverage.py` passes.

**Done when:** `make lint-ruff lint-mypy` pass, the touched suites pass, and the coverage and changelog checks pass.

## Risks

- A probe on 2026-10-26 over a copy of this repository's `docs/` and `workspace.toml`, adding `Priority: urgent` to a spec, a brief, an intent, and a captured item in place, left the whole `status` output byte-equal and changed only `generated_at` in the `outstanding` output.
- AC-0007's fixture may need more registry shape than expected to give two ready specs and two shaping-ready items. The `depends-on-headers` equivalence suite already builds such trees; reuse its builder before writing a new one.

## Changelog

- Drafted 2026-10-26.
