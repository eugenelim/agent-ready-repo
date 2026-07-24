# Page archetypes

Twelve surface archetypes and four shared contracts that govern any of them.
Use this reference whenever `information-architecture` is invoked: identify
the archetype first (the archetype determines the first-screen contract and
navigation behavior), then apply the product-object mapping, attention
contract, and read/write permission contract appropriate to what the user
can do on that surface.

---

## 1. Marketing landing

**Primary user:** Visitor or prospective adopter — no account, unknown needs.

**Job:** Decide in under 30 seconds whether this product is worth the next
action (sign up, contact, explore docs).

**First-screen contract:** Above-fold names the outcome the user achieves
(*not* the feature list) and shows one primary call to action. Scroll story
extends the proof from outcome to mechanism to social validation.

**Primary action:** Click the primary CTA — sign up, start trial, contact.

**Expected result:** CTA click routes to the first step of the acquisition
flow without interruption.

**Next action:** Onboarding surface (see archetype 2).

**Proof:** Five-second test — a stranger can name who this is for and what
they achieve, without reading body copy.

**Read/write consequence:** Visitor reads only; no account state changes
until the CTA is completed. Treat the click itself as the transition to
`proposed-write` (email capture or account creation).

**Critical states:** No-JavaScript fallback (page is still legible); mobile
above-fold (single column, CTA visible without scroll); slow-network (above-fold
renders without blocking on deferred scripts).

**Navigation behavior:** Primary navigation is minimal — brand mark + one
CTA. Resist adding secondary nav links that provide escape routes before
the CTA is reached. Footer carries full navigation for returning visitors.

---

## 2. Onboarding

**Primary user:** New account holder — authenticated, zero existing work.

**Job:** Reach the first moment of real value (the "first-success event")
with minimum friction.

**First-screen contract:** Greet by role or intent, not by generic welcome
copy. Show a progress indicator only if the setup requires multiple steps.
First action is the simplest possible step toward the first-success event —
not a settings page, not a tour.

**Primary action:** Complete the first setup step (connect a tool, name a
project, import data, etc.).

**Expected result:** User arrives at a populated, working state — not a
blank workspace.

**Next action:** Product workspace surface (archetype 3) with the first
real work artifact visible.

**Proof:** First-success event is reachable within the session without help
documentation.

**Read/write consequence:** Each step is a `confirmed-write` — the user
explicitly advances. No step should auto-write to a visible production
artifact without confirmation.

**Critical states:** Already-completed state (user returns mid-onboarding —
resume, don't restart); skip-for-now path (user wants to explore before
committing to setup); error recovery (a step failed — show why and the
re-try path, not a dead end).

**Navigation behavior:** Suppress primary navigation during onboarding steps
to prevent distracting exits. Provide a clear "skip" or "do this later"
escape that does not erase progress.

---

## 3. Product workspace

**Primary user:** Active user — authenticated, has existing work.

**Job:** Pick up where they left off and advance their primary task.

**First-screen contract:** Show the user's own work in the most recent or
most relevant state. Do not land on an empty surface if the user has
existing artifacts. The "last worked" item or the primary in-progress item
is the correct default.

**Primary action:** Open, continue, or create a primary artifact.

**Expected result:** The artifact opens at the correct state (populated with
the user's data, not a blank template).

**Next action:** Task completion or a downstream surface (review, export,
share).

**Proof:** A user returning after 72 hours can orient to their work state
within 10 seconds without help.

**Read/write consequence:** Opening an artifact is `read-only` until an
edit action is taken. An explicit edit action transitions to `draft`.
Saving is `confirmed-write`.

**Critical states:** Empty workspace (first use after onboarding — invite to
create, not a blank surface); loading state (artifact list fetching —
preserve layout, show skeleton); permission boundary (a shared artifact the
user can view but not edit — show `read-only` state with a visible indicator).

**Navigation behavior:** Persistent primary navigation (all top-level
destinations reachable). Secondary navigation within the workspace is
contextual to the current artifact type. Breadcrumb or session label
keeps the user oriented to their position.

---

## 4. Dashboard / admin

**Primary user:** Role-based user — manager, analyst, or administrator
monitoring system or team state.

**Job:** Detect anomalies, act on exceptions, and confirm normal operation —
without opening individual records.

**First-screen contract:** The most actionable or highest-priority signal is
at the top left. Status indicators are scannable, not decorative. KPIs are
current and time-stamped.

**Primary action:** Drill into an anomaly or act on an exception.

**Expected result:** The exception view provides context sufficient to act
without opening a separate help document.

**Next action:** Resolve the exception in a transactional flow (archetype 5)
or navigate to a detail record.

**Proof:** A manager can identify the highest-priority issue without
scrolling, within the first glance.

**Read/write consequence:** Dashboard surfaces are `read-only` by default.
Administrative controls (archiving, bulk status changes) are `destructive`
or `confirmed-write` — always require explicit confirmation.

**Critical states:** Stale data (last-refreshed timestamp visible;
auto-refresh status shown); empty dashboard (no data yet — contextual
guidance, not a blank chart); all-green state (normal operation confirmed —
explicitly, not by absence of red); role-scoped view (the user sees only
what their role permits — permission boundary is visible but not alarming).

**Navigation behavior:** Top-level navigation persists. Widgets link to
detail records or filtered views. Drill-down preserves context (back
navigates to the dashboard view, not the top level).

---

## 5. Transactional flow

**Primary user:** Any authenticated user completing a multi-step, reversible
or irreversible action (checkout, form submission, configuration wizard).

**Job:** Complete a specific action with confidence — knowing what they
committed to, what will change, and how to recover if wrong.

**First-screen contract:** Name the action and what it affects in the heading.
Show a progress indicator for multi-step flows. First input or decision is
visible without scrolling.

**Primary action:** Advance to the next step or submit.

**Expected result:** Clear confirmation that the action completed or that
input was accepted and the next step is ready.

**Next action:** Confirmation surface or return to workspace.

**Proof:** User can state what they committed to without re-reading the form.

**Read/write consequence:** Each step transition is `proposed-write` (shown
in a review state) or `confirmed-write` (immediately applied). Irreversible
steps are `destructive` — require explicit confirmation with consequence
stated in plain language. Undo-recovery paths are named for reversible steps.

**Critical states:** Validation error (inline, adjacent to the failing field,
not at the top of the form); partial save (progress preserved when navigating
away mid-flow); confirmation (summary of what was committed, visible after
submit); undo window (if an undo-recovery path exists, the window and its
expiry are shown immediately after confirmation).

**Navigation behavior:** Suppress navigation during active steps to prevent
accidental abandonment. Provide explicit "back" and "cancel" controls with
stated consequences (back goes to the previous step without losing input;
cancel returns to the origin with an unsaved-changes warning if applicable).

---

## 6. Pack / catalogue

**Primary user:** Explorer or buyer — browsing to discover and select an item.

**Job:** Find the right item from a set, evaluate it, and commit to or
install it.

**First-screen contract:** The browse surface opens in a scanned, not
searched, state — category groupings visible, top items surfaced by
relevance. Search and filter controls are present but not foregrounded over
the browse grid.

**Primary action:** Select an item to view its detail.

**Expected result:** Detail view shows enough information to make the
commit/install decision without a second search.

**Next action:** Install, purchase, or add to a project — a transactional
flow (archetype 5).

**Proof:** A first-time explorer can find a relevant item within two minutes
without using search.

**Read/write consequence:** Browse is `read-only`. Selecting an item is
`read-only`. Installing or purchasing transitions to `confirmed-write`
(install) or a transactional flow for purchase.

**Critical states:** Empty results (filter produced zero matches — show how
to recover: relax the filter, clear all, browse instead); loading (card grid
skeleton preserves layout); item unavailable (item exists but is
unpurchasable — explain why and offer an alternative, not a dead end);
installed-already state (item is installed — show manage/upgrade path, not
the install CTA).

**Navigation behavior:** Facet/filter controls are persistent within the
browse view. Selecting a card navigates to detail; back returns to the browse
position (preserving scroll and filter state). Breadcrumb anchors the user:
catalogue > category > item.

---

## 7. Journey

**Primary user:** Planner or team lead — mapping a multi-phase user or
service experience.

**Job:** Capture the sequence of stages, actions, and feelings across a
journey to expose failure modes and opportunities.

**First-screen contract:** Journey map canvas opens at the correct phase
range — not an empty canvas, not a zoomed-out unreadable overview. The
current working phase is in view.

**Primary action:** Add or edit a stage, action, touchpoint, or finding.

**Expected result:** The edit is immediately visible in the map and persists
across sessions.

**Next action:** Derive screen flows (user-flow) or service blueprint.

**Proof:** A second team member can read the journey map cold and name the
primary user pain without asking the author.

**Read/write consequence:** Viewing is `read-only`. Editing is `draft`
(auto-saves) until explicitly published to a shared state (`confirmed-write`).

**Critical states:** Blank canvas (first use — scaffold a default stage
structure to invite the first edit, not a blank grid); collaborator editing
(concurrent edits — show active collaborators, resolve conflicts without
data loss); export state (journey rendered as a shareable artifact — PDF,
image, or linked doc).

**Navigation behavior:** Journey surface uses a horizontal stage-based
navigation within the map. Primary navigation is accessible but not
persistent within the canvas view.

---

## 8. Tutorial

**Primary user:** Learner — new to a concept, tool, or workflow; following
prescribed steps.

**Job:** Acquire a skill by doing — completing a worked example, not just
reading.

**First-screen contract:** Goal is named in the heading (what the learner
will be able to do after completing this). Prerequisites are listed before
step 1. Step 1 is visible without scrolling.

**Primary action:** Complete step 1 and observe the result.

**Expected result:** The learner sees that the step worked — the observable
outcome matches what the tutorial described.

**Next action:** Continue to step 2 or the next tutorial in a series.

**Proof:** Learner can complete the tutorial independently — without
external help — and produce the named outcome.

**Read/write consequence:** Tutorial exercises are sandboxed or clearly
scoped. If a tutorial step writes to a real artifact (not a sandbox),
it is `confirmed-write` with the consequence stated before the step.

**Critical states:** Stuck state (step failed — show the error and the
recovery path inline; never leave the learner at a broken terminal with
no next step); prerequisite missing (tool or account not set up — name
what's needed and link to setup, don't proceed past step 1); completion
state (all steps done — confirm completion and name the next tutorial or
exercise).

**Navigation behavior:** Tutorial navigation is linear by default — previous
step / next step controls. A chapter or section menu is available but
secondary. Do not surface unrelated tutorials as "you might also like" until
completion.

---

## 9. Task how-to

**Primary user:** Practitioner — knows the tool, looking for a specific
procedure.

**Job:** Find the exact steps for a task and complete it without reading the
whole document.

**First-screen contract:** Heading names the task, not the concept. A brief
one-line "use when:" scopes the guide. Step 1 is visible above the fold.

**Primary action:** Find and execute the relevant step.

**Expected result:** The task is completed; the practitioner can return to
their work.

**Next action:** Return to the product workspace or the next related how-to.

**Proof:** A practitioner who knows the tool but forgot the exact steps can
complete the task from the guide in under 3 minutes.

**Read/write consequence:** The guide itself is `read-only`. Steps that
write to the user's environment (a configuration change, a destructive
command) are marked explicitly: `confirmed-write` (a reversible change)
or `destructive` (an irreversible change — shown in a callout before the
command).

**Critical states:** Prerequisite path (setup not done — steps that require
a prior setup name it inline with a link); multiple platform paths (the steps
differ by OS or config — show a platform selector, not parallel sets of
steps); outdated warning (the procedure applies to a specific version — name
it; if the content may be stale, date it and link to the changelog).

**Navigation behavior:** In-page navigation (anchor links to H2 sections) for
long how-tos. Related how-tos linked at the bottom. No sidebar nav within the
task guide itself — a sidebar is for the guide collection (reference index, archetype 10).

---

## 10. Reference index

**Primary user:** Practitioner or developer — looking for a specific fact,
parameter, or API surface.

**Job:** Find a precise piece of information and extract it without reading
surrounding content.

**First-screen contract:** Search or alphabetical navigation is the
primary entry point. Content is organized by lookup key (a command name,
a field name, a concept), not by narrative arc.

**Primary action:** Search or navigate to the reference entry.

**Expected result:** The entry answers the question completely — definition,
type/signature, example, related entries — without requiring the reader to
open another document.

**Next action:** Return to the task or open a related reference entry.

**Proof:** A practitioner can find a specific parameter's type and default
value within 60 seconds.

**Read/write consequence:** Reference indexes are `read-only`.

**Critical states:** No-results search (suggest a related term; link to the
how-to for the closest task); stale content (reference applies to a specific
version — version selector or "last updated" date visible); incomplete entry
(a field is documented but its values are not exhaustive — mark it explicitly,
not silently).

**Navigation behavior:** Persistent alphabetical or category-based index
navigation. In-page anchor links within long entries. Search is always
accessible. Breadcrumb: reference > category > entry.

---

## 11. Explanation

**Primary user:** Reader — wants to understand a concept, the reason behind
a decision, or the shape of a system.

**Job:** Build a durable mental model — not find a fact, not complete a task.

**First-screen contract:** Heading names the concept. Opening paragraph
names what the reader will understand by the end and who this explanation
is for. The first section introduces the concept at the reader's current
level, not the expert's level.

**Primary action:** Read through to build understanding.

**Expected result:** Reader can explain the concept in their own words.

**Next action:** Related how-to, tutorial, or a deeper explanation of a
sub-concept.

**Proof:** A reader new to the concept can pass a short verbal quiz after
reading — without going back to look up answers.

**Read/write consequence:** Explanations are `read-only`.

**Critical states:** Jargon-heavy opening (reader hits a term they don't
know before building context — link to the glossary or explain inline, not
later); concept before problem (reader doesn't know why this matters — name
the problem the concept solves before naming the concept); length (if the
explanation exceeds 1500 words, it likely covers multiple concepts — split
by concept, link forward).

**Navigation behavior:** Linear reading is the primary flow. Anchor links
to H2 sections for long explanations. A "related concepts" section at the
bottom, not a sidebar during reading.

---

## 12. Multi-surface

**Primary user:** Any user who arrives at a product with multiple distinct
surfaces — a marketing site, a docs site, and a product app — and needs
to move between them without losing context.

**Job:** Move between surfaces without losing their place or their mental
model of where they are.

**First-screen contract:** Each surface identifies itself and its
relationship to the other surfaces in the product. A user who lands on
docs via search knows they can get to the app (and vice versa) without
a second search.

**Primary action:** Navigate to the surface that serves their current
job.

**Expected result:** The target surface loads at the correct entry point
for the job — not the home page of that surface.

**Next action:** Complete the job on the destination surface.

**Proof:** A user who arrives via search on any surface can reach any
other surface within two clicks, without backtracking to a home page.

**Read/write consequence:** Navigation between surfaces is `read-only`.
Entering a product surface that requires authentication is a `read-only`
→ `proposed-write` transition (the login prompt).

**Critical states:** Cross-surface dead end (the user has completed a
task on one surface and has no visible path to the logical next surface
— this is a critical wayfinding failure); authenticated vs. unauthenticated
state (a surface that serves both must show the correct nav without
requiring a page reload after login).

**Navigation behavior:** A persistent cross-surface navigation element —
at minimum a header link set — is visible on every page of every surface.
A footer link is the minimum; a persistent header is the standard. A user
who arrives at docs via a search engine and has never seen the marketing
site must have a visible, persistent route to it. Flag the absence of a
docs→marketing bridge as a blocker.

---

## Product-object mapping

Every surface exists because a user is doing something with a **product
object** — the entity the surface is about. Before designing the hierarchy,
name the primary object and the user's relationship to it.

### Object roles

| Role | What the user does | Examples |
|---|---|---|
| **Creates** | Brings the object into existence | New project, new journey map, new API key |
| **Receives** | Gets an object they did not initiate | Notification, assigned task, shared document |
| **Inspects** | Reads or audits the object without changing it | Dashboard metric, reference entry, audit log |
| **Changes** | Modifies an existing object | Edit a flow, update a setting, rename a project |
| **Approves** | Accepts or rejects a proposed change | Pull request review, budget approval, content sign-off |

### Visual weight rule

The object's role determines the visual weight of the primary action:

- **Creates / Changes / Approves** — primary action has maximum visual weight
  (the largest, most prominent interactive element above the fold).
- **Receives** — the incoming object has maximum visual weight; the action
  to act on it (accept, dismiss, route) is secondary.
- **Inspects** — no primary action needed above the fold; the object's data
  is the primary element.

### Mapping procedure

For each surface, answer these questions before designing hierarchy:

1. What is the primary object on this surface?
2. What role does the user have with that object?
3. What is the secondary object, if any?
4. Does the user's role with the object match the surface archetype?
   (An "inspect" role should route to a dashboard or reference index, not
   a transactional flow.)

A mismatch between the object role and the archetype is a design signal:
either the archetype is wrong for the job, or the surface is trying to
serve two incompatible jobs.

---

## Card-use test

A card is appropriate when **all three** of the following hold:

1. **The object is comparable.** The user needs to scan and compare multiple
   instances of the same object type (products, team members, templates).
2. **The object has a thumbnail or a primary attribute that scans well.**
   A card with only a title and a date is not better than a list row — it
   wastes space.
3. **The set size is browsable.** Cards are a browse pattern; if the user
   typically searches rather than browses, a list or table is faster.

### When cards are wrong

- The user is looking for a specific known item → use a list or table with search.
- The objects have many comparable attributes → use a table (attributes in columns).
- The set is larger than 50 items and browsing is not the primary mode → use a list with progressive load, not a card grid.
- The object is a line item or a log entry → use a list row.
- The card's secondary text is cut off by the card boundary and the cut text is decision-critical → use a list or expand the detail.

### Non-card alternatives

| Alternative | Use when |
|---|---|
| **List row** | Set is large, browsing is not primary, objects have few visual attributes |
| **Table** | Multiple attributes must be compared across instances |
| **Inline accordion** | Objects have variable depth; user drills into some but not all |
| **Feed / timeline** | Objects are ordered by time and the time relationship is the point |
| **Tree** | Objects have a hierarchical parent-child relationship |
| **Single pane** | Only one object is in scope at a time (a workspace, a detail view) |

---

## Attention contract

The attention contract names what the surface requires from the user.
Every surface operates under exactly one level at any given moment. Name
it before designing the hierarchy — the level determines which UI patterns
are appropriate.

### No-action

The user is reading or monitoring. No response is required, no deadline exists.
- Use: dashboards in a stable state, reference indexes, explanation pages.
- Pattern: no persistent call to action above the fold. Status is informational.
- Anti-pattern: a "no-action" surface with a primary CTA creates false urgency.

### Optional-progress

An action is available but not urgent. The user can defer without consequence.
- Use: onboarding suggestions, recommended next steps, optional configuration.
- Pattern: action available and visible, but not the most prominent element.
  Secondary button or inline link, not a modal.
- Anti-pattern: framing an optional action with urgent language ("You must
  do this") misrepresents the contract and erodes trust.

### Decision-required

The user must make a choice before continuing. The flow is blocked pending
the decision, but the decision is not irreversible.
- Use: confirmation dialogs, review steps, plan selection.
- Pattern: present the choice with enough context to decide. Two clear options;
  do not use three if two suffice. The default, if one exists, is pre-selected
  and labeled.
- Anti-pattern: blocking the flow for a decision that doesn't actually matter,
  or hiding the consequence of each option.

### Blocked-pending

The user cannot proceed because something outside their control has not resolved.
- Use: payment processing, approval waiting, async job running.
- Pattern: show progress, explain what is happening and how long it typically
  takes, provide a "notify me" or "go back" path. Never a spinner with no
  context.
- Anti-pattern: a blocked state that looks like an error, or one that offers
  no recovery path if the block does not resolve.

---

## Read/write permission contract

The permission contract names what the user can do to an object on a surface.
Apply it per object, per surface — a surface may show multiple objects with
different permission levels.

### Read-only

The user can see the object but cannot change it. The cause must be
determinable (role-based, not-yet-published, archived, pending approval).
- Pattern: no edit controls visible. A visible, non-alarming indicator
  names why editing is unavailable and, where possible, how to gain access.
- Anti-pattern: presenting an edit control that fails when the user clicks it.

### Draft

The user is editing a private copy. Changes are not visible to others until
explicitly shared or published.
- Pattern: "Draft" label visible. Autosave is active. Share/publish control
  is clearly distinct from save.
- Anti-pattern: a draft that auto-publishes on save, or a draft with no
  visible indication it is not yet visible to others.

### Proposed-write

The user has proposed a change that requires another action to take effect —
a form filled but not yet submitted, a setting staged but not yet applied.
- Pattern: changes are clearly staged (a summary of what will change). A
  "confirm" or "apply" action applies the proposed change; a "cancel" or
  "discard" reverts to the previous state.
- Anti-pattern: no visible staging — the user doesn't know if the change is
  pending or already applied.

### Confirmed-write

The user's action is applied immediately and visible to others (or to the
system) upon save.
- Pattern: save action is explicit. A success confirmation is immediate and
  proportionate to the change's weight. If the change has a visible effect
  on other users, name that effect.
- Anti-pattern: a silent save (the user doesn't know the change was applied)
  or an over-dramatic confirmation for a minor change.

### Destructive

The action permanently removes or irrevocably alters an object.
- Pattern: the action is at least one click away from a visible control
  (not the primary button). A confirmation dialog names exactly what will
  be deleted or changed and states that the action cannot be undone.
  The confirm button is not the default; the cancel button is.
- Anti-pattern: a destructive action as the primary button, or a
  confirmation dialog that does not name what will be lost.

### Undo-recovery

The action has been applied but can be reversed within a defined window.
- Pattern: a toast or inline notice appears immediately after the action,
  showing the undo control and the window duration ("Deleted. Undo (30s)").
  After the window closes, the action becomes permanent (transitions to
  confirmed-write or destructive as appropriate).
- Anti-pattern: an undo window that silently closes without notice, or an
  undo that works but does not confirm it has been applied.
