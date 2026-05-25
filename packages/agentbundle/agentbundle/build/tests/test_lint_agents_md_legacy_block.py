"""T9 / AC31 — `tools/lint-agents-md.py` warns when a projected
`AGENTS.md` still carries the legacy `<!-- agent-skills:start -->`
literal *and* the contract declares Codex `skill` as `direct-directory`.

The check fires through the linter's existing `warn(...)` closure
(prefix `⚠` on stderr), not `note(...)` — so the exit code remains 0.

Test shape: CLI subprocess invocation in a `tmp_path` scratch tree
that mirrors the repo's layout (root `AGENTS.md`, `CLAUDE.md` symlink,
synthetic `docs/contracts/adapter.toml`). The linter is run with
`cwd=tmp_path`; the test asserts the return code and stderr.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
LINTER = REPO_ROOT / "tools" / "lint-agents-md.py"


_CONTRACT_DIRECT_DIRECTORY = """\
[primitive.skill]
source-path = ".apm/skills/"

[[adapter.codex.projection]]
primitive = "skill"
mode = "direct-directory"
target-path = ".agents/skills/"
on-conflict = "prompt-then-preserve"
"""

_CONTRACT_LEGACY = """\
[primitive.skill]
source-path = ".apm/skills/"

[[adapter.codex.projection]]
primitive = "skill"
mode = "managed-block-inline"
target-path = "AGENTS.md"
managed-block-delimiter-start = "<!-- agent-skills:start -->"
managed-block-delimiter-end = "<!-- agent-skills:end -->"
on-conflict = "preserve-outside-block"
"""


def _seed_tree(
    root: Path,
    contract_body: str,
    agents_md_body: str,
) -> None:
    contracts = root / "docs" / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "adapter.toml").write_text(contract_body, encoding="utf-8")

    (root / "AGENTS.md").write_text(agents_md_body, encoding="utf-8")
    (root / "CLAUDE.md").symlink_to("AGENTS.md")


def _run_linter(cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    return subprocess.run(
        [sys.executable, str(LINTER)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class LegacyBlockWarningTests(unittest.TestCase):
    def test_warns_when_legacy_marker_present_with_direct_directory_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _seed_tree(
                tmp_path,
                contract_body=_CONTRACT_DIRECT_DIRECTORY,
                agents_md_body=(
                    "# AGENTS.md\n\n"
                    "Outside content.\n\n"
                    "<!-- agent-skills:start -->\n"
                    "- **work-loop** — desc\n"
                    "<!-- agent-skills:end -->\n"
                ),
            )

            result = _run_linter(tmp_path)
            # The warning must fire and must name the offending file
            # path. It must NOT change the exit code — other checks
            # (e.g. CLAUDE.md symlink, AGENTS.md size) determine the
            # return value.
            self.assertIn("legacy-codex-skill-block", result.stderr)
            self.assertIn("AGENTS.md", result.stderr)
            self.assertIn("⚠", result.stderr)

    def test_no_warn_when_legacy_marker_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _seed_tree(
                tmp_path,
                contract_body=_CONTRACT_DIRECT_DIRECTORY,
                agents_md_body="# AGENTS.md\n\nNo legacy block here.\n",
            )

            result = _run_linter(tmp_path)
            self.assertNotIn("legacy-codex-skill-block", result.stderr)

    def test_no_warn_when_contract_still_managed_block(self) -> None:
        # If the contract hasn't flipped (some adopter mid-upgrade
        # against an older bundle), the marker is expected — the linter
        # does not warn.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _seed_tree(
                tmp_path,
                contract_body=_CONTRACT_LEGACY,
                agents_md_body=(
                    "# AGENTS.md\n\n"
                    "<!-- agent-skills:start -->\n"
                    "<!-- agent-skills:end -->\n"
                ),
            )

            result = _run_linter(tmp_path)
            self.assertNotIn("legacy-codex-skill-block", result.stderr)


if __name__ == "__main__":
    unittest.main()
