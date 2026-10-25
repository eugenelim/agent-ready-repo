#!/usr/bin/env python3
"""Inventory rules for the workspace retirement record (spec workspace-retirement).

``check_repository`` applies the spec's inventory rules (AC-0001 to AC-0009,
AC-0019, AC-0021) to a repository root and returns every violation tagged with
its criterion. The record rules (AC-0010 to AC-0016) belong to task T2 and
plug in at ``check_record``. Standard library only; the check reads the
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


def check_record(root: Path, record: Path) -> list[Violation]:
    """Seam for task T2: the record rules AC-0010 to AC-0016. Not implemented here."""
    return []


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
    """Build a tiny git repo, write inventory and brief outside it, run the check."""
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
    return check_repository(root, inventory, tmp_path / "retirement-record.md", brief)


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
    found = check_repository(root, tmp_path / "nope.toml", tmp_path / "rec.md", brief)
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
    again = check_repository(
        tmp_path / "repo", tmp_path / "inventory.toml", tmp_path / "r.md", tmp_path / "brief.md"
    )
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
    not DEFAULT_INVENTORY.exists(),
    reason="expected to fail until T3 creates docs/specs/workspace-retirement/inventory.toml",
)
def test_real_repository_passes_every_rule() -> None:
    """AC-0018 / AC-0022: the same check on this checkout, no arguments."""
    found = check_repository()
    assert found == [], "\n".join(str(v) for v in found)
