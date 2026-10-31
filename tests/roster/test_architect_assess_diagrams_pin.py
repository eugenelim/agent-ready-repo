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


SPECS = REPO_ROOT / "docs/specs"
EXCEPTION = "Exception: with `--diagrams`, which `docs/specs/architect-assess-html-diagrams/spec.md` owns."
AMENDED = {
    "architect-assess-html-report": (
        "- Any `<script>` element in the output",
        "- Load script, style, font, or image from a network location.",
        "- Add a third-party dependency, a vendored third-party asset",
        "- [x] Each Mermaid fence appears as a `<pre>` under the visible label",
        "- [x] `references/html-report.md` lists every exit 2 reason",
        "- [x] Opened in a real browser, a sample report shows shaded heat cells",
    ),
    "architect-assess-html-report-style": (
        "- **Constrained by:**",
        "- Any element, attribute, or CSP source beyond those the acceptance criteria name.",
        "- Add a script, a web font, an image, or any network reference to the page.",
        "- [x] Every element in the parsed output is one of",
        "- [x] Every attribute in the parsed output is one of",
    ),
}


def test_every_amended_parent_rule_carries_the_exception() -> None:
    for slug, starts in AMENDED.items():
        lines = (SPECS / slug / "spec.md").read_text(encoding="utf-8").splitlines()
        for start in starts:
            hits = [line for line in lines if line.startswith(start)]
            assert len(hits) == 1, (slug, start)
            assert hits[0].endswith(EXCEPTION), (slug, start)


def test_user_docs_name_the_flag_the_host_and_the_sharing_warning() -> None:
    guides = (
        REPO_ROOT / "guides/architect/reference/architecture-assessment.md",
        REPO_ROOT / "guides/architect/how-to/assess-a-repository.md",
    )
    for path in guides:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "cdn.jsdelivr.net" in text, path.name
        assert "share" in text.lower() and "readers who accept that" in text, path.name
    reference = " ".join(guides[0].read_text(encoding="utf-8").split())
    assert "--diagrams" in reference
