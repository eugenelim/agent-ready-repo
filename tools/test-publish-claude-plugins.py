#!/usr/bin/env python3
"""Construction tests for tools/catalogue/publish_claude_plugins.py.

That script's `_assert_membership` is the only runtime check standing between a
`git push` and a public marketplace: the publish job triggers on `push: main`
with `contents: write` and declares no `needs:` on the build-check job, so
nothing else in CI gates it. It shipped untested.

Every case builds synthetic `packs/` and `dist/` trees under a temp root, so
none of the three refusals is confused with a real-repo condition.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "publish_claude_plugins",
    Path(__file__).parent / "catalogue" / "publish_claude_plugins.py",
)
pub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pub)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _source_pack(root: Path, slug: str, *, user: bool) -> None:
    d = root / "packs" / slug
    (d / ".claude-plugin").mkdir(parents=True)
    scopes = '["repo", "user"]' if user else '["repo"]'
    (d / "pack.toml").write_text(
        f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "0.3"\n'
        f'[pack.install]\ndefault-scope = "repo"\nallowed-scopes = {scopes}\n',
        encoding="utf-8", newline="\n")
    (d / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": slug, "version": "1.0.0"}), encoding="utf-8", newline="\n")


def _root_marketplace(root: Path, names) -> None:
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": n} for n in names]}),
        encoding="utf-8", newline="\n")


def _in(root: Path, fn, *args):
    """Run `fn` with cwd at `root` — the script resolves relative paths."""
    prev = Path.cwd()
    os.chdir(root)
    try:
        return fn(*args)
    finally:
        os.chdir(prev)


def _refuses(root: Path, published_dirs, marketplace_names) -> str | None:
    try:
        _in(root, pub._assert_membership, set(published_dirs), set(marketplace_names))
    except SystemExit as exc:
        return str(exc)
    return None


def main() -> int:
    print("test-publish-claude-plugins:")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        _root_marketplace(root, ["userpack"])
        _check("a consistent set passes",
               _refuses(root, ["userpack"], ["userpack"]) is None,
               f"got {_refuses(root, ['userpack'], ['userpack'])}")

        # Refusal 1: a stale dist/ directory for a pack the source no longer
        # publishes. `make build` has no `clean` dependency, so this survives.
        msg = _refuses(root, ["userpack", "gonepack"], ["userpack", "gonepack"])
        _check("a stale/unpublishable directory refuses",
               msg is not None and "gonepack" in msg, f"got {msg}")

        # Refusal 1b: the pack is *present* in the source and simply repo-only.
        # Refusal 1 is driven by an absent pack, so it survives deleting the
        # scope branch in `_publishable_from_source`; this case does not.
        _source_pack(root, "repopack", user=False)
        msg = _refuses(root, ["userpack", "repopack"], ["userpack", "repopack"])
        _check("a present-but-repo-only pack refuses on scope",
               msg is not None and "repopack" in msg, f"got {msg}")

        # Refusal 2: an entry whose directory is absent — a dangling fetch for
        # every adopter, which is the defect the spec opens on.
        msg = _refuses(root, ["userpack"], ["userpack", "ghost"])
        _check("a dangling marketplace entry refuses",
               msg is not None and "ghost" in msg, f"got {msg}")

        # Refusal 3: a published directory nobody lists.
        msg = _refuses(root, ["userpack", "orphan"], ["userpack"])
        _check("an unlisted published directory refuses",
               msg is not None and "orphan" in msg, f"got {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        # The root marketplace must not advertise what the branch does not carry.
        _root_marketplace(root, ["userpack", "notonbranch"])
        msg = _refuses(root, ["userpack"], ["userpack"])
        _check("a root entry the branch lacks refuses",
               msg is not None and "notonbranch" in msg, f"got {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        _source_pack(root, "catalogue-curation", user=True)
        _root_marketplace(root, ["userpack"])
        # EXCLUDE is applied first and is exempt: catalogue-curation is
        # operator-only, a different reason from being repo-only, and folding
        # the two would re-publish it if its scopes were ever widened.
        _check("the operator-only exclusion is exempt from the refusals",
               _refuses(root, ["userpack"], ["userpack"]) is None,
               "EXCLUDE must be applied before the membership assertion")

    _check("catalogue-curation is still the only name exclusion",
           {"catalogue-curation"} == pub.EXCLUDE, f"got {pub.EXCLUDE}")

    # The refusals above drive `_assert_membership` directly, so deleting its
    # single call from `main()` leaves every one of them green — and that call
    # is the only runtime check between `git push` and a public marketplace.
    # Pin the call site structurally, not by substring: a commented-out call
    # or one inside a dead branch must not read as wired.
    src = Path(pub.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    main_fn = next((n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    called = main_fn is not None and any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "_assert_membership"
        for n in ast.walk(main_fn)
    )
    _check("main() actually calls _assert_membership", called,
           "the membership refusal is defined but never reached — publishing "
           "would push whatever the build produced")

    if FAILURES:
        print(f"test-publish-claude-plugins: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-publish-claude-plugins: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
