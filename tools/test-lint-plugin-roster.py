#!/usr/bin/env python3
"""Construction tests for tools/lint-plugin-roster.py.

The point of this gate is that it is NOT derived from the production predicate,
so its test must not be either. Every case builds a marketplace by hand and
asserts against the module's hard-coded rosters.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
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
    _check("the allowlist is the 16 published packs plus 10 job inputs",
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
               "packs/code-intelligence/**",
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

    for catch_all in ("packs/*/pack.toml", "packs/*/.claude-plugin/plugin.json"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # A catch-all over every pack's manifest makes a repo-only pack's
            # version bump open a deployment approval it cannot justify.
            _workflow(root, sorted(lint.expected_paths()) + [catch_all])
            out = lint.check_publish_trigger(root)
            _check(f"a workflow carrying {catch_all} fails",
                   len(out) == 1 and catch_all in out[0], f"got {out}")

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

    # --- what the shipped filter does and does not match ------------------
    import yaml

    workflow_doc = yaml.safe_load((repo_root / lint.WORKFLOW_REL).read_text(encoding="utf-8"))
    triggers = workflow_doc.get("on", workflow_doc.get(True))
    push_paths = triggers["push"]["paths"]

    def _matches(pattern: str, path: str) -> bool:
        """GitHub path-filter semantics: `*` stops at `/`, `**` crosses it."""
        out, i = "", 0
        while i < len(pattern):
            if pattern.startswith("**", i):
                out, i = out + ".*", i + 2
            elif pattern[i] == "*":
                out, i = out + "[^/]*", i + 1
            else:
                out, i = out + re.escape(pattern[i]), i + 1
        return re.fullmatch(out, path) is not None

    def _hit(path: str) -> bool:
        return any(_matches(pattern, path) for pattern in push_paths)

    _check("no shipped push path has a wildcard in the pack segment",
           not [p for p in push_paths
                if p.startswith("packs/") and "*" in p.split("/")[1]],
           f"got {[p for p in push_paths if p.startswith('packs/')]}")

    for pack in sorted(lint.NOT_PUBLISHED):
        files = [f"packs/{pack}/pack.toml", f"packs/{pack}/.claude-plugin/plugin.json",
                 f"packs/{pack}/.apm/skills/example/SKILL.md"]
        _check(f"repo-only pack {pack} matches no push path",
               not [f for f in files if _hit(f)],
               f"matched {[f for f in files if _hit(f)]}")

    for pack in sorted(lint.PUBLISHED):
        files = [f"packs/{pack}/pack.toml", f"packs/{pack}/.claude-plugin/plugin.json"]
        _check(f"published pack {pack} manifests match a push path",
               all(_hit(f) for f in files),
               f"unmatched {[f for f in files if not _hit(f)]}")

    _check("the workflow file's own path is a push path",
           _hit(lint.WORKFLOW_REL.as_posix()), "not matched")

    _check("the workflow keeps workflow_dispatch", "workflow_dispatch" in triggers,
           f"triggers {sorted(map(str, triggers))}")
    _check("the publish job keeps the claude-plugin-publish environment",
           workflow_doc["jobs"]["publish"].get("environment") == "claude-plugin-publish",
           f"got {workflow_doc['jobs']['publish'].get('environment')!r}")

    # Registrations, not substrings: a commented-out `_script_step(...)` call
    # leaves the file names in the source but removes the step from the chain.
    chain_tree = ast.parse(
        (repo_root / "tools" / "repo" / "build_gate_chain.py").read_text(encoding="utf-8")
    )
    registered = {
        node.args[2].value
        for node in ast.walk(chain_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_script_step"
        and len(node.args) >= 3
        and isinstance(node.args[2], ast.Constant)
    }
    _check("the gate chain registers both the membership and the roster lint",
           {"lint-plugin-membership.py", "lint-plugin-roster.py"} <= registered,
           f"registered {sorted(r for r in registered if 'plugin' in r)}")

    # A pack moving between the rosters changes what must be published. The
    # workflow's list has to move with it, in the same commit, or the lint fails;
    # the workflow file is then itself a push path, so that commit starts a run.
    original = lint.PUBLISHED, lint.NOT_PUBLISHED
    try:
        for label, pack, published_after in (
            ("promoting repo-only pack core", "core", True),
            ("withdrawing published pack architect", "architect", False),
        ):
            lint.PUBLISHED, lint.NOT_PUBLISHED = original  # each case starts clean
            before = set(original[0])
            after = (before | {pack}) if published_after else (before - {pack})
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _workflow(root, sorted(lint.expected_paths()))  # list as it was
                lint.PUBLISHED = frozenset(after)
                lint.NOT_PUBLISHED = frozenset(
                    (set(original[1]) - {pack}) if published_after
                    else (set(original[1]) | {pack})
                )
                stale = lint.check_publish_trigger(root)
                _check(f"{label} with the workflow list unchanged fails",
                       len(stale) == 1 and f"packs/{pack}/**" in stale[0], f"got {stale}")
                _workflow(root, sorted(lint.expected_paths()))  # list moved too
                moved = lint.check_publish_trigger(root)
                _check(f"{label} passes once the workflow list moves with it",
                       moved == [], f"got {moved}")
    finally:
        lint.PUBLISHED, lint.NOT_PUBLISHED = original

    if FAILURES:
        print(f"test-lint-plugin-roster: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-roster: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
