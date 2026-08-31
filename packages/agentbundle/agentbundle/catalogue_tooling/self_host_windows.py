"""Windows-portability compat suite for ``agentbundle catalogue self-host --check --windows``.

Runs the path-sensitive and encoding-sensitive tests that the Windows CI job
exercises for portability verification. Each step is a subprocess call using
``sys.executable`` so the correct interpreter is always used regardless of
how the process was launched.

Steps run in sequence; the first non-zero exit code is returned immediately,
matching the stop-on-failure behaviour of the CI workflow they replace.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# pytest's JUnit report opens with a single `<testsuite ...>` element carrying
# these counts as attributes. Read with a narrow pattern rather than an XML
# parser: the file is one we generated seconds earlier in a temporary
# directory, and pulling in an XML parser for two integers would add a parsing
# surface this module has no other use for.
#
# Each attribute is matched independently because pytest emits `skipped` before
# `tests`; a single pattern that fixed their order silently matched nothing and
# reported every run as having executed zero tests.
_TESTSUITE_ELEMENT = re.compile(r"<testsuite\b[^>]*>")


def _attribute(element: str, name: str) -> int:
    """Read one integer attribute from a `<testsuite>` element."""

    matched = re.search(rf'\b{name}="(\d+)"', element)
    return int(matched.group(1)) if matched else 0


# The steps judged by executed-test count rather than return code alone.
# Lifted to a module constant so a test can assert the set: with it inline, a
# deleted label silently reverted the floor and the whole file stayed green.
EXECUTED_FLOOR_LABELS = frozenset(
    {"direct source acquisition", "direct admission", "direct install"}
)


def _step(label: str, cmd: list[str], cwd: Path) -> int:
    print(f"\n=== {label} ===", flush=True)
    if not cwd.exists():
        print(f"SKIP — working directory not found: {cwd}", flush=True)
        return 1
    return subprocess.run(cmd, cwd=cwd).returncode


def _executed_count(report: Path) -> int:
    """Tests that actually ran, from a pytest JUnit report.

    Skipped tests are subtracted deliberately. A pytest run where every test
    skipped — a missing optional dependency, a platform guard, a collection
    error swallowed into a skip — exits 0, so a step judged by return code alone
    reports a pass for a suite that never executed anything.
    """

    if not report.exists():
        return 0
    element = _TESTSUITE_ELEMENT.search(report.read_text(encoding="utf-8"))
    if element is None:
        return 0
    found = element.group(0)
    return _attribute(found, "tests") - _attribute(found, "skipped")


def _pytest_step_with_executed_floor(
    label: str, targets: list[str], cwd: Path, python: str
) -> int:
    """Run a pytest target and require it to have executed at least one test.

    Used for the modules whose Windows arms exist precisely to prove they run
    on Windows: reporting a pass for an all-skipped run would make the Windows
    signal indistinguishable from no signal at all.
    """

    print(f"\n=== {label} ===", flush=True)
    if not cwd.exists():
        print(f"SKIP — working directory not found: {cwd}", flush=True)
        return 1
    with tempfile.TemporaryDirectory(prefix="agentbundle-windows-junit-") as scratch:
        report = Path(scratch) / "report.xml"
        completed = subprocess.run(
            [python, "-m", "pytest", *targets, f"--junitxml={report}"], cwd=cwd
        )
        if completed.returncode != 0:
            return completed.returncode
        # One invocation produces one report, so the count is an aggregate over
        # every target. The previous loop recomputed that same aggregate once
        # per target and named a different target each time, claiming per-target
        # attribution it never had; it was correct only because each step
        # happens to pass a single target.
        executed = _executed_count(report)
        if executed == 0:
            print(
                f"FAIL — {', '.join(targets)} executed no tests on this "
                f"platform; an all-skipped run exits 0 and would otherwise "
                f"report a pass",
                flush=True,
            )
            return 1
        print(f"executed {executed} test(s)", flush=True)
    return 0


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
        # Direct-install suites. Their Windows arms assert documented
        # `unknown`/no-write outcomes for FIFO and symlink cases rather than
        # skipping, so they must actually execute here — hence the executed-count
        # floor below rather than a bare return-code check. The performance suite
        # stays off this list deliberately.
        (
            "direct source acquisition",
            ["tests/unit/test_direct_source_acquisition.py"],
            pkg,
        ),
        (
            "direct admission",
            ["tests/unit/test_direct_admission.py"],
            pkg,
        ),
        (
            "direct install",
            ["tests/integration/test_direct_install.py"],
            pkg,
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
        # Re-renders every declared knowledge bundle and compares the result
        # against the committed tree, so a Windows-only encoding, path, or
        # ordering difference fails here rather than reaching main. The
        # adopter-facing hook above does not carry this gate — it is a
        # catalogue-maintainer concern — so without this stage no Windows runner
        # touches the compiler at all.
        (
            "okf compiler checks",
            [py, str(root / "tools" / "check-okf-managed-packs.py"), "--root", str(root)],
            root,
        ),
    ]

    executed_floor_labels = EXECUTED_FLOOR_LABELS
    for label, cmd, cwd in steps:
        if label in executed_floor_labels:
            rc = _pytest_step_with_executed_floor(label, cmd, cwd, py)
        else:
            rc = _step(label, cmd, cwd)
        if rc != 0:
            return rc

    return 0
