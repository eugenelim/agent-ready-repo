"""Behavior and security tests for the new-rfc skill's `rfc.py` script.

Each test works on a fresh copy of the script and its helper in a temporary
folder, so the default RFC folder (the script's own) is disposable. The git
seam is replaced everywhere; only one test spawns an interpreter.
"""

from __future__ import annotations

import ast
import datetime
import importlib.util
import itertools
import os
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

sys.dont_write_bytecode = True

SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/scripts"
SECTIONS = (
    "Summary",
    "Motivation",
    "Proposal",
    "Costs and what could go wrong",
    "Alternatives",
    "How we will know it works",
)
TEMPLATE = (
    "# RFC-NNNN: <short title>\n\n"
    "<!-- guidance comment -->\n\n"
    "- **Status:** Draft\n"
    "- **Author:** <account-handle>\n"
    "- **Date opened:** YYYY-MM-DD\n"
    "- **Date closed:**\n\n"
    + "".join(f"## {name}\n\n<!-- text -->\n\n" for name in SECTIONS)
)
_COUNTER = itertools.count()


def rfc_text(status: str = "Draft", skip: str = "", filler: str = "", title: str = "RFC-0001: T") -> str:
    """A well-formed RFC body, optionally missing one section or carrying filler."""
    parts = [f"# {title}\n\n- **Status:** {status}\n- **Author:** someone\n\n"]
    for name in SECTIONS:
        if name != skip:
            parts.append(f"## {name}\n\nbody\n\n")
    parts.append(filler)
    return "".join(parts)


class Rig:
    """A script folder copy with the module loaded from it and a captured console."""

    def __init__(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        self.dir = tmp_path / "docs" / "rfc"
        self.dir.mkdir(parents=True)
        for name in ("rfc.py", "file_safety.py"):
            shutil.copy2(SKILL_SCRIPTS / name, self.dir / name)
        (self.dir / "template.md.tmpl").write_text(TEMPLATE, encoding="utf-8")
        self.capsys = capsys
        self.mod = self.load(self.dir)

    @staticmethod
    def load(script_dir: Path, stub: bool = True) -> Any:
        """Load rfc.py under a pack-and-skill-specific name."""
        name = f"_repo_governance_new_rfc_rfc_{next(_COUNTER)}"
        spec = importlib.util.spec_from_file_location(name, script_dir / "rfc.py")
        assert spec is not None and spec.loader is not None
        module: Any = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

        def no_git(*_: Any) -> None:
            raise AssertionError("git must not run")

        if stub:
            module._spawn = no_git
            module.remote_names = lambda: None
        return module

    def run(self, *argv: str) -> tuple[int, str, str]:
        """Run main(argv) and return exit code, stdout and stderr."""
        self.capsys.readouterr()
        code = self.mod.main(list(argv))
        out = self.capsys.readouterr()
        return code, out.out, out.err

    def put(self, name: str, text: str = "", folder: Path | None = None) -> Path:
        path = (folder or self.dir) / name
        path.write_text(text or rfc_text(), encoding="utf-8")
        return path

    def snapshot(self, folder: Path | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for p in sorted((folder or self.dir).iterdir()):
            if p.is_symlink():
                out[p.name] = ("link", os.readlink(p))
            elif p.is_dir():
                out[p.name] = "dir"
            else:
                out[p.name] = p.read_bytes()
        return out


@pytest.fixture
def rig(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Rig:
    return Rig(tmp_path, capsys)


# -- next (AC-0008, AC-0009) -------------------------------------------------


def test_next_counts_records_notes_companions_and_remote(rig: Rig) -> None:
    assert rig.run("next")[1] == "0001\n"
    rig.put("0003-a.md")
    (rig.dir / "0007-notes").mkdir()
    rig.put("0009-b-research.md")
    assert rig.run("next")[1] == "0010\n"
    rig.mod.remote_names = lambda: {"0011-r.md", "0012-notes", "README.md"}
    assert rig.run("next")[1] == "0013\n"


def test_next_uses_upstream_and_origin_through_git_seam(rig: Rig) -> None:
    top = rig.dir.parent.parent
    calls: list[tuple[list[str], str, dict[str, str]]] = []

    def fake(argv: list[str], cwd: str, env: dict[str, str]) -> tuple[int, str]:
        calls.append((argv, cwd, env))
        sub = argv[9:]
        if sub[:2] == ["rev-parse", "--show-toplevel"]:
            return 0, str(top) + "\n"
        if sub[0] == "symbolic-ref":
            return (0, "origin/main\n") if "origin" in sub[-1] else (1, "")
        if sub[:2] == ["rev-parse", "--verify"]:
            return (0, "abc\n") if sub[-1] == "origin/main" else (1, "")
        if sub[0] == "ls-tree":
            assert sub[-1] == "origin/main:docs/rfc"
            return 0, "0020-r.md\n0021-notes\n"
        raise AssertionError(sub)

    rig.mod = Rig.load(rig.dir, stub=False)  # the real remote_names
    rig.mod._spawn = fake
    assert rig.run("next")[1] == "0022\n"
    assert calls


def test_next_exits_2_when_unreadable_or_full(rig: Rig, tmp_path: Path) -> None:
    code, out, _ = rig.run("--dir", str(tmp_path / "missing"), "next")
    assert (code, out) == (2, "")
    alias = tmp_path / "alias"
    alias.symlink_to(rig.dir)
    code, out, _ = rig.run("--dir", str(alias), "next")
    assert (code, out) == (2, "")
    rig.put("9999-a.md")
    code, out, err = rig.run("next")
    assert (code, out) == (2, "") and err


# -- new (AC-0010, AC-0011) --------------------------------------------------


def test_new_writes_numbered_file_from_template(rig: Rig) -> None:
    rig.put("0004-a.md")
    code, out, _ = rig.run("new", "Short Title", "--author", "someone")
    assert code == 0 and "0005-short-title.md" in out
    text = (rig.dir / "0005-short-title.md").read_text(encoding="utf-8")
    assert text.startswith("# RFC-0005: Short Title\n")
    assert f"**Date opened:** {datetime.date.today().isoformat()}" in text
    assert "**Author:** someone" in text and "<account-handle>" not in text


def test_new_title_placeholders_are_not_reexpanded(rig: Rig) -> None:
    rig.run("new", "About YYYY-MM-DD and <account-handle>", "--slug", "x")
    text = (rig.dir / "0001-x.md").read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# RFC-0001: About YYYY-MM-DD and <account-handle>"
    assert "**Author:** <account-handle>" in text


def test_new_refuses_used_number_or_dangling_link_and_writes_nothing(rig: Rig) -> None:
    rig.put("0003-a.md")
    before = rig.snapshot()
    assert rig.run("new", "Other", "--number", "3")[0] == 1
    (rig.dir / "0004-short-title.md").symlink_to(rig.dir / "nowhere")
    before = rig.snapshot()
    assert rig.run("new", "Short title", "--number", "4")[0] == 1
    assert rig.snapshot() == before


def test_new_refuses_template_that_is_a_link(rig: Rig, tmp_path: Path) -> None:
    (rig.dir / "template.md.tmpl").unlink()
    (tmp_path / "t").write_text(TEMPLATE, encoding="utf-8")
    (rig.dir / "template.md.tmpl").symlink_to(tmp_path / "t")
    before = rig.snapshot()
    assert rig.run("new", "Title")[0] == 2
    assert rig.snapshot() == before


# -- check (AC-0012, AC-0016 to AC-0021) ------------------------------------


def test_check_reads_draft_as_record(rig: Rig) -> None:
    rig.put("XXXX-a.md", rfc_text(skip="Proposal"))
    code, out, _ = rig.run("check")
    assert code == 0 and "XXXX-a.md" in out and "## Proposal" in out


def _padded(words: int, fenced: bool = False) -> str:
    headings = " ".join(f"## {s}" for s in SECTIONS)
    base = len(headings.split())
    fill = " ".join(["w"] * (words - base - (2 if fenced else 0)))
    body = f"```\n{fill}\n```\n" if fenced else fill + "\n"
    sections = "".join(f"## {s}\n\n" for s in SECTIONS)
    header = "- **Related:** " + " ".join(["h"] * 6000) + "\n"
    return f"# RFC-0001: title words here\n\n- **Status:** Draft\n{header}\n{sections}{body}"


@pytest.mark.parametrize("fenced", [False, True])
def test_check_word_limit_counts_all_but_title_and_header(rig: Rig, fenced: bool) -> None:
    rig.put("0001-a.md", _padded(5000, fenced))
    assert "words" not in rig.run("check")[1]
    rig.put("0001-a.md", _padded(5001, fenced))
    assert "5,001 words" in rig.run("check")[1]


@pytest.mark.parametrize("missing", SECTIONS)
def test_check_warns_on_each_missing_section(rig: Rig, missing: str) -> None:
    rig.put("0001-a.md", rfc_text(skip=missing))
    out = rig.run("check")[1]
    assert out.count("warning") == 1 and f"'## {missing}'" in out


def test_check_section_must_be_exact_level_two_heading(rig: Rig) -> None:
    text = rfc_text(skip="Summary") + "### Summary\n\n## Summary extra\n"
    rig.put("0001-a.md", text)
    assert "'## Summary'" in rig.run("check")[1]


def test_check_warns_on_shared_number(rig: Rig) -> None:
    rig.put("0001-a.md")
    rig.put("0001-b.md")
    rig.put("0001-a-research.md", "x")
    rig.put("XXXX-c.md")
    rig.put("XXXX-d.md")
    out = rig.run("check")[1]
    assert out.count("number 0001 is used by") == 1 and "XXXX" not in out.replace("XXXX-", "")


@pytest.mark.parametrize("status", ["Accepted", "Rejected", "Withdrawn", "Experimental", "Superseded"])
def test_check_skips_terminal_statuses(rig: Rig, status: str) -> None:
    rig.put("0001-a.md", rfc_text(status=status, skip="Summary", filler="w " * 6000))
    assert rig.run("check", "--strict") == (0, "", "")


def test_check_does_not_skip_open_status_and_skips_companions(rig: Rig) -> None:
    rig.put("0001-a.md", rfc_text(status="Final Comment Period", skip="Summary"))
    (rig.dir / "0002-b-research.md").write_bytes(b"\xff" * (1024 * 1024 + 5))
    code, out, _ = rig.run("check", str(rig.dir / "0002-b-research.md"))
    assert (code, out) == (0, "")
    assert "'## Summary'" in rig.run("check")[1]


def test_check_exit_codes(rig: Rig) -> None:
    rig.put("0001-a.md", rfc_text(skip="Summary"))
    assert rig.run("check")[0] == 0
    assert rig.run("check", "--strict")[0] == 1
    rig.put("0002-b.md", rfc_text())
    assert rig.run("check", str(rig.dir / "0002-b.md"), "--strict")[0] == 0
    assert rig.run("check", str(rig.dir / "0009-none.md"))[0] == 2
    (rig.dir / "0003-c.md").write_bytes(b"\xff\xfe")
    assert rig.run("check", "--strict")[0] == 2


def test_check_named_files_limit_length_and_section_checks(rig: Rig) -> None:
    rig.put("0001-a.md", rfc_text(skip="Summary"))
    rig.put("0002-b.md", rfc_text(skip="Proposal"))
    out = rig.run("check", str(rig.dir / "0002-b.md"))[1]
    assert "0002-b.md" in out and "0001-a.md" not in out


def test_check_named_non_record_is_skipped_and_outside_folder_is_an_error(rig: Rig, tmp_path: Path) -> None:
    rig.put("notes.txt", "x")
    code, out, _ = rig.run("check", str(rig.dir / "notes.txt"))
    assert code == 0 and "notes.txt" in out
    outside = tmp_path / "0001-z.md"
    outside.write_text(rfc_text(), encoding="utf-8")
    assert rig.run("check", str(outside))[0] == 2


# -- renumber (AC-0013 to AC-0015) -------------------------------------------


def test_renumber_renames_file_and_title(rig: Rig) -> None:
    rig.put("XXXX-a.md", rfc_text(title="RFC-XXXX: T"))
    code, out, _ = rig.run("renumber", str(rig.dir / "XXXX-a.md"), "5")
    assert code == 0 and "0005-a.md" in out
    assert not (rig.dir / "XXXX-a.md").exists()
    assert (rig.dir / "0005-a.md").read_text(encoding="utf-8").startswith("# RFC-0005: T\n")


def test_renumber_exits_1_on_used_number(rig: Rig) -> None:
    rig.put("XXXX-a.md")
    rig.put("0005-b.md")
    assert rig.run("renumber", str(rig.dir / "XXXX-a.md"), "5")[0] == 1


def test_renumber_refuses_symlinked_directory_component(rig: Rig, tmp_path: Path) -> None:
    rig.put("XXXX-a.md")
    alias = tmp_path / "alias"
    alias.symlink_to(rig.dir)
    before = rig.snapshot()
    assert rig.run("--dir", str(rig.dir), "renumber", str(alias / "XXXX-a.md"), "5")[0] == 2
    assert rig.snapshot() == before


def test_renumber_refuses_symlinked_directory_component_under_cwd(
    rig: Rig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig.put("XXXX-a.md")
    (tmp_path / "docs" / "alias").symlink_to(rig.dir)
    monkeypatch.chdir(tmp_path / "docs")
    before = rig.snapshot()
    assert rig.run("--dir", "alias", "renumber", "alias/XXXX-a.md", "5")[0] == 2
    assert rig.snapshot() == before


def test_renumber_failure_paths_leave_exactly_the_original(
    rig: Rig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig.put("XXXX-a.md", rfc_text(title="RFC-XXXX: T"))
    original = rig.snapshot()
    src = str(rig.dir / "XXXX-a.md")

    def fails(*args: str) -> None:
        code = rig.run(*args)[0]
        assert code != 0, args
        assert rig.snapshot() == original, args

    fails("renumber", src, "0")
    fails("renumber", src, "10000")
    fails("renumber", str(rig.dir / "template.md.tmpl"), "5")
    fails("renumber", str(rig.dir / "missing.md"), "5")
    (rig.dir / "0005-a.md").symlink_to(rig.dir / "nowhere")  # dangling link at the target name
    original = rig.snapshot()
    fails("renumber", src, "5")
    (rig.dir / "0005-a.md").unlink()
    # unlink of the source fails after the copy was made
    real_unlink = os.unlink

    def failing_unlink(path: Any, *a: Any, **k: Any) -> None:
        if str(path).endswith("XXXX-a.md"):
            raise OSError("denied")
        real_unlink(path, *a, **k)

    with monkeypatch.context() as m:
        m.setattr(os, "unlink", failing_unlink)
        original = rig.snapshot()
        fails("renumber", src, "5")
    # the exclusive create is refused
    fs = rig.mod._fs()

    def refuse(*a: Any, **k: Any) -> None:
        raise fs.UnsafeContentError("refused")

    with monkeypatch.context() as m:
        m.setattr(fs, "write_confined_regular_file", refuse)
        fails("renumber", src, "5")
    # a non-UTF-8 and an oversized source
    for name, data in (("XXXX-b.md", b"\xff\xfe"), ("XXXX-c.md", b"x" * (1024 * 1024 + 1))):
        (rig.dir / name).write_bytes(data)
        original = rig.snapshot()
        fails("renumber", str(rig.dir / name), "6")
    # the source is a link
    (rig.dir / "XXXX-d.md").symlink_to(tmp_path / "elsewhere.md")
    original = rig.snapshot()
    fails("renumber", str(rig.dir / "XXXX-d.md"), "7")


# -- imports and docs (AC-0023, AC-0084) -------------------------------------


def test_script_imports_only_standard_library() -> None:
    tree = ast.parse((SKILL_SCRIPTS / "rfc.py").read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.add((node.module or "").split(".")[0])
    assert modules and modules <= set(sys.stdlib_module_names)


def test_script_opens_no_folder_file_outside_the_loader() -> None:
    tree = ast.parse((SKILL_SCRIPTS / "rfc.py").read_text(encoding="utf-8"))
    banned = {"read_text", "write_text", "read_bytes", "write_bytes", "iterdir", "glob", "rglob"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "open"
        if isinstance(node, ast.Attribute):
            assert node.attr not in banned
            if node.attr == "open":
                assert isinstance(node.value, ast.Name) and node.value.id == "os"


def test_docstring_and_check_help_name_the_three_warnings(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLUMNS", "300")
    doc = rig.mod.__doc__
    assert "decided" not in doc.lower()
    paragraph = doc[doc.index("`check`"):]
    for text in (paragraph, ""):
        assert "branch" not in text.lower()
    with pytest.raises(SystemExit) as exit_info:
        rig.mod.main(["check", "--help"])
    assert exit_info.value.code == 0
    help_text = re.sub(r"\s+", " ", rig.capsys.readouterr().out)
    for text in (paragraph, help_text):
        flat = re.sub(r"\s+", " ", text)
        for word in ("length", "missing-section", "number-clash"):
            assert word in flat, word
        assert "decided" not in flat.lower() and "branch" not in flat.lower()


def test_check_starts_no_git_and_warns_about_no_branch_presence(rig: Rig) -> None:
    rig.put("0001-a.md", rfc_text(status="Accepted"))
    rig.mod.remote_names = lambda: set()

    def boom(*a: Any, **k: Any) -> None:
        raise AssertionError("check started a process")

    with pytest.MonkeyPatch.context() as m:
        m.setattr(subprocess, "run", boom)
        m.setattr(subprocess, "Popen", boom)
        assert rig.run("check", "--strict") == (0, "", "")


# -- folder inspection (AC-0026, AC-0031, AC-0028, AC-0029) ------------------


def test_check_exempts_only_the_two_scripts_and_ignores_notes(rig: Rig) -> None:
    (rig.dir / "README.md").write_text("x", encoding="utf-8")
    (rig.dir / "0001-notes").mkdir()
    (rig.dir / "0001-notes" / "evil.py").write_text("x", encoding="utf-8")
    assert rig.run("check", "--strict") == (0, "", "")


def test_check_warns_about_other_code_bytecode_and_folders(rig: Rig, tmp_path: Path) -> None:
    for name in ("extra.py", "x.pyc", "y.pth", "z.so"):
        (rig.dir / name).write_text("x", encoding="utf-8")
    (rig.dir / "__pycache__").mkdir()
    (rig.dir / "sub").mkdir()
    (rig.dir / "0001-other").mkdir()
    out = rig.run("check")[1]
    for name in ("extra.py", "x.pyc", "y.pth", "z.so", "__pycache__", "sub", "0001-other"):
        assert name in out, name
    assert out.count("warning") == 7


def test_check_warns_when_helper_is_a_link(rig: Rig, tmp_path: Path) -> None:
    (tmp_path / "real.py").write_text("x", encoding="utf-8")
    other = tmp_path / "other"
    other.mkdir()
    (other / "file_safety.py").symlink_to(tmp_path / "real.py")
    assert "file_safety.py" in rig.run("--dir", str(other), "check")[1]


def test_check_reports_odd_names_and_never_reads_them(rig: Rig) -> None:
    (rig.dir / "0001-A.md").write_bytes(b"x" * (1024 * 1024 + 9))
    (rig.dir / "weird.txt").write_bytes(b"\xff")
    (rig.dir / "9999-Bad.md").write_text("x", encoding="utf-8")
    code, out, err = rig.run("check")
    assert code == 0 and err == ""
    assert "0001-A.md" in out and "weird.txt" in out
    assert rig.run("next")[1] == "0001\n"
    assert rig.run("renumber", str(rig.dir / "0001-A.md"), "5")[0] == 2


def test_check_skips_directories_named_like_records(rig: Rig) -> None:
    (rig.dir / "0001-a.md").mkdir()
    code, out, err = rig.run("check")
    assert code == 0 and err == "" and "0001-a.md" in out
    assert rig.run("next")[1] == "0001\n"


def test_reads_refuse_links_and_cap_size(rig: Rig, tmp_path: Path) -> None:
    (tmp_path / "t.md").write_text(rfc_text(), encoding="utf-8")
    (rig.dir / "0001-l.md").symlink_to(tmp_path / "t.md")
    assert rig.run("check", str(rig.dir / "0001-l.md"))[0] == 2
    (rig.dir / "0002-h.md").hardlink_to(tmp_path / "t.md")
    assert rig.run("check", str(rig.dir / "0002-h.md"))[0] == 2
    big = rig.dir / "0003-big.md"
    big.write_text(rfc_text(), encoding="utf-8")
    with big.open("ab") as handle:
        handle.write(b" " * (1024 * 1024 - big.stat().st_size))
    assert big.stat().st_size == 1024 * 1024
    assert rig.run("check", str(big))[0] == 0
    with big.open("ab") as handle:
        handle.write(b" ")
    assert rig.run("check", str(big))[0] == 2


# -- names (AC-0030, AC-0032) -------------------------------------------------


def test_new_slug_rules(rig: Rig) -> None:
    rig.run("new", "T", "--slug", "A_b  c")
    assert (rig.dir / "0001-a-b-c.md").exists()
    rig.run("new", "T", "--slug", "x" * 80)
    assert (rig.dir / f"0002-{'x' * 60}.md").exists()
    rig.run("new", ("word " * 40).strip())
    names = [p.name for p in rig.dir.glob("0003-*")]
    assert len(names) == 1 and re.fullmatch(r"0003-[a-z0-9]+(-[a-z0-9]+)*\.md", names[0])
    assert len(names[0]) <= len("0003-.md") + 60


@pytest.mark.parametrize("args", [
    ("new", "T", "--number", "0"),
    ("new", "T", "--number", "10000"),
    ("new", "日本語"),
    ("new", "T", "--slug", "foo-research"),
    ("new", "\x1b \u200b"),
])
def test_new_refuses_bad_names_and_numbers(rig: Rig, args: tuple[str, ...]) -> None:
    before = rig.snapshot()
    assert rig.run(*args)[0] == 2
    assert rig.snapshot() == before


def test_new_title_is_one_clean_line(rig: Rig) -> None:
    rig.run("new", "A\n## Injected‮ title", "--slug", "x")
    first = (rig.dir / "0001-x.md").read_text(encoding="utf-8").splitlines()[0]
    assert first == "# RFC-0001: A ## Injected title"


def test_names_with_control_characters_are_escaped(rig: Rig) -> None:
    bad = "0001-a\x1b[31m.md"
    (rig.dir / bad).write_text("x", encoding="utf-8")
    (rig.dir / "0002-b.md").write_text(rfc_text(skip="Summary"), encoding="utf-8")
    code, out, err = rig.run("check", str(rig.dir / bad), str(rig.dir / "0002-b.md"), str(rig.dir / "\x1b-gone.md"))
    assert "\x1b" not in out + err and "\\x1b" in out + err
    code, out, err = rig.run("renumber", str(rig.dir / bad), "7")
    assert "\x1b" not in out + err


# -- git (AC-0033) ------------------------------------------------------------


def test_every_git_call_is_hardened_read_only_and_runs_in_the_folder(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[list[str], str, dict[str, str]]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.append((argv, str(kwargs.get("cwd")), dict(kwargs.get("env") or {})))
        sub = argv[9]
        out = {"rev-parse": str(rig.dir.parent.parent) + "\n", "symbolic-ref": "origin/main\n",
               "ls-tree": "0002-x.md\n"}[sub]
        return subprocess.CompletedProcess(argv, 0, out, "")

    rig.mod = Rig.load(rig.dir, stub=False)  # real _spawn and remote_names
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert rig.run("next")[1] == "0003\n"
    rig.run("new", "T", "--slug", "t")
    assert seen
    for argv, cwd, env in seen:
        assert argv[0] == "git"
        assert argv[1:9] == ["-c", "core.fsmonitor=", "-c", f"core.hooksPath={os.devnull}",
                             "-c", "protocol.allow=never", "-c", "safe.bareRepository=explicit"]
        assert argv[9] in {"rev-parse", "symbolic-ref", "ls-tree"}
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        assert Path(cwd).resolve() == rig.dir.resolve()


def test_git_subcommand_outside_allowlist_is_refused(rig: Rig) -> None:
    mod = Rig.load(rig.dir)
    with pytest.raises(ValueError):
        mod._git("fetch", "origin")


# -- --dir (AC-0034) ----------------------------------------------------------


def test_dir_targets_only_the_given_folder(
    rig: Rig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    marker = tmp_path / "planted-ran"
    (other / "file_safety.py").write_text(f"open({str(marker)!r}, 'w')\n", encoding="utf-8")
    (other / "template.md.tmpl").write_text(TEMPLATE + "OTHER-TEMPLATE\n", encoding="utf-8")
    rig.put("0005-other.md", folder=other)
    rig.put("0001-script.md")
    rig.put("0042-script-too.md")

    fs = rig.mod._fs()
    roots: list[Path] = []
    for name in ("read_confined_regular_file", "write_confined_regular_file", "validate_confined_directory"):
        real: Callable[..., Any] = getattr(fs, name)

        def spy(root: Path, *a: Any, _real: Callable[..., Any] = real, **k: Any) -> Any:
            roots.append(Path(root))
            return _real(root, *a, **k)

        monkeypatch.setattr(fs, name, spy)
    scanned: list[Path] = []
    real_scandir = os.scandir

    def scan(path: Any = ".") -> Any:
        scanned.append(Path(os.fspath(path)))
        return real_scandir(path)

    with monkeypatch.context() as m:
        m.setattr(os, "scandir", scan)
        assert rig.run("--dir", str(other), "next")[1] == "0006\n"
        assert rig.run("--dir", str(other), "new", "Fresh", "--slug", "fresh")[0] == 0
        assert rig.run("--dir", str(other), "check")[0] == 0
    assert (other / "0006-fresh.md").exists() and not (rig.dir / "0006-fresh.md").exists()
    assert "OTHER-TEMPLATE" in (other / "0006-fresh.md").read_text(encoding="utf-8")
    assert roots and {r.resolve() for r in roots} == {other.resolve()}
    assert scanned and {s.resolve() for s in scanned} == {other.resolve()}
    assert not marker.exists()
    assert not (other / "__pycache__").exists()


def test_dir_must_be_a_folder(rig: Rig, tmp_path: Path) -> None:
    (tmp_path / "f").write_text("x", encoding="utf-8")
    assert rig.run("--dir", str(tmp_path / "f"), "next")[0] == 2


# -- isolation and loading (AC-0024, AC-0025) ---------------------------------


def test_isolated_run_ignores_planted_module_and_bytecode(rig: Rig, tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    source = tmp_path / "plant.py"
    source.write_text(f"open({str(marker)!r}, 'a').write('ran')\n", encoding="utf-8")
    (rig.dir / "argparse.py").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    helper = rig.dir / "file_safety.py"
    cache = Path(importlib.util.cache_from_source(str(helper)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    py_compile.compile(
        str(source), cfile=str(cache), doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    )
    planted_bytes = cache.read_bytes()

    done = subprocess.run(
        [sys.executable, "-I", str(rig.dir / "rfc.py"), "next"],
        capture_output=True, text=True, cwd=tmp_path, timeout=60, check=False,
    )
    assert done.returncode == 0 and done.stdout == "0001\n", done.stderr
    assert not marker.exists()
    assert cache.read_bytes() == planted_bytes

    # Positive control: a by-path loader runs the planted bytecode, so the fixture is live.
    spec = importlib.util.spec_from_file_location("_planted_control", helper)
    assert spec is not None and spec.loader is not None
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = False
    try:
        spec.loader.exec_module(importlib.util.module_from_spec(spec))
    finally:
        sys.dont_write_bytecode = previous
    assert marker.read_text(encoding="utf-8") == "ran"


def test_helper_that_is_a_link_is_not_loaded(rig: Rig, tmp_path: Path) -> None:
    (tmp_path / "real.py").write_text(
        (SKILL_SCRIPTS / "file_safety.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (rig.dir / "file_safety.py").unlink()
    (rig.dir / "file_safety.py").symlink_to(tmp_path / "real.py")
    mod = Rig.load(rig.dir)
    code = mod.main(["next"])
    assert code == 2 and "file_safety" in rig.capsys.readouterr().err
