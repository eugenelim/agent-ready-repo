"""This repository's own pull-request form, and the guide that installs it.

These live outside the pack because a pack test may not read above its pack:
`.github/` and `guides/` are repository surfaces, not `core` content.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    return Path(out.stdout.strip()) if out.returncode == 0 else Path.cwd()


ROOT = _repo_root()
FORM = ROOT / ".github" / "pull_request_template.md"
GUIDE = ROOT / "guides" / "core" / "how-to" / "adapt-to-project.md"
ASSET = "pull-request-template.md"
ASSET_SOURCE = ROOT / "packs/core/.apm/skills/work-loop/assets" / ASSET
DESTINATIONS = {
    ".github/pull_request_template.md",
    ".gitlab/merge_request_templates/Default.md",
}
TASK_LIST_MARKER = re.compile(r"^\s*- \[[ x]\]", re.M)


def _guide_section() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    return text.split("## Install the pull-request template", 1)[1].split("\n## ", 1)[0]


def _flat(text: str) -> str:
    """Whitespace-normalised, for multi-word fragments in wrapped prose.

    Without it a fragment fails whenever the paragraph is reflowed -- a
    formatting change, not the deletion this pin exists to catch.
    """
    return " ".join(text.split())


# ------------------------------------------------------------------- AC-0009

def test_this_repositorys_form_carries_no_task_list_marker():
    assert not TASK_LIST_MARKER.search(FORM.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- AC-0011

def test_the_guide_still_says_an_existing_convention_wins():
    """Deletion pin. Catches removal; does not certify wording."""
    assert "should keep it" in _flat(_guide_section())


# ------------------------------------------- the installer SCRIPT is RUN

INSTALLER = ROOT / "packs/core/.apm/skills/work-loop/scripts/install-pr-template.py"


def _run_installer(cwd: Path, adapter: str = ".agents") -> subprocess.CompletedProcess:
    """Run the copy installed under `cwd`, as an adopter would.

    `sys.executable`, not a bare interpreter name: the installer must run on
    whatever Python the adopter has, including on Windows where `python3` may
    not be on PATH at all.
    """
    script = _installed(cwd, adapter)
    assert script.is_file(), (
        f"no installed script at {script} — the fixture must install one, or the "
        "test silently exercises the repository's copy instead"
    )
    return subprocess.run([sys.executable, str(script)], cwd=cwd,
                          capture_output=True, text=True)


def _repo_with_asset(tmp_path: Path, adapter: str) -> Path:
    """A real installed layout: the skill's assets AND its scripts.

    The installer resolves the asset as its own sibling, so a fixture that
    installs only the asset would silently exercise the repository's copy
    instead of the fixture's.
    """
    root = tmp_path / "repo"
    skill = root / adapter / "skills" / "work-loop"
    (skill / "assets").mkdir(parents=True)
    (skill / "scripts").mkdir(parents=True)
    # Bytes, not text: `write_text` would normalise newlines and make a CRLF
    # stream compare equal to an LF one, which is not byte-identity.
    (skill / "assets" / ASSET).write_bytes(ASSET_SOURCE.read_bytes())
    (skill / "scripts" / INSTALLER.name).write_bytes(INSTALLER.read_bytes())
    return root


def _installed(root: Path, adapter: str = ".agents") -> Path:
    return root / adapter / "skills/work-loop/scripts" / INSTALLER.name


def test_the_installer_installs_both_templates_in_a_fresh_repository(tmp_path):
    root = _repo_with_asset(tmp_path, ".agents")
    proc = _run_installer(root)
    assert proc.returncode == 0, proc.stderr
    expected = ASSET_SOURCE.read_bytes()
    for destination in DESTINATIONS:
        installed = root / destination
        assert installed.is_file(), destination
        # Byte-identity, not existence: `touch` would satisfy `is_file()`.
        assert installed.read_bytes() == expected, destination


@pytest.mark.parametrize("adapter", [".agents", ".claude", ".kiro"])
def test_the_installer_works_for_every_declared_adapter_root(tmp_path, adapter):
    """AC-0011 claims any declared root; two of three left `.kiro` unverified."""
    root = _repo_with_asset(tmp_path, adapter)
    assert _run_installer(root, adapter).returncode == 0
    assert (root / ".github/pull_request_template.md").read_bytes() == ASSET_SOURCE.read_bytes()


def test_the_installer_refuses_when_its_sibling_asset_is_missing(tmp_path):
    """The asset is resolved as a sibling, so a broken install is a missing file."""
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".agents/skills/work-loop/assets" / ASSET).unlink()
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert "reinstall the core pack" in proc.stderr
    # Every destination, not just the first: an erroneous `.gitlab` write would
    # otherwise pass.
    for destination in DESTINATIONS:
        assert not (root / destination).exists(), destination


def test_the_installer_is_idempotent(tmp_path):
    root = _repo_with_asset(tmp_path, ".agents")
    assert _run_installer(root).returncode == 0
    second = _run_installer(root)
    assert second.returncode == 0
    assert second.stdout.count("keeping your existing") == 2


def test_the_installer_keeps_an_existing_convention(tmp_path):
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").mkdir()
    (root / ".github/pull_request_template.md").write_text("MY OWN", encoding="utf-8")
    proc = _run_installer(root)
    assert proc.returncode == 0
    assert (root / ".github/pull_request_template.md").read_text() == "MY OWN"
    assert (root / ".gitlab/merge_request_templates/Default.md").is_file()


def test_the_installer_keeps_a_dangling_symlink_destination(tmp_path):
    """`-e` is false for a dangling symlink, so a leaf-only check writes THROUGH it.

    Asserting the symlink still exists proves nothing: `cp` follows it and
    creates the target, leaving the link in place. What distinguishes the two
    implementations is whether the link's target was created.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").mkdir()
    (root / ".github/pull_request_template.md").symlink_to("nowhere.md")
    proc = _run_installer(root)
    assert proc.returncode == 0
    assert (root / ".github/pull_request_template.md").is_symlink()
    assert "keeping your existing" in proc.stdout
    assert not (root / ".github/nowhere.md").exists(), "wrote through the dangling link"


def test_the_installer_refuses_a_symlinked_destination_ancestor(tmp_path):
    root = _repo_with_asset(tmp_path, ".agents")
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".github").symlink_to(outside, target_is_directory=True)
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert "leaves the repository" in proc.stderr
    assert not (outside / "pull_request_template.md").exists()


def test_the_installer_refuses_a_symlinked_source_ancestor(tmp_path):
    """A symlinked directory above the asset supplies bytes from outside."""
    root = tmp_path / "repo"
    (root / ".agents/skills").mkdir(parents=True)
    outside = tmp_path / "outside" / "work-loop"
    (outside / "assets").mkdir(parents=True)
    (outside / "scripts").mkdir(parents=True)
    (outside / "assets" / ASSET).write_text("BYTES FROM OUTSIDE", encoding="utf-8")
    (outside / "scripts" / INSTALLER.name).write_bytes(INSTALLER.read_bytes())
    (root / ".agents/skills/work-loop").symlink_to(outside, target_is_directory=True)

    proc = _run_installer(root)
    assert proc.returncode != 0, proc.stdout
    assert not (root / ".github/pull_request_template.md").exists()


def test_a_stale_install_under_another_root_does_not_block_this_one(tmp_path):
    """The invoked script identifies its own adapter.

    Scanning every root and refusing differing copies let a stale `.claude`
    install block a valid `.agents` invocation. The asset is now this script's
    sibling, so the question cannot arise.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    stale = root / ".claude" / "skills" / "work-loop" / "assets"
    stale.mkdir(parents=True)
    (stale / ASSET).write_text("A STALE TEMPLATE", encoding="utf-8")
    proc = _run_installer(root, ".agents")
    assert proc.returncode == 0, proc.stderr
    assert (root / ".github/pull_request_template.md").read_bytes() == ASSET_SOURCE.read_bytes()


def test_the_installer_reports_failure_when_a_destination_cannot_be_written(tmp_path):
    """A regular file where a directory must go fails deterministically.

    A mode-0500 directory does not: it stays writable under root or with
    suitable capabilities, so the test would depend on process privileges.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").write_text("not a directory", encoding="utf-8")
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert (root / ".gitlab/merge_request_templates/Default.md").is_file()


def test_the_guide_invokes_the_installer_and_nothing_more():
    """AC-0017. The guide is documentation again: one invocation, no program.

    It had grown a confinement walk, an adapter loop, a failure accumulator and
    a subshell -- executable logic a human was expected to copy and maintain
    inside prose.
    """
    section = _guide_section()
    bash = re.findall(r"^\s{0,3}(?:`{3,}|~{3,})bash\n(.*?)^\s{0,3}(?:`{3,}|~{3,})\s*$",
                      section, re.S | re.M)
    assert len(bash) == 1, f"expected one bash block, found {len(bash)}"
    lines = [line for line in bash[0].splitlines() if line.strip()]
    assert len(lines) == 1, f"the guide still embeds a program: {lines}"
    # The single line must itself invoke the shipped installer: accepting the
    # name anywhere in the section lets that line run something else entirely.
    # Under a DECLARED adapter root: any path ending in the script name would
    # otherwise satisfy this, including one outside the pack entirely.
    roots = "|".join(re.escape(r) for r in (".agents/skills", ".claude/skills",
                                            ".kiro/skills"))
    assert re.fullmatch(
        rf"python3? (?:{roots})/work-loop/scripts/install-pr-template\.py",
        lines[0].strip()), lines[0]


# ------------------------------------------------- portability, incl. Windows

def test_the_installer_uses_no_posix_only_facilities():
    """The pack ships to adopters on any platform.

    A shell script excluded Windows outright. Python does not, but only while
    the module keeps away from POSIX-only imports and shells out to nothing.
    """
    source = INSTALLER.read_text(encoding="utf-8")
    for posix_only in ("import fcntl", "import pwd", "import grp", "import termios",
                       "os.getuid", "os.geteuid", "os.fork", "os.system",
                       "subprocess", "shell=True"):
        assert posix_only not in source, posix_only


def test_the_installer_reconfigures_its_streams_to_utf8():
    """Required of every `.apm` script that prints, before its first print."""
    source = INSTALLER.read_text(encoding="utf-8")
    assert 'sys.stdout.reconfigure(encoding="utf-8"' in source
    assert 'sys.stderr.reconfigure(encoding="utf-8"' in source
    first_print = source.index("print(")
    assert source.index("sys.stdout.reconfigure") < first_print


def test_containment_is_decided_by_resolution_not_by_a_symlink_walk(tmp_path):
    """A Windows directory junction is not a symlink.

    `Path.is_symlink()` is false for one, so an ancestor walk would pass while
    the junction still redirects the read or the write. Resolving and checking
    containment catches symlinks and reparse points alike, on every platform.
    """
    # Parsed, not grepped: the function's own docstring explains why
    # `is_symlink()` is unsuitable, and a text search reads that prose as code.
    tree = ast.parse(INSTALLER.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "escapes_root")
    called = {n.func.attr for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "is_relative_to" in called, "containment is not decided by resolution"
    assert "resolve" in called, "the path is not resolved before the check"
    assert "is_symlink" not in called, "the check still walks for symlinks"

    # Behavioural: a redirected ancestor is refused even though the leaf is not
    # itself a link -- the shape a junction takes.
    root = _repo_with_asset(tmp_path, ".agents")
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".github").symlink_to(outside, target_is_directory=True)
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert not (outside / "pull_request_template.md").exists()


def test_the_guide_names_a_windows_friendly_invocation():
    """`python3` is frequently absent on Windows; the guide must say so."""
    flat = _flat(_guide_section())
    assert re.search(r"`python`[^.]{0,60}`python3`[^.]{0,40}Windows", flat) \
        or re.search(r"Windows[^.]{0,60}`python`", flat), flat


def test_the_installer_keeps_a_template_symlinked_to_a_shared_location(tmp_path):
    """A non-dangling symlink pointing outside the repo is a legitimate setup.

    Nothing is written in the keep branch, so where the existing template points
    is the adopter's business. Confining before that branch refused a team
    template stored in a shared location and failed an install that touches
    nothing. This fix was applied, probed, then destroyed by a `git checkout --`
    in a later mutation sweep and reported as done; the regression test is what
    makes that impossible to repeat.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "team.md").write_text("TEAM TEMPLATE", encoding="utf-8")
    (root / ".github").mkdir()
    (root / ".github/pull_request_template.md").symlink_to(shared / "team.md")

    proc = _run_installer(root)
    assert proc.returncode == 0, proc.stderr
    assert "keeping your existing" in proc.stdout
    assert (shared / "team.md").read_text(encoding="utf-8") == "TEAM TEMPLATE"
    assert (root / ".gitlab/merge_request_templates/Default.md").is_file()


def test_both_behavioural_suites_are_actually_gated():
    """AC-0018. They shipped once with no roster entry and no workflow step.

    A suite nothing runs reports nothing: the installer and the release checker
    were green only because they were run by hand.
    """
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/build-check.yml").read_text(encoding="utf-8")
    for suite in ("tools/test_pull_request_template_adoption.py",
                  "tools/test_check_core_release.py"):
        assert suite in makefile, f"{suite} is in no Makefile roster line"
        assert suite in workflow, f"{suite} is in no build-check step"
    # The whole-repository parity linter is NOT run here: an unrelated workflow
    # step added without its disposition would fail this pull-request-template
    # test. `tools/test-lint-ci-parity.py` owns that gate; this test owns only
    # the registration of these two suites.


def test_the_copy_publishes_by_rename(tmp_path):
    """A truncated file would be read as the adopter's own template next run.

    Structural half. The behavioural half lives in
    `test_a_mid_copy_failure_leaves_no_destination_and_no_temp`, which drives
    the module in-process and fails `copyfileobj` mid-stream — the seam an
    earlier draft wrongly called unconstructible after considering only
    subprocess-level failures.
    """
    tree = ast.parse(INSTALLER.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "install_one")
    calls = [n for n in ast.walk(fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    names = [c.func.attr for c in calls]
    assert "replace" in names, "the copy does not publish by rename"
    assert any(n in names for n in ("copyfile", "copyfileobj")), names
    # Whichever copy form is used, it must not write `dest` directly.
    copied_to = {a.id for c in calls if c.func.attr in ("copyfile", "copyfileobj")
                 for a in c.args if isinstance(a, ast.Name)}
    assert "dest" not in copied_to, "the copy writes the destination directly"

    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").write_text("not a directory", encoding="utf-8")
    proc = _run_installer(root)
    assert proc.returncode != 0
    # The handler must not crash: the second destination still installs.
    assert (root / ".gitlab/merge_request_templates/Default.md").is_file()
    assert not list(root.glob("**/*.partial")), "a partial file was left behind"


def test_a_pre_created_temp_path_cannot_capture_the_copy(tmp_path):
    """A predictable temp name is a redirect waiting to happen.

    Verified against the earlier fixed `.partial` name: pre-creating it as a
    symlink captured the template outside the repository while the install
    reported success. `mkstemp` creates with O_EXCL and a random suffix, so the
    path cannot be pre-created and cannot be followed.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".github").mkdir()
    (root / ".github/pull_request_template.md.partial").symlink_to(outside / "captured.md")

    proc = _run_installer(root)
    assert proc.returncode == 0, proc.stderr
    assert not (outside / "captured.md").exists(), "the copy was captured outside the repo"
    assert (root / ".github/pull_request_template.md").read_bytes() == ASSET_SOURCE.read_bytes()
    assert not list((root / ".github").glob(".pr-template-*")), "a temp file was left behind"


def test_the_temp_file_is_created_exclusively_with_a_random_name():
    """Structural: a fixed sibling name is the defect, not the copy itself."""
    tree = ast.parse(INSTALLER.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "install_one")
    names = {n.func.attr for n in ast.walk(fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "mkstemp" in names, "the temp file is not exclusively created"
    assert "with_name" not in names, "a predictable sibling name is still built"


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_installed_templates_keep_the_assets_permissions(tmp_path):
    """`mkstemp` creates 0600 and `replace` preserves it.

    Without copying the source's mode the installed template is owner-only
    while the asset it came from is world-readable — measured: 644 in, 600 out.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    source = root / ".agents/skills/work-loop/assets" / ASSET
    source.chmod(0o644)
    assert _run_installer(root).returncode == 0
    expected = stat.S_IMODE(source.stat().st_mode)
    for destination in DESTINATIONS:
        actual = stat.S_IMODE((root / destination).stat().st_mode)
        assert actual == expected, f"{destination}: {oct(actual)} != {oct(expected)}"


def test_a_mid_copy_failure_leaves_no_destination_and_no_temp(tmp_path, monkeypatch):
    """The case a subprocess test cannot provoke: a failure DURING the write.

    Every failure the other tests cause happens before a byte is written, so
    they cannot distinguish publish-by-rename from a direct copy. Driving the
    module in-process and failing `copyfileobj` mid-stream can.
    """
    spec = importlib.util.spec_from_file_location("installer_inproc", INSTALLER)
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)

    root = tmp_path / "repo"
    (root / ".github").mkdir(parents=True)
    src = tmp_path / "asset.md"
    src.write_bytes(ASSET_SOURCE.read_bytes())
    dest = root / ".github/pull_request_template.md"

    def _fail_midway(source, out, *args, **kwargs):
        out.write(b"partial")
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(installer.shutil, "copyfileobj", _fail_midway)
    assert installer.install_one(src, dest, root) is False
    assert not dest.exists(), "a truncated destination survived"
    assert not list((root / ".github").glob(".pr-template-*")), "a temp file survived"


def test_an_existing_directory_destination_is_refused(tmp_path):
    """A directory is not a template the forge can read.

    Treating it as an existing convention would report an install that never
    happened.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github/pull_request_template.md").mkdir(parents=True)
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert "is not a file" in proc.stderr


def test_a_symlink_to_a_directory_is_refused(tmp_path):
    """`is_file()` is false for it, but `exists()` is true — so it is not kept.

    Sibling of the directory case: a link to a directory is no more readable by
    the forge than a directory is, and reporting it kept claims an install that
    never happened.
    """
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").mkdir()
    a_dir = tmp_path / "a_dir"
    a_dir.mkdir()
    (root / ".github/pull_request_template.md").symlink_to(a_dir, target_is_directory=True)
    proc = _run_installer(root)
    assert proc.returncode != 0
    assert "is not a file" in proc.stderr


def test_a_symlink_to_a_file_is_kept(tmp_path):
    """The supported case the refusal above must not catch."""
    root = _repo_with_asset(tmp_path, ".agents")
    (root / ".github").mkdir()
    target = tmp_path / "team.md"
    target.write_text("TEAM", encoding="utf-8")
    (root / ".github/pull_request_template.md").symlink_to(target)
    proc = _run_installer(root)
    assert proc.returncode == 0, proc.stderr
    assert "keeping your existing" in proc.stdout
    assert target.read_text(encoding="utf-8") == "TEAM"


# ------------------------ AC-0005: portability, owned at repository level

# This check resolves candidate paths against the repository root, so it cannot
# live in `packs/core/tests/` — a pack test may not read above its own pack, and
# the boundary lint refuses it. The subject is shipped pack prose; the question
# ("does this path exist HERE?") is repository-scoped.

SHIPPED_PROSE = (
    ROOT / "packs/core/.apm/skills/work-loop/assets/pull-request-template.md",
    ROOT / "packs/core/.apm/skills/work-loop/references/pr-authoring.md",
)


def _fence_bodies(text: str) -> list[str]:
    lines, spans, opened, marker = text.splitlines(), [], None, None
    for i, line in enumerate(lines):
        opener = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if opened is None:
            if opener:
                opened, marker = i, opener.group(1)
        elif opener and opener.group(1)[0] == marker[0] \
                and len(opener.group(1)) >= len(marker) and not opener.group(2).strip():
            spans.append((opened, i))
            opened, marker = None, None
    if opened is not None:
        spans.append((opened, len(lines)))
    return ["\n".join(lines[a + 1:b]) for a, b in spans]


def _candidate_paths(text: str) -> set[str]:
    """Backtick code spans and words inside fences, filtered to path-like tokens.

    Named blind spot: a path written in bare prose, outside a code span and
    outside a fence, is not extracted.
    """
    candidates = set(re.findall(r"`([^`\n]+)`", text))
    for block in _fence_bodies(text):
        candidates |= set(block.split())
    return {c for c in candidates
            if "/" in c and not any(ch.isspace() for ch in c)
            and "<" not in c and ">" not in c}


def test_shipped_prose_cites_no_path_that_exists_only_in_this_repository():
    """AC-0005. A repository-only path is meaningless in an adopter's tree."""
    for path in SHIPPED_PROSE:
        for candidate in sorted(_candidate_paths(path.read_text(encoding="utf-8"))):
            if candidate in DESTINATIONS:
                continue
            # An absolute candidate would discard the root, and a `..` candidate
            # would escape it, making the result depend on the operator's disk.
            assert not Path(candidate).is_absolute(), f"{path.name}: {candidate!r} is absolute"
            target = (ROOT / candidate).resolve()
            assert target.is_relative_to(ROOT), f"{path.name}: {candidate!r} escapes the root"
            assert not (target.exists() or target.is_symlink()), (
                f"{path.name}: {candidate!r} resolves in this repository"
            )


def test_portability_does_not_depend_on_unrelated_repository_paths():
    """Creating a path a shipped example names must not fail this control."""
    for path in SHIPPED_PROSE:
        for candidate in _candidate_paths(path.read_text(encoding="utf-8")):
            assert candidate in DESTINATIONS or "<" in candidate or ">" in candidate, (
                f"{path.name}: {candidate!r} could collide with a future repository path"
            )
