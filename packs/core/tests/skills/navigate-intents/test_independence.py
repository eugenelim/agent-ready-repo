"""Independence tests for the navigate-intents query module.

These tests prove that:
- The query result is independent of workspace.toml presence (AC-0035).
- The scripts directory imports only stdlib and co-located files (AC-0036).

They are frozen red in T1 (module absent) and turn green when T3 implements
navigate_intents.run_query().
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import shutil
import sys
import tempfile

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"

_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURE_MIXED = _HERE / "fixtures" / "mixed"

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

_IMPORT_ERROR: Exception | None = None


def _load_navigate_intents():
    module_path = _SCRIPTS / "navigate_intents.py"
    spec = importlib.util.spec_from_file_location(
        "core_navigate_intents_navigate_intents_ind", module_path
    )
    if spec is None or spec.loader is None:
        pytest.fail(f"navigate_intents.py not found at {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["core_navigate_intents_navigate_intents_ind"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


try:
    nav = _load_navigate_intents()
except Exception as exc:  # noqa: BLE001
    nav = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def _skip_if_module_absent() -> None:
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"navigate_intents.py not found at {_SCRIPTS / 'navigate_intents.py'} — "
            f"expected red in T1 (module absent): {_IMPORT_ERROR}"
        )


# ---------------------------------------------------------------------------
# Helper: strip nondeterministic fields before comparing results
# ---------------------------------------------------------------------------


def _stripped(result: dict) -> dict:  # type: ignore[type-arg]
    """Return result with generated_at and root stripped from provenance.

    root varies between temp-dir corpora and the fixture corpus.
    generated_at is time-dependent.
    """
    import copy
    r = copy.deepcopy(result)
    prov = r.get("provenance", {})
    prov.pop("generated_at", None)
    prov.pop("root", None)
    r["provenance"] = prov
    return r


# ---------------------------------------------------------------------------
# AC-0035: workspace.toml independence
# ---------------------------------------------------------------------------


def test_workspace_toml_absent_gives_same_result() -> None:
    """Result is identical whether workspace.toml is absent from the corpus (AC-0035)."""
    _skip_if_module_absent()
    # Run query on mixed/ (no workspace.toml there)
    result, code = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert code == 0
    assert result["status"] == "ok"


def test_workspace_toml_present_gives_same_result() -> None:
    """Result is identical when workspace.toml is present in the corpus (AC-0035)."""
    _skip_if_module_absent()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # Copy mixed/ into temp dir
        shutil.copytree(str(_FIXTURE_MIXED), str(tmp / "corpus"))
        corpus = tmp / "corpus"
        # Add a workspace.toml
        (corpus / "workspace.toml").write_text(
            '[workspace]\nname = "test-workspace"\n', encoding="utf-8"
        )
        result_with, code_with = nav.run_query(  # type: ignore[union-attr]
            corpus, ["query", "--operation", "summary"]
        )
        assert code_with == 0

    # Also run on original (no workspace.toml)
    result_without, code_without = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert code_without == 0
    # Both results must be structurally identical after stripping generated_at
    assert _stripped(result_with) == _stripped(result_without), (
        "Result must be identical whether workspace.toml is present or absent"
    )


def test_workspace_toml_unreadable_gives_same_result() -> None:
    """Result is identical when workspace.toml is unreadable (AC-0035)."""
    import stat
    _skip_if_module_absent()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        shutil.copytree(str(_FIXTURE_MIXED), str(tmp / "corpus"))
        corpus = tmp / "corpus"
        ws_toml = corpus / "workspace.toml"
        ws_toml.write_text('[workspace]\nname = "restricted"\n', encoding="utf-8")
        # Make it unreadable
        ws_toml.chmod(0)
        try:
            result_unreadable, code_u = nav.run_query(  # type: ignore[union-attr]
                corpus, ["query", "--operation", "summary"]
            )
        finally:
            # Restore permissions so tempdir cleanup works
            ws_toml.chmod(stat.S_IRUSR | stat.S_IWUSR)

    result_normal, code_n = nav.run_query(  # type: ignore[union-attr]
        _FIXTURE_MIXED, ["query", "--operation", "summary"]
    )
    assert code_u == 0
    assert code_n == 0
    assert _stripped(result_unreadable) == _stripped(result_normal), (
        "Result must be identical when workspace.toml is unreadable"
    )


# ---------------------------------------------------------------------------
# AC-0036: stdlib-only imports in scripts/
# ---------------------------------------------------------------------------


def _stdlib_module_names() -> frozenset[str]:
    """Return the set of stdlib top-level module names for the current Python."""
    import sys
    # sys.stdlib_module_names is available from Python 3.10+
    if hasattr(sys, "stdlib_module_names"):
        return frozenset(sys.stdlib_module_names)
    # Fallback: use a fixed set of commonly accepted stdlib modules
    return frozenset({
        "__future__", "_thread", "abc", "aifc", "argparse", "array", "ast",
        "asynchat", "asyncio", "asyncore", "atexit", "audioop", "base64",
        "bdb", "binascii", "binhex", "bisect", "builtins", "bz2", "calendar",
        "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs", "codeop",
        "colorsys", "compileall", "concurrent", "configparser", "contextlib",
        "contextvars", "copy", "copyreg", "cProfile", "csv", "ctypes",
        "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
        "dis", "distutils", "doctest", "email", "encodings", "enum",
        "errno", "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
        "fractions", "ftplib", "functools", "gc", "getopt", "getpass",
        "gettext", "glob", "grp", "gzip", "hashlib", "heapq", "hmac",
        "html", "http", "idlelib", "imaplib", "imghdr", "imp", "importlib",
        "inspect", "io", "ipaddress", "itertools", "json", "keyword",
        "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox",
        "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
        "multiprocessing", "netrc", "nis", "nntplib", "numbers", "operator",
        "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle",
        "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib",
        "posix", "posixpath", "pprint", "profile", "pstats", "pty", "pwd",
        "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random",
        "re", "readline", "reprlib", "resource", "rlcompleter", "runpy",
        "sched", "secrets", "select", "selectors", "shelve", "shlex",
        "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr",
        "socket", "socketserver", "spwd", "sqlite3", "sre_compile",
        "sre_constants", "sre_parse", "ssl", "stat", "statistics", "string",
        "stringprep", "struct", "subprocess", "sunau", "symtable", "sys",
        "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
        "termios", "test", "textwrap", "threading", "time", "timeit",
        "tkinter", "token", "tokenize", "tomllib", "trace", "traceback",
        "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
        "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
        "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
        "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib",
        "zoneinfo",
    })


def _colocated_names(scripts_dir: pathlib.Path) -> frozenset[str]:
    """Return the stem names of co-located .py files."""
    return frozenset(p.stem for p in scripts_dir.glob("*.py"))


def _collect_imports(source: str) -> list[str]:
    """Return a list of top-level module names imported in source."""
    tree = ast.parse(source)
    tops = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tops.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            tops.append(node.module.split(".")[0])
    return tops


def test_scripts_import_only_stdlib_and_colocated() -> None:
    """Every .py in scripts/ imports only stdlib or co-located modules (AC-0036)."""
    stdlib = _stdlib_module_names()
    colocated = _colocated_names(_SCRIPTS)
    allowed = stdlib | colocated

    violations: list[str] = []
    for py_file in sorted(_SCRIPTS.glob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        for mod_name in _collect_imports(source):
            if mod_name not in allowed:
                violations.append(f"{py_file.name}: imports {mod_name!r}")

    assert not violations, (
        "scripts/ must only import stdlib or co-located modules:\n"
        + "\n".join(violations)
    )
