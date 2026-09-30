# Verification Ledger: Creative Direction Contract

## T4 packaging and guide

- 2026-09-27: Updated the Experience Design guide so `creative-direction` publishes the engagement mode, product-specific visual thesis, first-viewport thesis, optional approved visual target, and content/asset honesty contract.
- 2026-09-27: Bumped `packs/experience-design/pack.toml` and `packs/experience-design/.claude-plugin/plugin.json` to `4.0.2`. The branch first targeted `4.0.1`; `main` released that version separately, so the rebase moved this release to `4.0.2`.
- 2026-09-27: Added a free-standing `experience-design` `4.0.2` changelog entry directly below the `[core][2.27.1]` entry and above the `4.0.1` entry `main` already published. `test_the_core_release_heading_sits_directly_beneath_unreleased` requires the `[core]` heading to be the first one under `[Unreleased]`, so the new entry cannot lead the file. Highlights decision: yes, this changes what pack consumers can ask `creative-direction` to produce and what evidence they should expect in the artifact.
- 2026-09-27: Matching-version assertion passed: pack, plugin, and marketplace all report `4.0.2`.
- 2026-09-28: The rebase onto `main` after PR #1455 dropped the hand-edited `.claude-plugin/marketplace.json` version line, reverting it to `4.0.1` while `pack.toml` and `plugin.json` stayed at `4.0.2`. Six CI jobs failed on the one inconsistency, all reporting `CAT-V-015 self-host projection is out of date`. Regenerating with `python3 -m agentbundle catalogue self-host --root . --write` produced exactly that one line and nothing else; `--check` then reported no drift.
- 2026-09-27: The guide's `**What it looks like:**` excerpt was rewritten as a verbatim contiguous run of the first 84 lines of `creative-direction-template.md`, covering the new engagement-mode, visual-thesis, first-viewport, and approved-visual-target blocks. An abridged excerpt failed the CI job `Guidebook steps agree across every surface` with `artifact_preview: excerpt does not appear verbatim in its declared source`; `python3 tools/lint-guidebook-steps.py guides/experience-design` now reports OK.
- 2026-09-27: The new pack suite was wired to a runner. CI job `Caps enforcer self-test` failed with `packs/experience-design/tests/skills/creative-direction holds a suite that no runner names`. The suite reads only its own pack, so the pack tree is its correct home; it is now named by one `run-test-suite` line in the Makefile and by a new `build-check.yml` / `gate-main` step, with matching `STEP_DISPOSITION`, `_GATE_MAIN_CHECKS`, and `SUITE_DISPOSITION` entries in `tools/lint-ci-parity.py`. `python3 tools/lint-pack-test-boundary.py` passed 8 cases; `tools/lint-ci-parity.py` passed both directions; `tools/test-lint-ci-parity.py` passed 216 cases.
- 2026-09-27: The two `run-test-suite` plan digests in `tools/test_local_ci_shared_test_deduplication.py` were re-pinned because the added Makefile line moves the plan. Sole cause was proven: the new line appears exactly once at index 36 in both plans, and removing it recomputes the superseded pins `3bd4c26d…` and `c4325088…` element for element. The prior pins were live, not stale — the same function over `origin/main:Makefile` returns an empty error list. The suite then passed: 51 passed in 75.09s.
- 2026-09-27: Targeted pytest passed: `tests/roster/test_experience_design_guide_agreement.py`, `packs/experience-design/tests/skills/creative-direction/test_contract.py`, and `tests/conformance/test_pack_metadata.py` reported 59 passed in 1.59s.
- 2026-09-27: Deep catalogue lint passed with advisory warnings only: `python3 -m agentbundle catalogue lint --root . --deep` exited 0 after 8.70s.
- 2026-09-27: `make lint-ruff lint-mypy` passed after 3.03s.
- 2026-09-27: `make build-self` did not regenerate the marketplace because the unforced repository-owned write path refused the dirty worktree before writing. The marketplace entry was updated to match the source manifests, and the matching-version assertion above checked the result.
- 2026-09-27: `python3 -m agentbundle catalogue verify --root .` failed during temporary-directory cleanup with `PermissionError: Operation not permitted` while removing generated `author-product-docs/references`. A bounded retry with `TMPDIR` inside the workspace failed on the same cleanup path.
- 2026-09-27: `make build-self DRY_RUN=1` failed during shadow-tree cleanup with `PermissionError: Operation not permitted` while removing generated `.claude` and `.codex` projection directories.
- 2026-09-27: The failed verifier and self-host checks left `.pytest-tmp/` scratch directories. Sandboxed and escalated `rm -rf .pytest-tmp` both failed with `Operation not permitted`.
- 2026-09-27: Controller rerun after all implementation changes: the contract, guide-agreement, and pack-metadata suites reported 59 passed in 0.97s (4.35s wall time); the two existing Experience Design containment and handoff suites reported 17 passed in 0.72s (4.18s wall time).
- 2026-09-27: Controller rerun after all implementation changes: `make lint-ruff lint-mypy` passed in 2.62s, and deep catalogue lint exited 0 in 7.10s with 73 existing advisory findings outside this change.
- 2026-09-27: An approved outside-sandbox rerun of catalogue verification still reached the accepted supervised-worker cleanup limitation documented by ADR-0094: generated `product-documentation/author-product-docs/references` could not be unlinked. The failure is outside the diff and remains a known local skip rather than evidence of catalogue-content drift.
- 2026-09-27: Repository-owned `_aggregate_marketplace` regenerated the marketplace into `/private/tmp/creative-direction-marketplace-10a41c20`; `cmp -s` returned 0 against `.claude-plugin/marketplace.json`. Both files have SHA-256 `ad1642d45e1de997ed2adca0bf12bf647530555f9cb3c5d819f582060a3bf620`, providing byte-for-byte zero-drift evidence without bypassing the dirty-tree guard.
- 2026-09-27: Post-review repair rerun combined all targeted contract, guide, metadata, containment, and handoff suites: 76 passed in 1.37s (5.31s wall time). The required `make lint-ruff lint-mypy` gate then passed in 3.88s.

## Manual invocation

The exact in-worktree skill was installed alone at repo scope for the Codex adapter under `/private/tmp/creative-direction-manual-10a41c20/.agents/skills/creative-direction`. Byte comparison confirmed the installed `SKILL.md` and artifact template match their source files. The host CLI could not start a second process because its in-process app-server client hit the same managed-runtime `Operation not permitted` constraint in sandboxed and approved outside-sandbox attempts. The current agent therefore exercised that installed copy directly, with no optional upstream pack or visual capability, and wrote `/private/tmp/creative-direction-manual-10a41c20/direction/facilities-risk-queue.md` (SHA-256 `a347b85ff40f1d193f8f2740aef2a043c785796c7767ffbb8b7689b0ab601a00`).

Direct-answer prompt:

```text
Use creative-direction for a responsive web surface.

Product: a maintenance-planning tool for small facilities teams.
Audience: an operations manager who has twenty minutes between service calls and needs to decide which preventive jobs to schedule first.
Distinctive mechanism: it turns inspection notes and asset age into a visible risk queue with a plain-language reason for each ranked job.
Honest proof available: sample risk queue rows, reason labels, inspection-note snippets, and before/after schedule conflicts from a demo workspace.
Surface genre: workspace dashboard.
Approved visual target: none.
No Product Engineering pack, Frontend Engineering pack, comp, browser runtime, or image-analysis tool is available.
```

Observed result:

- AC-0001: primary engagement mode is `operate`; secondary mode is `none`; surface genre remains the separate `workspace dashboard` value.
- AC-0003: the product-specific visual thesis names the time-boxed operations manager, the risk-queue mechanism, and demo-only proof with explicit limits.
- AC-0005: the first-viewport thesis makes the top maintenance decision and its reason clear, exposes asset-age and inspection-note evidence, and supports scheduling or continuing down the queue.
- AC-0007: approved visual target is `none`; binding and illustrative fields are also `none`; responsive adaptation is still stated.
- AC-0008: demo rows, labels, snippets, and conflicts are available evidence; real customer data, outcomes, testimonials, certifications, screenshots, imagery, and measured savings are explicit placeholders. Provenance is direct user answers plus a demo workspace; no generated visual asset is proposed.
- AC-0012: the run completed without Product Engineering, Frontend Engineering, product intent, Digital Experience Contract, screen brief, existing product, comp, browser runtime, or image-analysis capability.
- AC-0016: route selection was deterministic (`originate` from the supplied state), and the run introduced no executable engine, extension, hook, downloaded binary, or dependency.

## Review roster

- Adversarial review: clean after two rounds and independent adjudication; the three first-round blockers were fixed, and the second-round lifecycle finding was refuted as closeout work owned by the work-loop.
- Experience reviewer: named skip because that optional reviewer role is not installed. Reader-facing agreement is covered by the guide-agreement suite and the adversarial review.
- Security reviewer: not warranted; the change adds no authority, untrusted-input, tool, permission, sandbox, network, secret, or data-handling boundary.
- Frontend reviewer: not warranted; no HTML, CSS, or JavaScript is produced.
- Design reviewer: not warranted; no architect-pack integration or architecture artifact is involved.
- Quality engineer: not warranted; the change adds no operational-safety module, dependency, abstraction boundary, or other high-risk trigger.
