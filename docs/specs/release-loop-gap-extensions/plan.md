# Plan: release-loop-gap-extensions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Self-coverage disposition record

**Resolve:** All fidelity-ladder levels and their properties are specified in RFC-0074
(grounded by ecosystem evidence — Testcontainers, LocalStack, vCluster, AWS multi-account
patterns). The fleet manifest schema, e2e host repo definition, and deploy sequencing
vocabulary are specified in RFC-0075 (grounded by release-please, Flux/ArgoCD patterns).
Both RFCs are self-contained; no additional domain-grounding check fires.

**Surface (irreducible):** The L4/L4+ "requires policy audit" claim is judgment-sensitive —
an implementing agent must assess whether the adopter's cluster network policies are correctly
scoped. This is acknowledged in RFC-0074's Drawbacks section and surfaced explicitly in the
qualification section's boolean test. It cannot be made self-evident by doctrine alone; the
surface is the correct response.

**Declined patterns (named at PLAN, binding at REVIEW):**

- *Tempted to create a standalone `fidelity-ladder` skill.* Declining — the reference module
  is consumed by `work-loop` and `release-loop`; it is not user-invocable. A skill with
  a `description:` frontmatter field would appear in the skill catalogue, which is incorrect.
- *Tempted to extend `environment-isolation.md` inline.* Declining — that module is REVIEW
  (does this environment meet the bar?); the fidelity-ladder is EXECUTE/QUALIFY (how to build
  one that does). Conflating them corrupts the role distinction that the rest of the
  `operational-safety/references/` directory maintains.
- *Tempted to create a `fleet-manifest.md` reference file in `release-engineering`.* Declining
  — the fleet manifest schema has exactly one consumer today (the Polyrepo topology section).
  Extracting to a reference file before a second consumer appears is premature.
- *Tempted to add a coordinator script for fleet manifest assembly.* Declining — ADR-0031
  prohibits new executables; the fleet assembly is a bot PR / CI workflow, which is
  adopter toolchain, not a skill artifact.

## Tasks

### T1 — Create `packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md`

**Depends on:** none
**Verification mode:** Visual / manual QA (reference module is a user-consumed artifact; structural
  presence verified by test -f and grep AC1–AC4)
**Done when:** File exists; AC1 (`test -f`), AC2 (7+ level entries), AC3 (three provability
  classes), AC4 (three qualification dimensions) all pass.

**Approach:**
Create the file as an EXECUTE/QUALIFY module (not REVIEW — no frontmatter `description:`
field; this is a reference file, not a skill). Structure:
- Opening: module role (EXECUTE/QUALIFY; loaded when the agent chooses a local-infra-equivalent
  or qualifies an ephemeral environment for the outer loop); distinction from
  `environment-isolation.md` (which is REVIEW).
- Seven-level ladder table: columns — Level, Name, Technology examples, Coverage, Isolation
  provability; rows L0–L3 (inner-loop) and L4/L4+/L5/L6 (outer-loop boundary and above).
  Mark L0–L3 as inner-loop, L4+ as outer-loop.
- Per-level descriptors (structured text blocks matching RFC-0074 §fidelity-ladder-specification):
  Level, Coverage, Isolation, Gaps, Use when, Budget (where applicable), Note/Qualification.
- LocalStack license note (March 2024 commercial license change; harness-neutral stance).
- Inner-loop budget heuristic (sub-5-minute rule; L0–L1 always; L2–L3 ceiling).
- The three-dimension outer-loop qualification test (table: Dimension / Condition / How to test).
- Provability classification section: self-evident / requires-policy-audit /
  programmatically-auditable; which levels map to each class.
- L5 floor section: why L5 is the minimum; what "correctly configured" means in three boolean
  conditions; L4/L4+ conditional qualification via policy audit.

**Tests (goal-based):**
```bash
test -f packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -c "^Level: L" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
# expected: 8 (L0, L1, L2, L3, L4, L4+, L5, L6)
grep -i "self-evident" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -i "requires policy audit\|requires-policy-audit" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -i "programmatically auditable\|programmatically-auditable" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -i "prod reachability" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -i "data isolation" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
grep -i "inter-env isolation\|inter.env isolation" packs/core/.apm/skills/operational-safety/references/fidelity-ladder.md
```

---

### T2 — Add fidelity-ladder section to `packs/core/.apm/skills/work-loop/SKILL.md`

**Depends on:** none (independent file; can run concurrently with T1)
**Verification mode:** Visual / manual QA (skill content; grep AC5)
**Done when:** A "fidelity ladder" or "Fidelity ladder" heading exists in SKILL.md after
  `## Anti-patterns to refuse`; section cross-references the fidelity-ladder module; section
  contains the "push up the ladder" budget heuristic and level tokens L0 and L5.

**Approach:**
Append a new `## Fidelity ladder` section after the existing `## Anti-patterns to refuse`
section (currently the last section at line ~912). Section content per RFC-0074 D3:
- When to consult (when the task needs local-infra-equivalents).
- Brief summary of the seven levels with the inner-loop budget heuristic (sub-5 min floor).
- Cross-reference pointer: "The full ladder specification — level descriptors, isolation
  provability classifications, and the outer-loop qualification test — is in
  `operational-safety/references/fidelity-ladder.md`."
- The "push up the ladder" heuristic: prefer the highest fidelity level that fits the budget;
  L0–L1 are always in-loop; L2–L3 are the inner-loop ceiling for most services; L4 and above
  are CI-managed (outer-loop territory).
- Build-pack handoff note: when a build pack ships a fidelity-ladder scaffold reference, that
  replaces this section's ladder detail — note the hook point explicitly.

**Tests (goal-based):**
```bash
grep -i "## Fidelity ladder\|## fidelity" packs/core/.apm/skills/work-loop/SKILL.md
grep -i "fidelity-ladder.md" packs/core/.apm/skills/work-loop/SKILL.md
# expected: at least one match (cross-reference)
grep "sub-5\|push up" packs/core/.apm/skills/work-loop/SKILL.md
# expected: heuristic text present
grep "L0\|L5" packs/core/.apm/skills/work-loop/SKILL.md
# expected: level tokens present
```

---

### T3 — Add two new sections to `release-loop/SKILL.md`

**Depends on:** none (independent file from T1/T2; but both sections go in the same file,
  so author sequentially in one edit pass)
**Verification mode:** Visual / manual QA (skill content; grep AC6, AC9–AC11)
**Done when:** Both sections exist in the file; all grep checks for AC6, AC9, AC10, AC11 pass.

**Approach:**
Append two new `##` sections after the existing `## Artifact provenance verification` section
(currently the last section, ending around line 590):

**Section A: `## Ephemeral environment qualification`** (RFC-0074 D5)
- When to run: at outer-loop cycle start, before the collect phase (or infra-apply in the
  mono-component case).
- The L5 floor statement: "An ephemeral environment must meet L5 (dedicated cloud account
  / project, or a k8s namespace or vCluster that has passed the three-dimension policy
  audit) for the 'reversible' label to hold under the minimum-regret carve. An environment
  below this floor is a consent-gate crossing — surface to human; do not proceed with
  autonomous deploy."
- The three qualification dimensions (table: Dimension / Condition / How to test), matching
  the fidelity-ladder module exactly.
- The provability classification summary (self-evident / requires-audit / programmatically-
  auditable) with which action each class requires at cycle start.
- L4/L4+ conditional path: qualifies only after a policy audit per the requires-audit class;
  absent the audit, treat as a consent gate.
- Pointer to `operational-safety/references/fidelity-ladder.md` for the full ladder and
  level descriptors.

**Section B: `## Polyrepo topology`** (RFC-0075 D1–D5)
- Single-component (monorepo) case: collect phase is a no-op; no fleet manifest needed.
- Fleet manifest (`release-fleet.yaml`) schema block with all mandatory fields:
  `schema_version`, `fleet_name`, `assembled_at`, `components[]` (name, repo, g4_package_ref,
  image_ref), `deploy_sequence[]` (component, depends_on, gate), `e2e_suite_ref`.
- Courier snapshot discipline note: the fleet manifest is the courier snapshot; `g4_package_ref`
  is the version-pinned authority pointer; neither the fleet manifest nor the host repo forks
  component G4 packages.
- Canonical e2e host repo definition (Must contain / Must NOT contain / Must install).
- Five-term vocabulary table (Component / Stage / Gate / Depends-on / Release manifest)
  with orchestrator mapping columns (ArgoCD / Flux / Spinnaker + GHA).
- Collect-then-validate pre-deploy step specification (pseudocode block): for each component
  in fleet_manifest.components — fetch g4_package_ref, run RFC-0072 D6 provenance check,
  confirm image_ref consistency; on all-pass → advance to infra-apply; on any failure →
  surface to human.
- ADR-0022 distinction note: "ADR-0022 covers the product-engineering meta-repo for feature
  coordination; this mechanism covers the release-loop's cross-repo coordination — parallel
  but distinct."
- Triggering conventions (bot PR approach vs. scheduled reconciliation).

**Tests (goal-based):**
```bash
grep -i "## Ephemeral environment qualification\|## ephemeral" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep "L5" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "consent gate" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -c "Prod reachability\|Data isolation\|Inter-env isolation" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: 3
grep -i "## Polyrepo topology\|## polyrepo" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep "schema_version" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep "fleet_name\|assembled_at\|g4_package_ref\|deploy_sequence\|image_ref\|e2e_suite_ref" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: all present
grep -i "collect" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "infra-apply" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep "provenance" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "must not contain\|no component source" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -c "Component\|Stage\|Gate\|Depends-on\|Release manifest" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "courier snapshot" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "does not fork\|never fork\|read-only reference" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep -i "requires policy audit\|requires-policy-audit" packs/release-engineering/.apm/skills/release-loop/SKILL.md
grep "L4+" packs/release-engineering/.apm/skills/release-loop/SKILL.md
```

---

### T4 — Add cross-reference notes to `docs/specs/release-loop/spec.md`

**Depends on:** none (independent file — cross-reference markers point at RFC numbers, not at skill content)
**Verification mode:** goal-based (grep AC7, AC12)
**Done when:** RFC-0074 appears near AC3 and AC10(h) (at least 2 matches); RFC-0075 appears
  near AC9 (at least 1 match).

**Approach:**
For AC3 in `docs/specs/release-loop/spec.md`: append `(→ RFC-0074 for the qualification test
and provability classification)` or equivalent after the AC's final sentence.
For AC10(h): append `(→ RFC-0074 D2 / D5 for the isolation floor and the three-dimension test)`.
For AC9: append `(→ RFC-0075 for the fleet manifest schema, e2e host repo definition, and
deploy sequencing vocabulary)`.
No AC text changes — these are additive reference markers.

**Tests (goal-based):**
```bash
grep -c "RFC-0074" docs/specs/release-loop/spec.md
# expected: ≥ 2
grep "RFC-0075" docs/specs/release-loop/spec.md
# expected: ≥ 1
```

---

### T5 — Version bumps, changelog, build-self, lint gates, mark spec shipped + RFCs Accepted

**Depends on:** T1, T2, T3, T4
**Verification mode:** goal-based
**Done when:** Both packs at their new versions; changelog updated; build-self exits 0;
  all lint gates pass; this spec's Status is Shipped and all ACs checked; both RFCs Accepted.

**Approach:**
1. Edit `packs/core/pack.toml`: `version = "0.15.4"` → `"0.15.5"`
2. Edit `packs/core/.claude-plugin/plugin.json`: `"version": "0.15.4"` → `"0.15.5"`
3. Edit `packs/release-engineering/pack.toml`: `version = "0.1.5"` → `"0.1.6"`
4. Edit `packs/release-engineering/.claude-plugin/plugin.json`: `"version": "0.1.5"` → `"0.1.6"`
5. Add `[Unreleased]` changelog entries to `docs/product/changelog.md`:
   - `core` 0.15.5: new `fidelity-ladder` reference module in `operational-safety`; new
     fidelity-ladder section in `work-loop`.
   - `release-engineering` 0.1.6: new ephemeral environment qualification section and
     Polyrepo topology section in `release-loop`.
6. Fix RFC-0074 wording before Accepted flip: change "six-level" → "seven-level" in reviewer
   brief (line ~38 and ~52) and goals section (line ~167); change "L4 floor" → "L5 floor" in
   the Ask/Answer paragraph (line ~121) and goals section (line ~168); change "minor version
   bump" → "patch version bump" in the Reviewer brief Change-if-accepted and Follow-on
   artifacts sections.
7. Fix RFC-0075 wording: change "minor version bump" → "patch version bump" in the Reviewer
   brief Change-if-accepted and Follow-on artifacts sections.
8. Set RFC-0074 Status: Accepted + Date closed: 2026-07-27
9. Set RFC-0075 Status: Accepted + Date closed: 2026-07-27
10. Run `make build-self`
11. Run `make build-check`
12. Run `python tools/lint-agents-md.py`
13. Set this spec Status: Shipped; mark AC1–AC16 `[x]`

**Tests (goal-based):**
```bash
grep 'version = "0.15.5"' packs/core/pack.toml
grep '"version": "0.15.5"' packs/core/.claude-plugin/plugin.json
grep 'version = "0.1.6"' packs/release-engineering/pack.toml
grep '"version": "0.1.6"' packs/release-engineering/.claude-plugin/plugin.json
make build-check
python tools/lint-agents-md.py
```
