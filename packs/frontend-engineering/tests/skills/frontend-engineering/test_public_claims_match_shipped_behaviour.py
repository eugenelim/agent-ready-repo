"""Holds the pack's public claims to the behaviour it actually ships.

The pack README and the main skill both describe the verify-mode gate run. Each
had drifted from the GATES phase that performs it: the README promised a
typecheck, a Playwright baseline and a Core Web Vitals measurement that no gate
runs, and the skill's verify procedure enumerated four of the five gates the
GATES phase ships and then said "four" twice in the prose beneath.

Every gate assertion below reads the GATES phase headings for its expectation
rather than restating a count or a step number. A literal `5` here would pass
while a sixth gate shipped unenumerated, which is the failure this file exists to
catch: the verify list went stale exactly because nothing read the section it
summarises.

One assertion is a **one-way rule** rather than a derivation, and says so at its
own site: the count check on the fifth verify step reds a step that characterises
the gates above it *by number*, and does not reach the same false claim phrased
without one.

Scope note. The claim guards read a *bounded region* — the README's verify
bullet, the skill's state-matrix section — not the whole file. Two real
collisions are why: `baseline` appears honestly in the README's
deep-accessibility-audit job (the stated WCAG 2.2 AA gap) and `Playwright` in its
`Reads:` bullet, so a file-wide search for either would red on a legitimate
sentence. The percentage check is bounded differently again — by the
rationale/table split inside the state-matrix section, which puts the
`200–400% zoom` row out of its reach. A guard that cannot say which region it
read cannot say what its green means.

Those two collisions are named by their bullet rather than by line number on
purpose: an earlier version of this note cited them as `README.md:39` and `:74`,
and a deletion one line above the second staled it within the same change.
"""

from __future__ import annotations

import re

import pytest
from frontend_engineering_rendered_page_rules import PACK_ROOT, read_skill

README = PACK_ROOT / "README.md"

# `five` is not the expected gate count. It is how the prose spells whatever
# count the GATES phase headings yield, so a sixth gate reds the prose guard
# on its assertion — naming the count the prose should carry — rather than
# passing on a stale literal. The table runs to `six` deliberately, so that
# case reports the missing count instead of a bare lookup failure.
NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill() -> str:
    return read_skill()


# ── section readers ─────────────────────────────────────────────────────────


def _section(markdown: str, heading: str) -> str:
    """The body under ``heading``, up to the next heading at the same level."""
    level = heading.split(" ", 1)[0]
    parts = markdown.split(f"\n{heading}\n", 1)
    assert len(parts) == 2, f"{heading!r} is gone from the file"
    body = parts[1]
    end = body.find(f"\n{level} ")
    return body[:end] if end != -1 else body


def _readme_verify_bullet(readme_markdown: str) -> str:
    """The README's `Verify a surface before shipping` job, bolded heading to blank line."""
    marker = "**Verify a surface before shipping**"
    assert marker in readme_markdown, "the README no longer describes verify mode"
    body = readme_markdown.split(marker, 1)[1]
    end = body.find("\n\n")
    return body[:end] if end != -1 else body


def gates_phase_gates(skill_markdown: str) -> list[tuple[int, str]]:
    """`(number, name)` for every numbered gate the GATES phase ships, in order.

    The name is the heading text with its trailing parenthetical tooling note
    dropped, because the verify list does not repeat those notes.
    """
    section = _section(skill_markdown, "## GATES phase — Verification")
    gates = []
    for match in re.finditer(r"^### (\d+)\. (.+)$", section, re.MULTILINE):
        name = re.sub(r"\s*\([^()]*\)\s*$", "", match.group(2)).strip()
        gates.append((int(match.group(1)), name))
    assert gates, "the GATES phase ships no numbered gates"
    return gates


def verify_mode_steps(skill_markdown: str) -> list[tuple[int, str]]:
    """`(number, bolded name)` for every step the verify procedure enumerates."""
    section = _section(skill_markdown, "### Mode: verify")
    steps = [
        (int(number), name.strip())
        for number, name in re.findall(r"^(\d+)\. \*\*(.+?)\*\*", section, re.MULTILINE)
    ]
    assert steps, "the verify procedure enumerates no steps"
    return steps


def verify_mode_section(skill_markdown: str) -> str:
    return _section(skill_markdown, "### Mode: verify")


# ── 1. the README's verify promise names no absent capability ───────────────


@pytest.mark.parametrize(
    "absent",
    [
        # A typecheck gate. The GATES phase ships none, and the pack adds no
        # TypeScript toolchain.
        "typecheck",
        # A screenshot-baseline comparison. Gate 5 states, in the skill, that it
        # ships no baseline and compares against no stored image.
        "playwright",
        "baseline",
        "stored image",
    ],
)
def test_the_readme_verify_promise_claims_no_absent_capability(
    readme: str, absent: str
) -> None:
    bullet = _readme_verify_bullet(readme).lower()
    assert absent not in bullet, (
        f"the README's verify job claims {absent!r}, which the GATES phase "
        "does not ship"
    )


def test_the_readme_verify_promise_presents_no_unmeasured_cwv_gate(
    readme: str,
) -> None:
    """No gate measures Core Web Vitals, so the verify promise may not list one.

    `perf result` remains a field of the evidence manifest, and the README may
    still say so elsewhere. What it may not do is present CWV measurement as one
    of the gates this sequence runs.
    """
    bullet = _readme_verify_bullet(readme)
    gate_names = " ".join(name for _, name in gates_phase_gates(read_skill())).lower()
    assert "core web vital" not in gate_names and "cwv" not in gate_names, (
        "a gate now measures CWV — this guard's premise is stale and the README "
        "claim it forbids may be legitimate again"
    )
    for claim in ("cwv measurement", "core web vitals measurement"):
        assert claim not in bullet.lower(), (
            f"the README's verify job presents {claim!r} as a gate, but no gate "
            "measures it"
        )


def test_the_readme_verify_promise_does_not_deny_the_manifest_write(
    readme: str,
) -> None:
    """Verify mode writes the evidence manifest, so it is not read-only.

    The README once said both in one sentence. Either half alone is defensible;
    the contradiction is not.
    """
    bullet = _readme_verify_bullet(readme)
    lowered = bullet.lower()
    assert "evidence manifest" in lowered, (
        "the README's verify job no longer mentions the evidence manifest it writes"
    )
    for denial in ("read-only", "read only", "no writes"):
        assert denial not in lowered, (
            f"the README's verify job claims {denial!r} while the run writes the "
            "evidence manifest"
        )


# ── 2. the worked example carries no unexecuted measurement ─────────────────


def test_the_worked_example_shows_no_fabricated_metric_values(readme: str) -> None:
    """The example run reported three CWV numbers no run produced.

    Scoped to the fenced `How it works` transcript, which is the only place the
    README speaks in the voice of a completed run. A number in prose elsewhere is
    a claim about the pack, not a claim about a run that happened.
    """
    transcript = _section(readme, "## How it works")
    for metric in ("LCP", "CLS", "INP"):
        assert not re.search(rf"\b{metric}\b\s*[:=]?\s*[\d.]", transcript), (
            f"the worked example reports a {metric} value, but the gate sequence "
            "measures none"
        )


# ── 3. the worked example's genre route agrees with the routing table ───────


def genre_routing_table(skill_markdown: str) -> list[tuple[str, str]]:
    """`(surface type, skill)` for every row of the § 1b routing table."""
    section = _section(skill_markdown, "### 1b. Genre routing (T2 — requires experience-design pack)")
    rows = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[1].startswith("---") or cells[1] == "Load":
            continue
        skill_name = cells[1].strip("`")
        if skill_name:
            rows.append((cells[0], skill_name))
    assert rows, "the genre routing table has no rows"
    return rows


def test_the_example_genre_route_is_the_one_the_table_names(
    readme: str, skill: str
) -> None:
    """A notification panel is a component interaction, so the table decides.

    The expectation is read from the table row covering interactions, never
    written here: rename the skill in the table and this test follows it, delete
    the row and this test reds.
    """
    interaction_rows = [
        skill_name
        for surface, skill_name in genre_routing_table(skill)
        if "interaction" in surface.lower()
    ]
    assert len(interaction_rows) == 1, (
        f"expected exactly one routing row for interaction surfaces, got "
        f"{interaction_rows}"
    )
    expected = interaction_rows[0]

    transcript = _section(readme, "## How it works")
    match = re.search(r"Genre route:\s*([a-z0-9-]+)", transcript)
    assert match, "the worked example no longer shows a genre route"
    assert match.group(1) == expected, (
        f"the notification-panel example routes to {match.group(1)!r}, but the "
        f"routing table sends a component interaction to {expected!r}"
    )


# ── 4. the state matrix instructs without citing an invented source ─────────


def test_the_state_matrix_cites_no_unsupported_statistic(skill: str) -> None:
    """The rationale carried a 2025 study of 50 dashboards that does not exist.

    Two shapes are refused in this one section: a percentage, and the vocabulary
    of a citation. The operational instruction is asserted separately below, so
    removing the claim cannot take the instruction with it.
    """
    section = _section(skill, "### 3. State matrix")
    rationale = section.split("\n\n| State |", 1)[0]
    assert not re.search(r"\d+\s*%", rationale), (
        "the state-matrix rationale cites a percentage; state the rule instead"
    )
    for citation_word in ("study", "survey", "research found", "researchers"):
        assert citation_word not in rationale.lower(), (
            f"the state-matrix rationale cites a {citation_word!r} the pack "
            "cannot source"
        )


def test_the_state_matrix_still_instructs_enumeration(skill: str) -> None:
    """The useful half of that paragraph. Removing the statistic kept it."""
    section = _section(skill, "### 3. State matrix")
    rationale = section.split("\n\n| State |", 1)[0].lower()
    assert "enumerate" in rationale, (
        "the state-matrix rationale no longer instructs enumeration"
    )
    for state in ("empty", "error"):
        assert state in rationale, (
            f"the state-matrix rationale no longer names the {state} state as one "
            "to enumerate explicitly"
        )


# ── 5. verify mode enumerates every gate the GATES phase ships ──────────────


def test_verify_mode_enumerates_every_gate_in_order(skill: str) -> None:
    """One verify step per shipped gate, same numbers, same names.

    This is the guard the drift needed. Gate 5 shipped, the Visual QA checklist
    already required it, and the verify procedure listed four steps — because
    nothing compared the two lists.
    """
    gates = gates_phase_gates(skill)
    steps = verify_mode_steps(skill)
    assert [number for number, _ in steps] == [number for number, _ in gates], (
        f"verify mode enumerates steps {[n for n, _ in steps]} but the GATES "
        f"phase ships gates {[n for n, _ in gates]}"
    )
    for (gate_number, gate_name), (_, step_name) in zip(gates, steps, strict=True):
        assert step_name == gate_name, (
            f"verify step {gate_number} is named {step_name!r} but GATES phase "
            f"step {gate_number} is {gate_name!r}"
        )


def test_verify_mode_prose_states_the_shipped_gate_count(skill: str) -> None:
    """The two counts in the paragraph beneath the list, derived not pinned."""
    count = len(gates_phase_gates(skill))
    word = NUMBER_WORDS[count]
    section = verify_mode_section(skill)
    for phrase in (f"all {word} gates", f"reports {word} green gates"):
        assert phrase in section, (
            f"the verify procedure does not say {phrase!r}; the GATES phase ships "
            f"{count} gates"
        )
    for wrong in set(NUMBER_WORDS.values()) - {word}:
        assert f"all {wrong} gates" not in section, (
            f"the verify procedure still says 'all {wrong} gates'"
        )
        assert f"reports {wrong} green gates" not in section, (
            f"the verify procedure still says 'reports {wrong} green gates'"
        )


def inspection_gate_number(skill_markdown: str) -> int:
    """The GATES phase number of the rendered-page inspection gate.

    Read rather than pinned, so inserting a gate before the inspection retargets
    this guard onto the inspection's new position instead of onto whichever step
    happens to be fifth. Pinning `5` would have left the guard reading the wrong
    step in silence — the mirror of the staleness it exists to catch.
    """
    for number, name in gates_phase_gates(skill_markdown):
        if name == "Rendered-page inspection":
            return number
    raise AssertionError(
        "the GATES phase ships no gate named 'Rendered-page inspection'"
    )


def test_verify_mode_points_at_the_inspection_gate_without_restating_it(
    skill: str,
) -> None:
    """The inspection step routes the reader to the section that owns the rules.

    The inspection gate's capture, judgement, privacy, completeness and
    no-baseline rules live in its own section and its reference. The verify list
    may name the gate; it may not become a second, drifting copy of those rules.
    """
    number = inspection_gate_number(skill)
    section = verify_mode_section(skill)
    fifth = [line for line in section.splitlines() if line.startswith(f"{number}. ")]
    assert len(fifth) == 1, (
        f"the verify procedure has no single step {number}, which is where the "
        "GATES phase puts the rendered-page inspection"
    )
    line = fifth[0]
    assert f"GATES phase step {number}" in line, (
        "the inspection verify step does not point at the section that defines it"
    )
    assert "channel" not in line.lower() and "viewport" not in line.lower(), (
        "the fifth verify step restates Gate 5's completeness rules instead of "
        "pointing at them"
    )
    # A ONE-WAY RULE, not a derivation of the class. The step may not
    # characterise the other gates by number: an earlier version said "the four
    # gates above never open the page", which is false — Gate 4's checklist
    # opens a browser for print preview — and which widened the inspection
    # section's own accurate three-gate statement. Any count in this line is
    # that shape returning. What this does NOT reach is the same false claim
    # with the number dropped ("the gates above never open the page"); that is a
    # stated blind spot, and the remedy for it is that the step carries no
    # rationale at all.
    counts = set(re.findall(r"\b(?:one|two|three|four|five|six|seven)\b", line.lower()))
    assert not counts, (
        f"the inspection verify step makes a counting claim about the other "
        f"gates ({sorted(counts)}); it may name its gate and point at the "
        "section, which owns what the gates above it do"
    )
    digits = set(re.findall(r"\d+", line)) - {str(number)}
    assert not digits, (
        f"the inspection verify step carries the numbers {sorted(digits)}; only "
        "its own step number belongs in it"
    )


# ── 6. Gate 5's no-baseline contract is untouched ───────────────────────────

# Byte-exact on purpose. This sentence is the whole reason the README may not
# promise a stored-image baseline; the guard above is only as strong as this one.
GATE_FIVE_NO_BASELINE = (
    "This step ships no baseline and compares against no stored image"
)


def test_gate_five_still_ships_no_baseline(skill: str) -> None:
    assert GATE_FIVE_NO_BASELINE in skill, (
        "Gate 5 no longer states that it ships no baseline and compares against "
        "no stored image — the README guard above rests on this sentence"
    )


# ── 7. the README offers every route its own example takes ──────────────────
#
# Correcting the example's route to `interaction-design` exposed a second
# contradiction rather than creating one: the create-mode job above it offered a
# closed three-item list that never included it, so the README named a route it
# did not offer. Both halves are read from the artifacts — the offered set from
# the README's own route list, the legitimate set from the skill's § 1b table —
# so neither can drift alone. Neither half states a route name here.


def readme_offered_genre_skills(readme_markdown: str) -> set[str]:
    """The genre skills the README's create-mode job offers as routes.

    Read from the em-dash-delimited route list inside the job's parenthetical,
    and matched on **any** backticked identifier rather than on a `-design`
    suffix. The suffix was the first shape of this reader and it was wrong:
    `design-system-foundations` is a routable genre skill (`SKILL.md` § 1b) that
    does not carry it, so a README offering that route was invisible here — the
    example guard would have red on a correct README and the routability guard
    would have passed over an unroutable name.

    Scoping to the list segment rather than the whole sentence is what lets the
    pattern stay general: the co-install pack is named outside the segment, so
    it needs no subtracting, and a name moved into the segment reds the
    routability guard instead of being silently excused. A job whose
    parenthetical loses that structure reds here rather than returning a
    narrower set.

    The span is the whole middle of the `pick …` parenthetical, taken by
    splitting it on em dashes and requiring exactly three parts. Both looser
    readings were wrong and each failed in the opposite direction: a greedy match
    over the job body widened the span across "if `experience-design` is
    co-installed" and swallowed the pack name, and a non-greedy match inside the
    parenthetical shortened it to a prefix when a second dash pair appeared,
    silently excusing every route after it. Splitting reds on either, because
    either changes the part count.
    """
    job = readme_markdown.split("**Create a new surface from a design handoff**", 1)
    assert len(job) == 2, "the README no longer describes the create-mode job"
    body = job[1].split("\n\n", 1)[0]
    parenthetical = re.search(r"\(pick ([^()]*)\)", body, re.DOTALL)
    assert parenthetical, (
        "the create-mode job no longer offers its routes in a `(pick …)` "
        "parenthetical, so the offered routes cannot be located"
    )
    parts = parenthetical.group(1).split("—")
    assert len(parts) == 3, (
        f"the create-mode job's `(pick …)` parenthetical splits into "
        f"{len(parts)} em-dash-delimited parts, not 3, so its route list can no "
        "longer be told from the prose around it"
    )
    offered = set(re.findall(r"`([a-z][a-z0-9-]+)`", parts[1]))
    assert offered, "the create-mode job offers no genre skill"
    return offered


def test_the_readme_offers_the_route_its_own_example_takes(readme: str) -> None:
    offered = readme_offered_genre_skills(readme)
    transcript = _section(readme, "## How it works")
    match = re.search(r"Genre route:\s*([a-z0-9-]+)", transcript)
    assert match, "the worked example no longer shows a genre route"
    assert match.group(1) in offered, (
        f"the example routes to {match.group(1)!r}, which the README's own route "
        f"list does not offer: {sorted(offered)}"
    )


def test_every_route_the_readme_offers_is_one_the_skill_routes_to(
    readme: str, skill: str
) -> None:
    """The README may not invent a genre skill the routing table does not name."""
    routable = {skill_name for _, skill_name in genre_routing_table(skill)}
    for offered in readme_offered_genre_skills(readme):
        assert offered in routable, (
            f"the README offers {offered!r} as a genre route, but the skill's "
            f"routing table does not name it"
        )
