"""T2: kiro hook-wiring `attach-to-agent` validate rail.

In-memory tests of the pure rail function `check_kiro_attach_to_agent`
plus filesystem-shaped tests of the wrapper `check_kiro_wiring`. Pack-
shaped dicts are constructed inline; no on-disk fixture packs are used
(those land in T3 and exercise the same rails via the integration path).

Acceptance criterion the rail covers: spec AC6.
Refusal text (RFC-0005 § Repo-scope Kiro promotion):
    pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent'
    (or names an unknown agent); required for kiro projection
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

REFUSAL_PREFIX = "pack {pack}'s hook-wiring {name}.toml does not declare 'attach-to-agent'"


class InMemoryRailKiroTargetedTests(unittest.TestCase):
    """Rail fires when `kiro` is in target_adapters."""

    def test_refuses_wiring_without_attach_to_agent(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="personal-reviewers",
            wiring_tomls={"on-prompt": {"hooks": {"userPromptSubmit": [{"command": "x"}]}}},
            agent_basenames={"reviewer"},
            target_adapters={"kiro"},
        )
        self.assertIsNotNone(refusal)
        self.assertIn("personal-reviewers", refusal)
        self.assertIn("on-prompt.toml", refusal)
        self.assertIn("does not declare 'attach-to-agent'", refusal)
        self.assertIn("required for kiro projection", refusal)

    def test_refuses_attach_to_agent_naming_unknown_agent(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="clipboard-summary",
            wiring_tomls={"on-prompt": {"attach-to-agent": "non-existent"}},
            agent_basenames={"clipboard-watcher"},
            target_adapters={"kiro"},
        )
        self.assertIsNotNone(refusal)
        self.assertIn("clipboard-summary", refusal)
        self.assertIn("or names an unknown agent", refusal)

    def test_refuses_attach_to_agent_of_wrong_type(self) -> None:
        """A non-string `attach-to-agent` is shape-wrong; the rail treats it the same as missing."""
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={"on-prompt": {"attach-to-agent": ["reviewer"]}},
            agent_basenames={"reviewer"},
            target_adapters={"kiro"},
        )
        self.assertIsNotNone(refusal)

    def test_accepts_attach_to_agent_naming_known_agent(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="personal-reviewers",
            wiring_tomls={"on-prompt": {"attach-to-agent": "reviewer"}},
            agent_basenames={"reviewer"},
            target_adapters={"kiro"},
        )
        self.assertIsNone(refusal)

    def test_first_offender_wins(self) -> None:
        """Multiple wiring TOMLs — the rail surfaces the first failure only."""
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={
                "a": {"attach-to-agent": "reviewer"},
                "b": {},
                "c": {"attach-to-agent": "missing"},
            },
            agent_basenames={"reviewer"},
            target_adapters={"kiro"},
        )
        self.assertIsNotNone(refusal)
        self.assertIn("b.toml", refusal)
        self.assertNotIn("c.toml", refusal)


class InMemoryRailKiroCliTargetedTests(unittest.TestCase):
    """The rail fires for the whole merge-into-agent-json family — `kiro-cli`
    as well as the legacy `kiro` (RFC-0022 / kiro-install-alias-parity). The
    `attach-to-agent` merge target exists for both, so both validate it."""

    def test_fires_for_kiro_cli_unknown_agent(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="cli-pack",
            wiring_tomls={"on-prompt": {"attach-to-agent": "non-existent"}},
            agent_basenames={"reviewer"},
            target_adapters={"kiro-cli"},
        )
        self.assertIsNotNone(refusal)
        self.assertIn("or names an unknown agent", refusal)

    def test_accepts_well_formed_kiro_cli(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="cli-pack",
            wiring_tomls={"on-prompt": {"attach-to-agent": "reviewer"}},
            agent_basenames={"reviewer"},
            target_adapters={"kiro-cli"},
        )
        self.assertIsNone(refusal)


class InMemoryRailNonKiroTargetTests(unittest.TestCase):
    """Rail is a no-op when kiro isn't in target_adapters — Claude-Code-only packs."""

    def test_claude_code_only_with_attach_to_agent_accepted(self) -> None:
        """AC6 / plan T2: a Claude-Code-only pack with `attach-to-agent` present
        — the field is ignored, not refused."""
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={"on-prompt": {"attach-to-agent": "anything"}},
            agent_basenames=set(),  # no agents shipped
            target_adapters={"claude-code"},
        )
        self.assertIsNone(refusal)

    def test_claude_code_only_without_attach_to_agent_accepted(self) -> None:
        """Claude-Code-only packs don't need `attach-to-agent` — the rail must
        be a no-op for them regardless of wiring shape."""
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={"on-prompt": {}},
            agent_basenames=set(),
            target_adapters={"claude-code"},
        )
        self.assertIsNone(refusal)

    def test_empty_target_adapters_accepted(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={"on-prompt": {}},
            agent_basenames=set(),
            target_adapters=set(),
        )
        self.assertIsNone(refusal)


class InMemoryRailEmptyWiringTests(unittest.TestCase):
    """Rail no-op when the pack ships no hook-wiring."""

    def test_no_wiring_no_refusal(self) -> None:
        from agentbundle.build.scope_rails import check_kiro_attach_to_agent

        refusal = check_kiro_attach_to_agent(
            pack_name="demo",
            wiring_tomls={},
            agent_basenames={"reviewer"},
            target_adapters={"kiro"},
        )
        self.assertIsNone(refusal)


class FilesystemWrapperTests(unittest.TestCase):
    """`check_kiro_wiring` reads from disk, parses each wiring TOML with
    tomllib, and delegates to the in-memory rail. A malformed wiring TOML
    refuses on its own (per RFC-0005's refuse-and-explain pattern)."""

    def _make_pack(self, tmp_path: Path, *, wiring: dict[str, str], agents: list[str]) -> Path:
        pack = tmp_path / "demo-pack"
        (pack / ".apm" / "hook-wiring").mkdir(parents=True, exist_ok=True)
        for name, body in wiring.items():
            (pack / ".apm" / "hook-wiring" / f"{name}.toml").write_text(
                body, encoding="utf-8"
            )
        if agents:
            (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)
            for name in agents:
                (pack / ".apm" / "agents" / f"{name}.md").write_text(
                    f"# {name}\n", encoding="utf-8"
                )
        return pack

    def test_filesystem_wrapper_refuses_missing_attach_to_agent(self) -> None:
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = self._make_pack(
                tmp,
                wiring={"on-prompt": '[[hooks.userPromptSubmit]]\ncommand = "x"\n'},
                agents=["reviewer"],
            )
            refusal = check_kiro_wiring(pack, "demo-pack", {"kiro"})
            self.assertIsNotNone(refusal)
            self.assertIn("does not declare 'attach-to-agent'", refusal)

    def test_filesystem_wrapper_accepts_well_formed_pack(self) -> None:
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = self._make_pack(
                tmp,
                wiring={
                    "on-prompt": textwrap.dedent("""
                        attach-to-agent = "reviewer"

                        [[hooks.userPromptSubmit]]
                        command = "do-thing"
                    """).strip()
                },
                agents=["reviewer"],
            )
            self.assertIsNone(check_kiro_wiring(pack, "demo-pack", {"kiro"}))

    def test_filesystem_wrapper_refuses_missing_attach_to_agent_for_kiro_cli(self) -> None:
        """The wrapper fires for the merging adapter `kiro-cli` too — symlink /
        parse / missing-attach refusals are preserved for the adapter that now
        owns the legacy JSON+merge behavior (RFC-0022 / kiro-install-alias-parity)."""
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = self._make_pack(
                tmp,
                wiring={"on-prompt": '[[hooks.userPromptSubmit]]\ncommand = "x"\n'},
                agents=["reviewer"],
            )
            refusal = check_kiro_wiring(pack, "demo-pack", {"kiro-cli"})
            self.assertIsNotNone(refusal)
            self.assertIn("does not declare 'attach-to-agent'", refusal)

    def test_filesystem_wrapper_skips_when_no_kiro_in_targets(self) -> None:
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = self._make_pack(
                tmp,
                wiring={"on-prompt": '[[hooks.SomethingPascal]]\ncommand = "x"\n'},
                agents=[],
            )
            # Same malformed shape as the "refuse" test, but no kiro target → no-op.
            self.assertIsNone(check_kiro_wiring(pack, "demo-pack", {"claude-code"}))

    def test_filesystem_wrapper_skips_pack_without_wiring_dir(self) -> None:
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = tmp / "demo-pack"
            pack.mkdir()
            self.assertIsNone(check_kiro_wiring(pack, "demo-pack", {"kiro"}))

    def test_filesystem_wrapper_refuses_malformed_toml(self) -> None:
        """A wiring TOML that fails to parse is a pack-author error; the rail
        surfaces it with a clear refusal rather than a hidden tomllib trace."""
        import tempfile

        from agentbundle.build.scope_rails import check_kiro_wiring

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            pack = self._make_pack(
                tmp,
                wiring={"on-prompt": "this is not = valid = toml ["},
                agents=["reviewer"],
            )
            refusal = check_kiro_wiring(pack, "demo-pack", {"kiro"})
            self.assertIsNotNone(refusal)
            self.assertIn("failed to parse", refusal)


if __name__ == "__main__":
    unittest.main()
