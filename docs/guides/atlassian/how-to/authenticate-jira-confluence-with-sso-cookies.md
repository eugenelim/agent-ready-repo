# Authenticate Jira / Confluence with an SSO web session

On an Atlassian **Data Center** instance fronted by corporate SSO where personal
access tokens are blocked, [`jira`](../../../../packs/atlassian/.apm/skills/jira/)
reads and [`confluence-crawler`](../../../../packs/atlassian/.apm/skills/confluence-crawler/)
can authenticate by a captured web session (a cookie jar) instead of a token. This
is the `auth: sso-cookie` path (RFC-0035); both skills keep a `creds` (token)
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

## 2. Register the session (once, per developer)

```bash
python scripts/setup_sso.py        # in the jira (or confluence-crawler) skill dir
```

This validates the config, then drives `sso-broker register`, which opens a headed
browser for interactive SSO sign-in and captures the session into the broker's
`0600` store. Re-run it whenever the session expires (a `401` from a read tells
you to). The agent never runs this for you — it's an interactive browser flow.

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

## Upgrading a pre-baked config without losing your edits

`references/sso-config.toml` is upstream-owned but locally edited — exactly the
case the [`adapt-to-project`](../../core/how-to/adapt-to-project.md) **class-2
`.upstream` companion merge** handles. When a later catalogue release ships a new
upstream `sso-config.toml`, install writes it alongside yours as a `.upstream`
companion rather than clobbering your instance config; `adapt-to-project` then
walks you through merging any new upstream keys into your edited file. So an
org's pre-baked config survives upgrades — you reconcile new connection-param
keys deliberately, you don't lose them.
