"""The governance-extras to repo-governance rename is complete (AC-0001 to AC-0003, AC-0025).

`git grep -l` for the old pack name must return only paths the rename spec
admits: frozen records, the build-pipeline fixture, pinned baseline evidence,
the rename map, the migration text, and tests of the hint, the lint and this
check. Frozen status comes from a file's own or owning record's `Status:` line
and from RFC-0110 D3's path rule for dated changelog history.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

from agentbundle.cli import _build_parser
from agentbundle.commands.install import run

REPO_ROOT = Path(__file__).resolve().parents[2]
# Built from parts so this file is not a hit of its own search.
OLD_NAME = "governance" + "-extras"
NEW_NAME = "repo-governance"

FROZEN_RECORD_STATUSES = {"accepted", "rejected", "withdrawn"}
FROZEN_SPEC_STATUSES = {"shipped", "done", "archived", "complete", "recorded"}
_STATUS_RE = re.compile(
    r"^[\s>*-]*\**Status(?::\*\*|\*\*:|:)\s*\**([A-Za-z]+)", re.MULTILINE | re.IGNORECASE
)

FIXTURE_DIR = "packages/agentbundle/tests/build_pipeline/fixtures/"
# Exact paths admitted regardless of status (migration text, hint, lint and
# check tests, the map itself).
ADMITTED_PATHS = frozenset({
    "contracts/renames/pack-renames.toml",
    "packages/agentbundle/CHANGELOG.md",
    "packages/agentbundle/tests/_rename_fixtures.py",
    "tests/roster/test_repo_governance_migration_text.py",
    "packs/repo-governance/README.md",
    "packages/agentbundle/tests/unit/test_pack_renames.py",
    "packages/agentbundle/tests/integration/test_rename_hint_cli.py",
    "packages/agentbundle/tests/integration/test_rename_migration_e2e.py",
    "packages/agentbundle/tests/integration/_https_archive.py",
    "tools/lint-pack-renames.py",
    "tools/test-lint-pack-renames.py",
    "tests/roster/test_repo_governance_rename_completeness.py",
    "packages/agentbundle/tests/build_pipeline/fixtures/README.md",
    "packages/agentbundle/tests/build_pipeline/test_end_to_end_build.py",
    "docs/product/briefs/repo-governance-pack.md",
    # Digest-pinned golden fixture; its test forbids regeneration.
    "packs/core/tests/skills/work-loop/fixtures/corpus/001-recorded/plan.md",
})
INVENTORY = "docs/specs/workspace-retirement/inventory.toml"
FROZEN_SPEC_DIR = "docs/specs/" + OLD_NAME + "-without-core/"
ADMITTED_PREFIXES = (
    FIXTURE_DIR + "packs/" + OLD_NAME + "/",
    "docs/product/research/plan-evolution-experiments/",
    "tools/plan_evolution_workbench/fixtures/",
    "docs/specs/" + "repo-governance-rename/",
    "docs/knowledge/observations/",
    "docs/product/changelog",
)
# Changelog fragments are named `docs/product/changelog.d/...`; the three
# agentbundle fragments are admitted by the prefix above.


def _status(path: Path) -> str | None:
    try:
        match = _STATUS_RE.search(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    return match.group(1).lower() if match else None


def _owning_record(rel: str) -> Path | None:
    """Return the record or spec file whose status governs `rel`, if any."""
    parts = rel.split("/")
    if parts[:2] in (["docs", "adr"], ["docs", "rfc"]) and len(parts) >= 3:
        ordinal = re.match(r"(\d+)", parts[2])
        if ordinal is None:
            return None
        if len(parts) == 3:
            return REPO_ROOT / rel
        for candidate in sorted((REPO_ROOT / "docs" / parts[1]).glob(ordinal.group(1) + "-*.md")):
            return candidate
        return None
    if parts[:2] == ["docs", "specs"] and len(parts) >= 4:
        folder = REPO_ROOT / "docs" / "specs" / parts[2]
        if parts[3] == "plan.md" and len(parts) == 4 and _status(folder / "plan.md"):
            return folder / "plan.md"
        for name in ("spec.md", "plan.md"):
            if (folder / name).is_file():
                return folder / name
    if parts[:3] == ["docs", "product", "intents"]:
        return REPO_ROOT / rel
    return None


def _is_frozen(rel: str) -> bool:
    if parts_match := re.match(r"packages/[^/]+/CHANGELOG\.md$", rel):
        return bool(parts_match)
    record = _owning_record(rel)
    if record is None:
        return False
    status = _status(record)
    if rel.startswith("docs/product/intents/"):
        return status == "fulfilled"
    if rel.startswith(("docs/adr/", "docs/rfc/")):
        return status in FROZEN_RECORD_STATUSES
    return status in FROZEN_SPEC_STATUSES


def _is_admitted(rel: str) -> bool:
    if rel in ADMITTED_PATHS or rel.startswith(ADMITTED_PREFIXES):
        return True
    if rel in ("docs/adr/README.md", "docs/rfc/README.md"):
        return _index_rows_are_frozen(rel)
    if rel == INVENTORY:
        return _inventory_lines_reference_frozen_spec(
            (REPO_ROOT / rel).read_text(encoding="utf-8")
        )
    if rel == "workspace.toml":
        return _workspace_lines_are_registrations()
    return _is_frozen(rel)


def _index_rows_are_frozen(rel: str) -> bool:
    """Every matching line of a generated index is the row of a frozen record."""
    kind = rel.split("/")[1]
    for line in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines():
        if OLD_NAME not in line:
            continue
        link = re.search(r"\((\d+-[^)\s]+\.md)\)", line) or re.search(
            r"\b(\d{4}-[\w-]+\.md)", line
        )
        if link is None:
            return False
        if _status(REPO_ROOT / "docs" / kind / link.group(1)) not in FROZEN_RECORD_STATUSES:
            return False
    return True


def _inventory_lines_reference_frozen_spec(text: str) -> bool:
    """Every line naming the old pack references the frozen spec directory."""
    return all(FROZEN_SPEC_DIR in line for line in text.splitlines() if OLD_NAME in line)


def _workspace_lines_are_registrations() -> bool:
    """Only the brief's and this spec's registrations may keep the old name."""
    allowed = (
        "docs/product/briefs/repo-governance-pack.md",
        "docs/specs/" + "repo-governance-rename/spec.md",
    )
    for line in (REPO_ROOT / "workspace.toml").read_text(encoding="utf-8").splitlines():
        if OLD_NAME in line and not any(f'path = "{path}"' in line for path in allowed):
            return False
    return True


def _grep_hits() -> list[str]:
    result = subprocess.run(
        ["git", "grep", "-l", OLD_NAME],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr
    return sorted(line for line in result.stdout.splitlines() if line)


def test_no_unclassified_path_names_the_old_pack() -> None:
    """AC-0025: every remaining hit is frozen, a fixture, or an admitted exception."""
    offenders = [rel for rel in _grep_hits() if not _is_admitted(rel)]
    assert offenders == [], "live paths still name the old pack:\n" + "\n".join(offenders)


def test_inventory_with_a_stray_live_line_is_not_admitted() -> None:
    """AC-0025: one live line naming the old pack in the inventory fails the check."""
    frozen = f'pattern = "{FROZEN_SPEC_DIR}*"'
    stray = f'pattern = "packs/{OLD_NAME}/pack.toml"'
    assert _inventory_lines_reference_frozen_spec(frozen)
    assert not _inventory_lines_reference_frozen_spec(frozen + "\n" + stray)


def test_old_pack_directories_are_gone() -> None:
    """AC-0025: the pack and its guides moved; nothing is left under the old paths."""
    assert not (REPO_ROOT / "packs" / OLD_NAME).exists()
    assert not (REPO_ROOT / "guides" / OLD_NAME).exists()


def test_pack_manifest_and_plugin_manifest_carry_the_new_name() -> None:
    """AC-0001: parsed pack.toml and plugin.json name the pack and version 2.2.0."""
    pack = tomllib.loads(
        (REPO_ROOT / "packs" / NEW_NAME / "pack.toml").read_text(encoding="utf-8")
    )["pack"]
    plugin = json.loads(
        (REPO_ROOT / "packs" / NEW_NAME / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )
    assert (pack["name"], pack["version"], pack["display_name"]) == (
        NEW_NAME,
        "2.2.0",
        "Repository Governance",
    )
    assert (plugin["name"], plugin["version"]) == (NEW_NAME, "2.2.0")


def test_iac_terraform_requires_the_renamed_pack() -> None:
    """AC-0002: iac-terraform is 0.2.0 and requires repo-governance ^2.0."""
    root = REPO_ROOT / "packs" / "iac-terraform"
    pack = tomllib.loads((root / "pack.toml").read_text(encoding="utf-8"))["pack"]
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert pack["version"] == "0.2.0" and plugin["version"] == "0.2.0"
    required = {dep["pack"]: dep["version"] for dep in pack["dependencies"]["required"]}
    assert required[NEW_NAME] == "^2.0"
    assert OLD_NAME not in required


def test_full_ceremony_profile_installs_the_renamed_pack(tmp_path: Path) -> None:
    """AC-0003: the profile install into an empty repository exits 0 and records 2.2.0."""
    args = _build_parser().parse_args([
        "install",
        str(REPO_ROOT),
        "--profile",
        "full-ceremony",
        "--output",
        str(tmp_path),
    ])
    assert run(args) == 0
    from agentbundle.config import load_state

    rows = load_state(tmp_path / ".agentbundle-state.toml").rows_for_pack(NEW_NAME)
    assert rows, "install recorded no state naming repo-governance"
    assert {ps.installed_version for ps in rows.values()} == {"2.2.0"}
