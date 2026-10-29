"""Independent preservation evidence through the shipped evidence store.

A fixture substrate (``fixtures/preservation-substrate/``) has a base and a head
implementation. One oracle per term runs on an implementation under test; the
producer emits a passing receipt only when the oracle passes and then fails on
the oracle's named mutation. Every verdict is decided by
``EvidenceStore.append_receipt`` and ``EvidenceStore.evaluate_verdicts``.

Spec: docs/specs/grounding-preservation-evidence/spec.md
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib.util
import itertools
import os
import stat
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors and loaders ──────────────────────────────────────────────────

WORK_LOOP = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPTS = WORK_LOOP / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "preservation-substrate"
HEAD_SOURCE = (FIXTURES / "head.py").read_text(encoding="utf-8")
BASE_SOURCE = (FIXTURES / "base.py").read_text(encoding="utf-8")


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = prev


def _load_source(name: str, source: str) -> ModuleType:
    """Execute *source* as a fresh module; registered only while it runs (dataclasses need it)."""
    mod = ModuleType(name)
    sys.modules[name] = mod
    try:
        exec(compile(source, f"<{name}>", "exec"), mod.__dict__)  # noqa: S102
    finally:
        sys.modules.pop(name, None)
    return mod


BASE = _load_source("core_work_loop_preservation_evidence_base", BASE_SOURCE)


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path."""
    return _load_module("core_work_loop_acc_preservation_evidence", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def es() -> ModuleType:
    """_evidence_store.py loaded by path."""
    return _load_module("core_work_loop_es_preservation_evidence", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_module(
        "core_work_loop_sc_preservation_evidence", SCRIPTS / "_security_capability.py"
    )


# ── Corpus and the edits the oracles apply ────────────────────────────────────

CORPUS: dict[str, str] = {
    "a.py": "value shared\ndef util\ncall helper\n",
    "b.py": "def shared\ncall util\ncall shared\n",
    "c.py": "def helper\ncall shared\nvalue gamma\ndef other\n",
    "d.py": "call other\nvalue extra\n",
}
EDIT_FILE = "c.py"
EDIT_TEXT = "def helper\ncall util\ncall shared\nvalue delta\n"
EDITED: dict[str, str] = {**CORPUS, EDIT_FILE: EDIT_TEXT}
REMOVED_FILE = "c.py"


def _lines(corpus: dict[str, str], kind: str) -> list[tuple[str, str]]:
    """(file, NAME) for every line of *kind*, read from the text alone."""
    found = []
    for file, text in corpus.items():
        for line in text.splitlines():
            word, _, name = line.strip().partition(" ")
            if word == kind and name.strip():
                found.append((file, name.strip()))
    return found


def _names(corpus: dict[str, str], kind: str) -> set[str]:
    return {name for _, name in _lines(corpus, kind)}


QUERIES = sorted(
    _names(CORPUS, "def") | _names(CORPUS, "call") | _names(CORPUS, "value")
)


LIFECYCLE_QUERIES = sorted(
    {name for corpus in (CORPUS, EDITED) for kind in ("def", "call", "value") for name in _names(corpus, kind)}
)


def _searched_values(impl: ModuleType, graph: object) -> list[tuple[str, str]]:
    """(file, NAME) of every value node the production search returns when values are requested."""
    return [
        (file, name)
        for query in LIFECYCLE_QUERIES
        for kind, file, name in impl.search(graph, query, include_values=True)
        if kind == "value"
    ]


def _graph_values(impl: ModuleType, graph: object) -> set[str]:
    """Names of the value nodes a graph exposes through the production search path."""
    return {name for _, name in _searched_values(impl, graph)}


# ── Oracles ───────────────────────────────────────────────────────────────────


def _same_resolution(left: object, right: object, fields: list[str]) -> bool:
    """Two resolver results agree, field by field, on *fields*."""
    if left is None or right is None:
        return left is None and right is None
    return all(getattr(left, f) == getattr(right, f) for f in fields)


def check_ordinary_calls(impl: ModuleType) -> bool:
    """AC-0003: base and implementation resolve every call name alike on base fields."""
    fields = [f.name for f in dataclasses.fields(BASE.Resolution)]
    base_graph, impl_graph = BASE.build(CORPUS), impl.build(CORPUS)
    return all(
        _same_resolution(
            BASE.resolve_call(base_graph, name), impl.resolve_call(impl_graph, name), fields
        )
        for name in sorted(_names(CORPUS, "call"))
    )


def check_ordinary_calls_tautological(impl: ModuleType) -> bool:
    """AC-0011: the same comparison with both sides resolved by the implementation."""
    fields = [f.name for f in dataclasses.fields(BASE.Resolution)]
    left, right = impl.build(CORPUS), impl.build(CORPUS)
    return all(
        _same_resolution(
            impl.resolve_call(left, name), impl.resolve_call(right, name), fields
        )
        for name in sorted(_names(CORPUS, "call"))
    )


def check_default_search(impl: ModuleType) -> bool:
    """AC-0004 default term: default search results equal the base's, per query."""
    base_graph, impl_graph = BASE.build(CORPUS), impl.build(CORPUS)
    return all(
        Counter(BASE.search(base_graph, q)) == Counter(impl.search(impl_graph, q))
        for q in QUERIES
    )


def check_explicit_search(impl: ModuleType) -> bool:
    """AC-0004 explicit term: base default result plus one entry per matching value line."""
    base_graph, impl_graph = BASE.build(CORPUS), impl.build(CORPUS)
    for q in QUERIES:
        expected = Counter(BASE.search(base_graph, q))
        expected.update(("value", file, name) for file, name in _lines(CORPUS, "value") if name == q)
        if Counter(impl.search(impl_graph, q, include_values=True)) != expected:
            return False
    return True


def semantic(graph: object) -> tuple[list[tuple[str, str, str]], list[tuple[tuple, tuple]]]:
    """A graph's nodes and edges as (kind, file, name) tuples, ignoring ids and order."""
    nodes = graph.nodes  # type: ignore[attr-defined]
    key = {i: (n.kind, n.file, n.name) for i, n in nodes.items()}
    edges = [(key[a], key[b]) for a, b in graph.edges]  # type: ignore[attr-defined]
    return sorted(key.values()), sorted(edges)


def check_equivalence(impl: ModuleType) -> bool:
    """AC-0005: full build equals build plus update, and the form sees one missing edge."""
    full = impl.build(EDITED)
    incremental = impl.build(CORPUS)
    incremental.update(EDIT_FILE, EDIT_TEXT)
    if semantic(full) != semantic(incremental):
        return False
    broken = impl.build(EDITED)
    broken.edges = set(sorted(broken.edges)[1:])
    return semantic(full) != semantic(broken)


def check_create(impl: ModuleType) -> bool:
    """AC-0006 create: a build holds exactly the corpus's value names."""
    return _graph_values(impl, impl.build(CORPUS)) == _names(CORPUS, "value")


def check_update(impl: ModuleType) -> bool:
    """AC-0006 update: after an edit the graph holds exactly the edited corpus's value names."""
    graph = impl.build(CORPUS)
    graph.update(EDIT_FILE, EDIT_TEXT)
    return _graph_values(impl, graph) == _names(EDITED, "value")


def check_delete(impl: ModuleType) -> bool:
    """AC-0006 delete: nothing names the removed file and the rest's value names remain."""
    graph = impl.build(CORPUS)
    graph.remove(REMOVED_FILE)
    remaining = {f: t for f, t in CORPUS.items() if f != REMOVED_FILE}
    if any(file == REMOVED_FILE for file, _ in _searched_values(impl, graph)):
        return False
    # Search cannot see edges, so dangling edges are read from the graph the removal returned.
    if any(a not in graph.nodes or b not in graph.nodes for a, b in graph.edges):
        return False
    return _graph_values(impl, graph) == _names(remaining, "value")


def check_rebuild(impl: ModuleType) -> bool:
    """AC-0006 rebuild: a rebuild holds exactly the current corpus's value names."""
    graph = impl.build(CORPUS)
    graph.update(EDIT_FILE, EDIT_TEXT)
    return _graph_values(impl, graph.rebuild()) == _names(EDITED, "value")


CONSUMER_SNIPPET = """
by_position = Resolution("t", "f.py")
by_keyword = Resolution(target="t", file="f.py")
if by_position != by_keyword:
    raise AssertionError("construction differs")
match by_position:
    case Resolution(target, file):
        if target != "t" or file != "f.py":
            raise AssertionError("destructured values differ")
    case _:
        raise AssertionError("pattern did not match")
"""


def check_compatibility(impl: ModuleType) -> bool:
    """AC-0007: a consumer using only base fields still builds and destructures the type."""
    code = compile(CONSUMER_SNIPPET, "<consumer>", "exec")
    try:
        exec(code, {"Resolution": impl.Resolution})  # noqa: S102
    except Exception:
        return False
    return True


def _budgeted(text: str) -> int:
    """Count of def and value lines in *text*."""
    return len(_lines({"f": text}, "def")) + len(_lines({"f": text}, "value"))


def check_bounded_work(impl: ModuleType) -> bool:
    """AC-0008: invalidated nodes do not exceed the def and value lines before plus after."""
    graph = impl.build(CORPUS)
    invalidated = len(graph.update(EDIT_FILE, EDIT_TEXT))
    return invalidated <= _budgeted(CORPUS[EDIT_FILE]) + _budgeted(EDIT_TEXT)


def check_feature(impl: ModuleType) -> bool:
    """AC-0012: a build holds a value node for each value line (existence only)."""
    graph = impl.build(CORPUS)
    held = Counter((n.file, n.name) for n in graph.nodes.values() if n.kind == "value")
    return held == Counter(_lines(CORPUS, "value"))


@dataclass(frozen=True)
class Oracle:
    """One term's oracle, its receipt shape, and its named mutation."""

    property_id: str
    term: str
    observation_type: str
    passing: str
    failing: str
    check: Callable[[ModuleType], bool]
    mutation: tuple[str, str]


def _o(
    prop: str,
    term: str,
    check: Callable[[ModuleType], bool],
    old: str,
    new: str,
    *,
    observation: str = "test-result",
    passing: str = "pass",
    failing: str = "fail",
) -> Oracle:
    return Oracle(prop, term, observation, passing, failing, check, (old, new))


P_CALLS = "ordinary-calls-resolve-to-no-values"
P_SEARCH = "default-search-excludes-values"
P_EQUIV = "full-incremental-semantic-equivalence"
P_BOUND = "one-file-edit-invalidation-bound"
P_LIFE = "values-created-updated-deleted-rebuilt"
P_COMPAT = "public-result-type-compatibility"

ORACLES: tuple[Oracle, ...] = (
    _o(
        P_CALLS,
        "differential-resolver",
        check_ordinary_calls,
        'if n.name == name and n.kind == "def"',
        "if n.name == name",
    ),
    _o(
        P_SEARCH,
        "default-query",
        check_default_search,
        "include_values: bool = False",
        "include_values: bool = True",
    ),
    _o(
        P_SEARCH,
        "explicit-query",
        check_explicit_search,
        'n.kind == "value" and n.name == query',
        'n.kind == "value"',
    ),
    _o(
        P_EQUIV,
        "equivalence-harness",
        check_equivalence,
        "self._relink({file}, affected)",
        "self._relink(set(), affected)",
    ),
    _o(
        P_BOUND,
        "invalidation-count",
        check_bounded_work,
        "return invalidated",
        "return set(self.nodes)",
        observation="command-result",
        passing="within-budget",
        failing="over-budget",
    ),
    _o(
        P_LIFE,
        "create",
        check_create,
        "return Graph(corpus).load(skip_values=False)",
        "return Graph(corpus).load(skip_values=True)",
    ),
    _o(
        P_LIFE,
        "update",
        check_update,
        "dropped = self._drop(file, ALL_KINDS)",
        "dropped = self._drop(file, CODE_KINDS)",
    ),
    _o(
        P_LIFE,
        "delete",
        check_delete,
        'self._drop(file, {"def", "call", "value"})',
        'self._drop(file, {"def", "call"})',
    ),
    _o(
        P_LIFE,
        "rebuild",
        check_rebuild,
        "return Graph(self.corpus).load(skip_values=False)",
        "return Graph(self.corpus).load(skip_values=True)",
    ),
    _o(
        P_COMPAT,
        "downstream-compile",
        check_compatibility,
        "synthetic: bool = False",
        "synthetic: bool",
        observation="command-result",
    ),
)
PROPERTY_IDS = list(dict.fromkeys(o.property_id for o in ORACLES))
ORACLE_IDS = [f"{o.property_id}:{o.term}" for o in ORACLES]
BY_PROPERTY: dict[str, list[Oracle]] = {
    p: [o for o in ORACLES if o.property_id == p] for p in PROPERTY_IDS
}
BOUNDED = next(o for o in ORACLES if o.term == "invalidation-count")
CREATE = next(o for o in ORACLES if o.term == "create")


# ── The producer ──────────────────────────────────────────────────────────────

_LOAD_COUNTER = itertools.count()


def fingerprint(source: str) -> str:
    """SHA-256 of the implementation-under-test source."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def mutant_source(oracle: Oracle, source: str = HEAD_SOURCE) -> str:
    """*source* with the oracle's named mutation applied."""
    old, new = oracle.mutation
    return source.replace(old, new)


def _run(check: Callable[[ModuleType], bool], source: str) -> bool:
    """Run *check* on the module *source* defines; any error is a failing run."""
    try:
        module = _load_source(f"core_work_loop_preservation_evidence_iut_{next(_LOAD_COUNTER)}", source)
        return bool(check(module))
    except Exception:
        return False


@cache
def _outcome(oracle: Oracle, source: str) -> str:
    """The producer's outcome for one oracle over one implementation source."""
    if not _run(oracle.check, source):
        return oracle.failing
    old, _ = oracle.mutation
    if old not in source:
        return "fail"
    if _run(oracle.check, mutant_source(oracle, source)):
        return "fail"
    return oracle.passing


def produce(oracle: Oracle, source: str) -> dict:
    """The evidence-receipt.v1 record the producer emits for *oracle* over *source*."""
    return {
        "schema_version": 1,
        "receipt_id": f"{oracle.property_id}:{oracle.term}",
        "acceptance_fingerprint": fingerprint(source),
        "lineage": {"criterion_ref": oracle.property_id},
        "selector": {"term": oracle.term},
        "freshness_mode": "exact-subject",
        "observation": {"type": oracle.observation_type},
        "outcome": _outcome(oracle, source),
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def receipts_for(property_id: str, source: str) -> list[dict]:
    """The producer's receipts for every term of one property."""
    return [produce(o, source) for o in BY_PROPERTY[property_id]]


def _property(property_id: str) -> dict:
    """The acceptance-property.v1 record for one of the six properties."""
    return {
        "schema_version": 1,
        "property_id": property_id,
        "spec_ref": "docs/specs/shared-substrate-change/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {
            "paths_or_artifacts": ["src/model/"],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [
            {
                "term": o.term,
                "observation_type": o.observation_type,
                "producer_class": "ci-runner",
                "outcomes": [o.passing],
            }
            for o in BY_PROPERTY[property_id]
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "supported-review-failure"},
        "policy_version": "v1",
    }


# ── Store helpers ─────────────────────────────────────────────────────────────

_LOGS = itertools.count()


def _null_sink(event: object) -> None:
    """Audit sink that accepts and drops every event."""


def _verdict(
    es: ModuleType,
    sc: ModuleType,
    acc: ModuleType,
    tmp_path: Path,
    property_id: str,
    receipts: list[dict],
    current_fp: str,
) -> dict:
    """Append *receipts* through the evidence store; return the store verdict for the property."""
    store = es.EvidenceStore(tmp_path / f"evidence-{next(_LOGS)}.log")
    store.open()
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    for index, receipt in enumerate(receipts):
        store.append_receipt(
            receipt,
            transaction_id=f"tx-{index:03d}",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    [verdict] = store.evaluate_verdicts(
        [_property(property_id)], current_fp, acc, adapter="sequential-reference"
    )
    return verdict


HEAD_FP = fingerprint(HEAD_SOURCE)
HEAD = _load_source("core_work_loop_preservation_evidence_head", HEAD_SOURCE)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0001: every property is supported over the head source
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("property_id", PROPERTY_IDS)
def test_head_receipts_support_each_property(
    property_id: str, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0001: the producer's head receipts give a supported store verdict."""
    assert acc.validate_property_dict(_property(property_id)) == (True, "ok")
    receipts = receipts_for(property_id, HEAD_SOURCE)
    for receipt in receipts:
        assert es.validate_receipt_dict(receipt) == (True, "ok")
        assert receipt["outcome"] == next(
            o.passing for o in ORACLES if o.term == receipt["selector"]["term"]
        )

    verdict = _verdict(es, sc, acc, tmp_path, property_id, receipts, HEAD_FP)

    assert verdict["verdict"] == "supported"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0002: each named mutant fails its oracle and leaves the property insufficient
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("oracle", ORACLES, ids=ORACLE_IDS)
def test_named_mutant_fails_its_oracle(
    oracle: Oracle, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0002: the oracle fails on its mutant and the property is insufficient."""
    mutant = mutant_source(oracle)
    assert mutant != HEAD_SOURCE
    assert oracle.check(HEAD)
    assert not _run(oracle.check, mutant)

    receipts = receipts_for(oracle.property_id, mutant)
    verdict = _verdict(es, sc, acc, tmp_path, oracle.property_id, receipts, fingerprint(mutant))

    assert verdict["verdict"] == "insufficient"


@pytest.mark.parametrize("oracle", ORACLES, ids=ORACLE_IDS)
def test_each_mutation_old_text_occurs_exactly_once(oracle: Oracle) -> None:
    """AC-0002: a named mutation's old text occurs exactly once in head.py."""
    assert HEAD_SOURCE.count(oracle.mutation[0]) == 1


@pytest.mark.parametrize("oracle", ORACLES, ids=ORACLE_IDS)
def test_each_named_mutant_loads(oracle: Oracle) -> None:
    """AC-0002: a mutant that cannot load would fail every oracle and prove nothing."""
    _load_source(f"core_work_loop_preservation_evidence_loads_{oracle.term}", mutant_source(oracle))


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0003 to AC-0008: each oracle
# ═══════════════════════════════════════════════════════════════════════════════


def test_ordinary_calls_compares_base_fields_only() -> None:
    """AC-0003: the new field is the only allowed delta and the oracle passes on head."""
    base_fields = [f.name for f in dataclasses.fields(BASE.Resolution)]
    head_fields = [f.name for f in dataclasses.fields(HEAD.Resolution)]
    assert head_fields[: len(base_fields)] == base_fields
    assert head_fields[len(base_fields) :] == ["synthetic"]
    assert check_ordinary_calls(HEAD)
    assert not _run(check_ordinary_calls, mutant_source(ORACLES[0]))


def test_default_and_explicit_search_terms_fail_independently() -> None:
    """AC-0004: each search term fails only on its own mutant."""
    default, explicit = ORACLES[1], ORACLES[2]
    assert default.term == "default-query" and explicit.term == "explicit-query"
    assert check_default_search(HEAD) and check_explicit_search(HEAD)
    default_mutant, explicit_mutant = mutant_source(default), mutant_source(explicit)
    assert not _run(check_default_search, default_mutant)
    assert _run(check_explicit_search, default_mutant)
    assert not _run(check_explicit_search, explicit_mutant)
    assert _run(check_default_search, explicit_mutant)


def test_search_compares_multisets_of_kind_file_name() -> None:
    """AC-0004: results are (kind, file, name) entries that keep multiplicity."""
    graph = HEAD.build({"x.py": "def n\ncall n\ncall n\nvalue n\n"})
    assert Counter(HEAD.search(graph, "n")) == Counter(
        [("def", "x.py", "n"), ("call", "x.py", "n"), ("call", "x.py", "n")]
    )
    assert len(HEAD.search(graph, "n", include_values=True)) == 4


def test_equivalence_form_ignores_ids_and_order_but_sees_one_edge() -> None:
    """AC-0005: the semantic form equates reordered builds and separates a one-edge difference."""
    reordered = HEAD.build(dict(reversed(list(EDITED.items()))))
    assert semantic(reordered) == semantic(HEAD.build(EDITED))
    assert set(reordered.nodes) != set(HEAD.build(EDITED).nodes)
    other = HEAD.build(EDITED)
    other.edges = set(sorted(other.edges)[1:])
    assert semantic(other) != semantic(HEAD.build(EDITED))
    assert check_equivalence(HEAD)


def test_lifecycle_terms_pass_on_head_and_read_names_from_text() -> None:
    """AC-0006: the four terms pass on head against value names read from corpus text."""
    assert _names(CORPUS, "value") == {"shared", "gamma", "extra"}
    assert _names(EDITED, "value") == {"shared", "delta", "extra"}
    for check in (check_create, check_update, check_delete, check_rebuild):
        assert check(HEAD), check.__name__


def test_compatibility_snippet_compiles_and_runs_against_head() -> None:
    """AC-0007: the consumer snippet compiles, runs, and uses only base fields."""
    compile(CONSUMER_SNIPPET, "<consumer>", "exec")
    base_fields = {f.name for f in dataclasses.fields(BASE.Resolution)}
    assert base_fields == {"target", "file"}
    assert check_compatibility(HEAD)
    assert check_compatibility(BASE)


def test_bounded_work_is_command_result_and_within_budget(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0008: head invalidates within the def-and-value bound; the receipt is command-result."""
    graph = HEAD.build(CORPUS)
    invalidated = len(graph.update(EDIT_FILE, EDIT_TEXT))
    bound = _budgeted(CORPUS[EDIT_FILE]) + _budgeted(EDIT_TEXT)
    assert bound == 5
    assert invalidated <= bound
    receipt = produce(BOUNDED, HEAD_SOURCE)
    assert receipt["observation"]["type"] == "command-result"
    assert receipt["outcome"] == "within-budget"


def test_bounded_work_mutant_emits_over_budget() -> None:
    """AC-0008: with the mutant as implementation under test, the producer emits over-budget."""
    mutant = mutant_source(BOUNDED)
    assert produce(BOUNDED, mutant)["outcome"] == "over-budget"
    graph = _load_source("core_work_loop_preservation_evidence_bound_mutant", mutant).build(CORPUS)
    assert len(graph.update(EDIT_FILE, EDIT_TEXT)) > 5


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0009 to AC-0012: incomplete evidence
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("property_id", PROPERTY_IDS)
def test_missing_receipts_are_insufficient(
    property_id: str, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0009: with its own receipts absent and every other property's present, insufficient."""
    others = [
        r for p in PROPERTY_IDS if p != property_id for r in receipts_for(p, HEAD_SOURCE)
    ]
    assert others

    verdict = _verdict(es, sc, acc, tmp_path, property_id, others, HEAD_FP)

    assert verdict["verdict"] == "insufficient"


@pytest.mark.parametrize("property_id", PROPERTY_IDS)
def test_stale_receipts_are_insufficient_against_the_subject(
    property_id: str, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0010: receipts over an earlier head are supported there and insufficient on head."""
    earlier = HEAD_SOURCE + "# behavior-neutral note\n"
    assert fingerprint(earlier) != HEAD_FP
    receipts = receipts_for(property_id, earlier)
    assert [r["outcome"] for r in receipts] == [o.passing for o in BY_PROPERTY[property_id]]

    against_earlier = _verdict(es, sc, acc, tmp_path, property_id, receipts, fingerprint(earlier))
    against_head = _verdict(es, sc, acc, tmp_path, property_id, receipts, HEAD_FP)

    assert against_earlier["verdict"] == "supported"
    assert against_head["verdict"] == "insufficient"


def test_tautological_oracle_is_caught_by_the_producer(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0011: resolving both sides with the implementation passes the mutant, so fail."""
    real = ORACLES[0]
    tautology = dataclasses.replace(real, check=check_ordinary_calls_tautological)
    assert _run(check_ordinary_calls_tautological, mutant_source(real))
    receipt = produce(tautology, HEAD_SOURCE)
    assert receipt["outcome"] == "fail"

    verdict = _verdict(es, sc, acc, tmp_path, real.property_id, [receipt], HEAD_FP)

    assert verdict["verdict"] == "insufficient"


def test_feature_only_evidence_earns_pass_only_for_create(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0012: the value-creation feature test passes the producer only for lifecycle create."""
    assert check_feature(HEAD)
    feature = {
        o: dataclasses.replace(o, check=check_feature) for o in ORACLES
    }
    for original, bound in feature.items():
        outcome = produce(bound, HEAD_SOURCE)["outcome"]
        expected = original.passing if original is CREATE else "fail"
        assert outcome == expected, original.term

    for property_id in PROPERTY_IDS:
        receipts = [produce(feature[o], HEAD_SOURCE) for o in BY_PROPERTY[property_id]]
        verdict = _verdict(es, sc, acc, tmp_path, property_id, receipts, HEAD_FP)
        assert verdict["verdict"] == "insufficient", property_id


def test_feature_test_passes_on_the_compatibility_mutant() -> None:
    """AC-0012: the feature test cannot see the compatibility break."""
    compat = next(o for o in ORACLES if o.property_id == P_COMPAT)
    assert _run(check_feature, mutant_source(compat))
    assert not _run(compat.check, mutant_source(compat))


# ═══════════════════════════════════════════════════════════════════════════════
# Fixture hygiene
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("source", [BASE_SOURCE, HEAD_SOURCE], ids=["base", "head"])
def test_fixture_modules_import_only_the_standard_library(source: str) -> None:
    """The fixture substrate imports nothing outside the standard library."""
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names)
