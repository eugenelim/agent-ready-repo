"""Construction tests for the DA3/DA10 document-architecture gate script.

Loads `check_document_architecture.py` by path, under a pack-unique module
name, matching `packs/architect/tests/skills/architect-assess/test_profile_repo.py:23`
(`packs/AGENTS.md` § Writing pack tests forbids a bare-name import of a
skill's `scripts/`, since several skills ship a same-named module).
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "architect-design"
SCRIPT_PATH = SKILL_DIR / "scripts" / "check_document_architecture.py"
FILE_SAFETY_PATH = SKILL_DIR / "scripts" / "file_safety.py"


def _load_gate() -> ModuleType:
    """Load the gate script from its repository path, never by bare import."""

    spec = importlib.util.spec_from_file_location("architect_design_gate_script", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["architect_design_gate_script"] = module
    spec.loader.exec_module(module)
    return module


def _module_imports(path: Path) -> set[str]:
    """Return the top-level module names *path* imports, read with `ast`."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module.split(".")[0])
    return modules


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        check=False,
    )


# --- AC-0001: loaded by path, under a pack-unique name --------------------


def test_gate_script_loads_by_path_under_a_pack_unique_module_name() -> None:
    gate = _load_gate()
    assert sys.modules["architect_design_gate_script"] is gate
    assert hasattr(gate, "count_sentences")
    assert hasattr(gate, "count_words")
    assert hasattr(gate, "main")


# stub: true — the red contract surface, before the parser exists.
def test_da3_reports_a_four_sentence_paragraph() -> None:
    gate = _load_gate()
    assert gate.count_sentences("One. Two. Three. Four.") == 4


# --- AC-0002 / AC-0077: standard-library-only imports ----------------------


def test_script_imports_are_stdlib_only_and_never_agentbundle() -> None:
    modules = _module_imports(SCRIPT_PATH)
    assert "agentbundle" not in modules
    allowed = set(sys.stdlib_module_names)
    assert modules <= allowed, modules - allowed


def test_sibling_helper_imports_are_stdlib_only() -> None:
    modules = _module_imports(FILE_SAFETY_PATH)
    allowed = set(sys.stdlib_module_names)
    assert modules <= allowed, modules - allowed


# --- AC-0073: byte identity lives in tests/roster, not here ----------------
# `tests/roster/test_architect_design_reviewer_projection.py` pins it
# (AC-0074); this file does not duplicate that assertion.


# --- AC-0075: a tampered sibling refuses through the script's own channel --


def _sabotage_absent(staged: Path, source: Path) -> None:
    (staged / "file_safety.py").unlink()


def _sabotage_symlink(staged: Path, source: Path) -> None:
    target = staged / "file_safety.py"
    target.unlink()
    target.symlink_to(source)


def _sabotage_truncated(staged: Path, source: Path) -> None:
    (staged / "file_safety.py").write_text("# partial\n", encoding="utf-8")


@pytest.mark.parametrize(
    "label, sabotage",
    [
        ("absent", _sabotage_absent),
        ("symlink", _sabotage_symlink),
        ("truncated", _sabotage_truncated),
    ],
)
def test_a_tampered_helper_sibling_refuses_through_the_declared_channel(
    tmp_path: Path, label: str, sabotage: Callable[[Path, Path], None]
) -> None:
    """Absent, symlinked and truncated mirrors all report as refusals, not tracebacks."""

    staged = tmp_path / label
    shutil.copytree(SCRIPT_PATH.parent, staged)
    sabotage(staged, FILE_SAFETY_PATH)
    proc = subprocess.run(
        [sys.executable, str(staged / SCRIPT_PATH.name), "--root", str(tmp_path), "placeholder.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2, f"{label}: accepted a tampered mirror:\n{proc.stdout}{proc.stderr}"
    assert proc.stderr.strip(), f"{label}: refused silently"
    assert "Traceback" not in proc.stderr, f"{label}: crashed:\n{proc.stderr}"


# --- AC-0009 / AC-0076: root canonicalized, path handed through unresolved -


def test_read_target_canonicalizes_a_symlinked_root(tmp_path: Path) -> None:
    gate = _load_gate()
    real_root = tmp_path / "real_root"
    real_root.mkdir()
    target = real_root / "doc.md"
    target.write_text("Hello there. It works well.\n", encoding="utf-8")
    symlinked_root = tmp_path / "alias_root"
    symlinked_root.symlink_to(real_root, target_is_directory=True)

    text = gate.read_target(symlinked_root, target, gate.MAX_BYTES)
    assert text == "Hello there. It works well.\n"


def test_read_target_hands_the_helper_an_unresolved_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resolving the path first would let a symlinked parent escape unseen."""

    gate = _load_gate()
    root = tmp_path / "root"
    real_dir = root / "real"
    real_dir.mkdir(parents=True)
    (real_dir / "doc.md").write_text("Hello there. It works.\n", encoding="utf-8")
    alias = root / "alias"
    alias.symlink_to(real_dir, target_is_directory=True)
    target = alias / "doc.md"

    seen: dict[str, Path] = {}
    safety = gate.file_safety()
    original = safety.read_confined_regular_file

    def _recording(root_arg: Path, path_arg: Path, *, max_bytes: int | None = None) -> bytes:
        seen["path"] = path_arg
        return original(root_arg, path_arg, max_bytes=max_bytes)

    monkeypatch.setattr(safety, "read_confined_regular_file", _recording)
    with pytest.raises(gate.Refusal):
        gate.read_target(root, target, gate.MAX_BYTES)
    assert seen["path"] == target, "the wrapper resolved the path before delegating"


# --- AC-0010, AC-0011, AC-0012, AC-0013: the refusal table -----------------


def test_read_target_refuses_a_symlinked_parent_leaving_the_root(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "doc.md").write_text("Hello. Escaped.\n", encoding="utf-8")
    escape = root / "escape"
    escape.symlink_to(outside, target_is_directory=True)
    target = escape / "doc.md"

    with pytest.raises(gate.Refusal) as excinfo:
        gate.read_target(root, target, gate.MAX_BYTES)
    safety = gate.file_safety()
    if safety._supports_descriptor_walk():
        assert excinfo.value.reason == "directory boundary cannot be opened safely: escape/doc.md"
    else:
        assert excinfo.value.reason


def test_read_target_refuses_non_regular_and_multiply_linked_entries(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()

    directory = root / "adir"
    directory.mkdir()
    with pytest.raises(gate.Refusal):
        gate.read_target(root, directory, gate.MAX_BYTES)

    fifo = root / "afifo.md"
    os.mkfifo(fifo)
    with pytest.raises(gate.Refusal):
        gate.read_target(root, fifo, gate.MAX_BYTES)

    outside = tmp_path / "outside.md"
    outside.write_text("secret\n", encoding="utf-8")
    link = root / "alink.md"
    link.symlink_to(outside)
    with pytest.raises(gate.Refusal):
        gate.read_target(root, link, gate.MAX_BYTES)

    original = root / "original.md"
    original.write_text("Hello there.\n", encoding="utf-8")
    hardlinked = root / "hardlinked.md"
    os.link(original, hardlinked)
    with pytest.raises(gate.Refusal):
        gate.read_target(root, hardlinked, gate.MAX_BYTES)


def test_read_target_enforces_the_byte_bound(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()

    under = root / "under.md"
    under.write_bytes(b"a" * (gate.MAX_BYTES - 1))
    text = gate.read_target(root, under, gate.MAX_BYTES)
    assert len(text) == gate.MAX_BYTES - 1

    over = root / "over.md"
    over.write_bytes(b"a" * (gate.MAX_BYTES + 1))
    with pytest.raises(gate.Refusal):
        gate.read_target(root, over, gate.MAX_BYTES)


def test_read_target_refuses_when_the_root_is_a_symlink_loop(tmp_path: Path) -> None:
    """`Path.resolve()` raises `RuntimeError`, not `OSError`, on a symlink loop."""

    gate = _load_gate()
    loop_root = tmp_path / "loop_root"
    loop_root.symlink_to(loop_root)
    target = loop_root / "doc.md"
    with pytest.raises(gate.Refusal):
        gate.read_target(loop_root, target, gate.MAX_BYTES)


def test_read_target_refuses_a_path_outside_the_root(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("Hello there.\n", encoding="utf-8")
    with pytest.raises(gate.Refusal):
        gate.read_target(root, outside, gate.MAX_BYTES)


def test_read_target_refuses_non_utf8_bytes(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    target = root / "binary.md"
    target.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(gate.Refusal) as excinfo:
        gate.read_target(root, target, gate.MAX_BYTES)
    assert "UTF-8" in excinfo.value.reason


@pytest.mark.skipif(
    os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="root ignores directory permission bits",
)
def test_read_target_refuses_a_permission_error(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    blocked_dir = root / "blocked"
    blocked_dir.mkdir()
    target = blocked_dir / "doc.md"
    target.write_text("Hello there.\n", encoding="utf-8")
    blocked_dir.chmod(0o000)
    try:
        with pytest.raises(gate.Refusal):
            gate.read_target(root, target, gate.MAX_BYTES)
    finally:
        blocked_dir.chmod(0o755)


# --- AC-0007: refusal carries and renders the path and the reason ----------


def test_refusal_render_carries_the_path_and_reason() -> None:
    gate = _load_gate()
    refusal = gate.Refusal("weird/path.md", "some reason")
    rendered = refusal.render()
    assert "weird/path.md" in rendered
    assert "some reason" in rendered


# --- AC-0003: streams reconfigured before the first write ------------------


def test_main_reconfigures_streams_before_any_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gate = _load_gate()

    class _Recorder:
        def __init__(self) -> None:
            self.first_call: str | None = None

        def reconfigure(self, **kwargs: object) -> None:
            if self.first_call is None:
                self.first_call = "reconfigure"

        def write(self, data: str) -> int:
            if self.first_call is None:
                self.first_call = "write"
            return len(data)

        def flush(self) -> None:
            pass

    out = _Recorder()
    err = _Recorder()
    monkeypatch.setattr(gate.sys, "stdout", out)
    monkeypatch.setattr(gate.sys, "stderr", err)
    root = tmp_path / "root"
    root.mkdir()
    gate.main(["--root", str(root), str(root / "missing.md")])
    assert out.first_call == "reconfigure"
    assert err.first_call == "reconfigure"


# --- AC-0004, AC-0005, AC-0006: CLI exit codes -----------------------------


def test_cli_exits_zero_with_no_finding(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    doc = root / "doc.md"
    doc.write_text("Short prose. Two sentences here.\n", encoding="utf-8")
    proc = _run_cli("--root", str(root), str(doc))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout == ""


def test_cli_exits_one_with_a_finding(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    doc = root / "doc.md"
    doc.write_text("One. Two. Three. Four.\n", encoding="utf-8")
    proc = _run_cli("--root", str(root), str(doc))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "DA3" in proc.stdout


def test_cli_exits_two_on_a_refusal(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    proc = _run_cli("--root", str(root), str(root / "missing.md"))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert proc.stderr


def test_cli_a_refusal_dominates_a_finding_across_targets(tmp_path: Path) -> None:
    """2 dominates 1: a refusal on one target still reports the other's finding."""

    root = tmp_path / "root"
    root.mkdir()
    finding_doc = root / "finding.md"
    finding_doc.write_text("One. Two. Three. Four.\n", encoding="utf-8")
    missing = root / "missing.md"
    proc = _run_cli("--root", str(root), str(finding_doc), str(missing))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "DA3" in proc.stdout, "the finding on the readable target must still be reported"
    assert "refused" in proc.stderr


# --- AC-0009 / AC-0076: `--root .` plus a relative target is a real result,
#     not a refusal — the documented adopter/CI invocation ------------------


def test_cli_accepts_a_relative_root_and_a_relative_target(tmp_path: Path) -> None:
    """`--root .` is the documented CLI invocation; it must not refuse every target."""

    doc = tmp_path / "doc.md"
    doc.write_text("Short prose. Two sentences here.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", ".", "doc.md"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_read_target_joins_a_relative_target_onto_a_relative_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = _load_gate()
    (tmp_path / "doc.md").write_text("Hello there. It works.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    text = gate.read_target(Path(), Path("doc.md"), gate.MAX_BYTES)
    assert text == "Hello there. It works.\n"


def test_read_target_confines_an_absolute_target_through_a_symlinked_root(
    tmp_path: Path,
) -> None:
    """Same defect class as the relative-root case: root resolves, target does not."""

    gate = _load_gate()
    real_root = tmp_path / "real_root"
    real_root.mkdir()
    (real_root / "doc.md").write_text("Hello there. It works well.\n", encoding="utf-8")
    alias_root = tmp_path / "alias_root"
    alias_root.symlink_to(real_root, target_is_directory=True)

    text = gate.read_target(alias_root, alias_root / "doc.md", gate.MAX_BYTES)
    assert text == "Hello there. It works well.\n"


# --- AC-0008: --root is required -------------------------------------------


def test_parser_requires_root() -> None:
    gate = _load_gate()
    with pytest.raises(SystemExit):
        gate._parser().parse_args(["doc.md"])


# --- AC-0014: no catastrophic-backtracking shape in the sentence pattern ---


def test_sentence_boundary_pattern_has_no_catastrophic_backtracking_shape() -> None:
    gate = _load_gate()
    pattern = gate._SENTENCE_BOUNDARY_PATTERN.pattern
    assert not re.search(r"\([^()]*[+*][^()]*\)[+*]", pattern), pattern
    assert not re.search(r"\([^()]*\|[^()]*\)[+*]", pattern), pattern


# --- AC-0015: hostile paths are escaped, one line per finding -------------


def test_finding_and_refusal_rendering_escape_hostile_paths() -> None:
    gate = _load_gate()
    hostile = "evil\n\x1b[31mFAKE\x1b[0m.md"

    finding = gate.Finding("DA3", hostile, "paragraph of 4 sentences (budget 3)", line=1)
    rendered_finding = finding.render()
    assert "\n" not in rendered_finding
    assert "\x1b" not in rendered_finding

    refusal = gate.Refusal(hostile, "some reason")
    rendered_refusal = refusal.render()
    assert "\n" not in rendered_refusal
    assert "\x1b" not in rendered_refusal


def test_a_real_refusal_reason_escapes_a_hostile_filename(tmp_path: Path) -> None:
    """A benign-reason `Refusal` cannot catch this: `reason` embeds the path too.

    `read_target` builds its reason from `str(exc)`, and the vendored helper's
    exception text embeds the confined-relative path — so a hostile on-disk
    filename must not leak a raw control byte through `reason`, not only
    through `path`.
    """
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    hostile_name = "evil\n\x1b[31mFAKE\x1b[0m.md"
    hostile = root / hostile_name
    os.mkfifo(hostile)  # not a regular file: the refusal reason embeds its name
    with pytest.raises(gate.Refusal) as excinfo:
        gate.read_target(root, hostile, gate.MAX_BYTES)
    assert hostile_name in excinfo.value.reason, "the reason must still name the file"
    rendered = excinfo.value.render()
    assert "\n" not in rendered
    assert "\x1b" not in rendered


# --- AC-0017: the paragraph budget, on both sides --------------------------


def test_da3_budget_holds_at_three_and_fires_at_four() -> None:
    gate = _load_gate()
    assert gate.count_sentences("One. Two. Three.") == 3
    assert gate.count_sentences("One. Two. Three. Four.") == 4


# --- AC-0017: a sentence-initial trigger is not only an ASCII capital ------
# The old pattern only fired on `[A-Z]`, so a paragraph opening every
# sentence with inline code, a digit, a quote, or an emphasis marker
# undercounted and passed a budget it should have failed.


def test_da3_counts_a_backtick_initial_sentence() -> None:
    gate = _load_gate()
    assert (
        gate.count_sentences(
            "One thing here. `DA1` is one. `DA2` is two. `DA3` is three."
        )
        == 4
    )


def test_da3_counts_a_digit_initial_sentence() -> None:
    gate = _load_gate()
    assert (
        gate.count_sentences(
            "One thing. 2 things happen. 3 more things. 4 more things."
        )
        == 4
    )


def test_da3_counts_a_quote_initial_sentence() -> None:
    gate = _load_gate()
    assert (
        gate.count_sentences(
            "First. “Quoted” next. **Bold** next. Fourth one."
        )
        == 4
    )


def test_da3_counts_a_glyph_initial_sentence() -> None:
    """An emoji and a Latin-1 accented capital both open a new sentence."""

    gate = _load_gate()
    assert gate.count_sentences("First one. \U0001f600 Second one.") == 2
    assert gate.count_sentences("First one. École is next.") == 2


def test_da3_does_not_split_an_inline_lettered_label() -> None:
    """A lone-letter label like `a.` attaches to what follows, not a sentence of its own."""

    gate = _load_gate()
    assert (
        gate.count_sentences(
            "a. `DA1` is one. `DA2` is two. `DA3` is three. `DA4` is four."
        )
        == 4
    )


# --- AC-0019: DA3 excludes frontmatter, comments, fences, tables, lists,
#     block quotes and headings from prose ----------------------------------


def test_da3_excludes_non_prose_constructs() -> None:
    gate = _load_gate()
    text = (
        "---\n"
        "title: x\n"
        "---\n"
        "\n"
        "<!-- A note. With two. Three sentences. Four here. -->\n"
        "\n"
        "# Heading one\n"
        "\n"
        "```text\n"
        "One. Two. Three. Four.\n"
        "```\n"
        "\n"
        "| a | b |\n"
        "| - | - |\n"
        "\n"
        "- List item. Two. Three. Four.\n"
        "\n"
        "> Quote. Two. Three. Four.\n"
        "\n"
        "Real prose. Two. Three.\n"
    )
    stripped = gate.strip_excluded(text)
    paragraphs = list(gate.prose_paragraphs(stripped))
    assert len(paragraphs) == 1
    _, prose = paragraphs[0]
    assert prose == "Real prose. Two. Three."


def test_da3_treats_a_list_continuation_line_as_still_excluded() -> None:
    """A wrapped continuation line carries no marker of its own but is not prose."""

    gate = _load_gate()
    text = (
        "- Item one continues\n"
        "  onto a wrapped line that is not a new list item.\n"
        "- Item two.\n"
    )
    assert list(gate.prose_paragraphs(text)) == []


def test_da3_treats_a_pipe_row_inside_a_fence_as_still_fenced() -> None:
    """A fenced block's pipe-delimited line is not read as a table row."""

    gate = _load_gate()
    text = "```text\n| not | a | table |\n```\n\nReal prose. Two sentences.\n"
    paragraphs = list(gate.prose_paragraphs(text))
    assert len(paragraphs) == 1
    assert paragraphs[0][1] == "Real prose. Two sentences."


# --- AC-0020: abbreviations and decimals do not split a sentence ----------


def test_count_sentences_does_not_split_on_abbreviations_or_decimals() -> None:
    gate = _load_gate()
    paragraph = (
        "We ship v3.14 today. It handles e.g. retries, i.e. backoff, etc. "
        "properly, vs. the old build."
    )
    assert gate.count_sentences(paragraph) == 2


# --- AC-0021: a heading directly above wrapped prose ----------------------


def test_heading_above_wrapped_prose_yields_one_paragraph() -> None:
    gate = _load_gate()
    text = "## Heading\nWrapped prose line one\nline two continues.\n"
    paragraphs = list(gate.prose_paragraphs(text))
    assert len(paragraphs) == 1
    start_line, prose = paragraphs[0]
    assert start_line == 2
    assert prose == "Wrapped prose line one\nline two continues."


# --- AC-0022: the finding carries file, line and sentence count -----------


def test_finding_render_carries_path_line_and_count() -> None:
    gate = _load_gate()
    finding = gate.Finding("DA3", "docs/example.md", "paragraph of 4 sentences (budget 3)", line=12)
    rendered = finding.render()
    assert "docs/example.md" in rendered
    assert ":12:" in rendered
    assert "4 sentences" in rendered


def test_evaluate_target_reports_the_da3_finding_with_line_and_count(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    doc = root / "doc.md"
    doc.write_text("# Title\n\nOne. Two. Three. Four.\n", encoding="utf-8")
    findings = gate.evaluate_target(root, doc)
    da3 = [finding for finding in findings if finding.gate == "DA3"]
    assert len(da3) == 1
    assert da3[0].line == 3
    assert "4 sentences" in da3[0].message


# --- AC-0023: the word count is pinned at the bound and one over ----------


def test_count_words_pins_the_da10_bound() -> None:
    gate = _load_gate()
    at_bound = " ".join(f"word{i}" for i in range(gate.WORD_BOUND))
    over_bound = at_bound + " oneextra"
    assert gate.count_words(at_bound) == gate.WORD_BOUND
    assert gate.count_words(over_bound) == gate.WORD_BOUND + 1


def test_evaluate_target_reports_da10_only_over_the_bound(tmp_path: Path) -> None:
    gate = _load_gate()
    root = tmp_path / "root"
    root.mkdir()
    at_bound_doc = root / "at_bound.md"
    at_bound_doc.write_text(" ".join(f"word{i}" for i in range(gate.WORD_BOUND)), encoding="utf-8")
    over_bound_doc = root / "over_bound.md"
    over_bound_doc.write_text(
        " ".join(f"word{i}" for i in range(gate.WORD_BOUND + 1)), encoding="utf-8"
    )

    at_bound_findings = [f for f in gate.evaluate_target(root, at_bound_doc) if f.gate == "DA10"]
    over_bound_findings = [f for f in gate.evaluate_target(root, over_bound_doc) if f.gate == "DA10"]
    assert at_bound_findings == []
    assert len(over_bound_findings) == 1
    assert f"{gate.WORD_BOUND + 1} words" in over_bound_findings[0].message


# --- AC-0016: the skill states the agent does not invoke the script -------


def test_skill_states_the_agent_does_not_invoke_the_gate_script() -> None:
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "check_document_architecture.py" in skill_text
    assert "does not invoke" in skill_text
    assert "human author" in skill_text and "adopter" in skill_text


# The sentence-initial rule is stated as "any non-space opens a sentence",
# with the non-boundaries neutralised by masking beforehand. These two tables
# are the intent: the first says what MUST register a boundary, the second
# what must NOT. An enumerated allowlist of opening characters was tried and
# withdrawn -- its holes (a markdown link, a parenthesis, an underscore, a
# non-Latin capital) each silently dropped a boundary, which is the
# under-count DA3 exists to catch.

_MUST_SPLIT = (
    ("markdown link", "One. [Two](x) here. [Three](x) here. [Four](x) here."),
    ("parenthesis", "One. (Two) here. (Three) here. (Four) here."),
    ("underscore emphasis", "One. _Two_ here. _Three_ here. _Four_ here."),
    ("en dash", "One. – Two here. – Three here. – Four here."),
    ("cyrillic capital", "One. Аb cd. Бb cd. Вb cd."),
    ("greek capital", "One. Αb cd. Βb cd. Γb cd."),
    ("contraction", "It works. It doesn't. Third one here. Fourth one here."),
    ("possessive", "Read it. That is the reviewer's. Third here. Fourth here."),
    ("single-letter name", "We chose X over Y. It says so. A third. A fourth."),
)

_MUST_NOT_SPLIT = (
    ("decimal", "Latency is 1.5 ms. That is fine.", 2),
    ("e.g.", "See e.g. the model. It holds.", 2),
    ("i.e. and etc.", "Use i.e. this, etc. and stop. Next one.", 2),
    ("version string", "Use v1.2.3 here. Done.", 2),
    ("lowercase label", "a. `DA1` one. `DA2` two. `DA3` three. `DA4` four.", 4),
)


@pytest.mark.parametrize("label,paragraph", _MUST_SPLIT, ids=[c[0] for c in _MUST_SPLIT])
def test_da3_registers_a_boundary_whatever_opens_the_next_sentence(
    label: str, paragraph: str
) -> None:
    gate = _load_gate()
    assert gate.count_sentences(paragraph) == 4, label


@pytest.mark.parametrize(
    "label,paragraph,expected",
    _MUST_NOT_SPLIT,
    ids=[c[0] for c in _MUST_NOT_SPLIT],
)
def test_da3_does_not_register_a_boundary_on_a_masked_period(
    label: str, paragraph: str, expected: int
) -> None:
    gate = _load_gate()
    assert gate.count_sentences(paragraph) == expected, label


# The uppercase-lone-letter tradeoff has a cost as well as a benefit, and the
# cost belongs in a table too: masking an uppercase `Y.` dropped a real
# boundary, so it is no longer masked, and a genuine initial now over-counts.
# Pinned so a future change to _INITIAL_PATTERN has to re-decide it rather
# than move it silently.
_MUST_OVERCOUNT = (
    ("initial", "J. Smith said. Second. Third. Fourth.", 5),
)


@pytest.mark.parametrize(
    "label,paragraph,expected",
    _MUST_OVERCOUNT,
    ids=[c[0] for c in _MUST_OVERCOUNT],
)
def test_da3_over_counts_a_genuine_initial_as_an_accepted_tradeoff(
    label: str, paragraph: str, expected: int
) -> None:
    gate = _load_gate()
    assert gate.count_sentences(paragraph) == expected, label


# A sentence boundary has a CLOSING side as well as an opening one, and only
# the opening side was ever tested. Every case in `_MUST_SPLIT` and
# `_MUST_NOT_SPLIT` above puts whitespace immediately after the terminator,
# so the closing side is unreachable by that whole table rather than merely
# under-covered by it -- which is how a paragraph like `**One.** Two. Three.
# Four.` read as three sentences through a fully green suite. Bold lead-ins
# are house style in the documents this skill ships, so a delimiter-heavy
# paragraph was very nearly invisible to `DA3`.
#
# Each row carries its own `direction`, and the test asserts all four
# directions are present. An over-count scan cannot find an under-count, so
# the table is built to make a one-directional revision of it fail rather
# than pass quietly:
#
#   `split`     -- the boundary must register through the delimiters.
#   `keep`      -- a masked period must still not split.
#   `overcount` -- a cost the counter knowingly accepts.
#   `residual`  -- a known wrong answer, pinned so it stays a decision.
_DELIMITED_BOUNDARY_CASES = (
    ("split", "bold lead-in", "**One.** Two. Three. Four.", 4),
    ("split", "italic span", "One. *Two.* Three. Four.", 4),
    ("split", "underscore emphasis", "One. _Two._ Three. Four.", 4),
    ("split", "inline code", "One. Two is `it.` Three. Four.", 4),
    ("split", "straight double quote", 'One. He said "go." Three. Four.', 4),
    ("split", "curly double quote", "One. He said “go.” Three. Four.", 4),
    ("split", "curly single quote", "One. He said ‘go.’ Three. Four.", 4),
    ("split", "guillemet", "One. Il a dit «va.» Three. Four.", 4),
    ("split", "parenthesis", "One. (An aside.) Three. Four.", 4),
    ("split", "bracket", "One. [An aside.] Three. Four.", 4),
    ("split", "brace", "One. {An aside.} Three. Four.", 4),
    ("split", "nested delimiters", 'One. (He said "go.") Three. Four.', 4),
    ("split", "exclamation in bold", "**Stop!** Two. Three. Four.", 4),
    ("split", "question in bold", "**Why?** Two. Three. Four.", 4),
    ("split", "strikethrough", "~~One.~~ Two. Three. Four.", 4),
    ("split", "CJK corner bracket", "One. He said 「Go.」 Three. Four.", 4),
    ("split", "angle bracket", "One. 〈Two.〉 Three. Four.", 4),
    # The severity case: three delimited sentences collapsed into one.
    ("split", "every sentence delimited", "**Bold.** *Ital.* `Code.` Four.", 4),
    ("keep", "enumeration label in code", "Set `a.` then continue.", 1),
    ("keep", "decimal", "Latency is 1.5 ms. That is fine.", 2),
    ("keep", "abbreviation inside a quote", 'He wrote "e.g. this" today. Next.', 2),
    ("keep", "ellipsis", "Standards... live on. Next one.", 2),
    ("keep", "lowercase label", "a. `DA1` one. `DA2` two. `DA3` three. `DA4` four.", 4),
    ("keep", "contraction", "It works. It doesn't. Third one here. Fourth here.", 4),
    ("keep", "possessive", "Read it. That is the reviewer's. Third here. Fourth here.", 4),
    # A destination whose dots are interior is unaffected: the terminator has
    # to be the LAST character before the `)` for the closer run to reach it.
    ("keep", "link destination with dots inside",
     "See [api](https://x.test/v1.2/a?q=1) first. Then go.", 2),
    # The over-counts the source names as accepted, grouped by reason rather
    # than counted — a stated count goes stale the next time a row is added.
    # This one is prose: masking an uppercase lone letter dropped a real
    # boundary, so a genuine initial is counted twice instead.
    ("overcount", "genuine initial", "J. Smith said. Second. Third. Fourth.", 5),
    # These two are markup rather than prose. The fence cannot reach a
    # rendered paragraph; the comment close reaches only malformed source,
    # since the stripping pass removes a complete `<!-- ... -->` span and an
    # orphan `-->` survives it.
    ("overcount", "Starlight fence", "Prose ends here.\n:::note", 2),
    ("overcount", "unstripped comment close", "Prose ends here.\n--> trailing", 2),
    # This one reaches real prose, unlike the two above, and the shipped
    # counter answered it correctly. It is accepted rather than fixed: the
    # alternative masks what a code span contains, which stops counting a
    # span that IS a sentence and trades a visible over-count for a silent
    # under-count. Pinned so the trade stays a decision.
    ("overcount", "terminator inside a code span", "Use the pattern `foo.*` here. Next one.", 3),
    # `!` was never only a terminator: "Compute n! before allocation." already
    # over-counted, because the `!` was followed by a space. Bracketing used to
    # hide that and no longer does. Same accepted class, one more syntax.
    ("overcount", "bracketed factorial", "Compute ⟨n!⟩ first. Then record it.", 3),
    # All three delimited-token rows count one more than they did before the
    # closer tolerance, so all three regress on these exact inputs. What is
    # different here is the CLASS: an unbracketed factorial already
    # over-counted, so that one was a hidden instance of a live class, while
    # a URL ending in a terminator was counted correctly before and is not.
    # Masking a destination needs real Markdown scanning, and the source says
    # why a regex for it costs more than the over-count it removes.
    ("overcount", "link destination ending in a terminator",
     "Read [search](https://example.test/s?) before rollout. Then deploy.", 3),
    # The irreducible residual. A one-letter sentence end behind a delimiter
    # and an enumeration label behind one are the same shape; only what
    # follows separates them, and the mask cannot read that. Splitting here
    # would break the `keep` row above, so this row stays wrong on purpose.
    # The shipped counter answered this one wrongly too, so nothing regressed.
    ("residual", "one-letter end behind a delimiter", "One. Two is `x.` Three. Four.", 3),
    # An ASCII `>` closer, excluded on a measured trade rather than missed:
    # admitting it fixes this row and breaks two autolink rows, which design
    # documents carry far more often than an angle-wrapped sentence. The
    # source records the measurement. Pinned so the trade stays a decision.
    ("residual", "ASCII angle bracket", "One. <Two.> Three. Four.", 3),
)


@pytest.mark.parametrize(
    "direction,label,paragraph,expected",
    _DELIMITED_BOUNDARY_CASES,
    ids=[f"{c[0]}-{c[1]}" for c in _DELIMITED_BOUNDARY_CASES],
)
def test_da3_counts_across_a_closing_delimiter(
    direction: str, label: str, paragraph: str, expected: int
) -> None:
    gate = _load_gate()
    assert gate.count_sentences(paragraph) == expected, (direction, label)


def _rows_missing_their_expectation(gate: ModuleType) -> set[str]:
    """Return the label of every row whose count differs from its pin.

    Not the same as "every row *gate* answers wrongly": the `overcount` and
    `residual` rows pin answers the source calls wrong on purpose, so they
    are absent from this set while `gate` is behaving as shipped.
    """
    return {
        label
        for _, label, paragraph, expected in _DELIMITED_BOUNDARY_CASES
        if gate.count_sentences(paragraph) != expected
    }


def test_the_delimiter_table_covers_both_directions() -> None:
    """A table that only ever grew in one direction is the original defect.

    The under-count survived a green suite not because the suite only looked
    for over-counts -- `_MUST_SPLIT` above requires boundaries to register --
    but because no case in it put anything between the terminator and the
    whitespace, so the closing side was unreachable from every direction the
    table already covered. Asserting the set of directions -- rather than a
    row count, which upstream churn breaks -- keeps a later revision from
    narrowing this back to a single-direction scan.
    """
    directions = {case[0] for case in _DELIMITED_BOUNDARY_CASES}
    assert directions == {"split", "keep", "overcount", "residual"}


def test_reverting_either_half_of_the_closer_tolerance_reds_this_table() -> None:
    """Both patterns are load-bearing, and the table proves it on each one.

    The direction labels above are only labels: a later edit could keep four
    rows, tag one with each direction, and satisfy that assertion while
    deleting every row that can fail. This is the control with teeth. It
    reverts each half of the closer tolerance independently and asserts the
    table catches each -- so the table cannot be gutted without one of these
    two reversions going quiet. What they preserve is one load-bearing
    witness for each half, not the table's breadth -- a table cut down to
    one row per direction would still satisfy both. Each reverted form keeps
    the `(?<![.!?])`
    anchor, which the historical line did not carry: the anchor is a separate
    cost fix, and holding it constant is what isolates the closer tolerance as
    the only variable.

    Reverting the boundary alone restores the under-count. Reverting only the
    lone-letter mask, with the boundary left tolerant, produces the
    *over-count* on an inline `a.` label instead: that asymmetry is why the
    two patterns cannot be changed one at a time.
    """
    pre_closer_boundary = re.compile(r"(?<![.!?])[.!?]+(?=\s+\S)")
    pre_closer_initial = re.compile(r"(?<![A-Za-z0-9'’ʼ])[a-z]\.(?=\s)")

    assert _rows_missing_their_expectation(_load_gate()) == set()

    boundary_reverted = _load_gate()
    boundary_reverted._SENTENCE_BOUNDARY_PATTERN = pre_closer_boundary
    broken_by_boundary = _rows_missing_their_expectation(boundary_reverted)
    assert "bold lead-in" in broken_by_boundary
    assert "every sentence delimited" in broken_by_boundary

    mask_reverted = _load_gate()
    mask_reverted._INITIAL_PATTERN = pre_closer_initial
    broken_by_mask = _rows_missing_their_expectation(mask_reverted)
    assert "enumeration label in code" in broken_by_mask, (
        "the mask half must be load-bearing on its own"
    )


def test_the_closer_literal_still_matches_the_categories_it_claims() -> None:
    """The hand-written closer set is regenerated here rather than trusted.

    The source writes the set out instead of sweeping `unicodedata` at
    import, because that would rebuild, on every invocation, a set that
    changes only when Unicode does.
    A written-out set drifts as Unicode adds characters, and nothing else
    would notice, so this derives it and compares.
    """
    gate = _load_gate()
    derived = {
        chr(code)
        for code in range(0x110000)
        if unicodedata.category(chr(code)) in {"Pe", "Pf"}
    } | set("*_`~\"'")
    assert set(gate._CLOSING_CHARACTERS) == derived


def test_the_boundary_pattern_is_linear_in_a_run_of_terminators() -> None:
    """A run of terminators with no whitespace must not backtrack quadratically.

    The shape grep above reads the pattern's text and cannot see cost. This
    reads cost. Without the `(?<![.!?])` anchor the engine retries the run
    from every position inside it and rescans the closer run each time. Over
    a fourfold input, linear growth predicts about 4x and quadratic about
    16x, so a bound of 8x sits between the two classes over that range. That
    bound is all this test enforces: it measures only the shipped pattern at
    two sizes and passes any ratio under 8x, which separates this pattern
    from the known unanchored one over the sampled range. It does not prove
    linearity, and a curve whose quadratic term only dominates later would
    pass. Asserted as a ratio between two sizes rather than an absolute
    duration, so a slow machine does not red it.
    """
    gate = _load_gate()

    def elapsed(size: int) -> float:
        hostile = "x " + "!" * size + ")" * size
        start = time.perf_counter()
        gate.count_sentences(hostile)
        return time.perf_counter() - start

    # Warm the engine so the first call's setup does not land in a sample.
    elapsed(64)
    small = min(elapsed(400) for _ in range(5))
    large = min(elapsed(1600) for _ in range(5))
    # Four times the input. Linear predicts ~4x; quadratic predicts ~16x.
    assert large < small * 8, (small, large)
