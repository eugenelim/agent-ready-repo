"""Schema admission for `[pack.layout.<scope>].section` (spec AC9, AC15).

A pack names the adopter-facing layout section it writes into. The section name
is not derivable from the pack name — `experience-design` writes `[design]`,
`desk-research` writes `[research]` — so the manifest declares it.

The key carries the same character class `pack_name` does, because it becomes a
TOML table header and the lookup key every reader trusts. Structural injection
is closed downstream by `config._emit_basic_string`; refusing here is the
bell-rings-loud companion, and it also rejects a well-formed name carrying `/`
or `.` that no reader could ever match.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

# This tree ships to adopters, where `contracts/` does not exist — so the
# packaged copy is the only one addressable here. The repository rule that the
# two copies agree lives in `tests/conformance/`, which never ships.
_PACKAGED_SCHEMA = (
    Path(__file__).resolve().parents[2] / "agentbundle" / "_data" / "pack.schema.json"
)


def _schema() -> dict:
    return json.loads(_PACKAGED_SCHEMA.read_text(encoding="utf-8"))


def _manifest(layout: dict) -> dict:
    return {
        "pack": {
            "name": "example",
            "version": "1.0.0",
            "description": "example pack",
            "layout": layout,
        }
    }


def _validates(layout: dict) -> bool:
    try:
        jsonschema.Draft202012Validator(_schema()).validate(_manifest(layout))
    except jsonschema.ValidationError:
        return False
    return True


@pytest.mark.parametrize("scope", ["repo", "user"])
def test_section_is_admitted_at_both_scopes(scope: str) -> None:
    assert _validates({scope: {"section": "design", "output_dir": "docs/design"}})


@pytest.mark.parametrize("scope", ["repo", "user"])
def test_unknown_sibling_key_is_still_refused(scope: str) -> None:
    """Admitting `section` must not open the sub-table to anything else."""
    assert not _validates({scope: {"section": "design", "bogus": "x"}})


@pytest.mark.parametrize(
    "section",
    [
        "a/b",            # path separator — no reader resolves it
        "Design",         # upper case
        "-leading",       # leading hyphen
        "with space",
        "with.dot",
        "",               # empty
    ],
)
def test_section_outside_the_character_class_is_refused(section: str) -> None:
    assert not _validates({"repo": {"section": section, "output_dir": "d"}})


@pytest.mark.parametrize("section", ["design", "research", "product-engineering", "a1"])
def test_section_inside_the_character_class_is_admitted(section: str) -> None:
    assert _validates({"repo": {"section": section, "output_dir": "d"}})


def test_the_packaged_schema_carries_the_key_at_both_scopes() -> None:
    """The engine validates against this copy, so it must carry the key.

    That the repository copy agrees is a repository rule, checked where the
    repository is present — see `tests/conformance/`.
    """
    layout = json.loads(_PACKAGED_SCHEMA.read_text(encoding="utf-8"))["properties"][
        "pack"
    ]["properties"]["layout"]["properties"]
    for scope in ("repo", "user"):
        assert "section" in layout[scope]["properties"], scope
