# Plan: xd-design-system-foundations

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Constrained by:** RFC-0071 (D3a, D3b, D9), ADR-0038, RFC-0047 § Errata

## Approach

Single PR. All changes are file authoring and JSON/TOML edits — no runtime logic. Tasks are sequenced so each depends on the previous, with the marketplace regeneration last.

Verification: goal-based throughout (grep scoped to `.md`/`.toml` extensions, JSON validity, tool exit codes, file existence). AC2 trigger disjointness is verified as a **recorded manual QA check** — both skills' trigger phrases are enumerated below and confirmed non-overlapping. `run-pack-evals.py` is a probabilistic report-only tool and is not used as a gate.

## AC2: Trigger phrase disjointness (recorded manual check)

After implementation, both description: fields must produce disjoint trigger sets. The intended phrases are:

**design-token-taxonomy triggers:**
- "derive a token taxonomy"
- "name our tokens by semantic role"
- "derive our spacing and type scale from the direction"

**design-system-foundations triggers:**
- "apply design token foundations"
- "set up our token implementation"
- "build the design token foundation for this project"

**Near-misses (design-token-taxonomy → design-system-foundations):**
- "set up design tokens → design-system-foundations"
- "implement design tokens → design-system-foundations"

Intersection: empty. This record satisfies AC2.

## The 10 old positives (retain-or-move reference for AC20)

The pre-rename `design-system/evals/eval_queries.json` has exactly 10 `should_trigger: true` queries:

| # | Query | Re-home to |
|---|-------|-----------|
| 1 | "Derive a spacing scale from our aesthetic direction" | design-token-taxonomy |
| 2 | "Set up our design tokens and name them by role" | design-system-foundations |
| 3 | "Turn the named aesthetic direction into a design system" | design-system-foundations |
| 4 | "What should our type scale be, structurally — what ratio organizes it?" | design-token-taxonomy |
| 5 | "We have named goals; now build the token taxonomy from them" | design-token-taxonomy |
| 6 | "Establish a semantic token system for the product" | design-system-foundations |
| 7 | "Define the scale that generates both our spacing and type steps" | design-token-taxonomy |
| 8 | "How should we organize tokens so values can change without renaming everything?" | design-token-taxonomy |
| 9 | "Create the foundational design-system rules from our direction" | design-system-foundations |
| 10 | "Set up the token and scale taxonomy for our component library" | design-system-foundations |

Note: query #9 contains the substring "design-system" as natural language — this is expected and excluded from the AC10 structural sweep (scoped to `.md`/`.toml` files, not `eval_queries.json` query text).

Disposition: 5 stay in `design-token-taxonomy` (queries 1,4,5,7,8); 5 migrate to `design-system-foundations` (queries 2,3,6,9,10).

## Tasks

### Task 1 — Rename `design-system` → `design-token-taxonomy` with updated triggers, DTCG fix, and full in-pack sweep

**Depends on:** none
**Verification:** goal-based (structural files); AC2 recorded manual check

**Done when (AC1, AC2-partial, AC3, AC10, AC20-partial):**
- `packs/experience-design/.apm/skills/design-token-taxonomy/` exists; `design-system/` absent
- `design-token-taxonomy/SKILL.md` description: field has the AC2-planned triggers; "set up design tokens" absent
- "W3C Design Tokens interchange shape" absent from all files in `packs/experience-design/`
- All sibling skill structural files updated; AC10 sweep clean

**Tests:**
```bash
# AC1
ls packs/experience-design/.apm/skills/design-token-taxonomy/SKILL.md
test ! -d packs/experience-design/.apm/skills/design-system && echo "old dir absent"

# AC2 — trigger: planned phrases present; old phrase absent
grep "derive a token taxonomy" packs/experience-design/.apm/skills/design-token-taxonomy/SKILL.md
grep "design-system-foundations" packs/experience-design/.apm/skills/design-token-taxonomy/SKILL.md
python3 -c "
import re
text = open('packs/experience-design/.apm/skills/design-token-taxonomy/SKILL.md').read()
desc = [l for l in text.splitlines() if l.strip().startswith('description:')][0]
assert 'set up design tokens' not in desc, 'old trigger still in description field'
print('AC2 old-phrase check OK')
"

# AC3 — pack-wide DTCG phrase absent
python3 -c "
import subprocess
r = subprocess.run(['grep','-rl','W3C Design Tokens interchange','packs/experience-design/'], capture_output=True, text=True)
assert not r.stdout.strip(), f'stale DTCG phrase in: {r.stdout.strip()}'
print('AC3 OK')
"

# AC10 — structural files sweep (.md + .toml only, excluding eval_queries.json query text by extension)
python3 -c "
import subprocess
r = subprocess.run(
  'grep -rn \"\\bdesign-system\\b\" packs/experience-design/ --include=\"*.md\" --include=\"*.toml\" ' +
  '| grep -v design-system-foundations | grep -v design-systems | grep -v design-system-chain | grep -v design-token-taxonomy',
  shell=True, capture_output=True, text=True
)
assert not r.stdout.strip(), f'stale structural refs remain:\n{r.stdout[:500]}'
print('AC10 sweep OK')
"
```

**Approach:**
1. `git mv packs/experience-design/.apm/skills/design-system packs/experience-design/.apm/skills/design-token-taxonomy`
2. `design-token-taxonomy/SKILL.md`: update `name:`, `description:`, heading, body DTCG prose
3. `design-token-taxonomy/references/token-taxonomy-derivation.md`: replace DTCG phrase
4. `design-token-taxonomy/evals/evals.json`: update `skill_name`; remove stale DTCG assertion text
5. `design-token-taxonomy/evals/eval_queries.json`: retain 5 taxonomy positives; set 5 apply-positives to `should_trigger: false` (to be re-homed in Task 2); add near-miss negatives
6. Sibling skill sweep (structural files only): update `design-system` → `design-token-taxonomy` routing mentions in all ~16 affected SKILL.md/references files; replace DTCG phrase in README.md; update `pack.toml` and `plugin.json` description fields

---

### Task 2 — Author `design-system-foundations` skill with evals

**Depends on:** Task 1
**Verification:** goal-based; AC2 manual check completed (phrases enumerated in this plan)

**Done when (AC4, AC5, AC6, AC7, AC20):**
- `design-system-foundations/SKILL.md` exists with correct frontmatter and both mode sections
- All 4 evals files valid JSON; ≥5 positive, ≥5 negative in foundations eval_queries.json
- AC20: all 10 old positives present with `should_trigger: true` across both files

**Tests:**
```bash
ls packs/experience-design/.apm/skills/design-system-foundations/SKILL.md
grep "name: design-system-foundations" packs/experience-design/.apm/skills/design-system-foundations/SKILL.md

# AC5 — lightweight (8 terms, unambiguous)
python3 -c "
text = open('packs/experience-design/.apm/skills/design-system-foundations/SKILL.md').read().lower()
required = ['semantic color', 'typography', 'spacing', 'radius', 'focus style', 'status', 'responsive', 'component token']
missing = [t for t in required if t not in text]
assert not missing, f'missing lightweight: {missing}'
print('lightweight OK')
"

# AC5 — full mode (specific terms; light/dark not bare light)
python3 -c "
import re
text = open('packs/experience-design/.apm/skills/design-system-foundations/SKILL.md').read()
assert re.search(r'light.dark|light theme|light and dark', text, re.I), 'missing light/dark theme'
assert re.search(r'alias', text, re.I), 'missing alias layer'
assert re.search(r'anatomy', text, re.I), 'missing component anatomy'
assert re.search(r'DTCG', text), 'missing DTCG'
assert re.search(r'where practical', text, re.I), 'missing where practical'
assert re.search(r'deferred', text, re.I), 'missing deferred note'
print('full mode OK')
"

# AC6/AC7
python3 -c "
import json
q = json.load(open('packs/experience-design/.apm/skills/design-system-foundations/evals/eval_queries.json'))
pos = [x for x in q if x['should_trigger']]
neg = [x for x in q if not x['should_trigger']]
assert len(pos) >= 5 and len(neg) >= 5
print(f'{len(pos)} pos, {len(neg)} neg OK')
"

# AC20 — all 10 old positives accounted for (using plan.md hardcoded list)
python3 -c "
import json
old_positives = [
  'Derive a spacing scale from our aesthetic direction',
  'Set up our design tokens and name them by role',
  'Turn the named aesthetic direction into a design system',
  'What should our type scale be, structurally — what ratio organizes it?',
  'We have named goals; now build the token taxonomy from them',
  'Establish a semantic token system for the product',
  'Define the scale that generates both our spacing and type steps',
  'How should we organize tokens so values can change without renaming everything?',
  'Create the foundational design-system rules from our direction',
  'Set up the token and scale taxonomy for our component library',
]
dtt = json.load(open('packs/experience-design/.apm/skills/design-token-taxonomy/evals/eval_queries.json'))
dsf = json.load(open('packs/experience-design/.apm/skills/design-system-foundations/evals/eval_queries.json'))
covered = {x['query'] for x in dtt if x['should_trigger']} | {x['query'] for x in dsf if x['should_trigger']}
missing = [q for q in old_positives if q not in covered]
assert not missing, f'dropped: {missing}'
print(f'AC20 OK — all {len(old_positives)} positives covered')
"
```

**Approach:**
1. Create `design-system-foundations/SKILL.md` (lightweight + full mode, triggers from AC2 record)
2. Create `design-system-foundations/evals/eval_queries.json` with 5 re-homed positives (queries 2,3,6,9,10 verbatim from the 10-old-positives table) plus 2+ new positives, plus 5+ negatives
3. Create `design-system-foundations/evals/evals.json` with one eval covering lightweight output shape

---

### Task 3 — Update pack.toml + plugin.json (version bump + evals list)

**Depends on:** Task 1, Task 2
**Verification:** goal-based

**Done when (AC8, AC9):**
- pack.toml version `1.3.0`; evals list updated; description fields clean
- plugin.json version `1.3.0`; description fields clean

**Tests:**
```bash
python3 -c "
import tomllib, re
with open('packs/experience-design/pack.toml','rb') as f: d = tomllib.load(f)
assert d['pack']['version'] == '1.3.0'
skills = d['pack']['evals']['skills']
assert 'design-token-taxonomy' in skills and 'design-system-foundations' in skills
assert 'design-system' not in skills
desc = d['pack']['description']
stale = re.findall(r'\bdesign-system\b(?!-foundations|-token|-chain|-systems)', desc)
assert not stale, f'stale in pack.toml desc: {stale}'
assert 'W3C Design Tokens interchange' not in desc
print('pack.toml OK')
"
python3 -c "
import json, re
d = json.load(open('packs/experience-design/.claude-plugin/plugin.json'))
assert d['version'] == '1.3.0'
desc = d.get('description', '')
stale = re.findall(r'\bdesign-system\b(?!-foundations|-token|-chain|-systems)', desc)
assert not stale
assert 'W3C Design Tokens interchange' not in desc
print('plugin.json OK')
"
```

**Approach:**
1. `pack.toml`: bump version; update evals list; description already handled in Task 1 step 6
2. `plugin.json`: bump version; description already handled in Task 1 step 6 (confirm)

---

### Task 4 — Update FE genre routing

**Depends on:** Task 2
**Verification:** goal-based

**Tests:**
```bash
grep "design-system-foundations" .claude/skills/frontend-engineering/SKILL.md
grep "design-system-foundations" .agents/skills/frontend-engineering/SKILL.md
```

**Approach:** Add note to genre routing section in both FE SKILL.md files: if `design-system-foundations` has run, a token foundation exists — reference it before seeding the CSS token block.

---

### Task 5 — Add how-to guide: design-system-chain

**Depends on:** Task 2
**Verification:** goal-based

**Tests:**
```bash
ls docs/guides/experience-design/how-to/design-system-chain.md
python3 -c "
text = open('docs/guides/experience-design/how-to/design-system-chain.md').read()
for term in ['two-step', 'lightweight', 'full mode', 'design-token-taxonomy', 'design-system-foundations']:
  assert term.lower() in text.lower() or term in text, f'missing: {term}'
print('AC13 OK')
"
```

---

### Task 6 — Update pack page and journey page (web/)

**Depends on:** Task 1, Task 2
**Verification:** goal-based

**Tests:**
```bash
# AC14 — pack page
grep "design-token-taxonomy" web/src/content/packs/experience-design.md
grep "design-system-foundations" web/src/content/packs/experience-design.md
python3 -c "
import re, pathlib
text = pathlib.Path('web/src/content/packs/experience-design.md').read_text()
stale = re.findall(r'\bdesign-system\b(?!-foundations|-token|-chain)', text)
assert not stale, f'stale in pack page: {stale}'
print('AC14 OK')
"

# AC15 — journey page
grep "design-token-taxonomy" web/src/content/journeys/experience-design.md
grep "design-system-foundations" web/src/content/journeys/experience-design.md
python3 -c "
import re, pathlib
text = pathlib.Path('web/src/content/journeys/experience-design.md').read_text()
stale = re.findall(r'\bdesign-system\b(?!-foundations|-token|-chain)', text)
assert not stale, f'stale in journey page: {stale}'
print('AC15 OK')
"
```

**Approach:**
1. Pack page: replace `- design-system` → `- design-token-taxonomy`; add `- design-system-foundations`; update prose
2. Journey page: update `design-system` skill entry; add `design-system-foundations` entry; update `whatChanges` prose

---

### Task 7 — Contract drift check + build-self

**Depends on:** Tasks 1–6
**Verification:** goal-based

```bash
python3 tools/check-contract-drift.py --root .
python3 tools/build_gate_chain.py build-self --force --packs-dir packs
python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs
```

---

### Task 8 — Update workspace.toml + roadmap + specs/README.md

**Depends on:** Tasks 1–7
**Verification:** goal-based

```bash
python3 -c "
import tomllib
with open('workspace.toml','rb') as f: d = tomllib.load(f)
shipped = d['ini-003']['work']['shipped']
queue = d['ini-003']['work']['queue']
assert any('xd-design-system-foundations' in str(s) for s in shipped)
assert not any('xd-design-system-foundations' in str(s) for s in queue)
print('workspace.toml OK')
"
grep "xd-design-system-foundations" docs/product/roadmap.md
grep "xd-design-system-foundations" docs/specs/README.md
```

**Approach:**
1. workspace.toml: move entry from queue to shipped
2. docs/product/roadmap.md: add shipped entry
3. docs/specs/README.md: add Shipped row

---

## Changelog

- 2026-07-24: Plan authored (eugenelim); updated after three adversarial review passes: B1→B3: sweep scoped to .md/.toml files (excludes eval query text), DTCG pack-wide grep, README.md included; B2: run-pack-evals demoted to advisory; AC2 trigger disjointness recorded as manual check with phrase sets enumerated here; B4/C2: AC20 uses plan-hardcoded 10-item list (no git-show dependency); C3: Task 6 and AC10/AC14/AC15 regex uses \bdesign-system\b(?!-foundations|-token|-chain) with trailing \b; N4: Task 3 regex cleaned up.
