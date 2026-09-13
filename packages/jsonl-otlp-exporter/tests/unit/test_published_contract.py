"""T7 — the published contract a stranger reads.

Covers AC-0030, AC-0031, AC-0032.

These are structural checks on authored prose: a heading, a parseable block, a
named string. Wording is not asserted -- only the things a reader must be able
to find, and the claim that the example actually works.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

from jsonl_otlp_exporter.encode import encode_records
from jsonl_otlp_exporter.profile import REQUIRED_KEYS, parse_profile

PACKAGE = Path(__file__).resolve().parents[2]
README = PACKAGE / "README-pypi.md"
PROFILES = PACKAGE / "docs" / "profiles.md"


def _section(text: str, heading: str) -> str:
    """The body under a level-2 heading, up to the next level-2 heading."""
    start = text.index(heading) + len(heading)
    rest = text[start:]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


class TestReadme:
    """AC-0030, AC-0032 — what the published page must say, and where."""

    def test_the_what_this_sends_section_exists_and_carries_its_literals(self):
        body = _section(README.read_text(encoding="utf-8"), "\n## What this sends")
        for literal in ("OTLP logs", "--config", "sends nothing until an endpoint is configured"):
            assert literal in body, f"{literal!r} must appear under '## What this sends'"

    def test_the_compatibility_statement_is_present(self):
        text = README.read_text(encoding="utf-8")
        assert "semantic versioning" in text
        assert "the profile format is provisional while the version is 0.x" in text


class TestProfilesGuide:
    """AC-0031 — a worked profile a stranger can copy, and it has to be real."""

    def _worked_profile(self) -> dict:
        blocks = re.findall(r"```toml\n(.*?)```", PROFILES.read_text(encoding="utf-8"), re.S)
        assert blocks, "docs/profiles.md must carry a fenced toml block"
        return tomllib.loads(blocks[0])

    def test_the_worked_block_parses_as_a_valid_profile(self):
        """Not merely valid TOML: it must satisfy the same validator a run uses,
        so a reader who copies it gets a profile that works."""
        parsed = parse_profile(self._worked_profile())
        assert parsed.timestamp_format in {"rfc3339", "epoch-millis", "epoch-seconds"}

    def test_every_key_is_documented_outside_the_block(self):
        text = PROFILES.read_text(encoding="utf-8")
        prose = re.sub(r"```toml\n.*?```", "", text, flags=re.S)
        for key in sorted(REQUIRED_KEYS):
            assert key in prose, f"{key} must be explained, not only demonstrated"

    def test_the_worked_allowlist_omits_at_least_one_input_field(self):
        """The example has to demonstrate default-deny, not just describe it."""
        text = PROFILES.read_text(encoding="utf-8")
        sample = json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))
        profile = parse_profile(self._worked_profile())
        routed = profile.routed_fields
        omitted = set(sample) - set(profile.allowlist) - routed
        assert omitted, "the worked example must leave at least one input field behind"

    def test_the_omitted_field_really_is_absent_from_the_output(self):
        """Runs the documented example through the real encoder.

        A guide that claims a field is dropped and is wrong is worse than one
        that says nothing, because a reader relies on it for what leaves their
        machine.
        """
        text = PROFILES.read_text(encoding="utf-8")
        sample = json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))
        profile = parse_profile(self._worked_profile())
        body = encode_records([sample], profile, service_name="example")
        blob = json.dumps(body)
        omitted = set(sample) - set(profile.allowlist) - profile.routed_fields
        for field in omitted:
            assert field not in blob, f"{field} is documented as dropped but was emitted"
            assert str(sample[field]) not in blob, f"the VALUE of {field} reached the payload"

    def test_the_documented_severity_numbers_are_inside_the_accepted_range(self):
        for value in self._worked_profile()["severity_map"].values():
            assert 1 <= value <= 24


class TestReadmeLinks:
    """The README is rendered on PyPI, where a relative link does not resolve."""

    def test_every_link_out_of_the_readme_is_absolute(self):
        text = README.read_text(encoding="utf-8")
        targets = re.findall(r"\]\(([^)]+)\)", text)
        relative = [t for t in targets if not t.startswith(("http://", "https://", "#"))]
        assert not relative, f"relative links break on PyPI: {relative}"
