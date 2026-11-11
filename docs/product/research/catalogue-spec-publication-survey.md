# Survey: how platforms publish a versioned specification with stable schema URLs

> Discipline: applied (practitioner-pattern survey)

- **Mode:** desk-research `applied`
- **Run date:** 2026-10-21
- **Feeds:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) and the Draft intent `catalogue-specification-publication`

## The question

The agentbundle catalogue contracts sit in a mixed `contracts/` folder. No schema
resolves at a real URL, and only `adapter.toml` carries a version. This survey asks
how comparable platforms publish a specification and its schemas, so RFC-0109 can
choose a home, a URL and version scheme, an `$id` scheme, and a drift check.

It covers ten platforms and tools: the Model Context Protocol (MCP), OpenAPI, JSON
Schema, SchemaStore, Agent Skills, Agent Plugins, Development Containers, the
Kubernetes API reference, CloudEvents, and two docs-versioning tools (Docusaurus and
mike).

## How sources were counted

Every source is a primary one: the project's own site, spec, or repository. Each
project counts once, however many of its pages are cited. Kubernetes and CloudEvents
are both CNCF projects, but they have separate maintainers and policies, so they
count as two. Docusaurus and mike are tool documentation about their own tools, so
findings that rest on them carry the `vendor-blogged` downgrade.

Each quote was fetched on 2026-10-21. Five URLs were also checked for an HTTP 200
response that day; those checks are marked "served".

## Findings

### 1. Where the specification lives

- **Each platform below publishes its specification on a website it controls,
  not on a Git file view.** [high] CloudEvents is the exception in this set: its
  specification is read from GitHub release tags.
  - MCP: `modelcontextprotocol.io/specification`, built from one repository that
    "contains the" specification, the protocol schema and the official docs.
  - OpenAPI: spec.openapis.org hosts "authoritative _source-of-truth_ HTML
    renderings". The GitHub repository "contains the Markdown sources".
  - JSON Schema: json-schema.org, with each version at a dated path such as
    `/draft/2020-12/`.
  - Agent Plugins: agent-plugins.org serves the schemas. The repository README is "a
    non-normative introduction".
  - Kubernetes: the reference lives under `kubernetes.io/docs/reference/`.
  - Dev Containers and Agent Skills: `containers.dev` and `agentskills.io/specification`.
- **A dedicated spec site and a section of the docs site are both common. A separate
  repository is common but not required.** [moderate] Downgrade: heterogeneity.
  OpenAPI, JSON Schema and Agent Plugins run a dedicated spec host. MCP, Kubernetes,
  Dev Containers and Agent Skills put the specification inside their documentation
  site. MCP keeps the spec, schema and docs in one repository.

### 2. URL and version scheme

- **Each released version has its own path, and that path does not change.** [high]
  - MCP: `/specification/2026-07-28/`, with schemas in `schema/2026-07-28/`. Final
    versions "will not be changed".
  - Agent Plugins: `schemas/1.0.0/` and `schemas/1.1.0/` side by side. "1.0.0 is the
    current published release" and "1.1.0 is a working draft".
  - OpenAPI: `spec.openapis.org/oas/v3.1.1.html`.
  - JSON Schema: `/draft/2020-12/`, with older drafts still listed.
  - Kubernetes: the current release at `kubernetes.io`, and the four previous
    releases on frozen hosts such as `v1-36.docs.kubernetes.io`.
- **Semantic versions and date versions are both in wide use. Neither is the
  standard.** [high]
  - Date: MCP uses "`YYYY-MM-DD`, to indicate the last date backwards incompatible
    changes were made", and the version "will *not* be incremented" for compatible
    changes. JSON Schema switched to date names: "The current version is _2020-12_".
  - Semver: OpenAPI (3.1.1), Agent Plugins (1.0.0), CloudEvents (`ce@v1.0.2`).
- **A patch number is not part of what tools match on.** [high]
  - OpenAPI: "The patch version _SHOULD NOT_ be considered by tooling, making no
    distinction between `3.1.0` and `3.1.1`".
  - CloudEvents: `specversion` carries "only … the 'major' and 'minor' version
    numbers", so "'patch' changes to the specification" do not change it.
  - Docusaurus, on versioning docs for a patch release: "You probably shouldn't".
- **A `latest` alias is a convenience for people. Tools pin a version.** [high]
  - JSON-Schema-Test-Suite: `latest` "is a symbolic link which points to the directory
    which is the most recent release".
  - mike: "Each alias creates a symbolic link to the base directory of the real
    version of the docs".
  - Docusaurus: the latest version "Usually has path `/docs`". Kubernetes: the apex
    host is the current release.
  - SchemaStore: the catalogue `url` field holds the latest version, and a `versions`
    map lists each pinned one.

### 3. How `$id` maps to a served URL

- **An `$id` is an identifier, not a promise that something can be fetched.** [high]
  - JSON Schema core § 8.2.1: the URI "is an identifier and not necessarily a network
    locator". § 8.2.3: implementations "SHOULD NOT assume they should perform a
    network operation when they encounter a network-addressable URI".
  - JSON Schema structuring guide: identifiers "are not necessarily
    network-addressable", and "it's recommended that you always use an absolute URI
    when declaring a base URI with `$id`".
- **Where a platform does serve its schemas, the `$id` is the served URL.** [high]
  - Agent Plugins: `$id` `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
    Served.
  - OpenAPI: `$id` `https://spec.openapis.org/oas/3.1/schema/2022-10-07`. Served.
  - JSON Schema: `https://json-schema.org/draft/2020-12/schema`. Served as
    `application/schema+json`.
- **Many specifications publish schemas with no `$id` at all.** [moderate] Downgrade:
  indirectness (the absence is a fact, not a stated policy). The MCP `schema.json`,
  the Dev Containers base schema, and the CloudEvents JSON schema all start with
  `$schema` and no `$id`.

### 4. Whether changing an `$id` or URL is a breaking change

- **A published schema URL is treated as permanent. A new identity is minted rather
  than an old one moved.** [moderate] Downgrade: indirectness (only SchemaStore states
  it as a rule).
  - SchemaStore: "When renaming a schema name, the old version must continue to exist.
    Otherwise, all references to it will break." Moving a schema to self-hosting means
    keeping the original file and pointing it at the new home with `$ref`.
  - OpenAPI mints a new dated `$id` for each schema iteration (`…/schema/2022-10-07`)
    rather than changing the bytes behind an existing one.
  - Kubernetes removes API elements only by "incrementing the version of the API
    group".

### 5. Spec version and implementation version

- **The specification version moves on its own line. Implementations say which
  specification versions they support.** [high]
  - MCP: every request declares a protocol version. Servers reply with the versions
    they support, and "Clients and servers **MAY** support multiple protocol versions
    simultaneously".
  - CloudEvents: each SDK is its own repository, with no SDK-to-spec version mapping.
  - Dev Containers: `devcontainers/cli` is the "reference implementation", with no
    version coupling stated.
  - Kubernetes: the API track (`v1`, `v1beta1`) is separate from the release number
    (1.37). Deprecation windows count releases.

### 6. Generated reference pages and narrative prose

- **Field reference is generated from the machine contract. Concepts and rules are
  written by hand.** [moderate] Downgrade: heterogeneity (projects differ on which one
  wins when they disagree).
  - Kubernetes: the reference "is built from the Kubernetes OpenAPI spec using the
    kubernetes-sigs/reference-docs generation code".
  - MCP: one Schema Reference page per version, from a schema "defined in TypeScript
    first". How that page is built is not documented.
  - OpenAPI takes the other side: its JSON Schema is "non-authoritative", and the prose
    wins.
  - Agent Skills is prose plus a field table, with no published schema.

### 7. Conformance and test suites

- **A conformance suite is versioned with the specification, and a reference
  validator ships beside it.** [moderate] Downgrade: heterogeneity.
  - JSON-Schema-Test-Suite: a "subdirectory for each released version", with frozen
    old drafts.
  - MCP conformance: a test framework filtered by `--spec-version`, with a `draft`
    suite.
  - Agent Skills: `skills-ref validate ./my-skill`, inside the spec repository.
- **An unowned suite decays.** [low] Downgrade: single source. The CloudEvents
  conformance tool "has been archived due to inactivity".

### 8. The cost of versioned documentation

- **Every frozen version is a copy someone keeps building. Projects keep few of
  them.** [moderate] Downgrade: vendor-blogged.
  - Docusaurus: "If your documentation rarely changes, don't add versioning", and
    "try to keep the number of your versions below 10".
  - mike: "once you've generated your docs for a particular version, you should never
    need to touch that version again".
  - Kubernetes keeps "the current version of Kubernetes and the four previous
    versions".

## What this means for agentbundle [synthesis]

- A section of the existing docs site is enough. MCP and Kubernetes publish there, so
  a separate spec repository is not a precondition (findings 1 and 5).
- Publish each released version at an immutable path, put the same absolute URL in
  `$id`, and offer `latest` only as a human alias (findings 2 and 3).
- Keep the patch number out of the path and out of `$id` (finding 2).
- Treat an `$id`, once published, as permanent. Mint a new versioned `$id` instead of
  changing an old one (finding 4).
- Version the catalogue specification on its own line. The CLI reports which version
  it enforces (finding 5).
- Generate field tables from the schemas. Keep narrative for concepts, and have it
  link to the schema rather than restate fields (finding 6). This repository already
  makes `contracts/` normative (RFC-0076 D1), which is the Kubernetes side of the
  split, not the OpenAPI side.
- Publish few versions. Cut a version only when member bytes change (finding 8).

## Known unknowns

- **Known-unknown:** whether `eugenelim.github.io/agent-ready-repo` URLs redirect to a
  custom domain if one is added later. The GitHub Pages docs fetched here say a user
  site's custom domain is used for its project sites. They do not say the old
  `github.io` paths redirect. Would be closed by a test on a scratch repository or an
  explicit GitHub statement.
- **Known-unknown:** whether any adopter tool registers these schemas by their current
  bare-filename `$id` (`pack.schema.json`). No catalogue specification member
  uses a cross-file `$ref`. Would be closed by asking adopters or searching public code for
  the bare IDs.
- **Known-unknown:** how MCP builds its Schema Reference page, and how mature the
  `starlight-versions` plugin is for a Starlight site. Would be closed by reading the
  MCP docs build and the plugin's versioning guide.
- **Unknowable:** how many adopters will pin a versioned URL rather than `latest`.
  Why not: the behaviour depends on adoption that has not happened yet.
- **Inference:** GitHub Pages serves static files and has no server-side redirect
  setting, so a `latest` alias for a JSON file must be a copy, not a redirect. HTML
  pages can redirect with a meta refresh.

## Sources

- MCP versioning: <https://modelcontextprotocol.io/specification/versioning>
- MCP repository: <https://github.com/modelcontextprotocol/modelcontextprotocol>
- MCP conformance: <https://github.com/modelcontextprotocol/conformance>
- OpenAPI 3.1.1: <https://spec.openapis.org/oas/v3.1.1.html>
- OpenAPI 3.1 schema: <https://spec.openapis.org/oas/3.1/schema/2022-10-07>
- OpenAPI repository: <https://github.com/OAI/OpenAPI-Specification>
- JSON Schema core 2020-12: <https://json-schema.org/draft/2020-12/json-schema-core>
- JSON Schema structuring guide: <https://json-schema.org/understanding-json-schema/structuring>
- JSON Schema specification index: <https://json-schema.org/specification>
- JSON-Schema-Test-Suite: <https://github.com/json-schema-org/JSON-Schema-Test-Suite>
- SchemaStore contributing guide: <https://github.com/SchemaStore/schemastore/blob/master/CONTRIBUTING.md>
- Agent Skills specification: <https://agentskills.io/specification>
- Agent Plugins repository: <https://github.com/agentplugins/agent-plugins-spec>
- Agent Plugins 1.0.0 schema: <https://agent-plugins.org/schemas/1.0.0/plugin.schema.json>
- Dev Containers spec: <https://containers.dev/implementors/spec/> and <https://github.com/devcontainers/spec>
- Kubernetes reference generation: <https://kubernetes.io/docs/contribute/generate-ref-docs/kubernetes-api/>
- Kubernetes doc versions: <https://kubernetes.io/docs/home/supported-doc-versions/>
- Kubernetes deprecation policy: <https://kubernetes.io/docs/reference/using-api/deprecation-policy/>
- CloudEvents spec: <https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md>
- CloudEvents conformance: <https://github.com/cloudevents/conformance>
- Docusaurus versioning: <https://docusaurus.io/docs/versioning>
- mike: <https://github.com/jimporter/mike>
- GitHub Pages custom domains: <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages>
