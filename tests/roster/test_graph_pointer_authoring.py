#!/usr/bin/env python3
"""Construction pins: authoring sources emit only typed graph pointers.

Re-derives the bounded writer-candidate universe from the real tree, compares it
with an explicit role manifest, and fails when an author-facing source still
stamps or instructs an untyped populated ``Parent intent:`` or ``Brief:`` value.

Run with pytest.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SEARCH_ROOTS = ("packs/core", "packs/product-engineering", "docs/guides", "guides")
EXCLUDED_DIRS = frozenset(
    {
        "tests", "test", "fixtures", "fixture", "evals", "eval", "build",
        "node_modules", "__pycache__", ".git", ".venv", "venv", "dist",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }
)
MENTION = re.compile(r"Parent intent:|Brief:")

S = "packs/core/.apm/skills/"
P = "packs/product-engineering/.apm/skills/"

# path -> (role, reason). A reason is required for "excluded" only.
MANIFEST: dict[str, tuple[str, str]] = {
    S + "new-spec/assets/spec.md": ("template", ""),
    S + "new-spec/SKILL.md": ("instruction", ""),
    S + "new-spec/references/spec-and-plan-contract.md": ("instruction", ""),
    S + "author-delivery-brief/SKILL.md": ("instruction", ""),
    S + "author-delivery-brief/examples/shape-a-outcome-brief.md": ("example", ""),
    S + "author-delivery-brief/examples/shape-b-story-list-brief.md": ("example", ""),
    "packs/core/seeds/docs/product/briefs/_template.md": ("template", ""),
    P + "intent/assets/intent-template.md": ("template", ""),
    P + "align-value-stream/assets/rollup-template.md": ("template", ""),
    P + "intent/SKILL.md": ("instruction", ""),
    P + "intent/references/decompose.md": ("instruction", ""),
    P + "intent/references/recursive-decomposition.md": ("instruction", ""),
    "guides/core/reference/product-brief-fields.md": ("instruction", ""),
    "guides/core/how-to/start-the-work.md": ("instruction", ""),
    "guides/core/how-to/close-and-disposition-work.md": ("instruction", ""),
    "guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md": ("instruction", ""),
    "guides/core/explanation/why-a-brief-layer.md": ("instruction", ""),
    "guides/product-engineering/reference/intent-fields-and-modes.md": ("instruction", ""),
    "guides/product-engineering/how-to/shape-a-product-strategy.md": ("instruction", ""),
    S + "navigate-intents/SKILL.md": (
        "excluded", "describes which pointer fields the reader follows; writes none"),
    S + "workspace-status/references/agentbundle-layout.md": (
        "excluded", "names the Brief: chain as a path-layout constraint; writes none"),
    "packs/core/DESIGN.md": ("excluded", "design record of the reader; writes no field"),
    P + "align-value-stream/references/cross-component-rollup.md": (
        "excluded", "describes how coverage reads Brief: back-links; writes none"),
    "guides/core/how-to/navigate-intents.md": (
        "excluded", "describes the reader's output; writes no field"),
    "guides/core/how-to/run-a-live-demo.md": (
        "excluded", "quotes `Brief: none` as demo output only"),
    "guides/core/reference/spec-shape-and-lld.md": (
        "excluded", "link text naming the sibling fields; writes no value"),
}
ROLES = {"instruction", "template", "example", "generated-copy", "excluded"}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def derive_candidates() -> set[str]:
    """Return repo-relative Markdown paths that mention either governed field."""
    found: set[str] = set()
    for top in SEARCH_ROOTS:
        base = ROOT / top
        for path in base.rglob("*.md"):
            parts = path.relative_to(base).parts
            if any(p in EXCLUDED_DIRS for p in parts[:-1]):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            if MENTION.search(path.read_text(encoding="utf-8")):
                found.add(path.relative_to(ROOT).as_posix())
    return found


# --- detection predicates -------------------------------------------------

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_BRIEF_HDR = re.compile(r"^\s*(?:[-*]\s+)?\*\*Brief:\*\*(.*)$", re.M)
_PARENT_HDR = re.compile(r"^\s*(?:[-*]\s+)?\*\*Parent intent:\*\*(.*)$", re.M)
_TYPED_BRIEF = re.compile(r"^`?brief:[A-Za-z0-9<>_-]+`?$")
_TYPED_PARENT = re.compile(r"^`?[a-z<][a-z0-9<>_-]*:[A-Za-z0-9<>_-]+`?$")
_NONE = re.compile(r"^none\b", re.I)
# The one allowed legacy sentence: readers (never authors) accept old paths.
_LEGACY_READER = re.compile(
    r"\b(?:readers?\s+(?:still\s+)?(?:keep\s+)?accept(?:ing|s)?)\b[^.]*\blegacy\b", re.I)
_PATH_OFFER = re.compile(
    r"docs/product/briefs/<slug>\.md|repository-relative path|accepted fallback", re.I)


def untyped_header_values(text: str) -> list[str]:
    """Header lines whose populated value is not a typed pointer.

    Comments are stripped first, so an empty value with only a comment passes.
    A value is acceptable when empty, when its first word is ``none``, or when
    it is ``brief:<slug>`` (Brief) or ``<kind>:<slug>`` (Parent intent),
    including the angle-bracket placeholders the templates use.
    """
    bad: list[str] = []
    for rx, typed in ((_BRIEF_HDR, _TYPED_BRIEF), (_PARENT_HDR, _TYPED_PARENT)):
        for m in rx.finditer(text):
            val = _COMMENT.sub("", m.group(1)).strip()
            if not val or _NONE.match(val) or typed.match(val):
                continue
            bad.append(m.group(0).strip())
    return bad


def path_offers(text: str) -> list[str]:
    """Sentences that offer a repository path or fallback as a Brief value to write.

    Only paragraphs that discuss the ``Brief:`` field or its back-link are
    inspected, sentence by sentence. A sentence phrased as reader behaviour
    ("Readers still accept a legacy repository path ...") is allowed.
    """
    bad: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        flat = " ".join(para.split())
        if "Brief:" not in flat and "back-link" not in flat:
            continue
        for sent in re.split(r"(?<=[.;])\s+(?=[A-Z`<*-])", flat):
            if _PATH_OFFER.search(sent) and not _LEGACY_READER.search(sent):
                bad.append(sent)
    return bad


def never_interpreted(text: str) -> list[str]:
    """Lines saying Parent intent is provenance that is never interpreted."""
    return [
        ln.strip()
        for ln in text.splitlines()
        if "Parent intent:" in ln and re.search(r"never interpreted|provenance only", ln, re.I)
    ]


def authoring_gaps(rel: str, text: str) -> list[str]:
    gaps = [f"{rel}: untyped header: {v}" for v in untyped_header_values(text)]
    gaps += [f"{rel}: path offered: {s}" for s in path_offers(text)]
    gaps += [f"{rel}: stale parent meaning: {s}" for s in never_interpreted(text)]
    return gaps


# --- VI-2001: universe, manifest, remaining gaps ----------------------------


def test_manifest_roles_are_valid_and_exclusions_have_reasons() -> None:
    for rel, (role, reason) in MANIFEST.items():
        assert role in ROLES, rel
        assert (role != "excluded") or reason, f"{rel}: exclusion needs a reason"


def test_every_candidate_is_classified_and_no_entry_is_stale() -> None:
    derived = derive_candidates()
    unclassified = sorted(derived - MANIFEST.keys())
    stale = sorted(MANIFEST.keys() - derived)
    assert not unclassified, f"candidates missing from manifest: {unclassified}"
    assert not stale, f"manifest entries no longer candidates: {stale}"


def test_no_authoring_source_writes_an_untyped_populated_pointer() -> None:
    gaps: list[str] = []
    for rel, (role, _reason) in sorted(MANIFEST.items()):
        if role == "excluded":
            continue
        gaps += authoring_gaps(rel, _read(rel))
    assert not gaps, "\n".join(gaps)


# --- predicate self-checks: each predicate must be able to fail --------------


@pytest.mark.parametrize(
    "line",
    [
        "- **Brief:** docs/product/briefs/x.md",
        "- **Brief:** my-brief",
        "- **Brief:** `docs/product/briefs/x.md` <!-- note -->",
        "- **Parent intent:** my-intent",
        "- **Parent intent:** docs/product/intents/x.md",
        "- **Parent intent:** [x](docs/product/intents/x.md)",
    ],
)
def test_untyped_header_predicate_fails_on_untyped_values(line: str) -> None:
    assert untyped_header_values(line)


@pytest.mark.parametrize(
    "line",
    [
        "- **Brief:** brief:my-brief",
        "- **Brief:** <!-- optional -->",
        "- **Brief:** none",
        "- **Brief:** None, authored directly",
        "- **Parent intent:** `<kind>:<slug>` <!-- x -->",
        "- **Parent intent:** `intent:account-self-service`",
        "- **Parent intent:** <!-- none; received directly -->",
        "# Brief: A heading is not a header",
    ],
)
def test_untyped_header_predicate_passes_typed_or_empty_values(line: str) -> None:
    assert not untyped_header_values(line)


def test_path_offer_predicate_fails_on_fallback_and_passes_reader_sentence() -> None:
    old = (
        "Set the `Brief:` header to `brief:<slug>` (the path\n"
        "`docs/product/briefs/<slug>.md` is an accepted fallback)."
    )
    assert path_offers(old)
    assert path_offers("The `Brief:` back-link may be the repository-relative path.")
    ok = (
        "Write the `Brief:` header as `brief:<slug>`. "
        "Readers still accept a legacy repository path in older specs."
    )
    assert not path_offers(ok)
    assert not path_offers("A brief lives at `docs/product/briefs/<slug>.md`.")


def test_stale_parent_meaning_predicate_fails() -> None:
    assert never_interpreted("- **Parent intent:** `x:y` <!-- provenance only, never interpreted -->")
    assert never_interpreted("Parent intent: carried as provenance; never interpreted.")
    assert not never_interpreted("- **Parent intent:** `x:y` <!-- the work-loop checks it -->")


# --- VI-2002: content pins ---------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "packs/core/seeds/docs/product/briefs/_template.md",
        S + "author-delivery-brief/examples/shape-a-outcome-brief.md",
    ],
)
def test_parent_intent_comment_names_a_parent_pointer(rel: str) -> None:
    line = next(ln for ln in _read(rel).splitlines() if "**Parent intent:**" in ln)
    for phrase in (
        "registered kind and `Slug:`",
        "`intent:<slug>`",
        "names an existing intent when the brief changes",
        "Distinct from `Epic:`",
    ):
        assert phrase in line, f"{rel}: missing {phrase!r}"
    for banned in ("never interpreted", "provenance only", "provenance;"):
        assert banned not in line


def test_field_guide_passage() -> None:
    text = " ".join(_read("guides/core/reference/product-brief-fields.md").split())
    for phrase in (
        "Write a brief's `Parent intent:` as the target intent's registered kind and `Slug:`",
        "`outcome:service-reliability` or `intent:account-self-service`",
        "Write a spec's `Brief:` as `brief:<slug>`",
        "New and changed artifacts are checked",
        "Readers keep accepting legacy repository paths in those older artifacts",
        "An absent value or a value beginning with the word `none` records no pointer",
    ):
        assert phrase in text, phrase


def test_work_loop_guide_passage() -> None:
    text = " ".join(_read("guides/core/how-to/start-the-work.md").split())
    for phrase in (
        "Before completing a change, the work-loop checks all active `Parent intent:` and `Brief:` fields",
        "each artifact the change adds or modifies",
        "A typed pointer must name an existing target of the field's type",
        "A body-only edit still selects that artifact for checking",
    ):
        assert phrase in text, phrase
