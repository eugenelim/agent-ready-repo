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
    S + "work-intake/SKILL.md": ("instruction", ""),
    S + "work-intake/references/lifecycle-index.md": ("instruction", ""),
    S + "workspace-status/references/mutate.md": ("instruction", ""),
    "guides/core/reference/workspace-toml-schema.md": ("instruction", ""),
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


_RESEARCH_PATH = re.compile(r"research or notes", re.I)


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
            if _RESEARCH_PATH.search(sent) and "Discovery" in flat and "Brief:" not in sent:
                continue  # a research or notes path in a Discovery passage, not a Brief value
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


def test_path_offer_predicate_exempts_discovery_research_paths() -> None:
    assert not path_offers(
        "Discovery: sits next to Brief:. When it names a research or notes file, "
        "use its repository-relative path.")
    assert path_offers("Brief: may be the repository-relative path.")
    assert path_offers(
        "Brief: may be the repository-relative path, like a research or notes file.")
    assert path_offers(
        "Discovery or Brief: may be the repository-relative path, like a research or notes file.")


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
        "Before completing a change, the work-loop checks all active `Parent intent:`, `Brief:`, and `Discovery:` fields",
        "each artifact the change adds or modifies",
        "A typed pointer must name an existing target of the field's type",
        "A body-only edit still selects that artifact for checking",
    ):
        assert phrase in text, phrase


# --- Discovery writers: typed intent form, repository-path provenance --------

DISCOVERY_MENTION = re.compile(r"Discovery:")
# path -> (role, reason). Instruction, template, example, generated-copy roles
# are recorded separately from excluded readers; reasons are for "excluded".
DISCOVERY_MANIFEST: dict[str, tuple[str, str]] = {
    S + "new-spec/SKILL.md": ("instruction", ""),
    S + "new-spec/references/spec-and-plan-contract.md": ("instruction", ""),
    S + "new-spec/assets/spec.md": ("template", ""),
    "guides/core/how-to/close-and-disposition-work.md": ("instruction", ""),
    "guides/core/how-to/start-the-work.md": (
        "excluded", "lists the checked fields only; instructs no value form"),
    S + "navigate-intents/SKILL.md": (
        "excluded", "describes the pointer fields the reader follows; writes none"),
    "guides/core/how-to/navigate-intents.md": (
        "excluded", "describes the reader's output; writes no field"),
    "packs/core/DESIGN.md": ("excluded", "design record of the reader; writes no field"),
    P + "discovery-loop/SKILL.md": (
        "excluded", "names the up-edge header as a lint prerequisite; instructs no value form"),
}
DISCOVERY_WRITERS = sorted(r for r, (role, _) in DISCOVERY_MANIFEST.items() if role != "excluded")
# Each kind is stated either as a typed prefix (`outcome:<slug>`) or as a bare
# kind name in backticks; `Parent intent:` does not count for the intent kind.
_TYPED_FORMS = tuple(
    re.compile(rf"(?<![\w-])(?<!Parent ){kind}:|`{kind}`")
    for kind in ("outcome", "opportunity", "capability", "intent")
)
_BARE_INTENTS_PATH = re.compile(r"docs/product/intents/")
_LEGACY = re.compile(r"\blegacy\b|older specs", re.I)


def derive_discovery_candidates() -> set[str]:
    """Return repo-relative Markdown paths that mention the ``Discovery:`` field."""
    found: set[str] = set()
    for top in SEARCH_ROOTS:
        base = ROOT / top
        for path in base.rglob("*.md"):
            parts = path.relative_to(base).parts
            if any(p in EXCLUDED_DIRS for p in parts[:-1]):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            if DISCOVERY_MENTION.search(path.read_text(encoding="utf-8")):
                found.add(path.relative_to(ROOT).as_posix())
    return found


def discovery_path_offers(text: str) -> list[str]:
    """Sentences naming ``Discovery:`` that offer a bare intents path as the form to write."""
    bad: list[str] = []
    for para in re.split(r"\n\s*\n|\n(?=\s*- )", text):
        flat = " ".join(para.split())
        if "Discovery:" not in flat:
            continue
        for sent in re.split(r"(?<=[.;])\s+(?=[A-Z`<*-])", flat):
            if "Discovery:" in sent and _BARE_INTENTS_PATH.search(sent) and not _LEGACY.search(sent):
                bad.append(sent)
    return bad


def discovery_form_gaps(text: str) -> list[str]:
    """Typed forms missing from every passage that names ``Discovery:``.

    A passage is a paragraph or list item. One passage must carry all four forms,
    so an unrelated mention elsewhere (such as ``Parent intent:``) cannot satisfy it.
    """
    passages = [
        " ".join(p.split())
        for p in re.split(r"\n\s*\n|\n(?=\s*- )", text)
        if "Discovery:" in p
    ]
    return min(
        ([rx.pattern for rx in _TYPED_FORMS if not rx.search(p)] for p in passages),
        key=len,
        default=[rx.pattern for rx in _TYPED_FORMS],
    )


def test_discovery_manifest_roles_are_valid_and_exclusions_have_reasons() -> None:
    for rel, (role, reason) in DISCOVERY_MANIFEST.items():
        assert role in ROLES, rel
        assert (role != "excluded") or reason, f"{rel}: exclusion needs a reason"
    assert {r for r, _ in DISCOVERY_MANIFEST.values()} >= {"instruction", "template", "excluded"}


def test_every_discovery_candidate_is_classified_and_no_entry_is_stale() -> None:
    derived = derive_discovery_candidates()
    assert not sorted(derived - DISCOVERY_MANIFEST.keys()), "unclassified Discovery candidates"
    assert not sorted(DISCOVERY_MANIFEST.keys() - derived), "stale Discovery manifest entries"


@pytest.mark.parametrize("rel", DISCOVERY_WRITERS)
def test_discovery_writer_names_typed_intent_and_repository_path_forms(rel: str) -> None:
    text = " ".join(_read(rel).split())
    assert not discovery_form_gaps(_read(rel)), rel
    assert "repository-relative path" in text, rel
    assert "registered kind" in text, rel
    assert not discovery_path_offers(_read(rel)), rel


@pytest.mark.parametrize(
    "rel",
    [S + "new-spec/SKILL.md", S + "new-spec/references/spec-and-plan-contract.md"],
)
def test_discovery_instruction_states_precedence_and_provenance_meaning(rel: str) -> None:
    text = " ".join(_read(rel).split())
    for phrase in (
        "`Kind:` takes precedence over `Level:`",
        "New and changed specs are checked for typed, live intent targets; legacy paths remain readable",
        "does not itself assert a feature-delivery route",
    ):
        assert phrase in text, f"{rel}: missing {phrase!r}"


def test_close_guide_states_the_discovery_form_once_and_entries_refer_to_it() -> None:
    text = _read("guides/core/how-to/close-and-disposition-work.md")
    form = next(
        ln for ln in text.splitlines()
        if ln.startswith("The accepted `Discovery:` form")
    )
    assert not discovery_form_gaps(form)
    for code in (
        "delivery-target-missing", "delivery-reference-malformed",
        "delivery-reference-unsafe", "artifact-not-in-graph",
    ):
        entry = next(ln for ln in text.splitlines() if ln.startswith(f"- `{code}`"))
        assert "accepted `Discovery:` form" in entry, code


def test_discovery_form_predicate_can_fail() -> None:
    full = (
        "Set `Discovery:` to `outcome:<slug>`, `opportunity:<slug>`, "
        "`capability:<slug>`, or `intent:<slug>`.\n"
    )
    assert not discovery_form_gaps(full)
    assert discovery_form_gaps("")
    assert discovery_form_gaps(full.replace("`opportunity:<slug>`, ", ""))
    other = "Write the brief's `Parent intent:` as `intent:<slug>`.\n"
    assert discovery_form_gaps(
        "Set `Discovery:` to `outcome:<slug>`, `capability:<slug>`.\n\n" + other)


def test_build_loop_guide_lists_discovery_among_checked_fields() -> None:
    text = " ".join(_read("guides/core/how-to/start-the-work.md").split())
    assert "`Parent intent:`, `Brief:`, and `Discovery:` fields" in text


def test_discovery_path_offer_predicate_can_fail() -> None:
    assert discovery_path_offers("Set `Discovery:` to `docs/product/intents/x.md`.")
    assert not discovery_path_offers(
        "Set `Discovery:` to `intent:x`. A legacy `docs/product/intents/x.md` path is readable.")
    assert not discovery_path_offers("A decision brief lives in `docs/product/intents/x.md`.")
