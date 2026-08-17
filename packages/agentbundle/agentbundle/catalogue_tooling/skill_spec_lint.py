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
import stat
import tomllib
from pathlib import Path
from typing import Any

from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
)
from agentbundle.catalogue_tooling.package import _TRANSIENT_DIRS
from agentbundle.catalogue_tooling.results import Diagnostic, Severity

# ---------------------------------------------------------------------------
# Spec constants
# ---------------------------------------------------------------------------

ALLOWED_SKILL_KEYS = frozenset({"name", "description", "license", "compatibility",
                                 "metadata", "allowed-tools"})
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BLESSED_SUBDIRS = frozenset({"scripts", "references", "assets", "evals"})
IGNORED_DEV_DIRS = _TRANSIENT_DIRS

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
_CODE_PARSE = "CAT-S001"   # parse / read failure
_CODE_FM = "CAT-S002"   # frontmatter shape / key violation
_CODE_BODY = "CAT-S003"   # body content violation
_CODE_LAYOUT = "CAT-S004"   # directory layout violation (WARN)
_CODE_EVALS = "CAT-S005"   # evals/ schema violation
_CODE_TOML = "CAT-S006"   # pack.toml [pack.evals] cross-ref violation


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class _DuplicateKeyError(Exception):
    def __init__(self, key: object, line: int) -> None:
        self.key = key
        self.line = line


def _path_is_junction(path: Path) -> bool:
    """Return whether *path* is a Windows junction, failing closed on errors."""
    checker = getattr(path, "is_junction", None)
    if checker is None:
        return False
    try:
        return bool(checker())
    except OSError:
        return True


def _require_yaml() -> Any:
    """Import yaml, raising ImportError with an install hint when absent."""
    try:
        import yaml  # noqa: PLC0415 — lazy, PyYAML is optional
        return yaml
    except ImportError:
        raise ImportError(
            "Deep skill-spec lint requires PyYAML. "
            "Install with: pip install 'agentbundle[lint]'"
        ) from None


def _make_loader(yaml: Any) -> Any:
    """Return a SafeLoader subclass that rejects duplicate mapping keys."""
    class _FrontmatterLoader(yaml.SafeLoader):
        pass

    def _construct_no_dups(
        loader: Any, node: Any, deep: bool = False
    ) -> dict[Any, Any]:
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None,
                f"expected a mapping node, got {node.id}",
                node.start_mark,
            )
        mapping: dict[Any, Any] = {}
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


def _check_eval_queries(evals_json: Path, *, content: str | None = None) -> list[str]:
    """Return structural findings for one ``eval_queries.json`` manifest."""
    try:
        source = content if content is not None else evals_json.read_text(encoding="utf-8")
        data = json.loads(source)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"evals/eval_queries.json is not valid JSON: {exc}"]
    if not isinstance(data, list):
        return ["evals/eval_queries.json must be a JSON array at top level"]
    if not data:
        return ["evals/eval_queries.json must contain at least one query"]
    findings: list[str] = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            findings.append(f"eval_queries[{idx}] must be an object")
            continue
        query = entry.get("query")
        if not isinstance(query, str) or not query:
            findings.append(f"eval_queries[{idx}].query must be a non-empty string")
        should_trigger = entry.get("should_trigger")
        if not isinstance(should_trigger, bool):
            findings.append(
                f"eval_queries[{idx}].should_trigger must be a boolean "
                f"(got {type(should_trigger).__name__})"
            )
    return findings


def _check_evals_json(
    skill_dir: Path,
    evals_json: Path,
    skill_name: str | None,
    *,
    content: str | None = None,
) -> list[str]:
    """Return structural and referenced-file findings for one eval manifest."""
    try:
        source = content if content is not None else evals_json.read_text(encoding="utf-8")
        data = json.loads(source)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"evals/evals.json is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return ["evals/evals.json must be a JSON object"]
    findings: list[str] = []
    manifest_skill_name = data.get("skill_name")
    if not isinstance(manifest_skill_name, str) or not manifest_skill_name:
        findings.append("evals.json 'skill_name' must be a non-empty string")
    elif skill_name and manifest_skill_name != skill_name:
        findings.append(
            f"evals.json skill_name {manifest_skill_name!r} does not match "
            f"skill name {skill_name!r}"
        )
    evals_list = data.get("evals")
    if not isinstance(evals_list, list):
        findings.append("evals.json 'evals' must be a list")
        return findings
    if not evals_list:
        findings.append("evals.json 'evals' must contain at least one entry")
        return findings
    seen_ids: set[object] = set()
    for idx, entry in enumerate(evals_list):
        if not isinstance(entry, dict):
            findings.append(f"evals[{idx}] must be an object")
            continue
        eval_id = entry.get("id")
        if not isinstance(eval_id, (int, str)) or isinstance(eval_id, bool):
            findings.append(
                f"evals[{idx}].id must be int or str (got {type(eval_id).__name__})"
            )
        elif eval_id in seen_ids:
            findings.append(f"evals[{idx}] duplicate id {eval_id!r}")
        else:
            seen_ids.add(eval_id)
        prompt = entry.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            findings.append(f"evals[{idx}].prompt must be a non-empty string")
        expected = entry.get("expected_output")
        if not isinstance(expected, str) or not expected:
            findings.append(f"evals[{idx}].expected_output must be a non-empty string")
        files = entry.get("files")
        if files is not None:
            if not isinstance(files, list):
                findings.append(f"evals[{idx}].files must be a list")
            else:
                try:
                    canonical_skill_dir = skill_dir.resolve()
                except (OSError, RuntimeError):
                    canonical_skill_dir = skill_dir
                for file_ref in files:
                    if not isinstance(file_ref, str) or not file_ref:
                        findings.append(
                            f"evals[{idx}].files entry must be a non-empty string"
                        )
                        continue
                    try:
                        resolved = (skill_dir / file_ref).resolve()
                    except (OSError, RuntimeError):
                        findings.append(
                            f"evals[{idx}].files entry {file_ref!r} cannot be resolved"
                        )
                        continue
                    if not resolved.is_relative_to(canonical_skill_dir):
                        findings.append(
                            f"evals[{idx}].files entry {file_ref!r} resolves outside "
                            "the skill directory"
                        )
                    elif not resolved.exists():
                        findings.append(
                            f"evals[{idx}].files entry {file_ref!r} does not exist"
                        )
        assertions = entry.get("assertions")
        if assertions is not None:
            if not isinstance(assertions, list):
                findings.append(f"evals[{idx}].assertions must be a list")
            else:
                for assertion_index, assertion in enumerate(assertions):
                    if not isinstance(assertion, str) or not assertion:
                        findings.append(
                            f"evals[{idx}].assertions[{assertion_index}] must be a "
                            "non-empty string"
                        )
    return findings


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
            raw = read_confined_regular_file(path.parent, path)
        except (OSError, UnsafeContentError) as exc:
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

    def _report_eval_queries(
        skill_dir: Path, evals_json: Path, pack_name: str | None
    ) -> None:
        try:
            content = read_confined_regular_file(skill_dir, evals_json).decode("utf-8")
        except (OSError, UnicodeDecodeError, UnsafeContentError) as exc:
            _err(
                evals_json,
                f"could not read eval manifest: {exc}",
                code=_CODE_EVALS,
                pack_name=pack_name,
            )
            return
        for message in _check_eval_queries(evals_json, content=content):
            _err(evals_json, message, code=_CODE_EVALS, pack_name=pack_name)

    def _report_evals_json(
        skill_dir: Path,
        evals_json: Path,
        skill_name: str | None,
        pack_name: str | None,
    ) -> None:
        try:
            content = read_confined_regular_file(skill_dir, evals_json).decode("utf-8")
        except (OSError, UnicodeDecodeError, UnsafeContentError) as exc:
            _err(
                evals_json,
                f"could not read eval manifest: {exc}",
                code=_CODE_EVALS,
                pack_name=pack_name,
            )
            return
        for message in _check_evals_json(
            skill_dir, evals_json, skill_name, content=content
        ):
            _err(evals_json, message, code=_CODE_EVALS, pack_name=pack_name)

    def _check_evals(skill_dir: Path, path: Path, skill_name: str | None,
                     pack_name: str | None) -> None:
        evals_dir = skill_dir / "evals"
        try:
            evals_metadata = evals_dir.lstat()
        except FileNotFoundError:
            return
        except OSError:
            _err(
                evals_dir,
                "could not inspect evals directory",
                code=_CODE_EVALS,
                pack_name=pack_name,
            )
            return
        if (
            stat.S_ISLNK(evals_metadata.st_mode)
            or _path_is_junction(evals_dir)
            or not stat.S_ISDIR(evals_metadata.st_mode)
        ):
            _err(
                evals_dir,
                "evals entry is not a real directory",
                code=_CODE_EVALS,
                pack_name=pack_name,
            )
            return
        evals_json = evals_dir / "evals.json"
        eval_queries_json = evals_dir / "eval_queries.json"

        def _manifest_present(manifest: Path) -> bool | None:
            """Return no-follow presence, diagnosing inspection failures."""
            try:
                manifest.lstat()
            except FileNotFoundError:
                return False
            except OSError:
                _err(
                    manifest,
                    "could not inspect eval manifest",
                    code=_CODE_EVALS,
                    pack_name=pack_name,
                )
                return None
            return True

        evals_present = _manifest_present(evals_json)
        queries_present = _manifest_present(eval_queries_json)
        if evals_present is False and queries_present is False:
            _err(path, "evals/ directory present but neither evals/evals.json "
                        "nor evals/eval_queries.json is present",
                 code=_CODE_EVALS, pack_name=pack_name)
            return
        if evals_present:
            _report_evals_json(skill_dir, evals_json, skill_name, pack_name)
        if queries_present:
            _report_eval_queries(skill_dir, eval_queries_json, pack_name)

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

    def _validate_walk_root(
        walk_dir: Path,
    ) -> tuple[bool, tuple[Path, str] | None]:
        """Validate every directory component without following links."""
        try:
            relative = walk_dir.relative_to(root)
        except ValueError:
            return False, (walk_dir, "skill walk root is outside catalogue root")
        if ".." in relative.parts:
            return False, (walk_dir, "skill walk root contains path traversal")
        current = root
        for part in relative.parts:
            current /= part
            try:
                metadata = current.lstat()
            except FileNotFoundError:
                return False, None
            except OSError:
                return False, (current, "could not inspect skill walk root")
            if stat.S_ISLNK(metadata.st_mode) or _path_is_junction(current):
                return False, (current, "linked skill walk root is not allowed")
            if not stat.S_ISDIR(metadata.st_mode):
                return False, (current, "skill walk root is not a directory")
        try:
            walk_dir.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (OSError, RuntimeError, ValueError):
            return False, (walk_dir, "skill walk root escapes catalogue root")
        return True, None

    walk_roots: list[tuple[Path, str | None]] = []  # (walk_dir, pack_name)
    root_errors: list[tuple[Path, str, str | None]] = []
    crossref_pack_dirs: list[Path] = []
    packs_root = root / "packs"

    if pack is not None:
        if not KEBAB.fullmatch(pack):
            root_errors.append(
                (packs_root, "pack filter is not a safe pack name", None)
            )
        else:
            pack_dir = packs_root / pack
            walk_roots.append((pack_dir / ".apm" / "skills", pack))
            pack_present, pack_error = _validate_walk_root(pack_dir)
            if pack_present and pack_error is None:
                crossref_pack_dirs.append(pack_dir)
    else:
        walk_roots.append((root / ".claude" / "skills", None))
        packs_present, packs_error = _validate_walk_root(packs_root)
        if packs_error is not None:
            root_errors.append((*packs_error, None))
        elif packs_present:
            try:
                with os.scandir(packs_root) as it:
                    pack_entries = sorted(it, key=lambda entry: entry.name)
            except OSError:
                root_errors.append(
                    (packs_root, "could not enumerate packs for deep lint", None)
                )
            else:
                for entry in pack_entries:
                    if entry.name.startswith("_"):
                        continue
                    pack_dir = Path(entry.path)
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError:
                        root_errors.append(
                            (pack_dir, "could not inspect pack for deep lint", entry.name)
                        )
                        continue
                    if (
                        stat.S_ISLNK(metadata.st_mode)
                        or _path_is_junction(pack_dir)
                    ):
                        root_errors.append(
                            (pack_dir, "linked pack is not allowed", entry.name)
                        )
                    elif stat.S_ISDIR(metadata.st_mode):
                        crossref_pack_dirs.append(pack_dir)
                        walk_roots.append(
                            (pack_dir / ".apm" / "skills", entry.name)
                        )

    # ── Walk skills ───────────────────────────────────────────────────────

    def _skill_mds(walk_dir: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
        """Return skill paths and bounded traversal errors under *walk_dir*.

        Directory entries are inspected without following links. Transient
        directories are skipped before inspection; every other traversal error
        becomes a catalogue-relative diagnostic instead of silently weakening
        the deep lint pass.
        """
        result: list[Path] = []
        errors: list[tuple[Path, str]] = []
        root_present, root_error = _validate_walk_root(walk_dir)
        if root_error is not None:
            return [], [root_error]
        if not root_present:
            return [], []
        try:
            with os.scandir(walk_dir) as it:
                entries = sorted(it, key=lambda entry: entry.name)
        except OSError:
            return [], [(walk_dir, "could not enumerate skill directory")]
        for entry in entries:
            if entry.name in _TRANSIENT_DIRS:
                continue
            entry_path = Path(entry.path)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError:
                errors.append((entry_path, "could not inspect skill directory"))
                continue
            is_link = stat.S_ISLNK(metadata.st_mode) or _path_is_junction(entry_path)
            if not (stat.S_ISDIR(metadata.st_mode) or is_link):
                continue
            if is_link:
                errors.append((entry_path, "linked skill directory is not allowed"))
                continue
            skill_md = entry_path / "SKILL.md"
            try:
                skill_metadata = skill_md.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                errors.append((skill_md, "could not inspect skill entry"))
                continue
            if (
                stat.S_ISLNK(skill_metadata.st_mode)
                or _path_is_junction(skill_md)
            ):
                errors.append((skill_md, "linked skill entry is not allowed"))
            elif not stat.S_ISREG(skill_metadata.st_mode):
                errors.append((skill_md, "non-regular skill entry is not allowed"))
            elif skill_metadata.st_nlink > 1:
                errors.append((skill_md, "hard-linked skill entry is not allowed"))
            else:
                result.append(skill_md)
        return sorted(result), errors

    for error_path, message, pack_name in root_errors:
        _err(error_path, message, code=_CODE_PARSE, pack_name=pack_name)
    for walk_dir, pack_name in walk_roots:
        skill_mds, walk_errors = _skill_mds(walk_dir)
        for error_path, message in walk_errors:
            _err(error_path, message, code=_CODE_PARSE, pack_name=pack_name)
        for skill_md in skill_mds:
            try:
                _check_skill(skill_md, pack_name)
            except (OSError, RuntimeError):
                _err(skill_md, "could not inspect skill contents",
                     code=_CODE_PARSE, pack_name=pack_name)

    # ── [pack.evals].skills cross-reference ──────────────────────────────

    for pack_dir in sorted(crossref_pack_dirs):
        pack_toml = pack_dir / "pack.toml"
        pn = pack_dir.name
        try:
            pack_toml.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            _err(
                pack_toml,
                "could not inspect pack.toml",
                code=_CODE_TOML,
                pack_name=pn,
            )
            continue
        try:
            manifest_text = read_confined_regular_file(
                pack_dir, pack_toml
            ).decode("utf-8")
            manifest = tomllib.loads(manifest_text)
        except (
            OSError,
            UnicodeDecodeError,
            UnsafeContentError,
            tomllib.TOMLDecodeError,
        ) as exc:
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
            if not KEBAB.fullmatch(entry):
                _err(
                    pack_toml,
                    f"[pack.evals].skills entry {entry!r} is not a safe skill name",
                    code=_CODE_TOML,
                    pack_name=pn,
                )
                continue
            skill_dir = pack_dir / ".apm" / "skills" / entry
            skill_present, skill_error = _validate_walk_root(skill_dir)
            if not skill_present or skill_error is not None:
                _err(pack_toml, f"[pack.evals].skills names {entry!r} but "
                                 f"it is not a skill directory",
                     code=_CODE_TOML, pack_name=pn)
                continue
            eval_queries = skill_dir / "evals" / "eval_queries.json"
            try:
                eval_metadata = eval_queries.lstat()
            except OSError:
                eval_metadata = None
            if (
                eval_metadata is None
                or not stat.S_ISREG(eval_metadata.st_mode)
                or eval_metadata.st_nlink > 1
                or _path_is_junction(eval_queries)
            ):
                _err(pack_toml, f"[pack.evals].skills names {entry!r} but "
                                 f"it ships no evals/eval_queries.json",
                     code=_CODE_TOML, pack_name=pn)

    return diags
