"""The intent corpus checks are wired to a gate that fails on their exit codes.

Two controls over the same directory, both reached through the same job:
`intent_corpus_lint.py --dir ... --root .` for the metadata shape, and
`intent_ordinal.py --check ...` for typed-ordinal uniqueness. The second had no
caller anywhere until it was added here — allocation is invoked by prose in
`work-intake/SKILL.md`, so a hand-made rename reusing an ordinal left no trace.

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
ORDINAL = "packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py"
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


def test_a_job_runs_the_intent_ordinal_check() -> None:
    """Without this, `--check` is a mode with no caller in the repository.

    Asserted on the job body rather than the file, so the step cannot drift
    into some other workflow whose `paths:` filter does not carry the intents.
    """
    text = _workflow()
    start = text.index("  lint-intent-corpus:")
    job = text[start : text.index("\n  lint-guide-titles:", start)]
    assert ORDINAL in job
    assert f"--check {INTENTS}" in job


def test_the_ordinal_check_exits_non_zero_on_a_seeded_duplicate(
    tmp_path: Path,
) -> None:
    """The gate's premise: two records on one typed ordinal make it fail.

    `--check` takes no `--root`; it resolves its argument against the process
    working directory and refuses an escape. So this runs the way the workflow
    step runs it — cwd at the tree root, the directory passed relative.
    """
    directory = tmp_path / "intents"
    directory.mkdir()
    body = "# Intent\n"
    (directory / "FEAT-0001-alpha.md").write_text(body, encoding="utf-8")

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / ORDINAL), "--check", "intents"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

    clean = run()
    assert clean.returncode == 0, clean.stderr
    assert "no duplicate ordinals" in clean.stderr

    # A different type on the same ordinal is not a collision: the namespace is
    # per token. Without this the next assertion would also pass for a check
    # that ignored the token and counted bare digits.
    (directory / "CAP-0001-beta.md").write_text(body, encoding="utf-8")
    still_clean = run()
    assert still_clean.returncode == 0, still_clean.stderr

    (directory / "FEAT-0001-gamma.md").write_text(body, encoding="utf-8")
    seeded = run()
    assert seeded.returncode == 1, seeded.stdout
    assert "duplicate ordinal FEAT-0001" in seeded.stderr


def test_the_real_corpus_has_no_duplicate_ordinals_today() -> None:
    """The live claim, at the gate's own entry point rather than a fixture."""
    result = subprocess.run(
        [sys.executable, str(ROOT / ORDINAL), "--check", INTENTS],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "no duplicate ordinals" in result.stderr
