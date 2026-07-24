# Page archetypes: when to use which

**Use this when:** you have a surface to design and need to identify which page archetype applies before designing hierarchy — or when a surface feels wrong and you need a framework to diagnose it.
**Prerequisites:** `experience-design` pack installed.
**Result:** a matched archetype with its first-screen contract, attention contract, and read/write permission contract applied to your surface.

> **How-to** — task-oriented. Pick the right archetype for your surface and
> apply its structural contracts. For *why* the archetypes are shaped this
> way, read [The experience thread](../explanation/the-experience-thread.md).
> For the full archetype reference with all fields, see
> `information-architecture/references/page-archetypes.md`.

Archetype selection is the first step of `information-architecture`. Run it
before designing hierarchy — the archetype determines the first-screen
contract, the navigation behavior, and the permission and attention contracts
that shape every control on the surface.

## Decision procedure

Work through these questions in order. Stop at the first question that
produces a clear answer.

**1. What is the user's primary relationship to the main object on this surface?**

- They are deciding whether to acquire or sign up → **Marketing landing** (1)
- They are setting up for the first time → **Onboarding** (2)
- They are resuming work on something they created → **Product workspace** (3)
- They are monitoring state across multiple objects → **Dashboard / admin** (4)

**2. Is the user completing a bounded, multi-step action?**
→ **Transactional flow** (5)

**3. Is the user browsing a catalogue of items to find and select one?**
→ **Pack / catalogue** (6)

**4. Is the user mapping or documenting a sequence of stages or events?**
→ **Journey** (7)

**5. What kind of documentation is this?**
- The user is following prescribed steps to acquire a new skill → **Tutorial** (8)
- The user knows the tool and wants the exact procedure for a task → **Task how-to** (9)
- The user is looking up a specific fact, parameter, or API surface → **Reference index** (10)
- The user wants to understand a concept, not complete a task → **Explanation** (11)

**6. Does this surface span multiple distinct surfaces (marketing site, docs, product app)?**
→ **Multi-surface** (12) — apply cross-surface wayfinding to all constituent surfaces.

**If the surface matches two archetypes:** name both, state which structural
decisions each implies, and pick the one whose first-screen contract is correct
for the primary user job. A surface that genuinely needs two archetypes is
trying to serve two incompatible jobs — split it.

---

## 12-archetype quick-reference

| # | Archetype | Primary user | Primary job | First-screen contract |
|---|-----------|-------------|-------------|----------------------|
| 1 | Marketing landing | Visitor / prospect | Decide in under 30s whether to acquire | Outcome in the heading, one primary CTA above fold |
| 2 | Onboarding | New account holder | Reach first-success event with minimum friction | Greet by role/intent; simplest possible first step visible |
| 3 | Product workspace | Active user | Pick up where they left off | User's own work in its most recent state |
| 4 | Dashboard / admin | Role-based user | Detect anomalies, act on exceptions | Most actionable signal top-left; KPIs time-stamped |
| 5 | Transactional flow | Any authenticated user | Complete a bounded action with confidence | Action + what it affects named in heading; progress indicator |
| 6 | Pack / catalogue | Explorer / buyer | Find and select the right item | Browse grid open; search/filter present but not foregrounded |
| 7 | Journey | Planner / team lead | Capture stages and expose failure modes | Canvas at correct phase range; current phase in view |
| 8 | Tutorial | Learner | Acquire a skill by doing | Goal named in heading; prerequisites listed; step 1 visible |
| 9 | Task how-to | Practitioner | Complete a specific task | Task-named heading; "use when" scoped; step 1 above fold |
| 10 | Reference index | Practitioner / developer | Find a precise fact and extract it | Search or alphabetical nav is the primary entry |
| 11 | Explanation | Reader | Build a mental model | Concept named; opening paragraph names who and what they'll understand |
| 12 | Multi-surface | Any user | Move between surfaces without losing context | Each surface identifies itself and its relationship to others |

---

## Applying the attention contract

Once you have the archetype, name the attention contract for your surface:

| Contract level | When to use | Pattern |
|---|---|---|
| **No-action** | User is reading or monitoring; no response required | No persistent CTA above fold |
| **Optional-progress** | Action available but not urgent; user can defer | Action visible but secondary; inline link or secondary button |
| **Decision-required** | User must choose before continuing; not irreversible | Two clear options with context; default pre-selected if one exists |
| **Blocked-pending** | User cannot proceed; something external is resolving | Progress + explanation + "notify me" or "go back" path |

Match the contract to your archetype:
- Marketing landing, dashboard, reference index, explanation → **No-action** (browsing)
- Onboarding suggestions, recommended next steps → **Optional-progress**
- Plan selection, review steps, confirmation dialogs → **Decision-required**
- Payment processing, approval waiting, async jobs → **Blocked-pending**

---

## Applying the read/write permission contract

For every control on the surface, name the permission level before designing it:

| Level | What it means | Key pattern |
|---|---|---|
| **Read-only** | User sees but cannot change | No edit controls; visible non-alarming indicator of why |
| **Draft** | User edits a private copy | "Draft" label; autosave; publish is distinct from save |
| **Proposed-write** | Change staged but not yet applied | Summary of what will change; confirm and cancel controls |
| **Confirmed-write** | Applied immediately on save | Explicit save action; proportionate success confirmation |
| **Destructive** | Permanently removes or irrevocably changes | At least one click from primary button; confirmation names what is lost |
| **Undo-recovery** | Applied but reversible within a window | Toast with undo control and window duration immediately after action |

**Common mismatches to catch:**

- A dashboard card with an edit button on a `read-only` surface → remove the control or add a visible permission indicator.
- A transactional flow that auto-saves on form advance without a review step → add `proposed-write` staging.
- A destructive action as the default/primary button → move to secondary with a confirmation dialog.

---

## Applying the card-use test

Before using cards for any object set, confirm all three criteria hold:

1. The objects are **comparable** (user needs to scan and compare multiple instances).
2. Each object has a **thumbnail or scannable primary attribute**.
3. The set is **browsable** (typically fewer than 50 items; browsing, not searching, is the primary mode).

If any criterion fails, use a list, table, or another non-card pattern instead.
The full criteria and alternatives table are in
`information-architecture/references/page-archetypes.md` § Card-use test.

---

## Worked example: a settings page

> "Structure the settings page for our product."

**Step 1 — Apply the decision procedure:**
- The user is not acquiring, onboarding, monitoring, or completing a bounded multi-step action.
- They are making configuration changes to an existing product → closest archetype: **Product workspace** (3) — if the settings are a panel within the workspace, or **Transactional flow** (5) if the settings involve a staged confirm/cancel pattern.

**Step 2 — Name the object and role:**
- Object: product configuration settings.
- Role: **Changes** (modifying an existing object).
- Visual weight rule: primary action (Save changes) has maximum visual weight.

**Step 3 — Apply the attention contract:**
- Settings are available but not urgent → **Optional-progress** (user can defer without consequence).
- Exception: a setting that requires a decision before continuing (e.g., a billing plan change) → **Decision-required** for that section.

**Step 4 — Apply the permission contract:**
- Read the current setting: **Read-only**.
- Edit a setting: **Draft** (staged, not yet applied) or **Proposed-write** (summary shown before save).
- Save the setting: **Confirmed-write**.
- Delete an account or data: **Destructive** — confirmation required, naming what is lost.

**Result:** A settings page with grouped sections (navigation by category),
edit controls visible but secondary (not the first thing seen), a save
action with maximum visual weight within each section, and a destructive
zone clearly separated at the bottom of the page.
