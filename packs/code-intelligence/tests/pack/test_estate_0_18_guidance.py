"""Guidance quality gates: pin-version and retired-claim scanners.

Tests cover:

- AC-0004 / AC-0005: pin scanner over the shipped surface and its planted samples.
  See the §Floor and pin criteria in the spec for the policy.
- AC-0027 / AC-0028: retired-claim scanner over the shipped surface and its planted
  samples. Patterns map to gaps.md §Paths, §Completeness, §Impact, §Provenance and
  evidence, and §Capability discovery.
- AC-0030 / AC-0031: route teaching in SKILL.md and references/.
- AC-0035: eval case for route-and-depth questions.
- AC-0038: main() exits non-zero on a missing path and on an empty directory.

Run the guide checks as one-liners from the repository root:

    python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance',\
'packs/code-intelligence/tests/pack/test_estate_0_18_guidance.py'); \
m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'],\
scanner='pin'))"

    python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance',\
'packs/code-intelligence/tests/pack/test_estate_0_18_guidance.py'); \
m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'],\
scanner='retired'))"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = PACK_ROOT / ".apm"

#: Text files in the pack's exported payload plus the pack manifest and README.
#: These are the three components that `spec.md` calls the "shipped surface".
_SHIPPED_SURFACE: tuple[Path, ...] = (
    RUNTIME_ROOT,
    PACK_ROOT / "README.md",
    PACK_ROOT / "pack.toml",
)

# ── Pin scanner ───────────────────────────────────────────────────────────────

#: Matches any `cargo install wicked-estate` or `cargo install wicked-estate-mcp`
#: occurrence (with possible extra whitespace).
_CARGO_INSTALL_RE: re.Pattern[str] = re.compile(
    r"\bcargo\s+install\s+wicked-estate(?:-mcp)?"
)

#: The exact version every install command must pin. A test ties it to the
#: preflight's `PINNED_VERSION`, so the scanner and the preflight cannot drift.
REQUIRED_PIN = "0.18.0"

#: Each `cargo install` occurrence must continue with exactly this form: the
#: package name, then `--version <REQUIRED_PIN> --locked`.
_CORRECT_PIN_RE: re.Pattern[str] = re.compile(
    r"\bcargo\s+install\s+wicked-estate(?:-mcp)?\s+--version\s+"
    + re.escape(REQUIRED_PIN)
    + r"\s+--locked"
)


def _scan_pin(path: Path) -> list[str]:
    """Return ``'file:line'`` for every line holding an incorrectly pinned install.

    Each ``cargo install wicked-estate(-mcp)?`` occurrence is checked on its own:
    it must be followed immediately by ``--version <REQUIRED_PIN> --locked``. A
    correct pin elsewhere on the same line does not excuse a stale one.
    """
    hits: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if any(
            not _CORRECT_PIN_RE.match(line, m.start())
            for m in _CARGO_INSTALL_RE.finditer(line)
        ):
            hits.append(f"{path}:{i}")
    return hits


# ── Retired-claim scanner ─────────────────────────────────────────────────────

#: Patterns for prose claims that 0.18.0 rendered stale.  Each group targets one
#: conceptual gap from gaps.md that 0.18.0 closed or reworded.  The scanner
#: normalises text before matching: lowercase, strip ``* _ ``` Markdown emphasis,
#: collapse all whitespace (including newlines) to a single space.  That lets it
#: catch a phrase split across a wrapped line or broken by emphasis characters.
#:
#: Groups:
#:   path absent       — gaps.md §Paths closed by wicked-estate path
#:   silent depth      — gaps.md §Completeness: --depth and searched_depth
#:   no CLI depth      — gaps.md §Impact: flat list replaced by --depth 1
#:   no CLI edge       — gaps.md §Provenance and evidence: path hops carry these
#:   stale counts      — gaps.md §Capability discovery: tool count changed
#:   stale version     — bare 0.16 floor or version claim (0.16.7 provenance OK)
_RETIRED_PATTERNS: tuple[re.Pattern[str], ...] = (
    # path absent — gaps.md §Paths
    re.compile(r"\bno path query\b"),
    re.compile(r"\bnothing returns the path between\b"),
    re.compile(r'\bno "how does a reach b" primitive\b'),
    re.compile(r"\breachability, not the route\b"),
    re.compile(r"reachability is answerable; the route is not\b"),
    re.compile(r"reachability yes, the route no\b"),
    re.compile(r"\bpaths (?:\||—) absent\b"),
    # silent depth — gaps.md §Completeness
    re.compile(r"\btwelve[- ]hops?\b"),
    re.compile(r"\bfixed depth of 12\b"),
    re.compile(r"\bhardcod(?:ed|es)\b"),
    re.compile(r"\bdepth cap unreported\b"),
    re.compile(r"\bhorizon is silent\b"),
    re.compile(r"\bsilent (?:depth-12 )?horizon\b"),
    re.compile(r"\bdepth-12 traversal cap\b"),
    re.compile(r"\bthird limit (?:is|and it is) (?:not reported|unreported)\b"),
    re.compile(r"\bfourth limit that is not reported\b"),
    # no CLI depth — gaps.md §Impact
    re.compile(r"\bimpact cannot be separated\b"),
    re.compile(r"\bdepth on a cli blast radius\b"),
    re.compile(r"\bflat list with no depth\b"),
    # no CLI edge evidence — gaps.md §Provenance and evidence
    re.compile(r"\bnot printed on the cli read paths\b"),
    re.compile(r"\bper-edge confidence or provenance on cli read paths\b"),
    re.compile(r"\babsent from (?:the )?cli output\b"),
    # stale counts — gaps.md §Capability discovery
    re.compile(r"\b29 tool"),
    re.compile(r"\bleaving 19\b"),
    re.compile(r"\bfive subcommands\b"),
    # stale version — bare 0.16 floor; 0.16.7 provenance does not match
    re.compile(r"\b0\.16(?!\.\d)"),
)


def _normalize_retired(text: str) -> str:
    """Normalize text for retired-claim matching.

    Lowercase, strip Markdown emphasis characters (``* _ ```), then collapse
    every whitespace run (including newlines) to a single space.  This lets the
    scanner catch a phrase that is split across a wrapped line or interrupted by
    emphasis markup.
    """
    text = text.lower()
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text)


def _scan_retired(path: Path) -> list[str]:
    """Return ``'file:line'`` for each line matching a retired-claim pattern.

    The full file content is normalised first so that cross-line phrases are
    detected.  When a pattern matches the normalised full text, the function
    then searches line by line to recover an approximate line number.  If no
    individual line matches (true cross-line case), line 1 is reported.

    Each unique ``file:line`` pair is reported at most once regardless of how
    many patterns match on the same line.
    """
    raw = path.read_text(encoding="utf-8")
    norm_full = _normalize_retired(raw)
    raw_lines = raw.splitlines()

    hits: list[str] = []
    reported: set[str] = set()

    for pattern in _RETIRED_PATTERNS:
        if not pattern.search(norm_full):
            continue
        # Recover approximate line number by scanning per-normalised-line.
        for i, line in enumerate(raw_lines, start=1):
            if pattern.search(_normalize_retired(line)):
                key = f"{path}:{i}"
                if key not in reported:
                    hits.append(key)
                    reported.add(key)
                break
        else:
            # Cross-line match: attribute to line 1 as a conservative fallback.
            key = f"{path}:1"
            if key not in reported:
                hits.append(key)
                reported.add(key)

    return hits


# ── Planted samples (AC-0005, AC-0028) ───────────────────────────────────────

#: Stale sentences taken from the pre-0.18 pack and guides, at least one per
#: pattern, so a pattern that stops matching is caught.
_RETIRED_STALE_SAMPLE: tuple[str, ...] = (
    # path absent — gaps.md §Paths
    "**There is no path query.** You can establish that A reaches B.",
    "Nothing returns the path between two symbols.",
    'There is no "how does A reach B" primitive on either surface.',
    "that tells you reachability, not the route.",
    "Reachability is answerable; the route is not.",
    "Reachability yes, the route no.",
    "## 6. Paths — **Absent**",
    # silent depth — gaps.md §Completeness
    "Its traversal stops at twelve hops and does not say so.",
    "The CLI traverses to a fixed depth of 12 and does not report whether it reached that limit.",
    "The CLI hardcodes blast-radius traversal to **depth 12**.",
    "| 12 | Completeness | Partial — depth cap unreported |",
    "Dependents beyond 12 hops are counted in neither field — the horizon is silent.",
    "**The CLI blast radius has a silent depth-12 horizon.**",
    "On the CLI side this covers the depth-12 traversal cap.",
    "A third limit is unreported — the CLI stops at a fixed depth.",
    "The twelve-hop traversal cap is a fourth limit that is *not* reported.",
    "**Depth on a CLI blast radius**, so direct and transitive impact cannot be separated.",
    "**Per-edge confidence or provenance on CLI read paths**, although every edge carries them.",
    "| 10 | Provenance / evidence | Partial — in the model, absent from CLI output |",
    "`--readonly` drops the ten write tools, leaving 19.",
    "**But only from five subcommands** — `query`, `blast-radius`, `stats`.",
    # no CLI depth — gaps.md §Impact (joined from two wrapped lines)
    (
        "*Caveat, CLI only:* the result is a flat list with no depth, so direct"
        " and transitive impact cannot be separated from the CLI alone."
    ),
    # no CLI edge evidence — README.md (joined from two wrapped lines)
    (
        "**Per-edge confidence and provenance are not printed on the CLI read"
        " paths**, even though every edge carries them."
    ),
    # stale counts — README.md (joined from two wrapped lines)
    (
        "The MCP server advertises **29 tool schemas**, and they stay resident"
        " in the agent's context for the entire session whether or not a single"
        " one is called."
    ),
    # stale version — README.md
    "4 means the binary is older than the 0.16 floor this pack was verified against.",
)

#: Current 0.18 sentences that must not match the retired-claim scanner.
#: Taken from the §Behavior & rules section of the plan.
_RETIRED_CURRENT_SAMPLE: tuple[str, ...] = (
    "A `found: false` with `depth_bounded: true` means the route is not proven absent.",
    "Measured on Wicked Estate 0.16.7 against a real repository.",
    "`--depth 1` returns the direct dependents.",
    "`path` hops carry confidence and provenance; `blast-radius` rows do not.",
)

#: Stale cargo install lines that must be rejected by the pin scanner.
_PIN_STALE_SAMPLES: tuple[str, ...] = (
    "cargo install wicked-estate --locked",
    "cargo install wicked-estate --version 0.16.7 --locked",
    "cargo install wicked-estate --version 0.18.0 --locked && cargo install wicked-estate-mcp --locked",
)

#: Correct cargo install lines that must be accepted by the pin scanner.
_PIN_CURRENT_SAMPLES: tuple[str, ...] = (
    "cargo install wicked-estate --version 0.18.0 --locked",
    "cargo install wicked-estate-mcp --version 0.18.0 --locked",
)


# ── File collection ───────────────────────────────────────────────────────────


def _collect_text_files(paths: list[str]) -> list[Path] | None:
    """Collect readable text files from the given paths.

    Returns ``None`` when any path does not exist, or an empty list when no
    readable text file is found.  Directories are walked recursively;
    ``__pycache__`` subtrees are skipped.
    """
    collected: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            sys.stderr.write(f"error: path does not exist: {p}\n")
            return None
        if p.is_file():
            collected.append(p)
        else:
            for child in sorted(p.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    collected.append(child)

    text_files: list[Path] = []
    for f in collected:
        try:
            f.read_text(encoding="utf-8")
            text_files.append(f)
        except (UnicodeDecodeError, OSError):
            pass  # skip binary or unreadable files

    return text_files


# ── Public entry point ────────────────────────────────────────────────────────


def main(paths: list[str], scanner: str = "pin") -> int:
    """Scan *paths* with the named scanner and return an exit code.

    Exit codes:

    - ``0`` — no violations found.
    - ``1`` — one or more violations found; each is printed to stdout as
      ``file:line``.
    - ``2`` — a given path does not exist, or the paths hold no file to scan.

    Args:
        paths: Paths to scan.  Each may be a file or a directory; directories
            are walked recursively.
        scanner: ``"pin"`` checks every ``cargo install wicked-estate(-mcp)?``
            occurrence for ``--version 0.18.0 --locked``.  ``"retired"`` checks
            for prose claims that Wicked Estate 0.18.0 rendered stale.
    """
    text_files = _collect_text_files(paths)
    if text_files is None:
        return 2
    if not text_files:
        sys.stderr.write("error: no text files found to scan\n")
        return 2

    if scanner == "pin":
        scan_fn = _scan_pin
    elif scanner == "retired":
        scan_fn = _scan_retired
    else:
        sys.stderr.write(f"error: unknown scanner {scanner!r}\n")
        return 2

    hits: list[str] = []
    for f in text_files:
        hits.extend(scan_fn(f))

    for h in hits:
        print(h)
    return 1 if hits else 0


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_pin_scanner_shipped_surface_is_clean() -> None:
    """AC-0004: every cargo install occurrence in the shipped surface carries the correct 0.18.0 pin.

    Fails until T2 updates pack.toml, scripts/estate_preflight.py, and all prose
    install commands.
    """
    result = main(
        [str(p) for p in _SHIPPED_SURFACE],
        scanner="pin",
    )
    assert result == 0, "pin scanner found incorrect cargo install pins in the shipped surface"


def test_required_pin_equals_preflight_pinned_version() -> None:
    """AC-0004: the pin the scanner requires is the preflight's ``PINNED_VERSION``."""
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(
        "code_intelligence_guidance_estate_preflight",
        RUNTIME_ROOT / "skills" / "code-intelligence" / "scripts" / "estate_preflight.py",
    )
    assert spec and spec.loader
    preflight = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight)
    assert preflight.PINNED_VERSION == REQUIRED_PIN


def test_pin_scanner_planted_samples(tmp_path: Path) -> None:
    """AC-0005: pin scanner rejects stale install lines and accepts the correct 0.18.0 pin."""
    stale_file = tmp_path / "stale_pins.md"
    stale_file.write_text("\n".join(_PIN_STALE_SAMPLES) + "\n", encoding="utf-8")
    assert _scan_pin(stale_file), (
        "pin scanner must reject stale pin samples"
    )

    for sample in _PIN_STALE_SAMPLES:
        single = tmp_path / "single_stale.md"
        single.write_text(sample + "\n", encoding="utf-8")
        assert _scan_pin(single), f"pin scanner must reject: {sample!r}"

    current_file = tmp_path / "current_pins.md"
    current_file.write_text("\n".join(_PIN_CURRENT_SAMPLES) + "\n", encoding="utf-8")
    assert not _scan_pin(current_file), (
        "pin scanner must accept correct 0.18.0 pin samples"
    )

    for sample in _PIN_CURRENT_SAMPLES:
        single = tmp_path / "single_current.md"
        single.write_text(sample + "\n", encoding="utf-8")
        assert not _scan_pin(single), f"pin scanner must accept: {sample!r}"


def test_retired_claim_scanner_shipped_surface_is_clean() -> None:
    """AC-0027: the retired-claim scanner finds no match in the shipped surface.

    Fails until T2 rewrites the prose to remove stale gap claims.  Pattern
    groups: paths absent (gaps.md §Paths), silent depth (gaps.md §Completeness),
    no CLI depth (gaps.md §Impact), no CLI edge evidence (gaps.md §Provenance
    and evidence), stale counts (gaps.md §Capability discovery), stale version.
    """
    result = main(
        [str(p) for p in _SHIPPED_SURFACE],
        scanner="retired",
    )
    assert result == 0, (
        "retired-claim scanner found stale claims in the shipped surface"
    )


def test_retired_claim_planted_samples(tmp_path: Path) -> None:
    """AC-0028: retired-claim scanner matches every stale sentence and no current sentence.

    Stale sentences come from the pre-0.18 pack and guides, at least one per pattern.
    Current sentences must not trigger any pattern; in particular, a 0.16.7
    provenance note must not match the bare-0.16 version pattern.
    """
    # Every stale sentence must produce at least one hit.
    for sentence in _RETIRED_STALE_SAMPLE:
        single = tmp_path / "stale_single.md"
        single.write_text(sentence + "\n", encoding="utf-8")
        assert _scan_retired(single), (
            f"retired scanner must match stale sentence: {sentence!r}"
        )

    # Every pattern is exercised by some stale sentence.
    normalised = [_normalize_retired(s) for s in _RETIRED_STALE_SAMPLE]
    unexercised = [
        p.pattern for p in _RETIRED_PATTERNS if not any(p.search(s) for s in normalised)
    ]
    assert not unexercised, f"patterns with no stale sample sentence: {unexercised}"

    # No current sentence may produce any hit.
    for sentence in _RETIRED_CURRENT_SAMPLE:
        single = tmp_path / "current_single.md"
        single.write_text(sentence + "\n", encoding="utf-8")
        assert not _scan_retired(single), (
            f"retired scanner must NOT match current sentence: {sentence!r}"
        )


def test_route_teaching_wicked_estate_path() -> None:
    """AC-0030: SKILL.md, capability-map.md, and investigation-patterns.md each contain 'wicked-estate path'.

    Fails until T2 adds the path command to the skill and references.  The
    capability gaps.md §Paths is closed by 0.18.0.
    """
    skill_md = RUNTIME_ROOT / "skills" / "code-intelligence" / "SKILL.md"
    capability_map = (
        RUNTIME_ROOT / "skills" / "code-intelligence" / "references" / "capability-map.md"
    )
    investigation = (
        RUNTIME_ROOT
        / "skills"
        / "code-intelligence"
        / "references"
        / "investigation-patterns.md"
    )
    for path in (skill_md, capability_map, investigation):
        assert "wicked-estate path" in path.read_text(encoding="utf-8"), (
            f"{path.name} must contain 'wicked-estate path' (AC-0030)"
        )


def test_blast_radius_depth_flag_taught() -> None:
    """AC-0031: SKILL.md and capability-map.md each have a line containing both 'blast-radius' and '--depth'.

    Fails until T2 documents the --depth flag.  The silent-depth gap from
    gaps.md §Completeness is resolved by the new searched_depth and
    depth_horizon_reached fields.
    """
    skill_md = RUNTIME_ROOT / "skills" / "code-intelligence" / "SKILL.md"
    capability_map = (
        RUNTIME_ROOT / "skills" / "code-intelligence" / "references" / "capability-map.md"
    )
    for path in (skill_md, capability_map):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert any("blast-radius" in line and "--depth" in line for line in lines), (
            f"{path.name} must have a line containing both 'blast-radius' and '--depth' (AC-0031)"
        )


def test_eval_case_covers_route_question() -> None:
    """AC-0035: evals.json contains a case whose prompt mentions 'reach' and whose assertions name both 'wicked-estate path' and 'depth_bounded'.

    Fails until T3 adds the route-and-depth eval case.
    """
    evals_path = (
        RUNTIME_ROOT / "skills" / "code-intelligence" / "evals" / "evals.json"
    )
    evals_data = json.loads(evals_path.read_text(encoding="utf-8"))
    cases = evals_data.get("evals", evals_data if isinstance(evals_data, list) else [])

    route_cases = [c for c in cases if "reach" in c.get("prompt", "")]
    assert route_cases, "evals.json must contain at least one case with 'reach' in the prompt"

    def _assertions_text(case: dict) -> str:
        assertions = case.get("assertions", [])
        if isinstance(assertions, list):
            return " ".join(str(a) for a in assertions)
        return str(assertions)

    matching = [
        c for c in route_cases
        if "wicked-estate path" in _assertions_text(c)
        and "depth_bounded" in _assertions_text(c)
    ]
    assert matching, (
        "At least one 'reach' eval case must assert both 'wicked-estate path' and 'depth_bounded'"
    )


def test_main_rejects_missing_path(tmp_path: Path) -> None:
    """AC-0038: main() exits non-zero when a given path does not exist."""
    missing = tmp_path / "does_not_exist"
    result = main([str(missing)], scanner="pin")
    assert result != 0, "main() must exit non-zero for a non-existent path"


def test_main_rejects_empty_directory(tmp_path: Path) -> None:
    """AC-0038: main() exits non-zero when the given paths hold no file to scan."""
    empty = tmp_path / "empty_dir"
    empty.mkdir()
    result = main([str(empty)], scanner="pin")
    assert result != 0, "main() must exit non-zero when no files are found"
