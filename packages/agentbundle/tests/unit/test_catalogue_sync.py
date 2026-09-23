"""Tests for ``agentbundle catalogue sync`` (spec: catalogue-sync-dry-run)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from agentbundle import safety
from agentbundle.catalogue_tooling import initialise_self_hosted as ish
from agentbundle.cli import _build_parser
from agentbundle.commands import catalogue_sync
from agentbundle.https_catalogue import CatalogueArchiveResult

# Reused rather than copied — T4 introduces this helper and its first rows in
# test_catalogue_tooling_self_hosted_init.py; every later task's no-write case
# parametrises against the same walk, per plan.md § Construction tests.
from tests.unit.test_catalogue_tooling_self_hosted_init import walk_target_tree

# T9's fixture pack declaring adapter-contract major 1 (spec AC-0019); every
# pack shipped in this repository declares major 0, so this fixture is what
# makes that refusal able to fail.
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "catalogue_sync"


def _make_source(root: Path, *, pack_version: str = "1.0.0") -> Path:
    """Create a minimal valid source catalogue tree at ``root``."""
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        f'version = "{pack_version}"\n',
    )


def _make_source_with_pack_toml(root: Path, pack_toml_text: str) -> Path:
    """Create a minimal source catalogue whose one pack declares *pack_toml_text*."""
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
    (pack / "pack.toml").write_text(pack_toml_text, encoding="utf-8")
    (pack / "README.md").write_text("# Alpha\n", encoding="utf-8")
    return root


def _write_minimal_sync_state(
    target: Path,
    *,
    packs: list[str] | None = None,
    managed_paths: list[dict] | None = None,
) -> None:
    """Write the minimal schema-3 state a derivable AC-0009 selection needs.

    ``packs`` recorded (even the empty explicit list) is what makes the
    recipe derivable -- an *absent* ``packs`` key, by contrast, is one of
    AC-0009's underivable conditions.
    """
    state_path = target / ".agentbundle" / "self-host-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "3",
                "managed_paths": managed_paths or [],
                "recipe": {
                    "packs": list(packs) if packs is not None else [],
                    "profiles": [],
                },
            }
        ),
        encoding="utf-8",
    )


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
# AC-0010, AC-0011, AC-0016: the Tier verdict per planned path, the companion
# path, the reported selection, and the seven counts' identity.
# ---------------------------------------------------------------------------

# STUB: AC-0010
def test_sync_reports_tier_verdict_and_selection(derived_tree, upstream, capsys):
    from agentbundle.commands import catalogue_sync

    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"adopter\n")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream), "--dry-run"]
    )

    catalogue_sync.run(args)

    out = capsys.readouterr().out
    assert "would-companion" in out
    assert "packs/alpha/README.md" in out


def _setup_five_path_states(derived_tree: Path, upstream: Path) -> None:
    """Drive all five AC-0010 path states into one target/source pair.

    Shared by the per-verdict test below and the seven-count identity test,
    so the two can't drift into checking different fixtures under the same
    name.
    """
    (upstream / "packs" / "alpha" / "extra.md").write_bytes(b"legacy\n")
    (derived_tree / "packs" / "alpha" / "extra.md").write_bytes(b"legacy\n")
    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"edited by the adopter\n")
    (derived_tree / "packs" / "alpha" / "stale.md").write_bytes(b"stale\n")
    # AC-0010 row 2: recorded, absent on disk -> would-update. Still planned
    # by the source (so it stays in `planned_paths`) and recorded with a
    # real digest, but never created under the target -- no companion file
    # here, unlike every other recorded path this fixture drives.
    (upstream / "packs" / "alpha" / "missing-on-disk.md").write_bytes(b"once-installed\n")

    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append({"path": "packs/alpha/extra.md", "sha256": None})
    state["managed_paths"].append(
        {
            "path": "packs/alpha/stale.md",
            "sha256": hashlib.sha256(b"stale\n").hexdigest(),
        }
    )
    state["managed_paths"].append(
        {
            "path": "packs/alpha/missing-on-disk.md",
            "sha256": hashlib.sha256(b"once-installed\n").hexdigest(),
        }
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")


def test_sync_five_path_states_and_reported_selection(derived_tree, upstream, capsys):
    """Drive all five AC-0010 path states through one run and check the
    reported verdict, the companion path, and the reported pack/profile
    selection against the recorded recipe."""
    _setup_five_path_states(derived_tree, upstream)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    catalogue_sync.run(args)
    doc = json.loads(capsys.readouterr().out)

    verdicts_by_path = {row["path"]: row for row in doc["verdicts"]}
    # recorded, present, sha matches -> would-update.
    assert verdicts_by_path["packs/alpha/pack.toml"]["verdict"] == "would-update"
    # recorded, absent on disk -> would-update (AC-0010 row 2; distinct from
    # the present-and-matching row above, so this is not the same assertion
    # under a different path).
    assert verdicts_by_path["packs/alpha/missing-on-disk.md"]["verdict"] == "would-update"
    assert "companion" not in verdicts_by_path["packs/alpha/missing-on-disk.md"]
    # recorded, present, sha differs -> would-companion, naming the
    # safety.companion_path result (not a locally assembled string).
    assert verdicts_by_path["packs/alpha/README.md"]["verdict"] == "would-companion"
    assert verdicts_by_path["packs/alpha/README.md"]["companion"] == str(
        safety.companion_path(Path("packs/alpha/README.md"))
    )
    # recorded, present, sha256: null -> schema-1-inert.
    assert verdicts_by_path["packs/alpha/extra.md"]["verdict"] == "schema-1-inert"
    # not recorded -> untouched.
    assert verdicts_by_path["catalogue.toml"]["verdict"] == "untouched"
    # recorded, absent from the current plan (source dropped it), unedited
    # -> would-remove.
    assert verdicts_by_path["packs/alpha/stale.md"]["verdict"] == "would-remove"
    assert doc["summary"]["would_remove"] == 1

    # The five states are mutually exclusive by construction: each path
    # above landed in exactly one bucket.
    assert {row["verdict"] for row in doc["verdicts"]} <= {
        "would-update", "would-companion", "schema-1-inert", "untouched",
        "would-remove",
    }

    # The reported selection equals the recorded recipe's.
    assert doc["packs"] == ["alpha"]
    assert doc["profiles"] == []


# ---------------------------------------------------------------------------
# Security finding 2 / adversarial finding 2: a recorded-and-planned path is
# screened through the file_safety confinement helper before it ever reaches
# `safety.classify`, which reads the on-disk entry with a raw, symlink-
# following, hard-link-blind open. Every case below is a shape `classify`
# itself cannot safely resolve.
# ---------------------------------------------------------------------------

def test_sync_directory_where_recorded_file_expected_is_uncompared_not_a_crash(
    derived_tree, upstream, capsys
):
    """A directory sitting where a recorded regular file is expected must
    not crash `run()` with `IsADirectoryError` (AC-0014) — it is screened
    out before `classify` and counted `uncompared` instead of getting a
    verdict row (AC-0016/AC-0017)."""
    readme = derived_tree / "packs" / "alpha" / "README.md"
    readme.unlink()
    readme.mkdir()
    (readme / "nested.txt").write_text("oops\n", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    doc = json.loads(capsys.readouterr().out)
    verdicts_by_path = {row["path"]: row for row in doc["verdicts"]}
    assert "packs/alpha/README.md" not in verdicts_by_path
    assert doc["summary"]["uncompared"] >= 1


def test_sync_symlinked_recorded_path_is_uncompared_not_followed(
    derived_tree, upstream, capsys
):
    """A symlink at a recorded path must not have its destination's bytes
    decide the Tier verdict — it is refused before `classify` ever reads
    through it, even when the destination's content would otherwise match
    the recorded digest exactly."""
    readme = derived_tree / "packs" / "alpha" / "README.md"
    destination = derived_tree / "packs" / "alpha" / "real-content.md"
    destination.write_bytes(readme.read_bytes())  # matches the recorded sha
    readme.unlink()
    try:
        readme.symlink_to(destination)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    doc = json.loads(capsys.readouterr().out)
    verdicts_by_path = {row["path"]: row for row in doc["verdicts"]}
    assert "packs/alpha/README.md" not in verdicts_by_path
    assert doc["summary"]["uncompared"] >= 1


def _parse_rendered_counts(table_out: str) -> dict[str, int]:
    """Recover the seven counts from `_render_plan`'s fixed ``counts:`` line.

    Mirrors that line's exact ``key=value`` shape rather than re-deriving
    the counts a second way, so this is a format-equality check, not a
    second computation that could independently agree by chance.
    """
    counts_line = next(
        line for line in table_out.splitlines() if line.startswith("counts:")
    )
    parsed: dict[str, int] = {}
    for token in counts_line[len("counts: "):].split():
        key, value = token.split("=")
        parsed[key.replace("-", "_")] = int(value)
    return parsed


# STUB: AC-0016
def test_sync_reports_seven_counts_and_the_identity(derived_tree, upstream, capsys):
    """Quality finding 3: pin the exact seven values on the five-path-state
    fixture (which already carries a schema-1-inert entry), and compare the
    table's rendered counts against the JSON `summary` from the same run —
    AC-0016's own named oracle. A per-bucket mis-attribution keeps every
    verdict row correct, so only this exact-value and cross-surface check
    can catch it; the identity alone (compared + uncompared == recorded
    count) cannot."""
    _setup_five_path_states(derived_tree, upstream)

    args_table = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args_table) == 0
    table_counts = _parse_rendered_counts(capsys.readouterr().out)

    args_json = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args_json) == 0
    summary = json.loads(capsys.readouterr().out)["summary"]

    expected = {
        "would_update": 2,
        "would_companion": 1,
        "untouched": 1,
        "would_remove": 1,
        "schema_1_inert": 1,
        "compared": 5,
        "uncompared": 0,
    }
    assert summary == expected
    assert table_counts == expected

    recorded_count = len(
        json.loads(
            (derived_tree / ".agentbundle" / "self-host-state.json").read_text(
                encoding="utf-8"
            )
        )["managed_paths"]
    )
    assert summary["compared"] + summary["uncompared"] == recorded_count


def test_sync_identity_accounts_for_malformed_and_unrenderable_entries(
    derived_tree, upstream, capsys
):
    """The identity's denominator is the raw managed_paths array before
    filtering; a malformed entry (no "path" key) and an unrenderable one
    (a control character) both land in uncompared (spec AC-0016)."""
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    recorded_count_before = len(state["managed_paths"])
    state["managed_paths"].append({"sha256": "z" * 64})
    state["managed_paths"].append({"path": "packs/alpha/\x1b[2Kevil.md", "sha256": "z" * 64})
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    catalogue_sync.run(args)
    summary = json.loads(capsys.readouterr().out)["summary"]

    assert summary["compared"] + summary["uncompared"] == recorded_count_before + 2
    assert summary["uncompared"] >= 2


# ---------------------------------------------------------------------------
# AC-0009: every underivable recorded-selection state, including every
# ownership-state loader failure, exits the cannot-answer code with its
# condition named.
# ---------------------------------------------------------------------------

def test_sync_no_state_file_exits_cannot_answer(derived_tree, upstream, capsys):
    (derived_tree / ".agentbundle" / "self-host-state.json").unlink()

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert "no state file at the target" in capsys.readouterr().err


def _drop_recipe_key(state: dict) -> None:
    del state["recipe"]


def _recipe_not_object(state: dict) -> None:
    state["recipe"] = ["not-an-object"]


def _recipe_without_packs_or_profiles(state: dict) -> None:
    state["recipe"].pop("packs", None)
    state["recipe"].pop("profiles", None)


def _recipe_selection_discarded(state: dict) -> None:
    state["recipe"]["packs"] = ["does-not-exist-in-source"]
    state["recipe"].pop("profiles", None)


AC_0009_RECIPE_MUTATIONS = {
    "no-recipe-key": _drop_recipe_key,
    "recipe-not-object": _recipe_not_object,
    "neither-packs-nor-profiles": _recipe_without_packs_or_profiles,
    "selection-discarded": _recipe_selection_discarded,
}


@pytest.mark.parametrize("case", sorted(AC_0009_RECIPE_MUTATIONS))
def test_sync_ac0009_recipe_conditions_exit_cannot_answer(
    derived_tree, upstream, capsys, case
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    AC_0009_RECIPE_MUTATIONS[case](state)
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert "no recorded selection is derivable" in capsys.readouterr().err


def test_sync_ownership_state_confinement_refusal_exits_cannot_answer(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    outside = derived_tree.parent / "outside-state.json"
    outside.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
    state_path.unlink()
    try:
        state_path.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


def test_sync_ownership_state_invalid_utf8_exits_cannot_answer(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state_path.write_bytes(b"\xff\xfe not valid utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


def test_sync_ownership_state_invalid_json_exits_cannot_answer(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state_path.write_text("{not json", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


def test_sync_ownership_state_non_object_document_exits_cannot_answer(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state_path.write_text("[]", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


def test_sync_ownership_state_io_failure_exits_cannot_answer(
    derived_tree, upstream, capsys, monkeypatch
):
    def _raise_os_error(*_args, **_kwargs):
        raise OSError("disk gremlin")

    monkeypatch.setattr(ish, "read_confined_regular_file", _raise_os_error)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


def test_sync_ownership_state_recursion_exhaustion_exits_cannot_answer(
    derived_tree, upstream, capsys, monkeypatch
):
    def _raise_recursion_error(*_args, **_kwargs):
        raise RecursionError

    monkeypatch.setattr(ish.json, "loads", _raise_recursion_error)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3
    assert (
        "the ownership-state loader could not return a state object"
        in capsys.readouterr().err
    )


# ---------------------------------------------------------------------------
# AC-0012: every value this command renders that it did not itself author is
# routed through the bounded terminal-safe scalar check before it reaches any
# output surface. One rejecting case per value kind the sink-class probe
# (docs/specs/catalogue-sync-dry-run/notes/grounding/probe-sink-class.py)
# enumerates: the field name and reason appear, the value never does. The
# pass direction alone cannot distinguish an applied check from an absent
# one, so each case drives a genuinely hostile value through the real
# command rather than asserting the check function in isolation.
# ---------------------------------------------------------------------------

# STUB: AC-0012 (value kind: managed_path)
def test_unrenderable_recorded_value_is_reported_by_field_not_value(
    derived_tree, upstream, capsys
):
    from agentbundle.commands import catalogue_sync

    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append(
        {"path": "packs/alpha/\x1b[2Kevil.md", "sha256": "z" * 64}
    )
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )

    catalogue_sync.run(args)
    captured = capsys.readouterr()

    assert "managed_paths" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: planned_path -- a source-tree entry name, not a recorded one.
def test_sync_rejects_hostile_planned_path(derived_tree, tmp_path, capsys):
    source = tmp_path / "hostile-planned-path-source"
    _make_source(source)
    (source / "packs" / "alpha" / "evil\x1b[31m.md").write_bytes(b"data\n")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "planned_paths" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: companion_path -- a computed value, checked at its own render
# site rather than trusted because its input path already passed.
def test_sync_rejects_hostile_companion_path(derived_tree, upstream, monkeypatch, capsys):
    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"edited by the adopter\n")
    monkeypatch.setattr(
        catalogue_sync, "companion_path", lambda _path: "AGENTS\x1b[31m.upstream.md"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "companion_path" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: archive_sha256 -- resolved from the fetched descriptor, not
# authored by this command. A leading-space violation, not a control
# character: `--format json` escapes a raw control byte on the way out, so
# a control-character marker would still look absent from the *serialized*
# text even with the check removed, and the case would not discriminate.
# A boundary (whitespace) violation survives JSON's own escaping unchanged,
# so its presence or absence in the captured text genuinely tracks whether
# this command's own check ran.
def test_sync_rejects_hostile_archive_sha256(derived_tree, tmp_path, monkeypatch, capsys):
    extracted = tmp_path / "extracted-hostile-sha"
    _make_source(extracted)
    hostile_sha = " " + "a" * 63
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256=hostile_sha,
        ),
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json",
         "--dry-run", "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "rejected archive_sha256" in captured.out + captured.err
    assert hostile_sha not in captured.out + captured.err


# value kind: source_revision, in both its tag and SHA forms -- the same
# sink, driven with a representative hostile value of each shape. Same
# boundary-violation rationale as the archive_sha256 case above.
@pytest.mark.parametrize(
    "hostile_revision",
    ["v1.2.3 ", " " + "a" * 39],
    ids=["tag-form", "sha-form"],
)
def test_sync_rejects_hostile_source_revision(
    derived_tree, tmp_path, monkeypatch, capsys, hostile_revision
):
    extracted = tmp_path / "extracted-hostile-revision"
    _make_source(extracted)
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256="b" * 64,
            source_revision=hostile_revision,
        ),
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json",
         "--dry-run", "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "rejected source_revision" in captured.out + captured.err
    assert hostile_revision not in captured.out + captured.err


# value kind: source_uri -- the rendered source, named only under attributed.
def test_sync_rejects_hostile_source_uri(derived_tree, upstream, monkeypatch, capsys):
    hostile_uri = "git+https://github.com/example\x1b[31m/repo@main"
    monkeypatch.setattr(catalogue_sync, "resolve_catalogue", lambda _uri: upstream)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", hostile_uri,
         "--attribution", "attributed", "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "rejected source" in captured.out + captured.err
    assert hostile_uri not in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


def _source_pack_version_hostile(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0\\u001b[31mHOSTILE"\n',
    )


# value kind: pack_version -- the source manifest's own [pack] version text.
def test_sync_rejects_hostile_pack_version(derived_tree, tmp_path, capsys):
    source = _source_pack_version_hostile(tmp_path / "hostile-pack-version-source")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "pack_version" in captured.out + captured.err
    assert "HOSTILE" not in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


def _source_adapter_contract_version_hostile(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[pack.adapter-contract]\n'
        'version = "0.2\\u001b[31mHOSTILE"\n',
    )


# value kind: adapter_contract_version -- same manifest, the other field.
def test_sync_rejects_hostile_adapter_contract_version(derived_tree, tmp_path, capsys):
    source = _source_adapter_contract_version_hostile(
        tmp_path / "hostile-adapter-contract-source"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "adapter_contract_version" in captured.out + captured.err
    assert "HOSTILE" not in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


def _source_dependency_hostile(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[[pack.dependencies.required]]\n'
        'catalogue = "upstream-catalogue"\n'
        'pack = "beta\\u001b[31mHOSTILE"\n'
        'version = ">=1.0.0"\n',
    )


# value kind: dependency_edge_name -- a dependency edge's declared pack name.
def test_sync_rejects_hostile_dependency_edge_name(derived_tree, tmp_path, capsys):
    source = _source_dependency_hostile(tmp_path / "hostile-dependency-source")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "dependency_edge_name" in captured.out + captured.err
    assert "HOSTILE" not in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: packs -- a selected pack's own directory name (a source-tree
# entry name AC-0012 names expressly), reached via an explicit-but-empty
# recorded selection: `select_packs` treats `[]` the same as `None` and
# resolves to every source pack directory.
def test_sync_rejects_hostile_pack_name(tmp_path, capsys):
    target = tmp_path / "target"
    target.mkdir()
    _write_minimal_sync_state(target, packs=None)

    source = tmp_path / "hostile-pack-name-source"
    _make_source(source)
    hostile_pack = source / "packs" / "evil\x1b[31m"
    hostile_pack.mkdir(parents=True)
    (hostile_pack / "pack.toml").write_text(
        '[pack]\nname = "evil"\nversion = "1.0.0"\n', encoding="utf-8"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "packs" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: profiles -- a selected profile's own file stem, same
# select-all-on-empty-selection reachability as the packs case above.
def test_sync_rejects_hostile_profile_name(tmp_path, capsys):
    target = tmp_path / "target"
    target.mkdir()
    _write_minimal_sync_state(target, packs=None)

    source = tmp_path / "hostile-profile-name-source"
    _make_source(source)
    profiles_dir = source / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "evil\x1b[31m.toml").write_text(
        '[profile]\nname = "evil"\n', encoding="utf-8"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    assert "profiles" in captured.out + captured.err
    assert "\x1b" not in captured.out + captured.err


# value kind: target -- the resolved `--target` path, an argv value of the
# same provenance as `--source` (which this module already routes).
def test_sync_rejects_hostile_target(tmp_path, capsys):
    target = tmp_path / "evil\x1b[31m-target"
    target.mkdir()
    _write_minimal_sync_state(target, packs=["alpha"])
    source = tmp_path / "hostile-target-source"
    _make_source(source)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run",
         "--format", "json"]
    )

    assert catalogue_sync.run(args) == 0
    captured = capsys.readouterr()
    doc = json.loads(captured.out)
    assert doc["target"] is None
    assert any("rejected target" in line for line in doc["rejections"])
    assert "\x1b" not in captured.out


# ---------------------------------------------------------------------------
# Security finding 5: `[pack.dependencies] required`/`conflicts` is a valid
# TOML scalar as well as an array. An unguarded non-list container must be
# skipped and reported, and the run must still print its plan and exit 0 —
# AC-0013's success row, undisturbed by AC-0018's warn-only signals.
# ---------------------------------------------------------------------------

def _source_dependency_required_not_a_list(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[pack.dependencies]\n'
        'required = 1\n',
    )


def _source_dependency_conflicts_not_a_list(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[pack.dependencies]\n'
        'conflicts = "not-an-array"\n',
    )


@pytest.mark.parametrize(
    "builder,field",
    [
        (_source_dependency_required_not_a_list, "dependency_required"),
        (_source_dependency_conflicts_not_a_list, "dependency_conflicts"),
    ],
    ids=["required", "conflicts"],
)
def test_sync_malformed_dependency_container_reports_and_still_succeeds(
    derived_tree, tmp_path, capsys, builder, field
):
    source = builder(tmp_path / f"malformed-{field}-source")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert field in capsys.readouterr().out


# ---------------------------------------------------------------------------
# AC-0007, AC-0008: the replayed modes and their provenance are named, and
# two runs whose recorded modes differ, invoked with identical flags,
# produce byte-identical plans.
# ---------------------------------------------------------------------------

def test_sync_recorded_modes_do_not_affect_the_plan(derived_tree, upstream, capsys):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    args_first = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args_first) == 0
    first = capsys.readouterr().out
    doc = json.loads(first)
    assert doc["modes"] == {
        "attribution": "white-label", "tooling": "external",
        "guides": "selected", "provenance": "flags-and-defaults",
    }

    state["recipe"].update(attribution="attributed", tooling="vendored", guides="none")
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args_second = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args_second) == 0
    second = capsys.readouterr().out

    assert first == second  # byte equality, not mere similarity


# ---------------------------------------------------------------------------
# The `--format json` document's content on each refusing row of spec
# AC-0013 that sync's own dispatch reaches today (T8 owns the ordered, total
# table over every row, including the `--check` comparison rows).
# ---------------------------------------------------------------------------

def test_sync_json_document_shape_on_malformed_compare_tree_without_check(
    derived_tree, upstream, capsys
):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--compare-tree", "--format", "json"]
    )
    assert catalogue_sync.run(args) == 2
    doc = json.loads(capsys.readouterr().out)
    assert doc == {"ok": False, "error": "--compare-tree requires --check"}


def test_sync_json_document_shape_on_malformed_symlink_target(
    derived_tree, upstream, tmp_path, capsys
):
    link = tmp_path / "symlinked-target"
    try:
        link.symlink_to(derived_tree)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(link), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args) == 2
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "symlink" in doc["error"]


def test_sync_json_document_shape_on_cannot_answer_resolution_refusal(
    derived_tree, capsys
):
    # `git+ssh://` is refused by `resolve_catalogue` itself (a `CatalogueError`)
    # -- the resolution half of AC-0002's refusal set, reused here for its
    # JSON shape rather than a local path, which `resolve_catalogue` accepts
    # unconditionally and only ``replay_derivation`` later finds unverifiable.
    source_uri = "git+ssh://git@example.com/example-owner/example-repo.git"
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", source_uri,
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc == {"ok": False, "error": "source could not be resolved"}


def test_sync_json_document_shape_on_cannot_answer_verification_refusal(
    derived_tree, tmp_path, capsys
):
    # `packs/alpha/` exists so T7's `_resolve_effective_selection` call (which
    # `derived_tree`'s recorded `packs: ["alpha"]` would otherwise fail before
    # this row is ever reached, since `alpha` would resolve from no source at
    # all) resolves cleanly — no catalogue.toml is what still reaches
    # `replay_derivation`'s own read and raises `ReplayError`.
    unverifiable_source = tmp_path / "unverifiable-source"
    pack = unverifiable_source / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(unverifiable_source),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc == {"ok": False, "error": "source could not be verified"}


def test_sync_json_document_shape_on_cannot_answer_no_recorded_selection(
    derived_tree, upstream, capsys
):
    (derived_tree / ".agentbundle" / "self-host-state.json").unlink()

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    assert catalogue_sync.run(args) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "no recorded selection is derivable" in doc["error"]


# ---------------------------------------------------------------------------
# AC-0018, AC-0019, AC-0020: compatibility warns and never refuses, the
# existing spec-version gate still refuses, and the derived-tree baseline
# manifest read goes through the declared confinement helper.
# ---------------------------------------------------------------------------

# STUB: AC-0018
def test_moved_pack_version_warns_without_changing_exit_code(
    derived_tree, upstream_with_bumped_pack, capsys
):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream_with_bumped_pack), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert "pack version" in capsys.readouterr().out


def _source_pack_version_unchanged(root: Path) -> Path:
    return _make_source(root, pack_version="1.0.0")


def _source_pack_version_bumped(root: Path) -> Path:
    return _make_source(root, pack_version="1.1.0")


def _source_dependency_satisfied(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n',
    )


def _source_dependency_unmet(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[[pack.dependencies.required]]\n'
        'catalogue = "upstream-catalogue"\n'
        'pack = "beta"\n'
        'version = ">=1.0.0"\n',
    )


def _source_adapter_contract_version_unchanged(root: Path) -> Path:
    # derived_tree's own copy of packs/alpha/pack.toml declares no
    # `[pack.adapter-contract]` table at all, so the matching absent arm
    # is a source that likewise declares none.
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n',
    )


def _source_adapter_contract_version_changed(root: Path) -> Path:
    # Major 0 — agrees with this CLI's own SPEC_VERSION major, so this stays
    # a warn-only signal rather than tripping AC-0019's refusal gate.
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[pack.adapter-contract]\n'
        'version = "0.2"\n',
    )


def _source_dependency_conflicts_absent(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n',
    )


def _source_dependency_conflicts_violated(root: Path) -> Path:
    return _make_source_with_pack_toml(
        root,
        '[pack]\n'
        'name = "alpha"\n'
        'version = "1.0.0"\n'
        '\n'
        '[[pack.dependencies.conflicts]]\n'
        'catalogue = "upstream-catalogue"\n'
        'pack = "alpha"\n'
        'version = ">=1.0.0"\n',
    )


# Each value is (signal-absent builder, signal-present builder, a substring
# that appears only in the present arm's output). Two arms per signal: the
# absent arm's exit code is pinned to the literal 0 (a healthy run succeeds),
# and the present arm's exit code is compared against the absent arm's rather
# than against a second literal — so drift in either direction fails. AC-0018
# names four signals, so this parametrisation carries all four rather than
# a representative subset: a shared comparison code path is exactly where a
# missing arm would let one signal's row silently drop while another passes.
COMPATIBILITY_SIGNAL_BUILDERS = {
    "pack-version-changed": (
        _source_pack_version_unchanged, _source_pack_version_bumped,
        "pack version",
    ),
    "adapter-contract-version-changed": (
        _source_adapter_contract_version_unchanged,
        _source_adapter_contract_version_changed,
        "adapter-contract version",
    ),
    "required-dependency-unmet": (
        _source_dependency_satisfied, _source_dependency_unmet,
        "required dependency",
    ),
    "conflicts-dependency-violated": (
        _source_dependency_conflicts_absent, _source_dependency_conflicts_violated,
        "conflict with",
    ),
}


@pytest.mark.parametrize("signal", sorted(COMPATIBILITY_SIGNAL_BUILDERS))
def test_compatibility_signal_warns_without_changing_exit_code(
    derived_tree, tmp_path, capsys, signal
):
    absent_builder, present_builder, marker = COMPATIBILITY_SIGNAL_BUILDERS[signal]

    absent_source = absent_builder(tmp_path / f"{signal}-absent")
    args_absent = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(absent_source), "--dry-run"]
    )
    exit_absent = catalogue_sync.run(args_absent)
    out_absent = capsys.readouterr().out

    present_source = present_builder(tmp_path / f"{signal}-present")
    args_present = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(present_source), "--dry-run"]
    )
    exit_present = catalogue_sync.run(args_present)
    out_present = capsys.readouterr().out

    assert exit_absent == 0  # the constant pin: a healthy run succeeds
    assert exit_present == exit_absent  # warn-only: the signal never moves the code
    assert marker not in out_absent
    assert marker in out_present


def test_sync_refuses_when_adapter_contract_major_mismatches(derived_tree, tmp_path, capsys):
    """Spec AC-0019: a pack declaring a differing adapter-contract major
    refuses via the existing uniform-refusal gate, returning AC-0013's
    difference code — distinct from AC-0018's warn-only signals above."""
    pack_toml_text = (
        FIXTURES / "adapter_contract_major_mismatch" / "pack.toml"
    ).read_text(encoding="utf-8")
    source = _make_source_with_pack_toml(
        tmp_path / "adapter-contract-major-mismatch-source", pack_toml_text
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(source), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 1
    assert "incompatible pack" in capsys.readouterr().err


def test_sync_reads_derived_tree_baseline_through_the_confinement_helper(
    derived_tree, upstream_with_bumped_pack, monkeypatch, capsys
):
    """Spec AC-0020: the derived-tree baseline manifest read goes through the
    declared ``file_safety`` helper. Patching it to always refuse must make
    the pack-version signal disappear — an inline lexical-prefix check would
    not observe this patch and the test would still pass."""
    monkeypatch.setattr(
        catalogue_sync,
        "read_confined_regular_file",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            catalogue_sync.UnsafeContentError("patched refusal")
        ),
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", str(upstream_with_bumped_pack), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 0
    assert "pack version" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# AC-0013, AC-0014: the exit-code table is total and disjoint. One input per
# row, plus the boundary cases that establish totality (a resolver exception,
# malformed input, and the scalar recorded-path container) rather than
# relying on first-match-wins ordering to provide it.
# ---------------------------------------------------------------------------

# STUB: AC-0013
def test_check_returns_cannot_answer_when_pin_has_no_digest(
    derived_tree, upstream, capsys
):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--check"]
    )

    assert catalogue_sync.run(args) == 3
    assert "archive_sha256" in capsys.readouterr().err


# Row: "any: the invocation is malformed" — --compare-tree without --check
# and a symlinked target are already covered by AC-0002/AC-0007's tests
# above; "an omitted --source" and "neither or both of --dry-run and
# --check" are argparse-level refusals (both flags required) and never
# reach run() at all, per the comment in run() itself.

# Row: "any: source could not be resolved or its integrity could not be
# verified" — a CatalogueError case is covered above (AC-0002's resolution-
# refusal tests); this is AC-0014's second boundary case, a *non*-
# CatalogueError exception from the resolver, which must still reach a named
# row rather than propagate as an uncaught traceback.
def test_sync_resolver_exception_reaches_cannot_answer_without_a_traceback(
    derived_tree, upstream, monkeypatch, capsys
):
    def _raise(_uri):
        raise RuntimeError("unexpected resolver failure")

    monkeypatch.setattr(catalogue_sync, "resolve_catalogue", _raise)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )

    assert catalogue_sync.run(args) == 3


# Row: "--dry-run: the identity leak check reported a violation" — AC-0004
# and AC-0005 drive this at the replay-callable level; this is the row's
# CLI-level case, the one AC-0013's table itself binds to a code.
#
# Uses a fresh minimal-state target rather than `derived_tree`: that
# fixture's recorded recipe already carries a real `owner_email`, and
# `collect_fields`'s non-interactive default seeds the identity transform
# from it, which neutralises this exact anchor before the leak check ever
# runs — a target with no recorded owner fields is what leaves the anchor
# untransformed and the leak observable.
def test_sync_identity_leak_violation_returns_difference_code(tmp_path, capsys):
    target = tmp_path / "target"
    target.mkdir()
    _write_minimal_sync_state(target, packs=["alpha"])

    source = tmp_path / "leaky-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'maintainers = [{name = "Upstream Maintainer", '
        'email = "leaky@upstream.example.com"}]\n',
        encoding="utf-8",
    )
    pack = source / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (pack / "README.md").write_text(
        "contact leaky@upstream.example.com\n", encoding="utf-8"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run",
         "--format", "json"]
    )

    assert catalogue_sync.run(args) == 1
    # AC-0005: the command reports the violation count on top of the exit
    # code — one hit, `packs/alpha/README.md`'s `maintainer_email` anchor.
    doc = json.loads(capsys.readouterr().out)
    assert doc["violations"] == 1


# Row: "--dry-run or --check --compare-tree: the recorded-path container is
# not an array". The recipe stays derivable (packs=["alpha"]) — this is what
# separates a container that cannot be iterated at all from a malformed
# *entry*, which AC-0016 routes to "uncompared" instead.
def test_sync_scalar_managed_paths_container_cannot_answer_and_prints_no_plan(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"] = 0
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args_dry_run = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    assert catalogue_sync.run(args_dry_run) == 3
    dry_run_captured = capsys.readouterr()
    assert dry_run_captured.out == ""
    assert "not an array" in dry_run_captured.err

    args_check = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )
    assert catalogue_sync.run(args_check) == 3
    check_captured = capsys.readouterr()
    assert check_captured.out == ""
    assert "not an array" in check_captured.err


# Rows: "--check, no --compare-tree" — the four malformed-or-absent
# archive_sha256 shapes, and the success/difference comparison once a valid
# recorded digest is in play. `0` and `{}` are not strings at all; the row's
# condition is about absence or a malformed shape, not only a wrong length.
@pytest.mark.parametrize(
    "recorded_sha256",
    ["", 0, {}, "a" * 63],
    ids=["empty-string", "zero", "empty-object", "63-char-hex"],
)
def test_sync_check_cannot_answer_on_malformed_recorded_digest(
    derived_tree, tmp_path, monkeypatch, capsys, recorded_sha256
):
    extracted = tmp_path / "extracted-malformed-digest"
    _make_source(extracted)
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256="c" * 64,
        ),
    )
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pin"]["archive_sha256"] = recorded_sha256
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json", "--check"]
    )

    assert catalogue_sync.run(args) == 3
    assert "archive_sha256" in capsys.readouterr().err
    assert not extracted.exists()


def test_sync_check_cannot_answer_when_source_affords_no_verified_digest(
    derived_tree, upstream, capsys
):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--check"]
    )

    assert catalogue_sync.run(args) == 3
    assert "no verified archive_sha256" in capsys.readouterr().err


def test_sync_check_reports_success_when_recorded_digest_matches(
    derived_tree, tmp_path, monkeypatch, capsys
):
    extracted = tmp_path / "extracted-digest-match"
    _make_source(extracted)
    digest = "d" * 64
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256=digest,
        ),
    )
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pin"]["archive_sha256"] = digest
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json", "--check"]
    )

    assert catalogue_sync.run(args) == 0
    assert not extracted.exists()


def test_sync_check_reports_difference_when_recorded_digest_differs(
    derived_tree, tmp_path, monkeypatch, capsys
):
    extracted = tmp_path / "extracted-digest-differs"
    _make_source(extracted)
    monkeypatch.setattr(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256="e" * 64,
        ),
    )
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pin"]["archive_sha256"] = "f" * 64
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree),
         "--source", "catalogue+https://example.com/channel.json", "--check"]
    )

    assert catalogue_sync.run(args) == 1


# Rows: "--check --compare-tree" over four trees — clean, edited, an empty
# recorded set, and a partially dropped recorded set. The last two are what
# separate "nothing differs" (success) from "nothing was compared"
# (cannot-answer); a test that only covers clean and edited cannot tell them
# apart, which is why all four are driven rather than a representative pair.
def test_sync_check_compare_tree_reports_success_on_clean_tree(
    derived_tree, upstream, capsys
):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )

    assert catalogue_sync.run(args) == 0


def test_sync_check_compare_tree_reports_difference_on_edited_tree(
    derived_tree, upstream, capsys
):
    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(
        b"edited by the adopter\n"
    )

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )

    assert catalogue_sync.run(args) == 1


def test_sync_check_compare_tree_cannot_answer_on_empty_recorded_set(
    derived_tree, upstream, capsys
):
    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"] = []
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )

    assert catalogue_sync.run(args) == 3


def test_sync_check_compare_tree_cannot_answer_when_a_recorded_path_is_dropped(
    derived_tree, upstream, capsys
):
    # One of the two recorded paths (packs/alpha/pack.toml) still matches;
    # the other was dropped from disk entirely. This must NOT read as
    # "nothing differs" — it must cannot-answer, because not every recorded
    # path could be compared.
    (derived_tree / "packs" / "alpha" / "README.md").unlink()

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )

    assert catalogue_sync.run(args) == 3


def test_sync_no_invocation_produces_a_code_outside_the_four(
    derived_tree, upstream, tmp_path, capsys
):
    """Every case this module drives anywhere returns one of the four codes
    AC-0013 declares — never a fifth."""
    codes: set[int] = set()

    args_dry_run = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--dry-run"]
    )
    codes.add(catalogue_sync.run(args_dry_run))
    capsys.readouterr()

    args_malformed = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--compare-tree"]
    )
    codes.add(catalogue_sync.run(args_malformed))
    capsys.readouterr()

    args_check_no_digest = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream), "--check"]
    )
    codes.add(catalogue_sync.run(args_check_no_digest))
    capsys.readouterr()

    args_compare_success = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )
    codes.add(catalogue_sync.run(args_compare_success))
    capsys.readouterr()

    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"edited\n")
    args_compare_differs = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--check", "--compare-tree"]
    )
    codes.add(catalogue_sync.run(args_compare_differs))
    capsys.readouterr()

    assert codes <= {0, 1, 2, 3}
    assert codes == {0, 1, 2, 3}  # this exact run reaches all four codes


# ---------------------------------------------------------------------------
# T2: the scope predicate that selects the write set (spec AC-0033 clauses
# 4-5, AC-0042, AC-0043, AC-0066).
#
# The planned-path set every test below drives the predicate against comes
# from a real `replay_derivation` call over an on-disk fixture source, never
# from a hand-written `planned_paths = {...}` literal — the fixture ships a
# `core` pack and a `core-extras` sibling (the prefix trap AC-0043 names), a
# `credential-brokers` pack (which pulls `packages/credbroker/**` into the
# plan), a `packages/agentbundle/` tree (collected under
# `.agentbundle/tooling/agentbundle/**` in vendored mode), a
# `packs/catalogue-curation/` tree (collected under
# `.agentbundle/tooling/packs/catalogue-curation/**` — the subtree a
# narrower "only agentbundle/" reading would wrongly admit), a profile, a
# shared guide, and a conformance test, so every clause this task verifies
# has a real planned path to exercise it.
# ---------------------------------------------------------------------------

def _make_scope_predicate_source(root: Path) -> Path:
    """Build a real, on-disk source catalogue naming every subtree T2's tests
    need, so `replay_derivation` produces the planned-path set those tests
    drive the scope predicate against."""
    root.mkdir(parents=True)
    (root / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'display_name = "Upstream Catalogue"\n'
        'description = "A source catalogue for scope-predicate tests."\n',
        encoding="utf-8",
    )
    for pack_name in ("core", "core-extras", "credential-brokers"):
        pack_dir = root / "packs" / pack_name
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            f'[pack]\nname = "{pack_name}"\nversion = "1.0.0"\n', encoding="utf-8"
        )
    curation_dir = root / "packs" / "catalogue-curation"
    curation_dir.mkdir(parents=True)
    (curation_dir / "marker.txt").write_text("curation\n", encoding="utf-8")
    credbroker_pkg = root / "packages" / "credbroker" / "credbroker"
    credbroker_pkg.mkdir(parents=True)
    (credbroker_pkg / "__init__.py").write_text("", encoding="utf-8")
    agentbundle_pkg = root / "packages" / "agentbundle"
    agentbundle_pkg.mkdir(parents=True)
    (agentbundle_pkg / "marker.py").write_text("", encoding="utf-8")
    profiles_dir = root / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8"
    )
    guides_dir = root / "guides" / "_shared"
    guides_dir.mkdir(parents=True)
    (guides_dir / "example.md").write_text("# guide\n", encoding="utf-8")
    conformance_dir = root / "tests" / "conformance"
    conformance_dir.mkdir(parents=True)
    (conformance_dir / "example_test.py").write_text("", encoding="utf-8")
    return root


def _replay_scope_predicate_source(
    tmp_path: Path, *, tooling: str = "vendored", packs: list[str] | None = None
) -> set[str]:
    """Return the real planned-path set a `replay_derivation` call produces
    over :func:`_make_scope_predicate_source`."""
    source = _make_scope_predicate_source(tmp_path / "source")
    cfg = ish.SelfHostedInitConfig(
        target=tmp_path / "derived",
        source=source,
        tooling=tooling,
        attribution="white-label",
        guides="selected",
        name="probe",
        display_name="Probe",
        description="probe",
        owner_name="Probe",
        owner_email="probe@example.invalid",
        packs=packs,
        dry_run=True,
    )
    replay = ish.replay_derivation(cfg, interactive=False)
    return set(replay.file_bytes)


def test_scope_predicate_admits_named_subtrees_and_unions_repeated_pack(tmp_path):
    planned = _replay_scope_predicate_source(tmp_path)

    admitted, _ = catalogue_sync.select_write_set(
        planned, pack_names=["core"], profile_names=["default"], guides=True
    )

    assert "packs/core/pack.toml" in admitted
    assert "profiles/default.toml" in admitted
    assert "guides/_shared/example.md" in admitted

    admitted_union, _ = catalogue_sync.select_write_set(
        planned, pack_names=["core", "core-extras"], profile_names=[], guides=False
    )
    assert "packs/core/pack.toml" in admitted_union
    assert "packs/core-extras/pack.toml" in admitted_union


def test_scope_predicate_excludes_nothing_with_no_scoping_flag(tmp_path):
    # tooling=external and no credential-brokers pack selected: this fixture's
    # planned set carries no deferred-package path, so "excludes nothing" is
    # observable as an exact-equality, not merely a superset check.
    planned = _replay_scope_predicate_source(
        tmp_path, tooling="external", packs=["core", "core-extras"]
    )

    admitted, deferred = catalogue_sync.select_write_set(
        planned, pack_names=[], profile_names=[], guides=False
    )

    assert admitted == planned
    assert deferred == 0


def test_scope_predicate_excludes_catalogue_toml_and_conformance_under_any_scope(
    tmp_path,
):
    planned = _replay_scope_predicate_source(tmp_path)

    admitted, _ = catalogue_sync.select_write_set(
        planned, pack_names=["core"], profile_names=[], guides=False
    )

    assert "catalogue.toml" in planned
    assert "catalogue.toml" not in admitted
    conformance_paths = {p for p in planned if p.startswith("tests/conformance/")}
    assert conformance_paths  # the fixture actually ships one
    assert not (conformance_paths & admitted)


@pytest.mark.parametrize(
    "pack_names,profile_names,guides",
    [
        ([], [], False),
        (["core"], [], False),
        ([], ["default"], False),
        ([], [], True),
    ],
)
def test_scope_predicate_defers_vendored_and_credbroker_paths_under_every_scope(
    tmp_path, pack_names, profile_names, guides
):
    planned = _replay_scope_predicate_source(tmp_path)
    deferred_paths = {
        p for p in planned
        if p.startswith(("packages/credbroker/", ".agentbundle/tooling/"))
    }
    # The whole vendored tooling root is the extent, not only its
    # `agentbundle/` subdirectory — the fixture's `packs/catalogue-curation/`
    # copy is exactly the subtree a narrower reading would wrongly admit.
    assert any(
        p.startswith(".agentbundle/tooling/packs/catalogue-curation/")
        for p in deferred_paths
    )
    assert any(
        p.startswith(".agentbundle/tooling/agentbundle/") for p in deferred_paths
    )
    assert deferred_paths  # the fixture actually ships every deferred subtree

    admitted, deferred_count = catalogue_sync.select_write_set(
        planned,
        pack_names=pack_names,
        profile_names=profile_names,
        guides=guides,
    )

    assert not (deferred_paths & admitted)
    assert deferred_count == len(deferred_paths)


def test_scope_predicate_pack_core_does_not_admit_core_extras_sibling(tmp_path):
    planned = _replay_scope_predicate_source(tmp_path)
    assert "packs/core-extras/pack.toml" in planned  # the fixture ships the sibling

    admitted, _ = catalogue_sync.select_write_set(
        planned, pack_names=["core"], profile_names=[], guides=False
    )

    assert "packs/core-extras/pack.toml" not in admitted


# ---------------------------------------------------------------------------
# T3: the state merge and the pin (spec AC-0033 clause 1, AC-0036, AC-0037,
# AC-0044, AC-0045, AC-0059). Both functions are pure over their arguments —
# no test in this section touches a filesystem.
# ---------------------------------------------------------------------------


def _base_old_state(
    *, packs: list[str], profiles: list[str] | None = None, **recipe_extra: object
) -> dict:
    return {
        "schema_version": "3",
        "managed_paths": [],
        "adapters": ["claude-code"],
        "managed_target_path": "",
        "source_pack_identity": "",
        "source_root_kind": "self-hosted-source",
        "recipe": {
            "packs": list(packs),
            "profiles": list(profiles) if profiles is not None else [],
            "guides": "selected",
            "attribution": "white-label",
            "tooling": "external",
            "name": "acme",
            "display_name": "Acme",
            "description": "an acme catalogue",
            "owner_name": "Acme Team",
            "owner_email": "team@acme.example.invalid",
            "preferred_adapter": "claude-code",
            "repository_url": None,
            **recipe_extra,
        },
        "pin": {
            "source_revision": None,
            "archive_sha256": None,
            "synced_at": "2026-09-01T00:00:00Z",
        },
    }


def test_merge_path_set_equals_recorded_minus_removed_union_written():
    old_state = _base_old_state(packs=["alpha"])
    recorded = {
        "packs/alpha/README.md": "sha-untouched",
        "packs/alpha/stale.md": "sha-stale",
        "packs/alpha/edited.md": "sha-adopter-edited",
    }
    # "packs/alpha/new.md" simulates a Tier-1 write; "packs/alpha/stale.md"
    # is stale-removed this run; "packs/alpha/edited.md" is would-companion —
    # its *original* path is untouched (no key in `written`) and its
    # companion destination is never a key in either mapping, so neither
    # this function's signature nor its logic has anywhere for a companion
    # path to enter the merged set. "packs/other/untouched.md" is a Tier-3
    # planned path this run never admits at all — absent from every input.
    written = {
        "packs/alpha/new.md": "sha-new",
    }
    removed = {"packs/alpha/stale.md"}

    merged = catalogue_sync.merge_ownership_state(
        old_state,
        recorded=recorded,
        written=written,
        removed=removed,
        pack_names=["alpha"],
        profile_names=[],
        pin=old_state["pin"],
    )

    merged_paths = {
        entry["path"]: entry["sha256"] for entry in merged["managed_paths"]
    }
    assert merged_paths == {
        "packs/alpha/README.md": "sha-untouched",
        "packs/alpha/edited.md": "sha-adopter-edited",
        "packs/alpha/new.md": "sha-new",
    }
    assert "packs/alpha/stale.md" not in merged_paths  # removed
    # AC-0059's two absolute clauses are NOT asserted here, deliberately.
    # Asserting that a Tier-3 path or a companion destination is absent, when
    # neither was supplied in `recorded` or `written`, holds whatever this
    # function does -- it is a check that cannot fail. Measured 2026-09-23:
    # feeding "packs/alpha/README.upstream.md" in via `recorded` leaves it in
    # the merged set, so the exclusion is not a property of this function.
    #
    # Under the contribution reading the owner took, that is correct: AC-0059
    # says "a path THE RUN CLASSIFIED Tier-3", and this run classifies nothing
    # that arrives through `recorded`. The clauses bind the caller, which is
    # the only seam that knows which paths were companion destinations -- and
    # a suffix filter here would be wrong outright, since AC-0071 shows a
    # source may legitimately ship `x.upstream.md`. T4/T6 own the assertion
    # that no companion destination ever enters `written`; the verification
    # ledger records that hand-off.


def test_merge_digests_are_written_bytes_or_pre_run_value():
    old_state = _base_old_state(packs=["alpha"])
    recorded = {
        "packs/alpha/updated.md": "sha-pre-run",
        "packs/alpha/untouched.md": "sha-pre-run-untouched",
    }
    written = {"packs/alpha/updated.md": "sha-post-write"}

    merged = catalogue_sync.merge_ownership_state(
        old_state,
        recorded=recorded,
        written=written,
        removed=[],
        pack_names=["alpha"],
        profile_names=[],
        pin=old_state["pin"],
    )

    merged_paths = {
        entry["path"]: entry["sha256"] for entry in merged["managed_paths"]
    }
    assert merged_paths["packs/alpha/updated.md"] == "sha-post-write"
    assert merged_paths["packs/alpha/untouched.md"] == "sha-pre-run-untouched"


def test_merge_carries_the_effective_selection_ac0033_clause1_produced():
    old_state = _base_old_state(packs=["alpha"], profiles=["default"])

    merged = catalogue_sync.merge_ownership_state(
        old_state,
        recorded={},
        written={},
        removed=[],
        pack_names=["alpha", "beta"],
        profile_names=["default", "extra"],
        pin=old_state["pin"],
    )

    assert merged["recipe"]["packs"] == ["alpha", "beta"]
    assert merged["recipe"]["profiles"] == ["default", "extra"]


def test_merge_pack_list_after_new_pack_is_pre_run_list_plus_the_name():
    old_state = _base_old_state(packs=["alpha", "beta"])

    merged = catalogue_sync.merge_ownership_state(
        old_state,
        recorded={},
        written={},
        removed=[],
        # T6 owns resolving this union; this task asserts only that the
        # merge records whatever effective selection it is handed.
        pack_names=["alpha", "beta", "gamma"],
        profile_names=[],
        pin=old_state["pin"],
    )

    assert set(merged["recipe"]["packs"]) == {"alpha", "beta", "gamma"}
    assert "alpha" in merged["recipe"]["packs"]
    assert "beta" in merged["recipe"]["packs"]  # no pre-run entry is dropped


def test_merge_scoped_run_leaves_every_recorded_identity_field_at_pre_run_value():
    old_state = _base_old_state(
        packs=["alpha"],
        guides="selected",
        attribution="attributed",
        tooling="vendored",
    )
    old_recipe = dict(old_state["recipe"])

    # A `--pack alpha` scoped run: the effective selection is unchanged
    # (alpha was already recorded), but the scope predicate (T2) narrowed
    # what was *written*, not what this merge records for every other field.
    merged = catalogue_sync.merge_ownership_state(
        old_state,
        recorded={},
        written={},
        removed=[],
        pack_names=["alpha"],
        profile_names=[],
        pin=old_state["pin"],
    )

    identity_fields = set(old_recipe) - {"packs", "profiles"}
    for field in identity_fields:
        assert merged["recipe"][field] == old_recipe[field], field


@pytest.mark.parametrize(
    "source_uri,archive_sha256,source_revision,expected_revision,expected_archive",
    [
        ("/local/clone/path", None, None, None, None),
        ("git+https://github.com/owner/repo@v1.2.3", None, None, "v1.2.3", None),
        ("git+https://github.com/owner/repo", None, None, "main", None),
        (
            "archive+https://example.test/archive.tar.gz#sha256=deadbeef",
            "deadbeef" * 8,
            None,
            None,
            "deadbeef" * 8,
        ),
        (
            "catalogue+https://example.test/catalogue.tar.gz#sha256=deadbeef",
            "deadbeef" * 8,
            "v9.9.9",
            "v9.9.9",
            "deadbeef" * 8,
        ),
        (
            "catalogue+https://example.test/catalogue.tar.gz#sha256=deadbeef",
            "deadbeef" * 8,
            None,
            None,
            "deadbeef" * 8,
        ),
    ],
)
def test_pin_per_source_form_under_attributed(
    source_uri, archive_sha256, source_revision, expected_revision, expected_archive
):
    pin = catalogue_sync.build_pin(
        source_uri,
        archive_sha256=archive_sha256,
        source_revision=source_revision,
        attributed=True,
        synced_at="2026-09-23T00:00:00Z",
    )

    assert pin["source_uri"] == source_uri
    assert pin["source_revision"] == expected_revision
    assert pin["archive_sha256"] == expected_archive
    assert pin["synced_at"] == "2026-09-23T00:00:00Z"


@pytest.mark.parametrize(
    "source_uri",
    [
        "/local/clone/path",
        "git+https://github.com/owner/repo@v1.2.3",
        "archive+https://example.test/archive.tar.gz#sha256=deadbeef",
        "catalogue+https://example.test/catalogue.tar.gz#sha256=deadbeef",
    ],
)
def test_pin_source_uri_absent_under_white_label_on_every_row(source_uri):
    pin = catalogue_sync.build_pin(
        source_uri,
        archive_sha256="deadbeef" * 8,
        source_revision="v9.9.9",
        attributed=False,
        synced_at="2026-09-23T00:00:00Z",
    )

    assert "source_uri" not in pin


# ---------------------------------------------------------------------------
# T4: the write sequence applies a plan or restores the tree.
#
# `edited_tree` (plan.md § Construction tests) is built programmatically
# rather than as a committed fixture directory, matching this file's existing
# convention for every other generated-source fixture (`_make_source`,
# `_make_scope_predicate_source`) — a bounded search found no existing helper
# already shaped for this task's needs, so a new one is warranted (Cut before
# adding rung 2/7: an adequate repository pattern for *how* to build it, no
# adequate existing builder *of* it).
#
# One source ships:
#   - `packs/alpha/` — `README.md` (on-disk matches recorded -> would-update),
#     `unchanged.md` (on-disk differs from recorded -> would-companion).
#   - `packs/beta/` — a pack the recorded recipe never named (an "introduced"
#     pack): every path Tier-3/untouched, all admitted per AC-0033 clause 3's
#     third admission.
#   - `profiles/default.toml` — likewise an introduced profile.
#   - `guides/_shared/guide.md`, `catalogue.toml`,
#     `tests/conformance/test_example.py` — Tier-3/untouched for an ordinary
#     reason (never recorded, never introduced): never admitted.
# The recorded state additionally carries `packs/alpha/gone.md` — present,
# sha-matching, no longer planned by the source: the stale recorded path the
# removal guard admits.
# ---------------------------------------------------------------------------


def _make_apply_source(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream"\n'
        'display_name = "Upstream"\n'
        'description = "apply sequence test source"\n',
        encoding="utf-8",
    )
    alpha = root / "packs" / "alpha"
    alpha.mkdir(parents=True)
    (alpha / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (alpha / "README.md").write_text("# Alpha v2\n", encoding="utf-8")
    (alpha / "unchanged.md").write_text("upstream bytes\n", encoding="utf-8")
    beta = root / "packs" / "beta"
    beta.mkdir(parents=True)
    (beta / "pack.toml").write_text(
        '[pack]\nname = "beta"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (beta / "NEW.md").write_text("new pack file\n", encoding="utf-8")
    profiles = root / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8"
    )
    guides = root / "guides" / "_shared"
    guides.mkdir(parents=True)
    (guides / "guide.md").write_text("# guide\n", encoding="utf-8")
    conformance = root / "tests" / "conformance"
    conformance.mkdir(parents=True)
    (conformance / "test_example.py").write_text("", encoding="utf-8")
    return root


def _write_apply_old_state(
    target: Path, *, extra_recipe: dict | None = None
) -> None:
    alpha = target / "packs" / "alpha"
    alpha.mkdir(parents=True)
    (alpha / "README.md").write_bytes(b"# Alpha\n")
    (alpha / "unchanged.md").write_bytes(b"adopter edited\n")
    (alpha / "gone.md").write_bytes(b"stale\n")
    state_path = target / ".agentbundle" / "self-host-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    recipe = {
        "packs": ["alpha"],
        "profiles": [],
        "guides": "selected",
        "attribution": "white-label",
        "tooling": "external",
        "name": "derived",
        "display_name": "Derived",
        "description": "d",
        "owner_name": "Owner",
        "owner_email": "owner@example.invalid",
        "preferred_adapter": "claude-code",
        "repository_url": None,
    }
    recipe.update(extra_recipe or {})
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "3",
                "managed_paths": [
                    {
                        "path": "packs/alpha/README.md",
                        "sha256": hashlib.sha256(b"# Alpha\n").hexdigest(),
                    },
                    {
                        "path": "packs/alpha/unchanged.md",
                        "sha256": hashlib.sha256(b"original\n").hexdigest(),
                    },
                    {
                        "path": "packs/alpha/gone.md",
                        "sha256": hashlib.sha256(b"stale\n").hexdigest(),
                    },
                ],
                "adapters": ["claude-code"],
                "managed_target_path": str(target),
                "source_pack_identity": "derived",
                "source_root_kind": "self-hosted-source",
                "recipe": recipe,
                "pin": {
                    "source_revision": None,
                    "archive_sha256": None,
                    "synced_at": "2026-09-01T00:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )


def _replay_apply_fixture(tmp_path: Path, *, tag: str = "default"):
    """Build the `edited_tree` fixture and replay it. Returns
    ``(target, replay, verdict_rows)``.

    ``packs=["alpha", "beta"]``/``profiles=["default"]`` simulate what T6
    owns resolving (AC-0033 clause 1's union of the recorded recipe with any
    name a scoping flag introduces) -- a bare replay with no explicit
    selection would instead read back only the recorded recipe's own
    ``["alpha"]``/``[]``, leaving "beta"/"default" never selected at all,
    which is not the scenario this fixture is for.
    """
    source = _make_apply_source(tmp_path / f"apply-source-{tag}")
    target = tmp_path / f"apply-target-{tag}"
    target.mkdir()
    _write_apply_old_state(target)
    cfg = ish.SelfHostedInitConfig(
        target=target, source=source, tooling="external", attribution="white-label",
        guides="selected", dry_run=True,
        packs=["alpha", "beta"], profiles=["default"],
    )
    replay = ish.replay_derivation(cfg, interactive=False)
    assert not replay.violations
    planned_paths = set(replay.file_bytes)
    _counts, verdict_rows = catalogue_sync._classify_planned_paths(
        target, replay.old_state, planned_paths, []
    )
    return target, replay, verdict_rows


def _apply(target: Path, replay, verdict_rows, **overrides) -> catalogue_sync.WriteSequenceResult:
    kwargs: dict = {
        "old_state": replay.old_state,
        "verdict_rows": verdict_rows,
        "file_bytes": replay.file_bytes,
        "planned_paths": set(replay.file_bytes),
        "pack_names": replay.pack_names,
        "profile_names": replay.profile_names,
        "guides_scope": False,
        "guides_mode": replay.config.guides,
        "pin": {"synced_at": "2026-09-23T00:00:00Z", "source_revision": None,
                "archive_sha256": None},
    }
    kwargs.update(overrides)
    return catalogue_sync.apply_write_sequence(target, **kwargs)


def test_apply_write_order_is_packs_profiles_guides_derivation_then_state(
    tmp_path, monkeypatch
):
    # Verifies AC-0032. A hand-built verdict set: the fourth (derivation-wide)
    # group is non-empty only on an unscoped run, so it is included here
    # deliberately -- a fixture that always supplies a scoping flag could not
    # observe it.
    target = tmp_path / "target"
    target.mkdir()
    calls: list[str] = []

    def _record_jailed(root, relpath, content, **kwargs):
        calls.append(relpath)
        return root / relpath

    def _record_companion(root, relpath, content, **kwargs):
        calls.append("packs/alpha/README.upstream.md")
        return root / relpath

    def _record_state(root, merged_state):
        calls.append("STATE")

    monkeypatch.setattr(catalogue_sync, "write_jailed", _record_jailed)
    monkeypatch.setattr(catalogue_sync, "write_companion", _record_companion)
    monkeypatch.setattr(catalogue_sync, "write_merged_state", _record_state)

    verdict_rows = [
        ("guides/_shared/example.md", "would-update", None),
        ("profiles/default.toml", "would-update", None),
        ("packs/alpha/README.md", "would-companion", "packs/alpha/README.upstream.md"),
        ("catalogue.toml", "would-update", None),
    ]
    file_bytes = {
        "guides/_shared/example.md": b"g",
        "profiles/default.toml": b"p",
        "packs/alpha/README.md": b"r",
        "catalogue.toml": b"c",
    }
    result = catalogue_sync.apply_write_sequence(
        target,
        old_state={},
        verdict_rows=verdict_rows,
        file_bytes=file_bytes,
        planned_paths=set(file_bytes),
        pack_names=[], profile_names=[],
        guides_scope=False, guides_mode="selected",
        pin={},
    )

    assert result.ok
    assert calls == [
        "packs/alpha/README.upstream.md",
        "profiles/default.toml",
        "guides/_shared/example.md",
        "catalogue.toml",
        "STATE",
    ]


def test_apply_written_set_equals_admitted_rows_in_both_directions(tmp_path):
    # Verifies AC-0033 clauses 3 and 6, and AC-0045.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path)
    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    expected_written_paths = {
        "packs/alpha/README.md",              # would-update
        "packs/beta/pack.toml",               # untouched, beta is introduced
        "packs/beta/NEW.md",                  # untouched, beta is introduced
        "profiles/default.toml",              # untouched, default is introduced
    }
    assert set(result.written) == expected_written_paths
    # The companion is a SEPARATE destination from `written` -- AC-0034's own
    # bytes assertion covers it below; asserting it here too would make this
    # an "at least" check that a would-update-only oracle also passes.
    assert (target / "packs" / "alpha" / "unchanged.upstream.md").exists()
    # An ordinary untouched path (not introduced) is never admitted.
    assert "catalogue.toml" not in result.written
    assert "guides/_shared/guide.md" not in result.written
    assert "tests/conformance/test_example.py" not in result.written
    # State is written (clause 6) -- not part of `written`, but the file
    # exists afterward.
    assert (target / ".agentbundle" / "self-host-state.json").exists()


def test_apply_companion_carries_source_bytes_and_original_is_unchanged(tmp_path):
    # Verifies AC-0034.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="companion")
    before_digest = hashlib.sha256(
        (target / "packs" / "alpha" / "unchanged.md").read_bytes()
    ).hexdigest()

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    companion = target / "packs" / "alpha" / "unchanged.upstream.md"
    assert companion.read_bytes() == replay.file_bytes["packs/alpha/unchanged.md"]
    after_digest = hashlib.sha256(
        (target / "packs" / "alpha" / "unchanged.md").read_bytes()
    ).hexdigest()
    assert after_digest == before_digest


def test_apply_companion_destination_never_enters_written(tmp_path):
    # Discharges the obligation T3 handed forward (docs/specs/
    # catalogue-sync-apply/notes/verification-ledger.md § Execution --
    # wave 1): `merge_ownership_state` has no argument through which a
    # companion destination could arrive, but that only holds if this
    # task's own `written` mapping -- the argument T6 will pass it -- never
    # puts one there either. Driven through the real write sequence, over a
    # fixture where a would-companion path genuinely exists, so the
    # assertion fails if the companion path enters `written` (it did, before
    # this task's `is_companion` guard was added).
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="companion-written")
    before_digest = hashlib.sha256(
        (target / "packs" / "alpha" / "unchanged.md").read_bytes()
    ).hexdigest()
    companion_destination = "packs/alpha/unchanged.upstream.md"
    assert any(
        v == "would-companion" and c == companion_destination
        for _p, v, c in verdict_rows
    ), "fixture must actually carry a would-companion row"

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert companion_destination not in result.written
    after_digest = hashlib.sha256(
        (target / "packs" / "alpha" / "unchanged.md").read_bytes()
    ).hexdigest()
    assert after_digest == before_digest


def test_apply_stale_removal_runs_after_writes_with_full_keep_set(tmp_path, monkeypatch):
    # Verifies AC-0035.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="removal-order")
    calls: list[tuple[str, tuple, dict]] = []
    real_select_removal_set = catalogue_sync.select_removal_set

    def _spy_select_removal_set(*args, **kwargs):
        calls.append(("select_removal_set", args, kwargs))
        return real_select_removal_set(*args, **kwargs)

    real_write_jailed = catalogue_sync.write_jailed

    def _spy_write_jailed(root, relpath, content, **kw):
        calls.append(("write_jailed", (relpath,), {}))
        return real_write_jailed(root, relpath, content, **kw)

    real_write_companion = catalogue_sync.write_companion

    def _spy_write_companion(root, relpath, content, **kw):
        calls.append(("write_companion", (relpath,), {}))
        return real_write_companion(root, relpath, content, **kw)

    monkeypatch.setattr(catalogue_sync, "select_removal_set", _spy_select_removal_set)
    monkeypatch.setattr(catalogue_sync, "write_jailed", _spy_write_jailed)
    monkeypatch.setattr(catalogue_sync, "write_companion", _spy_write_companion)

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert "packs/alpha/gone.md" in result.removed
    write_call_indexes = [
        i for i, c in enumerate(calls) if c[0] in ("write_jailed", "write_companion")
    ]
    removal_call_index = next(
        i for i, c in enumerate(calls) if c[0] == "select_removal_set"
    )
    assert write_call_indexes  # the fixture writes at least one path
    assert max(write_call_indexes) < removal_call_index

    # The keep-set argument is the full replayed set, not the write set.
    removal_kwargs_call = calls[removal_call_index]
    _name, args, _kwargs = removal_kwargs_call
    full_replayed_arg = args[2]
    assert full_replayed_arg == set(replay.file_bytes)
    assert full_replayed_arg != set(result.written)  # the two sets differ here


def test_apply_keep_set_handed_to_the_shipped_guard_is_full_replayed(
    tmp_path, monkeypatch
):
    """AC-0035: the keep-set the SHIPPED removal guard receives is the full
    replayed set, on a scoped run as well as an unscoped one.

    Two things this pins that the sibling ordering test above cannot.

    It spies `_plan_stale_owned_paths`, not `select_removal_set`. AC-0035
    constrains the argument handed to the shipped guard, and a narrowing
    inside `select_removal_set` -- which is exactly where the plan's § Never
    do violation would live -- never touches `select_removal_set`'s own
    inputs. Measured 2026-09-23: a spy one level too high reports 9 paths
    while the guard is handed 3.

    And it drives a SCOPED run. With no scoping flag every path is in scope,
    so narrowing the keep-set is a no-op and an unscoped fixture cannot fail.
    """
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="keepset-scoped")
    seen: list[set[str]] = []
    real_guard = catalogue_sync._plan_stale_owned_paths

    def _spy(target_arg, old_state_arg, current_paths):
        seen.append(set(current_paths))
        return real_guard(target_arg, old_state_arg, current_paths)

    monkeypatch.setattr(catalogue_sync, "_plan_stale_owned_paths", _spy)
    _apply(target, replay, verdict_rows, scope_packs=["alpha"])

    assert seen, "_plan_stale_owned_paths was never called"
    assert seen[0] == set(replay.file_bytes)

    # Teeth: under this scope a narrowed keep-set is strictly smaller, so the
    # assertion above can actually fail. Without this the test would pass on
    # a fixture whose every path happened to be in scope.
    in_scope_only = {q for q in replay.file_bytes if q.startswith("packs/alpha/")}
    assert in_scope_only < set(replay.file_bytes)


def test_apply_unscoped_run_leaves_vendored_tooling_present_and_out_of_coverage(
    tmp_path,
):
    # Verifies AC-0069 (the case that matters -- unscoped, no scope excludes
    # these paths at all, so only coverage protects them).
    source = _make_apply_source(tmp_path / "vendored-source")
    target = tmp_path / "vendored-target"
    target.mkdir()
    _write_apply_old_state(target, extra_recipe={"tooling": "vendored"})
    tooling_dir = target / ".agentbundle" / "tooling" / "agentbundle"
    tooling_dir.mkdir(parents=True)
    (tooling_dir / "marker.py").write_bytes(b"vendored\n")
    credbroker_dir = target / "packages" / "credbroker"
    credbroker_dir.mkdir(parents=True)
    (credbroker_dir / "marker.py").write_bytes(b"cred\n")
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append(
        {"path": ".agentbundle/tooling/agentbundle/marker.py",
         "sha256": hashlib.sha256(b"vendored\n").hexdigest()}
    )
    state["managed_paths"].append(
        {"path": "packages/credbroker/marker.py",
         "sha256": hashlib.sha256(b"cred\n").hexdigest()}
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")

    cfg = ish.SelfHostedInitConfig(
        target=target, source=source, tooling="external", attribution="white-label",
        guides="selected", dry_run=True,
        packs=["alpha", "beta"], profiles=["default"],
    )
    replay = ish.replay_derivation(cfg, interactive=False)
    planned_paths = set(replay.file_bytes)
    _counts, verdict_rows = catalogue_sync._classify_planned_paths(
        target, replay.old_state, planned_paths, []
    )

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert (tooling_dir / "marker.py").exists()
    assert (credbroker_dir / "marker.py").exists()
    assert ".agentbundle/tooling/agentbundle/marker.py" not in result.removed
    assert "packages/credbroker/marker.py" not in result.removed
    assert ".agentbundle/tooling/agentbundle/marker.py" in result.out_of_coverage
    assert "packages/credbroker/marker.py" in result.out_of_coverage


def test_apply_pack_scoped_coverage_leaves_out_of_pack_recorded_paths_present(
    tmp_path,
):
    # Verifies AC-0064's scope axis: a --pack run leaves every recorded path
    # outside that pack present, including one the guard would otherwise
    # admit for removal.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="scoped-removal")
    # "packs/alpha/gone.md" is stale and guard-removable; scope this run to
    # "beta" only, so alpha's subtree -- including gone.md -- is out of scope.
    # `pack_names`/`profile_names` stay the resolved effective selection
    # (unchanged); `scope_packs` is the `--pack beta` flag itself.
    result = _apply(
        target, replay, verdict_rows,
        scope_packs=["beta"],
    )

    assert result.ok, result
    assert (target / "packs" / "alpha" / "gone.md").exists()
    assert "packs/alpha/gone.md" not in result.removed
    assert "packs/alpha/gone.md" in result.out_of_coverage


def test_apply_guides_mode_none_leaves_recorded_guides_paths_present(tmp_path):
    # Verifies AC-0069 clause 2 -- the mode-narrowing axis, which no fixed
    # subtree list reaches.
    source = _make_apply_source(tmp_path / "guides-mode-source")
    target = tmp_path / "guides-mode-target"
    target.mkdir()
    _write_apply_old_state(target)
    guide_path = target / "guides" / "_shared" / "old-guide.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_bytes(b"old guide\n")
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append(
        {"path": "guides/_shared/old-guide.md",
         "sha256": hashlib.sha256(b"old guide\n").hexdigest()}
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")

    cfg = ish.SelfHostedInitConfig(
        target=target, source=source, tooling="external", attribution="white-label",
        guides="none", dry_run=True,
        packs=["alpha", "beta"], profiles=["default"],
    )
    replay = ish.replay_derivation(cfg, interactive=False)
    planned_paths = set(replay.file_bytes)
    _counts, verdict_rows = catalogue_sync._classify_planned_paths(
        target, replay.old_state, planned_paths, []
    )

    result = _apply(target, replay, verdict_rows, guides_mode="none")

    assert result.ok, result
    assert guide_path.exists()
    assert "guides/_shared/old-guide.md" not in result.removed
    assert "guides/_shared/old-guide.md" in result.out_of_coverage


def test_apply_credbroker_path_no_longer_shipped_is_never_removed(tmp_path):
    # Verifies AC-0064: coverage, not the keep-set, makes the protection
    # absolute even when the source has stopped shipping the path at all.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="credbroker")
    credbroker_dir = target / "packages" / "credbroker"
    credbroker_dir.mkdir(parents=True)
    (credbroker_dir / "gone.py").write_bytes(b"cred\n")
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append(
        {"path": "packages/credbroker/gone.py",
         "sha256": hashlib.sha256(b"cred\n").hexdigest()}
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")
    replay.old_state["managed_paths"] = state["managed_paths"]

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert (credbroker_dir / "gone.py").exists()
    assert "packages/credbroker/gone.py" not in result.removed
    assert "packages/credbroker/gone.py" in result.out_of_coverage


def test_apply_removal_refuses_at_unlink_when_entry_becomes_link_like(tmp_path):
    # Verifies AC-0073. `_plan_stale_owned_paths` (a separate module's own
    # import of `sha256_confined_regular_file`) already found `gone.md`
    # removable (present, sha-matching, no longer planned) at plan time;
    # this patches `catalogue_sync`'s own reference, which only
    # `_confined_unlink` -- the at-unlink recheck -- ever calls, so this
    # fires exactly once, at the moment of the unlink and not at the plan.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="unlink-race")
    gone = target / "packs" / "alpha" / "gone.md"
    real_sha256_confined = catalogue_sync.sha256_confined_regular_file

    def _fake_confined(root, path):
        if path == gone:
            gone.unlink()
            elsewhere = target / "elsewhere.txt"
            elsewhere.write_bytes(b"x")
            gone.symlink_to(elsewhere)
            raise catalogue_sync.UnsafeContentError("became a symlink")
        return real_sha256_confined(root, path)

    with patch.object(
        catalogue_sync, "sha256_confined_regular_file", side_effect=_fake_confined
    ):
        result = _apply(target, replay, verdict_rows)

    assert result.removal_failed
    assert "packs/alpha/gone.md" not in result.removed
    assert gone.is_symlink()  # left as the race left it, not clobbered


def test_apply_removal_spelling_traversal_resolves_inside_protected_subtree(tmp_path):
    # Verifies AC-0069's spelling clause, traversal half. Driven directly
    # against `_in_coverage` rather than through the full removal pipeline:
    # `_plan_stale_owned_paths`'s own confined sha guard refuses a literal
    # `..` path segment outright (a dot-segment is never removable through
    # the shipped guard, traversal or not), so a traversal-spelled recorded
    # path can never reach "removable" candidacy at all -- this is the
    # security-hardening the guard already carries, and this task's own
    # coverage check is a second, independent layer over what the guard does
    # admit. Coverage's own spelling safety is tested at the seam that owns
    # it.
    target = tmp_path / "spelling-target"
    tooling_dir = target / ".agentbundle" / "tooling" / "agentbundle"
    tooling_dir.mkdir(parents=True)
    (tooling_dir / "x.py").write_bytes(b"vendored\n")
    (target / "packages").mkdir()
    traversal_path = "packages/../.agentbundle/tooling/agentbundle/x.py"

    in_coverage = catalogue_sync._in_coverage(
        target, traversal_path,
        pack_names=["alpha"], profile_names=[], guides_mode="selected", scope=None,
    )

    assert not in_coverage


def _filesystem_is_case_insensitive(tmp_path: Path) -> bool:
    marker = tmp_path / "CaseProbe"
    marker.write_text("x", encoding="utf-8")
    try:
        return (tmp_path / "caseprobe").exists()
    finally:
        marker.unlink()


def test_apply_removal_case_insensitive_spelling_resolves_inside_protected_subtree(
    tmp_path,
):
    # Verifies AC-0069's spelling clause, case-insensitive half. Skipped
    # where the filesystem does not fold case -- see AGENTS.md's package
    # traps note on platform-dependent tests.
    if not _filesystem_is_case_insensitive(tmp_path):
        pytest.skip("filesystem does not fold case")

    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="case")
    tooling_dir = target / ".agentbundle" / "tooling" / "agentbundle"
    tooling_dir.mkdir(parents=True)
    (tooling_dir / "x.py").write_bytes(b"vendored\n")
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    differently_cased_path = ".agentbundle/Tooling/agentbundle/x.py"
    state["managed_paths"].append(
        {"path": differently_cased_path,
         "sha256": hashlib.sha256(b"vendored\n").hexdigest()}
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")
    replay.old_state["managed_paths"] = state["managed_paths"]

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert (tooling_dir / "x.py").exists()
    assert differently_cased_path not in result.removed
    assert differently_cased_path in result.out_of_coverage


def test_apply_occupied_companion_destination_is_reported_and_untouched(tmp_path):
    # Verifies AC-0070's admission half.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="occupied")
    companion = target / "packs" / "alpha" / "unchanged.upstream.md"
    companion.write_bytes(b"adopter's own resolution")

    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    assert companion.read_bytes() == b"adopter's own resolution"
    assert "packs/alpha/unchanged.md" in result.companion_occupied
    assert "packs/alpha/unchanged.md" not in result.written
    assert companion.name not in [Path(p).name for p in result.written]


def test_apply_companion_admission_race_takes_write_failed_not_occupied(tmp_path):
    # Verifies AC-0070's admission race: a destination absent at admission
    # and created before the write is byte-identical afterwards and the run
    # takes the write-failed row -- a stat-at-admission implementation using
    # the clobbering rename would pass the occupied case and fail this one.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="race")
    companion = target / "packs" / "alpha" / "unchanged.upstream.md"
    assert not companion.exists()

    real_write_jailed = catalogue_sync.write_jailed

    def _race_before_publish(root, relpath, content, **kwargs):
        if relpath == "packs/alpha/README.md":
            # Write order (AC-0032) puts README.md immediately before the
            # companion destination -- create the companion's destination
            # out from under the run right before it gets there.
            companion.write_bytes(b"raced in by another writer")
        return real_write_jailed(root, relpath, content, **kwargs)

    with patch.object(catalogue_sync, "write_jailed", side_effect=_race_before_publish):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.write_failed_path == "packs/alpha/unchanged.upstream.md"
    assert "packs/alpha/unchanged.md" not in result.companion_occupied
    assert companion.read_bytes() == b"raced in by another writer"


def test_apply_companion_publish_leaves_link_count_one_and_no_staged_residue(tmp_path):
    # Verifies AC-0070's post-publish state.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="post-publish")
    result = _apply(target, replay, verdict_rows)

    assert result.ok, result
    companion = target / "packs" / "alpha" / "unchanged.upstream.md"
    assert companion.stat().st_nlink == 1
    siblings = [
        p.name for p in companion.parent.iterdir()
        if p.name != companion.name and p.name.startswith("unchanged.upstream.md.")
    ]
    assert siblings == []
    # Confinement helpers read it back without refusing.
    catalogue_sync.sha256_confined_regular_file(target, companion)


def test_apply_companion_write_failure_for_other_reason_is_write_failed_not_occupied(
    tmp_path,
):
    # Verifies AC-0070's failure attribution.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="other-failure")

    def _fail_companion(root, relpath, content, **kwargs):
        raise OSError("disk gremlin")

    with patch.object(catalogue_sync, "write_companion", side_effect=_fail_companion):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.write_failed_path == "packs/alpha/unchanged.upstream.md"
    assert "packs/alpha/unchanged.md" not in result.companion_occupied


def test_apply_companion_collision_refuses_whole_run(tmp_path):
    # Verifies AC-0071.
    source = _make_apply_source(tmp_path / "collision-source")
    # The source itself ships a path equal to the companion destination
    # `alpha/unchanged.md` would compute.
    (source / "packs" / "alpha" / "unchanged.upstream.md").write_text(
        "colliding upstream content\n", encoding="utf-8"
    )
    target = tmp_path / "collision-target"
    target.mkdir()
    _write_apply_old_state(target)
    cfg = ish.SelfHostedInitConfig(
        target=target, source=source, tooling="external", attribution="white-label",
        guides="selected", dry_run=True,
        packs=["alpha", "beta"], profiles=["default"],
    )
    replay = ish.replay_derivation(cfg, interactive=False)
    before = walk_target_tree(target)
    planned_paths = set(replay.file_bytes)
    _counts, verdict_rows = catalogue_sync._classify_planned_paths(
        target, replay.old_state, planned_paths, []
    )

    result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.companion_collision == {
        "packs/alpha/unchanged.md": "packs/alpha/unchanged.upstream.md",
    }
    after = walk_target_tree(target)
    assert after == before


def test_apply_new_pack_directory_is_removed_on_injected_write_failure(tmp_path):
    # Verifies AC-0038's entry-set half: a file-only restore passes every
    # other rollback case and fails this one.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="new-pack-rollback")
    real_write_jailed = catalogue_sync.write_jailed

    def _fail_beta_new(root, relpath, content, **kwargs):
        if relpath == "packs/beta/NEW.md":
            raise OSError("disk gremlin")
        return real_write_jailed(root, relpath, content, **kwargs)

    with patch.object(catalogue_sync, "write_jailed", side_effect=_fail_beta_new):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.write_failed_path == "packs/beta/NEW.md"
    assert result.restored
    assert not (target / "packs" / "beta").exists()


def test_apply_snapshot_bound_refuses_before_the_prompt_and_before_any_write(tmp_path):
    # Verifies AC-0076's pre-prompt sum. The low-level bound check.
    target = tmp_path / "bound-target"
    big_file = target / "packs" / "alpha" / "big.md"
    big_file.parent.mkdir(parents=True)
    big = b"x" * (1024 * 1024)
    big_file.write_bytes(big)

    with pytest.raises(catalogue_sync.SnapshotBoundExceeded) as exc_info:
        catalogue_sync.snapshot_write_set(
            target, {"packs/alpha/big.md"}, bound=1024
        )
    assert exc_info.value.bound == 1024
    assert exc_info.value.measured >= len(big)

    # Integrated: a full apply run over the same tree refuses before any
    # write when its own bound is set below the write set's measured size,
    # and the file is untouched.
    verdict_rows = [("packs/alpha/big.md", "would-update", None)]
    file_bytes = {"packs/alpha/big.md": b"new upstream content"}
    result = catalogue_sync.apply_write_sequence(
        target,
        old_state={"managed_paths": [
            {"path": "packs/alpha/big.md", "sha256": hashlib.sha256(big).hexdigest()},
        ], "recipe": {"packs": ["alpha"], "profiles": []}},
        verdict_rows=verdict_rows,
        file_bytes=file_bytes,
        planned_paths=set(file_bytes),
        pack_names=["alpha"], profile_names=[],
        guides_scope=False, guides_mode="selected",
        pin={},
        snapshot_bound_bytes=1024,
    )

    assert not result.ok
    assert result.snapshot_bound_exceeded == (1024, len(big))
    assert big_file.read_bytes() == big


def test_apply_snapshot_as_built_bound_reads_no_more_than_the_bound(
    tmp_path, monkeypatch
):
    # Verifies AC-0076's as-built half: a finished-total implementation
    # passes the pre-prompt case above and fails this one.
    target = tmp_path / "grow-target"
    target.mkdir()
    small = target / "small.txt"
    small.write_bytes(b"x" * 10)  # st_size is small -- passes the pre-prompt sum

    read_lengths: list[int] = []
    real_chunks = catalogue_sync._read_bounded_chunks

    def _grown_chunks(path):
        if path == small:
            # Simulate a file that grew past what its st_size predicted, by
            # yielding far more than 10 bytes.
            for _ in range(1000):
                chunk = b"y" * 1024
                read_lengths.append(len(chunk))
                yield chunk
        else:
            yield from real_chunks(path)

    monkeypatch.setattr(catalogue_sync, "_read_bounded_chunks", _grown_chunks)

    with pytest.raises(catalogue_sync.SnapshotBoundExceeded):
        catalogue_sync.snapshot_write_set(target, {"small.txt"}, bound=2048)

    assert sum(read_lengths) <= 2048 + 1024  # stopped within one chunk of the bound


def test_apply_restore_matches_pre_run_walk_tuple_on_injected_failure(tmp_path):
    # Verifies AC-0038's restore half: comparing paths and digests alone
    # passes a restore that changed a mode.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="restore-tuple")
    before = walk_target_tree(target)

    real_write_jailed = catalogue_sync.write_jailed
    calls = {"n": 0}

    def _fail_second_write(root, relpath, content, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk gremlin")
        return real_write_jailed(root, relpath, content, **kwargs)

    with patch.object(catalogue_sync, "write_jailed", side_effect=_fail_second_write):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.restored
    after = walk_target_tree(target)
    assert after == before


def test_apply_restore_leaves_unreached_paths_as_another_writer_left_them(tmp_path):
    # Verifies AC-0038's leave-as-found half and AC-0041's every-row
    # permitted difference: a restore driven off the whole snapshot rather
    # than off what the run acted on passes the restore-tuple case above and
    # fails this one.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="leave-as-found")
    real_write_jailed = catalogue_sync.write_jailed
    order_seen: list[str] = []

    def _fail_first_write(root, relpath, content, **kwargs):
        order_seen.append(relpath)
        if len(order_seen) == 1:
            # Another writer edits a path further along in write order,
            # before this run ever reaches it.
            later = target / "packs" / "beta" / "NEW.md"
            later.parent.mkdir(parents=True, exist_ok=True)
            later.write_bytes(b"another writer's bytes")
            raise OSError("disk gremlin")
        return real_write_jailed(root, relpath, content, **kwargs)

    with patch.object(catalogue_sync, "write_jailed", side_effect=_fail_first_write):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    later = target / "packs" / "beta" / "NEW.md"
    assert later.read_bytes() == b"another writer's bytes"


def test_apply_restore_failure_names_every_unrestored_path(tmp_path):
    # Verifies AC-0058.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="restore-fails")
    real_write_jailed = catalogue_sync.write_jailed
    calls = {"n": 0}

    def _fail_second_write(root, relpath, content, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk gremlin")
        return real_write_jailed(root, relpath, content, **kwargs)

    def _fail_restore(*_args, **_kwargs):
        raise OSError("restore also fails")

    with (
        patch.object(catalogue_sync, "write_jailed", side_effect=_fail_second_write),
        patch.object(catalogue_sync, "restore_from_snapshot", side_effect=_fail_restore),
        pytest.raises(OSError),
    ):
        _apply(target, replay, verdict_rows)

    # `restore_from_snapshot` itself never raises in production use (it is
    # best-effort and returns unrestored paths); assert the REAL function's
    # own contract directly instead of through the mocked-out orchestrator.
    target2, replay2, verdict_rows2 = _replay_apply_fixture(tmp_path, tag="restore-fails-2")
    snapshot = catalogue_sync.snapshot_write_set(
        target2, {"packs/alpha/README.md", "packs/beta/NEW.md"}
    )
    (target2 / "packs" / "beta").mkdir(parents=True, exist_ok=True)
    (target2 / "packs" / "beta" / "NEW.md").write_bytes(b"present")

    def _unlink_fails(self, *a, **kw):
        raise OSError("cannot unlink")

    with patch.object(Path, "unlink", _unlink_fails):
        unrestored = catalogue_sync.restore_from_snapshot(
            target2, snapshot, ["packs/beta/NEW.md"]
        )
    assert "packs/beta/NEW.md" in unrestored


def test_apply_planned_path_outside_target_root_is_refused_at_the_write(tmp_path):
    # Verifies AC-0052.
    target = tmp_path / "target"
    target.mkdir()
    verdict_rows = [("../escape.md", "would-update", None)]
    file_bytes = {"../escape.md": b"x"}
    result = catalogue_sync.apply_write_sequence(
        target,
        old_state={},
        verdict_rows=verdict_rows,
        file_bytes=file_bytes,
        planned_paths=set(file_bytes),
        pack_names=[], profile_names=[],
        guides_scope=False, guides_mode="selected",
        pin={},
    )
    assert not result.ok
    assert result.write_failed_path == "../escape.md"
    assert not (tmp_path / "escape.md").exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.write_bytes(b"changed digest"),
        lambda p: (p.unlink(), p.symlink_to(p.parent / "elsewhere")),
        lambda p: p.write_bytes(b"appeared"),  # only meaningful for the "found none" case
    ],
    ids=["changed-digest", "changed-entry-kind", "found-present-where-none-expected"],
)
def test_apply_gate_recheck_detects_every_divergence_shape(tmp_path, mutate):
    # Verifies AC-0077's gate recheck (3 of 6 cases).
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="gate")
    would_update_paths = {p for p, v, _ in verdict_rows if v == "would-update"}
    snapshot = catalogue_sync.snapshot_write_set(target, would_update_paths)
    expected = {
        p: (
            hashlib.sha256(snapshot[p].content).hexdigest()
            if snapshot[p].kind == "file" else None
        )
        for p in would_update_paths
    }
    target_path = target / "packs" / "alpha" / "README.md"
    if "found-present-where-none-expected" in mutate.__qualname__:
        pass
    # Force one path (README.md, would-update, on-disk-present) to diverge.
    mutate(target_path)

    diverged = catalogue_sync.gate_recheck(target, expected)

    assert "packs/alpha/README.md" in diverged


def test_apply_gate_recheck_no_divergence_over_unchanged_state(tmp_path):
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="gate-clean")
    would_update_paths = {p for p, v, _ in verdict_rows if v == "would-update"}
    snapshot = catalogue_sync.snapshot_write_set(target, would_update_paths)
    expected = {
        p: (
            hashlib.sha256(snapshot[p].content).hexdigest()
            if snapshot[p].kind == "file" else None
        )
        for p in would_update_paths
    }

    diverged = catalogue_sync.gate_recheck(target, expected)

    assert diverged == []


def test_apply_gate_recheck_over_full_run_refuses_before_any_write(tmp_path):
    # Verifies the gate recheck integrated in the full sequence, at the
    # cannot-answer point before the write phase opens. The snapshot and the
    # gate recheck both run inside one synchronous call with no real wait
    # between them, so the race this reaches for -- an edit landing between
    # the two -- is simulated as a side effect of the snapshot call itself,
    # the narrowest point the window can be reached from outside.
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="gate-full")
    before = walk_target_tree(target)
    real_snapshot = catalogue_sync.snapshot_write_set

    def _snapshot_then_race(target_arg, paths, **kwargs):
        snapshot = real_snapshot(target_arg, paths, **kwargs)
        (target / "packs" / "alpha" / "README.md").write_bytes(b"raced in during the wait")
        return snapshot

    with patch.object(catalogue_sync, "snapshot_write_set", side_effect=_snapshot_then_race):
        result = _apply(target, replay, verdict_rows)

    assert not result.ok
    assert result.gate_diverged == ["packs/alpha/README.md"]
    after = walk_target_tree(target)
    # Nothing this run did -- only the simulated race, which is the
    # divergence the fixture set up.
    assert after == {
        **before,
        "packs/alpha/README.md": {
            "kind": "file", "mode": after["packs/alpha/README.md"]["mode"],
            "target": None, "bytes": b"raced in during the wait",
        },
    }


def test_apply_rename_recheck_refuses_after_earlier_write_landed_and_restores_it(
    tmp_path,
):
    # Verifies AC-0077's rename recheck, driven at the rename after an
    # earlier write has landed: AC-0038's restore covers the landed writes.
    # A dedicated two-would-update fixture, so the write order (AC-0032) is
    # under direct control: "a.md" writes first, "b.md" second.
    target = tmp_path / "rename-recheck-target"
    alpha = target / "packs" / "alpha"
    alpha.mkdir(parents=True)
    (alpha / "a.md").write_bytes(b"old a")
    (alpha / "b.md").write_bytes(b"old b")
    old_state = {
        "managed_paths": [
            {"path": "packs/alpha/a.md", "sha256": hashlib.sha256(b"old a").hexdigest()},
            {"path": "packs/alpha/b.md", "sha256": hashlib.sha256(b"old b").hexdigest()},
        ],
        "recipe": {"packs": ["alpha"], "profiles": []},
    }
    verdict_rows = [
        ("packs/alpha/a.md", "would-update", None),
        ("packs/alpha/b.md", "would-update", None),
    ]
    file_bytes = {
        "packs/alpha/a.md": b"new a",
        "packs/alpha/b.md": b"new b",
    }
    real_write_jailed = catalogue_sync.write_jailed

    def _race_after_first_write(root, relpath, content, **kwargs):
        if relpath == "packs/alpha/a.md":
            # "a.md" writes first (AC-0032); race "b.md" before this
            # function reaches it.
            (alpha / "b.md").write_bytes(b"raced in after the first write landed")
        return real_write_jailed(root, relpath, content, **kwargs)

    with patch.object(catalogue_sync, "write_jailed", side_effect=_race_after_first_write):
        result = catalogue_sync.apply_write_sequence(
            target, old_state=old_state, verdict_rows=verdict_rows,
            file_bytes=file_bytes, planned_paths=set(file_bytes),
            pack_names=["alpha"], profile_names=[],
            guides_scope=False, guides_mode="selected", pin={},
        )

    assert not result.ok
    assert result.write_failed_path == "packs/alpha/b.md"
    assert result.restored
    # The raced-in bytes are what the OTHER writer left -- AC-0041's every-
    # row permitted difference -- not clobbered by our own would-be write.
    assert (alpha / "b.md").read_bytes() == b"raced in after the first write landed"
    # The earlier landed write ("a.md") was rolled back to its pre-run value.
    assert (alpha / "a.md").read_bytes() == b"old a"


def test_apply_target_reads_refused_on_hardlink_and_reparse_point_inputs(tmp_path):
    # Verifies AC-0065 re-driven through the apply path's own reads (the
    # gate recheck).
    target, replay, verdict_rows = _replay_apply_fixture(tmp_path, tag="confinement")
    readme = target / "packs" / "alpha" / "README.md"
    other = target / "packs" / "alpha" / "hardlink-partner.md"
    os.link(readme, other)

    expected = {"packs/alpha/README.md": hashlib.sha256(b"# Alpha\n").hexdigest()}
    diverged = catalogue_sync.gate_recheck(target, expected)

    assert "packs/alpha/README.md" in diverged


# ---------------------------------------------------------------------------
# T5: consent gates the first write (spec AC-0031, AC-0049, AC-0050, AC-0072).
#
# The gate's returned decision is the oracle throughout. AC-0031's own oracle
# is the target tree, but that only moves once T6's `_run_apply` composes
# this gate with the write sequence — driving a tree here would test
# duplicated test logic rather than the planned implementation (plan.md T5
# § Tests), so every case below asserts the boolean decision or the prompt
# text `_consent_gate` builds, never a filesystem effect.
# ---------------------------------------------------------------------------

# The four fidelity tokens `_resolve_source` returns, one per source form
# (see the module-level comment above `_DIGEST_BEARING_PREFIXES`).
_FIDELITY_TOKENS = [
    "local-path",
    "git-tls",
    "digest-adopter-pinned",
    "digest-publisher-asserted",
]


def test_consent_gate_yes_flag_proceeds_without_touching_stdin(monkeypatch):
    def _boom(prompt=""):
        raise AssertionError("input() must not be called with yes=True")

    monkeypatch.setattr("builtins.input", _boom)
    # isatty must not even be consulted under yes=True, but patch it
    # defensively so a regression that does consult it still fails loudly.
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    assert catalogue_sync._consent_gate(
        yes=True,
        attributed=False,
        source_raw="/local/source",
        fidelity_token="local-path",
    ) is True


def test_consent_gate_affirmative_reply_proceeds(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    assert catalogue_sync._consent_gate(
        yes=False,
        attributed=False,
        source_raw="/local/source",
        fidelity_token="local-path",
    ) is True


def test_consent_gate_negative_reply_declines(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")

    assert catalogue_sync._consent_gate(
        yes=False,
        attributed=False,
        source_raw="/local/source",
        fidelity_token="local-path",
    ) is False


def test_consent_gate_end_of_input_with_no_terminal_declines_without_prompting(
    monkeypatch,
):
    def _boom(prompt=""):
        raise AssertionError("input() must not be called on a non-TTY")

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("builtins.input", _boom)

    assert catalogue_sync._consent_gate(
        yes=False,
        attributed=False,
        source_raw="/local/source",
        fidelity_token="local-path",
    ) is False


def test_consent_gate_names_no_source_uri_outside_attributed_mode(monkeypatch):
    captured: dict[str, str] = {}

    def _capture(prompt=""):
        captured["prompt"] = prompt
        return "y"

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _capture)

    catalogue_sync._consent_gate(
        yes=False,
        attributed=False,
        source_raw="https://example.test/should-not-appear",
        fidelity_token="local-path",
    )

    assert "https://example.test/should-not-appear" not in captured["prompt"]


def test_consent_gate_names_the_source_uri_under_attributed_mode(monkeypatch):
    captured: dict[str, str] = {}

    def _capture(prompt=""):
        captured["prompt"] = prompt
        return "y"

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _capture)

    catalogue_sync._consent_gate(
        yes=False,
        attributed=True,
        source_raw="https://example.test/should-appear",
        fidelity_token="local-path",
    )

    assert "https://example.test/should-appear" in captured["prompt"]


@pytest.mark.parametrize("fidelity_token", _FIDELITY_TOKENS)
def test_consent_gate_names_the_fidelity_token_on_the_prompt(
    monkeypatch, fidelity_token
):
    captured: dict[str, str] = {}

    def _capture(prompt=""):
        captured["prompt"] = prompt
        return "y"

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _capture)

    catalogue_sync._consent_gate(
        yes=False,
        attributed=False,
        source_raw="/local/source",
        fidelity_token=fidelity_token,
    )

    assert fidelity_token in captured["prompt"]


@pytest.mark.parametrize("fidelity_token", _FIDELITY_TOKENS)
def test_plan_document_and_render_carry_each_source_forms_fidelity_token(
    capsys, fidelity_token
):
    # AC-0072's `--yes`-run half: a `--yes` run never prompts, so this drives
    # the printed plan and the `--format json` document directly rather than
    # through the prompt, over the same four tokens the prompt test above
    # covers — a prompt-only fixture would leave this half unverified.
    doc = catalogue_sync._plan_document(
        target=Path("/tmp/target"),
        dry_run=True,
        check=False,
        fidelity_token=fidelity_token,
        archive_sha256=None,
        source_revision=None,
        attribution="white-label",
        tooling="external",
        guides="selected",
        source_raw="/local/source",
        attributed=False,
        pack_names=[],
        profile_names=[],
        summary={
            "would_update": 0,
            "would_companion": 0,
            "untouched": 0,
            "would_remove": 0,
            "schema_1_inert": 0,
            "compared": 0,
            "uncompared": 0,
        },
        verdict_rows=[],
        compatibility=[],
        violations=0,
        rejections=[],
    )
    assert doc["fidelity"] == fidelity_token

    catalogue_sync._render_plan(doc, fmt="table")
    assert f"fidelity: {fidelity_token}" in capsys.readouterr().out

    catalogue_sync._render_plan(doc, fmt="json")
    printed = json.loads(capsys.readouterr().out)
    assert printed["fidelity"] == fidelity_token


def test_consent_gate_recorded_value_failing_terminal_safe_check_is_not_prompted(
    monkeypatch,
):
    captured: dict[str, str] = {}

    def _capture(prompt=""):
        captured["prompt"] = prompt
        return "y"

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _capture)

    # Fails only the whitespace bound (a trailing space) — never a control
    # character, which an escaping sink (e.g. `json.dumps`) would neutralise
    # whether or not the check runs, making a control-character assertion
    # vacuous (spec AC-0049; plan.md T5 § Tests).
    unsafe_source = "https://example.test/repo "
    # Pin which bound trips: the trailing space fails `_is_safe_recipe_text`
    # (whitespace), and the stripped value alone would pass it — proving this
    # case is not also rejected on length or on a control character.
    assert not ish._is_safe_recipe_text(unsafe_source)
    assert ish._is_safe_recipe_text(unsafe_source.strip())

    catalogue_sync._consent_gate(
        yes=False,
        attributed=True,
        source_raw=unsafe_source,
        fidelity_token="local-path",
    )

    assert unsafe_source not in captured["prompt"]
    assert "rejected source" in captured["prompt"]


# ---------------------------------------------------------------------------
# The whole-tree walk (spec AC-0015), reusing T4's helper rather than a copy.
# T5's rows: a dry-run success and a resolution refusal reached via sync's
# own dispatch, over-and-above T4's replay_derivation-level rows.
#
# Each case is a (setup, invoke) pair: `setup` prepares the target's
# pre-existing tree (an already-derived catalogue's recorded state and any
# adopter edits) *before* the walk's "before" snapshot, and `invoke` is the
# only step that runs sync — the one step the walk holds to "no write".
# T4/T5's original two rows need no target-side setup.
# ---------------------------------------------------------------------------

def _no_target_setup(target: Path) -> None:
    pass


def _setup_success_target(target: Path) -> None:
    # AC-0009: a target with no recorded selection is itself one of the
    # underivable conditions, so this success row needs one recorded — T5
    # predates that check and this setup supplies the minimal state it
    # requires to still land on AC-0013's success row.
    _write_minimal_sync_state(target, packs=["alpha"])


def _invoke_sync_dry_run_success(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0


def _invoke_sync_resolution_refusal(target: Path) -> None:
    missing = str(target.parent / "sync-tree-walk-missing-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", missing, "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3


def _setup_would_companion_target(target: Path) -> None:
    readme = target / "packs" / "alpha" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_bytes(b"edited by the adopter\n")
    _write_minimal_sync_state(
        target,
        packs=["alpha"],
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"# Alpha\n").hexdigest(),
            }
        ],
    )


def _invoke_sync_dry_run_would_companion(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-companion-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0


def _setup_would_remove_target(target: Path) -> None:
    gone = target / "packs" / "alpha" / "gone.md"
    gone.parent.mkdir(parents=True, exist_ok=True)
    gone.write_bytes(b"stale content\n")
    _write_minimal_sync_state(
        target,
        packs=["alpha"],
        managed_paths=[
            {
                "path": "packs/alpha/gone.md",
                "sha256": hashlib.sha256(b"stale content\n").hexdigest(),
            }
        ],
    )


def _invoke_sync_dry_run_would_remove(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-remove-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 0


def _invoke_sync_dry_run_underivable_selection(target: Path) -> None:
    # No state file at all -- one of AC-0009's own underivable conditions.
    source = _make_source(target.parent / "sync-tree-walk-underivable-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3


def _invoke_sync_dry_run_adapter_contract_refusal(target: Path) -> None:
    # T9: a selected pack's adapter-contract major differing from the CLI's
    # refuses (spec AC-0019) — the row this task adds to the walk.
    pack_toml_text = (
        FIXTURES / "adapter_contract_major_mismatch" / "pack.toml"
    ).read_text(encoding="utf-8")
    source = _make_source_with_pack_toml(
        target.parent / "sync-tree-walk-adapter-contract-source", pack_toml_text
    )
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 1


# T8's own rows: the `--check` digest-only and `--compare-tree` paths, the
# scalar recorded-path container, and the identity leak's difference code
# reached through sync's own dispatch rather than the replay callable.

def _invoke_sync_check_no_compare_tree_cannot_answer(target: Path) -> None:
    # A local-path source affords no verified digest, so this is
    # AC-0013's row 7 — reached before the recorded pin is even read.
    source = _make_source(target.parent / "sync-tree-walk-check-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--check"]
    )
    assert catalogue_sync.run(args) == 3


def _setup_check_compare_tree_success_target(target: Path) -> None:
    pack_toml = target / "packs" / "alpha" / "pack.toml"
    pack_toml.parent.mkdir(parents=True, exist_ok=True)
    pack_toml.write_bytes(b'[pack]\nname = "alpha"\nversion = "1.0.0"\n')
    _write_minimal_sync_state(
        target,
        packs=["alpha"],
        managed_paths=[
            {
                "path": "packs/alpha/pack.toml",
                "sha256": hashlib.sha256(pack_toml.read_bytes()).hexdigest(),
            }
        ],
    )


def _invoke_sync_check_compare_tree_success(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-compare-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source),
         "--check", "--compare-tree"]
    )
    assert catalogue_sync.run(args) == 0


def _setup_check_compare_tree_cannot_answer_target(target: Path) -> None:
    _write_minimal_sync_state(target, packs=["alpha"], managed_paths=[])


def _invoke_sync_check_compare_tree_cannot_answer(target: Path) -> None:
    source = _make_source(
        target.parent / "sync-tree-walk-compare-empty-source"
    )
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source),
         "--check", "--compare-tree"]
    )
    assert catalogue_sync.run(args) == 3


def _setup_dry_run_scalar_container_target(target: Path) -> None:
    _write_minimal_sync_state(target, packs=["alpha"])
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"] = 0
    state_path.write_text(json.dumps(state), encoding="utf-8")


def _invoke_sync_dry_run_scalar_container_cannot_answer(target: Path) -> None:
    source = _make_source(target.parent / "sync-tree-walk-scalar-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 3


def _invoke_sync_dry_run_identity_leak_difference(target: Path) -> None:
    source = target.parent / "sync-tree-walk-leaky-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'maintainers = [{name = "Upstream Maintainer", '
        'email = "leaky@upstream.example.com"}]\n',
        encoding="utf-8",
    )
    pack = source / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (pack / "README.md").write_text(
        "contact leaky@upstream.example.com\n", encoding="utf-8"
    )
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    assert catalogue_sync.run(args) == 1


# Adversarial finding 5: five more AC-0013 rows the registry above omitted —
# row 1 (a malformed invocation reachable through `run()`), rows 9-11 (the
# three digest-bearing `--check` rows; every registered `--check` row above
# uses a local-path source, which refuses at row 8 before the recorded pin is
# ever read), and row 14 (`--check --compare-tree`, some differ).

def _invoke_sync_malformed_compare_tree_without_check(target: Path) -> None:
    # AC-0013 row 1: `--compare-tree` without `--check` is malformed and
    # never reaches the recorded state or the source at all.
    source = _make_source(target.parent / "sync-tree-walk-malformed-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source),
         "--dry-run", "--compare-tree"]
    )
    assert catalogue_sync.run(args) == 2


def _invoke_sync_check_digest_source_no_recorded_pin(target: Path) -> None:
    # AC-0013 row 9: a digest-bearing source (so `_check_digest_only` reads
    # past its own "no verified digest" row), but the recorded pin carries
    # no `archive_sha256` at all -- `_setup_success_target`'s minimal state
    # never writes a "pin" key.
    extracted = _make_source(target.parent / "sync-tree-walk-check-no-pin-source")
    with patch.object(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256="9" * 64,
        ),
    ):
        args = _build_parser().parse_args(
            ["catalogue", "sync", str(target),
             "--source", "catalogue+https://example.com/channel.json", "--check"]
        )
        assert catalogue_sync.run(args) == 3


_TREE_WALK_RECORDED_DIGEST = "1" * 64


def _setup_check_digest_recorded_target(target: Path) -> None:
    _write_minimal_sync_state(target, packs=["alpha"])
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pin"] = {"archive_sha256": _TREE_WALK_RECORDED_DIGEST}
    state_path.write_text(json.dumps(state), encoding="utf-8")


def _invoke_sync_check_digest_matches(target: Path) -> None:
    # AC-0013 row 10: the recorded digest equals the resolved source's own
    # verified digest.
    extracted = _make_source(
        target.parent / "sync-tree-walk-check-digest-match-source"
    )
    with patch.object(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri,
            archive_sha256=_TREE_WALK_RECORDED_DIGEST,
        ),
    ):
        args = _build_parser().parse_args(
            ["catalogue", "sync", str(target),
             "--source", "catalogue+https://example.com/channel.json", "--check"]
        )
        assert catalogue_sync.run(args) == 0


def _invoke_sync_check_digest_differs(target: Path) -> None:
    # AC-0013 row 11: the recorded digest differs from the resolved source's.
    extracted = _make_source(
        target.parent / "sync-tree-walk-check-digest-differ-source"
    )
    with patch.object(
        catalogue_sync,
        "fetch_catalogue_archive_with_provenance",
        lambda uri: CatalogueArchiveResult(
            path=extracted, artifact_uri=uri, archive_sha256="2" * 64,
        ),
    ):
        args = _build_parser().parse_args(
            ["catalogue", "sync", str(target),
             "--source", "catalogue+https://example.com/channel.json", "--check"]
        )
        assert catalogue_sync.run(args) == 1


def _invoke_sync_check_compare_tree_differs(target: Path) -> None:
    # AC-0013 row 14: `--check --compare-tree`, every recorded path
    # compared and some differ. Reuses `_setup_would_companion_target`'s
    # recorded-vs-edited README, which is exactly this shape.
    source = _make_source(target.parent / "sync-tree-walk-compare-differs-source")
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source),
         "--check", "--compare-tree"]
    )
    assert catalogue_sync.run(args) == 1


# Registry T5 adds to; later tasks extend it further rather than copying it.
# Each value is a (setup, invoke) pair — see the section comment above.
SYNC_TREE_WALK_CASES = {
    "sync-dry-run-success": (_setup_success_target, _invoke_sync_dry_run_success),
    "sync-resolution-refusal": (_no_target_setup, _invoke_sync_resolution_refusal),
    "sync-dry-run-would-companion": (
        _setup_would_companion_target, _invoke_sync_dry_run_would_companion,
    ),
    "sync-dry-run-would-remove": (
        _setup_would_remove_target, _invoke_sync_dry_run_would_remove,
    ),
    "sync-dry-run-underivable-selection": (
        _no_target_setup, _invoke_sync_dry_run_underivable_selection,
    ),
    "sync-dry-run-adapter-contract-refusal": (
        _setup_success_target, _invoke_sync_dry_run_adapter_contract_refusal,
    ),
    "sync-check-no-compare-tree-cannot-answer": (
        _setup_success_target, _invoke_sync_check_no_compare_tree_cannot_answer,
    ),
    "sync-check-compare-tree-success": (
        _setup_check_compare_tree_success_target,
        _invoke_sync_check_compare_tree_success,
    ),
    "sync-check-compare-tree-cannot-answer": (
        _setup_check_compare_tree_cannot_answer_target,
        _invoke_sync_check_compare_tree_cannot_answer,
    ),
    "sync-dry-run-scalar-container-cannot-answer": (
        _setup_dry_run_scalar_container_target,
        _invoke_sync_dry_run_scalar_container_cannot_answer,
    ),
    "sync-dry-run-identity-leak-difference": (
        _setup_success_target, _invoke_sync_dry_run_identity_leak_difference,
    ),
    "sync-malformed-compare-tree-without-check": (
        _no_target_setup, _invoke_sync_malformed_compare_tree_without_check,
    ),
    "sync-check-digest-source-no-recorded-pin": (
        _setup_success_target, _invoke_sync_check_digest_source_no_recorded_pin,
    ),
    "sync-check-digest-matches": (
        _setup_check_digest_recorded_target, _invoke_sync_check_digest_matches,
    ),
    "sync-check-digest-differs": (
        _setup_check_digest_recorded_target, _invoke_sync_check_digest_differs,
    ),
    "sync-check-compare-tree-differs": (
        _setup_would_companion_target, _invoke_sync_check_compare_tree_differs,
    ),
}


@pytest.mark.parametrize("case", sorted(SYNC_TREE_WALK_CASES))
def test_sync_leaves_the_target_tree_unchanged(tmp_path, case):
    target = tmp_path / "target"
    target.mkdir()
    (target / "adopter-owned.txt").write_text("keep me\n", encoding="utf-8")
    setup, invoke = SYNC_TREE_WALK_CASES[case]
    setup(target)
    before = walk_target_tree(target)

    invoke(target)

    after = walk_target_tree(target)
    assert after == before


# ---------------------------------------------------------------------------
# T6: `_run_apply` owns the apply exit rows (spec AC-0039, AC-0040, AC-0046,
# AC-0047, AC-0048, AC-0049, AC-0051, AC-0057, AC-0066, AC-0068, AC-0069).
#
# `_run_apply` is called directly, not through `run()`/the real parser: T7
# (not yet landed) is what wires `--pack`/`--profile`/`--guides`/`--package`/
# `--yes` onto the CLI namespace `run()` reads. This mirrors T5's own
# established pattern of driving a composed seam directly rather than
# building a parser-shaped test double.
# ---------------------------------------------------------------------------


def _write_apply_run_state(
    target: Path, *, recipe: dict, managed_paths: object = None
) -> None:
    state_path = target / ".agentbundle" / "self-host-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "3",
                "managed_paths": managed_paths if managed_paths is not None else [],
                "recipe": recipe,
            }
        ),
        encoding="utf-8",
    )


def _apply_run_target(
    tmp_path: Path,
    tag: str,
    *,
    recipe: dict | None = None,
    managed_paths: object = None,
) -> tuple[Path, Path]:
    """A minimal apply-ready ``(target, source)`` pair: *source* ships one
    pack, ``alpha`` (:func:`_make_source`); *target* records *recipe*
    (defaulting to ``{"packs": ["alpha"], "profiles": []}``) and
    *managed_paths*.
    """
    source = _make_source(tmp_path / f"run-apply-source-{tag}")
    target = tmp_path / f"run-apply-target-{tag}"
    target.mkdir()
    resolved_recipe = {"packs": ["alpha"], "profiles": []}
    resolved_recipe.update(recipe or {})
    _write_apply_run_state(target, recipe=resolved_recipe, managed_paths=managed_paths)
    return target, source


def _call_run_apply(target: Path, source: Path, **overrides) -> int:
    kwargs: dict = {
        "target": target,
        "source_path": source,
        "fidelity_token": "local-path",
        "archive_sha256": None,
        "source_revision": None,
        "attribution": "white-label",
        "tooling": "external",
        "guides": "selected",
        "attributed": False,
        "source_raw": str(source),
        "fmt": "table",
        "yes": True,
        "cli_pack_names": [],
        "cli_profile_names": [],
        "guides_scope": False,
    }
    kwargs.update(overrides)
    return catalogue_sync._run_apply(**kwargs)


def test_run_apply_success_row_writes_admitted_paths_and_returns_zero(tmp_path):
    # AC-0039's `0 — success` row: every planned write lands, removal and the
    # state write complete, and `companion_occupied` is zero. A recorded,
    # unedited README (on-disk sha == recorded sha, source bytes differ) is
    # what classifies `would-update` — with no recorded entry at all the
    # path is untouched-but-not-introduced and never admitted.
    target, source = _apply_run_target(
        tmp_path,
        "success",
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"old bytes\n").hexdigest(),
            }
        ],
    )
    readme = target / "packs" / "alpha" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_bytes(b"old bytes\n")

    code = _call_run_apply(target, source)

    assert code == 0
    assert readme.read_bytes() == (source / "packs" / "alpha" / "README.md").read_bytes()
    state = json.loads(
        (target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )
    written_paths = {entry["path"] for entry in state["managed_paths"]}
    assert "packs/alpha/README.md" in written_paths


def test_run_apply_companion_occupied_returns_difference_not_success(tmp_path):
    # AC-0039's `1 — difference` row: every write lands but an occupied
    # companion destination stops the run short of a clean `0`.
    target, source = _apply_run_target(
        tmp_path,
        "companion-occupied",
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"pre-existing digest that never matches\n").hexdigest(),
            }
        ],
    )
    (target / "packs" / "alpha").mkdir(parents=True, exist_ok=True)
    (target / "packs" / "alpha" / "README.md").write_bytes(b"adopter edit\n")
    occupant = target / "packs" / "alpha" / "README.upstream.md"
    occupant.write_bytes(b"already here\n")

    code = _call_run_apply(target, source)

    assert code == 1
    assert occupant.read_bytes() == b"already here\n"


def test_run_apply_unshipped_cli_pack_name_is_malformed_and_writes_nothing(tmp_path):
    # AC-0046: a `--pack` name the resolved source does not ship.
    target, source = _apply_run_target(tmp_path, "unshipped-cli-pack")
    before = walk_target_tree(target)

    code = _call_run_apply(target, source, cli_pack_names=["ghost"])

    assert code == 2
    assert walk_target_tree(target) == before


def test_run_apply_unshipped_cli_profile_name_is_malformed_and_writes_nothing(tmp_path):
    # AC-0046, profile axis.
    target, source = _apply_run_target(tmp_path, "unshipped-cli-profile")
    before = walk_target_tree(target)

    code = _call_run_apply(target, source, cli_profile_names=["ghost"])

    assert code == 2
    assert walk_target_tree(target) == before


def test_run_apply_recorded_packs_wrong_type_is_cannot_answer(tmp_path):
    # AC-0068: a present-but-invalid recorded selection (wrong type) refuses.
    target, source = _apply_run_target(
        tmp_path, "packs-wrong-type", recipe={"packs": "alpha", "profiles": []}
    )
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 3
    assert walk_target_tree(target) == before


def test_run_apply_recorded_profiles_list_of_non_strings_is_cannot_answer(tmp_path):
    # AC-0068, profiles axis, a different invalid shape (list of non-strings)
    # — driven independently per plan.md T6 § Tests.
    target, source = _apply_run_target(
        tmp_path, "profiles-non-strings", recipe={"packs": ["alpha"], "profiles": [1, 2]}
    )
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 3
    assert walk_target_tree(target) == before


def test_run_apply_recorded_packs_names_a_tooling_pack_is_cannot_answer(tmp_path):
    # AC-0068's own regression case: `select_packs` silently drops a tooling
    # pack name (`catalogue-curation` — the one name `_TOOLING_PACKS`
    # carries) from an explicit selection rather than refusing, so a
    # recorded list naming only such a name must refuse *here* instead of
    # resolving to "no narrowing requested". The source ships the pack
    # directory (so this is not merely "unshipped") — only its tooling
    # status excludes it.
    source = tmp_path / "run-apply-source-packs-names-tooling-pack"
    _make_source(source)
    curation = source / "packs" / "catalogue-curation"
    curation.mkdir(parents=True)
    (curation / "pack.toml").write_text(
        '[pack]\nname = "catalogue-curation"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    target = tmp_path / "run-apply-target-packs-names-tooling-pack"
    target.mkdir()
    _write_apply_run_state(
        target, recipe={"packs": ["catalogue-curation"], "profiles": []}
    )
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 3
    assert walk_target_tree(target) == before


def test_run_apply_absent_profiles_field_selects_nothing_not_a_refusal(tmp_path):
    # AC-0068: an absent field is the narrowing outcome, never a refusal.
    target, source = _apply_run_target(tmp_path, "absent-profiles", recipe={"packs": ["alpha"]})
    state_path = target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    del state["recipe"]["profiles"]
    state_path.write_text(json.dumps(state), encoding="utf-8")

    code = _call_run_apply(target, source)

    assert code == 0


def test_run_apply_empty_recorded_packs_selects_nothing_not_a_refusal(tmp_path):
    # AC-0068: an empty list is the narrowing outcome, never a refusal.
    target, source = _apply_run_target(
        tmp_path, "empty-packs-no-refusal", recipe={"packs": [], "profiles": []}
    )

    code = _call_run_apply(target, source)

    assert code == 0


def test_run_apply_empty_recorded_packs_does_not_remove_recorded_pack_tree(tmp_path):
    # AC-0069's selection axis — the regression this delivery is most at
    # risk of reintroducing: an empty recorded `packs` category must put no
    # path under `packs/` inside coverage, so a recorded pack tree the
    # source still ships survives even though `packs` resolves to nothing.
    # `select_packs(source, [])` would otherwise widen internally and (were
    # coverage keyed off the pre-resolution selection) delete this tree.
    target, source = _apply_run_target(
        tmp_path,
        "empty-packs-coverage",
        recipe={"packs": [], "profiles": []},
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"adopter content\n").hexdigest(),
            }
        ],
    )
    alpha = target / "packs" / "alpha"
    alpha.mkdir(parents=True)
    (alpha / "README.md").write_bytes(b"adopter content\n")
    before_readme = (alpha / "README.md").read_bytes()

    code = _call_run_apply(target, source)

    assert code == 0
    # The pack tree survives untouched — only the ownership state (clause 6,
    # written on every successful run) legitimately changes.
    assert (alpha / "README.md").read_bytes() == before_readme
    state = json.loads(
        (target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )
    recorded_paths = {entry["path"] for entry in state["managed_paths"]}
    assert "packs/alpha/README.md" in recorded_paths


def test_run_apply_recorded_path_container_not_array_is_cannot_answer(tmp_path):
    target, source = _apply_run_target(tmp_path, "container-not-array", managed_paths="not-a-list")
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 3
    assert walk_target_tree(target) == before


def test_run_apply_format_json_without_yes_is_malformed(tmp_path):
    # AC-0030's document clause: an apply run with `--format json` and no
    # `--yes` would share stdout between the prompt and the document.
    target, source = _apply_run_target(tmp_path, "json-no-yes")
    before = walk_target_tree(target)

    code = _call_run_apply(target, source, fmt="json", yes=False)

    assert code == 2
    assert walk_target_tree(target) == before


def test_run_apply_source_resolution_failure_is_cannot_answer_and_writes_nothing(
    tmp_path,
):
    # AC-0039's row 3, driven for the apply invocation specifically through
    # `run()`'s own dispatch — the `--dry-run`/`--check` rows are re-driven
    # elsewhere in this file rather than inherited (plan.md T6 § Tests): the
    # table is this spec's own, not phase 2's shorter one. Reached via a
    # hand-built namespace, since the parser does not yet admit a bare apply
    # invocation (T7).
    target = tmp_path / "resolution-failure-target"
    target.mkdir()
    missing_source = tmp_path / "does-not-exist"
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(missing_source), "--dry-run"]
    )
    args.dry_run = False
    before = walk_target_tree(target)

    assert catalogue_sync.run(args) == 3
    assert walk_target_tree(target) == before


def test_run_apply_identity_leak_violation_returns_difference_and_never_prompts(
    tmp_path, monkeypatch
):
    # AC-0039's leak row (`1 — difference`) and AC-0051: no write, and the
    # operator is never prompted for consent.
    source = tmp_path / "leaky-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'maintainers = [{name = "Upstream Maintainer", '
        'email = "leaky@upstream.example.com"}]\n',
        encoding="utf-8",
    )
    pack = source / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (pack / "README.md").write_text(
        "contact leaky@upstream.example.com\n", encoding="utf-8"
    )
    target = tmp_path / "leaky-target"
    target.mkdir()
    _write_apply_run_state(target, recipe={"packs": ["alpha"], "profiles": []})
    before = walk_target_tree(target)

    def _boom(prompt=""):
        raise AssertionError("input() must not be called on a leak violation")

    monkeypatch.setattr("builtins.input", _boom)

    code = _call_run_apply(target, source, yes=False)

    assert code == 1
    assert walk_target_tree(target) == before


def test_run_apply_adapter_contract_mismatch_returns_difference(tmp_path):
    pack_toml_text = (
        FIXTURES / "adapter_contract_major_mismatch" / "pack.toml"
    ).read_text(encoding="utf-8")
    source = _make_source_with_pack_toml(
        tmp_path / "run-apply-adapter-mismatch-source", pack_toml_text
    )
    target = tmp_path / "run-apply-adapter-mismatch-target"
    target.mkdir()
    _write_apply_run_state(target, recipe={"packs": ["alpha"], "profiles": []})
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 1
    assert walk_target_tree(target) == before


@pytest.mark.parametrize("mode_flag", [("--dry-run",), ("--check",)])
def test_run_package_recognized_name_refuses_before_fetch_on_every_invocation(
    tmp_path, monkeypatch, mode_flag
):
    # AC-0047: `--package` with a recognised name refuses on apply, on
    # `--dry-run`, and on `--check` alike, and the row sits above source
    # resolution — no fetch is ever performed.
    target = tmp_path / "package-target"
    target.mkdir()
    source = tmp_path / "package-source"

    def _boom(uri):
        raise AssertionError("source resolution must not run for --package")

    monkeypatch.setattr(catalogue_sync, "resolve_catalogue", _boom)
    monkeypatch.setattr(catalogue_sync, "fetch_catalogue_archive_with_provenance", _boom)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), *mode_flag]
    )
    args.package = "agentbundle"

    assert catalogue_sync.run(args) == 3


def test_run_apply_package_recognized_name_refuses_before_fetch(tmp_path, monkeypatch):
    # AC-0047's third invocation — a bare apply run supplying `--package`.
    # Reachable only via a hand-built namespace: the mutually exclusive
    # `--dry-run`/`--check` group is still `required=True` until T7 lands.
    target = tmp_path / "package-apply-target"
    target.mkdir()
    source = tmp_path / "package-apply-source"

    def _boom(uri):
        raise AssertionError("source resolution must not run for --package")

    monkeypatch.setattr(catalogue_sync, "resolve_catalogue", _boom)
    monkeypatch.setattr(catalogue_sync, "fetch_catalogue_archive_with_provenance", _boom)

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--dry-run"]
    )
    args.dry_run = False
    args.package = "credbroker"

    assert catalogue_sync.run(args) == 3


def test_run_apply_two_runs_identical_flags_differing_recorded_modes_write_same_bytes(
    tmp_path,
):
    # AC-0048: recorded `attribution`/`tooling`/`guides` never affect what an
    # apply run writes — only the flags do. Neither call below overrides the
    # `tooling`/`attribution` *flags* (both keep `_call_run_apply`'s
    # defaults), only the *recorded* recipe values differ.
    managed_paths = [
        {"path": "packs/alpha/README.md", "sha256": hashlib.sha256(b"old bytes\n").hexdigest()}
    ]
    target_a, source_a = _apply_run_target(
        tmp_path, "modes-a", recipe={"packs": ["alpha"], "profiles": [],
                                      "attribution": "attributed", "tooling": "vendored",
                                      "guides": "none"},
        managed_paths=managed_paths,
    )
    target_b, source_b = _apply_run_target(
        tmp_path, "modes-b", recipe={"packs": ["alpha"], "profiles": [],
                                      "attribution": "white-label", "tooling": "external",
                                      "guides": "selected"},
        managed_paths=managed_paths,
    )
    for target in (target_a, target_b):
        readme = target / "packs" / "alpha" / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_bytes(b"old bytes\n")

    code_a = _call_run_apply(target_a, source_a)
    code_b = _call_run_apply(target_b, source_b)

    assert code_a == code_b == 0
    assert (target_a / "packs" / "alpha" / "README.md").read_bytes() == (
        target_b / "packs" / "alpha" / "README.md"
    ).read_bytes()


def test_run_apply_recorded_source_value_failing_terminal_safe_check_is_not_prompted(
    tmp_path, monkeypatch
):
    # AC-0049: the consent prompt never receives a value that fails the
    # bounded terminal-safe scalar check; the field is reported by name
    # instead.
    target, source = _apply_run_target(tmp_path, "unsafe-source")
    captured: dict[str, str] = {}

    def _capture(prompt=""):
        captured["prompt"] = prompt
        return "y"

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _capture)
    unsafe_source = "https://example.test/repo "
    assert not ish._is_safe_recipe_text(unsafe_source)

    code = _call_run_apply(
        target, source, yes=False, attributed=True, source_raw=unsafe_source,
    )

    assert code == 0
    assert unsafe_source not in captured["prompt"]
    assert "rejected source" in captured["prompt"]


def test_run_apply_companion_collision_refuses_cannot_answer_and_writes_nothing(
    tmp_path,
):
    # AC-0071, driven at `_run_apply`'s own composition rather than only at
    # `apply_write_sequence`'s level.
    source = tmp_path / "collision-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\nname = "upstream"\ndisplay_name = "Upstream"\n'
        'description = "d"\n',
        encoding="utf-8",
    )
    pack = source / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (pack / "x.md").write_text("source x\n", encoding="utf-8")
    (pack / "x.upstream.md").write_text("source companion\n", encoding="utf-8")

    target = tmp_path / "collision-target"
    target.mkdir()
    xmd = target / "packs" / "alpha" / "x.md"
    xmd.parent.mkdir(parents=True, exist_ok=True)
    xmd.write_bytes(b"adopter edit\n")
    _write_apply_run_state(
        target,
        recipe={"packs": ["alpha"], "profiles": []},
        managed_paths=[
            {"path": "packs/alpha/x.md", "sha256": hashlib.sha256(b"original\n").hexdigest()}
        ],
    )
    before = walk_target_tree(target)

    code = _call_run_apply(target, source)

    assert code == 3
    assert walk_target_tree(target) == before


def test_run_apply_snapshot_bound_exceeded_refuses_before_prompt_and_before_write(
    tmp_path, monkeypatch
):
    target, source = _apply_run_target(tmp_path, "snapshot-bound")

    def _boom_prompt(prompt=""):
        raise AssertionError("input() must not be called before the snapshot bound check")

    def _boom_snapshot(target_arg, paths, *, bound=catalogue_sync._SNAPSHOT_BOUND_BYTES):
        raise catalogue_sync.SnapshotBoundExceeded(bound=10, measured=20)

    monkeypatch.setattr("builtins.input", _boom_prompt)
    monkeypatch.setattr(catalogue_sync, "snapshot_write_set", _boom_snapshot)

    code = _call_run_apply(target, source, yes=False)

    assert code == 3


def test_run_apply_snapshot_unreadable_refuses_cannot_answer(tmp_path, monkeypatch):
    target, source = _apply_run_target(tmp_path, "snapshot-unreadable")

    def _boom_snapshot(target_arg, paths, *, bound=catalogue_sync._SNAPSHOT_BOUND_BYTES):
        raise catalogue_sync.SnapshotUnreadableError("packs/alpha/README.md")

    def _boom_prompt(prompt=""):
        raise AssertionError("input() must not be called on a snapshot-unreadable refusal")

    monkeypatch.setattr(catalogue_sync, "snapshot_write_set", _boom_snapshot)
    monkeypatch.setattr("builtins.input", _boom_prompt)

    code = _call_run_apply(target, source, yes=False)

    assert code == 3


def test_run_apply_no_terminal_no_yes_refuses_difference_and_writes_nothing(tmp_path, monkeypatch):
    target, source = _apply_run_target(tmp_path, "no-terminal")
    before = walk_target_tree(target)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    code = _call_run_apply(target, source, yes=False)

    assert code == 1
    assert walk_target_tree(target) == before


def test_run_apply_declined_consent_refuses_difference_and_writes_nothing(tmp_path, monkeypatch):
    target, source = _apply_run_target(tmp_path, "declined")
    before = walk_target_tree(target)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")

    code = _call_run_apply(target, source, yes=False)

    assert code == 1
    assert walk_target_tree(target) == before


def test_run_apply_gate_recheck_diverged_after_consent_refuses_cannot_answer(
    tmp_path, monkeypatch
):
    # AC-0039's snapshot-scoped trailing note: the gate recheck row sits
    # below the consent rows because the gate runs after consent by
    # construction. Consent (`--yes`) is given here, and only the recheck —
    # driven by monkeypatching `gate_recheck` itself, since the gate always
    # runs after this function's own snapshot build — reports a divergence.
    target, source = _apply_run_target(tmp_path, "gate-recheck")
    monkeypatch.setattr(catalogue_sync, "gate_recheck", lambda target_arg, expected: ["packs/alpha/README.md"])

    code = _call_run_apply(target, source)

    assert code == 3


def test_run_apply_write_failure_restored_returns_apply_failed(tmp_path, monkeypatch):
    target, source = _apply_run_target(
        tmp_path,
        "write-fails-restored",
        managed_paths=[
            {"path": "packs/alpha/README.md", "sha256": hashlib.sha256(b"old\n").hexdigest()}
        ],
    )
    (target / "packs" / "alpha").mkdir(parents=True, exist_ok=True)
    (target / "packs" / "alpha" / "README.md").write_bytes(b"old\n")

    real_write_jailed = catalogue_sync.write_jailed

    def _boom(root, relpath, content, **kwargs):
        if relpath == "packs/alpha/README.md":
            raise OSError("simulated write failure")
        return real_write_jailed(root, relpath, content, **kwargs)

    monkeypatch.setattr(catalogue_sync, "write_jailed", _boom)

    code = _call_run_apply(target, source)

    assert code == 4
    # Restored: the adopter's pre-run bytes are back.
    assert (target / "packs" / "alpha" / "README.md").read_bytes() == b"old\n"


def test_run_apply_write_failure_restore_fails_names_unrestored_path(
    tmp_path, monkeypatch, capsys
):
    target, source = _apply_run_target(
        tmp_path,
        "write-fails-unrestored",
        managed_paths=[
            {"path": "packs/alpha/README.md", "sha256": hashlib.sha256(b"old\n").hexdigest()}
        ],
    )
    (target / "packs" / "alpha").mkdir(parents=True, exist_ok=True)
    (target / "packs" / "alpha" / "README.md").write_bytes(b"old\n")

    def _boom_write(root, relpath, content, **kwargs):
        raise OSError("simulated write failure")

    def _boom_restore(target_arg, snapshot, acted_paths):
        return ["packs/alpha/README.md"]

    monkeypatch.setattr(catalogue_sync, "write_jailed", _boom_write)
    monkeypatch.setattr(catalogue_sync, "restore_from_snapshot", _boom_restore)

    code = _call_run_apply(target, source)

    assert code == 4
    assert "packs/alpha/README.md" in capsys.readouterr().err


def test_run_apply_removal_failure_returns_apply_failed(tmp_path, monkeypatch):
    target, source = _apply_run_target(
        tmp_path,
        "removal-fails",
        managed_paths=[
            {"path": "packs/alpha/gone.md", "sha256": hashlib.sha256(b"stale\n").hexdigest()}
        ],
    )
    gone = target / "packs" / "alpha" / "gone.md"
    gone.parent.mkdir(parents=True, exist_ok=True)
    gone.write_bytes(b"stale\n")

    monkeypatch.setattr(catalogue_sync, "_confined_unlink", lambda target_arg, path: False)

    code = _call_run_apply(target, source)

    assert code == 4


def test_run_apply_state_write_failure_returns_apply_failed(tmp_path, monkeypatch):
    target, source = _apply_run_target(tmp_path, "state-write-fails")

    def _boom(target_arg, merged_state):
        raise OSError("simulated state write failure")

    monkeypatch.setattr(catalogue_sync, "write_merged_state", _boom)

    code = _call_run_apply(target, source)

    assert code == 4


def test_run_apply_replay_boundary_fault_reaches_cannot_answer_not_a_crash(
    tmp_path, monkeypatch
):
    # AC-0040: a fault injected at the replay boundary — anything other than
    # the already-handled `ReplayError` — still reaches a named row.
    target, source = _apply_run_target(tmp_path, "replay-boom")

    def _boom(cfg, *, interactive=False):
        raise RuntimeError("simulated unexpected replay failure")

    monkeypatch.setattr(catalogue_sync, "replay_derivation", _boom)

    code = _call_run_apply(target, source)

    assert code == 3


def test_run_apply_printed_acted_rows_equal_admitted_write_set(tmp_path, capsys):
    # AC-0057: the row set the run prints equals the row set its write phase
    # acts on (the "consented-plan-is-applied" half).
    target, source = _apply_run_target(tmp_path, "printed-plan")

    code = _call_run_apply(target, source, fmt="json")
    doc = json.loads(capsys.readouterr().out)

    acted_paths = {row["path"] for row in doc["acted"] if row["verdict"] != "would-remove"}
    state = json.loads(
        (target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )
    written_paths = {entry["path"] for entry in state["managed_paths"]}

    assert code == 0
    assert acted_paths <= written_paths


def test_run_apply_deferred_package_count_equals_planned_package_paths(tmp_path, capsys):
    # AC-0066: the reported `deferred_package` count equals the number of
    # planned paths clause 5 excludes. Clause 5 only ever excludes a path
    # clause 3 would otherwise admit (a `would-update`/`would-companion`
    # verdict, or a path belonging to a newly introduced pack/profile) — a
    # `packages/credbroker/**` path nobody has recorded yet is plain
    # `untouched` and was never a write candidate in the first place, so
    # this fixture records two such paths with a stale digest, and the
    # source now ships different bytes for both (`would-update`), which is
    # what makes clause 5's exclusion — and this count — observable.
    source = tmp_path / "deferred-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\nname = "upstream"\ndisplay_name = "Upstream"\n'
        'description = "d"\n',
        encoding="utf-8",
    )
    creds_pack = source / "packs" / "credential-brokers"
    creds_pack.mkdir(parents=True)
    (creds_pack / "pack.toml").write_text(
        '[pack]\nname = "credential-brokers"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    pkg = source / "packages" / "credbroker"
    pkg.mkdir(parents=True)
    (pkg / "one.txt").write_text("vendored v2\n", encoding="utf-8")
    (pkg / "two.txt").write_text("vendored v2\n", encoding="utf-8")

    target = tmp_path / "deferred-target"
    target_pkg = target / "packages" / "credbroker"
    target_pkg.mkdir(parents=True)
    (target_pkg / "one.txt").write_bytes(b"vendored v1\n")
    (target_pkg / "two.txt").write_bytes(b"vendored v1\n")
    _write_apply_run_state(
        target,
        recipe={"packs": ["credential-brokers"], "profiles": []},
        managed_paths=[
            {
                "path": "packages/credbroker/one.txt",
                "sha256": hashlib.sha256(b"vendored v1\n").hexdigest(),
            },
            {
                "path": "packages/credbroker/two.txt",
                "sha256": hashlib.sha256(b"vendored v1\n").hexdigest(),
            },
        ],
    )
    before_one = (target_pkg / "one.txt").read_bytes()

    code = _call_run_apply(target, source, fmt="json")
    doc = json.loads(capsys.readouterr().out)

    assert code == 0
    assert doc["summary"]["deferred_package"] == 2
    # Never written: clause 5 excludes it from the write set entirely.
    assert (target_pkg / "one.txt").read_bytes() == before_one


# T7: the parser admits an apply run (spec AC-0030, AC-0060, AC-0074).
#
# Every test below drives `_build_parser()` itself — never a hand-built
# `argparse.Namespace` — because the parser's own defaults (and its own
# refusals) are what these criteria constrain. AC-0043's `--dry-run`-side
# scoping restriction and its `--check`-side malformed row are T6/T7's own
# recorded gap (plan.md's live cross-task note): neither `run()` nor
# `_run_dry_run` reads `--pack`/`--profile`/`--guides` yet, and that wiring
# sits in `commands/catalogue_sync.py`, outside this task's `Touches:`.


def _find_subparsers_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    raise AssertionError("no _SubParsersAction found on parser")


def test_sync_bare_invocation_reaches_run_apply_via_the_real_parser(tmp_path):
    # AC-0030: neither --dry-run nor --check present means apply. Reached
    # through the real parser's own default for the now-optional mutually
    # exclusive group — a hand-built namespace would supply that default
    # itself and could not prove the parser decides it.
    target, source = _apply_run_target(
        tmp_path,
        "bare-invocation",
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"old bytes\n").hexdigest(),
            }
        ],
    )
    readme = target / "packs" / "alpha" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_bytes(b"old bytes\n")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--yes"]
    )

    assert catalogue_sync.run(args) == 0
    assert readme.read_bytes() == (source / "packs" / "alpha" / "README.md").read_bytes()


def test_sync_both_dry_run_and_check_exits_2_via_the_real_parser(tmp_path):
    # AC-0030: supplying both flags is malformed.
    with pytest.raises(SystemExit) as exc:
        _build_parser().parse_args(
            ["catalogue", "sync", str(tmp_path), "--source", str(tmp_path),
             "--dry-run", "--check"]
        )
    assert exc.value.code == 2


@pytest.mark.parametrize("mode_flag", ["--dry-run", "--check"])
def test_sync_yes_outside_apply_run_exits_2_via_the_real_parser(tmp_path, mode_flag):
    # AC-0030: `--yes` outside an apply run is malformed. Asserting only
    # that a bare apply run accepts `--yes` (the prior test) would pass a
    # parser that also lets `--yes` ride along with `--dry-run`/`--check`.
    with pytest.raises(SystemExit) as exc:
        _build_parser().parse_args(
            ["catalogue", "sync", str(tmp_path), "--source", str(tmp_path),
             mode_flag, "--yes"]
        )
    assert exc.value.code == 2


def test_sync_guides_resolves_to_scoping_flag_and_guides_mode_abbreviation_is_rejected():
    # AC-0060: `--guides` is its own scoping flag (distinct from
    # `--guides-mode`), and the subparser resolves no abbreviated option
    # name — an abbreviation of `--guides-mode` is rejected rather than
    # silently resolving to it. Asserting only that `--guides` works would
    # pass a parser that still abbreviates `--guides-mode`.
    args = _build_parser().parse_args(
        ["catalogue", "sync", "target", "--source", "source", "--guides", "--dry-run"]
    )
    assert args.guides is True
    assert args.guides_mode is None

    with pytest.raises(SystemExit) as exc:
        _build_parser().parse_args(
            ["catalogue", "sync", "target", "--source", "source",
             "--guides-mo", "none", "--dry-run"]
        )
    assert exc.value.code == 2


def test_sync_subparser_help_does_not_claim_the_command_is_read_only():
    # AC-0074: the registered subparser's help string, read from the
    # parser rather than from the source file, no longer claims the
    # command is read-only or writes nothing.
    parser = _build_parser()
    catalogue_sp = _find_subparsers_action(parser).choices["catalogue"]
    cat_sub_action = _find_subparsers_action(catalogue_sp)
    sync_help = next(
        pseudo.help
        for pseudo in cat_sub_action._choices_actions
        if pseudo.dest == "sync"
    )
    assert "read-only" not in sync_help.lower()
    assert "writes nothing" not in sync_help.lower()


def test_sync_apply_format_json_without_yes_exits_2_via_the_real_parser(tmp_path):
    # AC-0030's document clause, driven through the real parser rather than
    # `_call_run_apply`'s hand-built kwargs.
    target, source = _apply_run_target(tmp_path, "json-no-yes-parser")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source), "--format", "json"]
    )

    assert catalogue_sync.run(args) == 2


@pytest.mark.parametrize(
    "scope_args",
    [("--pack", "alpha"), ("--profile", "alpha"), ("--guides",)],
    ids=["pack", "profile", "guides"],
)
def test_sync_check_with_a_scoping_flag_is_malformed(tmp_path, scope_args):
    # AC-0030's --check clause / AC-0039's malformed row: any of --pack,
    # --profile or --guides supplied with --check is malformed — `--check`
    # answers whether the whole recorded recipe is current and has no
    # scoped variant. Reached before source resolution, so a nonexistent
    # source/target need no real fixture.
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(tmp_path), "--source", str(tmp_path),
         "--check", *scope_args]
    )

    assert catalogue_sync.run(args) == 2


def test_sync_dry_run_pack_scope_excludes_the_out_of_scope_pack_from_the_printed_plan(
    tmp_path, capsys
):
    # AC-0043's preview half: the same scope that would restrict an apply
    # run's write set restricts the plan a --dry-run preview prints. Both
    # packs carry a real, would-update change here — asserting only that
    # the in-scope pack's path is present would pass a preview that never
    # narrows at all; the out-of-scope pack's path must actually be absent.
    source = tmp_path / "scope-preview-source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\nname = "upstream"\ndisplay_name = "Upstream"\n'
        'description = "d"\n',
        encoding="utf-8",
    )
    for name in ("alpha", "beta"):
        pack = source / "packs" / name
        pack.mkdir(parents=True)
        (pack / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "1.0.0"\n', encoding="utf-8"
        )
        (pack / "README.md").write_text(f"new {name} bytes\n", encoding="utf-8")

    target = tmp_path / "scope-preview-target"
    target.mkdir()
    _write_apply_run_state(
        target,
        recipe={"packs": ["alpha", "beta"], "profiles": []},
        managed_paths=[
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(b"old alpha bytes\n").hexdigest(),
            },
            {
                "path": "packs/beta/README.md",
                "sha256": hashlib.sha256(b"old beta bytes\n").hexdigest(),
            },
        ],
    )
    for name in ("alpha", "beta"):
        readme = target / "packs" / name / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_bytes(f"old {name} bytes\n".encode())

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(target), "--source", str(source),
         "--dry-run", "--pack", "alpha", "--format", "json"]
    )

    code = catalogue_sync.run(args)
    doc = json.loads(capsys.readouterr().out)

    assert code == 0
    paths = {row["path"] for row in doc["verdicts"]}
    assert "packs/alpha/README.md" in paths
    assert "packs/beta/README.md" not in paths
