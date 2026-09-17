# Spec: conventions-retirement

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — see Assumptions for the waived RFC gate
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`docs/CONVENTIONS.md` does not exist, and neither does its seed at
`packs/core/seeds/docs/CONVENTIONS.md`.

Every obligation those files carried lives with the artifact that owns its
surface. The rules an agent needs to orient at session start — the commit
format, the pull-request questions, and the privacy rule — live in `AGENTS.md`,
which is the only conventions document an agent loads. Adopters installing the
`core` pack receive those rules in `packs/core/seeds/AGENTS.md`.

No actionable source names the retired path, and every anchor that addressed it
resolves in the destination recorded in
[`notes/anchor-map.txt`](notes/anchor-map.txt).

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Current architecture | `docs/architecture/pack-layout.md`, `docs/architecture/README.md`, `docs/product/README.md` | maintainer | Relocated sections present under their own headings | AC6 anchors resolve |
| Adopter entry point | `docs/README.md`, seeded | maintainer | Hierarchy and lifecycle classes stated where a reader enters `docs/` | AC15, AC16 |
| Maintainer procedure | `guides/core/`, `guides/governance-extras/` | maintainer | Relocated prose sits in the destination's Diátaxis genre | AC6 anchors resolve |
| Interface compatibility | `packs/core/seeds/AGENTS.md`, root `AGENTS.md` | maintainer | The three session-priming rules present | AC4, AC5 |
| Decision rationale | `.claude/skills/new-spec/`, `.claude/skills/work-loop/` | maintainer | §4 subsections and the §5c completion gate re-homed | AC2 |
| Release history | `docs/product/changelog.md` | maintainer | `core` entry naming the seed withdrawal | AC11 |

## Boundaries

### Always do

- Edit the source, never a projection. `packs/<pack>/.apm/` is the upstream for
  `.claude/`, `.agents/` and `.codex/`; `packs/*/JOURNEY.md` is the upstream for
  `web/src/content/journeys/`. Run `make build-self` to regenerate rather than
  hand-editing a projected copy.
- Keep the two file pairs consistent, each under its own relation:
  `docs/CONVENTIONS.md` and `packs/core/seeds/docs/CONVENTIONS.md` are
  byte-identical until both are deleted, asserted at
  `tests/roster/test_shaping_review_documentation_contract.py:53`; root
  `AGENTS.md` and `packs/core/seeds/AGENTS.md` are distinct files under
  different caps that must carry the same three session-priming rules, not the
  same bytes.
- Re-point a section's full consumer set in the same task that removes that
  section's heading, so the tree holds no dangling anchor between tasks.
- Re-point a test that names the retired path at the new owner, and record it
  failing against an owner with the relocated content removed.
- Prove a relocation preserved something. Every moved section carries at least one
  assertion that named operative content from it resolves in the destination.
  Which tokens is an execution-time choice; that an assertion exists is not,
  because an empty-discovery check alone passes when the section is deleted.

### Ask first

- Deleting any section not named in the plan's re-homing map.
- Raising a cap in `tools/lint-agents-md.py` beyond the increment the relocated
  rules need.
- Changing what `agentbundle install` does to an adopter's existing on-disk copy.

### Never do

- **Structural:** add a new top-level directory, a new module boundary, or a new
  dependency. Every destination exists today.
- Introduce a generated `REPO_MAP.md` or any new projection.
- Edit a historical record to repair a reference. The predicate is: a spec, plan,
  note or adjudication under `docs/specs/<feature>/`; a record under `docs/rfc/`,
  `docs/adr/`, `docs/product/<record>/`, `docs/product/changelog.md`,
  `docs/knowledge/observations/` or
  `docs/knowledge/topics/`; a package `CHANGELOG.md`; or a file under a
  `work-loop` fixture corpus. A directory index such as `docs/specs/README.md` or
  `docs/product/README.md` is not a historical record and is repaired normally. The 2026-09-14 members are
  listed in [`notes/consumer-inventory.txt`](notes/consumer-inventory.txt).
- Delete a test rather than re-point it, or let a control survive as a negative
  assertion over a source that no longer exists.

## Testing Strategy

| Objective outcome | Mode | Why |
| --- | --- | --- |
| Both files absent | Goal-based check | A path either exists or it does not. |
| No actionable source names the retired path | TDD | One recorded script is the predicate, so the check and its prose cannot drift. |
| The projection allow-list is empty | TDD | A tuple's contents are compressible, and a test already pins its size. |
| The three priming rules present in both `AGENTS.md` files | TDD | Presence of named tokens is checkable without judgement. |
| Every recorded anchor use has a resolving replacement | TDD | A closed recorded set compared against a mapping is a set predicate that survives the work landing. |
| Every relocated section left operative content behind | TDD | Otherwise deletion and relocation are indistinguishable to the gate. |
| Links this change adds stay inside the installed scaffold | TDD | The installed path list compared against the links this change touches. |
| The new `docs/README.md` ships | Goal-based check | A path either appears in the install snapshot or it does not. |
| The relocated credential contract still reds on removal | TDD | A re-pointed assertion proves nothing until shown failing. |
| The scaffold's relative links resolve | TDD | The existing check already carries this shape. |
| The changelog entry names the withdrawal | TDD | A body-reading assertion, not a heading check. |
| Both manifests carry the bumped version | TDD | Two file reads and an equality. |
| § Scaling profiles survives in its destination | TDD | Operative content pinned in `CONTRIBUTING.md`, not inferred from the move. |
| Relocated prose sits in its destination's genre | Visual / manual QA | Diátaxis genre fit is a judgement no assertion makes. Advisory: no completion gate reads it. |

## Acceptance Criteria

- [ ] AC1 — `docs/CONVENTIONS.md` and `packs/core/seeds/docs/CONVENTIONS.md` are
  absent from the working tree.
- [ ] AC2 — Every file recorded in
  [`notes/consumer-inventory.txt`](notes/consumer-inventory.txt) no longer cites
  the conventions document. The check ranges over that fixed baseline, because
  `notes/ac2-scan.sh` is an editable file and a criterion reading only its live
  output is discharged by widening one exclusion.
- [ ] AC2b — `sh notes/ac2-scan.sh` returns no file outside the AC2 baseline, so a
  consumer introduced during the work is not left behind.
- [ ] AC2c — A canary asserts the live `notes/ac2-scan.sh` matches the approved
  form recorded outside it, by digest. Checking only that named exclusion classes
  still exclude is blind to a class added later: one extra pathspec shrinks every
  task's discovery domain with the canary green. Pinning the form satisfies this
  without restating the pathspecs anywhere.
- [ ] AC3 — `PROJECTED_README_OVERRIDES` in
  `packages/agentbundle/agentbundle/build/self_host.py` is the empty tuple.
- [ ] AC4 — `packs/core/seeds/AGENTS.md` states the Conventional Commits type
  list, the four pull-request questions, and the privacy rule.
- [ ] AC5 — Root `AGENTS.md` states those same three rules.
- [ ] AC6 — Every one of the 30 anchor uses recorded in
  [`notes/anchor-inventory.txt`](notes/anchor-inventory.txt) has a replacement link
  that resolves to an existing heading in the file its anchor is mapped to in
  [`notes/anchor-map.txt`](notes/anchor-map.txt). The check opens each recorded
  consumer, because a destination that exists proves the content landed and not
  that the consumer was re-pointed at it, and the link must carry the mapped
  heading's fragment, because comparing paths alone passes on any bare link the
  consumer already holds. A use that cannot carry such a link
  resolves through a recorded disposition instead, and the record says which:
  the content landed in the citing file itself; the consumer is not Markdown
  and its pointer is pinned as the exact spelling its reader resolves; or the
  guidance is not adopter-facing and the note is deleted. The check ranges
  over the recorded pre-relocation uses, because the live set empties as the work
  lands and a criterion over an empty set cannot fail.
- [ ] AC6b — `sh notes/ac2-scan.sh 'CONVENTIONS\.md#'` returns no file, so no live
  anchor still addresses the retired path.
- [ ] AC7 — `tests/roster/test_credential_broker_contract_docs.py` asserts the
  four broker ids and `metadata.auth` against
  `guides/credential-brokers/how-to/add-a-credentialed-skill.md`.
- [ ] AC8 — That assertion fails when the broker list is stripped from
  `guides/credential-brokers/how-to/add-a-credentialed-skill.md`.
- [ ] AC9 — `tests/roster/test_tdd_stub_lifecycle_contract.py` asserts every
  member of its `live_sources` tuple exists before reading it.
- [ ] AC10 — `tests/roster/test_install_snapshot.py` checks that the relative
  links **this change adds or edits** resolve across the Markdown the core scaffold
  produces, rather than reading one named seed file. Narrowed on the same ground as
  AC14 and against the same backlog entry.
- [ ] AC11 — `docs/product/changelog.md` carries a **new** free-standing `core`
  entry, topmost among the `core` sections, whose body names the seed
  withdrawal. Appending a sentence to an already-released entry does not
  satisfy this.
- [ ] AC12 — `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both carry `2.27.0`, and the criterion names that value rather than an
  ordering: a patch bump satisfies any looser comparison, and the only machine
  check is that the two files agree with each other
  (`catalogue_tooling/lint.py:1748`). The released baseline moved while this
  change was in flight — core shipped several patches on `main` — which is why
  the target is pinned to a value and not expressed relative to a predecessor.
- [ ] AC13 — `CONTRIBUTING.md` states the scaling-profile names and their
  contributor ranges.
- [ ] AC14 — No link **this change adds or edits** in a file under
  `packs/core/seeds/` points outside the installed paths listed in
  `tests/fixtures/install_snapshot/core.paths.txt`. Narrowed to the links this
  retirement touches: the seed tree already carries out-of-scaffold links to
  `adr/`, `rfc/`, `guides/`, `GOVERNANCE.md`, `personas.md` and
  `release-checklist.md` that predate this change and are logged as
  `core-seeds-mandate-other-packs-content` in `[backlog].open`.
- [ ] AC15 — `packs/core/seeds/docs/README.md` exists and states the document
  hierarchy and the living / frozen / governance lifecycle classes.
- [ ] AC17 — `packs/core/seeds/AGENTS.md` carries a `## Documentation` section
  routing to `docs/README.md`. Its only reference to anything under `docs/` today
  is the pointer to the retired file, so without this an adopter's root
  `AGENTS.md` names no entry into the doc tree.
- [ ] AC20 — That `## Documentation` table names no path absent from
  `tests/fixtures/install_snapshot/core.paths.txt`. The repo's own table lists
  `docs/adr/`, `docs/rfc/`, `guides/` and `ARCHITECTURE.md`, none of which core
  installs, so copying it verbatim would ship the dangling references this change
  exists to remove. Its universal rows — a repeating agent workflow lives in its
  own `SKILL.md`, and a mechanically knowable fact lives in code, schema,
  manifest, test or linter — carry over unchanged.
- [ ] AC21 — `packs/core/seeds/AGENTS.md` states, under § Development workflow,
  that changes are scoped precisely with assumptions and conflicts surfaced before
  building, that destructive or irreversible operations need confirmation, that a
  new top-level directory goes through the repository decision process, and that
  unrelated discoveries stay out of the current change.
- [ ] AC22 — `packs/core/seeds/AGENTS.md` states, under § Coding conventions, that
  changed code gets types and docstrings with crossed boundaries validated, that a
  new dependency is recorded in the owning package instructions or an ADR before
  it is added, and that a conflict between documented guidance and code is never
  silently resolved — the evidence and trade-off are stated and the owning source
  updated rather than a generated projection.
- [ ] AC23 — `packs/core/seeds/AGENTS.md` states that credentials and personal
  information are never committed, with generic placeholders used in repository
  artifacts, and that stale or conflicting instructions are reported rather than
  worked around.
- [ ] AC24 — The recommended-additional-guidance comment in
  `packs/core/seeds/AGENTS.md` no longer offers `Documentation`,
  `Security considerations` or `Scoped instructions`, because this change promotes
  all three into the file; `Repository structure` remains offered.
- [ ] AC18 — Seeded `docs/README.md` names every docs area core seeds, with what
  belongs there and its lifecycle class, and carries a placeholder row an adopter
  extends when a pack adds an area core does not seed.
- [ ] AC19 — `_SEEDS_REQUIRED_PLACEHOLDERS` in
  `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` declares
  `docs/README.md`, and the catalogue seed lint accepts it. A seed with no declared
  shape is rejected as unknown, fail-loud.
- [ ] AC16 — `docs/README.md` appears in
  `tests/fixtures/install_snapshot/core.paths.txt`, and the install snapshot suite
  passes with it present.

## Follow-ons

- None.

## Assumptions

- Technical: the actionable consumer set is whatever `sh notes/ac2-scan.sh`
  returns; `notes/consumer-inventory.txt` records its 2026-09-14 output as a
  baseline. Some sources cite the document by section without the `.md` suffix,
  including `packs/core/.apm/skills/new-spec/assets/spec.md`, the template every
  future spec inherits, so the pattern deliberately omits the suffix.
- Technical: the anchor uses are enumerated in
  [`notes/anchor-inventory.txt`](notes/anchor-inventory.txt) and mapped to their
  destinations in [`notes/anchor-map.txt`](notes/anchor-map.txt), each with the
  command that regenerates it.
- Technical: before this change, `docs/CONVENTIONS.md` was the sole entry in
  `PROJECTED_README_OVERRIDES`. AC3 empties the tuple, so the live value is
  what `self_host.py` defines, not what this dated assumption records.
- Technical: `_classify_seeds` walks only what exists under `seeds_dir`
  (`packages/agentbundle/agentbundle/commands/_common.py:138-167`), and seeds
  land outside the adapter projection prefixes so they never interact with the
  orphan scan (`install.py:1678-1683`). A withdrawn seed leaves an adopter's
  existing file in place.
- Technical: both `packs/core/seeds/AGENTS.md` and root `AGENTS.md` pass the
  line caps `tools/lint-agents-md.py` enforces, and the seed cap was raised to
  admit the rules this change moves into it. The linter is the statement of
  what fits; recording the measurements here dated them within the same
  change, which is why they are absent.
- Technical: the credentialed-skill authoring contract already has an owner.
  `guides/credential-brokers/how-to/add-a-credentialed-skill.md:32-37` states
  `metadata.auth` and all four broker ids and `:43` the argv ban, and
  `guides/_shared/how-to/author-a-skill.md:18` routes authors there. § Credentialed
  skills lands in that how-to, per the plan's rule that each destination is the
  artifact already cited as that surface's owner. An earlier draft named
  `packages/credbroker/README.md` and claimed `security-checklists` cited it; no
  file in the tree cites that path except `packages/agentbundle/README.md:301`, so
  the claim was false (owner decision 2026-09-15).
- Process: a core pack release needs a matching version bump and a free-standing
  changelog entry (`packs/AGENTS.local.md:28-30`).
- Process: the release is a minor bump to `2.27.0`, not a major. `packs/AGENTS.md`
  § Version bump rule gives minor for new primitives and major for removals, and
  this change is both: it adds `docs/README.md` as a new seed and withdraws
  `docs/CONVENTIONS.md`. The owner decided minor on 2026-09-15, on the ground that
  the withdrawal takes no capability from anyone — `_classify_seeds`
  (`packages/agentbundle/agentbundle/commands/_common.py:138-167`) leaves an
  existing adopter's copy in place, and the content is re-homed into files every
  adopter already receives. A major bump would also put core outside the `^2.0`
  range that `governance-extras`, `iac-terraform`, `monorepo-extras` and
  `release-engineering` declare, forcing four unrelated packs to move
  (user confirmation 2026-09-15).
- Process: § 3 of the retired file made an RFC mandatory for a deprecation. The
  owner waived that gate (user confirmation 2026-09-14).
- Product: adopters receive the session-priming rules through
  `packs/core/seeds/AGENTS.md` rather than a separate seeded conventions file
  (user confirmation 2026-09-14).
- Product: the owner accepted the measured scope after it replaced a much smaller
  early estimate (user confirmation 2026-09-14).
- Product: pack-layout guidance is not adopter-facing. An adopter scaffold installs
  no `packs/` directory (`tests/fixtures/install_snapshot/core.paths.txt`), so the
  seeded note about the
  pack source-of-truth split is deleted rather than re-pointed; it described
  authoring this catalogue, not using it (user confirmation 2026-09-14).
