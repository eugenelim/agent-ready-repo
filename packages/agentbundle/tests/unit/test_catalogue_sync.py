"""Tests for ``agentbundle catalogue sync`` (spec: catalogue-sync-dry-run)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from agentbundle.cli import _build_parser
from agentbundle.commands import catalogue_sync
from agentbundle.https_catalogue import CatalogueArchiveResult

# Reused rather than copied — T4 introduces this helper and its first rows in
# test_catalogue_tooling_self_hosted_init.py; every later task's no-write case
# parametrises against the same walk, per plan.md § Construction tests.
from tests.unit.test_catalogue_tooling_self_hosted_init import walk_target_tree


def _make_source(root: Path, *, pack_version: str = "1.0.0") -> Path:
    """Create a minimal valid source catalogue tree at ``root``."""
    root.mkdir(parents=True)
    (root / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'display_name = "Upstream Catalogue"\n'
        'description = "A source catalogue for sync tests."\n',
        encoding="utf-8",
    )
    pack = root / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\n'
        'name = "alpha"\n'
        f'version = "{pack_version}"\n',
        encoding="utf-8",
    )
    (pack / "README.md").write_text("# Alpha\n", encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# AC-0001: fidelity token and pin values per source form
# ---------------------------------------------------------------------------

# STUB: AC-0001
def test_sync_names_fidelity_token_per_source_form(derived_tree, upstream, capsys):
    # The real parser, never a hand-rolled Namespace: a hand-rolled one carries
    # no parser defaults, so a missing default reads as a passing test.
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert "local-path" in capsys.readouterr().out


@pytest.mark.parametrize(
    "kind,fidelity_token,archive_sha256,source_revision",
    [
        ("local-path", "local-path", None, None),
        ("git-tls", "git-tls", None, None),
        ("archive", "digest-adopter-pinned", "a" * 64, None),
        ("catalogue", "digest-publisher-asserted", "b" * 64, "v1.2.3"),
    ],
)
def test_sync_names_fidelity_token_and_pin_per_source_form(
    derived_tree, upstream, tmp_path, monkeypatch, capsys,
    kind, fidelity_token, archive_sha256, source_revision,
):
    if kind == "local-path":
        source_uri = str(upstream)
    elif kind == "git-tls":
        source_uri = "git+https://github.com/example-owner/example-repo@main"
        monkeypatch.setattr(catalogue_sync, "resolve_catalogue", lambda uri: upstream)
    elif kind == "archive":
        source_uri = f"archive+https://example.com/a.tar.gz#sha256={archive_sha256}"
        extracted = tmp_path / "extracted-archive"
        shutil.copytree(upstream, extracted)
        monkeypatch.setattr(
            catalogue_sync,
            "fetch_catalogue_archive_with_provenance",
            lambda uri: CatalogueArchiveResult(
                path=extracted, artifact_uri=uri,
                archive_sha256=archive_sha256, source_revision=source_revision,
            ),
        )
    else:
        source_uri = "catalogue+https://example.com/channel.json"
        extracted = tmp_path / "extracted-catalogue"
        shutil.copytree(upstream, extracted)
        monkeypatch.setattr(
            catalogue_sync,
            "fetch_catalogue_archive_with_provenance",
            lambda uri: CatalogueArchiveResult(
                path=extracted, artifact_uri=uri,
                archive_sha256=archive_sha256, source_revision=source_revision,
            ),
        )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", source_uri, "--dry-run", "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["fidelity"] == fidelity_token
    assert doc["pin"]["archive_sha256"] == archive_sha256
    assert doc["pin"]["source_revision"] == source_revision

    if kind in ("archive", "catalogue"):
        assert not extracted.exists()


# ---------------------------------------------------------------------------
# AC-0002: the source is named only under attributed, on every channel,
# including refusals.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("attribution", ["white-label", "attributed"])
def test_sync_names_source_only_under_attributed(derived_tree, upstream, capsys, attribution):
    source_uri = str(upstream)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", source_uri,
         "--attribution", attribution, "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    if attribution == "attributed":
        assert source_uri in captured.out
    else:
        assert source_uri not in captured.out
        assert source_uri not in captured.err

    args_json = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", source_uri,
         "--attribution", attribution, "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args_json) == 0
    captured_json = capsys.readouterr()
    if attribution == "attributed":
        assert source_uri in captured_json.out
    else:
        assert source_uri not in captured_json.out
        assert source_uri not in captured_json.err


@pytest.mark.parametrize("attribution", ["white-label", "attributed"])
def test_sync_verification_refusal_never_leaks_source_outside_attributed(
    derived_tree, tmp_path, capsys, attribution
):
    """A source resolvable as a path but missing catalogue.toml raises
    ``ReplayError`` inside ``replay_derivation`` — the verification half of
    AC-0002's refusal set.
    """
    missing_source = str(tmp_path / "does-not-exist")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", missing_source,
         "--attribution", attribution, "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    captured = capsys.readouterr()
    if attribution == "attributed":
        assert missing_source in captured.out or missing_source in captured.err
    else:
        assert missing_source not in captured.out
        assert missing_source not in captured.err

    args_json = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", missing_source,
         "--attribution", attribution, "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args_json) == 3
    captured_json = capsys.readouterr()
    if attribution == "attributed":
        assert missing_source in captured_json.out
    else:
        assert missing_source not in captured_json.out
        assert missing_source not in captured_json.err


@pytest.mark.parametrize("attribution", ["white-label", "attributed"])
def test_sync_resolution_refusal_never_leaks_source_outside_attributed(
    derived_tree, capsys, attribution
):
    """``git+ssh://`` is refused by ``resolve_catalogue`` itself — the
    resolution half of AC-0002's refusal set.
    """
    source_uri = "git+ssh://git@example.com/example-owner/example-repo.git"

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", source_uri,
         "--attribution", attribution, "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    captured = capsys.readouterr()
    if attribution == "attributed":
        assert source_uri in captured.out or source_uri in captured.err
    else:
        assert source_uri not in captured.out
        assert source_uri not in captured.err


# ---------------------------------------------------------------------------
# AC-0003: the replayed modes come from flags and their defaults, never the
# recorded recipe. Driven through the whole command — the collect_fields seam
# T3 covers cannot express this violation, because _SelfHostRecipeInput
# carries no mode field.
# ---------------------------------------------------------------------------

# STUB: AC-0003 (T5's CLI-level case; T3 owns the collect_fields-seam case)
def test_sync_dry_run_replays_flag_modes_not_recorded_ones(derived_tree, upstream, capsys):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["recipe"].update(attribution="attributed", tooling="vendored", guides="none")
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    out = capsys.readouterr().out
    assert "white-label" in out
    assert "external" in out
    assert "selected" in out


# ---------------------------------------------------------------------------
# Target: explicit vs. omitted (defaults to the current directory).
# ---------------------------------------------------------------------------

def test_sync_target_is_explicit(derived_tree, upstream):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert args.target == str(derived_tree)


def test_sync_target_defaults_to_current_directory(derived_tree, upstream, monkeypatch, capsys):
    monkeypatch.chdir(derived_tree)
    args = _build_parser().parse_args(
        ["catalogue", "sync", "--source", str(upstream), "--dry-run"]
    )
    assert args.target == "."
    assert catalogue_sync.run(args) == 0


# ---------------------------------------------------------------------------
# The extracted directory is gone on the succeeding and each refusing path.
# ---------------------------------------------------------------------------

def test_sync_cleans_up_extracted_directory_on_success_and_on_refusal(
    derived_tree, upstream, tmp_path, monkeypatch
):
    ok_dir = tmp_path / "extracted-ok"
    shutil.copytree(upstream, ok_dir)
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(path=ok_dir, artifact_uri=uri),
    )
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json", "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0
    assert not ok_dir.exists()

    bad_dir = tmp_path / "extracted-bad"
    bad_dir.mkdir()  # no catalogue.toml -> ReplayError
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(path=bad_dir, artifact_uri=uri),
    )
    args2 = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json", "--dry-run"]
    )
    assert catalogue_sync.run(args2) == 3
    assert not bad_dir.exists()


# ---------------------------------------------------------------------------
# The whole-tree walk (spec AC-0015), reusing T4's helper rather than a copy.
# T5's rows: a dry-run success and a resolution refusal reached via sync's
# own dispatch, over-and-above T4's replay_derivation-level rows.
# ---------------------------------------------------------------------------

def _sync_dry_run_success_row(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0


def _sync_resolution_refusal_row(target: Path) -> None:
    missing = str(target.parent / "sync-tree-walk-missing-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", missing, "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3


# Registry T5 adds to; later tasks extend it further rather than copying it.
SYNC_TREE_WALK_CASES = {
    "sync-dry-run-success": _sync_dry_run_success_row,
    "sync-resolution-refusal": _sync_resolution_refusal_row,
}


@pytest.mark.parametrize("case", sorted(SYNC_TREE_WALK_CASES))
def test_sync_leaves_the_target_tree_unchanged(tmp_path, case):
    target = tmp_path / "target"
    target.mkdir()
    (target / "adopter-owned.txt").write_text("keep me\n", encoding="utf-8")
    before = walk_target_tree(target)

    SYNC_TREE_WALK_CASES[case](target)

    after = walk_target_tree(target)
    assert after == before
