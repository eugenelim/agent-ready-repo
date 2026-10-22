"""Write a status input of exactly 4,194,304 bytes that passes every readiness check.

Usage: python ac0042_generate_max_status.py <repo root> <output file> [--distinct-codes]

The object is a base status whose ``canonical.blocked`` list repeats one blocked entry per
spec path of the repository (``docs/specs/<slug>/spec.md``), round after round, until the
next entry would push the text past the limit.  Trailing spaces, which the input checks
allow, bring it to exactly 4,194,304 bytes.  A path that occurs more than once in the
blocked list is one record with its repeated codes removed, so every entry stays valid.

With ``--distinct-codes`` every entry names the first spec path and carries its own valid
code, so one loaded record holds tens of thousands of distinct codes: the case that would
show a projection whose cost grows faster than its input.
"""

from __future__ import annotations

import json
import pathlib
import sys

LIMIT = 4_194_304
NEXT_ACTION = "Complete or explicitly revise the dependency."


def entry(path: str, code: str = "unsatisfied_dependency") -> dict[str, object]:
    finding = {"code": code, "dispatchable": False, "next_action": NEXT_ACTION}
    return {"path": path, "dispatchable": False, "findings": [finding]}


def main(root: pathlib.Path, out: pathlib.Path, distinct: bool = False) -> None:
    paths = sorted(p.relative_to(root).as_posix() for p in (root / "docs/specs").glob("*/spec.md"))
    if not paths:
        raise SystemExit("no spec paths found")
    base = {
        "schema_version": 1, "mode": "status", "workspace_present": True, "workspace_root": ".",
        "canonical": {"performed": True, "bounded": True, "findings": [],
                      "ready": [], "active": [], "blocked": []},
    }
    head = json.dumps(base, separators=(",", ":"))
    # Everything up to the empty blocked list, then the entries, then the closing "]}}".
    prefix, suffix = head[: head.index('"blocked":[') + len('"blocked":[')], "]}}"
    pieces: list[str] = []
    size = len(prefix) + len(suffix)
    i = 0
    while True:
        one = entry(paths[0], f"c{i}") if distinct else entry(paths[i % len(paths)])
        text = json.dumps(one, separators=(",", ":"))
        extra = len(text) + (1 if pieces else 0)
        if size + extra > LIMIT:
            break
        pieces.append(text)
        size += extra
        i += 1
    body = prefix + ",".join(pieces) + suffix
    data = body.encode("utf-8") + b" " * (LIMIT - len(body.encode("utf-8")))
    out.write_bytes(data)
    print(f"entries={len(pieces)} distinct_paths={len(paths)} bytes={len(data)}")


if __name__ == "__main__":
    distinct = "--distinct-codes" in sys.argv[3:]
    main(pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]), distinct)
