"""Hold the verification-ledger contract together across its governing surfaces.

`docs/specs/verification-ledger` splits an approved delivery contract from the
evidence produced by executing it. `spec.md` and `plan.md` are hash-pinned once
the plan is approved, so an obligation that names either as the destination for
an execution observation can never be discharged. The repair states one rule —
substantive edits end at approval, observations go to the sibling verification
ledger — and this module keeps every surface that states it agreeing with the
executable guard that enforces it.

Two halves are asserted per governing source, and **both must be independently
killable**:

1. *pinned* — the source says substantive edits end at plan approval.
2. *routing* — the source says an execution observation goes to the ledger.

An earlier revision of this file asserted only the first half. Deleting the
routing clause from three separate sources left it green, which made it a guard
that could not fail for the delivery's central claim. Every clause below is
therefore listed individually so a deletion of any one of them reddens.

The closed set of rule-bearing sources is six paths represented by eight
guarded regions in `SOURCES`. `SKILL.md` is a pure pointer and carries no rule
of its own; the how-to keeps its own pre-existing immutability statement plus a
routing clause.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
GUARDS = ROOT / "packs/core/.apm/skills/work-loop/scripts/_loop_guards.py"

#: Phrasings that granted a substantive post-approval edit before the repair.
#: A bounded regression backstop, not a proof that no new licence can be worded.
#: Prose cannot be proved free of an arbitrary permission; the positive clauses
#: are the contract, and these catch the specific wordings that caused the
#: defect. Add a row when a new one is observed in the wild.
RETIRED_LICENCES = (
    "`Drafting` or `Executing`",
    "Drafting or Executing",
    "before ship, the plan is Living and you edit it freely",
)

#: Vocabulary a Step 2 restatement of the mutability rule would use. This is a
#: bounded marker list, not proof that no rule can be phrased another way.
RESTATED_RULE_MARKERS = (
    "pinned in substance",
    "immutable in substance",
    "change substantively",
    "hash-pinned",
)


def _read(relative: str) -> str:
    """Read one UTF-8 repository surface."""
    return (ROOT / relative).read_text(encoding="utf-8")


def _load_guards() -> ModuleType:
    """Load `_loop_guards` by path, the way production loads it."""
    spec = importlib.util.spec_from_file_location("_loop_guards_ledger_probe", str(GUARDS))
    assert spec is not None and spec.loader is not None, f"cannot load {GUARDS}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section(relative: str, anchor: str | None) -> str:
    """Return the region `anchor` opens, or the whole file when `anchor` is None.

    Three anchor shapes, because the governing surfaces genuinely have three:
    a Markdown heading (ends at the next same-or-shallower heading), a bold
    paragraph lead such as `**What the pin covers.**` (ends at the next bold
    lead or heading — `state-schema.md` carries exactly one heading, so a
    heading-only extractor would silently return the rest of the file), and
    `None` for a file whose guarded clauses legitimately span all of it.

    Every shape fails loudly on a missing anchor or terminator rather than
    widening. A silently widened region lets an assertion be satisfied by prose
    from a section it was never meant to read, and a truncated one hides the
    clauses it was meant to cover.
    """
    text = _read(relative)
    if anchor is None:
        return text
    assert anchor in text, f"{relative}: anchor {anchor!r} not found"
    start = text.index(anchor) + len(anchor)
    if anchor.startswith("#"):
        depth = len(anchor) - len(anchor.lstrip("#"))
        terminator = rf"\n#{{1,{depth}}}[ \t]"
    else:
        # A bold *paragraph lead* is blank-line separated. Without that, a
        # re-wrap that happens to push an inline bold span (`**Canonical
        # form**`) to the start of a line truncates the region before the
        # guarded clause and reddens the suite on a no-op edit.
        terminator = r"\n\n[ \t]*\*\*\w|\n#{1,6}[ \t]"
    match = re.search(terminator, text[start:])
    end = start + match.start() if match else len(text)
    region = text[start:end]
    assert region.strip(), f"{relative}: region after {anchor!r} is empty"
    return region


def _flat(text: str) -> str:
    """Collapse wrapping and Markdown leaders so a clause compares whole.

    Blockquote and list markers are stripped before whitespace collapses, so
    re-wrapping guarded prose — a change with no meaning — cannot redden this
    module and no clause has to be split into separately satisfiable fragments.
    """
    stripped = (re.sub(r"^[ \t]*(?:>[ \t]?|[-*+][ \t]+)+", "", line) for line in text.splitlines())
    return " ".join(" ".join(stripped).split())


#: `relative path`, anchor (heading, bold lead, or None for whole file),
#: pinned clauses, routing clauses.
SOURCES: tuple[tuple[str, str | None, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "packs/core/seeds/docs/CONVENTIONS.md",
        "### A spec directory freezes as a unit, when the spec ships",
        (
            "only while the plan is `Drafting`, and ends when the plan is approved",
            "both `spec.md` and `plan.md` are pinned in substance",
        ),
        ("An observation produced by execution belongs in the sibling `notes/verification-ledger.md`",),
    ),
    (
        "packs/core/seeds/docs/CONVENTIONS.md",
        "**`plan.md` is the implementation strategy.**",
        (
            "It may change substantively only while `Drafting`; once approved, both it and `spec.md` are pinned except for lifecycle bookkeeping",
        ),
        (),
    ),
    (
        "packs/core/seeds/docs/CONVENTIONS.md",
        "**Lifecycle:** specs are",
        (
            "from approval onward the correction is the controlled-amendment path, not an in-flight edit",
        ),
        ("an observation produced by execution goes to the verification ledger",),
    ),
    (
        "packs/core/.apm/skills/new-spec/assets/plan.md",
        None,
        (
            "It may change substantively only while its Status is `Drafting`",
            "After approval, `spec.md` and `plan.md` are pinned in substance",
        ),
        (
            "execution observations belong in `docs/specs/<feature>/notes/verification-ledger.md`",
            "Never name `spec.md` or `plan.md` as an execution-evidence destination",
        ),
    ),
    (
        "packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md",
        "## Verification ledger",
        ("The approved `spec.md` and `plan.md` retain obligations only",),
        (
            "notes/verification-ledger.md",
            "The ledger is not hash-pinned",
            "needs no amendment to either approved artifact",
        ),
    ),
    (
        "guides/core/explanation/why-the-plan-owns-the-lld.md",
        "## The shape of the answer",
        ("allowed to change as you learn while it is `Drafting`",),
        ("plan-and-execute-non-trivial-work.md",),
    ),
    (
        "packs/core/.apm/skills/work-loop/references/pre-execute-review.md",
        "## Mid-EXECUTE re-plan — Phase-1 note",
        (
            "approved `spec.md` and `plan.md` are **immutable in substance**",
            "still causes a refusal",
        ),
        ("For an execution observation rather than a plan error, follow the",),
    ),
    (
        "packs/core/.apm/skills/work-loop/references/state-schema.md",
        "**What the pin covers.**",
        ("Everything else stays pinned",),
        (),
    ),
)


def test_the_status_guard_admits_executing_and_refuses_a_regressed_token(
    tmp_path,
) -> None:
    """Call the real status guard, not its data table.

    Asserting that `"Executing"` appears in `_LEGAL_AFTER_APPROVAL` proves a
    string is present, not that the guard admits the status. Minimal fixtures
    are used rather than this delivery's own artifacts, so a later edit to them
    cannot make this pass or fail for a reason unrelated to the guard.
    """
    guards = _load_guards()

    def _write(spec_status: str, plan_status: str) -> pathlib.Path:
        directory = tmp_path / f"{spec_status}-{plan_status}"
        directory.mkdir()
        (directory / "spec.md").write_text(
            f"# Spec: fixture\n\n- **Status:** {spec_status}\n", encoding="utf-8"
        )
        (directory / "plan.md").write_text(
            f"# Plan: fixture\n\n- **Status:** {plan_status}\n", encoding="utf-8"
        )
        return directory

    legal = _write("Implementing", "Executing")
    assert (
        guards.assert_status_legal("probe", legal / "spec.md", legal / "plan.md") is None
    ), "the guard must admit an Executing plan beside an Implementing spec"

    regressed = _write("Implementing", "Drafting")
    reason = guards.assert_status_legal(
        "probe", regressed / "spec.md", regressed / "plan.md"
    )
    assert reason is not None and "Drafting" in reason, (
        "the guard must refuse a plan whose status regressed out of the "
        f"post-approval set; got {reason!r}"
    )


def test_a_substantive_edit_moves_the_pin_but_bookkeeping_does_not() -> None:
    """The exemption every governing source describes, run against the real hasher."""
    guards = _load_guards()
    plan = "# Plan: fixture\n\n- **Status:** Approved\n\n## Approach\n\nOne step.\n"

    def canon(text: str) -> str:
        return guards.canonical_contract(text, ac_section_only=False)

    assert canon(plan.replace("- **Status:** Approved", "- **Status:** Executing", 1)) == canon(
        plan
    ), "the preamble status token must stay exempt from the pin"
    assert canon(plan.replace("One step.", "One step.\n\n- [x] done\n", 1)) == canon(
        plan.replace("One step.", "One step.\n\n- [ ] done\n", 1)
    ), "progress checkboxes must stay exempt from the pin"
    assert canon(
        plan.replace("One step.", "One step. Record the observed red here.", 1)
    ) != canon(plan), "a substantive plan edit must move the canonical digest"


def test_every_governing_source_states_the_pinned_half() -> None:
    """Each rule-bearing source says substantive edits end at plan approval."""
    for relative, heading, pinned, _routing in SOURCES:
        flat = _flat(_section(relative, heading))
        for clause in pinned:
            assert clause in flat, (
                f"{relative}: missing pinned clause {clause!r} — post-approval "
                "mutability guidance must agree with the approved-artifact hash guards"
            )


def test_every_governing_source_routes_observations_to_the_ledger() -> None:
    """Each source that owns a destination sends an observation to the ledger.

    Separate from the pinned half on purpose: deleting a routing clause while
    leaving the mutability clause intact is the regression that the first
    revision of this module could not see.
    """
    for relative, heading, _pinned, routing in SOURCES:
        if not routing:
            continue
        flat = _flat(_section(relative, heading))
        for clause in routing:
            assert clause in flat, (
                f"{relative}: missing ledger-routing clause {clause!r} — an "
                "execution observation must have a destination outside the "
                "approved artifacts"
            )


def test_no_governing_source_carries_a_retired_edit_licence() -> None:
    """Bounded regression backstop against the specific wordings that caused the defect."""
    for relative, heading, _pinned, _routing in SOURCES:
        flat = _flat(_section(relative, heading))
        for licence in RETIRED_LICENCES:
            assert licence not in flat, (
                f"{relative}: retired edit licence {licence!r} is back — post-approval "
                "mutability guidance must agree with the approved-artifact hash guards"
            )


def test_how_to_keeps_immutability_and_routes_to_the_ledger() -> None:
    """The public how-to keeps its own rule and names the ledger destination."""
    relative = "guides/core/how-to/plan-and-execute-non-trivial-work.md"
    flat = _flat(_section(relative, "### Spec amendment mid-flight"))

    assert "the approved plan is immutable in substance" in flat, (
        f"{relative}: the retained immutability statement is gone"
    )
    assert (
        "Anything else — task text, a `Depends on:` edge, re-indenting a criterion, "
        "or free text appended after the status token — invalidates it." in flat
    ), f"{relative}: the enumeration of invalidating edits must stay one contiguous clause"
    assert "verification-ledger procedure" in flat, (
        f"{relative}: missing the ledger-routing clause"
    )


def test_work_loop_points_at_the_procedure_without_restating_it() -> None:
    """Step 2 stays a resolvable pointer, not a seventh home for the rule."""
    relative = "packs/core/.apm/skills/work-loop/SKILL.md"
    execute = _section(relative, "## Step 2. EXECUTE")
    pointer = (
        "**Execution observations:** follow the [verification-ledger procedure]"
        "(references/delivery-contract-lifecycle.md#verification-ledger)."
    )

    assert pointer in execute, f"{relative}: Step 2 must carry the ledger pointer verbatim"
    for licence in RETIRED_LICENCES:
        assert licence not in _flat(execute), (
            f"{relative}: Step 2 must not restate the mutability rule ({licence!r})"
        )
    for marker in RESTATED_RULE_MARKERS:
        assert marker not in _flat(execute), (
            f"{relative}: Step 2 restates the mutability rule with marker {marker!r}"
        )


def test_the_ledger_destination_resolves_to_one_owning_reference() -> None:
    """The path the sources name is defined in exactly one place."""
    lifecycle = "packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md"
    flat = _flat(_section(lifecycle, "## Verification ledger"))
    assert "docs/specs/<feature>/notes/verification-ledger.md" in flat, (
        f"{lifecycle}: the owning reference must state the ledger path"
    )
    # Portability: shipped pack content cites no repository-internal record.
    assert "docs/specs/verification-ledger" not in flat, (
        f"{lifecycle}: pack content must not cite this repository's own spec"
    )


def test_the_core_release_surfaces_agree() -> None:
    """Pack and plugin carry one version and the changelog leads with it."""
    import tomllib

    pack = tomllib.loads(_read("packs/core/pack.toml"))["pack"]["version"]
    plugin = json.loads(_read("packs/core/.claude-plugin/plugin.json"))["version"]
    assert pack == plugin, f"core pack {pack} and plugin {plugin} must agree"

    changelog = _read("docs/product/changelog.md")
    core_headings = re.findall(r"^## \[core\]\[([^\]]+)\]", changelog, re.MULTILINE)
    assert core_headings, "changelog carries no [core] release heading"
    assert core_headings[0] == pack, (
        f"topmost [core] changelog heading is {core_headings[0]}, not the shipped {pack}"
    )


#: Every guarded region, as `(path, anchor)`, pinned independently of `SOURCES`.
#: Path membership alone is not enough once one path owns several regions: two
#: rows of `CONVENTIONS.md` can become one and leave the distinct-path tuple
#: unchanged, so the deleted region's clauses stop being asserted while every
#: test stays green. That is the round-2 defect — a table that both defines and
#: drives its own assertions — recurring one level down, so the regions are
#: enumerated here too.
AC3_REQUIRED_REGIONS = (
    ("packs/core/seeds/docs/CONVENTIONS.md", "### A spec directory freezes as a unit, when the spec ships"),
    ("packs/core/seeds/docs/CONVENTIONS.md", "**`plan.md` is the implementation strategy.**"),
    ("packs/core/seeds/docs/CONVENTIONS.md", "**Lifecycle:** specs are"),
    ("packs/core/.apm/skills/new-spec/assets/plan.md", None),
    ("packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md", "## Verification ledger"),
    ("guides/core/explanation/why-the-plan-owns-the-lld.md", "## The shape of the answer"),
    ("packs/core/.apm/skills/work-loop/references/pre-execute-review.md", "## Mid-EXECUTE re-plan — Phase-1 note"),
    ("packs/core/.apm/skills/work-loop/references/state-schema.md", "**What the pin covers.**"),
)

#: AC3's closed set, pinned independently of `SOURCES` so deleting a row from
#: one cannot silently shrink the other.
AC3_REQUIRED_SOURCES = (
    "packs/core/seeds/docs/CONVENTIONS.md",
    "packs/core/.apm/skills/new-spec/assets/plan.md",
    "packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md",
    "guides/core/explanation/why-the-plan-owns-the-lld.md",
    "packs/core/.apm/skills/work-loop/references/pre-execute-review.md",
    "packs/core/.apm/skills/work-loop/references/state-schema.md",
)

#: The canonical path, or a resolvable pointer to the section that owns it.
LEDGER_DESTINATIONS = (
    "notes/verification-ledger.md",
    "delivery-contract-lifecycle.md#verification-ledger",
    "plan-and-execute-non-trivial-work.md",
)


def test_the_closed_source_set_keeps_every_member_ac3_names() -> None:
    """Deleting a path from `SOURCES` must fail here rather than shrink the guard.

    A path may have several rows because independently guarded regions can be
    far apart in one source. `SOURCES` both defines and is iterated by the
    clause tests, so a removed path takes its own assertions with it and every
    other test stays green. Pinning first-appearance path membership to the
    criterion closes that without treating multiple regions as new sources.
    """
    covered = tuple(
        dict.fromkeys(relative for relative, _anchor, _pinned, _routing in SOURCES)
    )
    assert covered == AC3_REQUIRED_SOURCES, (
        "SOURCES no longer matches AC3's closed set of six rule-bearing sources; "
        f"missing {sorted(set(AC3_REQUIRED_SOURCES) - set(covered))!r}, "
        f"unexpected {sorted(set(covered) - set(AC3_REQUIRED_SOURCES))!r}"
    )

    regions = tuple((relative, anchor) for relative, anchor, _pinned, _routing in SOURCES)
    assert regions == AC3_REQUIRED_REGIONS, (
        "SOURCES no longer guards every enumerated region; dropping one leaves "
        "its clauses unasserted while the distinct-path tuple still matches. "
        f"missing {sorted(set(AC3_REQUIRED_REGIONS) - set(regions))!r}, "
        f"unexpected {sorted(set(regions) - set(AC3_REQUIRED_REGIONS))!r}"
    )


def test_every_routing_surface_names_one_canonical_destination() -> None:
    """A source may not invent its own ledger path.

    Carrying the word "ledger" is not agreement: a source could route an
    observation to `notes/execution-log.md` and still read plausibly.
    """
    for relative, _anchor, _pinned, routing in SOURCES:
        if not routing:
            continue
        flat = _flat(
            "\n".join(
                _section(candidate, anchor)
                for candidate, anchor, _pinned, _routing in SOURCES
                if candidate == relative
            )
        )
        assert any(dest in flat for dest in LEDGER_DESTINATIONS), (
            f"{relative}: routes an execution observation somewhere other than the "
            f"canonical destination — expected one of {LEDGER_DESTINATIONS!r}"
        )


def test_the_core_release_heading_sits_directly_beneath_unreleased() -> None:
    """AC4 requires adjacency, which "first [core] heading anywhere" does not give."""
    import tomllib

    changelog = _read("docs/product/changelog.md")
    following = re.findall(
        r"^## \[([^\]]+)\]\[([^\]]+)\]",
        changelog[changelog.index("## [Unreleased]") :],
        re.MULTILINE,
    )
    assert following, "no versioned release heading follows [Unreleased]"
    artifact, version = following[0]
    pack = tomllib.loads(_read("packs/core/pack.toml"))["pack"]["version"]
    assert artifact == "core", (
        f"the heading directly beneath [Unreleased] is [{artifact}], not [core]"
    )
    assert version == pack, (
        f"the heading directly beneath [Unreleased] is core {version}, "
        f"not the shipped {pack}"
    )
