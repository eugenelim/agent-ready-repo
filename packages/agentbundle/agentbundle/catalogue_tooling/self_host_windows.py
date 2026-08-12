"""Windows-portability compat suite for ``agentbundle catalogue self-host --check --windows``.

Runs the path-sensitive and encoding-sensitive tests that the Windows CI job
exercises for portability verification. Each step is a subprocess call using
``sys.executable`` so the correct interpreter is always used regardless of
how the process was launched.

Steps run in sequence; the first non-zero exit code is returned immediately,
matching the stop-on-failure behaviour of the CI workflow they replace.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _step(label: str, cmd: list[str], cwd: Path) -> int:
    print(f"\n=== {label} ===", flush=True)
    if not cwd.exists():
        print(f"SKIP — working directory not found: {cwd}", flush=True)
        return 1
    return subprocess.run(cmd, cwd=cwd).returncode


def run_windows_compat(root: Path) -> int:
    """Run the full Windows compat suite rooted at *root*.

    Returns 0 when every step passes; the exit code of the first failing
    step otherwise.
    """
    py = sys.executable
    pkg = root / "packages" / "agentbundle"

    steps: list[tuple[str, list[str], Path]] = [
        # Populate dist/ so build-check drift gates have their input.
        (
            "catalogue build",
            [py, "-m", "agentbundle", "catalogue", "build", "--root", str(root)],
            root,
        ),
        # Self-host drift check (writer-template byte-identity, plugin.json shape,
        # vendored _emit_basic_string parity). Calls the standard --check path,
        # not --windows, so there is no recursion.
        (
            "self-host --check",
            [py, "-m", "agentbundle", "catalogue", "self-host", "--check", "--root", str(root)],
            root,
        ),
        # Path-sensitive agentbundle pytest suite
        (
            "converters install/uninstall",
            [py, "-m", "pytest", "tests/integration/test_install_converters_user_scope.py"],
            pkg,
        ),
        (
            "shared-libs projection retirement (credbroker T9)",
            [py, "-m", "pytest", "tests/build_pipeline/test_shared_libs_projection.py"],
            pkg,
        ),
        (
            "self-host recipe config (externalize-self-host-config)",
            [py, "-m", "pytest", "tests/build_pipeline/test_self_host_recipe_config.py"],
            pkg,
        ),
        (
            "self-host fixture guard (windows-build-self-entry)",
            [py, "-m", "pytest", "tests/build_pipeline/test_self_host_fixture_guard.py"],
            pkg,
        ),
        (
            "user-libs vendored floor (credbroker-user-scope T3)",
            [py, "-m", "pytest", "tests/build_pipeline/test_user_libs_projection.py"],
            pkg,
        ),
        (
            "user-scope floor delivery (credbroker-user-scope T4)",
            [py, "-m", "pytest", "tests/integration/test_credential_brokers_pack_install.py"],
            pkg,
        ),
        (
            "hook parity-net suite (windows-hooks-phase3)",
            [py, "-m", "pytest", str(root / "packs" / "core" / "tests" / "hooks")],
            root,
        ),
        # Atlassian SSO suites (asyncio + SSL-context wiring is platform-sensitive).
        # Pack tests live outside the runtime payload.
        #
        # Probe the dependencies first. Both trios `importorskip("credbroker")` at
        # module scope, and `_step` below judges a step by its return code alone —
        # so without this, a machine missing credbroker skips both suites entirely
        # and the step reports pass.
        (
            "atlassian SSO dependency probe",
            [py, "-c", "import credbroker, httpx"],
            root,
        ),
        (
            "jira SSO suites (atlassian-sso-cookie)",
            [
                py, "-m", "pytest",
                "test_sso_config.py", "test_sso_client.py", "test_setup_sso.py",
                "test_check_sso_login.py",
            ],
            root / "packs" / "atlassian" / "tests" / "skills" / "jira",
        ),
        (
            "confluence-crawler SSO suites (atlassian-sso-cookie)",
            [py, "-m", "pytest", "test_sso_config.py", "test_sso_client.py", "test_setup_sso.py"],
            root / "packs" / "atlassian" / "tests" / "skills" / "confluence-crawler",
        ),
        # Experience agnosticism lint (proves `python` portability, not `python3`)
        (
            "experience lint self-test (design-craft-pack)",
            [py, str(root / "tools" / "test-lint-experience-agnostic.py")],
            root,
        ),
        (
            "experience lint (design-craft-pack)",
            [py, str(root / "tools" / "lint-experience-agnostic.py")],
            root,
        ),
        # Pre-pr aggregator (end-to-end adopter flow on Windows)
        (
            "pre-pr aggregator",
            [py, str(root / "tools" / "hooks" / "pre-pr.py")],
            root,
        ),
    ]

    for label, cmd, cwd in steps:
        rc = _step(label, cmd, cwd)
        if rc != 0:
            return rc

    return 0
