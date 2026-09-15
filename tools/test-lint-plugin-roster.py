#!/usr/bin/env python3
"""Construction tests for tools/lint-plugin-roster.py.

The point of this gate is that it is NOT derived from the production predicate,
so its test must not be either. Every case builds a marketplace by hand and
asserts against the module's hard-coded rosters.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "lint_plugin_roster", Path(__file__).parent / "lint-plugin-roster.py"
)
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _workflow(root: Path, paths, key: str = "paths", branches="[main]") -> None:
    """Write a minimal publish workflow carrying the given push trigger."""
    path = root / lint.WORKFLOW_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "on:\n  push:\n"
    if branches is not None:
        body += f"    branches: {branches}\n"
    if paths is not None:
        body += f"    {key}:\n"
        body += "".join(f"      - '{entry}'\n" for entry in paths)
    body += "  workflow_dispatch:\njobs:\n  publish:\n    runs-on: ubuntu-latest\n"
    path.write_text(body, encoding="utf-8", newline="\n")


def _marketplace(root: Path, names) -> None:
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": n} for n in names]}),
        encoding="utf-8", newline="\n",
    )


def main() -> int:
    print("test-lint-plugin-roster:")

    _check("the two rosters do not overlap",
           not (lint.PUBLISHED & lint.NOT_PUBLISHED),
           f"overlap: {sorted(lint.PUBLISHED & lint.NOT_PUBLISHED)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _marketplace(root, sorted(lint.PUBLISHED))
        _check("the exact published roster passes", lint.check(root) == [],
               f"got {lint.check(root)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # THE case this gate exists for: a repo-only pack got widened and
        # published. The derived membership lint stays green here.
        _marketplace(root, sorted(lint.PUBLISHED) + ["core"])
        out = lint.check(root)
        _check("a widened repo-only pack fails",
               len(out) == 1 and "core" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Fail-closed truncation: absences alone would miss this.
        _marketplace(root, sorted(lint.PUBLISHED - {"architect"}))
        out = lint.check(root)
        _check("a silently dropped pack fails",
               len(out) == 1 and "architect" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _marketplace(root, sorted(lint.PUBLISHED) + ["brand-new-pack"])
        out = lint.check(root)
        _check("an unrostered pack forces a decision",
               len(out) == 1 and "brand-new-pack" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = lint.check(root)
        _check("a missing marketplace fails", len(out) == 1, f"got {out}")

    # --- the publish workflow's push path allowlist ----------------------
    # Hand-built expectations again: deriving them from the production helper
    # would compare PUBLISHED against itself.
    _check("the allowlist is the 15 published packs plus 12 job inputs",
           lint.expected_paths() == frozenset({
               "packs/agent-skill-engineering/**",
               "packs/architect/**",
               "packs/atlassian/**",
               "packs/contracts/**",
               "packs/converters/**",
               "packs/credential-brokers/**",
               "packs/desk-research/**",
               "packs/experience-design/**",
               "packs/figma/**",
               "packs/frontend-engineering/**",
               "packs/github/**",
               "packs/linear/**",
               "packs/product-documentation/**",
               "packs/product-engineering/**",
               "packs/product-strategy/**",
               "packs/*/pack.toml",
               "packs/*/.claude-plugin/plugin.json",
               "packages/agentbundle/**",
               "Makefile",
               "tools/catalogue/**",
               "tools/pack_scope.py",
               "tools/lint-claude-plugin-publish-control.py",
               ".github/claude-plugin-publish-control.json",
               "tools/capture-publish-control-evidence.py",
               "docs/specs/claude-plugin-hook-parity/publish-control-evidence.json",
               ".claude-plugin/marketplace.json",
               ".github/workflows/publish-claude-plugins.yml",
           }),
           f"got {sorted(lint.expected_paths())}")

    # No repo-only pack may appear: triggering on one opens a deployment
    # approval for a push that cannot change the published tree.
    _check("no repo-only pack is in the allowlist",
           not ({f"packs/{n}/**" for n in lint.NOT_PUBLISHED} & lint.expected_paths()),
           f"got {sorted({f'packs/{n}/**' for n in lint.NOT_PUBLISHED} & lint.expected_paths())}")

    # The live file, not a fixture: this is the assertion that turns red when
    # the workflow and the roster part company.
    repo_root = Path(__file__).resolve().parents[1]
    out = lint.check_publish_trigger(repo_root)
    _check("the shipped workflow's allowlist matches the roster", out == [],
           f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _workflow(root, sorted(lint.expected_paths()))
        _check("an exact allowlist passes", lint.check_publish_trigger(root) == [],
               f"got {lint.check_publish_trigger(root)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # THE case an allowlist exists to be caught on: a published pack is not
        # in it, so its pushes silently stop publishing.
        _workflow(root, sorted(lint.expected_paths() - {"packs/architect/**"}))
        out = lint.check_publish_trigger(root)
        _check("a published pack missing from the allowlist fails",
               len(out) == 1 and "packs/architect/**" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The builder dropping out is the same failure with a wider blast
        # radius: every pack stops republishing on a code change.
        _workflow(root, sorted(lint.expected_paths() - {"packages/agentbundle/**"}))
        out = lint.check_publish_trigger(root)
        _check("a dropped job input fails",
               len(out) == 1 and "packages/agentbundle/**" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _workflow(root, sorted(lint.expected_paths()) + ["packs/core/**"])
        out = lint.check_publish_trigger(root)
        _check("a repo-only pack in the allowlist fails",
               len(out) == 1 and "packs/core/**" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Dropping either whole-of-packs glob makes a scope NARROWING
        # untriggerable, leaving a withdrawn pack live on the public
        # marketplace until some unrelated push happens to publish.
        _workflow(root, sorted(lint.expected_paths() - {"packs/*/pack.toml"}))
        out = lint.check_publish_trigger(root)
        _check("dropping the pack.toml glob fails",
               len(out) == 1 and "packs/*/pack.toml" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Retargeting the branch leaves every path assertion green while
        # publication from `main` stops, so it is pinned separately.
        _workflow(root, sorted(lint.expected_paths()), branches="[release]")
        out = lint.check_publish_trigger(root)
        _check("publishing from a branch other than main fails",
               len(out) == 1 and "'release'" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _workflow(root, sorted(lint.expected_paths()), branches=None)
        out = lint.check_publish_trigger(root)
        _check("an absent branch filter fails",
               len(out) == 1 and "not ['main']" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A mapping collapses to its keys under `set()`, so equality alone
        # would pass a `paths:` block GitHub cannot use.
        path = root / lint.WORKFLOW_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "on:\n  push:\n    branches: [main]\n    paths:\n"
            + "".join(f"      '{e}': yes\n" for e in sorted(lint.expected_paths())),
            encoding="utf-8", newline="\n",
        )
        out = lint.check_publish_trigger(root)
        _check("a `paths:` mapping fails",
               len(out) == 1 and "not a list" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _workflow(root, sorted(lint.expected_paths()), key="paths-ignore")
        out = lint.check_publish_trigger(root)
        _check("a `paths-ignore` filter fails",
               len(out) == 1 and "paths-ignore" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The unfiltered shape that shipped before this allowlist existed: a
        # revert has to be loud rather than merely allowed, and it gets its own
        # message so it does not read as a malformed filter.
        _workflow(root, None)
        out = lint.check_publish_trigger(root)
        _check("dropping the filter entirely fails",
               len(out) == 1 and "declares no `paths:` allowlist" in out[0],
               f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = lint.check_publish_trigger(Path(tmp))
        _check("a missing workflow file fails",
               len(out) == 1 and "is missing" in out[0], f"got {out}")

    if FAILURES:
        print(f"test-lint-plugin-roster: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-roster: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
