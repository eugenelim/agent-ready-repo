"""T12: cross-consumer schema-migration parametrised tests.

Both ``agentbundle adapt`` (CLI) and ``agentbundle build self`` (self-host)
read ``.adapt-discovery.toml`` via the shared typed loader. This file
exercises the legacy-vs-canonical shape matrix against **both consumers**
in a single parametrised set, so a future drift in either stays caught.

Per spec AC8/AC9: legacy refusal stderr lines are exact, per consumer:

  CLI:        ``adapt: legacy [accepted] table; migrate to [markers]
              per docs/specs/adapt-to-project/spec.md``
  self-host:  ``self-host: legacy [adapt] table; migrate to [markers]
              per docs/specs/adapt-to-project/spec.md``
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agentbundle.build import self_host
from agentbundle.commands import adapt
from agentbundle.config import PackState, State, dump_state
from agentbundle.safety import sha256_bytes


def _seed_repo(root: Path) -> None:
    state = State()
    p = root / "AGENTS.md"
    p.write_text("x\n", encoding="utf-8")
    state.packs["core"] = PackState(
        installed_version="0.1.0",
        files={
            "AGENTS.md": {
                "sha": sha256_bytes(b"x\n"),
                "from-pack-version": "0.1.0",
            }
        },
    )
    (root / ".agentbundle-state.toml").write_text(
        dump_state(state), encoding="utf-8"
    )


def _run_cli(root: Path) -> int:
    return adapt.run(argparse.Namespace(root=str(root), values_from=None, ci=False))


def _run_self_host(root: Path) -> int:
    packs_dir = root / "packs"
    packs_dir.mkdir(exist_ok=True)
    return self_host.run_self_host(
        working_tree=root,
        packs_dir=packs_dir,
        dry_run=True,
        force=True,
        contract={"primitive": {}, "adapter": {"claude-code": {"projection": []}}},
    )


@pytest.mark.parametrize(
    "consumer,body,expected_first_line",
    [
        (
            "cli",
            '[accepted]\nowner = "x"\n',
            "adapt: legacy [accepted] table; migrate to [markers] per "
            "docs/specs/adapt-to-project/spec.md",
        ),
        (
            "self-host",
            '[adapt]\nproject-name = "x"\n',
            "self-host: legacy [adapt] table; migrate to [markers] per "
            "docs/specs/adapt-to-project/spec.md",
        ),
    ],
    ids=["cli-refuses-legacy-accepted", "self-host-refuses-legacy-adapt"],
)
def test_consumer_refuses_legacy_shape(
    consumer: str, body: str, expected_first_line: str, tmp_path, capsys
):
    """Each consumer refuses its respective legacy shape with the
    spec-mandated prefixed first stderr line."""
    _seed_repo(tmp_path)
    (tmp_path / ".adapt-discovery.toml").write_text(body, encoding="utf-8")

    if consumer == "cli":
        rc = _run_cli(tmp_path)
    else:
        rc = _run_self_host(tmp_path)
    assert rc != 0
    first = capsys.readouterr().err.splitlines()[0]
    assert first == expected_first_line


@pytest.mark.parametrize(
    "consumer",
    ["cli", "self-host"],
    ids=["cli-accepts-canonical", "self-host-accepts-canonical"],
)
def test_consumer_accepts_canonical_markers_shape(consumer: str, tmp_path, capsys):
    """Both consumers accept the canonical `[markers]` shape without
    a legacy-refusal line."""
    _seed_repo(tmp_path)
    (tmp_path / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n[markers]\nowner = "x"\n',
        encoding="utf-8",
    )
    if consumer == "cli":
        rc = _run_cli(tmp_path)
    else:
        rc = _run_self_host(tmp_path)
    # No legacy-prefix line on stderr.
    err = capsys.readouterr().err
    for line in err.splitlines():
        assert "legacy [accepted]" not in line
        assert "legacy [adapt]" not in line
    # CLI succeeds outright; self-host may fail downstream (no real
    # packs), but the discovery read must have passed.
    if consumer == "cli":
        assert rc == 0
