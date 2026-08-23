"""Repository-level onboarding documentation contracts for the core install.

These assertions live here rather than in ``packs/core/tests/pack/`` because
they read ``guides/`` — a pack-scoped test that climbs above its own pack is
rejected by ``lint-boundary-structural``'s ``pack-tests-stay-in-pack`` check.
The pack-local half of the same contract (the core README) is asserted by
``packs/core/tests/pack/test_apm_readme_disclosure.py``.
"""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _collapsed(path: Path) -> str:
    """Read one documentation source, collapsing prose whitespace.

    Collapsing means a rewrap of the source cannot silently change what these
    substring assertions cover.
    """
    return " ".join(path.read_text(encoding="utf-8").split())


def test_adapt_guide_rejects_stale_scope_command() -> None:
    """The adapt-to-project guide documents no `agentbundle adapt --scope`."""
    guide = _collapsed(REPOSITORY_ROOT / "guides/core/how-to/adapt-to-project.md")

    assert "does not accept a `--scope` option" in guide
    assert "agentbundle adapt --scope" not in guide


def test_install_route_docs_disclose_local_scope_omissions() -> None:
    """Local installs are not documented as receiving seeds or a marker."""
    body = _collapsed(
        REPOSITORY_ROOT / "guides/_shared/explanation/install-routes.md"
    )

    assert "Local scope deliberately omits seeds" in body
    assert "No marker, layout section, or chained `adapt`" in body

    # The load-bearing claim is that a lifecycle hook is a repeat of the
    # printed handoff and never a precondition for it. Both halves are
    # asserted, so weakening either one fails here.
    assert "may repeat that nudge" in body
    assert "never the only path" in body

    # Negative half: the page must not tell the adopter to condition on a hook
    # nudge, which is the dependency this contract exists to remove.
    assert "if no nudge appears" not in body
    assert "does not surface a nudge" not in body

    # AC14's positive half — what the installer *does* guarantee — is as
    # load-bearing as the caveat, and is easy to drop while trimming hedging.
    assert "the installer guarantees the projected files" in body
    assert "does not guarantee hook execution or context injection" in body


def test_install_route_docs_make_no_universal_marker_claim() -> None:
    """Only the direct repo route writes a marker; no page may generalise it."""
    for rel in (
        "guides/_shared/explanation/install-routes.md",
        "guides/core/how-to/adapt-to-project.md",
        "docs/architecture/agentbundle.md",
    ):
        body = _collapsed(REPOSITORY_ROOT / rel)
        for stale in (
            "written automatically by every supported install route",
            "every supported install route",
            "Every install route writes",
            "every install route writes",
        ):
            assert stale not in body, (
                f"{rel} reintroduced the universal-marker claim {stale!r}; "
                f"local scope and the plugin/APM routes write no marker"
            )


def test_living_docs_do_not_confuse_apm_targets_with_direct_adapters() -> None:
    """AC7: the direct-adapter set and APM's target set stay distinct.

    `contracts/adapter.toml` is the source of truth for direct adapters, and it
    declares Cursor and Gemini among them. A living doc that attributes those to
    APM's `HookIntegrator` instead commits exactly the confusion AC7 forbids,
    which is what `guides/core/explanation/core-pack.md` did before this ran.
    """
    import tomllib

    contract = tomllib.loads(
        (REPOSITORY_ROOT / "contracts/adapter.toml").read_text(encoding="utf-8")
    )
    declared = set(contract["adapter"])
    assert {"cursor", "gemini"} <= declared, (
        "contracts/adapter.toml no longer declares cursor/gemini as direct "
        "adapters — this assertion's premise moved; re-derive it"
    )

    raw = (REPOSITORY_ROOT / "guides/core/explanation/core-pack.md").read_text(
        encoding="utf-8"
    )

    # Scope the assertion to whole PARAGRAPHS (and table rows) that mention
    # HookIntegrator, not to a `.`-delimited tail. A dot-split stops at the
    # first `.` — including the one in a path like `.apm/hook-wiring/...` — so a
    # misattribution placed after any dotted token, before the mention, or one
    # sentence later would slip straight through.
    blocks = [
        " ".join(block.split())
        for block in raw.replace("\n|", "\n\n|").split("\n\n")
        if "HookIntegrator" in block
    ]
    assert blocks, (
        "guides/core/explanation/core-pack.md no longer mentions HookIntegrator"
    )

    # Direction is the discriminator, not co-occurrence: the correct text names
    # these as direct adapters *and* mentions APM in the same table row. So
    # require each name to sit on the direct-adapter side — introduced by the
    # phrase "direct adapters" — and to be absent from the APM side, the text
    # following the HookIntegrator mention.
    direct_names = {"Cursor": "cursor", "Gemini": "gemini"}
    for block in blocks:
        apm_side = block.split("HookIntegrator", 1)[1]
        for display, key in direct_names.items():
            if key not in declared or display not in block:
                continue
            assert display not in apm_side, (
                f"guides/core/explanation/core-pack.md credits APM's "
                f"HookIntegrator with {display!r}, which contracts/adapter.toml "
                f"declares a direct adapter. Passage: {block!r}"
            )
            direct_side = block.split("HookIntegrator", 1)[0]
            assert "direct adapters" in direct_side.split(display)[0], (
                f"guides/core/explanation/core-pack.md names {display!r} in an "
                f"APM passage without introducing it as a direct adapter. "
                f"Passage: {block!r}"
            )

    # And the page must still name them somewhere as direct adapters.
    page = " ".join(raw.split())
    assert "Cursor" in page and "Gemini" in page


def test_hook_wiring_source_reads_as_portable_not_claude_only() -> None:
    """AC10: the core hook-wiring comments describe a portable source.

    AC10 had no verification artifact, so the wording it mandates could be
    rewritten away silently. The file is a pack source, but this claim is about
    repository-wide adapter portability, so it is asserted here.
    """
    body = _collapsed(
        REPOSITORY_ROOT / "packs/core/.apm/hook-wiring/session-start.toml"
    )

    assert "Portable hook-wiring source" in body
    assert "each direct adapter decides" in body
    # Codex is named as a merge target, which is the fact that made the old
    # Claude-only framing wrong.
    assert ".codex/hooks.json" in body
    # The obsolete Kiro exclusion must not come back.
    assert "Kiro is out of scope" not in body
    assert "Kiro-only field" not in body
