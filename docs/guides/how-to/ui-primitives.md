# How to use the UI primitives

This guide covers the sixteen reusable UI components for the platform site
(`web/` and `docs-site/`). Use these primitives when authoring product
documentation, journey pages, or catalogue entries that describe agentic
workflows.

---

## Decision guide — which primitive to reach for

| Situation | Primitive |
|-----------|-----------|
| Display a single-line badge for a resource scope, state, or label | `StatusChip` |
| Communicate whether an agent will read or write | `ReadWriteBadge` |
| Communicate how complete a result set is | `CoverageBadge` |
| Show whether a required permission is present | `PermissionBadge` |
| Display a natural-language prompt the user can copy | `PromptBlock` |
| Show just the copyable prompt string inline | `CopyPrompt` |
| Show an agent asking a clarifying question | `AgentClarification` |
| Show what a step will return (records, counts, warnings) | `ExpectedResult` |
| Show a human-decision gate that blocks progress | `DecisionBand` |
| Show a write operation waiting for confirmation | `WriteConfirmation` |
| Show a single next action (prompt, guide, stage, or decision) | `NextAction` |
| Show job-based navigation tabs or nav links | `TaskSwitcher` |
| Show progress through connected journey stages | `JourneyRail` |
| Display a compact skill reference lookup | `SkillRecord` |
| Introduce a page with its outcome and primary action | `PageHero` |
| Show compact metadata (mode, permissions, coverage) | `PageMeta` |

---

## Card-use test

Before adding a card layout to agentic documentation, ask:

1. Are there truly multiple items the reader needs to compare? A single item is not a card.
2. Do the items share the same fields? Mixed-field items are a list, not a card grid.
3. Is the primary job to scan, not to read? Cards invite scanning; prose invites reading.

If the answer to all three is yes, a card layout may be appropriate. Otherwise
use a list (`SkillRecord` for reference data, `ExpectedResult` for records).

---

## State semantics

All badge components and StatusChip share a common state vocabulary. Use these
states consistently — never repurpose a state for a different semantic meaning.

| State | Semantic meaning | Token family |
|-------|-----------------|--------------|
| `informational` / `read-only` | Agent is observing; no changes | `--ds-state-info-*` |
| `draft` | Agent is composing; no changes saved | `--ds-state-neutral-*` |
| `proposed-write` | Agent proposes a change; awaiting human confirmation | `--ds-state-warn-*` |
| `confirmed-write` | Human confirmed; agent is writing | `--ds-state-success-*` |
| `approval-required` | Write requires explicit approval step | `--ds-state-warn-*` |
| `complete` | All items returned | `--ds-state-success-*` |
| `partial` | Some items returned | `--ds-state-warn-*` |
| `blocked` | Operation cannot proceed | `--ds-state-danger-*` |
| `failed` | Operation failed | `--ds-state-danger-*` |
| `unavailable` | Feature or permission not available | `--ds-state-neutral-*` |

---

## Accessibility expectations

Every primitive meets WCAG 2.2 AA:

- All states are communicated in visible text (never color alone).
- Interactive elements have accessible names (`aria-label` or visible text).
- Touch targets are ≥ 44 × 44 px.
- Focus visible styles use `outline: 2px solid var(--ds-accent)`.
- Live regions (`aria-live="polite"`) announce dynamic updates (copy success,
  status changes).

---

## Responsive expectations

| Primitive | Desktop | Mobile (<768px) |
|-----------|---------|-----------------|
| `JourneyRail` | Horizontal `<ol>` with connected stages | `<details>/<summary>` accordion per stage |
| `PageMeta` | Single flex row | Wraps to prioritized rows |
| `SkillRecord` | CSS grid aligned rows | Stacked `<dl>` definitions |
| `WriteConfirmation` | Inline panel | Single-column, full-width actions |
| All others | Flex or block | Stack naturally |

---

## Usage patterns

### Pattern 1: Prompt followed by result

A typical agent interaction where the user provides a prompt and the agent
returns structured data.

```astro
---
import PromptBlock from '../components/primitives/PromptBlock.astro';
import ExpectedResult from '../components/primitives/ExpectedResult.astro';
---

<PromptBlock
  speaker="User"
  prompt="List all open Jira issues assigned to the team"
  mode="read-only"
/>

<ExpectedResult
  summary="Returns all open issues assigned to the current team"
  records={[
    { key: 'Type', value: 'Bug, Story, Task, Epic' },
    { key: 'Filter', value: 'status = Open AND assignee in membersOf(team)' },
    { key: 'Limit', value: 'Up to 50 per page' },
  ]}
  status="partial"
  warnings={['Results are capped at 50 per page']}
/>
```

---

### Pattern 2: Read-only state followed by a decision gate

Shows an agent in read-only mode presenting a summary, followed by a decision
the human must make before any writes occur.

```astro
---
import PageMeta from '../components/primitives/PageMeta.astro';
import DecisionBand from '../components/primitives/DecisionBand.astro';
---

<PageMeta
  items={[
    { type: 'mode', mode: 'read-only' },
    { type: 'permission', permission: 'read:issues', access: 'granted' },
  ]}
/>

<DecisionBand
  summary="Update 12 sprint issues to 'In Progress'"
  consequence="This change is visible to your entire team immediately."
  primaryAction={{ label: 'Confirm update', href: '/confirm' }}
  secondaryAction={{ label: 'Cancel', href: '/cancel' }}
  scope="Issues in current sprint only — backlog is unchanged."
/>
```

---

### Pattern 3: Reference record

A compact lookup table for a skill's read/write surface.

```astro
---
import SkillRecord from '../components/primitives/SkillRecord.astro';
---

<SkillRecord
  name="jira-team-status"
  goals={['Review what the team is working on', 'Identify blocked stories']}
  reads="Issues, sprints, assignees, status transitions"
  writes="Read-only — no Jira writes"
  returns="Summary table of in-progress, blocked, and recently completed items"
  limits="Up to 50 issues; pagination available"
  followUp="Use jira-story-triage to prioritise unresolved blockers"
/>
```

---

### Pattern 4: Write confirmation

An in-flow confirmation panel before a destructive or consequential write.

```astro
---
import WriteConfirmation from '../components/primitives/WriteConfirmation.astro';
---

<WriteConfirmation
  objects={['PROJ-101', 'PROJ-102', 'PROJ-103']}
  fields={[
    { label: 'Status', value: 'In Progress → Done' },
    { label: 'Sprint', value: 'Sprint 24 → Closed' },
  ]}
  protectedFields={['Priority', 'Labels', 'Assignee']}
  writeCount={3}
  consequence="Closing these issues will move them out of the active sprint."
  onConfirm="/confirm-close"
  onCancel="/cancel"
/>
```

---

### Pattern 5: Mobile journey presentation

A journey rail that shows step progression and adapts to small screens.

```astro
---
import JourneyRail from '../components/primitives/JourneyRail.astro';
---

<JourneyRail
  currentId="review"
  stages={[
    { id: 'connect',     label: 'Connect',     status: 'complete' },
    { id: 'triage',      label: 'Triage',      status: 'complete' },
    { id: 'review',      label: 'Review',      description: 'Human reviews proposed changes' },
    { id: 'apply',       label: 'Apply',       isDecisionBoundary: true },
    { id: 'verify',      label: 'Verify' },
  ]}
/>
```

At desktop (≥ 768 px) this renders as a connected horizontal rail with the
current stage highlighted. At mobile (< 768 px) each stage becomes a
`<details>/<summary>` accordion, with the current stage open by default.

---

## Component reference

### StatusChip

Display-only. Use as the state-display atom inside other badge components.

```astro
<StatusChip label="draft" />
<StatusChip label="confirmed" state="confirmed-write" />
<StatusChip label="live update" state="info" live={true} />
```

Props: `label: string`, `state?: string`, `live?: boolean`

`live={true}` adds `role="status"` and `aria-live="polite"` for dynamic
updates announced to assistive technology.

**Anti-pattern:** Do not use StatusChip as the sole indicator of a write
consequence. Use ReadWriteBadge instead — it adds visible consequence text.

---

### ReadWriteBadge

Use when documenting what an agent will do (read vs. write vs. destructive).

```astro
<ReadWriteBadge mode="read-only" />
<ReadWriteBadge mode="proposed-write" />
<ReadWriteBadge mode="destructive" />
```

Props: `mode: 'read-only' | 'draft' | 'proposed-write' | 'confirmed-write' | 'publish' | 'destructive'`

Visible consequence text for each mode:
- `read-only` → "Read only"
- `draft` → "Draft — no changes saved"
- `proposed-write` → "Review before writing"
- `confirmed-write` → "Writing confirmed"
- `publish` → "Publishing now"
- `destructive` → "Destructive — cannot undo"

**Anti-pattern:** Do not use color alone to distinguish read from write — the
visible consequence label is the semantic carrier.

---

### CoverageBadge

Use when a result set is not complete (filtered, capped, or permission-limited).

```astro
<CoverageBadge coverage="complete" />
<CoverageBadge coverage="partial" detail="3 of 12 items returned" />
<CoverageBadge coverage="permission-limited" />
```

Props: `coverage: 'complete' | 'filtered' | 'partial' | 'capped' | 'permission-limited'`,
`detail?: string`

**Anti-pattern:** Do not suppress the badge when results are partial — the reader
must know the result set is incomplete.

---

### PermissionBadge

Use to show whether a permission required for a step is present.

```astro
<PermissionBadge permission="read:issues" access="granted" />
<PermissionBadge permission="write:issues" access="missing" />
```

Props: `permission: string`, `access: 'granted' | 'missing' | 'unknown'`

**Anti-pattern:** Never render raw credential values in the `permission` prop.
Use role names (`read:issues`) not tokens or API keys.

---

### PromptBlock

Use to display a natural-language prompt the user can copy and send to an agent.

```astro
<PromptBlock
  speaker="User"
  prompt="Review the current sprint and flag stories blocked for more than 48 hours."
  mode="read-only"
/>
```

Props: `speaker?: string`, `prompt: string`, `mode?: ReadWriteMode`,
`context?: string`, `variables?: Record<string, string>`

Visual contract: amber left border (`--ds-accent`), `--ds-accent-subtle` fill,
Inter sans-serif font. This is intentionally distinct from code blocks
(dark background, monospace font, no left border).

**Anti-pattern:** Do not use PromptBlock for code snippets. Use a fenced code
block instead.

---

### CopyPrompt

Use for inline copyable prompt strings, without the speaker/context framing
of PromptBlock.

```astro
<CopyPrompt prompt="agentbundle install --pack core" />
```

Props: `prompt: string`

---

### AgentClarification

Use to show a clarifying question the agent is asking before acting.

```astro
<AgentClarification
  question="Which sprint should the stories be moved to?"
  options={['Sprint 24', 'Sprint 25', 'Backlog']}
  reason="The target sprint was not specified in the request."
/>
```

Props: `question: string`, `options?: string[]`, `reason?: string`,
`blocked?: boolean`

`blocked={true}` applies `--ds-state-warn-*` styling to indicate the agent
cannot proceed without an answer. It is never styled as an error (danger state).

---

### ExpectedResult

Use to document what a skill returns — record structure, counts, and warnings.

```astro
<ExpectedResult
  summary="Returns open issues for the team"
  records={[{ key: 'Limit', value: '50 per page' }]}
  status="partial"
  warnings={['Results capped at 50']}
  followUp={[{ label: 'Filter by assignee', href: '/guides/jira/filter' }]}
/>
```

Props: `summary: string`, `records?: {key, value}[]`, `status?: string`,
`warnings?: string[]`, `followUp?: {label, href}[]`

Table cells scroll horizontally on narrow viewports — do not suppress overflow.

---

### NextAction

Use to present exactly one recommended next action to the user.

```astro
<NextAction type="prompt" label="Run sprint review" prompt="Show me blocked stories in the current sprint" />
<NextAction type="guide" label="Set up credentials" href="/guides/setup" />
<NextAction type="decision" label="Confirm write" href="/confirm" />
```

Props: `type: 'prompt' | 'guide' | 'stage' | 'decision'`, `label: string`,
`href?: string`, `prompt?: string`

Do not stack multiple NextAction components — it conveys a single next step.
Use TaskSwitcher or a list for multiple options.

---

### DecisionBand

Use to present a human-decision gate that blocks agent progress until confirmed.

```astro
<DecisionBand
  summary="Merge 6 pull requests to main"
  consequence="This action triggers CI and notifies reviewers."
  primaryAction={{ label: 'Confirm merge', href: '/confirm' }}
  secondaryAction={{ label: 'Cancel', href: '/cancel' }}
  scope="PRs in this sprint only — other branches are unchanged."
/>
```

Props: `summary: string`, `consequence: string`,
`primaryAction: {label, href}`, `secondaryAction?: {label, href}`,
`scope?: string`

Full-width panel with `--ds-state-warn-bg` fill and `4px solid --ds-accent`
left border. Consequence text is bold and larger than adjacent body text.

**Anti-pattern:** Do not use DecisionBand for informational content. It is a
decision gate — the primary action must represent a consequential choice.

---

### WriteConfirmation

Use to collect explicit confirmation before writing, updating, or deleting data.

See Pattern 4 above for a full example.

Props: `objects: string[]`, `fields: WriteField[]`, `protectedFields?: string[]`,
`writeCount: number`, `consequence: string`, `onConfirm?: string`,
`onCancel?: string`

Rendered as an in-flow `<section>` — not a `<dialog>`. Cancel is the first
focusable action (safe-path-first). Protected fields section is shown when
any field has `protected: true` or the `protectedFields` array is non-empty.

---

### PageHero

Use at the top of a journey or guide page to communicate the page's outcome
and primary action.

```astro
<PageHero
  title="Set up Jira integration"
  outcome="Your agent can read and manage your team's sprint backlog."
  primaryAction={{ label: 'Get started', href: '#step-1' }}
/>
```

Props: `title: string`, `outcome: string`, `primaryAction?: {label, href}`,
`secondaryAction?: {label, href}`, `badge?: BadgeProps`, `proof?: string`

Uses `--ds-surface` (light background). Does not assume a dark hero canvas.

---

### PageMeta

Use to show compact metadata at the top of a documentation page.

```astro
<PageMeta items={[
  { type: 'mode', mode: 'read-only' },
  { type: 'permission', permission: 'read:issues', access: 'granted' },
  { type: 'coverage', coverage: 'partial' },
]} />
```

Props: `items: PageMetaItem[]` — each item has a `type` and the corresponding
badge props for that type.

Wraps to multiple rows at ≤ 390 px.

---

### TaskSwitcher

Use for job-based navigation tabs or contextual navigation links.

```astro
<!-- Navigation mode: link to different pages -->
<TaskSwitcher
  type="nav"
  items={[
    { label: 'Overview', href: '/guides/jira' },
    { label: 'Setup', href: '/guides/jira/setup' },
    { label: 'Skills', href: '/guides/jira/skills' },
  ]}
/>

<!-- Tab mode: switch panels on the same page -->
<TaskSwitcher
  type="tabs"
  activeId="setup"
  items={[
    { label: 'Setup', id: 'setup' },
    { label: 'Usage', id: 'usage' },
    { label: 'Limits', id: 'limits' },
  ]}
/>
```

Props: `type: 'nav' | 'tabs'`, `items: {label, href?, id?}[]`, `activeId?: string`

`type="nav"` is pure CSS; `type="tabs"` includes a minimal inline script for
ARIA tab management and arrow-key navigation.

---

### JourneyRail

See Pattern 5 above.

Props: `stages: JourneyStage[]`, `currentId?: string`

Each stage: `id: string`, `label: string`, `description?: string`,
`status?: 'complete' | 'current' | 'upcoming'`, `isDecisionBoundary?: boolean`

Decision boundaries are shown with a dashed connector and diamond marker class.

---

### SkillRecord

See Pattern 3 above.

Props: `name: string`, `goals: string[]`, `reads: string`, `writes: string`,
`returns: string`, `limits?: string`, `followUp?: string`

Renders as a CSS grid definition list on desktop; switches to stacked `<dl>`
at ≤ 390 px.

---

## Anti-patterns

| Anti-pattern | Why it's wrong | What to use instead |
|---|---|---|
| Using color as the sole state indicator | Fails WCAG 1.4.1 (Use of Color) | All state components include visible text |
| Stacking multiple `NextAction` components | Confuses the user about which action to take | Use `TaskSwitcher` or a list |
| Using `DecisionBand` for informational content | It communicates "stop and decide" — not "here is information" | Use `ExpectedResult` or a standard blockquote |
| Using `PromptBlock` for code | Code blocks have their own distinct rendering contract | Use a fenced ``` code block |
| Omitting `CoverageBadge` on partial results | Reader assumes results are complete | Always show `CoverageBadge coverage="partial"` |
| Using `<dialog>` for WriteConfirmation | Modal interrupts focus unexpectedly | Use the in-flow `WriteConfirmation` panel |
| Adding `aria-expanded` to `<details>/<summary>` | Browser manages this natively; manual ARIA creates conflict | Let native `<details>` manage its own state |
