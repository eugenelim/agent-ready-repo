#!/usr/bin/env python3
"""CI-parity gate: every step `build-check.yml` runs carries a disposition —
either the `make` target that covers it locally, or why no local gate can.

**The defect this exists to prevent.** `make ci`'s comment claimed for months that
it mirrored `build-check.yml`. It did not, and nothing said so. Two gates reached
CI red past a green local run (PR #872): the catalogue-curation guard, which had
no local equivalent anywhere, and the SAST leg, whose `SKIP_SAST=1` skip was a
mid-run `echo`. Wiring those two shut fixes today; it does not stop the next CI
step from landing with no local counterpart and no signal. This linter is the
standing check.

**Two layers, and only one of them is the trust anchor.**

*1 — the roster (`STEP_DISPOSITION`), complete and extraction-independent.* Every
`run:`/`uses:` step of an in-scope workflow must carry a disposition, and every
disposition must name a real step; both directions fail. `LOCAL("<target>")` must
name a target reachable from `make ci`; `CI_ONLY("<reason>")` must state one.
Nothing in this layer reads a shell command, so **no shell shape can defeat it**.

*2 — corroboration (extraction), best-effort.* For a step declared `LOCAL`, every
gate target the extractor does see must be locally covered. Because the roster
already carries completeness, a bug here can only raise a false alarm — never
grant a false pass. That inversion is the design's point.

An earlier version made layer 2 the anchor: whether a step needed a declaration
at all was decided by the extractor. Four review rounds each defeated it a
different way — over-broad coverage from a `:=` assignment, then a whole-line
recipe comment, then an inline one; `pytest` matched inside a path; a subshell
`cd` composing a phantom prefix that a directory match then covered. Each of the
six is fixed and pinned, but the class has no completeness proof, and a fix in
one round caused the defect in the next. So the anchor moved.

``WORKFLOW_SCOPE`` classifies every workflow file: in scope, or out with a reason.
A new workflow fails until classified, so "parity" cannot quietly come to mean
"parity with the one workflow we happened to pick".

**What this gate proves.** No step of an in-scope workflow can be added, renamed,
or removed without a human dispositioning it, and no `LOCAL` claim can name a
target `make ci` does not reach. Every declaration is a sentence a reviewer can
read and check.

**What it does not prove — the residual, stated plainly.** A gate added *inside a
step that already has a disposition* is not caught: the disposition is per step,
so a second command on a later line of an existing step changes nothing the roster
sees. Extraction catches that case only when the new command names a literal path
it can parse. **No per-step scheme closes this**; only executing or fully parsing
each command would. `tools/test-lint-ci-parity.py` asserts the residual explicitly
(`roster-residual-hidden-gate-in-known-step`) so nobody reads more into a clean
run than it gives.

`packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py` is
deliberately *not* a coverage source even though it invokes some of the same
linters: it runs only under `agentbundle catalogue self-host --windows`, so
counting it would let a Windows-only invocation certify a macOS `make ci` run.

## The second roster: which pull-request check gates each suite

`STEP_DISPOSITION` above answers "what covers this CI step locally".
`SUITE_DISPOSITION` answers the opposite question — "which pull-request check
gates this suite" — for every command the Makefile's `run-test-suite` define
runs. The two are different claims, and conflating them is the defect it exists
to prevent: suites reached only inside that define run under `make test` and
`test-after-build-check`, under neither `make build-check` nor any required
pull-request check, so a pull request could be green on every check while they
were red. Measured at 114 targets, 52 of them reached by no pull-request
workflow at all. `packs/frontend-engineering/tests/` shipped its own guards that
way.

`tools/lint-pack-test-boundary.py`'s `every-suite-dir-has-a-runner` answers a
third, narrower question — whether *anything* runs a pack suite, where the
Makefile counts as a runner. A suite can satisfy that rule and still be gated by
no pull request, which is exactly how the gap stayed invisible.

**Completeness is anchored on the define's recipe lines, not on extracted
targets.** `suite_lines` supplies the closed set, and it interprets no command:
it joins continuations, drops blank lines, drops a `#` line only when it holds no
`$(`, and strips a leading `@`. Keying the roster on the targets a command yields
would inherit the extractor's blind spots — a command it cannot read would
produce no key, demand no entry, and leave the gap silent one layer down.

## What the suite roster does not prove — the residual, stated plainly

Six limits, none of which a clean run rules out.

* **Completeness is extraction-independent at the LINE level, not at the target
  level.** `suite_lines` interprets no command, so no parser failure removes a
  recipe line from the roster. But which *targets* a line carries is read by
  `line_targets`, and a suite the extractor cannot see is caught only by the
  opaque-operand arm — which is itself extraction. A pytest operand that is
  neither a literal path nor a recognised expansion would escape.
* **Corroboration is best-effort in *both* directions**, unlike the forward
  gate's one-way claim. A false-positive extraction can satisfy a wrong
  `PR_GATED`; a false-negative one can let a stale `NO_PR_GATE` stand.
* **Corroboration proves a step names a suite, not that it runs it.**
  `echo "python -m pytest <suite>"` yields the same operand as a real
  invocation. A bare `echo <dir>` yields nothing, so a passing mention is
  excluded, but execution is not established.
* **`PR_GATED_IF` records a condition nobody evaluates.** A conditionally gated
  suite may simply not run on a given pull request.
* **A declared exception (`_SUITE_SOURCE_EXCEPTIONS`) asserts coverage rather
  than reading it,** and is the one source here that can grant coverage the
  workflow does not provide. Three things bound it: the named step's name must
  be unique in its workflow, every listed suite must appear in that step's own
  `run`, and that body is digest-pinned so any edit reddens a test and obliges a
  human to re-check. What none of that establishes is that the step *executes*
  the listed suites — only that the workflow text still says what it said when a
  human last looked. A parse was built for this shape instead and removed after
  seven defects in three review rounds, two of them phantom coverage.
* **A reason is checked for presence, never for truth.** `NO_PR_GATE("todo")`
  passes the lint. Whether a reason is accurate is a human-review control, and
  so is whether a `PR_GATED` step's command really executes the suite.

Separately, and not a limit of the roster: `run_with_floor` in `build-check.yml`
runs two suites through a subshell that `cd`s and runs bare `pytest`. Neither is
a `run-test-suite` target, so no entry depends on it; were one added, the
unrecognised shape would fail a *true* claim rather than pass a false one.

Both rosters compare *written* paths. Spell a path in a workflow exactly as the
define spells it: a parent directory matches neither direction and reports a real
gate as absent.

Usage:
    python tools/lint-ci-parity.py [--root .]

Exit codes: 0 = every step and every suite line dispositioned and corroborated,
1 = one or more violations, 2 = tool error (a workflow, the Makefile, or a local
gate source unreadable, PyYAML absent).
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

WORKFLOW_DIR = ".github/workflows"
# Sentinel passed alongside the workflow filenames when `.github/actions/` exists.
COMPOSITE_ACTION_DIR = "<.github/actions>"

# Every workflow file must be classified. IN_SCOPE → its gates are parity-checked.
# Out-of-scope → the reason, so "nothing gates this" is a written fact rather
# than an omission. A file here that no longer exists, or a file on disk missing
# from this map, is a violation.
#
# IN_SCOPE is an explicit sentinel, not the empty string: `""` would make the
# most important entry in this table indistinguishable from a forgotten reason,
# and copy-pasting that line would pull a new workflow into scope silently.
IN_SCOPE = None

WORKFLOW_SCOPE: dict[str, str | None] = {
    "build-check.yml": IN_SCOPE,
    "test-corpus.yml":
        "Out of scope, and deliberately so. Each of its four matrix jobs invokes "
        "`make test` undecomposed — the matrix varies only a shard integer, and "
        "selection lives in the Makefile (tools/shard_test_roster.py reads "
        "`make -n test-unleased`), so the workflow still enumerates no suite and "
        "there is nothing for a parity check to compare. Sharding moved where "
        "the roster runs, not what states it. Dispatch-only: it runs on no pull "
        "request, so it gates nothing and claims nothing beyond what `make test` "
        "claims (spec/remote-gate-dispatch).",
    "test-roster.yml":
        "Out of scope. It runs one suite in parallel, which is deliberately NOT "
        "equivalent to any local invocation: `make test` reaches the roster "
        "serially through its `tests/` sweep. Parity is not the claim, so a "
        "parity check would assert a correspondence this surface disclaims. "
        "Dispatch-only (spec/remote-gate-dispatch).",
    "build-check-windows.yml":
        "Windows runner; drives `agentbundle catalogue self-host --check "
        "--windows`, which a macOS/Linux `make ci` cannot reproduce.",
    "docs.yml":
        "Out of scope for this gate. `make pre-pr` overlaps much of it "
        "incidentally, but nothing verifies that overlap.",
    "catalogue-tooling-ci-gates.yml":
        "Out of scope; same backlog entry as docs.yml. Note: this one bites — "
        "its Gate B fixture is a synthetic external catalogue built by "
        "`agentbundle catalogue build`, so an engine change can redden it "
        "while every `make` target stays green. That happened once "
        "(docs/specs/claude-plugin-route-scope): a route filter emptied the "
        "fixture's marketplace and the build raised. Reproduce locally with "
        "`make external-catalogue-smoke`, which copies "
        "tools/tests/fixtures/external-catalogue-smoke/`.",
    "ci-security.yml":
        "Out of scope; same backlog entry as docs.yml.",
    "codeql.yml": "GitHub-hosted analysis; no local equivalent exists.",
    "pack-evals.yml":
        "Runs live model evals against a metered API; deliberately not a local "
        "gate.",
    "pages.yml":
        "Deploy workflow. Its built-output `check-site-plugin-offers.py` "
        "assertion is intentionally non-blocking because it requires the full "
        "site build; the assertion's self-test remains in the blocking local "
        "build gate chain. Since spec/docs-site-build-contract-hardening it ALSO "
        "carries one hard gate — the rehype plugin suite, whose local counterpart "
        "is `make test` (npm run test:plugins --prefix docs-site) and whose "
        "presence, ordering and path filters are pinned by "
        "tools/test-pages-workflow.py, run from the required gate-main. It blocks "
        "the deploy, not the merge: this workflow is not a required context.",
    "publish-catalogue.yml": "Publish workflow, not a gate.",
    "publish-claude-plugins.yml": "Publish workflow, not a gate.",
    "release-agentbundle.yml":
        "Release workflow. It carries one hard gate — RFC-0082's "
        "export-boundary check — whose local counterpart is `make test` "
        "(tools/test_check_artifact_contents.py) and whose presence in the "
        "workflow is pinned by test_the_gate_step_is_actually_invoked. "
        "Everything else here is release plumbing.",
    "release-credbroker.yml": "Release workflow, not a gate.",
    "release-jsonl-otlp-exporter.yml": "Release workflow, not a gate.",
    "iac-release-loop-canary.yml": "Scheduled canary against live infra.",
    "iac-staleness.yml": "Scheduled staleness probe against live infra.",
}

# The entrypoint whose reachability defines "locally covered". The reachable set
# is *derived* from the Makefile, never declared: a hand-written list is the one
# table that could be widened to silence a parity failure, which spec § Never do
# bans and a frozenset cannot enforce. `zipapp`, `site-sync`, `validate`, and
# `release-preflight` name script paths `make ci` never runs, and the derivation
# is what keeps them out.
CI_ENTRYPOINT = "ci"

# Local sources read at invocation positions only.
GATE_CHAIN = "tools/repo/build_gate_chain.py"
AGGREGATORS = ("tools/catalogue/pre_pr_catalogue.py", "tools/hooks/pre-pr.py")

# Command prefixes that provision the environment rather than run a gate. Their
# arguments (requirements files, package pins) are not gate targets. Matched per
# shell segment, not per line: `pip install x && python3 tools/gate.py` must
# still yield the gate. A leading `sudo` is stripped before matching, so
# `sudo apt-get install …` is provisioning while `sudo python3 tools/gate.py`
# is not.
PROVISIONING = (
    "pip", "pip3", "python -m pip", "python3 -m pip",
    "apt-get", "npm", "brew",
)

# A path-shaped token: no whitespace, ends in .py or .sh.
_PATH_TOKEN = re.compile(r"[A-Za-z0-9_./\\-]+\.(?:py|sh)\b")
# `-m pytest a/ b/ -q` — the non-flag arguments are gate targets even without an
# extension, which is how `make test`'s directory roots are seen. Bare `pytest`
# counts too: CI writes `python -m pytest`, the Makefile writes `$(PYTHON) -m
# pytest`, and a `cd … && pytest` form is plausible.
#
# `pytest` must sit at a *command* position — whitespace or line start before it,
# whitespace or line end after. `\bpytest\b` also matched inside a path, so
# `bash tools/run-pytest-suite.sh` was read as a pytest invocation with no path
# argument; combined with a `working-directory` that resolved to a covered
# directory, the step reported covered while its real gate went unchecked.
_PYTEST_ARGS = re.compile(r"(?:^|\s)(?:-m\s+)?pytest(?=\s|$)(.*)$")

# pytest flags whose *next* token is a value, not a path. Reading a value as a
# target is the fatal direction: `--ignore packs/converters/` would mark an
# excluded tree covered and retire every exemption beneath it.
_PYTEST_VALUE_FLAGS = frozenset({
    "-c", "-p", "-k", "-m", "-o", "-n", "-W", "--ignore", "--ignore-glob",
    "--rootdir", "--cov", "--deselect", "--confcutdir", "--junitxml", "--basetemp",
})
# `_script_step("label", "tools", "catalogue", "x.py")` — the path arrives split
# across arguments, so reassemble it or the chain's own steps read as uncovered.
# `[^)]*` is deliberate: the earlier `(?:"[^"]*"\s*,?\s*)+` form had two ways to
# consume each separator and backtracked exponentially on an unterminated call —
# ~3s at 24 arguments, i.e. a mid-edit syntax error hung `make build-check` with
# no diagnostic. Call arguments contain no `)`, so this is both linear and exact.
_SCRIPT_STEP = re.compile(r"_script_step\(([^)]*)\)", re.S)
# `_pytest_step_cwd("label", "<dir>", "<target>", ...)` — the directory-scoped
# step kind. Its targets are bare filenames resolved against the cwd, so a
# literal scan for repo-root paths would miss them entirely and report the
# gate as CI-only when it is wired locally.
_PYTEST_STEP_CWD = re.compile(r"_pytest_step_cwd\(([^)]*)\)", re.S)
_RUN_CALL = re.compile(r"_run\(\s*(.*?)\)", re.S)
_QUOTED = re.compile(r"\"([^\"]*)\"")

# ── The disposition roster: one entry per `run:`/`uses:` step ────────────────
#
# This is the gate's completeness property, and it does not depend on the
# extractor. Every step of an in-scope workflow must appear here, and every entry
# must correspond to a real step — both directions fail. A step added in *any*
# shape (inline shell, a composite `uses:` action, a form the extractor cannot
# parse) fails until a human dispositions it.
#
# That is the fix for what four review rounds kept finding: previously, whether a
# step needed a declaration at all was decided by the extractor, so an extractor
# miss meant no declaration was ever demanded. Now the roster demands one
# unconditionally and extraction only *corroborates* — see `check()`.
#
#   LOCAL("<make target>")  the target that covers this step. Must be reachable
#                           from `make ci`, and every gate target the extractor
#                           does see for this step must be locally covered.
#   CI_ONLY("<reason>")     no local gate runs it, and why. Provisioning steps,
#                           suites needing unvendored libraries, inline shell with
#                           no repo script to call.
#
# Authored from what the gate already concluded rather than by hand, then
# reviewed; `tools/test-lint-ci-parity.py` pins the invariants.


def LOCAL(make_target: str) -> tuple[str, str]:
    return ("local", make_target)


def CI_ONLY(reason: str) -> tuple[str, str]:
    return ("ci-only", reason)


def PR_GATED(where: str) -> tuple[str, str]:
    """Declare a suite reached by an unconditional pull-request check."""
    return ("pr-gated", where)


def PR_GATED_IF(where: str, condition: str) -> tuple[str, str, str]:
    """Declare a suite reached only when *condition* holds.

    `where` and `condition` stay SEPARATE fields. Joining them into one string
    broke both checks that read this entry: corroboration compares a source's
    `where` for equality, which a joined value never matches, so every
    conditional claim went unverified; and the empty-reason check reads the same
    value, which a blank condition leaves non-empty, so it could not fire.
    """
    return ("pr-gated-if", where, condition)


def NO_PR_GATE(reason: str) -> tuple[str, str]:
    """Declare why a suite has no pull-request gate."""
    return ("no-pr-gate", reason)


STEP_DISPOSITION: dict[str, tuple[str, str]] = {
    "<unnamed step in build-check>":
        CI_ONLY(
            "`uses: actions/checkout` in the AGGREGATOR job (this key is job-id "
            "scoped, and the aggregator kept the id `build-check`). Deliberately "
            "shallow — AC12 exempts it from fetch-depth: 0 because it runs one "
            "stdlib script over one workflow file and touches no history — and "
            "persist-credentials: false. No local equivalent: a working tree is the "
            "local precondition, not a gate."
        ),
    "Detect whether SAST-relevant files changed":
        CI_ONLY(
            "Computes an output for a later step; reads SAST_DIRS/SAST_CONFIG "
            "from the Makefile, so it cannot drift from them by construction."
        ),
    "Set up Python":
        CI_ONLY(
            "`uses: actions/setup-python@v5`. Provisioning."
        ),
    "Install tools dependencies":
        CI_ONLY(
            "Provisioning."
        ),
    "Install SAST/SCA tools":
        CI_ONLY(
            "Provisioning."
        ),
    "Install bandit unconditionally (lint-nosec-form's ID registry)":
        CI_ONLY(
            "Provisioning — but not interchangeable with the conditional step "
            "above, which is why it is a separate row. `make build-check` "
            "chains lint-nosec-form.py on every run, and its unknown-test-id "
            "check reads bandit's registry; without bandit that check silently "
            "no-ops. Behind the skip_sast condition it was inert on exactly the "
            "diffs it exists for. Locally the contributor already has bandit "
            "(tools/requirements-sast.txt), so there is no make target to name."
        ),
    "Run make build-check":
        LOCAL("build-check"),
    # ── build-check.yml is FIVE jobs: four work jobs + the aggregator ────────
    # spec/ci-gate-parallelization split out gate-sast and gate-export-boundary;
    # spec/ci-gate-credbroker added gate-credbroker.
    # `make build-check` still covers gate-main ∪ gate-sast, but NO single local
    # command equals any single CI job — gate-main runs the local gate minus SAST.
    # That is AC16's one-to-many parity model; per-job reproduction is
    # `make build-check SAST_DELEGATED=1` and `make sast` respectively.
    "<unnamed step in gate-main>":
        CI_ONLY(
            "`uses: actions/checkout@v4` — repository checkout. No local "
            "equivalent; a working tree is the local precondition, not a gate."
        ),
    "<unnamed step in gate-sast>":
        CI_ONLY("Repository checkout for the SAST job."),
    "Set up Python (gate-sast)":
        CI_ONLY("Interpreter provisioning; pinned per AC12."),
    "Run make sast":
        LOCAL("sast"),
    "<unnamed step in gate-export-boundary>":
        CI_ONLY(
            "Repository checkout for the export-boundary job. Deliberately NOT "
            "sparse: the suite's real-artifact tests skipif on "
            "packages/agentbundle being a directory (AC14)."
        ),
    "Set up Python (gate-export-boundary)":
        CI_ONLY("Interpreter provisioning; pinned per AC12."),
    "Install tools dependencies (gate-export-boundary)":
        CI_ONLY(
            "Provisioning. `build` and `setuptools` come from here; without them "
            "the suite's wheel check skips while reporting green."
        ),
    "Install agentbundle (editable) + pytest (gate-export-boundary)":
        CI_ONLY("Provisioning; the gate declares pytest in _DEPENDENCY_IMPORTS."),
    "Install credbroker (editable, with crypto extra) (gate-export-boundary)":
        CI_ONLY(
            "Provisioning. check-artifact-contents.py's _DEPENDENCY_IMPORTS "
            "includes credbroker and RAISES on a miss."
        ),
    "<unnamed step in gate-credbroker>":
        CI_ONLY(
            "Repository checkout for the credbroker job. Deliberately SHALLOW — no "
            "fetch-depth: 0, because packages/credbroker invokes git nowhere; the "
            "same carve-out the aggregator carries. No local equivalent: a working "
            "tree is the local precondition, not a gate."
        ),
    "Set up Python (gate-credbroker)":
        CI_ONLY("Interpreter provisioning; pinned per AC12."),
    "Install credbroker (editable, with crypto extra) + pytest (gate-credbroker)":
        CI_ONLY(
            "Provisioning, and the whole of this job's dependency need: the suite "
            "imports only stdlib, pytest, credbroker, and cryptography/argon2 from "
            "the [crypto] extra. The extra is not optional — without it 21 vault "
            "tests and 11 @requires_crypto cases skip silently, which is why the "
            "pytest step below probes for it rather than trusting this step."
        ),
    "Set up Python (aggregator)":
        CI_ONLY("Interpreter provisioning for the posture test."),
    "Run the build-check.yml posture test":
        LOCAL("build-check"),
    "Require every gate":
        CI_ONLY(
            "Consults needs.*.result across sibling jobs. No local target can "
            "reproduce it — `make ci` runs the legs directly rather than through "
            "GitHub's scheduler. This is the residual AC16 names, and it is why "
            "this step is split from the posture test above, which IS local."
        ),
    "Install ripgrep":
        CI_ONLY(
            "Provisioning."
        ),
    "Install agentbundle (editable) + pytest":
        CI_ONLY(
            "Provisioning."
        ),
    "Install ruff + mypy":
        CI_ONLY(
            "Provisioning."
        ),
    "ruff lint (style, imports, common bugs)":
        LOCAL("lint-ruff"),
    "mypy type-check (typed packages only)":
        LOCAL("lint-mypy"),
    "pytest version constants (CLI_VERSION ↔ pyproject drift guard)":
        LOCAL("test-after-build-check"),
    "pytest adapter resolver (RFC-0011/0012, ADR-0004 rebrand)":
        LOCAL("test-after-build-check"),
    "pytest converters install/uninstall (AC6a)":
        LOCAL("test-after-build-check"),
    "pytest pack-profiles (RFC-0034)":
        LOCAL("test-after-build-check"),
    "pytest convenient-install-defaults (RFC-0046)":
        LOCAL("test-after-build-check"),
    "pytest credbroker floor precedence (credbroker-user-scope T1)":
        LOCAL("test-after-build-check"),
    "pytest shared-libs projection retirement (credbroker T9)":
        LOCAL("test-after-build-check"),
    "pytest self-host recipe config (externalize-self-host-config)":
        LOCAL("test-after-build-check"),
    "pytest self-host fixture guard (windows-build-self-entry)":
        LOCAL("test-after-build-check"),
    "pytest make-free gate chains (windows-build-gate-chain)":
        LOCAL("test-after-build-check"),
    "pytest import-time path leaks (collector sys.path guard)":
        LOCAL("test-after-build-check"),
    "pytest gitattributes merge-driver scope (AC1)":
        LOCAL("test-after-build-check"),
    "pytest merge-driver behaviour (AC2-AC4)":
        LOCAL("test-after-build-check"),
        "pytest guides sidebar generation":
            LOCAL("test-after-build-check"),
        "pytest journey editorial decisions":
            LOCAL("test-after-build-check"),
    # Both wired by docs/specs/build-check-coverage-gaps. The seven files these
    # two steps run were on `make test`'s Makefile line and in no workflow's
    # run: steps — locally gated, remotely not.
    "pytest guides + catalogue navigation":
        LOCAL("test-after-build-check"),
    # Its own step rather than an append to the guides step: that step's body is
    # pinned whole by `site-guides-body-exact`, and this suite is neither a guides
    # nor a navigation check.
    "pytest stasis-stop retirement claims":
        LOCAL("test-after-build-check"),
    "pytest site build + link rewriting":
        LOCAL("test-after-build-check"),
    # spec/site-ci-contract-closure AC4/AC6. Both halves are reachable from
    # `make ci` via the `test-after-build-check` target: the checker on its own
    # line near the top, and its suite on the site/catalogue pytest line.
    "docs palette contrast gate":
        LOCAL("test-after-build-check"),
    # spec/docs-site-build-contract-hardening AC7. Reachable from `make ci` via
    # `test-after-build-check`, which invokes the same script.
    "pages.yml deploy-gate posture":
        LOCAL("test-after-build-check"),
    # The Pages concurrency checker is independently reachable from `make ci`
    # through `test-after-build-check`, and runs in required gate-main so it
    # cannot become the unwired workflow-posture anti-pattern.
    "pages.yml concurrency posture":
        LOCAL("test-after-build-check"),
    # RFC-0082 export boundary. The gate itself runs in release-agentbundle.yml;
    # this step runs the gate's own tests, so a regression to always-exit-0 goes
    # red here rather than staying silently green.
    "pytest export-boundary gate":
        LOCAL("test-after-build-check"),
    "Install credbroker (editable, with crypto extra)":
        CI_ONLY(
            "Provisioning."
        ),
    "pytest credbroker (RFC-0023 Phase 1)":
        LOCAL("test-after-build-check"),
    "pytest credential-setup skill (RFC-0023 T8 + missing-credbroker guard)":
        CI_ONLY(
            "PROVISIONING, and DECIDED to stay here (2026-08-16). The suite "
            "spawns setup.py as a subprocess, and that script hard-exits 3 when "
            "credbroker is not INSTALLED; a source path on PYTHONPATH does not "
            "satisfy it (verified in CI, twice). Moving it would mean "
            "`pip install -e ./packages/credbroker` inside `make build-check`, "
            "which is already heavy and is otherwise install-free and offline. "
            "The suite's subject is installed-package behaviour, so running it "
            "against a source path would test something no adopter experiences "
            "— CI is its honest home, not a compromise. Do not re-open this as "
            "a step-vocabulary gap: the chain has `_pytest_step_cwd`."
        ),
    "pip install httpx for the atlassian SSO suites (RFC-0035)":
        CI_ONLY(
            "Provisioning."
        ),
    "pytest jira SSO suites (atlassian-sso-cookie)":
        CI_ONLY(
            "needs httpx>=0.27 (RFC-0035 step installs it)."
        ),
    "pytest confluence-crawler SSO suites (atlassian-sso-cookie)":
        CI_ONLY(
            "needs httpx>=0.27 (RFC-0035 step installs it)."
        ),
    "pytest catalogue-test carve-out destinations (RFC-0082)":
        LOCAL("test-after-build-check"),
    "pytest frontend-engineering pack suite (pr-gate-suite-disposition)":
        LOCAL("test-after-build-check"),
    "pytest shared-test dedup guard (pr-gate-suite-disposition)":
        LOCAL("test-after-build-check"),
    "pytest pack-test compatibility class characterization (ADR-0101)":
        CI_ONLY(
            "deliberately not local: proving isolated-vs-grouped collection "
            "equivalence spawns 30 collect-only pytest processes (~36s), more "
            "launches than the compatibility classes remove, so wiring it into "
            "`make test` would leave the local loop slower than before the "
            "change. The local signal is the ~2s two-check "
            "lint-pack-test-boundary invocation, which covers the silent hazard "
            "this step cannot see."
        ),
    "pytest user-libs vendored floor (credbroker-user-scope T3)":
        LOCAL("test-after-build-check"),
    "pytest cursor adapter (cursor-full-parity)":
        LOCAL("test-after-build-check"),
    "pytest gemini adapter (gemini-full-parity)":
        LOCAL("test-after-build-check"),
    "pytest architect design-reviewer guards (RFC-0032)":
        LOCAL("test-after-build-check"),
    "pytest enriched-pack-manifest (RFC-0031)":
        LOCAL("test-after-build-check"),
    "pytest catalogue Wave 4 live contracts (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest consolidated-pack-layout installer append (RFC-0040)":
        LOCAL("test-after-build-check"),
    "pytest kiro drop-warning contract":
        LOCAL("test-after-build-check"),
    "pytest core work-loop activation hook (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest package pytest pythonpath (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest shaping-review contracts (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest RFC-0099 activation + fixture register (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest TDD stub lifecycle contract (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest loop-telemetry contracts (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest agent-skill-engineering consumer integrations (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest curation QA + RFC template contracts (roster-owned)":
        LOCAL("test-after-build-check"),
    "pytest CLI-hygiene sweep (agentbundle-cli-hygiene)":
        LOCAL("test-after-build-check"),
    "converters source-attribution scrub (AC2)":
        CI_ONLY(
            "Inline `rg` scrub; needs ripgrep, which the workflow apt-installs. "
            "No repo script to call — reimplementing it locally would create a "
            "second implementation of one gate."
        ),
    "converters Rail-C marker scrub (AC3)":
        CI_ONLY(
            "Inline `rg` scrub; same reason as the AC2 scrub above."
        ),
    "converters evals.json carry-over disposition (AC4 + AC4a)":
        CI_ONLY(
            "Inline shell loop with an embedded `python3 -c` assertion; no repo "
            "script to call, so there is no path to wire or exempt."
        ),
    "pytest markdown-to-html installed entry-point contract":
        LOCAL("test-after-build-check"),
    "pytest mermaid-renderer installed entry-point contract":
        LOCAL("test-after-build-check"),
    "pip install the Markdown→Office render libraries (RFC-0036)":
        CI_ONLY(
            "Provisioning."
        ),
    "pytest markdown-to-pptx renderer (markdown-to-office-publishing)":
        CI_ONLY(
            "needs python-pptx==1.0.2 (RFC-0036 step installs it)."
        ),
    "pytest markdown-to-docx renderer (markdown-to-office-publishing)":
        CI_ONLY(
            "needs docxtpl==0.20.2 + python-docx==1.2.0 (RFC-0036 step installs "
            "them)."
        ),
    "pytest markdown-to-xlsx renderer (markdown-to-office-publishing)":
        CI_ONLY(
            "needs openpyxl==3.1.5 (RFC-0036 step installs it)."
        ),
    "pip install the Tier-0 PDF library (extraction-tier0)":
        CI_ONLY(
            "Provisioning."
        ),
    "pytest file-to-markdown extraction (extraction-tier0-and-output-contract)":
        CI_ONLY(
            "needs pypdf==5.1.0 (extraction-tier0 step installs it)."
        ),
    "pip install the Tier-0 .msg reader (extraction-msg olefile, ADR-0046)":
        CI_ONLY(
            "Provisioning."
        ),
    "pytest msg-to-markdown extraction (extraction-msg-to-markdown-python-contract)":
        CI_ONLY(
            "needs olefile==0.47 (ADR-0046 step installs it)."
        ),
    "catalogue-curation guard lint + self-test (RFC-0059 D6)":
        LOCAL("build-check"),
    "catalogue-curation skill-script tests (RFC-0059 security ACs)":
        LOCAL("build-check"),
    "experience framework-agnosticism lint + self-test (design-craft-pack AC8)":
        LOCAL("build-check"),
    "pack description drift backstop + self-test":
        LOCAL("build-check"),
}


# This roster is deliberately written from the expanded `test-unleased` recipe,
# then reviewed against pull-request workflows.  Its closed set is the recipe
# lines, not what the parser happens to recognise.
# ── The inverse roster: one entry per command the define runs ────────────────
#
# `STEP_DISPOSITION` above answers "what covers this CI step locally". This one
# answers the opposite question — "which pull-request check gates this suite" —
# and the two are not the same claim. `tools/lint-pack-test-boundary.py`'s
# `every-suite-dir-has-a-runner` rule answers a third, narrower one: whether
# *anything* runs a pack suite, where the Makefile counts. A suite can satisfy
# that rule and still be gated by no pull request, which is exactly how
# `packs/frontend-engineering/tests/` came to ship its own guards PR-ungated.
#
# **Completeness is anchored on the define's recipe lines, not on extracted
# targets.** `suite_lines` supplies the closed set. Keying this roster on the
# targets a command yields would inherit the extractor's blind spots: a command
# it cannot read would produce no key, demand no entry, and leave the gap silent
# one layer down from the defect this exists to close. `npm run test:plugins` is
# the live proof — a real `node --test` suite that yields no path operand at all.
#
#   PR_GATED(where)              a step of an unfiltered, unconditional
#                                pull-request workflow runs it. Corroborated.
#   PR_GATED_IF(where, why)      a pull-request workflow runs it, but only
#                                sometimes — a path filter, or a conditional
#                                step or job. A weaker claim, stated as one.
#   NO_PR_GATE(reason)           no pull-request check runs it, and why.
#
# Authored from what `pr_gate_sources` concluded, then reviewed entry by entry —
# the same way `STEP_DISPOSITION` above was built. The lint checks that a reason
# is *present*; whether it is *true* is a human-review control.
# The source strings and conditions that many entries share. Written once
# because the roster wrote them out 21, 6 and 21 times respectively, and a
# renamed job or step then meant that many synchronised edits plus a flood of
# identical violations. The KEYS stay explicit per suite — a roster whose keys
# were also derived would stop being a declaration, which is the property the
# whole design rests on.
_PACK_HOOK_LINUX = (
    "catalogue-tooling-ci-gates.yml / pack-hook-tests / "
    "Run repo/pack hook suites (Linux)"
)
_WHY_PATH_FILTERED = (
    "its workflow's pull_request trigger carries a path filter, so a pull "
    "request outside that filter does not run it"
)
_WHY_FILTERED_AND_CONDITIONAL = (
    "its workflow's pull_request trigger carries a path filter and its step or "
    "job is conditional, so a pull request outside that filter does not run it"
)


SUITE_DISPOSITION: dict[str, tuple[str, ...]] = {
    'packages/agentbundle/tests/':
        PR_GATED_IF(
            "catalogue-tooling-ci-gates.yml / agentbundle-tests / Run full agentbundle test "
            "suite (Linux)",
            _WHY_PATH_FILTERED,
        ),
    'packages/credbroker/':
        PR_GATED(
            "build-check.yml / gate-credbroker / pytest credbroker (RFC-0023 Phase 1)"
        ),
    'packages/jsonl-otlp-exporter/':
        NO_PR_GATE(
            "Distribution suite for jsonl-otlp-exporter. `make test` runs it; no pull-request "
            "workflow names it. release-jsonl-otlp-exporter.yml runs on a tag, not a pull "
            "request."
        ),
    'tools/lint-conformance-portability.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/lint-direct-code-table.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/check-docs-contrast.py':
        PR_GATED(
            "build-check.yml / gate-main / docs palette contrast gate"
        ),
    'tools/test-pages-workflow.py':
        PR_GATED(
            "build-check.yml / gate-main / pages.yml deploy-gate posture"
        ),
    'tools/test-pages-concurrency.py':
        PR_GATED(
            "build-check.yml / gate-main / pages.yml concurrency posture"
        ),
    'tests/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/core/tests/hooks/':
        PR_GATED_IF(
            "catalogue-tooling-ci-gates.yml / pack-hook-tests / Run pack hook suites (Windows — "
            "curated portable subset)",
            _WHY_PATH_FILTERED,
        ),
    'packs/core/tests/pack/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/core/tests/skills/adapt-to-project/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/author-brief/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the core batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/core/tests/skills/author-delivery-brief/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the core batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/core/tests/skills/bug-fix/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/capture-work/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/close-work/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/contract-acquisition/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the core batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/core/tests/skills/intake-intent/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the core batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/core/tests/skills/new-spec/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the core batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/core/tests/skills/project-knowledge/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/receive-brief/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/work-intake/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/work-loop/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/core/tests/skills/workspace-status/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/catalogue-curation/tests/pack/':
        NO_PR_GATE(
            "Pack suite for catalogue-curation. `make test` runs it; no workflow names it, so it "
            "reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/catalogue-curation/tests/skills/compile-okf/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the catalogue-curation batch; no workflow "
            "names it, so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/product-documentation/tests/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/frontend-engineering/tests/skills/frontend-engineering/':
        PR_GATED(
            "build-check.yml / gate-main / pytest frontend-engineering pack "
            "suite (pr-gate-suite-disposition)"
        ),
    'packs/architect/tests/pack/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/architect/tests/skills/architect-assess/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/architect/tests/skills/architect-design/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the architect batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/architect/tests/skills/architect-review/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the architect batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/credential-brokers/tests/pack/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/atlassian/tests/skills/jira/test_intake_policy.py':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the atlassian batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/atlassian/tests/skills/jira-align/test_jira_align_intake_policy.py':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the atlassian batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/atlassian/tests/skills/flow-metrics/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/atlassian/tests/skills/jira-brief-intake/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the atlassian batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/atlassian/tests/skills/jira-align-brief-intake/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the atlassian batch; no workflow names it, "
            "so it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/github/tests/skills/github-brief-intake/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the github batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/product-engineering/tests/pack/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/agent-skill-engineering/tests/pack/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/agent-skill-engineering/tests/integration/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/agent-skill-engineering/tests/skills/author_or_update/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/agent-skill-engineering/tests/skills/review_or_optimize/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/linear/tests/skills/linear/':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'packs/linear/tests/skills/linear-brief-intake/':
        NO_PR_GATE(
            "Pack skill suite. `make test` runs it in the linear batch; no workflow names it, so "
            "it reaches CI only through the dispatch-only test-corpus.yml."
        ),
    'packs/converters/tests/skills/markdown-to-html/':
        PR_GATED(
            "build-check.yml / gate-main / pytest markdown-to-html installed entry-point "
            "contract"
        ),
    'packs/converters/tests/skills/mermaid-renderer/':
        PR_GATED(
            "build-check.yml / gate-main / pytest mermaid-renderer installed entry-point "
            "contract"
        ),
    'packs/desk-research/tests/skills/desk-research/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/desk-research-project-start/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/pack/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/desk-research-project-check/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/desk-research-project-digest/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/desk-research-project-status/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/desk-research-project-synthesize/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'packs/desk-research/tests/skills/devils-advocate/':
        PR_GATED_IF(
            _PACK_HOOK_LINUX,
            _WHY_FILTERED_AND_CONDITIONAL,
        ),
    'tools/test_build_gate_chain.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest make-free gate chains "
            "(windows-build-gate-chain)"
        ),
    'tools/test_journey_editorial_decisions.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest journey editorial decisions"
        ),
    'tools/test_catalogue_tooling_rewire.py':
        PR_GATED_IF(
            "catalogue-tooling-ci-gates.yml / catalogue-repo-rewire / pytest rewire tests",
            _WHY_PATH_FILTERED,
        ),
    'tools/test_catalogue_tooling_docs.py':
        PR_GATED_IF(
            "catalogue-tooling-ci-gates.yml / catalogue-repo-rewire / pytest docs contract tests",
            _WHY_PATH_FILTERED,
        ),
    'tools/test_validate_guides.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides + catalogue navigation"
        ),
    'tools/test_check_guide_index.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides + catalogue navigation"
        ),
    'tools/test_catalogue_navigation.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides + catalogue navigation"
        ),
    'tools/test_documentation_entry_links.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides + catalogue navigation"
        ),
    'tools/test_build_site_link_rewrites.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest site build + link rewriting"
        ),
    'tools/test_check_rendered_site_links.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest site build + link rewriting"
        ),
    'tools/test_build_site_routing.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest site build + link rewriting"
        ),
    'tools/test_check_docs_contrast.py':
        PR_GATED(
            "build-check.yml / gate-main / docs palette contrast gate"
        ),
    'tools/test_build_site_inventory.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides sidebar generation"
        ),
    'tools/test_build_site_projection.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides sidebar generation"
        ),
    'tools/test_build_site_sidebar.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest guides sidebar generation"
        ),
    'tools/test_browser_gate_subset.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest site build + link rewriting"
        ),
    'tools/test_stasis_retirement_claims.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest stasis-stop retirement claims"
        ),
    'tools/test_local_ci_shared_test_deduplication.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest shared-test dedup guard "
            "(pr-gate-suite-disposition)"
        ),
    'tools/test_gitattributes_merge_driver.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest gitattributes merge-driver scope (AC1)"
        ),
    'tools/test_merge_driver_behaviour.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest merge-driver behaviour (AC2-AC4)"
        ),
    'tools/test_workspace_status.py':
        PR_GATED(
            "build-check.yml / gate-main / Run make build-check"
        ),
    'tools/test_workspace_status_cli.py':
        PR_GATED(
            "build-check.yml / gate-main / Run make build-check"
        ),
    'tools/test_worktree_hygiene.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_worktree_lease_interlock.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_worktree_import_resolution.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_editable_install_guard.py':
        NO_PR_GATE(
            "Exercises the editable install and child-process plumbing of a developer checkout, "
            "which a CI runner does not reproduce."
        ),
    'tools/test_gate_enumeration.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out "
            "destinations (RFC-0082)"
        ),
    'tools/test_import_time_path_leaks.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest import-time path leaks (collector sys.path "
            "guard)"
        ),
    'tools/test_managed_child.py':
        NO_PR_GATE(
            "Exercises the editable install and child-process plumbing of a developer checkout, "
            "which a CI runner does not reproduce."
        ),
    'tools/test_coordination_lease.py':
        PR_GATED_IF(
            "build-check-windows.yml / lock-semantics-windows / Run coordination lease publisher "
            "and prober",
            _WHY_PATH_FILTERED,
        ),
    'tools/test_branch_added_paths.py':
        NO_PR_GATE(
            "Runs under `make test` only; no pull-request workflow names it, so it reaches CI "
            "through the dispatch-only test-corpus.yml."
        ),
    'tools/test_bootstrap.py':
        NO_PR_GATE(
            "Exercises the editable install and child-process plumbing of a developer checkout, "
            "which a CI runner does not reproduce."
        ),
    'tools/test_run_slot.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_with_lease_cli.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_playwright_evidence_lifecycle.py':
        NO_PR_GATE(
            "Runs under `make test` only; no pull-request workflow names it, so it reaches CI "
            "through the dispatch-only test-corpus.yml."
        ),
    'tools/test_worktree_lifecycle_hooks.py':
        NO_PR_GATE(
            "Acquires or inspects a real coordination lease and worktree state, which a CI "
            "runner's fresh checkout cannot present. `make test` runs it under the lease it "
            "needs."
        ),
    'tools/test_frontend_runtime.py':
        NO_PR_GATE(
            "Runs under `make test` only; no pull-request workflow names it, so it reaches CI "
            "through the dispatch-only test-corpus.yml."
        ),
    'tools/test_check_artifact_contents.py':
        PR_GATED(
            "build-check.yml / gate-export-boundary / pytest export-boundary gate"
        ),
    'tools/test_lint_agents_md_diataxis_block.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_lint_agents_md_legacy_block.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_lint_agents_md_risk_block.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_lint_agents_md_frontmatter_scope.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_catalogue_curation_guard.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_contract_parity.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_marketplace_envelope_parity.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_guide_authoring_standard.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_guide_ledger_integrity.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_release_check.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_check_release_impact.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_scaffold_projection.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_conformance_portability.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_lint_direct_code_table.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_lint_guides_no_repo_only_refs.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_okf_pre_pr.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_pack_test_compatibility.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_check_distribution_route_decisions.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/test_route_branch_guard.py':
        PR_GATED(
            "build-check.yml / gate-main / pytest catalogue-test carve-out destinations "
            "(RFC-0082)"
        ),
    'tools/lint-pack-test-boundary.py':
        PR_GATED_IF(
            "docs.yml / loop-cohort / Pack runtime boundary (no pack's .apm/ carries tests; "
            "projection is clean)",
            _WHY_PATH_FILTERED,
        ),
    # The four lines that yield no path operand. Each is keyed by a literal
    # substring of the line, because there is no target to key on — and each is
    # dispositioned on its own terms rather than waved through as "not a suite".
    "command -v npm":
        NO_PR_GATE(
            "Shell guard, not a suite: `make test` stops here with an install "
            "hint when Node.js is absent."
        ),
    "test -d docs-site/node_modules":
        NO_PR_GATE(
            "Shell guard, not a suite: `make test` stops here with an `npm ci` "
            "hint when the docs-site dependencies are absent."
        ),
    "npm run test:plugins":
        NO_PR_GATE(
            "A real test suite — `node --test` over two `.test.ts` files, per "
            "docs-site/package.json — and the one that proves completeness "
            "cannot be keyed on extracted targets, since it yields no path "
            "operand. No pull-request workflow runs it; `make test` does."
        ),
    '$(PYTHON) -c "import httpx"':
        NO_PR_GATE(
            "Import precondition for the atlassian SSO suites, not a suite "
            "itself. build-check.yml installs httpx explicitly instead."
        ),
}

# The only keys a line may be resolved by *substring* match. Every other key is
# a path and matches a line only by being one of its extracted targets.
#
# This separation is load-bearing, and its absence was a false pass. With any key
# eligible for substring matching, the repo-root key `tests/` is a substring of
# almost every test path, so a line naming `packs/anything/tests/` resolved
# against it and demanded no entry of its own. A `# $(shell ... pytest
# packs/sneaky/tests/ ...)` comment -- a line GNU Make expands and runs -- passed
# the gate that way.
_SUBSTRING_KEYS = frozenset({
    "command -v npm",
    "test -d docs-site/node_modules",
    "npm run test:plugins",
    '$(PYTHON) -c "import httpx"',
})


def _strip_comment_lines(text: str) -> str:
    """Drop whole-line `#` comments.

    A comment *inside* a `_script_step(...)` call would otherwise stop the
    quoted-argument match at the `#`, silently dropping that step from the local
    set and producing a parity failure whose real cause is a comment.
    """
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _utf8_streams() -> None:
    """Windows cp1252 guard — UTF-8 streams before any glyph is printed.

    Called from `main`, not at import, so importing this module for its pure
    functions does not reconfigure the importer's streams.
    """
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def _strip_inline_comment(line: str) -> str:
    """Truncate *line* at the first unquoted `#`.

    Whole-line recipe comments were closed one round earlier; the inline form
    (`@true  # see also tools/lint-x.py`) was still scanned, which let a comment
    grant coverage for a gate deleted from the chain.
    """
    out, quote = [], None
    for ch in line:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            break
        out.append(ch)
    return "".join(out)


def _strip_shell_noise(line: str) -> str:
    """Drop quoting and shell punctuation so path tokens match cleanly."""
    return re.sub(r"[\"'()|&;><]", " ", line)


def _segments(line: str) -> list[str]:
    """Split a shell line into independently-runnable commands.

    Per-segment classification is what keeps `pip install x && python3
    tools/gate.py` from being written off wholesale as provisioning — the
    under-extraction direction, which is the dangerous one.
    """
    return [seg for seg in re.split(r"&&|\|\||[;|]", line) if seg.strip()]


def _is_provisioning(segment: str) -> bool:
    """True when *segment* installs tooling rather than running a gate."""
    cmd = segment.strip().lstrip("@-(").strip()
    if cmd.startswith("sudo "):  # `sudo apt-get …` provisions; `sudo python3 x.py` does not
        cmd = cmd[len("sudo "):].strip()
    return any(cmd == p or cmd.startswith(p + " ") for p in PROVISIONING)


def _cd_target(segment: str, subshell: bool) -> str | None:
    """The directory a leading `cd <dir>` moves to, and whether it persists.

    Returns the directory only when the `cd` genuinely affects later *lines*. A
    parenthesised `(cd x && …)` runs in a subshell, so it does not — treating it
    as persistent produced phantom targets like
    `packages/credbroker/tools/lint-new-gate.py`, and because `make test` covers
    `packages/credbroker/` by prefix, a brand-new gate on the following line
    reported *covered*. `build-check.yml` already uses that subshell idiom.

    `cd -`, `cd ~`, `cd $VAR` and absolute paths are not resolvable here, so they
    clear the working directory rather than composing a nonsense prefix.
    """
    if subshell:
        return None
    match = re.match(r"\s*\(?\s*cd\s+(\S+?)\s*\)?\s*$", segment)
    if not match:
        return None
    dest = match.group(1).replace("\\", "/").removeprefix("./")
    # Strip surrounding quotes BEFORE the guard. `cd "$dir"` is the same
    # unresolvable case as `cd $dir`, but the quoted token starts with `"`, so
    # the guard missed it and composed the phantom prefix `"$dir"/` — the very
    # failure mode this function's docstring warns about, reached by the form
    # a careful shell author is most likely to write.
    if len(dest) >= 2 and dest[0] == dest[-1] and dest[0] in "\"'":
        dest = dest[1:-1]
    if dest.startswith(("-", "~", "/", "$")) or ".." in dest.split("/") or not dest:
        return ""  # unresolvable — clear, never compose
    return dest


def _pytest_path_args(segment: str) -> list[str] | None:
    """Path arguments of a pytest invocation in *segment*, or None if not pytest.

    An empty list means "pytest with no path argument" — it collects from the
    working directory, so the caller substitutes that instead.

    Value-taking flags are skipped **along with their value**. Without that,
    `pytest tests/ --ignore packs/converters/` would enter the local coverage
    set as `packs/converters/`, marking an *excluded* tree covered and silently
    retiring every exemption beneath it. That is the fatal direction: the value
    of a flag is never a gate target.
    """
    match = _PYTEST_ARGS.search(segment)
    if not match:
        return None
    tokens = match.group(1).split()
    out: list[str] = []
    skip_next = False
    for tok in tokens:
        if skip_next:
            skip_next = False
            continue
        if tok.startswith("-"):
            skip_next = tok in _PYTEST_VALUE_FLAGS
            continue
        if "{" in tok or "$" in tok:  # unresolved make / shell variable
            continue
        if "/" not in tok and not tok.endswith((".py", ".sh")):
            continue  # a flag value that slipped through, not a path
        out.append(tok.replace("\\", "/").removeprefix("./"))
    return out


def suite_lines(makefile_text: str) -> list[str]:
    """Return executable `run-test-suite` lines as `test-unleased` expands them.

    This is deliberately lexical.  A line the target extractor cannot understand
    still needs a roster entry, because GNU Make can expand a function in a recipe
    comment before the shell sees that comment.
    """
    expanded: list[str] = []
    for names, _deps, recipe in iter_makefile_rules(makefile_text):
        if "test-unleased" not in names:
            continue
        for raw in recipe:
            expanded.extend(_expanded_recipe_lines(makefile_text, raw))
    lines: list[str] = []
    for line in _join_continuations(expanded):
        stripped = line.lstrip()
        # A recipe comment is dropped ONLY when it can carry no expansion at
        # all. GNU Make accepts `${...}` as readily as `$(...)`, and expands
        # either inside a recipe comment before the shell sees it, so a rule
        # keyed on `$(` alone still dropped `# ${shell ... pytest ...}` — the
        # same hatch through the other brace. Any `$` keeps the line.
        if not stripped or (stripped.startswith("#") and "$" not in stripped):
            continue
        if stripped.startswith("@"):
            stripped = stripped[1:]
        lines.append(stripped)
    return lines


# A pytest operand that is a variable expansion rather than a literal path.
# `$(PYTHON) -m pytest known/tests/ $(EXTRA_SUITE) -q` yields one target, and an
# all-targets rule keyed only on what extraction SEES then let the opaque operand
# ride free on its literate neighbour's entry.
_OPAQUE_OPERAND = re.compile(r"\$[({][^)}]*[)}]")
# A roster key that is a path rather than a command phrase. Used to keep a path
# entry out of the line-key remedy; see the dead-entry branch in `check_suites`.
_PATH_SHAPED = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*(?:/|\.py|\.sh)$")


def opaque_operands(line: str) -> list[str]:
    """Variable-expansion operands of a pytest invocation on *line*.

    The command position is excluded: every recipe line in the define is written
    `$(PYTHON) -m pytest …`, so the interpreter itself is an expansion and is not
    an operand. Only tokens *after* the `pytest` token count.
    """
    found: list[str] = []
    for segment in _segments(_strip_inline_comment(line)):
        # Deliberately NOT `_strip_shell_noise`: it replaces parentheses with
        # spaces, so `$(EXTRA_SUITE)` arrives as `$ EXTRA_SUITE` and the
        # expansion this function exists to find is already gone. The raw
        # segment is the only place it survives.
        match = _PYTEST_ARGS.search(segment)
        if match is None:
            continue
        skip_next = False
        for token in match.group(1).split():
            if skip_next:
                skip_next = False
                continue
            if token in _PYTEST_VALUE_FLAGS:
                skip_next = True
                continue
            if token.startswith("-"):
                continue
            # Strip balanced outer quotes, then search rather than fullmatch:
            # `"$(EXTRA)"`, `'${EXTRA}'` and `$(SUITE_DIR)/tests/` are all
            # expansions, and a fullmatch on the bare form caught only the last
            # of the three shapes an author is likely to write.
            bare = token
            for quote in ('"', "'"):
                if len(bare) > 1 and bare[0] == quote and bare[-1] == quote:
                    bare = bare[1:-1]
            if _OPAQUE_OPERAND.search(bare):
                found.append(bare)
    return found


def _matches_at_boundary(key: str, line: str) -> bool:
    """Whether *key* occurs in *line* as a complete command phrase.

    Raw containment let a key resolve a DIFFERENT command:
    `npm run test:plugins-extra` contains `npm run test:plugins`, so a newly
    added suite inherited an existing entry's disposition and demanded none of
    its own. The character after the match must therefore end the phrase.
    """
    for match in re.finditer(re.escape(key), line):
        tail = line[match.end():match.end() + 1]
        if tail == "" or tail in " \t\"'<>|&;)":
            return True
    return False


def line_targets(line: str) -> list[str]:
    """Propose path targets from one suite line for corroboration only."""
    found: list[str] = []
    for segment in _segments(_strip_inline_comment(line)):
        clean = _strip_shell_noise(segment)
        found.extend(
            m.group(0).replace("\\", "/").removeprefix("./")
            for m in _PATH_TOKEN.finditer(clean)
        )
        found.extend(_pytest_path_args(clean) or [])
    return list(dict.fromkeys(target for target in found if target))


def _prefixed(target: str, working_directory: str) -> str:
    wd = working_directory.strip().strip("/")
    tok = target.replace("\\", "/").removeprefix("./")
    combined = f"{wd}/{tok}" if wd else tok
    normalized = posixpath.normpath(combined)
    if tok.endswith("/") and normalized != ".":
        normalized += "/"
    return normalized


def extract_step_targets(run: str, working_directory: str = "") -> list[str]:
    """Gate targets a single `run:` body exercises. Pure — no filesystem.

    A plain `cd` is carried across lines — a `run: |` body is one shell script, so
    `cd packs/x/scripts` on one line governs the `pytest test_a.py` on the next.
    A *parenthesised* `(cd x && …)` is a subshell and applies to its own line
    only; treating it as persistent produced phantom prefixed paths that a
    directory-prefix match then covered, letting a brand-new gate report clean.
    """
    targets: list[str] = []
    wd = working_directory
    for raw in run.splitlines():
        line = _strip_inline_comment(raw)
        if not line.strip():
            continue
        subshell = line.lstrip().startswith("(")
        segment_wd = wd  # a subshell `cd` applies to its own line only
        for segment in _segments(line):
            moved_to = _cd_target(segment, subshell=False)
            if moved_to is not None:
                # A parenthesised group is a subshell: the `cd` dies with the
                # line, so it prefixes this line's targets and nothing after.
                if subshell:
                    segment_wd = moved_to
                else:
                    wd = segment_wd = moved_to
                continue
            if _is_provisioning(segment):
                continue
            clean = _strip_shell_noise(segment)
            pytest_args = _pytest_path_args(clean)
            path_tokens = [m.group(0) for m in _PATH_TOKEN.finditer(clean)]
            if pytest_args == [] and not path_tokens:
                # `pytest` with no path argument collects from the cwd, so the
                # working directory *is* the target. Only when the segment names
                # no path at all — never as a reason to skip the path scan, which
                # is how a `bash tools/run-pytest-suite.sh` gate went missing.
                if segment_wd:
                    targets.append(segment_wd.strip("/") + "/")
                continue
            for tok in path_tokens + (pytest_args or []):
                targets.append(_prefixed(tok, segment_wd))
    # Order-preserving dedupe: the failure message reads in workflow order.
    return list(dict.fromkeys(targets))


def _step_working_directory(job: dict, step: dict) -> str:
    """A step's working directory, falling back to the job's `defaults.run`."""
    if step.get("working-directory"):
        return str(step["working-directory"])
    defaults = job.get("defaults") or {}
    run_defaults = defaults.get("run") or {} if isinstance(defaults, dict) else {}
    return str(run_defaults.get("working-directory") or "")


def extract_ci_targets(workflow: dict, name: str = "build-check.yml") -> dict:
    """Classify every step of *workflow*.

    Returns ``{"steps": [names], "by_step": {name: [targets]},
    "where": {name: "<file> step '<name>'"},
    "duplicates": [names appearing more than once]}``.

    **`steps` is the roster, and it is the load-bearing output** — it lists every
    `run:`/`uses:` step regardless of whether anything could be extracted from it,
    which is what lets `check()` demand a disposition for each. `by_step` is the
    extractor's best effort and is used only to corroborate.

    A step carrying `uses:` instead of `run:` is on the roster like any other: a
    gate added as a composite or third-party action (`gitleaks-action`,
    `dependency-review-action`) is the normal Actions idiom, and skipping it would
    let one land undispositioned. Same for a job whose body is a
    reusable-workflow `uses:`.
    """
    steps: list[str] = []
    by_step: dict[str, list[str]] = {}
    where: dict[str, str] = {}
    for job_id, job in (workflow.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        if "uses" in job and not job.get("steps"):
            label = f"job {job_id} (reusable workflow)"
            steps.append(label)
            where.setdefault(label, f"{name} job {job_id!r}")
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            if "run" not in step and "uses" not in step:
                continue
            label = str(step.get("name") or f"<unnamed step in {job_id}>")
            steps.append(label)
            where.setdefault(label, f"{name} step {label!r}")
            if "run" not in step:
                continue  # `uses:` step — on the roster, nothing to extract
            found = extract_step_targets(str(step["run"]), _step_working_directory(job, step))
            if found:
                by_step.setdefault(label, []).extend(found)
    duplicates = sorted({s for s in steps if steps.count(s) > 1})
    return {
        "steps": list(dict.fromkeys(steps)),
        "by_step": by_step,
        "where": where,
        "duplicates": duplicates,
    }


# make flags whose next token is a value, so `$(MAKE) -C sub other` names `other`
# and not `sub` — reading `-C`'s value as the target both loses the real one and
# pulls a directory name into the reachable set.
_MAKE_VALUE_FLAGS = frozenset({"-C", "--directory", "-f", "--file", "-j", "--jobs",
                               "-l", "--load-average", "-o", "--old-file",
                               "-W", "--what-if"})


def _sub_make_targets(args: str) -> list[str]:
    """Target names in a `$(MAKE) <args>` invocation. Pure — no filesystem."""
    out: list[str] = []
    skip_next = False
    for tok in args.split():
        if skip_next:
            skip_next = False
            continue
        if tok.startswith("-"):
            skip_next = tok in _MAKE_VALUE_FLAGS
            continue
        if "=" in tok or tok.startswith("$"):
            continue  # a variable override, not a target
        out.append(tok)
    return out


def iter_makefile_rules(text: str):
    """Yield ``(targets, prerequisites, recipe_lines)`` for each Makefile rule.

    One parser, two consumers (`derive_reachable_targets` and
    `makefile_recipe_targets`) — written twice, the two would have to agree about
    where a rule begins and ends, and a disagreement is silent by construction.

    Three shapes matter, and every one of them fails *closed* if mishandled here:

    * **Recipe comments are not commands.** A tab-indented `#` line is dropped.
      Without this, `\\t# TODO: re-enable pytest packs/` puts `packs/` into the
      coverage set, and because coverage is prefix-based that one comment marks
      every `packs/**` gate covered — the permanently-green outcome this module
      exists to prevent. `\\t# historically: $(MAKE) zipapp` likewise pulled an
      unreachable target in.
    * **Backslash continuations** join, so `ci: build-check \\` + `\\ttest` does
      not file `test` as a recipe line of `ci` and lose everything it covers.
    * **Multi-target rules** (`a b:`) yield both names, so their recipe is not
      dropped entirely.

    Conditional directives (`ifeq`/`else`/`endif`) do not end a rule. Recipe lines
    *inside* a conditional are still yielded; which branch make would take is not
    modelled, so a conditional recipe over-contributes rather than vanishing.
    """
    rule_head = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\- ]*?)\s*::?(?!=)(.*)$")
    directive = re.compile(r"^\s*(?:ifeq|ifneq|ifdef|ifndef|else|endif)\b")
    lines, joined = text.splitlines(), []
    i = 0
    while i < len(lines):
        line = lines[i]
        while line.endswith("\\") and i + 1 < len(lines):
            i += 1
            line = line[:-1].rstrip() + " " + lines[i].lstrip()
        joined.append(line)
        i += 1

    targets: list[str] = []
    prereqs: list[str] = []
    recipe: list[str] = []
    for line in joined:
        if line.startswith("\t"):
            if targets and not line.lstrip("\t").lstrip().startswith("#"):
                recipe.append(line)
            continue
        if directive.match(line):
            continue  # a conditional does not end the rule
        head = line.split("#", 1)[0]
        match = rule_head.match(head)
        if not match:
            if targets:
                yield targets, prereqs, recipe
            targets, prereqs, recipe = [], [], []
            continue
        if targets:
            yield targets, prereqs, recipe
        targets = match.group(1).split()
        prereqs = [tok for tok in match.group(2).split() if not tok.startswith("$")]
        recipe = []
    if targets:
        yield targets, prereqs, recipe


def derive_reachable_targets(text: str, entrypoint: str = CI_ENTRYPOINT) -> set[str]:
    """Makefile targets reachable from *entrypoint*, derived — never declared.

    Walks the prerequisite graph transitively and follows `$(MAKE) <target>`
    invocations found inside reachable recipes (which is how `build-check`
    reaches `sast`). Deriving it is the point: a hand-written list is the one
    table that could be widened to make a parity failure disappear, and no
    staleness check can catch that.
    """
    prereqs: dict[str, list[str]] = {}
    recipes: dict[str, list[str]] = {}
    for names, deps, recipe in iter_makefile_rules(text):
        for name in names:
            prereqs.setdefault(name, []).extend(deps)
            recipes.setdefault(name, []).extend(recipe)
    reachable: set[str] = set()
    frontier = [entrypoint]
    while frontier:
        target = frontier.pop()
        if target in reachable:
            continue
        reachable.add(target)
        if target not in prereqs:
            continue  # a prerequisite naming a file, not a rule
        frontier.extend(prereqs[target])
        for line in recipes.get(target, []):
            for call in re.finditer(r"\$\(MAKE\)\s+([^;&|]*)", line):
                # Split on shell separators: the live Makefile writes
                # `if …; then $(MAKE) sast; else …; fi` on one continued line, and
                # a greedy tail swallowed `; fi` into the target list, yielding
                # `sast;` and `fi` instead of `sast`.
                frontier.extend(_sub_make_targets(call.group(1)))
    return reachable


def _expanded_recipe_lines(text: str, recipe_line: str) -> list[str]:
    """Expand one literal ``$(call <macro>,...)`` recipe for path discovery.

    Local CI's full and composed test targets call the same lexical Make macro.
    Treating that invocation as opaque made every command inside the composed
    route disappear from parity reachability. This intentionally supports only
    a whole-line call with comma-free literal arguments; an unsupported shape
    remains opaque and therefore fails closed at the disposition check.
    """
    match = re.fullmatch(
        r"\s*\$\(call\s+([A-Za-z0-9_.-]+),(.*)\)\s*",
        recipe_line,
    )
    if match is None:
        return [recipe_line]
    name, raw_args = match.groups()
    macro = re.search(
        rf"(?ms)^(?:override )?define {re.escape(name)}\n(.*?)^endef$",
        text,
    )
    if macro is None:
        return [recipe_line]
    args = raw_args.split(",")
    expanded = macro.group(1)
    for index, value in enumerate(args, start=1):
        expanded = expanded.replace(f"$({index})", value)
    if re.search(r"\$\([1-9]\)", expanded):
        return [recipe_line]
    return _join_continuations(expanded.splitlines())


def _join_continuations(lines: list[str]) -> list[str]:
    """Fold backslash continuations so one command is one line.

    A grouped pytest invocation spans several physical lines and only the first
    carries the `pytest` token, so splitting physically hides every path operand
    from the reachability match — the step reads as "not reachable from make ci"
    while it in fact runs. `_iter_rules` already folds for the same reason; this
    is the macro-body path it does not cover.
    """
    out: list[str] = []
    pending: list[str] = []
    for raw in lines:
        if raw.endswith("\\"):
            pending.append(raw[:-1].rstrip())
            continue
        pending.append(raw)
        out.append(" ".join(part.strip() for part in pending) if len(pending) > 1 else pending[0])
        pending = []
    if pending:
        out.append(" ".join(part.strip() for part in pending) if len(pending) > 1 else pending[0])
    return out


def makefile_recipe_targets(text: str, reachable: set[str]) -> set[str]:
    """Invocation targets in the recipes of *reachable* Makefile targets only.

    Recipe lines outside those targets, every variable assignment, and every
    recipe comment are ignored — see `iter_makefile_rules` for why each of those
    exclusions is load-bearing.
    """
    found: set[str] = set()
    for names, _deps, recipe in iter_makefile_rules(text):
        if not any(name in reachable for name in names):
            continue
        for raw in recipe:
            for expanded in _expanded_recipe_lines(text, raw):
                for segment in _segments(_strip_inline_comment(expanded)):
                    clean = _strip_shell_noise(segment)
                    path_scan = re.sub(r"(?:^|\s)--ignore=[^\s]+", " ", clean)
                    found.update(
                        m.group(0).replace("\\", "/").removeprefix("./")
                        for m in _PATH_TOKEN.finditer(path_scan)
                    )
                    found.update(_pytest_path_args(clean) or [])
    return {t for t in found if t}


def script_step_targets(text: str) -> set[str]:
    """Paths named by gate-chain step calls.

    Covers both `_script_step("label", *parts)`, whose parts join into a
    repo-relative path, and `_pytest_step_cwd("label", "<dir>", *targets)`,
    whose targets are bare filenames resolved against the directory — those are
    joined here so the reachability scan sees the same repo-relative path the CI
    step names.
    """
    stripped = _strip_comment_lines(text)
    found = set()
    for call in _SCRIPT_STEP.finditer(stripped):
        parts = _QUOTED.findall(call.group(1))
        if len(parts) > 1:  # parts[0] is the human label
            found.add("/".join(parts[1:]))
    for call in _PYTEST_STEP_CWD.finditer(stripped):
        parts = _QUOTED.findall(call.group(1))
        if len(parts) > 2:  # label, cwd, then one or more targets
            cwd = parts[1].rstrip("/")
            for target in parts[2:]:
                found.add(f"{cwd}/{target}")
    return found


def run_call_targets(text: str) -> set[str]:
    """Paths named in `_run(...)` argv in the pre-PR aggregators.

    Scoped to `_run(...)` rather than the whole file so prose and docstrings —
    which name plenty of scripts nothing runs — cannot become coverage. Comments
    are stripped for the same reason: `tools/hooks/pre-pr.py` ships *commented*
    `_run(...)` examples by design as the adopter wiring stub, and an example
    edited to name a real script would otherwise become coverage for a script
    nothing runs.
    """
    found = set()
    for call in _RUN_CALL.finditer(_strip_comment_lines(text)):
        for tok in _QUOTED.findall(call.group(1)):
            if _PATH_TOKEN.fullmatch(tok):
                found.add(tok.replace("\\", "/").removeprefix("./"))
    return found


def local_targets(root: Path, chain_text: str | None = None) -> set[str]:
    """Everything `make ci` reaches, read from invocation positions only.

    **Every source is itself gated on reachability.** The Makefile half comes from
    `derive_reachable_targets`, and each *indirect* source — the gate chain, the
    two pre-PR aggregators — contributes only when `make ci` actually invokes it,
    i.e. when its own path is in the Makefile-derived set. Unioning them
    unconditionally meant dropping `build-check` from `ci:` (which removes
    `catalogue verify`, the whole gate chain including this linter, and the SAST
    leg) left the coverage set byte-identical, so the gate did not notice. That
    also made the "dropped prerequisite collapses coverage" property true only of
    the prerequisites whose coverage happens to come from a recipe line.

    *chain_text* overrides the gate chain's source, which is how the self-test
    proves the wiring is load-bearing by A/B rather than by restating this
    composition.
    """
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    local = makefile_recipe_targets(makefile, derive_reachable_targets(makefile))
    if GATE_CHAIN in local:
        if chain_text is None:
            chain_text = (root / GATE_CHAIN).read_text(encoding="utf-8")
        local |= script_step_targets(chain_text)
    for rel in AGGREGATORS:
        if rel in local:
            local |= run_call_targets((root / rel).read_text(encoding="utf-8"))
    return local


def is_covered(target: str, local: set[str]) -> bool:
    """True when *local* names *target* outright or a directory containing it."""
    if target in local:
        return True
    return any(entry.endswith("/") and target.startswith(entry) for entry in local)


# `for d in <literal paths>; do … pytest "$d" …; done`. One workflow runs 24 pack
# suites this way, and the operand pytest receives is `"$d"`, so a scan for
# literal operands sees none of them. That is not hypothetical laxity: the roster
# was first authored FROM this extractor, so all 24 inherited its blind spot and
# 21 shipped a `NO_PR_GATE` reason asserting that no workflow named them, while
# `catalogue-tooling-ci-gates.yml` named every one.
#
# The shape is read deliberately narrowly. The loop's list must be literal, and
# the body must invoke pytest on that same variable — otherwise a loop over
# package names, or one whose body only echoes, would contribute phantom
# coverage. Coverage is the direction where a false positive is consequential, so
# this reads one shape exactly rather than guessing at shell semantics.


# Steps whose pytest invocation no static scan can attribute, with the literal
# suites each one runs. A DECLARATION, not a parse.
#
# `catalogue-tooling-ci-gates.yml` runs 24 pack suites as
# `for d in <paths>; do python -m pytest "$d" -q; done`, so the operand pytest
# receives is `"$d"` and no scan of the step sees a suite. Ignoring that cost 21
# entries a `NO_PR_GATE` reason asserting no workflow named them, while that
# workflow ran every one.
#
# A reader for the loop shape was built and then removed. It produced seven
# defects across three review rounds, two of them PHANTOM COVERAGE — `true` then
# `echo "python -m pytest $d"` reported the suites as gated, and a leading `#`
# comment deleted the rest of the body so a real invocation went unseen. Both
# came from one mistake: `_segments` and `_strip_inline_comment` are documented
# single-*line* helpers, applied to a multi-line shell body. This module's own
# docstring records that making extraction the trust anchor was defeated four
# ways and that a fix in one round caused the next round's defect; the loop
# reader was that class again, and phantom coverage is the direction that
# silently validates a false `PR_GATED_IF`.
#
# So the roster stays the anchor here too. `tools/lint-pack-test-boundary.py`
# carries `_UNRESOLVABLE_RUNNER_EXCEPTIONS` keyed the same way for this same
# loop, which is the precedent this follows. The residual is stated rather than
# parsed: these suites' coverage rests on a hand declaration, and the docstring
# says so. What IS checked: the named step's name is unique in its workflow,
# every listed path appears in that step's own `run`, and both that body and this
# declared tuple are digest-pinned, so any edit to either reddens a test and
# sends a human back to re-check. What is NOT checked is whether the step
# actually executes the listed suites — only that the workflow text still says
# what it said when a human last looked. That residual is the honest cost of the
# trade, and strictly smaller than a parser that invents coverage.
_SUITE_SOURCE_EXCEPTIONS: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    (
        "catalogue-tooling-ci-gates.yml",
        "Run repo/pack hook suites (Linux)",
    ): (
        "a bash for-loop runs one literal suite per process, so the operand "
        "pytest receives is `\"$d\"` and no static scan can attribute it",
        (
            "packs/core/tests/hooks/",
            "packs/core/tests/pack/",
            "packs/core/tests/skills/adapt-to-project/",
            "packs/core/tests/skills/bug-fix/",
            "packs/core/tests/skills/capture-work/",
            "packs/core/tests/skills/close-work/",
            "packs/core/tests/skills/project-knowledge/",
            "packs/core/tests/skills/receive-brief/",
            "packs/core/tests/skills/work-intake/",
            "packs/core/tests/skills/work-loop/",
            "packs/core/tests/skills/workspace-status/",
            "packs/product-documentation/tests/",
            "packs/desk-research/tests/pack/",
            "packs/desk-research/tests/skills/desk-research/",
            "packs/desk-research/tests/skills/desk-research-project-start/",
            "packs/desk-research/tests/skills/desk-research-project-check/",
            "packs/desk-research/tests/skills/desk-research-project-digest/",
            "packs/desk-research/tests/skills/desk-research-project-status/",
            "packs/desk-research/tests/skills/desk-research-project-synthesize/",
            "packs/desk-research/tests/skills/devils-advocate/",
            "packs/agent-skill-engineering/tests/pack/",
            "packs/agent-skill-engineering/tests/integration/",
            "packs/agent-skill-engineering/tests/skills/author_or_update/",
            "packs/agent-skill-engineering/tests/skills/review_or_optimize/",
        ),
    ),
}


def pr_gate_sources(root: Path) -> dict[str, list[dict[str, str | bool]]]:
    """Map recognised suite targets to their pull-request workflow sources."""
    import yaml

    sources: dict[str, list[dict[str, str | bool]]] = {}
    workflow_dir = root / WORKFLOW_DIR
    chain_targets: set[str] | None = None
    for path in sorted(workflow_dir.glob("*.y*ml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        triggers = doc.get("on", doc.get(True))
        if not isinstance(triggers, dict) or "pull_request" not in triggers:
            continue
        trigger = triggers["pull_request"]
        filtered = isinstance(trigger, dict) and (
            "paths" in trigger or "paths-ignore" in trigger
        )
        jobs = doc.get("jobs") or {}
        job_defaults = (doc.get("defaults") or {}).get("run") or {}
        step_names = [
            str(step.get("name") or "<unnamed step>")
            for job in jobs.values()
            if isinstance(job, dict)
            for step in (job.get("steps") or [])
            if isinstance(step, dict)
        ]
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            # PRESENCE, not truth. `if: false` loads as Python False, so a
            # truthiness test read a step that never runs as unconditional and
            # let it corroborate a PR_GATED claim. Any `if` at all makes the
            # coverage conditional; that is what the disposition has to say.
            job_conditional = "if" in job or bool(job.get("continue-on-error"))
            job_wd = (
                (job.get("defaults") or {}).get("run") or job_defaults
            ).get("working-directory", "") or ""
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                step_name = str(step.get("name") or "<unnamed step>")
                where = f"{path.name} / {job_name} / {step_name}"
                conditional = job_conditional or "if" in step or bool(
                    step.get("continue-on-error")
                )
                run = str(step.get("run") or "")
                # Attributed per STEP, not per step NAME. `extract_ci_targets`
                # groups by name, and two steps sharing one name then share the
                # merged target list — so an unconditional step that runs
                # nothing could lend its standing to a conditional step's suite.
                working_directory = str(
                    step.get("working-directory", job_wd) or ""
                )
                # Keyed on a step NAME, so it applies only when that name is
                # unique in the workflow. A duplicate would otherwise receive
                # all the declared targets even if it runs none, and attach its
                # own `if:` state to that phantom coverage — the cross-crediting
                # this module already fixed once, returning through the
                # declaration instead of through `extract_ci_targets`.
                declared = (
                    _SUITE_SOURCE_EXCEPTIONS.get((path.name, step_name))
                    if step_names.count(step_name) == 1
                    else None
                )
                targets = [
                    *extract_step_targets(run, working_directory),
                    *(declared[1] if declared else ()),
                ]
                if re.search(r"(?:^|\s)make\s+build-check(?:\s|$)", run):
                    if chain_targets is None:
                        chain_targets = script_step_targets(
                            (root / GATE_CHAIN).read_text(encoding="utf-8")
                        )
                    targets = list(dict.fromkeys([*targets, *chain_targets]))
                for target in targets:
                    sources.setdefault(target, []).append(
                        {
                            "workflow": path.name,
                            "where": where,
                            "filtered": filtered,
                            "conditional": conditional,
                        }
                    )
    return sources


def check_suites(
    root: Path,
    *,
    makefile_text: str | None = None,
    dispositions: dict[str, tuple[str, ...]] | None = None,
    sources: dict[str, list[dict[str, str | bool]]] | None = None,
) -> list[str]:
    """Check suite-roster completeness and pull-request coverage claims."""
    dispositions = SUITE_DISPOSITION if dispositions is None else dispositions
    if makefile_text is None:
        makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    sources = pr_gate_sources(root) if sources is None else sources
    lines = suite_lines(makefile_text)
    line_entries: dict[str, set[str]] = {}
    violations: list[str] = []
    for line in lines:
        targets = line_targets(line)
        # Computed once, boundary-matched, and used for BOTH the opaque-operand
        # remedy and `resolved`. Two separate reads were self-contradictory: the
        # opaque branch tested raw containment, so a key merely mentioned on the
        # line suppressed the violation, while a key legitimately declared for a
        # mixed literal/opaque line never entered `resolved` and was then
        # reported dead — making AC-0002's required remedy impossible to satisfy.
        substring_keys = {
            key
            for key in _SUBSTRING_KEYS & set(dispositions)
            if _matches_at_boundary(key, line)
        }
        if targets:
            # EVERY target must carry an entry, not merely one of them. "At
            # least one" is the weaker rule and it reopens the gap this roster
            # exists to close: `run-test-suite` batches up to nineteen modules
            # onto a single continued line, so a twentieth added beside them
            # would inherit its siblings' dispositions and demand none of its
            # own -- a new suite landing PR-ungated in silence, which is the
            # original defect one layer down.
            resolved = (set(targets) & set(dispositions)) | substring_keys
            missing = [target for target in targets if target not in dispositions]
            # An opaque operand is a suite the roster cannot name, so the line
            # needs a declared substring key of its own. Without this, a known
            # target beside `$(EXTRA_SUITE)` satisfied the line and the opaque
            # one demanded nothing — the escape the recipe-line anchor exists to
            # prevent, reopened by keying the check on extracted targets.
            opaque = opaque_operands(line)
            if opaque and not substring_keys:
                violations.append(
                    f"suite line {line!r} passes "
                    f"{', '.join(sorted(opaque))} to pytest, which names no "
                    "literal path. Add a literal-substring key for this line, "
                    "to the roster AND to `_SUBSTRING_KEYS`: an operand the "
                    "roster cannot resolve is a suite it cannot disposition."
                )
            if missing:
                violations.append(
                    f"suite line {line!r} runs "
                    f"{', '.join(sorted(missing))} with no SUITE_DISPOSITION "
                    "entry. Add one per target naming the pull-request check "
                    "that gates it, or NO_PR_GATE with the reason none does."
                )
        else:
            resolved = substring_keys
            if not resolved:
                violations.append(
                    f"suite line {line!r} has no SUITE_DISPOSITION entry and no "
                    "path operand to key one on. Add a literal-substring key "
                    "for it, to the roster AND to `_SUBSTRING_KEYS`; a line the "
                    "extractor cannot read still runs."
                )
        line_entries[line] = resolved
    resolved_entries = set().union(*line_entries.values()) if line_entries else set()
    for entry in sorted(set(dispositions) - resolved_entries):
        # An entry that MATCHES a line but is not declared a substring key is a
        # half-finished remedy, not a dead entry, and saying "dead" sent the
        # author to delete the entry they had just been told to add. Adding a
        # line key takes two edits — the roster and `_SUBSTRING_KEYS` — because
        # a path key must stay ineligible for substring matching: the repo-root
        # key `tests/` boundary-matches almost every test line.
        # Only a LINE-KEY candidate may be told to enter `_SUBSTRING_KEYS`. A
        # path-shaped entry must not: `tests/` boundary-matches almost every
        # test line, so diagnosing an unresolved path as a half-declared line
        # key would recommend exactly the edit that makes a path key
        # substring-eligible — the broad false pass the hand declaration exists
        # to prevent. A path entry keeps the dead-entry remedy.
        if (
            entry not in _SUBSTRING_KEYS
            and not _PATH_SHAPED.match(entry)
            and any(_matches_at_boundary(entry, line) for line in lines)
        ):
            violations.append(
                f"suite {entry!r} — matches a run-test-suite line but is not "
                "declared a substring key, so nothing resolves it. Add it to "
                "`_SUBSTRING_KEYS` as well; a line key takes both edits."
            )
            continue
        violations.append(
            f"suite {entry!r} — dead SUITE_DISPOSITION entry: no run-test-suite "
            "line resolves it. Remove it or add the suite to the define."
        )
    for suite, entry in sorted(dispositions.items()):
        kind, value, *extra = entry
        condition = extra[0] if extra else ""
        suite_sources = sources.get(suite, [])
        named = [source for source in suite_sources if source["where"] == value]
        if kind == "pr-gated":
            # One defect, one message. The specific diagnoses below and the
            # generic one are the same failure seen at different resolutions, so
            # emitting both makes an author read two lines to learn one thing —
            # and made a self-test case that asserts a single violation fail for
            # the wrong reason.
            if any(
                not source["filtered"] and not source["conditional"]
                for source in named
            ):
                pass  # corroborated
            elif any(source["filtered"] for source in named):
                violations.append(
                    f"suite {suite!r} — PR_GATED names filtered source {value!r}. "
                    "Use PR_GATED_IF with its path condition."
                )
            elif any(source["conditional"] for source in named):
                violations.append(
                    f"suite {suite!r} — PR_GATED names conditional source {value!r}. "
                    "Use PR_GATED_IF with the step or job condition."
                )
            else:
                violations.append(
                    f"suite {suite!r} — PR_GATED source {value!r} does not reach it "
                    "through a required pull-request check. Correct the source "
                    "or re-disposition it."
                )
        elif kind == "no-pr-gate":
            # ANY pull-request workflow that names the suite contradicts this,
            # not only an unconditional one. Ignoring conditional sources let 21
            # entries ship a reason asserting that no workflow named them while
            # a path-filtered workflow ran every one — `NO_PR_GATE` has to mean
            # "no pull-request check reaches this at all", because
            # `PR_GATED_IF` is what the conditional case is for.
            unconditional = next(
                (
                    source
                    for source in suite_sources
                    if not source["filtered"] and not source["conditional"]
                ),
                None,
            )
            if unconditional:
                violations.append(
                    f"suite {suite!r} — NO_PR_GATE is contradicted by covering step "
                    f"{unconditional['where']!r}. Change it to PR_GATED."
                )
            elif suite_sources:
                conditional_source = suite_sources[0]
                violations.append(
                    f"suite {suite!r} — NO_PR_GATE is contradicted by "
                    f"{conditional_source['where']!r}, which reaches it "
                    "conditionally. Change it to PR_GATED_IF stating the "
                    "condition."
                )
            if not value.strip():
                violations.append(
                    f"suite {suite!r} — NO_PR_GATE has an empty reason; state the "
                    "route that runs it or the missing precondition."
                )
        elif kind == "pr-gated-if":
            # Corroborated like PR_GATED, but inverted: the named source must
            # exist AND must actually be conditional. Without this the claim was
            # unverifiable, so a conditional entry could name a workflow or step
            # that does not exist.
            if not named:
                violations.append(
                    f"suite {suite!r} — PR_GATED_IF source {value!r} names no "
                    "step of any pull-request workflow. Correct the source or "
                    "re-disposition it."
                )
            elif not any(
                source["filtered"] or source["conditional"] for source in named
            ):
                violations.append(
                    f"suite {suite!r} — PR_GATED_IF names {value!r}, which is "
                    "unfiltered and unconditional, so the coverage is not in "
                    "fact conditional. Use PR_GATED."
                )
            if not condition.strip():
                violations.append(
                    f"suite {suite!r} — PR_GATED_IF has an empty condition; "
                    "state what makes the coverage conditional."
                )
        else:
            violations.append(f"suite {suite!r} — unknown disposition kind {kind!r}.")
    return violations


def check(
    classified: dict,
    local: set[str],
    reachable: set[str],
    workflow_files: set[str],
    *,
    dispositions: dict[str, tuple[str, str]] | None = None,
    scope: dict[str, str | None] | None = None,
) -> list[str]:
    """Every violation, in a stable order.

    Two layers, in this order of trust:

    **1. The roster (complete, extraction-independent).** Every step of an
    in-scope workflow must carry a disposition and every disposition must name a
    real step. A `LOCAL` disposition must name a make target `make ci` actually
    reaches; a `CI_ONLY` one must state a reason. Nothing here reads a shell
    command, so no shell shape can defeat it — this is what guarantees a new gate
    cannot land in silence.

    **2. Corroboration (extraction, best-effort).** For a step declared `LOCAL`,
    every gate target the extractor *does* see must be locally covered. Because
    the roster already carries completeness, an extractor bug here can only raise
    a false alarm — never grant a false pass. That inversion is the point: for
    four review rounds the extractor's misses were silent, and now they are loud.

    The tables are keyword parameters defaulting to the module globals, so each
    self-test case passes its own without mutating shared state.
    """
    dispositions = STEP_DISPOSITION if dispositions is None else dispositions
    scope = WORKFLOW_SCOPE if scope is None else scope

    steps = classified["steps"]           # every run:/uses: step name, in order
    by_step = classified["by_step"]       # step name -> extracted targets
    where = classified["where"]           # step name -> "<workflow> step '<name>'"

    v = [
        f"step {step!r} ({where.get(step, 'in-scope workflow')}) has no entry in "
        "STEP_DISPOSITION. Add LOCAL(\"<make target>\") naming the target that "
        "covers it, or CI_ONLY(\"<reason>\") saying why no local gate can."
        for step in steps
        if step not in dispositions
    ]
    v += [
        f"step {step!r} — dead STEP_DISPOSITION entry: no in-scope workflow has a "
        "step by that name. Remove it."
        for step in sorted(dispositions)
        if step not in steps
    ]
    for step in sorted(set(dispositions) & set(steps)):
        kind, value = dispositions[step]
        if kind == "local":
            if value not in reachable:
                v.append(
                    f"step {step!r} — declared LOCAL({value!r}), but `make "
                    f"{value}` is not reachable from `make {CI_ENTRYPOINT}`. "
                    "Either wire it into the chain or re-disposition the step."
                )
                continue
            uncovered = [t for t in by_step.get(step, []) if not is_covered(t, local)]
            if uncovered:
                v.append(
                    f"step {step!r} — declared LOCAL({value!r}), but "
                    f"{', '.join(sorted(uncovered))} is not reachable from "
                    "`make ci`. Either the disposition is wrong, or the gate was "
                    "never wired locally."
                )
        elif not value.strip():
            v.append(
                f"step {step!r} — CI_ONLY with an empty reason; state why no local "
                "gate can run it."
            )
        elif kind != "ci-only":
            v.append(f"step {step!r} — unknown disposition kind {kind!r}.")
    v += [
        f"step {step!r} — appears more than once in an in-scope workflow, so one "
        "disposition would silence both. Give each step a distinct name."
        for step in classified["duplicates"]
    ]
    v += [
        f"{name} — WORKFLOW_SCOPE marks this out of scope with an empty reason; "
        "state why nothing gates it locally."
        for name, reason in sorted(scope.items())
        if reason is not IN_SCOPE and not str(reason).strip()
    ]
    v += [
        f"{name} — workflow file not classified in WORKFLOW_SCOPE. Add it as "
        "in-scope, or out-of-scope with the reason nothing gates it locally."
        for name in sorted(workflow_files - set(scope))
    ]
    if COMPOSITE_ACTION_DIR in workflow_files and COMPOSITE_ACTION_DIR not in scope:
        # A composite action's own `run:` steps are never read — only the
        # workflow step that calls it, which the roster does disposition. Later
        # edits inside action.yml add gates with no signal, so force the decision
        # the moment the directory appears.
        v.append(
            ".github/actions/ exists — a composite action's own `run:` steps are "
            "never read by this linter, only the workflow step that calls it. Add "
            f"a {COMPOSITE_ACTION_DIR!r} entry to WORKFLOW_SCOPE stating how those "
            "steps are covered (that acknowledgement clears this), or teach the "
            "linter to read action.yml."
        )
    v += [
        f"{name} — WORKFLOW_SCOPE names a workflow that no longer exists. "
        "Remove it."
        for name in sorted(set(scope) - workflow_files)
    ]
    return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CI-parity gate for build-check.yml.")
    ap.add_argument("--root", default=".", help="repo root (default: .)")
    args = ap.parse_args(argv)
    _utf8_streams()
    root = Path(args.root).resolve()

    try:
        import yaml
    except ImportError:
        print(
            "lint-ci-parity: PyYAML not installed — run: "
            "pip install -r tools/requirements.txt",
            file=sys.stderr,
        )
        return 2

    wf_dir = root / WORKFLOW_DIR
    if not wf_dir.is_dir():
        print(f"lint-ci-parity: {WORKFLOW_DIR} not found under {root}", file=sys.stderr)
        return 2
    workflow_files = {p.name for p in wf_dir.iterdir() if p.suffix in (".yml", ".yaml")}
    if (root / ".github" / "actions").is_dir():
        workflow_files.add(COMPOSITE_ACTION_DIR)

    in_scope = [name for name, reason in WORKFLOW_SCOPE.items() if reason is IN_SCOPE]
    classified: dict = {"steps": [], "by_step": {}, "where": {}, "duplicates": []}
    for name in in_scope:
        if name not in workflow_files:
            # Let `check()` raise the staleness violation the table exists for,
            # rather than exiting 2 with a tool error.
            continue
        try:
            doc = yaml.safe_load((wf_dir / name).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            print(f"lint-ci-parity: cannot read {name}: {exc}", file=sys.stderr)
            return 2
        if not isinstance(doc, dict):
            print(f"lint-ci-parity: {name} is not a mapping", file=sys.stderr)
            return 2
        one = extract_ci_targets(doc, name)
        classified["steps"] += one["steps"]
        for step, targets in one["by_step"].items():
            classified["by_step"].setdefault(step, []).extend(targets)
        classified["where"].update(one["where"])
        classified["duplicates"] += one["duplicates"]
    # Duplicates are computed over the MERGED roster, not per workflow: once a
    # second workflow enters scope, two same-named steps in different files would
    # collapse and one disposition would silence both.
    merged = classified["steps"]
    classified["duplicates"] = sorted(
        set(classified["duplicates"]) | {s for s in merged if merged.count(s) > 1}
    )
    classified["steps"] = list(dict.fromkeys(merged))

    try:
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        reachable = derive_reachable_targets(makefile)
        local = local_targets(root)
    except OSError as exc:
        print(f"lint-ci-parity: cannot read a local gate source: {exc}", file=sys.stderr)
        return 2

    violations = check(classified, local, reachable, workflow_files)
    try:
        violations += check_suites(root, makefile_text=makefile)
    except (OSError, yaml.YAMLError) as exc:
        print(f"lint-ci-parity: cannot read a pull-request gate source: {exc}", file=sys.stderr)
        return 2
    if violations:
        for item in violations:
            print(f"lint-ci-parity: ✖ {item}", file=sys.stderr)
        print(
            f"lint-ci-parity: {len(violations)} parity violation(s).",
            file=sys.stderr,
        )
        return 1
    ci_only = sum(1 for k, _ in STEP_DISPOSITION.values() if k == "ci-only")
    # Both rosters report their own counts, so a green run says which checks
    # actually ran. A silently deleted arm would otherwise leave this line
    # unchanged, which is the shape that makes a dead gate look like a passing
    # one.
    kinds = [entry[0] for entry in SUITE_DISPOSITION.values()]
    gated = kinds.count("pr-gated")
    gated_if = kinds.count("pr-gated-if")
    ungated = kinds.count("no-pr-gate")
    print(
        f"lint-ci-parity: ok — {len(classified['steps'])} step(s) across "
        f"{len(in_scope)} in-scope workflow(s), all dispositioned "
        f"({len(STEP_DISPOSITION) - ci_only} locally covered, {ci_only} CI-only); "
        f"{sum(len(v) for v in classified['by_step'].values())} extracted target(s) "
        "corroborated."
    )
    # Three distinct counts, because they are three distinct things and
    # reporting one as another is a claim about what ran. `SUITE_DISPOSITION`
    # holds a key per target PLUS a key per line with no path operand, so it is
    # larger than either the line count or the target count.
    suite_line_count = len(suite_lines(makefile))
    target_count = len({
        target for line in suite_lines(makefile)
        for target in (line_targets(line) or [])
    })
    print(
        f"lint-ci-parity: ok — {suite_line_count} recipe line(s) of "
        f"`run-test-suite` carrying {target_count} target(s), all "
        f"dispositioned across {len(SUITE_DISPOSITION)} roster key(s) "
        f"({gated} PR-gated, {gated_if} conditionally gated, {ungated} with no "
        "pull-request gate)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
