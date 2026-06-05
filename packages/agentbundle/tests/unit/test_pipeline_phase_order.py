"""T7: build-pipeline phase-order invariant — RFC-0005.

Per RFC-0005 § Build-pipeline ordering invariant, the pipeline projects
primitives in fixed order **`hook-body` → `agent` → `hook-wiring` →
`command` → `skill`** within each pack. `merge-into-agent-json` reads
the agent JSON the agent projection wrote, so agents must land first.

This test file instruments the adapter `project()` functions and
asserts the iteration order. It runs against every reference adapter
(claude-code, kiro, copilot, codex) so the invariant holds uniformly,
not just for Kiro. Per the plan, "cross-pack ordering is not
introduced" — the invariant is intra-pack.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


PHASE_ORDER = ("hook-body", "agent", "hook-wiring", "command", "skill")


def _multi_primitive_pack(root: Path) -> Path:
    """A pack carrying every primitive type so phase-order assertions
    have meaningful structure to walk."""
    pack = root / "pack"
    (pack / ".apm" / "skills" / "demo").mkdir(parents=True)
    (pack / ".apm" / "skills" / "demo" / "SKILL.md").write_text(
        "# demo\n", encoding="utf-8"
    )
    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Demo agent.\ntools: Read\n---\nbody\n",
        encoding="utf-8",
    )
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "on-spawn.sh").write_text(
        "#!/bin/sh\nexit 0\n", encoding="utf-8"
    )
    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring" / "on-spawn.toml").write_text(
        'attach-to-agent = "reviewer"\n\n'
        '[[hooks.agentSpawn]]\ncommand = "$HOOK_BODY_PATH"\n',
        encoding="utf-8",
    )
    (pack / ".apm" / "commands").mkdir(parents=True)
    (pack / ".apm" / "commands" / "qux.md").write_text("# qux\n", encoding="utf-8")
    return pack


class PhaseOrderExecutionTests(unittest.TestCase):
    """Each adapter's ``project()`` walks primitives in PHASE_ORDER.
    These tests instrument the adapter's primitive-iterator entry
    point at runtime — wrapping ``_iter_primitives`` so we capture
    what the live ``project()`` call actually consumes, not just what
    the helper would yield in isolation. AC16 demands the
    *observed* order from the *running* pipeline; tautological tests
    that just iterate the helper in isolation would pass a no-op
    implementation."""

    def _run_with_recorder(self, adapter_module, pack: Path, out: Path) -> list[str]:
        """Run ``adapter_module.project()`` with the iterator instrumented.

        We monkey-patch ``_iter_primitives`` on the adapter module to
        wrap the real generator and capture each yielded primitive in
        a recording list. The real generator's behaviour is preserved
        — the wrap only observes. After ``project()`` returns, the
        recorder reflects the actual production iteration order.
        """
        from agentbundle.build.contract import load as load_contract

        contract = load_contract(CONTRACT_PATH)
        out.mkdir(parents=True, exist_ok=True)

        original_iter = adapter_module._iter_primitives
        recorded: list[str] = []

        def recording_iter(contract):
            for primitive in original_iter(contract):
                recorded.append(primitive)
                yield primitive

        adapter_module._iter_primitives = recording_iter
        try:
            adapter_module.project(pack, contract, out)
        finally:
            adapter_module._iter_primitives = original_iter
        return recorded

    def test_kiro_project_iterates_in_phase_order(self) -> None:
        from agentbundle.build.adapters import kiro

        with tempfile.TemporaryDirectory() as tmp:
            pack = _multi_primitive_pack(Path(tmp))
            order = self._run_with_recorder(kiro, pack, Path(tmp) / "out")
            self._assert_phase_order(order, "kiro")
            # Kiro projects all five primitives: hook-body, agent,
            # hook-wiring, command (dropped, skipped), skill.
            self.assertIn("agent", order)
            self.assertIn("hook-wiring", order)
            self.assertIn("hook-body", order)
            # `agent` must precede `hook-wiring` — the merge target
            # invariant. AC16's load-bearing assertion.
            self.assertLess(
                order.index("agent"),
                order.index("hook-wiring"),
                "kiro projected hook-wiring before agent — merge target absent",
            )

    def test_claude_code_project_iterates_in_phase_order(self) -> None:
        from agentbundle.build.adapters import claude_code

        with tempfile.TemporaryDirectory() as tmp:
            pack = _multi_primitive_pack(Path(tmp))
            order = self._run_with_recorder(claude_code, pack, Path(tmp) / "out")
            self._assert_phase_order(order, "claude-code")

    def test_copilot_project_iterates_in_phase_order(self) -> None:
        from agentbundle.build.adapters import copilot

        with tempfile.TemporaryDirectory() as tmp:
            # The shared `_multi_primitive_pack` ships kiro-shaped wiring
            # (`agentSpawn` + `attach-to-agent`); copilot now projects
            # hook-wiring via `copilot-hooks-json`, which fail-closes on that
            # unmapped event. Give copilot a compatible SessionStart wiring so
            # all four projected primitives iterate (only `command` drops).
            pack = _multi_primitive_pack(Path(tmp))
            (pack / ".apm" / "hook-wiring" / "on-spawn.toml").write_text(
                "[[hooks.SessionStart]]\n"
                'hooks = [ { type = "command", command = "echo hi" } ]\n',
                encoding="utf-8",
            )
            order = self._run_with_recorder(copilot, pack, Path(tmp) / "out")
            self._assert_phase_order(order, "copilot")

    def test_codex_project_iterates_in_phase_order(self) -> None:
        from agentbundle.build.adapters import codex

        with tempfile.TemporaryDirectory() as tmp:
            pack = _multi_primitive_pack(Path(tmp))
            order = self._run_with_recorder(codex, pack, Path(tmp) / "out")
            self._assert_phase_order(order, "codex")

    def _assert_phase_order(self, recorded: list[str], adapter_name: str) -> None:
        """Recorded primitives must appear in PHASE_ORDER. Primitives
        the adapter doesn't project legitimately don't appear; ones
        it does project must respect the order. Equivalent to: the
        recorded sequence is a subsequence of PHASE_ORDER."""
        recorded_indices = [PHASE_ORDER.index(p) for p in recorded]
        self.assertEqual(
            recorded_indices,
            sorted(recorded_indices),
            f"{adapter_name}: primitives iterated out of phase order: "
            f"{recorded} (PHASE_ORDER={PHASE_ORDER})",
        )


class KiroHookWiringMergeDuringBuildTests(unittest.TestCase):
    """AC15 end-to-end: ``merge-into-agent-json`` fires during
    ``kiro.project()`` when a pack ships both an agent and a wiring
    TOML naming that agent. T6 shipped the merge engine; T7 wires it
    into the kiro adapter's pipeline. This test pins the integration:
    a real pack on disk produces a real merged agent JSON in dist/."""

    def test_kiro_pipeline_merges_wiring_into_agent_json(self) -> None:
        import json as _json

        from agentbundle.build.adapters import kiro

        with tempfile.TemporaryDirectory() as tmp:
            pack = _multi_primitive_pack(Path(tmp))
            out = Path(tmp) / "out"
            kiro.project(pack, _load_contract(), out)

            # Agent landed.
            agent_path = out / ".kiro" / "agents" / "reviewer.json"
            self.assertTrue(agent_path.exists(), "kiro pipeline didn't produce agent JSON")

            data = _json.loads(agent_path.read_text(encoding="utf-8"))
            # Body fields from agent .md frontmatter present.
            self.assertEqual(data["name"], "reviewer")
            self.assertEqual(data["description"], "Demo agent.")
            self.assertEqual(data["tools"], ["read_file"])

            # Wiring merged: hooks.agentSpawn with an id-tagged entry.
            self.assertIn("hooks", data, "wiring did not merge into agent JSON")
            self.assertIn("agentSpawn", data["hooks"])
            entries = data["hooks"]["agentSpawn"]
            self.assertEqual(len(entries), 1)
            # Id tag follows the <pack>:<basename> shape from T5/T6.
            self.assertEqual(entries[0]["id"], "pack:on-spawn")
            self.assertEqual(entries[0]["command"], "$HOOK_BODY_PATH")


class CrossAdapterIndependenceTests(unittest.TestCase):
    """RFC-0005: cross-pack ordering is not introduced. The build
    pipeline's *adapter-level* independence is the load-bearing
    guarantee — pack X projecting against Claude Code never touches
    pack Y's Kiro outputs (different target paths). Cross-pack
    contamination *within the same adapter* is prevented at validate
    time by T2's `check_kiro_wiring` rail (refuses
    `attach-to-agent` that names an agent the same pack doesn't ship),
    not at build time — once a pack passes validate, the pipeline
    trusts its `attach-to-agent` is same-pack.

    This test pins the adapter-level boundary: pack X's Claude Code
    wiring lands in `.claude/settings.local.json`; pack Y's Kiro
    agent lands in `.kiro/agents/<name>.json`. Even if both packs
    project against the same `output_root`, their outputs occupy
    distinct paths.
    """

    def test_kiro_agent_path_disjoint_from_claude_settings_path(self) -> None:
        from agentbundle.build.adapters import claude_code, kiro

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            pack_kiro = tmp_path / "pack-kiro"
            (pack_kiro / ".apm" / "agents").mkdir(parents=True)
            (pack_kiro / ".apm" / "agents" / "reviewer.md").write_text(
                "---\nname: reviewer\n---\nbody\n", encoding="utf-8"
            )

            pack_cc = tmp_path / "pack-cc"
            (pack_cc / ".apm" / "hook-wiring").mkdir(parents=True)
            (pack_cc / ".apm" / "hook-wiring" / "on-prompt.toml").write_text(
                '[hooks]\nUserPromptSubmit = ["do-thing"]\n', encoding="utf-8"
            )

            out = tmp_path / "out"
            contract = _load_contract()
            kiro.project(pack_kiro, contract, out)
            claude_code.project(pack_cc, contract, out)

            # Kiro produces the agent JSON at .kiro/agents/<name>.json.
            self.assertTrue((out / ".kiro" / "agents" / "reviewer.json").exists())
            # Claude Code's settings (if any) live elsewhere — and
            # critically, never touch the Kiro agent JSON.
            kiro_agent_text = (out / ".kiro" / "agents" / "reviewer.json").read_text(encoding="utf-8")
            self.assertNotIn(
                "do-thing",
                kiro_agent_text,
                "Claude Code adapter's wiring leaked into Kiro agent JSON",
            )


def _load_contract() -> dict:
    from agentbundle.build.contract import load as load_contract
    return load_contract(CONTRACT_PATH)


if __name__ == "__main__":
    unittest.main()
