"""Tests for area inference — T3 (TDD, red phase written first).

Verification mode: TDD.
Spec:  docs/specs/spec-retirement-eligibility/spec.md  § Area attribution
Plan:  docs/specs/spec-retirement-eligibility/plan.md  § T3

Four cases from the plan task body:
1. A non-packs top-level namespace is inferred and a spec naming it is
   attributed to it (portability criterion).
2. A spec matching no inferred namespace is attributed "unscoped", never blank.
3. Two calls over the same tracked file list return equal results (determinism).
4. No spec that names an inferred namespace is left unattributed.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_RETIREMENT_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_retirement.py"
)


def _load_retirement():
    """Load workspace_status_retirement under a unique module name."""
    module_name = "workspace_status_retirement_t3"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _RETIREMENT_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_RETIREMENT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Case 1: portability — a non-packs top-level namespace is inferred and matched
# ---------------------------------------------------------------------------

def test_non_packs_namespace_is_attributed() -> None:
    """A spec naming a top-level directory that is not 'packs' is attributed to it.

    Spec § Area attribution:
    "In a fixture whose only top-level source directory is named something
    other than 'packs', a spec whose body names that directory is attributed
    to it."
    """
    mod = _load_retirement()
    # Only source directory in the tracked list is "widgets"; docs is also tracked
    # but is not a "source" namespace (or rather: it IS tracked, so inference
    # includes it; the spec body explicitly names "widgets/" to match).
    tracked = [
        "widgets/foo/bar.py",
        "widgets/baz.py",
        "docs/specs/myspec/spec.md",
    ]
    namespaces = mod.infer_namespaces(tracked)
    # Spec body mentions the widgets namespace by path
    spec_text = (
        "This spec covers work in widgets/foo and widgets/baz.\n"
        "See widgets/ for the implementation directory.\n"
    )
    area = mod.attribute_spec(spec_text, namespaces)
    assert area == "widgets", (
        f"Expected 'widgets', got {area!r}. "
        "A spec naming a top-level source directory must be attributed to it."
    )


# ---------------------------------------------------------------------------
# Case 2: unmatched spec → "unscoped", never blank
# ---------------------------------------------------------------------------

def test_unmatched_spec_is_unscoped() -> None:
    """A spec matching no inferred namespace is attributed 'unscoped', never blank.

    Spec § Area attribution:
    "A candidate matching no inferred namespace is attributed 'unscoped'."
    """
    mod = _load_retirement()
    tracked = ["widgets/foo/bar.py", "docs/specs/myspec/spec.md"]
    namespaces = mod.infer_namespaces(tracked)
    # Spec body contains no mention of any tracked namespace directory
    spec_text = (
        "This spec covers some unrelated work. "
        "No namespace is mentioned here by path.\n"
    )
    area = mod.attribute_spec(spec_text, namespaces)
    assert area == "unscoped", (
        f"Expected 'unscoped', got {area!r}. "
        "A spec with no namespace match must be attributed 'unscoped'."
    )
    assert area != "", "Attribution must never be blank; 'unscoped' is required."


# ---------------------------------------------------------------------------
# Case 3: determinism — two calls over the same tracked file list return equal
# ---------------------------------------------------------------------------

def test_infer_namespaces_is_deterministic() -> None:
    """Two calls over the same tracked file list return equal results.

    Plan T3: "Two calls over an unchanged tracked file list return equal results."
    Testing Strategy § Area attribution:
    "Inference is a pure function of the tracked file list; two calls over
    the same list return equal results."
    """
    mod = _load_retirement()
    tracked = [
        "packs/core/foo.py",
        "docs/specs/myspec/spec.md",
        "tools/helper.py",
        "tests/roster/test_foo.py",
    ]
    result1 = mod.infer_namespaces(tracked)
    result2 = mod.infer_namespaces(tracked)
    assert result1 == result2, (
        "infer_namespaces must be deterministic: "
        f"first call returned {result1!r}, second call returned {result2!r}."
    )


# ---------------------------------------------------------------------------
# Case 4: no spec naming an inferred namespace is left unattributed
# ---------------------------------------------------------------------------

def test_spec_naming_namespace_is_not_unscoped() -> None:
    """No spec that names an inferred namespace is left unattributed.

    Plan T3: "No spec that names an inferred namespace is left unattributed."
    """
    mod = _load_retirement()
    # A namespace "agents" is present in tracked files
    tracked = ["agents/foo/bar.py", "agents/baz.py"]
    namespaces = mod.infer_namespaces(tracked)
    # The spec body explicitly names the "agents" namespace as a path prefix
    spec_text = "See agents/foo for the implementation.\n"
    area = mod.attribute_spec(spec_text, namespaces)
    assert area != "unscoped", (
        "Got 'unscoped' but spec body names the 'agents' namespace. "
        "A spec naming an inferred namespace must be attributed, not left unscoped."
    )
    assert area == "agents", (
        f"Expected 'agents', got {area!r}. "
        "The attributed namespace must match the one named in the spec body."
    )
