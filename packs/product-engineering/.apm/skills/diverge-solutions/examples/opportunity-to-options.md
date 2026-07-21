# Example: Opportunity to Solution Options

This example walks `diverge-solutions` from a free-form opportunity description
(no step-2 artifact) through three structured options to a recommendation and
artifact. It demonstrates the degrade path (Step 2 readiness), the option
schema, and the workspace.toml suggestion.

---

## Input

**Opportunity (free-form description, no `identify-opportunities` artifact):**

> "The team has confirmed that PEs spend 60–80% of shaping time re-explaining
> context to agents at each session start, with no durable per-initiative memory
> of prior framing decisions."

---

## Step 2 readiness check

No `identify-opportunities` artifact was provided. Checking skill roster —
`identify-opportunities` is not in the available skills.

Step 2 (`identify-opportunities`) provides JTBD grounding: the functional job
the PE needs done (reduce re-briefing overhead), the emotional job (confidence
that the agent starts from shared context), and the social job (signal to
stakeholders that shaping decisions are traceable). Without this grounding,
key bets in the options may miss JTBD depth — options are generated from the
confirmed signal, not a validated opportunity canvas.

User opted to proceed. A **Step 2 readiness** section will appear in the artifact.

---

## Intake and altitude check

Input is **initiative-scope**: affects all PE shaping work across the initiative,
not a single feature. Altitude confirmed. Proceeding.

---

## Generating options

Opportunity: durable per-initiative shaping memory to eliminate session-start
re-briefing overhead.

Three options spanning different mechanics, scopes, and bets:

**Option A — Structured shaping log**
*Mechanic:* PEs maintain a freeform markdown journal per initiative.
*Scope:* per-initiative, manually maintained.
*Approach:* A `shaping-log.md` file in the initiative directory. PEs record key
decisions, rejected options, and open questions after each session. Agents are
instructed (via SKILL.md convention) to read this file at session start before
any shaping work.
*Key bets:* PEs will consistently update the log after sessions (not skip it when
time-pressured); freeform prose is retrieval-friendly enough for agents to surface
the right context.
*Trade-offs:* Lowest tooling investment; highest maintenance burden. Drift-prone
when PEs are under pressure. No schema enforcement — an agent reading a stale or
sparse log gets partial context with no signal about staleness.
*Status:* parked

**Option B — Workspace.toml shaping section**
*Mechanic:* Structured TOML fields capture initiative shaping state.
*Scope:* initiative + cross-session, version-controlled alongside the work queue.
*Approach:* Add a `[ini-NNN.shaping]` section to `workspace.toml` that records the
current shaping phase, active spec path, key decisions, and open questions in a
machine-readable format. The `workspace-status` skill surfaces this at session
start automatically.
*Key bets:* TOML field updates are low-friction enough for PEs to maintain them
(the format is already established by the work queue); agents can reliably parse
and surface structured shaping state without hallucinating prose context.
*Trade-offs:* Leverages existing infrastructure (workspace.toml + workspace-status).
Requires schema discipline — fields must stay parseable. Slightly more rigid than
freeform prose; a field the PE wants to capture may not have a home yet.
*Status:* recommended

**Option C — Agent session-start orientation skill**
*Mechanic:* Active synthesis from git history and spec artifacts.
*Scope:* whole workspace; fires at every session start.
*Approach:* A new `orient-session` skill that reads git log, open specs, and
decision artifacts at session start and synthesises a context brief for the agent
— so PEs never need to re-brief manually.
*Key bets:* Synthesis quality is high enough to replace manual re-briefing without
introducing hallucinated context; the skill is maintainable as spec and decision
formats evolve.
*Trade-offs:* Highest capability ceiling. Also highest implementation cost and
ongoing maintenance. Synthesis failures are silent — an agent that synthesised
incorrectly may not surface the error until a shaping decision contradicts prior
decisions.
*Status:* parked

---

## Recommendation

**Workspace.toml shaping section** — the dominant bet (TOML is low-friction for PEs
already using the work queue format) is the most defensible of the three. Option A
relies on PE discipline under pressure; Option C's synthesis risk is asymmetric
(silent failures compound into bad shaping decisions). Option B's rigidity is the
acceptable cost: the schema can grow incrementally, and `workspace-status` already
surfaces the file at session start.

---

## Residual bets

Across all options: agents must be able to read and surface initiative context
reliably at session start — this is an assumption that holds across Options A, B,
and C and will need to be validated regardless of which is selected.

---

## Step 2 readiness

No `identify-opportunities` artifact was provided for this opportunity. The options
above were generated from the confirmed signal ("PEs spend 60–80% of shaping time
re-briefing agents"). Without a step-2 JTBD canvas, the key bets in each option
may miss emotional and social job dimensions — for example, whether the social job
(stakeholder traceability of shaping decisions) is better served by the structured
log (Option A, human-readable) or the TOML section (Option B, machine-readable
but less narrative). Running `identify-opportunities` first would ground these bets
before the PE selects an option.

---

## Artifact

```markdown
---
type: solution-options
slug: pe-shaping-memory
opportunity: "PEs spend 60–80% of shaping time re-explaining context to agents at each session start, with no durable per-initiative memory of prior framing decisions."
date: 2026-07-21
recommendation: Workspace.toml shaping section
---

# Solution Options: pe-shaping-memory

## Opportunity

PEs spend 60–80% of shaping time re-explaining context to agents at each session
start, with no durable per-initiative memory of prior framing decisions.

## Options

### Option A: Structured shaping log

**Approach:** PEs maintain a freeform markdown journal per initiative. Agents
read it at session start.
**Key bets:**
- PEs will consistently update the log after sessions.
- Freeform prose is retrieval-friendly enough for agent context surfacing.
**Trade-offs:** Lowest tooling investment; highest maintenance burden. Drift-prone
under pressure. No staleness signal.
**Status:** parked

### Option B: Workspace.toml shaping section

**Approach:** A `[ini-NNN.shaping]` section captures phase, active spec, key
decisions, and open questions in structured TOML. `workspace-status` surfaces
it at session start.
**Key bets:**
- TOML updates are low-friction enough for PEs already using the work queue.
- Agents can parse and surface structured shaping state reliably.
**Trade-offs:** Leverages existing infrastructure. Requires schema discipline;
slightly more rigid than freeform prose.
**Status:** recommended

### Option C: Agent session-start orientation skill

**Approach:** A new `orient-session` skill synthesises git log, open specs, and
decision artifacts into a context brief at every session start.
**Key bets:**
- Synthesis quality is high enough to replace manual re-briefing.
- The skill is maintainable as formats evolve.
**Trade-offs:** Highest capability ceiling and highest implementation cost.
Synthesis failures are silent.
**Status:** parked

## Recommendation

**Workspace.toml shaping section.** The dominant bet (TOML is low-friction for
PEs already using the work queue format) is the most defensible. Option A relies
on PE discipline under pressure; Option C's silent synthesis failures are
asymmetric risk.

## Residual bets

Agents must reliably surface initiative context at session start — shared
assumption across all three options.

## Step 2 readiness

No `identify-opportunities` artifact was provided. Key bets may miss emotional
and social JTBD dimensions. Running step 2 first would ground these before
option selection.

## Suggested workspace.toml entry

Add to `[ini-NNN.shaping_queue]` backlog:

```toml
{slug = "pe-shaping-memory", type = "shape"},
```

Use `capture-work` or edit `workspace.toml` manually.
```

---

## workspace.toml suggestion

Add to `[ini-NNN.shaping_queue]` backlog:

```toml
{slug = "pe-shaping-memory", type = "shape"},
```

Use `capture-work` or edit `workspace.toml` manually.
