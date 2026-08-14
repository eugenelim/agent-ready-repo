---
title: "Authenticate Jira and Confluence with an SSO web session"
summary: "Configure read-only Jira and Confluence skills to authenticate through a securely stored corporate SSO browser session."
pack: atlassian
kind: how-to
---

# Authenticate Jira / Confluence with an SSO web session

**Use this when:** Your Atlassian Data Center instance blocks personal access tokens and requires corporate SSO sign-in for Jira reads or Confluence space crawls.
**Prerequisites:** The `jira` or `confluence-crawler` skill installed; an enterprise-edited `references/sso-config.toml` pointing at your corporate instance.
**Result:** A registered SSO session in the broker's secured store so both skills authenticate via captured web session instead of a token — and a `jira.py check` that re-establishes it, headlessly, when it expires.

On an Atlassian **Data Center** instance fronted by corporate SSO where personal
access tokens are blocked, [`jira`](../../../packs/atlassian/.apm/skills/jira/)
reads and [`confluence-crawler`](../../../packs/atlassian/.apm/skills/confluence-crawler/)
can authenticate by a captured web session (a cookie jar) instead of a token. This
is the `auth: sso-cookie` path; both skills keep a `creds` (token)
fallback, so nothing changes for token users.

> **Scope.** Data Center only, **reads only** (JQL search, get issue/project/user;
> Confluence space crawl). Writes over the cookie path are refused pending XSRF
> design. Cloud is out of scope — use a token there.

## 1. Pre-bake the instance config (once, per org)

Each skill ships `references/sso-config.toml` placeholder-shaped (`auth_default =
"creds"`, `*.invalid` hosts). An enterprise edits it to point at the corporate
instance and flips the default:

```toml
auth_default = "sso-cookie"

[sso]
profile = "jira"
base_url = "https://jira.corp.example.com"          # https only
login_url = "https://sso.corp.example.com/login"
success_url_pattern = "https://jira.corp.example.com/secure/Dashboard.jspa"
cookie_domains = ["corp.example.com"]                # the jar is confined to these
validation_endpoint = "/rest/api/2/myself"           # root-relative
```

Distribute this as a pack customization so a developer installs the pack already
pointed at your instance. The config carries **no secrets** — only connection
parameters; the session cookie never lives here.

`profile` is confined to `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` — it becomes a
filename and a keychain entry name — and Windows reserved device names (`CON`,
`NUL`, `COM1`…) are refused with or without an extension.

## 2. Register the session (once, per developer)

```bash
python scripts/jira.py check --register        # in the jira skill dir
```

One command: it captures the session and then runs the check. A browser opens
for you to sign in, and the destination host is printed to stderr first.

**Run this yourself.** The agent will relay the command as text; it never
invokes it. Everything after this is automatic.

Before opening anything, `check --register` asks your instance where it sends
users to sign in and compares that against `login_url`. On a mismatch it refuses
with both hosts named and no browser. **It does not always verify.** Where
`login_url` sits on the *same host* as `base_url` — SP-initiated SAML, which is
the majority Data Center configuration — the check short-circuits and confirms
nothing. Treat `check --register` as the best available first-run path, not as a
guarantee.

`scripts/setup_sso.py` remains, for exactly two cases:

- a **scripted pre-bake**, where an org registers profiles without a person present;
- when `check --register` **refuses** because it cannot confirm the destination —
  a host mismatch you know to be correct, or a topology where nothing resolves.

It performs **no** destination check at all. It is safe only because you type it.

**`confluence-crawler` registers through `setup_sso.py`.** It has no
`--register` verb and no self-healing `check` yet; both skills share one broker
store, so registering the profile from either skill serves both. Registering via
`jira.py check --register` is the better route where the profile is shared.

### Hardening: keeping the agent away from `--register` (Claude Code only)

If you want belt as well as braces, a Claude Code user can add a deny rule in
**`~/.claude/settings.json`** — the user-scope file, not the repo's:

```json
{ "permissions": { "deny": ["Bash(python scripts/jira.py check --register*)"] } }
```

It must live in your home directory because anything inside the repo
(`.claude/settings.local.json`) is a file the agent can edit.

**This is belt, not a boundary.** It reduces accidental invocation by an erring
agent. It does **not** put first capture out of an agent's reach: an agent with
shell access can invoke `~/.agentbundle/bin/sso-broker.py register` directly,
bypassing every command-level rule. Only privilege separation would support an
out-of-reach claim, and none ships today.

`kiro-ide`, `codex`, `copilot`, `cursor` and `gemini` have **no equivalent
per-command control** — they offer coarse sandbox levels or tool-name
allow-lists, not per-invocation rules. On those, the skill rules are the only
layer.

## 3. Use the skills normally

```bash
python scripts/jira.py check                         # confirms the session
python scripts/jira.py search 'project = ABC' --limit 20
python scripts/crawl_space.py --space ENG
```

On the cookie path the skill attaches the confined jar to its HTTP client, sends
**no** `Authorization` header, and honors your corporate proxy and CA bundle
(`HTTPS_PROXY` / `NO_PROXY`, `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`). The session
cookie is a bearer secret — the skill resolves it through the broker and never
prints it.

### `check` self-heals an expired session

Your app session expires long before your corporate SSO session does. When it
has, `jira.py check` re-establishes it and retries, in the same command — no
second step and **no browser**: the recapture runs headless, and it takes no
sign-in destination, so nothing an agent does can steer where it goes.

Two cases where it stops instead:

| What happened | What you see |
|---|---|
| Your **IdP** session has expired too — typically first use of the day | exit 2 and a message naming `check --register`. No login page is opened. Run the command it names. |
| No session was ever captured on this machine | exit 2 naming the same command. |

Only `check` does this. Every other subcommand behaves exactly as before, and
`check` on the token path is unchanged.

`--insecure` is a global flag (`jira.py --insecure check`) and is **inert** on
the cookie path — the session cookie is a bearer secret, so TLS verification
stays on. `check` says so rather than letting you believe otherwise.

## Upgrading a pre-baked config without losing your edits

`references/sso-config.toml` is upstream-owned but locally edited — exactly the
case the [`adapt-to-project`](../../core/how-to/adapt-to-project.md) **class-2
`.upstream` companion merge** handles. When a later catalogue release ships a new
upstream `sso-config.toml`, install writes it alongside yours as a `.upstream`
companion rather than clobbering your instance config; `adapt-to-project` then
walks you through merging any new upstream keys into your edited file. So an
org's pre-baked config survives upgrades — you reconcile new connection-param
keys deliberately, you don't lose them.
