"""Generate a deterministic neutral catalogue index."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agentbundle.catalogue_tooling.index_generator import CatalogueIndexError, generate_index
from agentbundle.safety import PathJailError, WriteError, assert_under, write_files_no_follow

if TYPE_CHECKING:
    import argparse


_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _diagnostic(code: str, message: str, location: str) -> dict[str, str]:
    return {"code": code, "message": message.replace("\n", " "), "location": location}


def _result(
    *,
    status: str,
    dry_run: bool,
    output: str | None,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "command": "catalogue index",
        "status": status,
        "dry_run": dry_run,
        "output": output,
        "diagnostics": diagnostics,
    }


def _emit(args: argparse.Namespace, result: dict[str, Any]) -> None:
    if args.format == "json":
        print(json.dumps(result, allow_nan=False, sort_keys=True))
        return
    if result["status"] == "ok":
        if args.dry_run:
            print("Validation passed.")
        else:
            print(f"Wrote catalogue index: {result['output']}")
        return
    for diagnostic in result["diagnostics"]:
        print(
            f"error[{diagnostic['code']}] {diagnostic['location']}: {diagnostic['message']}",
            file=sys.stderr,
        )


def _timestamp(args: argparse.Namespace) -> str | None:
    value = args.generated_at
    if value is not None:
        if not _RFC3339.fullmatch(value):
            raise CatalogueIndexError(
                "invalid-generated-at",
                "generated_at must be a valid RFC 3339 date-time with timezone",
                "generated_at",
            )
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise CatalogueIndexError(
                "invalid-generated-at",
                "generated_at must be a valid RFC 3339 date-time with timezone",
                "generated_at",
            ) from exc
        return (
            parsed.astimezone(dt.UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is None:
        return None
    try:
        seconds = int(source_date_epoch)
        return (
            dt.datetime.fromtimestamp(seconds, dt.UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (ValueError, OverflowError, OSError) as exc:
        raise CatalogueIndexError(
            "invalid-source-date-epoch",
            "SOURCE_DATE_EPOCH must be an in-range Unix integer timestamp",
            "SOURCE_DATE_EPOCH",
        ) from exc


def _output_path(root: Path, value: str | None) -> tuple[Path, bool]:
    if value is None:
        return root / "catalogue-index.json", True
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate, False
    return root / candidate, True


def run(args: argparse.Namespace) -> int:
    """Generate, validate, and optionally publish a catalogue index."""
    root = Path(args.catalogue_root)
    try:
        generated_at = _timestamp(args)
        index = generate_index(root, generated_at)
        output, confined = _output_path(root, args.output)
        if confined:
            try:
                assert_under(root, output)
            except (PathJailError, OSError, RuntimeError) as exc:
                raise CatalogueIndexError(
                    "unsafe-output",
                    "output path is outside the catalogue root",
                    "output",
                ) from exc
        serialized = (
            json.dumps(index, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        written: str | None = None
        if not args.dry_run:
            write_files_no_follow(output.parent, {output.name: serialized})
            written = str(output)
        result = _result(
            status="ok",
            dry_run=args.dry_run,
            output=written,
            diagnostics=[],
        )
        _emit(args, result)
        return 0
    except CatalogueIndexError as exc:
        diagnostic = _diagnostic(exc.code, exc.message, exc.location)
    except (PathJailError, RuntimeError):
        diagnostic = _diagnostic(
            "unsafe-output", "output path is outside the catalogue root", "output"
        )
    except (WriteError, OSError, ValueError) as exc:
        diagnostic = _diagnostic(
            "filesystem", str(exc) or "catalogue index filesystem operation failed", "output"
        )

    _emit(
        args,
        _result(
            status="error",
            dry_run=args.dry_run,
            output=None,
            diagnostics=[diagnostic],
        ),
    )
    return 1
