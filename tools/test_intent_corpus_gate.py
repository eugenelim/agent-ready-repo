"""The intent corpus lint is wired to a gate that fails on its exit code.

Covers T8 of `docs/specs/intent-metadata-shape-contract/plan.md`. Which gate it
is was a repository-local placement decision taken at execution: `docs.yml`
already runs doc-tree linters against the real tree, and its `paths:` filter
already carries both triggers this check needs — `docs/**` for the intents
themselves and `packs/**/.apm/skills/**` for the validator that decides them.

The workflow is read as text rather than parsed, matching
`tools/test_build_gate_chain.py`: these suites run in a dependency-free context
where importing a YAML library fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"
LINT = (
    "packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py"
)
INTENTS = "docs/product/intents"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_a_job_runs_the_intent_corpus_lint() -> None:
    """Without this, the lint's exit code is one nobody invokes."""
    text = _workflow()
    assert "lint-intent-corpus:" in text
    assert LINT in text
    assert f"--dir {INTENTS}" in text


def test_the_workflow_fires_when_an_intent_changes() -> None:
    """A gate that never runs is not a gate."""
    text = _workflow()
    paths = text[: text.index("jobs:")]
    assert "'docs/**'" in paths


def test_the_workflow_fires_when_the_validator_changes() -> None:
    """A rule change must re-check the corpus it decides."""
    text = _workflow()
    paths = text[: text.index("jobs:")]
    assert "'packs/**/.apm/skills/**'" in paths


def test_the_lint_exits_non_zero_on_a_seeded_violation(tmp_path: Path) -> None:
    """The gate's premise: a non-conforming intent makes the command fail.

    Seeded in a temporary directory rather than the real one, so the assertion
    needs no write to `docs/product/intents/` and cannot leave the tree dirty.
    """
    directory = tmp_path / "intents"
    directory.mkdir()
    conforming = "\n".join(
        [
            "# Intent: a fixture",
            "",
            "- **Slug:** `a-fixture`",
            "- **Level:** feature",
            "- **Owner:** eugenelim",
            "- **Status:** Draft",
            "",
            "## Outcome",
            "",
            "Text.",
            "",
        ]
    )
    (directory / "FEAT-0001-a.md").write_text(conforming, encoding="utf-8")

    clean = subprocess.run(
        [sys.executable, str(ROOT / LINT), "--dir", "intents", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert clean.returncode == 0, clean.stderr

    (directory / "FEAT-0002-bad.md").write_text(
        conforming.replace("- **Status:** Draft", "- **Status:** Shipped").replace(
            "a-fixture", "bad-fixture"
        ),
        encoding="utf-8",
    )
    seeded = subprocess.run(
        [sys.executable, str(ROOT / LINT), "--dir", "intents", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert seeded.returncode != 0
    assert "FEAT-0002-bad.md" in seeded.stderr
    assert "Status" in seeded.stderr


def test_the_real_corpus_passes_the_gate_today() -> None:
    """AC-0033 at the gate's own entry point, not only through the library."""
    result = subprocess.run(
        [sys.executable, str(ROOT / LINT), "--dir", INTENTS, "--root", str(ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout
