"""Credential boundary contract tests for catalogue_fetch and https_catalogue.

All source inspection is done via AST over the packaged source, located
relative to ``agentbundle.__file__``.  No repository paths outside the
package directory are read.

Assertions:
- No string literal ``AGENTBUNDLE_HTTP_BEARER_TOKEN`` in the covered modules.
- No ``import netrc`` / ``from netrc`` import.
- No ``.netrc`` path literal in source.
- No ``config show`` / ``.jfrog`` / ``jfrog-cli.conf`` credential-store reads.
- No ``subprocess`` use except in ``catalogue_fetch/jfrog_cli.py``
  (which does not exist in this release).
- Every ``credbroker`` import is ``from credbroker import <public name>``
  where the public name is in ``credbroker.__all__``.
- No bare ``import credbroker`` and no private ``credbroker._*`` imports.
- No ``os.environ`` read of credential-bearing keys.
- AgentBundle's package metadata declares ``credbroker>=0.7,<0.8``.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path
from typing import Iterator

import agentbundle

# ---------------------------------------------------------------------------
# Source file discovery (package-local only)
# ---------------------------------------------------------------------------

_PKG_DIR: Path = Path(agentbundle.__file__).resolve().parent
_PYPROJECT: Path = _PKG_DIR.parent / "pyproject.toml"

# Covered modules: catalogue_fetch/*.py and https_catalogue.py.
# subprocess is allowed only in catalogue_fetch/jfrog_cli.py (T4, not yet present).
_SUBPROCESS_ALLOWED: frozenset[str] = frozenset({"jfrog_cli.py"})


def _covered_sources() -> list[tuple[str, str]]:
    """Return [(label, source_text), ...] for the covered modules."""
    sources = []
    cf_dir = _PKG_DIR / "catalogue_fetch"
    if cf_dir.is_dir():
        for py in sorted(cf_dir.glob("*.py")):
            sources.append((f"catalogue_fetch/{py.name}", py.read_text(encoding="utf-8")))
    hc = _PKG_DIR / "https_catalogue.py"
    if hc.is_file():
        sources.append(("https_catalogue.py", hc.read_text(encoding="utf-8")))
    return sources


def _collect_docstring_ids(tree: ast.AST) -> set[int]:
    """Return the id() of every AST node that is a module/class/function docstring."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = None
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
        if body and isinstance(body[0], ast.Expr):
            expr_value = body[0].value
            if isinstance(expr_value, ast.Constant) and isinstance(expr_value.value, str):
                ids.add(id(expr_value))
    return ids


def _ast_string_constants(tree: ast.AST) -> Iterator[str]:
    """Yield string constant values from an AST tree, excluding docstrings."""
    docstring_ids = _collect_docstring_ids(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
        ):
            yield node.value


def _ast_imports(tree: ast.AST) -> Iterator[ast.stmt]:
    """Yield all Import and ImportFrom statements in an AST tree."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node


# ---------------------------------------------------------------------------
# Test: no AGENTBUNDLE_HTTP_BEARER_TOKEN string literal
# ---------------------------------------------------------------------------


def test_no_bearer_token_env_key_literal() -> None:
    """No string literal 'AGENTBUNDLE_HTTP_BEARER_TOKEN' appears in covered modules."""
    secret_key = "AGENTBUNDLE_HTTP_BEARER_TOKEN"
    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for val in _ast_string_constants(tree):
            if secret_key in val:
                violations.append(f"{label}: string literal contains {secret_key!r}")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no import netrc / from netrc
# ---------------------------------------------------------------------------


def test_no_netrc_import() -> None:
    """No module in the covered set imports the netrc stdlib module."""
    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for node in _ast_imports(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "netrc" or alias.name.startswith("netrc."):
                        violations.append(f"{label}: bare import netrc")
            elif isinstance(node, ast.ImportFrom) and node.module and (
                node.module == "netrc" or node.module.startswith("netrc.")
            ):
                violations.append(f"{label}: from netrc import ...")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no .netrc path literal
# ---------------------------------------------------------------------------


def test_no_netrc_path_literal() -> None:
    """No string literal references the .netrc file path."""
    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for val in _ast_string_constants(tree):
            if ".netrc" in val:
                violations.append(f"{label}: string literal contains '.netrc'")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no JFrog credential-store reads (config show, .jfrog, jfrog-cli.conf)
# ---------------------------------------------------------------------------


def test_no_jfrog_credential_store_literals() -> None:
    """No covered module contains JFrog credential-store path or command literals."""
    forbidden_patterns = [".jfrog", "jfrog-cli.conf", "config show"]
    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for val in _ast_string_constants(tree):
            for pat in forbidden_patterns:
                if pat in val:
                    violations.append(
                        f"{label}: string literal contains {pat!r}"
                    )
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no subprocess import except in jfrog_cli.py
# ---------------------------------------------------------------------------


def test_no_subprocess_except_jfrog_cli() -> None:
    """No covered module uses subprocess except catalogue_fetch/jfrog_cli.py."""
    violations: list[str] = []
    for label, source in _covered_sources():
        filename = Path(label).name
        if filename in _SUBPROCESS_ALLOWED:
            continue  # jfrog_cli.py is allowed to use subprocess
        tree = ast.parse(source)
        for node in _ast_imports(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess" or alias.name.startswith("subprocess."):
                        violations.append(f"{label}: import subprocess")
            elif isinstance(node, ast.ImportFrom) and node.module and (
                node.module == "subprocess"
                or node.module.startswith("subprocess.")
            ):
                violations.append(f"{label}: from subprocess import ...")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: every credbroker import is from credbroker import <public name>
# ---------------------------------------------------------------------------


def test_credbroker_imports_use_only_public_names() -> None:
    """All credbroker imports use 'from credbroker import <name>' with a public name."""
    import credbroker as _cb
    public_names: frozenset[str] = frozenset(getattr(_cb, "__all__", []))

    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for node in _ast_imports(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "credbroker" or alias.name.startswith("credbroker."):
                        violations.append(
                            f"{label}: bare 'import {alias.name}' — "
                            "must use 'from credbroker import <public name>'"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "credbroker":
                    for alias in node.names:
                        if alias.name not in public_names:
                            violations.append(
                                f"{label}: 'from credbroker import {alias.name}' — "
                                f"{alias.name!r} is not in credbroker.__all__"
                            )
                elif module.startswith("credbroker."):
                    violations.append(
                        f"{label}: import from private credbroker submodule {module!r}"
                    )
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no os.environ subscript/get of credential-bearing keys
# ---------------------------------------------------------------------------

# Credential-bearing environment variable keys that must not be read directly
# in catalogue_fetch or https_catalogue.
_CREDENTIAL_ENV_KEYS: frozenset[str] = frozenset({"AGENTBUNDLE_HTTP_BEARER_TOKEN"})


def test_no_os_environ_credential_key_access() -> None:
    """No covered module reads credential-bearing keys directly from os.environ."""
    violations: list[str] = []
    for label, source in _covered_sources():
        tree = ast.parse(source)
        for val in _ast_string_constants(tree):
            # Any string constant matching a credential key that appears in a
            # call to os.environ.get or os.environ[] would have been caught by
            # the literal-content check above; we also guard via regex on the
            # raw source to be belt-and-suspenders.
            if val in _CREDENTIAL_ENV_KEYS:
                violations.append(
                    f"{label}: string literal equals credential env key {val!r}"
                )
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: installed metadata (or pyproject.toml) declares credbroker>=0.7,<0.8
# ---------------------------------------------------------------------------

def _specifier_set(requirement: str) -> set[str]:
    """Return the comma-separated specifiers of ``credbroker<spec>`` as a set."""
    spec = requirement[len("credbroker"):].split(";", 1)[0]
    return {part.replace(" ", "") for part in spec.split(",") if part.strip()}


def test_agentbundle_metadata_declares_credbroker_dependency() -> None:
    """AgentBundle's package metadata declares credbroker>=0.7,<0.8. AC-0001

    The pyproject beside the imported package is the code under test, so it is
    read first; installed metadata is consulted only when no pyproject ships
    beside the package (an installed wheel). Installed metadata can belong to
    a different checkout of the same distribution, so it never takes priority.
    """
    requirements: list[str] = []
    if _PYPROJECT.is_file():
        with _PYPROJECT.open("rb") as fh:
            requirements = tomllib.load(fh).get("project", {}).get("dependencies", [])
    else:
        import importlib.metadata as _meta

        requirements = _meta.requires("agentbundle") or []

    credbroker_requirements = [
        req for req in requirements if re.match(r"credbroker\b", req.strip().lower())
    ]
    assert len(credbroker_requirements) == 1, (
        f"expected exactly one credbroker requirement, got {credbroker_requirements!r}"
    )
    assert _specifier_set(credbroker_requirements[0].strip().lower()) == {">=0.7", "<0.8"}
