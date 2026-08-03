# Spec: xd-copy-direction

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0062](../../rfc/0062-content-design-and-copy-direction-skills.md) (Accepted 2026-07-23)
- **Brief:** none
- **Contract:** none — skill SKILL.md artifact; no API/event/RPC interface
- **Shape:** integration — new skill integrated into `packs/experience-design`; re-scope of `tone-of-voice`; cross-pack boundary notes across `product-engineering`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## RFC reconciliation note

RFC-0062 uses the names `aesthetic-direction` and `voice-and-microcopy`; the current skills are `creative-direction` and `ux-writing` respectively (renamed since RFC authoring). RFC-0062's follow-on spec list used `copy-direction-skill`; this spec slug is `xd-copy-direction` (ini-003 naming prefix). These name drifts have no functional impact.

RFC-0062 D4 defines a two-way boundary: `copy-direction` ↔ `voice-and-microcopy`. This spec expands the boundary to four-way (`copy-direction` / `ux-writing` / `content-design` / `tone-of-voice`) as described in the workspace.toml shaping annotation, which was authored after the RFC and reflects the settled design including `content-design`'s role and `tone-of-voice`'s re-scoped position as the brand-level register upstream of `copy-direction`.

### RFC-0071 decision #4 conflict

`workspace.toml` lines 153–163 record five pre-implementation decisions that "must be ratified in RFC-0071 before any M1+ spec starts"; decision #4 reads: "copy-direction extends tone-of-voice frontmatter; not a new skill." This appears to contradict this spec, which builds copy-direction as a full new skill.

**Resolution:** The queue entry at `workspace.toml` lines 242–263 supersedes decision #4. It reads: "Governance: RFC-0062 (Accepted), not RFC-0071. RFC-0071 accepted RFC-0062; this spec is its implementation." RFC-0062 designed copy-direction as a full new XD skill from the start. Decision #4 was a pre-implementation shaping hypothesis that was resolved by RFC-0062 Acceptance; the comment is stale. This PR updates the stale comment in `workspace.toml` to note it was superseded by the RFC-0062 acceptance and the queue entry's governance note.

### Tone-of-voice relationship

The shipped `tone-of-voice` skill occupies both the brand-register role and the per-surface acquisition role simultaneously. This spec resolves the overlap by re-scoping `tone-of-voice` to brand-level register only, and installing `copy-direction` as the per-surface acquisition copy positioning skill.

**Output-path de-confliction:** both skills currently write to `<output_dir>/copy/<slug>.md`. After re-scope, `tone-of-voice` writes a single brand-level doc at `<output_dir>/copy/brand-register.md` (stable slug; not per-surface). `copy-direction` writes per-surface docs at `<output_dir>/copy/<surface-slug>.md`. This prevents overwrite when both are used in the same adopter workspace.

## Objective

This spec delivers:

1. **`copy-direction` SKILL.md** in `packs/experience-design/.apm/skills/copy-direction/` — a per-surface marketing/acquisition copy positioning skill. Its 8-step *procedure* follows `creative-direction`'s interrogation rhythm; its artifact/layout/reference model mirrors `tone-of-voice` (seven reference files, `type: copy-direction` frontmatter, per-surface `<output_dir>/copy/<surface-slug>.md` path). Scope: owns per-surface marketing/acquisition copy voice for a specific surface (hero headlines, above-fold narrative, taglines, campaign copy). Takes a content brief as optional upstream input in step 1 (if a content brief exists for the surface, it sources the audience map and `communication_mode`). Feeds `ux-writing` for per-screen UI copy states. References `tone-of-voice` brand-register doc in step 3 as an optional upstream referent.

2. **`tone-of-voice` full re-scope** — eight sub-changes are required:
   - **(a)** *Frontmatter description* — remove per-surface acquisition triggers; scope to brand-level register ("what voice should our copy have overall", "how do we sound different from competitors", "help us name a distinctive register").
   - **(b)** *"When to invoke" step 4* — replace per-surface surface list (marketing/acquisition copy, above-fold narrative, taglines, announcement copy) with brand-level scope (overall product copy personality, cross-surface voice consistency, copy register documentation).
   - **(c)** *Anti-pattern block* — change "This skill names copy direction for marketing/acquisition copy voice and positioned copy" to "This skill names brand-level copy register — the cross-surface voice and copy personality that all per-surface copy decisions reference."
   - **(d)** *Step 6 output path* — change `<output_dir>/copy/<slug>.md` to `<output_dir>/copy/brand-register.md`; add boundary note: "For per-surface copy positioning (hero headlines, above-fold narrative, taglines), use `copy-direction`."
   - **(e)** *`references/agentbundle-layout.md` — path and slug examples* — change slug examples from `landing-page`, `product-launch`, `onboarding` to the stable `brand-register` convention; update the frontmatter contract to document `brand-register`.
   - **(f)** *`references/agentbundle-layout.md` — `surface:` field* — remove the `surface: <marketing/acquisition | onboarding | announcement | other>` frontmatter field from the contract; it is inherently per-surface and does not apply to a single brand-level register doc. Replace with `scope: brand-level` if a discriminator is needed.
   - **(g)** *Per-surface content-brief coupling in steps 3, 7, and 8* — remove all three per-surface couplings: (i) step 3's paragraph "If a content brief is upstream and its frontmatter declares `communication_mode: product-copy`…" and the anti-AI-smell editorial gate run; (ii) step 7's "For `product-copy` mode: run the anti-AI-smell scan from `references/editorial-quality-gates.md`…" clause; (iii) step 8's "if a content brief exists for this surface, the tone-of-voice goals must be consistent with the brief's section jobs and narrative arc" clause. Brand-level register direction does not originate from a single surface's content brief. The `editorial-quality-gates.md` reference file remains in `tone-of-voice/references/` but is no longer invoked. The editorial gate function (anti-AI-smell scan against copy goals) moves to `copy-direction` — where it belongs, since copy-direction takes a content brief as input and must apply the scan there.
   - **(h)** *Boundary note* — add a "Do NOT use" note pointing per-surface acquisition copy positioning (hero headlines, above-fold, taglines) to `copy-direction`.

3. **Reference tree** — seven reference files for `copy-direction` covering audience mapping, interrogation sequence, copy grounding, copy arbitration, plain-language floor, output path resolution, and editorial quality gates (anti-AI-smell scan applied when the upstream content brief declares `communication_mode: product-copy`).

4. **Assets** — `copy-direction-template.md` mirroring `tone-of-voice-template.md` format with copy-goal fields adapted for per-surface positioning.

5. **Activation evals** — `eval_queries.json` (Tier-A activation coverage) and `evals.json` (LLM-judge rubric). Five `tone-of-voice` eval queries are per-surface and must move to `should_trigger: false` in `tone-of-voice`'s `eval_queries.json`:
   - "Write a copy direction doc for our landing page — we know the vibe but can't name it"
   - "What should our hero headline feel like? We want authority without sounding cold"
   - "Copy vibe check — does our above-fold copy sound like us?"
   - "What copy goals should drive our product launch announcement?"
   - "Before we write the tagline, we need to name what it should feel like"

   Five brand-level queries remain `should_trigger: true` in `tone-of-voice`: the "developer tool too corporate", "sound different from competitors", "sound like a guide not an expert", "distinctive register", and "copy arbitration rule" entries.

6. **Pack metadata** — `experience-design/pack.toml` updated: `copy-direction` in `[pack.evals].skills`; version `2.0.0`. `experience-design/.claude-plugin/plugin.json` bumped to `2.0.0`. `product-engineering/pack.toml` bumped to `0.13.3` (patch — body change only). `product-engineering/.claude-plugin/plugin.json` bumped to `0.13.3`. `make build-self` run **after both packs are bumped** to regenerate `.claude-plugin/marketplace.json`.

7. **Journey and pack pages** — `JOURNEY.md`, `web/src/content/packs/experience-design.md`, and the regenerated `web/src/content/journeys/experience-design.md` updated to include `copy-direction`.

8. **Four-way boundary documentation** — all four files updated atomically:
   - `copy-direction/SKILL.md` description: three "Do NOT use" boundary clauses (ux-writing, content-design, tone-of-voice)
   - `ux-writing/SKILL.md` procedure extended: (a) routing boundary note references `copy-direction` for per-surface marketing/acquisition copy voice including onboarding; (b) step 1 now resolves `[design].output_dir` via two-step layout lookup (repo-root `./agentbundle-layout.toml` → user-profile `~/.agentbundle/agentbundle-layout.toml` → default `docs/design`); (c) step 1 loads `<output_dir>/copy/brand-register.md` by fixed path if present, validating `type: tone-of-voice` AND `scope: brand-level` before use; (d) step 1 reconciles an existing voice chart against the brand register and surfaces conflicts before reusing; (e) step 1 derives and writes a new voice chart from the brand register when no chart exists but a register is present.
   - `content-design/SKILL.md` frontmatter description: updated to reference `copy-direction` for per-surface acquisition copy voice; `tone-of-voice` retained only as brand-register companion
   - `content-design/SKILL.md` step 5 body: copy-direction replaces tone-of-voice as the per-surface handoff; the `communication_mode: product-copy` consumer line updated to name copy-direction; tone-of-voice retained as brand-register companion
   - `tone-of-voice/SKILL.md` description: re-scoped (sub-change a); boundary note added (sub-change h)

9. **How-to guide** — `guides/experience-design/how-to/copy-boundary.md`.

10. **Workspace bookkeeping** — move queue entry to shipped; update the stale RFC-0071 decision #4 comment in `workspace.toml` to note it was superseded by RFC-0062 Acceptance and the queue entry's governance note.

11. **RFC-0071 erratum** — RFC-0071 has two factual errors introduced by copy-direction's addition: lines 313–314 describe copy-direction as upstream of tone-of-voice (ordering reversed; correct: tone-of-voice is upstream), and line 311 reads "All 19 skills" (should be 20 after copy-direction is added). An `## Errata` section is appended to `docs/rfc/0071-digital-experience-doctrine.md` correcting both.

12. **Guide and reference corrections** — `guides/experience-design/README.md` updated: skill count "18 skills" → "19 skills"; "copy direction" added to the skill inventory summary. `packs/experience-design/.apm/skills/tone-of-voice/references/copy-jtbd.md` ranking criterion 2 updated from surface-specific language to brand-wide language to match tone-of-voice's re-scoped brand-level purpose.

## Boundaries

### Always do

- Follow `creative-direction`'s 8-step interrogation *rhythm* for `copy-direction`'s procedure; use `tone-of-voice`'s artifact/layout/reference model (seven refs, `type:` pinned, layout reference file)
- Scope `copy-direction` strictly to per-surface marketing/acquisition copy positioning
- Scope `tone-of-voice` (after re-scope) to brand-level register only — all eight sub-changes required
- Name `ux-writing` as the handoff for per-screen UI copy states in `copy-direction`
- Reference `tone-of-voice` brand-register doc in `copy-direction` step 3 as an optional upstream referent
- Pin the `copy-direction` artifact path: `<output_dir>/copy/<surface-slug>.md` with `type: copy-direction`
- Pin the re-scoped `tone-of-voice` artifact path: `<output_dir>/copy/brand-register.md`
- Pass `python3 tools/lint-experience-agnostic.py` — no stack tokens, no color literals, no dimension values
- Pass `python3 tools/lint-web-journey-parity.py` — skill count parity after regeneration
- Regenerate `web/src/content/journeys/experience-design.md` via `python3 tools/build-site.py --journeys-only`
- Bump both pack.toml AND plugin.json in lockstep for each bumped pack; run `make build-self` only after **both** packs are bumped

### Ask first

- Changing the `copy-direction` artifact `type:` from `copy-direction`
- Adding `copy-direction` to the `digital-experience-contract.md` template field set
- Changing the `tone-of-voice` re-scope beyond the eight sub-changes enumerated above

### Never do

- Put color literals, dimension values, or stack tokens in any `packs/experience-design/` file
- Produce finished copy strings in the `copy-direction` skill procedure
- Modify any file outside the scope listed in ACs
- Change the lint scripts themselves

## Testing Strategy

- **Skill exists:** `ls packs/experience-design/.apm/skills/copy-direction/SKILL.md` exits 0
- **Agnosticism lint passes:** `python3 tools/lint-experience-agnostic.py` exits 0
- **Journey parity holds:** `python3 tools/lint-web-journey-parity.py` exits 0
- **Artifact type pinned:** `grep "type: copy-direction" packs/experience-design/.apm/skills/copy-direction/references/agentbundle-layout.md` hits
- **Template exists:** `ls packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md` exits 0
- **Evals exist:** `ls packs/experience-design/.apm/skills/copy-direction/evals/eval_queries.json packs/experience-design/.apm/skills/copy-direction/evals/evals.json` exits 0
- **Evals count:** `python3 -c "import json,pathlib; d=json.loads(pathlib.Path('packs/experience-design/.apm/skills/copy-direction/evals/eval_queries.json').read_text()); assert sum(1 for q in d if q['should_trigger'])>=6; assert sum(1 for q in d if not q['should_trigger'])>=6"`
- **All seven references exist:** `ls packs/experience-design/.apm/skills/copy-direction/references/{agentbundle-layout,audience-jtbd,copy-grounding,copy-arbitration,interrogation-sequence,plain-language-floor,editorial-quality-gates}.md` exits 0
- **Boundary in ux-writing:** `grep "copy-direction" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits
- **Boundary in content-design frontmatter:** `python3 -c "t=open('packs/experience-design/.apm/skills/content-design/SKILL.md').read(); fm=t.split('---')[1]; assert 'copy-direction' in fm"`
- **Boundary in content-design body:** `grep -n "copy-direction" packs/experience-design/.apm/skills/content-design/SKILL.md | grep -v "^[1234]:"`
- **Boundary in tone-of-voice:** `grep "copy-direction" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` hits
- **tone-of-voice output path updated:** `grep "brand-register" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` hits
- **tone-of-voice layout ref output path and surface field:** `grep "brand-register" packs/experience-design/.apm/skills/tone-of-voice/references/agentbundle-layout.md` hits; `grep "surface:" packs/experience-design/.apm/skills/tone-of-voice/references/agentbundle-layout.md | grep -v "brand-level"` exits non-zero (per-surface field removed)
- **tone-of-voice product-copy coupling removed (steps 3 + 7):** `grep -c "product-copy" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` outputs `0`
- **tone-of-voice step 8 content-brief clause removed:** `grep -q "section jobs and narrative arc" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` exits non-zero
- **tone-of-voice per-surface eval queries moved:** `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json')); moved=[q for q in d if 'landing page' in q['query'] or 'hero headline' in q['query'] or 'above-fold' in q['query'] or 'product launch announcement' in q['query'] or 'tagline' in q['query']]; assert all(not q['should_trigger'] for q in moved), moved"`
- **tone-of-voice brand-level queries retained:** `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json')); assert sum(1 for q in d if q['should_trigger']) == 8, 'expected 8 brand-level true queries'"`
- **XD pack.toml version and evals:** `python3 -c "import tomllib; t=tomllib.load(open('packs/experience-design/pack.toml','rb')); assert t['pack']['version']=='2.0.0' and 'copy-direction' in t['pack']['evals']['skills']"`
- **XD plugin.json version:** `python3 -c "import json; p=json.load(open('packs/experience-design/.claude-plugin/plugin.json')); assert p['version']=='2.0.0'"`
- **PE pack.toml version:** `python3 -c "import tomllib; t=tomllib.load(open('packs/product-engineering/pack.toml','rb')); assert t['pack']['version']=='0.13.3'"`
- **PE plugin.json version:** `python3 -c "import json; p=json.load(open('packs/product-engineering/.claude-plugin/plugin.json')); assert p['version']=='0.13.3'"`
- **Marketplace parity:** `python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); xd=next(p for p in d['plugins'] if p.get('displayName')=='Experience Design'); pe=next(p for p in d['plugins'] if p.get('displayName')=='Product Engineering'); assert xd['version']=='2.0.0' and pe['version']=='0.13.3'"`
- **How-to guide exists:** `ls guides/experience-design/how-to/copy-boundary.md` exits 0
- **JOURNEY.md has copy-direction entry:** `grep "copy-direction" packs/experience-design/JOURNEY.md` hits
- **Shipped:** `python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); s=d['ini-003']['work']['shipped']; assert any(s2=='spec/xd-copy-direction' if isinstance(s2,str) else s2.get('path')=='spec/xd-copy-direction' for s2 in s)"`
- **Queue cleared:** `python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); q=d['ini-003']['work']['queue']; assert not any((s if isinstance(s,str) else s.get('path',''))=='spec/xd-copy-direction' for s in q)"`
- **TOML valid:** `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0
- **tone-of-voice per-surface phrases removed (description + step 4 + anti-pattern):** `grep -cE "(hero headline|above-fold|taglines|announcement copy|onboarding copy voice)" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` outputs `0`
- **tone-of-voice anti-pattern rephrase applied:** `grep -q "brand-level copy register" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` exits 0
- **ux-writing stale onboarding routing removed:** `grep -qE "copy voice and register[^;]*tone-of-voice" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exits non-zero (stale per-surface ownership pointer gone; clause-scoped so a brand-register companion mention later on the same line is safe); `grep -q "onboarding.*copy-direction" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exits 0 (copy-direction named as onboarding copy voice owner)
- **ux-writing two-step layout lookup:** `grep -q "agentbundle/agentbundle-layout.toml" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits (user-profile path referenced)
- **ux-writing brand-register fixed-path lookup:** `grep "copy/brand-register.md" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits; `grep "scope.*brand-level\|brand-level.*scope" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits (validation check present)
- **ux-writing voice-chart derivation from register:** `grep "derive.*voice chart\|voice chart.*register\|derived.*register" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits (chart derivation branch present)
- **Manual review:** `copy-direction` SKILL.md contains all 8 steps; step 1 mentions content brief as optional upstream input; step 3 references `tone-of-voice` brand-register doc with marker validation; step 8 names `ux-writing`; description has three "Do NOT use" boundary notes; `tone-of-voice` step 3 no longer contains per-surface content-brief coupling
- **RFC-0071 erratum present:** `grep -q "Errata" docs/rfc/0071-digital-experience-doctrine.md` exits 0
- **Guide skill count updated:** `grep -q "19 skills" guides/experience-design/README.md` exits 0
- **copy-jtbd brand-wide criterion:** `grep -q "brand reaches" packs/experience-design/.apm/skills/tone-of-voice/references/copy-jtbd.md` exits 0

## Acceptance Criteria

- [x] `packs/experience-design/.apm/skills/copy-direction/SKILL.md` exists; `name: copy-direction`; description triggers on per-surface acquisition copy positioning; three boundary "Do NOT use" clauses (ux-writing, content-design, tone-of-voice)
- [x] SKILL.md 8-step procedure follows `creative-direction`'s interrogation rhythm; layout/artifact/reference model mirrors `tone-of-voice`; step 1 references optional upstream content brief; step 3 references `tone-of-voice` brand-register doc as optional upstream referent; step 8 names `ux-writing` as handoff
- [x] `packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md` exists; mirrors `tone-of-voice-template.md` format with copy-goal fields for per-surface positioning
- [x] `packs/experience-design/.apm/skills/copy-direction/evals/eval_queries.json` exists; ≥6 `should_trigger: true` entries (per-surface acquisition copy); ≥6 `should_trigger: false` entries (brand register, UI copy, SEO, content-design scope)
- [x] `packs/experience-design/.apm/skills/copy-direction/evals/evals.json` exists; `skill_name: copy-direction`; at least one eval scenario — verified by: `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/copy-direction/evals/evals.json')); assert d.get('skill_name')=='copy-direction' and len(d.get('evals',d.get('scenarios',[])))>0"`
- [x] All seven reference files exist under `packs/experience-design/.apm/skills/copy-direction/references/`: `agentbundle-layout.md`, `audience-jtbd.md`, `copy-grounding.md`, `copy-arbitration.md`, `interrogation-sequence.md`, `plain-language-floor.md`, `editorial-quality-gates.md`
- [x] `copy-direction/references/agentbundle-layout.md` pins path `<output_dir>/copy/<surface-slug>.md` with `type: copy-direction`
- [x] `python3 tools/lint-experience-agnostic.py` exits 0
- [x] `packs/experience-design/pack.toml`: `[pack.evals].skills` includes `copy-direction`; `[pack].version` is `2.0.0`
- [x] `packs/experience-design/.claude-plugin/plugin.json` version is `2.0.0`
- [x] `packs/experience-design/JOURNEY.md` `skills:` list includes a `copy-direction` entry with `description` and `humanTouches: 0`
- [x] `web/src/content/packs/experience-design.md` `skills:` list includes `copy-direction`
- [x] `web/src/content/journeys/experience-design.md` `skills:` list includes `copy-direction` (regenerated from JOURNEY.md)
- [x] `python3 tools/lint-web-journey-parity.py` exits 0
- [x] `packs/product-engineering/.apm/skills/ux-writing/SKILL.md` boundary note references `copy-direction` for per-surface marketing/acquisition copy voice including onboarding copy voice; removes or replaces any pointer to `tone-of-voice` for per-surface copy voice
- [x] `packs/experience-design/.apm/skills/content-design/SKILL.md` frontmatter description references `copy-direction` for per-surface acquisition copy voice; `tone-of-voice` retained as brand-register companion; step 5 body: copy-direction is the per-surface handoff; `communication_mode: product-copy` consumer line names copy-direction; tone-of-voice retained as brand-register companion
- [x] `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md`: all eight sub-changes applied — description re-scoped (a); step 4 updated (b); anti-pattern updated (c); step 6 path changed to `brand-register.md` (d); step 3 content-brief coupling removed (g); boundary note added (h); `communication_mode: product-copy` no longer in step 3 body
- [x] `packs/experience-design/.apm/skills/tone-of-voice/references/agentbundle-layout.md`: slug examples changed to `brand-register.md` convention (e); `surface:` per-surface field removed or replaced with `scope: brand-level` (f)
- [x] The five per-surface tone-of-voice eval queries enumerated in Objective §5 are `should_trigger: false` in `packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json`; five brand-level queries remain `should_trigger: true`
- [x] `packs/product-engineering/pack.toml` version is `0.13.3`; `docs/product/changelog.md` `[Unreleased]` section updated with entries for experience-design 2.0.0 and product-engineering 0.13.3
- [x] `packs/product-engineering/.claude-plugin/plugin.json` version is `0.13.3`
- [x] `.claude-plugin/marketplace.json` reflects `experience-design` version `2.0.0` and `product-engineering` version `0.13.3` (generated after both bumps)
- [x] `guides/experience-design/how-to/copy-boundary.md` exists; contains a decision table for `copy-direction` vs `ux-writing` vs `content-design`; mentions `tone-of-voice` as brand-register companion
- [x] `workspace.toml` `["ini-003".work].shipped` contains `"spec/xd-copy-direction"` as exact path; absent from `queue` by exact path; stale RFC-0071 decision #4 comment updated to note superseded by RFC-0062; TOML parses cleanly
- [x] `docs/rfc/0071-digital-experience-doctrine.md` has an `## Errata` section correcting the copy-direction ↔ tone-of-voice ordering error (lines 313–314) and the skill count error (line 311: 19 → 20)
- [x] `guides/experience-design/README.md` skill count updated to "19 skills"; "copy direction" added to skill inventory summary
- [x] `packs/experience-design/.apm/skills/tone-of-voice/references/copy-jtbd.md` ranking criterion 2 updated from per-surface language to brand-wide language (reads "Across all channels and surfaces this brand reaches…")

## Assumptions

- `tone-of-voice` re-scope requires eight sub-changes including step 3 content-brief coupling removal and `surface:` frontmatter field removal from agentbundle-layout.md
- `web/src/content/packs/experience-design.md` is NOT auto-generated (verified: no `generated: true` field)
- `packs/product-engineering/pack.toml` current version is `0.13.2`; target is `0.13.3` (patch — body-only change to ux-writing SKILL.md boundary note)
- RFC-0062 `Date closed: 2026-07-23` is already set — confirmed by reading the RFC file
- `xd-skill-boundaries` in workspace.toml has `needs = ["work:spec/digital-experience-contract", "work:spec/xd-copy-direction"]` (array, two deps); moving xd-copy-direction to shipped satisfies the second dependency
- The `make build-self` step must run after BOTH packs are bumped; if tasks are executed sequentially Task 3 (XD bump) then Task 4 (PE bump + build-self), the marketplace will reflect both
