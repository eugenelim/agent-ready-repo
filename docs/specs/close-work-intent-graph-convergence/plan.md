# Plan: Close-work intent graph convergence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/DESIGN.md` § Intent-edge derivation: source, copies, pins, and consumers (names this copy as the planned convergence); analogous implementation: `closure_index.py`'s own `_run_resolver` and `_get_closure_terminality`, which load a co-located copy after an `lstat` regular-file check and expose a provider seam (`_snapshot_provider`); their tests: `packs/core/tests/pack/test_intent_delivery_relations_copies.py` and `packs/core/tests/skills/close-work/test_closure_delivery_snapshot.py`; deviation: the derivation's helper loaders use fixed module names, so a second copy binds the first copy's helpers (T1 corrects this).

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

Put the copy in place first and make it safe to load beside the navigator's copy (T1). Then move the downward `children` arm onto it behind a provider seam (T2), then the upward walk (T3). Removing the old parser comes after both arms have moved, so no state exists where neither path parses parents (T4). The real-corpus comparison runs once the new code is complete and before the docs land (T5), so any unattributed difference stops the work before release prose claims a result. Docs, the frozen spec's pointer, and the release come last (T6).

The riskiest part is migrating the existing `children`-arm tests. They describe intent files through an injected `_reader` and `_dir_lister`, and the derivation reads the real filesystem through its confinement helper. The `_graph_provider` seam lets those tests inject a derived graph built from the same fixture text, so they keep their shape.

## Constraints

- RFC-0105 D1: one derivation feeds every intent-graph reader; each relationship keeps its basis and trust class.
- RFC-0103 and its 2026-10-08 errata entry: the typed reference grammar the derivation resolves.
- ADR-0119: the closure check's place in the lifecycle.
- ADR-0007 and ADR-0074: agent-invoked skill scripts, standard library only.
- The catalogue authoring standards ban cross-skill imports, so `close-work` loads its own copy.
- `packs/AGENTS.md`: tests load modules under unique names; a non-cosmetic `core` change bumps `pack.toml` and `plugin.json` together, updates the eval harness, and is projected with `agentbundle catalogue self-host --root . --write`.
- The brief's publication constraint: this slice merges into `feature/intent-navigation` while that branch is open.
- FEAT-0002's 2026-10-07 Amendment, with the owner's 2026-10-10 addition of the third cause, bounds which verdicts may change (spec AC-0015).

## Construction tests

**Integration tests:** `test_closure_parent_edges_corpus` runs `check_ancestor_closure` and `resolve_intent_ancestors` with no seams injected over one temporary fixture corpus. That corpus holds all four typed prefixes, a path-form parent, a tombstone, a brief sharing its parent's slug, and a two-level chain. This proves the default provider loads the copy from `close-work/scripts/` and the arms agree end to end.

**Manual verification:** none beyond T5's corpus comparison.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure — `guides/core/how-to/close-and-disposition-work.md` | T6 | Guide lints green | Both reasons listed with cause and remedy |
| Architecture — `packs/core/DESIGN.md` | T6 | Section diff | Consumer, copy, pin, and no-second-parser statements present |
| Historical contract pointer — `closure-eligibility-check/spec.md` `Status:` | T6 | AC-0014's test | Test green |
| Release history — changelog `[core][3.1.1]`, versions | T6 | Changelog and version diff | `/now/` projection test green |
| Executable proof — `packs/core/tests/skills/close-work/`, copies test, parity tool test | T1–T4 | Suites green | Run ids in the ledger |
| Verification record — `notes/verification-ledger.md` | T5 | Ledger entry | Cited by the closing PR |
| Design facts below (seam, loader naming, refusal mapping) | T1–T3 | Code and docstrings | Mechanically inferable from `closure_index.py` and its tests once merged; no further owner |

## Design (LLD)

### Interfaces & contracts

- `closure_index.py` gains a keyword-only test seam `_graph_provider: Callable[[Path], dict[str, Any]] | None` on `check_ancestor_closure`, `_build_descendant_closure`, and `resolve_intent_ancestors`, beside the existing `_snapshot_provider`. Its default loads `close-work/scripts/intent_graph.py` under the module name `core_close_work_intent_graph`. It uses the `lstat` regular-file discipline of `_get_closure_terminality`, then calls `derive(root)`.
- Refusal reasons: `intent-graph-unavailable: <code>`, where `<code>` is the derivation's `DerivationError.code`. A copy that cannot be loaded gives `intent-graph-unavailable: copy-unavailable`. `parent-edge-refused` covers the AC-0010 and AC-0011 cases. Inside the closure decision they are raised as `_ClosureDeliveryRefusal` and returned as `ClosureRefuse`. From `resolve_intent_ancestors` they are raised as `_ClosureDeliveryRefusal`, as its resolver failure already is.
- Traces to AC-0009, AC-0010, AC-0011, AC-0012.

Owned by: T2, T3

### Behavior & rules

- **Ancestor node.** The ancestor's node is the live intent node whose `slug` equals the ancestor slug. The derivation already refuses a duplicate intent slug as `duplicate_identity`.
- **Children.** These are the intent nodes with an edge whose `field` is `Parent intent`, whose `from` is an intent node, and whose `to` is the ancestor's node id. Their `Status:` and `Decomposed:` come from one open by `close-work`'s own reader, which keeps the existing visited set. Tombstones are never nodes, so AC-0005 holds without a rule of its own.
- **Names A.** A refused edge names ancestor `A` when its `value`, or a value in `basis.values` for `multiple_values`, does either of these:
  - It equals `A`'s slug after removing a leading `<kind>:` prefix from the reference grammar.
  - It is a repository path equal to `A`'s `path`.
- **Upward walk.** Start from the artifact's node: `intent` by slug, `brief:<slug>` for a brief. Follow the single resolved `Parent intent` edge out of each node. The visited set is keyed by node id, not bare slug. That keying is what fixes cause 3. A spec's first hop stays on the resolver snapshot. A refused edge met on the walk raises `parent-edge-refused`.
- **Lazy derivation.** A decision calls the provider on its first `children` terminus only, and caches the graph for that decision alone. That keeps AC-0012's zero-run case and `closure-eligibility-check`'s no-reuse rule, its criterion 0021.
- Traces to AC-0004 through AC-0013.

Owned by: T2, T3

### Component / module decomposition

- **Loader binding.** Both copies of `intent_graph.py` name their helper modules from their own folder, for example `core_<skill-dir>_file_safety` and `core_<skill-dir>_resolver`, with the skill directory name's hyphens replaced by underscores. A byte-identical copy can then bind its own helpers. Slice 1's tests do not reference the fixed names, so none move.
- **Removals.** `closure_index.py` loses `_is_parent_edge`, `REFERENCE_KIND_VOCABULARY`, `REFERENCE_KIND_UPSTREAM_*`, and `reference_kind_parity_disagreements`. `tools/check_closure_terminality_parity.py` loses the reference-kind check. It keeps `_walk_is_not_vacuous`, which now exercises the derivation-backed `children` arm over the real corpus.
- Traces to AC-0001, AC-0002, AC-0003.

Owned by: T1, T4

### Failure, edge cases & resilience

- Every derivation failure refuses. None degrades to an empty descendant set or an empty chain, because an empty set reads as a legitimate refusal or eligibility ground.
- Traces to AC-0009, AC-0010, AC-0011.

Owned by: T2, T3

### Quality attributes (NFRs)

- **Cost.** The derivation took 0.09–0.19 s over the real corpus in the 2026-10-10 spike, running from a copy of `close-work/scripts/`. A `children` decision adds one run. No bar is set. T5 records the observed time in the ledger.
Owned by: T5

## Tasks

### T1: Copy in place, bound to its own helpers, and pinned

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, `packs/core/tests/pack/test_intent_delivery_relations_copies.py`, `packs/core/tests/skills/close-work/test_closure_graph_copy.py`

**Tests:**
- AC-0001: extend the byte-identity loop in `test_vi1904_only_canonical_delivery_inverter_exists` with a pair assertion: `close-work/scripts/intent_graph.py` against `navigate-intents/scripts/intent_graph.py`.
- AC-0002: `test_closure_graph_copy.py::test_each_copy_binds_its_own_helpers` loads both copies under unique names, in both orders, in subprocess-free fresh `sys.modules` snapshots. It asserts each copy's `_get_file_safety().__file__` and `_get_resolver().__file__` sit in that copy's folder. Stub (red today: the close-work copy binds `navigate-intents/scripts/_file_safety.py`, observed in the spike):

```python
def test_each_copy_binds_its_own_helpers(monkeypatch):
    for first, second in ((NAV, CW), (CW, NAV)):
        monkeypatch.setattr(sys, "modules", dict(sys.modules))
        mods = {d: _load(f"_t_ig_{d.parent.name}_{first.parent.name}", d / "intent_graph.py") for d in (first, second)}
        for d, m in mods.items():
            assert Path(m._get_file_safety().__file__).parent == d
            assert Path(m._get_resolver().__file__).parent == d
```

**Done when:** both tests are green, and the `navigate-intents` suite is green unchanged.

### T2: Descendant closure takes children from the derivation

**Depends on:** T1
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_*.py`, `packs/core/tests/skills/close-work/test_closure_parent_edges.py`

**Tests:**
- AC-0004: `test_closure_parent_edges.py` runs one fixture per prefix (`intent:`, `capability:`, `outcome:`, `opportunity:`) plus a path-form parent. A temporary corpus goes through `check_ancestor_closure` with the default provider, and the test asserts the live-descendant names in a `ClosureNotEligible`.
- AC-0005: a tombstone whose `Parent intent:` names the ancestor sits beside one live child, and the closure holds only the live child.
- AC-0009 (decision part): a provider that raises `DerivationError("duplicate_identity", …)` gives `ClosureRefuse` with reason `intent-graph-unavailable: duplicate_identity`. A missing copy gives `intent-graph-unavailable: copy-unavailable`.
- AC-0010: run one fixture per derivation state that can name `A`: `multiple_values` with one value naming `A`, a `cycle` through `A`, and a `retired_target` path form naming `A`'s file. Each gives `parent-edge-refused`.
- AC-0012: a counting provider shows one call for a `children` decision and two nested `children` levels. It shows zero calls for `brief`, `spec`, `closed-empty`, and `direct-light` decisions.
- AC-0013: a counting `_reader` over a diamond fixture shows each path opened at most once, and every opened path in the descendant locators.
- Integration: `test_closure_parent_edges_corpus` (see Construction tests).
- Migration: the `children`-arm cases in `test_closure_walk.py`, `test_closure_index_bounds.py`, `test_closure_packet.py`, `test_closure_staleness.py`, `test_closure_verdict_coverage.py`, `test_closure_entry.py`, and `test_closure_delivery_snapshot.py` pass a `_graph_provider` built from their fixture text. Each keeps its asserted verdict. A bound test that counted intent-collection candidate opens now asserts the AC-0013 bound.

**Approach:**
- Migrate the existing tests in the same commit as the seam. A suite left on `_dir_lister` alone would pass by never reaching the new arm.

**Done when:** every listed test is green, and `python3 -m pytest packs/core/tests/skills/close-work -q` is green.

### T3: Upward walk takes parent edges from the derivation

**Depends on:** T2
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_parent_edges.py`, `packs/core/tests/skills/close-work/test_closure_entry.py`, `packs/core/tests/skills/close-work/test_closure_t11_vi.py`, `packs/core/tests/skills/close-work/test_closure_broken_spec_refusal.py`

**Tests:**
- AC-0006: a four-level chain uses a different prefix at each hop. `resolve_intent_ancestors` from the bottom intent, and from a brief at the bottom, returns all live ancestors nearest first.
- AC-0007: a spec with one delivery relation and one non-feature `Discovery:` provenance record, through an injected snapshot, returns both intents first, each followed by its own chain.
- AC-0008: a brief `x` with `Parent intent: intent:x` returns intent `x` first.
- AC-0009 (walk part): a failing provider raises `_ClosureDeliveryRefusal` with `intent-graph-unavailable: <code>`.
- AC-0011: run one fixture per refusal state the derivation returns for an intent's or a brief's `Parent intent:` (`dangling`, `retired_target`, `kind_mismatch`, `out_of_type`, `multiple_values`, `cycle`, `unparseable`), each placed on the walked artifact and again on a reached ancestor. Each raises `parent-edge-refused`.
- Migration: the existing `resolve_intent_ancestors` cases keep their expected chains.

**Done when:** the listed tests and the full `close-work` suite are green.

### T4: The old parent parser is gone

**Depends on:** T3
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `tools/check_closure_terminality_parity.py`, `tools/test_check_closure_terminality_parity.py`, `packs/core/tests/skills/close-work/test_closure_graph_copy.py`

**Tests:**
- AC-0003: `test_closure_graph_copy.py::test_no_preamble_parent_read` parses `closure_index.py` with `ast`. It fails on any subscript or `.get` whose key is the literal `"Parent intent"`, unless the enclosing function is `_build_brief_parent_feat_map` or `_validate_snapshot_dict`. It also fails if `_is_parent_edge` or `REFERENCE_KIND_VOCABULARY` is defined.
- `tools/test_check_closure_terminality_parity.py` drops its reference-kind cases, and `python3 tools/check_closure_terminality_parity.py` exits 0 on the real corpus.

**Done when:** both checks are green.

### T5: Real-corpus verdict comparison recorded

**Depends on:** T4
**Touches:** `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md`

**Tests:**
- AC-0015: a throwaway script outside the repository, its source pasted into the ledger, loads two modules. One is `closure_index.py` at the base commit (`git show <base>:…` into a temporary folder holding that commit's `close-work/scripts/`). The other is the working tree's.
  - For every live intent, brief, and spec, it compares `resolve_intent_ancestors` output.
  - For every distinct ancestor, it compares `check_ancestor_closure` verdict kind and reason, with `_freshness_checker=lambda: True`.
  - It attributes each difference by the first hop where the chains diverge: that hop's value prefix (cause 1), a tombstone file at the old match (cause 2), or the walker's own slug (cause 3).
  - It exits 1 on any unattributed difference.
  - The 2026-10-10 probe counted 74 chain differences: 70 from cause 1, 4 from cause 3, 0 from cause 2. The ledger records the run's own counts.

**Done when:** the ledger records the base commit, exit code 0, the per-cause counts, and one timed derivation run.

### T6: Docs, frozen pointer, and release

**Depends on:** T5
**Touches:** `guides/core/how-to/close-and-disposition-work.md`, `packs/core/DESIGN.md`, `docs/specs/closure-eligibility-check/spec.md`, `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/.apm/skills/close-work/evals/evals.json`, `tests/roster/test_close_work_graph_convergence_supersession.py`, adapter projections

**Tests:**
- AC-0014: `tests/roster/test_close_work_graph_convergence_supersession.py` reads the `Status:` line for the prefix, this spec's path, and the three criterion ids. It compares every `- [x]` line against `git show <base>:docs/specs/closure-eligibility-check/spec.md`, using the merge base with `origin/feature/intent-navigation`.
- The guide lints named in the spec's Durable Outputs are green.
- An eval case is added to `close-work/evals/evals.json` for a closure whose child records a refused parent pointer, expecting `parent-edge-refused` to be named.
- `agentbundle catalogue self-host --root . --write` leaves no diff on a re-run. `make lint-ruff lint-mypy` is green.

**Approach:**
- The `Status:` pointer is spec-to-spec, not spec-to-ADR. No ADR governs this change; the decision lives in FEAT-0002's Amendment and this spec. `catalogue-sync-dry-run`'s `Status:` line is the precedent.

**Done when:** the listed checks are green, the versions read `3.1.1`, and the changelog entry carries a `### Highlights` bullet.

## Rollout

- **Delivery:** one pull request into `feature/intent-navigation`, released as `core` 3.1.1 when that branch merges to the default branch under slice 4. Reversible by revert. Nothing is persisted.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** slice 4's rebase refreshes resolver copies. That refresh now also covers `close-work/scripts/intent_graph.py`, which AC-0001's pin keeps in step.

## Risks

- About 70 artifacts gain ancestors they never had: capability, outcome, and opportunity parents. Closers will see verdicts for those ancestors for the first time, often `not-accepted` refusals on Draft capabilities. This is the intended correction. The changelog highlight says so.
- Test migration in T2 is wide. A test moved onto `_graph_provider` with a graph that disagrees with its fixture text would pass while testing nothing. The integration test runs with no seams to catch that.

## Changelog
