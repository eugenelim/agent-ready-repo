# workspace-status — Current Behavior Map

> Authoritative source for Order 0 characterization. Serves as both test index and
> implementation reference. Where RFC, prose, and implementation disagree, the
> disagreement is noted explicitly.

---

## 1. Inputs

| Input | Source | Notes |
|-------|--------|-------|
| `workspace.toml` | Repo root | Required; skill offers to initialise if absent |
| `docs/specs/*/spec.md` | Spec tree | Used by reconciliation scans (Step 2a) |
| `docs/product/findings/rfc-candidates.md` | Findings register | Read for count display |
| `docs/product/findings/roadmap-intents.md` | Findings register | Read for count display |

**No flags, modes, or CLI switches exist.** workspace-status is invoked by name with no
arguments. "Quick" vs "full" are not currently implemented — all invocations run the
full procedure including reconciliation.

---

## 2. Modes and triggers

workspace-status is a skill (LLM instructions), not a Python CLI. It triggers on
natural-language phrases: "workspace status", "orient me", "what's next", "session
start", "show the queue", etc. (full list in SKILL.md frontmatter description).

There is no "quick" mode that skips reconciliation and no "full" mode that adds extra
checks. The current behavior is: always run all three reconciliation scan types.

**Known schema/usage drift — initiative status vocabulary:**

SKILL.md (line 57) documents the initiative status vocabulary as `active | paused | closed`.
However, the real `workspace.toml` in this repo uses `complete` (not `closed`) for at least
one historical initiative. The engine and skill both accept whatever string is present; the
characterization suite (AC2b) exercises `complete` as the observed legacy form. A future
order should either align the vocabulary (update `workspace.toml` to `closed`) or update
the SKILL.md documentation to include `complete` as a valid synonym.

---

## 3. How ready, blocked, active, and shipped are computed

### Entry types

A `[work].queue` entry is either:
- A bare string `"spec/foo"` — no dependencies, unconditionally ready
- An inline object `{path = "spec/foo", needs = "work:spec/bar"}` — has dependencies

An entry in `[work].active` is the currently in-progress spec (one per initiative
by convention; multiple allowed by schema).

An entry in `[work].shipped` is a completed spec. Shipped entries are always bare strings.

### Ready

An entry is **ready** when all its `needs` entries are satisfied (see §5). An entry
with no `needs` field is unconditionally ready unless already in `active` or `shipped`.

### Blocked

An entry is **blocked** when one or more `needs` entries are not satisfied.

### Active

Entries in `[work].active` are surfaced as currently in-progress. They do NOT appear in
the ready/blocked classification — they are already running. A queue entry whose path
also appears in `active` or `shipped` is excluded from the ready/blocked classification
(SKILL.md §2: "unconditionally ready unless already in active or shipped").

### Shipped

Entries in `[work].shipped` are historical. They are used as the satisfaction source for
`work:<path>` and cross-initiative `ini-NNN:work:<path>` needs.

---

## 4. How shaping_queue entries are classified

`[shaping_queue].active` entries appear under "Ready to start" with type-appropriate
skill routing (see §7). `[shaping_queue].backlog` entries appear under "Blocked" or
not at all, depending on whether their `needs` are satisfied.

### Signal entries

`type = "signal"` entries NEVER appear as "Ready to start". They surface under
"Active context" as ongoing landscape monitoring. They do not graduate.

---

## 5. `needs` prefixes and resolution semantics

| Prefix | Resolves against | Satisfied when |
|--------|-----------------|----------------|
| `work:<path>` | `["<same-ini>".work].shipped` OR `["<same-ini>".work].active` | Path appears in shipped **or active** (active counts as in-progress) |
| `shape:<slug>` | `["<same-ini>".shaping_queue].active` OR not present | In active OR absent from all shaping lists |
| `research:<slug>` | `["<same-ini>".shaping_queue]` entries of `type = "research"` | Entry is NOT in `.backlog` |
| `brief:<path>` | `["<same-ini>".brief_queue].ready` or `executing` | In ready or executing |
| `<ini-slug>:work:<path>` | `["<ini-slug>".work].shipped` | Path appears in target ini's shipped |

**Known gap:** `backlog:<slug>` prefix is documented in `workspace.toml` header comments
(line 14) but absent from the SKILL.md needs-resolution table (§2). The behavior for
`backlog:<slug>` needs is **undefined** — the skill will either ignore it, treat it as
unknown, or fail to resolve. This is a spec/implementation gap to be fixed in a later
order.

**Known behavior:** `shape:<slug>` resolves as satisfied when the slug is absent from
ALL shaping lists — meaning if a shaping prerequisite was never added to any queue, it
is treated as done. This is intentional (RFC-0064 D9).

---

## 6. Three reconciliation scan types

Run every time workspace-status is invoked. All three pass over `docs/specs/*/spec.md`
files. Status is extracted from the first line matching `- **Status:**`.

### Type 1 — Forward scan: untracked live specs

Walk every directory under `docs/specs/` containing a `spec.md`. For each:
1. Extract Status. Skip if not `Approved` or `Implementing`.
2. Derive canonical path: `spec/<dirname>`.
3. Check if path appears in ANY initiative's queue, active, or shipped list.
4. If absent from all → **Type 1 finding**: "untracked live spec".

Scope: ALL spec directories under `docs/specs/`, regardless of initiative.

### Type 2 — Backward scan: stale queue/active entries

For each initiative, for each path in `[work].queue` and `[work].active`:
1. Resolve `docs/specs/<slug>/spec.md`. Skip if absent (no warning).
2. Extract Status. If `Shipped` or `Archived` → **Type 2 finding**: "stale entry".

**Note:** `[work].active` entries in Type 2 get a special interactive check:
"Is `<path>` actively being worked on in this session?" Confirmed inactive entries
are included in the cleanup offer.

Scope: queue and active entries of ALL initiatives.

### Type 3 — Shipped scan: prematurely shipped entries

For each initiative, for each path in `[work].shipped`:
1. Resolve `docs/specs/<slug>/spec.md`. Skip if absent (no warning).
2. Extract Status. If `Approved` or `Implementing` → **Type 3 finding**: "prematurely shipped".

Scope: shipped entries of ALL initiatives.

### Cleanup write (Type 2 only)

After user confirmation (Y), workspace-status writes back to workspace.toml:
- Shipped spec in queue/active: remove from queue/active; append bare string to shipped
- Archived spec in queue/active: remove from queue/active; do NOT add to shipped
- Uses comment-preserving write (tomlkit or targeted text insertion)
- NEVER uses `tomllib` + `tomli_w` round-trip (strips comments)

---

## 7. Skill routing by shaping entry type

| Type | Routed skill | Pack required |
|------|-------------|---------------|
| `shape` (default) | `frame-intent` | None (core) |
| `research` | `desk-research-project-start` | desk-research pack |
| `strategy` | `frame-situation` (M2); interim: `frame-intent` | product-engineering pack (M2) |
| `signal` | No action; "active context" only | — |
| `design` | `experience-status`; fallback: `journey-mapping` | experience-design pack |

If required pack is not installed, workspace-status surfaces: "requires `<pack-name>` pack."

---

## 8. workspace.toml reads performed by work-loop

work-loop reads `workspace.toml` in **Step 0 ORIENT**:

1. **Active spec resolution** (argless invocation only):
   - Reads `["ini-NNN".work].active` across all active initiatives
   - Branch 0: zero active → stops, points to workspace-status
   - Branch 1: exactly one active → uses that spec path
   - Branch 2+: more than one active → lists all, asks user to pick

2. **Stale-queue check** (Step 0):
   - Reads `["ini-NNN".work].queue` and `["ini-NNN".work].active`
   - For each entry, checks `docs/specs/<slug>/spec.md` Status
   - If Status = `Shipped` → emits **warning only**, does NOT write
   - Does not trigger cleanup; cleanup is workspace-status's responsibility

3. **Shaping-item guard** (Step 0, before PLAN):
   - Derives slug from the spec path (strips `docs/specs/` prefix and trailing `/`)
   - Checks **active initiatives only** (`status == "active"`); paused/closed/complete initiatives are skipped
   - Scans each active initiative's `[shaping_queue].active` and `.backlog` for a slug match
   - Also scans the top-level `[backlog].open` typed entries for a slug match
   - On match: stops before PLAN and surfaces the routing skill (see Section 7)
   - On no match: proceeds to PLAN normally

---

## 9. workspace.toml writes performed by work-loop

**Current behavior (as of commit `a46d6f46`):** work-loop writes to `workspace.toml`
in **one** place only. The done-step that moved specs from `active → shipped` or
`queue → shipped` was deliberately removed in that commit ("workspace-status
responsibility, not work-loop's"). The finish checklist now only sets the spec.md
`**Status:**` to `Shipped` — it does not write to workspace.toml.

### 9a. Deferred items (DECIDE step)

When a reviewer finding is deferred:
- Writes `{slug = "<slug>", source = "spec/<name> ACn"}` to `[backlog].open`
- Requires a cold-start-sufficient TOML comment above the entry
- Uses comment-preserving write; same constraint as workspace-status cleanup

**Historical note:** `spec/work-loop-queue-shipped-fix` (Status: Shipped) specified a
done-step that moved specs from `active`/`queue` → `shipped` in workspace.toml. That
write was removed in commit `a46d6f46` when responsibility was reassigned to
workspace-status. The spec remains in the repo as history; its ACs no longer
reflect current work-loop behavior.

---

## 10. State ownership analysis (current vs. proposed)

### Current (authoritative today)

| State | Authoritative source | Derived/duplicated |
|-------|--------------------|--------------------|
| Spec status (Approved/Implementing/Shipped/Archived) | `docs/specs/<slug>/spec.md` **Status:** field | workspace.toml queue/active/shipped lists are a MANUAL mirror |
| Work queue order | `[work].queue` list order | No derivation mechanism |
| Cross-initiative deps | `needs` field on queue entries | Resolved at display time by workspace-status |
| Backlog items | `[backlog].open` | No derivation; manually added by work-loop DECIDE |
| Shaping queue state | `[shaping_queue].active` + `.backlog` | Manually maintained |

### Current duplication gap

`workspace.toml` maintains `active` and `shipped` arrays that DUPLICATE the
authoritative status in each `spec.md`. A spec marked `Shipped` in its `spec.md`
but still in `[work].queue` is a stale entry (Type 2 finding). This duplication
is the root cause of **Type 2 and Type 3** reconciliation findings.

`[work].queue` is **authoritative ordered portfolio intent** — it is not a lifecycle
mirror. Queue order is declared by the team; it cannot be derived from spec status.

**Type 1 is independent.** The Type 1 forward scan finds specs in `Approved` or
`Implementing` status that do not appear in any workspace.toml list. It is an
*undeclared-work audit*, not drift between `spec.md` and `work.active`/`work.shipped`.
Removing `work.active` and `work.shipped` does **not** eliminate Type 1.

**Known defect:** `work.active` is redundant with `spec.md Status: Implementing`.
**Known defect:** `work.shipped` is redundant with `spec.md Status: Shipped`.

### Proposed future ownership (labeled as proposed, not current)

The workspace.toml collision design (memory: `project_workspace_collision_design.md`)
proposes:
- Remove `work.active` and `work.shipped` from workspace.toml
- Derive active/shipped status from `spec.md Status:` at runtime
- Keep only `work.queue` (ordered intent) as the authoritative source in workspace.toml

This simplification would eliminate Type 2 and Type 3 reconciliation scan types by
removing the duplication. Type 1 remains — it is the untracked-live-spec audit and
does not depend on `work.active`/`work.shipped`. A "quick" / "full" mode split would
be the mechanism to move Type 1 off the default session-start path (KD-04).
**This is NOT implemented in Order 0.**

---

## 11. Known defects and gaps

| ID | Category | Description | Severity |
|----|----------|-------------|---------|
| KD-01 | Spec gap | `backlog:<slug>` needs prefix documented in workspace.toml header but absent from SKILL.md needs-resolution table | Minor |
| KD-02 | Behavior gap | No cycle detection: if A needs B and B needs A, both show as blocked forever with no error | Minor |
| KD-03 | Behavior gap | Missing dependency targets: a `work:spec/foo` need that points to a spec absent from ALL lists will never be satisfied; no warning | Minor |
| KD-04 | Behavior gap | No "quick" mode — reconciliation always runs even for simple orientation queries | Performance |
| KD-05 | Duplication | `work.active`/`work.shipped` duplicate `spec.md Status:`; cause of Type 2 and Type 3 findings (Type 1 is an independent undeclared-work audit) | Architectural |
| KD-06 | Spec inconsistency | SKILL.md says `shape:<slug>` "treated as shipped if not present" but workspace.toml header says `shape:` without this qualification | Minor |
| KD-07 | Missing test | `brief:<path>` needs resolution is underspecified; `brief_queue` structure varies | Minor |

---

## 12. Reference: status extraction algorithm

From a `spec.md` file:
1. Find the first line starting with `- **Status:**`
2. Transition form `X → Y` (or `X → Y → Z` multi-hop): use a greedy match to capture the first word after the **last** `→`. Examples: `Approved → Shipped` → `Shipped`; `Draft → Approved → Shipped` → `Shipped`.
3. Simple form: take first word after `**Status:** ` (stop at whitespace or `<!--`)
4. If no `**Status:**` line → unknown status; skip this path in all scans

Valid vocabulary: `Draft | Approved | Implementing | Shipped | Archived`
