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

.PHONY: build build-self build-self-dry-run build-check build-scaffold lint-packs pre-pr validate clean zipapp release-preflight

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
	$(PYTHON) tools/hooks/pre-pr.py

build-check: lint-packs build
	$(PYTHON) -m agentbundle.build check --packs-dir $(PACKS_DIR)
	$(PYTHON) tools/hooks/pre-pr.py
	# Doc-drift spec-metadata gate (RFC-0016 § Errata / ADR-0007). The lint is a
	# work-loop skill script that ships to adopters; the catalogue runs the
	# PROJECTED copy as its fail-closed CI gate (mirrors how pre-pr.py invokes
	# the projected loop-cohort.py). NOT wired into the projected pre-pr.py hook.
	$(PYTHON) .claude/skills/work-loop/scripts/test-lint-spec-status.py
	$(PYTHON) .claude/skills/work-loop/scripts/lint-spec-status.py

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
