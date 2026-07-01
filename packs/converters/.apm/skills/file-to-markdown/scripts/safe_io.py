#!/usr/bin/env python3
"""
safe_io.py — defensive helpers for parsing untrusted document input.

The Tier-0 floor treats document inputs as **untrusted** (they are fed into AI
context layers, where the local-files-trusted carve-out does not hold). This
module centralizes the three guards every reader routes through :

  * ``parse_xml`` — an XXE- and entity-expansion-safe XML read. Uses only
    stdlib ``xml.etree.ElementTree`` (which does not resolve external entities),
    and refuses any DTD/DOCTYPE up front — so both external-entity (XXE) and
    internal-entity (billion-laughs) attacks are closed, since both require a
    DTD to declare the entity. ``lxml`` / ``minidom`` / ``sax`` at defaults are
    never used.
  * ``SafeZip`` / ``open_safe_zip`` — a decompression-bomb-guarded zip reader.
    Refuses, *before* full decompression, on every axis: an implausible
    declared-vs-compressed size ratio, a total-cumulative-uncompressed cap, and
    an entry-count cap; reads members in-memory by known name only (never joins
    an entry name into a filesystem path — the path-join guard), refuses
    traversal names, and never recurses into a nested-archive member.
  * ``confine`` — realpath + path-*component* containment output confinement
    (not a string-prefix check), mirroring the ``markdown-to-office-publishing``
    benchmark; a sibling like ``root-evil`` is rejected against root ``root``.
  * ``check_input_size`` — the coarse max-input-bytes ceiling shared by
    every Tier-0 parser.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

# --- Coarse resource ceilings ---------------------------------------

MAX_INPUT_BYTES = 200 * 1024 * 1024        # 200 MB — coarse input-file ceiling
MAX_ZIP_ENTRIES = 10_000                   # OOXML/ODF/EPUB have many members, not this many
MAX_ZIP_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024   # 500 MB cumulative uncompressed
MAX_ZIP_RATIO = 200                        # declared:compressed ratio (text ~10-20x; bombs 1000x+)
MAX_ZIP_MEMBER_BYTES = 150 * 1024 * 1024   # 150 MB for a single member (e.g. document.xml)

# Member extensions we refuse to hand back — a member that is itself an archive
# is the nested-archive bomb axis; the readers never recurse into one.
_NESTED_ARCHIVE_EXTS = {
    ".zip", ".gz", ".bz2", ".xz", ".7z", ".rar", ".tar", ".jar", ".war",
    ".docx", ".xlsx", ".pptx", ".epub", ".odt", ".ods", ".odp",
}


class ResourceCeilingError(ValueError):
    """An input exceeded a coarse resource ceiling."""


class ZipBombError(ValueError):
    """A zip tripped a decompression-bomb guard."""


class XmlSafetyError(ValueError):
    """XML carried a DTD/DOCTYPE (XXE / entity-expansion guard)."""


# --- Input-size ceiling -----------------------------------------------------


def check_input_size(path: Path, *, max_bytes: int = MAX_INPUT_BYTES) -> int:
    """Refuse an oversized input up front; return its size in bytes."""
    size = path.stat().st_size
    if size > max_bytes:
        raise ResourceCeilingError(
            f"input {path.name} is {size} bytes, over the {max_bytes}-byte "
            f"ceiling; refusing to parse unbounded — split or pre-trim the file"
        )
    return size


# --- XXE-safe XML -----------------------------------------------------------


def parse_xml(data: bytes | str) -> ET.Element:
    """Parse untrusted XML into an ElementTree Element, XXE/DTD-safe.

    stdlib ``ElementTree`` does not resolve external entities; the DTD refusal
    below additionally blocks internal-entity (billion-laughs) *definitions*,
    so an undefined ``&entity;`` reference simply raises rather than expanding.
    """
    raw = data.encode("utf-8") if isinstance(data, str) else data
    _reject_dtd(raw)
    return ET.fromstring(raw)


def _reject_dtd(data: bytes) -> None:
    # Scan the whole buffer, not a fixed prolog window: a DOCTYPE legitimately
    # precedes the root element, and an attacker can pad the prolog with
    # whitespace/comments past any fixed window before declaring the DTD.
    # OOXML/ODF/EPUB members never carry a literal `<!DOCTYPE`, so a whole-buffer
    # scan cannot false-positive on their content.
    if re.search(rb"<!DOCTYPE", data, re.IGNORECASE):
        raise XmlSafetyError(
            "XML DTD/DOCTYPE is not allowed (external-entity / billion-laughs guard)"
        )


# --- Decompression-bomb-guarded zip reader ----------------------------------


def _is_safe_member_name(name: str) -> bool:
    """A member name is safe iff it is relative and has no ``..`` component and
    no drive/root — so it could never be joined into a path that escapes."""
    if not name or name.startswith("/") or name.startswith("\\"):
        return False
    p = Path(name)
    if p.is_absolute() or (len(p.drive) > 0):
        return False
    return ".." not in p.parts


def _is_nested_archive(name: str) -> bool:
    return Path(name).suffix.lower() in _NESTED_ARCHIVE_EXTS


class SafeZip:
    """A zip reader that reads members in-memory by known name, with a
    per-member decompression cap. Construct via :func:`open_safe_zip`, which
    enforces the global (entry-count / cumulative / ratio) axes first."""

    def __init__(
        self,
        zf: zipfile.ZipFile,
        *,
        max_member_bytes: int,
        max_total_uncompressed: int = MAX_ZIP_TOTAL_UNCOMPRESSED,
    ) -> None:
        self._zf = zf
        self._max_member_bytes = max_member_bytes
        self._max_total = max_total_uncompressed
        self._read_total = 0  # cumulative ACTUAL bytes decompressed via read_member
        self._names = set(zf.namelist())

    def __enter__(self) -> "SafeZip":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._zf.close()

    def has_member(self, name: str) -> bool:
        return name in self._names

    def namelist(self) -> list[str]:
        return list(self._names)

    def harden_untrusted(self) -> None:
        """Fully validate every member before an ordinary Office library (whose
        transitive ``lxml`` parser we do not control) re-opens the raw file.

        The library path bypasses :meth:`read_member`, so this is where the
        per-member cap, the cumulative-actual-bytes cap, and the DTD refusal are
        enforced for it: read each safe, non-nested member through the capped
        path (catching an *understated* declared size that the central-directory
        axes miss), and whole-buffer-scan every XML-looking member for a DTD —
        by extension *or* by an ``<`` prolog, since ``lxml`` will parse XML
        content regardless of suffix. Nested-archive and traversal members are
        skipped, never recursed into."""
        for name in self._names:
            if not _is_safe_member_name(name) or _is_nested_archive(name):
                # Nested-archive members are skipped, never recursed into (the
                # nested-bomb axis). They are intentionally outside the read-time
                # cap: the ordinary Office libs never decompress an embedded
                # archive member (openpyxl reads xl/*, python-docx word/*,
                # python-pptx ppt/*), so an understated nested member is never
                # actually expanded — only its declared-size axes in
                # open_safe_zip apply, which is sufficient.
                continue
            data = self.read_member(name)  # per-member + cumulative caps
            looks_xml = (
                name.lower().endswith((".xml", ".rels"))
                or data.lstrip()[:1] == b"<"
            )
            if looks_xml:
                _reject_dtd(data)

    def read_member(self, name: str) -> bytes:
        """Read one member fully in-memory by its exact known name.

        Never constructs a filesystem path from ``name`` (the path-join guard):
        traversal names are refused, and the read is bounded by the per-member
        byte cap so a member that lied about its declared size (the metadata
        cannot be trusted) is still caught at read time. Nested archives are
        refused — the reader never recurses into one."""
        if not _is_safe_member_name(name):
            raise ZipBombError(f"refusing unsafe zip member name {name!r}")
        if _is_nested_archive(name):
            raise ZipBombError(f"refusing to read nested-archive member {name!r}")
        if name not in self._names:
            raise KeyError(name)
        with self._zf.open(name) as f:
            data = f.read(self._max_member_bytes + 1)
        if len(data) > self._max_member_bytes:
            raise ZipBombError(
                f"zip member {name!r} exceeds the {self._max_member_bytes}-byte "
                f"per-member cap (declared size may have been understated)"
            )
        self._read_total += len(data)
        if self._read_total > self._max_total:
            raise ZipBombError(
                f"cumulative decompressed bytes exceed the {self._max_total}-byte "
                f"cap (declared sizes may have been understated across members)"
            )
        return data


def open_safe_zip(
    path: Path,
    *,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_total_uncompressed: int = MAX_ZIP_TOTAL_UNCOMPRESSED,
    max_ratio: int = MAX_ZIP_RATIO,
    max_member_bytes: int = MAX_ZIP_MEMBER_BYTES,
) -> SafeZip:
    """Open a zip, refusing on every decompression-bomb axis *before* any
    member is decompressed. Reads use the zip's central-directory
    metadata only, which requires no decompression."""
    zf = zipfile.ZipFile(path)
    try:
        infos = zf.infolist()
        if len(infos) > max_entries:
            raise ZipBombError(
                f"zip has {len(infos)} entries, over the {max_entries} cap"
            )
        total = 0
        for info in infos:
            total += info.file_size
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > max_ratio:
                    raise ZipBombError(
                        f"zip member {info.filename!r} declares a {ratio:.0f}x "
                        f"compression ratio, over the {max_ratio}x cap"
                    )
        if total > max_total_uncompressed:
            raise ZipBombError(
                f"zip declares {total} cumulative uncompressed bytes, over the "
                f"{max_total_uncompressed}-byte cap"
            )
    except BaseException:
        zf.close()
        raise
    return SafeZip(
        zf,
        max_member_bytes=max_member_bytes,
        max_total_uncompressed=max_total_uncompressed,
    )


# --- Output-path confinement ------------------------------------------------


def confine(path: Path, root: Path) -> Path:
    """Resolve ``path`` (following symlinks) and require it under ``root``.

    Path-*component* containment (``root`` is the resolved path or among its
    ``.parents``), not a string-prefix check, so a sibling like ``root-evil``
    is rejected against root ``root``. Raises ``ValueError`` on escape."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    raise ValueError(
        f"path {path!r} resolves to {resolved} which is outside {root_resolved}; "
        f"refusing to write outside the confinement root"
    )
