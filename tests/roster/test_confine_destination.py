"""AC3: the repo-governance confinement check accepts only in-root targets.

Roster-owned: it loads the shipped helper and CLI by path from the pack tree.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "packs/repo-governance/.apm/skills/new-adr/scripts"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helper = _load("roster_confine_destination_record_paths", SCRIPTS / "_record_paths.py")
cli = _load("roster_confine_destination_cli", SCRIPTS / "confine-destination.py")


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def _symlink(target: str | Path, link: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("cannot create symlinks here")


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "docs/adr").mkdir(parents=True)
    return repo


def _listing(path: Path) -> list[str]:
    return sorted(str(p.relative_to(path)) for p in path.rglob("*")) + sorted(
        child.name for child in path.parent.iterdir())


# --- accept -----------------------------------------------------------------

def test_existing_directory_accepted(root: Path) -> None:
    assert helper.confine_destination(root, "docs/adr") == str(
        (root / "docs/adr").resolve())


def test_missing_directory_accepted(root: Path) -> None:
    assert helper.confine_destination(root, "docs/new/deep") == str(
        root.resolve() / "docs/new/deep")
    assert not (root / "docs/new").exists()


def test_in_root_prefix_symlink_accepted_and_resolved(root: Path) -> None:
    _symlink(root / "docs", root / "alias")
    got = helper.confine_destination(root, "alias/adr")
    assert got == str((root / "docs/adr").resolve())
    assert "alias" not in got


def test_new_file_good_name_accepted(root: Path) -> None:
    got = helper.confine_destination(root, "docs/adr", new_file="0001-x.md")
    assert got == str((root / "docs/adr").resolve() / "0001-x.md")
    assert not (root / "docs/adr/0001-x.md").exists()


def test_new_file_in_missing_directory_creates_nothing(root: Path) -> None:
    helper.confine_destination(root, "docs/new", new_file="0001-x.md")
    assert not (root / "docs/new").exists()


def test_read_file_regular_accepted(root: Path) -> None:
    (root / "docs/adr/0001-x.md").write_text("x")
    got = helper.confine_destination(root, "docs/adr", read_file="0001-x.md")
    assert got == str((root / "docs/adr/0001-x.md").resolve())


def test_root_file_regular_accepted(root: Path) -> None:
    (root / "agentbundle-layout.toml").write_text("x")
    assert helper.confine_root_file(root, "agentbundle-layout.toml") == str(
        root.resolve() / "agentbundle-layout.toml")


# --- refuse: input grammar --------------------------------------------------

@pytest.mark.parametrize("relative", [
    "/abs/path", "C:/x", "c:rel", "docs\\adr", "docs/a\tb", "docs/a\nb",
    "", "docs//adr", "docs/./adr", "docs/../adr", "..", ".", "docs/",
    "a" * 1001, "docs/a\u0085b", "docs/a\u2028b", "docs/a\u2029b", "docs/a\x7fb",
])
def test_bad_relative_refused(root: Path, relative: str) -> None:
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, relative)


def test_resolved_path_over_1000_chars_refused(root: Path) -> None:
    relative = "/".join(["d" * 50] * 20)  # 1019 chars once joined
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, relative[:990])


def test_resolves_to_root_refused(root: Path) -> None:
    _symlink(".", root / "self")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "self")


# --- refuse: filesystem -----------------------------------------------------

def test_escaping_prefix_link_refused(root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink(outside, root / "out")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "out/adr")


def test_broken_prefix_link_refused(root: Path) -> None:
    _symlink("nowhere", root / "broken")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "broken/adr")


def test_looping_prefix_link_refused(root: Path) -> None:
    _symlink("b", root / "a")
    _symlink("a", root / "b")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "a/adr")


def test_final_component_symlink_refused(root: Path) -> None:
    _symlink(root / "docs/adr", root / "linked")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "linked")


def test_existing_non_directory_refused(root: Path) -> None:
    (root / "docs/file").write_text("x")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/file")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/file/sub")


def test_root_not_a_directory_refused(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.write_text("x")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(plain, "docs")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(tmp_path / "missing", "docs")


def _junction(link: Path, target: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("junctions exist only on Windows")
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True)
    if result.returncode != 0:
        pytest.skip("cannot make a junction here")


def test_in_root_junction_resolves_to_its_target(root: Path) -> None:
    _junction(root / "junc", root / "docs")
    assert helper.confine_destination(root, "junc/adr") == str(
        (root / "docs/adr").resolve())


def test_escaping_junction_refused(root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    (outside / "adr").mkdir(parents=True)
    _junction(root / "junc", outside)
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "junc/adr")


def test_component_that_resolves_outside_is_caught_by_resolved_containment(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """lstat reports a plain directory, yet the resolved location escapes.

    A junction or a component swapped after the walk looks like this; only
    the closing resolved-path containment can refuse it.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    swapped = root.resolve() / "docs" / "adr"

    real_resolve = Path.resolve

    def fake_resolve(self: Path, strict: bool = False) -> Path:
        if self == swapped:
            return outside
        return real_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", fake_resolve)
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr")


# --- new-file ---------------------------------------------------------------

def test_new_file_existing_file_refused(root: Path) -> None:
    (root / "docs/adr/0001-x.md").write_text("x")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", new_file="0001-x.md")


def test_new_file_existing_symlink_refused(root: Path) -> None:
    _symlink("nowhere", root / "docs/adr/0001-x.md")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", new_file="0001-x.md")


@pytest.mark.parametrize("name", [
    "x.txt", "x", ".md", "a/b.md", "../x.md", "x\\y.md", "x\n.md", "",
    "x\u0085.md", "x\u2028.md", "x\u2029.md",
])
def test_new_file_bad_name_refused(root: Path, name: str) -> None:
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", new_file=name)


@pytest.mark.parametrize("char", [
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2066", "\u2067", "\u2068", "\u2069",
])
def test_bidi_formatting_character_refused(root: Path, char: str) -> None:
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, f"docs/a{char}b")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", new_file=f"x{char}.md")


# --- read-file and root-file ------------------------------------------------

def test_read_file_symlink_refused(root: Path) -> None:
    (root / "docs/real.md").write_text("x")
    _symlink(root / "docs/real.md", root / "docs/adr/0001-x.md")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", read_file="0001-x.md")


def test_read_file_hard_link_refused(root: Path) -> None:
    (root / "docs/real.md").write_text("x")
    try:
        os.link(root / "docs/real.md", root / "docs/adr/0001-x.md")
    except OSError:
        pytest.skip("cannot hard link here")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", read_file="0001-x.md")


def test_read_file_directory_refused(root: Path) -> None:
    (root / "docs/adr/sub.md").mkdir()
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr", read_file="sub.md")


def test_read_file_bad_name_refused(root: Path) -> None:
    for name in ("a/b.md", "..", "x\\y", ""):
        with pytest.raises(helper.EntryRefused):
            helper.confine_destination(root, "docs/adr", read_file=name)


def test_root_file_symlink_and_hard_link_refused(root: Path) -> None:
    (root / "real.toml").write_text("x")
    _symlink("real.toml", root / "agentbundle-layout.toml")
    with pytest.raises(helper.EntryRefused):
        helper.confine_root_file(root, "agentbundle-layout.toml")
    try:
        os.link(root / "real.toml", root / "second.toml")
    except OSError:
        pytest.skip("cannot hard link here")
    with pytest.raises(helper.EntryRefused):
        helper.confine_root_file(root, "second.toml")


def test_root_file_bad_name_refused(root: Path) -> None:
    for name in ("docs/x", "../x", "", "a\\b"):
        with pytest.raises(helper.EntryRefused):
            helper.confine_root_file(root, name)


def test_read_file_missing_is_absent(root: Path) -> None:
    with pytest.raises(helper.EntryAbsent):
        helper.confine_destination(root, "docs/adr", read_file="nope.md")
    with pytest.raises(helper.EntryAbsent):
        helper.confine_destination(root, "no/such/dir", read_file="nope.md")
    with pytest.raises(helper.EntryAbsent):
        helper.confine_root_file(root, "nope.toml")


def test_absent_in_refused_directory_is_a_refusal(root: Path) -> None:
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/../x", read_file="nope.md")


# --- CLI exit codes and stdout ---------------------------------------------

def test_cli_success_prints_one_line(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, str(root), "docs/adr")
    assert (code, err) == (0, "")
    assert out == str((root / "docs/adr").resolve()) + "\n"


def test_cli_missing_name_exits_3_not_2(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, str(root), "docs/adr", "--read-file", "nope.md")
    assert (code, out) == (3, "")
    code, out, err = _run(capsys, str(root), "--root-file", "nope.toml")
    assert (code, out) == (3, "")


def test_cli_root_file_present(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (root / "agentbundle-layout.toml").write_text("x")
    code, out, _ = _run(capsys, str(root), "--root-file", "agentbundle-layout.toml")
    assert code == 0
    assert out == str(root.resolve() / "agentbundle-layout.toml") + "\n"


def test_cli_refusal_exit_2_stderr_only(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, str(root), "/etc")
    assert (code, out) == (2, "")
    assert err.startswith("refused: ")


@pytest.mark.parametrize("argv", [
    [], ["only-root"], ["r", "d", "--new-file"], ["r", "d", "--new-file", "a.md", "--read-file", "b"],
    ["r", "--root-file", "x", "extra"],
])
def test_cli_bad_usage_is_refusal_not_traceback(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, *argv)
    assert (code, out) == (2, "")
    assert "Traceback" not in err


def test_cli_newline_in_resolved_path_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "repo"
    (repo / "real\nname").mkdir(parents=True)
    _symlink("real\nname", repo / "alias")
    code, out, err = _run(capsys, str(repo), "alias/adr")
    assert (code, out) == (2, "")
    assert err.count("\n") == 1 and "Traceback" not in err


def test_cli_non_utf8_argument_refused_with_empty_stdout(root: Path) -> None:
    script = str(SCRIPTS / "confine-destination.py")
    for argv in ([str(root), "docs/\udcff"], [str(root), "docs/adr", "--new-file", "\udcff.md"]):
        try:
            result = subprocess.run([sys.executable, script, *argv], capture_output=True)
        except (UnicodeEncodeError, OSError):
            pytest.skip("this platform cannot pass a non-UTF-8 argument")
        assert result.returncode == 2 and result.stdout == b""
        assert b"Traceback" not in result.stderr


def test_cli_run_creates_nothing_under_scripts_dir(root: Path, tmp_path: Path) -> None:
    import shutil

    scripts = tmp_path / "scripts"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    before = sorted(str(p.relative_to(scripts)) for p in scripts.rglob("*"))
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    for argv in ([str(root), "docs/adr"], [str(root), "../x"],
                 [str(root), "--root-file", "nope"]):
        subprocess.run([sys.executable, str(scripts / "confine-destination.py"), *argv],
                       capture_output=True, text=True, env=env)
    assert sorted(str(p.relative_to(scripts)) for p in scripts.rglob("*")) == before


def test_cli_subprocess_exit_codes(root: Path) -> None:
    script = str(SCRIPTS / "confine-destination.py")
    ok = subprocess.run([sys.executable, script, str(root), "docs/adr"],
                        capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stdout.strip() == str((root / "docs/adr").resolve())
    absent = subprocess.run([sys.executable, script, str(root), "--root-file", "nope"],
                            capture_output=True, text=True)
    assert (absent.returncode, absent.stdout, absent.stderr) == (3, "", "")
    refused = subprocess.run([sys.executable, script, str(root), "../x"],
                             capture_output=True, text=True)
    assert refused.returncode == 2 and refused.stdout == ""
    assert refused.stderr.startswith("refused: ") and "Traceback" not in refused.stderr


# --- no effect, no race -----------------------------------------------------

def test_refusal_leaves_tree_unchanged(root: Path, tmp_path: Path) -> None:
    _symlink(tmp_path, root / "out")
    before = _listing(root)
    for kwargs in ({"relative": "out/x"}, {"relative": "docs/../x"},
                   {"relative": "docs/adr", "new_file": "bad.txt"}):
        with pytest.raises(helper.EntryRefused):
            helper.confine_destination(root, **kwargs)
    assert _listing(root) == before


def test_link_swapped_in_after_first_check_is_refused(root: Path, tmp_path: Path) -> None:
    assert helper.confine_destination(root, "docs/adr") == str(
        (root / "docs/adr").resolve())
    (root / "docs/adr").rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink(outside, root / "docs/adr")
    with pytest.raises(helper.EntryRefused):
        helper.confine_destination(root, "docs/adr")
