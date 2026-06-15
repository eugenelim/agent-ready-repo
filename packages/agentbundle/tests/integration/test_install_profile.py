"""T5 (pack-profiles AC3–AC8, AC12, AC13): `install --profile` orchestrator.

End-to-end against a fixture catalogue + temp scope roots. Verifies one command
installs the batch in authored order, at one scope, on one pinned adapter, with
`install_route="profile"` rows and no profile state entity; that already-
installed packs are skipped (never tripping refuse-on-reinstall); that a later
pack's pre-flight failure (path-jail / adapter mismatch) aborts before any
write; and that a genuine write-phase I/O failure leaves a consistent prefix
plus a per-pack summary.
"""

from __future__ import annotations

import contextlib
import io

import pytest


# ---------------------------------------------------------------------------
# Hygiene — pin $HOME and reset install.py's once-per-process detection sets.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_home_and_caches(tmp_path, monkeypatch):
    from agentbundle.commands import install

    home = tmp_path / "iso_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()
    yield
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()


# ---------------------------------------------------------------------------
# Fixture-catalogue builders
# ---------------------------------------------------------------------------


def _stage_pack(cat, name, *, version="0.1.0", scope="repo", deps=None,
                allowed_adapters=None):
    pdir = cat / "packs" / name
    skill = pdir / ".apm" / "skills" / f"{name}-skill"
    skill.mkdir(parents=True)
    lines = [
        "[pack]",
        f'name = "{name}"',
        f'version = "{version}"',
        'description = "fixture"',
        "[pack.adapter-contract]",
        'version = "0.6"',
        "[pack.install]",
        f'default-scope = "{scope}"',
        f'allowed-scopes = ["{scope}"]',
    ]
    if allowed_adapters is not None:
        lines.append(
            "allowed-adapters = [" + ", ".join(f'"{a}"' for a in allowed_adapters) + "]"
        )
    for dep_name, dep_range in deps or []:
        lines += [
            "[[pack.dependencies.required]]",
            'catalogue = "agent-ready-repo"',
            f'pack = "{dep_name}"',
            f'version = "{dep_range}"',
        ]
    (pdir / "pack.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        f"---\ndescription: fixture skill for {name}.\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def _stage_profile(cat, name, scope, packs):
    pdir = cat / "profiles"
    pdir.mkdir(parents=True, exist_ok=True)
    body = [f'scope = "{scope}"', 'description = "fixture profile"']
    for p in packs:
        body += ["[[packs]]", f'pack = "{p}"']
    (pdir / f"{name}.toml").write_text("\n".join(body) + "\n", encoding="utf-8")


def _three_pack_repo_catalogue(cat):
    """pf-core (no deps) + two addons that each require pf-core ^0.1."""
    _stage_pack(cat, "pf-core", version="0.4.9", scope="repo")
    _stage_pack(cat, "pf-addon-a", scope="repo", deps=[("pf-core", "^0.1")])
    _stage_pack(cat, "pf-addon-b", scope="repo", deps=[("pf-core", "^0.1")])
    _stage_profile(cat, "test-bundle", "repo", ["pf-core", "pf-addon-a", "pf-addon-b"])


def _run_install(argv):
    """Run `agentbundle install <argv>` via the real parser; capture output."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install
    from agentbundle.user_config import load_user_config

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    args._user_config = load_user_config()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def _repo_state(target):
    from agentbundle.config import load_state

    return load_state(target / ".agentbundle-state.toml")


# ---------------------------------------------------------------------------
# AC3, AC5, AC12, AC13 — ordered, one scope, one adapter, profile route
# ---------------------------------------------------------------------------


def test_profile_installs_ordered_one_scope_one_adapter_with_route(tmp_path):
    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)

    rc, out, err = _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert rc == 0, f"profile install failed: {err}"

    state = _repo_state(target)
    for name in ("pf-core", "pf-addon-a", "pf-addon-b"):
        assert name in state.packs, f"{name} missing from state"
        ps = state.packs[name]
        assert ps.install_route == "profile", f"{name} route={ps.install_route!r}"
        assert ps.scope == "repo"
        assert ps.adapter == "claude-code"

    # On-disk files landed under the one adapter's repo projection.
    assert (target / ".claude" / "skills" / "pf-core-skill" / "SKILL.md").exists()
    assert (target / ".claude" / "skills" / "pf-addon-a-skill" / "SKILL.md").exists()

    # Summary in authored deps-first order.
    assert out.index("pf-core") < out.index("pf-addon-a") < out.index("pf-addon-b")
    assert "installed" in out

    # No profile entity in state — only per-pack rows.
    assert "test-bundle" not in state.packs


def test_profile_state_schema_version_unchanged(tmp_path):
    from agentbundle.config import STATE_SCHEMA_VERSION

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)
    _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert _repo_state(target).schema_version == STATE_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# AC6 — already-installed packs skipped, refuse-on-reinstall not tripped
# ---------------------------------------------------------------------------


def test_profile_skips_already_installed(tmp_path):
    from agentbundle.config import PackState, State, dump_state

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)

    # Pre-seed pf-core at repo scope.
    state = State()
    state.packs["pf-core"] = PackState(installed_version="0.4.9", scope="repo")
    (target / ".agentbundle-state.toml").write_text(dump_state(state), encoding="utf-8")

    rc, out, err = _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert rc == 0, f"profile install failed: {err}"
    assert "pf-core: already present, skipped" in out
    assert "use 'upgrade'" not in err  # refuse-on-reinstall not tripped

    final = _repo_state(target)
    assert final.packs["pf-addon-a"].install_route == "profile"
    assert final.packs["pf-addon-b"].install_route == "profile"


# ---------------------------------------------------------------------------
# AC5 — pinned adapter disallowed by a batch pack → refuse before any write
# ---------------------------------------------------------------------------


def test_profile_refuses_when_a_pack_disallows_the_pinned_adapter(tmp_path):
    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    # pf-core legacy (→ claude-code default); pf-addon-b only allows codex.
    _stage_pack(cat, "pf-core", version="0.4.9", scope="repo")
    _stage_pack(cat, "pf-addon-b", scope="repo", deps=[("pf-core", "^0.1")],
                allowed_adapters=["codex"])
    _stage_profile(cat, "split", "repo", ["pf-core", "pf-addon-b"])

    rc, out, err = _run_install(["--profile", "split", str(cat), "--output", str(target)])
    assert rc == 1
    assert "pf-addon-b" in err
    assert "does not allow adapter 'claude-code'" in err
    assert "codex" in err  # compatible-adapter suggestion
    # Refused before any write: no state file, no projected files.
    assert not (target / ".agentbundle-state.toml").exists()
    assert not (target / ".claude").exists()


# ---------------------------------------------------------------------------
# AC4 — path-jail failure on a later pack aborts before any write
# ---------------------------------------------------------------------------


def test_profile_path_jail_on_later_pack_aborts_before_any_write(tmp_path, monkeypatch):
    from agentbundle import safety

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)

    # Simulate a path-jail escape for pf-addon-a's projection during the
    # read-only Step-8 probe (which runs inside the dry-run pre-flight).
    orig = safety.assert_under

    def fake_assert_under(root, target_path):
        if "pf-addon-a-skill" in str(target_path):
            raise safety.PathJailError("simulated jail escape for pf-addon-a")
        return orig(root, target_path)

    monkeypatch.setattr(safety, "assert_under", fake_assert_under)

    rc, out, err = _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert rc != 0
    assert "pre-flight failed for pack 'pf-addon-a'" in err
    # Zero files written for ANY pack — including the well-formed pf-core.
    assert not (target / ".agentbundle-state.toml").exists()
    assert not (target / ".claude").exists()


# ---------------------------------------------------------------------------
# AC8 — genuine write-phase I/O failure: consistent prefix + per-pack summary
# ---------------------------------------------------------------------------


def test_profile_partial_write_failure_leaves_consistent_prefix(tmp_path, monkeypatch):
    from agentbundle import safety

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)

    # WriteError (the genuine-I/O residual — distinct from PathJailError) on
    # pf-addon-a's write loop only. Pre-flight (dry-run) never calls
    # write_jailed, so all packs pass pre-flight; the failure is mid-write.
    orig = safety.write_jailed

    def fake_write_jailed(root, relpath, content, **kw):
        if "pf-addon-a-skill" in relpath:
            raise safety.WriteError("simulated disk full")
        return orig(root, relpath, content, **kw)

    monkeypatch.setattr(safety, "write_jailed", fake_write_jailed)

    rc, out, err = _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert rc == 1

    # pf-core (the prefix) persisted; pf-addon-a failed; no rollback.
    state = _repo_state(target)
    assert "pf-core" in state.packs
    assert (target / ".claude" / "skills" / "pf-core-skill" / "SKILL.md").exists()
    assert "pf-addon-a" not in state.packs
    assert not (target / ".claude" / "skills" / "pf-addon-a-skill").exists()

    # Per-pack summary reports the split, including the unattempted tail.
    assert "pf-core: installed" in out
    assert "pf-addon-a: failed" in out
    assert "pf-addon-b: not attempted" in out


# ---------------------------------------------------------------------------
# AC4/AC7 — pre-flight refusals through the orchestrator (before any write)
# ---------------------------------------------------------------------------


def test_profile_refuses_when_dep_preinstalled_at_unsatisfying_version(tmp_path):
    """A dep already on disk at a version that does not satisfy the range is
    refused at pre-flight — name-membership must not bypass the version check."""
    from agentbundle.config import PackState, State, dump_state

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _three_pack_repo_catalogue(cat)

    # pf-core present at 0.0.1 (does NOT satisfy pf-addon-a's pf-core ^0.1).
    state = State()
    state.packs["pf-core"] = PackState(installed_version="0.0.1", scope="repo")
    (target / ".agentbundle-state.toml").write_text(dump_state(state), encoding="utf-8")

    rc, out, err = _run_install(["--profile", "test-bundle", str(cat), "--output", str(target)])
    assert rc != 0
    assert "pre-flight failed for pack 'pf-addon-a'" in err
    # No addon files written (refused before any write).
    assert not (target / ".claude" / "skills" / "pf-addon-a-skill").exists()
    assert "pf-addon-a" not in _repo_state(target).packs


def test_profile_refuses_when_pack_requires_dep_not_in_batch(tmp_path):
    """A profile pack whose required dep is neither installed nor in the
    profile is refused through the orchestrator (AC4 dep precondition)."""
    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _stage_pack(cat, "pf-core", version="0.4.9", scope="repo")
    _stage_pack(cat, "pf-addon-a", scope="repo", deps=[("pf-core", "^0.1")])
    # Profile omits pf-core — pf-addon-a's dep is out of the batch.
    _stage_profile(cat, "incomplete", "repo", ["pf-addon-a"])

    rc, out, err = _run_install(["--profile", "incomplete", str(cat), "--output", str(target)])
    assert rc != 0
    assert "pre-flight failed for pack 'pf-addon-a'" in err
    assert not (target / ".agentbundle-state.toml").exists()


def test_profile_refuses_scope_mismatch(tmp_path):
    """A user-scope profile naming a repo-only pack is refused at pre-flight
    (AC4 scope precondition)."""
    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _stage_pack(cat, "pf-core", version="0.4.9", scope="repo")  # repo-only
    _stage_profile(cat, "userbad", "user", ["pf-core"])

    rc, out, err = _run_install(["--profile", "userbad", str(cat), "--output", str(target)])
    assert rc != 0
    assert "pre-flight failed for pack 'pf-core'" in err


def test_profile_refuses_pack_installed_at_opposite_scope(tmp_path, monkeypatch):
    """A profile pack already installed at the opposite scope is refused with a
    clear, profile-aware message (not the single-pack '--force' line)."""
    from agentbundle.config import PackState, State, dump_state
    from agentbundle import scope as scope_mod

    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    # Dual-scope packs so the user-scope profile is otherwise valid.
    _stage_pack(cat, "pf-tool", scope="user")
    # Make it dual-scope by hand (allowed-scopes both).
    (cat / "packs" / "pf-tool" / "pack.toml").write_text(
        '[pack]\nname = "pf-tool"\nversion = "0.1.0"\ndescription = "fixture"\n'
        '[pack.adapter-contract]\nversion = "0.6"\n'
        '[pack.install]\ndefault-scope = "user"\nallowed-scopes = ["user", "repo"]\n',
        encoding="utf-8",
    )
    (cat / "packs" / "pf-tool" / ".apm" / "skills" / "pf-tool-skill").mkdir(parents=True, exist_ok=True)
    (cat / "packs" / "pf-tool" / ".apm" / "skills" / "pf-tool-skill" / "SKILL.md").write_text(
        "---\ndescription: fixture.\n---\n\n# pf-tool\n", encoding="utf-8"
    )
    _stage_profile(cat, "userset", "user", ["pf-tool"])

    # Pre-install pf-tool at REPO scope (the opposite of the profile's user scope).
    repo_state = State()
    repo_state.packs["pf-tool"] = PackState(installed_version="0.1.0", scope="repo")
    (target / ".agentbundle-state.toml").write_text(dump_state(repo_state), encoding="utf-8")

    rc, out, err = _run_install(["--profile", "userset", str(cat), "--output", str(target)])
    assert rc == 1
    assert "already" in err and "repo scope" in err
    assert "--force" not in err  # not the misleading single-pack remedy


# ---------------------------------------------------------------------------
# AC13 — single-pack install still records install_route="cli"
# ---------------------------------------------------------------------------


def test_single_pack_install_still_records_cli_route(tmp_path):
    cat = tmp_path / "cat"
    target = tmp_path / "repo"
    target.mkdir()
    _stage_pack(cat, "pf-core", version="0.4.9", scope="repo")

    rc, out, err = _run_install(["--pack", "pf-core", str(cat), "--output", str(target)])
    assert rc == 0, f"single-pack install failed: {err}"
    assert _repo_state(target).packs["pf-core"].install_route == "cli"
