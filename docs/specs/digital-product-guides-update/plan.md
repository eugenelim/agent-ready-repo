# Plan: digital-product-guides-update

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Executing | Done -->

## Approach

All changes are docs-only. Four task areas: (1) README rewrite with complete index + "Start here" walkthrough; (2) two existing how-to guides get missing cross-links; (3) web/src/content/ gets a prose mention and a skill addition; (4) workspace.toml queue move, deferred backlog entries, spec status flip, and build verification. No new files created; no skill or eval content touched; pack version stays at 1.6.0.

Task 2 depends on Task 1 (link-resolution check must cover new README links). Task 4 depends on Tasks 1–3. Tasks 1 and 3 are independent.

## Constraints

- RFC-0071: no SKILL.md body edits.
- Pack version stays at 1.6.0 (docs-only).
- Conventional Commits; no Co-Authored-By trailer; git user eugenelim.
- Journey page body is prose-only (no inline hyperlinks) — add cross-pack eval as prose.
- Do NOT touch `{slug = "digital-product-profile", needs = "ini-003:work:spec/digital-product-guides-update"}` in `[backlog].open` (workspace.toml:1064); this is a valid dependency reference.

## Construction tests

Cross-cutting: Python link-resolution check (in Task 4) covers all files under `docs/guides/experience-design/` after all edits are complete.
Manual QA: cold read of "Start here" section after Task 1 is done.

## Design (LLD)

Not applicable — no code or structural change.

## Risks

Low. All changes are additive markdown edits. The workspace.toml queue move is verified with `tomllib.load`.

## Tasks

### Task 1 — Rewrite `docs/guides/experience-design/README.md`

**Depends on:** none

**Tests:**
- `grep -F "the-experience-thread.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "author-design-intent.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "copy-layer-boundary.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "design-review.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "design-system-chain.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "page-archetypes.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "run-cross-pack-eval.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "reference/experience-design.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -F "state-coverage.md" docs/guides/experience-design/README.md` ≥ 1
- `grep -c "Start here" docs/guides/experience-design/README.md` ≥ 1
- `grep -c "21 skills" docs/guides/experience-design/README.md` ≥ 1
- `grep -c "18 skills" docs/guides/experience-design/README.md` = 0
- Manual QA: "Start here" cold read — seven numbered phases in chain order, each with a link to the right how-to.

**Mode:** Goal-based check + manual QA

**Approach:**
Rewrite `docs/guides/experience-design/README.md`. Preserve the file's overall structure (intro, sections, footer).

1. **Update intro paragraph:**
   - Replace "18 skills" with "21 skills"
   - Update skill enumeration: replace "design system" with "design-token-taxonomy and design-system-foundations"
   - Keep framework-agnostic method language and standards citations intact

2. **Add `## Start here` section** immediately after the intro, before other sections:
   ```markdown
   ## Start here

   New here? The XD chain runs in this order:

   1. **Discover** — map the customer journey, content intent, and copy voice goals
      → [Thread a feature from journey to screens](how-to/author-design-intent.md)
   2. **Define** — derive the screen flow and design principles
      → [Thread a feature from journey to screens](how-to/author-design-intent.md)
   3. **Design intent** — establish aesthetic direction and apply the token foundation
      → [Derive a token taxonomy and apply the design token foundation](how-to/design-system-chain.md)
   4. **Design each screen** — identify the page archetype, then apply IA, genre-specific structure, and interaction patterns
      → [Page archetypes: when to use which](how-to/page-archetypes.md)
   5. **Self-review** — run the three-pass design-review before the independent reviewer
      → [Run a design review before the independent pass](how-to/design-review.md)
   6. **Independent review** — `experience-reviewer` reviews the full screen set in forked context
   7. **Quality floor** — all 18 states required across every screen
      → [State coverage reference — the 18-state set](reference/state-coverage.md)
   ```

3. **Reorganize guide listings** under phase-aligned headers, keeping all existing content:

   **## Explanation**
   - [The experience thread](explanation/the-experience-thread.md)

   **## How-to**
   Organized by XD chain phase:
   - *Connective thread (discover → define)*: [Thread a feature from journey to screens](how-to/author-design-intent.md)
   - *Design intent*: [Derive a token taxonomy and apply the design token foundation](how-to/design-system-chain.md)
   - *Surface design*: [Page archetypes: when to use which](how-to/page-archetypes.md)
   - *Review*: [Run a design review before the independent pass](how-to/design-review.md)
   - *Copy and content*: [The three-way copy boundary: copy-direction, ux-writing, and content-design](how-to/copy-layer-boundary.md)
   - *Cross-pack*: [How to run the cross-pack experience eval](how-to/run-cross-pack-eval.md)

   **## Reference**
   - [The skills, the reviewer, and the quality-floor](reference/experience-design.md)
   - [State coverage reference — the 18-state set](reference/state-coverage.md)

4. **Keep the footer:** `Installing and upgrading live in [`../_shared/`](../_shared/).`

**Done when:** all 12 test greps pass and manual QA cold read passes.

---

### Task 2 — Add missing cross-links to how-to guides

**Depends on:** Task 1 (link-resolution check in Task 4 must cover README links and guide links together)

**Note:** The following cross-links are already present in the files and require no edits:
- `design-review.md → ../reference/state-coverage.md` (lines 13, 141)
- `page-archetypes.md → information-architecture` (lines 11, 13, 124)
- `copy-layer-boundary.md → tone-of-voice` (line 84)

**Tests (all start red — 0 matches before edits):**
- `grep -F "](author-design-intent.md)" docs/guides/experience-design/how-to/design-system-chain.md` ≥ 1
- `grep -F "](design-system-chain.md)" docs/guides/experience-design/how-to/author-design-intent.md` ≥ 1
- `grep -F "](page-archetypes.md)" docs/guides/experience-design/how-to/author-design-intent.md` ≥ 1

**Mode:** Goal-based check

**Approach:**

1. **`how-to/design-system-chain.md`** — Read the file. At the natural conclusion of the guide, add:
   ```markdown
   ## See also

   - [Thread a feature from journey to screens](author-design-intent.md) — the full XD chain context in which this two-step token chain sits.
   ```

2. **`how-to/author-design-intent.md`** — Read the file. Locate step 3 (design intent / creative direction + design system). Add one sentence:
   - "For the two-step token chain in detail, see [Derive a token taxonomy and apply the design token foundation](design-system-chain.md)."
   Locate step 4 (information architecture). Add one sentence:
   - "To identify the right page archetype before designing hierarchy, see [Page archetypes: when to use which](page-archetypes.md)."

**Done when:** all three link-shaped greps pass.

---

### Task 3 — Update `web/src/content/journeys/` and `web/src/content/packs/`

**Depends on:** none

**Tests:**
- `grep -c "cross-pack eval\|cross-pack experience eval" web/src/content/journeys/experience-design.md` ≥ 1
- `grep -c "experience-status" web/src/content/packs/experience-design.md` ≥ 1
- `grep -c "21 skills" web/src/content/packs/experience-design.md` ≥ 1
- `grep -c "20 skills" web/src/content/packs/experience-design.md` = 0

**Mode:** Goal-based check

**Approach:**

1. **`web/src/content/journeys/experience-design.md`** — In step 5 ("Review independently"), after the `- **Output:**` line, add:
   ```
   - **Cross-pack chain validation:** to validate the full cross-pack chain — strategy through rendered evidence — run the cross-pack experience eval after the independent review is clean.
   ```
   (Prose only; no inline hyperlink — consistent with existing link-free body style.)

2. **`web/src/content/packs/experience-design.md`** — Two edits:
   - Add `- experience-status` to the `skills:` YAML list (after `workspace-design` or at a logical position near the other status-oriented skills).
   - In the prose description paragraph, replace "20 skills" with "21 skills".

**Done when:** all four test greps pass.

---

### Task 4 — workspace.toml, spec status, and build verification

**Depends on:** Tasks 1, 2, 3

**Tests:**
- `python3 -c "import tomllib; f=open('workspace.toml','rb'); data=tomllib.load(f); q=data['ini-003']['work']['queue']; assert not any('digital-product-guides-update' in (str(e)) for e in q), 'still in queue'"` exits 0
- `python3 -c "import tomllib; d=tomllib.load(open('workspace.toml','rb')); assert any('digital-product-guides-update' in str(e) for e in d['ini-003']['work']['shipped'])"` exits 0
- `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` exits 0
- `grep -c "xd-cross-pack-tutorial" workspace.toml` ≥ 1
- `grep -c "xd-cross-pack-intent-index" workspace.toml` ≥ 1
- `grep -c "digital-product-profile" workspace.toml` ≥ 1 (confirm backlog reference preserved)
- Python link-resolution check (see below) exits 0
- `grep "Status.*Shipped" docs/specs/digital-product-guides-update/spec.md` ≥ 1
- `grep -c "^\- \[x\]" docs/specs/digital-product-guides-update/spec.md` = 9 and `grep -c "^\- \[ \]" docs/specs/digital-product-guides-update/spec.md` = 2
- `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs` exits 0

**Mode:** Goal-based check

**Approach:**

1. **`workspace.toml`** — Targeted edits (read the file section by section; do not truncate):
   - In `["ini-003".work].queue`: remove the line `{path = "spec/digital-product-guides-update", needs = "work:spec/cross-pack-experience-eval"},`
   - In `["ini-003".work].shipped`: add `"spec/digital-product-guides-update",  # Shipped 2026-07-24`
   - In `[backlog].open`: add two entries (keeping `{slug = "digital-product-profile", needs = "ini-003:work:spec/digital-product-guides-update"}` intact):
     ```toml
     # Cross-pack tutorial deferred from ini-003 M6. End-to-end tutorial showing the full
     # strategy→PE→XD→FE→review→measurement arc using a realistic digital product example.
     # Unblocks when all M1–M6 specs ship and the skill set is final.
     {slug = "xd-cross-pack-tutorial", source = "spec/digital-product-guides-update AC10"},
     # Cross-pack intent index deferred from ini-003 M6. "I want to…" → which pack +
     # skill + guide for each common adopter starting job. Unblocks when all M1–M6 specs ship.
     {slug = "xd-cross-pack-intent-index", source = "spec/digital-product-guides-update AC11"},
     ```

2. **Python link-resolution check** — run inline after workspace.toml edits:
   ```python
   import os, re
   base = "docs/guides/experience-design"
   errors = []
   for root, _, files in os.walk(base):
       for f in files:
           if not f.endswith(".md"): continue
           path = os.path.join(root, f)
           text = open(path, encoding="utf-8").read()
           for m in re.finditer(r'\]\(([^)#\s]+\.md)', text):
               target = m.group(1)
               abs_target = os.path.normpath(os.path.join(root, target))
               if not os.path.exists(abs_target):
                   errors.append(f"{path}: broken link → {target}")
   if errors:
       for e in errors: print(e)
       raise SystemExit(1)
   print("All links resolve")
   ```

3. **`docs/specs/digital-product-guides-update/spec.md`**:
   - Change `- **Status:** Implementing` to `- **Status:** Shipped`
   - Set ACs #1–#9 to `[x]` (lines starting with `- [ ]` for the non-deferred ACs)
   - Leave ACs #10 and #11 as `- [ ]` with their `(deferred: ...)` markers

4. Run `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"`.

5. Run `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs` (regression guard; docs changes do not affect build-self output, but the check confirms no accidental drift).

**Done when:** all 10 tests pass.

## Changelog

- 2026-07-24: Initial plan authored. Docs-only; 4 tasks; no pack bump.
- 2026-07-24: Revised after adversarial-reviewer passes 1–3. Removed pre-existing cross-link tasks (state-coverage, IA, tone-of-voice already linked). Added deferred backlog entries. Tightened verification to per-file identity greps and link-shaped greps. Added Python link-resolution check. Added workspace.toml preservation guard for digital-product-profile reference. Added AC [x]-marking step to Task 4.
