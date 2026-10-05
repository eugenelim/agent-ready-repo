"""The experience-design → frontend-engineering visual handoff, across the pack boundary.

Both packs are installed into one temporary repository through `agentbundle
install`, and every rule this module applies is parsed from that installation —
never from `packs/` source — so a drift in either pack's shipped contract, in the
fixtures, or in the golden eval cases turns this module red.

The walk below evaluates the installed tables over a fixture design tree. It
decides nothing a table cell does not decide: any vocabulary it does not know
raises, and the mutation tests prove the cells, not this code, drive the route.
Nothing here renders. Run records are fixture data describing a run; this module
claims no visual verification.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import re
import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "visual-handoff-golden-path"
SCENARIOS = (
    "confirmed",
    "unconfirmed",
    "missing-taxonomy",
    "unresolved-domain",
    "standalone",
    "refusal",
    "silent-domain",
)
PACKS = ("experience-design", "frontend-engineering")
FALLBACK = "references/fallback-tokens.md"


def test_every_scenario_fixture_is_present() -> None:
    """Verifies AC-0001's surface: each of the six paths has a fixture tree."""
    missing = [s for s in SCENARIOS if not (FIXTURES / s / "scenario.toml").is_file()]
    assert not missing, f"scenario fixtures missing: {missing}"


# ── installation ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def skills(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Install both packs into one repository; return its `.claude/skills`."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    tmp = tmp_path_factory.mktemp("visual-handoff")
    home, repo, catalogue = tmp / "home", tmp / "repo", tmp / "catalogue"
    home.mkdir()
    repo.mkdir()
    for pack in PACKS:
        shutil.copytree(REPO_ROOT / "packs" / pack, catalogue / "packs" / pack)
    with patch.dict(os.environ, {"HOME": str(home), "USERPROFILE": str(home)}):
        for pack in PACKS:
            args = _build_parser().parse_args([
                "install",
                str(catalogue),
                "--pack",
                pack,
                "--output",
                str(repo),
                "--scope",
                "repo",
                "--adapter",
                "claude-code",
            ])
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                rc = install.run(args)
            assert rc == 0, f"installing {pack} failed:\n{out.getvalue()}"
    return repo / ".claude" / "skills"


# ── reading installed Markdown ───────────────────────────────────────────────


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table_after(text: str, anchor: str, *, where: str) -> list[dict[str, str]]:
    """The first Markdown table after `anchor`, as header-keyed rows."""
    assert anchor in text, f"{where}: no {anchor!r} in the installed copy"
    rest = text.split(anchor, 1)[1]
    # An anchor that is itself a table's header row starts that table.
    lines = (anchor + rest if anchor.startswith("|") else rest).splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("|")), None)
    assert start is not None, f"{where}: no table after {anchor!r}"
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append(line)
    header = _cells(rows[0])
    return [dict(zip(header, _cells(r), strict=True)) for r in rows[2:]]


def _rule_table(text: str, heading: str, *, where: str) -> dict[str, str]:
    """A two-column `Rule | Value` (or `Rung`-keyed) table as a mapping."""
    return {
        list(row.values())[0]: list(row.values())[1]
        for row in _table_after(text, heading, where=where)
    }


def _ticked(cell: str) -> str:
    return cell.strip().strip("`")


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    block = text[4:].split("\n---", 1)[0]
    out = {}
    for line in block.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip('"')
    return out


@dataclass(frozen=True)
class Rules:
    """Every installed rule the walk applies, parsed once."""

    precedence: list[dict[str, str]]
    gaps: dict[str, str]
    standalone: dict[str, str]
    refusals: dict[str, str]
    read_paths: list[tuple[str, str]]
    refusal_records: dict[str, str]
    slug_pattern: str
    slug_max_length: int
    no_design_section_skip: str
    visual_target_values: tuple[str, ...]
    domains: tuple[str, ...]

    @classmethod
    def load(cls, skills: Path, *, observation: str | None = None) -> Rules:
        fe = skills / "frontend-engineering"
        vo_where = "frontend-engineering references/visual-observation.md"
        vo = (
            observation
            if observation is not None
            else (fe / "references" / "visual-observation.md").read_text(encoding="utf-8")
        )
        dh = (fe / "references" / "design-handoff.md").read_text(encoding="utf-8")
        skill = (fe / "SKILL.md").read_text(encoding="utf-8")
        cd = (
            skills / "creative-direction" / "assets" / "creative-direction-template.md"
        ).read_text(encoding="utf-8")
        tt = (skills / "design-system" / "assets" / "token-taxonomy-template.md").read_text(
            encoding="utf-8"
        )

        flat = " ".join(skill.split())
        slug = re.search(r"not matching `(\^[^`]+\$)`, or over (\d+) characters", flat)
        assert slug, "frontend SKILL.md: no slug pattern and length bound"
        skip = re.search(r"named skip, `(design handoff: [^`]*\[design\][^`]*)`", flat)
        assert skip, "frontend SKILL.md: no named skip for a missing [design] section"
        vt = re.search(r'^visual_target: "<([^>]+)>"', cd, re.M)
        assert vt, "creative-direction template: no visual_target values"
        return cls(
            precedence=_table_after(vo, "## Authority precedence", where=vo_where),
            gaps=_rule_table(vo, "## Upstream gaps", where=vo_where),
            standalone=_rule_table(vo, "## Standalone work", where=vo_where),
            refusals=_rule_table(vo, "## Refusals are not demotions", where=vo_where),
            read_paths=[
                (_ticked(r["Read path"]), _ticked(r["Required `type:`"]))
                for r in _table_after(dh, "## The three read paths", where="design-handoff.md")
            ],
            refusal_records={
                r["Refusal"]: _ticked(r["Record"])
                for r in _table_after(dh, "## The six refusals", where="design-handoff.md")
            },
            slug_pattern=slug.group(1),
            slug_max_length=int(slug.group(2)),
            no_design_section_skip=skip.group(1),
            visual_target_values=tuple(v.strip() for v in vt.group(1).split("|")),
            domains=tuple(row["Domain"] for row in _authority_rows(tt, "token-taxonomy template")),
        )


def _authority_rows(text: str, where: str) -> list[dict[str, str]]:
    anchor = "| Domain | Rung that supplied it |"
    assert anchor in text, f"{where}: no Authority domain table"
    lines = text.split(anchor, 1)[1].splitlines()[2:]
    rows = []
    for line in lines:
        if not line.startswith("|"):
            break
        domain, rung = _cells(line)[:2]
        rows.append({"Domain": domain, "Rung": rung})
    return rows


# ── the walk ─────────────────────────────────────────────────────────────────


@dataclass
class Read:
    """What the handoff read produced for one fixture."""

    completed: bool
    record: str | None = None
    artifacts: dict[str, dict] = field(default_factory=dict)


@dataclass
class Route:
    """What the walk decided for one fixture."""

    read: Read
    composition: str | None
    values: str | None
    domains: dict[str, object]
    gap_records: list[dict[str, object]]
    loaded: set[str]
    notes: list[str]


def _read_handoff(rules: Rules, tree: Path, slug: str) -> Read:
    layout = tree / "agentbundle-layout.toml"
    config = tomllib.loads(layout.read_text(encoding="utf-8")) if layout.is_file() else {}
    if "design" not in config:
        return Read(completed=True, record=rules.no_design_section_skip)
    if len(slug) > rules.slug_max_length or not re.fullmatch(rules.slug_pattern, slug):
        template = next(v for k, v in rules.refusal_records.items() if k.startswith("Slug"))
        record = re.sub(r"<[^>]+>", f"does not match {rules.slug_pattern}", template)
        return Read(completed=False, record=record)
    root = tree / config["design"]["output_dir"]
    artifacts = {}
    for read_path, required_type in rules.read_paths:
        if "<screen>" in read_path:
            continue  # this fixture set carries no per-screen briefs
        path = root / read_path.replace("<slug>", slug)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if _frontmatter(text).get("type") != required_type:
            continue
        artifacts[required_type] = {"frontmatter": _frontmatter(text), "body": text}
    return Read(completed=True, artifacts=artifacts)


def _unresolved_domains(taxonomy: dict | None) -> list[str]:
    if taxonomy is None:
        return []
    return [
        row["Domain"]
        for row in _authority_rows(taxonomy["body"], "fixture taxonomy")
        if _ticked(row["Rung"]) == "unresolved"
    ]


def walk(rules: Rules, scenario: str, *, tree: Path | None = None) -> Route:
    """Resolve one fixture through the installed tables."""
    tree = tree or FIXTURES / scenario
    facts = tomllib.loads((tree / "scenario.toml").read_text(encoding="utf-8"))
    loaded = {"references/design-handoff.md", "references/visual-observation.md"}
    read = _read_handoff(rules, tree, facts["slug"])
    notes: list[str] = []

    if not read.completed:
        demotes = rules.refusals["refusal-demotes"]
        if demotes == "never":
            return Route(read, None, None, {}, [], loaded, notes)
        if demotes != "always":
            raise ValueError(f"unknown refusal-demotes value {demotes!r}")
        notes.append("refusal absorbed into a demotion")

    direction = read.artifacts.get("creative-direction")
    taxonomy = read.artifacts.get("token-taxonomy")
    incumbent = bool(facts["incumbent_system"])

    # Gap sources, as the installed gap-sources cell names them.
    sources = rules.gaps["gap-sources"]
    assert "named skip" in sources and "needed domain unresolved" in sources, sources
    assert "leaves a domain silent" in sources, sources
    kinds = re.findall(r"`([a-z-]+)`", rules.gaps["gap-record-contents"])
    supply_kind, completion_kind = kinds[0], kinds[1]
    fields_match = re.search(
        r"persists only the (.+?) and one fixed (.+?):", rules.gaps["gap-record-contents"]
    )
    assert fields_match, rules.gaps["gap-record-contents"]
    gap_fields = (fields_match.group(1), fields_match.group(2))

    held: list[tuple[str, str]] = []
    if direction and taxonomy is None and not incumbent:
        held = [(d, supply_kind) for d in rules.domains]
    elif taxonomy is not None:
        unresolved = _unresolved_domains(taxonomy)
        held = [(d, completion_kind) for d in unresolved]
        # A needed domain the taxonomy neither gives values for nor records
        # unresolved is silent. A `### <Domain>` commitments section stands in
        # for "gives values"; every fixture section carries the values its
        # implementation sets. Need is fixture data, with no default.
        assert "needed_domains" in facts, f"{tree.name}: a resolving taxonomy needs needed_domains"
        held += [
            (d, completion_kind)
            for d in facts["needed_domains"]
            if d not in unresolved and f"\n### {d}\n" not in taxonomy["body"]
        ]

    def holds(token: str, row_index: int) -> bool:
        token = token.strip()
        if token.startswith("visual_target:"):
            value = token.split(":", 1)[1].strip()
            if value not in rules.visual_target_values:
                raise ValueError(f"unknown visual_target value {value!r}")
            return bool(direction) and direction["frontmatter"].get("visual_target") == value
        if token == "artifact-resolved":
            return bool(read.artifacts)
        if token == "established-surface":
            return incumbent
        if token == "no-higher-rung-resolved":
            return not any(predicate(r, i) for i, r in enumerate(rules.precedence[:row_index]))
        if token == "no-upstream-gap-held":
            return not held
        raise ValueError(f"unknown Requires token {token!r}")

    def predicate(row: dict[str, str], index: int) -> bool:
        return all(holds(t, index) for t in row["Requires"].split(" and "))

    holding = [r for i, r in enumerate(rules.precedence) if predicate(r, i)]
    composition = holding[0]["Rung"] if holding else None
    value_rows = [r for r in holding if not r["Binds"].startswith("Composition only")]
    values = value_rows[0]["Rung"] if value_rows else None

    if direction and direction["frontmatter"].get("visual_target") != "confirmed":
        notes.append(
            "direction does not carry visual_target: confirmed "
            f"(records {direction['frontmatter'].get('visual_target', 'nothing')})"
        )

    def admitted(token: str) -> bool:
        token = token.strip()
        if token == "no-applicable-design-artifact":
            return not read.artifacts
        if token == "no-incumbent-system":
            return not incumbent
        if token == "no-upstream-authority-to-complete":
            return not held
        if token == "handoff-read-completed":
            return read.completed
        raise ValueError(f"unknown standalone token {token!r}")

    admits = rules.standalone["admits"].split(",")
    standalone = all(admitted(t) for t in admits) and admitted(rules.standalone["requires"])
    if standalone:
        notes.append("standalone admitted: " + ", ".join(t.strip() for t in admits))
        if read.record:
            notes.append(f"reached via named skip: {read.record}")

    domains: dict[str, object] = {}
    held_domains = {d for d, _ in held}
    for domain in rules.domains:
        if domain in held_domains:
            domains[domain] = next(k for d, k in held if d == domain)
        elif taxonomy is not None:
            domains[domain] = "taxonomy"
        elif incumbent:
            domains[domain] = "incumbent"
        elif standalone:
            domains[domain] = "fallback"
        elif values == "local-premise":
            domains[domain] = "local-premise"
    if "fallback" in domains.values():
        loaded.add(FALLBACK)

    gap_records = []
    for kind in sorted({k for _, k in held}):
        gap_records.append({
            gap_fields[0]: sorted(d for d, k in held if k == kind),
            gap_fields[1]: kind,
        })
    return Route(read, composition, values, domains, gap_records, loaded, notes)


@pytest.fixture(scope="module")
def rules(skills: Path) -> Rules:
    return Rules.load(skills)


# ── the six paths (AC-0001 – AC-0008) ────────────────────────────────────────


def test_every_rule_is_read_from_the_installation(skills: Path, rules: Rules) -> None:
    """AC-0001: both packs installed; a missing installed table fails loudly."""
    for pack_skill in ("frontend-engineering", "design-system", "creative-direction"):
        assert (skills / pack_skill / "SKILL.md").is_file(), pack_skill
    assert [r["Rung"] for r in rules.precedence] == [
        "approved-visual-target",
        "direction-and-taxonomy",
        "incumbent-system",
        "local-premise",
    ]
    stripped = (
        (skills / "frontend-engineering" / "references" / "visual-observation.md")
        .read_text(encoding="utf-8")
        .replace("## Upstream gaps", "## Gaps")
    )
    with pytest.raises(AssertionError, match="Upstream gaps"):
        Rules.load(skills, observation=stripped)


def test_confirmed_target_supplies_composition_and_taxonomy_supplies_values(rules: Rules) -> None:
    """AC-0002."""
    route = walk(rules, "confirmed")
    assert route.composition == "approved-visual-target"
    assert route.values == "direction-and-taxonomy"
    assert set(route.domains.values()) == {"taxonomy"}, route.domains
    assert FALLBACK not in route.loaded


def test_unconfirmed_target_resolves_one_rung_down(rules: Rules) -> None:
    """AC-0003."""
    route = walk(rules, "unconfirmed")
    assert (route.composition, route.values) == ("direction-and-taxonomy",) * 2
    assert set(route.domains.values()) == {"taxonomy"}, route.domains
    assert any("does not carry visual_target: confirmed" in n for n in route.notes), route.notes
    assert FALLBACK not in route.loaded


def test_missing_taxonomy_holds_every_value_domain(rules: Rules) -> None:
    """AC-0004."""
    route = walk(rules, "missing-taxonomy")
    assert route.composition == "direction-and-taxonomy"
    assert set(route.domains) == set(rules.domains)
    assert set(route.domains.values()) == {"taxonomy-supply-required"}, route.domains
    assert "local-premise" not in route.domains.values()
    assert FALLBACK not in route.loaded


def test_unresolved_domain_is_held_and_routed(rules: Rules) -> None:
    """AC-0005."""
    route = walk(rules, "unresolved-domain")
    held = {d for d, v in route.domains.items() if v != "taxonomy"}
    assert held == {"Typography"}, route.domains
    assert route.domains["Typography"] == "domain-completion-required"
    assert FALLBACK not in route.loaded
    assert route.gap_records == [
        {"axes held": ["Typography"], "operation kind": "domain-completion-required"}
    ]


def test_standalone_reaches_the_explicit_fallback(rules: Rules) -> None:
    """AC-0006."""
    route = walk(rules, "standalone")
    assert route.read.record == "design handoff: no [design] section configured"
    assert route.composition == route.values == "local-premise"
    assert FALLBACK in route.loaded
    admits = [t.strip() for t in rules.standalone["admits"].split(",")]
    assert any(n == "standalone admitted: " + ", ".join(admits) for n in route.notes), route.notes


def test_refusal_halts_without_reaching_any_rung(rules: Rules) -> None:
    """AC-0007."""
    route = walk(rules, "refusal")
    assert route.read.record is not None
    assert route.read.record.startswith("design handoff: slug rejected — "), route.read.record
    assert route.composition is None and route.values is None
    assert route.domains == {}
    assert route.read.artifacts == {}
    assert FALLBACK not in route.loaded
    # The premise: under a conforming slug this same tree resolves both
    # artifacts, so the empty extraction above is the refusal's doing.
    conforming = _read_handoff(rules, FIXTURES / "refusal", "checkout")
    assert set(conforming.artifacts) == {"creative-direction", "token-taxonomy"}


def _mutated(skills: Path, old: str, new: str) -> Rules:
    path = skills / "frontend-engineering" / "references" / "visual-observation.md"
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    return Rules.load(skills, observation=text.replace(old, new))


def test_the_installed_cells_drive_the_route(skills: Path) -> None:
    """AC-0008: each mutation is in-vocabulary, so the walk completes and the
    route itself changes — a vocabulary-guard raise would fail this test."""
    demoting = _mutated(skills, "| refusal-demotes | never |", "| refusal-demotes | always |")
    route = walk(demoting, "refusal")
    assert route.composition is not None, "refusal-demotes: always reached no rung"

    retargeted = _mutated(
        skills,
        "| approved-visual-target | direction/<slug>.md | visual_target: confirmed |",
        "| approved-visual-target | direction/<slug>.md | visual_target: none |",
    )
    route = walk(retargeted, "confirmed")
    assert route.composition == "direction-and-taxonomy"


# ── concrete values: provenance and consumption (AC-0009 – AC-0013, AC-0023) ──

CONFIRMED = FIXTURES / "confirmed"
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
COLOUR_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\(")


def _section(text: str, heading: str) -> str:
    assert heading in text, f"no {heading!r}"
    return text.split(heading, 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]


def _role_table(text: str, heading: str) -> dict[str, tuple[str, str]]:
    rows = _table_after(_section(text, heading), "| Role |", where=heading)
    return {_ticked(r["Role"]): (r["Resolved value"], r["Traces to"]) for r in rows}


@pytest.fixture(scope="module")
def taxonomy() -> str:
    return (CONFIRMED / "design" / "tokens" / "checkout.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def direction() -> str:
    return (CONFIRMED / "design" / "direction" / "checkout.md").read_text(encoding="utf-8")


def _expected_declarations(taxonomy: str) -> dict[str, str]:
    """Taxonomy role → the custom property the golden implementation binds it to."""
    expected = {}
    for role, (value, _) in _role_table(taxonomy, "### Color").items():
        expected["--color-" + role.replace(".", "-")] = value
    for role, (value, _) in _role_table(taxonomy, "### Spacing and rhythm").items():
        expected["--" + role.replace(".", "-")] = value
    return expected


def _declarations(css: str) -> dict[str, str]:
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", css))


# Properties whose value must come from a role, never a literal, in the markup.
ROLE_BOUND = re.compile(
    r"(?<![\w-])(color|background(?:-color)?|gap|padding[\w-]*|margin[\w-]*)\s*:\s*([^;}]+)"
)


def consumption_violations(css: str, html: str, expected: dict[str, str]) -> list[str]:
    """Every way an implementation — token file and markup alike — can fail to
    consume the taxonomy as given."""
    declarations = re.findall(r"(--[\w-]+):\s*([^;]+);", css + "\n" + html)
    problems = []
    for prop, value in expected.items():
        values = [v.strip() for p, v in declarations if p == prop]
        if not values:
            problems.append(f"{prop}: not declared; taxonomy resolved {value!r}")
        problems += [
            f"{prop}: declares {v!r}, taxonomy resolved {value!r}" for v in values if v != value
        ]
    problems += [
        f"declares {p}, outside the naming the taxonomy records"
        for p, _ in declarations
        if p.startswith("--ds-")
    ]
    problems += [f"markup holds raw colour {m}" for m in COLOUR_LITERAL.findall(html)]
    for name, value in ROLE_BOUND.findall(html):
        # Zero is a relationship, not a value a taxonomy owns.
        if re.sub(r"var\(--[\w-]+\)|\b0\b", "", value).strip():
            problems.append(f"markup sets {name} to {value.strip()!r} rather than a role")
    if "--ds-" in html:
        problems.append("markup references a property outside the taxonomy's naming")
    return problems


def _fallback_values(skills: Path) -> dict[str, str]:
    text = (skills / "frontend-engineering" / FALLBACK).read_text(encoding="utf-8")
    return _declarations(text)


def test_value_provenance_matches_each_domains_rung(taxonomy: str, direction: str) -> None:
    """AC-0009."""
    rungs = {r["Domain"]: _ticked(r["Rung"]) for r in _authority_rows(taxonomy, "taxonomy")}
    assert rungs["Color"] == "incumbent-system"
    assert rungs["Spacing and rhythm"] == "approved-direction"
    incumbent = re.search(r"\*\*Incumbent source:\*\* (\S+)", taxonomy)
    assert incumbent and (CONFIRMED / incumbent.group(1)).is_file()
    for role, (_, traces) in _role_table(taxonomy, "### Color").items():
        assert incumbent.group(1) in traces, f"colour role {role} does not trace to the incumbent"
    goals = set(re.findall(r"^\d+\. \*\*(.+?)\*\*", direction, re.M))
    decided = {
        row["Axis"]
        for row in _table_after(direction, "## Direction sheet", where="fixture direction")
        if not row["This direction commits to"].startswith("`[platform-default]`")
    }
    for role, (_, traces) in _role_table(taxonomy, "### Spacing and rhythm").items():
        assert traces in goals | decided, f"spacing role {role} traces to {traces!r}"


def test_incumbent_traced_values_are_the_incumbents(taxonomy: str) -> None:
    """AC-0010."""
    brand = _declarations((CONFIRMED / "src" / "styles" / "brand.css").read_text(encoding="utf-8"))
    for role, (value, traces) in _role_table(taxonomy, "### Color").items():
        prop = re.search(r"`(--[\w-]+)`", traces)
        assert prop, f"{role}: names no incumbent property"
        assert brand.get(prop.group(1)) == value, (role, prop.group(1), brand.get(prop.group(1)))


def _luminance(hex_value: str) -> float:
    channels = [int(hex_value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _pairings(taxonomy: str) -> list[dict[str, str]]:
    return _table_after(
        _section(taxonomy, "## Accessibility"),
        "| Foreground |",
        where="fixture Accessibility pairings",
    )


def test_every_pairing_clears_its_installed_contrast_floor(skills: Path, taxonomy: str) -> None:
    """AC-0011."""
    skill = (skills / "frontend-engineering" / "SKILL.md").read_text(encoding="utf-8")
    floor = {
        row["Element"]: float(row["Minimum ratio"].split(":")[0])
        for row in _table_after(skill, "#### WCAG contrast floor", where="frontend SKILL.md")
    }
    colours = {role: value for role, (value, _) in _role_table(taxonomy, "### Color").items()}
    pairings = _pairings(taxonomy)
    assert pairings, "the fixture checks no pairing"
    for row in pairings:
        fg, bg, element = (
            _ticked(row["Foreground"]),
            _ticked(row["Background"]),
            row["Element class"],
        )
        assert element in floor, f"{element!r} is not an installed contrast-floor class"
        ratio = _contrast(colours[fg], colours[bg])
        assert ratio >= floor[element], f"{fg} on {bg}: {ratio:.2f} < {floor[element]}"


def test_every_authority_rung_is_an_installed_design_system_rung(
    skills: Path, taxonomy: str
) -> None:
    """AC-0012."""
    skill = (skills / "design-system" / "SKILL.md").read_text(encoding="utf-8")
    installed = {
        _ticked(row["Rung"])
        for row in _table_after(skill, "| Rung | Source | Binds |", where="design-system SKILL.md")
    }
    named = {_ticked(r["Rung"]) for r in _authority_rows(taxonomy, "taxonomy")}
    assert named <= installed, named - installed


def test_the_implementation_consumes_the_taxonomy_as_given(skills: Path, taxonomy: str) -> None:
    """AC-0013, including the two fallback substitutions that must fail it."""
    css = (CONFIRMED / "implementation" / "tokens.css").read_text(encoding="utf-8")
    html = (CONFIRMED / "implementation" / "index.html").read_text(encoding="utf-8")
    expected = _expected_declarations(taxonomy)
    assert consumption_violations(css, html, expected) == []

    fallback = _fallback_values(skills)
    for prop, fallback_prop in (
        ("--color-accent-action", "--ds-color-primary"),
        ("--space-3", "--ds-space-3"),
    ):
        assert fallback[fallback_prop] != expected[prop], "the fixture shares a fallback value"
        swapped = re.sub(
            rf"({re.escape(prop)}:\s*)[^;]+;", rf"\g<1>{fallback[fallback_prop]};", css
        )
        assert swapped != css
        assert consumption_violations(swapped, html, expected), f"{prop} swap went undetected"

        # The markup is half the implementation: a redeclaration there, or a
        # literal in place of the role, fails the same check.
        redeclared = html.replace(
            "<style>", f"<style>\n    :root {{ {prop}: {fallback[fallback_prop]}; }}", 1
        )
        assert consumption_violations(css, redeclared, expected), f"{prop} redeclaration missed"
        bypassed = html.replace(f"var({prop})", fallback[fallback_prop])
        assert bypassed != html
        assert consumption_violations(css, bypassed, expected), f"{prop} literal use missed"


def test_an_accessibility_adaptation_is_recorded_and_checked(taxonomy: str) -> None:
    """AC-0023."""
    adaptations = _table_after(
        _section(taxonomy, "## Accessibility"),
        "| Role | Incumbent value |",
        where="fixture adaptations",
    )
    assert adaptations, "no adaptation recorded"
    paired = {_ticked(r[k]) for r in _pairings(taxonomy) for k in ("Foreground", "Background")}
    for row in adaptations:
        before, after = HEX.findall(row["Incumbent value"]), HEX.findall(row["Resolved value"])
        assert before and after and before != after, row
        assert _ticked(row["Role"]) in paired, f"{row['Role']} is adapted but no pairing checks it"


# ── render, observe, correct, then gates (AC-0014 – AC-0017, AC-0024) ────────


@dataclass(frozen=True)
class LoopRules:
    gates: tuple[str, ...]
    chromium_gates: frozenset[str]
    correction_passes: int
    verification_renders: int
    divergence_classes: frozenset[str]
    states: frozenset[str]
    unconditional_states: frozenset[str]
    result_states: frozenset[str]

    @classmethod
    def load(cls, skills: Path) -> LoopRules:
        fe = skills / "frontend-engineering"
        skill = (fe / "SKILL.md").read_text(encoding="utf-8")
        vo = (fe / "references" / "visual-observation.md").read_text(encoding="utf-8")
        inspection = (fe / "references" / "rendered-page-inspection.md").read_text(
            encoding="utf-8"
        )
        assert "## GATES phase" in skill, "frontend SKILL.md: no GATES phase"
        gates_text = skill.split("## GATES phase", 1)[1].split("\n## ", 1)[0]
        headings = re.findall(r"^### \d+\. (.+)$", gates_text, re.M)
        bound = _rule_table(vo, "## Loop bound", where="visual-observation.md")
        states = _rule_table(vo, "## Representative states", where="visual-observation.md")
        return cls(
            gates=tuple(h.split(" (", 1)[0] for h in headings),
            chromium_gates=frozenset(
                h.split(" (", 1)[0] for h in headings if "requires Chromium" in h
            ),
            correction_passes=int(bound["correction-passes"]),
            verification_renders=int(bound["verification-renders-after-correction"]),
            divergence_classes=frozenset(
                row["Class"]
                for row in _table_after(vo, "## Divergence classes", where="visual-observation.md")
            ),
            states=frozenset(k for k, v in states.items() if v.startswith("required")),
            unconditional_states=frozenset(k for k, v in states.items() if v == "required"),
            result_states=frozenset(
                row["Result state"]
                for row in _table_after(
                    inspection, "## Result states", where="rendered-page-inspection.md"
                )
            ),
        )


@pytest.fixture(scope="module")
def loop(skills: Path) -> LoopRules:
    return LoopRules.load(skills)


def _record(name: str) -> dict:
    return json.loads((FIXTURES / name / "run-record.json").read_text(encoding="utf-8"))


def _gate_violations(record: dict, loop: LoopRules) -> list[str]:
    events = record["events"]
    gates = [e for e in events if e["step"] == "gate"]
    problems = []
    if tuple(g["name"] for g in gates) != loop.gates:
        problems.append(f"gate events {[g['name'] for g in gates]} are not {list(loop.gates)}")
    problems += [
        f"gate {g['name']} records no ran" for g in gates if not isinstance(g.get("ran"), bool)
    ]
    return problems


def run_violations(record: dict, loop: LoopRules, declared_states: list[str]) -> list[str]:
    """Every way a rendered run can break the installed loop rules."""
    events = record["events"]
    steps = [e["step"] for e in events]
    problems = _gate_violations(record, loop)
    first_gate = steps.index("gate") if "gate" in steps else len(steps)
    loop_steps = {"render", "observe", "correct", "residual"}
    if any(s in loop_steps for s in steps[first_gate:]):
        problems.append("a render, observe or correct event follows a gate")

    renders = [e for e in events if e["step"] == "render"]
    for r in renders:
        if r.get("state") not in loop.states:
            problems.append(f"render state {r.get('state')!r} is not an installed state")
    rendered = {r.get("state") for r in renders}
    for state in loop.unconditional_states | set(declared_states):
        if state not in rendered:
            problems.append(f"no {state} render")

    corrections = [i for i, s in enumerate(steps) if s == "correct"]
    if len(corrections) > loop.correction_passes:
        problems.append(f"{len(corrections)} corrections; the bound is {loop.correction_passes}")
    if corrections:
        start = corrections[-1] + 1
        end = next((j for j in range(start, len(steps)) if steps[j] == "gate"), len(steps))
        after = steps[start:end].count("render")
        if after != loop.verification_renders:
            problems.append(
                f"{after} renders after the correction; the bound is {loop.verification_renders}"
            )
    for i in corrections:
        observed = [e for e in events[:i] if e["step"] == "observe"]
        gaps = {g["class"] for g in (observed[-1]["material_gaps"] if observed else [])}
        if not gaps or not gaps <= loop.divergence_classes:
            problems.append("a correction cites no installed material-gap class")
        if not set(events[i].get("addresses", [])) <= gaps:
            problems.append("a correction addresses a gap nobody observed")
    for i, e in enumerate(events):
        if e["step"] == "observe" and not any(
            p["step"] == "render" and p.get("capture") for p in events[:i]
        ):
            problems.append("an observation precedes every captured render")
        if e["step"] == "residual":
            if any(s == "correct" for s in steps[i:]):
                problems.append("a residual divergence was corrected")
            if not {d["class"] for d in e["divergences"]} <= loop.divergence_classes:
                problems.append("a residual cites an unknown divergence class")
    return problems


def no_browser_violations(record: dict, loop: LoopRules) -> list[str]:
    problems = _gate_violations(record, loop)
    steps = [e["step"] for e in record["events"]]
    if {"observe", "correct"} & set(steps):
        problems.append("a run with no browser observed or corrected")
    for gate in (e for e in record["events"] if e["step"] == "gate"):
        if gate["name"] in loop.chromium_gates:
            if gate.get("ran") is not False:
                problems.append(f"{gate['name']} claims to have run without Chromium")
            if not str(gate.get("reason", "")).strip():
                problems.append(f"{gate['name']} records no reason")
    inspection = next((e for e in record["events"] if e.get("name") == loop.gates[-1]), {})
    if inspection.get("result_state") != "skipped-no-browser":
        problems.append("the rendered-page inspection does not carry skipped-no-browser")
    if not any("Chromium" in item for item in record["manifest"]["unverified_items"]):
        problems.append("the manifest does not name the missing capability")
    return problems


def _declared_states() -> list[str]:
    facts = tomllib.loads((CONFIRMED / "scenario.toml").read_text(encoding="utf-8"))
    return facts.get("conditional_states", [])


def test_the_loop_precedes_the_gates(skills: Path, loop: LoopRules) -> None:
    """AC-0014."""
    skill = (skills / "frontend-engineering" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.index("### Render and observe before the gates") < skill.index("## GATES phase")
    record = _record("confirmed")
    assert _gate_violations(record, loop) == []
    steps = [e["step"] for e in record["events"]]
    last_loop = max(i for i, s in enumerate(steps) if s in {"render", "observe", "correct"})
    assert last_loop < steps.index("gate")


def test_the_confirmed_run_stays_inside_the_loop_bound(loop: LoopRules) -> None:
    """AC-0015."""
    record = _record("confirmed")
    assert run_violations(record, loop, _declared_states()) == []
    steps = [e["step"] for e in record["events"]]
    assert steps.count("correct") == 1 and "residual" in steps


def _relabelled(record: dict, state: str, as_state: str) -> dict:
    out = copy.deepcopy(record)
    for event in out["events"]:
        if event.get("state") == state:
            event["state"] = as_state
    return out


def test_the_run_check_rejects_each_broken_record(loop: LoopRules) -> None:
    """AC-0016: five negative records derived from the confirmed one."""
    good = _record("confirmed")
    declared = _declared_states()
    assert declared, "the confirmed scenario declares no conditional state"

    gate_first = copy.deepcopy(good)
    gate_first["events"].insert(
        0,
        gate_first["events"].pop(
            next(i for i, e in enumerate(gate_first["events"]) if e["step"] == "gate")
        ),
    )

    second_correction = copy.deepcopy(good)
    at = next(i for i, e in enumerate(second_correction["events"]) if e["step"] == "residual")
    second_correction["events"][at:at] = [
        {"step": "observe", "material_gaps": [{"class": "alignment", "note": "x"}]},
        {"step": "correct", "addresses": ["alignment"]},
        {"step": "render", "state": "primary-state", "capture": "again.png"},
    ]

    uncaptured = copy.deepcopy(good)
    first_observe = next(i for i, e in enumerate(uncaptured["events"]) if e["step"] == "observe")
    for event in uncaptured["events"][:first_observe]:
        event.pop("capture", None)

    # Relabel rather than delete, so the render count — and every other rule —
    # still holds and only state coverage can fail.
    no_primary = _relabelled(good, "primary-state", declared[0])
    no_conditional = _relabelled(good, declared[0], "primary-state")

    # Each negative breaks exactly one rule, so each rule has a test that reds
    # when that rule alone is removed.
    for broken, only in (
        (gate_first, "a render, observe or correct event follows a gate"),
        (second_correction, f"2 corrections; the bound is {loop.correction_passes}"),
        (uncaptured, "an observation precedes every captured render"),
        (no_primary, "no primary-state render"),
        (no_conditional, f"no {declared[0]} render"),
    ):
        assert run_violations(broken, loop, declared) == [only]


def test_the_no_browser_run_claims_nothing_it_could_not_do(loop: LoopRules) -> None:
    """AC-0017, with the two negatives derived from the no-browser record."""
    record = _record("no-browser")
    assert "skipped-no-browser" in loop.result_states
    assert loop.chromium_gates, "no installed gate says it requires Chromium"
    assert no_browser_violations(record, loop) == []
    for gate in loop.chromium_gates:
        for mutate in (lambda e: e.update(ran=True), lambda e: e.update(reason="")):
            broken = copy.deepcopy(record)
            mutate(next(e for e in broken["events"] if e.get("name") == gate))
            assert no_browser_violations(broken, loop), f"{gate} mutation was accepted"


def test_every_required_state_is_rendered(loop: LoopRules) -> None:
    """AC-0024."""
    declared = _declared_states()
    assert declared and set(declared) <= loop.states - loop.unconditional_states, declared
    rendered = {e["state"] for e in _record("confirmed")["events"] if e["step"] == "render"}
    assert rendered <= loop.states
    assert loop.unconditional_states | set(declared) <= rendered


# ── golden eval cases, as installed (AC-0018 – AC-0020) ──────────────────────

GOLDEN_CASES = {
    "visual-golden-path-confirmed-values": "confirmed",
    "visual-golden-path-unconfirmed-target": "unconfirmed",
    "visual-golden-path-refusal-preserved": None,
}
# `--ds-*` is the pack's system-token namespace, so a correct build may use it;
# what marks a fallback substitution is the fallback's own values. These three
# are distinctive enough that a correct answer has no reason to emit them.
FALLBACK_SIGNATURE = ("--ds-color-primary", "--ds-color-surface-alt", "--ds-color-on-surface")


def _fallback_excludes(skills: Path) -> set[str]:
    values = _fallback_values(skills)
    return {
        form
        for prop in FALLBACK_SIGNATURE
        for form in (values[prop].lower(), values[prop].upper())
    }


@pytest.fixture(scope="module")
def eval_cases(skills: Path) -> dict[str, dict]:
    path = skills / "frontend-engineering" / "evals" / "evals.json"
    return {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["evals"]}


def test_golden_cases_grade_both_sides(skills: Path, eval_cases: dict[str, dict]) -> None:
    """AC-0018."""
    needed = _fallback_excludes(skills)
    for case_id in GOLDEN_CASES:
        case = eval_cases.get(case_id)
        assert case is not None, f"{case_id} is not installed"
        assert "files" not in case, f"{case_id} needs a seeded file"
        expect = case.get("expect", {})
        assert expect.get("output_contains"), f"{case_id} has no positive criterion"
        missing = needed - set(expect.get("output_excludes", []))
        assert not missing, f"{case_id} does not exclude {sorted(missing)}"
        assertions = case.get("assertions", [])
        assert any(a.startswith("Does not") for a in assertions), case_id
        assert any(not a.startswith("Does not") for a in assertions), case_id


def test_golden_cases_expect_their_own_scenarios_values(eval_cases: dict[str, dict]) -> None:
    """AC-0019."""
    for case_id, scenario in GOLDEN_CASES.items():
        if scenario is None:
            continue
        text = (FIXTURES / scenario / "design" / "tokens" / "checkout.md").read_text(
            encoding="utf-8"
        )
        colours = _role_table(text, "### Color")
        contains = eval_cases[case_id]["expect"]["output_contains"]
        for role in ("accent.action", "surface.default"):
            assert colours[role][0] in contains, (
                f"{case_id}: {role} {colours[role][0]} not expected"
            )


def test_existing_gap_and_standalone_cases_carry_deterministic_criteria(
    skills: Path, eval_cases: dict[str, dict]
) -> None:
    """AC-0020."""
    for case_id in (
        "visual-authority-upstream-gap-missing-taxonomy",
        "visual-authority-unresolved-domain",
    ):
        excludes = eval_cases[case_id].get("expect", {}).get("output_excludes", [])
        assert _fallback_excludes(skills) <= set(excludes), case_id
    standalone = eval_cases["visual-authority-standalone"].get("expect", {})
    assert "local-premise" in standalone.get("output_contains", [])


# ── a taxonomy-silent domain (silent-domain-gap AC-0005, AC-0006, AC-0011) ───


def test_a_silent_needed_domain_is_held(rules: Rules) -> None:
    """AC-0005: Typography is listed in the Authority table but given no
    values, and nothing records it unresolved."""
    route = walk(rules, "silent-domain")
    assert route.domains["Typography"] == "domain-completion-required"
    facts = tomllib.loads(
        (FIXTURES / "silent-domain" / "scenario.toml").read_text(encoding="utf-8")
    )
    for domain in facts["needed_domains"]:
        if domain != "Typography":
            assert route.domains[domain] == "taxonomy", (domain, route.domains[domain])
    assert FALLBACK not in route.loaded
    assert route.gap_records == [
        {"axes held": ["Typography"], "operation kind": "domain-completion-required"}
    ]


def test_an_unneeded_silent_domain_is_not_held(rules: Rules) -> None:
    """AC-0011: Graphic language has no values and is not needed."""
    facts = tomllib.loads(
        (FIXTURES / "silent-domain" / "scenario.toml").read_text(encoding="utf-8")
    )
    taxonomy = (FIXTURES / "silent-domain" / "design" / "tokens" / "checkout.md").read_text(
        encoding="utf-8"
    )
    assert "Graphic language" not in facts["needed_domains"]
    assert "\n### Graphic language\n" not in taxonomy
    held = {d for d, v in walk(rules, "silent-domain").domains.items() if v != "taxonomy"}
    assert "Graphic language" not in held


def test_every_resolving_fixture_declares_its_needs_and_holds_none_silent(
    rules: Rules, tmp_path: Path
) -> None:
    """AC-0006, with the mutation that proves the check can red."""
    for scenario in ("confirmed", "unconfirmed", "unresolved-domain"):
        facts = tomllib.loads((FIXTURES / scenario / "scenario.toml").read_text(encoding="utf-8"))
        assert facts.get("needed_domains"), f"{scenario} declares no needed_domains"
    refusal = tomllib.loads((FIXTURES / "refusal" / "scenario.toml").read_text(encoding="utf-8"))
    assert refusal.get("needed_domains"), "refusal declares no needed_domains"
    for scenario in ("confirmed", "unconfirmed"):
        assert not walk(rules, scenario).gap_records, scenario

    tree = tmp_path / "confirmed"
    shutil.copytree(FIXTURES / "confirmed", tree)
    taxonomy = tree / "design" / "tokens" / "checkout.md"
    text = taxonomy.read_text(encoding="utf-8")
    stripped = re.sub(r"### Typography\n.*?(?=### Color)", "", text, flags=re.S)
    assert stripped != text
    taxonomy.write_text(stripped, encoding="utf-8")
    assert (
        walk(rules, "confirmed", tree=tree).domains["Typography"] == "domain-completion-required"
    )


def test_the_silent_domain_eval_grades_the_hold(skills: Path, eval_cases: dict[str, dict]) -> None:
    """silent-domain-gap AC-0007."""
    case = eval_cases.get("visual-authority-silent-domain")
    assert case is not None, "visual-authority-silent-domain is not installed"
    assert "no typography values" in case["prompt"]
    assert "custom-property block you bound" in case["prompt"]
    assertions = case["assertions"]
    assert any(a.startswith("Does not") and "silent typography domain" in a for a in assertions)
    assert any(not a.startswith("Does not") and "upstream gap" in a for a in assertions)
    expect = case["expect"]
    assert "domain-completion-required" in expect["output_contains"]
    assert "#2f5d50" in expect["output_contains"] and "#2f5d50" in case["prompt"]
    assert _fallback_excludes(skills) <= set(expect["output_excludes"])


def test_golden_prompts_state_type_shape_and_layout_values(eval_cases: dict[str, dict]) -> None:
    """silent-domain-gap AC-0008: each golden prompt states its own fixture's
    Typography role values and its Shape and containment and Spatial structure
    commitments, verbatim."""
    for case_id, scenario in GOLDEN_CASES.items():
        if scenario is None:
            continue
        text = (FIXTURES / scenario / "design" / "tokens" / "checkout.md").read_text(
            encoding="utf-8"
        )
        prompt = eval_cases[case_id]["prompt"]
        for value, _ in _role_table(text, "### Typography").values():
            assert value in prompt, f"{case_id}: typography {value!r} missing"
        for heading in ("### Shape and containment", "### Spatial structure"):
            commitments = [
                ln.split(":**", 1)[1].strip().rstrip(".")
                for ln in _section(text, heading).splitlines()
                if ln.startswith("- **") and not ln.startswith("- **Relationship:**")
            ]
            assert commitments, f"{scenario}: {heading} commits nothing"
            for commitment in commitments:
                assert commitment in prompt, f"{case_id}: {heading} {commitment!r} missing"


def test_the_golden_implementation_sets_the_taxonomy_type_and_shape(taxonomy: str) -> None:
    """The confirmed fixture needs Typography and Shape and containment, so its
    golden implementation sets them: each Typography role's size, weight and
    line height, the control border, and square corners."""
    html = (CONFIRMED / "implementation" / "index.html").read_text(encoding="utf-8")
    fonts = re.findall(r"font:\s*([^;]+);", html)
    for role, (value, _) in _role_table(taxonomy, "### Typography").items():
        size, weight, leading = (part.strip() for part in value.split(",")[1:4])
        assert any(f"{weight} {size}/{leading}" in font for font in fonts), (role, value, fonts)
    control = re.search(r"\binput \{([^}]*)\}", html)
    assert control, "the golden implementation styles no input control"
    assert "border: 1px solid var(--color-text-muted)" in control.group(1)
    assert re.search(r"border-radius:\s*0\s*(;|$)", control.group(1).strip()), control.group(1)
