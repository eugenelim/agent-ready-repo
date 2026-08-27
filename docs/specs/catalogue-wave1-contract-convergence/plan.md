# Plan: catalogue-wave1-contract-convergence

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)
- **Governed by:** RFC-0076 D1–D4

## Trio

**Goal:** Establish the contract authority model — sync four missing schemas from
`contracts/` to `agentbundle/_data/`, add a byte-parity CI gate, create the portable
authoring-standards hub and add it to the init scaffold, fix stale fork language across
README/docs-site, and add normative pointers in `packs/AGENTS.md` and `packs/README.md`.
The result is a cold reader on any of the five audience journeys finding a consistent,
authoritative path to machine contracts and the authoring hub.

**Assumptions:**
- `contracts/guide.schema.json`, `contracts/skill.schema.json`,
  `contracts/skill-manifest.schema.json`, and `contracts/target-vocab.toml` exist at HEAD
  and are valid. *(Verified: all four present.)*
- The current agentbundle version is `0.26.0`; this wave bumps it to `0.26.1`.
- `tools/catalogue/sync_authoring_scaffold.py --write` runs `_write_manifest()` automatically
  — no separate manifest.json update step is needed.
- The new parity check tool wires into `build_gate_chain.py` as a `_script_step` in the
  `build_check()` chain — no Makefile change is needed.
- `guides/_shared/how-to/create-a-catalogue.md` is the one place that shows the scaffold
  directory listing inline; no other guide duplicates it.

**Declined patterns:**
- Generating or contract-testing the existing prose schema map in `packs/AGENTS.md` — that is
  Wave 3 work; this wave adds only the normative pointer.
- Adding `profiles/AGENTS.md` normative pointer — permitted if line budget allows, but not in
  scope; deferred to Wave 1 follow-on.
- Citing RFC/ADR/spec paths in the shipped `catalogue-authoring-standards.md` guide.
- Adding scaffold-init tests beyond the scaffold-listing update — out of scope.

---

## Design (LLD)

### Schema sync (AC14–AC17)

Copy four files verbatim from `contracts/` to `packages/agentbundle/agentbundle/_data/`:

| Source | Destination |
|--------|-------------|
| `contracts/guide.schema.json` | `agentbundle/_data/guide.schema.json` |
| `contracts/skill.schema.json` | `agentbundle/_data/skill.schema.json` |
| `contracts/skill-manifest.schema.json` | `agentbundle/_data/skill-manifest.schema.json` |
| `contracts/target-vocab.toml` | `agentbundle/_data/target-vocab.toml` |

No schema content changes — byte-identical copies only.

### Parity check tool (AC19)

`tools/catalogue/check_contract_parity.py` — pure-stdlib Python, **bare invocation** (no
`--check`/`--write` modes — the tool only checks, never writes):

- Walk `contracts/` for every `*.schema.json` and `*.toml` file (not README.md or subdirs).
- For each file in `contracts/`, check if `agentbundle/_data/<filename>` exists; if absent
  and not in the allowlist (`install-defaults.toml`, `install-marker.py`), record as failure.
- For each file present in both, compare bytes; record as failure if they differ.
- Exit 0 only when all contracts/ files are synced and byte-identical.
- Exit 1 on any failure; print per-file details to stderr.
- Prints `check_contract_parity: ok — N shared file(s) byte-identical.` on success.

After Wave 1 sync, 11 files will be in contracts/; all 11 must be present in `_data/`.
The gate will enforce both presence and parity on all 11 going forward.

### Build-check wiring (AC20)

Add one `_script_step` to `build_gate_chain.py` `build_check()` — after `pre-pr-catalogue`,
before `test-lint-spec-status`. The tool is invoked bare (no flag):

```python
_script_step(
    "check-contract-parity",
    "tools", "catalogue", "check_contract_parity.py",
),
```

### Authoring hub (AC7–AC12)

New file `guides/_shared/reference/catalogue-authoring-standards.md` with:

- Frontmatter: `title`, `summary`, `pack: _shared`, `kind: reference`, `status: stable`
- Preamble stating that `contracts/` is normative and these guides explain how to use them
- Routing table linking to: pack manifest (`contracts/pack.schema.json`), pack README standard,
  pack layout, skill frontmatter (`contracts/skill.schema.json`), skill body and progressive
  disclosure, profile format (`contracts/profile.schema.json`), lint and verify commands,
  CI contract, package and publication guidance
- Placeholder section "Optional pack integrations" (Wave 2 — not yet available)
- Placeholder section "Journey format" (Wave 4 — not yet available)
- No host CI workflow requirements, Make target requirements, or RFC/ADR/spec citations
- All links resolve from within the scaffold

### Scaffold sync extension (AC21–AC22)

Add one pair to `_SYNC_PAIRS` in `sync_authoring_scaffold.py`:

```python
(
    _REPO_ROOT / "guides" / "_shared" / "reference" / "catalogue-authoring-standards.md",
    "guides/_shared/reference/catalogue-authoring-standards.md",
),
```

Then run `python3 tools/catalogue/sync_authoring_scaffold.py --write` — this copies the hub
to `_data/catalogue-scaffold/guides/_shared/reference/` and regenerates `manifest.json`.

### Scaffold listing update (AC24)

In `guides/_shared/how-to/create-a-catalogue.md`, the code block at lines 30–54 shows the
scaffold directory tree. Add the hub file:

```diff
     guides/
       _shared/
         reference/
           catalogue-ci-contract.md
+          catalogue-authoring-standards.md
```

### Version bump (AC18)

Two files, both bumped to `0.26.1` in lockstep:
- `packages/agentbundle/pyproject.toml`: `version = "0.26.0"` → `version = "0.26.1"`
- `packages/agentbundle/agentbundle/version.py`: `CLI_VERSION = "0.26.0"` → `CLI_VERSION = "0.26.1"`

Commit message for any `agentbundle/_data/` change must include:
```
Engine-Change-RFC: RFC-0076
```

### Changelog (AC18 support)

Add to `docs/product/changelog.md` `[Unreleased]` `### Added`:

```
- **`agentbundle` 0.26.1**: bundles `guide.schema.json`, `skill.schema.json`,
  `skill-manifest.schema.json`, and `target-vocab.toml` from the canonical
  `contracts/` source, enabling offline skill and guide validation. Adds
  `guides/_shared/reference/catalogue-authoring-standards.md` to the init scaffold.
```

---

## Tasks

### Task 1 — Phase A: Documentation and stale fixes

**Depends on:** none (pre-RFC safe changes; RFC-0076 now Accepted)

**Files to change:**

1. **`contracts/README.md`** — replace the Files table with a complete 11-row table; add
   RFC-0076 D1 authority model note below the table. ACs 1–2.

2. **`README.md` line 132** — replace `"Adopt the catalogue as-is, or fork it as your own.
   Write your conventions and review standards into \`core\`..."` with text describing
   `agentbundle catalogue init` as the entry point. Change the
   `[How to build your org's catalogue →]` link target from `docs/architecture/catalogue.md`
   to `guides/_shared/how-to/create-a-catalogue.md`. AC3.

3. **`docs-site/src/content/docs/index.mdx` line 78** — replace `"Adopt the catalogue
   as-is, or fork it as your own org's catalogue."` with a sentence pointing to
   `agentbundle catalogue init`. AC4.

4. **`packs/AGENTS.md`** — add normative pointer in the `## pack.toml schema map` section
   (or the nearest heading): `"The machine source of truth for pack.toml format is
   \`contracts/pack.schema.json\`."` File must remain ≤ 150 lines. AC6.

**Verify:** grep absence of "fork it as your own" in README.md and index.mdx; grep presence
of normative pointer in packs/AGENTS.md; grep all 11 contract names in contracts/README.md.

---

### Task 2 — Phase B: Authoring hub

**Depends on:** none

**Files to change:**

1. **NEW `guides/_shared/reference/catalogue-authoring-standards.md`** — hub file per LLD.
   ACs 7–12.

2. **`guides/_shared/reference/README.md`** — add entry:
   `- [\`catalogue-authoring-standards.md\`](catalogue-authoring-standards.md) — routing table
   for every catalogue authoring standard: packs, skills, profiles, CI, package, and
   publication.` AC13.

3. **`packs/README.md` § "Further reading"** — add bullet:
   `- \`guides/_shared/reference/catalogue-authoring-standards.md\` — unified authoring
   standards hub: pack and skill schemas, profile format, lint and verify commands, CI
   contract, packaging.` AC5.

**Verify:** file exists; frontmatter valid; routing table has all required destinations;
placeholder sections present; no RFC/ADR/spec citations; packs/README has hub link.

---

### Task 3 — Phase C: Schema sync and parity gate

**Depends on:** none

**Files to change:**

1. **Copy schemas** — byte-identical copies to `packages/agentbundle/agentbundle/_data/`:
   - `contracts/guide.schema.json` → `_data/guide.schema.json`
   - `contracts/skill.schema.json` → `_data/skill.schema.json`
   - `contracts/skill-manifest.schema.json` → `_data/skill-manifest.schema.json`
   - `contracts/target-vocab.toml` → `_data/target-vocab.toml`

   ACs 14–17. Verify byte-parity immediately with `diff contracts/X _data/X`.

2. **NEW `tools/catalogue/check_contract_parity.py`** — per LLD. AC19.

3. **`tools/repo/build_gate_chain.py`** — add `_script_step("check-contract-parity", ...)`
   in `build_check()` after the `pre-pr-catalogue` step. AC20.

4. **`packages/agentbundle/pyproject.toml`** — bump `version = "0.26.1"`. AC18.

5. **`packages/agentbundle/agentbundle/version.py`** — bump `CLI_VERSION = "0.26.1"`. AC18.

6. **`docs/product/changelog.md`** — add Unreleased entry per LLD. AC18 support.

7. **`packages/agentbundle/README-pypi.md`** — note that the wheel now bundles `guide.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`, and `target-vocab.toml` for offline validation. AC29.

**Commit message must include:** `Engine-Change-RFC: RFC-0076`

**Verify:** `python3 tools/catalogue/check_contract_parity.py` exits 0; four files exist in
`_data/`; diff each pair confirms byte-identical; both pyproject.toml and version.py show 0.26.1.

---

### Task 4 — Phase D: Scaffold inclusion

**Depends on:** Task 2 (hub file must exist at source path before sync)

**Files to change:**

1. **`tools/catalogue/sync_authoring_scaffold.py`** — add the new pair to `_SYNC_PAIRS` per
   LLD. Then run `python3 tools/catalogue/sync_authoring_scaffold.py --write` — this copies
   the hub to the scaffold and regenerates `manifest.json`. ACs 21–23.

2. **`guides/_shared/how-to/create-a-catalogue.md`** — update the scaffold directory listing
   code block (lines ~30–54) to include `catalogue-authoring-standards.md` under
   `guides/_shared/reference/`. AC24.

**Commit message must include:** `Engine-Change-RFC: RFC-0076` (this task writes to `_data/`
via `sync_authoring_scaffold.py --write`).

**Verify:** scaffold file exists at
`_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`;
`python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0; `manifest.json`
contains the new file's entry.

---

### Task 5 — Regression verification

**Depends on:** Tasks 1, 2, 3, 4

1. Run `python3 -m pytest packages/agentbundle/tests/ -q` — exits 0. AC26.
2. Run `SKIP_SAST=1 make build-check` — exits 0. AC25.
3. Verify `wc -l packs/AGENTS.md` ≤ 150. AC27.
4. Verify `wc -l AGENTS.md` ≤ 250 (root CLAUDE.md symlink). AC28.
5. Verify `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0.
6. Verify `python3 tools/catalogue/check_contract_parity.py` exits 0.

---

## Dependency graph

```
Task 1 (Phase A doc fixes)  ──┐
Task 2 (Phase B hub)        ──┤── Task 4 (Phase D scaffold) ──┐
Task 3 (Phase C schema sync)──┘                               └── Task 5 (regression)
```

Tasks 1, 2, and 3 are independent and can start in parallel. Task 4 must follow Task 2.
Task 5 must follow all four.

---

## Commit checklist

- [ ] `contracts/README.md` lists all 11 contracts with RFC-0076 D1 authority note
- [ ] `README.md` fork language removed; `agentbundle catalogue init` present; link target = `guides/_shared/how-to/create-a-catalogue.md`
- [ ] `docs-site/index.mdx` fork language removed
- [ ] `packs/AGENTS.md` normative pointer present; file ≤ 150 lines
- [ ] `guides/_shared/reference/catalogue-authoring-standards.md` created; contract refs are text citations not hyperlinks
- [ ] `guides/_shared/reference/README.md` updated
- [ ] `packs/README.md` Further reading has hub link
- [ ] Four schemas copied to `_data/`; byte-parity confirmed
- [ ] `tools/catalogue/check_contract_parity.py` created; bare invocation exits 0
- [ ] `build_gate_chain.py` has `check-contract-parity` step (no --check flag)
- [ ] `pyproject.toml` version = "0.26.1"
- [ ] `agentbundle/version.py` CLI_VERSION = "0.26.1"
- [ ] `changelog.md` [Unreleased] entry added
- [ ] `README-pypi.md` updated with bundled-schema note
- [ ] `sync_authoring_scaffold.py` `_SYNC_PAIRS` extended; `--write` run
- [ ] `manifest.json` updated (by sync --write)
- [ ] `create-a-catalogue.md` scaffold listing updated
- [ ] `SKIP_SAST=1 make build-check` exits 0
- [ ] `pytest packages/agentbundle/tests/ -q` exits 0
- [ ] Engine-Change-RFC footer on commit(s) touching `_data/`
