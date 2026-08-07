# Plan: pack-description-quality

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `tools/lint-pack-descriptions.py` + `tools/test-lint-pack-descriptions.py` — new
  repository policy lint and its self-test.
- `tools/repo/build_gate_chain.py` + `.github/workflows/build-check.yml` — wire the
  lint into both gate surfaces (`lint-ci-parity` fails if they disagree).
- `packs/*/pack.toml` — description only (no version bump; see spec Assumption 2).
- `packs/*/.claude-plugin/plugin.json` — mirrored description.
- `.claude-plugin/marketplace.json` — regenerated or hand-synced (T3 decides).
- `docs/product/changelog.md`, `workspace.toml` (`[backlog].open` entry only).

**Tests that demonstrate done**
- New unit tests for the ceiling, the independence of the two caps, and the
  absence of a `pack.schema.json` change.
- `make build-check` + `python3 -m pytest packages/agentbundle/tests/ -q`.
- A repo-wide script asserting every pack ≤400 chars and the three files agree.

**What I am NOT changing**
- Any skill or agent `description` (activation-bearing — see spec § two-audience).
- Anything under `packages/agentbundle/` — `pack.schema.json`, the packaged
  `lint_packs`, `contracts/target-vocab.toml`. All are adopter-facing.
- Any pack's `keywords`, `categories`, `README.md`, or skill content.
- The adapter contract, recipes, or any install route.

**Tempted and declined**
- *Add `maxLength` to `pack.schema.json`* — declined: adopter-facing validation;
  an editorial cap there breaks third-party packs for our house style.
- *Reuse `Constraints.description_max` for the pack cap* — declined: that value is
  a target-derived ingest cap for activation-bearing frontmatter; sharing it would
  couple display copy to Kiro's parser limit.
- *Fix the Codex 2% skill-budget problem in the same PR* — declined: different
  field, different audience, much larger blast radius. Deferred to backlog.
- *Rewrite pack READMEs to match* — declined: the READMEs are already good and are
  where the good taglines came from; touching them widens the diff for no gain.
- *Auto-derive the description from the README's first line* — declined: cute, but
  couples two artifacts with different lengths and lifecycles; one caller only.

## Resolve-vs-surface disposition record

| Item | Disposition |
| --- | --- |
| Schema cap vs lint-only | **Resolved** — lint-only; stated in spec § Never do, surfaced to the human before EXECUTE. |
| Whether `build-self` regenerates `marketplace.json` | **Resolve in T3** — empirical check, contradicting prior note. |
| Whether metadata-only changes need a version bump | **Resolved (T4)** — no bump; no gate requires one and `marketplace.json` republishes independently. |
| Codex 2% skill-description budget | **Surfaced + deferred** — backlog entry; out of scope. |

## Tasks

### T1 — Pack-description ceiling as a repo policy lint (TDD)

**Depends on:** none

**Tests:** `tools/test-lint-pack-descriptions.py`
- `test_description_over_ceiling_is_flagged` — 401-char description → one finding
  naming pack, actual length, ceiling.
- `test_description_at_ceiling_passes` — exactly 400 chars → no finding.
- `test_absent_description_is_not_flagged` — no `[pack].description` → no finding.
- `test_pack_ceiling_independent_of_target_cap` — `_PACK_DESCRIPTION_MAX` is not
  `Constraints.description_max`, and changing one does not move the other.
- `test_pack_schema_has_no_description_maxlength` — reads `pack.schema.json`,
  asserts no `maxLength` under `properties.pack.properties.description`.

**Approach:** a pure-stdlib `tools/` lint with `MAX_DESCRIPTION = 400`, a
`find_violations()` pure function, `--root` flag, exit 0/1 — the shape every other
`tools/lint-*.py` uses. Wired into `build_gate_chain.py` and `build-check.yml` as
a `test-lint-*` / `lint-*` pair.

**Revised mid-EXECUTE.** First implemented inside
`packages/agentbundle/agentbundle/build/lint_packs.py`; the curation guard
(RFC-0059 D6) refused the changeset, which surfaced that `lint_packs` ships in
the published package and runs on adopter catalogues via `agentbundle catalogue
lint`. That is the same adopter-imposition objection already raised against
`pack.schema.json`, so the ceiling moved to `tools/` and the
`packages/agentbundle/` edits were reverted.

### T2 — Rewrite all pack descriptions (goal-based)

**Depends on:** T1

**Tests:** no stub (goal-based).
**Done when:** the T1 lint exits clean across `packs/`, and a script reports every
description ≤400 chars with a verb-or-outcome opening clause.

**Approach:** rewrite each to the formula — sentence 1 = the job, verb-first,
≤ ~90 chars, standalone; optional sentence 2 = compressed capability list or the
one differentiator. Seed each from the pack's own README tagline where one exists.
Strip cross-pack references, provenance name-drops, negative space, internal paths.

### T3 — Sync the three files (goal-based)

**Depends on:** T2

**Tests:** no stub (goal-based).
**Done when:** a script confirms `pack.toml`, `packs/<pack>/.claude-plugin/plugin.json`,
and `.claude-plugin/marketplace.json` carry byte-identical descriptions per pack.

**Approach:** edit per-pack `plugin.json`; then run `make build-self` and diff to
determine empirically whether the root `marketplace.json` regenerates. If it does
not, hand-sync it. Record the answer in the spec's Assumption 1.

### T4 — Version-bump decision (goal-based)

**Depends on:** T3

**Tests:** no stub (goal-based).
**Done when:** `make build-check` passes and every pack's version is identical
across `pack.toml`, `plugin.json`, and `marketplace.json`.

**Approach:** RESOLVED — no bump. No gate requires one, no test pins a real pack
version, and `marketplace.json` republishes on merge independent of pack version,
so the new copy reaches browsing adopters regardless. Rationale recorded in
spec Assumption 2.

### T5 — Changelog + deferred-item record (goal-based)

**Depends on:** T4

**Tests:** no stub (goal-based).
**Done when:** `CHANGELOG.md` has an `[Unreleased]` entry; `workspace.toml`
`[backlog].open` carries the Codex skill-budget entry;
`.claude/skills/work-loop/scripts/lint-spec-status.py --root .` exits clean.
