"""Keep the release-only journey unchanged beside core-like installed files."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "platform_engineering_release_loop_core_journey_helpers",
    HERE / "test_github_release_journeys.py",
)
assert spec and spec.loader
helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helpers
spec.loader.exec_module(helpers)
# This fixture also reuses test_release_admission_journey's local review records.
journey = helpers.journey


class CorePresentJourney(helpers.GithubJourney):
    """Use the same stages while allowing optional core files in the installation."""

    def isolated(self) -> None:
        """Keep runtime modules confined and require the core-like files to remain."""
        assert {path.name for path in (self.root / "skills").iterdir()} == {
            "release-loop", "prepare-release-handoff", "work-loop",
        }
        assert (self.root / "skills/work-loop/SKILL.md").is_file()
        for name in ("quality-engineer", "security-reviewer"):
            assert (self.root / "agents" / f"{name}.md").is_file()
        for path in self.root.rglob("*"):
            assert not path.is_symlink()
            assert path.resolve().is_relative_to(self.root.resolve())
        for module in (self.collector, self.validator, self.admission, self.admission.handoff,
                       self.github, self.github.admission, self.github.handoff):
            assert Path(module.__file__).resolve().is_relative_to(self.root.resolve())


def test_release_only_with_core(journey: Any) -> None:
    """Reach the same final result with core-like skills and reviewers alongside."""
    # Pack tests cannot read another pack; model only its optional installed layout.
    skill = journey.root / "skills/work-loop"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: work-loop\ndescription: Core-like workflow stand-in.\n---\n"
        "# Work loop\nFollow the repository's workflow.\n", encoding="utf-8",
    )
    agents = journey.root / "agents"
    agents.mkdir()
    for name in ("quality-engineer", "security-reviewer"):
        (agents / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: Optional core-like reviewer.\n---\n"
            "Review only when requested; required local reviews still apply.\n",
            encoding="utf-8",
        )
    installed = CorePresentJourney(
        journey.root, journey.collector, journey.validator, journey.admission,
        journey.request, journey.capsys,
    )
    installed.github = journey.github
    installed.controls = journey.controls
    installed.snapshot = journey.snapshot
    helpers.test_application_release_reaches_final(installed)
