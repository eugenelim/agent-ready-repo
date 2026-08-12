# How to roll out the Claude-plugin publisher App

**Audience:** the repository owner. Every step below needs owner-level access to
repository settings; nothing here can be delegated to CI or to an agent.
**Purpose:** completes T13 of [`docs/specs/claude-plugin-hook-parity/plan.md`](../../specs/claude-plugin-hook-parity/plan.md)
— the operational half of [ADR-0079](../../adr/0079-executable-plugin-branch-publisher-identity.md).

---

## Why this exists

ADR-0079 makes a dedicated, repository-scoped GitHub App the **only** actor that
may update `claude-plugins-dist`, the mutable branch adopters install executable
plugin code from. The code half of that decision has shipped. The settings half
— the App, the protected environment, and the branch ruleset — is this runbook.

Until you finish it, two things are true and both are deliberate:

- The publisher runs with the generic Actions app (`contents: write`). That is
  the interim identity required by spec **AC36**, not an oversight.
- `claude-plugins-dist` has **no ruleset**, so it is not yet protected from an
  ordinary write. This is the exposure ADR-0079 exists to close.

The ordering is mechanically enforced in both directions. You cannot ship the
App-token workflow before the credentials exist, and once the evidence file
lands, the interim workflow fails its own construction test — so the final step
of this runbook is not optional bookkeeping, it is what makes CI green again.

## Before you start

- `gh` authenticated as the repository owner: `gh auth status`
- The repository's `owner/name` — used as `--repo` below.
- Roughly 30 minutes. Step 1 is browser-only; the rest is scriptable.

---

## Step 1 — Create and install the App *(browser only)*

There is no API that creates a GitHub App on your behalf, and the private key is
downloadable exactly once. Do this by hand.

1. Go to **Settings → Developer settings → GitHub Apps → New GitHub App**.
2. Name it so the actor is recognisable in an audit log, e.g.
   `claude-plugin-publisher`.
3. Set **Repository permissions → Contents: Read and write**. Grant nothing
   else — the desired-state contract asserts `contents` is the *only* write
   permission, and the capture tool will refuse a broader installation.
4. Uncheck **Active** under Webhook; this App never receives events.
5. Under **Where can this GitHub App be installed?**, choose **Only on this
   account**.
6. Create it, then **Generate a private key** and keep the downloaded `.pem`
   somewhere you can paste from once.
7. **Install App** → select **Only select repositories** → this repository only.
8. Note the **App ID** from the App's settings page.

## Step 2 — Configure the protected environment

The environment already exists but holds nothing. Give it the policy ADR-0079
specifies, then the credentials.

```bash
REPO=<owner/name>
APP_ID=<app id from step 1>

# main-only deployments, owner approval required, no admin bypass.
gh api -X PUT "repos/$REPO/environments/claude-plugin-publish" \
  -F "can_admins_bypass=false" \
  -F "deployment_branch_policy[protected_branches]=false" \
  -F "deployment_branch_policy[custom_branch_policies]=true"

gh api -X POST \
  "repos/$REPO/environments/claude-plugin-publish/deployment-branch-policies" \
  -f "name=main" -f "type=branch"
```

Add yourself as a required reviewer with **prevent self-review** enabled, in
**Settings → Environments → claude-plugin-publish**. The REST API cannot set
`prevent_self_review`, so this part is browser-only too.

Then store the credentials — the App ID as a *variable*, the key as a *secret*:

```bash
gh variable set CLAUDE_PLUGIN_PUBLISHER_APP_ID \
  --env claude-plugin-publish --repo "$REPO" --body "$APP_ID"

gh secret set CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY \
  --env claude-plugin-publish --repo "$REPO" < /path/to/private-key.pem
```

Delete the `.pem` afterwards. If you lose it, generate a new key on the App and
re-run the `gh secret set` line — the App ID does not change.

## Step 3 — Prove the ruleset on the canary branch first

The live branch is **never** the target of a negative probe. Exercise the
ruleset against a throwaway branch, confirm both outcomes, then retarget.

```bash
git push origin main:claude-plugins-dist-control-canary
```

Create a ruleset in **Settings → Rules → New ruleset** targeting exactly
`refs/heads/claude-plugins-dist-control-canary`, with:

- **Restrict updates**, **Restrict deletions**, **Block force pushes** enabled.
- Exactly one bypass actor: the App from step 1, mode **Always**.
- No user, team, role, deploy key, or the generic GitHub Actions app.

Now record both canary outcomes:

```bash
# Negative: your ordinary identity must be REJECTED.
git commit --allow-empty -m "canary: ordinary identity"
git push origin HEAD:claude-plugins-dist-control-canary   # expect a rejection
```

For the positive case, trigger the publisher against the canary via
`workflow_dispatch` once the App-token step is restored (step 5), or push using
an installation token minted from the App. The push must be **accepted**.

Then clean up and retarget the ruleset to `refs/heads/claude-plugins-dist`:

```bash
git push origin --delete claude-plugins-dist-control-canary
```

> If your GitHub plan cannot express an App-only bypass or a required
> environment reviewer, **stop and surface it** — do not widen the bypass list
> to make the step pass. That trade was considered and rejected in ADR-0079.

## Step 4 — Capture the evidence

```bash
python3 tools/capture-publish-control-evidence.py \
  --repo "$REPO" \
  --ordinary-update rejected \
  --publisher-app-update accepted
```

This writes `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`
from live API state. It reads no secret — only the App ID, which is a public
identifier, plus structural booleans. The two canary outcomes are passed
explicitly rather than inferred, so the evidence cannot confirm itself from a
settings read.

Verify it against the independently authored desired state:

```bash
python3 tools/lint-claude-plugin-publish-control.py --require-live-evidence
```

Fix any mismatch in **settings**, not in the evidence file. The two documents
are meant to be written independently; editing the evidence to match the
contract destroys the only signal this check provides.

## Step 5 — Restore the App-token workflow

With evidence committed, the interim identity is now the violation. Restore the
App-token shape in `.github/workflows/publish-claude-plugins.yml`:

- `permissions: contents: read`
- `environment: claude-plugin-publish` on the `publish` job
- the `actions/create-github-app-token` step, SHA-pinned, reading
  `vars.CLAUDE_PLUGIN_PUBLISHER_APP_ID` and
  `secrets.CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY`
- the publish step's `CLAUDE_PLUGIN_PUBLISH_TOKEN` sourced from
  `steps.publisher-token.outputs.token`

The pre-revert shape is in git history — `git show 63f36552 --
.github/workflows/publish-claude-plugins.yml` — and is a correct starting point.
Keep the full-SHA pins and `persist-credentials: false`; both are required in
either identity.

Confirm the ordering rule now agrees with reality:

```bash
python3 tools/test-publish-claude-plugins.py
python3 tools/test-lint-claude-plugin-publish-control.py
make build-check
```

## Step 6 — Close out T13

1. Commit the evidence file and the restored workflow together.
2. Record the frozen-artifact errata named in T13 step 5 —
   `claude-plugins-manifest-correctness`, `claude-plugin-route-scope`, and
   ADR-0072's dated branch-integrity statements. Re-run the frozen-artifact grep
   first; if it finds another Shipped/Accepted premise, amend T13 before
   closing.
3. Only now may the spec move to `Shipped`, and only now may a hook-bearing
   user-capable pack publish.

## Verifying it actually worked

Do not stop at a green build. Push to `main` and confirm the publish job reached
the end:

```bash
gh run list --workflow=publish-claude-plugins.yml --limit 1
gh api repos/$REPO/branches/claude-plugins-dist \
  --jq '.commit.commit.committer.date, .commit.commit.message'
```

The branch's newest commit should name the `main` SHA you just pushed. A green
run that skipped the publish step is not a successful rollout.
