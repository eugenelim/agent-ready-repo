#!/usr/bin/env python3
"""
msg_fixtures.py — a minimal pure-Python CFBF/OLE2 (.msg) writer + corpus builder
for tests.

No permissive `.msg` *writer* exists on PyPI (``olefile`` is read-only), so the
"generated corpus" the spec's Testing Strategy calls for is produced here. The
writer implements the Compound File Binary Format (MS-CFB) with a real mini
stream + MiniFAT: ``olefile`` forces the mini-stream cutoff to 4096 regardless of
the header field, so every small stream MUST live in the MiniFAT — the naive
"declare cutoff 0" trick reads back empty.

Streams are named with **real** MAPI property tags (``__substg1.0_<id><type>``)
so a fixture is shaped like a genuine Outlook ``.msg`` and both this skill's
``olefile``-based reader and the independent Node ``msgreader`` package parse it.

This is test infrastructure, not a runtime path of the converter.
"""
from __future__ import annotations

import struct
from datetime import datetime, timezone
from pathlib import Path

SIG = bytes.fromhex("D0CF11E0A1B11AE1")
FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
NOSTREAM = 0xFFFFFFFF
SECT = 512
MINISECT = 64
CUTOFF = 4096

T_STORAGE, T_STREAM, T_ROOT = 1, 2, 5


class _Entry:
    def __init__(self, name, otype, data=b"", children=None):
        self.name = name
        self.otype = otype
        self.data = data
        self.children = children or []
        self.left = self.right = self.child = NOSTREAM
        self.start = ENDOFCHAIN
        self.size = 0
        self.idx = None


def _cfb_key(e):
    return (len(e.name.encode("utf-16-le")), e.name.upper())


def _build_bst(entries):
    entries = sorted(entries, key=_cfb_key)

    def build(lo, hi):
        if lo > hi:
            return NOSTREAM
        mid = (lo + hi) // 2
        entries[mid].left = build(lo, mid - 1)
        entries[mid].right = build(mid + 1, hi)
        return entries[mid].idx

    return build(0, len(entries) - 1)


def _spec_to_entries(spec, storage_name=None):
    """Turn a message spec dict into a storage (or the root's children).

    spec: {top: {stream_name: bytes}, recipients: [dict], attachments: [dict],
           embedded: {att_index: sub_spec}}."""
    kids = [_Entry(n, T_STREAM, d) for n, d in spec.get("top", {}).items()]
    for i, rec in enumerate(spec.get("recipients", [])):
        kids.append(_Entry("__recip_version1.0_#%08X" % i, T_STORAGE,
                           children=[_Entry(n, T_STREAM, d) for n, d in rec.items()]))
    embedded = spec.get("embedded", {})
    for i, att in enumerate(spec.get("attachments", [])):
        akids = [_Entry(n, T_STREAM, d) for n, d in att.items()]
        if i in embedded:
            # An embedded message: AttachMethod=5 + a PtypObject storage holding
            # the nested message's streams (real MSG layout for afEmbeddedMessage).
            akids.append(_spec_to_entries(embedded[i], "__substg1.0_3701000D"))
        kids.append(_Entry("__attach_version1.0_#%08X" % i, T_STORAGE, children=akids))
    if storage_name is None:
        return kids
    return _Entry(storage_name, T_STORAGE, children=kids)


def write_msg(path, spec):
    """Write a `.msg` fixture from a message spec dict (see _spec_to_entries)."""
    root = _Entry("Root Entry", T_ROOT)
    root.children = _spec_to_entries(spec)

    all_entries = [root]
    root.idx = 0

    def collect(e):
        for c in e.children:
            c.idx = len(all_entries)
            all_entries.append(c)
        for c in e.children:
            collect(c)

    collect(root)

    def set_tree(e):
        if e.children:
            e.child = _build_bst(e.children)
        for c in e.children:
            set_tree(c)

    set_tree(root)

    sectors, fat = [], []

    def alloc_regular(data):
        if not data:
            return ENDOFCHAIN
        n = (len(data) + SECT - 1) // SECT
        start = len(sectors)
        for i in range(n):
            sectors.append(data[i * SECT:(i + 1) * SECT].ljust(SECT, b"\x00"))
            fat.append(len(sectors) if i < n - 1 else ENDOFCHAIN)
        return start

    mini_data = bytearray()
    minifat = []
    for e in all_entries:
        if e.otype != T_STREAM:
            continue
        e.size = len(e.data)
        if e.size == 0:
            e.start = ENDOFCHAIN
        elif e.size >= CUTOFF:
            e.start = alloc_regular(e.data)
        else:
            n = (e.size + MINISECT - 1) // MINISECT
            e.start = len(minifat)
            for i in range(n):
                mini_data += e.data[i * MINISECT:(i + 1) * MINISECT].ljust(MINISECT, b"\x00")
                minifat.append(len(minifat) + 1 if i < n - 1 else ENDOFCHAIN)

    root.start = alloc_regular(bytes(mini_data))
    root.size = len(mini_data)

    per_fat = SECT // 4
    if minifat:
        minifat_full = minifat + [FREESECT] * ((-len(minifat)) % per_fat)
        minifat_bytes = b"".join(struct.pack("<I", v) for v in minifat_full)
        first_minifat = alloc_regular(minifat_bytes)
        num_minifat = len(minifat_bytes) // SECT
    else:
        first_minifat, num_minifat = ENDOFCHAIN, 0

    dir_bytes = b"".join(_pack_entry(e) for e in all_entries)
    n_slots = (len(dir_bytes) + SECT - 1) // SECT * (SECT // 128)
    dir_bytes += _pack_free() * (n_slots - len(all_entries))
    dir_start = alloc_regular(dir_bytes)

    nfat = 1
    while True:
        need = (len(sectors) + nfat + per_fat - 1) // per_fat
        if need == nfat:
            break
        nfat = need
    fat_start = len(sectors)
    for _ in range(nfat):
        sectors.append(None)
        fat.append(FATSECT)
    fat_full = fat + [FREESECT] * (nfat * per_fat - len(fat))
    fat_bytes = b"".join(struct.pack("<I", v) for v in fat_full)
    for i in range(nfat):
        sectors[fat_start + i] = fat_bytes[i * SECT:(i + 1) * SECT]

    hdr = bytearray(SECT)
    hdr[0:8] = SIG
    struct.pack_into("<H", hdr, 24, 0x003E)
    struct.pack_into("<H", hdr, 26, 0x0003)
    struct.pack_into("<H", hdr, 28, 0xFFFE)
    struct.pack_into("<H", hdr, 30, 0x0009)
    struct.pack_into("<H", hdr, 32, 0x0006)
    struct.pack_into("<I", hdr, 44, nfat)
    struct.pack_into("<I", hdr, 48, dir_start)
    struct.pack_into("<I", hdr, 56, CUTOFF)
    struct.pack_into("<I", hdr, 60, first_minifat)
    struct.pack_into("<I", hdr, 64, num_minifat)
    struct.pack_into("<I", hdr, 68, ENDOFCHAIN)
    difat = [fat_start + i for i in range(nfat)] + [FREESECT] * (109 - nfat)
    for i, v in enumerate(difat[:109]):
        struct.pack_into("<I", hdr, 76 + i * 4, v)

    Path(path).write_bytes(bytes(hdr) + b"".join(sectors))
    return path


def _pack_entry(e):
    name = e.name.encode("utf-16-le") + b"\x00\x00"
    buf = bytearray(128)
    buf[0:len(name)] = name
    struct.pack_into("<H", buf, 64, len(name))
    buf[66] = e.otype
    buf[67] = 1
    struct.pack_into("<I", buf, 68, e.left)
    struct.pack_into("<I", buf, 72, e.right)
    struct.pack_into("<I", buf, 76, e.child)
    struct.pack_into("<I", buf, 116, e.start)
    struct.pack_into("<Q", buf, 120, e.size)
    return bytes(buf)


def _pack_free():
    buf = bytearray(128)
    for off in (68, 72, 76):
        struct.pack_into("<I", buf, off, NOSTREAM)
    return bytes(buf)


# --- MAPI property-tag helpers (real Outlook tags) --------------------------

def substg(prop_id_hex, type_hex):
    return "__substg1.0_%s%s" % (prop_id_hex.upper(), type_hex.upper())


def u16(s):
    return s.encode("utf-16-le")


def filetime(dt):
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    delta = dt.astimezone(timezone.utc) - epoch
    return struct.pack("<Q", int(delta.total_seconds() * 10_000_000))


def _props_header(recip_count=0, attach_count=0):
    return (b"\x00" * 8 + struct.pack("<I", recip_count + 1)
            + struct.pack("<I", attach_count + 1)
            + struct.pack("<I", recip_count) + struct.pack("<I", attach_count)
            + b"\x00" * 8)


# Real MAPI property tags used by the corpus and the reader.
PID = {
    "Subject": "0037", "Body": "1000", "Html": "1013", "RtfCompressed": "1009",
    "SenderName": "0C1A", "SenderEmail": "0C1F", "SenderSmtp": "5D01",
    "MessageDeliveryTime": "0E06", "ClientSubmitTime": "0039", "CreationTime": "3007",
    "DisplayTo": "0E04", "DisplayCc": "0E03", "DisplayBcc": "0E02",
    "Importance": "0017", "MessageClass": "001A", "TransportHeaders": "007D",
    "DisplayName": "3001", "EmailAddress": "3003", "SmtpAddress": "39FE",
    "RecipientType": "0C15", "AddressType": "3002",
    "AttachLongFilename": "3707", "AttachFilename": "3704", "AttachMimeTag": "370E",
    "AttachContentId": "3712", "AttachMethod": "3705", "AttachDataObject": "3701",
    "AttachSize": "0E20",
}


def _str(pid_name, value):
    return {substg(PID[pid_name], "001F"): u16(value)}


def _int(pid_name, value):
    return {substg(PID[pid_name], "0003"): struct.pack("<I", value)}


def _time(pid_name, dt):
    return {substg(PID[pid_name], "0040"): filetime(dt)}


def _bin(pid_name, data):
    return {substg(PID[pid_name], "0102"): data}


def recipient(name, email, kind):
    """kind: 'to'|'cc'|'bcc' -> RecipientType 1/2/3."""
    rt = {"to": 1, "cc": 2, "bcc": 3}[kind]
    d = {"__properties_version1.0": _props_header()}
    d.update(_str("DisplayName", name))
    d.update({substg(PID["SmtpAddress"], "001F"): u16(email)})
    d.update({substg(PID["RecipientType"], "0003"): struct.pack("<I", rt)})
    return d


def attachment(filename, mime, data, *, content_id=None, method=1):
    d = {"__properties_version1.0": _props_header()}
    d.update({substg(PID["AttachLongFilename"], "001F"): u16(filename)})
    d.update({substg(PID["AttachMimeTag"], "001F"): u16(mime)})
    d.update({substg(PID["AttachMethod"], "0003"): struct.pack("<I", method)})
    d.update({substg(PID["AttachSize"], "0003"): struct.pack("<I", len(data))})
    if content_id:
        d.update({substg(PID["AttachContentId"], "001F"): u16(content_id)})
    d.update({substg(PID["AttachDataObject"], "0102"): data})
    return d


def message_spec(*, subject=None, sender_name=None, sender_email=None,
                 body=None, html=None, rtf_compressed=None,
                 delivery=None, submit=None, creation=None, importance=None,
                 recipients=None, attachments=None, embedded=None,
                 display_to=None):
    top = {"__properties_version1.0": _props_header(
        len(recipients or []), len(attachments or []))}
    top.update(_str("MessageClass", "IPM.Note"))
    if subject is not None:
        top.update(_str("Subject", subject))
    if sender_name is not None:
        top.update(_str("SenderName", sender_name))
    if sender_email is not None:
        top.update({substg(PID["SenderSmtp"], "001F"): u16(sender_email)})
    if body is not None:
        top.update(_str("Body", body))
    if html is not None:
        # Real .msg store PidTagHtml as PtypBinary UTF-8 bytes.
        top.update(_bin("Html", html.encode("utf-8")))
    if rtf_compressed is not None:
        top.update(_bin("RtfCompressed", rtf_compressed))
    if delivery is not None:
        top.update(_time("MessageDeliveryTime", delivery))
    if submit is not None:
        top.update(_time("ClientSubmitTime", submit))
    if creation is not None:
        top.update(_time("CreationTime", creation))
    if importance is not None:
        top.update(_int("Importance", importance))
    if display_to is not None:
        top.update(_str("DisplayTo", display_to))
    return {"top": top, "recipients": recipients or [],
            "attachments": attachments or [], "embedded": embedded or {}}


def lzfu_compressed(raw_size, payload=b"\x00\x00"):
    """A well-formed LZFu (PidTagRtfCompressed) header declaring ``raw_size``
    uncompressed bytes. Used to exercise the LZFu byte-cap without shipping a
    real decompressor. Header: compSize, rawSize, magic 'LZFu', crc."""
    body = struct.pack("<I", raw_size) + struct.pack("<I", 0x75465A4C) + b"\x00" * 4 + payload
    comp_size = len(body)
    return struct.pack("<I", comp_size) + body


def corpus():
    """The generated `.msg` parity corpus: list of (name, spec, authored_truth).

    Covers plain/HTML bodies, to/cc/bcc, an attachment, an inline `cid:` image,
    an embedded `.msg`, non-ASCII text, and importance set. ``authored_truth`` is
    the ground truth this corpus asserts against (the strong, portable AC3 gate);
    the Node `msgreader` cross-check is the independent oracle over the same bytes.
    """
    from datetime import datetime, timezone

    dt = datetime(2024, 3, 1, 12, 30, tzinfo=timezone.utc)
    items = []

    items.append(("plain", message_spec(
        subject="Plain hello", sender_name="Alice", sender_email="alice@corp.com",
        body="Just a plain body.", submit=dt,
        recipients=[recipient("Bob", "bob@corp.com", "to")]),
        {"subject": "Plain hello", "sender_email": "alice@corp.com",
         "recipient_emails": {"bob@corp.com"}, "kinds": {"to"},
         "body_kind": "plain", "attachment_names": set(), "embedded": 0}))

    items.append(("html_tocc bcc", message_spec(
        subject="HTML report", sender_name="Alice", sender_email="alice@corp.com",
        html="<h1>H</h1><p><b>Bold</b> and <a href='http://x'>link</a>.</p>",
        delivery=dt, importance=2,
        recipients=[recipient("Bob", "bob@corp.com", "to"),
                    recipient("Carol", "carol@corp.com", "cc"),
                    recipient("Dan", "dan@corp.com", "bcc")]),
        {"subject": "HTML report", "sender_email": "alice@corp.com",
         "recipient_emails": {"bob@corp.com", "carol@corp.com", "dan@corp.com"},
         "kinds": {"to", "cc", "bcc"}, "importance": "high",
         "body_kind": "html", "attachment_names": set(), "embedded": 0}))

    items.append(("attach_inline", message_spec(
        subject="With attachments", sender_name="Alice", sender_email="alice@corp.com",
        body="See attached.", submit=dt,
        recipients=[recipient("Bob", "bob@corp.com", "to")],
        attachments=[attachment("data.pdf", "application/pdf", b"%PDF-1.4 data"),
                     attachment("logo.png", "image/png", b"PNGDATA", content_id="cid1")]),
        {"subject": "With attachments", "sender_email": "alice@corp.com",
         "recipient_emails": {"bob@corp.com"}, "kinds": {"to"}, "body_kind": "plain",
         "attachment_names": {"data.pdf", "logo.png"}, "embedded": 0}))

    items.append(("nonascii", message_spec(
        subject="Café — déjà vu ☕", sender_name="Zoë", sender_email="zoe@corp.com",
        body="Naïve — résumé — 日本語.", submit=dt,
        recipients=[recipient("Bob", "bob@corp.com", "to")]),
        {"subject": "Café — déjà vu ☕", "sender_email": "zoe@corp.com",
         "recipient_emails": {"bob@corp.com"}, "kinds": {"to"}, "body_kind": "plain",
         "attachment_names": set(), "embedded": 0}))

    inner = message_spec(subject="Fwd inner", sender_name="Eve",
                         sender_email="eve@corp.com", body="inner body")
    items.append(("embedded", {
        **message_spec(
            subject="Has embedded", sender_name="Alice", sender_email="alice@corp.com",
            body="See forwarded.", submit=dt,
            recipients=[recipient("Bob", "bob@corp.com", "to")],
            attachments=[attachment("fwd.msg", "application/vnd.ms-outlook", b"",
                                    method=5)]),
        "embedded": {0: inner}},
        {"subject": "Has embedded", "sender_email": "alice@corp.com",
         "recipient_emails": {"bob@corp.com"}, "kinds": {"to"}, "body_kind": "plain",
         "attachment_names": {"fwd.msg"}, "embedded": 1}))

    return items


if __name__ == "__main__":  # smoke check
    import olefile
    p = write_msg("/tmp/fx.msg", message_spec(
        subject="Hi", sender_name="A", sender_email="a@x.com", body="hello",
        recipients=[recipient("B", "b@x.com", "to")],
        attachments=[attachment("r.pdf", "application/pdf", b"%PDF")]))
    print("isOle:", olefile.isOleFile(p))
