# Page contracts

Each section below is the contract for one artifact type. Load only the section that matches the artifact you are writing or revising. The contract answers three questions: what the first screen must make obvious, what content is required, and what to move lower or link out.

Diátaxis is an authoring contract, not a directory structure. A how-to guide that lives in `guides/core/how-to/` follows the how-to contract. So does one that lives in a flat `guides/how-to/`. The file's location does not change what it promises the reader.

## Choosing the right kind

Choose by reader posture — what the reader is doing right now, not what topic they are reading about. The same person, on different days, will land in different kinds.

| Reader's posture right now | Kind |
| --- | --- |
| On rails, attentive, wants a guaranteed working result | **Tutorial** |
| Has a named problem, wants the recipe | **How-to** |
| In a hurry, scanning for the authoritative answer | **Reference** |
| Away from the keyboard, wants to understand *why* | **Explanation** |

Pack READMEs and journeys are chosen by context. See their contracts below.

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
- The scope of what is read and what may change
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
- An intent index — what the reader can accomplish
- Inputs: what the reader provides
- Outputs: what the skill returns
- Reads: what is accessed without asking
- Writes: what may change
- Limits: caps, timeouts, pagination, rate limits

**Move lower or link out:**
- Narrative walkthroughs (→ How-to or Tutorial)
- Explanation of why the design works this way (→ Explanation)
- Getting-started instructions (→ Tutorial)

**Anti-patterns to refuse:**
- Editorializing ("this is the recommended option…")
- Entries of the same kind shaped differently from their siblings
- Skipping an option because it is "rarely used"

**Sync discipline:** Reference rots when behavior drifts. A behavior change → reference update in the same PR is the rule. For auto-generated sections, mark them with a comment pointing to the source data so readers know not to hand-edit the copy.

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

## Pack README

**First screen must answer:** "What can this help me do?"

**Required content:**
- What the pack helps users accomplish — in the user's language, not skill names
- Natural-language starter requests — the exact words to use
- What the user gets back — concrete result preview
- Install command
- Links to deeper guides

**Move lower or link out:**
- The full skill inventory (names, flags, schema) (→ Reference guide)
- Configuration and setup details (→ How-to guide)
- Architecture of how the pack is composed (→ DESIGN.md)

**Anti-patterns to refuse:**
- Opening with a skill or command list
- Requiring the reader to know a skill name to begin
- Describing capabilities in abstract terms without a concrete prompt
- Duplicating machine facts already in `pack.toml`

---

## Journey

**First screen must answer:** "What happens from start to finish?"

**Required content (one block per stage):**
- **You say** — the natural-language request the reader sends
- **Agent does** — what the agent reads, fetches, or computes
- **You get** — the concrete result
- **Decision** — what the reader decides or confirms before the next stage

**Move lower or link out:**
- Skill cards and implementation vocabulary (→ Reference guide)
- Configuration and permission details (→ How-to guide)
- Error-handling reference (→ Reference guide)

**Anti-patterns to refuse:**
- Describing what the skill does without showing what the reader says and gets
- Stages without a visible decision or outcome
- Mixing implementation vocabulary into the user-facing flow
