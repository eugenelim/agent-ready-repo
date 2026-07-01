#!/usr/bin/env python3
"""
convert.py — convert Outlook `.msg` and MIME `.eml` email to Markdown at Tier 0.

The Python port of the `msg-to-markdown` skill (RFC-0058 Open-Q2 / ADR-0045).
It replaces the Node runtime and the `@nicecode/msg-reader` / `msgreader` npm
packages: `.msg` is read via `olefile` + first-party MAPI decoding (`mapi.py`,
ADR-0046) and `.eml` via the stdlib `email` package, both populating **one**
internal email model that a single renderer turns into Markdown. Every output
carries the unified Tier-0 output contract (`contract.build_frontmatter`) and is
written through an output-path confinement guard (`safe_io.confine`).

A `.msg`/`.eml` is untrusted input, so the skill enforces its own resource
ceilings (see `mapi.py`), confines every attachment/output write, bounds
embedded-message recursion, makes no network call, and loads no ML/OCR model.

Usage:
    python scripts/convert.py <file.msg|file.eml> [more ...]
    python scripts/convert.py --attachments <file.msg|file.eml>   # confined extract
    python scripts/convert.py --check [olefile]                   # probe the reader

Stdout markers (parsed by callers — do not rename without sign-off):
    WROTE: <path>        — the written Markdown file
    SUMMARY: <json>      — a one-line summary of the conversion
    EXTRACTED: <path>    — an extracted attachment (attachments sub-command)
    SKIPPED: <reason>    — an attachment that was not extracted
    WARNING: <msg>       — non-fatal issue (requires-review)
"""
from __future__ import annotations

import json
import sys
from datetime import timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

import contract
import html_md
import mapi
import safe_io

# olefile is resolved pip-on-demand via --check, never auto-installed (mirrors
# file-to-markdown's optional-library pattern). Pin a minimum version (ADR-0046).
OPTIONAL_LIBS = {"olefile": "python -m pip install 'olefile>=0.47'"}

SUPPORTED_EXTS = {".msg", ".eml"}


# --- .eml reader → the same internal model ----------------------------------


def read_eml(path: Path) -> mapi.EmailModel:
    """Parse a `.eml` (MIME) file into the shared EmailModel, walking multipart
    bodies (preferred text/plain vs text/html) and nested message/rfc822 parts,
    bounded by the same recursion caps + cumulative budget as `.msg`."""
    import email
    from email import policy

    try:
        msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    except Exception as exc:
        raise mapi.MsgParseError(f"malformed .eml: {exc}") from exc
    budget = mapi._Budget()
    return _eml_message_to_model(msg, budget, depth=0, counters={"embedded": 0})


def _eml_message_to_model(msg, budget, depth, counters) -> mapi.EmailModel:
    from email.utils import getaddresses, parseaddr, parsedate_to_datetime

    m = mapi.EmailModel()
    m.subject = str(msg["Subject"]) if msg["Subject"] else None
    fn, fe = parseaddr(str(msg.get("From", "")))
    m.sender_name, m.sender_email = fn or None, fe or None

    for header, kind in (("To", "to"), ("Cc", "cc"), ("Bcc", "bcc")):
        for nm, em in getaddresses(msg.get_all(header, [])):
            if nm or em:
                m.recipients.append(mapi.Recipient(name=nm, email=em, kind=kind))

    if msg["Date"]:
        try:
            dt = parsedate_to_datetime(str(msg["Date"]))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            m.date = dt.astimezone(timezone.utc).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            m.date = None

    imp = (str(msg["Importance"]).lower() if msg["Importance"] else None)
    if imp in ("high", "normal", "low"):
        m.importance = imp

    # Body: preferred text/plain, else text/html reduced to Markdown.
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
    except Exception:
        part = None
    if part is not None:
        content = part.get_content()
        budget.take(len(content.encode("utf-8", errors="replace")))
        if part.get_content_type() == "text/html":
            m.body_kind, m.body_text = "html", content
        else:
            m.body_kind, m.body_text = "plain", content

    for part in msg.iter_attachments():
        ctype = part.get_content_type()
        if ctype == "message/rfc822":
            filename = part.get_filename() or "embedded-message.eml"
            m.attachments.append(mapi.Attachment(
                filename=filename, size=None, ctype=ctype, inline=False,
                is_embedded_msg=True))
            if depth + 1 > mapi.MAX_EMBED_DEPTH or counters["embedded"] >= mapi.MAX_EMBED_COUNT:
                m.notes.append(
                    "A nested message was not traversed: the recursion depth "
                    f"({mapi.MAX_EMBED_DEPTH}) or count ({mapi.MAX_EMBED_COUNT}) cap was reached.")
                m.requires_review = True
                continue
            counters["embedded"] += 1
            sub_msg = part.get_content()
            sub = _eml_message_to_model(sub_msg, budget, depth + 1, counters)
            m.embedded_subjects.append(sub.subject or "(no subject)")
            m.notes.extend(sub.notes)
            if sub.requires_review:
                m.requires_review = True
        else:
            try:
                payload = part.get_content()
            except Exception:
                payload = b""
            raw = payload if isinstance(payload, bytes) else str(payload).encode("utf-8", "replace")
            budget.take(len(raw))
            m.attachments.append(mapi.Attachment(
                filename=part.get_filename() or "unnamed",
                size=len(raw), ctype=ctype,
                inline=(part.get_content_disposition() == "inline" or bool(part["Content-ID"])),
                is_embedded_msg=False))
    return m


# --- Rendering --------------------------------------------------------------


def _cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def _fmt_size(size) -> str:
    if not isinstance(size, int):
        return "—"
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def _fmt_recips(recips) -> str:
    parts = []
    for r in recips:
        s = r.name or ""
        if r.email:
            s += f" <{r.email}>"
        parts.append(_cell(s.strip()))
    return "; ".join(p for p in parts if p) or "—"


def render(m: mapi.EmailModel) -> str:
    lines = [f"# {m.subject or 'No Subject'}", "", "| Field | Value |", "| --- | --- |"]
    frm = (m.sender_name or "")
    if m.sender_email:
        frm += f" <{m.sender_email}>"
    lines.append(f"| **From** | {_cell(frm.strip()) or '—'} |")
    to = [r for r in m.recipients if r.kind == "to"]
    cc = [r for r in m.recipients if r.kind == "cc"]
    bcc = [r for r in m.recipients if r.kind == "bcc"]
    lines.append(f"| **To** | {_fmt_recips(to)} |")
    if cc:
        lines.append(f"| **CC** | {_fmt_recips(cc)} |")
    if bcc:
        lines.append(f"| **BCC** | {_fmt_recips(bcc)} |")
    if m.date:
        lines.append(f"| **Date** | {_cell(m.date)} |")
    if m.importance and m.importance != "normal":
        lines.append(f"| **Importance** | {_cell(m.importance)} |")
    lines += ["", "---", ""]

    body = html_md.html_to_markdown(m.body_text) if m.body_kind == "html" else m.body_text
    lines.append(body.strip() if body.strip() else "*No message body found.*")
    lines.append("")

    if m.attachments:
        lines += ["---", "", "## Attachments", "", "| # | Filename | Size | Type |",
                  "| --- | --- | --- | --- |"]
        for i, a in enumerate(m.attachments, 1):
            name = _cell(a.filename) + (" (inline)" if a.inline else "")
            ext = Path(a.filename).suffix.lower() or "—"
            lines.append(f"| {i} | {name} | {_fmt_size(a.size)} | {_cell(a.ctype) or ext} |")
        lines.append("")

    embedded = [a for a in m.attachments if a.is_embedded_msg]
    if embedded:
        note = f"> **Note:** This email contains {len(embedded)} embedded message(s)"
        if m.embedded_subjects:
            note += " (" + "; ".join(_cell(s) for s in m.embedded_subjects) + ")"
        note += ". Run this skill on the extracted .msg file(s) to convert them as well."
        lines += [note, ""]

    for n in m.notes:
        lines += [f"> {n}", ""]

    return "\n".join(lines).rstrip("\n") + "\n"


# --- Assemble + confined write ----------------------------------------------


def assemble(m: mapi.EmailModel, content_type: str, source_name: str) -> str:
    fields = {
        "source-file": source_name,
        "content-type": content_type,
        "ingestion-date": contract.now_iso(),
    }
    frontmatter = contract.build_frontmatter(
        tier=contract.TIER_0,
        extraction_confidence="low" if m.requires_review else "high",
        requires_review=m.requires_review,
        fields=fields,
    )
    return frontmatter + "\n\n" + render(m).rstrip("\n") + "\n"


def _refused_doc(content_type: str, source_name: str, message: str) -> str:
    fields = {
        "source-file": source_name,
        "content-type": content_type,
        "ingestion-date": contract.now_iso(),
    }
    frontmatter = contract.build_frontmatter(
        tier=contract.TIER_0, extraction_confidence="low", requires_review=True,
        fields=fields)
    return frontmatter + "\n\n> **Not extracted.** " + message + "\n"


def write_output(input_path: Path, text: str) -> Path:
    root = input_path.resolve().parent
    output_path = safe_io.confine(root / (input_path.stem + ".md"), root)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def convert_file(input_path: Path) -> None:
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        print(f"ERROR: Unsupported file type '{ext}'. Supported: .msg, .eml",
              file=sys.stderr)
        sys.exit(1)
    if ext == ".msg" and not _lib_available("olefile"):
        print("ERROR: reading .msg needs 'olefile', which is not installed. "
              f"Install it ({OPTIONAL_LIBS['olefile']}) and retry.", file=sys.stderr)
        sys.exit(2)

    content_type = "msg" if ext == ".msg" else "eml"
    model = None
    try:
        safe_io.check_input_size(input_path)
        model = mapi.read_msg(input_path) if ext == ".msg" else read_eml(input_path)
        text = assemble(model, content_type, input_path.name)
    except (safe_io.ResourceCeilingError, mapi.MsgResourceError, mapi.MsgParseError) as exc:
        text = _refused_doc(content_type, input_path.name, str(exc))

    output_path = write_output(input_path, text)
    print(f"WROTE: {output_path}")
    print("SUMMARY: " + json.dumps(_summary(model, content_type)))
    if model is None or model.requires_review:
        print("WARNING: extraction flagged requires-review (low confidence)")


def _summary(m: mapi.EmailModel | None, content_type: str) -> dict:
    if m is None:
        return {"contentType": content_type, "refused": True}
    to = [r for r in m.recipients if r.kind == "to"]
    return {
        "contentType": content_type,
        "subject": m.subject or "No Subject",
        "from": m.sender_name or m.sender_email or "Unknown",
        "to": _fmt_recips(to),
        "date": m.date or "Unknown",
        "hasHtmlBody": m.body_kind == "html",
        "hasPlainBody": m.body_kind == "plain",
        "bodyLength": len(m.body_text),
        "attachmentCount": len(m.attachments),
        "embeddedMsgCount": sum(1 for a in m.attachments if a.is_embedded_msg),
        "ccCount": sum(1 for r in m.recipients if r.kind == "cc"),
        "bccCount": sum(1 for r in m.recipients if r.kind == "bcc"),
        "requiresReview": m.requires_review,
    }


# --- Confined attachment extraction (AC6) -----------------------------------


def safe_basename(name: str) -> str | None:
    """Reduce an attacker-controlled stored filename to a confined basename.

    Refuses empty / `.` / `..` / absolute / drive / UNC names; otherwise reduces
    to the final component under **both** POSIX and Windows separators. Returns
    None on refusal. `safe_io.confine` is the belt-and-suspenders second check."""
    if not name or name in (".", ".."):
        return None
    if PurePosixPath(name).is_absolute() or PureWindowsPath(name).is_absolute():
        return None
    if PureWindowsPath(name).drive or name.startswith(("\\\\", "//")):
        return None
    base = PureWindowsPath(PurePosixPath(name).name).name.strip()
    if not base or base in (".", ".."):
        return None
    # Reject embedded NUL / control chars (C0, DEL, and C1): unwritable
    # (write_bytes raises on a NUL) and undisplayable — fail-soft to SKIPPED
    # rather than crash the loop.
    if any(ord(ch) < 32 or 0x7F <= ord(ch) <= 0x9F for ch in base):
        return None
    return base


def extract_attachments(input_path: Path) -> None:
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        print(f"ERROR: Unsupported file type '{ext}'. Supported: .msg, .eml",
              file=sys.stderr)
        sys.exit(1)
    if ext == ".msg" and not _lib_available("olefile"):
        print("ERROR: reading .msg needs 'olefile', which is not installed. "
              f"Install it ({OPTIONAL_LIBS['olefile']}).", file=sys.stderr)
        sys.exit(2)

    try:
        safe_io.check_input_size(input_path)
        raws = (mapi.read_attachments(input_path) if ext == ".msg"
                else _eml_raw_attachments(input_path))
    except (safe_io.ResourceCeilingError, mapi.MsgResourceError, mapi.MsgParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not raws:
        print("No attachments to extract.")
        return

    out_dir = input_path.resolve().parent / (input_path.stem + "_attachments")
    if out_dir.is_symlink():
        print(f"ERROR: refusing to extract into a symlinked directory: {out_dir}",
              file=sys.stderr)
        sys.exit(1)
    out_dir.mkdir(exist_ok=True)

    for raw in raws:
        if raw.data is None:
            print(f"SKIPPED (embedded message, no flat content): {raw.filename or '(unnamed)'}")
            continue
        base = safe_basename(raw.filename)
        if base is None:
            print(f"SKIPPED (unsafe filename): {raw.filename!r}")
            continue
        try:
            target = safe_io.confine(out_dir / base, out_dir)
        except ValueError:
            print(f"SKIPPED (path escapes extraction dir): {raw.filename!r}")
            continue
        try:
            target.write_bytes(raw.data)
        except (OSError, ValueError) as exc:
            # A filename the filesystem rejects must not abort the whole loop.
            print(f"SKIPPED (unwritable filename): {raw.filename!r} ({exc})")
            continue
        print(f"EXTRACTED: {target}")


def _eml_raw_attachments(input_path: Path) -> list[mapi.RawAttachment]:
    import email
    from email import policy

    # check_input_size is enforced by the caller (extract_attachments).
    msg = email.message_from_bytes(input_path.read_bytes(), policy=policy.default)
    budget = mapi._Budget()
    out: list[mapi.RawAttachment] = []
    for part in msg.iter_attachments():
        if part.get_content_type() == "message/rfc822":
            out.append(mapi.RawAttachment(
                filename=part.get_filename() or "embedded-message.eml",
                data=None, is_embedded_msg=True))
            continue
        try:
            payload = part.get_content()
        except Exception:
            payload = b""
        data = payload if isinstance(payload, bytes) else str(payload).encode("utf-8", "replace")
        budget.take(len(data))
        out.append(mapi.RawAttachment(
            filename=part.get_filename() or "", data=data, is_embedded_msg=False))
    return out


# --- CLI --------------------------------------------------------------------


def _lib_available(import_name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(import_name) is not None


def cmd_check(names: list[str]) -> int:
    targets = names or list(OPTIONAL_LIBS)
    missing = False
    for name in targets:
        present = _lib_available(name)
        print(f"{name}: {'present' if present else 'absent'}")
        if not present:
            missing = True
            if name in OPTIONAL_LIBS:
                print(f"  install: {OPTIONAL_LIBS[name]}", file=sys.stderr)
    return 2 if missing else 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: convert.py <file.msg|file.eml> [...] | --attachments <file> "
              "| --check [olefile]", file=sys.stderr)
        return 1
    if args[0] == "--check":
        return cmd_check(args[1:])
    if args[0] == "--attachments":
        if len(args) != 2:
            print("Usage: convert.py --attachments <file.msg|file.eml>", file=sys.stderr)
            return 1
        extract_attachments(Path(args[1]))
        return 0
    for arg in args:
        convert_file(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
