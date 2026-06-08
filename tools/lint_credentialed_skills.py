#!/usr/bin/env python3
"""Reports findings against credentialed-skill conventions across the
four broker variants (env / cli / creds / sso-cookie) declared by a
skill's `metadata.auth` field. Exits non-zero on any finding so the
script composes with the existing lint family (lint-agents-md.py,
lint-agent-artifacts.py, etc.); `tools/hooks/pre-pr.py` runs it as
part of the pre-PR gate.

Reference: docs/specs/credential-broker-contract/spec.md (AC24 / AC25).

Extracted from `tools/lint-credentialed-skills.sh`'s embedded Python
heredoc (T15 EXECUTE-time amendment, 2026-05-26) for Windows
portability — bash isn't on PATH on a stock Windows runner and the
heredoc indirection meant `bash` fell through to a missing WSL
distribution. The `.sh` is kept as a thin back-compat shim that
delegates to this `.py`.
"""
from __future__ import annotations

import os
import sys

# Single positional argument: the lint root (directory to scan).
# Falls back to the current working directory if absent so callers
# that just want "lint the repo I'm in" don't have to plumb anything.
if len(sys.argv) >= 2:
    _lint_root_arg = sys.argv[1]
else:
    _lint_root_arg = os.environ.get("LINT_ROOT", ".")
sys.argv = [sys.argv[0], _lint_root_arg]

import ast
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()

# --- Broker-agnostic constants ---------------------------------------

BANNED_FLAGS = {"token", "api_token", "api_key", "bearer", "pat", "password"}

# Dotfile name composed from parts so the lint's own source does not
# carry the literal `.agentbundle/credentials.env` string that the
# rule refuses (`feedback_credentialed_lint_substring_trap`).
DOTFILE_PARENT = "." + "agentbundle"
DOTFILE_BASENAME = "credentials" + ".env"
DOTFILE_SUBSTRING = f"{DOTFILE_PARENT}/{DOTFILE_BASENAME}"
OPTOUT_MARKER = "# credentialed-primitive: reads-creds-directly"

SECURITY_HEADING = "### Security rules (non-negotiable)"

# RFC-0013 § 1 + § 5 — Don't-block phrases keyed by broker.
# Section text is whitespace-normalised before substring search so
# phrases that bullet-wrap across lines still match.
REQUIRED_PHRASES_BY_BROKER = {
    "cli": (
        "**Never** read that store, print it, or echo the token",
        "**Never** put the token on the command line",
        "do not run it for them",
    ),
    "creds": (
        "**Never** read that file, print it, or echo the token",
        "**Never** put the token on the command line",
        "do not run it for them",
    ),
    "env": (
        "**Never** print, log, or echo the value of",
        "**Never** put the credential on the command line",
        "Do not write the value anywhere yourself",
    ),
    "sso-cookie": (
        "**Never** read the jar file directly, print its contents, or echo cookie values",
        "**Never** put a session cookie on the command line",
        "do not run any setup helper for them",
    ),
}

# Shim files (RFC-0013 § 4c) — exempt from the dotfile-substring
# check because they ARE the broker that reads the file. Byte-anchored
# against the canonical source so a hand-rolled file with the same
# basename cannot bypass the rule at lint time.
# Known limitation (security-review round-4 Concern 4, deferred to
# follow-up): the byte-anchor is a lint-time integrity check; runtime
# tampering (a post-install hook mutating the projected shim after the
# lint has read it) is out of scope for this rule. A follow-up would
# either (a) path-anchor the exemption to the canonical projection
# target rather than byte-anchor, or (b) sign the canonical shim and
# verify the signature at build time.
SHIM_BASENAMES = frozenset({
    "credentials_shim.py",
    "_keychain_macos.py",
    "_credman_windows.py",
})
def _resolve_repo_root() -> pathlib.Path:
    """Resolve the repo root via ``git rev-parse``; fall back to
    ``Path.cwd()`` when no git checkout is present. Decouples the
    canonical-shim exemption from the caller's CWD — pytest runners
    that ``os.chdir`` away from the repo root would otherwise silently
    lose the exemption and start reporting the canonical shim files
    themselves as findings."""
    import subprocess as _sp
    try:
        result = _sp.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except (OSError, FileNotFoundError):
        pass
    return pathlib.Path.cwd()


SHIM_SOURCE_DIR = (
    _resolve_repo_root()
    / "packs"
    / "credential-brokers"
    / ".apm"
    / "shared-libs"
)
_shim_source_bytes_cache: dict[str, bytes | None] = {}


def _shim_source_bytes(basename: str) -> bytes | None:
    if basename not in _shim_source_bytes_cache:
        src = SHIM_SOURCE_DIR / basename
        try:
            _shim_source_bytes_cache[basename] = src.read_bytes()
        except OSError:
            _shim_source_bytes_cache[basename] = None
    return _shim_source_bytes_cache[basename]


def _is_canonical_shim(py: pathlib.Path) -> bool:
    if py.name not in SHIM_BASENAMES:
        return False
    expected = _shim_source_bytes(py.name)
    if expected is None:
        return False
    try:
        return py.read_bytes() == expected
    except OSError:
        return False


# SSO broker target path — composed from parts so the lint's own
# source does not carry the literal multi-segment string and trip
# `feedback_credentialed_lint_substring_trap`.
SSO_BROKER_PARENT = "." + "agentbundle"
SSO_BROKER_BIN_DIR = "bin"
SSO_BROKER_BASENAME = "sso-broker" + ".py"
SSO_BROKER_TAIL = (SSO_BROKER_PARENT, SSO_BROKER_BIN_DIR, SSO_BROKER_BASENAME)


# --- Frontmatter parser (single-source from existing impl) ----------

KEY_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
HEADING_TERMINATE_RE = re.compile(r"\n#{1,6}\s")
NESTED_KEY_RE = re.compile(r"^\s+([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
LIST_INLINE_RE = re.compile(r"^\[(.*)\]$")

findings = 0


def relpath(p):
    try:
        return p.relative_to(root)
    except ValueError:
        return p


def report(path, message):
    global findings
    findings += 1
    print(f"✖ {relpath(path)}: {message}", file=sys.stderr)


def parse_inline_list(raw: str) -> list[str] | None:
    """Parse `["a", "b"]` / `['a','b']` inline lists; None on shape mismatch."""
    m = LIST_INLINE_RE.match(raw.strip())
    if m is None:
        return None
    inside = m.group(1).strip()
    if not inside:
        return []
    items = []
    for part in inside.split(","):
        s = part.strip()
        if (
            len(s) >= 2
            and s[0] == s[-1]
            and s[0] in ('"', "'")
        ):
            s = s[1:-1]
        items.append(s)
    return items


def parse_frontmatter(path):
    """Return (fields, body) or (None, text) if frontmatter is absent.

    Minimal stdlib YAML-subset parser matching ``lint-agent-artifacts.py``
    — single-line scalars plus nested mappings under an empty-value
    key (the agentskills.io ``metadata:`` escape hatch shape).
    Inline lists `[a, b]` are parsed as Python lists; the parser
    treats nested values otherwise as strings.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fields: dict[str, object] = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = KEY_RE.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            mapping: dict[str, object] = {}
            block_indent = None
            j = i + 1
            while j < end:
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                indent = len(nxt) - len(nxt.lstrip())
                if indent == 0:
                    break
                if block_indent is None:
                    block_indent = indent
                elif indent != block_indent:
                    report(
                        path,
                        f"malformed frontmatter — doubly-nested "
                        f"mapping under {key!r} at line {j + 1} "
                        f"(parser supports one level of nesting only)"
                    )
                    return None, text
                nm = NESTED_KEY_RE.match(nxt)
                if not nm:
                    break
                nval = nm.group(2).strip()
                if (
                    len(nval) >= 2
                    and nval[0] == nval[-1]
                    and nval[0] in ('"', "'")
                ):
                    nval = nval[1:-1]
                lst = parse_inline_list(nm.group(2).strip())
                if lst is not None:
                    mapping[nm.group(1)] = lst
                else:
                    mapping[nm.group(1)] = nval
                j += 1
            fields[key] = mapping if mapping else ""
            i = j
            continue
        # Top-level value: strip balanced quotes for parity with the
        # nested parse path.
        if (
            len(val) >= 2
            and val[0] == val[-1]
            and val[0] in ('"', "'")
        ):
            val = val[1:-1]
        fields[key] = val
        i += 1
    body = "\n".join(lines[end + 1 :])
    return fields, body


def section_body(body, heading):
    """Slice ``body`` from ``heading`` to the next heading or EOF."""
    idx = body.find(heading)
    if idx < 0:
        return None
    rest = body[idx:]
    m = HEADING_TERMINATE_RE.search(rest, len(heading))
    if m is None:
        return rest
    return rest[: m.start()]


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def normalize_flag(s):
    return s.lstrip("-").casefold().replace("-", "_")


# --- AST helpers -----------------------------------------------------


def _literal_string(node):
    """Return a string if ``node`` reduces to a string literal at
    parse time, ``None`` otherwise. Handles Constant, BinOp(Add)
    chains, JoinedStr with only literal pieces, and Subscript of a
    literal Tuple/List."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string(node.left)
        right = _literal_string(node.right)
        if left is not None and right is not None:
            return left + right
        return None
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                parts.append(piece.value)
                continue
            if isinstance(piece, ast.FormattedValue):
                inner = _literal_string(piece.value)
                if inner is None:
                    return None
                parts.append(inner)
                continue
            return None
        return "".join(parts)
    if isinstance(node, ast.Subscript):
        container = node.value
        if not isinstance(container, (ast.Tuple, ast.List)):
            return None
        slice_node = node.slice
        if not (
            isinstance(slice_node, ast.Constant)
            and isinstance(slice_node.value, int)
        ):
            return None
        if not (0 <= slice_node.value < len(container.elts)):
            return None
        return _literal_string(container.elts[slice_node.value])
    return None


def _starred_first_literal(node):
    if not isinstance(node, ast.Starred):
        return None
    inner = node.value
    if not isinstance(inner, (ast.Tuple, ast.List)) or not inner.elts:
        return None
    return _literal_string(inner.elts[0])


def add_argument_flags(py_path):
    """Yield (raw, normalised, lineno) for each first-arg flag literal
    AND for each `dest=<banned-name>` keyword argument. The `dest=`
    branch catches the evasion `parser.add_argument("--xyzzy",
    dest="token")` where the user-facing flag name is innocuous but
    the resolved attribute name leaks the credential — `args.token`
    is still credential-shaped at runtime."""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"),
                         filename=str(py_path))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue
        if not node.args:
            continue
        first = node.args[0]
        value = _literal_string(first)
        if value is None:
            value = _starred_first_literal(first)
        if value is not None and value.startswith("-"):
            yield value, normalize_flag(value), node.lineno
        # dest= keyword check — argparse exposes args.<dest> regardless of
        # the visible flag name. A banned dest leaks the credential just
        # as much as a banned flag does.
        for kw in node.keywords:
            if kw.arg != "dest":
                continue
            dest_value = _literal_string(kw.value)
            if dest_value is None:
                continue
            yield f"dest={dest_value!r}", normalize_flag(dest_value), node.lineno


def _ast_for(py_path):
    try:
        return ast.parse(py_path.read_text(encoding="utf-8"),
                         filename=str(py_path))
    except (OSError, SyntaxError):
        return None


def has_credentials_shim_import(py_path):
    """True iff *py_path* contains `from ... credentials_shim import …`
    or `import credentials_shim`."""
    tree = _ast_for(py_path)
    if tree is None:
        return False
    target_module = "credentials" + "_shim"  # avoid literal trap
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == target_module:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target_module:
                    return True
    return False


def has_credbroker_import(py_path):
    """True iff *py_path* imports the `credbroker` resolver — `from credbroker
    import …` (or a submodule) or `import credbroker`.

    RFC-0023 replaces the build-projected `credentials_shim` sibling with the
    pip-installable `credbroker` library; an `auth: creds` consumer satisfies
    the resolver-import requirement with either form during (and after) the
    migration.
    """
    tree = _ast_for(py_path)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "credbroker":
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "credbroker":
                    return True
    return False


def env_reads(py_path):
    """Yield literal env-var names read via os.environ[...] /
    os.environ.get(...) / os.getenv(...). Only first-arg
    Constant(str) shapes count — declarations must be explicit."""
    tree = _ast_for(py_path)
    if tree is None:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            container = node.value
            # os.environ["NAME"]
            if (
                isinstance(container, ast.Attribute)
                and container.attr == "environ"
                and isinstance(container.value, ast.Name)
                and container.value.id == "os"
            ):
                slice_node = node.slice
                if (
                    isinstance(slice_node, ast.Constant)
                    and isinstance(slice_node.value, str)
                ):
                    yield slice_node.value
        if isinstance(node, ast.Call):
            func = node.func
            # os.environ.get("NAME") / os.getenv("NAME")
            if isinstance(func, ast.Attribute):
                if (
                    func.attr == "get"
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "environ"
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "os"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) \
                            and isinstance(node.args[0].value, str):
                        yield node.args[0].value
                elif (
                    func.attr == "getenv"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "os"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) \
                            and isinstance(node.args[0].value, str):
                        yield node.args[0].value


def _path_chain_components(node):
    """Resolve `Path.home() / "a" / "b"` BinOp chains into the leftmost
    seed marker + accumulated components.

    Returns a tuple ``(seed_kind, components)`` where ``seed_kind`` is
    one of ``"home"`` (resolved Path.home() / Path("~").expanduser() /
    os.path.expanduser("~")), ``"absolute"`` (string literal absolute
    path), ``"relative"`` (string literal relative path), or ``None``
    if the chain cannot be resolved.

    ``components`` are the path tail components collected from the
    right side of the chain plus the seed itself when relevant.
    """
    # Strip a wrapping str(...) call for the common `str(Path.home() / ...)`
    # shape.
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "str" and len(node.args) == 1:
        return _path_chain_components(node.args[0])
    components: list[str] = []
    cur = node
    # Walk down `BinOp(Div)` chains, collecting right-hand string
    # literals.
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = _literal_string(cur.right)
        if right is None:
            return None, []
        components.insert(0, right)
        cur = cur.left
    # cur is now the leftmost seed.
    if isinstance(cur, ast.Call):
        callee = cur.func
        # Path.home()
        if isinstance(callee, ast.Attribute) and callee.attr == "home" \
                and isinstance(callee.value, ast.Name) and callee.value.id == "Path":
            return "home", components
        # os.path.expanduser("~")
        if isinstance(callee, ast.Attribute) and callee.attr == "expanduser" \
                and isinstance(callee.value, ast.Attribute) \
                and callee.value.attr == "path" \
                and isinstance(callee.value.value, ast.Name) \
                and callee.value.value.id == "os":
            if cur.args and isinstance(cur.args[0], ast.Constant) \
                    and cur.args[0].value == "~":
                return "home", components
        # Path("~").expanduser()
        if isinstance(callee, ast.Attribute) and callee.attr == "expanduser" \
                and isinstance(callee.value, ast.Call) \
                and isinstance(callee.value.func, ast.Name) \
                and callee.value.func.id == "Path":
            args = callee.value.args
            if args and isinstance(args[0], ast.Constant) and args[0].value == "~":
                return "home", components
    # String-literal seed (e.g. "/opt/foo" / "bar" or "rel/path")
    seed_literal = _literal_string(cur)
    if seed_literal is not None:
        # If the seed is an absolute path, components are seed.parts + collected
        seed_path = pathlib.PurePosixPath(seed_literal)
        seed_components = list(seed_path.parts)
        kind = "absolute" if seed_path.is_absolute() else "relative"
        return kind, seed_components + components
    return None, []


def sso_broker_call_targets(py_path):
    """Yield `(seed_kind, components, lineno)` for every path-chain
    expression in *py_path* — i.e. every `Path.home() / "x" / "y"`
    BinOp chain or `str(...)` of same, plus every string-literal path.

    AC25 names `subprocess.run` as the canonical call site for the
    sso-cookie broker, but in practice authors assign the resolved
    path to a local name (`broker = str(Path.home() / ".agentbundle"
    / "bin" / "sso-broker.py")`) and pass the *name* to
    `subprocess.run`. Tracking every assignment statement would
    duplicate Python's scoping for marginal added precision; instead
    the lint surveys path chains module-wide and pairs them with a
    separate `subprocess.run` existence check (`has_subprocess_run`).
    The combined check catches the architectural rule without
    requiring inline call-site forms."""
    tree = _ast_for(py_path)
    if tree is None:
        return
    # Track nodes already resolved as part of a larger BinOp chain so
    # the walk doesn't emit duplicate findings for the chain's
    # intermediates. Without this, a `Path.home() / "x" / "y"`
    # expression yields three results (the full chain plus two
    # partials) — only the full chain matters for the rule.
    consumed: set[int] = set()

    def _consume_descendants(node):
        for child in ast.walk(node):
            consumed.add(id(child))

    for node in ast.walk(tree):
        if id(node) in consumed:
            continue
        seed_kind, components = _path_chain_components(node)
        if seed_kind is None:
            continue
        if not components:
            continue
        _consume_descendants(node)
        lineno = getattr(node, "lineno", 0)
        yield seed_kind, tuple(components), lineno


def disallowed_subprocess_calls(py_path):
    """Yield `(name, lineno)` for every `subprocess.Popen`, `os.system`,
    or `os.exec*` call. `auth: sso-cookie` consumers are restricted to
    `subprocess.run` against the broker; the others widen the
    exfiltration surface (Popen's stdin/stdout pipes, os.system's
    shell-string interpolation, exec*'s in-process replacement).
    Refusing them in the lint shrinks the exfil window if a consumer's
    broker invocation is a decoy.

    Handles both attribute-access shapes (`subprocess.Popen(...)`,
    `os.system(...)`) and import-alias shapes
    (`from subprocess import Popen as P; P(...)`, `from os import
    system as s; s(...)`) — the same alias-evasion shape that
    `has_subprocess_run` defends against."""
    tree = _ast_for(py_path)
    if tree is None:
        return
    aliases: dict[str, str] = {}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            local = alias.asname or alias.name
            if node.module == "subprocess" and alias.name == "Popen":
                aliases[local] = "subprocess.Popen"
            elif node.module == "os" and (
                alias.name == "system" or alias.name.startswith("exec")
            ):
                aliases[local] = f"os.{alias.name}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            base = func.value
            attr = func.attr
            if isinstance(base, ast.Name):
                if base.id == "subprocess" and attr == "Popen":
                    yield f"subprocess.{attr}", node.lineno
                elif base.id == "os" and (attr == "system" or attr.startswith("exec")):
                    yield f"os.{attr}", node.lineno
        elif isinstance(func, ast.Name):
            canonical = aliases.get(func.id)
            if canonical is not None:
                yield canonical, node.lineno


def has_subprocess_run(py_path):
    """True iff *py_path* contains `subprocess.run(...)`, or `run(...)`
    where `run` was imported from `subprocess` in the same module.

    The fallback branch is gated on a same-file `from subprocess import
    run [as <alias>]` so an unrelated callable named `run` (a local
    helper, `pytest.main`, …) cannot satisfy the rule. Without this
    gate, an `auth: sso-cookie` consumer that lacks a broker
    invocation but happens to call any function called `run` would
    pass — defeating AC25's "consumer must invoke sso-broker.py via
    subprocess" promise."""
    tree = _ast_for(py_path)
    if tree is None:
        return False
    run_aliases: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name == "run":
                    run_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "run":
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                return True
        elif isinstance(func, ast.Name) and func.id in run_aliases:
            return True
    return False


def imports_playwright(py_path):
    tree = _ast_for(py_path)
    if tree is None:
        return False
    target = "playwright"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and \
                node.module.split(".")[0] == target:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == target:
                    return True
    return False


def denyset_flag_groups(py_path):
    """Yield, per set/list/tuple literal, the set of normalize_flag'd
    flag-shaped string elements. A hand-maintained token deny-set
    (``TOKEN_CLI_FLAGS = frozenset({...})`` / ``_ARGV_BAN = {...}`` / a list
    or tuple) shows up as one such group, name-agnostically; the caller
    identifies the deny-set as a group carrying >= 2 canonical banned flags
    so an incidental set that merely mentions one token-shaped flag isn't
    mistaken for one. ``ast.walk`` visits the inner ``Set``/``List`` of a
    ``frozenset({...})`` / ``frozenset([...])`` directly, so no Call handling
    is needed — which also avoids double-counting the same literal."""
    tree = _ast_for(py_path)
    if tree is None:
        return
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            continue
        flags = set()
        for el in node.elts:
            s = _literal_string(el)
            if s is not None and s.startswith("-"):
                flags.add(normalize_flag(s))
        if flags:
            yield flags


def has_scrubbing_parser(py_path):
    """True iff the file defines an ``argparse.ArgumentParser`` subclass that
    overrides ``error()`` — the value-scrubbing backstop that keeps a
    token-shaped flag outside the deny-set from having its value echoed by
    argparse's stock error message.

    Structural check only: it confirms an ``error()`` override *exists*, not
    that it actually scrubs. The scrubbing behavior itself is verified by the
    CLIs' token smoke tests + manual A/B, not here; this is the source-level
    drift sentinel that the backstop wasn't deleted."""
    tree = _ast_for(py_path)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_is_argparse = any(
            (isinstance(b, ast.Attribute) and b.attr == "ArgumentParser")
            or (isinstance(b, ast.Name) and b.id == "ArgumentParser")
            for b in node.bases
        )
        if base_is_argparse and any(
            isinstance(m, ast.FunctionDef) and m.name == "error"
            for m in node.body
        ):
            return True
    return False


# --- Main scan -------------------------------------------------------

skill_md_files = []
for pattern in (
    ".claude/skills/*/SKILL.md",
    "packs/*/.apm/skills/*/SKILL.md",
    "skills/*/SKILL.md",
):
    skill_md_files.extend(sorted(root.glob(pattern)))

scanned = 0

for skill_md in skill_md_files:
    fields, body = parse_frontmatter(skill_md)
    if fields is None:
        continue
    metadata = fields.get("metadata")
    if not isinstance(metadata, dict):
        continue
    # Local YAML-subset parser stores everything as strings; a future
    # real-YAML upgrade would emit bools — normalise both sides so
    # the rule survives a parser swap without silently going dormant.
    if str(metadata.get("credentialed", "")).strip().lower() != "true":
        continue
    scanned += 1

    primitive_class = metadata.get("primitive-class", "")
    auth = metadata.get("auth", "") or ""
    namespace = metadata.get("namespace", "") or ""
    keys = metadata.get("keys", [])
    if isinstance(keys, str):
        # Fallback for non-inline shape — empty or unparsed
        keys = []

    skill_dir = skill_md.parent

    # --- Broker-agnostic D1: Don't-block presence ---------------
    section = section_body(body, SECURITY_HEADING)
    if section is None:
        report(skill_md, f"missing heading: {SECURITY_HEADING}")
    else:
        normalised = normalize_whitespace(section)
        phrases = REQUIRED_PHRASES_BY_BROKER.get(auth)
        if phrases is None:
            # Skill declares an unknown auth value — refused upstream
            # by lint-agent-artifacts.py (AC26), but be defensive.
            report(
                skill_md,
                f"unknown metadata.auth={auth!r} "
                f"(expected one of {sorted(REQUIRED_PHRASES_BY_BROKER)})",
            )
        else:
            for phrase in phrases:
                if normalize_whitespace(phrase) not in normalised:
                    report(
                        skill_md,
                        f"security section missing required phrase "
                        f"for broker {auth!r}: {phrase!r}",
                    )

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        continue

    py_files = sorted(p for p in scripts_dir.rglob("*.py") if p.is_file())

    # --- Broker-agnostic D2: argv ban (credentialed-cli) --------
    if primitive_class == "credentialed-cli":
        for py in py_files:
            for raw, norm, lineno in add_argument_flags(py):
                if norm in BANNED_FLAGS:
                    report(
                        py,
                        f"line {lineno}: argv-borne credential flag "
                        f"{raw!r} accepted by argparse (normalised "
                        f"{norm!r} ∈ {sorted(BANNED_FLAGS)})",
                    )

        # --- D2b: deny-set completeness + scrubbing backstop --------
        # A token deny-set is a set/list/tuple literal carrying >= 2 of the
        # canonical banned flags. The >= 2 floor keeps an incidental literal
        # that merely mentions one token-shaped flag (e.g. an MCP header set)
        # from being mistaken for a deny-set. Conditional on such a deny-set
        # being present, so D2b never fires on minimal/unrelated scripts —
        # which means a credentialed-cli that ships NO deny-set at all is not
        # covered here (D2a's add_argument ban is the floor for that case).
        # When a deny-set is present it must (a) carry ALL the canonical six
        # — catching the drift where a consumer silently drops one — and
        # (b) be backed by a value-scrubbing ArgumentParser, so a token-shaped
        # flag OUTSIDE the deny-set doesn't have its value echoed by error().
        token_denysets = [
            g
            for py in py_files
            for g in denyset_flag_groups(py)
            if len(g & BANNED_FLAGS) >= 2
        ]
        if token_denysets:
            present = set().union(*token_denysets)
            missing = sorted(BANNED_FLAGS - present)
            if missing:
                report(
                    skill_md,
                    f"token deny-set is incomplete — missing canonical "
                    f"banned flag(s) {missing}; the argv ban requires all of "
                    f"{sorted(BANNED_FLAGS)}",
                )
            if not any(has_scrubbing_parser(py) for py in py_files):
                report(
                    skill_md,
                    "ships a token deny-set but no value-scrubbing "
                    "ArgumentParser subclass (one overriding error()); a "
                    "token-shaped flag outside the deny-set would have its "
                    "value echoed verbatim by argparse's error message",
                )

    # --- Broker-agnostic D3: dotfile read ----------------------
    for py in py_files:
        if _is_canonical_shim(py):
            continue
        try:
            content = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if DOTFILE_SUBSTRING not in line:
                continue
            if OPTOUT_MARKER in line.rstrip():
                continue
            report(
                py,
                f"line {lineno}: skill reads {DOTFILE_SUBSTRING} directly "
                f"(architectural violation — opt-out marker absent)",
            )

    # --- AC25 broker-specific AST walks ------------------------
    # Skip the canonical shim files themselves when checking consumer-
    # side imports / reads — they are the broker, not the consumer.
    consumer_py_files = [p for p in py_files if not _is_canonical_shim(p)]

    if auth == "creds":
        # RFC-0023: the `creds` resolver may be the pip-installable `credbroker`
        # library or the legacy build-projected `credentials_shim` sibling.
        # Accept either import form (consumers migrate skill-by-skill).
        found_resolver_import = any(
            has_credentials_shim_import(p) or has_credbroker_import(p)
            for p in consumer_py_files
        )
        if not found_resolver_import:
            target = "credentials" + "_shim"
            report(
                skill_md,
                f"auth=creds requires at least one credential-resolver import "
                f"in scripts/ — `from credbroker import …` (RFC-0023) or the "
                f"legacy `from .{target} import …` — none found",
            )

    elif auth == "env":
        # Schema requires namespace + keys.
        if not namespace:
            report(skill_md, "auth=env requires metadata.namespace")
        if not keys:
            report(skill_md, "auth=env requires metadata.keys (non-empty list)")
        if namespace and keys:
            reads = set()
            for p in consumer_py_files:
                reads.update(env_reads(p))
            # Env-name shape matches the shim's `_tier1_env` / `_dotfile_env_name`
            # convention: uppercase the *namespace*, leave the *key* as-declared.
            # Today every consumer schema uses uppercase key names, but a
            # future `keys: ["api_token"]` schema would otherwise have the
            # lint expect `FOO_API_TOKEN` and the shim resolve `FOO_api_token`.
            ns_prefix = str(namespace).upper()
            for key in keys:
                expected = f"{ns_prefix}_{str(key)}"
                if expected not in reads:
                    report(
                        skill_md,
                        f"auth=env declares key {key!r} under namespace "
                        f"{namespace!r}; expected env read of "
                        f"{expected!r} not found in scripts/",
                    )

    elif auth == "sso-cookie":
        targets_home = False
        any_subprocess_run = False
        for p in consumer_py_files:
            for bad_name, lineno in disallowed_subprocess_calls(p):
                report(
                    p,
                    f"line {lineno}: auth=sso-cookie consumer uses "
                    f"{bad_name}(...) — only subprocess.run is permitted "
                    f"(Popen / os.system / os.exec* widen the exfiltration "
                    f"surface; the broker is invoked via subprocess.run only)",
                )
            if imports_playwright(p):
                report(
                    p,
                    "auth=sso-cookie consumer imports Playwright directly "
                    "(broker dependency only; consumers invoke "
                    "sso-broker.py via subprocess)",
                )
            if has_subprocess_run(p):
                any_subprocess_run = True
            for seed_kind, components, lineno in sso_broker_call_targets(p):
                tail3 = tuple(components[-3:])
                matches_target = tail3 == SSO_BROKER_TAIL
                ends_in_basename = (
                    components and components[-1] == SSO_BROKER_BASENAME
                )
                if matches_target and seed_kind == "home":
                    targets_home = True
                elif ends_in_basename and seed_kind == "absolute":
                    report(
                        p,
                        f"line {lineno}: auth=sso-cookie path expression "
                        f"targets hard-coded absolute path "
                        f"({'/'.join(components)!r}); use "
                        f"Path.home() / {DOTFILE_PARENT!r} / "
                        f"{SSO_BROKER_BIN_DIR!r} / {SSO_BROKER_BASENAME!r}",
                    )
        if not targets_home:
            report(
                skill_md,
                f"auth=sso-cookie requires a path expression resolving to "
                f"Path.home() / {DOTFILE_PARENT!r} / "
                f"{SSO_BROKER_BIN_DIR!r} / {SSO_BROKER_BASENAME!r} "
                f"in scripts/ (none found)",
            )
        elif not any_subprocess_run:
            report(
                skill_md,
                "auth=sso-cookie requires a subprocess.run call in scripts/ "
                "(broker path resolved but no subprocess.run found)",
            )

    elif auth == "cli":
        # No positive-grep enforcement; broker-agnostic checks above
        # already covered.
        pass

print(f"Credentialed-skill lint: {scanned} skill(s) scanned, "
      f"{findings} finding(s).")

if findings:
    sys.exit(1)
