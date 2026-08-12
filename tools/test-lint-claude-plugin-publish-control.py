#!/usr/bin/env python3
"""Mutation tests for the Claude-plugin publication-control lint."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("lint-claude-plugin-publish-control.py")
SPEC = importlib.util.spec_from_file_location("publish_control_lint", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)


def main() -> int:
    desired = json.loads(lint.DESIRED_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        print(f"  {'ok  ' if condition else 'FAIL'} {name}")
        if not condition:
            failures.append(name)

    check("desired state is internally valid", not lint.validate_desired(desired))
    desired_mutations = {
        "desired target branch": (
            ("branch", "target"),
            "refs/heads/main",
        ),
        "desired bypass actor": (
            ("branch", "bypass", "actor_type"),
            "OrganizationAdmin",
        ),
        "desired app permissions": (
            ("app", "permissions", "contents"),
            "read",
        ),
        "desired environment reviewer": (
            ("environment", "required_reviewers"),
            0,
        ),
        "desired canary result": (
            ("canary", "ordinary_update"),
            "accepted",
        ),
    }
    for name, (path, value) in desired_mutations.items():
        changed = copy.deepcopy(desired)
        cursor = changed
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        check(f"mutated {name} fails", bool(lint.validate_desired(changed)))

    evidence = copy.deepcopy(desired)
    evidence["branch"]["bypass"]["actor_id"] = 12345
    evidence["app"]["id"] = 12345
    evidence["environment"]["app_id_value"] = "12345"
    evidence.update(
        {
            "observed_at": "2026-08-10T00:00:00Z",
            "observation_source": "github-api-sanitized",
        }
    )
    check("matching independent evidence passes", not lint.compare_evidence(desired, evidence))

    mutations = {
        "bypass actor": ("branch", "bypass", "actor_id", 67890),
        "exact target": ("branch", "target", None, "refs/heads/main"),
        "environment branch": ("environment", "deployment_branches", None, ["*"]),
        "reviewer policy": ("environment", "required_reviewers", None, 0),
        "ordinary canary": ("canary", "ordinary_update", None, "accepted"),
        "app canary": ("canary", "publisher_app_update", None, "rejected"),
    }
    for name, (group, key, nested, value) in mutations.items():
        changed = copy.deepcopy(evidence)
        if nested is None:
            changed[group][key] = value
        else:
            changed[group][key][nested] = value
        check(f"mutated {name} fails", bool(lint.compare_evidence(desired, changed)))

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        desired_path = root / "desired.json"
        evidence_path = root / "missing.json"
        desired_path.write_text(json.dumps(desired), encoding="utf-8")
        check(
            "required absent evidence fails",
            lint.main(
                [
                    "--desired",
                    str(desired_path),
                    "--evidence",
                    str(evidence_path),
                    "--require-live-evidence",
                ]
            )
            == 1,
        )
        pack = root / "packs" / "hook-pack"
        (pack / ".claude-plugin").mkdir(parents=True)
        (pack / ".apm" / "hooks").mkdir(parents=True)
        (pack / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (pack / ".apm" / "hooks" / "run.py").write_text("pass\n", encoding="utf-8")
        (pack / "pack.toml").write_text(
            "[pack]\n"
            'name = "hook-pack"\n'
            'version = "0.1.0"\n'
            "[pack.adapter-contract]\n"
            'version = "0.18"\n'
            "[pack.install]\n"
            'default-scope = "user"\n'
            'allowed-scopes = ["user"]\n'
            "user-scope-hooks = true\n",
            encoding="utf-8",
        )
        check(
            "publishable hook pack automatically requires live evidence",
            lint.main(
                [
                    "--desired",
                    str(desired_path),
                    "--evidence",
                    str(evidence_path),
                    "--root",
                    str(root),
                ]
            )
            == 1,
        )

    # AC36 — identity/provisioning sequencing, both directions.
    app_workflow = (
        "permissions:\n  contents: read\n"
        "    environment: claude-plugin-publish\n"
        "      - uses: actions/create-github-app-token@" + "0" * 40 + "\n"
        "        persist-credentials: false\n"
    )
    interim_workflow = (
        "permissions:\n  contents: write\n"
        "          CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
        "        persist-credentials: false\n"
    )
    check(
        "app identity is detected",
        lint.detect_publisher_mode(app_workflow) == "app",
    )
    check(
        "interim identity is detected",
        lint.detect_publisher_mode(interim_workflow) == "interim",
    )
    check(
        "a two-identity publisher is detected as mixed",
        lint.detect_publisher_mode(app_workflow + interim_workflow) == "mixed",
    )
    check(
        "an identity-less publisher is detected as unknown",
        lint.detect_publisher_mode("permissions:\n  contents: read\n") == "unknown",
    )
    check(
        "provisioned + app identity passes sequencing",
        not lint.validate_sequencing(app_workflow, True),
    )
    check(
        "unprovisioned + interim identity passes sequencing",
        not lint.validate_sequencing(interim_workflow, False),
    )
    check(
        "unprovisioned + app identity fails sequencing",
        bool(lint.validate_sequencing(app_workflow, False)),
    )
    check(
        "provisioned + interim identity fails sequencing",
        bool(lint.validate_sequencing(interim_workflow, True)),
    )
    check(
        "mixed identity fails sequencing in both provisioning states",
        bool(lint.validate_sequencing(app_workflow + interim_workflow, False))
        and bool(lint.validate_sequencing(app_workflow + interim_workflow, True)),
    )
    check(
        "a persisted-credential checkout fails in either identity",
        bool(lint.validate_sequencing(
            interim_workflow.replace("        persist-credentials: false\n", ""),
            False,
        ))
        and bool(lint.validate_sequencing(
            app_workflow.replace("        persist-credentials: false\n", ""),
            True,
        )),
    )

    # The sequencing rule reaches the CLI, not just the helper: a workflow that
    # cannot authenticate must turn the gate that runs inside the publish job red.
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        desired_path = root / "desired.json"
        desired_path.write_text(json.dumps(desired), encoding="utf-8")
        workflow_path = root / "publish.yml"
        workflow_path.write_text(app_workflow, encoding="utf-8")
        check(
            "lint CLI refuses an app-token workflow with no evidence",
            lint.main(
                [
                    "--desired",
                    str(desired_path),
                    "--evidence",
                    str(root / "absent.json"),
                    "--root",
                    str(root),
                    "--workflow",
                    str(workflow_path),
                ]
            )
            == 1,
        )
        workflow_path.write_text(interim_workflow, encoding="utf-8")
        check(
            "lint CLI accepts the interim workflow with no evidence",
            lint.main(
                [
                    "--desired",
                    str(desired_path),
                    "--evidence",
                    str(root / "absent.json"),
                    "--root",
                    str(root),
                    "--workflow",
                    str(workflow_path),
                ]
            )
            == 0,
        )

    if failures:
        print(f"test-lint-claude-plugin-publish-control: FAIL ({len(failures)})")
        return 1
    print("test-lint-claude-plugin-publish-control: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
