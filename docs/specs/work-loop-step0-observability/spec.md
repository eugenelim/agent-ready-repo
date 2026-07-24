# Spec: work-loop-step0-observability

- **Status:** Shipped
- **Owner:** eugenelim
- **Constrained by:** `spec/spec-C-workloop-argless-resume` (defines Branch-1 behavior; Status: Shipped — body not modified by this spec); RFC-0067 §Change C

Mode: light (no structural or public-interface risk trigger — SKILL.md content edit + projection update)

## Objective

Step 0 of the work-loop has two related readability problems that erode
observability and maintainability. First, Branch 1 (exactly one active item)
silently begins the loop without stating the resolved spec path in the
orientation block — a stale `.active` entry pointing at the wrong spec goes
undetected until PLAN is already under way. Branch 3 (more than one active
item) already lists all paths before asking the user to pick; Branch 1
should match that explicitness. Second, the "Active spec" bullet in the
orientation block conflates two concerns: it is a data-surface field (collect
and display the active path) but its text also carries the three branch
outcomes as inline control-flow actions. This mixes data-surface and
control-flow in the same bullet, and duplicates the branch outcomes — they
are stated again in the closing paragraph — creating two sources of truth
that must stay aligned.

This spec fixes both: (1) Branch 1 echoes the resolved path in the
orientation block before proceeding; (2) the "Active spec" bullet is trimmed
to data-surfacing only, and the branch-outcome resolution is stated once, in
the closing paragraph.

**Backlog items consumed:** `work-loop-step0-branch1-echo-resolved-path`,
`work-loop-step0-branch-layout-restructure`.

## Acceptance Criteria

- [x] **AC1.** The closing paragraph of Step 0 in the source SKILL.md
  (`packs/core/.apm/skills/work-loop/SKILL.md`) directs Branch 1 to echo
  "Beginning on `<resolved-path>`" (or equivalent phrasing) before
  proceeding to PLAN — so the resolved path is explicitly visible to the
  user. This instruction lives in the closing paragraph, not in the
  "Active spec" bullet.
- [x] **AC2.** Branch 3 (more than one active item) already lists all active
  paths — verified that no change to its behavior is needed.
- [x] **AC3.** The three data-surface fields (Initiative / Milestone / Active
  spec) in the orientation block's bullet list do not contain embedded
  control-flow action text — the "Exactly one → begin on that spec without
  asking. Zero → surface… More than one → list…" clause is removed from the
  "Active spec" bullet.
- [x] **AC4.** Branch-outcome resolution is stated once (in the closing
  paragraph), not at both the "Active spec" bullet and the closing paragraph.
- [x] **AC5.** `make build-self FORCE=1` exits 0 and the projected
  `.claude/skills/work-loop/SKILL.md` reflects all changes.
- [x] **AC6.** The closing paragraph's Branch 1 instruction directs the echo,
  and Branch 2's exact message ("No active spec found — run `workspace-status`
  to see what's ready to start.") and Branch 3's "list all and ask" phrasing
  are relocated verbatim from the "Active spec" bullet into the closing
  paragraph when the bullet is trimmed. The relocated text does not paraphrase
  or abbreviate the Branch 2 message.

## Boundaries

### Always do
- Edit `packs/core/.apm/skills/work-loop/SKILL.md` (source) — Step 0 only
- Re-project with `make build-self FORCE=1`

### Never do
- Change the semantics of Branch 1 — it must still proceed without asking
  after echoing the path; only the echo is added
- Change the semantics of Branch 2 (zero active items) or Branch 3 (more
  than one active item)
- Touch any section of SKILL.md other than Step 0
- Add new branches or alter the routing logic

### Ask first
- Any wording change to Branch 2's "No active spec found…" message
- Any wording change to Branch 3's listing or asking behavior
- Removing the closing paragraph (it carries non-redundant content: the
  path-stripping instruction and the PLAN-entry mechanics)

## Testing Strategy

Goal-based throughout. After editing:
1. Read `packs/core/.apm/skills/work-loop/SKILL.md` Step 0 and verify:
   - "Active spec" bullet contains no branch control-flow text (AC3)
   - The closing paragraph contains the Branch 1 echo instruction: "state 'Beginning on `<resolved-path>`'" (AC1)
   - The closing paragraph contains Branch 2's verbatim message and Branch 3's list phrasing, relocated from the bullet (AC4, AC6)
   - Branch outcomes appear in the closing paragraph and nowhere else in Step 0 (AC4)
2. Run `make build-self FORCE=1`; verify exit 0 (AC5)
3. Read `.claude/skills/work-loop/SKILL.md` (projected) and confirm it matches
   the source edits (AC5)

## Assumptions

- Technical: source SKILL.md is at `packs/core/.apm/skills/work-loop/SKILL.md`;
  projected copy is at `.claude/skills/work-loop/SKILL.md` (confirmed via find).
- Technical: `make build-self FORCE=1` routes through
  `python3 tools/build_gate_chain.py build-self --force --packs-dir packs`
  (confirmed via Makefile lines 52–53); `FORCE=1` bypasses the dirty-tree guard.
- Technical: in the current SKILL.md, Branch 1's control-flow text is inside
  the "Active spec" bullet as "Exactly one → begin on that spec without asking."
  — the echo is absent.
- Technical: branch outcomes appear in two places — inside the "Active spec"
  bullet and in the closing paragraph (SKILL.md:167-172, confirmed to be inside
  Step 0 boundary); the closing paragraph is the better single source because it
  also carries the path-stripping instruction and PLAN-entry mechanics.
- Process: `docs/specs/spec-C-workloop-argless-resume/spec.md` is Shipped
  (Frozen) — its body is not modified by this spec. spec-C's AC2 Branch 1
  text ("begin the loop on that spec without asking") predates the echo
  requirement; this spec supersedes it by adding the echo instruction to the
  source SKILL.md. spec-C is referenced as the historical contract definition.

## Tasks

1. Read `packs/core/.apm/skills/work-loop/SKILL.md` Step 0 to confirm exact
   line numbers (they may have shifted since this spec was authored).
2. Edit the "Active spec" bullet: remove the inline branch-outcome text;
   leave only the data-surface instruction ("Collect every path in
   `["ini-NNN".work].active` across all active initiatives").
3. Edit the closing paragraph: add Branch 1 echo — "state 'Beginning on
   `<resolved-path>`' in the orientation block, then strip the `spec/` prefix…";
   expand to name all three branches explicitly, making the paragraph the single
   canonical statement of branch outcomes.
4. Run `make build-self FORCE=1`; confirm exit 0; read projected SKILL.md to
   verify changes propagated.

## Declined

- Removing the closing paragraph and consolidating all branch logic into the
  bullet list — the closing paragraph carries path-stripping and PLAN-entry
  mechanics not duplicated in the bullet; removing it would lose those.
- Rewording Branch 3's listing behavior — Branch 3 already lists all paths and
  asks the user to pick; changing it is out of scope.
- Adding a "### Branch resolution" subsection — the closing paragraph is the
  natural home; a new subsection restructures more than necessary for light mode.
- Editing `docs/specs/spec-C-workloop-argless-resume/spec.md` body — that spec
  is Shipped (Frozen). CONVENTIONS §4 does not allow body edits to frozen specs.
  This spec supersedes spec-C's Branch-1 description by updating the source
  SKILL.md directly; spec-C remains as a historical record of the prior contract.
