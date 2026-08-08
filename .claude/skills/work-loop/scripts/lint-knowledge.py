#!/usr/bin/env python3
"""Lints docs/knowledge/patterns.jsonl. Every non-empty line must be a
JSON object with the required keys, the right `kind` value, and an
id that matches the K-NNNN format. Exit non-zero on any error.

The empty file is valid (no learnings yet).

Fixture mode: pass a path argument to lint a different file (used by the
self-test). An argument rather than an environment variable on purpose: the
hook is for a caller that is already invoking this script deliberately, and an
env var flowing into a filesystem target is an unvalidated external-control
path (CWE-22 / CWE-73) that the repo's SAST rule rightly refuses. The argument
is resolved before the chdir below, so a relative path means what the caller
meant by it.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path.cwd()


REQUIRED_KEYS = {"id", "kind", "scope", "title", "body", "source"}
OPTIONAL_KEYS = {"tier"}
ALLOWED_KINDS = {"pattern", "gotcha", "antipattern"}
ALLOWED_TIERS = {"invariant", "observation"}
ID_PATTERN = re.compile(r"^K-\d{4,}$")

# Entries must be raw UTF-8, not `\uXXXX`-escaped. Both forms are valid JSON, so
# an author reaching for json.dumps' default (ensure_ascii=True) silently drifts
# the file's encoding — and for a non-BMP character the default emits a
# *surrogate pair* (😀 → 😀), which is valid JSON but not a valid
# TOML/YAML scalar downstream. `append-knowledge.py` writes the correct form;
# this rule catches everything else.
# `(?<!\\)((?:\\\\)*\\)` matches the backslash run without backtracking. The
# obvious `(\\+)u` form is quadratic — it retries the greedy run at every start
# offset, and this linter runs unfiltered over a repo file in CI, so a long
# adversarial line would hang the gate that exists to reject it (CWE-1333).
_ESCAPE_RE = re.compile(r"(?<!\\)((?:\\\\)*\\)u([0-9a-fA-F]{4})")
# Belt and braces: refuse to regex a pathological line at all.
_MAX_LINE = 8192
# `gratuitous_escapes` exempts these so an entry carrying one gets a single
# clear error rather than two: the decoded pass refuses the character itself, in
# both spellings. The literal form also breaks `str.splitlines()`, which is how
# both this linter and session-start.py read the file.
_LINE_BREAKERS = frozenset({0x85, 0x2028, 0x2029})
# The C0 characters JSON actually needs an escape for. The rest of C0 has no
# business in a knowledge entry in *either* form — the writer refuses a
# literal ESC because session-start replays it as an ANSI sequence, so the
# gate must refuse the escaped spelling too or the hand-edit path is open.
# No C0 character is permitted in a field value at all — `field_problems`
# refuses category `Cc` on the decoded string, which covers the literal and the
# escaped spelling together. So there is no "JSON needs this escape" carve-out
# to make: an escaped C0 is refused by the decoded pass, and the escape rule
# below only has to exempt the three line separators, whose escaped form is the
# one representation that survives `splitlines()`.
# Zero-width carriers. The rule is **default-ignorable code point**, not any one
# Unicode category — a first version refused only `Cf` and was bypassed by
# variation selectors, which are `Mn`. Framing it this way means the next
# carrier class is covered by construction rather than by another round.
#
# ZWJ / ZWNJ and the two emoji presentation selectors are the legitimate
# exceptions: they shape neighbouring characters rather than carry payload.
_ALLOWED_FORMAT_CHARS = frozenset("\u200c\u200d\ufe0e\ufe0f")
# All four allowed characters count toward a run. Excluding the presentation
# selectors reopened the channel this rule exists to close: an alternating
# VS15/VS16 or ZWJ/VS16 sequence is then invisible to every check, and 80 of
# them landed in a real file during review. The threshold is what separates
# payload from text — measured across six real sequences, emoji cap at two
# adjacent (heart-on-fire is VS16 then ZWJ; so do the flag and bouncing-ball
# forms), while a usable alphabet needs many more.
_RUN_CHARS = _ALLOWED_FORMAT_CHARS
_MAX_ADJACENT_INVISIBLE = 2
# Unicode's Default_Ignorable_Code_Point property, verbatim (DerivedCoreProperties).
# Hand-listed because `unicodedata` does not expose the property, and enumerated
# rather than sampled because sampling is what failed twice: the first version
# keyed on `Cf` and was bypassed by the variation selectors (Mn), the second
# added those five ranges and was bypassed by the Mongolian free variation
# selectors — the identical construct in a different block. The unassigned
# ranges are included deliberately: a code point with no glyph today is still a
# carrier, and future assignments inherit the property.
_HIDDEN_RANGES = (
    (0x00AD, 0x00AD),    # soft hyphen
    (0x034F, 0x034F),    # combining grapheme joiner
    (0x061C, 0x061C),    # Arabic letter mark
    (0x115F, 0x1160),    # Hangul choseong/jungseong fillers
    (0x17B4, 0x17B5),    # Khmer inherent vowels
    (0x180B, 0x180F),    # Mongolian free variation selectors + vowel separator
    (0x200B, 0x200F),    # zero-width space .. RTL mark
    (0x202A, 0x202E),    # bidi embedding/override
    (0x2060, 0x206F),    # word joiner .. nominal digit shapes (incl. unassigned 2065)
    (0x3164, 0x3164),    # Hangul filler
    (0xFE00, 0xFE0F),    # variation selectors 1-16
    (0xFEFF, 0xFEFF),    # zero-width no-break space / BOM
    (0xFFA0, 0xFFA0),    # halfwidth Hangul filler
    (0xFFF0, 0xFFF8),    # unassigned, default-ignorable
    (0x1BCA0, 0x1BCA3),  # shorthand format controls
    (0x1D173, 0x1D17A),  # musical format controls
    (0xE0000, 0xE0FFF),  # tag block + variation selector supplement + unassigned
)

# A run cap bounds *adjacency*; it does not bound *volume*. Interleaving two
# legal joiners after every visible character stays under any adjacency limit
# and still carries an arbitrary instruction — 608 invisible characters hid a
# 76-character payload inside ordinary-looking advice during review. So cap the
# total too: 2% of the field, floor 4, which passes every emoji sequence
# measured and every realistic body.
_INVISIBLE_BUDGET_DIVISOR = 50  # i.e. 2% of the field
_MIN_INVISIBLE_ALLOWANCE = 4


def invisible_budget(value: str) -> int:
    return max(_MIN_INVISIBLE_ALLOWANCE, len(value) // _INVISIBLE_BUDGET_DIVISOR)


def is_hidden_char(ch: str) -> bool:
    """True when *ch* renders as nothing and can therefore carry payload.

    Shared with `append-knowledge.py`, which imports this module — one
    definition, so the writer and the gate cannot disagree about what is
    invisible.
    """
    if ch in _ALLOWED_FORMAT_CHARS:
        return False
    if unicodedata.category(ch) == "Cf":
        return True
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _HIDDEN_RANGES)


def gratuitous_escapes(raw: str) -> list[tuple[str, str]]:
    """Return (escape, character) for each `\\uXXXX` that should have been literal.

    The pattern's lookbehind guarantees the matched backslash run is odd-length,
    so the match is a real escape rather than a literal `\\u` in body text.
    """
    found: list[tuple[str, str]] = []
    for m in _ESCAPE_RE.finditer(raw):
        cp = int(m.group(2), 16)
        # Skip anything the decoded pass refuses outright. Otherwise an escaped
        # C0 fires twice, and the escape rule's advice — "write it literally" —
        # points at a form that is also refused.
        if cp in _LINE_BREAKERS or unicodedata.category(chr(cp)) == "Cc":
            continue
        found.append((f"\\u{m.group(2)}", chr(cp)))
    return found


def field_problems(value: str) -> list[str]:
    r"""Every per-character rule, applied to a *decoded* field value.

    Decoded on purpose: `json.loads` has already collapsed `\u001b` and a
    literal ESC to the same character, so one pass here covers both spellings.
    Checking the raw line instead is how the gate ended up accepting control
    characters the writer refused — the escape regex only ever saw the
    `\uXXXX` form, and the short escapes (`\b \t \n \f \r`) were never
    inspected at all.
    """
    problems: list[str] = []
    run = invisible = 0
    for ch in value:
        cp = ord(ch)
        if unicodedata.category(ch) == "Cc":
            problems.append(f"control character U+{cp:04X}")
        elif is_hidden_char(ch):
            problems.append(f"invisible character U+{cp:04X} "
                            f"({unicodedata.name(ch, 'unnamed')})")
        if cp in _LINE_BREAKERS:
            # U+0085 is Cc and caught above; U+2028 is Zl and U+2029 is Zp, so
            # neither falls under any other rule. They have to be named here or
            # the *escaped* spelling survives the round trip intact and forges a
            # line into the block session-start replays — a closed
            # `=== end knowledge ===` followed by an instruction reads as
            # genuine to any line-oriented consumer. The writer already refuses
            # all three; this is what makes that true of the gate as well.
            problems.append(f"line separator U+{cp:04X}")
        if 0xD800 <= cp <= 0xDFFF:
            problems.append(f"lone surrogate U+{cp:04X}")
        if ch in _RUN_CHARS:
            run += 1
            invisible += 1
            if run == _MAX_ADJACENT_INVISIBLE + 1:
                problems.append(f"run of {run} adjacent zero-width characters")
        else:
            run = 0
    budget = invisible_budget(value)
    if invisible > budget:
        problems.append(f"{invisible} zero-width characters in {len(value)} "
                        f"(budget {budget}) — adjacency alone does not bound volume")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    # Resolve against the caller's cwd *before* chdir, so a relative override
    # points where the caller meant rather than at the repo root.
    override = pathlib.Path(args[0]).expanduser().resolve() if args else None
    os.chdir(_repo_root())
    knowledge_file = override or pathlib.Path("docs/knowledge/patterns.jsonl")
    error_count = 0

    def err(line_no: int, msg: str) -> None:
        nonlocal error_count
        print(f"✖ {knowledge_file}:{line_no}: {msg}", file=sys.stderr)
        error_count += 1

    if not knowledge_file.exists():
        print(
            f"⚠ {knowledge_file}: file does not exist — knowledge base not initialized",
            file=sys.stderr,
        )
        return 1

    seen_ids: dict[str, int] = {}

    # A gate that tracebacks on its own input is not a gate: report the
    # undecodable file as the error it is, so the caller (and the writer that
    # shells out to this script) gets a message instead of a stack trace.
    try:
        content = knowledge_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(
            f"✖ {knowledge_file}: not valid UTF-8 — byte 0x{exc.object[exc.start]:02x} "
            f"at position {exc.start} ({exc.reason})",
            file=sys.stderr,
        )
        return 1

    for line_no, raw in enumerate(content.splitlines(), start=1):
        if not raw.strip():
            continue

        # Checked on the raw line, before parsing: json.loads decodes the escape
        # away, so the drift is invisible to any check on the parsed object.
        # Reported through err() — a lone surrogate cannot be printed to this
        # script's stdout, which is configured errors="strict".
        if len(raw) > _MAX_LINE:
            err(line_no, f"line is {len(raw)} characters; the limit is {_MAX_LINE}")
            continue

        for escape, char in gratuitous_escapes(raw):
            err(
                line_no,
                f"{escape} escapes a character that should be written literally "
                f"({char!r}) — write raw UTF-8 "
                f"(json.dumps(..., ensure_ascii=False)), or append via "
                f"append-knowledge.py",
            )

        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            err(line_no, f"not valid JSON: {exc.msg}")
            continue

        if not isinstance(entry, dict):
            err(line_no, "must be a JSON object, not a list or scalar")
            continue

        keys = set(entry)
        missing = REQUIRED_KEYS - keys
        if missing:
            err(line_no, f"missing required keys: {sorted(missing)}")

        extra = keys - REQUIRED_KEYS - OPTIONAL_KEYS
        if extra:
            err(
                line_no,
                f"unknown keys: {sorted(extra)} "
                f"(allowed: {sorted(REQUIRED_KEYS | OPTIONAL_KEYS)})",
            )

        # Run remaining content checks against whatever fields are present
        # — surface every problem on the line in one lint pass rather than
        # making the author re-run the linter per fix.

        # Every value is content: session-start replays `id` and `kind` into the
        # session block alongside the prose. A non-string slipped past every
        # `isinstance(...) and ...` branch below without firing an error, and
        # carried 80 invisible characters through the gate in a list and a dict.
        for key, value in entry.items():
            if not isinstance(value, str):
                err(line_no, f"{key!r} must be a string, got "
                             f"{type(value).__name__!r}")
                continue
            for problem in field_problems(value):
                err(
                    line_no,
                    f"{key!r} contains a {problem} — entries are replayed "
                    f"verbatim into every session, so these are refused; "
                    f"write entries with append-knowledge.py",
                )

        id_val = entry.get("id")
        if isinstance(id_val, str) and not ID_PATTERN.match(id_val):
            err(line_no, f"id {id_val!r} must match ^K-\\d{{4,}}$ (e.g. K-0001)")
        elif isinstance(id_val, str):
            if id_val in seen_ids:
                err(
                    line_no,
                    f"duplicate id {id_val!r} "
                    f"(first seen on line {seen_ids[id_val]})",
                )
            else:
                seen_ids[id_val] = line_no

        kind_val = entry.get("kind")
        if isinstance(kind_val, str) and kind_val not in ALLOWED_KINDS:
            err(
                line_no,
                f"kind {kind_val!r} must be one of {sorted(ALLOWED_KINDS)}",
            )

        for k in ("scope", "title", "body", "source"):
            if k not in entry:
                continue  # missing-key error already fired above
            v = entry[k]
            if not isinstance(v, str) or not v.strip():
                err(line_no, f"{k!r} must be a non-empty string")
                continue
            if k == "scope":
                segments = [g.strip() for g in v.split(",") if g.strip()]
                if not segments:
                    err(line_no, "'scope' must contain at least one non-empty glob segment")

        if "tier" in entry:
            tier_val = entry["tier"]
            if not isinstance(tier_val, str):
                err(line_no, f"tier must be a string, got {type(tier_val).__name__!r}")
            elif tier_val not in ALLOWED_TIERS:
                err(
                    line_no,
                    f"tier {tier_val!r} must be one of {sorted(ALLOWED_TIERS)}"
                    f" (or omitted, defaulting to 'observation')",
                )

    print(f"\nKnowledge entries checked: {len(seen_ids)}.")
    if error_count:
        print(
            f"Knowledge lint: failed ({error_count} error(s)).",
            file=sys.stderr,
        )
        return 1
    print("Knowledge lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
