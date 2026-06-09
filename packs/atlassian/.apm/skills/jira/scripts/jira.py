#!/usr/bin/env python3
"""Jira REST API CLI (Atlassian Cloud v3 + Server / Data Center v2).

Subcommands:
    check               Verify credentials and reachability.
    whoami              Print the authenticated user record.

    # Issues
    get-issue KEY                Fetch an issue.
    create-issue                 POST /issue with body from --field/--data-file.
    update-issue KEY             PUT /issue/{KEY} (partial; only listed fields).
    delete-issue KEY --yes       Delete an issue (irreversible).
    transition KEY               Apply a workflow transition by name or id.
    list-transitions KEY         Show available transitions for an issue.
    comment KEY --body TEXT      Add a comment.
    attach KEY --file PATH       Upload an attachment.

    # Search
    search "JQL"                 JQL search with auto-pagination.

    # Projects
    get-project KEY              Fetch a project.
    list-projects                Paginate /project/search.

    # Users
    get-user                     Cloud: --account-id; Server: --username/--key.
    list-users --query Q         Search users.

    # Escape hatch
    raw METHOD PATH              Arbitrary request when nothing above fits.

The Jira API token / PAT is never accepted on the command line. It is
resolved via the ``credbroker`` library (Tier 1 env → Tier 2 OS keyring →
Tier 3 dotfile); run ``credential-setup`` skill to populate the namespace.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Bootstrap when invoked as ``python scripts/jira.py`` so the
# relative imports of sibling modules (e.g. ``_client``) resolve
# against the siblings in this directory. Gated on
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
        AuthError,
        JiraClient,
        JiraError,
        load_credentials,
    )
except ModuleNotFoundError as _import_exc:  # noqa: E402
    # A missing module here is a non-secret dependency (e.g. httpx);
    # `credbroker` is imported lazily inside load_credentials(), so its
    # absence surfaces at runtime (exit 1 via the top-level handler), not
    # at this import guard.
    sys.stderr.write(
        f"error: missing dependency {_import_exc.name!r} — run: "
        "python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(2)

log = logging.getLogger("jira.cli")

# Banded exit-code taxonomy (docs/specs/credentialed-cli-exit-code-contract):
#   0     success
#   1     functional / operational error — bad args, server 5xx, transport,
#         keychain hard-fail, unexpected; the stderr message carries the cause
#   2     user must act — credential missing/invalid/expired, 401/403, or a
#         missing dependency; `check` returns this
#   3-9   reserved for the credential/auth band (never reuse for functional)
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_ACTION = 2

# Superset of the CONVENTIONS § "The argv ban" canonical six
# (--token, --api-token, --api-key, --bearer, --pat, --password) plus the
# short -t and a Jira-specific alias.
TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--api-key", "--bearer", "-t",
    "--jira-token", "--pat", "--password",
})


def _reject_token_on_cli(argv: list[str]) -> None:
    """Jira tokens / PATs are secret; refuse to accept them as CLI args."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API tokens must not be passed on the command line. "
                "Run `credential-setup` skill to store JIRA_API_TOKEN "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


class _ScrubbingArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that scrubs token-shaped values from error messages.

    argparse's stock ``error()`` echoes the offending argv tokens verbatim —
    including the value half of an unrecognised ``--flag VALUE``. A token
    passed under a flag the deny-list doesn't enumerate (``--credential
    SECRET``, ``--apikey SECRET``) would otherwise leak ``SECRET`` to stderr
    / the agent transcript. This subclass redacts any argv token of length
    >= 20 on a likely-credential character set before chaining to the stock
    error handler.
    """

    # Credential-shaped token: >= 20 chars on a base64 / base64url / JWT /
    # percent-encoded charset. `.` and `~` are included so dotted bearer /
    # JWT tokens (header.payload.signature) match — without `.` the anchored
    # regex fails on the separators and the value would leak. The >= 20 floor
    # is deliberate (modern PATs/tokens exceed it); a shorter value under an
    # out-of-set flag is not redacted.
    _CREDENTIAL_LOOKING_RE = re.compile(r"^[A-Za-z0-9_/+=%.~-]{20,}$")
    _STRIP_CHARS = "'\"`(),;:."

    def error(self, message: str) -> None:  # type: ignore[override]
        def _check(value: str) -> bool:
            core = value.strip(self._STRIP_CHARS)
            return bool(self._CREDENTIAL_LOOKING_RE.match(core))

        def _scrub(match: re.Match[str]) -> str:
            tok = match.group(0)
            if tok.startswith("-"):
                # Glued ``--flag=VALUE`` — check the RHS of the first ``=``
                # for credential shape and replace only that half.
                if "=" in tok:
                    flag, _, value = tok.partition("=")
                    if _check(value):
                        return f"{flag}=<scrubbed>"
                return tok
            if _check(tok):
                return "<scrubbed>"
            return tok

        scrubbed = re.sub(r"\S+", _scrub, message)
        super().error(scrubbed)


def _build_parser() -> argparse.ArgumentParser:
    p = _ScrubbingArgumentParser(
        prog="jira.py",
        description="Query the Jira REST API (Cloud v3 or Server/DC v2).",
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

    sub = p.add_subparsers(
        dest="command", required=True, parser_class=_ScrubbingArgumentParser,
    )

    sub.add_parser("check", help="Verify credentials and reachability.")
    sub.add_parser("whoami", help="Show the authenticated user record.")

    # --- issues ---
    gi = sub.add_parser("get-issue", help="Fetch a single issue.")
    gi.add_argument("issue_key", help="Issue key (e.g. PROJ-123) or numeric id.")
    gi.add_argument("--fields", default=None,
                    help="Comma-separated field list (e.g. summary,status). "
                         "Use *all for everything, -comment to exclude.")
    gi.add_argument("--expand", default=None,
                    help="Comma-separated expand list "
                         "(renderedFields, names, schema, transitions, ...).")

    ci = sub.add_parser("create-issue", help="Create a new issue.")
    _add_body_flags(ci)

    ui = sub.add_parser("update-issue", help="Partially update an issue (PUT).")
    ui.add_argument("issue_key")
    ui.add_argument("--no-notify", action="store_true",
                    help="Suppress the watcher notification email.")
    _add_body_flags(ui)

    di = sub.add_parser("delete-issue", help="Delete an issue (irreversible).")
    di.add_argument("issue_key")
    di.add_argument("--delete-subtasks", action="store_true",
                    help="Also delete subtasks (otherwise the call 400s).")
    di.add_argument("--yes", action="store_true",
                    help="Required confirmation flag.")

    tr = sub.add_parser("transition", help="Apply a workflow transition.")
    tr.add_argument("issue_key")
    g = tr.add_mutually_exclusive_group(required=True)
    g.add_argument("--to", dest="transition_name",
                   help="Transition name (e.g. 'Done'). Resolved to id.")
    g.add_argument("--id", dest="transition_id",
                   help="Transition id from list-transitions.")
    tr.add_argument("--field", action="append", default=[], metavar="KEY=VALUE",
                    help="Field to set during the transition (repeatable). "
                         "JSON-parsed if possible, else string.")

    lt = sub.add_parser("list-transitions",
                        help="Show available transitions for an issue.")
    lt.add_argument("issue_key")

    cm = sub.add_parser("comment", help="Add a comment to an issue.")
    cm.add_argument("issue_key")
    cm.add_argument("--body", required=True, help="Comment text. Plain string; "
                    "wrapped to ADF on Cloud automatically.")

    at = sub.add_parser("attach", help="Upload an attachment.")
    at.add_argument("issue_key")
    at.add_argument("--file", dest="file_path", required=True, type=Path,
                    help="Local file path to upload.")

    # --- search ---
    sr = sub.add_parser("search", help="JQL search with auto-pagination.")
    sr.add_argument("jql", help="JQL expression, quoted.")
    sr.add_argument("--fields", default=None,
                    help="Comma-separated field list.")
    sr.add_argument("--expand", default=None,
                    help="Comma-separated expand list.")
    sr.add_argument("--limit", type=int, default=None,
                    help="Total max issues across all pages (default: all).")
    sr.add_argument("--page-size", type=int, default=50,
                    help="Issues per request (max 100).")

    # --- projects ---
    gp = sub.add_parser("get-project", help="Fetch a project.")
    gp.add_argument("key_or_id", help="Project key (PROJ) or numeric id.")

    lp = sub.add_parser("list-projects", help="Paginate /project/search.")
    lp.add_argument("--query", default=None,
                    help="Optional substring filter on project name/key.")
    lp.add_argument("--limit", type=int, default=None)
    lp.add_argument("--page-size", type=int, default=50)

    # --- users ---
    gu = sub.add_parser("get-user", help="Fetch a user record.")
    gu.add_argument("--account-id", default=None,
                    help="Cloud lookup: 24-char accountId.")
    gu.add_argument("--username", default=None,
                    help="Server/DC lookup: username.")
    gu.add_argument("--key", default=None,
                    help="Server/DC lookup: user key (legacy).")

    lu = sub.add_parser("list-users", help="Search users.")
    lu.add_argument("--query", required=True,
                    help="Cloud: name/email substring. Server: username substring.")
    lu.add_argument("--limit", type=int, default=None)
    lu.add_argument("--page-size", type=int, default=50)

    # --- raw ---
    rw = sub.add_parser("raw", help="Issue an arbitrary request.")
    rw.add_argument(
        "method",
        choices=("GET", "POST", "PUT", "PATCH", "DELETE"),
        help="HTTP method.",
    )
    rw.add_argument(
        "path",
        help=(
            "Path. Absolute (/rest/api/3/...) or relative to the API "
            "prefix (e.g. 'issue/PROJ-1/worklog')."
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
    """Body-source flags for create-issue / update-issue."""
    sub.add_argument(
        "--data-file",
        type=Path,
        default=None,
        help=(
            "Path to a JSON file containing the request body. The body may "
            "be a flat fields dict or already wrapped as {\"fields\": {...}}."
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
            "otherwise sent as a string. Merges over --data-file. "
            "Examples: --field summary=\"...\" --field "
            "project='{\"key\":\"PROJ\"}' --field labels='[\"a\",\"b\"]'."
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
    overrides = _parse_field_pairs(args.field)
    if overrides:
        # If the loaded body is already wrapped ({"fields": {...}} — as Jira's
        # own create / update payloads are), merge --field overrides INTO
        # body["fields"]. Merging at the top level would leave both
        # body["fields"]["summary"] and body["summary"] populated, which
        # the API would either silently drop or 400 on.
        if any(k in body for k in ("fields", "update", "transition")):
            existing_fields = dict(body.get("fields") or {})
            existing_fields.update(overrides)
            body["fields"] = existing_fields
        else:
            body.update(overrides)
    if not body:
        raise ValueError("no body provided — pass --data-file or --field")
    return body


# --- command implementations ----------------------------------------------


async def _cmd_check(client: JiraClient) -> int:
    try:
        info = await client.whoami()
    except AuthError as exc:
        print(f"auth failed: {exc}", file=sys.stderr)
        return EXIT_USER_ACTION
    except JiraError as exc:
        print(f"server error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    name = (
        info.get("displayName")
        or info.get("name")
        or info.get("emailAddress")
        or "?"
    )
    print(
        f"ok: connected to {client.base_url} ({client.flavor}) as {name}"
    )
    return EXIT_OK


async def _cmd_whoami(client: JiraClient, writer: "OutputWriter") -> int:
    info = await client.whoami()
    writer.emit_single(info)
    return EXIT_OK


async def _cmd_get_issue(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    issue = await client.get_issue(
        args.issue_key, fields=args.fields, expand=args.expand
    )
    writer.emit_single(issue)
    return EXIT_OK


async def _cmd_create_issue(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    try:
        body = _load_body(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    result = await client.create_issue(body)
    writer.emit_single(result if isinstance(result, dict) else {"value": result})
    return EXIT_OK


async def _cmd_update_issue(
    client: JiraClient, args: argparse.Namespace
) -> int:
    try:
        body = _load_body(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    await client.update_issue(
        args.issue_key, body, notify_users=not args.no_notify
    )
    print(f"ok: updated {args.issue_key}", file=sys.stderr)
    return EXIT_OK


async def _cmd_delete_issue(
    client: JiraClient, args: argparse.Namespace
) -> int:
    if not args.yes:
        print(
            "error: delete is destructive — pass --yes to confirm.",
            file=sys.stderr,
        )
        return EXIT_ERROR
    await client.delete_issue(
        args.issue_key, delete_subtasks=args.delete_subtasks
    )
    print(f"ok: deleted {args.issue_key}", file=sys.stderr)
    return EXIT_OK


async def _cmd_list_transitions(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    transitions = await client.list_transitions(args.issue_key)
    for t in transitions:
        writer.emit_record(t)
    writer.finish()
    return EXIT_OK


async def _cmd_transition(
    client: JiraClient, args: argparse.Namespace
) -> int:
    try:
        fields = _parse_field_pairs(args.field) if args.field else None
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    await client.transition_issue(
        args.issue_key,
        transition_id=args.transition_id,
        transition_name=args.transition_name,
        fields=fields,
    )
    label = args.transition_name or args.transition_id
    print(f"ok: transitioned {args.issue_key} → {label}", file=sys.stderr)
    return EXIT_OK


async def _cmd_comment(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    result = await client.add_comment(args.issue_key, args.body)
    writer.emit_single(result if isinstance(result, dict) else {"value": result})
    return EXIT_OK


async def _cmd_attach(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    if not args.file_path.is_file():
        print(f"error: file not found: {args.file_path}", file=sys.stderr)
        return EXIT_ERROR
    results = await client.add_attachment(args.issue_key, args.file_path)
    for r in results:
        writer.emit_record(r)
    writer.finish()
    return EXIT_OK


async def _cmd_search(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    if args.page_size <= 0 or args.page_size > 100:
        print("error: --page-size must be 1..100", file=sys.stderr)
        return EXIT_ERROR
    async for issue in client.iter_search(
        args.jql,
        fields=args.fields,
        expand=args.expand,
        page_size=args.page_size,
        limit=args.limit,
    ):
        writer.emit_record(issue)
    writer.finish()
    return EXIT_OK


async def _cmd_get_project(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    proj = await client.get_project(args.key_or_id)
    writer.emit_single(proj)
    return EXIT_OK


async def _cmd_list_projects(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    async for proj in client.iter_projects(
        query=args.query, page_size=args.page_size, limit=args.limit
    ):
        writer.emit_record(proj)
    writer.finish()
    return EXIT_OK


async def _cmd_get_user(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    if not (args.account_id or args.username or args.key):
        print(
            "error: provide --account-id (cloud) or --username/--key (server).",
            file=sys.stderr,
        )
        return EXIT_ERROR
    user = await client.get_user(
        account_id=args.account_id, username=args.username, key=args.key
    )
    writer.emit_single(user)
    return EXIT_OK


async def _cmd_list_users(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    async for user in client.iter_users(
        args.query, page_size=args.page_size, limit=args.limit
    ):
        writer.emit_record(user)
    writer.finish()
    return EXIT_OK


async def _cmd_raw(
    client: JiraClient, args: argparse.Namespace, writer: "OutputWriter"
) -> int:
    params: dict[str, str] = {}
    for pair in args.param:
        if "=" not in pair:
            print(f"error: --param {pair!r} must be KEY=VALUE", file=sys.stderr)
            return EXIT_ERROR
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


# --- output writer ---------------------------------------------------------


class OutputWriter:
    """Streams records in json / jsonl / csv."""

    def __init__(self, fmt: str, output: Path | None) -> None:
        self._fmt = fmt
        self._path = output
        self._fh = (
            output.open("w", encoding="utf-8", newline="") if output else sys.stdout
        )
        self._close = output is not None
        self._buffer: list[dict] = []
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
            self._csv_fields = set(record.keys())
            self._csv_writer = csv.DictWriter(
                self._fh,
                fieldnames=list(record.keys()),
                extrasaction="ignore",
                quoting=csv.QUOTE_MINIMAL,
            )
            self._csv_writer.writeheader()
        else:
            # Warn (once per key) when a row has keys that aren't in the
            # CSV header. DictWriter with extrasaction="ignore" will
            # silently drop them, which is silent data loss the user
            # needs to know about. Cleanly switching to a wider header
            # mid-stream isn't possible in CSV; the user should rerun
            # with --format jsonl or pass --fields to pin the schema.
            extras = set(record.keys()) - self._csv_fields - self._csv_warned
            if extras:
                self._csv_warned |= extras
                print(
                    f"warning: CSV header was fixed from the first row; "
                    f"these keys appear in later rows and will be omitted: "
                    f"{', '.join(sorted(extras))}. Use --format jsonl for "
                    f"a complete export, or pass --fields to pin the "
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


# --- entrypoint ------------------------------------------------------------


async def _run(args: argparse.Namespace) -> int:
    try:
        credentials = load_credentials()
    except AuthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USER_ACTION

    writer = OutputWriter(args.format, args.output)
    try:
        async with JiraClient(
            credentials, verify_tls=not args.insecure
        ) as client:
            cmd = args.command
            if cmd == "check":
                return await _cmd_check(client)
            if cmd == "whoami":
                return await _cmd_whoami(client, writer)
            if cmd == "get-issue":
                return await _cmd_get_issue(client, args, writer)
            if cmd == "create-issue":
                return await _cmd_create_issue(client, args, writer)
            if cmd == "update-issue":
                return await _cmd_update_issue(client, args)
            if cmd == "delete-issue":
                return await _cmd_delete_issue(client, args)
            if cmd == "list-transitions":
                return await _cmd_list_transitions(client, args, writer)
            if cmd == "transition":
                return await _cmd_transition(client, args)
            if cmd == "comment":
                return await _cmd_comment(client, args, writer)
            if cmd == "attach":
                return await _cmd_attach(client, args, writer)
            if cmd == "search":
                return await _cmd_search(client, args, writer)
            if cmd == "get-project":
                return await _cmd_get_project(client, args, writer)
            if cmd == "list-projects":
                return await _cmd_list_projects(client, args, writer)
            if cmd == "get-user":
                return await _cmd_get_user(client, args, writer)
            if cmd == "list-users":
                return await _cmd_list_users(client, args, writer)
            if cmd == "raw":
                return await _cmd_raw(client, args, writer)
            print(f"error: unknown command {cmd!r}", file=sys.stderr)
            return EXIT_ERROR
    except AuthError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return EXIT_USER_ACTION
    except JiraError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
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
    # Top-level catch-all: no exception escapes as a traceback. `except
    # Exception` deliberately does NOT catch SystemExit / KeyboardInterrupt
    # (BaseException) — argparse usage exits and Ctrl-C (130) pass through.
    try:
        return asyncio.run(_run(args))
    except Exception as exc:  # noqa: BLE001 — intentional functional catch-all
        name = type(exc).__name__
        if name == "Tier2HardFailError":
            sys.stderr.write(
                f"error: OS keyring unavailable ({name}); set JIRA_API_TOKEN "
                "via env or the dotfile, or run `credential-setup`.\n"
            )
        else:
            # Never echo str(exc) on the unexpected path — it may carry a
            # token-shaped value. Print the type only.
            sys.stderr.write(f"error: unexpected {name}; report this if it persists.\n")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
