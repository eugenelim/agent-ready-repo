# Plan: Close-work intent graph convergence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
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

Put the copy in place first and make it safe to load beside the navigator's copy (T1). Then move the downward `children` arm onto it behind a provider seam, and key the descendant set by kind and slug (T2). The upward walk follows (T3). The old parser goes, and the parent-kind parity check moves to the kinds the derivation reads, only after both arms have moved, so no state exists where neither path parses parents (T4). The real-corpus comparison runs once the new code is complete and before the docs land (T5), so an unattributed difference stops the work before release prose claims a result. Docs, the frozen spec's pointer, and the release come last (T6).

The riskiest part is migrating the existing `children`-arm and ancestor-walk tests. They describe intent files through an injected `_reader` and `_dir_lister`, or through in-memory `fields` for artifacts never written to disk, and the derivation reads the real filesystem through its confinement helper. The `_graph_provider` seam lets those tests inject a derived graph built from the same fixture text. Ancestor-walk cases that relied on unwritten `fields` move to fixture files.

## Constraints

- RFC-0105 D1: one derivation feeds every intent-graph reader; each relationship keeps its basis and trust class.
- RFC-0103 and its 2026-10-08 errata entry: the typed reference grammar the derivation resolves.
- ADR-0119: the closure check's place in the lifecycle.
- ADR-0007 and ADR-0074: agent-invoked skill scripts, standard library only.
- The catalogue authoring standards ban cross-skill imports, so `close-work` loads its own copy.
- `packs/AGENTS.md`: tests load modules under unique names; a non-cosmetic `core` change bumps `pack.toml` and `plugin.json` together, updates the eval harness, and is projected with `agentbundle catalogue self-host --root . --write`.
- The brief's publication constraint: this slice merges into `feature/intent-navigation` while that branch is open.
- FEAT-0002's 2026-10-07 and 2026-10-10 owner Amendments bound which verdicts may change (spec AC-0015) and authorise superseding the closure check's read bounds.
- FEAT-0005's Boundary condition (c), read as the closure check records it: the verdict uses only the ancestor chain and the descendant closure; discovery may read more.

## Construction tests

**Integration tests:** `test_closure_parent_edges_corpus` runs `check_ancestor_closure` and `resolve_intent_ancestors` with no seams injected over one temporary fixture corpus. That corpus holds all four typed prefixes, a path-form parent, a tombstone, a brief sharing its parent's slug, an intent with a same-slug brief beneath it, and a two-level chain. This proves the default provider loads the copy from `close-work/scripts/` and the arms agree end to end.

**Manual verification:** none beyond T5's corpus comparison.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision record — FEAT-0002 Amendment 2026-10-10, brief constraint | none (lands with spec approval) | Diff in the approval change | Amendment present |
| User procedure — `guides/core/how-to/close-and-disposition-work.md` | T6 | Guide lints green | All three reasons listed with cause and remedy |
| Architecture — `packs/core/DESIGN.md` | T6 | Section diff | Consumer, copy, pin, and no-second-parser statements present |
| Historical contract pointer — `closure-eligibility-check/spec.md` `Status:` | T6 | AC-0014's test | Test green |
| Release history — changelog `[core][3.1.1]`, versions | T6 | Changelog and version diff | `/now/` projection test green |
| Executable proof — `packs/core/tests/skills/close-work/`, copies test, parity tool test | T1–T4 | Suites green | Run ids in the ledger |
| Verification record — `notes/verification-ledger.md` | T5 | Ledger entry | Cited by the closing PR |
| Design facts below (seam, loader naming, refusal mapping, keying) | T1–T4 | Code and docstrings | Mechanically inferable from `closure_index.py` and its tests once merged; no further owner |

## Design (LLD)

### Interfaces & contracts

- `closure_index.py` gains a keyword-only test seam `_graph_provider: Callable[[Path], dict[str, Any]] | None` on `check_ancestor_closure`, `_build_descendant_closure`, and `resolve_intent_ancestors`, beside the existing `_snapshot_provider`. Its default loads `close-work/scripts/intent_graph.py` under the module name `core_close_work_intent_graph`. It uses the `lstat` regular-file discipline of `_get_closure_terminality`, then calls `derive(root)`.
- Refusal reasons:
  - `intent-graph-unavailable: <code>`. `<code>` is the `code` attribute of a raised `DerivationError`, matched by class name so the copy's own class is recognised. Every other exception from loading the copy or running `derive()`, an `ImportError` from its helper loaders included, gives `copy-unavailable`. This mirrors `_get_snapshot`, which already catches every exception.
  - `parent-edge-refused` for the AC-0010 and AC-0011 cases.
  - `artifact-not-in-graph` for AC-0017 (the walked artifact has no node) and AC-0007 (a spec's first-hop intent has no node).
- Inside the closure decision these are raised as `_ClosureDeliveryRefusal` and returned as `ClosureRefuse`. From `resolve_intent_ancestors` they are raised as `_ClosureDeliveryRefusal`, as its resolver failure already is.
- The copy loader takes a keyword-only `_graph_module_path: Path | None` override, on the pattern of `_run_resolver`'s `_resolver_path`, so a test can point it at a missing or linked file.
- `resolve_intent_ancestors` keeps its signature. Its `fields` argument stays for the spec route's compatibility and supplies no parent edge for an intent or brief.

Traces to AC-0006, AC-0007, AC-0009, AC-0010, AC-0011, AC-0012, AC-0017.

Owned by: T2, T3

### Behavior & rules

- **Node lookup.** An intent is found as the live intent node with that `slug`. A brief is found as node `brief:<slug>`. The derivation refuses a duplicate intent or brief slug as `duplicate_identity`, so each lookup has at most one answer.
- **Children.** These are the intent nodes with an edge whose `field` is `Parent intent`, whose `from` is an intent node, and whose `to` is the ancestor's node id. Their `Decomposed:` comes from one open by `close-work`'s own reader. Tombstones are never nodes, so AC-0005 holds without a rule of its own.
- **Refused edges that bear on a decision.** For each intent on the closure whose terminus is `children`, the evaluated ancestor included, refuse when a refused `Parent intent` edge from an intent node names it. Use the AC-0010 naming rule, reading the prefixes from the loaded copy's resolver (`_get_resolver()._PARENT_INTENT_KINDS`). Strip only those intent prefixes, so an `out_of_type` value such as `brief:x` never names intent `x`. The states that can name a live intent are `kind_mismatch`, `multiple_values`, and `cycle`. `dangling`, `retired_target`, and `out_of_type` resolve only when no live intent matches, or when the value names another type.
- **Descendant keying.** The descendant set is keyed by `(kind, slug)`, and the brief arm's seen-set likewise. `ClosureNotEligible.live_descendants` keeps its `(slug, status)` pairs, so a same-slug intent and brief can both appear.
- **Upward walk.** Start from the artifact's own node (AC-0017 refuses when absent) and follow the single resolved `Parent intent` edge out of each node. The visited set is keyed by node id, seeded with the walked artifact's own node id. A spec's first hop stays on the resolver snapshot, depth-first in snapshot order: relations, then provenance records. Each first-hop intent is looked up as a derivation node; one with no node raises `artifact-not-in-graph`. The visited set skips only an intent node already returned. Each ancestor's status is the node's `status`. Its terminus comes from one open of the node's `path` by `close-work`'s own reader. A refused edge met on the walk raises `parent-edge-refused`.
- **Lazy derivation.** A decision calls the provider on its first `children` terminus only, and caches the graph for that decision alone. That keeps AC-0012's zero-run case and `closure-eligibility-check`'s no-reuse rule, its criterion 0021.

Traces to AC-0004 through AC-0013, AC-0017, AC-0018.

Owned by: T2, T3

### Component / module decomposition

- **Loader binding.** Both copies of `intent_graph.py` name their helper modules from their own folder, for example `core_<skill-dir>_file_safety` and `core_<skill-dir>_resolver`, with the skill directory name's hyphens replaced by underscores. A byte-identical copy can then bind its own helpers. Slice 1's tests do not reference the fixed names, so none move.
- **Removals.** `closure_index.py` loses `_is_parent_edge`, `REFERENCE_KIND_VOCABULARY`, `REFERENCE_KIND_UPSTREAM_*`, and `reference_kind_parity_disagreements`.
- **Parity retarget.** `tools/check_closure_terminality_parity.py` replaces its reference-kind check with one comparing `close-work/scripts/intent_delivery_relations.py`'s `_PARENT_INTENT_KINDS` to `intent_shape.OUTCOME_CO_OWNER_KINDS` in both directions. Nothing else pins that list today. The derivation reads it through `_get_resolver()`, so a kind added upstream and missing there would turn a child into an `unparseable` refused edge that names no ancestor. The tool keeps `_walk_is_not_vacuous`, which now exercises the derivation-backed `children` arm over the real corpus.

Traces to AC-0001, AC-0002, AC-0003, AC-0016.

Owned by: T1, T4

### Quality attributes (NFRs)

- **Cost.** Two measurements exist. FEAT-0002's de-risk timed the delivery resolver run as a subprocess: 1.55 s median, 1.14–4.34 s. The 2026-10-10 spike timed `derive()` in process, warm: 0.09–0.19 s. One closeout runs the derivation once per `resolve_intent_ancestors` call and once per `children` decision. No bar is set. T5 records the time of a whole closeout over the real corpus.

Owned by: T5

## Tasks

### T1: Copy in place, bound to its own helpers, and pinned

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, `packs/core/tests/pack/test_intent_delivery_relations_copies.py`, `packs/core/tests/skills/close-work/test_closure_graph_copy.py`

**Tests:**
- AC-0001: extend the byte-identity loop in `test_vi1904_only_canonical_delivery_inverter_exists` with a pair assertion: `close-work/scripts/intent_graph.py` against `navigate-intents/scripts/intent_graph.py`.
- AC-0002: `test_closure_graph_copy.py::test_each_copy_binds_its_own_helpers` loads both copies under unique names, in both orders, each order inside a fresh `sys.modules` snapshot. It asserts each copy's `_get_file_safety().__file__` and `_get_resolver().__file__` sit in that copy's folder. Stub (red today: the close-work copy binds `navigate-intents/scripts/_file_safety.py`, observed in the spike):

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

### T2: Descendant closure takes children from the derivation and keys by kind

**Depends on:** T1
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_*.py`, `packs/core/tests/skills/close-work/test_closure_parent_edges.py`

**Tests:**
- AC-0004: `test_closure_parent_edges.py` runs one fixture per prefix (`intent:`, `capability:`, `outcome:`, `opportunity:`) plus a path-form parent. A temporary corpus goes through `check_ancestor_closure` with the default provider, and the test asserts the live-descendant names in a `ClosureNotEligible`.
- AC-0005: a tombstone whose `Parent intent:` names the ancestor sits beside one live child, and the closure holds only the live child.
- AC-0018: ancestor `P` (`children`) has child intent `X` (`Decomposed: … brief`, terminal), and the resolver snapshot names a live brief `X` for it. The verdict is `ClosureNotEligible` naming brief `X`'s status. The same fixture with a spec `X` under a `spec` terminus does the same.
- AC-0009 (decision part): one case uses a real corpus fault (a live intent missing `Slug:`) through the default provider and gives `intent-graph-unavailable: malformed_record`. Another uses a missing copy, through `_graph_module_path`, and gives `intent-graph-unavailable: copy-unavailable`.
- AC-0010: run one fixture per state that can name a live intent: `kind_mismatch` (`intent:a` where `a` is a capability), `multiple_values` with one value naming the intent, and a `cycle` through it. Each is placed once against the evaluated ancestor and once against a nested `children` descendant two levels down, and each gives `parent-edge-refused`. A negative fixture, `out_of_type` `brief:a` beside intent `a`, is not refused on that ground.
- AC-0012: a counting provider shows one call for a `children` decision and for two nested `children` levels. It shows zero calls for `brief`, `spec`, `closed-empty`, and `direct-light` decisions.
- AC-0013: a counting `_reader` and a counting confined read inside the derivation run over a diamond fixture. They show each real path opened at most once by each. Every path `close-work`'s reader opened is the `path` of an artifact in the returned descendant set.
- Integration: `test_closure_parent_edges_corpus` (see Construction tests).
- Migration: the `children`-arm cases in `test_closure_walk.py`, `test_closure_index_bounds.py`, `test_closure_packet.py`, `test_closure_staleness.py`, `test_closure_verdict_coverage.py`, `test_closure_entry.py`, and `test_closure_delivery_snapshot.py` pass a `_graph_provider` built from their fixture text. Each keeps its asserted verdict. A bound test that counted intent-collection candidate opens now asserts the AC-0013 bound.

**Approach:**
- Migrate the existing tests in the same commit as the seam. A suite left on `_dir_lister` alone would pass by never reaching the new arm.

**Done when:** every listed test is green, and `python3 -m pytest packs/core/tests/skills/close-work -q` is green.

### T3: Upward walk takes parent edges from the derivation

**Depends on:** T2
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_parent_edges.py`, `packs/core/tests/skills/close-work/test_closure_entry.py`, `packs/core/tests/skills/close-work/test_closure_t11_vi.py`, `packs/core/tests/skills/close-work/test_closure_broken_spec_refusal.py`

**Tests:**
- AC-0006: a four-level chain uses a different prefix at each hop. `resolve_intent_ancestors` runs from the bottom intent, and from a brief at the bottom, and the test asserts the full `(slug, status, terminus)` tuples nearest first. Each ancestor's status carries trailing text, such as `Accepted (2026-10-01)`, to show it is echoed as recorded.
- AC-0017: an intent slug and a brief slug present in `fields` but absent from the corpus each raise `artifact-not-in-graph`. A walked intent whose on-disk `Parent intent:` differs from the caller's `fields` follows the on-disk edge.
- AC-0007: a spec has two delivery relations and one non-feature `Discovery:` provenance record, through an injected snapshot. The returned tuples follow the depth-first order the spec states, with a shared grandparent returned once.
- AC-0007 (absent first hop): an injected snapshot naming an intent with no file raises `artifact-not-in-graph`.
- AC-0008: brief `x` with `Parent intent: intent:x` returns intent `x` first. Spec `y` whose snapshot names intent `y` returns intent `y` first.
- AC-0009 (walk part): a real corpus fault through the default provider raises `_ClosureDeliveryRefusal` with `intent-graph-unavailable: malformed_record`.
- AC-0011: an intent fixture runs each state an intent's `Parent intent:` can take: `dangling`, `retired_target`, `kind_mismatch`, `out_of_type`, `multiple_values`, `cycle`, and `unparseable`. A brief fixture runs each state a brief's can take: `dangling`, `retired_target`, `multiple_values`, and `unparseable`. Each is placed on the walked artifact and again on a reached ancestor, and each raises `parent-edge-refused`.
- Migration: existing `resolve_intent_ancestors` cases that passed `fields` for unwritten artifacts write those artifacts as fixture files and keep their expected chains.

**Done when:** the listed tests and the full `close-work` suite are green.

### T4: The old parent parser is gone and the kind pin moves

**Depends on:** T3
**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `tools/check_closure_terminality_parity.py`, `tools/test_check_closure_terminality_parity.py`, `packs/core/tests/skills/close-work/test_closure_graph_copy.py`

**Tests:**
- AC-0003: `test_closure_graph_copy.py::test_no_preamble_parent_read` parses `closure_index.py` with `ast`. It fails on any subscript, `.get`, or `in` test whose key is the literal `"Parent intent"` applied to a value returned by `_preamble`. It also fails if `_is_parent_edge`, `REFERENCE_KIND_VOCABULARY`, or `reference_kind_parity_disagreements` is defined.
- AC-0016: `tools/test_check_closure_terminality_parity.py` gains two cases, one per direction. A temporary copy of the resolver with a kind added, and one with a kind removed, each make the tool exit 1 and name the kind. `python3 tools/check_closure_terminality_parity.py` exits 0 on the real repository.

**Done when:** both checks are green.

### T5: Real-corpus verdict comparison recorded

**Depends on:** T4
**Touches:** `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md`

**Tests:**
- AC-0015: a throwaway script outside the repository, its source pasted into the ledger, runs against a detached worktree of the base commit as the one corpus root.
  - It loads the base commit's `close-work/scripts/` and the head commit's `close-work/scripts/` into two temporary folders, each module under its own name, and points both at that root.
  - It records chains, descendant sets, and verdicts as the criterion states, with `_freshness_checker=lambda: True`.
  - It attributes a chain difference by the first hop where the chains diverge. That hop's value prefix is cause 1. A tombstone file at the old match is cause 2. A matching slug of another kind is cause 3. It attributes a descendant-set difference by the differing member: a tombstone member is cause 2, and a member sharing a slug with another member of another kind is cause 3. Cause 1 never explains a descendant-set difference, because the old `children` arm already read all four prefixes. It attributes a verdict difference to the difference beneath it.
  - It exits 1 on any unattributed difference.

**Done when:** the ledger records both commits, exit code 0, the per-cause counts, and the wall time of one full closeout over the real corpus.

### T6: Docs, frozen pointer, and release

**Depends on:** T5
**Touches:** `guides/core/how-to/close-and-disposition-work.md`, `packs/core/DESIGN.md`, `docs/specs/closure-eligibility-check/spec.md`, `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/.apm/skills/close-work/evals/evals.json`, `tests/roster/test_close_work_graph_convergence_supersession.py`, adapter projections

**Tests:**
- AC-0014: `tests/roster/test_close_work_graph_convergence_supersession.py` reads the `Status:` line for the prefix, this spec's path, and the three criterion ids. It hashes the file with its `Status:` line removed and compares the result to a SHA-256 literal in the test, computed at the base commit, so the check survives the integration branch's deletion and covers criterion continuation lines.
- The guide lints named in the spec's Durable Outputs are green.
- An eval case is added to `close-work/evals/evals.json` for a closure whose child records a refused parent pointer, expecting `parent-edge-refused` to be named.
- `agentbundle catalogue self-host --root . --write` leaves no diff on a re-run. `make lint-ruff lint-mypy` is green.

**Approach:**
- The `Status:` pointer is spec-to-spec, not spec-to-ADR. No ADR governs this change; the decision lives in FEAT-0002's 2026-10-10 Amendment and this spec. `catalogue-sync-dry-run`'s `Status:` line is the precedent.

**Done when:** the listed checks are green, the versions read `3.1.1`, and the changelog entry carries a `### Highlights` bullet.

## Rollout

- **Delivery:** one pull request into `feature/intent-navigation`, carrying this slice's `core` bump to 3.1.1 on that branch. The published release version is set when slice 4 merges the branch to the default branch. Reversible by revert. Nothing is persisted.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** slice 4's rebase refreshes resolver copies. That refresh now also covers `close-work/scripts/intent_graph.py`, which AC-0001's pin keeps in step.

## Risks

- About 70 artifacts gain ancestors they never had: capability, outcome, and opportunity parents. Closers will see verdicts for those ancestors for the first time, often `not-accepted` refusals on Draft capabilities. This is the intended correction. The changelog highlight says so.
- A child recorded with a mismatched kind, such as `intent:a` for a capability `a`, was a child before and is now a refused edge that refuses its ancestor's closure. None exists on 2026-10-10.
- Keying descendants by kind changes descendant sets wherever a closure holds a same-slug intent and brief or spec. These are cause-3 differences, and T5 expects them.
- Test migration in T2 and T3 is wide. A test moved onto `_graph_provider` with a graph that disagrees with its fixture text would pass while testing nothing. The integration test runs with no seams to catch that.

## Changelog

- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
