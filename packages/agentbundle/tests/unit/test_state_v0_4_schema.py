"""T1 (RFC-0052): state-file schema v0.4 — multi-adapter rows + hard
cross-version refusal.

v0.4 re-keys state to ``[pack.<name>.adapters.<adapter>]`` so one pack can
carry multiple adapter rows at one scope (ADR-0039). Cross-version handling
is a **hard refusal**: a v0.4 reader refuses any ``schema-version`` it does
not recognise — including an absent version and the immediately-prior v0.3 —
on both read and write (allowlist, not denylist). Migration is greenfield
(RFC-0052 D8): no converter, re-install.
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path


def _write_tmp(test: unittest.TestCase, text: str) -> Path:
    import tempfile

    fd_dir = tempfile.mkdtemp()
    test.addCleanup(__import__("shutil").rmtree, fd_dir, ignore_errors=True)
    path = Path(fd_dir) / ".agentbundle-state.toml"
    path.write_text(text, encoding="utf-8")
    return path


class StateSchemaVersionTests(unittest.TestCase):
    def test_state_schema_version_is_0_4(self) -> None:
        from agentbundle import config

        self.assertEqual(config.STATE_SCHEMA_VERSION, "0.4")


class MultiAdapterRowTests(unittest.TestCase):
    """One pack, two adapter rows, at one scope."""

    def _two_row_state(self):
        from agentbundle import config

        ps_cc = config.PackState(
            installed_version="1.2.0",
            scope="user",
            adapter="claude-code",
            files={".claude/skills/x/SKILL.md": {"sha": "aaa"}},
        )
        ps_codex = config.PackState(
            installed_version="1.2.0",
            scope="user",
            adapter="codex",
            files={".agents/skills/x/SKILL.md": {"sha": "bbb"}},
        )
        state = config.State()
        state.packs[("research", "claude-code")] = ps_cc
        state.packs[("research", "codex")] = ps_codex
        return state

    def test_emit_two_adapter_rows(self) -> None:
        from agentbundle import config

        out = config.dump_state(self._two_row_state())
        self.assertIn('schema-version = "0.4"', out)
        self.assertIn("[pack.research.adapters.claude-code]", out)
        self.assertIn("[pack.research.adapters.codex]", out)

    def test_emit_load_emit_byte_stable(self) -> None:
        # The canonical (loaded) form is a fixed point: once a state file
        # has been through the loader (which applies read-time defaults
        # like claude-code's target-file), emit → load → emit is byte-stable.
        from agentbundle import config

        canonical = config.dump_state(
            config.load_state(_write_tmp(self, config.dump_state(self._two_row_state())))
        )
        again = config.dump_state(config.load_state(_write_tmp(self, canonical)))
        self.assertEqual(canonical, again)

    def test_load_resolves_both_rows(self) -> None:
        from agentbundle import config

        path = _write_tmp(self, config.dump_state(self._two_row_state()))
        state = config.load_state(path)
        self.assertTrue(state.has_pack("research"))
        self.assertEqual(state.adapters_for_pack("research"), ["claude-code", "codex"])
        self.assertIsNotNone(state.row("research", "codex"))
        self.assertEqual(
            state.row("research", "codex").files[".agents/skills/x/SKILL.md"]["sha"],
            "bbb",
        )


class EmitterInjectionTests(unittest.TestCase):
    """The nested adapter key must route through ``_toml_key`` so a
    non-``[alnum-_]`` pack/adapter name cannot inject phantom TOML."""

    def test_pack_name_with_quote_round_trips(self) -> None:
        import tomllib

        from agentbundle import config

        weird = 'we"ird.name'
        ps = config.PackState(installed_version="1.0.0", adapter="codex")
        state = config.State()
        state.packs[(weird, "codex")] = ps
        out = config.dump_state(state)
        # The emitted header must be re-parseable by tomllib (no phantom
        # structure from the embedded quote / dot).
        parsed = tomllib.loads(out)
        self.assertIn(weird, parsed["pack"])
        # And it round-trips through the loader.
        path = _write_tmp(self, out)
        reloaded = config.load_state(path)
        self.assertTrue(reloaded.has_pack(weird))

    def test_adapter_name_with_control_char_round_trips(self) -> None:
        import tomllib

        from agentbundle import config

        weird_adapter = "ad\tapter"
        ps = config.PackState(installed_version="1.0.0", adapter=weird_adapter)
        state = config.State()
        state.packs[("demo", weird_adapter)] = ps
        out = config.dump_state(state)
        parsed = tomllib.loads(out)  # must not raise
        self.assertIn("demo", parsed["pack"])


class HardCrossVersionRefusalTests(unittest.TestCase):
    """Allowlist refusal: anything not exactly ``"0.4"`` raises, read and
    write, including absent and v0.3 (RFC-0052 falsifier)."""

    def _assert_refuses(self, toml_text: str, *, version_in_msg: str) -> None:
        from agentbundle import config

        path = _write_tmp(self, toml_text)
        for for_write in (False, True):
            with self.assertRaises(config.StateFileLegacy) as ctx:
                config.load_state(path, for_write=for_write)
            self.assertIn(version_in_msg, str(ctx.exception))

    def test_v03_refused_on_read_and_write(self) -> None:
        # A real v0.3 file (flat [pack.<name>] rows) must refuse, not be
        # mis-parsed under v0.4 rules.
        self._assert_refuses(
            textwrap.dedent("""
                schema-version = "0.3"

                [pack.demo]
                installed-version = "0.1.0"
                scope = "user"
                primitives = []

                [pack.demo.files]
            """).strip() + "\n",
            version_in_msg="0.3",
        )

    def test_v02_refused(self) -> None:
        self._assert_refuses(
            'schema-version = "0.2"\n\n[pack.demo]\n',
            version_in_msg="0.2",
        )

    def test_absent_schema_version_refused(self) -> None:
        # No fallback to the current constant — absent raises.
        self._assert_refuses(
            "[pack.demo]\n",
            version_in_msg="absent",
        )

    def test_future_version_refused(self) -> None:
        self._assert_refuses(
            'schema-version = "0.5"\n',
            version_in_msg="0.5",
        )


class V04NotMisparseableAsZeroFilePackTests(unittest.TestCase):
    """RFC-0052 falsifier (structural): a v0.4 file's
    ``[pack.<name>.adapters.<adapter>]`` shape must not be mis-readable as a
    zero-file pack by the v0.3 parse rules. We assert against a frozen copy
    of the v0.3 parse logic, since the live reader is now v0.4.
    """

    def test_v04_file_under_v03_rules_yields_no_real_pack_state(self) -> None:
        import tomllib

        from agentbundle import config

        v04_text = config.dump_state(self._single_codex_row())
        raw = tomllib.loads(v04_text)
        # Frozen v0.3 parse rule: a pack body's ``files`` map is read
        # directly off ``[pack.<name>]`` (no ``adapters`` level). Under v0.4
        # the real files live one level deeper, so the v0.3 rule sees an
        # empty ``files`` and an ``adapters`` sub-table it has no concept
        # of — i.e. it would mis-classify the pack as zero-file. We assert
        # that mismatch is detectable: the v0.3-level ``files`` is empty
        # while the true footprint is non-empty.
        pack_body = raw["pack"]["research"]
        v03_level_files = pack_body.get("files", {})
        self.assertEqual(v03_level_files, {})
        self.assertIn("adapters", pack_body)
        # The live v0.4 reader recovers the real footprint.
        path = _write_tmp(self, v04_text)
        state = config.load_state(path)
        self.assertEqual(
            set(state.row("research", "codex").files),
            {".agents/skills/x/SKILL.md"},
        )

    def _single_codex_row(self):
        from agentbundle import config

        state = config.State()
        state.packs[("research", "codex")] = config.PackState(
            installed_version="1.2.0",
            scope="user",
            adapter="codex",
            files={".agents/skills/x/SKILL.md": {"sha": "bbb"}},
        )
        return state


if __name__ == "__main__":
    unittest.main()
