"""Roster check: operative text is off the workspace registry (registry-upgrade-notes).

The operative-set checks (AC-0008, AC-0009, AC-0019) loop over the registered
surface groups. A self-test plants one file per rule under ``tmp_path`` so each
check is proven to fire.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

UPGRADE_PAGE = "guides/core/how-to/upgrade-from-a-workspace-registry.md"
REPAIR_SKILL = "packs/core/.apm/skills/workspace-status/"
DRAFT_NOTES = "docs/specs/pre-cutover-closure/notes/upgrade-notes.md"
DRAFT_SHA256 = "417412d4adb63ce114802cc8beffa82f1ae303b8a4d4c0dd9971e03fc8500a58"
THIS_TEST = "tests/roster/test_registry_upgrade_notes.py"

# name -> glob patterns. Later tasks append groups; the operative set is their union.
SURFACE_GROUPS: dict[str, list[str]] = {
    "core-pack": [
        "packs/core/README.md",
        "packs/core/DESIGN.md",
        "packs/core/JOURNEY.md",
        "packs/core/docs/**",
        "packs/core/seeds/**",
        "packs/core/.apm/**/*.md",
        "packs/core/.apm/**/*.json",
    ],
    "repo-governance-manifest": ["packs/repo-governance/pack.toml"],
    "_example": [
        "packs/_example/README.md",
        "packs/_example/DESIGN.md",
        "packs/_example/JOURNEY.md",
        "packs/_example/docs/**",
        "packs/_example/seeds/**",
        "packs/_example/.apm/**/*.md",
        "packs/_example/.apm/**/*.json",
    ],
    "_okf-pilot-cost-engineering": [
        "packs/_okf-pilot-cost-engineering/README.md",
        "packs/_okf-pilot-cost-engineering/DESIGN.md",
        "packs/_okf-pilot-cost-engineering/JOURNEY.md",
        "packs/_okf-pilot-cost-engineering/docs/**",
        "packs/_okf-pilot-cost-engineering/seeds/**",
        "packs/_okf-pilot-cost-engineering/.apm/**/*.md",
        "packs/_okf-pilot-cost-engineering/.apm/**/*.json",
    ],
    "agent-skill-engineering": [
        "packs/agent-skill-engineering/README.md",
        "packs/agent-skill-engineering/DESIGN.md",
        "packs/agent-skill-engineering/JOURNEY.md",
        "packs/agent-skill-engineering/docs/**",
        "packs/agent-skill-engineering/seeds/**",
        "packs/agent-skill-engineering/.apm/**/*.md",
        "packs/agent-skill-engineering/.apm/**/*.json",
    ],
    "architect": [
        "packs/architect/README.md",
        "packs/architect/DESIGN.md",
        "packs/architect/JOURNEY.md",
        "packs/architect/docs/**",
        "packs/architect/seeds/**",
        "packs/architect/.apm/**/*.md",
        "packs/architect/.apm/**/*.json",
    ],
    "atlassian": [
        "packs/atlassian/README.md",
        "packs/atlassian/DESIGN.md",
        "packs/atlassian/JOURNEY.md",
        "packs/atlassian/docs/**",
        "packs/atlassian/seeds/**",
        "packs/atlassian/.apm/**/*.md",
        "packs/atlassian/.apm/**/*.json",
    ],
    "catalogue-curation": [
        "packs/catalogue-curation/README.md",
        "packs/catalogue-curation/DESIGN.md",
        "packs/catalogue-curation/JOURNEY.md",
        "packs/catalogue-curation/docs/**",
        "packs/catalogue-curation/seeds/**",
        "packs/catalogue-curation/.apm/**/*.md",
        "packs/catalogue-curation/.apm/**/*.json",
    ],
    "code-intelligence": [
        "packs/code-intelligence/README.md",
        "packs/code-intelligence/DESIGN.md",
        "packs/code-intelligence/JOURNEY.md",
        "packs/code-intelligence/docs/**",
        "packs/code-intelligence/seeds/**",
        "packs/code-intelligence/.apm/**/*.md",
        "packs/code-intelligence/.apm/**/*.json",
    ],
    "contracts": [
        "packs/contracts/README.md",
        "packs/contracts/DESIGN.md",
        "packs/contracts/JOURNEY.md",
        "packs/contracts/docs/**",
        "packs/contracts/seeds/**",
        "packs/contracts/.apm/**/*.md",
        "packs/contracts/.apm/**/*.json",
    ],
    "converters": [
        "packs/converters/README.md",
        "packs/converters/DESIGN.md",
        "packs/converters/JOURNEY.md",
        "packs/converters/docs/**",
        "packs/converters/seeds/**",
        "packs/converters/.apm/**/*.md",
        "packs/converters/.apm/**/*.json",
    ],
    "credential-brokers": [
        "packs/credential-brokers/README.md",
        "packs/credential-brokers/DESIGN.md",
        "packs/credential-brokers/JOURNEY.md",
        "packs/credential-brokers/docs/**",
        "packs/credential-brokers/seeds/**",
        "packs/credential-brokers/.apm/**/*.md",
        "packs/credential-brokers/.apm/**/*.json",
    ],
    "desk-research": [
        "packs/desk-research/README.md",
        "packs/desk-research/DESIGN.md",
        "packs/desk-research/JOURNEY.md",
        "packs/desk-research/docs/**",
        "packs/desk-research/seeds/**",
        "packs/desk-research/.apm/**/*.md",
        "packs/desk-research/.apm/**/*.json",
    ],
    "experience-design": [
        "packs/experience-design/README.md",
        "packs/experience-design/DESIGN.md",
        "packs/experience-design/JOURNEY.md",
        "packs/experience-design/docs/**",
        "packs/experience-design/seeds/**",
        "packs/experience-design/.apm/**/*.md",
        "packs/experience-design/.apm/**/*.json",
    ],
    "figma": [
        "packs/figma/README.md",
        "packs/figma/DESIGN.md",
        "packs/figma/JOURNEY.md",
        "packs/figma/docs/**",
        "packs/figma/seeds/**",
        "packs/figma/.apm/**/*.md",
        "packs/figma/.apm/**/*.json",
    ],
    "frontend-engineering": [
        "packs/frontend-engineering/README.md",
        "packs/frontend-engineering/DESIGN.md",
        "packs/frontend-engineering/JOURNEY.md",
        "packs/frontend-engineering/docs/**",
        "packs/frontend-engineering/seeds/**",
        "packs/frontend-engineering/.apm/**/*.md",
        "packs/frontend-engineering/.apm/**/*.json",
    ],
    "github": [
        "packs/github/README.md",
        "packs/github/DESIGN.md",
        "packs/github/JOURNEY.md",
        "packs/github/docs/**",
        "packs/github/seeds/**",
        "packs/github/.apm/**/*.md",
        "packs/github/.apm/**/*.json",
    ],
    "iac-terraform": [
        "packs/iac-terraform/README.md",
        "packs/iac-terraform/DESIGN.md",
        "packs/iac-terraform/JOURNEY.md",
        "packs/iac-terraform/docs/**",
        "packs/iac-terraform/seeds/**",
        "packs/iac-terraform/.apm/**/*.md",
        "packs/iac-terraform/.apm/**/*.json",
    ],
    "linear": [
        "packs/linear/README.md",
        "packs/linear/DESIGN.md",
        "packs/linear/JOURNEY.md",
        "packs/linear/docs/**",
        "packs/linear/seeds/**",
        "packs/linear/.apm/**/*.md",
        "packs/linear/.apm/**/*.json",
    ],
    "monorepo-extras": [
        "packs/monorepo-extras/README.md",
        "packs/monorepo-extras/DESIGN.md",
        "packs/monorepo-extras/JOURNEY.md",
        "packs/monorepo-extras/docs/**",
        "packs/monorepo-extras/seeds/**",
        "packs/monorepo-extras/.apm/**/*.md",
        "packs/monorepo-extras/.apm/**/*.json",
    ],
    "product-documentation": [
        "packs/product-documentation/README.md",
        "packs/product-documentation/DESIGN.md",
        "packs/product-documentation/JOURNEY.md",
        "packs/product-documentation/docs/**",
        "packs/product-documentation/seeds/**",
        "packs/product-documentation/.apm/**/*.md",
        "packs/product-documentation/.apm/**/*.json",
    ],
    "product-engineering": [
        "packs/product-engineering/README.md",
        "packs/product-engineering/DESIGN.md",
        "packs/product-engineering/JOURNEY.md",
        "packs/product-engineering/docs/**",
        "packs/product-engineering/seeds/**",
        "packs/product-engineering/.apm/**/*.md",
        "packs/product-engineering/.apm/**/*.json",
    ],
    "product-strategy": [
        "packs/product-strategy/README.md",
        "packs/product-strategy/DESIGN.md",
        "packs/product-strategy/JOURNEY.md",
        "packs/product-strategy/docs/**",
        "packs/product-strategy/seeds/**",
        "packs/product-strategy/.apm/**/*.md",
        "packs/product-strategy/.apm/**/*.json",
    ],
    "release-engineering": [
        "packs/release-engineering/README.md",
        "packs/release-engineering/DESIGN.md",
        "packs/release-engineering/JOURNEY.md",
        "packs/release-engineering/docs/**",
        "packs/release-engineering/seeds/**",
        "packs/release-engineering/.apm/**/*.md",
        "packs/release-engineering/.apm/**/*.json",
    ],
    "repo-governance": [
        "packs/repo-governance/README.md",
        "packs/repo-governance/DESIGN.md",
        "packs/repo-governance/JOURNEY.md",
        "packs/repo-governance/docs/**",
        "packs/repo-governance/seeds/**",
        "packs/repo-governance/.apm/**/*.md",
        "packs/repo-governance/.apm/**/*.json",
    ],
    "user-guide-diataxis": [
        "packs/user-guide-diataxis/README.md",
        "packs/user-guide-diataxis/DESIGN.md",
        "packs/user-guide-diataxis/JOURNEY.md",
        "packs/user-guide-diataxis/docs/**",
        "packs/user-guide-diataxis/seeds/**",
        "packs/user-guide-diataxis/.apm/**/*.md",
        "packs/user-guide-diataxis/.apm/**/*.json",
    ],
    "pack-pages": ["web/src/content/packs/**"],
    "core-guides": ["guides/README.md", "guides/core/**/*.md"],
    "other-guides": ["guides/**/*.md"],
    "docs": [
        "docs/architecture/**/*.md",
        "docs/guides/**",
        "docs/product/journeys/**",
        "docs/product/README.md",
        "docs/product/workspace-toml-deps.md",
        "docs/product/initiatives/_template.md",
        "docs/backlog.md",
        "docs/specs/README.md",
    ],
    "root": [
        "ARCHITECTURE.md",
        "CONTRIBUTING.md",
        "llms.txt",
        "packages/agentbundle/README.md",
        ".github/dependabot.yml",
    ],
}

RETIRED_COMMAND_TOKENS = (
    "workspace-status status",
    "workspace-status reconcile",
    "workspace-status explain",
    "selected-membership",
    "retirement-candidates",
    "repair-rollback",
    "--migration-selection",
    "prune --select",
    "[authorization.migration]",
    ".workspace-migrations.json",
    "workspace.toml transition",
    "rerun reconciliation",
)
REGISTRY_MODEL_TOKENS = (
    "shaping_queue",
    "[work].queue",
    "brief_queue",
    "workspace entry",
    "workspace membership",
)
DELETED_GUIDES = (
    "guides/core/how-to/migrate-capture-work.md",
    "guides/core/reference/workspace-toml-schema.md",
)
DISPATCH_PAGES = (
    "guides/core/how-to/orient-at-session-start.md",
    "guides/core/explanation/two-room-model.md",
    "guides/core/tutorials/your-first-workspace.md",
    "packs/core/JOURNEY.md",
)
RECORDS_PREFIXES = (
    "docs/specs/",
    "docs/rfc/",
    "docs/adr/",
    "docs/lifecycle/",
    "docs/knowledge/",
    "docs/design/",
    "docs/product/intents/",
    "docs/product/briefs/",
    "docs/product/captured/",
    "docs/product/research/",
    "docs/product/findings/",
    "docs/product/shaping/",
    "docs/product/design/",
    "docs/product/changelog.d/",
    "docs/product/initiatives/ini-",
)
RECORDS_FILES = ("docs/specs/README.md",)  # carved out of the docs/specs/ prefix
RECORDS_EXACT = ("docs/product/roadmap.md", "docs/product/changelog.md")


# ---- text helpers -------------------------------------------------------------


def normalize(text: str) -> str:
    """Collapse each run of whitespace to one space."""
    return " ".join(text.split())


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a repository glob (`**` crosses directories, `*` does not)."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z")


def words(text: str) -> set[str]:
    """Lowercase words; a word ending `n't` also counts as `not`."""
    found = set(re.findall(r"[a-z0-9]+(?:['’][a-z]+)*", text.lower()))
    for w in list(found):
        if w.replace("’", "'").endswith("n't"):
            found.add("not")
    return found


def has_word(unit: str, *wanted: str) -> bool:
    """Word match: whole word; `delet` and `regist` match as prefixes."""
    ws = words(unit)
    for want in wanted:
        if want in ("delet", "regist"):
            if any(w.startswith(want) for w in ws):
                return True
        elif want in ws:
            return True
    return False


_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
_FENCE = re.compile(r"^\s*(```|~~~)")


def markdown_units(text: str) -> list[tuple[str, str]]:
    """Mention units of a Markdown file as (kind, text); headings are skipped.

    kind is `frontmatter`, `fence`, `table`, `list` or `paragraph`.
    """
    lines = text.splitlines()
    units: list[tuple[str, str]] = []
    i = 0
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            units.append(("frontmatter", lines[j]))
            j += 1
        if j < len(lines):
            i = j + 1
        else:  # unterminated: not frontmatter
            units.clear()
    block: list[str] = []
    block_kind = ""

    def flush() -> None:
        nonlocal block, block_kind
        if block:
            units.append((block_kind, "\n".join(block)))
        block, block_kind = [], ""

    in_fence = False
    while i < len(lines):
        line = lines[i]
        i += 1
        if _FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            units.append(("fence", line))
            continue
        if (
            not line.strip()
            or line.lstrip().startswith("#")
            and re.match(r"^\s{0,3}#{1,6}(\s|$)", line)
        ):
            flush()
        elif line.lstrip().startswith("|"):
            flush()
            units.append(("table", line))
        elif _LIST_ITEM.match(line):
            flush()
            block, block_kind = [line], "list"
        elif block:  # continuation of a list item or paragraph
            block.append(line)
        else:
            block, block_kind = [line], "paragraph"
    flush()
    return units


def json_strings(value: object) -> list[str]:
    """Every string value of a JSON document, recursively."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for v in value for s in json_strings(v)]
    if isinstance(value, dict):
        return [s for v in value.values() for s in json_strings(v)]
    return []


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def units_of(rel: str, text: str) -> list[tuple[str, str]]:
    """Mention units of any file as (kind, text)."""
    if rel.endswith(".md"):
        return markdown_units(text)
    if rel.endswith(".json"):
        try:
            return [("json", s) for s in json_strings(json.loads(text))]
        except ValueError:
            pass
    return [("line", line) for line in text.splitlines()]


def normalized_parts(rel: str, text: str) -> list[str]:
    """Normalized text: one entry per JSON string value, else the whole file."""
    if rel.endswith(".json"):
        try:
            return [normalize(s) for s in json_strings(json.loads(text))]
        except ValueError:
            pass
    return [normalize(text)]


# ---- file selection -----------------------------------------------------------


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True, text=True
    ).stdout
    return [p for p in out.split("\0") if p]


def operative_files(root: Path, files: list[str], groups: dict[str, list[str]]) -> list[str]:
    patterns = [glob_to_regex(p) for globs in groups.values() for p in globs]
    return sorted(
        f
        for f in files
        if f != UPGRADE_PAGE and any(p.match(f) for p in patterns) and (root / f).is_file()
    )


def in_records(rel: str) -> bool:
    if rel in RECORDS_FILES:
        return False
    return (
        rel.startswith(RECORDS_PREFIXES)
        or rel in RECORDS_EXACT
        or rel.rsplit("/", 1)[-1].startswith("CHANGELOG")
    )


# ---- checks (each returns violation strings) ----------------------------------


def check_ac0008(root: Path, files: list[str]) -> list[str]:
    bad: list[str] = []
    for rel in files:
        in_repair = rel.startswith(REPAIR_SKILL)
        tokens = RETIRED_COMMAND_TOKENS + (() if in_repair else REGISTRY_MODEL_TOKENS)
        for part in normalized_parts(rel, read_text(root / rel)):
            bad += [f"{rel}: {t}" for t in tokens if t in part]
    return sorted(set(bad))


def check_ac0009(root: Path, files: list[str]) -> list[str]:
    bad: list[str] = []
    for rel in files:
        if rel.startswith(REPAIR_SKILL + "evals/"):
            continue
        for kind, unit in units_of(rel, read_text(root / rel)):
            if "workspace-status" not in unit or "repair" in unit:
                continue
            if kind == "json" and not any(c.isspace() for c in unit):
                continue
            if kind == "frontmatter" and re.match(r"\s*(?:-\s+)?name\s*:", unit):
                continue
            bad.append(f"{rel}: {normalize(unit)[:80]}")
    return bad


def check_ac0019(root: Path, files: list[str]) -> list[str]:
    bad: list[str] = []
    for rel in files:
        for _, unit in units_of(rel, read_text(root / rel)):
            if "workspace.toml" not in unit or not has_word(unit, "regist"):
                continue
            if "repair" in unit or has_word(
                unit, "no", "not", "never", "nothing", "none", "without"
            ):
                continue
            bad.append(f"{rel}: {normalize(unit)[:80]}")
    return bad


def check_ac0003_deletion(text: str) -> list[str]:
    """AC-0003's second sentence, over one Markdown file's mention units."""
    return [
        normalize(u)[:80]
        for _, u in markdown_units(text)
        if "workspace.toml" in u
        and has_word(u, "delet")
        and not has_word(u, "no", "not", "never", "keep")
    ]


def check_ac0010_stale_refs(root: Path, files: list[str]) -> list[str]:
    bad = [f"exists: {p}" for p in DELETED_GUIDES if (root / p).exists()]
    for rel in files:
        if in_records(rel) or rel == THIS_TEST or not (root / rel).is_file():
            continue
        text = read_text(root / rel)
        bad += [
            f"{rel}: {n}"
            for n in ("migrate-capture-work.md", "workspace-toml-schema.md")
            if n in text
        ]
    return bad


_LINK = re.compile(r"\]\(([^)\s]+)\)")


def check_ac0010_links(root: Path, pages: list[str], files: list[str]) -> list[str]:
    """Each relative Markdown link resolves to a tracked file or a directory holding one."""
    tracked = set(files)
    bad: list[str] = []
    for rel in pages:
        for target in _LINK.findall(read_text(root / rel)):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^#|^/", target):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            resolved = (Path(rel).parent / path).as_posix()
            parts: list[str] = []
            for seg in resolved.split("/"):
                if seg == "..":
                    if parts:
                        parts.pop()
                elif seg not in ("", "."):
                    parts.append(seg)
            norm = "/".join(parts)
            if norm not in tracked and not any(f.startswith(norm + "/") for f in tracked):
                bad.append(f"{rel}: {target}")
    return bad


def check_ac0011(root: Path) -> list[str]:
    bad = [p for p in DISPATCH_PAGES if "dispatch.py" not in read_text(root / p)]
    journeys = "web/src/content/journeys"

    def state() -> dict[str, str]:
        """Path -> SHA-256 of each journey page git tracks or would track.

        Tracked pages and untracked pages git does not ignore are both listed,
        so a build that adds a page is a change; ignored generated pages (a pack
        whose journey is not published) stay out, so a fresh checkout that first
        creates them still compares equal.
        """
        listed: set[str] = set()
        for extra in ([], ["--others", "--exclude-standard"]):
            out = subprocess.run(
                ["git", "ls-files", "-z", *extra, "--", journeys],
                cwd=root,
                capture_output=True,
                check=True,
            ).stdout.decode("utf-8")
            listed.update(filter(None, out.split("\0")))
        return {
            rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
            if (root / rel).is_file()
            else "absent"
            for rel in sorted(listed)
        }

    before = state()
    subprocess.run(
        [sys.executable, "tools/build-site.py", "--journeys-only"], cwd=root, check=True
    )
    if state() != before:
        bad.append(f"{journeys} changed by build-site --journeys-only")
    return bad


def check_ac0004(root: Path) -> list[str]:
    digest = hashlib.sha256((root / DRAFT_NOTES).read_bytes()).hexdigest()
    return [] if digest == DRAFT_SHA256 else [f"{DRAFT_NOTES}: {digest}"]


# ---- the real repository ------------------------------------------------------


def test_ac0004_draft_unchanged() -> None:
    assert check_ac0004(REPO_ROOT) == []


def test_operative_set_ac0008_ac0009_ac0019() -> None:
    files = operative_files(REPO_ROOT, tracked_files(REPO_ROOT), SURFACE_GROUPS)
    assert check_ac0008(REPO_ROOT, files) == []
    assert check_ac0009(REPO_ROOT, files) == []
    assert check_ac0019(REPO_ROOT, files) == []


def test_ac0006_core_first_value_names_dispatch() -> None:
    manifest = tomllib.loads(read_text(REPO_ROOT / "packs/core/pack.toml"))
    first_value = manifest["pack"]["first-value"]
    for key in ("verification", "recovery"):
        assert "dispatch.py" in first_value[key], key
        assert "workspace-status" not in first_value[key], key
    readme = normalize(read_text(REPO_ROOT / "packs/core/README.md"))
    assert normalize(first_value["verification"]) in readme


def test_ac0007_repo_governance_manifest_has_no_workspace_status() -> None:
    assert "workspace-status" not in read_text(REPO_ROOT / "packs/repo-governance/pack.toml")


def test_ac0011_core_journey_names_dispatch() -> None:
    assert "dispatch.py" in read_text(REPO_ROOT / "packs/core/JOURNEY.md")


def test_ac0010_no_stale_references_or_dangling_links() -> None:
    files = tracked_files(REPO_ROOT)
    assert check_ac0010_stale_refs(REPO_ROOT, files) == []
    pages = [UPGRADE_PAGE, *(p for p in DISPATCH_PAGES if p.startswith("guides/"))]
    assert check_ac0010_links(REPO_ROOT, pages, files) == []


def test_ac0011_dispatch_pages_and_journey_build() -> None:
    assert check_ac0011(REPO_ROOT) == []


# ---- self-test: each rule fires on a planted file -----------------------------


def _plant(root: Path, rel: str, text: str) -> list[str]:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return [rel]


def test_self_retired_token(tmp_path: Path) -> None:
    files = _plant(tmp_path, "a.md", "Run `workspace-status   status` now.\n")
    assert check_ac0008(tmp_path, files)
    files = _plant(tmp_path, "b.md", "Use `repair-plan`.\n")
    assert check_ac0008(tmp_path, files) == []


def test_self_registry_token_outside_repair_skill(tmp_path: Path) -> None:
    text = "The shaping_queue key.\n"
    assert check_ac0008(tmp_path, _plant(tmp_path, "a.md", text))
    assert check_ac0008(tmp_path, _plant(tmp_path, REPAIR_SKILL + "SKILL.md", text)) == []


def test_self_workspace_status_list_items(tmp_path: Path) -> None:
    text = "- Run workspace-status to see things\n  and more\n- Run workspace-status repair-plan\n"
    bad = check_ac0009(tmp_path, _plant(tmp_path, "a.md", text))
    assert len(bad) == 1 and "to see things" in bad[0]


def test_self_ac0009_sentence_fence_json_frontmatter(tmp_path: Path) -> None:
    ok = _plant(tmp_path, "ok.md", "Use workspace-status repair-plan here.\n")
    assert check_ac0009(tmp_path, ok) == []
    fenced = _plant(tmp_path, "f.md", "```mermaid\nA --> workspace-status\n```\n")
    assert len(check_ac0009(tmp_path, fenced)) == 1
    js = _plant(
        tmp_path, "a.json", json.dumps({"k": "workspace-status", "m": ["workspace-status"]})
    )
    assert check_ac0009(tmp_path, js) == []
    js_bad = _plant(tmp_path, "b.json", json.dumps({"k": "call workspace-status now"}))
    assert len(check_ac0009(tmp_path, js_bad)) == 1
    fm = _plant(
        tmp_path,
        "fm.md",
        "---\nname: workspace-status\ndescription: workspace-status\n---\n# workspace-status\n",
    )
    assert len(check_ac0009(tmp_path, fm)) == 1  # only the description line; name and heading pass
    eval_file = _plant(tmp_path, REPAIR_SKILL + "evals/e.md", "workspace-status alone\n")
    assert check_ac0009(tmp_path, eval_file) == []


def test_self_registration_sentence(tmp_path: Path) -> None:
    bad = _plant(tmp_path, "a.md", "Registration of `workspace.toml` is required.\n")
    assert check_ac0019(tmp_path, bad)
    for sentence in (
        "There is no registration in `workspace.toml`.\n",
        "Registration in `workspace.toml` is handled by repair.\n",
        "Registry rows in `workspace.toml` don't matter.\n",
    ):
        assert check_ac0019(tmp_path, _plant(tmp_path, "b.md", sentence)) == []


def test_self_dangling_link(tmp_path: Path) -> None:
    pages = _plant(
        tmp_path, "guides/a.md", "See [x](b.md#frag) and [y](missing.md) and [z](https://e.com).\n"
    )
    _plant(tmp_path, "guides/b.md", "b\n")
    bad = check_ac0010_links(tmp_path, pages, ["guides/a.md", "guides/b.md"])
    assert bad == ["guides/a.md: missing.md"]


def test_self_ac0003_deletion_proxy() -> None:
    assert check_ac0003_deletion("Don't delete `workspace.toml`.\n") == []
    assert check_ac0003_deletion("Delete `workspace.toml`.\n")
    assert check_ac0003_deletion("Keep it; deleting `workspace.toml` is not needed.\n") == []


def test_self_markdown_units() -> None:
    text = "---\nname: x\n---\n# Heading workspace-status\n\n| a | b |\n\npara one\nline two\n"
    kinds = [k for k, _ in markdown_units(text)]
    assert kinds == ["frontmatter", "table", "paragraph"]


# --- Upgrade page (AC-0001, AC-0002, AC-0003) -------------------------------

_AC0002_TOKENS = (
    "repair-plan",
    "repair-apply --yes",
    "needs-to-header",
    "captured-entry-drop",
    "refresh-policy-move",
    ".work-intake.toml",
    "[authorization.refresh]",
    "unmigrated_workspace",
    "dispatch.py",
    "status",
    "reconcile",
    "explain",
    "selected-membership",
    "prune",
    "retirement-candidates",
    "repair-rollback",
    "[authorization.migration]",
    ".workspace-migrations.json",
    "workspace_status()",
    "ini_slug",
    "shaping",
    "WORKSPACE_MCP_DISPATCHED_ITEM",
    # The behaviors the pre-cutover-closure draft lists as not carried over.
    "<initiative>",
    "<initiative>.name",
    "<initiative>.status",
    "<initiative>.milestone",
    "<initiative>.parent",
    "entry position",
    "behavior outside tracked files",
    "origin_mode",
    "profile",
    "refresh",
)


def _page() -> str:
    return read_text(REPO_ROOT / UPGRADE_PAGE)


def _run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_ac0001_frontmatter_title_and_lints() -> None:
    text = _page()
    front = text.split("---", 2)[1]
    fields = dict(line.split(":", 1) for line in front.strip().splitlines() if ":" in line)
    assert fields["pack"].strip() == "core"
    assert fields["kind"].strip() == "how-to"
    h1 = next(line for line in text.splitlines() if line.startswith("# "))
    assert h1[2:].strip() == fields["title"].strip()
    validated = _run_tool("tools/validate_guides.py", UPGRADE_PAGE)
    assert validated.returncode == 0, validated.stdout + validated.stderr
    lint = _run_tool("tools/lint-guides-no-repo-only-refs.py")
    assert lint.returncode == 0, lint.stdout + lint.stderr
    index = read_text(REPO_ROOT / "guides/core/README.md")
    assert "how-to/upgrade-from-a-workspace-registry.md" in index


def test_ac0002_names_each_token_in_backticks() -> None:
    text = normalize(_page())
    missing = [token for token in _AC0002_TOKENS if f"`{token}`" not in text]
    assert missing == []


def test_ac0003_migration_warning_precedes_upgrade_and_no_delete_instruction() -> None:
    text = _page()
    assert text.index(".workspace-migrations.json") < text.index("agentbundle upgrade")
    assert check_ac0003_deletion(text) == []


# --- Seed and its tooling (AC-0005, AC-0023) ---------------------------------


def test_ac0005_fresh_core_install_writes_no_workspace_toml(tmp_path: Path) -> None:
    assert not (REPO_ROOT / "packs/core/seeds/workspace.toml").exists()
    target = tmp_path / "repo"
    target.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    home = tmp_path / "home"
    env = dict(os.environ)
    env.update(
        HOME=str(home),
        AGENTBUNDLE_USER_ROOT=str(home / ".agentbundle"),
        PYTHONIOENCODING="utf-8",
    )
    installed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "install",
            str(REPO_ROOT),
            "--pack",
            "core",
            "--output",
            str(target),
            "--scope",
            "repo",
            "--adapter",
            "claude-code",
            "--yes",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert (target / "AGENTS.md").is_file()
    assert not (target / "workspace.toml").exists()


def test_ac0023_seed_tooling_drops_workspace_toml() -> None:
    sys.path.insert(0, str(REPO_ROOT / "packages/agentbundle"))
    try:
        from agentbundle.build import self_host
        from agentbundle.catalogue_tooling import lint
    finally:
        sys.path.pop(0)
    assert "workspace.toml" not in self_host.EXCLUDED_PATTERNS
    tables = [
        value
        for value in vars(lint).values()
        if isinstance(value, dict) and "AGENTS.md" in value and "docs/specs/README.md" in value
    ]
    assert tables, "seed-placeholder table not found"
    assert all("workspace.toml" not in table for table in tables)


# --- Next actions (AC-0008 code clause, AC-0012, AC-0024) --------------------

_DISPATCH_TABLES = (
    "packs/core/.apm/skills/work-loop/scripts/_header_readiness.py",
    "packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py",
    "packages/agentbundle/agentbundle/_data/_header_readiness.py",
    "packages/agentbundle/agentbundle/workspace_mcp.py",
)
_REPAIR_TABLES = (
    "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py",
    "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py",
    "packs/core/.apm/skills/workspace-status/SKILL.md",
)


def test_ac0008_no_code_file_says_rerun_reconciliation() -> None:
    roots = ("packs/", "packages/agentbundle/agentbundle/")
    bad = [
        rel
        for rel in tracked_files(REPO_ROOT)
        if rel.endswith(".py")
        and rel.startswith(roots)
        and (rel.startswith("packages/") or "/.apm/" in rel)
        and "rerun reconciliation" in normalize(read_text(REPO_ROOT / rel))
    ]
    assert bad == []


_FINDING_TABLE_NAMES = {"_FINDING_NEXT_ACTIONS", "_KNOWN_FINDINGS", "next_actions"}


def _next_actions(rel: str) -> list[str]:
    """Each finding table's next-action values: table rows of a skill, else AST dict values."""
    text = read_text(REPO_ROOT / rel)
    if rel.endswith(".md"):
        return [row.split("|")[-2] for row in text.splitlines() if row.startswith("| `")]
    values: list[str] = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        else:
            continue
        if _FINDING_TABLE_NAMES.intersection(names) and isinstance(node.value, ast.Dict):
            values += [
                v.value
                for v in node.value.values
                if isinstance(v, ast.Constant) and isinstance(v.value, str)
            ]
    return values


def test_ac0012_no_next_action_says_reconciliation() -> None:
    bad = [
        f"{rel}: {action}"
        for rel in _DISPATCH_TABLES + _REPAIR_TABLES
        for action in _next_actions(rel)
        if "reconciliation" in action
    ]
    assert bad == []
    for rel in _DISPATCH_TABLES + _REPAIR_TABLES:
        assert _next_actions(rel), f"{rel}: no finding table found"


def test_ac0024_changed_next_actions_name_their_command() -> None:
    for rel in _DISPATCH_TABLES:
        assert "then run `dispatch.py` again." in read_text(REPO_ROOT / rel), rel
    for rel in _REPAIR_TABLES:
        assert "then run `repair-plan` again." in read_text(REPO_ROOT / rel), rel


# --- Records and release (AC-0013, AC-0014, AC-0015, AC-0017) ----------------

_INVENTORY = "docs/specs/workspace-retirement/inventory.toml"
_RECORD = "docs/specs/workspace-retirement/retirement-record.md"
_BRIEF = "docs/product/briefs/workspace-registry-retirement-delivery.md"
_FRAGMENT = "docs/product/changelog.d/fddd49ef-5bc1-4110-8652-21a38557e3a1.md"
# A later release supersedes a pack's version in this map: its fragment names
# the pack at the new version, and the map points that pack at its fragment.
_RELEASED = {
    "core": ("4.0.15", "docs/product/changelog.d/9b9b670f-c8a1-48ea-b3bb-64819eba374c.md"),
    "repo-governance": ("2.5.2", _FRAGMENT),
    "product-strategy": ("0.2.11", _FRAGMENT),
    "experience-design": ("4.2.2", _FRAGMENT),
    "desk-research": ("1.1.11", _FRAGMENT),
    "atlassian": ("0.10.5", _FRAGMENT),
    "linear": ("0.3.6", _FRAGMENT),
    "github": ("0.3.1", _FRAGMENT),
    "product-engineering": ("2.0.6", _FRAGMENT),
}


def _rows() -> list[dict[str, object]]:
    import tomllib

    return tomllib.loads(read_text(REPO_ROOT / _INVENTORY))["row"]


def test_ac0013_inventory_rows() -> None:
    rows = {row["pattern"]: row for row in _rows()}
    own = rows["docs/specs/registry-upgrade-notes/*"]
    # Once the spec shipped, workspace-toml-deletion moved its row to the history set.
    assert (own["class"], own["owner"]) == ("historical", "none")
    assert UPGRADE_PAGE in rows
    draft = rows[DRAFT_NOTES]
    assert (draft["class"], draft["owner"]) == ("historical", "none")
    for deleted in DELETED_GUIDES:
        assert deleted not in rows
    assert "packs/core/seeds/workspace.toml" not in rows


def test_ac0014_closure_bullet() -> None:
    text = read_text(REPO_ROOT / _RECORD)
    section = text.split("## Compatibility closure", 1)[1].split("\n## ", 1)[0]
    bullets = [b for b in section.split("\n- ") if "../registry-upgrade-notes/spec.md" in b]
    assert len(bullets) == 1
    assert UPGRADE_PAGE in bullets[0]
    assert "seed" in bullets[0] and "rename" in bullets[0]


def test_ac0015_brief_names_the_spec() -> None:
    text = read_text(REPO_ROOT / _BRIEF)
    assert "| `registry-upgrade-notes` |" in text
    assert "operative references (`registry-upgrade-notes`)" in text


def test_ac0017_versions_and_fragment() -> None:
    import tomllib

    for pack, (version, fragment_path) in _RELEASED.items():
        manifest = tomllib.loads(read_text(REPO_ROOT / f"packs/{pack}/pack.toml"))
        plugin = json.loads(read_text(REPO_ROOT / f"packs/{pack}/.claude-plugin/plugin.json"))
        assert manifest["pack"]["version"] == version == plugin["version"], pack
        fragment = read_text(REPO_ROOT / fragment_path)
        assert f'name = "{pack}"\nversion = "{version}"' in fragment, pack
    fragment = read_text(REPO_ROOT / _FRAGMENT)
    assert 'name = "agentbundle"\nversion = "0.60.1"' in fragment
    assert UPGRADE_PAGE in fragment


# --- Ledger approvals (AC-0016) ----------------------------------------------

_LEDGER = "docs/specs/registry-upgrade-notes/notes/verification-ledger.md"


# AC-0016 is a delivery-time pin. The upgrade page is still bound at head; the record
# and the brief are bound to this spec's merge commit, because the closing slice
# (workspace-toml-deletion) edits both after this spec shipped.
_DELIVERY_COMMIT = "88c952f49"


def _approved_bytes(path: str) -> bytes:
    if path == UPGRADE_PAGE:
        return (REPO_ROOT / path).read_bytes()
    return subprocess.run(
        ["git", "show", f"{_DELIVERY_COMMIT}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout


def test_ac0016_ledger_binds_each_approved_file_at_head() -> None:
    ledger = read_text(REPO_ROOT / _LEDGER)
    for path in (UPGRADE_PAGE, _RECORD, _BRIEF):
        digest = hashlib.sha256(_approved_bytes(path)).hexdigest()
        rows = [
            line
            for line in ledger.splitlines()
            if line.startswith("| ") and "eugenelim" in line and f"`{path}`" in line
        ]
        assert rows, f"no approval row for {path}"
        assert f"`{digest}`" in rows[-1], f"{path}: ledger SHA-256 differs from the file at head"


# --- Release metadata (AC-0017) and the run-time bounds (AC-0020) ------------

_RENAME_MAP = "contracts/renames/pack-renames.toml"
_RENAME_MAP_BASE_SHA256 = "a6d7361be39a7addfc2471316426dcb89dada1c062f3528843699fd444823e57"


def test_ac0017_release_metadata_leads_with_the_new_versions() -> None:
    import tomllib

    version = tomllib.loads(read_text(REPO_ROOT / "packages/agentbundle/pyproject.toml"))[
        "project"
    ]["version"]
    changelog = read_text(REPO_ROOT / "packages/agentbundle/CHANGELOG.md")
    readme = read_text(REPO_ROOT / "packages/agentbundle/README-pypi.md")
    first_release = next(line for line in changelog.splitlines() if line.startswith("## ["))
    assert first_release.startswith(f"## [{version}]")
    first_news = next(line for line in readme.splitlines() if line.startswith("## What's new in "))
    assert first_news == f"## What's new in {version}"
    marketplace = json.loads(read_text(REPO_ROOT / ".claude-plugin/marketplace.json"))
    listed = {entry["name"]: entry.get("version") for entry in marketplace["plugins"]}
    for pack, (released, _fragment_path) in _RELEASED.items():
        if pack in listed:
            assert listed[pack] == released, pack


def _projection_files(root: Path) -> set[Path]:
    return {
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts
    }


def test_ac0020_every_skill_copy_but_work_loop_matches_its_source() -> None:
    sources = {
        skill.name: skill for skill in REPO_ROOT.glob("packs/*/.apm/skills/*") if skill.is_dir()
    }
    bad = []
    for target_root in (REPO_ROOT / ".claude/skills", REPO_ROOT / ".agents/skills"):
        for target in sorted(p for p in target_root.iterdir() if p.is_dir()):
            if target.name == "work-loop" or target.name not in sources:
                continue
            source = sources[target.name]
            files = _projection_files(source)
            if _projection_files(target) != files:
                bad.append(f"{target}: file set differs")
                continue
            bad.extend(
                f"{target / rel}"
                for rel in sorted(files)
                if (target / rel).read_bytes() != (source / rel).read_bytes()
            )
    assert bad == []


def test_ac0020_rename_map_is_unchanged_from_the_base() -> None:
    digest = hashlib.sha256((REPO_ROOT / _RENAME_MAP).read_bytes()).hexdigest()
    assert digest == _RENAME_MAP_BASE_SHA256


def test_self_ac0011_sees_a_page_the_build_adds(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    journeys = root / "web/src/content/journeys"
    journeys.mkdir(parents=True)
    (journeys / "core.md").write_text("# core\n", encoding="utf-8")
    (journeys / ".gitignore").write_text("ignored.md\n", encoding="utf-8")
    build = root / "tools/build-site.py"
    build.parent.mkdir(parents=True)
    build.write_text(
        "from pathlib import Path\n"
        "d = Path('web/src/content/journeys')\n"
        "(d / 'ignored.md').write_text('generated\\n')\n"
        "(d / 'new-pack.md').write_text('# new\\n')\n",
        encoding="utf-8",
    )
    for args in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *args], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "commit",
            "-qm",
            "seed",
        ],
        cwd=root,
        check=True,
    )
    pages = DISPATCH_PAGES
    try:
        globals()["DISPATCH_PAGES"] = ()
        found = check_ac0011(root)
    finally:
        globals()["DISPATCH_PAGES"] = pages
    assert found == ["web/src/content/journeys changed by build-site --journeys-only"]
    (journeys / "new-pack.md").unlink()
    build.write_text(
        "from pathlib import Path\n"
        "(Path('web/src/content/journeys') / 'ignored.md').write_text('again\\n')\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "commit",
            "-qm",
            "build",
        ],
        cwd=root,
        check=True,
    )
    try:
        globals()["DISPATCH_PAGES"] = ()
        assert check_ac0011(root) == []
    finally:
        globals()["DISPATCH_PAGES"] = pages
