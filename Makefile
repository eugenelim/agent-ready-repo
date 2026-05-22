# Build pipeline entrypoint — every target delegates to
# `python3 -m agentbundle.build`. Argument parsing happens inside the
# Python package; this file is the thin user surface spec § Boundaries
# § Always do calls for.

PYTHON ?= python3
PYTHONPATH := packages/agentbundle:$(PYTHONPATH)
PACKS_DIR ?= packages/agentbundle/agentbundle/build/tests/fixtures/packs
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
ifeq ($(DRY_RUN),1)
	$(PYTHON) -m agentbundle.build self --dry-run --packs-dir $(PACKS_DIR)
else
	$(PYTHON) -m agentbundle.build self --packs-dir $(PACKS_DIR)
endif

build-self-dry-run:
	$(PYTHON) -m agentbundle.build self --dry-run --packs-dir $(PACKS_DIR)

build-check:
	$(PYTHON) -m agentbundle.build check --packs-dir $(PACKS_DIR)

build-scaffold:
	@test -n "$(OUTPUT)" || (echo "make build-scaffold OUTPUT=<dir> required" >&2; exit 1)
	$(PYTHON) -m agentbundle.build scaffold --packs-dir $(PACKS_DIR) --output $(OUTPUT)

validate:
	$(PYTHON) -m agentbundle.build validate docs/specs/adapter-contract/contract.toml

clean:
	rm -rf $(OUTPUT_DIR)
