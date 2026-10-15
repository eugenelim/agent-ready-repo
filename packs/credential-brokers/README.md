# Credential Brokers

Your agent can use skills that call signed-in services while your tokens stay out of the repository and out of the chat.

## Install

Install it once for your user account:

```bash
agentbundle install --pack credential-brokers
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install credential-brokers@agent-ready-repo
```

## What your agent can do

- Run credentialed skills, such as Jira or Figma, with tokens it never sees.
- Walk you through storing each key a skill needs, one prompt at a time.
- Keep each secret in your OS keychain, or in a private file on Linux.
- Reuse a corporate SSO session for skills that sign in through a browser.
- Let you add or rotate a key at any time.

## Skills

- **`credential-setup`** — An interactive setup that prompts you for each key a credentialed skill declares and stores it in the safest place available. You start it yourself.

You also get two helpers that skills call, not you: `credbroker`, a Python library that resolves credentials in-process, and `sso-broker`, which handles SSO cookie sessions.

## Works with

Works with Claude Code, Codex, Copilot, Kiro IDE, Cursor, and Gemini CLI. [Atlassian](../atlassian/README.md), [Figma](../figma/README.md), and [Linear](../linear/README.md) require it for their tokens. To build your own credentialed skill, see [Add credentials to a skill](../../guides/credential-brokers/how-to/add-a-credentialed-skill.md).

## Questions

**How do I store a token?** Install a credentialed pack, then say "set up credentials". The skill prompts you, and you type each value.

**Does the agent ever see my token?** No. Setup runs for you, not the agent, and the value is not echoed into the transcript. The setup script refuses `--token`, `--pat`, and `--password` flags, so a secret never goes on the command line.

**Where is it stored?** The OS keychain on macOS and Windows. On Linux it is a `0600` file at `~/.agentbundle/credentials.env`. Skills also accept an environment variable first.

**Do I call the broker myself?** No. A credentialed skill resolves its token through it once setup has stored it.

## Details

Scope: user (default), repo · Version: 0.3.4 · Source: [packs/credential-brokers](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/credential-brokers)
