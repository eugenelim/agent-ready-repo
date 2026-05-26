"""T9 (credential-broker-contract): ``add-credentialed-skill`` author skill —
the four per-broker template variants, frontmatter, and per-broker
Don't-block presence (spec § AC27).
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SEED_SKILL = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "add-credentialed-skill"
PROJECTED_SKILL = REPO_ROOT / ".claude" / "skills" / "add-credentialed-skill"
ASSETS = SEED_SKILL / "assets"

BROKER_IDS = ("env", "cli", "creds", "sso-cookie")


def test_seed_skill_exists():
    assert SEED_SKILL.is_dir()
    assert (SEED_SKILL / "SKILL.md").is_file()
    assert ASSETS.is_dir()


def test_projected_skill_matches_seed():
    """`make build-self` should keep seed and projected in sync."""
    assert PROJECTED_SKILL.is_dir()
    assert (PROJECTED_SKILL / "SKILL.md").is_file()
    seed_body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    projected_body = (PROJECTED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert seed_body == projected_body, "seed and projected diverged — rerun make build-self"


def test_skill_frontmatter_includes_required_triggers():
    """AC27: triggers listed in description."""
    body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
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


def test_four_broker_templates_exist():
    """AC27: per-broker templates ship as four labelled files."""
    for broker in BROKER_IDS:
        path = ASSETS / f"credentialed-skill-SKILL-{broker}.md"
        assert path.is_file(), f"template missing for broker {broker!r}: {path}"


def test_old_single_file_template_removed():
    """AC27: the per-primitive-class single file is gone — broker is the axis now."""
    old = ASSETS / "credentialed-skill-SKILL.md"
    assert not old.exists(), (
        "old single-file template still present; per RFC-0013 § 7 the four "
        "per-broker variants replace it"
    )


def test_each_template_has_security_rules_block():
    """AC27: every variant carries the verbatim section heading."""
    for broker in BROKER_IDS:
        body = (ASSETS / f"credentialed-skill-SKILL-{broker}.md").read_text(encoding="utf-8")
        assert "### Security rules (non-negotiable)" in body, (
            f"{broker} template missing Security rules section"
        )


def test_each_template_argv_ban_phrase():
    """AC27: every broker keeps the verbatim argv-ban phrasing."""
    for broker in BROKER_IDS:
        body = (ASSETS / f"credentialed-skill-SKILL-{broker}.md").read_text(encoding="utf-8")
        assert "Never** put" in body, f"{broker} template missing argv-ban phrase"
        # The five canonical flags from RFC-0006 § 4.
        for flag in ("--token", "--api-token", "--bearer", "--pat", "--password"):
            assert flag in body, f"{broker} template missing argv-ban flag {flag!r}"


def test_creds_template_carries_make_build_self_instruction():
    """RFC-0013 § 7: the `auth: creds` flow tells the author to run
    `make build-self` before running tests."""
    body = (ASSETS / "credentialed-skill-SKILL-creds.md").read_text(encoding="utf-8")
    assert "make build-self" in body, (
        "auth: creds template missing the verbatim make build-self instruction"
    )


def test_creds_template_imports_credentials_shim():
    """AC27 / AC25: the `auth: creds` template shows the sibling import shape."""
    body = (ASSETS / "credentialed-skill-SKILL-creds.md").read_text(encoding="utf-8")
    assert "from .credentials_shim import" in body, (
        "auth: creds template missing the sibling-shim import line"
    )


def test_sso_cookie_template_invokes_canonical_broker_path():
    """AC27 / AC25 / AC17: the `auth: sso-cookie` template subprocess-invokes
    the broker at the canonical Path.home() / .agentbundle / bin path."""
    body = (ASSETS / "credentialed-skill-SKILL-sso-cookie.md").read_text(encoding="utf-8")
    assert "Path.home()" in body
    assert ".agentbundle" in body
    assert "sso-broker.py" in body


def test_env_template_declares_namespace_and_keys():
    """RFC-0013 § 6: env-broker frontmatter requires namespace + keys."""
    body = (ASSETS / "credentialed-skill-SKILL-env.md").read_text(encoding="utf-8")
    assert "namespace:" in body
    assert "keys:" in body


def test_skill_body_walks_broker_first():
    """RFC-0013 § 7: the author picks the broker first."""
    body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    # The first numbered step talks about picking the broker.
    pick_broker_idx = body.find("1. **Pick the broker")
    pick_class_idx = body.find("2. **Pick the primitive class")
    assert pick_broker_idx > 0, "skill body does not start with 'Pick the broker'"
    assert pick_class_idx > pick_broker_idx, "primitive-class step must follow broker step"


def test_skill_body_names_all_four_broker_ids():
    """RFC-0013 § 7: the author flow enumerates env / cli / creds / sso-cookie."""
    body = (SEED_SKILL / "SKILL.md").read_text(encoding="utf-8")
    for broker in BROKER_IDS:
        assert f"`{broker}`" in body, f"author skill body does not name broker {broker!r}"


def test_skill_passes_lint_agent_artifacts():
    """AC27: ``tools/lint-agent-artifacts.py`` accepts the new skill."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "lint-agent-artifacts.py")],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"lint-agent-artifacts refused the new skill:\n{res.stdout}\n{res.stderr}"
    )


def test_skill_passes_lint_agents_md():
    """AC27: ``tools/lint-agents-md.py`` resolves all internal links."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "lint-agents-md.py")],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"lint-agents-md refused:\n{res.stdout}\n{res.stderr}"
    )
