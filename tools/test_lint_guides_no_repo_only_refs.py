"""Black-box contract tests for the shipped-guide governance-reference lint."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_SCRIPT = REPO_ROOT / "tools" / "lint-guides-no-repo-only-refs.py"


def _run_lint(tmp_path: Path, markdown: str) -> subprocess.CompletedProcess[str]:
    guides_root = tmp_path / "guides"
    guides_root.mkdir()
    (guides_root / "example.md").write_text(markdown, encoding="utf-8")
    (tmp_path / "docs" / "specs" / "real-record").mkdir(parents=True)
    return subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--guides-root", str(guides_root)],
        check=False,
        capture_output=True,
        text=True,
    )


# STUB: AC2 — every forbidden Markdown destination class is rejected.
@pytest.mark.parametrize(
    ("markdown", "reason_fragment"),
    [
        ("[decision](../../../docs/adr/0001-example.md)\n", "adr"),
        ("[proposal](../../../rfc/0071-example.md)\n", "rfc"),
        ("[contract](../../../specs/real-record/spec.md)\n", "specs"),
        ("[history](../../../docs/CHANGELOG.md)\n", "changelog"),
    ],
)
def test_forbidden_markdown_link_targets_fail(
    tmp_path: Path,
    markdown: str,
    reason_fragment: str,
) -> None:
    result = _run_lint(tmp_path, markdown)

    assert result.returncode == 1
    assert "example.md:1:" in result.stdout
    assert reason_fragment in result.stdout.lower()


def test_forbidden_reference_link_target_fails(tmp_path: Path) -> None:
    result = _run_lint(
        tmp_path,
        "Read the [proposal][internal].\n\n[internal]: ../../../rfc/0071-example.md\n",
    )

    assert result.returncode == 1
    assert "example.md:3:" in result.stdout
    assert "/rfc/" in result.stdout


# STUB: AC3 — numbered decision-record tokens are rejected.
@pytest.mark.parametrize("token", ["RFC-0071", "ADR-12", "ADR-1234"])
def test_numbered_governance_tokens_fail(tmp_path: Path, token: str) -> None:
    result = _run_lint(tmp_path, f"Governed by {token}.\n")

    assert result.returncode == 1
    assert "example.md:1:" in result.stdout
    assert token in result.stdout


# STUB: AC4 — a spec citation is rejected when its slug exists under docs/specs.
@pytest.mark.parametrize("citation", ["spec/real-record", "docs/specs/real-record/spec.md"])
def test_real_spec_slug_citations_fail(tmp_path: Path, citation: str) -> None:
    result = _run_lint(tmp_path, f"See `{citation}` for authority.\n")

    assert result.returncode == 1
    assert "example.md:1:" in result.stdout
    assert "real spec" in result.stdout.lower()


# STUB: AC4 — concepts, placeholders, commands, and invented examples stay valid.
def test_kept_spec_examples_pass(tmp_path: Path) -> None:
    result = _run_lint(
        tmp_path,
        "\n".join([
            "Use spec/plan, spec/loop, and spec/slice as concepts.",
            "new-spec drafts docs/specs/<feature>/spec.md.",
            "Run work-loop docs/specs/<slug>/.",
            "Try the invented docs/specs/webhook-retries/ example.",
            "",
        ]),
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "OK — no repo-only governance references in guides/"


# STUB: AC5 — the documented marker suppresses its own or the following line.
@pytest.mark.parametrize(
    "markdown",
    [
        "See RFC-0071. <!-- guides-lint: allow compatibility example -->\n",
        "<!-- guides-lint: allow compatibility example -->\nSee RFC-0071.\n",
    ],
)
def test_allow_marker_suppresses_same_or_next_line(
    tmp_path: Path,
    markdown: str,
) -> None:
    result = _run_lint(tmp_path, markdown)

    assert result.returncode == 0


# STUB: AC1/AC6 — the real command exposes help and exact clean output.
def test_help_and_clean_exit_contract(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    clean_result = _run_lint(tmp_path, "Record an ADR or open an RFC.\n")

    assert help_result.returncode == 0
    assert "--guides-root" in help_result.stdout
    assert clean_result.returncode == 0
    assert clean_result.stdout == "OK — no repo-only governance references in guides/\n"


# STUB: AC1 — resolved guide files must remain inside the selected guide root.
def test_symlinked_guide_file_escape_fails_closed(tmp_path: Path) -> None:
    guides_root = tmp_path / "guides"
    guides_root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("See RFC-0071.\n", encoding="utf-8")
    try:
        (guides_root / "escape.md").symlink_to(outside)
    except OSError as exc:  # pragma: no cover - platform permission limitation
        pytest.skip(f"symlink creation unavailable: {exc}")
    (tmp_path / "docs" / "specs").mkdir(parents=True)

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--guides-root", str(guides_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "outside the guides root" in result.stderr.lower()


# STUB: AC1 — resolved spec directories must remain inside docs/specs.
def test_symlinked_spec_directory_escape_fails_closed(tmp_path: Path) -> None:
    guides_root = tmp_path / "guides"
    guides_root.mkdir()
    (guides_root / "example.md").write_text("A clean guide.\n", encoding="utf-8")
    specs_root = tmp_path / "docs" / "specs"
    specs_root.mkdir(parents=True)
    outside = tmp_path / "outside-spec"
    outside.mkdir()
    try:
        (specs_root / "escape-record").symlink_to(outside, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - platform permission limitation
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--guides-root", str(guides_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "outside the specs root" in result.stderr.lower()


# STUB: AC1 — recursive discovery refuses linked directories before descent.
def test_symlinked_guide_directory_fails_closed(tmp_path: Path) -> None:
    guides_root = tmp_path / "guides"
    guides_root.mkdir()
    real_directory = guides_root / "real"
    real_directory.mkdir()
    (real_directory / "example.md").write_text("A clean guide.\n", encoding="utf-8")
    try:
        (guides_root / "alias").symlink_to(real_directory, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - platform permission limitation
        pytest.skip(f"symlink creation unavailable: {exc}")
    (tmp_path / "docs" / "specs").mkdir(parents=True)

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--guides-root", str(guides_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "linked guide directory" in result.stderr.lower()


# STUB: AC1 — path-resolution loops fail closed at the CLI boundary.
def test_self_referential_guides_root_fails_closed(tmp_path: Path) -> None:
    guides_root = tmp_path / "guides"
    try:
        guides_root.symlink_to(guides_root, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - platform permission limitation
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--guides-root", str(guides_root)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "resolve" in result.stderr.lower()
