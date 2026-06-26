"""Multi-pack install pressure tests + cross-pack ``--force`` clobber pin
+ per-adapter coverage.

These tests exercise the canonical adopter flow at the *modern* per-IDE
projection (RFC-0012; ``emit_install_routes`` defaults to False under
the argparse parser). They are intentionally end-to-end against the
live ``packs/`` catalogue rather than synthetic fixtures because the
load-bearing invariant is *how the shipped packs compose*, not how a
hypothetical pack would.

Three concerns:

  1. **Pressure matrix.** Scenarios that pin multi-pack composition at
     both scopes: install ordering, accumulation in state.toml,
     dependency-rail enforcement, re-install refusal, orphan-recovery
     refusal, and user-scope analogues. The regression net for the
     claim *"installing core then governance refuses unless I use
     --force"*: if any future change breaks the canonical multi-pack
     flow on a clean repo, one of these fails.

  2. **Cross-pack ``--force`` invariant.** When pack B's install
     triggers orphan cleanup via ``--force``, only B's files may be
     unlinked. Pack A's state-tracked files must be byte-identical
     before and after — pinned in both directions (A's force / B
     intact, B's force / A intact). Each cross-pack test additionally
     spies on ``safety.scan_for_pack_artifacts`` to *prove* the
     orphan-cleanup branch fired with a non-empty result, so a
     regression that silently skips branch (c) cannot make the test
     pass vacuously.

  3. **Per-adapter coverage.** Every test in concerns (1) and (2) that
     touches an on-disk projection runs once per shipped adapter
     (``claude-code``, ``kiro``, ``codex``, ``copilot``) — projection
     layout differs per adapter (``.claude/`` vs ``.kiro/`` vs
     ``.agents/skills/`` vs ``.github/skills/``) and the
     orphan-recovery scanner's per-pack heuristic interacts
     differently with each shape. Per AGENTS.local.md § "Install-test
     coverage rule", install-handler tests must fan out across all
     four shipped adapters; adapter-specific gaps are pinned
     explicitly as their own tests rather than silently elided.

Per-adapter projection geometry:

  - Copilot's skill projection lands at ``.github/skills/<skill>/SKILL.md``
    (docs/specs/copilot-skills-and-web — first-class Agent Skills, was a flat
    ``.github/instructions/<skill>.instructions.md``). The per-pack scanner at
    ``safety.scan_for_pack_artifacts`` matches these by directory name, exactly
    like ``.claude/skills/<name>/`` etc., so copilot is no longer the odd one
    out: the orphan branch fires at copilot for both *core* (skills + hooks at
    ``.github/hooks/``) and *governance-extras* (skills-only). Copilot's
    ``allowed-prefixes.repo`` is now ``[.github/skills/, .github/agents/,
    .github/hooks/]``. Both Direction A (force install governance-extras) and
    Direction B (force install core) therefore run at all shipped adapters.

Catalogue source: the live ``packs/`` tree in this repo. ``core`` and
``governance-extras`` are the canonical repo-only pair (governance
depends on core); ``architect`` and ``atlassian`` are the canonical
user-scope pair (workspace-agnostic, default-scope=user).
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import tomllib
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Per-adapter projection geometry
# ---------------------------------------------------------------------------


def _shipped_adapters() -> tuple[str, ...]:
    """Derive the tuple of shipped adapter names from the live contract.

    ``_data/adapter.toml`` is the source of truth; this helper reads
    its ``[adapter.*]`` table set via ``scope.shipped_adapters_from_contract``.
    Tests parametrize over the returned tuple so adding a fifth adapter
    to the contract surfaces missing coverage as test-collection
    expansion, not as silent drift.
    """
    from agentbundle.scope import shipped_adapters_from_contract

    return shipped_adapters_from_contract()


_SHIPPED_ADAPTERS: tuple[str, ...] = _shipped_adapters()


# Adapters at which an orphan-scan over governance-extras's primitives
# (skills only — new-rfc, new-adr, update-conventions) finds something.
# Includes copilot since docs/specs/copilot-skills-and-web: its `skill`
# projection is now a first-class `.github/skills/<name>/` directory tree,
# which the per-pack scanner's directory heuristic matches by name exactly
# like every other adapter (was a flat `<primitive>.instructions.md` whose
# stem evaded the scanner — that asymmetry is retired). For *core* (which
# also ships hooks) the scanner fires at all adapters too.
_ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES: tuple[str, ...] = (
    "claude-code", "kiro", "codex", "cursor", "copilot", "gemini",
)


def _skill_path(adapter: str, skill_name: str) -> str:
    """Return the relative path where ``adapter`` projects skill ``skill_name``.

    Source of truth: ``packages/agentbundle/agentbundle/_data/adapter.toml``
    ``[[adapter.<name>.projection]]`` ``target-path`` for the skill primitive.
    The mapping is hand-mirrored here so a refactor that changes one half
    surfaces as a test failure rather than silent skip — the pinning is the
    point of per-adapter parametrization.
    """
    if adapter == "claude-code":
        return f".claude/skills/{skill_name}/SKILL.md"
    # RFC-0022 kiro-adapter-split: `kiro-ide` / `kiro-cli` both project skills
    # to `.kiro/skills/` like the retained `kiro` alias.
    if adapter in ("kiro", "kiro-ide", "kiro-cli"):
        return f".kiro/skills/{skill_name}/SKILL.md"
    if adapter == "codex":
        return f".agents/skills/{skill_name}/SKILL.md"
    if adapter == "copilot":
        # docs/specs/copilot-skills-and-web: first-class Agent Skills —
        # `.github/skills/<name>/SKILL.md` (was a flat `.instructions.md`).
        return f".github/skills/{skill_name}/SKILL.md"
    # RFC-0026 cursor-full-parity: cursor projects skills to `.cursor/skills/`.
    if adapter == "cursor":
        return f".cursor/skills/{skill_name}/SKILL.md"
    # RFC-0027 gemini-full-parity: gemini projects skills to `.gemini/skills/`.
    if adapter == "gemini":
        return f".gemini/skills/{skill_name}/SKILL.md"
    raise ValueError(f"unknown adapter: {adapter!r}")


# ---------------------------------------------------------------------------
# Test hygiene
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_home_and_caches(tmp_path, monkeypatch):
    """Pin ``$HOME`` to a per-test tmp dir AND reset install.py's
    once-per-process detection sets.

    Why HOME isolation runs for every test (not just user-scope):
    governance-extras declares ``[[pack.dependencies.required]]``, so
    installing it at any scope routes through the dependency gate,
    which unions ``repo_state ∪ user_state``. The user_state is
    loaded from ``Path('~').expanduser() / '.agentbundle/state.toml'``
    via ``scope.resolve_user_root``. Without HOME isolation the
    repo-scope tests read the developer's actual
    ``~/.agentbundle/state.toml`` — a dev with stale entries there
    can make the dependency-rail assertion misfire. Set HOME for
    every test, regardless of scope. User-scope tests override this
    with their own ``tmp_path / "home"`` so they can read back the
    resulting state file at a known path.

    Why the caches are cleared: ``install.py``'s
    ``_classify_pre_rfc0012_state`` short-circuits on the second call
    per ``(output_root, pack_name)`` per process (the
    ``_INBAND_DETECTION_SEEN`` set). Production ``agentbundle``
    invocations are short-lived processes so this resets naturally —
    test runners do not. The set's docstring explicitly names
    "test harness" as a case that MUST reset. Same shape for the
    ``_DROPPED_WARNING_SEEN`` set.
    """
    from agentbundle.commands import install

    home = tmp_path / "iso_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()
    yield
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _install_argv(argv: list[str]) -> tuple[int, str, str]:
    """Build a fully-defaulted argparse Namespace and run install.

    Using the argparse parser ensures every attribute the install
    handler inspects (``emit_install_routes``, ``adapter``,
    ``force_merge``, etc.) carries its CLI default. Building a bare
    ``argparse.Namespace`` from a dict picks up ``hasattr`` fallback
    paths inside install.py that don't match what an adopter would hit
    on the CLI — e.g. ``emit_install_routes`` falls through to the
    legacy dist-tree at repo scope when the attribute is absent.
    """
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def _install_pack_at_adapter(
    pack: str,
    adopter: Path,
    adapter: str,
    *,
    extra: list[str] | None = None,
) -> tuple[int, str, str]:
    """Run ``agentbundle install --pack <pack> --adapter <adapter>`` at repo scope."""
    argv = ["--pack", pack, "--adapter", adapter,
            "--output", str(adopter), str(REPO_ROOT)]
    if extra:
        argv = argv[:4] + extra + argv[4:]
    return _install_argv(argv)


def _state(adopter_or_home: Path, *, scope: str) -> dict[str, Any]:
    """Load and return the state TOML for the named scope.

    ``scope="repo"`` reads ``<adopter>/.agentbundle-state.toml``;
    ``scope="user"`` reads ``<home>/.agentbundle/state.toml``.
    Returns an empty dict if the file is absent.
    """
    if scope == "repo":
        path = adopter_or_home / ".agentbundle-state.toml"
    else:
        path = adopter_or_home / ".agentbundle" / "state.toml"
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _packs_in_state(state: dict[str, Any]) -> set[str]:
    return set(state.get("pack", {}).keys())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state_tracked_files(state: dict[str, Any], pack: str) -> dict[str, str]:
    """Return ``{relpath: recorded_sha}`` for ``pack``'s state-tracked files.

    The SHA recorded in state is computed at install.py as
    ``safety.sha256_bytes(content)`` over the bytes written to disk,
    so on-disk sha matches recorded sha at install time.

    v0.4 TOML shape: ``[pack.<name>.adapters.<adapter>.files]``.
    Unions across all adapter rows for the named pack.
    """
    pack_body = state.get("pack", {}).get(pack, {})
    adapters = pack_body.get("adapters", {})
    out: dict[str, str] = {}
    for _adapter, row in adapters.items():
        for rel, meta in row.get("files", {}).items():
            if rel not in out:  # first adapter wins on overlap
                out[rel] = meta.get("sha", "")
    return out


def _drop_pack_from_state(adopter: Path, pack_name: str) -> None:
    """Remove all ``[pack.<pack_name>.adapters.*]`` rows from on-disk state
    via the production load/dump roundtrip.

    Implemented through ``config.load_state`` + ``config.dump_state``
    rather than line-grep so the test does not depend on
    ``dump_state``'s exact serialization shape (multi-line tables,
    array-of-tables headers like ``[[pack.<name>.adapters.<a>.hook-wiring-owned]]``,
    blank-line conventions). A future change to the writer's emission
    order cannot silently break this helper.
    """
    from agentbundle.config import dump_state, load_state

    state_path = adopter / ".agentbundle-state.toml"
    state = load_state(state_path)
    # Remove all (pack_name, *) rows — v0.4 state is keyed by (name, adapter).
    keys_to_drop = [(n, a) for (n, a) in state.packs if n == pack_name]
    for key in keys_to_drop:
        del state.packs[key]
    state_path.write_text(dump_state(state), encoding="utf-8")


# ---------------------------------------------------------------------------
# Repo-scope pressure matrix (core + governance-extras), per adapter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter", _SHIPPED_ADAPTERS)
def test_install_core_then_governance_extras_accumulates_repo_state(
    tmp_path, adapter,
):
    """S1: install core, then governance-extras; state has both rows;
    both packs' files land at the adapter-specific projection path;
    the second install does NOT refuse and does NOT require --force.

    Parametrized over all four shipped adapters so a regression that
    breaks composition at one adapter (e.g. an adapter-specific
    refusal short-circuit) surfaces as a test failure scoped to that
    adapter, not as silent breakage at one of the four projections.
    """
    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc1, _, err1 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc1 == 0, f"core install at {adapter} failed: {err1}"

    rc2, _, err2 = _install_pack_at_adapter("governance-extras", adopter, adapter)
    assert rc2 == 0, (
        f"governance-extras install after core at {adapter} must succeed "
        f"without --force; stderr: {err2}"
    )

    state = _state(adopter, scope="repo")
    assert _packs_in_state(state) >= {"core", "governance-extras"}, (
        f"state.toml at {adapter} missing one of the packs after both "
        f"installs: {sorted(_packs_in_state(state))}"
    )

    # Adapter-specific spot-check: work-loop is core's load-bearing
    # skill; new-rfc is governance-extras's. The path depends on the
    # adapter's projection layout — sourced from _skill_path().
    work_loop_path = adopter / _skill_path(adapter, "work-loop")
    new_rfc_path = adopter / _skill_path(adapter, "new-rfc")
    assert work_loop_path.exists(), (
        f"core's work-loop skill missing at {adapter}'s expected path "
        f"{work_loop_path.relative_to(adopter)}"
    )
    assert new_rfc_path.exists(), (
        f"governance-extras's new-rfc skill missing at {adapter}'s "
        f"expected path {new_rfc_path.relative_to(adopter)}"
    )


@pytest.mark.parametrize("adapter", _SHIPPED_ADAPTERS)
def test_governance_extras_first_refuses_then_succeeds_after_core(
    tmp_path, adapter,
):
    """S2: governance-extras → core → governance-extras at every adapter.

    Pins the dependency rail (governance-extras requires core ^0.1).
    The dep gate consults state.toml (union of repo + user) and is
    adapter-agnostic, but running it at every adapter catches a
    regression where one adapter's resolver short-circuits before
    the gate (RFC-0012-style per-IDE projection edge cases).
    """
    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc1, _, err1 = _install_pack_at_adapter("governance-extras", adopter, adapter)
    assert rc1 != 0, (
        f"governance-extras must refuse without core in state at {adapter}"
    )
    assert "requires 'core'" in err1, (
        f"unexpected refusal message at {adapter}: {err1!r}"
    )

    rc2, _, err2 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc2 == 0, f"core install at {adapter} failed: {err2}"

    rc3, _, err3 = _install_pack_at_adapter("governance-extras", adopter, adapter)
    assert rc3 == 0, (
        f"governance-extras must succeed at {adapter} once core's state "
        f"row is present; stderr: {err3}"
    )


@pytest.mark.parametrize("adapter", _SHIPPED_ADAPTERS)
def test_reinstall_same_pack_repo_scope_refused(tmp_path, adapter):
    """S3: install core twice at every adapter → second attempt
    refuses with ``use 'upgrade' to change version``. ``--force`` does
    NOT bypass this case (RFC-0004 Step 4a). The refusal is
    state-driven, so it should hold at every adapter."""
    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc1, _, err1 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc1 == 0, f"first install at {adapter} failed: {err1}"

    rc2, _, err2 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc2 != 0
    assert "already installed at repo" in err2, (
        f"unexpected stderr at {adapter}: {err2!r}"
    )
    assert "use 'upgrade' to change version" in err2

    rc3, _, err3 = _install_pack_at_adapter(
        "core", adopter, adapter, extra=["--force"],
    )
    assert rc3 != 0, (
        f"--force must not bypass same-scope re-install refusal at {adapter}"
    )
    assert "already installed at repo" in err3


@pytest.mark.parametrize("adapter", _SHIPPED_ADAPTERS)
def test_lost_state_reinstall_over_projection_files_is_clean(tmp_path, adapter):
    """Issue #190: install core, delete state.toml, reinstall core → a CLEAN
    reinstall, NOT an orphan refusal, at every shipped adapter.

    The on-disk files are all in the current projection (byte-identical to what
    the first install wrote), so they are companion-protected / Tier-1, never
    misclassified as interrupted-install orphans. This pins spec
    `core-install-seed-delivery` AC4 across adapters.

    The orphan-recovery feature still fires for *genuine* non-projection crumbs
    — see `test_install_orphan_reshape.py` (install-level) and
    `test_copilot_orphan_scan_finds_skills_and_hooks` (scanner-level).
    Before issue #190 this scenario refused with a "prior install interrupted"
    message and `--force` would `unlink()` the adopter's files; that hostile
    behaviour is exactly what the fix removes.

    **Also pins the early-render ↔ Step-7 key-match invariant across adapters.**
    The orphan filter compares on-disk files against a projection relpath set
    rendered at Step-3c, which must stay byte-identical to the Step-7 render the
    first install wrote. If the two `_render_for_repo_scope` call sites ever
    desync (e.g. one gains a `state_adapter`/`--adapter` argument the other
    lacks), the relpaths stop matching and this lost-state reinstall would
    wrongly refuse as an orphan — failing here at the affected adapter. Do not
    delete this as "redundant" with the single-adapter orphan-reshape tests.
    """
    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc1, _, err1 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc1 == 0, f"first install at {adapter} failed: {err1}"

    state_path = adopter / ".agentbundle-state.toml"
    assert state_path.exists()
    state_path.unlink()

    # First install seeded the once-per-process detection cache;
    # without this clear the second install short-circuits before
    # reaching any of `_classify_pre_rfc0012_state`'s (a)/(b)/(c)
    # branches. In production each `agentbundle install` is a fresh
    # process so this happens for free.
    from agentbundle.commands import install as _install_mod
    _install_mod._clear_inband_detection_seen()

    rc2, _, err2 = _install_pack_at_adapter("core", adopter, adapter)
    assert rc2 == 0, (
        f"lost-state reinstall over byte-identical projection files must be a "
        f"clean reinstall at {adapter}, not a refusal; stderr: {err2!r}"
    )
    assert "orphan" not in err2.lower(), (
        f"reinstall over current-projection files must not be flagged as an "
        f"orphan at {adapter}; stderr: {err2!r}"
    )
    assert state_path.exists(), "the clean reinstall must rewrite state.toml"


def test_copilot_orphan_scan_finds_skills_and_hooks(tmp_path):
    """Copilot-specific pin: the per-pack scanner finds orphans under both
    ``.github/skills/`` (skill directory trees, matched by directory name)
    and ``.github/hooks/`` (hook bodies, matched by stem).

    docs/specs/copilot-skills-and-web flipped copilot's ``skill`` projection
    from a flat ``<primitive>.instructions.md`` (whose stem evaded the
    scanner) to a first-class ``.github/skills/<name>/SKILL.md`` directory
    tree — so the scanner now matches copilot skills by directory name, the
    same as every other adapter. This pin asserts that parity; if it ever
    regresses, ``_ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES`` (which now includes
    copilot) would also break.
    """
    from agentbundle import safety
    from agentbundle.commands import install as _install_mod

    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc1, _, err1 = _install_pack_at_adapter("core", adopter, "copilot")
    assert rc1 == 0, f"first install failed: {err1}"

    state_path = adopter / ".agentbundle-state.toml"
    state_path.unlink()

    _install_mod._clear_inband_detection_seen()

    # Direct-call the scanner with core's primitive set + copilot's current
    # repo-scope prefixes (v0.11: skills at `.github/skills/`, hook bodies at
    # `.github/hooks/`, agents at `.github/agents/`).
    pack_dir = REPO_ROOT / "packs" / "core"
    prefixes = [".github/skills/", ".github/agents/", ".github/hooks/"]
    orphans = safety.scan_for_pack_artifacts(
        adopter, prefixes, pack_dir=pack_dir, pack_name="core",
    )
    rels = sorted(p.relative_to(adopter).as_posix() for p in orphans)

    # Skills are now found (directory-name match), unlike the retired flat shape.
    skill_hits = [r for r in rels if r.startswith(".github/skills/")]
    assert skill_hits, (
        f"expected scanner to find core's skill dirs at copilot; got: {rels!r}"
    )
    # Hook bodies are found too.
    hook_hits = [r for r in rels if r.startswith(".github/hooks/")]
    assert hook_hits, (
        f"expected scanner to find core's hook files at copilot; got: {rels!r}"
    )


# ---------------------------------------------------------------------------
# User-scope pressure matrix (architect + atlassian)
# ---------------------------------------------------------------------------


def test_user_scope_multi_pack_accumulates_state(tmp_path, monkeypatch):
    """S5: install architect at user, then atlassian at user. Both
    packs default to user scope (workspace-agnostic). The user-scope
    state file accumulates both rows. User-scope adapter resolution is
    its own surface (RFC-0011 / RFC-0012's user-scope clauses); the
    install-handler tests in this module pin the repo-scope per-IDE
    multi-pack flow, not the user-scope adapter matrix."""
    adopter = tmp_path / "adopter"
    adopter.mkdir()
    # Override the autouse-fixture HOME with one we control by path
    # so we can read the resulting user state file.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc1, _, err1 = _install_argv(
        ["--pack", "architect", "--scope", "user",
         "--output", str(adopter), str(REPO_ROOT)]
    )
    assert rc1 == 0, f"architect install failed: {err1}"

    rc2, _, err2 = _install_argv(
        ["--pack", "atlassian", "--scope", "user",
         "--output", str(adopter), str(REPO_ROOT)]
    )
    assert rc2 == 0, (
        "atlassian install after architect must succeed; "
        f"stderr: {err2}"
    )

    user_state = _state(fake_home, scope="user")
    assert _packs_in_state(user_state) >= {"architect", "atlassian"}, (
        f"user state.toml missing one of the packs: "
        f"{sorted(_packs_in_state(user_state))}"
    )


def test_user_scope_reinstall_same_pack_refused(tmp_path, monkeypatch):
    """S6: install architect at user twice → second refuses with the
    same ``use 'upgrade' to change version`` line as repo scope."""
    adopter = tmp_path / "adopter"
    adopter.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc1, _, err1 = _install_argv(
        ["--pack", "architect", "--scope", "user",
         "--output", str(adopter), str(REPO_ROOT)]
    )
    assert rc1 == 0, f"first install failed: {err1}"

    rc2, _, err2 = _install_argv(
        ["--pack", "architect", "--scope", "user",
         "--output", str(adopter), str(REPO_ROOT)]
    )
    assert rc2 != 0
    assert "already installed at user" in err2
    assert "use 'upgrade' to change version" in err2


# ---------------------------------------------------------------------------
# CRITICAL: cross-pack ``--force`` invariant pin, per adapter
# ---------------------------------------------------------------------------


def _run_cross_pack_force_clobber_scenario(
    adopter: Path,
    monkeypatch,
    *,
    adapter_name: str,
    pre_installed: tuple[str, str],
    drop_and_force: str,
    protected: str,
) -> None:
    """Set up the cross-pack ``--force`` clobber scenario and assert
    invariants: install succeeds, the orphan branch fired with a
    non-empty result (positive signal — without it a regression that
    returns ``[]`` from the scanner would make the test pass
    vacuously), and every protected file is byte-equal before/after.

    Procedure (the same shape both invariant tests follow):

      1. Install both packs cleanly at the named adapter.
      2. Snapshot ``protected``'s state-tracked file SHAs.
      3. Drop ``drop_and_force``'s state row via ``dump_state``
         roundtrip (production loader/serialiser, so the helper does
         not depend on the exact on-disk byte shape).
      4. Spy on ``safety.scan_for_pack_artifacts`` so we can later
         assert the orphan branch fired with a non-empty result.
      5. Clear ``_INBAND_DETECTION_SEEN`` so detection actually fires.
      6. Install ``drop_and_force`` with ``--force`` at the same adapter.
      7. Assert: rc=0, the spy recorded a non-empty result for the
         ``drop_and_force`` pack, every protected file still exists
         with the same SHA.
    """
    from agentbundle import safety
    from agentbundle.commands import install as _install_mod

    pack_a, pack_b = pre_installed

    rc1, _, err1 = _install_pack_at_adapter(pack_a, adopter, adapter_name)
    assert rc1 == 0, f"{pack_a} install at {adapter_name} failed: {err1}"
    rc2, _, err2 = _install_pack_at_adapter(pack_b, adopter, adapter_name)
    assert rc2 == 0, f"{pack_b} install at {adapter_name} failed: {err2}"

    # Snapshot the protected pack's tracked files.
    state = _state(adopter, scope="repo")
    protected_files = _state_tracked_files(state, protected)
    assert protected_files, (
        f"{protected}'s state row at {adapter_name} carries no files; "
        f"test setup is wrong"
    )

    # Sanity: the two packs' state-tracked file sets do not overlap.
    # If a future catalogue change has them shipping the same on-disk
    # path, this test cannot pin the cross-pack invariant because
    # ownership is ambiguous (and path-jail would normally have caught
    # the collision at install-time write).
    other = pack_a if protected == pack_b else pack_b
    other_files = set(_state_tracked_files(state, other).keys())
    overlap = set(protected_files.keys()) & other_files
    assert not overlap, (
        f"catalogue packs {pack_a} and {pack_b} at {adapter_name} share "
        f"file paths: {sorted(overlap)} — different bug class"
    )

    # Pre-condition: state SHA matches on-disk SHA. install.py:788
    # records ``safety.sha256_bytes(content)`` over written bytes, so
    # the two are equal at install time. If they're not, the test
    # setup itself is wrong (mismatch is ambiguous downstream).
    for rel, recorded_sha in protected_files.items():
        on_disk = adopter / rel
        assert on_disk.exists(), (
            f"pre-condition: {rel} must exist on disk at {adapter_name}"
        )
        assert _sha256(on_disk) == recorded_sha, (
            f"pre-condition: {rel} sha mismatches state at {adapter_name} "
            f"— test setup is wrong"
        )

    # Drop the to-be-forced pack's state row via production roundtrip.
    _drop_pack_from_state(adopter, drop_and_force)
    post_state = _state(adopter, scope="repo")
    assert drop_and_force not in _packs_in_state(post_state)
    assert protected in _packs_in_state(post_state)

    # Spy on the scanner — capture (kwargs, result) for every call so
    # we can assert orphan cleanup actually ran with a non-empty list.
    calls: list[tuple[dict, list]] = []
    original_scan = safety.scan_for_pack_artifacts

    def _spy(root, allowed_prefixes, *, pack_dir=None, pack_name=None):
        result = original_scan(
            root, allowed_prefixes, pack_dir=pack_dir, pack_name=pack_name
        )
        calls.append(
            ({"pack_name": pack_name, "pack_dir": pack_dir}, list(result))
        )
        return result

    monkeypatch.setattr(safety, "scan_for_pack_artifacts", _spy)

    # Clear once-per-process detection cache so branch (c) re-runs.
    _install_mod._clear_inband_detection_seen()

    rc3, _, err3 = _install_pack_at_adapter(
        drop_and_force, adopter, adapter_name, extra=["--force"],
    )
    assert rc3 == 0, (
        f"{drop_and_force} --force install at {adapter_name} must succeed; "
        f"stderr: {err3}"
    )

    # POSITIVE SIGNAL: prove the orphan branch fired with a non-empty
    # result. Without this assertion, a regression that returns [] from
    # the scanner (or skips the call entirely) would let the test pass
    # vacuously — exactly the failure mode this test is supposed to
    # catch.
    matching = [
        (kwargs, result) for kwargs, result in calls
        if kwargs["pack_name"] == drop_and_force and result
    ]
    assert matching, (
        f"orphan-cleanup branch did not fire for {drop_and_force} at "
        f"{adapter_name}: scan_for_pack_artifacts was either not called "
        f"for this pack or returned []. Calls captured: "
        f"{[(k['pack_name'], len(r)) for k, r in calls]}"
    )

    # Post-condition: every protected file is still on disk with its
    # recorded SHA — ANY mismatch is the cross-pack clobber bug.
    missing = [
        rel for rel in protected_files
        if not (adopter / rel).exists()
    ]
    clobbered = [
        rel for rel, sha in protected_files.items()
        if (adopter / rel).exists() and _sha256(adopter / rel) != sha
    ]
    assert not missing and not clobbered, (
        f"cross-pack clobber detected at {adapter_name} after "
        f"{drop_and_force} --force install:\n"
        f"  missing (unlinked): {missing}\n"
        f"  sha-changed (overwritten): {clobbered}"
    )


@pytest.mark.parametrize("adapter_name", _ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES)
def test_force_orphan_cleanup_does_not_clobber_other_packs_files(
    tmp_path, monkeypatch, adapter_name,
):
    """Direction A, per adapter: governance-extras ``--force`` must
    not unlink any of core's state-tracked files. Runs at **every** shipped
    adapter including copilot (docs/specs/copilot-skills-and-web): copilot's
    skills now project as a `.github/skills/<name>/` directory tree that the
    scanner matches by name, so governance-extras (skills-only) is scannable at
    copilot — no longer the vacuous case the old flat `.instructions.md`
    projection created. The copilot scanner behaviour is pinned separately in
    ``test_copilot_orphan_scan_finds_skills_and_hooks``."""
    adopter = tmp_path / "adopter"
    adopter.mkdir()
    _run_cross_pack_force_clobber_scenario(
        adopter, monkeypatch,
        adapter_name=adapter_name,
        pre_installed=("core", "governance-extras"),
        drop_and_force="governance-extras",
        protected="core",
    )


@pytest.mark.parametrize("adapter_name", _SHIPPED_ADAPTERS)
def test_force_orphan_cleanup_reverse_direction_does_not_clobber(
    tmp_path, monkeypatch, adapter_name,
):
    """Direction B (symmetric), per adapter: core ``--force`` must
    not unlink any of governance-extras's state-tracked files.

    Runs at all four adapters — core ships hook files under
    ``tools/hooks/`` (a non-copilot-specific surface in every
    adapter's ``allowed-prefixes.repo``), and the scanner matches by
    stem against those hook primitive names at every adapter. So
    the orphan branch fires for core at copilot too, even though
    Direction A doesn't fire there.

    The scanner's per-pack scoping uses each pack's primitive_names
    set as the filter. A regression that mis-scopes name overlap in
    one direction (e.g. for the *smaller* primitive set) but not the
    other would slip past Direction A. The reverse case traverses the
    same code path with different inputs — adding it costs little and
    closes the asymmetric-coverage gap.
    """
    adopter = tmp_path / "adopter"
    adopter.mkdir()
    _run_cross_pack_force_clobber_scenario(
        adopter, monkeypatch,
        adapter_name=adapter_name,
        pre_installed=("core", "governance-extras"),
        drop_and_force="core",
        protected="governance-extras",
    )
