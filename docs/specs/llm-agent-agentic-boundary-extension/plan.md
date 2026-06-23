# Plan: llm-agent-agentic-boundary-extension

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A pure-prose change across two packs plus reciprocal governance bookkeeping.
The shape: extend one reference module with three control-altitude checks and a
standards-line update (the substantive change, in `core`), then keep every
record that *pointed at the gap* consistent — the overlay lens (in `architect`),
the overlay's coverage-parity note, the overlay's deferred AC, and the backlog
register. The riskiest part is **altitude discipline**: the new module checks
must read as *what a reviewer verifies on a diff* (containment, privilege
control, memory integrity), not as the design-altitude *naming* the overlay
already owns — duplicating the overlay is the failure mode the spec's `Never do`
guards. Everything is verified goal-based (grep/diff/build/lint) except the
final consumer check, which is manual QA: the `security-reviewer` itself reads
the extended module on this PR's diff.

Order of operations: edit the module (T1) → standards surface (T2) → soften the
lens, both copies (T3) → reciprocal records, all in one commit (T4) → version
bumps + build-self + changelog (T5). T1-T2 are the `core` content; T3 is the
`architect` content; T4 is repo-owned docs; T5 is the build/release mechanics
that must run last so projection and `marketplace.json` reflect the final state.

## Constraints

- **RFC-0029** — the module is the orchestrator-loaded, progressive-disclosure
  depth library consumed by `security-reviewer` (no Skill tool); the universal
  method stays in the agent body, shape-specific depth stays in the module. The
  three-bucket delegation legend and the module's currency-update-as-maintenance
  framing both come from here.
- **ADR-0032** — the accepted decision that the overlay names these boundaries
  at design altitude and records the module extension as deferred backlog work;
  the route-to-`security-reviewer` boundary and the coverage-parity criterion
  are its calls. This plan executes that deferral.
- **CHARTER Principle 3** — prose the agent reasons from, never executable
  tooling/evals. **ADR-0023** — the three-reviewer ceiling; no new reviewer.
- **`agentic-well-architected-overlay` spec** — the bidirectional coverage-parity
  AC and the deferred AC this closes; the per-skill byte-identical-lens-copies
  constraint.

## Construction tests

Most verification is per-task below. Cross-cutting:

**Integration tests:** none beyond per-task checks (pure-prose change; no code).

**Manual verification:**
- Run the `security-reviewer` subagent with the extended `llm-agent` module
  inlined into its brief against a **synthetic agentic snippet** (code-exec tool
  + delegation chain + memory write — this PR's own diff is pure prose with no
  agentic sink); record that it reasons from the three new module checks. Pass
  condition: the report cites the three new checks as the control depth, not a
  particular verdict (spec AC: security-reviewer reasons from the new checks).
- `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` passes
  after T4 (deferral-anchor + status invariants across the touched specs).

## Tasks

### T1: Three agentic boundary checks land in the `llm-agent` module

**Depends on:** none

**Tests:**
- `grep` the implementation-checks section of
  `packs/core/.apm/skills/security-checklists/references/llm-agent.md` for the
  three new check titles (execution isolation & blast radius; inter-agent
  identity/privilege propagation; memory poisoning) — each present (spec ACs 1-3).
- The execution-isolation check names the **three confinement axes** (filesystem
  scope, network egress, resource/time bounds) and flags its network-egress facet
  `hybrid` with an `outbound-ssrf` cross-reference (spec AC1); the memory check
  names both the **write gate** (provenance/trust before persistence) and the
  read side (spec AC3).
- Each new check line begins with a delegation tag (`reason` for all three; the
  egress facet noted `hybrid` inline) per the legend (spec AC: module shape).
- The six existing checks are byte-unchanged in title and tag — LLM03 stays the
  sole `tool` check; LLM01/05/06/02/10 stay `reason` (spec AC: existing checks
  untouched).
- The four structural anchors are still present: the delegation-legend lines, the
  `## Spec-stage (proactive control)` heading, the `## Established-helper bypass`
  heading, and the implementation-checks list (spec AC: module keeps shape).
- The **Spec-stage (proactive control)** paragraph names the containment,
  privilege-propagation, and memory-integrity design-time questions (extending,
  not replacing, the instruction-vs-data / least-privilege framing) (spec AC:
  spec-stage proactive control covers the three boundaries).

**Approach:**
- Add three `reason`-tagged checks to the **Implementation checks** list, each
  one sentence of *what the reviewer verifies*, anchored on OWASP Top 10 for
  Agentic Applications:2026 — execution isolation on **ASI02** + **ASI05**,
  privilege propagation on **ASI03**, memory poisoning on **ASI06** + **LLM04** —
  distinct from the existing LLM06 authorization check (containment ≠
  authorization). Decompose execution isolation into the three confinement axes;
  give memory poisoning the write-gate + read-side framing.
- Extend the **Spec-stage (proactive control)** paragraph minimally so the
  design-time control names the containment/isolation, privilege-propagation, and
  memory-integrity questions where they belong — without restating the overlay's
  design-altitude prose.

**Done when:** the greps above pass and the new checks read at control altitude (a
reviewer could act on each against a diff), with the existing six checks intact.

### T2: Standards surface names OWASP Top 10 for Agentic Applications:2026 + LLM04

**Depends on:** T1

**Tests:**
- `grep -Fn "ASI02" <module>` and `grep -Fn "LLM04" <module>` → present in the
  Standards block (use wrap-safe tokens — the phrase "Agentic Applications:2026"
  line-wraps in the module's `> **Standards:**` block) (spec AC: standards surface
  names the added families).
- `grep -Fn "Agentic Applications:2026" security-checklists/SKILL.md` → matches
  the `llm-agent` module-index row's anchor cell and the frontmatter
  `description:` (both single-line there).

**Approach:**
- Update the module **Standards** header to add **OWASP Top 10 for Agentic
  Applications:2026** (ASI02 Tool Misuse & Exploitation, ASI03 Agent Identity &
  Privilege Abuse, ASI05 Unexpected Code Execution, ASI06 Memory & Context
  Poisoning) and **LLM04** (Data & Model Poisoning) alongside the existing
  categories.
- Update the `SKILL.md` module-index `llm-agent` anchor cell and the frontmatter
  description's standards parenthetical to match.

**Done when:** both greps pass and the three surfaces (module header, index row,
frontmatter) agree on the standards named.

### T3: The overlay lens prose is softened in both copies

**Depends on:** T1

**Tests:**
- `diff packs/architect/.apm/skills/architect-design/references/lens-genai-agentic.md
  packs/architect/.apm/skills/architect-review/references/lens-genai-agentic.md`
  → differ only in the per-skill duplication note (spec AC: both copies identical).
- **Negative grep on byte-accurate substrings** — two portable `grep -Frn`
  invocations (avoid `\|` BRE alternation, which is non-portable to BSD/macOS
  grep): `grep -Frn "the module's current checks" packs/architect/` and
  `grep -Frn "surface catches up" packs/architect/` → **no matches** (spec AC: stale
  claims gone). NB: the live source reads `reach **beyond** the module's current
  checks` (markdown bold) and wraps `agentic` / `surface catches up` across two
  lines, so the full phrases never match — grep the unbolded, unwrapped
  substrings, which the removal must eliminate.
- **Positive check (section-scoped read, not a bare-token grep)** — read the
  rewritten "Routes into the security boundary" section and confirm all three
  boundaries (`execution isolation`, `identity/privilege`, `memory poisoning`)
  are now listed among the concerns that route to a named `llm-agent` check. A
  bare-token grep is insufficient here: those tokens also appear in the Tier B/C
  bullets above and the source line-wraps `identity/privilege\npropagation`, so
  the check is a scoped read of the routing sentence — corroborated by the
  negative grep going to zero — so a non-edit fails red (the stale paragraph would
  still be present). T3 folds the three into the routing sentence as one explicit
  clause ("…and — for a system that acts, delegates, or persists state — …") so
  the read is unambiguous even though the sentence soft-wraps.

**Approach:**
- In the "Routes into the security boundary" section, fold the three boundaries
  into the sentence listing the concerns that route to a named `llm-agent` check
  as one explicit clause (currently "The concerns that route to a named module
  check today: prompt injection, data egress & disclosure, …"; drop "today"), and
  rewrite the "Three
  agentic boundaries reach **beyond** the module's current checks … until the
  security module's agentic surface catches up" paragraph so it no longer claims
  the module lacks these checks — keeping the design-altitude routing statement
  and the "name frameworks never" sentence intact.
- Apply the identical edit to both copies; preserve each file's one-line
  duplication note.

**Done when:** the diff passes, the negative grep is zero, and the section read
confirms all three boundaries route to a named `llm-agent` check.

### T4: Reciprocal records resolve consistently, in one commit

**Depends on:** T1, T2, T3

**Tests:**
- `python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` exits 0
  — the authoritative deferral check: invariant (iv) confirms no **live**
  `(deferred: …)` marker for this anchor remains anywhere a spec AC carries it
  (and that no orphan deferral exists). Preferred over a raw `grep` for the
  marker literal, which would self-match this spec/plan's own documentation of the
  marker (spec AC: no dangling deferral marker / no orphan backlog heading).
- `grep -n "^### llm-agent-module-agentic-boundary-extension" docs/backlog.md` →
  **zero matches** (heading removed) (spec AC: no orphan backlog heading).
- The overlay spec's previously-deferred AC reads `- [x]` and no longer carries
  its deferral marker, with its **descriptive prose byte-unchanged**
  (frozen-body carve-out) (spec AC: deferred AC closed without a body rewrite).
- `grep -n "design-altitude-only" docs/specs/agentic-well-architected-overlay/notes/coverage-parity.md`
  → the three boundary rows no longer carry it; they name `llm-agent` checks (the
  separate LLM08 row and the pass-condition prose legitimately still use the
  phrase) (spec AC: coverage-parity updated).
- **Expected-to-remain** (not failures): the anchor string still appears in this
  spec's body + README row (provenance) and the frozen overlay `plan.md`
  (immutable historical code-span). Do not chase these.

**Approach:**
- `docs/specs/agentic-well-architected-overlay/notes/coverage-parity.md` (a
  re-runnable artifact, not frozen prose): change the three direction-(b) rows
  from "design-altitude-only → backlog `#…`" to the named `llm-agent` checks
  (removing the backlog-anchor links). **Rewrite the "Net-new boundaries
  reconciled" section** so its now-false assertion ("exceed the current `llm-agent`
  surface … no Agentic-Top-10 content") reads past-tense — the module now covers
  them via the three checks — and drop the `docs/backlog.md#…` deferred-entry
  pointer there. Leaving only the table rows delinked would leave the paragraph
  internally contradictory.
- `docs/specs/agentic-well-architected-overlay/spec.md`: flip the deferred AC's
  checkbox `[ ]`→`[x]` and remove the `(deferred: …)` marker — **the only
  sanctioned edits**; leave the AC's descriptive prose byte-unchanged as the
  frozen record (the checkbox carries current truth). Do **not** reword the body.
- `docs/backlog.md`: remove the `### llm-agent-module-agentic-boundary-extension`
  entry (closed items leave the backlog). The only remaining inbound mention is
  the frozen overlay plan's historical code-span (not a hyperlink; immutable), so
  no tombstone is needed — the maintenance rule's tombstone exception fires on a
  *dangling link*, and there is none.

**Done when:** the four checks above pass (marker gone, heading gone,
coverage-parity remapped incl. the Net-new paragraph, AC checkbox flipped without
prose rewrite, lint clean) — and all four record edits land in **one commit** (no
partial half-open state).

### T5: Version bumps, projection refresh, changelog

**Depends on:** T1, T2, T3, T4

**Tests:**
- `core` `pack.toml` `[pack].version` == `.claude-plugin/plugin.json` version ==
  `0.4.14`; `architect` both == `0.8.1` (spec ACs: version bumps).
- `make build-self FORCE=1` succeeds; `git status` shows the expected `core`
  `.claude/` projection refresh and `marketplace.json` update, with **no**
  unexpected drift (spec AC: projection refreshed, no residual drift).
- `docs/product/changelog.md` `[Unreleased] → Added` carries an entry naming the
  **core 0.4.14** module extension as the primary change (architect 0.8.1 lens
  softening as the ride-along), distinct from the existing architect-0.8.0 overlay
  entry (spec AC: changelog entry).

**Approach:**
- Bump `core` 0.4.13 → 0.4.14 and `architect` 0.8.0 → 0.8.1, each `pack.toml` +
  `plugin.json` in lockstep.
- Add the `[Unreleased] → Added` changelog entry, headed on the core 0.4.14
  module extension (architect 0.8.1 named as the ride-along).
- Run `make build-self FORCE=1`; verify drift is confined to `core` projection +
  `marketplace.json`; clear any stray `__pycache__` before the drift check.

**Done when:** versions match, build-self is clean of unexpected drift, changelog
entry present.

## Rollout

Pure content/governance change. No infrastructure, no external systems, no
deployment sequencing. Delivery is the merge itself; "rollback" is a revert. The
only ordering constraint is internal (T5 runs last so projection +
`marketplace.json` reflect the final state) — captured by the `Depends on:` DAG
above.

## Risks

- **Altitude drift** — the new module checks creep into design-altitude prose,
  duplicating the overlay. Mitigated by the spec's `Never do` and by the
  control-altitude phrasing rule in T1; the adversarial + security reviewers
  check it on the diff.
- **Lens divergence** — the two `architect` lens copies drift during the T3 edit.
  Mitigated by the T3 `diff` test (the pack's standing byte-identical constraint).
- **Build drift** — a stray `__pycache__` or a missed `build-self` run leaves the
  drift gate red. Mitigated by clearing `__pycache__` and running `build-self
  FORCE=1` as the last task, then a clean `git status`.

## Changelog

- 2026-06-23: initial plan.
- 2026-06-23: spec-stage adversarial + security review revisions — decomposed
  execution isolation into three confinement axes (filesystem / egress-`hybrid` /
  resource), added the memory-poisoning write-gate, pinned the existing six
  checks' tags (LLM03 stays `tool`), mapped the boundaries to released OWASP ASI
  IDs (ASI02/03/05/06), constrained the frozen overlay-AC edit to checkbox +
  marker only (no prose rewrite), widened the dangling-reference check to all of
  `docs/`, re-pointed the dogfood at a synthetic agentic snippet (verdict not
  gated), and headed the changelog on the core bump.
