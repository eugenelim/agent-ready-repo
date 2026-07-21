# Plan: m2-frame-situation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/frame-situation/SKILL.md` — plus its
worked example, a how-to guide, and lint/build verification. There is no
engine, script, or contract file (Charter Principle 3).

The shape mirrors `frame-domain` (same pack, same pattern): skill body defines
the procedure and artifact schema; the agent following it produces the typed
artifact; path resolution is config-driven three-tier. The key difference:
`frame-domain` wraps `desk-research` applied mode; `frame-situation` wraps
**embedded Wardley maturity reasoning** — no sub-skill delegation; the
maturity model is documented inline and applied by the executing agent.

`make build-self` is **not** a verification gate for this spec — the PE pack is
user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`. Verification uses
`lint-packs`, `validate`, and `build` instead, matching the sibling pattern
from `frame-domain`.

Order of operations: author SKILL.md (T1), author worked example (T2) and
how-to guide (T3) in parallel after T1, then lint/build (T4).

## Constraints

- **RFC-0064 D9** — `frame-situation` consumes raw input signals and routes them
  as `shape`-typed queue entries. Input-signal = raw triggering event; `type = "signal"`
  in workspace.toml = standing non-graduating landscape concern — distinct.
- **RFC-0064 M2.1** — frame-situation embeds Wardley capability maturity; output =
  typed finding + six-step route anchor.
- **RFC-0064 Amendment #3 + `docs/specs/queue-add/`** — workspace.toml write-back is
  the `queue-add` front door's responsibility; `capture-work` is the proposed rename,
  not yet accepted; this skill suggests verbally.
- **Known Unknowns resolved 2026-07-18** — frame-intent vs frame-situation coexist.
- **Charter Principle 3** — prompt-only; no runtime engine, script, or file-path
  generator wired here.
- **PE pack style** — SKILL.md <100 lines; depth in `references/` only if needed.
- **Phase-slice doctrine** — skill ships WITH its guide (AC11).
- **File-per-slug path** — `<output_dir>/shaping/<slug>/situation-framing.md`;
  slug in the path prevents collision on multiple runs.

## Tasks

### T1 — Author SKILL.md

**Depends on:** none

**Verification:** goal-based — file at correct path, <100 lines, frontmatter
passes `tools/lint-skill-spec.py`, `lint-packs` passes.

**Approach:**

Author `packs/product-engineering/.apm/skills/frame-situation/SKILL.md` with:

**Frontmatter:**
- `name: frame-situation`
- `description:` one sentence — when to invoke (initiative/capability-level
  signal → situation framing → six-step route anchor), what it produces
  (Situation Framing artifact + Wardley maturity assessment + shaping route),
  what NOT to use it for (feature-scope → frame-intent; assumption testing →
  de-risk-intent; breaking down → decompose-intent).

**When to invoke (5–7 lines):**
- Confirm signal is initiative/capability-scope, not feature-scope.
- Feature-scope → redirect to `frame-intent`; ambiguous altitude → ask.
- Unclassifiable signal (too thin) → elicit more detail before proceeding.

**Procedure (the six steps, inline):**

1. **Intake** — read the signal (free text or pointer to an existing artifact);
   infer altitude (initiative vs capability); confirm. If feature-scoped, redirect
   to `frame-intent`. If ambiguous, ask.

2. **Classify the finding type** — assess which of the five types fits:
   `opportunity` | `risk` | `gap` | `threat` | `emergent-capability`. If the
   signal is underdetermined, name the ambiguity and elicit. State the chosen
   type and one-line rationale in the artifact.

3. **Wardley maturity assessment** — identify up to three capability areas
   implicated. For each, place on the four-stage curve with evidence and
   strategic implication. Inline the stage definitions (one line each) so
   Wardley-unfamiliar users can follow:
   - *Genesis*: novel, uncertain, no best practice; explore/experiment.
   - *Custom-built*: hand-crafted for specific needs; invest to differentiate or
     watch for emerging standards.
   - *Product*: widely available and improving; buy/adopt over build.
   - *Commodity*: standardized utility; use off-the-shelf; competing here is waste.
   When confident placement is not possible, mark as residual assumption. When
   zero capabilities are placeable, emit an all-residual-assumptions table.

4. **Recommend six-step entry point** — decide based on signal richness:
   - Unknown problem → step 2 (`identify-opportunities`, default).
   - Known problem, unknown options → step 3 (`diverge-solutions`).
   - Known options, need bet committed → step 5 (`place-bet`).
   State the recommendation and one-sentence rationale.

5. **Emit `situation-framing.md`** — resolve `output_dir` via config-driven
   three-tier procedure (same as `frame-intent`): repo-scope
   `agentbundle-layout.toml [product]` → user-scope → two-branch elicitation.
   After resolving: realpath-expand, symlink-resolve, reject `..` escapes and
   any symlink that exits the root. Surface the resolved absolute path before
   writing. Write to `<output_dir>/shaping/<slug>/situation-framing.md`.

   Degrade: if `identify-opportunities` is not in the available skills, note
   this in the artifact under "Step 2 readiness" and explain what the skill
   provides. Do not block artifact emission.

6. **Suggest `workspace.toml` entry** — print the TOML snippet:
   ```toml
   {slug = "<slug>", type = "shape"},
   ```
   Direct the user to add it to `[ini-NNN.shaping_queue]` backlog via
   `queue-add` or manual edit. Do not write to `workspace.toml`.

**Anti-patterns to refuse** (inline, 3–4 lines):
- Writing to workspace.toml. Writing to a literal path. Producing a brief.
  Forcing a Wardley stage when confidence is too low.

Inline the `situation-framing.md` artifact schema (frontmatter + body sections)
so the agent knows exactly what to emit (do not put this in a `references/` file —
the skill must fit in <100 lines and the schema is short enough to inline).

**Done when:** `tools/lint-skill-spec.py .../frame-situation/SKILL.md` exits 0,
`lint-packs` green, `wc -l` ≤ 100.

---

### T2 — Author worked example

**Depends on:** T1

**Verification:** manual QA — read the example; confirm it walks an end-to-end
pass and produces a recognizable `situation-framing.md` artifact.

**Approach:**

Author
`packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md`
using a synthetic but realistic signal:

> "Engineering reported that every team in the org hand-rolls its own agent
> skill discovery mechanism — three implementations found, no standard emerging."

Demonstrate:
- **Signal classification:** gap (coordination overhead rising, convergence
  opportunity)
- **Wardley assessment:** agent skill discovery (Custom-built, with evidence);
  inter-team coordination overhead (Genesis, no established pattern)
- **Route recommendation:** step 2 (`identify-opportunities`) — problem is
  confirmed but functional/emotional/social jobs not yet documented
- **Artifact stub** showing the `situation-framing.md` shape with frontmatter
- **workspace.toml suggestion** TOML snippet

**Done when:** example file exists, is adopter-clean (no RFC-NNNN, no
`agent-ready-repo`), reads as a coherent end-to-end narrative.

---

### T3 — Author Diátaxis how-to guide

**Depends on:** T1

**Verification:** goal-based for file existence; manual QA that it accurately
describes the shipped skill.

**Approach:**

`docs/guides/product-engineering/how-to/` exists (the Diátaxis `how-to/`
bucket under the PE pack guide). Author
`docs/guides/product-engineering/how-to/frame-a-situation.md` as a
Diátaxis how-to (task-oriented; reader knows what goal they want).

Cover:
1. When to reach for `frame-situation` vs `frame-intent` — the altitude
   decision: initiative/capability-level signal vs feature-scope request.
2. What makes a well-formed signal (enough to classify, not pre-solved).
3. How to use the Wardley assessment to choose the six-step entry point.
4. What to do with the workspace.toml suggestion (add via `queue-add` or
   manually).

Length: ~1–2 pages. No internal-catalogue references (RFC-NNNN, `agent-ready-repo`).

**Done when:** file exists at the correct Diátaxis path.

---

### T4 — Lint and build verification

**Depends on:** T1, T2, T3

**Verification:** goal-based — all commands exit 0.

**Approach:**

```bash
# From repo root
make lint-packs        # source-side frontmatter/description/body-shape
make validate          # pack manifest validation
make build             # build artifacts
pytest packages/agentbundle  # pack/contract tests (same gate as frame-domain)
# Adopter-cleanliness grep (lint-agent-artifacts.py covers projected packs,
# not user-scope PE pack — verify directly):
grep -rn "RFC-0064\|agent-ready-repo\|RFC-00" \
  packs/product-engineering/.apm/skills/frame-situation/
# Goal-based greps for degrade/redirect branches (AC8, AC9) — pinned to
# unique phrases; count-only OR-grep would pass vacuously on other matches:
grep -F "Step 2 readiness" \
  packs/product-engineering/.apm/skills/frame-situation/SKILL.md   # AC8 degrade
grep -F "altitude mismatch" \
  packs/product-engineering/.apm/skills/frame-situation/SKILL.md   # AC9 redirect
grep -F "genuinely ambiguous" \
  packs/product-engineering/.apm/skills/frame-situation/SKILL.md   # AC9 ask
# Line count
wc -l packs/product-engineering/.apm/skills/frame-situation/SKILL.md
```

Note: `make build-self` still runs as a drift check (confirms no unexpected
change to self-host projection), but does **not** project this skill — the PE
pack is user-scope (`_DEFAULT_SELF_HOST_PACKS` = core / governance-extras /
user-guide-diataxis; `product-engineering` excluded). `lint-seeds` is
irrelevant (this skill ships no seeds). `lint-agent-artifacts.py` covers
projected packs only, not user-scope packs; adopter-cleanliness is verified
by the direct grep above.

**Done when:** lint-packs + validate + build exit 0; adopter-cleanliness grep
is clean; AC8/AC9 greps return ≥1 match each; SKILL.md ≤ 100 lines.

## Design (LLD)

**Shape:** mixed. Pruned sub-sections: no service interface, no UI, no
NFR-with-a-bar. Retaining: design decisions, data & schema, dependencies.

### Design decisions

- **Wardley assessment is inline, not delegated.** No `wardley-assess` sub-skill;
  the model is embedded in the SKILL.md procedure. Four-stage definitions inline
  so Wardley-unfamiliar adopters can follow without prior reading.
- **File-per-slug path prevents collision.** `<output_dir>/shaping/<slug>/situation-framing.md`
  — each signal produces its own path; a second run never overwrites the first.
  This matches `frame-domain`'s per-initiative subfolder pattern (not
  `frame-intent`'s flat file-per-slug) because situation framing may later
  accumulate sibling artifacts (opportunity assessment, etc.) under the same slug.
- **One typed artifact.** `frame-domain` emits two because they have separate
  downstream lifecycles. `frame-situation` emits one — all components (classification,
  Wardley, route) feed the same shaping chain step together.
- **Three capability areas cap.** Beyond three, the assessment becomes a strategy
  document rather than a framing artifact; three forces prioritization.
- **No workspace.toml write.** Deferred to `capture-work`. This skill is scope-
  bounded to analysis + artifact; workspace coordination belongs to its owner.
- **config-driven path (same as frame-intent).** Re-uses the established three-tier
  convention; no second path-resolution model in the pack.

### Data & schema

`situation-framing.md` — the one typed artifact:

```markdown
---
type: situation-framing
slug: <derived-from-signal-subject>
signal: "<one-line signal description>"
finding-type: opportunity | risk | gap | threat | emergent-capability
date: <ISO date>
shaping-entry: identify-opportunities | diverge-solutions | place-bet
---

# Situation Framing: <slug>

## Signal
<The raw signal, quoted or paraphrased>

## Finding
**Type:** <finding-type>
**Rationale:** <one-paragraph reasoning>

## Wardley Capability Assessment

| Capability | Stage | Evidence | Strategic implication |
|---|---|---|---|
| <name> | Genesis / Custom-built / Product / Commodity | <evidence> | <implication> |

> **Residual assumptions:** <capability(ies) that could not be confidently placed>

## Recommended Entry Point
**Step:** <shaping-entry> (`<skill-name>`)
**Rationale:** <one sentence>

## Step 2 readiness
<When identify-opportunities is absent: name the missing skill and describe
what step 2 requires. Omit when skill is present.>

## Suggested workspace.toml entry
Add to `[ini-NNN.shaping_queue]` backlog:
```toml
{slug = "<slug>", type = "shape"},
```
Use `queue-add` or edit `workspace.toml` manually.
```
```

### Dependencies

- **`frame-intent`** — sibling skill; altitude redirect target. No import;
  redirect is verbal.
- **`identify-opportunities`** — step 2; detect-and-degrade if absent (AC8).
- **`agentbundle-layout.toml`** — config-tier read; same three-tier as
  `frame-intent`.
- **`queue-add` / `capture-work`** — downstream workspace.toml write; named in
  the suggested-entry output; not a runtime dependency.

## Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-07-20 | Initial plan + spec authored | First pass |
| 2026-07-20 | Fixed artifact path to file-per-slug; fixed guide path to `how-to/`; fixed projection gates (lint-packs/validate/build, not build-self); added AC8/AC9 greps; aligned constraint to RFC-0064 Amendment #3; resolved ambiguous-signal handling | Adversarial review Blockers 1–4 + Concerns 5–9 + Nits 10–11 |
| 2026-07-20 | Pinned AC8/AC9 greps to unique phrases (Step 2 readiness / altitude mismatch / genuinely ambiguous); added packages/agentbundle pytest leg; fixed capture-work reference to docs/specs/queue-add/ | Adversarial re-review Blocker 1 + Concerns 2–3 |
