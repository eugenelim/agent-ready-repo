"""T6: `merge-into-agent-json` mode — Kiro hook-wiring merger.

Pure-function unit coverage. Integration coverage against the
`kiro-repo-hooks` and `kiro-user-hooks` fixtures lives in the
corresponding integration test files.

Mirrors the shape of T5's `test_user_merge_json.py` but adapts for the
pack-owned target file (no adopter-collision logic, no force_merge,
missing-agent-file refusal with the `internal:` text).

Covers spec ACs:
  - AC15 — merge into pack-owned agent JSON writes hooks.<event>
           arrays with id-tagged entries; other agent JSON keys
           (name, description, etc.) untouched.
  - AC19 — uninstall removes wiring-owned entries from the agent JSON;
           the agent file itself remains.
  - AC17 (validate-time) — covered by scope_rails tests in
           `test_kiro_event_vocabulary.py`; this file's vocabulary
           tests pin the rail-output shape against the projection
           module.

Plus internal failure modes:
  - Missing agent file at merge time refuses with the RFC-0005
    `internal: <agent-file> missing` text (pipeline-ordering invariant
    violation; reachable only via test instrumentation).
  - Unparseable agent JSON refuses with the `cannot parse` text.
  - Wrong-shape `hooks` or `hooks.<event>` refuses.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


def _seed_agent_json(target: Path, extra: dict | None = None) -> None:
    """Pre-create the agent JSON file with body fields T6 must preserve."""
    body: dict = {"name": "reviewer", "description": "Reviews pending work."}
    if extra:
        body.update(extra)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# AC15 — merge into pack-owned agent JSON, preserve body keys
# ---------------------------------------------------------------------------


class MergeIntoAgentJsonTests(unittest.TestCase):
    def test_merges_into_existing_agent_json(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            owned = project(
                target_path=target,
                pack_name="clipboard-summary",
                wiring_tomls={
                    "on-prompt": {
                        "attach-to-agent": "reviewer",
                        "hooks": {
                            "userPromptSubmit": [{"command": "x", "matcher": ""}]
                        },
                    }
                },
            )
            data = json.loads(target.read_text(encoding="utf-8"))
            # Body keys preserved.
            self.assertEqual(data["name"], "reviewer")
            self.assertEqual(data["description"], "Reviews pending work.")
            # Hooks merged.
            self.assertEqual(data["hooks"]["userPromptSubmit"][0]["id"], "clipboard-summary:on-prompt")
            self.assertEqual(data["hooks"]["userPromptSubmit"][0]["command"], "x")
            self.assertEqual(owned, [("userPromptSubmit", "clipboard-summary:on-prompt")])

    def test_reinstall_byte_for_byte(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            wiring = {
                "on-prompt": {
                    "attach-to-agent": "reviewer",
                    "hooks": {"userPromptSubmit": [{"command": "x"}]},
                }
            }
            project(target, "p", wiring)
            first = target.read_bytes()
            project(target, "p", wiring)
            self.assertEqual(target.read_bytes(), first)

    def test_two_packs_overlapping_event_append(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            project(target, "alpha", {"h": {"hooks": {"E": [{"command": "a"}]}}})
            project(target, "beta", {"h": {"hooks": {"E": [{"command": "b"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            self.assertEqual(ids, ["alpha:h", "beta:h"])

    def test_preserves_existing_unrelated_top_level_keys(self) -> None:
        """A Kiro agent JSON may carry fields beyond name/description.
        The merger must not touch them — the file is pack-owned, but the
        owner is the pack as a whole, not just the wiring."""
        from agentbundle.build.projections.merge_into_agent_json import project

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target, extra={"model": "claude-opus-4-7", "tools": ["Read"]})
            project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["model"], "claude-opus-4-7")
            self.assertEqual(data["tools"], ["Read"])


# ---------------------------------------------------------------------------
# AC19 — uninstall removes owned entries; agent file remains
# ---------------------------------------------------------------------------


class UninstallTests(unittest.TestCase):
    def test_uninstall_removes_owned_entries_only(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            project,
            unproject,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            project(target, "alpha", {"h": {"hooks": {"E": [{"command": "a"}]}}})
            project(target, "beta", {"h": {"hooks": {"E": [{"command": "b"}]}}})
            unproject(target, [("E", "alpha:h")])
            data = json.loads(target.read_text(encoding="utf-8"))
            ids = [e["id"] for e in data["hooks"]["E"]]
            self.assertEqual(ids, ["beta:h"])

    def test_uninstall_keeps_agent_file_in_place(self) -> None:
        """RFC-0005 § Uninstall: the agent file itself stays — the
        agent primitive's `direct-file` uninstall removes it."""
        from agentbundle.build.projections.merge_into_agent_json import (
            project,
            unproject,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            owned = project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            unproject(target, owned)
            self.assertTrue(target.exists(), "agent file must survive unproject")
            data = json.loads(target.read_text(encoding="utf-8"))
            # Body still there.
            self.assertEqual(data["name"], "reviewer")

    def test_uninstall_removes_empty_event_array(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            project,
            unproject,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            _seed_agent_json(target)
            project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            unproject(target, [("E", "p:h")])
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertNotIn("E", data.get("hooks", {}))


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


class FailureModeTests(unittest.TestCase):
    def test_missing_agent_file_refuses_with_internal_text(self) -> None:
        """RFC-0005: a missing agent file at merge time is a
        pipeline-ordering invariant violation. The refusal text names
        the internal nature so it's diagnosable as a CLI bug, not an
        adopter mistake."""
        from agentbundle.build.projections.merge_into_agent_json import (
            AgentJsonRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "missing.json"
            self.assertFalse(target.exists())
            with self.assertRaises(AgentJsonRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            msg = str(ctx.exception)
            self.assertIn("internal:", msg)
            self.assertIn("missing", msg)
            self.assertIn("agent must project before wiring", msg)

    def test_unparseable_agent_json_refuses(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            AgentJsonRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            target.write_text("{not valid", encoding="utf-8")
            before = target.read_bytes()
            with self.assertRaises(AgentJsonRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            self.assertIn("cannot parse", str(ctx.exception))
            # File unchanged.
            self.assertEqual(target.read_bytes(), before)

    def test_wrong_shape_hooks_refuses(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            AgentJsonRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            target.write_text(json.dumps({"name": "x", "hooks": ["wrong"]}), encoding="utf-8")
            with self.assertRaises(AgentJsonRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            self.assertIn("hooks has unexpected shape", str(ctx.exception))

    def test_wrong_shape_hooks_event_refuses(self) -> None:
        from agentbundle.build.projections.merge_into_agent_json import (
            AgentJsonRefusal,
            project,
        )

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "reviewer.json"
            target.write_text(
                json.dumps({"name": "x", "hooks": {"E": "wrong"}}),
                encoding="utf-8",
            )
            with self.assertRaises(AgentJsonRefusal) as ctx:
                project(target, "p", {"h": {"hooks": {"E": [{"command": "x"}]}}})
            self.assertIn("hooks.E has unexpected shape", str(ctx.exception))


# ---------------------------------------------------------------------------
# AC17/AC17b — per-adapter event-vocabulary check
# ---------------------------------------------------------------------------


class EventVocabularyRailTests(unittest.TestCase):
    """The vocabulary gate is rail-side (scope_rails.check_kiro_event_vocabulary);
    this class drives the rail directly. The CLI wiring is tested in
    `test_kiro_user_hooks_fixture.py` / `test_fixtures_validate.py`."""

    def test_refuses_pascal_event_against_kiro_vocabulary(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_event_vocabulary

        refusal = check_kiro_event_vocabulary(
            pack_name="demo",
            wiring_tomls={
                "on-prompt": {"hooks": {"UserPromptSubmit": [{"command": "x"}]}}
            },
            vocabulary=["agentSpawn", "userPromptSubmit", "preToolUse"],
            target_adapters={"kiro"},
            adapter_name="kiro",
        )
        self.assertIsNotNone(refusal)
        self.assertIn("UserPromptSubmit", refusal)
        self.assertIn("not in adapter 'kiro' agent-event-vocabulary", refusal)

    def test_accepts_camelcase_event_in_kiro_vocabulary(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_event_vocabulary

        refusal = check_kiro_event_vocabulary(
            pack_name="demo",
            wiring_tomls={
                "on-prompt": {"hooks": {"userPromptSubmit": [{"command": "x"}]}}
            },
            vocabulary=["agentSpawn", "userPromptSubmit", "preToolUse"],
            target_adapters={"kiro"},
            adapter_name="kiro",
        )
        self.assertIsNone(refusal)

    def test_no_check_when_vocabulary_absent(self) -> None:
        """AC17b: when the resolved target adapter declares no
        `agent-event-vocabulary`, the rail must not fire. Claude Code
        accepts arbitrary event names because its projection declares
        no vocabulary."""
        from agentbundle.build.scope_rails import check_kiro_event_vocabulary

        refusal = check_kiro_event_vocabulary(
            pack_name="demo",
            wiring_tomls={
                "on-prompt": {"hooks": {"UserPromptSubmit": [{"command": "x"}]}}
            },
            vocabulary=None,  # adapter doesn't declare it
            target_adapters={"claude-code"},
            adapter_name="claude-code",
        )
        self.assertIsNone(refusal)

    def test_no_check_when_kiro_not_in_targets(self) -> None:
        """Symmetric to the attach-to-agent rail: if kiro isn't in the
        target set, the rail is a no-op."""
        from agentbundle.build.scope_rails import check_kiro_event_vocabulary

        refusal = check_kiro_event_vocabulary(
            pack_name="demo",
            wiring_tomls={
                "on-prompt": {"hooks": {"UserPromptSubmit": [{"command": "x"}]}}
            },
            vocabulary=["agentSpawn"],
            target_adapters={"claude-code"},
            adapter_name="kiro",
        )
        self.assertIsNone(refusal)

    def test_first_offender_wins(self) -> None:
        """Iteration order: wiring_tomls dict-insertion → each body's
        hooks dict-insertion. Python 3.7+ pins both; the first
        out-of-vocabulary event encountered must be the one surfaced.
        Pin the order strictly so a refactor that accidentally
        reorders iteration regresses loudly."""
        from agentbundle.build.scope_rails import check_kiro_event_vocabulary

        refusal = check_kiro_event_vocabulary(
            pack_name="demo",
            wiring_tomls={
                "first": {"hooks": {"GoodEvent": [{"command": "x"}], "BadOne": [{"command": "y"}]}},
                "second": {"hooks": {"AlsoBad": [{"command": "z"}]}},
            },
            vocabulary=["GoodEvent"],
            target_adapters={"kiro"},
            adapter_name="kiro",
        )
        self.assertIsNotNone(refusal)
        self.assertIn("BadOne", refusal, f"first offender wasn't BadOne: {refusal}")
        self.assertNotIn("AlsoBad", refusal, "rail kept walking past first offender")
        self.assertIn("first.toml", refusal, "refusal didn't name the offending wiring")


if __name__ == "__main__":
    unittest.main()
