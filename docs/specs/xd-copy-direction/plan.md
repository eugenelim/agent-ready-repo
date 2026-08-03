# Plan: xd-copy-direction

- **Status:** Done <!-- Drafting | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Mode

Full — structural trigger: new public skill interface in `packs/experience-design`; also re-scopes existing `tone-of-voice` skill.

## Assumption trio

- **Files I'll touch:** `packs/experience-design/.apm/skills/copy-direction/` (new, all files), `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` (8 sub-changes), `packs/experience-design/.apm/skills/tone-of-voice/references/agentbundle-layout.md` (slug + path + surface field), `packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json` (5 queries moved), `packs/experience-design/.apm/skills/content-design/SKILL.md` (frontmatter description + step 5 body), `packs/product-engineering/.apm/skills/ux-writing/SKILL.md` (boundary note), `packs/product-engineering/pack.toml` (0.13.3), `packs/product-engineering/.claude-plugin/plugin.json` (0.13.3), `packs/experience-design/pack.toml` (2.0.0 + evals), `packs/experience-design/.claude-plugin/plugin.json` (2.0.0), `packs/experience-design/JOURNEY.md` (add entry), `web/src/content/packs/experience-design.md` (add entry), `web/src/content/journeys/experience-design.md` (regenerated), `guides/experience-design/how-to/copy-boundary.md` (new), `workspace.toml` (queue → shipped + comment update)
- **Tests that demonstrate done:** `python3 tools/lint-experience-agnostic.py` exits 0; `python3 tools/lint-web-journey-parity.py` exits 0; all AC verification commands in spec Testing Strategy pass; tone-of-voice eval migration assertion passes
- **Not changing:** loop-engine/loop-cohort scripts, lint scripts, skills outside the four boundary-note files + tone-of-voice
- **Post-review additions (codex rounds 3–5):** RFC-0062 Errata section added (Approver-signed); tone-of-voice references updated to brand-level language (copy-jtbd.md, copy-arbitration.md, plain-language-floor.md); ux-writing and content-design boundary notes updated; shipped guides updated

## Declined patterns

- Merging copy-direction and tone-of-voice — declined: distinct scopes; merging overloads tone-of-voice
- Adding VoC research as a required step — declined: RFC-0062 OQ2 says VoC is optional input
- Adding copy-direction to the `digital-experience-contract.md` template — declined: out of scope
- Bumping to 2.0.0 (major) — initially declined; reversed after codex review: tone-of-voice re-scope removes the per-surface path contract (breaking change), requiring a major bump. Final shipped version: 2.0.0.
- Moving all tone-of-voice reference files — declined: only `agentbundle-layout.md` needs the path + field fix
- Running `make build-self` in Task 3 (before PE bump) — declined: marketplace would show stale PE version; build-self must run after both packs are bumped (end of Task 4)

## Resolve-vs-surface disposition record

| Finding | Source | Disposition |
|---|---|---|
| tone-of-voice occupies same scope as RFC-0062's copy-direction | R1 B1 | Resolved: full 8-sub-change re-scope |
| ux-writing + content-design boundary notes point to tone-of-voice | R1 B2 | Resolved: four-way atomic boundary; content-design frontmatter also updated |
| tone-of-voice activation evals overlap | R1 B3 | Resolved: 5 per-surface queries enumerated + moved |
| PE pack bump needed for ux-writing edit | R1 B4 | Resolved: PE 0.13.2→0.13.3 + plugin.json + build-self |
| Testing strategy gaps | R1 C5 | Resolved: all ACs have verification commands |
| Output path and type not pinned | R1 C6 | Resolved: agentbundle-layout.md pins type: copy-direction |
| No boundary note in tone-of-voice | R1 C7 | Resolved: sub-change (h) |
| Queue-absence uses substring, collides with xd-skill-boundaries needs= | R2 B1 | Resolved: exact path equality assertion |
| plugin.json + make build-self absent | R2 B2 | Resolved: lockstep ACs + build-self in Task 4 |
| tone-of-voice re-scope too shallow | R2 B3 | Resolved: 8 sub-changes (step 4, step 6, anti-pattern, layout ref, step 3 ALL per-surface coupling including steps 3+7+8, surface field) |
| Output-path collision tov/copy-direction | R2 C4 | Resolved: tov→brand-register.md; copy-direction→surface-slug |
| content-design frontmatter description still routes to tone-of-voice | R2 C5 | Resolved: content-design frontmatter + step 5 body both updated |
| Procedure model vs artifact/layout model conflated | R2 C6 | Resolved: spec distinguishes creative-direction rhythm vs tone-of-voice artifact model |
| tone-of-voice eval migration not enumerated | R2 C7 | Resolved: 5 specific queries enumerated |
| PE version-compare lexical | R2 N8 | Resolved: exact version '0.13.3' |
| make build-self runs before PE version bump | R3 B1 | Resolved: build-self moved to end of Task 4 (after PE bump) |
| RFC-0071 decision #4 contradiction unreconciled | R3 B2 | Resolved: spec reconciliation note + workspace.toml comment update in Task 5 |
| tone-of-voice step 3 + surface: field survive re-scope | R3 B3 | Resolved: sub-changes (g) and (f) added |
| No Depends-on in plan tasks | R3 B4 | Resolved: all tasks have Depends on: field |
| AC11/AC19/AC22 have no done-when checks | R3 C5 | Resolved: done-when commands added per task |
| Cross-file eval overlap check unverifiable as worded | R3 C6 | Resolved: AC restated as "five enumerated queries are false"; mechanical assertion added |
| sub-change (g) misses steps 7 + 8 product-copy coupling | R4 B1 | Resolved: sub-change (g) enumerates all three sites; separate step-8 check added (`grep -q "section jobs and narrative arc"`) |
| editorial gate relocation has no reference home in copy-direction | R4 B2 | Resolved: 7th reference file `editorial-quality-gates.md` added to copy-direction |
| AC19 brand-level count half unverified | R4 C3 | Resolved: `assert sum(true)==5` added to tone-of-voice eval done-when |
| evals.json AC verified by existence only | R4 C4 | Resolved: Python assertion checks `skill_name` + non-empty scenarios |
| step-8 clause has no verification | R5 B1 | Resolved: `grep -q "section jobs and narrative arc"` exits non-zero added |
| ref count "6" vs "seven" inconsistency | R5 C2 | Resolved: §1 and Boundary changed to "seven" |
| steps (b)+(c) re-scope have no targeted verification | R5 C3 | Resolved: phrase-absence + anti-pattern grep added |
| ux-writing stale onboarding→tone-of-voice pointer | R5 C4 | Resolved: AC14 updated; Objective §8 names copy-direction as onboarding owner |
| onboarding grep over-broad, can false-fail correct edit | R6 C1 | Resolved: clause-scoped (`copy voice and register[^;]*tone-of-voice` absent; `onboarding.*copy-direction` present) |
| negative grep still false-fails on brand-register mention later in same line | R7 C1 | Resolved: `[^;]*` stops the greedy match at the first semicolon-delimiter; brand-register mention in later clause can't trip check |
| content-design step 5 replace-vs-augment unspecified | R3 C7 | Resolved: spec AC 16 says copy-direction replaces tov as per-surface handoff; communication_mode updated |
| Spec Assumption misstates xd-skill-boundaries dep shape | R3 C8 | Resolved: Assumption corrected to array form with both deps |
| creative-direction template claim is false | R3 N9 | Resolved: spec reason changed to "copy-focused fields" not "no template" |
| content-brief input in copy-direction unpinned | R3 N10 | Resolved: step 1 AC + manual-review check added |

## Tasks

### T1 — Copy-direction SKILL.md and reference tree

**Depends on:** none

**Verification mode:** Goal-based + manual review of procedure against spec ACs

**Done when:**
- `ls packs/experience-design/.apm/skills/copy-direction/SKILL.md` exits 0
- `ls packs/experience-design/.apm/skills/copy-direction/references/{agentbundle-layout,audience-jtbd,copy-grounding,copy-arbitration,interrogation-sequence,plain-language-floor,editorial-quality-gates}.md` exits 0
- `grep "type: copy-direction" packs/experience-design/.apm/skills/copy-direction/references/agentbundle-layout.md` hits
- `python3 tools/lint-experience-agnostic.py` exits 0
- Manual: description has three "Do NOT use" clauses; 8-step procedure present; step 1 mentions content brief as optional input; step 3 references tone-of-voice brand-register doc; step 8 names ux-writing

**Approach:**
Create `packs/experience-design/.apm/skills/copy-direction/`. Write SKILL.md following `creative-direction`'s 8-step interrogation rhythm; use `tone-of-voice`'s artifact/layout model (seven refs, `type: copy-direction`, per-surface `copy/<surface-slug>.md`). Write all seven reference files: `agentbundle-layout.md` (pins `type: copy-direction`, per-surface slug path), `audience-jtbd.md`, `copy-grounding.md`, `copy-arbitration.md`, `interrogation-sequence.md`, `plain-language-floor.md`, `editorial-quality-gates.md` (anti-AI-smell scan; invoked when upstream content brief declares `communication_mode: product-copy`).

### T2 — Assets and evals

**Depends on:** none (can run in parallel with Task 1)

**Verification mode:** Goal-based

**Done when:**
- `ls packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md` exits 0
- `python3 -c "import json,pathlib; d=json.loads(pathlib.Path('packs/experience-design/.apm/skills/copy-direction/evals/eval_queries.json').read_text()); assert sum(1 for q in d if q['should_trigger'])>=6; assert sum(1 for q in d if not q['should_trigger'])>=6"`
- `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/copy-direction/evals/evals.json')); assert d.get('skill_name')=='copy-direction' and len(d.get('evals',d.get('scenarios',[])))>0"`
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
Write `copy-direction-template.md` mirroring `tone-of-voice-template.md` format with copy-goal fields for per-surface positioning. Write `eval_queries.json` with ≥6 per-surface acquisition copy `true` entries and ≥6 `false` entries. Write `evals.json` with `skill_name: copy-direction`.

### T3 — XD pack metadata and journey/pack page updates

**Depends on:** Task 1, Task 2 (parity lint needs skill directory to exist)

**Verification mode:** Goal-based

**Done when:**
- `python3 -c "import tomllib; t=tomllib.load(open('packs/experience-design/pack.toml','rb')); assert t['pack']['version']=='2.0.0' and 'copy-direction' in t['pack']['evals']['skills']"`
- `python3 -c "import json; p=json.load(open('packs/experience-design/.claude-plugin/plugin.json')); assert p['version']=='2.0.0'"`
- `grep "copy-direction" packs/experience-design/JOURNEY.md` hits
- `grep "copy-direction" web/src/content/packs/experience-design.md` hits
- `python3 tools/lint-web-journey-parity.py` exits 0

**Approach:**
Update `pack.toml` (`copy-direction` in evals.skills, version 2.0.0). Update `.claude-plugin/plugin.json` (version 2.0.0) in lockstep. Add copy-direction entry to `JOURNEY.md` (`description` + `humanTouches: 0`). Edit `web/src/content/packs/experience-design.md` to add `copy-direction`. Regenerate `web/src/content/journeys/experience-design.md` via `python3 tools/build-site.py --journeys-only`. Do NOT run `make build-self` here — PE is not yet bumped.

### T4 — Four-way boundary updates, tone-of-voice full re-scope, PE pack bump, and how-to guide

**Depends on:** Task 3 (build-self must run after XD is already bumped)

**Verification mode:** Goal-based

**Done when:**
- `grep "copy-direction" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` hits
- `python3 -c "t=open('packs/experience-design/.apm/skills/content-design/SKILL.md').read(); fm=t.split('---')[1]; assert 'copy-direction' in fm"` hits
- `grep "copy-direction" packs/experience-design/.apm/skills/content-design/SKILL.md` hits in body line >4
- `grep "copy-direction" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` hits
- `grep "brand-register" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` hits
- `grep -c "product-copy" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` outputs `0` (steps 3 and 7 coupling removed)
- `grep -q "section jobs and narrative arc" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` exits non-zero (step 8 clause removed)
- `grep -cE "(hero headline|above-fold|taglines|announcement copy|onboarding copy voice)" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` outputs `0`
- `grep -q "brand-level copy register" packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` exits 0
- `grep -qE "copy voice and register[^;]*tone-of-voice" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exits non-zero (stale per-surface pointer removed; clause-scoped so brand-register mention later on same line is safe)
- `grep -q "onboarding.*copy-direction" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` exits 0 (copy-direction named as onboarding copy voice owner)
- `grep "brand-register" packs/experience-design/.apm/skills/tone-of-voice/references/agentbundle-layout.md` hits
- `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json')); moved=[q for q in d if 'landing page' in q['query'] or 'hero headline' in q['query'] or 'above-fold' in q['query'] or 'product launch announcement' in q['query'] or 'tagline' in q['query']]; assert all(not q['should_trigger'] for q in moved)"`
- `python3 -c "import json; d=json.load(open('packs/experience-design/.apm/skills/tone-of-voice/evals/eval_queries.json')); assert sum(1 for q in d if q['should_trigger']) == 8"`
- `python3 -c "import tomllib; t=tomllib.load(open('packs/product-engineering/pack.toml','rb')); assert t['pack']['version']=='0.13.3'"`
- `python3 -c "import json; p=json.load(open('packs/product-engineering/.claude-plugin/plugin.json')); assert p['version']=='0.13.3'"`
- `python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); xd=next(p for p in d['plugins'] if p.get('displayName')=='Experience Design'); pe=next(p for p in d['plugins'] if p.get('displayName')=='Product Engineering'); assert xd['version']=='2.0.0' and pe['version']=='0.13.3'"`
- `ls guides/experience-design/how-to/copy-boundary.md` exits 0

**Approach (all four boundary files updated atomically):**

1. Update `ux-writing/SKILL.md` boundary note: reference `copy-direction` for per-surface marketing/acquisition copy voice.
2. Update `content-design/SKILL.md`:
   - Frontmatter description: reference `copy-direction` for per-surface acquisition copy voice; `tone-of-voice` as brand-register companion.
   - Step 5 body: copy-direction replaces tone-of-voice as the per-surface handoff; `communication_mode: product-copy` consumer line updated to name copy-direction; tone-of-voice retained as brand-register companion.
3. Re-scope `tone-of-voice/SKILL.md` (all eight sub-changes):
   - (a) Frontmatter description: remove per-surface triggers; brand-level scope.
   - (b) "When to invoke" step 4: replace per-surface surface list with brand-level.
   - (c) Anti-pattern block: "brand-level copy register" phrasing.
   - (d) Step 6: output path → `copy/brand-register.md`; boundary note added.
   - (g) Steps 3 + 7 + 8: remove step 3's content-brief/`communication_mode: product-copy` paragraph; remove step 7's "For `product-copy` mode" anti-AI-smell clause; remove step 8's "if a content brief exists for this surface…section jobs and narrative arc" clause.
   - (h) Add "Do NOT use" boundary note for per-surface acquisition work.
4. Update `tone-of-voice/references/agentbundle-layout.md`:
   - (e) Slug examples → `brand-register.md`.
   - (f) Remove `surface:` per-surface field; replace with `scope: brand-level`.
5. Update `tone-of-voice/evals/eval_queries.json`: move five enumerated per-surface queries to `should_trigger: false`.
6. Bump `packs/product-engineering/pack.toml` to `0.13.3`; bump `.claude-plugin/plugin.json` to `0.13.3`.
7. Run `make build-self` — both packs are now bumped; marketplace regeneration reflects both.
8. Write `guides/experience-design/how-to/copy-boundary.md` with decision table.

### T5 — Workspace bookkeeping

**Depends on:** Task 3, Task 4 (all changes must be complete)

**Verification mode:** Goal-based

**Done when:**
- `python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); s=d['ini-003']['work']['shipped']; assert any(s2=='spec/xd-copy-direction' if isinstance(s2,str) else s2.get('path')=='spec/xd-copy-direction' for s2 in s)"`
- `python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); q=d['ini-003']['work']['queue']; assert not any((s if isinstance(s,str) else s.get('path',''))=='spec/xd-copy-direction' for s in q)"`
- `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0

**Approach:**
Move `spec/xd-copy-direction` from `["ini-003".work].queue` to `["ini-003".work].shipped` using comment-preserving text edit (not tomllib round-trip). Update the stale RFC-0071 decision #4 comment (workspace.toml ~line 160) to append: "SUPERSEDED: RFC-0062 Accepted 2026-07-23; copy-direction implemented as a full new skill per RFC-0062 design — see queue entry below."
