from __future__ import annotations

import re

import pytest
from knowledge_test_support import PACK_ROOT, load_project_knowledge_module

SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "project-knowledge"
SKILL = SKILL_ROOT / "SKILL.md"


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_ac26_each_progressive_mode_has_a_disjoint_helper_surface() -> None:
    module = load_project_knowledge_module()
    assert module.helpers_for("capture") == {"capture_observation"}
    assert module.helpers_for("distill") == {
        "read_journal",
        "read_topic",
        "read_source",
        "write_knowledge",
    }
    assert module.helpers_for("enquire") == {
        "read_committed_map",
        "read_committed_topic",
        "read_freshness_source",
    }
    assert module.helper_registries_are_disjoint()
    assert "write" not in module.helpers_for("enquire")
    assert "read_journal" not in module.helpers_for("enquire")
    with pytest.raises(ValueError):
        module.call_helper("enquire", "write_knowledge")


def test_ac26_router_has_three_progressive_mode_references() -> None:
    text = _skill_text()
    for reference in (
        "references/capture-mode.md",
        "references/distill-mode.md",
        "references/enquire-mode.md",
    ):
        assert reference in text
        assert (SKILL_ROOT / reference).is_file()


def test_ac27_skill_metadata_declares_exact_informational_union() -> None:
    text = _skill_text()
    match = re.search(r"metadata:\n\s+boundaries:\s*\[(.*?)\]", text)
    assert match, "project-knowledge must declare metadata.boundaries"
    boundaries = [item.strip() for item in match.group(1).split(",")]
    assert boundaries == ["filesystem_read_untrusted", "filesystem_write"]


def test_ac29_router_does_not_expose_network_command_or_permission_capability() -> None:
    text = _skill_text().lower()
    forbidden = ("network", "credential", "authorization", "permission-management")
    for term in forbidden:
        assert term not in text
    module = load_project_knowledge_module()
    assert not (set(module.all_helpers()) & {"run_command", "fetch_url", "read_secret"})


def test_lock_token_contract_is_csprng_and_rejects_forged_or_reused_tokens() -> None:
    module = load_project_knowledge_module()
    first = module.new_lock_token()
    second = module.new_lock_token()
    assert first != second
    assert len(first) >= 64
    lock = module.LockTokenState(token=first)
    assert lock.release(first)
    assert not lock.release(first)
    assert not module.LockTokenState(token=first).release(second)
