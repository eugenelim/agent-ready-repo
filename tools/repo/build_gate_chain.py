#!/usr/bin/env python3
"""Make-free, cross-platform self-host gate chains (repo-native).

`make build-self` / `make build-check` orchestrate the self-host gates; on
Windows there is no `make`, so contributors invoke this script instead:

    python tools/repo/build_gate_chain.py build-self
    python tools/repo/build_gate_chain.py build-check

**Why it lives in `tools/repo/`, not the shipped `agentbundle` package.** It
orchestrates *this repo's* gates: `build-check` spawns repo-native scripts —
`tools/catalogue/pre_pr_catalogue.py` (explicitly never projected to adopters)
and the projected `.claude/skills/.../*.py` linters — that do not exist in a
`pip install agentbundle` consumer's tree. The reusable engine (`catalogue
lint` / `build` / `verify` / `self-host`) is the public `agentbundle catalogue`
surface; this is the repo-specific wiring. Putting it here keeps the published
package's CLI surface unchanged (no release) and avoids baking repo-only paths
into the wheel.

The Windows-incompatible SAST leg (Semgrep) is intentionally NOT chained here
— it stays Makefile-appended.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# tools/repo/ → tools/ → repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Used to build a child's PYTHONPATH (`_agentbundle_env`), never inserted on this
# process's sys.path. Doing that at import time made a combined
# `pytest tools/ tests/` run order-dependent: two collected test modules import
# this one, `tools/` is walked before `tests/`, so the insert landed before any
# test ran and the first `import agentbundle` cached the worktree copy in
# sys.modules for the whole session. Tests that failed on their own passed in that
# combined run. (Not `make test`, which never puts the two trees in one process —
# Makefile:394 runs `tests/` alone, in its own invocation. There the exported
# PYTHONPATH on Makefile:11 is what resolves these packages.) pyproject.toml's
# [tool.pytest.ini_options] pythonpath is the declared way to put them on
# sys.path; tools/test_import_time_path_leaks.py fails if an import-time insert
# comes back.
_AGENTBUNDLE_PATH = str(REPO_ROOT / "packages" / "agentbundle")

# A chain step: a human label plus a zero-arg thunk returning an exit code.
Step = tuple[str, Callable[[], int]]


_CREDBROKER_PATH = str(REPO_ROOT / "packages" / "credbroker")


def _agentbundle_env() -> dict:
    """Env with packages/agentbundle on PYTHONPATH for subprocess agentbundle calls."""
    env = os.environ.copy()
    pp = env.get("PYTHONPATH", "")
    parts = [p for p in pp.split(os.pathsep) if p]
    if _AGENTBUNDLE_PATH not in parts:
        env["PYTHONPATH"] = os.pathsep.join([_AGENTBUNDLE_PATH] + parts)
    return env


def _source_packages_env() -> dict:
    """Env with BOTH source packages on PYTHONPATH.

    Both are importable from source — neither needs `pip install -e` — so a
    directory-scoped step can run a suite that imports them without the chain
    taking on provisioning. Appended after any caller PYTHONPATH so a real
    installed copy still wins.
    """
    env = _agentbundle_env()
    parts = [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
    if _CREDBROKER_PATH not in parts:
        env["PYTHONPATH"] = os.pathsep.join(parts + [_CREDBROKER_PATH])
    return env


def _run_chain(steps: list[Step]) -> int:
    """Run *steps* in order; stop at the first non-zero and return its code."""
    for label, step in steps:
        rc = int(step())
        if rc != 0:
            print(f"build chain: ✖ {label} failed (exit {rc})", file=sys.stderr)
            return rc
    return 0


def _handler_step(label: str, func: Callable[[argparse.Namespace], int], **ns_kwargs) -> Step:
    """Wrap an in-process handler call as a chain step."""
    def _thunk(func=func, ns=argparse.Namespace(**ns_kwargs)) -> int:  # noqa: B008
        return int(func(ns))

    return (label, _thunk)


def _script_step(label: str, *path_parts: str, args: tuple[str, ...] = ()) -> Step:
    """Wrap a repo-relative Python script and its arguments as a chain step."""
    script = Path(*path_parts)

    def _thunk(script=script, args=args) -> int:
        return subprocess.run(
            [sys.executable, str(script), *args], check=False
        ).returncode

    return (label, _thunk)


def _pytest_step(label: str, *path_parts: str) -> Step:
    """Wrap a repo-relative pytest module as a chain step."""
    test_path = Path(*path_parts)

    def _thunk(test_path=test_path) -> int:
        return subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-q"],
            check=False,
        ).returncode

    return (label, _thunk)


def _pytest_step_cwd(label: str, cwd: str, *targets: str, floor: int | None = None) -> Step:
    """Wrap a pytest run that must execute FROM a directory.

    Some suites are directory-scoped by construction: their `conftest.py` puts
    the skill's `scripts/` on `sys.path`, so running them from the repo root
    collects nothing useful. CI expresses that with `working-directory:`; the
    chain had no vocabulary for it, so those gates were CI-only and a local
    `make build-check` could not run them at all.

    Windows-clean, which is the whole reason this is a step kind rather than a
    shell string: `subprocess`'s own `cwd=` moves the child, so there is no
    `cd &&`, no shell, and no POSIX-only quoting. The argv stays a plain list.

    The child also gets the repo's source packages on `PYTHONPATH`. Moving the
    cwd out of the repo root is what makes this necessary: a suite that imports
    `credbroker` or `agentbundle` finds them by path rather than by install, so
    the step does not require `pip install -e` provisioning that a local
    `make build-check` has no reason to do. CI proved the need — without it the
    credential-setup suite exits 3 at import on a runner where credbroker is not
    installed.
    """
    directory = Path(cwd)

    def _thunk(directory=directory, targets=targets, floor=floor) -> int:
        workdir = str(REPO_ROOT / directory)
        env = _source_packages_env()
        argv = [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            "-q",
            "-p",
            "no:cacheprovider",
        ]
        if floor is not None:
            # The explicitly loaded plugin counts this execution's real items
            # and fails during collection before any test body runs.  Keeping
            # the floor on this argv avoids a second interpreter/collection and
            # preserves inherited stdout/stderr and native pytest failures.
            argv.extend(
                [
                    "-p",
                    "tools.pytest_collection_floor",
                    f"--minimum-collected={floor}",
                    f"--collection-floor-suite={directory.as_posix()}",
                ]
            )
        return subprocess.run(
            argv,
            cwd=workdir,
            check=False,
            env=env,
        ).returncode

    return (label, _thunk)


def _module_step(label: str, *cmd_args: str) -> Step:
    """Run ``python -m agentbundle <cmd_args>`` as a chain step.

    Propagates PYTHONPATH so packages/agentbundle is importable in the
    subprocess regardless of the caller's environment.
    """
    env = _agentbundle_env()

    def _thunk(env=env) -> int:
        return subprocess.run(
            [sys.executable, "-m", "agentbundle"] + list(cmd_args),
            check=False,
            env=env,
        ).returncode

    return (label, _thunk)


def build_self(args: argparse.Namespace) -> int:
    """`build-self` chain: agentbundle catalogue self-host --write (mirrors `make build-self`)."""
    op_args: list[str]
    if args.dry_run:
        op_args = ["--check"]
        label = "catalogue self-host --check"
    else:
        op_args = ["--write"] + (["--force"] if args.force else [])
        label = "catalogue self-host --write"

    steps: list[Step] = [
        _module_step(label, "catalogue", "self-host", "--root", ".", *op_args),
    ]
    return _run_chain(steps)


def build_check(args: argparse.Namespace) -> int:
    """`build-check` chain: every Windows-clean build and policy gate.

    The chain owns portable verification so direct make-free invocation has the
    same coverage as the Make target. It then materializes build output and runs
    the repo-specific gates. The nested pre-PR aggregator skips only its own
    portable verification because this chain has already completed it.

    The SAST leg is intentionally omitted (Semgrep has no Windows support and
    is conditional) — it stays Makefile-appended after this chain.
    """
    steps: list[Step] = [
        _module_step(
            "catalogue-verify",
            "catalogue", "verify", "--root", ".",
        ),
        _module_step(
            "catalogue-build",
            "catalogue", "build", "--root", ".", "--output", args.output_dir,
        ),
        _script_step(
            "pre-pr-catalogue",
            "tools", "catalogue", "pre_pr_catalogue.py",
            args=("--skip-verify",),
        ),
        _script_step(
            "check-contract-parity",
            "tools", "catalogue", "check_contract_parity.py",
        ),
        _pytest_step(
            "test-lint-spec-status",
            "packs", "core", "tests", "skills", "work-loop", "test_lint_spec_status.py",
        ),
        _script_step(
            "lint-spec-status",
            ".claude", "skills", "work-loop", "scripts", "lint-spec-status.py",
            args=("--all",),
        ),
        _pytest_step(
            "test-lint-brief-coverage",
            "packs",
            "core",
            "tests",
            "skills",
            "author-delivery-brief",
            "test_lint_brief_coverage.py",
        ),
        _script_step(
            "lint-brief-coverage",
            ".claude", "skills", "author-delivery-brief", "scripts", "lint-brief-coverage.py",
        ),
        _pytest_step(
            "test-lint-traceability",
            "packs", "core", "tests", "skills", "work-loop", "test_lint_traceability.py",
        ),
        _script_step(
            "lint-traceability",
            ".claude", "skills", "work-loop", "scripts", "lint-traceability.py",
        ),
        _script_step(
            "test-workspace-status",
            "tools", "test_workspace_status.py",
        ),
        _script_step(
            "test-workspace-status-cli",
            "tools", "test_workspace_status_cli.py",
        ),
        _pytest_step(
            "test-verify-host-checks",
            "tools", "catalogue", "tests", "test_verify_host_checks.py",
        ),
        _script_step(
            "verify-host-checks",
            "tools", "catalogue", "verify_host_checks.py",
        ),
        # Repo-own lints that build-check.yml ran and no local chain did, so a
        # green `make ci` said nothing about them (spec/local-gate-ci-parity).
        # Both default to `--root .` (the guard also to `--base origin/main`),
        # so they invoke zero-arg like every other step here. They belong in
        # this chain rather than the projected tools/hooks/pre-pr.py, which
        # deliberately runs no repo linters — see each linter's docstring.
        _script_step(
            "test-lint-catalogue-curation-guard",
            "tools", "test-lint-catalogue-curation-guard.py",
        ),
        _script_step(
            "lint-catalogue-curation-guard",
            "tools", "lint-catalogue-curation-guard.py",
        ),
        _script_step(
            "test-lint-experience-agnostic",
            "tools", "test-lint-experience-agnostic.py",
        ),
        _script_step(
            "lint-experience-agnostic",
            "tools", "lint-experience-agnostic.py",
        ),
        # tools/pack_scope.py is the single stdlib mirror of
        # commands/validate.py:_allowed_scopes that the three route gates and
        # the publish script share. This differential test is what stops it
        # drifting from the resolver it mirrors.
        _script_step(
            "test-pack-scope",
            "tools", "test-pack-scope.py",
        ),
        # Claude-plugin route membership. Lives here, not in pytest: this is
        # the only required, path-unfiltered gate, and `make build-check` runs
        # no pytest. Widening a pack's allowed-scopes publishes its code to a
        # public marketplace — this is the tripwire for that.
        _script_step(
            "test-lint-plugin-membership",
            "tools", "test-lint-plugin-membership.py",
        ),
        _script_step(
            "lint-plugin-membership",
            "tools", "lint-plugin-membership.py",
        ),
        # The roster tripwire. Distinct from the membership lint above, which
        # derives both sides from the same predicate and is therefore green
        # when the predicate itself is wrong. This one enumerates literally.
        _script_step(
            "test-lint-plugin-roster",
            "tools", "test-lint-plugin-roster.py",
        ),
        _script_step(
            "lint-plugin-roster",
            "tools", "lint-plugin-roster.py",
        ),
        # The publish script's three refusals are the only runtime check
        # between `git push` and a public marketplace — the publish job has no
        # `needs:` on this one.
        _script_step(
            "test-publish-claude-plugins",
            "tools", "test-publish-claude-plugins.py",
        ),
        _script_step(
            "test-lint-claude-plugin-publish-control",
            "tools", "test-lint-claude-plugin-publish-control.py",
        ),
        _script_step(
            "lint-claude-plugin-publish-control",
            "tools", "lint-claude-plugin-publish-control.py",
        ),
        # The capture script that produces the evidence the linter above checks
        # is operator-run, so nothing else exercises its `--repo` guard. That
        # guard is the only constraint on a value interpolated into the API
        # paths, and urllib does not normalise the selector it is handed — so
        # it is worth a gate even though the script itself never runs in CI.
        # Placed after the self-test/linter pair above, not between them.
        _script_step(
            "test-capture-publish-control-evidence",
            "tools", "test-capture-publish-control-evidence.py",
        ),
        # Per-site `(path, pattern, expected)` — the sites do not share a
        # pattern, so one repo-wide grep would pass green on most of them.
        _script_step(
            "test-lint-plugin-route-docs",
            "tools", "test-lint-plugin-route-docs.py",
        ),
        _script_step(
            "lint-plugin-route-docs",
            "tools", "lint-plugin-route-docs.py",
        ),
        # The site's `pluginInstallable` field is hand-copied from pack.toml —
        # `tools/build-site.py` feeds docs-site/, not web/ — so this is what
        # keeps the copy honest. The built-output half lives in pages.yml; see
        # docs/specs/claude-plugin-route-scope AC8 for why it is not here.
        _script_step(
            "test-lint-site-scope-parity",
            "tools", "test-lint-site-scope-parity.py",
        ),
        _script_step(
            "lint-site-scope-parity",
            "tools", "lint-site-scope-parity.py",
        ),
        # The built-output gate itself needs a real site build, so it runs in
        # pages.yml. Its *self-test* needs nothing, so it runs here and blocks:
        # a broken assertion in a non-blocking gate is the quietest failure
        # this spec can produce.
        _script_step(
            "test-check-site-plugin-offers",
            "tools", "test-check-site-plugin-offers.py",
        ),
        # Drift backstop only — the pack-description quality bar is
        # guides/_shared/reference/catalogue-authoring-standards.md § 2.
        _script_step(
            "test-lint-pack-descriptions",
            "tools", "test-lint-pack-descriptions.py",
        ),
        _script_step(
            "lint-pack-descriptions",
            "tools", "lint-pack-descriptions.py",
        ),
        # Published marketplace manifests carry these values verbatim, so
        # protect maintainers from an identifying address reaching that route.
        _script_step(
            "test-lint-pack-maintainer-emails",
            "tools", "test-lint-pack-maintainer-emails.py",
        ),
        _script_step(
            "lint-pack-maintainer-emails",
            "tools", "lint-pack-maintainer-emails.py",
        ),
        # npm install scripts execute dependency code during installation, so
        # keep this supply-chain permission check in the unfiltered policy
        # chain. Its mutation self-test runs first: a broken detector would
        # otherwise report green on the clean repository it is meant to guard.
        _script_step(
            "test-lint-npm-allow-scripts",
            "tools", "test-lint-npm-allow-scripts.py",
        ),
        _script_step(
            "lint-npm-allow-scripts",
            "tools", "lint-npm-allow-scripts.py",
        ),
        # The bandit suppression-comment form (ADR-0084). bandit.yaml's header
        # is the canonical statement of the rule and of why this runs here
        # rather than in `make sast`. Correction (ADR-0086 / AC14): it DOES need a
        # scanner — lint-nosec-form resolves bandit's test ids and, when bandit is
        # absent, sets a caveat and exits 0, dropping its unknown-id check rather
        # than failing. #986 provisions bandit unconditionally in `gate-main`, at the
        # pinned version and with a registry-resolution probe, precisely so this leg
        # is not inert. The older claim that it "needs no scanner" was the falsehood
        # that fail-open depended on.
        #
        # The form is not spelled out in this comment on purpose: bandit
        # tokenises this file too, so a comment quoting the literal directive IS
        # one to its parser. Writing it out here blanket-suppressed this very
        # line until lint-nosec-form caught it.
        _script_step(
            "test-lint-nosec-form",
            "tools", "test-lint-nosec-form.py",
        ),
        _script_step(
            "lint-nosec-form",
            "tools", "lint-nosec-form.py",
        ),
        # The Semgrep twin of the bandit form lint above, and separate from it
        # because the two suppression grammars differ: Semgrep matches raw line
        # text rather than parsed comments, and a second comment marker does not
        # terminate its rule-id list the way bandit's does. It checks suppression
        # *form* only — a stdlib-only gate cannot reach Semgrep's rule registry
        # to confirm a named rule exists.
        _script_step(
            "test-lint-nosemgrep-form",
            "tools", "test-lint-nosemgrep-form.py",
        ),
        _script_step(
            "lint-nosemgrep-form",
            "tools", "lint-nosemgrep-form.py",
        ),
        # The standing check that the repo-lint steps above do not become stale
        # again: lint-ci-parity fails when build-check.yml gains a gate with no
        # local counterpart and no declared exemption.
        _script_step(
            "test-lint-ci-parity",
            "tools", "test-lint-ci-parity.py",
        ),
        _script_step(
            "test-build-check-windows-workflow",
            "tools", "test-build-check-windows-workflow.py",
        ),
        # spec/ci-gate-parallelization AC13: the posture test for build-check.yml's
        # own job graph. Runs its mutation matrix first — an assertion whose mutation
        # never executes is an unverified assertion, and this file is the local-parity
        # path for the copy that runs inside the aggregator job.
        _script_step(
            "test-build-check-workflow",
            "tools", "test-build-check-workflow.py",
        ),
        # ci-security.yml's security-posture assertion lives in the unfiltered
        # chain because no other local gate reads that workflow.
        _script_step(
            "test-ci-security-workflow",
            "tools", "test-ci-security-workflow.py",
        ),
        # ADR-0017's advisory CodeQL signal is security-load-bearing even though
        # branch protection does not yet require it. The posture test proves the
        # query suite, the read-only default floor against the analyzer's
        # elevated grant, an exhaustive analysis-config `paths-ignore` list, the
        # presence of the analyze step, the trigger surface (no
        # `pull_request_target`, no `paths:` allowlist, `main` branches, the
        # weekly re-scan), an elevated-grant backstop over every job but
        # `analyze`, and the literal AC12 concurrency group and cancellation
        # expressions, with `analyze` pinned as the sole `security-events`
        # writer. It does not pin ADDITIONAL grants on the analyze job itself.
        _script_step(
            "test-codeql-workflow",
            "tools", "test-codeql-workflow.py",
        ),
        # AC10: no CI path executes `build-check`'s `$(MAKE) sast` branch after
        # ADR-0086, so nothing else would notice it being deleted or made
        # unreachable. Skips cleanly where `make` is absent.
        _script_step(
            "assert-sast-chain-reachable",
            "tools", "assert-sast-chain-reachable.py",
        ),
        _script_step(
            "lint-ci-parity",
            "tools", "lint-ci-parity.py",
        ),
        # tools/test-all.py is hand-run, so its manifest rotted unnoticed for
        # weeks. This suite's live case asserts every TESTS entry resolves to a
        # file — the cheap half of the umbrella, gated, without running the
        # multi-minute suite itself.
        _script_step(
            "test-test-all",
            "tools", "test-test-all.py",
        ),
        # Promoted from an on-demand tool to a gate. It was held back pending
        # calibration evidence — two clean passes on origin/main with no false
        # positive, to confirm exit-0 stability before a red build could be
        # blamed on the check itself. Recorded: 2026-08-01, 2026-08-15,
        # 2026-08-16 (three, one more than the bar asked for).
        _script_step(
            "check-contract-drift",
            "tools", "repo", "check_contract_drift.py",
        ),
        # lint-performance-p0 (ADR-0087). These go in the UNFILTERED chain, not
        # `docs.yml`, because that workflow is `paths`-filtered to an explicit
        # file allowlist with no `tools/**` or `packages/**` entry — a PR adding
        # a per-path `check-ignore` to an unlisted file would run neither gate.
        _script_step(
            "git-ignore resolver self-test",
            "tools", "test-lint-git-ignore.py",
        ),
        _script_step(
            "no-direct-check-ignore",
            "tools", "lint-no-direct-check-ignore.py",
        ),
        _script_step(
            "no-direct-check-ignore self-test",
            "tools", "test-lint-no-direct-check-ignore.py",
        ),
        # The behaviour contract for the boundary lint. It reads its capture
        # subject from a pinned commit, so the job running it needs full history
        # — see the `fetch-depth: 0` note in .github/workflows/docs.yml.
        _script_step(
            "boundary-lint golden baseline",
            "tools", "test-lint-boundary-golden.py",
        ),
        _script_step(
            "boundary-lint structural properties",
            "tools", "test-lint-boundary-structural.py",
        ),
        _script_step(
            "agents-md gitignore probes",
            "tools", "test-lint-agents-md-gitignore-probes.py",
        ),
        # The three structural boundary gates for ARCHITECTURE.md section 3.
        # These go in the UNFILTERED chain for the same reason the check-ignore
        # gates above do: `docs.yml` is `paths`-filtered to an explicit file
        # allowlist, so a PR that violates one of these boundaries in a file the
        # allowlist does not name would run neither the lint nor its self-test.
        # Each lint is paired with its self-test, because a lint whose own
        # detection is broken reports "passed" on a violating tree.
        _script_step(
            "adapter-layer-boundary",
            "tools", "lint-adapter-layer-boundary.py",
        ),
        _script_step(
            "adapter-layer-boundary self-test",
            "tools", "test-lint-adapter-layer-boundary.py",
        ),
        _script_step(
            "pack-dependency-declaration",
            "tools", "lint-pack-dependency-declaration.py",
        ),
        _script_step(
            "pack-dependency-declaration self-test",
            "tools", "test-lint-pack-dependency-declaration.py",
        ),
        _script_step(
            "generated-path-ownership",
            "tools", "lint-generated-path-ownership.py",
        ),
        _script_step(
            "generated-path-ownership self-test",
            "tools", "test-lint-generated-path-ownership.py",
        ),
        # Directory-scoped: each suite's conftest puts its skill's scripts/ on
        # sys.path, so both collect nothing from the repo root. Pure stdlib —
        # no install, no network — so they belong in the local chain.
        # The floors are not decoration: these invocations name a directory
        # rather than files, so a suite that fails to land would silently
        # reduce the count and still exit 0.
        _pytest_step_cwd(
            "pytest catalogue-curation assimilate-primitive",
            "packs/catalogue-curation/tests/skills/assimilate-primitive",
            floor=30,
        ),
        _pytest_step_cwd(
            "pytest catalogue-curation assimilate-repo",
            "packs/catalogue-curation/tests/skills/assimilate-repo",
            floor=7,
        ),
    ]
    return _run_chain(steps)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_gate_chain",
        description="Make-free self-host gate chains (mirrors the Makefile targets).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bs = sub.add_parser("build-self", help="catalogue self-host (write or check).")
    bs.add_argument("--dry-run", action="store_true", help="Check mode (read-only).")
    bs.add_argument("--force", action="store_true", help="Force overwrite existing projections.")
    bs.add_argument(
        "--no-symlink", action="store_true",
        help="Ignored (handled by agentbundle internally).",
    )
    bs.add_argument("--packs-dir", default="packs", help="Ignored (resolved via --root .).")
    bs.set_defaults(func=build_self)

    bc = sub.add_parser(
        "build-check",
        help="catalogue verify, build, pre-pr-catalogue, spec-status, "
             "brief-coverage, traceability, workspace-status tests, "
             "catalogue-curation guard, experience-agnosticism lint, CI parity "
             "(no SAST).",
    )
    bc.add_argument("--packs-dir", default="packs", help="Ignored (resolved via --root .).")
    bc.add_argument(
        "--output-dir",
        default="dist",
        help="Artifact dir for the catalogue build leg (default: dist/).",
    )
    bc.set_defaults(func=build_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Resolve every repo-relative path (packs/, tools/, .claude/) against the
    # repo root regardless of where the script is invoked from.
    os.chdir(REPO_ROOT)
    args = _build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
