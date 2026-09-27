# Verification ledger — xd-genre-router

This file records judgement-based evidence that the mechanical gates cannot
settle. The approved `spec.md` and `plan.md` hold the obligations.

## Manual-QA judgements

| # | Judgement | Artifact read | Verdict | Reviewer | Date |
| --- | --- | --- | --- | --- | --- |
| 1 | Each genre reference carries its source skill's method, grounding citations, and scope boundaries | `information-architecture/references/analytical-design.md`, `conversion-design.md`, `documentation-design.md`, `informational-design.md`, `marketplace-design.md`, and `workspace-design.md`, checked against their source `SKILL.md` files before T4 deletion | **Pass.** Each reference preserves the source method sections rather than reducing them to a summary: invocation checks, structural method, grounding reference tier, handoff or boundary rules, and anti-patterns are present. Cross-genre boundaries were rewritten as sibling reference citations where needed so the folded skill does not route to removed registrations, without dropping the boundary itself. `conversion-design.md` still loads `references/editorial-quality-gates.md`, and the shared editorial file is present for that citation. | Codex implementer | 2026-09-26 |
| 2 | The genre-selection rubric is decidable from the brief's `surface-genre:` field alone | `packs/experience-design/.apm/skills/information-architecture/SKILL.md` | **Pass.** The procedure says to select exactly one route when the per-screen brief declares `surface-genre:`, and the rubric maps the seven allowed values directly: six values route to genre references inside `information-architecture`, and `transactional-journey` routes to `interaction-design`. No additional project fact, content type, or judgement gate is needed to choose the row. | Codex implementer | 2026-09-26 |
| 3 | The experience-design guide routes by genre through one skill, and its `Where it lands` paths agree with the surviving `SKILL.md` | `guides/experience-design/reference/experience-design.md`, `guides/experience-design/how-to/design-each-screen.md`, and `packs/experience-design/.apm/skills/information-architecture/SKILL.md` | **Pass.** The guide tells readers to declare the genre in `surface-genre:` and says `information-architecture` applies the matching method for marketing, documentation, analytical, informational, marketplace, workspace, or general IA surfaces. The screen guide's `Where it lands` path is `<output_dir>/screens/<slug>-ia.md`, matching the surviving skill's `Writes:` target and Step 8 output path. | Codex implementer | 2026-09-26 |

## T11 closeout confirmations

- **Final review and shipment authorization:** Codex completed a local final
  diff review on 2026-09-26 without external model or subagent calls. It found
  and corrected two stale routes in live Draft intents, then corrected the
  classification and current-state handling of two notes owned by an
  `Implementing` sibling delivery. A second removed-name sweep found only the
  two documented source exemptions plus historical or contract-owned records.
  The repository owner then explicitly directed that this spec be marked
  Shipped. That authorization accepts the named managed-filesystem skips below
  as local-environment limits while leaving their supported-profile/CI checks
  visible rather than weakening the commands or tests.

- **Install/update observation:** One bounded local fixture observation ran on
  2026-09-26 against temp root
  `/private/tmp/xd-genre-router-t11.2aqTG3`. The intended old fixture carried
  the six retired skill directory names, then attempted repo-scope
  `agentbundle install` followed by `agentbundle upgrade` from the current
  fold branch. The install did not reach a valid installed state: fixture setup
  printed six `Can't open .../<retired-skill>/SKILL.md` lines because the copied
  source landed as nested `information-architecture/` directories, and the
  initial install then hit the managed cleanup limit before state was written.
  Python `tempfile` cleanup failed with `PermissionError: [Errno 1] Operation
  not permitted` while calling `os.rmdir` on
  `/var/folders/c9/x1zrm_1s55d4q6vrvwx9rsnw0000gn/T/tmpjoc8tp7_/.claude/skills/documentation-design/information-architecture/references`.
  The observed exit codes were `INSTALL_RC=1`, `UPGRADE_RC=1`, and
  `INSPECT_RC=0`; the follow-on upgrade reported that `experience-design` was
  not installed for adapter `claude-code`, the adopter had no
  `.agentbundle-state.toml`, no `information-architecture` install, and no
  stale retired-skill directories to inspect. That invalid fixture therefore
  did not establish prune or non-prune behaviour and was not retried under the
  managed environment's cleanup restriction.

  Read-only inspection of the exact whole-pack update path settles the result:
  `agentbundle.commands.upgrade._apply_single_row` walks only the new
  projection, writes those paths, and adds or replaces their `pack_state.files`
  records. It has no old-minus-new removal pass. The only removal in that path
  reconciles user-scope hook-wiring rows. By contrast, the separate direct-skill
  update contract explicitly plans and removes obsolete files in
  `test_direct_skill_upgrade_plans_writes_and_removals_without_catalogue`,
  including pruning the empty parent directory. The current whole-pack update
  therefore leaves a skill directory resident when the new pack no longer
  declares it. The `experience-design` 3.0.0 changelog entry now tells existing
  adopters to remove all six retired skill directories after upgrade so their
  stale `SKILL.md` registrations cannot remain active.

- **Frontend handoff zero-occurrence check:** The frontend handoff guide carries
  no routing target, genre-skill name, `experience-design`, or the word
  `genre`. The confirmation command was
  `rg -n "conversion-design\|documentation-design\|analytical-design\|informational-design\|marketplace-design\|workspace-design\|information-architecture\|experience-design\|genre" guides/frontend-engineering/how-to/read-the-design-handoff.md`,
  which returned zero matches on 2026-09-26.

- **`DESIGN.md` § 10 sole-editor citation:** This slice is the sole editor of
  the `packs/experience-design/DESIGN.md` § 10 genre-skill rationale. The
  sibling `docs/specs/creative-direction-modes/spec.md` compatibility criterion
  states that `packs/experience-design/DESIGN.md` § 10 is not edited by that
  delivery; its reason is that `xd-genre-router` authors the amendment once the
  six genre skills stop existing.

- **Genre eval sets:** No genre quality-eval set was knowingly dropped. All six
  retired genre eval sets were carried into the surviving
  `information-architecture` eval surface, so no `GENRE-EVALS-DROPPED:` marker
  is owed.

## Environmental skips

- The literal recursive removed-name grep also saw ignored local bytecode at
  `tools/__pycache__/add-rendering-directives.cpython-313.pyc`. It is not a
  repository artifact and was preserved as existing ignored workspace state.
  The source-tree sweep with `__pycache__` excluded returned no non-exempt hit.

- T10a's unforced `make build-self` correctly refused the dirty implementation
  worktree. The documented `FORCE=1` path was attempted once and reached the
  managed environment's denied `os.rmdir` path while replacing
  `.claude/skills/assimilate-primitive/scripts`; it was not retried. Four
  partially removed tracked files were restored byte-for-byte from `HEAD` with
  `apply_patch`. The same self-host implementation's narrow
  `_aggregate_marketplace` generator then regenerated only
  `.claude-plugin/marketplace.json`. The one local catalogue-verification run
  reached its assertions but failed while `TemporaryDirectory` cleaned
  `/var/folders/c9/x1zrm_1s55d4q6vrvwx9rsnw0000gn/T/tmpobwiextf`: Python
  `os.rmdir` returned `EPERM`. It was not retried; catalogue verification is
  left to CI or a supported profile.
  Root deep catalogue lint likewise reported exactly six errors, all
  `CAT-L010` findings for the six empty local directory shells recorded below;
  the `frontend-engineering` pack-scoped deep lint passed with its existing
  advisory body-length warning.

- The T7 Astro gate completed `npm ci`, then `npm run build` reached Vite and
  failed with `EPERM` while renaming
  `web/node_modules/.vite/deps_temp_891e61cf` to
  `web/node_modules/.vite/deps`. This is a generated-cache rename in the
  managed workspace, not a schema or content rejection. The build was not
  retried and remains for CI or a supported filesystem profile; the separate
  `python3 tools/build-site.py` projection passed.

- `tools/lint-guidebook-steps.py` remains a documented sweep exemption. Its
  only retired-name hit is the explanatory comment `# "analytical-design
  SKILL.md", which names a file without locating it.` The comment names a file
  without referencing the skill, so T7a records the exemption here instead of
  rewriting an unrelated tool to silence the completeness check.

- `packs/experience-design/.apm/skills/tone-of-voice/references/editorial-quality-gates.md`
  remains the second documented sweep exemption. Its retired-name hit is
  excluded because the sibling `xd-copy-router` fold owns the byte-sensitive
  three-copy reconciliation for the editorial-quality-gates copies; this slice
  must not rewrite that copy to satisfy a removed-name sweep.

- The same `tone-of-voice` editorial-quality-gates copy carries a stale
  duplication note: it still says the reference is intentionally duplicated
  into `conversion-design`'s `references/editorial-quality-gates.md`, but this
  fold deleted the `conversion-design` skill directory. That stale note remains
  until `xd-copy-router` reconciles the three editorial-quality-gates variants.

- T4 deleted every tracked file beneath the six retired skill directories.
  A bounded `find` over those exact directories returned no files, but the
  managed workspace denied both `rmdir` and `rm -d`, including after the one
  permitted escalation, so six empty directory shells remain locally. Git does
  not preserve empty directories; the repository artifact and CI checkout omit
  them. No code, test, or no-stub assertion was weakened, and the denied
  cleanup was not retried.

- The targeted roster selector reached two unchanged cleanup-sensitive cases:
  `tests/roster/test_core_install_handoff.py::test_real_core_repo_install_emits_deterministic_next_action`
  and
  `tests/roster/test_core_install_handoff.py::test_real_core_local_install_emits_next_without_marker_or_seeds`.
  Both ended in the managed environment's denied `os.rmdir` cleanup path.
  `git diff --quiet HEAD -- tests/roster/test_core_install_handoff.py` exited 0,
  confirming the test file matches HEAD. The unaffected selector, with exactly
  those two node IDs deselected, passed: 86 passed, 1756 deselected in 4.41s.

## T7 documentation classification

T7 classified `docs/` hits for the six retired genre skill names on
2026-09-26. The open class is empty after the T7 edits. Live records edited by
T7 were:

- `docs/product/journeys/designer-designs-surface.md` — live journey and single
  source of truth for the design chain; updated to describe the surviving
  `information-architecture` route.
- `docs/product/intents/xd-ia-archetypes-objects.md` — live queued intent with
  zero retired-skill names; re-measured and re-dated because this fold moved its
  IA and frontend line-range baselines and changed the nearest reference
  structure.
- `docs/product/intents/skill-sequence-wayfinding.md` — live intent whose
  pre-fold evidence named the retired registrations; updated to distinguish
  the historical measurement from the current genre-reference route.
- `docs/product/intents/growth-strategy-pack-charter.md` and
  `docs/product/intents/FEAT-0002-intent-graph-navigation.md` — live Draft
  intents found during final review after T7 had misclassified them as
  terminal. Their current routing statements now name
  `information-architecture` and its marketing, analytical, or workspace genre
  method instead of retired registrations.
- `docs/specs/pack-guidebook-walkability/notes/acceptance-set-construction.md`
  and `deliverable-form-ledger.md` — notes owned by an `Implementing` sibling
  delivery, found during final review after T7 had misclassified them as frozen.
  The live mutation recipe now removes `information-architecture` from the
  current 14-skill guidebook. The dated 2026-09-11 measurement keeps its
  retired-name rows and totals as historical evidence, with a current-state
  note that the six registrations were folded and no longer define routes.
- `docs/design/content/docs-guides-index.md` — live design content brief;
  retargeted to `information-architecture` with the documentation reference.
- `docs/design/content/journeys-index.md` — live design content brief;
  retargeted to `information-architecture` with the marketplace reference.
- `docs/design/content/marketing-home.md` and
  `docs/design/copy/marketing-home.md` — live design content/copy briefs;
  retargeted to `information-architecture` with the marketing reference.
- `docs/design/discovery/team-orientation-brief.md`,
  `docs/design/discovery/team-orientation-ia.md`,
  `docs/design/discovery/team-orientation-marketing-structure.md`, and
  `docs/design/discovery/team-orientation-seam.md` — live team-orientation
  discovery artifacts; prose retargeted to `information-architecture` with the
  relevant marketing or documentation reference. The artifact
  `type: conversion-design` field in
  `team-orientation-marketing-structure.md` was preserved unchanged.
- `docs/design/journeys/claude-apps-practitioner-current-state.md`,
  `docs/design/journeys/docs-guides-champion-current-state.md`,
  `docs/design/journeys/marketing-champion-current-state.md`, and
  `docs/design/journeys/team-orientation-future-state.md` — live journey
  records; ownership hand-offs retargeted to `information-architecture` with
  the relevant genre reference.
- `docs/design/screens/team-orientation/guides-index.md` and
  `docs/design/screens/team-orientation/marketing-home.md` — live screen
  records; ownership notes retargeted to `information-architecture` with the
  relevant documentation or marketing reference.

Remaining `docs/` hits are classified as follows:

- **Preserved artifact types:**
  `docs/design/discovery/team-orientation-marketing-structure.md` contains
  `type: conversion-design`, and
  `docs/design/discovery/team-orientation-docs-structure.md` contains
  `type: documentation-design`. These are live artifact contract values, not
  skill routes, and were intentionally not changed.
- **Dated design evidence or discovery outputs:** `docs/design/discovery/team-orientation-screen-list.md`,
  `docs/design/discovery/team-orientation-traffic-evidence.md`,
  `docs/design/discovery/team-orientation-heuristic-baseline.md`,
  `docs/product/findings/experience-design-thread-pressure-test.md`,
  `docs/product/findings/s7-walkability-handoff.md`,
  `docs/product/research/aesthetic-style-survey.md`, and
  `docs/product/research/experience-design-consolidation-analysis.md`.
- **Accepted product records not edited by T7:**
  `docs/product/briefs/experience-design-skill-consolidation.md`.
- **Frozen governance/spec records or spec-owned notes:** `docs/adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md`,
  `docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md`,
  `docs/rfc/0067-session-arc-conventions-and-pack-workflow-guide.md`,
  `docs/specs/xd-skill-boundaries/benchmark.md`,
  `docs/specs/m3-experience-design-rename/plan.md`,
  `docs/specs/experience-pack-0.6.0/spec.md`,
  `docs/specs/experience-pack-0.6.0/plan.md`,
  `docs/specs/xd-web-journey-skill-count/spec.md`,
  `docs/specs/spec-D-pack-workflow-guide/spec.md`,
  `docs/specs/design-handoff-read/spec.md`,
  `docs/specs/design-output-addressing/spec.md`,
  `docs/specs/communication-modes-editorial/spec.md`,
  `docs/specs/communication-modes-editorial/plan.md`,
  `docs/specs/communication-modes-editorial/test-results.md`,
  `docs/specs/xd-genre-router/spec.md`,
  `docs/specs/xd-genre-router/plan.md`,
  `docs/specs/xd-genre-router/notes/routing-classification-evidence.md`, and
  this ledger.
- **Sibling-slice records:** `docs/specs/xd-copy-router/spec.md` and
  `docs/specs/xd-copy-router/plan.md`; T7 records the hand-off but does not edit
  the sibling slice.
- **Release history:** `docs/product/changelog.md`; T7 does not rewrite
  historical changelog entries.

No open `docs/` record remains owed a T7 edit.

## T7 sibling hand-off confirmations

- `docs/product/intents/xd-state-reviewer-doctrine.md` was not edited by T7.
  The sibling `xd-copy-router` spec carries the owed criterion: update that
  intent against the `experience-reviewer` edits, or record it as confirmed
  unchanged.
- The sibling `xd-copy-router` spec also owns its copy-layer edits, so this
  delivery does not change the doctrine bytes or pre-empt that hash-sensitive
  work.
