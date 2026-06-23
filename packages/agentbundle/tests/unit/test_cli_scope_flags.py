"""T16: argparse surface gains --scope on six subcommands + --force on install.

Verifies AC #(RFC-0004) for the agent-spec-cli spec:
  - --scope {repo,user} is accepted on install, uninstall, upgrade, diff,
    init-state, and list-targets.
  - Passing --scope to any forbidden subcommand (list-packs, scaffold,
    validate, render, adapt) exits non-zero with the documented stderr
    `unknown flag for <verb>: --scope`. Parametrised across both
    space-separated (`--scope user`) and value-glued (`--scope=user`)
    forms.
  - --force is accepted only on install; any other verb refuses with
    `unknown flag for <verb>: --force`.
  - --scope <bogus> is rejected with argparse's invalid-choice error.

The custom ArgumentParser subclass `_VerbAwareParser` in cli.py rewrites
the "unrecognized arguments" message — the test pins the exact stderr
text byte-for-byte for both flag forms.
"""

from __future__ import annotations

import contextlib
import io
import pytest

from agentbundle import cli


# A minimal set of "valid trailing args" per subcommand so the parse
# reaches the --scope token rather than failing earlier on a missing
# positional. Each entry is the argv list (already-split). The
# subcommand under test is appended at the call site.
_BASE_ARGS = {
    "install": ["--pack", "core", "/fake/catalogue"],
    "uninstall": ["--pack", "core"],
    "upgrade": ["--pack", "core", "/fake/catalogue"],
    "diff": ["packs/core"],
    "init-state": ["--pack", "core"],
    "list-targets": [],
    "list-packs": ["/fake/catalogue"],
    "scaffold": ["--output", "/tmp/out"],
    "validate": ["packs/core"],
    "render": ["packs/core", "--output", "/tmp/out"],
    "adapt": [],
}


def _parse(argv: list[str]) -> tuple[int | None, str]:
    """Parse with cli._build_parser; return (exit_code_or_none, stderr_text)."""
    parser = cli._build_parser()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        try:
            parser.parse_args(argv)
        except SystemExit as exc:
            return exc.code, buf.getvalue()
    return None, buf.getvalue()


# ---------------------------------------------------------------------------
# --scope is accepted on the six subcommands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subcommand",
    ["install", "uninstall", "upgrade", "diff", "init-state", "list-targets"],
)
@pytest.mark.parametrize("flag_form", ["space", "glued"])
def test_scope_accepted(subcommand, flag_form):
    args = [subcommand] + _BASE_ARGS[subcommand]
    if flag_form == "space":
        args += ["--scope", "user"]
    else:
        args += ["--scope=user"]
    rc, err = _parse(args)
    assert rc is None, (
        f"--scope rejected on {subcommand!r} ({flag_form}): exit={rc}, "
        f"stderr={err!r}"
    )


# ---------------------------------------------------------------------------
# --scope is rejected on the five forbidden subcommands with exact stderr
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subcommand", ["list-packs", "scaffold", "validate", "render", "adapt"]
)
@pytest.mark.parametrize("flag_form", ["space", "glued"])
def test_scope_rejected_with_documented_stderr(subcommand, flag_form):
    args = [subcommand] + _BASE_ARGS[subcommand]
    if flag_form == "space":
        args += ["--scope", "user"]
    else:
        args += ["--scope=user"]
    rc, err = _parse(args)
    assert rc != 0, f"{subcommand} {flag_form}: parse succeeded but should refuse"
    # Exact byte-for-byte match on the documented contract.
    assert f"unknown flag for {subcommand}: --scope\n" == err, (
        f"{subcommand} {flag_form}: stderr mismatch.\nGot: {err!r}"
    )


# ---------------------------------------------------------------------------
# --force is rejected on every verb other than install with exact stderr
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subcommand",
    [
        "list-packs", "list-targets", "scaffold", "validate", "render",
        "adapt", "diff", "upgrade", "uninstall", "init-state",
    ],
)
def test_force_rejected_on_non_install(subcommand):
    args = [subcommand] + _BASE_ARGS[subcommand] + ["--force"]
    rc, err = _parse(args)
    assert rc != 0, f"{subcommand}: --force was accepted but only install permits it"
    assert f"unknown flag for {subcommand}: --force\n" == err, (
        f"{subcommand}: stderr mismatch.\nGot: {err!r}"
    )


def test_force_accepted_on_install():
    args = ["install"] + _BASE_ARGS["install"] + ["--force"]
    rc, err = _parse(args)
    assert rc is None, f"--force rejected on install: rc={rc} stderr={err!r}"


# ---------------------------------------------------------------------------
# --scope value validation
# ---------------------------------------------------------------------------


def test_scope_bogus_value_rejected():
    """argparse's `choices=...` rejects values outside {repo, user}."""
    args = ["install"] + _BASE_ARGS["install"] + ["--scope", "global"]
    rc, err = _parse(args)
    assert rc != 0
    # Default argparse text — not rewritten because the flag is recognised.
    assert "invalid choice" in err
    assert "repo" in err and "user" in err


# ---------------------------------------------------------------------------
# upgrade: --to removed, --yes added, primitive flags mutually exclusive
# ---------------------------------------------------------------------------


def test_upgrade_no_version_argument_parses():
    """`upgrade --pack core <catalogue>` parses with no version argument; the
    target version is derived from the catalogue, so the namespace carries no
    `to_version`."""
    parser = cli._build_parser()
    args = parser.parse_args(["upgrade", "--pack", "core", "/fake/catalogue"])
    assert not hasattr(args, "to_version")


def test_upgrade_to_flag_removed():
    """The `--to` flag is gone — passing it is now an unknown argument."""
    rc, err = _parse(["upgrade", "--pack", "core", "--to", "0.2.0", "/fake/catalogue"])
    assert rc != 0, "--to should no longer be accepted on upgrade"


def test_upgrade_yes_flag():
    """`--yes` is accepted and defaults to False."""
    parser = cli._build_parser()
    default = parser.parse_args(["upgrade", "--pack", "core", "/fake/catalogue"])
    assert default.yes is False
    with_yes = parser.parse_args(
        ["upgrade", "--pack", "core", "--yes", "/fake/catalogue"]
    )
    assert with_yes.yes is True


def test_upgrade_primitive_flags_mutually_exclusive():
    """Two per-primitive flags at once are rejected by the parser instead of
    silently upgrading only the first."""
    rc, err = _parse(
        ["upgrade", "--pack", "core", "--skill", "a", "--agent", "b",
         "/fake/catalogue"]
    )
    assert rc != 0, "two primitive flags should be mutually exclusive"
    assert "not allowed with argument" in err or "mutually exclusive" in err
