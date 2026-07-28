"""Tests for PackState provenance fields (artifact_uri, archive_sha256, source_revision).

Covers:
  - HTTPS install writes provenance into PackState
  - Local install leaves provenance as None
  - HTTPS upgrade updates provenance on the existing row
  - State files without provenance fields are read as None (backward compat)

Parametrization opt-out: these tests target state-accumulation logic, not the
per-adapter projection layout, so they are not parametrized over adapters.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import shutil
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
CONVERTERS_PACK_SRC = REPO_ROOT / "packs" / "converters"


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import install

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = install.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


def _run_upgrade(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands import upgrade

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = upgrade.run(args)
    return rc, stdout.getvalue(), stderr.getvalue()


def _install_args(cat: Path, repo: Path, *, scope: str = "repo") -> argparse.Namespace:
    return argparse.Namespace(
        pack="converters",
        catalogue=str(cat),
        output=str(repo),
        scope=scope,
        force=False,
        force_merge=False,
        adapter=None,
    )


def _upgrade_args(catalogue: str, repo: Path) -> argparse.Namespace:
    return argparse.Namespace(
        pack="converters",
        catalogue=catalogue,
        root=str(repo),
        scope="repo",
        yes=True,
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
    )


class InstallHTTPSProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.cat = self.tmp / "catalogue"
        (self.cat / "packs").mkdir(parents=True)
        shutil.copytree(CONVERTERS_PACK_SRC, self.cat / "packs" / "converters")

    def _read_pack_state(self) -> object:
        from agentbundle.config import load_state

        state_path = self.repo / ".agentbundle-state.toml"
        state = load_state(state_path)
        rows = state.rows_for_pack("converters")
        self.assertEqual(len(rows), 1, f"expected 1 adapter row, got: {list(rows)}")
        return next(iter(rows.values()))

    def test_install_from_https_sets_provenance(self) -> None:
        from agentbundle.https_catalogue import CatalogueArchiveResult

        fake_uri = "https://example.com/releases/1.0.0/converters.tar.gz"
        fake_sha = "a" * 64
        fake_rev = "abc123def456"
        fake_result = CatalogueArchiveResult(
            path=self.cat,
            artifact_uri=fake_uri,
            archive_sha256=fake_sha,
            source_revision=fake_rev,
        )

        with patch(
            "agentbundle.https_catalogue.fetch_catalogue_archive_with_provenance",
            return_value=fake_result,
        ):
            args = argparse.Namespace(
                pack="converters",
                catalogue="catalogue+https://example.com/channel.json",
                output=str(self.repo),
                scope="repo",
                force=False,
                force_merge=False,
                adapter=None,
            )
            rc, _stdout, _stderr = _run_install(args)

        self.assertEqual(rc, 0, _stderr)
        ps = self._read_pack_state()
        self.assertEqual(ps.artifact_uri, fake_uri)
        self.assertEqual(ps.archive_sha256, fake_sha)
        self.assertEqual(ps.source_revision, fake_rev)

    def test_install_from_local_leaves_provenance_null(self) -> None:
        rc, _stdout, _stderr = _run_install(_install_args(self.cat, self.repo))

        self.assertEqual(rc, 0, _stderr)
        ps = self._read_pack_state()
        self.assertIsNone(ps.artifact_uri)
        self.assertIsNone(ps.archive_sha256)
        self.assertIsNone(ps.source_revision)

    def test_upgrade_from_https_updates_provenance(self) -> None:
        from agentbundle.https_catalogue import CatalogueArchiveResult

        # First install from local (provenance = None)
        rc, _stdout, _stderr = _run_install(_install_args(self.cat, self.repo))
        self.assertEqual(rc, 0, f"initial install failed: {_stderr}")

        ps_before = self._read_pack_state()
        self.assertIsNone(ps_before.artifact_uri)

        # Upgrade from HTTPS (mocked)
        fake_uri = "https://example.com/releases/1.0.0/converters-v2.tar.gz"
        fake_sha = "b" * 64
        fake_rev = "def456abc123"
        fake_result = CatalogueArchiveResult(
            path=self.cat,
            artifact_uri=fake_uri,
            archive_sha256=fake_sha,
            source_revision=fake_rev,
        )

        with patch(
            "agentbundle.https_catalogue.fetch_catalogue_archive_with_provenance",
            return_value=fake_result,
        ):
            rc, _stdout, _stderr = _run_upgrade(
                _upgrade_args("catalogue+https://example.com/channel.json", self.repo)
            )

        self.assertEqual(rc, 0, _stderr)
        ps = self._read_pack_state()
        self.assertEqual(ps.artifact_uri, fake_uri)
        self.assertEqual(ps.archive_sha256, fake_sha)
        self.assertEqual(ps.source_revision, fake_rev)


class StateReadWithoutProvenanceFieldsTests(unittest.TestCase):
    def test_state_read_without_provenance_fields_is_valid(self) -> None:
        import tempfile

        from agentbundle.config import STATE_SCHEMA_VERSION, load_state

        state_toml = textwrap.dedent(f"""\
            schema-version = "{STATE_SCHEMA_VERSION}"

            [pack.converters.adapters.claude-code]
            installed-version = "1.0.0"
            install-route = "cli"
            scope = "repo"
            user-root = "~/.agentbundle"
            primitives = []

            [pack.converters.adapters.claude-code.files]
        """)

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        state_path = tmp / ".agentbundle-state.toml"
        state_path.write_text(state_toml, encoding="utf-8")

        state = load_state(state_path)
        ps = state.row("converters", "claude-code")
        self.assertIsNotNone(ps)
        self.assertIsNone(ps.artifact_uri)
        self.assertIsNone(ps.archive_sha256)
        self.assertIsNone(ps.source_revision)
