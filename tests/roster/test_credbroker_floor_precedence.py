"""Repository roster pin for credential consumer floor bootstraps."""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKS = REPO_ROOT / "packs"
CONSUMER_SCRIPTS = [
    ("credential-brokers/.apm/skills/credential-setup/scripts", "setup.py"),
    ("figma/.apm/skills/figma/scripts", "figma.py"),
    ("atlassian/.apm/skills/jira/scripts", "jira.py"),
    ("atlassian/.apm/skills/jira-align/scripts", "jira_align.py"),
    ("atlassian/.apm/skills/confluence-crawler/scripts", "crawl_space.py"),
    ("atlassian/.apm/skills/confluence-publisher/scripts", "publish_page.py"),
]


@pytest.mark.parametrize("skill_relpath,entry_name", CONSUMER_SCRIPTS)
def test_floor_appended_lowest_precedence_never_inserted(
    skill_relpath: str, entry_name: str,
) -> None:
    entry = PACKS / skill_relpath / entry_name
    if not entry.is_file():
        pytest.skip(f"{entry} not present in this checkout")
    source = entry.read_text(encoding="utf-8")
    assert '"~/.agentbundle/lib").expanduser()' in source
    assert "sys.path.append(str(_floor))" in source
    for line in source.splitlines():
        if "sys.path.insert" in line:
            assert "_floor" not in line and "agentbundle/lib" not in line
    append_index = source.index("sys.path.append(str(_floor))")
    if entry_name == "setup.py":
        assert append_index < source.index("from credbroker import")
    else:
        assert source.index("sys.path.insert(0, str(_here.parent))") < append_index
