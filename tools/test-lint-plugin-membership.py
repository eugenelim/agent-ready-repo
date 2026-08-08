#!/usr/bin/env python3
"""Construction tests for tools/lint-plugin-membership.py.

Runs under the gate chain, not pytest — `make build-check` runs no pytest.

The load-bearing case is `test_extra_entry_fails`: it is the mutation AC9
requires, and it is chosen so the **projected-path drift gate cannot produce the
same failure**. That gate regenerates `.claude-plugin/marketplace.json` into a
shadow tree and diffs it, so mutating the real file exits non-zero on drift
whether or not this lint is registered at all. Every case here therefore runs
against a synthetic tree under a temp root, where no drift gate is watching, so
a green run proves *this* gate is doing the work.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "lint_plugin_membership", Path(__file__).parent / "lint-plugin-membership.py"
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


def _pack(root: Path, slug: str, *, version: str | None, scopes: list[str] | None,
          manifest: bool = True) -> None:
    d = root / "packs" / slug
    d.mkdir(parents=True)
    body = f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
    if version is not None:
        body += f'\n[pack.adapter-contract]\nversion = "{version}"\n'
    if scopes is not None:
        rendered = ", ".join(f'"{s}"' for s in scopes)
        body += f'\n[pack.install]\ndefault-scope = "repo"\nallowed-scopes = [{rendered}]\n'
    (d / "pack.toml").write_text(body, encoding="utf-8", newline="\n")
    if manifest:
        (d / ".claude-plugin").mkdir()
        (d / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": slug, "version": "1.0.0"}), encoding="utf-8", newline="\n"
        )


def _marketplace(root: Path, names: list[str]) -> None:
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"name": "t", "owner": {"name": "t"},
                    "plugins": [{"name": n} for n in names]}),
        encoding="utf-8", newline="\n",
    )


def main() -> int:
    print("test-lint-plugin-membership:")

    # The scope resolver mirrors commands/validate.py — pin its real gate.
    _check(
        "contract version is the gate, not the install table",
        lint.allowed_scopes(
            {"pack": {"install": {"allowed-scopes": ["repo", "user"]}}}
        ) == ["repo"],
        "a pack with no [pack.adapter-contract] must resolve ['repo']",
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root, "userpack", version="0.3", scopes=["repo", "user"])
        _pack(root, "repopack", version="0.3", scopes=["repo"])
        _pack(root, "_example", version="0.3", scopes=["repo", "user"])
        _pack(root, "nomanifest", version="0.3", scopes=["repo", "user"], manifest=False)

        _check("derived set admits only the user-capable pack",
               lint.publishable(root / "packs") == {"userpack"},
               f"got {lint.publishable(root / 'packs')}")

        _marketplace(root, ["userpack"])
        _check("clean tree passes", lint.check(root) == [], f"got {lint.check(root)}")

        # THE mutation AC9 names. Synthetic tree: no drift gate can claim this.
        _marketplace(root, ["userpack", "repopack"])
        out = lint.check(root)
        _check("extra repo-only entry fails",
               len(out) == 1 and "repopack" in out[0], f"got {out}")

        # The fail-closed direction: a truncation that drops a publishable pack.
        _marketplace(root, [])
        out = lint.check(root)
        _check("missing publishable entry fails",
               len(out) == 1 and "userpack" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root, "userpack", version="0.3", scopes=["repo", "user"])
        # No marketplace written at all. Returning clean here is the
        # "vacuously green" shape — the gate must not read a missing artifact
        # as nothing to check.
        out = lint.check(root)
        _check("missing root marketplace fails when packs are publishable",
               len(out) == 1 and "missing" in out[0], f"got {out}")

    if FAILURES:
        print(f"test-lint-plugin-membership: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-membership: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
