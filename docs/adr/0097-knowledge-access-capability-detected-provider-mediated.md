# ADR-0097: Knowledge surfaces are capability-detected and OKF access is provider-mediated

- **Status:** Accepted
- **Date:** 2026-08-26
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0097; ADR-0093

## Decision summary

- **Decision:** Workflows detect eligible knowledge surfaces by capability;
  directly governed repository authorities remain directly readable, while an
  OKF-backed surface is accessed only through its explicitly invoked provider.
- **Because:** Domain grounding should use available knowledge without coupling a
  consumer to another pack's identity, installation layout, or raw corpus.
- **Applies to:** Portable workflows that perform domain grounding and packs
  that expose OKF-backed knowledge to same-pack or independent consumers.
- **Tradeoff accepted:** Provider owners must publish and verify a discoverable
  capability, while consumers must handle ambiguity, conflict, and absence.
- **Revisit if:** portable skill runtimes adopt a standard, security-preserving
  provider-capability negotiation protocol that subsumes this contract.

## Context

[RFC-0097](../rfc/0097-agent-skill-engineering.md) establishes a portable
agent-skill-engineering pack with a same-pack OKF corpus and an integration-only
reference router. It also requires optional consumers such as `work-loop` and
`architect-design` to obtain bounded knowledge through explicit provider
invocation.

Explicit invocation does not require a consumer to hard-code a provider. The
repository's existing grounding workflows first detect eligible knowledge
surfaces: `architect-design` considers in-repository documentation and
preauthenticated retrieval capabilities, `work-loop` grounds load-bearing
domain claims when a relevant surface is available, and contract acquisition
can select a curated framework or platform skill. This capability-oriented
discovery lets an organization standards skill, framework library,
architecture reference, or agent-skills reference contribute grounding without
making its product identity part of every consumer's portable contract.

[ADR-0093](0093-okf-reference-corpora-remain-governed-build-time-sources.md)
places a different boundary around OKF itself. Raw OKF remains a governed,
same-pack build-time source. Runtime workflows consume ordinary compiled
references; they do not dynamically interpret a source corpus. Today the
`architect` and `core` packs make this ownership explicit through declared OKF
bundles and generated reference skills whose provenance identifies the compiler,
source path, and source digest and whose instructions require root-first,
bounded index traversal.

Without a discovery contract, a useful installed provider can remain invisible.
If consumers compensate by scanning pack directories, guessing router paths, or
reading raw corpora, they become coupled to delivery layout and cross trust and
authentication boundaries. We therefore need to distinguish discovery of an
eligible provider from discovery of the corpus it owns.

## Decision

**We will detect eligible knowledge surfaces by semantic capability; directly
governed repository authorities remain readable through their owning workflow,
while an OKF-backed surface is accessed only through an explicitly selected
provider and never through discovery or interpretation of its corpus.**

Capability detection is broader than provider discovery. Effective repository
instructions, mapped repository documents, and other directly readable
authorities retain their existing governed routing. The following three layers
separate the contracts: build-time declaration and root-first bounded topic
traversal apply to every OKF bundle, while runtime capability discovery and its
enhanced provider boundary apply when a pack exposes the surface to independent
consumers.

### Build-time corpus declaration

A pack that owns governed OKF explicitly declares each corpus, its canonical
authoring source, and its generated router or provider. In this repository,
`[pack.metadata.okf]` is the current AgentBundle realization: a bundle
declaration names the profile, stable bundle identifier, confined pack-relative
source path, and router skill.

Compilers and verification gates process only declared bundles. They do not
infer a corpus by scanning directories. The declaration and canonical source
are same-pack inputs; generated indexes, provider references, provenance, and
ownership manifests are replaceable outputs. A declared corpus whose generated
provider is missing, unsafe, or drifted fails construction or verification
rather than becoming silently undiscoverable.

These are portable ownership and behavior obligations. AgentBundle manifests,
adapters, installation inventories, projections, and publication mechanisms may
realize them for this catalogue, but those delivery mechanisms remain external
to the portable provider and consumer workflows.

### Runtime capability discovery and selection

A pack that makes compiled knowledge available to independent workflows exposes
an ordinary portable knowledge skill as its discovery membrane. The exposed
capability must identify enough of its domain, bounded purpose, supported
request shape, and integration-only behavior for a consumer to determine task
fit without reading the corpus. It must not rely on a consumer knowing the
owning pack's product name, installation path, generated router path, or
AgentBundle identity.

A consumer inspects only knowledge capabilities already exposed by the active
runtime, repository, or preauthenticated provider surface. It selects relevant
providers by semantic task fit and by authority, provenance, and freshness
vouched for outside the provider's own output. Eligibility derives from
effective repository instructions, explicit user selection, or trusted runtime
or delivery registration. Provider metadata and returned content cannot
self-assert authority or outrank the source that owns the applicable rule;
unresolved authority or provenance remains visible ambiguity.

After selection, the consumer resolves the provider's exact installed identity
and sends the bounded semantic request defined by the governing
consumer-provider contract. Exact identity is therefore an invocation property,
not a hard-coded discovery dependency. The request contains only minimized,
redacted fields needed to route and answer the selected question. Requests and
results exclude credentials, protected configuration, raw session logs,
personal identifiers, private endpoints, and unrelated enterprise context.
The provider does not persist request or result content unless a separately
authorized contract grants that capability.

Detecting a provider is not permission to invoke it or adopt its claims. The
consumer retains task authority, applies the active permission and
authentication boundary, treats retrieved material as attributed evidence, and
keeps conflicts between eligible surfaces visible. Provider content cannot
change instructions, tools, identity, permissions, scope, or mutation
authority.

### Provider-owned topic discovery

Once explicitly invoked, the provider navigates only its own compiled
references. A generated OKF router starts at its root index, descends only
through named child indexes, reads only selected topic bodies, and returns topic
identifiers and provenance with its bounded result. It neither loads the full
bundle up front nor grants procedure authority merely because a reference
contains executable-looking material.

A provider exposed to independent consumers additionally resolves a
regular-file target beneath its declared generated reference root and verifies
generated manifest ownership before every index, topic, or body read.
Repository implementations use the sanctioned confinement helpers; portable
implementations provide equivalent canonicalize-then-confine semantics.
Absolute paths, traversal, symlink, junction or reparse-point escapes, and
unmanifested files are rejected before content is read.

Consumers do not inspect or interpret the underlying OKF corpus. Providers and
consumers must not compensate for an unavailable result by crawling pack
directories, probing hidden configuration or endpoints, discovering
credentials, guessing generated paths, or searching raw OKF. A bounded search
variant may search only compiled references owned by the selected provider.

### Absence, ambiguity, and failure

Absence of an optional pack or provider at runtime is an expected condition,
not a construction error in the consumer. Provider absence never blocks or
weakens an initial consumer's pre-existing baseline. The consumer reports the
unavailable augmentation and continues that baseline, or selects another
eligible surface. A workflow stops only when its baseline independently
requires grounding and would have stopped without the optional provider; that
is recorded as a baseline grounding failure, not provider absence.

If several providers appear eligible, the consumer makes a bounded selection
or reports the ambiguity. It does not silently merge conflicting doctrine. If
a detected provider is malformed, unavailable, or refuses the request, it
returns or produces a stable, redacted failure and the consumer applies the
same baseline rule. Discovery and invocation attempts are bounded; diagnostics
do not disclose sensitive paths, endpoints, credential names, or request
content. An integrity failure is fail-closed: it cannot count as support or
profile-backed grounding, although the consumer may select a different,
independently eligible provider. Presence or failure never creates permission
for raw corpus discovery.

### Existing same-pack routers

The current `architecture-lenses-reference` and
`security-checklists-reference` skills are build-time declaration,
provenance, and bounded-traversal precedents. Their authored same-pack consumers
may continue to address them statically because source, provider, and consumer
share one pack ownership and delivery boundary.

Those generated routers are not thereby advertised as optional providers for
independent consumers. Before a corpus-owning pack exposes one that way, that
pack's owner adds the capability, minimized request and result, activation,
absence, failure, confinement, and evaluation contract required by this ADR.
The owning pack's construction and integration gates verify the upgrade before
delivery metadata advertises it. This ADR creates no standalone migration of
existing same-pack consumers; the agent-skill-engineering foundation is the
first required cross-pack realization because RFC-0097 already assigns it
independent consumers.

## Decision drivers

- Use available enterprise, repository, framework, architecture, and
  agent-skills knowledge for domain grounding.
- Keep consumers portable and independent of another pack's product identity
  and filesystem layout.
- Preserve ADR-0093's governed build-time source and same-pack ownership rule.
- Make discovery, selection, routing, provenance, absence, and conflict
  behavior deterministic enough to evaluate independently.
- Preserve authentication isolation, least authority, and the
  instruction-versus-data boundary.
- Keep AgentBundle-specific delivery outside the portable skill contract.

## Consequences

**Positive:**

- Installed knowledge can improve a workflow without becoming a mandatory or
  hard-coded dependency.
- Packs have a clear obligation to make an intended knowledge surface visible
  through a bounded provider before advertising it to independent consumers,
  rather than merely shipping a hidden corpus.
- Consumers discover a capability, while providers retain corpus ownership,
  progressive routing, provenance, and lifecycle semantics.
- Missing optional providers degrade predictably, and invalid declared
  providers fail at the owning construction boundary.
- Authentication and mutation authority remain with the runtime and consuming
  workflow rather than flowing from retrieved content.

**Negative:**

- Provider owners must maintain capability descriptions, compiled routers,
  provenance, negative activation behavior, data minimization, confinement,
  and absence/failure fixtures.
- Consumers need explicit selection and conflict behavior instead of a single
  assumed provider name.
- Runtimes with weak skill enumeration or explicit-only activation support may
  require external adapter metadata while retaining the same portable
  semantics.
- Capability metadata can drift from the compiled corpus unless construction
  and router-precision gates verify them together.

**Revisit if:** portable skill runtimes adopt a standard, security-preserving
provider-capability negotiation protocol that subsumes this contract.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** Fixtures prove declared-corpus-to-provider completeness;
  capability-based discovery followed by exact-identity invocation; root-first
  bounded topic traversal with provenance for every generated router; and, for
  independently exposed providers, per-read confinement with manifest
  ownership, externally anchored eligibility, minimized non-persistent requests
  and results, clean absence that preserves the consumer baseline, bounded
  redacted failures, fail-closed malformed or drifted providers, visible
  ambiguity and conflict, negative activation, and no independent-consumer
  access to catalogue source-pack, installation, generated-router, raw-OKF,
  hidden-configuration, endpoint, or credential paths. The fixture set includes
  organization standards, framework-library, architecture-reference, and
  agent-skills-reference surfaces. Separate same-pack static-router fixtures
  prove root-first access stays within the router's own generated reference root
  without imposing the independent-consumer discovery membrane.
- **Owner:** catalogue and corpus-owning pack maintainers

## Alternatives considered

**Hard-code provider identities in every consumer.** Rejected because it makes
portable workflows depend on another pack's product name and installed layout,
prevents equivalent organization or framework providers from participating,
and confuses exact invocation with discovery.

**Forbid cross-pack discovery and use only same-pack knowledge.** Rejected
because it leaves available domain grounding unused and forces consumers to
duplicate doctrine or operate with avoidably low confidence.

**Discover corpora by filesystem convention or raw OKF search.** Rejected
because it violates ADR-0093, couples consumers to authoring and delivery
layout, bypasses provider routing and provenance, and broadens filesystem and
instruction-injection exposure.

**Centralize all knowledge in one shared runtime service.** Rejected because it
moves corpus ownership, availability, authentication, and version compatibility
into a mandatory service boundary. The provider-mediated contract permits such
a service when exposed as an eligible capability but does not require it.

**Copy relevant corpus material into each consumer pack.** Rejected because it
creates competing authorities and synchronization work; the repository already
has evidence that copied taxonomies require parity tooling and drift.

**Use only delivery-time integration declarations.** Rejected because external
declarations such as `pack.integrations` can describe installed composition and
fallback without polluting portable instructions, but they do not let a
workflow recognize other already-authorized organization, repository,
framework, architecture, or agent-skills knowledge surfaces by capability.

## References

- [RFC-0097: Agent Skill Engineering](../rfc/0097-agent-skill-engineering.md)
- [ADR-0093: OKF reference corpora remain governed build-time sources within
  their owning pack](0093-okf-reference-corpora-remain-governed-build-time-sources.md)
- [`architect` OKF bundle declaration](../../packs/architect/pack.toml)
- [`architecture-lenses-reference` generated provider](../../packs/architect/.apm/skills/architecture-lenses-reference/SKILL.md)
- [`security-checklists-reference` generated provider](../../packs/core/.apm/skills/security-checklists-reference/SKILL.md)
