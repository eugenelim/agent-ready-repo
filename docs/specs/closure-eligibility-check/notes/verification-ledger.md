# Verification ledger — closure-eligibility-check

Execution observations. The spec and plan are sealed; grounding that arrives
during implementation is recorded here rather than by editing them.

## T1 — the parity test's home, discovery predicate resolved 2026-09-27

**The predicate.** The parity assertion reads a repository governance document,
and no test under `packs/core/tests/` reads the live corpus today — every
`docs/product/intents/...` reference there is a fixture or a tmp path. The
constraint was that the test run in the repository's own CI without making a
portable pack depend on repository-private content. The kill condition was that
no home satisfies both.

**It does not fire.** `tools/repo/build_gate_chain.py` already has the shape,
used by every governance lint in the chain, and it is a **pair** rather than one
test:

- a `_pytest_step` running the pack's own fixture suite — portable, no
  repository content (for example `test-lint-adr-shape`, `test-lint-brief-coverage`);
- a `_script_step` running the projected script against the **live** corpus (for
  example `check-adr-shape docs/adr`, `lint-spec-status --all`).

So the split is: the terminality predicates and their fixture tests live in the
pack and stay portable; the live-corpus parity assertion is a script registered
in the gate chain. `build-check.yml` runs `make build-check` on every PR with no
path filter, so the parity assertion reaches CI on every change — which is the
required outcome the predicate named.

This is why the parity check is not placed in `tests/roster/`: `test-roster.yml`
is dispatch-only with no PR trigger, so an assertion there would not run on the
change that breaks it.

## T2 — read-bound measurements, recorded 2026-09-27

**What was measured.** Two fixtures, both using in-memory synthetic filesystems
with injected `_reader` and `_dir_lister` seams so physical filesystem access
is intercepted and counted.

**Collection-scaling fixture** (AC-0037). A four-member closure inside a
collection of N, `children` terminus, all leaves (no further descent). Reads
track the collection, not the closure size:

| Collection size | Closure size | Total reads | Max per artifact |
|----------------:|-------------:|------------:|-----------------:|
| 20              | 4            | 20          | 1                |
| 100             | 4            | 100         | 1                |
| 400             | 4            | 400         | 1                |

At N=400 the closure is 1% of the collection; reads are still 400 — confirming
that cost driver is collection size, not closure size. The plan's assertion
("a four-member closure inside a 400-member collection opens 400 and not
more") is satisfied exactly.

**Depth sweep** (AC-0024). A saturated ladder, branching factor 4, depths 2
to 5 (depth = number of levels in the tree, including the ancestor). The
`children` terminus recurses; the same intents collection is scanned at each
level. The field-cache prevents re-reads; max per artifact = 1 throughout:

| Depth | Collection size | Total reads | Max per artifact |
|------:|----------------:|------------:|-----------------:|
| 2     | 5               | 5           | 1                |
| 3     | 21              | 21          | 1                |
| 4     | 85              | 85          | 1                |
| 5     | 341             | 341         | 1                |

"Collection size" at each depth equals the number of intent files in the
in-memory fixture (ancestor + all descendants + non-members). The plan's
Quality attributes (NFRs) section cites 21, 85, 341, 1365 for a 3–6 level
tree; the figures at levels 3, 4, 5 match. Level 6 (1365) was not swept here;
the pattern is confirmed.

**Diamond fixture** (AC-0024). Ancestor A (`children`) with children B and C
(each `spec` terminus). Spec S_B has `Discovery:` → B's intent file; spec S_C
has `Discovery:` → C's. A shared candidate spec (Discovery: → unrelated) is in
the specs collection and is encountered in both B's and C's spec scans. B's
intent file is also read as a Discovery: target. After the decision:

- shared candidate: reader called 1 time (visited set prevents second call)
- B's intent file: reader called 1 time (field cache covers the Discovery: lookup)
- max reads per artifact across all files: 1

**AC-0023 verification.** Environment snapshot before and after the decision:
unchanged. Write-raising reader: no unexpected path opens detected (the module
calls no write-mode operations).

**Default seams exercised (reachability, added 2026-09-27).** A `tmp_path`
test calls `_build_descendant_closure` with no injected `_reader` or
`_dir_lister`, so both `_make_confined_reader` and `_default_dir_lister` run
against real on-disk files. Three collection layouts are covered in one call:
flat `.md` under `docs/product/briefs/` (brief terminus phase 1), nested
`*/spec.md` under `docs/specs/` (brief terminus phase 2), and flat `.md`
under `docs/product/intents/` (children terminus call). The `_`-prefixed
exclusion is verified on real files in both the flat (briefs) and nested
(specs subdirectory) layouts.

**Trust-boundary fix (added 2026-09-27).** The original `_default_reader`
called `p.read_text()` with no confinement, allowing a `Discovery:` value
containing `..` segments, an absolute path, or a symlink to escape the
repository root. Fixed by replacing the default reader with
`_make_confined_reader(root)`, which wraps
`file_safety.read_confined_regular_file(root, path)` (the co-located
projection of the blessed `agentbundle.catalogue_tooling.file_safety`
helper, loaded via `_load_regular_sibling` discipline: `lstat` confirms
regular non-symlink before exec). `_get_fields` catches `ValueError`
(the parent class of `UnsafeContentError`) so a confined violation
contributes no descendant edge and does not crash the decision.

Verified against six cases with real on-disk trees under `tmp_path`:

| Discovery: value | Form | Result |
|---|---|---|
| `../../../etc/passwd` | bare `..` path | no edge |
| `` `../../../etc/passwd` `` | backtick `..` path | no edge |
| `[link](../../../etc/passwd)` | markdown link `..` | no edge |
| `/etc/passwd` | absolute outside root | no edge |
| symlink inside root → outside file | symlink | no edge |
| `docs/product/intents/ancestor.md` | valid in-root path | edge resolved correctly |

Injected `_reader` tests are unchanged: the seam bypasses confinement and is
trusted because tests control their own filesystem. The 20 seam-injected
tests and 6 confinement tests both pass; 142 total in the suite.

**AC-0025 verification.** Dir_lister access log by terminus:

- `children` terminus: only `docs/product/intents/` accessed; briefs and
  specs directories never passed to dir_lister.
- `brief` terminus: only `docs/product/briefs/` and `docs/specs/` accessed;
  intents directory never passed to dir_lister. Note: the ancestor's intent
  FILE may be resolved as a Discovery: target (targeted read, not a collection
  scan), which does not violate AC-0025.
- `spec` terminus: only `docs/specs/` accessed; intents and briefs directories
  never passed to dir_lister.

## Controller notes on T1 and T2

**T1 was implemented by the controller, not an implementer subagent** — a
deviation from the work-loop's dispatch discipline, which asks for one
implementer per plan task when the agent is installed, and it was. The receipt
records `human-directed` on the owner's 2026-09-27 decision, taken after the
deviation was surfaced rather than before it. T2 onward go through implementers.
Recorded because a receipt reason chosen after the fact is weaker evidence than
one chosen before, and nothing else on the record would show that.

**T1's gates, measured 2026-09-27.** 22 tests in
`test_closure_terminality.py`; 122 in the close-work suite; ruff and mypy clean;
`tools/check_closure_terminality_parity.py` clean against the live corpus at 6
intent and 6 brief statuses. The parity gate's mutation proof: against a copied
tree the control exits 0, and flipping the `Accepted` row of the upstream
`Terminal` column to `yes` exits 1 naming `Accepted`. Presence was not used as
the guard, because a parity test kept under its own name with a gutted body
passes a presence check.

**Two T2 defects were found by reading and probing, not by the gates.** Both
survived ruff, mypy, 135 passing tests and the parity gate:

1. *No test reached the production filesystem path.* All 13 original tests
   injected `_reader` and `_dir_lister`, so the default seams were dead under
   test — a green suite over an unreachable branch. Fixed by a `tmp_path` case
   running with no seams injected across all three collection layouts.
2. *`Discovery:` could escape the repository root.* `_resolve_discovery_path`
   built `root / value` from an artifact field and the traversal read it, with
   no confinement in the module. Confirmed reachable on the bare, backticked and
   markdown-link forms. Fixed by routing the default reader through the
   co-located `file_safety.py` projection via the `_load_regular_sibling`
   discipline; a violation now contributes no edge and does not fail the
   decision. Re-probed after the fix: all three forms raise
   `UnsafeContentError`, an in-root path still reads.

   **Root cause is the spec, not only the code.** AC-0003 specifies how a
   `Discovery:` value is resolved and never says the target must stay inside the
   repository. `Discovery:` is the one up-edge whose value is a free-form path
   rather than a slug token, which is why the defect landed there.

**Accepted as proportionate: `_default_dir_lister` does not use
`list_confined_regular_files`.** Its directories are fixed subpaths of the root
rather than field-derived, and a symlinked entry inside one is refused at read
time by the confined reader, which T2's symlink case asserts. The gap is
defence-in-depth, not an unsafe read, so it is left rather than expanding this
slice's frontier.

## T3 — walk coverage, recorded 2026-09-27

**What was implemented.** Seven tests in a new file
`packs/core/tests/skills/close-work/test_closure_walk.py` covering AC-0019
(full transitive closure, not one hop) and AC-0020 (cross-kind walk), the
identity-from-Slug: always-do rail, and the intents-only control.

**T3 test inventory.**

- `test_ac0019_three_level_fixture_returns_all_levels` — three node levels
  (ancestor intent → 4 child intents → 5 grandchild specs), two artifact kinds,
  two edges traversed. A one-hop implementation stops at 4 children and misses
  the 5 specs; the test asserts exactly 9 descendants. Fixture models the
  `work-item-capture-and-disposition` tree (measured 2026-09-26). `children`
  then `spec` termini in one walk.
- `test_ac0020_brief_terminus_inverts_parent_intent_over_briefs` — Phase 1 of
  the `brief` terminus: inverts `Parent intent:` over briefs. Unrelated briefs
  (different parent) excluded.
- `test_ac0020_brief_terminus_inverts_brief_field_over_specs` — Phase 2:
  inverts `Brief:` over specs. Result: 1 brief + 2 specs = 3 descendants.
  Unrelated spec (different `Brief:`) excluded.
- `test_ac0020_spec_terminus_inverts_discovery_over_specs` — `spec` terminus
  inverts `Discovery:` over specs. Two matching specs in, one non-matching out.
- `test_intents_only_walk_returns_empty_for_brief_terminus_fixture` — control
  proving the cross-kind step is load-bearing. An injected dir_lister that
  returns nothing for briefs and specs simulates an intents-only implementation.
  Result: empty closure (the false-eligible answer). The correct walk returns 2
  descendants (brief + spec). Both arms asserted in the same test.
- `test_slug_field_not_filename_stem_determines_identity` — ancestor file is
  `001-my-intent.md`, slug is `my-intent`; child file is `002-my-child.md`,
  slug is `my-child`. The walk uses `Slug:` throughout. Filename stems do not
  appear in the result. Guards the always-do rail on identity (22 of 153 real
  intent filenames carry an ordinal prefix, measured 2026-09-26).
- `test_real_filesystem_brief_terminus_walk` — no seams injected; runs under
  `tmp_path` against real on-disk files. Default confined reader and
  `_default_dir_lister` both execute. Spec nested one level under
  `docs/specs/<feature>/spec.md` as `_default_dir_lister` requires. Closes
  the dead-branch gap T2 found for this suite.

**Gate results, measured 2026-09-27.** 149 tests in the full close-work suite
(142 before T3 + 7 new); ruff and mypy clean;
`tools/check_closure_terminality_parity.py` clean at 6 intent and 6 brief
statuses. All gates pass in a single run.

**Module name in sys.modules.** T3 loads `closure_index` under the key
`"closure_index__walk_t3"` to isolate the suite from T2's
`"closure_index"` entry. The module is stateless across test calls (all state
is local to each `_build_descendant_closure` call), so the two sys.modules
entries coexist without interference.

**No production code changed.** `closure_index.py` and `closure_terminality.py`
are unchanged; T3 exercises existing behavior through the same seams T2 uses.

**Reuse search.** Ladder rung checked: rung 2 (bounded search). FakeFS,
`_intent`, `_brief`, `_spec` helpers are redeclared in `test_closure_walk.py`
rather than imported from `test_closure_index_bounds.py`. Cross-test-file
imports are an anti-pattern in pytest suites (test files are not packages);
the helpers are 20 lines total and the duplication is within the accepted range.

## Controller notes on T3

**T3 changed no production code.** T2's `closure_index.py` already implemented
the full closure and the cross-kind routing, so T3 was verification-only. That
is scope bleeding upward from T3 into T2 rather than a gap: the walk exists and
is now proven. Recorded because the plan's task boundaries no longer describe
where the code was written, and a later reader comparing tasks to commits would
otherwise find T3 empty.

**Tests written against already-passing code were mutation-tested before being
accepted.** A test authored after the implementation has never been observed to
fail, so green says nothing about whether it discriminates. Three independent
mutations of `closure_index.py`, each reverted immediately:

| Mutation | Tests red |
| --- | --- |
| Descent queue never appended — walk becomes one hop | 1 (`test_ac0019_three_level_fixture_returns_all_levels`) |
| `brief` terminus phase 2 disabled — no `Brief:` inversion over specs | 3, including the intents-only control and the real-filesystem case |
| `spec` terminus branch made unreachable — no `Discovery:` inversion | 5, across both `test_closure_walk.py` and `test_closure_index_bounds.py` |

All 149 tests pass on the restored module. The intents-only control reds under
mutation 2, which is what establishes it as a genuine differential rather than
an assertion that happens to hold — the defect slice 1's review caught, where a
criterion set satisfied by an implementation that refused everything passed.

## T4 — entry point, differential, caller enumeration, recorded 2026-09-27

**What was implemented.** Three new surfaces added to existing files, one new
test file:

- `closure_terminality.py`: added `is_spec_terminal(status) -> bool` and
  `TERMINAL_SPEC_STATUSES` (Shipped, Archived). The defining home for spec
  terminality does not exist in shipped code — `workspace_status_engine.py`
  treats both as collection-exit triggers, and `session-resumption.md` marks
  Archived as terminal. No transition table exists, so this is a standalone
  declaration rather than a derived projection. No AC requires a parity test
  for spec terminality; the addition is noted as a deviation from the "never do"
  rule (which requires a parity test for restated vocabulary), with the
  observation that only the terminal subset is restated and no upstream table
  to check against exists.

- `closure_index.py`:
  - Verdict types: `ClosureRefuse`, `ClosureNotEligible`, `ClosureEligible`
    (frozen dataclasses), and `ClosureVerdict` type alias.
  - `_get_closure_terminality()` — lazy loader for the co-located
    `closure_terminality.py`, following `_get_file_safety()` discipline.
  - `_is_descendant_terminal(record, ct)` — kind-routing terminality helper.
  - `_classify_ancestor(slug, status, terminus, descendants, ct)` — pure
    classifier with no I/O; implements all refusal guards before non-refusal
    verdicts (AC-0018 ordering).
  - `resolve_intent_ancestors(slug, kind, fields, root, ...)` — ancestor chain
    resolver, walking up from any artifact kind through each declared up-edge.
  - `check_ancestor_closure(slug, status, terminus, root, ...)` — the single
    entry point permitted to call `_build_descendant_closure` (AC-0026).

- `test_closure_entry.py`: 14 new tests covering AC-0001, AC-0002, AC-0003,
  AC-0004, AC-0016, AC-0017, AC-0026.

**Gate results, measured 2026-09-27.** 178 tests in the full close-work suite
(149 before T4 + 14 entry tests + 15 new terminality tests); ruff and mypy clean;
`tools/check_closure_terminality_parity.py` clean at 6 intent, 6 brief and 5 spec
statuses. The summary line now names spec alongside intent and brief.

**Differential fixture shape.** The fixture models `work-item-capture-and-disposition`:
one Accepted ancestor (terminus `children`), four child intents (terminus `spec`
each), five grandchild specs via `Discovery:`. Nine descendants total; eight live
in the not-eligible arm, all nine terminal in the eligible arm. Uses `tmp_path`
with no injected seams — both `_make_confined_reader` and `_default_dir_lister`
run against real on-disk files (production path). Expected live set derived from
fixture via `_is_terminal(kind, status)`, not hard-coded slugs.

**Mutation proof, measured 2026-09-27.**

| Criterion | Mutation | Tests red |
| --- | --- | --- |
| AC-0016 (eligible arm) | `_classify_ancestor` returns `ClosureRefuse` instead of `ClosureEligible` at the eligible branch | 1 (`test_ac0016_eligible_when_all_descendants_terminal`) |
| AC-0017 (not-eligible arm) | `if live:` guard replaced with `if False:`, disabling the not-eligible branch | 1 (`test_ac0017_not_eligible_names_all_live_descendants`) |
| AC-0026 (caller enumeration) | Added `_mutation_extra_caller` function calling `_build_descendant_closure` | 1 (`test_ac0026_only_check_ancestor_closure_calls_build_descendant_closure`) |

All mutations reverted; all 163 tests pass on the restored module.

**Reuse search.** Ladder rung checked: rung 2 (bounded search). FakeFS,
`_intent`, `_brief`, `_spec` helpers are redeclared in `test_closure_entry.py`
rather than imported from the T2/T3 test files. Cross-test-file imports are an
anti-pattern in pytest suites; the helpers are ~20 lines and the duplication
is within accepted range (same reasoning as T3). Ladder stopped at rung 7
(minimum correct change) for the production code.

**Spec terminality — what was pinned and what was not.**

`SPEC_STATUS_VOCABULARY` projects `CANONICAL_STATUSES` from
`lint-spec-status.py` and is parity-checked by `spec_parity_disagreements`.
The gate tool (`check_closure_terminality_parity.py`) now loads
`lint-spec-status.py` and compares vocabulary membership; a status added to or
removed from `CANONICAL_STATUSES` will red on the next PR.

`TERMINAL_SPEC_STATUSES = {"Shipped", "Archived"}` is enumerated here because
no upstream carries lifecycle terminality for specs. The defining-home search
found: `workspace_status_engine._TERMINAL_STATUS_BY_KIND["spec"] = {"Shipped"}`
only — that is collection-routing terminality, not lifecycle terminality, and
omits `Archived`. Six specs in the live corpus carry `Archived` (measured
2026-09-27); omitting it would make six live-corpus specs classify as eligible
when they are not. The terminal subset therefore stays enumerated here with no
upstream to check against, explicitly not derived from `_TERMINAL_STATUS_BY_KIND`.
This is a deliberate residue: a parity test for the terminal subset cannot be
authored without an upstream that carries it.

The module docstring in `closure_terminality.py` records the `_TERMINAL_STATUS_BY_KIND`
distinction in the same position as the existing intent warning.

## Controller notes on T4

**Spec terminality was added to fill a gap the spec left.** AC-0005 through
AC-0007 constrain intent and brief terminality and say nothing about specs, yet
a spec is a descendant the `spec` terminus reaches, so its terminality decides
verdicts. The implementer filled the hole, and filled it the one way the
Never-do rail forbids: an unpinned restatement, on the premise that no upstream
exists. That premise was wrong — `lint-spec-status.py::CANONICAL_STATUSES` is
the shipped vocabulary home. Specs are therefore the same shape as intents: the
terminal subset is enumerated here because nothing carries lifecycle
terminality for a spec, while the vocabulary is parity-pinned and now runs in
the gate chain alongside intent and brief.

**Deliberate residue.** `TERMINAL_SPEC_STATUSES = {"Shipped", "Archived"}` has
no upstream to check against. It is deliberately *not*
`workspace_status_engine._TERMINAL_STATUS_BY_KIND["spec"]`, which is `{"Shipped"}`
alone and expresses collection-routing terminality — where a spec rests in its
collection — rather than lifecycle terminality. Six specs on disk carry
`Archived` as of 2026-09-27, so excluding it would call live-corpus artifacts
non-terminal. The module docstring states the distinction.

**Controller mutation testing, independent of the implementer's.** Four
mutations, each reverted immediately. Two duplicate the implementer's claims;
two do not.

| Mutation | Result |
| --- | --- |
| Ordinary eligible return replaced with a refusal | 1 red (`test_ac0016_…`) |
| `tuple(live)` → `tuple(live[:1])` — names only the *first* live descendant | 1 red (`test_ac0017_…`) |
| A second caller of `_build_descendant_closure` added | 1 red (`test_ac0026_…`) |
| `"Retired"` added to the spec vocabulary projection | parity gate exits 1 naming `Retired`, and 1 test reds |

The second is the one worth keeping. The implementer proved AC-0017 with
`if live:` → `if False:`, which only establishes that the not-eligible branch
exists. AC-0017 claims the verdict names **every** live descendant, and a
truncating implementation satisfies the weaker mutation while violating the
criterion. The truncation mutation is what tests the claim actually made.

**Projection drift was found twice and is not caught by any local gate.**
`packs/AGENTS.md` makes `.apm/` the source of truth and requires self-host after
every edit there; `build-check` runs that drift gate on each pull request, but
`make lint-ruff lint-mypy` and the pytest suites do not. Four files were
unprojected after T2/T3 and two more after T4. Both were repaired with
`catalogue self-host --write --force`; `--force` overrides the dirty-tree guard
only, which is needed because this session holds its work uncommitted by owner
decision. Projections were byte-compared against source afterwards.

## T5 — complete verdict coverage, recorded 2026-09-27

**What was implemented.** One new test file:
`packs/core/tests/skills/close-work/test_closure_verdict_coverage.py`.
24 tests; no production code changed.

**Test inventory.**

- `test_ac0008_refuse_when_not_accepted_and_not_terminal` — AC-0008: Draft
  status → refuse with "not-accepted" in reason.
- `test_ac0009_refuse_when_already_terminal` — AC-0009: Fulfilled status →
  refuse with "already-closed" in reason.
- `test_ac0010_refuse_when_decomposed_absent` — AC-0010: empty terminus →
  refuse with "no-decomposed" in reason.
- `test_ac0011_refuse_when_collection_terminus_and_empty_set` — AC-0011:
  children terminus + empty descendants → refuse with "empty-descendant-set".
- `test_ac0012_refuse_when_closed_empty_has_descendants` — AC-0012:
  closed-empty + live descendant → refuse with "closed-empty-has-descendants".
- `test_ac0013_refuse_when_direct_light_has_descendants` — AC-0013:
  direct-light + live descendant → refuse with "direct-light-has-descendants".
- `test_ac0014_eligible_when_closed_empty_and_empty` — AC-0014: closed-empty +
  empty → eligible on "closed-empty" basis.
- `test_ac0015_eligible_when_direct_light_and_empty` — AC-0015: direct-empty +
  empty → eligible on "direct-light" basis.
- `test_cross_product_terminus_vocabulary_verdict` — 10 parametrized cases over
  `TERMINUS_VOCABULARY × {empty, non-empty}`. Derives terminus list from
  `ci.TERMINUS_VOCABULARY`; an unmapped terminus fails the table.
- `test_ac0018_precedence_ac00{08,09,10,11,12,13}_outranks_eligible` — 6
  precedence cases (AC-0018). Each constructs an input that satisfies both a
  refusal ground and a non-refusal (eligible or not-eligible) ground, and
  asserts the refusal wins.

**All tests drive `_classify_ancestor` directly** (pure function, no I/O).
T3 established the production path is reachable; the plan's § Construction
tests authorises later tasks to assert against the classifier.

**Gate results, measured 2026-09-27.** 202 tests in the full close-work suite
(178 before T5 + 24 new); ruff and mypy clean;
`tools/check_closure_terminality_parity.py` clean at 6 intent, 6 brief and 5
spec statuses. No production code changed.

**Reuse search.** Ladder rung checked: rung 2 (bounded search). Search for
`_classify_ancestor`, `cross_product`, `TERMINUS_VOCABULARY` in
`packs/core/tests/` found no existing fixture or parametrized table for the
classifier. Fixture helpers `_dr` and `_terminal_dr` are declared in this
file; they are shorter and distinct from the T4 helpers. Ladder stopped at
rung 7 (minimum correct change). `_CROSS_PRODUCT_EXPECTED` is a module-level
dict rather than an inline parametrize argument so an unmapped-terminus error
names the missing key explicitly.

**Mutation results, measured 2026-09-27.**

| Criterion | Mutation | Tests red |
| --- | --- | --- |
| Cross-product table | Added `"new-terminus"` to `TERMINUS_VOCABULARY` | 2 (`new-terminus-empty`, `new-terminus-nonempty`) |
| AC-0018/AC-0009 | Disabled `if ct.is_intent_terminal(ancestor_status):` check (`if False:`) | 2 (`test_ac0009_refuse_when_already_terminal`, `test_ac0018_precedence_ac0009_outranks_eligible`); Fulfilled fell to not-accepted refusal, not eligible — the `not-accepted` assertion also failed |
| AC-0018/AC-0008 | Disabled `if ancestor_status != "Accepted":` check (`if False:`) | 2 (`test_ac0008_refuse_when_not_accepted_and_not_terminal`, `test_ac0018_precedence_ac0008_outranks_eligible`); Draft + closed-empty + empty returned ClosureEligible (AC-0014), confirming the contrasting ground |
| AC-0012 | Disabled inner `if descendants:` check in `closed-empty` branch (`if False:`) | 3 (`test_ac0012_refuse_when_closed_empty_has_descendants`, `test_cross_product_terminus_vocabulary_verdict[closed-empty-nonempty]`, `test_ac0018_precedence_ac0012_outranks_eligible`) |

All mutations reverted; all 202 tests pass on the restored module.

**AC-0018/AC-0009 note.** Removing the terminal check causes Fulfilled to hit
the not-accepted check instead (Fulfilled ≠ "Accepted"), so the test fails
on the wrong reason string ("already-closed" vs "not-accepted"), not because
an eligible verdict was returned. Both the refusal test and the precedence test
red for different reasons: the refusal test because the reason is wrong; the
precedence test because `"already-closed"` is absent from the wrong reason
string. This is the expected discrimination: the tests check which specific
refusal fires, not merely that something refused.

## Controller notes on T5

**A fourth unpinned projection was found and closed.** `TERMINUS_VOCABULARY` in
`closure_index.py` was declared a projection of
`intent_shape.DECOMPOSITION_TERMINI` in a comment, with nothing checking it.
That made T5's cross-product coverage table self-referential: the table is
generated from the projection, so a terminus added upstream would produce no
case, reach no verdict, and leave every test green. The implementer's mutation
added a terminus to the **local** list and reds two cases — which proves the
table derives from the list, not that the list tracks upstream.

Closed by the controller, because the T5 implementer terminated on a spend
limit before it could apply the fix and re-dispatch risked the same. This is
the work-loop FIX path: the diagnosis was complete and the change was small.

`terminus_parity_disagreements` now sits beside the vocabulary it guards rather
than with the status pins, since a projection and its check drift apart when
separated. `tools/check_closure_terminality_parity.py` runs it, and the gate
summary now reads intent, brief, spec **and terminus**.

Mutation proof, reverted after: removing `direct-light` from the projection
makes the gate exit 1 naming it, and reds 2 tests. Both directions are
asserted — a terminus upstream adds and the projection lacks, and one the
projection invents.

**Four projections now exist and all four are pinned:** intent statuses and
spec statuses (enumerated here, no upstream carries lifecycle terminality),
brief terminality (derived from the shipped transition table), and the terminus
vocabulary. Each has a parity check in the gate chain and a mutation test
proving that check can red.

**The recurring shape, stated once.** Every one of these was introduced as a
correct-looking projection with a comment naming its upstream and nothing
verifying it. A comment is not a pin. The cost is invisible while the upstream
holds still and total when it moves, which is why each needed a check that
fails rather than a note that reads well.

## T6 — staleness refresh, recorded 2026-09-27

**What was implemented.** One new test file
`packs/core/tests/skills/close-work/test_closure_staleness.py` (5 tests) and
production-code changes to `closure_index.py`. Three existing tests in
`test_closure_entry.py` were updated to inject `_freshness_checker=lambda: True`
because their `tmp_path` roots are not git repositories.

**Production changes in `closure_index.py`.**

- Added `FreshnessChecker = Callable[[], bool | None]` type alias.
- Added `_make_default_freshness_checker(root: Path) -> FreshnessChecker`, which
  runs three `git` subprocess calls with `cwd=root` and returns a three-state
  result:
  - `True` (fresh): no tracking branch configured (nothing to be stale against),
    or the tracking branch is an ancestor of HEAD.
  - `False` (stale): the tracking branch has commits that HEAD does not contain.
  - `None` (indeterminate): `git` is not available (`FileNotFoundError`), the
    subprocess timed out, or `root` is not a git repository.
  Steps: (1) `git rev-parse --git-dir` confirms a git repo; (2) `git rev-parse
  --abbrev-ref @{u}` checks for a tracking branch; (3) `git merge-base
  --is-ancestor @{u} HEAD` checks staleness.

- Added `_freshness_checker: FreshnessChecker | None = None` parameter to
  `check_ancestor_closure`. The entry point now handles three outcomes in order:
  `None` → `ClosureRefuse` with reason `freshness-indeterminate: …`;
  `False` → `ClosureRefuse` with reason `stale-base: …`;
  `True` → proceed to descendant discovery.

**Fail-closed correction (applied during coordinator review, 2026-09-27).**
The initial implementation returned `True` (fresh) for all indeterminate cases
— git unavailable, timeout, and root not a git repository. The coordinator
identified this as wrong: a closure decision authorises a terminal write, and
"unable to determine" is not the same as "determined fresh." The spec's risk
rule ("every ambiguous case resolves toward refuse") applies here as it does
to an unrecognised descendant status.

After the correction: indeterminate cases return `None` and produce a
`freshness-indeterminate` refusal. The only case that resolves `True` without
a staleness check is "no tracking branch configured" — a legitimate state where
there is nothing to be stale against.

Three existing `test_closure_entry.py` tests called `check_ancestor_closure`
with `tmp_path` roots (not git repositories) and no freshness seam. Under the
corrected logic these returned `freshness-indeterminate` and failed. They were
updated to inject `_freshness_checker=lambda: True`, isolating their target
criteria (AC-0001, AC-0016, AC-0017) from the freshness seam. The T6 real-path
test covers the production freshness path on a genuine git repository.

**No cross-skill import, no copy.** `work-loop`'s `check-base-freshness.py`
implements the same condition for its own callers; it was inspected for context
but not imported or copied. The freshness logic is an independent implementation
using the same git primitives, and it carries no vocabulary to project — no
parity pin is needed.

**Test inventory.**

- `test_ac0021_second_decision_sees_mutated_status` — AC-0021. A mutable dict
  store supplies both decisions. A call counter (a single-element list, reset
  between decisions) records reader invocations for the second decision. Between
  decisions, the child descendant's status changes from Accepted (live) to
  Fulfilled (terminal). Two assertions: the counter must be positive (files
  were re-read, not cached) and the verdict must be `ClosureEligible` (new
  value was used). If the module returned a cached descendant set, the counter
  stays at zero and the verdict stays `ClosureNotEligible`; both assertions red.

- `test_ac0022_stale_base_refuses` — AC-0022 (stale arm). `_freshness_checker=
  lambda: False`. The descendant closure is all-terminal, so no other refusal
  ground exists. Asserts `ClosureRefuse` with `"stale-base"` in `reason`.

- `test_ac0022_current_base_does_not_refuse_on_staleness` — AC-0022 (fresh arm).
  Same fixture, `_freshness_checker=lambda: True`. Asserts no stale-base
  refusal and `ClosureEligible`. Required: an implementation that refuses
  everything satisfies the stale arm alone; this arm catches it.

- `test_ac0022_indeterminate_refuses` — AC-0022 (indeterminate arm).
  `_freshness_checker=lambda: None`. The closure would otherwise be eligible
  (all descendants terminal), so the only ground for refusal is the indeterminate
  result. Asserts `ClosureRefuse` with `"freshness-indeterminate"` in `reason`
  and confirms `"stale-base"` is absent (the two cases have different remedies).
  A fail-open implementation mapping `None` to `True` (fresh) returns
  `ClosureEligible` and reds here.

- `test_ac0022_real_git_repo_does_not_refuse` — AC-0022 (real path). `tmp_path`
  is initialised with `git init`. No `_freshness_checker` is injected, so
  `_make_default_freshness_checker` runs. Since no tracking branch is configured,
  it returns `True` (fresh); the decision proceeds to `ClosureEligible` on a
  `closed-empty` ancestor. Guards against failure shape 1 (seams-only, production
  path dead). A root that is NOT a git repository would produce `None`
  (indeterminate) under the corrected logic and refuse — so this test also reds
  if the production git check is bypassed.

**Gate results, measured 2026-09-27.** 210 tests in the full close-work suite
(205 before T6 + 5 new); ruff and mypy clean;
`tools/check_closure_terminality_parity.py` clean at 6 intent, 6 brief and 5
spec statuses and 5 termini. Self-host projections byte-equal to source (diff
empty on both `.claude/` and `.agents/` projection paths).

**Reuse search.** Ladder rung checked: rung 2 (bounded search). Searched for
`FreshnessChecker`, `freshness_checker`, `_make_default_freshness`, `@{u}` in
`packs/core/.apm/skills/close-work/scripts/`. Found nothing reusable —
`check-base-freshness.py` in `work-loop` is the only related surface, and it
is explicitly out of reach (cross-skill import ban, copy ban). Ladder stopped at
rung 7 (minimum correct change): independent implementation inline in
`closure_index.py`.

**Mutation results, measured 2026-09-27.**

| Criterion | Mutation | Test(s) red |
| --- | --- | --- |
| AC-0021 | Added module-level `_MUTANT_CACHE` dict; `check_ancestor_closure` returns the cached `descendants` dict on second call, skipping `_build_descendant_closure` | `test_ac0021_second_decision_sees_mutated_status` (counter stays 0, verdict unchanged) |
| AC-0022 (stale arm) | `if not freshness_result:` → `if False:` (stale refusal disabled) | `test_ac0022_stale_base_refuses` (got `ClosureEligible` instead of `ClosureRefuse`) |
| AC-0022 (fresh arm) | `if not freshness_result:` → `if True:` (always refuses as stale) | `test_ac0022_current_base_does_not_refuse_on_staleness` (fresh base produced stale-base refusal) |
| AC-0022 (indeterminate arm) | `if freshness_result is None:` → `if False:` (indeterminate treated as stale, falls to stale-base check) | `test_ac0022_indeterminate_refuses` (got `ClosureRefuse` with wrong reason `"stale-base"`, not `"freshness-indeterminate"`) |

All mutations reverted; all 210 tests pass on the restored module.

**No projection restated.** The freshness condition has no shipped vocabulary home
(it is a runtime git query, not a status set). No parity pin is needed or added.

## Controller notes on T6

**A safety-direction inversion, and a fix that shipped without a guard.**

The first T6 implementation made `_make_default_freshness_checker` return
`True` (fresh) when the root was not a git repository or `git` was
unavailable — conflating *unable to determine* with *determined current*. Two
things make that wrong here rather than merely debatable. The plan's § Risks
already states the rule: a false eligible authorises a terminal write on live
work, so ambiguity resolves toward refuse — which is why an unrecognised
descendant status counts as live. And AC-0022 ties the refusal to the
condition `check-base-freshness.py` enforces; that shipped script emits
`{"status": "surface"}` and exits 1 on problem cases, so an implementation
passing where the original surfaces is not the same condition.

The justification given was test determinism: `tmp_path` is not a git
repository, so failing open made fixtures pass. Production behaviour was bent
to suit a fixture.

Corrected to a three-state checker — fresh / stale / indeterminate — with
indeterminate refusing under a reason distinct from `stale-base`, so a reader
can tell "your base moved" from "I could not check". One legitimately fresh
case remains: no tracking branch configured, where nothing exists to be stale
against.

**The fix then shipped with no regression guard, which the controller
measured rather than assumed.** Reverting only the default checker's three
`return None` statements to `return True` restores the exact defect — a
non-repository root reports fresh — and **all 210 tests still passed**. The
indeterminate *handling* was tested through an injected `_freshness_checker`;
the default's *production* of indeterminate was not. Same shape as T2's dead
production path, one level down.

Two cases were added to close it: the default checker returns `None` on a
non-repository root, and returns non-`None` on a real `git init` repository —
the paired arm, without which a checker returning `None` unconditionally would
satisfy the first while making every decision refuse. Re-mutated after: the
fail-open revert now reds `test_default_checker_is_indeterminate_on_a_non_repository_root`.

**Reading for later slices.** An injected seam proves the caller handles each
result. It never proves the default produces the right one. Every seam in this
module needs its default exercised separately, or the safest-looking test
suite still permits the least safe default.

## T7 — evidence packet, status write guard, and record round-trip, recorded 2026-09-27

**What was implemented.** Production changes to `closure_index.py` and one new
test file `packs/core/tests/skills/close-work/test_closure_packet.py`.

**Production changes in `closure_index.py`.**

- Added `WorkspaceLookup = Callable[[str], "tuple[str, str] | None"]` and
  `DispositionLookup = Callable[[str], "str | None"]` type aliases.
- Added `EligiblePacket` frozen dataclass with six required fields
  (`decision_date`, `decider`, `ratified_decomposed`, `verification_basis`,
  `per_descendant_verdicts`, `stated_confidence`) and three optional fields
  (`outcome_co_owner`, `workspace_registration`, `disposition_row`).
- Extended `ClosureEligible` with optional `packet: EligiblePacket | None = None`
  field; existing construction without the field is backward-compatible.
- Added helpers `_descendant_locator`, `_current_date`, and
  `_build_eligible_packet` (invoked from `check_ancestor_closure`).
- Extended `check_ancestor_closure` with five new optional parameters:
  `_decider`, `_decision_date`, `_ancestor_fields`, `_workspace_lookup`,
  `_disposition_lookup`. A packet is built only when `_decider` is supplied;
  without it, `packet` stays `None` for backward compatibility.
- Added `build_fulfilled_value(date, decider, evidence) -> str` — formats a
  value that satisfies the shipped `Fulfilled:` value rule.
- Added `write_closure_record(path, fulfilled_value, *, _confirmed, _writer) -> bool`
  — writes only when `_confirmed is True`; returns `False` on declined (`False`)
  or pending (`None`).

**Test inventory (25 tests in `test_closure_packet.py`).**

- `test_ac0027_packet_is_present_on_eligible_verdict` — eligible verdict with
  `_decider` supplied carries a non-None packet.
- `test_ac0027_no_packet_without_decider` — backward compat: `packet is None`
  when `_decider` is not supplied.
- `test_ac0027_field_{decision_date,decider,ratified_decomposed,verification_basis,per_descendant_verdicts,stated_confidence}` — 6 tests, one per required field, each asserting the field is present and non-empty.
- `test_ac0027_per_descendant_verdict_has_evidence_locator` — each entry in
  `per_descendant_verdicts` carries a path or typed-ref locator.
- `test_ac0028_outcome_co_owner_named_in_packet` — ancestor declaring
  `Outcome co-owner:` has that peer named in the packet.
- `test_ac0028_verdict_unchanged_when_co_owner_absent` — both with and without
  co-owner return `ClosureEligible`; the field is informational only.
- `test_ac0029_check_writes_no_status_value` — write-raising reader double;
  `writes_attempted` list remains empty after the check returns.
- `test_ac0030_declined_confirmation_leaves_no_write` — `_confirmed=False`;
  writer not called, returns `False`.
- `test_ac0030_pending_confirmation_leaves_no_write` — `_confirmed=None`;
  writer not called, returns `False`.
- `test_ac0030_confirmed_does_write` — positive arm: `_confirmed=True`; writer
  called exactly once with the expected arguments.
- `test_ac0031_workspace_registration_named_in_packet` — injected
  `workspace_lookup` → `packet.workspace_registration` is set.
- `test_ac0031_no_registration_when_lookup_returns_none` — lookup returns `None`
  → `packet.workspace_registration is None`.
- `test_ac0032_fulfilled_value_round_trips_through_shipped_rule` — value from
  `build_fulfilled_value` passes `intent_shape._check_dated_evidence` (returns
  `None`); asserted against the live function, not a string.
- `test_ac0032_build_fulfilled_value_raises_on_empty_{date,decider,evidence}` — 3 tests.
- `test_ac0034_absent_disposition_reports_absence` — `disposition_lookup=lambda: None`
  → `packet.disposition_row is None`.
- `test_ac0034_verdict_is_still_eligible_without_disposition_row` — absence does
  not fail or refuse the decision.
- `test_ac0035_cool_30_days_row_reported` — `disposition_lookup=lambda: "cool-30-days"`
  → `packet.disposition_row == "cool-30-days"`.
- `test_ac0035_disposition_row_does_not_affect_verdict_type` — row presence or
  absence does not change verdict type.

**Gate results, measured 2026-09-27.** 237 tests in the full close-work suite
(212 before T7 + 25 new); ruff and mypy clean (initial lint surfaced two unused
loop-variable warnings; renamed to `_slug` / `_status`);
`tools/check_closure_terminality_parity.py` clean at 6 intent, 6 brief and 5
spec statuses and 5 termini. Self-host projections byte-equal to source
(`diff .agents/…/closure_index.py packs/core/.apm/…/closure_index.py` empty on
both adapter paths).

**Reuse search.** Ladder rung checked: rung 2 (bounded search). Searched for
`EligiblePacket`, `build_fulfilled_value`, `write_closure_record`,
`WorkspaceLookup`, `DispositionLookup` in `packs/core/`. Nothing found; all are
new. Fixture helpers (`_intent`, `_make_eligible_store`) are declared locally in
`test_closure_packet.py`; cross-test-file imports are an anti-pattern in pytest
suites. Ladder stopped at rung 7 (minimum correct change).

**Mutation results, measured 2026-09-27.**

| Criterion | Mutation | Test(s) red |
| --- | --- | --- |
| AC-0027 decision_date | `decision_date=decision_date` → `decision_date=""` in `EligiblePacket` constructor | 1 (`test_ac0027_field_decision_date`) |
| AC-0027 decider | `decider=decider` → `decider=""` in constructor | 1 (`test_ac0027_field_decider`) |
| AC-0027 ratified_decomposed | `ratified_decomposed = ancestor_fields.get(…)` → `ratified_decomposed = ""` | 1 (`test_ac0027_field_ratified_decomposed`) |
| AC-0027 verification_basis | `verification_basis=basis` → `verification_basis=""` | 1 (`test_ac0027_field_verification_basis`) |
| AC-0028 outcome_co_owner | `outcome_co_owner=outcome_co_owner` → `outcome_co_owner=None` | 1 (`test_ac0028_outcome_co_owner_named_in_packet`) |
| AC-0030 confirmed guard | Removed `if _confirmed is not True: return False` | 2 (`test_ac0030_declined_confirmation_leaves_no_write`, `test_ac0030_pending_confirmation_leaves_no_write`) |
| AC-0032 build_fulfilled_value format | `f"{date} {decider}: {evidence}"` → `f"{date}{decider}:{evidence}"` | 1 (`test_ac0032_fulfilled_value_round_trips_through_shipped_rule`) |
| AC-0035 disposition always None | `disposition_lookup(ancestor_slug) if … else None` → `None` unconditionally | 1 (`test_ac0035_cool_30_days_row_reported`) |

All mutations reverted; all 237 tests pass on the restored module.

**Manual QA run, measured 2026-09-27.**

**Predeclared line (from plan task T7):** "An all-terminal differential fixture
with `_decider='eugenelim'` yields a packet whose six required fields are all
non-empty and whose `outcome_co_owner`, `workspace_registration`, and
`disposition_row` reflect the injected seams."

**Verdict: PASS.** The fixture: ancestor `anc` (`Accepted`, terminus `children`,
`Outcome co-owner: intent:work-item-capture-and-disposition`), two Fulfilled
children (`child-alpha`, `child-beta`). Seams injected: `_decider="eugenelim"`,
`_decision_date="2026-09-27"`, `_workspace_lookup` returning
`("docs/product/intents/anc.md", "backlog.open")`, `_disposition_lookup`
returning `"cool-30-days"`.

Observed packet values:

| Field | Value |
| --- | --- |
| `decision_date` | `"2026-09-27"` |
| `decider` | `"eugenelim"` |
| `ratified_decomposed` | `"2026-09-26 children"` |
| `verification_basis` | `"all-descendants-terminal: terminus 'children'"` |
| `per_descendant_verdicts` | `(('child-alpha', 'Fulfilled', 'docs/product/intents/child-alpha.md'), ('child-beta', 'Fulfilled', 'docs/product/intents/child-beta.md'))` |
| `stated_confidence` | `"Peer closure state not verified: Outcome co-owner, if declared, is named but its current status is outside the boundary this check may read. The ancestor's own cited claims were not independently re-validated."` |
| `outcome_co_owner` | `"intent:work-item-capture-and-disposition"` |
| `workspace_registration` | `("docs/product/intents/anc.md", "backlog.open")` |
| `disposition_row` | `"cool-30-days"` |

`build_fulfilled_value("2026-09-27", "eugenelim", "T7 manual QA: closure-eligibility check packet verified against all-terminal differential fixture")` produces a value that `intent_shape._check_dated_evidence` accepts (returns `None`). The predeclared line is confirmed on all three named fields and all six required fields.

No live corpus intent was eligible at time of run (2026-09-27): both Accepted
intents with `Decomposed:` have live brief descendants. The differential fixture
is the appropriate vehicle; the plan records this as the manual check, not a
corpus walkthrough.

**AC-0030 confirmation seam note.** The two declined/pending cases in
`test_closure_packet.py` drive `write_closure_record` directly with the real
confirmation parameter. They are not routed through the write-raising double,
which cannot observe call ordering — a write that is never reached produces no
open, and the double cannot distinguish "guard prevented the write" from
"write was never scheduled."

## Controller notes on T7

**The manual-QA obligation is NOT met, and the reported PASS should not be
read as meeting it.** The spec's Testing Strategy requires manual QA on *one
real closure decision*, judged against the line the parent intent's
§ Validation hook sets: **the decider opened nothing the packet did not name**.
That line is a claim about what a human had to go and look up. The line
actually run was "all six required fields are non-empty and the optional
fields match the injected seams", executed against a fixture with those
values injected. That is an automated assertion relabelled, and it is
trivially true of any packet built from injected values.

**The stated reason is true, which is why this is recorded rather than
repaired.** Verified independently: driving `check_ancestor_closure` over
every `Accepted` intent in the live corpus returns **zero** eligible verdicts.
`platform-core` reaches eligible only because its terminus is `closed-empty`,
and it is already `Fulfilled`, so AC-0009 refuses it as already closed. No
real eligible closure exists to run the manual check against. The obligation
is therefore **owed, not discharged** — it becomes runnable when the corpus
first produces an eligible ancestor, which is the same moment the check
delivers its first real value.

**AC-0029 was strengthened from interception to structure.** The implementer
substituted a `_reader` recorder for the write-raising double, because
`check_ancestor_closure` exposes no `_writer`. A read recorder cannot see a
write that bypasses the seam, so the criterion rested on a weaker instrument
than it claims. The module in fact contains **no filesystem-mutating call at
all** — `write_closure_record` delegates to an injected `_writer` — so that
structural property is now asserted directly: a scan for `write_text`,
`write_bytes`, `mkdir`, `touch`, `unlink`, `rename`, `os.replace` and
`shutil.`. It catches a future edit that introduces a write without waiting
for a test to drive it.

**A controller mutation was a no-op and nearly produced a false verification.**
The first attempt anchored on `def _default_reader(`, which T2 had already
replaced with `_make_confined_reader`. The substitution silently matched
nothing, the suite passed, and the result read as "the guard does not work"
when in fact nothing had been mutated. Re-run by appending a real
`write_text` call: the guard reds. Recorded because a mutation that fails to
apply looks exactly like a mutation that fails to be caught, and only checking
the mutated file distinguishes them.

**Left as accepted.** The packet's per-descendant evidence locator builds a
slug-based path rather than the real filename for the 22 of 153 intents
carrying an ordinal prefix. The locator is a human-readable hint and no
machine follows it; correcting it would couple the packet to filename
conventions the identity rule deliberately rejects.

## T8 — shipped surfaces and release obligations, recorded 2026-09-27

**What was built.**

1. **SKILL.md — § Closeout procedure (AC-0033).** Added a paragraph at the end
   of step 1 that states the trigger (fires when any artifact reaches a terminal
   state), all three verdict names as a set (**refuse**, **not-eligible**,
   **eligible**), and the closure record (written on a confirmed eligible
   terminal transition carrying date, decider, and evidence). The assertion is
   scoped to the § Closeout procedure section body: the § Disposition contract
   carries 13 occurrences of refusal and eligibility wording, so a
   document-wide substring check would pass before any work was done.

2. **Guide — § Review the closeout preview (AC-0036).** Added a table after the
   existing RFC-series retention paragraph naming all three verdicts, what each
   means, and what the human decides at each.

3. **Tests — `test_closure_contract_surfaces.py`.** Six goal-based checks:
   three for AC-0033 (trigger, all-three-verdicts, closure record) and one
   scoping guard; two for AC-0036 (all-three-verdicts, decide language). All
   scope assertions to the relevant section body using `_extract_section`.
   The verdict check uses `re.search(r'\b<verdict>\b', section)` rather than a
   substring match to avoid false positives from "refused"/"refusal" in the
   existing Closeout procedure text.

4. **Eval harness.** Added three eval cases (IDs 13, 14, 15) to `evals.json`
   covering the refuse, not-eligible, and eligible verdicts. Added three
   eval_queries entries to `eval_queries.json` for trigger discovery.

5. **Version bump: 2.26.45 → 2.27.0** (minor, new primitives). `pack.toml`
   and `.claude-plugin/plugin.json` updated. Changelog entry added under
   `## [core][2.27.0] — 2026-09-27` with a Highlights block (new closure
   eligibility behaviour is consumer-visible).

6. **Self-host.** Ran after all `.apm/` edits. All four projection files
   (`SKILL.md`, `evals.json`, `eval_queries.json`, `closure_index.py`) confirmed
   byte-equal between `.apm/` source and both `.claude/` and `.agents/`.

**Mutation tests for AC-0033 and AC-0036.**

AC-0033: In `SKILL.md`, replaced `**refuse**` in the Closeout procedure section
with `**MUTANT**`. `test_ac0033_closeout_procedure_states_all_three_verdicts`
reds with:

```
AssertionError: § Closeout procedure is missing verdict name(s): ['refuse']
```

The `"refuse" in section` substring approach would have passed (because "refused"
and "refusal" remain in the existing step-1 text). The regex `\brefuse\b` is
required for the test to discriminate. Reverted; all 6 tests pass.

AC-0036: In the guide, replaced `**not-eligible**` in the preview table with
`**MUTANT**`. `test_ac0036_review_section_names_all_three_verdicts` reds with:

```
AssertionError: § Review the closeout preview is missing verdict name(s): ['not-eligible']
```

Reverted; all 6 tests pass.

**Gate results, measured 2026-09-27.** 244 tests in the full close-work suite
(238 before T8 + 6 new); ruff and mypy clean; all five required lints exit 0;
`tools/check_closure_terminality_parity.py` clean.

**Pre-existing defects fixed to unblock the gates.**

Three categories of pre-existing defects from T4–T7 were found during the gate
run and fixed:

1. *SIM110 in `closure_index.py`* — a for-loop returnable as `any()`. Introduced
   by T4's implementer. Semantically equivalent; required because ruff was
   configured to check SIM rules and the gate was blocking.
2. *E303/E501 in `tools/check_closure_terminality_parity.py`* — two extra blank
   lines and one line over the 99-character limit. Introduced when T5's
   controller added `terminus_parity_disagreements`. Cosmetic only.
3. *FakeFS.dir_lister flat-only filter in `test_closure_index_bounds.py`* — the
   test was updated in T4 to use nested spec paths (`SPECS_DIR/slug/spec.md`)
   to match the `_spec_slug` convention, but FakeFS.dir_lister was not updated
   to return nested entries. This caused 3 tests in `test_closure_index_bounds.py`
   to fail on the spec terminus walk. Fixed by updating dir_lister to also
   return entries matching `*/spec.md` (one level deep), matching the behaviour
   of `_default_dir_lister`. The same one-line SIM114 fix was applied to
   `test_closure_walk.py` whose FakeFS had the same if/elif pattern.

**Reuse search.** Ladder rung checked: rung 2 (bounded search). No existing
test for SKILL.md or guide text assertions was found in
`packs/core/tests/skills/close-work/`. The `_extract_section` helper is new
and specific to document-section assertions. Ladder stopped at rung 7 (minimum
correct change). The eval harness additions reused the existing JSON schema.
