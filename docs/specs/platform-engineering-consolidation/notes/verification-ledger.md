# Verification ledger: platform-engineering consolidation

Execution evidence for [`spec.md`](../spec.md). Cloud account numbers, role identifiers and bucket names are omitted; the fixture renders them from environment secrets.

## Run

The work-loop supervisor ran ten tasks (T1–T8 from the plan, T9 and T10 as review repairs) under run `run-40619ab44c5881ca`.

- **Workers:** Codex headless implementers wrote T1–T6 and T9. The controller ran T7, T8 and T10.
- **Acceptance:** three independent Codex passes returned 20, then 24, then 26 of 27 criteria.
- **Review:** Codex adversarial, security and quality reviewers ran three rounds. Round 1 found 3 issues, round 2 found 1, and round 3 was clean on every role.

## Migration against the real CLI

Each case below ran in a fresh Git repository with the branch's `agentbundle` CLI. The old catalogue was `git archive 42849d1e7`; the new one was the branch head after T5. Old packs need `core` and `repo-governance` installed first, so each setup installs them from the old catalogue.

| Criterion | Case | Result |
| --- | --- | --- |
| AC-0017 | `codex` and `cursor` share `.agents/skills/`; both old packs at `repo` for each | Phase 1 then phase 2 leave `platform-engineering` once per adapter, no old row in state, no old-only file. Every `platform-engineering` skill is in `.agents/skills/`. |
| AC-0018 | `release-loop/SKILL.md` edited before phase 1 (`claude-code`, `repo`) | Uninstall kept the edit (`31 removed, 1 kept`). Phase 2 left the edit intact and wrote `SKILL.upstream.md` beside it. |
| AC-0019 | Same adapter and scope | Install refused while old rows remained, changing no file or state row. Phase 2 succeeded after phase 1. |
| AC-0019 | Another adapter sharing paths (`codex` old, `cursor` new) | Refused, changing nothing. Phase 2 succeeded after phase 1. |
| AC-0019 | Another adapter (`codex` old, `claude-code` new) | Not refused: installed beside the old rows. Phase 1 then phase 2 reached the clean end state. |
| AC-0019 | Another scope (old at `local`, new at `repo`) | Not refused. Installed beside the old rows and wrote four `.upstream` companions next to the old files. After phase 1 and phase 2 the real files hold the new content and the four companions remain. |
| AC-0020 | `iac-terraform` at `repo`, `release-engineering` at `local`, one adapter | Choosing `repo` migrated both. Interrupting after the first uninstall, then re-running phase 1 and phase 2 twice, reached the same rows and files. |
| AC-0021 | Rollback from the pinned ref | Uninstall of `platform-engineering` kept the edit. Reinstalling `release-engineering` refused while `SKILL.upstream.md` remained. After merging and deleting the companion, both old packs reinstalled with the edit kept. |
| AC-0021 | Rename hint | `install --pack iac-terraform` and `--pack release-engineering` from the new catalogue both print `pack '<name>' was renamed to 'platform-engineering'` with the install step. |

The migration how-to and the pack README name both unrefused configurations, the companion cleanup after a cross-scope install, and the companion step before rollback.

## Old-name search

`git grep -n -I -e iac-terraform -e release-engineering HEAD` at the final run head (`307cc55b7`) found 731 lines in 161 files. No line outside the exempt categories names an installable pack. [`old-name-search.md`](old-name-search.md) lists every line with its category.

| Category | Lines |
| --- | --- |
| Frozen shipped specs and their notes | 439 |
| Frozen accepted RFCs and ADRs, with notes | 126 |
| Released changelog entries | 47 |
| Historical research, design, discovery, briefs, findings, intents, knowledge and charter | 30 |
| Rename fixtures and rename-hint tests | 20 |
| This spec | 22 |
| Migration and rollback text naming the retired packs | 12 |
| Links to frozen RFC-0065 by file name | 10 |
| Unchanged core and repo-governance source, or its self-hosted copies | 7 |
| Unshipped or archived spec records | 6 |
| Test assertions and comments naming retired routes | 5 |
| This release's changelog fragment | 3 |
| Rename map | 2 |
| Anchor tombstone for frozen RFC links | 1 |
| Decision index row titling a frozen record | 1 |

`governance/manifest.example.yaml` is the self-hosted copy of the unchanged repo-governance seed, so it keeps the old name until a repo-governance release; the amendment of 2026-11-22 records this.

## Core installed

In a fresh repository with `core` then `platform-engineering` installed, the state lists both packs.

- **Terraform-only:** `discover` ready, `check-summary` ready, `check-review` pass, and the bundle valid with 9 of 9 evidence items verified. These match the core-absent run.
- **Release-only:** collection validated 6 of 6 evidence items and admission admitted, using the installed `release-loop`. Its files are byte-identical to the core-absent install.
- **Test:** `test_release_journey_with_core.py` runs the full release journey with core-like skills and reviewer agents beside the platform skills, and asserts the core-absent results. A pack test may not read another pack's files.

## Live Terraform

These runs used only `platform-engineering`, installed into a fresh repository, with Terraform 1.17.2.

- **Provider:** `terraform init -backend=false` and `terraform providers schema -json` fetched `registry.terraform.io/hashicorp/null` 3.3.2.
- **Plan:** `fmt -check`, `validate` and `plan -out=tfplan` succeeded. `show -json` gave one change, `null_resource.example` create.
- **Review and bundle:** `check-review` passed, and `plan_bundle.py validate` returned `valid` with all 9 evidence items verified.
- **No apply:** no apply or destroy ran, and no state file exists.

The run was repeated with the fixture's target (`sandbox`, `example-sandbox`); that bundle is the one AC-0024 admits. It also passed with `core` installed beside the pack.

## Live GitHub Actions fixture

The fixture is `eugenelim/pe-release-fixture`, with the environment and cloud controls the [GitHub Actions execution ledger](../../platform-engineering-github-actions-execution/notes/verification-ledger.md) records.

**Fixture commits:**
- `20b1152` vendors `release-loop` from `packs/platform-engineering`. All 23 tracked files are byte-identical to the pack copy.
- `bf0611a` and `f346477` add the end-to-end adaptations:
  - Prepare copies the reviewed plan bundle into the candidate as a `terraform-plan` component.
  - Build attests the bundle, and prepare records that attestation as the component's provenance.
  - The plan checks cite the bundle's own validation and review evidence.
  - The deploy archive allowlist admits the bundle files.

**AC-0024 bundle:** the fixture's `release/iac/bundle.json` is the sandbox capture above. Only its nine evidence locators were rewritten to the candidate layout, and the hidden lock file was renamed `dependency-lock.hcl` so artifact upload keeps it. Every evidence file matches its recorded digest.

| Run | Case | Outcome |
| --- | --- | --- |
| 45135785130 (prepare 45135012070) | AC-0023 release-only, admission `5aeab909…7a71` | Every step succeeded, including teardown, which confirms the target key absent |
| 45193028969 (prepare 45192693242) | AC-0024 end-to-end, admission `c0223397…1909` | Admission pins plan bundle `sha256:1cc9a82f…5503`. Every step succeeded, and the records summary is `audited` with `cleanup_state` `torn-down`. |

**Refused attempts, none with a cloud mutation:**
- 45125643237 was cancelled before approval, after its evidence aged past the one-hour policy.
- 45135354147 stopped at `bind` with `approval-unbound`: the approval comment lacked `admission:<digest>`.
- 45136793481 stopped at `verify-admission` with `stale`: it was approved after the one-hour window.

**Pre-deploy reviews:** on two candidates, a Codex reviewer blocked first.
- **Reliability:** it questioned the conditional `ListBucket` grant for the absence check. Three earlier runs' teardown steps (44960420449, 44952869442, 43931762853) show S3 returning 404. Recording that in the permissions description cleared it.
- **Security:** it found the plan component had no provenance, which the bundle attestation fixed.

Every candidate dispatched after that passed both reviews.

## Gates

- **Pack suites:** `generate-iac` 730, `prepare-release-handoff` 176 and `release-loop` 5,366 tests pass, one process per skill directory.
- **Lints and builds:**
  - Catalogue lint and verify, `make lint-ruff lint-mypy` and `make precheck` pass (bandit is not installed locally).
  - `tools/lint-pack-test-boundary.py`, guide validation, the guide index, guide titles and `changelog.py validate` pass.
  - The site build passes. Web tests pass 240 of 240, and docs-site plugin tests pass 13 of 13.
  - `make build-self` twice leaves no diff.
- **Roster:** 3,481 pass. The 7 credbroker-wheel results in `test_portable_catalogue_authentication_packaging.py` fail locally (no `setuptools`) and on main.
- **Local-only failure:** `test_agent_plugin_projection.py::test_agent_plugin_manifest_sanitizes_deep_unused_metadata` fails the same way on `origin/main` under local Python 3.14.9. Main's build-check passes it, so the pull request's CI is the evidence of record for AC-0006.
- **Knowledge-freshness lint:** it reports one stale pin, on an unrelated topic (`repairing-the-cited-surface-leaves-its-siblings-contradicting-it`), identical on main.
