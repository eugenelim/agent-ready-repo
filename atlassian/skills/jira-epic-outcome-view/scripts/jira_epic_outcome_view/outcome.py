"""Read an Epic's outcome out of the one fixed location, and nowhere else.

The outcome lives in the Epic's ``description`` field, in the block under
a top-level ``Outcome`` heading. That location is fixed and is not
configurable per invocation: two teams reading the same view from two
different locations is the drift this convention exists to prevent.

Jira returns a description in two shapes. Cloud REST v3 returns a
structured document; Server and Data Center REST v2 return plain or wiki
text. A reader that handles one shape returns nothing on the other, and
nothing is indistinguishable from an Epic that never recorded an outcome
-- so both shapes are read here, by one reader, against one grammar.

Nothing in this module writes, and nothing in it invents text. Where the
location is empty the answer is ``None``, which the view renders as an
explicit absence.
"""
from __future__ import annotations

import re
from collections.abc import Collection, Iterator, Mapping, Sequence
from typing import Any

#: The heading that opens the block, compared case-insensitively after
#: trimming. "Top-level" describes the block's position in the
#: description, not a required heading level.
HEADING_TEXT = "outcome"

#: The location, named once. The reader, the prompt and the paste-ready
#: text all have to mean the same place; three separately worded strings
#: drift, and a team then pastes into somewhere the reader does not look.
OUTCOME_LOCATION = (
    'the Epic\'s "description" field, in the block under a top-level '
    '"Outcome" heading'
)

# A Markdown ATX heading is one to six hashes and then a space; seven
# hashes is not a heading. A Confluence wiki heading is h1. to h6. and
# then a space. Setext underlining is deliberately not recognised: it
# would make any line followed by dashes a heading, and a description
# with a horizontal rule in it would then terminate the block early.
_ATX_HEADING = re.compile(r"^#{1,6}[ \t]+(.*)$")
_WIKI_HEADING = re.compile(r"^h[1-6]\.[ \t]+(.*)$")

# Nodes that hold their siblings apart. Siblings join with one newline
# when any of them is one of these, and concatenate with no separator
# otherwise. The test is on the block set rather than on an inline
# allowlist because ADF keeps gaining inline types: an unlisted one --
# `inlineExtension`, `mediaInline`, `placeholder` -- would otherwise
# split the whole paragraph it sits in, plain text siblings and all.
_BLOCK_TYPES = frozenset(
    {
        "blockCard", "blockquote", "bulletList", "codeBlock", "decisionItem",
        "decisionList", "embedCard", "expand", "extension", "bodiedExtension",
        "heading", "layoutColumn", "layoutSection", "listItem", "mediaGroup",
        "mediaSingle", "multiBodiedExtension", "nestedExpand", "orderedList",
        "panel", "paragraph", "rule", "table", "tableCell", "tableHeader",
        "tableRow", "taskItem", "taskList",
    }
)

#: The deepest ADF nesting this reader will descend. Jira accepts a
#: description of 32,767 characters, which is enough to nest containers
#: far past the interpreter's own recursion limit -- and a `RecursionError`
#: raised here would take down the whole view rather than one Epic's
#: outcome. Past this depth the answer is no outcome for that Epic, which
#: is the same answer an empty block gives and leaves the rest readable.
MAX_NESTING_DEPTH = 100


class _TooDeeplyNested(Exception):
    """An ADF description nested past ``MAX_NESTING_DEPTH``."""


class OutcomeAnswerError(Exception):
    """An ``--outcome`` argument this view refuses rather than guesses at.

    Refusing is the safe direction in all three cases it covers. Silently
    ignoring a key outside the scope loses the words a team just typed,
    and picking the first or last of two answers for one key discards one
    of them without saying which.
    """


def extract_outcome(description: Any) -> str | None:
    """The recorded outcome for one Epic, verbatim, or ``None``.

    ``None`` is returned for a description with no ``Outcome`` heading,
    for a heading whose block is empty, and for an Epic with no
    description at all. Those are the same answer to a reader: nothing is
    recorded. Treating only the first as absent renders a blank for the
    others.

    Verbatim means the block's text with leading and trailing blank lines
    removed and nothing else changed -- no reflowing and no Markdown
    rendering.
    """
    if isinstance(description, Mapping):
        return _from_document(description)
    if isinstance(description, str):
        return _from_text(description)
    return None


def parse_answers(
    values: Sequence[str] | None, *, epic_keys: Collection[str]
) -> dict[str, str]:
    """The team's answers, keyed by Epic, from repeatable ``--outcome``.

    ``EPIC-KEY=`` with empty text is a decline and is dropped here, which
    leaves that Epic rendering the prompt exactly as an omitted argument
    does. A key outside the queried scope and a key given twice are both
    refused, because either one would quietly lose an answer.
    """
    answers: dict[str, str] = {}
    seen: set[str] = set()
    for value in values or ():
        key, separator, text = value.partition("=")
        key = key.strip()
        if not separator or not key:
            raise OutcomeAnswerError(
                f"--outcome expects EPIC-KEY=<text>, and got {value!r}"
            )
        if key in seen:
            raise OutcomeAnswerError(
                f"--outcome was given twice for {key}. Pass one answer per Epic: "
                f"keeping either of two answers would discard the other."
            )
        seen.add(key)
        if key not in epic_keys:
            raise OutcomeAnswerError(
                f"--outcome names {key}, which is not an Epic in the queried scope. "
                f"Nothing was rendered for it, so the words would have been lost."
            )
        if text.strip():
            answers[key] = text
    return answers


def _from_text(description: str) -> str | None:
    """The block under the first ``Outcome`` heading in a text description."""
    block: list[str] | None = None
    for line in description.splitlines():
        title = _heading_title(line)
        if block is None:
            if title is not None and title.strip().lower() == HEADING_TEXT:
                block = []
            continue
        if title is not None:
            # The next heading of any level closes the block. A second
            # Outcome heading is one of those: the first opens the block
            # and the rest are ignored rather than merged, because
            # merging silently concatenates two authors' answers.
            break
        block.append(line)
    return None if block is None else _trimmed(block)


def _heading_title(line: str) -> str | None:
    """The heading's text, or ``None`` when the line is not a heading."""
    for pattern in (_ATX_HEADING, _WIKI_HEADING):
        match = pattern.match(line)
        if match is not None:
            return match.group(1)
    return None


def _from_document(description: Mapping[str, Any]) -> str | None:
    """The block under the first ``Outcome`` heading in an ADF description."""
    try:
        return _document_block(description)
    except _TooDeeplyNested:
        # One unreadable description is one Epic with no outcome. Letting
        # the error out would withhold every other Epic's reading too.
        return None


def _document_block(description: Mapping[str, Any]) -> str | None:
    block: list[str] | None = None
    for node in _document_order(description, 0):
        if node.get("type") == "heading":
            if block is not None:
                break
            if _node_text(node, 0).strip().lower() == HEADING_TEXT:
                block = []
            continue
        if block is not None:
            block.append(_node_text(node, 0))
    if block is None:
        return None
    return _trimmed("\n".join(block).splitlines())


def _document_order(node: Mapping[str, Any], depth: int) -> Iterator[Mapping[str, Any]]:
    """The document's nodes in order, with every heading surfaced.

    A container is yielded whole unless it holds a heading somewhere
    inside it, in which case the walk descends into it. Testing only the
    document's direct children would let a heading inside a `panel`, an
    `expand`, a `blockquote` or a `layoutColumn` pass as ordinary text,
    and the container plus everything after it would render as the team's
    outcome. The text reader already ends the block at a heading of any
    level, so a document reader that does not disagrees with it on the
    same description.
    """
    _check_depth(depth)
    for child in _child_nodes(node):
        if child.get("type") == "heading":
            yield child
        elif _holds_heading(child, depth + 1):
            yield from _document_order(child, depth + 1)
        else:
            yield child


def _holds_heading(node: Mapping[str, Any], depth: int) -> bool:
    _check_depth(depth)
    return any(
        child.get("type") == "heading" or _holds_heading(child, depth + 1)
        for child in _child_nodes(node)
    )


def _check_depth(depth: int) -> None:
    if depth > MAX_NESTING_DEPTH:
        raise _TooDeeplyNested(depth)


def _child_nodes(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    content = node.get("content") or []
    if not isinstance(content, list):
        return []
    return [child for child in content if isinstance(child, Mapping)]


def _node_text(node: Mapping[str, Any], depth: int) -> str:
    """One node's text, by the traversal the verbatim rule pins.

    Each descendant text node in document order; a ``hardBreak`` as a
    newline; inline siblings concatenated with no separator; sibling
    block nodes -- paragraphs, list items -- joined with a single
    newline. The descent is depth-bounded: an over-nested description
    raises rather than exhausting the interpreter's stack.
    """
    _check_depth(depth)
    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text") or "")
    if node_type == "hardBreak":
        return "\n"
    children = _child_nodes(node)
    if not children:
        return ""
    separator = (
        "\n" if any(child.get("type") in _BLOCK_TYPES for child in children) else ""
    )
    return separator.join(_node_text(child, depth + 1) for child in children)


def _trimmed(lines: Sequence[str]) -> str | None:
    """The block with leading and trailing blank lines dropped, or ``None``.

    Nothing inside the block is touched: no line is re-wrapped, no
    trailing space on a content line is stripped, and no markup is
    rendered. A block that is empty once the blank lines are gone is the
    present-but-empty case, which is no outcome recorded.
    """
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end]) or None
