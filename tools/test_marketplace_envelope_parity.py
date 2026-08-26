"""Parity gate for the Claude-plugin marketplace envelope.

The advertised branch and the marketplace description are each stated in more than one
place by construction: the catalogue schema lists `claude-plugin-branch` and
`marketplace-description` under `[catalogue.build]`'s `required`, so `catalogue.toml`
cannot omit them, while ADR-0072 pins the branch in `build/main.py`'s `_DIST_BRANCH`.
Where one home is impossible, this repository's control is a parity gate — the same
shape as `tools/test_contract_parity.py` for the `contracts/` <-> `_data/` twins.

ADR-0072 rests its accepted mutable-`ref` residual on branch integrity, and branch
protection is scoped to a *repository*. So the gate anchors both halves of what an
adopter resolves — `source.ref` **and** `source.url` — plus `source.path`, which selects
which subtree of the protected ref is fetched and executed.

Two layers, deliberately:

1. **The resolved value is the authority.** For the two constants in `build/main.py` the
   gate reads what the build actually emits, in a **child interpreter** — `-I` (no
   environment, no user site, no cwd on `sys.path`), `-B` (so it cannot write bytecode
   into the tree it audits, which `CAT-V-014` would then report as drift), and
   `--check-hash-based-pycs always` (so an `unchecked_hash` `.pyc` cannot stand in for
   source). It does not import in-process: `sys.modules` is the real authority behind an
   import, any module-scope statement in any module of the same pytest command can
   pre-fill it, and pytest imports every collected module before running any test — so a
   plant collected *later* still wins, and a forged `__file__` then satisfies an
   attribute-based provenance claim. Provenance therefore comes from the **finder**
   (`importlib.util.find_spec(...).origin`), never from the module. Values must be of
   type exactly `str`; a subclass can define `__eq__`/`__ne__` that lie and wins
   reflected-operand priority, so comparisons go through `str.__eq__`.

   The publisher is a `tools` script rather than an installed module, so it is covered by
   layer 2 only — the gate will not exec a script by path to read a constant out of it.
   That residual is `marketplace-publisher-branch-layer-2-only`.

2. **The literal check keeps the value reviewable.** A resolved value alone would accept
   `_DIST_BRANCH = os.environ.get(...)` — correct today, environment-dependent tomorrow.
   So each anchored symbol must also be bound exactly once, at **module scope**, to a
   string literal. Scope matters: a function-local or comprehension binding is not a
   rebind of the module global, and counting one reddens the gate on benign code.

**Known residual.** Neither layer bounds a rebind that happens *after* import — a
function that mutates the global while the build runs, including
`catalogue_tooling/build.py:106-109`, which rebinds both constants from `catalogue.toml`
around `cmd_build` and is the sanctioned path the original defect actually lived on.
Bounding that needs a different instrument (a runtime assertion inside the build, or a
semgrep rule over these two modules); registered as
`marketplace-envelope-post-import-rebind-unbounded`.

Every reader takes a tree root so the mutation suite can drive `check_envelope_parity`
over a fixture instead of mutating tracked security-control files in place. The
resolved-value layer applies only to the live tree, because a fixture of anchor paths is
not an importable package; a handful of tests build a full package copy to drive that
layer directly.

Each parity assertion raises `ParityError` rather than using a bare `assert`: under
`python -O` an assert is compiled away, and these comparisons *are* the gate — measured,
a hostile `source.ref` went undetected under `-O` while the run reported success.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tomllib
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

PUBLISH_CONTROL = Path(".github/claude-plugin-publish-control.json")
PUBLISHER = Path("tools/catalogue/publish_claude_plugins.py")
BUILD_MAIN = Path("packages/agentbundle/agentbundle/build/main.py")
SELF_HOST = Path("packages/agentbundle/agentbundle/build/self_host.py")
CATALOGUE_TOML = Path("catalogue.toml")
ROOT_MARKETPLACE = Path(".claude-plugin/marketplace.json")
MAKEFILE = Path("Makefile")
BUILD_CHECK_WORKFLOW = Path(".github/workflows/build-check.yml")
SELF = Path(__file__).resolve().relative_to(REPO_ROOT)
#: How the gate finds the parallel pytest list in both files. If this file is
#: renamed or unwired, update this anchor — the failure message names it.
PYTEST_LIST_ANCHOR = "tools/test_contract_parity.py"

#: This gate's own line in the Makefile's pytest list, as the unwiring probes must
#: delete it. ADR-0096 moved that list out of the `test-unleased` recipe and into
#: the `run-test-suite` macro both test targets call, which drops one level of
#: recipe indentation — so the literal carries ONE tab, not two. One definition,
#: because two probes delete the same line and a half-updated pair would leave a
#: probe silently anchored on text that no longer exists.
MAKEFILE_GATE_LINE = "\ttools/test_marketplace_envelope_parity.py \\\n"

#: Every path `check_envelope_parity` reads. A probe materialises exactly these into
#: a fixture tree; copying the repository would drag ~70 MB plus three symlinked
#: context files, and a symlink-following copy would write a mutation back into the
#: live worktree.
ANCHOR_PATHS = (
    PUBLISH_CONTROL, PUBLISHER, BUILD_MAIN, SELF_HOST,
    CATALOGUE_TOML, ROOT_MARKETPLACE, MAKEFILE, BUILD_CHECK_WORKFLOW,
)

#: ADR-0072 pins the branch; `tools/lint-claude-plugin-publish-control.py:302-312`
#: pins `branch` against this same literal. `repo` is pinned by no PR-time gate
#: (`--subject "$GITHUB_REPOSITORY"` is passed only by the publish workflow), so the
#: gate pins it here: otherwise a PR could move `repo`, the evidence copy, the
#: entries' `source.url`, and the pack links together and stay green.
EXPECTED_BRANCH = "claude-plugins-dist"
EXPECTED_REPO = "eugenelim/agent-ready-repo"

_REFS_HEADS = "refs/heads/"
_BUILD_MAIN_MODULE = "agentbundle.build.main"
_DESCRIPTION_SYMBOL = "_MARKETPLACE_DESCRIPTION"
_BRANCH_SYMBOL = "_DIST_BRANCH"
_PUBLISHER_SYMBOL = "BRANCH"
_REF_FORBIDDEN = re.compile(r"[^\x21-\x7e]|[~^:?*\[\\]")
#: Dynamic rebinds layer 2 cannot model. A tripwire over the two anchor modules, so
#: an author reaches for review rather than landing one silently; layer 1 is what
#: actually catches them.
_DYNAMIC_REBIND = re.compile(
    r"globals\s*\(|vars\s*\(|locals\s*\(|sys\.modules\s*\[|__dict__\s*\[|"
    r"setattr\s*\(|\bexec\s*\("
)


class ParityError(AssertionError):
    """A source could not be read, or could not be read unambiguously."""


def _read_text(root: Path, relative: Path) -> str:
    target = root / relative
    if target.is_symlink():
        raise ParityError(
            f"{relative}: is a symlink — a parity anchor must be a real file. Note this "
            f"guards the leaf only; a symlinked parent redirects both layers identically, "
            f"so it is not a divergence this gate can see."
        )
    if not target.is_file():
        raise ParityError(f"{relative}: missing — a parity anchor cannot be skipped")
    try:
        return target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise ParityError(f"{relative}: unreadable ({exc})") from exc


def _load_json(root: Path, relative: Path) -> object:
    try:
        return json.loads(_read_text(root, relative))
    except json.JSONDecodeError as exc:
        raise ParityError(f"{relative}: unparseable JSON ({exc})") from exc


def _load_toml(root: Path, relative: Path) -> dict:
    try:
        return tomllib.loads(_read_text(root, relative))
    except tomllib.TOMLDecodeError as exc:
        raise ParityError(f"{relative}: unparseable TOML ({exc})") from exc


def _module(root: Path, relative: Path) -> ast.Module:
    try:
        return ast.parse(_read_text(root, relative), filename=str(relative))
    except SyntaxError as exc:
        raise ParityError(f"{relative}: unparseable Python ({exc})") from exc


def _dig(payload: object, relative: Path, *keys: str) -> object:
    cursor = payload
    for depth, key in enumerate(keys):
        if not isinstance(cursor, dict):
            raise ParityError(f"{relative}: {'.'.join(keys[:depth]) or '<root>'} is not a table/object")
        if key not in cursor:
            raise ParityError(f"{relative}: {'.'.join(keys[: depth + 1])} is missing")
        cursor = cursor[key]
    return cursor


# --------------------------------------------------------------------------- #
# Layer 1 — the resolved value (live tree only, and authoritative)
# --------------------------------------------------------------------------- #

#: Read in a fresh, isolated interpreter. `sys.modules` is the real authority behind
#: an in-process import, and any module-scope statement in any file of the same pytest
#: command can pre-fill it — pytest imports every collected module before running any
#: test, so even a plant file collected *after* this one wins. A forged `__file__` on
#: the plant then satisfies an attribute-based provenance check. A child process has
#: no in-process plant to inherit, and `importlib.util.find_spec` asks the *finder*
#: where the module lives rather than asking the module to say where it came from.
_RESOLVE_CHILD = r"""
import sys
sys.path.insert(0, PACKAGE_ROOT)
import importlib
import importlib.util
import json

spec = importlib.util.find_spec("agentbundle.build.main")
module = importlib.import_module("agentbundle.build.main")
branch = module._DIST_BRANCH
description = module._MARKETPLACE_DESCRIPTION
print(json.dumps({
    "origin": getattr(spec, "origin", None),
    "branch": str(branch),
    "branch_type": type(branch).__name__,
    "description": str(description),
    "description_type": type(description).__name__,
}))
"""


def resolve_build_main_constants(root: Path) -> dict[str, str]:
    """Return `_DIST_BRANCH` and `_MARKETPLACE_DESCRIPTION` as the build resolves them.

    Runs in a child interpreter with `-I` (no environment, no user site, no cwd on
    `sys.path`) so nothing this process imported can influence the result, and with
    `--check-hash-based-pycs always` so an `unchecked_hash` `.pyc` committed under
    `build/__pycache__/` cannot stand in for the source.

    `-B` is not optional: `-I` implies `-E`, so the child ignores
    `PYTHONDONTWRITEBYTECODE` from the environment and would write `__pycache__` into
    the tree it audits. Because `CAT-V-014` compares `dist/` against a freshly built
    tree, that bytecode gets copied into `dist/` and reported as generated-output
    drift — so without `-B` this gate would redden the very check it exists to
    protect. Measured: four `__pycache__` directories per run.

    The type name of each constant is reported by the child so the parent can refuse
    a `str` subclass: `isinstance` admits one, and a subclass may define `__eq__` /
    `__ne__` that lie while winning reflected-operand priority.
    """
    package_root = (root / BUILD_MAIN).parents[2]
    child = _RESOLVE_CHILD.replace("PACKAGE_ROOT", repr(str(package_root)))
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "--check-hash-based-pycs", "always", "-c", child],
            capture_output=True, text=True, cwd=str(root), timeout=120, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ParityError(f"{_BUILD_MAIN_MODULE}: could not resolve in a child ({exc})") from exc
    if completed.returncode != 0:
        raise ParityError(
            f"{_BUILD_MAIN_MODULE}: child failed (rc={completed.returncode}): "
            f"{completed.stderr.strip()[-400:]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ParityError(
            f"{_BUILD_MAIN_MODULE}: child emitted unparseable output ({exc}): "
            f"{completed.stdout.strip()[:200]}"
        ) from exc

    origin = payload.get("origin")
    expected = str((root / BUILD_MAIN).resolve())
    if origin is None or str(Path(origin).resolve()) != expected:
        raise ParityError(
            f"provenance mismatch: the finder resolved {_BUILD_MAIN_MODULE} to "
            f"{origin!r}, expected {expected!r}. The resolved-value layer must read "
            f"the tree under audit — an editable install can point at a sibling "
            f"worktree, which was measured on a real machine."
        )
    for key in ("branch", "description"):
        if payload.get(f"{key}_type") != "str":
            raise ParityError(
                f"{_BUILD_MAIN_MODULE}: {key} resolves to type "
                f"{payload.get(f'{key}_type')!r}, not exactly str; a str subclass can "
                f"define a comparison that lies"
            )
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise ParityError(f"{_BUILD_MAIN_MODULE}: {key} resolved empty")
    return {"branch": payload["branch"], "description": payload["description"]}


def _differs(value: object, expected: str) -> bool:
    """``value != expected`` without dispatching to a hostile ``__ne__``."""
    return type(value) is not str or not str.__eq__(value, expected)


# --------------------------------------------------------------------------- #
# Layer 2 — the value is a reviewable literal (fixture-probeable)
# --------------------------------------------------------------------------- #

#: Statements that open a new scope. A binding inside one is *not* a binding of the
#: module global, so the reader must not descend into them: counting a function-local
#: `_DIST_BRANCH = x.upper()` as a rebind reddens the gate on benign code, with a
#: diagnostic ("an extra binding decides what is emitted") that is simply false.
#: Comprehensions are scopes too in Python 3, so a comprehension target is local.
_SCOPE_BOUNDARIES = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
    ast.comprehension, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp,
)


def _module_scope_nodes(module: ast.Module):
    """Every node reachable at module scope, stopping at each new scope."""
    stack = list(module.body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, _SCOPE_BOUNDARIES):
            continue
        stack.extend(ast.iter_child_nodes(node))


def _bound_names(module: ast.Module, symbol: str) -> list[str]:
    """Every *module-scope* static binding of *symbol*, as node-kind labels.

    Not exhaustive by construction — bounding every rebinding form is the
    resolved-value layer's job, and six review rounds established that enumerating
    syntax leaks. This layer exists so the emitted value stays reviewable in a diff.

    A `global` statement is the one deliberate cross-scope case: `def f(): global X; X =
    ...` does rebind the module global when called, so it is searched for over the whole
    tree rather than module scope alone.
    """
    found: list[str] = []

    def names_in(target: ast.AST, *, ctx: tuple = (ast.Store,)) -> bool:
        # Context matters: a Name inside a Subscript target (`D[_X] = 1`) is a Load and
        # must not read as a binding, while a `del` target is a Del.
        return any(
            isinstance(sub, ast.Name) and sub.id == symbol and isinstance(sub.ctx, ctx)
            for sub in ast.walk(target)
        )

    for node in _module_scope_nodes(module):
        if isinstance(node, ast.Assign):
            if any(names_in(t) for t in node.targets):
                found.append("Assign")
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            if isinstance(node.target, ast.Name) and node.target.id == symbol:
                found.append(type(node).__name__)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            if names_in(node.target):
                found.append("For")
        elif isinstance(node, ast.withitem):
            if node.optional_vars is not None and names_in(node.optional_vars):
                found.append("withitem")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                # `import a.b` binds `a`; `import a.b as c` binds `c`; `import *` may
                # bind anything, so it is an ambiguity rather than a match.
                if (alias.asname or alias.name.split(".")[0]) == symbol or alias.name == "*":
                    found.append(type(node).__name__)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                found.append(type(node).__name__)
        elif isinstance(node, ast.ExceptHandler):
            if node.name == symbol:
                found.append("ExceptHandler")
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)):
            if node.name == symbol:
                found.append(type(node).__name__)
        elif isinstance(node, ast.MatchMapping):
            if node.rest == symbol:
                found.append("MatchMapping")
        elif isinstance(node, ast.Delete):
            if any(names_in(t, ctx=(ast.Del,)) for t in node.targets):
                found.append("Delete")
        elif isinstance(node, getattr(ast, "TypeAlias", ())) and isinstance(
            node.name, ast.Name
        ) and node.name.id == symbol:
            found.append("TypeAlias")

    # `global` reaches the module namespace from inside a function, so it is the one
    # binding form searched beyond module scope.
    found += [
        "Global"
        for node in ast.walk(module)
        if isinstance(node, ast.Global) and symbol in node.names
    ]
    return found


def literal_assignment(root: Path, relative: Path, symbol: str) -> str:
    """*symbol* is bound exactly once, at module scope, to a string literal."""
    module = _module(root, relative)
    bindings = _bound_names(module, symbol)
    if len(bindings) != 1:
        raise ParityError(
            f"{relative}: {symbol} has {len(bindings)} static bindings {bindings}, "
            f"expected exactly one; the build reads it as a module global, so an extra "
            f"binding decides what is emitted"
        )
    assigns = [
        n for n in module.body
        if isinstance(n, (ast.Assign, ast.AnnAssign))
        and any(isinstance(t, ast.Name) and t.id == symbol
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))
    ]
    if len(assigns) != 1:
        raise ParityError(f"{relative}: {symbol} is not assigned exactly once at module scope")
    value = assigns[0].value
    if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
        kind = type(value).__name__ if value is not None else "no value"
        raise ParityError(
            f"{relative}: {symbol} is not a string literal ({kind}) — the emitted value "
            f"must be reviewable in the diff, not computed. An annotated assignment is "
            f"accepted; a BinOp or os.environ.get(...) is not."
        )
    refuse_dynamic_rebind(root, relative, symbol)
    return value.value


def refuse_dynamic_rebind(root: Path, relative: Path, symbol: str) -> None:
    """Refuse a dynamic write to *symbol* in *relative*.

    A tripwire, not a proof: a construct split across lines escapes it, which is
    layer 1's to catch. Scoped to lines naming the symbol so an unrelated
    ``setattr()`` elsewhere in a 1200-line module does not redden the gate.
    """
    dynamic = [
        n for n, line in enumerate(_read_text(root, relative).splitlines(), 1)
        if _DYNAMIC_REBIND.search(line) and symbol in line
    ]
    if dynamic:
        raise ParityError(
            f"{relative}: line(s) {dynamic} rebind {symbol} dynamically; this needs "
            f"review, not a silent landing."
        )


def assert_git_ref_safe(branch: str, source: Path) -> str:
    if not branch:
        raise ParityError(
            f"{source}: branch name is empty — '{_REFS_HEADS}' alone names no branch a "
            f"ruleset can guard"
        )
    components = branch.split("/")
    if (
        branch in {"HEAD", "@"}
        or branch.startswith("-")
        or ".." in branch
        or "@{" in branch
        or _REF_FORBIDDEN.search(branch)
        or any(not c or c.startswith(".") or c.endswith((".", ".lock")) for c in components)
    ):
        raise ParityError(f"{source}: unsafe or non-ASCII branch name {branch!r}")
    return branch


# --------------------------------------------------------------------------- #
# Data anchors
# --------------------------------------------------------------------------- #

def read_publish_control_branch(root: Path) -> str:
    target = _dig(_load_json(root, PUBLISH_CONTROL), PUBLISH_CONTROL, "branch", "target")
    if not isinstance(target, str):
        raise ParityError(f"{PUBLISH_CONTROL}: branch.target is not a string")
    if not target.startswith(_REFS_HEADS):
        raise ParityError(
            f"{PUBLISH_CONTROL}: branch.target {target!r} has no {_REFS_HEADS!r} prefix; "
            f"a bare name would let the ruleset guard nothing"
        )
    return assert_git_ref_safe(target[len(_REFS_HEADS) :], PUBLISH_CONTROL)


def read_publish_control_repo(root: Path) -> str:
    repo = _dig(_load_json(root, PUBLISH_CONTROL), PUBLISH_CONTROL, "repo")
    if not isinstance(repo, str) or repo.count("/") != 1 or not all(repo.split("/")):
        raise ParityError(f"{PUBLISH_CONTROL}: repo {repo!r} is not 'owner/name'")
    return repo


def read_catalogue_build(root: Path, key: str) -> str:
    value = _dig(_load_toml(root, CATALOGUE_TOML), CATALOGUE_TOML, "catalogue", "build", key)
    if not isinstance(value, str):
        raise ParityError(f"{CATALOGUE_TOML}: catalogue.build.{key} is not a string")
    return value


def read_marketplace_sources(root: Path) -> list[tuple[str, str, str]]:
    """``(label, source.ref, source.url)`` per entry, labelled by *index*.

    Labelled by index, not by ``name``: the name is content from the file under
    audit and is not unique, so keying a comparison by it lets a duplicate-named
    entry's clean value overwrite an injected one.
    """
    payload = _dig(_load_json(root, ROOT_MARKETPLACE), ROOT_MARKETPLACE, "plugins")
    if not isinstance(payload, list) or not payload:
        raise ParityError(
            f"{ROOT_MARKETPLACE}: plugins is empty or not a list — 'every entry agrees' "
            f"must not be vacuously true"
        )
    out: list[tuple[str, str, str]] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise ParityError(f"{ROOT_MARKETPLACE}: plugins[{index}] is not an object")
        raw_name = entry.get("name")
        if not isinstance(raw_name, str) or not raw_name:
            raise ParityError(
                f"{ROOT_MARKETPLACE}: plugins[{index}].name is missing or not a string; "
                f"the path pin compares against it, and blaming path for a name defect "
                f"would name the wrong source"
            )
        name = raw_name
        label = f"{ROOT_MARKETPLACE}:plugins[{index}] ({name})"
        source = entry.get("source")
        if not isinstance(source, dict):
            raise ParityError(f"{label}.source is missing or not an object")
        if _differs(source.get("source"), "git-subdir"):
            raise ParityError(f"{label}.source.source is {source.get('source')!r}, not 'git-subdir'")
        # Checked before the key-set refusal below, which would otherwise catch `sha`
        # as merely "unexpected" and lose the reason it matters.
        if "sha" in source:
            raise ParityError(
                f"{label}.source pins a sha; this gate anchors ref, so a sha-pinned entry "
                f"would silently leave the anchor set"
            )
        extra = set(source) - {"source", "url", "path", "ref"}
        if extra:
            raise ParityError(
                f"{label}.source carries unexpected keys {sorted(extra)}; a redirect key "
                f"riding alongside a correct url is otherwise caught only by CAT-V-013, "
                f"whose step returns [] when the validator import fails "
                f"(catalogue_tooling/verify.py:1227-1231) and when neither dist/ nor the "
                f"root marketplace exists (:1224)"
            )
        if _differs(source.get("path"), name):
            raise ParityError(
                f"{label}.source.path is {source.get('path')!r}, expected {name!r}; "
                f"path selects which subtree of the protected ref is fetched and run"
            )
        ref, url = source.get("ref"), source.get("url")
        if not isinstance(ref, str) or not ref:
            raise ParityError(f"{label}.source.ref is missing or not a string")
        if not isinstance(url, str) or not url:
            raise ParityError(f"{label}.source.url is missing or not a string")
        out.append((label, ref, url))
    return out


def self_host_description_default(root: Path) -> ast.expr:
    funcs = [
        n for n in _module(root, SELF_HOST).body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "_aggregate_marketplace"
    ]
    if len(funcs) != 1:
        raise ParityError(
            f"{SELF_HOST}: expected exactly one module-level _aggregate_marketplace, "
            f"found {len(funcs)}"
        )
    args = funcs[0].args
    names = [a.arg for a in args.args]
    if "description" not in names:
        raise ParityError(f"{SELF_HOST}: _aggregate_marketplace has no description parameter")
    index = names.index("description") - (len(names) - len(args.defaults))
    if index < 0:
        raise ParityError(
            f"{SELF_HOST}: _aggregate_marketplace's description carries no default; reading "
            f"a neighbouring parameter's default would blame the wrong node"
        )
    return args.defaults[index]


def self_host_passes_description(root: Path) -> list[int]:
    """Lines where a caller passes ``description=`` — a fourth statement by the back door."""
    return [
        node.lineno
        for node in ast.walk(_module(root, SELF_HOST))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_aggregate_marketplace"
        and any(kw.arg == "description" for kw in node.keywords)
    ]


def pytest_group(root: Path, relative: Path, anchor: str) -> frozenset[str]:
    """The ``tools/*.py`` set of the one logical pytest command naming *anchor*.

    Continuations are joined first and the single logical line is taken, rather than
    walking outward from the anchor line while adjacent lines happen to name a
    ``tools/`` path: that walk narrows silently the moment an interior line names a
    non-``tools`` path, which is exactly the "narrow a drift check's comparison
    scope" failure the spec forbids.
    """
    text = _read_text(root, relative).replace("\\\n", " ")
    lines = [re.sub(r"#.*$", "", line) for line in text.splitlines()]
    matching = [line for line in lines if anchor in line]
    if len(matching) != 1:
        raise ParityError(
            f"{relative}: expected exactly one command naming {anchor}, found {len(matching)}"
        )
    return frozenset(re.findall(r"tools/[\w./-]+\.py", matching[0]))


# --------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------
# The parity assertions. Every one raises `ParityError` rather than using a bare
# `assert`: under `python -O` an assert is compiled away, and this module's comparisons
# ARE the gate — measured, a hostile `source.ref` went undetected under `-O` while the
# run reported success. `assert` is left to the test functions, where pytest needs it.
#
# Split into one function per invariant so a mutation probe can require the *specific*
# message it expects. With one flat body a probe could only observe "something failed",
# and a probe that cannot tell which refusal fired cannot show that refusal works:
# mutation-testing this suite found 20 of 40 individual refusals could be deleted with
# every test still green, because downstream parity caught the mutation first.
# ---------------------------------------------------------------------------

_MSG_BRANCH_PIN = "ADR-0072 pins"
_MSG_REPO_PIN = "no PR-time gate pins this field"
_MSG_BRANCH_PARITY = "advertised branch disagrees"
_MSG_URL_PARITY = "source.url must be"
_MSG_DESCRIPTION_PARITY = "description disagrees"
_MSG_SELF_HOST_DEFAULT = "description default must be"
_MSG_SELF_HOST_CALLER = "is called with description="
_MSG_FORGED_FILE = "binds __file__"
_MSG_GATE_MEMBERSHIP = "is not in the"
_MSG_LIST_PARITY = "must name the same files"


def _assert_adr_pins(root: Path) -> tuple[str, str]:
    """`branch.target` and `repo` are the literals ADR-0072 fixes."""
    branch = read_publish_control_branch(root)
    repo = read_publish_control_repo(root)
    if _differs(branch, EXPECTED_BRANCH):
        raise ParityError(
            f"{PUBLISH_CONTROL}: branch.target names {branch!r}; {_MSG_BRANCH_PIN} "
            f"{EXPECTED_BRANCH!r} and rests on that branch's protection ruleset"
        )
    if _differs(repo, EXPECTED_REPO):
        raise ParityError(
            f"{PUBLISH_CONTROL}: repo is {repo!r}, expected {EXPECTED_REPO!r}; "
            f"{_MSG_REPO_PIN}, so the gate pins it here"
        )
    return branch, repo


def _assert_branch_parity(root: Path, branch: str, sources: list) -> None:
    reference = f"{PUBLISH_CONTROL}:branch.target={branch!r}"
    anchors = [
        (f"{PUBLISHER}:{_PUBLISHER_SYMBOL}", literal_assignment(root, PUBLISHER, _PUBLISHER_SYMBOL)),
        (f"{BUILD_MAIN}:{_BRANCH_SYMBOL}", literal_assignment(root, BUILD_MAIN, _BRANCH_SYMBOL)),
        (f"{CATALOGUE_TOML}:claude-plugin-branch", read_catalogue_build(root, "claude-plugin-branch")),
        *((f"{label}.source.ref", ref) for label, ref, _url in sources),
    ]
    bad = [f"{k}={v!r}" for k, v in anchors if _differs(v, branch)]
    if bad:
        raise ParityError(
            f"{_MSG_BRANCH_PARITY} with {reference}: {bad}. Moving the advertised branch "
            f"legitimately means all five anchors plus a superseding ADR plus the "
            f"repository ruleset — not one of them."
        )


def _assert_url_parity(root: Path, repo: str, sources: list) -> None:
    expected = f"https://github.com/{repo}.git"
    bad = [f"{k}.source.url={v!r}" for k, _ref, v in ((s[0], s[1], s[2]) for s in sources)
           if _differs(v, expected)]
    if bad:
        raise ParityError(
            f"{_MSG_URL_PARITY} {expected!r}, implied by {PUBLISH_CONTROL}:repo={repo!r} — "
            f"branch protection is scoped to a repository, so ref parity against another "
            f"repo's url guards nothing: {bad}"
        )


def _assert_description_parity(root: Path) -> None:
    constant = literal_assignment(root, BUILD_MAIN, _DESCRIPTION_SYMBOL)
    anchors = [
        (f"{CATALOGUE_TOML}:marketplace-description",
         read_catalogue_build(root, "marketplace-description")),
        (f"{ROOT_MARKETPLACE}:description",
         _dig(_load_json(root, ROOT_MARKETPLACE), ROOT_MARKETPLACE, "description")),
    ]
    bad = [f"{k}={v!r}" for k, v in anchors if _differs(v, constant)]
    if bad:
        raise ParityError(
            f"{_MSG_DESCRIPTION_PARITY} with {BUILD_MAIN}:{_DESCRIPTION_SYMBOL}="
            f"{constant!r}: {bad}"
        )


def _assert_self_host_contract(root: Path, description: str) -> None:
    """`_aggregate_marketplace`'s `description` default is a fourth statement — anchored.

    It would be better to delete it: `self_host.py` could import
    `_MARKETPLACE_DESCRIPTION` instead, leaving three homes rather than four. That change
    was made and then reverted, because `packages/agentbundle/` is a protected tree —
    `tools/lint-catalogue-curation-guard.py` requires an `Engine-Change-RFC:` trailer and
    `AGENTS.local.md` additionally requires a version bump. Turning a config-drift fix
    into an engine release is the wrong trade, so the literal stays and this anchors it.
    Registered as `marketplace-description-fourth-statement-in-self-host`.

    Anchoring is not equivalent to deleting: it catches divergence, not the duplication
    itself. But it is the property that matters — this default, not
    `_MARKETPLACE_DESCRIPTION`, is what writes the committed root marketplace, so an edit
    here with no edit elsewhere would ship a description nothing else states.
    """
    default = self_host_description_default(root)
    if not (isinstance(default, ast.Constant) and isinstance(default.value, str)):
        raise ParityError(
            f"{SELF_HOST}: _aggregate_marketplace's {_MSG_SELF_HOST_DEFAULT} a string "
            f"literal (found {type(default).__name__}); the gate anchors its value, and "
            f"a computed default cannot be anchored"
        )
    if _differs(default.value, description):
        raise ParityError(
            f"{_MSG_DESCRIPTION_PARITY}: {SELF_HOST}'s _aggregate_marketplace default is "
            f"{default.value!r}, not {description!r}. That default — not "
            f"{_DESCRIPTION_SYMBOL} — is what writes the committed root marketplace, so a "
            f"change here alone ships a description nothing else states."
        )
    passed = self_host_passes_description(root)
    if passed:
        raise ParityError(
            f"{SELF_HOST}: _aggregate_marketplace {_MSG_SELF_HOST_CALLER} at line(s) "
            f"{passed}; a caller-supplied description escapes this anchor entirely"
        )
    refuse_dynamic_rebind(root, SELF_HOST, _DESCRIPTION_SYMBOL)


def _assert_no_forged_provenance(root: Path) -> None:
    """A module-scope `__file__ = ...` forges an attribute-based provenance claim.

    The finder-supplied origin does not trust `__file__`, so this is belt-and-braces —
    but a module has no legitimate reason to assign it, and refusing it outright is
    cheaper than reasoning about what a forgery could reach.
    """
    forged = _bound_names(_module(root, BUILD_MAIN), "__file__")
    if forged:
        raise ParityError(
            f"{BUILD_MAIN}: {_MSG_FORGED_FILE} {forged}; that forges provenance and no "
            f"anchor module has a reason to do it"
        )


def _assert_gate_wiring(root: Path) -> None:
    make_group = pytest_group(root, MAKEFILE, PYTEST_LIST_ANCHOR)
    ci_group = pytest_group(root, BUILD_CHECK_WORKFLOW, PYTEST_LIST_ANCHOR)
    me = SELF.as_posix()
    for relative, group in ((MAKEFILE, make_group), (BUILD_CHECK_WORKFLOW, ci_group)):
        if me not in group:
            raise ParityError(
                f"{relative}: the parity gate {me} {_MSG_GATE_MEMBERSHIP} test group it "
                f"guards; set equality alone holds vacuously if neither list names it"
            )
    if make_group != ci_group:
        raise ParityError(
            f"{MAKEFILE} and {BUILD_CHECK_WORKFLOW} {_MSG_LIST_PARITY}; only in "
            f"{MAKEFILE}: {sorted(make_group - ci_group)}; only in "
            f"{BUILD_CHECK_WORKFLOW}: {sorted(ci_group - make_group)}"
        )


def assert_resolved_matches(resolved: dict, branch: str, description: str) -> None:
    """The value the build emits equals the literal the diff shows.

    A separate function because on the live tree these are equal by construction, so no
    fixture can drive a mismatch through `check_envelope_parity` — without a seam the
    comparison is unverifiable, which a mutation sweep of this suite duly reported.
    """
    if _differs(resolved.get("branch"), branch):
        raise ParityError(
            f"{_MSG_BRANCH_PARITY}: {_BUILD_MAIN_MODULE}.{_BRANCH_SYMBOL} resolves to "
            f"{resolved.get('branch')!r}, not {branch!r} — the literal in the source and "
            f"the value the build emits are different things"
        )
    if _differs(resolved.get("description"), description):
        raise ParityError(
            f"{_MSG_DESCRIPTION_PARITY}: {_BUILD_MAIN_MODULE}.{_DESCRIPTION_SYMBOL} "
            f"resolves to {resolved.get('description')!r}, not {description!r}"
        )


def check_envelope_parity(root: Path, *, resolve: bool = False) -> None:
    """Assert the marketplace envelope agrees across every anchor under *root*.

    The single entry point, so a mutation probe drives the real gate rather than
    restating its arithmetic. ``resolve`` adds the resolved-value layer and applies only
    to the live tree, where the package under audit is importable.
    """
    if resolve and root.resolve() != REPO_ROOT.resolve():
        raise ParityError(
            "resolve=True is only valid for the live tree: the resolved-value layer "
            "reads the tree under audit, not a fixture"
        )
    branch, repo = _assert_adr_pins(root)
    sources = read_marketplace_sources(root)

    _assert_no_forged_provenance(root)
    _assert_branch_parity(root, branch, sources)
    _assert_url_parity(root, repo, sources)
    description = literal_assignment(root, BUILD_MAIN, _DESCRIPTION_SYMBOL)
    _assert_description_parity(root)
    _assert_self_host_contract(root, description)
    _assert_gate_wiring(root)

    if resolve:
        assert_resolved_matches(
            resolve_build_main_constants(root),
            branch,
            literal_assignment(root, BUILD_MAIN, _DESCRIPTION_SYMBOL),
        )


# STUB: AC3, AC4, AC5, AC6, AC9 — the live tree, with the resolved-value layer engaged.
def test_marketplace_envelope_agrees_across_every_anchor() -> None:
    check_envelope_parity(REPO_ROOT, resolve=True)


# STUB: AC7 — the literal layer refuses an ambiguous, shadowed, or computed symbol.
def test_literal_layer_refuses_shadowed_or_computed_symbols(tmp_path: Path) -> None:
    target = tmp_path / BUILD_MAIN
    target.parent.mkdir(parents=True, exist_ok=True)

    def read(body: str) -> str:
        target.write_text(body, encoding="utf-8")
        return literal_assignment(tmp_path, BUILD_MAIN, _BRANCH_SYMBOL)

    assert read('_DIST_BRANCH = "b"\n') == "b"
    assert read('_DIST_BRANCH: str = "b"\n') == "b", "an annotated assignment is a valid anchor"

    base = '_DIST_BRANCH = "b"\n'
    refused = [
        base + '_DIST_BRANCH: str = "attacker"\n',
        base + '_DIST_BRANCH += "-attacker"\n',
        base + 'if True:\n    _DIST_BRANCH = "attacker"\n',
        base + 'for _DIST_BRANCH in ["attacker"]:\n    pass\n',
        base + 'with open("f") as _DIST_BRANCH:\n    pass\n',
        # NOT here: `_x = [_DIST_BRANCH for _DIST_BRANCH in [...]]`. A comprehension is
        # its own scope in Python 3, so that target does not rebind the module global —
        # refusing it was over-strictness with a false diagnostic, not a control.
        base + 'def f():\n    global _DIST_BRANCH\n    _DIST_BRANCH = "attacker"\n',
        base + 'from attacker import _DIST_BRANCH\n',
        base + 'import attacker as _DIST_BRANCH\n',
        base + 'from attacker import x as _DIST_BRANCH\n',
        base + 'from attacker import *\n',
        base + 'def _DIST_BRANCH():\n    pass\n',
        base + 'class _DIST_BRANCH:\n    pass\n',
        base + 'try:\n    pass\nexcept OSError as _DIST_BRANCH:\n    pass\n',
        base + 'match v:\n    case _DIST_BRANCH:\n        pass\n',
        base + 'del _DIST_BRANCH\n',
        base + 'globals()["_DIST_BRANCH"] = "attacker"\n',
        base + 'vars()["_DIST_BRANCH"] = "attacker"\n',
        base + 'setattr(sys.modules[__name__], "_DIST_BRANCH", "attacker")\n',
        base + 'exec(\'_DIST_BRANCH = "attacker"\')\n',
        'if True:\n    _DIST_BRANCH = "b"\n',
        '_DIST_BRANCH = "a" + "b"\n',
        '_DIST_BRANCH = os.environ.get("X", "b")\n',
        '',
    ]
    for body in refused:
        try:
            read(body)
        except ParityError:
            continue
        raise AssertionError(f"layer 2 accepted a shadowed or computed symbol:\n{body}")


# STUB: AC7 — branch-shape refusal.
def test_branch_shape_is_validated() -> None:
    unsafe = ("", " ", "-x", "--upload-pack=touch", "a..b", "a@{0}", "HEAD", "@",
              "a\nb", "x.lock", "a.lock/b", "a/.b", "a//b", "/a", "a/", "a.",
              "claude-plugins-d\u0456st", "a~b", "a^b", "a:b", "a?b", "a*b", "a[b", "a\\b")
    for name in unsafe:
        try:
            assert_git_ref_safe(name, PUBLISH_CONTROL)
        except ParityError:
            continue
        raise AssertionError(f"accepted unsafe branch name {name!r}")
    assert assert_git_ref_safe(EXPECTED_BRANCH, PUBLISH_CONTROL) == EXPECTED_BRANCH


# ---------------------------------------------------------------------------
# T3 — the mutation suite (AC8).
#
# Each probe drives `check_envelope_parity` over a fixture and asserts the failure
# names the mutated source. Driving the real entry point is the point: a probe that
# restated the comparison would assert its own arithmetic.
# ---------------------------------------------------------------------------

_LITERAL_DESCRIPTION = (
    '"Agent skills, subagents, and hooks for Claude Code and other coding agents."'
)


def _fixture(tmp_path: Path) -> Path:
    """Materialise the anchor paths only.

    `copyfile` per path, never `copytree`: the tree is ~70 MB before
    `docs-site/node_modules`, and a symlink-following copy of a symlinked anchor would
    write a probe's mutation back into the live worktree.
    """
    root = tmp_path / "tree"
    for relative in ANCHOR_PATHS:
        source = REPO_ROOT / relative
        assert source.is_file() and not source.is_symlink(), f"{relative} is not a real file"
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return root


def _edit(root: Path, relative: Path, old: str, new: str) -> None:
    target = root / relative
    text = target.read_text(encoding="utf-8")
    assert old in text, f"{relative}: probe anchor {old!r} not found — the probe is stale"
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def _edit_json(root: Path, relative: Path, mutate) -> None:
    target = root / relative
    payload = json.loads(target.read_text(encoding="utf-8"))
    mutate(payload)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _append(root: Path, relative: Path, snippet: str) -> None:
    target = root / relative
    target.write_text(target.read_text(encoding="utf-8") + "\n" + snippet + "\n", encoding="utf-8")


def _append_text(root: Path, relative: Path, snippet: str) -> None:
    target = root / relative
    target.write_text(target.read_text(encoding="utf-8") + "\n" + snippet + "\n", encoding="utf-8")


def _duplicate_entry(payload: dict) -> None:
    """A second entry under an existing name carrying a hostile ref.

    Keyed by entry `name`, the legitimate entry's clean value overwrote this one; the
    comparison is keyed by index for exactly this reason.
    """
    clone = json.loads(json.dumps(payload["plugins"][0]))
    clone["source"]["ref"] = "attacker-branch"
    payload["plugins"].insert(0, clone)


def _coordinated_repo_move(root: Path) -> None:
    """Move `repo` *and* every entry's `source.url` together, as one PR would."""
    hostile = "eugenelirn/agent-ready-repo"
    _edit_json(root, PUBLISH_CONTROL, lambda d: d.__setitem__("repo", hostile))
    _edit_json(
        root, ROOT_MARKETPLACE,
        lambda d: [
            e["source"].__setitem__("url", f"https://github.com/{hostile}.git")
            for e in d["plugins"]
        ],
    )


def _drop_gate_from_both_lists(root: Path) -> None:
    """Unwire the gate from both lists at once, keeping them equal."""
    _edit(root, MAKEFILE, MAKEFILE_GATE_LINE, "")
    _edit(
        root, BUILD_CHECK_WORKFLOW,
        "            tools/test_marketplace_envelope_parity.py \\\n", "",
    )


def _symlink_anchor(root: Path) -> None:
    """Replace an anchor with a symlink to its own content."""
    target = root / CATALOGUE_TOML
    payload = target.with_suffix(".real")
    payload.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.unlink()
    target.symlink_to(payload)


#: (probe id, the source the failure must name, mutation).
_MUTATIONS = [
    # the five branch anchors
    ("branch-target", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL,
                          lambda p: p["branch"].__setitem__("target", "refs/heads/attacker"))),
    ("publisher-BRANCH", PUBLISHER,
     lambda r: _edit(r, PUBLISHER, 'BRANCH = "claude-plugins-dist"', 'BRANCH = "attacker-branch"')),
    ("_DIST_BRANCH", BUILD_MAIN,
     lambda r: _edit(r, BUILD_MAIN, '_DIST_BRANCH = "claude-plugins-dist"',
                     '_DIST_BRANCH = "attacker-branch"')),
    ("catalogue-branch", CATALOGUE_TOML,
     lambda r: _edit(r, CATALOGUE_TOML, 'claude-plugin-branch     = "claude-plugins-dist"',
                     'claude-plugin-branch     = "main"')),
    ("marketplace-ref", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE,
                          lambda p: p["plugins"][0]["source"].__setitem__("ref", "attacker-branch"))),
    # the repository anchors
    ("publish-control-repo", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL, lambda p: p.__setitem__("repo", "attacker/evil"))),
    ("marketplace-url", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p["plugins"][0]["source"].__setitem__(
         "url", "https://github.com/attacker/evil.git"))),
    ("marketplace-path", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p["plugins"][0]["source"].__setitem__(
         "path", "credential-brokers"))),
    # the three description anchors
    ("_MARKETPLACE_DESCRIPTION", BUILD_MAIN,
     lambda r: _edit(r, BUILD_MAIN, _LITERAL_DESCRIPTION, '"Something else entirely."')),
    ("catalogue-description", CATALOGUE_TOML,
     lambda r: _edit(r, CATALOGUE_TOML, _LITERAL_DESCRIPTION, '"drifted"')),
    ("marketplace-description", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p.__setitem__("description", "drifted"))),
    # the self_host contract
    ("self-host-default-drifts", SELF_HOST,
     lambda r: _edit(r, SELF_HOST, _LITERAL_DESCRIPTION, '"a different description"')),
    ("self-host-default-computed", SELF_HOST,
     lambda r: _edit(r, SELF_HOST, f"description: str = (\n        {_LITERAL_DESCRIPTION}\n    ),",
                     'description: str = os.environ.get("D", "x"),')),
    ("self-host-caller-passes-description", SELF_HOST,
     lambda r: _edit(
         r, SELF_HOST,
         "_aggregate_marketplace(packs_dir, working_tree, owner=owner, name=marketplace_name)",
         "_aggregate_marketplace(packs_dir, working_tree, owner=owner, "
         'name=marketplace_name, description="x")')),
    ("self-host-dynamic-rebind", SELF_HOST,
     lambda r: _append(r, SELF_HOST, 'globals()["_MARKETPLACE_DESCRIPTION"] = "x"')),
    # the wiring anchors
    ("gate-unwired-from-makefile", MAKEFILE,
     lambda r: _edit(r, MAKEFILE, MAKEFILE_GATE_LINE, "")),
    ("gate-unwired-from-workflow", BUILD_CHECK_WORKFLOW,
     lambda r: _edit(r, BUILD_CHECK_WORKFLOW,
                     "            tools/test_marketplace_envelope_parity.py \\\n", "")),
    ("pytest-lists-diverge", MAKEFILE,
     lambda r: _edit(r, MAKEFILE, "tools/test_contract_parity.py",
                     "tools/test_contract_parity.py tools/test_smuggled.py")),
    # structural failure modes AC7 enumerates
    ("shadow-annassign", BUILD_MAIN,
     lambda r: _append(r, BUILD_MAIN, '_DIST_BRANCH: str = "attacker-branch"')),
    ("shadow-import", BUILD_MAIN,
     lambda r: _append(r, BUILD_MAIN, "from attacker import _DIST_BRANCH")),
    ("shadow-def", BUILD_MAIN,
     lambda r: _append(r, BUILD_MAIN, 'def _DIST_BRANCH():\n    return "attacker-branch"')),
    ("shadow-del", BUILD_MAIN, lambda r: _append(r, BUILD_MAIN, "del _DIST_BRANCH")),
    ("dynamic-setattr-sys-modules", BUILD_MAIN,
     lambda r: _append(r, BUILD_MAIN,
                       'setattr(sys.modules[__name__], "_DIST_BRANCH", "attacker-branch")')),
    ("forged-dunder-file", BUILD_MAIN,
     lambda r: _append(r, BUILD_MAIN, '__file__ = "/forged/path.py"')),
    ("non-literal-value", BUILD_MAIN,
     lambda r: _edit(r, BUILD_MAIN, '_DIST_BRANCH = "claude-plugins-dist"',
                     '_DIST_BRANCH = os.environ.get("B", "claude-plugins-dist")')),
    ("symbol-removed", BUILD_MAIN,
     lambda r: _edit(r, BUILD_MAIN, '_DIST_BRANCH = "claude-plugins-dist"', "")),
    ("unparseable-python", BUILD_MAIN, lambda r: _append(r, BUILD_MAIN, "def (:")),
    ("missing-anchor-file", CATALOGUE_TOML, lambda r: (r / CATALOGUE_TOML).unlink()),
    ("unparseable-json", ROOT_MARKETPLACE,
     lambda r: (r / ROOT_MARKETPLACE).write_text("{not json", encoding="utf-8")),
    ("branch-target-bare-name", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL,
                          lambda p: p["branch"].__setitem__("target", "claude-plugins-dist"))),
    ("branch-target-empty-remainder", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL,
                          lambda p: p["branch"].__setitem__("target", "refs/heads/"))),
    ("branch-target-unsafe-shape", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL, lambda p: p["branch"].__setitem__(
         "target", "refs/heads/--upload-pack=touch"))),
    ("plugins-empty", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p.__setitem__("plugins", []))),
    ("entry-missing-source", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p["plugins"][0].pop("source"))),
    ("entry-missing-name", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda p: p["plugins"][0].pop("name"))),
    ("source-not-git-subdir", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE,
                          lambda p: p["plugins"][0]["source"].__setitem__("source", "github"))),
    ("source-extra-redirect-key", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE,
                          lambda p: p["plugins"][0]["source"].__setitem__("repo", "attacker/evil"))),
    ("source-pins-sha", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE,
                          lambda p: p["plugins"][0]["source"].__setitem__("sha", "deadbeef"))),
    ("duplicate-named-entry", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, _duplicate_entry)),
    # Coordinated attacks. These are the only shapes the ADR-0072 literal pins uniquely
    # catch: move one field alone and downstream parity catches it, so without these the
    # pins could be deleted with every test still green.
    ("coordinated-repo-and-urls", PUBLISH_CONTROL, _coordinated_repo_move),
    ("both-lists-drop-the-gate", MAKEFILE, _drop_gate_from_both_lists),
    # Reader rails AC7 enumerates that no probe reached.
    ("symlinked-anchor", CATALOGUE_TOML, _symlink_anchor),
    ("plugins-not-a-list", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda d: d.__setitem__("plugins", {"a": 1}))),
    ("entry-missing-ref", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda d: d["plugins"][0]["source"].pop("ref"))),
    ("branch-target-not-a-string", PUBLISH_CONTROL,
     lambda r: _edit_json(r, PUBLISH_CONTROL, lambda d: d["branch"].__setitem__("target", 7))),
    ("duplicate-pytest-list-anchor", MAKEFILE,
     lambda r: _append_text(r, MAKEFILE, f"# {PYTEST_LIST_ANCHOR} mentioned again\n\t$(PYTHON) -m pytest {PYTEST_LIST_ANCHOR} -q")),
    ("entry-missing-url", ROOT_MARKETPLACE,
     lambda r: _edit_json(r, ROOT_MARKETPLACE, lambda d: d["plugins"][0]["source"].pop("url"))),
]

#: The refusal each probe must provoke, keyed by probe id.
#:
#: Without this a probe asserted only that *some* failure named the mutated path — and
#: mutation-testing this suite showed 20 of 40 individual refusals could be deleted with
#: every test still green, because a downstream parity check caught the mutation first.
#: Both ADR-0072 literal pins were among the survivors. Requiring the specific message
#: is what makes each probe evidence for its own arm.
_EXPECTED_REFUSAL = {
    "branch-target": _MSG_BRANCH_PIN,
    "publish-control-repo": _MSG_REPO_PIN,
    "publisher-BRANCH": _MSG_BRANCH_PARITY,
    "_DIST_BRANCH": _MSG_BRANCH_PARITY,
    "catalogue-branch": _MSG_BRANCH_PARITY,
    "marketplace-ref": _MSG_BRANCH_PARITY,
    "coordinated-repo-and-urls": _MSG_REPO_PIN,
    "marketplace-url": _MSG_URL_PARITY,
    "marketplace-path": "source.path is",
    "_MARKETPLACE_DESCRIPTION": _MSG_DESCRIPTION_PARITY,
    "catalogue-description": _MSG_DESCRIPTION_PARITY,
    "marketplace-description": _MSG_DESCRIPTION_PARITY,
    "self-host-default-drifts": _MSG_DESCRIPTION_PARITY,
    "self-host-default-computed": _MSG_SELF_HOST_DEFAULT,
    "self-host-caller-passes-description": _MSG_SELF_HOST_CALLER,
    "self-host-dynamic-rebind": "rebind",
    "gate-unwired-from-makefile": _MSG_GATE_MEMBERSHIP,
    "gate-unwired-from-workflow": _MSG_GATE_MEMBERSHIP,
    "pytest-lists-diverge": _MSG_LIST_PARITY,
    "both-lists-drop-the-gate": _MSG_GATE_MEMBERSHIP,
    "forged-dunder-file": _MSG_FORGED_FILE,
    "shadow-annassign": "static bindings",
    "shadow-import": "static bindings",
    "shadow-def": "static bindings",
    "shadow-del": "static bindings",
    "dynamic-setattr-sys-modules": "rebind",
    "non-literal-value": "not a string literal",
    "symbol-removed": "0 static bindings",
    "unparseable-python": "unparseable Python",
    "missing-anchor-file": "missing",
    "unparseable-json": "unparseable JSON",
    "symlinked-anchor": "is a symlink",
    "branch-target-bare-name": "has no 'refs/heads/' prefix",
    "branch-target-empty-remainder": "branch name is empty",
    "branch-target-unsafe-shape": "unsafe or non-ASCII branch name",
    "plugins-empty": "empty or not a list",
    "plugins-not-a-list": "empty or not a list",
    "entry-missing-source": "source is missing or not an object",
    "entry-missing-name": "name is missing or not a string",
    "entry-missing-ref": "ref is missing or not a string",
    "entry-missing-url": "url is missing or not a string",
    "branch-target-not-a-string": "branch.target is not a string",
    "duplicate-pytest-list-anchor": "expected exactly one command naming",
    "source-not-git-subdir": "not 'git-subdir'",
    "source-extra-redirect-key": "unexpected keys",
    "source-pins-sha": "pins a sha",
    "duplicate-named-entry": _MSG_BRANCH_PARITY,
}


def test_unmutated_fixture_passes(tmp_path: Path) -> None:
    """Positive control.

    Without it a probe could go red because the fixture was broken rather than because
    the mutation was detected, and the suite would look like coverage while proving
    nothing.
    """
    check_envelope_parity(_fixture(tmp_path))


@pytest.mark.parametrize(
    ("probe_id", "relative", "mutate"),
    [pytest.param(probe_id, rel, fn, id=probe_id) for probe_id, rel, fn in _MUTATIONS],
)
def test_mutation_is_detected(
    tmp_path: Path, probe_id: str, relative: Path, mutate
) -> None:
    root = _fixture(tmp_path)
    mutate(root)
    expected = _EXPECTED_REFUSAL[probe_id]
    try:
        check_envelope_parity(root)
    except AssertionError as exc:
        message = str(exc)
        assert relative.as_posix() in message, (
            f"the failure must name {relative}; a probe that cannot grep for its own "
            f"source cannot show the mutation was detected for the right reason. "
            f"Got: {message}"
        )
        assert expected in message, (
            f"expected the {expected!r} refusal to fire for probe {probe_id!r}, but the "
            f"failure was: {message}. A probe satisfied by any nearby refusal is not "
            f"evidence that its own arm works."
        )
        return
    raise AssertionError(f"mutation of {relative} was NOT detected")


def test_resolve_is_refused_for_a_fixture_root(tmp_path: Path) -> None:
    """The resolved-value layer reads the tree under audit, not a fixture."""
    with pytest.raises(ParityError, match="live tree"):
        check_envelope_parity(_fixture(tmp_path), resolve=True)


# ---------------------------------------------------------------------------
# Resolved-value layer probes (AC6). A fixture of anchor paths is not an importable
# package, so these copy the package and drive the reader directly.
# ---------------------------------------------------------------------------


def _package_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    shutil.copytree(
        REPO_ROOT / "packages/agentbundle",
        root / "packages/agentbundle",
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
    )
    return root


def test_resolved_read_is_immune_to_an_in_process_plant(tmp_path: Path) -> None:
    """`sys.modules` is the authority behind an in-process import — so don't use one.

    Any module-scope statement in any module of the same pytest command can pre-fill
    the cache, and pytest imports every collected module before running any test, so
    even a plant collected later wins. Reading in a child interpreter is what makes
    that irrelevant; this asserts it stays irrelevant.
    """
    root = _package_fixture(tmp_path)
    honest = resolve_build_main_constants(root)
    plant = types.ModuleType(_BUILD_MAIN_MODULE)
    plant.__file__ = str((root / BUILD_MAIN).resolve())
    plant._DIST_BRANCH = "planted-branch"
    plant._MARKETPLACE_DESCRIPTION = "planted-description"
    original = sys.modules.get(_BUILD_MAIN_MODULE)
    sys.modules[_BUILD_MAIN_MODULE] = plant
    try:
        assert resolve_build_main_constants(root) == honest, "an in-process plant reached the child"
    finally:
        if original is None:
            sys.modules.pop(_BUILD_MAIN_MODULE, None)
        else:
            sys.modules[_BUILD_MAIN_MODULE] = original


@pytest.mark.parametrize(
    "snippet",
    [
        pytest.param('_n = "_DIST" "_BRANCH"\nglobals()[_n] = "attacker-branch"', id="indirect-name"),
        pytest.param('_d = globals()\n_d[\n    "_DIST_BRANCH"\n] = "attacker-branch"', id="split-lines"),
        pytest.param(
            'import pathlib as _p\n'
            '__file__ = str(_p.Path.cwd() / "packages/agentbundle/agentbundle/build/main.py")\n'
            '_DIST_BRANCH = "attacker-branch"',
            id="forged-dunder-file",
        ),
    ],
)
def test_resolved_layer_detects_a_rebind_the_literal_layer_cannot(tmp_path: Path, snippet: str) -> None:
    """Each of these escapes the literal layer; the resolved value does not lie."""
    root = _package_fixture(tmp_path)
    target = root / BUILD_MAIN
    target.write_text(target.read_text(encoding="utf-8") + "\n" + snippet + "\n", encoding="utf-8")
    assert _differs(resolve_build_main_constants(root)["branch"], EXPECTED_BRANCH), (
        "the resolved value agreed with the protected ref despite a rebind"
    )


def test_resolved_layer_refuses_a_str_subclass(tmp_path: Path) -> None:
    root = _package_fixture(tmp_path)
    target = root / BUILD_MAIN
    target.write_text(
        target.read_text(encoding="utf-8")
        + '\nclass _S(str):\n'
        "    def __eq__(self, other): return True\n"
        "    def __ne__(self, other): return False\n"
        "    def __hash__(self): return hash(str(self))\n"
        'globals()["_DIST_BRANCH"] = _S("attacker-branch")\n',
        encoding="utf-8",
    )
    with pytest.raises(ParityError, match="not exactly str"):
        resolve_build_main_constants(root)


def test_resolved_layer_fails_loudly_when_the_package_is_unimportable(tmp_path: Path) -> None:
    """A layer that cannot read must fail, never degrade to a skip.

    Built through `_package_fixture` rather than by planting a lone `main.py`, so the
    fixture is a REGULAR package. A hand-built tree with no `__init__.py` is a PEP 420
    namespace package, and a namespace package loses to a regular one on `sys.path`
    regardless of order — so on any machine with `agentbundle` installed in
    site-packages the child resolved THAT copy and raised the provenance refusal
    instead of the import failure this case is about. The assertion then failed on the
    message, and the whole case only passed where the package happened to be absent.
    """
    root = _package_fixture(tmp_path)
    (root / BUILD_MAIN).write_text("", encoding="utf-8")
    with pytest.raises(ParityError, match="child failed"):
        resolve_build_main_constants(root)


def test_resolved_mismatch_is_refused() -> None:
    """The resolved-vs-literal comparison, driven directly.

    On the live tree these agree by construction, so this seam is the only place the
    comparison can be observed failing.
    """
    assert_resolved_matches(
        {"branch": EXPECTED_BRANCH, "description": "d"}, EXPECTED_BRANCH, "d"
    )
    with pytest.raises(ParityError, match=_MSG_BRANCH_PARITY):
        assert_resolved_matches(
            {"branch": "attacker-branch", "description": "d"}, EXPECTED_BRANCH, "d"
        )
    with pytest.raises(ParityError, match=_MSG_DESCRIPTION_PARITY):
        assert_resolved_matches(
            {"branch": EXPECTED_BRANCH, "description": "drifted"}, EXPECTED_BRANCH, "d"
        )


def test_resolved_layer_refuses_a_module_from_another_tree(tmp_path: Path) -> None:
    """The provenance refusal, in the scenario it exists for.

    When the audited tree does not provide the package, the finder resolves whatever an
    install points at — measured on a real machine, an editable install resolved a
    *sibling worktree of this repository*, so the layer would have validated someone
    else's constant. It must refuse, not reassure.
    """
    root = tmp_path / "no-package-here"
    root.mkdir()  # must exist: it is the child's cwd
    with pytest.raises(ParityError, match="provenance mismatch"):
        resolve_build_main_constants(root)
