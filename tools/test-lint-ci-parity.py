#!/usr/bin/env python3
"""Self-test for tools/lint-ci-parity.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.

A parity linter fails in practice by reporting **ok** while checking nothing, so
most of these cases exist to pin the ways that could happen. The reasoning behind
each is in the linter's own docstring; this file states the assertions.

Every `check()` case passes its own declaration tables through the keyword
parameters rather than mutating the module globals, so no case depends on
another's leftovers.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-ci-parity.py"

_FAILURES: list[str] = []
_CASES = 0


def _utf8_streams() -> None:
    """Windows cp1252 guard — UTF-8 streams before any glyph is printed.

    Called from `main`, not at import, so importing this module for its pure
    functions does not reconfigure the importer's streams.
    """
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _load():
    spec = importlib.util.spec_from_file_location("_lint_ci_parity_under_test", LINTER)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        raise RuntimeError(f"cannot load {LINTER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load()
ONLY_BUILD_CHECK = {"build-check.yml": M.IN_SCOPE}


def _check(name: str, got: object, want: object) -> None:
    global _CASES
    _CASES += 1
    if got != want:
        _FAILURES.append(f"{name}: got {got!r}, want {want!r}")


def _check_true(name: str, cond: bool) -> None:
    _check(name, bool(cond), True)


def _check_fires(name: str, violations: list[str], needle: str) -> None:
    """Exactly the expected violation class fired, and nothing else."""
    global _CASES
    _CASES += 1
    if len(violations) != 1 or needle not in violations[0]:
        _FAILURES.append(
            f"{name}: want one violation containing {needle!r}, got {violations!r}"
        )


def _check_in(name: str, needle: str, haystack: str) -> None:
    global _CASES
    _CASES += 1
    if needle not in haystack:
        _FAILURES.append(f"{name}: missing {needle!r} in output\n  output: {haystack!r}")


def _recipe_lines(makefile: str, target: str) -> list[str]:
    """The tab-indented recipe of *target*, comment lines excluded."""
    out: list[str] = []
    seen = False
    for line in makefile.splitlines():
        if not seen:
            seen = bool(re.match(rf"^{re.escape(target)}\s*::?(?!=)", line))
            continue
        if line.startswith("\t"):
            if not line.lstrip("\t").lstrip().startswith("#"):
                out.append(line)
            continue
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue  # blank / comment lines do not end a recipe
        break
    return out


# Variables the macro branches on. Cleared from the child env before each case
# sets what it means to test — inheriting the ambient values made the
# `local-skip` case pass on a laptop and fail inside CI, where `GITHUB_WORKFLOW`
# is really `build-check`, so the case took the benign branch. That is the exact
# local-vs-CI divergence this whole spec exists to catch, reproduced in its own
# suite; a case must assert against the environment it declares, not the one it
# happens to run in.
_VERDICT_ENV_KEYS = ("SKIP_SAST", "GITHUB_WORKFLOW", "GITHUB_ACTIONS")


def _run_verdict(makefile: str, env_extra: dict[str, str]) -> str:
    """Execute the `gate_verdict` macro body under `sh` with exactly *env_extra*.

    Substitutes make's `$(…)` expansions by hand rather than shelling out to
    `make`, so the case runs the same way from any directory.
    """
    macro = re.search(r"define gate_verdict\n(.*?)\nendef", makefile, re.S)
    body = macro.group(1) if macro else ""
    body = body.lstrip("@")
    for var, value in (("$(1)", "make ci"), ("$(SAST_DIRS)", "tools packs packages"),
                       ("$(SAST_CONFIG)", "bandit.yaml Makefile")):
        body = body.replace(var, value)
    body = body.replace("$(SKIP_SAST)", env_extra.get("SKIP_SAST", ""))
    body = body.replace("$$", "$")
    env = {k: v for k, v in os.environ.items() if k not in _VERDICT_ENV_KEYS}
    env.update(env_extra)
    res = subprocess.run(["sh", "-c", body], capture_output=True, text=True,
                         check=False, env=env)
    return res.stdout + res.stderr


def _classified(steps=None, by_step=None, duplicates=None) -> dict:
    steps = list(steps or [])
    return {
        "steps": steps,
        "by_step": by_step or {},
        "where": {s: f"build-check.yml step {s!r}" for s in steps},
        "duplicates": duplicates or [],
    }


MAKEFILE = """\
PYTHON ?= python3
SAST_DIRS := tools packs packages
SAST_CONFIG := bandit.yaml Makefile

test:
\t$(PYTHON) -m pytest packages/agentbundle/tests/ -q
\t$(PYTHON) -m pytest -p no:cacheprovider packages/credbroker/ -q
\t$(PYTHON) -m pytest packs/core/tests/ --ignore packs/converters/ -q

lint-ruff:
\t$(PYTHON) tools/lint-ruff.py

zipapp:
\t$(PYTHON) tools/build_zipapp.py $(OUTPUT_DIR)

sast:
\tbandit -r $(SAST_DIRS) -c bandit.yaml -q

build-check:
\t$(MAKE) sast

ci: build-check test lint-ruff
"""

GATE_CHAIN = '''\
"""Docstring naming tools/never-run.py, which nothing invokes."""
steps = [
    # a comment inside the call must not truncate the match
    _script_step("lint-spec-status", ".claude", "skills", "x", "lint-spec-status.py"),
    _module_step("catalogue-build", "catalogue", "build"),
]
'''

AGGREGATOR = '''\
"""Prose mentions tools/also-never-run.py."""
_run("agents-md hygiene", [py, "tools/lint-agents-md.py"])
'''


def main() -> int:
    _utf8_streams()
    # ── extract_step_targets ────────────────────────────────────────────────
    _check("step-script-token",
           M.extract_step_targets("python3 tools/lint-x.py --root ."),
           ["tools/lint-x.py"])
    _check("step-pytest-paths",
           M.extract_step_targets("python -m pytest tests/unit/test_a.py tests/int/ -q"),
           ["tests/unit/test_a.py", "tests/int/"])
    _check("step-working-directory-prefix",
           M.extract_step_targets("python -m pytest test_render.py", "packs/x/scripts"),
           ["packs/x/scripts/test_render.py"])
    _check(
        "step-working-directory-parent-normalized",
        M.extract_step_targets(
            "python -m pytest ../../packs/x/tests/test_rule.py",
            "packages/agentbundle",
        ),
        ["packs/x/tests/test_rule.py"],
    )
    _check("step-provisioning-yields-nothing",
           M.extract_step_targets("pip install -r tools/requirements.txt"), [])
    _check("step-flag-value-not-a-target",
           M.extract_step_targets("python -m pytest -q -p no:cacheprovider"), [])
    # A provisioning command must not take a real gate down with it.
    _check("step-compound-provisioning-keeps-gate",
           M.extract_step_targets("sudo apt-get install -y rg && python3 tools/lint-scrub.py"),
           ["tools/lint-scrub.py"])
    _check("step-compound-all-provisioning",
           M.extract_step_targets("sudo apt-get update && sudo apt-get install -y ripgrep"), [])
    # `cd x && pytest` with no path argument collects from the cwd, so the cwd is
    # the target — otherwise the step reads as having nothing to declare.
    _check("step-cd-then-bare-pytest",
           M.extract_step_targets("(cd packs/a/scripts && python -m pytest -q -p no:cacheprovider)"),
           ["packs/a/scripts/"])
    _check("step-explicit-working-directory",
           M.extract_step_targets("python -m pytest test_x.py", "packages/credbroker"),
           ["packages/credbroker/test_x.py"])

    # `--ignore <dir>` names a tree pytest EXCLUDES. Reading it as a target would
    # mark that tree covered and silently retire every exemption beneath it.
    _check("pytest-ignore-value-not-a-target",
           M._pytest_path_args(
               "-m pytest packages/agentbundle/tests/ --ignore packs/converters/ -q"),
           ["packages/agentbundle/tests/"])
    _check("pytest-config-value-not-a-target",
           M._pytest_path_args("-m pytest tests/ -c tools/pytest.ini"), ["tests/"])
    _check("pytest-not-pytest", M._pytest_path_args("python3 tools/x.py"), None)

    # ── extract_ci_targets: the classifier itself ───────────────────────────
    c = M.extract_ci_targets({"jobs": {"b": {"steps": [
        {"name": "two targets", "run": "python3 tools/a.py\npython3 tools/b.py"},
        {"name": "nothing to declare", "run": "echo hello"},
        {"name": "composite gate", "uses": "./.github/actions/secret-scan"},
        "not a dict",
        {"name": "no run or uses"},
    ]}}}, "wf.yml")
    _check("classify-targets", sorted(c["by_step"]["two targets"]),
           ["tools/a.py", "tools/b.py"])
    _check("classify-target-attribution", c["where"]["two targets"],
           "wf.yml step 'two targets'")
    # THE ROSTER: every run:/uses: step is listed whether or not anything could be
    # extracted from it. That is what makes the disposition demand unconditional,
    # so an extractor miss can no longer remove the demand for a declaration.
    _check("classify-roster", c["steps"],
           ["two targets", "nothing to declare", "composite gate"])
    _check("classify-roster-includes-untargeted",
           "nothing to declare" in c["steps"] and "nothing to declare" not in c["by_step"],
           True)
    _check("classify-reusable-workflow-job",
           M.extract_ci_targets(
               {"jobs": {"g": {"uses": "./.github/workflows/r.yml"}}})["steps"],
           ["job g (reusable workflow)"])
    _check("classify-duplicate-names",
           M.extract_ci_targets({"jobs": {"b": {"steps": [
               {"name": "same", "run": "echo a"},
               {"name": "same", "run": "echo b"}]}}})["duplicates"],
           ["same"])

    # ── reachability is derived from the Makefile, never declared ───────────
    reach = M.derive_reachable_targets(MAKEFILE)
    for t in ("ci", "build-check", "test", "lint-ruff", "sast"):
        _check_true(f"reachable[{t}]", t in reach)
    _check("unreachable-zipapp", "zipapp" in reach, False)
    # Dropping a prerequisite from `ci:` must collapse coverage, not be ignored:
    # a hand-declared reachable set is the one table that could be widened to
    # make a parity failure disappear, and no staleness check catches that.
    thin_makefile = MAKEFILE.replace(
        "ci: build-check test lint-ruff", "ci: build-check lint-ruff")
    _check("dropped-prereq-loses-reachability",
           "test" in M.derive_reachable_targets(thin_makefile), False)
    full = M.makefile_recipe_targets(MAKEFILE, reach)
    thin = M.makefile_recipe_targets(
        thin_makefile, M.derive_reachable_targets(thin_makefile))
    _check_true("dropped-prereq-loses-coverage", len(full - thin) >= 2)

    # ── local coverage: invocation positions only ──────────────────────────
    _check_true("makefile-reachable-pytest-dir", "packages/agentbundle/tests/" in full)
    _check_true("makefile-reachable-script", "tools/lint-ruff.py" in full)
    for token in ("tools", "packs", "packages", "bandit.yaml", "Makefile"):
        _check(f"makefile-vars-not-coverage[{token}]", token in full, False)
    _check("makefile-unreachable-target", "tools/build_zipapp.py" in full, False)
    _check("makefile-ignore-value-not-coverage", "packs/converters/" in full, False)

    _check("script-step-reassembly", M.script_step_targets(GATE_CHAIN),
           {".claude/skills/x/lint-spec-status.py"})
    _check("prose-not-coverage[gate-chain]",
           "tools/never-run.py" in M.script_step_targets(GATE_CHAIN), False)
    _check("run-call-extraction", M.run_call_targets(AGGREGATOR),
           {"tools/lint-agents-md.py"})
    _check("prose-not-coverage[aggregator]",
           "tools/also-never-run.py" in M.run_call_targets(AGGREGATOR), False)

    _check_true("covered-exact", M.is_covered("a/b.py", {"a/b.py"}))
    _check_true("covered-dir-prefix", M.is_covered("a/b/c.py", {"a/b/"}))
    _check("uncovered-partial-name", M.is_covered("a/bc.py", {"a/b"}), False)

    # ── check(): the roster, then corroboration ─────────────────────────────
    def chk(classified, local, files, reachable=("test", "build-check"), **tables):
        tables.setdefault("dispositions", {})
        tables.setdefault("scope", ONLY_BUILD_CHECK)
        return M.check(classified, local, set(reachable), files, **tables)

    wf = {"build-check.yml"}
    LOCAL, CI_ONLY = M.LOCAL, M.CI_ONLY

    _check("check-clean",
           chk(_classified(["s"], {"s": ["a.py"]}), {"a.py"}, wf,
               dispositions={"s": LOCAL("test")}), [])
    _check("check-clean-ci-only",
           chk(_classified(["s"]), set(), wf,
               dispositions={"s": CI_ONLY("needs a GPU")}), [])

    # THE COMPLETENESS PROPERTY: a step with no disposition fails, whatever the
    # extractor did or did not see. This is the one check no shell shape defeats.
    _check_fires("check-undispositioned-step-fails",
                 chk(_classified(["brand new gate"]), set(), wf),
                 "no entry in STEP_DISPOSITION")
    _check_fires("check-undispositioned-even-when-target-looks-covered",
                 chk(_classified(["brand new gate"], {"brand new gate": ["a.py"]}),
                     {"a.py"}, wf),
                 "no entry in STEP_DISPOSITION")
    _check_fires("check-dead-disposition-fails",
                 chk(_classified(), set(), wf,
                     dispositions={"gone": CI_ONLY("was provisioning")}),
                 "dead STEP_DISPOSITION")
    # A LOCAL disposition must name a target `make ci` actually reaches, or the
    # claim "this is covered locally" is unfalsifiable.
    _check_fires("check-local-names-unreachable-target",
                 chk(_classified(["s"]), set(), wf,
                     dispositions={"s": LOCAL("zipapp")}),
                 "is not reachable from `make ci`")
    # Corroboration: extraction can contradict a LOCAL claim, and when it does the
    # human is wrong or the wiring is missing. An extractor bug here is a false
    # ALARM, never a false pass — that inversion is the design's point.
    _check_fires("check-local-contradicted-by-extraction",
                 chk(_classified(["s"], {"s": ["packs/x/test_a.py"]}), set(), wf,
                     dispositions={"s": LOCAL("test")}),
                 "not reachable from")
    _check_fires("check-empty-ci-only-reason-fails",
                 chk(_classified(["s"]), set(), wf, dispositions={"s": CI_ONLY("   ")}),
                 "empty reason")
    _check_fires("check-duplicate-step-name-fails",
                 chk(_classified(["s"], duplicates=["s"]), set(), wf,
                     dispositions={"s": CI_ONLY("x")}),
                 "appears more than once")
    _check_fires("check-unclassified-workflow-fails",
                 chk(_classified(), set(), wf | {"brand-new.yml"}), "not classified")
    _check_fires("check-vanished-workflow-fails",
                 chk(_classified(), set(), set()), "no longer exists")
    _check_fires("check-blank-scope-reason-fails",
                 chk(_classified(), set(), wf | {"new.yml"},
                     scope={"build-check.yml": M.IN_SCOPE, "new.yml": "  "}),
                 "empty reason")

    # ── prose in a Makefile recipe is not coverage ──────────────────────────
    # A tab-indented `#` line inside a reachable recipe used to be scanned like a
    # command: one comment naming `pytest packs/` made every `packs/**` gate read
    # covered, and `# historically: $(MAKE) zipapp` pulled an unreachable target
    # in. The live Makefile already carries such comment lines.
    commented = MAKEFILE.replace(
        "test:\n", "test:\n\t# flaky: re-enable pytest packs/; see tools/lint-x.py\n")
    prose_local = M.makefile_recipe_targets(
        commented, M.derive_reachable_targets(commented))
    _check("prose-not-coverage[makefile-path]", "tools/lint-x.py" in prose_local, False)
    _check("prose-not-coverage[makefile-pytest-dir]", "packs/" in prose_local, False)
    commented_make = MAKEFILE.replace(
        "build-check:\n", "build-check:\n\t# historically: $(MAKE) zipapp\n")
    _check("prose-not-coverage[makefile-sub-make]",
           "zipapp" in M.derive_reachable_targets(commented_make), False)

    # `$(MAKE) -C sub other` names `other`, not `-C`'s value.
    sub_make = "ci: b\nb:\n\t$(MAKE) -C sub other\nother:\n\techo hi\n"
    reach_sub = M.derive_reachable_targets(sub_make)
    _check_true("sub-make-target", "other" in reach_sub)
    _check("sub-make-not-flag-value", "sub" in reach_sub or "-C" in reach_sub, False)

    # Continuations and multi-target rules are ordinary Makefile shapes; dropping
    # them collapses coverage and reports the wrong cause.
    _check_true("continuation-prereq",
                "test" in M.derive_reachable_targets(
                    "ci: build-check \\\n\ttest\ntest:\n\techo hi\n"))
    multi = "ci: gateA\ngateA gateB:\n\tpython3 tools/g.py\n"
    _check_true("multi-target-rule",
                "tools/g.py" in M.makefile_recipe_targets(
                    multi, M.derive_reachable_targets(multi)))

    # `pytest` must be at a command position. `\bpytest\b` matched inside a path,
    # so `bash tools/run-pytest-suite.sh` read as a bare pytest invocation — and
    # with a working-directory that resolved to a covered dir, the step reported
    # covered while its real gate went unchecked.
    _check("pytest-in-path-is-not-pytest",
           M.extract_step_targets("bash tools/run-pytest-suite.sh"),
           ["tools/run-pytest-suite.sh"])
    _check("pytest-in-path-with-wd",
           M.extract_step_targets("bash run-pytest-helper.sh", "packs/core/tests"),
           ["packs/core/tests/run-pytest-helper.sh"])
    # `cd` persists across lines of one `run: |` body — it is one shell script.
    _check("cd-persists-across-lines",
           M.extract_step_targets("cd packs/x/scripts\npython -m pytest test_a.py"),
           ["packs/x/scripts/test_a.py"])
    # Job-level `defaults.run.working-directory` is the fallback when a step omits it.
    _check("job-defaults-working-directory",
           M.extract_ci_targets({"jobs": {"b": {
               "defaults": {"run": {"working-directory": "packages/credbroker"}},
               "steps": [{"name": "s", "run": "python -m pytest test_x.py"}]}}})["by_step"]["s"],
           ["packages/credbroker/test_x.py"])

    # A parenthesised `(cd x && …)` is a subshell: it prefixes its own line and
    # nothing after. Persisting it produced `packages/credbroker/tools/lint-new.py`,
    # which `make test`'s `packages/credbroker/` prefix covered — a brand-new gate
    # reporting clean. `build-check.yml` already uses that idiom.
    _check("subshell-cd-does-not-leak",
           M.extract_step_targets(
               "(cd packages/credbroker && python -m pytest -q)\n"
               "python3 tools/lint-brand-new-gate.py"),
           ["packages/credbroker/", "tools/lint-brand-new-gate.py"])
    _check("unresolvable-cd-clears",
           M.extract_step_targets("cd -\npython3 tools/g.py"), ["tools/g.py"])
    # An inline trailing comment in a recipe is not an invocation either — the
    # whole-line case was closed a round earlier and this one was still open, so a
    # comment could grant coverage for a gate deleted from the chain.
    inline = MAKEFILE.replace(
        "lint-ruff:\n", "lint-ruff:\n\t@true  # see also tools/lint-deleted.py\n")
    _check("prose-not-coverage[makefile-inline]",
           "tools/lint-deleted.py" in M.makefile_recipe_targets(
               inline, M.derive_reachable_targets(inline)), False)

    # Indirect coverage sources are themselves gated on reachability. Unioning
    # them unconditionally meant dropping `build-check` from `ci:` — which removes
    # the whole gate chain, `catalogue verify`, and the SAST leg — left the
    # coverage set byte-identical, so AC4d held only for the prerequisites whose
    # coverage came from a recipe line.
    real_makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    for prereq in ("build-check", "pre-pr", "test", "lint-ruff"):
        dropped = re.sub(rf"(?m)^(ci:.*) {re.escape(prereq)}\b", r"\1", real_makefile)
        _check(f"dropped-prereq-reachability[{prereq}]",
               prereq in M.derive_reachable_targets(dropped), False)
    dropped_bc = re.sub(r"(?m)^(ci:.*) build-check\b", r"\1", real_makefile)
    _check("dropped-build-check-drops-gate-chain",
           M.GATE_CHAIN in M.makefile_recipe_targets(
               dropped_bc, M.derive_reachable_targets(dropped_bc)), False)

    # ── the roster's improvement over extraction alone, and its residual ────
    # A NEW step whose only extracted target phantom-prefixes a covered directory
    # landed silently under the extraction-only design (round 4's Blocker 2 shape).
    # The roster fails it because the step is undispositioned, whatever the
    # extractor concluded — that is the whole reason the roster is the trust anchor.
    phantom = _classified(["brand new gate"],
                          {"brand new gate": ["packages/credbroker/tools/lint-new.py"]})
    _check_fires("roster-catches-phantom-covered-new-step",
                 chk(phantom, {"packages/credbroker/"}, wf),
                 "no entry in STEP_DISPOSITION")
    # And the residual, asserted so nobody reads more into the gate than it gives:
    # a hidden gate added INSIDE an already-dispositioned step is not caught. No
    # per-step scheme catches it; only reading the command would.
    hidden = _classified(["s"], {"s": ["a.py"]})
    _check("roster-residual-hidden-gate-in-known-step",
           chk(hidden, {"a.py"}, wf, dispositions={"s": LOCAL("test")}), [])

    # ── live: the real repo is parity-clean ────────────────────────────────
    res = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(REPO_ROOT)],
        capture_output=True, text=True, check=False,
    )
    _check("live-clean", res.returncode, 0)
    if res.returncode != 0:
        _FAILURES.append(f"live-clean output: {(res.stdout + res.stderr)!r}")

    # ── the gate actually FAILS: exit codes pinned end-to-end ───────────────
    # Every case above drives `check()` as a pure function, so `return 1` → `0`
    # would leave the violations printed, the chain green, and the suite passing.
    with tempfile.TemporaryDirectory() as td:
        fake = pathlib.Path(td)
        (fake / ".github" / "workflows").mkdir(parents=True)
        (fake / ".github" / "workflows" / "build-check.yml").write_text(
            "jobs:\n  b:\n    steps:\n      - name: a gate\n"
            "        run: python3 tools/nobody-runs-this.py\n", encoding="utf-8")
        (fake / "Makefile").write_text("ci:\n\techo hi\n", encoding="utf-8")
        (fake / "tools" / "repo").mkdir(parents=True)
        (fake / M.GATE_CHAIN).write_text("steps = []\n", encoding="utf-8")
        for rel in M.AGGREGATORS:
            (fake / rel).parent.mkdir(parents=True, exist_ok=True)
            (fake / rel).write_text("# no _run calls\n", encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(LINTER), "--root", str(fake)],
            capture_output=True, text=True, check=False,
        )
        _check("undispositioned-step-exits-1", res.returncode, 1)
        # The roster names the *step*, which is the thing a human dispositions —
        # the target is the extractor's business and no longer the trust anchor.
        _check_in("undispositioned-step-named", "'a gate'", res.stdout + res.stderr)
        _check_in("undispositioned-step-actionable", "STEP_DISPOSITION",
                  res.stdout + res.stderr)

    with tempfile.TemporaryDirectory() as td:
        res = subprocess.run(
            [sys.executable, str(LINTER), "--root", td],
            capture_output=True, text=True, check=False,
        )
        _check("missing-workflow-dir-exits-2", res.returncode, 2)

    # ── live: the wiring this spec added is load-bearing, asserted A/B ──────
    # Both sides go through the linter's own local_targets(), so a future third
    # coverage source cannot make this case quietly diverge from main().
    chain_text = (REPO_ROOT / M.GATE_CHAIN).read_text(encoding="utf-8")
    wired = M.local_targets(REPO_ROOT, chain_text)
    stripped = "\n".join(
        line for line in chain_text.splitlines()
        if "lint-catalogue-curation-guard.py" not in line
        and "lint-experience-agnostic.py" not in line
    )
    unwired = M.local_targets(REPO_ROOT, stripped)
    for gate in (
        "tools/lint-catalogue-curation-guard.py",
        "tools/test-lint-catalogue-curation-guard.py",
        "tools/lint-experience-agnostic.py",
        "tools/test-lint-experience-agnostic.py",
    ):
        _check_true(f"load-bearing-wired[{gate}]", M.is_covered(gate, wired))
        _check(f"load-bearing-unwired[{gate}]", M.is_covered(gate, unwired), False)

    # ── the Makefile's terminal verdict stays wired, and says the right thing ─
    # AC3's verification was manual QA, which produces a one-time observation. A
    # later edit dropping the call, commenting it out, or inverting the branch
    # would silently restore the "green, ship it" ambiguity the spec removed, and
    # no other gate reads the macro.
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    _check_true("verdict-macro-defined", "define gate_verdict" in makefile)
    for target in ("build-check", "ci"):
        # The recipe is the contiguous tab-indented block after the target line,
        # with comment lines excluded. A span regex that does not stop at `#`
        # swallowed the whole SAST comment block, so a commented-out call — a
        # shell no-op that prints nothing — still read as wired.
        recipe = _recipe_lines(makefile, target)
        _check_true(f"verdict-wired[{target}]",
                    any("$(call gate_verdict," in line for line in recipe))

    # Polarity, by execution rather than by grep: counting `printf`s and grepping
    # for `GITHUB_WORKFLOW` survives inverting the test, which would print the
    # reassuring CI line on a laptop — exactly the false assurance AC3a removes.
    if shutil.which("sh"):
        for label, env, expected, forbidden in (
            ("local-skip", {"SKIP_SAST": "1"},
             "INCOMPLETE — this is NOT a full pass", "complete for this diff"),
            ("ci-skip", {"SKIP_SAST": "1", "GITHUB_WORKFLOW": "build-check"},
             "complete for this diff", "INCOMPLETE"),
            ("full-run", {}, "complete — every leg of this target was invoked", "INCOMPLETE"),
        ):
            out = _run_verdict(makefile, env)
            _check_true(f"verdict-says[{label}]", expected in out)
            _check(f"verdict-omits[{label}]", forbidden in out, False)

        # The cases above must not depend on the ambient environment. Inside CI,
        # `GITHUB_WORKFLOW` really is `build-check`, which made `local-skip` take
        # the benign branch and turned this suite into the very local-vs-CI
        # divergence the spec exists to catch. Pin the scrub by running the
        # local-skip case with those variables ambient.
        polluted = dict(os.environ)
        os.environ.update({"GITHUB_WORKFLOW": "build-check", "GITHUB_ACTIONS": "true"})
        try:
            out = _run_verdict(makefile, {"SKIP_SAST": "1"})
            _check_true("verdict-ignores-ambient-ci-env",
                        "INCOMPLETE — this is NOT a full pass" in out)
        finally:
            os.environ.clear()
            os.environ.update(polluted)
    else:  # pragma: no cover — Windows contributor path
        print("… verdict polarity cases skipped: no `sh` on PATH")

    if _FAILURES:
        print(f"✖ {len(_FAILURES)}/{_CASES} cases failed:")
        for f in _FAILURES:
            print(f"  - {f}")
        return 1
    print(f"✓ all {_CASES} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
