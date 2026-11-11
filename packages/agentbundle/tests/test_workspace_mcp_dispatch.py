"""The MCP `workspace_status` tool runs the packaged dispatch, and the dispatched item has two forms."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from agentbundle import workspace_mcp as mod
from agentbundle._data import dispatch as packaged_dispatch


class _FakeBridge:
    def get_fsm_state(self) -> dict:
        return {}

    def has_anchored_engine_state(self) -> bool:
        return False


def _spec(root: Path, slug: str, status: str, extra: str = "") -> None:
    spec_dir = root / "docs" / "specs" / slug
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(
        f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{extra}",
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(f"# Plan: {slug}\n", encoding="utf-8")


def _status(root: Path) -> dict[str, Any]:
    return mod._WorkspaceStatusTool(root, _FakeBridge()).call()


def _planted(root: Path) -> Path:
    """One ready spec, one active spec and one blocked spec, with no `workspace.toml`."""
    root.mkdir(parents=True)
    _spec(root, "ready-one", "Approved")
    _spec(root, "active-one", "Implementing")
    _spec(root, "blocked-one", "Approved", "- **Depends on:** spec:ready-one\n")
    return root


def _no_ini_slug(value: object) -> bool:
    if isinstance(value, dict):
        return "ini_slug" not in value and all(_no_ini_slug(v) for v in value.values())
    if isinstance(value, list):
        return all(_no_ini_slug(v) for v in value)
    return True


def test_lists_follow_the_packaged_dispatch_without_workspace_toml(tmp_path: Path) -> None:
    root = _planted(tmp_path / "repo")
    assert not (root / "workspace.toml").exists()

    result = _status(root)
    output = packaged_dispatch.dispatch(root)

    assert result["canonical"] == output
    assert result["shaping"] == []
    for key in ("ready", "active", "blocked"):
        assert [item["path"] for item in result[key]] == [i["path"] for i in output[key]]
        assert [item["slug"] for item in result[key]] == [i["slug"] for i in output[key]]
        assert [item["findings"] for item in result[key]] == [i["findings"] for i in output[key]]
    assert [i["slug"] for i in result["ready"]] == ["ready-one"]
    assert [i["slug"] for i in result["active"]] == ["active-one"]
    assert [i["slug"] for i in result["blocked"]] == ["blocked-one"]
    assert all(item["dispatchable"] for item in result["ready"])
    assert not any(item["dispatchable"] for item in result["blocked"] + result["active"])
    for item in result["ready"] + result["active"] + result["blocked"]:
        assert item["type"] == "work"
        assert item["dispatch_skill"] == "work-loop"
        assert item["required_pack"] == "core"
        assert item["has_gates"] is True
        assert "output_pattern" in item
    assert _no_ini_slug(result)


def test_entry_free_repository_yields_empty_lists(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    result = _status(root)

    assert result["ready"] == result["active"] == result["blocked"] == result["shaping"] == []
    assert result["canonical"] == packaged_dispatch.dispatch(root)


def test_unmigrated_repository_returns_the_refusal_output(tmp_path: Path) -> None:
    root = _planted(tmp_path / "repo")
    (root / "workspace.toml").write_text(
        '["ini-001".work]\nqueue = [{path = "docs/specs/ready-one/spec.md", kind = "spec",'
        ' source = {mode = "repo-origin"}, summary = "s", needs = []}]\n'
        "active = []\nshipped = []\n",
        encoding="utf-8",
    )

    result = _status(root)

    assert result["canonical"] == packaged_dispatch.dispatch(root)
    assert result["canonical"]["decision"]["action"] == "refuse"
    assert {f["code"] for f in result["canonical"]["findings"]} == {"unmigrated_workspace"}
    assert result["ready"] == result["active"] == result["blocked"] == []
    assert _no_ini_slug(result)


class _CraftedDispatch:
    """A stand-in dispatch whose output holds items the tool's filters must skip."""

    @staticmethod
    def dispatch(root: Path) -> dict[str, Any]:
        def item(path: str, slug: str) -> dict[str, Any]:
            return {"path": path, "slug": slug, "status": "Approved", "findings": []}

        return {
            "schema_version": 1,
            "ready": [
                item("docs/specs/good/spec.md", "good"),
                item("docs/specs/-bad/spec.md", "-bad"),
            ],
            "active": [],
            "blocked": [
                item("docs/product/briefs/not-a-spec.md", "not-a-spec"),
                item("docs/specs/also-good/spec.md", "also-good"),
            ],
            "findings": [],
            "decision": {"action": "ask", "path": None, "candidates": [], "findings": []},
        }


def test_filters_skip_unsafe_slugs_and_non_spec_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "_load_packaged_dispatch", lambda: _CraftedDispatch)

    result = _status(tmp_path)

    assert [i["slug"] for i in result["ready"]] == ["good"]
    assert [i["slug"] for i in result["blocked"]] == ["also-good"]
    assert result["canonical"]["schema_version"] == 1


def test_a_dispatch_failure_returns_the_failure_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> Any:
        raise RuntimeError("unavailable")

    monkeypatch.setattr(mod, "_load_packaged_dispatch", _boom)

    result = _status(tmp_path)

    assert result["ready"] == result["active"] == result["shaping"] == []
    assert result["canonical"]["findings"][0]["code"] == "configuration_mismatch"
    assert _no_ini_slug(result)


def test_the_tool_loads_dispatch_from_the_packaged_data_only() -> None:
    assert mod._load_packaged_dispatch() is packaged_dispatch
    assert Path(packaged_dispatch.__file__).parent.name == "_data"
    assert not hasattr(mod, "_load_workspace_status_engine")


# -- AC-0028: the dispatched item ---------------------------------------------------


def _tools(
    repo: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> Any:
    monkeypatch.delenv("WORKSPACE_MCP_SPEC_PATH", raising=False)
    monkeypatch.setenv("WORKSPACE_MCP_DISPATCHED_ITEM", value)
    return mod._GitTools(repo)


@pytest.mark.parametrize(
    ("value", "branch"),
    [
        ("shape:alpha", "shape/alpha"),
        ("ini-001/shape:alpha", "ini-001/shape/alpha"),
    ],
)
def test_both_forms_bind_a_branch_and_the_same_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str, branch: str
) -> None:
    tools = _tools(tmp_path, monkeypatch, value)
    reference = _tools(tmp_path, monkeypatch, "ini-001/shape:alpha")

    assert tools._expected_branch == branch
    assert tools._output_spec is not None
    assert tools._output_pattern == reference._output_pattern
    assert tools._output_spec == reference._output_spec
    assert tools._discovery_mode is False


@pytest.mark.parametrize(
    "value",
    [
        "spec:a/b",
        "shape:a/b",
        "shape:..",
        "shape:-bad",
        "shape:",
        ":alpha",
        "alpha",
        "unknown:alpha",
        "ini-001/unknown:alpha",
        "ini-001/shape:a/b",
        "ini-001/shape:-bad",
        "../shape:alpha",
        "ini-001/ /shape:alpha",
        "a/b/shape:alpha",
    ],
)
def test_malformed_unsafe_or_unknown_values_block_git_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    tools = _tools(tmp_path, monkeypatch, value)

    assert tools._expected_branch is None
    assert tools._output_spec is None
    assert tools._output_pattern is None
    assert tools._discovery_mode is True
    assert "error" in tools.git_branch({"name": "shape/alpha"})
    assert "error" in tools.git_commit({"message": "m"})


def test_branch_must_match_the_two_part_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _tools(tmp_path, monkeypatch, "shape:alpha")

    result = tools.git_branch({"name": "ini-001/shape/alpha"})

    assert "does not match the dispatched-item branch 'shape/alpha'" in result["error"]


# -- AC-0032: the texts -------------------------------------------------------------


def _tool_by_name(name: str) -> dict[str, Any]:
    tools = mod._StdioLoop.__new__(mod._StdioLoop)._build_tools_list()
    return next(tool for tool in tools if tool["name"] == name)


def test_server_texts_name_type_slug_and_no_ini_slug_field() -> None:
    rule5 = mod.DEFAULT_SESSION_INSTRUCTION.split("5. ", 1)[1].split("\n\n6. ", 1)[0]
    branch = _tool_by_name("git_branch")
    branch_texts = (
        branch["description"],
        branch["inputSchema"]["properties"]["name"]["description"],
    )
    for text in (rule5, *branch_texts):
        assert "<type>/<slug>" in text
        assert "ini_slug" not in text
    status = _tool_by_name("workspace_status")["description"]
    assert "ini_slug" not in status
    assert "shaping[] — always an empty list" in status
    assert "ini_slug" not in mod.DEFAULT_SESSION_INSTRUCTION
