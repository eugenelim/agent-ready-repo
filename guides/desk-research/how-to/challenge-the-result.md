---
title: "Challenge the result"
summary: "Argue against the synthesis before you act on it, and score competing explanations against the same evidence."
pack: desk-research
kind: how-to
order: 3
---

# Challenge the result

**Step 3 of 4 — Challenge the result**
<!-- rung: packs/desk-research/JOURNEY.md -->

**What changes:** Findings that survive an adversarial pass are separated from findings that were never tested.
<!-- rung: packs/desk-research/JOURNEY.md -->

**What you need first:** The survey from the previous step.
<!-- rung: authored -->

*Skipping costs:* A confident synthesis goes forward with its weakest findings indistinguishable from its strongest.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [Episodic vs project research](../explanation/episodic-vs-project-research.md) explains the two axes: how deep one session goes, and how long an investigation runs.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `devils-advocate` | The survey | The strongest objection to each finding, and a verdict on each. | Required |
| `compare-hypotheses` | A decision-shaped question and its evidence | Competing hypotheses scored against the same evidence. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. In every path below, `<topic-slug>` is the short kebab-case name you
give the investigation, and it stays the same across every artifact so one
study's files sort together.

<!-- rung: packs/desk-research/JOURNEY.md -->

## Run `devils-advocate` — the strongest objections

**You type:**
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

```
Argue against this survey. Find the strongest counter-evidence for each finding and tell me which ones should be downgraded.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

> **Agent:** Done — I've written the strongest objection to each finding, each routed to a verdict — a confidence downgrade, or an irreducible tension to `<topic-slug>-counterpoints.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

> **You:** You downgraded a finding because one source disagreed. Say whether that source is independent of the ones supporting it, or the downgrade is not earned.
>
> **Agent:** I checked and the dissenting source shares an employer with one supporting source, so I withdrew that downgrade and recorded why.

**Output varies** with how much counter-evidence exists and how contested the field is.
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Ask which verdicts are `do-not-resolve` and under what conditions each side holds; this surfaces a tension flattened into a false winner.
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

**Watch out for:** A review that downgrades everything is as useless as one that downgrades nothing. Notice verdicts with no counter-evidence cited — an objection without evidence is a doubt, and doubts do not change a rating.
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

**Where it lands:** `<topic-slug>-counterpoints.md`.
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

**What it looks like:**
<!-- rung: packs/desk-research/.apm/skills/devils-advocate/SKILL.md -->

```markdown
# Counterpoints — <target artifact or claim>

## Finding: <quoted from target>

- **Counter-position:** <strongest objection, one paragraph>.
- **Counter-evidence:** <citations>.
- **Verdict:** rating downgrade — `[high]` → `[moderate]`. Reason:
  contested-in-field.

## Finding: <next>

- **Counter-position:** <a credible, well-evidenced opposing position>.
- **Counter-evidence:** <citations — substantive, on both sides>.
- **Verdict:** do-not-resolve. Both hold under different conditions:
  <finding> holds when <conditions>; <counter-position> holds when
  <conditions>. More evidence would not collapse this to one answer.
```

*The agent replaces every `<…>`. This is the schema the skill writes to; the artifact continues in the same shape.*

## Run `compare-hypotheses` — the evidence matrix

**You type:**
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

```
Compare the competing explanations here as hypotheses, and score each against the evidence we have.
```

**Agent returns:**
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

> **Agent:** Done — I've written an evidence matrix scoring each hypothesis against the same evidence, for and against to `<topic-slug>-hypotheses.md`.

**You push back:**
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

> **You:** H2 has no contradicting evidence listed, which means you did not look for any. Search against it specifically, then rescore.
>
> **Agent:** I searched against H2, found two contradicting items, and its confidence dropped from high to moderate.

**Output varies** with how many credible explanations exist and how much evidence separates them.
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (testable):** Ask which single piece of evidence, if it were wrong, would change the ranking; this surfaces a matrix resting on one load-bearing item.
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

**Watch out for:** A hypothesis with only supporting evidence has not been tested, it has been illustrated. Notice any row whose contradicting column is empty and send the agent back to look.
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

**Where it lands:** `<topic-slug>-hypotheses.md`.
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

**What it looks like:**
<!-- rung: packs/desk-research/.apm/skills/compare-hypotheses/SKILL.md -->

```markdown
# Hypotheses — <decision question>

## Hypothesis H1: <name>

- **Claim:** <one sentence>.
- **Confidence:** `[moderate]`.
- **Strongest supporting:** <evidence item with citation>.
- **Strongest contradicting:** <evidence item with citation>.

## Hypothesis H2: <name>

(same shape)

## Matrix

|                 | H1  | H2  | H3  |
```

*The agent replaces every `<…>`. This is the schema the skill writes to; the artifact continues in the same shape.*

## Where this leads

**Done with this step:** You can move on when every downgrade cites independent counter-evidence and every irreducible tension is labelled as one.
<!-- rung: authored -->

Stage 3 of four. For a single-session question this is the last step.

**Next:** [Run it as a project](run-it-as-a-project.md).
<!-- rung: authored -->

**Go deeper:** [the `desk-research` pack reference](../reference/desk-research-pack.md) — every skill this step runs, with its inputs and outputs.
<!-- rung: authored -->
