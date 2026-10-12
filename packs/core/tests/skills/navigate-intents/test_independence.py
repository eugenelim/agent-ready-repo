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
import json
import pathlib
import shutil
import sys

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


# Every operation and format, so AC-0035's "every query result" is what is
# compared, not one operation.
_ALL_QUERIES: tuple[tuple[str, ...], ...] = (
    ("--operation", "summary"),
    ("--operation", "record", "--id", "bravo-feat"),
    ("--operation", "tree"),
    ("--operation", "tree", "--format", "text"),
    ("--operation", "ancestors", "--id", "bravo-feat"),
    ("--operation", "search", "--selectors", '{"level": "feature"}'),
    ("--operation", "outstanding"),
    ("--operation", "outstanding", "--format", "text"),
)


def _serialised_results(root: pathlib.Path) -> list[bytes]:
    """Run every query on *root*; return each result as bytes with only generated_at removed."""
    out: list[bytes] = []
    for args in _ALL_QUERIES:
        result, code = nav.run_query(root, ["query", *args])  # type: ignore[union-attr]
        assert code == 0, f"{args} failed: {result}"
        if isinstance(result, dict):
            result = dict(result)
            result["provenance"] = {
                k: v for k, v in result["provenance"].items() if k != "generated_at"
            }
            out.append(json.dumps(result, separators=(",", ":")).encode("utf-8"))
        else:
            out.append(result.encode("utf-8"))
    return out


def test_workspace_toml_absent_present_unreadable_give_identical_results(
    tmp_path: pathlib.Path,
) -> None:
    """Every query result is byte-identical with workspace.toml absent, present, or unreadable (AC-0035).

    One root is changed in place, so provenance.root is the same in every run
    and only generated_at is removed before comparing.
    """
    import stat

    _skip_if_module_absent()
    corpus = tmp_path / "corpus"
    shutil.copytree(str(_FIXTURE_MIXED), str(corpus))
    absent = _serialised_results(corpus)

    ws_toml = corpus / "workspace.toml"
    ws_toml.write_text(
        '[workspace]\nname = "test-workspace"\n\n["ini-001".work]\nqueue = []\n',
        encoding="utf-8",
    )
    present = _serialised_results(corpus)

    ws_toml.chmod(0)
    try:
        unreadable = _serialised_results(corpus)
    finally:
        ws_toml.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert present == absent, "a present workspace.toml changed a query result"
    assert unreadable == absent, "an unreadable workspace.toml changed a query result"


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
