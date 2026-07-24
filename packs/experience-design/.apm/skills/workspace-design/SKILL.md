---
name: workspace-design
description: "Use when designing a workspace surface — a productivity tool, a collaborative environment, an agentic UI, or any surface whose primary purpose is to support sustained professional work across sessions. Triggers on 'design the workspace', 'structure the tool UI', 'collaborative editing surface', 'agentic UI design', 'multi-agent coordination UI', 'task management surface', 'session arc design'. Covers context-persistence, collaboration state IA, ambient attention, agentic patterns, and interrupt design. Do NOT use for dashboards and monitoring views (use analytical-design) or marketplace surfaces (use marketplace-design). Surface genre: workspace. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: workspace-design

Converts the session arc, the collaboration model, and the agentic patterns into a **structural specification for a workspace surface** — the context-persistence architecture, the attention zone layout, the collaboration state IA, the interrupt and notification design, and the agentic patterns that make a workspace surface feel like a professional environment rather than a series of disconnected screens. This skill is IA and structure; it does not design individual component interactions (that is `interaction-design`) and does not derive tokens or color (that is `design-system` and `creative-direction`).

## When to invoke

Confirm all three before specifying:

1. **The surface supports sustained professional work** — the user returns to this surface repeatedly, across sessions, to do work that is too complex or too large to finish in a single visit. If the primary goal is information (use `informational-design`) or data comprehension (use `analytical-design`), those skills are more appropriate.
2. **The session arc is defined** — what does a complete work session look like? What is the user doing when they arrive, work, persist, and leave? Without a session arc, context-persistence decisions are guesses.
3. **The collaboration model is named** — is the surface single-user, asynchronously collaborative, or real-time collaborative? The answer drives presence, live-editing, and sharing IA decisions fundamentally.

## Context-persistence patterns

A workspace surface's most critical job is to remove the cognitive overhead of "where was I?" The three patterns below address different scales of context loss:

**Last-location persistence**
When a user returns to the workspace, they land where they left off — not on a dashboard or a landing page. The default state is the user's last working context. Name what "last location" means in this workspace (the last open document, the last active task, the last open channel).

**Returning-session re-orientation**
After a gap (overnight, a week, a return from vacation), the user needs to re-orient before they can work. The surface proactively provides a re-orientation summary:
- What changed since they were last here
- What they were working on when they left
- What requires attention now (mentions, unresolved items, blocked tasks)
This is not a notification feed; it is a structured re-entry point.

**Breadcrumb + recents + activity**
Three complementary navigation affordances:
- **Breadcrumb:** where am I in the hierarchy of this workspace? (Project → Sprint → Task)
- **Recents:** what have I worked on in the recent past? (The last N documents/items, ordered by recency)
- **Activity:** what happened in this workspace since I last looked? (Changes, comments, status updates from collaborators)

Name which of the three are present and where they are positioned. A workspace with none of the three requires the user to reconstruct their context from memory on every return.

## Session arc — 5 stages

Design for the full arc, not just the working stage:

| Stage | What the user needs | Design implications |
|-------|-------------------|---------------------|
| **Arrive** | Context re-establishment — where was I? | Last-location persistence or returning-session re-orientation, depending on recency of last visit |
| **Orient** | Understand what requires attention — what's new? | Activity feed, notification surface, re-orientation summary |
| **Work** | Uninterrupted focus on the primary task | Ambient attention zones, focal zones, interrupt suppression |
| **Persist** | Save and exit gracefully — my work is safe | Save-state indicators (autosave + confirmation), draft vs. published state, unsaved-changes guard |
| **Collaborate** | Share, hand off, or review with another person | Presence indicators, sharing model IA, commenting surface |

Design decisions made for the Work stage often break the Arrive and Persist stages. Walk all five stages explicitly.

## Collaboration state IA

**Presence** (who else is here right now)
Presence indicators are ambient — they answer "is anyone else working in this space right now?" without demanding attention. Design presence as ambient metadata, not as a notification.
- Named presence (avatar + name, visible in the document or workspace header) vs. anonymous presence (count without identity) — the choice depends on the workspace's collaboration model
- Presence staleness: how long does a presence indicator remain visible after a user stops interacting? Define the timeout and the indicator behavior at timeout.

**Live editing** (who is changing what right now)
When multiple users can edit simultaneously, the live-editing state answers "what is being changed right now, and by whom?" Design:
- Cursor/selection visibility: whose cursor is where, in what color, with whose name
- Conflict prevention: can two users edit the same cell/sentence simultaneously, or does the surface serialize? Name the model explicitly.
- Edit attribution: after a live session, is there a history that attributes each change? The IA decision here drives trust in collaborative work products.

**Following mode** (I want to see what you're seeing)
When a user wants to follow another user's screen in real-time (for training, debugging, pair-working), the following mode:
- Makes it unambiguous whose perspective is being shown (not the follower's own navigation)
- Provides a clear entry/exit affordance — the user should not accidentally enter or exit following mode
- Preserves the follower's navigation history for when they exit (they return to where they were, not to the followee's location)

## Interrupt and notification design

**Ambient by default**
Interrupts in a workspace surface compete with concentrated work. The default posture for all notification types is **ambient** — visible at the periphery without demanding attention. Interrupts escalate from ambient to focal only when the information is time-sensitive and action-required.

**Interrupt escalation ladder**
| Level | Modality | When to use |
|-------|----------|------------|
| Ambient badge | Count indicator, no sound, no motion | New messages, background activity |
| Gentle nudge | Brief animation or color change, no sound | Nearing a deadline, a collaborator is waiting |
| Focal interrupt | Modal or full-attention overlay, may use sound | Destructive action pending, session expiry, error requiring immediate resolution |

Do not allow low-priority notifications to use focal interrupt modality. Every focal interrupt that turns out to be non-urgent erodes the modality's credibility.

**Permission and sharing model IA**
The permission model governs what a user can see and do. Its IA decisions:
- Where does a user discover what they can access? (The absence of access should be as visible as access — "you need permission to view this" is better than a 404)
- Where does a user request access? The path from "I can't see this" to "I've requested access" must be visible from the point of denial.
- How does an owner share? Sharing should be reachable from the object being shared, not from a settings page.

## Agentic UI patterns

When the workspace surface includes autonomous agents running tasks on the user's behalf, the IA must make agent activity legible without demanding constant attention:

**Task queue visibility**
The user needs to know what the agent is working on, in what order, and what requires their input. A task queue is the agent's working memory made visible:
- Pending tasks (not yet started)
- Active task (currently running, with a progress indicator that is meaningful, not decorative)
- Completed tasks (with outcome visible — success, failure, or partial result)
- Blocked tasks (waiting for human input — these are the items that require the user's attention)

**Agent status indicators**
Agent status is ambient unless it requires action. Design:
- Running: a subtle progress signal (not a spinner that demands attention)
- Waiting for input: a focal signal (the agent is blocked and cannot proceed without the user)
- Error: a focal signal with a recoverable action ("resume from here" or "show what failed")
- Complete: a brief ambient confirmation; no persistent indicator unless the output requires review

**Human-in-the-loop (HITL) confirmation surfaces**
When an agent must pause for human approval before taking a consequential action, the confirmation surface must:
- Name the action clearly ("I am about to delete 47 files matching this pattern")
- Make the consequence visible before the confirmation (not after)
- Offer a "show me what this affects" option before confirming
- Name the recovery path if the user approves and the action produces an unexpected outcome

**Output review surfaces**
When an agent produces an output that the user must review before it is used (a generated document, a proposed code change, a drafted email), the review surface:
- Shows the output in context, not in isolation (where will this be used?)
- Shows a diff when the output modifies existing content (what changed vs. the baseline?)
- Provides an accept/reject/edit affordance at the review stage, not after the output is already in place

**Multi-agent coordination visibility**
When multiple agents are running in parallel or in a chain, the coordination IA makes the dependency structure visible:
- Which agents are running?
- Which agent is waiting for which other agent?
- Where is the current bottleneck?
- Where can the user intervene?
A multi-agent workspace that hides its coordination graph from the user produces a surface that feels unpredictable; legibility of the graph is what makes it feel controllable.

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on a workspace surface, study how these products handle session continuity and agentic legibility: Linear (task-state clarity + keyboard-first productivity), Notion (context-persistence + collaborative editing state), Cursor (agentic UI patterns + HITL confirmation). Internalize the structural philosophy — attention zone design, agentic legibility, session arc continuity — not the surface treatment.

## Anti-patterns to refuse

- **Landing on a dashboard instead of the last location.** A workspace that greets a returning user with a generic dashboard instead of their last working context adds cognitive overhead on every return. Design for last-location persistence as the default; offer a dashboard as an explicit opt-in.
- **Focal interrupts for ambient information.** Notification modality inflation — using sound, motion, or modal overlays for non-urgent information — trains users to dismiss focal interrupts without reading them. Reserve focal interrupts for actions that cannot wait.
- **Agentic output that cannot be reviewed before it is applied.** An agent that writes files, sends messages, or modifies data without a review step between output and application is an agent without an undo. Design a review surface for every consequential agentic output.
- **Sharing model accessible only from settings.** A user who wants to share an object should not need to navigate to a settings page. Sharing is reachable from the object; settings is for workspace-wide permissions.
- **Missing persistence confirmation.** A workspace surface with no save-state indicator leaves the user uncertain about whether their work is safe when they leave. Autosave is not the same as autosave confirmation — the user needs to SEE that their work was saved.
