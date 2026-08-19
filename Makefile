# Build pipeline entrypoint — every target delegates to
# `python3 -m agentbundle.build`. Argument parsing happens inside the
# Python package; this file is the thin user surface spec § Boundaries
# § Always do calls for.

PYTHON ?= python3
PYTHONPATH := packages/agentbundle:packages/credbroker:$(PYTHONPATH)
PACKS_DIR ?= packs
OUTPUT_DIR ?= dist
PACK ?=
RECIPE ?=

export PYTHONPATH

.PHONY: build build-self build-self-dry-run build-check build-scaffold lint-packs pre-pr package sast print-sast-dirs print-sast-config validate clean zipapp release-preflight lint-ruff lint-mypy test ci

# Portable catalogue engine — lint packs against the adapter contract.
lint-packs:
	$(PYTHON) -m agentbundle catalogue lint --root .

build: lint-packs
ifeq ($(RECIPE),)
ifeq ($(PACK),)
	$(PYTHON) -m agentbundle.build build --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
else
	$(PYTHON) -m agentbundle.build build --pack $(PACK) --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
endif
else
ifeq ($(PACK),)
	$(PYTHON) -m agentbundle.build build --recipe $(RECIPE) --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
else
	$(PYTHON) -m agentbundle.build build --recipe $(RECIPE) --pack $(PACK) --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
endif
endif

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
	$(call gate_verdict,make build-check)

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
SEMGREP_EXCLUDE := \
	--exclude "tools/semgrep/fixtures/*/positive.py" \
	--exclude-rule python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 \
	--exclude-rule python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected \
	--exclude-rule python.lang.security.use-defused-xml.use-defused-xml \
	--exclude-rule python.lang.security.audit.insecure-file-permissions.insecure-file-permissions

sast:
	@command -v bandit   >/dev/null 2>&1 || { echo "make sast: bandit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v pip-audit >/dev/null 2>&1 || { echo "make sast: pip-audit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v semgrep   >/dev/null 2>&1 || { echo "make sast: semgrep not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
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
	python3 tools/audit-requirements.py tools/requirements.txt $$(find packs -name requirements.txt | sort)
	# Audit the PEP 517 backends that execute during package builds. Extract the
	# declarations from pyproject.toml itself so the SCA input cannot drift.
	python3 tools/audit-requirements.py --build-system \
		packages/agentbundle/pyproject.toml packages/credbroker/pyproject.toml
	# Audit AgentBundle's authoring/lint extra from pyproject.toml so the SCA
	# input fails closed if the optional dependency declaration changes.
	python3 tools/audit-requirements.py --optional-group lint \
		packages/agentbundle/pyproject.toml
	# semgrep>=1.166 hard-pins mcp==1.23.3 and click~=8.1.8, both carrying known CVEs
	# (mcp: CVE-2026-52870, CVE-2026-52869, CVE-2026-59950; click: PYSEC-2026-2132).
	# Attack surface is negligible: these packages are SAST-tooling transitive deps only,
	# never present in shipped artifacts (which declare dependencies=[]); exploiting the
	# mcp CVEs requires a Semgrep backend compromise + targeted CI attack; the click CVE
	# requires controlling semgrep's CLI args (i.e. write access to this repo).
	# Suppression is unblocked once semgrep ships mcp>=1.28.1 + click>=8.3.3 deps.
	# Full diagnosis and unblock condition: workspace.toml [backlog].open, entry
	# `semgrep-mcp-cve-allowlist` — the suppressions' only recorded expiry.
	@echo "pip-audit -r tools/requirements-sast.txt (semgrep transitive-dep CVE allowlist applied)"
	@pip-audit -r tools/requirements-sast.txt \
		--ignore-vuln CVE-2026-52870 \
		--ignore-vuln CVE-2026-52869 \
		--ignore-vuln CVE-2026-59950 \
		--ignore-vuln PYSEC-2026-2132
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
	semgrep --config p/python --config p/security-audit --config tools/semgrep/ --error --quiet --metrics off $(SEMGREP_EXCLUDE) $(SAST_DIRS)
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
# Requires: python -m pip install -e packages/agentbundle ruff mypy pytest
#           python -m pip install -e 'packages/credbroker[crypto]'
#           pip install -r tools/requirements-sast.txt  (for build-check SAST leg; or SKIP_SAST=1)

lint-ruff:
	@command -v ruff >/dev/null 2>&1 || { echo "make lint-ruff: ruff not found — run: pip install ruff" >&2; exit 1; }
	$(PYTHON) tools/lint-ruff.py

lint-mypy:
	@command -v mypy >/dev/null 2>&1 || { echo "make lint-mypy: mypy not found — run: pip install mypy" >&2; exit 1; }
	$(PYTHON) tools/lint-mypy.py

# Dev-time Python deps beyond agentbundle: jsonschema>=4.0, PyYAML  (see tools/requirements.txt)
# Core package + tools tests. The full CI test matrix runs on GitHub Actions.
#
# Do NOT collapse the pack-test lines into `pytest packs/*/tests/`. Pack test
# suites share basenames across skills (several `test_render.py`,
# `test_exit_codes.py`, `test_next_ordinal.py`), and so do the modules they
# import — three skills ship a `render.py`, two ship a byte-identical
# `ssrf_check.py`. pytest refuses the duplicate test basenames outright, and a
# sys.path-based sibling import would bind the first `render` for all three
# renderers. One process per skill test directory is a correctness requirement,
# not a style choice; see catalogue-authoring-standards.md § 4.
test:
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
	$(PYTHON) -m pytest tests/ -q
	$(PYTHON) -m pytest packs/core/tests/hooks/ -q
	$(PYTHON) -m pytest packs/core/tests/pack/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/adapt-to-project/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/author-brief/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/bug-fix/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/capture-work/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/new-spec/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/project-knowledge/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/receive-brief/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/work-intake/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/work-loop/ -q
	$(PYTHON) -m pytest packs/core/tests/skills/workspace-status/ -q
	$(PYTHON) -m pytest packs/catalogue-curation/tests/pack/ -q
	$(PYTHON) -m pytest packs/catalogue-curation/tests/skills/compile-okf/ -q
	$(PYTHON) -m pytest packs/product-documentation/tests/ -q
	$(PYTHON) -m pytest packs/architect/tests/pack/ -q
	$(PYTHON) -m pytest packs/architect/tests/skills/architect-review/ -q
	$(PYTHON) -m pytest packs/credential-brokers/tests/pack/ -q
	$(PYTHON) -c "import httpx"
	$(PYTHON) -m pytest packs/atlassian/tests/skills/jira/test_intake_policy.py -q
	$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-align/test_jira_align_intake_policy.py -q
	$(PYTHON) -m pytest packs/atlassian/tests/skills/flow-metrics/ -q
	$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-brief-intake/ -q
	$(PYTHON) -m pytest packs/atlassian/tests/skills/jira-align-brief-intake/ -q
	$(PYTHON) -m pytest packs/github/tests/skills/github-brief-intake/ -q
	$(PYTHON) -m pytest packs/product-engineering/tests/pack/ -q
	$(PYTHON) -m pytest packs/linear/tests/skills/linear/ -q
	$(PYTHON) -m pytest packs/linear/tests/skills/linear-brief-intake/ -q
	$(PYTHON) -m pytest packs/converters/tests/skills/markdown-to-html/ -q
	$(PYTHON) -m pytest packs/converters/tests/skills/mermaid-renderer/ -q
	@n=$$($(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research/ -q --collect-only | grep -c '::' || true); \
	 if [ "$$n" -lt 9 ]; then echo "packs/desk-research/tests/skills/desk-research/ collected $$n, expected >= 9" >&2; exit 1; fi
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research/ -q
	@n=$$($(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-start/ -q --collect-only | grep -c '::' || true); \
	 if [ "$$n" -lt 7 ]; then echo "packs/desk-research/tests/skills/desk-research-project-start/ collected $$n, expected >= 7" >&2; exit 1; fi
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-start/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/pack/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-check/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-digest/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-status/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-synthesize/ -q
	$(PYTHON) -m pytest packs/desk-research/tests/skills/devils-advocate/ -q
	$(PYTHON) -m pytest tools/test_build_gate_chain.py tools/test_journey_editorial_decisions.py tools/test_catalogue_tooling_rewire.py tools/test_catalogue_tooling_docs.py tools/test_validate_guides.py tools/test_check_guide_index.py tools/test_catalogue_navigation.py tools/test_documentation_entry_links.py tools/test_build_site_link_rewrites.py tools/test_check_rendered_site_links.py tools/test_build_site_routing.py tools/test_check_docs_contrast.py tools/test_build_site_inventory.py tools/test_build_site_projection.py tools/test_build_site_sidebar.py tools/test_browser_gate_subset.py -q
	$(PYTHON) -m pytest tools/test_workspace_status.py tools/test_workspace_status_cli.py -q
	$(PYTHON) -m pytest tools/test_check_artifact_contents.py -q
	$(PYTHON) -m pytest \
		tools/test_lint_agents_md_diataxis_block.py \
		tools/test_lint_agents_md_legacy_block.py \
		tools/test_lint_agents_md_risk_block.py \
		tools/test_catalogue_curation_guard.py \
		tools/test_contract_parity.py \
		tools/test_marketplace_envelope_parity.py \
		tools/test_guide_authoring_standard.py \
		tools/test_release_check.py \
		tools/test_check_release_impact.py \
		tools/test_scaffold_projection.py \
		tools/test_conformance_portability.py \
		tools/test_lint_guides_no_repo_only_refs.py \
		tools/test_okf_pre_pr.py -q

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
ci: build-check pre-pr lint-ruff lint-mypy test
	$(call gate_verdict,make ci)

# ── Site publishing ──────────────────────────────────────────────────────────
# Requires: npm ci --prefix docs-site (one-time setup)
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
