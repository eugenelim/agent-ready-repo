#!/usr/bin/env python3
"""Linear GraphQL API CLI (api.linear.app).

Subcommands:
    check                        Verify credentials and reachability.
    get-issue IDENTIFIER         Fetch one issue by human slug (e.g. ENG-123).
    get-project PROJECT_ID       Fetch a project's issues (up to 250).

The Linear API key is never accepted on the command line. It is resolved via
the ``credbroker`` library (Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile);
run ``credential-setup`` skill to populate the ``linear`` namespace.

Auth: ``Authorization: <KEY>`` (no "Bearer" prefix — Linear uses bare token).
Endpoint: https://api.linear.app/graphql
Rate limit: 5 000 req/hr for Personal API Keys; 429 + Retry-After respected.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, "") and __spec__ is None:
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    _here = Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    _floor = Path("~/.agentbundle/lib").expanduser()
    if _floor.is_dir() and str(_floor) not in sys.path:
        sys.path.append(str(_floor))
    __package__ = _here.name

try:
    import httpx
except ModuleNotFoundError as _import_exc:
    sys.stderr.write(
        f"error: missing dependency {_import_exc.name!r} — run: "
        "python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(2)

log = logging.getLogger("linear.cli")

# Banded exit-code taxonomy (docs/specs/credentialed-cli-exit-code-contract):
#   0     success
#   1     functional / operational error — bad args, server 5xx, transport, unexpected
#   2     user must act — credential missing/invalid/expired, 401/403
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_ACTION = 2

GRAPHQL_URL = "https://api.linear.app/graphql"
PAGE_SIZE = 50
MAX_PAGES = 5  # hard bound: ≤250 issues (PAGE_SIZE × MAX_PAGES)
DEFAULT_TIMEOUT_S = 30.0

TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--api-key", "--bearer", "-t",
    "--linear-token", "--pat", "--password",
    "--access-token", "--auth-token",
})

_CREDENTIAL_LOOKING_RE = re.compile(r"^[A-Za-z0-9_/+=%.~-]{20,}$")
_STRIP_CHARS = "'\"`(),;:."


def _reject_token_on_cli(argv: list[str]) -> None:
    """Linear API keys must not appear as command-line arguments."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API keys must not be passed on the command line. "
                "Run `credential-setup` skill to store LINEAR_API_KEY "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


class _ScrubbingArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that redacts credential-shaped values from error messages."""

    def error(self, message: str) -> None:
        def _scrub(match: re.Match[str]) -> str:
            tok = match.group(0)
            if tok.startswith("-"):
                if "=" in tok:
                    flag, _, value = tok.partition("=")
                    core = value.strip(_STRIP_CHARS)
                    if _CREDENTIAL_LOOKING_RE.match(core):
                        return f"{flag}=<scrubbed>"
                return tok
            core = tok.strip(_STRIP_CHARS)
            if _CREDENTIAL_LOOKING_RE.match(core):
                return "<scrubbed>"
            return tok

        scrubbed = re.sub(r"\S+", _scrub, message)
        super().error(scrubbed)


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Resolve the Linear API key via credbroker (lazy import).

    Never logs, echoes, or returns the key to the caller's output path.
    Exits with EXIT_USER_ACTION (2) when credentials are missing.
    """
    from credbroker import (
        CredentialsMissingError,
        load_credentials as _resolver_load,
    )

    try:
        creds = _resolver_load("linear", required_keys=["API_KEY"])
    except CredentialsMissingError as exc:
        sys.stderr.write(
            f"error: credentials missing — {exc}\n"
            "Run `credential-setup` skill to store LINEAR_API_KEY.\n"
        )
        raise SystemExit(EXIT_USER_ACTION) from exc

    return creds.API_KEY  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# GraphQL transport
# ---------------------------------------------------------------------------

def _graphql_request(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    url: str = GRAPHQL_URL,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """POST one GraphQL request.  Returns the parsed JSON body.

    Raises SystemExit(EXIT_USER_ACTION) on 401/403.
    Raises SystemExit(EXIT_ERROR) on network errors, server 5xx, or non-JSON.
    On HTTP 429 the caller is responsible for reading Retry-After and retrying.
    """
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "linear-skill/0.1",
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    except httpx.TransportError as exc:
        sys.stderr.write(f"error: network error — {exc}\n")
        raise SystemExit(EXIT_ERROR) from exc

    if resp.status_code in (401, 403):
        sys.stderr.write(
            f"error: HTTP {resp.status_code} — credentials invalid or "
            "insufficient permissions. Regenerate your Personal API Key at "
            "Linear → Settings → API and re-run `credential-setup`.\n"
        )
        raise SystemExit(EXIT_USER_ACTION)

    if resp.status_code == 429:
        return resp  # type: ignore[return-value]  # caller checks is_429

    if resp.status_code >= 500:
        sys.stderr.write(f"error: Linear server error {resp.status_code}\n")
        raise SystemExit(EXIT_ERROR)

    try:
        body = resp.json()
    except Exception as exc:
        sys.stderr.write(f"error: non-JSON response from Linear — {exc}\n")
        raise SystemExit(EXIT_ERROR) from exc

    if "errors" in body:
        messages = "; ".join(e.get("message", str(e)) for e in body["errors"])
        sys.stderr.write(f"error: GraphQL error — {messages}\n")
        raise SystemExit(EXIT_ERROR)

    return body


def _graphql_with_retry(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    url: str = GRAPHQL_URL,
) -> dict[str, Any]:
    """Call _graphql_request and apply exactly one Retry-After retry on 429."""
    result = _graphql_request(api_key, query, variables, url=url)

    # Check if the raw httpx.Response came back (429 path)
    if isinstance(result, httpx.Response) and result.status_code == 429:
        retry_after = int(result.headers.get("Retry-After", "1"))
        log.debug("429 rate-limited; sleeping %s s (Retry-After)", retry_after)
        time.sleep(retry_after)
        # Second attempt — if it 429s again, surface as error
        result2 = _graphql_request(api_key, query, variables, url=url)
        if isinstance(result2, httpx.Response) and result2.status_code == 429:
            sys.stderr.write(
                "error: rate limited by Linear twice in a row; try again later.\n"
            )
            raise SystemExit(EXIT_ERROR)
        return result2

    return result


# ---------------------------------------------------------------------------
# GraphQL queries
# ---------------------------------------------------------------------------

_VIEWER_QUERY = """
{ viewer { id name email } }
"""

_GET_ISSUE_QUERY = """
query GetIssueByIdentifier($identifier: String!) {
  issues(filter: { identifier: { eq: $identifier } }) {
    nodes {
      id
      identifier
      title
      description
      children {
        nodes {
          identifier
          title
        }
      }
      project {
        id
        name
        url
      }
    }
  }
}
"""

_GET_PROJECT_QUERY = """
query GetProject($id: String!, $first: Int!, $cursor: String) {
  project(id: $id) {
    id
    name
    issues(first: $first, after: $cursor) {
      nodes {
        identifier
        title
        description
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------

def cmd_check(args: argparse.Namespace, api_key: str) -> None:
    data = _graphql_with_retry(api_key, _VIEWER_QUERY)
    viewer = data.get("data", {}).get("viewer", {})
    _write_output({"authenticated": True, "viewer": viewer}, args)


def cmd_get_issue(args: argparse.Namespace, api_key: str) -> None:
    data = _graphql_with_retry(
        api_key, _GET_ISSUE_QUERY, {"identifier": args.identifier}
    )
    nodes = data.get("data", {}).get("issues", {}).get("nodes", [])
    if not nodes:
        sys.stderr.write(
            f"error: issue {args.identifier!r} not found — check the identifier.\n"
        )
        raise SystemExit(EXIT_ERROR)
    _write_output(nodes[0], args)


def cmd_get_project(args: argparse.Namespace, api_key: str) -> None:
    result = _get_project_pages(api_key, args.project_id)
    _write_output(result, args)


def _get_project_pages(
    api_key: str,
    project_id: str,
    *,
    url: str = GRAPHQL_URL,
) -> dict[str, Any]:
    """Fetch project issues up to MAX_PAGES pages; return combined result dict."""
    all_issues: list[dict[str, Any]] = []
    cursor: str | None = None
    project_meta: dict[str, Any] = {}

    for _page in range(MAX_PAGES):
        variables: dict[str, Any] = {
            "id": project_id,
            "first": PAGE_SIZE,
            "cursor": cursor,
        }
        data = _graphql_with_retry(api_key, _GET_PROJECT_QUERY, variables, url=url)
        project_node = data.get("data", {}).get("project")
        if project_node is None:
            sys.stderr.write(
                f"error: project {project_id!r} not found or inaccessible.\n"
            )
            raise SystemExit(EXIT_ERROR)

        if not project_meta:
            project_meta = {"id": project_node.get("id"), "name": project_node.get("name")}

        issues_conn = project_node.get("issues", {})
        all_issues.extend(issues_conn.get("nodes", []))
        page_info = issues_conn.get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return {**project_meta, "issues": {"nodes": all_issues}}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _write_output(data: Any, args: argparse.Namespace) -> None:
    fmt = getattr(args, "format", "json")
    output_path = getattr(args, "output", None)

    if fmt == "jsonl":
        items = data if isinstance(data, list) else [data]
        text = "\n".join(json.dumps(item, ensure_ascii=False) for item in items) + "\n"
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        log.info("Written to %s", output_path)
    else:
        sys.stdout.write(text)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def _build_parser() -> _ScrubbingArgumentParser:
    p = _ScrubbingArgumentParser(
        prog="linear",
        description="Linear GraphQL API CLI. API key is resolved via credbroker.",
    )
    p.add_argument("--format", choices=["json", "jsonl"], default="json")
    p.add_argument("--output", metavar="FILE")
    p.add_argument("--verbose", action="store_true")

    sub = p.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("check", help="Verify credentials and reachability.")

    get_issue = sub.add_parser("get-issue", help="Fetch one issue by identifier.")
    get_issue.add_argument("identifier", help="Issue identifier e.g. ENG-123")

    get_project = sub.add_parser("get-project", help="Fetch a project's issues.")
    get_project.add_argument("project_id", help="Project UUID")

    return p


def main(argv: list[str] | None = None) -> None:
    _reject_token_on_cli(argv if argv is not None else sys.argv[1:])
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    api_key = _load_api_key()

    dispatch = {
        "check": cmd_check,
        "get-issue": cmd_get_issue,
        "get-project": cmd_get_project,
    }
    handler = dispatch.get(args.subcommand)
    if handler is None:
        parser.error(f"unknown subcommand: {args.subcommand!r}")

    try:
        handler(args, api_key)
    except SystemExit:
        raise
    except Exception as exc:
        log.debug("unexpected error", exc_info=True)
        sys.stderr.write(f"error: unexpected — {exc}\n")
        raise SystemExit(EXIT_ERROR) from exc


if __name__ == "__main__":
    main()
