#!/usr/bin/env python3
"""Mutation tests for the Claude-plugin publication-control lint."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

SCRIPT = Path(__file__).with_name("lint-claude-plugin-publish-control.py")
SPEC = importlib.util.spec_from_file_location("publish_control_lint", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)

TEST_NOW = datetime(2026, 8, 28, tzinfo=UTC)


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
        # Re-enabling self-review prevention reintroduces the deadlock the
        # ADR-0079 erratum of 2026-08-12 records: the sole reviewer is always
        # the triggering actor, so no publication is approvable by anyone.
        "desired self-review policy": (
            ("environment", "prevent_self_review"),
            True,
        ),
        "desired canary result": (
            ("canary", "ordinary_update"),
            "accepted",
        ),
        # The subject the controls are authored for. An unset, empty, or
        # traversal-shaped value would let the evidence comparison below bind to
        # nothing while still comparing equal.
        "desired repo emptied": (("repo",), ""),
        "desired repo not owner/name": (("repo",), "agent-ready-repo"),
        "desired repo dot segment": (("repo",), "owner/.."),
        "desired schema version": (("version",), 1),
    }
    # Behaviour, not identity: __module__ is assigned by the loader from the
    # name _load_capture_module passes, so ANY file at that path satisfies a
    # name comparison -- including a two-line stub whose _validate_repo returns
    # its argument unchanged. Exercise the rule's two halves instead.
    _shared_rule = lint._load_capture_module()._validate_repo
    for label, value, accepted in (
        ("a dot segment", "owner/..", False),
        ("a leading-dot repository name", "owner/.github", True),
        ("a bare name with no owner", "agent-ready-repo", False),
    ):
        try:
            _shared_rule(value)
        except Exception:  # noqa: BLE001 - CaptureError, whatever the module names it
            got = False
        else:
            got = True
        check(
            f"the shared owner/name rule {'accepts' if accepted else 'rejects'} {label}",
            got is accepted,
        )
    # Blocker 2: the loop above pins the CAPTURE TOOL's rule, not the linter's
    # USE of it -- a locally restated regex in validate_desired would leave it
    # green. Swap the loader for a permissive stub and assert validate_desired
    # then ACCEPTS what the real rule rejects: only a linter that actually calls
    # the loaded module can change its answer.
    _real_loader = lint._load_capture_module

    class _PermissiveCapture:
        class CaptureError(RuntimeError):
            pass

        @staticmethod
        def _validate_repo(repo):
            return repo

    lint._load_capture_module = lambda: _PermissiveCapture
    try:
        bare = copy.deepcopy(desired)
        bare["repo"] = "agent-ready-repo"          # no owner: the real rule refuses
        delegated = not any("owner/name" in e for e in lint.validate_desired(bare))
    finally:
        lint._load_capture_module = _real_loader
    check(
        "validate_desired delegates to the loaded rule rather than a local copy",
        delegated,
    )
    # And a loader that cannot produce a usable module is a lint error, not a
    # traceback out of validate_desired.
    lint._load_capture_module = _real_loader
    for label, stub in (
        ("raises", lambda: (_ for _ in ()).throw(ValueError("boom"))),
        ("returns a module with no _validate_repo", lambda: object()),
    ):
        lint._load_capture_module = stub
        try:
            errs = lint.validate_desired(copy.deepcopy(desired))
            ok = bool(errs)
        except Exception:  # noqa: BLE001
            ok = False
        finally:
            lint._load_capture_module = _real_loader
        check(f"a capture module that {label} is reported, not raised", ok)

    check(
        "a desired file with no repo at all fails",
        bool(lint.validate_desired({k: v for k, v in desired.items() if k != "repo"})),
    )
    for name, (path, value) in desired_mutations.items():
        changed = copy.deepcopy(desired)
        cursor = changed
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        check(f"mutated {name} fails", bool(lint.validate_desired(changed)))

    evidence = copy.deepcopy(desired)
    evidence.update(
        {
            "identities_agree": True,
            "observed_at": "2026-08-10T00:00:00Z",
            "observation_source": "github-api-sanitized",
        }
    )
    check(
        "matching independent evidence passes",
        not lint.compare_evidence(desired, evidence, now_utc=TEST_NOW),
    )

    def freshness_result(observed_at: str) -> tuple[list[str], list[str]]:
        changed = copy.deepcopy(evidence)
        changed["observed_at"] = observed_at
        warnings: list[str] = []
        errors = lint.compare_evidence(
            desired, changed, now_utc=TEST_NOW, warnings=warnings
        )
        return errors, warnings

    fresh_errors, fresh_warnings = freshness_result("2026-08-27T00:00:00Z")
    check(
        "fresh evidence has no warning or error", not fresh_errors and not fresh_warnings
    )
    warn_errors, warn_warnings = freshness_result("2026-07-28T00:00:00Z")
    check(
        "31-day-old evidence warns without an error",
        not warn_errors and bool(warn_warnings),
    )
    fail_errors, fail_warnings = freshness_result("2026-05-29T00:00:00Z")
    check("91-day-old evidence fails", bool(fail_errors) and not fail_warnings)
    malformed_errors, _ = freshness_result("not-a-timestamp")
    check("non-ISO observed_at fails", bool(malformed_errors))
    naive_errors, _ = freshness_result("2026-08-10T00:00:00")
    check("naive observed_at fails without a TypeError", bool(naive_errors))
    future_errors, _ = freshness_result("2026-08-29T00:00:00Z")
    check("future-dated evidence fails", bool(future_errors))

    mutations = {
        "bypass actor": ("branch", "bypass", "actor_type", "OrganizationAdmin"),
        "exact target": ("branch", "target", None, "refs/heads/main"),
        "environment branch": ("environment", "deployment_branches", None, ["*"]),
        "reviewer policy": ("environment", "required_reviewers", None, 0),
        "ordinary canary": ("canary", "ordinary_update", None, "accepted"),
        "app canary": ("canary", "publisher_app_update", None, "rejected"),
    }
    # Evidence captured against a DIFFERENT, well-configured repository is
    # byte-indistinguishable from a real capture in every other field — this
    # comparison is the only thing that separates them.
    for label, value in (
        ("another repository", "someone-else/agent-ready-repo"),
        ("None", None),
    ):
        changed = copy.deepcopy(evidence)
        changed["repo"] = value
        check(
            f"evidence naming {label} fails",
            bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
        )
    changed = copy.deepcopy(evidence)
    changed.pop("repo")
    check(
        "evidence with no repo at all fails",
        bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
    )
    # Both keys absent compare EQUAL, so without a self-standing check the
    # binding would rest on validate_desired happening to run first.
    stripped_desired = {k: v for k, v in desired.items() if k != "repo"}
    check(
        "evidence and desired BOTH missing repo still fails",
        bool(lint.compare_evidence(stripped_desired, changed, now_utc=TEST_NOW)),
    )
    # The schema-version comparison is the only thing that rejects a stale v1
    # artifact against the v2 desired file -- the migration this change makes.
    changed = copy.deepcopy(evidence)
    changed["version"] = 1
    check(
        "stale v1 evidence against a v2 desired control fails",
        bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
    )

    # --subject: the one half of the binding a fork or clone cannot satisfy,
    # because github.repository is set by the runner, not by a committed file.
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        desired_path = root / "desired.json"
        desired_path.write_text(json.dumps(desired), encoding="utf-8")
        evidence_path = root / "evidence.json"
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        base = [
            "--desired", str(desired_path),
            "--evidence", str(evidence_path),
            "--workflow", str(lint.WORKFLOW_PATH),
        ]
        for label, subject, expected in (
            ("no --subject is accepted (make build-check passes none)", None, 0),
            ("the declared subject is accepted", desired["repo"], 0),
            ("a fork's subject is refused", "someone-else/agent-ready-repo", 1),
            ("an empty subject is refused", "", 1),
        ):
            argv = list(base) if subject is None else [*base, "--subject", subject]
            check(
                f"--subject: {label}", lint.main(argv, now_utc=TEST_NOW) == expected
            )

        warning_evidence = copy.deepcopy(evidence)
        warning_evidence["observed_at"] = "2026-07-28T00:00:00Z"
        evidence_path.write_text(json.dumps(warning_evidence), encoding="utf-8")
        check(
            "31-day warning does not change the lint exit code",
            lint.main(base, now_utc=TEST_NOW) == 0,
        )
    for name, (group, key, nested, value) in mutations.items():
        changed = copy.deepcopy(evidence)
        if nested is None:
            changed[group][key] = value
        else:
            changed[group][key][nested] = value
        check(
            f"mutated {name} fails",
            bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
        )

    for label, mutate in (
        ("absent", lambda e: e.pop("identities_agree")),
        ("false", lambda e: e.update(identities_agree=False)),
        ("truthy-but-not-true", lambda e: e.update(identities_agree="yes")),
    ):
        changed = copy.deepcopy(evidence)
        mutate(changed)
        check(
            f"identities_agree {label} fails",
            bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
        )

    for label, path in (
        ("app id", ("app", "id")),
        ("bypass actor_id", ("branch", "bypass", "actor_id")),
        ("environment app_id_value", ("environment", "app_id_value")),
    ):
        changed = copy.deepcopy(evidence)
        cursor = changed
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = 4242424
        check(
            f"a leaked {label} fails",
            bool(lint.compare_evidence(desired, changed, now_utc=TEST_NOW)),
        )
    check(
        "a nested identifier anywhere is caught by the walk",
        bool(lint._identifier_leaks({"a": {"b": [{"node_id": "x"}]}})),
    )
    check(
        "a clean evidence body reports no leaks",
        not lint._identifier_leaks(evidence),
    )

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
        "          app-id: ${{ vars.CLAUDE_PLUGIN_PUBLISHER_APP_ID }}\n"
        "          private-key: ${{ secrets.CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY }}\n"
        "          permission-contents: write\n"
        "          CLAUDE_PLUGIN_PUBLISH_TOKEN: "
        "${{ steps.publisher-token.outputs.token }}\n"
        "      - uses: actions/checkout@" + "0" * 40 + "\n"
        "        persist-credentials: false\n"
    )
    interim_workflow = (
        "permissions:\n  contents: write\n"
        "          CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
        "      - uses: actions/checkout@" + "0" * 40 + "\n"
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
            interim_workflow.replace("        persist-credentials: false\n", "", 1),
            False,
        ))
        and bool(lint.validate_sequencing(
            app_workflow.replace("        persist-credentials: false\n", "", 1),
            True,
        )),
    )

    partial_app = (
        "permissions:\n  contents: read\n"
        "    environment: claude-plugin-publish\n"
        "          CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.MY_PAT }}\n"
        "      - uses: actions/checkout@" + "0" * 40 + "\n"
        "        persist-credentials: false\n"
    )
    check(
        "a partial app identity is detected as incomplete-app",
        lint.detect_publisher_mode(partial_app) == "incomplete-app",
    )
    check(
        "a partial app identity fails sequencing in both provisioning states",
        bool(lint.validate_sequencing(partial_app, True))
        and bool(lint.validate_sequencing(partial_app, False)),
    )
    check(
        "a quoted write grant is caught alongside the app identity",
        bool(lint.validate_sequencing(
            app_workflow.replace(
                "permissions:\n  contents: read\n",
                "permissions:\n  contents: read\n    permissions:\n"
                "      contents: 'write'\n",
            ),
            True,
        )),
    )
    check(
        "a flow-style write grant is caught",
        bool(lint.WRITE_GRANT.search("permissions: { contents: write }\n")),
    )
    check(
        "the token step's permission-contents is not read as a write grant",
        not lint.WRITE_GRANT.search("          permission-contents: write\n"),
    )
    check(
        "a commented-out persist-credentials does not satisfy the check",
        bool(lint.validate_sequencing(
            interim_workflow.replace(
                "        persist-credentials: false\n",
                "      # persist-credentials: false is set below\n",
            ),
            False,
        )),
    )
    check(
        "a second checkout without the option fails",
        bool(lint.validate_sequencing(
            interim_workflow + "      - uses: actions/checkout@" + "1" * 40 + "\n",
            False,
        )),
    )
    check(
        "a workflow with no checkout step fails",
        bool(lint.validate_sequencing(
            "permissions:\n  contents: write\n"
            "          CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n",
            False,
        )),
    )
    for key in ("app_id", "login", "email", "token", "surprise_field"):
        check(
            f"a top-level {key} in evidence fails",
            bool(lint._identifier_leaks({key: "x"})),
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
        # Deleting the evidence file must NOT re-legalize the interim
        # publisher: that is the mode switch AC36 clause 4 forbids.
        workflow_path.write_text(interim_workflow, encoding="utf-8")
        check(
            "lint CLI refuses missing evidence even for the interim workflow",
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
        # The one legal no-evidence state: an explicit, reviewable opt-out in
        # the committed contract, paired with the interim identity.
        decommissioned = copy.deepcopy(desired)
        decommissioned["control_status"] = "decommissioned"
        decom_path = root / "decommissioned.json"
        decom_path.write_text(json.dumps(decommissioned), encoding="utf-8")
        check(
            "decommissioned contract + interim workflow is accepted",
            lint.main(
                [
                    "--desired", str(decom_path),
                    "--evidence", str(root / "absent.json"),
                    "--root", str(root),
                    "--workflow", str(workflow_path),
                ]
            )
            == 0,
        )
        app_path = root / "app.yml"
        app_path.write_text(app_workflow, encoding="utf-8")
        check(
            "decommissioned contract still refuses the app workflow",
            lint.main(
                [
                    "--desired", str(decom_path),
                    "--evidence", str(root / "absent.json"),
                    "--root", str(root),
                    "--workflow", str(app_path),
                ]
            )
            == 1,
        )
        check(
            "--require-live-evidence overrides the decommission opt-out",
            lint.main(
                [
                    "--desired", str(decom_path),
                    "--evidence", str(root / "absent.json"),
                    "--root", str(root),
                    "--workflow", str(workflow_path),
                    "--require-live-evidence",
                ]
            )
            == 1,
        )

    if failures:
        print(f"test-lint-claude-plugin-publish-control: FAIL ({len(failures)})")
        return 1
    print("test-lint-claude-plugin-publish-control: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
