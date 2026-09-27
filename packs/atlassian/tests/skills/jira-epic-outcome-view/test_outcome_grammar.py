"""The heading grammar and what "verbatim" preserves.

One grammar, so one reader is determinate. Two readers that disagree
about which line is a heading, or about how a structured document turns
into text, both return something and both call it the outcome -- and the
team never learns which one it is reading.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def outcome(load_module):
    return load_module("outcome")


def _adf(*nodes: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(nodes)}


def _heading(text: str, level: int = 2) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _para(*nodes: dict) -> dict:
    return {"type": "paragraph", "content": list(nodes)}


def _text(text: str) -> dict:
    return {"type": "text", "text": text}


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        pytest.param("h2. Outcome\nCustomers self-serve.\n", "Customers self-serve.",
                     id="confluence-wiki-heading"),
        pytest.param("###### Outcome\nCustomers self-serve.\n", "Customers self-serve.",
                     id="deepest-markdown-heading"),
        pytest.param("## OUTCOME\nCustomers self-serve.\n", "Customers self-serve.",
                     id="case-insensitive"),
        pytest.param("##   Outcome   \nCustomers self-serve.\n", "Customers self-serve.",
                     id="heading-text-is-trimmed"),
    ],
)
def test_the_heading_is_recognised_across_the_grammar(outcome, description, expected):
    """Any level, either markup, any capitalisation. "Top-level" is about
    where the block sits, not which level the heading uses."""
    assert outcome.extract_outcome(description) == expected


@pytest.mark.parametrize(
    ("description", "reason"),
    [
        pytest.param("Outcome\n=======\nCustomers self-serve.\n",
                     "setext underlining is not a heading", id="setext-equals"),
        pytest.param("Outcome\n-------\nCustomers self-serve.\n",
                     "setext underlining is not a heading", id="setext-dashes"),
        pytest.param("####### Outcome\nCustomers self-serve.\n",
                     "seven hashes is not a heading", id="seven-hashes"),
        pytest.param("#Outcome\nCustomers self-serve.\n",
                     "a heading marker needs a space after it", id="no-space"),
        pytest.param("h7. Outcome\nCustomers self-serve.\n",
                     "wiki headings stop at h6", id="wiki-h7"),
    ],
)
def test_what_the_grammar_does_not_admit(outcome, description, reason):
    """Recognising setext underlining would make any line above a rule a
    heading, so a description with a horizontal rule in it would end the
    block early and the reader would silently return half an outcome."""
    assert outcome.extract_outcome(description) is None, reason


def test_a_second_outcome_heading_is_ignored_rather_than_merged(outcome):
    """Merging would join two people's answers into one paragraph and
    present the result as something the team wrote."""
    description = (
        "## Outcome\nCustomers self-serve.\n\n"
        "## Outcome\nSomething else entirely.\n"
    )

    extracted = outcome.extract_outcome(description)

    assert extracted == "Customers self-serve."
    assert "Something else entirely." not in extracted


def test_a_nested_heading_closes_the_block(outcome):
    """A deeper heading terminates the block like any other heading."""
    description = "## Outcome\nCustomers self-serve.\n### Detail\nNot the outcome.\n"

    assert outcome.extract_outcome(description) == "Customers self-serve."


def test_verbatim_changes_nothing_inside_the_block(outcome):
    """Blank lines above and below go; everything inside stays. No
    re-wrapping, no list rendering, no markdown collapsed away."""
    block = "  Customers self-serve.\n\n- one\n- two\n\n    indented tail"
    description = f"## Outcome\n\n\n{block}\n\n\n## Scope\nLater.\n"

    assert outcome.extract_outcome(description) == block


def test_a_structured_document_joins_blocks_with_one_newline(outcome):
    """Sibling block nodes -- paragraphs and list items -- join with a
    single newline. Without the rule, two readers produce different text
    and both call it verbatim."""
    description = _adf(
        _heading("Outcome", level=4),
        _para(_text("Customers self-serve.")),
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [_para(_text("one"))]},
                {"type": "listItem", "content": [_para(_text("two"))]},
            ],
        },
        _heading("Scope"),
        _para(_text("Not the outcome.")),
    )

    assert outcome.extract_outcome(description) == "Customers self-serve.\none\ntwo"


def test_a_structured_document_concatenates_inline_nodes(outcome):
    """Inline siblings concatenate with no separator, and a hard break
    becomes a newline. Inserting a space between inline nodes would
    change the team's words while claiming to reproduce them."""
    description = _adf(
        _heading("Outcome"),
        _para(
            _text("Customers "),
            {"type": "text", "text": "self-serve", "marks": [{"type": "strong"}]},
            _text("."),
            {"type": "hardBreak"},
            _text("Support handles the rest."),
        ),
    )

    assert (
        outcome.extract_outcome(description)
        == "Customers self-serve.\nSupport handles the rest."
    )


def test_the_surrounding_document_is_not_read_as_outcome(outcome):
    """The description is shared with scope and acceptance criteria."""
    description = _adf(
        _para(_text("Scope: self-serve only.")),
        _heading("Outcome"),
        _para(_text("Customers self-serve.")),
        _heading("Acceptance criteria"),
        _para(_text("Returns portal ships.")),
    )

    assert outcome.extract_outcome(description) == "Customers self-serve."


def test_a_heading_nested_in_a_container_closes_the_block(outcome):
    """The structured-document twin of the text case above. A heading
    inside a `panel`, an `expand`, a `blockquote` or a `layoutColumn` is
    still a heading: reading only the document's direct children swallows
    it, and the container plus everything after it renders as the team's
    outcome. One shape working and the other not is exactly the asymmetry
    one grammar for both readers exists to prevent."""
    description = _adf(
        _heading("Outcome"),
        _para(_text("Customers self-serve.")),
        {
            "type": "panel",
            "attrs": {"panelType": "info"},
            "content": [_heading("Detail", level=3), _para(_text("Not the outcome."))],
        },
    )

    extracted = outcome.extract_outcome(description)

    assert extracted == "Customers self-serve."
    assert "Not the outcome." not in extracted


def test_a_container_with_no_heading_is_still_read_as_block_text(outcome):
    """The other side of that rule: descending is for terminating the
    block, not for dropping the text of a container that holds none."""
    description = _adf(
        _heading("Outcome"),
        {
            "type": "blockquote",
            "content": [_para(_text("Customers self-serve.")), _para(_text("Twice."))],
        },
    )

    assert outcome.extract_outcome(description) == "Customers self-serve.\nTwice."


def test_an_unlisted_inline_node_does_not_split_its_paragraph(outcome):
    """ADF keeps gaining inline types. Choosing the separator from a closed
    inline allowlist makes one unrecognised sibling -- `inlineExtension`,
    `mediaInline`, `placeholder` -- split the whole paragraph, plain text
    siblings and all, and the team's sentence arrives in pieces."""
    description = _adf(
        _heading("Outcome"),
        _para(
            _text("Customers "),
            {"type": "inlineExtension", "attrs": {"extensionKey": "anything"}},
            _text("self-serve."),
        ),
    )

    assert outcome.extract_outcome(description) == "Customers self-serve."


def test_a_block_sibling_still_joins_with_one_newline(outcome):
    """The separator rule is decided by block-ness, so a real block child
    must keep its newline: reading every unknown type as inline would
    concatenate two paragraphs into one line."""
    description = _adf(
        _heading("Outcome"),
        {
            "type": "blockquote",
            "content": [_para(_text("one")), _para(_text("two"))],
        },
    )

    assert outcome.extract_outcome(description) == "one\ntwo"
