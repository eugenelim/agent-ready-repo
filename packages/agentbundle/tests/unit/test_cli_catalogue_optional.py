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
        # RFC-0047: the discovery verbs are now optional too.
        ["list-packs"],
        ["list-profiles"],
    ],
)
def test_catalogue_optional_on_all_source_verbs(argv):
    ns = _build_parser().parse_args(argv)
    assert ns.catalogue is None


@pytest.mark.parametrize(
    "argv",
    [
        ["install", "--pack", "core", "git+https://github.com/x/y"],
        ["upgrade", "--pack", "core", "/local/catalogue"],
        ["list-packs", "git+https://github.com/x/y"],
        ["list-profiles", "/local/catalogue"],
    ],
)
def test_explicit_catalogue_passes_through(argv):
    ns = _build_parser().parse_args(argv)
    assert ns.catalogue == argv[-1]
