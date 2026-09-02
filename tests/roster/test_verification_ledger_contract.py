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

The closed set of rule-bearing sources is the six in `SOURCES`. `SKILL.md` is a
pure pointer and carries no rule of its own; the how-to keeps its own
pre-existing immutability statement plus a routing clause.
"""

from __future__ import annotations

import importlib.util
import json
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
        terminator = rf"\n#{{1,{depth}}} "
    else:
        terminator = r"\n\*\*[A-Z]|\n#{1,6} "
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
        ("An observation produced by execution belongs in the sibling verification ledger",),
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


def test_the_guard_pins_both_approved_artifacts_and_admits_executing() -> None:
    """Exercise the real guard: `Executing` is legal, a substantive edit is not."""
    guards = _load_guards()

    legal = guards._LEGAL_AFTER_APPROVAL
    assert "Executing" in legal["plan.md"], "plan.md must admit Executing after approval"
    assert "Implementing" in legal["spec.md"], "spec.md must admit Implementing after approval"

    spec_dir = ROOT / "docs/specs/verification-ledger"
    baseline_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")
    baseline_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")

    # The two documented exemptions must not move the digest.
    plan_text = (spec_dir / "plan.md").read_text(encoding="utf-8")
    assert "- **Status:** Approved" in plan_text
    exempt = plan_text.replace("- **Status:** Approved", "- **Status:** Executing", 1)
    assert guards.canonical_contract(exempt, ac_section_only=False) == guards.canonical_contract(
        plan_text, ac_section_only=False
    ), "the preamble status token must stay exempt from the pin"

    # A substantive edit must move it. This is the property every governing
    # source below describes in prose.
    substantive = plan_text.replace(
        "## Approach", "## Approach\n\nAn execution observation is recorded here.", 1
    )
    assert guards.canonical_contract(
        substantive, ac_section_only=False
    ) != guards.canonical_contract(plan_text, ac_section_only=False), (
        "a substantive plan edit must move the canonical digest"
    )
    assert baseline_plan and baseline_spec, "both approved artifacts must hash"


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
