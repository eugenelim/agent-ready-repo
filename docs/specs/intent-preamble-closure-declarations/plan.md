# Plan: Intent preamble closure declarations

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/architecture/reference.md` (pack source and projection ownership); `packs/AGENTS.md` and `packs/core/AGENTS.md` (runtime export, test, eval, and version rules); `intent_shape.py` with `test_intent_shape.py`; `lint-traceability.py` with `test_lint_traceability.py`; `intent-preamble-lifecycle-records` as the prior field-contract slice

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted.

## Approach

Extend the existing intent-shape table and bounded preamble reader first, then validate the peer pointer against the traceability linter's already-derived intent node ids without wiring a new edge. Migrate the two live intents only after both validation surfaces exist, then update the authoring surfaces, pack evals, versions, projections, and changelog.

The cheapest disconfirming probe ran against the current module on 2026-09-25. It returned `commented_field_visible=True`, `closed_empty_refused=True`, and `malformed_co_owner_accepted=True`, so each load-bearing change begins from an observable red state.

## Constraints

- RFC-0103 owns the canonical `<kind>:<slug>` pointer form and the intent node identities this slice reuses.
- `.apm/` is authoring source. Generated `.agents/` and `.claude/` projections are never edited directly.
- Core and Product Engineering pack changes each update that pack's eval harness and bump matching `pack.toml` and `.claude-plugin/plugin.json` versions.
- Shipped pack content carries no repository ADR, RFC, spec, task, or acceptance-criterion citation.
- `docs/specs/intent-metadata-shape-contract/` stays frozen. This spec records the new contract instead of rewriting historical criteria.
- FEAT-0005 owns every closure refusal and transition decision. No task here edits `close-work`.
- The local profile can run assertions but Python temporary-directory cleanup can fail with `PermissionError: [Errno 1] Operation not permitted` after them. Do not weaken tests or retry that environment failure; use the supported exact deselections for local evidence and leave cleanup-sensitive coverage to CI.

## Construction tests

T1 through T3 are TDD tasks. Each stores a compilable red contract-surface assertion below; EXECUTE copies the approved block into the named existing suite before production edits. T4 and T5 are goal-based and therefore record `no stub (mode)`.

The current red states are independent: the parser returns a field inside a multiline comment, the value table accepts a malformed co-owner because the name is organic, the decomposition rule rejects `closed-empty`, and the traceability lint ignores an unresolved co-owner and exits zero. The stored T1 and T2 stubs were compiled and observed red on 2026-09-25. A direct unresolved-pointer fixture observed T3's intended zero exit before the managed profile denied Python cleanup; that cleanup path will not be retried locally. The positive controls keep a repair from satisfying the contract by rejecting every input.

**Integration tests:** the real intent corpus and traceability commands run after the two migrations and after projection.

**Manual verification:** read the completed field-reference row and each refusal remedy against the runtime rule. This closeout read is not an acceptance criterion because prose cannot mechanically prove its own truth.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — intent field reference | T2 | roster parity and runtime-table tests | row tier and terminus set agree with `intent_shape.py`; prose read against the rule |
| Current product truth — intent template, how-tos, and live intents | T4 | template conformance plus parser assertions over both live files | no named surface offers the old terminus set or omits the optional field |
| Maintainer procedure — refusal guide | T4 | worked examples driven by the real message classes | each refusal is repairable without this spec |
| Current architecture — validator docstrings | T1, T3 | module-level tests and diff review | ownership and non-edge rule remain stated beside their implementation |
| Release history — Core and Product Engineering entries | T5 | changelog lint/build | entries name the adopter-visible field and terminus changes |

## Design (LLD)

### Design decisions

**Owned by:** T1, T2, T3

- **Closed-empty is a decomposition terminus, not a field.** AC-0005 owns the value contract. Extending the existing terminus set records this completed decision without adding a second field that would need a coherence rule against `Decomposed:`.
- **The co-owner uses the target's canonical node id.** AC-0001 owns the packet-decidable value contract. Corpus validation compares that accepted value with the intent ids traceability already derives instead of duplicating slug syntax that `Slug:` itself does not enforce.
- **A peer declaration is not a graph edge.** Resolution reuses the graph's node registry only as an identity index. It adds no edge to `Graph.edges`, so dangling-target, reachability, cycle, and structural-orphan checks do not reinterpret co-ownership as decomposition.
- **HTML-comment visibility is decided before field and heading recognition.** A small stateful scan yields only visible text to the existing line matcher. The value normalizer continues to own trailing visible comments and backticks, which keeps the existing order-sensitive contract in one place.
- **An unclosed comment hides the remainder.** Markdown renders the remainder hidden, so the preamble reader treats it the same way and neither credits nor judges field-shaped text after the opener.

### Data & schema

**Owned by:** T1, T2, T3

| Declaration | Tier | Value |
| --- | --- | --- |
| `Outcome co-owner` | constrained when present | AC-0001 owns the value vocabulary; a `VALUE_RULES` predicate owns its per-artifact shape and the peer-reference helper owns AC-0002 and AC-0003 corpus validation |
| `Decomposed` | constrained when present | AC-0005 owns the value vocabulary; the existing `_check_decomposed()` path consumes the extended `DECOMPOSITION_TERMINI` set |
| HTML comments | parser visibility | text from `<!--` through `-->`, including lines and headings, is not preamble content |

### Interfaces & contracts

**Owned by:** T2, T3

`validate_live_intent()` remains the one-artifact surface and gains only packet-decidable shape. The traceability command owns target resolution because it already derives every canonical intent id; it obtains `Outcome co-owner:` through `intent_shape.read_preamble()` or an equivalent shared comment-aware reader rather than its raw field regex. A pure peer-reference helper reports faults before structural classification and never calls `Graph.add_edge()`. The command supplies that helper with the visible declarations and intent ids it discovered.

No repository `contracts/` artifact is added. The public interface is the Markdown preamble contract documented in the adopter field reference.

## Tasks

### T1: HTML-comment regions cannot declare preamble data

**Depends on:** none

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/work-intake/scripts/intent_shape.py`, `packs/core/tests/skills/work-intake/test_intent_shape.py`

**Tests:**

- `test_ac0007_html_comment_regions_are_not_preamble` (AC-0007), `stub: true`
- `test_ac0008_visible_trailing_comments_keep_normalizing` (AC-0008), completed during green

```python
# STUB: AC-0007
def test_ac0007_html_comment_regions_are_not_preamble() -> None:
    text = "\n".join(
        [
            "# Intent",
            "",
            "- **Owner:** maintainer",
            "- **Slug:** source",
            "- **Level:** feature",
            "<!--",
            "- **Status:** Draft",
            "- **Outcome co-owner:** intent:hidden",
            "## Hidden heading",
            "-->",
            "- **Status:** Accepted",
            "- **Outcome co-owner:** intent:visible",
            "",
            "## Outcome",
        ]
    )

    pairs = intent_shape.read_preamble(text)

    assert pairs.count(("Status", "Accepted")) == 1
    assert ("Status", "Draft") not in pairs
    assert ("Outcome co-owner", "intent:hidden") not in pairs
    assert ("Outcome co-owner", "intent:visible") in pairs
```

**Approach:** Add comment-region state ahead of the existing heading and field matchers. Leave `normalize_value()` as the owner of visible trailing-comment and backtick normalization.

**Done when:** the stored stub is green and the existing normalization and body-boundary cases pass unchanged.

### T2: Co-owner shape and closed-empty values are decided on the shared surface

**Depends on:** T1

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/work-intake/scripts/intent_shape.py`, `packs/core/tests/skills/work-intake/test_intent_shape.py`, `tests/roster/test_intent_field_reference_parity.py`, `guides/product-engineering/reference/intent-fields-and-modes.md`

**Tests:**

- `test_ac0001_outcome_co_owner_requires_an_intent_kind_and_target` (AC-0001), `stub: true`
- `test_ac0005_closed_empty_is_a_decomposition_terminus` (AC-0005), `stub: true`
- AC-0006 and AC-0011 extend the same fixture families during green

```python
# STUB: AC-0001
def test_ac0001_outcome_co_owner_requires_an_intent_kind_and_target() -> None:
    valid = _preamble(_with(**{"Outcome co-owner": "intent:peer"}))
    invalid = _preamble(_with(**{"Outcome co-owner": "peer"}))

    assert "Outcome co-owner" not in _fields_at_fault(valid)
    assert "Outcome co-owner" in _fields_at_fault(invalid)


# STUB: AC-0005
def test_ac0005_closed_empty_is_a_decomposition_terminus() -> None:
    text = _with_decomposition(
        "2026-09-24 closed-empty",
        [],
        section=False,
    )

    assert _accepted(text)
    assert "closed-empty" in intent_shape.DECOMPOSITION_TERMINI
```

**Approach:** Add one field predicate to `VALUE_RULES` and one member to `DECOMPOSITION_TERMINI`. Reuse `_check_decomposed()` and `progress_state()` without a second closed-empty path. Update the field reference's `Outcome co-owner` and `Decomposed` rows in the same task so the parity suite can prove the public field table matches the runtime contract.

**Done when:** both stored stubs and the expanded field-reference parity suite, including the two changed field-reference rows, are green.

### T3: Co-owner targets resolve without becoming graph edges

**Depends on:** T2

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/work-loop/test_lint_traceability.py`

**Tests:**

- `test_ac0002_outcome_co_owner_helper_reports_unresolved_target` (AC-0002), `stub: true`
- `test_ac0002_unresolved_outcome_co_owner_refuses` (AC-0002), command-level case completed during green
- `test_ac0003_self_co_owner_refuses` (AC-0003), completed during green
- `test_ac0004_outcome_co_owner_does_not_add_graph_edges` compares `Graph.edges` and structural findings for the same fixture with and without a valid declaration (AC-0004), completed during green
- `test_ac0019_commented_outcome_co_owner_is_absent` covers both closed and unclosed comment regions at command level (AC-0019), completed during green

```python
# STUB: AC-0002
def test_ac0002_outcome_co_owner_helper_reports_unresolved_target() -> None:
    module_spec = importlib.util.spec_from_file_location("_trace_co_owner", str(LINTER))
    assert module_spec is not None and module_spec.loader is not None
    mod = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(mod)

    findings = mod.outcome_co_owner_findings(
        {"intent:source": "intent:missing"},
        {"intent:source"},
    )

    expect(bool(findings), "an unresolved co-owner must produce a finding")
    report = "\n".join(findings)
    expect("intent:source" in report, report)
    expect("Outcome co-owner" in report, report)
    expect("intent:missing" in report, report)
```

**Approach:** Read the visible field from each recognized intent path through the shared comment-aware preamble reader, compare it against the already-derived intent-id subset through the pure helper, and report peer-reference violations separately from edge classification. The check never calls `add_edge()`. Complete the green path with command-level temporary-corpus cases for AC-0002 through AC-0004 and AC-0019. Those cleanup-sensitive subprocess cases run on CI; the local affected-suite command deselects `test_ac0002_unresolved_outcome_co_owner_refuses`, `test_ac0003_self_co_owner_refuses`, `test_ac0004_outcome_co_owner_does_not_add_graph_edges`, and `test_ac0019_commented_outcome_co_owner_is_absent` by exact node id while the pure helper tests provide local evidence.

**Done when:** the stored stub, self-reference case, valid-target case, edge-set comparison, and command-level CI cases are green. The implementation record names every local deselection rather than treating the cleanup denial as a product failure.

### T4: Live intents and authoring surfaces carry the declarations

**Depends on:** T2, T3

**Mode:** Goal-based check

**Touches:** `docs/product/intents/remote-ci-verification-parity.md`, `docs/product/intents/STRAT-0002-platform-core.md`, `guides/product-engineering/how-to/frame-the-intent.md`, `guides/product-engineering/how-to/hand-it-to-build.md`, `guides/product-engineering/how-to/fix-a-refused-intent.md`, `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`

**Tests:**

- `no stub (mode: goal-based)`
- Load each live file through `read_preamble()` and compare the effective value with AC-0009 and AC-0010.
- Run the rendered-template conformance tests for AC-0012; T2 owns the AC-0011 field-reference parity evidence.
- Read each changed guide as a whole before closeout; mechanical tests own row presence and runtime parity, while the read checks the four worked repairs against AC-0020's runtime classes and absence behavior.

**Done when:** AC-0009, AC-0010, AC-0012, and AC-0020 are green and the changed documentation has passed its closeout read.

### T5: Pack releases and repository gates agree with the new contract

**Depends on:** T1, T2, T3, T4

**Mode:** Goal-based check

**Touches:** Core and Product Engineering eval files, matching `pack.toml` and `.claude-plugin/plugin.json` versions, generated projections, `docs/product/changelog.md`

**Tests:**

- `no stub (mode: goal-based)`
- Add Work Intake eval coverage for hidden comments, malformed co-owner shape, and the `closed-empty` value; add Frame Intent eval coverage for the optional field and terminus (AC-0015).
- Bump each changed pack's matching manifest pair, run `make build-self`, and prove source/projection parity without editing projections directly (AC-0016).
- Add both pack release entries to `docs/product/changelog.md` (AC-0017).
- Run every command in the handoff's Verify list unfiltered, plus the affected pack suites and guide checks (AC-0013, AC-0014).
- Confirm changed shipped pack content contains no internal-governance citation and run the pack-boundary lint (AC-0018).

**Done when:** AC-0013 through AC-0018, the affected suites, and the remaining repository gates all pass.

## Rollout

- **Delivery:** one repository change. The validation rules land with both live migrations, so no intermediate revision makes the real corpus invalid.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** runtime rules, migrations, documentation, evals, versions, projections, and changelog ship together.

## Risks

- Comment-region handling affects every intent field, so an overly broad scanner can hide visible metadata or expose hidden metadata. Existing normalization and body-boundary fixtures remain unchanged controls.
- Reusing the graph builder can accidentally turn the peer pointer into ancestry. AC-0004 compares edge sets to catch that specific coupling.
- The co-owner kind set can drift from intent recognition. AC-0011 and the traceability fixtures compare against runtime-derived ids rather than a second slug grammar.
- Two pack updates can leave one eval or version behind. T5 treats each pack as its own release unit.

## Changelog

- 2026-09-25: spec approved by eugenelim
- 2026-09-25: plan approved by eugenelim
- 2026-09-25: controlled amendment authorized by eugenelim; moved the two field-reference row changes from T4 to T2 so T2 can satisfy its approved parity gate without changing behavior, acceptance criteria, or non-goals
- 2026-09-25: unchanged spec scope reapproved by eugenelim after the controlled amendment
- 2026-09-25: corrected plan reapproved by eugenelim after the controlled amendment
