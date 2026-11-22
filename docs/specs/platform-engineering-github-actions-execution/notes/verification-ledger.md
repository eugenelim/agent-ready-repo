# Verification ledger: GitHub Actions release execution

Execution evidence for [`spec.md`](../spec.md). Cloud account numbers, role identifiers, bucket names and audit version ids are omitted; `<account>`, `<target-bucket>` and `<audit-bucket>` stand for them.

## Live fixture

| Item | Value |
| --- | --- |
| Repository | `eugenelim/pe-release-fixture` (public, GitHub.com, created 2026-11-15, immutable OIDC subject form) |
| Environment | `sandbox`: required reviewer `eugenelim`, `prevent_self_review: true`, `can_admins_bypass: false`, protected branches only |
| Release branch | `main`, repository ruleset: pull request with 1 approval, non-fast-forward, deletion; repository admins bypass |
| Agent identity | GitHub App `pe-release-fixture-agent`, installed on the fixture only, permissions `actions: write`, `contents: read`, `deployments: read`, `metadata: read`; public, so its record is readable by the job |
| Cloud | AWS sandbox `<account>`, owner-attested non-production with no real user data; region `us-east-1` |
| Role trust | GitHub OIDC provider, `StringEquals` on `aud`, `sub` `repo:eugenelim@473231/pe-release-fixture@1459092128:environment:sandbox:job_workflow_ref:eugenelim/pe-release-fixture/.github/workflows/release-deploy-job.yml@refs/heads/main` and `repository_id` |
| Stores | `<target-bucket>` unversioned, one-day expiry, `s3:*` deny on `releases/current.json` to every principal but the role; `<audit-bucket>` versioned, Object Lock COMPLIANCE one day, no lifecycle on `decisions/` or `ops/`, `s3:*` deny to every principal but the role, erasure and protection changes denied to everyone |
| Controls | `max_executions` 20 per one-day window; the fixture renders bucket and role names from environment secrets so none is committed |

Fixture-only adaptations, none in shipped templates: a `release-build.yml` that creates a GitHub build-provenance attestation for the payload; prepare records `gh attestation verify --source-digest $GITHUB_SHA` output as the provenance evidence and adds the owner's operations note as evidence; deploy-job renders controls from secrets and admits the note in its archive allowlist; a negative `oidc-sandbox-probe.yml`.

## Readiness over real settings

The reference's capture recipe, run with the agent app token for GitHub and sandbox administrator reads for AWS, gave `ready` with every control `met` and no blocked mutation. With the environment's required reviewer removed, the same capture gave `blocked`, `human-approval` `missing` with `reviewers-missing` and `self-review-allowed`, and `blocked_mutations` `deploy`, `teardown`.

## Focused pre-deploy review

Independent Codex release reviewers, each given only its role definition, checklist and the artifact, reviewed four candidates.

- A synthetic-provenance candidate returned `insufficient-evidence` from both roles (source binding unproven, audit retention unowned), so `check-stage --stage pre-deploy` refused `skipped-stage`.
- A candidate with real attestation but mismatched source repository and build commit was `blocked` on provenance; the reliability role also found that teardown's absence check returns 403 without bucket listing.
- After both fixes, every later candidate passed both roles and reached `execution-eligible`. One reliability concern stays open: audit history grows until the owner retires the fixture.

## Live runs

All dispatches were by the agent app unless noted; every approval was by the owner.

Prepare runs: 43793468692 (for 43793686180), 43804431392 (43804619860), 43807444467 (43807671076), 43811462726 (43811652158, 43811841447, 43812255246, 43812272549, 43814284163), 43814642660 (43815405563, 43815908352, 43817057303), 43820708251 (43820962617), 43830782898 (43831007361). Each prepare ran on the same commit as its build attestation and the deploy workflow.

| Run | Case | Outcome |
| --- | --- | --- |
| 43807671076 #1 | Happy path, approval comment `admission:<digest>` | Every step succeeded: verify-admission, bind, credentials, budget (0 of 20 used), audit, recheck (live readiness all met), mutate-object, observe, teardown (absence confirmed), ops, summary (exit 0 means `audited`) |
| 43807671076 #2 | Re-run requested by the agent | `bind` refused `rerun-refused`; credentials, budget, audit, recheck, mutate-object, observe, teardown, ops and summary skipped |
| 43811652158 | Dispatch input names another admission | `bind` refused `admission-digest-mismatch`; every later step skipped |
| 43811841447 | Approval comment names another admission | `bind` refused `approval-unbound`; every later step skipped |
| 43793686180 | Approval with an empty comment | `bind` refused `approval-unbound`; every later step skipped |
| 43814284163 | Prepare artifact deleted by the agent before approval | `verify-admission` stopped on the artifact listing; every later step skipped |
| 43817057303 | Required reviewer removed from the environment | No gate; `bind` refused `protection-changed`; every later step skipped |
| 43804619860 | Agent app was private | `recheck` live capture got 403 on the app record and failed closed after the decision write; ops recorded `no-mutation` |
| 43812255246, 43812272549 | Two identical dispatches | The second stayed `pending`, not cancelled; jobs ran 05:48:30–05:49:12Z and 06:02:07–06:02:47Z |
| 43815405563 | Cancelled by the agent right after `recheck` | The steps had finished first; `reconcile` from the uploaded records, a fresh run and jobs capture, the full audit listing and a fresh observation returned `retry-allowed`; without the ops record it returned `pause` (`ops-missing`) |
| 43820962617 | Approved after the candidate's evidence passed the policy's one-hour age | `verify-admission` refused `stale`; every later step skipped |
| 43831007361 | Cancelled by the agent while a fixture-only 45 s pause held `observe`, after `mutate-object` succeeded | Run `cancelled`: decision version 08:25:38Z, target write 08:25:51Z, cancel 08:25:53Z, `observe` cancelled; guarded teardown removed the object and ops recorded `torn-down` at 08:26:10Z. `reconcile` from the uploaded records, a fresh run and jobs capture, the full audit listing and a fresh observation (key absent) returned `retry-allowed` |
| 43815908352 | Owner dispatched, then tried to approve | `current_user_can_approve: false`; no approval was recorded; cancelled |
| 43814564315 | Second workflow in `sandbox` asks for the deploy role | `AssumeRoleWithWebIdentity` returned AccessDenied |

### Re-runs with post-run effect observations

Each row below has a post-run observation of the single declared effect (`releases/current.json`, listed by the sandbox administrator). Every later step after the refusing step was skipped.

| Run | Prepare | Case | Refusal | Observation |
| --- | --- | --- | --- | --- |
| 43890215996 | 43889677871 | Required reviewer removed; no gate | `bind`: `protection-changed` | 14:52:08Z absent |
| 43890321787 | 43889677871 | Dispatch names another admission | `bind`: `admission-digest-mismatch` | 15:20:33Z absent |
| 43895303360 | 43889677871 | Approved after the evidence expired | `verify-admission`: `stale` | 15:50:55Z absent |
| 43901470444 #1 | 43901025849 | Approval comment names another admission | `bind`: `approval-unbound` | 15:57:41Z absent |
| 43901470444 #2 | 43901025849 | Re-run requested by the agent | `bind`: `rerun-refused` | 16:04:56Z absent |
| 43903509661 | 43901025849 | Prepare artifact deleted by the agent before approval | `verify-admission`: artifact listing | 16:18:47Z absent |

### Deploy-role erasure probe

Run 43879729120 (prepare 43879362230) added a fixture-only `erasure-probe` step after `audit`, running as the deploy role. Deleting its own decision version returned AccessDenied. Shortening that version's COMPLIANCE retention was refused by S3. The version was then read back with the same version id, an unchanged checksum, lock mode `COMPLIANCE` and an unchanged retain-until time. The rest of the run completed the happy path, and the effect was observed absent at 14:48:05Z.

### Deploy-role overwrite probe and the updated template

Run 44952869442 (prepare 44952504320, 2026-11-21) ran the template after the review repairs (native S3 listing pages, prerequisite guards, step names) with the fixture-only `erasure-probe` extended by an overwrite attempt. As the deploy role, deleting its own decision version returned AccessDenied and shortening its retention was refused. Writing different bytes to the same decision key only created a new version. A by-id read-back of the recorded version returned unchanged bytes and checksum, lock mode `COMPLIANCE`, and the original retain-until time, 2026-11-22T22:22:16Z. Every deploy step then succeeded.

Run 43931762853 (2026-11-16) ran the same repaired template without the probe and also succeeded in every step; the effect was observed absent at 18:44:32Z. Runs 43913414358 and 43932529949 were approved after their evidence expired, or not at all, and stopped at `verify-admission` with `stale` or were cancelled before any step.

Before these runs, the fixture's operations note was amended with a dated retirement (2026-12-31), a lifetime bound (at most 940 executions and about 1,900 audit versions, under 5 MB) and a stop rule at 2,000 versions, after a fresh reliability reviewer raised unbounded audit growth to a blocker. Both reviewers then passed.

### Final template

Run 44960420449 (prepare 44960262038, 2026-11-21) ran the shipped template after every review repair: controls rendered from a committed placeholder template and the environment secrets, native S3 listing pages with required decision and ops streams, no conditions on prerequisite or mutate steps, and full role-ARN binding. Every step from `verify-admission` to `records` succeeded, and the target was observed empty afterwards.

No-mutation proof: CloudTrail `AssumeRoleWithWebIdentity` events for the deploy role exist only for session names `release-43804619860`, `release-43807671076` (one event, attempt 1), `release-43812255246`, `release-43812272549`, `release-43815405563` and `release-43831007361`. No session exists for any refused run or for the re-run attempt, so none of them held credentials that could write the target. The probe's call is recorded as AccessDenied.

Identity and store checks outside runs:

- The agent app token got 403 for `PUT` environment, listing environment secrets, deleting the ruleset, and approving a waiting deployment.
- The sandbox administrator got AccessDenied writing the target key, writing a decision object, deleting a decision version and overwriting it, and 403 reading it.
- Audit listing after the happy path: decision written 05:09:18Z, ops 05:09:39Z; the target bucket was empty after teardown.
- IAM policy simulation for the deploy role on a decision object, with the live audit bucket policy: `s3:DeleteObject`, `s3:DeleteObjectVersion`, `s3:PutObjectRetention`, `s3:BypassGovernanceRetention` and `s3:PutObjectLegalHold` are `explicitDeny`. `s3:PutObject` is allowed and adds a new version; versioning and COMPLIANCE retention leave the recorded version unchanged.
- Ordering from uploaded records: run 43815405563 wrote its decision at 06:17:31Z, the target at 06:17:45Z and ops at 06:17:50Z; run 43831007361 at 08:25:38Z, 08:25:51Z and 08:26:10Z.

## Defects found by the live runs and fixed

- `get-bucket-versioning` on a never-versioned bucket prints nothing; capture records `{}` only for that exit-0 empty answer.
- GitHub reports `sub_claim_prefix` as the subject's full repository part; readiness now requires it to equal this repository's form.
- Deploy-job steps lacked names, so the jobs API could not identify `mutate-` steps for `reconcile`; each step's name now equals its id.
- Teardown's absence check needs `s3:ListBucket` on the target, limited by `StringEquals` `s3:prefix` to the effect key; readiness accepts exactly that.
- The job uploaded no records, so the agent could not reconcile; it now uploads `release-records` whenever binding succeeded.
- The prepare example now records the source repository URL next to the revision.
- `budget`, `recheck` and `reconcile` now refuse `listing-incomplete` when a listing's continuation markers skip a page, and `summary` takes `--controls` only as an optional key check (both found by the acceptance verifiers).
- The reference and guides now state that the agent app must be public.

## Gates

- `packs/release-engineering/tests`: 5,320 passed.
- `make lint-ruff lint-mypy`, `make precheck`, `tools/lint-pack-test-boundary.py`, `tools/changelog.py validate`, guide validation and self-host: clean.
- `pytest tests/roster`: 3,481 passed; 1 failure and 6 errors, all in `test_portable_catalogue_authentication_packaging.py` (local credbroker wheel build). The same file fails identically on a clean `origin/main` worktree here, so it is pre-existing; captured as `docs/product/captured/pre-existing-credbroker-wheel-build-local.md`.

## Acceptance and review

- Eight independent Codex acceptance verifiers checked all 44 criteria against the real artifacts; their failures drove repair tasks T10 to T18. The final verifier passed all 44.
- Six review rounds by Codex adversarial, security and quality reviewers. Supported findings were repaired in T14, T16, T17 and T18, plus two working-material corrections to the spec's readiness table. The final round was clean for all three roles.

## Limits

- The controller host also holds owner-level GitHub and AWS credentials. The runs prove the controls against the agent app identity. The bucket policies limit even the administrator's writes, but an administrator can change those policies.
- The candidate payload is a committed synthetic image manifest. Its provenance is a real GitHub attestation, but no container image was built or run.
- The interrupted run needed a fixture-only pause to place the cancellation after the mutation; a cancellation during the provider write itself is covered by the offline `reconcile` cases.
- GitHub's UI approval twice failed to record or omitted the comment; both cases ended in refusal or expiry, not mutation.
