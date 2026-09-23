# Spec: catalogue-wave1-contract-convergence

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D1–D4](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Contract:** `contracts/pack.schema.json` (read-only in this wave), `contracts/README.md` (updated), `contracts/catalogue-index.schema.json` (not yet, Wave 4)
- **Shape:** docs + engine change + stale fixes

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural: new guide in scaffold = engine change; public interface:
contracts/README is a public-facing document; affects five audience journeys)

## Objective

Six of eight audience navigation targets fail today. This wave addresses the
foundations: the contract authority model is documented, four missing schemas are
synced from `contracts/` to `agentbundle/_data/`, `contracts/README.md` lists all
eleven active contracts, a portable authoring-standards hub exists at
`guides/_shared/reference/catalogue-authoring-standards.md` (and in the init scaffold),
and stale documentation is repaired — the "fork" language in `README.md` and
`docs-site/src/content/docs/index.mdx`, the incomplete path reference in `packs/AGENTS.md`,
and the contracts-coverage gap in `packs/AGENTS.md`.

After this wave, a cold reader on any of the five audience journeys finds a consistent,
authoritative path to the machine contracts and the portable authoring hub. Wave 2 adds
the optional integration convention; Wave 3 adds the bundled-contract inspection CLI.

## Boundaries

### Always do

- Verify schema byte-parity between `contracts/<f>.json` and `agentbundle/_data/<f>` for every newly synced file before committing.
- Verify `tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after every scaffold change.
- Keep packs/AGENTS.md ≤ 150 lines and AGENTS.local.md ≤ 250 lines.
- Add `Engine-Change-RFC: RFC-0076` to every commit message that changes `agentbundle/_data/`.
- Keep the authoring hub free of host CI workflow requirements, Make target requirements, and internal governance citations (RFC/ADR/spec paths).

### Ask first

- Adding any schema file to `contracts/` that is not listed in D3's target table.
- Changing any existing schema content (this wave syncs only; schema content changes are gated on Wave 2 spec for pack.schema.json and Wave 4 for catalogue-index.schema.json).
- Changing packs/AGENTS.md beyond the normative pointer and line-count fix.

### Never do

- Edit the projected outputs under `.claude-code/`, `.cursor/`, `.kiro/`, etc. directly — edit `.apm/` sources then run `self-host`.
- Add host-specific CI workflow YAML to the scaffold.
- Cite RFC, ADR, or spec paths in the shipped guide content (`catalogue-authoring-standards.md`).
- Exceed the AGENTS.md line caps (packs/AGENTS.md ≤ 150, root AGENTS.md ≤ 250).

## Testing Strategy

- **contracts/README completeness (AC1–AC2):** visual/manual QA — grep confirms all 11 contract filenames appear in the README table; authority statement for RFC-0076 D1 present.
- **Stale fix — README.md (AC3):** grep confirms "fork it as your own" absent; `agentbundle catalogue init` present; redirect target `guides/_shared/how-to/create-a-catalogue.md` resolves.
- **Stale fix — docs-site/index.mdx (AC4):** grep confirms "fork it as your own" absent from the file.
- **packs/README.md hub link (AC5):** grep confirms link to `catalogue-authoring-standards.md` present in "Further reading".
- **packs/AGENTS.md normative pointer (AC6):** grep confirms normative pointer phrase present; `wc -l` ≤ 150.
- **Hub frontmatter and preamble (AC7–AC8):** visual/manual QA — frontmatter keys match spec; preamble exact-phrase present.
- **Hub routing table and placeholders (AC9–AC11):** visual/manual QA — all required routing destinations listed; placeholder sections present and clearly marked "not yet available".
- **Hub link integrity (AC12):** visual/manual — grep confirms no RFC/ADR/spec path citations; guide-to-guide links verified resolvable within the scaffold; contract references are non-hyperlink path citations, not Markdown links to source-repo paths.
- **guides/reference/README entry (AC13):** grep confirms new hub entry present.
- **Schema sync, byte-parity (AC14–AC17):** TDD — Python tests in `packages/agentbundle/tests/` assert `contracts/<schema>` bytes == `agentbundle/_data/<schema>` bytes for each of the four newly synced files.
- **Version bump (AC18):** grep confirms `pyproject.toml` version = "0.26.1"; grep confirms `agentbundle/version.py` `CLI_VERSION` = "0.26.1"; git log confirms `Engine-Change-RFC: RFC-0076` in the relevant commit.
- **Parity gate tool (AC19):** bare invocation `python3 tools/catalogue/check_contract_parity.py` exits 0 on clean repo; exits 1 when any `contracts/` schema file lacks an `agentbundle/_data/` counterpart (except the allowlisted `_data/`-only files); exits 1 when any shared file's bytes differ.
- **Build-check wiring (AC20):** `SKIP_SAST=1 make build-check` exits 0 and the chain output includes the "check-contract-parity" step label.
- **Scaffold file present (AC21):** `find` confirms file exists at `_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`.
- **Scaffold sync check (AC22):** `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0.
- **Manifest updated (AC23):** grep confirms the new hub file path key present in `_data/catalogue-scaffold/manifest.json`.
- **create-a-catalogue.md listing (AC24):** grep confirms `catalogue-authoring-standards.md` appears in the scaffold code block.
- **PyPI readme (AC29):** `README-pypi.md` mentions the four bundled schemas or the offline validation capability.
- **Regression build-check (AC25):** `SKIP_SAST=1 make build-check` exits 0.
- **Regression pytest (AC26):** `python3 -m pytest packages/agentbundle/tests/ -q` exits 0.
- **Line count (AC27–AC28):** `wc -l packs/AGENTS.md` ≤ 150; `wc -l AGENTS.md` ≤ 250.

## Acceptance Criteria

### Phase A — Documentation and stale fixes (pre-RFC safe; no engine change)

**contracts/README completeness (D3)**

- [x] AC1: `contracts/README.md` has a Files table listing all eleven contracts: `adapter.toml`, `adapter.schema.json`, `pack.schema.json`, `plugin-manifest.schema.json`, `plugin-manifest.derived.schema.json`, `catalogue.schema.json`, `profile.schema.json`, `guide.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`, `target-vocab.toml`. Each row has a What-it-pins description and a Governing-spec-or-RFC column.
- [x] AC2: `contracts/README.md` notes RFC-0076 D1 as the authority model source and states that `contracts/` is the canonical authored source for all listed contracts.

**Stale fixes**

- [x] AC3: `README.md` § "The catalogue" no longer contains the phrase "fork it as your own". The paragraph is updated to describe `agentbundle catalogue init` as the current entry point. The `docs/architecture/catalogue.md` link is redirected to `guides/_shared/how-to/create-a-catalogue.md`.
- [x] AC4: `docs-site/src/content/docs/index.mdx` § "A foundation to build on" no longer contains "fork it as your own". The text is updated to describe `agentbundle catalogue init` as the entry point.
- [x] AC5: `packs/README.md` "Further reading" section contains a link to `guides/_shared/reference/catalogue-authoring-standards.md` (the hub).
- [x] AC6: `packs/AGENTS.md` § "Authoring or editing a skill" or § "pack.toml schema map" contains an explicit normative statement: "The machine source of truth for pack.toml format is `contracts/pack.schema.json`." The file remains ≤ 150 lines.

### Phase B — Authoring hub (D4)

- [x] AC7: `guides/_shared/reference/catalogue-authoring-standards.md` exists with frontmatter `title: "Catalogue authoring standards"`, `summary: "..."`, `pack: _shared`, `kind: reference`, `status: stable`.
- [x] AC8: The hub has a preamble stating "Machine contracts in `contracts/` are normative. These guides explain how to use them."
- [x] AC9: The hub has a numbered or linked routing table that covers at minimum: catalogue format, pack manifest (citing `contracts/pack.schema.json` as a non-hyperlink path), pack README standard, pack layout, skill frontmatter (citing `contracts/skill.schema.json`), skill body and progressive-disclosure guidance, profile format (citing `contracts/profile.schema.json`), lint and verify commands, CI contract, package and publication guidance. Contract citations are plain-text path references, not Markdown hyperlinks (the `contracts/` directory does not exist in the scaffold).
- [x] AC10: The hub contains a placeholder section "Optional pack integrations" (to be filled by Wave 2) that is clearly marked as not yet available.
- [x] AC11: The hub contains a placeholder section "Journey format" (to be filled by Wave 4) that is clearly marked as not yet available.
- [x] AC12: The hub contains no host CI workflow requirements, Make target requirements, or internal governance citations (RFC/ADR/spec paths). Every guide-to-guide link in the hub resolves from within the scaffold. Contract references (`contracts/*.schema.json`, `contracts/*.toml`) are plain-text path citations, not Markdown hyperlinks — the `contracts/` directory is not in the scaffold.
- [x] AC13: `guides/_shared/reference/README.md` has an entry for the new hub.

### Phase C — Schema sync (D2)

- [x] AC14: `packages/agentbundle/agentbundle/_data/guide.schema.json` exists and is byte-identical to `contracts/guide.schema.json`.
- [x] AC15: `packages/agentbundle/agentbundle/_data/skill.schema.json` exists and is byte-identical to `contracts/skill.schema.json`.
- [x] AC16: `packages/agentbundle/agentbundle/_data/skill-manifest.schema.json` exists and is byte-identical to `contracts/skill-manifest.schema.json`.
- [x] AC17: `packages/agentbundle/agentbundle/_data/target-vocab.toml` exists and is byte-identical to `contracts/target-vocab.toml`.

> **Note (discovered fix):** A pre-existing drift in `packages/agentbundle/agentbundle/_data/profile.schema.json` was discovered during D2 implementation — the `contracts/` version had richer annotations (`$schema`, `$id`, `title`, field descriptions) absent from `_data/`. No semantic change. Synced `contracts/` → `_data/` per the D1 authority model direction and recorded in changelog (0.26.1 Unreleased).

- [x] AC18: `packages/agentbundle/pyproject.toml` version is bumped (patch) to `0.26.1`. `packages/agentbundle/agentbundle/version.py` `CLI_VERSION` is set to `"0.26.1"` in lockstep. Commit message contains `Engine-Change-RFC: RFC-0076`.
- [x] AC19: `tools/catalogue/check_contract_parity.py` is a pure-stdlib Python tool invoked without flags. It exits 0 when every `*.schema.json` and `*.toml` contract file in `contracts/` has a byte-identical counterpart in `agentbundle/_data/`. It exits 1 when (a) any `contracts/` contract file is absent from `agentbundle/_data/`, or (b) any shared file's bytes differ. This detects both drift and forgotten sync. (`install-defaults.toml` and `install-marker.py` are not in `contracts/`, so no allowlist is needed.)
- [x] AC20: `tools/repo/build_gate_chain.py` `build_check()` includes a `_script_step("check-contract-parity", "tools", "catalogue", "check_contract_parity.py")` step. `SKIP_SAST=1 make build-check` runs the step and fails the chain if `check_contract_parity.py` exits non-zero.

### Phase D — Scaffold inclusion (D4 engine change)

- [x] AC21: `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md` exists and matches the content of `guides/_shared/reference/catalogue-authoring-standards.md` after scaffold sync.
- [x] AC22: `tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after the scaffold sync.
- [x] AC23: The scaffold manifest (`packages/agentbundle/agentbundle/_data/catalogue-scaffold/manifest.json`) is updated to include the new hub file in its file list.
- [x] AC24: The `create-a-catalogue.md` how-to guide's scaffold directory listing (the inline code block showing `my-catalogue/guides/...`) is updated to include `guides/_shared/reference/catalogue-authoring-standards.md`.

### PyPI release impact

- [x] AC29: `packages/agentbundle/README-pypi.md` is updated to note that the wheel now bundles `guide.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`, and `target-vocab.toml` for offline validation.

### Regression

- [x] AC25: `SKIP_SAST=1 make build-check` exits 0.
- [x] AC26: `python3 -m pytest packages/agentbundle/tests/ -q` exits 0.
- [x] AC27: packs/AGENTS.md ≤ 150 lines (CI enforces; verify after any edit).
- [x] AC28: root AGENTS.md ≤ 250 lines (CI enforces; verify after any edit).

## Assumptions

- Technical: `contracts/guide.schema.json`, `contracts/skill.schema.json`, `contracts/skill-manifest.schema.json`, and `contracts/target-vocab.toml` exist at HEAD and are valid (verified: all four are present in contracts/).
- Technical: `tools/catalogue/sync_authoring_scaffold.py` can be extended to cover the new hub file, or the hub file is already in the scaffold sync scope (verify before implementing).
- Technical: `make build-check` is the CI gate and can invoke a new Python tool added to `tools/catalogue/`.
- Deferred: Guide links in the hub that point to Wave 2 (optional integrations) and Wave 4 (journey format) content use placeholder text only. Full routing added in those waves' specs.
- Deferred: `profiles/AGENTS.md` normative pointer (profile schema → `contracts/profile.schema.json`) is not in scope here. Tracked in `workspace.toml [backlog].open` as slug `profiles-agents-normative-pointer`; unblocked after this wave ships.
