#!/usr/bin/env python3
"""Perplexity Sonar retriever — env-broker authenticated.

metadata.auth: env
metadata.env: PERPLEXITY_API_KEY
metadata.shape: synthesized
metadata.description: Query Perplexity Sonar for a synthesised answer
  with citations. Requires PERPLEXITY_API_KEY in the environment.

Note: Perplexity does not expose citation primacy in its response; this
retriever tags every citation `secondary` as the conservative default
(a synthesis layer's citations are by nature derivative). The caller
must re-classify citations against the primacy taxonomy in
references/retriever-interface.md before applying `/research`'s
≥3-independent-sources triangulation rule, because three
non-independent `secondary` citations should not count as triangulated.

Usage:
    PERPLEXITY_API_KEY=... python perplexity-retriever.py "query text"

Returns JSON on stdout matching the retriever-interface contract:
    {"content": str, "citations": [...], "shape": "synthesized"}

Dependencies: Python 3 stdlib only (urllib + json).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

PERPLEXITY_API = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"


def retrieve(query: str) -> dict:
    """Query Perplexity Sonar; return the retriever-interface dict."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "PERPLEXITY_API_KEY not set in environment. "
            "This retriever uses the env broker; set the key and retry."
        )

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Answer the user's question with citations. "
                    "Be concise; the caller will integrate."
                ),
            },
            {"role": "user", "content": query},
        ],
    }
    req = urllib.request.Request(
        PERPLEXITY_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    # B310: constant https Perplexity API base.
    with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310
        body = json.loads(resp.read().decode("utf-8"))

    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = (message.get("content") or "").strip()
    raw_citations = body.get("citations") or []

    citations = []
    for cite in raw_citations:
        if isinstance(cite, str):
            citations.append(
                {"url": cite, "title": cite, "primacy": "secondary"}
            )
        elif isinstance(cite, dict):
            citations.append(
                {
                    "url": cite.get("url", ""),
                    "title": cite.get("title", cite.get("url", "")),
                    "primacy": "secondary",
                }
            )

    return {
        "content": content,
        "citations": citations,
        "shape": "synthesized",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: perplexity-retriever.py <query>", file=sys.stderr)
        return 2
    query = " ".join(sys.argv[1:])
    try:
        result = retrieve(query)
    except RuntimeError as exc:
        print(f"perplexity-retriever: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        print(f"perplexity-retriever: HTTP {exc.code} — {exc.reason}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
