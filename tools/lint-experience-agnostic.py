#!/usr/bin/env python3
"""Framework-agnosticism lint for the `experience-design` pack (RFC-0033).

The `experience-design` pack ships portable design *method*, never a stack or a
values cheat-sheet (RFC-0033 Guardrails A and B; the charter's "not a
framework that picks your tech stack"). This lint is the mechanical floor
under that promise — the RFC-0007 grep-enforcement pattern, scoped to one
pack. It walks every Markdown file under `packs/experience-design/` and fails on
any **stack token** (UI-framework name, styling-language syntax, animation
library, ARIA role) or **values-table shape** (color literal — hex, rgb(),
hsl(); a dimension/duration literal — px/ms/rem/em/pt/vh/vw and decimal
seconds; a contrast/scale ratio like `4.5:1`; a named easing curve) — the
things that turn portable method into a single stack's cheat-sheet.

It is **catalogue-governance tooling under `tools/`, not a pack primitive**
(the pack stays pure markdown) and is deliberately **not** promoted to a
repo-wide convention — that would be a separate RFC (RFC-0033 Follow-on).

Scope: Markdown only. `pack.toml` / `plugin.json` are not design content and
are not scanned. The patterns are tuned to catch a real leak (a CSS snippet,
a reprinted palette, an ARIA role used as the answer) without tripping on
legitimate method prose — so framework names match case-sensitively as the
proper nouns they are (the adjective "angular" is fine; the framework
"Angular" is not), and a hex match requires at least one digit so word-slugs
like `#facade` don't false-positive.

Exit codes:
  0 — clean: no stack token or values-table shape found.
  1 — at least one violation found (printed with `::error::` for CI).
  2 — tool error (the scan root does not exist).

Self-test / fixture mode: point the scan at a different tree with
  EXPERIENCE_ROOT=/path/to/tree python3 tools/lint-experience-agnostic.py
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except OSError:
        pass
    return pathlib.Path(__file__).resolve().parent.parent


# Each rule is (label, compiled-pattern). A line matching any pattern is a
# violation. Patterns are deliberately narrow: every one names a token that
# has no place in framework-agnostic design *method* — it only appears when
# a specific stack or a literal value has leaked in.
def _rules() -> list[tuple[str, re.Pattern[str]]]:
    return [
        # UI-framework names — proper nouns, matched case-sensitively so the
        # design adjective "angular" and the verb "react" stay legal.
        (
            "UI-framework name",
            re.compile(
                r"\b(React|Vue|Angular|Svelte|Tailwind|Bootstrap|Next\.js|Nuxt|"
                r"SwiftUI|Jetpack Compose|Flutter)\b"
            ),
        ),
        # Styling-language / CSS surface — the language itself, the media
        # query, the reduced-motion *feature* (the principle "reduced-motion"
        # is fine), and unambiguous grid/flex property syntax. Bare "grid" /
        # "flex" as layout *concepts* are intentionally not matched.
        (
            "styling-language / CSS syntax",
            re.compile(
                r"\bCSS\b|@media|prefers-reduced-motion|"
                r"display\s*:\s*(grid|flex)|"
                r"\b(grid-template(-columns|-rows)?|grid-auto-\w+"
                r"|flex-direction|flex-grow|flex-basis|justify-content"
                r"|align-items|align-content)\b"
            ),
        ),
        # ARIA — the design skills speak orientation/wayfinding as concepts,
        # never platform roles (Guardrail B).
        (
            "ARIA role / attribute",
            re.compile(r"\bARIA\b|\baria-[a-z]+\b|\brole\s*=\s*[\"']"),
        ),
        # Animation libraries — motion is a *principle* here, never a library.
        (
            "animation library",
            re.compile(
                r"Framer Motion|\bframer-motion\b|\bGSAP\b|\breact-spring\b"
                r"|\banime\.js\b|\banimate\.css\b"
            ),
        ),
        # Color literals — a reprinted palette, in any common notation.
        # Digit-bearing hex (#1a2b3c) requires a digit so all-letter word
        # slugs (#facade, #abc) don't false-positive; a separate rule catches
        # the all-letter greyscale shorthands (#fff, #ccc) that the digit-guard
        # would otherwise miss. rgb()/hsl() functional notations are
        # unambiguous — they never appear in agnostic prose.
        (
            "color literal",
            re.compile(
                r"#(?=[0-9a-fA-F]*[0-9])[0-9a-fA-F]{3}\b"
                r"|#(?=[0-9a-fA-F]*[0-9])[0-9a-fA-F]{6}\b"
                r"|#([0-9a-fA-F])\1{2}\b"
                r"|\brgba?\s*\(|\bhsla?\s*\("
            ),
        ),
        # Dimension / duration literals — a reprinted spacing / type / timing
        # scale. A digit followed by a CSS unit, optionally across a single
        # space (`400 ms` is as much a reprinted value as `400ms` — a designer
        # who wrote "respond within 400 ms" reprinted the number either way).
        # `s` (seconds) is matched only with a decimal point (0.2s / 0.2 s) so
        # decades ("the 1990s") and bare counts don't false-positive; `%` is
        # deliberately omitted because plain prose ("80% of users") uses it
        # constantly.
        (
            "dimension / duration literal",
            re.compile(
                r"\b\d+(\.\d+)?\s?(px|ms|rem|em|pt|vh|vw|vmin|vmax)\b"
                r"|\b\d+\.\d+\s?s\b"
            ),
        ),
        # Contrast / scale ratios reprinted as a literal — the value the docs
        # say most often to *point to WCAG* for, never to print (e.g. 4.5:1,
        # 3:1). Matches an `N:1` shape; aspect ratios like 16:9 don't end in 1.
        (
            "ratio literal",
            re.compile(r"\b\d+(\.\d+)?\s*:\s*1\b"),
        ),
        # Named easing curves — a reprinted motion-curve table.
        (
            "named easing curve",
            re.compile(r"\bcubic-bezier\b|\bease-in-out\b|\bease-in\b|\bease-out\b"),
        ),
    ]


def _scan_root() -> pathlib.Path:
    override = os.environ.get("EXPERIENCE_ROOT")
    if override:
        return pathlib.Path(override)
    return _repo_root() / "packs" / "experience-design"


def main() -> int:
    root = _scan_root()
    if not root.exists():
        print(
            f"::error::experience agnosticism lint: scan root {root} does not exist",
            file=sys.stderr,
        )
        return 2

    rules = _rules()
    violations: list[str] = []

    for md in sorted(root.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:  # pragma: no cover
            print(f"::error::could not read {md}: {exc}", file=sys.stderr)
            return 2
        rel = md.relative_to(root) if md.is_relative_to(root) else md
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, pattern in rules:
                m = pattern.search(line)
                if m:
                    violations.append(
                        f"{rel}:{lineno}: {label}: '{m.group(0)}'  "
                        f"— experience ships portable method, not a stack or a "
                        f"values table (RFC-0033)"
                    )

    if violations:
        for v in violations:
            print(f"::error::{v}", file=sys.stderr)
        print(
            f"\n✖ experience agnosticism lint: {len(violations)} "
            f"violation(s) in {root}",
            file=sys.stderr,
        )
        return 1

    print(f"✓ experience agnosticism lint: clean ({root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
