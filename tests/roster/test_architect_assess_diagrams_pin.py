"""The architect-assess diagrams pin matches docs-site and the ADR that records it."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDERER = REPO_ROOT / "packs/architect/.apm/skills/architect-assess/scripts/render_html.py"
ADR = next((REPO_ROOT / "docs/adr").glob("0153-architect-assess-draws-diagrams-*.md"))


def _constant(name: str) -> str:
    match = re.search(rf'^{name} = "([^"]+)"$', RENDERER.read_text(encoding="utf-8"), re.M)
    assert match, name
    return match.group(1)


def test_pinned_version_equals_the_docs_site_pin() -> None:
    manifest = json.loads((REPO_ROOT / "docs-site/package.json").read_text(encoding="utf-8"))
    declared = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
    assert declared["mermaid"] == _constant("MERMAID_VERSION")


def test_pinned_url_is_built_from_the_version() -> None:
    text = RENDERER.read_text(encoding="utf-8")
    assert (
        'MERMAID_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}'
        '/dist/mermaid.min.js"'
    ) in text


def test_adr_records_the_pinned_version_url_and_hash() -> None:
    adr = ADR.read_text(encoding="utf-8")
    version = _constant("MERMAID_VERSION")
    assert f"https://cdn.jsdelivr.net/npm/mermaid@{version}/dist/mermaid.min.js" in adr
    assert _constant("MERMAID_SRI") in adr
    assert "**Status:** Accepted" in adr


def test_adr_states_its_required_points() -> None:
    adr = " ".join(ADR.read_text(encoding="utf-8").split())
    for phrase in (
        "integrity attribute binds the bytes",
        "opt-in",
        "docs-site",
        "Revisit if",
        "advisory is published against the pinned version",
        "the CDN host changes",
    ):
        assert phrase in adr, phrase
