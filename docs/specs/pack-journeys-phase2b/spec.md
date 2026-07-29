---
**Feature:** pack-journeys-phase2b
**Status:** Shipped
**Mode:** Full (risk triggers: multi-feature dependent tasks, structural change, public-interface change)
**Constrained by:** Phase 2B brief (`.context/attachments/mVGtEe/pasted_text_2026-07-28_13-02-51.txt`)
---

# Pack-owned canonical journeys — Phase 2B

## Objective

Make `packs/<pack>/JOURNEY.md` the canonical source for a pack's primary first-value
journey when that pack has a meaningful multi-stage experience. The central site and
catalogue render pack-owned journeys rather than own duplicate journey prose.

This phase defines the journey contract, adds discovery and validation, updates the
journey renderer to consume pack-owned sources, preserves all public journey routes,
migrates one representative pilot (`product-documentation`), and leaves the remaining
16 journeys on the legacy path.

## Boundaries

**In scope:**
- Journey contract and stage contract definitions (spec + validator)
- State vocabulary centrally defined and enforced
- `tools/lint-journey-contract.py` — extend to accept `**State:**` as a valid optional
  label (rank 5, after Output); required so generated files pass the existing linter
- `tools/lint-pack-journeys.py` — new validation tool for pack-local JOURNEY.md files;
  includes skill-count parity check so the invariant is enforced in CI
- `tools/test-lint-pack-journeys.py` — self-tests for the new validator
- `tools/build-site.py` — extended with (1) `sync_pack_journeys()` function, (2) a
  `--journeys-only` flag that runs ONLY the journey sync and skips Starlight aggregation
  (no Tokensession CSS check, no pack README copying, etc.)
- `web/src/content.config.ts` — add `journey_id`, `start_state`, `end_state`, `generated`
  as optional fields (backward-compatible)
- `tools/catalogue/pre_pr_catalogue.py` — add: (a) `python tools/build-site.py
  --journeys-only` sync step before parity/contract lints; (b) `lint-pack-journeys.py`
  gate and self-test; (c) `lint-journey-contract.py` gate and self-test
- `.github/workflows/pages.yml` — add `python tools/build-site.py --journeys-only`
  step before `npm run build --prefix web` so the generated journey file exists during
  the web/Astro build
- `packs/product-documentation/JOURNEY.md` — pilot migration
- `web/src/content/journeys/product-documentation.md` — deleted from git; replaced by
  the sync-generated version (gitignored)
- `web/src/content/journeys/.gitignore` — marks generated journey files
- `guides/_shared/how-to/pack-journey-authoring.md` — internal maintainer how-to guide
  (NOT in `guides/` — that is catalogue-facing)
- `web/CLAUDE.md` — document generated journey file build dependency

**Out of scope:**
- Migration of any journey beyond `product-documentation`
- Journey UI redesign (Phase 2C)
- Atlassian journey changes or Atlassian skill behavior
- Making JOURNEY.md mandatory for every pack
- Including JOURNEY.md in the installed runtime payload
- Deleting the full legacy central journey system
- Changing existing `journeyUrl` pack-page behavior ("Journey coming soon" is rendered
  by the existing pack template when `journeyUrl` is absent — no new code needed)

## Assumptions

1. The existing `web/src/content/journeys/` content collection remains the source
   Astro reads from; `[journey].astro` renderer is not changed beyond trivial schema.
2. `packs/product-documentation/.apm/skills/author-product-docs/` exists (confirmed
   2026-07-28; one skill directory present).
3. `tools/build-site.py --journeys-only` will be added and invoked before each Astro
   web build — in `pages.yml`, `pre_pr_catalogue.py`, and documented for local use.
4. Direct `npm run build --prefix web` without the journeys-only sync will fail if
   generated files are absent — documented in `web/CLAUDE.md`.
5. `agentbundle install` reads only `.apm/skills/*/SKILL.md` and `.apm/agents/*.md`;
   JOURNEY.md is invisible to install (confirmed 2026-07-28).
6. Phase 2A has no implementation dependency on Phase 2B.

**Declined patterns:**
- Tempted to keep generated file in git (eliminates pages.yml ordering concern) →
  declining; a committed generated artifact diverges silently when the pack-local
  source changes without regenerating; the gitignore + pages.yml fix is cleaner.
- Tempted to use Astro 5 content layer API → declining; pre-build sync is simpler.
- Tempted to migrate all 17 journeys → declining; one pilot only.
- Tempted to redesign journey UI → declining; Phase 2C.
- Tempted to require JOURNEY.md for all packs → declining; conditional per the brief.
- Tempted to include JOURNEY.md in install payload → declining; catalogue-source only.
- Tempted to add a `slug:` field separate from `journey_id` → declining; `journey_id`
  serves as both duplicate detector and URL slug; sufficient for Phase 2B.

## Journey-level contract

Required frontmatter for pack-local `JOURNEY.md`:

```yaml
# Required for pack-local use:
journey_id: string        # unique kebab-case ID; used as URL slug (generated file stem)
pack: string              # must match the pack directory name

# Optional Phase 2B additions:
start_state: StateVocab   # state at journey start
end_state: StateVocab     # state at journey end

# Inherited required fields (same as existing journey collection schema):
scope: user | repo
tagline: string
contract:
  useItWhen: string
  youProvide: string
  youReceive: string
  yourDecisions: [string]
skills:
  - name: string          # must exist in packs/{pack}/.apm/skills/{name}/
    description: string
    humanTouches: integer  # len(skills) must equal len(packs/{pack}/.apm/skills/*)
humanGates: [...]          # all existing gate fields required
typicalSession:
  agentTurns: string
  humanTouches: integer
  wallClockMinutes: string
docsUrl: string
packUrl: string
# optional:
relatedJourneys: [string]
prerequisitePacks: [string]
whatChanges: string
goodOutputDescription: string
```

## Stage contract

Each stage is an h3 heading (`### N. Title`) followed by fixed-label bullet lines.
Label rank order matches the existing `lint-journey-contract.py` convention:

```
You provide        (rank 0, optional)
<Actor> does       (rank 1, optional; Actor ∈ {Agent, Reviewer, Loop})
You do             (rank 2, optional)
You decide         (rank 3; REQUIRED when stage state ∈ write/destructive set)
Output             (rank 4, required)
State              (rank 5, REQUIRED for pack-local stages; absent in legacy files)
```

`lint-journey-contract.py` is updated (T0) to accept `State` as a valid optional rank-5
label so generated files (which preserve `**State:**` lines) pass the linter. State is
never required for legacy files; the linter just stops rejecting it.

## State vocabulary

Defined in `tools/lint-pack-journeys.py` as module-level frozensets:

```python
STATE_VOCAB = frozenset({
    "read-only", "draft", "proposed-write", "confirmed-write",
    "publish", "destructive", "no-action-required", "decision-required", "blocked",
})

# Require a **You decide:** label in the same stage:
WRITE_STATES = frozenset({
    "proposed-write", "confirmed-write", "publish", "destructive", "decision-required",
})
```

`decision-required` is in `WRITE_STATES` because a stage explicitly named as requiring
a decision must carry the `**You decide:**` label — omitting it would be contradictory.

## Discovery and fallback behavior

1. `packs/<pack>/JOURNEY.md` exists and validates → canonical; sync generates
   `web/src/content/journeys/{journey_id}.md` with `generated: true`.
2. No pack-local JOURNEY.md → legacy central file used unchanged.
3. Pack-local JOURNEY.md AND a central file (without `generated: true`) with the same
   `journey_id`/slug → dual canonical ownership error.
4. Pack-local JOURNEY.md AND any central file (without `generated: true`) with the same
   `pack:` value (even at a different slug) → same-pack dual-canonical error (prevents
   silent route changes).
5. No canonical or legacy journey → no journey rendered; pack page shows "Journey
   coming soon" (existing pack template behavior — `[pack].astro` checks `journeyUrl`
   optional; no new code needed).

Both ownership checks (rule 3 and rule 4) are enforced by `lint-pack-journeys.py` AND
by `sync_pack_journeys()` in `build-site.py`. The sync must perform both checks before
generating any file so it never creates a stray output.

## Route derivation

The generated file is placed at `web/src/content/journeys/{journey_id}.md`. Slug in
the URL = `journey_id`. For the pilot:
- `journey_id: product-documentation` → URL: `/journeys/product-documentation/` (unchanged)

For future migrations (not Phase 2B scope), a pack whose legacy route differs from its
pack name would use a matching `journey_id` (e.g. `product-engineering` → `journey_id:
discovery` → URL: `/journeys/discovery/`).

## Installation and export exclusion

`JOURNEY.md` is catalogue-source documentation only. Confirmed by code inspection:
`agentbundle.pack_inventory` enumerates only `.apm/skills/*/SKILL.md`; install reads
nothing else from the pack root. Verified by smoke test in T9 step 11 using the correct
CLI: `python -m agentbundle install --pack product-documentation --output "$tmpdir"`.

## Acceptance Criteria

- [x] AC1 `packs/<pack>/JOURNEY.md` is a supported canonical journey source — the sync
      step in `build-site.py --journeys-only` generates a valid Astro content collection
      entry from a pack-local JOURNEY.md with `generated: true` in frontmatter.
- [x] AC2 Journey ownership is optional — packs without JOURNEY.md use their legacy
      central source unchanged; packs with no legacy source show "Journey coming soon"
      (existing template behavior, no new code).
- [x] AC3 `lint-pack-journeys.py` validates each of: journey_id present, pack matches
      directory, skills exist in pack, skill count matches pack directory count, state
      vocabulary correct, write/destructive/decision-required stages have You decide label,
      no duplicate journey_id, no dual ownership (either same slug or same pack at a
      different slug).
- [x] AC4 Dual canonical ownership detected: validator fails when both pack-local and
      non-generated central file claim the same slug OR the same pack.
- [x] AC5 `packs/product-documentation/JOURNEY.md` exists with `journey_id: product-
      documentation`, `start_state: read-only`, `end_state: confirmed-write`, and
      `**State:**` in every stage with correct vocabulary values.
- [x] AC6 `web/src/content/journeys/product-documentation.md` is deleted from git;
      `web/src/content/journeys/.gitignore` lists it.
- [x] AC7 Running `python tools/build-site.py --journeys-only` generates
      `web/src/content/journeys/product-documentation.md` with `generated: true`.
- [x] AC8 `/journeys/product-documentation/` URL is unchanged after migration (Astro
      builds the page from the generated content file).
- [x] AC9 Pack page `/packs/product-documentation/` shows the journey link
      (the `journeyUrl` frontmatter field in `web/src/content/packs/` is unchanged).
- [x] AC10 `lint-pack-journeys.py` enforces skill-count parity for the pilot (1 skill
       in JOURNEY.md == 1 `.apm/skills/` directory).
- [x] AC11 `lint-journey-contract.py` passes on the generated pilot file — `State` is
       now accepted as a valid optional rank-5 label; all legacy files unaffected.
       Note: `atlassian.md` and `user-guide-diataxis.md` had pre-existing label failures;
       both updated to fixed label set and live gate wired in the vienna-v1 convergence PR.
- [x] AC12 `agentbundle install --pack product-documentation --output "$tmpdir"` produces
       no JOURNEY.md anywhere in `$tmpdir` — verified by `find "$tmpdir" -name JOURNEY.md`.
- [x] AC13 `guides/_shared/how-to/pack-journey-authoring.md` exists and covers: when to add
       JOURNEY.md, journey-level contract, stage contract, state vocabulary, skill reference
       validation, route preservation (journey_id = slug), installation exclusion, migration
       procedure (step-by-step), and how to avoid duplicate canonical sources.
- [x] AC14 All 16 non-pilot journey files pass `lint-web-journey-parity.py` unchanged.
       `lint-journey-contract.py` live gate enabled (see AC11 note — deferred gate closed by vienna-v1 convergence PR).
- [x] AC15 `make build-check` and `make pre-pr` pass with all new gates wired.
- [x] AC16 No journey other than `product-documentation` was migrated in this phase.

## Testing Strategy

**TDD (validator):** `tools/test-lint-pack-journeys.py` fixtures:
- Valid JOURNEY.md → exit 0
- `journey_id` ≠ pack dir name → exit 0 (ID ≠ name is valid)
- Missing `journey_id` → exit 1
- Invalid state in stage (`**State:** bogus`) → exit 1
- Invalid `start_state` vocab → exit 1
- Invalid `end_state` vocab → exit 1
- Referenced skill not in `.apm/skills/` → exit 1
- Skill count mismatch (2 listed, 1 in pack) → exit 1
- Duplicate `journey_id` across two packs → exit 1
- Dual ownership same slug (pack-local + non-generated central) → exit 1
- Dual ownership same pack different slug → exit 1
- Write stage without `**You decide:**` → exit 1
- `decision-required` stage without `**You decide:**` → exit 1
- Missing `**Output:**` in stage → exit 1
- Central file with `generated: true` + pack-local → exit 0 (valid)

**Goal-based:** `build-site.py --journeys-only` generates file; `make site-build` passes;
`make pre-pr` and `make build-check` pass.

**Visual/Manual QA:** Serve via `npm run dev --background --prefix web`; verify
`/journeys/product-documentation/` at 1440/1024/390px; skill cards, human gates, pack
page link all correct.

**Install smoke test (AC12):** Run `python -m agentbundle install --pack product-documentation
--output "$tmpdir"` (with correct catalogue args) and assert no JOURNEY.md in output tree.
