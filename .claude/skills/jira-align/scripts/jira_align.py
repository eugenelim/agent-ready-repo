#!/usr/bin/env python3
"""Jira Align REST API 2.0 CLI.

Subcommands:
    check               Verify credentials and base URL reachability.
    whoami              Print the authenticated user record.
    get RESOURCE ID     Fetch a single record (e.g. ``get epics 1001``).
    list RESOURCE       Paginate a collection with optional OData filters.
    search RESOURCE Q   Shorthand for ``list RESOURCE --filter Q``.
    create RESOURCE     POST a new record, body from --data-file or --field.
    update RESOURCE ID  PUT/PATCH an existing record.
    delete RESOURCE ID  DELETE a record (requires --yes).
    raw METHOD PATH     Arbitrary call for endpoints not wrapped above.

The Jira Align bearer token is never accepted on the command line. It
is resolved via the ``agentbundle.credentials`` loader (Tier 1 env →
Tier 2 OS keyring → Tier 3 dotfile); run ``agentbundle creds setup
jiraalign`` to populate the namespace.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Allow ``python scripts/jira_align.py`` to import the sibling _client module
# regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import (  # noqa: E402
    AuthError,
    JiraAlignClient,
    JiraAlignError,
    load_credentials,
)

log = logging.getLogger("jira_align.cli")

EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_AUTH_ERROR = 2
EXIT_SERVER_ERROR = 3

TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--bearer", "-t",
    "--jira-align-token", "--jiraalign-token",
})


def _reject_token_on_cli(argv: list[str]) -> None:
    """Jira Align tokens are secret; refuse to accept them as CLI args."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API tokens must not be passed on the command line. "
                "Run `agentbundle creds setup jiraalign` to store "
                "JIRAALIGN_API_TOKEN via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_USER_ERROR)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jira_align.py",
        description="Query Jira Align REST API 2.0 (cloud or on-prem).",
    )
    p.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    p.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification. Only if the user explicitly asks.",
    )
    p.add_argument(
        "--format",
        choices=("json", "jsonl", "csv"),
        default="json",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this file instead of stdout.",
    )

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verify credentials and reachability.")
    sub.add_parser("whoami", help="Show the authenticated user record.")

    g = sub.add_parser("get", help="Fetch a single record.")
    g.add_argument("resource", help="Resource name, e.g. epics, features, stories.")
    g.add_argument("item_id", help="Item ID.")
    g.add_argument("--expand", default=None, help="Comma-separated expand list.")

    lst = sub.add_parser("list", help="List records with optional OData filters.")
    _add_list_flags(lst)

    sr = sub.add_parser("search", help="List with a --filter shorthand.")
    sr.add_argument("resource")
    sr.add_argument("query", help="OData $filter expression.")
    _add_list_flags(sr, resource_positional=False, with_filter=False)

    cr = sub.add_parser("create", help="POST a new record.")
    cr.add_argument("resource")
    _add_body_flags(cr)

    up = sub.add_parser("update", help="PUT or PATCH an existing record.")
    up.add_argument("resource")
    up.add_argument("item_id")
    up.add_argument(
        "--method",
        choices=("PUT", "PATCH"),
        default="PUT",
        help="HTTP method (default: PUT).",
    )
    _add_body_flags(up)

    dl = sub.add_parser("delete", help="DELETE a record.")
    dl.add_argument("resource")
    dl.add_argument("item_id")
    dl.add_argument(
        "--yes",
        action="store_true",
        help="Required confirmation flag; deletes refuse to run without it.",
    )

    rw = sub.add_parser("raw", help="Issue an arbitrary request.")
    rw.add_argument(
        "method",
        choices=("GET", "POST", "PUT", "PATCH", "DELETE"),
        help="HTTP method.",
    )
    rw.add_argument(
        "path",
        help=(
            "Path. Absolute (/rest/align/api/2/...) or relative to the API "
            "prefix (e.g. 'epics/1001/milestones')."
        ),
    )
    rw.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Query parameter (repeatable).",
    )
    rw.add_argument(
        "--data-file",
        type=Path,
        default=None,
        help="Path to a JSON file to send as the request body.",
    )

    return p


def _add_body_flags(sub: argparse.ArgumentParser) -> None:
    """Body-source flags for create/update: --data-file or repeated --field."""
    sub.add_argument(
        "--data-file",
        type=Path,
        default=None,
        help=(
            "Path to a JSON file containing the request body. Either this "
            "or --field is required."
        ),
    )
    sub.add_argument(
        "--field",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Field to include in the body (repeatable). VALUE is parsed as "
            "JSON if possible (numbers, true/false, null, arrays, objects), "
            "otherwise sent as a string. Merges over --data-file."
        ),
    )


def _parse_field_pairs(pairs: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--field {pair!r} must be KEY=VALUE")
        k, v = pair.split("=", 1)
        if not k:
            raise ValueError(f"--field {pair!r} has an empty key")
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def _load_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if args.data_file is not None:
        raw = json.loads(args.data_file.read_text("utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("--data-file must contain a JSON object")
        body.update(raw)
    body.update(_parse_field_pairs(args.field))
    if not body:
        raise ValueError("no body provided — pass --data-file or --field")
    return body


def _add_list_flags(
    sub: argparse.ArgumentParser,
    *,
    resource_positional: bool = True,
    with_filter: bool = True,
) -> None:
    if resource_positional:
        sub.add_argument("resource")
    if with_filter:
        sub.add_argument("--filter", dest="filter_expr", default=None,
                         help="OData $filter expression.")
    sub.add_argument("--select", default=None, help="Comma-separated field list.")
    sub.add_argument("--orderby", default=None, help="OData $orderby expression.")
    sub.add_argument("--expand", default=None, help="Comma-separated expand list.")
    sub.add_argument("--limit", type=int, default=None,
                     help="Total max records (default: all).")
    sub.add_argument("--page-size", type=int, default=100,
                     help="Records per request (max 100).")


async def _cmd_check(client: JiraAlignClient) -> int:
    try:
        info = await client.whoami()
    except AuthError as exc:
        print(f"auth failed: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    except JiraAlignError as exc:
        print(f"server error: {exc}", file=sys.stderr)
        return EXIT_SERVER_ERROR
    user_id = info.get("id") or info.get("ID") or info.get("Id") or "?"
    email = info.get("email") or info.get("emailAddress") or ""
    print(
        f"ok: connected to {client.base_url} as user {user_id} {email}".rstrip()
    )
    return EXIT_OK


async def _cmd_whoami(client: JiraAlignClient, writer: "OutputWriter") -> int:
    info = await client.whoami()
    writer.emit_single(info)
    return EXIT_OK


async def _cmd_get(
    client: JiraAlignClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    item = await client.get_one(args.resource, args.item_id, expand=args.expand)
    writer.emit_single(item)
    return EXIT_OK


async def _cmd_list(
    client: JiraAlignClient,
    args: argparse.Namespace,
    writer: "OutputWriter",
    *,
    filter_expr: str | None,
) -> int:
    if args.page_size <= 0 or args.page_size > 100:
        print("error: --page-size must be 1..100", file=sys.stderr)
        return EXIT_USER_ERROR
    async for item in client.iter_list(
        args.resource,
        filter_expr=filter_expr,
        select=args.select,
        orderby=args.orderby,
        expand=args.expand,
        page_size=args.page_size,
        limit=args.limit,
    ):
        writer.emit_record(item)
    writer.finish()
    return EXIT_OK


async def _cmd_create(
    client: JiraAlignClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    try:
        body = _load_body(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USER_ERROR
    result = await client.create(args.resource, body)
    if result is None:
        print("(created, no content returned)", file=sys.stderr)
        return EXIT_OK
    if isinstance(result, dict):
        writer.emit_single(result)
    else:
        writer.emit_single({"value": result})
    return EXIT_OK


async def _cmd_update(
    client: JiraAlignClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    try:
        body = _load_body(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USER_ERROR
    result = await client.update(
        args.resource, args.item_id, body, method=args.method
    )
    if result is None:
        print("(updated, no content returned)", file=sys.stderr)
        return EXIT_OK
    if isinstance(result, dict):
        writer.emit_single(result)
    else:
        writer.emit_single({"value": result})
    return EXIT_OK


async def _cmd_delete(
    client: JiraAlignClient, args: argparse.Namespace
) -> int:
    if not args.yes:
        print(
            "error: delete is destructive — pass --yes to confirm.",
            file=sys.stderr,
        )
        return EXIT_USER_ERROR
    await client.delete(args.resource, args.item_id)
    print(
        f"ok: deleted {args.resource}/{args.item_id}",
        file=sys.stderr,
    )
    return EXIT_OK


async def _cmd_raw(
    client: JiraAlignClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    params: dict[str, str] = {}
    for pair in args.param:
        if "=" not in pair:
            print(f"error: --param {pair!r} must be KEY=VALUE", file=sys.stderr)
            return EXIT_USER_ERROR
        k, v = pair.split("=", 1)
        params[k] = v
    body: Any = None
    if args.data_file is not None:
        body = json.loads(args.data_file.read_text("utf-8"))
    result = await client.raw(
        args.method, args.path, params=params or None, json_body=body
    )
    if isinstance(result, list):
        for item in result:
            writer.emit_record(item if isinstance(item, dict) else {"value": item})
        writer.finish()
    elif isinstance(result, dict):
        writer.emit_single(result)
    elif result is None:
        print("(no content)", file=sys.stderr)
    else:
        writer.emit_single({"value": result})
    return EXIT_OK


class OutputWriter:
    """Streams records in json / jsonl / csv."""

    def __init__(self, fmt: str, output: Path | None) -> None:
        self._fmt = fmt
        self._path = output
        self._fh = (
            output.open("w", encoding="utf-8", newline="") if output else sys.stdout
        )
        self._close = output is not None
        self._buffer: list[dict] = []  # json mode buffers
        self._csv_writer: csv.DictWriter | None = None
        self._csv_fields: set[str] = set()
        self._csv_warned: set[str] = set()

    def emit_single(self, record: dict) -> None:
        if self._fmt == "json":
            json.dump(record, self._fh, indent=2, default=str)
            self._fh.write("\n")
        elif self._fmt == "jsonl":
            self._fh.write(json.dumps(record, default=str) + "\n")
        elif self._fmt == "csv":
            self._write_csv_row(record)

    def emit_record(self, record: dict) -> None:
        if self._fmt == "json":
            self._buffer.append(record)
        elif self._fmt == "jsonl":
            self._fh.write(json.dumps(record, default=str) + "\n")
        elif self._fmt == "csv":
            self._write_csv_row(record)

    def finish(self) -> None:
        if self._fmt == "json":
            json.dump(self._buffer, self._fh, indent=2, default=str)
            self._fh.write("\n")

    def _write_csv_row(self, record: dict) -> None:
        if self._csv_writer is None:
            # DictWriter needs the field list up front; derive from first row.
            self._csv_fields = set(record.keys())
            self._csv_writer = csv.DictWriter(
                self._fh,
                fieldnames=list(record.keys()),
                extrasaction="ignore",
                quoting=csv.QUOTE_MINIMAL,
            )
            self._csv_writer.writeheader()
        else:
            # Warn (once per key) when later rows contain keys not in the
            # header — extrasaction="ignore" silently drops them, which
            # is data loss the user needs to know about.
            extras = set(record.keys()) - self._csv_fields - self._csv_warned
            if extras:
                self._csv_warned |= extras
                print(
                    f"warning: CSV header was fixed from the first row; "
                    f"these keys appear in later rows and will be omitted: "
                    f"{', '.join(sorted(extras))}. Use --format jsonl for "
                    f"a complete export, or pass --select to pin the "
                    f"schema explicitly.",
                    file=sys.stderr,
                )
        self._csv_writer.writerow(
            {k: _csv_scalar(v) for k, v in record.items()}
        )

    def close(self) -> None:
        if self._close:
            self._fh.close()


def _csv_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, default=str)


async def _run(args: argparse.Namespace) -> int:
    try:
        credentials = load_credentials()
    except AuthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR

    writer = OutputWriter(args.format, args.output)
    try:
        async with JiraAlignClient(
            credentials, verify_tls=not args.insecure
        ) as client:
            if args.command == "check":
                return await _cmd_check(client)
            if args.command == "whoami":
                return await _cmd_whoami(client, writer)
            if args.command == "get":
                return await _cmd_get(client, args, writer)
            if args.command == "list":
                return await _cmd_list(
                    client, args, writer, filter_expr=args.filter_expr
                )
            if args.command == "search":
                return await _cmd_list(
                    client, args, writer, filter_expr=args.query
                )
            if args.command == "create":
                return await _cmd_create(client, args, writer)
            if args.command == "update":
                return await _cmd_update(client, args, writer)
            if args.command == "delete":
                return await _cmd_delete(client, args)
            if args.command == "raw":
                return await _cmd_raw(client, args, writer)
            print(f"error: unknown command {args.command!r}", file=sys.stderr)
            return EXIT_USER_ERROR
    except AuthError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return EXIT_AUTH_ERROR
    except JiraAlignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_SERVER_ERROR
    finally:
        writer.close()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    _reject_token_on_cli(argv)
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
