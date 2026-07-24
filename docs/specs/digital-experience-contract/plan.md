# Plan: digital-experience-contract

## Mode
Full (structural change + multi-feature risk triggers)

## Tasks

### Task 1 — Author and place the four contract template copies + build-self
**Depends on:** none
**Verification mode:** goal-based
**Done when:**
- `find packs/*/\.apm -name "digital-experience-contract.md" | wc -l` returns 4
- `grep -c "^###" packs/experience-design/.apm/skills/design-review/references/digital-experience-contract.md` returns 32
- `diff packs/product-strategy/.apm/skills/synthesize-stakeholder-research/references/digital-experience-contract.md packs/core/.apm/skills/frontend-engineering/references/digital-experience-contract.md` exits 0
- `ls .claude/skills/frontend-engineering/references/digital-experience-contract.md` exists (post build-self)

**Approach:**
1. Create `packs/core/.apm/skills/frontend-engineering/references/` directory (new)
2. Write the canonical template once (see spec Template Schema table for exact field order, owner tags, and tiers)
3. Copy byte-for-byte to all four anchor paths
4. Run `make build-self FORCE=1` to project the core copy to `.claude/skills/frontend-engineering/references/digital-experience-contract.md`
5. Verify `git status` shows the projected file as new

**Template structure (must match exactly):**

```
---
schema-version: "1.0"
risk-tier: explore     # explore | pilot | production
product-slug: <replace-with-product-slug>
---

<!-- Digital Experience Contract
     Owner map: each section is owned by one discipline. Skills in that pack
     fill their section; skills in other packs may READ all sections.
     Skills must not silently rewrite another discipline's section — mark
     proposed changes with a [provisional — <pack> not installed] label and
     state what specialist work remains.
     Graceful capability detection: if a required skill is not installed,
     perform the smallest safe fallback, label the output provisional, and
     name what specialist work remains.
-->

# Digital Experience Contract: <replace-with-product-slug>

## Strategy [owner: product-strategy]

### Target User and Context
<!-- Required: explore+ -->
<!-- Who the product is for; their situation; what they are trying to accomplish -->

### Diagnosis and Strategic Choices
<!-- Required: explore+ -->
<!-- What is broken or underserved; the choices made and what was ruled out -->

### Adoption Hypothesis
<!-- Required: explore+ -->
<!-- First-success event: the one action that proves first value
     Repeat-value behavior: what brings the user back -->

### Value Loop
<!-- Required: explore+ -->
<!-- How value compounds with each successive use; the reinforcing mechanism -->

### Metric Tree
<!-- Required: pilot+ -->
<!-- The causal chain from user behavior to outcome; north-star metric + leading indicators -->

### Differentiation
<!-- Required: pilot+ -->
<!-- What this product does distinctly; the mechanism of the moat -->

### Assumptions and Kill Criteria
<!-- Required: explore+ -->
<!-- Core bets; what would falsify each; kill threshold per assumption -->

## Product Engineering [owner: product-engineering]

### Opportunity and Bet
<!-- Required: explore+ -->
<!-- The problem being addressed; the bet made; evidence base (lightweight at explore) -->

### Evidence Ladder
<!-- Required: explore+ -->
<!-- Each claim classified: observed | supported | inferred | assumed | unknown -->

### First-Success Operationalization
<!-- Required: explore+ -->
<!-- Concretely what first success looks like end-to-end for one user -->

### Thin Slice
<!-- Required: pilot+ -->
<!-- One user can: begin a real task, reach a meaningful result,
     encounter and recover from one material failure, produce instrumentation -->

### Capabilities
<!-- Required: pilot+ -->
<!-- What the product must do to deliver the thin slice and first success -->

### Rollout and Recovery Plan
<!-- Required: pilot+ -->
<!-- Staged rollout; support plan; rollback trigger; recovery path -->

### Learning Plan
<!-- Required: pilot+ -->
<!-- What signals confirm or refute the bet; review cadence; decision thresholds -->

## Experience Design [owner: experience-design]

### Primary Journey
<!-- Required: explore+ -->
<!-- The end-to-end user journey from first contact to first-success event -->

### Surface Map
<!-- Required: pilot+ -->
<!-- Every surface in the product; surface type per page-archetypes taxonomy -->

### Information Architecture
<!-- Required: pilot+ -->
<!-- Structure, hierarchy, navigation, wayfinding -->

### Content Hierarchy
<!-- Required: pilot+ -->
<!-- What the product must say at each surface; content brief references -->

### Product Objects
<!-- Required: pilot+ -->
<!-- The core objects the user acts on; their identity, relationships, states -->

### Interaction and Attention Model
<!-- Required: production+ -->
<!-- How the user moves through the product; what the product draws attention to -->

### States and Permissions
<!-- Required: pilot+ -->
<!-- All states per quality-floor (18-state set); permission matrix per surface -->

### Responsive Behavior
<!-- Required: production+ -->
<!-- Breakpoint strategy; cross-channel continuity -->

### Design System Reference
<!-- Required: pilot+ -->
<!-- Which token taxonomy and design-system-foundations output this surface uses -->

## Frontend Engineering [owner: core]

### Prototype or Representation
<!-- Required: explore+ -->
<!-- Earliest rendered evidence: wireframe, clickable prototype, or first built surface.
     At explore tier: a static mockup or prototype is sufficient. -->

### Implemented Behavior
<!-- Required: production+ -->
<!-- What the built surface does; how it matches the design contract above -->

### Accessibility Evidence
<!-- Required: pilot+ -->
<!-- Pilot: accessibility requirements stated; known a11y gaps listed.
     Production: complete WCAG 2.2 AA audit; automated + manual results. -->

### Browser Behavior
<!-- Required: production+ -->
<!-- Baseline Widely Available browser matrix; per-browser test results -->

### Performance
<!-- Required: production+ -->
<!-- LCP / INP / CLS at p75 (mobile + desktop separately where field data exists).
     Asset budget: JS, images, fonts, third-party scripts. -->

### Security and Privacy
<!-- Required: production+ -->
<!-- Data handled; privacy controls; security review status -->

### Reliability
<!-- Required: production+ -->
<!-- Error rates; SLOs; monitoring and alerting; recovery path -->

### Instrumentation
<!-- Required: pilot+ -->
<!-- Events tracked; dashboards; how learning-plan signals are measured.
     Production: measurement dashboard confirmed live. -->

### Rendered Evidence
<!-- Required: pilot+ -->
<!-- Screenshot, recording, or live URL of the rendered and working surface.
     Production: must be the deployed, live surface — not a staging snapshot. -->
```

---

### Task 2 — Create `tools/check-contract-drift.py` and `tools/test-check-contract-drift.py`
**Depends on:** Task 1 (needs the canonical structure)
**Verification mode:** TDD
**Done when:** `python tools/test-check-contract-drift.py` exits 0 (nine test trees)

**Drift check algorithm:**
1. Open each of the four anchor files; if any is missing → exit 1, name the path
2. Read all four as bytes
3. If all four are byte-identical → exit 0 (fast path)
4. Otherwise, fall back to structural fingerprint comparison to produce a named diagnosis:
   a. Parse `schema-version` from the YAML frontmatter of each file using:
      `re.search(r'^schema-version:\s*"([^"]+)"', frontmatter_block, re.MULTILINE)`
      — if no match, exit 1 with "no parseable schema-version in <pack>"
   b. Extract structural fingerprint: scan lines for h2 headers (`^## `), h3 headers (`^### `),
      and `<!-- Required: ` lines following an h3 (the tier for the preceding field)
   c. Compare all four fingerprints against the first; for any divergence, name:
      the pack, the position (index), what was expected (from pack 1), and what was found
5. Exit 1 with diagnosis

**Test trees (nine, matching spec Testing Strategy Trees A–I):**
- A: four identical copies → exit 0
- B: one copy has `schema-version: "2.0"` → exit 1, names pack
- C: one copy has `<!-- Required: pilot+ -->` where others have `<!-- Required: explore+ -->` → exit 1, names field and tier
- D: one copy missing the `<!-- Required: ... -->` annotation on one field → exit 1, names the field
- E: one copy has an extra h3 not in others → exit 1, names the extra header
- F: one copy is missing an h3 that the others have → exit 1, names the missing field
- G: one file missing from disk → exit 1, names the path
- H: one copy has h3s in different order → exit 1, names the position mismatch
- I: one copy has no parseable frontmatter block → exit 1, clean error (no uncaught exception)

---

### Task 3 — Create explanation guide
**Depends on:** none (parallel with Tasks 1–2)
**Verification mode:** goal-based
**Done when:**
- `docs/guides/core/explanation/digital-experience-contract.md` exists
- `grep "^## " docs/guides/core/explanation/digital-experience-contract.md` returns: The contract, The three tiers, The ownership map, Graceful capability detection

**Approach:** Diátaxis explanation page. Audience: adopter who just installed one of the four packs and wants to understand the contract concept. Content:
- **The contract** — the "locally polished, globally broken" problem; why a shared schema; what it is (a markdown template, a blank form, not a ceremony)
- **The three tiers** — table from the spec (tier / when / what's required); emphasize that explore mode is intentionally lightweight
- **The ownership map** — which discipline fills which section; the read-all / write-own rule
- **Graceful capability detection** — what happens when a required skill isn't installed (provisional label; state remaining work; no phantom handoff)
- One-line pointer to RFC-0071 for governance detail (no link — just cite by number)
- One-line reference to each of the four pack journey pages using their MkDocs path

---

### Task 4 — Add journey page cross-references
**Depends on:** none (parallel with Tasks 1–3)
**Verification mode:** goal-based
**Done when:**
- `grep "Digital Experience Contract" web/src/content/journeys/product-strategy.md` hits
- `grep "Digital Experience Contract" web/src/content/journeys/experience-design.md` hits
- `grep "Digital Experience Contract" web/src/content/journeys/core.md` hits

**Approach:** Read each journey file's `whatChanges` YAML scalar value. The value is a quoted multi-sentence string. Append a sentence at the very end (inside the closing `"`). Do not rewrite existing prose. The sentence must use the phrase "Digital Experience Contract" so the goal-based grep passes. Link form: use plain text (the phrase) — no markdown link inside a YAML scalar string.

---

## Verification gate (post-EXECUTE, pre-REVIEW)

Run in order after all tasks complete:

```bash
# Gate 1: all four pack copies exist
find packs -path "*/references/digital-experience-contract.md" | sort

# Gate 2: all four copies are byte-identical
diff packs/product-strategy/.apm/skills/synthesize-stakeholder-research/references/digital-experience-contract.md \
     packs/product-engineering/.apm/skills/frame-intent/references/digital-experience-contract.md
diff packs/product-engineering/.apm/skills/frame-intent/references/digital-experience-contract.md \
     packs/experience-design/.apm/skills/design-review/references/digital-experience-contract.md
diff packs/experience-design/.apm/skills/design-review/references/digital-experience-contract.md \
     packs/core/.apm/skills/frontend-engineering/references/digital-experience-contract.md
# all three diffs → exit 0

# Gate 3: drift check self-test
python tools/test-check-contract-drift.py

# Gate 4: drift check on live copies
python tools/check-contract-drift.py --root .

# Gate 5: projected artifact committed
ls .claude/skills/frontend-engineering/references/digital-experience-contract.md

# Gate 6: guide exists with required h2s
grep "^## " docs/guides/core/explanation/digital-experience-contract.md

# Gate 7: journey cross-references
grep "Digital Experience Contract" web/src/content/journeys/product-strategy.md
grep "Digital Experience Contract" web/src/content/journeys/experience-design.md
grep "Digital Experience Contract" web/src/content/journeys/core.md

# Gate 8: no unexpected file types changed
git diff --name-only | grep -E "SKILL\.md|pack\.toml|evals" || echo "clean"
```

## Deferred (out of scope for this spec)

- `digital-experience-contract-pe-journey-xref` — PE journey page doesn't exist; deferred to `spec/product-engineering-shaping-doctrine`
- `contract-drift-check-gate-promotion` — promotion to build-check gate; deferred pending calibration evidence
