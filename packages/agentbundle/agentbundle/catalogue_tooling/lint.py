"""Portable catalogue lint engine.

Entry point: lint_catalogue(root, pack=None) -> LintResult

Rules split into three tiers:
  - Catalogue-level (_CatalogueRules): presence, duplicates, config paths
  - Pack-level (_PackRules): per-pack TOML/JSON/frontmatter/metadata checks
  - Portability (via lint_packs.lint_pack): symlinks, Windows-poisonous names

All rules are read-only. No file is written during a lint run.
Output sorted by (pack, path, line, col, code).
"""

from __future__ import annotations

import ast
import json
import os
import re
import tomllib
from pathlib import Path

from agentbundle.build.self_host import projects_claude_artifacts
from agentbundle.catalogue_tooling.config import (
    CatalogueConfig,
    CatalogueConfigError,
    load_catalogue_config,
)
from agentbundle.catalogue_tooling.diagnostics import DiagnosticCode
from agentbundle.catalogue_tooling.manifest import plugin_json_path
from agentbundle.catalogue_tooling.results import Diagnostic, LintResult, Severity

# Frontmatter regex: matches the YAML front-matter block at the top of a file
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Required SKILL.md frontmatter keys
_SKILL_REQUIRED_KEYS = ("name", "description")

# Agent frontmatter required keys
_AGENT_REQUIRED_KEYS = ("name", "description")

# Adapter names cache
_ADAPTER_NAMES: frozenset[str] | None = None

# Allowed scope values per adapter contract
_ALLOWED_SCOPES = frozenset({"repo", "user"})

# Max lengths from lint_packs
_MAX_NAME_LEN = 64
_MAX_DESC_LEN = 1024

# Primitive name pattern
_PRIM_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_AGENTBUNDLE_VERSION: str | None = None


def _get_agentbundle_version() -> str:
    global _AGENTBUNDLE_VERSION
    if _AGENTBUNDLE_VERSION is None:
        try:
            from agentbundle import __version__
            _AGENTBUNDLE_VERSION = __version__
        except Exception:
            _AGENTBUNDLE_VERSION = "unknown"
    return _AGENTBUNDLE_VERSION


def _get_adapter_names() -> frozenset[str]:
    global _ADAPTER_NAMES
    if _ADAPTER_NAMES is None:
        try:
            from agentbundle.catalogue_tooling.config import _load_adapter_names
            _ADAPTER_NAMES = _load_adapter_names()
        except Exception:
            _ADAPTER_NAMES = frozenset()
    return _ADAPTER_NAMES


def _diag(
    code: DiagnosticCode,
    severity: Severity,
    message: str,
    *,
    pack: str | None = None,
    path: str | None = None,
    line: int | None = None,
    col: int | None = None,
    remediation: str | None = None,
) -> Diagnostic:
    return Diagnostic(
        code=code.value,
        severity=severity,
        pack=pack,
        path=path,
        line=line,
        col=col,
        message=message,
        remediation=remediation,
    )


def _sort_key(d: Diagnostic) -> tuple:
    return (d.pack or "", d.path or "", d.line or 0, d.col or 0, d.code)


def _load_pack_schema() -> dict | None:
    try:
        from importlib.resources import files
        resource = files("agentbundle").joinpath("_data/pack.schema.json")
        if resource.is_file():
            return json.loads(resource.read_text(encoding="utf-8"))
    except Exception:
        pass
    here = Path(__file__).resolve()
    schema_path = here.parents[1] / "_data" / "pack.schema.json"
    if schema_path.exists():
        try:
            return json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse YAML-style frontmatter from a markdown file. Returns None if absent."""
    m = _FM_RE.match(text)
    if not m:
        return None
    fields: dict[str, str] = {}
    for raw_line in m.group(1).splitlines():
        if ":" in raw_line:
            k, _, v = raw_line.partition(":")
            fields[k.strip()] = v.strip()
    return fields


# ---------------------------------------------------------------------------
# Profile lint helpers
# ---------------------------------------------------------------------------

_PROFILE_CARET_RE = re.compile(r"^\^([0-9]+)\.([0-9]+)$")


def _profile_allowed_scopes(pack_toml: dict) -> list[str]:
    install = pack_toml.get("pack", {}).get("install")
    if isinstance(install, dict):
        scopes = install.get("allowed-scopes")
        if isinstance(scopes, list) and scopes:
            return [s for s in scopes if isinstance(s, str)]
        default = install.get("default-scope")
        if isinstance(default, str):
            return [default]
    return ["repo"]


def _profile_required_deps(pack_toml: dict) -> list[tuple[str, str]]:
    deps = pack_toml.get("pack", {}).get("dependencies", {})
    out: list[tuple[str, str]] = []
    if isinstance(deps, dict):
        for entry in deps.get("required") or []:
            if isinstance(entry, dict):
                out.append((entry.get("pack", ""), entry.get("version", "")))
    return out


def _profile_satisfies(installed_version: str, dep_range: str) -> bool | None:
    """``^X.Y`` caret-minor satisfaction check. None = unsupported range grammar."""
    m = _PROFILE_CARET_RE.match(dep_range)
    if m is None:
        return None
    req_major, req_minor = int(m.group(1)), int(m.group(2))
    parts = installed_version.split(".")
    try:
        ima = int(parts[0]) if len(parts) > 0 else 0
        imi = int(parts[1]) if len(parts) > 1 else 0
        ipa = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return False
    return ima == req_major and (imi > req_minor or (imi == req_minor and ipa >= 0))


def _profile_load_packs(packs_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not packs_dir.is_dir():
        return out
    for pack_dir in sorted(packs_dir.iterdir()):
        if pack_dir.name.startswith("_"):
            continue  # reserved authoring asset
        toml_path = pack_dir / "pack.toml"
        if not toml_path.exists():
            continue
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            continue
        name = data.get("pack", {}).get("name") or pack_dir.name
        out[name] = data
    return out


def _profile_lint_one(profile_id: str, raw: dict, packs: dict[str, dict]) -> list[str]:
    violations: list[str] = []
    scope = raw.get("scope")
    if scope not in ("user", "repo"):
        violations.append(
            f"profile {profile_id!r}: scope must be 'user' or 'repo', got {scope!r}"
        )
    entries = raw.get("packs")
    if not isinstance(entries, list) or not entries:
        violations.append(f"profile {profile_id!r}: 'packs' must be a non-empty list")
        return violations

    names = [e.get("pack") for e in entries if isinstance(e, dict) and e.get("pack")]
    index = {name: i for i, name in enumerate(names)}

    for i, name in enumerate(names):
        pack_toml = packs.get(name)
        if pack_toml is None:
            violations.append(f"profile {profile_id!r}: pack {name!r} not found in packs/")
            continue
        if scope in ("user", "repo"):
            allowed = _profile_allowed_scopes(pack_toml)
            if scope not in allowed:
                violations.append(
                    f"profile {profile_id!r}: pack {name!r} does not allow scope "
                    f"{scope!r} (allowed-scopes: {allowed})"
                )
        for dep_name, dep_range in _profile_required_deps(pack_toml):
            if dep_name not in index:
                violations.append(
                    f"profile {profile_id!r}: pack {name!r} requires {dep_name!r} "
                    f"({dep_range}), which is not in the profile (dependency-incomplete)"
                )
                continue
            if index[dep_name] >= i:
                violations.append(
                    f"profile {profile_id!r}: pack {dep_name!r} (required by "
                    f"{name!r}) is listed at or after it; required deps must come "
                    f"first (mis-ordered)"
                )
            dep_toml = packs.get(dep_name)
            if dep_toml is not None:
                dep_version = dep_toml.get("pack", {}).get("version", "")
                sat = _profile_satisfies(dep_version, dep_range)
                if sat is None:
                    violations.append(
                        f"profile {profile_id!r}: pack {name!r} declares an "
                        f"unsupported version range {dep_range!r} for {dep_name!r} "
                        f"(only ^X.Y is supported)"
                    )
                elif sat is False:
                    violations.append(
                        f"profile {profile_id!r}: pack {name!r} requires "
                        f"{dep_name!r} {dep_range}, but the catalogue ships "
                        f"{dep_name} v{dep_version}, which does not satisfy it "
                        f"(dependency-incomplete)"
                    )
    return violations


# ---------------------------------------------------------------------------
# Seeds lint helpers
# ---------------------------------------------------------------------------

_SEEDS_BLOCKLIST_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"agent-ready-repo", "catalogue name 'agent-ready-repo'"),
    (r"RFC-00\d\d", "catalogue RFC reference (RFC-NNNN)"),
    (r"K-00\d\d", "catalogue knowledge entry (K-NNNN)"),
    (
        r"\b("
        r"distribution-adapters|self-hosting|agent-spec-cli|"
        r"user-scope-hooks|converters-pack|"
        r"claude-plugins-install-route|codex-native-skills|"
        r"apm-install-route-parity|skill-secrets|wire-session-start-hook|"
        r"kiro-ide-hook|windows-ci-bundler|windows-hooks-phase3"
        r")\b",
        "catalogue spec name",
    ),
)
_SEEDS_BLOCKLIST_RE = [(re.compile(p), name) for p, name in _SEEDS_BLOCKLIST_PATTERNS]

_SEEDS_REQUIRED_PLACEHOLDERS: dict[str, tuple[str, ...]] = {
    "docs/CHARTER.md": ("<replace with one sentence>", "<bullet>", "<principle>"),
    "docs/architecture/overview.md": (
        "<list your packs and packages here>", "<app-name>", "<package-name>",
    ),
    "docs/specs/README.md": ("<!-- no specs yet -->",),
    "docs/knowledge/patterns.jsonl": (),
    "docs/rfc/README.md": ("<!-- no RFCs yet -->",),
    "docs/adr/README.md": ("<!-- no ADRs yet -->",),
    "governance/manifest.example.yaml": ("ADR-NNNN",),
    "docs/architecture/README.md": (),
    "docs/knowledge/README.md": (),
    "docs/product/README.md": (),
    "docs/product/roadmap.md": ("YYYY-MM-DD",),
    "docs/product/changelog.md": ("pack-name][version",),
    "docs/product/briefs/_template.md": ("<slug>", "<one-line outcome>"),
    "workspace.toml": ("[backlog]",),
    "docs/CONVENTIONS.md": (),
    "AGENTS.md": ("<project-name>",),
    "guides/README.md": (),
    "guides/tutorials/README.md": (),
    "guides/how-to/README.md": (),
    "guides/reference/README.md": (),
    "guides/explanation/README.md": (),
    "packages/README.md": (),
    "packages/_example/README.md": ("`_example`",),
    "packages/_example/AGENTS.md": ("placeholder package",),
    ".gitignore": (),
    "_agents-footer.md": (),
}

_SEEDS_SENTINEL_RE = re.compile(
    r"^\s*<!--\s*seed-content-lint-ignore:\s*([^>]+?)\s*-->\s*$"
)
_SEEDS_FENCE_RE = re.compile(r"^\s*```")


def _seeds_is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or (s.startswith("<!--") and s.endswith("-->"))


def _seeds_check_file(path: Path, seeds_root: Path) -> list[str]:
    """Return violation strings for one seed file (empty list = clean).

    Byte-identical message strings to the original standalone seeds linter EXCEPT
    the fail-loud unknown-seed message, which references
    lint.py (_PackRules._check_seeds).
    """
    violations: list[str] = []
    try:
        relative = path.relative_to(seeds_root).as_posix()
    except ValueError:
        return [f"{path}: not under a seeds_root"]

    if relative not in _SEEDS_REQUIRED_PLACEHOLDERS:
        return [
            f"{path}: unknown seed file — declare its expected "
            "placeholder shape in lint.py (_PackRules._check_seeds):_SEEDS_REQUIRED_PLACEHOLDERS, "
            "or remove the file. (Fail-loud policy: every seed under "
            "packs/<pack>/seeds/ must have a declared shape.)"
        ]

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    if relative == "docs/knowledge/patterns.jsonl":
        if content.strip():
            violations.append(
                f"{path}:1: patterns.jsonl seed must be empty "
                "(no entries at seed time; adopters' knowledge entries "
                "accumulate post-install)"
            )
        return violations

    required = _SEEDS_REQUIRED_PLACEHOLDERS[relative]
    if required and not any(token in content for token in required):
        violations.append(
            f"{path}: required placeholder missing — expected at least "
            f"one of: {', '.join(repr(t) for t in required)}. "
            "Seeds are scaffold; restore placeholder shape."
        )

    lines = content.splitlines()
    pending_sentinel = False
    pending_sentinel_lineno = 0
    pending_sentinel_reason = ""
    in_fence = False

    for lineno, raw_line in enumerate(lines, start=1):
        if _SEEDS_FENCE_RE.match(raw_line):
            in_fence = not in_fence
            pending_sentinel = False
            continue
        if in_fence:
            continue
        sentinel_match = _SEEDS_SENTINEL_RE.match(raw_line)
        if sentinel_match:
            if pending_sentinel:
                violations.append(
                    f"{path}:{lineno}: stacked sentinel (previous on "
                    f"line {pending_sentinel_lineno}; pick one)"
                )
                pending_sentinel = False
            else:
                pending_sentinel = True
                pending_sentinel_lineno = lineno
                pending_sentinel_reason = sentinel_match.group(1)
            continue
        if _seeds_is_blank_or_comment(raw_line):
            continue
        if pending_sentinel:
            pending_sentinel = False
            continue
        for regex, name in _SEEDS_BLOCKLIST_RE:
            if regex.search(raw_line):
                violations.append(
                    f"{path}:{lineno}: contains {name} — pack seeds must "
                    "be placeholder shape. "
                    "Add a `<!-- seed-content-lint-ignore: <reason> -->` "
                    "sentinel immediately above the line if the catalogue "
                    "string is genuinely required."
                )
    if pending_sentinel:
        violations.append(
            f"{path}:{pending_sentinel_lineno}: trailing sentinel "
            f"(reason={pending_sentinel_reason!r}) — no content line "
            "follows; remove the sentinel."
        )
    return violations


# ---------------------------------------------------------------------------
# First-value lint helpers
# ---------------------------------------------------------------------------

_FV_AUDIENCE_POSTURES = frozenset({"non-technical", "mixed", "technical"})
_FV_PLACEHOLDER_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9 _-]*>")


# ---------------------------------------------------------------------------
# Credentialed-skill AST helpers
# ---------------------------------------------------------------------------

_CS_BANNED_FLAGS = frozenset({"token", "api_token", "api_key", "bearer", "pat", "password"})
_CS_DOTFILE_PARENT = "." + "agentbundle"
_CS_DOTFILE_BASENAME = "credentials" + ".env"
_CS_DOTFILE_SUBSTRING = f"{_CS_DOTFILE_PARENT}/{_CS_DOTFILE_BASENAME}"
_CS_OPTOUT_MARKER = "# credentialed-primitive: reads-creds-directly"
_CS_SECURITY_HEADING = "### Security rules (non-negotiable)"
_CS_CREDBROKER_SSO_RESOLVER = "load_sso_cookies"
_CS_SSO_BROKER_PARENT = "." + "agentbundle"
_CS_SSO_BROKER_BIN_DIR = "bin"
_CS_SSO_BROKER_BASENAME = "sso-broker" + ".py"
_CS_SSO_BROKER_TAIL = (_CS_SSO_BROKER_PARENT, _CS_SSO_BROKER_BIN_DIR, _CS_SSO_BROKER_BASENAME)
_CS_SHIM_BASENAMES = frozenset({
    "credentials_shim.py", "_keychain_macos.py", "_credman_windows.py"
})
_CS_REQUIRED_PHRASES_BY_BROKER = {
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

_CS_KEY_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
_CS_HEADING_TERMINATE_RE = re.compile(r"\n#{1,6}\s")
_CS_NESTED_KEY_RE = re.compile(r"^\s+([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
_CS_LIST_INLINE_RE = re.compile(r"^\[(.*)\]$")


def _cs_normalize_flag(s: str) -> str:
    return s.lstrip("-").casefold().replace("-", "_")


def _cs_normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _cs_parse_inline_list(raw: str) -> list[str] | None:
    m = _CS_LIST_INLINE_RE.match(raw.strip())
    if m is None:
        return None
    inside = m.group(1).strip()
    if not inside:
        return []
    items = []
    for part in inside.split(","):
        s = part.strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            s = s[1:-1]
        items.append(s)
    return items


def _cs_parse_frontmatter(path: Path) -> tuple[dict | None, str]:
    """Minimal stdlib frontmatter parser — returns (fields, body) or (None, text)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, ""
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
    fields: dict = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = _CS_KEY_RE.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            mapping: dict = {}
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
                    return None, text
                nm = _CS_NESTED_KEY_RE.match(nxt)
                if not nm:
                    break
                nval = nm.group(2).strip()
                if len(nval) >= 2 and nval[0] == nval[-1] and nval[0] in ('"', "'"):
                    nval = nval[1:-1]
                lst = _cs_parse_inline_list(nm.group(2).strip())
                if lst is not None:
                    mapping[nm.group(1)] = lst
                else:
                    mapping[nm.group(1)] = nval
                j += 1
            fields[key] = mapping if mapping else ""
            i = j
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        fields[key] = val
        i += 1
    body = "\n".join(lines[end + 1:])
    return fields, body


def _cs_section_body(body: str, heading: str) -> str | None:
    idx = body.find(heading)
    if idx < 0:
        return None
    rest = body[idx:]
    m = _CS_HEADING_TERMINATE_RE.search(rest, len(heading))
    if m is None:
        return rest
    return rest[: m.start()]


def _cs_literal_string(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _cs_literal_string(node.left)
        right = _cs_literal_string(node.right)
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
                inner = _cs_literal_string(piece.value)
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
        if not (isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, int)):
            return None
        if not (0 <= slice_node.value < len(container.elts)):
            return None
        return _cs_literal_string(container.elts[slice_node.value])
    return None


def _cs_starred_first_literal(node: ast.expr) -> str | None:
    if not isinstance(node, ast.Starred):
        return None
    inner = node.value
    if not isinstance(inner, (ast.Tuple, ast.List)) or not inner.elts:
        return None
    return _cs_literal_string(inner.elts[0])


def _cs_ast_for(py_path: Path) -> ast.Module | None:
    try:
        return ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    except (OSError, SyntaxError):
        return None


def _cs_add_argument_flags(py_path: Path):
    tree = _cs_ast_for(py_path)
    if tree is None:
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
        value = _cs_literal_string(first)
        if value is None:
            value = _cs_starred_first_literal(first)
        if value is not None and value.startswith("-"):
            yield value, _cs_normalize_flag(value), node.lineno
        for kw in node.keywords:
            if kw.arg != "dest":
                continue
            dest_value = _cs_literal_string(kw.value)
            if dest_value is None:
                continue
            yield f"dest={dest_value!r}", _cs_normalize_flag(dest_value), node.lineno


def _cs_has_credentials_shim_import(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
    if tree is None:
        return False
    target_module = "credentials" + "_shim"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == target_module:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target_module:
                    return True
    return False


def _cs_has_credbroker_import(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
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


def _cs_has_credbroker_sso_import(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "credbroker":
            for alias in node.names:
                if alias.name == _CS_CREDBROKER_SSO_RESOLVER:
                    return True
        if (
            isinstance(node, ast.Attribute)
            and node.attr == _CS_CREDBROKER_SSO_RESOLVER
            and isinstance(node.value, ast.Name)
            and node.value.id == "credbroker"
        ):
            return True
    return False


def _cs_env_reads(py_path: Path):
    tree = _cs_ast_for(py_path)
    if tree is None:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            container = node.value
            if (
                isinstance(container, ast.Attribute)
                and container.attr == "environ"
                and isinstance(container.value, ast.Name)
                and container.value.id == "os"
            ):
                slice_node = node.slice
                if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                    yield slice_node.value
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and ((
                func.attr == "get"
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "environ"
                and isinstance(func.value.value, ast.Name)
                and func.value.value.id == "os"
            ) or (
                func.attr == "getenv"
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
            )) and node.args and isinstance(node.args[0], ast.Constant) \
                            and isinstance(node.args[0].value, str):
                yield node.args[0].value


def _cs_path_chain_components(node: ast.expr) -> tuple[str | None, list[str]]:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "str" and len(node.args) == 1:
        return _cs_path_chain_components(node.args[0])
    components: list[str] = []
    cur: ast.expr = node
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = _cs_literal_string(cur.right)
        if right is None:
            return None, []
        components.insert(0, right)
        cur = cur.left
    if isinstance(cur, ast.Call):
        callee = cur.func
        if (isinstance(callee, ast.Attribute) and callee.attr == "home"
                and isinstance(callee.value, ast.Name) and callee.value.id == "Path"):
            return "home", components
        if (isinstance(callee, ast.Attribute) and callee.attr == "expanduser"
                and isinstance(callee.value, ast.Attribute)
                and callee.value.attr == "path"
                and isinstance(callee.value.value, ast.Name)
                and callee.value.value.id == "os"
                and cur.args
                and isinstance(cur.args[0], ast.Constant)
                and cur.args[0].value == "~"):
            return "home", components
        if isinstance(callee, ast.Attribute) and callee.attr == "expanduser" \
                and isinstance(callee.value, ast.Call) \
                and isinstance(callee.value.func, ast.Name) \
                and callee.value.func.id == "Path":
            args = callee.value.args
            if args and isinstance(args[0], ast.Constant) and args[0].value == "~":
                return "home", components
    seed_literal = _cs_literal_string(cur)
    if seed_literal is not None:
        import pathlib as _pathlib
        seed_path = _pathlib.PurePosixPath(seed_literal)
        seed_components = list(seed_path.parts)
        kind = "absolute" if seed_path.is_absolute() else "relative"
        return kind, seed_components + components
    return None, []


def _cs_is_dotfile_chain(result: tuple) -> bool:
    _, components = result
    return (
        len(components) >= 2
        and components[-2] == _CS_DOTFILE_PARENT
        and components[-1] == _CS_DOTFILE_BASENAME
    )


def _cs_check_dotfile_read(py_path: Path) -> list[tuple[int, str]]:
    try:
        source = py_path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if node.args:
                chain = _cs_path_chain_components(node.args[0])
                if _cs_is_dotfile_chain(chain):
                    lineno = node.lineno
                    if _CS_OPTOUT_MARKER not in lines[lineno - 1]:
                        results.append((lineno, "open() reads dotfile credentials"))
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"read_text", "read_bytes", "open"}
        ):
            chain = _cs_path_chain_components(node.func.value)
            if _cs_is_dotfile_chain(chain):
                lineno = node.lineno
                if _CS_OPTOUT_MARKER not in lines[lineno - 1]:
                    results.append((lineno, f".{node.func.attr}() reads dotfile credentials"))
    flagged_linenos = {lineno for lineno, _ in results}
    for i, line in enumerate(lines, start=1):
        if i in flagged_linenos:
            continue
        if _CS_DOTFILE_SUBSTRING in line and _CS_OPTOUT_MARKER not in line.rstrip():
            results.append((i, f"skill reads {_CS_DOTFILE_SUBSTRING} directly"))
    return results


def _cs_sso_broker_call_targets(py_path: Path):
    tree = _cs_ast_for(py_path)
    if tree is None:
        return
    consumed: set[int] = set()

    def _consume_descendants(node: ast.AST) -> None:
        for child in ast.walk(node):
            consumed.add(id(child))

    for node in ast.walk(tree):
        if id(node) in consumed:
            continue
        seed_kind, components = _cs_path_chain_components(node)  # type: ignore[arg-type]
        if seed_kind is None or not components:
            continue
        _consume_descendants(node)
        lineno = getattr(node, "lineno", 0)
        yield seed_kind, tuple(components), lineno


def _cs_disallowed_subprocess_calls(py_path: Path):
    tree = _cs_ast_for(py_path)
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


def _cs_has_subprocess_run(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
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


def _cs_imports_playwright(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
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


def _cs_denyset_flag_groups(py_path: Path):
    tree = _cs_ast_for(py_path)
    if tree is None:
        return
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            continue
        flags = set()
        for el in node.elts:
            s = _cs_literal_string(el)
            if s is not None and s.startswith("-"):
                flags.add(_cs_normalize_flag(s))
        if flags:
            yield flags


def _cs_has_scrubbing_parser(py_path: Path) -> bool:
    tree = _cs_ast_for(py_path)
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


def _cs_is_canonical_shim(py: Path, shim_source_dir: Path) -> bool:
    if py.name not in _CS_SHIM_BASENAMES:
        return False
    if py.parent.name not in {"scripts", "shared-libs"}:
        return False
    expected_path = shim_source_dir / py.name
    try:
        expected = expected_path.read_bytes()
    except OSError:
        return False
    try:
        return py.read_bytes() == expected
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Catalogue-level rules
# ---------------------------------------------------------------------------


class _CatalogueRules:
    def __init__(self, root: Path, config: CatalogueConfig) -> None:
        self._root = root
        self._config = config
        self._resolved_root: Path | None = None
        self._resolved_config_paths: dict[str, Path] = {}
        self._unsafe_config_paths: set[str] = set()

    def collect(self, pack_filter: str | None) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        diagnostics.extend(self._check_config_paths())
        diagnostics.extend(self._check_markers())
        diagnostics.extend(self._check_duplicate_identities())
        diagnostics.extend(self._check_profiles())
        return diagnostics

    def _configured_path(self, field: str, default: str) -> Path | None:
        if field in self._unsafe_config_paths:
            return None
        if field in self._resolved_config_paths:
            return self._resolved_config_paths[field]
        return self._root / default

    def _packs_dir(self) -> Path | None:
        return self._configured_path("packs", "packs")

    def _marketplace_path(self) -> Path | None:
        return self._configured_path(
            "marketplace", ".claude-plugin/marketplace.json"
        )

    def _check_markers(self) -> list[Diagnostic]:
        diags: list[Diagnostic] = []
        root_packs = self._root / "packs"
        root_packs_valid = root_packs.is_dir()
        if root_packs_valid and self._resolved_root is not None:
            try:
                resolved_root_packs = root_packs.resolve(strict=True)
                root_packs_valid = resolved_root_packs.is_relative_to(self._resolved_root)
            except (OSError, RuntimeError):
                root_packs_valid = False
        if not root_packs_valid:
            diags.append(_diag(
                DiagnosticCode.CAT_L002,
                Severity.ERROR,
                f"literal root packs directory missing or unsafe: {root_packs}",
                remediation="Create a literal packs directory inside the catalogue root.",
            ))

        packs_dir = self._packs_dir()
        configured_packs = self._config.paths.packs
        if configured_packs != "packs" and packs_dir is not None and not packs_dir.is_dir():
            diags.append(_diag(
                DiagnosticCode.CAT_L002,
                Severity.ERROR,
                f"configured packs directory missing: {packs_dir}",
                remediation=(
                    "Create the configured packs directory or update "
                    "catalogue.toml paths.packs."
                ),
            ))

        mp = self._marketplace_path()
        preferred_adapter = self._config.distribution.agentbundle.preferred_adapter
        if (
            mp is not None
            and projects_claude_artifacts(preferred_adapter)
            and not mp.exists()
        ):
            diags.append(_diag(
                DiagnosticCode.CAT_L002,
                Severity.ERROR,
                f"marketplace.json missing: {mp}",
                remediation="Run 'make build-self' or 'agentbundle catalogue self-host --write'.",
            ))
        return diags

    def _check_duplicate_identities(self) -> list[Diagnostic]:
        packs_dir = self._packs_dir()
        if packs_dir is None or not packs_dir.is_dir():
            return []
        seen_names: dict[str, str] = {}
        diags: list[Diagnostic] = []
        for entry in sorted(packs_dir.iterdir()):
            if entry.name.startswith("_"):
                continue  # reserved authoring asset
            if not entry.is_dir() or not (entry / "pack.toml").exists():
                continue
            try:
                data = tomllib.loads((entry / "pack.toml").read_text(encoding="utf-8"))
                pack_name = data.get("pack", {}).get("name", "")
            except Exception:
                continue
            if pack_name in seen_names:
                diags.append(_diag(
                    DiagnosticCode.CAT_L003,
                    Severity.ERROR,
                    f"duplicate pack identity {pack_name!r}:"
                    f" found in {seen_names[pack_name]!r} and {entry.name!r}",
                    pack=entry.name,
                    remediation="Each pack must have a unique [pack].name.",
                ))
            else:
                seen_names[pack_name] = entry.name
        return diags

    def _profiles_dir(self) -> Path | None:
        return self._configured_path("profiles", "profiles")

    def _check_profiles(self) -> list[Diagnostic]:
        profiles_dir = self._profiles_dir()
        if profiles_dir is None or not profiles_dir.is_dir():
            return []
        packs_dir = self._packs_dir()
        if packs_dir is None:
            return []
        packs = _profile_load_packs(packs_dir)
        diags: list[Diagnostic] = []
        for toml_path in sorted(profiles_dir.glob("*.toml")):
            profile_id = toml_path.stem
            try:
                raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            except (tomllib.TOMLDecodeError, OSError) as exc:
                diags.append(_diag(
                    DiagnosticCode.CAT_L028,
                    Severity.ERROR,
                    f"profile {profile_id!r}: cannot parse: {exc}",
                    path=str(toml_path),
                ))
                continue
            for violation in _profile_lint_one(profile_id, raw, packs):
                diags.append(_diag(
                    DiagnosticCode.CAT_L028,
                    Severity.ERROR,
                    violation,
                    path=str(toml_path),
                ))
        return diags

    def _check_config_paths(self) -> list[Diagnostic]:
        diags: list[Diagnostic] = []
        try:
            root = self._root.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            self._unsafe_config_paths.update(
                {"packs", "profiles", "contracts", "marketplace", "build_output"}
            )
            return [_diag(
                DiagnosticCode.CAT_L021,
                Severity.ERROR,
                f"catalogue root cannot be resolved safely: {exc}",
                remediation="Use a readable catalogue root without circular symlinks.",
            )]
        self._resolved_root = root
        paths_obj = self._config.paths
        for field in ("packs", "profiles", "contracts", "marketplace", "build_output"):
            val = getattr(paths_obj, field, None)
            if not val:
                continue
            try:
                resolved = (self._root / val).resolve()
                if not resolved.is_relative_to(root):
                    self._unsafe_config_paths.add(field)
                    diags.append(_diag(
                        DiagnosticCode.CAT_L021,
                        Severity.ERROR,
                        f"catalogue.paths.{field} resolves outside catalogue root: {val!r}",
                        remediation="Use a relative path that stays within the catalogue root.",
                    ))
                else:
                    self._resolved_config_paths[field] = resolved
            except (OSError, RuntimeError) as exc:
                self._unsafe_config_paths.add(field)
                diags.append(_diag(
                    DiagnosticCode.CAT_L021,
                    Severity.ERROR,
                    f"catalogue.paths.{field} cannot be resolved safely: {val!r}: {exc}",
                    remediation="Use a relative path without circular or escaping symlinks.",
                ))
        return diags


# ---------------------------------------------------------------------------
# Pack-level rules
# ---------------------------------------------------------------------------


class _PackRules:
    def __init__(self, pack_dir: Path, root: Path) -> None:
        self._dir = pack_dir
        self._root = root
        self._name = pack_dir.name
        self._pack_toml: dict | None = None
        self._pack_toml_loaded = False

    def _get_pack_toml(self) -> dict | None:
        if not self._pack_toml_loaded:
            self._pack_toml_loaded = True
            toml_path = self._dir / "pack.toml"
            if toml_path.exists():
                try:
                    self._pack_toml = tomllib.loads(toml_path.read_text(encoding="utf-8"))
                except Exception:
                    self._pack_toml = None
        return self._pack_toml

    def collect(self) -> list[Diagnostic]:
        diags: list[Diagnostic] = []
        diags.extend(self._check_dir_name_vs_pack_toml())
        diags.extend(self._check_pack_toml_parseable())
        diags.extend(self._check_pack_schema_validation())
        diags.extend(self._check_plugin_json())
        diags.extend(self._check_name_version_parity())
        diags.extend(self._check_skills())
        diags.extend(self._check_agents())
        diags.extend(self._check_seeds())
        diags.extend(self._check_first_value())
        diags.extend(self._check_credentialed_skills())
        return diags

    def _check_dir_name_vs_pack_toml(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        pack_name = pt.get("pack", {}).get("name", "")
        if pack_name and pack_name != self._name:
            return [_diag(
                DiagnosticCode.CAT_L004,
                Severity.ERROR,
                f"directory name {self._name!r} differs from [pack].name {pack_name!r}",
                pack=self._name,
                path=str(self._dir / "pack.toml"),
                remediation="Rename the directory to match [pack].name, or update [pack].name.",
            )]
        return []

    def _check_pack_toml_parseable(self) -> list[Diagnostic]:
        toml_path = self._dir / "pack.toml"
        if not toml_path.exists():
            return []
        try:
            tomllib.loads(toml_path.read_text(encoding="utf-8"))
            return []
        except Exception as exc:
            return [_diag(
                DiagnosticCode.CAT_L005,
                Severity.ERROR,
                f"pack.toml is not valid TOML: {exc}",
                pack=self._name,
                path=str(toml_path),
                remediation="Fix the TOML syntax error in pack.toml.",
            )]

    def _check_pack_schema_validation(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        schema = _load_pack_schema()
        if schema is None:
            return [_diag(
                DiagnosticCode.CAT_L006,
                Severity.WARN,
                "pack.schema.json not found; skipping schema validation",
                pack=self._name,
                remediation="Ensure pack.schema.json is bundled with agentbundle.",
            )]
        from agentbundle.build.validate import validate
        errors = validate(pt, schema)
        if errors:
            return [_diag(
                DiagnosticCode.CAT_L006,
                Severity.ERROR,
                f"pack.toml fails schema validation: {errors[0]}",
                pack=self._name,
                path=str(self._dir / "pack.toml"),
                remediation="Fix the pack.toml field(s) reported by the schema validator.",
            )]
        return []

    def _check_plugin_json(self) -> list[Diagnostic]:
        plugin_path = plugin_json_path(self._dir)
        if not plugin_path.exists():
            return []
        try:
            data = json.loads(plugin_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return [_diag(
                DiagnosticCode.CAT_L007,
                Severity.ERROR,
                f"plugin.json is not valid JSON: {exc}",
                pack=self._name,
                path=str(plugin_path),
                remediation="Fix the JSON syntax error in plugin.json.",
            )]
        # Basic schema check: must have name and version
        diags: list[Diagnostic] = []
        for key in ("name", "version"):
            if key not in data:
                diags.append(_diag(
                    DiagnosticCode.CAT_L008,
                    Severity.ERROR,
                    f"plugin.json missing required key: {key!r}",
                    pack=self._name,
                    path=str(plugin_path),
                    remediation=f"Add {key!r} to plugin.json.",
                ))
        return diags

    def _check_name_version_parity(self) -> list[Diagnostic]:
        pt = self._get_pack_toml()
        if pt is None:
            return []
        plugin_path = plugin_json_path(self._dir)
        if not plugin_path.exists():
            return []
        try:
            plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        pack_name = pt.get("pack", {}).get("name", "")
        pack_ver = pt.get("pack", {}).get("version", "")
        plugin_name = plugin_data.get("name", "")
        plugin_ver = plugin_data.get("version", "")
        diags: list[Diagnostic] = []
        if pack_name and plugin_name and pack_name != plugin_name:
            diags.append(_diag(
                DiagnosticCode.CAT_L009,
                Severity.ERROR,
                f"name mismatch: pack.toml={pack_name!r}, plugin.json={plugin_name!r}",
                pack=self._name,
                remediation="Keep [pack].name and plugin.json name in sync.",
            ))
        if pack_ver and plugin_ver and pack_ver != plugin_ver:
            diags.append(_diag(
                DiagnosticCode.CAT_L009,
                Severity.ERROR,
                f"version mismatch: pack.toml={pack_ver!r}, plugin.json={plugin_ver!r}",
                pack=self._name,
                remediation="Keep [pack].version and plugin.json version in sync.",
            ))
        return diags

    def _check_skills(self) -> list[Diagnostic]:
        skills_dir = self._dir / ".apm" / "skills"
        if not skills_dir.is_dir():
            return []
        diags: list[Diagnostic] = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                diags.append(_diag(
                    DiagnosticCode.CAT_L010,
                    Severity.ERROR,
                    f"skill directory {skill_dir.name!r} missing SKILL.md",
                    pack=self._name,
                    path=str(skill_dir),
                    remediation="Add a SKILL.md with name and description frontmatter.",
                ))
                continue
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            if fm is None:
                diags.append(_diag(
                    DiagnosticCode.CAT_L011,
                    Severity.ERROR,
                    "SKILL.md missing frontmatter",
                    pack=self._name,
                    path=str(skill_md),
                    remediation="Add --- frontmatter with name and description.",
                ))
                continue
            for key in _SKILL_REQUIRED_KEYS:
                if not fm.get(key):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L011,
                        Severity.ERROR,
                        f"SKILL.md frontmatter missing required key: {key!r}",
                        pack=self._name,
                        path=str(skill_md),
                        remediation=f"Add {key!r} to the SKILL.md frontmatter.",
                    ))
            # Check description length
            desc = fm.get("description", "")
            if len(desc) > _MAX_DESC_LEN:
                diags.append(_diag(
                    DiagnosticCode.CAT_L026,
                    Severity.ERROR,
                    f"SKILL.md description exceeds {_MAX_DESC_LEN} chars ({len(desc)})",
                    pack=self._name,
                    path=str(skill_md),
                    remediation="Shorten the description field.",
                ))
        return diags

    def _check_agents(self) -> list[Diagnostic]:
        agents_dir = self._dir / ".apm" / "agents"
        if not agents_dir.is_dir():
            return []
        diags: list[Diagnostic] = []
        for agent_file in sorted(agents_dir.rglob("*.md")):
            text = agent_file.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            if fm is None:
                diags.append(_diag(
                    DiagnosticCode.CAT_L012,
                    Severity.ERROR,
                    f"agent file {agent_file.name!r} missing frontmatter",
                    pack=self._name,
                    path=str(agent_file),
                    remediation="Add --- frontmatter with name and description.",
                ))
                continue
            for key in _AGENT_REQUIRED_KEYS:
                if not fm.get(key):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L012,
                        Severity.ERROR,
                        f"agent file frontmatter missing required key: {key!r}",
                        pack=self._name,
                        path=str(agent_file),
                        remediation=f"Add {key!r} to the agent frontmatter.",
                    ))
        return diags

    def _check_seeds(self) -> list[Diagnostic]:
        """CAT-L029: seeds lint (opt-in via [pack].lint-seeds = true)."""
        pt = self._get_pack_toml()
        if pt is None:
            return []
        if pt.get("pack", {}).get("lint-seeds") is not True:
            return []
        seeds_dir = self._dir / "seeds"
        if not seeds_dir.is_dir():
            return []
        diags: list[Diagnostic] = []
        # os.walk(followlinks=False) avoids traversing into symlinked
        # directories, which rglob does on Python 3.11/3.12 (3.13 fixed it).
        for dirpath_str, _dirs, filenames in os.walk(seeds_dir, followlinks=False):
            for fname in sorted(filenames):
                path = Path(dirpath_str) / fname
                if path.is_symlink():
                    continue
                for violation in _seeds_check_file(path, seeds_dir):
                    diags.append(_diag(
                        DiagnosticCode.CAT_L029,
                        Severity.ERROR,
                        violation,
                        pack=self._name,
                        path=str(path),
                    ))
        return diags

    def _check_first_value(self) -> list[Diagnostic]:
        """CAT-L030: [pack.first-value] contract enforcement."""
        pt = self._get_pack_toml()
        if pt is None:
            return []
        pack_name = self._name
        toml_path = self._dir / "pack.toml"
        diags: list[Diagnostic] = []

        def _v(msg: str) -> None:
            diags.append(_diag(
                DiagnosticCode.CAT_L030,
                Severity.ERROR,
                f"{pack_name}: {msg}",
                pack=pack_name,
                path=str(toml_path),
            ))

        fv = pt.get("pack", {}).get("first-value")
        if fv is None:
            return []  # Section absent → pack has not adopted the contract; skip.

        ap = fv.get("audience-posture")
        if ap is None:
            _v("audience-posture: missing")
        elif ap not in _FV_AUDIENCE_POSTURES:
            _v(f"audience-posture: {ap!r} not in {sorted(_FV_AUDIENCE_POSTURES)}")

        surfaces = fv.get("surfaces")
        if surfaces is None:
            _v("surfaces: missing")
        elif not isinstance(surfaces, list):
            _v("surfaces: must be a list")
        elif len(surfaces) == 0:
            _v("surfaces: must have at least one entry")
        else:
            allowed_adapters = (
                pt.get("pack", {}).get("install", {}).get("allowed-adapters")
            )
            if isinstance(allowed_adapters, list):
                for s in surfaces:
                    if s not in allowed_adapters:
                        _v(f"surfaces: {s!r} not in allowed-adapters {allowed_adapters}")

        prereqs = fv.get("prerequisites")
        if prereqs is None:
            _v("prerequisites: missing")
        elif not isinstance(prereqs, list):
            _v("prerequisites: must be a list")
        else:
            for i, entry in enumerate(prereqs):
                if isinstance(entry, str) and len(entry) > 80:
                    _v(f"prerequisites[{i}]: {len(entry)} chars (max 80): {entry!r}")

        verification = fv.get("verification")
        if verification is None:
            _v("verification: missing")
        elif not isinstance(verification, str):
            _v("verification: must be a string")
        elif len(verification) > 160:
            _v(f"verification: {len(verification)} chars (max 160)")

        recovery = fv.get("recovery")
        if recovery is None:
            _v("recovery: missing")
        elif not isinstance(recovery, str):
            _v("recovery: must be a string")
        elif len(recovery) > 300:
            _v(f"recovery: {len(recovery)} chars (max 300)")

        if fv.get("level-b") is True:
            starter_task = fv.get("starter-task")
            if starter_task is None:
                _v("starter-task: missing (required when level-b = true)")
            elif not isinstance(starter_task, str):
                _v("starter-task: must be a string")
            elif len(starter_task) > 120:
                _v(f"starter-task: {len(starter_task)} chars (max 120)")

            starter_prompt = fv.get("starter-prompt")
            if starter_prompt is None:
                _v("starter-prompt: missing (required when level-b = true)")
            elif not isinstance(starter_prompt, str):
                _v("starter-prompt: must be a string")
            else:
                if len(starter_prompt) > 500:
                    _v(f"starter-prompt: {len(starter_prompt)} chars (max 500)")
                m = _FV_PLACEHOLDER_RE.search(starter_prompt)
                if m:
                    _v(f"starter-prompt: placeholder token {m.group()!r} not allowed")

            expected_result = fv.get("expected-result")
            if expected_result is None:
                _v("expected-result: missing (required when level-b = true)")
            elif not isinstance(expected_result, str):
                _v("expected-result: must be a string")
            elif len(expected_result) > 200:
                _v(f"expected-result: {len(expected_result)} chars (max 200)")

            next_action = fv.get("next-action")
            if next_action is None:
                _v("next-action: missing (required when level-b = true)")
            elif not isinstance(next_action, str):
                _v("next-action: must be a string")
            elif len(next_action) > 120:
                _v(f"next-action: {len(next_action)} chars (max 120)")

        if fv.get("writes-to-repo") is True:
            safety_gate = fv.get("safety-gate")
            if safety_gate is None:
                _v("safety-gate: missing (required when writes-to-repo = true)")
            elif not isinstance(safety_gate, str):
                _v("safety-gate: must be a string")
            elif len(safety_gate) > 200:
                _v(f"safety-gate: {len(safety_gate)} chars (max 200)")

        tutorial = fv.get("tutorial")
        if tutorial is not None:
            tutorial_path = self._root / tutorial
            if not tutorial_path.is_file():
                _v(f"tutorial: {tutorial!r} does not exist (relative to root)")
            elif tutorial_path.suffix != ".md":
                _v(f"tutorial: {tutorial!r} must be a .md file (got {tutorial_path.suffix!r})")

        return diags

    def _check_credentialed_skills(self) -> list[Diagnostic]:
        """CAT-L031: credentialed-skill convention checks (D1/D2/D2b/D3)."""
        skills_dir = self._dir / ".apm" / "skills"
        if not skills_dir.is_dir():
            return []
        shim_source_dir = self._root / "packs" / "credential-brokers" / ".apm" / "shared-libs"
        diags: list[Diagnostic] = []

        def _report(path: Path, message: str) -> None:
            try:
                rel = str(path.relative_to(self._dir))
            except ValueError:
                rel = str(path)
            diags.append(_diag(
                DiagnosticCode.CAT_L031,
                Severity.ERROR,
                message,
                pack=self._name,
                path=rel,
            ))

        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            fields, body = _cs_parse_frontmatter(skill_md)
            if fields is None:
                continue
            metadata = fields.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if str(metadata.get("credentialed", "")).strip().lower() != "true":
                continue

            primitive_class = metadata.get("primitive-class", "")
            auth = metadata.get("auth", "") or ""
            auth_fallback = metadata.get("auth-fallback", "") or ""
            namespace = metadata.get("namespace", "") or ""
            keys = metadata.get("keys", [])
            if isinstance(keys, str):
                keys = []

            # D1: Don't-block presence in Security section
            section = _cs_section_body(body, _CS_SECURITY_HEADING)
            if section is None:
                _report(skill_md, f"missing heading: {_CS_SECURITY_HEADING}")
            else:
                normalised = _cs_normalize_whitespace(section)
                required_brokers = [auth]
                if auth_fallback:
                    required_brokers.append(auth_fallback)
                for broker in required_brokers:
                    phrases = _CS_REQUIRED_PHRASES_BY_BROKER.get(broker)
                    if phrases is None:
                        field = "auth" if broker == auth else "auth-fallback"
                        _report(
                            skill_md,
                            f"unknown metadata.{field}={broker!r} "
                            f"(expected one of {sorted(_CS_REQUIRED_PHRASES_BY_BROKER)})",
                        )
                        continue
                    for phrase in phrases:
                        if _cs_normalize_whitespace(phrase) not in normalised:
                            _report(
                                skill_md,
                                f"security section missing required phrase "
                                f"for broker {broker!r}: {phrase!r}",
                            )

            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                continue

            py_files = sorted(p for p in scripts_dir.rglob("*.py") if p.is_file())

            # D2: argv ban (credentialed-cli)
            if primitive_class == "credentialed-cli":
                for py in py_files:
                    for raw, norm, lineno in _cs_add_argument_flags(py):
                        if norm in _CS_BANNED_FLAGS:
                            _report(
                                py,
                                f"line {lineno}: argv-borne credential flag "
                                f"{raw!r} accepted by argparse (normalised "
                                f"{norm!r} ∈ {sorted(_CS_BANNED_FLAGS)})",
                            )

                # D2b: deny-set completeness + scrubbing backstop
                token_denysets = [
                    g
                    for py in py_files
                    for g in _cs_denyset_flag_groups(py)
                    if len(g & _CS_BANNED_FLAGS) >= 2
                ]
                if token_denysets:
                    present = set().union(*token_denysets)
                    missing = sorted(_CS_BANNED_FLAGS - present)
                    if missing:
                        _report(
                            skill_md,
                            f"token deny-set is incomplete — missing canonical "
                            f"banned flag(s) {missing}; the argv ban requires all of "
                            f"{sorted(_CS_BANNED_FLAGS)}",
                        )
                    if not any(_cs_has_scrubbing_parser(py) for py in py_files):
                        _report(
                            skill_md,
                            "ships a token deny-set but no value-scrubbing "
                            "ArgumentParser subclass (one overriding error()); a "
                            "token-shaped flag outside the deny-set would have its "
                            "value echoed verbatim by argparse's error message",
                        )

            # D3: dotfile read (AST walk)
            for py in py_files:
                if _cs_is_canonical_shim(py, shim_source_dir):
                    continue
                for lineno, desc in _cs_check_dotfile_read(py):
                    _report(
                        py,
                        f"line {lineno}: {desc} "
                        f"(architectural violation — opt-out marker absent)",
                    )

            # Broker-specific checks
            consumer_py_files = [
                p for p in py_files if not _cs_is_canonical_shim(p, shim_source_dir)
            ]

            if auth == "creds":
                found_resolver_import = any(
                    _cs_has_credentials_shim_import(p) or _cs_has_credbroker_import(p)
                    for p in consumer_py_files
                )
                if not found_resolver_import:
                    target = "credentials" + "_shim"
                    _report(
                        skill_md,
                        f"auth=creds requires at least one credential-resolver import "
                        f"in scripts/ — `from credbroker import …` or the "
                        f"legacy `from .{target} import …` — none found",
                    )

            elif auth == "env":
                if not namespace:
                    _report(skill_md, "auth=env requires metadata.namespace")
                if not keys:
                    _report(skill_md, "auth=env requires metadata.keys (non-empty list)")
                if namespace and keys:
                    reads: set[str] = set()
                    for p in consumer_py_files:
                        reads.update(_cs_env_reads(p))
                    ns_prefix = str(namespace).upper()
                    for key in keys:
                        expected = f"{ns_prefix}_{str(key)}"
                        if expected not in reads:
                            _report(
                                skill_md,
                                f"auth=env declares key {key!r} under namespace "
                                f"{namespace!r}; expected env read of "
                                f"{expected!r} not found in scripts/",
                            )

            elif auth == "sso-cookie":
                targets_home = False
                any_subprocess_run = False
                resolves_via_credbroker = any(
                    _cs_has_credbroker_sso_import(p) for p in consumer_py_files
                )
                for p in consumer_py_files:
                    for bad_name, lineno in _cs_disallowed_subprocess_calls(p):
                        _report(
                            p,
                            f"line {lineno}: auth=sso-cookie consumer uses "
                            f"{bad_name}(...) — only subprocess.run is permitted "
                            f"(Popen / os.system / os.exec* widen the exfiltration "
                            f"surface; the broker is invoked via subprocess.run only)",
                        )
                    if _cs_imports_playwright(p):
                        _report(
                            p,
                            "auth=sso-cookie consumer imports Playwright directly "
                            "(broker dependency only; consumers invoke "
                            "sso-broker.py via subprocess)",
                        )
                    if _cs_has_subprocess_run(p):
                        any_subprocess_run = True
                    for seed_kind, components, lineno in _cs_sso_broker_call_targets(p):
                        tail3 = tuple(components[-3:])
                        matches_target = tail3 == _CS_SSO_BROKER_TAIL
                        ends_in_basename = (
                            components and components[-1] == _CS_SSO_BROKER_BASENAME
                        )
                        if matches_target and seed_kind == "home":
                            targets_home = True
                        elif ends_in_basename and seed_kind == "absolute":
                            _report(
                                p,
                                f"line {lineno}: auth=sso-cookie path expression "
                                f"targets hard-coded absolute path "
                                f"({'/'.join(components)!r}); use "
                                f"Path.home() / {_CS_SSO_BROKER_PARENT!r} / "
                                f"{_CS_SSO_BROKER_BIN_DIR!r} / {_CS_SSO_BROKER_BASENAME!r}",
                            )
                if resolves_via_credbroker:
                    pass
                elif not targets_home:
                    _report(
                        skill_md,
                        f"auth=sso-cookie requires either a credbroker SSO import "
                        f"(`from credbroker import {_CS_CREDBROKER_SSO_RESOLVER}`) or a path "
                        f"expression resolving to Path.home() / {_CS_SSO_BROKER_PARENT!r} / "
                        f"{_CS_SSO_BROKER_BIN_DIR!r} / {_CS_SSO_BROKER_BASENAME!r} "
                        f"in scripts/ (neither found)",
                    )
                elif not any_subprocess_run:
                    _report(
                        skill_md,
                        "auth=sso-cookie requires a subprocess.run call in scripts/ "
                        "(broker path resolved but no subprocess.run found)",
                    )

        return diags


# ---------------------------------------------------------------------------
# Legacy finding translator (lint_packs string → Diagnostic)
# ---------------------------------------------------------------------------


def _translate_legacy_finding(pack_name: str, finding: str) -> Diagnostic:
    """Map a lint_packs string finding to a Diagnostic with a stable code."""
    # "pack: symlink not portable to Windows: relpath"
    if "symlink not portable to Windows" in finding:
        path_part = finding.split(": ", 2)[-1] if finding.count(": ") >= 2 else ""
        return _diag(
            DiagnosticCode.CAT_L022,
            Severity.WARN,
            finding,
            pack=pack_name,
            path=path_part or None,
        )
    # Windows-poisonous name → CAT-L023
    return _diag(
        DiagnosticCode.CAT_L023,
        Severity.ERROR,
        finding,
        pack=pack_name,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def lint_catalogue(root: Path, pack: str | None = None, *, deep: bool = False) -> LintResult:
    """Run all portable catalogue lint rules against *root*.

    When *pack* is given, pack-level diagnostics are filtered to that pack.
    Catalogue-level rules (CAT-L001, CAT-L002) always run against the full
    catalogue. Read-only; raises no exceptions (all errors become diagnostics).

    When *deep* is ``True``, runs the full agentskills.io spec-compliance lint
    via :mod:`agentbundle.catalogue_tooling.skill_spec_lint`.  Requires the
    ``pyyaml`` optional extra (``pip install 'agentbundle[lint]'``); raises
    ``ImportError`` when PyYAML is absent so the CLI can exit 2.
    """
    from agentbundle.build.lint_packs import lint_pack as _lint_pack

    diagnostics: list[Diagnostic] = []

    # Step 1: load catalogue.toml; emit CAT-L001 and return early on error
    config = None
    try:
        config = load_catalogue_config(root)
    except CatalogueConfigError as exc:
        diagnostics.append(_diag(
            DiagnosticCode.CAT_L001,
            Severity.ERROR,
            f"catalogue.toml is present but invalid: {exc}",
            remediation="Fix the reported validation error in catalogue.toml.",
        ))
        diagnostics.sort(key=_sort_key)
        return LintResult(
            ok=False,
            diagnostics=diagnostics,
            schema_version=1,
            command="catalogue lint",
            operation="lint",
            agentbundle_version=_get_agentbundle_version(),
            catalogue_schema_version=1,
        )

    if config is None:
        diagnostics.append(_diag(
            DiagnosticCode.CAT_L002,
            Severity.ERROR,
            f"catalogue.toml missing: {root / 'catalogue.toml'}",
            remediation="Create a valid catalogue.toml at the catalogue root.",
        ))
        return LintResult(
            ok=False,
            diagnostics=diagnostics,
            schema_version=1,
            command="catalogue lint",
            operation="lint",
            agentbundle_version=_get_agentbundle_version(),
            catalogue_schema_version=1,
        )

    # Step 2: catalogue-level rules
    cat_rules = _CatalogueRules(root, config)
    diagnostics.extend(cat_rules.collect(pack))

    # Step 3: determine packs dir
    packs_dir = cat_rules._packs_dir()

    # Step 4+5: per-pack rules
    if packs_dir is not None and packs_dir.is_dir():
        for pack_dir in sorted(packs_dir.iterdir()):
            if pack_dir.name.startswith("_"):
                continue  # reserved authoring asset
            if not pack_dir.is_dir() or not (pack_dir / "pack.toml").exists():
                continue
            pack_name = pack_dir.name
            if pack is not None and pack_name != pack:
                continue

            # Pack-level rules
            pack_rules = _PackRules(pack_dir, root)
            diagnostics.extend(pack_rules.collect())

            # Portability rules from lint_packs
            legacy_findings = _lint_pack(pack_dir)
            for finding in legacy_findings:
                diagnostics.append(_translate_legacy_finding(pack_name, finding))

    # Deep spec-compliance pass
    if deep:
        from agentbundle.catalogue_tooling.skill_spec_lint import lint_skill_spec
        deep_diags = lint_skill_spec(root, pack=pack)
        diagnostics.extend(deep_diags)

    diagnostics.sort(key=_sort_key)
    ok = not any(d.severity == Severity.ERROR for d in diagnostics)

    return LintResult(
        ok=ok,
        diagnostics=diagnostics,
        schema_version=1,
        command="catalogue lint",
        operation="lint",
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=config.schema if config else 1,
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_json(result: LintResult) -> str:
    """Return a single valid JSON document for *result*. Deterministic."""
    data = {
        "schema_version": result.schema_version,
        "command": result.command,
        "operation": result.operation,
        "agentbundle_version": result.agentbundle_version,
        "catalogue_schema_version": result.catalogue_schema_version,
        "ok": result.ok,
        "diagnostics": [
            {
                "code": d.code,
                "severity": d.severity.name,
                "pack": d.pack,
                "path": d.path,
                "line": d.line,
                "col": d.col,
                "message": d.message,
                "remediation": d.remediation,
            }
            for d in result.diagnostics
        ],
    }
    return json.dumps(data, sort_keys=True, indent=2)


def render_table(result: LintResult) -> str:
    """Return a grouped plain-text table for *result*."""
    if not result.diagnostics:
        return f"ok: catalogue lint clean ({result.agentbundle_version})"

    lines: list[str] = []
    by_pack: dict[str, list[Diagnostic]] = {}
    for d in result.diagnostics:
        key = d.pack or "(catalogue)"
        by_pack.setdefault(key, []).append(d)

    for pack_key in sorted(by_pack):
        lines.append(f"── {pack_key} ──")
        for d in by_pack[pack_key]:
            loc = ""
            if d.path:
                loc = d.path
                if d.line is not None:
                    loc += f":{d.line}"
            sev = d.severity.name
            lines.append(f"  [{d.code}] {sev} {loc}")
            lines.append(f"    {d.message}")
            if d.remediation:
                lines.append(f"    → {d.remediation}")
        lines.append("")

    status = "ok" if result.ok else "FAIL"
    lines.append(f"{status}: {len(result.diagnostics)} finding(s)")
    return "\n".join(lines)
