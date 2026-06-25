"""The self-host pack / adapter allow-lists are sourced from the recipe.

`SELF_HOST_PACKS` and `SELF_HOST_ADAPTERS` are derived at import from
`recipes/self-host.toml` (`[recipe.packs].include` / `[recipe.adapters].targets`)
rather than hardcoded. These tests pin the extractor's fallback behaviour, prove
the read path is actually exercised (with values that differ from the defaults,
so a silent fallback can't masquerade as a successful read), and confirm import
stays total when the recipe is unreadable or malformed (AC3).
"""

from __future__ import annotations

import tomllib
import unittest
from unittest import mock

import agentbundle.build.self_host as sh
from agentbundle.build.self_host import (
    SELF_HOST_ADAPTERS,
    SELF_HOST_PACKS,
    _DEFAULT_SELF_HOST_ADAPTERS,
    _DEFAULT_SELF_HOST_PACKS,
    _extract_self_host_lists,
    _read_recipe_text,
)

# Values deliberately unlike the defaults, so a test that sees them knows the
# read→extract path ran rather than the total fallback.
_DIFFERING_RECIPE = (
    '[recipe.packs]\ninclude = ["only-pack"]\n'
    '[recipe.adapters]\ntargets = ["only-adapter"]\n'
)


class ExtractSelfHostListsTest(unittest.TestCase):
    def test_empty_recipe_falls_back_to_defaults(self):
        packs, adapters = _extract_self_host_lists({})
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, _DEFAULT_SELF_HOST_ADAPTERS)

    def test_missing_keys_fall_back_per_list(self):
        # adapters present, packs absent → packs default, adapters honoured
        recipe = {"recipe": {"adapters": {"targets": ["codex"]}}}
        packs, adapters = _extract_self_host_lists(recipe)
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, ("codex",))

    def test_present_lists_are_read(self):
        recipe = {
            "recipe": {
                "packs": {"include": ["core", "extra"]},
                "adapters": {"targets": ["claude-code"]},
            }
        }
        packs, adapters = _extract_self_host_lists(recipe)
        self.assertEqual(packs, ("core", "extra"))
        self.assertEqual(adapters, ("claude-code",))


class LoadSelfHostListsTest(unittest.TestCase):
    """`_load_self_host_lists` is the read→extract path with a total fallback."""

    def test_read_path_wins_with_differing_values(self):
        # Differing values prove the recipe was actually read and extracted,
        # not silently defaulted (the shipped recipe equals the defaults, so the
        # module-constant test below can't distinguish read from fallback).
        with mock.patch.object(sh, "_read_recipe_text", return_value=_DIFFERING_RECIPE):
            packs, adapters = sh._load_self_host_lists()
        self.assertEqual(packs, ("only-pack",))
        self.assertEqual(adapters, ("only-adapter",))

    def test_unreadable_recipe_falls_back(self):
        with mock.patch.object(sh, "_read_recipe_text", return_value=None):
            packs, adapters = sh._load_self_host_lists()
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, _DEFAULT_SELF_HOST_ADAPTERS)

    def test_read_error_falls_back(self):
        # AC3: a read that raises (non-UTF-8 bytes, permission error) must not
        # crash module import — it falls back to the defaults.
        with mock.patch.object(sh, "_read_recipe_text", side_effect=OSError("boom")):
            packs, adapters = sh._load_self_host_lists()
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, _DEFAULT_SELF_HOST_ADAPTERS)

    def test_malformed_toml_falls_back(self):
        with mock.patch.object(sh, "_read_recipe_text", return_value="not = = valid"):
            packs, adapters = sh._load_self_host_lists()
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, _DEFAULT_SELF_HOST_ADAPTERS)

    def test_real_read_text_error_falls_back(self):
        # Exercise the actual `read_text(encoding="utf-8")` raise inside
        # `_read_recipe_text` (the line the original blocker was about), not just
        # a mocked boundary — a non-UTF-8 recipe must fall back, not crash.
        boom = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        with mock.patch("pathlib.Path.read_text", side_effect=boom):
            packs, adapters = sh._load_self_host_lists()
        self.assertEqual(packs, _DEFAULT_SELF_HOST_PACKS)
        self.assertEqual(adapters, _DEFAULT_SELF_HOST_ADAPTERS)


class ModuleConstantsMatchRecipeTest(unittest.TestCase):
    def test_constants_derive_from_shipped_recipe(self):
        text = _read_recipe_text("self-host")
        self.assertIsNotNone(text, "self-host recipe must resolve")
        packs, adapters = _extract_self_host_lists(tomllib.loads(text))
        self.assertEqual(SELF_HOST_PACKS, packs)
        self.assertEqual(SELF_HOST_ADAPTERS, adapters)


if __name__ == "__main__":
    unittest.main()
