# Build pipeline entrypoint — every target delegates to
# `python3 -m agentbundle catalogue`. Argument parsing happens inside the
# Python package; this file is the thin user surface spec § Boundaries
# § Always do calls for.

# Keep explicit environment/command-line overrides verbatim. The default stays
# lazy so non-Python targets do not pay a pyenv-shim launch; its first use asks
# isolated Python for the active executable, shell-quotes it, then replaces this
# recursive value with the resolved simple value for the rest of the make run.
PYTHON ?= $(eval PYTHON := $(shell python3 -I -B -c 'import shlex, sys; print(shlex.quote(sys.executable) if sys.executable else "")'))$(if $(PYTHON),$(PYTHON),$(error unable to resolve python3 executable))
PYTHONPATH := packages/agentbundle:packages/credbroker:$(PYTHONPATH)
# Stale __pycache__ makes catalogue verify's fresh-output build (CAT-V-014)
# fail mid-run, on a clean tree too. Overridable: PYTHONDONTWRITEBYTECODE= make ci
PYTHONDONTWRITEBYTECODE ?= 1
export PYTHONDONTWRITEBYTECODE
PACKS_DIR ?= packs
OUTPUT_DIR ?= dist
PACK ?=
RECIPE ?=

export PYTHONPATH

.PHONY: lint-editable-install build build-self build-self-dry-run build-check build-check-unleased build-scaffold lint-packs external-catalogue-smoke pre-pr package sast sast-unleased print-sast-dirs print-sast-config validate clean zipapp release-preflight lint-ruff lint-mypy test test-unleased test-after-build-check test-after-build-check-unleased ci

# Portable catalogue engine — lint packs against the adapter contract.
lint-packs:
	$(PYTHON) -m agentbundle catalogue lint --root .

build: lint-packs
	$(if $(filter packs,$(PACKS_DIR)),,$(error build: PACKS_DIR=$(PACKS_DIR) is unsupported; catalogue build resolves packs from --root))
ifeq ($(RECIPE),)
ifeq ($(PACK),)
	$(PYTHON) -m agentbundle catalogue build --root . --output $(OUTPUT_DIR)
else
	$(PYTHON) -m agentbundle catalogue build --root . --output $(OUTPUT_DIR) --pack $(PACK)
endif
else
ifeq ($(PACK),)
	$(PYTHON) -m agentbundle catalogue build --root . --output $(OUTPUT_DIR) --recipe $(RECIPE)
else
	$(PYTHON) -m agentbundle catalogue build --root . --output $(OUTPUT_DIR) --recipe $(RECIPE) --pack $(PACK)
endif
endif

# Local counterpart of catalogue-tooling-ci-gates.yml Gate B's build step, run
# on demand: `make external-catalogue-smoke`. Reproduces the one command that
# reddened Gate B while every local target stayed green, against the same
# committed fixture CI copies, so the two cannot drift.
#
# Deliberately NOT a prerequisite of `ci`. docs/specs/local-ci-orchestration
# ADR-0096 pins `make ci`'s direct prerequisites to exactly build-check,
# lint-ruff, lint-mypy and test-after-build-check, and tools/test-lint-ci-parity.py's
# `local-ci-direct-prereqs` case enforces it. Chaining this target would need a
# frozen-spec amendment; run it directly, or before raising a catalogue-engine
# PR.
#
# CI additionally proves wheel isolation, venv install, lint, verify, package
# and archive verification. This target proves only the build step.
external-catalogue-smoke:
	@tmp_dir="$$(mktemp -d)"; trap 'rm -rf "$$tmp_dir"' EXIT; \
		cp -R tools/tests/fixtures/external-catalogue-smoke/. "$$tmp_dir"; \
		touch "$$tmp_dir/AGENTS.md"; mkdir -p "$$tmp_dir/profiles" "$$tmp_dir/contracts"; \
		$(PYTHON) -m agentbundle catalogue build --root "$$tmp_dir" --output "$$tmp_dir/dist"

# Self-host projection via the portable catalogue engine.
# Windows contributors: python tools/repo/build_gate_chain.py build-self
build-self:
ifeq ($(DRY_RUN),1)
ifeq ($(FORCE),1)
	$(PYTHON) -m agentbundle catalogue self-host --root . --check --force
else
	$(PYTHON) -m agentbundle catalogue self-host --root . --check
endif
else
ifeq ($(FORCE),1)
	$(PYTHON) -m agentbundle catalogue self-host --root . --write --force
else
	$(PYTHON) -m agentbundle catalogue self-host --root . --write
endif
endif

build-self-dry-run:
	$(PYTHON) -m agentbundle catalogue self-host --root . --check

# Projected-artifact + spec-state aggregator. Mirrors what
# docs.yml's per-layer jobs and the `Lifecycle hooks` job run in CI;
# chained into build-check below so `make build-check` is the single
# local gate that covers both lint surfaces (packs source via
# lint-packs, projected .claude/* artifacts via pre-pr). Safe to call
# directly when you want only the artifact checks without rebuilding.
pre-pr:
	$(PYTHON) tools/catalogue/pre_pr_catalogue.py

# Package this catalogue into a distributable archive (three-file Artifactory layout).
# Usage: make package BUNDLE=eng RELEASE=2026.07.24.1 CHANNEL=stable OUTPUT=/tmp/out
BUNDLE   ?=
RELEASE  ?=
CHANNEL  ?=
OUTPUT   ?=

package:
	@test -n "$(BUNDLE)"   || (echo "make package BUNDLE=<name> required"   >&2; exit 1)
	@test -n "$(RELEASE)"  || (echo "make package RELEASE=<ver> required"   >&2; exit 1)
	@test -n "$(CHANNEL)"  || (echo "make package CHANNEL=<ch> required"    >&2; exit 1)
	@test -n "$(OUTPUT)"   || (echo "make package OUTPUT=<dir> required"    >&2; exit 1)
	$(PYTHON) -m agentbundle catalogue package \
		--root . --bundle $(BUNDLE) --release $(RELEASE) --channel $(CHANNEL) --output $(OUTPUT)

# Terminal verdict banner. A local run that skipped a leg CI will run must never
# be mistakable for a full pass, so the LAST thing a gate prints states which
# kind of run it was. The mid-run skip notice below is not enough on its own — it
# scrolls away, and the reader who scrolls to the bottom is exactly the reader
# about to conclude "green, ship it". $(1) is the invoked target's name.
#
# Three outcomes, not two. Since ADR-0086 build-check.yml no longer sets
# SKIP_SAST=1: the SAST/SCA leg is its own `gate-sast` job, and `gate-main`
# invokes this target with SAST_DELEGATED=1 instead. So the third outcome is
# "delegated" — this target did not scan, and something else did. On a laptop
# SKIP_SAST is still a shortcut whose consequence the reader inherits, which is
# why it keeps the INCOMPLETE banner.
#
# "was invoked", not "ran": make reports whether each leg exited 0, and a leg can
# exit 0 having gated nothing — the wired catalogue-curation guard skips its
# path-gate when the base ref is missing or stale (backlog
# `curation-guard-silent-base-skip`). The banner should not assert more than make
# can see.
# The delegated branch keys on `$(origin SAST_DELEGATED)` being `command line`,
# NOT on any environment variable. That is the whole point: GITHUB_WORKFLOW, CI,
# GITHUB_ACTIONS and RUNNER_ENVIRONMENT are each either synthesised by `act` or
# exportable from a devcontainer image or a shell profile, so none of them can
# distinguish "CI deliberately delegated this" from "something in my environment
# happens to be set". Command-line origin can, because only the invoker supplies
# it. An ambient SAST_DELEGATED therefore does NOT reach the quiet banner and does
# NOT skip the leg — it runs the scan and prints the honest "complete" verdict.
define gate_verdict
@if [ "$(origin SAST_DELEGATED)" = "command line" ] && [ -n "$(SAST_DELEGATED)" ]; then \
	printf '\n%s: %s\n' '$(1)' 'complete for this target — SAST/SCA was NOT invoked here; it is delegated.'; \
	printf '%s\n\n' 'This target did not scan. To scan on this machine: make sast'; \
elif [ -n "$(SKIP_SAST)" ]; then \
	printf '\n%s\n' '*************************************************************'; \
	printf '*** %s: %s\n' '$(1)' 'INCOMPLETE — this is NOT a full pass.'; \
	printf '%s\n' '*** The SAST/SCA leg was SKIPPED (SKIP_SAST is set).'; \
	printf '*** CI runs that leg on any diff touching: %s\n' "$(SAST_DIRS)"; \
	printf '*** or: %s\n' "$(SAST_CONFIG)"; \
	printf '%s\n' '*** Re-run without SKIP_SAST before treating this as green.'; \
	printf '%s\n\n' '*************************************************************'; \
else \
	printf '\n%s: %s\n\n' '$(1)' 'complete — every leg of this target was invoked, SAST/SCA included.'; \
fi
endef

# The cross-platform chain owns portable verification, the persistent build,
# and repo-only policy gates. Keeping the sequence there gives the Make target
# and the make-free Windows command one source of truth.
# Windows contributors: python tools/repo/build_gate_chain.py build-check
build-check:
	$(PYTHON) tools/repo/coordination_lease.py with-lease -- $(MAKE) -f $(firstword $(MAKEFILE_LIST)) build-check-unleased
	$(call gate_verdict,make build-check)

build-check-unleased:
	$(PYTHON) tools/repo/build_gate_chain.py build-check --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
	# SAST/SCA gate (ADR-0017) — runs last so the fast, offline drift/lint
	# checks above fail quickly before the slower, network-bound scanners.
	# Two things short-circuit this leg only (the drift + lint gates above always
	# run): SKIP_SAST, still a laptop shortcut; and SAST_DELEGATED passed ON THE
	# COMMAND LINE, which is how `gate-main` says "gate-sast owns the scan".
	# ADR-0086 partially supersedes ADR-0017 here: the leg is no longer chained
	# into the required job in CI, but this Makefile chain is DELIBERATELY intact
	# so `make build-check` on a developer machine still scans — that is what
	# ADR-0017's dogfooding rationale actually required, and tools/assert-sast-
	# chain-reachable.py pins it, because after the split no CI path runs this
	# branch and nothing else would notice it being deleted.
	@if [ "$(origin SAST_DELEGATED)" = "command line" ] && [ -n "$(SAST_DELEGATED)" ]; then \
		echo "build-check: SAST_DELEGATED passed on the command line — SAST/SCA delegated, not invoked by this target"; \
	elif [ -n "$(SKIP_SAST)" ]; then \
		echo "build-check: SKIP_SAST set — skipping SAST/SCA gate (no SAST-relevant changes to scan)"; \
	else \
		$(MAKE) sast; \
	fi

# SAST/SCA gate (ADR-0017). Three OSS scanners, installed from
# tools/requirements-sast.txt as CI-only dev tools — never shipped runtime
# deps. Chained into build-check above so the repo's single native gate runs it
# locally. NOT in build-check.yml CI any more: since ADR-0086 the leg is its own
# `gate-sast` job and `gate-main` passes SAST_DELEGATED=1, so this chain runs only
# on a developer machine — which is exactly what ADR-0017's dogfooding rationale
# required, and what tools/assert-sast-chain-reachable.py now pins. Not added to
# tools/hooks/pre-pr.py or
# tools/catalogue/pre_pr_catalogue.py (the Windows CI path runs the former;
# Semgrep has no Windows support). Linux/macOS only (Semgrep).
#
# These four Semgrep rules are excluded as duplicates of findings already
# dispositioned for Bandit, with no coverage loss (Bandit still flags new
# instances of each class):
#   - sha1   → ONE remaining site (packages/agentbundle/agentbundle/config.py —
#              an 8-char derivation cache key), a documented non-security digest
#              annotated `usedforsecurity=False`; Bandit B324 is satisfied,
#              Semgrep's rule can't read the kwarg. Bandit B324 still flags any
#              new sha1. The second site (loop-cohort.py's review fingerprint)
#              was FIXED in core 2.3.0 rather than suppressed — a real fix
#              satisfies Bandit, Semgrep and the org's Snyk scan, which no
#              exclusion here can reach. Retire this exclusion entirely once
#              config.py's digest is migrated too.
#   - urllib → constant/operator-configured bases, line-precise `# nosec B310`.
#   - xml    → stdlib ElementTree (no external entities/DTDs), `# nosec B314`.
#   - chmod  → the one hit is a restrictive 0o700 (secure); Bandit B103 is
#              correctly silent on it and still flags genuinely-permissive modes.
# Excluding the duplicates avoids a second inline pragma system in shipped pack
# scripts.
SAST_DIRS := tools packs packages tests

# The SAST config / CI surface that *governs* the gate but lives outside
# SAST_DIRS. A diff touching any of these must run SAST so a change that
# loosens the gate (e.g. a wider bandit.yaml exclusion or SEMGREP_EXCLUDE) is
# validated by the gate it changes — build-check.yml's detection treats these
# as SAST-relevant. (tools/requirements-sast.txt and tools/semgrep/ are already
# covered by SAST_DIRS, so they need not be repeated here.)
#
# The two npm lockfiles are here for a different reason than the rest of this
# list: they are the SCA gate's *input*, not its config, and neither `docs-site/`
# nor `web/` is under SAST_DIRS. Without them a dependency-bump PR — a diff whose
# only changed file is a lockfile — would set SKIP_SAST=1 and skip the one gate
# written to check it. `tools/npm-audit-allowlist.toml` is genuine config: an
# added suppression must be validated by the gate it loosens, exactly like a
# widened bandit.yaml exclusion.
SAST_CONFIG := bandit.yaml .snyk Makefile tools/audit-requirements.py tools/npm-audit-allowlist.toml docs-site/package-lock.json web/package-lock.json .github/workflows/build-check.yml .github/workflows/codeql.yml

# Single source of truth for the SAST scan scope + config surface.
# build-check.yml's SAST-relevance detection reads these (`make -s
# print-sast-dirs` / `print-sast-config`) instead of hard-coding the lists, so
# the workflow predicate can't drift from them and silently skip the scan on a
# newly-added scannable dir or an edit to the gate's own config.
print-sast-dirs:
	@echo $(SAST_DIRS)

print-sast-config:
	@echo $(SAST_CONFIG)
# Deliberately-vulnerable rule fixtures. tools/semgrep/fixtures/**/positive.py
# exists to PROVE a custom rule fires; if the gate scanned it, every custom rule
# with a positive fixture would red the build by design. Mirrors bandit.yaml's
# `*/tests/*` exclusion, for the same reason.
#
# Scoped to `positive.py` specifically, NOT the whole fixtures/ directory: a
# directory-wide exclusion would also drop every future negative fixture and
# helper from p/python and p/security-audit, which is wider than the need.
# Residual coverage on what IS excluded: Bandit (bandit.yaml excludes only
# `*/tests/*`) plus tools/test-semgrep-argv-boundary.py, which asserts the exact
# finding count. That self-test runs ONLY the custom rule, so it is not a
# substitute for the registry rulesets — hence keeping the exclusion narrow.
#
# The last two entries are excluded for a different reason than the four above:
# not a false positive, a per-rule TIMEOUT. ADR-0102 admits this vehicle and
# fixes its required shape — a stated residual and a retirement trigger, both
# below. Two interprocedural env→subprocess
# taint rules exceed the default 5s/rule/file budget on one large,
# subprocess-dense dev-CLI test file each — `dangerous-system-call-tainted-env-args`
# on tools/test_workspace_status.py (3,422 lines) and
# `dangerous-subprocess-use-tainted-env-args` on tools/test_workspace_status_cli.py
# (3,817 lines). Those two timeouts are the only reason the scan exits non-zero
# under --strict on this tree. Every figure in this block was measured on semgrep
# 1.175.0 — the floor tools/requirements-sast.txt pins and CI installs, not
# whatever a laptop happens to carry; see the version preflight in sast-unleased.
#
# Scoped by PATH, not by rule id, and that choice is the whole point. The
# obvious spelling is `--exclude-rule <id>`, which takes a rule id only —
# semgrep has no rule+path scoping in one flag — so it would drop both rules
# repo-wide. Measured what that costs: a canary
# `subprocess.run([os.environ["TOOL"], "--version"])` planted under packs/ is
# reported by `dangerous-subprocess-use-tainted-env-args` with the rules on and
# reported by NOTHING with them off — not by bandit at this gate's floor
# (run-bandit-gate.py pins --severity-level medium, and B603/B606/B607 are LOW),
# and not by CodeQL, which is not a required check on main AND cannot see the
# source kind at all: its default `remote` threat model treats os.environ as
# trusted, and the pinned codeql-action accepts no `threat-models` setting to
# change that (tracked as `codeql-cannot-see-environment-sources`). Excluding the
# two rules would therefore have left packages/credbroker/ and
# packs/core/.apm/hooks/session-start.py — the surface
# tools/semgrep/env-path-taint.yml calls the one place the threat is real — with
# no blocking detector for env-tainted subprocess argv at all.
#
# Excluding the two FILES instead keeps both rules live everywhere else. What it
# gives up is every rule that applies to them — measured on one of the two at
# this recipe's config: 344 rules loaded, 196 run on that file, 0 findings —
# which codeql.yml's `**/test_*.py` already ignores. Bandit still scans them, but not
# for the class dropped here: its subprocess tail is LOW and this gate's floor is
# medium. Measured at the time of writing, the full config at --timeout 60 finds
# 0 findings and 0 errors on both files, so nothing detected is being hidden.
#
# The patterns carry a slash, so semgrep anchors them at the git root and they
# match exactly the two files named — verified by diffing the scanned set with
# and without: it drops by exactly two, and those two are the named files. In a
# non-git tree semgrep would anchor per scan root instead, and `tools/...` would
# be read against each of SAST_DIRS; no such path exists today.
#
# This costs nothing measurable. Keeping both rules live on the other ~1,565
# files runs the same wall time as excluding them repo-wide (35s either way on
# 1.175.0), so the blocking coverage above is retained for free rather than
# bought.
#
# Nothing detects a stale entry — semgrep accepts an `--exclude` naming a file
# that no longer exists, silently and with exit 0. Tracked as
# `sast-semgrep-exclude-has-no-staleness-detector`.
#
# `--timeout 60` also clears the timeouts (measured: exit 0) and is deliberately
# NOT used: it masks a pathological rule/file interaction rather than fixing it.
# It costs little wall time — the cap is per rule per file, so only the two
# pathological pairs reach it — but a masked interaction is not a fixed one.
#
# Retire once semgrep's taint engine stops timing out on these pairs, or once
# either file is split below the per-rule budget. Still timing out as of 1.175.0,
# nine releases after the behaviour was first seen, so this is not a transient.
SEMGREP_EXCLUDE := \
	--exclude "tools/semgrep/fixtures/*/positive.py" \
	--exclude-rule python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 \
	--exclude-rule python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected \
	--exclude-rule python.lang.security.use-defused-xml.use-defused-xml \
	--exclude-rule python.lang.security.audit.insecure-file-permissions.insecure-file-permissions \
	--exclude "tools/test_workspace_status.py" \
	--exclude "tools/test_workspace_status_cli.py"

sast:
	$(PYTHON) tools/repo/coordination_lease.py with-lease -- $(MAKE) -f $(firstword $(MAKEFILE_LIST)) sast-unleased

sast-unleased:
	@command -v bandit   >/dev/null 2>&1 || { echo "make sast: bandit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v pip-audit >/dev/null 2>&1 || { echo "make sast: pip-audit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v semgrep   >/dev/null 2>&1 || { echo "make sast: semgrep not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	# Presence is not enough for semgrep, unlike the tools around it: its timeouts
	# and --strict diagnostics are engine behaviour that moves between releases,
	# and SEMGREP_EXCLUDE's justification is measurements taken at one version.
	# Both bounds are read from the manifest so the two cannot drift.
	@$(PYTHON) tools/check-semgrep-version.py
	@command -v npm       >/dev/null 2>&1 || { echo "make sast: npm not found — install Node.js (>=24, per docs-site/package.json engines) for the npm SCA leg" >&2; exit 1; }
	# Bandit's stderr is a gate signal, not chatter (ADR-0084): under -q it
	# carries only diagnostics about the scan's own integrity — a `# nosec` it
	# could not parse, one that matched no finding, a file it could not read —
	# and none of those move its exit code. run-bandit-gate.py fails on any of
	# them. The self-test below proves it, for the same reason the two
	# self-tests further down exist: this gate is silent when it works and
	# would be just as silent if it were simplified back into a no-op.
	python3 tools/test-sast-stderr-gate.py
	python3 tools/run-bandit-gate.py $(SAST_DIRS)
	# The filter below stands in front of pip-audit, so a bug that drops a
	# *third-party* pin would take this gate green over an unaudited dependency.
	# Prove it before trusting it.
	python3 tools/test-audit-requirements.py
	# Audits every third-party pin, and skips this repo's own packages —
	# `dependencies = []` on both, so they contribute no tree, and resolving them
	# against the public index would couple a merge to a release that has not
	# happened yet. Every skip is printed. See tools/audit-requirements.py.
	python3 tools/audit-requirements.py $$(find packs -name requirements.txt | sort)
	# Discover tools/requirements*.txt in the auditor so a new CI manifest is
	# covered at once; requirements-sast.txt remains on its direct, suppression-
	# bearing invocation below.
	python3 tools/audit-requirements.py --tools-manifests
	# Audit the PEP 517 backends that execute during package builds. Extract the
	# declarations from pyproject.toml itself so the SCA input cannot drift.
	python3 tools/audit-requirements.py --build-system \
		packages/agentbundle/pyproject.toml packages/credbroker/pyproject.toml
	# Audit AgentBundle's authoring/lint extra from pyproject.toml so the SCA
	# input fails closed if the optional dependency declaration changes.
	python3 tools/audit-requirements.py --optional-group lint \
		packages/agentbundle/pyproject.toml
	# No suppressions. This leg carried four `--ignore-vuln` flags for semgrep's
	# mcp/click transitive pins until semgrep 1.174 shipped mcp==1.29.0 and
	# click~=8.4.2, clearing them. The removed flags named CVE ids while
	# pip-audit now reports the same three advisories under PYSEC ids; OSV
	# records them as aliases, one to one -- CVE-2026-52870/PYSEC-2026-3481,
	# CVE-2026-52869/PYSEC-2026-3482, CVE-2026-59950/PYSEC-2026-3483 -- so the
	# suppressions retired are exactly the advisories measured as cleared.
	# Note what this command does and does not see: pip-audit RESOLVES the
	# requirements file, so it always audits the newest version the range allows
	# and would read clean even at the old `semgrep>=1.166` floor. It says
	# nothing about the semgrep actually installed on this machine — that is what
	# requirements-sast.txt's floor is for, and why the floor moved with this
	# change rather than being left behind.
	# A new suppression here needs a written diagnosis and a recorded unblock
	# condition, the discipline that retired the last four.
	@echo "pip-audit -r tools/requirements-sast.txt"
	@pip-audit -r tools/requirements-sast.txt
	# Both shipped packages declare dependencies=[]; their optional extras are
	# the only third-party code either can pull, so audit those explicitly.
	# Mirror packages/credbroker/pyproject.toml [crypto] and
	# packages/agentbundle/pyproject.toml [lint]. The [lint] extra was missed
	# until an audit of the AST07 backlog entry went looking: the entry asked
	# whether SCA was wired for agentbundle, the runtime answer was "there is
	# nothing to scan", and the extra was the one thing that was not nothing.
	@printf 'cryptography>=42\nargon2-cffi>=23\npyyaml>=6.0\n' | pip-audit -r /dev/stdin
	# npm SCA leg (ADR-0083). pip-audit above covers every Python dependency and
	# no JavaScript; the repo's two npm projects ship their lockfiles into built
	# output. Same "prove it before trusting it" order as the pip-audit leg: the
	# self-test runs first, because a live audit against a healthy registry is
	# silent both when the gate works and when it has been broken into a no-op.
	python3 tools/test-audit-npm.py
	python3 tools/audit-npm.py --root .
	# Prove the wrapper below still speaks before trusting its silence — same
	# order and same reason as the two SCA self-tests above.
	python3 tools/test-semgrep-strict-gate.py
	# --strict turns semgrep's own diagnostics into a gate signal. It buys exactly
	# one thing: a PARTIAL parse failure (an unbalanced bracket, a nonsense token)
	# now fails the build instead of being ignored. It does NOT close the
	# whole-file case — `def broken(:` still yields empty errors and exit 0 even
	# under --strict — so `sast-semgrep-unparseable-target-reads-clean` in
	# workspace.toml stays open; tools/test-semgrep-argv-boundary.py's `scan_all`
	# docstring holds the measured behaviour.
	#
	# It runs behind run-semgrep-gate.py, not on a bare recipe line, because
	# --strict and --quiet together exit non-zero with zero bytes on both streams
	# (measured, 1.166.0). ADR-0084 wrapped Bandit for this exact reason — a
	# control this quiet needs a script and a test, not a flag.
	#
	# Revisit if: p/python and p/security-audit are fetched unpinned, so a future
	# registry rule that times out on any file in SAST_DIRS reds the gate on an
	# unrelated diff. ADR-0017 already accepts registry churn and names pin-or-
	# vendor as the mitigation. Reach for that before widening SEMGREP_EXCLUDE.
	python3 tools/run-semgrep-gate.py --config p/python --config p/security-audit --config tools/semgrep/ --strict --error --quiet --metrics off $(SEMGREP_EXCLUDE) $(SAST_DIRS)
	# Prove the custom rules still fire. The scan above is silent both when the
	# rules work and when they have been broken into no-ops, so it cannot tell
	# the two apart — this self-test asserts the exact finding count on a
	# deliberately-vulnerable fixture and on its fixed twin. It lives here, not
	# in docs.yml, because it needs semgrep on PATH: there it would skip
	# silently and gate nothing.
	python3 tools/test-semgrep-argv-boundary.py

build-scaffold:
	@test -n "$(OUTPUT)" || (echo "make build-scaffold OUTPUT=<dir> required" >&2; exit 1)
	$(PYTHON) -m agentbundle.build scaffold --packs-dir $(PACKS_DIR) --output $(OUTPUT)

validate:
	$(PYTHON) -m agentbundle.build validate docs/contracts/adapter.toml

clean:
	rm -rf $(OUTPUT_DIR)

zipapp:
	$(PYTHON) tools/build_zipapp.py $(OUTPUT_DIR)

release-preflight: lint-packs
	@bash tools/repo/release_check.sh

# ── Static analysis + tests ──────────────────────────────────────────────────
# Do NOT install agentbundle or credbroker to work on this repository.
#
# Run things this way instead:
#   python3 -m agentbundle <args>      the CLI, from this worktree, no install
#   make test / make build-check       gates; PYTHONPATH (line 7) supplies both
#   pytest <path>                      pyproject.toml's [tool.pytest.ini_options]
#                                      pythonpath supplies both, no env prefix
#
# Why not install: an editable install is global to the interpreter, and several
# worktrees share one here. `pip install -e` from this worktree changes what every
# other worktree's subprocesses import, and doing it while a peer's gates are
# running kills them mid-run. `make lint-editable-install` refuses the state where
# that has already happened. See ADR-0094.
#
# A plain (wheel) install is fine and is how the `agentbundle` console script gets
# onto PATH; an editable install pointing at THIS worktree is fine too. Neither is
# what these targets use.
#
# Requires: ruff mypy pytest
#           pip install -r tools/requirements.txt        (jsonschema>=4.0, PyYAML)
#           cryptography argon2-cffi                     (credbroker's [crypto]
#               extras; without them the vault tests skip instead of asserting)
#           pip install -r tools/requirements-sast.txt   (build-check SAST leg;
#               or SKIP_SAST=1)

# Refuses an editable install of these packages that points at another worktree
# — the state that makes this worktree's subprocesses import someone else's code.
# Silent on a plain install and on an editable install pointing here.
lint-editable-install:
	$(PYTHON) tools/repo/editable_install_guard.py

lint-ruff:
	@command -v ruff >/dev/null 2>&1 || { echo "make lint-ruff: ruff not found — run: pip install ruff" >&2; exit 1; }
	$(PYTHON) tools/lint-ruff.py

lint-mypy:
	@command -v mypy >/dev/null 2>&1 || { echo "make lint-mypy: mypy not found — run: pip install mypy" >&2; exit 1; }
	$(PYTHON) tools/lint-mypy.py

# Core package + tools tests. The full CI test matrix runs on GitHub Actions.
# Dev-time Python deps are listed above; agentbundle and credbroker are not
# among them, because these targets import both from source.
#
# Do NOT collapse the pack-test lines into `pytest packs/*/tests/`. Pack test
# suites share basenames across skills (several `test_render.py`,
# `test_exit_codes.py`, `test_next_ordinal.py`), and so do the modules they
# import — three skills ship a `render.py`, two ship a byte-identical
# `ssrf_check.py`. pytest refuses the duplicate test basenames outright, and a
# sys.path-based sibling import would bind the first `render` for all three
# renderers.
#
# So a pack test suite gets its own process by default. The grouped invocations
# below are not exceptions to that rule — each one is a compatibility class
# declared in tools/pack_test_compatibility.py, whose members were characterised
# (isolated vs grouped node IDs, forward and reverse order) before being
# declared, and whose safety lint-pack-test-boundary.py re-derives from source on
# every run. Adding a suite directory does not add it to a class.
#
# Two consequences worth knowing before editing these lines. A grouped command
# must name every member: an ancestor path like `packs/<pack>/tests/` would let a
# future suite join the class silently, and the lint refuses it. And a suite with
# a collection floor must stay the sole target of its own invocation, because
# pytest_collection_floor counts a whole session — which is why the two
# desk-research floor lines are separate from the six-member class.
#
# See ADR-0101 and catalogue-authoring-standards.md § 4.
test:
	$(PYTHON) tools/repo/coordination_lease.py with-lease -- $(MAKE) -f $(firstword $(MAKEFILE_LIST)) test-unleased

override define run-test-suite
$(PYTHON) -m pytest packages/agentbundle/tests/ -q
$(PYTHON) -m pytest packages/credbroker/ -q
$(PYTHON) tools/lint-conformance-portability.py --root .
# spec/site-ci-contract-closure AC6: the docs-palette WCAG gate runs locally
# too, so `make ci` covers what gate-main's contrast step runs.
$(PYTHON) tools/check-docs-contrast.py
# spec/docs-site-build-contract-hardening AC6: the rehype plugin suite runs
# locally too. Without this `make ci` stays green with a red plugin suite —
# the orphan class the register tracks as tools-test-runner-boundary.
@command -v npm >/dev/null 2>&1 || { echo "make test: npm not found — install Node.js (>=24, per docs-site/package.json engines)" >&2; exit 1; }
@test -d docs-site/node_modules || { echo "make test: docs-site deps missing — run: npm ci --prefix docs-site" >&2; exit 1; }
npm run test:plugins --prefix docs-site
$(PYTHON) tools/test-pages-workflow.py
$(PYTHON) tools/test-pages-concurrency.py
$(PYTHON) -m pytest tests/ -q
$(PYTHON) -m pytest packs/core/tests/hooks/ -q
$(PYTHON) -m pytest packs/core/tests/pack/ -q
$(PYTHON) -m pytest packs/core/tests/skills/adapt-to-project/ -q
$(PYTHON) -m pytest packs/core/tests/skills/author-brief/ -q
$(PYTHON) -m pytest packs/core/tests/skills/author-delivery-brief/ $(2) -q
$(PYTHON) -m pytest packs/core/tests/skills/bug-fix/ -q
$(PYTHON) -m pytest packs/core/tests/skills/capture-work/ -q
$(PYTHON) -m pytest packs/core/tests/skills/close-work/ -q
$(PYTHON) -m pytest packs/core/tests/skills/contract-acquisition/ -q
$(PYTHON) -m pytest packs/core/tests/skills/intake-intent/ -q
$(PYTHON) -m pytest packs/core/tests/skills/new-spec/ -q
$(PYTHON) -m pytest packs/core/tests/skills/project-knowledge/ -q
$(PYTHON) -m pytest packs/core/tests/skills/receive-brief/ -q
$(PYTHON) -m pytest packs/core/tests/skills/work-intake/ -q
$(PYTHON) -m pytest packs/core/tests/skills/work-loop/ $(1) -q
$(PYTHON) -m pytest packs/core/tests/skills/workspace-status/ -q
$(PYTHON) -m pytest packs/catalogue-curation/tests/pack/ -q
$(PYTHON) -m pytest packs/catalogue-curation/tests/skills/compile-okf/ -q
$(PYTHON) -m pytest packs/product-documentation/tests/ -q
$(PYTHON) -m pytest \
	packs/architect/tests/pack/ \
	packs/architect/tests/skills/architect-assess/ \
	packs/architect/tests/skills/architect-design/ \
	packs/architect/tests/skills/architect-review/ -q
$(PYTHON) -m pytest packs/credential-brokers/tests/pack/ -q
$(PYTHON) -c "import httpx"
$(PYTHON) -m pytest packs/atlassian/tests/skills/jira/test_intake_policy.py -q
$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-align/test_jira_align_intake_policy.py -q
$(PYTHON) -m pytest packs/atlassian/tests/skills/flow-metrics/ -q
$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-brief-intake/ -q
$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-align-brief-intake/ -q
$(PYTHON) -m pytest packs/github/tests/skills/github-brief-intake/ -q
$(PYTHON) -m pytest packs/product-engineering/tests/pack/ -q
$(PYTHON) -m pytest \
	packs/agent-skill-engineering/tests/pack/ \
	packs/agent-skill-engineering/tests/integration/ \
	packs/agent-skill-engineering/tests/skills/author_or_update/ \
	packs/agent-skill-engineering/tests/skills/review_or_optimize/ -q
$(PYTHON) -m pytest \
	packs/linear/tests/skills/linear/ \
	packs/linear/tests/skills/linear-brief-intake/ -q
$(PYTHON) -m pytest --import-mode=importlib \
	packs/converters/tests/skills/markdown-to-html/ \
	packs/converters/tests/skills/mermaid-renderer/ -q
$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research/ -q -p tools.pytest_collection_floor --minimum-collected=9 --collection-floor-suite=packs/desk-research/tests/skills/desk-research/
$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-start/ -q -p tools.pytest_collection_floor --minimum-collected=7 --collection-floor-suite=packs/desk-research/tests/skills/desk-research-project-start/
$(PYTHON) -m pytest --import-mode=importlib \
	packs/desk-research/tests/pack/ \
	packs/desk-research/tests/skills/desk-research-project-check/ \
	packs/desk-research/tests/skills/desk-research-project-digest/ \
	packs/desk-research/tests/skills/desk-research-project-status/ \
	packs/desk-research/tests/skills/desk-research-project-synthesize/ \
	packs/desk-research/tests/skills/devils-advocate/ -q
$(PYTHON) -m pytest tools/test_build_gate_chain.py tools/test_journey_editorial_decisions.py tools/test_catalogue_tooling_rewire.py tools/test_catalogue_tooling_docs.py tools/test_validate_guides.py tools/test_check_guide_index.py tools/test_catalogue_navigation.py tools/test_documentation_entry_links.py tools/test_build_site_link_rewrites.py tools/test_check_rendered_site_links.py tools/test_build_site_routing.py tools/test_check_docs_contrast.py tools/test_build_site_inventory.py tools/test_build_site_projection.py tools/test_build_site_sidebar.py tools/test_browser_gate_subset.py tools/test_local_ci_shared_test_deduplication.py -q
$(3)
$(PYTHON) -m pytest tools/test_worktree_hygiene.py -q
$(PYTHON) -m pytest tools/test_worktree_lease_interlock.py -q
$(PYTHON) -m pytest tools/test_worktree_import_resolution.py -q
$(PYTHON) -m pytest tools/test_editable_install_guard.py -q
# This exact class is stable in forward/reverse order and under the state-leak
# characterization controls. The import-time path guard deliberately retains
# its sanitized full-roster child collection inside this outer pytest process.
$(PYTHON) -m pytest \
	tools/test_import_time_path_leaks.py \
	tools/test_managed_child.py \
	tools/test_coordination_lease.py \
	tools/test_branch_added_paths.py \
	tools/test_bootstrap.py -q
$(PYTHON) -m pytest tools/test_run_slot.py -q
$(PYTHON) -m pytest tools/test_with_lease_cli.py -q
$(PYTHON) -m pytest tools/test_playwright_evidence_lifecycle.py -q
$(PYTHON) -m pytest tools/test_worktree_lifecycle_hooks.py -q
$(PYTHON) -m pytest tools/test_frontend_runtime.py -q
$(PYTHON) -m pytest tools/test_check_artifact_contents.py -q
$(PYTHON) -m pytest \
	tools/test_lint_agents_md_diataxis_block.py \
	tools/test_lint_agents_md_legacy_block.py \
	tools/test_lint_agents_md_risk_block.py \
	tools/test_lint_agents_md_frontmatter_scope.py \
	tools/test_catalogue_curation_guard.py \
	tools/test_contract_parity.py \
	tools/test_marketplace_envelope_parity.py \
	tools/test_guide_authoring_standard.py \
	tools/test_release_check.py \
	tools/test_check_release_impact.py \
	tools/test_scaffold_projection.py \
	tools/test_conformance_portability.py \
	tools/test_lint_guides_no_repo_only_refs.py \
	tools/test_okf_pre_pr.py \
	tools/test_pack_test_compatibility.py -q
# The identity derivation is what catches the SILENT hazard — a subject module
# bound to the wrong path, or a sys.path mutation added to a class member.
# Collection-only characterization cannot see either, and at ~2s this is the
# fast feedback for anyone editing packs/*/tests/**. The full characterization
# (isolated-vs-grouped node IDs, reverse order, importlib controls) spawns 30
# collect-only processes for ~36s and runs in build-check.yml instead.
$(PYTHON) tools/lint-pack-test-boundary.py \
	--check compatibility-classes-are-well-formed \
	--check class-members-keep-distinct-module-identity
endef

test-unleased: lint-editable-install
	$(call run-test-suite,,,$(PYTHON) -m pytest tools/test_workspace_status.py tools/test_workspace_status_cli.py -q)

# build-check has already run the five exact shared files before this composed
# route starts. Standalone `make test` deliberately calls the same macro above
# without exclusions and remains the complete public test gate. The reduction
# is safe only behind test-after-build-check's explicit owner dependency;
# tools/test_local_ci_shared_test_deduplication.py prevents ownership/exclusion
# drift and proves recursive and parallel Make retain that ordering.
test-after-build-check: build-check
	$(PYTHON) tools/repo/coordination_lease.py with-lease -- $(MAKE) -f $(firstword $(MAKEFILE_LIST)) test-after-build-check-unleased

test-after-build-check-unleased: lint-editable-install
	$(call run-test-suite,--ignore=packs/core/tests/skills/work-loop/test_lint_spec_status.py --ignore=packs/core/tests/skills/work-loop/test_lint_traceability.py,--ignore=packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py,)

# Local CI gate. Exactly one workflow is watched: build-check.yml.
# tools/lint-ci-parity.py — chained into build-check — holds a disposition per
# step: each one declares either the make target that covers it locally, or why no
# local gate can. So a CI step cannot be added, renamed, or removed without someone
# dispositioning it. It does NOT prove the two environments verify the same things,
# nor catch a gate added inside a step that already has a disposition — read that
# file's § What it does not prove before treating a clean run as equivalence. The previous claim here ("mirrors build-check.yml +
# docs.yml") was unverified and had drifted: the catalogue-curation guard and the
# SAST leg both reached CI red past a green local run
# (spec/local-gate-ci-parity).
#
# No other workflow is covered. `make pre-pr` incidentally overlaps much of
# docs.yml, but nothing verifies that overlap, so a green `make ci` is not
# evidence about it; every workflow's in/out-of-scope status is recorded in
# lint-ci-parity.py's WORKFLOW_SCOPE, which fails on an unclassified new one.
#
# Skip SAST: SKIP_SAST=1 make ci — the run then ends with an INCOMPLETE banner,
# because a run missing a leg CI will run must not read like a pass.
# build-check already runs pre_pr_catalogue.py --skip-verify after its one
# portable verification and persistent build. A direct pre-pr prerequisite here
# would repeat both the aggregator and portable verification in the same CI run.
ci: build-check lint-ruff lint-mypy test-after-build-check
	$(call gate_verdict,make ci)

# ── Site publishing ──────────────────────────────────────────────────────────
# Requires: make bootstrap-sites (one-time setup) — site-build builds web/ first,
# so the web tree is needed here too, not only docs-site.
# Build order is load-bearing: web/ build cleans build/; docs-site/ build
# writes into build/docs/. These targets are the valid LOCAL full-generation
# sequence — one build-site.py pass, then both builds. CI is NOT identical; see
# docs-site/AGENTS.md § Build, which owns that comparison. site-link-check is the
# one target here that runs tools/check-rendered-site-links.py after both builds,
# as CI does.

.PHONY: site-sync site-build site-link-check site-serve

site-sync:  ## Aggregate repo content into docs-site/src/content/docs/ (run before build/serve)
	$(PYTHON) tools/build-site.py

site-build: site-sync  ## Build full site → build/ (marketing) + build/docs/ (Starlight)
	npm run build --prefix web
	npm run build --prefix docs-site

site-link-check: site-build  ## Build both sites, then audit emitted internal links
	$(PYTHON) tools/check-rendered-site-links.py --build-dir build

site-serve: site-sync  ## Start Starlight dev server at http://localhost:4321
	npm run dev --prefix docs-site

.PHONY: worktree-doctor bootstrap-web bootstrap-docs-site bootstrap-sites web-browser-gate

worktree-doctor:  ## Inspect worktree-local generated and runtime artifacts
	$(PYTHON) tools/repo/worktree_hygiene.py scan

bootstrap-web:  ## Install only web npm dependencies
	$(PYTHON) tools/repo/bootstrap.py web

bootstrap-docs-site:  ## Install only docs-site npm dependencies
	$(PYTHON) tools/repo/bootstrap.py docs-site

bootstrap-sites:  ## Install web and docs-site npm dependencies
	$(PYTHON) tools/repo/bootstrap.py sites

web-browser-gate:  ## Run the browser gate on a leased preview port
	$(PYTHON) tools/repo/frontend_runtime.py gate
