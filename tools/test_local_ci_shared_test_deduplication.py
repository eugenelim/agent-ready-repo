"""Construction contracts for shared tests composed by local ``make ci``.

The five files in ``SHARED_TESTS`` remain complete standalone gates.  These
tests pin the semantic collection that permits one composed CI invocation to
let build-check own those executions while the reduced test route excludes
only their exact paths.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Protocol
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent

SHARED_TESTS = (
    "packs/core/tests/skills/work-loop/test_lint_spec_status.py",
    "packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py",
    "packs/core/tests/skills/work-loop/test_lint_traceability.py",
    "tools/test_workspace_status.py",
    "tools/test_workspace_status_cli.py",
)

CORE_COLLECTIONS = {
    # Re-pinned by RFC-0096 Wave 4 (AC2d). Reconciled on every rebase by the
    # same check: this branch's node set must match main's exactly except for
    # one rename, `test_invariant_ii_transition_ok_when_deferred` ->
    # `..._fails_when_deferred`, because a `(deferred: <slug>)` marker no
    # longer makes a newly shipped AC valid. The count therefore tracks main
    # unchanged while the digest moves; if a future rebase shows any other
    # delta, disposition it before re-pinning rather than taking either side.
    # Re-pinned 2026-08-28: 73 -> 78. `2d435502e` ("a timed-out base read must
    # not read as 'spec is new'") added five timeout-degradation tests —
    # test_default_base_ref_primary_probe_timeout_degrades_to_no_base,
    # ..._fallback_probe_timeout_degrades_to_no_base,
    # test_base_ref_probe_timeout_degrades_to_unresolvable,
    # test_base_spec_show_timeout_skips_diff_invariants_for_unchanged_specs, and
    # test_repo_root_probe_timeout_degrades_to_script_relative_root — and this
    # contract was not re-pinned with them, so the check has been red on main
    # since that commit. Dispositioned rather than taken from either side, as the
    # note above requires: all five are genuine additions covering git-probe
    # timeout degradation, nothing was removed or renamed, and the other two
    # entries below still reproduce. Adding a test here is expected; leaving this
    # number behind is what makes the contract stop meaning anything.
    SHARED_TESTS[0]: (
        78,
        "dd567702b9fe8bdbcff7c8da65b501c64ccaba1fb1cf009fd438befd67db51fc",
    ),
    SHARED_TESTS[1]: (
        16,
        "9eb21215317b77e1b24e1433a4219c87aa09ee9220462850475b0431fe1b8bcd",
    ),
    SHARED_TESTS[2]: (
        45,
        "ea3e0a39355fe8ae06f3bf3cba73bacdc6793a9c64f7254c28647a46f695056b",
    ),
}

EXPECTED_BUILD_OWNERS = (
    (SHARED_TESTS[0], "test-lint-spec-status", "_pytest_step"),
    (SHARED_TESTS[1], "test-lint-brief-coverage", "_pytest_step"),
    (SHARED_TESTS[2], "test-lint-traceability", "_pytest_step"),
    (SHARED_TESTS[3], "test-workspace-status", "_script_step"),
    (SHARED_TESTS[4], "test-workspace-status-cli", "_script_step"),
)

COMPOSED_EXCLUSIONS = {
    SHARED_TESTS[0],
    SHARED_TESTS[1],
    SHARED_TESTS[2],
}

EXPECTED_COMPOSED_IGNORES = {
    "packs/core/tests/skills/work-loop/": {
        SHARED_TESTS[0],
        SHARED_TESTS[2],
    },
    "packs/core/tests/skills/author-delivery-brief/": {SHARED_TESTS[1]},
}

COLLECTION_FLOORS = {
    "packs/desk-research/tests/skills/desk-research/": 9,
    "packs/desk-research/tests/skills/desk-research-project-start/": 7,
}

PROVEN_COMPATIBLE_FILES = (
    "tools/test_import_time_path_leaks.py",
    "tools/test_managed_child.py",
    "tools/test_coordination_lease.py",
    "tools/test_branch_added_paths.py",
    "tools/test_bootstrap.py",
)
PROVEN_COMPATIBLE_NODE_HASH = (
    "efa4ae209fbba434d71b9c090415ed0c77d6f14674094f410a992def9082bdc3"
)

FIRST_TOOL_BATCH = (
    "tools/test_build_gate_chain.py",
    "tools/test_journey_editorial_decisions.py",
    "tools/test_catalogue_tooling_rewire.py",
    "tools/test_catalogue_tooling_docs.py",
    "tools/test_validate_guides.py",
    "tools/test_check_guide_index.py",
    "tools/test_catalogue_navigation.py",
    "tools/test_documentation_entry_links.py",
    "tools/test_build_site_link_rewrites.py",
    "tools/test_check_rendered_site_links.py",
    "tools/test_build_site_routing.py",
    "tools/test_check_docs_contrast.py",
    "tools/test_build_site_inventory.py",
    "tools/test_build_site_projection.py",
    "tools/test_build_site_sidebar.py",
    "tools/test_browser_gate_subset.py",
    "tools/test_local_ci_shared_test_deduplication.py",
)

RETAINED_TOOL_SINGLETONS = (
    "tools/test_worktree_hygiene.py",
    "tools/test_worktree_lease_interlock.py",
    "tools/test_worktree_import_resolution.py",
    "tools/test_editable_install_guard.py",
    "tools/test_run_slot.py",
    "tools/test_with_lease_cli.py",
    "tools/test_playwright_evidence_lifecycle.py",
    "tools/test_worktree_lifecycle_hooks.py",
    "tools/test_frontend_runtime.py",
    "tools/test_check_artifact_contents.py",
)

FINAL_TOOL_BATCH = (
    "tools/test_lint_agents_md_diataxis_block.py",
    "tools/test_lint_agents_md_legacy_block.py",
    "tools/test_lint_agents_md_risk_block.py",
    "tools/test_lint_agents_md_frontmatter_scope.py",
    "tools/test_catalogue_curation_guard.py",
    "tools/test_contract_parity.py",
    "tools/test_marketplace_envelope_parity.py",
    "tools/test_guide_authoring_standard.py",
    "tools/test_release_check.py",
    "tools/test_check_release_impact.py",
    "tools/test_scaffold_projection.py",
    "tools/test_conformance_portability.py",
    "tools/test_lint_guides_no_repo_only_refs.py",
    "tools/test_okf_pre_pr.py",
    # Added 2026-08-28 with the pack-test compatibility classes (ADR-0101).
    # Nothing globs `tools/test_*.py`, so a module absent from this batch is
    # never executed. Only the declaration/derivation suite is here: its sibling
    # `tools/test_pack_test_class_characterization.py` spawns 30 collect-only
    # pytest processes for ~36s and runs in build-check.yml instead, with a ~2s
    # two-check `lint-pack-test-boundary.py` invocation carrying the local
    # signal. That invocation is a separate recipe line, not a member of this
    # batch, which is why it does not appear here.
    "tools/test_pack_test_compatibility.py",
)

WORKSPACE_STATUS_PAIR = SHARED_TESTS[3:]
EXPECTED_ROOT_TOOL_PATHS = frozenset(
    ("tests/",)
    + FIRST_TOOL_BATCH
    + WORKSPACE_STATUS_PAIR
    + RETAINED_TOOL_SINGLETONS
    + PROVEN_COMPATIBLE_FILES
    + FINAL_TOOL_BATCH
)

_STATE_GUARD_RUNNER = r"""
import asyncio
import importlib.util
import json
import locale
import logging
import multiprocessing
import os
import pathlib
import signal
import sys
import threading
import time
import warnings
from collections import Counter

import pytest

ROOT = pathlib.Path(os.environ["STATE_GUARD_REPO_ROOT"]).resolve()
DESIGNATED = pathlib.Path(os.environ["STATE_GUARD_FS_PREFIX"])
ALLOW_PATH = Counter(json.loads(os.environ.get("STATE_GUARD_ALLOW_PATH", "{}")))
WATCHED = ("agentbundle", "credbroker", "tools.repo.build_gate_chain")


def _resolution(name):
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return "<unresolvable>"
    return str(getattr(spec, "origin", None)) if spec else "<missing>"


def _path_counts():
    counts = Counter()
    for entry in sys.path:
        if not entry:
            continue
        try:
            entry = str(pathlib.Path(entry).resolve())
        except OSError:
            pass
        counts[entry] += 1
    return counts


def _signals():
    found = {}
    for member in signal.Signals:
        if member.name in {"SIGKILL", "SIGSTOP"}:
            continue
        try:
            handler = signal.getsignal(member)
        except (OSError, ValueError):
            continue
        found[member.name] = handler if isinstance(handler, int) else id(handler)
    return found


def _logging_handlers():
    def participant_handlers(logger):
        # Pytest adds its two capture handlers before each test setup and
        # removes them after the final teardown.  Those runner-owned handlers
        # make the first-setup and post-final-teardown snapshots intentionally
        # asymmetric; participant handlers must still compare exactly.
        return tuple(
            (type(handler).__name__, handler.level, id(handler))
            for handler in logger.handlers
            if not (
                type(handler).__module__ == "_pytest.logging"
                and type(handler).__qualname__ == "LogCaptureHandler"
            )
        )

    loggers = [("root", logging.getLogger())]
    loggers.extend(
        (name, logger)
        for name, logger in logging.Logger.manager.loggerDict.items()
        if isinstance(logger, logging.Logger)
    )
    return sorted(
        (name, participant_handlers(logger))
        for name, logger in loggers
    )


def _snapshot():
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
    policy = asyncio.get_event_loop_policy()
    return {
        "cwd": os.getcwd(),
        "env": env,
        "path": _path_counts(),
        "meta_path": tuple((type(f).__module__, type(f).__qualname__, id(f)) for f in sys.meta_path),
        "resolution": {name: _resolution(name) for name in WATCHED},
        "logging": _logging_handlers(),
        "warnings": tuple(map(repr, warnings.filters)),
        "signals": _signals(),
        "locale": locale.setlocale(locale.LC_ALL, None),
        "timezone": (os.environ.get("TZ"), time.tzname, time.timezone),
        "asyncio": (type(policy).__module__, type(policy).__qualname__, id(policy)),
        "threads": sorted(
            (thread.name, thread.ident, thread.daemon)
            for thread in threading.enumerate()
            if thread is not threading.current_thread() and thread.is_alive()
        ),
        "children": sorted(child.pid for child in multiprocessing.active_children()),
        "filesystem": sorted(str(path) for path in DESIGNATED.parent.glob(DESIGNATED.name + "*")),
    }


def _changed(before, after, *, allow_path=False):
    changed = []
    for name in before:
        if name == "path" and allow_path:
            delta = Counter(after[name])
            delta.subtract(before[name])
            delta = Counter({key: value for key, value in delta.items() if value})
            if delta != ALLOW_PATH:
                changed.append("path=" + repr(dict(delta)))
        elif name == "logging" and before[name] != after[name]:
            changed.append(
                "logging=" + repr({"before": before[name], "after": after[name]})
            )
        elif before[name] != after[name]:
            changed.append(name)
    return changed


class StateGuard:
    def __init__(self):
        self.at_start = None
        self.execution = None
        self.current_file = None

    def pytest_sessionstart(self, session):
        self.at_start = _snapshot()

    def pytest_collection_finish(self, session):
        after = _snapshot()
        changed = _changed(self.at_start, after, allow_path=True)
        if changed:
            pytest.fail("state guard collection delta: " + ", ".join(changed))

    def pytest_runtest_setup(self, item):
        current_file = str(item.path)
        snapshot = _snapshot()
        if self.execution is None:
            self.execution = snapshot
        elif current_file != self.current_file:
            changed = _changed(self.execution, snapshot)
            if changed:
                pytest.fail("state guard file-boundary delta: " + ", ".join(changed))
        self.current_file = current_file

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(self, item, nextitem):
        yield
        # Pytest restores warnings.filters around the whole runtest protocol,
        # outside pytest_runtest_teardown.  Mutate after that restoration so
        # the synthetic control proves a surviving warning-filter leak is
        # visible at the following file boundary.
        if os.environ.pop("STATE_GUARD_LATE_WARNING", None):
            warnings.simplefilter("always", RuntimeWarning)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item, nextitem):
        yield
        if nextitem is None and self.execution is not None:
            changed = _changed(self.execution, _snapshot())
            if changed:
                pytest.fail("state guard final delta: " + ", ".join(changed))


code = pytest.main(
    ["-q", "-p", "no:cacheprovider", *json.loads(os.environ["STATE_GUARD_ARGS"])],
    plugins=[StateGuard()],
)
raise SystemExit(int(code))
"""

CONSTRUCTION_TEST_PATH = "tools/test_local_ci_shared_test_deduplication.py"
# Approved pre-change ``test-unleased`` dry-run plan after Python-path and
# line-continuation normalization.  The composed digest removes only the exact
# workspace-status pair command from that same baseline; the construction test
# path is the sole intentional addition and is checked separately below.
# Re-pinned 2026-08-26 (RFC-0096 Wave 4), then again after rebasing onto the
# collection-floor fold, then again on 2026-08-28 for the
# `agent-skill-engineering` pack. Its four suites join both routes:
# `tests/pack/`, `tests/integration/`, and the two `tests/skills/` directories.
# Verified by diffing both normalized dry-run plans against `origin/main`'s
# Makefile — standalone 67->71 and composed 66->70, the delta being exactly
# those four added lines with no other line moved, reordered, or dropped.
#
# Re-pinned again on 2026-08-28 for the core-guidance routing slice, which adds
# the canonical `packs/core/tests/skills/author-delivery-brief/` and
# `packs/core/tests/skills/intake-intent/` suites and moves the shared
# coverage-test exclusion from the `receive-brief` compatibility alias
# directory to that canonical owner: standalone 71->73, composed 70->72.
#
# Re-pinned once more on the same day for the pack-test compatibility classes
# (ADR-0101, spec/pack-test-compatibility-classes), MERGED on top of the routing
# slice above. Eighteen pack lines fold into five grouped invocations, so both
# plans shrink by 13 from the routing-slice baseline and then gain one line for
# the two-check `lint-pack-test-boundary.py` invocation that now carries the
# identity derivation locally: standalone 73->61, composed 72->60. The net -12
# is deliberate arithmetic, not a miscount — the grouping removes 13 pytest
# launches and the identity gate adds one non-pytest command.
# Both deltas are additive and independent — the routing slice
# adds two core suites that no class claims, and the classes fold suites in five
# other packs — so the merged figure is the arithmetic of the two, not a
# reconciliation of competing edits. Verified three ways: the counts move
# together, `_parse_runner_files` reports 32 pack-scoped invocations against 45
# on this branch's base and 47 after the routing slice, and the collected node-ID
# set is unchanged with raw equal to unique on both sides. The two floor-bearing
# desk-research lines are untouched, and both new `tools/test_pack_test_*.py`
# modules join the final batch's single continued command.
APPROVED_STANDALONE_PLAN_DIGEST = (
    "1e097b6dcf6b1264ac50222cba6d905748a69ddd391384293f613c3df3aaf4f3"
)
APPROVED_COMPOSED_PLAN_DIGEST = (
    "847607344749b41c8efeb978a400f77c11d8c075012533967c321b4bb99e733e"
)

# Approved bytes of every surface this change must leave alone, taken from the
# merge base this branch rebases onto.  A digest here moves only when the owning
# change moves it: ``sast-unleased`` was re-pinned when `main` retired semgrep's
# four transitive-dep ``--ignore-vuln`` suppressions, verified as byte-identical
# to `origin/main`'s recipe rather than recomputed from this worktree alone.
# ``SEMGREP_EXCLUDE`` and ``sast-unleased`` were re-pinned again by the change
# that owns them here — the two timing-out harness files joined the exclusion
# list, the scan moved behind ``tools/run-semgrep-gate.py`` with ``--strict``,
# and ``tools/check-semgrep-version.py`` joined the recipe's tool checks.
# Recomputed from this worktree because this branch authored the edit, and
# checked the only way that is safe: the other six surfaces were recomputed at
# the same time and are unchanged, so the move is confined to the two blocks the
# change deliberately edits.
MAKE_BASELINE_DIGESTS = {
    "build-check-unleased": "f9df737082cf0a4f1ee554ca3eac710da77623a447c8ef62a3678c8a7d8ad4ca",
    "sast": "6e3046497a9f9ed10e559865ecd9e330d88e37417ccfc35af20bc610616ef0b4",
    "sast-unleased": "cb4177f36bd64773812db97f879ad7e49e197370ecb9934ecb8a133318d4b1e5",
    "SAST_DIRS": "7cb835cf14ea0c97bf450810aea5b0194dbf289b03659ad9308c6efde146ba8c",
    "SAST_CONFIG": "df0eeff32c8f18c84f917e7ea579039c8cc3ab54f4e7adb4b1bc6d09b857961c",
    "SEMGREP_EXCLUDE": "f838b4f5433821278a8004ae90eba5d024b579055ccc9b23b8e659ee6d5c8115",
    "gate_verdict": "aa9d2cc83cc7d9e59fe411c5788f5abf6c5810772407170fff21d28107564d79",
    "gate_verdict_calls": "116c367fbb376618b499ffba4f4d79138a5ca32f7948631e678519e9a16565be",
}

EXPECTED_SKIP_XFAIL_CALLS = {
    SHARED_TESTS[0]: {
        "pytest.skip(f'{name}: symlink creation unavailable ({exc})')": 1,
        # Guards on the unreadable-spec case: POSIX mode bits do not stop a
        # read for root, and do not exist on Windows. The test asserts a spec
        # the linter cannot read is warned about rather than reported clean.
        "pytest.skip('root can read a mode-000 file')": 1,
        "pytest.skip('POSIX mode bits')": 1,
    },
    SHARED_TESTS[1]: {},
    SHARED_TESTS[2]: {
        "pytest.skip(f'{name}: symlink creation unavailable ({exc})')": 1,
    },
    SHARED_TESTS[3]: {
        (
            "unittest.SkipTest(f'{label}: skill absent, "
            "{_SKIP_ANCHOR_ENV} set')"
        ): 1,
    },
    SHARED_TESTS[4]: {
        "self.skipTest('CLI not yet created')": 16,
        "self.skipTest('Engine not yet moved')": 3,
        "self.skipTest(f'symlinks unavailable: {exc}')": 1,
        (
            "unittest.skipIf(sys.platform == 'win32', "
            "'symlink test not portable on Windows')"
        ): 1,
        (
            "unittest.skipIf(sys.platform == 'win32', "
            "'symlink needs elevated privs on Windows')"
        ): 1,
        (
            "unittest.skipIf(sys.platform == 'win32', "
            "'symlink needs elevated privileges')"
        ): 1,
    },
}

EXPECTED_WINDOWS_SKIPS = {
    f"{SHARED_TESTS[4]}::SymlinkConfinementTests::test_symlink_escape_not_read",
    f"{SHARED_TESTS[4]}::RepairPlanTests::test_repair_plan_plan_file_is_symlink",
    (
        f"{SHARED_TESTS[4]}::WorkIntakeMigrationCliStubTests::"
        "test_ac27_migration_workspace_symlink_escape_uses_result_envelope"
    ),
}

APPROVED_ENVIRONMENT_SKIP_SOURCES = {
    SHARED_TESTS[0]: {
        "symlink_or_skip": re.compile(
            r"^.+: symlink creation unavailable \(.+\)$"
        ),
    },
    SHARED_TESTS[2]: {
        "symlink_or_skip": re.compile(
            r"^.+: symlink creation unavailable \(.+\)$"
        ),
    },
}


def _runtime_skip_errors(
    observed: list[tuple[str, str, str]],
    *,
    platform: str,
) -> list[str]:
    """Reject runtime skips outside the reviewed shared-owner policy."""
    errors: list[str] = []
    for relative_path, node, reason in observed:
        source_pattern = APPROVED_ENVIRONMENT_SKIP_SOURCES.get(
            relative_path, {}
        ).get(node)
        if source_pattern is not None and source_pattern.fullmatch(reason):
            continue
        pytest_nodeid = f"{relative_path}::{node.replace('.', '::')}"
        if platform == "win32" and pytest_nodeid in EXPECTED_WINDOWS_SKIPS:
            continue
        errors.append(
            f"unexpected runtime skip: {relative_path}::{node}: {reason}"
        )
    return errors


def _load_module(relative_path: str, name: str) -> ModuleType:
    """Load one repository test module without requiring it to be a package."""
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parametrize_ids(function: ast.FunctionDef) -> tuple[str, ...] | None:
    """Return explicit pytest parameter IDs for the simple shared core tests."""
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        dotted = ast.unparse(decorator.func)
        if dotted != "pytest.mark.parametrize":
            continue
        ids_node = next(
            (keyword.value for keyword in decorator.keywords if keyword.arg == "ids"),
            None,
        )
        if ids_node is None:
            raise AssertionError(f"{function.name} must declare explicit parameter IDs")
        ids = ast.literal_eval(ids_node)
        if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
            raise AssertionError(f"{function.name} has unsupported pytest IDs")
        return tuple(ids)
    return None


def _static_core_node_ids(relative_path: str) -> tuple[str, ...]:
    """Derive the checked-in pytest node contract without launching pytest."""
    tree = ast.parse((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    node_ids: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        if isinstance(node, ast.AsyncFunctionDef):
            raise AssertionError(f"unsupported async shared test: {node.name}")
        parameter_ids = _parametrize_ids(node)
        if parameter_ids is None:
            node_ids.append(f"{relative_path}::{node.name}")
        else:
            node_ids.extend(
                f"{relative_path}::{node.name}[{parameter_id}]"
                for parameter_id in parameter_ids
            )
    return tuple(node_ids)


def test_tools_changes_do_not_add_a_pytest_dependency() -> None:
    """Scoped tools guidance keeps new and modified test adapters stdlib-only."""
    for relative_path in (SHARED_TESTS[3], __file__):
        path = Path(relative_path)
        if path.is_absolute():
            path = path.relative_to(REPO_ROOT)
        tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        assert "pytest" not in imports, path


def _iter_unittest_cases(suite: unittest.TestSuite) -> Iterator[unittest.TestCase]:
    """Flatten a unittest suite while retaining its direct-runner membership."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_unittest_cases(item)
        else:
            assert isinstance(item, unittest.TestCase)
            yield item


def _target_rule(makefile: str, target: str) -> tuple[list[str], str]:
    """Return exact prerequisites and tab-indented recipe for one Make target."""
    lines = makefile.splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^{re.escape(target)}\s*:\s*(.*)$", line)
        if match is None:
            continue
        recipe: list[str] = []
        for candidate in lines[index + 1 :]:
            if candidate.startswith("\t"):
                recipe.append(candidate)
                continue
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                continue
            break
        return match.group(1).split(), "\n".join(recipe)
    return [], ""


def _make_macro(makefile: str, name: str) -> str:
    """Extract one complete Make ``define`` body, including its sentinels."""
    match = re.search(
        rf"(?ms)^(?:override )?define {re.escape(name)}\n.*?^endef$",
        makefile,
    )
    return match.group(0) if match else ""


def _floor_make_errors(makefile: str) -> list[str]:
    """Return one-pass floor or inherited-stream drift in the real Make macro."""
    macro = _make_macro(makefile, "run-test-suite")
    errors: list[str] = []
    for suite, floor in COLLECTION_FLOORS.items():
        lines = [line.strip() for line in macro.splitlines() if suite in line]
        if len(lines) != 1:
            errors.append(f"{suite}: expected one real floor command")
            continue
        line = lines[0]
        required = {
            "$(PYTHON) -m pytest",
            suite,
            "-q",
            "-p tools.pytest_collection_floor",
            f"--minimum-collected={floor}",
            f"--collection-floor-suite={suite}",
        }
        if not all(token in line for token in required):
            errors.append(f"{suite}: one-pass floor argv drift")
        if "--collect-only" in line:
            errors.append(f"{suite}: collect-only probe remains")
        if any(token in line for token in ("|", ">", "<")):
            errors.append(f"{suite}: stdout/stderr no longer inherited")
    return errors


def _mutate_floor_make_command(makefile: str, suite: str, suffix: str) -> str:
    """Append one shell stream mutation to a real floor command."""
    lines = makefile.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if suite in line and "$(PYTHON) -m pytest" in line
    ]
    if len(matches) != 1:
        raise AssertionError(f"{suite}: expected one mutable pytest command")
    lines[matches[0]] = f"{lines[matches[0]]} {suffix}"
    return "\n".join(lines) + ("\n" if makefile.endswith("\n") else "")


def _skip_xfail_calls(relative_path: str) -> dict[str, int]:
    """Return the complete static contract for ways a shared case can skip."""
    tree = ast.parse((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    calls: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        terminal = ast.unparse(node.func).rsplit(".", 1)[-1]
        if terminal not in {
            "SkipTest",
            "skip",
            "skipIf",
            "skipTest",
            "skipUnless",
            "xfail",
        }:
            continue
        rendered = ast.unparse(node)
        calls[rendered] = calls.get(rendered, 0) + 1
    return calls


def _live_pytest_contract(*targets: str) -> dict[str, dict[str, object]]:
    """Collect live pytest skip/xfail metadata in a residue-free subprocess."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "tools.test_local_ci_shared_test_deduplication",
            *targets,
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    prefix = "SHARED-COLLECTION-CONTRACT="
    payloads = [
        line.removeprefix(prefix)
        for line in result.stdout.splitlines()
        if line.startswith(prefix)
    ]
    assert len(payloads) == 1, result.stdout + result.stderr
    value = json.loads(payloads[0])
    assert isinstance(value, dict)
    return value


def _filtered_contract(
    contract: dict[str, dict[str, object]], relative_path: str
) -> dict[str, dict[str, object]]:
    """Select one shared file from a directory-level live collection."""
    prefix = f"{relative_path}::"
    return {
        nodeid: metadata
        for nodeid, metadata in contract.items()
        if nodeid.startswith(prefix)
    }


class _PytestMarker(Protocol):
    """Structural type for the marker fields used by the collection hook."""

    name: str


class _PytestItem(Protocol):
    """Structural type for the collected-item fields used by the hook."""

    nodeid: str
    obj: object

    def iter_markers(self) -> Iterator[_PytestMarker]:
        """Yield the item's effective markers."""


class _PytestSession(Protocol):
    """Structural type for pytest's collection-finished hook argument."""

    items: list[_PytestItem]


def pytest_collection_finish(session: _PytestSession) -> None:
    """Emit live collection metadata when this stdlib module is a pytest plugin."""
    contract: dict[str, dict[str, object]] = {}
    for item in session.items:
        markers = sorted(
            marker.name
            for marker in item.iter_markers()
            if marker.name in {"skip", "skipif", "xfail"}
        )
        contract[item.nodeid] = {
            "markers": markers,
            "unittest_skip": bool(
                getattr(item.obj, "__unittest_skip__", False)
            ),
            "unittest_skip_reason": str(
                getattr(item.obj, "__unittest_skip_why__", "")
            ),
        }
    print(f"SHARED-COLLECTION-CONTRACT={json.dumps(contract, sort_keys=True)}")


def _build_owned_shared_tests(chain_source: str) -> tuple[tuple[str, str, str], ...]:
    """Derive shared path ownership from the real ``build_check`` AST."""
    tree = ast.parse(chain_source)
    build_check = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_check"
    )
    owners: list[tuple[str, str, str]] = []
    calls = sorted(
        (
            node
            for node in ast.walk(build_check)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"_pytest_step", "_script_step"}
        ),
        key=lambda node: node.lineno,
    )
    for call in calls:
        literal_args = [
            arg.value
            for arg in call.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        ]
        if len(literal_args) < 2:
            continue
        label, *parts = literal_args
        path = "/".join(parts)
        if path in SHARED_TESTS:
            owners.append((path, label, call.func.id))
    return tuple(owners)


def _recipe_source(makefile: str, target: str) -> str:
    """Extract exact command-bearing target bytes for an approved baseline."""
    lines = makefile.splitlines(keepends=True)
    start = next(
        index
        for index, line in enumerate(lines)
        if re.match(rf"^{re.escape(target)}[ \t]*:", line)
    )
    end = start + 1
    while end < len(lines) and lines[end].startswith("\t"):
        end += 1
    return "".join(lines[start:end])


def _variable_source(makefile: str, name: str) -> str:
    """Extract one single- or backslash-continued Make variable declaration."""
    lines = makefile.splitlines(keepends=True)
    start = next(
        index
        for index, line in enumerate(lines)
        if re.match(rf"^{re.escape(name)}[ \t]*:?=", line)
    )
    end = start + 1
    while lines[end - 1].rstrip("\r\n").endswith("\\"):
        end += 1
    return "".join(lines[start:end])


def _approved_make_surfaces(makefile: str) -> dict[str, str]:
    """Return every security/verdict surface that this change must not alter."""
    macro_start = makefile.index("define gate_verdict\n")
    macro_end = makefile.index("endef\n", macro_start) + len("endef\n")
    call_sites = "".join(
        line
        for line in makefile.splitlines(keepends=True)
        if "$(call gate_verdict," in line
    )
    return {
        "build-check-unleased": _recipe_source(makefile, "build-check-unleased"),
        "sast": _recipe_source(makefile, "sast"),
        "sast-unleased": _recipe_source(makefile, "sast-unleased"),
        "SAST_DIRS": _variable_source(makefile, "SAST_DIRS"),
        "SAST_CONFIG": _variable_source(makefile, "SAST_CONFIG"),
        "SEMGREP_EXCLUDE": _variable_source(makefile, "SEMGREP_EXCLUDE"),
        "gate_verdict": makefile[macro_start:macro_end],
        "gate_verdict_calls": call_sites,
    }


def _composition_errors(makefile: str, chain_source: str) -> list[str]:
    """Return fail-closed drift errors for the composed shared-test contract."""
    errors: list[str] = []
    owners = _build_owned_shared_tests(chain_source)
    if owners != EXPECTED_BUILD_OWNERS:
        errors.append("build ownership drift")

    ci_deps, _ci_recipe = _target_rule(makefile, "ci")
    if ci_deps != ["build-check", "lint-ruff", "lint-mypy", "test-after-build-check"]:
        errors.append("ci graph drift")

    composed_deps, composed_recipe = _target_rule(makefile, "test-after-build-check")
    if composed_deps != ["build-check"]:
        errors.append("composed owner dependency missing")
    if "with-lease" not in composed_recipe or "test-after-build-check-unleased" not in composed_recipe:
        errors.append("composed lease wrapper drift")

    unleased_deps, unleased_recipe = _target_rule(
        makefile, "test-after-build-check-unleased"
    )
    if unleased_deps != ["lint-editable-install"]:
        errors.append("composed unleased dependency drift")
    exclusions = set(re.findall(r"--ignore=([^\s,)]+)", unleased_recipe))
    if exclusions != COMPOSED_EXCLUSIONS:
        errors.append("composed exclusion drift")
    if any(path in unleased_recipe for path in SHARED_TESTS[3:]):
        errors.append("workspace pytest command was not omitted")

    standalone_deps, standalone_recipe = _target_rule(makefile, "test-unleased")
    if standalone_deps != ["lint-editable-install"]:
        errors.append("standalone dependency drift")
    if "--ignore=" in standalone_recipe:
        errors.append("standalone test became reduced")
    if not all(path in standalone_recipe for path in SHARED_TESTS[3:]):
        errors.append("standalone workspace coverage missing")

    macro = _make_macro(makefile, "run-test-suite")
    if not all(
        directory in macro
        for directory in (
            "packs/core/tests/skills/work-loop/",
            "packs/core/tests/skills/author-delivery-brief/",
            "packs/core/tests/skills/receive-brief/",
        )
    ):
        errors.append("standalone core coverage missing")

    phony_match = re.search(r"(?m)^\.PHONY:\s*(.*)$", makefile)
    phony = set(phony_match.group(1).split()) if phony_match else set()
    if not {"test-after-build-check", "test-after-build-check-unleased"} <= phony:
        errors.append("composed targets are not phony")
    return errors


def test_core_pytest_semantic_node_contracts_are_exact() -> None:
    """The three directory-collected core files retain their reviewed nodes."""
    for relative_path, (expected_count, expected_digest) in CORE_COLLECTIONS.items():
        node_ids = _static_core_node_ids(relative_path)
        digest = hashlib.sha256(("\n".join(node_ids) + "\n").encode()).hexdigest()
        assert len(node_ids) == expected_count, relative_path
        assert digest == expected_digest, relative_path


def test_shared_skip_xfail_contracts_are_exact_and_routes_match_live() -> None:
    """Unexpected static or live skip/xfail drift cannot retain a green union."""
    for relative_path, expected in EXPECTED_SKIP_XFAIL_CALLS.items():
        assert _skip_xfail_calls(relative_path) == expected, relative_path

    work_loop = _live_pytest_contract("packs/core/tests/skills/work-loop/")
    delivery_brief = _live_pytest_contract(
        "packs/core/tests/skills/author-delivery-brief/"
    )
    for relative_path, directory_contract in (
        (SHARED_TESTS[0], work_loop),
        (SHARED_TESTS[1], delivery_brief),
        (SHARED_TESTS[2], work_loop),
    ):
        file_contract = _live_pytest_contract(relative_path)
        assert file_contract == _filtered_contract(directory_contract, relative_path)
        assert not any(metadata["markers"] for metadata in file_contract.values())
        assert not any(metadata["unittest_skip"] for metadata in file_contract.values())

    workspace_contract = _live_pytest_contract(SHARED_TESTS[3], SHARED_TESTS[4])
    workspace_nodes = _filtered_contract(workspace_contract, SHARED_TESTS[3])
    workspace_module = _load_module(
        SHARED_TESTS[3], "_shared_workspace_live_collection_contract"
    )
    workspace_class = vars(workspace_module)["TestWorkspaceStatusCases"]
    direct_workspace_nodes = {
        f"{SHARED_TESTS[3]}::TestWorkspaceStatusCases::{method_name}"
        for method_name in unittest.defaultTestLoader.getTestCaseNames(
            workspace_class
        )
    }
    assert len(workspace_nodes) == len(direct_workspace_nodes) == 86
    assert set(workspace_nodes) == direct_workspace_nodes
    assert not any(
        metadata["markers"]
        for metadata in workspace_nodes.values()
    )

    cli_contract = _filtered_contract(workspace_contract, SHARED_TESTS[4])
    live_skips = {
        nodeid
        for nodeid, metadata in cli_contract.items()
        if metadata["unittest_skip"]
    }
    cli_module = _load_module(SHARED_TESTS[4], "_shared_cli_skip_contract")
    assert cli_module._CLI.is_file()
    assert cli_module._ENGINE.is_file()
    direct_suite = unittest.defaultTestLoader.loadTestsFromModule(cli_module)
    direct_cli_nodes: set[str] = set()
    direct_skip_reasons: dict[str, str] = {}
    for case in _iter_unittest_cases(direct_suite):
        method_name = case._testMethodName
        method = getattr(case, method_name)
        nodeid = f"{SHARED_TESTS[4]}::{type(case).__name__}::{method_name}"
        direct_cli_nodes.add(nodeid)
        if not getattr(method, "__unittest_skip__", False):
            continue
        direct_skip_reasons[nodeid] = str(
            getattr(method, "__unittest_skip_why__", "")
        )
    assert len(cli_contract) == len(direct_cli_nodes) == 158
    assert set(cli_contract) == direct_cli_nodes
    expected_live_skips = EXPECTED_WINDOWS_SKIPS if sys.platform == "win32" else set()
    assert live_skips == expected_live_skips
    assert set(direct_skip_reasons) == live_skips
    assert all(
        cli_contract[nodeid]["unittest_skip_reason"] == reason
        for nodeid, reason in direct_skip_reasons.items()
    )
    assert not any(metadata["markers"] for metadata in cli_contract.values())


def test_workspace_status_direct_and_pytest_share_one_case_registry() -> None:
    """Direct and pytest entrypoints must consume the same 86 semantic cases."""
    module = _load_module(SHARED_TESTS[3], "_shared_workspace_status_contract")
    cases = module.CASES
    assert len(cases) == 86
    labels = [label for label, _case in cases]
    functions = [case for _label, case in cases]
    assert len(set(labels)) == len(labels)
    assert len(set(functions)) == len(functions)

    registry_class = vars(module)["TestWorkspaceStatusCases"]
    method_names = unittest.defaultTestLoader.getTestCaseNames(registry_class)
    assert len(method_names) == len(cases)
    for method_name, (_label, case) in zip(method_names, cases, strict=True):
        method = getattr(registry_class, method_name)
        assert method._workspace_status_case is case
    assert "for label, fn in CASES" in inspect.getsource(module.main)

    tree = ast.parse((REPO_ROOT / SHARED_TESTS[3]).read_text(encoding="utf-8"))
    top_level_tests = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert top_level_tests == set()


def test_workspace_status_runtime_skip_is_a_failure_for_both_adapters() -> None:
    """An undeclared environment skip cannot make either owner route green."""
    module = _load_module(SHARED_TESTS[3], "_shared_workspace_skip_contract")
    old_anchor = module._WORK_LOOP_MD
    old_env = os.environ.get(module._SKIP_ANCHOR_ENV)
    module._WORK_LOOP_MD = REPO_ROOT / "missing-work-loop-contract-anchor.md"
    os.environ[module._SKIP_ANCHOR_ENV] = "1"
    try:
        try:
            module._run_case(module.case_work_loop_contract_anchor)
        except AssertionError as exc:
            assert "unexpected skip" in str(exc)
        else:
            raise AssertionError("pytest adapter accepted an unexpected runtime skip")

        old_cases = module.CASES
        module.CASES = (
            ("forced unexpected skip", module.case_work_loop_contract_anchor),
        )
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                assert module.main() != 0
            assert "unexpected skip" in output.getvalue()
        finally:
            module.CASES = old_cases
    finally:
        module._WORK_LOOP_MD = old_anchor
        if old_env is None:
            os.environ.pop(module._SKIP_ANCHOR_ENV, None)
        else:
            os.environ[module._SKIP_ANCHOR_ENV] = old_env


def test_runtime_skip_policy_covers_all_five_owner_routes() -> None:
    """Every shared owner admits only its explicitly reviewed runtime skips."""
    observed: list[tuple[str, str, str]] = []
    old_ci = os.environ.pop("CI", None)
    try:
        for relative_path, module_name in (
            (SHARED_TESTS[0], "_shared_spec_status_runtime_skip"),
            (SHARED_TESTS[2], "_shared_traceability_runtime_skip"),
        ):
            module = _load_module(relative_path, module_name)

            class BrokenSymlink:
                def symlink_to(self, *_args: object, **_kwargs: object) -> None:
                    raise OSError("forced construction probe")

            try:
                module.symlink_or_skip(
                    "construction-probe", BrokenSymlink(), "unused-target"
                )
            except BaseException as exc:
                assert type(exc).__name__ == "Skipped"
                observed.append((relative_path, "symlink_or_skip", str(exc)))
            else:
                raise AssertionError(f"{relative_path} did not exercise its skip path")
    finally:
        if old_ci is not None:
            os.environ["CI"] = old_ci

    assert _runtime_skip_errors(observed, platform=sys.platform) == []
    for relative_path in SHARED_TESTS:
        unexpected = [*observed, (relative_path, "unexpected-node", "forced skip")]
        assert _runtime_skip_errors(unexpected, platform=sys.platform) == [
            f"unexpected runtime skip: {relative_path}::unexpected-node: forced skip"
        ]

    cli_module = _load_module(SHARED_TESTS[4], "_shared_cli_runtime_skip")
    old_cli = cli_module._CLI
    cli_module._CLI = REPO_ROOT / "missing-workspace-status-cli.py"
    try:
        case = cli_module.CLIContractTests("test_cli_success")
        try:
            case.test_cli_success()
        except unittest.SkipTest as exc:
            cli_skip = (SHARED_TESTS[4], "CLIContractTests.test_cli_success", str(exc))
        else:
            raise AssertionError("CLI missing-path mutation did not skip")
    finally:
        cli_module._CLI = old_cli
    assert _runtime_skip_errors([cli_skip], platform=sys.platform) == [
        (
            f"unexpected runtime skip: {SHARED_TESTS[4]}::"
            "CLIContractTests.test_cli_success: CLI not yet created"
        )
    ]

    with tempfile.NamedTemporaryFile(prefix="shared-symlink-target-") as target_handle:
        target = Path(target_handle.name)
        link = target.with_name(f"{target.name}-link")
        try:
            try:
                link.symlink_to(target)
            except OSError as exc:
                observed.append(
                    (
                        SHARED_TESTS[4],
                        (
                            "WorkIntakeMigrationCliStubTests."
                            "test_ac7_status_refuses_linked_workspace_before_"
                            "projecting_legacy_bytes"
                        ),
                        f"symlinks unavailable: {exc}",
                    )
                )
            assert _runtime_skip_errors(observed, platform=sys.platform) == []
        finally:
            link.unlink(missing_ok=True)

    migration_case = cli_module.WorkIntakeMigrationCliStubTests(
        "test_ac7_status_refuses_linked_workspace_before_projecting_legacy_bytes"
    )

    class FakeTemporaryDirectory:
        def __enter__(self) -> str:
            return "/construction-skip-probe"

        def __exit__(self, *_args: object) -> None:
            return None

    with (
        mock.patch.object(
            cli_module.tempfile,
            "TemporaryDirectory",
            return_value=FakeTemporaryDirectory(),
        ),
        mock.patch.object(cli_module.Path, "write_text", return_value=0),
        mock.patch.object(
            cli_module.Path,
            "symlink_to",
            side_effect=OSError("forced symlink failure"),
        ),
    ):
        try:
            migration_case.test_ac7_status_refuses_linked_workspace_before_projecting_legacy_bytes()
        except unittest.SkipTest as exc:
            symlink_skip = (
                SHARED_TESTS[4],
                (
                    "WorkIntakeMigrationCliStubTests."
                    "test_ac7_status_refuses_linked_workspace_before_"
                    "projecting_legacy_bytes"
                ),
                str(exc),
            )
        else:
            raise AssertionError("CLI symlink mutation did not exercise its skip")
    assert _runtime_skip_errors([symlink_skip], platform=sys.platform) == [
        (
            f"unexpected runtime skip: {SHARED_TESTS[4]}::"
            "WorkIntakeMigrationCliStubTests."
            "test_ac7_status_refuses_linked_workspace_before_projecting_legacy_bytes: "
            "symlinks unavailable: forced symlink failure"
        )
    ]


def test_workspace_status_cli_unittest_and_pytest_method_contracts_match() -> None:
    """The CLI file exposes exactly one TestCase method set to both runners."""
    module = _load_module(SHARED_TESTS[4], "_shared_workspace_status_cli_contract")
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    direct_ids = {
        ".".join(case.id().split(".")[-2:])
        for case in _iter_unittest_cases(suite)
    }

    test_case_classes = [
        value
        for value in vars(module).values()
        if inspect.isclass(value)
        and value.__module__ == module.__name__
        and issubclass(value, unittest.TestCase)
    ]
    pytest_unittest_ids = {
        f"{test_case.__name__}.{method}"
        for test_case in test_case_classes
        for method in unittest.defaultTestLoader.getTestCaseNames(test_case)
    }

    assert len(direct_ids) == 158
    assert direct_ids == pytest_unittest_ids
    assert not hasattr(module, "load_tests")

    tree = ast.parse((REPO_ROOT / SHARED_TESTS[4]).read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        for node in tree.body
    )


def test_build_check_owns_each_shared_path_once_with_exact_runner_types() -> None:
    """The make-free Windows chain remains the sole shared-test owner."""
    chain = (REPO_ROOT / "tools/repo/build_gate_chain.py").read_text(encoding="utf-8")
    assert _build_owned_shared_tests(chain) == EXPECTED_BUILD_OWNERS
    assert all((REPO_ROOT / path).is_file() for path in SHARED_TESTS)


def test_real_ci_graph_owns_each_shared_test_exactly_once() -> None:
    """Standalone remains full while composed CI excludes exact build owners."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    chain = (REPO_ROOT / "tools/repo/build_gate_chain.py").read_text(encoding="utf-8")
    assert _composition_errors(makefile, chain) == []


def test_real_make_floors_are_one_pass_and_keep_inherited_streams() -> None:
    """Both desk floors live on their one real pytest command without a pipe."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert _floor_make_errors(makefile) == []


def test_real_make_root_tool_groups_match_the_approved_profiles() -> None:
    """The approved root/tool roster is explicit once in each applicable route."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert _root_tool_topology_errors(makefile) == []


def test_root_tool_topology_mutations_fail_closed() -> None:
    """Removal, duplication, broad discovery, and stale ownership all redden."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    grouped_member = f"\t{PROVEN_COMPATIBLE_FILES[1]} \\\n"
    assert grouped_member in makefile

    removed = makefile.replace(grouped_member, "", 1)
    assert "standalone root/tool membership drift" in _root_tool_topology_errors(
        removed
    )

    duplicated = makefile.replace(grouped_member, grouped_member * 2, 1)
    assert "standalone root/tool membership drift" in _root_tool_topology_errors(
        duplicated
    )

    broad = makefile.replace(
        "$(PYTHON) -m pytest \\\n\ttools/test_import_time_path_leaks.py \\\n",
        "$(PYTHON) -m pytest tools/ \\\n\ttools/test_import_time_path_leaks.py \\\n",
        1,
    )
    assert "broad tools discovery is forbidden" in _root_tool_topology_errors(broad)

    stale_workspace = makefile.replace(
        "$(PYTHON) -m pytest tools/test_workspace_status.py "
        "tools/test_workspace_status_cli.py -q)",
        "$(PYTHON) -m pytest tools/test_workspace_status.py -q)",
        1,
    )
    assert "standalone root/tool membership drift" in _root_tool_topology_errors(
        stale_workspace
    )


def test_approved_group_collection_is_the_exact_isolated_union_in_both_orders() -> None:
    """Grouping changes neither node identity nor skip/xfail disposition."""
    for marker in (None, "skip", "xfail"):
        isolated: list[str] = []
        for path in PROVEN_COMPATIBLE_FILES:
            isolated.extend(_collect_candidate_nodes((path,), marker=marker))
        assert len(isolated) == len(set(isolated))

        forward = _collect_candidate_nodes(PROVEN_COMPATIBLE_FILES, marker=marker)
        reverse = _collect_candidate_nodes(
            tuple(reversed(PROVEN_COMPATIBLE_FILES)), marker=marker
        )
        assert Counter(forward) == Counter(isolated)
        assert Counter(reverse) == Counter(isolated)
        if marker is None:
            assert len(isolated) == 58
            assert (
                hashlib.sha256("\n".join(sorted(isolated)).encode()).hexdigest()
                == PROVEN_COMPATIBLE_NODE_HASH
            )


def test_approved_group_collection_has_only_the_characterized_path_delta() -> None:
    """Importing the five files moves only the reviewed root/tools path pair."""
    prefix = REPO_ROOT / "state_guard_unused"
    result = _run_state_guard(
        PROVEN_COMPATIBLE_FILES,
        collect_only=True,
        designated_prefix=prefix,
        allow_path={
            str(REPO_ROOT): 1,
            # One ordinary pytest prepend plus the characterized consequent
            # prepend after test_branch_added_paths inserts the repo root.
            str(REPO_ROOT / "tools"): 2,
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_full_body_verifier_pins_real_isolated_and_reordered_sessions() -> None:
    """The explicit verifier owns eight real, fail-fast state-guard sessions."""
    repo = str(REPO_ROOT)
    tools = str(REPO_ROOT / "tools")
    expected = tuple(
        (
            f"isolated:{path}",
            (path,),
            {tools: 1, **({repo: 1} if path == PROVEN_COMPATIBLE_FILES[3] else {})},
        )
        for path in PROVEN_COMPATIBLE_FILES
    ) + (
        (
            "group:forward:1",
            PROVEN_COMPATIBLE_FILES,
            {repo: 1, tools: 2},
        ),
        (
            "group:reverse",
            tuple(reversed(PROVEN_COMPATIBLE_FILES)),
            {repo: 1, tools: 2},
        ),
        (
            "group:forward:2",
            PROVEN_COMPATIBLE_FILES,
            {repo: 1, tools: 2},
        ),
    )
    assert _approved_compatibility_verification_runs() == expected

    green = subprocess.CompletedProcess([], 0, "58 passed\n", "")
    with mock.patch.object(
        sys.modules[__name__], "_run_state_guard", return_value=green
    ) as run:
        assert _verify_approved_compatibility_class(REPO_ROOT) == 0
    assert run.call_count == 8
    for index, ((_, paths, allow_path), call) in enumerate(
        zip(expected, run.call_args_list, strict=True), 1
    ):
        assert call.args == (paths,)
        assert call.kwargs == {
            "designated_prefix": REPO_ROOT
            / f"pytest-session-state-{os.getpid()}-{index}",
            "allow_path": allow_path,
        }

    red = subprocess.CompletedProcess([], 1, "failed\n", "diagnostic\n")
    with mock.patch.object(
        sys.modules[__name__], "_run_state_guard", side_effect=(green, red)
    ) as run:
        assert _verify_approved_compatibility_class(REPO_ROOT) == 1
    assert run.call_count == 2


def test_compatibility_class_has_no_atexit_registration() -> None:
    """The actual class is clean and the source check rejects a registration."""
    for path in PROVEN_COMPATIBLE_FILES:
        source = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert _forbidden_atexit_registration_errors(source) == []
    assert _forbidden_atexit_registration_errors(
        "import atexit\natexit.register(lambda: None)\n"
    ) == ["atexit registration"]


def test_state_guard_controls_detect_each_persistent_channel() -> None:
    """Synthetic file-boundary leaks prove every runtime channel is observed."""
    mutations = {
        "env": "import os\nos.environ['STATE_GUARD_LEAK'] = '1'",
        "cwd": (
            "import os, pathlib\n"
            "os.chdir(pathlib.Path(os.environ['STATE_GUARD_REPO_ROOT']).parent)"
        ),
        "logging": "import logging\nlogging.getLogger().addHandler(logging.NullHandler())",
        "warnings": "import os\nos.environ['STATE_GUARD_LATE_WARNING'] = '1'",
        "signals": (
            "import signal\n"
            "signal.signal(signal.SIGTERM, lambda signum, frame: None)"
        ),
        "locale": (
            "import locale\n"
            "before = locale.setlocale(locale.LC_ALL, None)\n"
            "for candidate in ('C', 'C.UTF-8', 'en_US.UTF-8'):\n"
            "    try:\n"
            "        locale.setlocale(locale.LC_ALL, candidate)\n"
            "    except locale.Error:\n"
            "        continue\n"
            "    if locale.setlocale(locale.LC_ALL, None) != before:\n"
            "        break"
        ),
        "timezone": (
            "import os, time\n"
            "os.environ['TZ'] = 'GMT+5' if os.environ.get('TZ') != 'GMT+5' else 'UTC0'\n"
            "getattr(time, 'tzset', lambda: None)()"
        ),
        "asyncio": (
            "import asyncio\n"
            "asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())"
        ),
        "threads": (
            "import threading, time\n"
            "threading.Thread(target=time.sleep, args=(1.5,), daemon=False).start()"
        ),
        "children": (
            "import multiprocessing, time\n"
            "multiprocessing.Process(target=time.sleep, args=(1.5,)).start()"
        ),
        "filesystem": (
            "import os, pathlib\n"
            "pathlib.Path(os.environ['STATE_GUARD_FS_PREFIX']).write_text('leak')"
        ),
    }
    for channel, mutation in mutations.items():
        with unittest.TestCase().subTest(channel=channel):
            paths: list[Path] = []
            with tempfile.NamedTemporaryFile(
                prefix="state_guard_fs_", dir=REPO_ROOT
            ) as prefix_handle:
                designated = Path(prefix_handle.name)
            try:
                mutator_body = "def test_mutator():\n" + "".join(
                    f"    {line}\n" for line in mutation.splitlines()
                )
                for label, body in (
                    ("mutator", mutator_body),
                    ("following", "def test_following():\n    pass\n"),
                ):
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        prefix=f"test_state_guard_{label}_",
                        suffix=".py",
                        dir=REPO_ROOT,
                        delete=False,
                    ) as handle:
                        handle.write(body)
                        paths.append(Path(handle.name))
                result = _run_state_guard(
                    tuple(path.name for path in paths),
                    designated_prefix=designated,
                )
                output = result.stdout + result.stderr
                assert result.returncode != 0, f"undetected {channel} mutation:\n{output}"
                assert channel in output, output
            finally:
                for path in paths:
                    path.unlink(missing_ok=True)
                designated.unlink(missing_ok=True)


def test_grouped_failure_retains_normal_pytest_attribution() -> None:
    """A failing member cannot be hidden by the surrounding compatibility class."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="test_group_failure_",
        suffix=".py",
        dir=REPO_ROOT,
        delete=False,
    ) as handle:
        failure = Path(handle.name)
        handle.write("def test_group_synthetic_failure():\n    assert False\n")
    try:
        env = os.environ.copy()
        env.pop("PYTEST_ADDOPTS", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *PROVEN_COMPATIBLE_FILES,
                failure.name,
                "-q",
                "-p",
                "no:cacheprovider",
                "-k",
                "group_synthetic_failure",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert result.returncode == 1, result.stdout + result.stderr
        assert f"{failure.name}::test_group_synthetic_failure" in result.stdout
        assert "1 failed, 58 deselected" in result.stdout
    finally:
        failure.unlink(missing_ok=True)


def test_import_path_guard_attributes_a_temporary_package_path_mutator() -> None:
    """The retained broad child catches the dangerous fails-alone/pass-grouped shape."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="test_path_leak_mutator_",
        suffix=".py",
        dir=REPO_ROOT / "tools",
        delete=False,
    ) as handle:
        mutator = Path(handle.name)
        handle.write(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).parents[1] / 'packages' / "
            "'agentbundle'))\n"
            "def test_control():\n    pass\n"
        )
    try:
        guard = _load_module(
            "tools/test_import_time_path_leaks.py", "path_guard_mutation_control"
        )
        report = guard._collect_in_child()
        mutator_node = f"tools/{mutator.name}"
        assert any(
            leak["nodeid"] == mutator_node for leak in report["leaks"]
        ), report
        assert report["final"] != report["baseline"]
    finally:
        mutator.unlink(missing_ok=True)


def test_make_floor_stream_mutations_fail_closed() -> None:
    """Redirection and pipes on either desk stream are independently detected."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    suite = next(iter(COLLECTION_FLOORS))
    for suffix in (
        "> floor.stdout",
        "2> floor.stderr",
        "| tee floor.stdout",
        "2>&1 | tee floor.stderr",
    ):
        mutated = _mutate_floor_make_command(makefile, suite, suffix)
        assert _floor_make_errors(mutated), suffix


def test_shared_test_contract_mutations_fail_closed() -> None:
    """Missing owners and stale, absent, or double exclusions cannot go green."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    chain = (REPO_ROOT / "tools/repo/build_gate_chain.py").read_text(encoding="utf-8")
    assert _composition_errors(makefile, chain) == []

    without_owner = chain.replace('"tools", "test_workspace_status.py",', '"tools", "renamed_workspace_status.py",', 1)
    assert "build ownership drift" in _composition_errors(makefile, without_owner)

    without_exclusion = makefile.replace(f"--ignore={SHARED_TESTS[0]}", "", 1)
    assert "composed exclusion drift" in _composition_errors(without_exclusion, chain)

    stale_exclusion = makefile.replace(
        f"--ignore={SHARED_TESTS[0]}",
        "--ignore=packs/core/tests/skills/work-loop/test_unrelated.py",
        1,
    )
    assert "composed exclusion drift" in _composition_errors(stale_exclusion, chain)

    double_skip = chain.replace(
        '"tools", "test_workspace_status_cli.py",',
        '"tools", "renamed_workspace_status_cli.py",',
        1,
    )
    assert "build ownership drift" in _composition_errors(makefile, double_skip)

    owner_call = '''\
        _script_step(
            "test-workspace-status",
            "tools", "test_workspace_status.py",
        ),
'''
    duplicate_owner = chain.replace(owner_call, owner_call * 2, 1)
    assert duplicate_owner != chain
    assert "build ownership drift" in _composition_errors(makefile, duplicate_owner)


def test_sast_sca_and_terminal_verdict_surfaces_match_approved_bytes() -> None:
    """The composition edit cannot change scanner commands, order, or verdicts."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    surfaces = _approved_make_surfaces(makefile)
    assert set(surfaces) == set(MAKE_BASELINE_DIGESTS)
    for name, source in surfaces.items():
        assert hashlib.sha256(source.encode()).hexdigest() == MAKE_BASELINE_DIGESTS[name]


def _make_dry_run(
    target: str,
    *,
    assignments: tuple[str, ...] = (),
    makefile_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Expand one real Make target, optionally from a mutation fixture."""
    make = shutil.which("make")
    if make is None:
        raise unittest.SkipTest("actual Make construction requires make")

    fixture: Path | None = None
    makefile = Path("Makefile")
    if makefile_text is not None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".mk",
            prefix="local-ci-expansion-",
            delete=False,
        ) as handle:
            fixture = Path(handle.name)
            handle.write(makefile_text)
        makefile = fixture
    try:
        return subprocess.run(
            [
                make,
                "-f",
                str(makefile),
                "-n",
                target,
                *assignments,
                f"PYTHON={sys.executable}",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    finally:
        if fixture is not None:
            fixture.unlink(missing_ok=True)


def _normalized_command_plan(stdout: str) -> list[str]:
    """Normalize a Make dry-run into stable command-bearing lines."""
    plan: list[str] = []
    pending = ""
    for raw_line in stdout.splitlines():
        physical = raw_line.strip()
        continued = physical.endswith("\\")
        if continued:
            physical = physical[:-1]
        pending = f"{pending} {physical}".strip()
        if continued:
            continue
        line = " ".join(pending.split())
        pending = ""
        if not line or line.startswith("#"):
            continue
        plan.append(line.replace(sys.executable, "<PYTHON>"))
    if pending:
        plan.append(" ".join(pending.split()).replace(sys.executable, "<PYTHON>"))
    return plan


def _root_tool_pytest_groups(stdout: str) -> tuple[tuple[str, ...], ...]:
    """Return explicit root/tool pytest targets from one expanded Make plan."""
    groups: list[tuple[str, ...]] = []
    for line in _normalized_command_plan(stdout):
        tokens = line.split()
        try:
            pytest_index = next(
                index
                for index in range(len(tokens) - 1)
                if tokens[index : index + 2] == ["-m", "pytest"]
            )
        except StopIteration:
            continue
        targets = tuple(
            token
            for token in tokens[pytest_index + 2 :]
            if token in {"tests/", "tools/"} or token.startswith("tools/test_")
        )
        if targets:
            groups.append(targets)
    return tuple(groups)


def _root_tool_topology_errors(makefile_text: str | None = None) -> list[str]:
    """Return membership or process-boundary drift in the two real profiles."""
    errors: list[str] = []
    standalone = _make_dry_run("test-unleased", makefile_text=makefile_text)
    composed = _make_dry_run(
        "test-after-build-check-unleased", makefile_text=makefile_text
    )
    if standalone.returncode != 0 or composed.returncode != 0:
        return ["Make expansion failed"]

    standalone_groups = _root_tool_pytest_groups(standalone.stdout)
    composed_groups = _root_tool_pytest_groups(composed.stdout)
    if len(standalone_groups) != 15:
        errors.append("standalone root/tool process count drift")
    if len(composed_groups) != 14:
        errors.append("composed root/tool process count drift")

    standalone_paths = [path for group in standalone_groups for path in group]
    composed_paths = [path for group in composed_groups for path in group]
    if Counter(standalone_paths) != Counter(EXPECTED_ROOT_TOOL_PATHS):
        errors.append("standalone root/tool membership drift")
    expected_composed = EXPECTED_ROOT_TOOL_PATHS - set(WORKSPACE_STATUS_PAIR)
    if Counter(composed_paths) != Counter(expected_composed):
        errors.append("composed root/tool membership drift")
    if PROVEN_COMPATIBLE_FILES not in standalone_groups:
        errors.append("approved compatibility class drift")
    if PROVEN_COMPATIBLE_FILES not in composed_groups:
        errors.append("composed compatibility class drift")
    if WORKSPACE_STATUS_PAIR not in standalone_groups:
        errors.append("standalone workspace-status ownership drift")
    if any(set(group) & set(WORKSPACE_STATUS_PAIR) for group in composed_groups):
        errors.append("composed workspace-status ownership drift")
    if any("tools/" in group for group in standalone_groups + composed_groups):
        errors.append("broad tools discovery is forbidden")
    return errors


def _collect_candidate_nodes(
    paths: tuple[str, ...], *, marker: str | None = None
) -> tuple[str, ...]:
    """Collect candidate node IDs in one fresh, ambient-option-free process."""
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if marker is not None:
        argv.extend(["-m", marker])
    argv.extend(paths)
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode not in {0, 5}:
        raise AssertionError(
            f"candidate collection failed ({result.returncode}):\n{result.stdout}\n"
            f"{result.stderr}"
        )
    return tuple(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("tools/") and "::" in line
    )


def _run_state_guard(
    paths: tuple[str, ...],
    *,
    collect_only: bool = False,
    designated_prefix: Path,
    allow_path: dict[str, int] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the test-only process-state plugin in a fresh interpreter."""
    args = (["--collect-only"] if collect_only else []) + list(paths)
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["STATE_GUARD_REPO_ROOT"] = str(REPO_ROOT)
    env["STATE_GUARD_FS_PREFIX"] = str(designated_prefix)
    env["STATE_GUARD_ARGS"] = json.dumps(args)
    env["STATE_GUARD_ALLOW_PATH"] = json.dumps(allow_path or {})
    return subprocess.run(
        [sys.executable, "-B", "-c", _STATE_GUARD_RUNNER],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )


def _approved_compatibility_verification_runs(
) -> tuple[tuple[str, tuple[str, ...], dict[str, int]], ...]:
    """Return the exact isolated and grouped full-body evidence sequence."""
    repo = str(REPO_ROOT)
    tools = str(REPO_ROOT / "tools")
    isolated = tuple(
        (
            f"isolated:{path}",
            (path,),
            {tools: 1, **({repo: 1} if path == PROVEN_COMPATIBLE_FILES[3] else {})},
        )
        for path in PROVEN_COMPATIBLE_FILES
    )
    grouped = (
        ("group:forward:1", PROVEN_COMPATIBLE_FILES, {repo: 1, tools: 2}),
        (
            "group:reverse",
            tuple(reversed(PROVEN_COMPATIBLE_FILES)),
            {repo: 1, tools: 2},
        ),
        ("group:forward:2", PROVEN_COMPATIBLE_FILES, {repo: 1, tools: 2}),
    )
    return isolated + grouped


def _verify_approved_compatibility_class(designated_root: Path) -> int:
    """Execute every approved full-body state-guard session, failing fast."""
    for index, (label, paths, allow_path) in enumerate(
        _approved_compatibility_verification_runs(), 1
    ):
        result = _run_state_guard(
            paths,
            designated_prefix=designated_root
            / f"pytest-session-state-{os.getpid()}-{index}",
            allow_path=allow_path,
        )
        if result.returncode != 0:
            print(f"{label}: exit {result.returncode}", file=sys.stderr)
            print(result.stdout, end="", file=sys.stderr)
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        summary = next(
            (line for line in reversed(result.stdout.splitlines()) if "passed" in line),
            "completed without a pytest pass summary",
        )
        print(f"{label}: {summary}")
    return 0


def _forbidden_atexit_registration_errors(source: str) -> list[str]:
    """Reject atexit registration in compatibility-class test source."""
    tree = ast.parse(source)
    return [
        "atexit registration"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "atexit"
        and node.func.attr == "register"
    ]


def _without_construction_addition(plan: list[str]) -> list[str]:
    """Remove the one approved new test path before baseline comparison."""
    return [
        " ".join(line.replace(f" {CONSTRUCTION_TEST_PATH}", "").split())
        for line in plan
    ]


def _plan_digest(plan: list[str]) -> str:
    """Hash a normalized command plan with an unambiguous line boundary."""
    return hashlib.sha256(("\n".join(plan) + "\n").encode()).hexdigest()


def _effective_composition_errors(makefile_text: str | None = None) -> list[str]:
    """Return drift in GNU Make's effective standalone and composed commands."""
    errors: list[str] = []
    standalone = _make_dry_run("test-unleased", makefile_text=makefile_text)
    composed = _make_dry_run(
        "test-after-build-check-unleased", makefile_text=makefile_text
    )
    if standalone.returncode != 0 or composed.returncode != 0:
        return ["Make expansion failed"]

    standalone_ignore_list = re.findall(r"--ignore=([^\s]+)", standalone.stdout)
    composed_ignore_list = re.findall(r"--ignore=([^\s]+)", composed.stdout)
    standalone_ignores = set(standalone_ignore_list)
    composed_ignores = set(composed_ignore_list)
    if standalone_ignores:
        errors.append("standalone effective recipe became reduced")
    if (
        composed_ignores != COMPOSED_EXCLUSIONS
        or len(composed_ignore_list) != len(COMPOSED_EXCLUSIONS)
    ):
        errors.append("composed effective exclusion drift")
    if not all(path in standalone.stdout for path in SHARED_TESTS[3:]):
        errors.append("standalone effective workspace coverage missing")
    if any(path in composed.stdout for path in SHARED_TESTS[3:]):
        errors.append("composed effective workspace command present")
    if not all(
        directory in standalone.stdout and directory in composed.stdout
        for directory in (
            "packs/core/tests/skills/work-loop/",
            "packs/core/tests/skills/author-delivery-brief/",
            "packs/core/tests/skills/receive-brief/",
        )
    ):
        errors.append("effective core directory coverage drift")

    composed_lines = _normalized_command_plan(composed.stdout)
    for target, expected_ignores in EXPECTED_COMPOSED_IGNORES.items():
        target_lines = [
            line
            for line in composed_lines
            if f"-m pytest {target}" in line
        ]
        actual_ignores = (
            set(re.findall(r"--ignore=([^\s]+)", target_lines[0]))
            if len(target_lines) == 1
            else set()
        )
        if len(target_lines) != 1 or actual_ignores != expected_ignores:
            errors.append("composed effective ignore placement drift")
            break

    workspace_command = " ".join(
        f"<PYTHON> -m pytest {SHARED_TESTS[3]} {SHARED_TESTS[4]} -q".split()
    )
    standalone_full_plan = _normalized_command_plan(standalone.stdout)
    if standalone.stdout.count(CONSTRUCTION_TEST_PATH) != 1:
        errors.append("standalone construction coverage drift")
    if composed.stdout.count(CONSTRUCTION_TEST_PATH) != 1:
        errors.append("composed construction coverage drift")
    if (
        _plan_digest(_without_construction_addition(standalone_full_plan))
        != APPROVED_STANDALONE_PLAN_DIGEST
    ):
        errors.append("approved standalone command plan drift")

    standalone_plan: list[str] = []
    workspace_command_count = 0
    for line in standalone_full_plan:
        if workspace_command in line:
            workspace_command_count += line.count(workspace_command)
            line = " ".join(
                line.replace(workspace_command, "").strip(" ;").split()
            )
        if line:
            standalone_plan.append(line)

    composed_plan: list[str] = []
    for line in composed_lines:
        for path in COMPOSED_EXCLUSIONS:
            line = line.replace(f" --ignore={path}", "")
        composed_plan.append(" ".join(line.split()))

    if (
        _plan_digest(_without_construction_addition(composed_plan))
        != APPROVED_COMPOSED_PLAN_DIGEST
    ):
        errors.append("approved composed command plan drift")

    if workspace_command_count != 1 or standalone_plan != composed_plan:
        errors.append("effective non-shared command plan drift")
    return errors


def _run_make_harness(
    target: str,
    *,
    fail_shared: bool = False,
    fail_nonshared: bool = False,
    ambient_profile: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the real recursive graph with only expensive leaf recipes replaced."""
    make = shutil.which("make")
    if make is None or os.name != "posix":
        raise unittest.SkipTest(
            "actual recursive Make construction requires POSIX make"
        )

    harness_text = f"""\
include {REPO_ROOT / 'Makefile'}

build-check:
\t@if [ \"$$FAIL_SHARED\" = 1 ]; then echo 'EVENT shared-failure'; exit 23; fi
\t@sleep 0.1
\t@echo 'EVENT build-check'

lint-editable-install:
\t@:

lint-ruff:
\t@:

lint-mypy:
\t@:

test-unleased:
\t@echo \"EVENT full makelevel=$$MAKELEVEL\"

test-after-build-check-unleased:
\t@if [ \"$$FAIL_NONSHARED\" = 1 ]; then echo 'EVENT nonshared-failure'; exit 29; fi
\t@echo \"EVENT reduced makelevel=$$MAKELEVEL\"
"""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".mk",
        prefix="local-ci-shared-test-",
        delete=False,
    ) as handle:
        harness = Path(handle.name)
        handle.write(harness_text)
    try:
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "MAKELEVEL"}
        }
        env["FAIL_SHARED"] = "1" if fail_shared else "0"
        env["FAIL_NONSHARED"] = "1" if fail_nonshared else "0"
        if ambient_profile:
            env["LOCAL_CI_TEST_PROFILE"] = "reduced"
        return subprocess.run(
            [
                make,
                "-f",
                str(harness),
                "-j4",
                target,
                f"PYTHON={sys.executable}",
                "SKIP_SAST=1",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    finally:
        harness.unlink(missing_ok=True)


def test_real_recursive_make_selects_safe_full_and_composed_routes() -> None:
    """The first-file harness pins recursion, ambient safety, and parallel order."""
    composed = _run_make_harness("ci")
    assert composed.returncode == 0, composed.stdout + composed.stderr
    assert "EVENT full" not in composed.stdout
    assert composed.stdout.count("EVENT build-check") == 1
    assert composed.stdout.count("EVENT reduced") == 1
    assert composed.stdout.index("EVENT build-check") < composed.stdout.index("EVENT reduced")
    makelevel = re.search(r"EVENT reduced makelevel=(\d+)", composed.stdout)
    assert makelevel is not None and int(makelevel.group(1)) > 0

    standalone = _run_make_harness("test", ambient_profile=True)
    assert standalone.returncode == 0, standalone.stdout + standalone.stderr
    assert standalone.stdout.count("EVENT full") == 1
    assert "EVENT reduced" not in standalone.stdout
    assert "EVENT build-check" not in standalone.stdout


def test_standalone_make_rejects_command_line_suite_reduction() -> None:
    """A command-line macro value cannot replace standalone test coverage."""
    result = _make_dry_run(
        "test-unleased",
        assignments=("run-test-suite=@echo EVENT command-line-reduced",),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EVENT command-line-reduced" not in result.stdout
    assert "packages/agentbundle/tests/" in result.stdout
    assert f"{SHARED_TESTS[3]} {SHARED_TESTS[4]}" in result.stdout


def test_effective_make_recipes_apply_exact_composition_and_fail_on_mutation() -> None:
    """Real Make expansion pins every placeholder that applies the reduction."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert _effective_composition_errors() == []

    without_work_loop_parameter = makefile.replace(
        "packs/core/tests/skills/work-loop/ $(1) -q",
        "packs/core/tests/skills/work-loop/ -q",
        1,
    )
    assert "composed effective exclusion drift" in _effective_composition_errors(
        without_work_loop_parameter
    )

    without_delivery_brief_parameter = makefile.replace(
        "packs/core/tests/skills/author-delivery-brief/ $(2) -q",
        "packs/core/tests/skills/author-delivery-brief/ -q",
        1,
    )
    assert "composed effective exclusion drift" in _effective_composition_errors(
        without_delivery_brief_parameter
    )

    hardcoded_workspace_command = makefile.replace(
        "$(3)\n",
        (
            "$(PYTHON) -m pytest tools/test_workspace_status.py "
            "tools/test_workspace_status_cli.py -q\n$(3)\n"
        ),
        1,
    )
    assert "composed effective workspace command present" in (
        _effective_composition_errors(hardcoded_workspace_command)
    )

    nonshared_command = "$(PYTHON) -m pytest tools/test_worktree_hygiene.py -q"
    moved_nonshared_command = makefile.replace(
        f"{nonshared_command}\n",
        "",
        1,
    ).replace(
        (
            "$(PYTHON) -m pytest tools/test_workspace_status.py "
            "tools/test_workspace_status_cli.py -q)"
        ),
        (
            "$(PYTHON) -m pytest tools/test_workspace_status.py "
            f"tools/test_workspace_status_cli.py -q; {nonshared_command})"
        ),
        1,
    )
    assert "effective non-shared command plan drift" in (
        _effective_composition_errors(moved_nonshared_command)
    )

    swapped_parameters = makefile.replace(
        "packs/core/tests/skills/author-delivery-brief/ $(2) -q",
        "packs/core/tests/skills/author-delivery-brief/ $(1) -q",
        1,
    ).replace(
        "packs/core/tests/skills/work-loop/ $(1) -q",
        "packs/core/tests/skills/work-loop/ $(2) -q",
        1,
    )
    assert "composed effective ignore placement drift" in (
        _effective_composition_errors(swapped_parameters)
    )

    deleted_nonshared_command = makefile.replace(
        "$(PYTHON) -m pytest packs/core/tests/skills/work-intake/ -q\n",
        "",
        1,
    )
    deletion_errors = _effective_composition_errors(deleted_nonshared_command)
    assert "approved standalone command plan drift" in deletion_errors
    assert "approved composed command plan drift" in deletion_errors


def test_real_recursive_make_propagates_shared_and_unrelated_failures() -> None:
    """Both owning-gate and ordinary non-shared failures keep composed CI red."""
    shared = _run_make_harness("ci", fail_shared=True)
    assert shared.returncode != 0
    assert "EVENT shared-failure" in shared.stdout
    assert "EVENT reduced" not in shared.stdout

    nonshared = _run_make_harness("ci", fail_nonshared=True)
    assert nonshared.returncode != 0
    assert "EVENT build-check" in nonshared.stdout
    assert "EVENT nonshared-failure" in nonshared.stdout
    assert "EVENT reduced" not in nonshared.stdout


if __name__ == "__main__":
    if sys.argv[1:] != ["--verify-approved-compatibility-class"]:
        raise SystemExit(
            "usage: python tools/test_local_ci_shared_test_deduplication.py "
            "--verify-approved-compatibility-class"
        )
    raise SystemExit(
        _verify_approved_compatibility_class(Path(tempfile.gettempdir()))
    )
