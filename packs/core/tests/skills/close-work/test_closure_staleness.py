"""T6 — staleness refresh: per-decision index freshness and stale-base refusal.

Covers AC-0021 and AC-0022 of ``docs/specs/closure-eligibility-check/``.

**AC-0021** — every descendant state a verdict rests on is resolved during the
decision that uses it.  No decision reuses a state, an index, or a verdict built
by an earlier decision.  Asserted by a call counter that reds when a cached set
is returned: the reader records how many times it is called; a second decision
that skips re-reading (because it returned a cached result) leaves the counter
at zero and the assertion fails.  The verdict also discriminates: after a
descendant's status is mutated from live to terminal, a fresh index returns
eligible while a cached index still returns not-eligible.

**AC-0022** — a closure decision refuses with ``stale-base`` when HEAD is not
current against the merge target, with ``freshness-indeterminate`` when the
check cannot be performed, and does not refuse on either ground when the base
is current.  All three arms are exercised; a refusal-only implementation that
never proceeds fails the fresh arm.

Three failure shapes deliberately avoided:

1. *Seams-only, production path dead.*  ``test_ac0022_real_git_repo_does_not_refuse``
   calls ``check_ancestor_closure`` with no ``_freshness_checker`` argument
   against a ``tmp_path`` root that is initialised as a real git repository (via
   ``git init``).  ``_make_default_freshness_checker`` runs, detects no tracking
   branch, and returns ``True`` (fresh — nothing to be stale against); the
   decision then proceeds to ``ClosureEligible``.  The production path is reached
   with a genuine git root, not a synthetic fixture.

2. *A differential that does not discriminate.*  AC-0021's test uses a mutable
   store: if the module had cached the descendant set, the second verdict would
   be unchanged and the test would fail.  AC-0022's three arms are separate tests;
   any single arm can be satisfied by an implementation that always refuses or
   always proceeds.

3. *Indeterminate treated as fresh.*  ``test_ac0022_indeterminate_refuses``
   injects ``lambda: None`` and asserts ``ClosureRefuse`` with
   ``"freshness-indeterminate"`` in the reason.  A fail-open implementation that
   maps ``None`` to ``True`` (fresh) returns ``ClosureEligible`` and reds here.

Module loaded under ``"closure_index__staleness_t6"`` to isolate this suite from
the T2–T5 sys.modules entries.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# ── Module loader ─────────────────────────────────────────────────────────────

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)

# Literal paths: the pack-boundary lint cannot prove a computed join stays
# inside the owning pack, and it is right not to try.
_MODULE_PATHS = {
    "closure_index": _SCRIPTS / "closure_index.py",
    "closure_terminality": _SCRIPTS / "closure_terminality.py",
}


def _load(name: str, key: str):
    """Load a close-work script by absolute path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, _MODULE_PATHS[name])
    assert spec and spec.loader, f"no module at {_MODULE_PATHS[name]}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index", "closure_index__staleness_t6")

# ── Fixture helpers ───────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"


def _intent(
    slug: str,
    status: str = "Accepted",
    decomposed: str | None = None,
    parent: str | None = None,
) -> str:
    """Build a minimal intent preamble string."""
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-09-01 {decomposed}")
    lines.append("")
    return "\n".join(lines)


# ── AC-0021: each decision builds a fresh index ───────────────────────────────


def test_ac0021_second_decision_sees_mutated_status() -> None:
    """AC-0021: a second decision re-reads inputs and sees a mutated status.

    The mutable store supplies the filesystem.  Between decisions, a descendant's
    status changes from live (Accepted) to terminal (Fulfilled).  A call counter
    tracks reader invocations for the second decision:

    - If the module returned a cached set, the reader is never called for the
      second decision (counter stays at zero) — assertion fails.
    - If the module built a fresh index, the reader is called at least once
      (counter is positive) — and the verdict reflects the mutation.

    Both the counter assertion and the verdict assertion are required: the counter
    proves re-reading occurred; the verdict proves the new value was used.
    """
    ancestor_path = INTENTS_DIR / "ancestor.md"
    child_path = INTENTS_DIR / "child.md"

    # Mutable dict — we replace values between decisions.
    store: dict[Path, str] = {
        ancestor_path: _intent("ancestor", status="Accepted", decomposed="children"),
        child_path: _intent("child", status="Accepted", parent="ancestor"),
    }

    # Call counter — reset between decisions to measure only the second call's reads.
    call_count: list[int] = [0]

    def reader(path: Path) -> str:
        """Count reads and return content from the mutable store."""
        if path in store:
            call_count[0] += 1
            return store[path]
        return ""

    def dir_lister(d: Path) -> list[Path]:
        return [p for p in store if p.parent == d]

    # Decision 1: child status is Accepted (live) → not-eligible.
    verdict1 = ci.check_ancestor_closure(
        "ancestor",
        "Accepted",
        "children",
        ROOT,
        _reader=reader,
        _dir_lister=dir_lister,
        _freshness_checker=lambda: True,  # fresh — isolate the freshness seam
    )
    assert isinstance(verdict1, ci.ClosureNotEligible), (
        f"Decision 1 expected ClosureNotEligible, got {verdict1!r}"
    )

    # Mutate: child is now terminal.
    store[child_path] = _intent("child", status="Fulfilled", parent="ancestor")
    # Reset the counter so we measure only decision 2's reads.
    call_count[0] = 0

    # Decision 2: must re-read the store and see the updated status.
    verdict2 = ci.check_ancestor_closure(
        "ancestor",
        "Accepted",
        "children",
        ROOT,
        _reader=reader,
        _dir_lister=dir_lister,
        _freshness_checker=lambda: True,
    )

    # Counter assertion: the reader must have been called — no caching occurred.
    assert call_count[0] > 0, (
        f"Reader was not called during decision 2 (count={call_count[0]}). "
        "The module appears to have returned a cached descendant set from decision 1 "
        "rather than building a fresh index. AC-0021 requires every decision to "
        "re-resolve all inputs."
    )

    # Verdict assertion: the new status must be reflected.
    assert isinstance(verdict2, ci.ClosureEligible), (
        f"Decision 2 returned {verdict2!r}; expected ClosureEligible after "
        f"mutating child to Fulfilled.  "
        f"(reader call count for decision 2: {call_count[0]}; "
        f"decision 1 returned {verdict1!r})"
    )


# ── AC-0022: stale-base refusal and its paired positive ──────────────────────


def test_ac0022_stale_base_refuses() -> None:
    """AC-0022 (stale arm): a stale freshness check produces ClosureRefuse(stale-base).

    The descendant closure would be eligible, so the only reason for refusal is
    the stale base — the test is not contaminated by other refusal grounds.
    """
    ancestor_path = INTENTS_DIR / "ancestor.md"
    child_path = INTENTS_DIR / "child.md"
    store: dict[Path, str] = {
        ancestor_path: _intent("ancestor", status="Accepted", decomposed="children"),
        child_path: _intent("child", status="Fulfilled", parent="ancestor"),  # terminal
    }

    verdict = ci.check_ancestor_closure(
        "ancestor",
        "Accepted",
        "children",
        ROOT,
        _reader=lambda p: store.get(p, ""),
        _dir_lister=lambda d: [p for p in store if p.parent == d],
        _freshness_checker=lambda: False,  # stale
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"Expected ClosureRefuse on stale base, got {verdict!r}"
    )
    assert "stale-base" in verdict.reason, (
        f"ClosureRefuse reason does not contain 'stale-base': {verdict.reason!r}"
    )


def test_ac0022_current_base_does_not_refuse_on_staleness() -> None:
    """AC-0022 (fresh arm): a current base does not produce a stale-base refusal.

    This arm is required: an implementation that refuses everything satisfies
    the stale arm alone but fails here.  The same descendant fixture as the stale
    arm is used — all descendants terminal — so the only expected verdict
    difference between the two arms is the staleness reason.
    """
    ancestor_path = INTENTS_DIR / "ancestor.md"
    child_path = INTENTS_DIR / "child.md"
    store: dict[Path, str] = {
        ancestor_path: _intent("ancestor", status="Accepted", decomposed="children"),
        child_path: _intent("child", status="Fulfilled", parent="ancestor"),  # terminal
    }

    verdict = ci.check_ancestor_closure(
        "ancestor",
        "Accepted",
        "children",
        ROOT,
        _reader=lambda p: store.get(p, ""),
        _dir_lister=lambda d: [p for p in store if p.parent == d],
        _freshness_checker=lambda: True,  # fresh
    )
    # Must not be a stale-base refusal.
    assert not (
        isinstance(verdict, ci.ClosureRefuse) and "stale-base" in verdict.reason
    ), (
        f"Fresh base produced a stale-base refusal: {verdict!r}"
    )
    # With all descendants terminal and no other refusal ground, expect eligible.
    assert isinstance(verdict, ci.ClosureEligible), (
        f"Expected ClosureEligible on fresh base with all-terminal closure, "
        f"got {verdict!r}"
    )


# ── AC-0022: indeterminate refuses ───────────────────────────────────────────


def test_ac0022_indeterminate_refuses() -> None:
    """AC-0022 (indeterminate arm): a None freshness result refuses with freshness-indeterminate.

    ``None`` represents the indeterminate case — git unavailable, timeout, or root
    is not a git repository.  The closure decision authorises a terminal write, so
    "unable to determine" must block rather than pass through.

    The stale arm uses ``lambda: False`` (which alone cannot confirm the check
    discriminates rather than always refusing); this arm confirms that the reason
    string distinguishes indeterminate from stale.  A fail-open implementation
    that maps ``None`` to ``True`` (fresh) returns ``ClosureEligible`` and reds.
    """
    ancestor_path = INTENTS_DIR / "ancestor.md"
    child_path = INTENTS_DIR / "child.md"
    store: dict[Path, str] = {
        ancestor_path: _intent("ancestor", status="Accepted", decomposed="children"),
        child_path: _intent("child", status="Fulfilled", parent="ancestor"),  # terminal
    }

    verdict = ci.check_ancestor_closure(
        "ancestor",
        "Accepted",
        "children",
        ROOT,
        _reader=lambda p: store.get(p, ""),
        _dir_lister=lambda d: [p for p in store if p.parent == d],
        _freshness_checker=lambda: None,  # indeterminate
    )
    assert isinstance(verdict, ci.ClosureRefuse), (
        f"Expected ClosureRefuse on indeterminate freshness, got {verdict!r}"
    )
    assert "freshness-indeterminate" in verdict.reason, (
        f"ClosureRefuse reason should contain 'freshness-indeterminate' for the "
        f"indeterminate case; got: {verdict.reason!r}"
    )
    # Must not say stale-base — the two cases have different remedies.
    assert "stale-base" not in verdict.reason, (
        f"Indeterminate refusal reason must not say 'stale-base': {verdict.reason!r}"
    )


# ── AC-0022 real-path test: production default runs against a real git repo ──


def test_ac0022_real_git_repo_does_not_refuse(tmp_path: Path) -> None:
    """AC-0022 (real path): a current HEAD in a real git repo does not produce a freshness refusal.

    ``tmp_path`` is initialised as a git repository via ``git init``.  No tracking
    branch is configured, so ``_make_default_freshness_checker`` returns ``True``
    (fresh — no upstream to be stale against).  No ``_freshness_checker`` is
    injected, so the production default executes its full three-step logic.

    This guards against failure shape 1: a seams-only test that leaves the
    production freshness path unreached.  A ``tmp_path`` root that is NOT a git
    repository would cause the checker to return ``None`` (indeterminate) under
    the corrected logic, and would refuse — so this test would also red if the
    production path were not exercising the real git check.
    """
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            pytest.skip("git init failed — git may not be available")
    except FileNotFoundError:
        pytest.skip("git not found in PATH")

    intents_dir = tmp_path / "docs" / "product" / "intents"
    intents_dir.mkdir(parents=True)

    # A simple closed-empty ancestor — no descendants expected.
    (intents_dir / "simple-ancestor.md").write_text(
        "- **Slug:** simple-ancestor\n"
        "- **Status:** Accepted\n"
        "- **Decomposed:** 2026-09-01 closed-empty\n"
    )

    # No _freshness_checker injected → production default runs against the real git repo.
    # No tracking branch → returns True (fresh) → decision proceeds.
    verdict = ci.check_ancestor_closure(
        "simple-ancestor",
        "Accepted",
        "closed-empty",
        tmp_path,
        # _reader and _dir_lister omitted → production defaults run too.
    )
    # No tracking branch in the git-init'd tmp_path → fresh → no freshness refusal.
    assert not (
        isinstance(verdict, ci.ClosureRefuse)
        and (
            "stale-base" in verdict.reason
            or "freshness-indeterminate" in verdict.reason
        )
    ), (
        f"Unexpected freshness refusal against a git-init'd repo with no tracking "
        f"branch: {verdict!r}"
    )
    # closed-empty with empty descendant set → eligible.
    assert isinstance(verdict, ci.ClosureEligible), (
        f"Expected ClosureEligible for closed-empty ancestor with no descendants "
        f"in a current git repo, got {verdict!r}"
    )


# ── The default checker's own verdict, not just the caller's handling of it ───
#
# The tests above drive indeterminate and stale through an injected
# ``_freshness_checker``, which proves ``check_ancestor_closure`` *handles*
# each result. They say nothing about whether the default checker *produces*
# the right one. That gap was measured: reverting
# ``_make_default_freshness_checker``'s three ``return None`` statements to
# ``return True`` restores a fail-open default — a root that is not a git
# repository reports fresh — and every other test in this pack still passes.
# These two cases are the regression guard for that.


def test_default_checker_is_indeterminate_on_a_non_repository_root(
    tmp_path: Path,
) -> None:
    """Unable to determine is not the same as determined fresh.

    A closure decision authorises a terminal write, so the direction that
    refuses to authorise is the safe one — the same reason an unrecognised
    descendant status counts as live. The shipped condition this mirrors,
    ``work-loop``'s ``check-base-freshness.py``, surfaces rather than passes
    when it cannot check.
    """
    assert ci._make_default_freshness_checker(tmp_path)() is None


def test_default_checker_is_not_indeterminate_on_a_real_repository(
    tmp_path: Path,
) -> None:
    """The paired positive arm.

    Without it, a checker that returned ``None`` unconditionally would satisfy
    the case above while making every closure decision refuse.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-q", "--allow-empty", "-m", "base"],
        cwd=tmp_path, check=True,
    )
    assert ci._make_default_freshness_checker(tmp_path)() is not None
