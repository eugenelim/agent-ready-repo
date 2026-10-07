"""Goal-based documentation checks for the composition example.

Verifies that composition-example.md carries the required sections, labels,
links, and evidence limits, and that SKILL.md and README.md route to it with
the required nonnormative statements.  All reads stay inside the pack.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

# Resolved at import time; tests use these constants directly.
PACK_ROOT: Path = Path(__file__).resolve().parents[2]
SKILL_DIR: Path = PACK_ROOT / ".apm" / "skills" / "code-intelligence"
REFERENCES_DIR: Path = SKILL_DIR / "references"
EXAMPLE_PATH: Path = REFERENCES_DIR / "composition-example.md"
SKILL_MD: Path = SKILL_DIR / "SKILL.md"
README_MD: Path = PACK_ROOT / "README.md"

# Exact names the plan and spec require.
PROVIDER_FIT_HEADING: str = "## Provider-fit path"
FALLBACK_HEADING: str = "## Fallback path"
WHO_OWNS_HEADING: str = "## Who owns what"

# The acceptance question sentence must be identical in both paths.
ACCEPTANCE_QUESTION: str = (
    "Is every call site that must change identified, "
    "with the ones that could not be established named?"
)

# Links the example must carry (relative to the references/ directory).
REQUIRED_LINKS: tuple[str, ...] = (
    "capability-map.md",
    "evidence.md",
    "gaps.md",
    "investigation-patterns.md",
    "../scripts/estate_preflight.py",
)

# CLI verbs that are real Wicked Estate commands (from test_estate_surface_vocabulary).
# Used to detect if the Core-owned section accidentally names a provider command.
_ESTATE_CLI_VERBS: frozenset[str] = frozenset(
    {
        "annotate", "annotations", "blast-radius", "by-requirement",
        "changed-since", "clusters", "compact", "context", "correspond",
        "cross-graph", "dead-code", "drift", "entrypoints", "export",
        "fingerprint", "graph-view", "hotspots", "import-telemetry", "index",
        "leaves", "nodes", "path", "plugins", "query", "rank", "resolve",
        "scip", "semantic", "semantics", "source", "stale-annotations",
        "stats", "subscribe", "tfstate", "watch",
    }
)

# Wicked Estate output field names in backtick notation that must not appear
# in the Core-owned section.
_WE_FIELD_NAMES: tuple[str, ...] = (
    "`unresolved`",
    "`truncated_dependents`",
    "`depth_horizon_reached`",
    "`node_cap_reached`",
    "`searched_depth`",
    "`symbol_id`",
    "`dependents`",
)

# MCP estate tool names (CamelCase) that must not appear in the Core-owned section.
_MCP_ESTATE_TOOLS: frozenset[str] = frozenset(
    {
        "BlastRadius", "TraverseGraph", "SearchEntity", "RetrieveEntity",
        "FetchContent", "ContextBundle", "RulesInventory", "RankHotspots",
        "Communities", "Lineage", "Path", "SemanticSearch",
    }
)

# Words that, if found in a sentence about investigation patterns in an
# asserting context, indicate a forbidden claim.
_PATTERN_CLAIM_WORDS: tuple[str, ...] = (
    "complete",
    "exhaustive",
    "required",
    "closed",
)

_NEGATE_WORDS: tuple[str, ...] = (
    "not", "never", "may", "need not", "cannot", "no longer",
)


def _read(path: Path) -> str:
    """Read a file and return its text, raising AssertionError if it does not exist."""
    assert path.exists(), f"expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def _section_after(text: str, heading: str) -> str:
    """Return the text that follows *heading* up to the next same-level heading."""
    pos = text.find(heading)
    assert pos >= 0, f"heading {heading!r} not found in document"
    after = text[pos + len(heading):]
    # Determine the heading level from its leading '#' characters.
    level = len(heading) - len(heading.lstrip("#"))
    # Find the next heading at the same or higher level.
    next_pos = len(after)
    for m in re.finditer(r"^#{1," + str(level) + r"} ", after, re.MULTILINE):
        if m.start() > 0:
            next_pos = m.start()
            break
    return after[:next_pos]


def _subsection_after(text: str, heading: str) -> str:
    """Return the text following a ### subsection heading within *text*."""
    pos = text.find(heading)
    assert pos >= 0, f"subsection {heading!r} not found"
    after = text[pos + len(heading):]
    m = re.search(r"^###+ ", after, re.MULTILINE)
    if m:
        return after[: m.start()]
    return after


def test_example_walks_the_provider_fit_path() -> None:
    """AC-0001: the Provider-fit path section states the question, cites the capability map,
    shows the preflight command, a bare stats run, the exact blast-radius invocation,
    names unresolved and truncated_dependents as limits, shows a source check, and
    names a stopping point.
    """
    text: str = _read(EXAMPLE_PATH)
    section: str = _section_after(text, PROVIDER_FIT_HEADING)

    assert "parse_config" in section, "section must state the repository question"
    assert (
        "capability-map.md#graph-relationships" in section
        or "Blast radius / who depends on this" in section
    ), (
        "section must link to capability-map.md#graph-relationships or name the "
        "'Blast radius / who depends on this' capability-map entry"
    )
    assert "wicked-estate resolve" in section, (
        "section must show the resolve step before querying direct dependents"
    )
    assert "python scripts/estate_preflight.py --check" in section, (
        "section must show the preflight command"
    )
    assert "wicked-estate stats" in section, (
        "section must show a bare wicked-estate stats run for freshness"
    )
    assert "wicked-estate blast-radius parse_config --depth 1 --json" in section, (
        "section must show the exact blast-radius invocation"
    )
    assert "unresolved" in section, (
        "section must name unresolved as a limit the answer keeps"
    )
    assert "truncated_dependents" in section, (
        "section must name truncated_dependents as a limit the answer keeps"
    )
    assert "source" in section.lower(), (
        "section must describe a source check of the load-bearing call sites"
    )
    assert "stop" in section.lower(), (
        "section must name a stopping point"
    )
    assert ACCEPTANCE_QUESTION in section, (
        "section must include the acceptance question"
    )


def test_example_walks_the_fallback_paths() -> None:
    """AC-0002: the Fallback path section covers exits 2, 3, and 4, the STALENESS scenario
    with repository history, labels text search as a different evidence class, does not
    use the word 'equivalent', names what cannot be established, and reaches the same
    acceptance question without an install, index, or refresh step.
    """
    text: str = _read(EXAMPLE_PATH)
    section: str = _section_after(text, FALLBACK_HEADING)

    assert "exits 2" in section or "exit 2" in section.lower() or "(preflight exits 2)" in section, (
        "section must cover preflight exit 2 (binary absent)"
    )
    assert "exits 3" in section or "exit 3" in section.lower() or "(preflight exits 3)" in section, (
        "section must cover preflight exit 3 (no index)"
    )
    assert "exits 4" in section or "exit 4" in section.lower() or "(preflight exits 4)" in section, (
        "section must cover preflight exit 4 (version below floor)"
    )
    assert "STALENESS:" in section, (
        "section must show the STALENESS: line scenario"
    )
    assert "git log" in section, (
        "section must pair the STALENESS scenario with repository history"
    )
    assert "different evidence class" in section, (
        "section must label text search and source reading as a different evidence class"
    )
    assert "equivalent" not in section.lower(), (
        "section must not use the word 'equivalent' to describe text search"
    )
    assert "cannot establish" in section or "cannot" in section, (
        "section must name what text search cannot establish"
    )
    assert ACCEPTANCE_QUESTION in section, (
        "section must reach the same acceptance question as the provider-fit path"
    )
    section_lower: str = section.lower()
    assert "wicked-estate index" not in section_lower, (
        "section must not include an index step"
    )
    assert "re-index" not in section_lower or "do not re-index" in section_lower, (
        "section must not instruct a re-index without a negation"
    )
    assert "cargo install" not in section_lower, (
        "section must not include an install step"
    )


def test_example_labels_every_owner() -> None:
    """AC-0003: the Who owns what section carries Core-owned and pack-owned labels with
    the required items under each.
    """
    text: str = _read(EXAMPLE_PATH)
    who_section: str = _section_after(text, WHO_OWNS_HEADING)

    # Locate the subsections by their ### labels.
    assert "core-owned" in who_section.lower(), (
        "Who owns what must carry a Core-owned subsection"
    )
    assert "pack-owned" in who_section.lower(), (
        "Who owns what must carry a pack-owned subsection"
    )

    core_text: str = _subsection_after(who_section, "### Core-owned")

    # Required items under Core-owned.
    assert "question" in core_text.lower() and "stopping" in core_text.lower(), (
        "Core-owned must include the question and stopping condition"
    )
    assert "fallback" in core_text.lower(), (
        "Core-owned must include fallback"
    )
    assert "attribution" in core_text.lower(), (
        "Core-owned must include attribution"
    )
    assert "authority" in core_text.lower(), (
        "Core-owned must include authority"
    )
    assert "locator" in core_text.lower() or "--locator-b64" in core_text, (
        "Core-owned authority must mention the inquiry owner's locator reader"
    )
    assert "provider output is data" in core_text.lower() or (
        "provider" in core_text.lower() and "data" in core_text.lower()
    ), (
        "Core-owned authority must state that provider output is data"
    )
    assert "verification" in core_text.lower(), (
        "Core-owned must include verification"
    )

    pack_text: str = _subsection_after(who_section, "### Pack-owned")

    # Required items under pack-owned.
    assert "prerequisite" in pack_text.lower(), (
        "Pack-owned must include prerequisites"
    )
    assert "command" in pack_text.lower(), (
        "Pack-owned must include commands"
    )
    assert "capability" in pack_text.lower() and "map" in pack_text.lower(), (
        "Pack-owned must include capability mapping"
    )
    assert "evidence" in pack_text.lower() and "field" in pack_text.lower(), (
        "Pack-owned must include evidence fields"
    )
    assert "gap" in pack_text.lower(), (
        "Pack-owned must include gaps"
    )
    assert "investigation pattern" in pack_text.lower() or "patterns" in pack_text.lower(), (
        "Pack-owned must include investigation patterns"
    )


def test_core_owned_rules_name_no_provider_detail() -> None:
    """AC-0006: the Core-owned list carries no wicked-estate command, Wicked Estate output
    field, MCP tool name, or graph term from the capability map.
    """
    text: str = _read(EXAMPLE_PATH)
    who_section: str = _section_after(text, WHO_OWNS_HEADING)
    core_text: str = _subsection_after(who_section, "### Core-owned")

    # No wicked-estate CLI command invocations in the Core-owned section.
    cli_invocation = re.compile(r"\bwicked-estate\s+(?!--)([a-z][a-z-]*)")
    found_commands = cli_invocation.findall(core_text)
    unknown_commands = [v for v in found_commands if v in _ESTATE_CLI_VERBS]
    assert not unknown_commands, (
        f"Core-owned section must not name wicked-estate CLI commands: {unknown_commands}"
    )

    # No backtick-quoted WE output field names.
    for field in _WE_FIELD_NAMES:
        assert field not in core_text, (
            f"Core-owned section must not contain WE output field {field!r}"
        )

    # No MCP estate tool names.
    for tool in _MCP_ESTATE_TOOLS:
        # Avoid matching substrings: check for word boundary or backtick context.
        pattern = re.compile(r"(?<![A-Za-z])" + re.escape(tool) + r"(?![A-Za-z])")
        assert not pattern.search(core_text), (
            f"Core-owned section must not name MCP tool {tool!r}"
        )

    # No graph-specific WE terms (CLI command names used as concepts).
    graph_terms = ("blast-radius", "stats", "blast_radius")
    for term in graph_terms:
        assert term not in core_text, (
            f"Core-owned section must not use WE graph term {term!r}"
        )


def test_example_links_canonical_references() -> None:
    """AC-0004: the example links to capability-map.md, evidence.md, gaps.md,
    investigation-patterns.md, and ../scripts/estate_preflight.py, and every
    relative link resolves inside the skill directory.
    """
    text: str = _read(EXAMPLE_PATH)

    targets = {
        m.group(1).split("#", 1)[0]
        for m in re.finditer(r"\]\(([^)\s]+)\)", text)
        if not re.match(r"[a-z]+:|#", m.group(1))
    }
    for required in REQUIRED_LINKS:
        assert required in targets, (
            f"composition-example.md must link to {required!r}"
        )

    # Match link text against the skill's own file list instead of building a
    # path from it, so the check cannot reach outside the pack.
    skill_files = {
        p.relative_to(SKILL_DIR).as_posix() for p in SKILL_DIR.rglob("*") if p.is_file()
    }
    for target in sorted(targets):
        relative = posixpath.normpath(posixpath.join("references", target))
        assert relative in skill_files, (
            f"link target {target!r} does not resolve to a file inside the skill directory"
        )


def test_example_copies_no_canonical_detail() -> None:
    """AC-0004: no run of ten or more consecutive words in the example appears in SKILL.md
    or any other file in references/, and the example carries no preflight exit-code table
    and no completeness-field table.
    """
    example_text: str = _read(EXAMPLE_PATH)

    # Check for absent tables: no preflight exit-code table header.
    assert "| Exit | Meaning" not in example_text, (
        "example must not carry a preflight exit-code table"
    )
    # No completeness-field table header from capability-map.md.
    assert "| CLI field | MCP field" not in example_text and \
           "| Limit |" not in example_text, (
        "example must not carry a completeness-field table"
    )

    # Build the combined reference corpus: SKILL.md + all references/ files
    # except the example itself.
    corpus_parts: list[str] = [_read(SKILL_MD)]
    for ref_file in sorted(REFERENCES_DIR.glob("*.md")):
        if ref_file != EXAMPLE_PATH:
            corpus_parts.append(_read(ref_file))
    corpus: str = " ".join(corpus_parts)

    # Tokenise the example by whitespace and check 10-gram windows.
    tokens: list[str] = example_text.split()
    window_size = 10
    for i in range(len(tokens) - window_size + 1):
        gram: str = " ".join(tokens[i : i + window_size])
        assert gram not in corpus, (
            f"example shares a {window_size}-word run with a canonical reference: "
            f"{gram!r}"
        )


def test_skill_and_readme_route_to_the_example() -> None:
    """AC-0008: SKILL.md and README.md each link to the example, call it an example
    rather than a contract, and state that other providers may expose fewer, different,
    or new capabilities and need not emulate Wicked Estate.
    """
    for label, path in (("SKILL.md", SKILL_MD), ("README.md", README_MD)):
        text: str = _read(path)
        assert "composition-example.md" in text, (
            f"{label} must link to composition-example.md"
        )
        assert "example" in text.lower(), (
            f"{label} must call the composition reference an example"
        )
        # Must not call it a contract without a negation nearby.
        contract_pos = text.lower().find("contract")
        if contract_pos >= 0:
            context = text[max(0, contract_pos - 40) : contract_pos + 40].lower()
            assert any(neg in context for neg in ("not a contract", "nonnormative", "illustrative", "not a required")), (
                f"{label} must not present the composition example as a contract"
            )
        assert "need not emulate wicked estate" in text.lower() or (
            "other providers" in text.lower() and "need not" in text.lower()
        ), (
            f"{label} must state that other providers need not emulate Wicked Estate"
        )
        assert "fewer, different, or new" in text.lower() or (
            "other providers may" in text.lower()
        ), (
            f"{label} must state that other providers may expose fewer, different, or new capabilities"
        )


def test_investigation_patterns_stay_open() -> None:
    """AC-0009: across SKILL.md, README.md, and every file in references/, no sentence
    calls the five investigation patterns complete, exhaustive, required, or closed, and
    SKILL.md and the example each state that the current patterns may change.
    """
    files_to_check: list[tuple[str, Path]] = [
        ("SKILL.md", SKILL_MD),
        ("README.md", README_MD),
    ]
    for ref_file in sorted(REFERENCES_DIR.glob("*.md")):
        files_to_check.append((ref_file.name, ref_file))

    for label, path in files_to_check:
        text: str = _read(path)
        # Check each sentence for forbidden claims about the patterns.
        for sentence in re.split(r"[.!?]\s+", text):
            lower = sentence.lower()
            if "pattern" not in lower and "investigation" not in lower:
                continue
            for forbidden in _PATTERN_CLAIM_WORDS:
                if forbidden in lower and not any(neg in lower for neg in _NEGATE_WORDS):
                    raise AssertionError(
                        f"{label}: sentence about patterns uses forbidden word "
                        f"{forbidden!r} without negation: {sentence[:120]!r}"
                    )
        # Must not claim patterns are a provider-neutral contract.
        assert "provider-neutral contract" not in text.lower(), (
            f"{label} must not call the investigation patterns a provider-neutral contract"
        )

    # SKILL.md and the example must each state that the current patterns may change.
    for label, path in (("SKILL.md", SKILL_MD), ("example", EXAMPLE_PATH)):
        text = _read(path)
        assert "patterns may change" in text.lower() or (
            "current" in text.lower() and "may change" in text.lower()
        ), (
            f"{label} must state that the current patterns may change"
        )


def test_example_retains_only_synthetic_evidence() -> None:
    """AC-0012: the example holds no absolute local path, home-directory path, email
    address, credential-shaped key, or hostname outside example.com and example.invalid,
    and states that provider output is untrusted data.
    """
    text: str = _read(EXAMPLE_PATH)

    # No absolute local paths (Unix or Windows style).
    assert not re.search(r"^/(?!example)[^\s]+", text, re.MULTILINE), (
        "example must not contain absolute local paths"
    )
    assert not re.search(r"\b[A-Z]:\\", text), (
        "example must not contain Windows absolute paths"
    )

    # No home-directory paths.
    assert "~/" not in text, (
        "example must not contain home-directory paths"
    )

    # No email addresses.
    assert not re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text), (
        "example must not contain email addresses"
    )

    # No credential-shaped keys (long hex or base64 strings that look like secrets).
    assert not re.search(r"\b[A-Za-z0-9+/]{40,}={0,2}\b", text), (
        "example must not contain credential-shaped keys"
    )

    # No hostnames outside example.com, example.invalid, and the upstream project link.
    for m in re.finditer(r"https?://([^/\s)\"']+)", text):
        host = m.group(1)
        # Allow github.com for the upstream project reference.
        if host in ("github.com", "example.com", "example.invalid") or \
           host.endswith((".example.com", ".example.invalid")):
            continue
        raise AssertionError(f"example contains a disallowed hostname {host!r}")

    # Must state that provider output is untrusted data.
    assert "untrusted data" in text.lower(), (
        "example must state that provider output is untrusted data"
    )
