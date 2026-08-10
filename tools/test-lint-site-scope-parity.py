#!/usr/bin/env python3
"""Construction tests for tools/lint-site-scope-parity.py.

Runs under the gate chain, not pytest — `make build-check` runs no pytest.

Every case builds a synthetic tree under a temp root. The real `web/` tree is
not mutated: it is a projected-adjacent surface other gates watch, and a
mutation there could exit non-zero for a reason that has nothing to do with
this lint.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "lint_site_scope_parity", Path(__file__).parent / "lint-site-scope-parity.py"
)
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL {name}: {detail}")


def _tree(root: Path, slug: str, *, version: str | None, scopes: list[str],
          page_says: str | None) -> None:
    d = root / "packs" / slug
    d.mkdir(parents=True)
    body = f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
    if version is not None:
        body += f'\n[pack.adapter-contract]\nversion = "{version}"\n'
    rendered = ", ".join(f'"{s}"' for s in scopes)
    body += f'\n[pack.install]\ndefault-scope = "repo"\nallowed-scopes = [{rendered}]\n'
    (d / "pack.toml").write_text(body, encoding="utf-8", newline="\n")
    pages = root / "web" / "src" / "content" / "packs"
    pages.mkdir(parents=True, exist_ok=True)
    if page_says is not None:
        (pages / f"{slug}.md").write_text(
            f"---\nname: {slug}\npluginInstallable: {page_says}\nscope: repo\n---\n",
            encoding="utf-8", newline="\n",
        )


def main() -> int:
    print("test-lint-site-scope-parity:")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _tree(root, "agree-true", version="0.3", scopes=["repo", "user"], page_says="true")
        _tree(root, "agree-false", version="0.3", scopes=["repo"], page_says="false")
        _check("agreeing pages pass", lint.check(root) == [], f"got {lint.check(root)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # THE mutation: the page claims the plugin route for a repo-only pack.
        _tree(root, "drifted", version="0.3", scopes=["repo"], page_says="true")
        out = lint.check(root)
        _check("page claiming plugin route for a repo-only pack fails",
               len(out) == 1 and "drifted" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # `scope` mirrors default-scope, so gating on it would hide this pack.
        # The parity gate must read allowed-scopes instead.
        _tree(root, "default-repo-allows-user", version="0.3",
              scopes=["repo", "user"], page_says="true")
        _check("default-scope repo + allowed-scopes user is plugin-installable",
               lint.check(root) == [], f"got {lint.check(root)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _tree(root, "orphan", version="0.3", scopes=["repo", "user"], page_says=None)
        out = lint.check(root)
        _check("pack with no site page fails", len(out) == 1 and "orphan" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A missing content directory must not read as "nothing to check":
        # `check-site-plugin-offers` drops its own existence guard because
        # this gate promises a page per pack.
        _tree(root, "somepack", version="0.3", scopes=["repo", "user"], page_says="true")
        shutil.rmtree(root / "web")
        out = lint.check(root)
        _check("a missing site content directory fails rather than passing",
               len(out) == 1 and "is missing" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # ...but a checkout with neither site nor packs is genuinely nothing.
        _check("no site and no packs is vacuously fine", lint.check(root) == [],
               f"got {lint.check(root)}")

    if FAILURES:
        print(f"test-lint-site-scope-parity: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-site-scope-parity: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
