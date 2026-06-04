#!/usr/bin/env python3
"""Figma REST API CLI (api.figma.com v1).

Subcommands:
    check                       Verify credentials and reachability.
    whoami                      Print the authenticated user record.

    # Files
    get-file FILE_KEY                  Fetch a file (full or scoped).
    get-nodes FILE_KEY --ids ID,ID     Fetch specific nodes.
    get-file-meta FILE_KEY             Lightweight file metadata.
    list-versions FILE_KEY             Version history.

    # Images
    export-images FILE_KEY --ids ...   Render nodes to images on disk.

    # Comments
    list-comments FILE_KEY
    post-comment FILE_KEY --message TEXT [--node-id ID] [--reply-to CID]

    # Diagrams
    figjam-to-mermaid FILE_KEY NODE_ID   FigJam connector graph → Mermaid.

    # Enterprise-only typically
    get-variables FILE_KEY [--published]
    list-dev-resources FILE_KEY

    # Escape hatch
    raw METHOD PATH

The Figma PAT is never accepted on the command line. It is resolved via
the build-projected ``credentials_shim`` sibling (Tier 1 env → Tier 2 OS keyring →
Tier 3 dotfile); run ``credential-setup`` skill to populate the
namespace.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Bootstrap when invoked as ``python scripts/figma.py`` so the
# relative imports of sibling modules — including ``_client``'s
# ``from .credentials_shim import …`` — resolve against the
# build-projected siblings in this directory. Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness is responsible for
# its own package context.
if __package__ in (None, "") and __spec__ is None:
    # Windows console hardening: this CLI writes UTF-8 payloads to stdout,
    # and sys.stdout defaults to errors="strict" — so on a legacy Windows
    # console (cp1252) a non-ASCII write raises UnicodeEncodeError. Force
    # UTF-8 on stdout here, before any write. stderr defaults to
    # backslashreplace (it mojibakes rather than crashing), but reconfigure
    # it too for clean bytes; doing both before the import guard means even
    # its messages emit correctly. Guarded: a replaced stream (StringIO under
    # a test harness) or pythonw's None has no reconfigure().
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    _here = Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name

try:
    from ._client import (  # noqa: E402
        AccessError,
        AuthError,
        FigmaClient,
        FigmaError,
        load_credentials,
    )
except ModuleNotFoundError as _import_exc:  # noqa: E402
    # 1 = functional/internal (shim not projected); 2 = user must act (deps).
    if _import_exc.name and "credentials_shim" in _import_exc.name:
        sys.stderr.write(
            "error: credentials_shim sibling not projected — run "
            "`make build-self` or reinstall the credential-brokers pack.\n"
        )
        raise SystemExit(1)
    sys.stderr.write(
        f"error: missing dependency {_import_exc.name!r} — run: "
        "python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(2)

log = logging.getLogger("figma.cli")

# Banded exit-code taxonomy (docs/specs/credentialed-cli-exit-code-contract):
#   0     success
#   1     functional / operational error — bad args, server 5xx, transport,
#         keychain hard-fail, unexpected; the stderr message carries the cause
#   2     user must act — credential missing/invalid/expired, 401/403 (incl.
#         scope/plan access), or a missing dependency; `check` returns this
#   3-9   reserved for the credential/auth band (never reuse for functional)
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_ACTION = 2

# Normalised forms (lowercased, underscores → hyphens) of the banned
# argv shapes. The check is case-insensitive so ``--Token`` /
# ``--API_TOKEN`` are rejected before argparse echoes their value to
# stderr in an "unrecognized arguments" error.
TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--api-key", "--bearer", "-t",
    "--figma-token", "--pat", "--password",
    "--access-token", "--auth-token", "--auth", "--secret",
})

# Substring patterns on the flag NAME (not its value) that catch
# token-shaped flags the explicit deny-list doesn't enumerate
# (``--apikey``, ``--credential``, ``--personal-access-token``, etc.).
# Case-insensitive. False-positives across the current flag set were
# checked at authoring time — none of the legitimate flags
# (--verbose / --format / --output / --ids / --depth / --geometry /
# --version / --plugin-data / --branch-data / --scale /
# --use-absolute-bounds / --svg-* / --page-size / --before / --after /
# --message / --node-id / --reply-to / --published / --param /
# --data-file) contain any of these substrings.
SECRET_LIKE_FLAG_RE = re.compile(
    r"(?i)(token|secret|password|bearer|api[_-]?key|pat|auth|credential)"
)

# Figma URL → FILE_KEY extractor. Anchored at the start of the string
# so `https://evil.com/figma.com/file/PWNED` does not match — only real
# figma.com URLs do.
FILE_KEY_URL_RE = re.compile(
    r"^https?://(?:www\.)?figma\.com/(?:file|design|board|proto)/([A-Za-z0-9]+)"
)

# Bare FILE_KEY shape — alphanumeric (no path separators, no whitespace,
# no query characters). Validated at `_extract_file_key` boundary so a
# malformed input cannot reshape downstream URL templates.
FILE_KEY_BARE_RE = re.compile(r"^[A-Za-z0-9]+$")

# Node-id canonical (`1:2`) and URL-encoded (`1-2`) shapes. Validated
# at the boundary so a node-id-shaped slot cannot smuggle other content
# (path traversal characters, newlines, query-param injection) into a
# Figma request.
NODE_ID_CANONICAL_RE = re.compile(r"^\d+:\d+$")


def _normalise_argv_head(s: str) -> str:
    return s.lower().replace("_", "-")


def _reject_token_on_cli(argv: list[str]) -> None:
    """Figma PATs are secret; refuse to accept them as CLI args."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        norm = _normalise_argv_head(head)
        if norm in TOKEN_CLI_FLAGS or (
            head.startswith("-") and SECRET_LIKE_FLAG_RE.search(head)
        ):
            sys.stderr.write(
                "error: API tokens must not be passed on the command line. "
                "Run `credential-setup` skill to store FIGMA_API_TOKEN "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


class _ScrubbingArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that scrubs token-shaped values from error messages.

    argparse's stock ``error()`` echoes the offending argv tokens
    verbatim — including the value half of any unrecognised
    ``--flag VALUE``. If a user typos a flag (`--apikey SECRET` instead
    of `--api-key`, which is itself rejected, or any other unknown
    spelling), the stock message would leak ``SECRET`` to stderr / the
    agent transcript. This subclass redacts any non-flag argv token of
    length ≥ 20 with a likely-credential character set before chaining
    to the stock error handler.
    """

    # `%` included to catch percent-encoded values (a deliberately
    # encoded secret would otherwise survive the scrub) even though
    # the realistic threat model is bare token values.
    _CREDENTIAL_LOOKING_RE = re.compile(r"^[A-Za-z0-9_/+=%-]{20,}$")
    # Quoting / punctuation argparse and the shell may wrap a value in
    # before it lands in an error message.
    _STRIP_CHARS = "'\"`(),;:."

    def error(self, message: str) -> None:  # type: ignore[override]
        def _check(value: str) -> bool:
            core = value.strip(self._STRIP_CHARS)
            return bool(self._CREDENTIAL_LOOKING_RE.match(core))

        def _scrub(match: re.Match[str]) -> str:
            tok = match.group(0)
            if tok.startswith("-"):
                # Glued ``--flag=VALUE`` form — argparse echoes the
                # entire token verbatim; check the RHS of the first ``=``
                # for credential shape and replace only that half.
                if "=" in tok:
                    flag, _, value = tok.partition("=")
                    if _check(value):
                        return f"{flag}=<scrubbed>"
                return tok
            # Bare positional value — strip surrounding quotes /
            # parentheses / punctuation so an argparse-wrapped value
            # like ``'SECRET_VALUE'`` is still caught.
            if _check(tok):
                return "<scrubbed>"
            return tok

        scrubbed = re.sub(r"\S+", _scrub, message)
        super().error(scrubbed)


def _extract_file_key(s: str) -> str:
    """Accept either a bare FILE_KEY or a full figma.com URL.

    Validates the bare-string branch so a value like
    ``KEY/../variables/local`` or ``KEY?published=true`` cannot
    reshape downstream ``/v1/files/{key}/...`` URL templates.
    """
    if s.startswith("http://") or s.startswith("https://"):
        m = FILE_KEY_URL_RE.match(s)
        if not m:
            # Do not echo `s` — a URL with credentials in the userinfo
            # (e.g. ``https://user:token@host/...``) would otherwise
            # leak the token to stderr.
            raise SystemExit(
                "could not extract FILE_KEY: input looks like a URL but "
                "does not match the figma.com/{file,design,board,proto}/<KEY> "
                "shape (value omitted from this message)."
            )
        return m.group(1)
    if not FILE_KEY_BARE_RE.match(s):
        # Same scrub discipline as the URL branch — don't echo the
        # offending value.
        raise SystemExit(
            "FILE_KEY must be alphanumeric (no slashes, query characters, "
            "or whitespace). Value omitted from this message."
        )
    return s


_URL_FORM_NODE_ID_RE = re.compile(r"^\d+-\d+$")


def _normalise_node_id(node_id: str) -> str:
    """Figma URLs encode node ids with `-` (e.g. `node-id=1-2`); the
    REST API always returns them with `:` (`1:2`). Normalise to the
    response shape for either input form. Surrounding whitespace is
    stripped — copy-paste from the UI commonly carries it. Rejects
    anything that doesn't match either form so a node-id slot cannot
    smuggle other content."""
    node_id = node_id.strip()
    if _URL_FORM_NODE_ID_RE.match(node_id):
        return node_id.replace("-", ":")
    if NODE_ID_CANONICAL_RE.match(node_id):
        return node_id
    raise SystemExit(
        "node id must be in the form `1:23` (API native) or `1-23` "
        "(Figma URL native). Value omitted from this message."
    )


def _normalise_node_ids_csv(ids_csv: str) -> str:
    """Apply :func:`_normalise_node_id` to each comma-separated entry.

    Rejects an empty / all-whitespace CSV — the dispatcher relies on
    "ids present" as a meaningful signal and should not silently degrade
    to "no scope" when the user typed something.
    """
    entries = [part for part in (p.strip() for p in ids_csv.split(",")) if part]
    if not entries:
        raise SystemExit(
            "--ids must contain at least one node id (got empty list)."
        )
    return ",".join(_normalise_node_id(entry) for entry in entries)


def _build_parser() -> argparse.ArgumentParser:
    p = _ScrubbingArgumentParser(
        prog="figma.py",
        description="Query the Figma REST API.",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging on the figma.* loggers only. "
             "httpx / httpcore stay at WARNING regardless to avoid "
             "header-byte leakage.",
    )
    p.add_argument(
        "--format",
        choices=("json", "jsonl"),
        default="json",
        help="Output format for list-shaped responses (default: json). "
             "Ignored by `export-images` (writes image bytes) and "
             "`figjam-to-mermaid` (writes a fenced Mermaid block).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this file (or directory, for export-images).",
    )

    # parser_class pinned explicitly so the scrubber's error() override
    # applies at the subparser level too. Default behaviour is
    # parser_class=type(self), but pinning makes the contract explicit
    # rather than implicit on CPython's argparse internals.
    sub = p.add_subparsers(
        dest="command",
        required=True,
        parser_class=_ScrubbingArgumentParser,
    )

    sub.add_parser("check", help="Verify credentials and reachability.")
    sub.add_parser("whoami", help="Show the authenticated user record.")

    # --- files ---
    gf = sub.add_parser("get-file", help="Fetch a file (full or scoped).")
    gf.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    gf.add_argument("--ids", default=None,
                    help="Comma-separated node ids to scope the response.")
    gf.add_argument("--depth", type=int, default=None,
                    help="Limit tree traversal depth (1 = pages only).")
    gf.add_argument("--geometry", choices=("paths",), default=None,
                    help="Include geometry (`paths`) on returned nodes.")
    gf.add_argument("--version", default=None,
                    help="Specific version id (from list-versions).")
    gf.add_argument("--plugin-data", default=None,
                    help="Plugin id(s) to fetch shared plugin data.")
    gf.add_argument("--branch-data", action="store_true",
                    help="Include branch metadata for files on a branch.")

    gn = sub.add_parser("get-nodes", help="Fetch specific nodes by id.")
    gn.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    gn.add_argument("--ids", required=True,
                    help="Comma-separated node ids (e.g. 1:2,1:3).")
    gn.add_argument("--depth", type=int, default=None)
    gn.add_argument("--geometry", choices=("paths",), default=None)
    gn.add_argument("--version", default=None)

    gm = sub.add_parser("get-file-meta", help="Lightweight file metadata.")
    gm.add_argument("file_key", help="FILE_KEY or figma.com URL.")

    lv = sub.add_parser("list-versions", help="File version history.")
    lv.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    lv.add_argument("--page-size", type=int, default=None,
                    help="Versions per page (Figma default 30, max 50).")
    lv.add_argument("--before", type=int, default=None,
                    help="Pagination cursor: versions before this id.")
    lv.add_argument("--after", type=int, default=None,
                    help="Pagination cursor: versions after this id.")

    # --- images ---
    ei = sub.add_parser("export-images", help="Render nodes to images.")
    ei.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    ei.add_argument("--ids", required=True,
                    help="Comma-separated node ids to render.")
    ei.add_argument("--format", dest="img_format",
                    choices=("png", "jpg", "svg", "pdf"), default="png",
                    help="Output image format (default: png).")
    ei.add_argument("--scale", type=float, default=1.0,
                    help="Render scale, (0, 4] (default: 1.0).")
    ei.add_argument("--use-absolute-bounds", action="store_true",
                    help="Render using node's absolute bounding box.")
    ei.add_argument("--version", default=None,
                    help="Render from a specific file version.")
    ei.add_argument("--svg-include-id", action="store_true",
                    help="(svg) include node ids in element id attrs.")
    ei.add_argument("--no-svg-outline-text", dest="svg_outline_text",
                    action="store_false", default=True,
                    help="(svg) keep text as <text> instead of outlining.")
    ei.add_argument("--no-svg-simplify-stroke", dest="svg_simplify_stroke",
                    action="store_false", default=True,
                    help="(svg) don't simplify strokes to fills.")

    # --- comments ---
    lc = sub.add_parser("list-comments", help="List file comments.")
    lc.add_argument("file_key", help="FILE_KEY or figma.com URL.")

    pc = sub.add_parser("post-comment", help="Post a comment to a file.")
    pc.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    pc.add_argument("--message", required=True, help="Comment text.")
    pc.add_argument("--node-id", default=None,
                    help="Pin the comment to a specific node.")
    pc.add_argument("--reply-to", dest="comment_id", default=None,
                    help="Comment id to reply to (creates a thread reply).")

    # --- diagrams ---
    fm = sub.add_parser(
        "figjam-to-mermaid",
        help="Convert a FigJam connector graph to a Mermaid flowchart.",
    )
    fm.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    fm.add_argument("node_id", help="Frame / section / page node id.")

    # --- enterprise ---
    gv = sub.add_parser(
        "get-variables",
        help="Fetch local (or published) variables. Typically Enterprise.",
    )
    gv.add_argument("file_key", help="FILE_KEY or figma.com URL.")
    gv.add_argument("--published", action="store_true",
                    help="Fetch published (not local) variables.")

    ld = sub.add_parser(
        "list-dev-resources",
        help="Fetch dev resources on file nodes. Typically Dev Mode.",
    )
    ld.add_argument("file_key", help="FILE_KEY or figma.com URL.")

    # --- raw ---
    rw = sub.add_parser("raw", help="Arbitrary request.")
    rw.add_argument("method", choices=("GET", "POST", "PUT", "PATCH", "DELETE"))
    rw.add_argument("path", help="API path (e.g. files/KEY or /v1/files/KEY).")
    rw.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                    help="Query parameter (repeatable).")
    rw.add_argument("--data-file", type=Path, default=None,
                    help="JSON file to send as the request body.")

    return p


def _write_output(args: argparse.Namespace, data: Any) -> None:
    """Render ``data`` to stdout or --output per --format."""
    if args.format == "jsonl" and isinstance(data, list):
        rendered = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
    else:
        rendered = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        sys.stdout.write(rendered + "\n")


# --- figjam-to-mermaid helpers ----------------------------------------------

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_]+")

# FigJam shape → Mermaid node shape syntax. The label is interpolated at the
# `{}` placeholder. Falls back to `["{}"]` (rectangle) for anything not
# enumerated here.
#
# PARALLELOGRAM_RIGHT / _LEFT use *matched* slashes (Mermaid parallelogram);
# *mismatched* slashes ([/...\] and [\.../]) are Mermaid's trapezoid shapes
# and would render the wrong primitive.
#
# Mermaid has no triangle shape; both TRIANGLE_UP and TRIANGLE_DOWN collapse
# to the asymmetric/flag shape (`>"…"]`) as a best-fit. Documented in SKILL.md
# "What it preserves".
FIGJAM_SHAPE_TO_MERMAID = {
    "SQUARE": '["{}"]',
    "ROUNDED_RECTANGLE": '("{}")',
    "ELLIPSE": '(("{}"))',
    "DIAMOND": '{{"{}"}}',
    "TRIANGLE_UP": '>"{}"]',
    "TRIANGLE_DOWN": '>"{}"]',
    "PARALLELOGRAM_RIGHT": '[/"{}"/]',
    "PARALLELOGRAM_LEFT": '[\\"{}"\\]',
    "ENG_DATABASE": '[("{}")]',
    "CLOUD": '(["{}"])',
    "PREDEFINED_PROCESS": '[["{}"]]',
}

# Mermaid edge syntax keyed by (start_has_arrow, end_has_arrow).
_EDGE_BY_CAPS = {
    (False, False): "---",
    (False, True): "-->",
    (True, False): "<--",
    (True, True): "<-->",
}

# Generic auto-generated names FigJam / Figma assigns when the author
# never renames the shape. Always ``<Type>`` followed by ``<space>``
# and a number — bare ``Frame`` / ``Group`` / etc. without a trailing
# number is treated as a deliberate (even if odd) name and survives
# the heuristic. Matched case-insensitively because Figma's auto-name
# casing has varied across versions.
_GENERIC_AUTO_NAME_RE = re.compile(
    r"^(frame|group|rectangle|ellipse|shape|sticky)\s+\d+$",
    re.IGNORECASE,
)


def _safe_node_id(node_id: str) -> str:
    return "n" + _SAFE_ID_RE.sub("_", node_id)


def _is_arrow_cap(cap: str | None) -> bool:
    """Figma stroke caps that visually read as arrows."""
    if not cap:
        return False
    return cap.upper().startswith(("ARROW", "TRIANGLE"))


def _best_label(node: dict) -> str:
    """Pick a human label. Prefer non-generic ``name``; otherwise descend
    for the first TEXT/SHAPE_WITH_TEXT/STICKY ``characters``; fall back to
    the node type."""
    name = (node.get("name") or "").strip()
    if name and not _GENERIC_AUTO_NAME_RE.match(name):
        return name
    # Direct text children first (BFS-ish on this level).
    children = node.get("children") or []
    for child in children:
        if child.get("type") in ("TEXT", "SHAPE_WITH_TEXT", "STICKY"):
            chars = (child.get("characters") or "").strip()
            if chars:
                return chars
    # Then descend.
    for child in children:
        deeper = _best_label(child)
        if deeper and deeper != child.get("type") and deeper != (child.get("name") or "").strip():
            return deeper
    return name or node.get("type", "node")


def _mermaid_emit(
    node: dict,
    parent_subgraph_id: str | None,
    lines: list[str],
    edges: list[str],
    indent: int,
) -> None:
    """Walk the node tree, emitting Mermaid lines.

    Containment is encoded via Mermaid `subgraph` blocks alone — we do
    NOT emit `parent --- child` edges, which the skilldrop original did
    and which produces unreadable noise in real files. Arrows come only
    from explicit CONNECTOR nodes; their directionality is read from
    ``connectorStartStrokeCap`` / ``connectorEndStrokeCap``.
    """
    type_ = node.get("type")
    pad = "    " * indent

    if type_ in ("DOCUMENT", "CANVAS"):
        for child in node.get("children", []) or []:
            _mermaid_emit(child, parent_subgraph_id, lines, edges, indent)
        return

    if type_ in ("FRAME", "GROUP", "SECTION"):
        my_id = _safe_node_id(node["id"])
        label = _best_label(node).replace('"', "'")[:60]
        lines.append(f'{pad}subgraph {my_id}["{label}"]')
        for child in node.get("children", []) or []:
            _mermaid_emit(child, my_id, lines, edges, indent + 1)
        lines.append(f"{pad}end")
        return

    if type_ == "CONNECTOR":
        start = node.get("connectorStart") or {}
        end = node.get("connectorEnd") or {}
        a = start.get("endpointNodeId")
        b = end.get("endpointNodeId")
        if a and b:
            start_arrow = _is_arrow_cap(node.get("connectorStartStrokeCap"))
            end_arrow = _is_arrow_cap(node.get("connectorEndStrokeCap"))
            edge_op = _EDGE_BY_CAPS[(start_arrow, end_arrow)]
            text = (node.get("text") or {}).get("characters") or ""
            text = text.strip().replace('"', "'")[:40]
            if text:
                edges.append(f"    {_safe_node_id(a)} {edge_op}|{text}| {_safe_node_id(b)}")
            else:
                edges.append(f"    {_safe_node_id(a)} {edge_op} {_safe_node_id(b)}")
        return

    if type_ == "SHAPE_WITH_TEXT":
        my_id = _safe_node_id(node["id"])
        label = _best_label(node).replace('"', "'")[:60]
        shape = node.get("shapeType") or "SQUARE"
        template = FIGJAM_SHAPE_TO_MERMAID.get(shape, '["{}"]')
        lines.append(f"{pad}{my_id}{template.format(label)}")
        return

    if type_ == "STICKY":
        my_id = _safe_node_id(node["id"])
        label = _best_label(node).replace('"', "'")[:60]
        lines.append(f'{pad}{my_id}["{label}"]')
        return

    if type_ in ("RECTANGLE", "INSTANCE", "COMPONENT", "TEXT"):
        my_id = _safe_node_id(node["id"])
        label = _best_label(node).replace('"', "'")[:60]
        lines.append(f'{pad}{my_id}["{label}"]')
        return

    if type_ == "ELLIPSE":
        my_id = _safe_node_id(node["id"])
        label = _best_label(node).replace('"', "'")[:60]
        lines.append(f'{pad}{my_id}(("{label}"))')
        return

    # Unhandled type — descend in case there are connectors below.
    for child in node.get("children", []) or []:
        _mermaid_emit(child, parent_subgraph_id, lines, edges, indent)


# --- command dispatch -------------------------------------------------------


async def _dispatch(args: argparse.Namespace) -> int:
    try:
        creds = load_credentials()
    except AuthError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write(
            "run `credential-setup` skill to set FIGMA_API_TOKEN\n"
        )
        return EXIT_USER_ACTION

    async with FigmaClient(creds) as client:
        cmd = args.command

        if cmd == "check":
            try:
                me = await client.whoami()
            except AuthError as exc:
                sys.stderr.write(f"{exc}\n")
                return EXIT_USER_ACTION
            handle = me.get("handle") or me.get("email") or "?"
            sys.stdout.write(f"figma: authenticated as {handle}\n")
            return EXIT_OK

        if cmd == "whoami":
            data = await client.whoami()
            _write_output(args, data)
            return EXIT_OK

        if cmd == "get-file":
            # `args.ids is not None` distinguishes "not supplied" (None,
            # fetch whole file) from "supplied empty" (`""`, user
            # error). The normaliser raises a clean error on the
            # empty-supplied case.
            data = await client.get_file(
                _extract_file_key(args.file_key),
                ids=_normalise_node_ids_csv(args.ids) if args.ids is not None else None,
                depth=args.depth,
                geometry=args.geometry,
                version=args.version,
                plugin_data=args.plugin_data,
                branch_data=args.branch_data,
            )
            _write_output(args, data)
            return EXIT_OK

        if cmd == "get-nodes":
            data = await client.get_file_nodes(
                _extract_file_key(args.file_key),
                ids=_normalise_node_ids_csv(args.ids),
                depth=args.depth,
                geometry=args.geometry,
                version=args.version,
            )
            _write_output(args, data)
            return EXIT_OK

        if cmd == "get-file-meta":
            data = await client.get_file_meta(_extract_file_key(args.file_key))
            _write_output(args, data)
            return EXIT_OK

        if cmd == "list-versions":
            data = await client.list_versions(
                _extract_file_key(args.file_key),
                page_size=args.page_size,
                before=args.before,
                after=args.after,
            )
            _write_output(args, data)
            return EXIT_OK

        if cmd == "export-images":
            return await _cmd_export_images(args, client)

        if cmd == "list-comments":
            data = await client.list_comments(_extract_file_key(args.file_key))
            _write_output(args, data)
            return EXIT_OK

        if cmd == "post-comment":
            client_meta = None
            if args.node_id:
                node_id = _normalise_node_id(args.node_id)
                client_meta = {"node_id": node_id, "node_offset": {"x": 0, "y": 0}}
            data = await client.post_comment(
                _extract_file_key(args.file_key),
                message=args.message,
                client_meta=client_meta,
                comment_id=args.comment_id,
            )
            _write_output(args, data)
            return EXIT_OK

        if cmd == "figjam-to-mermaid":
            return await _cmd_figjam_to_mermaid(args, client)

        if cmd == "get-variables":
            try:
                if args.published:
                    data = await client.get_variables_published(
                        _extract_file_key(args.file_key)
                    )
                else:
                    data = await client.get_variables_local(
                        _extract_file_key(args.file_key)
                    )
            except AccessError as exc:
                sys.stderr.write(f"{exc}\n")
                sys.stderr.write(
                    "Figma Variables typically require Enterprise org membership. "
                    "If your account is Enterprise and you still see this, the PAT "
                    "may need to be regenerated with the right scope.\n"
                )
                return EXIT_USER_ACTION
            _write_output(args, data)
            return EXIT_OK

        if cmd == "list-dev-resources":
            try:
                data = await client.list_dev_resources(
                    _extract_file_key(args.file_key)
                )
            except AccessError as exc:
                sys.stderr.write(f"{exc}\n")
                sys.stderr.write(
                    "Figma Dev Resources require Dev Mode access. "
                    "If you have Dev Mode and still see this, regenerate the PAT "
                    "with the file_dev_resources:read scope.\n"
                )
                return EXIT_USER_ACTION
            _write_output(args, data)
            return EXIT_OK

        if cmd == "raw":
            params: dict[str, Any] = {}
            for kv in args.param:
                if "=" not in kv:
                    # Do NOT echo the bare ``kv`` value — a user who
                    # mistakenly passed a secret-bearing value would
                    # otherwise see it surface in stderr / the agent
                    # transcript.
                    sys.stderr.write(
                        "--param must be KEY=VALUE (value omitted from "
                        "this message)\n"
                    )
                    return EXIT_ERROR
                k, v = kv.split("=", 1)
                params[k] = v
            body = None
            if args.data_file:
                # Defence in depth: forbid pointing --data-file at the
                # secrets dotfile. json.loads would raise on its
                # KEY=VALUE shape so this is not directly exploitable,
                # but the architecture rule that skills do not read the
                # credential store applies transitively to --data-file
                # input. Path components compared separately so the
                # forbidden-substring lint does not trip on
                # this guard line.
                resolved = args.data_file.expanduser().resolve()
                parts = set(resolved.parts)
                if resolved.name == "credentials.env" and ".agentbundle" in parts:
                    sys.stderr.write(
                        "error: --data-file may not point at the "
                        "credential store\n"
                    )
                    return EXIT_ERROR
                body = json.loads(args.data_file.read_text(encoding="utf-8"))
            data = await client.raw(
                args.method, args.path, params=params or None, json_body=body,
            )
            _write_output(args, data)
            return EXIT_OK

    sys.stderr.write(f"unknown command: {args.command}\n")
    return EXIT_ERROR


async def _cmd_export_images(
    args: argparse.Namespace, client: FigmaClient,
) -> int:
    file_key = _extract_file_key(args.file_key)
    rendered = await client.render_images(
        file_key,
        ids=_normalise_node_ids_csv(args.ids),
        format=args.img_format,
        scale=args.scale,
        svg_outline_text=args.svg_outline_text,
        svg_include_id=args.svg_include_id,
        svg_simplify_stroke=args.svg_simplify_stroke,
        use_absolute_bounds=args.use_absolute_bounds,
        version=args.version,
    )
    images: dict[str, str] = rendered.get("images") or {}
    if not images:
        sys.stderr.write("Figma returned no image URLs for the requested ids.\n")
        return EXIT_ERROR

    output_dir = args.output or Path(f"figma-export-{file_key}")
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = args.img_format

    written: dict[str, str] = {}
    for node_id, url in images.items():
        if not url:
            sys.stderr.write(f"warning: empty render URL for node {node_id}\n")
            continue
        safe_name = _SAFE_ID_RE.sub("_", node_id)
        target = output_dir / f"{safe_name}.{ext}"
        target.write_bytes(await client.download(url))
        written[node_id] = str(target)

    sys.stdout.write(json.dumps({"file_key": file_key, "written": written}, indent=2))
    sys.stdout.write("\n")
    return EXIT_OK


async def _cmd_figjam_to_mermaid(
    args: argparse.Namespace, client: FigmaClient,
) -> int:
    file_key = _extract_file_key(args.file_key)
    # Figma URLs encode node ids with `-` (`node-id=1-2`); the REST API
    # returns them with `:` (`1:2`). Normalise so both input forms work.
    node_id = _normalise_node_id(args.node_id)
    data = await client.get_file_nodes(file_key, ids=node_id)
    node = (
        data.get("nodes", {})
        .get(node_id, {})
        .get("document")
    )
    if not node:
        sys.stderr.write(
            f"error: node {node_id} not found in {file_key}\n"
        )
        return EXIT_ERROR

    lines: list[str] = ["flowchart TB"]
    edges: list[str] = []
    _mermaid_emit(node, None, lines, edges, indent=0)
    lines.extend(edges)

    rendered = "```mermaid\n" + "\n".join(lines) + "\n```\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    _reject_token_on_cli(argv)
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Logging discipline: --verbose ONLY raises the ``figma.*`` namespace
    # to DEBUG. httpx / httpcore stay at WARNING regardless — their DEBUG
    # output can include the literal HTTP/1.1 request bytes in some
    # versions, which would expose the X-Figma-Token header in transcripts.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.verbose:
        logging.getLogger("figma").setLevel(logging.DEBUG)
    for noisy in ("httpx", "httpcore", "hpack", "h11", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Top-level catch-all: no exception escapes as a traceback. `except
    # Exception` deliberately does NOT catch SystemExit (input-validation
    # raises) or KeyboardInterrupt (BaseException) — those pass through.
    try:
        return asyncio.run(_dispatch(args))
    except AuthError as exc:
        sys.stderr.write(f"{exc}\n")
        return EXIT_USER_ACTION
    except AccessError as exc:
        # Scope/plan access (403, or a 404 the token can't see). Per the
        # banded taxonomy this is user-must-act (2), not a functional
        # error (1). Without this clause it falls through to
        # `except FigmaError` below and mis-reports as exit 1 for every
        # command except get-variables / list-dev-resources (which catch
        # AccessError inline with endpoint-specific hints and return first).
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write(
            "the token lacks scope for this endpoint, or the resource "
            "requires Enterprise / Dev Mode. Regenerate the PAT with the "
            "required scope, or run `credential-setup`.\n"
        )
        return EXIT_USER_ACTION
    except FigmaError as exc:
        sys.stderr.write(f"figma error: {exc}\n")
        return EXIT_ERROR
    except Exception as exc:  # noqa: BLE001 — intentional functional catch-all
        name = type(exc).__name__
        if name == "Tier2HardFailError":
            sys.stderr.write(
                f"error: OS keyring unavailable ({name}); set FIGMA_API_TOKEN "
                "via env or the dotfile, or run `credential-setup`.\n"
            )
        else:
            sys.stderr.write(f"error: unexpected {name}; report this if it persists.\n")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
