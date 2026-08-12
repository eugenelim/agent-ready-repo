#!/usr/bin/env python3
"""Construction tests for tools/catalogue/publish_claude_plugins.py.

That script's `_assert_membership` is the only runtime check standing between a
`git push` and a public marketplace: the publish job triggers on `push: main`
with `contents: write` and declares no `needs:` on the build-check job, so
nothing else in CI gates it. It shipped untested.

Every case builds synthetic `packs/` and `dist/` trees under a temp root, so
none of the three refusals is confused with a real-repo condition.
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    "publish_claude_plugins",
    Path(__file__).parent / "catalogue" / "publish_claude_plugins.py",
)
pub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pub)

FAILURES: list[str] = []
_PUBLISH_FORBIDDEN = (
    "claude-plugin-publish",
    "CLAUDE_PLUGIN_PUBLISHER_APP_ID",
    "CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY",
    "tools/catalogue/publish_claude_plugins.py",
    "claude-plugins-dist",
)


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _workflow_offenders(
    workflow_texts: dict[Path, str], publisher_path: Path
) -> list[str]:
    """Return forbidden publisher-boundary references outside its workflow."""
    return [
        f"{path.name}:{needle}"
        for path, workflow_text in workflow_texts.items()
        if path != publisher_path
        for needle in _PUBLISH_FORBIDDEN
        if needle in workflow_text
    ]


def _source_pack(
    root: Path,
    slug: str,
    *,
    user: bool,
    hooks: bool = False,
    consent: bool = False,
) -> None:
    d = root / "packs" / slug
    (d / ".claude-plugin").mkdir(parents=True)
    scopes = '["repo", "user"]' if user else '["repo"]'
    pack_toml = (
        f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "0.3"\n'
        f'[pack.install]\ndefault-scope = "repo"\nallowed-scopes = {scopes}\n'
    )
    if consent:
        pack_toml += "user-scope-hooks = true\n"
    (d / "pack.toml").write_text(
        pack_toml,
        encoding="utf-8", newline="\n")
    (d / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": slug, "version": "1.0.0"}), encoding="utf-8", newline="\n")
    if hooks:
        hook_dir = d / ".apm" / "hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "run.sh").write_text("exit 0\n", encoding="utf-8", newline="\n")


def _root_marketplace(root: Path, names) -> None:
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": n} for n in names]}),
        encoding="utf-8", newline="\n")


def _in(root: Path, fn, *args):
    """Run `fn` with cwd at `root` — the script resolves relative paths."""
    prev = Path.cwd()
    os.chdir(root)
    try:
        return fn(*args)
    finally:
        os.chdir(prev)


def _refuses(root: Path, published_dirs, marketplace_names) -> str | None:
    try:
        _in(root, pub._assert_membership, set(published_dirs), set(marketplace_names))
    except SystemExit as exc:
        return str(exc)
    return None


def main() -> int:
    print("test-publish-claude-plugins:")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        _root_marketplace(root, ["userpack"])
        _check("a consistent set passes",
               _refuses(root, ["userpack"], ["userpack"]) is None,
               f"got {_refuses(root, ['userpack'], ['userpack'])}")

        # Refusal 1: a stale dist/ directory for a pack the source no longer
        # publishes. `make build` has no `clean` dependency, so this survives.
        msg = _refuses(root, ["userpack", "gonepack"], ["userpack", "gonepack"])
        _check("a stale/unpublishable directory refuses",
               msg is not None and "gonepack" in msg, f"got {msg}")

        # Refusal 1b: the pack is *present* in the source and simply repo-only.
        # Refusal 1 is driven by an absent pack, so it survives deleting the
        # scope branch in `_publishable_from_source`; this case does not.
        _source_pack(root, "repopack", user=False)
        msg = _refuses(root, ["userpack", "repopack"], ["userpack", "repopack"])
        _check("a present-but-repo-only pack refuses on scope",
               msg is not None and "repopack" in msg, f"got {msg}")

        _source_pack(root, "unconsented", user=True, hooks=True)
        msg = _refuses(
            root,
            ["userpack", "unconsented"],
            ["userpack", "unconsented"],
        )
        _check("a hook pack without user-scope consent refuses",
               msg is not None and "unconsented" in msg, f"got {msg}")

        _source_pack(root, "consented", user=True, hooks=True, consent=True)
        _check("a hook pack with user-scope consent remains publishable",
               _refuses(root, ["userpack", "consented"],
                        ["userpack", "consented"]) is None,
               "consent should lift Rail B")

        # Refusal 2: an entry whose directory is absent — a dangling fetch for
        # every adopter, which is the defect the spec opens on.
        msg = _refuses(root, ["userpack"], ["userpack", "ghost"])
        _check("a dangling marketplace entry refuses",
               msg is not None and "ghost" in msg, f"got {msg}")

        # Refusal 3: a published directory nobody lists. `orphan` must exist
        # in the source and be user-capable, or refusal 1 (`stale`) fires
        # first and this case passes without ever reaching refusal 3 — it did,
        # and deleting `orphaned` outright left the whole file green.
        # Assert the message, not just the slug, for the same reason.
        _source_pack(root, "orphan", user=True)
        msg = _refuses(root, ["userpack", "orphan"], ["userpack"])
        _check("an unlisted published directory refuses",
               msg is not None and "orphan" in msg
               and "no marketplace entry" in msg, f"got {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        # The root marketplace must not advertise what the branch does not carry.
        _root_marketplace(root, ["userpack", "notonbranch"])
        msg = _refuses(root, ["userpack"], ["userpack"])
        _check("a root entry the branch lacks refuses",
               msg is not None and "notonbranch" in msg, f"got {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _source_pack(root, "userpack", user=True)
        _source_pack(root, "catalogue-curation", user=True)
        # The root marketplace *file* must carry `catalogue-curation`: it is the
        # only input the load-bearing `- EXCLUDE` subtracts from, and
        # `_assert_membership` reads it from disk rather than taking it as an
        # argument. Without it the assertion passed with the exemption deleted,
        # which is the one thing it exists to catch.
        _root_marketplace(root, ["userpack", "catalogue-curation"])
        # EXCLUDE is applied first and is exempt: catalogue-curation is
        # operator-only, a different reason from being repo-only, and folding
        # the two would re-publish it if its scopes were ever widened. The
        # branch legitimately does not carry it, so without the exemption this
        # reads as "the root advertises a pack the branch lacks".
        _check("the operator-only exclusion is exempt from the refusals",
               _refuses(root, ["userpack"], ["userpack"]) is None,
               "EXCLUDE must be applied before the membership assertion")

    _check("catalogue-curation is still the only name exclusion",
           {"catalogue-curation"} == pub.EXCLUDE, f"got {pub.EXCLUDE}")

    # Publisher authentication is environment-only and non-persistent. The
    # raw token must not survive into argv, remote URLs, output, or exceptions.
    token = "fixture-secret-token"
    auth_env = pub._git_auth_env({pub.TOKEN_ENV: token, "PATH": os.environ["PATH"]})
    _check("raw publisher token is removed from the child environment",
           pub.TOKEN_ENV not in auth_env
           and all(token not in str(value) for value in auth_env.values()),
           f"keys: {sorted(auth_env)}")
    _check("git auth is supplied through an extra-header environment value",
           auth_env.get("GIT_CONFIG_KEY_0") == "http.https://github.com/.extraheader"
           and auth_env.get("GIT_CONFIG_COUNT") == "1",
           f"got {auth_env}")
    try:
        pub._git_auth_env({})
    except SystemExit as exc:
        missing_message = str(exc)
    else:
        missing_message = ""
    _check("missing token refuses before remote access",
           "before remote access" in missing_message and token not in missing_message,
           f"got {missing_message!r}")
    output = io.StringIO()
    with mock.patch.object(
        pub.subprocess,
        "run",
        side_effect=pub.subprocess.CalledProcessError(1, ["git", "push", "origin"]),
    ):
        try:
            with contextlib.redirect_stdout(output):
                pub._run(["git", "push", "origin"], env=auth_env)
        except pub.subprocess.CalledProcessError as exc:
            exception_text = str(exc)
        else:
            exception_text = ""
    _check("publisher auth is absent from logs and subprocess exceptions",
           token not in output.getvalue() and token not in exception_text,
           f"stdout={output.getvalue()!r}; exception={exception_text!r}")
    with mock.patch.object(
        pub.subprocess,
        "check_output",
        return_value="https://github.com/example/project.git\n",
    ):
        _check("HTTPS GitHub origin is accepted",
               pub._assert_https_github_origin().endswith("project.git"))
    for unsafe_origin in (
        "git@github.com:example/project.git\n",
        "https://token@github.com/example/project.git\n",
        "https://example.com/example/project.git\n",
    ):
        with mock.patch.object(
            pub.subprocess, "check_output", return_value=unsafe_origin
        ):
            try:
                pub._assert_https_github_origin()
            except SystemExit:
                refused = True
            else:
                refused = False
        _check(f"unsafe origin {unsafe_origin.strip()!r} is refused", refused)

    # Offline workflow construction gate. It intentionally scans every
    # workflow so a second token-bearing or dist-writing workflow cannot hide
    # outside the publisher file.
    repo_root = Path(__file__).resolve().parents[1]
    workflow_dir = repo_root / ".github" / "workflows"
    workflows = sorted(
        set(workflow_dir.glob("*.yml")) | set(workflow_dir.glob("*.yaml"))
    )
    publisher_path = repo_root / ".github" / "workflows" / "publish-claude-plugins.yml"
    publisher = publisher_path.read_text(encoding="utf-8")

    # AC36 — the asserted shape follows the provisioning state, because
    # asserting the end-state shape unconditionally is exactly how an
    # unauthenticatable publisher stayed green for eight consecutive commits.
    # Provisioning is read from the committed evidence file only; this suite is
    # hermetic and must never reach the network to decide which shape is legal.
    evidence_path = (
        repo_root / "docs" / "specs" / "claude-plugin-hook-parity"
        / "publish-control-evidence.json"
    )
    provisioned = evidence_path.exists()
    _control_spec = importlib.util.spec_from_file_location(
        "lint_claude_plugin_publish_control",
        repo_root / "tools" / "lint-claude-plugin-publish-control.py",
    )
    control = importlib.util.module_from_spec(_control_spec)
    _control_spec.loader.exec_module(control)

    expected_mode = "app" if provisioned else "interim"
    _check("publisher identity matches the provisioning state",
           control.detect_publisher_mode(publisher) == expected_mode,
           f"expected {expected_mode} identity, got "
           f"{control.detect_publisher_mode(publisher)}")
    _check("the live publisher satisfies its own sequencing rule",
           not control.validate_sequencing(publisher, provisioned),
           f"got {control.validate_sequencing(publisher, provisioned)}")

    # Both mutation directions, independent of which state the repo is in now.
    app_shape = (
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
    interim_shape = (
        "permissions:\n  contents: write\n"
        "          CLAUDE_PLUGIN_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
        "      - uses: actions/checkout@" + "0" * 40 + "\n"
        "        persist-credentials: false\n"
    )
    _check("minting an app token without provisioning evidence is refused",
           bool(control.validate_sequencing(app_shape, False)),
           "an unauthenticatable publisher passed the sequencing rule")
    _check("keeping the interim identity after provisioning is refused",
           bool(control.validate_sequencing(interim_shape, True)),
           "the generic Actions app survived the app-only rollout")
    _check("a publisher naming both identities is refused",
           bool(control.validate_sequencing(app_shape + interim_shape, False))
           and bool(control.validate_sequencing(app_shape + interim_shape, True)),
           "a two-identity publisher was accepted")
    _check("a publisher naming no identity is refused",
           bool(control.validate_sequencing("permissions:\n  contents: read\n", False)),
           "an identity-less publisher was accepted")

    if provisioned:
        _check("publisher GITHUB_TOKEN is read-only",
               re.search(r"(?m)^permissions:\n  contents: read$", publisher)
               is not None
               and re.search(
                   r"(?m)^\s+contents:\s+write\s*(?:#.*)?$", publisher
               ) is None,
               "publisher must not grant the generic Actions app write access")
        _check("publisher uses the protected environment",
               "environment: claude-plugin-publish" in publisher,
               "environment missing")
    else:
        _check("interim publisher carries no protected-environment reference",
               "environment: claude-plugin-publish" not in publisher,
               "interim publisher references an environment that holds no "
               "credentials, which blocks the job on a nonexistent approval")
        _check("interim publisher mints no app token",
               "uses: actions/create-github-app-token@" not in publisher,
               "interim publisher would mint a token it has no key for")
    _check("checkout credentials are not persisted",
           "persist-credentials: false" in publisher,
           "checkout would leave ambient credentials")
    uses_refs = re.findall(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)", publisher)
    _check("every external publisher action is full-SHA pinned",
           bool(uses_refs) and all(
               re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) for ref in uses_refs
           ), f"got {uses_refs}")
    # Match the executed step, not a prose mention: the header comment names
    # this script too, and a `find` on the bare path would score the comment.
    control_gate = publisher.find(
        "run: python3 tools/lint-claude-plugin-publish-control.py"
    )
    _check("the publication-control gate is an executed step",
           control_gate >= 0,
           "control state is never verified during publication")
    if provisioned:
        token_mint = publisher.find(
            "name: Mint repository-scoped publisher token"
        )
        _check("publication-control lint runs before token minting",
               0 <= control_gate < token_mint,
               "publisher can mint credentials before control state is verified")
    # The token mapping is single-valued and bound to the final publish step in
    # both identities; only its source changes with the mode.
    token_source = (
        "${{ steps.publisher-token.outputs.token }}" if provisioned
        else "${{ secrets.GITHUB_TOKEN }}"
    )
    _check("the publish token reaches only the final publisher step",
           publisher.count(token_source) == 1
           and re.search(
               r"name: Publish to claude-plugins-dist branch[\s\S]*?"
               r"CLAUDE_PLUGIN_PUBLISH_TOKEN: " + re.escape(token_source),
               publisher,
           ) is not None,
           "publish token is missing, duplicated, or attached to an earlier step")
    workflow_texts = {
        path: path.read_text(encoding="utf-8")
        for path in workflows
    }
    offenders = _workflow_offenders(workflow_texts, publisher_path)
    _check("no other workflow can invoke or authenticate the dist publisher",
           not offenders, f"got {offenders}")
    yaml_mutation = dict(workflow_texts)
    yaml_mutation[workflow_dir / "backdoor.yaml"] = (
        "jobs:\n  publish:\n    environment: claude-plugin-publish\n"
    )
    _check("a forbidden .yaml workflow turns the construction gate red",
           bool(_workflow_offenders(yaml_mutation, publisher_path)),
           "the workflow suffix or forbidden reference was ignored")

    # The refusals above drive `_assert_membership` directly, so deleting its
    # single call from `main()` leaves every one of them green — and that call
    # is the only runtime check between `git push` and a public marketplace.
    # Pin the call site structurally, not by substring — and by *reachability*,
    # not mere presence: `ast.walk` descends into `if False:` and into code
    # below an unconditional `return`, so a walk-anywhere check reads a dead
    # call as wired. Require the call at statement position in a block that is
    # entered unconditionally, with no unconditional exit above it.
    src = Path(pub.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    main_fn = next((n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "main"), None)

    def _reachable_call(body: list[ast.stmt]) -> bool:
        """Statement-position call in `body`, before any unconditional exit.

        Descends only into `with`/`try` bodies — blocks whose statements run
        without a condition. `if`/`while`/`else` are deliberately not followed:
        a call reachable only under a condition is not a wired call site.
        """
        for stmt in body:
            if isinstance(stmt, (ast.Return, ast.Raise)):
                return False
            if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "_assert_membership"):
                return True
            if isinstance(stmt, ast.With) and _reachable_call(stmt.body):
                return True
            if isinstance(stmt, ast.Try) and _reachable_call(stmt.body):
                return True
        return False

    called = main_fn is not None and _reachable_call(main_fn.body)
    _check("main() reaches _assert_membership unconditionally", called,
           "the membership refusal is defined but never reached — publishing "
           "would push whatever the build produced")

    def _top_level_call_index(name: str) -> int | None:
        if main_fn is None:
            return None
        for index, stmt in enumerate(main_fn.body):
            value = stmt.value if isinstance(stmt, (ast.Expr, ast.Assign)) else None
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == name
            ):
                return index
        return None

    origin_guard = _top_level_call_index("_assert_https_github_origin")
    remote_probe = _top_level_call_index("_check")
    _check(
        "main() refuses non-HTTPS origins before its first remote probe",
        origin_guard is not None
        and remote_probe is not None
        and origin_guard < remote_probe,
        f"origin_guard={origin_guard}; remote_probe={remote_probe}",
    )

    if FAILURES:
        print(f"test-publish-claude-plugins: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-publish-claude-plugins: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
