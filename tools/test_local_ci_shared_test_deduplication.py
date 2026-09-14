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
    # Re-pinned 2026-08-31: 78 -> 85, in two steps neither of which re-pinned this
    # contract, so it has been red on main since the first of them. Recomputing the
    # static node set at each revision of the pinned file gives 78 at `34f00cf29`
    # (digest `dd567702b9`, the value replaced here), 82 at `d5192da9a`, and 85 at
    # `487b298c4`; nothing was removed or renamed at either step, and the surviving
    # 78 keep their original relative order.
    # `d5192da9a` ("scope lint-spec-status to the specs a session touched") added
    # four tests for the selection it introduced —
    # test_default_scope_checks_changed_spec_but_not_unchanged_specs,
    # test_all_scope_checks_unchanged_specs_too,
    # test_unresolvable_base_ref_falls_back_to_full_per_spec_checks, and
    # test_scoped_run_keeps_dangling_reference_warnings_repo_wide.
    # `487b298c4` ("keep the deferral-anchor invariant repo-wide, and close three
    # more fail-opens") added three more —
    # test_scoped_run_keeps_deferral_anchors_repo_wide,
    # test_scoped_run_reports_the_coverage_it_achieved, and
    # test_undetermined_changed_set_sweeps_and_says_so.
    # Dispositioned rather than taken from either side, as the note above requires:
    # each of the seven asserts a distinct way scoped selection could silently check
    # nothing, which is the failure the two commits set out to prevent, and the other
    # two entries below still reproduce.
    # Re-pinned 2026-09-10: 85 -> 87. The core lints now default to reporting
    # warn-only findings rather than listing them, and two additions cover that
    # default — test_warn_only_findings_are_hidden_without_verbose and
    # test_a_failing_run_still_lists_warnings_without_verbose, the second
    # asserting that a HARD violation still prints warnings so a failure is
    # never truncated. Dispositioned as the note above requires: an AST diff of
    # the test-name set against origin/main shows two additions, no removal and
    # no rename, and the `lint-brief-coverage` entry below still reproduces,
    # which confirms the recomputation method rather than assuming it.
    SHARED_TESTS[0]: (
        87,
        "ba7a01f5b92da41e2f6ba0b2a51c2d57d7edef9b3630f9e88d4418969b3546e1",
    ),
    # Re-pinned 2026-09-01: 16 -> 27. `885176fad` ("separate brief withdrawal
    # from cancellation") added the six-state lifecycle coverage without
    # re-pinning this contract, and its two new parametrized tests carried no
    # `ids=`, so the ID requirement below fired before the count ever could —
    # this check has been red on main since that commit. Dispositioned rather
    # than taken from either side: recomputing the static node set at
    # `20c0ba50e` reproduces 16 (digest `9eb2121531`, the value replaced here);
    # against that base the delta is one rename, test_all_shipped_delivered ->
    # test_explicitly_shipped_all_shipped_map_is_delivered (same body, now
    # writing the brief's explicit `Shipped` status, because an all-shipped Spec
    # map alone no longer closes a brief), plus three unparametrized additions —
    # test_all_shipped_map_requires_explicit_shipped_status,
    # test_statusless_all_shipped_map_fails_closed, and
    # test_shipped_requires_nonempty_all_shipped_map — and two parametrized
    # ones: test_untracked_backlink_contributes_execution_evidence (2 arms) and
    # test_terminated_brief_child_scope (6 arms, one per Withdrawn/Cancelled
    # crossing with a child's Approved/Implementing/Shipped state). Nothing else
    # was removed, and the surviving 15 keep their original relative order.
    SHARED_TESTS[1]: (
        27,
        "fccaac7b6628f5848f29f22c64bd613f7bfcb688433aadee39fbcd90d1448821",
    ),
    # Re-pinned 2026-09-10: 45 -> 48, same change as SHARED_TESTS[0]. A passing
    # traceability run now withholds its per-item detail lines, and three
    # additions cover it — test_detail_lines_are_hidden_on_a_passing_run,
    # test_a_failing_run_prints_every_line_without_verbose (a non-zero exit is
    # never truncated), and test_every_detail_line_carries_the_detail_prefix,
    # which fails if a new `out.append` uses a different indent and so would
    # otherwise be unsuppressible. Dispositioned by the same AST diff: three
    # additions, no removal, no rename.
    SHARED_TESTS[2]: (
        48,
        "1f360511421f260d9d25850f8c889a59007f5c66ceeb40e6dee12fcb86416010",
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
    # Measured at 4,247 on 2026-08-30 (CPython 3.13.13,
    # PYTHONPATH=packages/agentbundle:packages/credbroker, configfile
    # packages/agentbundle/pyproject.toml). The floor is 75.3% of measured,
    # leaving 1,047 tests of headroom. The measurement is recorded with its
    # date and interpreter rather than as a bare subtraction: an undated figure
    # cannot be re-checked, and a bare `python3 -m pytest
    # packages/agentbundle/tests/` measures the wrong thing — it resolves a
    # stale non-editable `agentbundle` from site-packages, because that
    # package's pyproject.toml is the nearer pytest configfile and does not
    # carry the root `pythonpath`.
    "packages/agentbundle/tests/": 3200,
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
    # spec/self-host-projection-merge-driver: both suites gate the
    # `merge=regen` block, and `lint-ci-parity` disposes their gate-main steps
    # as LOCAL("test-after-build-check") -- which is only true while this batch
    # runs them.
    "tools/test_gitattributes_merge_driver.py",
    "tools/test_merge_driver_behaviour.py",
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
    "tools/test_guide_ledger_integrity.py",
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
    # Added with the distribution-route decision checker. Nothing globs
    # `tools/test_*.py`, so both were unreachable from any gate before this:
    # the first carries the checker's own mutation evidence, and the second is
    # the guard that fails when a route decision returns to shared build-time
    # code. They join THIS batch specifically because
    # `test_marketplace_envelope_parity` requires the Makefile group naming
    # `test_contract_parity.py` and the build-check.yml step naming it to hold
    # the same set; the first tools batch has no CI counterpart to match.
    "tools/test_check_distribution_route_decisions.py",
    "tools/test_route_branch_guard.py",
    # Added with the direct-install diagnostic-code table lint. The lint
    # itself is a separate recipe line beside lint-conformance-portability;
    # this is its mutation control.
    "tools/test_lint_direct_code_table.py",
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
# Re-pinned by spec/direct-skill-repository-installation, which is the owning
# change. Two edits move both digests, and both appear in the standalone and
# the composed plan alike:
#
#   T10a — the `packages/agentbundle/tests/` line in `run-test-suite` gained
#          `-p tools.pytest_collection_floor`, `--minimum-collected=3200`, and
#          `--collection-floor-suite=packages/agentbundle/tests/`. The floor is
#          registered in COLLECTION_FLOORS above with its measurement.
#   T10  — `tools/lint-direct-code-table.py` runs beside
#          `lint-conformance-portability.py`, and its mutation companion
#          `tools/test_lint_direct_code_table.py` joins the final tool batch.
#          Both are registered in `.github/workflows/build-check.yml` too,
#          because CI runs `build-check` rather than `make test` and a
#          Makefile-only registration never gates a PR.
#
# No other command in either plan changed.
#
# Re-pinned again 2026-09-01 for `tools/test_guide_ledger_integrity.py`, which
# joins the final tools batch, MERGED on top of the direct-skill-repository
# re-pin above. Both line counts are unchanged by this second edit — that batch
# is one continued command, so the module lengthens an existing line rather than
# adding one. Dispositioned by running the same `_effective_composition_errors`
# path against the merged Makefile with and without this change's Makefile line:
# the without-case reproduces the two digests the direct-skill re-pin recorded,
# so that pin was current and this change is the sole cause of the move. Exactly
# one line shifts in each plan, gaining one token, and that token is the new
# module; no other line moves, is reordered, or is dropped.
#
# Re-pinned again 2026-09-03 for the two distribution-route checker modules,
# and corrected 2026-09-08 to the FINAL tools batch after CI's
# `test_marketplace_envelope_parity` refused the first: that gate holds the
# Makefile group naming `test_contract_parity.py` and the build-check.yml step
# naming it to the same set, and the first batch has no CI counterpart. The
# digests below are the final-batch placement. Dispositioned the same way: the same
# `_effective_composition_errors` path was run against this worktree with the
# Makefile line reverted, and it reproduced both digests above exactly, so those
# pins were current and this change is the sole cause of the move. Exactly one
# line shifts in each plan, gaining two tokens, and those tokens are the two new
# modules; no other line moves, is reordered, or is dropped. Line counts are
# unchanged — that batch is one continued command, so the modules lengthen an
# existing line rather than adding one.
# Re-pinned 2026-09-13 for the two merge-driver modules
# (spec/self-host-projection-merge-driver), which join the final tools batch.
# They gate the `merge=regen` block, and `lint-ci-parity` disposes their
# gate-main steps as LOCAL("test-after-build-check"), which is only true while
# this batch runs them.
#
# Dispositioned both ways, through `_effective_composition_errors` itself
# rather than a hand-rolled recomputation. Reproducing a pinned value needs the
# whole path, not just `_normalized_command_plan`: standalone is
# `_plan_digest(_without_construction_addition(plan))`, and composed first
# strips ` --ignore=<path>` for every `COMPOSED_EXCLUSIONS` member from each
# line and re-joins on whitespace. Stopping at the normalized plan yields a
# different hash and sends the next re-pinner chasing a phantom move.
#
# (1) Sole cause: the same path run against this worktree's Makefile and
# against `5c96716d8:Makefile` (before the batch line changed) keeps both line
# counts — 62 standalone, 61 composed — with exactly one line differing in each
# at index 47, gaining exactly the two new module tokens; no other line moves,
# is reordered, or is dropped. (2) Prior pins were current: with the superseded
# digests swapped back in, that same path against the reverted Makefile
# reports no drift, reproducing `d29b113d…` and `61120874…` exactly. This
# second half matters more here than in earlier entries, because this re-pin
# sits on a merge of origin/main that could itself have moved the plan.
# Re-pinned by spec/rendered-page-visual-inspection, which gives the
# frontend-engineering pack its first test tree and so its first runner line.
# Dispositioned through `_effective_composition_errors` itself, both ways the
# block above requires.
#
# (1) Sole cause: the same path against this worktree's Makefile and against
# `05d5ca2fa~1:Makefile` (before the runner line landed) moves each plan by
# exactly one line — standalone 62 -> 63, composed 61 -> 62 — inserting
# `<PYTHON> -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`
# at index 31 in both. Deleting that one line from the new plan reproduces the
# old plan element for element, and it appears exactly once, so nothing else
# moved, was reordered, or was dropped; every later index differs only by the
# shift. (2) Prior pins were current: `_effective_composition_errors` run over
# the pre-change Makefile with the superseded digests still in place reports no
# drift at all, reproducing `7fadaf20…` and `e48c8b01…` exactly, so this re-pin
# is not sitting on a move someone else already made.
APPROVED_STANDALONE_PLAN_DIGEST = (
    "8f32abf234db484ed12269e7b4182a34e5db5ea21764556e852e4d96f17c7583"
)
APPROVED_COMPOSED_PLAN_DIGEST = (
    "de0cadbf5e920afe80eb4ffb024474afa59af915b26e5ab014fdb008bb1c5390"
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
    # Bumped 2026-09-13 for ADR-0113: the comment above the SAST branch was
    # restated (dogfooding -> local reproduction path). Verified before the bump
    # by diffing the extracted surface against HEAD — 9 changed lines, 0 of them
    # non-comment, so the scanner commands, their order, and the verdicts this
    # digest exists to pin are byte-identical.
    "build-check-unleased": "4299c65f68880e4f2e67e4cbf4ac6103154340ccd25ab98c8fca5e574a92b3b9",
    "sast": "6e3046497a9f9ed10e559865ecd9e330d88e37417ccfc35af20bc610616ef0b4",
    "sast-unleased": "cb4177f36bd64773812db97f879ad7e49e197370ecb9934ecb8a133318d4b1e5",
    "SAST_DIRS": "7cb835cf14ea0c97bf450810aea5b0194dbf289b03659ad9308c6efde146ba8c",
    "SAST_CONFIG": "df0eeff32c8f18c84f917e7ea579039c8cc3ab54f4e7adb4b1bc6d09b857961c",
    # Bumped 2026-09-13 for the httpsconnection-detected exclusion. Verified
    # before the bump through `_approved_make_surfaces` itself rather than by
    # hand: SEMGREP_EXCLUDE was the SOLE surface to move, by exactly one added
    # line (the new --exclude-rule), and every other pinned surface reproduced
    # byte-identically. The prior pins were all current against the pre-change
    # Makefile -- zero drift -- so this supersedes a live value, not a stale one.
    "SEMGREP_EXCLUDE": "fefa18aadb6cbbd0ce5295c006ac941d9fdf406dc938fefc62122c1d57ef77c7",
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
    # Linters lead: they are lease-free and finish in seconds, so they must not
    # sit behind build-check's network-bound SAST/SCA leg. build-check keeps its
    # position ahead of test-after-build-check, which also declares it directly.
    if ci_deps != ["lint-ruff", "lint-mypy", "build-check", "test-after-build-check"]:
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
    assert len(cli_contract) == len(direct_cli_nodes) == 162
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

    assert len(direct_ids) == 162
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


# GNU Make announces recursion as ``make[N]: Entering directory '<abs path>'``
# and a matching Leaving line. Those are Make's own notices rather than recipe
# commands, and they carry the checkout's absolute path, so admitting them
# would make the plan differ between a contributor's tree and CI. Make emits
# them only for a recursive invocation, which is why a direct ``pytest`` run
# never sees them while the same test under ``make test`` does. A real recipe
# that invokes Make echoes as ``make -C ...``, with no colon after the program
# name, so it does not match this pattern.
_MAKE_DIRECTORY_NOTICE = re.compile(r"^make(\[\d+\])?: (Entering|Leaving) directory ")


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
        if not line or line.startswith("#") or _MAKE_DIRECTORY_NOTICE.match(line):
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


def _drift_diagnostic(label: str, plan: list[str]) -> list[str]:
    """Report the computed digest and plan so a drift names its own cause.

    A bare "drift" verdict cannot be acted on from a CI log, where the plan is
    not reproducible by hand: the reader needs the digest to re-pin and the
    lines to diff against the approved baseline.
    """
    return [
        f"{label} computed digest: {_plan_digest(plan)}",
        *(f"{label} plan[{index}]: {line}" for index, line in enumerate(plan)),
    ]


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
    standalone_baseline = _without_construction_addition(standalone_full_plan)
    if _plan_digest(standalone_baseline) != APPROVED_STANDALONE_PLAN_DIGEST:
        errors.append("approved standalone command plan drift")
        errors.extend(_drift_diagnostic("standalone", standalone_baseline))

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

    composed_baseline = _without_construction_addition(composed_plan)
    if _plan_digest(composed_baseline) != APPROVED_COMPOSED_PLAN_DIGEST:
        errors.append("approved composed command plan drift")
        errors.extend(_drift_diagnostic("composed", composed_baseline))

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


def test_recursive_make_notices_do_not_move_the_plan_digest() -> None:
    """Make's own recursion notices must not enter the compared plan.

    Under ``make test`` the dry run is a recursive invocation, so Make emits
    ``Entering``/``Leaving directory`` lines carrying the checkout's absolute
    path. A direct ``pytest`` run is not recursive and never sees them, so
    admitting them would pin a digest that only reproduces off CI.
    """
    checkout = "/home/runner/work/agent-ready-repo/agent-ready-repo"
    raw = _make_dry_run("test-unleased").stdout
    recursive = (
        f"make[2]: Entering directory '{checkout}'\n"
        f"{raw}\n"
        f"make[2]: Leaving directory '{checkout}'\n"
    )
    assert _normalized_command_plan(recursive) == _normalized_command_plan(raw)
    assert checkout not in "\n".join(_normalized_command_plan(recursive))


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


def _shard_module() -> ModuleType:
    """Load the shard selector from its repository path."""
    return _load_module("tools/shard_test_roster.py", "_shard_test_roster")


def _shard_fixture_lines() -> list[str]:
    """Return a small roster with every precondition and three work units."""
    return [
        "python3 tools/repo/editable_install_guard.py",
        (
            'command -v npm >/dev/null 2>&1 || { echo "npm missing" >&2; '
            "exit 1; }"
        ),
        (
            'test -d docs-site/node_modules || { echo "deps missing" >&2; '
            "exit 1; }"
        ),
        'python3 -c "import httpx"',
        "python3 -m pytest tests/one/ -q",
        "npm run test:plugins --prefix docs-site",
        "python3 tools/test-pages-workflow.py",
    ]


class _ShardRecordingExecutor:
    """Record each subprocess boundary and return configured status codes."""

    def __init__(self, failures: dict[str, int] | None = None) -> None:
        """Configure optional command-to-status failures."""
        self.calls: list[str] = []
        self.failures = failures or {}

    def __call__(
        self,
        command: str,
        *,
        cwd: Path,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        """Record one command with the production executor's call shape."""
        assert cwd == REPO_ROOT
        assert check is False
        self.calls.append(command)
        return subprocess.CompletedProcess(
            command,
            self.failures.get(command, 0),
        )


@contextlib.contextmanager
def _shard_outside_a_shard() -> Iterator[None]:
    """Run a `main()` case as if not already inside a shard.

    These tests are themselves part of the roster, so under
    `make test SHARD=n SHARDS=m` the selector's own re-entry marker is present
    in the environment and `main()` would refuse by design. Clearing it is what
    lets the same case mean the same thing sharded and unsharded -- without it
    the suite passes locally and fails only on a sharded runner.
    """
    shard = _shard_module()
    with mock.patch.dict(os.environ):
        os.environ.pop(shard.REENTRY_MARKER, None)
        yield


def test_shard_classifies_preconditions_work_and_ignored_lines() -> None:
    """All live line classes are explicit, and unknown lines fail closed."""
    shard = _shard_module()
    preconditions = _shard_fixture_lines()[:4]
    for line in preconditions:
        assert shard.classify(line) == "precondition", line
    assert shard.classify("python3 -m pytest tests/ -q") == "work"
    assert shard.classify("# roster explanation") == "ignore"
    assert shard.classify("   ") == "ignore"

    offending = "ruby unexpected_runner.rb"
    with unittest.TestCase().assertRaises(shard.RosterError) as caught:
        shard.classify(offending)
    assert offending in str(caught.exception)


def test_shard_unit_key_uses_path_arguments_and_normalized_fallback() -> None:
    """Interpreter paths do not hide weighted targets; npm uses its command."""
    shard = _shard_module()
    assert (
        shard.unit_key("/usr/bin/python3 -m pytest tests/ -q")
        == "tests/"
    )
    assert (
        shard.unit_key(" npm   run test:plugins   --prefix docs-site ")
        == "npm run test:plugins --prefix docs-site"
    )


def test_shard_refuses_recursive_make_lines_before_make_runs() -> None:
    """Recursive and forced recipe lines are rejected before expansion."""
    shard = _shard_module()
    fixtures = {
        "recursive": """override define run-test-suite
$(MAKE) observable
endef
test-unleased:
\t$(call run-test-suite)
""",
        "recursive-braced": """override define run-test-suite
${MAKE} observable
endef
test-unleased:
\t$(call run-test-suite)
""",
        "forced": """override define run-test-suite
echo safe
endef
test-unleased:
\t+echo observable
""",
    }
    for name, makefile_text in fixtures.items():
        make_run = mock.Mock()
        with (
            mock.patch.object(shard.subprocess, "run", make_run),
            unittest.TestCase().assertRaises(shard.RosterError),
        ):
            shard.roster_lines(makefile_text)
        # The refusal must PRECEDE the subprocess, not report it afterwards:
        # GNU Make would already have run these lines under `-n`.
        assert make_run.call_args_list == [], name


def test_shard_refuses_nonzero_roster_expansion_without_execution() -> None:
    """A partial dry-run roster never reaches the command executor."""
    shard = _shard_module()
    # The truncated stdout must be lines that classify CLEANLY, so the only
    # thing that can refuse them is the non-zero status. An unclassifiable
    # payload would make this test pass via the classifier even with the status
    # check deleted -- proven: that mutation survived until this fixture changed.
    make_result = subprocess.CompletedProcess(
        ["make"],
        9,
        stdout=(
            "python3 -m pytest tests/ -q\n"
            "python3 -m pytest packs/core/tests/pack/ -q\n"
        ),
        stderr="expansion failed\n",
    )
    recorder = _ShardRecordingExecutor()
    with _shard_outside_a_shard(), mock.patch.object(
        shard.subprocess, "run", return_value=make_result
    ):
        result = shard.main(["--shard", "1", "--shards", "1"], executor=recorder)
    assert result != 0
    assert recorder.calls == []


def test_shard_selector_validation_records_zero_execution() -> None:
    """Data-driven invalid selectors all fail before a roster unit executes."""
    shard = _shard_module()
    invalid_selectors = (
        ("negative shard", ["--shard", "-1", "--shards", "2"]),
        ("zero shard", ["--shard", "0", "--shards", "2"]),
        ("non-integer shard", ["--shard", "one", "--shards", "2"]),
        ("negative shards", ["--shard", "1", "--shards", "-2"]),
        ("zero shards", ["--shard", "1", "--shards", "0"]),
        ("non-integer shards", ["--shard", "1", "--shards", "two"]),
        ("shard exceeds shards", ["--shard", "3", "--shards", "2"]),
        # Make cannot tell unset from empty: `make test SHARD=1` arrives here
        # as an empty --shards, and must be refused rather than defaulted.
        ("shard only", ["--shard", "1", "--shards", ""]),
        ("shards only", ["--shard", "", "--shards", "2"]),
        ("whitespace shard", ["--shard", "  ", "--shards", "2"]),
        ("missing selector", []),
        ("shard flag only", ["--shard", "1"]),
        ("shards flag only", ["--shards", "2"]),
        ("unknown flag", ["--shrd", "1", "--shards", "2"]),
        ("duplicate flag", ["--shard", "1", "--shard", "2", "--shards", "2"]),
        ("flag without value", ["--shard", "1", "--shards"]),
        ("shards exceed work", ["--shard", "1", "--shards", "4"]),
    )
    for name, argv in invalid_selectors:
        recorder = _ShardRecordingExecutor()
        with _shard_outside_a_shard(), mock.patch.object(
            shard,
            "roster_lines",
            return_value=_shard_fixture_lines(),
        ):
            result = shard.main(argv, executor=recorder)
        assert result != 0, name
        assert recorder.calls == [], name


def test_shard_live_roster_partitions_are_complete_and_deterministic() -> None:
    """Every supported shard count is a non-empty partition of the live roster."""
    shard = _shard_module()
    units = [
        line for line in shard.roster_lines() if shard.classify(line) == "work"
    ]
    for shard_count in range(1, 9):
        first = shard.partition(units, shard_count)
        second = shard.partition(units, shard_count)
        flattened = [unit for selected in first for unit in selected]
        assert Counter(flattened) == Counter(units), shard_count
        assert all(selected for selected in first), shard_count
        assert first == second, shard_count

        dropped = [list(selected) for selected in first]
        dropped[-1].pop()
        assert Counter(unit for part in dropped for unit in part) != Counter(units)
        duplicated = [list(selected) for selected in first]
        duplicated[0].append(units[0])
        assert Counter(unit for part in duplicated for unit in part) != Counter(units)


def test_shard_weights_separate_the_two_heaviest_units() -> None:
    """The two heaviest LIVE invocations land in different shards.

    Derived from `_unit_weight`, never named here: an earlier version hardcoded
    a suite that measurement later demoted from first to third, so the assertion
    could have stayed green while the actual heaviest pair shared a shard.
    """
    shard = _shard_module()
    work = [line for line in shard.roster_lines() if shard.classify(line) == "work"]
    ranked = sorted(work, key=lambda unit: -shard._unit_weight(unit))
    heaviest, second = ranked[0], ranked[1]
    assert shard._unit_weight(heaviest) > shard._unit_weight(second) * 0.5

    assignments = shard.partition(work, 4)
    home = {
        unit: index
        for index, selected in enumerate(assignments)
        for unit in selected
    }
    assert home[heaviest] != home[second], (
        shard.unit_key(heaviest),
        shard.unit_key(second),
    )
    # A constant weight collapses this: LPT degenerates to roster order.
    assert len({shard._unit_weight(unit) for unit in work}) > 1


def test_shard_execution_keeps_unit_boundaries_and_all_preconditions() -> None:
    """Each shard runs every precondition, then its exact work-unit list."""
    shard = _shard_module()
    lines = _shard_fixture_lines()
    preconditions = [line for line in lines if shard.classify(line) == "precondition"]
    work_units = [line for line in lines if shard.classify(line) == "work"]
    assignments = shard.partition(work_units, 2)

    for shard_index, assigned in enumerate(assignments, start=1):
        recorder = _ShardRecordingExecutor()
        with _shard_outside_a_shard(), mock.patch.object(
            shard, "roster_lines", return_value=lines
        ):
            result = shard.main(
                ["--shard", str(shard_index), "--shards", "2"],
                executor=recorder,
            )
        assert result == 0
        assert recorder.calls == [*preconditions, *assigned]
        assert recorder.calls[: len(preconditions)] == preconditions


def test_shard_execution_fails_fast_before_later_work_units() -> None:
    """A failed work process propagates its status and stops the shard."""
    shard = _shard_module()
    lines = _shard_fixture_lines()
    preconditions = [line for line in lines if shard.classify(line) == "precondition"]
    work_units = [line for line in lines if shard.classify(line) == "work"]
    recorder = _ShardRecordingExecutor({work_units[1]: 7})

    with _shard_outside_a_shard(), mock.patch.object(
        shard, "roster_lines", return_value=lines
    ):
        result = shard.main(["--shard", "1", "--shards", "1"], executor=recorder)
    assert result == 7
    assert recorder.calls == [*preconditions, work_units[0], work_units[1]]


# ── test-corpus.yml shard-matrix contract ────────────────────────────────────
# The matrix list and the `SHARDS=` literal in the run command are two
# independent pieces of text. If they disagree -- a matrix of [1,2,3] against
# SHARDS=4 -- every job goes green while one shard's suites never run. That is
# the failure class docs/product/intents/gates-that-read-clean-while-gating-
# nothing.md tracks, so the two are pinned against each other here.

SHARD_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test-corpus.yml"


def _shard_workflow_run_scalars(text: str) -> list[str]:
    """Return every executable ``run:`` body, inline and block, from a workflow."""
    lines = text.splitlines()
    scalars: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(\|-?|>-?)?\s*(.*)$", lines[index])
        if match is None:
            index += 1
            continue
        indent, block, inline = match.group(1), match.group(2), match.group(3)
        if block is None:
            scalars.append(inline)
            index += 1
            continue
        body: list[str] = []
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line.startswith(indent + " "):
                break
            body.append(line)
            index += 1
        scalars.append("\n".join(body))
    return scalars


def _shard_matrix_errors(text: str) -> list[str]:
    """Return disagreement between the shard matrix and the ``SHARDS=`` literal."""
    errors: list[str] = []
    matrix_match = re.search(r"(?m)^\s*shard:\s*\[([^\]]*)\]\s*$", text)
    # Read SHARDS= from the EXECUTABLE run scalars only. The surrounding
    # comments explain the contract and contain `SHARDS=4` in prose; a
    # whole-file search matches the backtick-quoted comment first and compares
    # the matrix against a literal nothing executes.
    # Read SHARDS= from the ONE `make test` scalar, not the first scalar that
    # happens to contain the token: an unrelated earlier step containing
    # `SHARDS=4` would otherwise satisfy this check while the real command ran
    # `SHARDS=3`, leaving a shard unrun with every job green.
    make_test = [
        scalar
        for scalar in _shard_workflow_run_scalars(text)
        if re.search(r"(?m)^\s*make\s+test(\s|$)", scalar)
    ]
    if len(make_test) != 1:
        return [f"expected exactly one `make test` run scalar, found {len(make_test)}"]
    shards_match = re.search(r"SHARDS=(\S+)", make_test[0])
    if matrix_match is None:
        return ["no shard matrix found"]
    if shards_match is None:
        return ["no SHARDS= literal found"]

    entries = [item.strip() for item in matrix_match.group(1).split(",") if item.strip()]
    if not all(entry.isdigit() for entry in entries):
        return [f"non-integer matrix entry in {entries}"]
    indexes = [int(entry) for entry in entries]
    try:
        declared = int(shards_match.group(1))
    except ValueError:
        return [f"SHARDS= is not an integer: {shards_match.group(1)!r}"]

    if len(set(indexes)) != len(indexes):
        errors.append(f"duplicate shard index in {indexes}")
    if sorted(indexes) != list(range(1, declared + 1)):
        errors.append(
            f"matrix {sorted(indexes)} is not exactly 1..{declared} (SHARDS={declared})"
        )
    return errors


def test_shard_workflow_matrix_is_exactly_one_through_shards() -> None:
    """The shipped matrix and its SHARDS literal cannot disagree."""
    assert _shard_matrix_errors(SHARD_WORKFLOW.read_text(encoding="utf-8")) == []


def test_shard_workflow_matrix_drift_is_caught() -> None:
    """A gap or a duplicate in the matrix is reported, not tolerated."""
    text = SHARD_WORKFLOW.read_text(encoding="utf-8")
    gapped = text.replace("shard: [1, 2, 3, 4]", "shard: [1, 2, 3]", 1)
    assert gapped != text
    assert _shard_matrix_errors(gapped) != []

    duplicated = text.replace("shard: [1, 2, 3, 4]", "shard: [1, 2, 2, 4]", 1)
    assert duplicated != text
    assert _shard_matrix_errors(duplicated) != []


def _shard_roster_leaks(scalars: list[str]) -> list[str]:
    """Return run scalars that enumerate a suite instead of invoking the target.

    Scoped to executable ``run:`` bodies on purpose. The file's COMMENTS
    legitimately mention ``tests/`` and a test-case name while executing
    neither, so a whole-file text scan would report the shipped workflow.
    Installing pytest is likewise not invoking it, so the check looks for an
    invocation shape rather than the bare word.
    """
    leaks: list[str] = []
    for scalar in scalars:
        if re.search(r"(?m)(^|\s)-m\s+pytest(\s|$)", scalar):
            leaks.append(f"invokes pytest: {scalar!r}")
        if re.search(r"(?m)^\s*pytest(\s|$)", scalar):
            leaks.append(f"invokes pytest: {scalar!r}")
        if re.search(r"test_[A-Za-z0-9_]*\.py", scalar):
            leaks.append(f"names a test file: {scalar!r}")
        # With OR without a trailing slash: `make check packs/core/tests` names
        # a suite just as `tests/` does, and requiring the slash let it through.
        if re.search(r"(^|[\s'\"=/])tests(/|\s|$)", scalar):
            leaks.append(f"names a suite directory: {scalar!r}")
    return leaks


def test_shard_workflow_run_scalars_enumerate_no_suite() -> None:
    """No executable step in test-corpus.yml carries a second roster."""
    scalars = _shard_workflow_run_scalars(SHARD_WORKFLOW.read_text(encoding="utf-8"))
    assert scalars, "no run: scalars parsed — the parser, not the file, is wrong"
    assert _shard_roster_leaks(scalars) == []


def test_shard_workflow_roster_leak_detector_catches_each_shape() -> None:
    """Each forbidden enumeration shape is actually detected."""
    for leaked in (
        "python -m pytest tools/test_build_gate_chain.py -q",
        "pytest packs/core/tests/pack/ -q",
        "make check tools/test_check_artifact_contents.py",
        "make test tests/",
    ):
        assert _shard_roster_leaks([leaked]), leaked


def test_shard_workflow_runs_one_test_step_on_the_exact_runner() -> None:
    """One `make test` step, and the runner label stays an exact literal."""
    text = SHARD_WORKFLOW.read_text(encoding="utf-8")
    scalars = _shard_workflow_run_scalars(text)
    make_test = [s for s in scalars if re.search(r"(?m)^\s*make\s+test(\s|$)", s)]
    assert len(make_test) == 1, make_test
    assert re.fullmatch(
        r"make test SHARD=\$\{\{ matrix\.shard \}\} SHARDS=\d+", make_test[0].strip()
    ), make_test[0]
    assert re.search(r"(?m)^\s*runs-on:\s*ubuntu-latest\s*$", text)


def test_shard_expansion_carries_no_make_chatter_under_hostile_flags() -> None:
    """The dry run stays clean, so `classify` needs no exemption for chatter.

    Regression: run 34789996081 failed all four shards on
    `make[1]: Entering directory ...`. roster_lines runs `make -n` from inside a
    make recipe, so MAKELEVEL is non-zero and GNU Make announces the directory
    on stdout. macOS make stayed quiet; Linux did not.

    The first fix added BOTH `--no-print-directory` and a `make[N]: ` exemption
    in `classify`. The exemption was a hole in a fail-closed classifier, so it is
    gone: this asserts the flag alone is sufficient, including when an ambient
    `-w` in MAKEFLAGS asks for the opposite. Any such line now REFUSES, as an
    unrecognised roster line should.
    """
    shard = _shard_module()
    for environment in (
        {"MAKELEVEL": "1"},
        {"MAKELEVEL": "2", "MAKEFLAGS": "w"},
        {"MAKELEVEL": "1", "MAKEFLAGS": "w --"},
    ):
        with mock.patch.dict(os.environ, environment):
            lines = shard.roster_lines()
        chatter = [
            line
            for line in lines
            if line.lstrip().startswith("make[")
            or "Entering directory" in line
            or "Leaving directory" in line
        ]
        assert not chatter, (environment, chatter[:2])

    # And the classifier no longer excuses it, so a regression is loud.
    for diagnostic in (
        "make[1]: Entering directory '/home/runner/work/x/x'",
        "make[2]: Leaving directory '/tmp/x'",
    ):
        try:
            shard.classify(diagnostic)
        except shard.RosterError:
            continue
        raise AssertionError(f"should have been refused: {diagnostic!r}")


def test_shard_expansion_passes_no_print_directory() -> None:
    """The dry run suppresses the diagnostic at source, not only on read."""
    shard = _shard_module()
    captured: dict[str, list[str]] = {}

    def fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
        captured["argv"] = list(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    with mock.patch.object(shard.subprocess, "run", fake_run):
        shard.roster_lines()
    assert "--no-print-directory" in captured["argv"], captured["argv"]


def test_shard_refuses_combined_force_recipe_prefixes() -> None:
    """`@+cmd` forces execution under -n exactly as `+cmd` does."""
    shard = _shard_module()
    for prefix in ("+", "@+", "-+", "+@", "@-+"):
        makefile_text = (
            "override define run-test-suite\necho safe\nendef\n"
            f"test-unleased:\n\t{prefix}echo observable\n"
        )
        make_run = mock.Mock()
        with (
            mock.patch.object(shard.subprocess, "run", make_run),
            unittest.TestCase().assertRaises(shard.RosterError),
        ):
            shard.roster_lines(makefile_text)
        assert make_run.call_args_list == [], prefix

    # `@` and `-` alone do NOT force execution and must stay allowed, or the
    # refusal would reject the roster's own silenced guard lines.
    allowed = (
        "override define run-test-suite\n@echo safe\n-echo safe\nendef\n"
        "test-unleased:\n\t$(call run-test-suite)\n"
    )
    with mock.patch.object(
        shard.subprocess,
        "run",
        return_value=subprocess.CompletedProcess(["make"], 0, stdout="", stderr=""),
    ):
        shard.roster_lines(allowed)


def test_shard_pytest_shape_outranks_a_precondition_substring() -> None:
    """A suite whose PATH contains a precondition marker is still work.

    Otherwise it leaves the union's work multiset and runs in every shard
    instead of exactly one -- a suite that is over-run and under-proved at once.
    """
    shard = _shard_module()
    line = "python3 -m pytest tools/repo/editable_install_guard.py -q"
    assert shard.classify(line) == "work"
    # The real precondition, which is not a pytest invocation, still classifies.
    assert shard.classify("python3 tools/repo/editable_install_guard.py") == "precondition"


def test_shard_matrix_check_reads_only_the_make_test_scalar() -> None:
    """An unrelated step mentioning SHARDS= cannot satisfy the matrix check."""
    text = SHARD_WORKFLOW.read_text(encoding="utf-8")
    decoyed = text.replace(
        "      - name: make test\n",
        "      - name: decoy\n        run: echo SHARDS=4\n\n      - name: make test\n",
        1,
    ).replace("make test SHARD=${{ matrix.shard }} SHARDS=4", "make test SHARD=${{ matrix.shard }} SHARDS=3", 1)
    assert decoyed != text
    assert _shard_matrix_errors(decoyed) != []


def test_shard_roster_leak_detector_catches_slashless_suite_paths() -> None:
    """A suite directory named without a trailing slash is still a leak."""
    assert _shard_roster_leaks(["make check packs/core/tests"])
    assert _shard_roster_leaks(["make check tests"])
    # And the legitimate shipped steps still read clean.
    assert _shard_roster_leaks(["python -m pip install pytest -r tools/requirements.txt"]) == []
    assert _shard_roster_leaks(["npm ci --prefix docs-site"]) == []


def test_shard_child_environment_cannot_reselect_a_shard() -> None:
    """A roster command that runs `make test` must not inherit the selector.

    Regression: run 34789473362 shard 4 recursed until killed at its timeout,
    producing no output. Make exports command-line variables through MAKEFLAGS,
    so the Makefile harnesses in this very file re-entered the sharded branch.
    """
    shard = _shard_module()
    hostile = {
        "SHARD": "4",
        "SHARDS": "4",
        "MAKEFLAGS": "w -- SHARD=4 SHARDS=4 FOO=keep",
        "PATH": os.environ.get("PATH", ""),
    }
    with mock.patch.dict(os.environ, hostile, clear=True):
        env = shard.child_environment()
    assert "SHARD" not in env
    assert "SHARDS" not in env
    assert "SHARD=4" not in env["MAKEFLAGS"]
    assert "SHARDS=4" not in env["MAKEFLAGS"]
    # Unrelated MAKEFLAGS content survives — this scrubs the selector, not the
    # caller's whole Make configuration.
    assert "FOO=keep" in env["MAKEFLAGS"]
    assert "w" in env["MAKEFLAGS"].split()
    assert env[shard.REENTRY_MARKER] == "1"


def test_shard_refuses_to_run_nested_inside_another_shard() -> None:
    """Residual nesting fails immediately rather than hanging."""
    shard = _shard_module()
    recorder = _ShardRecordingExecutor()
    with mock.patch.dict(os.environ, {shard.REENTRY_MARKER: "1"}):
        result = shard.main(["--shard", "1", "--shards", "2"], executor=recorder)
    assert result != 0
    assert recorder.calls == []


def test_shard_executor_and_expansion_both_use_the_scrubbed_environment() -> None:
    """Both the dry run and every work unit run with the selector stripped."""
    shard = _shard_module()
    seen: list[dict[str, str]] = []

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        seen.append(kwargs.get("env") or {})
        return subprocess.CompletedProcess(args[0] if args else [], 0, stdout="", stderr="")

    with mock.patch.object(shard.subprocess, "run", fake_run):
        shard.roster_lines()
        shard._default_executor("true", cwd=REPO_ROOT, check=False)
    assert len(seen) == 2
    for env in seen:
        assert "SHARD" not in env and "SHARDS" not in env
        assert env.get(shard.REENTRY_MARKER) == "1"


NESTED_SHARD_SUITE = "SHARD_SUITE_NESTED"


def test_shard_suite_passes_with_the_reentry_marker_set() -> None:
    """Run the shard cases as a SHARDED RUNNER runs them, and require green.

    This suite is itself in the roster, so under `make test SHARD=n SHARDS=m`
    the selector's re-entry marker is already in the environment and any case
    calling `main()` without `_shard_outside_a_shard()` is refused. That
    asymmetry passes on a developer's machine and fails only on a sharded
    runner -- it cost run 34790977529 shard 4.

    Three earlier attempts checked this by reading the source: a six-line
    lexical window (which reported itself, twice, and also reported a correctly
    guarded case whose wrapper sat further up), then an AST walk keyed to a
    hardcoded receiver name (which an alias evaded), then one that bound
    receivers (which still only proved a wrapper existed SOMEWHERE in the
    function, not that it enclosed the call). Each round moved the check without
    settling it, because the property is about what happens at RUN time and the
    source cannot decide it.

    So this executes the real thing instead. Every evasion the source-reading
    versions argued about -- aliased loaders, chained receivers, a wrapper in
    the wrong branch -- fails here for the same reason a plain omission does.
    """
    if os.environ.get(NESTED_SHARD_SUITE):
        raise unittest.SkipTest("inner run: this case is what spawned it")

    environment = dict(os.environ)
    environment[_shard_module().REENTRY_MARKER] = "1"
    environment[NESTED_SHARD_SUITE] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(Path(__file__)),
            "-q",
            "--no-header",
            "-k",
            "shard",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    # Guard the guard: a run that collected nothing would pass vacuously.
    assert " passed" in result.stdout, result.stdout[-2000:]


def test_shard_executor_names_the_shell_and_runs_one_command() -> None:
    """Each unit runs as `sh -c <line>`: Make's own model, one line per call.

    Pinned because the argv shape is load-bearing twice over. It must stay a
    SHELL invocation -- roster lines carry `||`, redirections and brace groups
    that only a shell understands -- and it must stay ONE line per call, since
    joining two would merge invocations the Makefile requires to be separate.
    """
    shard = _shard_module()
    captured: list[list[str]] = []

    def fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
        captured.append(list(argv))
        return subprocess.CompletedProcess(argv, 0)

    line = 'command -v npm >/dev/null 2>&1 || { echo "missing" >&2; exit 1; }'
    with mock.patch.object(shard.subprocess, "run", fake_run):
        shard._default_executor(line, cwd=REPO_ROOT, check=False)

    assert captured == [["sh", "-c", line]], captured
    # The command is one argv element, never split or concatenated.
    assert captured[0][2] == line
