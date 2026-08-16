# Cross-pack consumer pressure test

> Discipline: applied architecture pressure test

This note tests whether RFC-0088 lets an existing website-oriented provider pack
remove duplicate browser infrastructure without a published npm SDK. It does
not propose changing an existing pack.

**Confidence legend:** **high** means the conclusion follows directly from the
destination pack/projection contract inspected for this import; **moderate**
means it remains a composed inference. Confidence is not Experimental spike
evidence or architecture acceptance.

## Verdict

The cross-pack shape works only if `web-pilot` hosts adapter-defined read
behaviors rather than a fixed domain method set. AgentBundle dependency metadata
establishes an install precondition; a stable user-local JSON launcher provides
runtime linkage. No Node import from another pack's projected files and no npm
publication are required. [high]

The first release cannot absorb provider mutations. Reads are the contract
pressure test; create, update, delete, send, submit, and other mutations require
a later policy RFC. Supervised repair is not a production mutation back door.
[high]

## Reusable vertical-pack shape

| Layer | Generic provider example | Owner after adoption |
| --- | --- | --- |
| User workflows | Review, search, prioritization, presentation, confirmations | Provider skills |
| Deterministic domain logic | Classification, grouping, pagination decisions, formatting | Provider scripts |
| Website adapter | Auth predicate, origins, selectors, observed read endpoints, schemas, downloads, named read behaviors | Adapter artifact bundled by provider |
| Browser foundation | Profile ownership, headed handoff, CLI inspection, Playwright host, policy events, artifacts, redaction, lifecycle | `web-pilot` |

The provider pack remains the catalogue-facing product. An adapter is a driver
payload admitted separately because installing agent instructions is not the
same trust decision as controlling an authenticated browser.

## Cross-pack runtime contract

```text
provider skill or script
  -> stable installed web-pilot launcher
  -> versioned JSON behavior job
  -> exact consumer activation and resource-scope validation
  -> exact immutable adapter digest
  -> native Playwright execution in the bound browser
  -> validated JSON or opaque local artifact handle
```

The provider bundles a candidate adapter and behavior schemas. Setup asks the
launcher to inspect and admit it. `web-pilot` does not scan another pack or
silently install projected code. A provider update does not activate a changed
digest.

## Adapter-defined behavior examples

The foundation treats behavior IDs as adapter-scoped opaque names. A
software-delivery provider might declare:

```text
work.items.list@1
work.item.read@1
work.items.search@1
docs.pages.read@1
build.runs.list@1
build.artifact.download@1
```

Each behavior binds exact input/output schemas, sensitivity class, result
policy, resource scope, and origin/method rules. Provider scripts retain classification, scoring,
reconciliation, and presentation above the runtime.

## Responsibilities a provider can remove

After a read migration passes construction and local smoke tests, a provider can
remove:

- its standalone Playwright installation and browser launch path;
- duplicate persistent profiles and login handoff;
- generic browser lifetime, crash, timeout, lock, and reconnect handling;
- cookie export/replay code where the context request client suffices;
- generic download confinement, hashing, retention, and redaction;
- generic probe capture/export plumbing; and
- adapter install, upgrade, rollback, and grant state.

Provider-specific authentication predicates, selectors, endpoints, schemas,
pagination, and token observation stay in the adapter. Provider workflow and
presentation logic stay in its skills and scripts.

## What blocks a complete migration

| Option | Result |
| --- | --- |
| Route normal mutations through repair/raw browser access | Reject; it converts an exceptional diagnostic boundary into an ungoverned API |
| Migrate reads but retain a second long-term profile for writes | Transitional only; preserves split identity and duplicate lifecycle |
| Keep v1 read-only and design mutation policy later | Recommend; preserves the RFC's authorization claim |
| Do nothing | Retains duplicate runtime and profile code indefinitely |

## Required construction test

Before acceptance, render and install three synthetic packs:

1. a synthetic `web-pilot` foundation;
2. `example-provider`, with skills, scripts, a bundled adapter, and a required dependency; and
3. `example-provider-peer`, with a separate grant to a subset of the same adapter, connection, and resources.

The test must prove:

- dependency failure occurs before writes when the foundation is absent;
- setup installs an exact candidate through the stable launcher;
- source and rendered scans reject sibling-skill reads, projection imports, provider-owned Playwright runtime imports, and undeclared cross-pack Node imports;
- incompatible protocol, behavior, schema, or digest state fails before browser launch;
- a conforming provider's declared identity cannot accidentally use the peer's
  grant; this is not a malicious same-user isolation claim;
- each conforming provider can invoke only its behavior/schema/resource tuple;
- sensitivity-class mismatch, result-policy mismatch, and an attempted narrower
  policy without grant amendment fail before browser launch, while exact grants
  for both `agent-summary` and `local-artifact-only` succeed;
- a newly discovered resource inherits no grant;
- one provider may activate a new digest while the peer retains the old admitted digest;
- the same live browser serves login, adapter work, and CLI inspection;
- a provider update cannot silently activate code; and
- a disabled foundation returns a typed runtime-dependency failure rather than launching a fallback browser.

## npm graduation test

The JSON process ABI is sufficient until at least one is observed:

- a non-AgentBundle runtime consumer;
- multiple foundation packs requiring in-process imports; or
- two independently implemented provider packs demonstrating that generated or copied contract types drift despite conformance tests.

Until then, npm publication adds a release and supply-chain surface without
solving a demonstrated problem.

## Known unknowns

- Which provider read paths can use the cookie-sharing request client and which require page execution or bearer-token observation.
- Whether bundled candidate paths remain stable across every adapter projection.
- Whether copied/generated schema types remain usable for independent provider authors.
- Which mutation policy could eventually remove a transitional second profile without weakening user confirmation.
