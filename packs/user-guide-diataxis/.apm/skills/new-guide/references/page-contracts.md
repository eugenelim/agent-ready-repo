# Page contracts

Each section below is the contract for one surface type. Load only the section
that matches the page you are writing or revising. The contract answers three
questions for each type: what the first screen must make obvious, what content
is required, and what to move lower or link out.

## Choosing the right surface type

For the four Diátaxis types, choose by reader posture — what the reader is doing
right now, not what topic they are reading about. The same person, on different
days, will land in different quadrants.

| Reader's posture right now | Surface |
| --- | --- |
| On rails, attentive, wants a guaranteed working result | **Tutorial** |
| Has a named problem, wants the recipe | **How-to** |
| In a hurry, scanning for the authoritative answer | **Reference** |
| Away from the keyboard, wants to understand *why* | **Explanation** |

Pack pages and journey pages are chosen by context: if the page describes what a
pack does and how to start, it is a Pack page. If the page walks through a
complete user flow from first request to final outcome, it is a Journey page.

---

## Tutorial

**First screen must answer:** "How do I complete my first real journey?"

**Required content:**
- The exact first request to send — copyable, not paraphrased
- The expected result after that first request
- Checkpoints along the way ("you should see…")
- A complete outcome at the end — the reader finishes with something real
- Each step says what to do and what the reader should observe

**Move lower or link out:**
- Alternatives and variations (→ How-to)
- Architecture and design decisions (→ Explanation)
- Exhaustive option lists (→ Reference)
- Prerequisites beyond the minimum needed to start

**Anti-patterns to refuse:**
- Offering the reader a choice mid-tutorial
- Inserting explanation of *why* without linking out
- Steps that produce no observable result
- A result the reader cannot verify

---

## How-to

**First screen must answer:** "How do I accomplish this one goal?"

**Required content:**
- A copyable request or command that starts the task
- The scope of what the skill reads and what it may change
- A minimal procedure covering the common path
- Common variations the reader is likely to hit
- The most likely follow-up request after the task completes

**Move lower or link out:**
- Theory and background (→ Explanation)
- Exhaustive field-by-field reference (→ Reference)
- Step-by-step setup a beginner needs (→ Tutorial)
- Options the reader will never vary

**Anti-patterns to refuse:**
- A title that names a topic rather than the reader's problem
- Reteaching basics the competent reader already knows
- Covering only the linear happy path with no realistic variations

---

## Reference

**First screen must answer:** "What exactly does this skill accept and do?"

**Required content:**
- An intent index — what the reader can accomplish with this skill
- Inputs: what the reader provides
- Outputs: what the skill returns
- Reads: what the skill reads without asking
- Writes: what the skill may change
- Limits: caps, timeouts, pagination, rate limits

**Move lower or link out:**
- Narrative walkthroughs (→ How-to or Tutorial)
- Explanation of why the design works this way (→ Explanation)
- Getting-started instructions (→ Tutorial)

**Anti-patterns to refuse:**
- Editorializing ("this is the recommended option…")
- Entries of the same kind shaped differently from their siblings
- Skipping an option because it is "rarely used"

**Sync discipline:** Reference rots when the code drifts. A code change → reference update in the same PR is the rule, not a nice-to-have. For auto-generated sections, mark them with a comment pointing to the source data so readers know not to hand-edit the copy.

---

## Explanation

**First screen must answer:** "How do these pieces fit together and why?"

**Required content:**
- A mental model the reader can hold in their head
- How the components compose — what connects to what
- Trade-offs and the reasoning behind key design choices
- Boundaries — what this concept is and is not

**Move lower or link out:**
- Step-by-step procedures (→ How-to)
- Exhaustive parameter lists (→ Reference)
- Guaranteed-outcome walkthroughs (→ Tutorial)

**Anti-patterns to refuse:**
- Step-by-step instructions embedded in the explanation
- Open-ended scope with no "About <topic>" frame
- Refusing to take a position where the design is opinionated

---

## Pack page

**First screen must answer:** "What can this help me do?"

**Required content:**
- Job cards — what a reader with a concrete goal can accomplish
- Natural-language prompts — the exact words to use, not skill names
- Result previews — what the agent returns for each task
- The common journey — a start-to-finish sequence for the primary use case

**Move lower or link out:**
- The full skill inventory (names, flags, schema)
- Installation and setup details
- Architecture of how the pack is composed

**Anti-patterns to refuse:**
- Opening with a skill or command list
- Requiring the reader to know a skill name to begin the first task
- Describing capabilities in abstract terms without a concrete prompt

---

## Journey page

**First screen must answer:** "What happens from start to finish?"

**Required content (one block per stage):**
- **You say** — the natural-language request the reader sends
- **Agent does** — what the agent reads, fetches, or computes
- **You get** — the concrete result
- **Decision** — what the reader decides or confirms before the next stage

**Move lower or link out:**
- Skill cards and implementation vocabulary
- Configuration and permission details
- Error-handling reference

**Anti-patterns to refuse:**
- Describing what the skill does without showing what the reader says and gets
- Stages without a visible decision or outcome
- Mixing implementation vocabulary into the user-facing flow
