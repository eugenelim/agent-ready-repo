# Adapter contract, distribution, and construction-fixture survey

> Discipline: applied practitioner-pattern survey

**Topic:** Private executable website-adapter packaging, installation,
discovery, versioning, trust, development, and deterministic reference
fixtures.
**Checked:** 2026-08-14
**Purpose:** Ground RFC-0088's provider-pack, adapter, and distribution
decisions without creating a second catalogue.

**Confidence legend:** **high** means a current official primary contract or
direct destination contract supports the claim; **moderate** means the
conclusion composes several sources or is an architectural analogy; **low**
means sources conflict. Confidence is not local spike validation or RFC
acceptance.

## Ecosystem patterns

### Editor extensions

Editor extensions commonly separate a declarative manifest, host compatibility,
immutable package, install decision, activation, and publisher trust. Extension
code still runs with broad host authority; capability metadata informs review
but does not sandbox code. [high]

Sources: [VS Code extension manifest](https://code.visualstudio.com/api/references/extension-manifest),
[VSIX packaging](https://code.visualstudio.com/api/working-with-extensions/publishing-extension),
[extension runtime security](https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security).

### Infrastructure providers

Terraform separates its runtime plugin protocol from its registry protocol and
supports exact selections, hashes, private registries, and filesystem mirrors.
That separation demonstrates that an executable contract does not require a
new remote marketplace. Integrity identifies bytes; it does not establish that
the code is trustworthy. [high]

Sources: [plugin protocol](https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol),
[provider registry protocol](https://developer.hashicorp.com/terraform/internals/provider-registry-protocol),
[dependency lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock).

### Account-oriented integrations

Home Assistant separates integration code from configuration entries and
supports multiple configured instances, migrations, scaffolding, and
conformance. This supports separate adapter code, connection bindings, and
resource/configuration generations. [high]

Sources: [integration structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/),
[manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/),
[config flows](https://developers.home-assistant.io/docs/core/integration/config_flow/).

### npm packages

npm supplies private packages, registry authentication, semantic versions, and
lockfiles. It also adds registry credentials, release administration, install
supply-chain exposure, and a public API commitment. It is a possible future
transport, not a prerequisite for AgentBundle consumers using a process
contract. [high]

Sources: [private packages](https://docs.npmjs.com/about-private-packages),
[private publication](https://docs.npmjs.com/creating-and-publishing-private-packages).

## Destination repository fit

The destination's `pack.toml` schema already supports:

- normal pack identity and soft categories;
- open `[pack.metadata.<namespace>]` data;
- required pack dependencies;
- declared npm runtime dependencies; and
- user-scope installation and adapter projection.

It does not provide a `pack.type`, cross-catalogue dependency resolution, Node
module linking between packs, or a remote adapter registry. Required dependency
versions use `^X.Y`. The provider contract must match those facts.

The primary extension is therefore a provider pack, not a bare adapter. The
pack carries user-facing skills, self-contained deterministic scripts, setup
guidance, a required `web-pilot` dependency, and normally a candidate adapter
artifact. Installing the pack makes that candidate available; it does not admit
or activate the executable digest.

## Packaging options

| Model | Upgrade/rollback | Trust posture | Use |
| --- | --- | --- | --- |
| Mutable local folder | Weak | Executes mutable code | Development link only |
| Provider pack with bundled candidate | Pack version plus independent digest activation | Exact reviewed artifact | Recommended product shape |
| Git source | Strong source history | Checkout is mutable | Source location only |
| Private npm package | Strong SemVer/lock | Registry/install supply chain | Future transport |
| Declarative recipe | Runtime-owned | Narrowest executable surface | Supported restricted tier |
| Self-contained ESM artifact | Exact digest | Trusted code in constrained host | Required capable tier |
| Local registry pointing to external paths | Target may change | Time-of-check/time-of-use gap | Reject |
| New remote catalogue | Central discovery | New publisher/update trust system | Reject initially |
| No extension contract | No new machinery | Every site couples to foundation releases | Reject |

## Recommended artifact lifecycle

1. Package a self-contained artifact from source.
2. Parse and validate the inert manifest and schemas without loading code.
3. Reject traversal, symlinks, native add-ons, install scripts, remote schemas, and unexpected executables.
4. Compute and display the exact digest plus behavior/schema/origin/method/trust diff.
5. Obtain approval before any executable conformance or health code runs.
6. Stage, rehash, mark complete, and atomically finalize a disabled artifact.
7. Run synthetic conformance in the constrained child host.
8. Authorize validation-only connection setup.
9. Confirm live identity and resources.
10. Obtain a separate consumer behavior activation.
11. Retain the prior digest and configuration generation for rollback.

Normal jobs execute only exact installed digests. A failed conformance or live
candidate health check leaves existing activations unchanged.

## Why a second catalogue is not required

An adapter runtime needs an artifact format, manifest, compatibility handshake,
installer, activation record, and developer workflow. It does not need search,
publisher namespaces, a remote index, automatic updates, or a marketplace.

Public or private Git can host provider-pack and adapter source. The existing
AgentBundle catalogue distributes provider packs. Each machine explicitly
packages, inspects, admits, and activates immutable adapter artifacts. A local
`registry.json` is an installation database, not a catalogue.

A future distribution RFC requires independent publishers needing discovery,
multiple users needing centralized approval or revocation, a non-AgentBundle
consumer, or demonstrated operational failure of direct installation. Its first
option is carrying immutable artifacts through the existing catalogue.

## Execution boundary

The manifest must be readable before code executes. Capable execution loads the
exact ESM digest in a child Node host with a sanitized environment, no inherited
secrets, no child-process/native-addon grant, constrained filesystem/network
intent, and host-supplied Playwright objects. These controls reduce mistakes;
they do not sandbox malicious code running as the same operating-system user.

Node's Permission Model is expressly defense in depth. A declarative adapter
tier can make a stronger restriction claim because the runtime interprets an
allowlisted operation set. It must remain separate from the native capable ABI.

Source: [Node Permission Model](https://nodejs.org/api/permissions.html).

## Development and repair workflow

The eventual workflow should separate these actions:

- scaffold source and copied/generated contract types;
- enable a visibly marked mutable development link;
- open the bound browser for supervised repair;
- capture local structural/network/download metadata without auth headers or raw bodies;
- create an explicit, redacted, user-reviewed model projection;
- run contract and synthetic tests;
- package an immutable candidate;
- inspect and install it disabled;
- activate per consumer; and
- roll back without changing connection aliases or profiles.

No probe, model-generated patch, or development link can activate itself.

## Reference fixture

The required reference is a synthetic authenticated `example-service`. It must
exercise login handoff, same-context continuation, validation/behavior
separation, persistent reuse, wrong identity, resource discovery and consent,
expiry, drift, downloads, crash, contention, upgrade, rollback, and disconnect.

Any real-site reference is post-acceptance work under a separate RFC. It must be
inside the software-delivery charter domain, have a safe test environment, use
supported APIs/exports before internal endpoints, and pass terms/rate-limit
review. Failure to find one does not block the synthetic foundation contract.

## Known unknowns

- Whether plain self-contained ESM avoids a bundler dependency.
- Whether Node permissions compose with the selected module/IPC shape on each platform.
- Whether users need a shared adapter distribution index.
- Whether builds can be made reproducible; source/ref, recipe, materials,
  toolchain, lockfile digest, and reproducibility status remain mandatory even
  when the answer is no.
- Which future website changes will break an adapter.
