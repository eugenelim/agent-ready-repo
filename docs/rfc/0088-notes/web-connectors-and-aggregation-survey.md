# Connector and aggregation boundary transfer

> Discipline: imported architecture evidence, adapted to destination scope

**Topic:** Which object-model conclusions from the source connector and
aggregation survey remain useful to RFC-0088.
**Adapted:** 2026-08-14
**Purpose:** Preserve the source survey's architectural conclusions without
promoting out-of-scope product domains into this software-delivery catalogue.

## Evidence disposition

The source bundle compared a connector directory, a consented connection
platform, and a multi-provider aggregation product. Those products and their
domain contracts are outside this repository's charter. Their named examples
and external citations are therefore not promoted as destination evidence.

This note retains only the object-model hypotheses that the destination can
test with synthetic software-delivery providers. They are not treated as
validated merely because the source products use similar concepts. S5 must
prove the connection/resource/grant model locally before RFC acceptance.

> **Status:** Every “proposed destination direction” below remains Draft.
> Source-survey confidence is neither Experimental spike evidence nor
> architecture acceptance.

## Transferred hypotheses and destination decisions

### Connector, connection, and resource are distinct

**Imported hypothesis:** a discoverable connector definition, one
authenticated login, and the resources visible through that login are
different objects.

**Proposed destination direction:** a provider pack is the catalogue-facing connector;
a connection binding owns one authenticated browser/profile identity; resource
bindings are separately aliased objects beneath the connection. A resource
never owns the profile.

**Destination test:** two synthetic resources beneath one connection use one
profile, but a grant for one resource cannot invoke the other.

### Discovery claims are not runtime authority

**Imported hypothesis:** directory metadata helps discovery but does not grant
runtime access.

**Proposed destination direction:** `categories` and `pack.metadata.web-pilot` select
discovery and future construction lint only. Runtime checks the admitted
adapter digest, consumer activation, connection/configuration generation,
behavior/schema tuple, result policy, and resource scope.

**Destination test:** changing metadata alone cannot admit an adapter, create a
connection, or widen a behavior grant.

### Authentication is a lifecycle

**Imported hypothesis:** initial connection, user-present repair,
reauthorization, capability/resource changes, and disconnect are distinct
states.

**Proposed destination direction:** provider setup covers connect/validate, resource and
capability selection, health, reauthenticate/re-consent, repair,
upgrade/rollback, and disconnect-local. Disconnect-local revokes local grants
and retires local state; v1 does not mutate authorization settings on the
website.

**Destination test:** the synthetic lifecycle proves reauthentication with a
matching identity can preserve scope, while a new resource or changed identity
requires explicit consent.

### Capabilities are consented, not inferred

**Imported hypothesis:** connection existence does not imply authorization for
every supported operation or visible resource.

**Proposed destination direction:** a consumer activation binds the exact behavior,
schema, sensitivity class, result policy, connection, and resource scope. Newly
discovered resources and new adapter behaviors require explicit grant changes.

**Destination test:** undeclared behavior, schema mismatch, newly discovered
resource, and a declared-identity/grant mismatch from a conforming caller all
fail before browser launch. This is not a malicious same-user isolation test.

### Aggregation belongs above connectors

**Imported hypothesis:** reconciliation, normalized views, and route switching
are domain semantics above a connection runtime.

**Proposed destination direction:** a future software-delivery aggregation pack owns its
domain profile and reconciliation. `web-pilot` supplies only the browser
backend for a provider whose supported source is an authenticated website.

**Destination test:** the foundation passes through schema-validated opaque
domain payloads and does not merge resources or provider routes.

## Destination object map

| RFC-0088 object | Responsibility | Must not become |
| --- | --- | --- |
| Provider pack | Discovery, skills, deterministic domain scripts, setup, bundled candidate adapter | Runtime authority or browser-profile owner |
| Website adapter | Exact executable browser driver, behavior schemas, origin/method declarations | Catalogue product or agent-facing workflow |
| Connection binding | One login, profile namespace, identity/configuration generations | Global adapter/behavior grant |
| Resource binding | Local alias and minimum provider correlation beneath a connection | Profile owner or implicit grant |
| Consumer activation | Exact adapter/behavior/schema/configuration/resource/result tuple | Claim of isolation from a malicious same-user caller |
| Domain aggregator | Reconciliation and normalized multi-provider meaning | Browser substrate |

## Destination provider profile

The destination has no `pack.type` and no `web-automation` entry in its current
soft category vocabulary. The provisional profile is:

```toml
[pack]
categories = ["integrations"]

[[pack.dependencies.required]]
catalogue = "agent-ready-repo"
pack = "web-pilot"
version = "^1.0"

[pack.metadata.web-pilot]
profile = "provider-v1"
declared-intent = "read-only"
setup-skill = "example-provider-setup"
web-skill = "example-provider-web"
adapter-delivery = "bundled"
```

The fields remain claims until future lint verifies them. Provider metadata
does not authorize a browser job.

### Domain-profile gate

A machine-readable domain-profile claim requires an accepted owner, immutable
definition and schema digests, sensitivity floor, behavior-role mapping, and
canonical fixture suite. The provider depends on the owner pack; catalogue
conformance verifies the inert claim; the runtime authorizes only the exact
underlying behavior tuple.

No domain profile is proposed here.

## Known unknowns

- Whether a second independently authored provider justifies adding
  `web-automation` to the soft category vocabulary.
- Which software-delivery pack should own the first domain profile.
- How to reconcile one logical resource reached through two provider routes
  without exposing provider identifiers to the model.
- Whether local website adapters can remain reliable enough to justify this
  foundation when supported APIs are unavailable.
