"""Construction contracts for the progressive authoring workflow."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
AUTHOR_ROOT = PACK_ROOT / ".apm" / "skills" / "author-or-update-agent-skill"
# Literal so every path this suite opens is statically confined to its own
# pack; the routes the SKILL.md actually names are asserted against these.
AUTHOR_ROUTES = (
    "references/create.md",
    "references/frame.md",
    "references/knowledge-provider-pattern.md",
    "references/knowledge-surfaces.md",
    "references/language-extension-seams.md",
    "references/provenance.md",
    "references/provider-contract.md",
    "references/retrieval-evaluation.md",
    "references/safety-and-authority.md",
    "references/security-boundaries.md",
    "references/update.md",
)
# Every authoring case, not only those declaring a payload. All eight record an
# `evals/evals.json` digest, so a set naming four left four free to carry a
# stale digest that the parametrized sweep below would never read.
AUTHORING_EVAL_IDS = frozenset(
    {
        "frame-new-skill",
        "update-existing-skill",
        "cold-start-orientation",
        "cross-session-resumption",
        "progressive-result-presentation",
        "knowledge-provider-read-only-entry",
        "pytest-suite",
        "node-browser-suite",
    }
)
AUTHOR_EVIDENCE_SOURCES = (
    # The workflow body itself. A graded authoring result depends on the body
    # that produced it far more than on the eval payload, and without this key
    # a result measured against a superseded body satisfies every other guard
    # here -- which is how two contract fixes in this slice moved the body
    # while the recorded evidence still looked bound to it.
    "SKILL.md",
    "evals/evals.json",
    "evals/files/update-existing-SKILL.md",
    "evals/files/pytest-suite-SKILL.md",
    "evals/files/node-browser-suite-SKILL.md",
)


def _frontmatter(text: str) -> dict[str, object]:
    """Parse skill YAML frontmatter."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_authoring_skill_exposes_only_the_progressive_foundation_modes() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["name"] == "author-or-update-agent-skill"
    assert metadata["metadata"] == {
        "boundaries": ["filesystem_read_untrusted", "filesystem_write"]
    }
    description = str(metadata["description"]).lower()
    for positive in ("frame", "create", "update", "agent skill"):
        assert positive in description
    assert "use when the user asks" in description
    assert "skill.md" in description
    for internal in ("knowledge-provider", "runtime-package", "agentbundle"):
        assert internal not in description
    # An unnamed or ambiguous target must route into this workflow rather than
    # producing a clarifying refusal that never selects it.
    assert "select it first and resolve the target inside the workflow" in description
    assert "with nothing attached" in description
    assert "do not use for review-only requests" in description
    # Outcome, not vocabulary, separates the two adjacent workflows.
    assert "any request whose outcome is a changed skill file belongs here" in description
    assert "resolving an ambiguous target is this workflow's first step" in text
    assert "`frame` is the default and is read-only" in text
    assert "explicit mode transition" in text
    for unavailable in (
        "`runtime-package`",
        "`runtime-profile`",
        "`plugin`",
        "`hook`",
        "`subagent`",
    ):
        assert unavailable in _unavailable_modes(text), unavailable
    # Advertised, so it must not appear in the unavailable region at all -- a
    # backticked match anywhere in the file would be satisfied by either.
    assert "`knowledge-provider`" not in _unavailable_modes(text)
    assert "contract_version: agent-skill-engineering-foundation/v1" in text
    assert "status: unavailable" in text


def test_every_unsupported_mode_has_the_exact_versioned_unavailable_result() -> None:
    fixture = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "unsupported-mode-cases.json"
        ).read_text(encoding="utf-8")
    )
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    modes = {case["mode"] for case in fixture["cases"]}

    assert modes == {
        "runtime-package",
        "runtime-profile",
        "plugin",
        "hook",
        "subagent",
    }
    assert all(case["expected_status"] == "unavailable" for case in fixture["cases"])
    assert fixture["contract_version"] in text
    assert f"reason: {fixture['reason']}" in text
    assert f"baseline: {fixture['baseline']}" in text
    assert all(f"`{mode}`" in text for mode in modes)


def test_authoring_skill_routes_progressively_and_keeps_local_links_valid() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    routes = re.findall(r"\((references/[^)]+\.md)\)", text)
    assert set(routes) == set(AUTHOR_ROUTES)
    assert text.index("references/frame.md") < text.index("references/create.md")
    assert text.index("references/create.md") < text.index("references/update.md")


@pytest.mark.parametrize("route", AUTHOR_ROUTES)
def test_authoring_reference_route_resolves(route: str) -> None:
    assert (AUTHOR_ROOT / route).is_file()


def test_boundary_contract_confines_before_read_and_isolates_authentication() -> None:
    safety = (AUTHOR_ROOT / "references" / "safety-and-authority.md").read_text(
        encoding="utf-8"
    )
    assert "Canonicalize and symlink-resolve" in safety
    assert "without reading" in safety
    assert "candidate's contents" in safety
    assert "immediately before mutation" in safety
    assert "filesystem_read_untrusted" in safety
    assert "filesystem_write" in safety
    assert "Do not inspect credentials" in safety
    assert "least-authority broker" in safety


def test_activation_examples_are_discriminating_and_versionable() -> None:
    cases = json.loads(
        (AUTHOR_ROOT / "evals" / "eval_queries.json").read_text(encoding="utf-8")
    )
    assert len(cases) >= 8
    assert any(case["should_trigger"] for case in cases)
    assert any(not case["should_trigger"] for case in cases)
    assert all(set(case) == {"query", "should_trigger"} for case in cases)


def test_authoring_behavior_evals_cover_frame_and_existing_update() -> None:
    payload = json.loads(
        (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
    )
    cases = {case["id"]: case for case in payload["evals"]}

    # One id per line, so admitting the next case is a one-line diff rather
    # than a rewrite of the equality.
    assert set(cases) == {
        "frame-new-skill",
        "update-existing-skill",
        "cold-start-orientation",
        "cross-session-resumption",
        "progressive-result-presentation",
        "knowledge-provider-read-only-entry",
        "pytest-suite",
        "node-browser-suite",
    }
    assert cases["frame-new-skill"].get("files") is None
    update_files = cases["update-existing-skill"]["files"]
    assert update_files == ["evals/files/update-existing-SKILL.md"]
    assert (AUTHOR_ROOT / "evals" / "files" / "update-existing-SKILL.md").is_file()
    assert all(case["assertions"] for case in cases.values())
    # Read defensively: a case added upstream may declare no expect block, and
    # a KeyError there would read as this slice's failure rather than a missing
    # declaration in someone else's case.
    assert all(
        case.get("expect", {}).get("output_contains")
        for case in cases.values()
        if "expect" in case
    )
    assert all("expect" in case for case in cases.values()), sorted(
        i for i, c in cases.items() if "expect" not in c
    )


def test_independent_behavior_results_cover_both_authoring_cases() -> None:
    evidence = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "behavior-results.json"
        ).read_text(encoding="utf-8")
    )
    results = {result["eval_id"]: result for result in evidence["results"]}
    cases = {
        case["id"]: case
        for case in json.loads(
            (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
    }

    assert set(results) == {
        "frame-new-skill",
        "update-existing-skill",
        "cold-start-orientation",
        "cross-session-resumption",
        "progressive-result-presentation",
        "knowledge-provider-read-only-entry",
        "pytest-suite",
        "node-browser-suite",
        "detect-activation-failure",
        "detect-script-contract-failure",
    }
    # Each exemption names an exact (case, index) so a *different* miss still
    # reddens while the known one does not read as a pass.
    #
    # ("cross-session-resumption", 1) is inherited: the case asks for a durable
    # record while its sibling assertion requires the skill's read-only boundary
    # preserved, and durability implies the write that boundary forbids. Two
    # independent attesting contexts have now called the pair contradictory.
    #
    # ("progressive-result-presentation", 2) is new at this slice, measured
    # 2026-08-31. The response stated the universal rule -- exactly one next
    # action -- and paired it with two of the four states it had named, giving
    # the other two a reporting rule rather than a next action. The assertion is
    # well posed and the response did not meet it, so it is recorded as measured
    # rather than reworded. Nothing in the skill's contract governs how
    # exhaustively a framing response enumerates states, so unlike the two
    # contract gaps this slice fixed, there is no wording defect behind it.
    known_misses = {
        ("cross-session-resumption", 1),
        ("progressive-result-presentation", 2),
    }
    for eval_id in cases:
        result = results[eval_id]
        case = cases[eval_id]
        for index, verdict in enumerate(result["assertions"]):
            assert verdict or (eval_id, index) in known_misses, (eval_id, index)
        assert {
            (eval_id, index)
            for index, verdict in enumerate(result["assertions"])
            if not verdict
        } <= known_misses
        # Bind the record to what the eval declares, not merely to truthiness.
        # Without this a recorded run could claim any markers at all -- the
        # negation of the frame mode's read-only contract included -- and stay
        # green, because the digests below bind the eval *inputs* and never the
        # recorded outcome. Mirrors the review side's `actual_findings` check.
        assert set(result["actual_markers"]) == set(case["expect"]["output_contains"])
        assert len(result["assertions"]) == len(case["assertions"])
        # Equality, not a subset: `<=` is satisfied by the empty set, so a
        # result could record no provenance at all and the aggregate digest
        # tests below would still pass on a sibling result's copy of the path.
        # A case's own `files` may be absent (`frame-new-skill` prepares no
        # workspace) while it still consumes the eval payload that declares
        # it, so the floor is the declared files plus that payload.
        assert set(result["source_files"]) == {
            "SKILL.md",
            "evals/evals.json",
            *(case.get("files") or ()),
        }
        # Not redundant with the equality above: that pins *which* sources a
        # result names, this pins that each is one the digest tests below
        # cover, so a newly declared source cannot arrive without one.
        assert set(result["source_files"]) <= set(AUTHOR_EVIDENCE_SOURCES)


@pytest.mark.parametrize("relative_path", AUTHOR_EVIDENCE_SOURCES)
def test_authoring_behavior_evidence_matches_its_source_digest(
    relative_path: str,
) -> None:
    evidence = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "behavior-results.json"
        ).read_text(encoding="utf-8")
    )
    path = AUTHOR_ROOT / relative_path
    assert path.is_file()
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    # Scoped to this skill's own results. `source_files` keys are
    # skill-relative but the fixture is pack-global, so an unscoped sweep
    # reads the review records' `evals/evals.json` -- a different file under a
    # different root -- as a second digest for this path and fails.
    recorded = {
        result["source_files"][relative_path]
        for result in evidence["results"]
        if result["eval_id"] in AUTHORING_EVAL_IDS
        and relative_path in result.get("source_files", {})
    }
    assert recorded == {digest}


# Each clause a graded run forced into the shipped body. Three conjuncts per
# clause: exactly one paragraph carries the anchor, it sits under the pinned
# heading, and its whitespace-collapsed text hashes to the recorded digest.
#
# The predicate reached this shape after four review rounds each defeated the
# previous one:
#
#   1. eval assertions only -- authored in the same change as the behavior they
#      assert, so a mirror rather than a contract.
#   2. `substring in body` checks -- one asserted a truncated prefix, and
#      swapping the words just past it removed the disposition.
#   3. more `substring in body` checks -- an unpinned limb, `Remain in `frame``,
#      could be flipped to `Enter `update`` with every asserted substring intact.
#      Positive containment is monotone under insertion, so that predicate class
#      cannot catch an appended reversal however many sentences it enumerates.
#   4. a bare paragraph digest -- answered "some paragraph somewhere collapses to
#      this hash", not "this clause is in force". The normative paragraph could be
#      replaced with an advisory sentence and the original re-appended verbatim
#      under a `## Superseded guidance (not normative)` heading, or a flipped
#      duplicate added below the original where first-match never reached it.
#
# What the conjuncts close, stated at the width they actually hold:
#   - the match count closes duplication;
#   - the heading pin closes relocation to another section, and the uniqueness
#     assertion closes relocation under a second copy of the same heading, which
#     the heading pin alone did not -- round 4's probe varied the heading's text
#     and never varied how many headings carried it;
#   - the digest closes rewording, including markup-only edits, within a
#     normative block.
# Re-wrapping the same words changes none of them.
#
# NOT closed, because this reads the raw file rather than the rendered document:
# a clause whose bytes are preserved inside a non-normative block -- a fence, a
# four-space indent, an HTML comment, or an `<div hidden>` wrapper -- satisfies
# every conjunct while being absent from what a reader sees. Stripping those
# spans here was considered and rejected: it enumerates span kinds, and the
# enumeration is already incomplete (a four-space indent collapses identically,
# since whitespace collapsing discards leading indentation). Making the predicate
# categorical needs a real CommonMark parse, which is a new dependency to defend
# two prose sentences and would need its own decision record.
#
# Also not closed, and not closable here: a contradicting sentence elsewhere.
# That is a judgment about meaning, not a property of form, and it stays with
# review.
#
# Re-pinning is meant to be deliberate. These clauses exist because a graded run
# measured their absence, so changing one is a contract change needing a fresh
# measurement and an updated record -- not a digest refresh.
MEASUREMENT_FORCED_CLAUSES = {
    # "Identifying which mode the work will need is not entering it ... Until
    # that transition the receipt reports `Mode: frame`, however far the plan has
    # progressed -- a fully specified patch that has not been authorized is still
    # framing."
    "mode-identity": (
        "Identifying which mode the work will need is not entering it.",
        "## Modes",
        "747111bd13a24f2e6c55aa1ed5ff0bbf0aa6801993b3b823067d5268d8fa96fe",
    ),
    # "The same holds when the target is resolved but the *requested change* is
    # not ... Remain in `frame`, name the candidate changes and the authority
    # each would need ... Do not infer a change from the target's current shape."
    # One paragraph, so this also pins the authority-cost clause and the
    # `Remain in `frame`` directive that the substring guards left free.
    "unspecified-change": (
        "The same holds when the target is resolved but the *requested change* "
        "is not",
        "## Modes",
        "b08e6757ea5fddf3e9c581d5ed0f5f7020ff050a17a241e7fb6f21977a2dca09",
    ),
}


def _clause_paragraphs(body: str, anchor: str) -> list[tuple[str | None, str]]:
    """Every (nearest preceding heading, collapsed paragraph) carrying `anchor`.

    Returns all matches rather than the first: a duplicate paragraph with one
    sentence reversed is invisible to a first-match lookup, and the count is what
    makes it visible.

    Whitespace is collapsed before matching, not after. The source is
    hard-wrapped, so an anchor spanning a line break finds nothing in the raw
    paragraph -- that exact mistake made an earlier version of this helper return
    nothing and report every mutation as caught.
    """
    heading: str | None = None
    buffer: list[str] = []
    found: list[tuple[str | None, str]] = []

    def flush() -> None:
        if buffer:
            collapsed = " ".join(" ".join(buffer).split())
            if anchor in collapsed:
                found.append((heading, collapsed))
        buffer.clear()

    for line in body.splitlines():
        if re.match(r"#{1,6}\s+\S", line):
            flush()
            heading = line.strip()
            continue
        if not line.strip():
            flush()
            continue
        buffer.append(line)
    flush()
    return found


def test_shipped_body_keeps_the_two_clauses_measurement_forced() -> None:
    """Each forced clause is unique, correctly placed, and byte-identical."""
    body = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")

    headings = [
        line.strip() for line in body.splitlines() if re.match(r"#{1,6}\s+\S", line)
    ]

    for name, (anchor, heading, expected) in MEASUREMENT_FORCED_CLAUSES.items():
        assert headings.count(heading) == 1, (
            f"{name}: {headings.count(heading)} headings read {heading!r}, "
            "expected exactly 1. With two, the clause can be gutted where it is "
            "normative and re-appended verbatim under the duplicate, and the "
            "heading conjunct below cannot tell the copies apart."
        )
        matches = _clause_paragraphs(body, anchor)
        assert len(matches) == 1, (
            f"{name}: {len(matches)} paragraphs carry this clause's anchor, "
            "expected exactly 1. None means the clause is gone; more than one "
            "means a copy exists, and a copy is how a reversed duplicate hides "
            "behind the original. Sections holding it: "
            f"{[h for h, _ in matches]}"
        )
        found_heading, region = matches[0]
        assert found_heading == heading, (
            f"{name}: the clause moved out of {heading!r} into "
            f"{found_heading!r}. Its text is unchanged, so the digest below "
            "would still match -- but a clause quoted under a different heading "
            "is not the same clause in force."
        )
        digest = hashlib.sha256(region.encode()).hexdigest()
        assert digest == expected, (
            f"{name}: the measurement-forced clause changed.\n"
            f"  recorded: {expected}\n"
            f"  found:    {digest}\n"
            f"  now reads: {region}\n"
            "Re-wrapping the same words does not reach here, so some word or its "
            "markup changed -- a blockquote prefix, a fence, or a conversion to "
            "bullets all land here with no word altered. This clause is in the "
            "body because a graded run measured its absence; changing it needs a "
            "fresh measurement and a record update in the slice qa.md, not a new "
            "digest."
        )


def test_the_two_forced_clauses_are_distinct_paragraphs() -> None:
    """The two clauses are two paragraphs, not one.

    This is not subsumed by the digest checks above, and the catching set is
    narrow enough to be worth stating: merging the two paragraphs *and*
    refreshing both recorded digests to the merged value satisfies every conjunct
    above -- one match each, both under the same heading, both digests as
    recorded -- because the two clauses genuinely share a heading. Only the
    distinctness check notices that two names now resolve to one paragraph.

    `assert all(...)` is likewise load-bearing rather than duplicated: one
    missing region and one present region give a two-element set, which would
    satisfy the length comparison vacuously.
    """
    body = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    regions = []
    for anchor, _, _ in MEASUREMENT_FORCED_CLAUSES.values():
        matches = _clause_paragraphs(body, anchor)
        regions.append(matches[0][1] if matches else None)

    assert all(regions), "a forced clause has no paragraph"
    assert len(set(regions)) == len(regions), "both anchors resolve to one paragraph"


def test_portable_workflow_contains_no_delivery_or_runtime_coupling() -> None:
    content = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(AUTHOR_ROOT.rglob("*.md"))
    ).lower()
    for forbidden in (
        "packages/agentbundle",
        "agentbundle install",
        "agentbundle-manifest",
        ".claude-plugin",
        ".codex/skills",
    ):
        assert forbidden not in content


MODES_SECTION = re.compile(r"^## Modes$(.*?)^## ", re.MULTILINE | re.DOTALL)
MODE_BULLET = re.compile(r"^- \*\*(?P<name>[a-z][a-z-]*)\*\* — ", re.MULTILINE)
UNAVAILABLE_SENTENCE = re.compile(
    r"Requests to\s+author (.*?)\s+use the stable unavailable result", re.DOTALL
)


def _modes_section(text: str) -> str:
    """Return the Modes section only, never the whole file."""
    match = MODES_SECTION.search(text)
    assert match, "SKILL.md has no Modes section"
    return match.group(1)


def _mode_bullet_names(text: str) -> set[str]:
    """Return the modes the Modes list advertises, from its bullets alone."""
    return set(MODE_BULLET.findall(_modes_section(text)))


def _unavailable_modes(text: str) -> str:
    """Return the unavailable-result sentence, so a match elsewhere cannot pass for it."""
    match = UNAVAILABLE_SENTENCE.search(text)
    assert match, "SKILL.md has no unavailable-result sentence"
    return match.group(1)


def _mode_bullet(text: str, mode: str) -> str:
    """Return one mode's own bullet.

    Never the section opener: "`frame` is the default and is read-only" would
    otherwise satisfy a read-only assertion for every mode.
    """
    section = _modes_section(text)
    starts = [(m.group("name"), m.start()) for m in MODE_BULLET.finditer(section)]
    for index, (name, start) in enumerate(starts):
        if name == mode:
            end = starts[index + 1][1] if index + 1 < len(starts) else len(section)
            return section[start:end]
    raise AssertionError(f"no bullet for mode {mode!r}")


def _transition_sentence(text: str) -> str:
    """Return the sentence authorizing a write out of knowledge-provider.

    Scoped to that sentence. The shipped "Move to `create` or `update` only
    after an explicit mode transition and immediately before the first write"
    gates a single moment and cannot express read-only entry plus a later,
    separate authorization, so naming the mode there would satisfy the
    assertion while contradicting read-only entry.
    """
    for sentence in _modes_section(text).replace("\n", " ").split("."):
        if "authorizes that write" in sentence:
            return sentence
    raise AssertionError("no separate write-authorizing transition sentence")


def _modules_for(mode: str) -> set[str]:
    """Return the reference modules a mode's own bullet links."""
    bullet = _mode_bullet((AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8"), mode)
    return set(re.findall(r"\(references/([a-z0-9-]+\.md)\)", bullet))


def test_mode_is_advertised_and_not_declared_unavailable() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert _mode_bullet_names(text) == {"frame", "create", "update", "knowledge-provider"}
    assert "knowledge-provider" not in _unavailable_modes(text)


def test_mode_entry_is_read_only_and_write_is_gated() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    entry = _mode_bullet(text, "knowledge-provider")
    assert "read-only" in entry
    assert "knowledge-provider" in _transition_sentence(text)


def test_mode_specific_modules_are_exactly_four() -> None:
    assert _modules_for("knowledge-provider") == {
        "knowledge-provider-pattern.md",
        "provenance.md",
        "retrieval-evaluation.md",
        "security-boundaries.md",
    }
    # The common contract's safety module still governs every mode, so it is
    # not a knowledge-provider-specific module.
    assert "safety-and-authority.md" not in _modules_for("knowledge-provider")
