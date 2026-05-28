#!/usr/bin/env python3
"""arXiv retriever — unauthenticated public API wrapper.

metadata.shape: raw
metadata.description: Search arXiv for papers matching a query.
  Returns the first 10 results with title, authors, abstract, and URL.

This retriever is unauthenticated; no `metadata.auth` is declared.
See references/retriever-interface.md for the auth-shape convention.

Usage:
    python arxiv-retriever.py "query text"

Returns JSON on stdout matching the retriever-interface contract:
    {"content": str, "citations": [...], "shape": "raw"}

Dependencies: Python 3 stdlib only (urllib + xml).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def retrieve(query: str) -> dict:
    """Search arXiv; return the retriever-interface dict."""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 10,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        body = resp.read().decode("utf-8")

    root = ET.fromstring(body)
    entries = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = (entry.findtext(f"{ATOM_NS}title") or "").strip()
        summary = (entry.findtext(f"{ATOM_NS}summary") or "").strip()
        link = ""
        for link_el in entry.findall(f"{ATOM_NS}link"):
            if link_el.attrib.get("type") == "text/html":
                link = link_el.attrib.get("href", "")
                break
        if not link:
            link_el = entry.find(f"{ATOM_NS}id")
            link = (link_el.text or "").strip() if link_el is not None else ""
        authors = [
            (a.findtext(f"{ATOM_NS}name") or "").strip()
            for a in entry.findall(f"{ATOM_NS}author")
        ]
        entries.append(
            {
                "title": title,
                "authors": authors,
                "summary": summary,
                "url": link,
            }
        )

    content_lines = []
    citations = []
    for e in entries:
        content_lines.append(f"# {e['title']}")
        if e["authors"]:
            content_lines.append("Authors: " + ", ".join(e["authors"]))
        content_lines.append(e["summary"])
        content_lines.append("")
        citations.append(
            {
                "url": e["url"],
                "title": e["title"],
                "primacy": "primary",
            }
        )

    return {
        "content": "\n".join(content_lines).strip(),
        "citations": citations,
        "shape": "raw",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: arxiv-retriever.py <query>", file=sys.stderr)
        return 2
    query = " ".join(sys.argv[1:])
    try:
        result = retrieve(query)
    except urllib.error.HTTPError as exc:
        print(f"arxiv-retriever: HTTP {exc.code} — {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"arxiv-retriever: network error — {exc.reason}", file=sys.stderr)
        return 1
    except ET.ParseError as exc:
        print(f"arxiv-retriever: malformed XML response — {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
