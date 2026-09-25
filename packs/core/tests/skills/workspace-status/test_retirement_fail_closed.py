"""Tests for fail-closed reading and confinement — T0c (TDD).

Verification mode: TDD (red written first, then green).
Spec:  docs/specs/spec-retirement-eligibility/spec.md  §§ Fail closed, Confinement
Plan:  docs/specs/spec-retirement-eligibility/plan.md  § T0c

T0c test cases from the plan task body
---------------------------------------
1.  Each substrate type (TOML, JSON, text, spec body) made unreadable: named
    refusal produced; every candidate whose blockers depend on it is suppressed.
2.  Each substrate type made unparseable: named refusal + suppression.
3.  Path ``../../../../etc/passwd``: refused ``path-escapes-root``;
    ``_OPEN_FUNC`` never called (reader stub proves no file was opened).
4.  Symlinked directory component: refused ``path-escapes-root``;
    ``_OPEN_FUNC`` never called.
5.  A valid path routes through ``confined_read_bytes``; removing that call
    turns the confinement cases red.
6.  Suppression is corpus-level: a candidate with no scan blockers is still
    suppressed when its evidence corpus cannot be read.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------

_PACK_ROOT = Path(__file__).resolve().parents[3]
_RETIREMENT_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_retirement.py"
)

_MODULE_NAME = "workspace_status_retirement_t0c"


def _load_retirement():
    """Load workspace_status_retirement under a unique name to avoid cache collisions."""
    if _MODULE_NAME in sys.modules:
        return sys.modules[_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _RETIREMENT_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_RETIREMENT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def _fresh_candidates(*slugs: str) -> dict[str, dict]:
    """Return a candidates dict where every slug starts eligible with no blockers."""
    return {slug: {"eligible": True, "blockers": []} for slug in slugs}


# ---------------------------------------------------------------------------
# Group 1: Unreadable substrate → named refusal + candidates suppressed
# ---------------------------------------------------------------------------

class TestUnreadableSubstrate:
    """Each substrate type made unreadable produces a named refusal and suppression.

    Spec § Fail closed:
    'A refusal naming any member of a corpus suppresses the eligibility of
    every candidate the blocker over that corpus is evaluated over, whether
    or not that candidate carries any blocker.'
    'A suppressed candidate is emitted carrying the blocker evidence-unread.'
    """

    @pytest.mark.skipif(
        not hasattr(os, "getuid") or os.getuid() == 0,
        reason="chmod tests require a non-root POSIX environment",
    )
    def test_toml_unreadable_suppresses_candidates(self, tmp_path: Path) -> None:
        """workspace.toml unreadable → input-unreadable refusal + candidate suppressed."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        ws = root / "workspace.toml"
        ws.write_text("[backlog]\n")
        ws.chmod(0o000)

        candidates = _fresh_candidates("myspec")
        try:
            result = mod.read_toml_substrate(root, "workspace.toml", candidates)
        finally:
            ws.chmod(0o644)

        assert result is None, "Unreadable TOML substrate must return None"
        assert candidates["myspec"]["eligible"] is False, (
            "Suppressed candidate must not be eligible"
        )
        assert "evidence-unread" in candidates["myspec"]["blockers"], (
            "Suppressed candidate must carry evidence-unread blocker"
        )

    @pytest.mark.skipif(
        not hasattr(os, "getuid") or os.getuid() == 0,
        reason="chmod tests require a non-root POSIX environment",
    )
    def test_json_unreadable_suppresses_candidates(self, tmp_path: Path) -> None:
        """A JSON substrate (contract with x-spec) unreadable → input-unreadable + suppression."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        f = root / "contract.json"
        f.write_text('{"x-spec": "docs/specs/myspec"}')
        f.chmod(0o000)

        candidates = _fresh_candidates("myspec")
        try:
            result = mod.read_json_substrate(root, "contract.json", candidates)
        finally:
            f.chmod(0o644)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    @pytest.mark.skipif(
        not hasattr(os, "getuid") or os.getuid() == 0,
        reason="chmod tests require a non-root POSIX environment",
    )
    def test_spec_body_unreadable_suppresses_candidate(self, tmp_path: Path) -> None:
        """Spec body unreadable → spec-unreadable refusal code + candidate suppressed.

        The refusal code for a spec body is spec-unreadable, not input-unreadable.
        """
        mod = _load_retirement()
        root = tmp_path / "repo"
        (root / "docs" / "specs" / "myspec").mkdir(parents=True)
        spec_file = root / "docs" / "specs" / "myspec" / "spec.md"
        spec_file.write_text("# Spec\n- **Status:** Shipped\n")
        spec_file.chmod(0o000)

        candidates = _fresh_candidates("myspec")
        try:
            result = mod.read_text_substrate(
                root,
                "docs/specs/myspec/spec.md",
                candidates,
                spec_body=True,
            )
        finally:
            spec_file.chmod(0o644)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    @pytest.mark.skipif(
        not hasattr(os, "getuid") or os.getuid() == 0,
        reason="chmod tests require a non-root POSIX environment",
    )
    def test_text_unreadable_suppresses_candidates(self, tmp_path: Path) -> None:
        """A text substrate (e.g. brief body) unreadable → input-unreadable + suppression."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        brief_dir = root / "docs" / "product" / "briefs"
        brief_dir.mkdir(parents=True)
        brief = brief_dir / "mybrief.md"
        brief.write_text("# Brief\n")
        brief.chmod(0o000)

        candidates = _fresh_candidates("myspec")
        try:
            result = mod.read_text_substrate(
                root, "docs/product/briefs/mybrief.md", candidates
            )
        finally:
            brief.chmod(0o644)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    @pytest.mark.skipif(
        not hasattr(os, "getuid") or os.getuid() == 0,
        reason="chmod tests require a non-root POSIX environment",
    )
    def test_protected_manifest_unreadable_suppresses_candidates(
        self, tmp_path: Path
    ) -> None:
        """The protected-directory manifest unreadable → input-unreadable + suppression."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        manifest = root / ".workspace-prune-protected.toml"
        manifest.write_text("[protected]\npaths = []\n")
        manifest.chmod(0o000)

        candidates = _fresh_candidates("myspec")
        try:
            result = mod.read_toml_substrate(
                root, ".workspace-prune-protected.toml", candidates
            )
        finally:
            manifest.chmod(0o644)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]


# ---------------------------------------------------------------------------
# Group 2: Unparseable substrate → input-unparseable refusal + suppression
# ---------------------------------------------------------------------------

class TestUnparseableSubstrate:
    """Each substrate type made unparseable produces input-unparseable and suppression.

    Spec § Fail closed:
    'An input that reads but cannot be parsed is refused as input-unparseable.'
    """

    def test_toml_unparseable_suppresses_candidates(self, tmp_path: Path) -> None:
        """workspace.toml with invalid TOML → input-unparseable + candidate suppressed."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        (root / "workspace.toml").write_bytes(b"[[[not valid toml")

        candidates = _fresh_candidates("myspec")
        result = mod.read_toml_substrate(root, "workspace.toml", candidates)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    def test_json_unparseable_suppresses_candidates(self, tmp_path: Path) -> None:
        """A JSON substrate with invalid JSON → input-unparseable + suppression."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        (root / "contract.json").write_bytes(b"{not valid json")

        candidates = _fresh_candidates("myspec")
        result = mod.read_json_substrate(root, "contract.json", candidates)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    def test_spec_body_invalid_utf8_suppresses_candidate(self, tmp_path: Path) -> None:
        """A spec body with invalid UTF-8 → input-unparseable + candidate suppressed."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        (root / "docs" / "specs" / "myspec").mkdir(parents=True)
        (root / "docs" / "specs" / "myspec" / "spec.md").write_bytes(
            b"# Spec\n\xff\xfe invalid utf-8 sequence"
        )

        candidates = _fresh_candidates("myspec")
        result = mod.read_text_substrate(
            root,
            "docs/specs/myspec/spec.md",
            candidates,
            spec_body=True,
        )

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]

    def test_text_invalid_utf8_suppresses_candidates(self, tmp_path: Path) -> None:
        """A text substrate with invalid UTF-8 → input-unparseable + suppression."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        (root / "brief.md").write_bytes(b"# Brief\n\xff\xfe")

        candidates = _fresh_candidates("myspec")
        result = mod.read_text_substrate(root, "brief.md", candidates)

        assert result is None
        assert candidates["myspec"]["eligible"] is False
        assert "evidence-unread" in candidates["myspec"]["blockers"]


# ---------------------------------------------------------------------------
# Group 3 & 4: Confinement — asserted by absence of the read (reader stub)
# ---------------------------------------------------------------------------

class TestConfinement:
    """Path-escape and symlink cases asserted by the absence of the read.

    Spec § Confinement:
    'A path derived from repository content that resolves outside the repository
    root is refused as path-escapes-root and is not read.'
    'A path reached through a symlink, junction, or reparse point is refused as
    path-escapes-root and is not read.'

    The reader stub (_OPEN_FUNC) fails the test if called, proving the refusal
    is produced before any file is opened — not merely that a refusal appeared.
    """

    def test_escaping_path_refused_before_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A path containing .. components is refused path-escapes-root without opening.

        _OPEN_FUNC is stubbed to fail if called; if the stub fires, the path
        validation did not stop the open.  If the stub never fires, the path was
        rejected at step 1 (format check) without any OS call.
        """
        mod = _load_retirement()

        def fail_if_opened(*args: object, **kwargs: object) -> int:
            pytest.fail(
                "_OPEN_FUNC must not be called for a path that escapes the root. "
                "If this fires, the path traversal check failed to stop the open."
            )

        monkeypatch.setattr(mod, "_OPEN_FUNC", fail_if_opened)

        # A slug constructed from a needs value that traverses outside the root.
        escaping_path = "docs/specs/../../../../etc/passwd/spec.md"

        with pytest.raises(mod.ConfinementRefusal) as exc_info:
            mod.confined_read_bytes(tmp_path, escaping_path)

        assert exc_info.value.code == "path-escapes-root", (
            f"Expected path-escapes-root, got {exc_info.value.code!r}. "
            "A traversing path must be refused before any OS call."
        )

    def test_symlinked_component_refused_before_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A path through a symlink component is refused path-escapes-root without opening.

        The component walk (step 2) detects the symlink via lstat() before
        any open().  _OPEN_FUNC is stubbed to fail if called.
        """
        mod = _load_retirement()

        root = tmp_path / "repo"
        root.mkdir()
        (root / "docs" / "specs").mkdir(parents=True)
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        # Make docs/specs/evil-spec a symlink pointing outside the root.
        (root / "docs" / "specs" / "evil-spec").symlink_to(outside_dir)

        def fail_if_opened(*args: object, **kwargs: object) -> int:
            pytest.fail(
                "_OPEN_FUNC must not be called for a path whose component is "
                "a symlink.  If this fires, the component walk did not stop "
                "the open before the symlink."
            )

        monkeypatch.setattr(mod, "_OPEN_FUNC", fail_if_opened)

        with pytest.raises(mod.ConfinementRefusal) as exc_info:
            mod.confined_read_bytes(root, "docs/specs/evil-spec/spec.md")

        assert exc_info.value.code == "path-escapes-root", (
            f"Expected path-escapes-root, got {exc_info.value.code!r}. "
            "A symlinked path component must be refused before any open()."
        )

    def test_valid_path_routes_through_confined_read_bytes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A valid, readable path routes through confined_read_bytes successfully.

        Verifies 'every repository read routes through the skill's own
        confinement helper': removing confined_read_bytes from the pipeline
        would leave the path-escape and symlink tests able to reach open()
        unchecked, turning those cases red.
        """
        mod = _load_retirement()

        root = tmp_path / "repo"
        root.mkdir()
        (root / "workspace.toml").write_text("[backlog]\n")

        calls: list[str] = []
        original = mod.confined_read_bytes

        def tracking_reader(
            r: Path, p: str, **kw: object
        ) -> bytes:
            calls.append(p)
            return original(r, p, **kw)

        monkeypatch.setattr(mod, "confined_read_bytes", tracking_reader)

        candidates = _fresh_candidates("myspec")
        result = mod.read_toml_substrate(root, "workspace.toml", candidates)

        assert result is not None, "A valid TOML file must be read successfully"
        assert "workspace.toml" in calls, (
            "read_toml_substrate must route through confined_read_bytes"
        )


# ---------------------------------------------------------------------------
# Group 5: Corpus-level suppression — not blocker-level
# ---------------------------------------------------------------------------

class TestCorpusSuppression:
    """Suppression is corpus-level: keying on produced blockers suppresses nothing.

    Spec § Fail closed:
    'Suppression is therefore a property of the scan, never of the blockers the
    scan happened to yield: an unread input produces no blockers, so keying
    suppression on the blockers it produced suppresses nothing.'
    """

    def test_apply_refusals_suppresses_all_named_candidates(
        self, tmp_path: Path
    ) -> None:
        """apply_refusals marks every named slug not-eligible with evidence-unread."""
        mod = _load_retirement()

        candidates = _fresh_candidates("spec-a", "spec-b")
        refusals = [
            mod.Refusal(
                code="input-unreadable",
                path="workspace.toml",
                suppresses=["spec-a", "spec-b"],
            )
        ]
        mod.apply_refusals(candidates, refusals)

        for slug in ("spec-a", "spec-b"):
            assert candidates[slug]["eligible"] is False, (
                f"{slug} must be marked not-eligible after suppression"
            )
            assert "evidence-unread" in candidates[slug]["blockers"], (
                f"{slug} must carry evidence-unread after suppression"
            )

    def test_candidate_not_named_in_suppresses_remains_eligible(
        self, tmp_path: Path
    ) -> None:
        """A refusal only suppresses the slugs it names; others stay eligible."""
        mod = _load_retirement()

        candidates = _fresh_candidates("spec-a", "spec-b")
        mod.apply_refusals(
            candidates,
            [
                mod.Refusal(
                    code="input-unreadable",
                    path="workspace.toml",
                    suppresses=["spec-a"],
                )
            ],
        )

        assert candidates["spec-a"]["eligible"] is False
        assert "evidence-unread" in candidates["spec-a"]["blockers"]
        assert candidates["spec-b"]["eligible"] is True, (
            "spec-b must remain eligible: it was not named in the refusal"
        )
        assert "evidence-unread" not in candidates["spec-b"]["blockers"]

    def test_candidate_with_no_blockers_is_suppressed_when_corpus_unread(
        self, tmp_path: Path
    ) -> None:
        """A clean candidate (no scan blockers) is suppressed by corpus-level refusal.

        This is the core property: a candidate that would have no blockers from
        a scan still receives evidence-unread when the corpus cannot be read.
        Keying on scan blockers would suppress nothing here, because an unread
        corpus produces no scan blockers.
        """
        mod = _load_retirement()

        root = tmp_path / "repo"
        root.mkdir()
        ws = root / "workspace.toml"
        ws.write_bytes(b"[[[not valid toml")

        # clean-spec has NO blockers; it would be eligible if the corpus were read.
        candidates = _fresh_candidates("clean-spec")
        result = mod.read_toml_substrate(root, "workspace.toml", candidates)

        assert result is None
        assert candidates["clean-spec"]["eligible"] is False, (
            "A candidate with no scan blockers must still be suppressed when "
            "its evidence corpus cannot be read — suppression is corpus-level, "
            "not blocker-level."
        )
        assert "evidence-unread" in candidates["clean-spec"]["blockers"], (
            "The evidence-unread blocker must be applied by corpus-level suppression"
        )

    def test_read_confined_substrate_fail_closed_branch_suppresses_candidates(
        self, tmp_path: Path
    ) -> None:
        """read_confined_substrate suppresses candidates when the read fails.

        This is the load-bearing fail-closed branch: the except ConfinementRefusal
        block that calls apply_refusals.  Removing that block would leave
        candidates eligible after a read failure, turning this test red.
        """
        mod = _load_retirement()

        root = tmp_path / "repo"
        root.mkdir()

        # A file that does not exist → ConfinementRefusal(input-unreadable).
        candidates = _fresh_candidates("spec-x")
        result = mod.read_confined_substrate(root, "nonexistent.toml", candidates)

        assert result is None
        assert candidates["spec-x"]["eligible"] is False, (
            "Failing to read a substrate must suppress dependent candidates. "
            "This test turns red if the except ConfinementRefusal block is removed."
        )
        assert "evidence-unread" in candidates["spec-x"]["blockers"]


# ---------------------------------------------------------------------------
# Group 6: Refusal reason from inside the guarded open
# ---------------------------------------------------------------------------

class TestRefusalFromInsideGuardedOpen:
    """Refusal codes come from inside the guarded open, not from second OS calls.

    Spec § Confinement:
    'Each refusal reason is produced from inside the guarded open. A refusal
    code is never derived from a second filesystem call on a path already refused,
    because that call re-walks an attacker-controlled path outside the guard.'
    """

    def test_nonexistent_file_produces_refusal_not_exception(
        self, tmp_path: Path
    ) -> None:
        """A nonexistent path produces ConfinementRefusal, not an unhandled OSError."""
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()

        with pytest.raises(mod.ConfinementRefusal) as exc_info:
            mod.confined_read_bytes(root, "workspace.toml")

        assert exc_info.value.code in ("input-unreadable", "spec-unreadable"), (
            f"Expected input-unreadable or spec-unreadable, got {exc_info.value.code!r}"
        )

    def test_read_limit_produces_input_too_large_refusal(
        self, tmp_path: Path
    ) -> None:
        """A file exceeding 8 MiB is refused as input-too-large, not truncated.

        The read stops at _READ_LIMIT rather than measuring the result afterwards.
        """
        mod = _load_retirement()
        root = tmp_path / "repo"
        root.mkdir()
        big_file = root / "big.toml"
        # Write slightly more than 8 MiB.
        big_file.write_bytes(b"x" * (8 * 1024 * 1024 + 1))

        with pytest.raises(mod.ConfinementRefusal) as exc_info:
            mod.confined_read_bytes(root, "big.toml")

        assert exc_info.value.code == "input-too-large", (
            f"Expected input-too-large, got {exc_info.value.code!r}. "
            "A file exceeding 8 MiB must be refused, not silently truncated."
        )


class TestPathSwappedBetweenCheckAndOpen:
    """The device/inode re-check across the open.

    The criterion requires a path swapped between the pre-open ``stat()`` and
    the opened descriptor to be refused rather than read.  A real race is not
    needed to drive it: ``_OPEN_FUNC`` is injectable, so an open that returns a
    descriptor to a *different* file reproduces the swap deterministically.

    Without this case the guard is unverified — disabling the comparison leaves
    the whole suite green, which is how a control that cannot fail survives.
    """

    def test_descriptor_for_a_different_file_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mod = _load_retirement()
        root = tmp_path
        spec_dir = root / "docs" / "specs" / "swapped"
        spec_dir.mkdir(parents=True)
        target = spec_dir / "spec.md"
        target.write_text("- **Status:** Shipped\n", encoding="utf-8")

        decoy = root / "docs" / "specs" / "swapped" / "decoy.md"
        decoy.write_text("attacker content\n", encoding="utf-8")

        real_open = os.open

        def open_the_decoy(path: object, flags: int, *args: object) -> int:
            # Same call shape, different inode: the swap the guard exists for.
            return real_open(decoy, flags)

        monkeypatch.setattr(mod, "_OPEN_FUNC", open_the_decoy)

        with pytest.raises(mod.ConfinementRefusal) as caught:
            mod.confined_read_bytes(
                root, "docs/specs/swapped/spec.md", spec_body=True
            )
        assert caught.value.path == "docs/specs/swapped/spec.md"

    def test_descriptor_for_the_same_file_is_read(self, tmp_path: Path) -> None:
        """The negative half: an unswapped read still succeeds.

        Without it the case above would pass against an implementation that
        refuses everything.
        """
        mod = _load_retirement()
        root = tmp_path
        spec_dir = root / "docs" / "specs" / "unswapped"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Shipped\n", encoding="utf-8")

        body = mod.confined_read_bytes(
            root, "docs/specs/unswapped/spec.md", spec_body=True
        )
        assert b"Shipped" in body
