"""Pins the `Risk triggers:` spec header against its three homes.

The spec metadata contract owns the token table, `work-loop`'s risk-trigger
block owns the trigger names, and the spec-status lint owns the token set. A
trigger added to the block without a token, or a token the lint does not know,
would leave the record unable to say which triggers fired.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm" / "skills"
CONTRACT = SKILLS / "new-spec" / "references" / "spec-and-plan-contract.md"
TEMPLATE = SKILLS / "new-spec" / "assets" / "spec.md"
WORK_LOOP = SKILLS / "work-loop" / "SKILL.md"

_HEADER_LINE = "- **Risk triggers:**"


def _contract_table() -> list[tuple[str, str]]:
    """Return the (token, trigger) rows under the contract's Risk triggers bullet."""
    text = CONTRACT.read_text(encoding="utf-8")
    start = text.index("- **Risk triggers.**")
    end = text.index("\n### ", start)
    rows = re.findall(r"^\s*\| `([a-z-]+)` \| ([^|]+?) \|$", text[start:end], re.MULTILINE)
    return [(token, trigger.strip()) for token, trigger in rows]


def _block_labels() -> list[str]:
    """Return the bold bullet labels between the risk-trigger markers, in order."""
    text = WORK_LOOP.read_text(encoding="utf-8")
    start = text.index("<!-- risk-triggers:start")
    end = text.index("risk-triggers:end -->", start)
    return re.findall(r"^- \*\*([^*]+)\*\*", text[start:end], re.MULTILINE)


def test_contract_table_lists_every_risk_trigger_in_block_order() -> None:
    rows = _contract_table()
    assert rows, "the contract has no Risk triggers token table"
    assert [trigger for _token, trigger in rows] == _block_labels()


def test_contract_tokens_are_distinct() -> None:
    tokens = [token for token, _trigger in _contract_table()]
    assert len(tokens) == len(set(tokens))
    assert "none" not in tokens


def test_template_carries_exactly_one_risk_triggers_line() -> None:
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    assert sum(line.startswith(_HEADER_LINE) for line in lines) == 1


def _load_lint() -> types.ModuleType:
    """Load the spec-status lint under a pack-and-skill-qualified name."""
    path = SKILLS / "work-loop" / "scripts" / "lint-spec-status.py"
    spec = importlib.util.spec_from_file_location("core_work_loop_lint_spec_status_rtr", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    stdout, stderr = sys.stdout, sys.stderr
    try:
        spec.loader.exec_module(module)
    finally:
        sys.stdout, sys.stderr = stdout, stderr
    return module


def test_lint_token_set_equals_the_contract_table() -> None:
    tokens = {token for token, _trigger in _contract_table()}
    assert set(_load_lint().RISK_TRIGGER_TOKENS) == tokens
