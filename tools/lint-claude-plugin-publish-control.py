#!/usr/bin/env python3
"""Validate desired and observed controls for Claude-plugin publication."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIRED_PATH = REPO_ROOT / ".github" / "claude-plugin-publish-control.json"
EVIDENCE_PATH = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "claude-plugin-hook-parity"
    / "publish-control-evidence.json"
)
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "publish-claude-plugins.yml"

# AC36 — the workflow must authenticate with the identity that actually exists.
# Presence of the committed evidence file is the only offline signal for whether
# the ADR-0079 publisher App was ever provisioned; nothing here touches the
# network. Markers are matched against step/permission syntax rather than prose
# so the file's own explanatory comments cannot flip the detected mode.
APP_IDENTITY_MARKERS = (
    "uses: actions/create-github-app-token@",
    "environment: claude-plugin-publish",
    "${{ vars.CLAUDE_PLUGIN_PUBLISHER_APP_ID }}",
    "${{ secrets.CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY }}",
)
APP_IDENTITY_MARKERS = APP_IDENTITY_MARKERS + (
    "CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ steps.publisher-token.outputs.token }}",
)
INTERIM_IDENTITY_MARKERS = (
    "CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
)

# A write grant in block style (`  contents: write`), a quoted scalar
# (`contents: 'write'`), or flow style (`{ contents: write }`). A bare
# `"contents: write" in text` test also matched the token step's own
# `permission-contents: write`; an unquoted-only anchor missed the quoted form.
WRITE_GRANT = re.compile(
    r"(?m)(?:^\s+|[{,]\s*)contents:\s*['\"]?write['\"]?\s*(?=$|[},#\s])"
)
PERSIST_CREDENTIALS_FALSE = re.compile(
    r"(?m)^\s+persist-credentials:\s*['\"]?false['\"]?\s*(?:#.*)?$"
)
CHECKOUT_STEP = re.compile(r"uses:\s*actions/checkout@")

# Every key the evidence artifact may carry. An allowlist, not a denylist: the
# denylist was fail-open at the top level, which is the one place an unexpected
# key survives `compare_evidence`'s exact-dict comparison of the known blocks.
ALLOWED_EVIDENCE_KEYS = frozenset(
    {
        "version",
        "branch",
        "app",
        "environment",
        "identities_agree",
        "canary",
        "observed_at",
        "observation_source",
    }
)


def detect_publisher_mode(workflow: str) -> str:
    """Classify the publisher workflow's authentication identity.

    Returns ``app`` (ADR-0079 end state), ``interim`` (generic Actions app),
    ``mixed`` when both shapes appear, or ``unknown`` when neither does. The
    last two are always violations: a publisher that names two identities, or
    none, cannot be reasoned about by the sequencing rule below.
    """
    present = [marker for marker in APP_IDENTITY_MARKERS if marker in workflow]
    has_interim = any(marker in workflow for marker in INTERIM_IDENTITY_MARKERS)
    if present and has_interim:
        return "mixed"
    if len(present) == len(APP_IDENTITY_MARKERS):
        return "app"
    if present:
        # Some App markers but not all. Requiring every marker is what stops a
        # publisher that merely names the protected environment while sourcing
        # its token from an arbitrary secret from passing as the App identity.
        return "incomplete-app"
    if has_interim:
        return "interim"
    return "unknown"


def validate_sequencing(workflow: str, evidence_present: bool) -> list[str]:
    """Return violations of the identity/provisioning ordering (AC36).

    Both directions fail closed. Shipping the App-token shape before the
    credentials exist is what broke publication on `main`; leaving the interim
    shape after provisioning would silently keep the generic Actions app as a
    writer the ruleset is meant to exclude.
    """
    errors: list[str] = []
    mode = detect_publisher_mode(workflow)
    if mode == "mixed":
        errors.append(
            "publisher workflow declares both the App-token and interim "
            "identities; exactly one must be present"
        )
    elif mode == "unknown":
        errors.append(
            "publisher workflow declares no recognized publish identity; "
            "expected the App-token step or the interim GITHUB_TOKEN mapping"
        )
    elif evidence_present and mode != "app":
        errors.append(
            "publisher App is provisioned (evidence present) but the workflow "
            "still holds the interim identity; restore the App-token step"
        )
    elif not evidence_present and mode != "interim":
        errors.append(
            "publisher workflow mints an App token but no provisioning "
            "evidence exists; the job cannot authenticate — complete the "
            "rollout (docs/guides/how-to/publisher-app-rollout.md) or restore "
            "the interim identity"
        )
    if mode == "incomplete-app":
        missing = [m for m in APP_IDENTITY_MARKERS if m not in workflow]
        errors.append(
            "publisher workflow names the App identity only partially; "
            f"missing {missing}. Naming the protected environment while "
            "sourcing the token elsewhere is not the App identity"
        )
    if mode == "app" and WRITE_GRANT.search(workflow):
        errors.append(
            "App-token publisher must keep GITHUB_TOKEN read-only"
        )
    # One `persist-credentials: false` per checkout step, matched as a mapping
    # key rather than a substring: a bare test was satisfied by a comment, and a
    # second checkout step omitting the option would leave the ambient token in
    # .git/config for the rest of the job that later holds the publisher token.
    checkouts = len(CHECKOUT_STEP.findall(workflow))
    disclaimers = len(PERSIST_CREDENTIALS_FALSE.findall(workflow))
    if checkouts and disclaimers < checkouts:
        errors.append(
            f"{checkouts} checkout step(s) but {disclaimers} "
            "`persist-credentials: false` setting(s); every checkout in the "
            "publisher must refuse to persist ambient credentials"
        )
    elif not checkouts:
        errors.append("publisher workflow has no checkout step to constrain")
    return errors


def _load_pack_scope_module():
    spec = importlib.util.spec_from_file_location(
        "pack_scope", REPO_ROOT / "tools" / "pack_scope.py"
    )
    if spec is None or spec.loader is None:
        raise ValueError("cannot load the canonical pack-scope mirror")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_publishable_hook_pack(root: Path) -> bool:
    """Return whether publication now includes executable authored hooks."""
    packs_dir = root / "packs"
    if not packs_dir.is_dir():
        return False
    pack_scope = _load_pack_scope_module()
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").is_file():
            continue
        if not (pack / ".claude-plugin" / "plugin.json").is_file():
            continue
        try:
            metadata = tomllib.loads((pack / "pack.toml").read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if not pack_scope.is_user_capable(metadata):
            continue
        for relative in (Path(".apm/hooks"), Path(".apm/hook-wiring")):
            source = pack / relative
            if source.is_dir() and any(item.is_file() for item in source.rglob("*")):
                return True
    return False


# Internal settings must not enter the repository. These keys are the ones a
# well-meaning regeneration would reintroduce, because they are what the live
# API returns alongside the structural state we do want.
FORBIDDEN_IDENTIFIER_KEYS = (
    "actor_id",
    "app_id",
    "login",
    "email",
    "token",
    "app_id_value",
    "installation_id",
    "ruleset_id",
    "account_id",
    "node_id",
)


def _identifier_leaks(value: object, path: str = "evidence") -> list[str]:
    """Return every forbidden identifier key reachable inside `value`.

    Walks rather than checking known locations: the point is to catch an
    identifier wherever a future capture change puts it, including a bare `id`
    on the app block, which is where this leaked the first time.
    """
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            here = f"{path}.{key}"
            # Top level is allowlisted: `compare_evidence` compares the known
            # blocks by exact dict equality, so an unexpected key survives only
            # here. Deeper levels use the denylist plus a bare `id`.
            if path == "evidence" and key not in ALLOWED_EVIDENCE_KEYS:
                errors.append(
                    f"{here} is not an allowed evidence key; the artifact "
                    f"carries exactly {sorted(ALLOWED_EVIDENCE_KEYS)}"
                )
            elif key in FORBIDDEN_IDENTIFIER_KEYS or key == "id":
                errors.append(
                    f"{here} carries an internal identifier; evidence records "
                    "identities_agree, never the identifiers themselves"
                )
            errors.extend(_identifier_leaks(nested, here))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_identifier_leaks(nested, f"{path}[{index}]"))
    return errors


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_desired(desired: dict) -> list[str]:
    """Return violations of the repository-authored control contract."""
    errors: list[str] = []
    branch = desired.get("branch")
    if not isinstance(branch, dict):
        return ["desired branch control must be an object"]
    expected_branch = {
        "target": "refs/heads/claude-plugins-dist",
        "restrict_updates": True,
        "restrict_deletions": True,
        "block_force_pushes": True,
        "bypass": {
            "actor_type": "Integration",
            "actor_binding": "environment_app_id",
            "mode": "always",
        },
    }
    if branch != expected_branch:
        errors.append("branch control must target dist with only the publisher-app bypass")

    app = desired.get("app")
    expected_app = {
        "installation_scope": "selected_repository",
        # metadata:read is mandatory and cannot be removed from a GitHub App;
        # pinning the exact full map is what makes a broader installation — an
        # added administration:read or secrets:read — fail the comparison.
        "permissions": {"contents": "write", "metadata": "read"},
    }
    if app != expected_app:
        errors.append(
            "publisher app must be repository-scoped with exactly "
            "contents:write plus the mandatory metadata:read"
        )

    environment = desired.get("environment")
    expected_environment = {
        "name": "claude-plugin-publish",
        "deployment_branches": ["main"],
        "required_reviewers": 1,
        "prevent_self_review": True,
        "allow_admin_bypass": False,
        "app_id_variable": "CLAUDE_PLUGIN_PUBLISHER_APP_ID",
        "private_key_secret": "CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY",
    }
    if environment != expected_environment:
        errors.append("protected environment policy does not match the publisher boundary")

    canary = desired.get("canary")
    expected_canary = {
        "branch": "refs/heads/claude-plugins-dist-control-canary",
        "ordinary_update": "rejected",
        "publisher_app_update": "accepted",
        "live_branch_negative_tested": False,
    }
    if canary != expected_canary:
        errors.append("canary contract must prove ordinary denial and app acceptance")
    if desired.get("version") != 1:
        errors.append("desired control version must be 1")
    return errors


def compare_evidence(desired: dict, evidence: dict) -> list[str]:
    """Compare independently captured sanitized state with desired state."""
    errors: list[str] = []
    if evidence.get("version") != desired.get("version"):
        errors.append("evidence version differs from desired control")
    observed_branch = evidence.get("branch")
    observed_app = evidence.get("app")
    observed_environment = evidence.get("environment")
    if not all(
        isinstance(value, dict)
        for value in (observed_branch, observed_app, observed_environment)
    ):
        errors.append("evidence branch, app, and environment must be objects")
    else:
        if observed_branch != desired.get("branch"):
            errors.append("evidence branch differs from desired control")
        if observed_app != desired.get("app"):
            errors.append("evidence app differs from desired control")
        if observed_environment != desired.get("environment"):
            errors.append("evidence environment differs from desired control")
        # The three-way identity agreement is asserted, not restated. Carrying
        # the App ID three times would publish an internal identifier for no
        # gain; the capture tool compares them against live state and records
        # only the verdict, which must be explicitly true.
        if evidence.get("identities_agree") is not True:
            errors.append(
                "evidence must assert identities_agree: true — the ruleset "
                "bypass actor, the App installation, and the environment's App "
                "ID variable all naming the same App"
            )
        errors.extend(_identifier_leaks(evidence))
    if evidence.get("canary") != desired.get("canary"):
        errors.append("evidence canary differs from desired control")
    observed_at = evidence.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at:
        errors.append("evidence must include a non-empty observed_at timestamp")
    source = evidence.get("observation_source")
    if source != "github-api-sanitized":
        errors.append("evidence observation_source must be github-api-sanitized")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--desired", type=Path, default=DESIRED_PATH)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--workflow", type=Path, default=WORKFLOW_PATH)
    parser.add_argument("--require-live-evidence", action="store_true")
    args = parser.parse_args(argv)

    try:
        desired = _load(args.desired)
    except ValueError as exc:
        print(f"lint-claude-plugin-publish-control: {exc}", file=sys.stderr)
        return 1
    errors = validate_desired(desired)
    try:
        workflow = args.workflow.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read {args.workflow}: {exc}")
    else:
        errors.extend(validate_sequencing(workflow, args.evidence.exists()))
    if args.evidence.exists():
        try:
            evidence = _load(args.evidence)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            errors.extend(compare_evidence(desired, evidence))
    elif (
        desired.get("control_status") == "decommissioned"
        and not args.require_live_evidence
    ):
        # The only way to legitimately run without evidence: an explicit,
        # reviewable edit to the committed contract in the same commit.
        pass
    else:
        # Unconditional by default. Gating this on --require-live-evidence or on
        # _has_publishable_hook_pack (still False while no user-capable pack
        # ships hooks) meant a commit deleting the evidence file re-legalized the
        # generic-Actions publisher with every gate green — exactly what AC36
        # clause 4 forbids.
        errors.append(
            f"live evidence is required but absent: {args.evidence}. To stand "
            "the control down, set control_status: decommissioned in the "
            "desired-state file in the same commit"
        )

    for error in errors:
        print(f"lint-claude-plugin-publish-control: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
