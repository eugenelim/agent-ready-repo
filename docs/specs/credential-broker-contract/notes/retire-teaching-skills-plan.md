# Plan — retire the two credentialed-skill *teaching* primitives

**Date:** 2026-05-31 · **Branch:** `eugenelim/credentialed-skill-example-need`
· **Vehicle:** spec amendment + RFC-0013 § Errata (user-approved 2026-05-31)

## Why

RFC-0013 §9 mandated two teaching skills in `core` —
`add-credentialed-skill` (authoring procedure) and
`example-credentialed-skill` (runnable no-op reference). Review concluded
neither is structurally necessary:

- Enforcement is the **lint** (`tools/lint_credentialed_skills.py`) + the
  frontmatter schema — not the skills. The lint walks pack *source*
  (`packs/*/.apm/skills/*/SKILL.md`) and already covers the **real**
  credentialed skills (`credential-setup` in `credential-brokers`; `jira`,
  `jira-align`, `confluence-*`, `figma`). Deleting the fictional example
  loses **zero** lint coverage (verified: 8 skills scanned, 0 findings,
  example excluded).
- The authoring procedure duplicates the Diátaxis how-to
  (`docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md`) almost verbatim.
- The example only runs because `make build-self` commits a copy of the
  broker shim into `core`, coupling `core` to `credential-brokers`.

## Tasks (all goal-based verification — deletion + docs, no new logic)

> **Single PR.** All six tasks co-land in one PR. The spec amendment's
> present-tense ACs (AC27/AC43/line-94 say the how-to "carries the four
> blocks") and its five `RFC-0013 § Errata` pointers resolve only once T1
> and T3 land — so the spec edit must **not** merge ahead of the
> implementing tasks. Dependency order below.

- **T1 — Consolidate authoring guidance into the how-to.** *(Depends on: none)*
  Inline the four verbatim `### Security rules (non-negotiable)` blocks
  (creds / env / cli / sso-cookie) into the how-to's Step 7, replacing the
  "copy from `assets/`" indirection. Retarget **all six** dangling refs in
  `docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md` (review-confirmed):
  line 5 (runnable-reference link → a real consumer, `jira`), line 26
  (`assets/` link → the inline blocks), line 50 (frontmatter pointer →
  inline), line 151 (Step 7 "copy from `assets/`" → inline), lines 205-206
  (footer "Author skill" + "Worked example" links → the how-to is now
  self-contained; point "reference" at `jira`).
  *Done when:* how-to carries all four verbatim blocks; **zero** links to
  either deleted path (`grep -c` returns 0); `lint_credentialed_skills.py`
  still green.

- **T2 — Amend `credential-broker-contract/spec.md`.** *(Depends on: T1, T3 — the amended present-tense ACs assert the how-to carries the four blocks (T1) and point at RFC-0013 § Errata (T3); drafted in PLAN, reviewed pre-EXECUTE, but must not merge ahead of T1/T3)*
  - AC28: retarget canonical reference example → `jira`
    (`packs/atlassian/.apm/skills/jira/scripts/_client.py`, already a real
    `load_credentials` consumer); note example retired (see Changelog).
  - AC34: subject skill deleted; teaching surface is now the how-to.
    Separation-gate machinery is historical (already satisfied).
  - **AC27**: superseded — templates retired; four verbatim blocks → how-to.
  - **AC43**: drop the dead "lands in same PR as AC27" coupling clause.
  - **AC35**: range `AC28–AC33` → `AC29–AC33` (AC28 superseded).
  - Lines 23 / 94 / 95: "six in-tree consumers … + seventh site (teaching
    block)" → "five in-tree consumers"; drop the author-skill SKILL.md
    assertion (its test is deleted in T4).
  - **Boundary line 63** (`Never do`): re-anchor the "author runs
    `make build-self`, no auto-invoke" rail from the deleted skill → the
    how-to.
  - **Testing-Strategy "Why" column** (the authoring-guidance row, ~line 94
    after edits shifted it — grep by content, not line number): drop the
    `add-credentialed-skill author flow` clause.
  - **Manual-QA line 100**: retarget `add-credentialed-skill guide rewrite`
    → the how-to.
  - **Risks/Assumptions lines 222 + 229** + **AC42**: reconcile the "six + seventh
    site" / "six in-tree migrations" premise to historical-with-retirement-note.
  - Add a dated `## Changelog` erratum entry recording the retirement.
  *(Note: this spec uses prose `- **ACnn.**` ACs, not task-list checkboxes
  — a pre-existing deviation from CONVENTIONS § 4; the checkbox
  ship-transition invariant doesn't apply at `Status: Draft`.)*
  *Done when:* `lint-spec-status.py` green; spec reads coherently; **no AC,
  Boundary, Testing-Strategy row, or Risks line asserts a deleted
  artifact** (`grep` the whole spec for both skill names — every remaining
  hit is an explicit "retired/superseded" annotation).

- **T3 — RFC-0013 § Errata.** *(Depends on: none)*
  Append `## Errata` recording the §9 reversal, Approver-signed. Leave the
  §9 body intact (historical record). Mirror **RFC-0016 § Errata** (the
  sole `## Errata`-heading model; RFC-0011 uses inline-prose erratum, not a
  heading — do not follow it for format).
  *Done when:* erratum present + signed (Approver: eugenelim); §9 body
  unchanged.

- **T4 — Delete the skills + retire self-referential tests.** *(Depends on: T1 — the verbatim blocks must be inlined into the how-to before `assets/` is deleted)*
  - `rm -r packs/core/.apm/skills/{add-credentialed-skill,example-credentialed-skill}`
  - Delete `tests/integration/test_add_credentialed_skill.py` and
    `test_example_credentialed_skill.py` (both test only the deleted
    artifacts).
  - In `test_credential_user_scope_invocation.py`: drop the
    `core/.apm/skills/example-credentialed-skill/scripts → cli.py` param
    row (line ~145). The other six entry-points stay; the test already
    `pytest.skip`s absent rows, so this is hygiene.
  *Done when:* dirs gone; targeted pytest suite green.

- **T5 — Sweep active user-facing docs (instructions that point at deleted skills).** *(Depends on: T1 — active docs retarget to the consolidated how-to / real consumers)*
  In scope: `CONTRIBUTING.md`, `docs/architecture/credentials.md`,
  `docs/guides/credential-brokers/explanation/credentialed-skills.md`, **`README.md:169`**
  (skill-roster line for `add-credentialed-skill` — a now-false inventory
  entry, not seed-projected, needs a direct edit: remove the bullet),
  `packs/core/seeds/docs/CONVENTIONS.md` (seed → projects to
  `docs/CONVENTIONS.md`), and the stale fixture string in
  `tools/test-lint-skill-spec.py:364/556` (pair-edit to a surviving skill
  path). Retarget to the how-to / a real consumer. *(Note: the spec's
  `lint-credentialed-skills.sh` references are a back-compat shim to the
  `.py` — both are live; do NOT rewrite the spec's `.sh` mentions.)*
  **Out of scope (warn-only, other-spec/frozen — leave as historical):**
  `skill-secrets` (Shipped) spec/plan/notes, `pack-allowed-adapters`
  (Draft) spec/plan, RFC-0006, RFC-0011. Record a one-line `pack-allowed-adapters`
  deferred-cleanup pointer in `docs/backlog.md`.
  *Done when:* no *active* doc instructs the reader to use a deleted skill;
  `lint-agent-artifacts.py` + `lint-spec-status.py` green.

- **T6 — Re-project + gate.** *(Depends on: T1, T2, T3, T4, T5)* `make build-self`, then `make build-check`.
  *Done when:* build-check green; `.claude/skills/` no longer carries the
  two skills (`marketplace.json` aggregates packs by description, not
  per-skill — it never listed them, so nothing changes there); `git
  status` clean.

## Verification (GATES)

```
python3 tools/lint_credentialed_skills.py .
python3 tools/lint-agent-artifacts.py
python3 .claude/skills/work-loop/scripts/lint-spec-status.py
python3 -m pytest packages/agentbundle/tests/integration/test_credential_user_scope_invocation.py
make build-check
```

## AC28 retarget rationale

`jira` over `credential-setup`: `credential-setup` is a credential *writer*
(its `setup.py` does not import the `load_credentials` triple), so it's a
poor exemplar of the consumer import line AC28 pins. `jira`'s
`_client.py:652` is a real `from .credentials_shim import (CredentialsMissingError,
Tier2HardFailError, load_credentials)` consumer — the strongest standing
reference. Lint coverage (the user's point) is satisfied by *all* real
credentialed skills regardless of AC28's exemplar pick.
