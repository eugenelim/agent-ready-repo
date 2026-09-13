"""Console-script entry point: the exit-code contract, and the wiring.

Three statuses and no others: 0, 1, 130. The 2-9 band is deliberately unclaimed
so a consumer can use it for its own credential or auth taxonomy without
colliding with this tool -- which is why an unrecognised flag has to be mapped
off argparse's default 2.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
from collections.abc import Sequence

from . import __version__
from .config import ConfigRefused, resolve_endpoint
from .encode import encode_records
from .profile import ProfileRefused, default_service_name, load_profile
from .source import InputRefused, iter_records, open_input
from .transport import (
    DestinationRefused,
    batch_records,
    resolve_destination,
    send_batches,
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INTERRUPTED = 130


class _Parser(argparse.ArgumentParser):
    """argparse exits 2 on a usage error; 2 is reserved, so this maps it to 1."""

    def error(self, message: str):  # noqa: D102 - argparse's own contract
        self.exit(EXIT_FAILED, f"{self.prog}: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="jsonl-otlp-export",
        description="Send JSONL records to an OpenTelemetry Collector as OTLP logs.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--input", required=True, help="the JSONL file to read")
    parser.add_argument("--root", default=None, help="directory the input must resolve inside")
    parser.add_argument("--config", default=None, help="TOML file declaring [telemetry].endpoint")
    parser.add_argument("--profile", default=None, help="TOML file declaring the field mapping")
    parser.add_argument("--service-name", default=None, help="resource service.name")
    parser.add_argument("--follow", action="store_true", help="keep reading appended lines")
    parser.add_argument("--for", dest="for_seconds", type=int, default=None,
                        help="end the run this many seconds after the first read")
    parser.add_argument("--best-effort", action="store_true",
                        help="exit 0 even when sending fails")
    return parser


def _connection_factory(scheme, connect_host, port, timeout, context):
    if scheme == "https":
        return http.client.HTTPSConnection(connect_host, port, timeout=timeout, context=context)
    return http.client.HTTPConnection(connect_host, port, timeout=timeout)


def _run(args, env, stream, connection_factory) -> int:
    # AC-0033 ("no endpoint -> exit 0") and AC-0052 ("no --profile -> exit 1")
    # are both unconditional and collide when neither is supplied. Off-by-default
    # wins: it is the Boundaries' first "Always do", and AC-0052 exists to stop a
    # *built-in* profile deciding the payload -- a question that does not arise
    # when nothing is being sent. Checking the profile first would demand one
    # from a user who has not enabled sending at all.
    endpoint = resolve_endpoint(env, args.config)

    # A profile that WAS supplied is validated even when nothing is configured,
    # which is what makes the documented dry run real: run with no endpoint to
    # check a profile, send nothing, and hear about any mistake in it. Returning
    # before this point would report success for a profile that cannot work.
    profile = load_profile(args.profile, args.root) if args.profile is not None else None

    if endpoint is None:
        print(
            "jsonl-otlp-export: no endpoint is configured; nothing was sent. "
            "Set OTEL_EXPORTER_OTLP_LOGS_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT, "
            "or give --config a TOML file declaring [telemetry].endpoint.",
            file=stream,
        )
        return EXIT_OK

    if profile is None:
        profile = load_profile(None, args.root)  # raises: there is no default
    service_name = args.service_name or default_service_name(args.profile)
    # AC-0055 anchors the run bound at the FIRST destination resolution, and
    # AC-0040 requires the request bound to cover resolution. `resolve_destination`
    # does the DNS work, so the clock starts before it, not when sending begins.
    run_started = time.monotonic()
    destination = resolve_destination(endpoint)
    fd = open_input(args.input, args.root)

    unmapped: dict[object, int] = {}
    dropped_deep: dict[str, int] = {}
    emitted = [0]

    def encode(batch, diagnostics=True):
        # `diagnostics` is False when the batcher re-encodes a subset it has
        # already encoded once to measure it. The callbacks fired on the parent
        # were complete and correct; firing them again on each half double-counts
        # every record.
        body = encode_records(
            batch, profile, service_name,
            on_skip=(lambda index, reason: print(
                f"jsonl-otlp-export: record {index + 1} of this batch skipped: {reason}",
                file=stream,
            )) if diagnostics else None,
            on_unmapped_severity=(lambda value: unmapped.__setitem__(
                value, unmapped.get(value, 0) + 1
            )) if diagnostics else None,
            on_dropped_deep=(lambda key: dropped_deep.__setitem__(
                key, dropped_deep.get(key, 0) + 1
            )) if diagnostics else None,
        )
        # Count what was actually EMITTED, not that the encoder ran. A batch
        # whose every record was skipped still posts a well-formed body with an
        # empty logRecords list, which a receiver answers 200 -- so counting
        # invocations reports success for a run that sent no record at all.
        if diagnostics:
            emitted[0] += len(body["resourceLogs"][0]["scopeLogs"][0]["logRecords"])
        return json.dumps(body).encode("utf-8")

    try:
        records = iter_records(
            fd, follow=args.follow, for_seconds=args.for_seconds, stream=stream
        )
        outcome = send_batches(
            batch_records(records, encode, on_oversize=lambda size: print(
                f"jsonl-otlp-export: one record encodes to {size} bytes, over the "
                "8 MiB request ceiling, and cannot be split; it was not sent",
                file=stream,
            )),
            destination,
            connection_factory,
            stream=stream,
            best_effort=args.best_effort,
            run_started=run_started,
        )
    finally:
        os.close(fd)

    for value, count in unmapped.items():
        # Once per distinct value with a count, not once per record: a run over a
        # large file would otherwise print a line per record and bury everything.
        print(
            f"jsonl-otlp-export: severity value {str(value).split(':', 1)[-1]} is not in the profile's "
            f"severity_map; {count} record(s) sent without a severity",
            file=stream,
        )

    for key, count in dropped_deep.items():
        print(
            f"jsonl-otlp-export: attribute {key!r} nests deeper than the limit; "
            f"omitted from {count} record(s)",
            file=stream,
        )

    if emitted[0] == 0:
        print("jsonl-otlp-export: no line yielded a valid record; nothing was sent",
              file=stream)
        return EXIT_FAILED
    if outcome.status != EXIT_OK and args.best_effort and not outcome.partial_success:
        # Same scoping as in send_batches: best-effort forgives a send failure,
        # not a receiver rejecting records on their content.
        return EXIT_OK
    return EXIT_FAILED if outcome.status else EXIT_OK


def main(argv: Sequence[str] | None = None, env=None, stream=None,
         connection_factory=None) -> int:
    stream = stream if stream is not None else sys.stderr
    env = os.environ if env is None else env
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        # `--version` and `--help` exit 0 through here; a usage error is already
        # mapped to 1 by _Parser.error. Anything else is normalised, so the
        # reserved band can never leak out of argparse.
        code = exc.code if isinstance(exc.code, int) else EXIT_FAILED
        return EXIT_OK if code == EXIT_OK else EXIT_FAILED

    try:
        return _run(args, env, stream, connection_factory or _connection_factory)
    except KeyboardInterrupt:
        print("jsonl-otlp-export: interrupted", file=stream)
        return EXIT_INTERRUPTED
    except (ConfigRefused, ProfileRefused, InputRefused, DestinationRefused) as exc:
        print(f"jsonl-otlp-export: {exc}", file=stream)
        return EXIT_FAILED
    except Exception as exc:  # noqa: BLE001 - the table's "unhandled exception" row
        # Never `BaseException`: SystemExit and KeyboardInterrupt must pass
        # through to their own handling rather than being flattened to 1.
        print(f"jsonl-otlp-export: unexpected failure: {exc}", file=stream)
        return EXIT_FAILED


if __name__ == "__main__":  # pragma: no cover - console script is the surface
    sys.exit(main())
