"""Parser parity: the readiness module's source-authority parser is `work-intake`'s.

`work-loop`'s `_header_readiness.py` ports the `parse_source_authority` closure of
`work-intake`'s `refresh.py` instead of loading it, so dispatch needs no other skill.
Nothing regenerates the port: this test runs both parsers over every
`toml source-authority` block in the repository's docs, packs and tests, and over a
fixed set of edge cases, and requires the same accept or refuse and the same parsed
fields each time.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import itertools
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "packs/core/.apm/skills"
_SCANNED = ("docs", "packs", "tests")
_SUFFIXES = {".md", ".py", ".txt", ".toml"}
_SKIPPED = {"__pycache__", ".git", "node_modules", ".venv"}
_BLOCK = re.compile(r"^```toml source-authority\s*$\n.*?^```\s*$", re.MULTILINE | re.DOTALL)
_COUNTER = itertools.count()


def _load(path: Path, stem: str) -> ModuleType:
    """Load a skill script by path under a unique name that names its pack and skill."""
    name = f"core_{stem}_parity_{next(_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


@pytest.fixture(scope="module")
def parsers() -> tuple[Any, Any]:
    ported = _load(SKILLS / "work-loop/scripts/_header_readiness.py", "work_loop_readiness")
    source = _load(SKILLS / "work-intake/scripts/refresh.py", "work_intake_refresh")
    return ported.parse_source_authority, source.parse_source_authority


def _texts() -> list[tuple[str, str]]:
    """Each repository file that holds a source-authority fence, with its path."""
    found: list[tuple[str, str]] = []
    for top in _SCANNED:
        for path in sorted((REPO_ROOT / top).rglob("*")):
            if (
                path.suffix not in _SUFFIXES
                or _SKIPPED & set(path.parts)
                or not path.is_file()
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "```toml source-authority" in text:
                found.append((path.relative_to(REPO_ROOT).as_posix(), text))
    return found


def _outcome(parser: Any, markdown: str) -> tuple[str, Any]:
    """`("accept", fields)` or `("refuse", code)`, so two parsers' results compare."""
    try:
        parsed = parser(markdown)
    except ValueError as refusal:
        return "refuse", (type(refusal).__name__, str(refusal))
    return "accept", dataclasses.asdict(parsed)


_VALID = (
    '```toml source-authority\ncontract_version = "source-authority.v1"\n'
    'mode = "tracker-origin"\nsource_ref = "example-service://ABC-1"\n'
    'source_revision = "r1"\n\n[owned_fields]\nOutcome = "local"\n```\n'
)
_EDGE_CASES = {
    "valid": f"# Spec\n\n{_VALID}",
    "no-block": "# Spec\n\nnothing here\n",
    "two-blocks": f"{_VALID}\n{_VALID}",
    "empty-block": "```toml source-authority\n```\n",
    "not-toml": "```toml source-authority\nthis = = bad\n```\n",
    "unknown-key": _VALID.replace("[owned_fields]", 'extra = "x"\n\n[owned_fields]'),
    "bad-contract": _VALID.replace("source-authority.v1", "source-authority.v2"),
    "bad-mode": _VALID.replace("tracker-origin", "sideways"),
    "accepted-revision": _VALID.replace(
        'source_revision = "r1"\n', 'source_revision = "r1"\naccepted_revision = "r0"\n'
    ),
    "bad-owner": _VALID.replace('Outcome = "local"', 'Outcome = "nobody"'),
    "long-ref": _VALID.replace("example-service://ABC-1", "x" * 5000),
}


def test_the_scan_reaches_source_authority_blocks() -> None:
    texts = _texts()
    assert sum(len(_BLOCK.findall(text)) for _, text in texts) >= 3


@pytest.mark.parametrize("name", sorted(_EDGE_CASES))
def test_the_ported_parser_matches_on_each_edge_case(parsers: tuple[Any, Any], name: str) -> None:
    ported, source = parsers
    assert _outcome(ported, _EDGE_CASES[name]) == _outcome(source, _EDGE_CASES[name])


def test_edge_cases_cover_both_outcomes(parsers: tuple[Any, Any]) -> None:
    kinds = {_outcome(parsers[1], text)[0] for text in _EDGE_CASES.values()}
    assert kinds == {"accept", "refuse"}


def test_the_ported_parser_matches_on_every_repository_block(parsers: tuple[Any, Any]) -> None:
    ported, source = parsers
    checked = 0
    for relative, text in _texts():
        for candidate in (text, *_BLOCK.findall(text)):
            assert _outcome(ported, candidate) == _outcome(source, candidate), relative
            checked += 1
    assert checked >= 3
