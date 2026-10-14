"""_supervisor_projector — plan grammar, task projection, and envelope references.

Pure functions over spec and plan text. Nothing here writes, and nothing reads
a file except through the reader the caller passes in.

The plan grammar section walks task sections and reads `Depends on:` the way
`loop-cohort.py` does, so both read one plan the same way while that script
remains.

Task projection turns `### Tn: Title` sections into task-contract records. A
task's identity is its title without the number, and its revision digests the
title and the pinned fields (`Tests:` with its stub fences, `Touches:`,
`Done when:`, and `Effects:`), so renumbering, reordering, and edits to working
fields such as `Approach:` or `Depends on:` leave it unchanged.

Envelope references are the six reviewed-envelope reference values. Each is the
reference name joined to a SHA-256 over the name and its owning content, each
section prefixed by its heading and canonicalized by the shared contract
canonicalizer, so bookkeeping edits (checkboxes, the status token, working
sections) leave every value unchanged.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

__all__ = [
    "CHANGE_OWNERS",
    "ENVELOPE_REFERENCE_NAMES",
    "TERMINAL_INTENT_CHANGE",
    "classify_replan",
    "ProjectionRefused",
    "envelope_references",
    "project_plan",
    "spec_metadata_value",
    "spec_status",
    "plan_status",
    "terminal_intent",
    "task_contract",
    "walk_task_sections",
    "parse_depends_on",
]

_SCRIPTS_DIR = Path(__file__).resolve().parent

# ── Plan grammar ─────────────────────────────────────────────────────────────
# Task headings may be level 2 or level 3 (`## T<n>` or `### T<n>`).
TASK_HEADING_RE = re.compile(r"^#{2,3}\s+(T\d+[a-z]?)\b", re.MULTILINE)
_RANGE_RE = re.compile(r"(T\d+)\s*-\s*(T\d+)")
_TASK_ID_RE = re.compile(r"T\d+[a-z]?")
_CROSS_MARKER_RE = re.compile(r"spec:([A-Za-z0-9._-]+)/(T\d+[a-z]?)")
_CROSS_LEGACY_RE = re.compile(r"`(?!T\d+[a-z]?`)([A-Za-z0-9._-]+)`\s*(T\d+[a-z]?)")


def _local_dep_ids(field: str) -> set[str]:
    """Local task IDs a `Depends on:` field names ahead of its first `(`.

    Trailing parenthetical prose is commentary, not declaration.
    """
    head = field.split("(")[0]
    cleaned = _CROSS_MARKER_RE.sub("", head)
    cleaned = _CROSS_LEGACY_RE.sub("", cleaned)
    if not cleaned.strip() or re.fullmatch(r"\s*none\s*", cleaned, re.IGNORECASE):
        return set()
    ids: set[str] = set()
    for lo, hi in _RANGE_RE.findall(cleaned):
        ids.update(f"T{i}" for i in range(int(lo[1:]), int(hi[1:]) + 1))
    ids.update(_TASK_ID_RE.findall(cleaned))
    return ids


def parse_depends_on(field: str, local_task_ids):
    """Parse a 'Depends on:' field value into local task IDs and cross-spec markers."""
    head = field.split("(")[0]
    cross = _CROSS_MARKER_RE.findall(head) + _CROSS_LEGACY_RE.findall(head)
    return {t for t in _local_dep_ids(field) if t in local_task_ids}, cross


class _TaskSection(NamedTuple):
    """One plan task's boundaries, as offsets into the plan text.

    `start` opens the heading; `body_start` is just past it; `end` is where the
    next task heading begins, or the end of the text for the final task.
    """

    task_id: str
    start: int
    body_start: int
    end: int


def walk_task_sections(text: str) -> list[_TaskSection]:
    """Return each task section's boundaries, in plan order."""
    matches = list(TASK_HEADING_RE.finditer(text))
    return [
        _TaskSection(
            task_id=m.group(1),
            start=m.start(),
            body_start=m.end(),
            end=matches[i + 1].start() if i + 1 < len(matches) else len(text),
        )
        for i, m in enumerate(matches)
    ]


# ── Supervisor projection ────────────────────────────────────────────────────


class ProjectionRefused(Exception):
    """A projection was refused with a stable code and the owner who can fix it."""

    def __init__(self, code: str, owner: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.owner = owner
        self.detail = detail or code


ENVELOPE_REFERENCE_NAMES: tuple[str, ...] = (
    "spec_policy",
    "scope_and_non_goals",
    "authority_and_security",
    "public_contracts",
    "durable_outputs",
    "accepted_risk",
)

# Spec sections each section-backed reference owns, in digest order.
_SECTION_OWNERS: dict[str, tuple[str, ...]] = {
    "spec_policy": ("Acceptance Criteria", "Testing Strategy", "Agent Rules"),
    "scope_and_non_goals": ("Scope and Non-goals",),
    "durable_outputs": ("Durable Outputs",),
    "accepted_risk": ("Accepted Risk",),
}
_PROTECTED_HEADINGS = (
    "Acceptance Criteria",
    "Testing Strategy",
    "Agent Rules",
    "Scope and Non-goals",
    "Durable Outputs",
    "Accepted Risk",
    "Terminal Intent",
)
_H2_RE = re.compile(r"^##[ \t]+(?P<title>\S.*?)[ \t]*$")
_META_RE = re.compile(
    r"^[ \t]*(?:[-*][ \t]+)?\*\*(?P<name>[A-Za-z][A-Za-z -]*?):\*\*[ \t]*(?P<value>.*)$"
)
_TASK_TITLE_RE = re.compile(r"^#{2,3}[ \t]+(T\d+[a-z]?)\b[ \t]*[:.]?[ \t]*(?P<title>.*?)[ \t]*$")
_FIELD_RE = re.compile(
    r"^(?:[-*][ \t]+)?\*\*(?P<name>[A-Za-z][A-Za-z -]*?):\*\*[ \t]?(?P<rest>.*)$"
)
_STUB_ATTR_RE = re.compile(r'[ \t]+(?P<key>[a-z-]+)=(?:"(?P<quoted>[^"]*)"|(?P<bare>[^\s"]+))')
_FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<run>`{3,}|~{3,})(?P<info>.*)$")
_EFFECT_NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_CITED_ID_RE = re.compile(r"\b(?P<kind>ADR|RFC)-(?P<num>\d{1,6})\b")
_STATUS_RE = re.compile(r"^[ \t]*(?:[-*][ \t]+)?\*\*Status:\*\*[ \t]*(?P<token>[A-Za-z-]+)")
_MAX_STUB_BYTES = 1024 * 1024


_SIBLINGS: dict[str, ModuleType] = {}


def _sibling(filename: str) -> ModuleType:
    """Load a sibling script by path, once, unregistered in ``sys.modules``."""
    cached = _SIBLINGS.get(filename)
    if cached is not None:
        return cached
    path = _SCRIPTS_DIR / filename
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        alias = "_supervisor_projector_" + filename.removesuffix(".py").lstrip("_")
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path.name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    _SIBLINGS[filename] = module
    return module


def _canonical(text: str) -> str:
    return str(_sibling("_loop_guards.py").canonical_contract(text, ac_section_only=True))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize(text: str) -> str:
    """LF line endings, no trailing whitespace, no surrounding blank lines."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip("\n")


class _Sections(NamedTuple):
    preamble: str
    sections: list[tuple[str, str]]  # (title, heading line + body)


def _split_h2(text: str) -> _Sections:
    """Split Markdown at level-2 headings, ignoring headings inside fences."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    fence: tuple[str, int] | None = None
    for line in lines:
        m = _FENCE_RE.match(line)
        if m:
            char, run = m.group("run")[0], len(m.group("run"))
            if fence is None:
                fence = (char, run)
            elif char == fence[0] and run >= fence[1] and not m.group("info").strip():
                fence = None
        elif fence is None:
            h = _H2_RE.match(line)
            if h:
                sections.append((h.group("title"), [line]))
                continue
        (sections[-1][1] if sections else preamble).append(line)
    return _Sections("\n".join(preamble), [(t, "\n".join(body)) for t, body in sections])


def _find_sections(text: str, title: str) -> list[str]:
    want = title.casefold()
    return [body for t, body in _split_h2(text).sections if t.casefold() == want]


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def spec_metadata_value(spec_text: str, name: str) -> list[str]:
    """Return every preamble value for metadata field *name* (with continuation lines).

    HTML comments, such as template guidance, are not part of a value.
    """
    preamble = _HTML_COMMENT_RE.sub("", _split_h2(spec_text).preamble)
    lines = preamble.split("\n")
    values: list[str] = []
    current: list[str] | None = None
    for line in lines:
        m = _META_RE.match(line)
        if m:
            if current is not None:
                values.append(" ".join(current).strip())
                current = None
            if m.group("name").casefold() == name.casefold():
                current = [m.group("value")]
            continue
        if current is not None and line[:1] in (" ", "\t") and line.strip():
            current.append(line.strip())
        elif current is not None:
            values.append(" ".join(current).strip())
            current = None
    if current is not None:
        values.append(" ".join(current).strip())
    return values


def _status_token(text: str) -> str | None:
    for line in _split_h2(text).preamble.split("\n"):
        m = _STATUS_RE.match(line)
        if m:
            return m.group("token")
    return None


def spec_status(spec_text: str) -> str | None:
    """The spec's `Status:` token, or None."""
    return _status_token(spec_text)


def plan_status(plan_text: str) -> str | None:
    """The plan's `Status:` token, or None."""
    return _status_token(plan_text)


def terminal_intent(spec_text: str) -> str | None:
    """The `## Terminal Intent` value: its first backticked token, else first word.

    Returns None when the section is absent. A repeated section refuses.
    """
    bodies = _find_sections(spec_text, "Terminal Intent")
    if not bodies:
        return None
    if len(bodies) > 1:
        raise ProjectionRefused(
            "ambiguous-reference", "Terminal Intent", "the Terminal Intent heading repeats"
        )
    body = bodies[0].split("\n", 1)[1] if "\n" in bodies[0] else ""
    tick = re.search(r"`([^`\n]+)`", body)
    if tick:
        return tick.group(1).strip()
    word = re.search(r"[A-Za-z][A-Za-z-]*", body)
    return word.group(0) if word else ""


def _cited_record_path(token: str, list_dir: Callable[[str], list[str]]) -> str | None:
    """Resolve an `ADR-n`, `RFC-n`, or repository path token to one record path."""
    m = _CITED_ID_RE.search(token)
    if m:
        directory = "docs/adr" if m.group("kind") == "ADR" else "docs/rfc"
        number = m.group("num").zfill(4)
        names = [
            n for n in list_dir(directory) if n.startswith(f"{number}-") and n.endswith(".md")
        ]
        if len(names) != 1:
            raise ProjectionRefused(
                "unreadable-reference", token, f"{token} resolves to {len(names)} records"
            )
        return f"{directory}/{names[0]}"
    candidate = token.strip().strip("`")
    if candidate.endswith(".md") and "/" in candidate:
        return candidate
    return None


def _record_section(text: str, kind: str) -> str:
    title = {"ADR": "Decision", "RFC": "Proposal"}.get(kind)
    if title is None:
        return text
    bodies = _find_sections(text, title)
    if len(bodies) != 1:
        return text
    return bodies[0]


class EnvelopeProjection(NamedTuple):
    """The six reference values and the cited records they read."""

    refs: dict[str, str]
    cited_paths: tuple[str, ...]


def envelope_references(
    spec_text: str,
    *,
    read_record: Callable[[str], str],
    list_dir: Callable[[str], list[str]],
) -> EnvelopeProjection:
    """Derive the six reviewed-envelope reference values from the working spec.

    *read_record* returns a cited record's text by repository-relative path and
    raises ``OSError`` or ``ValueError`` when it cannot be read; *list_dir*
    returns the file names in a repository-relative directory, or ``[]``.
    """
    for heading in _PROTECTED_HEADINGS:
        if len(_find_sections(spec_text, heading)) > 1:
            raise ProjectionRefused(
                "ambiguous-reference", heading, f"the {heading} heading repeats"
            )
    content: dict[str, list[str]] = {}
    for name, headings in _SECTION_OWNERS.items():
        parts = []
        for heading in headings:
            found = _find_sections(spec_text, heading)
            parts.append(_canonical(found[0]) if found else f"## {heading}")
        content[name] = parts
    cited: list[str] = []
    for field, ref in (
        ("Constrained by", "authority_and_security"),
        ("Contract", "public_contracts"),
    ):
        values = spec_metadata_value(spec_text, field)
        if len(values) > 1:
            raise ProjectionRefused(
                "ambiguous-reference", f"{field}:", f"the {field}: field repeats"
            )
        value = values[0] if values else ""
        content[ref] = [f"{field}: {_normalize(value)}"]
        if ref != "authority_and_security":
            continue
        for token in re.split(r"[,;]", value):
            if not token.strip():
                continue
            token = token.strip()
            path = _cited_record_path(token, list_dir)
            if path is None:
                continue
            try:
                text = read_record(path)
            except (OSError, ValueError) as exc:
                raise ProjectionRefused(
                    "unreadable-reference", token.strip(), f"cited record {path} cannot be read"
                ) from exc
            m = _CITED_ID_RE.search(token)
            section = _record_section(text, m.group("kind") if m else "")
            content[ref].append(f"{path}\n{_canonical(section)}")
            cited.append(path)
    refs = {
        name: f"{name}:" + _sha256(name + "\n" + "\n".join(content[name]))
        for name in ENVELOPE_REFERENCE_NAMES
    }
    return EnvelopeProjection(refs, tuple(sorted(set(cited))))


# ── Task projection ──────────────────────────────────────────────────────────


def _task_identity(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:48].strip("-") or "task"
    return f"{slug}-{_sha256(title)[:8]}"


def _fields(body_lines: list[str], *, indented_only: bool = False) -> dict[str, list[str]]:
    """Top-level `**Name:**` fields, each with its continuation lines.

    In a task body every line up to the next field continues the field. Outside
    tasks (*indented_only*), only indented lines continue it.
    """
    fields: dict[str, list[str]] = {}
    current: list[str] | None = None
    fence: tuple[str, int] | None = None
    for line in body_lines:
        m = _FENCE_RE.match(line)
        if m:
            char, run = m.group("run")[0], len(m.group("run"))
            if fence is None:
                fence = (char, run)
            elif char == fence[0] and run >= fence[1] and not m.group("info").strip():
                fence = None
        elif fence is None:
            f = _FIELD_RE.match(line)
            if f:
                # A repeated field extends the first, so no authored line is lost.
                current = fields.setdefault(f.group("name").strip(), [])
                current.append(f.group("rest"))
                continue
        if current is not None and indented_only and fence is None and not line[:1].isspace():
            current = None
        if current is not None:
            current.append(line)
    return fields


def _parse_stubs(tests_lines: list[str]) -> list[dict]:
    """Extract `stub path=... run="..." red-exit=...` fences from a Tests field."""
    stubs: list[dict] = []
    i = 0
    while i < len(tests_lines):
        m = _FENCE_RE.match(tests_lines[i])
        info = m.group("info").strip() if m else ""
        if not m or not (info == "stub" or info.startswith("stub ")):
            i += 1
            continue
        indent, char, run = m.group("indent"), m.group("run")[0], len(m.group("run"))
        attrs: dict[str, str] = {}
        rest = info[len("stub") :]
        position = 0
        while True:
            token = _STUB_ATTR_RE.match(rest, position)
            if token is None:
                break
            key = token.group("key")
            value = (
                token.group("quoted") if token.group("quoted") is not None else token.group("bare")
            )
            if key not in ("path", "run", "red-exit") or key in attrs:
                raise ProjectionRefused(
                    "invalid-stub-fence", "plan author", f"stub fence has bad attribute {key!r}"
                )
            attrs[key] = value
            position = token.end()
        if rest[position:].strip():
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "stub fence info is malformed"
            )
        path, command = attrs.get("path", ""), attrs.get("run", "")
        segments = path.split("/")
        if (
            not path
            or path.startswith("/")
            or "\\" in path
            or ":" in path
            or any(s in ("", ".", "..") for s in segments)
        ):
            raise ProjectionRefused(
                "invalid-stub-path", "plan author", "stub path must be repository-relative"
            )
        if not command.strip():
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "stub fence needs a run command"
            )
        try:
            red_exit = sorted({int(code) for code in attrs.get("red-exit", "1").split(",")})
        except ValueError as exc:
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "red-exit must list integers"
            ) from exc
        if any(not 0 <= code <= 255 for code in red_exit):
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "red-exit codes must be 0 to 255"
            )
        payload: list[str] = []
        i += 1
        while i < len(tests_lines):
            close = _FENCE_RE.match(tests_lines[i])
            if (
                close
                and close.group("run")[0] == char
                and len(close.group("run")) >= run
                and not close.group("info").strip()
            ):
                break
            line = tests_lines[i]
            payload.append(line[len(indent) :] if line.startswith(indent) else line.lstrip(" \t"))
            i += 1
        else:
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "stub fence is not closed"
            )
        data = "\n".join(payload) + "\n"
        if len(data.encode("utf-8")) > _MAX_STUB_BYTES:
            raise ProjectionRefused(
                "invalid-stub-fence", "plan author", "stub payload is too large"
            )
        stubs.append({
            "path": path,
            "run": command,
            "red_exit": red_exit,
            "digest": _sha256(data),
            "content": data,
        })
        i += 1
    return stubs


def _effect_names(value: str) -> list[str]:
    names = []
    for raw in value.split(","):
        name = raw.strip().strip("`").strip()
        if not name or name.casefold() == "none":
            continue
        if not _EFFECT_NAME_RE.fullmatch(name):
            raise ProjectionRefused(
                "invalid-effect-name", "plan author", f"effect name {name!r} is invalid"
            )
        names.append(name)
    return names


class PlanProjection(NamedTuple):
    """Projected tasks in plan order, and the plan-level finish effects."""

    tasks: list[dict]
    finish_effects: list[str]


def project_plan(plan_text: str) -> PlanProjection:
    """Project task-contract records and finish effects from plan text.

    Refuses an untitled task, an effect name repeated across `**Effects:**`
    lines, a malformed stub fence, and an unsafe stub path.
    """
    text = plan_text.replace("\r\n", "\n").replace("\r", "\n")
    sections = walk_task_sections(text)
    positions = [s.task_id for s in sections]
    local_ids = set(positions)
    raw: list[tuple[_TaskSection, str, dict[str, list[str]]]] = []
    outside: list[str] = text[: sections[0].start].split("\n") if sections else text.split("\n")
    for section in sections:
        heading, _, body = text[section.start : section.end].partition("\n")
        title_match = _TASK_TITLE_RE.match(heading)
        title = title_match.group("title").strip() if title_match else ""
        if not title:
            raise ProjectionRefused(
                "untitled-task", "plan author", f"{section.task_id} has no title"
            )
        # Content after the last task's own level-2 heading belongs to the plan, not the task.
        body_lines: list[str] = []
        tail: list[str] = []
        for line in body.split("\n"):
            if tail or (_H2_RE.match(line) and not line.startswith("###")):
                tail.append(line)
            else:
                body_lines.append(line)
        outside.extend(tail)
        raw.append((section, title, _fields(body_lines)))
    finish: list[str] = []
    for name, lines in _fields(outside, indented_only=True).items():
        if name.casefold() == "effects":
            finish.extend(_effect_names(" ".join(line.strip() for line in lines)))
    # A repeated title is told apart by its order among the tasks sharing it.
    identity_of: dict[str, str] = {}
    seen: dict[str, int] = {}
    for section, title, _ in raw:
        seen[title] = seen.get(title, 0) + 1
        suffix = "" if seen[title] == 1 else f"-{seen[title]}"
        identity_of[section.task_id] = _task_identity(title) + suffix
    tasks: list[dict] = []
    for section, title, fields in raw:

        def field(name: str, fields: dict[str, list[str]] = fields) -> str:
            for key, value in fields.items():
                if key.casefold() == name.casefold():
                    return _normalize("\n".join(value))
            return ""

        tests_lines = next((v for k, v in fields.items() if k.casefold() == "tests"), [])
        stubs = _parse_stubs(tests_lines)
        effects = _effect_names(field("Effects"))
        local, _cross = parse_depends_on(field("Depends on"), local_ids)
        depends = [identity_of[p] for p in positions if p in local and p != section.task_id]
        pinned = {
            "title": title,
            "tests": field("Tests"),
            "touches": field("Touches"),
            "done_when": field("Done when"),
            "effects": field("Effects"),
        }
        stub_digest = (
            _sha256(
                json.dumps(
                    [{k: s[k] for k in ("path", "run", "red_exit", "content")} for s in stubs],
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            if stubs
            else None
        )
        tasks.append({
            "schema_version": 1,
            "task_id": identity_of[section.task_id],
            "title": title,
            "position": section.task_id,
            "revision": _sha256(json.dumps(pinned, sort_keys=True, separators=(",", ":"))),
            "depends_on": depends,
            "touches": [
                g.strip().strip("`")
                for g in field("Touches").split("(")[0].split(",")
                if g.strip()
            ],
            "done_when": field("Done when"),
            "effects": effects,
            "verification_mode": field("Verification mode").split("\n")[0] or "unspecified",
            "stubs": stubs,
            "stub_digest": stub_digest,
            "no_stub": bool(re.search(r"\bno stub\b", field("Tests"), re.IGNORECASE)),
        })
    names = [n for t in tasks for n in t["effects"]] + finish
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ProjectionRefused(
            "duplicate-effect-name",
            "plan author",
            f"effect names repeat across Effects lines: {', '.join(duplicates)}",
        )
    return PlanProjection(tasks, finish)


def task_contract(task: dict) -> dict:
    """The task-contract.v1 record for a projected task (stub content omitted)."""
    record = dict(task)
    record["stubs"] = [
        {k: s[k] for k in ("path", "run", "red_exit", "digest")} for s in task["stubs"]
    ]
    return record


# ── Replan classification ────────────────────────────────────────────────────

# The refusal code and the owner who can amend each protected reference.
CHANGE_OWNERS: dict[str, tuple[str, str]] = {
    "spec_policy": ("criteria-changed", "spec-amendment owner"),
    "scope_and_non_goals": ("scope-changed", "spec-amendment owner"),
    "authority_and_security": ("authority-changed", "decision owner"),
    "public_contracts": ("contract-changed", "contract owner"),
    "durable_outputs": ("durable-outputs-changed", "spec-amendment owner"),
    "accepted_risk": ("accepted-risk-changed", "risk owner"),
}
TERMINAL_INTENT_CHANGE: tuple[str, str] = ("terminal-intent-changed", "plan-review authority")


def classify_replan(
    *,
    approved_envelope: dict,
    approved_intent: str,
    current_refs: dict[str, str],
    current_intent: str | None,
) -> tuple[str, str] | None:
    """Classify the working spec against the current approval pair.

    Returns ``None`` when the change needs no approval (a new task projection),
    or the ``(code, owner)`` of the refusal. The approval decision itself is the
    shared change classifier's; this names which reference moved and who owns it.
    """
    acceptance = _sibling("_acceptance.py")
    proposed = acceptance.derive_envelope(current_refs)
    intent = approved_intent if current_intent is None else current_intent
    verdict = acceptance.classify_change(
        current_envelope_fingerprint=approved_envelope["envelope_fingerprint"],
        current_terminal_intent=approved_intent,
        proposed_envelope_fingerprint=proposed["envelope_fingerprint"],
        proposed_terminal_intent=intent,
    )
    if verdict == "no-approval-required":
        return None
    for name in ENVELOPE_REFERENCE_NAMES:
        if approved_envelope["refs"].get(name) != current_refs.get(name):
            return CHANGE_OWNERS[name]
    return TERMINAL_INTENT_CHANGE
