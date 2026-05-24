"""T11: ``add-credentialed-skill`` author skill — goal-based checks
against the seed and template body (spec § AC28).
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SEED_SKILL = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "add-credentialed-skill"
PROJECTED_SKILL = REPO_ROOT / ".claude" / "skills" / "add-credentialed-skill"
TEMPLATE = SEED_SKILL / "assets" / "credentialed-skill-SKILL.md"
LINT_CRED_SKILLS = REPO_ROOT / "tools" / "lint-credentialed-skills.sh"


def test_seed_skill_exists():
    assert SEED_SKILL.is_dir()
    assert (SEED_SKILL / "SKILL.md").is_file()
    assert TEMPLATE.is_file()


def test_projected_skill_matches_seed():
    """`make build-self` should keep seed and projected in sync."""
    assert PROJECTED_SKILL.is_dir()
    assert (PROJECTED_SKILL / "SKILL.md").is_file()
    # The projected SKILL.md content equals the seed (modulo any pack-build
    # rewriting; lint catches drift in build-check).
    seed_body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    projected_body = (PROJECTED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert seed_body == projected_body, "seed and projected diverged — rerun make build-self"


def test_skill_frontmatter_includes_required_triggers():
    """AC28: triggers listed in description."""
    body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    # Frontmatter is between the first pair of ``---`` lines.
    parts = body.split("---", 2)
    assert len(parts) >= 3
    frontmatter = parts[1]
    assert "name: add-credentialed-skill" in frontmatter
    description_line = [
        line for line in frontmatter.splitlines()
        if line.startswith("description:")
    ]
    assert len(description_line) == 1
    desc = description_line[0]
    for trigger in (
        "add a credentialed skill",
        "new credentialed primitive",
    ):
        assert trigger in desc, f"trigger phrase missing from description: {trigger!r}"


def test_template_has_both_labelled_variants():
    """AC28: template carries `### Variant: credentialed-cli` and
    `### Variant: mcp-server`."""
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "### Variant: credentialed-cli" in body
    assert "### Variant: mcp-server" in body


def test_credentialed_cli_variant_contains_verbatim_dont_block():
    """AC28: the credentialed-cli variant carries the verbatim RFC-0006 § 4
    block (two ``**Never**`` lines + the ``do not run it for them``
    phrase + the ``agentbundle creds setup <namespace>`` reference)."""
    body = TEMPLATE.read_text(encoding="utf-8")
    # Slice to the credentialed-cli variant section.
    start = body.find("### Variant: credentialed-cli")
    end = body.find("### Variant: mcp-server")
    assert start >= 0 and end > start, "variants not in expected order"
    section = body[start:end]
    for phrase in (
        "**Never** read that file, print it, or echo the token",
        "**Never** put the token on the command line",
        "do not run it for them",
        "agentbundle creds setup <namespace>",
        "### Security rules (non-negotiable)",
    ):
        assert phrase in section, (
            f"credentialed-cli variant missing phrase: {phrase!r}"
        )


def test_template_block_passes_t10_lint_when_copied_into_a_skill(tmp_path):
    """AC28 template+lint integration: a fixture skill that copies the
    credentialed-cli variant body into its SKILL.md passes T10's
    `lint-credentialed-skills.sh` clean. Closes the drift-trap between
    the template (T11) and the lint (T10)."""
    if not LINT_CRED_SKILLS.is_file():
        pytest.skip(
            "T10 lint script absent (this test is gated on T10 having merged)"
        )
    template_body = TEMPLATE.read_text(encoding="utf-8")
    start = template_body.find("### Variant: credentialed-cli")
    end = template_body.find("### Variant: mcp-server")
    variant_section = template_body[start:end]

    # Extract the markdown ``` block (the actual skill body the author copies)
    code_start = variant_section.find("```markdown\n")
    code_end = variant_section.find("```", code_start + len("```markdown\n"))
    assert code_start >= 0 and code_end > code_start, "code block markers missing"
    skill_body = variant_section[code_start + len("```markdown\n"):code_end].strip()

    skill_dir = tmp_path / "skills" / "fixture-from-template"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: fixture-from-template\n"
        "description: Fixture skill assembled from the T11 template variant; T10 lint should accept it.\n"
        "credentialed: true\n"
        "primitive-class: credentialed-cli\n"
        "---\n\n" + skill_body + "\n",
        encoding="utf-8",
    )

    env = {**os.environ, "LINT_ROOT": str(tmp_path)}
    res = subprocess.run(
        ["bash", str(LINT_CRED_SKILLS)],
        cwd=str(REPO_ROOT), env=env,
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"lint refused the template-derived skill — drift between T11 "
        f"and T10:\nstdout={res.stdout}\nstderr={res.stderr}"
    )


def test_skill_passes_lint_agent_artifacts():
    """AC28: ``tools/lint-agent-artifacts.py`` accepts the new skill."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "lint-agent-artifacts.py")],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"lint-agent-artifacts refused the new skill:\n{res.stdout}\n{res.stderr}"
    )


def test_skill_passes_lint_agents_md():
    """AC28: ``tools/lint-agents-md.py`` resolves all internal links."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "lint-agents-md.py")],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"lint-agents-md refused:\n{res.stdout}\n{res.stderr}"
    )
