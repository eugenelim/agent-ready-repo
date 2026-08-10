#!/usr/bin/env python3
"""Sibling self-test for `tools/check-site-plugin-offers.py`.

Every other gate this spec added ships one of these; this was the exception,
and it is the gate that reads *rendered HTML* — the one place a silently
disabled check looks identical to a clean run.

Drives the real `main()` over synthetic build trees. Each case is a state the
gate must call, in both directions: an offer for a repo-only pack, a missing
offer for a user-capable one, and a build directory that is not there at all.

Usage:
    python3 tools/test-check-site-plugin-offers.py
"""

from __future__ import annotations

import contextlib
import importlib.util as _ilu
import io
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_spec = _ilu.spec_from_file_location(
    "check_site_plugin_offers", Path(__file__).parent / "check-site-plugin-offers.py"
)
gate = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(gate)

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _pack(root: Path, slug: str, *, user: bool) -> None:
    d = root / "packs" / slug
    d.mkdir(parents=True)
    scopes = '["repo", "user"]' if user else '["repo"]'
    (d / "pack.toml").write_text(
        f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "0.3"\n'
        f"[pack.install]\nallowed-scopes = {scopes}\n",
        encoding="utf-8", newline="\n")


def _page(build: Path, slug: str, *, offers: str | None) -> None:
    p = build / "packs" / f"{slug}.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = f"<pre>claude plugin install {offers}@agent-ready-repo</pre>" if offers else "<p>no offer</p>"
    p.write_text(f"<html><body>{body}</body></html>", encoding="utf-8", newline="\n")


def _run(root: Path, build: Path) -> tuple[int, str]:
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = gate.main(["--root", str(root), "--build-dir", str(build)])
    return rc, err.getvalue()


def main() -> int:
    print("test-check-site-plugin-offers:")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build = root / "build"
        _pack(root, "wide", user=True)
        _page(build, "wide", offers="wide")
        rc, err = _run(root, build)
        _check("a user-capable pack offered on its page passes", rc == 0, f"rc={rc} {err}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build = root / "build"
        _pack(root, "wide", user=True)
        _pack(root, "narrow", user=False)
        _page(build, "wide", offers="wide")
        _page(build, "narrow", offers="narrow")
        rc, err = _run(root, build)
        _check("an offer for a repo-only pack fails",
               rc == 1 and "narrow is not" in err, f"rc={rc} {err}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build = root / "build"
        _pack(root, "wide", user=True)
        # The conditional inverted rather than removed: the page renders, but
        # the block is gone. A one-directional check would call this clean.
        _page(build, "wide", offers=None)
        rc, err = _run(root, build)
        _check("a missing offer for a user-capable pack fails",
               rc == 1 and "offers no plugin install command" in err, f"rc={rc} {err}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root, "wide", user=True)
        rc, err = _run(root, root / "build")
        _check("an absent build dir fails rather than passing vacuously",
               rc == 1 and "no build dir" in err, f"rc={rc} {err}")

    with tempfile.TemporaryDirectory() as tmp:
        # An empty build tree is the shape a silently-disabled site build
        # leaves behind: no offers found, nothing to compare. It must not read
        # as `ok — 0 pack(s) offered`.
        root = Path(tmp)
        build = root / "build"
        _pack(root, "wide", user=True)
        build.mkdir()
        rc, err = _run(root, build)
        _check("an empty build tree fails rather than reporting zero offers",
               rc == 1, f"rc={rc} {err}")

    if FAILURES:
        print(f"test-check-site-plugin-offers: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-check-site-plugin-offers: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
