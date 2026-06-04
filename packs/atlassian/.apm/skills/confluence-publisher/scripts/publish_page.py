"""Publish a single page to Confluence — create new or update existing.

Invocation examples:

    python scripts/publish_page.py --check
    python scripts/publish_page.py --page-id 12345 --input report.md
    python scripts/publish_page.py --url 'https://acme.atlassian.net/wiki/spaces/ENG/pages/12345/Foo' --input report.md
    python scripts/publish_page.py --from-frontmatter --input crawled/handbook.md
    python scripts/publish_page.py --space ENG --title 'Q3 Roadmap' --parent-id 555 --input roadmap.md
    python scripts/publish_page.py --page-id 42 --input report.md --dry-run

Credentials are resolved via the build-projected ``credentials_shim`` sibling
(Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile); run
``credential-setup`` skill to populate the namespace. The
token is never accepted on the command line.

Exit codes:
- 0  success (or dry-run printed)
- 2  user action required (missing creds, ambiguous target, validation)
- 1  unexpected error
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from urllib.parse import urljoin

# Bootstrap when invoked as ``python scripts/publish_page.py`` so the
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

# Every sibling import that transitively pulls a third-party dependency goes
# inside this guard so a missing dep yields the banded exit-2 "run pip
# install" message instead of a raw traceback: ._render pulls markdown_it,
# ._target pulls yaml. When they sat below the guard a missing one bypassed
# the contract entirely.
try:
    from ._client import (  # noqa: E402
        AuthError,
        ConflictError,
        ConfluenceClient,
        ConfluenceError,
        PageRef,
        load_credentials,
    )
    from ._render import (  # noqa: E402
        ALLOWED_INPUT_FORMATS,
        INPUT_MARKDOWN,
        as_storage_xhtml,
        extract_title_from_markdown,
    )
    from ._target import (  # noqa: E402
        ResolvedTarget,
        TargetResolutionError,
        read_input,
        resolve_target,
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

log = logging.getLogger("confluence_publisher")

# Banded exit-code taxonomy (docs/specs/credentialed-cli-exit-code-contract):
#   0     success
#   1     functional / operational error (message carries the cause)
#   2     user must act — credentials, conflicts, target/input the user must fix
#   3-9   reserved for the credential/auth band (never reuse for functional)
EXIT_OK = 0
EXIT_USER_ACTION = 2
EXIT_ERROR = 1

DEFAULT_VERSION_COMMENT = "Published by confluence-publisher"

# Token-shaped CLI flags are rejected before argparse runs — argparse would
# otherwise echo the offending ``--flag VALUE`` verbatim in its
# "unrecognized arguments" error, leaking the secret to stderr / the agent
# transcript. The Confluence PAT (or Cloud API token used as a Basic-auth
# password) is resolved only via env / keyring / dotfile. Mirrors the
# sibling jira / jira-align idiom (exact-set match).
# Superset of the CONVENTIONS § "The argv ban" canonical six
# (--token, --api-token, --api-key, --bearer, --pat, --password) plus the
# short -t and a Confluence-specific alias.
TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--api-key", "--bearer", "-t",
    "--confluence-token", "--pat", "--password",
})


def _reject_token_on_cli(argv: list[str]) -> None:
    """Confluence tokens / PATs are secret; refuse to accept them as CLI args."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API tokens must not be passed on the command line. "
                "Run `credential-setup` skill to store CONFLUENCE_API_TOKEN "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check", action="store_true",
                        help="Verify credentials and connectivity, then exit")

    # Target-mode flags — at most one of the first three.
    parser.add_argument("--page-id", help="Update this page (preferred)")
    parser.add_argument("--url", help="Confluence URL; page ID parsed from /pages/<id>")
    parser.add_argument("--from-frontmatter", action="store_true",
                        help="Read confluence_id (and optional version) from YAML frontmatter")
    parser.add_argument("--space", help="Space key for lookup-or-create mode")
    parser.add_argument("--title", help="Page title for lookup-or-create mode (or to override on update)")
    parser.add_argument("--parent-id", help="Parent page ID (lookup-or-create mode)")

    # Input.
    parser.add_argument("--input", help="Source file path, or '-' for stdin")
    parser.add_argument("--input-format", choices=ALLOWED_INPUT_FORMATS,
                        default=INPUT_MARKDOWN,
                        help="markdown (default), storage, text")

    # Publish behavior.
    parser.add_argument("--version-comment", default=DEFAULT_VERSION_COMMENT,
                        help="Recorded on the new page version")
    parser.add_argument("--attach", action="append", default=[],
                        metavar="PATH",
                        help="Upload file as a page attachment (repeatable)")
    parser.add_argument("--label", action="append", default=[],
                        metavar="LABEL",
                        help="Apply label after publish (repeatable)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print rendered storage XHTML and planned op; no writes")
    parser.add_argument("--insecure", action="store_true",
                        help="Disable TLS verification (Server/DC with self-signed)")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    return parser.parse_args(argv)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _decide_title(
    *,
    cli_title: str | None,
    rendered_md: str | None,
    existing: PageRef | None,
) -> str | None:
    if cli_title:
        return cli_title
    if rendered_md:
        guess = extract_title_from_markdown(rendered_md)
        if guess:
            return guess
    if existing is not None:
        return existing.title
    return None


def _build_storage(
    *,
    body: str,
    input_format: str,
    attachments: list[Path],
) -> str:
    filenames = [p.name for p in attachments]
    return as_storage_xhtml(
        body,
        input_format=input_format,
        attachment_filenames=filenames,
    )


def _full_url(base_url: str, webui_path: str) -> str:
    if not webui_path:
        return base_url
    if webui_path.startswith(("http://", "https://")):
        return webui_path
    return urljoin(base_url + "/", webui_path.lstrip("/"))


def _check(client: ConfluenceClient) -> int:
    me = client.whoami()
    name = (
        me.get("displayName")
        or me.get("publicName")
        or me.get("username")
        or me.get("accountId")
        or "<unknown>"
    )
    print(f"OK: authenticated as {name} against {client.base_url}")
    return EXIT_OK


def _route_auth_error(exc: AuthError) -> int:
    # 403 means the token works but lacks permission — a setup re-run won't
    # fix it. Surface as ERROR so the agent doesn't tell the user to
    # reconfigure a working token. Any AuthError without an HTTP status
    # (e.g. constructor-time validation) routes to NEED-INPUT by intent:
    # those errors are "the user must provide something" by definition.
    if exc.status_code == 403:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"NEED-INPUT: {exc}", file=sys.stderr)
    return EXIT_USER_ACTION


def _resolve_existing_page(
    *,
    client: ConfluenceClient,
    target: ResolvedTarget,
) -> PageRef | None:
    if target.page_id:
        return client.get_page(target.page_id)
    if target.space_key and target.title:
        matches = client.find_page_by_title(target.space_key, target.title)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ids = ", ".join(m.id for m in matches)
            raise TargetResolutionError(
                f"NEED-INPUT: multiple pages match space={target.space_key} title={target.title!r}: "
                f"page IDs [{ids}] — pass --page-id to disambiguate"
            )
        return None
    raise TargetResolutionError("internal: target has no page_id and no space+title")


def _upload_attachments(
    client: ConfluenceClient,
    page_id: str,
    attachments: list[Path],
) -> None:
    for path in attachments:
        if not path.exists():
            raise FileNotFoundError(f"attachment not found: {path}")
        log.info("uploading attachment: %s", path.name)
        client.upload_attachment(page_id, path)


def _apply_labels(client: ConfluenceClient, page_id: str, labels: list[str]) -> list[str]:
    failures: list[str] = []
    for label in labels:
        try:
            client.apply_label(page_id, label)
        except ConfluenceError as exc:
            log.warning("label %r failed: %s", label, exc)
            failures.append(label)
    return failures


def _publish(
    *,
    client: ConfluenceClient,
    target: ResolvedTarget,
    args: argparse.Namespace,
) -> int:
    attachments = [Path(p) for p in (args.attach or [])]
    for path in attachments:
        if not path.exists():
            print(f"ERROR: attachment not found: {path}", file=sys.stderr)
            return EXIT_USER_ACTION

    existing = _resolve_existing_page(client=client, target=target)

    body_storage = _build_storage(
        body=target.body_text,
        input_format=args.input_format,
        attachments=attachments,
    )

    rendered_md = target.body_text if args.input_format == INPUT_MARKDOWN else None
    title = _decide_title(
        cli_title=target.title,
        rendered_md=rendered_md,
        existing=existing,
    )

    if existing is None:
        if not target.space_key:
            print("ERROR: create requires --space", file=sys.stderr)
            return EXIT_USER_ACTION
        if not title:
            print(
                "ERROR: create requires a title — pass --title or include a # H1 in markdown",
                file=sys.stderr,
            )
            return EXIT_USER_ACTION
        op = "create"
    else:
        op = "update"
        if not title:
            title = existing.title

    if args.dry_run:
        print(f"DRY-RUN: would {op} page" + (f" {existing.id}" if existing else ""))
        print(f"TITLE: {title}")
        print(f"SPACE: {target.space_key or (existing.space_key if existing else '<unknown>')}")
        if attachments:
            print("ATTACHMENTS: " + ", ".join(p.name for p in attachments))
        if args.label:
            print("LABELS: " + ", ".join(args.label))
        print("--- storage XHTML ---")
        print(body_storage)
        return EXIT_OK

    if existing is None:
        page = client.create_page(
            space_key=target.space_key or "",
            title=title or "Untitled",
            body_storage=body_storage,
            parent_id=target.parent_id,
        )
        # Create must come first; attachments follow. A body referencing
        # an attachment renders broken until the upload completes.
        if attachments:
            _upload_attachments(client, page.id, attachments)
    else:
        # Existing page: upload attachments first so the new body's
        # <ac:image> references resolve immediately after update. If
        # any upload raises, the body update below is skipped and the
        # previously-uploaded attachments persist on the page — re-run
        # is idempotent (Confluence dedupes attachments by filename).
        if attachments:
            _upload_attachments(client, existing.id, attachments)
        new_version = existing.version + 1
        try:
            page = client.update_page(
                page_id=existing.id,
                title=title or existing.title,
                space_key=existing.space_key,
                body_storage=body_storage,
                new_version=new_version,
                version_comment=args.version_comment,
            )
        except ConflictError:
            log.warning("409 on update; re-reading to check for concurrent edit")
            refreshed = client.get_page(existing.id)
            # If the page advanced past our expected next version, a
            # concurrent edit landed — don't silently overwrite it.
            if refreshed.version > existing.version:
                print(
                    f"ERROR: concurrent edit — page {existing.id} advanced from "
                    f"version {existing.version} to {refreshed.version} while "
                    "publishing. Re-read the current content and re-run if your "
                    "changes still apply.",
                    file=sys.stderr,
                )
                return EXIT_USER_ACTION
            try:
                page = client.update_page(
                    page_id=refreshed.id,
                    title=title or refreshed.title,
                    space_key=refreshed.space_key,
                    body_storage=body_storage,
                    new_version=refreshed.version + 1,
                    version_comment=args.version_comment,
                )
            except ConflictError:
                print(
                    "ERROR: persistent conflict on update. Re-run after "
                    "confirming the latest content is what you want.",
                    file=sys.stderr,
                )
                return EXIT_USER_ACTION

    label_failures: list[str] = []
    if args.label:
        label_failures = _apply_labels(client, page.id, args.label)

    full_url = _full_url(client.base_url, page.webui_path)
    print(f"OK: {op} page {page.id} (version {page.version}) — {full_url}")
    if label_failures:
        print(
            "WARNING: failed to apply labels: " + ", ".join(label_failures),
            file=sys.stderr,
        )
    return EXIT_OK


def _run_publish(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)

    if args.insecure:
        print(
            "WARNING: TLS verification disabled (--insecure) — the connection "
            "to Confluence is not authenticated and is vulnerable to "
            "man-in-the-middle attacks.",
            file=sys.stderr,
        )

    try:
        creds = load_credentials()
    except AuthError as exc:
        print(f"NEED-INPUT: {exc}", file=sys.stderr)
        print(
            "Run `credential-setup` skill to configure credentials.",
            file=sys.stderr,
        )
        return EXIT_USER_ACTION

    with ConfluenceClient(creds, verify_tls=not args.insecure) as client:
        if args.check:
            try:
                return _check(client)
            except AuthError as exc:
                return _route_auth_error(exc)
            except ConfluenceError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return EXIT_ERROR

        if not args.input:
            print("ERROR: --input is required (or '-' for stdin)", file=sys.stderr)
            return EXIT_USER_ACTION

        try:
            raw_body = read_input(args.input)
        except FileNotFoundError as exc:
            print(f"ERROR: input file not found: {exc}", file=sys.stderr)
            return EXIT_USER_ACTION

        try:
            target = resolve_target(
                raw_body=raw_body,
                page_id=args.page_id,
                url=args.url,
                from_frontmatter=args.from_frontmatter,
                space=args.space,
                title=args.title,
                parent_id=args.parent_id,
            )
        except TargetResolutionError as exc:
            print(f"NEED-INPUT: {exc}", file=sys.stderr)
            return EXIT_USER_ACTION

        try:
            return _publish(client=client, target=target, args=args)
        except TargetResolutionError as exc:
            print(f"{exc}", file=sys.stderr)
            return EXIT_USER_ACTION
        except AuthError as exc:
            return _route_auth_error(exc)
        except ConfluenceError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return EXIT_ERROR


def main(argv: list[str] | None = None) -> int:
    # Guard runs before _run_publish's own parse, against the same argv
    # source the parser will see (explicit argv, else sys.argv[1:]), so the
    # reject and the parse can never diverge on what they inspect.
    _reject_token_on_cli(sys.argv[1:] if argv is None else argv)
    # Top-level catch-all: no exception escapes as a traceback. `except
    # Exception` deliberately does NOT catch SystemExit / KeyboardInterrupt.
    try:
        return _run_publish(argv)
    except Exception as exc:  # noqa: BLE001 — intentional functional catch-all
        name = type(exc).__name__
        if name == "Tier2HardFailError":
            sys.stderr.write(
                f"error: OS keyring unavailable ({name}); set CONFLUENCE_API_TOKEN "
                "via env or the dotfile, or run `credential-setup`.\n"
            )
        else:
            sys.stderr.write(f"error: unexpected {name}; report this if it persists.\n")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
