"""Regression: credentialed-skill entry-points must work under the
user-scope install layout.

The user-scope install drops each skill into a flat ``scripts/``
directory under ``~/.claude/skills/<skill>/`` with NO ``__init__.py``
and NO PYTHONPATH set. The SKILL.md docs tell users to invoke entry-
points as ``python scripts/setup.py <namespace>`` (or equivalent for
each credentialed CLI). Without a bootstrap that restores the package
context, the documented ``from .credentials_shim import ...`` line at
the top of each entry-point raises::

    ImportError: attempted relative import with no known parent package

before argparse ever runs. The fix is a ``__package__``-bootstrap block
at the top of every entry-point script (see
``docs/specs/credential-broker-contract/spec.md`` AC28). The bootstrap
is a no-op when ``__package__`` is already set (e.g. by the
``_load_cli_module`` test helper in
``test_example_credentialed_skill.py``).

This test verifies the bootstrap holds for every shipped entry-point
under the real user-scope layout — no test harness, no synthetic
parent package, no PYTHONPATH.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKS = REPO_ROOT / "packs"
SHIM_SOURCE = PACKS / "credential-brokers" / ".apm" / "shared-libs"


def _stage_user_scope_skill(
    tmp_path: pathlib.Path, source_scripts_dir: pathlib.Path,
) -> pathlib.Path:
    """Stage a skill's ``scripts/`` directory the way user-scope
    install would: byte-copy every ``.py`` sibling from the source
    skill plus the projected shim siblings from shared-libs, into a
    flat tmp scripts/ dir with NO ``__init__.py`` anywhere on the
    path. Returns the staged scripts/ dir."""
    staged = tmp_path / "scripts"
    staged.mkdir()
    for entry in source_scripts_dir.iterdir():
        if entry.is_file() and entry.suffix == ".py":
            shutil.copy(entry, staged / entry.name)
    # Shim siblings are projected into every consumer's scripts/ by
    # make build-self; under user-scope install the adapter projects
    # the same byte-identical copies. Re-project here from the
    # canonical source so the test does not depend on a prior
    # make build-self having run.
    for shim in SHIM_SOURCE.iterdir():
        if shim.is_file() and shim.suffix == ".py":
            target = staged / shim.name
            if not target.exists():
                shutil.copy(shim, target)
    # Verify the no-package-marker invariant — this is the shape that
    # breaks the relative-import idiom without a bootstrap.
    assert not (staged / "__init__.py").exists()
    assert not (tmp_path / "__init__.py").exists()
    return staged


def _clean_env() -> dict[str, str]:
    """A minimal subprocess env that does NOT leak the developer's
    PYTHONPATH (which can mask the bug by making the shim importable
    via an unrelated route)."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k in {"PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP"}
    }
    env.pop("PYTHONPATH", None)
    return env


def _invoke_help(scripts_dir: pathlib.Path, entry_name: str) -> subprocess.CompletedProcess:
    """Invoke ``python scripts/<entry>.py --help`` from the parent of
    scripts/ with a clean env. ``--help`` triggers every top-of-module
    import (where the bug lives) without exercising the script's
    actual logic."""
    return subprocess.run(
        [sys.executable, f"scripts/{entry_name}", "--help"],
        cwd=str(scripts_dir.parent),
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )


def _assert_no_relative_import_error(result: subprocess.CompletedProcess, entry: str) -> None:
    """Narrow assertion: the only failure shape this test owns is
    ``attempted relative import with no known parent package``.
    Third-party module imports (yaml, slugify, …) failing under a
    bare test interpreter are out of scope — those are runtime
    dependencies the entry-point legitimately needs, and they fail
    *after* the relative-import boundary the fix targets."""
    assert "attempted relative import with no known parent package" not in result.stderr, (
        f"{entry}: relative-import failure — bootstrap block missing or broken.\n"
        f"exit={result.returncode}\nstderr:\n{result.stderr}"
    )
    if result.returncode == 0:
        return
    # Out-of-scope: a missing third-party runtime dep. Anchor on the
    # ``No module named '<name>'`` shape and the explicit set of
    # credential-area module names so we don't accidentally accept a
    # ``ModuleNotFoundError: httpx._client`` (where the substring
    # ``_client`` would otherwise match) as out-of-scope.
    stderr = result.stderr
    credential_area_modules = (
        "'credentials_shim'",
        "'_keychain_macos'",
        "'_credman_windows'",
        "'_client'",
        "'_sso_keychain_macos'",
        "'_sso_credman_windows'",
    )
    bare_module_not_found = (
        "ModuleNotFoundError: No module named" in stderr
        and not any(mod in stderr for mod in credential_area_modules)
    )
    if bare_module_not_found:
        return  # Out-of-scope dep failure; bug-of-interest is absent.
    raise AssertionError(
        f"{entry}: unexpected non-zero exit from --help.\n"
        f"exit={result.returncode}\nstderr:\n{stderr}"
    )


# ─────────────────────────── per-entry-point ───────────────────────────

@pytest.mark.parametrize(
    "skill_relpath,entry_name",
    [
        ("credential-brokers/.apm/skills/credential-setup/scripts", "setup.py"),
        ("core/.apm/skills/example-credentialed-skill/scripts", "cli.py"),
        ("figma/.apm/skills/figma/scripts", "figma.py"),
        ("atlassian/.apm/skills/jira/scripts", "jira.py"),
        ("atlassian/.apm/skills/jira-align/scripts", "jira_align.py"),
        ("atlassian/.apm/skills/confluence-crawler/scripts", "crawl_space.py"),
        ("atlassian/.apm/skills/confluence-publisher/scripts", "publish_page.py"),
    ],
)
def test_entry_point_imports_resolve_under_user_scope_layout(
    tmp_path: pathlib.Path, skill_relpath: str, entry_name: str,
) -> None:
    """Each shipped credentialed-skill entry-point loads cleanly when
    invoked as ``python scripts/<entry>.py --help`` from a flat
    user-scope layout. This is the exact invocation the SKILL.md docs
    instruct adopters to use."""
    src = PACKS / skill_relpath
    if not (src / entry_name).is_file():
        pytest.skip(f"{src / entry_name} not present in this checkout")
    staged = _stage_user_scope_skill(tmp_path, src)
    result = _invoke_help(staged, entry_name)
    _assert_no_relative_import_error(result, f"{skill_relpath}/{entry_name}")


def test_sso_broker_tier2_backend_loads_under_user_scope_layout(
    tmp_path: pathlib.Path,
) -> None:
    """AC22b regression: the SSO broker's Tier-2 backend must load
    under the realistic post-fix `~/.agentbundle/bin/` layout, not
    silently degrade to None on macOS/Windows.

    The AC22b shim-companion projection puts `credentials_shim.py`
    next to `sso-broker.py` + `_sso_keychain_macos.py` +
    `_sso_credman_windows.py` in the bin/ target, so
    `_sso_*`'s `from .credentials_shim import Tier2HardFailError`
    resolves. Without the companion, the `_sso_*` import fails and
    `sso-broker.py`'s try/except cascade degrades `_tier2_backend`
    to `None` — exactly on the platforms the broker's Tier-2 path
    is supposed to exercise.

    Invocation shape: documented user-facing form
    `python bin/sso-broker.py show-tier2-backend` (positional verb).
    Per `feedback_test_real_invocation_not_synthesised_import` — no
    runpy.run_path, no importlib synthesis, no package-context
    forging. The `show-tier2-backend` verb prints `repr(_tier2_backend)`
    and exits 0; that's all the test asserts on.

    Platform-keyed assertion against the design contract:
    `_sso_keychain_macos` on darwin / `_sso_credman_windows` on win32
    / `None` on linux (no Tier-2 backend on Linux is by design per
    spec § Boundaries § Never do)."""
    src = PACKS / "credential-brokers" / ".apm" / "adapter-root-bins"
    shim_src = PACKS / "credential-brokers" / ".apm" / "shared-libs"
    if not (src / "sso-broker.py").is_file():
        pytest.skip("sso-broker.py not present")
    # Stage the realistic post-AC22b user-scope layout.
    staged_bin = tmp_path / "bin"
    staged_bin.mkdir()
    for entry in src.iterdir():
        if entry.is_file() and entry.suffix == ".py":
            shutil.copy(entry, staged_bin / entry.name)
    # AC22b companion: the build pipeline projects credentials_shim.py
    # next to sso-broker.py + the _sso_* siblings. Re-project here
    # from the canonical source so the test does not depend on a
    # prior `make build-self` having run.
    shutil.copy(
        shim_src / "credentials_shim.py",
        staged_bin / "credentials_shim.py",
    )
    assert (staged_bin / "credentials_shim.py").exists()
    assert not (staged_bin / "__init__.py").exists()
    # The shim's own platform backends MUST NOT be projected into
    # bin/ — sso-broker uses its own _sso_* backends; the shim's
    # _tier2_backend resolves to None when loaded from bin/ per
    # AC22c, which is correct behaviour.
    assert not (staged_bin / "_keychain_macos.py").exists()
    assert not (staged_bin / "_credman_windows.py").exists()

    result = subprocess.run(
        [sys.executable, "bin/sso-broker.py", "show-tier2-backend"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    _assert_no_relative_import_error(result, "sso-broker.py")
    assert result.returncode == 0, (
        f"show-tier2-backend exited {result.returncode}.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    stdout = result.stdout
    if sys.platform == "darwin":
        assert "_sso_keychain_macos" in stdout, (
            f"AC22b regression: Tier-2 backend silently degraded to None "
            f"on darwin under realistic user-scope layout. stdout: {stdout!r}"
        )
    elif sys.platform == "win32":
        assert "_sso_credman_windows" in stdout, (
            f"AC22b regression: Tier-2 backend silently degraded to None "
            f"on win32 under realistic user-scope layout. stdout: {stdout!r}"
        )
    else:
        # Linux / other: no Tier-2 backend by design.
        assert "None" in stdout, (
            f"sso-broker on {sys.platform!r}: expected `None` Tier-2 "
            f"backend (no Tier-2 on non-darwin / non-win32 per spec § "
            f"Boundaries); got {stdout!r}"
        )
