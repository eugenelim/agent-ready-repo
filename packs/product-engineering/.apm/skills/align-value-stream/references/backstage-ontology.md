# The Backstage catalog — ontology and federation

The meta-repo's catalog reuses **Backstage's** Software Catalog ontology rather
than inventing one. Backstage is a real, widely-adopted tool, so its vocabulary
is recognized formalization, not jargon.

## The entity ontology

| Entity | What it is |
| --- | --- |
| **Domain** | A bounded area of the business (a value stream). The top of the tree. |
| **System** | A collection of components that together deliver a capability. |
| **Component** | A deployable unit — a service, a website, a library. One per component repo. |
| **API** | An interface a Component **provides** or **consumes** (REST, events, gRPC, …). |

The relations that carry provider/consumer roles are Backstage-native:
`providesApi` / `consumesApi` (source fields `spec.providesApis` /
`spec.consumesApis` on a `Component`). The meta-repo mirrors these rather than
inventing parallel frontmatter — see `shared-contract-handoff.md` for how the
roles drive the contract direction.

## Federation — reference, never re-author

Each component repo owns its **`catalog-info.yaml`** at its root (Backstage
mandates that filename and location). The meta-repo's catalog is **federated**:
it references each repo's `catalog-info.yaml` (Backstage does this with a
`Location` entity pointing at the file's URL) rather than copying the entity
definitions in. Re-authoring them here forks the data and guarantees drift — the
component repo is always the authority for its own component and the APIs it
provides or consumes.

Because `catalog-info.yaml` is Backstage-native and lives at each component
repo's **root**, it falls outside this pack's "seeds land in `docs/product/`"
convention — so the pack ships it as the **sample below**, not as a projected
seed. Copy the shape into each component repo, not into the meta-repo.

## A worked `catalog-info.yaml` sample (lives at a component repo's root)

```yaml
# <component-repo>/catalog-info.yaml — the component repo owns this; the
# meta-repo's catalog references it (a Backstage Location entity), never copies it.
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: <component-name>
  description: <one-line outcome this component delivers>
  annotations:
    backstage.io/source-location: url:https://<host>/<org>/<component-repo>/
spec:
  type: service              # service | website | library
  lifecycle: production      # experimental | production | deprecated
  owner: <team>
  system: <system-name>      # the capability this component is part of
  providesApis:
    - <api-name>             # the interface this component is the provider for
  consumesApis:
    - <other-api-name>       # an interface this component depends on
---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: <api-name>
spec:
  type: openapi              # openapi | asyncapi | grpc | graphql
  lifecycle: production
  owner: <team>
  definition:
    $text: ./contracts/openapi/<api-name>.yaml   # reference; authority lives where shared-contract-handoff settles it
```

The meta-repo's federated view is the **Domain** and **System** entities that
group these Components, plus `Location` references to each repo's file — the
cross-cutting layer no single component repo can own.
