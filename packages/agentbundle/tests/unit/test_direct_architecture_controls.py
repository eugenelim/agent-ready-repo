"""AC17/AC39 architecture-regression controls over AgentBundle's direct modules.

These are static controls on *our own* source, not scans of publisher payloads.
Each family is expressed as a checker over a source string so that every rule
can be paired with a mutation fixture: a rule with no fixture that kills it is a
control that cannot fail, and this file exists to make that impossible.
"""

from __future__ import annotations

import ast
from pathlib import Path

import agentbundle.bounded_metadata as bounded_metadata
import agentbundle.direct_install as direct_install
import agentbundle.direct_source as direct_source
import agentbundle.direct_source_acquisition as direct_source_acquisition
import agentbundle.direct_source_state as direct_source_state
import agentbundle.direct_validate as direct_validate
import pytest

# Every module on the direct route, not the three the control happened to pass
# on. `direct_source_state` is named by the LLD; `direct_install` and
# `direct_validate` are direct modules this spec added. Scoping the control to
# the modules that satisfy it is how it stayed green while `direct_install`
# canonicalised a path with `.resolve()` — a spelling AC39 exists to ban.
DIRECT_MODULES = (
    direct_source,
    direct_source_acquisition,
    direct_source_state,
    direct_install,
    direct_validate,
    bounded_metadata,
)

# AC17's explicit execution-name set. Written out rather than derived, because a
# derivation over `dir(os)` silently tracks whatever the running interpreter
# happens to expose and would quietly shrink on a platform missing a name.
OS_EXECUTION_NAMES = frozenset(
    {
        "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp",
        "execvpe", "fork", "forkpty", "posix_spawn", "posix_spawnp",
        "startfile", "system", "popen",
    }
)
BANNED_BUILTINS = frozenset({"exec", "eval", "compile", "__import__"})
# `realpath` and `abspath` are named because they are the spellings that defeat
# AC39's caller-side-canonicalization rule while passing a ban written only
# against `resolve`.
BANNED_PATH_OBSERVERS = frozenset(
    {"lstat", "stat", "fstat", "resolve", "realpath", "abspath", "readlink"}
)
# AC34's single carve-out, as a (module filename, function name) pair.
PROBE_CARVE_OUT = ("direct_source.py", "probe_measured_path")
# AC39's four *named callable* mechanisms. Mechanism (3), AC6's library-resolved
# per-member destination and linkname check, is an extraction seam rather than
# an allowlistable call and is exempt by name.
CONFINEMENT_CALLS = frozenset(
    {
        "validate_confined_directory",
        "read_confined_regular_file",
        "write_jailed",
        "probe_measured_path",
        # The traversal form of mechanism (1); it validates the directory it
        # walks through the same helper.
        "walk_confined_regular_files",
        "list_confined_regular_files",
    }
)
BANNED_PREFIX_HELPERS = frozenset({"commonpath", "commonprefix", "normpath"})


def _enclosing_functions(tree: ast.AST) -> dict[int, str]:
    """Map each line to the nearest enclosing function name."""

    owner: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for inner in ast.walk(node):
                line = getattr(inner, "lineno", None)
                if line is not None and line not in owner:
                    owner[line] = node.name
    return owner


def _module_names(tree: ast.AST) -> set[str]:
    """Names bound by a plain `import X`, which are module references.

    AC17 bans `stat` as an *observation* — `path.stat()` — not as a module.
    A module-level `import stat` is explicitly admitted and outside the
    carve-out's scope, because AC34 needs `stat.S_ISDIR`/`S_ISLNK` for the
    wrong-type-for-its-kind refusal. Without this distinction the control
    reports the very spelling the criteria require.
    """

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _is_path_expression(node: ast.AST) -> bool:
    """True when *node* is path-shaped, so a `startswith` on it is a jail check.

    The ban has to be narrowed this way: a bare-name ban is undecidable here and
    would equally flag AC13's `sha256-1:` digest-prefix refusal and AC3's
    `git+https` source grammar, both of which live in these same modules.
    """

    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in {"str", "Path", "PurePosixPath"}:
            return True
        # `os.fspath(x)`, and `<expr>.as_posix()` — `file_safety.py` itself
        # spells `path.relative_to(root).as_posix()` ten times, so this is the
        # form a direct module would most naturally reach for.
        if isinstance(func, ast.Attribute) and func.attr in {"fspath", "as_posix"}:
            return True
    if isinstance(node, ast.JoinedStr):
        return any(
            isinstance(value, ast.FormattedValue) for value in node.values
        )
    if isinstance(node, ast.Name) and "path" in node.id.lower():
        return True
    return isinstance(node, ast.Attribute) and "path" in node.attr.lower()


def direct_module_findings(source: str, filename: str) -> list[str]:
    """Return every architecture-control violation in *source*."""

    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    modules = _module_names(tree)
    findings: list[str] = []

    def report(node: ast.AST, rule: str) -> None:
        findings.append(f"{filename}:{getattr(node, 'lineno', 0)}: {rule}")

    for node in ast.walk(tree):
        # --- execution surface -------------------------------------------
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in {"subprocess", "runpy"}:
                    report(node, f"import of {alias.name}")
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in {"subprocess", "runpy"}:
                report(node, f"import from {node.module}")
            if root == "os":
                for alias in node.names:
                    if alias.name in OS_EXECUTION_NAMES:
                        report(node, f"from os import {alias.name}")
        if isinstance(node, ast.Attribute):
            if node.attr in OS_EXECUTION_NAMES or node.attr.startswith("spawn"):
                report(node, f"os execution attribute {node.attr}")
            if node.attr in BANNED_PREFIX_HELPERS:
                report(node, f"hand-rolled confinement helper {node.attr}")
        if isinstance(node, ast.Name):
            if node.id in BANNED_BUILTINS:
                report(node, f"builtin {node.id}")
            if node.id in OS_EXECUTION_NAMES:
                report(node, f"os execution name {node.id}")

        # --- path observers, with AC34's single carve-out ------------------
        if isinstance(node, ast.Attribute | ast.Name):
            name = node.attr if isinstance(node, ast.Attribute) else node.id
            module_reference = isinstance(node, ast.Name) and node.id in modules
            if name in BANNED_PATH_OBSERVERS and not module_reference:
                enclosing = owner.get(getattr(node, "lineno", -1))
                carved = (filename, enclosing) == PROBE_CARVE_OUT
                if not carved:
                    report(node, f"path observer {name}")

        # --- AC39: joins are confined by an admitted mechanism -------------
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "startswith"
            and _is_path_expression(node.value)
        ):
            report(node, "hand-rolled path prefix check")
        if isinstance(node, ast.Call):
            for argument in node.args:
                if isinstance(argument, ast.Attribute) and argument.attr == "startswith":
                    report(node, "hand-rolled path prefix check")
        if isinstance(node, ast.ListComp | ast.GeneratorExp | ast.SetComp):
            # The ban is on *stripping* `..`, not on testing for it. A
            # comprehension that yields its own loop variable while filtering
            # `..` out silently sanitises a hostile path into an admissible
            # one; a generator whose element is a comparison is a refusal, and
            # refusing is exactly what AC39 asks for. Both spellings mention
            # `..`, so only the shape separates them.
            strips = (
                len(node.generators) == 1
                and isinstance(node.elt, ast.Name)
                and isinstance(node.generators[0].target, ast.Name)
                and node.elt.id == node.generators[0].target.id
                and any("'..'" in ast.dump(test) for test in node.generators[0].ifs)
            )
            if strips:
                report(node, "`..`-stripping comprehension")

    return findings


def test_direct_modules_pass_every_architecture_control():
    # AC17, AC39 — the real modules are clean.
    for module in DIRECT_MODULES:
        path = Path(module.__file__)
        findings = direct_module_findings(path.read_text(encoding="utf-8"), path.name)
        assert findings == [], "\n".join(findings)


def test_the_probe_carve_out_is_exactly_one_function():
    # AC34 — `probe_measured_path` is the sole `lstat` carve-out, and it must
    # return a refusal decision rather than a `stat_result`.
    source = Path(direct_source.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    probe = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "probe_measured_path"
    )
    returns = [
        node
        for node in ast.walk(probe)
        if isinstance(node, ast.Return) and node.value is not None
    ]
    assert returns, "the probe must return a decision"
    for node in returns:
        rendered = ast.dump(node)
        assert "stat_result" not in rendered
        assert "MeasuredPathProbe" in rendered, ast.unparse(node)

    annotation = ast.unparse(probe.returns) if probe.returns else ""
    assert annotation == "MeasuredPathProbe", annotation

    # Widening the carve-out to a second function is itself a regression.
    lstat_owners = {
        owner
        for owner, name in _observer_uses(source)
        if name in BANNED_PATH_OBSERVERS
    }
    assert lstat_owners == {"probe_measured_path"}, lstat_owners


def _observer_uses(source: str) -> list[tuple[str | None, str]]:
    """Every path-observer use paired with its enclosing function."""

    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    modules = _module_names(tree)
    uses: list[tuple[str | None, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute | ast.Name):
            name = node.attr if isinstance(node, ast.Attribute) else node.id
            if isinstance(node, ast.Name) and node.id in modules:
                continue
            if name in BANNED_PATH_OBSERVERS:
                uses.append((owner.get(getattr(node, "lineno", -1)), name))
    return uses


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("import subprocess\n", "import of subprocess"),
        ("import runpy\n", "import of runpy"),
        ("from os import system\n", "from os import system"),
        ("import os\ndef f():\n    return os.system('x')\n", "os execution attribute system"),
        ("import os\ndef f():\n    return os.spawnv('x')\n", "os execution attribute spawnv"),
        ("def f(src):\n    return eval(src)\n", "builtin eval"),
        ("def f(src):\n    return exec(src)\n", "builtin exec"),
        ("import os\ndef f(p):\n    return os.path.realpath(p)\n", "path observer realpath"),
        ("import os\ndef f(p):\n    return os.path.abspath(p)\n", "path observer abspath"),
        ("def f(p):\n    return p.resolve()\n", "path observer resolve"),
        ("def f(p):\n    return p.lstat()\n", "path observer lstat"),
        # The narrowed `startswith` ban: a Path-typed receiver is a jail check.
        (
            "def f(path, root):\n    return str(path).startswith(root)\n",
            "hand-rolled path prefix check",
        ),
        (
            "def f(path, root):\n    return path.relative_to(root).as_posix().startswith('x')\n",
            "hand-rolled path prefix check",
        ),
        (
            "import os\ndef f(a, b):\n    return os.path.commonpath([a, b])\n",
            "hand-rolled confinement helper commonpath",
        ),
        (
            "import os\ndef f(a, b):\n    return os.path.commonprefix([a, b])\n",
            "hand-rolled confinement helper commonprefix",
        ),
        (
            "import os\ndef f(p):\n    return os.path.normpath(p)\n",
            "hand-rolled confinement helper normpath",
        ),
        (
            "def f(parts):\n    return [p for p in parts if p != '..']\n",
            "`..`-stripping comprehension",
        ),
    ],
)
def test_each_control_has_a_mutation_that_kills_it(mutation, expected):
    # Every rule above is paired with source that must trip it. A rule with no
    # such fixture is a control that cannot fail.
    findings = direct_module_findings(mutation, "direct_source.py")
    assert any(expected in finding for finding in findings), (
        f"mutation did not trip {expected!r}: {findings}"
    )


def test_the_carve_out_is_scoped_to_one_module_and_one_function():
    # Deleting or widening the carve-out must be visible. The same `lstat` in a
    # different function, or in a different direct module, still refuses.
    inside = "def probe_measured_path(p):\n    return p.lstat()\n"
    assert direct_module_findings(inside, "direct_source.py") == []
    assert direct_module_findings(inside, "bounded_metadata.py") != []
    outside = "def other(p):\n    return p.lstat()\n"
    assert direct_module_findings(outside, "direct_source.py") != []


def test_prefix_ban_does_not_flag_the_grammars_that_share_these_modules():
    # A bare-name `startswith` ban is undecidable at this seam and would equally
    # flag AC13's digest-prefix refusal and AC3's source grammar, both of which
    # live in these same modules. Narrowing to path-shaped receivers is what
    # makes the rule expressible at all.
    for benign in (
        "def f(digest):\n    return digest.startswith('sha256-1:')\n",
        "def f(source):\n    return source.startswith('git+https://github.com/')\n",
        "def f(ref):\n    return ref.startswith('refs/tags/')\n",
    ):
        assert direct_module_findings(benign, "direct_source.py") == [], benign


def test_confinement_calls_are_the_admitted_mechanisms():
    # AC39 — every confinement call reached by a direct module is one of the
    # admitted named mechanisms. A join confined by anything else is the
    # regression this names.
    for module in DIRECT_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        confinement_like = {
            name
            for name in called
            if "confined" in name or "jailed" in name or name.endswith("_probe")
        }
        assert confinement_like <= CONFINEMENT_CALLS, (
            f"{Path(module.__file__).name} calls an unlisted confinement "
            f"mechanism: {confinement_like - CONFINEMENT_CALLS}"
        )
