"""T8: install marker write + chained `adapt.run` in-process.

AC19a: every successful install appends a `[[packs-installed]]` entry
to `.adapt-install-marker.toml` at the install's scope root via
`os.replace` atomic rename.

AC19b: after the marker write, the CLI runs `agentbundle.commands.adapt.run`
in-process (no subprocess, no LLM) with `values_from = <repo>/.adapt-discovery.toml`
regardless of install scope (markers are repo-only).

AC19c: `agentbundle scaffold` lays down a `.gitignore` containing
`.adapt-install-marker.toml`.

AC19d: failure-mode robustness for (i) missing discovery file and
(ii) malformed discovery file.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import tomllib
from pathlib import Path

import pytest


ADDON_NO_DEPENDENCIES = """\
[pack]
name = "addon"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""


def _stage_pack(catalogue_root: Path, name: str, body: str) -> Path:
    pack = catalogue_root / "packs" / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(body, encoding="utf-8")
    (pack / ".apm").mkdir()
    return pack


def _install(args_dict) -> tuple[int, str, str]:
    from agentbundle.commands.install import run

    args = argparse.Namespace(**args_dict)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = run(args)
    return rc, out.getvalue(), err.getvalue()


def test_install_writes_marker_at_repo_scope_root(tmp_path):
    """Repo-scope install writes the marker at `<repo>/.adapt-install-marker.toml`
    with a single `[[packs-installed]]` entry for the installed pack."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_NO_DEPENDENCIES)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _, _ = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0
    marker_path = target / ".adapt-install-marker.toml"
    assert marker_path.exists(), "repo-scope marker file must be written"
    data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    assert data["marker-schema-version"] == "0.1"
    entries = data.get("packs-installed", [])
    assert len(entries) == 1
    assert entries[0]["name"] == "addon"
    assert entries[0]["version"] == "0.1.0"
    # `scope` field is NOT in the schema — the path encodes scope.
    assert "scope" not in entries[0]


def test_install_marker_appends_atomically(tmp_path):
    """Two sequential installs at the same scope produce two entries
    (atomic-rename append protocol)."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "alpha", ADDON_NO_DEPENDENCIES.replace("addon", "alpha"))
    _stage_pack(cat, "beta", ADDON_NO_DEPENDENCIES.replace("addon", "beta"))
    target = tmp_path / "repo"
    target.mkdir()

    _install(dict(pack="alpha", catalogue=str(cat), output=str(target), scope=None, force=False))
    _install(dict(pack="beta", catalogue=str(cat), output=str(target), scope=None, force=False))

    marker_path = target / ".adapt-install-marker.toml"
    data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    entries = data.get("packs-installed", [])
    names = sorted(e["name"] for e in entries)
    assert names == ["alpha", "beta"]


def test_install_with_no_discovery_file_emits_one_line_and_succeeds(tmp_path):
    """Per AC19d(i): missing repo-scope `.adapt-discovery.toml` causes
    the chained adapt step to emit one stderr line; install exits 0;
    marker file still written."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_NO_DEPENDENCIES)
    target = tmp_path / "repo"
    target.mkdir()

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0
    assert (target / ".adapt-install-marker.toml").exists()
    assert (
        "adapt: no .adapt-discovery.toml at repo root; markers left unresolved"
        in err
    )


def test_install_chained_adapt_failure_returns_nonzero_preserves_marker(tmp_path):
    """Per AC19d(ii): malformed `.adapt-discovery.toml` causes the
    chained adapt to refuse; install exits non-zero; marker still
    on disk (it was written before the chained adapt step)."""
    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_NO_DEPENDENCIES)
    target = tmp_path / "repo"
    target.mkdir()
    # Pre-seed a malformed discovery file (legacy [accepted] table).
    (target / ".adapt-discovery.toml").write_text(
        '[accepted]\nowner = "x"\n', encoding="utf-8"
    )

    rc, _, err = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc != 0, "malformed discovery must propagate non-zero"
    assert (target / ".adapt-install-marker.toml").exists(), (
        "marker file must remain on disk after chained adapt failure"
    )
    assert "adapt: legacy [accepted] table" in err


def test_install_chains_adapt_in_process_no_subprocess(tmp_path, monkeypatch):
    """Per AC19b: the chained `adapt` runs in-process, not via subprocess."""
    import subprocess

    cat = tmp_path / "cat"
    _stage_pack(cat, "addon", ADDON_NO_DEPENDENCIES)
    target = tmp_path / "repo"
    target.mkdir()
    # Pre-seed canonical discovery so the chain has values to apply.
    (target / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n[markers]\nowner = "octocat"\n',
        encoding="utf-8",
    )

    # Trap any subprocess invocation. If the chain shells out, this raises.
    def _no_subprocess(*args, **kwargs):
        raise AssertionError(
            f"chained adapt must not invoke subprocess: args={args!r}"
        )

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    monkeypatch.setattr(subprocess, "Popen", _no_subprocess)
    monkeypatch.setattr(subprocess, "call", _no_subprocess)

    rc, _, _ = _install(
        dict(pack="addon", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0


def test_marker_in_seed_gitignore(tmp_path):
    """AC19c: the core pack's seeded `.gitignore` contains
    `.adapt-install-marker.toml` so adopters running `agentbundle scaffold`
    don't accidentally commit the local scratch."""
    pack_gitignore = (
        Path(__file__).parent.parent.parent.parent.parent
        / "packs"
        / "core"
        / "seeds"
        / ".gitignore"
    )
    assert pack_gitignore.exists(), (
        f".gitignore seed not found at {pack_gitignore} — scaffold "
        "AC19c can't lay it down."
    )
    body = pack_gitignore.read_text(encoding="utf-8")
    assert ".adapt-install-marker.toml" in body
