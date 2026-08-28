"""Contract tests for the editable-install guard.

# STUB: AC5, AC6, AC7 — materialised at PLAN per CONVENTIONS § Stub → EXECUTE
# handoff, then expanded. The load-bearing cases are the two negatives: a
# regular install and an editable install pointing at THIS worktree must both
# stay silent, because firing on either would make the guard a false alarm on a
# legitimate setup.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import editable_install_guard as guard  # noqa: E402


class FakeDist:
    """Stands in for a Distribution: a name, a location, and a raw record.

    `location` must sit OUTSIDE the fixture root, because the guard skips
    source-tree metadata by location — that is what stops an in-worktree
    `*.egg-info` from answering instead of the real install.
    """

    def __init__(self, name: str, location: Path, payload: str | None) -> None:
        self.metadata = {"Name": name}
        self._location = location
        self._payload = payload

    def locate_file(self, _relative: str) -> Path:
        return self._location

    def read_text(self, name: str) -> str | None:
        return self._payload if name == "direct_url.json" else None


def editable_record(path: Path) -> str:
    return json.dumps({"url": path.as_uri(), "dir_info": {"editable": True}})


class GuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
        (self.root / "packages/agentbundle").mkdir(parents=True)
        # A stand-in site-packages, deliberately outside the fixture root.
        self.site = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: self.site.rmdir() if self.site.is_dir() else None)
        # A peer worktree sharing a name prefix with this one.
        self.peer = self.root.parent / (self.root.name + "-peer")
        self.peer.mkdir(exist_ok=True)
        self.addCleanup(lambda: self.peer.rmdir() if self.peer.is_dir() else None)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_with(
        self,
        payloads: dict[str, str | None],
        *,
        locations: dict[str, Path] | None = None,
        raises: Exception | None = None,
    ) -> tuple[int, str]:
        locations = locations or {}

        def distributions() -> list[FakeDist]:
            if raises is not None:
                raise raises
            return [
                FakeDist(name, locations.get(name, self.site), payload)
                for name, payload in payloads.items()
            ]

        with mock.patch.object(guard.md, "distributions", distributions):
            code, lines = guard.check(self.root)
        return code, "\n".join(lines)

    # ---- the negatives: a legitimate setup must never fail -------------------

    def test_regular_wheel_install_is_silent(self) -> None:
        """The operator's deliberate install has no direct_url.json."""
        code, text = self.run_with({"agentbundle": None, "credbroker": None})
        self.assertEqual(code, 0)
        self.assertEqual(text, "")

    def test_absent_install_is_silent(self) -> None:
        code, text = self.run_with({})
        self.assertEqual(code, 0)
        self.assertEqual(text, "")

    def test_editable_pointing_at_this_worktree_is_silent(self) -> None:
        code, text = self.run_with({"agentbundle": editable_record(self.root)})
        self.assertEqual(code, 0)
        self.assertEqual(text, "")

    def test_editable_pointing_into_this_worktree_is_silent(self) -> None:
        """`pip install -e packages/agentbundle` records the package dir."""
        code, text = self.run_with(
            {"agentbundle": editable_record(self.root / "packages/agentbundle")}
        )
        self.assertEqual(code, 0)
        self.assertEqual(text, "")

    def test_non_editable_direct_url_is_silent(self) -> None:
        """A local-wheel or VCS pin records direct_url without editable."""
        payload = json.dumps({"url": self.peer.as_uri(), "dir_info": {}})
        code, text = self.run_with({"agentbundle": payload})
        self.assertEqual(code, 0)
        self.assertEqual(text, "")

    # ---- the positive: the actual clobbering state ---------------------------

    def test_editable_pointing_at_a_peer_worktree_fails(self) -> None:
        code, text = self.run_with({"agentbundle": editable_record(self.peer)})
        self.assertEqual(code, 1)
        self.assertIn("EDITABLE install points outside this worktree", text)
        self.assertIn(str(self.peer), text)

    def test_a_sibling_name_prefix_is_not_treated_as_inside(self) -> None:
        """Containment is component-wise, not a string prefix.

        `<root>-peer` shares a prefix with `<root>`; a startswith check would
        call it inside and the guard would miss the one state it exists for.
        """
        self.assertTrue(str(self.peer).startswith(str(self.root)))
        code, _ = self.run_with({"agentbundle": editable_record(self.peer)})
        self.assertEqual(code, 1)

    def test_the_failure_names_a_repair_that_needs_no_peer_coordination(self) -> None:
        _, text = self.run_with({"agentbundle": editable_record(self.peer)})
        self.assertIn("pip uninstall", text)
        self.assertIn("python3 -m agentbundle", text)
        self.assertIn(str(self.root / "packages/agentbundle"), text)

    def test_both_packages_are_checked(self) -> None:
        code, text = self.run_with(
            {
                "agentbundle": editable_record(self.peer),
                "credbroker": editable_record(self.peer),
            }
        )
        self.assertEqual(code, 1)
        self.assertIn("agentbundle:", text)
        self.assertIn("credbroker:", text)

    # ---- never crash, never fail on an unreadable record --------------------

    def test_unparseable_record_reports_without_failing(self) -> None:
        code, text = self.run_with({"agentbundle": "{not json"})
        self.assertEqual(code, 0)
        self.assertIn("unreadable", text)

    def test_non_local_url_host_is_refused_not_trusted(self) -> None:
        payload = json.dumps(
            {"url": "file://evil.example/tmp/x", "dir_info": {"editable": True}}
        )
        code, text = self.run_with({"agentbundle": payload})
        self.assertEqual(code, 0)
        self.assertIn("unreadable", text)

    def test_undeterminable_root_skips_instead_of_failing(self) -> None:
        (self.root / ".git").unlink()
        deep = self.root / "a" / "b"
        deep.mkdir(parents=True)
        code, lines = guard.check(deep)
        self.assertEqual(code, 0)
        self.assertIn("skipped", "\n".join(lines))

    def test_source_tree_metadata_cannot_answer_for_the_install(self) -> None:
        """The blocker this guard shipped with, now pinned.

        `Makefile:7` puts `packages/agentbundle` first on PYTHONPATH for every
        make target, so the in-worktree `*.egg-info` answered instead of the
        real install — and an egg-info has no `direct_url.json`, so every
        verdict came back "regular". Measured: the guard was blind in exactly
        the invocation that registers it. Discovery therefore skips any
        distribution whose metadata lives inside this worktree.
        """
        code, text = self.run_with(
            {"agentbundle": None},
            locations={"agentbundle": self.root / "packages/agentbundle"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(text, "", "source-tree metadata is not an install")

        # The same name, this time genuinely installed and pointing at a peer.
        code, text = self.run_with({"agentbundle": editable_record(self.peer)})
        self.assertEqual(code, 1, "the real install must still be seen")

    def test_source_tree_metadata_enumerated_first_does_not_mask_the_install(self) -> None:
        """Both records present, source-tree one FIRST — the shipped failure.

        `md.distribution(name)` returned the first match on `sys.path`, and the
        Makefile puts the source tree first, so the real install was masked. The
        guard must consider every matching record, not the first.
        """
        def distributions() -> list[FakeDist]:
            return [
                FakeDist("agentbundle", self.root / "packages/agentbundle", None),
                FakeDist("agentbundle", self.site, editable_record(self.peer)),
            ]

        with mock.patch.object(guard.md, "distributions", distributions):
            code, lines = guard.check(self.root)
        self.assertEqual(code, 1, "a masked install must still be found")
        self.assertIn(str(self.peer), "\n".join(lines))

    def test_main_returns_zero_for_a_clean_classification(self) -> None:
        """`main`'s exit code is a property of the classifier, not of this box."""

        def distributions() -> list[FakeDist]:
            return [FakeDist("agentbundle", self.site, None)]

        with mock.patch.object(guard.md, "distributions", distributions):
            self.assertEqual(guard.main(["--directory", str(self.root)]), 0)

    def test_a_case_variant_path_naming_this_worktree_is_silent(self) -> None:
        """`Path.resolve()` does not fold case and `normcase` is a Windows no-op,
        so `/users/...` for `/Users/...` would otherwise be a permanent false
        alarm on a correct setup."""
        swapped = Path(str(self.root).replace("/Users/", "/users/", 1))
        if swapped == self.root:  # fixture root is not under /Users
            swapped = Path(str(self.root).upper())
        code, _ = self.run_with({"agentbundle": editable_record(swapped)})
        self.assertEqual(code, 0)

    def test_a_broken_environment_reports_without_failing(self) -> None:
        code, text = self.run_with({}, raises=ValueError("bad env"))
        self.assertEqual(code, 0)
        self.assertIn("unreadable", text)

    def test_localhost_url_host_is_accepted(self) -> None:
        payload = json.dumps(
            {"url": f"file://localhost{self.peer}", "dir_info": {"editable": True}}
        )
        code, _ = self.run_with({"agentbundle": payload})
        self.assertEqual(code, 1)

    def test_a_relative_url_path_is_refused_not_compared(self) -> None:
        payload = json.dumps({"url": "file:packages/agentbundle", "dir_info": {"editable": True}})
        code, text = self.run_with({"agentbundle": payload})
        self.assertEqual(code, 0)
        self.assertIn("unreadable", text)

    def test_an_empty_record_is_reported(self) -> None:
        code, text = self.run_with({"agentbundle": "   "})
        self.assertEqual(code, 0)
        self.assertIn("unreadable", text)

    def test_the_cited_adr_ordinal_resolves_to_a_real_file(self) -> None:
        """The ordinal moved 0093 -> 0094 mid-change; nothing pinned it."""
        source = (Path(__file__).resolve().parent / "repo" / "editable_install_guard.py").read_text(
            encoding="utf-8"
        )
        ordinals = re.findall(r"ADR-(\d{4})", source)
        self.assertTrue(ordinals, "the failure banner should cite an ADR")
        adr_dir = Path(__file__).resolve().parent.parent / "docs" / "adr"
        for ordinal in set(ordinals):
            self.assertTrue(
                list(adr_dir.glob(f"{ordinal}-*.md")), f"ADR-{ordinal} resolves to no file"
            )

    def test_the_guard_never_recommends_the_shape_it_exists_to_prevent(self) -> None:
        """No repair may be an editable install — for any package.

        The agentbundle branch used to offer `pip install -e <this worktree>`,
        described in its own text as zero-sum: it satisfies the guard here by
        moving the identical failure onto whichever worktree owned the pointer
        before. A maintainer following that advice re-arms the guard for a peer,
        which is how the same failure kept circulating between worktrees. A
        plain install is a snapshot and tracks no worktree, so it ends the loop.
        """
        for name in ("agentbundle", "credbroker"):
            _, text = self.run_with({name: editable_record(self.peer)})
            # Scope to the repair block: the diagnostic above it legitimately
            # explains that `pip install -e` is global, and a whole-text match
            # would fire on that explanation rather than on a recommendation.
            repairs = text.split("To repair, preferring the first:", 1)[1]
            offered = [line.strip() for line in repairs.splitlines()
                       if line.strip().startswith("python3 -m pip")]
            assert offered, f"{name} names no repair command"
            for command in offered:
                self.assertNotIn(" install -e ", f"{command} ", f"{name}: {command}")
                self.assertNotIn(" install --editable ", f"{command} ")

    def test_the_uninstall_repair_does_not_overclaim(self) -> None:
        """`-I` children cannot see PYTHONPATH, so 'nothing needs it' is false.

        `tools/test_marketplace_envelope_parity.py` spawns its child with `-I`,
        which ignores PYTHONPATH and resolves only site-packages. An unqualified
        "nothing in this repository needs the install" sends a maintainer who
        uninstalls into a second, unrelated red gate.
        """
        _, text = self.run_with({"agentbundle": editable_record(self.peer)})
        self.assertNotIn("Nothing in", text)
        self.assertIn("-I", text)

    def test_credbroker_is_not_offered_a_console_script_it_lacks(self) -> None:
        """`credbroker` declares no [project.scripts] and has no __main__."""
        _, text = self.run_with({"credbroker": editable_record(self.peer)})
        self.assertIn("library with no console script", text)
        self.assertNotIn("python3 -m pip install -e", text.split("credbroker:")[1])


if __name__ == "__main__":
    unittest.main()
