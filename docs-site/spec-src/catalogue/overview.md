This page is the draft of the agentbundle catalogue specification. A catalogue is a repository that publishes packs and profiles for agents to install. The specification is the set of contract files below, and a catalogue is checked against them.

The `draft/` section tracks `main`, so it changes with every merge. It is not a release. No released version is published yet.

## What a catalogue must contain

A catalogue holds these parts, each checked against one member contract below:

- A `catalogue.toml` that names the catalogue.
- Packs, each with a `pack.toml`, and skills with `SKILL.md` frontmatter.
- Profiles, which bundle packs for install.
- A `catalogue-index` file when the catalogue is published as an index.
- A `catalogue-manifest.json` inside a catalogue archive.

The [starter catalogue](https://github.com/eugenelim/agent-ready-repo/tree/main/packages/agentbundle/agentbundle/_data/catalogue-scaffold) that `agentbundle catalogue init` writes shows a working layout. [Create a catalogue](/agent-ready-repo/docs/guides/_shared/how-to/create-a-catalogue/) walks through running it.

## How a catalogue is checked

Three commands check a catalogue:

- `agentbundle catalogue lint` checks the source files against the schemas.
- `agentbundle catalogue verify` checks the catalogue as a whole.
- `agentbundle catalogue package` builds the archive and its manifest.

Two checks live only in code and have no schema here. The archive checks confirm that a packaged archive matches its own manifest, with every file present and every digest correct; their IDs start with `CAT-V-ARC-`. The `JOURNEY.md` validator checks a pack's journey file. The [JOURNEY.md format guide](/agent-ready-repo/docs/guides/_shared/reference/pack-journey-format/) describes that file. It is informative, not part of this specification.

## Member contracts

Each section below says what one contract is for. A JSON member's page has a field table, a TOML member's page shows the whole file, and the raw file is the source of truth.

## pack-schema-json

Describes the `pack.toml` file that gives a pack its metadata and adapter settings.

## catalogue-schema-json

Describes the `catalogue.toml` file that configures a catalogue.

## profile-schema-json

Describes a profile, a named bundle of packs that installs together.

## skill-schema-json

Describes the frontmatter at the top of a `SKILL.md` file.

## skill-manifest-schema-json

Describes the manifest that lists a skill's files.

## target-vocab-toml

Lists the per-target limits and patterns that pack metadata is checked against.

## catalogue-index-schema-json

Describes the neutral index that lists a catalogue's packs for tools that read a catalogue without installing it.

## adapter-toml

Lists how each kind of content projects into each supported agent tool.

## adapter-schema-json

Describes the shape of `adapter.toml`.

## catalogue-manifest-schema-json

Describes the `catalogue-manifest.json` that `agentbundle catalogue package` writes into an archive. It covers shape only.
