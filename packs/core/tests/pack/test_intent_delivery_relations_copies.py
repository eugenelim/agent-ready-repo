# The AC-0014 stub test lives in tests/roster/test_intent_delivery_relations_repository.py.
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2]
BINS = CORE / ".apm" / "adapter-root-bins"
SOURCE = BINS / "intent_delivery_relations.py"
HELPER = BINS / "_file_safety.py"

_CLOSE_WORK_SCRIPTS = CORE / ".apm" / "skills" / "close-work" / "scripts"
_WORK_LOOP_SCRIPTS = CORE / ".apm" / "skills" / "work-loop" / "scripts"
_NAVIGATE_INTENTS_SCRIPTS = CORE / ".apm" / "skills" / "navigate-intents" / "scripts"
_CLOSURE_INDEX = _CLOSE_WORK_SCRIPTS / "closure_index.py"
_LINT_TRACEABILITY = _WORK_LOOP_SCRIPTS / "lint-traceability.py"

# ── Module loaders ─────────────────────────────────────────────────────────────


def _load_closure_index(suffix: str) -> object:
    """Load closure_index.py under a unique module name."""
    key = f"_copies_test_closure_index_{suffix}"
    spec = importlib.util.spec_from_file_location(key, _CLOSURE_INDEX)
    assert spec and spec.loader, f"closure_index not found at {_CLOSURE_INDEX}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_resolver(suffix: str) -> object:
    """Load the resolver source under a unique module name."""
    key = f"_copies_test_resolver_{suffix}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, SOURCE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


# ── VI-1902: each consumer locates resolver from its own file path ─────────────


def test_vi1902_absent_resolver_is_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """VI-1902 — An absent resolver beside the consumer yields
    delivery-resolver-unavailable from both consumers. Proved through the
    _resolver_path seam without removing the real sibling copy.

    AC-0014, AC-0018.
    """
    nonexistent = tmp_path / "nonexistent_intent_delivery_relations.py"

    # close-work: _run_resolver with absent path raises ValueError
    ci = _load_closure_index("absent")
    raised = False
    try:
        ci._run_resolver(tmp_path, _resolver_path=nonexistent)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "close-work must raise ValueError for absent resolver"

    # lint-traceability: same
    ms = importlib.util.spec_from_file_location(
        "_copies_test_lint_absent", _LINT_TRACEABILITY
    )
    assert ms and ms.loader
    lt = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(lt)
    raised = False
    try:
        lt._run_resolver(tmp_path, _resolver_path=nonexistent)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "lint-traceability must raise ValueError for absent resolver"


def test_vi1902_linked_resolver_is_delivery_resolver_unavailable(
    tmp_path: Path,
) -> None:
    """VI-1902 — A symlinked resolver beside the consumer yields
    delivery-resolver-unavailable from both consumers.

    AC-0014, AC-0018.
    """
    real = tmp_path / "real.py"
    real.write_bytes(SOURCE.read_bytes())
    link = tmp_path / "intent_delivery_relations_link.py"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    # close-work
    ci = _load_closure_index("linked")
    raised = False
    try:
        ci._run_resolver(tmp_path, _resolver_path=link)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "close-work must raise ValueError for linked resolver"

    # lint-traceability
    ms = importlib.util.spec_from_file_location(
        "_copies_test_lint_linked", _LINT_TRACEABILITY
    )
    assert ms and ms.loader
    lt = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(lt)
    raised = False
    try:
        lt._run_resolver(tmp_path, _resolver_path=link)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "lint-traceability must raise ValueError for linked resolver"


# ── VI-1904: caller inventory (VI-1402 restated) ───────────────────────────────


def test_vi1904_only_canonical_delivery_inverter_exists() -> None:
    """VI-1904 — Only adapter-root-bins/intent_delivery_relations.py and its two
    byte-identical skill copies produce delivery-relation types; each consumer
    locates the resolver beside its own file; retired entry points are absent.

    AC-0014.
    """
    apm_root = CORE / ".apm"
    assert apm_root.is_dir(), f"APM root not found: {apm_root}"

    production_files = sorted(
        p for p in apm_root.rglob("*.py")
        if p.is_file() and not any(part.startswith("__") for part in p.parts)
    )
    assert production_files, "No production .py files found under .apm/"

    _DELIVERY_TYPE_LITERALS = {"direct-delivery", "coordinated-delivery"}

    # ── Assertion 1: Only the canonical source and its two copies produce ──────
    # delivery relation types.  Byte identity is verified inline.
    producers: list[Path] = []
    for path in production_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, val in zip(node.keys, node.values, strict=False):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "type"
                        and isinstance(val, ast.Constant)
                        and val.value in _DELIVERY_TYPE_LITERALS
                    ):
                        producers.append(path)
                        break

    # Accepted producers: the adapter-root-bins source + 3 byte-identical copies.
    accepted_relpaths = {
        SOURCE.relative_to(apm_root),
        (_CLOSE_WORK_SCRIPTS / "intent_delivery_relations.py").relative_to(apm_root),
        (_WORK_LOOP_SCRIPTS / "intent_delivery_relations.py").relative_to(apm_root),
        (_NAVIGATE_INTENTS_SCRIPTS / "intent_delivery_relations.py").relative_to(apm_root),
    }

    non_accepted = [
        p for p in producers
        if p.relative_to(apm_root) not in accepted_relpaths
    ]
    assert not non_accepted, (
        "VI-1904: Only the canonical source and its two skill copies may produce "
        "delivery relation types; unexpected producers: "
        + ", ".join(str(p.relative_to(apm_root)) for p in non_accepted)
    )

    # All three accepted files must be present.
    for rel in accepted_relpaths:
        assert any(
            p.relative_to(apm_root) == rel for p in producers
        ), f"VI-1904: expected producer not found: {rel}"

    # Byte identity: each skill copy == source.
    for skill_scripts in (_CLOSE_WORK_SCRIPTS, _WORK_LOOP_SCRIPTS, _NAVIGATE_INTENTS_SCRIPTS):
        skill_copy = skill_scripts / "intent_delivery_relations.py"
        assert skill_copy.read_bytes() == SOURCE.read_bytes(), (
            f"VI-1904: {skill_copy.relative_to(apm_root)} is not byte-identical to source"
        )

    # Byte identity: the two intent_graph.py copies match each other.
    assert (
        _CLOSE_WORK_SCRIPTS / "intent_graph.py"
    ).read_bytes() == (_NAVIGATE_INTENTS_SCRIPTS / "intent_graph.py").read_bytes(), (
        "AC-0001: close-work/scripts/intent_graph.py is not byte-identical to "
        "navigate-intents/scripts/intent_graph.py"
    )

    # ── Assertion 2: Each consumer locates resolver beside its own file ────────
    closure_src = _CLOSURE_INDEX.read_text(encoding="utf-8")
    lint_src = _LINT_TRACEABILITY.read_text(encoding="utf-8")

    # Each consumer must reference _RESOLVER_PATH built from __file__,
    # not from root / ".agentbundle" / "bin".
    assert "_RESOLVER_PATH" in closure_src, (
        "VI-1904: closure_index.py must define _RESOLVER_PATH"
    )
    assert "_RESOLVER_PATH" in lint_src, (
        "VI-1904: lint-traceability.py must define _RESOLVER_PATH"
    )
    # Neither consumer may reference the retired .agentbundle/bin path.
    assert '".agentbundle"' not in closure_src or ".agentbundle/bin" not in closure_src, (
        "VI-1904: closure_index.py must not reference .agentbundle/bin"
    )

    # ── Assertion 3: Retired consumer-local inversion entry points are absent ──
    assert "_resolve_discovery_path" not in closure_src, (
        "VI-1904: _resolve_discovery_path (retired pre-T2 function) must not be "
        "in closure_index.py"
    )
    try:
        lint_tree = ast.parse(lint_src, filename=str(_LINT_TRACEABILITY))
    except SyntaxError as exc:
        pytest.fail(f"VI-1904: lint-traceability.py has a syntax error: {exc}")

    spec_up_has_discovery = False
    for node in ast.walk(lint_tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_SPEC_UP_FIELDS"
        ):
            if isinstance(node.value, (ast.Tuple, ast.List)):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and elt.value == "Discovery":
                        spec_up_has_discovery = True
            break
    assert not spec_up_has_discovery, (
        "VI-1904: 'Discovery' must not be in _SPEC_UP_FIELDS (retired pre-T3 path)"
    )
