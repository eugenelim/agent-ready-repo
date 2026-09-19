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


# --- AC-0017: the paragraph budget, on both sides --------------------------


def test_da3_budget_holds_at_three_and_fires_at_four() -> None:
    gate = _load_gate()
    assert gate.count_sentences("One. Two. Three.") == 3
    assert gate.count_sentences("One. Two. Three. Four.") == 4


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
