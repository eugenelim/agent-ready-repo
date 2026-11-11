"""The MCP status tool blocks on `Depends on:` headers and refuses unmigrated `needs`."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "agentbundle" / "workspace_mcp.py"


def _load_module():
    """Load workspace_mcp as a module without executing main()."""
    spec = importlib.util.spec_from_file_location("agentbundle.workspace_mcp", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("agentbundle.workspace_mcp", mod)
    spec.loader.exec_module(mod)
    return mod


class _FakeBridge:
    def get_fsm_state(self):  # noqa: ANN201
        return {}

    def has_anchored_engine_state(self) -> bool:
        return False


def _edge_workspace(tmp_path: Path, *, header: bool) -> Path:
    """A queued spec waiting on an open spec, as a header edge or a `needs` entry."""
    tmp_path.mkdir(parents=True)
    if not header:
        (tmp_path / "workspace.toml").write_text(
            """\
["ini-001".work]
queue = [
  {path = "docs/specs/waiter/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "waits", needs = [{type = "local", kind = "spec", path = "docs/specs/target/spec.md"}]},
]
active = []
shipped = []
""",
            encoding="utf-8",
        )
    for slug, status, extra in (
        ("waiter", "Approved", "- **Depends on:** spec:target\n" if header else ""),
        ("target", "Approved", ""),
    ):
        spec_dir = tmp_path / "docs" / "specs" / slug
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{extra}",
            encoding="utf-8",
        )
        (spec_dir / "plan.md").write_text(f"# Plan: {slug}\n", encoding="utf-8")
    return tmp_path


def test_mcp_blocks_on_a_header_edge_and_refuses_a_workspace_entry(tmp_path: Path) -> None:
    """A `Depends on:` header blocks the waiting spec; a workspace entry is refused."""
    mod = _load_module()
    header = mod._WorkspaceStatusTool(
        _edge_workspace(tmp_path / "header", header=True), _FakeBridge()
    ).call()
    assert [item["slug"] for item in header["blocked"]] == ["waiter"]
    assert {f["code"] for f in header["blocked"][0]["findings"]} == {
        "unsatisfied_dependency"
    }
    entry = mod._WorkspaceStatusTool(
        _edge_workspace(tmp_path / "needs", header=False), _FakeBridge()
    ).call()
    assert entry["ready"] == entry["blocked"] == entry["active"] == []
    assert entry["canonical"]["decision"]["action"] == "refuse"
    assert {f["code"] for f in entry["canonical"]["findings"]} == {"unmigrated_workspace"}
