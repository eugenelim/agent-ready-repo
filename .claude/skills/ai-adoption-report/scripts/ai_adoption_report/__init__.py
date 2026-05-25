#!/usr/bin/env python3
"""ai-adoption-report CLI entry point.

T1 scaffold: argparse subcommands (baseline / cohort / program), Python
version guard, path-safety helper, --window FROM..TO parser, exit codes.
Each subcommand body is a stub that prints "not yet implemented" and
exits 0. Later tasks fill in the real work.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, Sequence, Tuple

PYTHON_FLOOR = (3, 10)

EXIT_OK = 0
EXIT_BUG = 1
EXIT_VALIDATION = 2


def _check_python_version(version_info=None) -> None:
    info = version_info if version_info is not None else sys.version_info
    if (info[0], info[1]) < PYTHON_FLOOR:
        floor = ".".join(str(x) for x in PYTHON_FLOOR)
        have = ".".join(str(info[i]) for i in range(min(3, len(info))))
        print(
            "ai-adoption-report requires Python {} or later; running under {}".format(
                floor, have
            ),
            file=sys.stderr,
        )
        sys.exit(EXIT_VALIDATION)


_check_python_version()


class ValidationError(Exception):
    """Flag-combo / path-safety errors. Exit 2."""


# ---------------------------------------------------------------------------
# --window FROM..TO parser
# ---------------------------------------------------------------------------
# `date.fromisoformat` accepts forms like `2026-02-19T00:00:00` on newer
# Pythons; the regex pins the input to a bare YYYY-MM-DD date so a window
# expressed with a time component is rejected up front.
_ISO_DATE_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")


def parse_window_flag(s: str) -> Tuple[str, str]:
    """Parse `--window FROM..TO` into two YYYY-MM-DD strings.

    Returns the two strings verbatim — no normalization. String equality
    is the spec's window-match rule for program mode (see spec §"Input
    file validation").
    """
    parts = s.split("..")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise argparse.ArgumentTypeError(
            "--window must be FROM..TO with both YYYY-MM-DD dates present; got '{}'".format(s)
        )
    for side, value in (("from", parts[0]), ("to", parts[1])):
        if not _ISO_DATE_RE.match(value):
            raise argparse.ArgumentTypeError(
                "--window {} '{}' is not YYYY-MM-DD (no time component allowed)".format(
                    side, value
                )
            )
        try:
            date.fromisoformat(value)
        except ValueError:
            raise argparse.ArgumentTypeError(
                "--window {} '{}' is not a valid calendar date".format(side, value)
            )
    return parts[0], parts[1]


# ---------------------------------------------------------------------------
# Path safety: every path-bearing flag must resolve inside Path.cwd().
# ---------------------------------------------------------------------------
def validate_local_path(path: str, *, role: str) -> Path:
    """Resolve ``path`` and assert it lies inside the current working dir.

    ``role`` names the originating flag (e.g. ``"baseline"``, ``"output"``);
    it is woven into every error message so the user knows which flag was
    bad. Reused by every mode for every path-bearing flag.

    Raises :class:`ValidationError` (exit 2) on null bytes, unresolvable
    paths, or paths that resolve outside ``Path.cwd()``.
    """
    if "\x00" in path:
        raise ValidationError("--{}: path contains a null byte".format(role))
    try:
        resolved = Path(path).resolve()
    except OSError as e:
        raise ValidationError(
            "--{}: cannot resolve path '{}': {}".format(role, path, e)
        )
    cwd = Path.cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise ValidationError(
            "--{}: path '{}' resolves outside the current working directory ({})".format(
                role, path, cwd
            )
        )
    return resolved


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------
FORMAT_CHOICES = ("markdown", "json", "both")


def _common_parent() -> argparse.ArgumentParser:
    """Parent parser holding the common flags shared by every mode.

    Held as a single parser and re-used across all three subparsers via
    ``parents=[common]`` so each subcommand's ``--help`` lists the common
    flags alongside its mode-specific ones.
    """
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--output",
        required=True,
        metavar="FILE",
        help=(
            "Path to Markdown output. JSON sidecar is written to the same "
            "path with .md replaced by .json (or appended if no extension)."
        ),
    )
    parent.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default="both",
        help="Output format. Default: both.",
    )
    parent.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output files. Without it, exit 2 on collision.",
    )
    parent.add_argument(
        "--title",
        metavar="TITLE",
        help='Optional title for the Markdown header. Default: "AI-adoption report — <mode>".',
    )
    parent.add_argument(
        "--verbose",
        action="store_true",
        help="Debug logging.",
    )
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-adoption-report",
        description=(
            "Consume flow-metrics JSON outputs and produce a comparison "
            "report in one of three modes: baseline, cohort, program."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", metavar="MODE")
    # required=True via attribute assignment for portability with older
    # argparse subparser quirks; the bare invocation still surfaces a
    # clean "the following arguments are required" error.
    sub.required = True

    common = _common_parent()

    # baseline ----------------------------------------------------------
    baseline = sub.add_parser(
        "baseline",
        parents=[common],
        help="Compare a single scope across two windows (pre-AI vs current).",
        description="baseline mode: two flow-metrics JSONs in, deltas out.",
    )
    baseline.add_argument(
        "--baseline",
        required=True,
        metavar="PATH",
        help="flow-metrics JSON for the prior window.",
    )
    baseline.add_argument(
        "--current",
        required=True,
        metavar="PATH",
        help="flow-metrics JSON for the current window.",
    )
    baseline.add_argument(
        "--include-cohort-breakdown",
        dest="include_cohort_breakdown",
        action="store_true",
        help=(
            "Append a cohort-vs-control comparison when both inputs carry "
            "a cohort_breakdown block with matching meta.cohort_jql."
        ),
    )

    # cohort ------------------------------------------------------------
    cohort = sub.add_parser(
        "cohort",
        parents=[common],
        help="Report the within-window AI-cohort vs control split.",
        description="cohort mode: one flow-metrics JSON (with cohort_breakdown) in, deltas out.",
    )
    cohort.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="flow-metrics JSON produced with --cohort-jql.",
    )

    # program -----------------------------------------------------------
    program = sub.add_parser(
        "program",
        parents=[common],
        help="Roll up many scopes for a single window.",
        description="program mode: N flow-metrics JSONs in, per-scope rows + aggregates out.",
    )
    program.add_argument(
        "--inputs",
        required=True,
        metavar="DIR",
        help="Directory of flow-metrics JSON files. Globs *.json (no recursion).",
    )
    program.add_argument(
        "--window",
        required=True,
        type=parse_window_flag,
        metavar="FROM..TO",
        help="Window filter; only inputs whose meta.window matches are included.",
    )
    program.add_argument(
        "--include-cohort-breakdown",
        dest="include_cohort_breakdown",
        action="store_true",
        help=(
            "Roll up cohort/control across scopes that carry a "
            "cohort_breakdown block."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Flag-combo / path-safety validation. Runs before any file read.
# ---------------------------------------------------------------------------
def _path_roles_for_mode(args: argparse.Namespace) -> Iterator[Tuple[str, str]]:
    yield ("output", args.output)
    if args.mode == "baseline":
        yield ("baseline", args.baseline)
        yield ("current", args.current)
    elif args.mode == "cohort":
        yield ("input", args.input)
    elif args.mode == "program":
        yield ("inputs", args.inputs)
    else:
        # Defensive: build_parser() restricts args.mode to one of the
        # three above. Any other value means a subparser was added without
        # updating this dispatch — fail loudly instead of silently
        # skipping path validation.
        raise ValidationError("unknown mode '{}'".format(args.mode))


def validate_args(args: argparse.Namespace) -> None:
    """Apply T1 flag-combo validation.

    Currently only path-safety: every path-bearing flag must resolve
    inside ``Path.cwd()``. Later tasks layer on input-file validation
    (T2) and mode-specific checks (T3, T4).
    """
    for role, value in _path_roles_for_mode(args):
        validate_local_path(value, role=role)


# ---------------------------------------------------------------------------
# Subcommand dispatch. baseline + cohort delegate to T3's modes module;
# program is still stubbed for T4/T6.
# ---------------------------------------------------------------------------
def _default_title(mode: str) -> str:
    return "AI-adoption report — {}".format(mode)


def _resolve_generated_at() -> str:
    """Return the ``generated_at`` timestamp the renderers should use.

    Honors the test-pinning env var :data:`write.GENERATED_AT_ENV_VAR`
    (``AI_ADOPTION_REPORT_GENERATED_AT``) for deterministic-build tests
    (T9's golden-file diffs rely on this). When unset, returns the
    current UTC clock in ISO-8601 seconds precision with the trailing
    ``Z`` form (``2026-05-19T14:30:00Z``).

    T7 stays pure — never reads the clock or env. T8 owns the timestamp
    and threads it through ``render_markdown`` / ``render_json``.
    """
    from .write import GENERATED_AT_ENV_VAR

    pinned = os.environ.get(GENERATED_AT_ENV_VAR)
    if pinned:
        return pinned
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _render_and_write(args: argparse.Namespace, report) -> None:
    """Render + atomic-write per ``--format``.

    Dispatch:

    - ``markdown``: write only the Markdown file at ``--output``.
    - ``json``: write only the derived ``.json`` sidecar; the Markdown
      renderer is **not** invoked at all (spec line 86, "json skips
      Markdown rendering"). The ``--output`` flag is interpreted as the
      Markdown-path-shaped value and the sidecar is derived from it —
      so ``--format=json --output report.md`` writes ``report.json``
      and never touches ``report.md``.
    - ``both`` (default): render both, derive sidecar, write both atomically.
    """
    from .render import render_json, render_markdown
    from .write import derive_sidecar_path, write_outputs

    markdown_path = validate_local_path(args.output, role="output")
    title = getattr(args, "title", None) or _default_title(report.mode)
    generated_at = _resolve_generated_at()
    fmt = getattr(args, "format", "both")

    if fmt == "markdown":
        md_text = render_markdown(report, title=title, generated_at=generated_at)
        write_outputs(
            [(markdown_path, md_text)],
            overwrite=args.overwrite,
        )
    elif fmt == "json":
        # Per spec line 86 + T8 brief option (a): the --output path is
        # always Markdown-shaped; for --format=json we still derive the
        # sidecar path from it but skip the Markdown renderer entirely.
        json_path = derive_sidecar_path(markdown_path)
        json_text = render_json(report, title=title, generated_at=generated_at)
        write_outputs(
            [(json_path, json_text)],
            overwrite=args.overwrite,
        )
    else:  # "both"
        json_path = derive_sidecar_path(markdown_path)
        md_text = render_markdown(report, title=title, generated_at=generated_at)
        json_text = render_json(report, title=title, generated_at=generated_at)
        write_outputs(
            [(markdown_path, md_text), (json_path, json_text)],
            overwrite=args.overwrite,
        )


def _run_baseline(args: argparse.Namespace) -> int:
    # Local import to avoid a module-load cycle: modes.py imports
    # ValidationError from this package.
    from .modes import run_baseline

    report = run_baseline(args)
    _render_and_write(args, report)
    return EXIT_OK


def _run_cohort(args: argparse.Namespace) -> int:
    from .modes import run_cohort

    report = run_cohort(args)
    _render_and_write(args, report)
    return EXIT_OK


def _run_program(args: argparse.Namespace) -> int:
    from .modes import run_program

    report = run_program(args)
    _render_and_write(args, report)
    return EXIT_OK


_DISPATCH = {
    "baseline": _run_baseline,
    "cohort": _run_cohort,
    "program": _run_program,
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
        return _DISPATCH[args.mode](args)
    except ValidationError as e:
        print("error: {}".format(e), file=sys.stderr)
        return EXIT_VALIDATION


if __name__ == "__main__":
    sys.exit(main())
