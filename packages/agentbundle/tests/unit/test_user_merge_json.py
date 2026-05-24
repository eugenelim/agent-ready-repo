"""T5: `user-merge-json` mode — Claude Code user-scope hook-wiring merger.

Pure-function unit coverage. Integration coverage against the
`cc-user-hooks` fixture lives in
``packages/agentbundle/tests/integration/test_cc_user_hooks_fixture.py``.

Covers spec ACs:
  - AC8  — empty file → write hooks.<event> arrays with id-tagged entries.
  - AC9  — reinstall same version is byte-for-byte no-op.
  - AC10 — second pack with overlapping event appends; first pack unmoved.
  - AC11 — uninstall removes only owned entries; empty arrays removed.
  - AC12 — adopter hand-edit collision refuses; --force-merge adopts.
  - AC13 — unparseable JSON refuses non-zero; file unchanged.
  - AC14 — wrong-shape `hooks` or `hooks.<event>` refuses with the
           `<key-path> has unexpected shape` text.
  - Plus: auto-init absent `hooks` to `{}` and absent `hooks.<event>`
    to `[]`. Atomic write via `Path.replace`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# AC8 — empty file → write hooks.<event> arrays with id-tagged entries
# ---------------------------------------------------------------------------


class EmptyFileTests(unittest.TestCase):
    def test_empty_settings_writes_hooks_event_array(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            owned = project(
                target_path=target,
                pack_name="personal-reviewers",
                wiring_tomls={
                    "on-prompt": {
                        "hooks": {
                            "UserPromptSubmit": [{"command": "do-x", "matcher": ""}]
                        }
                    }
                },
            )
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("hooks", data)
            self.assertIn("UserPromptSubmit", data["hooks"])
            entries = data["hooks"]["UserPromptSubmit"]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["id"], "personal-reviewers:on-prompt")
            self.assertEqual(entries[0]["command"], "do-x")
            # No other top-level keys.
            self.assertEqual(set(data.keys()), {"hooks"})
            # Owned-state list reflects what we wrote.
            self.assertEqual(owned, [("UserPromptSubmit", "personal-reviewers:on-prompt")])

    def test_absent_file_creates_with_empty_object_and_appends(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            self.assertFalse(target.exists())
            project(
                target_path=target,
                pack_name="p",
                wiring_tomls={"h": {"hooks": {"Event": [{"command": "x"}]}}},
            )
            self.assertTrue(target.exists())
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["hooks"]["Event"][0]["id"], "p:h")

    def test_other_top_level_keys_preserved(self) -> None:
        """Adopter-set keys (theme, model, env) must not be touched."""
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"theme": "dark", "model": "opus", "env": {"K": "V"}}),
                encoding="utf-8",
            )
            project(
                target_path=target,
                pack_name="p",
                wiring_tomls={"h": {"hooks": {"E": [{"command": "x"}]}}},
            )
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["theme"], "dark")
            self.assertEqual(data["model"], "opus")
            self.assertEqual(data["env"], {"K": "V"})
            self.assertIn("hooks", data)


# ---------------------------------------------------------------------------
# AC9 — reinstall same version is byte-for-byte no-op
# ---------------------------------------------------------------------------


class IdempotencyTests(unittest.TestCase):
    def test_reinstall_same_version_byte_for_byte(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            wiring = {"on-prompt": {"hooks": {"UserPromptSubmit": [{"command": "x"}]}}}
            project(target, "p", wiring)
            first = target.read_bytes()
            project(target, "p", wiring)
            second = target.read_bytes()
            self.assertEqual(first, second, "reinstall changed bytes")

    def test_reinstall_position_preserved(self) -> None:
        """Reinstalling a pack must not reorder its entries within the array."""
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            project(target, "a", {"x": {"hooks": {"E": [{"command": "1"}]}}})
            project(target, "b", {"y": {"hooks": {"E": [{"command": "2"}]}}})
            project(target, "a", {"x": {"hooks": {"E": [{"command": "1"}]}}})  # reinstall a
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            # `a:x` must still be first.
            self.assertEqual(ids, ["a:x", "b:y"])


# ---------------------------------------------------------------------------
# AC10 — second pack appends; first pack unmoved
# ---------------------------------------------------------------------------


class TwoPacksOverlappingEventTests(unittest.TestCase):
    def test_second_pack_appends_after_first(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            project(target, "alpha", {"hk": {"hooks": {"E": [{"command": "a"}]}}})
            project(target, "beta", {"hk": {"hooks": {"E": [{"command": "b"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            self.assertEqual(ids, ["alpha:hk", "beta:hk"])
            commands = [e["command"] for e in data["hooks"]["E"]]
            self.assertEqual(commands, ["a", "b"])


# ---------------------------------------------------------------------------
# AC11 — uninstall removes only owned entries
# ---------------------------------------------------------------------------


class UninstallTests(unittest.TestCase):
    def test_uninstall_removes_only_owned(self) -> None:
        from agentbundle.build.projections.user_merge_json import project, unproject

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            project(target, "alpha", {"hk": {"hooks": {"E": [{"command": "a"}]}}})
            project(target, "beta", {"hk": {"hooks": {"E": [{"command": "b"}]}}})
            unproject(target, [("E", "alpha:hk")])
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            self.assertEqual(ids, ["beta:hk"])

    def test_uninstall_position_preserved_for_survivors(self) -> None:
        from agentbundle.build.projections.user_merge_json import project, unproject

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            project(target, "a", {"h": {"hooks": {"E": [{"command": "1"}]}}})
            project(target, "b", {"h": {"hooks": {"E": [{"command": "2"}]}}})
            project(target, "c", {"h": {"hooks": {"E": [{"command": "3"}]}}})
            unproject(target, [("E", "b:h")])
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            self.assertEqual(ids, ["a:h", "c:h"])

    def test_uninstall_removes_empty_event_array(self) -> None:
        """RFC-0005: empty `hooks.<event>` arrays are removed (not left as `[]`)."""
        from agentbundle.build.projections.user_merge_json import project, unproject

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{}", encoding="utf-8")
            project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            unproject(target, [("E", "p:h")])
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertNotIn("E", data.get("hooks", {}))

    def test_uninstall_against_absent_file_is_noop(self) -> None:
        from agentbundle.build.projections.user_merge_json import unproject

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            # No-op: file doesn't exist; nothing to remove.
            unproject(target, [("E", "p:h")])
            self.assertFalse(target.exists())


# ---------------------------------------------------------------------------
# AC12 — adopter collision refuses; --force-merge adopts
# ---------------------------------------------------------------------------


class AdopterCollisionTests(unittest.TestCase):
    def test_collision_with_adopter_entry_refuses(self) -> None:
        """An adopter-hand-authored entry with matching command must
        refuse install with the RFC-0005-specified text."""
        from agentbundle.build.projections.user_merge_json import (
            UserMergeRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"UserPromptSubmit": [{"command": "do-x"}]}}),
                encoding="utf-8",
            )
            with self.assertRaises(UserMergeRefusal) as ctx:
                project(
                    target,
                    "p",
                    {"on-prompt": {"hooks": {"UserPromptSubmit": [{"command": "do-x"}]}}},
                )
            msg = str(ctx.exception)
            self.assertIn("p's hook on-prompt at event UserPromptSubmit", msg)
            self.assertIn("appears to be already wired", msg)
            self.assertIn("--force-merge", msg)

    def test_collision_whitespace_normalised(self) -> None:
        """Collision detection compares commands after whitespace normalisation
        per RFC-0005 (`textual equality after whitespace normalisation`)."""
        from agentbundle.build.projections.user_merge_json import (
            UserMergeRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"E": [{"command": "  do-x   "}]}}),
                encoding="utf-8",
            )
            with self.assertRaises(UserMergeRefusal):
                project(target, "p", {"h": {"hooks": {"E": [{"command": "do-x"}]}}})

    def test_force_merge_adopts_collision(self) -> None:
        """--force-merge replaces the adopter entry; original preserved
        in a state-file snapshot path returned by project()."""
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"E": [{"command": "do-x"}]}}),
                encoding="utf-8",
            )
            project(
                target,
                "p",
                {"h": {"hooks": {"E": [{"command": "do-x"}]}}},
                force_merge=True,
            )
            data = json.loads(target.read_text(encoding="utf-8"))
            # The single entry is now id-tagged (adopter's was untagged).
            self.assertEqual(len(data["hooks"]["E"]), 1)
            self.assertEqual(data["hooks"]["E"][0]["id"], "p:h")

    def test_no_collision_when_commands_differ(self) -> None:
        """An adopter entry with a different command does NOT collide;
        the pack's entry appends alongside."""
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"E": [{"command": "manual-thing"}]}}),
                encoding="utf-8",
            )
            project(target, "p", {"h": {"hooks": {"E": [{"command": "pack-thing"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(len(data["hooks"]["E"]), 2)


# ---------------------------------------------------------------------------
# AC13 — unparseable JSON refuses; file unchanged
# ---------------------------------------------------------------------------


class UnparseableJsonTests(unittest.TestCase):
    def test_unparseable_settings_refuses(self) -> None:
        from agentbundle.build.projections.user_merge_json import (
            UserMergeRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text("{not valid json", encoding="utf-8")
            before = target.read_bytes()
            with self.assertRaises(UserMergeRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            msg = str(ctx.exception)
            self.assertIn("cannot parse", msg)
            self.assertIn("fix or back up", msg)
            # File unchanged.
            self.assertEqual(target.read_bytes(), before)


# ---------------------------------------------------------------------------
# AC14 — wrong-shape hooks key refuses with `unexpected shape` text
# ---------------------------------------------------------------------------


class WrongShapeTests(unittest.TestCase):
    def test_hooks_as_array_refuses(self) -> None:
        from agentbundle.build.projections.user_merge_json import (
            UserMergeRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(json.dumps({"hooks": ["wrong"]}), encoding="utf-8")
            with self.assertRaises(UserMergeRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            self.assertIn("hooks has unexpected shape", str(ctx.exception))

    def test_hooks_event_as_string_refuses(self) -> None:
        from agentbundle.build.projections.user_merge_json import (
            UserMergeRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"E": "wrong-shape"}}),
                encoding="utf-8",
            )
            with self.assertRaises(UserMergeRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            self.assertIn("hooks.E has unexpected shape", str(ctx.exception))


# ---------------------------------------------------------------------------
# Auto-init absent keys
# ---------------------------------------------------------------------------


class AutoInitTests(unittest.TestCase):
    def test_absent_hooks_key_auto_initialised(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
            project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("hooks", data)
            self.assertEqual(data["theme"], "dark")  # preserved

    def test_absent_event_in_existing_hooks_auto_initialised(self) -> None:
        from agentbundle.build.projections.user_merge_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "settings.json"
            target.write_text(
                json.dumps({"hooks": {"Other": [{"command": "y"}]}}),
                encoding="utf-8",
            )
            project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("E", data["hooks"])
            self.assertIn("Other", data["hooks"])


# ---------------------------------------------------------------------------
# hook_id helper
# ---------------------------------------------------------------------------


class HookIdTests(unittest.TestCase):
    def test_synthesize_id_shape(self) -> None:
        from agentbundle.build.projections.hook_id import synthesize_id

        self.assertEqual(
            synthesize_id("personal-reviewers", "on-prompt"),
            "personal-reviewers:on-prompt",
        )

    def test_synthesize_id_preserves_hyphens(self) -> None:
        from agentbundle.build.projections.hook_id import synthesize_id

        self.assertEqual(
            synthesize_id("my-pack", "long-hook-name"),
            "my-pack:long-hook-name",
        )


if __name__ == "__main__":
    unittest.main()
