# Spec: stale-reference-corrections

- **Status:** Shipped (AC4's register anchor `semgrep-mcp-cve-allowlist` was
  closed on 2026-08-25 when its recorded unblock condition arrived and the four
  `--ignore-vuln` suppressions were removed from the `sast` target; the entry is
  gone from `workspace.toml [backlog].open`, and the Makefile citation AC4
  repointed went with the suppressions it annotated. Not a supersession — every
  decision here stands, and AC4's repointing was correct for as long as the
  suppressions existed.)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — every change is a comment or a prose sentence. No
  executable behavior, no gate outcome, and no public interface moves.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. Two conditional triggers were
checked and did NOT fire. (1) Security boundary: the Makefile edit is the COMMENT
above the `--ignore-vuln` block, not the block — the four suppressed CVE ids, the
manifest, and the invocation are byte-identical after this change. (2) Governance
boundary: `[backlog].open` is a display projection the dispatch classifiers never
read (`workspace_status_engine.py` `extract_repo_backlog`), and no `(deferred: <slug>)`
anchor in any spec resolves against the five slugs removed here — verified by grep.
Lean fill: Objective + Acceptance Criteria + Boundaries + Assumptions. -->

## Objective

Five `[backlog].open` entries record the same defect class: a comment or a
documented claim that was true when written and is false now. Each entry's own
`Fix:` line is fully determined — none needs a decision, a measurement, or an
environment — and each says in so many words that it was left out of its parent
PR because it fell outside that PR's touched area, not because it was hard.

They are corrected together because a reader who trusts any one of them is
misled in the same way, and because a single-item PR for a one-line comment
costs more review attention than the correction is worth.

Success: every corrected claim is verifiable by a command recorded beside it in
this spec, and the five entries leave `[backlog].open`.

## Acceptance Criteria

- [x] **AC1 — `build-check.yml`'s credential-setup comment block sits above the
  step it documents.** The five-line block that opens "The credential-setup
  skill's own suite (RFC-0023 T8 + the missing-credbroker guard)" moves from
  above `pytest guides + catalogue navigation` to immediately above
  `pytest credential-setup skill (RFC-0023 T8 + missing-credbroker guard)`.

  Evidence of the defect: the block's own subject line names the
  `credential-setup` step, and four unrelated steps
  (`pytest guides + catalogue navigation`, `pytest site build + link rewriting`,
  `docs palette contrast gate`, `pages.yml deploy-gate posture`) sit between the
  two. A reader takes a leading comment as describing the step that follows it.

  Verification: `python3 tools/test-build-check-workflow.py` and
  `python3 tools/lint-ci-parity.py` both stay green — the block is a comment, so
  no assertion family, no `PINNED_JOB_STATEMENTS` entry, and no parity roster
  entry reads it. No step name, `run:` body, `working-directory:`, or step order
  changes.

- [x] **AC2 — `web/src/design-system.md` stops claiming the docs CSS imports
  `tokens.css`.** Both passages are corrected: § 6 Dark mode and § 8 Starlight
  CSS audit.

  Evidence of the defect: `docs-site/src/styles/starlight.css` says so itself at
  its compatibility-layer header — "tokens.css is no longer imported; these
  definitions re-derive exactly the consumed names onto the doc palette" — and
  the file contains zero `@import`. The docs palette is self-contained per
  ADR-0085; `--ds-*` names survive only as a re-derivation for the shared
  primitive components.

  In the same § 6 passage, and corrected with it because they are the same
  claim about the same mechanism, not a second subject: the section says dark
  mode is applied "via `[data-theme='dark']`", and its resolved-value table
  cites `--prim-dark-950` → `#0b0e12`, `--prim-dark-900` → `#111520`,
  `--ds-accent` → `#e8952b`, `--prim-amber-300` → `#f5bc6a`. Measured: the docs
  sheet carries **no** `[data-theme='dark']` selector and **no** `--prim-*`
  token, and none of those four hex values appears anywhere under
  `docs-site/src/styles/`. The surface is dark-**first** — `:root` is the dark
  theme and `:root[data-theme='light']` overrides it — so the stated direction
  is inverted as well as the values being wrong.

  Also in § 8, and corrected with it for the same reason: its known-deviations
  table asserted two raw `#ffffff` literals against a "Closest `--ds-*` token"
  of `--ds-hero-fg`. Measured: `--ds-hero-fg` does not exist in `starlight.css`
  at all, so the comparison column named a token the sheet does not carry; and
  the `.site-footer__brand { color }` row is simply resolved — that rule now
  reads `color: var(--doc-heading)`. One deviation survives
  (`--sl-color-text-invert`'s light-theme assignment, `starlight.css:124`) and
  the table is narrowed to it.

  Verification: `grep -c '@import' docs-site/src/styles/starlight.css` returns
  `0`; `grep -c -- '--prim-' docs-site/src/styles/starlight.css` returns `0`;
  `grep -c "data-theme='dark'" docs-site/src/styles/starlight.css` returns `0`;
  `grep -n -- '--ds-hero-fg' docs-site/src/styles/starlight.css` returns
  nothing; every token/hex pair in both corrected tables resolves in
  `starlight.css`. The four `--prim-*` hexes that remain in `design-system.md`
  are § 1's `web/` primitive table and are correct against
  `web/src/styles/tokens.css` — they were never the defect.

- [x] **AC3 — `lint-build.py`'s `docs-site` entry is attributed to the RFC that
  authorises it.** The trailing comment on the `"docs-site"` member of
  `RFC_AUTHORISED_DIRS` cites RFC-0089 rather than ADR-0055.

  Evidence of the defect: the tuple's own header (`tools/lint-build.py:31-32`)
  reads "Top-level directories explicitly authorised by an Accepted RFC. Add
  entries only when an Accepted RFC authorises the new directory." ADR-0055 is
  an ADR. `docs/rfc/0089-starlight-docs-boundary.md` is Accepted, is titled
  "Starlight docs boundary", and its decision weight names ratifying the
  permanent top-level project as its subject.

  Verification: `python3 tools/lint-build.py` stays green; the tuple's
  membership is unchanged (comment only).

- [x] **AC4 — the semgrep suppression's recorded expiry resolves, and the SCA
  gap it points at names every uncovered file.** Two edits:

  1. `Makefile` — the comment above the four `--ignore-vuln` flags cites
     "docs/backlog.md § semgrep-mcp-cve-allowlist" as the diagnosis and unblock
     condition. `docs/backlog.md` is an anchor tombstone whose own header says
     "All open work has migrated to `workspace.toml [backlog].open`", and it
     carries no semgrep section — `grep -i semgrep docs/backlog.md` returns
     nothing. The citation is repointed at `workspace.toml [backlog].open`.
     This was the suppressions' only recorded expiry.
  2. `workspace.toml` — `sast-requirements-not-audited` names only
     `tools/requirements-sast.txt` and `tools/requirements-ci-security-locked.txt`.
     `tools/requirements-evals-locked.txt` exists, is equally unaudited, and
     falls outside every other entry. Its comment and `summary` are widened to
     name it.

  The suppression itself does not lift: measured this session, semgrep 1.166.0
  still requires `mcp==1.23.3` and `click~=8.1.8`, so the unblock condition the
  comment states is unmet and all four `--ignore-vuln` flags stay.

  Verification: `grep -n "docs/backlog.md" Makefile` returns nothing;
  `make sast`'s pip-audit leg still passes the same four suppressions; the four
  CVE ids are byte-identical in the diff.

- [ ] (deferred: packs-agents-normative-pointer) **AC5 — `packs/` names its machine source of truth.** Attempted and reverted; the entry's premise does not survive the repository's own contract.

  The gap is real: `grep -n "pack.schema.json" packs/AGENTS.md packs/README.md`
  returns nothing, while `profiles/AGENTS.md:18` names
  `contracts/profile.schema.json`.

  Why the edit was reverted. Both files are projected into the authoring
  scaffold (`tools/catalogue/sync_authoring_scaffold.py` `_SYNC_PAIRS`), and that
  scaffold is what `catalogue init` writes into an adopter's catalogue root. The
  scaffold ships `guides/ packs/ profiles/ tests/` and **no `contracts/`
  directory**, so the pointer is true here and false in every adopter's tree.
  `test_scaffold_projection.py::test_packs_agents_md_cites_only_paths_it_ships`
  exists precisely to catch that and did — measured: the edit reddens `make ci`
  on arrival with "State the rule without the citation, or ship the file." The
  current path-free wording is deliberate, not an oversight.

  `packs/README.md` carries no equivalent assertion, so the same pointer lands
  green there — and is equally false for the adopter. It was reverted too rather
  than shipped on the strength of an absent test.

  Second instance, found the same way and the reason the entry's premise
  inverts: `profiles/AGENTS.md` already carries the dangling form, and
  `test_scaffold_projection.py` asserts only that it exists and is non-empty. The
  file the entry named as the precedent to mirror is a second occurrence of the
  same defect.

  Closing it needs a decision — ship the schemas in the scaffold, keep the
  wording path-free and close the entry as won't-fix, or build a repo-only
  projection carve-out that `_SYNC_PAIRS` byte-identity does not offer. The
  rewritten `[backlog].open` entry carries all three options and the
  recommendation.

- [x] **AC6 — four entries leave `[backlog].open`; the fifth is rewritten.**
  `packs-agents-normative-pointer` stays open, its comment replaced with what
  AC5 measured, so the next author does not repeat the attempt. The other four
  are deleted, not
  moved to `[backlog].closed`: that collection admits only `kind = "defect"`
  backed by a real artifact carrying `Status: Closed`, and fabricating one is
  what this repository's own remediation forbids. Deletion is the established
  practice — `[backlog].closed` has stayed empty across the project's history.

  No `(deferred: <slug>)` anchor resolves against any of the five (verified by
  `grep -rn "deferred: <slug>" docs/`), so `lint-spec-status.py` invariant (iv)
  is unaffected. The two prose mentions in
  `docs/specs/pip-audit-batching/spec.md` (Archived) are registered-deferral
  narrative, not anchors, and are left alone — it is a frozen record and its
  account of what was deferred at the time stays true.

  Verification: `workspace-status status --root .` exits 0 and reports four
  fewer open entries than the base ref. Deliberately stated as a delta, not an
  absolute: `[backlog].open` grows on other branches, and this spec was rebased
  once onto four intervening merges that added entries of their own.

## Boundaries

**Never do**

- Lift the four `--ignore-vuln` suppressions. Their stated condition is unmet
  (semgrep 1.166.0 still pins `mcp==1.23.3`), so removing them would redden
  `make sast` on arrival.
- Re-attribute the `contracts` or `guides` members of `RFC_AUTHORISED_DIRS`.
  Both cite ADR-0055 and neither has an authorising RFC to point at; inventing
  one is the fabrication AC6 refuses elsewhere.
- Edit `docs/specs/pip-audit-batching/spec.md` or any other frozen spec body.
- Change a step name, `run:` body, `working-directory:`, or step order in
  `build-check.yml`.
- Touch `[work]`, `[shaping_queue]`, `[brief_queue]`, or initiative membership
  in `workspace.toml`.

## Assumptions

1. `docs/backlog.md` remains a tombstone. Confirmed by its own header; AC4
   repoints away from it rather than adding a section to it.
2. `contracts/pack.schema.json` and the wheel's `_data/` copy stay identical.
   Confirmed byte-identical this session; AC5 names the repo-root path because
   that is the one an author edits.
3. Comments in `build-check.yml` are not asserted by the posture test. Confirmed
   by reading `PINNED_JOB_STATEMENTS` and `_NO_CWD_STEPS`, and re-confirmed by
   running the suite after the move (AC1).
