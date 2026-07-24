# Spec: digital-product-guides-update

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071 (Digital Experience Doctrine governance gate)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `docs/guides/experience-design/` tree accumulated guides across Wave 1 and Wave 2 of ini-003. Each guide is individually correct but the index (`README.md`) is incomplete: it omits five guides added in Wave 2 (four how-tos — design-review, design-system-chain, copy-layer-boundary, run-cross-pack-eval — and one reference — state-coverage), has no "start here" walkthrough, and is missing two cross-links between related guides. The `web/src/content/journeys/experience-design.md` page is missing the cross-pack eval addition from M5. The `web/src/content/packs/experience-design.md` page lists 20 skills but omits `experience-status`.

This spec completes the integrative layer for the XD-specific surface of M6: a coherent guide index organized by journey phase, a "start here" end-to-end walkthrough, the two missing cross-links, and accurate skill and guide inventories on the marketing site — so an adopter landing cold can navigate the full design thread without repo knowledge.

The M6 workspace.toml brief also calls for an end-to-end cross-pack tutorial and cross-pack intent indexes; those are deferred to backlog items (see ACs below).

## Boundaries

### Always do

- Update `README.md` to index every guide file in `docs/guides/experience-design/`, including `explanation/`, `how-to/`, and `reference/`.
- Add "Start here" walkthrough section with correct cross-links in phase order.
- Add the two genuinely-missing cross-links: `design-system-chain.md → author-design-intent.md` and `author-design-intent.md → design-system-chain.md` and `page-archetypes.md`.
- Match the journey page step descriptions to the full Wave 2 chain (add cross-pack eval prose mention to step 5).
- Add `experience-status` to the packs page skill list; correct "20 skills" count to "21 skills".
- Move `spec/digital-product-guides-update` from `["ini-003".work].queue` to `["ini-003".work].shipped` in `workspace.toml`. Do not touch the `{slug = "digital-product-profile", needs = …}` backlog reference that legitimately cites this path.
- Flip `- **Status:**` from `Implementing` to `Shipped` and check ACs #1–#9 to `[x]` in the same PR.

### Ask first

- Any change to skill `SKILL.md` body or description.
- Any change to eval fixtures or checkers.
- Any new how-to or reference guide file beyond what already exists.

### Never do

- Touch `packs/experience-design/.apm/skills/**` (skill content) — docs-only.
- Touch `packs/experience-design/.apm/evals/**` (eval files) — docs-only.
- Bump the pack version (docs-only; no skill or eval content touched).
- Add a new top-level directory to `docs/guides/`.
- Create new guide files — only update the README index and existing files.
- Delete the `{slug = "digital-product-profile", needs = "ini-003:work:spec/digital-product-guides-update"}` entry in `[backlog].open`.

## Testing Strategy

Mixed: **goal-based checks** for most behaviors; **manual QA** for the organizational quality of the "Start here" section.

| Behavior | Mode | Verification |
|---|---|---|
| README indexes `explanation/the-experience-thread.md` | Goal-based | `grep -F "the-experience-thread.md" README.md` ≥ 1 |
| README indexes `how-to/author-design-intent.md` | Goal-based | `grep -F "author-design-intent.md" README.md` ≥ 1 |
| README indexes `how-to/copy-layer-boundary.md` | Goal-based | `grep -F "copy-layer-boundary.md" README.md` ≥ 1 |
| README indexes `how-to/design-review.md` | Goal-based | `grep -F "design-review.md" README.md` ≥ 1 |
| README indexes `how-to/design-system-chain.md` | Goal-based | `grep -F "design-system-chain.md" README.md` ≥ 1 |
| README indexes `how-to/page-archetypes.md` | Goal-based | `grep -F "page-archetypes.md" README.md` ≥ 1 |
| README indexes `how-to/run-cross-pack-eval.md` | Goal-based | `grep -F "run-cross-pack-eval.md" README.md` ≥ 1 |
| README indexes `reference/experience-design.md` | Goal-based | `grep -F "reference/experience-design.md" README.md` ≥ 1 |
| README indexes `reference/state-coverage.md` | Goal-based | `grep -F "state-coverage.md" README.md` ≥ 1 |
| README has "Start here" section | Goal-based | `grep -c "Start here" README.md` ≥ 1 |
| README skill count correct | Goal-based | `grep -c "21 skills" README.md` ≥ 1 and `grep -c "18 skills" README.md` = 0 |
| "Start here" lists all phases in chain order, each with link | Manual QA | Cold read: seven numbered phases each cross-linking the right how-to |
| design-system-chain → author-design-intent link (new) | Goal-based | `grep -F "](author-design-intent.md)" how-to/design-system-chain.md` ≥ 1 |
| author-design-intent → design-system-chain link (new) | Goal-based | `grep -F "](design-system-chain.md)" how-to/author-design-intent.md` ≥ 1 |
| author-design-intent → page-archetypes link (new) | Goal-based | `grep -F "](page-archetypes.md)" how-to/author-design-intent.md` ≥ 1 |
| All relative links in guides resolve | Goal-based | Python link-resolution check (see plan Task 4) exits 0 |
| Journey page mentions cross-pack eval | Goal-based | `grep -c "cross-pack eval\|cross-pack experience eval" journeys/experience-design.md` ≥ 1 |
| Packs page lists experience-status | Goal-based | `grep -c "experience-status" packs/experience-design.md` ≥ 1 |
| Packs page skill count corrected | Goal-based | `grep -c "21 skills" packs/experience-design.md` ≥ 1 and `grep -c "20 skills" packs/experience-design.md` = 0 |
| workspace.toml: queue has no DPGU entry | Goal-based | `grep "spec/digital-product-guides-update" workspace.toml` absent from queue block |
| workspace.toml: shipped has DPGU entry | Goal-based | `grep "spec/digital-product-guides-update" workspace.toml` present in shipped block |
| workspace.toml backlog: xd-cross-pack-tutorial | Goal-based | `grep -c "xd-cross-pack-tutorial" workspace.toml` ≥ 1 |
| workspace.toml backlog: xd-cross-pack-intent-index | Goal-based | `grep -c "xd-cross-pack-intent-index" workspace.toml` ≥ 1 |
| workspace.toml parse | Goal-based | `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0 |
| Spec Status: Shipped + ACs #1–#9 checked | Goal-based | `grep "Status.*Shipped" spec.md` ≥ 1; `grep -c "^\- \[x\]" spec.md` ≥ 9 |

## Acceptance Criteria

- [x] `docs/guides/experience-design/README.md` indexes every guide file that exists on disk: `explanation/the-experience-thread.md`; `how-to/author-design-intent.md`, `copy-layer-boundary.md`, `design-review.md`, `design-system-chain.md`, `page-archetypes.md`, `run-cross-pack-eval.md`; `reference/experience-design.md`, `state-coverage.md`. Each file is confirmed by a per-file `grep -F "<filename>.md" README.md` ≥ 1 check.
- [x] `README.md` intro skill count reads "21 skills" (not "18 skills"). Organized by a logical grouping that reflects the XD chain order.
- [x] `README.md` includes a "Start here" section with seven numbered phases in XD chain order. Each phase that maps to a guide cross-links it (phase 6 — independent review — has no dedicated how-to; phase 7 — quality floor — links the state-coverage reference). Cold-read manual QA: navigable without prior knowledge.
- [x] `how-to/design-system-chain.md` contains an explicit markdown link `](author-design-intent.md)` — verified by `grep -F "](author-design-intent.md)"`.
- [x] `how-to/author-design-intent.md` contains explicit markdown links `](design-system-chain.md)` and `](page-archetypes.md)` — each verified by link-shaped grep.
- [x] All internal markdown relative links in `docs/guides/experience-design/` resolve (Python link-resolution check exits 0).
- [x] `web/src/content/journeys/experience-design.md` step 5 mentions the cross-pack eval in prose (no inline hyperlink; consistent with existing link-free body style).
- [x] `web/src/content/packs/experience-design.md` skill list includes `experience-status`; prose description updated to "21 skills" (not "20 skills").
- [x] `workspace.toml` updated: `spec/digital-product-guides-update` absent from `queue`, present in `shipped`; backlog entries added for `xd-cross-pack-tutorial` and `xd-cross-pack-intent-index`; `digital-product-profile` needs-reference intact; `tomllib.load` exits 0; spec `Status: Shipped`; ACs #1–#9 set to `[x]`.
- [ ] End-to-end cross-pack tutorial (strategy→PE→XD→FE→review→measurement example). (deferred: xd-cross-pack-tutorial)
- [ ] Cross-pack intent index ("I want to…" → pack + skill + guide). (deferred: xd-cross-pack-intent-index)

## Assumptions

- Technical: Pack is at 1.6.0 on origin/main (verified: `pack.toml` in worktree)
- Technical: 21 skills in the XD pack including `experience-status` (verified: `ls packs/experience-design/.apm/skills/`)
- Technical: `README.md` currently omits five guides: `copy-layer-boundary`, `design-review`, `design-system-chain`, `run-cross-pack-eval` (how-to) and `state-coverage` (reference) (verified: file listing vs README content)
- Technical: `design-review.md → state-coverage`, `page-archetypes → information-architecture`, and `copy-layer-boundary → tone-of-voice` cross-links ALREADY EXIST in the files (verified: grep at spec-authoring time) — not in scope for Task 2
- Technical: Genuine missing cross-links: `design-system-chain → author-design-intent` and `author-design-intent → design-system-chain/page-archetypes` (verified: grep returned 0)
- Technical: Journey page does not mention cross-pack eval (verified: `grep -c "cross-pack" web/src/content/journeys/experience-design.md` = 0)
- Technical: Journey page body uses prose without inline hyperlinks (verified: grep for `](` in body = 0)
- Technical: Packs page missing `experience-status` in skills list (verified: grep count = 0)
- Technical: `site/` is a MkDocs site serving `docs/` content; no separate XD journey/pack pages in site/ (verified: `find site/ -name "experience-design*"` returned no results); updating `docs/guides/experience-design/` covers the docs site content
- Technical: `workspace.toml:1064` contains `{slug = "digital-product-profile", needs = "ini-003:work:spec/digital-product-guides-update"}` — this is a legitimate dependency reference that must NOT be removed in Task 4
- Process: Docs-only changes do not warrant a pack version bump (established by M6 brief in workspace.toml)
- Process: Conventional Commits, no Co-Authored-By trailer; git user eugenelim

## Bundled fixes

Ride-along edits in scope of the same PR (same-area, same-concern):

- **`docs/specs/README.md`** — DPGU spec row moved from Active specs to Shipped specs (archived); `| --- | --- | --- | --- |` table delimiter restored (was replaced when inserting the row); status cell corrected to "Shipped" to match `spec.md`. Same-concern: this index tracks the lifecycle state of every spec in this repo, including this one.
- **`docs/guides/experience-design/README.md` line 15** — citation updated from "the W3C Design Tokens interchange shape" to "the Design Tokens Community Group (DTCG)". Same sentence as the skill-count and skill-name edits that Task 1 touches; DTCG is the recognized body name used in the pack's SKILL.md bodies and is more precise than the original phrasing. No AC or plan step explicitly called for this; it is declared here as a bundled mechanical improvement to the standards citation in the same intro paragraph the plan edits.
