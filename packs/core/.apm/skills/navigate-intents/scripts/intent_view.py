"""Offline view assembly and publication for the navigate-intents export.

Receives the payload that ``navigate_intents.build_view_payload`` builds and
never derives the intent graph itself.  Standard-library-only.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from datetime import UTC as _UTC
except ImportError:  # Python < 3.11
    _UTC = _dt.timezone.utc  # type: ignore[assignment]  # noqa: UP017

# Characters that must never appear raw inside the HTML data block.
_DATA_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    " ": "\\u2028",
    " ": "\\u2029",
}


class ViewRefusal(Exception):
    """A refusal to build or publish the view, carrying the closed error fields."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        limits: dict[str, Any] | None = None,
        observed: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.limits = limits or {}
        self.observed = observed or {}


def source_links(
    root: Path, nodes: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Map each node id to its source link and return the commit used, or None.

    Every link is inert (the repository-relative path as plain text).
    """
    return {n["id"]: {"kind": "inert", "path": n.get("path", "")} for n in nodes}, None


def data_block_json(payload: dict[str, Any]) -> str:
    """Serialise *payload* so it is safe inside a ``<script>`` data block."""
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    for raw, escaped in _DATA_ESCAPES.items():
        text = text.replace(raw, escaped)
    return text


def build_html(payload: dict[str, Any]) -> str:
    """Return the HTML document that carries *payload* in its one data block."""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        '<head><meta charset="utf-8"><title>Intent graph</title></head>\n'
        "<body>\n"
        '<script type="application/json" id="intent-data">'
        f"{data_block_json(payload)}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def publish(html: str, destination: str | None, name: str | None) -> Path:
    """Write *html* to a new file in *destination* and return its absolute path.

    Refuses rather than overwrite an existing entry.
    """
    directory = Path(os.path.realpath(destination or tempfile.gettempdir()))
    if not directory.is_dir():
        raise ViewRefusal("invalid_destination", "the destination is not a directory")
    file_name = name or _dt.datetime.now(tz=_UTC).strftime("intent-graph-%Y%m%dT%H%M%SZ.html")
    target = directory / file_name
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise ViewRefusal(
            "destination_exists", "an entry with that name already exists"
        ) from None
    except OSError:
        raise ViewRefusal("publish_failed", "the file could not be written") from None
    with os.fdopen(fd, "wb") as handle:
        handle.write(html.encode("utf-8"))
    return target
