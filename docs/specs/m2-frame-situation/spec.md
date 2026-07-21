# Spec: m2-frame-situation

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2 · Strategic Shaping; D9 typed shaping queue entries); known-unknowns resolved 2026-07-18 (frame-intent vs frame-situation: coexist, different output contracts); RFC-0064 Amendment #3 + `docs/specs/queue-add/` (workspace.toml write-back is the `queue-add` / proposed `capture-work` front door's responsibility — frame-situation suggests the entry verbally only; `capture-work` is the proposed rename of `queue-add`, not yet accepted). Sub-RFC pe-pack-strategic-shaping (RFC-00XX) is not yet accepted — this spec proceeds under resolved constraints and may require minor revision on sub-RFC acceptance.
- **Brief:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineer or PM working a `strategy`-typed shaping queue item — or
holding a raw signal (market observation, OKR gap, user pain pattern,
engineering finding, competitive signal, technology shift) — runs
`frame-situation` and gets a **Situation Framing** typed artifact that:
(1) classifies the signal into a typed finding,
(2) assesses the maturity of up to three relevant capability areas on the
Wardley evolution curve (Genesis → Custom-built → Product → Commodity),
and (3) anchors the situation to the **PE six-step shaping sequence**
(`frame-situation` → `identify-opportunities` → `diverge-solutions` →
validate → `place-bet` → `map-capabilities`) with a recommended entry
point and rationale.

The artifact is committed to `<output_dir>/shaping/<slug>/situation-framing.md`
(the designed default for output_dir is `docs/product/`; resolved via
config-driven three-tier procedure) and becomes the traceable starting point
for the shaping chain. The skill then suggests (but does not write) a
`shape`-typed `[shaping_queue]` entry for `workspace.toml`; the user adds
it via `queue-add` or manually.

**Scope:** initiative-level and capability-level signals. Feature-scope
requests are redirected to `frame-intent`. This is step 1 of the PE
shaping loop, not a brief factory.

## Boundaries

### Always do

- **Classify the input signal** into one of the defined finding types:
  `opportunity` | `risk` | `gap` | `threat` | `emergent-capability`. When
  the signal is ambiguous or too thin to confidently classify, name the
  ambiguity and elicit more detail before forcing a type — never assign a
  type to an underdetermined signal.
- **Assess Wardley maturity** for up to three capability areas the signal
  implicates. Place each on the Genesis → Custom-built → Product → Commodity
  curve, state the evidence for the placement, and state the strategic
  implication (e.g. "Custom-built → invest to differentiate or adopt an
  emerging standard; Product → buy or adopt to commoditize"). Where the
  agent cannot confidently place a capability, name it as a residual
  assumption. When no capabilities can be placed, emit an all-residual-
  assumptions table and explain why placement is deferred.
- **Recommend a six-step entry point** based on the signal type and what
  is already known: if the problem space is well-understood, start at step
  3 or later; if speculative, default to step 2. State the reasoning
  explicitly so the PE can override.
- **Emit `situation-framing.md`** — written to
  `<output_dir>/shaping/<slug>/situation-framing.md`, with stable marker
  (`type: situation-framing`) carrying: signal classification, Wardley
  assessment per capability, six-step entry-point recommendation, and named
  residual assumptions. The slug is derived from the signal's subject.
- **Resolve the write path via config-driven three-tier procedure**
  (repo-scope `agentbundle-layout.toml [product]` → user-scope →
  two-branch elicitation). After resolving, realpath-expand and
  symlink-resolve the path; reject any `..` escape **and** any symlink
  chain that exits the intended root. Surface the resolved absolute path to
  the adopter before writing.
- **Suggest a `workspace.toml` [shaping_queue] entry** — print the TOML
  snippet for the user to add (a `shape`-typed entry with the derived slug);
  direct the user to `queue-add` or manual edit. Do not write to
  `workspace.toml`.
- **Redirect feature-scoped requests to `frame-intent`** — when the signal
  is clearly a single feature request (a specific screen, endpoint, or
  interaction below the capability level), name the altitude mismatch and
  offer to redirect. When altitude is genuinely ambiguous (could be a
  feature or a capability), ask — never force one altitude.
- **Detect absence of `identify-opportunities`** and degrade cleanly: name
  the missing skill in the artifact and explain what step 2 of the sequence
  requires; framing and artifact emission continue unblocked.

### Ask first

- Before skipping all six steps and treating the signal as already-bet
  (signals are framing inputs; bets require `place-bet` to be on record).
- Before adding a second typed artifact to this skill.
- Before any write path that resolves outside the repo tree or via a
  realpath-escaped symlink (untrusted-origin — confirm the resolved absolute
  path before writing).

### Never do

- **Never** write to `workspace.toml` directly — the skill suggests the
  entry; the user commits the workspace change.
- **Never** write to a literal hardcoded path — always resolve via the
  three-tier config procedure; `docs/product/` is the designed default, not
  a constant.
- **Never** mandate Wardley vocabulary on a user who has not adopted it —
  offer the maturity framing with brief stage definitions, but do not block
  if the user prefers plain-language descriptions.
- **Never** produce a brief directly — step 5 (`place-bet`) and then
  `decompose-intent`/`author-brief` own the brief hand-off.
- **Never** exceed 100 lines in `SKILL.md`.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

This is a prompt-only skill (Charter Principle 3) — no compressible
invariant logic. Verification is goal-based for structure and
manual-QA for judgment.

- **Skill file and lint gates: goal-based.** File exists at the conventional
  path, `tools/lint-skill-spec.py` passes, `lint-packs` passes, <100 lines,
  valid frontmatter.
- **Skill behavior (signal classification, Wardley assessment, route
  recommendation, artifact emission): manual QA.** Walk the worked example
  end to end; record the observed artifact content in the implementing PR.
- **Degrade branch (AC8) and redirect branch (AC9): goal-based grep.** The
  SKILL.md body must contain prose specifying both branches. Pinned assertions
  (phrases unique to each branch; must return ≥1 match each):
  AC8 degrade: `grep -F "Step 2 readiness"` (the artifact section that names the
  missing skill); AC9 redirect: `grep -F "altitude mismatch"` (redirect branch);
  AC9 ambiguous-ask: `grep -F "genuinely ambiguous"` (ask-don't-force branch).
  A count-only OR-grep would pass vacuously; pin to unique phrases.
- **Diátaxis guide: goal-based for file existence, manual QA for accuracy.**
  Guide at `docs/guides/product-engineering/how-to/frame-a-situation.md`;
  reads accurately against the shipped skill (review recorded in PR).
- **Projection: goal-based.** `lint-packs`, `validate`, and `build` exit 0.
  Adopter-cleanliness verified by grep over the SKILL body (no RFC-NNNN, no
  `agent-ready-repo`). `make build-self` is not used — the PE pack is
  user-scope and excluded from self-host projection.

## Acceptance Criteria

- [x] **AC1.** `frame-situation` ships at
  `packs/product-engineering/.apm/skills/frame-situation/SKILL.md`
  — <100 lines, valid frontmatter, passes `tools/lint-skill-spec.py` and
  `lint-packs`.

- [x] **AC2.** The skill classifies the input signal into one of the defined
  finding types (`opportunity` | `risk` | `gap` | `threat` |
  `emergent-capability`) and surfaces the classification with a one-line
  rationale in the artifact. When the signal is underdetermined, the skill
  names the ambiguity and elicits more detail before assigning a type.

- [x] **AC3.** The skill produces a Wardley maturity assessment for up to
  three relevant capability areas named in or implied by the signal, placing
  each on the Genesis → Custom-built → Product → Commodity curve with evidence
  and strategic implication. Where confidence is low, the placement is a
  residual assumption. When zero capabilities can be confidently placed, the
  artifact emits an all-residual-assumptions table and explains the deferral.

- [x] **AC4.** The skill recommends a PE six-step entry-point
  (`identify-opportunities`, `diverge-solutions`, or `place-bet`) with a
  one-sentence rationale. The default is step 2 (`identify-opportunities`);
  richer signals with a documented problem and vetted options may enter at
  step 3 or step 5.

- [x] **AC5.** The skill emits a file at
  `<output_dir>/shaping/<slug>/situation-framing.md` — slug derived from
  the signal's subject — with stable marker (`type: situation-framing`)
  carrying: signal classification, Wardley assessment per capability,
  recommended six-step entry point, and named residual assumptions.
  A second run for a different signal writes to a different slug path; no
  collision.

- [x] **AC6.** The skill resolves the write path via the config-driven
  three-tier procedure (repo-scope → user-scope → two-branch elicitation);
  realpath-expands and symlink-resolves the path; rejects `..` escapes and
  any symlink chain that exits the intended root; surfaces the resolved
  absolute path to the adopter before writing.

- [x] **AC7.** After the artifact is written, the skill suggests a
  `shape`-typed `[shaping_queue]` workspace.toml entry for the user to add
  — without writing to `workspace.toml` itself. The suggestion includes the
  derived slug and directs the user to `queue-add` or manual edit.

- [x] **AC8.** When `identify-opportunities` is not detected in the available
  skills, the skill degrades cleanly: the artifact notes the missing skill
  and describes what step 2 of the sequence requires; framing and artifact
  emission continue unblocked. The SKILL.md body contains explicit prose
  specifying this degrade behavior (goal-based grep).

- [x] **AC9.** When the input is feature-scoped (clearly below the capability
  level), the skill names the altitude mismatch and offers to redirect to
  `frame-intent`. When altitude is genuinely ambiguous, the skill asks rather
  than forcing one level. The SKILL.md body contains explicit prose specifying
  both paths (goal-based grep).

- [x] **AC10.** A worked example ships at
  `packs/product-engineering/.apm/skills/frame-situation/examples/`
  demonstrating the happy path: raw signal → typed finding → Wardley
  assessment → route recommendation → `situation-framing.md` artifact.
  The example is adopter-clean (no RFC-NNNN references, no
  `agent-ready-repo` references).

- [x] **AC11.** A Diátaxis how-to guide ships at
  `docs/guides/product-engineering/how-to/frame-a-situation.md` covering:
  when to use `frame-situation` vs `frame-intent` (altitude decision); what
  a well-formed signal looks like; and how to use the Wardley assessment
  output to choose the six-step entry point.

- [x] **AC12.** `lint-packs`, `validate`, `build`, and the `packages/agentbundle`
  pack/contract tests exit 0. Grep over the SKILL.md body confirms no
  adopter-facing internal-catalogue references. `make build-self` stays
  drift-free (the PE pack is user-scope, excluded from `_DEFAULT_SELF_HOST_PACKS`,
  so build-self does not project the skill; confirmed by noting it in the plan).

## Assumptions

- **A1.** RFC-00XX · pe-pack-strategic-shaping has not been accepted. This
  spec proceeds under the boundary decisions already resolved in RFC-0064
  (2026-07-18): frame-intent vs frame-situation coexist with different
  scopes and output contracts. This spec may require revision on sub-RFC
  acceptance, but no new boundary decisions are made here.
- **A2.** The six-step PE sequence is anchored in RFC-0064 and stable enough
  to name in the skill body without the sub-RFC.
- **A3.** Wardley Evolution curve vocabulary (Genesis / Custom-built / Product /
  Commodity) is the canonical maturity model; the skill body briefly defines
  each stage so Wardley-unfamiliar adopters can follow without prior reading.
- **A4.** `docs/guides/product-engineering/` exists and carries Diátaxis
  sub-buckets (`how-to/`, `reference/`, `tutorials/`, `explanation/`). The
  guide file at `how-to/frame-a-situation.md` does not yet exist.
- **A5.** Workspace.toml write-back (auto-adding the [shaping_queue] entry)
  is the `queue-add` front door's responsibility per RFC-0064 Amendment #3
  (`docs/specs/queue-add/`). `capture-work` is the proposed rename, not yet
  accepted; the shipped skill and spec are `queue-add`. This skill suggests
  the entry verbally.
