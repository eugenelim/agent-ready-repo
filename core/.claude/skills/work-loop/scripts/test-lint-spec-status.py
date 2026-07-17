#!/usr/bin/env python3
"""Self-test for the sibling lint-spec-status.py (the Tier-1 spec-status lint).

Builds fixture spec trees in a tempdir and runs the linter as a
subprocess against the documented `python <skill>/scripts/lint-spec-status.py
--root <dir>` invocation — the same shape the CI gate uses.
Exercises each of the four invariants red-and-green, including the
lenient leading-token parse, the diff-triggered ship transition (with
real git base fixtures), the grandfather and no-base branches, and the
warn-only doc-reference invariant.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

LINTER = Path(__file__).resolve().parent / "lint-spec-status.py"

_AC_HEADER = "## Acceptance Criteria\n\n"


def write_spec(root: Path, name: str, status: str, acs: str) -> None:
    p = root / "docs" / "specs" / name / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# Spec: {name}\n\n- **Status:** {status}\n\n{_AC_HEADER}{acs}\n",
        encoding="utf-8",
    )


def write_backlog(root: Path, headings: list[str]) -> None:
    p = root / "docs" / "backlog.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = "# Backlog\n\n" + "".join(f"## {h}\n\n- item\n\n" for h in headings)
    p.write_text(body, encoding="utf-8")


def run_lint(root: Path, base_ref: str | None = None) -> tuple[int, str, str]:
    argv = [sys.executable, str(LINTER), "--root", str(root)]
    if base_ref is not None:
        argv += ["--base-ref", base_ref]
    proc = subprocess.run(argv, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def git_init_commit(root: Path) -> None:
    env_argv = [
        ["git", "-C", str(root), "init", "-q"],
        ["git", "-C", str(root), "add", "-A"],
        ["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "base"],
    ]
    for argv in env_argv:
        subprocess.run(argv, check=True, capture_output=True)


FAILURES: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def case_clean() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        write_spec(root, "ok", "Draft", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root)  # no base ref → invariant (ii) skipped
        expect(rc == 0, f"clean fixture should exit 0, got {rc}: {err}")


def case_invariant_i_out_of_vocab() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        write_spec(root, "bad", "Drafting", "- [ ] AC1\n")
        rc, _, err = run_lint(root)
        expect(rc == 1, f"out-of-vocab 'Drafting' should exit 1, got {rc}")
        expect("invariant (i)" in err, f"expected invariant (i) msg: {err}")


def case_invariant_i_lenient() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        write_spec(root, "annotated", "Shipped (2026-05-26)", "- [x] AC1\n")
        write_spec(root, "arrowed", "Approved → Shipped (landed)", "- [x] AC1\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"annotated/arrowed status should pass (i), got {rc}: {err}")


def case_invariant_ii_transition_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        write_spec(root, "shipping", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        # Flip to Shipped in the working tree with an unchecked, undeferred AC.
        write_spec(root, "shipping", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 1, f"ship transition w/ unchecked AC should exit 1, got {rc}")
        expect("invariant (ii)" in err, f"expected invariant (ii) msg: {err}")


def case_invariant_ii_transition_ok_when_deferred() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, ["later-work"])
        write_spec(root, "shipping", "Draft", "- [ ] AC1 open\n")
        git_init_commit(root)
        write_spec(
            root, "shipping", "Shipped",
            "- [x] AC1 done\n- [ ] AC2 later (deferred: later-work)\n",
        )
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 0, f"ship w/ checked+deferred ACs should exit 0, got {rc}: {err}")


def case_invariant_ii_grandfather() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # Already Shipped on the base with an unchecked AC → grandfathered.
        write_spec(root, "old", "Shipped", "- [ ] AC1 never checked\n")
        git_init_commit(root)
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 0, f"already-Shipped spec should be grandfathered, got {rc}: {err}")


def case_invariant_ii_no_base() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)  # plain dir, not a git repo, no base ref
        write_backlog(root, [])
        write_spec(root, "shipping", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root)  # resolve_default_base_ref → None
        expect(rc == 0, f"no base ref → (ii) skipped, should exit 0, got {rc}: {err}")
        expect("no base ref resolvable" in err, f"expected skip warning: {err}")


def case_invariant_i_missing_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # A spec with no `- **Status:**` header line at all.
        p = root / "docs" / "specs" / "headless" / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# Spec: headless\n\n{_AC_HEADER}- [ ] AC1\n", encoding="utf-8")
        rc, _, err = run_lint(root)
        expect(rc == 1, f"missing Status header should exit 1, got {rc}")
        expect("no `- **Status:**`" in err, f"expected missing-status msg: {err}")


def case_invariant_iv_resolves_multiword_anchor() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A real multi-word, punctuated heading must slugify and resolve.
        write_backlog(root, ["Cross Spec Work!"])
        write_spec(root, "deferring", "Draft",
                   "- [ ] AC1 (deferred: cross-spec-work)\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"deferral to slugified heading should resolve, got {rc}: {err}")


def case_invariant_iv_github_double_hyphen_anchor() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # GitHub turns `## A / b` into anchor `a--b` (double hyphen, no
        # collapse). The lint must match that to keep its "GitHub slug
        # rules" promise.
        write_backlog(root, ["Cross-spec / outside"])
        write_spec(root, "deferring", "Draft",
                   "- [ ] AC1 (deferred: cross-spec--outside)\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"double-hyphen GitHub anchor should resolve, got {rc}: {err}")


def case_invariant_ii_born_shipped_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # A brand-new spec absent at base, born Shipped with an unchecked AC.
        write_spec(root, "preexisting", "Draft", "- [x] AC1\n")
        git_init_commit(root)  # base has no `newborn` spec
        write_spec(root, "newborn", "Shipped", "- [ ] AC1 open\n")
        rc, _, err = run_lint(root, base_ref="HEAD")
        expect(rc == 1, f"new spec born Shipped w/ unchecked AC should exit 1, got {rc}")
        expect("invariant (ii)" in err, f"expected invariant (ii) msg: {err}")


def case_invariant_iv_missing_anchor() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, ["some-other-heading"])
        write_spec(root, "deferring", "Draft",
                   "- [ ] AC1 (deferred: nonexistent-anchor)\n")
        rc, _, err = run_lint(root)
        expect(rc == 1, f"dangling deferral anchor should exit 1, got {rc}")
        expect("invariant (iv)" in err, f"expected invariant (iv) msg: {err}")


def case_invariant_iv_placeholder_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # The template placeholder `<anchor>` must NOT be treated as a real
        # deferral marker (it would never resolve).
        write_spec(root, "templatey", "Draft",
                   "- [ ] AC1 uses `(deferred: <anchor>)` in prose\n")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"placeholder <anchor> should be ignored, got {rc}: {err}")


def case_invariant_iii_warn_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
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


def case_iii_code_ref_resolves_and_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        touch(root, "tools/real.py")
        write_spec_body(root, "coderef",
                        "Touches `tools/real.py` and `tools/missing.py`.")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"code-ref check must be warn-only (exit 0), got {rc}")
        expect("tools/missing.py" in err, f"missing code ref should warn: {err}")
        expect("tools/real.py" not in err, f"resolving code ref must not warn: {err}")


def case_iii_code_ref_exclusions_with_controls() -> None:
    # Each excluded shape is paired with a shape-matched full-path control that
    # IS flagged — so a no-op extractor (matching nothing) fails this case.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
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


def case_iii_code_ref_suffix_strip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
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


def case_iii_code_ref_markdown_link() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
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


def case_v_agreement_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        write_contract(root, "contracts/openapi/orders.yaml",
                       "openapi: 3.1.0\nx-spec: [docs/specs/orders/]\n")
        write_spec_with_contract(root, "orders", "`contracts/openapi/orders.yaml`")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"agreement should exit 0, got {rc}: {err}")
        expect("invariant (v)" not in err, f"agreement must not warn (v): {err}")


def case_v_forward_without_backward_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # contract exists but carries no x-spec back-ref, and no REGISTRY.md
        write_contract(root, "contracts/openapi/orders.yaml", "openapi: 3.1.0\n")
        write_spec_with_contract(root, "orders", "`contracts/openapi/orders.yaml`")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"missing backward ref must be warn-only (exit 0), got {rc}")
        expect("invariant (v)" in err, f"expected invariant (v) warning: {err}")


def case_v_no_contracts_noop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
        # template placeholder value + an explicit "none"; no contracts/ tree
        write_spec_with_contract(
            root, "templ", '<!-- contracts/<type>/<name> … or "none" -->')
        write_spec_with_contract(root, "plain", "none")
        rc, _, err = run_lint(root)
        expect(rc == 0, f"no-contracts should exit 0, got {rc}: {err}")
        expect("invariant (v)" not in err, f"no-contracts must not warn (v): {err}")


def case_v_extensionless_registry_and_dangling() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_backlog(root, [])
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


def main() -> int:
    for case in (
        case_clean,
        case_invariant_i_out_of_vocab,
        case_invariant_i_lenient,
        case_invariant_ii_transition_fails,
        case_invariant_ii_transition_ok_when_deferred,
        case_invariant_ii_grandfather,
        case_invariant_ii_no_base,
        case_invariant_i_missing_status,
        case_invariant_ii_born_shipped_fails,
        case_invariant_iv_resolves_multiword_anchor,
        case_invariant_iv_github_double_hyphen_anchor,
        case_invariant_iv_missing_anchor,
        case_invariant_iv_placeholder_ignored,
        case_invariant_iii_warn_only,
        case_iii_code_ref_resolves_and_missing,
        case_iii_code_ref_exclusions_with_controls,
        case_iii_code_ref_suffix_strip,
        case_iii_code_ref_markdown_link,
        case_v_agreement_passes,
        case_v_forward_without_backward_warns,
        case_v_no_contracts_noop,
        case_v_extensionless_registry_and_dangling,
    ):
        case()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"test-lint-spec-status: {len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("test-lint-spec-status: all invariant cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
