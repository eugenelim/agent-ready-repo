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

.PHONY: build build-self build-self-dry-run build-check build-scaffold validate clean

build:
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

build-self:
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

build-self-dry-run:
	$(PYTHON) -m agentbundle.build self --dry-run --packs-dir $(PACKS_DIR)

build-check:
	$(PYTHON) -m agentbundle.build check --packs-dir $(PACKS_DIR)

build-scaffold:
	@test -n "$(OUTPUT)" || (echo "make build-scaffold OUTPUT=<dir> required" >&2; exit 1)
	$(PYTHON) -m agentbundle.build scaffold --packs-dir $(PACKS_DIR) --output $(OUTPUT)

validate:
	$(PYTHON) -m agentbundle.build validate docs/contracts/adapter.toml

clean:
	rm -rf $(OUTPUT_DIR)
