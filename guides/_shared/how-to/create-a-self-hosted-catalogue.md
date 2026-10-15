---
title: "Host on Artifactory"
summary: "Let your organization install from a catalogue you host on JFrog Artifactory."
pack: _shared
kind: how-to
---

# Host on Artifactory

Create two Artifactory repositories and two identities: one publishes the catalogue and a different one reads it.

## Create the repositories

Create a PyPI repository for the `agentbundle` wheel and a Generic repository for catalogue archives, their SHA256 sidecars (checksum files), and channel descriptors. Make the release paths immutable, and allow replacement only under `channels/`, because a channel descriptor is the pointer to the current release.

## Create two identities

Give the publisher write access only to the Generic repository paths it needs, and use a restricted service identity or a CI-issued token instead of a personal one. Give readers a separate read-only identity for the channel and release paths. A login for one does not authenticate the other.

## Package the catalogue

Build the archive and its checksum in a job that holds no publishing secret:

```bash
agentbundle catalogue package --root . --bundle platform --release 1.0.0 --channel stable --output dist/
```

This writes the archive, its `.sha256` file, and the channel descriptor under `dist/`.

## Upload in order

In a protected release job, use the JFrog CLI to upload the archive, then the checksum, then `channels/<channel>.json`. Upload the descriptor last, because it makes the release visible to readers.

## Sign in to read

Readers sign in with the JFrog CLI, which saves a profile that `agentbundle` finds by matching the catalogue's URL:

```bash
jf login
```

`agentbundle` tries a bearer token in `AGENTBUNDLE_HTTP_BEARER_TOKEN`, then a JFrog CLI profile, then a `.netrc` entry, then anonymous access, and stops at the first one that is configured. A configured provider that is broken fails the install and does not fall back.

## Install without network access

On a machine that cannot reach Artifactory, pass a local catalogue and turn off remote lookup:

```bash
AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue
```

This skips remote lookup, and it does not make a protected remote catalogue available offline.

Next, [roll out across an enterprise](roll-out-agent-ready-repo-across-an-enterprise.md). To derive your catalogue from an existing one, see [Self-hosted catalogue init and sync](../reference/self-hosted-catalogue-init.md).
