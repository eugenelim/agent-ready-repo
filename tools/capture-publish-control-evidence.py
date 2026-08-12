#!/usr/bin/env python3
"""Capture sanitized live publication-control state as T13's evidence artifact.

Reads the live ruleset, environment, and App installation through `gh api` and
emits the shape `tools/lint-claude-plugin-publish-control.py` compares against
`.github/claude-plugin-publish-control.json`.

The artifact carries NO identifiers — no App ID, installation ID, ruleset ID, or
account ID. Those are internal settings and do not belong in the repository. The
three-way identity agreement they used to evidence is computed here against live
state and recorded as the single `identities_agree` boolean; the lint refuses any
evidence file that reintroduces a raw identifier.

The canary outcomes are deliberately NOT inferred. They record pushes the
operator performed, not state the API holds, so asserting them from a settings
read would make the evidence self-confirming — exactly the failure mode the
desired-state/evidence split exists to prevent. Pass them explicitly once the
canary sequence in docs/guides/how-to/publisher-app-rollout.md has been run.

The installation read authenticates as the App, because no user-token route to
it exists: `gh`'s OAuth token is refused by `/user/installations` (403) and
`/repos/{repo}/installation` is App-only (404). So the private key is required
here, and must not be deleted until this step has run.

Usage:
    python3 tools/capture-publish-control-evidence.py --repo owner/name \\
        --private-key ~/.config/github-apps/claude-plugin-publisher.pem \\
        --ordinary-update rejected --publisher-app-update accepted
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
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


def _validate_repo(repo: str) -> str:
    """Return `repo` if it is a bare `owner/name`, else raise.

    Keeps a stray path segment out of the API URLs assembled below, so the
    fixed-scheme guarantee those calls rely on is actually true.
    """
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repo):
        raise CaptureError(
            f"--repo must be a bare owner/name, got {repo!r}"
        )
    return repo


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
    """Return the sanitized ruleset for `target`, plus its bypass actor id.

    The actor id is returned for comparison only and never reaches the
    artifact — see build_evidence.
    """
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
            },
        }, actor.get("actor_id")
    raise CaptureError(
        f"no active ruleset targets {target}; create it before capturing "
        "evidence (runbook step 3)"
    )


def observe_environment(repo: str) -> dict:
    """Return the sanitized environment policy, plus its App ID variable value.

    The App ID is returned for comparison only and never reaches the
    artifact — see build_evidence.
    """
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
    }, variable.get("value")


def _b64url(raw: bytes) -> str:
    """Return base64url without padding, as JWT requires."""
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _mint_app_jwt(app_id: object, key_path: Path) -> str:
    """Return a short-lived RS256 JWT asserting the App's own identity.

    Signing shells out to `openssl` to keep this tool pure-stdlib: RS256 needs
    an RSA implementation the standard library does not provide, and adding a
    crypto dependency for one signature in an operator-run script is not worth
    the supply-chain surface.
    """
    header = _b64url(b'{"alg":"RS256","typ":"JWT"}')
    issued = int(time.time()) - 60
    claims = json.dumps(
        {"iat": issued, "exp": issued + 600, "iss": str(app_id)},
        separators=(",", ":"),
    )
    signing_input = f"{header}.{_b64url(claims.encode())}"
    try:
        completed = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(key_path), "-binary"],
            input=signing_input.encode(),
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        raise CaptureError("`openssl` is required to sign the App JWT") from None
    if completed.returncode != 0:
        raise CaptureError(
            "could not sign the App JWT with "
            f"{key_path}: {completed.stderr.decode().strip()}"
        )
    return f"{signing_input}.{_b64url(completed.stdout)}"


def _app_api(path: str, jwt: str) -> object:
    """Return parsed JSON from an App-authenticated (JWT) GitHub API read."""
    request = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        # nosec B310 — the scheme is a fixed literal above, and every path
        # segment interpolated into it is either a constant or a `--repo` value
        # already constrained to `owner/name` by _validate_repo.
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and path.endswith("/installation"):
            raise CaptureError(
                "the App is not installed on this repository (404). Install it "
                "on this repository only, then re-run (runbook step 1)"
            ) from None
        raise CaptureError(f"GET {path} failed: HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise CaptureError(f"GET {path} failed: {exc.reason}") from None


def observe_app(repo: str, app_id: object, key_path: Path) -> dict:
    """Return the sanitized installation scope and permissions of the App.

    Authenticates AS the App. Neither user-token route works here: `gh`'s OAuth
    token is not authorized for `/user/installations` (403), and
    `/repos/{repo}/installation` is App-only by design (404/401). Signing a JWT
    with the private key the operator already holds is the only path that reads
    installation permissions authoritatively rather than taking them on trust.
    """
    jwt = _mint_app_jwt(app_id, key_path)
    identity = _app_api("app", jwt)
    if str(identity.get("id")) != str(app_id):
        raise CaptureError(
            f"private key belongs to App {identity.get('id')!r}, but the "
            f"environment variable names {app_id!r}; they must be the same App"
        )
    installation = _app_api(f"repos/{repo}/installation", jwt)
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
    }, installation.get("app_id")


def build_evidence(
    repo: str, target: str, canary: dict, key_path: Path
) -> dict:
    """Assemble the full sanitized evidence document."""
    # Environment first: its App ID variable is what selects the installation.
    environment, environment_app_id = observe_environment(repo)
    branch, bypass_actor_id = observe_branch(repo, target)
    app, installation_app_id = observe_app(repo, environment_app_id, key_path)

    # The three identities are compared HERE and only the verdict is recorded.
    # Committing the App ID three times would publish an internal identifier
    # into the repository for no gain: the artifact is a record that the check
    # passed against live state, and re-running this tool re-verifies it. Same
    # trust model as the canary outcomes above.
    identities = {
        str(value)
        for value in (bypass_actor_id, installation_app_id, environment_app_id)
    }
    identities_agree = (
        None not in (bypass_actor_id, installation_app_id, environment_app_id)
        and len(identities) == 1
    )
    if not identities_agree:
        raise CaptureError(
            "the ruleset bypass actor, the App installation, and the "
            "environment's App ID variable do not all name the same App; fix "
            "the mismatch in settings before capturing evidence"
        )
    return {
        "version": 1,
        "branch": branch,
        "app": app,
        "environment": environment,
        "identities_agree": identities_agree,
        "canary": canary,
        "observed_at": datetime.now(UTC).isoformat(),
        "observation_source": "github-api-sanitized",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument(
        "--private-key",
        type=Path,
        required=True,
        help="path to the publisher App's PEM; used only to sign a short-lived "
        "JWT for the App-only installation read, never written anywhere",
    )
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
        _validate_repo(args.repo)
        evidence = build_evidence(
            args.repo, args.target, canary, args.private_key
        )
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
