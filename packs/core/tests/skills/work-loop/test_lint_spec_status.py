#!/usr/bin/env python3
"""Pytest coverage for the Tier-1 spec-status lint.

Builds fixture spec trees in a tempdir and runs the linter as a
subprocess against the documented `python <skill>/scripts/lint-spec-status.py
--root <dir>` invocation — the same shape the CI gate uses.
Exercises the hard and warn-only invariants red-and-green, including the
lenient leading-token parse, the diff-triggered ship transition (with
real git base fixtures), the grandfather and no-base branches, and the
Acceptance-Criteria section opt-out.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
LINTER = SCRIPT_DIR / "lint-spec-status.py"

_AC_HEADER = "## Acceptance Criteria\n\n"


def write_spec(root: Path, name: str, status: str, acs: str) -> None:
    p = root / "docs" / "specs" / name / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# Spec: {name}\n\n- **Status:** {status}\n\n{_AC_HEADER}{acs}\n",
        encoding="utf-8",
    )


def write_workspace_backlog(root: Path, slugs: list[str]) -> None:
    p = root / "workspace.toml"
    if slugs:
        lines = "\n".join(f'  {{slug = "{s}"}},' for s in slugs)
        body = f"[backlog]\nopen = [\n{lines}\n]\n"
    else:
        body = "[backlog]\nopen = []\n"
    p.write_text(body, encoding="utf-8")


def run_lint(
    root: Path, base_ref: str | None = None, all_specs: bool = False
) -> tuple[int, str, str]:
    """Run the CLI from the temporary repository that owns ``root``."""
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    argv = [sys.executable, str(LINTER), "--root", str(root)]
    if base_ref is not None:
        argv += ["--base-ref", base_ref]
    if all_specs:
        argv.append("--all")
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(root))
    return proc.returncode, proc.stdout, proc.stderr


@contextmanager
def best_effort_tempdir() -> Iterator[str]:
    """Yield a new-test tempdir despite this sandbox's rmdir restriction."""
    tmp = tempfile.mkdtemp()
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def load_linter_module() -> types.ModuleType:
    """Load the core work-loop linter under a collision-proof module name."""
    spec = importlib.util.spec_from_file_location(
        "core_work_loop_lint_spec_status", LINTER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    stdout = sys.stdout
    stderr = sys.stderr
    stdout_config = (stdout.encoding, stdout.errors)
    stderr_config = (stderr.encoding, stderr.errors)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.stdout = stdout
        sys.stderr = stderr
        stdout.reconfigure(encoding=stdout_config[0], errors=stdout_config[1])
        stderr.reconfigure(encoding=stderr_config[0], errors=stderr_config[1])
    return module


def git_init_commit(root: Path) -> None:
    env_argv = [
        ["git", "-C", str(root), "init", "-q"],
        ["git", "-C", str(root), "add", "-A"],
        ["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "base"],
    ]
    for argv in env_argv:
        subprocess.run(argv, check=True, capture_output=True)


def expect(cond: bool, msg: str) -> None:
    """Assert a condition through pytest instead of aggregate state."""
    assert cond, msg


def symlink_or_skip(name: str, link: Path, target: Path | str) -> bool:
    """Create a required symlink, recording a real skip only outside CI."""
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        if os.environ.get("CI"):
            pytest.fail(f"{name}: CI must support this symlink regression: {exc}")
        pytest.skip(f"{name}: symlink creation unavailable ({exc})")
    return True


def _timed_out_run(calls: list[float]) -> Callable[..., subprocess.CompletedProcess]:
    """Return a subprocess seam that records and raises the configured timeout."""
    def run(*args, **kwargs):
        calls.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    return run


def test_default_base_ref_primary_probe_timeout_degrades_to_no_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_linter_module()
    calls: list[float] = []
    monkeypatch.setattr(module.subprocess, "run", _timed_out_run(calls))

    assert module.resolve_default_base_ref(Path("/repo")) is None
    assert calls == [module.GIT_TIMEOUT_S]


def test_default_base_ref_fallback_probe_timeout_degrades_to_no_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_linter_module()
    calls: list[float] = []

    def run(*args, **kwargs):
        calls.append(kwargs["timeout"])
        if len(calls) == 1:
            return subprocess.CompletedProcess(args[0], 1, "", "")
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(module.subprocess, "run", run)

    assert module.resolve_default_base_ref(Path("/repo")) is None
    assert calls == [module.GIT_TIMEOUT_S, module.GIT_TIMEOUT_S]


def test_base_ref_probe_timeout_degrades_to_unresolvable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_linter_module()
    calls: list[float] = []
    monkeypatch.setattr(module.subprocess, "run", _timed_out_run(calls))

    assert not module.base_ref_resolves(Path("/repo"), "origin/main")
    assert calls == [module.GIT_TIMEOUT_S]


def test_base_spec_show_timeout_skips_diff_invariants_for_unchanged_specs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A timed-out base object read is not evidence that a spec is new."""
    module = load_linter_module()
    calls: list[float] = []
    original_run = module.subprocess.run

    def run(*args, **kwargs):
        if "show" in args[0]:
            calls.append(kwargs["timeout"])
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        return original_run(*args, **kwargs)

    with best_effort_tempdir() as tmp:
        root = Path(tmp).resolve()
        sectionless = root / "docs" / "specs" / "sectionless" / "spec.md"
        sectionless.parent.mkdir(parents=True)
        sectionless.write_text(
            "# Spec: sectionless\n\n- **Status:** Shipped\n", encoding="utf-8"
        )
        write_spec(root, "unchecked", "Shipped", "- [ ] grandfathered\n")
        git_init_commit(root)

        monkeypatch.setattr(module.subprocess, "run", run)
        monkeypatch.setattr(module, "base_ref_resolves", lambda _root, _ref: True)
        # all_specs=True: this case's subject IS unchanged specs, and the scoped
        # default does not read them, so the `git show` base comparison it
        # guards only happens in the exhaustive mode CI runs.
        hard, warn = module.check(root, "HEAD", all_specs=True)

    assert hard == []
    assert calls == [module.GIT_TIMEOUT_S, module.GIT_TIMEOUT_S], warn
    assert sum("diff-triggered invariants (ii) and (vi) skipped" in item for item in warn) == 2


def test_repo_root_probe_timeout_degrades_to_script_relative_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_linter_module()
    calls: list[float] = []
    monkeypatch.setattr(module.subprocess, "run", _timed_out_run(calls))

    assert module._repo_root() == Path(module.__file__).resolve().parent.parent
    assert calls == [module.GIT_TIMEOUT_S]


def test_clean() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "ok", "Draft", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root)  # no base ref → invariant (ii) skipped
        expect(rc == 0, f"clean fixture should exit 0, got {rc}: {err}")


def test_invariant_i_out_of_vocab() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "bad", "Drafting", "- [ ] AC1\n")
        rc, out, err = run_lint(root)
        expect(rc == 1, f"out-of-vocab 'Drafting' should exit 1, got {rc}")
        expect("invariant (i)" in err, f"expected invariant (i) msg: {err}")


def test_invariant_i_lenient() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "annotated", "Shipped (2026-05-26)", "- [x] AC1\n")
        write_spec(root, "arrowed", "Approved → Shipped (landed)", "- [x] AC1\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"annotated/arrowed status should pass (i), got {rc}: {err}")


def test_invariant_ii_transition_fails() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "shipping", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        # Flip to Shipped in the working tree with an unchecked, undeferred AC.
        write_spec(root, "shipping", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 1, f"ship transition w/ unchecked AC should exit 1, got {rc}")
        expect("invariant (ii)" in err, f"expected invariant (ii) msg: {err}")


def test_invariant_ii_transition_fails_when_deferred() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_workspace_backlog(root, ["later-work"])
        write_spec(root, "shipping", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec(
            root, "shipping", "Shipped",
            "- [x] AC1 done\n- [ ] AC2 later (deferred: later-work)\n",
        )
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 1, f"new ship with a deferred AC should exit 1, got {rc}")
        expect("invariant (ii)" in err, f"expected invariant (ii) msg: {err}")
        expect("unchecked" in err, f"expected unchecked diagnostic: {err}")


def test_invariant_ii_grandfather() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # Already Shipped on the base with an unchecked AC → grandfathered.
        write_spec(root, "old", "Shipped", "- [ ] AC1 never checked\n")
        git_init_commit(root)
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 0, f"already-Shipped spec should be grandfathered, got {rc}: {err}")


def test_invariant_ii_no_base() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)  # plain dir, not a git repo, no base ref
        write_spec(root, "shipping", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root)  # resolve_default_base_ref → None
        expect(rc == 0, f"no base ref → (ii) skipped, should exit 0, got {rc}: {err}")
        expect("no base ref resolvable" in err, f"expected skip warning: {err}")


def test_invariant_i_missing_status() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # A spec with no `- **Status:**` header line at all.
        p = root / "docs" / "specs" / "headless" / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# Spec: headless\n\n{_AC_HEADER}- [ ] AC1\n", encoding="utf-8")
        rc, _, err = run_lint(root)
        expect(rc == 1, f"missing Status header should exit 1, got {rc}")
        expect("no `- **Status:**`" in err, f"expected missing-status msg: {err}")


def test_invariant_iv_resolves_workspace_slug() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # A slug in workspace.toml [backlog].open must resolve a (deferred:) marker.
        write_workspace_backlog(root, ["some-deferred-item"])
        write_spec(root, "deferring", "Draft",
                   "- [ ] AC1 (deferred: some-deferred-item)\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"deferral to workspace.toml slug should resolve, got {rc}: {err}")


# STUB: AC1 — repository metadata must not be read through an outside symlink.
def test_workspace_symlink_outside_root_does_not_resolve_deferral() -> None:
    with best_effort_tempdir() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        root.mkdir()
        outside = sandbox / "outside-workspace.toml"
        outside.write_text(
            '# workspace-content-sentinel\n[[backlog.open]]\nslug = "outside-only-anchor"\n',
            encoding="utf-8",
        )
        if not symlink_or_skip(
            "workspace symlink confinement", root / "workspace.toml", outside
        ):
            return
        write_spec(
            root,
            "deferring",
            "Draft",
            "- [ ] AC1 (deferred: outside-only-anchor)\n",
        )

        rc, out, err = run_lint(root)

        expect(rc == 1, f"outside workspace symlink must not resolve an anchor: {err}")
        expect("invariant (iv)" in err, f"expected unresolved-anchor diagnostic: {err}")
        expect(
            "workspace-content-sentinel" not in out + err,
            f"outside workspace content leaked to diagnostics: {out} {err}",
        )


# STUB: AC1 — link and code-reference probes must not consult outside targets.
def test_reference_candidates_outside_root_do_not_resolve() -> None:
    with best_effort_tempdir() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        root.mkdir()
        (sandbox / "outside.md").write_text("outside-doc-sentinel\n", encoding="utf-8")
        (sandbox / "outside.py").write_text("outside_code_sentinel = 1\n", encoding="utf-8")
        write_spec_body(
            root,
            "escaping-refs",
            "See [outside](../../../../outside.md) and "
            "`../../../../outside.py`.",
        )

        rc, out, err = run_lint(root)

        expect(rc == 0, f"reference findings remain warn-only, got {rc}: {err}")
        expect("outside.md" in err, f"outside doc target must not resolve: {err}")
        expect("outside.py" in err, f"outside code target must not resolve: {err}")
        expect(
            "outside-doc-sentinel" not in out + err
            and "outside_code_sentinel" not in out + err,
            f"outside reference content leaked to diagnostics: {out} {err}",
        )


# CONTRACT CONTROL: AC1 — the existing contract-file confinement stays pinned.
def test_contract_file_symlink_outside_root_does_not_resolve() -> None:
    with best_effort_tempdir() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        root.mkdir()
        outside = sandbox / "outside-contract.yaml"
        outside.write_text(
            "openapi: 3.1.0\nx-spec: [docs/specs/orders/]\n"
            "outside-contract-sentinel: true\n",
            encoding="utf-8",
        )
        contract = root / "contracts" / "openapi" / "orders.yaml"
        contract.parent.mkdir(parents=True)
        if not symlink_or_skip("contract-file symlink confinement", contract, outside):
            return
        write_spec_with_contract(root, "orders", "`contracts/openapi/orders.yaml`")

        rc, out, err = run_lint(root)

        expect(rc == 0, f"contract finding remains warn-only, got {rc}: {err}")
        expect("does not resolve to a file" in err,
               f"outside contract symlink must be rejected before read: {err}")
        expect(
            "outside-contract-sentinel" not in out + err,
            f"outside contract content leaked to diagnostics: {out} {err}",
        )


def test_invariant_ii_born_shipped_fails() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # A brand-new spec absent at base, born Shipped with an unchecked AC.
        write_spec(root, "preexisting", "Draft", "- [x] AC1\n")
        git_init_commit(root)  # base has no `newborn` spec
        write_spec(root, "newborn", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 1, f"new spec born Shipped w/ unchecked AC should exit 1, got {rc}")
        expect("invariant (ii)" in err, f"expected invariant (ii) msg: {err}")


def test_invariant_iv_missing_anchor() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "deferring", "Draft",
                   "- [ ] AC1 (deferred: nonexistent-anchor)\n")
        rc, _, err = run_lint(root)
        expect(rc == 1, f"dangling deferral anchor should exit 1, got {rc}")
        expect("invariant (iv)" in err, f"expected invariant (iv) msg: {err}")


def test_invariant_iv_placeholder_ignored() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # The template placeholder `<anchor>` must NOT be treated as a real
        # deferral marker (it would never resolve).
        write_spec(root, "templatey", "Draft",
                   "- [ ] AC1 uses `(deferred: <anchor>)` in prose\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"placeholder <anchor> should be ignored, got {rc}: {err}")


def test_invariant_iii_warn_only() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        p = root / "docs" / "specs" / "linky" / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# Spec: linky\n\n- **Status:** Draft\n\n"
            "See [the plan](plan.md) which does not exist.\n\n"
            f"{_AC_HEADER}- [ ] AC1\n",
            encoding="utf-8",
        )
        rc, _, err = run_lint(root)
        expect(rc == 0, f"dangling doc ref must be warn-only (exit 0), got {rc}")
        expect("invariant (iii)" in err, f"expected invariant (iii) warning: {err}")


def write_spec_body(root: Path, name: str, body: str) -> None:
    """Write a Draft spec whose body (between Status and the AC section)
    is `body` — used to exercise invariant (iii) code references."""
    p = root / "docs" / "specs" / name / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# Spec: {name}\n\n- **Status:** Draft\n\n{body}\n\n{_AC_HEADER}- [ ] AC1\n",
        encoding="utf-8",
    )


def touch(root: Path, rel: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x\n", encoding="utf-8")


def test_iii_code_ref_resolves_and_missing() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        touch(root, "tools/real.py")
        write_spec_body(root, "coderef",
                        "Touches `tools/real.py` and `tools/missing.py`.")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"code-ref check must be warn-only (exit 0), got {rc}")
        expect("tools/missing.py" in err, f"missing code ref should warn: {err}")
        expect("tools/real.py" not in err, f"resolving code ref must not warn: {err}")


def test_iii_code_ref_exclusions_with_controls() -> None:
    # Each excluded shape is paired with a shape-matched full-path control that
    # IS flagged — so a no-op extractor (matching nothing) fails this case.
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec_body(
            root, "excl",
            "Bare `install.py`; placeholder `packages/<pkg>/x.py`; glob "
            "`tools/lint-*.py`; prose ellipsis `packs/core/...x.toml`. "
            "Controls: `tools/install.py`, `packages/real/x.py`, "
            "`tools/lint-missing.py`, `packs/core/ctrl-missing.toml`.",
        )
        rc, _, err = run_lint(root)
        expect(rc == 0, f"exit 0 expected, got {rc}: {err}")
        # excluded shapes never warn
        for excluded in ("`install.py`", "packages/<pkg>", "lint-*.py", "...x.toml"):
            expect(excluded not in err, f"excluded shape leaked into warnings: {excluded}")
        # brace-expansion shorthand is excluded even when rooted (so the brace
        # rule, not the root check, is what's under test).
        write_spec_body(root, "braces", "See `packages/adapters/{a,b}.py`.")
        rc2, _, err2 = run_lint(root)
        expect("{a,b}" not in err2 and rc2 == 0,
               f"brace-expansion shorthand must not warn: {err2}")
        # shape-matched full-path controls DO warn
        for control in ("tools/install.py", "packages/real/x.py",
                        "tools/lint-missing.py", "packs/core/ctrl-missing.toml"):
            expect(control in err, f"control should warn but didn't: {control}: {err}")


def test_iii_code_ref_suffix_strip() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        touch(root, "tools/y.py")
        write_spec_body(
            root, "suffix",
            "See `tools/y.py:42`, `tools/y.py:42:10`, `tools/y.py#L42`; "
            "but `tools/gone.py:7` is stale.",
        )
        rc, _, err = run_lint(root)
        expect(rc == 0, f"exit 0 expected, got {rc}")
        expect("tools/y.py" not in err, f"located path (with locator) must not warn: {err}")
        expect("tools/gone.py" in err, f"missing path with locator should warn: {err}")


def test_iii_code_ref_markdown_link() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec_body(root, "linkref", "See [the helper](../../tools/nope.py).")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"exit 0 expected, got {rc}")
        expect("nope.py" in err, f"dangling markdown code link should warn: {err}")


def write_spec_with_contract(
    root: Path, name: str, contract_value: str, status: str = "Draft"
) -> None:
    """Draft spec carrying a `- **Contract:**` header — exercises invariant (v)."""
    p = root / "docs" / "specs" / name / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# Spec: {name}\n\n- **Status:** {status}\n"
        f"- **Contract:** {contract_value}\n\n{_AC_HEADER}- [ ] AC1\n",
        encoding="utf-8",
    )


def write_contract(root: Path, relpath: str, content: str) -> None:
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_v_agreement_passes() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_contract(root, "contracts/openapi/orders.yaml",
                       "openapi: 3.1.0\nx-spec: [docs/specs/orders/]\n")
        write_spec_with_contract(root, "orders", "`contracts/openapi/orders.yaml`")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"agreement should exit 0, got {rc}: {err}")
        expect("invariant (v)" not in err, f"agreement must not warn (v): {err}")


def test_v_forward_without_backward_warns() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # contract exists but carries no x-spec back-ref, and no REGISTRY.md
        write_contract(root, "contracts/openapi/orders.yaml", "openapi: 3.1.0\n")
        write_spec_with_contract(root, "orders", "`contracts/openapi/orders.yaml`")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"missing backward ref must be warn-only (exit 0), got {rc}")
        expect("invariant (v)" in err, f"expected invariant (v) warning: {err}")


def test_v_no_contracts_noop() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # template placeholder value + an explicit "none"; no contracts/ tree
        write_spec_with_contract(
            root, "templ", '<!-- contracts/<type>/<name> … or "none" -->')
        write_spec_with_contract(root, "plain", "none")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"no-contracts should exit 0, got {rc}: {err}")
        expect("invariant (v)" not in err, f"no-contracts must not warn (v): {err}")


def test_v_extensionless_registry_and_dangling() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        # extensionless format → REGISTRY.md is the backward channel
        write_contract(root, "contracts/proto/payments/v1/payments.proto",
                       'syntax = "proto3";\n')
        write_contract(
            root, "contracts/REGISTRY.md",
            "# Registry\n\n- `contracts/proto/payments/v1/payments.proto` "
            "→ docs/specs/payments/\n")
        write_spec_with_contract(
            root, "payments", "`contracts/proto/payments/v1/payments.proto`")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"registry-backed extensionless should exit 0, got {rc}: {err}")
        expect("invariant (v)" not in err, f"REGISTRY backref should satisfy (v): {err}")
        # a Contract: header naming a non-existent contract warns (dangling)
        write_spec_with_contract(root, "ghost", "`contracts/openapi/ghost.yaml`")
        rc2, _, err2 = run_lint(root)
        expect(rc2 == 0 and "invariant (v)" in err2 and "ghost.yaml" in err2,
               f"dangling Contract: ref should warn (v), warn-only: {err2}")


# STUB: AC1 — the contract registry must not be read through an outside symlink.
def test_contract_registry_symlink_outside_root_does_not_supply_backref() -> None:
    with best_effort_tempdir() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        root.mkdir()
        token = "contracts/proto/payments/v1/payments.proto"
        write_contract(root, token, 'syntax = "proto3";\n')
        outside = sandbox / "outside-registry.md"
        outside.write_text(
            f"- `{token}` → docs/specs/payments/ outside-registry-sentinel\n",
            encoding="utf-8",
        )
        if not symlink_or_skip(
            "contract-registry symlink confinement",
            root / "contracts" / "REGISTRY.md",
            outside,
        ):
            return
        write_spec_with_contract(root, "payments", f"`{token}`")

        rc, out, err = run_lint(root)

        expect(rc == 0, f"registry finding remains warn-only, got {rc}: {err}")
        expect("lacks a backward" in err,
               f"outside registry must not satisfy the back-reference: {err}")
        expect(
            "outside-registry-sentinel" not in out + err,
            f"outside registry content leaked to diagnostics: {out} {err}",
        )


def test_multiline_comment_not_matched() -> None:
    """Regression: a **Status:** inside a multiline HTML comment must not
    be returned before the live status field (parse_status was applying
    _HTML_COMMENT_RE per-line, so block comments were never stripped)."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        spec = root / "docs" / "specs" / "commented" / "spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        # The commented status uses a non-canonical token ("Nonexistent") so
        # that the per-line implementation (which would pick it up from inside
        # the comment) would fail the vocabulary check.  The fix strips the
        # whole comment block first; "Draft" is the only status seen → exit 0.
        spec.write_text(
            "# Spec: commented\n\n"
            "<!--\n"
            "- **Status:** Nonexistent\n"
            "-->\n"
            "- **Status:** Draft\n\n"
            "## Acceptance Criteria\n\n"
            "- [x] AC1\n",
            encoding="utf-8",
        )
        rc, _, err = run_lint(root)
        expect(rc == 0, f"live Draft should pass vocab check, got {rc}: {err}")


# ---------------------------------------------------------------------------
# AC-heading casing
#
# The heading match used to be case-sensitive, so a spec written with
# `## Acceptance criteria` collected zero criteria and its AC-completeness
# invariant passed VACUOUSLY — the linter reported success on a spec whose
# criteria it never read. 18 specs were silently un-gated that way, and the
# count only grew, because nothing tells an author which casing is wanted.
# ---------------------------------------------------------------------------

_LOWER_AC_HEADER = "## Acceptance criteria\n\n"


def _write_spec_with_header(root: Path, name: str, status: str, acs: str, header: str) -> None:
    p = root / "docs" / "specs" / name / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# Spec: {name}\n\n- **Status:** {status}\n\n{header}{acs}\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "header",
    ["## Acceptance Criteria\n\n", _LOWER_AC_HEADER, "## ACCEPTANCE CRITERIA\n\n"],
    ids=["title-case", "sentence-case", "upper-case"],
)
def test_unchecked_ac_is_caught_whatever_the_heading_casing(header: str) -> None:
    """A spec born Shipped with an unchecked AC must fail under any casing.

    Invariant (ii) is diff-triggered, so this mirrors
    `test_invariant_ii_born_shipped_fails`: a spec absent at base, born Shipped.

    This is the regression that matters. With the old case-sensitive match the
    sentence-case arm EXITED 0 — a clean bill of health for a spec shipping an
    unmet criterion, because the linter never found the section to read.
    """
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        _write_spec_with_header(root, "preexisting", "Draft", "- [x] AC1\n", header)
        git_init_commit(root)
        _write_spec_with_header(root, "newborn", "Shipped", "- [ ] AC1 open\n", header)
        rc, out, err = run_lint(root, base_ref="HEAD")
        assert rc == 1, f"unchecked AC under {header!r} should exit 1, got {rc}\n{out}\n{err}"
        assert "invariant (ii)" in err, err


@pytest.mark.parametrize(
    "header",
    ["## Acceptance Criteria\n\n", _LOWER_AC_HEADER],
    ids=["title-case", "sentence-case"],
)
def test_fully_checked_spec_under_either_casing(header: str) -> None:
    """A clean spec stays clean under the canonical heading; a near miss is
    reported as a heading defect, never as a missing section.

    The casings are no longer interchangeable: (vi) enforces the canonical form
    on a new spec. What must NOT happen is the near-miss arm being told to add a
    `none` opt-out — that would put a false "no criteria" marker on a spec that
    has one.
    """
    canonical = header == "## Acceptance Criteria\n\n"
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        _write_spec_with_header(root, "preexisting", "Draft", "- [x] AC1\n", header)
        git_init_commit(root)
        _write_spec_with_header(root, "newborn", "Shipped", "- [x] AC1 done\n", header)
        rc, out, err = run_lint(root, base_ref="HEAD")
        if canonical:
            assert rc == 0, f"clean spec should exit 0, got {rc}\n{out}\n{err}"
        else:
            assert rc == 1, f"a near-miss heading must be reported\n{out}\n{err}"
            assert "heading must be exactly" in err, err
            assert "do NOT add a `none` opt-out" in err, err


# ---------------------------------------------------------------------------
# Invariant (vi): an absent Acceptance-Criteria section requires an explicit,
# reasoned metadata opt-out. The section detector is EXACT while the criterion
# collector stays permissive -- deliberately one-directional. (vi) enforces the
# canonical heading so drift cannot reseed; (ii) keeps reading criteria it can
# plainly see. Collapsing them either way regresses: a strict collector silently
# un-gates (ii), a permissive detector reopens the drift path.
# ---------------------------------------------------------------------------


def write_spec_without_ac_section(
    root: Path,
    name: str,
    marker_value: str | None = None,
) -> Path:
    """Write a Draft spec with no Acceptance-Criteria section."""
    spec = root / "docs" / "specs" / name / "spec.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    marker = (
        f"- **Acceptance Criteria:** {marker_value}\n"
        if marker_value is not None
        else ""
    )
    spec.write_text(
        f"# Spec: {name}\n\n- **Status:** Draft\n{marker}\n## Objective\n\nFixture.\n",
        encoding="utf-8",
    )
    return spec


def test_vi_heading_present_without_marker_is_clean() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "has-criteria", "Draft", "- [ ] AC1 open\n")

        rc, _, err = run_lint(root)

        assert rc == 0, f"real AC section without opt-out should be clean: {err}"


def test_vi_missing_heading_with_reasoned_marker_is_clean() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        reason = "this investigation prescribes no work"
        spec = write_spec_without_ac_section(root, "opted-out", f"none — {reason}")

        rc, _, err = run_lint(root)
        parsed = load_linter_module().acceptance_criteria_opt_out(
            spec.read_text(encoding="utf-8")
        )

        assert rc == 0, f"reasoned opt-out should be clean: {err}"
        assert parsed is not None and parsed[1] == reason


def test_vi_missing_heading_at_base_and_now_is_grandfathered() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        spec = write_spec_without_ac_section(root, "grandfathered")
        git_init_commit(root)
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("Fixture.", "Fixture updated."),
            encoding="utf-8",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 0, f"base-sectionless spec should be grandfathered: {err}"
        assert "hard violation" not in err


def test_vi_losing_heading_without_marker_is_hard() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "loses-section", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec_without_ac_section(root, "loses-section")

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"removed AC section without marker should be hard: {err}"
        assert "invariant (vi)" in err


def test_vi_new_spec_without_heading_or_marker_is_hard() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec_without_ac_section(root, "new-sectionless")

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"new sectionless spec without marker should be hard: {err}"
        assert "invariant (vi)" in err


def test_vi_marker_in_body_does_not_satisfy() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "body-marker", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        spec = write_spec_without_ac_section(root, "body-marker")
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                "Fixture.",
                "- **Acceptance Criteria:** none — marker is in the body.",
            ),
            encoding="utf-8",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"body marker must not satisfy the preamble contract: {err}"
        assert "no `- **Acceptance Criteria:**" in err


def test_vi_ascii_hyphen_marker_has_precise_near_miss_error() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec_without_ac_section(
            root,
            "ascii-hyphen",
            "none - this separator is ASCII",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"ASCII-hyphen near miss should be hard: {err}"
        assert "em dash (U+2014), not an ASCII hyphen" in err
        assert "no `- **Acceptance Criteria:**" not in err


def test_vi_lowercase_marker_has_precise_near_miss_error() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        spec = write_spec_without_ac_section(root, "lowercase-marker")
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                "- **Status:** Draft\n",
                "- **Status:** Draft\n"
                "- **Acceptance criteria:** none — lowercase field name\n",
            ),
            encoding="utf-8",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"lowercase near miss should be hard: {err}"
        assert "must use exact casing `Acceptance Criteria`" in err
        assert "no `- **Acceptance Criteria:**" not in err


@pytest.mark.parametrize(
    "marker_value",
    ["none", "none —"],
    ids=["missing-reason", "empty-reason"],
)
def test_vi_reasonless_marker_is_hard(marker_value: str) -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        spec = write_spec_without_ac_section(root, "reasonless", marker_value)

        rc, _, err = run_lint(root)
        parsed = load_linter_module().acceptance_criteria_opt_out(
            spec.read_text(encoding="utf-8")
        )

        assert rc == 1, f"reasonless opt-out should be hard: {err}"
        assert "invariant (vi)" in err
        assert parsed is not None and parsed[1] == ""


def test_vi_heading_and_marker_are_a_hard_contradiction() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        spec = root / "docs" / "specs" / "contradiction" / "spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(
            "# Spec: contradiction\n\n"
            "- **Status:** Draft\n"
            "- **Acceptance Criteria:** none — this spec prescribes no work\n\n"
            "## Acceptance Criteria\n\n"
            "- [ ] AC1 open\n",
            encoding="utf-8",
        )

        rc, _, err = run_lint(root)

        assert rc == 1, f"section plus opt-out should be contradictory: {err}"
        assert "invariant (vi)" in err


def test_vi_lowercase_heading_counts_as_present() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        _write_spec_with_header(
            root,
            "lowercase-heading",
            "Draft",
            "- [ ] AC1 open\n",
            _LOWER_AC_HEADER,
        )

        rc, _, err = run_lint(root)

        assert rc == 0, f"sentence-case AC heading should count as present: {err}"


def test_vi_fenced_heading_and_checkboxes_do_not_count() -> None:
    lint = load_linter_module()
    fenced_example = (
        "# Spec: fenced-heading\n\n"
        "```markdown\n"
        "```toml\n"
        "## Acceptance Criteria\n\n"
        "- [ ] example checkbox\n"
        "```\n"
    )

    assert not lint.acceptance_criteria_section_present(fenced_example)
    assert lint.acceptance_criteria_lines(fenced_example) == []

    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        spec = root / "docs" / "specs" / "fenced-heading" / "spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(
            fenced_example.replace(
                "# Spec: fenced-heading\n\n",
                "# Spec: fenced-heading\n\n- **Status:** Draft\n\n",
            ),
            encoding="utf-8",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"fenced example must not satisfy invariant (vi): {err}"
        assert "invariant (vi)" in err


def test_vi_fenced_opt_out_marker_does_not_satisfy() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        spec = root / "docs" / "specs" / "fenced-marker" / "spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(
            "# Spec: fenced-marker\n\n"
            "```markdown\n"
            "- **Acceptance Criteria:** none — example only\n"
            "```\n"
            "- **Status:** Draft\n\n"
            "## Objective\n\nFixture.\n",
            encoding="utf-8",
        )

        lint = load_linter_module()
        assert lint.acceptance_criteria_opt_out(
            spec.read_text(encoding="utf-8")
        ) is None

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"fenced marker must not satisfy invariant (vi): {err}"
        assert "no `- **Acceptance Criteria:**" in err


@pytest.mark.parametrize(
    "header",
    ["### Acceptance Criteria\n\n", "  ## Acceptance Criteria\n\n"],
    ids=["h3", "indented-h2"],
)
def test_vi_commonmark_heading_shapes_are_not_the_canonical_section(
    header: str,
) -> None:
    """`###` and an indented `##` are legal CommonMark but are NOT the one
    supported shape. They no longer satisfy (vi) -- accepting them is the drift
    path that let six specs diverge -- while the collector still reads their
    criteria so (ii) keeps working."""
    lint = load_linter_module()
    spec = f"# Spec: s\n\n- **Status:** Shipped\n\n{header}\n- [x] a\n"
    assert lint.acceptance_criteria_section_present(spec) is False, header
    assert len(lint.acceptance_criteria_lines(spec)) == 1, header


def test_vi_placeholder_reason_is_rejected() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "base", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec_without_ac_section(
            root,
            "placeholder-reason",
            "none — <one-line reason>",
        )

        rc, _, err = run_lint(root, base_ref="HEAD")

        assert rc == 1, f"placeholder reason must be rejected: {err}"
        assert "non-placeholder one-line reason" in err


def test_collector_accepts_a_superset_of_what_the_detector_accepts() -> None:
    """The two matchers diverge on purpose, in one direction only.

    Superset, never the reverse. If the DETECTOR ever accepted a spelling the
    collector could not read, (vi) would report a section that (ii) reads
    nothing from -- the vacuous pass this invariant exists to close. The other
    direction is safe: the collector over-reading only means (ii) checks more.
    """
    lint = load_linter_module()
    shapes = [
        "## Acceptance Criteria",
        "## Acceptance criteria",
        "### Acceptance Criteria",
        "  ## Acceptance Criteria",
    ]
    for heading in shapes:
        spec = f"# Spec: s\n\n{heading}\n\n- [ ] AC1 open\n"
        detected = lint.acceptance_criteria_section_present(spec)
        collected = bool(lint.acceptance_criteria_lines(spec))
        assert not (detected and not collected), (
            f"{heading!r}: detector accepts a shape the collector cannot read"
        )


def test_vi_mutation_missing_section_fires_until_only_marker_is_added() -> None:
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "mutation", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        spec = write_spec_without_ac_section(root, "mutation")
        without_marker = spec.read_text(encoding="utf-8")
        marker = (
            "- **Acceptance Criteria:** none — mutation fixture prescribes no work\n"
        )
        with_marker = without_marker.replace(
            "- **Status:** Draft\n",
            f"- **Status:** Draft\n{marker}",
            1,
        )
        assert with_marker.replace(marker, "", 1) == without_marker

        lint = load_linter_module()
        hard_before, _ = lint.check(root.resolve(), base_ref="HEAD")
        assert hard_before, "missing-section fixture must produce a hard violation"
        assert any("invariant (vi)" in violation for violation in hard_before)

        spec.write_text(with_marker, encoding="utf-8")
        hard_after, _ = lint.check(root.resolve(), base_ref="HEAD")

        assert hard_before != hard_after, "marker mutation must change the result"
        assert hard_after == []


def test_ac_heading_presence_is_exact_while_the_collector_is_permissive() -> None:
    """One-directional strictness, pinned in both directions.

    (vi) enforces the canonical heading so drift cannot reseed; the collector
    stays permissive so (ii) never stops reading criteria it can plainly see.
    """
    lint = load_linter_module()
    for heading in ("## Acceptance criteria", "### Acceptance Criteria",
                    "  ## Acceptance Criteria"):
        spec = f"# Spec: s\n\n- **Status:** Shipped\n\n{heading}\n\n- [x] a\n"
        assert lint.acceptance_criteria_section_present(spec) is False, heading
        assert len(lint.acceptance_criteria_lines(spec)) == 1, heading
    canonical = (
        "# Spec: s\n\n- **Status:** Shipped\n\n## Acceptance Criteria\n\n- [x] a\n"
    )
    assert lint.acceptance_criteria_section_present(canonical) is True
    assert len(lint.acceptance_criteria_lines(canonical)) == 1


def test_near_miss_heading_is_warned_not_silently_accepted() -> None:
    """Silence would un-gate an adopter's spec without telling anyone.

    Measured before this warning existed: making the collector strict took an
    adopter shipping an unmet criterion under `## Acceptance criteria` from a
    hard invariant (ii) violation to exit 0. Not breaking a build is not the
    same as still working.
    """
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        _write_spec_with_header(root, "legacy", "Draft", "- [x] AC1\n", _LOWER_AC_HEADER)
        git_init_commit(root)
        # --all because the subject is a spec IDENTICAL to base. The scoped
        # default skips it by design, so this invariant's behaviour lives in the
        # exhaustive mode -- which is the mode CI runs.
        rc, out, err = run_lint(root, base_ref="HEAD", all_specs=True)
        assert rc == 0, f"a near miss must warn, not fail: {out}\n{err}"
        assert "`## Acceptance Criteria`" in err, err


def test_a_commented_out_ac_section_is_a_hard_error() -> None:
    """The one shape the body readers get wrong, turned into a hard error.

    `acceptance_criteria_section_present` and the collector read raw text, so a
    commented-out heading counts as a section and its checkboxes are harvested:
    (vi) satisfied and (ii) checking criteria the author disabled. Rather than
    teach both readers to parse comments -- the change that failed four review
    rounds -- the shape is rejected, which makes their disagreement unreachable
    in a passing state.
    """
    lint = load_linter_module()
    spec = (
        "# Spec: s\n\n- **Status:** Shipped\n\n"
        "<!--\n## Acceptance Criteria\n\n- [ ] disabled\n-->\n"
    )
    found = lint.commented_out_ac_heading(spec)
    assert found is not None and found[0] == 6, found


def test_a_commented_draft_beside_a_live_section_is_rejected() -> None:
    """A commented-out Acceptance-Criteria section is not a supported shape in
    ANY position, including beside a live one.

    Allowing it as "the author's business" let a commented, superseded `- [ ]`
    be collected as a real criterion, so invariant (ii) blocked a ship on work
    nobody intended to do. Criteria that no longer apply are deleted; git
    history is where superseded ones live.
    """
    lint = load_linter_module()
    spec = (
        "# Spec: s\n\n## Acceptance Criteria\n\n- [x] real\n\n"
        "<!--\n## Acceptance Criteria\n\n- [ ] superseded\n-->\n"
    )
    assert lint.commented_out_ac_heading(spec) is not None


def test_backticked_comment_syntax_does_not_trigger_the_rule() -> None:
    """The false-positive that makes a code-span-blind rule unusable.

    `docs/specs/digital-experience-contract/spec.md` documents a template whose
    fields carry comment-syntax annotations, writing an opener and a closer in
    backticks 23 lines apart. A reader with no notion of code spans pairs those
    two *mentions* into a span covering that spec's real heading and all 17 of
    its criteria, and would red-line a perfectly good spec.
    """
    lint = load_linter_module()
    spec = (
        "# Spec: s\n\n- **Status:** Shipped\n\n"
        "- A field marked with a `<!-- Required:` annotation.\n\n"
        "## Acceptance Criteria\n\n- [x] real\n\n"
        "- Written as `<!-- Required: <tier>+ -->` on the next line.\n"
    )
    assert lint.commented_out_ac_heading(spec) is None
    assert len(lint.acceptance_criteria_lines(spec)) == 1


def test_an_unterminated_comment_opener_does_not_trigger_the_rule() -> None:
    """An opener with no closer is literal text. Treating it as a comment
    running to end of document would swallow a real section and make invariant
    (ii) vacuous on that spec."""
    lint = load_linter_module()
    spec = (
        "# Spec: s\n\n<!-- stray opener, never closed\n\n"
        "## Acceptance Criteria\n\n- [x] real\n"
    )
    assert lint.commented_out_ac_heading(spec) is None


def test_code_span_scan_is_linear_on_a_long_backtick_run() -> None:
    """A regex formulation of this scan backtracked cubically -- a 12 KB
    backtick line took 106 s end-to-end, against a file-size cap admitting 8 MB
    of untrusted repository content."""
    import time

    lint = load_linter_module()
    start = time.monotonic()
    lint._code_span_ranges("`" * 12000)
    assert time.monotonic() - start < 1.0


@pytest.mark.parametrize(
    "line,expect",
    [
        ("  - **Acceptance Criteria:** none — r", "column 0"),
        ("* **Acceptance Criteria:** none — r", "`-` bullet"),
        ("- **Acceptance Criteria**: none — r", "colon belongs inside"),
        ("-  **Acceptance Criteria:** none — r", "exactly one space"),
        ("- **Acceptance criteria:** none — r", "exact casing"),
        ("- **Acceptance Criteria:** none - r", "em dash"),
    ],
    ids=["indented", "asterisk", "colon-outside", "double-space",
         "casing", "hyphen"],
)
def test_every_attempted_opt_out_shape_is_diagnosed(line: str, expect: str) -> None:
    """A visibly attempted opt-out must never pass in silence.

    The near-miss pattern anchored on a literal `^- `, so four of these six
    escaped BOTH readers: the spec passed clean with a malformed marker on the
    page, and the author got no signal at all. Widening what is DIAGNOSED is not
    widening what is ACCEPTED -- the accepting pattern stays exact.
    """
    lint = load_linter_module()
    assert lint.acceptance_criteria_opt_out(line + "\n") is None, line
    found = lint.acceptance_criteria_opt_out_near_miss(line + "\n")
    assert found is not None, f"{line!r} escaped both readers"
    assert expect in found[1], found


def test_the_canonical_marker_is_still_accepted() -> None:
    """The control for the case above: widening the diagnostic must not turn a
    correct marker into a near miss."""
    lint = load_linter_module()
    line = "- **Acceptance Criteria:** none — a stated reason\n"
    assert lint.acceptance_criteria_opt_out(line) is not None
    assert lint.acceptance_criteria_opt_out_near_miss(line) is None


@pytest.mark.parametrize(
    "value",
    ["tracked in the linked issue", "n/a", "see RFC-0001"],
    ids=["prose", "n-a", "cross-reference"],
)
def test_a_prose_value_is_not_an_attempted_opt_out(value: str) -> None:
    """Claiming prose in this field would hard-fail a spec that has a perfectly
    good Acceptance-Criteria section -- the regression that made gating the
    near-miss on the diff trigger look necessary."""
    lint = load_linter_module()
    line = f"- **Acceptance Criteria:** {value}\n"
    assert lint.acceptance_criteria_opt_out_near_miss(line) is None


def test_an_unreadable_spec_is_reported_not_silently_skipped() -> None:
    """A spec the linter cannot read must not be reported as clean.

    `_read` returns None for an unreadable file or one over the size cap, and
    skipping quietly is a vacuous pass over an entire file -- the failure mode
    every invariant here exists to prevent, applied to the whole document.
    """
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("root can read a mode-000 file")
    if sys.platform == "win32":
        pytest.skip("POSIX mode bits")
    lint = load_linter_module()
    with best_effort_tempdir() as tmp:
        # Resolve: `check()` is called directly here rather than through the CLI,
        # so it does not get `_validated_root`'s canonicalisation. On macOS
        # mkdtemp returns /var/... while resolve() gives /private/var/..., and
        # `_confined_path`'s relative_to() would then drop every spec silently.
        root = Path(tmp).resolve()
        _write_spec_with_header(
            root, "a", "Shipped", "- [x] done\n", "## Acceptance Criteria\n\n"
        )
        git_init_commit(root)
        target = root / "docs" / "specs" / "a" / "spec.md"
        target.chmod(0o000)
        try:
            _hard, warn = lint.check(root, "HEAD")
        finally:
            target.chmod(0o644)
    assert any("could not be read" in w for w in warn), warn


def test_an_unresolvable_base_ref_skips_instead_of_red_lining() -> None:
    """A base ref was taken on trust; verifying it is the whole fix.

    When an explicit `--base-ref` did not resolve, `base_spec_text` returned
    None for EVERY spec, which the diff-triggered invariants read as "new spec".
    A typo'd or unfetched ref therefore red-lined a clean corpus and told each
    author to add an opt-out marker for a section that was there all along --
    while the module docstring promised the opposite. A CI job with an
    unfetched ref got a confident, wrong failure.
    """
    lint = load_linter_module()
    with best_effort_tempdir() as tmp:
        root = Path(tmp).resolve()
        _write_spec_with_header(root, "sectionless", "Shipped", "", "")
        git_init_commit(root)
        good_hard, _ = lint.check(root, "HEAD")
        bad_hard, bad_warn = lint.check(root, "origin/definitely-not-a-ref")
    assert good_hard == [], good_hard
    assert bad_hard == [], f"an unresolvable ref must not red-line: {bad_hard}"
    assert any("does not resolve" in w for w in bad_warn), bad_warn
    assert any("invariant (vi)" in w for w in bad_warn), bad_warn


def test_a_resolvable_base_ref_still_drives_the_diff_triggers() -> None:
    """The control: verification must not disable the invariants it guards."""
    lint = load_linter_module()
    with best_effort_tempdir() as tmp:
        root = Path(tmp).resolve()
        _write_spec_with_header(
            root, "old", "Draft", "- [x] a\n", "## Acceptance Criteria\n\n"
        )
        git_init_commit(root)
        _write_spec_with_header(root, "newborn", "Shipped", "", "")
        hard, _warn = lint.check(root, "HEAD")
    assert any("invariant (vi)" in v for v in hard), hard


def test_default_scope_checks_changed_spec_but_not_unchanged_specs() -> None:
    """Scoped mode must not degrade into an empty per-spec selection."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "changed", "Draft", "- [x] AC1\n")
        write_spec(root, "unchanged", "Drafting", "- [x] legacy invalid status\n")
        git_init_commit(root)

        write_spec(root, "changed", "Drafting", "- [x] AC1\n")
        rc, _out, err = run_lint(root, base_ref="HEAD")

    assert rc == 1, "the changed spec's hard violation must be checked"
    assert "docs/specs/changed/spec.md" in err, err
    assert "docs/specs/unchanged/spec.md" not in err, err


def test_all_scope_checks_unchanged_specs_too() -> None:
    """The CI escape hatch retains full per-spec coverage."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "changed", "Draft", "- [x] AC1\n")
        write_spec(root, "unchanged", "Drafting", "- [x] legacy invalid status\n")
        git_init_commit(root)

        write_spec(root, "changed", "Draft", "- [x] changed body\n")
        rc, _out, err = run_lint(root, base_ref="HEAD", all_specs=True)

    assert rc == 1, "--all must retain full per-spec coverage"
    assert "docs/specs/unchanged/spec.md" in err, err


def test_unresolvable_base_ref_falls_back_to_full_per_spec_checks() -> None:
    """A bad base ref must not make a gate that checked nothing look clean."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "invalid", "Drafting", "- [x] AC1\n")
        git_init_commit(root)

        rc, _out, err = run_lint(root, base_ref="origin/definitely-not-a-ref")

    assert rc == 1, "an unresolved base must full-sweep instead of selecting zero"
    assert "docs/specs/invalid/spec.md" in err, err


def test_scoped_run_keeps_dangling_reference_warnings_repo_wide() -> None:
    """The warn-only cross-spec reference pass remains outside scoped selection."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "changed", "Draft", "- [x] AC1\n")
        write_spec(root, "unchanged", "Draft", "See [missing](nope.md).\n")
        git_init_commit(root)

        write_spec(root, "changed", "Draft", "- [x] changed body\n")
        rc, _out, err = run_lint(root, base_ref="HEAD")

    assert rc == 0, err
    assert "docs/specs/unchanged/spec.md" in err, err
    assert "invariant (iii)" in err, err


def test_scoped_run_keeps_deferral_anchors_repo_wide() -> None:
    """Invariant (iv)'s second input is workspace.toml, not the spec file.

    Closing a `[backlog].open` entry -- the routine close-work operation --
    invalidates the marker in every spec citing it, none of which need have
    changed. Scoping (iv) to changed specs would let that land unreported, and
    it is a HARD invariant, so this is the case that keeps it out of scope.
    """
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "deferring", "Draft", "- [ ] AC2 (deferred: some-followup)\n")
        (root / "workspace.toml").write_text(
            '[backlog]\nopen = [{slug = "some-followup"}]\nclosed = []\n',
            encoding="utf-8",
        )
        git_init_commit(root)

        # Close the entry and touch NO spec.
        (root / "workspace.toml").write_text(
            '[backlog]\nopen = []\nclosed = [{slug = "some-followup"}]\n',
            encoding="utf-8",
        )
        rc, out, err = run_lint(root, base_ref="HEAD")

    assert rc == 1, f"a broken deferral anchor must fail the scoped run: {out}\n{err}"
    assert "invariant (iv)" in err, err


def test_scoped_run_reports_the_coverage_it_achieved() -> None:
    """A run that selected nothing must not read like a full sweep."""
    with best_effort_tempdir() as tmp:
        root = Path(tmp)
        write_spec(root, "only", "Draft", "- [x] AC1\n")
        git_init_commit(root)
        scoped_rc, scoped_out, _ = run_lint(root, base_ref="HEAD")
        all_rc, all_out, _ = run_lint(root, base_ref="HEAD", all_specs=True)

    assert scoped_rc == 0 and all_rc == 0
    assert "0 of 1 spec(s) changed against HEAD" in scoped_out, scoped_out
    assert "all 1 spec(s)" in all_out, all_out


def test_undetermined_changed_set_sweeps_and_says_so() -> None:
    """`changed_spec_paths` returning None must full-sweep, not select zero.

    The docstring calls that contract out; without a case for it the contract
    could be inverted into a silent zero-selection with nothing red.
    """
    module = load_linter_module()
    with best_effort_tempdir() as tmp:
        root = Path(tmp).resolve()
        write_spec(root, "unchanged-but-invalid", "TOTALLY-INVALID", "- [x] AC1\n")
        git_init_commit(root)

        original = module.changed_spec_paths
        module.changed_spec_paths = lambda *_a, **_k: None
        try:
            hard, warn = module.check(root, "HEAD")
        finally:
            module.changed_spec_paths = original

    assert any("invariant (i)" in v for v in hard), hard
    assert any("could not determine changed specs" in w for w in warn), warn
    assert module.LAST_SCOPE["mode"] == "all", module.LAST_SCOPE


def test_opting_out_while_keeping_a_commented_draft_is_rejected() -> None:
    """Also rejected beside an opt-out marker -- but for the right reason.

    This shape originally drew TWO contradictory hard errors: one telling the
    author to add a marker they already had, and one reporting both a section
    and a marker, because presence counted the commented heading as live. The
    message bug and the presence bug are fixed; the rejection itself is
    correct, because the commented section should be deleted.
    """
    lint = load_linter_module()
    spec = (
        "# Spec: decided\n\n- **Status:** Draft\n"
        "- **Acceptance Criteria:** none — a decision record\n\n"
        "<!--\n## Acceptance Criteria\n\n- [ ] abandoned draft\n-->\n"
    )
    assert lint.commented_out_ac_heading(spec) is not None
    # ...and NOT via the section/marker contradiction: a commented heading is
    # not a live section, so that check must stay quiet.
    assert lint.acceptance_criteria_section_present(spec) is False


def test_a_commented_heading_is_not_a_near_miss() -> None:
    """The rejection must cite the commented section, not a heading-spelling
    problem. Before presence became comment-aware the near-miss scan read raw
    text and reported `should be exactly '## Acceptance Criteria' (found
    '## Acceptance Criteria')` -- warning about the form it had just found."""
    lint = load_linter_module()
    with best_effort_tempdir() as tmp:
        root = Path(tmp).resolve()
        (root / "docs" / "specs" / "decided").mkdir(parents=True)
        (root / "docs" / "specs" / "decided" / "spec.md").write_text(
            "# Spec: decided\n\n- **Status:** Draft\n"
            "- **Acceptance Criteria:** none — decisions only\n\n"
            "<!--\n## Acceptance Criteria\n\n- [ ] draft\n-->\n",
            encoding="utf-8",
        )
        (root / "workspace.toml").write_text(
            "[backlog]\nopen = []\nclosed = []\n", encoding="utf-8"
        )
        git_init_commit(root)
        # all_specs=True: the spec is committed and so identical to base, which
        # the scoped default skips. The subject here is the spec's content, not
        # the selection, so pin the content behaviour in the exhaustive mode.
        hard, warn = lint.check(root, "HEAD", all_specs=True)
    assert any("is commented out" in v for v in hard), hard
    assert not any("should be exactly" in w for w in warn), warn


def test_a_commented_only_section_without_a_marker_is_still_a_hard_error() -> None:
    """The control: the exclusion must not disable the guard itself."""
    lint = load_linter_module()
    spec = (
        "# Spec: s\n\n- **Status:** Shipped\n\n"
        "<!--\n## Acceptance Criteria\n\n- [ ] disabled\n-->\n"
    )
    assert lint.commented_out_ac_heading(spec) is not None
