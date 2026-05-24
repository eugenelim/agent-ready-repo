"""Windows-portability: CLI normalises `\\` → `/` at the
boundary so a Windows user typing `packs\\core\\seeds` lands in the
same code path as `packs/core/seeds`."""

from __future__ import annotations

import argparse

import pytest

from agentbundle.cli import _build_parser, _normalise_path_separators


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _normalise_path_separators(args)
    return args


def test_scaffold_output_with_backslashes_normalised():
    args = _parse(["scaffold", "--output", r"packs\core\seeds"])
    assert args.output == "packs/core/seeds"


def test_diff_root_and_pack_path_normalised():
    args = _parse(
        ["diff", r"packs\core", "--root", r"some\nested\dir"]
    )
    assert args.pack_path == "packs/core"
    assert args.root == "some/nested/dir"


def test_install_catalogue_local_path_normalised():
    args = _parse(
        [
            "install",
            "--pack",
            "core",
            r"local\packs\catalogue",
            "--output",
            r"sandbox\out",
        ]
    )
    assert args.catalogue == "local/packs/catalogue"
    assert args.output == "sandbox/out"


def test_install_catalogue_git_uri_left_alone():
    """URI-shaped catalogues — `git+https://…` — must not be rewritten;
    their separators are URL semantics."""
    uri = "git+https://example.com/owner/catalogue.git"
    args = _parse(["install", "--pack", "core", uri, "--output", "out"])
    assert args.catalogue == uri


def test_non_path_attribute_left_alone_even_with_backslashes():
    """Only the curated allow-list is rewritten; a future content-string
    flag carrying a literal backslash (regex, message body) is safe."""
    ns = argparse.Namespace(message=r"line one\nline two", catalogue="ok")
    _normalise_path_separators(ns)
    assert ns.message == r"line one\nline two"


def test_uri_value_on_path_attribute_left_alone():
    """`catalogue` IS in the allow-list, but URI-shaped values are
    detected by `://` and skipped."""
    ns = argparse.Namespace(catalogue=r"scheme://host\path")
    _normalise_path_separators(ns)
    assert ns.catalogue == r"scheme://host\path"


def test_allow_list_pins_path_bearing_attributes():
    """Lock the allow-list shape so adding a new path-bearing CLI
    argument forces a corresponding test update — the kind of change
    that would otherwise be silent."""
    from agentbundle.cli import _PATH_BEARING_ATTRS

    assert _PATH_BEARING_ATTRS == frozenset(
        {
            "output",
            "output_dir",
            "root",
            "pack_path",
            "packs_dir",
            "catalogue",
            "values_from",
            "path",
        }
    )


def test_agentbundle_build_validate_path_normalises():
    """The `validate` positional on the sibling parser is named `path`
    — confirm the normaliser rewrites it identically to every other
    path-bearing flag."""
    from agentbundle.build import _build_parser as build_parser
    from agentbundle.cli import _normalise_path_separators as normalise

    parser = build_parser()
    args = parser.parse_args(["validate", r"docs\contracts\adapter.toml"])
    normalise(args)
    assert args.path == "docs/contracts/adapter.toml"


def test_forward_slashes_only_passthrough():
    """A path that's already POSIX-shaped must not be touched."""
    args = _parse(["scaffold", "--output", "packs/core/seeds"])
    assert args.output == "packs/core/seeds"


def test_normalise_ignores_non_string_attributes():
    """argparse stores some flags as bool/None; the helper must skip
    them. The path attribute used here is one of the allow-listed
    names (`output`) so we also verify the rewrite still fires when
    the allow-list matches."""
    ns = argparse.Namespace(verbose=True, count=None, output=r"a\b")
    _normalise_path_separators(ns)
    assert ns.verbose is True
    assert ns.count is None
    assert ns.output == "a/b"


def test_agentbundle_build_parser_also_normalises():
    """The `python -m agentbundle.build` parser is a sibling entry
    point — it must apply the same normalisation so the lint-packs
    subcommand (and every other build subcommand) behaves identically
    to the top-level CLI on Windows-shaped paths."""
    from agentbundle.build import _build_parser as build_parser
    from agentbundle.cli import _normalise_path_separators as normalise

    parser = build_parser()
    args = parser.parse_args(
        ["lint-packs", "--packs-dir", r"my\packs\dir"]
    )
    normalise(args)
    assert args.packs_dir == "my/packs/dir"


@pytest.mark.parametrize(
    "subcommand,argv,attr,expected",
    [
        (
            "render",
            ["render", r"packs\core", "--output", r"out\dir"],
            "pack_path",
            "packs/core",
        ),
        ("upgrade", [
            "upgrade", "--pack", "core", "--to", "0.2.0",
            r"cat\path", "--root", r"r\oot",
        ], "root", "r/oot"),
        ("uninstall", [
            "uninstall", "--pack", "core", "--root", r"a\b\c",
        ], "root", "a/b/c"),
    ],
)
def test_path_normalised_across_subcommands(subcommand, argv, attr, expected):
    args = _parse(argv)
    assert getattr(args, attr) == expected
