---
title: "Configure agentbundle"
summary: "Set a default agent and catalogue, and sign in to a protected catalogue."
pack: _shared
kind: how-to
aliases:
  - guides/_shared/how-to/configure-adapter
---

# Configure agentbundle

Save the agent and catalogue you use, so you stop passing them on every install.

## Set your agent

Save a default agent:

```bash
agentbundle config set adapter cursor
```

Every new install now targets Cursor unless you pass `--adapter`. An upgrade keeps the agent a pack was installed with.

## Set your catalogue

Install from your own catalogue by default:

```bash
agentbundle config set source git+https://github.com/<owner>/<catalogue>
```

Leave this unset to use your organization's default or the public catalogue.

## Check your settings

See each setting and where it comes from:

```bash
agentbundle config get
```

`agentbundle config unset adapter` removes a setting, and `agentbundle config path` shows where the file lives.

## Sign in to a protected catalogue

For a catalogue that needs a sign-in, set a token for the session:

```bash
export AGENTBUNDLE_HTTP_BEARER_TOKEN=<token>
```

`agentbundle` also uses a JFrog CLI profile or a `~/.netrc` entry when it finds one.

The [command reference](../reference/agentbundle.md#environment-variables) lists every setting, environment variable, and sign-in rule.
