"""PLAN-time contract stub for source-agent `metadata.boundaries` validation.

T1 of `docs/specs/shaping-review-contracts` makes boundary metadata a validated
source contract. The declaration lives on the source agent under
`packs/*/.apm/agents/`, not on the projected `.claude/agents/` artifact, which
the Claude Code projection seam strips — `metadata` is not a recognised Claude
Code subagent frontmatter key.

The grounded seam is `catalogue verify` step 2, which runs `lint_catalogue` over
the pack tree (`catalogue_tooling/verify.py:141-150`, `:2199`). These assertions
pin that step's observable behaviour without pinning which module inside
`lint_catalogue` grows the check.

Lives in `tests/roster/` rather than `packages/agentbundle/tests/` because it is
a PLAN-time red stub. `packages/agentbundle/MANIFEST.in` grafts `tests/` into the
sdist and `tools/check-artifact-contents.py` re-runs the whole extracted tree,
raising `ArtifactViolation` on any non-zero exit with no deselection hook — so a
red module there reddens `gate-export-boundary`, `build-and-smoke`, and
`make build-check`.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.catalogue_tooling.lint import lint_catalogue
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

_PACK_TOML = (
    '[pack]\nname = "pack-a"\nversion = "0.1.0"\n\n'
    "[pack.first-value]\n"
    'audience-posture = "technical"\n'
    'surfaces = ["claude"]\n'
    "prerequisites = []\n"
    'verification = "run tests"\n'
    'recovery = "revert"\n'
)


def _catalogue(root: Path, agent_frontmatter: str) -> Path:
    """Build a minimal one-pack catalogue carrying a single source agent."""
    root.joinpath("catalogue.toml").write_text(
        emit_catalogue_toml(
            name="test-catalogue",
            display_name="Test catalogue",
            description="Agent boundary metadata fixture.",
            minimum_agentbundle_version="0.32.0",
            owner_name="Example User",
            preferred_adapter="claude-code",
        ),
        encoding="utf-8",
        newline="\n",
    )
    marketplace = root / ".claude-plugin"
    marketplace.mkdir(parents=True, exist_ok=True)
    marketplace.joinpath("marketplace.json").write_text(
        "{}", encoding="utf-8", newline="\n"
    )
    pack = root / "packs" / "pack-a"
    agents = pack / ".apm" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    pack.joinpath("pack.toml").write_text(_PACK_TOML, encoding="utf-8", newline="\n")
    manifest = pack / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '{"name": "pack-a", "version": "0.1.0"}', encoding="utf-8", newline="\n"
    )
    agents.joinpath("probe-reviewer.md").write_text(
        f"---\n{agent_frontmatter}---\n\n# Probe\n\nBody.\n",
        encoding="utf-8",
        newline="\n",
    )
    return root


_VALID = (
    "name: probe-reviewer\n"
    "description: Probe agent.\n"
    "tools: Read, Grep, Glob\n"
    "skills: []\n"
    "model: opus\n"
    "metadata:\n"
    "  type: agent\n"
    "  boundaries: [filesystem_read_untrusted]\n"
)

_WIDENED = _VALID.replace(
    "boundaries: [filesystem_read_untrusted]",
    "boundaries: [filesystem_read_untrusted, filesystem_write, network_fetch]",
)

_UNKNOWN_VALUE = _VALID.replace(
    "boundaries: [filesystem_read_untrusted]", "boundaries: [read_everything]"
)

_NOT_A_LIST = _VALID.replace(
    "boundaries: [filesystem_read_untrusted]", "boundaries: filesystem_read_untrusted"
)


def _boundary_diagnostics(root: Path) -> list[str]:
    return [
        d.message
        for d in lint_catalogue(root).diagnostics
        if "boundaries" in d.message
    ]


def test_valid_boundary_declaration_is_accepted(tmp_path: Path) -> None:
    """A declared read-only boundary passes the source-agent gate."""
    # STUB: AC6 — catalogue validation accepts a source agent's metadata.boundaries
    assert _boundary_diagnostics(_catalogue(tmp_path, _VALID)) == []


def test_unknown_boundary_value_is_rejected(tmp_path: Path) -> None:
    """A value outside the security convention's five is a diagnostic."""
    # STUB: AC6 — missing or widened source declarations fail catalogue verification
    assert _boundary_diagnostics(_catalogue(tmp_path, _UNKNOWN_VALUE))


def test_non_list_boundaries_is_rejected(tmp_path: Path) -> None:
    """`boundaries` must be a list, not a bare scalar."""
    # STUB: AC6 — the validator enforces the bounded metadata schema
    assert _boundary_diagnostics(_catalogue(tmp_path, _NOT_A_LIST))


def test_widened_boundaries_on_a_read_only_agent_is_rejected(tmp_path: Path) -> None:
    """Write and network boundaries cannot ride along with read-only tools."""
    # STUB: AC6 — no declaration widens beyond the agent's tools
    assert _boundary_diagnostics(_catalogue(tmp_path, _WIDENED))
