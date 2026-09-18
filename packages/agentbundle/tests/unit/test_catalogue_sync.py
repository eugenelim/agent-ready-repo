"""Tests for ``agentbundle catalogue sync`` (spec: catalogue-sync-dry-run)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

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


def test_sync_five_path_states_and_reported_selection(derived_tree, upstream, capsys):
    """Drive all five AC-0010 path states through one run and check the
    reported verdict, the companion path, and the reported pack/profile
    selection against the recorded recipe."""
    (upstream / "packs" / "alpha" / "extra.md").write_bytes(b"legacy\n")
    (derived_tree / "packs" / "alpha" / "extra.md").write_bytes(b"legacy\n")
    (derived_tree / "packs" / "alpha" / "README.md").write_bytes(b"edited by the adopter\n")
    (derived_tree / "packs" / "alpha" / "stale.md").write_bytes(b"stale\n")

    state_path = derived_tree / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append({"path": "packs/alpha/extra.md", "sha256": None})
    state["managed_paths"].append(
        {
            "path": "packs/alpha/stale.md",
            "sha256": hashlib.sha256(b"stale\n").hexdigest(),
        }
    )
    state_path.write_text(json.dumps(state), encoding="utf-8")

    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )
    catalogue_sync.run(args)
    doc = json.loads(capsys.readouterr().out)

    verdicts_by_path = {row["path"]: row for row in doc["verdicts"]}
    # recorded, present, sha matches -> would-update.
    assert verdicts_by_path["packs/alpha/pack.toml"]["verdict"] == "would-update"
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


# STUB: AC-0016
def test_sync_reports_seven_counts_and_the_identity(derived_tree, upstream, capsys):
    args = _build_parser().parse_args(
        ["catalogue", "sync", str(derived_tree), "--source", str(upstream),
         "--dry-run", "--format", "json"]
    )

    catalogue_sync.run(args)
    summary = json.loads(capsys.readouterr().out)["summary"]

    assert set(summary) == {
        "would_update", "would_companion", "untouched", "would_remove",
        "schema_1_inert", "compared", "uncompared",
    }
    # The plan's literal stub illustration asserts `== 1`; derived_tree (T1)
    # actually records two managed_paths entries, so the identity's
    # denominator is read from the fixture rather than restated as a second
    # literal that could drift from it — see the implementer report's
    # Deviations section.
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
