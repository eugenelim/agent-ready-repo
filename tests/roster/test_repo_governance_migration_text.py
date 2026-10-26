"""AC-0026: the release texts carry the hint builder's migration steps."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from agentbundle.pack_renames import Installed, build_rename_hint
from agentbundle.version import CLI_VERSION

REPO = Path(__file__).resolve().parents[2]
_FIXTURES = REPO / "packages" / "agentbundle" / "tests" / "_rename_fixtures.py"
_spec = importlib.util.spec_from_file_location("_rename_fixtures", _FIXTURES)
assert _spec is not None and _spec.loader is not None
fx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fx)

SOURCE = "git+https://github.com/eugenelim/agent-ready-repo"
SENTENCE = (
    "Replace `claude-code` with the adapter your `governance-extras` is "
    "installed for."
)
STEP_RE = re.compile(r"^\s*\d+\. (agentbundle .+)$", re.MULTILINE)


def _hint_steps(tmp_path: Path) -> list[str]:
    cat = fx.catalogue(tmp_path, packs={fx.DEP: fx.DEP_TOML})
    installed = Installed(
        {
            ("governance-extras", "claude-code"): SOURCE,
            ("iac-terraform", "claude-code"): SOURCE,
        }
    )
    hint = build_rename_hint(
        "governance-extras",
        catalogue_dir=cat,
        source=SOURCE,
        installed=installed,
        command="install",
    )
    steps = STEP_RE.findall("\n".join(hint.lines))
    assert len(steps) == 3
    return steps


def _changelog_entry() -> str:
    text = (REPO / "packages/agentbundle/CHANGELOG.md").read_text(encoding="utf-8")
    return text.split("## [0.57.0]", 1)[1].split("\n## [", 1)[0]


def _readme_section() -> str:
    text = (REPO / "packs/repo-governance/README.md").read_text(encoding="utf-8")
    heading = "## Migrating from governance-extras"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_version_reads_0_57_0() -> None:
    assert CLI_VERSION == "0.57.0"


def test_changelog_and_readme_steps_equal_the_hint(tmp_path: Path) -> None:
    expected = _hint_steps(tmp_path)
    for text in (_changelog_entry(), _readme_section()):
        assert STEP_RE.findall(text) == expected


def test_both_texts_carry_the_replace_adapter_sentence() -> None:
    for text in (_changelog_entry(), _readme_section()):
        assert SENTENCE in text
