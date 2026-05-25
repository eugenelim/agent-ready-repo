"""Doc-grep checks for apm-install-route-parity sibling-spec amendments.

T7, T8, T10, T11, T12 of `docs/specs/apm-install-route-parity/plan.md`
modify four sibling specs, the manual-QA matrix, and a per-pack README.
These tests are mechanical greps — they pin the literal contract-surface
strings the plan calls out, so a future edit cannot silently drop them.

Spec: docs/specs/apm-install-route-parity/spec.md
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def _read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T7 / AC14: adapt-to-project spec gains AC27 + Changelog line
# ---------------------------------------------------------------------------


def test_adapt_spec_has_ac27_apm_stale_entry_drop():
    """T7 / AC14: AC27 lands in the Acceptance Criteria block of
    adapt-to-project/spec.md — bound the assertion to that block so a
    paraphrase elsewhere (Changelog, prose) cannot silently pass."""
    body = _read("docs/specs/adapt-to-project/spec.md")
    ac_start = body.find("## Acceptance Criteria")
    assert ac_start >= 0, "adapt-to-project/spec.md must have an AC section"
    # Locate the section's end (next ## header).
    after_header = body.find("\n## ", ac_start + len("## Acceptance Criteria"))
    ac_block = body[ac_start:after_header] if after_header > 0 else body[ac_start:]
    assert "**AC27" in ac_block, "AC27 must appear in the AC list, not just in prose"
    assert "APM-route stale-entry drop" in ac_block, (
        "AC27 must name the APM-route stale-entry-drop rail within the AC block"
    )


def test_adapt_spec_changelog_names_this_spec():
    body = _read("docs/specs/adapt-to-project/spec.md")
    assert "docs/specs/apm-install-route-parity/spec.md" in body, (
        "adapt-to-project Changelog must reference apm-install-route-parity by path"
    )


def test_adapt_spec_schema_permits_apm_install_route_value():
    """T3 / AC10: schema permitted-values list extended to include "apm"."""
    body = _read("docs/specs/adapt-to-project/spec.md")
    assert '"cli" | "claude-plugins" | "apm"' in body, (
        "schema comment must list all three permitted install-route values"
    )


# ---------------------------------------------------------------------------
# T8 / AC15: distribution-adapters spec amendment
# ---------------------------------------------------------------------------


def test_distribution_adapters_changelog_names_this_spec():
    body = _read("docs/specs/distribution-adapters/spec.md")
    assert "docs/specs/apm-install-route-parity/spec.md" in body


def test_distribution_adapters_changelog_names_v05_bump():
    body = _read("docs/specs/distribution-adapters/spec.md")
    # Look for a v0.4 → v0.5 line in the Changelog.
    assert "v0.4 → v0.5" in body or "0.4 → 0.5" in body, (
        "Changelog must record the contract version bump"
    )


def test_distribution_adapters_has_apm_conformance_ac():
    """T8 / AC15: APM-route conformance AC lands in the Acceptance
    Criteria block — bound the assertion to that block so a paraphrase
    in the Changelog cannot silently pass for it."""
    body = _read("docs/specs/distribution-adapters/spec.md")
    ac_start = body.find("## Acceptance Criteria")
    assert ac_start >= 0, "distribution-adapters/spec.md must have an AC section"
    after_header = body.find("\n## ", ac_start + len("## Acceptance Criteria"))
    ac_block = body[ac_start:after_header] if after_header > 0 else body[ac_start:]
    lower = ac_block.lower()
    assert "apm-route conformance" in lower or "apm route conformance" in lower, (
        "distribution-adapters spec must declare an apm-route conformance AC "
        "within the Acceptance Criteria block"
    )


def test_distribution_adapters_names_apm_test_file_by_path():
    body = _read("docs/specs/distribution-adapters/spec.md")
    assert (
        "packages/agentbundle/tests/integration/test_apm_install_route.py"
        in body
    ), (
        "distribution-adapters spec must reference the APM test file by literal path"
    )


# ---------------------------------------------------------------------------
# T10: claude-plugins-install-route spec amendments
# ---------------------------------------------------------------------------


def test_precedent_spec_ac1_allowlist_includes_argparse():
    body = _read("docs/specs/claude-plugins-install-route/spec.md")
    # AC1's allow-list is enumerated as a set literal in the AC body.
    assert "argparse, datetime, hashlib" in body, (
        "AC1 allow-list must list argparse alongside the other stdlib modules"
    )


def test_precedent_spec_ac9_hook_command_includes_flag():
    body = _read("docs/specs/claude-plugins-install-route/spec.md")
    assert "--install-route claude-plugins" in body, (
        "AC9 hook-command literal must include --install-route claude-plugins"
    )


def test_precedent_spec_ac9_shlex_token_list_includes_flag():
    body = _read("docs/specs/claude-plugins-install-route/spec.md")
    # The expected-token list must include the two new tokens.
    assert '"--install-route", "claude-plugins"' in body, (
        "AC9 shlex.split expected-token list must end with the two flag tokens"
    )


def test_precedent_spec_changelog_names_this_spec():
    body = _read("docs/specs/claude-plugins-install-route/spec.md")
    assert "docs/specs/apm-install-route-parity/spec.md" in body


# ---------------------------------------------------------------------------
# T11 / AC17: manual-QA matrix rows
# ---------------------------------------------------------------------------


def test_manual_qa_matrix_has_apm_core_row():
    body = _read("docs/specs/adapt-to-project/notes/manual-qa-matrix.md")
    assert "apm install of core at project scope" in body


def test_manual_qa_matrix_has_apm_converters_row():
    body = _read("docs/specs/adapt-to-project/notes/manual-qa-matrix.md")
    assert "apm install -g of converters at user scope" in body


def test_manual_qa_matrix_has_apm_per_target_row():
    body = _read("docs/specs/adapt-to-project/notes/manual-qa-matrix.md")
    assert "APM per-target characterisation" in body


def test_manual_qa_matrix_apm_rows_carry_verification_transcript():
    body = _read("docs/specs/adapt-to-project/notes/manual-qa-matrix.md")
    # Each of the three new APM rows declares verification = transcript.
    # Count occurrences of the apm-row identifying substrings to confirm
    # each one carries the transcript declaration nearby.
    for needle in (
        "apm install of core at project scope",
        "apm install -g of converters at user scope",
        "APM per-target characterisation",
    ):
        idx = body.find(needle)
        assert idx >= 0, f"row missing: {needle}"
        row = body[idx : idx + 800]
        assert "verification = transcript" in row, (
            f"row {needle!r} must declare verification = transcript; got: {row!r}"
        )


# ---------------------------------------------------------------------------
# T12 / AC18: packs/core/README.md disclosure
# ---------------------------------------------------------------------------


def test_core_readme_discloses_apm_manual_fallback():
    body = _read("packs/core/README.md")
    assert "agentbundle adapt --scope" in body, (
        "packs/core/README.md must name the manual-fallback gesture verbatim"
    )


def test_core_readme_names_four_covered_targets():
    body = _read("packs/core/README.md")
    for target in ("Claude Code", "Copilot", "Cursor", "Gemini"):
        assert target in body, (
            f"packs/core/README.md must name HookIntegrator-covered target {target!r}"
        )


def test_core_readme_names_three_uncovered_targets():
    body = _read("packs/core/README.md")
    for target in ("Codex", "OpenCode", "Windsurf"):
        assert target in body, (
            f"packs/core/README.md must name no-hook target {target!r}"
        )


def test_core_readme_disclosure_substrings_share_one_section(tmp_path):
    """AC18 paragraph-containment pin (quality-engineer Nit 8): the spec
    says *"all three substring sets appear within the same paragraph"*.
    A future README rewrite that splits the disclosure into three
    separated sections would pass each `test_core_readme_names_*` test
    above but would silently break the spec's intent. Pin a single
    contiguous window of the README that contains *all* nine required
    substrings."""
    body = _read("packs/core/README.md")
    needed = {
        "Claude Code", "Copilot", "Cursor", "Gemini",
        "Codex", "OpenCode", "Windsurf",
        "agentbundle adapt --scope",
    }
    # Walk every 1000-char window and assert at least one contains all
    # eight required substrings.
    window_size = 1000
    found_window = False
    for start in range(0, max(1, len(body) - window_size + 1)):
        window = body[start : start + window_size]
        if all(s in window for s in needed):
            found_window = True
            break
    assert found_window, (
        "packs/core/README.md disclosure must keep all eight required "
        f"substrings within a single {window_size}-char window; the "
        "current layout has split them across sections"
    )
