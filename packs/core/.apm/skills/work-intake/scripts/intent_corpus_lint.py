#!/usr/bin/env python3
"""Lint a directory of repository intents against the metadata shape contract.

Usage: python3 intent_corpus_lint.py --dir <repo-relative dir> [--root <path>]

Every file in the directory is routed to exactly one of two contracts by the
partition rule — a file is a tombstone if and only if its *preamble* carries a
``Tombstone:`` field — and then validated against that contract. No file is
skipped: a directory entry the lint does not route is a gap the exit code
cannot express, so routing is reported alongside the violations.

Exit codes follow the sibling allocator's posture rather than a lint's
convention. 0 is clean. 1 means at least one file is non-conforming. 2 means
the corpus could not be fully read, which is reported as its own state because
"no violations found" and "clean" are different claims about a corpus whose
files the lint could not open.

The preamble bound matters here twice. It decides the partition, so a
body-level ``Tombstone:`` line inside a narrative does not retire a live
intent, and it decides every field rule the live contract applies.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Bytecode is a write, and this lint promises to perform none.
sys.dont_write_bytecode = True

CONTRACT_LIVE = "live"
CONTRACT_TOMBSTONE = "tombstone"

# The tombstone field contract is `intent-renumber-and-reissue`'s: exactly
# three fields — the slug, unchanged from the retired artifact; the retirement
# date; and exactly one of the two terminal edges.
TOMBSTONE_PARTITION_FIELD = "Tombstone"
TOMBSTONE_REQUIRED: tuple[str, ...] = ("Slug", "Tombstone")
TOMBSTONE_EDGES: tuple[str, ...] = ("Reissued as", "Retired")
TOMBSTONE_FIELD_COUNT = 3

_MAX_BYTES = 1_000_000


def _load_sibling(name: str, module_name: str):
    """Load a sibling script by path under a pack-and-skill-qualified name.

    Skills are independent and several may ship a same-named script, so a bare
    ``import`` would bind whichever directory reached the path first and then
    cache it for every later importer.
    """
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling module {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_shape = _load_sibling("intent_shape", "core_work_intake_intent_shape")
_safety = _load_sibling("file_safety", "core_work_intake_file_safety")


@dataclass(frozen=True)
class FileViolation:
    """One refusal, naming the file, the field at fault, and why."""

    path: str
    field: str
    reason: str


@dataclass
class LintResult:
    """What one run establishes about a corpus."""

    routed: dict[str, str] = field(default_factory=dict)
    violations: list[FileViolation] = field(default_factory=list)
    progress: dict[str, dict[str, str]] = field(default_factory=dict)
    unreadable: list[str] = field(default_factory=list)

    @property
    def accounted(self) -> set[str]:
        """Every entry this run reached, routed or refused as unreadable.

        A file that could not be read cannot be routed to a contract, so it is
        absent from `routed` by construction. Reporting both sets lets a caller
        check that no directory entry went unmentioned, which the exit code
        alone cannot express.
        """
        return set(self.routed) | {
            entry.split(":", 1)[0] for entry in self.unreadable
        }

    @property
    def is_clean(self) -> bool:
        """True only when every file was read and every file conformed."""
        return not self.violations and not self.unreadable

    @property
    def exit_code(self) -> int:
        if self.unreadable:
            return 2
        if self.violations:
            return 1
        return 0


def _validate_tombstone(text: str) -> list[tuple[str, str]]:
    """Return ``(field, reason)`` for each way a tombstone fails its contract."""
    pairs = _shape.read_preamble(text)
    names = [name for name, _ in pairs]
    present = {name for name, value in pairs if value}
    faults: list[tuple[str, str]] = []

    for required in TOMBSTONE_REQUIRED:
        if required not in present:
            faults.append((required, "a tombstone's required field is absent"))

    edges = [edge for edge in TOMBSTONE_EDGES if edge in present]
    if len(edges) != 1:
        faults.append(
            (
                TOMBSTONE_EDGES[0],
                "a tombstone carries exactly one of "
                f"{' or '.join(f'`{edge}:`' for edge in TOMBSTONE_EDGES)}, "
                f"and this one carries {len(edges)}",
            )
        )

    if len(names) != TOMBSTONE_FIELD_COUNT:
        faults.append(
            (
                TOMBSTONE_PARTITION_FIELD,
                f"a tombstone carries exactly {TOMBSTONE_FIELD_COUNT} fields, "
                f"and this one carries {len(names)}",
            )
        )

    for name in sorted(set(names)):
        if names.count(name) > 1:
            faults.append((name, f"preamble field appears more than once "
                                 f"({names.count(name)})"))

    return faults


def _is_tombstone(text: str) -> bool:
    """The partition rule, read over the preamble alone."""
    return any(
        name == TOMBSTONE_PARTITION_FIELD and value
        for name, value in _shape.read_preamble(text)
    )


def lint_corpus(root: Path, directory: Path) -> LintResult:
    """Route and validate every file in ``directory``.

    Confinement goes through the skill's `file_safety` helper; a refusal there
    is an unreadable corpus rather than a crash, which is the state the exit
    code reports separately from a violation.
    """
    result = LintResult()
    root = Path(root)
    directory = Path(directory)

    try:
        _safety.validate_confined_directory(root, directory)
        paths = _safety.list_confined_regular_files(root, directory)
    except (_safety.UnsafeContentError, OSError, RuntimeError, ValueError) as error:
        result.unreadable.append(f"{directory}: {type(error).__name__}")
        return result

    # First pass: read and route. The live slug set has to exist before any
    # supersession is resolved, so validation cannot run in the same pass.
    texts: dict[str, str] = {}
    for path in sorted(paths):
        name = path.name
        try:
            raw = _safety.read_confined_regular_file(root, path, max_bytes=_MAX_BYTES)
            text = raw.decode("utf-8")
        except (_safety.UnsafeContentError, OSError, ValueError) as error:
            result.unreadable.append(f"{name}: {type(error).__name__}")
            continue
        texts[name] = text
        result.routed[name] = (
            CONTRACT_TOMBSTONE if _is_tombstone(text) else CONTRACT_LIVE
        )

    live_texts = [
        text for name, text in texts.items() if result.routed[name] == CONTRACT_LIVE
    ]
    live = _shape.live_slugs(live_texts)

    # Second pass: validate each file against the contract it routed to.
    for name, text in texts.items():
        if result.routed[name] == CONTRACT_TOMBSTONE:
            for field_name, reason in _validate_tombstone(text):
                result.violations.append(FileViolation(name, field_name, reason))
            continue

        for violation in _shape.validate_live_intent(text):
            result.violations.append(
                FileViolation(name, violation.field, violation.reason)
            )
        for violation in _shape.validate_supersession(text, live):
            result.violations.append(
                FileViolation(name, violation.field, violation.reason)
            )
        result.progress[name] = _shape.progress_state(text)

    return result


def _reconfigure_streams() -> None:
    """Both streams carry UTF-8 before the first print."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Lint one directory and return the process exit code."""
    _reconfigure_streams()

    parser = argparse.ArgumentParser(
        description="Lint repository intents against the metadata shape contract."
    )
    parser.add_argument("--dir", required=True, help="repository-relative directory")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    result = lint_corpus(root, root / args.dir)

    for name in sorted(result.progress):
        state = result.progress[name]
        rendered = ", ".join(f"{k}={state[k]}" for k in _shape.PROGRESS_FIELDS)
        print(f"{name}: {rendered}")

    for violation in sorted(result.violations, key=lambda v: (v.path, v.field)):
        print(
            f"{violation.path}: {violation.field}: {violation.reason}",
            file=sys.stderr,
        )

    for entry in sorted(result.unreadable):
        print(f"unreadable: {entry}", file=sys.stderr)

    counts = (
        f"{len(result.routed)} file(s), "
        f"{sum(1 for c in result.routed.values() if c == CONTRACT_LIVE)} live, "
        f"{sum(1 for c in result.routed.values() if c == CONTRACT_TOMBSTONE)} tombstone"
    )
    if result.is_clean:
        print(f"intent-corpus-lint: clean — {counts}")
    else:
        print(
            f"intent-corpus-lint: {len(result.violations)} violation(s), "
            f"{len(result.unreadable)} unreadable — {counts}",
            file=sys.stderr,
        )
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
