"""T8: ``agentbundle creds`` CLI verb (skill-secrets spec § AC16-AC23).

Covers the four subcommands (``setup``, ``check``, ``where``, ``rm``),
the tombstone-argument refusal (AC23), the no-``get`` negative test
(AC21), the per-platform tier-selection paths (AC16, AC22), the
non-tty stdin refusal (AC23 POSIX path), and the dual-scope state walk
for namespace enumeration (AC17).

In-process calls via ``agentbundle.cli.main`` cover everything that
doesn't need a real shell; the non-tty path uses ``subprocess`` so
``sys.stdin.isatty()`` actually returns ``False`` (rather than being
monkeypatched, which lets a buggy implementation pass).
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


# Sentinel anchor — AC23 documents this exact byte sequence and the
# test grep enforces it verbatim. Keep in sync with ``creds.py``'s
# ``_ARGV_REFUSAL_STDERR``.
ARGV_REFUSAL_SENTINEL = "tokens cannot be passed via argv"


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Redirect HOME / USERPROFILE so the dotfile and user-scope state
    walk land in ``tmp_path``; reset Tier-2 backend so each test owns
    its platform shape via monkeypatch (no leakage from earlier tests).
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for var in list(os.environ):
        if var.startswith("FIXTURE_T8_"):
            monkeypatch.delenv(var, raising=False)
    from agentbundle.creds import loader
    monkeypatch.setattr(loader, "_tier2_backend", None)
    return tmp_path


def _write_skill_fixture(
    root: Path,
    skill_name: str,
    namespace: str,
    *,
    secret_keys: tuple[str, ...] = ("API_TOKEN",),
    nonsecret_keys: tuple[str, ...] = (),
) -> Path:
    """Materialise a credentialed-skill fixture under ``root``.

    Writes:
      - ``<root>/.claude/skills/<skill_name>/SKILL.md`` with
        ``metadata.credentialed: true`` frontmatter (under the
        agentskills.io spec's ``metadata:`` escape hatch).
      - ``<root>/.claude/skills/<skill_name>/references/creds-schema.toml``
        declaring the requested keys.

    Returns the SKILL.md path.
    """
    skill_dir = root / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        textwrap.dedent(f"""\
            ---
            name: {skill_name}
            description: fixture credentialed skill for T8 testing
            metadata:
              credentialed: true
              primitive-class: credentialed-cli
            ---

            # Skill: {skill_name}
            """),
        encoding="utf-8",
    )
    schema_path = skill_dir / "references" / "creds-schema.toml"
    parts = [f'[namespace]\nname = "{namespace}"\n']
    for k in secret_keys:
        parts.append(
            f'\n[[namespace.keys]]\nname = "{k}"\nlabel = "{k}"\nsecret = true\n'
        )
    for k in nonsecret_keys:
        parts.append(
            f'\n[[namespace.keys]]\nname = "{k}"\nlabel = "{k}"\nsecret = false\n'
        )
    schema_path.write_text("".join(parts), encoding="utf-8")
    return skill_md


def _write_state_file(
    root: Path,
    pack: str,
    skill_relpaths: tuple[str, ...],
    *,
    user_scope: bool = False,
) -> Path:
    """Write a v0.3 ``.agentbundle-state.toml`` listing the given skills
    under ``[pack.<pack>.files]``.

    ``user_scope`` toggles the file location: ``<root>/.agentbundle-state.toml``
    (repo) or ``<root>/.agentbundle/state.toml`` (user, mirroring
    ``$HOME/.agentbundle/state.toml`` semantics).
    """
    if user_scope:
        path = root / ".agentbundle" / "state.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        scope_label = "user"
    else:
        path = root / ".agentbundle-state.toml"
        scope_label = "repo"
    lines = ['schema-version = "0.3"', "", f"[pack.{pack}]"]
    lines.append('installed-version = "0.0.1"')
    lines.append(f'scope = "{scope_label}"')
    for relpath in skill_relpaths:
        lines.append(f'\n[pack.{pack}.files."{relpath}"]')
        lines.append('sha = "deadbeefdeadbeef"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _install_fake_tier2(monkeypatch):
    """Install an in-memory Tier-2 backend so AC16/AC22 paths can be
    exercised without a real OS keyring. Returns the dict used by the
    fake backend so tests can inspect what was written.
    """
    from agentbundle.creds import loader

    store: dict[tuple[str, str], str] = {}

    class _Fake:
        @staticmethod
        def read_credential(namespace, key):
            return store.get((namespace, key))

        @staticmethod
        def write_credential(namespace, key, value):
            store[(namespace, key)] = value

        @staticmethod
        def delete_credential(namespace, key):
            store.pop((namespace, key), None)

    monkeypatch.setattr(loader, "_tier2_backend", _Fake)
    # Also patch ``sys.platform`` so the stderr label says "macOS
    # Keychain" or "Windows Credential Manager" (platform-discriminated
    # in ``_tier2_label``). On a real Darwin host the label already
    # matches; on Linux CI we need the override.
    if sys.platform not in ("darwin", "win32"):
        monkeypatch.setattr(sys, "platform", "darwin")
    return store


def _set_inputs(monkeypatch, *, secret_values: dict[str, str] | None = None,
                input_values: list[str] | None = None,
                isatty: bool = True):
    """Plumb fake answers into ``getpass.getpass``, ``input``, and
    ``sys.stdin.isatty`` for the in-process CLI calls.

    ``secret_values`` maps the *prompt label suffix* to the secret value
    so multiple keys can be answered in order; falling back to a single
    deterministic value when not specified.
    """
    from agentbundle.commands import creds as creds_mod

    def fake_getpass(prompt):
        if secret_values is None:
            return "secret-value"
        # Match by the trailing ``": "`` separator on the prompt.
        key = prompt.rstrip(": ").strip()
        return secret_values.get(key, "secret-value")

    input_iter = iter(input_values or [])

    def fake_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            return ""

    monkeypatch.setattr(creds_mod.getpass, "getpass", fake_getpass)
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: isatty)


def _run(argv):
    """Invoke the CLI in-process and return its exit code."""
    from agentbundle.cli import main
    return main(argv)


# ── AC21: no ``get`` subcommand ───────────────────────────────────────


def test_get_subcommand_returns_unknown_command(capsys):
    """AC21: ``agentbundle creds get foo`` exits non-zero with the
    documented stderr text ``unknown command: get``."""
    with pytest.raises(SystemExit) as exc:
        _run(["creds", "get", "foo"])
    assert exc.value.code != 0
    out = capsys.readouterr()
    assert "unknown command: get" in out.err


def test_creds_with_no_subcommand_exits_three(capsys):
    """``agentbundle creds`` (no subcommand) exits 3 with stderr naming
    the available subcommands. Not a spec AC anchor — defensive against
    a silent no-op (the dispatcher would otherwise reach
    ``creds.run`` with ``creds_func=None`` and return 3).
    """
    rc = _run(["creds"])
    assert rc == 3
    out = capsys.readouterr()
    assert "subcommand is required" in out.err
    for verb in ("setup", "check", "where", "rm"):
        assert verb in out.err


# ── AC23: tombstone argv arguments ────────────────────────────────────


@pytest.mark.parametrize("flag", [
    "--token", "--api-token", "--api-key",
    "--bearer", "--pat", "--password",
])
def test_setup_refuses_argv_borne_token(flag, capsys):
    """AC23: every named tombstone flag emits the canonical stderr
    sentinel and exits non-zero."""
    with pytest.raises(SystemExit) as exc:
        _run(["creds", "setup", flag, "leaked-token", "ns"])
    assert exc.value.code != 0
    out = capsys.readouterr()
    assert ARGV_REFUSAL_SENTINEL in out.err


@pytest.mark.parametrize("flag", [
    "--token", "--api-token", "--api-key",
    "--bearer", "--pat", "--password",
])
def test_setup_refuses_bare_tombstone_flag_with_no_value(flag, capsys):
    """AC23 corner case: the tombstone action uses ``nargs="?"`` so the
    flag fires whether a value follows it or not. Bare ``--token``
    (with no following value) must still produce the canonical
    sentinel — a future change to ``nargs`` could silently regress this.
    """
    with pytest.raises(SystemExit) as exc:
        _run(["creds", "setup", flag])
    assert exc.value.code != 0
    out = capsys.readouterr()
    assert ARGV_REFUSAL_SENTINEL in out.err


def test_setup_refuses_equals_form_tombstone_flag(capsys):
    """AC23: ``--token=leaked`` (equals-sign form, single argv token)
    also fires the action — argparse routes single-token ``--flag=val``
    through the same action as multi-token ``--flag val``.
    """
    with pytest.raises(SystemExit) as exc:
        _run(["creds", "setup", "--token=leaked", "ns"])
    assert exc.value.code != 0
    out = capsys.readouterr()
    assert ARGV_REFUSAL_SENTINEL in out.err


def test_argv_refusal_does_not_leak_to_other_creds_verbs(capsys):
    """AC23: tombstone scope is the ``setup`` subparser only.

    ``creds check --token foo bar`` falls through to argparse's default
    ``unrecognized arguments`` shape — the verbatim sentinel is *not*
    emitted because the flag wasn't registered on ``check``.
    """
    with pytest.raises(SystemExit):
        _run(["creds", "check", "--token", "foo", "ns"])
    out = capsys.readouterr()
    assert ARGV_REFUSAL_SENTINEL not in out.err


def test_argv_refusal_does_not_pollute_other_verbs(capsys):
    """AC23: tombstone scope is the ``creds setup`` subparser only. Other
    top-level verbs keep their argparse-default behaviour.

    ``install --pack core --token foo <catalogue>`` lets argparse parse
    past the required flags and reach the ``--token`` token; we then
    assert the canonical sentinel does **not** appear in stderr. (A
    bare ``install --token foo .`` would error on missing ``--pack``
    before the tombstone path could even be considered, which would
    make this test pass without exercising the contract — hence the
    fully-formed argv.)
    """
    with pytest.raises(SystemExit):
        _run([
            "install", "--pack", "core", "--token", "foo",
            "/nonexistent-catalogue-fixture",
        ])
    out = capsys.readouterr()
    assert ARGV_REFUSAL_SENTINEL not in out.err


# ── AC17: dual-scope state walk for namespace enumeration ─────────────


def test_setup_no_arg_walks_state_files(tmp_path, monkeypatch, capsys):
    """AC17: ``creds setup`` (no positional) walks both scope state
    files, lists each credentialed primitive with its scope, and prompts
    via ``input()`` for a selection.
    """
    # Repo-scope fixture: skill ``alpha`` declaring namespace ``alpha``.
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    # User-scope fixture (via HOME redirection in the autouse fixture):
    # ``$HOME/.claude/skills/beta/SKILL.md`` listed in
    # ``$HOME/.agentbundle/state.toml``.
    _write_skill_fixture(tmp_path, "beta", "beta")
    _write_state_file(
        tmp_path, "user-pack", (".claude/skills/beta/SKILL.md",),
        user_scope=True,
    )
    _install_fake_tier2(monkeypatch)
    _set_inputs(monkeypatch, input_values=["1"], isatty=True)

    rc = _run(["creds", "setup", "--root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr()
    # The listing shows each skill with its scope label.
    assert "alpha" in out.err
    assert "beta" in out.err
    assert "repo" in out.err
    assert "user" in out.err


def test_setup_no_arg_empty_state_exits_3(tmp_path, monkeypatch, capsys):
    """AC17 boundary: no credentialed primitives installed at either
    scope → exit 3 with stderr naming the situation."""
    _set_inputs(monkeypatch, isatty=True)
    rc = _run(["creds", "setup", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "no credentialed primitives" in out.err


# ── AC16: setup writes to the right tier per platform ────────────────


def test_setup_writes_to_tier2_on_capable_platform(tmp_path, monkeypatch, capsys):
    """AC16: on Darwin/Windows (Tier-2-capable), ``setup <namespace>``
    writes to the keyring and stderr matches ``wrote to keyring``."""
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    store = _install_fake_tier2(monkeypatch)
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "kr-secret"},
        isatty=True,
    )
    rc = _run(["creds", "setup", "alpha", "--root", str(tmp_path)])
    assert rc == 0
    assert store[("alpha", "API_TOKEN")] == "kr-secret"
    out = capsys.readouterr()
    assert "wrote to keyring" in out.err


def test_setup_writes_to_tier3_on_linux(tmp_path, monkeypatch, capsys):
    """AC16: on Linux (Tier 2 unavailable) the helper writes to the
    Tier-3 dotfile and stderr matches
    ``wrote to dotfile (Linux — Tier 2 deferred to v2 RFC)``.
    """
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    # No fake Tier 2 — _tier2_backend stays None per the autouse fixture.
    monkeypatch.setattr(sys, "platform", "linux")
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "dot-secret"},
        isatty=True,
    )
    rc = _run(["creds", "setup", "alpha", "--root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr()
    assert "wrote to dotfile" in out.err
    assert "Linux" in out.err
    # The dotfile carries the namespaced key.
    dotfile = tmp_path / ".agentbundle" / "credentials.env"
    assert "ALPHA_API_TOKEN=dot-secret" in dotfile.read_text()


def test_setup_insecure_fallback_on_capable_platform(
    tmp_path, monkeypatch, capsys
):
    """AC22: ``--allow-insecure-fallback`` on a Tier-2-capable platform
    writes to Tier 3 and stderr matches
    ``wrote to dotfile (insecure fallback)``.
    """
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    store = _install_fake_tier2(monkeypatch)
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "fb-secret"},
        isatty=True,
    )
    rc = _run([
        "creds", "setup", "alpha",
        "--allow-insecure-fallback",
        "--root", str(tmp_path),
    ])
    assert rc == 0
    out = capsys.readouterr()
    assert "wrote to dotfile" in out.err
    assert "insecure fallback" in out.err
    # The Tier-2 store was *not* written.
    assert ("alpha", "API_TOKEN") not in store


def test_setup_allow_permissive_acl_refuses_without_flag(
    tmp_path, monkeypatch, capsys
):
    """AC15 + AC22: a Tier-3 write whose Windows DACL parse raises
    ``PermissiveAclError`` exits 3 with stderr matching ``DACL too
    permissive`` when ``--allow-permissive-acl`` was not passed.

    Simulated via a monkeypatched ``_dotfile_write`` that raises on the
    no-flag path so the test runs on any host (Windows-only icacls is
    unreachable from Darwin CI).
    """
    from agentbundle.creds import loader
    from agentbundle.creds.exceptions import PermissiveAclError

    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setattr(sys, "platform", "linux")  # force Tier-3 path

    def fake_write(namespace, key, value, *, allow_permissive_acl=False):
        if not allow_permissive_acl:
            raise PermissiveAclError(
                f"DACL on {tmp_path} grants BUILTIN\\Users:R"
            )

    monkeypatch.setattr(loader, "_dotfile_write", fake_write)
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "x"},
        isatty=True,
    )
    rc = _run(["creds", "setup", "alpha", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "DACL too permissive" in out.err


def test_setup_allow_permissive_acl_accepts_with_flag(
    tmp_path, monkeypatch, capsys
):
    """AC15 + AC22: ``--allow-permissive-acl`` passes
    ``allow_permissive_acl=True`` through to ``_dotfile_write`` so the
    write succeeds even against a permissive DACL fixture; exit 0.
    """
    from agentbundle.creds import loader

    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setattr(sys, "platform", "linux")

    captured_kwargs: list[bool] = []

    def fake_write(namespace, key, value, *, allow_permissive_acl=False):
        captured_kwargs.append(allow_permissive_acl)

    monkeypatch.setattr(loader, "_dotfile_write", fake_write)
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "x"},
        isatty=True,
    )
    rc = _run([
        "creds", "setup", "alpha",
        "--allow-permissive-acl",
        "--root", str(tmp_path),
    ])
    assert rc == 0
    assert captured_kwargs == [True]


def test_setup_secret_and_nonsecret_keys_round_trip(tmp_path, monkeypatch):
    """AC24 + AC16: ``secret = true`` keys go through ``getpass``;
    ``secret = false`` keys go through ``input``. End-to-end via the
    Linux Tier-3 path so both values land in the dotfile."""
    _write_skill_fixture(
        tmp_path, "alpha", "alpha",
        secret_keys=("API_TOKEN",), nonsecret_keys=("BASE_URL",),
    )
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setattr(sys, "platform", "linux")
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "kr-tok"},
        input_values=["https://alpha.test"],
        isatty=True,
    )
    rc = _run(["creds", "setup", "alpha", "--root", str(tmp_path)])
    assert rc == 0
    dotfile_text = (tmp_path / ".agentbundle" / "credentials.env").read_text()
    assert "ALPHA_API_TOKEN=kr-tok" in dotfile_text
    assert "ALPHA_BASE_URL=" in dotfile_text


# ── AC18: check exit codes ────────────────────────────────────────────


def test_check_exits_zero_when_all_keys_resolve(tmp_path, monkeypatch):
    """AC18: every required key resolved at some tier → exit 0."""
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setenv("ALPHA_API_TOKEN", "from-env")
    rc = _run(["creds", "check", "alpha", "--root", str(tmp_path)])
    assert rc == 0


def test_check_exits_two_when_required_key_missing(tmp_path, capsys):
    """AC18: any missing key → exit 2, stderr names the missing keys."""
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    rc = _run(["creds", "check", "alpha", "--root", str(tmp_path)])
    assert rc == 2
    out = capsys.readouterr()
    assert "API_TOKEN" in out.err
    assert "missing" in out.err


def test_check_exits_three_on_unknown_namespace(tmp_path, capsys):
    """AC18: an unknown namespace (no skill declares it) is an "other"
    error → exit 3."""
    rc = _run(["creds", "check", "absent", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "absent" in out.err


def test_check_exits_three_on_malformed_schema(tmp_path, capsys):
    """AC18: a malformed schema is the spec's "other error" bucket
    (schema parse error → exit 3). The stderr surfaces the underlying
    parser error (``malformed``) rather than swallowing it inside the
    generic "no namespace declares..." message — operators need the
    root cause."""
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    # Stomp the schema with malformed TOML.
    (tmp_path / ".claude" / "skills" / "alpha" / "references"
     / "creds-schema.toml").write_text("this = is not [[ valid", encoding="utf-8")
    rc = _run(["creds", "check", "alpha", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "malformed" in out.err


# ── AC19: where prints per-key tier (no values) ───────────────────────


def test_where_prints_tier_per_key_no_values(tmp_path, monkeypatch, capsys):
    """AC19: ``where`` prints ``<KEY>: <tier>`` per required key.

    Across three keys we hit env, dotfile, and missing — confirming
    every label in the matrix at least once and that no value is leaked.
    """
    _write_skill_fixture(
        tmp_path, "alpha", "alpha",
        secret_keys=("API_TOKEN", "OTHER_SECRET", "ABSENT_KEY"),
    )
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setenv("ALPHA_API_TOKEN", "secret-env-value")
    # Stash OTHER_SECRET in the dotfile.
    from agentbundle.creds import loader
    loader._dotfile_write("alpha", "OTHER_SECRET", "dotfile-value")
    rc = _run(["creds", "where", "alpha", "--root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr()
    assert "API_TOKEN: env" in out.out
    assert "OTHER_SECRET: dotfile" in out.out
    assert "ABSENT_KEY: missing" in out.out
    # No value bytes leak — only tier labels.
    assert "secret-env-value" not in out.out
    assert "dotfile-value" not in out.out


# ── AC20: rm clears every tier holding the key ────────────────────────


def test_rm_removes_keys_from_keyring_and_dotfile(tmp_path, monkeypatch):
    """AC20: ``rm <namespace>`` deletes every key from every tier that
    holds it.

    Set up: API_TOKEN in keyring, BASE_URL in dotfile. After ``rm``,
    neither holds anything.
    """
    _write_skill_fixture(
        tmp_path, "alpha", "alpha",
        secret_keys=("API_TOKEN",), nonsecret_keys=("BASE_URL",),
    )
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    store = _install_fake_tier2(monkeypatch)
    store[("alpha", "API_TOKEN")] = "kr"
    from agentbundle.creds import loader
    loader._dotfile_write("alpha", "BASE_URL", "https://alpha.test")
    rc = _run(["creds", "rm", "alpha", "--root", str(tmp_path)])
    assert rc == 0
    assert ("alpha", "API_TOKEN") not in store
    assert loader._dotfile_read("alpha", "BASE_URL") is None


def test_rm_refuses_when_nothing_to_remove(tmp_path, capsys, monkeypatch):
    """AC20: helper refuses (stderr + non-zero) when no tier holds any
    of the namespace's keys."""
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    rc = _run(["creds", "rm", "alpha", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "nothing to remove" in out.err


def test_rm_notes_env_var_present_but_unremovable(tmp_path, monkeypatch, capsys):
    """AC20: env clears are documented on stderr ("the helper cannot
    unset another process's environ"). Env DOES count as "a tier that
    holds the key" — the helper does **not** refuse (spec § AC20:
    "refuses ... if no tier holds any of the namespace's keys"); it
    documents the env situation and exits 0.
    """
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setenv("ALPHA_API_TOKEN", "env-only")
    rc = _run(["creds", "rm", "alpha", "--root", str(tmp_path)])
    out = capsys.readouterr()
    assert "ALPHA_API_TOKEN" in out.err
    assert "unset manually" in out.err
    assert rc == 0


# ── AC23: setup refuses non-tty stdin (POSIX path) ────────────────────


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX tty-isatty path")
def test_setup_refuses_non_tty_stdin_via_subprocess(tmp_path):
    """AC23 POSIX path: real ``stdin=subprocess.DEVNULL`` (so
    ``sys.stdin.isatty()`` actually returns ``False`` for the child),
    helper exits non-zero with a categorised ``stdin-not-tty`` prefix
    that security tooling can pattern-match without parsing the body.
    """
    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    repo_root = Path(__file__).resolve().parents[3]
    pkg_root = repo_root / "packages" / "agentbundle"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PYTHONPATH"] = str(pkg_root) + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run(
        [
            sys.executable, "-m", "agentbundle", "creds", "setup",
            "alpha", "--root", str(tmp_path),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode != 0
    # AC23 categorised prefix (Adversarial Concern #11): the stderr
    # line is distinct from the argv-refusal path.
    assert "creds setup: stdin-not-tty:" in res.stderr


# ── AC11+AC18: read-path Tier-2 hard fail propagates (exit 3) ─────────


def test_check_exits_three_on_tier2_hard_fail_during_read(
    tmp_path, monkeypatch, capsys
):
    """AC11 + AC18: a Tier-2 ``read_credential`` that raises
    ``Tier2HardFailError`` must not be swallowed by ``_tier_for_key``
    and reported as ``"missing"`` (exit 2). The contract is exit 3,
    stderr names the cause; the Boundaries § Never do clause
    "No silent fallback from hard-fail Win32 error codes" depends on
    this propagation.
    """
    from agentbundle.creds import loader
    from agentbundle.creds.exceptions import Tier2HardFailError

    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setattr(sys, "platform", "darwin")

    class _ReadHardFail:
        @staticmethod
        def read_credential(*a, **kw):
            raise Tier2HardFailError(
                "ERROR_NO_SUCH_LOGON_SESSION (1312) — no logon session"
            )

        @staticmethod
        def write_credential(*a, **kw):
            return None

        @staticmethod
        def delete_credential(*a, **kw):
            return None

    monkeypatch.setattr(loader, "_tier2_backend", _ReadHardFail)
    rc = _run(["creds", "check", "alpha", "--root", str(tmp_path)])
    assert rc == 3, (
        "AC11 + AC18 contract: read-path Tier-2 hard fail must exit 3 "
        "(not 2 / missing). _tier_for_key swallowed the exception if "
        "this assertion fired with rc=2."
    )
    out = capsys.readouterr()
    assert "ERROR_NO_SUCH_LOGON_SESSION" in out.err or "Tier 2" in out.err, (
        f"stderr should name the Tier-2 hard-fail cause; got: {out.err!r}"
    )


# ── AC22: setup hard-fails when Tier-2 errors without opt-out ─────────


def test_setup_tier2_hard_fail_without_opt_out_exits_three(
    tmp_path, monkeypatch, capsys
):
    """AC22: a Tier-2 hard fail without ``--allow-insecure-fallback``
    exits 3 with stderr naming the cause."""
    from agentbundle.creds import loader
    from agentbundle.creds.exceptions import Tier2HardFailError

    _write_skill_fixture(tmp_path, "alpha", "alpha")
    _write_state_file(tmp_path, "core", (".claude/skills/alpha/SKILL.md",))
    monkeypatch.setattr(sys, "platform", "darwin")

    class _HardFail:
        @staticmethod
        def read_credential(*a, **kw):
            return None

        @staticmethod
        def write_credential(namespace, key, value):
            raise Tier2HardFailError("keychain locked")

        @staticmethod
        def delete_credential(*a, **kw):
            return None

    monkeypatch.setattr(loader, "_tier2_backend", _HardFail)
    _set_inputs(
        monkeypatch,
        secret_values={"API_TOKEN": "x"},
        isatty=True,
    )
    rc = _run(["creds", "setup", "alpha", "--root", str(tmp_path)])
    assert rc == 3
    out = capsys.readouterr()
    assert "Tier 2 hard fail" in out.err
    assert "--allow-insecure-fallback" in out.err


# ── Schema resolution diagnostics ─────────────────────────────────────


def test_namespace_resolves_via_user_scope_state(tmp_path, monkeypatch):
    """AC17 corollary: a credentialed primitive installed at user scope
    (not repo) still resolves for ``check`` / ``where`` / ``rm``."""
    _write_skill_fixture(tmp_path, "beta", "beta")
    _write_state_file(
        tmp_path, "user-pack", (".claude/skills/beta/SKILL.md",),
        user_scope=True,
    )
    monkeypatch.setenv("BETA_API_TOKEN", "user-scope-env")
    rc = _run(["creds", "check", "beta", "--root", str(tmp_path)])
    assert rc == 0
