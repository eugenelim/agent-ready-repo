"""Markdown / text / storage-XHTML → Confluence storage-format XHTML.

Internal module — not invoked by the agent directly.

The conversion mirrors confluence-crawler's allowlist so a crawl →
edit → publish round-trip preserves macros: code, info, warning,
note, tip, panel, expand.

Three input modes:
- ``markdown``: render CommonMark via markdown-it-py, then post-process
  the HTML for callout admonitions, code-fence macros, and image
  attachment rewrites.
- ``storage``: treat input as already-valid Confluence storage XHTML;
  return as-is. Escape hatch.
- ``text``: wrap each non-empty line in a ``<p>`` element. "Publish
  this string" path.
"""
from __future__ import annotations

import html
import re
import urllib.parse
from typing import Iterable

# markdown-it-py is the maintained CommonMark renderer; output is plain HTML.
from markdown_it import MarkdownIt

INPUT_MARKDOWN = "markdown"
INPUT_STORAGE = "storage"
INPUT_TEXT = "text"

ALLOWED_INPUT_FORMATS = (INPUT_MARKDOWN, INPUT_STORAGE, INPUT_TEXT)

# Bold-leadin admonitions mapping to Confluence macros — same vocabulary
# the crawler reverses.
_ADMONITION_MACROS = {
    "note": "note",
    "tip": "tip",
    "warning": "warning",
    "info": "info",
    "important": "warning",
}

# DOTALL so the body can span the soft-break newlines markdown-it-py
# emits inside a single <p>. MULTILINE not needed — we anchor on the
# literal <p>/</p> tags.
_ADMONITION_RE = re.compile(
    r"<p>\s*<strong>(Note|Tip|Warning|Info|Important):</strong>\s*(.*?)</p>",
    re.IGNORECASE | re.DOTALL,
)

_CODE_BLOCK_RE = re.compile(
    r"<pre><code(?:\s+class=\"language-(?P<lang>[^\"]+)\")?>(?P<body>.*?)</code></pre>",
    re.DOTALL,
)

_SELF_CLOSE_TAGS = ("br", "hr", "img")


def _self_close(html_text: str) -> str:
    out = html_text
    for tag in _SELF_CLOSE_TAGS:
        out = re.sub(
            rf"<{tag}([^>]*?)(?<!/)>",
            rf"<{tag}\1/>",
            out,
            flags=re.IGNORECASE,
        )
    return out


def _wrap_code_macro(match: re.Match[str]) -> str:
    lang = match.group("lang") or ""
    body = match.group("body")
    # The body has been HTML-escaped by markdown-it; reverse it for CDATA.
    raw = html.unescape(body)
    # Confluence stores plain-text-body in CDATA so escapes are not needed.
    lang_param = (
        f'<ac:parameter ac:name="language">{html.escape(lang)}</ac:parameter>'
        if lang
        else ""
    )
    safe_cdata = raw.replace("]]>", "]]]]><![CDATA[>")
    return (
        '<ac:structured-macro ac:name="code">'
        f"{lang_param}"
        f"<ac:plain-text-body><![CDATA[{safe_cdata}]]></ac:plain-text-body>"
        "</ac:structured-macro>"
    )


def _wrap_admonition_macro(match: re.Match[str]) -> str:
    label = match.group(1).lower()
    body = match.group(2).strip()
    macro = _ADMONITION_MACROS.get(label, "info")
    return (
        f'<ac:structured-macro ac:name="{macro}">'
        f"<ac:rich-text-body><p>{body}</p></ac:rich-text-body>"
        "</ac:structured-macro>"
    )


def _rewrite_image_attachments(html_text: str, attachment_filenames: Iterable[str]) -> str:
    names = set(attachment_filenames)
    if not names:
        return html_text

    def sub(match: re.Match[str]) -> str:
        attrs = match.group("attrs") or ""
        src_match = re.search(r'src="([^"]+)"', attrs)
        if not src_match:
            return match.group(0)
        src = src_match.group(1)
        # URL-encoded markdown like My%20Image.png needs to be decoded
        # before comparing against the on-disk attachment basename.
        filename = urllib.parse.unquote(src.split("/")[-1])
        if filename not in names:
            return match.group(0)
        alt_match = re.search(r'alt="([^"]*)"', attrs)
        alt = alt_match.group(1) if alt_match else ""
        alt_attr = f' ac:alt="{html.escape(alt, quote=True)}"' if alt else ""
        return (
            f"<ac:image{alt_attr}>"
            f'<ri:attachment ri:filename="{html.escape(filename, quote=True)}"/>'
            "</ac:image>"
        )

    return re.sub(r"<img(?P<attrs>[^>]*)/?>", sub, html_text)


def markdown_to_storage(
    md_text: str,
    *,
    attachment_filenames: Iterable[str] = (),
) -> str:
    """Render Markdown to Confluence storage XHTML.

    Pipeline: markdown-it-py renders to HTML → callout paragraphs get
    macro-wrapped → code fences get macro-wrapped → image refs matching
    an attachment filename are rewritten to <ac:image> → self-closing
    void elements normalised for XHTML.
    """
    md = MarkdownIt("commonmark", {"html": False, "breaks": False, "linkify": False})
    rendered = md.render(md_text)

    # Wrap code fences first (their HTML structure is the cleanest signal
    # before we start splicing macros for callouts).
    rendered = _CODE_BLOCK_RE.sub(_wrap_code_macro, rendered)

    # Callout admonitions — match against the full document so soft-break
    # paragraphs (multi-line <p>) are still detected.
    rendered = _ADMONITION_RE.sub(_wrap_admonition_macro, rendered)

    rendered = _rewrite_image_attachments(rendered, attachment_filenames)
    rendered = _self_close(rendered)
    return rendered.strip()


def text_to_storage(text: str) -> str:
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    return "\n".join(f"<p>{html.escape(p)}</p>" for p in paras)


def as_storage_xhtml(
    body: str,
    *,
    input_format: str,
    attachment_filenames: Iterable[str] = (),
) -> str:
    if input_format == INPUT_STORAGE:
        return body.strip()
    if input_format == INPUT_TEXT:
        return text_to_storage(body)
    if input_format == INPUT_MARKDOWN:
        return markdown_to_storage(body, attachment_filenames=attachment_filenames)
    raise ValueError(
        f"unknown input format {input_format!r}; expected one of "
        + ", ".join(ALLOWED_INPUT_FORMATS)
    )


_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def extract_title_from_markdown(md_text: str) -> str | None:
    """Return the first H1 heading text, or None if none."""
    match = _H1_RE.search(md_text)
    return match.group(1).strip() if match else None
