"""CLI-level tests for agentbundle catalogue init --preset self-hosted."""

from __future__ import annotations

import pytest
from agentbundle.cli import _build_parser

# ---------------------------------------------------------------------------
# Parser shape tests (no real init invoked)
# ---------------------------------------------------------------------------


def test_catalogue_init_preset_flag_accepted() -> None:
    parser = _build_parser()
    args = parser.parse_args(["catalogue", "init", "--preset", "self-hosted", "--source", "."])
    assert args.preset == "self-hosted"
    assert args.source == "."


def test_catalogue_init_tooling_flag_accepted() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--preset", "self-hosted",
        "--tooling", "vendored",
        "--source", "/tmp/src",
    ])
    assert args.tooling == "vendored"


def test_catalogue_init_attribution_flag_accepted() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--preset", "self-hosted",
        "--attribution", "attributed",
        "--source", "/tmp/src",
    ])
    assert args.attribution == "attributed"


def test_catalogue_init_repeatable_packs() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--pack", "core",
        "--pack", "governance-extras",
        "--source", "/tmp/src",
    ])
    assert args.packs == ["core", "governance-extras"]


def test_catalogue_init_repeatable_adapters() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--adapter", "claude-code",
        "--adapter", "kiro-ide",
        "--source", "/tmp/src",
    ])
    assert args.adapters == ["claude-code", "kiro-ide"]


def test_catalogue_init_repeatable_profiles() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--profile", "default",
        "--profile", "engineering",
        "--source", "/tmp/src",
    ])
    assert args.profiles == ["default", "engineering"]


def test_catalogue_init_guides_none() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--guides", "none",
        "--source", "/tmp/src",
    ])
    assert args.guides == "none"


def test_catalogue_init_owner_email() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--owner-email", "admin@example.com",
        "--source", "/tmp/src",
    ])
    assert args.owner_email == "admin@example.com"


def test_catalogue_init_repository_url() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "init",
        "--repository-url", "https://example.com/my-catalogue",
        "--source", "/tmp/src",
    ])
    assert args.repository_url == "https://example.com/my-catalogue"


def test_catalogue_package_flavor_runtime_default() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "package",
        "--bundle", "b", "--release", "1.0.0", "--channel", "stable",
        "--output", "/tmp/out",
    ])
    assert args.flavor == "runtime"


def test_catalogue_package_flavor_source() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        "catalogue", "package",
        "--bundle", "b", "--release", "1.0.0", "--channel", "stable",
        "--output", "/tmp/out",
        "--flavor", "source",
    ])
    assert args.flavor == "source"


def test_catalogue_init_preset_invalid_choice_exits() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["catalogue", "init", "--preset", "invalid-preset"])
    assert exc.value.code != 0


def test_catalogue_package_flavor_invalid_choice_exits() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args([
            "catalogue", "package",
            "--bundle", "b", "--release", "1.0.0", "--channel", "c",
            "--output", "/tmp", "--flavor", "invalid",
        ])
    assert exc.value.code != 0


# ---------------------------------------------------------------------------
# Mode-rule rejection tests (F9, F10)
# ---------------------------------------------------------------------------

def test_channel_with_flavor_source_exits_2(tmp_path) -> None:
    import argparse

    from agentbundle.commands import catalogue_package

    ns = argparse.Namespace(
        flavor="source",
        channel="stable",
        root=".",
        output=str(tmp_path / "out"),
        bundle="b",
        release="1.0.0",
        source_revision=None,
    )
    assert catalogue_package.run(ns) == 2


def test_self_hosted_flag_source_in_plain_mode_exits_2(tmp_path) -> None:
    import argparse

    from agentbundle.commands import catalogue_init

    ns = argparse.Namespace(
        preset=None,
        source="/some/source",
        tooling=None,
        guides=None,
        attribution=None,
        repository_url=None,
        owner_email=None,
        target=str(tmp_path / "target"),
        name=None, display_name=None, description=None,
        owner_name=None, preferred_adapter=None,
        dry_run=False, format="table",
        packs=None, adapters=None, profiles=None,
    )
    assert catalogue_init.run(ns) == 2


def test_self_hosted_flag_tooling_in_plain_mode_exits_2(tmp_path) -> None:
    import argparse

    from agentbundle.commands import catalogue_init

    ns = argparse.Namespace(
        preset=None,
        source=None,
        tooling="vendored",
        guides=None,
        attribution=None,
        repository_url=None,
        owner_email=None,
        target=str(tmp_path / "target"),
        name=None, display_name=None, description=None,
        owner_name=None, preferred_adapter=None,
        dry_run=False, format="table",
        packs=None, adapters=None, profiles=None,
    )
    assert catalogue_init.run(ns) == 2
