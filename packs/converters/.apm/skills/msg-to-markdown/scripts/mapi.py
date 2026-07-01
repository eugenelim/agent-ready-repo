#!/usr/bin/env python3
"""
mapi.py — a bounded, first-party MAPI-property reader for Outlook `.msg` files.

`olefile` (BSD-2, pip-on-demand) opens the OLE2/CFBF container; this module
decodes the `__substg1.0_<id><type>` property streams itself. It replaces the
Python-2-broken `msg-parser` (whose `DataModel.PtypInteger32` crashes on any
integer property under Python 3) and the GPL `extract-msg` — the reader choice
recorded in ADR-0046.

Because the parsing is now first-party code over **untrusted** input, this
module owns the resource + robustness guards a black-box library would (spec
AC9/AC10):

  * **Per-stream byte cap**, checked against the CFBF-declared size *before* the
    stream is materialized, and re-checked on read — the declared size is not
    trusted (an over-declared stream is refused; the whole-file
    ``check_input_size`` ceiling in ``convert.py`` means an understated size can
    only yield a smaller, bounded read).
  * **OLE2 stream/storage-count cap**, checked immediately after enumeration,
    before any stream read.
  * **Cumulative-output budget**, a single running total threaded through the
    embedded-message recursion (never re-initialized per level) so N
    shallow-but-large embedded parts cannot bypass it.
  * **Embedded-message recursion** bounded by depth and total count.
  * **Non-raising decode** (``errors="replace"``; odd-length / truncated /
    out-of-range buffers degrade, never throw), so a malformed property fails
    soft to ``requires-review`` rather than crashing.
  * **RTF is never decompressed** — the ``PidTagRtfCompressed`` LZFu header's
    declared uncompressed size is read and bounded, but no LZFu decoder runs
    (that would be a malformed-input control-flow surface); an RTF-only body
    degrades to a surfaced note.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

# --- Skill-owned resource ceilings (AC10) -----------------------------------

MAX_STREAM_BYTES = 64 * 1024 * 1024          # per single MAPI property stream
MAX_TOTAL_OUTPUT = 256 * 1024 * 1024         # cumulative across the whole walk
MAX_OLE_ENTRIES = 10_000                      # OLE2 stream + storage count
MAX_RTF_RAW_BYTES = 64 * 1024 * 1024          # LZFu-declared uncompressed size
MAX_EMBED_DEPTH = 3
MAX_EMBED_COUNT = 20

# --- Real MAPI property tags (id hex, upper) --------------------------------

P_SUBJECT = "0037"
P_BODY = "1000"
P_HTML = "1013"
P_RTF_COMPRESSED = "1009"
P_SENDER_NAME = "0C1A"
P_SENDER_EMAIL = "0C1F"
P_SENDER_SMTP = "5D01"
P_SENT_REPR_NAME = "0042"
P_SENT_REPR_SMTP = "5D02"
P_DELIVERY_TIME = "0E06"
P_SUBMIT_TIME = "0039"
P_CREATION_TIME = "3007"
P_IMPORTANCE = "0017"
P_DISPLAY_NAME = "3001"
P_EMAIL_ADDRESS = "3003"
P_SMTP_ADDRESS = "39FE"
P_RECIPIENT_TYPE = "0C15"
P_ATTACH_LONG_FILENAME = "3707"
P_ATTACH_FILENAME = "3704"
P_ATTACH_MIME = "370E"
P_ATTACH_CONTENT_ID = "3712"
P_ATTACH_METHOD = "3705"
P_ATTACH_DATA = "3701"        # PidTagAttachDataBinary (0102) / AttachDataObject
P_ATTACH_SIZE = "0E20"

ATTACH_METHOD_EMBEDDED = 5
IMPORTANCE_LABELS = {0: "low", 1: "normal", 2: "high"}
RECIPIENT_KINDS = {1: "to", 2: "cc", 3: "bcc"}
EMBEDDED_STORAGE = "__substg1.0_3701000D"    # PtypObject holding a nested message


class MsgResourceError(ValueError):
    """An input tripped a skill-owned resource ceiling (AC10)."""


class MsgParseError(ValueError):
    """A malformed/unreadable `.msg` — fails soft to requires-review (AC9)."""


# --- Internal email model ---------------------------------------------------


@dataclass
class Recipient:
    name: str
    email: str
    kind: str                # to | cc | bcc


@dataclass
class Attachment:
    filename: str
    size: int | None
    ctype: str
    inline: bool
    is_embedded_msg: bool


@dataclass
class EmailModel:
    subject: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    recipients: list[Recipient] = field(default_factory=list)
    date: str | None = None                # ISO-8601 UTC
    importance: str | None = None
    body_kind: str = "none"                # html | plain | rtf | none
    body_text: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    embedded_subjects: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    requires_review: bool = False


class _Budget:
    """Single cumulative-output accumulator threaded through the recursion."""

    def __init__(self, total: int | None = None) -> None:
        # Read the module global at call time (not as a default arg) so tests can
        # monkeypatch MAX_TOTAL_OUTPUT.
        self.remaining = MAX_TOTAL_OUTPUT if total is None else total

    def take(self, n: int) -> None:
        self.remaining -= n
        if self.remaining < 0:
            raise MsgResourceError(
                "cumulative decompressed output exceeds the "
                f"{MAX_TOTAL_OUTPUT}-byte budget (aggregated across embedded messages)"
            )


# --- Decoders (non-raising) -------------------------------------------------


def _decode_str(data: bytes, type_hex: str) -> str:
    if type_hex == "001F":               # PtypString (UTF-16LE)
        return data.decode("utf-16-le", errors="replace").rstrip("\x00")
    if type_hex == "001E":               # PtypString8 (codepage)
        return data.decode("cp1252", errors="replace").rstrip("\x00")
    return data.decode("utf-8", errors="replace")


def _decode_int(data: bytes) -> int | None:
    if len(data) < 4:
        return None
    return struct.unpack("<I", data[:4])[0]


def _decode_time(data: bytes) -> str | None:
    if len(data) < 8:
        return None
    val = struct.unpack("<Q", data[:8])[0]
    if val == 0:
        return None
    try:
        dt = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=val / 10)
    except (OverflowError, OSError, ValueError):
        return None                      # garbage FILETIME → fail soft (AC9)
    return dt.isoformat(timespec="seconds")


# --- Container walk ---------------------------------------------------------


class _Reader:
    def __init__(self, ole, budget: _Budget) -> None:
        self._ole = ole
        self._budget = budget
        self._paths = ole.listdir(streams=True, storages=True)
        if len(self._paths) > MAX_OLE_ENTRIES:
            raise MsgResourceError(
                f"OLE2 container has {len(self._paths)} entries, over the "
                f"{MAX_OLE_ENTRIES} stream/storage cap"
            )
        self._streams = [p for p in ole.listdir(streams=True)]

    def _children(self, prefix: list[str]):
        """Immediate child stream {name: path} and storage-name set under prefix."""
        n = len(prefix)
        streams: dict[str, list[str]] = {}
        storages: set[str] = set()
        for p in self._streams:
            if len(p) <= n or p[:n] != prefix:
                continue
            comp = p[n]
            if len(p) == n + 1:
                streams[comp] = p
            else:
                storages.add(comp)
        return streams, storages

    def _read(self, path: list[str]) -> bytes:
        # Distrust the declared size: refuse before materializing, re-check on read.
        try:
            declared = self._ole.get_size(path)
        except Exception:
            declared = 0
        if declared > MAX_STREAM_BYTES:
            raise MsgResourceError(
                f"stream {path[-1]!r} declares {declared} bytes, over the "
                f"{MAX_STREAM_BYTES}-byte per-stream cap"
            )
        with self._ole.openstream(path) as fh:
            data = fh.read(MAX_STREAM_BYTES + 1)
        if len(data) > MAX_STREAM_BYTES:
            raise MsgResourceError(
                f"stream {path[-1]!r} exceeds the {MAX_STREAM_BYTES}-byte per-stream cap"
            )
        self._budget.take(len(data))
        return data

    def _props(self, streams: dict[str, list[str]]) -> dict[str, tuple[str, list[str]]]:
        """Map property-id (hex upper) -> (type hex, stream path) for substg streams."""
        out: dict[str, tuple[str, list[str]]] = {}
        for name, path in streams.items():
            if not name.startswith("__substg1.0_") or len(name) < 20:
                continue
            pid = name[12:16].upper()
            typ = name[16:20].upper()
            out[pid] = (typ, path)
        return out

    def _get_str(self, props, pid) -> str | None:
        hit = props.get(pid)
        if hit is None:
            return None
        typ, path = hit
        return _decode_str(self._read(path), typ)

    def _get_int(self, props, pid) -> int | None:
        hit = props.get(pid)
        if hit is None:
            return None
        return _decode_int(self._read(hit[1]))

    def _get_time(self, props, pid) -> str | None:
        hit = props.get(pid)
        if hit is None:
            return None
        return _decode_time(self._read(hit[1]))

    def _get_bytes(self, props, pid) -> bytes | None:
        hit = props.get(pid)
        if hit is None:
            return None
        return self._read(hit[1])

    def parse(self, prefix: list[str], depth: int, counters: dict) -> EmailModel:
        streams, storages = self._children(prefix)
        props = self._props(streams)
        m = EmailModel()

        m.subject = self._get_str(props, P_SUBJECT)
        m.sender_name = self._get_str(props, P_SENDER_NAME) or self._get_str(props, P_SENT_REPR_NAME)
        m.sender_email = (self._get_str(props, P_SENDER_SMTP)
                          or self._get_str(props, P_SENDER_EMAIL)
                          or self._get_str(props, P_SENT_REPR_SMTP))

        imp = self._get_int(props, P_IMPORTANCE)
        if imp is not None:
            m.importance = IMPORTANCE_LABELS.get(imp, str(imp))

        # Date: delivery > submit > creation.
        m.date = (self._get_time(props, P_DELIVERY_TIME)
                  or self._get_time(props, P_SUBMIT_TIME)
                  or self._get_time(props, P_CREATION_TIME))

        # Body: HTML > plain > RTF-only (note). HTML property is binary bytes.
        html = self._get_bytes(props, P_HTML)
        if html:
            m.body_kind = "html"
            m.body_text = html.decode("utf-8", errors="replace")
        else:
            plain = self._get_str(props, P_BODY)
            if plain:
                m.body_kind = "plain"
                m.body_text = plain
            elif P_RTF_COMPRESSED in props:
                m.body_kind = "rtf"
                self._check_rtf(props)
                m.notes.append(
                    "Body is RTF-only (compressed). RTF is not decompressed by this "
                    "Tier-0 converter; open in Outlook and re-save as HTML/plain text."
                )
                m.requires_review = True

        # Recipients.
        for name in sorted(storages):
            if name.startswith("__recip_version1.0"):
                m.recipients.append(self._parse_recipient(prefix + [name]))

        # Attachments (+ embedded-message recursion).
        for name in sorted(storages):
            if name.startswith("__attach_version1.0"):
                self._parse_attachment(prefix + [name], m, depth, counters)

        return m

    def _parse_recipient(self, prefix: list[str]) -> Recipient:
        streams, _ = self._children(prefix)
        props = self._props(streams)
        name = self._get_str(props, P_DISPLAY_NAME) or ""
        email = self._get_str(props, P_SMTP_ADDRESS) or self._get_str(props, P_EMAIL_ADDRESS) or ""
        rt = self._get_int(props, P_RECIPIENT_TYPE)
        return Recipient(name=name, email=email, kind=RECIPIENT_KINDS.get(rt, "to"))

    def _parse_attachment(self, prefix: list[str], parent: EmailModel,
                          depth: int, counters: dict) -> None:
        streams, storages = self._children(prefix)
        props = self._props(streams)
        filename = (self._get_str(props, P_ATTACH_LONG_FILENAME)
                    or self._get_str(props, P_ATTACH_FILENAME) or "unnamed")
        mime = self._get_str(props, P_ATTACH_MIME) or "application/octet-stream"
        method = self._get_int(props, P_ATTACH_METHOD)
        content_id = self._get_str(props, P_ATTACH_CONTENT_ID)
        size = self._get_int(props, P_ATTACH_SIZE)
        has_embedded_storage = EMBEDDED_STORAGE in storages
        is_embedded = (method == ATTACH_METHOD_EMBEDDED or has_embedded_storage
                       or filename.lower().endswith(".msg"))

        parent.attachments.append(Attachment(
            filename=filename, size=size, ctype=mime,
            inline=bool(content_id), is_embedded_msg=is_embedded))

        if is_embedded and has_embedded_storage:
            if depth + 1 > MAX_EMBED_DEPTH or counters["embedded"] >= MAX_EMBED_COUNT:
                parent.notes.append(
                    "An embedded message was not traversed: the recursion "
                    f"depth ({MAX_EMBED_DEPTH}) or count ({MAX_EMBED_COUNT}) cap was reached."
                )
                parent.requires_review = True
                return
            counters["embedded"] += 1
            # Recurse with the SAME budget (threaded across the whole walk, AC10).
            sub = self.parse(prefix + [EMBEDDED_STORAGE], depth + 1, counters)
            parent.embedded_subjects.append(sub.subject or "(no subject)")
            parent.notes.extend(sub.notes)
            if sub.requires_review:
                parent.requires_review = True

    def _check_rtf(self, props) -> None:
        hit = props.get(P_RTF_COMPRESSED)
        if hit is None:
            return
        # Per-stream cap pre-check (distrust the declared size), mirroring _read,
        # before olefile materializes the stream on openstream.
        try:
            declared = self._ole.get_size(hit[1])
        except Exception:
            declared = 0
        if declared > MAX_STREAM_BYTES:
            raise MsgResourceError(
                f"RTF-compressed stream declares {declared} bytes, over the "
                f"{MAX_STREAM_BYTES}-byte per-stream cap")
        # Read only the LZFu header (compSize, rawSize, magic, crc) — never
        # decompress. Bound the DECLARED uncompressed size.
        with self._ole.openstream(hit[1]) as fh:
            header = fh.read(16)
        self._budget.take(len(header))
        if len(header) >= 8:
            raw_size = struct.unpack("<I", header[4:8])[0]
            if raw_size > MAX_RTF_RAW_BYTES:
                raise MsgResourceError(
                    f"RTF body declares {raw_size} uncompressed bytes, over the "
                    f"{MAX_RTF_RAW_BYTES}-byte LZFu cap"
                )


@dataclass
class RawAttachment:
    filename: str            # the attacker-controlled stored name (unsanitised)
    data: bytes | None       # None for an embedded message (no flat byte stream)
    is_embedded_msg: bool


def read_attachments(path) -> list[RawAttachment]:
    """Read top-level attachments' stored filename + bytes for the confined
    extraction sub-command. The filename is returned **unsanitised** — the caller
    (convert.py) is responsible for basename-reduction + confinement (AC6). Bytes
    are bounded by the same per-stream cap and cumulative budget."""
    import olefile

    if not olefile.isOleFile(str(path)):
        raise MsgParseError("not an OLE2 compound file (.msg)")
    try:
        ole = olefile.OleFileIO(str(path))
    except Exception as exc:
        raise MsgParseError(f"could not open OLE2 container: {exc}") from exc
    out: list[RawAttachment] = []
    try:
        reader = _Reader(ole, _Budget())
        _, storages = reader._children([])
        for name in sorted(storages):
            if not name.startswith("__attach_version1.0"):
                continue
            prefix = [name]
            streams, sub_storages = reader._children(prefix)
            props = reader._props(streams)
            filename = (reader._get_str(props, P_ATTACH_LONG_FILENAME)
                        or reader._get_str(props, P_ATTACH_FILENAME) or "")
            method = reader._get_int(props, P_ATTACH_METHOD)
            data = reader._get_bytes(props, P_ATTACH_DATA)
            # A genuinely embedded message has a nested storage and no flat data
            # stream; a flat `.msg` *file* attachment has bytes and MUST still be
            # extractable (keying the skip on the .msg filename would lose it).
            embedded = data is None and (method == ATTACH_METHOD_EMBEDDED
                                         or EMBEDDED_STORAGE in sub_storages)
            out.append(RawAttachment(filename=filename, data=data, is_embedded_msg=embedded))
    except MsgResourceError:
        raise
    except Exception as exc:
        raise MsgParseError(f"malformed .msg structure: {exc}") from exc
    finally:
        ole.close()
    return out


def read_msg(path) -> EmailModel:
    """Parse a `.msg` into the internal EmailModel. Raises MsgResourceError on a
    resource-ceiling trip and MsgParseError on a malformed/unreadable file."""
    import olefile

    if not olefile.isOleFile(str(path)):
        raise MsgParseError("not an OLE2 compound file (.msg)")
    try:
        ole = olefile.OleFileIO(str(path))
    except Exception as exc:  # malformed CFBF — fail soft (AC9)
        raise MsgParseError(f"could not open OLE2 container: {exc}") from exc
    try:
        reader = _Reader(ole, _Budget())
        return reader.parse([], depth=0, counters={"embedded": 0})
    except MsgResourceError:
        raise
    except Exception as exc:  # malformed MAPI/CFBF internals — fail soft (AC9)
        raise MsgParseError(f"malformed .msg structure: {exc}") from exc
    finally:
        ole.close()
