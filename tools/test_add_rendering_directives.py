from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("add-rendering-directives.py")
SPEC = importlib.util.spec_from_file_location("add_rendering_directives", SCRIPT)
assert SPEC and SPEC.loader
rendering = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rendering)
ROOT = Path(__file__).resolve().parents[1]


def skill(body: str, *, newline: str = "\n") -> bytes:
    text = f"---\nname: sample\ndescription: Use when testing.\n---\n\n# Sample\n\n{body}"
    return text.replace("\n", newline).encode("utf-8")


def make_skill(root: Path, pack: str, name: str, data: bytes) -> Path:
    path = root / "packs" / pack / ".apm" / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    return path


def test_okf_generated_skills_use_the_exact_independent_contract() -> None:
    asset = (
        ROOT
        / "packs/catalogue-curation/.apm/skills/compile-okf/assets/output-rendering.md"
    ).read_text(encoding="utf-8")
    assert asset == f"## Output rendering\n\n{rendering.UNIVERSAL_BLOCK}\n"


def test_inserts_managed_block_before_existing_output_content() -> None:
    original = skill("## Output rendering\n\nKeep this custom rule.\n\n## Procedure\n\nDo work.\n")

    rendered = rendering.render_skill(original, ["table"])
    text = rendered.decode("utf-8")

    assert text.index(rendering.START_MARKER) < text.index("Keep this custom rule.")
    assert text.count(rendering.START_MARKER) == 1
    assert "Table — When presenting several items" in text


def test_creates_missing_section_before_first_procedural_h2() -> None:
    original = skill("An introduction.\n\n## Procedure\n\nDo work.\n")

    text = rendering.render_skill(original, []).decode("utf-8")

    assert text.index("## Output rendering") < text.index("## Procedure")
    assert rendering.UNIVERSAL_BLOCK.strip() in text


def test_replaces_only_stale_managed_content() -> None:
    original = skill(
        "## Output rendering\n\n"
        f"{rendering.START_MARKER}\nOld managed prose.\n{rendering.END_MARKER}\n\n"
        "Keep this custom rule.\n"
    )

    text = rendering.render_skill(original, []).decode("utf-8")

    assert "Old managed prose." not in text
    assert "Keep this custom rule." in text
    assert text.count(rendering.START_MARKER) == 1


def test_refreshes_shape_directives_without_duplicates() -> None:
    old_diff = rendering.LEGACY_DIRECTIVE_TEXTS[0]
    original = skill(
        "## Output rendering\n\n"
        f"{rendering.START_MARKER}\nOld managed prose.\n{rendering.END_MARKER}\n\n"
        f"{old_diff}\n\n{rendering.D['table']}\n\n"
        f"{old_diff}\n{rendering.D['table']}\n\n"
        "Keep this custom rule.\n\n"
        "## Procedure\n\nDo work.\n"
    )

    text = rendering.render_skill(original, ["diff", "table"]).decode("utf-8")

    assert old_diff not in text
    assert text.count(rendering.D["diff"]) == 1
    assert text.count(rendering.D["table"]) == 1
    assert "Keep this custom rule." in text
    assert "## Procedure" in text


def test_markerless_legacy_section_converges_in_one_pass() -> None:
    original = skill(
        "## Output rendering\n\n"
        f"{rendering.LEGACY_DIRECTIVE_TEXTS[0]}\n\n"
        f"{rendering.D['table']}\n\n"
        "Keep this custom rule.\n\n"
        "## Procedure\n\nDo work.\n"
    )

    first = rendering.render_skill(original, ["diff", "table"])
    second = rendering.render_skill(first, ["diff", "table"])
    text = first.decode("utf-8")

    assert first == second
    assert rendering.LEGACY_DIRECTIVE_TEXTS[0] not in text
    assert text.count(rendering.D["diff"]) == 1
    assert text.count(rendering.D["table"]) == 1
    assert "Keep this custom rule." in text
    assert "## Procedure" in text


@pytest.mark.parametrize(
    "body,reason",
    [
        ("## Output rendering\n\n## Output rendering\n", "duplicate-output-section"),
        ("## Output rendering\n\n<!-- agentbundle:output-rendering:start -->\n", "unmatched-marker"),
        (
            "## Output rendering\n\n"
            "<!-- agentbundle:output-rendering:start -->\n"
            "x\n<!-- agentbundle:output-rendering:end -->\n"
            "<!-- agentbundle:output-rendering:start -->\n"
            "y\n<!-- agentbundle:output-rendering:end -->\n",
            "duplicate-marker",
        ),
    ],
)
def test_rejects_ambiguous_structure(body: str, reason: str) -> None:
    with pytest.raises(rendering.RenderError, match=reason):
        rendering.render_skill(skill(body), [])


def test_rejects_malformed_frontmatter() -> None:
    with pytest.raises(rendering.RenderError, match="malformed-frontmatter"):
        rendering.render_skill(b"---\nname: sample\n", [])


def test_preserves_crlf_terminal_newline_and_mode(tmp_path: Path) -> None:
    source = make_skill(tmp_path, "alpha", "sample", skill("## Procedure\n", newline="\r\n"))
    source.chmod(0o640)

    summary = rendering.run(tmp_path, write=True)

    assert summary.changed == 1
    assert b"\r\n" in source.read_bytes()
    assert b"\n" not in source.read_bytes().replace(b"\r\n", b"")
    assert source.read_bytes().endswith(b"\r\n")
    assert source.stat().st_mode & 0o777 == 0o640


def test_discovers_only_canonical_pack_sources(tmp_path: Path) -> None:
    canonical = make_skill(tmp_path, "alpha", "sample", skill("## Procedure\n"))
    projected = tmp_path / ".agents" / "skills" / "sample" / "SKILL.md"
    projected.parent.mkdir(parents=True)
    projected.write_bytes(skill("## Procedure\n"))
    claude = tmp_path / ".claude" / "skills" / "sample" / "SKILL.md"
    claude.parent.mkdir(parents=True)
    claude.write_bytes(skill("## Procedure\n"))

    assert rendering.discover_skill_files(tmp_path) == [canonical]


def test_check_then_write_is_idempotent(tmp_path: Path) -> None:
    source = make_skill(tmp_path, "alpha", "sample", skill("## Procedure\n"))

    assert rendering.run(tmp_path, write=False).changed == 1
    assert rendering.run(tmp_path, write=True).changed == 1
    first = source.read_bytes()
    assert rendering.run(tmp_path, write=True).changed == 0
    assert rendering.run(tmp_path, write=False).changed == 0
    assert source.read_bytes() == first


def test_canonical_skills_have_no_duplicate_or_legacy_shape_directives() -> None:
    for source in rendering.discover_skill_files(ROOT):
        content = source.read_text(encoding="utf-8")
        for directive in rendering.D.values():
            assert content.count(directive) <= 1, source
        for directive in rendering.LEGACY_DIRECTIVE_TEXTS:
            assert directive not in content, source


def test_preflight_rejects_symlink_before_any_write(tmp_path: Path) -> None:
    first = make_skill(tmp_path, "alpha", "first", skill("## Procedure\n"))
    target = make_skill(tmp_path, "alpha", "target", skill("## Procedure\n"))
    linked = tmp_path / "packs" / "alpha" / ".apm" / "skills" / "linked"
    try:
        linked.symlink_to(target.parent, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")

    before = first.read_bytes()
    with pytest.raises(rendering.RenderError, match="unsafe-source"):
        rendering.run(tmp_path, write=True)
    assert first.read_bytes() == before


def test_preflight_rejects_broken_skill_link_before_any_write(tmp_path: Path) -> None:
    first = make_skill(tmp_path, "alpha", "first", skill("## Procedure\n"))
    linked = tmp_path / "packs" / "alpha" / ".apm" / "skills" / "linked" / "SKILL.md"
    linked.parent.mkdir(parents=True)
    try:
        linked.symlink_to("missing.md")
    except OSError:
        pytest.skip("symlinks unavailable")

    before = first.read_bytes()
    with pytest.raises(rendering.BatchRenderError) as captured:
        rendering.run(tmp_path, write=True)

    assert captured.value.issues == (
        ("packs/alpha/.apm/skills/linked/SKILL.md", "unsafe-source"),
    )
    assert first.read_bytes() == before


def test_guide_carries_the_exact_managed_block() -> None:
    root = SCRIPT.parent.parent
    guide = (root / "guides/_shared/reference/output-rendering.md").read_text(
        encoding="utf-8"
    )
    start = guide.index(rendering.START_MARKER)
    end = guide.index(rendering.END_MARKER) + len(rendering.END_MARKER)
    assert guide[start:end] == rendering.UNIVERSAL_BLOCK


def test_diff_directive_keeps_needed_rationale_and_matches_the_guide() -> None:
    guide = (ROOT / "guides/_shared/reference/output-rendering.md").read_text(
        encoding="utf-8"
    )

    assert "Keep any needed rationale outside the diff." in rendering.D["diff"]
    assert "Never describe the change" not in rendering.D["diff"]
    assert "Keep any needed rationale outside the diff." in guide


def test_managed_block_preserves_attention_and_thoroughness_rules() -> None:
    for phrase in (
        "everyday words",
        "before naming it",
        "numbered steps",
        "one load-bearing point",
        "Do needed arithmetic",
        "not the path taken",
        "never reduce the work",
        "without counting, converting, opening a file",
    ):
        assert phrase in rendering.UNIVERSAL_BLOCK
    assert "another skill" not in rendering.UNIVERSAL_BLOCK
    assert ".agents/rules" not in rendering.UNIVERSAL_BLOCK


def test_check_reports_each_missing_section_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    make_skill(tmp_path, "alpha", "one", skill("## Procedure\n"))
    make_skill(tmp_path, "beta", "two", skill("## Procedure\n"))
    monkeypatch.setattr(rendering, "ROOT", tmp_path)

    assert rendering.main(["--check"]) == 1

    output = capsys.readouterr().out
    assert "packs/alpha/.apm/skills/one/SKILL.md: missing-section" in output
    assert "packs/beta/.apm/skills/two/SKILL.md: missing-section" in output
    assert str(tmp_path) not in output


def test_check_distinguishes_missing_block_from_stale_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    make_skill(
        tmp_path,
        "alpha",
        "missing",
        skill("## Output rendering\n\nKeep this shape rule.\n"),
    )
    make_skill(
        tmp_path,
        "alpha",
        "stale",
        skill(
            "## Output rendering\n\n"
            f"{rendering.START_MARKER}\nOld text.\n{rendering.END_MARKER}\n"
        ),
    )
    monkeypatch.setattr(rendering, "ROOT", tmp_path)

    assert rendering.main(["--check"]) == 1

    output = capsys.readouterr().out
    assert "packs/alpha/.apm/skills/missing/SKILL.md: missing-managed-block" in output
    assert "packs/alpha/.apm/skills/stale/SKILL.md: stale" in output


def test_preflight_reports_all_malformed_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    make_skill(
        tmp_path,
        "alpha",
        "one",
        skill("## Output rendering\n\n## Output rendering\n"),
    )
    make_skill(
        tmp_path,
        "beta",
        "two",
        skill("## Output rendering\n\n## Output rendering\n"),
    )
    monkeypatch.setattr(rendering, "ROOT", tmp_path)

    assert rendering.main(["--write"]) == 2

    error = capsys.readouterr().err
    assert "packs/alpha/.apm/skills/one/SKILL.md: duplicate-output-section" in error
    assert "packs/beta/.apm/skills/two/SKILL.md: duplicate-output-section" in error
    assert str(tmp_path) not in error
