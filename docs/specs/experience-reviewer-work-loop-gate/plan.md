# Plan: experience-reviewer-work-loop-gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Implementing

## Tasks

### Task 1: Write ADR-0047 and update ADR README

**Verification mode:** Visual / manual QA

**Done when:** `docs/adr/0047-experience-reviewer-as-work-loop-gate.md` exists,
status Accepted, records: the mandatory/recommended split (select-or-note for
full-mode user-facing diffs; recommendation only for light mode); the trigger
scoping rationale (existing "Structural or public-interface change" covers
net-new pages); and the ADR-0042 value test clearance. `docs/adr/README.md`
table includes ADR-0046 (if previously missing) and ADR-0047.

**Tests:** `no stub (mode)` — prose ADR.

**Approach:**
1. Check `docs/adr/README.md` tail — add ADR-0046 entry if missing.
2. Write `docs/adr/0047-experience-reviewer-as-work-loop-gate.md` following
   the repo ADR format.
3. Append ADR-0047 to `docs/adr/README.md` table.

**Depends on:** none

### Task 2: Update work-loop SKILL.md

**Verification mode:** Visual / manual QA

**Done when:** `packs/core/.apm/skills/work-loop/SKILL.md` contains:
(a) pre-EXECUTE design-intent pass bullet in PLAN section (both modes, advisory);
(b) experience-reviewer entry in specialist reviewer roster (REVIEW section) with
trigger, select-or-note fallback, and artifact/seed contract;
(c) experience-reviewer in end-of-session checklist reviewer-coverage line;
and the risk-triggers block is byte-unchanged (verified by grep of the block span).

**Tests:** `no stub (mode)` — prose skill; verified by reading the amended file.

**Approach:**
1. Edit `packs/core/.apm/skills/work-loop/SKILL.md`:
   - After the "Pre-EXECUTE secure-design review" bullet, insert a
     "Pre-EXECUTE design-intent pass (user-facing surface trigger)" bullet.
     The bullet must carry **no full-mode gate** — it is advisory in both modes
     (light mode reuses PLAN bullets verbatim; gating it to full-only would make
     Scenario C unverifiable).
   - After the `quality-engineer` specialist reviewer entry, add
     `experience-reviewer` entry with trigger, select-or-note fallback, and
     artifact/seed contract (rendered output + grounded reference + constraints).
   - Update the end-of-session checklist reviewer-coverage line to include
     `experience-reviewer on user-facing surface diffs (full mode)`.
2. Verify risk-triggers block unmodified via diff:
   `git diff packs/core/.apm/skills/work-loop/SKILL.md` should show no changes
   inside the `<!-- risk-triggers:start -->...<!-- risk-triggers:end -->` span.

**Depends on:** none

### Task 3: Bump core pack, run build-self, verify gates

**Verification mode:** Goal-based check

**Done when:** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
both read `0.8.0`; `make lint-packs` passes; `make build-self` completes without
error; `grep '"version"' marketplace.json` returns `"0.8.0"` for the core pack;
projected SKILL.md (`.claude/skills/work-loop/SKILL.md`) contains the new
experience-reviewer entry; risk-triggers block in all canonical copies is
byte-identical to the source.

**Tests:** `no stub (mode)` — build output and grep.

**Approach:**
1. Bump `[pack] version` in `packs/core/pack.toml` from `0.7.2` to `0.8.0`.
2. Bump `"version"` in `packs/core/.claude-plugin/plugin.json` from current
   to `0.8.0` (marketplace.json aggregates from plugin.json).
3. Run `make lint-packs`.
4. Run `make build-self`.
5. Verify risk-triggers block byte-equality via diff on the extracted span:
   extract the `<!-- risk-triggers:start -->...<!-- risk-triggers:end -->` block
   from each of the four canonical copies and diff them pairwise — any difference
   is a gate failure. `git diff` on the block region also works.

**Depends on:** Tasks 1 and 2

### Task 4: Update changelog and close backlog items

**Verification mode:** Goal-based check

**Done when:** `docs/product/changelog.md` has an `[Unreleased]` entry for the
experience-reviewer gate; backlog items `experience-reviewer-as-work-loop-gate`
and `experience-loop-trigger-for-site-changes` have shipped tombstones referencing
ADR-0047 and core 0.8.0.

**Tests:** `no stub (mode)` — grep.

**Approach:**
1. Add entry to `docs/product/changelog.md` `[Unreleased]` / `### Added`.
2. Add shipped tombstones to `docs/backlog.md` under both item headings.

**Depends on:** Tasks 1, 2, and 3
