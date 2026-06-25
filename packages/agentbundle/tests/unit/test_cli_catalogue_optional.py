"""T5: the `catalogue` positional is optional on `install`/`upgrade` and still
required on the discovery verbs — RFC-0046 (argparse surface only).
"""

from __future__ import annotations

import pytest

from agentbundle.cli import _build_parser


@pytest.mark.parametrize(
    "argv",
    [
        ["install", "--pack", "core"],
        ["install", "--profile", "starter"],
        ["upgrade", "--pack", "core"],
    ],
)
def test_catalogue_optional_on_install_and_upgrade(argv):
    ns = _build_parser().parse_args(argv)
    assert ns.catalogue is None


@pytest.mark.parametrize(
    "argv",
    [
        ["install", "--pack", "core", "git+https://github.com/x/y"],
        ["upgrade", "--pack", "core", "/local/catalogue"],
    ],
)
def test_explicit_catalogue_passes_through(argv):
    ns = _build_parser().parse_args(argv)
    assert ns.catalogue == argv[-1]


@pytest.mark.parametrize("verb", ["list-packs", "list-profiles"])
def test_catalogue_still_required_on_discovery_verbs(verb):
    with pytest.raises(SystemExit):
        _build_parser().parse_args([verb])
