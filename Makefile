# Build pipeline entrypoint — every target delegates to
# `python3 -m agentbundle.build`. Argument parsing happens inside the
# Python package; this file is the thin user surface spec § Boundaries
# § Always do calls for.

PYTHON ?= python3
PYTHONPATH := packages/agentbundle:$(PYTHONPATH)
PACKS_DIR ?= packs
OUTPUT_DIR ?= dist
PACK ?=
RECIPE ?=

export PYTHONPATH

.PHONY: build build-self build-self-dry-run build-check build-scaffold lint-packs pre-pr sast print-sast-dirs print-sast-config validate clean zipapp release-preflight

# Windows-portability gate. Refuses packs that ship symlinks or
# Windows-poisonous names under seeds/ or .apm/. Runs before every
# build target so a violation cannot be smuggled into dist/.
lint-packs:
	$(PYTHON) -m agentbundle.build lint-packs --packs-dir $(PACKS_DIR)

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

# Routes through the make-free repo-native chaining script
# (tools/build_gate_chain.py build-self) so the lint-packs → self step list
# lives in exactly one place and the Windows entry
# (`python tools/build_gate_chain.py build-self`) and this target cannot drift.
# The chain reaches `self` through `cmd_self`, so the tests/fixtures
# fixture-overwrite guard and the ALLOW_FIXTURE_PACKS override fire unchanged.
build-self:
ifeq ($(DRY_RUN),1)
ifeq ($(FORCE),1)
	$(PYTHON) tools/build_gate_chain.py build-self --dry-run --force --packs-dir $(PACKS_DIR)
else
	$(PYTHON) tools/build_gate_chain.py build-self --dry-run --packs-dir $(PACKS_DIR)
endif
else
ifeq ($(FORCE),1)
	$(PYTHON) tools/build_gate_chain.py build-self --force --packs-dir $(PACKS_DIR)
else
	$(PYTHON) tools/build_gate_chain.py build-self --packs-dir $(PACKS_DIR)
endif
endif

build-self-dry-run:
	$(PYTHON) tools/build_gate_chain.py build-self --dry-run --packs-dir $(PACKS_DIR)

# Projected-artifact + spec-state aggregator. Mirrors what
# docs.yml's per-layer jobs and the `Lifecycle hooks` job run in CI;
# chained into build-check below so `make build-check` is the single
# local gate that covers both lint surfaces (packs source via
# lint-packs, projected .claude/* artifacts via pre-pr). Safe to call
# directly when you want only the artifact checks without rebuilding.
pre-pr:
	$(PYTHON) tools/pre-pr-catalogue.py

# Routes the Windows-clean gate steps through the make-free repo-native script
# (tools/build_gate_chain.py build-check), which runs — in this order —
# lint-packs, build, check, pre-pr-catalogue, the spec-status self-test+lint
# pair (RFC-0016 § Errata / ADR-0007; runs the PROJECTED copy as its fail-closed
# gate), the brief-coverage self-test+lint pair (receive-brief; no-ops on
# this repo, fail-closed on a stale Spec map), and the traceability self-test+lint
# pair (work-loop; no-ops on this repo — no discovery chain — fail-closed on a
# dangling edge or cycle). The step list lives once, in the
# script, so this target and the Windows entry
# (`python tools/build_gate_chain.py build-check`) cannot drift. The script is
# repo-native (not an `agentbundle` subcommand) because it spawns repo-only
# scripts never shipped to adopters. The SAST leg below is NOT chained into the
# script — Semgrep has no Windows support and the leg is conditional — so it
# stays appended here, run last.
build-check:
	$(PYTHON) tools/build_gate_chain.py build-check --packs-dir $(PACKS_DIR) --output-dir $(OUTPUT_DIR)
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
SAST_CONFIG := bandit.yaml .snyk Makefile .github/workflows/build-check.yml .github/workflows/codeql.yml

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
	@for f in tools/requirements.txt $$(find packs -name requirements.txt | sort); do \
		echo "pip-audit -r $$f"; \
		pip-audit -r "$$f" || exit 1; \
	done
	# semgrep hard-pins mcp==1.23.3 (CVEs: 52870, 52869, 59950) and click~=8.1.8
	# (PYSEC-2026-2132) — unfixable until semgrep ships updated deps; tracked in backlog.
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
	@mkdir -p $(OUTPUT_DIR)
	@rm -rf $(OUTPUT_DIR)/_zipapp_stage
	@mkdir -p $(OUTPUT_DIR)/_zipapp_stage
	@cp -R packages/agentbundle/agentbundle $(OUTPUT_DIR)/_zipapp_stage/agentbundle
	@find $(OUTPUT_DIR)/_zipapp_stage -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find $(OUTPUT_DIR)/_zipapp_stage -name 'tests' -type d -exec rm -rf {} + 2>/dev/null || true
	$(PYTHON) -m zipapp $(OUTPUT_DIR)/_zipapp_stage \
		-o $(OUTPUT_DIR)/agentbundle.pyz \
		-m agentbundle.cli:main \
		-p '/usr/bin/env python3'
	@rm -rf $(OUTPUT_DIR)/_zipapp_stage
	@echo "built $(OUTPUT_DIR)/agentbundle.pyz"

release-preflight: lint-packs
	@bash tools/release-check.sh

# ── Site publishing ──────────────────────────────────────────────────────────
# Requires: pip install -r site/requirements.txt

.PHONY: site-sync site-build site-serve site-deploy

site-sync:  ## Aggregate repo content into site/docs/ (run before build/serve)
	$(PYTHON) tools/build-site.py

site-build: site-sync  ## Build static site → site/built/ (strict, matches CI)
	mkdocs build --config-file site/mkdocs.yml --strict

site-serve: site-sync  ## Start live-reload dev server at http://localhost:8000
	mkdocs serve --config-file site/mkdocs.yml

site-deploy: site-sync  ## Deploy to gh-pages branch (CI uses pages.yml instead)
	mkdocs gh-deploy --config-file site/mkdocs.yml --force
