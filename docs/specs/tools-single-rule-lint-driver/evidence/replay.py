#!/usr/bin/env python3
"""Replay the T1 corpus against the current tree and diff it byte-for-byte."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

SPD = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("capture", SPD / "capture.py")
cap = importlib.util.module_from_spec(spec)
sys.argv = ["capture", sys.argv[1] if len(sys.argv) > 1 else "."]
spec.loader.exec_module(cap)
import fixtures  # noqa: E402

REPO = Path(sys.argv[1]).resolve()
before = json.loads((SPD / "corpus-before.json").read_text())

# No per-rule filter on purpose: sys.argv is rewritten above for capture.py,
# and replaying all 48 every time also catches a migration that regresses a
# rule other than the one just touched.
bad, checked = [], 0
for rule in cap.RULES:
    now = {"clean": cap.invoke(rule, REPO, REPO, clean=True)}
    for mode, present in (("empty", True), ("absent", False)):
        now[mode] = cap.invoke(rule, cap.fixture_root(rule, present), REPO)
    root = cap.fixture_root(rule, True)
    fixtures.build(rule, root)
    now["violation"] = cap.invoke(rule, root, REPO)

    for mode, got in now.items():
        want = before[rule][mode]
        checked += 1
        for field in ("exit", "stdout", "stderr"):
            if got[field] != want[field]:
                bad.append((rule, mode, field, want[field], got[field]))

# `lint-nosec-form` and `lint-nosemgrep-form` end a clean run with a repo-wide
# count of the files they scanned, so ANY commit anywhere that adds a tracked
# file moves that number — including a rebase onto a moved main. Hard-coding
# the expected integers would make this artifact self-invalidating, so a
# difference that is ONLY that integer is reported separately from a behaviour
# change. The substitution is deliberately narrow: it rewrites the digits in
# that one phrase and nothing else, so any other byte that moves still fails.
_COUNT_PHRASE = re.compile(r"\b\d+ (tracked|UTF-8 text) file\(s\)")


def _count_normalised(text: str) -> str:
    return _COUNT_PHRASE.sub("<N> \\1 file(s)", text)


behaviour, counts = [], []
for entry in bad:
    _rule, _mode, _field, want, got = entry
    target = counts if (
        isinstance(want, str)
        and _COUNT_PHRASE.search(want)
        and _count_normalised(want) == _count_normalised(got)
    ) else behaviour
    target.append(entry)

print(f"replayed {checked} case(s)")
for rule, mode, field, want, got in counts:
    w = _COUNT_PHRASE.search(want).group(0)
    g = _COUNT_PHRASE.search(got).group(0)
    print(f"  count-only: {rule} [{mode}] {field}: {w} -> {g}")
if not behaviour:
    print("IDENTICAL — no behavioural difference from the pre-refactor capture"
          f" ({len(counts)} repo-wide count line(s) moved, which any added"
          " tracked file does)")
    sys.exit(0)
for rule, mode, field, want, got in behaviour:
    print(f"\n✖ {rule} [{mode}] {field}")
    print(f"   want: {want!r}"[:400])
    print(f"   got : {got!r}"[:400])
sys.exit(1)
