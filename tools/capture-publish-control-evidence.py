#!/usr/bin/env python3
"""Capture sanitized live publication-control state as T13's evidence artifact.

Reads the live ruleset, environment, and App installation through `gh api` and
emits the shape `tools/lint-claude-plugin-publish-control.py` compares against
`.github/claude-plugin-publish-control.json`. Nothing secret is read or written:
the App ID is a public identifier, and only structural booleans accompany it.

The canary outcomes are deliberately NOT inferred. They record pushes the
operator performed, not state the API holds, so asserting them from a settings
read would make the evidence self-confirming — exactly the failure mode the
desired-state/evidence split exists to prevent. Pass them explicitly once the
canary sequence in docs/guides/how-to/publisher-app-rollout.md has been run.

Usage:
    python3 tools/capture-publish-control-evidence.py --repo owner/name \\
        --ordinary-update rejected --publisher-app-update accepted
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "claude-plugin-hook-parity"
    / "publish-control-evidence.json"
)
ENVIRONMENT_NAME = "claude-plugin-publish"
APP_ID_VARIABLE = "CLAUDE_PLUGIN_PUBLISHER_APP_ID"
LIVE_BRANCH = "refs/heads/claude-plugins-dist"
CANARY_BRANCH = "refs/heads/claude-plugins-dist-control-canary"


class CaptureError(RuntimeError):
    """A live observation could not be made or did not match the contract."""


def _gh_api(path: str) -> object:
    """Return parsed JSON from `gh api <path>`, or raise CaptureError."""
    try:
        completed = subprocess.run(
            ["gh", "api", path],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise CaptureError(
            "the `gh` CLI is required to observe live settings; install it and "
            "authenticate with `gh auth login`"
        ) from None
    if completed.returncode != 0:
        raise CaptureError(
            f"gh api {path} failed ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CaptureError(f"gh api {path} returned non-JSON: {exc}") from None


def observe_branch(repo: str, target: str) -> dict:
    """Return the sanitized ruleset protecting `target`."""
    rulesets = _gh_api(f"repos/{repo}/rulesets")
    if not isinstance(rulesets, list):
        raise CaptureError("ruleset listing was not a JSON array")
    for summary in rulesets:
        detail = _gh_api(f"repos/{repo}/rulesets/{summary['id']}")
        conditions = detail.get("conditions", {}).get("ref_name", {})
        if target not in conditions.get("include", []):
            continue
        rules = {rule["type"] for rule in detail.get("rules", [])}
        bypass = detail.get("bypass_actors", [])
        if len(bypass) != 1:
            raise CaptureError(
                f"ruleset {detail.get('name')!r} has {len(bypass)} bypass "
                "actors; the contract admits exactly one (the publisher App)"
            )
        actor = bypass[0]
        return {
            "target": target,
            "restrict_updates": "update" in rules,
            "restrict_deletions": "deletion" in rules,
            "block_force_pushes": "non_fast_forward" in rules,
            "bypass": {
                "actor_type": actor.get("actor_type"),
                "actor_binding": "environment_app_id",
                "mode": actor.get("bypass_mode"),
                "actor_id": actor.get("actor_id"),
            },
        }
    raise CaptureError(
        f"no active ruleset targets {target}; create it before capturing "
        "evidence (runbook step 3)"
    )


def observe_environment(repo: str) -> dict:
    """Return the sanitized protected-environment policy and its App ID."""
    env = _gh_api(f"repos/{repo}/environments/{ENVIRONMENT_NAME}")
    reviewers = 0
    prevent_self_review = False
    for rule in env.get("protection_rules", []):
        if rule.get("type") == "required_reviewers":
            reviewers = len(rule.get("reviewers", []))
            prevent_self_review = bool(rule.get("prevent_self_review"))
    policy = env.get("deployment_branch_policy") or {}
    branches: list[str] = []
    if policy.get("custom_branch_policies"):
        named = _gh_api(
            f"repos/{repo}/environments/{ENVIRONMENT_NAME}"
            "/deployment-branch-policies"
        )
        branches = sorted(
            item["name"] for item in named.get("branch_policies", [])
        )
    variable = _gh_api(
        f"repos/{repo}/environments/{ENVIRONMENT_NAME}/variables/{APP_ID_VARIABLE}"
    )
    return {
        "name": ENVIRONMENT_NAME,
        "deployment_branches": branches,
        "required_reviewers": reviewers,
        "prevent_self_review": prevent_self_review,
        "allow_admin_bypass": bool(env.get("can_admins_bypass")),
        "app_id_variable": APP_ID_VARIABLE,
        "private_key_secret": "CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY",
        "app_id_value": variable.get("value"),
    }


def observe_app(app_id: object) -> dict:
    """Return the sanitized installation scope and permissions of the App.

    Read through `/user/installations` rather than `/repos/{repo}/installation`:
    the latter is documented for App (JWT) authentication and 403s under the
    user token `gh` holds, which would make this step unrunnable by the very
    operator the runbook addresses.
    """
    listing = _gh_api("user/installations")
    installations = listing.get("installations", [])
    for installation in installations:
        if str(installation.get("app_id")) != str(app_id):
            continue
        permissions = {
            key: value
            for key, value in (installation.get("permissions") or {}).items()
            if value == "write"
        }
        selection = installation.get("repository_selection")
        return {
            "installation_scope": (
                "selected_repository" if selection == "selected" else selection
            ),
            "permissions": permissions,
            "id": installation.get("app_id"),
        }
    raise CaptureError(
        f"no installation visible for App ID {app_id!r}; confirm the App is "
        "installed on this repository and that `gh` is authenticated as an "
        "account that can see it (runbook step 1)"
    )


def build_evidence(repo: str, target: str, canary: dict) -> dict:
    """Assemble the full sanitized evidence document."""
    # Environment first: its App ID variable is what selects the installation,
    # and compare_evidence requires the ruleset bypass actor, the installation,
    # and this variable to resolve to one identity.
    environment = observe_environment(repo)
    return {
        "version": 1,
        "branch": observe_branch(repo, target),
        "app": observe_app(environment["app_id_value"]),
        "environment": environment,
        "canary": canary,
        "observed_at": datetime.now(UTC).isoformat(),
        "observation_source": "github-api-sanitized",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--target",
        default=LIVE_BRANCH,
        help="ruleset ref to observe; use the canary ref mid-rollout",
    )
    parser.add_argument(
        "--ordinary-update",
        choices=("rejected", "accepted"),
        required=True,
        help="observed outcome of the ordinary-identity canary push",
    )
    parser.add_argument(
        "--publisher-app-update",
        choices=("rejected", "accepted"),
        required=True,
        help="observed outcome of the publisher-App canary push",
    )
    parser.add_argument(
        "--live-branch-negative-tested",
        action="store_true",
        help="only if the live branch itself was used as a negative probe; "
        "the contract requires this to stay false",
    )
    args = parser.parse_args(argv)

    canary = {
        "branch": CANARY_BRANCH,
        "ordinary_update": args.ordinary_update,
        "publisher_app_update": args.publisher_app_update,
        "live_branch_negative_tested": args.live_branch_negative_tested,
    }
    try:
        evidence = build_evidence(args.repo, args.target, canary)
    except CaptureError as exc:
        print(f"capture-publish-control-evidence: {exc}", file=sys.stderr)
        return 1

    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    print(f"capture-publish-control-evidence: wrote {args.output}")
    print(
        "Next: python3 tools/lint-claude-plugin-publish-control.py "
        "--require-live-evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
