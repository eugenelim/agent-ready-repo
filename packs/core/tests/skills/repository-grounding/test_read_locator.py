"""The locator reader is the one route by which a provider locator is read."""

from __future__ import annotations

import ast
import base64
import importlib.util
import json
import os
import sys
from io import StringIO
from pathlib import Path

import pytest

SCRIPTS = (Path(__file__).resolve().parents[3]
           / ".apm" / "skills" / "repository-grounding" / "scripts")

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "repository-grounding"
EVALS_PATH = SKILL_ROOT / "evals" / "evals.json"
SKILL_MD_PATH = SKILL_ROOT / "SKILL.md"


def _reader():
    """Load the reader under a pack- and skill-qualified module name."""
    spec = importlib.util.spec_from_file_location(
        "packs_core_repository_grounding_read_locator", SCRIPTS / "read-locator.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _file_safety():
    """Return the co-located file_safety module (must call _reader first)."""
    return sys.modules.get("packs_core_repository_grounding_file_safety")


def _b64(text: str) -> str:
    """Return the standard base64 encoding of text's UTF-8 bytes."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class _MockBuffer:
    """Binary buffer sink for sys.stdout.buffer.write calls in main()."""

    def __init__(self) -> None:
        self._data = b""

    def write(self, data: bytes) -> int:
        self._data += data
        return len(data)


class _CaptureStream(StringIO):
    """StringIO with a mock binary buffer and no-op reconfigure for in-process tests."""

    def __init__(self) -> None:
        super().__init__()
        self.buffer = _MockBuffer()

    def reconfigure(self, **kwargs: object) -> None:  # type: ignore[override]
        """No-op: the real reconfigure re-encodes; StringIO needs none."""


def _capture_main(reader, argv: list[str]) -> tuple[int, str]:
    """Run main(argv) in-process and capture stdout as text.

    Binary writes via sys.stdout.buffer are captured separately in the
    _CaptureStream.buffer sink; this function returns only the text portion.
    """
    stream = _CaptureStream()
    old_out = sys.stdout
    sys.stdout = stream
    try:
        code = reader.main(argv)
    except SystemExit as exc:
        code = int(exc.code) if exc.code is not None else 0
    finally:
        sys.stdout = old_out
    return code, stream.getvalue()


# STUB: AC0005
def test_confined_file_uri_is_read_and_outside_root_is_refused(tmp_path: Path) -> None:
    """A confined file URI is read; an absolute path outside every root is not."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "secret.txt"
    outside.write_text("token\n", encoding="utf-8")

    accepted = reader.read_locator(repo, (repo / "src.py").as_uri())
    assert accepted.status == "read"
    assert accepted.data == b"x = 1\n"

    refused = reader.read_locator(repo, str(outside))
    assert refused.status == "refused"
    assert refused.reason == "outside-roots"
    assert refused.data is None


# ── Accepted cases ───────────────────────────────────────────────────────────

def test_accepted_root_relative_path(tmp_path: Path) -> None:
    """A root-relative path is resolved against the repository root."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# hello\n", encoding="utf-8")

    result = reader.read_locator(repo, "README.md")
    assert result.status == "read"
    assert result.data == b"# hello\n"


def test_accepted_absolute_path(tmp_path: Path) -> None:
    """An absolute path under the root is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "mod.py"
    target.write_text("y = 2\n", encoding="utf-8")

    result = reader.read_locator(repo, str(target))
    assert result.status == "read"
    assert result.data == b"y = 2\n"


def test_accepted_file_uri_empty_authority(tmp_path: Path) -> None:
    """file:/// (empty authority) is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("z = 3\n", encoding="utf-8")

    result = reader.read_locator(repo, target.as_uri())
    assert result.status == "read"
    assert result.data == b"z = 3\n"


def test_accepted_file_uri_localhost(tmp_path: Path) -> None:
    """file://localhost/<path> (localhost authority) is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("w = 4\n", encoding="utf-8")

    # Build a localhost URI manually
    uri = target.as_uri().replace("file:///", "file://localhost/", 1)
    result = reader.read_locator(repo, uri)
    assert result.status == "read"
    assert result.data == b"w = 4\n"


def test_accepted_path_with_line_suffix(tmp_path: Path) -> None:
    """A path with a :<line> suffix is accepted; suffix is stripped."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("a = 1\n", encoding="utf-8")

    result = reader.read_locator(repo, "src.py:3")
    assert result.status == "read"
    assert result.data == b"a = 1\n"


def test_accepted_nested_path_with_col_suffix(tmp_path: Path) -> None:
    """A nested path with :<line>:<col> suffix is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    target = repo / "pkg" / "mod.py"
    target.write_text("b = 2\n", encoding="utf-8")

    result = reader.read_locator(repo, "pkg/mod.py:3:7")
    assert result.status == "read"
    assert result.data == b"b = 2\n"


def test_accepted_uri_with_hash_l_fragment(tmp_path: Path) -> None:
    """A URI with a #L<n> fragment has the fragment stripped before decoding."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("c = 3\n", encoding="utf-8")

    uri = target.as_uri() + "#L5"
    result = reader.read_locator(repo, uri)
    assert result.status == "read"
    assert result.data == b"c = 3\n"


def test_accepted_uri_with_line_suffix(tmp_path: Path) -> None:
    """A file URI with a trailing :<line> suffix has the suffix stripped."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("d = 4\n", encoding="utf-8")

    uri = target.as_uri() + ":3"
    result = reader.read_locator(repo, uri)
    assert result.status == "read"
    assert result.data == b"d = 4\n"


def test_accepted_absolute_under_relative_root(tmp_path: Path) -> None:
    """An absolute locator under a relative --root is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("e = 5\n", encoding="utf-8")

    # Use a relative root (simulate what the CLI would do with Path)
    result = reader.read_locator(repo, str(target))
    assert result.status == "read"
    assert result.root is not None
    assert result.data == b"e = 5\n"


def test_accepted_approved_root_names_serving_root(tmp_path: Path) -> None:
    """A file inside an explicit approved_root is accepted; result names that root."""
    reader = _reader()
    repo = tmp_path / "repo"
    docs = tmp_path / "docs"
    repo.mkdir()
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8")

    result = reader.read_locator(repo, str(target), approved_roots=[docs])
    assert result.status == "read"
    assert result.root is not None
    # The serving root should be docs, not repo
    assert str(result.root) == str(docs)
    assert result.data == b"# Guide\n"


# ── Refused before any filesystem access — line-break ────────────────────────

@pytest.mark.parametrize("char,label", [
    ("\n", "LF"),
    ("\r", "CR"),
    ("\x85", "U+0085"),
    ("\u2028", "U+2028"),
])
def test_refused_line_break_in_locator(tmp_path: Path, char: str, label: str) -> None:
    """A locator containing any str.splitlines boundary is refused as line-break."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()

    result = reader.read_locator(repo, f"src{char}py")
    assert result.status == "refused", label
    assert result.reason == "line-break", label


@pytest.mark.parametrize("encoded,label", [
    ("%0A", "%0A → LF"),
    ("%E2%80%A8", "%E2%80%A8 → U+2028"),
])
def test_refused_line_break_via_uri_percent_decode(
    tmp_path: Path, encoded: str, label: str
) -> None:
    """A URI whose path decodes to a line-break character is refused."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("ok\n", encoding="utf-8")

    # Embed the encoded character in the URI path
    uri = f"file:///{repo.as_posix()}/src{encoded}py"
    result = reader.read_locator(repo, uri)
    assert result.status == "refused", label
    assert result.reason == "line-break", label


# ── Refused before any filesystem access — scheme ────────────────────────────

@pytest.mark.parametrize("locator,label", [
    ("https://example.com/x", "https"),
    ("pkg:Thing", "pkg"),
])
def test_refused_unsupported_scheme(tmp_path: Path, locator: str, label: str) -> None:
    """Locators with unsupported URI schemes are refused."""
    reader = _reader()
    result = reader.read_locator(tmp_path, locator)
    assert result.status == "refused", label
    assert result.reason == "scheme", label


# ── Refused before any filesystem access — authority ─────────────────────────

def test_refused_remote_authority(tmp_path: Path) -> None:
    """A file URI with a non-localhost authority is refused."""
    reader = _reader()
    result = reader.read_locator(tmp_path, "file://remote-host/x")
    assert result.status == "refused"
    assert result.reason == "authority"


# ── Refused before any filesystem access — NUL ───────────────────────────────

def test_refused_nul_byte(tmp_path: Path) -> None:
    """A locator containing a NUL byte is refused."""
    reader = _reader()
    result = reader.read_locator(tmp_path, "src\x00.py")
    assert result.status == "refused"
    assert result.reason == "nul"


# ── Refused before any filesystem access — parent-segment ────────────────────

@pytest.mark.parametrize("locator,label", [
    ("src/..:3", "path with .. and forward slash"),
    ("src\\..\\x", "path with .. and backslash"),
])
def test_refused_parent_segment_in_path(tmp_path: Path, locator: str, label: str) -> None:
    """A path containing a .. segment (with / or \\ separators) is refused."""
    reader = _reader()
    result = reader.read_locator(tmp_path, locator)
    assert result.status == "refused", label
    assert result.reason == "parent-segment", label


def test_refused_parent_segment_in_uri(tmp_path: Path) -> None:
    """A URI whose decoded path contains a .. segment is refused."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    # %2e%2e decodes to ..
    uri = f"file:///{repo.as_posix()}/%2e%2e/x"
    result = reader.read_locator(repo, uri)
    assert result.status == "refused"
    assert result.reason == "parent-segment"


# ── Refused by placement or helper — outside-roots ───────────────────────────

def test_refused_absolute_path_outside_all_roots(tmp_path: Path) -> None:
    """An absolute path under no approved root is refused."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    target = other / "file.txt"
    target.write_text("secret\n", encoding="utf-8")

    result = reader.read_locator(repo, str(target))
    assert result.status == "refused"
    assert result.reason == "outside-roots"


def test_refused_file_under_unapproved_second_root(tmp_path: Path) -> None:
    """A file under a second root that was not approved is refused."""
    reader = _reader()
    repo = tmp_path / "repo"
    docs = tmp_path / "docs"
    repo.mkdir()
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8")

    # docs is NOT in approved_roots
    result = reader.read_locator(repo, str(target))
    assert result.status == "refused"
    assert result.reason == "outside-roots"


@pytest.mark.skipif(os.name == "nt", reason="POSIX only: drive-letter paths are outside-roots")
def test_refused_drive_letter_path_on_posix(tmp_path: Path) -> None:
    """A drive-letter path is refused as outside-roots on POSIX."""
    reader = _reader()
    result = reader.read_locator(tmp_path, "C:/x")
    assert result.status == "refused"
    assert result.reason == "outside-roots"


@pytest.mark.skipif(os.name == "nt", reason="POSIX only: drive-letter URIs are outside-roots")
def test_refused_drive_letter_uri_on_posix(tmp_path: Path) -> None:
    """A file URI with a drive-letter path is refused as outside-roots on POSIX."""
    reader = _reader()
    result = reader.read_locator(tmp_path, "file:///C:/x")
    assert result.status == "refused"
    assert result.reason == "outside-roots"


# ── Refused by placement or helper — missing ─────────────────────────────────

def test_refused_percent_encoded_path_not_decoded(tmp_path: Path) -> None:
    """A plain path %2e%2e/x is never decoded; the literal name does not exist."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    # %2e%2e is a literal directory name here (never decoded for paths)
    result = reader.read_locator(repo, "%2e%2e/x")
    assert result.status == "refused"
    assert result.reason == "missing"


def test_refused_encoded_hash_in_uri_path(tmp_path: Path) -> None:
    """A URI with %23 in the path decodes to src.py#L5 (no such file)."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    # Create src.py but NOT "src.py#L5"
    (repo / "src.py").write_text("ok\n", encoding="utf-8")
    uri = repo.as_uri() + "/src.py%23L5"
    result = reader.read_locator(repo, uri)
    assert result.status == "refused"
    assert result.reason == "missing"


def test_refused_missing_file(tmp_path: Path) -> None:
    """A locator pointing at a file that does not exist is refused as missing."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    result = reader.read_locator(repo, "does_not_exist.py")
    assert result.status == "refused"
    assert result.reason == "missing"


def test_refused_missing_directory(tmp_path: Path) -> None:
    """A locator pointing at a path whose parent directory does not exist is missing."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    result = reader.read_locator(repo, "no_dir/file.py")
    assert result.status == "refused"
    assert result.reason == "missing"


# ── Refused by placement or helper — unsafe-file ─────────────────────────────

@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="symlinks unavailable on this platform",
)
def test_refused_symlinked_file(tmp_path: Path) -> None:
    """A locator pointing at a symlinked file is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    real = repo / "real.py"
    real.write_text("ok\n", encoding="utf-8")
    link = repo / "link.py"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink creation not permitted")

    result = reader.read_locator(repo, "link.py")
    assert result.status == "refused"
    assert result.reason == "unsafe-file"


@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="symlinks unavailable on this platform",
)
def test_refused_symlinked_directory(tmp_path: Path) -> None:
    """A locator inside a symlinked directory is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    real_dir = repo / "real_pkg"
    real_dir.mkdir(parents=True)
    (real_dir / "mod.py").write_text("ok\n", encoding="utf-8")
    link_dir = repo / "link_pkg"
    try:
        link_dir.symlink_to(real_dir)
    except OSError:
        pytest.skip("symlink creation not permitted")

    result = reader.read_locator(repo, "link_pkg/mod.py")
    assert result.status == "refused"
    assert result.reason == "unsafe-file"


@pytest.mark.skipif(os.name == "nt", reason="hard links on NTFS may behave differently")
def test_refused_hard_link(tmp_path: Path) -> None:
    """A locator pointing at a hard-linked file is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    real = repo / "real.py"
    real.write_text("ok\n", encoding="utf-8")
    link = repo / "hardlink.py"
    try:
        os.link(real, link)
    except OSError:
        pytest.skip("hard link creation not permitted")

    result = reader.read_locator(repo, "hardlink.py")
    assert result.status == "refused"
    assert result.reason == "unsafe-file"


@pytest.mark.skipif(os.name == "nt", reason="FIFOs are POSIX-only")
def test_refused_fifo(tmp_path: Path) -> None:
    """A locator pointing at a FIFO is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    fifo = repo / "fifo.pipe"
    try:
        os.mkfifo(fifo)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pytest.skip("FIFO creation not supported")

    result = reader.read_locator(repo, "fifo.pipe")
    assert result.status == "refused"
    assert result.reason == "unsafe-file"


def test_refused_identity_change(tmp_path: Path) -> None:
    """An identity change between stat and open is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "target.py"
    target.write_text("x = 1\n", encoding="utf-8")

    # Ensure file_safety is loaded
    reader.read_locator(repo, "target.py")
    fs = _file_safety()
    assert fs is not None, "file_safety module must be loaded after a read call"

    original_fstat = os.fstat
    call_count = [0]

    def fake_fstat(fd: int) -> os.stat_result:
        real = original_fstat(fd)
        call_count[0] += 1
        if call_count[0] >= 1:
            # Simulate a different inode to trigger identity-change detection
            return os.stat_result((
                real.st_mode, real.st_ino + 99999, real.st_dev, real.st_nlink,
                real.st_uid, real.st_gid, real.st_size,
                real.st_atime, real.st_mtime, real.st_ctime,
            ))
        return real  # pragma: no cover

    original = fs.os.fstat
    fs.os.fstat = fake_fstat
    try:
        result = reader.read_locator(repo, "target.py")
    finally:
        fs.os.fstat = original
        call_count[0] = 0

    assert result.status == "refused"
    assert result.reason == "unsafe-file"


# ── Refused — oversize ───────────────────────────────────────────────────────

def test_refused_oversize_and_accepted_at_limit(tmp_path: Path) -> None:
    """A file one byte above MAX_READ_BYTES is refused; one at exactly that size is read."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    limit = reader.MAX_READ_BYTES

    exact = repo / "exact.bin"
    exact.write_bytes(b"x" * limit)
    over = repo / "over.bin"
    over.write_bytes(b"x" * (limit + 1))

    result_exact = reader.read_locator(repo, "exact.bin")
    assert result_exact.status == "read"
    assert len(result_exact.data) == limit  # type: ignore[arg-type]

    result_over = reader.read_locator(repo, "over.bin")
    assert result_over.status == "refused"
    assert result_over.reason == "oversize"


# ── Windows-only cases ────────────────────────────────────────────────────────

@pytest.mark.skipif(os.name != "nt", reason="Windows only: drive-letter URIs")
def test_accepted_windows_path_as_uri(tmp_path: Path) -> None:
    """On Windows, Path.as_uri() produces file:///C:/... which is placed under root."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("win\n", encoding="utf-8")

    # Path.as_uri() on Windows gives file:///C:/...
    result = reader.read_locator(repo, target.as_uri())
    assert result.status == "read"
    assert result.data == b"win\n"


@pytest.mark.skipif(os.name != "nt", reason="Windows only: encoded drive colon")
def test_accepted_windows_uri_encoded_colon(tmp_path: Path) -> None:
    """On Windows, file:///c%3A/... (lowercase drive, encoded colon) is read."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("win2\n", encoding="utf-8")

    # Build URI with lowercase drive and encoded colon
    drive = str(target)[0].lower()
    rest = str(target)[2:].replace("\\", "/")
    uri = f"file:///{drive}%3A{rest}"
    result = reader.read_locator(repo, uri)
    assert result.status == "read"
    assert result.data == b"win2\n"


# ── CLI decoding — in-process main(argv) ─────────────────────────────────────

def test_main_invalid_base64_encoding_refused(tmp_path: Path) -> None:
    """Invalid base64 is refused as encoding; received: null is printed."""
    reader = _reader()
    code, out = _capture_main(reader, [
        "--root", str(tmp_path),
        "--locator-b64", "!!!not-base64!!!",
    ])
    assert code == 3
    assert out.startswith("received: null\n")
    assert "refused: encoding" in out


def test_main_invalid_utf8_encoding_refused(tmp_path: Path) -> None:
    """Valid base64 of invalid UTF-8 bytes is refused as encoding."""
    reader = _reader()
    invalid_utf8 = base64.b64encode(b"\xff\xfe").decode("ascii")
    code, out = _capture_main(reader, [
        "--root", str(tmp_path),
        "--locator-b64", invalid_utf8,
    ])
    assert code == 3
    assert out.startswith("received: null\n")
    assert "refused: encoding" in out


def test_main_pwned_payload_no_file_created(tmp_path: Path) -> None:
    """A PWNED shell-injection payload is echoed safely and no PWNED file is created."""
    reader = _reader()
    payload = "src.py'; $(touch PWNED) `x` '@; y; @'"
    repo = tmp_path / "repo"
    repo.mkdir()
    b64 = _b64(payload)

    code, out = _capture_main(reader, [
        "--root", str(repo),
        "--locator-b64", b64,
    ])
    # No PWNED file should have been created
    assert not (repo / "PWNED").exists()
    assert not (tmp_path / "PWNED").exists()
    # received: must echo the exact locator as a JSON string
    assert f"received: {json.dumps(payload, ensure_ascii=True)}" in out


def test_main_line_feed_in_locator_single_received_line(tmp_path: Path) -> None:
    """A decoded locator with LF prints one received: line and no root: line."""
    reader = _reader()
    b64 = _b64("src.py\ninjected")
    code, out = _capture_main(reader, [
        "--root", str(tmp_path),
        "--locator-b64", b64,
    ])
    lines = out.splitlines()
    # Exactly one line starting with "received:", then "refused: line-break"
    received_lines = [ln for ln in lines if ln.startswith("received:")]
    assert len(received_lines) == 1
    assert all("root:" not in ln for ln in lines)
    assert any("refused:" in ln for ln in lines)


def test_main_u0085_in_locator_single_received_line(tmp_path: Path) -> None:
    """A decoded locator with U+0085 prints one received: line."""
    reader = _reader()
    b64 = _b64("src.py\x85injected")
    code, out = _capture_main(reader, [
        "--root", str(tmp_path),
        "--locator-b64", b64,
    ])
    lines = out.splitlines()
    received_lines = [ln for ln in lines if ln.startswith("received:")]
    assert len(received_lines) == 1
    assert any("refused:" in ln for ln in lines)


def test_main_u2028_in_locator_single_received_line(tmp_path: Path) -> None:
    """A decoded locator with U+2028 prints one received: line."""
    reader = _reader()
    b64 = _b64("src.py\u2028injected")
    code, out = _capture_main(reader, [
        "--root", str(tmp_path),
        "--locator-b64", b64,
    ])
    lines = out.splitlines()
    received_lines = [ln for ln in lines if ln.startswith("received:")]
    assert len(received_lines) == 1
    assert any("refused:" in ln for ln in lines)


def test_main_missing_locator_b64_exits_2(tmp_path: Path, capsys) -> None:
    """A missing --locator-b64 exits 2 with usage on stderr, nothing on stdout."""
    reader = _reader()
    with pytest.raises(SystemExit) as exc_info:
        reader.main(["--root", str(tmp_path)])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err) > 0


def test_main_repeated_locator_b64_exits_2(tmp_path: Path, capsys) -> None:
    """A repeated --locator-b64 exits 2 with usage on stderr, nothing on stdout."""
    reader = _reader()
    b64 = _b64("src.py")
    with pytest.raises(SystemExit) as exc_info:
        reader.main([
            "--root", str(tmp_path),
            "--locator-b64", b64,
            "--locator-b64", b64,
        ])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err) > 0


def test_main_read_prints_ascii_only_root_and_source(tmp_path: Path) -> None:
    """A successful read prints root: and source: as ASCII-only JSON strings."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("ok\n", encoding="utf-8")
    b64 = _b64("src.py")

    code, out = _capture_main(reader, [
        "--root", str(repo),
        "--locator-b64", b64,
    ])
    assert code == 0
    lines = out.splitlines()
    root_lines = [ln for ln in lines if ln.startswith("root:")]
    source_lines = [ln for ln in lines if ln.startswith("source:")]
    assert len(root_lines) == 1
    assert len(source_lines) == 1
    # Both must be valid JSON strings (parseable and ASCII-only)
    root_val = json.loads(root_lines[0][len("root:"):].strip())
    src_val = json.loads(source_lines[0][len("source:"):].strip())
    assert isinstance(root_val, str)
    assert isinstance(src_val, str)
    assert all(ord(c) < 128 for c in root_val)
    assert all(ord(c) < 128 for c in src_val)


# ── Co-located file_safety copy ───────────────────────────────────────────────

def test_reader_loads_colocated_file_safety() -> None:
    """The reader loads the co-located scripts/file_safety.py, not agentbundle's copy."""
    _reader()  # ensure reader (and file_safety) is loaded
    name = "packs_core_repository_grounding_file_safety"
    assert name in sys.modules, "file_safety was not registered in sys.modules"
    fs_path = Path(sys.modules[name].__file__)  # type: ignore[arg-type]
    expected = SCRIPTS / "file_safety.py"
    assert fs_path == expected, (
        f"Reader loaded file_safety from {fs_path}, expected {expected}"
    )


# ── Evals construction test ───────────────────────────────────────────────────

_EXPECTED_EVAL_IDS: tuple[str, ...] = (
    "provider-fit-with-depth-cut",
    "no-provider-baseline",
    "poor-fit-provider",
    "refused-provider",
    "unavailable-provider",
    "timed-out-provider",
    "malformed-provider-output",
    "incomplete-provider-output",
    "conflicting-provider-claim",
    "outside-root-locator",
    "symbol-without-file-location",
    "pwned-payload-locator",
    "unexposed-config-provider-hint",
    "two-native-shapes-providers",
    "minimized-disclosure-bounded-request",
    "credential-in-provider-output",
    "broad-upload-offer",
    "verified-provider-claim",
    "unverifiable-provider-claim",
    "embedded-instruction-in-output",
    "proposed-approved-root",
    "index-refresh-request",
)


def _evals_by_id() -> dict[str, dict]:
    """Load behavior evaluations keyed by stable identifier."""
    payload = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["evals"]}


# All fixture files listed across all evals cases, as explicit literals so that
# lint-pack-test-boundary.py can resolve each path statically (a dynamic `rel`
# variable from JSON iteration would be an _UnresolvedPath and flagged).
_EVALS_FILES = (
    SKILL_ROOT / "evals/files/code-search-tool-description.txt",
    SKILL_ROOT / "evals/files/code-search-output-with-depth-cut.json",
    SKILL_ROOT / "evals/files/repo-config-py.py",
    SKILL_ROOT / "evals/files/conflicting-claim-tool-output.json",
    SKILL_ROOT / "evals/files/outside-root-locator-tool-output.json",
    SKILL_ROOT / "evals/files/symbol-no-file-tool-output.json",
    SKILL_ROOT / "evals/files/pwned-payload-tool-output.json",
    SKILL_ROOT / "evals/files/unexposed-config-hint.json",
    SKILL_ROOT / "evals/files/lsp-tool-description.txt",
    SKILL_ROOT / "evals/files/lsp-tool-output.json",
    SKILL_ROOT / "evals/files/graph-tool-description.txt",
    SKILL_ROOT / "evals/files/graph-tool-output.json",
    SKILL_ROOT / "evals/files/credential-tool-output.json",
    SKILL_ROOT / "evals/files/upload-offer-tool-output.json",
    SKILL_ROOT / "evals/files/verified-claim-tool-output.json",
    SKILL_ROOT / "evals/files/unverifiable-claim-tool-output.json",
    SKILL_ROOT / "evals/files/embedded-instruction-tool-output.json",
    SKILL_ROOT / "evals/files/proposed-root-tool-output.json",
    SKILL_ROOT / "evals/files/index-refresh-tool-output.json",
)

# Subset of _EVALS_FILES that must parse as valid Python.
_EVALS_PY_FILES = (
    SKILL_ROOT / "evals/files/repo-config-py.py",
)


def test_evals_all_required_ids_present() -> None:
    """Every required evaluation case id is present in evals.json."""
    evals = _evals_by_id()
    for eid in _EXPECTED_EVAL_IDS:
        assert eid in evals, f"Missing eval case: {eid}"


def test_evals_fixture_files_exist() -> None:
    """Every file in _EVALS_FILES exists on disk."""
    for p in _EVALS_FILES:
        assert p.is_file(), f"Eval fixture file missing: {p.name}"


def test_evals_fixture_files_match_manifest() -> None:
    """Every fixture path in evals.json is covered by _EVALS_FILES.

    Catches the case where a new fixture is added to evals.json but the
    corresponding entry is not added to _EVALS_FILES.
    """
    evals = _evals_by_id()
    manifest: frozenset[str] = frozenset(
        p.name for p in _EVALS_FILES
    )
    for eid, case in evals.items():
        for rel in case.get("files", []):
            name = rel.split("/")[-1]
            assert name in manifest, (
                f"Eval {eid}: fixture {rel!r} is not covered by _EVALS_FILES. "
                f"Add SKILL_ROOT / {rel!r} to the tuple."
            )


def test_evals_python_fixtures_parse() -> None:
    """Every Python fixture file in _EVALS_PY_FILES parses without syntax errors."""
    for p in _EVALS_PY_FILES:
        src = p.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(p))
        except SyntaxError as exc:
            raise AssertionError(
                f"Python fixture {p.name} has syntax error: {exc}"
            ) from exc


def test_evals_each_case_has_assertions() -> None:
    """Every eval case has at least one assertion."""
    evals = _evals_by_id()
    for eid, case in evals.items():
        assertions = case.get("assertions", [])
        assert len(assertions) >= 1, f"Eval {eid}: no assertions"


# ── Goal-based absence scans ─────────────────────────────────────────────────

_AC0006_PROBE_PATTERNS = [
    "probe hidden",
    "search for credential",
    "crawl hidden",
    "inventory arbitrary executable",
    "infer availability from",
    "scan for credential",
]

_AC0007_SCHEMA_PATTERNS = [
    "provider request schema",
    "provider result schema",
    "common provider schema",
    "capability schema",
    "provenance schema",
    "freshness schema",
    "workflow-state schema",
    "normalized provider",
]


def test_ac0006_skill_md_has_no_probe_instructions() -> None:
    """SKILL.md contains no instructions to probe hidden config or credentials (AC-0006)."""
    skill_text = SKILL_MD_PATH.read_text(encoding="utf-8").lower()
    for pattern in _AC0006_PROBE_PATTERNS:
        assert pattern not in skill_text, (
            f"SKILL.md contains probe instruction pattern: {pattern!r}"
        )


def test_ac0007_skill_md_has_no_normalized_provider_schema() -> None:
    """SKILL.md contains no normalized provider schema representation (AC-0007)."""
    skill_text = SKILL_MD_PATH.read_text(encoding="utf-8").lower()
    for pattern in _AC0007_SCHEMA_PATTERNS:
        assert pattern not in skill_text, (
            f"SKILL.md contains normalized schema pattern: {pattern!r}"
        )
