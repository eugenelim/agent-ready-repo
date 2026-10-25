#!/usr/bin/env python3
"""Inventory rules for the workspace retirement record (spec workspace-retirement).

``check_repository`` applies the spec's inventory rules (AC-0001 to AC-0009,
AC-0019, AC-0021) to a repository root and returns every violation tagged with
its criterion. ``check_record`` applies the record rules (AC-0010 to AC-0016),
and ``workflow_wiring_violations`` checks that build-check runs this file on
every pull request (AC-0017). Standard library only; the check reads the
repository and writes nothing.
"""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SPEC_DIR = "docs/specs/workspace-retirement"
DEFAULT_INVENTORY = _REPO / _SPEC_DIR / "inventory.toml"
DEFAULT_RECORD = _REPO / _SPEC_DIR / "retirement-record.md"
DEFAULT_BRIEF = _REPO / "docs/product/briefs/workspace-registry-retirement-delivery.md"
_TERMINALITY_PATH = _REPO / "packs/core/.apm/skills/close-work/scripts/closure_terminality.py"

CLASSES = frozenset({
    "reader",
    "writer",
    "projection",
    "fixture",
    "seed",
    "guide",
    "promise",
    "contract",
    "record",
    "historical",
})
_WILDCARDS = "*?["
_MENTION_TOKENS = ("workspace.toml", "workspace-status", "workspace_status")
_PROVENANCE = re.compile(r"^\s*-\s*(\*\*)?Locator:(\*\*)?\s")
_STATUS_LINE = re.compile(r"^- \*\*Status:\*\*\s*(.*)$")
_SPEC_MD = re.compile(r"^(docs/specs/[^/]+)/spec\.md$")
_PACK_TEST_SKILL = re.compile(r"^(packs/[^/]+)/tests/skills/([^/]+)$")
_READINESS_PATH = "packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py"
_RFC_0106_CONTRACTS = (
    "docs/rfc/0064-ini-001-ai-native-ecosystem.md",
    "docs/product/AGENTS.md",
    "docs/product/intents/FEAT-0005-lifecycle-and-closure.md",
    "docs/product/intents/FEAT-0001-intent-identity-and-registration.md",
    "docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md",
)


@dataclass(frozen=True)
class Violation:
    """One broken rule: the criterion id, the offending path/row/fact, and why."""

    criterion: str
    subject: str
    detail: str

    def __str__(self) -> str:
        return f"{self.criterion}: {self.subject}: {self.detail}"


def _load_terminality() -> ModuleType:
    """Load close-work's terminal sets by file path, so they keep one home."""
    name = "_wr_inventory_closure_terminality"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _TERMINALITY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _status_value(text: str) -> str | None:
    """Return the first ``- **Status:**`` line's value, or None when absent."""
    for line in text.splitlines():
        found = _STATUS_LINE.match(line)
        if found:
            return found.group(1)
    return None


def _leading_word(status: str) -> str:
    found = re.match(r"[A-Za-z]+", status.strip())
    return found.group(0) if found else ""


def _typed_kind(path: str) -> str | None:
    """Classify a path as an intent, brief, or spec by the spec's Terms."""
    if fnmatch.fnmatchcase(path, "docs/product/intents/*.md"):
        return "intent"
    if fnmatch.fnmatchcase(path, "docs/product/briefs/*.md"):
        return "brief"
    if fnmatch.fnmatchcase(path, "docs/specs/*/spec.md"):
        return "spec"
    return None


def _is_terminal(kind: str, status: str) -> bool:
    terminality = _load_terminality()
    checks = {
        "intent": terminality.is_intent_terminal,
        "brief": terminality.is_brief_terminal,
        "spec": terminality.is_spec_terminal,
    }
    return bool(checks[kind](status))


class _Repo:
    """Tracked files of one repository root, with cached UTF-8 reads."""

    def __init__(self, root: Path) -> None:
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8", "surrogateescape")
        self.root = root
        self.tracked = sorted(p for p in listing.split("\0") if p)
        self._tracked_set = set(self.tracked)
        self._text: dict[str, str | None] = {}
        self.spec_dirs = {m.group(1) for p in self.tracked if (m := _SPEC_MD.match(p))}
        self.skill_dirs = {p.rsplit("/", 1)[0] for p in self.tracked if p.endswith("/SKILL.md")}
        self.skill_names = {d.rsplit("/", 1)[-1] for d in self.skill_dirs}

    def text(self, path: str) -> str | None:
        """File text, or None when it is not a readable regular UTF-8 file."""
        if path not in self._text:
            full = self.root / path
            try:
                data = None if full.is_symlink() or not full.is_file() else full.read_bytes()
                self._text[path] = None if data is None else data.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                self._text[path] = None
        return self._text[path]

    def spec_dir_of(self, path: str) -> str | None:
        parts = path.split("/")
        if len(parts) > 3 and parts[:2] == ["docs", "specs"]:
            candidate = "/".join(parts[:3])
            if candidate in self.spec_dirs:
                return candidate
        return None

    def is_skill_directory(self, prefix: str) -> bool:
        if prefix in self.skill_dirs:
            return True
        projected = prefix.split("/")[0] in (".claude", ".agents") and "/" in prefix
        if projected and prefix.rsplit("/", 1)[-1] in self.skill_names:
            return True
        found = _PACK_TEST_SKILL.match(prefix)
        return bool(found) and f"{found.group(1)}/.apm/skills/{found.group(2)}" in self.skill_dirs

    def spec_status_word(self, spec_dir: str) -> str | None:
        text = self.text(f"{spec_dir}/spec.md")
        status = None if text is None else _status_value(text)
        return None if status is None else _leading_word(status)


def _mention_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if any(tok in ln for tok in _MENTION_TOKENS)]


def _is_exempt(repo: _Repo, path: str, text: str, exact_patterns: set[str]) -> bool:
    """The spec's Exempt path rule."""
    if path in exact_patterns:
        return False
    kind = _typed_kind(path)
    if kind == "brief":
        status = _status_value(text)
        if status is not None and _is_terminal("brief", status):
            return True
    spec_dir = repo.spec_dir_of(path)
    if spec_dir is not None and repo.spec_status_word(spec_dir) == "Archived":
        return True
    if kind is not None or spec_dir is not None:
        return all(_PROVENANCE.match(ln) for ln in _mention_lines(text))
    return False


def _scanned_set(repo: _Repo, exact_patterns: set[str]) -> list[str]:
    scanned = []
    for path in repo.tracked:
        text = repo.text(path)
        if text is None or not _mention_lines(text):
            continue
        if not _is_exempt(repo, path, text, exact_patterns):
            scanned.append(path)
    return scanned


def _slice_numbers(brief: Path) -> set[int] | None:
    try:
        text = brief.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    numbers: set[int] = set()
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Delivery slices"
        elif inside and (found := re.match(r"(\d+)\.\s", line)):
            numbers.add(int(found.group(1)))
    return numbers


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _structure_violations(index: int, row: dict[str, Any]) -> list[Violation]:
    """AC-0001 per-row shape."""
    where = f"row[{index}] {row.get('pattern', '<no pattern>')!r}"
    found: list[Violation] = []
    for key in ("pattern", "consumer"):
        if not _nonempty_str(row.get(key)):
            found.append(Violation("AC-0001", where, f"`{key}` must be a non-empty string"))
    if not isinstance(row.get("class"), str):
        found.append(Violation("AC-0001", where, "`class` must be a string"))
    if "owner" not in row:
        found.append(Violation("AC-0001", where, "`owner` is required"))
    if "reads_order" in row and not isinstance(row["reads_order"], bool):
        found.append(Violation("AC-0001", where, "`reads_order` must be a boolean"))
    return found


def _wildcard_violation(repo: _Repo, where: str, pattern: str, cls: str) -> Violation | None:
    """AC-0005 for one row."""
    if not any(c in pattern for c in _WILDCARDS):
        return None
    prefix = pattern[:-2] if pattern.endswith("/*") else ""
    if prefix and not any(c in prefix for c in _WILDCARDS):
        if repo.is_skill_directory(prefix) and cls not in ("historical", "record"):
            return None
        if prefix in repo.spec_dirs and cls in ("contract", "historical"):
            return None
    return Violation(
        "AC-0005",
        where,
        "wildcard pattern must be `<prefix>/*` over one skill directory (not historical/record) "
        "or one spec directory (contract/historical)",
    )


def check_inventory(root: Path, inventory: Path, brief: Path) -> list[Violation]:
    """Apply AC-0001 to AC-0009, AC-0019 and AC-0021 to ``root``."""
    try:
        document = tomllib.loads(inventory.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        return [Violation("AC-0001", str(inventory), f"cannot read or parse inventory: {exc}")]
    rows = document.get("row")
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        return [
            Violation("AC-0001", str(inventory), "needs a non-empty array of tables named `row`")
        ]
    slices = _slice_numbers(brief)
    violations: list[Violation] = []
    if slices is None:
        violations.append(Violation("INPUT", str(brief), "cannot read the delivery brief"))
        slices = set()
    repo = _Repo(root)

    def label(i: int) -> str:
        return f"row[{i}] {rows[i].get('pattern')!r}"

    valid = [
        i
        for i, r in enumerate(rows)
        if _nonempty_str(r.get("pattern")) and isinstance(r.get("class"), str)
    ]
    for i, row in enumerate(rows):
        violations += _structure_violations(i, row)
    for i in valid:
        row = rows[i]
        cls, pattern = row["class"], row["pattern"]
        if cls not in CLASSES:
            violations.append(Violation("AC-0002", label(i), f"unknown class {cls!r}"))
        owner = row.get("owner")
        if "owner" in row:
            if owner == "none":
                if cls not in ("historical", "record"):
                    violations.append(
                        Violation(
                            "AC-0003",
                            label(i),
                            "only historical and record rows may carry owner `none`",
                        )
                    )
            elif isinstance(owner, bool) or not isinstance(owner, int) or owner not in slices:
                violations.append(
                    Violation(
                        "AC-0003",
                        label(i),
                        f"owner {owner!r} is neither `none` nor a brief slice number",
                    )
                )
        if (bad := _wildcard_violation(repo, label(i), pattern, cls)) is not None:
            violations.append(bad)
        if cls == "record" and not pattern.startswith(f"{_SPEC_DIR}/"):
            violations.append(
                Violation("AC-0019", label(i), f"record pattern must start with {_SPEC_DIR}/")
            )
        if cls == "projection":
            source = row.get("source")
            sources = {rows[j]["pattern"] for j in valid if rows[j]["class"] != "projection"}
            if not isinstance(source, str) or source not in sources:
                violations.append(
                    Violation(
                        "AC-0007",
                        label(i),
                        "projection `source` must equal the pattern of a non-projection row",
                    )
                )

    def governing(path: str) -> int | None:
        return next((i for i in valid if fnmatch.fnmatchcase(path, rows[i]["pattern"])), None)

    exact = {rows[i]["pattern"] for i in valid}
    scanned = _scanned_set(repo, exact)
    governs: dict[int, int] = {}
    for path in scanned:
        gi = governing(path)
        if gi is None:
            violations.append(Violation("AC-0004", path, "no inventory row governs this path"))
            gi_class = None
        else:
            governs[gi] = governs.get(gi, 0) + 1
            gi_class = rows[gi]["class"]
        if path.startswith((".claude/", ".agents/")) and gi_class != "projection":
            violations.append(
                Violation(
                    "AC-0007", path, "path under .claude/ or .agents/ needs a projection row"
                )
            )
        if gi_class == "historical":
            violations += _historical_violations(repo, path)
    for i in valid:
        if i not in governs:
            violations.append(Violation("AC-0006", label(i), "governs no path in the scanned set"))

    gi = governing(_READINESS_PATH)
    if gi is None or "readiness bridge" not in str(rows[gi].get("consumer", "")):
        violations.append(
            Violation(
                "AC-0009",
                _READINESS_PATH,
                "governing row's consumer must contain `readiness bridge`",
            )
        )
    for path in _RFC_0106_CONTRACTS:
        gi = governing(path)
        if gi is None or rows[gi]["class"] != "contract":
            violations.append(Violation("AC-0021", path, "governing row must be a `contract` row"))
    return violations


def _historical_violations(repo: _Repo, path: str) -> list[Violation]:
    """AC-0008 for one path governed by a historical row."""
    text = repo.text(path) or ""
    kind = _typed_kind(path)
    found: list[Violation] = []
    if kind is not None:
        status = _status_value(text)
        if status is None:
            found.append(Violation("AC-0008", path, "typed file has no `- **Status:**` line"))
        elif not _is_terminal(kind, status):
            found.append(Violation("AC-0008", path, f"{kind} status {status!r} is not terminal"))
    spec_dir = repo.spec_dir_of(path)
    if spec_dir is not None and kind != "spec":
        status = _status_value(repo.text(f"{spec_dir}/spec.md") or "")
        if status is None or not _is_terminal("spec", status):
            found.append(
                Violation("AC-0008", path, f"{spec_dir}/spec.md status {status!r} is not terminal")
            )
    return found


_RECORD_HEADINGS = ("Disposition", "Equivalence", "Compatibility closure", "Certification")
_COLUMNS = ("Fact", "Category", "Home", "Owner", "Authority")
_CATEGORIES = frozenset({
    "canonical artifact metadata",
    "derived state",
    "externally owned projection",
    "temporary migration state",
    "deliberate removal",
})
_LITERAL_FACTS = (
    "entry position",
    "spec registration as brief coverage evidence",
    "behavior outside tracked files",
)
_COVERAGE_FACT = "spec registration as brief coverage evidence"
_SCHEMA_PATH = "contracts/jsonschema/workspace-entry.schema.json"
_REGISTRY_PATH = "workspace.toml"
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]*)\)")
_ROW_SEPARATOR = re.compile(r"^:?-+:?$")
_INITIATIVE = re.compile(r"ini-[0-9]+")


def _fact_text(cell: str) -> str:
    """The spec's Fact text: the text with backtick code-span markers removed."""
    return cell.replace("`", "").strip()


def _headings(text: str) -> list[tuple[int, int, str]]:
    """(line index, level, heading text) for each heading outside a code fence."""
    found: list[tuple[int, int, str]] = []
    fence = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        elif not fence and (m := _HEADING.match(line)):
            found.append((index, len(m.group(1)), m.group(2)))
    return found


def _slug(heading: str) -> str:
    """GitHub heading slug: lowercase, keep letters, digits, ``_``, space, ``-``."""
    return re.sub(r"[^\w \-]", "", heading.lower()).replace(" ", "-")


def _section(text: str, headings: list[tuple[int, int, str]], at: int) -> str:
    """Text under ``headings[at]`` up to the next heading of the same or higher level."""
    lines = text.splitlines()
    start, level, _ = headings[at]
    end = len(lines)
    for index, other_level, _ in headings[at + 1 :]:
        if other_level <= level:
            end = index
            break
    return "\n".join(lines[start + 1 : end])


def _schema_facts(props: Any, prefix: str) -> set[str]:
    """Properties reached through ``properties`` keys alone, joined by ``.``."""
    facts: set[str] = set()
    if not isinstance(props, dict):
        return facts
    for name, sub in props.items():
        facts.add(f"{prefix}{name}")
        if isinstance(sub, dict) and "properties" in sub:
            facts |= _schema_facts(sub["properties"], f"{prefix}{name}.")
    return facts


def _registry_facts(table: dict[str, Any], prefix: tuple[str, ...]) -> set[str]:
    """Every key path of the registry, stopping at array values."""
    facts: set[str] = set()
    for key, value in table.items():
        parts = prefix + (key,)
        if len(parts) == 1 and _INITIATIVE.fullmatch(key):
            parts = ("<initiative>",)
        facts.add(".".join(parts))
        if isinstance(value, dict):
            facts |= _registry_facts_under(value, parts)
    return facts


def _registry_facts_under(table: dict[str, Any], parts: tuple[str, ...]) -> set[str]:
    facts: set[str] = set()
    for key, value in table.items():
        child = parts + (key,)
        facts.add(".".join(child))
        if isinstance(value, dict):
            facts |= _registry_facts_under(value, child)
    return facts


def _fact_set(root: Path) -> tuple[set[str], list[Violation]]:
    """The AC-0011 fact set for ``root``, plus any input problem found reading it."""
    problems: list[Violation] = []
    facts = set(_LITERAL_FACTS)
    try:
        schema = json.loads((root / _SCHEMA_PATH).read_text(encoding="utf-8"))
        facts |= _schema_facts(schema.get("properties"), "entry.")
        for name, definition in (schema.get("$defs") or {}).items():
            if isinstance(definition, dict):
                facts |= _schema_facts(definition.get("properties"), f"{name}.")
    except (OSError, UnicodeDecodeError, ValueError, AttributeError) as exc:
        problems.append(Violation("INPUT", _SCHEMA_PATH, f"cannot read the schema: {exc}"))
    try:
        registry = tomllib.loads((root / _REGISTRY_PATH).read_text(encoding="utf-8"))
        facts |= _registry_facts(registry, ())
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        problems.append(Violation("INPUT", _REGISTRY_PATH, f"cannot read the registry: {exc}"))
    return facts, problems


def _split_row(line: str) -> list[str]:
    cells = re.split(r"(?<!\\)\|", line.strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.replace("\\|", "|").strip() for c in cells]


def _disposition_rows(section: str) -> tuple[list[dict[str, str]], str | None]:
    """The Disposition table's rows keyed by column, or (rows, reason) when unusable."""
    table = [ln for ln in section.splitlines() if ln.lstrip().startswith("|")]
    if not table:
        return [], "no Markdown table"
    header = [_fact_text(c) for c in _split_row(table[0])]
    missing = [c for c in _COLUMNS if c not in header]
    if missing:
        return [], f"table lacks column(s) {', '.join(missing)}"
    rows = []
    for line in table[1:]:
        cells = _split_row(line)
        if cells and all(_ROW_SEPARATOR.match(c) for c in cells):
            continue
        cells += [""] * (len(header) - len(cells))
        rows.append({name: cells[i] for i, name in enumerate(header)})
    return rows, None


def _removal_violations(root: Path, record: Path, fact: str, authority: str) -> list[Violation]:
    """AC-0014 and AC-0015 for one ``deliberate removal`` row."""
    where = f"Disposition row {fact!r}"
    links = _LINK.findall(authority)
    if len(links) != 1:
        return [
            Violation("AC-0014", where, f"Authority holds {len(links)} links, needs exactly one")
        ]
    target, _, anchor = links[0].partition("#")
    root_real = root.resolve()
    try:
        resolved = (record.parent / target).resolve()
        relative = resolved.relative_to(root_real).as_posix()
    except (ValueError, OSError):
        return [Violation("AC-0014", where, f"link {links[0]!r} leaves the repository")]
    if not relative.startswith(("docs/rfc/", "docs/adr/")):
        return [Violation("AC-0014", where, f"{relative} is not under docs/rfc/ or docs/adr/")]
    try:
        if (root / relative).is_symlink() or not resolved.is_file():
            raise OSError("not a regular file")
        body = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Violation("AC-0014", where, f"cannot read {relative}: {exc}")]
    status = _status_value(body)
    if status is None or _leading_word(status) != "Accepted":
        return [Violation("AC-0014", where, f"{relative} status {status!r} is not Accepted")]
    heads = _headings(body)
    for at, (_, _, title) in enumerate(heads):
        if _slug(title) == anchor and fact in _fact_text(_section(body, heads, at)):
            return []
    return [
        Violation(
            "AC-0015",
            where,
            f"no heading in {relative} slugs to {anchor!r} with a section naming the Fact",
        )
    ]


def _coverage_violation(root: Path, home: str) -> Violation | None:
    """AC-0016 for the coverage row's Home cell."""
    text = _fact_text(_LINK.sub(lambda m: f" {m.group(1)} ", home))
    if text == "nothing":
        return None
    tracked = set(_Repo(root).tracked)
    for token in re.split(r"[\s,;]+", text):
        if token.strip(".,;:()").partition("#")[0] in tracked:
            return None
    return Violation(
        "AC-0016",
        f"Disposition row {_COVERAGE_FACT!r}",
        "Home names no tracked path and is not exactly `nothing`",
    )


def check_record(root: Path, record: Path) -> list[Violation]:
    """Apply AC-0010 to AC-0016 to the record at ``record`` for the repository ``root``."""
    try:
        text = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Violation("AC-0010", str(record), f"cannot read the record: {exc}")]
    violations: list[Violation] = []
    heads = _headings(text)
    top = [(i, t) for i, level, t in heads if level == 2]
    if tuple(t for _, t in top) != _RECORD_HEADINGS:
        violations.append(
            Violation(
                "AC-0010",
                str(record),
                f"`##` headings are {[t for _, t in top]}, need {list(_RECORD_HEADINGS)}",
            )
        )
    disposition = next(
        (at for at, (_, lv, t) in enumerate(heads) if lv == 2 and t == "Disposition"), None
    )
    if disposition is None:
        return violations + [Violation("AC-0011", str(record), "no `## Disposition` section")]
    rows, problem = _disposition_rows(_section(text, heads, disposition))
    if problem is not None:
        return violations + [Violation("AC-0011", "Disposition", problem)]
    facts, inputs = _fact_set(root)
    violations += inputs
    present = {_fact_text(r["Fact"]) for r in rows}
    for fact in sorted(facts - present):
        violations.append(Violation("AC-0011", fact, "fact set member has no Disposition row"))
    for row in rows:
        fact = _fact_text(row["Fact"])
        where = f"Disposition row {fact!r}"
        for column in ("Home", "Owner"):
            if not _fact_text(row[column]):
                violations.append(Violation("AC-0012", where, f"{column} is empty"))
        category = _fact_text(row["Category"])
        if category not in _CATEGORIES:
            violations.append(
                Violation("AC-0013", where, f"Category {category!r} is not one of five")
            )
        if category == "deliberate removal":
            violations += _removal_violations(root, record, fact, row["Authority"])
        if fact == _COVERAGE_FACT and (bad := _coverage_violation(root, row["Home"])) is not None:
            violations.append(bad)
    return violations


def check_repository(
    root: Path = _REPO,
    inventory: Path = DEFAULT_INVENTORY,
    record: Path = DEFAULT_RECORD,
    brief: Path = DEFAULT_BRIEF,
) -> list[Violation]:
    """Every rule the spec enforces, against ``root``; an empty list means pass."""
    return check_inventory(root, inventory, brief) + check_record(root, record)


# ───────────────────────────── fixture tests ─────────────────────────────────

_MENTION = "reads workspace.toml here\n"
_READINESS = "packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py"
_RFC0064 = "docs/rfc/0064-ini-001-ai-native-ecosystem.md"
_ADR0119 = "docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md"
_PRODUCT_AGENTS = "docs/product/AGENTS.md"
_FEAT0005 = "docs/product/intents/FEAT-0005-lifecycle-and-closure.md"
_FEAT0001 = "docs/product/intents/FEAT-0001-intent-identity-and-registration.md"
_FULFILLED = "- **Status:** Fulfilled\n\n" + _MENTION

_BRIEF = (
    "# Brief\n\n## Delivery slices\n\nNumbering note.\n\n"
    + "".join(f"{n}. **Slice {n}.** text\n" for n in range(1, 10))
    + "\n## Other\n\n10. not a slice\n"
)

_BASE_FILES: dict[str, str] = {
    _READINESS: "# " + _MENTION,
    _RFC0064: _MENTION,
    _ADR0119: _MENTION,
    _PRODUCT_AGENTS: _MENTION,
    _FEAT0005: _FULFILLED,
    _FEAT0001: _FULFILLED,
}


def _row(
    pattern: str, cls: str, consumer: str = "a consumer", owner: Any = 9, **extra: Any
) -> dict[str, Any]:
    return {"pattern": pattern, "class": cls, "consumer": consumer, "owner": owner, **extra}


_BASE_ROWS: list[dict[str, Any]] = [
    _row(_READINESS, "reader", "navigate-intents readiness bridge", 8),
    _row(_RFC0064, "contract"),
    _row(_ADR0119, "contract"),
    _row(_PRODUCT_AGENTS, "contract"),
    _row(_FEAT0005, "contract"),
    _row(_FEAT0001, "contract"),
]


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(value)


def _render_inventory(rows: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for row in rows:
        out.append("[[row]]")
        out.extend(f"{key} = {_toml_value(val)}" for key, val in row.items())
        out.append("")
    return "\n".join(out)


def _run(
    tmp_path: Path,
    extra_files: dict[str, str] | None = None,
    rows: list[dict[str, Any]] | None = None,
    *,
    drop_files: tuple[str, ...] = (),
    inventory_text: str | None = None,
) -> list[Violation]:
    """Build a tiny git repo, write inventory and brief outside it, run the inventory rules."""
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    files = {k: v for k, v in _BASE_FILES.items() if k not in drop_files}
    files.update(extra_files or {})
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    inventory = tmp_path / "inventory.toml"
    inventory.write_text(
        inventory_text
        if inventory_text is not None
        else _render_inventory(_BASE_ROWS + (rows or [])),
        encoding="utf-8",
    )
    brief = tmp_path / "brief.md"
    brief.write_text(_BRIEF, encoding="utf-8")
    return check_inventory(root, inventory, brief)


def _tags(violations: list[Violation]) -> set[str]:
    return {v.criterion for v in violations}


def _only(violations: list[Violation], criterion: str) -> None:
    assert _tags(violations) == {criterion}, [str(v) for v in violations]


def test_clean_base_fixture_passes(tmp_path: Path) -> None:
    assert _run(tmp_path) == []


def test_ac0001_unparseable_inventory(tmp_path: Path) -> None:
    _only(_run(tmp_path, inventory_text="[[row\n"), "AC-0001")


def test_ac0001_empty_row_array(tmp_path: Path) -> None:
    _only(_run(tmp_path, inventory_text="title = 'x'\n"), "AC-0001")


def test_ac0001_missing_inventory(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    brief = tmp_path / "brief.md"
    brief.write_text(_BRIEF, encoding="utf-8")
    found = check_inventory(root, tmp_path / "nope.toml", brief)
    _only(found, "AC-0001")


def test_ac0001_empty_consumer(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "guide", consumer="")]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, rows), "AC-0001")


def test_ac0001_missing_owner(tmp_path: Path) -> None:
    row = _row("notes.txt", "guide")
    del row["owner"]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, [row]), "AC-0001")


def test_ac0001_reads_order_must_be_boolean(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "reader", reads_order="yes")]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, rows), "AC-0001")


def test_reads_order_boolean_passes(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "reader", reads_order=True)]
    assert _run(tmp_path, {"notes.txt": _MENTION}, rows) == []


def test_ac0002_unknown_class(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "mystery")]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, rows), "AC-0002")


def test_ac0003_owner_not_a_slice(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "guide", owner=10)]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, rows), "AC-0003")


def test_ac0003_none_on_live_class(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "guide", owner="none")]
    _only(_run(tmp_path, {"notes.txt": _MENTION}, rows), "AC-0003")


def test_ac0003_none_on_historical_passes(tmp_path: Path) -> None:
    rows = [_row("CHANGELOG.md", "historical", owner="none")]
    assert _run(tmp_path, {"CHANGELOG.md": _MENTION}, rows) == []


def test_ac0004_unrowed_mention(tmp_path: Path) -> None:
    found = _run(tmp_path, {"tools/planted_mention.py": _MENTION})
    _only(found, "AC-0004")
    assert "tools/planted_mention.py" in found[0].subject


def test_ac0004_non_utf8_file_is_outside_scanned_set(tmp_path: Path) -> None:
    assert _run(tmp_path, {"blob.bin": "placeholder"}) == []
    blob = tmp_path / "repo" / "blob.bin"
    blob.write_bytes(b"\xff\xfe workspace.toml \xff")
    subprocess.run(
        ["git", "-C", str(tmp_path / "repo"), "add", "-A"], check=True, capture_output=True
    )
    again = check_inventory(tmp_path / "repo", tmp_path / "inventory.toml", tmp_path / "brief.md")
    assert again == []


def test_ac0004_shipped_spec_not_exempt(tmp_path: Path) -> None:
    files = {"docs/specs/feat/spec.md": "- **Status:** Shipped (2026-09-11)\n\n" + _MENTION}
    _only(_run(tmp_path, files), "AC-0004")


def test_ac0004_draft_spec_not_exempt(tmp_path: Path) -> None:
    files = {"docs/specs/feat/spec.md": "- **Status:** Draft\n\n" + _MENTION}
    _only(_run(tmp_path, files), "AC-0004")


def test_exempt_draft_intent_with_only_locator_mention(tmp_path: Path) -> None:
    files = {
        "docs/product/intents/FEAT-0099-x.md": "- **Status:** Draft\n- Locator: workspace.toml\n"
    }
    assert _run(tmp_path, files) == []


def test_exempt_bold_locator_form(tmp_path: Path) -> None:
    files = {
        "docs/product/intents/FEAT-0099-x.md": "- **Status:** Draft\n- **Locator:** workspace-status\n"
    }
    assert _run(tmp_path, files) == []


def test_exempt_archived_spec_notes_file(tmp_path: Path) -> None:
    files = {
        "docs/specs/old/spec.md": "- **Status:** Archived\n",
        "docs/specs/old/notes/n.md": _MENTION,
    }
    assert _run(tmp_path, files) == []


def test_exempt_terminal_brief(tmp_path: Path) -> None:
    files = {"docs/product/briefs/old.md": "- **Status:** Shipped\n\n" + _MENTION}
    assert _run(tmp_path, files) == []


def test_live_brief_not_exempt(tmp_path: Path) -> None:
    files = {"docs/product/briefs/live.md": "- **Status:** Ready\n\n" + _MENTION}
    _only(_run(tmp_path, files), "AC-0004")


def test_exact_row_overrides_exemption(tmp_path: Path) -> None:
    path = "docs/product/intents/FEAT-0098-x.md"
    files = {path: "- **Status:** Draft\n- Locator: workspace.toml\n"}
    # The exact row names a path the rule would exempt, so it stays scanned and governs.
    assert _run(tmp_path, files, [_row(path, "contract")]) == []


def test_ac0005_bare_star(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "guide"), _row("*", "guide")]
    _only(_run(tmp_path, {"notes.txt": _MENTION, "other.txt": _MENTION}, rows), "AC-0005")


def test_ac0005_skills_root_wildcard(tmp_path: Path) -> None:
    files = {
        "packs/core/.apm/skills/a/SKILL.md": "# a\n",
        "packs/core/.apm/skills/a/x.md": _MENTION,
    }
    rows = [
        _row("packs/core/.apm/skills/a/x.md", "reader"),
        _row("packs/core/.apm/skills/*", "reader"),
    ]
    files["packs/core/.apm/skills/b/y.md"] = _MENTION
    _only(_run(tmp_path, files, rows), "AC-0005")


def test_ac0005_guides_wildcard(tmp_path: Path) -> None:
    files = {"guides/a.md": _MENTION, "guides/b.md": _MENTION}
    rows = [_row("guides/a.md", "guide"), _row("guides/*", "guide")]
    _only(_run(tmp_path, files, rows), "AC-0005")


def test_ac0005_controls_skill_dir_and_exact_changelog(tmp_path: Path) -> None:
    files = {
        "packs/core/.apm/skills/workspace-status/SKILL.md": "# ws\n",
        "packs/core/.apm/skills/workspace-status/engine.py": _MENTION,
        "CHANGELOG.md": _MENTION,
    }
    rows = [
        _row("packs/core/.apm/skills/workspace-status/*", "reader"),
        _row("CHANGELOG.md", "historical", owner="none"),
    ]
    assert _run(tmp_path, files, rows) == []


def test_ac0005_skill_dir_wildcard_with_historical_class(tmp_path: Path) -> None:
    files = {
        "packs/core/.apm/skills/ws/SKILL.md": "# ws\n",
        "packs/core/.apm/skills/ws/engine.py": _MENTION,
    }
    rows = [_row("packs/core/.apm/skills/ws/*", "historical", owner="none")]
    _only(_run(tmp_path, files, rows), "AC-0005")


def test_ac0005_pack_test_skill_directory_is_a_skill_directory(tmp_path: Path) -> None:
    files = {
        "packs/core/.apm/skills/ws/SKILL.md": "# ws\n",
        "packs/core/tests/skills/ws/test_x.py": _MENTION,
    }
    rows = [_row("packs/core/tests/skills/ws/*", "fixture")]
    assert _run(tmp_path, files, rows) == []


def test_ac0005_spec_dir_wildcard_with_wrong_class(tmp_path: Path) -> None:
    files = {"docs/specs/f/spec.md": "- **Status:** Shipped\n\n" + _MENTION}
    _only(_run(tmp_path, files, [_row("docs/specs/f/*", "reader")]), "AC-0005")


def test_ac0005_spec_dir_control_historical_over_shipped(tmp_path: Path) -> None:
    files = {"docs/specs/f/spec.md": "- **Status:** Shipped (2026-09-11)\n\n" + _MENTION}
    assert _run(tmp_path, files, [_row("docs/specs/f/*", "historical", owner="none")]) == []


def test_ac0005_question_mark_in_exact_style_pattern(tmp_path: Path) -> None:
    _only(_run(tmp_path, {"a1.txt": _MENTION}, [_row("a?.txt", "guide")]), "AC-0005")


def test_ac0019_record_row_outside_spec_directory(tmp_path: Path) -> None:
    rows = [_row("notes/record.md", "record", owner="none")]
    _only(_run(tmp_path, {"notes/record.md": _MENTION}, rows), "AC-0019")


def test_ac0019_record_row_inside_spec_directory_passes(tmp_path: Path) -> None:
    path = "docs/specs/workspace-retirement/retirement-record.md"
    rows = [_row(path, "record", owner="none")]
    assert _run(tmp_path, {path: _MENTION}, rows) == []


def test_ac0006_shadowed_row(tmp_path: Path) -> None:
    rows = [_row("notes.txt", "guide"), _row("notes.txt", "reader")]
    found = _run(tmp_path, {"notes.txt": _MENTION}, rows)
    _only(found, "AC-0006")
    assert "notes.txt" in found[0].subject


def test_ac0006_row_governing_nothing(tmp_path: Path) -> None:
    _only(_run(tmp_path, rows=[_row("ghost.txt", "guide")]), "AC-0006")


def _projection_files() -> dict[str, str]:
    return {
        "packs/core/.apm/skills/x/SKILL.md": "# x\n",
        "packs/core/.apm/skills/x/a.md": _MENTION,
        ".claude/skills/x/a.md": _MENTION,
    }


def _projection_rows(source: str = "packs/core/.apm/skills/x/*") -> list[dict[str, Any]]:
    return [
        _row("packs/core/.apm/skills/x/*", "reader"),
        _row(".claude/skills/x/*", "projection", source=source),
    ]


def test_ac0007_projection_control(tmp_path: Path) -> None:
    assert _run(tmp_path, _projection_files(), _projection_rows()) == []


def test_ac0007_projection_source_does_not_match(tmp_path: Path) -> None:
    _only(_run(tmp_path, _projection_files(), _projection_rows("elsewhere/*")), "AC-0007")


def test_ac0007_projection_source_is_a_projection(tmp_path: Path) -> None:
    rows = [
        _row("packs/core/.apm/skills/x/*", "reader"),
        _row(".claude/skills/x/*", "projection", source=".claude/skills/x/*"),
    ]
    _only(_run(tmp_path, _projection_files(), rows), "AC-0007")


def test_ac0007_projection_row_missing_source(tmp_path: Path) -> None:
    rows = [_row("packs/core/.apm/skills/x/*", "reader"), _row(".claude/skills/x/*", "projection")]
    _only(_run(tmp_path, _projection_files(), rows), "AC-0007")


def test_ac0007_claude_path_governed_by_non_projection(tmp_path: Path) -> None:
    rows = [_row("packs/core/.apm/skills/x/*", "reader"), _row(".claude/skills/x/*", "reader")]
    _only(_run(tmp_path, _projection_files(), rows), "AC-0007")


def test_ac0008_draft_spec_under_historical_row(tmp_path: Path) -> None:
    path = "docs/specs/f/spec.md"
    files = {path: "- **Status:** Draft\n\n" + _MENTION}
    _only(_run(tmp_path, files, [_row(path, "historical", owner="none")]), "AC-0008")


def test_ac0008_contract_row_for_draft_spec_passes(tmp_path: Path) -> None:
    path = "docs/specs/f/spec.md"
    files = {path: "- **Status:** Draft\n\n" + _MENTION, "CHANGELOG.md": _MENTION}
    rows = [_row(path, "contract"), _row("CHANGELOG.md", "historical", owner="none")]
    assert _run(tmp_path, files, rows) == []


def test_ac0008_spec_directory_row_over_draft_plan(tmp_path: Path) -> None:
    files = {"docs/specs/f/spec.md": "- **Status:** Draft\n", "docs/specs/f/plan.md": _MENTION}
    found = _run(tmp_path, files, [_row("docs/specs/f/*", "historical", owner="none")])
    _only(found, "AC-0008")
    assert "docs/specs/f/plan.md" in found[0].subject


def test_ac0008_typed_file_without_status_line(tmp_path: Path) -> None:
    path = "docs/product/intents/FEAT-0097-x.md"
    _only(_run(tmp_path, {path: _MENTION}, [_row(path, "historical", owner="none")]), "AC-0008")


def test_ac0008_fulfilled_intent_under_historical_passes(tmp_path: Path) -> None:
    path = "docs/product/intents/FEAT-0097-x.md"
    files = {path: _FULFILLED}
    assert _run(tmp_path, files, [_row(path, "historical", owner="none")]) == []


def test_ac0008_accepted_intent_is_live(tmp_path: Path) -> None:
    path = "docs/product/intents/FEAT-0097-x.md"
    files = {path: "- **Status:** Accepted\n\n" + _MENTION}
    _only(_run(tmp_path, files, [_row(path, "historical", owner="none")]), "AC-0008")


def test_ac0009_wrong_consumer_text(tmp_path: Path) -> None:
    base = [r for r in _BASE_ROWS if r["pattern"] != _READINESS]
    bad = _render_inventory(base + [_row(_READINESS, "reader", "some reader", 8)])
    _only(_run(tmp_path, inventory_text=bad), "AC-0009")


def test_ac0009_no_governing_row(tmp_path: Path) -> None:
    base = [r for r in _BASE_ROWS if r["pattern"] != _READINESS]
    found = _run(tmp_path, inventory_text=_render_inventory(base))
    # The unrowed mention also fires AC-0004.
    assert _tags(found) == {"AC-0004", "AC-0009"}


def test_ac0021_wrong_class_on_named_contract(tmp_path: Path) -> None:
    base = [r for r in _BASE_ROWS if r["pattern"] != _PRODUCT_AGENTS]
    bad = _render_inventory(base + [_row(_PRODUCT_AGENTS, "guide")])
    found = _run(tmp_path, inventory_text=bad)
    _only(found, "AC-0021")
    assert _PRODUCT_AGENTS in found[0].subject


def test_ac0021_fulfilled_intent_with_contract_row_passes(tmp_path: Path) -> None:
    # _FEAT0001 is Fulfilled and keeps its exact contract row in the base fixture.
    assert _run(tmp_path) == []


def test_ac0021_named_contract_without_row(tmp_path: Path) -> None:
    base = [r for r in _BASE_ROWS if r["pattern"] != _RFC0064]
    found = _run(tmp_path, inventory_text=_render_inventory(base))
    # The file is also an unrowed mention, so AC-0004 fires beside AC-0021.
    assert _tags(found) == {"AC-0004", "AC-0021"}


# ───────────────────── terminal sets and the real repository ─────────────────


def test_terminal_sets_come_from_closure_terminality() -> None:
    module = _load_terminality()
    assert module.is_spec_terminal("Shipped (2026-09-11)")
    assert not module.is_spec_terminal("Implementing")
    assert module.is_intent_terminal("Fulfilled")
    assert module.is_brief_terminal("Shipped")


@pytest.mark.skipif(
    not (DEFAULT_INVENTORY.exists() and DEFAULT_RECORD.exists()),
    reason="expected to fail until T3 and T4 create the inventory and the record",
)
def test_real_repository_passes_every_rule() -> None:
    """AC-0018 / AC-0022: the same check on this checkout, no arguments."""
    found = check_repository()
    assert found == [], "\n".join(str(v) for v in found)


@pytest.mark.skipif(
    not DEFAULT_RECORD.exists(),
    reason="expected to fail until T4 creates docs/specs/workspace-retirement/retirement-record.md",
)
def test_real_record_passes_the_record_rules() -> None:
    found = check_record(_REPO, DEFAULT_RECORD)
    assert found == [], "\n".join(str(v) for v in found)


@pytest.mark.skipif(
    not DEFAULT_INVENTORY.exists(),
    reason="expected to fail until T3 creates docs/specs/workspace-retirement/inventory.toml",
)
def test_real_inventory_passes_the_inventory_rules() -> None:
    found = check_inventory(_REPO, DEFAULT_INVENTORY, DEFAULT_BRIEF)
    assert found == [], "\n".join(str(v) for v in found)


# ───────────────────────────── record rule fixtures ──────────────────────────────

_REC_PATH = "docs/specs/workspace-retirement/retirement-record.md"
_RFC_PATH = "docs/rfc/0001-fixture.md"
_RFC_ACCEPTED = (
    "# RFC 1\n\n- **Status:** Accepted (2026-01-01)\n\n"
    "## Errata\n\n- 2026-01-02: dropped behavior outside tracked files.\n\n"
    "## Where next_queue lives\n\nSection about `behavior outside tracked files` here.\n\n"
    "### Sub\n\nnested text\n\n## Other\n\nunrelated\n"
)
_FIXTURE_SCHEMA = {
    "properties": {
        "path": {"$ref": "#/$defs/p"},
        "summary": {"type": "string"},
        "nested": {"properties": {"inner": {"type": "string"}}},
    },
    "allOf": [{"properties": {"only_in_allof": {"type": "string"}}}],
    "$defs": {
        "source": {
            "properties": {"mode": {"enum": ["a"]}, "tracker": {"properties": {"id": {}}}},
            "allOf": [{"if": {"properties": {"mode": {"const": "a"}}}}],
        },
        "p": {"type": "string"},
    },
}
_FIXTURE_REGISTRY = '["ini-099"]\nname = "x"\n[ini-099.work]\nactive = []\n[backlog]\nopen = []\n'
_FIXTURE_FACTS = [
    "entry.path",
    "entry.summary",
    "entry.nested",
    "entry.nested.inner",
    "source.mode",
    "source.tracker",
    "source.tracker.id",
    "<initiative>",
    "<initiative>.name",
    "<initiative>.work",
    "<initiative>.work.active",
    "backlog",
    "backlog.open",
    "entry position",
    _COVERAGE_FACT,
    "behavior outside tracked files",
]
_REMOVAL = "behavior outside tracked files"
_REMOVAL_LINK = "[RFC 1 errata](../../rfc/0001-fixture.md#errata)"


def _base_rows() -> list[dict[str, str]]:
    rows = []
    for fact in _FIXTURE_FACTS:
        row = {
            "Fact": f"`{fact}`",
            "Category": "canonical artifact metadata",
            "Home": "`somewhere`",
            "Owner": "slice 9",
            "Authority": "",
        }
        if fact == _REMOVAL:
            row["Category"] = "deliberate removal"
            row["Authority"] = _REMOVAL_LINK
        if fact == _COVERAGE_FACT:
            row["Home"] = "nothing"
        rows.append(row)
    return rows


def _render_record(
    rows: list[dict[str, str]],
    headings: tuple[str, ...] = _RECORD_HEADINGS,
    columns: tuple[str, ...] = _COLUMNS,
) -> str:
    table = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    table += ["| " + " | ".join(r[c] for c in columns) + " |" for r in rows]
    out = []
    for heading in headings:
        out.append(f"## {heading}\n")
        if heading == "Disposition":
            out.append("\n".join(table) + "\n")
    return "\n".join(out)


def _record_check(
    tmp_path: Path,
    rows: list[dict[str, str]] | None = None,
    *,
    record_text: str | None = None,
    schema: dict[str, Any] | None = None,
    registry: str = _FIXTURE_REGISTRY,
    extra_files: dict[str, str] | None = None,
) -> list[Violation]:
    """Build a git repo holding schema, registry, an RFC, and a record; run the record rules."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    files = {
        _SCHEMA_PATH: json.dumps(_FIXTURE_SCHEMA if schema is None else schema),
        _REGISTRY_PATH: registry,
        _RFC_PATH: _RFC_ACCEPTED,
        _REC_PATH: _render_record(_base_rows() if rows is None else rows)
        if record_text is None
        else record_text,
    }
    files.update(extra_files or {})
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    return check_record(root, root / _REC_PATH)


def _with(rows: list[dict[str, str]], fact: str, **changes: str) -> list[dict[str, str]]:
    return [{**r, **changes} if _fact_text(r["Fact"]) == fact else r for r in rows]


def _without(rows: list[dict[str, str]], fact: str) -> list[dict[str, str]]:
    return [r for r in rows if _fact_text(r["Fact"]) != fact]


def test_record_clean_fixture_passes(tmp_path: Path) -> None:
    assert _record_check(tmp_path) == []


def test_fact_set_follows_properties_keys_only(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _record_check(tmp_path)
    facts, problems = _fact_set(root)
    assert problems == []
    assert facts == set(_FIXTURE_FACTS)
    assert not any("only_in_allof" in f for f in facts)


def test_ac0010_missing_heading(tmp_path: Path) -> None:
    text = _render_record(_base_rows(), headings=_RECORD_HEADINGS[:3])
    _only(_record_check(tmp_path, record_text=text), "AC-0010")


def test_ac0010_headings_out_of_order(tmp_path: Path) -> None:
    order = ("Disposition", "Compatibility closure", "Equivalence", "Certification")
    _only(_record_check(tmp_path, record_text=_render_record(_base_rows(), order)), "AC-0010")


def test_ac0010_extra_heading(tmp_path: Path) -> None:
    text = _render_record(_base_rows(), _RECORD_HEADINGS + ("Appendix",))
    _only(_record_check(tmp_path, record_text=text), "AC-0010")


def test_ac0010_heading_in_code_fence_is_ignored(tmp_path: Path) -> None:
    text = _render_record(_base_rows()) + "\n```\n## Not a heading\n```\n"
    assert _record_check(tmp_path, record_text=text) == []


def test_ac0010_missing_record_file(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _only(check_record(root, root / "nope.md"), "AC-0010")


def test_ac0011_fact_without_row(tmp_path: Path) -> None:
    found = _record_check(tmp_path, _without(_base_rows(), "entry.summary"))
    _only(found, "AC-0011")
    assert found[0].subject == "entry.summary"


def test_ac0011_allof_only_property_is_not_required(tmp_path: Path) -> None:
    assert _record_check(tmp_path) == []  # base rows carry no `entry.only_in_allof`


def test_ac0011_defs_property_without_definition_name(tmp_path: Path) -> None:
    rows = _with(_base_rows(), "source.mode", Fact="`mode`")
    found = _record_check(tmp_path, rows)
    _only(found, "AC-0011")
    assert found[0].subject == "source.mode"


def test_ac0011_initiative_table_written_by_its_name(tmp_path: Path) -> None:
    rows = _with(_base_rows(), "<initiative>.name", Fact="`ini-099.name`")
    found = _record_check(tmp_path, rows)
    _only(found, "AC-0011")
    assert found[0].subject == "<initiative>.name"


def test_ac0011_registry_key_without_row(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _without(_base_rows(), "backlog.open")), "AC-0011")


def test_ac0011_literal_fact_without_row(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _without(_base_rows(), "entry position")), "AC-0011")


def test_ac0011_table_missing_a_column(tmp_path: Path) -> None:
    text = _render_record(_base_rows(), columns=("Fact", "Category", "Home", "Owner"))
    _only(_record_check(tmp_path, record_text=text), "AC-0011")


def test_ac0011_no_table(tmp_path: Path) -> None:
    text = "".join(f"## {h}\n\n" for h in _RECORD_HEADINGS)
    _only(_record_check(tmp_path, record_text=text), "AC-0011")


def test_ac0012_empty_home(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _with(_base_rows(), "entry.path", Home="")), "AC-0012")


def test_ac0012_empty_owner(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _with(_base_rows(), "entry.path", Owner="")), "AC-0012")


def test_ac0013_sixth_category(tmp_path: Path) -> None:
    rows = _with(_base_rows(), "entry.path", Category="archived state")
    _only(_record_check(tmp_path, rows), "AC-0013")


def _removal(authority: str) -> list[dict[str, str]]:
    return _with(_base_rows(), _REMOVAL, Authority=authority)


def test_ac0014_link_to_draft_rfc(tmp_path: Path) -> None:
    draft = _RFC_ACCEPTED.replace("Accepted (2026-01-01)", "Draft")
    found = _record_check(tmp_path, extra_files={_RFC_PATH: draft})
    _only(found, "AC-0014")


def test_ac0014_two_links(tmp_path: Path) -> None:
    both = f"{_REMOVAL_LINK} {_REMOVAL_LINK}"
    _only(_record_check(tmp_path, _removal(both)), "AC-0014")


def test_ac0014_no_link(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _removal("see the RFC")), "AC-0014")


def test_ac0014_link_outside_rfc_and_adr(tmp_path: Path) -> None:
    files = {"docs/notes/n.md": _RFC_ACCEPTED}
    rows = _removal("[n](../../notes/n.md#errata)")
    _only(_record_check(tmp_path, rows, extra_files=files), "AC-0014")


def test_ac0014_link_that_escapes_the_repository(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _removal("[x](../../../../../etc/hosts#errata)")), "AC-0014")


def test_ac0014_missing_target(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _removal("[x](../../rfc/9999-none.md#errata)")), "AC-0014")


def test_ac0014_adr_target_passes(tmp_path: Path) -> None:
    files = {"docs/adr/0001-x.md": _RFC_ACCEPTED}
    rows = _removal("[a](../../adr/0001-x.md#errata)")
    assert _record_check(tmp_path, rows, extra_files=files) == []


def test_ac0015_section_does_not_name_the_fact(tmp_path: Path) -> None:
    rows = _removal("[RFC 1](../../rfc/0001-fixture.md#other)")
    _only(_record_check(tmp_path, rows), "AC-0015")


def test_ac0015_anchor_without_a_heading(tmp_path: Path) -> None:
    rows = _removal("[RFC 1](../../rfc/0001-fixture.md#missing)")
    _only(_record_check(tmp_path, rows), "AC-0015")


def test_ac0015_link_without_an_anchor(tmp_path: Path) -> None:
    _only(_record_check(tmp_path, _removal("[RFC 1](../../rfc/0001-fixture.md)")), "AC-0015")


def test_ac0015_underscore_heading_keeps_the_underscore(tmp_path: Path) -> None:
    good = _removal("[RFC 1](../../rfc/0001-fixture.md#where-next_queue-lives)")
    assert _record_check(tmp_path, good) == []
    bad = _removal("[RFC 1](../../rfc/0001-fixture.md#where-next-queue-lives)")
    _only(_record_check(tmp_path / "again", bad), "AC-0015")


def test_ac0015_section_includes_subsections_and_stops_at_same_level(tmp_path: Path) -> None:
    rfc = _RFC_ACCEPTED.replace("nested text", "nested `behavior outside tracked files`")
    rfc = rfc.replace("Section about `behavior outside tracked files` here.", "no mention")
    rows = _removal("[RFC 1](../../rfc/0001-fixture.md#where-next_queue-lives)")
    assert _record_check(tmp_path, rows, extra_files={_RFC_PATH: rfc}) == []
    stops = rfc.replace("nested `behavior outside tracked files`", "none").replace(
        "unrelated", "behavior outside tracked files"
    )
    _only(_record_check(tmp_path / "b", rows, extra_files={_RFC_PATH: stops}), "AC-0015")


def test_ac0016_prose_home(tmp_path: Path) -> None:
    rows = _with(_base_rows(), _COVERAGE_FACT, Home="the brief lint reads it")
    _only(_record_check(tmp_path, rows), "AC-0016")


def test_ac0016_tracked_path_home(tmp_path: Path) -> None:
    rows = _with(_base_rows(), _COVERAGE_FACT, Home="`workspace.toml` and prose")
    assert _record_check(tmp_path, rows) == []


def test_ac0016_untracked_path_home(tmp_path: Path) -> None:
    rows = _with(_base_rows(), _COVERAGE_FACT, Home="`tools/missing.py`")
    _only(_record_check(tmp_path, rows), "AC-0016")


def test_ac0016_nothing_in_backticks_passes(tmp_path: Path) -> None:
    rows = _with(_base_rows(), _COVERAGE_FACT, Home="`nothing`")
    assert _record_check(tmp_path, rows) == []


# ---------------------------------------------------------------------------
# AC-0017: the check runs on every pull request, unconditionally.
# ---------------------------------------------------------------------------

_WORKFLOW = _REPO / ".github/workflows/build-check.yml"
_STEP_RUN = "python -m pytest tests/roster/test_workspace_retirement_inventory.py"
_ROSTER_IF = "!cancelled() && steps.python.conclusion == 'success'"


def _indent(line: str) -> int:
    """Return the count of leading spaces on ``line``."""
    return len(line) - len(line.lstrip(" "))


def workflow_wiring_violations(text: str) -> list[str]:
    """Return every AC-0017 problem in a workflow's text, read line by line.

    PyYAML is not a standard-library module, so the check reads the block
    structure from indentation: the ``on:`` block, the job holding the step,
    and the step's own keys.
    """
    lines = text.splitlines()
    problems: list[str] = []
    on_at = next((n for n, line in enumerate(lines) if line.rstrip() in ("on:", '"on":')), None)
    if on_at is None:
        return ["workflow has no top-level `on:` block"]
    on_block = []
    for line in lines[on_at + 1 :]:
        if line.strip() and _indent(line) == 0:
            break
        on_block.append(line)
    if not any(line.strip() == "pull_request:" for line in on_block):
        problems.append("workflow does not trigger on pull_request")
    if any(line.strip().startswith(("paths:", "paths-ignore:")) for line in on_block):
        problems.append("workflow trigger carries a paths or paths-ignore filter")

    run_at = [n for n, line in enumerate(lines) if line.strip() == f"run: {_STEP_RUN}"]
    if len(run_at) != 1:
        return problems + [f"expected one step running `{_STEP_RUN}`, found {len(run_at)}"]
    run = run_at[0]
    step_start = next(n for n in range(run, -1, -1) if lines[n].lstrip().startswith("- "))
    step_indent = _indent(lines[step_start]) + 2
    step_end = next(
        (
            n
            for n in range(run + 1, len(lines))
            if lines[n].strip() and _indent(lines[n]) < step_indent
        ),
        len(lines),
    )
    step = [lines[step_start][: step_indent - 2] + "  " + lines[step_start].lstrip()[2:]]
    step += lines[step_start + 1 : step_end]
    keys = {
        line.strip().split(":", 1)[0]: line.strip().split(":", 1)[1].strip().strip('"')
        for line in step
        if _indent(line) == step_indent and ":" in line
    }
    if "continue-on-error" in keys:
        problems.append("the step carries continue-on-error")
    if "if" in keys and keys["if"] != _ROSTER_IF:
        problems.append(f"the step's if: is {keys['if']!r}, not the roster condition")

    job_start = next(
        n
        for n in range(step_start, -1, -1)
        if _indent(lines[n]) == 2 and lines[n].rstrip().endswith(":")
    )
    job_end = next(
        (
            n
            for n in range(step_start, len(lines))
            if lines[n].strip() and _indent(lines[n]) <= 2 and n > job_start
        ),
        len(lines),
    )
    for line in lines[job_start + 1 : job_end]:
        if _indent(line) == 4 and line.strip().startswith("continue-on-error:"):
            problems.append("the step's job carries continue-on-error")
        if _indent(line) == 4 and line.strip().startswith("if:"):
            problems.append("the step's job carries an if:")
    return problems


def test_ac0017_real_workflow_runs_the_check_on_every_pull_request() -> None:
    assert workflow_wiring_violations(_WORKFLOW.read_text(encoding="utf-8")) == []


_GOOD_WORKFLOW = f"""on:
  pull_request:
    branches: [main]
jobs:
  gate-main:
    runs-on: ubuntu-latest
    steps:
      - name: other
        run: echo hi
      - name: pytest workspace retirement inventory (roster-owned)
        if: "{_ROSTER_IF}"
        run: {_STEP_RUN}
"""


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        (("  pull_request:\n", "  push:\n"), "pull_request"),
        (("    branches: [main]\n", "    paths: [docs/**]\n"), "paths"),
        (("    runs-on:", "    if: false\n    runs-on:"), "job carries an if"),
        (("        run: echo hi\n", "        run: echo hi\n    if: false\n"), "job carries an if"),
        (
            (f"run: {_STEP_RUN}\n", f"run: {_STEP_RUN}\n    continue-on-error: true\n"),
            "job carries continue-on-error",
        ),
        ((f'if: "{_ROSTER_IF}"', "if: false"), "not the roster condition"),
        (
            (f"run: {_STEP_RUN}\n", f"run: {_STEP_RUN}\n        continue-on-error: true\n"),
            "continue-on-error",
        ),
        ((f"run: {_STEP_RUN}\n", "run: true\n"), "expected one step"),
    ],
)
def test_ac0017_wiring_rules(change: tuple[str, str], problem: str) -> None:
    assert workflow_wiring_violations(_GOOD_WORKFLOW) == []
    broken = _GOOD_WORKFLOW.replace(*change)
    found = workflow_wiring_violations(broken)
    assert len(found) == 1 and problem in found[0], found


def test_ac0017_quoted_on_key_is_read() -> None:
    assert workflow_wiring_violations(_GOOD_WORKFLOW.replace("on:\n", '"on":\n', 1)) == []
    assert workflow_wiring_violations("jobs: {}\n") == ["workflow has no top-level `on:` block"]
