"""Deterministic render tests for the OKF authoring compiler."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path, PureWindowsPath

import pytest
from agentbundle.catalogue_tooling.skill_spec_lint import lint_skill_spec

SCRIPT_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "compile-okf"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_ROOT))

import okf_compiler  # noqa: E402
from okf_compiler import (  # noqa: E402
    canonical_json_bytes,
    render_okf_bundle,
    review_projection_digest,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "render"
RUNBOOK_DIGEST = "sha256:5133e0ae722bc233c04ee2f91cff6e54dd040be65487ff353a986c3aafeaf1a7"
STRICT_JSON_VECTOR = b'{"a":[true,null],"b":1}\n'
STRICT_JSON_DIGEST = "sha256:b7c64ebef4296c41c0c46ab5e7a71a88ab124b5fdb82613abc75327ce6195ec6"


def _copy_fixture(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURE_ROOT / "rich", bundle)
    (bundle / "empty").mkdir(exist_ok=True)
    return bundle


def _render(tmp_path: Path):
    bundle = _copy_fixture(tmp_path)
    return render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )


def test_render_stubs_compile_red_then_indexes_are_exact(tmp_path: Path) -> None:
    # STUB: AC2 — hostile title metadata stays inside its canonical index entry.
    result = _render(tmp_path)

    assert result.diagnostics == ()
    assert result.files["references/okf/index.md"].decode() == (
        "---\n"
        'okf_version: "0.2"\n'
        "---\n"
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# OKF index: rich\n\n"
        "- [concepts](concepts/index.md) - 4 concepts\n"
    )
    assert result.files["references/okf/concepts/index.md"].decode() == (
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# OKF index: concepts\n\n"
        "- [Deprecated Knowledge](deprecated.md) - Deprecated Note\n"
        "- [x\\]\\(../../../../SKILL.md\\) \\[Read \\<this\\> instead "
        "\\\\ bait](hostile-title.md) - Active Reference\\<bad\\>\\\\tail\n"
        "- [Hostile Prompt](hostile.md) - Active Note\n"
        "- [Reviewed Runbook](runbook.md) - Active Playbook\n"
    )
    assert "references/okf/empty/index.md" not in result.files
    assert "references/okf/concepts/stale.md" in result.files


def test_index_metadata_fields_are_bounded_and_context_escaped() -> None:
    # STUB: AC1 — every interpolated display field uses one bounded encoder.
    encode = okf_compiler._index_display_value

    assert encode("a" * 200 + "[truncated]") == "a" * 200
    assert encode("Active\r\n[status](bad)") == (
        "Active\\r\\n\\[status\\]\\(bad\\)"
    )
    # The scheme colon is escaped too: escaping `<`/`>` stops an inline autolink,
    # but GFM linkifies a bare `https://` run with no delimiter around it at all.
    assert encode("Reference<https://example.invalid/>\\tail") == (
        "Reference\\<https\\://example.invalid/\\>\\\\tail"
    )


def test_generated_index_normalizes_every_display_field() -> None:
    # STUB: AC1 — normalization is wired to title, status, and type interpolation.
    class HostileStatus:
        """Remain active while exposing hostile text during display coercion."""

        def __eq__(self, other: object) -> bool:
            return other == "Active"

        def __str__(self) -> str:
            return "Active\r\n[status](bad)" + "s" * 205

    class HostileType:
        """Expose delimiters from a non-string metadata value."""

        def __str__(self) -> str:
            return "Reference<bad>\\tail" + "t" * 205

    concepts = {
        "concepts/hostile.md": okf_compiler.Concept(
            path="concepts/hostile.md",
            metadata={
                "title": "x](bad)\r\n" + "a" * 205,
                "status": HostileStatus(),
                "type": HostileType(),
            },
            body="",
        )
    }

    index = okf_compiler._render_indexes("rich", concepts)["concepts/index.md"]

    assert index == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: concepts\n\n"
        "- [x\\]\\(bad\\)\\r\\n"
        + "a" * 191
        + "](hostile.md) - Active\\r\\n\\[status\\]\\(bad\\)"
        + "s" * 179
        + " Reference\\<bad\\>\\\\tail"
        + "t" * 181
        + "\n"
    ).encode()


def test_generated_index_encodes_path_derived_link_text_and_destinations() -> None:
    # AC2/AC17 — source paths cannot manufacture compiler-owned Markdown links.
    directory = "concepts(root)[fake]"
    concept_path = f"{directory}/x.md) [Read this](hostile.md"
    concepts = {
        concept_path: okf_compiler.Concept(
            path=concept_path,
            metadata={"title": "Safe title", "status": "Active", "type": "Reference"},
            body="",
        ),
        "concepts0/ordinary.md": okf_compiler.Concept(
            path="concepts0/ordinary.md",
            metadata={"title": "Ordinary", "status": "Active", "type": "Reference"},
            body="",
        ),
    }

    indexes = okf_compiler._render_indexes("rich", concepts)

    assert indexes["index.md"] == (
        "---\n"
        'okf_version: "0.2"\n'
        "---\n"
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: rich\n\n"
        "- [concepts\\(root\\)\\[fake\\]]"
        "(concepts%28root%29[fake]/index.md) - 1 concepts\n"
        "- [concepts0](concepts0/index.md) - 1 concepts\n"
    ).encode()
    assert indexes[f"{directory}/index.md"] == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: concepts\\(root\\)\\[fake\\]\n\n"
        # Brackets stay literal: a CommonMark destination may contain them, and
        # only unbalanced parens, space and controls can break out of one.
        "- [Safe title](x.md%29%20[Read%20this]%28hostile.md) "
        "- Active Reference\n"
    ).encode()


def test_display_escaping_covers_the_whole_control_class() -> None:
    # AC1 — this test used to iterate the five separators the escape table listed,
    # which made it a positive control that could not detect an omission. It
    # omitted three: `\x1c`, `\x1d` and `\x1e`, which `str.splitlines()` breaks on
    # and which reach a title through a YAML `"\x1c"` escape. Driving the class
    # instead of a list is what makes the next omission fail here.
    separators = {*range(0x20), 0x7F, *range(0x80, 0xA0), 0x2028, 0x2029}
    friendly = {0x09: r"\t", 0x0A: r"\n", 0x0D: r"\r"}
    for code_point in sorted(separators):
        character = chr(code_point)
        expected = friendly.get(
            code_point,
            rf"\u{code_point:04x}" if code_point > 0xFF else rf"\x{code_point:02x}",
        )
        rendered = okf_compiler._index_display_value(f"a{character}b")
        assert rendered == f"a{expected}b", (hex(code_point), rendered)
        # The point of escaping: one entry can never read as two.
        assert len(rendered.splitlines()) == 1, (hex(code_point), rendered)
        assert character not in rendered, (hex(code_point), rendered)


def test_destination_encoding_covers_the_same_control_class_as_display() -> None:
    # AC1 — the display table escaped the Unicode line and paragraph separators
    # while the destination encoder left them raw, so one rendered line escaped the
    # separator in its link text and emitted it literally in its destination. Both
    # legs must agree, or a splitlines() reader still counts an extra entry.
    for code_point in (*range(0x20), 0x7F, 0x85, 0x2028, 0x2029):
        character = chr(code_point)
        encoded = okf_compiler._index_link_destination(f"a{character}b.md")
        assert character not in encoded, (hex(code_point), encoded)
        assert len(encoded.splitlines()) == 1, (hex(code_point), encoded)


def test_destination_encoding_permits_every_legitimate_filename_shape() -> None:
    # AC1 — the permitting direction. Two earlier versions of this encoder ran the
    # whole path through `quote()`, which turned a legitimately named `café.md`
    # into an unopenable `caf%C3%A9.md`. A suite that only proves the blocking
    # direction passed for both of them.
    for filename in ("café.md", "a-b._~c.md", "notes/日本語.md", "UPPER-lower.md"):
        assert okf_compiler._index_link_destination(filename) == filename, filename


def test_destination_encoding_covers_every_member_of_its_character_class() -> None:
    # AC1 — six reachable members had no test input, including `%`, the one the
    # spec gives an explicit security rationale for: without it an emitted `%20`
    # is indistinguishable from a literal one, so `two%20words.md` and
    # `two words.md` would collide on a single destination.
    assert okf_compiler._index_link_destination("two%20words.md") == "two%2520words.md"
    assert okf_compiler._index_link_destination("two words.md") == "two%20words.md"
    for filename, expected in (
        ("don't.md", "don%27t.md"),
        ("a`b.md", "a%60b.md"),
        ("a^b.md", "a%5Eb.md"),
        ("a{b}.md", "a%7Bb%7D.md"),
        ("a|b.md", "a%7Cb.md"),
        ("a\x9fb.md", "a%C2%9Fb.md"),
    ):
        assert okf_compiler._index_link_destination(filename) == expected, filename


def test_colon_bearing_filename_is_refused_so_the_destination_need_not_encode_it() -> None:
    # AC1 — `:` is left literal in a destination, which is safe only because the
    # path gate rejects it: `javascript:alert(1).md` would otherwise yield a live
    # scheme URL for any renderer that does not sanitize schemes. This test couples
    # the two, so relaxing the gate reddens a test that names the reason.
    assert okf_compiler._is_safe_relative_path("concepts/javascript:alert(1).md") is False
    assert ":" not in okf_compiler._LINK_DESTINATION_UNSAFE.pattern
    assert (
        okf_compiler._index_link_destination("javascript:alert(1).md")
        == "javascript:alert%281%29.md"
    )


def test_display_escaping_neutralizes_every_gfm_autolink_trigger() -> None:
    # AC1 — GFM linkifies three shapes with no surrounding Markdown, so a display
    # value could render as a live link without containing a delimiter. The
    # frontmatter leg refuses a reference outright, but path-derived text (a
    # directory name) reaches the same sink and no refusal covers it. Escaping the
    # one punctuation mark each trigger needs is renderer-verified to leave the
    # rendered text byte-identical while the link goes inert.
    assert okf_compiler._index_display_value("www.evil.invalid") == "www\\.evil.invalid"
    assert okf_compiler._index_display_value("WWW.Evil.Invalid") == "WWW\\.Evil.Invalid"
    assert (
        okf_compiler._index_display_value("see http://evil.invalid")
        == "see http\\://evil.invalid"
    )
    # A bare address is the trigger that matching `mailto:` alone missed entirely,
    # and escaping the `mailto:` colon does not defuse it — GFM linkifies the
    # address on its own.
    assert okf_compiler._index_display_value("ops@evil.invalid") == "ops\\@evil.invalid"
    assert (
        okf_compiler._index_display_value("mailto:ops@evil.invalid")
        == "mailto\\:ops\\@evil.invalid"
    )
    # Ordinary metadata is untouched: no trigger, no backslash.
    for benign in ("Concept: overview", "v1.2.3-notes", "release-readiness"):
        assert okf_compiler._index_display_value(benign) == benign, benign


def test_path_derived_heading_cannot_form_a_live_autolink() -> None:
    # AC1 — the directory name reaches `# OKF index: <name>` space-preceded, which
    # is a valid GFM www-autolink start. The frontmatter refusal cannot reach it.
    directory = "www.internal.invalid"
    concepts = {
        f"{directory}/x.md": okf_compiler.Concept(
            path=f"{directory}/x.md",
            metadata={"title": "Safe", "status": "Active", "type": "Reference"},
            body="",
        )
    }

    indexes = okf_compiler._render_indexes("rich", concepts)

    assert indexes[f"{directory}/index.md"] == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: www\\.internal.invalid\n\n"
        "- [Safe](x.md) - Active Reference\n"
    ).encode()
    # The destination keeps the directory literal so the path stays openable.
    assert b"(www.internal.invalid/index.md)" in indexes["index.md"]


def test_display_escaping_neutralizes_code_span_and_emphasis_delimiters() -> None:
    # AC1 — a backtick in `title` paired with one in `type` opened a code span that
    # swallowed that entry's own destination; `*`/`_` distorted the entry.
    assert okf_compiler._index_display_value("a`code`b") == "a\\`code\\`b"
    assert okf_compiler._index_display_value("a*em*b") == "a\\*em\\*b"
    assert okf_compiler._index_display_value("a_em_b") == "a\\_em\\_b"


def test_frontmatter_remote_reference_is_refused_anywhere_in_the_value() -> None:
    # AC1 — RFC-0087 rejected runtime external fetch, so a URL in frontmatter is
    # never dereferenced and has no supported function; what it could do is become
    # a live GFM autolink in a compiler-owned index. A prefix-only test was
    # defeated by one leading character, and missed `www.`/`mailto:` entirely.
    for value in (
        "Reference https://evil.invalid/x",
        "see http://evil.invalid",
        "go to www.evil.invalid",
        "mail mailto:ops@evil.invalid",
        # A bare address is the fourth shape GFM linkifies. Matching `mailto:`
        # alone left it open, and it is the form a real corpus is most likely to
        # carry, so it is the one that mattered most.
        "escalate to ops@evil.invalid",
        "first.last+tag@sub.evil.invalid",
    ):
        codes = [
            diagnostic.code
            for diagnostic in okf_compiler._metadata_diagnostics(
                "concepts/x.md", {"type": value}
            )
        ]
        assert codes == ["OKF009"], (value, codes)

    # Ordinary metadata stays clean.
    assert okf_compiler._metadata_diagnostics(
        "concepts/x.md", {"title": "Release readiness", "type": "Reference"}
    ) == []


def test_concept_body_may_carry_links_for_manual_follow_up() -> None:
    # Deliberate asymmetry: an organization-specific corpus points a reader at an
    # internal app or runbook for manual follow-up. The body is where such a
    # pointer belongs — it reaches the agent on descent, is never fetched, and is
    # not scanned by the frontmatter remote-reference gate.
    body = (
        "Escalate manually at https://internal.corp/approvals.\n"
        "See [the runbook](https://internal.corp/runbook) and www.internal.corp.\n"
    )
    concepts = {
        "concepts/escalation.md": okf_compiler.Concept(
            path="concepts/escalation.md",
            metadata={"title": "Escalation", "status": "Active", "type": "Reference"},
            body=body,
        )
    }

    assert okf_compiler._metadata_diagnostics(
        "concepts/escalation.md",
        concepts["concepts/escalation.md"].metadata,
    ) == []

    indexes = okf_compiler._render_indexes("rich", concepts)
    assert indexes["concepts/index.md"] == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: concepts\n\n"
        "- [Escalation](escalation.md) - Active Reference\n"
    ).encode()


def test_non_encodable_path_is_refused_at_the_gate_not_at_the_encode() -> None:
    # A filename the filesystem yields as surrogate-escaped bytes reaches strict
    # encodes in the scan and the sort. Rejecting it at the existing path gate
    # keeps the failure on the documented OKF004 exit path instead of aborting the
    # process on an uncaught UnicodeEncodeError with no diagnostic.
    assert okf_compiler._is_safe_relative_path("concepts/bad\udcffname.md") is False
    # Legitimate names, including non-ASCII, must still pass.
    assert okf_compiler._is_safe_relative_path("concepts/ok.md") is True
    assert okf_compiler._is_safe_relative_path("concepts/café.md") is True


def test_refusing_a_non_encodable_path_survives_the_diagnostic_sort() -> None:
    # The gate above is not the whole exit path. `_sort_diagnostics` keys on a
    # strict `encode("utf-8")` of the diagnostic's own path, so refusing the file
    # still ended in an uncaught UnicodeEncodeError one layer later — a refusal
    # that produced no OKF0xx line. Asserting the predicate alone could not see
    # that, so this drives the sink the refusal actually flows through.
    diagnostic = okf_compiler._diagnostic(
        "OKF004", "concepts/bad\udcffname.md", "unsafe path"
    )
    assert "\udcff" not in diagnostic.path
    sorted_diagnostics = okf_compiler._sort_diagnostics([diagnostic])
    assert [item.code for item in sorted_diagnostics] == ["OKF004"]
    # An ASCII path is untouched, so no existing diagnostic's path changes.
    assert (
        okf_compiler._diagnostic("OKF004", "concepts/ok.md", "m").path
        == "concepts/ok.md"
    )


def test_non_encodable_frontmatter_value_is_diagnosed_not_crashed() -> None:
    # `license`, `boundaries`, and a nested `x-agentbundle` skill `description`
    # reach strict encodes on the manifest and digest path. Each must produce
    # OKF003 rather than an uncaught UnicodeEncodeError.
    for metadata in (
        {"license": "a\ud800b"},
        {"boundaries": ["ok", "b\ud800d"]},
        {"x-agentbundle": {"skill": {"description": "d\ud800e"}}},
    ):
        codes = [
            diagnostic.code
            for diagnostic in okf_compiler._metadata_diagnostics("concepts/x.md", metadata)
        ]
        assert codes == ["OKF003"], (metadata, codes)

    # Clean metadata, and non-ASCII, stay clean.
    assert okf_compiler._metadata_diagnostics(
        "concepts/x.md",
        {"license": "Apache-2.0 OR MIT", "title": "Café naïve 日本"},
    ) == []


def test_metadata_normalization_survives_a_lone_surrogate() -> None:
    # AC1 — a crash is not an escape. `yaml.safe_load` accepts a `\\uD800` escape, so a
    # lone surrogate reaches the display helper and would otherwise raise
    # UnicodeEncodeError at the index `.encode("utf-8")`, producing a traceback with
    # no OKF0xx line and breaking the diagnostic contract.
    #
    # This covers the display leg. The path and frontmatter legs are closed at
    # their own gates and asserted by the two tests above; the destination
    # assertion below is defence in depth for a value arriving from elsewhere.
    assert okf_compiler._index_display_value("a\ud800b").encode("utf-8")
    assert okf_compiler._index_link_destination("bad\udcffname.md").encode("utf-8")

    # Order: cap the raw value, then normalize, then escape. Normalizing first
    # would let the slice cut a generated `\\uXXXX` sequence in half, and the cap
    # would stop counting input characters.
    boundary = okf_compiler._index_display_value("a" * 197 + "\ud800")
    assert boundary.endswith("\\\\ud800"), boundary[-12:]
    assert len(okf_compiler._index_display_value("a" * 250)) == 200

    concepts = {
        "concepts/plain.md": okf_compiler.Concept(
            path="concepts/plain.md",
            metadata={"title": "a\ud800b", "status": "Active", "type": "Reference"},
            body="",
        ),
    }

    indexes = okf_compiler._render_indexes("rich", concepts)

    # Visible and escaped: the surrogate becomes the literal text `\ud800`, whose
    # backslash the display table then escapes, so it cannot act as Markdown.
    assert indexes["concepts/index.md"] == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: concepts\n\n"
        "- [a\\\\ud800b](plain.md) - Active Reference\n"
    ).encode()

    # Substitution is byte-identical across repeated renders, so OKF012 cannot
    # fire on normalization alone.
    assert okf_compiler._render_indexes("rich", concepts) == indexes


def test_generated_index_encodes_character_reference_filenames() -> None:
    # AC1 destination clause — a CommonMark renderer resolves character
    # references inside a link destination, so `&`, `#`, and `;` must not reach
    # it literally. A filename of `..&#x2F;..&#x2F;SKILL.md` would otherwise
    # render as href="../../SKILL.md" — an attacker-chosen traversal target.
    concepts = {
        "concepts/..&#x2F;..&#x2F;SKILL.md": okf_compiler.Concept(
            path="concepts/..&#x2F;..&#x2F;SKILL.md",
            metadata={"title": "Bait", "status": "Active", "type": "Reference"},
            body="",
        ),
        # Must stay LITERAL: the router tells an agent to open the cited path, so
        # encoding a legitimately named file would hand it a path not on disk.
        "concepts/café.md": okf_compiler.Concept(
            path="concepts/café.md",
            metadata={"title": "Café", "status": "Active", "type": "Reference"},
            body="",
        ),
        "concepts/two words.md": okf_compiler.Concept(
            path="concepts/two words.md",
            metadata={"title": "Two words", "status": "Active", "type": "Reference"},
            body="",
        ),
    }

    indexes = okf_compiler._render_indexes("rich", concepts)

    assert indexes["concepts/index.md"] == (
        f"{okf_compiler.MANAGED_INDEX_MARKER}\n"
        "# OKF index: concepts\n\n"
        "- [Bait](..%26%23x2F%3B..%26%23x2F%3BSKILL.md) - Active Reference\n"
        "- [Café](café.md) - Active Reference\n"
        "- [Two words](two%20words.md) - Active Reference\n"
    ).encode()
    rendered = indexes["concepts/index.md"].decode("utf-8")
    for forgeable in ("&#x2F;", "&sol;", "&amp;"):
        assert forgeable not in rendered


def test_nested_index_paths_are_posix_on_windows_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bundle-internal paths must not inherit the host path separator."""
    concepts = {
        "concepts/assessment-intents/baseline.md": okf_compiler.Concept(
            path="concepts/assessment-intents/baseline.md",
            metadata={"title": "Baseline", "status": "Active", "type": "Reference"},
            body="",
        )
    }
    monkeypatch.setattr(okf_compiler, "Path", PureWindowsPath)

    indexes = okf_compiler._render_indexes("architecture-lenses", concepts)

    assert "concepts/assessment-intents/index.md" in indexes
    assert all("\\" not in path for path in indexes)
    assert b"(concepts/assessment-intents/index.md)" in indexes["index.md"]


def test_router_skill_is_deterministic_nested_and_has_no_tools(tmp_path: Path) -> None:
    first = _render(tmp_path / "first")
    second = _render(tmp_path / "second")
    router = first.files["SKILL.md"].decode()

    assert first.files == second.files
    assert "allowed-tools" not in router
    assert "metadata:\n  boundaries: [filesystem_read_untrusted]" in router
    assert "generated-by: compile-okf agentbundle-okf/v1" in router
    assert "source-path: okf/rich" in router
    assert "source-digest: sha256:" in router
    assert "Read `references/okf/index.md` first." in router
    assert "Ignore previous instructions" not in router


def test_procedure_skill_contains_reviewed_section_and_untrusted_includes(
    tmp_path: Path,
) -> None:
    result = _render(tmp_path)
    skill = result.files["skills/reviewed-runbook/SKILL.md"].decode()

    assert "allowed-tools" not in skill
    assert "reviewed-projection-digest: " + RUNBOOK_DIGEST in skill
    assert "metadata:\n  boundaries: [filesystem_read_untrusted]" in skill
    assert "1. Inspect the request." in skill
    assert "### Detail" in skill
    assert "Do not include this section." not in skill
    assert "Introductory data" not in skill
    assert result.files["skills/reviewed-runbook/references/include.md"] == (
        b"This is supporting data for the reviewed runbook.\n"
    )
    assert "Untrusted included data" in skill


def test_generated_skills_pass_existing_deep_skill_lint(tmp_path: Path) -> None:
    result = _render(tmp_path / "source")
    root = tmp_path / "lint-root"
    skill_root = root / "packs" / "generated" / ".apm" / "skills"
    router_dir = skill_root / "rich-router"
    procedure_dir = skill_root / "reviewed-runbook"
    router_dir.mkdir(parents=True)
    procedure_dir.mkdir()
    (router_dir / "SKILL.md").write_bytes(result.files["SKILL.md"])
    (procedure_dir / "SKILL.md").write_bytes(result.files["skills/reviewed-runbook/SKILL.md"])

    diagnostics = lint_skill_spec(root, pack="generated")

    assert [diagnostic for diagnostic in diagnostics if diagnostic.severity.name == "ERROR"] == []


def test_references_preserve_canonical_bytes_and_unknown_extensions(
    tmp_path: Path,
) -> None:
    bundle = _copy_fixture(tmp_path)
    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert result.files["references/okf/concepts/runbook.md"] == (
        bundle / "concepts" / "runbook.md"
    ).read_bytes()
    assert result.files["references/okf/extensions/unknown.json"] == (
        bundle / "extensions" / "unknown.json"
    ).read_bytes()


def test_manifest_bytes_are_stable_strict_json(tmp_path: Path) -> None:
    result = _render(tmp_path)
    raw = result.files[".okf-generated.json"]
    manifest = json.loads(raw)

    assert raw.endswith(b"\n")
    assert b"NaN" not in raw
    assert manifest["profile"] == "agentbundle-okf/v1"
    assert manifest["managed"][0]["kind"] == "okf-router"
    assert manifest["managed"][1]["kind"] == "okf-index"
    assert manifest["managed"][1]["marker"] == (
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->"
    )
    assert manifest["managed"][2]["kind"] == "okf-procedure-skill"


def test_canonical_review_tuple_digest_vector_and_invalidation(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    digest = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md",),
    )

    assert digest == RUNBOOK_DIGEST

    (bundle / "guides" / "include.md").write_text("Changed include.\n", encoding="utf-8")
    changed = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md",),
    )
    assert changed != RUNBOOK_DIGEST


def test_declared_review_digest_must_match_candidate(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={
            "concepts/runbook.md": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF008"]
    assert result.files == {}
    assert result.review_candidates["concepts/runbook.md"] == RUNBOOK_DIGEST


@pytest.mark.parametrize("concept_type", ["Reference", "Note"])
def test_projected_procedure_requires_playbook_concept(
    tmp_path: Path,
    concept_type: str,
) -> None:
    bundle = _copy_fixture(tmp_path)
    concept = bundle / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "type: Playbook",
            f"type: {concept_type}",
        ),
        encoding="utf-8",
    )

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF007"]
    assert result.files == {}


@pytest.mark.parametrize(
    ("body", "expected_code"),
    [
        ("# Reviewed Runbook\n\n## Missing\n\nText.\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure\n\nOne.\n\n## Procedure\n\nTwo.\n", "OKF007"),
        ("# Reviewed Runbook\n\n```md\n## Procedure\ninside\n```\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure ##\n\nText.\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure\n\n", "OKF007"),
    ],
)
def test_instruction_heading_must_select_one_unfenced_nonempty_section(
    tmp_path: Path, body: str, expected_code: str
) -> None:
    bundle = _copy_fixture(tmp_path)
    concept = bundle / "concepts" / "runbook.md"
    frontmatter = concept.read_text(encoding="utf-8").split("---\n", 2)[1]
    concept.write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == [expected_code]


def test_strict_canonical_json_rejects_non_finite_values() -> None:
    assert canonical_json_bytes({"b": 1, "a": [True, None]}) == STRICT_JSON_VECTOR
    assert review_projection_digest.bytes_digest(STRICT_JSON_VECTOR) == STRICT_JSON_DIGEST
    with pytest.raises(ValueError):
        canonical_json_bytes({"bad": float("nan")})
