"""Construction tests for the new-rfc governance script, one per criterion.

Cases call ``main`` in-process against temporary Git repositories; one smoke
case runs the script as a subprocess under the C locale.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import pathlib
import subprocess
import sys
import unicodedata
from typing import Any

import pytest

sys.dont_write_bytecode = True

SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/scripts"
SPEC = importlib.util.spec_from_file_location(
    "repo_governance_new_rfc_governance", SCRIPTS / "governance.py"
)
assert SPEC is not None and SPEC.loader is not None
GOV = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GOV
SPEC.loader.exec_module(GOV)

DEFAULT_MODEL = "single maintainer or small group by consensus"
DRAFT = (
    "# Governance\n\n"
    f"- **Decision model:** {DEFAULT_MODEL}\n\n"
    "## Maintainers\n\n- @alice\n\n"
    "## Owned paths\n\n- `GOVERNANCE.md`\n- `CODEOWNERS`\n- `AGENT_RULES.md`\n"
)
LAZY_DRAFT = DRAFT.replace(DEFAULT_MODEL, "lazy consensus")
LINK = "Roles and decision-making: [GOVERNANCE.md](../GOVERNANCE.md)"
GOVERNANCE_TARGETS = ("GOVERNANCE.md", "docs/GOVERNANCE.md", ".github/GOVERNANCE.md")
CODEOWNERS_TARGETS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
CHARTER_TARGETS = ("docs/CHARTER.md", "CHARTER.md")


def sha(data: bytes | str) -> str:
    """Return ``sha256:<hex>`` of text or bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def run_git(args: list[str], cwd: pathlib.Path) -> None:
    """Run a local Git setup command."""
    subprocess.run(
        ["git", *args], cwd=cwd, check=True, stdin=subprocess.DEVNULL,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """A fresh Git working tree."""
    root = tmp_path / "repo"
    root.mkdir()
    run_git(["init", "-q"], root)
    return root


class Result:
    """Exit status and captured streams of one call."""

    def __init__(self, code: int, out: str, err: str) -> None:
        self.code, self.out, self.err = code, out, err

    @property
    def refusal(self) -> str | None:
        """The reason of a one-line refusal, else None."""
        if self.code == 3 and self.out.startswith("refused: "):
            return self.out[len("refused: "):].rstrip("\n")
        return None


def call(
    capsys: pytest.CaptureFixture[str],
    root: pathlib.Path,
    sub: str,
    target: str,
    *extra: str,
    stdin: bytes | Any = b"",
    cwd: pathlib.Path | None = None,
) -> Result:
    """Run ``main`` in-process and capture its outcome."""
    capsys.readouterr()
    argv = [sub, "--root", str(root), "--target", target, *extra]
    code = GOV.main(argv, stdin, cwd or root)
    captured = capsys.readouterr()
    return Result(code, captured.out, captured.err)


def put(root: pathlib.Path, rel: str, text: str | bytes) -> None:
    """Create a file, with parents."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)


def listing(root: pathlib.Path) -> dict[str, str]:
    """sha256 of every file under *root*, ``.git`` included."""
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            found[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return found


def section(out: str, start: str, end: str) -> list[str]:
    """Lines strictly between two marker lines."""
    lines = out.split("\n")
    return lines[lines.index(start) + 1: lines.index(end)]


def field(out: str, name: str) -> str:
    """The value of a ``- Name: value`` line of a block."""
    prefix = f"- {name}: "
    for line in out.split("\n"):
        if line.startswith(prefix):
            return line[len(prefix):]
    raise AssertionError(f"no {name} line in {out!r}")


class NoRead:
    """A standard-input stand-in that fails the test when read."""

    def read(self, *_: object) -> bytes:
        raise AssertionError("standard input was read")


# --- AC-0001 / AC-0103 -------------------------------------------------------


@pytest.mark.parametrize("sub", ["show", "preview", "write"])
def test_ac_0001_root_must_be_the_worktree_top_level(
    sub: str, repo: pathlib.Path, tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    run_git(["init", "-q"], other)
    extra = ["--current", "absent", "--proposed", "sha256:" + "0" * 64] if sub == "write" else []
    result = call(capsys, repo, sub, "GOVERNANCE.md", *extra, stdin=NoRead(), cwd=other)
    assert result.refusal == "root-not-worktree"
    (repo / "sub").mkdir()
    result = call(capsys, repo / "sub", sub, "GOVERNANCE.md", *extra, stdin=NoRead(), cwd=repo / "sub")
    assert result.refusal == "root-not-worktree"
    outside = tmp_path / "plain"
    outside.mkdir()
    result = call(capsys, outside, sub, "GOVERNANCE.md", *extra, stdin=NoRead(), cwd=outside)
    assert result.refusal == "root-not-worktree"


def test_ac_0001_ignores_git_environment_overrides(
    repo: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    run_git(["init", "-q"], other)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    result = call(capsys, repo, "show", "GOVERNANCE.md")
    assert result.code == 0


@pytest.mark.parametrize("sub", ["show", "preview", "write"])
@pytest.mark.parametrize("target", ["README.md", "./GOVERNANCE.md", "governance.md", "docs/../GOVERNANCE.md", ""])
def test_ac_0103_target_must_be_allowed(
    sub: str, target: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    extra = ["--current", "absent", "--proposed", "sha256:" + "0" * 64] if sub == "write" else []
    result = call(capsys, repo, sub, target, *extra, stdin=NoRead())
    assert result.refusal == "target-not-allowed"


# --- input bounds, encoding, characters -------------------------------------


class RecordingStdin:
    """Records the sizes it was asked to read."""

    def __init__(self, data: bytes) -> None:
        self._buffer = io.BytesIO(data)
        self.asked: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.asked.append(size)
        return self._buffer.read(size)


@pytest.mark.parametrize("sub", ["preview", "write"])
def test_ac_0002_oversized_input_is_refused(
    sub: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stdin = RecordingStdin(b"a" * 65537)
    extra = ["--current", "absent", "--proposed", "sha256:" + "0" * 64] if sub == "write" else []
    result = call(capsys, repo, sub, "CODEOWNERS", *extra, stdin=stdin)
    assert result.refusal == "too-large"
    assert all(0 < n <= 65537 for n in stdin.asked)
    ok = call(capsys, repo, "preview", "CODEOWNERS", stdin=(b"# " + b"a" * 65534))
    assert ok.code == 0


@pytest.mark.parametrize("target", ["GOVERNANCE.md", "CODEOWNERS", "docs/CHARTER.md"])
@pytest.mark.parametrize("sub", ["preview", "write"])
def test_ac_0006_input_must_be_utf8(
    target: str, sub: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# Charter\n")
    extra = ["--after-line", "0"] if target.endswith("CHARTER.md") else []
    if sub == "write":
        extra += ["--current", "absent", "--proposed", "sha256:" + "0" * 64]
    result = call(capsys, repo, sub, target, *extra, stdin=b"abc\xff\xfe")
    assert result.refusal == "not-utf8"


@pytest.mark.parametrize(
    "char",
    ["\x00", "\x1b", "\x7f", "\x85", "\r", "\u2028", "\u2029", "\u061c", "\u200e",
     "\u200f", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067",
     "\u2068", "\u2069"],
)
def test_ac_0107_refused_characters(
    char: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for sub in ("preview", "write"):
        extra = ["--current", "absent", "--proposed", "sha256:" + "0" * 64] if sub == "write" else []
        result = call(capsys, repo, sub, "CODEOWNERS", *extra,
                      stdin=f"# a{char}b\n".encode())
        assert result.refusal == "refused-character"


def test_ac_0107_allowed_neighbours_are_not_refused(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for text in ("# a\tb\r\n/x @a\r\n", "# a\u200bb\n", "# \u202f\n"):
        assert call(capsys, repo, "preview", "CODEOWNERS", stdin=text.encode()).code == 0


# --- reads and confinement ---------------------------------------------------


def read_files_for(target: str) -> tuple[str, ...]:
    """The files a run reads for *target*, per the spec's Terms."""
    if target in CODEOWNERS_TARGETS:
        return CODEOWNERS_TARGETS
    return GOVERNANCE_TARGETS + CHARTER_TARGETS


READ_CASES = [
    (target, rel)
    for target in ("GOVERNANCE.md", "CODEOWNERS", "docs/CHARTER.md")
    for rel in read_files_for(target)
]


def make_shape(root: pathlib.Path, rel: str, shape: str) -> bool:
    """Create an unsafe shape at *rel*; False when the shape does not apply."""
    path = root / rel
    if shape == "dirlink":
        if "/" not in rel:
            return False
        real = root.parent / "elsewhere"
        real.mkdir(exist_ok=True)
        (real / path.name).write_text("x\n", encoding="utf-8")
        path.parent.parent.mkdir(parents=True, exist_ok=True)
        path.parent.symlink_to(real, target_is_directory=True)
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    if shape == "filelink":
        side = root.parent / "side.txt"
        side.write_text("x\n", encoding="utf-8")
        path.symlink_to(side)
    elif shape == "hardlink":
        side = root / "side.txt"
        side.write_text("x\n", encoding="utf-8")
        os.link(side, path)
    elif shape == "fifo":
        os.mkfifo(path)
    elif shape == "dangling":
        path.symlink_to(root.parent / "no-such-file")
    return True


@pytest.mark.parametrize("shape", ["dirlink", "filelink", "hardlink", "fifo"])
@pytest.mark.parametrize(("target", "rel"), READ_CASES)
def test_ac_0003_unsafe_files_are_refused(
    target: str, rel: str, shape: str, repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if not make_shape(repo, rel, shape):
        pytest.skip("shape needs a directory")
    before = listing(repo)
    proposal = b"# c\n" if "CODEOWNERS" in target else DRAFT.encode()
    for sub, stdin in (("show", b""), ("preview", proposal), ("write", proposal)):
        extra = ["--after-line", "0"] if sub != "show" and target.endswith("CHARTER.md") else []
        if sub == "write":
            extra += ["--current", "absent", "--proposed", sha(proposal)]
        result = call(capsys, repo, sub, target, *extra, stdin=stdin)
        assert result.refusal == "unsafe-path", (sub, result.out)
    assert listing(repo) == before


@pytest.mark.parametrize(("target", "rel"), READ_CASES)
def test_ac_0004_unsafe_is_never_reported_as_absent(
    target: str, rel: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_shape(repo, rel, "dangling")
    result = call(capsys, repo, "show", target)
    assert result.refusal == "unsafe-path"
    assert "absent" not in result.out
    if target == "CODEOWNERS":
        write = call(capsys, repo, "write", target, "--current", "absent",
                     "--proposed", sha("# c\n"), stdin=b"# c\n")
        assert write.refusal == "unsafe-path"


def test_ac_0005_reads_go_through_the_confined_helper(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fs = GOV._get_file_safety()
    calls: list[dict[str, Any]] = []
    real = fs.read_confined_regular_file

    def spy(root: pathlib.Path, path: pathlib.Path, **kwargs: Any) -> Any:
        calls.append({"path": path, **kwargs})
        return real(root, path, **kwargs)

    monkeypatch.setattr(fs, "read_confined_regular_file", spy)
    put(repo, "GOVERNANCE.md", DRAFT)
    assert call(capsys, repo, "show", "GOVERNANCE.md").code == 0
    assert calls
    assert all(c["max_bytes"] == 2_999_999 for c in calls)
    source = (SCRIPTS / "governance.py").read_text(encoding="utf-8")
    for banned in ("open(", "read_bytes", "read_text", "os.open"):
        assert banned not in source


def test_ac_0005_large_file_is_too_large(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", b"#" * 3_000_000)
    assert call(capsys, repo, "show", "CODEOWNERS").refusal == "too-large"
    put(repo, "CODEOWNERS", b"#" * 2_999_999)
    assert call(capsys, repo, "show", "CODEOWNERS").code == 0


# --- CODEOWNERS grammar -----------------------------------------------------


def preview_owners(
    capsys: pytest.CaptureFixture[str], root: pathlib.Path, text: str,
    target: str = "CODEOWNERS", *extra: str,
) -> Result:
    """Preview a CODEOWNERS proposal."""
    return call(capsys, root, "preview", target, *extra, stdin=text.encode("utf-8"))


def test_ac_0007_invalid_rule_line_is_numbered(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = "# header\n\n/ok @a\n/bad\\path @a\n/also[bad] @b\n"
    for sub in ("preview", "write"):
        extra = ["--current", "absent", "--proposed", sha(text)] if sub == "write" else []
        result = call(capsys, repo, sub, "CODEOWNERS", *extra, stdin=text.encode())
        assert result.refusal == "invalid-codeowners-line 4"


@pytest.mark.parametrize("line", ["!neg @a", "a#b @a", "/x[y] @a", "/x\\ @a", "/x @a # note"])
def test_ac_0007_each_invalid_shape(
    line: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_owners(capsys, repo, f"{line}\n").refusal == "invalid-codeowners-line 1"


@pytest.mark.parametrize(
    "space",
    ["\u00a0", "\u1680", *(chr(c) for c in range(0x2000, 0x200B)), "\u202f", "\u205f", "\u3000"],
)
def test_ac_0112_unicode_whitespace_in_a_pattern(
    space: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = preview_owners(capsys, repo, f"/a{space}b @x\n")
    assert result.refusal == "invalid-codeowners-line 1"


@pytest.mark.parametrize(
    "owner",
    ["a@example.com", "alice", "@", "@-a", "@a-", "@a--b", "@org/", "@a/b/c", "@a_b",
     "@" + "a" * 40, "@o/" + "t" * 101, "@a/-b", "@a/_b", "@é"],
)
def test_ac_0008_bad_owners(
    owner: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_owners(capsys, repo, f"/x {owner}\n").refusal == "invalid-codeowners-line 1"


@pytest.mark.parametrize("owner", ["@a", "@A1-b2", "@" + "a" * 39, "@org/team_1-x", "@o/" + "t" * 100])
def test_ac_0008_good_owners(
    owner: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_owners(capsys, repo, f"/x {owner}\n").code == 0


def test_ac_0009_proposed_rules_in_file_order(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = "# c\n\n/src/ @alice\n   \n  # indented comment\n/docs/ @acme/docs @bob\n*.md\n"
    out = preview_owners(capsys, repo, text).out
    assert section(out, "--- as GitHub reads it ---", "--- end ---") == [
        "3: /src/ → @alice", "6: /docs/ → @acme/docs @bob", "7: *.md → (no owners)",
    ]


def test_ac_0010_reads_now_section(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, ".github/CODEOWNERS", "# c\n/a @x\n/b[ @y\n\n/c\n")
    put(repo, "CODEOWNERS", "/other @z\n")
    out = preview_owners(capsys, repo, "/n @w\n").out
    assert section(out, "--- GitHub reads now ---", "--- as GitHub reads it ---") == [
        "2: /a → @x", "3: not valid for this mode: /b[ @y", "5: /c → (no owners)",
    ]


def test_ac_0010_invalid_line_keeps_leading_space_and_drops_one_trailing_cr(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", b"  /x a@example.invalid\r\n/ok @a\n")
    out = preview_owners(capsys, repo, "/n @w\n").out
    assert section(out, "--- GitHub reads now ---", "--- as GitHub reads it ---") == [
        "1: not valid for this mode:   /x a@example.invalid", "2: /ok → @a",
    ]


def test_ac_0010_reads_now_empty_when_none_present(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = preview_owners(capsys, repo, "/n @w\n").out
    assert section(out, "--- GitHub reads now ---", "--- as GitHub reads it ---") == []


def test_ac_0011_status_lines(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CODEOWNERS", "/d @x\n")
    put(repo, ".github/CODEOWNERS", "/g @x\n")
    out = preview_owners(capsys, repo, "/a\n/b @c\n/d\n").out
    assert field(out, "GitHub reads") == ".github/CODEOWNERS"
    assert field(out, "Also present") == ".github/CODEOWNERS, docs/CODEOWNERS"
    assert field(out, "Rules with no owners") == "2"
    out = preview_owners(capsys, repo, "/a @c\n", ".github/CODEOWNERS").out
    assert field(out, "Also present") == "docs/CODEOWNERS"


def test_ac_0011_none_values(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "docs").mkdir()
    out = preview_owners(capsys, repo, "# nothing\n", "docs/CODEOWNERS").out
    assert field(out, "GitHub reads") == "docs/CODEOWNERS"
    assert field(out, "Also present") == "none"
    assert field(out, "Rules with no owners") == "0"


def test_preview_block_line_order(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = "/a @b\n"
    out = preview_owners(capsys, repo, text).out
    prefixes = [
        "GOVERNANCE PREVIEW:", "- Target: CODEOWNERS", "- Kind: codeowners",
        "- Current: absent", f"- Proposed: {sha(text)} (6 bytes)",
        "- Approval required: yes \u2014 codeowners ownership change", "- Approved by: none",
        "- Characters made visible: 0", "- GitHub reads: CODEOWNERS",
        "- Also present: none", "- Rules with no owners: 0", "--- content ---",
    ]
    assert out.split("\n")[: len(prefixes)] == prefixes
    assert out.split("\n")[-4:] == ["--- as GitHub reads it ---", "1: /a → @b", "--- end ---", ""]
    assert out.endswith("--- end ---\n")


# --- visible form -----------------------------------------------------------


def test_ac_0012_visible_form_and_count(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unassigned = "\u0378"
    assert unicodedata.category(unassigned) == "Cn"
    put(repo, ".github/CODEOWNERS", "/r\u200bx @a\n")
    proposed = f"/p\ufe0fq @a\n# c\u3164d {unassigned}\n"
    out = preview_owners(capsys, repo, proposed, "CODEOWNERS").out
    content = section(out, "--- content ---", "--- end content ---")
    assert content[0] == "/p⟨U+FE0F⟩q @a"
    assert content[1] == "# c⟨U+3164⟩d ⟨U+0378⟩"
    now = section(out, "--- GitHub reads now ---", "--- as GitHub reads it ---")
    assert now == ["1: /r⟨U+200B⟩x → @a"]
    assert field(out, "Characters made visible") == "4"
    assert "\u200b" not in out and "\ufe0f" not in out and "\u3164" not in out


def test_content_section_adds_no_blank_line_before_its_end_marker(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = preview_owners(capsys, repo, "/src/ @alice\n", "CODEOWNERS").out
    assert section(out, "--- content ---", "--- end content ---") == ["/src/ @alice"]


def test_ac_0012_show_block(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = "a\u200bb\n\x01\n"
    put(repo, "GOVERNANCE.md", body)
    out = call(capsys, repo, "show", "GOVERNANCE.md").out
    lines = out.split("\n")
    assert lines[:5] == [
        "GOVERNANCE CURRENT:", "- Target: GOVERNANCE.md",
        f"- Current: {sha(body)}", "- Characters made visible: 2",
        "--- content ---",
    ]
    assert lines[5:7] == ["a⟨U+200B⟩b", "⟨U+0001⟩"]
    assert "--- end content ---" in lines
    absent = call(capsys, repo, "show", "docs/GOVERNANCE.md").out
    assert "- Current: absent" in absent
    assert "- Characters made visible: 0" in absent


def test_ac_0012_hidden_list_matches_unicode_categories() -> None:
    hidden = GOV.is_hidden
    for cp in range(0x110000):
        ch = chr(cp)
        cat = unicodedata.category(ch)
        if cat in ("Cf", "Zl", "Zp", "Cn", "Co", "Cs") or (
            cat == "Cc" and ch not in "\t\n"
        ):
            assert hidden(ch), hex(cp)
    for cp in (0xAD, 0x34F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180B, 0x180F, 0x3164,
               0xFE00, 0xFE0F, 0xFFA0, 0xFFF0, 0xFFF8, 0x1BCA0, 0x1BCA3, 0x1D173,
               0x1D17A, 0xE0000, 0xE0FFF):
        assert hidden(chr(cp)), hex(cp)
    assert not hidden("a") and not hidden("\t") and not hidden("\n") and not hidden("é")
    for lo, hi in GOV.HIDDEN_RANGES:
        assert lo <= hi


def test_ac_0013_text_reaches_stdout_only_in_sections(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", "/cur-marker @cur-marker\n")
    proposed = "/in-marker @in-marker\n"
    approved = "owner-marker\u200b"
    result = call(capsys, repo, "preview", "CODEOWNERS", "--approved-by", approved,
                  stdin=proposed.encode())
    assert result.err == ""
    assert "Approved by: owner-marker⟨U+200B⟩" in result.out
    allowed = set(
        section(result.out, "--- content ---", "--- end content ---")
        + section(result.out, "--- GitHub reads now ---", "--- end ---")
    )
    for line in result.out.split("\n"):
        if "marker" in line:
            assert line in allowed or line.startswith("- Approved by: ")
    # Refusals and usage errors carry no input text.
    bad = call(capsys, repo, "preview", "CODEOWNERS", "--approved-by", "evil-marker\x1b",
               stdin=proposed.encode())
    assert bad.out == "refused: invalid-approval\n" and bad.err == ""
    bad = call(capsys, repo, "preview", "CODEOWNERS", "--approved-by", "ok-marker",
               stdin=b"/x bad-marker\n")
    assert bad.out == "refused: invalid-codeowners-line 1\n" and bad.err == ""
    use = call(capsys, repo, "preview", "CODEOWNERS", "--bogus-marker", stdin=b"")
    assert use.code == 2 and use.out == "" and "marker" not in use.err


def test_ac_0014_show_and_preview_write_nothing(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    put(repo, "GOVERNANCE.md", DRAFT)
    put(repo, "docs/CHARTER.md", "# C\n")
    fs = GOV._get_file_safety()

    def boom(*_: object, **__: object) -> None:
        raise AssertionError("write attempted")

    monkeypatch.setattr(fs, "write_confined_regular_file", boom)
    before = listing(repo)
    assert call(capsys, repo, "show", "GOVERNANCE.md").code == 0
    assert call(capsys, repo, "preview", "GOVERNANCE.md", "--approved-by", "x",
                stdin=DRAFT.encode()).code == 0
    assert call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "1",
                stdin=LINK.encode()).code == 0
    assert call(capsys, repo, "preview", "CODEOWNERS", stdin=b"/a @b\n").code == 0
    assert listing(repo) == before


# --- approval ---------------------------------------------------------------


def approval(out: str) -> str:
    """The ``Approval required:`` value."""
    return field(out, "Approval required")


def test_ac_0015_and_ac_0016_reasons_and_order(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fresh = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode())
    assert approval(fresh.out) == "no"
    lazy = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=LAZY_DRAFT.encode())
    assert approval(lazy.out) == "yes — decision model is not the default"
    put(repo, "docs/GOVERNANCE.md", DRAFT)
    present = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode())
    assert approval(present.out) == "yes — a GOVERNANCE.md is present"
    both = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=LAZY_DRAFT.encode())
    assert approval(both.out) == "yes — a GOVERNANCE.md is present"
    put(repo, "GOVERNANCE.md", DRAFT)
    target_itself = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode())
    assert approval(target_itself.out) == "yes — a GOVERNANCE.md is present"
    owners = call(capsys, repo, "preview", "CODEOWNERS", stdin=b"/a @b\n")
    assert approval(owners.out) == "yes — codeowners ownership change"
    put(repo, "CODEOWNERS", "/a @b\n")
    comments = call(capsys, repo, "preview", "CODEOWNERS", stdin=b"# only\n/a @b\n")
    assert approval(comments.out) == "no"


def test_ac_0015_charter_never_needs_approval(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\n")
    put(repo, "GOVERNANCE.md", DRAFT)
    out = call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "1",
               stdin=LINK.encode()).out
    assert approval(out) == "no"


@pytest.mark.parametrize(
    "value", ["", "x" * 201, "a\x1bb", "a\nb", "a\r\nb", "a\u202eb", "a\u2028b", "a\rb"]
)
def test_ac_0017_invalid_approval(
    value: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for sub in ("preview", "write"):
        extra = ["--current", "absent", "--proposed", sha(DRAFT)] if sub == "write" else []
        result = call(capsys, repo, sub, "GOVERNANCE.md", *extra, "--approved-by", value,
                      stdin=DRAFT.encode())
        assert result.refusal == "invalid-approval"


def test_ac_0017_boundary_value_is_valid(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    value = "é" * 200
    out = call(capsys, repo, "preview", "GOVERNANCE.md", "--approved-by", value,
               stdin=DRAFT.encode())
    assert out.code == 0 and f"- Approved by: {value}" in out.out


def test_ac_0018_write_needs_a_named_approval(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", "/old @a\n")
    new = "/new @b\n"
    before = listing(repo)
    result = call(capsys, repo, "write", "CODEOWNERS", "--current", sha("/old @a\n"),
                  "--proposed", sha(new), stdin=new.encode())
    assert result.refusal == "approval-required"
    assert listing(repo) == before
    done = call(capsys, repo, "write", "CODEOWNERS", "--current", sha("/old @a\n"),
                "--proposed", sha(new), "--approved-by", "the owner decision",
                stdin=new.encode())
    assert done.code == 0
    assert (repo / "CODEOWNERS").read_text(encoding="utf-8") == new


def test_ac_0018_lazy_model_needs_approval(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = call(capsys, repo, "write", "GOVERNANCE.md", "--current", "absent",
                  "--proposed", sha(LAZY_DRAFT), stdin=LAZY_DRAFT.encode())
    assert result.refusal == "approval-required"
    assert not (repo / "GOVERNANCE.md").exists()


def test_ac_0019_shadowing_file_is_an_ownership_change(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", "* @owners\n")
    (repo / ".github").mkdir()
    out = call(capsys, repo, "preview", ".github/CODEOWNERS", stdin=b"# only a comment\n").out
    assert approval(out) == "yes — codeowners ownership change"
    assert field(out, "GitHub reads") == ".github/CODEOWNERS"


def test_ac_0019_other_changes(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", "* @owners\n")
    # a different rule list in the file GitHub reads
    assert approval(call(capsys, repo, "preview", "CODEOWNERS", stdin=b"* @other\n").out).startswith("yes")
    # an owned file that is not the one GitHub reads, written while a higher one exists
    (repo / "docs").mkdir()
    put(repo, ".github/CODEOWNERS", "* @owners\n")
    quiet = call(capsys, repo, "preview", "docs/CODEOWNERS", stdin=b"# note\n").out
    assert approval(quiet) == "no"
    # an unparseable current file makes any write an ownership change
    put(repo, ".github/CODEOWNERS", "/bad[ @a\n")
    assert approval(call(capsys, repo, "preview", ".github/CODEOWNERS", stdin=b"# c\n").out).startswith("yes")
    # creating the first file is a change only when it holds rules
    other = repo.parent / "second"
    other.mkdir()
    run_git(["init", "-q"], other)
    assert approval(call(capsys, other, "preview", "CODEOWNERS", stdin=b"/a @b\n").out).startswith("yes")


def test_ac_0020_comment_only_change_is_not_ownership(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, ".github/CODEOWNERS", "# old\n/a @b\n\n/c @d @e\n")
    out = call(capsys, repo, "preview", ".github/CODEOWNERS",
               stdin=b"# new comment\n/a @b\n# more\n\n\n/c @d @e\n").out
    assert approval(out) == "no"


# --- governance draft -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        DRAFT.replace("- **Decision model:**", "- Decision model:"),
        DRAFT + f"- **Decision model:** {DEFAULT_MODEL}\n",
        DRAFT.replace("- @alice", "- alice"),
        DRAFT.replace("- @alice", "prose only"),
        DRAFT.replace("- @alice", "- @alice @bob"),
        DRAFT.replace("`CODEOWNERS`", "CODEOWNERS"),
        DRAFT.replace("`AGENT_RULES.md`", ""),
        DRAFT.replace("`GOVERNANCE.md`", ""),
        DRAFT.replace("## Maintainers", "## People"),
        DRAFT.replace("## Owned paths", "## Paths"),
        DRAFT.replace("## Maintainers\n\n- @alice\n\n", "## Maintainers\n\n## Other\n\n- @alice\n\n"),
    ],
)
def test_ac_0021_incomplete_draft(
    text: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for sub in ("preview", "write"):
        extra = ["--current", "absent", "--proposed", sha(text)] if sub == "write" else []
        result = call(capsys, repo, sub, "GOVERNANCE.md", *extra, stdin=text.encode())
        assert result.refusal == "governance-draft-incomplete"


def test_ac_0021_complete_drafts_pass() -> None:
    assert GOV.is_governance_draft(DRAFT)
    assert GOV.is_governance_draft(LAZY_DRAFT)
    assert GOV.is_governance_draft(DRAFT.replace("- @alice", "- @alice\n- @acme/core"))
    assert GOV.decision_model(LAZY_DRAFT) == "lazy consensus"
    assert not GOV.is_governance_draft("- @<maintainer-handle>")


# --- charter ----------------------------------------------------------------


def test_ac_0022_charter_missing(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for sub in ("preview", "write"):
        extra = ["--current", "absent", "--proposed", sha(LINK)] if sub == "write" else []
        result = call(capsys, repo, sub, "docs/CHARTER.md", "--after-line", "0", *extra,
                      stdin=LINK.encode())
        assert result.refusal == "charter-missing"
    result = call(capsys, repo, "preview", "CHARTER.md", "--after-line", "0", stdin=LINK.encode())
    assert result.refusal == "charter-missing"


def test_ac_0110_target_must_be_the_charter(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# A\n")
    put(repo, "CHARTER.md", "# B\n")
    for sub in ("preview", "write"):
        extra = ["--current", sha("# B\n"), "--proposed", sha(LINK)] if sub == "write" else []
        result = call(capsys, repo, sub, "CHARTER.md", "--after-line", "0", *extra,
                      stdin=LINK.encode())
        assert result.refusal == "not-the-charter"
    ok = call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "0", stdin=b"Roles and decision-making: [GOVERNANCE.md](../GOVERNANCE.md)")
    assert ok.code == 0


def test_ac_0104_charter_already_links(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for charter, body in (
        ("docs/CHARTER.md", "# C\nSee [roles](../GOVERNANCE.md) now\n"),
        ("docs/CHARTER.md", "# C\n[g](GOVERNANCE.md)\n"),
        ("docs/CHARTER.md", "# C\n[g](./GOVERNANCE.md)\n"),
        ("CHARTER.md", "# C\n[g](docs/GOVERNANCE.md)\n"),
        ("CHARTER.md", "# C\n[g](.github/GOVERNANCE.md)\n"),
    ):
        root = repo.parent / f"r{abs(hash((charter, body)))}"
        root.mkdir()
        run_git(["init", "-q"], root)
        put(root, charter, body)
        link = "Roles and decision-making: [GOVERNANCE.md](GOVERNANCE.md)"
        for sub in ("preview", "write"):
            extra = ["--current", sha(body), "--proposed", sha(link)] if sub == "write" else []
            result = call(capsys, root, sub, charter, "--after-line", "1", *extra,
                          stdin=link.encode())
            assert result.refusal == "charter-already-links", (charter, body)
    put(repo, "docs/CHARTER.md", "# C\n[x](other.md) and [y](../README.md)\n")
    assert call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "1",
                stdin=LINK.encode()).code == 0


@pytest.mark.parametrize(
    "text",
    [
        "", "\n", "see [GOVERNANCE.md](../GOVERNANCE.md)",
        "Roles and decision-making: [GOVERNANCE.md](../GOVERNANCE.md)\n\n",
        "Roles and decision-making: [GOVERNANCE.md](../GOVERNANCE.md)\nmore",
        "Roles and decision-making: [GOVERNANCE.md](/GOVERNANCE.md)",
        "Roles and decision-making: [GOVERNANCE.md](https://example.com/GOVERNANCE.md)",
        "Roles and decision-making: [GOVERNANCE.md](a b)",
        "Roles and decision-making: [GOVERNANCE.md](../README.md)",
        "Roles and decision-making: [GOVERNANCE.md](../../GOVERNANCE.md)",
        "Roles and decision-making: [GOVERNANCE.md]()",
        "Roles and decision-making: [GOVERNANCE.md](a(b)",
        "roles and decision-making: [GOVERNANCE.md](../GOVERNANCE.md)",
    ],
)
def test_ac_0105_not_a_link_line(
    text: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\n")
    for sub in ("preview", "write"):
        extra = ["--current", sha("# C\n"), "--proposed", sha(text)] if sub == "write" else []
        result = call(capsys, repo, sub, "docs/CHARTER.md", "--after-line", "0", *extra,
                      stdin=text.encode())
        assert result.refusal == "not-a-link-line"


@pytest.mark.parametrize("after", [None, "-1", "3", "x", "", "1.0", "01x", "٣"])
def test_ac_0106_bad_line_number(
    after: str | None, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\nline two\n")
    flag = [] if after is None else ["--after-line", after]
    for sub in ("preview", "write"):
        extra = ["--current", sha("# C\nline two\n"), "--proposed", sha(LINK)] if sub == "write" else []
        result = call(capsys, repo, sub, "docs/CHARTER.md", *flag, *extra, stdin=LINK.encode())
        assert result.refusal == "bad-line-number"


def test_ac_0106_range_ends_are_valid(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\nline two\n")
    for n in ("0", "1", "2"):
        out = call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", n,
                   stdin=LINK.encode())
        assert out.code == 0
        assert field(out.out, "Inserted at line") == str(int(n) + 1)


# --- write ------------------------------------------------------------------


def test_ac_0023_proposed_digest_must_match(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = listing(repo)
    result = call(capsys, repo, "write", "GOVERNANCE.md", "--current", "absent",
                  "--proposed", sha(DRAFT + " "), stdin=DRAFT.encode())
    assert result.refusal == "bytes-differ-from-preview"
    assert listing(repo) == before


def test_ac_0024_target_must_be_unchanged(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ("--proposed", sha(DRAFT))
    root = repo.parent / "t24"
    root.mkdir()
    run_git(["init", "-q"], root)
    put(root, "GOVERNANCE.md", "existing\n")
    before = listing(root)
    r = call(capsys, root, "write", "GOVERNANCE.md", "--current", "absent", *args,
             "--approved-by", "owner", stdin=DRAFT.encode())
    assert r.refusal == "target-changed"
    r = call(capsys, root, "write", "GOVERNANCE.md", "--current", sha("other\n"), *args,
             "--approved-by", "owner", stdin=DRAFT.encode())
    assert r.refusal == "target-changed"
    assert listing(root) == before
    (root / "GOVERNANCE.md").unlink()
    r = call(capsys, root, "write", "GOVERNANCE.md", "--current", sha("existing\n"), *args,
             "--approved-by", "owner", stdin=DRAFT.encode())
    assert r.refusal == "target-changed"
    assert not (root / "GOVERNANCE.md").exists()


def test_ac_0025_and_ac_0026_successful_write(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "README.md", "readme\n")
    put(repo, "docs/CHARTER.md", "# C\n")
    run_git(["add", "."], repo)
    before = listing(repo)
    result = call(capsys, repo, "write", "GOVERNANCE.md", "--current", "absent",
                  "--proposed", sha(DRAFT), stdin=DRAFT.encode())
    assert result.code == 0 and result.err == ""
    assert result.out == f"written: GOVERNANCE.md {sha(DRAFT)}\n"
    assert (repo / "GOVERNANCE.md").read_bytes() == DRAFT.encode()
    after = listing(repo)
    assert {k: v for k, v in after.items() if k != "GOVERNANCE.md"} == before
    assert set(after) - set(before) == {"GOVERNANCE.md"}


def test_ac_0025_overwrite_with_approval(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "GOVERNANCE.md", "old\n")
    result = call(capsys, repo, "write", "GOVERNANCE.md", "--current", sha("old\n"),
                  "--proposed", sha(DRAFT), "--approved-by", "owner decision",
                  stdin=DRAFT.encode())
    assert result.out == f"written: GOVERNANCE.md {sha(DRAFT)}\n"
    assert (repo / "GOVERNANCE.md").read_bytes() == DRAFT.encode()


def test_ac_0027_helper_receives_expect_sha256(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fs = GOV._get_file_safety()
    seen: list[tuple[pathlib.Path, bytes, str | None]] = []
    real = fs.write_confined_regular_file

    def spy(root: pathlib.Path, path: pathlib.Path, data: bytes, *, expect_sha256: str | None) -> None:
        seen.append((path, data, expect_sha256))
        real(root, path, data, expect_sha256=expect_sha256)

    monkeypatch.setattr(fs, "write_confined_regular_file", spy)
    call(capsys, repo, "write", "CODEOWNERS", "--current", "absent", "--proposed",
         sha("# a\n"), "--approved-by", "owner", stdin=b"# a\n")
    old = hashlib.sha256(b"# a\n").hexdigest()
    call(capsys, repo, "write", "CODEOWNERS", "--current", f"sha256:{old}", "--proposed",
         sha("# b\n"), "--approved-by", "owner", stdin=b"# b\n")
    assert [(p.name, d, e) for p, d, e in seen] == [
        ("CODEOWNERS", b"# a\n", None), ("CODEOWNERS", b"# b\n", old),
    ]


def test_ac_0117_helper_failure_refuses_write_failed(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fs = GOV._get_file_safety()

    def fail(*_: object, **__: object) -> None:
        raise fs.UnsafeContentError("nope")

    monkeypatch.setattr(fs, "write_confined_regular_file", fail)
    result = call(capsys, repo, "write", "CODEOWNERS", "--current", "absent",
                  "--proposed", sha("# a\n"), "--approved-by", "owner", stdin=b"# a\n")
    assert result.code == 3 and result.refusal == "write-failed"


@pytest.mark.parametrize("charter", ["# C\nline two\nline three\n", "# C\nno newline", "", "one"])
def test_ac_0028_charter_write_matches_preview(
    charter: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", charter)
    lines = charter.count("\n") + (1 if charter and not charter.endswith("\n") else 0)
    for n in range(lines + 1):
        put(repo, "docs/CHARTER.md", charter)
        args = ("docs/CHARTER.md", "--after-line", str(n))
        current = sha(charter)
        preview = call(capsys, repo, "preview", *args, stdin=(LINK + "\n").encode())
        assert preview.code == 0
        proposed = field(preview.out, "Proposed").split(" ")[0]
        result = call(capsys, repo, "write", *args, "--current", current,
                      "--proposed", proposed, stdin=(LINK + "\n").encode())
        assert result.code == 0, result.out
        written = (repo / "docs/CHARTER.md").read_bytes()
        assert sha(written) == proposed
        parts = charter.split("\n")
        parts = parts[:-1] if parts[-1] == "" else parts
        tail = "\n" if n == lines or charter.endswith("\n") else ""
        expected = "\n".join(parts[:n] + [LINK] + parts[n:]) + tail
        assert written.decode() == expected


def test_ac_0028_charter_without_final_newline_gets_one_added(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CHARTER.md", "# C\nlast")
    link = "Roles and decision-making: [GOVERNANCE.md](GOVERNANCE.md)"
    out = call(capsys, repo, "preview", "CHARTER.md", "--after-line", "2", stdin=link.encode())
    expected = f"# C\nlast\n{link}\n"
    assert field(out.out, "Proposed") == f"{sha(expected)} ({len(expected)} bytes)"
    assert section(out.out, "--- content ---", "--- end content ---")[:3] == ["# C", "last", link]


# --- CLI behaviour ----------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        [], ["bogus"], ["show"], ["show", "--root", "."], ["preview", "--target", "CODEOWNERS"],
        ["show", "--root", ".", "--target", "CODEOWNERS", "--approved-by", "x"],
        ["write", "--root", ".", "--target", "CODEOWNERS"],
        ["write", "--root", ".", "--target", "CODEOWNERS", "--current", "nope", "--proposed", "sha256:" + "0" * 64],
        ["write", "--root", ".", "--target", "CODEOWNERS", "--current", "absent", "--proposed", "sha256:xyz"],
        ["preview", "--root", ".", "--target", "CODEOWNERS", "--extra"],
    ],
)
def test_ac_0029_usage_errors(
    argv: list[str], repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    code = GOV.main(argv, b"", repo)
    captured = capsys.readouterr()
    assert code == 2 and captured.out == "" and captured.err != ""


def test_ac_0030_exit_codes(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert call(capsys, repo, "show", "CODEOWNERS").code == 0
    assert call(capsys, repo, "show", "README.md").code == 3
    assert call(capsys, repo, "preview", "CODEOWNERS", stdin=b"bad[ @a\n").code == 3
    assert call(capsys, repo, "preview", "CODEOWNERS", stdin=b"# ok\n").code == 0


def test_ac_0031_utf8_output_under_the_c_locale(
    repo: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHONIO", "PYTHONUTF8", "PYTHONCOERCE"))}
    env["LC_ALL"] = "C"
    env["PYTHONCOERCECLOCALE"] = "0"
    env["PYTHONUTF8"] = "0"
    proposed = "# café \u200b\n/x @a\n"
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "governance.py"), "preview", "--root", str(repo),
         "--target", "CODEOWNERS", "--approved-by", "ok é"],
        input=proposed.encode("utf-8"), cwd=repo, env=env, capture_output=True, check=False,
    )
    assert done.returncode == 0, done.stderr
    text = done.stdout.decode("utf-8")
    assert "# café ⟨U+200B⟩" in text
    assert "- Approved by: ok é" in text
    shown = subprocess.run(
        [sys.executable, str(SCRIPTS / "governance.py"), "show", "--root", str(repo),
         "--target", "CODEOWNERS"],
        cwd=repo, env=env, capture_output=True, check=False,
    )
    assert shown.returncode == 0 and b"GOVERNANCE CURRENT:" in shown.stdout


# --- amended refusal order, parent directories, long numbers ------------------

UNSET = "sha256:" + "0" * 64


def write_call(
    capsys: pytest.CaptureFixture[str], root: pathlib.Path, target: str, stdin: bytes,
    current: str = "absent", proposed: str | None = None, *extra: str,
) -> Result:
    """Run ``write`` with well-formed arguments."""
    return call(capsys, root, "write", target, *extra, "--current", current,
                "--proposed", proposed or sha(stdin), stdin=stdin)


def test_ac_0116_and_ac_0120_missing_parent(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = listing(repo)
    for target, text in ((".github/GOVERNANCE.md", DRAFT), (".github/CODEOWNERS", "/a @b\n")):
        shown = call(capsys, repo, "show", target)
        assert shown.code == 0 and field(shown.out, "Current") == "absent"
        assert call(capsys, repo, "preview", target, stdin=text.encode()).refusal == "parent-missing"
        assert write_call(capsys, repo, target, text.encode()).refusal == "parent-missing"
    assert listing(repo) == before
    assert not (repo / ".github").exists()


@pytest.mark.parametrize("sub", ["show", "preview", "write"])
@pytest.mark.parametrize("shape", ["file", "dangling"])
def test_ac_0125_and_ac_0003_unsafe_parent_component(
    sub: str, shape: str, repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    if shape == "file":
        put(repo, ".github", "not a directory\n")
    else:
        (repo / ".github").symlink_to(repo.parent / "no-such-dir")
    proposal = b"/a @b\n"
    extra = ["--current", "absent", "--proposed", sha(proposal)] if sub == "write" else []
    result = call(capsys, repo, sub, ".github/CODEOWNERS", *extra, stdin=proposal)
    assert result.refusal == "unsafe-path"
    assert "absent" not in result.out


def test_ac_0121_charter_cases_without_parent(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    link = LINK.encode()
    assert call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "0",
                stdin=link).refusal == "charter-missing"
    put(repo, "CHARTER.md", "# C\n")
    assert call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "0",
                stdin=link).refusal == "not-the-charter"
    assert call(capsys, repo, "preview", ".github/CODEOWNERS",
                stdin=b"/bad[ @a\n").refusal == "invalid-codeowners-line 1"
    assert call(capsys, repo, "preview", ".github/CODEOWNERS",
                stdin=b"/a @a\n").refusal == "parent-missing"
    assert call(capsys, repo, "preview", ".github/GOVERNANCE.md",
                stdin=b"incomplete\n").refusal == "governance-draft-incomplete"


def test_ac_0121_charter_changed_after_preview(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    original = "# C\nline two\n"
    put(repo, "docs/CHARTER.md", original)
    out = call(capsys, repo, "preview", "docs/CHARTER.md", "--after-line", "2", stdin=LINK.encode()).out
    current, proposed = field(out, "Current"), field(out, "Proposed").split(" ")[0]

    def attempt() -> str | None:
        return call(capsys, repo, "write", "docs/CHARTER.md", "--after-line", "2",
                    "--current", current, "--proposed", proposed, stdin=LINK.encode()).refusal

    for change in (
        lambda: put(repo, "docs/CHARTER.md", "# rewritten\nline two\n"),
        lambda: put(repo, "docs/CHARTER.md", "# C\n"),
        lambda: put(repo, "docs/CHARTER.md", original + "See [g](../GOVERNANCE.md)\n"),
        lambda: (repo / "docs/CHARTER.md").unlink(),
    ):
        change()
        assert attempt() == "target-changed"
        put(repo, "docs/CHARTER.md", original)


def test_ac_0121_target_deleted_with_its_parent_after_preview(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, ".github/GOVERNANCE.md", "x\n")
    current = sha("x\n")
    (repo / ".github/GOVERNANCE.md").unlink()
    (repo / ".github").rmdir()
    result = write_call(capsys, repo, ".github/GOVERNANCE.md", DRAFT.encode(), current)
    assert result.refusal == "target-changed"


@pytest.mark.parametrize("sub", ["preview", "write"])
def test_ac_0121_adjacent_pairs_before_the_file_reads(
    sub: str, repo: pathlib.Path, tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    extra = ["--current", "absent", "--proposed", UNSET] if sub == "write" else []
    other = tmp_path / "other"
    other.mkdir()
    run_git(["init", "-q"], other)
    # root-not-worktree / target-not-allowed
    assert call(capsys, repo, sub, "nope", *extra, stdin=NoRead(), cwd=other).refusal == "root-not-worktree"
    # target-not-allowed / too-large
    assert call(capsys, repo, sub, "nope", *extra, stdin=b"x" * 65_537).refusal == "target-not-allowed"
    # too-large / not-utf8
    assert call(capsys, repo, sub, "GOVERNANCE.md", *extra, stdin=b"\xff" * 65_537).refusal == "too-large"
    # not-utf8 / refused-character
    assert call(capsys, repo, sub, "GOVERNANCE.md", *extra, stdin=b"\xff\x07").refusal == "not-utf8"
    # refused-character / invalid-approval
    assert call(capsys, repo, sub, "GOVERNANCE.md", *extra, "--approved-by", "",
                stdin=b"\x07").refusal == "refused-character"
    # invalid-approval / unsafe-path
    (repo / "GOVERNANCE.md").symlink_to(repo.parent / "gone")
    assert call(capsys, repo, sub, "GOVERNANCE.md", *extra, "--approved-by", "",
                stdin=DRAFT.encode()).refusal == "invalid-approval"


def test_ac_0121_unsafe_path_before_too_large_within_a_file(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "GOVERNANCE.md", b"#" * 3_000_000)
    os.link(repo / "GOVERNANCE.md", repo / "hard.md")
    result = call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode())
    assert result.refusal == "unsafe-path"


def test_ac_0121_files_are_read_in_listing_order(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "GOVERNANCE.md", b"#" * 3_000_000)
    put(repo, "docs/real.md", "# C\n")
    (repo / "docs/CHARTER.md").symlink_to(repo / "docs/real.md")
    assert call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode()).refusal == "too-large"
    (repo / "GOVERNANCE.md").write_bytes(b"ok\n")
    assert call(capsys, repo, "preview", "GOVERNANCE.md", stdin=DRAFT.encode()).refusal == "unsafe-path"


def test_ac_0121_last_file_unsafe_before_target_changed(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "CHARTER.md").symlink_to(repo / "elsewhere.md")
    result = write_call(capsys, repo, "GOVERNANCE.md", DRAFT.encode(), sha("stale\n"))
    assert result.refusal == "unsafe-path"


def test_ac_0121_target_changed_before_each_kind_check(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stale = sha("stale\n")
    assert write_call(capsys, repo, "GOVERNANCE.md", b"incomplete\n", stale).refusal == "target-changed"
    assert write_call(capsys, repo, "CODEOWNERS", b"/bad[ @a\n", stale).refusal == "target-changed"
    put(repo, "docs/CHARTER.md", "# C\nSee [g](GOVERNANCE.md)\n")
    result = call(capsys, repo, "write", "docs/CHARTER.md", "--after-line", "0",
                  "--current", stale, "--proposed", UNSET, stdin=LINK.encode())
    assert result.refusal == "target-changed"


def test_ac_0121_inside_the_charter_kind_checks(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\nSee [g](GOVERNANCE.md)\n")
    put(repo, "CHARTER.md", "# D\n")

    def prev(target: str, text: bytes, *flag: str) -> str | None:
        return call(capsys, repo, "preview", target, *flag, stdin=text).refusal

    assert prev("CHARTER.md", b"not a link", "--after-line", "99") == "not-the-charter"
    assert prev("docs/CHARTER.md", b"not a link", "--after-line", "99") == "not-a-link-line"
    assert prev("docs/CHARTER.md", LINK.encode(), "--after-line", "99") == "bad-line-number"
    assert prev("docs/CHARTER.md", LINK.encode(), "--after-line", "0") == "charter-already-links"


def test_ac_0121_parent_missing_before_bytes_differ(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = write_call(capsys, repo, ".github/CODEOWNERS", b"/a @b\n", "absent", UNSET)
    assert result.refusal == "parent-missing"


def test_ac_0121_bytes_differ_before_approval_required(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "CODEOWNERS", "/a @b\n")
    result = write_call(capsys, repo, "CODEOWNERS", b"/a @c\n", sha("/a @b\n"), UNSET)
    assert result.refusal == "bytes-differ-from-preview"
    result = write_call(capsys, repo, "CODEOWNERS", b"/a @c\n", sha("/a @b\n"))
    assert result.refusal == "approval-required"


def test_ac_0106_very_long_after_line_is_a_refusal(
    repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    put(repo, "docs/CHARTER.md", "# C\n")
    for sub in ("preview", "write"):
        extra = ["--current", sha("# C\n"), "--proposed", UNSET] if sub == "write" else []
        result = call(capsys, repo, sub, "docs/CHARTER.md", "--after-line", "9" * 4301,
                      *extra, stdin=LINK.encode())
        assert result.code == 3 and result.refusal == "bad-line-number"
        assert result.err == ""


def test_ac_0031_arguments_decoded_by_a_non_utf8_locale_are_recovered() -> None:
    escaped = b"ok \xc3\xa9".decode("ascii", "surrogateescape")
    assert GOV._utf8_argv(["--approved-by", escaped]) == ["--approved-by", "ok é"]
    assert GOV._utf8_argv(["plain"]) == ["plain"]
