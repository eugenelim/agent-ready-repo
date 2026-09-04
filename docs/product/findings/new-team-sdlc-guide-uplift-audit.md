# New-team SDLC adoption — journey map and guide uplift audit

> Discipline: audit (repository evidence + instrumented measurement).
> Confidence tags follow `adaptive-planning-survey.md`.
>
> **Reproduce every count here** with
> `python3 tools/audit-guide-affordances.py --ledger <path>`. The ledger records
> a line number for each hit, so any number below can be traced to the line that
> produced it.
>
> **Denominators.** The tree holds 24 pack manifests and 137 skills. Two are
> underscore-prefixed reserved authoring assets — `_example` and
> `_okf-pilot-cost-engineering` — which catalogue discovery skips:
> `_discover_pack_dirs` in
> `packages/agentbundle/agentbundle/commands/list_packs.py:94,104` admits a
> directory only when `not p.name.startswith("_")`. The **non-reserved
> catalogue corpus is 22 packs and 135 skills**, and every pack and skill
> percentage below uses it. Guide counts are over all 203 `.md` files under
> `guides/` except `AGENTS.md`.

**Question.** How does a new team adopt these packs across a whole SDLC, and
where must the guides be uplifted so that every skill has a chat input, a
demonstrated workflow input, a sample chat output, a stated outcome, and a
stated job to be done?

**Occasion.** 2026-09-03. The catalogue ships 22 non-reserved packs and 135
skills behind 203 guide files. No measurement existed of whether a newcomer can act from those
guides, and no guide covers the owner's own shaping-to-build route.

**Scope note.** This is an audit. It changes no guide. Every uplift row names the
file to change and the source to change it from.

---

## Part 1 — The route a new team actually walks

The catalogue ships three peer supervised loops — discovery, build, release —
with human gates at the handoffs (`guides/_shared/explanation/the-three-loops.md`).
A new team crosses them in six phases.

| Phase | What the team does | Packs | Scope | Owning guide |
| --- | --- | --- | --- | --- |
| 1 · Install | Get the CLI, install a profile, adapt an existing repo or seed a new one | `core` (+`full-ceremony`) | repo | `_shared/explanation/install-routes.md`, `core/how-to/adapt-to-project.md` |
| 2 · Shape | Turn a signal into a ratified intent | `desk-research`, `product-engineering`, `architect` (`inception` profile) | user | `product-engineering/`, `architect/`, `desk-research/` |
| 3 · Hand over | Admit the intent as repository work | `core` — `intake-intent` | repo | **none** (see G-1) |
| 4 · Build | Spec, plan, execute, gate, review, merge | `core` — `new-spec`, `work-loop` | repo | `core/how-to/plan-and-execute-non-trivial-work.md` |
| 5 · Govern | Circulate cross-cutting change; record settled decisions | `governance-extras` — `new-rfc`, `new-adr` | repo | `governance-extras/how-to/` |
| 6 · Release / report | Validate deployed; report engagement | `release-engineering`; `atlassian`/`linear`/`github` | repo | `release-engineering/how-to/run-a-release.md` |

**There is no one-command whole-lifecycle install.** `[high]` The three profiles
split across scopes and none includes release:

| Profile | Scope | Packs |
| --- | --- | --- |
| `inception` | user | `desk-research`, `product-engineering`, `architect` |
| `solution-architect` | user | `architect`, `desk-research`, `contracts` |
| `full-ceremony` | repo | `core`, `governance-extras`, `product-documentation`, `monorepo-extras` |

`release-engineering`, `product-strategy`, `experience-design`,
`frontend-engineering`, and `iac-terraform` are in no profile and must be
installed one at a time. Composition is left to the adopter, and no guide owns
the combined sequence.

---

## Part 2 — The shaping room

### Two chains ship, and nothing chooses between them

`[high]` The recursive intent chain and the six-step initiative chain both ship,
with no documented selection rule.

**Chain A — recursive intent** (`product-engineering/explanation/the-intent-tree.md`):

| Transition | Skill | Artifact |
| --- | --- | --- |
| signal → intent | `frame-intent` | `docs/product/intents/<slug>.md` |
| intent → tested intent | `de-risk-intent` | same file, `validation_hook` added |
| parent → children | `decompose-intent` | child intents one level down |
| leaf → delivery | `decompose-intent` | a handoff, not a spec |

Levels are an open recognized set — `product-vision`, `product-strategy`,
`capability`, `feature` — with Scale (app ↔ business-unit ↔ enterprise) as a
separate dimension (ADR-0033).

**Chain B — six-step initiative shaping** (`product-engineering/how-to/`):
`frame-situation` → `identify-opportunities` → `diverge-solutions` →
`de-risk-intent` → `place-bet` → `map-capabilities`, each writing into
`docs/product/shaping/<slug>/`.

A newcomer reading the how-to index sees twelve sibling how-tos with no entry
point and no ordering.

### Architecture attaches at shaping time but not at handover

`[high]` Concept co-shaping is documented well:
`_shared/explanation/shaping-a-new-engagement.md` describes product intent and
the architecture concept as two tracks that check each other, and
`architect/how-to/shape-an-architecture-concept.md` owns the ≤½-page concept.
`discovery-loop` runs an optional technical lens using `architect-design` and
`architect-diagram` when the pack is present.

The durable handoff is where it breaks. `workspace.toml` accepts
`kind = "design"` as a first-class shaping-queue artifact
(`core/reference/workspace-toml-schema.md:79,248`), but **no guide under
`guides/architect/` mentions `workspace.toml` at all** — verified by an
exhaustive grep of that tree. So an architecture artifact can be registered as a
dependency of a brief or spec, and nothing tells an architect to do it.

### Briefs

A delivery brief is a coordination artifact above the spec, at
`docs/product/briefs/<slug>.md`, never executable by `work-loop`
(`core/explanation/why-a-brief-layer.md`). The altitude is
`roadmap → brief → spec → AC`. Coverage is derived from each spec's own
`Status:` via `Brief:` back-links, so it cannot drift.

It is **required** when one coherent outcome needs several independently
shippable specs or crosses repositories; **skipped** when one feature intent maps
to one spec, or when `work-loop` direct-light applies. Lifecycle:
`Draft → Ready → Executing → Shipped`, with `Withdrawn`/`Cancelled` exits. A
`Ready` brief may carry zero specs, so Ready is not dispatchable.

---

## Part 3 — Handover to build: the largest single gap

`[high]` **G-1. The owner's actual route has no how-to.** The stated working
pattern is: shape intents with `desk-research` + `product-engineering` +
`architect`, then admit them with `intake-intent`. `intake-intent` is named in
exactly three guides — `core/how-to/start-or-remember-work.md`,
`core/reference/work-intake-routing-and-lifecycle.md`, and
`_shared/explanation/the-three-loops.md`. It is named in **zero** guides under
`guides/product-engineering/`, `guides/architect/`, or `guides/desk-research/`.

The skill itself is unambiguous — "Use when a raw or admitted request should
become a minimum repository intent for later shaping, without creating an RFC,
delivery brief, spec, or executable queue item." Nothing walks a shaper from a
finished intent to that call.

Consequence: the three upstream packs write durable artifacts at user scope, and
the guide set never closes the loop into repo scope. This is the same seam as
G-2 below.

`[moderate]` **G-2. Nothing owns the repository layout the upstream packs write
into.** The `inception` profile is user scope, but its skills write to
`docs/product/...` in a repo. No onboarding step creates or validates that target
layout before the first shaping run.

---

## Part 4 — Governance a new team inherits

| Artifact | Pack | Skill | Required when | States |
| --- | --- | --- | --- | --- |
| Charter | `core` (seed) | `init-project` / `adapt-to-project` | always, as a living doc | none — living |
| Spec + plan | `core` | `new-spec` | any full-mode risk trigger | `Draft → Approved → Implementing → Shipped`; `Archived` |
| ADR | `governance-extras` | `new-adr` | a settled cross-cutting decision with a real trade-off | `Proposed → Accepted \| Rejected`; then `Deprecated \| Superseded` |
| RFC | `governance-extras` | `new-rfc` | unresolved consequential direction, multi-owner circulation, reserved-boundary change | `Draft → Open → FCP → Accepted \| Rejected \| Withdrawn`; `Experimental` optional |

RFCs fan out after acceptance: architecture decisions become ADRs, concrete
behavior becomes specs, convention changes edit `docs/CONVENTIONS.md`.

`[moderate]` **G-3. RFCs and ADRs are not documented as consumers of shaping
output.** The owner's pattern sources RFC and ADR content from artifacts produced
by the three upstream packs. `guides/governance-extras/how-to/new-rfc.md` and
`new-adr.md` do not name an intent, a decision brief, a research survey, or an
architecture concept as an input. `desk-research` is the exception: it ships
`how-to/run-a-research-project-into-an-rfc.md`, which is the only documented
shaping-to-governance path and the correct template for the other two packs.

---

## Part 5 — The tracker boundary

The owner's position: feature intents, or slices within an intent or brief, are
copied into Jira/Linear/GitHub tickets; shaping is repo-centred and the delivery
systems are shallow shadow copies for engagement reporting.

`[high]` **The repository already states this principle — in a place no adopter
will find, and no code implements it.**

`packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
says, verbatim: *"The tree is the source of truth; the tracker is a render."* and
*"Never round-trip status back from the tracker."* It carries the projection
table:

| Canonical | `none` | Linear (lean) | Jira Align (deep) |
| --- | --- | --- | --- |
| product-vision / product-strategy intent | markdown | Initiative / label | Theme / Strategy tier |
| top (capability) intent | markdown | Initiative | Epic (Portfolio) |
| feature-level intent | markdown | Project | Feature (Program) |
| **spec / slice (leaf)** | a `core` brief | **Issue** | **Story** (Team) |
| story-as-trace (optional) | AC checklist | sub-issue / checklist | Story / sub-task |

It also states the limit: *"v1 ships the mapping + export shape … It does not
ship a live API integration."*

**Four findings follow.**

`[high]` **T-1. The position is undocumented in `guides/`.** No guide references
`tracker-projection.md` except one line in
`product-engineering/reference/intent-fields-and-modes.md`. The shipped tracker
guides — `_shared/how-to/choose-a-tracker-integration.md`,
`_shared/reference/tracker-vocabulary.md` — were delivered by
`docs/specs/m5-tracker-guides/` (Status: Shipped), whose objective was scoped to
"the tracker brief-**intake** landscape". The outbound direction was never in
scope. `tracker-vocabulary.md` explicitly says *"No row is a fixed mapping."*

`[high]` **T-2. Every shipped tracker guide leads with intake, i.e. the opposite
direction.** `choose-a-tracker-integration.md:10` — *"Use this when: tracked work
should become canonical repository work."* Same framing in
`atlassian/work-with-jira.md:32`, `linear/how-to/linear-brief-intake-and-sync.md:10`,
and `github/how-to/intake-a-github-milestone-as-a-brief.md:10`. Intake is the
right capability to keep, but presenting it as *the* route inverts the model.

`[high]` **T-3. No executable route pushes slices out.** All three
`*-brief-intake` skills are read-only by contract. The `*-refresh` processors
permit only comment, display-status, trace/PR links, and closure — Linear and
GitHub cannot create an issue or rewrite a body; Jira Align refresh is
acquisition-only. `work_intake_refresh.py` recognises repo-origin authority and
returns `projection_drift` without invoking any projector. Generic `jira` and
`jira-align` clients can create and update records, but nothing connects them to
`decompose-intent` or the projection table. **The gap is a documented mapping
with no exporter, not a missing decision.**

`[moderate]` **T-4. The Atlassian guides treat Jira story content as the thing to
improve.** `guides/atlassian/how-the-atlassian-pack-works.md:65` —
*"`jira` runs when you say 'apply the approved changes'… This is the first step
that writes to Jira."* The documented journey is backlog review → draft better
stories → write descriptions and acceptance criteria back to Jira. That is
materially richer than a shadow copy and contradicts the owner's position
directly. This is a **product decision to settle, not a doc bug**: either the
Atlassian pack serves teams whose shaping genuinely lives in Jira (in which case
the two models must be named and bounded), or it is realigned.

**Engagement reporting is the one part already aligned** `[high]`, and Jira-only:
`flow-metrics` reads Jira changelogs to canonical JSON, `ai-adoption-report`
reads only those files, and neither mutates Jira. Ten metrics; cohort split via
`--cohort-jql 'labels = ai-assisted'`. Documented limits: no Change Failure Rate
or MTTR without deployment data, deliberately no individual-productivity report,
point-in-time not live, and unlabelled AI-assisted work misclassifies into the
control group. No Linear or GitHub equivalent exists.

---

## Part 6 — Measured guide audit

**Method.** A detector script classified all 203 `.md` files under `guides/`
(excluding `AGENTS.md`) for five affordances, recording a line number for every
hit so each verdict is spot-checkable. Detectors were keyed to the measured house
conventions — `**Use this when:**` appears in 75 files, `## Before you start` /
`## Prerequisites` in 43 — rather than open-ended prose. The instrument was
verified in both directions before its numbers were used: it correctly scores
`architect/how-to/diagram-a-system.md` at 5/5, and one false negative was found
and fixed (the house form for a chat input is a bare ` ```text ` fence holding a
plain sentence, which raised A from 15% to 27%).

| Affordance | Definition | Present | Coverage |
| --- | --- | --: | --: |
| **A** chat input | a literal, copy-pasteable thing to type | 43/203 | **21%** |
| **B** demonstrated input | a worked example of what you supply into the workflow | 8/203 | **4%** |
| **C** sample output | an illustration of what the agent emits back | 67/203 | 33% |
| **D** stated outcome | an explicit end state, outside the opening framing | 21/203 | **10%** |
| **E** job to be done | who this is for / when to reach for it | 95/203 | 47% |

One file of 203 has all five — `architect/how-to/diagram-a-system.md`, the
exemplar every uplift row should be measured against. Sixty-six have none.
**Forty-eight guides name a skill in prose ("invoke `frame-intent`") without
ever showing what to type** — the dominant failure mode.

### By Diataxis kind

| kind | files | A | B | C | D | E |
| --- | --: | --: | --: | --: | --: | --: |
| how-to | 88 | 24 | 6 | 35 | 13 | 82 |
| explanation | 56 | 5 | 1 | 10 | 2 | 2 |
| reference | 38 | 6 | 1 | 12 | 1 | 2 |
| tutorial | 17 | 8 | 0 | 10 | 5 | 8 |
| *(no `kind:`)* | 4 | 0 | 0 | 0 | 0 | 1 |

The four rows without a `kind:` are `_shared` navigation indexes, kept in the
denominator because a missing `kind:` is itself a gap.

How-tos carry E almost universally (82/88) and A/D almost never — 24 and 13 of
88. Tutorials — the genre whose whole job is a worked run — carry **zero**
demonstrated inputs.

### The structural cause: the affordances already exist, one level up

`[high]` Fourteen of the 22 published packs (64%) ship a `JOURNEY.md`, and
**all fourteen carry a complete `contract:` block**. The authoritative validator
is `packages/agentbundle/agentbundle/catalogue_tooling/journey_validator.py`,
which defines `REQUIRED_CONTRACT_KEYS` at line 22 and rejects any contract field
outside the known set (lines 69-75).

| Journey field | Where it lives | Maps to | Coverage |
| --- | --- | --- | --- |
| `useItWhen` | `contract:` (required) | **E** job to be done | 14/14 |
| `youProvide` | `contract:` (required) | **B** demonstrated input | 14/14 |
| `youReceive` | `contract:` (required) | **D** stated outcome | 14/14 |
| `yourDecisions` | `contract:` (required) | human gates | 14/14 |
| `goodOutputDescription` | top level (optional) | **C** sample output | 4/14 |
| — | — | **A** chat input | **no such field exists** |

So **three** affordances are already authored and validated at pack level in
every journey, and a fourth exists in 4 of 14 — and none of them is projected
into the guides. The contract has no slot for the literal chat input at all.

`goodOutputDescription` is a **top-level** optional journey field, not a
contract key: `journey_validator.py` would reject it inside `contract:`. That
distinction matters for the fix in U8.

`[high]` **The chat inputs also already exist, in a third place.** Of 135
skills, 56 (41%) carry a quoted example utterance in their SKILL.md
`description`, and 49 (36%) say "Triggers on". Coverage is highest exactly where
the guides are weakest:

| Pack | skills | phrase in SKILL.md | guides | guides showing a chat input |
| --- | --: | --: | --: | --: |
| `product-strategy` | 9 | **9/9 (100%)** | 7 | **0/7** |
| `product-engineering` | 15 | **13/15 (87%)** | 18 | **1/18** |
| `architect` | 5 | 4/5 | 11 | 2/11 |
| `core` | 18 | 5/18 | 34 | 10/34 |
| `experience-design` | 20 | **0/20** | 5 | **0/5** |
| `frontend-engineering` | 9 | **0/9** | 6 | 1/6 |

**Thirty-three guides can gain a correct chat input by lifting a phrase that
already exists in the skill they document.** That is a projection task, not an
authoring task. Twenty-one distinct skills supply the strings, including most of
the shaping spine: `frame-intent` → "shape this", `de-risk-intent` →
"de-risk this", `decompose-intent` → "decompose this",
`identify-opportunities` → "map the jobs", `map-capabilities` →
"map our capabilities", `workspace-status` → "workspace status",
`init-project` → "start a new project", `new-spec` → "new spec".

`work-loop` is the notable absence: it carries no quoted utterance, so the
build-loop entry point needs authored phrasing rather than projection.

`experience-design` (20 skills) and `frontend-engineering` (9 skills) are the
opposite case: no invocation phrasing exists anywhere, so those must be
authored. That is why U14 sits outside the first brief — it is the only row with
no source to project from.

---

## Part 7 — The uplift table

Rows are ordered by the phase a new team reaches them. **Action** names the
cheapest sufficient move; **Source** names where the content comes from, so no
row is an invitation to invent.

| # | Phase | Target | Gap | Action | Source | Effort |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | 3 · hand over | **new** `guides/product-engineering/how-to/hand-an-intent-to-build.md`, plus a link from `guides/architect/README.md` and `guides/desk-research/README.md` | G-1: the owner's route has no how-to | Author the one missing how-to — finished intent → `intake-intent` → what Core does → which of spec / brief / RFC follows — and link it from the other two shaping packs so no shaping path dead-ends | `intake-intent/SKILL.md`, `core/reference/work-intake-routing-and-lifecycle.md`, `_shared/explanation/the-three-loops.md` | S |
| U2 | 2 · shape | 12 how-tos in `guides/product-engineering/how-to/` | A 2/18, D 2/18 | Add a ` ```text ` chat-input fence and a "What you have now" close to each | the 13 trigger phrases already in `product-engineering` SKILL.md descriptions | M |
| U3 | 2 · shape | 7 guides in `guides/product-strategy/` | A **0/7**, D 0/7, C 1/7 | Same two additions; worst-covered pack with a 100%-ready source | all 9 `product-strategy` SKILL.md trigger phrases | S |
| U4 | 5 · tracker | **new** `guides/_shared/how-to/project-slices-to-a-tracker.md` | T-1: the owner's position is unreachable | Promote `tracker-projection.md` to an adopter guide; add the missing GitHub and Jira Software columns; state plainly that export is manual in v1 | `decompose-intent/references/tracker-projection.md` (verbatim table + the one-way rule) | M |
| U5 | 5 · tracker | `_shared/how-to/choose-a-tracker-integration.md`, `_shared/reference/tracker-vocabulary.md` | T-2: both lead with intake | Add the outbound direction as the *default* and reframe intake as the brownfield entry; link U4 | U4, plus each `*-refresh` skill's permitted-action list | S |
| U6 | 2 · shape | `guides/architect/` (11 files) | G: no architect guide mentions `workspace.toml` | Add a "register the artifact" step showing a `kind = "design"` entry that a brief or spec can declare in `needs` | `core/reference/workspace-toml-schema.md:79,184,248` | S |
| U7 | 4 · govern | `governance-extras/how-to/new-rfc.md`, `new-adr.md` | G-3: shaping output is not named as an input | Add an "Inputs" section naming intent, decision brief, research survey, architecture concept | `desk-research/how-to/run-a-research-project-into-an-rfc.md` — the shipped template | S |
| U8 | all | `journey_validator.py`, `contracts/`, 14 `JOURNEY.md`, the docs and tests | A has no slot in the contract schema | Add `youType` (the literal first utterance) to the `contract:` block as **optional**, then back-fill 14 packs. The contract is closed — `journey_validator.py:69-75` rejects unknown fields — so this touches the validator, the authoring standard, the generator, and its tests, and a required field would break external packs | the 64 skills that already carry a quoted trigger | M |
| U9 | all | the 33 guides in the instrument's harvest table | 48 guides name a skill but show no input | Mechanical pass: lift each skill's phrase into a chat-input fence | the harvest table printed by `tools/audit-guide-affordances.py` | M |
| U10 | 2–4 | 17 tutorials | B **0/17** | Give each tutorial one worked input — the actual answers a reader gives to the elicitation, not a description of them | `architect/how-to/diagram-a-system.md` is the 5/5 exemplar | M |
| U11 | 1 · install | **new** `guides/_shared/how-to/install-the-whole-lifecycle.md` | no guide owns cross-scope composition | One ordered page: CLI → `inception` (user) → `full-ceremony` (repo) → the five packs in no profile → `release-engineering` last | `profiles/*.toml`, `_shared/explanation/install-routes.md`, `packs/release-engineering/pack.toml` | S |
| U12 | 2 · shape | `product-engineering/explanation/the-intent-tree.md` | two shaping chains, no selection rule | State when to use recursive intent vs the six-step chain, or record that one is legacy | ADR-0033; `product-engineering/JOURNEY.md` | S |
| U13 | 6 · report | `guides/linear/` (2 files), `guides/github/` (2 files) | 0/2 on four of five affordances each | Bring both to the `atlassian` baseline; both are two-file packs | `atlassian/` guides; the two packs' `JOURNEY.md` contracts | S |
| U14 | 2 · shape | `guides/experience-design/`, `guides/frontend-engineering/` | 29 skills, **0 trigger phrases anywhere** | Author invocation phrasing into the 29 SKILL.md descriptions first, then project | none — this is the only genuinely new authoring | L |
| U15 | all | `guides/README.md`, `contracts/guide.schema.json` | no sequence, prerequisites, or effort | Add the path axis from Part 8. `guide.schema.json` sets `additionalProperties: false`, so a new `path:` key needs a schema change — first test whether the existing optional `journey` + `order` keys can carry a path | Part 8; `contracts/guide.schema.json:33-56` | S |

**Sequencing.** U1, U4, U5, U11 unblock a new team and are small. U8 is a
**regression gate**, not a content source: one pack-level `youType` cannot supply
distinct inputs to 30 skill-specific guides, so it prevents the affordance from
being dropped again but does not do U2/U3/U9's work. Land it before the bulk
passes so they cannot regress; the per-guide × per-skill mapping those passes
consume is the harvest table emitted by
`tools/audit-guide-affordances.py`. U14 is the only row requiring net-new content
and should be scheduled independently.

---

## Part 8 — Grouping the guides as a curriculum

`guides/README.md` already carries two of the three axes a learner needs: a
jobs-to-be-done table ("I need to…") and a role list ("Choose by role"). What it
lacks is **sequence** — nothing states order, prerequisites, or effort — so a
newcomer gets a menu instead of a path.

### What Anthropic Academy does structurally

`[moderate]` **This subsection is the audit's only non-repository evidence.** It
comes from a web search and one fetch of the public catalogue on 2026-09-03, not
from this codebase, and it is a structural observation rather than a measured
claim. Sources: <https://anthropic.skilljar.com/> (catalogue page, fetched
2026-09-03) and secondary summaries including
<https://aiproductivity.ai/blog/anthropic-academy-free-courses-guide/> and
<https://www.termdock.com/en/blog/anthropic-academy-claude-courses-guide>.
Secondary sources disagree on the course count (13, 14, and 25 depending on
whether audience variants are counted separately), so treat the count as
approximate; the four structural moves below were visible on the catalogue page
itself.

Anthropic Academy organises ~25 catalogue entries on a Skilljar taxonomy of
**Plans → Paths → Courses → Lessons**, with four transferable moves:

1. **Audience-first tracks, not feature-first.** Three pillars — Build with
   Claude / Claude for work / Claude for personal — or equivalently AI Fluency
   (non-technical) / Product Training / Developer Deep-Dives. The split is by who
   you are, not by which product surface a page describes.
2. **A named `101` entry point per surface.** Claude 101, Claude Code 101, Claude
   Platform 101. Each track has an unmistakable front door.
3. **Paths as a first-class container above courses,** with an explicit
   recommended order — e.g. Claude Code 101 → Claude Code in Action →
   Introduction to Agent Skills → Introduction to Subagents.
4. **Audience variants over one spine.** AI Fluency is re-cut seven ways
   (educators, students, nonprofits, small business, builders, creative work)
   rather than rewritten per audience.

Stated effort per course is 30 minutes to ~2 hours, with a completion
certificate. Notably, the Academy catalogue page itself states **no
prerequisites and no durations** per course — so prerequisites are the axis to do
better than the reference, not to copy.

### The proposed structure

Keep Diataxis as the **document-type** axis — it is already frontmatter (`kind:`)
and drives generated navigation. Add an orthogonal **path** axis. Nothing moves
on disk, so the generated pack navigation and every existing URL survive.

One constraint to settle first: `contracts/guide.schema.json` sets
`additionalProperties: false` (line 56), so a new `path:` key is invalid until
the schema admits it. The schema already carries two optional keys that may be
enough — `journey` (a slug association, line 33) and `order` (a sort weight,
line 39). Test whether a path can be expressed as a `journey` before adding a
third key.

| Path | Front door (`101`) | Ordered course | Audience | Effort |
| --- | --- | --- | --- | --- |
| **P1 · Adopt the catalogue** | `install-routes` | install route → profile → `adapt-to-project` **or** `init-project` → `workspace-status` | anyone, first hour | ~1 h |
| **P2 · Shape what to build** | `the-intent-tree` | evidence (`desk-research`) → frame (`frame-intent`) → de-risk → decompose → architecture concept → **hand over (`intake-intent`)** | PM, product engineer, strategist | ~3 h |
| **P3 · Build it** | `plan-and-execute-non-trivial-work` | `workspace-status` → `new-spec` → `work-loop` → review → merge | engineer, agent | ~2 h |
| **P4 · Decide together** | `governance-index` | when RFC vs ADR vs spec → author → circulate → follow-on fan-out | tech lead, architect | ~1.5 h |
| **P5 · Ship and report** | `the-release-loop` | release loop → G5 → tracker projection → flow/DORA reporting | delivery lead, SRE | ~2 h |
| **P6 · Extend the catalogue** | `why-catalogue-curation` | assimilate → author a skill → author a pack → publish | AI enablement, catalogue owner | ~3 h |

Three rules make the paths hold their value:

- **Every path ends at a handoff, not at an artifact.** P2 ends at
  `intake-intent`, not at a written intent. This is exactly the gap U1 fills, and
  the path structure is what makes its absence visible.
- **Each course states its prerequisite path and its first-value moment** — the
  point at which the reader has something real. This is the axis the reference
  implementation omits.
- **Role variants re-cut P2 and P3 rather than duplicating them,** following the
  AI Fluency pattern: one spine, several entry ramps.

The owner's stated route is exactly **P2 → P3, with P4 drawing on P2's
artifacts.** That route is currently unwalkable end-to-end, because its final
step (U1) is undocumented and its governance inputs are unnamed (U7).

---

## Part 9 — Verified defects, fix-now

Each was confirmed against the file. These are wrong, not merely thin.

| # | File | Defect | Evidence |
| --- | --- | --- | --- |
| D1 | `product-engineering/how-to/frame-a-situation.md:93,107` | Tells the reader to run `queue-add`, a skill two renames dead | not in `packs/core/pack.toml`; `capture-work` is now itself a deprecated alias routing to `work-intake` |
| D2 | `_shared/how-to/install-a-profile.md:31,32`; `core/tutorials/start-a-new-project.md:18,35` | Names the pack `research`; it is `desk-research` | `profiles/inception.toml:22` — `pack = "desk-research"`; no `packs/research` exists |
| D3 | `product-engineering/reference/intent-fields-and-modes.md:77` | Documents a `[product-engineering]` config table | `frame-intent/SKILL.md:176,183` resolves `[product] output_dir` |
| D4 | `_shared/explanation/the-three-loops.md` | "**No human gates in the loop itself**" | `work-loop/SKILL.md:331` — "the **G-plan sequence** — two human approvals required" |
| D5 | `release-engineering/README.md:12` | "The pack ships two primitives" | ships three: `release-lead`, `release-loop`, `define-slo` |
| D6 | `core/explanation/role-journeys.md` | Names a `tracker-brief-intake` skill | that string appears in no other file in the repo; the real skills are `jira-`/`linear-`/`github-brief-intake` |
| D7 | `product-engineering/how-to/frame-a-situation.md:87` | Shows a legacy `{slug, type}` workspace entry | schema requires `path`/`locator`, `kind`, `source`, `summary`, `needs` — legacy entries are readable but **never dispatchable** |

### Found while fixing the seven, and fixed

| # | Where | Defect |
| --- | --- | --- |
| D8 | `atlassian/how-to/crawl-and-publish-confluence.md`, `measure-flow-and-dora-metrics.md` | linked `../reference/atlassian-skills.md`; the file is at `../atlassian-skills.md` |
| D9 | `core/explanation/role-journeys.md` | six journey-map links dropped the `docs/` segment |
| D10 | `core/how-to/plan-and-execute-non-trivial-work.md`, `governance-extras/how-to/new-adr.md`, `new-rfc.md` | eleven links to `../../../CONVENTIONS.md`; the file is at `docs/CONVENTIONS.md` |

All three were already broken at HEAD and are unrelated to the uplift; they were
corrected because they sit in files this change touches.

The defect behind D1 and D7 also ran deeper than the guides. `frame-situation`
and `diverge-solutions` **emit** the legacy entry and named the dead
`queue-add`, and `run-okr-cascade` *writes* that shape straight into
`workspace.toml` — so every gap it recorded was invisible to the queue it was
recording into. Fixing the guides alone would have left them contradicting their
own skills, so the skills were corrected too (`product-engineering` 0.13.9,
`product-strategy` 0.2.5).

### Also fixed — the rest of the guide tree's broken links

Twenty more broken relative links across 13 files this change did not otherwise
touch, all broken at HEAD, in four classes:

| Class | Links | Cause |
| --- | --: | --- |
| `../../../CONVENTIONS.md` | 5 | dropped the `docs/` segment; the file is `docs/CONVENTIONS.md` |
| `../../../architecture/…` | 3 | same, for `docs/architecture/pack-layout.md` and `credentials.md` |
| `../../../product/journeys/…` | 1 | same, for `docs/product/journeys/` |
| stale `desk-research` stems | 7 | the pack and two of its files were renamed; links kept `research-pack`, `desk-research-methodology`, and `desk-research-pipelines` |
| `guides/frontend-engineering/README.md` | 4 | site URLs written relative, three levels up, which leaves the repository |

The last class is worth naming: the links were reaching for the published
`/packs/<pack>/` and `/journeys/<pack>/` pages, which is the house convention
used four times each in the `atlassian` guides. They were rewritten to that
absolute form rather than to repository paths, because that is what the text
meant and what renders on the site.

`guides/` now carries **zero** broken relative links. Absolute site URLs are a
separate class that a filesystem check cannot judge; `make site-link-check` is
their gate.

D1, D2, and D6 each hand a newcomer a command or name that does not exist. D7
teaches an entry shape that will not dispatch.

---

## Result — measured after the uplift shipped

The uplift was executed in one session on 2026-09-03. Re-running
`python3 tools/audit-guide-affordances.py` against the shipped state:

| Affordance | Before | After | Change |
| --- | --: | --: | --: |
| **A** chat input | 43 (21%) | **92 (45%)** | +49 |
| **B** demonstrated input | 8 (4%) | 10 (5%) | +2 |
| **C** sample output | 67 (33%) | 67 (33%) | — |
| **D** stated outcome | 21 (10%) | **65 (32%)** | +44 |
| **E** job to be done | 95 (47%) | 101 (49%) | +6 |

By genre, where it matters most:

| kind | A before → after | D before → after |
| --- | --- | --- |
| how-to (91) | 24 → **60** | 13 → **52** |
| tutorial (17) | 8 → **13** | 5 → **10** |

Guides that name a skill without showing what to type fell from **48 to 21**.
Guides carrying none of the five fell from 66 to 56. The harvest backlog — a
guide with no chat input whose skill already has a phrase — fell from 33 to 12.

Skill invocation phrasing rose from **56 (41%) to 85 (63%)** of 135 skills, and
`Triggers on` from 49 to 78, because `experience-design` (20 skills) and
`frontend-engineering` (9) went from zero documented utterances to full
coverage.

**What did not move.** C is unchanged at 33%: no slice targeted sample outputs,
and it remains the softest of the five counts (see Known unknowns). B rose only
2, from the two `core` tutorials that gained a worked question-and-answer
exchange; the other 15 tutorials still describe their inputs rather than
demonstrate them. Both are the honest remainder, not a rounding artifact.

## Method and limits

**Instruments.** `tools/audit-guide-affordances.py`, shipped with this audit,
scores all 203 guide files for the five affordances and all 137 SKILL.md
descriptions for an invocation phrase, recording a line number for every hit. It
also emits the per-guide × per-skill harvest table that U9 consumes — the 30
guides and the 21 skills whose phrasing they can lift. Run it with `--ledger` to
write the full evidence ledger. Journey-contract and profile coverage were
measured by direct grep against `journey_validator.py` and `profiles/*.toml`.

Three headless Codex investigators produced the journey, tracker, and guide
inventories; the guide-inventory run reported `WORKER_BLOCKED` at 177 files and
was replaced by the detector. One independent Codex reviewer then attacked this
audit and the derived intent and brief; its sustained findings are folded in.

**Adopted after verification.** Reported findings were checked against the files
before entry here. One was **refuted and dropped**: the claim that
`install-routes.md` states the standalone CLI artifact has not shipped — no such
statement exists. One citation was corrected (`why-a-brief.md` →
`why-a-brief-layer.md`). One was **narrowed**: of nine files matching the stale
`research` pack name, only four sites in two files are wrong; the rest correctly
use `research` as an artifact *kind*. `/deep-research` and `/applied-research`
were checked and are rejected-alternative prose, not stale commands.

**Corrected after two independent review rounds.** Every count below moved at
least once. The instrument is in the repository precisely so the next reader can
re-derive them rather than trust them.

| Claim | First draft | Corrected | Cause |
| --- | --- | --- | --- |
| pack / skill denominator | 24 packs, 137 skills | 22 packs, 135 skills | two underscore-prefixed reserved authoring assets counted as shipped |
| A chat input | 55 (27%) | **43 (21%)** | a quoted sentence in running prose was read as a prompt; it is usually an illustration |
| D stated outcome | 23 (11%) | **21 (10%)** | a bare `## Verify` heading is an instruction, not an end state |
| C sample output | 68 (33%) | **67 (33%)** | one fence was counted as both an input and an output; a fence now has exactly one role |
| skills with a phrase | 64 (47%) | **56 (41%)** | a straight apostrophe was treated as a quote delimiter, so `"who's authoritative — STORM's"` became a fake utterance in eight descriptions |
| `Triggers on` | 53 | **49** | the regex also matched any bare occurrence of "trigger" |
| guides naming a skill with no input | 43 | **48** | follows from the tightened A |
| harvestable guides | 30 | **33** | follows from the tightened A |
| journey affordances | "four of five already authored" | **three universally, a fourth in 4/14** | `goodOutputDescription` is a top-level optional field, not a contract key |

Two structural claims were also wrong: `youType` was described as a free-form
additive change when `journey_validator.py:69-75` rejects unknown contract
fields, and a `path:` frontmatter key is invalid against
`contracts/guide.schema.json` (`additionalProperties: false`) until the schema
admits it. `work-loop`'s "continue" appeared in the first draft's list of
liftable phrases and was one of the eight apostrophe false positives; it is gone.

**Known unknowns.**

- Affordance detection is regex-based. It measures whether a guide *has the
  shape* of a chat input or an outcome, not whether the content is any good.
  Every number is a lower bound on quality.
- **Residual false positives, named rather than claimed absent.** C still counts
  a long fenced example as a sample output even when the fence illustrates a
  schema rather than an agent's reply — for example the TOML receipts at
  `guides/core/reference/workspace-toml-schema.md:203`. That is arguably a true
  positive (the agent does write those entries) but it is not a chat transcript,
  so C is the softest of the five counts. Anyone tightening it should add that
  line as a negative fixture first.
- Skill phrase detection reads only the SKILL.md `description`. A skill that
  documents its invocation in its body but not its description reads as missing.
- Effort tags (S/M/L) in Part 7 are unmeasured judgment.
- Path effort estimates in Part 8 are modelled on the reference's stated
  30-minute-to-2-hour range, not measured on this corpus.
- T-4 (Atlassian writes story content back to Jira) is a product-model conflict.
  This audit records it; it does not resolve it.
- No adopter has been observed walking any of these paths. Every journey and
  measurement claim is derived from repository evidence, not from use. The one
  exception is Part 8's reference-implementation subsection, which is sourced
  from the public Anthropic Academy catalogue and is labelled inline.
- Part 8's course-count figure is approximate: secondary sources disagree
  (13/14/25) depending on how audience variants are counted.
