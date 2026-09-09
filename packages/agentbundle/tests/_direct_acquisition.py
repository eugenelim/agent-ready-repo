"""Network-free acquisition fixture for direct ``git+https`` installs."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.diagnostics import (
    DiagnosticCode,
    make_direct_diagnostic,
)
from agentbundle.catalogue_tooling.results import Severity
from agentbundle.direct_source_acquisition import (
    AcquiredArchive,
    DirectAcquisitionError,
    parse_direct_source,
)


@dataclass(frozen=True)
class _Publication:
    """Prepared publisher bytes and the revision they represent."""

    tree: Path
    revision: str


class GitHttpsAcquisitionFake:
    """Patch acquisition with prepared archives keyed by repository and ref."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, storage: Path) -> None:
        self._publications: dict[tuple[str, str], _Publication] = {}
        self.calls: list[str] = []
        self._storage = storage
        monkeypatch.setattr(
            "agentbundle.direct_source_acquisition.acquire_git_https_archive",
            self.acquire,
        )

    def publish(
        self,
        repository: str,
        ref: str,
        tree: Path,
        *,
        revision: str | None = None,
    ) -> str:
        """Publish *tree*, replacing any prior publication for this ref."""

        for path in tree.rglob("*"):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise self._refusal(
                    DiagnosticCode.CAT_D007,
                    "a direct source may not carry links or special files",
                    str(path),
                    "Remove links and special files from the source tree.",
                )
        workspace = Path(
            tempfile.mkdtemp(
                prefix="agentbundle-direct-src-",
                dir=self._storage,
            )
        )
        snapshot = workspace / "tree"
        try:
            shutil.copytree(tree, snapshot)
            resolved_revision = revision or self._default_revision(ref, snapshot)
        except BaseException:
            shutil.rmtree(workspace, ignore_errors=True)
            raise
        self._publications[(repository, ref)] = _Publication(snapshot, resolved_revision)
        return resolved_revision

    def acquire(
        self,
        source_string: str,
        *,
        parent: Path | None = None,
        _clock: object = None,
        _progress: object = None,
        _max_download_bytes: object = None,
        _max_members: object = None,
        _max_decompressed_bytes: object = None,
        _inactivity_seconds: object = None,
    ) -> AcquiredArchive:
        """Return a fresh archive copy after production parsing and binding."""

        del (
            _clock,
            _progress,
            _max_download_bytes,
            _max_members,
            _max_decompressed_bytes,
            _inactivity_seconds,
        )
        self.calls.append(source_string)
        # Deliberately NOT `enforce_runtime_floor`. That floor guards real
        # acquisition — downloading and extracting a publisher archive — which
        # this fake never performs; it serves bytes the test already staged
        # locally. Calling it made every fake-driven test refuse `CAT-D005` on
        # any interpreter below the floor, which is a property of the runner
        # rather than of the source under test. The floor keeps its own coverage
        # in `tests/unit/test_direct_source_acquisition.py`.
        source = parse_direct_source(source_string)
        publication = self._publications.get(
            (f"{source.owner}/{source.repository}", source.ref)
        )
        if publication is None:
            raise self._refusal(
                DiagnosticCode.CAT_D006,
                "failed to fetch the source archive",
                source_string,
                "Check network reachability and the source spelling.",
            )
        self._verify_revision(
            source.ref_kind, source.ref, publication.revision, source_string
        )

        working = Path(
            tempfile.mkdtemp(prefix="agentbundle-direct-src-", dir=parent)
        )
        try:
            root = working / "archive"
            shutil.copytree(publication.tree, root)
            files = [path for path in root.rglob("*") if path.is_file()]
            return AcquiredArchive(
                root=root,
                revision=publication.revision,
                downloaded_bytes=sum(path.stat().st_size for path in files),
                members=len(files),
                working=working,
            )
        except BaseException:
            shutil.rmtree(working, ignore_errors=True)
            raise

    @staticmethod
    def _default_revision(ref: str, tree: Path) -> str:
        """Derive a deterministic 40-hex revision when the ref is not a SHA."""

        lowered = ref.lower()
        if len(lowered) == 40 and all(char in "0123456789abcdef" for char in lowered):
            return lowered
        if 7 <= len(lowered) < 40 and all(
            char in "0123456789abcdef" for char in lowered
        ):
            return (lowered + ("0" * 40))[:40]

        digest = hashlib.sha256()
        for path in sorted(tree.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(tree).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(path.read_bytes())
                digest.update(b"\0")
        return digest.hexdigest()[:40]

    @staticmethod
    def _verify_revision(ref_kind: str, ref: str, revision: str, source: str) -> None:
        """Apply the same SHA binding `_read_revision` applies to archives."""

        if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
            raise GitHttpsAcquisitionFake._refusal(
                DiagnosticCode.CAT_D004,
                "the archive carries no readable 40-hex commit SHA",
                source,
                "The archive is not a GitHub source archive.",
            )
        if ref_kind == "sha" and revision != ref.lower():
            raise GitHttpsAcquisitionFake._refusal(
                DiagnosticCode.CAT_D004,
                "the archive SHA does not equal the requested 40-hex ref",
                source,
                "The publisher moved the ref; re-pin to the new SHA.",
            )
        if ref_kind == "abbreviated-sha" and not revision.startswith(ref.lower()):
            raise GitHttpsAcquisitionFake._refusal(
                DiagnosticCode.CAT_D004,
                "the archive SHA does not extend the requested abbreviated ref",
                source,
                "Re-pin to the full 40-hex SHA.",
            )

    @staticmethod
    def _refusal(
        code: DiagnosticCode, message: str, source: str, remediation: str
    ) -> DirectAcquisitionError:
        """Create only registered direct-route refusals."""

        return DirectAcquisitionError(
            make_direct_diagnostic(
                code,
                Severity.ERROR,
                message,
                path=source,
                remediation=remediation,
            )
        )
