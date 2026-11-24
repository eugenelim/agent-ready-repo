# Protected GitHub Actions release example

These templates exercise a synthetic application release on GitHub.com using
GitHub-hosted `ubuntu-latest`. They collect committed example evidence, admit a
candidate, deploy its image manifest bytes to `releases/current.json`, observe
those bytes, and remove them. They do not build or publish a Docker image.
The example reports are synthetic; they provide no production assurance.

## Install and configure

1. Vendor the installed `release-loop` skill, including its scripts, references
   and assets, at `release-loop/` in the fixture repository. Python 3.11 or newer,
   curl, OpenSSL and the AWS CLI must be available (they ship on `ubuntu-latest`).
2. Copy the three `.example.yml` files to `.github/workflows/`, dropping
   `.example` from their names. Copy `controls.example.json` to
   `release-controls.template.json`. Set its repository, repository id, app identity
   and owner attestation to owner-reviewed fixture values. Keep `__TARGET_BUCKET__`,
   `__AUDIT_BUCKET__` and `__ROLE_NAME__` as placeholders. The protected job renders
   `work/controls.json` from the bucket secrets and the final name in
   `RELEASE_ROLE_ARN`, including when the role ARN has a path. It refuses unresolved
   placeholders or invalid JSON. Keep the workflow paths, `sandbox` environment,
   `example-sandbox` account label, `example-release` concurrency group, `app`
   payload component and `example-payload` effect id aligned with the templates.
   Audit prefixes remain bucket-qualified ARNs in controls; S3 keys contain
   only the key portion, such as `decisions/sandbox/<run>-<attempt>.json`.
3. Provision the environment, protected release branch, GitHub App, workflow-bound
   OIDC role, exclusive target writer and immutable audit store before dispatch.
   Use `references/github-actions.md` for the control mapping and capture recipe.
   The owner must attest that this isolated account has no real user data and no
   production path. A passing readiness report does not prove that attestation.
4. Put `RELEASE_ROLE_ARN`, `RELEASE_CLOUD_ACCOUNT`, `RELEASE_TARGET_BUCKET` and
   `RELEASE_AUDIT_BUCKET` in the `sandbox` environment's secrets. The called job
   reads its environment secrets; the caller also passes those names explicitly.
   Real role, account and bucket values never belong in workflow source. Use a
   separate deploy role with inline policies only. Allow only the operations
   named in controls, scoped to the exact effect, audit prefixes, configuration
   reads and the role's own inspection. Scope audit listings with `s3:prefix` to
   `decisions/*` and `ops/*`, and allow `s3:ListBucket` on the target bucket only with
   `StringEquals` `s3:prefix` set to `releases/current.json`, so teardown can confirm
   the deleted key is absent.
5. Keep the target bucket **unversioned** with expiration of the effect within
   seven days. The example refuses a versioned or suspended target so one delete
   removes all payload bytes. The audit bucket needs versioning and default
   COMPLIANCE object lock of at least seven days. Give the audit bucket an
   unrelated lifecycle rule under `example-unused/`; no rule may expire or
   transition the decision or ops prefixes. The workflow captures that lifecycle
   configuration and refuses capture errors rather than guessing missing state.

Checkout is pinned to `3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1), and upload-artifact to `cf430e030ddbb5b0abf93d22962f4752f3646cd9`
(v7.0.2). These were current pins at authoring time, supplied for this example;
review pins when adopting it.

## Prepare, review and dispatch

Run prepare on the protected release branch. It copies the existing image-only
candidate template, updates its time, source revision to `GITHUB_SHA`, evidence
and subject digests, validates it, and writes `admission.json`. One
`release-candidate` artifact holds the candidate, admission, policy and evidence.
The prepare job has read permissions only and no environment or OIDC access.

Download that artifact for focused security and reliability pre-deploy reviews.
Supply a base64-encoded JSON array containing exactly those two review records
as `pre_deploy_reviews` (at most 60,000 encoded characters). Records must bind the
candidate, target, current installed rubric digests, and evidence paths already
in the artifact, such as `security-report.json` and `test-report.json`. The job
writes them as `review-0.json` and `review-1.json`. It never fabricates reviews or
fetches additional review evidence. Dispatch with the successful `prepare_run_id`
and the bare 64-character SHA-256 of that artifact's `admission.json`.

The required human reviewer must differ from the triggering actor and agent.
Their approval comment must contain `admission:<64-character digest>`. Approvals
are specific to this dispatch. A re-run is refused. Prepare, controls and workflow
commits must agree; prepare again after changing any of them. The example policy
expires evidence after one hour, so finish review and approval within that time.

The job downloads the artifact ZIP with authenticated curl, following the signed
redirect without forwarding authorization to another host. It checks the archive
digest and exact member allowlist before extracting with `python3 -m zipfile`.
`bind` hashes that same downloaded file again, alongside the extracted admission.
Extraction must precede `bind` because binding needs the admission and evidence
files. Policy and controls are selected again from the protected checkout.

Only after admission and approval binding does the job request its OIDC identity
from GitHub and call `aws sts assume-role-with-web-identity`. Each returned
credential is masked before it reaches `GITHUB_ENV`. No third-party credential
action is used. Every audit and target call supplies the expected account owner.
Every object write supplies the marker and a provider-verified SHA-256 checksum.

The budget capture follows native S3 pagination for both prefixes, including
noncurrent versions, and fetches terminal ops bodies by version. Budget refusal
writes no audit decision. After the decision write, a fresh listing and live
settings capture feed `recheck` immediately before the target write.

## Outcomes and recovery

Any refusal stops the affected mutation. Teardown and summary require successful
`recheck`. Teardown re-reads the object and removes it only if its bytes and
marker match this binding. The summary reads the decision's immutable version
back inside the protected job and reports its stage and cleanup state. No
readiness report, binding, summary or stage grants production authority.

An interrupted, failed or unknown-effect run must be reconciled from a new
observation before retry. A retry is a new approved dispatch within the same
execution budget. A cancelled job can leave a decision without a terminal ops
record; only an owner-reviewed reconciliation in `reconciled_runs` can unblock
that history. Do not weaken checks or use another path after refusal. Workflow
records cannot prove exactly-once effects.

## Permission compatibility prerequisite

The checker requires Object Lock retention fields in the decision version's
head. AWS returns those fields only to callers with `s3:GetObjectRetention` on
the audit decision prefix. Include that read permission in the role and controls.
A checker version that rejects this narrowly scoped read cannot run these
examples: resolve that permission-model mismatch before deploying. Do not remove
retention checks or synthesize retention fields from bucket defaults.
