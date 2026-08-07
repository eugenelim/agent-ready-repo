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
# Three outcomes, not two. build-check.yml sets SKIP_SAST=1 itself whenever a
# PR's diff touches nothing SAST-relevant, so shouting INCOMPLETE inside a green
# required check on most PRs would train readers to ignore the banner — the same
# way the mid-run echo trained them to miss the skip. In CI the skip is a
# decision the workflow made from the diff; on a laptop it is a shortcut whose
# consequence the reader is about to inherit.
#
# "was invoked", not "ran": make reports whether each leg exited 0, and a leg can
# exit 0 having gated nothing — the wired catalogue-curation guard skips its
# path-gate when the base ref is missing or stale (backlog
# `curation-guard-silent-base-skip`). The banner should not assert more than make
# can see.
# The CI-intentional branch keys on GITHUB_WORKFLOW, not GITHUB_ACTIONS alone:
# the reassuring line asserts a specific provenance ("build-check.yml decided the
# diff has nothing to scan"), and any process can export GITHUB_ACTIONS — `act`,
# a devcontainer image, a developer exercising the CI branch — which would hand
# them a claim that is not true of their run.
define gate_verdict
@if [ -n "$(SKIP_SAST)" ] && [ "$$GITHUB_WORKFLOW" = "build-check" ]; then \
	printf '\n%s: %s\n\n' '$(1)' 'complete for this diff — SAST/SCA skipped by build-check.yml because the diff touches nothing scannable.'; \
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

# Portable verify then repo-only policy gates.
# Step 1 (portable): lint, build, schema, self-host drift — via agentbundle catalogue verify.
# Step 2 (repo-only): build output validation, pre-pr aggregator, spec/traceability linters.
# Windows contributors: python tools/repo/build_gate_chain.py build-check
build-check:
	$(PYTHON) -m agentbundle catalogue verify --root .
	$(PYTHON) tools/repo/build_gate_chain.py build-check --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
	# SAST/SCA gate (ADR-0017) — runs last so the fast, offline drift/lint
	# checks above fail quickly before the slower, network-bound scanners.
	# SKIP_SAST short-circuits the SAST/SCA leg only (the drift + lint gates
	# above always run). build-check.yml sets it for PRs that touch no
	# SAST-relevant file (neither SAST_DIRS nor SAST_CONFIG) — the scanners
	# have nothing to scan, so the ~76k-LOC pass is pure waste there. Intent of
	# ADR-0017 is preserved: SAST stays chained into the required build-check
	# job (not a separate skippable workflow) and runs on every PR that changes
	# a SAST-relevant file.
	@if [ -n "$(SKIP_SAST)" ]; then \
		echo "build-check: SKIP_SAST set — skipping SAST/SCA gate (no SAST-relevant changes to scan)"; \
	else \
		$(MAKE) sast; \
	fi
	$(call gate_verdict,make build-check)

# SAST/SCA gate (ADR-0017). Three OSS scanners, installed from
# tools/requirements-sast.txt as CI-only dev tools — never shipped runtime
# deps. Chained into build-check above so the repo's single native gate runs it
# locally and in build-check.yml CI. Not added to tools/hooks/pre-pr.py or
# tools/pre-pr-catalogue.py (the Windows CI path runs the former; Semgrep has no
# Windows support). Linux/macOS only (Semgrep).
#
# These four Semgrep rules are excluded as duplicates of findings already
# dispositioned for Bandit, with no coverage loss (Bandit still flags new
# instances of each class):
#   - sha1   → the two sites are documented non-security digests annotated
#              `usedforsecurity=False`; Bandit B324 is satisfied, Semgrep's rule
#              can't read the kwarg. Bandit B324 still flags any new sha1.
#   - urllib → constant/operator-configured bases, line-precise `# nosec B310`.
#   - xml    → stdlib ElementTree (no external entities/DTDs), `# nosec B314`.
#   - chmod  → the one hit is a restrictive 0o700 (secure); Bandit B103 is
#              correctly silent on it and still flags genuinely-permissive modes.
# Excluding the duplicates avoids a second inline pragma system in shipped pack
# scripts.
SAST_DIRS := tools packs packages

# The SAST config / CI surface that *governs* the gate but lives outside
# SAST_DIRS. A diff touching any of these must run SAST so a change that
# loosens the gate (e.g. a wider bandit.yaml exclusion or SEMGREP_EXCLUDE) is
# validated by the gate it changes — build-check.yml's detection treats these
# as SAST-relevant. (tools/requirements-sast.txt and tools/semgrep/ are already
# covered by SAST_DIRS, so they need not be repeated here.)
SAST_CONFIG := bandit.yaml .snyk Makefile tools/audit-requirements.py .github/workflows/build-check.yml .github/workflows/codeql.yml

# Single source of truth for the SAST scan scope + config surface.
# build-check.yml's SAST-relevance detection reads these (`make -s
# print-sast-dirs` / `print-sast-config`) instead of hard-coding the lists, so
# the workflow predicate can't drift from them and silently skip the scan on a
# newly-added scannable dir or an edit to the gate's own config.
print-sast-dirs:
	@echo $(SAST_DIRS)

print-sast-config:
	@echo $(SAST_CONFIG)
SEMGREP_EXCLUDE := \
	--exclude-rule python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 \
	--exclude-rule python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected \
	--exclude-rule python.lang.security.use-defused-xml.use-defused-xml \
	--exclude-rule python.lang.security.audit.insecure-file-permissions.insecure-file-permissions

sast:
	@command -v bandit   >/dev/null 2>&1 || { echo "make sast: bandit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v pip-audit >/dev/null 2>&1 || { echo "make sast: pip-audit not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	@command -v semgrep   >/dev/null 2>&1 || { echo "make sast: semgrep not found — run: pip install -r tools/requirements-sast.txt" >&2; exit 1; }
	bandit -r $(SAST_DIRS) -c bandit.yaml --severity-level medium --confidence-level medium -q
	# The filter below stands in front of pip-audit, so a bug that drops a
	# *third-party* pin would take this gate green over an unaudited dependency.
	# Prove it before trusting it.
	python3 tools/test-audit-requirements.py
	# Audits every third-party pin, and skips this repo's own packages —
	# `dependencies = []` on both, so they contribute no tree, and resolving them
	# against the public index would couple a merge to a release that has not
	# happened yet. Every skip is printed. See tools/audit-requirements.py.
	python3 tools/audit-requirements.py tools/requirements.txt $$(find packs -name requirements.txt | sort)
	# semgrep>=1.166 hard-pins mcp==1.23.3 and click~=8.1.8, both carrying known CVEs
	# (mcp: CVE-2026-52870, CVE-2026-52869, CVE-2026-59950; click: PYSEC-2026-2132).
	# Attack surface is negligible: these packages are SAST-tooling transitive deps only,
	# never present in shipped artifacts (which declare dependencies=[]); exploiting the
	# mcp CVEs requires a Semgrep backend compromise + targeted CI attack; the click CVE
	# requires controlling semgrep's CLI args (i.e. write access to this repo).
	# Suppression is unblocked once semgrep ships mcp>=1.28.1 + click>=8.3.3 deps.
	# Full diagnosis and unblock condition: docs/backlog.md § semgrep-mcp-cve-allowlist.
	@echo "pip-audit -r tools/requirements-sast.txt (semgrep transitive-dep CVE allowlist applied)"
	@pip-audit -r tools/requirements-sast.txt \
		--ignore-vuln CVE-2026-52870 \
		--ignore-vuln CVE-2026-52869 \
		--ignore-vuln CVE-2026-59950 \
		--ignore-vuln PYSEC-2026-2132
	# Both shipped packages declare dependencies=[]; credbroker's optional
	# [crypto] extra is the only third-party code either can pull, so audit it
	# explicitly. Mirror packages/credbroker/pyproject.toml [crypto].
	@printf 'cryptography>=42\nargon2-cffi>=23\n' | pip-audit -r /dev/stdin
	semgrep --config p/python --config p/security-audit --config tools/semgrep/ --error --quiet --metrics off $(SEMGREP_EXCLUDE) $(SAST_DIRS)

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
	@bash tools/release-check.sh

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
	$(PYTHON) -m pytest packages/agentbundle/tests/ packages/agentbundle/agentbundle/build/tests/ -q
	$(PYTHON) -m pytest packages/credbroker/ -q
	$(PYTHON) -m pytest packs/core/tests/ packs/product-documentation/tests/ -q
	@n=$$($(PYTHON) -m pytest packs/desk-research/tests/ -q --collect-only | grep -c '::' || true); \
	 if [ "$$n" -lt 16 ]; then echo "packs/desk-research/tests/ collected $$n, expected >= 16" >&2; exit 1; fi
	$(PYTHON) -m pytest packs/desk-research/tests/ -q
	$(PYTHON) -m pytest tools/test_build_gate_chain.py tools/test_catalogue_tooling_rewire.py tools/test_catalogue_tooling_docs.py tools/test_validate_guides.py tools/test_build_site_routing.py tools/test_build_site_inventory.py tools/test_build_site_projection.py tools/test_build_site_sidebar.py -q
	$(PYTHON) -m pytest tools/test_workspace_status.py tools/test_workspace_status_cli.py -q

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
# writes into build/docs/. This matches .github/workflows/pages.yml.

.PHONY: site-sync site-build site-serve

site-sync:  ## Aggregate repo content into docs-site/src/content/docs/ (run before build/serve)
	$(PYTHON) tools/build-site.py

site-build: site-sync  ## Build full site → build/ (marketing) + build/docs/ (Starlight)
	npm run build --prefix web
	npm run build --prefix docs-site

site-serve: site-sync  ## Start Starlight dev server at http://localhost:4321
	npm run dev --prefix docs-site
