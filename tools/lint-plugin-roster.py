#!/usr/bin/env python3
"""Roster tripwire: the published set, enumerated literally.

**Why this exists separately from `lint-plugin-membership.py`.** That gate
derives *both* sides of its comparison from the same predicate, so a predicate
bug moves them together and it stays green — a tautology. This one hard-codes
the expected rosters, so it is the only check that turns red when widening a
pack's `allowed-scopes` changes what gets published.

**If this fails, that is the gate working.** After
docs/specs/claude-plugin-route-scope, editing one line of `allowed-scopes`
publishes a pack's code to a public marketplace, or withdraws it. Do not "fix" a
failure by editing the lists below to match reality — confirm the change in
publication is what you meant (the spec's `Ask first` boundary), then update the
list in the same commit that changes the pack.

Both directions are pinned. Absences alone catch a fail-open bug; only the
present-set catches a fail-closed truncation that silently drops a pack.

It also pins the publish workflow's `paths:` push allowlist to `PUBLISHED`.
That allowlist is what keeps a push that cannot change a published plugin from
opening a deployment approval on the gated publish job, and it fails unsafe on
its own: a pack absent from it simply stops publishing, with nothing red. This
is the gate that makes it fail closed instead, in both directions -- and the
unrostered-pack refusal above is what forces a new pack through it at all.

Usage:
    python tools/lint-plugin-roster.py [--root .]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-plugin-roster"

# Repo-only: `allowed-scopes` omits "user", so the user-scope plugin route
# cannot honour an install of them.
NOT_PUBLISHED = frozenset({
    "catalogue-curation",
    "core",
    "governance-extras",
    "iac-terraform",
    "monorepo-extras",
    "release-engineering",
    "user-guide-diataxis",
})

# User-capable, and therefore offered on the route.
PUBLISHED = frozenset({
    # Added 2026-08-27 with docs/specs/agent-skill-engineering-foundation.
    # Owner decision: the pack declares user scope, so it ships the plugin
    # manifest that makes the advertised install resolve rather than
    # advertising a route the marketplace cannot serve.
    "agent-skill-engineering",
    "architect",
    "atlassian",
    "contracts",
    "converters",
    "credential-brokers",
    "desk-research",
    "experience-design",
    "figma",
    "frontend-engineering",
    "github",
    "linear",
    "product-documentation",
    "product-engineering",
    "product-strategy",
})


WORKFLOW_REL = Path(".github/workflows/publish-claude-plugins.yml")

# What the publish job consumes besides the published pack sources: the builder
# and the Make target that drives it, the publish script plus the pack-scope
# helper and root marketplace it reads, and the publication-control gate plus
# the three files it reads (its desired-state contract, the captured evidence,
# and the capture tool whose repository-name rule it loads). A push touching
# none of these and no published pack cannot change the output.
#
# The two `packs/*/` globs are deliberately every pack, not every published
# pack: `publish_claude_plugins.py` re-derives the publishable set from the
# whole of `packs/`, so a pack whose scopes NARROW must trigger the run that
# withdraws it from the public marketplace. They also make a new pack's first
# publish fire without waiting for `PUBLISHED` below to be extended.
PUBLISH_JOB_INPUTS = (
    "packs/*/pack.toml",
    "packs/*/.claude-plugin/plugin.json",
    "packages/agentbundle/**",
    "Makefile",
    "tools/catalogue/**",
    "tools/pack_scope.py",
    "tools/lint-claude-plugin-publish-control.py",
    # The publication-control gate's other two inputs: the desired-state
    # contract it compares against, and the capture tool whose repository-name
    # rule it `exec_module`s rather than restating.
    ".github/claude-plugin-publish-control.json",
    "tools/capture-publish-control-evidence.py",
    "docs/specs/claude-plugin-hook-parity/publish-control-evidence.json",
    # A publish refusal input: the publish script rejects a root marketplace
    # advertising packs the branch does not carry.
    ".claude-plugin/marketplace.json",
    ".github/workflows/publish-claude-plugins.yml",
)


class ToolError(RuntimeError):
    """An environment or parse problem. Exit 2, never a silent pass."""


def expected_paths() -> frozenset[str]:
    """Return the push paths the publish workflow must trigger on.

    The per-pack-source half is derived from ``PUBLISHED`` rather than written
    out again, so adding a pack to that roster is what adds its trigger path.
    ``PUBLISH_JOB_INPUTS`` carries the rest, including the two whole-of-``packs/``
    globs that keep a withdrawal triggerable.
    """
    return frozenset(f"packs/{name}/**" for name in PUBLISHED) | frozenset(
        PUBLISH_JOB_INPUTS
    )


def check_publish_trigger(root: Path) -> list[str]:
    """Return diagnostics for the publish workflow's push path filter."""
    workflow = root / WORKFLOW_REL
    if not workflow.exists():
        return [f"{GATE}: {WORKFLOW_REL.as_posix()} is missing"]
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment, not logic
        raise ToolError(
            f"{GATE}: PyYAML not installed — run: "
            f"pip install -r tools/requirements.txt"
        ) from exc
    try:
        doc = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ToolError(f"{GATE}: cannot read {WORKFLOW_REL.as_posix()}: {exc}") from exc
    # YAML 1.1 resolves a bare `on` key to the boolean True, so looking up the
    # string spelling alone finds nothing and reports a clean result.
    triggers = doc.get("on", doc.get(True)) if isinstance(doc, dict) else None
    push = triggers.get("push") if isinstance(triggers, dict) else None
    if not isinstance(push, dict):
        return [
            f"{GATE}: {WORKFLOW_REL.as_posix()} declares no `push:` mapping, so "
            f"there is no path filter to pin."
        ]
    # The branch filter, not only the path filter. Without this the lint's
    # own claim to pin the push trigger is false: retargeting `branches` stops
    # publication from `main`, or opens a deployment approval on every branch,
    # and every assertion here stays green.
    if push.get("branches") != ["main"]:
        return [
            f"{GATE}: {WORKFLOW_REL.as_posix()} publishes on "
            f"{push.get('branches')!r}, not ['main']. The published branch "
            f"tracks `main`; another branch either stops publication or opens "
            f"a deployment approval on pushes that must not publish."
        ]
    if "paths-ignore" in push:
        return [
            f"{GATE}: {WORKFLOW_REL.as_posix()} filters with `paths-ignore`. "
            f"The route is pinned to a `paths:` allowlist: an ignore-list has to "
            f"match EVERY changed file to skip, and a pack change here rides "
            f"with a changelog entry and the self-hosted projections, so it "
            f"skips nothing."
        ]
    if "paths" not in push:
        # The unfiltered shape that shipped before this allowlist existed. Its
        # own message, so a revert does not read as a malformed filter.
        return [
            f"{GATE}: {WORKFLOW_REL.as_posix()} declares no `paths:` allowlist, "
            f"so every push to `main` opens a deployment approval on the gated "
            f"publish job — including pushes that cannot change the output."
        ]
    paths = push.get("paths")
    # A mapping would collapse to its keys under `set()` and compare equal, so
    # the shape is checked before the contents.
    if not isinstance(paths, list):
        return [
            f"{GATE}: {WORKFLOW_REL.as_posix()} declares `paths:` as "
            f"{type(paths).__name__}, not a list of path patterns."
        ]
    found = set(paths)
    expected = set(expected_paths())
    failures = []
    for entry in sorted(expected - found):
        failures.append(
            f"{GATE}: {WORKFLOW_REL.as_posix()} does not trigger on {entry!r}. "
            f"An allowlist fails unsafe — a path missing here stops publishing "
            f"with nothing else red — so a pack added to PUBLISHED above gets "
            f"its trigger path in the same commit."
        )
    for entry in sorted(found - expected):
        failures.append(
            f"{GATE}: {WORKFLOW_REL.as_posix()} triggers on {entry!r}, which "
            f"neither a published pack nor the publish job consumes. Every "
            f"needless trigger opens a deployment approval on the gated job."
        )
    return failures


def check(root: Path) -> list[str]:
    marketplace = root / ".claude-plugin" / "marketplace.json"
    if not marketplace.exists():
        return [f"{GATE}: .claude-plugin/marketplace.json is missing"]
    listed = {
        p.get("name")
        for p in json.loads(marketplace.read_text(encoding="utf-8")).get("plugins", [])
        if p.get("name")
    }
    failures = []
    for name in sorted(listed & NOT_PUBLISHED):
        failures.append(
            f"{GATE}: {name!r} is published but is pinned repo-only. If you "
            f"widened its allowed-scopes, that publishes its code to a public "
            f"marketplace — see the spec's `Ask first` boundary — and this list "
            f"moves in the same commit."
        )
    for name in sorted(PUBLISHED - listed):
        failures.append(
            f"{GATE}: {name!r} is pinned as published but is absent from the "
            f"marketplace — a fail-closed truncation, or a deliberate narrowing "
            f"this list has not caught up with."
        )
    # A pack in neither list is new: force a decision rather than defaulting.
    for name in sorted(listed - PUBLISHED - NOT_PUBLISHED):
        failures.append(
            f"{GATE}: {name!r} is published but appears in neither roster — add "
            f"it to PUBLISHED if publishing it is intended."
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        failures = check(root) + check_publish_trigger(root)
    except ToolError as exc:
        print(exc, file=sys.stderr)
        return 2
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"{GATE}: FAIL ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print(
        f"{GATE}: ok — {len(PUBLISHED)} published, {len(NOT_PUBLISHED)} withheld, "
        f"{len(expected_paths())} push path(s) pinned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
