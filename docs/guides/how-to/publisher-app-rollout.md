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

> ### ✅ Completed 2026-08-12 — this procedure is now historical
>
> The rollout is done. The App is installed, the environment is configured, and an
> active ruleset protects `refs/heads/claude-plugins-dist` with the App as its
> only bypass actor. See the [ADR-0079
> errata](../../adr/0079-executable-plugin-branch-publisher-identity.md#errata)
> and the committed evidence at
> `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`.
>
> **Do not run these steps against the live control.** Step 3 deletes a branch
> and retargets the ruleset; step 5 restores a workflow shape that is already
> in place. Follow this document only to rebuild the control from nothing — after
> a key compromise, or when standing the same control up in another repository.
> Read it end to end first.

While the rollout was outstanding, two things were true and both were deliberate:

- The publisher ran with the generic Actions app (`contents: write`). That was
  the interim identity required by spec **AC36**, not an oversight.
- `claude-plugins-dist` had **no ruleset**, so it was not protected from an
  ordinary write. That was the exposure ADR-0079 exists to close.

The ordering is mechanically enforced in both directions. You cannot ship the
App-token workflow before the credentials exist, and once the evidence file
lands, the interim workflow fails its own construction test — so the final step
of this runbook is not optional bookkeeping, it is what makes CI green again.
Deleting the evidence file does **not** re-open the interim state: the lint
requires evidence unconditionally, and standing the control down means setting
`control_status: decommissioned` in `.github/claude-plugin-publish-control.json`
in the same commit.

## Before you start

- `gh` authenticated as the repository owner: `gh auth status`
- The repository's `owner/name` — used as `--repo` below.
- Roughly 30 minutes. Step 1 is browser-only; the rest is scriptable.

**Standing this up in a different repository? Do this first, before Step 1.**
A copied or forked tree inherits *both* halves of the publication control — the
desired-state contract and the previous repository's evidence — and they still
compare equal, so `make build-check` is green while attesting to controls that
were never observed here. The publish job refuses on its first run to `main`
(`--subject "$GITHUB_REPOSITORY"`), which is several steps before you reach the
capture in Step 4. So, in one commit, up front:

1. Set `repo` in `.github/claude-plugin-publish-control.json` to **this**
   repository's `owner/name`.
2. Delete the inherited
   `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` and set
   `control_status: decommissioned` in the same file, until Step 4's capture
   replaces it. That pair is the sanctioned way to run with no evidence.

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
6. Create it, then **Generate a private key**. The `.pem` downloads immediately
   and is never shown again; the `SHA256:` string on the page afterwards is a
   fingerprint, not the key. Move the file out of your download directory to
   somewhere owner-only, because you need it twice (step 2 and step 3):

   ```bash
   mkdir -p ~/.config/github-apps && chmod 700 ~/.config/github-apps
   mv ~/Downloads/<app-name>.*.private-key.pem \
      ~/.config/github-apps/claude-plugin-publisher.pem
   chmod 600 ~/.config/github-apps/claude-plugin-publisher.pem
   ```

   Leave it PKCS#1 (`-----BEGIN RSA PRIVATE KEY-----`) — that is what
   `actions/create-github-app-token` expects. Do not convert it to PKCS#8, and
   do not move it inside the repository.
7. **Install App** → select **Only select repositories** → this repository only.
   Creating the App does **not** install it, and an uninstalled App fails much
   later with an opaque 404 during step 4. Install it now, from
   `https://github.com/settings/apps/<app-name>/installations`.
8. Note the **App ID** from the App's settings page — the 6–8 digit numeric
   field. Not the Client ID (`Iv1.`/`Lv1.`) and not the App slug.

Before going further, confirm in the browser that the App's **Install App** page
lists this repository under *Installed*. There is no user-token API call that can
check this — the authoritative read is App-authenticated and happens in step 4,
which is late to discover a missed install.

## Step 2 — Configure the protected environment

The environment already exists but holds nothing. Give it the policy ADR-0079
specifies, then the credentials. This whole step is scriptable — reviewer policy
included.

```bash
REPO=<owner/name>
APP_ID=<app id from step 1>          # numeric App ID, not the Client ID
KEY=~/.config/github-apps/claude-plugin-publisher.pem
USER_ID=$(gh api user --jq .id)      # required-reviewer id, not the login
```

The reviewer list is an array of objects, which `-F` cannot express, so send a
JSON body. Setting all four policies in one `PUT` also avoids a window where the
environment holds credentials under a weaker policy:

```bash
gh api --method PUT "repos/$REPO/environments/claude-plugin-publish" \
  --input - <<JSON
{
  "wait_timer": 0,
  "prevent_self_review": true,
  "can_admins_bypass": false,
  "reviewers": [{"type": "User", "id": $USER_ID}],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
JSON

gh api --method POST \
  "repos/$REPO/environments/claude-plugin-publish/deployment-branch-policies" \
  -f name=main -f type=branch
```

Only then store the credentials — App ID as a *variable*, key as a *secret*:

```bash
gh variable set CLAUDE_PLUGIN_PUBLISHER_APP_ID \
  --env claude-plugin-publish --repo "$REPO" --body "$APP_ID"

gh secret set CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY \
  --env claude-plugin-publish --repo "$REPO" < "$KEY"
```

Confirm what actually stuck, rather than assuming the `PUT` honoured every key:

```bash
gh api "repos/$REPO/environments/claude-plugin-publish" \
  --jq '{can_admins_bypass, policy: .deployment_branch_policy,
         rules: [.protection_rules[] | {type, prevent_self_review,
                 reviewers: [.reviewers[]?.reviewer.login]}]}'
gh variable list --env claude-plugin-publish --repo "$REPO"
gh secret list --env claude-plugin-publish --repo "$REPO"
```

Expect `can_admins_bypass: false`, a `required_reviewers` rule with
`prevent_self_review: true` naming you, and `main` as the only deployment
branch.

**Keep the `.pem` until step 4 has run.** Step 3's positive probe signs a JWT
with it, and so does step 4's installation read — CI's copy in the environment
secret is not reachable from your shell. If you lose it at any point, generate a
new key on the App, re-run the `gh secret set` line, and delete the superseded
key from the App's page; the App ID does not change.

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

For the positive case, mint an installation token from the App and push with it.
Do not wait for step 5 — the workflow publishes to the live branch, not the
canary, so it cannot serve as this probe and the ordering would be circular.

```bash
KEY=~/.config/github-apps/claude-plugin-publisher.pem
b64() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

# A GitHub App JWT is valid for at most 10 minutes.
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64)
now=$(date +%s)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' \
  $((now - 60)) $((now + 540)) "$APP_ID" | b64)
sig=$(printf '%s.%s' "$header" "$payload" \
  | openssl dgst -sha256 -sign "$KEY" -binary | b64)
JWT="$header.$payload.$sig"

# Authenticating AS the App, so /repos/{repo}/installation is available here.
# It is NOT available to the user token `gh` holds, which is why
# capture-publish-control-evidence.py signs its own JWT for the same read.
# Headers go in on stdin, never in argv: another local process can read
# /proc/<pid>/cmdline, and this JWT can mint repository write tokens.
auth_config() { printf 'header = "Authorization: Bearer %s"\n' "$JWT"; }

INSTALL_ID=$(auth_config | curl -sf -K - \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/installation" | jq -r .id)

APP_TOKEN=$(auth_config | curl -sf -K - -X POST \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/$INSTALL_ID/access_tokens" \
  | jq -r .token)

git commit --allow-empty -m "canary: publisher app identity"

# Push to `origin` with the token supplied as a Git config header in the child
# environment — the same channel tools/catalogue/publish_claude_plugins.py uses
# (`_git_auth_env`). A credential-bearing remote URL would land the token in
# argv, in `.git/config`, and in git's error output.
GIT_CONFIG_COUNT=1 \
GIT_CONFIG_KEY_0="http.https://github.com/.extraheader" \
GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $(printf 'x-access-token:%s' \
  "$APP_TOKEN" | openssl base64 -A)" \
GIT_TERMINAL_PROMPT=0 \
  git push origin HEAD:claude-plugins-dist-control-canary   # expect ACCEPTED
```

That token expires in an hour and carries the App's installation permissions on
this repository only. Nothing needs to be stored. Note it is **not** narrowed the
way CI's is — the publish workflow passes `permission-contents: write` when it
mints, while this recipe takes the full installation set; keep the shell it lives
in short-lived.

> **If you would rather skip the JWT dance:** you can take the first successful
> publish on the live branch (after step 5) as the positive signal instead, and
> record `--publisher-app-update accepted` on that basis. It is a genuine
> App-accepted push. But it is *not* what T13 step 4 literally asks for, and the
> evidence file's `canary.branch` field will still name the canary ref — so
> amend T13 and the desired-state contract if you go that way, rather than
> letting the artifact imply a probe you did not run.

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
  --private-key "$KEY" \
  --ordinary-update rejected \
  --publisher-app-update accepted
```

This writes `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`
from live API state. The artifact carries **no identifier at all** — not the App
ID, installation ID, ruleset ID, or account ID — only structural booleans and
the asserted `identities_agree` verdict (AC36 clause 6). The two canary outcomes
are passed explicitly rather than inferred, so the evidence cannot confirm
itself from a settings read.

It does record one thing that is not a structural boolean: `repo`, the
`owner/name` you passed above. That is the **subject** of every observation in
the file rather than an observation itself, and the lint refuses an artifact
whose `repo` differs from the `repo` in `.github/claude-plugin-publish-control.json`.
If you are standing this control up in another repository you will already have
set that field — see § *Before you start*; this capture is what replaces the
placeholder evidence you decommissioned there. A repository name is a public path, not one of the
internal identifiers the paragraph above keeps out.

The key is needed because the installation read is App-authenticated. There is no
user-token route to it: `gh`'s OAuth token is refused by `/user/installations`
(403), and `/repos/{repo}/installation` is App-only (404). The tool signs a
ten-minute JWT, reads the installation, and keeps the key nowhere.

Once this has run and the lint below is green, the local key has no further use
— CI reads its own copy from the environment secret:

```bash
rm "$KEY"
```

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
