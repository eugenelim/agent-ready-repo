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

.PHONY: build build-self build-self-dry-run build-check build-scaffold lint-packs pre-pr sast validate clean zipapp release-preflight

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

build-self: lint-packs
	@case "$(PACKS_DIR)" in \
		*tests/fixtures/*) \
			if [ -z "$$ALLOW_FIXTURE_PACKS" ]; then \
				echo "make build-self: refusing — PACKS_DIR points into tests/fixtures/; this would overwrite your working tree with fixture data. Set ALLOW_FIXTURE_PACKS=1 to override, or set PACKS_DIR=packs (when the F-dist migration lands)." >&2; \
				exit 1; \
			fi ;; \
	esac
ifeq ($(DRY_RUN),1)
ifeq ($(FORCE),1)
	$(PYTHON) -m agentbundle.build self --dry-run --force --packs-dir $(PACKS_DIR)
else
	$(PYTHON) -m agentbundle.build self --dry-run --packs-dir $(PACKS_DIR)
endif
else
ifeq ($(FORCE),1)
	$(PYTHON) -m agentbundle.build self --force --packs-dir $(PACKS_DIR)
else
	$(PYTHON) -m agentbundle.build self --packs-dir $(PACKS_DIR)
endif
endif

build-self-dry-run: lint-packs
	$(PYTHON) -m agentbundle.build self --dry-run --packs-dir $(PACKS_DIR)

# Projected-artifact + spec-state aggregator. Mirrors what
# docs.yml's per-layer jobs and the `Lifecycle hooks` job run in CI;
# chained into build-check below so `make build-check` is the single
# local gate that covers both lint surfaces (packs source via
# lint-packs, projected .claude/* artifacts via pre-pr). Safe to call
# directly when you want only the artifact checks without rebuilding.
pre-pr:
	$(PYTHON) tools/pre-pr-catalogue.py

build-check: lint-packs build
	$(PYTHON) -m agentbundle.build check --packs-dir $(PACKS_DIR)
	$(PYTHON) tools/pre-pr-catalogue.py
	# Doc-drift spec-metadata gate (RFC-0016 § Errata / ADR-0007). The lint is a
	# work-loop skill script that ships to adopters; the catalogue runs the
	# PROJECTED copy as its fail-closed CI gate (mirrors how pre-pr.py invokes
	# the projected loop-cohort.py). NOT wired into the projected pre-pr.py hook.
	$(PYTHON) .claude/skills/work-loop/scripts/test-lint-spec-status.py
	$(PYTHON) .claude/skills/work-loop/scripts/lint-spec-status.py
	# Brief-coverage auto-rollup gate (receive-brief skill script). Same shape
	# as the spec-status pair above: run the PROJECTED self-test then the lint.
	# No-ops on this repo (it ships no brief); fail-closed on a stale Spec map.
	$(PYTHON) .claude/skills/receive-brief/scripts/test-lint-brief-coverage.py
	$(PYTHON) .claude/skills/receive-brief/scripts/lint-brief-coverage.py
	# SAST/SCA gate (ADR-0017) — runs last so the fast, offline drift/lint
	# checks above fail quickly before the slower, network-bound scanners.
	$(MAKE) sast

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
	@for f in tools/requirements.txt tools/requirements-sast.txt $$(find packs -name requirements.txt | sort); do \
		echo "pip-audit -r $$f"; \
		pip-audit -r "$$f" || exit 1; \
	done
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
