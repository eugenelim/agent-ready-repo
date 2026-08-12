"""Credential-brokers source and vendored-copy invariants."""

from __future__ import annotations

from pathlib import Path

from agentbundle.build import user_libs

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK = REPO_ROOT / "packs" / "credential-brokers"
SHIM_BASENAMES = (
    "credentials_shim.py",
    "_keychain_macos.py",
    "_credman_windows.py",
)


def test_companion_shim_sources_are_retained() -> None:
    source = PACK / ".apm" / "shared-libs"
    for basename in SHIM_BASENAMES:
        assert (source / basename).is_file()


def test_vendored_pack_copy_matches_package_source() -> None:
    package = REPO_ROOT / user_libs.PACKAGE_SUBPATH
    pack_copy = PACK / user_libs.PACK_TARGET_SUBDIR / user_libs.VENDORED_MODULE
    floor = REPO_ROOT / user_libs.TARGET_SUBDIR / user_libs.VENDORED_MODULE
    sources = user_libs.collect_sources(package)
    assert sources
    for relative, source in sources.items():
        assert (pack_copy / relative).read_bytes() == source.read_bytes()
        assert (floor / relative).read_bytes() == source.read_bytes()
