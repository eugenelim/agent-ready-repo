"""End-to-end (no network): bare source verbs (no `catalogue` positional)
resolve through the default chain at the command boundary.

Covers `install --pack core` (RFC-0046), the `install --profile` and
`_offer_upgrade` hand-off sites, and the discovery verbs `list-packs` /
`list-profiles` (RFC-0047). Uses layer 2 (`config set source` → a local
catalogue with both markers) so resolution short-circuits before layer 3,
exercising the full wiring (`resolve_catalogue_uri` → `resolve_default_source`
→ `resolve_catalogue`) without touching the network or the ambient editable
record.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import shutil
from pathlib import Path

from agentbundle.commands import install, list_packs, list_profiles
from agentbundle.user_config import UserConfig


REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_CORE = REPO_ROOT / "packs" / "core"


def _local_catalogue(tmp_path: Path) -> Path:
    """A tmp catalogue holding both markers (`packs/` + the marketplace file)
    and a real `packs/core/`."""
    cat = tmp_path / "cat"
    (cat / "packs").mkdir(parents=True)
    shutil.copytree(REAL_CORE, cat / "packs" / "core", symlinks=False)
    cp = cat / ".claude-plugin"
    cp.mkdir()
    (cp / "marketplace.json").write_text("{}", encoding="utf-8")
    return cat


def test_bare_install_resolves_via_config_source(tmp_path):
    cat = _local_catalogue(tmp_path)
    target = tmp_path / "repo"
    target.mkdir()

    # Bare invocation: catalogue=None; the source comes from layer 2.
    args = argparse.Namespace(
        pack="core",
        catalogue=None,
        output=str(target),
        scope=None,
        force=False,
        force_merge=False,
        profile=None,
        _user_config=UserConfig(source=str(cat)),
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    assert rc == 0, f"bare install failed: {err.getvalue()}"
    # Real artifact landed — the projected core tree exists under the target.
    assert any(target.rglob("*")), "install produced no files"


def test_bare_profile_install_reaches_default_resolver(tmp_path, monkeypatch):
    # AC: a bare `install --profile X` (no catalogue) resolves through the
    # default chain at the `_run_profile` site, not just the `--pack` path.
    from agentbundle.commands import _common

    seen = {}

    def _spy(args):
        seen["catalogue"] = args.catalogue
        return str(tmp_path / "empty-catalogue")  # no profile there → stops after resolve

    monkeypatch.setattr(_common, "resolve_catalogue_uri", _spy)

    args = argparse.Namespace(
        pack=None,
        profile="starter",
        catalogue=None,
        output=str(tmp_path),
        scope=None,
        adapter=None,
        _user_config=None,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        install.run(args)  # ProfileError after resolve is fine — we assert the call
    assert "catalogue" in seen, "_run_profile never reached the default resolver"
    assert seen["catalogue"] is None  # the omitted positional flowed through


def test_offer_upgrade_hands_off_resolved_uri(monkeypatch):
    # AC: the install→upgrade-offer hand-off carries the already-resolved URI,
    # never `args.catalogue` (which is None on a bare install) → no re-resolution.
    from agentbundle.commands import upgrade as _upgrade

    captured = {}
    monkeypatch.setattr(_upgrade, "run", lambda ns: captured.setdefault("ns", ns) and 0)

    args = argparse.Namespace(catalogue=None, output=".", _user_config=None)
    install._offer_upgrade(
        args, pack_name="core", scope="repo", catalogue_uri="git+https://resolved/x"
    )
    assert captured["ns"].catalogue == "git+https://resolved/x"


def test_bare_list_packs_resolves_default_source(tmp_path):
    # RFC-0047: a bare `list-packs` (no catalogue) resolves the source via the
    # same chain and lists the catalogue's packs.
    cat = _local_catalogue(tmp_path)
    args = argparse.Namespace(catalogue=None, _user_config=UserConfig(source=str(cat)))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = list_packs.run(args)
    assert rc == 0, err.getvalue()
    assert "core" in out.getvalue()


def test_bare_list_profiles_resolves_default_source(tmp_path):
    # RFC-0047: a bare `list-profiles` resolves the source AND reads it — plant a
    # profile so the test fails if resolution were dropped (an empty listing
    # would pass for the wrong reason).
    cat = _local_catalogue(tmp_path)
    profiles_dir = cat / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "sample.toml").write_text(
        'scope = "repo"\ndescription = "a sample profile"\n\n[[packs]]\npack = "core"\n',
        encoding="utf-8",
    )
    args = argparse.Namespace(catalogue=None, _user_config=UserConfig(source=str(cat)))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = list_profiles.run(args)
    assert rc == 0, err.getvalue()
    assert "sample" in out.getvalue()  # proves the resolved catalogue was read
