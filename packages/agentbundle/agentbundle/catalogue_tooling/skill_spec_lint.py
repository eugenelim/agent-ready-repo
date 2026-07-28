"""Deep SKILL.md spec-compliance linter (agentskills.io specification).

Ported from ``tools/lint-skill-spec.py``; returns structured Diagnostic
objects instead of printing so callers can integrate into the catalogue lint
result pipeline.

Entry point::

    lint_skill_spec(root, pack=None) -> list[Diagnostic]

Requires the ``pyyaml`` optional extra (``pip install 'agentbundle[lint]'``).
Raises ``ImportError`` with a clear install hint when PyYAML is absent.

All paths in returned diagnostics use forward slashes (POSIX) regardless of
platform.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path

from agentbundle.catalogue_tooling.results import Diagnostic, Severity

# ---------------------------------------------------------------------------
# Spec constants
# ---------------------------------------------------------------------------

ALLOWED_SKILL_KEYS = frozenset({"name", "description", "license", "compatibility",
                                 "metadata", "allowed-tools"})
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BLESSED_SUBDIRS = frozenset({"scripts", "references", "assets", "evals"})
IGNORED_DEV_DIRS = frozenset({"node_modules", ".venv", "venv", "__pycache__"})

RE_ABS_PATH = re.compile(r"(/Users/|/home/|/opt/|/var/|/etc/|C:\\)")
RE_INSTALL_PATH = re.compile(
    r"(?<!~)(?<![\w/])"
    r"(\.claude/skills/(?:[a-z0-9-]+/)?|"
    r"packs/[a-z0-9-]+/\.apm/skills/(?:[a-z0-9-]+/)?)"
)
RE_DEEP_SAME_SKILL = re.compile(
    r"(?<![\w./~])((?:scripts|references|assets)/[a-z0-9_./-]+/[a-z0-9_.-]+\.[a-z0-9]+)"
)
RE_ALLOWED_TOOLS_FLOW = re.compile(r"^allowed-tools\s*:\s*\[", re.MULTILINE)
META_SCALAR_TYPES = (str, bool, int, float, type(None))
YAML_LEADING_INDICATORS = "#[]{}|>&*@`%!?"
FOLDED_LITERAL_MARKERS = (">", "|", ">-", "|-", ">+", "|+")

# Diagnostic codes for skill-spec findings (CAT-S series)
_CODE_PARSE   = "CAT-S001"   # parse / read failure
_CODE_FM      = "CAT-S002"   # frontmatter shape / key violation
_CODE_BODY    = "CAT-S003"   # body content violation
_CODE_LAYOUT  = "CAT-S004"   # directory layout violation (WARN)
_CODE_EVALS   = "CAT-S005"   # evals/ schema violation
_CODE_TOML    = "CAT-S006"   # pack.toml [pack.evals] cross-ref violation


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class _DuplicateKeyError(Exception):
    def __init__(self, key: object, line: int) -> None:
        self.key = key
        self.line = line


def _require_yaml():
    """Import yaml, raising ImportError with an install hint when absent."""
    try:
        import yaml  # noqa: PLC0415 — lazy, PyYAML is optional
        return yaml
    except ImportError:
        raise ImportError(
            "Deep skill-spec lint requires PyYAML. "
            "Install with: pip install 'agentbundle[lint]'"
        ) from None


def _make_loader(yaml):
    """Return a SafeLoader subclass that rejects duplicate mapping keys."""
    class _FrontmatterLoader(yaml.SafeLoader):
        pass

    def _construct_no_dups(loader, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None,
                f"expected a mapping node, got {node.id}",
                node.start_mark,
            )
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise _DuplicateKeyError(key, key_node.start_mark.line + 1)
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    _FrontmatterLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_no_dups,
    )
    return _FrontmatterLoader


def _check_description_source(fm_lines: list[str]) -> tuple[int, str] | None:
    """Source-level policy checks on the raw ``description:`` line.

    Returns ``None`` on clean, or ``(line_index, message)`` on the first
    violation found. ``line_index`` is 0-based into ``fm_lines``.
    """
    for i, line in enumerate(fm_lines):
        m = re.match(r"^description:\s*(.*)$", line)
        if not m:
            continue
        value = m.group(1).rstrip()
        if value in FOLDED_LITERAL_MARKERS:
            return i, (
                f"description must be a single-line scalar; folded/literal "
                f"block syntax ({value!r}) is not portable"
            )
        if i + 1 < len(fm_lines):
            nxt = fm_lines[i + 1]
            if nxt.strip() and (nxt.startswith((" ", "\t"))):
                return i, (
                    "description must be a single-line scalar; "
                    "continuation lines (indented next line) are not portable"
                )
        if value == "":
            return None
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ('"', "'")
        ):
            return None
        leading = value[0]
        if leading in ("&", "*"):
            name = "anchor" if leading == "&" else "alias"
            return i, (
                f"description starts with YAML {name} indicator {leading!r} "
                f"in an unquoted scalar; the YAML parser will consume the "
                f"{name} and the value silently mutates. Wrap in double quotes."
            )
        if leading in YAML_LEADING_INDICATORS:
            return i, (
                f"description starts with YAML indicator {leading!r} in an "
                f"unquoted scalar; wrap value in double quotes"
            )
        if ": " in value:
            return i, (
                "description contains ': ' in an unquoted scalar; wrap "
                "value in double quotes (Kiro silently drops skills with "
                "this pattern from agent discovery -- kirodotdev/Kiro#8329)"
            )
        if re.search(r"\s#", value):
            return i, (
                "description contains whitespace-then-'#' in an unquoted "
                "scalar; the YAML parser treats everything from '#' as a "
                "comment and truncates the value. Wrap in double quotes."
            )
        return None
    return None


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def lint_skill_spec(root: Path, pack: str | None = None) -> list[Diagnostic]:
    """Check all SKILL.md files under *root* against the agentskills.io spec.

    When *pack* is provided only skills under ``packs/<pack>/`` are checked.

    Requires PyYAML (``pip install 'agentbundle[lint]'``).

    Returns a list of :class:`~agentbundle.catalogue_tooling.results.Diagnostic`
    objects; empty list means all checked skills are clean.
    """
    yaml = _require_yaml()
    Loader = _make_loader(yaml)
    diags: list[Diagnostic] = []

    def _relpath(p: Path) -> str:
        """Return a forward-slash path relative to *root*, or the posix str."""
        try:
            return p.relative_to(root).as_posix()
        except ValueError:
            return p.as_posix()

    def _err(path: Path, msg: str, line: int | None = None,
             code: str = _CODE_FM, pack_name: str | None = None) -> None:
        loc = _relpath(path)
        diags.append(Diagnostic(
            code=code,
            severity=Severity.ERROR,
            pack=pack_name,
            path=loc,
            line=line,
            col=None,
            message=msg,
            remediation=None,
        ))

    def _warn(path: Path, msg: str, line: int | None = None,
              code: str = _CODE_LAYOUT, pack_name: str | None = None) -> None:
        loc = _relpath(path)
        diags.append(Diagnostic(
            code=code,
            severity=Severity.WARN,
            pack=pack_name,
            path=loc,
            line=line,
            col=None,
            message=msg,
            remediation=None,
        ))

    # ── Frontmatter parser ────────────────────────────────────────────────

    def _parse_frontmatter(path: Path):
        """Return (fields, body_start_line, body, error, fm_text)."""
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return None, 0, "", f"could not read skill: {exc}", ""
        if raw.startswith(b"\xef\xbb\xbf"):
            return None, 0, "", (
                "UTF-8 BOM detected at file start; save the file as UTF-8 "
                "without BOM"
            ), ""
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return None, 0, "", "UTF-16 BOM detected; save as UTF-8 without BOM", ""
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            return None, 0, "", f"SKILL.md is not valid UTF-8: {exc}", ""
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None, 0, text, None, ""
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is None:
            return None, 0, text, "frontmatter opened with --- but never closed", ""
        fm_lines = lines[1:end]
        fm_text = "\n".join(fm_lines)
        body_start_line = end + 2
        body = "\n".join(lines[end + 1:])
        desc_check = _check_description_source(fm_lines)
        if desc_check is not None:
            fm_line_idx, desc_msg = desc_check
            file_line = fm_line_idx + 2
            return None, 0, text, f"line {file_line}: {desc_msg}", fm_text
        try:
            fields = yaml.load(fm_text, Loader=Loader)  # nosec B506
        except _DuplicateKeyError as exc:
            return None, 0, text, (
                f"duplicate frontmatter key {exc.key!r} (line {exc.line + 1})"
            ), fm_text
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            problem = getattr(exc, "problem", None) or str(exc)
            if mark is not None:
                return None, 0, text, (
                    f"malformed frontmatter (line {mark.line + 2}): {problem}"
                ), fm_text
            return None, 0, text, f"malformed frontmatter: {problem}", fm_text
        if fields is None:
            fields = {}
        if not isinstance(fields, dict):
            return None, 0, text, (
                "frontmatter must be a mapping at the top level "
                f"(got {type(fields).__name__})"
            ), fm_text
        return fields, body_start_line, body, None, fm_text

    # ── Per-skill checks ──────────────────────────────────────────────────

    def _check_frontmatter(path: Path, fields: dict, fm_text: str,
                           pack_name: str | None) -> None:
        unknown = sorted(set(fields) - ALLOWED_SKILL_KEYS)
        if unknown:
            _err(path, f"unknown top-level frontmatter keys: {unknown} "
                       f"(allowed: {sorted(ALLOWED_SKILL_KEYS)})",
                 pack_name=pack_name)

        name = fields.get("name")
        if not isinstance(name, str) or not name:
            _err(path, "missing required key: name", pack_name=pack_name)
        else:
            if not (1 <= len(name) <= 64):
                _err(path, f"name {name!r} must be 1–64 chars (got {len(name)})",
                     pack_name=pack_name)
            if not KEBAB.match(name):
                _err(path, f"name {name!r} must match ^[a-z0-9]+(-[a-z0-9]+)*$ "
                            f"(kebab-case)", pack_name=pack_name)
            elif name != path.parent.name:
                _err(path, f"name {name!r} does not match directory "
                            f"{path.parent.name!r}", pack_name=pack_name)

        desc = fields.get("description")
        if not isinstance(desc, str) or not desc:
            _err(path, "missing required key: description (must be non-empty)",
                 pack_name=pack_name)
        elif len(desc) > 1024:
            _err(path, f"description exceeds 1024 chars (got {len(desc)})",
                 pack_name=pack_name)

        if "license" in fields:
            lic = fields["license"]
            if not isinstance(lic, str) or not lic:
                _err(path, "'license' must be a non-empty string when present",
                     pack_name=pack_name)

        if "compatibility" in fields:
            compat = fields["compatibility"]
            if not isinstance(compat, str) or not compat:
                _err(path, "'compatibility' must be a non-empty string when present",
                     pack_name=pack_name)
            elif len(compat) > 500:
                _err(path, f"compatibility exceeds 500 chars (got {len(compat)})",
                     pack_name=pack_name)

        if "metadata" in fields:
            meta = fields["metadata"]
            if meta == "" or meta is None:
                pass
            elif not isinstance(meta, dict):
                _err(path, f"'metadata' must be a nested mapping "
                            f"(got {type(meta).__name__})", pack_name=pack_name)
            else:
                for mk, mv in meta.items():
                    if isinstance(mv, list):
                        for item in mv:
                            if not isinstance(item, META_SCALAR_TYPES):
                                _err(path, f"'metadata.{mk}' list entries "
                                            f"must be scalars "
                                            f"(got {type(item).__name__})",
                                     pack_name=pack_name)
                                break
                    elif isinstance(mv, dict):
                        pass
                    elif not isinstance(mv, META_SCALAR_TYPES):
                        _err(path, f"'metadata.{mk}' must be a scalar or a "
                                    f"list of scalars (got {type(mv).__name__})",
                             pack_name=pack_name)

        if "allowed-tools" in fields:
            tools = fields["allowed-tools"]
            if isinstance(tools, list):
                if RE_ALLOWED_TOOLS_FLOW.search(fm_text):
                    _err(path, "'allowed-tools' must be a space-separated string, "
                                "not a YAML flow-style list", pack_name=pack_name)
                else:
                    shape = ("an empty YAML flow list" if tools == []
                             else "a YAML block list")
                    _err(path, f"'allowed-tools' must be a space-separated "
                                f"string, not {shape}", pack_name=pack_name)
            elif not isinstance(tools, str) or not tools:
                _err(path, "'allowed-tools' must be a space-separated string "
                            "when present", pack_name=pack_name)

    def _check_body(path: Path, body: str, body_start_line: int,
                    pack_name: str | None) -> None:
        body_lines = body.splitlines()
        n = len(body_lines)
        if n > 1000:
            _err(path, f"body exceeds 1000 lines (got {n}); the spec "
                        f"recommends keeping SKILL.md under 500 lines",
                 code=_CODE_BODY, pack_name=pack_name)
        elif n > 500:
            _warn(path, f"body exceeds 500 lines (got {n}); the spec "
                         f"recommends staying under 500",
                  code=_CODE_BODY, pack_name=pack_name)

        for offset, line in enumerate(body_lines):
            line_no = body_start_line + offset
            abs_match = RE_ABS_PATH.search(line)
            if abs_match:
                _err(path, f"absolute system path in body: "
                            f"{abs_match.group(0)!r}",
                     line=line_no, code=_CODE_BODY, pack_name=pack_name)
            for install in RE_INSTALL_PATH.finditer(line):
                hit = install.group(1)
                _err(path, f"install-path reference in body: {hit!r} — "
                            f"skill bodies must use skill-relative paths for "
                            f"own files and name-only references for other skills",
                     line=line_no, code=_CODE_BODY, pack_name=pack_name)
            if not RE_INSTALL_PATH.search(line):
                for deep in RE_DEEP_SAME_SKILL.finditer(line):
                    hit = deep.group(1)
                    _warn(path, f"same-skill file reference deeper than one "
                                 f"level: {hit!r} (spec recommends ≤1 level)",
                          line=line_no, code=_CODE_BODY, pack_name=pack_name)

    def _check_layout(skill_dir: Path, path: Path,
                      pack_name: str | None) -> None:
        for child in sorted(skill_dir.iterdir()):
            if child.is_dir():
                if child.name in IGNORED_DEV_DIRS:
                    continue
                if child.name not in BLESSED_SUBDIRS:
                    _warn(path, f"non-blessed top-level subdirectory: "
                                 f"{child.name!r} (spec recommends "
                                 f"{sorted(BLESSED_SUBDIRS)} as the canonical layout)",
                          pack_name=pack_name)
            elif child.name != "SKILL.md":
                _warn(path, f"loose file at skill root: {child.name!r}",
                      code=_CODE_LAYOUT, pack_name=pack_name)

    def _check_eval_queries(evals_json: Path, pack_name: str | None) -> None:
        try:
            data = json.loads(evals_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _err(evals_json, f"evals/eval_queries.json is not valid JSON: {exc}",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        if not isinstance(data, list):
            _err(evals_json, "evals/eval_queries.json must be a JSON array at top level",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                _err(evals_json, f"eval_queries[{idx}] must be an object",
                     code=_CODE_EVALS, pack_name=pack_name)
                continue
            query = entry.get("query")
            if not isinstance(query, str) or not query:
                _err(evals_json,
                     f"eval_queries[{idx}].query must be a non-empty string",
                     code=_CODE_EVALS, pack_name=pack_name)
            st = entry.get("should_trigger")
            if not isinstance(st, bool):
                _err(evals_json,
                     f"eval_queries[{idx}].should_trigger must be a boolean "
                     f"(got {type(st).__name__})",
                     code=_CODE_EVALS, pack_name=pack_name)

    def _check_evals_json(skill_dir: Path, evals_json: Path,
                          skill_name: str | None, pack_name: str | None) -> None:
        try:
            data = json.loads(evals_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _err(evals_json, f"evals/evals.json is not valid JSON: {exc}",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        if not isinstance(data, dict):
            _err(evals_json, "evals/evals.json must be a JSON object",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        sn = data.get("skill_name")
        if not isinstance(sn, str) or not sn:
            _err(evals_json, "evals.json 'skill_name' must be a non-empty string",
                 code=_CODE_EVALS, pack_name=pack_name)
        elif skill_name and sn != skill_name:
            _err(evals_json, f"evals.json skill_name {sn!r} does not match "
                              f"skill name {skill_name!r}",
                 code=_CODE_EVALS, pack_name=pack_name)
        evals_list = data.get("evals")
        if not isinstance(evals_list, list):
            _err(evals_json, "evals.json 'evals' must be a list",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        seen_ids: set = set()
        for idx, entry in enumerate(evals_list):
            if not isinstance(entry, dict):
                _err(evals_json, f"evals[{idx}] must be an object",
                     code=_CODE_EVALS, pack_name=pack_name)
                continue
            eid = entry.get("id")
            if not isinstance(eid, (int, str)) or isinstance(eid, bool):
                _err(evals_json, f"evals[{idx}].id must be int or str "
                                  f"(got {type(eid).__name__})",
                     code=_CODE_EVALS, pack_name=pack_name)
            elif eid in seen_ids:
                _err(evals_json, f"evals[{idx}] duplicate id {eid!r}",
                     code=_CODE_EVALS, pack_name=pack_name)
            else:
                seen_ids.add(eid)
            prompt = entry.get("prompt")
            if not isinstance(prompt, str) or not prompt:
                _err(evals_json, f"evals[{idx}].prompt must be a non-empty string",
                     code=_CODE_EVALS, pack_name=pack_name)
            expected = entry.get("expected_output")
            if not isinstance(expected, str) or not expected:
                _err(evals_json, f"evals[{idx}].expected_output must be a "
                                  f"non-empty string",
                     code=_CODE_EVALS, pack_name=pack_name)
            files = entry.get("files")
            if files is not None:
                if not isinstance(files, list):
                    _err(evals_json, f"evals[{idx}].files must be a list",
                         code=_CODE_EVALS, pack_name=pack_name)
                else:
                    skill_dir_resolved = skill_dir.resolve()
                    for fpath in files:
                        if not isinstance(fpath, str) or not fpath:
                            _err(evals_json,
                                 f"evals[{idx}].files entry must be a non-empty string",
                                 code=_CODE_EVALS, pack_name=pack_name)
                            continue
                        resolved = (skill_dir / fpath).resolve()
                        try:
                            resolved.relative_to(skill_dir_resolved)
                        except ValueError:
                            _err(evals_json, f"evals[{idx}].files entry "
                                              f"{fpath!r} resolves outside "
                                              f"the skill directory",
                                 code=_CODE_EVALS, pack_name=pack_name)
                            continue
                        if not resolved.exists():
                            _err(evals_json, f"evals[{idx}].files entry "
                                              f"{fpath!r} does not exist",
                                 code=_CODE_EVALS, pack_name=pack_name)
            asserts = entry.get("assertions")
            if asserts is not None:
                if not isinstance(asserts, list):
                    _err(evals_json, f"evals[{idx}].assertions must be a list",
                         code=_CODE_EVALS, pack_name=pack_name)
                else:
                    for ai, a in enumerate(asserts):
                        if not isinstance(a, str) or not a:
                            _err(evals_json,
                                 f"evals[{idx}].assertions[{ai}] must be a "
                                 f"non-empty string",
                                 code=_CODE_EVALS, pack_name=pack_name)

    def _check_evals(skill_dir: Path, path: Path, skill_name: str | None,
                     pack_name: str | None) -> None:
        evals_dir = skill_dir / "evals"
        if not evals_dir.exists() or not evals_dir.is_dir():
            return
        evals_json = evals_dir / "evals.json"
        eval_queries_json = evals_dir / "eval_queries.json"
        if not evals_json.exists() and not eval_queries_json.exists():
            _err(path, "evals/ directory present but neither evals/evals.json "
                        "nor evals/eval_queries.json is present",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        if evals_json.exists():
            _check_evals_json(skill_dir, evals_json, skill_name, pack_name)
        if eval_queries_json.exists():
            _check_eval_queries(eval_queries_json, pack_name)

    def _check_skill(path: Path, pack_name: str | None) -> None:
        fields, body_start, body, ferr, fm_text = _parse_frontmatter(path)
        if ferr:
            _err(path, ferr, code=_CODE_PARSE, pack_name=pack_name)
            return
        if fields is None:
            _err(path, "missing YAML frontmatter (--- ... ---)",
                 code=_CODE_PARSE, pack_name=pack_name)
            return
        _check_frontmatter(path, fields, fm_text, pack_name)
        if not body.strip():
            _err(path, "body is empty", code=_CODE_BODY, pack_name=pack_name)
        _check_body(path, body, body_start, pack_name)
        _check_layout(path.parent, path, pack_name)
        _check_evals(path.parent, path, fields.get("name"), pack_name)

    # ── Build walk roots ──────────────────────────────────────────────────

    walk_roots: list[tuple[Path, str | None]] = []  # (walk_dir, pack_name)
    packs_root = root / "packs"

    if pack is not None:
        skill_root = packs_root / pack / ".apm" / "skills"
        if skill_root.exists():
            walk_roots.append((skill_root, pack))
    else:
        projection = root / ".claude" / "skills"
        if projection.exists():
            walk_roots.append((projection, None))
        if packs_root.exists():
            for p in sorted(packs_root.glob("*/.apm/skills")):
                pack_name = p.parent.parent.name
                walk_roots.append((p, pack_name))

    # ── Walk skills ───────────────────────────────────────────────────────

    def _skill_mds(walk_dir: Path) -> list[Path]:
        """Return all SKILL.md paths under walk_dir, including broken/circular symlinks.

        Path.glob("*/SKILL.md") silently skips broken/circular symlinks on
        Python 3.11 Linux (it checks is_file() internally). Using os.scandir
        with lstat ensures every SKILL.md — even a dangling or looped symlink —
        is visited so the linter can emit a diagnostic.
        """
        result: list[Path] = []
        try:
            with os.scandir(walk_dir) as it:
                for entry in it:
                    if not (entry.is_dir(follow_symlinks=True) or
                            entry.is_dir(follow_symlinks=False)):
                        continue
                    skill_md = Path(entry.path) / "SKILL.md"
                    try:
                        skill_md.lstat()  # succeeds for real files and any symlink
                        result.append(skill_md)
                    except OSError:
                        pass
        except OSError:
            pass
        return sorted(result)

    for walk_dir, pack_name in walk_roots:
        for skill_md in _skill_mds(walk_dir):
            try:
                _check_skill(skill_md, pack_name)
            except (OSError, RuntimeError) as exc:
                _err(skill_md, f"could not read skill: {exc}",
                     code=_CODE_PARSE, pack_name=pack_name)

    # ── [pack.evals].skills cross-reference ──────────────────────────────

    if packs_root.exists() and pack is None:
        for pack_toml in sorted(packs_root.glob("*/pack.toml")):
            pack_dir = pack_toml.parent
            pn = pack_dir.name
            try:
                manifest = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError) as exc:
                _err(pack_toml, f"could not parse pack.toml: {exc}",
                     code=_CODE_TOML, pack_name=pn)
                continue
            evals_cfg = manifest.get("pack", {}).get("evals")
            if evals_cfg is None:
                continue
            if not isinstance(evals_cfg, dict):
                _err(pack_toml, "[pack.evals] must be a table",
                     code=_CODE_TOML, pack_name=pn)
                continue
            skills = evals_cfg.get("skills", [])
            if not isinstance(skills, list):
                _err(pack_toml, "[pack.evals].skills must be an array of strings",
                     code=_CODE_TOML, pack_name=pn)
                continue
            for entry in skills:
                if not isinstance(entry, str) or not entry:
                    _err(pack_toml, f"[pack.evals].skills entry must be a "
                                     f"non-empty string (got {entry!r})",
                         code=_CODE_TOML, pack_name=pn)
                    continue
                skill_dir = pack_dir / ".apm" / "skills" / entry
                if not skill_dir.is_dir():
                    _err(pack_toml, f"[pack.evals].skills names {entry!r} but "
                                     f"it is not a skill directory",
                         code=_CODE_TOML, pack_name=pn)
                    continue
                if not (skill_dir / "evals" / "eval_queries.json").is_file():
                    _err(pack_toml, f"[pack.evals].skills names {entry!r} but "
                                     f"it ships no evals/eval_queries.json",
                         code=_CODE_TOML, pack_name=pn)

    return diags
