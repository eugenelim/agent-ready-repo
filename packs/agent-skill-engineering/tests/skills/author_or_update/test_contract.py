"""Construction contracts for the progressive authoring workflow."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
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
# `evals/evals.json` digest, so the two-id set at the merge base left six free to
# carry a stale digest the parametrized sweep below would never read.
#
# Pinned by its own test. Emptying this set fails closed -- the sweep's
# `recorded == {digest}` sees an empty set -- but *narrowing* it does not: drop one
# id, forge that result's digest, and the whole suite stays green. That is the
# mutation that matters here and the one an incomplete audit missed.
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
        "subagent-composition",
        "hook-plugin-design",
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
    "evals/files/subagent-composition-SKILL.md",
    "evals/files/hook-plugin-design-SKILL.md",
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
        "subagent-composition",
        "hook-plugin-design",
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


# Known misses, module scope so every consumer reads one object.
#
# Two inherited; three added at the composition-fixtures slice, each measured
# false in the 2026-09-09 round and each authorised by the owner that day. The
# slice's verification ledger carries case, assertion text, prior verdict,
# measured verdict and authority for every entry; this tuple is the
# machine-readable half and the ledger is the record.
#
# This was briefly reconstructed by parsing this file's own source. That parse
# kept the delimiting quote characters, so no pair could ever match an assertion
# string read from JSON and the exemption branch was dead — while the
# non-emptiness check written to catch exactly that class passed, because the
# set parsed non-empty and merely held the wrong strings.
KNOWN_MISSES = frozenset(
    {
        ("cross-session-resumption", "Adds a durable record a later session can read to resume"),
        (
            "progressive-result-presentation",
            "Pairs each incomplete state with the next action it hands the user",
        ),
        (
            "cross-session-resumption",
            "Names update as the mode the work will need, against the named existing "
            "skill root, without entering it before authorization",
        ),
        (
            "node-browser-suite",
            "Frames worker sizing against memory and browser cost, not CPU count alone",
        ),
        (
            "hook-plugin-design",
            "Names the undisclosed shared dependency as something a consumer must see "
            "before install",
        ),
    }
)


def test_independent_behavior_results_cover_both_authoring_cases() -> None:
    evidence = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "behavior-results.json"
        ).read_text(encoding="utf-8")
    )
    # Same last-wins hazard as `_authoring_records`: refuse a repeated id
    # before collapsing, or a shadowed record escapes every check below.
    raw_ids = [r["eval_id"] for r in evidence["results"]]
    assert len(raw_ids) == len(set(raw_ids)), sorted(
        i for i in set(raw_ids) if raw_ids.count(i) > 1
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
        "subagent-composition",
        "hook-plugin-design",
        "detect-activation-failure",
        "detect-script-contract-failure",
    }
    # Each exemption names an exact (case, assertion text) so a *different* miss still
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
    # Keyed by assertion *text*, not by index, and checked for liveness -- the
    # shape the review side already uses. An index-keyed exemption migrates onto
    # a different assertion when one is inserted or reworded above it, and the
    # length pin below only catches that until a legitimate re-record restores
    # the count. Text keying does not by itself stop an exemption outliving its
    # miss -- the liveness check asserts the assertion is still declared, not that
    # it is still failing -- so the exemptions are also asserted to be used.
    known_misses = KNOWN_MISSES

    # Every exemption still describes a declared assertion. Without this, a
    # reworded assertion silently drops its exemption's subject and the exemption
    # goes on excusing whatever now sits at that position.
    for eval_id, text in known_misses:
        assert eval_id in cases, eval_id
        assert text in cases[eval_id]["assertions"], (eval_id, text)

    for eval_id in cases:
        result = results[eval_id]
        case = cases[eval_id]
        exempt = {
            index
            for index, text in enumerate(case["assertions"])
            if (eval_id, text) in known_misses
        }
        for index, verdict in enumerate(result["assertions"]):
            assert verdict or index in exempt, (eval_id, index, case["assertions"][index])
        failing = {
            index
            for index, verdict in enumerate(result["assertions"])
            if not verdict
        }
        assert failing <= exempt
        # And the other direction: an exemption whose miss has since been repaired
        # must be removed, not left standing to excuse the next regression there.
        assert exempt <= failing, (eval_id, sorted(exempt - failing))
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
    assert recorded == {digest}, (
        f"{relative_path} moved since these results were graded. The recorded "
        "evidence must be re-measured, not re-stamped: run the round again and "
        "replace the verdicts, transcripts and observation identifier together. "
        "Refreshing this digest alone leaves verdicts attributed to a version "
        "that no longer exists. See the slice verification ledger under "
        "docs/specs/agent-skill-engineering-composition-fixtures/notes/."
    )


# Each clause a graded run forced into the shipped body.
#
# Four conjuncts per clause: the pinned heading occurs exactly once, exactly one
# paragraph carries the anchor, that paragraph's nearest preceding heading is the
# pinned one, and its whitespace-collapsed text hashes to the recorded digest.
#
# The predicate reached this shape after five review rounds each defeated the
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
#   5. three conjuncts -- match count, heading text, digest -- beaten by gutting
#      the clause in place and re-appending it verbatim under a *second*
#      `## Modes`, which a heading-text pin satisfies exactly. That is why the
#      uniqueness conjunct exists.
#
# A sixth round then defeated the four conjuncts too, with `- ## Superseded
# guidance` as a container-block heading, and that defeat was documented as
# uncovered rather than closed -- see the NOT-closed list below.
#
# A seventh round defeated the guard without touching the body at all: the
# subject set this dict provides was unpinned, so deleting an entry dropped that
# clause's coverage while everything stayed green. Pinned now, in its own test,
# because putting the pin inside one consumer left the sibling vacuous. The
# lesson that generalizes is in the slice qa.md: a set is safe only when some
# assertion demands a positive result from its members.
#
# Four conjuncts, stated at the width they actually hold:
#   - the pinned heading occurs exactly once, which closes relocation under a
#     second copy of the same heading *when that copy is a column-0 ATX
#     heading* -- round 4's probe varied the heading's text and never varied how
#     many headings carried it;
#   - exactly one paragraph carries the anchor, which closes duplication;
#   - that paragraph's nearest preceding heading is the pinned one, which closes
#     relocation *only when the replacement heading is a column-0 ATX heading*;
#   - the digest closes rewording, including markup-only edits, within a
#     normative block.
# Re-wrapping the same words changes none of them.
#
# NOT closed, all one class: this reads raw lines, not the rendered document.
#   - a clause whose bytes survive inside a non-normative block -- a fence, a
#     four-space indent, an HTML comment, a `<div hidden>` wrapper;
#   - a clause relocated under a heading this file's line pattern does not
#     recognize -- a setext underline, a 1-3-space-indented ATX heading, a raw
#     `<h2>`, or an ATX heading inside a container block such as
#     `- ## Superseded guidance`, after which the tracked nearest heading is
#     still the pinned one while a renderer shows the clause under the new h2.
#
# Two enumerations were proposed for these and both were rejected on
# adjudication, for the same reason each time: they enumerate members of an open
# class. A fence-and-comment stripper misses the four-space indent. A
# heading-form check over setext, indented ATX and raw HTML misses
# `- ## heading`, because heading *syntax* is a closed set but "the nearest
# heading preceding this paragraph in the rendered document" is not -- container
# blocks compose with heading syntax. Making the predicate categorical needs a
# real CommonMark parse: a new dependency to defend two prose sentences, which
# the cut-before-adding ladder routes through a decision record, not a test file.
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


def test_the_authoring_eval_id_set_covers_every_declared_case() -> None:
    """`AUTHORING_EVAL_IDS` is derived-checked, not merely declared.

    The set scopes which recorded results the digest sweep reads, so narrowing it
    silently drops a result from coverage while every assertion still passes.
    Emptying it fails closed; narrowing it does not, which is why it needs a pin
    of its own rather than the protection its use site appears to give it.

    Checked against the authoring skill's own declared cases, which are
    themselves pinned by set equality elsewhere in this file, so the two cannot
    drift apart without one of them reddening.
    """
    declared = {
        case["id"]
        for case in json.loads(
            (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
    }
    assert declared == AUTHORING_EVAL_IDS, (
        f"AUTHORING_EVAL_IDS is {sorted(AUTHORING_EVAL_IDS)} against declared "
        f"{sorted(declared)}. Narrowing this set removes a graded result from "
        "the digest sweep without failing anything else."
    )
    assert len(AUTHORING_EVAL_IDS) == 10


def test_the_pinned_clause_set_is_exactly_the_two_measured_clauses() -> None:
    """The subject set is pinned, independently of anything that iterates it.

    Its own test rather than a line inside one of the consumers. Both guards
    below loop over this dict, so an entry deleted -- or the dict emptied --
    makes them pass while asserting nothing: `all([])` is True and
    `len(set()) == len([])`. Putting the pin inside one consumer left the other
    still vacuous, which is a smaller version of the same defect.

    A clause legitimately added later reddens here exactly once, and is repaired
    in the same edit the re-pinning doctrine above already requires.
    """
    assert set(MEASUREMENT_FORCED_CLAUSES) == {
        "mode-identity",
        "unspecified-change",
    }, (
        f"the pinned clause set is {sorted(MEASUREMENT_FORCED_CLAUSES)}. Adding "
        "or removing a measurement-forced clause is a contract change: it needs "
        "a fresh measurement and a record update in the slice qa.md, not a "
        "silent edit to this dict."
    )
    # Anti-vacuity: an empty dict would satisfy the equality only if the expected
    # set were also empty, so assert the floor the guard is sized for.
    assert len(MEASUREMENT_FORCED_CLAUSES) == 2


def test_shipped_body_keeps_the_two_clauses_measurement_forced() -> None:
    """Each forced clause is unique, correctly placed, and byte-identical."""
    body = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")

    headings = [
        line.strip() for line in body.splitlines() if re.match(r"#{1,6}\s+\S", line)
    ]

    for name, (anchor, heading, expected) in MEASUREMENT_FORCED_CLAUSES.items():
        assert headings.count(heading) == 1, (
            f"{name}: {headings.count(heading)} column-0 ATX headings read "
            f"{heading!r}, expected exactly 1. None means the pinned heading was "
            "renamed, its level changed, or its form changed to one this "
            "line pattern does not recognize -- re-pin it deliberately. Two or "
            "more means the clause can be gutted where it is normative and "
            "re-appended verbatim under the duplicate, which the heading "
            "conjunct below cannot tell apart."
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


# ---------------------------------------------------------------------------
# Composition-fixture guards.
#
# The two cases this slice adds carry two fields the inherited cases do not: the
# pattern identifiers they exercise, and the text of the assertion that reports
# the defect their payload seeds. Both are required of these two cases only —
# a guard requiring them everywhere would redden on cases this slice does not
# own.
#
# Every "before this slice" comparison reads the base commit rather than the
# working tree. A baseline read from the tree is one the change under test can
# edit first, which is how a marker this slice invented becomes "inherited".
# ---------------------------------------------------------------------------

# The record's `transcript` value is relative to the spec directory, so this
# anchor is the spec directory itself.
SPEC_DIR = (
    PACK_ROOT.parents[1]
    / "docs"
    / "specs"
    / "agent-skill-engineering-composition-fixtures"
)
BASE_COMMIT = "d44484b29d1ba0f56cb0baf42fd79b1348e26a58"
COMPOSITION_CASES = ("subagent-composition", "hook-plugin-design")
# Per-case pattern lists are fixed by the contract, not derived from the
# declarations they check: membership in the admitted set is the weaker test
# that an unrelated admitted topic passes.
EXPECTED_PATTERNS = {
    "subagent-composition": ["skills-and-subagents-common-floor"],
    "hook-plugin-design": ["hooks-common-floor", "plugin-package-common-floor"],
}
# The inherited case whose shape these two share: read-only framing over a
# payload the case supplies. Its marker set is what they must equal.
MARKER_SIBLING = "pytest-suite"


def test_the_base_commit_matches_the_one_the_ledger_records() -> None:
    """`BASE_COMMIT` is bound to the recorded base, not merely declared.

    Three guards read their comparison set from this commit — the declared-case
    set, the sibling marker set, and the base payload digests. Point it at HEAD
    and none of them reddens: the case-set equality becomes `current == current`
    plus the two new ids, the sibling is compared with itself, and the payload
    digests are the ones the change under test just wrote. Every "before this
    slice" comparison silently becomes a current-tree comparison.

    That is not a sabotage path, it is the cheap repair: the next slice to add
    an eval case reddens the case-set equality, and bumping this constant is the
    first thing that makes it green again. Binding it to the ledger means doing
    so also has to move the recorded base, which is a visible act.
    """
    ledger = (SPEC_DIR / "notes" / "verification-ledger.md").read_text(encoding="utf-8")
    recorded = re.search(r"\*\*Base commit:\*\*\s*`([0-9a-f]{40})`", ledger)
    assert recorded, "the verification ledger records no base commit"
    assert BASE_COMMIT == recorded.group(1), (
        f"BASE_COMMIT is {BASE_COMMIT} but the ledger records "
        f"{recorded.group(1)}. Moving the base is a re-measurement, not a "
        "constant bump: change the ledger's recorded base and re-take the "
        "comparisons, or leave both alone."
    )


def _at_base(repo_relative_path: str) -> str:
    """Read a tracked file as of the slice's base commit.

    The seam in front of git: one subprocess per path, so the suite's cost stays
    in assertions rather than processes, and no test shells out ad hoc.
    """
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{repo_relative_path}"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PACK_ROOT.parents[1],
    ).stdout


AUTHOR_DECL_REPO_PATH = (
    "packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill"
    "/evals/evals.json"
)


def _declared_cases() -> dict[str, dict]:
    payload = json.loads((AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["evals"]}


def _base_cases() -> dict[str, dict]:
    payload = json.loads(_at_base(AUTHOR_DECL_REPO_PATH))
    return {case["id"]: case for case in payload["evals"]}


def test_composition_cases_declare_a_complete_field_set() -> None:
    """AC1: no required field on either new case is empty."""
    cases = _declared_cases()
    for case_id in COMPOSITION_CASES:
        case = cases[case_id]
        for field in ("id", "prompt", "expected_output", "assertions", "files"):
            assert case.get(field), (case_id, field)
        assert case["expect"]["output_contains"], case_id


def test_each_composition_case_names_its_own_payload() -> None:
    """AC2: each new case's payloads resolve, and no other case shares them.

    Scoped to the two new cases, which is what the criterion constrains. Global
    pairwise distinctness would be wrong: `update-existing-skill` and
    `cross-session-resumption` deliberately share one inherited payload, and
    this slice does not own that decision.
    """
    cases = _declared_cases()
    root = AUTHOR_ROOT.resolve()
    others = {
        (AUTHOR_ROOT / declared).resolve()
        for case_id, case in cases.items()
        if case_id not in COMPOSITION_CASES
        for declared in case.get("files") or ()
    }
    claimed: dict[Path, str] = {}
    for case_id in COMPOSITION_CASES:
        for declared in cases[case_id]["files"]:
            resolved = (AUTHOR_ROOT / declared).resolve()
            assert resolved.is_file(), (case_id, declared)
            # Canonical containment, not string prefixing: `..` rejection does
            # not stop an in-boundary symlink escape.
            assert root in resolved.parents, (case_id, declared)
            assert resolved not in others, (case_id, declared)
            assert resolved not in claimed, (case_id, claimed.get(resolved))
            claimed[resolved] = case_id


def test_the_declared_case_set_gains_exactly_the_two_new_ids() -> None:
    """AC3: the set is the base set plus these two, with nothing else moved."""
    assert set(_declared_cases()) == set(_base_cases()) | set(COMPOSITION_CASES)


@pytest.mark.parametrize("case_id", COMPOSITION_CASES)
def test_composition_case_declares_its_exact_pattern_list(case_id: str) -> None:
    """AC4: equality per case, and every identifier is an admitted topic."""
    declared = _declared_cases()[case_id]["patterns"]
    assert declared == EXPECTED_PATTERNS[case_id]
    admitted = {
        topic["topic"]
        for topic in json.loads(
            (PACK_ROOT / "tests" / "fixtures" / "topic-admission.json").read_text(
                encoding="utf-8"
            )
        )["topics"]
    }
    assert set(declared) <= admitted, (case_id, sorted(set(declared) - admitted))


def test_composition_cases_reuse_the_sibling_marker_set() -> None:
    """AC5: equality with one named sibling, read at base, sibling unmoved.

    Containment in the union of base declarations is the weaker check this
    replaces: that union spans modes and authorization states, so it admits
    `Mode: knowledge-provider` and `Write status: awaiting explicit
    authorization`, neither of which a read-only framing case produces.
    """
    cases = _declared_cases()
    base = _base_cases()
    sibling = set(base[MARKER_SIBLING]["expect"]["output_contains"])
    assert set(cases[MARKER_SIBLING]["expect"]["output_contains"]) == sibling
    for case_id in COMPOSITION_CASES:
        assert set(cases[case_id]["expect"]["output_contains"]) == sibling, case_id


def test_each_composition_case_names_a_distinct_seeded_defect_assertion() -> None:
    """AC6: the named text belongs to its own case, and the two differ."""
    cases = _declared_cases()
    named = []
    for case_id in COMPOSITION_CASES:
        case = cases[case_id]
        text = case["seeded_defect_assertion"]
        assert text in case["assertions"], (case_id, text)
        named.append(text)
    assert len(set(named)) == len(named), named


def test_composition_payloads_are_distinct_non_empty_drafts() -> None:
    """AC8: neither payload is empty, a copy of the other, or a base payload."""
    base_payloads = {
        hashlib.sha256(
            _at_base(f"{AUTHOR_DECL_REPO_PATH.rsplit('/', 1)[0]}/{name}").encode("utf-8")
        ).hexdigest()
        for name in (
            "files/update-existing-SKILL.md",
            "files/pytest-suite-SKILL.md",
            "files/node-browser-suite-SKILL.md",
        )
    }
    digests = {}
    cases = _declared_cases()
    for case_id in COMPOSITION_CASES:
        # From the declaration the case actually carries. Deriving the path from
        # the case id instead lets the two `files` values be swapped while this
        # guard goes on hashing the by-name files and stays green.
        declared = cases[case_id]["files"]
        assert len(declared) == 1, (case_id, declared)
        path = AUTHOR_ROOT / declared[0]
        raw = path.read_bytes()
        assert raw.strip(), case_id
        digest = hashlib.sha256(raw).hexdigest()
        assert digest not in base_payloads, case_id
        assert digest not in digests, (case_id, digests.get(digest))
        digests[digest] = case_id


def _authoring_records() -> dict[str, dict]:
    """Authoring records by id, with duplicate ids refused before collapsing.

    Indexing by `eval_id` is last-wins, so without this a repeated id hides the
    shadowed record from every per-record guard here — transcript digest and
    markers, transcript distinctness, round identity, verdict length,
    `source_files` equality — while the id-set equality stays green because it
    compares keys. The reachable path is a re-measured round appended rather
    than replacing its predecessor, which leaves a stale observation identifier
    and stale verdicts in the shipped evidence.
    """
    evidence = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "behavior-results.json").read_text(
            encoding="utf-8"
        )
    )
    rows = [r for r in evidence["results"] if r["eval_id"] in AUTHORING_EVAL_IDS]
    ids = [r["eval_id"] for r in rows]
    assert len(ids) == len(set(ids)), sorted(
        i for i in set(ids) if ids.count(i) > 1
    )
    return {r["eval_id"]: r for r in rows}


def test_every_verdict_is_readable_against_its_own_transcript() -> None:
    """AC9: the transcript is the falsifier, not the record's own account.

    Comparing `actual_markers` to the declaration is a mirror — both sides come
    from the same file. This binds each record to bytes in the tree: the digest
    must recompute, and every declared marker must occur in the response those
    bytes hold. A fabricated record has to produce a transcript that satisfies
    both.
    """
    cases = _declared_cases()
    for eval_id, record in _authoring_records().items():
        transcript = SPEC_DIR / record["transcript"]
        resolved = transcript.resolve()
        assert resolved.is_file(), (eval_id, record["transcript"])
        assert SPEC_DIR.resolve() in resolved.parents, (eval_id, record["transcript"])
        digest = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
        assert digest == record["captured_response_sha256"], eval_id
        body = resolved.read_text(encoding="utf-8")
        for marker in cases[eval_id]["expect"]["output_contains"]:
            assert marker in body, (eval_id, marker)


def test_authoring_transcripts_are_one_per_record() -> None:
    """AC9: no two records may rest on one transcript.

    Compared on resolved canonical targets rather than on the recorded strings,
    because two distinct paths under `notes/` — one a symlink — satisfy a string
    comparison while a single transcript backs both records.
    """
    records = _authoring_records()
    resolved = {
        eval_id: (SPEC_DIR / r["transcript"]).resolve()
        for eval_id, r in records.items()
    }
    assert len(set(resolved.values())) == len(resolved), sorted(resolved.items())


def test_every_authoring_record_belongs_to_one_round() -> None:
    """AC11: one observation identifier across the round, verdicts per assertion."""
    cases = _declared_cases()
    records = _authoring_records()
    evidence = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "behavior-results.json").read_text(
            encoding="utf-8"
        )
    )
    declared_round = evidence["graded_run"]["observation_id"]
    identifiers = {r["observation_id"] for r in records.values()}
    # Equality with the declared round, not merely mutual agreement: rewriting
    # every record to one arbitrary value satisfies agreement and says nothing.
    assert identifiers == {declared_round}, (sorted(identifiers), declared_round)
    for eval_id, record in records.items():
        assert len(record["assertions"]) == len(cases[eval_id]["assertions"]), eval_id


@pytest.mark.parametrize("case_id", COMPOSITION_CASES)
def test_the_seeded_defect_assertion_is_true_or_exempted(case_id: str) -> None:
    """AC13: the defect a payload seeds is reported, or its miss is on the record."""
    case = _declared_cases()[case_id]
    named = case["seeded_defect_assertion"]
    index = case["assertions"].index(named)
    verdict = _authoring_records()[case_id]["assertions"][index]
    # Anti-vacuity on the exemption side: the set must be non-empty AND every
    # entry must name an assertion some case actually declares, so a set of
    # well-formed strings that match nothing cannot stand in for a real one.
    declared = {a for c in _declared_cases().values() for a in c["assertions"]}
    assert KNOWN_MISSES, "exemption set is empty"
    assert all(t in declared for _, t in KNOWN_MISSES), sorted(
        t for _, t in KNOWN_MISSES if t not in declared
    )
    assert verdict or (case_id, named) in KNOWN_MISSES, (case_id, named)
