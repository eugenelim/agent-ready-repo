"""Exploration reads provider locators through grounding's reader, with its own ceiling."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import sys
from io import StringIO
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
SKILL_ROOT = SKILLS / "repository-exploration"
SKILL_MD_PATH = SKILL_ROOT / "SKILL.md"


def _reader():
    """Load the exploration reader under a pack- and skill-qualified module name."""
    name = "packs_core_repository_exploration_read_locator"
    if name in sys.modules:
        del sys.modules[name]
    # Also clear the cached grounding reader so the default path is re-checked.
    grounding_name = "packs_core_repository_exploration_grounding_reader"
    sys.modules.pop(grounding_name, None)
    spec = importlib.util.spec_from_file_location(
        name,
        SKILLS / "repository-exploration" / "scripts" / "read-locator.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


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


def _capture_main(
    reader,
    argv: list[str],
    *,
    sibling_path: Path | None = None,
) -> tuple[int, str, str]:
    """Run main(argv) in-process and capture stdout and stderr as text."""
    out_stream = _CaptureStream()
    err_stream = _CaptureStream()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = out_stream
    sys.stderr = err_stream
    try:
        code = reader.main(argv, _sibling_path=sibling_path)
    except SystemExit as exc:
        code = int(exc.code) if exc.code is not None else 0
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
    return code, out_stream.getvalue(), err_stream.getvalue()


# ── STUB: AC0012 ─────────────────────────────────────────────────────────────

def test_exploration_reader_applies_its_own_ceiling(tmp_path: Path) -> None:
    """A file at the declared ceiling is read; one byte more is refused."""
    reader = _reader()
    limit = reader.MAX_PROVIDER_READ_BYTES
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "at.bin").write_bytes(b"a" * limit)
    (repo / "over.bin").write_bytes(b"a" * (limit + 1))

    assert reader.read_locator(repo, "at.bin").status == "read"
    over = reader.read_locator(repo, "over.bin")
    assert over.status == "refused"
    assert over.reason == "oversize"


# ── Ceiling: monkeypatched to 16 applies the exploration value ────────────────

def test_monkeypatched_ceiling_applies_exploration_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With MAX_PROVIDER_READ_BYTES=16, 16 bytes reads and 17 bytes refuses (exploration value)."""
    reader = _reader()
    monkeypatch.setattr(reader, "MAX_PROVIDER_READ_BYTES", 16)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "small.bin").write_bytes(b"x" * 16)
    (repo / "big.bin").write_bytes(b"x" * 17)

    small = reader.read_locator(repo, "small.bin")
    assert small.status == "read"
    big = reader.read_locator(repo, "big.bin")
    assert big.status == "refused"
    assert big.reason == "oversize"


# ── Accepted cases (AC-0012) ─────────────────────────────────────────────────

def test_accepted_root_relative_path(tmp_path: Path) -> None:
    """A root-relative path is read through the grounding reader."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, "src.py")
    assert result.status == "read"
    assert result.data == b"x = 1\n"


def test_accepted_absolute_path(tmp_path: Path) -> None:
    """An absolute path under the repository root is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "mod.py"
    target.write_text("y = 2\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, str(target))
    assert result.status == "read"
    assert result.data == b"y = 2\n"


def test_accepted_file_uri(tmp_path: Path) -> None:
    """A file:/// URI pointing into the root is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "src.py"
    target.write_text("z = 3\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, target.as_uri())
    assert result.status == "read"
    assert result.data == b"z = 3\n"


def test_accepted_file_under_approved_root(tmp_path: Path) -> None:
    """A file under an explicit approved root is accepted."""
    reader = _reader()
    repo = tmp_path / "repo"
    docs = tmp_path / "docs"
    repo.mkdir()
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, str(target), approved_roots=[docs])
    assert result.status == "read"
    assert result.data == b"# Guide\n"


# ── Refused cases (AC-0012) ──────────────────────────────────────────────────

def test_refused_parent_segment(tmp_path: Path) -> None:
    """A locator with a .. segment is refused as parent-segment."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    result = reader.read_locator(repo, "src/../x")
    assert result.status == "refused"
    assert result.reason == "parent-segment"


def test_refused_absolute_outside_roots(tmp_path: Path) -> None:
    """An absolute path under no approved root is refused as outside-roots."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "other" / "secret.txt"
    outside.parent.mkdir()
    outside.write_text("token\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, str(outside))
    assert result.status == "refused"
    assert result.reason == "outside-roots"


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
    real.write_text("ok\n", encoding="utf-8", newline="\n")
    link = repo / "link.py"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink creation not permitted")
    result = reader.read_locator(repo, "link.py")
    assert result.status == "refused"
    assert result.reason == "unsafe-file"


@pytest.mark.skipif(os.name == "nt", reason="hard links on NTFS may behave differently")
def test_refused_hard_link(tmp_path: Path) -> None:
    """A locator pointing at a hard-linked file is refused as unsafe-file."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    real = repo / "real.py"
    real.write_text("ok\n", encoding="utf-8", newline="\n")
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
    target.write_text("x = 1\n", encoding="utf-8", newline="\n")

    # Prime the grounding reader by doing one successful read, then grab file_safety.
    reader.read_locator(repo, "target.py")
    grounding_name = "packs_core_repository_exploration_grounding_reader"
    gr = sys.modules.get(grounding_name)
    assert gr is not None
    # file_safety is cached in grounding's own sys.modules entry
    fs_name = "packs_core_repository_grounding_file_safety"
    fs = sys.modules.get(fs_name)
    assert fs is not None, "file_safety module must be loaded after a read call"

    original_fstat = os.fstat

    def fake_fstat(fd: int) -> os.stat_result:
        real = original_fstat(fd)
        extra = {
            name: getattr(real, name)
            for name in ("st_file_attributes", "st_reparse_tag")
            if hasattr(real, name)
        }
        return os.stat_result((
            real.st_mode, real.st_ino + 99999, real.st_dev, real.st_nlink,
            real.st_uid, real.st_gid, real.st_size,
            real.st_atime, real.st_mtime, real.st_ctime,
        ), extra)

    original = fs.os.fstat
    fs.os.fstat = fake_fstat
    try:
        result = reader.read_locator(repo, "target.py")
    finally:
        fs.os.fstat = original

    assert result.status == "refused"
    assert result.reason == "unsafe-file"


def test_refused_sub_dot_segment_below_root(tmp_path: Path) -> None:
    """A segment ending in a dot below the root is refused as parent-segment."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    result = reader.read_locator(repo, "sub./x.py")
    assert result.status == "refused"
    assert result.reason == "parent-segment"


@pytest.mark.skipif(
    os.name == "nt",
    reason="trailing-dot directory names are not creatable on Windows",
)
def test_accepted_root_with_trailing_dot_reads_absolute_locators(tmp_path: Path) -> None:
    """An absolute locator into a root whose own name ends in a dot is accepted."""
    reader = _reader()
    repo = tmp_path / "proj." / "repo"
    repo.mkdir(parents=True)
    (repo / "a.py").write_text("ok\n", encoding="utf-8", newline="\n")
    result = reader.read_locator(repo, str(repo / "a.py"))
    assert result.status == "read"
    assert result.data == b"ok\n"


# ── CLI cases (AC-0012) ──────────────────────────────────────────────────────

def test_cli_pwned_payload_no_file_created_received_exact(tmp_path: Path) -> None:
    """A PWNED payload is echoed in received: exactly; no PWNED file is created."""
    reader = _reader()
    payload = "src.py'; $(touch PWNED) `x` '@; y; @'"
    repo = tmp_path / "repo"
    repo.mkdir()
    b64 = _b64(payload)
    code, out, _err = _capture_main(reader, ["--root", str(repo), "--locator-b64", b64])
    assert not (repo / "PWNED").exists()
    assert not (tmp_path / "PWNED").exists()
    assert f"received: {json.dumps(payload, ensure_ascii=True)}" in out


def test_cli_read_prints_root_and_source_before_bytes(tmp_path: Path) -> None:
    """A successful read prints root: and source: before file bytes."""
    reader = _reader()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("ok\n", encoding="utf-8", newline="\n")
    b64 = _b64("src.py")
    code, out, _err = _capture_main(reader, ["--root", str(repo), "--locator-b64", b64])
    assert code == 0
    lines = out.splitlines()
    assert any(ln.startswith("root:") for ln in lines)
    assert any(ln.startswith("source:") for ln in lines)


def test_cli_repeated_locator_b64_exits_2_empty_stdout(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """A repeated --locator-b64 exits 2 with usage on stderr and nothing on stdout."""
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


# ── Sibling loading seam (AC-0012) ───────────────────────────────────────────

def test_sibling_missing_main_exits_4_stderr_raises_import(tmp_path: Path) -> None:
    """A missing sibling path makes main() exit 4 with stderr and read_locator raise ImportError."""
    reader = _reader()
    missing = tmp_path / "nonexistent" / "read-locator.py"
    code, out, err = _capture_main(
        reader, ["--root", str(tmp_path), "--locator-b64", _b64("x")],
        sibling_path=missing,
    )
    assert code == 4
    assert out == ""
    assert "repository-grounding locator reader unavailable" in err

    with pytest.raises(ImportError):
        reader.read_locator(tmp_path, "x", _sibling_path=missing)


@pytest.mark.skipif(
    not hasattr(os, "symlink"),
    reason="symlinks unavailable on this platform",
)
def test_sibling_symlink_main_exits_4_raises_import(tmp_path: Path) -> None:
    """A symlink to the real reader makes main() exit 4 and read_locator raise ImportError."""
    reader = _reader()
    real_path = reader._DEFAULT_GROUNDING_PATH
    link = tmp_path / "link-reader.py"
    try:
        link.symlink_to(real_path)
    except OSError:
        pytest.skip("symlink creation not permitted")

    code, out, err = _capture_main(
        reader, ["--root", str(tmp_path), "--locator-b64", _b64("x")],
        sibling_path=link,
    )
    assert code == 4
    assert out == ""
    assert "repository-grounding locator reader unavailable" in err

    with pytest.raises(ImportError):
        reader.read_locator(tmp_path, "x", _sibling_path=link)


def test_sibling_lacking_main_exits_4_raises_import(tmp_path: Path) -> None:
    """A sibling file lacking 'main' makes main() exit 4 and read_locator raise ImportError."""
    reader = _reader()
    incomplete = tmp_path / "incomplete-reader.py"
    incomplete.write_text("read_locator = None\n", encoding="utf-8")

    code, out, err = _capture_main(
        reader, ["--root", str(tmp_path), "--locator-b64", _b64("x")],
        sibling_path=incomplete,
    )
    assert code == 4
    assert out == ""
    assert "repository-grounding locator reader unavailable" in err

    with pytest.raises(ImportError):
        reader.read_locator(tmp_path, "x", _sibling_path=incomplete)


def test_default_sibling_path_resolves_to_grounding_reader(tmp_path: Path) -> None:
    """The default sibling path resolves to repository-grounding/scripts/read-locator.py."""
    reader = _reader()
    default = reader._DEFAULT_GROUNDING_PATH
    grounding_reader = (
        SKILLS / "repository-grounding" / "scripts" / "read-locator.py"
    )
    assert default.resolve() == grounding_reader.resolve()


# ── SKILL.md construction tests (goal-based text checks) ────────────────────

_PROCEDURE_STEPS = [
    "question",
    "stopping condition",
    "exposed",
    "fit",
    "natively",
    "fallback",
    "caveat",
    "authoritative",
    "stop",
]

_SURFACE_KEYWORDS = [
    "host metadata",
    "installed skills",
    "repository guidance",
    "user selection",
    "language",
    "editor",
    "code-navigation",
]

_NO_PROBE_PATTERNS = [
    "probe hidden",
    "search for credential",
    "crawl hidden",
    "inventory arbitrary executable",
    "infer availability from",
    "scan for credential",
]

_NO_SCHEMA_PATTERNS = [
    "provider request schema",
    "provider result schema",
    "common provider schema",
    "capability schema",
    "provenance schema",
    "freshness schema",
    "workflow-state schema",
    "normalized provider",
]

_EVIDENCE_RECORD_FIELDS = [
    "question",
    "stopping condition",
    "surfaces considered",
    "action invoked",
    "content sent",
    "root",
    "caveat",
    "authoritative",
    "stopped",
]


def _skill_text() -> str:
    """Return the lowercased SKILL.md text."""
    return SKILL_MD_PATH.read_text(encoding="utf-8").lower()


def test_skill_procedure_steps_present() -> None:
    """SKILL.md names all required ordered procedure steps."""
    text = _skill_text()
    for step in _PROCEDURE_STEPS:
        assert step in text, f"SKILL.md missing procedure step keyword: {step!r}"


def test_skill_exposed_surface_set_present() -> None:
    """SKILL.md names every surface from the exposed-only discovery rule."""
    text = _skill_text()
    for kw in _SURFACE_KEYWORDS:
        assert kw in text, f"SKILL.md missing surface keyword: {kw!r}"


def test_skill_no_probe_instructions() -> None:
    """SKILL.md contains no instructions to probe hidden config or credentials."""
    text = _skill_text()
    for pattern in _NO_PROBE_PATTERNS:
        assert pattern not in text, (
            f"SKILL.md contains probe instruction: {pattern!r}"
        )


def test_skill_no_normalized_provider_schema() -> None:
    """SKILL.md defines no normalized provider schema or common capability names."""
    text = _skill_text()
    for pattern in _NO_SCHEMA_PATTERNS:
        assert pattern not in text, (
            f"SKILL.md contains schema pattern: {pattern!r}"
        )


def test_skill_taxonomy_is_illustrative() -> None:
    """SKILL.md states that question types and provider shapes are illustrative."""
    text = _skill_text()
    assert "illustrative" in text, "SKILL.md must label taxonomy as illustrative"


def test_skill_evidence_record_fields_present() -> None:
    """SKILL.md evidence-record section names every required field."""
    text = _skill_text()
    for field in _EVIDENCE_RECORD_FIELDS:
        assert field in text, f"SKILL.md evidence-record missing field: {field!r}"


def test_skill_locator_read_through_reader_script() -> None:
    """SKILL.md tells agent to read locators only through scripts/read-locator.py with --locator-b64."""
    text = SKILL_MD_PATH.read_text(encoding="utf-8")
    assert "read-locator.py" in text, "SKILL.md must name the locator reader script"
    assert "--locator-b64" in text, "SKILL.md must name the --locator-b64 flag"
    text_lower = text.lower()
    assert "approved root" in text_lower, (
        "SKILL.md must require approved roots from the user or calling workflow"
    )


def test_skill_provider_output_is_data() -> None:
    """SKILL.md states that provider metadata, output, and returned file text are data."""
    text = _skill_text()
    assert "provider metadata" in text or "provider output" in text, (
        "SKILL.md must state that provider output is data"
    )
    assert "cannot" in text, (
        "SKILL.md must state what provider output cannot do"
    )


def test_skill_grounding_named_for_path_questions() -> None:
    """SKILL.md names repository-grounding as the route for path-seeded questions."""
    text = _skill_text()
    assert "repository-grounding" in text, (
        "SKILL.md must name repository-grounding for path-seeded governance questions"
    )
