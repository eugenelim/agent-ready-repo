"""The `workspace_status` payload reports the layout-resolved output path.

`_LIFECYCLE_MANIFEST` carries each item type's output pattern under an
in-repository convention base (`docs/product`, `docs/design`). An adopter
overrides that base with `output_dir` in `agentbundle-layout.toml`, and
RFC-0096 § 4 — the governing order under ADR-0120 D1 — puts declared
configuration ahead of that convention.

The defect these tests pin: the payload emitted `manifest["output_pattern"]`
unresolved, so a configured adopter read the convention base on the status
surface and the configured base everywhere else. One process, two answers
about where an item's output goes.

The agreement test is the load-bearing one. Asserting only that the payload
contains the configured string would pass on a second, independently drifting
resolver; comparing the payload against `_GitTools._resolve_output_pattern` —
the function that scopes the actual commit — is what pins the two surfaces to
one answer. The two spell it differently on purpose (the payload publishes
repository-relative paths, the git tool resolves absolute), so the comparison
is by resolved location, not by string.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.workspace_mcp import _GitTools, _WorkspaceStatusTool


class _FakeBridge:
    def get_fsm_state(self) -> dict:
        return {}

    def has_anchored_engine_state(self) -> bool:
        return False


def _workspace(root: Path, *, slug: str, item_type: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "workspace.toml").write_text(
        f"""\
["ini-001"]
name = "Layout"
status = "active"
milestone = "M1"

["ini-001".work]
queue = []
active = []
shipped = []

["ini-001".shaping_queue]
active = []
backlog = [{{slug = "{slug}", type = "{item_type}", needs = []}}]
""",
        encoding="utf-8",
    )


def _set_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """`Path.home()` reads USERPROFILE on Windows and HOME on POSIX, so a test
    that sets only one silently keeps the autouse conftest sandbox on the other
    platform and never sees its own user-scope fixture."""
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


def _shaping_item(root: Path, slug: str) -> dict:
    result = _WorkspaceStatusTool(root, _FakeBridge()).call()
    matches = [item for item in result["shaping"] if item["slug"] == slug]
    assert len(matches) == 1, f"expected one shaping item for {slug}: {result['shaping']}"
    return matches[0]


def test_payload_reports_the_configured_base_not_the_convention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _workspace(repo, slug="alpha", item_type="shape")
    (repo / "agentbundle-layout.toml").write_text(
        '[product]\noutput_dir = "artifacts/product"\n', encoding="utf-8"
    )
    _set_home(monkeypatch, tmp_path / "nohome")

    item = _shaping_item(repo, "alpha")

    assert item["output_pattern"] == [
        "artifacts/product/intents/{slug}.md",
        "artifacts/product/shaping/{slug}/**",
    ]


def test_payload_and_git_tool_resolve_to_the_same_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _workspace(repo, slug="alpha", item_type="shape")
    (repo / "agentbundle-layout.toml").write_text(
        '[product]\noutput_dir = "artifacts/product"\n', encoding="utf-8"
    )
    _set_home(monkeypatch, tmp_path / "nohome")

    payload_patterns = _shaping_item(repo, "alpha")["output_pattern"]
    git_patterns = _GitTools(repo)._resolve_output_pattern("ini-001/shape:alpha")

    assert git_patterns is not None
    assert [
        (repo / pattern.format(slug="alpha")).resolve() for pattern in payload_patterns
    ] == [Path(pattern).resolve() for pattern in git_patterns]


def test_payload_keeps_the_convention_base_when_nothing_is_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _workspace(repo, slug="alpha", item_type="shape")
    _set_home(monkeypatch, tmp_path / "nohome")

    item = _shaping_item(repo, "alpha")

    assert item["output_pattern"] == [
        "docs/product/intents/{slug}.md",
        "docs/product/shaping/{slug}/**",
    ]


def test_payload_withholds_a_base_outside_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A user-scope value must be absolute, so a personal vault resolves outside
    the repository. `git_commit` matches only paths `git status` reports, all of
    them repository-relative, so no glob in this payload can name that vault —
    and `_public_canonical_path` refuses to publish an absolute path at all.
    The item stays listed with no pattern, and the adopter is told why.
    """
    repo = tmp_path / "repo"
    _workspace(repo, slug="beta", item_type="research")
    vault = tmp_path / "vault" / "research"
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
        f'[research]\noutput_dir = "{vault}"\n', encoding="utf-8"
    )
    _set_home(monkeypatch, home)

    item = _shaping_item(repo, "beta")

    assert item["output_pattern"] is None
    assert str(vault) not in repr(item), "an absolute host path must not reach the payload"
    assert "outside the repository" in capsys.readouterr().err
