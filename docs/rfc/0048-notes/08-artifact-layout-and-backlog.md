# Artifact ontology, the backlog bridge, and a single-repo folder layout

Scope: **any document workspace upstream of the G3 handoff** — a single product
**monorepo** (multiple distributed components in `packages/`) is the worked example below,
but discovery is workspace-agnostic (three-tier resolution + discover-by-marker + the
file-based `_state/` store make an Obsidian vault or any markdown-with-`type:` workspace a
valid home; the only hard repo anchor is the G3 handoff into `work-loop`). The
single-monorepo framing was corrected per **§ Amendments 2026-06-26** (the discovery-repo /
work-repo split is no longer "out of scope" — child-4's lint already crosses boundaries by
stable id, not path).

## The backlog — the bridge between the loops

`discovery-loop` converges a **decision brief** (the ratified "what"), then decomposes
it into a **backlog**: an ordered, dependency-aware set of **work items**, each a
buildable slice scoped to one (or few) component(s). `work-loop` pulls them **one at a
time** in topological order. The backlog is the materialization of the cross-component
DAG (GAP-O7); `loop-cohort` (already a topological scheduler) feeds it.

The **service blueprint is the slicing instrument**: it maps each journey step to its
backstage components, so a discovery that spans many modules slices cleanly into
per-component work-loop runs, with cross-component edges (schema → service → UI) as
`depends-on`.

**Work item (slice) shape:**
```
- id: WI-007
  title: approve a proposed learning
  components: [api-service, web-app]      # which distributed modules it builds
  brief: docs/product/briefs/approved-learning.md
  depends_on: [WI-003]                    # identity before learning
  traces_to: outcome=learning-acceptance · decision-brief §learning
  status: todo | building | done
```

One item → its brief → `new-spec` → `work-loop` → a component increment in `packages/<c>/`.

## Artifact ontology (named)

| Loop | Artifact | Home |
| --- | --- | --- |
| discovery | **intent** (vision/strategy/capability/feature) | `docs/product/intents/` |
| discovery | **domain-framing** (real-activity + brownfield current-system) | `docs/discovery/<initiative>/domain-framing.md` |
| discovery | **scope-boundary** (MVP out-of-scope register; brief inherits at G3) | `docs/discovery/<initiative>/scope-boundary.md` |
| discovery | **persona** | `docs/discovery/<initiative>/` |
| discovery | **journey-map** | `docs/discovery/<initiative>/` |
| discovery | **service-blueprint** (the slicing instrument) | `docs/discovery/<initiative>/` |
| discovery | **screen-inventory** + per-screen **screen-brief** | `docs/discovery/<initiative>/screens/` |
| discovery | **aesthetic-direction** (the taste reference) | `docs/discovery/<initiative>/` |
| discovery | **decision-brief** (the G2 ratified shape) | `docs/discovery/<initiative>/` |
| bridge | **backlog** (ordered work items / slices) | `docs/discovery/<initiative>/backlog.md` |
| sidecar (carried schema — § Amendments 2026-06-26) | **blackboard · open-questions · traceability · decision-log** | `docs/discovery/<initiative>/_state/` |
| work | **brief** | `docs/product/briefs/` |
| work | **spec** + **plan** (each declares `Component:`) | `docs/specs/<feature>/` |
| cross | **architecture** (C4, domain model), **contracts** (OpenAPI/AsyncAPI) | `docs/architecture/`, `docs/contracts/` |
| governance | **ADR**, **RFC** | `docs/adr/`, `docs/rfc/` |
| build output | the **components** | `packages/<component>/` |

## Single-repo folder layout (anonymized `example-assistant`)

```
example-assistant/
├── docs/
│   ├── product/
│   │   ├── intents/
│   │   │   └── example-assistant.md          # intent ladder: vision→strategy→capability→feature
│   │   └── briefs/                           # work-loop handoff — one brief per backlog item
│   │       ├── resource-state.md
│   │       └── approved-learning.md
│   ├── discovery/                            # discovery-loop, per initiative (discovery-lead owns)
│   │   └── example-assistant/
│   │       ├── domain-framing.md
│   │       ├── scope-boundary.md
│   │       ├── persona.md
│   │       ├── journey-map.md
│   │       ├── service-blueprint.md          # frontstage screen ↔ backstage component → drives slicing
│   │       ├── screens/
│   │       │   ├── _inventory.md             # screen inventory + state matrix
│   │       │   └── learning-review.md        # per-screen brief
│   │       ├── aesthetic-direction.md
│   │       ├── decision-brief.md           # the ratified "what" (G2)
│   │       ├── backlog.md                    # the bridge: ordered, DAG'd work items
│   │       └── _state/                       # sidecar — typed convergence state (carried schema, § Amendments 2026-06-26)
│   │           ├── blackboard.json
│   │           ├── open-questions.md
│   │           ├── traceability.json         # outcome→…→spec→component edges
│   │           └── decision-log.md           # gate outcomes + audit trail
│   ├── specs/                                # work-loop input — one per backlog item
│   │   ├── resource-state/
│   │   │   ├── spec.md                       # Shape: data · Component: api-service + data-store
│   │   │   └── plan.md
│   │   └── approved-learning/
│   │       ├── spec.md                       # Shape: mixed · Component: api-service + web-app
│   │       └── plan.md
│   ├── architecture/                         # C4, domain model (cross-component)
│   ├── contracts/                            # OpenAPI / AsyncAPI per service boundary
│   ├── adr/   └── rfc/                        # governance
└── packages/                                 # the distributed components work-loop builds
    ├── web-app/                              # frontend — the screens
    ├── api-service/                          # backstage services / agent tools
    ├── data-store/                           # schema / persistence
    └── worker/                               # async / the learning pipeline
```

## How a multi-module discovery slices into distributed work-loops

1. `discovery-loop` converges one **decision-brief** for the initiative (spanning
   web-app + api-service + data-store + worker).
2. The **service-blueprint** assigns each journey step's backstage to a component.
3. `discovery-lead` decomposes it into **backlog** items, each scoped to a component
   slice, with `depends_on` edges (data-store schema → api-service → web-app screen).
4. `loop-cohort` topologically orders the backlog; `work-loop` pulls each item
   **one at a time** → brief → `new-spec` (`Component:` declared) → build into
   `packages/<component>/`.
5. The **traceability** sidecar threads outcome → … → spec → component, so the lint can
   prove every built component traces to a ratified decision and no orphan ships.

## Defining & establishing the layout (never hardcode a path)

The layout lives in the **current working folder** (the adopter's repo). Skills must
**never hardcode a literal path**; they resolve in three tiers (the
`research-project-start` resolve-or-default-or-elicit pattern, generalized):

1. **Config** — read the adopter's chosen path from `agentbundle-layout.toml`'s scope-keyed
   `[pack.layout]` (RFC-0040, the *existing* mechanism). E.g. `[experience.layout] discovery = "..."`.
2. **Designed default** — if no config key, use the default we designed
   (`docs/discovery/<initiative>/`, `docs/product/briefs/`, `docs/specs/`, `packages/<c>/`).
3. **Discover by marker** — if the adopter chose a different layout and neither config nor
   default matches what's on disk, **search the workspace** for the artifact by its **stable
   marker** (canonical filename + frontmatter `type:`), not by path. Surface if ambiguous
   (multiple/none) rather than guessing.

So the answer to "open vs defaults": **both** — suggest the designed defaults (works
out-of-box) *and* leave it open (config-overridable, and discoverable even if moved).

**Establishing the folders** — two complementary moves, both in the cwd:
- `init-project` / `adapt-to-project` **seed** `agentbundle-layout.toml` with the designed
  defaults at init/adapt time (and may scaffold the top-level tree).
- each **producing skill** creates its directory **lazily on first write**, at the resolved
  path — so nothing is pre-created that isn't used, and a custom layout is honored.

**Markers make discovery work:** every artifact carries a stable marker — a **canonical
filename** (`domain-framing.md`, `scope-boundary.md`, `journey-map.md`, `service-blueprint.md`, `backlog.md`, …)
**+ a frontmatter `type:`** — so a skill (or the traceability lint) can *find* it regardless
of where the adopter put it. This is what lets us not hardcode.

## Notes
- `docs/discovery/` and `docs/contracts/` are new top-level doc homes — *defaults*, not
  hardcoded (resolved per the three tiers above).
- Grouping is **by initiative** for discovery artifacts (one discovery-loop run = one
  decision-brief = one backlog) and **flat by feature** for briefs/specs (work-loop
  doesn't care about initiative grouping). Specs name their target `Component:`.
- Per-package specs (`packages/<c>/docs/specs/`) are an alternative for very large
  monorepos; central `docs/specs/` is the default.
