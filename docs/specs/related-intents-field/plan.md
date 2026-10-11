# Plan: Related intents field

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/DESIGN.md` § Intent-edge derivation: source, copies, pins, and consumers; analogous implementations: `intent_shape.validate_supersession` (a corpus-scoped pointer rule run by `intent_corpus_lint.py`) and `lint-traceability.py`'s `outcome_co_owner_findings` (a typed peer pointer that adds no graph edge); their tests: `packs/core/tests/skills/work-intake/test_intent_corpus_lint.py` and `packs/core/tests/skills/work-loop/test_lint_traceability.py::test_ac0004_outcome_co_owner_does_not_add_graph_edges`; deviation: `Superseded by:` is a bare slug, so the related rule needs typed parsing and a slug-to-kind map the lint does not build today.

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

The lint rule lands first (T1), because it is the writer-side guarantee and has no dependency on the navigator. The derivation then reads the field into edges in both copies at once (T2), and the query surface shows them (T3). T4 proves the two sides agree and that nothing else reads the field. Docs, the template, the contract pointer, and the release come last (T5).

The riskiest part is the agreement in AC-0006. The lint decides a target's kind and file admission in `intent_shape.py` and `intent_corpus_lint.py`, and the navigator in `intent_graph.py`, under the ban on cross-skill imports, so both rules exist twice. T4's shared fixture set, with the `Level:` spellings a lint-clean corpus can carry, is what keeps the two in step.

## Constraints

- RFC-0105 D1: one derivation feeds every intent-graph reader; each relationship keeps its basis and trust class.
- RFC-0103: the typed reference grammar, whose intent kinds are `intent`, `capability`, `outcome`, and `opportunity`.
- FEAT-0002 constraint C3 and delivery decision 4: the field's name, shape, one-sided writing, lint check, template line, and the no-reconciler pin.
- ADR-0007 and ADR-0074: agent-invoked skill scripts, standard library only.
- The catalogue authoring standards ban cross-skill imports; tests load modules under unique pack-and-skill names.
- `packs/AGENTS.md`: a non-cosmetic pack change bumps `pack.toml` and `plugin.json` together, updates the pack's eval harness, and is projected with `agentbundle catalogue self-host --root . --write`, run twice with no diff on the second run.
- Versions follow owner decision 7 in [`notes/verification-ledger.md`](notes/verification-ledger.md), which extends the integration-branch decision recorded in `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md`. `tests/roster/test_two_sided_prune_closure_invariant.py` admits one `core` bump per release.
- The owner's 2026-10-10 checkpoint decisions in the same ledger settle target liveness, the kind-match rule, `self_reference`, the trust class, the display surfaces, the contract pointer, and the no-reconciler pin.
- The brief's publication constraint: this slice merges into `feature/intent-navigation`.

## Construction tests

**Integration tests:** T4's `test_related_intents_lint_parity.py` runs one fixture set through `intent_corpus_lint.lint_corpus` and `navigate_intents.run_query`.

**Manual verification:** `intent_corpus_lint.py --dir docs/product/intents --root .` over the real corpus exits with the same code and violation set as before the change (no intent carries the field), recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Authoring template and its two guide mirrors (`frame-the-intent.md`, `hand-it-to-build.md`) | T5 | AC-0018's test | Test green |
| User reference row | T5 | AC-0019's test | Test green |
| Lint-refusal how-to section | T5 | Guide lints | Section present |
| Navigation how-to | T5 | Guide lints | Lists, lines, and `self_reference` present |
| Skill instructions | T5 | Self-host re-run with no diff | Descriptions present |
| Architecture — `packs/core/DESIGN.md` | T5 | Section diff | Field and no-reconciler rule named |
| Historical contract pointer — `intent-navigation/spec.md` header | T5 | Header diff | Line names this spec and the seven criteria |
| Release history and versions | T5 | Changelog and version diff | Version and `/now/` tests green |
| Evaluation harness — `navigate-intents/evals/eval_queries.json` prompt and `frame-intent/evals/evals.json` case | T5 | File diffs | Prompt and case present |
| Executable proof | T1–T5 | Suites green | Run ids in the ledger |
| Verification record | T5 | Ledger entry | Cited by the closing PR |
| Design facts below | T1–T4 | Code, docstrings, tests | Mechanically inferable once merged; no further owner |

## Design (LLD)

### Data & schema

A related edge is a dict in the derivation's existing edge shape: `from`, `field` (`Related intents`), `form`, `trust_class` (`pointer_checked`), `basis` (`{field, form}`), and either `to` and `value` (resolved) or `state` and `value` (refused). `retired_target` adds `reissued_as`. `multiple_values` carries `basis.values` and no `value`, as for the other fields.

Traces to AC-0007, AC-0008, AC-0009.

Owned by: T2

### Interfaces & contracts

- `intent_shape.py` gains `intent_node_ids(named_texts: Mapping[str, str]) -> dict[str, str]`, keyed by each file's path relative to the linted directory. It admits only names with no `/` that match the delivery resolver's artifact-file pattern, maps each admitted live intent's slug to its node id by the navigator's rule, and omits a slug two admitted intents share, so an item naming it is refused. `validate_corpus_scoped(text, live, *, intent_ids: Mapping[str, str] | None = None)` keeps its positional signature; `None` reads as an empty map, so a present field with no map fails closed. `intent_corpus_lint.lint_corpus` passes the map built from its live partition, Superseded intents included.
- `VALUE_RULES["Related intents"]` is the one-file shape rule (AC-0001), so the guide parity test classes the row `constrained when present`.
- `navigate_intents.py` adds `related_written_here` and `related_written_elsewhere` to `_build_intent_record` and to each `tree` entry, extends `_count_result_elements` with both lists, and adds the two text lines in `_build_text_tree`.

Traces to AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0011, AC-0012, AC-0013, AC-0014.

Owned by: T1, T3

### Behavior & rules

- **Derivation order.** In `derive()`'s intent loop, after parent edges, take the preamble's `Related intents` values, drop empty and leading-`none` ones, and refuse more than one distinct remaining value as `multiple_values`. Otherwise split the one value on `,`, trim, drop empties, and de-duplicate in first-seen order. Classify each item with `_value_form_intent_parent`, whose `typed` form already requires a well-formed remainder. A `typed` item with an intent kind checks self first, then goes through `_resolve_intent_typed`, which yields `kind_mismatch`, `retired_target`, or `dangling`. A `typed` `brief:` or `spec:` item is `out_of_type`; every other form is `unparseable`.
- **Isolation from parents.** Related edges never get `_is_cycle_candidate`, and every existing consumer filters edges by `field`, so cycles, children, ancestors, and placement are untouched. `summary` iterates every refused edge, so it counts related refusals without a change of its own.
- **Trust class.** `_multiple_values_edge` takes the trust class as a parameter, so related `multiple_values` edges carry `pointer_checked` while the other fields keep `pointer_unchecked`.
- **Lint rule order.** Shape (AC-0001) runs in `validate_live_intent`, through `VALUE_RULES`, which never sees a value emptied by normalization. Resolution (AC-0002 to AC-0004) runs in `validate_corpus_scoped` only on items that passed shape: self, then unknown slug, then kind mismatch, one violation per offending item. The kind is read by a port of `intent_graph._normalize_kind_level` and `_compute_node_id`: the first preamble `Kind:` and `Level:` values, comment-stripped, cut at ` (`, ` →`, `<!--`, backticks stripped, first word lower-cased. The leading-`none` test is the derivation's own: the first token of `value.split()`, lower-cased, equals `none`, so `none, intent:a` is a list in both readers. In a lint-clean corpus `Kind:` is already exactly `outcome` or `opportunity` once normalized, so only `Level:` exercises the cutting and case-folding.

Traces to AC-0001 to AC-0010, AC-0015, AC-0021, AC-0022.

Owned by: T1, T2

### Failure, edge cases & resilience

- A tombstone may share a live intent's slug; the real corpus has such pairs. `_resolve_intent_typed` looks up live intents before tombstones, so the live intent wins, and the lint's map, built from live intents only, agrees.
- `intent_shape.present_fields` keeps the first non-empty value, while the derivation keeps the first value. They differ only when a field repeats, which the lint already refuses, so the port may use either.
- Two admitted live intents sharing a slug make the derivation fail whole as `duplicate_identity`; the lint refuses any related item naming that slug, so it never reads as resolved.

Owned by: T1, T4

## Tasks

### T1: Lint rule for the field

**Depends on:** none
**Touches:** `packs/core/.apm/skills/work-intake/scripts/intent_shape.py`, `packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py`, `packs/core/tests/skills/work-intake/test_intent_corpus_lint.py`, `packs/core/tests/skills/work-intake/test_intent_shape.py`

**Tests:**
- AC-0001: in `test_intent_corpus_lint.py`, a parametrized case writes one target corpus plus one intent per bad value through `_run`, and asserts exit 1 with a `Related intents` violation for that file. A second case accepts `intent:a, capability:b, outcome:c, opportunity:d` with matching targets, `none — not yet` with no targets, and a comment-only value.
- AC-0002: four cases, one per fixture the criterion names, each asserting a violation whose field is `Related intents` and whose reason contains the item; the subdirectory case writes the target under `<dir>/sub/`, and the shared-slug case writes two admitted live intents with one slug.
- AC-0003, AC-0004: one case each, asserting exit 1 and the item in the violation reason.
- AC-0005: a parametrized case over the four statuses. Each target carries the records the state-coherence rules require: `Superseded by:` naming a live intent for `Superseded`, `Accepted:` for `Cancelled`, and `Accepted:` and `Fulfilled:` for `Fulfilled`.
- Unit: `test_intent_shape.py` asserts `intent_node_ids` over the AC-0006 spelling variants equals the expected ids, and that `validate_corpus_scoped(text, live)` with the field present and no map refuses.

Stub (red today: the lint has no rule for the field):

```python
def test_related_intents_self_reference_is_refused(tmp_path):
    text = _live("me").replace("## Outcome", "- **Related intents:** intent:me\n\n## Outcome")
    result = _run(tmp_path, {"FEAT-0001-me.md": text})
    assert result.exit_code == 1
    assert any(v.field == "Related intents" and "intent:me" in v.reason for v in result.violations)
```

**Done when:** `python3 -m pytest packs/core/tests/skills/work-intake -q` is green.

### T2: Derivation reads related edges, in both copies

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, `packs/core/tests/skills/navigate-intents/test_related_intents.py` (new), `packs/core/tests/skills/navigate-intents/test_derivation_contract.py`, `packs/core/tests/skills/navigate-intents/fixtures/negative/self_reference/` (new), `packs/core/tests/skills/navigate-intents/fixtures/README.md`

**Tests:**
- AC-0007: `test_related_intents.py` copies `fixtures/mixed/` and adds the field through `_intent`-style edits: the value `intent:a, intent:b, intent:a,` (three items, one a repeat, then a trailing comma) gives exactly two edges; `none`, and an empty value, give none.
- AC-0021: two differing lines give one `multiple_values` edge listing both values; a `none` line beside one `intent:a` line gives the single `intent:a` edge.
- AC-0022: a brief, a spec, and a tombstone each carrying the field give no related edge.
- AC-0008: one fixture per state, asserting `state`, `basis.form`, and for `retired_target` `reissued_as`, plus one resolved edge per intent kind, an `intent:Foo` item and a `brief:Bad_Slug` item that are both `unparseable`, and a `brief:x` item that is `out_of_type`. The committed `fixtures/negative/self_reference/` corpus ships an `expected-outstanding.json` that the manifest-driven suites accept, and `self_reference` joins the list `test_negative_fixture_dirs_exist` requires.
- AC-0009: every related edge in the AC-0007 and AC-0008 fixtures carries `pointer_checked`, and every `Parent intent:` edge in the same graph still carries `pointer_unchecked`.
- AC-0010: the mutual-pair and three-loop corpus, with and without the field, compared on every operation and identity the criterion names, with `generated_at` and the two related lists removed, and no related edge in `cycle`.
- AC-0020: the existing byte-identity assertion in `test_intent_delivery_relations_copies.py` stays green after the edit.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents -q` and `python3 -m pytest packs/core/tests/pack -q` are green.

### T3: Query surface shows related edges

**Depends on:** T2
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/tests/skills/navigate-intents/test_related_intents.py`, `packs/core/tests/skills/navigate-intents/test_text_tree.py`

**Tests:**
- AC-0011: `record` on each end of a one-sided relation, asserting both lists' contents and order, with a refused edge from a third intent naming the subject absent from both lists.
- AC-0012: `tree` entries carry both lists; `search` and `ancestors` entries have neither key.
- AC-0013: a generated corpus of 150 intents in one flat forest, each relating to two others, so parent and delivery edges stay under 400 and related entries take the total over it. Assert `result_too_large`, `error.observed.edges` equal to the related-entry count plus the other edges, and that the same corpus without the field returns `ok`.
- AC-0014: `test_text_tree.py` asserts the exact lines for a resolved edge, a refused edge, and an incoming edge, on an intent that also has a child, so the related lines' place before the child line is observed.
- AC-0015: `summary` over the AC-0008 fixtures counts each state, `self_reference` included.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents -q` is green.

### T4: Agreement, and no reconciler reads the field

**Depends on:** T1, T3
**Touches:** `packs/core/tests/skills/navigate-intents/test_related_intents_lint_parity.py` (new), `packs/core/tests/skills/close-work/test_closure_related_intents.py` (new)

**Tests:**
- AC-0006: `test_related_intents_lint_parity.py` loads the lint and the navigator under unique names. One lint-clean corpus holds targets with `Level: Capability`, `Level: capability (legacy)`, `Level: capability → retired name`, ``Kind: `outcome` ``, and `Kind: <!-- c --> opportunity`, related by all four prefixes, with one source value ``` `intent:a, capability:b` <!-- note --> ``` and one `None — later`. The lint exits 0, every related edge resolves, and the second source has none. A further case writes `none, intent:a` and asserts the lint exits 1 and the navigator returns an `unparseable` edge for `none` beside the `intent:a` edge. A parametrized case per AC-0008 and AC-0021 state builds the fixture, asserts the navigator state, and asserts the lint exits 1.
- AC-0016: in the same file, a scan over `packs/core/.apm/**/*.py` for the literal `Related intents` asserts the hit set equals the four allowed files. A positive control copies the tree to `tmp_path`, plants the literal in `close-work/scripts/closure_index.py`, and asserts the scan reports it.
- AC-0017: `test_closure_related_intents.py` writes a `children` closure corpus to disk whose descendants are all terminal and runs `check_ancestor_closure` with no `_graph_provider`, so the bundled derivation reads it, and with `_freshness_checker=lambda: True` and the corpus's accepted ancestor, so the preconditions pass. It first asserts the derived graph holds the resolved, `self_reference`, and `dangling` related edges, then asserts `ClosureEligible` with and without the field.

**Done when:** both new files and `python3 -m pytest packs/core/tests/skills/close-work -q` are green.

### T5: Template, docs, contract pointer, and release

**Depends on:** T4
**Touches:** `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`, `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json`, `guides/product-engineering/how-to/frame-the-intent.md`, `guides/product-engineering/how-to/hand-it-to-build.md`, `guides/product-engineering/reference/intent-fields-and-modes.md`, `guides/product-engineering/how-to/fix-a-refused-intent.md`, `guides/core/how-to/navigate-intents.md`, `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `packs/core/DESIGN.md`, `docs/specs/intent-navigation/spec.md`, `docs/product/changelog.md`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `tests/roster/test_intent_template_shape_conformance.py`, `docs/specs/related-intents-field/notes/verification-ledger.md`, adapter projections

**Tests:**
- AC-0018: `test_intent_template_shape_conformance.py` gains `test_the_template_and_its_mirrors_list_related_intents_after_outcome_co_owner`. It reads the template and every fenced block under a `<!-- rung: …/intent-template.md -->` marker in `guides/product-engineering/how-to/`, and asserts in each that the field line follows the `Outcome co-owner` line with a value that is one HTML comment, and that at least two mirror blocks were found. The existing resolved-template tests cover the rest.
- AC-0019: `tests/roster/test_intent_field_reference_parity.py`, unchanged, goes green only once the row reads `constrained when present`.
- The guide lints named in the spec's Durable Outputs are green.

**Done when:** the listed tests are green; `agentbundle catalogue self-host --root . --write` leaves no diff on its second run; `make lint-ruff lint-mypy` is green; `tests/roster/test_two_sided_prune_closure_invariant.py::test_pack_delivery_contract_is_complete_and_version_increased` passes with `core` at `3.1.0`; `product-engineering` reads `0.13.25` in both version files with a `[product-engineering][0.13.25]` changelog entry; `navigate-intents/evals/eval_queries.json` and `frame-intent/evals/evals.json` carry their new entries; and the ledger records the real-corpus lint run and the dispatched CI run ids.

## Rollout

- **Delivery:** one pull request into `feature/intent-navigation`. Slice 4 publishes `core` when it merges the branch to the default branch. Reversible by revert. Nothing is persisted.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none beyond the branch's own rebase before slice 4 merges it.

## Risks

- `product-engineering` 0.13.25 waits on the integration branch. If the default branch releases its own 0.13.25 first, the rebase before slice 4's merge renumbers this entry.
- The kind and file-admission rules exist in two scripts. T4's fixtures cover the spellings and file names a lint-clean corpus can carry; a change to either side's rule that the other does not follow would show as a lint-clean corpus with a refused related edge.
- A tree over the whole corpus counts each related edge twice, so heavy use of the field brings `result_too_large` sooner. `--depth` remains the bounded route.

## Changelog

none
