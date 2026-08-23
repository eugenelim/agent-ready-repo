"""Construction test: collecting this repository's suite must not add a packaged
source tree to `sys.path`.

**The defect this exists to prevent.** `tools/repo/build_gate_chain.py` used to
run `sys.path.insert(0, <repo>/packages/agentbundle)` at module scope, for an
in-process use it never had. Two collected test modules import it
(`tools/test_build_gate_chain.py`, `tools/catalogue/tests/test_verify_host_checks.py`),
pytest imports every collected module before running any test, and `tools/` is
walked before `tests/` — so the insert landed before the first test ran. The
first `import agentbundle` after it then cached the WORKTREE copy in
`sys.modules`, and every later test in that process saw it.

The consequence is the dangerous direction: two roster tests FAILED when run on
their own and PASSED inside a combined `pytest tools/ tests/` run, at the same
commit. A suite whose result depends on file order cannot be trusted, and the
accident is invisible — nothing in either roster test mentions `sys.path`.

Be precise about which invocation was affected, because it is easy to get
wrong. `make test` never puts `tools/` and `tests/` in one process — `Makefile:394`
runs `tests/` alone and the `tools/` modules run in separate invocations — so
this module was never imported in the session that ran the roster tests there. What makes
`make test` green is the PYTHONPATH exported on `Makefile:11`. The leak masked a
combined `pytest tools/ tests/`, which is how the failure was originally
measured.

**Why growth, and why a count.** `pyproject.toml` declares
`[tool.pytest.ini_options] pythonpath`, so `packages/agentbundle` and
`packages/credbroker` are on `sys.path` from the start of every session — by
design, and that is the *declared* pin. Presence therefore proves nothing. What
the accident produced was an EXTRA occurrence: `list.insert` does not
de-duplicate, so an import-time insert of an already-present directory takes the
entry's count from one to two. So this compares the count of `packages/*`
entries per collector, before against after, and any increase is a leak.

**Why the session is collected as-configured.** An earlier draft ran the child
with the declared `pythonpath` reduced to `"."`, so that any `packages/*` entry
at all was evidence. That is a stronger detector and the wrong trade: `Makefile`
tells contributors not to install `agentbundle` or `credbroker`, so on the
documented developer setup those imports would fail at COLLECTION and the guard
would redden for a reason that has nothing to do with a leak. Collecting under
`pyproject.toml` alone cannot fail that way.

**The second invariant, which does not depend on counting.** A count catches an
added occurrence, but not a *reorder*: `sys.path.remove(p)` followed by
`sys.path.append(p)` — the "tidy my path" idiom — leaves every count identical
while demoting the worktree copy below `site-packages`, flipping resolution
exactly as the original defect did. Nor does a count see a shadowing directory
outside `packages/`. So the probe also records where the finder actually
resolves `agentbundle` and `credbroker`, at session start and again when
collection ends, and requires the two to agree. That is the property the counts
are a proxy for, asserted directly.

**Why measured rather than linted.** A static scan for `sys.path.insert` is an
enumeration, and enumerations leak: the mutation can be indirect, conditional,
computed, or three imports deep. Two greps in the original investigation pointed
at the wrong file for exactly that reason —
`tools/test_marketplace_envelope_parity.py:186` matches a `sys.path.insert` that
lives inside a raw string of *child* source and never runs in the parent. So
this collects the real suite in a child interpreter and reads the real
`sys.path`, attributing any growth to the collector that caused it.

**What it does not prove, stated plainly.**

- A *conditional* insert (`if p not in sys.path: sys.path.insert(...)`) of an
  already-declared path adds no occurrence and moves no resolution, so neither
  invariant reports it. It is not the defect above while the declared pin
  stands — but it would become one if that `pythonpath` declaration were dropped.
- Coverage starts at `pytest_sessionstart`. The `pythonpath` entries are applied
  before that, during `Config._preparse`, as is anything a rootdir `conftest.py`
  does — there is none today. Such a mutation would land in the baseline and in
  the session-start resolution, and be invisible to both checks.
- Only `agentbundle` and `credbroker` are watched for resolution, and only
  `<repo>/packages/*` entries are counted. A third package shadowed by an
  import-time mutation is not covered.
- `sys.path` and the finder are not the only channels. A module could assign
  into `sys.modules` directly, or install a `sys.meta_path` finder that answers
  identically at both sample points. Neither is observed here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Collected in a child interpreter, because the property under test is a
#: property of a whole pytest session and this process is already inside one.
#: No `-o` overrides: the child must resolve `pyproject.toml` exactly as
#: `make test` does, so that a leak is the only thing that can move the counts.
_COLLECT_CHILD = r"""
import importlib.util
import json
import pathlib
import sys
from collections import Counter

import pytest

ROOT = pathlib.Path(sys.argv[1]).resolve()
PACKAGES = ROOT / "packages"
WATCHED = ("agentbundle", "credbroker")


def _packaged_counts():
    counts = Counter()
    for entry in sys.path:
        if not entry:
            continue
        try:
            resolved = pathlib.Path(entry).resolve()
        except OSError:
            continue
        if resolved == PACKAGES or PACKAGES in resolved.parents:
            counts[str(resolved)] += 1
    return counts


def _resolutions():
    # Where the finder says each watched package lives, right now. `find_spec`
    # on a top-level name imports nothing; once something HAS imported it, the
    # spec comes from sys.modules — which is exactly what later tests get.
    origins = {}
    for name in WATCHED:
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError):
            origins[name] = "<unresolvable>"
            continue
        origins[name] = str(getattr(spec, "origin", None)) if spec else "<missing>"
    return origins


class Probe:
    def __init__(self):
        self.before = {}
        self.baseline = Counter()
        self.leaks = []
        self.errors = []
        self.seen = []
        self.collected = 0
        self.final = Counter()
        self.resolved_at_start = {}
        self.resolved_at_end = {}

    def pytest_sessionstart(self, session):
        # NOT __init__: the `pythonpath` ini option is applied during
        # `Config._preparse`, which runs after this object is constructed and
        # before this hook. Snapshotting any earlier baselines an empty sys.path
        # and makes every later count look like growth.
        self.baseline = _packaged_counts()
        self.resolved_at_start = _resolutions()

    def pytest_collectstart(self, collector):
        self.before[collector.nodeid] = _packaged_counts()

    def pytest_collectreport(self, report):
        self.seen.append(report.nodeid)
        if report.failed:
            self.errors.append(report.nodeid)
        before = self.before.pop(report.nodeid, None)
        if before is None:
            return
        after = _packaged_counts()
        # Union of keys, so a REMOVAL is attributed too — `sys.path.remove` is a
        # resolution change as surely as an insert is.
        moved = {
            p: [before.get(p, 0), after.get(p, 0)]
            for p in set(before) | set(after)
            if before.get(p, 0) != after.get(p, 0)
        }
        if not moved:
            return
        # pytest emits a directory's collectreport AFTER its children, so an
        # ancestor re-reports a descendant's change. Keep the leaf: drop this
        # entry only when an already-recorded DESCENDANT reported the identical
        # movement. Matching on the movement alone would also swallow a second,
        # genuine leak that happened to show the same before/after numbers.
        if any(
            leak["moved"] == moved
            and leak["nodeid"].startswith(report.nodeid + "/")
            for leak in self.leaks
        ):
            return
        self.leaks.append({"nodeid": report.nodeid, "moved": moved})

    def pytest_collection_finish(self, session):
        self.collected = len(session.items)
        self.final = _packaged_counts()
        self.resolved_at_end = _resolutions()


probe = Probe()
code = pytest.main(
    ["--collect-only", "-q", "-p", "no:cacheprovider",
     "--continue-on-collection-errors", "tools", "tests"],
    plugins=[probe],
)
sys.stdout.write(
    "\nPROBE_JSON "
    + json.dumps({
        "leaks": probe.leaks,
        "errors": probe.errors,
        "seen": probe.seen,
        "collected": probe.collected,
        "baseline": dict(probe.baseline),
        "final": dict(probe.final),
        "resolved_at_start": probe.resolved_at_start,
        "resolved_at_end": probe.resolved_at_end,
        "code": int(code),
    })
    + "\n"
)
"""

#: Generous floor, not a pinned inventory: the suite collected 1623 items when
#: this was written, and an exact count would redden on any legitimate add or
#: remove. This only has to be high enough that a collection that fell over
#: early cannot pass vacuously. The named carriers below are the real
#: anti-vacuity check; this floor is the backstop for everything else.
MINIMUM_COLLECTED = 1200

#: The two collected modules that import `tools/repo/build_gate_chain.py`, and so
#: the two that carried the original leak into the session. If neither is in the
#: collected set, this guard is watching a session that cannot exhibit the defect
#: it was built for, and a green result means nothing.
CARRIER_MODULES = (
    "tools/test_build_gate_chain.py",
    "tools/catalogue/tests/test_verify_host_checks.py",
)


def _collect_in_child() -> dict:
    """Run a collect-only pytest session in a child and return its probe report."""
    env = os.environ.copy()
    # `make` exports PYTHONPATH with both package directories on it (Makefile:11).
    # Inheriting it would put `packages/agentbundle` on the child's sys.path a
    # second time before pytest starts. That is harmless for a movement
    # comparison, but it would mean this guard measured one configuration under
    # `make` and a different one under a bare `pytest`. Dropping it makes both
    # invocations measure pyproject.toml alone.
    env.pop("PYTHONPATH", None)
    # `-n auto` would move every import into xdist workers, where none of the
    # probe's hooks observe it.
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", "-c", _COLLECT_CHILD, str(REPO_ROOT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        # Collection measures ~4s; the headroom is for a loaded machine, not for
        # a wedged child, which should report rather than stall `make test`.
        timeout=300,
        check=False,
    )
    marker = "\nPROBE_JSON "
    if marker not in completed.stdout:
        raise AssertionError(
            "the collect-only child produced no probe report "
            f"(rc={completed.returncode}):\n"
            f"--- stdout tail ---\n{completed.stdout[-4000:]}\n"
            f"--- stderr tail ---\n{completed.stderr[-4000:]}"
        )
    return json.loads(completed.stdout.rsplit(marker, 1)[1].splitlines()[0])


class ImportTimePathLeakTest(unittest.TestCase):
    """One collected session, four assertions — the control must be able to fail."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _collect_in_child()

    def _child_context(self) -> str:
        return f" (child rc={self.report['code']}, {self.report['collected']} items collected)"

    def test_collection_reaches_the_modules_that_carried_the_leak(self) -> None:
        """A collection that fell over early would pass the leak check vacuously."""
        self.assertEqual(
            self.report["errors"],
            [],
            "collection errors mean the leak check never reached those modules, "
            "so a clean result below would prove nothing" + self._child_context(),
        )
        seen = set(self.report["seen"])
        self.assertEqual(
            [m for m in CARRIER_MODULES if m not in seen],
            [],
            "the modules that import build_gate_chain were not collected, so this "
            "session cannot exhibit the defect this guard exists to catch"
            + self._child_context(),
        )
        self.assertGreaterEqual(
            int(self.report["collected"]),
            MINIMUM_COLLECTED,
            "far fewer items collected than this suite has — the probe did not "
            "run the session it claims to have run" + self._child_context(),
        )

    def test_the_declared_pin_is_what_puts_packages_on_sys_path(self) -> None:
        """Without a baseline entry, a movement comparison could never move."""
        self.assertTrue(
            self.report["baseline"],
            "no packages/* entry was on the child's sys.path before collection: "
            "pyproject.toml's [tool.pytest.ini_options] pythonpath is how this "
            "suite resolves agentbundle and credbroker, and without it this "
            "guard is comparing against nothing" + self._child_context(),
        )
        # Deliberately no "each entry appears exactly once" assertion. An editable
        # install pointing at THIS worktree is a supported state (see the
        # `Unblocks when` line on the register entry this guard closes), and in
        # setuptools' `compat` editable mode that writes a raw-path .pth, which
        # would make a baseline count of 2 legitimate.

    def test_no_collector_moves_a_packaged_source_tree_on_sys_path(self) -> None:
        """Attributed form: names the leaf collector, so the fix has an address."""
        leaks = self.report["leaks"]
        detail = "\n".join(
            f"  {leak['nodeid']} took {path} from {counts[0]} to {counts[1]}"
            for leak in leaks
            for path, counts in leak["moved"].items()
        )
        self.assertEqual(
            leaks,
            [],
            "importing these collectors changed the packaged source trees on "
            "sys.path. That silently changes which copy of agentbundle or "
            "credbroker every later test in the session imports, and makes the "
            "result depend on file order:\n" + detail + "\n"
            "Fix: put the path on a child's PYTHONPATH where it is actually "
            "needed (see build_gate_chain._agentbundle_env) instead of mutating "
            "this process's sys.path. pyproject.toml's "
            "[tool.pytest.ini_options] pythonpath is the declared pin for the suite.",
        )
        # Backstop for a movement no collect hook was open for — a plugin, or an
        # import that outlived the collector that triggered it.
        self.assertEqual(
            self.report["final"],
            self.report["baseline"],
            "the packages/* entries on sys.path differ from the baseline, but no "
            "collector was credited with changing them" + self._child_context(),
        )

    def test_collection_does_not_move_where_the_packages_resolve(self) -> None:
        """The property the counts are a proxy for, asserted directly.

        Catches a reorder (`remove` then `append`), which keeps every count equal
        while demoting the worktree copy below site-packages, and a shadowing
        directory outside `packages/` that a count would never see.
        """
        self.assertEqual(
            self.report["resolved_at_end"],
            self.report["resolved_at_start"],
            "collecting the suite changed where agentbundle or credbroker "
            "resolves. Every test collected after the change imports a different "
            "copy from the ones collected before it" + self._child_context(),
        )


if __name__ == "__main__":
    unittest.main()
