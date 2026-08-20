# Falsifiability evidence — 2026-08-18

`python3 -m pytest tools/test_guide_authoring_standard.py tools/test_guide_typed_asides.py -q`
→ both files pass. `ruff` clean on both.

## What changed, and why the shape changed after review

The reported defect was `assert version == "0.37.1"` comparing the *current*
`pyproject.toml` version to a literal, so it failed on every release. Bumping it to
`0.37.2` would have been wrong: the surrounding assertions then require the 0.37.2
release notes to claim a change 0.37.2 did not make.

Review then established that wiring the whole file into a gate would be actively
harmful, so the file was **split**:

- `tools/test_guide_authoring_standard.py` — **gated.** The live invariants: the
  standard defines the fixed aside contract; the packaged scaffold copy is
  byte-identical; its manifest digest matches; `CLI_VERSION` matches `pyproject.toml`.
- `tools/test_guide_typed_asides.py` — **deliberately unwired.** The archival
  conversion record: a frozen 165-row blockquote ledger over 193 guide files, the
  release-handoff record, and the historical release-notes tripwire. Registered as
  `guide-blockquote-ledger-has-no-regenerator`.

The release-notes obligation on `README-pypi.md` naming the current version was
dropped from the gated set entirely — 12 of the last 25 version bumps did not touch
that file, so gating it would block that shape of PR with no documented step.
Registered as `readme-pypi-whats-new-unenforced`.

## Probes

Reproducible harness, committed here so the claim below is checkable rather than
asserted. It materialises only the files the target reads into a fixture and rebinds
**every** import-time path constant — rebinding `REPO_ROOT` alone is not enough,
because `AUTHORING_STANDARD` and `SCAFFOLD_ROOT` are derived at import time and would
still point at the live worktree.

```python
import importlib.util, pathlib, shutil, tempfile

NEEDED = [
    "guides/_shared/reference/catalogue-authoring-standards.md",
    "packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md",
    "packages/agentbundle/agentbundle/_data/catalogue-scaffold/manifest.json",
    "packages/agentbundle/pyproject.toml",
    "packages/agentbundle/agentbundle/version.py",
]

def load(path="tools/test_guide_authoring_standard.py"):
    spec = importlib.util.spec_from_file_location("t", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

real = load()

def fixture():
    root = pathlib.Path(tempfile.mkdtemp())
    for rel in NEEDED:
        dst = root / rel; dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real.REPO_ROOT / rel, dst)
    return root

def run(root):
    m = load()
    m.REPO_ROOT = root
    m.AUTHORING_STANDARD = root / "guides/_shared/reference/catalogue-authoring-standards.md"
    m.SCAFFOLD_ROOT = root / "packages/agentbundle/agentbundle/_data/catalogue-scaffold"
    m.test_authoring_standard_defines_the_fixed_aside_contract()
    m.test_packaged_scaffold_carries_the_standard_byte_identically()
    m.test_scaffold_manifest_records_the_standards_digest()
    m.test_cli_version_matches_the_packaged_version()
```

| Mutation | Result |
| --- | --- |
| baseline fixture, unmutated | passes (positive control) |
| `CLI_VERSION` drifts from `pyproject` | fails |
| projected scaffold copy edited | fails |
| **`manifest.json` digest edited, file bytes untouched** | fails |
| a `note`/`tip`/`caution`/`danger` row removed from the standard | fails |
| `"Use only those four types."` removed | fails |

The manifest-digest probe is the one review caught missing: the earlier
"scaffold copy edited" probe fails at the byte comparison first, so the digest
assertion never ran in a mutated state and had never been observed red.

For the archival file, mutations still recorded as detected: the `## [0.37.1]`
heading removed; the typed-asides wording deleted from that section; the wording
**moved** to another release's section (this is what proves the assertion is scoped,
not satisfied by presence anywhere); the callout-contract phrase removed from
`README-pypi.md`.
