# Plan: Intent delivery traceability

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `docs/architecture/reference.md` and `docs/architecture/pack-layout.md` own pack source and repo-scope primitive projection; `guides/_shared/how-to/author-a-skill.md` owns skill self-containment; `closure_index.py` with `test_closure_walk.py` and `lint-traceability.py` with `test_lint_traceability.py` are the two current implementations and construction paths. Named deviation: their current route handling differs, so this plan moves delivery inversion to one repo-scope primitive instead of preserving either consumer as the owner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted.

## Approach

Add a standard-library Core adapter-root CLI that builds one immutable relation snapshot from confined artifact preambles. Drive it with pure fixture tests, then replace the delivery-specific scans in `close-work` and `lint-traceability.py` with checked subprocess consumption of that snapshot before updating the Core projection, architecture page, eval evidence, versions, and changelog. The riskiest part is removing each private inversion without changing the unrelated closure and product-graph behavior around it.

The cheapest disconfirming probe ran the existing generic adapter-root projection case on 2026-10-04. Its projection assertion completed without a product failure; the test failed afterward in `TemporaryDirectory` cleanup with the sandbox's known `PermissionError`, so final projection proof remains assigned to CI rather than being claimed from this local run.

## Constraints

- ADR-0077 owns feature projection by shippability and coordination need.
- RFC-0103 owns typed cross-artifact reference grammar.
- `.apm/` is authoring source; generated runtime projections are outputs.
- Skills remain self-contained. They do not import sibling-skill files, and `.apm/shared-libs/` is not used for skill code.
- The resolver and consumers use Python 3.11 standard library plus the existing `agentbundle.catalogue_tooling.file_safety` confinement contract; they add no dependency.
- The feature reads preambles, returns an in-memory snapshot, and persists no graph, index, status, or coverage state.
- Core pack content carries no internal ADR, RFC, spec, task, or acceptance-criterion citation.
- Repository-durable retention: `docs/specs/intent-delivery-traceability/spec.md` and `plan.md` are read by the owner, implementer, reviewers, and CI; approval records their fingerprints. Code, tests, architecture guidance, and release history become the post-closeout evidence owners, while the spec directory remains frozen delivery history.

## Construction tests

The resolver is a pure TDD surface. Consumer wiring stays TDD but uses an implementation-discovered seam because the current scripts do not expose a shared dependency boundary; each task records the predicate and proof that close that gap.

**Integration tests:** **VI-1401** is owned by T4 and placed at `packs/core/tests/integration/test_intent_delivery_traceability.py::test_vi1401_resolver_and_consumers_share_delivery_snapshot`. It runs the direct, coordinated, explicit-empty, dual-provenance, missing-direct, missing-brief, direct-projection-mismatch, brief-projection-mismatch, unsafe-corpus, resource-limit, and resolver-unavailable corpus through the resolver and both consumers, then compares accepted delivery subsets and fail-closed diagnostics with the resolver result (AC-0012, AC-0013, AC-0014, AC-0016, AC-0017, AC-0018, AC-0019).

**Caller inventory:** **VI-1402** is owned by T4 and placed at `packs/core/tests/integration/test_intent_delivery_traceability.py::test_vi1402_only_canonical_delivery_inverter_exists`. It inventories production Python sources under `packs/core/.apm/`, asserts that only `adapter-root-bins/intent_delivery_relations.py` implements feature-delivery parsing and inversion, asserts that both consumers invoke that resolver, and rejects the retired consumer-local parser and inversion entry points. The T2 and T3 forced-fallback tests remain the behavioral proof that those retired paths are unreachable (AC-0014).

**Manual verification:** none; every accepted outcome has a deterministic parser, process, or projection oracle.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — resolver source, help, and tests | T1-T4 | Resolver fixtures, consumer parity, and installed invocation | One active delivery-inversion owner and matching consumer results |
| Current architecture — `docs/architecture/work-intake-and-artifact-routing.md` | T4 | Whole-page diff review against the shipped paths | The page points to the owner and consumers without copying their vocabulary |
| Release history — `docs/product/changelog.md` | T4 | Changelog and pack-version gates | The Core release entry names the adopter-visible change |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3

The canonical owner is `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`. A repo-scope adapter-root primitive survives every Core adapter projection at `<repository>/.agentbundle/bin/`, while a sibling-skill import and the specialised `shared-libs` rail do not satisfy the repository's skill portability rules.

The resolver's in-process `resolve_repository(root)` result and CLI JSON share one dictionary shape: `schema_version`, `complete`, `relations`, `classifications`, `provenance`, and `diagnostics`. Relation records carry canonical endpoint identifiers, relation type, route, and a field-basis map. Lists are sorted before strict serialization so an identical tree yields identical bytes.

### Interfaces & contracts

Owned by: T1, T2, T3

Both consumers invoke the projected resolver with the current Python interpreter, the repository root, JSON output, a bounded timeout, and captured standard streams. They validate the schema version, completeness flag, required keys, and output-size ceiling before use. Absence, an incomplete result, non-zero exit, timeout, invalid UTF-8, malformed JSON, or an unsupported schema version produces the consumer-authored `delivery-resolver-unavailable` code and no consumer-specific fallback; captured stderr is never forwarded.

This is an internal Core runtime seam, not a portable service or API contract, so the spec names `Contract: none`. The source, help output, typed construction fixtures, and architecture page own its compatibility surface.

### Failure, edge cases & resilience

Owned by: T1, T2, T3

The resolver distinguishes absent mappings, direct-route multiplicity, incompatible same-type targets, malformed references, unsafe lexical references, and explicit empty routes according to the spec criteria. `agentbundle.catalogue_tooling.file_safety` validates each artifact root, bounds enumeration, and performs every preamble read before relation validation; therefore an unsafe corpus entry produces only the AC-0016 incomplete result, while AC-0010 handles absolute and parent-traversing reference text that never reaches corpus admission. Every admitted file is opened at most once per snapshot, and body text cannot affect the result. The resolver enforces the six AC-0017 budgets before materializing the next entry, file, byte range, or serialized result. A refused corpus or breached budget returns `complete: false` with no partial delivery data. Diagnostic rendering admits only stable codes, limit names, and bounded repository-relative context. A consumer failure never falls back to its retired scanner because that would restore split answers.

### Dependencies & integration

Owned by: T1, T2, T3, T4

The Core pack already projects adapter-root binaries to `.agentbundle/bin/`; no new dependency or adapter-contract version is introduced. T1 first proves that the source and projected CLI can import the existing `agentbundle.catalogue_tooling.file_safety` contract in supported repo-scope execution. If that import is unavailable, implementation stops and the plan is amended rather than vendoring confinement logic or weakening the boundary. `close-work` retains ownership of status, freshness, and closure verdicts. `lint-traceability.py` retains the general product graph, endpoint, cycle, and orphan checks. The resolver owns only feature-delivery relation parsing, inversion, classification, and strict serialization.

## Tasks

### T1: The canonical resolver returns a deterministic typed snapshot

**Depends on:** none

**Mode:** TDD

**Touches:** `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`, `packs/core/tests/pack/test_intent_delivery_relations.py`

**Tests:**

- **VI-1001.** `test_ac0001_direct_relation_has_canonical_shape` covers both admitted `Discovery` forms—`intent:<slug>` and repository-relative intent path—against the same canonical relation (AC-0001), `stub: true`
- **VI-1002.** Complete the resolver fixture matrix for AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, and AC-0019 during green, including positive controls for every refusal.
- **VI-1003.** Prove source and projected helper availability, then exercise every AC-0016 unsafe corpus type, the AC-0016-over-AC-0010 precedence for a relation naming each refused entry, every first-over-limit boundary in AC-0017, incomplete snapshots without partial data, and strict sanitized resolver JSON for AC-0018. Kill condition: if the supported projected CLI cannot import the blessed confinement helper, stop and amend the plan rather than copying or weakening it.
- Stub validation: syntax and intended red passed on 2026-10-04 in disposable scratch; the sandbox reported its known temporary-directory cleanup denial after the result, and no repository test file was created.

```python
# STUB: AC-0001
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = (
    Path(__file__).resolve().parents[2]
    / ".apm"
    / "adapter-root-bins"
    / "intent_delivery_relations.py"
)


def _load_resolver():
    module_spec = importlib.util.spec_from_file_location(
        "_core_intent_delivery_relations",
        SOURCE,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "discovery",
    ["intent:alpha", "docs/product/intents/alpha.md"],
)
def test_ac0001_direct_relation_has_canonical_shape(
    tmp_path: Path,
    discovery: str,
) -> None:
    intents = tmp_path / "docs" / "product" / "intents"
    specs = tmp_path / "docs" / "specs" / "alpha-delivery"
    intents.mkdir(parents=True)
    specs.mkdir(parents=True)
    (intents / "alpha.md").write_text(
        "# Alpha\n\n"
        "- **Slug:** `alpha`\n"
        "- **Level:** feature\n"
        "- **Decomposed:** 2026-10-04 spec\n"
        "\n## Outcome\nignored body\n",
        encoding="utf-8",
    )
    (specs / "spec.md").write_text(
        "# Spec: Alpha delivery\n\n"
        "- **Status:** Draft\n"
        f"- **Discovery:** `{discovery}`\n"
        "\n## Outcome\nignored body\n",
        encoding="utf-8",
    )

    snapshot = _load_resolver().resolve_repository(tmp_path)

    assert snapshot["relations"] == [
        {
            "basis": {"intent": "Decomposed", "spec": "Discovery"},
            "intent": "intent:alpha",
            "route": "spec",
            "spec": "spec:alpha-delivery",
            "type": "direct-delivery",
        }
    ]
```

**Approach:** Build preamble parsing, normalization, confinement, relation derivation, and deterministic serialization in the adapter-root source. Keep CLI argument handling as a thin wrapper over `resolve_repository(root)`.

**Done when:** VI-1001 through VI-1003 pass.

### T2: Close-work consumes the canonical delivery subset

**Depends on:** T1

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_walk.py`, `packs/core/tests/skills/close-work/test_closure_index_bounds.py`

**Tests:**

- **VI-1101.** `no stub (implementation-discovered)` for AC-0012 and AC-0014. Discovery predicate: identify the narrowest existing seam where route-selected artifact membership enters the closure before status and freshness evaluation. Constraint: replace delivery inversion only; retain closure record and verdict ownership. Required outcome: an injected canonical snapshot supplies descendants while the old directory-inversion path is made to raise if called. Verification mode: TDD integration. Kill condition: if no seam isolates membership from closure policy, stop and amend the plan rather than moving closure decisions into the resolver.
- **VI-1102.** Run the existing closure walk, entry, and bounded-read suites unchanged as regression oracles (AC-0012).
- **VI-1103.** Force incomplete snapshots, every resolver invocation failure, hostile stderr, and hostile diagnostic context; assert `delivery-resolver-unavailable`, bounded sanitized output, and no retired fallback (AC-0017, AC-0018).

**Done when:** VI-1101 through VI-1103 pass.

### T3: Traceability consumes typed delivery relations without losing its graph checks

**Depends on:** T1

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/work-loop/test_lint_traceability.py`

**Tests:**

- **VI-1201.** `no stub (implementation-discovered)` for AC-0013 and AC-0014. Discovery predicate: identify the boundary between spec producer wiring and the linter's general graph classification. Constraint: canonical delivery records replace only delivery ownership; contextual provenance and non-delivery checks stay local. Required outcome: a fixture snapshot drives delivery edges while the old winner-selection path raises if it receives a delivery pointer. Verification mode: TDD integration. Kill condition: if the graph cannot accept typed delivery records without changing unrelated edge meaning, stop and amend the spec rather than flattening relation types.
- **VI-1202.** Run the existing endpoint, dangling, cycle, orphan, sidecar, and component cases unchanged as regression oracles (AC-0013).
- **VI-1203.** Force incomplete snapshots, every resolver invocation failure, hostile stderr, and hostile diagnostic context; assert `delivery-resolver-unavailable`, bounded sanitized output, unchanged non-delivery checks, and no retired fallback (AC-0017, AC-0018).

**Done when:** VI-1201 through VI-1203 pass.

### T4: Installed Core surfaces and durable records agree with the resolver

**Depends on:** T1, T2, T3

**Mode:** Goal-based check

**Touches:** `packs/core/tests/integration/test_intent_delivery_traceability.py`, Core close-work eval evidence, `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py` as projection source, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/architecture/work-intake-and-artifact-routing.md`, `docs/product/changelog.md`

**Tests:**

- **VI-1301.** `no stub (mode: goal-based)`; implement and run VI-1401 and VI-1402 at their named functions in `packs/core/tests/integration/test_intent_delivery_traceability.py` (AC-0012, AC-0013, AC-0014).
- **VI-1302.** `no stub (mode: goal-based)`; build the self-host projection from the adapter-root source without editing generated outputs, invoke the regenerated `.agentbundle/bin/intent_delivery_relations.py`, and byte-compare its normalized JSON with the source function for the same fixture (AC-0015).
- **VI-1303.** `no stub (mode: goal-based)`; update Core eval evidence, select the next unused Core minor version in both manifests for the new primitive, and run the affected pack, projection, lint, type, and documentation gates.
- **VI-1304.** Read the architecture page and changelog as whole surfaces against the shipped paths and behavior.

**Done when:** VI-1301 through VI-1304 pass.

## Rollout

The resolver, both consumers, and the Core projection ship in one pack release. There is no persisted state or migration. Rollback reverts the source changes and regenerates the self-host projection; corpus files remain untouched.

## Risks

- Process startup adds work to both consumers. The implementation measures one resolver invocation per consumer run and does not add per-artifact subprocesses.
- Existing traceability fixtures encode winner-selection behavior for non-delivery provenance. T3 must preserve that behavior outside feature delivery rather than deleting the generic graph contract.
- The current corpus contains missing and overpopulated mappings. The resolver must classify them without turning pre-existing repository data into an implementation blocker.

## Changelog

- 2026-10-04: spec approved by eugenelim
- 2026-10-04: plan approved by eugenelim
