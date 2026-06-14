# Plan: voice-and-microcopy

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Add a fifth pure-markdown skill to the `product-engineering` pack, mirroring the
existing skills' shape exactly: a lean `SKILL.md` (under 100 lines) that holds the
procedure and routes depth into `references/`, plus a travelling `assets/`
template. Three references carry the three deliverables (voice axes, microcopy
formulas, content checklist) so `SKILL.md` stays a thin orchestration layer. The
riskiest part is *staying inside the four charter bars* — keeping the content
framework-agnostic and habits-shaped, not drifting into a style-guide CMS or
tech-specific advice — and *not duplicating* the documentation-prose checklist
`house-voice-writing-craft` already shipped (different artifact: product UI copy
vs. docs prose). After the files land, the mechanical work is the version bump
(two files), the changelog entry, the README skill-table row, the Diátaxis guide
how-to + index entry, and refreshing the catalogue — `make build` re-aggregates
`dist/`, and `make build-self FORCE=1` refreshes the committed root
`.claude-plugin/marketplace.json` (a self-host projection).

## Constraints

- RFC-0030 / ADR-0019: the pack is **pure markdown, habits-shaped, user-scope**;
  no adapter-specific primitives, no seeds, templates travel in skill `assets/`.
- The `product-engineering-pack` v1 spec caps `SKILL.md` at **under 100 lines**
  and anchors names to recognized vocabulary.
- Edit `.apm/` sources only. The pack's skills are not projected into this repo's
  `.claude/`; `make build` refreshes `dist/`, while the committed root
  `.claude-plugin/marketplace.json` (all-packs aggregation) is refreshed by
  `make build-self FORCE=1` — its only drift here is the version line.

## Construction tests

This is a docs/markdown addition; verification is goal-based + manual QA.

**Integration tests:** none beyond the catalogue gates (`lint-packs`, `build`,
`validate`, `lint-agent-artifacts.py`).
**Manual verification:** read the skill + references against the Acceptance
Criteria; `wc -l SKILL.md` < 100; `marketplace.json` shows the bumped version.

## Tasks

### T1: Author the `voice-and-microcopy` skill (SKILL.md + references + asset)

**Depends on:** none

**Tests:**
- `SKILL.md` has valid frontmatter (`name: voice-and-microcopy`, a `description`
  with trigger phrases + `Do NOT` cross-refs) — verified by `lint-packs`.
- `wc -l SKILL.md` reports < 100.
- `references/voice-axes.md`, `references/microcopy-formulas.md`,
  `references/content-checklist.md`, and `assets/voice-chart-template.md` all exist.
- Each of error / empty / button / label has a formula and a paired before/after
  in `microcopy-formulas.md` (manual read).

**Approach:**
- Create `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
  with a When-to-invoke gate, a 3-step procedure (characterize voice → write
  microcopy with the state formula → run the content checklist), and an
  anti-patterns section, matching the sibling skills' voice.
- Write the three references and the voice-chart template asset.

**Done when:** the five files exist, `SKILL.md` < 100 lines, and `lint-packs`
passes on the pack.

### T2: Wire the pack metadata + catalogue (version, README, changelog, guides)

**Depends on:** T1

**Tests:**
- `pack.toml` `[pack] version` and `.claude-plugin/plugin.json` `version` match
  and are bumped from `0.3.1`.
- `marketplace.json` shows the bumped product-engineering version after `make build`.
- `docs/product/changelog.md` `[Unreleased] → Added` names the new skill.
- The pack `README.md` skill table includes a `voice-and-microcopy` row, and
  `docs/guides/product-engineering/README.md` links a new how-to that exists.

**Approach:**
- Bump pack version to `0.4.0` (additive new skill) in `pack.toml` +
  `plugin.json`; **update the `description`** in both (it enumerates the habit
  skills, so it goes stale) to name the new content layer.
- Add the README skill-table row + the Layout touch-ups as needed. **Bundled
  fix:** the README "Design principles" line says "Skills + `references/` +
  seeds" but the pack ships no `seeds/` — change "seeds" to "assets" (same-file,
  same-concern ride-along).
- Add the changelog entry.
- Add `docs/guides/product-engineering/how-to/write-product-microcopy.md` and an
  index row in the guides README.
- Run `make build`; confirm clean `git status`.

**Done when:** `make lint-packs build validate` and `tools/lint-agent-artifacts.py`
all pass and `git status` is clean.

## Rollout

Pure-markdown skill addition — no infra, no migration, no flag. Ships when the PR
merges; reversible by reverting the PR. The pack is user-scope, so adopters pick
it up on their next `agentbundle install` / `claude plugin install` / `apm install`.

## Risks

- **Charter-bar drift** — the content could slide into tech-specific or
  CMS-shaped territory. Mitigated by the `Never do` boundaries and the
  pre-EXECUTE adversarial pass.
- **Overlap with `house-voice-writing-craft`** — mitigated by scoping strictly to
  product UI copy and cross-referencing, not restating, the docs-prose checklist.

## Changelog

- 2026-06-14: initial plan.
- 2026-06-14: T1 + T2 complete; the committed root `.claude-plugin/marketplace.json`
  required `make build-self FORCE=1` (not `make build`, which only refreshes
  `dist/`) — spec ACs/assumptions corrected to match. Status → Done.
