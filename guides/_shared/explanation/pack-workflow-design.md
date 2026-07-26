# Pack workflow design

## What a pack is

A pack is a cohesive set of skills for a role's work — all the workflows one kind of specialist needs, bundled as a single installable unit. Before you write your first `SKILL.md`, work through the five steps below. Each one produces a concrete decision that feeds the next.

The design vocabulary throughout is the **session arc**: the five stages every sustained professional tool must support —

- **Arrive** — start a new session
- **Orient** — understand where you are and what comes next
- **Work** — drive the core workflow
- **Persist** — save durable artifacts across sessions
- **Collaborate** — hand off to the next stage or pack

The arc is the skeleton your skills hang on. Not every pack covers every stage; the decision tree in Step 1 tells you which stages apply.

## Step 1 — Characterize your workflow type

Walk this decision tree to identify your pack's type:

```
Does the pack maintain a work-in-progress thread across sessions —
tracking phases, a growing project, or cumulative state?
│
├─ No → Does each invocation produce a standalone artifact
│        that the user takes away?
│        ├─ Yes → Episodic
│        └─ No  → Stateless
│
└─ Yes → Does this pack create and own the project thread,
         or derive from a thread another pack owns?
          ├─ Own    → Sustained-project
          └─ Derive → Sustained-derived
```

| Type | Shape | Typical session |
| --- | --- | --- |
| **Episodic** | No persistent state between sessions | Each skill invocation is standalone; a completed artifact is the output |
| **Sustained-project** | Creates and manages a durable project | Session opens a thread; a status skill orients the return; pack drives the thread to completion |
| **Sustained-derived** | Reads from and builds on a project another pack owns | Session reads from a source project; adds derived artifacts |
| **Stateless** | Pure workflow transformation; no file-system output | Input → transformation → output; nothing persists |

**Output from this step:** your pack type. Write it down before moving to Step 2.

## Step 2 — Map the arc for your pack

For each arc stage, answer the guiding question. Your answers define which skills your pack needs and which it can safely skip.

**Arrive — "What does a user type to open this pack's first session?"**
Name the skill that kicks things off. For a sustained-project pack, this is your `*-project-start` skill. For an episodic pack, it is the first substantive skill — there is no session state to initialize.

**Orient — "When a user returns after a break, what do they need to know?"**
If the answer is non-trivial (where a project stands in its lifecycle, what was decided, what comes next), your pack needs a `*-status` skill. Episodic packs skip this stage: there is no persistent thread to orient to.

**Work — "Which one or two skills are the core workflows this pack enables?"**
Name them. These are the skills that do the pack's primary work — the reason a user installs it.

**Persist — "Does the pack accumulate a project directory across sessions?"**
If yes, design the vault-path shape in Step 4. An episodic pack may write a standalone artifact per invocation, but it does not build up a shared project directory over time — skip Step 4 for episodic and stateless packs.

**Collaborate — "What does the next pack in the user's workflow consume from this one?"**
Name the artifact type and file shape another pack might read. A sustained-derived pack depends on this being well-defined by the pack it derives from.

**Output from this step:** an arc map — one row per stage, naming the skill (or "none") and the artifact (or "none").

## Step 3 — Name your skills

Skill activation is description-driven — users invoke skills by natural language, not exact names. But names appear in the catalogue and in `SKILL.md` frontmatter, and a consistent verb vocabulary lets users predict what to type.

Use the five-verb taxonomy to pick the right name:

| Verb | Meaning | Activation phrasing |
| --- | --- | --- |
| `status` | Orient — "where am I / what's next?" | Cold-start phrases, "what's on today", "orient me" |
| `start` | Create/begin a sustained project | "start a research project", "kick off an investigation" |
| `check` | Quality/health read — "is it good / saturated / done?" | "is this ready", "should I keep gathering" |
| `init` | Repo-scaffold only | `init-project`, `adapt-to-project`; cf. `git init` |
| `resume` | Return to prior work | Activation phrase — not a skill name |

**Banned as skill names:** `arrive`, `orient`, `onboard`, `return`, `onboarding` — these are UX-stage labels, not user-facing commands. Using them as skill names causes activation collisions with the arc vocabulary users already know.

For the full taxonomy table and naming rules, see [How to author a skill](../how-to/author-a-skill.md#naming-your-skill).

**Output from this step:** a name for each skill in your arc map.

## Step 4 — Decide your vault-path shape

If your pack maintains a persistent project directory (sustained-project or sustained-derived), design the vault-path now. Skip this step if your pack is episodic (standalone output per invocation, no shared project state across sessions) or stateless.

**One `output_dir` base per pack.** Configure it once in `agentbundle-layout.toml`:

```toml
[your-pack-section]
output_dir = "~/your-output-dir"
```

Each pack has its own config section. Do not share a section with another pack.

**Skill-specific subdirectories under the base.** Each skill that writes files owns one subdirectory under `output_dir`. Do not write all artifacts flat into the base — it makes a status skill's scanning harder and creates namespace collisions as the pack grows.

The `journey-mapping` skill is the canonical example: it writes customer-journey artifacts to `<output_dir>/journeys/`. Other experience-design skills each own a sibling directory (`screens/`, `blueprints/`). The `experience-status` skill is the one skill that scans across all subdirectories — it reads the vault, not a single subpath.

**Output from this step:** a directory layout diagram for your pack's output.

## Step 5 — Register with workspace-status

If your pack has a `*-status` skill, register it so that `workspace-status` can route to it when a user cold-starts a session.

**How to register:**

1. Choose a `shaping_queue` type string for your pack. This string appears in `workspace.toml` entries for your pack's shaping items (for example, `design` for the experience-design pack, `research` for the desk-research pack).

2. Add a routing entry in the `workspace-status` skill's routing table: `type = "<your-type>"` → `<your-pack>-status`.

3. Add a fallback. When your pack is not installed, `workspace-status` skips the routing entry rather than erroring. Document the fallback message in your `*-status` skill body — it tells the user what to run to get started (for example, when the experience-design pack is not installed, `workspace-status` falls back gracefully rather than routing to `experience-status`).

**If your pack is episodic or stateless**, skip this step. There is no persistent thread to orient to, and a status skill for an episodic pack would have nothing to read.

**Output from this step:** a `shaping_queue` type string and a routing entry.

## Reference: worked archetypes

### Episodic — product-strategy

Each skill invocation is standalone. A product-strategy session runs a single skill — market analysis, competitive positioning, or user persona — and produces a complete artifact. There is no cross-session thread to track.

**Arc map:**

| Stage | Skill | Artifact |
| --- | --- | --- |
| Arrive | Any skill (e.g., `market-analysis`) | — |
| Orient | None | — |
| Work | Whichever skill the user invokes | Standalone analysis artifact |
| Persist | Each skill writes a per-invocation standalone artifact | Strategy document (not accumulated across sessions) |
| Collaborate | — | Artifact feeds adjacent workflows |

**No status skill needed** — each invocation is complete; there is no thread to return to.

Other catalogue packs that follow the episodic pattern: architect (each architecture review is standalone) and converters (each file conversion is standalone).

---

### Sustained-project — desk-research

The desk-research pack creates and manages a research project that spans multiple sessions. A project opens with `desk-research-project-start`, advances through capture → digest → synthesize → feedback phases, and closes when the stop signal fires.

**Arc map:**

| Stage | Skill | Artifact |
| --- | --- | --- |
| Arrive | `desk-research-project-start` | Creates `overview.md`; initializes the project |
| Orient | `desk-research-project-status` | Reads `overview.md`; reports phase and working hypothesis |
| Work | `desk-research`, `desk-research-project-check`, `desk-research-project-digest` | Source captures, saturation check, synthesis |
| Persist | All writing skills | Files under `<output_dir>/` (configured via `[research] output_dir`) |
| Collaborate | — | Synthesized research feeds product-strategy or experience-design |

The status skill reads `overview.md` at the configured `output_dir`. When no project exists, it surfaces a not-started message and points to `desk-research-project-start`.

---

### Sustained-derived — experience-design

The experience-design pack reads from customer-journey artifacts and derives screen flows, service blueprints, and experience assessments. It builds on what `journey-mapping` creates; it does not create the initial project from scratch.

**Arc map:**

| Stage | Skill | Artifact |
| --- | --- | --- |
| Arrive | `journey-mapping` (creates the first journey artifact) | Customer-journey map in `<output_dir>/journeys/` |
| Orient | `experience-status` | Reads frontmatter across `journeys/`, `screens/`, `blueprints/`; reports steel-thread completion |
| Work | `user-flow`, `service-blueprint`, other experience skills | Screen flows, blueprints |
| Persist | All writing skills | Files under `<output_dir>/journeys/`, `screens/`, `blueprints/` |
| Collaborate | — | Derived artifacts feed content-design and development |

When `[design] output_dir` is not configured, `experience-status` surfaces a not-configured message and points to `journey-mapping`, which sets the path on first run.

---

### Stateless — reserved category

The stateless type is reserved for future packs whose shape is pure transformation: input arrives, output leaves, nothing persists. No current catalogue pack fits this classification.

The converters pack and the architect pack are both **episodic** — each invocation produces a standalone artifact the user receives as output, not a transformation that feeds back into a pipeline without producing a visible artifact.

If you are designing a pack that genuinely fits the stateless shape — pure transformation, no file output, no session state — this is the right type. Verify first: if each run produces a file the user saves, you are episodic, not stateless.
