#!/usr/bin/env python3
"""Validate desired and observed controls for Claude-plugin publication."""

from __future__ import annotations

import argparse
import importlib.util
import json
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
INTERIM_IDENTITY_MARKERS = (
    "CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
)


def detect_publisher_mode(workflow: str) -> str:
    """Classify the publisher workflow's authentication identity.

    Returns ``app`` (ADR-0079 end state), ``interim`` (generic Actions app),
    ``mixed`` when both shapes appear, or ``unknown`` when neither does. The
    last two are always violations: a publisher that names two identities, or
    none, cannot be reasoned about by the sequencing rule below.
    """
    has_app = any(marker in workflow for marker in APP_IDENTITY_MARKERS)
    has_interim = any(marker in workflow for marker in INTERIM_IDENTITY_MARKERS)
    if has_app and has_interim:
        return "mixed"
    if has_app:
        return "app"
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
    if "contents: write" in workflow and mode == "app":
        errors.append(
            "App-token publisher must keep GITHUB_TOKEN read-only"
        )
    if "persist-credentials: false" not in workflow:
        errors.append(
            "publisher checkout must not persist ambient credentials in either "
            "identity mode"
        )
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
        "permissions": {"contents": "write"},
    }
    if app != expected_app:
        errors.append("publisher app must be repository-scoped with only contents:write")

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
        branch_without_id = json.loads(json.dumps(observed_branch))
        observed_bypass = branch_without_id.get("bypass", {})
        bypass_actor_id = (
            observed_bypass.pop("actor_id", None)
            if isinstance(observed_bypass, dict)
            else None
        )
        app_without_id = dict(observed_app)
        app_id = app_without_id.pop("id", None)
        environment_without_id = dict(observed_environment)
        environment_app_id = environment_without_id.pop("app_id_value", None)
        if branch_without_id != desired.get("branch"):
            errors.append("evidence branch differs from desired control")
        if app_without_id != desired.get("app"):
            errors.append("evidence app differs from desired control")
        if environment_without_id != desired.get("environment"):
            errors.append("evidence environment differs from desired control")
        normalized_ids = {str(value) for value in (bypass_actor_id, app_id, environment_app_id)}
        if None in (bypass_actor_id, app_id, environment_app_id) or len(normalized_ids) != 1:
            errors.append(
                "ruleset bypass, app installation, and environment variable "
                "must identify the same publisher App ID"
            )
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
    elif args.require_live_evidence or _has_publishable_hook_pack(args.root):
        errors.append(f"live evidence is required but absent: {args.evidence}")

    for error in errors:
        print(f"lint-claude-plugin-publish-control: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
