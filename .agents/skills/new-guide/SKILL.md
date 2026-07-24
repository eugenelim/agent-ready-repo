---
name: new-guide
description: "Create or substantially revise user guides, pack pages, and journey pages using Diátaxis plus conversation-first UX. Use when asked to write, simplify, restructure, audit, or modernize tutorials, how-to guides, reference pages, explanations, pack pages, or journey pages so readers can start from a natural-language goal, see what to say, understand what happens next, and reach an outcome without learning internal skill names first. Do NOT use for feature contracts (use `new-spec`), cross-cutting proposals (use `new-rfc`), recording decisions (use `new-adr`), minor single-line edits (normal PR), contributor docs, docstrings, release notes, or blog posts."
---

# Guide authoring

**Diátaxis determines where information lives. User intent determines how readers
enter it.**

A reader who does not know any pack or skill names must still be able to begin a
real task from the first screen.

Create or substantially revise one user-facing documentation surface. Use Diátaxis
to determine the page's job. Use conversation-first design to determine what the
reader encounters first.

## Prerequisites

- Read the actual skills, commands, or workflows the page documents.
- Identify one primary reader and one primary job.
- Preserve verified commands, permissions, defaults, and side effects.
- For generated pages, edit their source data or template — not the rendered output.

## Procedure

### Step 1 — Choose mode

**Create** a new guide, or **revise** an existing one.

Revise mode applies to substantial changes: restructuring the page's flow,
correcting the quadrant, major rewrites, adding conversation-first structure, or
auditing for inventory-first writing.

Minor edits — a typo fix, a single updated command, a broken link, a version
number — are a **normal PR against the existing file**. Stop here and redirect to
that path; do not proceed with this skill for minor edits.

### Step 2 — Pick the slug or confirm the file

- **Create:** choose a kebab-case slug matching what the reader would have searched
  for. `rotate-credential-token`, not `how-to-rotate-your-token-step-by-step`.
  The quadrant subdir carries the "how-to" / "tutorial" framing; do not repeat it
  in the filename.
- **Revise:** confirm the path to the existing file before proceeding.

### Step 3 — Write the conversation contract (gated)

Before any prose is drafted, produce the contract and wait for human confirmation.
This is the skill's gate — the body is blocked until the contract is signed off.

```
CONVERSATION CONTRACT:

reader: <role and context — not "all users"; who is reading right now>
job: <the specific thing they are trying to accomplish>
natural_start: <the exact words they would use to begin>
minimum_scope:
  - <the minimum the agent needs to start — team, board, time horizon, etc.>
first_result: <the concrete thing the reader gets back>
write_boundary: <what the agent reads vs. what it may change>
next_request: <the most likely follow-up after the first result lands>
```

Wait for human confirmation or revision. Two outcomes:

- Contract accepted → proceed to Step 4.
- Contract splits into two readers or two jobs → two pages. Surface this and ask
  the user to pick the first; the second goes to a follow-up.

### Step 4 — Choose the page contract type

Determine which of the six surface types applies. For the four Diátaxis types,
choose by reader posture — what the reader is doing right now, not what topic
they are reading about.

| Reader's posture right now | Surface type |
| --- | --- |
| On rails, attentive, wants a guaranteed working result | Tutorial |
| Has a named problem, wants the recipe | How-to |
| In a hurry, scanning for the authoritative answer | Reference |
| Away from the keyboard, wants to understand *why* | Explanation |

Pack pages describe what a pack does and how to start — choose by context.
Journey pages walk a complete user flow from first request to final outcome —
choose by context.

### Step 5 — Load the relevant contract from `references/page-contracts.md`

Read only the section that matches the surface type chosen in Step 4. Apply its
required content and "move lower" rules throughout drafting.

### Step 6 — Scaffold (create mode, four Diátaxis types only)

For create mode and the four Diátaxis quadrants, scaffold from the matching asset
template and write to the standard destination:

| Surface type | Asset to copy | Destination |
| --- | --- | --- |
| Tutorial | `assets/tutorials.md` | `docs/guides/tutorials/<slug>.md` |
| How-to | `assets/how-to.md` | `docs/guides/how-to/<slug>.md` |
| Reference | `assets/reference.md` | `docs/guides/reference/<slug>.md` |
| Explanation | `assets/explanation.md` | `docs/guides/explanation/<slug>.md` |

(Paths are skill-relative — the `assets/` folder lives next to this `SKILL.md`.)

For pack pages and journey pages in create mode, there is no fixed destination;
write where the repo's existing guides already live. Match the surrounding
structure.

If the repo organizes guides by pack — a `docs/guides/<pack>/<quadrant>/` layout
— prefix the destination with the owning pack, or `_shared/` for a cross-cutting
guide.

### Step 7 — Draft using conversation-first structure

Put the first useful example before inventories, architecture, terminology, or
exhaustive options. A reader who reaches word 120 without seeing a prompt,
command, or concrete result has waited too long.

Structure the core task flow using:

- **Say this** — the exact words the reader uses
- **What happens** — what the agent does in response
- **You get** — the concrete result
- **What to ask next** — the likely follow-up

### Step 8 — Apply conversation-first rules

Load [`references/conversation-first.md`](references/conversation-first.md) and
apply its eight sequencing rules. Key checks:

- Realistic user request within the first 120 words
- No more than two product-specific terms before that request
- User language before implementation names
- Read/write boundary explicit
- Next request shown

### Step 9 — Edit for density

Load [`references/clear-prose.md`](references/clear-prose.md) and edit. Pay
particular attention to the `## Conversation-first structure` section at the end
— it covers page-level structural tells that a word-level pass will miss.

When your environment provides subagents, hand the draft and the checklist to a
read-only subagent; that keeps the style read off your main context. The cold
self-read is the floor without subagents.

### Step 10 — Run the usability review

Load [`references/usability-review.md`](references/usability-review.md) and run
the six-item checklist. Each "yes" is a finding to fix before declaring the draft
ready. Also verify the conversation contract is reflected in the draft.

### Step 11 — Check links and cross-link siblings

Apply the link-out rule as you finalize:

- Tempted to explain *why* mid-tutorial → link to an explanation page
- Tempted to list every option mid-how-to → link to the reference
- Tempted to walk a beginner through setup mid-explanation → link to the tutorial
- Tempted to recommend a best practice mid-reference → link to the explanation

The link can be a placeholder (`<!-- TODO: link to … -->`) if the adjacent piece
does not exist yet; surface those placeholders in the final summary.

From the new or revised file, add a `See also` section linking existing siblings
only. From each existing sibling, add a reverse link. Check whether each file
exists before linking — do not write broken links and do not synthesize
plausible-sounding paths.

Do not touch the per-quadrant `README.md` files — those are the framework's
per-quadrant explainer, not a piece index.

## Verification

Before announcing the draft, confirm:

- [ ] The first actionable example appears within the first 120 words.
- [ ] The reader does not need to know a skill name to begin.
- [ ] Read and write behavior is explicit.
- [ ] The page shows at least one realistic follow-up.
- [ ] Skill inventory appears after user outcomes.
- [ ] A complete task has a visible start and finish.

## Anti-patterns to refuse

- **Drafting before the conversation contract is confirmed.** The body is gated.
  The contract is the cheapest place to catch a mismatched scope; once draft
  prose is on the page, rework compounds.
- **Using this skill for minor edits.** A typo fix, a single updated command, a
  broken link — these are normal PRs. This skill's procedure adds ceremony that
  minor edits do not warrant.
- **Picking the surface type by topic instead of by reader posture.** "Authentication"
  is a topic; *learning* it, *configuring* it, *looking up its parameters*, and
  *understanding why it is cookie-based* are four different pieces.
- **Blending surface types because "the reader will appreciate the context."** They
  will not. The link-out rule is non-negotiable.
- **Drafting a tutorial without running the steps end-to-end.** A tutorial that
  does not produce the promised result is worse than no tutorial. If the steps
  cannot be run, you are writing a how-to or an explanation — re-open the contract.
- **Writing reference in narrative voice.** Reference says *what*; recommendations
  live in explanation.
- **Writing explanation without an *About <X>* frame.** Open-ended explanation
  absorbs adjacent material and sprawls. Name the question the page answers.
- **Leading with a skill or pack inventory.** The reader came with a goal. The
  inventory belongs after the first task completes.
