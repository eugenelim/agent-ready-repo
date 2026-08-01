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

- [x] **AC1.** The "Active spec" bullet body carries an inline instruction to
  include "Beginning on `docs/specs/<slug>/spec.md`" in the orientation block
  for the exactly-one case (e.g., "If exactly one, include 'Beginning on
  `docs/specs/<slug>/spec.md`' in this orientation block"). The instruction is
  inline body text, not a sub-item.
- [x] **AC3.** The "Exactly one →" sub-item is removed from the "Active spec"
  bullet. Branch 2 and Branch 3 sub-items remain.
- [x] **AC4.** The closing paragraph's "exactly one active item" routing line
  (strip prefix + read + proceed to PLAN) is unchanged. The unreachable
  "Zero or multiple active items → stop after surfacing" bullet is removed.
- [x] **AC5.** `make build-self FORCE=1` exits 0 and both projected copies
  (`.claude/skills/work-loop/SKILL.md` and `.agents/skills/work-loop/SKILL.md`)
  reflect all changes.
- [x] **AC6.** `make build-check` exits 0.
- [x] **AC7.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  carry the next available patch version above the working pack version (check
  `python3 -c "import tomllib; d=tomllib.load(open('packs/core/pack.toml','rb')); print(d['pack']['version'])"` —
  `grep "^version"` matches both `[pack]` and `[pack.adapter-contract]`; use the
  TOML-scoped lookup). Use the next unused patch to avoid colliding with
  in-flight branches. A
  `docs/product/changelog.md` entry exists for the version.
- [x] **AC8.** `packs/core/.apm/skills/work-loop/evals/evals.json` contains
  three new eval cases: `step0-branch1-echo-resolved-spec` (exactly one active
  item → echo in orientation block), `step0-branch2-zero-active-specs` (zero
  active items → verbatim message + stop), and `step0-branch3-multiple-active-specs`
  (multiple active items → list + ask + stop).
- [x] **AC9.** Manual QA: work-loop invoked argless in a session with exactly one
  active spec produces an orientation block that includes "Beginning on
  `docs/specs/<slug>/spec.md`" as part of the block output. Observed output recorded.

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
