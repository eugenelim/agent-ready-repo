"""Regression tests for metadata-safe self-host file projection."""

from __future__ import annotations

import errno
import os
import stat
import sys
from pathlib import Path

import pytest
from agentbundle.build import projection_io
from agentbundle.build.projection_io import copy_projected_file


class TestCopyProjectedFile:
    """Adapter-independent helper coverage for identity and metadata policy."""

    def test_missing_output_root_is_created(self, tmp_path: Path) -> None:
        source = tmp_path / "source.txt"
        output = tmp_path / "missing-output"
        source.write_bytes(b"projected\n")

        copy_projected_file(
            source,
            output / "nested" / "target.txt",
            base=output,
            metadata="stat",
        )

        assert (output / "nested" / "target.txt").read_bytes() == b"projected\n"

    def test_existing_target_preserves_inode_owner_and_mode(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"new content\n")
        target.write_bytes(b"old content\n")
        if os.name == "posix":
            source.chmod(0o600)
            target.chmod(0o664)
        before = target.stat()

        def deny_metadata(*_args: object, **_kwargs: object) -> None:
            raise PermissionError("metadata denied")

        monkeypatch.setattr(projection_io.shutil, "copymode", deny_metadata)
        monkeypatch.setattr(projection_io.shutil, "copystat", deny_metadata)
        monkeypatch.setattr(projection_io.os, "utime", deny_metadata)
        monkeypatch.setattr(projection_io.os, "chmod", deny_metadata)
        if hasattr(projection_io.os, "fchmod"):
            monkeypatch.setattr(projection_io.os, "fchmod", deny_metadata)

        copy_projected_file(
            source,
            target,
            base=tmp_path,
            metadata="mode",
            preserve_existing_metadata=True,
        )

        after = target.stat()
        assert target.read_bytes() == b"new content\n"
        if sys.platform != "win32":
            assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
            assert after.st_ino == before.st_ino
            assert after.st_uid == before.st_uid
            assert after.st_gid == before.st_gid

    def test_existing_target_refuses_symlink(self, tmp_path: Path) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        outside = tmp_path / "outside.txt"
        source.write_bytes(b"projected\n")
        outside.write_bytes(b"outside\n")
        try:
            target.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks not available")

        with pytest.raises(OSError):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert target.is_symlink()
        assert outside.read_bytes() == b"outside\n"

    def test_fallback_refuses_linked_parent(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        outside = tmp_path / "outside"
        linked_parent = tmp_path / "linked"
        source.write_bytes(b"projected\n")
        outside.mkdir()
        try:
            linked_parent.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks not available")
        monkeypatch.setattr(
            projection_io,
            "_secure_dir_fd_available",
            lambda: False,
        )

        with pytest.raises(projection_io.ProjectionTypeError):
            copy_projected_file(
                source,
                linked_parent / "target.txt",
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert not (outside / "target.txt").exists()

    def test_existing_target_refuses_hard_link(self, tmp_path: Path) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        outside = tmp_path / "outside.txt"
        source.write_bytes(b"projected\n")
        outside.write_bytes(b"outside\n")
        try:
            os.link(outside, target)
        except OSError:
            pytest.skip("hard links not available")

        with pytest.raises(projection_io.ProjectionTypeError):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert outside.read_bytes() == b"outside\n"

    def test_partial_write_restores_original_bytes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"replacement content\n")
        original = b"original content\n"
        target.write_bytes(original)
        real_write_all = projection_io._write_all
        call_count = 0

        def fail_first_write(file_descriptor: int, content: bytes) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                os.write(file_descriptor, content[:3])
                raise OSError(errno.EIO, "injected partial write")
            real_write_all(file_descriptor, content)

        monkeypatch.setattr(projection_io, "_write_all", fail_first_write)
        with pytest.raises(OSError):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert target.read_bytes() == original

    def test_identity_mismatch_refuses_before_writing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"replacement\n")
        target.write_bytes(b"original\n")
        monkeypatch.setattr(
            projection_io,
            "_read_source_no_follow",
            lambda _source: (b"replacement\n", source.stat()),
        )
        monkeypatch.setattr(
            projection_io,
            "_same_file_identity",
            lambda *_args: False,
        )

        with pytest.raises(projection_io.ProjectionTypeError):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert target.read_bytes() == b"original\n"

    def test_write_only_target_still_updates_content(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Write-only fallback preserves the old content-copy permission floor."""
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"replacement\n")
        target.write_bytes(b"original\n")
        real_open = projection_io.os.open

        def deny_read_write(
            path: object,
            flags: int,
            *args: object,
            **kwargs: object,
        ) -> int:
            if flags & os.O_RDWR == os.O_RDWR:
                raise PermissionError("read access denied")
            return real_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(projection_io.os, "open", deny_read_write)
        copy_projected_file(
            source,
            target,
            base=tmp_path,
            metadata="stat",
            preserve_existing_metadata=True,
        )

        assert target.read_bytes() == b"replacement\n"

    def test_oversized_source_refuses_before_mutation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"replacement\n")
        target.write_bytes(b"original\n")
        monkeypatch.setattr(projection_io, "_MAX_IN_PLACE_BYTES", 1)

        with pytest.raises(OSError, match="exceeds"):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert target.read_bytes() == b"original\n"

    def test_oversized_existing_target_refuses_before_mutation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"x")
        original = b"original\n"
        target.write_bytes(original)
        monkeypatch.setattr(projection_io, "_MAX_IN_PLACE_BYTES", 1)

        with pytest.raises(OSError, match="target.txt.*exceeds"):
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert target.read_bytes() == original

    def test_write_and_restore_failures_are_both_reported(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_bytes(b"replacement\n")
        target.write_bytes(b"original\n")
        failures = iter((
            OSError(errno.EIO, "injected write failure"),
            OSError(errno.ENOSPC, "injected restore failure"),
        ))

        def fail_write_and_restore(*_args: object) -> None:
            raise next(failures)

        monkeypatch.setattr(projection_io, "_write_all", fail_write_and_restore)
        with pytest.raises(ExceptionGroup) as raised:
            copy_projected_file(
                source,
                target,
                base=tmp_path,
                metadata="stat",
                preserve_existing_metadata=True,
            )

        assert len(raised.value.exceptions) == 2
        assert "write failure" in str(raised.value.exceptions[0])
        assert "restore failure" in str(raised.value.exceptions[1])

    def test_new_target_inherits_requested_source_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "source.txt"
        source.write_bytes(b"new file\n")
        if os.name == "posix":
            source.chmod(0o640)

        mode_target = tmp_path / "mode-target.txt"
        copy_projected_file(
            source,
            mode_target,
            base=tmp_path,
            metadata="mode",
            preserve_existing_metadata=True,
        )
        stat_target = tmp_path / "stat-target.txt"
        copy_projected_file(
            source,
            stat_target,
            base=tmp_path,
            metadata="stat",
            preserve_existing_metadata=True,
        )

        if sys.platform != "win32":
            source_mode = stat.S_IMODE(source.stat().st_mode)
            assert stat.S_IMODE(mode_target.stat().st_mode) == source_mode
            assert stat.S_IMODE(stat_target.stat().st_mode) == source_mode
            assert stat_target.stat().st_mtime_ns == source.stat().st_mtime_ns
