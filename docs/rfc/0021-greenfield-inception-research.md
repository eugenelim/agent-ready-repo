# Research: greenfield idea→repo bootstrapping (for RFC-0021)

> Discipline: applied (practitioner-pattern survey)

Prior-art + best-practice + anti-pattern survey for the greenfield front-door.
Confidence per finding: `[high]`/`[moderate]`/`[low]`/`[uncertain]`.
Independence calibrated per practitioner taxonomy (same vendor/employer = one).
Recency flag: LLM-agent systems are <2yr in a fast-moving domain — cited as
current-generation; walking-skeleton/inception are slow-moving (no penalty).

## Findings

**F1 — Two paradigms exist for idea→repo. `[high]`** Scaffold-from-template
(cookiecutter / copier / Yeoman / `create-*`) vs multi-agent generation
(MetaGPT / ChatDev / AutoDev). Independent sources across both families.

**F2 — spec-kit is greenfield-first; we are the inverse. `[high]`**
`specify init` + a constitution bootstraps a new project; brownfield is still
only an open extension proposal (spec-kit #1436). Our repo has `adapt-to-project`
(brownfield) and lacks the greenfield front-door — confirming the gap is real.
Sources: spec-kit repo (primary), MS Learn lab, Scott Logic review — independent.

**F3 — Walking skeleton / tracer bullet / steel thread is THE principled
anti-yolo. `[high]`** A thin end-to-end slice that links the main architectural
components to validate the architecture early; "small integration pain all
along the way" beats a big cleanup. Cockburn (origin), Pragmatic Programmer
(tracer bullet), Rubick (steel threads), Code Climate, Equal Experts — independent,
slow-moving domain.

**F4 — Structured inception precedes code. `[high]`** Lean Inception (Fowler):
a focused kickoff that sets direction, MVP, and explicitly "NFRs, technical
architecture, tech stack, path to production," plus "a short architecture
decision log for each major choice — what you picked, why, alternatives
rejected, re-evaluation date." Value gate: "if you cannot explain the business
value in plain language, pause; code should not start yet." Fowler (primary) +
discovery-phase practitioner sources.

**F5 — The current spec-driven / agentic-SDD landscape to situate against
(replaces the abandoned Microsoft/AutoDev thread).**
- **BMAD-METHOD** `[high]` on framing, `[moderate]` on exact chain. Agent-
  orchestrated SDLC; the homepage confirms an "Analysis Phase: From Idea to
  Foundation," "Named Agents," and ideation→planning→agentic-implementation
  producing explicit version-controlled artifacts (docs.bmad-method.org,
  fetched). Secondary sources (GitHub, Medium guides) report the greenfield
  chain **analyst → project-brief → PM → PRD → architect → stories → code** —
  independently the *same* brief→foundation chain as our trilogy. The closest
  cousin to RFC-0021. Chain confirmed only via secondary → `[moderate]`.
- **OpenSpec** (Fission-AI) `[high]` (concepts.md fetched). Lightweight,
  **proposal-first**: `proposal → specs → design → tasks → implement`, with
  **delta specs** (ADDED/MODIFIED/REMOVED) merged into source-of-truth specs on
  archive; 20+ agents, no lock-in, lighter than spec-kit. Corroborates
  RFC-0019's brief/spec + contract-delta shape.
- **cc-sdd** (gotalab) `[moderate]`. npm SDD harness bringing Kiro-style
  `discovery → spec-init → requirements → design → tasks → impl` (EARS) to
  Claude Code/Codex/Cursor/etc.; "turn approved specs into long-running
  autonomous implementation." Its `discovery` front maps to our inception.
- **Intent** (Augment Code) `[moderate]`. Platform with **living specs** (the
  spec updates as the implementation changes; agents implement from current
  state) + coordinated multi-agent execution + enterprise compliance.
  Corroborates RFC-0019's auto-rollup coverage and spec-as-validation-gate.

(AutoDev ruled out by user; Copilot Workspace dropped — these four are the
grounded reference set the user named.)

**F6 — Multi-agent "AI software company" generates idea→repo. `[high]`**
MetaGPT: "Code = SOP(Team)"; one-line requirement → PRD / design / tasks / code
via PM/architect/engineer roles communicating through structured documents.
ChatDev: dialogue-based variant. Sources: arXiv 2308.00352 (primary) + IBM +
GitHub — independent.

**F7 — Template UPDATE support (copier) maps to our `.upstream` merge. `[moderate]`**
Copier is unique among scaffolders in syncing template evolution into already-
generated projects ("code lifecycle management"); cookiecutter/Yeoman can't.
This validates `adapt-to-project` + `.upstream` as the re-sync mechanism.
Sources: copier docs (primary) + cookiecutter.io comparison (vendor — counts as
one) + recallstack. Independence partial → `[moderate]`.

**F8 — Enterprise golden-path scaffolding = Backstage software templates.
`[moderate]`** `template.yaml` the scaffolder reads; encodes org tech stacks,
standards, CI/CD, security/compliance; ING's "Golden Path plugin" is a
meta-template stitching several team-owned templates. Maps to our stack packs
(RFC-0020). Sources: Backstage docs (primary, Spotify) + Red Hat + Roadie.

**F9 — The throwaway-vs-structured gate. `[moderate]`** Practitioner guidance:
"if the project is a single script or throwaway prototype, scaffold it directly;
for projects with real tech-stack/structure/tooling decisions, use the project
initialization workflow." Fewer independent sources (agent-skill catalogues,
practitioner blogs) → `[moderate]`; but it converges with the Lean-Inception
value gate (F4).

## Anti-patterns

**AP1 — yolo-prototype-then-cleanup. `[moderate]`** Building a throwaway to
"figure it out," then retrofitting structure — loses the research rationale and
the foundation. The walking skeleton (F3) is the deliberate replacement.

**AP2 — autonomous multi-agent over-generation. `[low]` (survivorship-bias
flagged)** Full "AI software company" generation (MetaGPT / ChatDev, and the
autonomous end of BMAD) produces impressive demos, but reported production
maintainability/quality is uneven; the blogs that survive are the successes.
Treat the agent-orchestrated SOP as a paradigm to *borrow the structure from*,
not adopt as an autonomous engine wholesale.

## Implication for RFC-0021

**BMAD independently validates the chain** (analyst→brief→PM→PRD→architect ≈
our 0021→0019→0020), so the *structure* is proven. Decline the autonomous
multi-agent *engine* (MetaGPT/ChatDev, BMAD's autonomous end). Instead
**compose our existing single-purpose skills** (brief → foundation → spec →
work-loop) and add the two genuinely-missing pieces the prior art validates: a
**structured inception gate** (F4 + F9) and a **walking skeleton** (F3), with
copier-style **re-sync** (F7) via existing machinery. Boring, maintainable,
charter-aligned (habit not infra) — borrowing the *agent-orchestrated
structured-document handoff* (BMAD, MetaGPT) without the agent-company.
OpenSpec's delta-specs and Intent's living-specs separately corroborate
RFC-0019's contract-delta + auto-rollup coverage.
