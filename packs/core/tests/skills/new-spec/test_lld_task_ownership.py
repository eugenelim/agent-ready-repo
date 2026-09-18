"""LLD task-ownership documentation contracts for new-spec."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
PLAN_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"

LLD_SECTION = re.compile(
    r"^## Design \(LLD\)\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
LLD_SUBSECTION = re.compile(
    r"^### (?P<title>.+?)\n(?P<body>.*?)(?=^### |^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
# The template documents the field; it does not carry a decision. A concrete
# value here would be copied verbatim into every plan authored from it, which
# is why this matches the documented slot rather than a task-ID list.
OWNED_BY_FIELD = re.compile(r"^(?:<!--\s*)?Owned by: \S.*$", re.MULTILINE)

# The documented form the slot must teach: a comma-separated list whose members
# may carry the lettered suffix. Asserted against the example the slot shows,
# because that example is the only statement of the form a plan author reads.
DOCUMENTED_FORM = re.compile(r"T[0-9]+[a-z]?, T[0-9]+[a-z]?")


def _lld_subsections(text: str) -> list[re.Match[str]]:
    """Return the Design (LLD) sub-sections from a plan template."""
    section = LLD_SECTION.search(text)
    assert section is not None
    return list(LLD_SUBSECTION.finditer(section.group("body")))


def _assert_lld_task_ownership(text: str) -> None:
    """Assert each LLD sub-section documents its owning task IDs."""
    subsections = _lld_subsections(text)

    assert len(subsections) == 9
    missing = [
        subsection.group("title")
        for subsection in subsections
        if OWNED_BY_FIELD.search(subsection.group("body")) is None
    ]
    assert not missing, f"LLD sub-sections missing Owned by: {missing}"

    unformed = [
        subsection.group("title")
        for subsection in subsections
        if not DOCUMENTED_FORM.search(
            OWNED_BY_FIELD.search(subsection.group("body")).group(0)
        )
    ]
    assert not unformed, (
        "Owned by: slots that do not document the comma-separated, "
        f"suffix-capable task-ID form: {unformed}"
    )


def test_lld_subsections_document_owning_task_ids() -> None:
    _assert_lld_task_ownership(PLAN_ASSET.read_text(encoding="utf-8"))


def test_lld_task_ownership_rejects_a_missing_non_first_field() -> None:
    text = PLAN_ASSET.read_text(encoding="utf-8")
    lld_section = LLD_SECTION.search(text)
    assert lld_section is not None
    subsection = _lld_subsections(text)[1]
    owned_by = OWNED_BY_FIELD.search(subsection.group("body"))
    assert owned_by is not None

    start = lld_section.start("body") + subsection.start("body") + owned_by.start()
    end = lld_section.start("body") + subsection.start("body") + owned_by.end()
    mutated = text[:start] + text[end:]

    with pytest.raises(AssertionError, match="Data & schema"):
        _assert_lld_task_ownership(mutated)


# The template documents the field inside an HTML comment; an authored plan
# writes it plainly. A HALF-wrapped field is neither: an unopened closer is
# stray text, and an unclosed opener means a comment is swallowing the rest of
# the plan. Either reading as a satisfied declaration would let an ownership
# obligation pass on a broken document.
HALF_WRAPPED = ("<!-- Owned by: T1", "Owned by: T1 -->")
WELL_FORMED = ("Owned by: T1", "<!-- Owned by: T1 -->")


def _checker_owned_by():
    import importlib.util

    path = PACK_ROOT / ".apm/skills/new-spec/scripts/lint-contract-item-alignment.py"
    # Unique module name: several skills ship same-named scripts, and a bare
    # name binds whichever directory reached sys.path first.
    spec = importlib.util.spec_from_file_location(
        "core_new_spec_lint_contract_item_alignment", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OWNED_BY


@pytest.mark.parametrize("text", WELL_FORMED)
def test_a_well_formed_owned_by_field_is_recognised(text: str) -> None:
    assert _checker_owned_by().findall(text)


@pytest.mark.parametrize("text", HALF_WRAPPED)
def test_a_half_wrapped_owned_by_field_is_not_a_declaration(text: str) -> None:
    assert not _checker_owned_by().findall(text)
