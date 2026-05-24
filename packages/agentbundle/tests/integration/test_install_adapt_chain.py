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
    """Per AC19b: the chained `adapt` runs in-process *and* substitutes
    markers. Both halves are asserted — the negative (no subprocess)
    *and* the positive (the chain actually executed and applied
    `[markers]` values to a projected file)."""
    import subprocess

    cat = tmp_path / "cat"
    # Stage a pack with an `<adapt:owner>` marker in a primitive file
    # that the projection picks up. The chain runs adapt with
    # --values-from <repo>/.adapt-discovery.toml; after install, the
    # projected file must contain the substituted value, not the
    # literal marker.
    pack_body = ADDON_NO_DEPENDENCIES
    pack = _stage_pack(cat, "addon", pack_body)
    (pack / ".apm" / "skills" / "demo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: x\n---\nowner=<adapt:owner>\n",
        encoding="utf-8",
    )
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
    # Positive assertion: the projected file got the substituted value
    # (chained adapt actually executed), not the literal `<adapt:owner>`.
    # The projection target depends on the adapter's projection rule;
    # walk the install target for the substituted token.
    found_substituted = False
    found_unsubstituted = False
    for p in target.rglob("*"):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        if "owner=octocat" in text:
            found_substituted = True
        if "<adapt:owner>" in text:
            found_unsubstituted = True
    assert found_substituted, (
        "chained adapt did not substitute <adapt:owner>; the chain "
        "may have been skipped entirely"
    )
    assert not found_unsubstituted, (
        "chained adapt left an unsubstituted <adapt:owner> marker on disk"
    )


def test_marker_in_seed_gitignore(tmp_path):
    """AC19c: invoking `agentbundle scaffold` against the core pack lays
    down a `.gitignore` containing `.adapt-install-marker.toml`.

    Drives the scaffold command end-to-end against a tmp output dir
    rather than checking the seed file directly — so a refactor that
    silently dropped dotfile projection (e.g., a switch from
    `Path.rglob` to a glob library that needs `include_hidden=True`,
    an added dotfile filter in the seeds walk, or a `.gitignore`-
    specific skip) would trip the test instead of slipping past.
    """
    from agentbundle.commands.scaffold import run as scaffold_run

    packs_dir = Path(__file__).resolve().parents[4] / "packs"
    output = tmp_path / "out"
    output.mkdir()
    ns = argparse.Namespace(
        pack="core",
        packs_dir=str(packs_dir),
        output=str(output),
    )
    rc = scaffold_run(ns)
    assert rc == 0, "scaffold against core pack should succeed"
    projected = output / ".gitignore"
    assert projected.exists(), (
        f"scaffold did not project .gitignore from packs/core/seeds/ "
        f"into {output}"
    )
    body = projected.read_text(encoding="utf-8")
    assert ".adapt-install-marker.toml" in body, (
        "projected .gitignore is missing the install-marker line; "
        f"scaffold output was:\n{body}"
    )


USER_ONLY_PACK = """\
[pack]
name = "user-only"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
"""


def test_user_scope_only_install_chains_adapt_against_args_output(tmp_path, monkeypatch):
    """User-scope-only install exercises `_chain_adapt`'s fallback path
    (no repo plan in `plans`, so `repo_root_for_adapt =
    Path(args.output).resolve()`).

    Contract pinned: the fallback resolves to `args.output`, not to
    `cwd`, `$HOME`, or any other path. To make that load-bearing the
    test seeds a sentinel `.adapt-discovery.toml` at `args.output`
    *only* and asserts two positive signals from the chained adapt:

      1. No no-discovery nudge in stderr — the chain found the
         discovery file at the path it resolved.
      2. `.adapt-pending.md` lands at `<args.output>/.adapt-pending.md`
         — the per-scope walk ran with `repo_root = args.output`,
         not some sibling path.

    A refactor that swapped the fallback to `Path.cwd()`, `$HOME`, or
    `Path("/tmp/whatever")` would trip *both* assertions in this
    fixture: no discovery file at those paths, no pending.md at
    target. The user-scope state file at `<HOME>/.agent-ready/state.toml`
    confirms the user-scope write path ran independently of the chain.
    """
    cat = tmp_path / "cat"
    _stage_pack(cat, "user-only", USER_ONLY_PACK)
    target = tmp_path / "repo"
    target.mkdir()
    # Sentinel discovery file at args.output. The fallback path must
    # resolve here for the chained adapt to find it.
    (target / ".adapt-discovery.toml").write_text(
        'discovery-schema-version = "0.1"\n[markers]\nowner = "octocat"\n',
        encoding="utf-8",
    )
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc, _, err = _install(
        dict(pack="user-only", catalogue=str(cat), output=str(target), scope="user", force=False)
    )
    assert rc == 0, f"user-scope-only install failed: {err}"
    # User-scope state file landed at the namespaced dot-directory.
    assert (fake_home / ".agent-ready" / "state.toml").exists(), (
        "user-scope install did not write state.toml at <HOME>/.agent-ready/"
    )
    # Discriminating assertion (1): the chain found the seeded discovery,
    # so the no-discovery nudge stays out of stderr.
    assert (
        "no .adapt-discovery.toml at repo root" not in err
    ), (
        "chain emitted the no-discovery nudge, meaning the fallback "
        "resolved to a path other than args.output; stderr was:\n" + err
    )
    # Discriminating assertion (2): the per-scope walk ran with
    # repo_root = args.output (the only place pending.md can land for
    # the repo scope of the chained adapt).
    assert (target / ".adapt-pending.md").exists(), (
        "chained adapt did not write pending.md at args.output; the "
        "fallback may have resolved to a different path"
    )
