"""The router's side of the ordinal contract.

`test_intent_ordinal.py` proves what the allocator returns; it never opens
`SKILL.md`, so it cannot see whether the router invokes it, guards its output,
or survives a refusal. Those claims are about the procedure, so this file reads
the procedure. Every expected token is derived from the allocator module's own
mapping, so the closed table is never restated here.
"""

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True

_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SKILL = _ROOT / ".apm/skills/work-intake/SKILL.md"
_TEXT = _SKILL.read_text(encoding="utf-8")
_FLAT = " ".join(_TEXT.split())

_SPEC = importlib.util.spec_from_file_location(
    "core_work_intake_intent_ordinal_for_prose",
    _ROOT / ".apm/skills/work-intake/scripts/intent_ordinal.py",
)
MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(MODULE)


def test_the_procedure_names_the_allocator_invocation() -> None:
    """AC-0006: the integration point is stated, not left to inference.

    A router that never names the script cannot be said to invoke it, and the
    allocator's own suite would still pass.
    """
    assert "scripts/intent_ordinal.py" in _FLAT
    assert "--dir" in _FLAT and "--token" in _FLAT


def test_every_mapped_level_and_token_appears_in_the_procedure() -> None:
    """AC-0006, AC-0016: the caller resolves `Level` from a closed table."""
    for level, token in MODULE.LEVEL_TOKENS.items():
        assert f"`{level}`" in _FLAT, f"{level} missing from the router table"
        assert f"`{token}`" in _FLAT, f"{token} missing from the router table"


def test_the_procedure_passes_a_token_never_the_level_string() -> None:
    """AC-0016: no adopter-controlled string reaches the command line.

    `Level` is adopter-controlled and this skill runs a shell, so the rule has
    to be stated where the invocation is, not only in the spec.
    """
    assert "pass only the resulting token" in _FLAT
    assert "never the `Level` string itself" in _FLAT


def test_an_unmapped_level_skips_the_invocation() -> None:
    """AC-0007, AC-0016: unmapped means no command runs at all."""
    assert "skip the allocation entirely" in _FLAT
    assert "/intents/<slug>.md" in _FLAT


def test_the_returned_ordinal_is_validated_before_it_becomes_a_path() -> None:
    """AC-0016: a malformed return must not compose a destination."""
    assert "^<TOKEN>-[0-9]{4,}$" in _FLAT


def test_a_refusal_never_stops_an_admission() -> None:
    """AC-0007, AC-0010: the branch that keeps the intent existing.

    This is the criterion the owner reversed a drifting spec over: a refused
    ordinal changes the filename, never whether the intent was admitted.
    """
    assert "Exit 1 never stops an admission" in _FLAT
    assert "Use the unprefixed destination" in _FLAT
    assert "Report no failure to the operator" in _FLAT


def test_the_procedure_states_every_refusal_cause() -> None:
    """AC-0010, AC-0024: the cause vocabulary is closed and carried across."""
    for cause in MODULE.REFUSAL_CAUSES:
        assert f"`{cause}`" in _FLAT, f"{cause} missing from the router prose"


def test_the_router_still_forbids_renaming_an_existing_artifact() -> None:
    """AC-0007: forward-only adoption, which a renaming router would break."""
    assert "Never rename an artifact that already exists" in _FLAT
