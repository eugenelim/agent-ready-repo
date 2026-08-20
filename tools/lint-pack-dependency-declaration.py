#!/usr/bin/env python3
"""Enforce that a pack declares every dependency it relies on.

Architecture section 3 is explicit: no pack may infer a dependency from another
pack's directory.  This gate deliberately uses two asymmetric detectors.  Check
A looks for executable `.py` and `.toml` lines that name `packs/<pack>/`, with
their `#` comment tails removed.  Markdown is deliberately *not* included:
measuring a prose-inclusive scan on the clean tree produced four false positives
in catalogue-curation's SKILL and reference Markdown.  One was an illustrative
hook landing path; the other three were prohibition-list examples telling a
skill not to write under another pack.  A SKILL.md path mention is an instruction
to a language model, not a filesystem dependency.  Widening this scan would
therefore redden the build without finding a real dependency.

Check B answers the opposite question with primitive-name references, not path
references.  A declared pack dependency is semantic: for example, atlassian
uses credential-brokers primitives without naming `packs/credential-brokers/`.
The measured path-reference version failed eight of the nine clean-tree
declarations for that reason.  Check B instead maps owned skills, agents, and
commands, then requires each required or recommended dependency to contribute a
referenced primitive name.  The current executable-only Check A and
primitive-name Check B measurements both find zero violations.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
# Floors carry headroom rather than pinning the current count. A floor equal to
# today's inventory turns every legitimate addition or removal into a build
# break, which trains a maintainer to bump the number without reading why it
# moved — the opposite of the deliberate update the message asks for. Measured:
# retiring one skill upstream took the counts below exact-count floors and
# reddened this gate for a change that was entirely correct. These values are
# set to catch a scan collapsing, which is the failure they exist for, and
# `tools/lint-no-direct-check-ignore.py` sets SCANNED_FLOOR the same way.
PACK_FLOOR = 18
PRIMITIVE_FLOOR = 110
PACK_PATH = re.compile(r"packs/([a-z0-9_-]+)/")
REFERENCE_SUFFIXES = frozenset({".md", ".toml", ".py", ".json"})
EXCLUDED_COMPONENTS = frozenset({"tests", "__pycache__", "node_modules"})
CHECK_B_EXCLUDED_COMPONENTS = EXCLUDED_COMPONENTS | {"evals"}


@dataclass
class AuditResult:
    """Inventory and findings produced by the two dependency checks."""

    packs: dict[str, Path] = field(default_factory=dict)
    primitives_by_pack: dict[str, set[str]] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


def _is_excluded(path: Path, excluded: frozenset[str]) -> bool:
    """Whether a file lies below an excluded directory component."""
    return any(component in excluded for component in path.parts)


def find_packs(root: Path) -> dict[str, Path]:
    """Return pack directories that have the required manifest."""
    packs_root = root / "packs"
    if not packs_root.is_dir():
        return {}
    return {
        path.name: path
        for path in sorted(packs_root.iterdir())
        if path.is_dir() and (path / "pack.toml").is_file()
    }


def _read_text(path: Path, root: Path, findings: list[str]) -> str | None:
    """Read UTF-8 content, making an unreadable source a loud failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        findings.append(
            f"{path.relative_to(root).as_posix()}: cannot be read ({exc}); "
            "the gate refuses to skip a file it cannot inspect"
        )
        return None


def find_primitives(
    root: Path, packs: dict[str, Path], findings: list[str]
) -> dict[str, set[str]]:
    """Map each pack to its owned primitive names and reject ambiguous names."""
    owners: dict[str, str] = {}
    primitives_by_pack: dict[str, set[str]] = {name: set() for name in packs}
    for pack_name, pack_dir in packs.items():
        candidates: list[tuple[str, Path]] = []
        skills = pack_dir / ".apm" / "skills"
        if skills.is_dir():
            candidates.extend(
                (path.parent.name, path)
                for path in skills.glob("*/SKILL.md")
                if path.is_file()
            )
        for kind in ("agents", "commands"):
            directory = pack_dir / ".apm" / kind
            if directory.is_dir():
                candidates.extend(
                    (path.stem, path) for path in directory.glob("*.md")
                    if path.is_file()
                )
        for primitive, _path in sorted(candidates):
            previous_owner = owners.get(primitive)
            if previous_owner is not None and previous_owner != pack_name:
                findings.append(
                    f"primitive `{primitive}` has ambiguous ownership: "
                    f"{previous_owner} and {pack_name}"
                )
            else:
                owners[primitive] = pack_name
            primitives_by_pack[pack_name].add(primitive)
    return primitives_by_pack


def declarations(
    root: Path, pack_name: str, pack_dir: Path, findings: list[str]
) -> set[str]:
    """Return only required and recommended dependency pack names."""
    manifest = pack_dir / "pack.toml"
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        findings.append(
            f"{manifest.relative_to(root).as_posix()}: cannot read pack "
            f"declarations ({exc})"
        )
        return set()
    try:
        dependency_data = data["pack"]["dependencies"]
    except (KeyError, TypeError):
        return set()
    declared: set[str] = set()
    for kind in ("required", "recommended"):
        entries = dependency_data.get(kind, [])
        if not isinstance(entries, list):
            findings.append(
                f"packs/{pack_name}/pack.toml: dependency section `{kind}` "
                "must be an array of tables"
            )
            continue
        for entry in entries:
            dependency = entry.get("pack") if isinstance(entry, dict) else None
            if not isinstance(dependency, str) or not dependency:
                findings.append(
                    f"packs/{pack_name}/pack.toml: dependency in `{kind}` "
                    "has no usable `pack` name"
                )
                continue
            declared.add(dependency)
    return declared


def _symlinked_directories(base: Path, root: Path) -> list[str]:
    """Repository-relative symlinked directories beneath ``base``.

    `Path.rglob` does not descend through a directory symlink, so anything under
    one is invisible to the scans below. That makes a symlink a blind spot
    rather than an error: content parked outside the scanned set and reached
    through a link inside it would never be inspected. The repository already
    refuses link-like roots elsewhere, so refuse them here rather than scan
    around them.
    """
    found: list[str] = []
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                if entry.is_dir():
                    found.append(entry.relative_to(root).as_posix())
                continue
            if entry.is_dir():
                stack.append(entry)
    return found


def _refuse_symlinks(base: Path, root: Path, findings: list[str]) -> None:
    """Record a finding for every symlinked directory in a scanned tree.

    The base itself is checked first. A symlink to a directory satisfies
    `is_dir()`, so a caller that guards with `is_dir()` and then walks would
    descend into the link's target and find no symlinked *children* — the link
    it should have refused is the walk's own root, and the tree reads clean.
    """
    if base.is_symlink():
        findings.append(
            f"{base.relative_to(root).as_posix()}: symlinked directory in a "
            "scanned tree; refusing to scan around it"
        )
        return
    for link in _symlinked_directories(base, root):
        findings.append(
            f"{link}: symlinked directory in a scanned tree; "
            "refusing to scan around it"
        )


def executable_files(pack_dir: Path) -> list[Path]:
    """Files in Check A's intentionally narrow executable-content scope."""
    return sorted(
        path for path in pack_dir.rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".toml"}
        and not _is_excluded(path.relative_to(pack_dir), EXCLUDED_COMPONENTS)
    )


def reference_files(pack_dir: Path) -> list[Path]:
    """Files in Check B's non-test semantic-reference scope.

    `pack.toml` is excluded, and that exclusion is load-bearing rather than
    tidiness. A dependency entry spells the depended-on pack's name — `pack =
    "desk-research"` — and many packs take their name from a primitive they own.
    Scanning the manifest therefore lets a declaration satisfy itself: the only
    "use" found is the declaration under test, so a dead entry reads as live and
    Check B can never fail. Measured: adding an unused `desk-research`
    dependency to `packs/github/pack.toml` passed while the manifest was in
    scope, and fails with it excluded. Every real declaration in this repository
    is still matched outside the manifest, so nothing legitimate depends on it.
    """
    manifest = pack_dir / "pack.toml"
    return sorted(
        path for path in pack_dir.rglob("*")
        if path.is_file()
        and path.suffix in REFERENCE_SUFFIXES
        and path != manifest
        and not _is_excluded(
            path.relative_to(pack_dir), CHECK_B_EXCLUDED_COMPONENTS
        )
    )


def _code_lines(path: Path, source: str, findings: list[str], relative: str) -> dict[int, str]:
    """Return `{lineno: code}` with comments removed and string bodies retained.

    Splitting a raw line on the first `#` is the obvious way to drop a comment
    and it is wrong in both directions. `sep = "#"; target = "packs/core/x"`
    loses the real reference after the `#` inside a string, so an undeclared
    dependency passes; that is a silent false negative in exactly the file type
    this check exists to police. So `.py` is tokenized and only genuine COMMENT
    tokens are dropped, and `.toml` is parsed so only real string *values* are
    searched. A file that cannot be tokenized or parsed FAILS — a silent skip
    here is a self-inflicted bypass.
    """
    if path.suffix == ".py":
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        except (tokenize.TokenError, SyntaxError, IndentationError) as exc:
            findings.append(f"{relative}: cannot tokenize: {exc}")
            return {}
        lines: dict[int, str] = {}
        for token in tokens:
            if token.type in {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE}:
                continue
            lines.setdefault(token.start[0], "")
            lines[token.start[0]] += " " + token.string
        return lines
    try:
        parsed = tomllib.loads(source)
    except tomllib.TOMLDecodeError as exc:
        findings.append(f"{relative}: cannot parse TOML: {exc}")
        return {}
    values: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            values.append(node)
        elif isinstance(node, dict):
            for key, item in node.items():
                values.append(str(key))
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed)
    # TOML carries no line numbers through `tomllib`, so a value hit is located
    # by finding the line that literally contains it. That keeps the reported
    # line honest without re-implementing a TOML parser.
    located: dict[int, str] = {}
    source_lines = source.splitlines()
    for value in values:
        for lineno, line in enumerate(source_lines, 1):
            if value and value in line:
                located.setdefault(lineno, "")
                located[lineno] += " " + value
    return located


def check_undeclared_paths(
    root: Path,
    pack_name: str,
    pack_dir: Path,
    declared: set[str],
    packs: dict[str, Path],
    findings: list[str],
) -> None:
    """Check A: require a declaration for executable cross-pack path use."""
    _refuse_symlinks(pack_dir, root, findings)
    for path in executable_files(pack_dir):
        source = _read_text(path, root, findings)
        if source is None:
            continue
        relative = path.relative_to(root).as_posix()
        for lineno, code in sorted(_code_lines(path, source, findings, relative).items()):
            for target in {match.group(1) for match in PACK_PATH.finditer(code)}:
                if target != pack_name and target in packs and target not in declared:
                    findings.append(
                        f"{relative}:{lineno}: "
                        f"references packs/{target}/ without declaring `{target}`"
                    )


def check_dead_declarations(
    root: Path,
    pack_name: str,
    pack_dir: Path,
    declared: set[str],
    primitives_by_pack: dict[str, set[str]],
    findings: list[str],
) -> None:
    """Check B: require each declaration to contribute a named primitive use."""
    source_parts: list[str] = []
    for path in reference_files(pack_dir):
        source = _read_text(path, root, findings)
        if source is not None:
            source_parts.append(source)
    source = "\n".join(source_parts)
    for dependency in sorted(declared):
        names = primitives_by_pack.get(dependency, set())
        # One alternation over the dependency's primitive names rather than one
        # regex pass per name, so the concatenated source is walked once. This
        # gate's cost is dominated by reading every pack file, not by matching,
        # so this is a simplification rather than a measured speed-up. The
        # lookarounds stay outside the alternation so a hyphenated name is still
        # matched whole — `\b` would match the `spec` inside `new-spec`, which
        # the hyphen-boundary self-test pins.
        used = False
        if names:
            alternation = "|".join(re.escape(name) for name in sorted(names))
            used = re.search(rf"(?<![\w-])(?:{alternation})(?![\w-])", source) is not None
        if not used:
            findings.append(
                f"pack `{pack_name}` declares `{dependency}`, but references "
                "no primitive it owns"
            )


def audit(root: Path) -> AuditResult:
    """Run both checks over packs rooted at ``root``."""
    result = AuditResult()
    result.packs = find_packs(root)
    result.primitives_by_pack = find_primitives(
        root, result.packs, result.findings
    )
    for pack_name, pack_dir in result.packs.items():
        declared = declarations(root, pack_name, pack_dir, result.findings)
        check_undeclared_paths(
            root, pack_name, pack_dir, declared, result.packs, result.findings
        )
        check_dead_declarations(
            root, pack_name, pack_dir, declared, result.primitives_by_pack,
            result.findings,
        )
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the lint and return a process status."""
    parser = argparse.ArgumentParser(
        description="Require pack dependencies to be declared and used."
    )
    parser.add_argument(
        "--root", default=None, metavar="PATH",
        help="repository root to audit (default: this repository)",
    )
    args = parser.parse_args(argv)
    root = ROOT if args.root is None else Path(args.root).resolve()
    result = audit(root)
    primitive_count = sum(len(names) for names in result.primitives_by_pack.values())

    if not result.packs:
        print("✖ no packs found to scan — this must not pass vacuously", file=sys.stderr)
        return 1
    if primitive_count == 0:
        print(
            "✖ no primitives found — the ownership map is empty, so check B "
            "cannot fail; this must not pass vacuously",
            file=sys.stderr,
        )
        return 1

    if args.root is None:
        floor_failures: list[str] = []
        if len(result.packs) < PACK_FLOOR:
            floor_failures.append(
                f"✖ found only {len(result.packs)} packs, below the recorded "
                f"floor of {PACK_FLOOR}; the scan silently narrowed or the "
                "floor needs a deliberate update."
            )
        if primitive_count < PRIMITIVE_FLOOR:
            floor_failures.append(
                f"✖ found only {primitive_count} primitives, below the recorded "
                f"floor of {PRIMITIVE_FLOOR}; the scan silently narrowed or the "
                "floor needs a deliberate update."
            )
        if floor_failures:
            print("\n".join(floor_failures), file=sys.stderr)
            return 1

    if result.findings:
        for finding in result.findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        print(
            f"✖ lint-pack-dependency-declaration: {len(result.findings)} "
            "violation(s)",
            file=sys.stderr,
        )
        return 1

    print(
        "ok   [pack-dependency-declaration] "
        f"({len(result.packs)} packs, {primitive_count} primitives)"
    )
    print("✓ lint-pack-dependency-declaration: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
