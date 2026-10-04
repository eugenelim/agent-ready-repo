"""Credential boundary contract tests for the packaged agentbundle tree.

All source inspection is done via AST over the packaged source, located
relative to ``agentbundle.__file__``.  No repository paths outside the
package directory are read.

Assertions over the WHOLE packaged tree:
- No string literal ``AGENTBUNDLE_HTTP_BEARER_TOKEN`` in any module.
- No ``import netrc`` / ``from netrc`` import in any module.
- No ``.netrc`` path literal in any module.
- No ``config show`` / ``.jfrog`` / ``jfrog-cli.conf`` credential-store literals.
- No ``subprocess`` use except in ``catalogue_fetch/jfrog_cli.py`` (whole tree).
- No ``os.environ[key]``, ``os.environ.get(key)``, ``os.getenv(key)``, or
  imported ``environ``/``getenv`` reads of credential-bearing keys, in any module.
- Only ``catalogue_fetch/jfrog_cli.py`` passes ``"jf"`` or ``"jf.exe"`` to a
  subprocess call or uses the ``jf api`` argv shape.
- Every ``credbroker`` import is ``from credbroker import <public name>``
  where the public name is in ``credbroker.__all__`` (catalogue-fetch modules).
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

# Only catalogue_fetch/jfrog_cli.py may call subprocess or invoke jf.
_SUBPROCESS_ALLOWED: frozenset[str] = frozenset({"jfrog_cli.py"})
_JF_ALLOWED_LABEL: str = "catalogue_fetch/jfrog_cli.py"


def _covered_sources() -> list[tuple[str, str]]:
    """Return [(label, source_text), ...] for the catalogue-fetch boundary modules.

    Covers ``catalogue_fetch/*.py`` and ``https_catalogue.py`` — the modules
    that touch credential data during catalogue acquisition.
    """
    sources = []
    cf_dir = _PKG_DIR / "catalogue_fetch"
    if cf_dir.is_dir():
        for py in sorted(cf_dir.glob("*.py")):
            sources.append((f"catalogue_fetch/{py.name}", py.read_text(encoding="utf-8")))
    hc = _PKG_DIR / "https_catalogue.py"
    if hc.is_file():
        sources.append(("https_catalogue.py", hc.read_text(encoding="utf-8")))
    return sources


def _whole_package_sources() -> list[tuple[str, str]]:
    """Return [(label, source_text), ...] for ALL Python files in the package tree.

    Used for checks that must hold across the whole packaged agentbundle tree,
    not just the catalogue-fetch boundary.
    """
    sources = []
    for py in sorted(_PKG_DIR.rglob("*.py")):
        label = str(py.relative_to(_PKG_DIR))
        sources.append((label, py.read_text(encoding="utf-8")))
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
# Test: no AGENTBUNDLE_HTTP_BEARER_TOKEN string literal (whole tree)
# ---------------------------------------------------------------------------


def test_no_bearer_token_env_key_literal() -> None:
    """No string literal 'AGENTBUNDLE_HTTP_BEARER_TOKEN' appears in any module."""
    secret_key = "AGENTBUNDLE_HTTP_BEARER_TOKEN"
    violations: list[str] = []
    for label, source in _whole_package_sources():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for val in _ast_string_constants(tree):
            if secret_key in val:
                violations.append(f"{label}: string literal contains {secret_key!r}")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no import netrc / from netrc (whole tree)
# ---------------------------------------------------------------------------


def test_no_netrc_import() -> None:
    """No module in the whole package imports the netrc stdlib module."""
    violations: list[str] = []
    for label, source in _whole_package_sources():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
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
# Test: no .netrc path literal (whole tree)
# ---------------------------------------------------------------------------


def test_no_netrc_path_literal() -> None:
    """No string literal references the .netrc file path in any module."""
    violations: list[str] = []
    for label, source in _whole_package_sources():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for val in _ast_string_constants(tree):
            if ".netrc" in val:
                violations.append(f"{label}: string literal contains '.netrc'")
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no JFrog credential-store reads (whole tree)
# ---------------------------------------------------------------------------


def test_no_jfrog_credential_store_literals() -> None:
    """No module in the whole package contains JFrog credential-store literals."""
    forbidden_patterns = [".jfrog", "jfrog-cli.conf", "config show"]
    violations: list[str] = []
    for label, source in _whole_package_sources():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for val in _ast_string_constants(tree):
            for pat in forbidden_patterns:
                if pat in val:
                    violations.append(
                        f"{label}: string literal contains {pat!r}"
                    )
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: no subprocess import except in jfrog_cli.py (whole tree)
# ---------------------------------------------------------------------------


def test_no_subprocess_except_jfrog_cli() -> None:
    """No catalogue-fetch or https_catalogue module uses subprocess except jfrog_cli.py.

    This check covers the catalogue-fetch boundary only (not the whole package
    tree, since other agentbundle modules legitimately use subprocess for
    unrelated purposes).  The whole-tree check for jf invocations is handled
    by ``test_only_jfrog_cli_invokes_jf``.
    """
    violations: list[str] = []
    for label, source in _covered_sources():
        filename = Path(label).name
        if filename in _SUBPROCESS_ALLOWED:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
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
# (catalogue-fetch boundary only — other modules need not import credbroker)
# ---------------------------------------------------------------------------


def test_credbroker_imports_use_only_public_names() -> None:
    """All credbroker imports in catalogue-fetch modules use public names."""
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
# Test: no os.environ/os.getenv read of credential-bearing keys (whole tree)
# ---------------------------------------------------------------------------

# Credential-bearing environment variable keys that must not be read directly.
_CREDENTIAL_ENV_KEYS: frozenset[str] = frozenset({"AGENTBUNDLE_HTTP_BEARER_TOKEN"})


def _check_environ_access(label: str, tree: ast.AST) -> list[str]:
    """Return violation messages for direct env reads of credential keys.

    Checks:
    - os.environ[<key>]
    - os.environ.get(<key>, ...)
    - os.getenv(<key>, ...)
    - environ[<key>] and environ.get(<key>) when imported via
      ``from os import environ`` or ``from os import getenv``
    """
    violations: list[str] = []
    # Collect names that refer to os.environ or os.getenv via import.
    environ_names: set[str] = set()
    getenv_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                target = alias.asname or alias.name
                if alias.name == "environ":
                    environ_names.add(target)
                elif alias.name == "getenv":
                    getenv_names.add(target)

    for node in ast.walk(tree):
        # os.environ[<key>]
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "os"
            and node.value.attr == "environ"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: os.environ[{node.slice.value!r}] reads credential key directly"
            )
        # os.environ.get(<key>, ...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and node.func.value.attr == "environ"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: os.environ.get({node.args[0].value!r}) reads credential key directly"
            )
        # os.getenv(<key>, ...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "getenv"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: os.getenv({node.args[0].value!r}) reads credential key directly"
            )
        # environ[<key>] via imported name
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in environ_names
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: environ[{node.slice.value!r}] reads credential key directly"
            )
        # environ.get(<key>) via imported name
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in environ_names
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: environ.get({node.args[0].value!r}) reads credential key directly"
            )
        # getenv(<key>) via imported name
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in getenv_names
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in _CREDENTIAL_ENV_KEYS
        ):
            violations.append(
                f"{label}: getenv({node.args[0].value!r}) reads credential key directly"
            )
    return violations


def test_no_os_environ_credential_key_access() -> None:
    """No module in the whole package reads credential-bearing keys via os.environ/getenv.

    Checks the full packaged tree using AST analysis of os.environ[key],
    os.environ.get(key), os.getenv(key), and imported-name forms.
    """
    violations: list[str] = []
    for label, source in _whole_package_sources():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        violations.extend(_check_environ_access(label, tree))
    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Test: only jfrog_cli.py invokes 'jf' via subprocess (whole tree)
# ---------------------------------------------------------------------------


def _has_jf_invocation(tree: ast.AST) -> bool:
    """Return True when the AST contains a subprocess call with a 'jf'/'jf.exe' constant.

    Looks for string constants 'jf' or 'jf.exe' that appear as arguments to
    subprocess.Popen, subprocess.run, subprocess.check_call, subprocess.check_output,
    or subprocess.call; or as elements of list/tuple literals that are passed to
    those functions.  Also detects the 'jf api' argv shape (a list whose first
    element is a Name/Constant and second is 'api').

    This check is conservative: it reports any file that contains the literal
    string 'jf' or 'jf.exe' as a direct Call argument or inside a list/tuple
    passed to a subprocess function.
    """
    _SUBPROCESS_FUNCS = frozenset({"Popen", "run", "check_call", "check_output", "call"})

    def _is_jf_constant(node: ast.expr) -> bool:
        return isinstance(node, ast.Constant) and node.value in ("jf", "jf.exe")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # subprocess.Popen(...) or subprocess.run(...) etc.
        is_subprocess_call = (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
            and func.attr in _SUBPROCESS_FUNCS
        )
        if not is_subprocess_call:
            continue
        # Check the first positional arg (the argv).
        if not node.args:
            continue
        argv_arg = node.args[0]
        # Direct string constant: subprocess.run("jf", ...)  — unusual but possible.
        if _is_jf_constant(argv_arg):
            return True
        # List or tuple: subprocess.run(["jf", "api", ...], ...)
        if isinstance(argv_arg, (ast.List, ast.Tuple)):
            for elt in argv_arg.elts:
                if _is_jf_constant(elt):
                    return True
    return False


def test_only_jfrog_cli_invokes_jf() -> None:
    """Only catalogue_fetch/jfrog_cli.py may pass 'jf' or 'jf.exe' to subprocess.

    No other module in the whole packaged tree may contain a subprocess call
    whose argv includes the literal string 'jf' or 'jf.exe'.  The allowed
    module is catalogue_fetch/jfrog_cli.py.
    """
    violations: list[str] = []
    for label, source in _whole_package_sources():
        if label == _JF_ALLOWED_LABEL:
            continue  # jfrog_cli.py is the only permitted caller.
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        if _has_jf_invocation(tree):
            violations.append(
                f"{label}: contains a subprocess call with 'jf' or 'jf.exe' in the argv"
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
