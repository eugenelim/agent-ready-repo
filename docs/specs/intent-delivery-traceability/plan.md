# Plan: Intent delivery traceability

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/architecture/reference.md` and `docs/architecture/pack-layout.md` own pack source and repo-scope primitive projection; `guides/_shared/how-to/author-a-skill.md` owns skill self-containment; `closure_index.py` with `test_closure_walk.py` and `lint-traceability.py` with `test_lint_traceability.py` are the two current implementations and construction paths. Named deviation: their current route handling differs, so this plan moves delivery inversion to one source resolver whose byte-identical, parity-pinned copies each consuming skill ships and runs, instead of preserving either consumer as the owner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted.

## Approach

Add one standard-library resolver source that builds an immutable relation snapshot from confined artifact preambles, ship byte-identical copies of it with each consuming skill, drive it with pure fixture tests, then replace the delivery-specific scans in `close-work` and `lint-traceability.py` with checked subprocess consumption of their own copy before updating eval evidence, versions, the architecture page, and the changelog. The riskiest part is removing each private inversion without changing the unrelated closure and product-graph behavior around it.

The cheapest disconfirming probe ran the existing generic adapter-root projection case on 2026-10-04. Its projection assertion completed without a product failure; the test failed afterward in `TemporaryDirectory` cleanup with the sandbox's known `PermissionError`, so final projection proof remains assigned to CI rather than being claimed from this local run.

## Constraints

- ADR-0077 owns feature projection by shippability and coordination need.
- RFC-0103 owns typed cross-artifact reference grammar.
- `.apm/` is authoring source; generated runtime projections are outputs.
- Skills remain self-contained. They do not import sibling-skill files, and `.apm/shared-libs/` is not used for skill code.
- The resolver and consumers use the Python 3.11 standard library plus the repository file-safety confinement contract; they add no dependency. The resolver loads a byte-identical `_file_safety.py` co-located in `adapter-root-bins/` (the leading underscore keeps it a private helper rather than a published execution entry), pinned to `agentbundle.catalogue_tooling.file_safety` by a parity test, because a pipx- or zipapp-only install does not put `agentbundle` on the interpreter that runs repo-scope scripts (owner decision 1 and the helper-rename entry, verification ledger 2026-10-05).
- The feature reads preambles, returns an in-memory snapshot, and persists no graph, index, status, or coverage state.
- Core pack content carries no internal ADR, RFC, spec, task, or acceptance-criterion citation.
- Repository-durable retention: `docs/specs/intent-delivery-traceability/spec.md` and `plan.md` are read by the owner, implementer, reviewers, and CI; approval records their fingerprints. Code, tests, architecture guidance, and release history become the post-closeout evidence owners, while the spec directory remains frozen delivery history.

## Construction tests

The resolver is a pure TDD surface. Consumer wiring stays TDD but uses an implementation-discovered seam because the current scripts do not expose a shared dependency boundary; each task records the predicate and proof that close that gap.

**Integration tests:** **VI-1401** is owned by T4, extended by T8, and placed at `packs/core/tests/integration/test_intent_delivery_traceability.py::test_vi1401_resolver_and_consumers_share_delivery_snapshot`. It runs the direct, coordinated, explicit-empty, dual-provenance, missing-direct, missing-brief, direct-projection-mismatch, brief-projection-mismatch, broken-spec-reference, unsafe-corpus, resource-limit, and resolver-unavailable corpus through the resolver and both consumers, then compares each consumer's delivery edge or descendant set for equality with the resolver result, and its fail-closed diagnostics and AC-0020 refusals with the resolver's diagnostics (AC-0012, AC-0013, AC-0014, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020).

**Caller inventory:** **VI-1402** is owned by T4, restated by T9, and placed at `packs/core/tests/integration/test_intent_delivery_traceability.py::test_vi1402_only_canonical_delivery_inverter_exists`. It inventories production Python sources under `packs/core/.apm/` and accepts as delivery-relation producers only `adapter-root-bins/intent_delivery_relations.py` and its two byte-identical copies in the `close-work` and `work-loop` skill `scripts/` folders, rejecting any other producer; it asserts each consumer runs the copy beside its own file, and rejects the retired consumer-local parser and inversion entry points. The T2 and T3 forced-fallback tests remain the behavioral proof that those retired paths are unreachable (AC-0014).

**Manual verification:** none; every accepted outcome has a deterministic parser, process, or projection oracle.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — resolver source, help, and tests | T1-T13 | Resolver fixtures, consumer parity, and installed invocation | One active delivery-inversion owner and matching consumer results |
| Current architecture — `docs/architecture/work-intake-and-artifact-routing.md` | T4, T8, T13 | Whole-page diff review against the shipped paths | The page points to the owner and consumers without copying their vocabulary |
| Release history — `docs/product/changelog.md` | T4, T8, T13 | Changelog and pack-version gates | The Core release entry names the adopter-visible change |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T5, T9, T14

The canonical source is `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py` with its private `_file_safety.py`. Each consuming skill ships byte-identical copies of both in its own `scripts/` folder (`close-work` and `work-loop`), pinned to the source by parity tests, and runs its own copy. The approved assumption that a repo-scope adapter-root primitive reaches `<repository>/.agentbundle/bin/` proved false: `agentbundle install` delivers adapter-root binaries only at user scope, and Core installs only at repo scope (verification ledger, 2026-10-06). The source's own `.agentbundle/bin/` projection, produced by the self-host build, remains a maintainer diagnostic tool in this repository, not an adopter route; adopter-facing records name only the skill-local copies. Skill-local copies travel with every install route, while a sibling-skill import and the specialised `shared-libs` rail would not satisfy the skill portability rules.

The resolver's in-process `resolve_repository(root)` result and CLI JSON share one dictionary shape: `schema_version`, `complete`, `relations`, `classifications`, `provenance`, and `diagnostics`. The amendment adds a seventh top-level key, `artifacts`, mapping each identifier any relation, provenance record, or diagnostic names to its repository-relative artifact path, so a consumer reads exactly the artifact the resolver matched. Relation records keep their delivered shape — canonical endpoint identifiers, relation type, route, and a field-basis map — so the delivered AC-0001 equality holds unchanged. A provenance record whose target resolves to an admitted intent also carries that intent's identifier. For each brief that an ambiguous spec `Brief:` names, the resolver adds one `Parent intent` provenance record per distinct admitted feature intent that the brief's valid `Parent intent:` values name, so values of different kinds that share one slug give one record, `{subject: brief:<slug>, field: "Parent intent", intent: intent:<slug>}`, so a consumer maps a named brief to every feature it names from the snapshot alone. Only an artifact whose `Slug:` matches the slug grammar becomes an identifier. Lists are sorted before strict serialization so an identical tree yields identical bytes.

### Interfaces & contracts

Owned by: T1, T2, T3, T5, T6, T7, T9, T10, T11, T14

Each consumer invokes the resolver copy in its own skill `scripts/` folder, located from its own resolved file path and never from the repository root, with the current Python interpreter, the repository root, JSON output, a bounded timeout, and captured standard streams. They validate the schema version, completeness flag, the exact seven top-level keys, output-size ceiling, the record shape of every item (a dict whose consumed fields are strings of the expected grammar), and every `artifacts` path against its identifier's type root and file grammar, before use. Absence, an incomplete result, non-zero exit, timeout, invalid UTF-8, malformed JSON, or an unsupported schema version produces the consumer-authored `delivery-resolver-unavailable` code and no consumer-specific fallback; captured stderr is never forwarded.

This is an internal Core runtime seam, not a portable service or API contract, so the spec names `Contract: none`. The source, help output, typed construction fixtures, and architecture page own its compatibility surface.

### Failure, edge cases & resilience

Owned by: T1, T2, T3, T5, T6, T7, T9, T10, T11, T14

The resolver distinguishes absent mappings, direct-route multiplicity, incompatible same-type targets, malformed references, unsafe lexical references, and explicit empty routes according to the spec criteria. The co-located, parity-pinned `_file_safety.py` — the resolver's only confinement source — validates each artifact root, bounds enumeration, and performs every preamble read before relation validation; therefore an unsafe corpus entry produces only the AC-0016 incomplete result, while AC-0010 handles absolute and parent-traversing reference text that never reaches corpus admission. Every admitted file is opened at most once per snapshot, and body text cannot affect the result. The resolver enforces the six AC-0017 budgets before materializing the next entry, file, byte range, or serialized result. A refused corpus or breached budget returns `complete: false` with no partial delivery data. Diagnostic rendering admits only stable codes, limit names, and identifiers or repository-relative paths that match the canonical grammar under a length cap; anything else is omitted. Every absolute or parent-traversing relation reference — any `Brief:` or `Parent intent:` value, or an intent-shaped `Discovery:` value — reports `delivery-reference-unsafe`; a non-intent-shaped `Discovery:` stays contextual provenance and is emitted without its target. Duplicate brief slugs are ambiguous, as duplicate intent slugs are. `_`-prefixed spec directories are not delivery artifacts. A link at any part of an artifact-root path makes the snapshot incomplete. The resolver reads only the default artifact roots, so the lint fails closed with `delivery-resolver-unavailable` when its configured or discovered spec or intent base differs from them. A consumer failure never falls back to its retired scanner because that would restore split answers.

### Dependencies & integration

Owned by: T1, T2, T3, T4, T5, T8, T9, T13

No new dependency or adapter-contract version is introduced: the resolver reaches adopters inside the two skills that use it. T1's kill condition fired in review: a documented pipx or zipapp install cannot import `agentbundle` from repo-scope scripts. The owner chose the co-located, parity-pinned copy pattern already used by three Core skills, projected as the private helper `_file_safety.py`, so confinement logic is projected unchanged rather than vendored or weakened. `close-work` retains ownership of status, freshness, and closure verdicts. `lint-traceability.py` retains the general product graph, endpoint, cycle, and orphan checks. The resolver owns only feature-delivery relation parsing, inversion, classification, and strict serialization.

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

### T5: The resolver loads co-located confinement and emits only validated identities

**Depends on:** T1

**Mode:** TDD

**Touches:** `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`, `packs/core/.apm/adapter-root-bins/_file_safety.py`, `packs/core/tests/pack/test_intent_delivery_relations.py`, `packs/core/tests/pack/test_intent_delivery_relations_confinement.py` (stub materialization file), the required-key sets in `packs/core/.apm/skills/close-work/scripts/closure_index.py` and `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, and the delivered six-key snapshot fixtures under `packs/core/tests/skills/close-work/`, `packs/core/tests/skills/work-loop/test_lint_traceability.py`, and `packs/core/tests/integration/test_intent_delivery_traceability.py`

**Tests:**

- **VI-1501.** `test_ac0016_resolver_runs_without_agentbundle` runs the resolver and its co-located helper under `python -I -S`, where `agentbundle` cannot be imported, and gets a complete snapshot carrying the `artifacts` key (AC-0016, AC-0018), `stub: true`. Green adds: a parity test pinning `_file_safety.py` byte-identical to `agentbundle.catalogue_tooling.file_safety`; the helper is found only in the resolver's own resolved directory and must be a regular, non-link file; a load failure exits 2 with one stable-code line before any corpus read.
- **VI-1502.** Slug grammar, unsafe relation references on every field AC-0010 names, a contextual non-intent `Discovery:` that is absolute or traversing, duplicate brief slugs, `_`-prefixed spec directories, and a link at an intermediate artifact-root part each produce the full expected snapshot, compared for equality (AC-0007, AC-0008, AC-0010, AC-0016, AC-0018).
- **VI-1503.** Every VI-1002 relation-semantics fixture (AC-0002–AC-0011, AC-0019) asserts equality with the complete expected snapshot, including `artifacts` and resolved provenance identity. VI-1001 stays byte-identical and green, because relation records keep their delivered shape.
- **VI-1504.** Hostile `Slug:`, `Decomposed:`, and `Discovery:` values carrying control, bidi, and instruction-shaped text never appear in resolver JSON (AC-0018).
- **VI-1505.** Both consumers accept exactly the seven-key snapshot, the delivered six-key fixtures move to seven keys, and every delivered suite stays green at the T5 boundary, so no task opens a red window (AC-0012, AC-0013, AC-0015).
- Stub validation: syntax and intended red ("co-located confinement helper is missing") passed on 2026-10-05 from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0016
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

BINS = Path(__file__).resolve().parents[2] / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"


def test_ac0016_resolver_runs_without_agentbundle(tmp_path: Path) -> None:
    assert HELPER.is_file(), "co-located confinement helper is missing"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shutil.copy2(SOURCE, bin_dir / SOURCE.name)
    shutil.copy2(HELPER, bin_dir / HELPER.name)
    repo = tmp_path / "repo"
    (repo / "docs" / "specs").mkdir(parents=True)

    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(bin_dir / SOURCE.name), "--root", str(repo)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert proc.returncode == 0
    snapshot = json.loads(proc.stdout)
    assert snapshot["complete"] is True
    assert snapshot["artifacts"] == {}
```

**Approach:** Load the helper the way close-work loads its co-located copy, from the script's own directory, then add the identity, unsafe-reference, and membership rules ahead of relation derivation. The `--help` text opens with the question the tool answers and names the two causes of exit 1.

**Done when:** VI-1501 through VI-1505 pass, and the resolver's `--help` opens with the question it answers and names the two causes of exit 1 (a resource limit or an unsafe corpus entry).

### T6: Close-work validates every snapshot record, reads matched paths, and refuses on broken specs

**Depends on:** T2, T5

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_broken_spec_refusal.py` (stub materialization file), and the existing suites under `packs/core/tests/skills/close-work/`

**Tests:**

- **VI-1601.** `test_ac0020_broken_spec_reference_refuses_closure` injects a snapshot whose only defect is an unsafe spec `Discovery:` and asserts the `spec`-route feature is refused with that code (AC-0020), `stub: true`. Green completes every row of AC-0020's refusal table, plus a fixture without such a diagnostic that keeps its verdict.
- **VI-1602.** A snapshot whose items are not dicts, whose consumed fields are not strings of the expected grammar, or whose `artifacts` path disagrees with its identifier's type root and file grammar, yields `delivery-resolver-unavailable` with no traceback (AC-0018).
- **VI-1603.** Descendant status is read from the snapshot's `artifacts` path, never rebuilt from a slug; an ancestor reached through provenance uses the resolved intent identifier (AC-0012).
- **VI-1604.** Rewritten close-work regression cases inject only snapshots the real resolver produces for their fixtures, or assert the changed verdict; the confinement cases name an escaping and a symlinked spec in the snapshot and prove neither adds a descendant (AC-0012, AC-0016).
- Stub validation: syntax and intended red (the feature is judged `ClosureEligible`) passed on 2026-10-05 from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0020
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "close-work"
    / "scripts"
    / "closure_index.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_core_close_work_closure_index_ac0020", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_ac0020_broken_spec_reference_refuses_closure(tmp_path: Path) -> None:
    ci = _load()
    spec_dir = tmp_path / "docs" / "specs" / "done-spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# Spec\n\n- **Status:** Shipped\n", encoding="utf-8")
    snapshot = {
        "schema_version": 1,
        "complete": True,
        "relations": [
            {
                "basis": {"intent": "Decomposed", "spec": "Discovery"},
                "intent": "intent:alpha",
                "route": "spec",
                "spec": "spec:done-spec",
                "type": "direct-delivery",
            }
        ],
        "classifications": [
            {"classification": "direct-delivery", "intent": "intent:alpha", "route": "spec"}
        ],
        "provenance": [],
        "diagnostics": [
            {"code": "delivery-reference-unsafe", "field": "Discovery", "subject": "spec:broken-spec"}
        ],
        "artifacts": {"spec:done-spec": "docs/specs/done-spec/spec.md"},
    }

    verdict = ci.check_ancestor_closure(
        "alpha",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=lambda _root: snapshot,
    )

    assert isinstance(verdict, ci.ClosureRefuse)
    assert "delivery-reference-unsafe" in verdict.reason
```

**Approach:** Validate the snapshot fully at the invocation seam, then resolve descendants and AC-0020 refusals from validated records only.

**Done when:** VI-1601 through VI-1604 pass, the unreachable `None` guard and the redundant `JSONDecodeError` catch are gone, and no comment in the touched code contradicts the fail-closed behaviour.

### T7: Traceability validates every snapshot record and keeps its non-delivery checks

**Depends on:** T3, T5

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/work-loop/test_lint_traceability.py`, `packs/core/tests/skills/work-loop/test_lint_traceability_delivery_checks.py` (stub materialization file), `packs/core/.apm/skills/work-loop/evals/evals.json`, `tools/test_local_ci_shared_test_deduplication.py`

**Tests:**

- **VI-1701.** `test_ac0013_diagnosed_spec_keeps_component_dangling_check` runs the lint, with the real resolver projected, on a projection-mismatch fixture whose spec carries a dangling `Component:`, and asserts the DANGLING violation and exit 1 survive (AC-0013), `stub: true`. Green adds the non-delivery `_wire_up` dangling checks for the same spec; only its backward-orphan classification is suppressed.
- **VI-1702.** A malformed snapshot record is a hard `delivery-resolver-unavailable` violation, never the degraded exit-0 path, including under `--strict` (AC-0018).
- **VI-1703.** In a repository with a chain anchor, a configured or discovered spec or intent base that differs from the resolver's default roots fails closed with `delivery-resolver-unavailable` while non-delivery checks still run; without an anchor the lint still exits 0 silently (AC-0013, AC-0018).
- **VI-1704.** Delivery diagnostic lines print only stable codes and grammar-valid, length-capped identifiers; hostile resolver output never reaches stdout or stderr (AC-0018).
- **VI-1705.** The fail-closed cases drive `_run_resolver` through a stub resolver that writes hostile stderr, emits invalid JSON, exceeds a test-lowered timeout, or returns `complete: false`, and assert on `check()` output; the provider reaches `check()` as a parameter rather than a module global (AC-0017, AC-0018).
- Stub validation: syntax and intended red (exit 0, so the dangling `Component:` was dropped) passed on 2026-10-05 from a disposable scratch mirror of `packs/core/`; no repository test file was created. That run took the lint path that accepts the snapshot, which is the path the lint takes after T5 because VI-1505 moves its key set with the resolver; EXECUTE re-proves this red before any T7 production change.

```python
# STUB: AC-0013
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

APM = Path(__file__).resolve().parents[3] / ".apm"
LINTER = APM / "skills" / "work-loop" / "scripts" / "lint-traceability.py"
BINS = APM / "adapter-root-bins"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac0013_diagnosed_spec_keeps_component_dangling_check(tmp_path: Path) -> None:
    for source in BINS.glob("*.py"):
        target = tmp_path / ".agentbundle" / "bin" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    _write(tmp_path / "docs/product/briefs/anchor.md", "# Brief\n\n- **Slug:** `anchor`\n")
    _write(
        tmp_path / "docs/product/intents/alpha.md",
        "# Alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n- **Decomposed:** 2026-10-05 spec\n",
    )
    for slug in ("s1", "s2"):
        _write(
            tmp_path / f"docs/specs/{slug}/spec.md",
            f"# Spec: {slug}\n\n- **Status:** Draft\n- **Discovery:** `intent:alpha`\n"
            + ("- **Component:** ghost-comp\n" if slug == "s1" else ""),
        )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 1
    assert "ghost-comp" in proc.stderr
```

**Approach:** Move the delivery-diagnostic effect to orphan classification only, validate the snapshot fully at the seam, and thread the provider through `check()`.

**Done when:** VI-1701 through VI-1705 pass; `_run_resolver` is annotated `dict`; the duplicate `_delivery_diag_specs` and `_contextual_prov` declarations, review-round comments, redundant `JSONDecodeError` catch, and dead `__wrapped__` test expression are gone; no comment or docstring in the touched lint code contradicts the fail-closed behaviour; and the work-loop eval evidence covers the hard malformed-record and configured-layout outcomes.

### T8: Integration proof, real projection, and adopter-facing records agree

**Depends on:** T4, T5, T6, T7

**Mode:** Goal-based check

**Touches:** `packs/core/tests/integration/test_intent_delivery_traceability.py`, `packs/core/tests/pack/test_intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/evals/evals.json`, `docs/product/changelog.md`, `guides/core/how-to/close-and-disposition-work.md`, `docs/architecture/work-intake-and-artifact-routing.md`, self-host projections

**Tests:**

- **VI-1801.** `no stub (mode: goal-based)`; bring VI-1401 to the scope stated under Construction tests, spawning the resolver CLI once per case.
- **VI-1802.** `no stub (mode: goal-based)`; one test installs Core at repository scope into a clean temporary repository with the in-tree `agentbundle` and invokes the installed `.agentbundle/bin/intent_delivery_relations.py`, comparing its JSON with `resolve_repository`; the projected exit-1 case forces an incomplete snapshot and asserts exactly 1 (AC-0015).
- **VI-1803.** `no stub (mode: goal-based)`; rebuild the self-host projection, and correct the changelog and how-to: each delivery code's severity as the code applies it, each cause of `delivery-resolver-unavailable` with its remedy, the repository-scope install requirement explained in plain words, and the closure-refusal rule. The how-to's refuse cell states one fact, and a list below the table says what each `delivery-…` code close-work can name means and what to edit.

**Done when:** VI-1801 through VI-1803 pass and the affected pack, projection, lint, type, and documentation gates pass.

### T9: Each consumer skill ships and runs its own resolver copy

**Depends on:** T8

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/close-work/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/scripts/_file_safety.py`, `packs/core/.apm/skills/work-loop/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/work-loop/scripts/_file_safety.py`, `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/pack/test_intent_delivery_relations_copies.py`, `packs/core/tests/integration/test_intent_delivery_traceability.py`, `packs/core/tests/**`, `tests/roster/**` (the four copies are byte-identical to the source; the copies test file is the stub materialization file; the integration file holds the VI-1402 inventory; the test globs cover every delivered test or fixture that installs the resolver at `.agentbundle/bin/` or asserts that location)

**Tests:**

- **VI-1901.** `test_ac0014_each_consumer_skill_ships_the_resolver` asserts each consuming skill's `scripts/` folder holds the resolver and helper byte-identical to the source (AC-0014), `stub: true`.
- **VI-1902.** Each consumer locates the resolver from its own resolved file path; a resolver absent beside the consumer, or a non-regular or linked one, is `delivery-resolver-unavailable`, proved through a narrow test seam for the location rather than by deleting the real copy (AC-0014, AC-0018).
- **VI-1904.** The VI-1402 caller inventory, restated under Construction tests, passes with the two copies in place and fails when any other production file produces a delivery relation (AC-0014).
- **VI-1903.** One test runs a real `agentbundle install --pack core --scope repo` into a clean temporary repository with the in-tree `agentbundle`, then runs each installed copy under `python -I -S` on a fixture and asserts its stdout equals the source's serialized snapshot byte-for-byte; it also runs the installed lint on a fixture with an anchor and asserts no `delivery-resolver-unavailable` (AC-0015).
- Stub validation: syntax and intended red ("close-work ships no intent_delivery_relations.py") passed on 2026-10-06, re-run after the stub was renamed to the criterion it pins, from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0014
from __future__ import annotations

from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
BINS = CORE / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"


def test_ac0014_each_consumer_skill_ships_the_resolver() -> None:
    for skill in ("close-work", "work-loop"):
        scripts = CORE / ".apm" / "skills" / skill / "scripts"
        for source in (SOURCE, HELPER):
            copy = scripts / source.name
            assert copy.is_file(), f"{skill} ships no {source.name}"
            assert copy.read_bytes() == source.read_bytes()
```

**Approach:** Copy the source and helper into both skills, point each consumer at its sibling copy, and move every delivered `.agentbundle/bin/` fixture to the new location or the seam.

**Done when:** VI-1901 through VI-1904 pass and no consumer or test still looks for the resolver under `.agentbundle/bin/`.

### T10: Resolver and lint emit only canonical diagnostic content

**Depends on:** T9

**Mode:** TDD

**Touches:** `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py` and its two skill copies, `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/pack/test_intent_delivery_relations_hostile_targets.py` (stub materialization file), and the lint and close-work validator tests

**Tests:**

- **VI-2001.** `test_ac0018_ambiguous_targets_carry_no_raw_artifact_text` asserts every diagnostic target the resolver emits for an ambiguous `Decomposed:` field is printable (AC-0018), `stub: true`. Green extends it to ambiguous `Discovery:` targets and checks decoded values: a target is only a canonical identifier, `docs/product/intents/<artifact file>`, or `<date> <route in the closed route set>`; anything else is omitted.
- **VI-2002.** Every provenance record whose target resolves to an admitted intent carries that intent's identifier, whatever the intent's route; an absolute provenance target, including a drive-letter or backslash form, is emitted without its target for both `Contract:` and `Discovery:` (AC-0001, AC-0010, AC-0018).
- **VI-2003.** Both consumers reject a diagnostic `field` outside the closed field set and a target outside the canonical forms, and a lint line prints only the code, a validated subject, a closed-set field, and canonical targets; an unhashable value in any closed-set field is `delivery-resolver-unavailable` in both consumers with no traceback, proved by one malformed-record table run against both (AC-0018).
- Stub validation: syntax and intended red (a raw control or bidi character reaches a target) passed on 2026-10-06 from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0018
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[2]
    / ".apm"
    / "adapter-root-bins"
    / "intent_delivery_relations.py"
)


def _load_resolver():
    module_spec = importlib.util.spec_from_file_location(
        "_core_intent_delivery_relations_ac0018",
        SOURCE,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_ac0018_ambiguous_targets_carry_no_raw_artifact_text(tmp_path: Path) -> None:
    intents = tmp_path / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    (intents / "alpha.md").write_text(
        "# Alpha\n\n"
        "- **Slug:** `alpha`\n"
        "- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\x1b[31m\n"
        "- **Decomposed:** 2026-10-06 brief‮\n",
        encoding="utf-8",
    )

    snapshot = _load_resolver().resolve_repository(tmp_path)

    ambiguous = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-relation-ambiguous" and d.get("subject") == "intent:alpha"
    ]
    assert ambiguous
    targets = [target for d in snapshot["diagnostics"] for target in d.get("targets", [])]
    assert all(target.isprintable() for target in targets)
```

**Approach:** Canonicalize targets where the resolver builds diagnostics, mirror the same closed sets in both consumer validators, and add the string guard to the lint's closed-set check.

**Done when:** VI-2001 through VI-2003 pass and the three resolver copies stay byte-identical.

### T11: Close-work refuses exactly the AC-0020 sets on both routes

**Depends on:** T10

**Mode:** TDD

**Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_ambiguous_refusal.py` (stub materialization file), and `packs/core/tests/skills/close-work/`

**Tests:**

- **VI-2101.** `test_ac0020_path_form_ambiguous_discovery_refuses_named_feature` uses the real resolver and asserts a feature named by the path form of an ambiguous `Discovery:` is refused with `delivery-relation-ambiguous` (AC-0020), `stub: true`.
- **VI-2102.** With real-resolver snapshots, one test per AC-0020 row, each placing the broken artifact on an unrelated spec or brief: an ambiguous `Discovery:` refuses each named feature on either route; an ambiguous `Brief:` refuses the feature named by each named brief's `Parent intent:`, or every `brief`-route feature when none resolves; malformed, unsafe, and missing-target spec `Brief:` each refuse every `brief`-route feature; a brief-subject diagnostic refuses every `brief`-route feature; every refusal names the stable code (AC-0020).
- **VI-2103.** An ancestor reached through provenance follows only the record's `intent` identifier, so the `intent:<slug>` and path forms of one reference give the same ancestor (AC-0001, AC-0012).
- **VI-2104.** Close-work's real `_run_resolver`, driven through stub resolvers, returns exactly `delivery-resolver-unavailable` for a linked resolver, a test-lowered timeout, oversized stdout, non-UTF-8 stdout, and hostile stderr, with no stub output in the reason (AC-0017, AC-0018).
- Stub validation: syntax and intended red (the named feature is judged `ClosureEligible`) passed on 2026-10-06 from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0020
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

APM = Path(__file__).resolve().parents[3] / ".apm"


def _load(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac0020_path_form_ambiguous_discovery_refuses_named_feature(tmp_path: Path) -> None:
    resolver = _load(
        "_core_intent_delivery_relations_ac0020",
        APM / "adapter-root-bins" / "intent_delivery_relations.py",
    )
    closure = _load(
        "_core_close_work_closure_index_ac0020_path",
        APM / "skills" / "close-work" / "scripts" / "closure_index.py",
    )
    for slug in ("alpha", "beta"):
        _write(
            tmp_path / f"docs/product/intents/{slug}.md",
            f"# {slug}\n\n- **Slug:** `{slug}`\n- **Level:** feature\n"
            "- **Status:** Accepted\n- **Decomposed:** 2026-10-06 spec\n",
        )
        _write(
            tmp_path / f"docs/specs/{slug}-delivery/spec.md",
            f"# Spec\n\n- **Status:** Shipped\n- **Discovery:** `intent:{slug}`\n",
        )
    _write(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Discovery:** `intent:alpha`\n"
        "- **Discovery:** `docs/product/intents/beta.md`\n",
    )

    verdict = closure.check_ancestor_closure(
        "beta",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=resolver.resolve_repository,
    )

    assert isinstance(verdict, closure.ClosureRefuse)
    assert "delivery-relation-ambiguous" in verdict.reason
```

**Approach:** Compute each broken field's refusal set from the snapshot alone, normalizing path-form targets through `artifacts` to identifiers.

**Done when:** VI-2101 through VI-2104 pass.

### T12: Lint and integration tests fail for the behaviour they name

**Depends on:** T10

**Mode:** Goal-based check

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/work-loop/`, `packs/core/tests/integration/test_intent_delivery_traceability.py`, `packs/core/.apm/skills/close-work/scripts/closure_index.py` (constants only)

**Tests:**

- **VI-2201.** `no stub (mode: goal-based)`; the configured-layout cases install a working resolver and assert the configured-base outcome for both the spec base and the intent base, and the default-bases control asserts exit 0 (AC-0013).
- **VI-2202.** `no stub (mode: goal-based)`; production `check()` reads no module-global provider, a `None` provider result is `delivery-resolver-unavailable`, the timeout case asserts through `check()`, and superseded tests that cannot fail for their stated behaviour are rewritten or removed (AC-0018).
- **VI-2203.** `no stub (mode: goal-based)`; each VI-1401 case spawns the resolver once and feeds that snapshot to both consumers' in-process seams.

**Done when:** VI-2201 through VI-2203 pass; one definition per constant, no unused sets, and no repeated top-level check remain in the touched consumer code; no lint comment says the resolver can return `None`; and no assertion checks for content its fixture never contained.

### T14: Close-work maps named briefs from the snapshot and refuses only AC-0020's sets

**Depends on:** T11, T12

**Mode:** TDD

**Touches:** `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/work-loop/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/close-work/test_closure_brief_parent_links.py` (stub materialization file), `packs/core/tests/skills/close-work/`, `packs/core/tests/skills/work-loop/`, `packs/core/tests/pack/`, `packs/core/tests/integration/test_intent_delivery_traceability.py`

**Tests:**

- **VI-2401.** `test_ac0020_every_parent_of_a_named_brief_is_refused` uses the real resolver: a brief whose file name differs from its slug carries two `Parent intent:` values and is named by an ambiguous spec `Brief:`; both named `spec`-route features are refused with `delivery-relation-ambiguous` and an unrelated `spec`-route feature stays eligible (AC-0020), `stub: true`.
- **VI-2402.** With real-resolver snapshots, a malformed, an unsafe, and a missing-target spec `Brief:`, and an ambiguous spec `Brief:` whose named briefs resolve to no feature, each refuse a `brief`-route feature with that code while an unrelated `spec`-route feature stays eligible (AC-0020).
- **VI-2403.** An ambiguous spec `Brief:` refuses a `closed-empty` and a `direct-light` feature named by a named brief's `Parent intent:`, and an ambiguous spec `Discovery:` refuses a named `direct-light` feature; an unrelated feature of the same route stays eligible in each case (AC-0020).
- **VI-2404.** The resolver emits the `Parent intent` provenance records the design defines, both consumers' validators accept that field, the lint's results are unchanged by them, and `Parent intent:` values of different kinds that share one slug form one parent, one record, and no ambiguity diagnostic (AC-0001, AC-0008).
- **VI-2405.** The lint returns exit 1 with `delivery-resolver-unavailable` and no traceback for a deeply nested resolver payload, and cuts a printed subject or target longer than 200 characters at the cap (AC-0018).
- Stub validation: syntax and intended red (`beta` is judged `ClosureEligible`) passed on 2026-10-07 from a disposable scratch mirror of `packs/core/`; no repository test file was created.

```python
# STUB: AC-0020
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

APM = Path(__file__).resolve().parents[3] / ".apm"


def _load(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac0020_every_parent_of_a_named_brief_is_refused(tmp_path: Path) -> None:
    resolver = _load(
        "_core_intent_delivery_relations_brief_parents",
        APM / "adapter-root-bins" / "intent_delivery_relations.py",
    )
    closure = _load(
        "_core_close_work_closure_index_brief_parents",
        APM / "skills" / "close-work" / "scripts" / "closure_index.py",
    )
    for slug in ("alpha", "beta", "gamma"):
        _write(
            tmp_path / f"docs/product/intents/{slug}.md",
            f"# {slug}\n\n- **Slug:** `{slug}`\n- **Level:** feature\n"
            "- **Status:** Accepted\n- **Decomposed:** 2026-10-07 spec\n",
        )
        _write(
            tmp_path / f"docs/specs/{slug}-delivery/spec.md",
            f"# Spec\n\n- **Status:** Shipped\n- **Discovery:** `intent:{slug}`\n",
        )
    _write(
        tmp_path / "docs/product/briefs/BRF-0001-shared.md",
        "# Shared\n\n- **Slug:** `shared`\n- **Status:** Executing\n"
        "- **Parent intent:** intent:alpha\n- **Parent intent:** intent:beta\n",
    )
    _write(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:shared`\n- **Brief:** `brief:missing`\n",
    )

    def verdict(slug: str):
        return closure.check_ancestor_closure(
            slug,
            "Accepted",
            "spec",
            tmp_path,
            _freshness_checker=lambda: True,
            _snapshot_provider=resolver.resolve_repository,
        )

    for named in ("alpha", "beta"):
        refused = verdict(named)
        assert isinstance(refused, closure.ClosureRefuse), (named, refused)
        assert "delivery-relation-ambiguous" in refused.reason
    assert isinstance(verdict("gamma"), closure.ClosureEligible)
```

**Approach:** The resolver reports each named brief's parents in the snapshot. Close-work reads every named-brief mapping from those records, parses no delivery field, and applies a spec `Brief:` diagnostic to a `spec`-route, `closed-empty`, or `direct-light` feature only through that mapping.

**Done when:** VI-2401 through VI-2405 pass; on the AC-0020 refusal path, close-work maps a brief named by an ambiguous spec `Brief:` only from the snapshot and reads no brief file to do so, while the delivered `resolve_intent_ancestors` brief walk stays unchanged; no unused `_feature_intent_ids_dl` remains in close-work; the resolver's `artifacts` comment matches the design's definition; the three resolver copies are byte-identical; and the integration docstring no longer says `direct-light` closure needs no snapshot.

### T13: Release 2.29.0 records agree with the shipped behaviour

**Depends on:** T9, T10, T11, T12, T14

**Mode:** Goal-based check

**Touches:** `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/work-loop/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `guides/core/how-to/close-and-disposition-work.md`, `docs/architecture/work-intake-and-artifact-routing.md`, `packs/core/.apm/skills/close-work/evals/evals.json`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `tools/test_local_ci_shared_test_deduplication.py`, `.claude/**`, `.agents/**`, `.agentbundle/**` (the last three are self-host projections)

**Tests:**

- **VI-2301.** `no stub (mode: goal-based)`; Core is `2.29.0` in both manifests, the changelog entry, and the architecture page; the changelog states each consumer's resolver condition as its code applies it, names the skill-local copies as what ships, and drops the `.agentbundle/bin/` claims.
- **VI-2302.** `no stub (mode: goal-based)`; the how-to gives both outcomes of a direct resolver run, every cause of `delivery-target-missing`, every field that produces `delivery-reference-malformed` with its accepted form, and a remedy that points at the skill-local resolver; the architecture page states each consumer's call frequency; the resolver `--help` explains its terms in plain words and says where an exit-1 cause is reported.
- **VI-2303.** `no stub (mode: goal-based)`; no acceptance-criterion, verification-item, or task citation added by this feature remains under `packs/core/.apm/`, and the plan-digest pins re-pin with a disposition against `origin/main`.

**Done when:** VI-2301 through VI-2303 pass and the full gate set passes.

## Rollout

The resolver, both consumers, and their skill-local copies ship in one Core release, `2.29.0`. There is no persisted state or migration. Rollback reverts the source changes and regenerates the self-host projection; corpus files remain untouched.

## Risks

- Process startup adds work to both consumers. The implementation measures one resolver invocation per consumer run and does not add per-artifact subprocesses.
- Existing traceability fixtures encode winner-selection behavior for non-delivery provenance. T3 must preserve that behavior outside feature delivery rather than deleting the generic graph contract.
- The current corpus contains missing and overpopulated mappings. The resolver classifies them; they block only what AC-0020 refuses. Two unsafe `Discovery:` links that would have refused every `spec`-route feature under AC-0020 were rewritten as `intent:<slug>` references under owner decision 4, so AC-0020 refuses nothing in the current corpus. Ten features whose own subject carries a missing-target or projection-mismatch diagnostic are still refused under AC-0012; the verification ledger names them, and repairing them is outside this delivery.

## Changelog

- 2026-10-04: spec approved by eugenelim
- 2026-10-04: plan approved by eugenelim
- 2026-10-05: controlled amendment after round-1 review. T1's kill condition fired (no `agentbundle` import on documented pipx or zipapp installs); the owner chose a co-located, parity-pinned `file_safety.py`, closure refusal for broken spec references (new AC-0020), and per-consumer wording. Adds T5–T8 for those decisions and the sustained review findings; T1–T4 are delivered and unchanged. Authority: `notes/verification-ledger.md`.
- 2026-10-05: amendment revised from the pre-EXECUTE review: snapshot paths move to a top-level `artifacts` key so delivered relation records keep their shape; T5–T7 each carry a validated stub; the helper is the private `_file_safety.py`; AC-0010 names which references it covers and AC-0020 fixes one refusal set per broken field; every sustained round-1 finding maps to a T5–T8 test or Done-when clause.
- 2026-10-05: second pre-EXECUTE revision: T5 moves both consumers' key sets and the delivered fixtures to the seven-key snapshot (VI-1505) so every task boundary stays green and T7's stub keeps its red; stubs are named after the criteria they pin with one materialization file each; T5 and T7 Done-when cover the `--help` text and the fail-closed comments; Risks records owner decision 4.
- 2026-10-05: third pre-EXECUTE revision: Risks separates AC-0020 refusals (none) from the ten AC-0012 own-subject refusals the ledger names; VI-1401's scope is stated once under Construction tests.
- 2026-10-05: amended spec approved by eugenelim
- 2026-10-05: amended plan approved by eugenelim, ratifying the private `_file_safety.py` helper name
- 2026-10-06: second controlled amendment after post-build review. A real repo-scope install never delivers adapter-root binaries, so each consuming skill ships its own parity-pinned resolver copy (owner decision 5); Core moves to `2.29.0` after rebasing onto `main` (owner decision 6). Adds T9–T13 for those decisions and the sustained findings; T1–T8 are delivered and unchanged. Authority: `notes/verification-ledger.md`.
- 2026-10-06: second amendment revised from its pre-EXECUTE review: VI-1402 restated to accept the two parity-pinned copies (VI-1904); T9's stub pins AC-0014; T12 and T13 own the remaining comment, assertion, and file-scope gaps; the source's `.agentbundle/bin/` projection is named a maintainer diagnostic tool.
- 2026-10-06: second amended spec approved by eugenelim
- 2026-10-06: second amended plan approved by eugenelim
- 2026-10-07: third controlled amendment after post-build review round 3. Close-work mapped a named brief to its features by reading the brief's file, against AC-0014 and T11; the owner chose resolver-reported brief parents (owner decision 7). Adds T14 for that decision and the round-3 findings, and T13 now depends on it; T1–T12 are delivered and unchanged. Authority: `notes/verification-ledger.md`.
- 2026-10-07: third amendment revised from its pre-EXECUTE review: T14's Done-when names the resolver comment and the unused set, scopes the no-brief-read rule to the AC-0020 refusal path, and the design counts one record per named intent.
- 2026-10-07: third amended spec approved by eugenelim
- 2026-10-07: third amended plan approved by eugenelim
