# Plan: release-loop-doctrine-gaps

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Self-coverage disposition record

**Resolve:** All six RFC-0072 sections can be derived directly from the RFC decisions
and the research evidence (Argo Rollouts, SLSA v1.2, OpenSLO v1 specs). The schema
fields, traffic defaults, and flag states are specified in the RFCs and grounded by
prior research; no additional domain-grounding check fires.

**Surface (irreducible):** The live budget consumption integration gap (RFC-0073 D5)
is not resolvable by the skill itself — the `define-slo` skill produces the SLO YAML,
but `budget_consumed_pct` must be read from the telemetry backend at gate-check time.
The skill names the instruction and the `query-failed` fallback state; the gap is
acknowledged and visible in the PRR, not silently papered over.

## Tasks

### T1 — Add six RFC-0072 doctrine sections to `release-loop/SKILL.md`
**Depends on:** none
**Verification mode:** Visual / manual QA (skill is a user-invocable artifact — the
  implementing agent exercises it by reading it; structural presence verified by grep AC1–AC6)
**Done when:** grep for six section headings in the updated SKILL.md returns 6 matches;
  all six AC1–AC6 grep checks pass.

**Approach:**
Append six new `##` sections after the existing `## Anti-patterns to refuse` section
(currently the last section, ending at line ~371). Sections:
1. `## The G4 handoff package` — `release-handoff.yaml` schema with all mandatory fields,
   tolerant-reader note, schema_version semantics.
2. `## Deploy ordering protocol` — four phases (infra-apply, service-deploy, smoke, canary)
   as the canonical ordering floor; tool field as hint; adopters may add phases.
3. `## Canary analysis defaults` — traffic steps (5%→25%→50%→100%), pause duration,
   threshold table by service class, four-outcome protocol (PROMOTE/ROLLBACK/PAUSE/HALT),
   failure limit, oscillation circuit-breaker reference (AC10(e)).
4. `## Feature flag lifecycle` — six states, four types with expected lifetimes,
   deploy→release decoupling invariant as a state-transition rule.
5. `## Rollback procedure` — service rollback (automatic; three-step verification),
   IaC rollback (non-automatic; consent gate; always-plan-before-apply); rollback
   verification protocol.
6. `## Artifact provenance verification` — SLSA L2 minimum; cosign/keyless or equivalent;
   verification before deploy; failure = consent gate crossing; three-step check.

**Tests (goal-based):**
```bash
grep -c "## The G4 handoff package\|## Deploy ordering\|## Canary analysis\|## Feature flag lifecycle\|## Rollback procedure\|## Artifact provenance verification" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: 6
grep "schema_version\|built_at\|component_manifest\|provenance_ref\|iac_plan_ref\|test_evidence_summary\|deploy_phases" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: each term appears at least once
grep "PROMOTE\|ROLLBACK\|PAUSE\|HALT" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: all four appear
grep "deployed-off\|enabled-pct\|full-rollout\|deprecated" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: all four appear
grep "SLSA\|cosign\|consent gate" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: all three appear
```

---

### T2 — Create `packs/release-engineering/.apm/skills/define-slo/SKILL.md`
**Depends on:** none (independent file creation)
**Verification mode:** Visual / manual QA (new skill; verified by lint-agent-artifacts.py
  exit 0 + grep AC7–AC8)
**Done when:** File exists with correct frontmatter; lint-agent-artifacts.py exits 0
  on the release-engineering pack; AC7 and AC8 grep checks pass.

**Approach:**
Create `packs/release-engineering/.apm/skills/define-slo/SKILL.md` with:
- Frontmatter: `name: define-slo`, one-line description naming SLO authoring +
  OpenSLO v1 + error-budget-policy + release-engineering pack home
- Body sections:
  - **When to invoke** — after the service is deployed; when the release-loop PRR
    shows `error-budget: not-defined`; when authoring a new service's reliability targets
  - **SLO artifact format (OpenSLO v1)** — rationale; required fields; worked
    example template with placeholder queries; `metricSource.type` as adopter fill-in
  - **The `error_budget_policy` block** — companion section; fields (halt_at, warn_at,
    postmortem_at, trailing_window); defaults; override guidance
  - **Error budget derivation** — formula and worked example
  - **Where to commit** — `slos/<service>.yaml`; consumed by release-loop PRR gate
  - **Query-at-gate-time** — the integration gap: `budget_consumed_pct` requires a
    trailing-window telemetry query at gate-check time; template query derivation;
    `query-failed` state meaning; not a silent pass
  - **Authoring-time query validation** — the skill instructs the implementing agent to
    execute the metric query against the backend once at SLO authoring time and confirm
    it returns a result in the expected range before committing the SLO document;
    this is the drawback-mitigation for metric query accuracy (RFC-0073 Drawbacks)
  - **Toolchain translation** — Sloth consumes OpenSLO directly; Pyrra requires a
    separate CRD; Nobl9 SaaS has its own format; adopter's pipeline translates

**Tests (goal-based):**
```bash
test -f packs/release-engineering/.apm/skills/define-slo/SKILL.md
grep "name: define-slo" packs/release-engineering/.apm/skills/define-slo/SKILL.md
grep "OpenSLO" packs/release-engineering/.apm/skills/define-slo/SKILL.md
grep "error_budget_policy" packs/release-engineering/.apm/skills/define-slo/SKILL.md
grep "not-defined\|within-budget\|exhausted" packs/release-engineering/.apm/skills/define-slo/SKILL.md
grep "query-failed" packs/release-engineering/.apm/skills/define-slo/SKILL.md
```

---

### T3 — Update release-loop SKILL.md PRR error-budget paragraph
**Depends on:** T1, T2 (same file as T1; T2 creates define-slo which T3 references)
**Verification mode:** Visual / manual QA (skill content; verified by grep AC9)
**Done when:** The old "supplied by a follow-on SLO-authoring capability" paragraph is
  replaced; the four states (not-defined, within-budget, warning, exhausted) are named;
  `define-slo` is referenced.

**Approach:**
In `release-loop/SKILL.md`, find the paragraph starting:
"The error-budget **artifact** is supplied by a follow-on SLO-authoring capability
(home provisional — a follow-on capability)."

Replace it with a four-state resolution protocol that:
- Names `not-defined` (no `slos/<service>.yaml`), `within-budget`, `warning: <N>% remaining`,
  and `exhausted: halt-releases` as the four states
- References `define-slo` as the skill that produces the SLO document
- Preserves the "launch PRR (pre-prod)" and "trailing window" distinctions

**Tests (goal-based):**
```bash
grep "not-defined\|within-budget\|warning.*remaining\|exhausted.*halt" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: all four patterns present
grep "define-slo" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: at least one match
# Confirm old text is gone:
grep "follow-on SLO-authoring capability" packs/release-engineering/.apm/skills/release-loop/SKILL.md
# expected: no match
```

---

### T4 — Add cross-reference notes to `docs/specs/release-loop/spec.md`
**Depends on:** T1, T3 (after content is written to know what to reference)
**Verification mode:** goal-based (grep checks)
**Done when:** AC5, AC6, AC7, AC10(e) each contain `→ RFC-0072`; AC6b contains `→ RFC-0073`.

**Approach:**
For each of AC5, AC6, AC7, AC10(e): append `(→ RFC-0072 for doctrine)` or equivalent
after the AC's final sentence (or the checkbox). For AC6b: append `(→ RFC-0073 for SLO
schema and PRR field resolution)`. No AC text changes — these are additive reference markers.

**Tests (goal-based):**
```bash
grep "RFC-0072" docs/specs/release-loop/spec.md
# expected: at least 4 matches (AC5, AC6, AC7, AC10e)
grep "RFC-0073" docs/specs/release-loop/spec.md
# expected: at least 1 match (AC6b)
```

---

### T5 — Version bump, changelog, build-self, lint gates, mark spec shipped
**Depends on:** T1, T2, T3, T4
**Verification mode:** goal-based
**Done when:** `pack.toml` and `plugin.json` both at `0.1.5`; changelog updated;
  `make build-self` exits 0; `make build-check`, `python tools/lint-agent-artifacts.py`,
  and `python tools/lint-agents-md.py` all exit 0; this spec's Status is Shipped and
  all ACs are checked; RFC-0072 and RFC-0073 are both Accepted.

**Approach:**
1. Edit `packs/release-engineering/pack.toml`: `version = "0.1.4"` → `"0.1.5"`
2. Edit `packs/release-engineering/.claude-plugin/plugin.json`: `"version": "0.1.4"` → `"0.1.5"`
3. Add `[Unreleased]` changelog entry to `docs/product/changelog.md` for release-engineering 0.1.5
4. Set RFC-0072 and RFC-0073 Status: Accepted, Date closed: 2026-07-27 (all decisions confirmed in authoring)
5. Run `make build-self`
6. Run `make build-check`
7. Run `python tools/lint-agent-artifacts.py`
8. Run `python tools/lint-agents-md.py`
9. Set this spec Status: Shipped; mark AC1–AC14 `[x]`

**Tests (goal-based):**
```bash
grep '"version": "0.1.5"' packs/release-engineering/.claude-plugin/plugin.json
grep 'version = "0.1.5"' packs/release-engineering/pack.toml
make build-check
python tools/lint-agent-artifacts.py
python tools/lint-agents-md.py
```
