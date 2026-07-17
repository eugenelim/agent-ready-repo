# Per-Pack Journey Page Template

Defines the content schema and section structure for `/journeys/[pack]/` pages.  
These pages are the platform site's primary differentiator — they show what it's like to *use* a pack, not just what it contains.  
Reference: `.context/site-information-architecture.md`, `site/aesthetic-direction.md`

---

## What a journey page is (and is not)

**Is:** A narrative walkthrough of a real usage session. Shows the human's role at every stage — what triggers them, what they review, what a good outcome looks like, what a bad one looks like.

**Is not:** A skills reference (that's `/docs/`). Not a pack catalogue card (that's `/packs/`). Not marketing copy.

**Reader:** An IC (individual contributor) who has decided to try the pack and wants to know what to expect before they start.

---

## Frontmatter schema

```yaml
---
# Required
pack: core                        # slug — matches /packs/[pack] and /docs/packs/[pack]
scope: repo                       # "user" | "repo"
tagline: "Spec → shipped code. Supervised."
prerequisitePacks: []             # slugs of packs that must be installed first

# Skills listed in usage order (not alphabetical)
skills:
  - name: work-loop
    description: "The build loop. Plans, executes, verifies, and reviews."
    humanTouches: 2               # number of human gates in a typical session
  - name: new-spec
    description: "Authors a spec document before the build loop starts."
    humanTouches: 1

# Human gates — in sequence order
humanGates:
  - id: G-plan                    # internal ID, not necessarily the global gate label
    globalGate: null              # "G3" | "G4" | "G5" | null (loop-internal gates)
    label: "Approve the plan"
    trigger: "Before work-loop begins execution"
    duration: "5–10 minutes"      # realistic time estimate
    whatToCheck:
      - "Is the Trio complete? (problem, user, success criteria)"
      - "Do the stated risk triggers match the actual change?"
      - "Is the plan scoped to what was asked — nothing more?"
      - "Are the assumption surfacings plausible?"
    whatGoodLooksLike: "A bounded plan with a clear trio, no scope creep, correct risk triggers."
    whatBadLooksLike: "A plan that extends the scope of the request, or a risk trigger that should have fired and didn't."
    consequence: "If you approve a bad plan, the agent executes it faithfully. The cost of a bad plan is the cost of a full loop iteration."
  - id: G-pr
    globalGate: G4
    label: "Merge the PR"
    trigger: "After all mechanical gates pass and adversarial review is clean"
    duration: "10–20 minutes"
    whatToCheck:
      - "Is adversarial review marked clean? (Re-run if in doubt.)"
      - "Does the implementation match the spec? If not, did the spec update?"
      - "Are the tests testing behavior, not implementation details?"
      - "Is there anything in the diff that wasn't in the plan?"
    whatGoodLooksLike: "Green gates, clean adversarial review, spec and implementation aligned."
    whatBadLooksLike: "Adversarial reviewer flagged something and you merged anyway. Or the spec drifted from the implementation without an update."
    consequence: "G4 is the last line of defense before the build loop output goes to release."

# Typical session shape
typicalSession:
  agentTurns: 8–12               # rough range for a well-scoped task
  humanTouches: 2                # plan approval + PR merge
  wallClockMinutes: 25–45        # for a medium-sized task

# Related content
docsUrl: /docs/guides/core/      # deep link into MkDocs
packUrl: /packs/core/            # pack catalogue card
relatedJourneys:
  - release                      # natural next journey after core
---
```

---

## Section structure

Every journey page uses this section sequence. Content varies; structure does not.

---

### Section 1 — Pack hero
**Component:** `JourneyHero.astro`  
**Surface:** Light zone (`--ds-surface-alt`) — override: owner decision (2026-07-16) — journey pages are fully light zone for consistency with the homepage Human Gates section; amber accents provide visual weight without a dark band

Elements:
- Pack name (display scale, amber)
- Scope badge (chip: `repo` or `user`, monospace)
- Tagline (subhead, hero-fg-2)
- Stat strip (3 items): number of skills · human touches per session · typical session time
- Two CTAs: `Install this pack →` | `Read the reference →`

---

### Section 2 — What changes when you install this
**Component:** inline section  
**Surface:** Light zone

**Job:** Before the journey narrative, give the reader a concrete sense of what they will now be able to do that they couldn't before. One paragraph, specific.

Example for `core`:
> After installing core, every coding task in your repo runs through the `work-loop`: plan → execute → verify → adversarial review. You get lint, typecheck, and tests as mechanical gates. Three specialist reviewers read every diff cold. The loop cannot self-certify — it always surfaces to you for plan approval and PR merge.

---

### Section 3 — Skills in this pack
**Component:** skills list  
**Surface:** Light zone (`--ds-surface-alt`)

**Layout:** One row per skill. Each row:
- Skill name (monospace chip, amber)
- Description (one sentence — what it does, not what it is)
- Human touches indicator (e.g., "2 gates" — visual indicator, amber)

---

### Section 4 — The journey (staged narrative)
**Component:** Markdown body (`<Content />` rendered from the journey `.md` file)  
**Surface:** Light zone

**Job:** Walk through a real session in past tense, second person. Each stage is a named step describing what happened — what the agent did and what the human did. This is the primary content — the rest is scaffolding for it.

**Authoring convention (per journey `.md` body):**

- Use past tense, second person: "You opened a task. The agent activated `work-loop`."
- Name the skill, not just the loop: "The agent ran `adversarial-reviewer` in a fresh session."
- Name the failure mode at every gate — what does a bad plan look like? What does a bad PR look like?
- Each stage has a `**You did:**` paragraph describing the human's active role — watching at key moments, redirecting, reading output, making decisions. Do not write "You did: Nothing."

**Example stage sequence for `core` / `work-loop`:**

```markdown
## Stage 1 — Brief the loop
You described the task. The agent activated `work-loop`, checked for risk triggers,
wrote the inline spec (trio: problem, user, success criteria), and surfaced assumptions.

**You did:** Read the trio. Confirmed scope. Approved the plan. 5–10 minutes.

## Stage 2 — Execution
The agent implemented against the spec, running lint, typecheck, and tests after
each logical change. When a gate failed, it fixed and re-ran before continuing.

**You did:** Watched at key moments — skimmed output after each logical task.
Answered quickly if the agent surfaced a question. Let it run when all was well.
```

---

### Section 5 — Human gates (detailed)
**Component:** `GateDetail.astro`  
**Surface:** Light zone (`--ds-surface-alt`) — override: owner decision (2026-07-16) — amber left-border cards on light background provide the visual weight; no dark band needed

**Job:** For each gate, give the human everything they need to make a confident decision. This is the section that makes the page distinctive — no other resource explains what the human actually does at each gate.

Each gate block:

```
G-plan — Approve the plan          ← amber gate ID, display on amber chip
Triggered: Before execution begins
Time: 5–10 minutes

WHAT TO CHECK
□ Is the Trio complete?
□ Do the stated risk triggers match the actual change?
□ Is the plan scoped to what was asked — nothing more?
□ Are the assumption surfacings plausible?

WHAT GOOD LOOKS LIKE
A bounded plan with a clear trio, no scope creep, correct risk triggers.

WHAT BAD LOOKS LIKE
A plan that extends the scope of the request, or a risk trigger that 
should have fired and didn't.

CONSEQUENCE OF SKIPPING
If you approve a bad plan, the agent executes it faithfully. 
The cost of a bad plan is the cost of a full loop iteration.
```

---

### Section 6 — What good output looks like
**Component:** inline / screenshot  
**Surface:** Light zone

**Job:** Concrete example of what a successful session produces. A screenshot of an actual PR description, or an actual spec, or an actual adversarial review output — not a fabricated example.

For `core`: Screenshot of a clean PR description showing the trio, what was deferred, and the specialist reviewer results.

*(Content to be authored. Placeholder: a structured text example until screenshots are available.)*

---

### Section 7 — Typical session shape
**Component:** Inline `.session-stats` grid (bespoke, not a shared component)  
**Surface:** Light zone

Three stats from the `typicalSession` frontmatter field:
- Agent turns (range)
- Human touches
- Wall-clock time

---

### Section 8 — Install and next steps
**Component:** Inline `.install-block` (bespoke, not a shared component)  
**Surface:** Light zone (`--ds-surface-alt`)

Install command from frontmatter.

Then: "What to do next" — two or three links:
- `Read the core reference →` (into `/docs/`)
- `Explore the release loop →` (next journey)
- `Browse the pack catalogue →`

---

## Content authoring priority

Content for journey pages does not exist yet and must be authored before the pages can be built. Priority order:

| Journey | Priority | Rationale |
|---|---|---|
| `core` | 1 | Every adopter installs this; it's the entry point |
| `discovery` | 1 | The discovery loop is the product's conceptual differentiator |
| `release` | 1 | Completes the full SDLC story |
| `research` | 2 | High independent utility |
| `architect` | 2 | Common in engineering-lead audiences |
| `experience` | 2 | Differentiates for product-engineering teams |
| All others | 3 | Content deferred until P1/P2 journeys are live |

---

## Writing guide for journey content

When authoring the Stage 4 narrative (the journey):

- **Write in past tense, second person:** "You opened a task. The agent activated `work-loop`." Not "The agent will activate..."
- **Name the skill, not just the loop:** "The loop runs `adversarial-reviewer` in a fresh session" — not "the loop reviews the diff."
- **Be specific about time:** "5–10 minutes to read the plan" is more useful than "a few minutes."
- **Name the failure mode at every gate:** What does a bad plan look like? What does a bad PR look like? The reader needs to recognize a bad outcome, not just a good one.
- **Do not soften the agent's limitations:** If the agent will occasionally propose a plan that's too broad, say so. Earned authority (goal #1) requires honesty about the limits.
