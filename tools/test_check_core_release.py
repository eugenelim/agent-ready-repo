"""The release checker's case table, from the plan's T7.

Every refusing row is directed at one wrong implementation. A single vague
"wrong version" case would be satisfied by a checker that ignores the major
component, by one that ignores the minor, and by one that accepts any patch
inequality -- so it rejects none of them.

Two rows carry decoys: the expected version appears in a *later* changelog
entry, and a valid Highlights bullet appears in a *later* entry. Without those,
a checker that searches the whole file passes while checking nothing about the
topmost entry.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_core_release", Path(__file__).resolve().parent / "check-core-release.py"
)
ccr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ccr)

BASE = "1.4.7"


def _changelog(*entries: tuple[str, bool]) -> str:
    """Entries top-down as (version, has_bullet)."""
    out = ["# Changelog\n"]
    for version, bullet in entries:
        out.append(f"## [core][{version}] — 2026-09-19\n")
        out.append("### Highlights\n")
        out.append("- A consumer-visible change.\n" if bullet else "\n")
    return "\n".join(out)


def _repo(tmp_path: Path, *, version: str, plugin: str | None = None,
          changelog: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "packs/core/.claude-plugin").mkdir(parents=True)
    (root / "docs/product").mkdir(parents=True)
    (root / "packs/core/pack.toml").write_text(
        f'[pack]\nname = "core"\nversion = "{BASE}"\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e", "-c", "user.name=t",
         "commit", "-qm", "base"], cwd=root, check=True)

    (root / "packs/core/pack.toml").write_text(
        f'[pack]\nname = "core"\nversion = "{version}"\n', encoding="utf-8")
    (root / "packs/core/.claude-plugin/plugin.json").write_text(
        json.dumps({"name": "core", "version": plugin or version}), encoding="utf-8")
    (root / "docs/product/changelog.md").write_text(
        changelog if changelog is not None else _changelog((version, True)),
        encoding="utf-8")
    return root


def test_a_valid_patch_successor_is_accepted(tmp_path):
    assert ccr.check(_repo(tmp_path, version="1.4.8"), "HEAD") == []


@pytest.mark.parametrize("version", ["2.4.8", "1.5.8", "1.4.7", "1.4.6", "1.4.9"])
def test_a_version_that_is_not_the_patch_successor_is_refused(tmp_path, version):
    """Major, minor, unchanged, one lower, and overshoot -- each its own case."""
    assert ccr.check(_repo(tmp_path, version=version), "HEAD")


def test_a_wrong_pack_toml_alone_is_refused(tmp_path):
    root = _repo(tmp_path, version="1.4.9", plugin="1.4.8",
                 changelog=_changelog(("1.4.8", True)))
    assert ccr.check(root, "HEAD")


def test_a_wrong_plugin_json_alone_is_refused(tmp_path):
    root = _repo(tmp_path, version="1.4.8", plugin="1.4.9")
    assert ccr.check(root, "HEAD")


def test_a_wrong_topmost_entry_is_refused_even_when_a_later_entry_matches(tmp_path):
    """Decoy: the expected version is present, but not at the top."""
    root = _repo(tmp_path, version="1.4.8",
                 changelog=_changelog(("1.4.7", True), ("1.4.8", True)))
    assert ccr.check(root, "HEAD")


def test_an_unbulleted_target_entry_is_refused_even_when_a_later_entry_has_one(tmp_path):
    """Decoy: a valid bullet exists in the file, but not in the target entry."""
    root = _repo(tmp_path, version="1.4.8",
                 changelog=_changelog(("1.4.8", False), ("1.4.7", True)))
    assert ccr.check(root, "HEAD")


def test_an_unresolvable_base_is_refused(tmp_path):
    reasons = ccr.check(_repo(tmp_path, version="1.4.8"), "not-a-commit")
    assert reasons and "does not resolve" in reasons[0]


# ------------------------------------------------------------------- AC-0016

def _independent_highlight_bullets(changelog: str, version: str) -> list[str]:
    """Read the entry's bullets without using the projection's own parser.

    The repository's existing real-changelog tests build BOTH their expected and
    their actual values from `build_site.parse_changelog_releases`, so an entry
    that parser cannot see is absent from both sides and those tests stay green
    while the entry never reaches the page. This reader exists to not share that
    blind spot.
    """
    import re as _re
    head = _re.compile(r"^## \[core\]\[" + _re.escape(version) + r"\]", _re.M)
    match = head.search(changelog)
    assert match, f"no core {version} entry"
    body = changelog[match.end():]
    nxt = _re.search(r"^## \[", body, _re.M)
    entry = body[: nxt.start()] if nxt else body
    section = entry.split("### Highlights", 1)[1].split("\n### ", 1)[0]

    bullets, current = [], None
    for line in section.splitlines():
        if _re.match(r"^- \S", line):
            if current is not None:
                bullets.append(" ".join(current.split()))
            current = line[2:]
        elif current is not None and line.startswith("  "):
            current += " " + line.strip()
        elif current is not None and not line.strip():
            bullets.append(" ".join(current.split()))
            current = None
    if current is not None:
        bullets.append(" ".join(current.split()))
    return bullets


def test_this_releases_highlights_reach_the_now_payload():
    import importlib.util as _ilu
    root = Path(__file__).resolve().parents[1]
    spec = _ilu.spec_from_file_location("build_site", root / "tools" / "build-site.py")
    build_site = _ilu.module_from_spec(spec)
    spec.loader.exec_module(build_site)

    import tomllib as _tomllib
    version = _tomllib.loads(
        (root / "packs/core/pack.toml").read_text(encoding="utf-8")
    )["pack"]["version"]
    changelog = (root / "docs/product/changelog.md").read_text(encoding="utf-8")

    payload = build_site.project_now_highlights(changelog)
    groups = [
        g for g in payload["groups"]
        if any(p["name"] == "core" and p["version"] == version for p in g["packages"])
    ]
    assert len(groups) == 1, f"expected exactly one core {version} group"

    projected = [" ".join(h["source"].split()) for h in groups[0]["highlights"]]
    assert projected == _independent_highlight_bullets(changelog, version)


def test_highlights_under_a_sibling_section_do_not_count(tmp_path):
    """A `## Notes` section's Highlights must not stand in for a missing one.

    The target entry has NO Highlights subsection at all. A checker that ends
    the entry at the next *release* heading reads the sibling section's bullet
    as this release's and wrongly accepts; ending at the next equal-or-shallower
    heading refuses. The two implementations disagree on exactly this input,
    which is what makes the case worth writing.
    """
    changelog = (
        "# Changelog\n\n"
        "## [core][1.4.8] — 2026-09-19\n\n"
        "Some entry prose with no Highlights subsection.\n\n"
        "## Notes\n\n"
        "### Highlights\n\n"
        "- A bullet that belongs to the notes section.\n"
    )
    assert ccr.check(_repo(tmp_path, version="1.4.8", changelog=changelog), "HEAD")
