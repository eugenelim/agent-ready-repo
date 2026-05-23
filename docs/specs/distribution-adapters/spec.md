# Spec: distribution-adapters

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md), [RFC-0002](../../rfc/0002-self-hosting.md)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Stand up the in-repo distribution machinery RFC-0001 commits to: a canonical
per-IDE **adapter contract** (TOML + JSON-Schema validator), a stdlib-only
Python **build pipeline** that consumes it, and four **reference adapters**
(Claude Code, Kiro, Copilot, Codex) that together project each of the four
packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`)
into ecosystem-native distribution artifacts. The user is the contributor or
adopter who runs `make build`: a single command must turn the source tree
under `packs/` into one installable APM package per pack at `dist/apm/<pack>/`
and one installable Claude Code plugin per pack at
`dist/claude-plugins/<pack>/`, plus a shared
`dist/claude-plugins/marketplace.json` aggregating every per-pack plugin
entry. The same pipeline, invoked as `make build --check`, must run in
dry-run mode against this repo's own self-host projection and exit non-zero
on any drift between source and on-disk projection — the gate RFC-0002 wires
into CI. Success is shaped by RFC-0001's three Success criteria: contract
validates against its own schema for all four reference targets; the build
pipeline produces installable artifacts on a clean checkout; the self-host
diff is a no-op.

This spec also pins:

- The **shape** of two schemas the rest of the catalogue reads: `pack.toml`
  (per-pack metadata, dependencies, adaptation manifest, and `seeds/` list)
  and `.claude-plugin/plugin.json` (the per-pack Claude Code plugin
  manifest). RFC-0002's self-host spec and RFC-0003's CLI spec reference
  these definitions — they are not redefined elsewhere.
- The **Tier-1/2/3 contract** (which files the bundle owns, which it shares
  with adopter edits, which it never touches) and the
  `.agent-ready-state.toml` schema and `.upstream.<ext>` companion semantics
  that operationalise it. **This spec pins the schemas only; the
  lifecycle behaviour** (companion-file creation/removal,
  `.agent-ready-state.toml` writes, Tier-2 detection on initial install)
  **is implemented by sibling specs** — `self-hosting` for `make build
  --self` and RFC-0003's CLI for install/update flows. No task in this
  plan implements Tier-2 behaviour; it pins the contract the consumers
  obey.
- The enumerated **recipe set** — the six recipe types RFC-0001 and RFC-0002
  jointly define. Any seventh recipe type requires an RFC or spec amendment.

## Projection modes (defined)

The seven projection modes RFC-0001 enumerates and this spec ships in
`adapter.toml`. Sibling specs reading this spec for projection-mode
semantics should find them here; AC #2's enum is defined-by-reference
to this list.

- **`direct-directory`** — copy a source directory tree byte-for-byte to
  the projected path. Default `on-conflict`: `prompt-then-preserve`.
- **`direct-file`** — copy a single source file byte-for-byte to the
  projected path. Default `on-conflict`: `prompt-then-preserve`.
- **`merge-json`** — deep-merge the source's JSON payload into a managed
  key of a target JSON file. Other keys are untouched. Default
  `on-conflict`: `merge-managed-key-only`.
- **`instruction-file`** — wrap source content as a per-file instruction
  document with adapter-declared frontmatter (e.g. Copilot's `applyTo`).
  Default `on-conflict`: `prompt-then-overwrite`.
- **`managed-block-inline`** — write the source content between
  delimiter strings inside a target text file; content outside the
  delimiters is preserved. Default `on-conflict`: `preserve-outside-block`.
- **`degraded-info-log`** — emit an `[info]` line on stderr at build
  time, write no file. Used when an adapter lacks a schema for a
  primitive (RFC-0001 Unresolved Q1, Kiro hook wiring).
- **`dropped`** — explicit no-op; no output file, no warning. The
  contract carries the `dropped` rule so the missing pair is intentional,
  not an oversight.

## Default-recipe behaviour

Plain `make build` (no flags) invokes only the three RFC-0001 recipes —
`per-pack-claude-plugin`, `per-pack-apm-package`, and `marketplace` —
producing `dist/` output without touching the working tree. `make build
--self` (and `--check`, its dry-run sibling) project the four reference
adapters directly into the working tree per the spec § Tier model
contract. The RFC-0002 self-host recipes (`per-pack-overlay`,
`composite-agents-md`, `composite-marketplace`) ship as recipe metadata
+ expansion-shape API in this spec; their **on-disk writers** are
implemented by sibling spec `self-hosting`. The split keeps `make
build` deterministic and side-effect-free against the working tree —
the property that lets CI run it without pre-cleanup.

## Tier model and adopter-edit semantics

The Tier model is the bundle-format contract for "what a file's owner is at
any moment." All adapters, recipes, the CLI, and `adapt-to-project` consume
it identically. RFC-0001 § Catalogue boundaries and update model is the
upstream source.

- **Tier-1 — bundle-owned, projected.** Files at adapter-contract paths
  that the adopter does not edit. The CLI install, `make build`, and the
  adapt step are free to (re)write these. Examples: `.claude/skills/<pack>/`,
  generated `dist/` content, `.kiro/skills/<name>/`. Tier-1 is the default
  for any output an adapter projects from a primitive.
- **Tier-2 — bundle-origin, adopter-edited.** Files that the bundle
  originally seeded but the adopter has since modified. Detection: the
  per-file SHA-256 in `.agent-ready-state.toml` no longer matches the
  bundle's last-installed content. Writes never clobber: an update drops a
  companion file at `<filename>.upstream.<ext>` (e.g. `AGENTS.md` stays;
  `AGENTS.upstream.md` is dropped next to it). `adapt-to-project` walks
  these companions, prompts the adopter per file, and removes the
  `.upstream.<ext>` once resolved.
- **Tier-3 — adopter-owned, untouched.** Files outside adapter-contract
  paths. The bundle never writes these; the adapt step may propose changes
  but only with per-file approval.

**`.upstream.<ext>` companion semantics.**
- *Filename rule:* `<stem>.upstream.<ext>` for a file at `<stem>.<ext>`
  (e.g. `AGENTS.md` → `AGENTS.upstream.md`; `docs/CHARTER.md` →
  `docs/CHARTER.upstream.md`). For files without an extension, the rule is
  `<stem>.upstream` with no extension.
- *Lifecycle:* created by `make build` (in `--self` mode) or by a CLI
  install/update when the target is detected as Tier-2; removed by
  `adapt-to-project` after the adopter resolves the conflict (keep, merge,
  or overwrite). Companions are tracked in `.agent-ready-state.toml`.
- *Initial install:* when a fresh install lands on a pre-existing
  adopter-edited file (Tier-3 → Tier-2 fast-path), the install drops a
  `.upstream.<ext>` companion rather than overwriting.

**`.agent-ready-state.toml` schema (this spec, v0.1).**

```toml
schema-version = "0.1"

[pack.<name>]                       # one section per installed pack
installed-version = "0.2.0"          # the pack version that produced the recorded hashes
source = "agent-ready-repo"          # catalogue identifier
install-route = "cli"                # "cli" | "apm" | "claude-plugin"
primitives = ["skill", "agent", "hook-body", "hook-wiring", "command"]
                                     # the primitive types this pack projects (subset of: skill, agent, hook-body, hook-wiring, command)

[pack.<name>.files]                  # per-file SHA-256 hash recorded at install time
"<projected-path>" = { sha = "<hex64>", from-pack-version = "<semver>" }
```

The CLI spec (RFC-0003) consumes this schema; this spec pins it. Per-pack
version drift (the third file in RFC-0001's sketch) is permitted —
`from-pack-version` is per-file. Subsequent schema evolution moves the
`schema-version` field forward.

## Recipe set (enumerated)

The recipe types this spec supports — and the only ones the build pipeline
recognises without an RFC or spec amendment:

| Recipe type | Source RFC | Output |
| --- | --- | --- |
| `per-pack-claude-plugin` | RFC-0001 | `dist/claude-plugins/<pack>/` (one per pack) |
| `per-pack-apm-package` | RFC-0001 | `dist/apm/<pack>/` (one per pack) |
| `marketplace` | RFC-0001 | `dist/claude-plugins/marketplace.json` (aggregate) |
| `per-pack-overlay` | RFC-0002 | self-host overlay of `.apm/` + `seeds/` into the working tree |
| `composite-agents-md` | RFC-0002 | composed `AGENTS.md` (or any composite text file) at the repo root *(this spec ships the recipe metadata + expansion-shape API; the on-disk writer is implemented by sibling spec `self-hosting`)* |
| `composite-marketplace` | RFC-0002 | composite of per-pack plugin manifests for the self-host marketplace *(this spec ships the recipe metadata + expansion-shape API; the on-disk writer is implemented by sibling spec `self-hosting`)* |

Any seventh recipe type requires a new RFC or a spec amendment — see
Boundaries *Ask first*.

## Primitive types and per-adapter projections

Five primitive types, projected by four reference adapters. Every (primitive,
adapter) pair has an explicit projection rule; the contract enumerates all
twenty pairs. Missing pairs default to `dropped` only when the contract
declares it so explicitly — no implicit defaults.

| Primitive | Source path (in `packs/<pack>/`) | Claude Code | Kiro | Copilot | Codex |
| --- | --- | --- | --- | --- | --- |
| `skill` | `.apm/skills/<name>/` | `direct-directory` → `.claude/skills/<name>/` | `direct-directory` → `.kiro/skills/<name>/` | `instruction-file` → `.github/instructions/<name>.instructions.md` | `managed-block-inline` → `AGENTS.md` |
| `agent` | `.apm/agents/<name>.md` | `direct-file` → `.claude/agents/<name>.md` | `direct-file` (with `kiro-agent-frontmatter-v0.9` rewrite) → `.kiro/agents/<name>.md` | `dropped` | `dropped` |
| `hook-body` | `.apm/hooks/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` | `direct-file` → `tools/hooks/<name>.{sh,py}` |
| `hook-wiring` | `.apm/hook-wiring/<name>.toml` | `merge-json` (under `hooks` key of `.claude/settings.local.json`) | `degraded-info-log` (RFC-0001 Open Q1 — until Kiro publishes a schema) | `dropped` | `dropped` |
| `command` | `.apm/commands/<name>.md` | `direct-file` → `.claude/commands/<name>.md` | `dropped` | `dropped` | `dropped` |

**Hook extensions.** A hook is a script; the runtime is determined by the
file extension. The build pipeline projects `hook-body` byte-for-byte —
`.sh` stays `.sh`, `.py` stays `.py`. No conversion. Both extensions are
valid in `packs/<pack>/.apm/hooks/`.

**`hook-wiring` source format.** One TOML file per hook at
`.apm/hook-wiring/<name>.toml`. Each file declares the `[hooks]` entries
to merge into `.claude/settings.local.json` (Claude Code) under the
`merge-managed-key-only` on-conflict policy. Other adapters consume the
same source path and project per the table above.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Place the canonical adapter contract at
  `docs/contracts/adapter.toml` with a sibling
  `adapter.schema.json`. This supersedes RFC-0001's original
  `docs/specs/adapter-contract/contract.toml` convention (see
  [RFC-0001 § Amendments](../../rfc/0001-bundle-distribution-by-adapter-spec.md#amendments));
  do not move it under `docs/specs/distribution-adapters/`.
- Use Python stdlib only (target 3.11+ for `tomllib`). Every adapter, every
  recipe consumer, every validator runs without `pip install`.
- Place build-pipeline code at `packages/agentbundle/agentbundle/build/`,
  with recipes under `packages/agentbundle/agentbundle/build/recipes/`,
  adapter implementations at
  `packages/agentbundle/agentbundle/build/adapters/{claude_code,kiro,copilot,codex}.py`,
  and the validator harness at
  `packages/agentbundle/agentbundle/build/validate.py`. The CLI imports
  `agentbundle.build` as a library; `tools/build/build.py` is a thin shim
  (≤ 10 lines, no logic) that calls `python -m agentbundle.build`.
- Implement all seven projection modes from RFC-0001
  (`direct-directory`, `direct-file`, `merge-json`, `instruction-file`,
  `managed-block-inline`, `degraded-info-log`, `dropped`) and honor each
  mode's per-RFC default `on-conflict` value.
- Enumerate every (primitive, adapter) pair in `adapter.toml`. Missing
  pairs default to `dropped` only when the contract states so explicitly.
- Validate pack-internal name uniqueness (no two skills with the same local
  name inside the same pack) at build time; allow cross-pack name reuse.
- Source named frontmatter mappings (e.g. `kiro-agent-frontmatter-v0.9`)
  from the contract TOML's `[frontmatter-mapping.*]` tables — adapters
  consume them generically, never via Python lookup tables.
- Source per-adapter frontmatter defaults (e.g. Copilot's `applyTo: "**"`)
  from `[frontmatter-default.*]` tables — adapters never hardcode the
  default.
- Exit non-zero with a one-line stderr message when validation or drift
  detection fails (so CI and the work-loop's `check-done.py` see the signal).
- Treat `make build --check` as exactly `make build --self --dry-run` plus
  a strict exit code: non-zero on any drift, regardless of warning level.
  The two commands share rendering; `--check` only differs in its gate
  contract.
- When sibling specs reference `pack.toml` or `.claude-plugin/plugin.json`
  shapes, they must link to this spec — flag in PR review if they inline
  the schema instead.

### Ask first

- Adding any projection mode beyond the seven RFC-0001 lists.
- Adding any adapter target beyond the four reference adapters.
- Adding any recipe type beyond the six enumerated in *Recipe set*.
- Schema changes to `pack.toml` or `.claude-plugin/plugin.json` beyond
  the RFC-named fields (these are consumed by RFC-0002 and RFC-0003).
- Any change to `make build`'s seven-subcommand surface (`build`, `build
  PACK=`, `build RECIPE=`, `--self`, `--self --dry-run`, `--check`,
  `--scaffold OUTPUT=`).
- Promoting Kiro hook *wiring* projection out of `degraded-info-log`
  (RFC-0001 Unresolved Q1 keeps it degraded until Kiro publishes a schema).

### Never do

- **No new top-level directory.** Everything lands under existing
  `docs/`, `packages/`, `tools/`, `packs/`, or `dist/` (and `dist/` is
  git-ignored build output, not source). New top-level paths go through RFC.
- **No Python module outside `packages/agentbundle/` for build-pipeline
  code.** `tools/build/build.py` is a thin shim only (no logic, ≤ 10
  lines, imports and calls `agentbundle.build.main`). Adapters, recipes,
  the validator, the contract loader, and tests all live under
  `packages/agentbundle/agentbundle/build/`.
- **No non-stdlib Python dependency.** No `requirements.txt`, no
  third-party imports, no vendored libraries. `packages/agentbundle/`
  has a `pyproject.toml` for packaging metadata only — its `dependencies`
  array is empty. The build pipeline imports only from the standard library.
- **No install-time placeholder substitution — except `make build --self`.**
  Every other mode (`make build`, adopter `agentbundle install`, APM
  `apm install`, Claude `/plugin install`) copies `<adapt:NAME>` markers
  through unchanged. `make build --self` is the *one authorised mode*
  that runs marker resolution as a final build step against this repo's
  concrete values; the resolver itself belongs to the `adapt-to-project`
  skill, which materialises `.adapt-discovery.toml` from this repo's
  values before the build step consumes it. RFC-0001 Open Q3
  (`<adapt:NAME>` for plugin-installed packs) stays deferred to
  `adapt-to-project`.
- **No edits to `docs/_templates/`.** Templates are governance scaffolding
  that ships to adopters; this spec produces distribution machinery, not
  template changes.
- **No silent overwrite semantics encoded outside the contract.** Every
  projection rule's `on-conflict` value lives in `adapter.toml` and is
  carried through into the rendered artifact's manifest (so downstream
  install tools and the adapt step honor RFC-0001's per-mode defaults).
  Adapters never hardcode an `on-conflict` policy.
- **No conformance test suite in this spec.** A *full* per-adapter
  conformance suite is RFC-0003's work; this spec ships unit-level
  projection tests per adapter only.

## Testing Strategy

Three behaviors close this spec; each gets one mode and one verification
artifact.

- **Contract + schema validation — TDD.** The `adapter.toml`/`adapter.schema.json`
  pair is pure data with a compressible invariant ("the contract validates
  against the schema; every adapter block enumerates every (primitive,
  adapter) pair; every projection rule has a defined `on-conflict`"). TDD
  because the invariant is what we ship; the test pins it directly, and
  the same harness powers the validator the build pipeline calls at startup.
- **Per-adapter projection rules — TDD.** Each of the four adapters maps
  source primitives to outputs by deterministic rules — pure functions
  with edge cases (collisions, frontmatter normalization, managed-block
  delimiters, dropped primitives, degraded-info-log emission). TDD because
  each rule is a compressible invariant and the rule set is what the
  contract calls out as the *specification*.
- **End-to-end build pipeline — goal-based check.** `make build` against
  the four reference packs on a clean checkout produces the expected
  `dist/apm/<pack>/` and `dist/claude-plugins/<pack>/` directory shapes
  plus `dist/claude-plugins/marketplace.json`. The one-liner *is* the
  contract: `make build && test -f dist/claude-plugins/marketplace.json
  && test -d dist/apm/core && …`. No mocking layer, no internal
  assertions; the artifact-on-disk verifies. Same for `make build
  --check` (the self-host gate): one-liner asserts the command exits zero
  on a clean tree.

No manual QA: there is no UI surface, no human gesture under test.

## Acceptance Criteria

- [ ] `docs/contracts/adapter.toml` exists, covers all four
  reference adapters (`claude-code`, `kiro`, `copilot`, `codex`), names
  the five primitive types (`skill`, `agent`, `hook-body`, `hook-wiring`,
  `command`), enumerates every (primitive, adapter) pair explicitly, and
  validates against a sibling `docs/contracts/adapter.schema.json`.
- [ ] All seven projection modes (`direct-directory`, `direct-file`,
  `merge-json`, `instruction-file`, `managed-block-inline`,
  `degraded-info-log`, `dropped`) appear in `adapter.schema.json` as the enum of
  legal `mode` values, and every projection rule in `adapter.toml`
  carries an `on-conflict` value matching RFC-0001's per-mode default
  table (or an explicit override from the legal set).
- [ ] `pack.toml` shape is pinned in
  `docs/contracts/pack.schema.json` and referenced from
  `adapter.toml`. The schema accepts `[pack]`, `[pack.dependencies]`
  (with `required`/`recommended`/`conflicts` keys), `[pack.adaptation]`,
  and `[pack.seeds]` tables per RFC-0001. The schema enforces shape
  only: `[pack.adaptation] infer-from` must be a string (a non-string
  is rejected); the semantic set of legal `infer-from` values lives in
  the `adapt-to-project` skill, not in this schema. A missing
  `[pack.dependencies.required]` array is *optional* (no required
  field). The schema's pass/fail tests pin both outcomes plus a
  `[pack.seeds]` shape check (entries must be relative-path strings;
  an absolute path or a non-string is rejected).
- [ ] `.claude-plugin/plugin.json` shape is pinned in a sibling
  `plugin-manifest.schema.json` validating the hand-authored per-pack
  manifests. Each pack's manifest is hand-authored at
  `packs/<pack>/.claude-plugin/plugin.json`; the build copies it
  unmodified into `dist/claude-plugins/<pack>/`.
- [ ] `packages/agentbundle/agentbundle/build/` runs under `python3
  --version` 3.11+ with zero non-stdlib imports (verified by
  `tools/lint-build.sh` and the `pre-pr.sh` hook — a wrong `import yaml`
  surfaces in the offending PR, not at end-of-stream). The CI job that
  runs `pre-pr.sh` exits non-zero on any non-stdlib import under
  `packages/agentbundle/agentbundle/build/`.
- [ ] `validate.py` implements a stdlib-only JSON-Schema subset (object,
  array, string, integer, boolean, enum, required, pattern, items,
  `properties` and `additionalProperties` for object recursion — and
  only these). The subset is documented in T1a's *Approach*. AC #1
  verifies `validate.py` accepts the conforming `adapter.toml` and
  rejects each mutation enumerated in `test_contract.py`. `properties`
  and `additionalProperties` are load-bearing — every shipped schema
  (`adapter.schema.json`, `pack.schema.json`, `plugin-manifest.schema.json`)
  uses them to recurse into nested objects.
- [ ] `make build` on a clean checkout, against the four reference
  fixture packs under
  `packages/agentbundle/agentbundle/build/tests/fixtures/packs/`
  (`core`, `governance-extras`, `user-guide-diataxis`,
  `monorepo-extras`), produces `dist/apm/<pack>/` and
  `dist/claude-plugins/<pack>/` directories for each of the four
  reference packs and a single `dist/claude-plugins/marketplace.json`
  listing every per-pack plugin entry; exit code zero. **Materialisation
  of production packs in a top-level `packs/` directory is out of
  scope** — that migration is RFC-0001's F-dist follow-on. This spec
  ships the pipeline; production packs land separately.
- [ ] Each adapter (`claude_code`, `kiro`, `copilot`, `codex`) has a
  per-adapter unit-test file under
  `packages/agentbundle/agentbundle/build/tests/` covering every
  projection mode that adapter's `adapter.toml` block uses (e.g.
  Copilot exercises `instruction-file`, `direct-file`, and `dropped`;
  Codex exercises `managed-block-inline`, `direct-file`, and `dropped`)
  plus the named frontmatter mapping or default where the contract
  declares one. Idempotence is asserted for `merge-json` (Claude Code)
  as well as `managed-block-inline` (Codex): running each adapter twice
  against the same fixture yields byte-identical output.
- [ ] The build pipeline's validation step (not any individual adapter)
  rejects a pack whose `.apm/skills/`, `.apm/agents/`, `.apm/hooks/`,
  `.apm/hook-wiring/`, or `.apm/commands/` contains two primitives with
  the same local name (pack-internal uniqueness per RFC-0001 §
  Pack-internal naming and collision policy), with a non-zero exit and
  a stderr message naming both paths.
- [ ] `make build --check` (dry-run self-host build + diff against
  on-disk projection) exits zero on a clean tree and exits non-zero
  with a per-file drift listing on any divergence. CI wiring of this
  gate is RFC-0002's spec's job; this spec ships the command.
- [ ] `make build --self` writes projected output to the working tree,
  resolves `<adapt:NAME>` markers against `.adapt-discovery.toml` as a
  final step (the one authorised mode for marker resolution per
  Boundaries § Never do), **refuses on a dirty tree without `--force`
  and exits non-zero with stderr naming the refusal** (verified by a
  T7 test against a dirty-tree fixture), and (with `--force`) honours
  each adapter's declared `on-conflict` policy from `adapter.toml` —
  `--force` overrides only the dirty-tree refusal, never the
  per-adapter on-conflict default. The substitution pass (read
  `.adapt-discovery.toml`, replace `<adapt:NAME>` markers across
  rendered output) is implemented by T7; the *materialisation* of
  `.adapt-discovery.toml` from repo values lives in the
  `adapt-to-project` skill (out of scope here — T7 ships only the
  consumer). Sibling spec `self-hosting` cites this AC.
- [ ] The supported recipe set is exactly the six types named in
  § Recipe set (`per-pack-claude-plugin`, `per-pack-apm-package`,
  `marketplace`, `per-pack-overlay`, `composite-agents-md`,
  `composite-marketplace`); a seventh requires an amendment to this
  spec or a new RFC. Sibling specs (self-hosting, CLI) cite this AC
  when consuming the recipe set.
- [ ] No new top-level source **directory** is introduced. Verified by
  `comm -23 <(git ls-tree -d --name-only HEAD | sort) <(git ls-tree
  -d --name-only "$(git merge-base HEAD main)" | sort)` returning an
  empty set after the change lands — the `-d` flag scopes the audit
  to directories (so `Makefile`, `.gitignore`, and other root-level
  files this spec touches do not trip it), and the merge-base
  comparison keeps the audit correct after a merge from `main` into
  the feature branch. `dist/` is git-ignored and does not count. No
  non-stdlib Python import is added (verified by the import-audit
  check above).
- [ ] Plain `make build` (no flags) produces only `dist/apm/<pack>/`,
  `dist/claude-plugins/<pack>/`, and `dist/claude-plugins/marketplace.json`
  — it does **not** invoke the three self-host recipes
  (`per-pack-overlay`, `composite-agents-md`, `composite-marketplace`).
  The working tree is unchanged after the run (verified by `git
  status` against the working tree before and after, returning byte-
  identical output). This pins the property § Default-recipe behaviour
  declares; T8 owns the test.
