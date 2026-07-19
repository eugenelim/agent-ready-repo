"""AC8 stub conformance — research-pack retriever scripts.

The spec's AC8 names a "stub conformance check" that imports each
example retriever and confirms `retrieve(query)` exists. This file
implements that check, plus a small description-token regression
test that catches the most common mode-dispatch misfire pattern
(someone "cleans up" the /desk-research SKILL.md description and drops
the load-bearing casual-cue tokens that bias mode selection).

Retriever side: imports both modules, asserts retrieve() is callable,
monkeypatches the urllib boundary so the test never hits an external
API, and asserts the returned dict conforms to the retriever-interface
contract (three keys; shape in the enumerated set).

Description side: reads packs/desk-research/.apm/skills/desk-research/SKILL.md,
asserts the description contains the casual cue tokens and the
explicit-default wording. The runtime mode-misfire itself is only
catchable in manual QA (per spec AC11); this catches the regression
where the description wording — which is the load-bearing dispatcher
signal — gets diluted in a future edit.
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
RESEARCH_SKILL = REPO_ROOT / "packs" / "desk-research" / ".apm" / "skills" / "desk-research"
ARXIV_SCRIPT = RESEARCH_SKILL / "scripts" / "arxiv-retriever.py"
PERPLEXITY_SCRIPT = RESEARCH_SKILL / "scripts" / "perplexity-retriever.py"
SKILL_MD = RESEARCH_SKILL / "SKILL.md"

VALID_SHAPES = {"raw", "synthesized", "meta"}
REQUIRED_KEYS = {"content", "citations", "shape"}


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArxivRetrieverConformance(unittest.TestCase):
    def test_imports_and_exposes_retrieve(self) -> None:
        module = _load(ARXIV_SCRIPT)
        self.assertTrue(hasattr(module, "retrieve"))
        self.assertTrue(callable(module.retrieve))

    def test_retrieve_returns_interface_shape(self) -> None:
        module = _load(ARXIV_SCRIPT)
        # Minimal Atom feed with one entry.
        canned_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Test paper</title>
    <id>http://arxiv.org/abs/0000.00000</id>
    <summary>An abstract about a paper.</summary>
    <author><name>Jane Doe</name></author>
    <link type="text/html" href="http://arxiv.org/abs/0000.00000"/>
  </entry>
</feed>"""

        class FakeResp:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *exc) -> None:
                return None

        with patch.object(module, "urllib") as mocked:
            mocked.parse.urlencode = lambda d: "encoded"
            mocked.request.urlopen.return_value = FakeResp(canned_xml)
            # ET is imported at module level; rebind through the module.
            result = module.retrieve("anything")

        self.assertIsInstance(result, dict)
        self.assertEqual(set(result.keys()), REQUIRED_KEYS)
        self.assertIn(result["shape"], VALID_SHAPES)
        self.assertEqual(result["shape"], "raw")
        self.assertIsInstance(result["citations"], list)
        # Non-empty citations are required for raw/synthesized per the
        # interface contract.
        self.assertGreater(len(result["citations"]), 0)
        for cite in result["citations"]:
            self.assertIn("url", cite)
            self.assertIn("title", cite)
            self.assertIn("primacy", cite)


class PerplexityRetrieverConformance(unittest.TestCase):
    def test_imports_and_exposes_retrieve(self) -> None:
        module = _load(PERPLEXITY_SCRIPT)
        self.assertTrue(hasattr(module, "retrieve"))
        self.assertTrue(callable(module.retrieve))

    def test_retrieve_returns_interface_shape(self) -> None:
        module = _load(PERPLEXITY_SCRIPT)
        canned_body = json.dumps(
            {
                "choices": [
                    {"message": {"content": "Synthesised answer here."}}
                ],
                "citations": [
                    {"url": "https://example.com/a", "title": "Source A"},
                    "https://example.com/b",
                ],
            }
        ).encode("utf-8")

        class FakeResp:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *exc) -> None:
                return None

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch.object(module.urllib.request, "urlopen", return_value=FakeResp(canned_body)):
                result = module.retrieve("anything")

        self.assertIsInstance(result, dict)
        self.assertEqual(set(result.keys()), REQUIRED_KEYS)
        self.assertIn(result["shape"], VALID_SHAPES)
        self.assertEqual(result["shape"], "synthesized")
        self.assertIsInstance(result["citations"], list)
        self.assertGreater(len(result["citations"]), 0)

    def test_missing_env_var_raises(self) -> None:
        module = _load(PERPLEXITY_SCRIPT)
        # patch.dict with clear=False then explicitly pop — empty patch
        # would still inherit ambient env in some shells.
        import os

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                module.retrieve("anything")


class ResearchSkillDescriptionRegression(unittest.TestCase):
    """The /desk-research SKILL.md description's wording is load-bearing —
    it's the dispatcher signal that biases between quick / standard /
    deep modes. AC11 enforces the behavior via manual QA; this test
    catches the most common regression (description "cleanup" that
    drops the casual-cue tokens or the explicit-default wording)."""

    def setUp(self) -> None:
        self.body = SKILL_MD.read_text(encoding="utf-8")
        # Extract the YAML frontmatter description field.
        m = re.search(r"^description:\s*\"?(.+?)\"?$", self.body, re.MULTILINE)
        self.assertIsNotNone(m, "SKILL.md missing description frontmatter")
        self.description = m.group(1)

    def test_casual_cue_tokens_present(self) -> None:
        # AC11's casual-phrasing set; at least these three must
        # appear in the description verbatim.
        for token in ("look up", "find out", "quick check"):
            self.assertIn(
                token,
                self.description,
                f"description missing casual-cue token {token!r} "
                f"— AC11 dispatcher bias depends on this",
            )

    def test_default_wording_present(self) -> None:
        # The default must be explicit in the description, not buried
        # in the body — the dispatcher only reads the description.
        self.assertRegex(
            self.description,
            r"as default|default.*quick|quick.*default",
            "description missing explicit default-mode wording "
            "— AC11 bias requires `quick` named as default",
        )

    def test_standard_or_deep_cue_tokens_present(self) -> None:
        # At least one standard/deep cue must appear so the description
        # biases away from quick on the academic-discipline side. The
        # tuple is the canonical contract — Always-do / AC11 / AC28
        # single-source the closed set from this test method.
        standard_deep_tokens = (
            "research with citations",
            "evidence-grounded",
            "go deep",
            "comprehensively",
        )
        for token in standard_deep_tokens:
            if token in self.description:
                return
        self.fail(
            f"description missing every standard/deep cue {standard_deep_tokens!r} "
            f"— AC11 bias requires at least one"
        )

    def test_applied_cue_tokens_present(self) -> None:
        # At least one applied cue from AC28's closed four-cue set
        # must appear so the description biases practitioner-
        # discipline dispatch. Phrase-shaped tokens only — the bare
        # token `applied` was deliberately excluded from AC28's
        # closed set to refuse incidental academic mentions
        # ("GRADE has been applied to clinical reviewing").
        applied_tokens = (
            "applied patterns for",
            "best practice for",
            "prior art on",
            "grey literature",
        )
        for token in applied_tokens:
            if token in self.description:
                return
        self.fail(
            f"description missing every applied cue {applied_tokens!r} "
            f"— AC11 bias requires at least one"
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
