"""Core pack hook and post-install disclosure checks."""

from __future__ import annotations

import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]

_HOOK_SECTION_HEADING = "## Post-install adaptation, and the hooks that only repeat it"


def _read(path: Path) -> str:
    """Read one documentation source as UTF-8."""
    return path.read_text(encoding="utf-8")


def _collapsed(body: str) -> str:
    """Collapse prose whitespace so line wrapping does not change assertions."""
    return " ".join(body.split())


def _core_next_action() -> str:
    """Read the handoff string from the pack manifest that owns it.

    `pack.toml` is the single source of truth for the installer's `Next:` text
    (`[pack.first-value] next-action`). Deriving it here rather than restating
    it means editing the manifest alone cannot leave the README quoting stale
    text with this suite green. The integration test keeps its own hard-coded
    literal on purpose — that copy *is* the AC1 contract and should fail loudly
    when the text changes.
    """
    manifest = tomllib.loads(_read(PACK_ROOT / "pack.toml"))
    return manifest["pack"]["first-value"]["next-action"]


def _hook_section() -> str:
    """Return the collapsed hook/post-install section, not the whole README.

    Slicing to the owning section preserves the locality that the previous
    sliding-window test provided: without it, a short fragment such as `trust`
    or `Cursor` could be satisfied by an unrelated mention elsewhere in the
    README and the assertion would stop meaning anything.
    """
    body = _read(PACK_ROOT / "README.md")
    start = body.index(_HOOK_SECTION_HEADING)
    return _collapsed(body[start:])


def _hook_section_paragraph_naming(needle: str) -> str:
    """Return the collapsed paragraph inside the hook section containing *needle*.

    A paragraph, not a `". "`-delimited sentence: sentence splitting breaks on
    the first dot, so a filename like `.apm/...` or a clause joined by an em
    dash silently truncates or widens the window being asserted.
    """
    body = _read(PACK_ROOT / "README.md")
    section = body[body.index(_HOOK_SECTION_HEADING):]
    for paragraph in section.split("\n\n"):
        if needle in paragraph:
            return _collapsed(paragraph)
    raise AssertionError(
        f"packs/core/README.md § {_HOOK_SECTION_HEADING} no longer has a "
        f"paragraph naming {needle!r}"
    )


def test_core_readme_discloses_codex_hook_projection_and_runtime_gates() -> None:
    """Codex projection and execution are documented as separate facts."""
    section = _hook_section()

    assert ".codex/hooks.json" in section
    assert "SessionStart" in section
    assert "A projected file does not prove execution" in section
    missing = [
        gate
        for gate in ("managed policy", "trust", "command resolution", "output protocol")
        if gate not in section
    ]
    assert not missing, (
        f"packs/core/README.md § {_HOOK_SECTION_HEADING} must keep projection "
        f"separate from execution by naming every runtime gate; missing: {missing}"
    )


def test_core_readme_names_current_apm_hook_targets() -> None:
    """The README follows APM's current HookIntegrator target inventory."""
    section = _hook_section()

    missing = [
        target
        for target in (
            "Claude Code",
            "Copilot",
            "Cursor",
            "Gemini",
            "Codex",
            "Antigravity",
            "Windsurf",
            "Kiro",
        )
        if target not in section
    ]
    assert not missing, (
        f"packs/core/README.md must track APM's HookIntegrator targets; "
        f"missing: {missing}"
    )
    assert "OpenCode remains unsupported" in section


def test_core_readme_discloses_deterministic_manual_handoff() -> None:
    """The installer handoff remains useful when lifecycle hooks do not run."""
    section = _hook_section()
    next_action = _core_next_action()

    assert next_action in section, (
        "packs/core/README.md must quote the installer handoff verbatim; "
        "re-sync its fenced block with [pack.first-value] next-action in "
        "packs/core/pack.toml"
    )
    assert "even if a hook also runs" in section


def test_core_readme_separates_skill_from_cli_adapt() -> None:
    """The README distinguishes the skill from deterministic CLI adapt.

    The repository-level halves of this contract — the adapt-to-project guide
    and the install-route explanation — are asserted by
    ``tests/roster/test_core_onboarding_documentation.py``, because a
    pack-scoped test may not read above ``packs/core``.
    """
    readme = _collapsed(_read(PACK_ROOT / "README.md"))

    assert "has no `--scope` option" in readme
    assert "agentbundle adapt --scope" not in readme


def test_core_readme_states_no_obsolete_hook_support_claim() -> None:
    """The stale "Codex has no hook surface" class of claim stays gone.

    The spec's testing strategy requires the obsolete claim to be *rejected*,
    not merely absent, so a future edit cannot reintroduce it silently. The
    literal needles below are the phrasing this change actually deleted — an
    invented paraphrase would not have matched it, and so would not have
    protected anything.
    """
    readme = _collapsed(_read(PACK_ROOT / "README.md"))

    for stale in (
        "lack the hook surface",
        "lacks the hook surface",
        "no hook surface",
        "lacks hooks",
        "projects the install-marker hook to",
    ):
        assert stale not in readme, (
            f"packs/core/README.md reintroduced the obsolete support claim "
            f"{stale!r}; Codex now supports repository hooks"
        )

    # Assert the POSITIVE contract, not a blocklist of negative words. A
    # blocklist is defeated by one interposed word ("no *usable* hook surface")
    # or by joining clauses with an em dash, and enumerating every phrasing of
    # "unsupported" is not a winnable game. Instead: the paragraph that names
    # HookIntegrator must list Codex among its targets and must carry no
    # negation at all.
    paragraph = _hook_section_paragraph_naming("HookIntegrator")
    assert "Codex" in paragraph, (
        "the APM HookIntegrator paragraph in packs/core/README.md omits Codex; "
        "APM covers it now, so the target list is stale"
    )
    # The invariant is that this paragraph is negation-FREE apart from the one
    # named exception. That is checkable; a blocklist of negative phrasings is
    # not — "no usable hook surface" defeats a "no hook" needle, and the next
    # rewording defeats whatever is added to chase it. Strip the single allowed
    # clause, then require no negation of any kind in what remains.
    remainder = paragraph.replace("OpenCode remains unsupported", "")
    negations = [
        token
        for token in ("no ", "not ", "n't", "cannot", "lack", "unsupported",
                      "out of scope", "except")
        if token in remainder
    ]
    assert not negations, (
        f"the APM HookIntegrator paragraph in packs/core/README.md carries "
        f"negation {negations}; every target it lists is supported and OpenCode "
        f"is the only documented exception, so any other negation is either a "
        f"stale support claim or belongs in its own paragraph. Paragraph: "
        f"{paragraph!r}"
    )


def test_core_readme_makes_no_universal_marker_claim() -> None:
    """No claim that every route or every install writes an adaptation marker."""
    readme = _collapsed(_read(PACK_ROOT / "README.md"))

    for stale in (
        "every supported install route",
        "Every install route writes",
        "every install route writes",
        "written automatically by every",
    ):
        assert stale not in readme, (
            f"packs/core/README.md reintroduced the universal-marker claim "
            f"{stale!r}; only the direct repo route writes a marker"
        )
