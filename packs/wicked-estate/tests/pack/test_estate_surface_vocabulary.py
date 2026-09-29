"""Fail if this pack names a Wicked Estate command or MCP tool that does not exist.

The pack's central promise is that it maps only what Wicked Estate exposes
today. Prose cannot enforce that, and an invented verb reads exactly like a real
one, so this suite pins the vocabulary.

Both allowlists were transcribed from Wicked Estate at the version recorded in
``VERIFIED_AGAINST``:

* CLI verbs — the dispatch arms in ``crates/wicked-estate/src/main.rs``. Note
  this is a superset of ``wicked-estate --help``, which omits ``graph-view``
  and ``by-requirement``.
* MCP tools — the registered tool names in ``crates/wicked-estate-mcp/src/``,
  cross-checked against the frozen conformance schemas under
  ``crates/wicked-estate-mcp/tests/conformance/schemas/``.

When Wicked Estate releases a new version, re-derive both lists from source
before widening them. Adding a name here to make a test pass, without checking
it upstream, defeats the only mechanical guard the pack has.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: The upstream release both allowlists were transcribed from.
VERIFIED_AGAINST = "0.16"

PACK_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = PACK_ROOT / ".apm"

#: Every subcommand `wicked-estate` dispatches. `hotspots` is an alias of `rank`.
CLI_VERBS = frozenset(
    {
        "annotate",
        "annotations",
        "blast-radius",
        "by-requirement",
        "changed-since",
        "clusters",
        "compact",
        "context",
        "correspond",
        "cross-graph",
        "dead-code",
        "drift",
        "entrypoints",
        "export",
        "fingerprint",
        "graph-view",
        "hotspots",
        "import-telemetry",
        "index",
        "leaves",
        "nodes",
        "plugins",
        "query",
        "rank",
        "resolve",
        "scip",
        "semantic",
        "semantics",
        "source",
        "stale-annotations",
        "stats",
        "subscribe",
        "tfstate",
        "watch",
    }
)

#: The 11 estate-domain MCP tools, plus `SemanticSearch`, which the server
#: advertises only when an embedding backend is available.
MCP_ESTATE_TOOLS = frozenset(
    {
        "SearchEntity",
        "RetrieveEntity",
        "TraverseGraph",
        "BlastRadius",
        "FetchContent",
        "ContextBundle",
        "RulesInventory",
        "RankHotspots",
        "Communities",
        "Lineage",
        "SemanticSearch",
    }
)

#: Dotted MCP tools across the rules, memory, knowledge, and proposal domains.
MCP_DOTTED_TOOLS = frozenset(
    {
        "rules.recall",
        "memory.capture",
        "memory.recall",
        "memory.reflect",
        "memory.erase",
        "memory.learn",
        "memory.coverage",
        "memory.list",
        "knowledge.ingest",
        "knowledge.write",
        "knowledge.relate",
        "knowledge.recall",
        "knowledge.coverage",
        "knowledge.relate_code",
        "knowledge.recall_about_code",
        "proposal.submit",
        "proposal.list",
        "proposal.approve",
        "proposal.reject",
    }
)

#: A `wicked-estate <verb>` invocation. Long flags are excluded so that a
#: documented `wicked-estate --help` does not read as a verb.
_CLI_INVOCATION = re.compile(r"\bwicked-estate\s+(?!-)([a-z][a-z-]*)")

#: A dotted MCP tool reference in one of the four domains that use this shape.
_DOTTED_TOOL = re.compile(r"\b((?:rules|memory|knowledge|proposal)\.[a-z_]+)\b")


def runtime_documents() -> list[Path]:
    """Every projected Markdown file in the pack's runtime payload."""
    return sorted(RUNTIME_ROOT.rglob("*.md"))


def test_runtime_payload_is_present() -> None:
    """A vocabulary guard that scans nothing would pass vacuously."""
    documents = runtime_documents()
    assert documents, f"no runtime Markdown found under {RUNTIME_ROOT}"


@pytest.mark.parametrize("document", runtime_documents(), ids=lambda p: p.name)
def test_cli_verbs_exist_upstream(document: Path) -> None:
    """Every `wicked-estate <verb>` the pack shows is a real subcommand."""
    text = document.read_text(encoding="utf-8")
    used = {match.group(1) for match in _CLI_INVOCATION.finditer(text)}
    unknown = sorted(used - CLI_VERBS)
    assert not unknown, (
        f"{document.relative_to(PACK_ROOT)} names CLI verbs absent from Wicked "
        f"Estate {VERIFIED_AGAINST}: {unknown}"
    )


@pytest.mark.parametrize("document", runtime_documents(), ids=lambda p: p.name)
def test_dotted_mcp_tools_exist_upstream(document: Path) -> None:
    """Every dotted MCP tool the pack names is a registered tool."""
    text = document.read_text(encoding="utf-8")
    used = {match.group(1) for match in _DOTTED_TOOL.finditer(text)}
    unknown = sorted(used - MCP_DOTTED_TOOLS)
    assert not unknown, (
        f"{document.relative_to(PACK_ROOT)} names MCP tools absent from Wicked "
        f"Estate {VERIFIED_AGAINST}: {unknown}"
    )


def test_capability_map_names_every_estate_tool() -> None:
    """The capability map is the pack's inventory, so it must be complete.

    An absent tool is the failure this catches: a reader who trusts the map to
    be exhaustive would conclude the capability does not exist.
    """
    capability_map = (
        RUNTIME_ROOT / "skills/code-intelligence/references/capability-map.md"
    ).read_text(encoding="utf-8")
    missing = sorted(tool for tool in MCP_ESTATE_TOOLS if tool not in capability_map)
    assert not missing, f"capability-map.md omits estate MCP tools: {missing}"


def test_capability_map_records_the_verified_version() -> None:
    """A surface map with no version is unfalsifiable a release later."""
    capability_map = (
        RUNTIME_ROOT / "skills/code-intelligence/references/capability-map.md"
    ).read_text(encoding="utf-8")
    assert VERIFIED_AGAINST in capability_map, (
        "capability-map.md must state the Wicked Estate version its rows were "
        f"verified against ({VERIFIED_AGAINST})"
    )


def test_no_workflow_state_vocabulary_in_runtime_payload() -> None:
    """The pack must not smuggle job-lifecycle semantics into estate guidance.

    These are the exact terms the pack's boundary section rules out. They may
    appear as prohibitions, so the check targets the graph-relationship spelling
    that would only occur if someone modelled workflow state as estate data.
    """
    forbidden = ("MIGRATES_TO", "INTENTIONALLY_CHANGED")
    offenders: list[str] = []
    for document in runtime_documents():
        text = document.read_text(encoding="utf-8")
        for term in forbidden:
            # Naming a term to forbid it is fine; asserting it as a real
            # relationship is not. Require the negation to be adjacent.
            for line in text.splitlines():
                if term in line and not any(
                    cue in line.lower() for cue in ("not ", "never", "do not", "belong")
                ):
                    offenders.append(f"{document.name}: {line.strip()}")
    assert not offenders, "workflow state asserted as estate data: " + "; ".join(offenders)
