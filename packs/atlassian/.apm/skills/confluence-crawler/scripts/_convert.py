"""Convert Confluence storage-format XHTML to Markdown.

Handles an allowlist of macros (code, info, warning, note, tip, panel,
expand, status). Unknown macros are dropped with a small HTML comment
marker so output stays reviewable.
"""
from __future__ import annotations

import html
import logging
import re

from lxml import etree
from markdownify import markdownify

from _links import LinkTargets, attachment_href, page_href

log = logging.getLogger("confluence_crawler.convert")

AC_NS = "http://atlassian.com/content"
RI_NS = "http://atlassian.com/resource/identifier"
NSMAP = {"ac": AC_NS, "ri": RI_NS}

ALLOWED_MACROS = {
    "code",
    "info",
    "warning",
    "note",
    "tip",
    "panel",
    "expand",
    "status",
}

# Admonition label + CSS-like class for blockquote rendering.
PANEL_LABELS = {
    "info": "INFO",
    "note": "NOTE",
    "tip": "TIP",
    "warning": "WARNING",
    "panel": "PANEL",
}

_HTML_ENTITY_RE = re.compile(r"&([a-zA-Z][a-zA-Z0-9]+);")


def _escape_entities(xhtml: str) -> str:
    """Convert named HTML entities (e.g. &nbsp;) to numeric form so the XML
    parser doesn't choke. Keeps the five XML-predefined entities as-is."""
    xml_safe = {"amp", "lt", "gt", "quot", "apos"}

    def sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in xml_safe:
            return match.group(0)
        codepoint = html.entities.name2codepoint.get(name)
        if codepoint is None:
            return match.group(0)
        return f"&#{codepoint};"

    return _HTML_ENTITY_RE.sub(sub, xhtml)


def _parse(storage_xhtml: str) -> etree._Element:
    wrapped = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<root xmlns:ac="{AC_NS}" xmlns:ri="{RI_NS}">'
        f"{_escape_entities(storage_xhtml)}"
        f"</root>"
    )
    parser = etree.XMLParser(recover=True, resolve_entities=False)
    return etree.fromstring(wrapped.encode("utf-8"), parser=parser)


def _q(prefix: str, name: str) -> str:
    return f"{{{NSMAP[prefix]}}}{name}"


def _text_of(element: etree._Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _inner_xml(element: etree._Element) -> str:
    """Serialize children of `element` back to XHTML (no outer tag)."""
    parts: list[str] = []
    if element.text:
        parts.append(html.escape(element.text, quote=False))
    for child in element:
        parts.append(
            etree.tostring(child, encoding="unicode", with_tail=True, method="xml")
        )
    return "".join(parts)


def _macro_params(macro: etree._Element) -> dict[str, str]:
    params: dict[str, str] = {}
    for p in macro.findall(_q("ac", "parameter")):
        name = p.get(_q("ac", "name")) or ""
        if name:
            params[name] = _text_of(p)
    return params


def _replace(element: etree._Element, replacement_xml: str) -> None:
    """Replace `element` with parsed XML fragment while preserving tail text."""
    tail = element.tail or ""
    wrapped = f"<wrap>{replacement_xml}</wrap>"
    try:
        frag = etree.fromstring(wrapped)
    except etree.XMLSyntaxError:
        log.warning("replacement parse failed; dropping macro")
        frag = etree.fromstring("<wrap></wrap>")
    parent = element.getparent()
    if parent is None:
        return
    idx = parent.index(element)
    parent.remove(element)
    prev_tail_holder = parent[idx - 1] if idx > 0 else None
    leading_text = frag.text or ""
    # lxml moves children when inserted, so capture the list and the last node now.
    frag_children = list(frag)
    if leading_text:
        if frag_children:
            frag_children[0].text = leading_text + (frag_children[0].text or "")
        elif prev_tail_holder is not None:
            prev_tail_holder.tail = (prev_tail_holder.tail or "") + leading_text
        else:
            parent.text = (parent.text or "") + leading_text
    for i, child in enumerate(frag_children):
        parent.insert(idx + i, child)
    if frag_children:
        last = frag_children[-1]
        last.tail = (last.tail or "") + tail
    elif not leading_text:
        if prev_tail_holder is not None:
            prev_tail_holder.tail = (prev_tail_holder.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    elif prev_tail_holder is not None:
        prev_tail_holder.tail = (prev_tail_holder.tail or "") + tail
    else:
        parent.text = (parent.text or "") + tail


def _transform_structured_macro(
    macro: etree._Element,
    page_id: str,
    targets: LinkTargets,
) -> None:
    name = (macro.get(_q("ac", "name")) or "").lower()
    params = _macro_params(macro)
    body = macro.find(_q("ac", "rich-text-body"))
    plain = macro.find(_q("ac", "plain-text-body"))

    if name == "code":
        language = params.get("language", "").strip()
        code = _text_of(plain)
        lang_attr = f' class="language-{html.escape(language)}"' if language else ""
        replacement = f"<pre{lang_attr}><code>{html.escape(code)}</code></pre>"
    elif name in PANEL_LABELS:
        label = PANEL_LABELS[name]
        title = params.get("title", "")
        header = f"<strong>[{label}]</strong>" + (
            f" <strong>{html.escape(title)}</strong>" if title else ""
        )
        inner = _process_inline_tree(body, page_id, targets) if body is not None else ""
        replacement = f"<blockquote><p>{header}</p>{inner}</blockquote>"
    elif name == "expand":
        title = html.escape(params.get("title", "Details"))
        inner = _process_inline_tree(body, page_id, targets) if body is not None else ""
        # markdownify drops <details>/<summary>; render as bold header + blockquote body.
        replacement = f"<p><strong>{title}</strong></p><blockquote>{inner}</blockquote>"
    elif name == "status":
        title = params.get("title", "").strip()
        color = params.get("colour", "").strip().upper()
        label = title or color or "STATUS"
        replacement = f"<strong>[{html.escape(label)}]</strong>"
    elif name in ALLOWED_MACROS:
        replacement = ""
    else:
        replacement = f"<p><em>[confluence macro not rendered: {html.escape(name)}]</em></p>"

    _replace(macro, replacement)


def _process_inline_tree(
    element: etree._Element | None,
    page_id: str,
    targets: LinkTargets,
) -> str:
    """Process a subtree to HTML (applies macro + link transforms, returns
    the inner HTML of `element`)."""
    if element is None:
        return ""
    _transform_in_place(element, page_id, targets)
    return _inner_xml(element)


def _transform_ac_link(link: etree._Element, page_id: str, targets: LinkTargets) -> None:
    page_ref = link.find(_q("ri", "page"))
    attach_ref = link.find(_q("ri", "attachment"))
    url_ref = link.find(_q("ri", "url"))
    body_el = link.find(_q("ac", "link-body"))
    plain_body = link.find(_q("ac", "plain-text-link-body"))

    if body_el is not None:
        label = _inner_xml(body_el) or "link"
    elif plain_body is not None:
        label = html.escape(_text_of(plain_body))
    elif page_ref is not None:
        label = html.escape(page_ref.get(_q("ri", "content-title"), "link"))
    elif attach_ref is not None:
        label = html.escape(attach_ref.get(_q("ri", "filename"), "attachment"))
    else:
        label = "link"

    if page_ref is not None:
        href = page_href(
            targets,
            space_key=page_ref.get(_q("ri", "space-key")),
            title=page_ref.get(_q("ri", "content-title")),
            page_id=None,
            webui_fallback=None,
        )
    elif attach_ref is not None:
        href = attachment_href(
            targets,
            page_id=page_id,
            filename=attach_ref.get(_q("ri", "filename"), "") or "",
        )
    elif url_ref is not None:
        href = url_ref.get(_q("ri", "value")) or "#"
    else:
        href = "#"

    _replace(link, f'<a href="{html.escape(href, quote=True)}">{label}</a>')


def _transform_ac_image(img: etree._Element, page_id: str, targets: LinkTargets) -> None:
    attach_ref = img.find(_q("ri", "attachment"))
    url_ref = img.find(_q("ri", "url"))
    alt = img.get(_q("ac", "alt")) or ""
    width = img.get(_q("ac", "width"))
    height = img.get(_q("ac", "height"))

    if attach_ref is not None:
        src = attachment_href(
            targets,
            page_id=page_id,
            filename=attach_ref.get(_q("ri", "filename"), "") or "",
        )
    elif url_ref is not None:
        src = url_ref.get(_q("ri", "value")) or ""
    else:
        _replace(img, "")
        return

    attrs = [f'src="{html.escape(src, quote=True)}"', f'alt="{html.escape(alt, quote=True)}"']
    if width:
        attrs.append(f'width="{html.escape(width, quote=True)}"')
    if height:
        attrs.append(f'height="{html.escape(height, quote=True)}"')
    _replace(img, f"<img {' '.join(attrs)}/>")


def _transform_in_place(
    root: etree._Element,
    page_id: str,
    targets: LinkTargets,
) -> None:
    # Work on a materialized list because we mutate the tree.
    for macro in list(root.iter(_q("ac", "structured-macro"))):
        if macro.getparent() is None:
            continue
        _transform_structured_macro(macro, page_id, targets)
    for link in list(root.iter(_q("ac", "link"))):
        if link.getparent() is None:
            continue
        _transform_ac_link(link, page_id, targets)
    for img in list(root.iter(_q("ac", "image"))):
        if img.getparent() is None:
            continue
        _transform_ac_image(img, page_id, targets)
    # Strip remaining unknown ac:/ri: elements (e.g. ac:task-list) as comments.
    for el in list(root.iter()):
        if el.getparent() is None:
            continue
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag.startswith(f"{{{AC_NS}}}") or tag.startswith(f"{{{RI_NS}}}"):
            _replace(el, "")


def to_markdown(
    storage_xhtml: str,
    *,
    page_id: str,
    targets: LinkTargets,
) -> str:
    if not storage_xhtml.strip():
        return ""
    root = _parse(storage_xhtml)
    _transform_in_place(root, page_id, targets)
    cleaned_html = _inner_xml(root)
    def _lang(tag: object) -> str:
        cls = getattr(tag, "get", lambda _k: None)("class") or ""
        if isinstance(cls, list):
            cls = " ".join(cls)
        for token in cls.split():
            if token.startswith("language-"):
                return token[len("language-"):]
        return ""

    md = markdownify(
        cleaned_html,
        heading_style="ATX",
        bullets="-",
        code_language_callback=_lang,
    )
    # Collapse >2 consecutive blank lines.
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
