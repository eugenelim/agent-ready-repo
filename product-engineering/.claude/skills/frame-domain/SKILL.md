---
name: frame-domain
description: Use when grounding a product in the real-world activity it serves and bounding its MVP before any screen, service, or architecture is drawn — at the G1.5 Domain & MVP point of the discovery loop, or standalone. Triggers on "frame the domain", "how is this activity really done", "ground this before we design", "what's in/out of the MVP", "draw the scope boundary", "is this scope creep". Produces two typed artifacts from one research-grounded pass — Domain Framing (real-world-activity grounding + best practice + naive-failure modes, plus a brownfield current-system half) and Scope Boundary (the MVP out-of-scope register). Do NOT use to shape the intent behind the work (use `frame-intent`), to test whether a bet holds (use `de-risk-intent`), or to break an intent down (use `decompose-intent`).
---

# Skill: frame-domain

Ground a product in the **real-world activity it serves** and **bound its MVP**
*before* any screen, service, or architecture is drawn. This is the discovery
loop's deepest correctness lever: the agent cannot reason through a domain it
does not know, so left ungrounded it **hallucinates the domain and over-scopes**.
`frame-domain` runs at the **G1.5 Domain & MVP** point — after `decompose-intent`
has produced capabilities, before the convergent design loop — or standalone.

From **one `research`-grounded pass** the skill emits **two typed artifacts**.
They ship together but are separate artifacts because they have separate
downstream lifecycles:

1. **Domain Framing** (`domain-framing.md`, `type: domain-framing`) — the
   grounding artifact, guarding against **hallucinating a domain the agent does
   not know**.
2. **Scope Boundary** (`scope-boundary.md`, `type: scope-boundary`) — the MVP
   **out-of-scope register**, the G1.5 **scope-creep guard** the brief
   inherits and refines at G3.

The skill **wraps** existing skills (`research` applied mode,
`decision-archaeology`) and **shapes** their output into the typed artifacts; it
does not re-implement retrieval. It is **prompt-only** (Charter Principle 3):
there is no engine, script, or filename generator — the agent following this body
writes the artifacts and their paths.

## When to invoke

Before framing, confirm:

1. The ask is *grounding-and-bounding a domain*, not shaping or breaking down an
   intent. If the user wants to shape the outcome/opportunity, route to
   `frame-intent`; to test whether a bet holds, `de-risk-intent`; to split a
   shaped intent into the next level, `decompose-intent`.
2. There is a **domain to ground** — a real-world activity the product serves
   that the agent does not already hold (how owners actually plan, restock, act).
   A pure refactor or chore has no domain to frame; say so.
3. Resolve whether the product is **greenfield or brownfield** — it gates one
   thing only: Domain Framing's current-system half (below).

This skill is **invokable standalone** with **no hard dependency on the
coordinator / discovery-loop** (which is unbuilt). It produces on demand; the
non-skippable "cannot proceed without it" gate property is the coordinator's to
own, not this skill's.

## Wrapping `research` applied mode — the real-world-activity half

Domain Framing's **real-world-activity half** is grounded by wrapping `research`
in **`applied` mode** — the practitioner / grey-literature discipline, with the
prior-art / best-practice / case-study / anti-pattern frames and the
survivorship-bias and stale-prior-art overlay. That applied-mode discipline is
what grounds *how the activity is really done* and surfaces the naive-design
failure modes; the agent's untested intuition is not a substitute.

Invoke `research` in `applied` mode against the domain. It emits a
`<topic-slug>-survey.md` — **that survey is an input, not the output**. This
skill **consumes and shapes** the applied-mode findings into the *Real-world
activity* section of Domain Framing; it does **not** re-implement retrieval and
it does **not** treat the survey itself as the Domain Framing artifact.

**This wrapped call stays an `applied` survey — the `research` methodology shape
does not fire on it.** `research` carries a separate `methodology` output shape
(a staged best-practice *method*) for direct process-shaped questions. That shape
fires only on a *direct* user request; a `research` call issued **by**
`frame-domain` for grounding is never reshaped into a methodology artifact, so
this grounding pass reliably returns the `applied` survey this section consumes.
(Use `research`'s methodology shape when the ask is *"the best way to do X, end to
end"* as a standalone question, not for product/MVP grounding — that is this
skill.)

The *Real-world activity* section captures three things:

- **How the activity is really done** — its cadence/horizon, and the gap between
  the *planned* and *actually done* (substitutions, skips, carry-overs), because
  a fantasy of the activity is the failure this section exists to prevent.
- **Best practice** — cited, applied-mode confidence-tagged.
- **Naive-design failure modes** — the anti-pattern frame: the designs that look
  obvious and reliably fail (e.g. demanding precise inventory).

## The brownfield half — `decision-archaeology` + architecture extraction

Domain Framing's **current-system half is produced only when a current system
exists**. For a brownfield product, reverse-engineer how the existing system
already does the activity:

- **Architecture extraction** from code and docs — the current domain model,
  events, and the seams that bind real choices.
- **`decision-archaeology`** over the existing system's choices — the rationale
  chain, the alternatives considered and rejected, and the revival check
  flagging rejected alternatives whose original rejection rationale no longer
  holds.

**Greenfield omits the brownfield half**, and the artifact says so — write the
explicit greenfield note (`brownfield: false`, "(greenfield — no current system
to reverse-engineer)") rather than leaving the section blank or, worse,
inventing a system that does not exist.

## The out-of-scope register — Scope Boundary

Scope Boundary is the **MVP out-of-scope register**: the explicit list of the
tempting-but-excluded capabilities, **each with its appetite reason** — not a
bare list. Anything not rooted in an in-appetite outcome is scope creep; the
register is the referent the **G1.5 scope-creep guard** and the human at the MVP
boundary reason against, and **the brief inherits and refines it at G3** (the
`scope-boundary → brief` edge).

Each entry names a capability the appetite *excludes* and the appetite reason it
is out — `<excluded capability> — out because <appetite reason>` — so the guard
and the reviewer can tell scope creep from in-appetite work. The classic
over-scope this rejects: a third-party fulfillment / external-service
integration the owner never asked for.

## Residual assumptions — never assert an ungrounded domain claim

Every finding the wrapped research **could not ground** is surfaced as a **named
residual assumption** — listed for the human reviewing the MVP boundary. An
unevidenced finding is *either* grounded by the wrapped research *or* surfaced as
a residual assumption — **an ungrounded domain claim is never asserted as fact**
in the artifact body. This is the line between a grounded artifact and a
confident hallucination, so a human sees exactly what rests on grounding and
what rests on a guess.

## The two artifact schemas

Two typed artifacts — markdown schemas carried in this body, not serialized
contract files (prompt-only).

**Domain Framing** — `domain-framing.md`, carrying `type: domain-framing`:

```markdown
---
type: domain-framing
initiative: <initiative-slug>
brownfield: true | false
---

# Domain framing — <initiative>

## Real-world activity            # grounded by research applied mode
- How the activity is really done (cadence/horizon, the real-vs-planned gap, …)
- Best practice (cited, applied-mode confidence-tagged)
- Naive-design failure modes (the anti-pattern frame)

## Current system (brownfield)    # produced only when a current system exists; greenfield omits + notes it
- How the existing system does it (architecture extraction)
- Decision archaeology: rationale chain · alternatives · revival candidates

## Residual assumptions           # what the wrapped research could not ground
- (degrade only) <which grounding dependency was absent> — why grounding is thin
- <ungrounded finding> — surfaced for the human, not asserted
```

**Scope Boundary** — `scope-boundary.md`, carrying `type: scope-boundary`:

```markdown
---
type: scope-boundary
initiative: <initiative-slug>
---

# Scope boundary — <initiative>

## Out-of-scope register          # the G1.5 scope-creep guard; the brief inherits/refines it at G3
- <excluded capability> — out because <appetite reason>
```

## Where the artifacts live — three-tier path resolution

Resolve **each** artifact's write path in this order — **config → designed
default → discover-by-marker** — **in this skill body**. Resolution is
**prompt-only**: the agent reads a config file and reasons about a path — there
is no engine, index, daemon, or hardcoded path. The skill **never writes a
literal path**; it always runs the three tiers and surfaces ambiguity rather than
guessing.

1. **Config — the adopter's discovery base from `agentbundle-layout.toml`.** Read
   the adopter-created `agentbundle-layout.toml` (the adopter-file
   mechanism) for the **discovery base** the cross-cutting layout effort settles.
   `docs/discovery/` is a **shared discovery-loop home**, so its config key is the
   **discovery layout key** — **not** `product-engineering`'s file-per-slug
   `intents`/`rollups` table, and **not** the manifest-side `[pack.layout]`
   default source. **That discovery key is currently unbound** (it is the layout
   effort's to mint — see § Ask first in the spec), so until it is bound this tier
   resolves nothing and resolution falls through to the default and marker tiers.
   The skill reads whatever discovery key the layout effort settles; it does
   **not** mint a new table itself, and it never *writes* the layout file.
2. **Designed default** — `docs/discovery/<initiative>/domain-framing.md` and
   `docs/discovery/<initiative>/scope-boundary.md`. `docs/discovery/` is a
   *resolved default*, not a path this skill mints.
3. **Discover-by-marker** — search the workspace for each artifact's **canonical
   filename + frontmatter `type:`** (`domain-framing.md` + `type: domain-framing`,
   `scope-boundary.md` + `type: scope-boundary`). The **marker, not the path, is
   the contract**: downstream lenses and the (future) traceability lint find each
   artifact by its marker regardless of where the adopter's layout puts it.

**Create the directory lazily on first write**, at the resolved path. **Surface
ambiguity rather than guess** — a marker search that returns **multiple** matches
(which one is authoritative?) or **zero** matches (where should it land?) is
surfaced to the human, not resolved by a guess. When the discovery key is
eventually bound, surface the resolved path before the first write and reject any
`..` escape or out-of-tree symlink, per the `frame-intent` /
`research-project-start` sibling skills.

## Detect-and-degrade on optional dependencies

`research` and `decision-archaeology` are **optional, Tier-1 detect-and-degrade**
dependencies (progressive enhancement). Because this is a
prompt-only skill with no script, the **detect primitive is the agent checking
its available-skills roster** — the same roster-check `new-spec` already relies on
— **not** a body-level `shutil.which`.

If `research` (or, in brownfield, `decision-archaeology`) is **not installed**:

- **Name the gap** in the artifact — **lead the *Residual assumptions* section
  with a one-line note** saying plainly which grounding dependency was absent
  (this is *why* grounding is thin, distinct from an ungrounded claim, so it
  heads the section rather than sitting in the list).
- **Degrade to best-effort grounding** — produce the most useful artifact the
  agent can from what it does hold; do **not** fail hard.
- **Flag the ungrounded residue** — route everything the absent dependency would
  have grounded into *Residual assumptions*. **Never fabricate grounding** to
  paper over the gap (the `Never do` "no silent assertion" rule backstops this).

## The producer pipeline

1. Resolve the initiative + the greenfield/brownfield read (frontmatter inputs).
2. **Real-world-activity half** — invoke `research` applied mode; consume and
   shape the survey findings into *Real-world activity*; carry the ungrounded
   residue to *Residual assumptions*.
3. **Current-system half** — if brownfield, invoke `decision-archaeology` +
   architecture extraction into *Current system*; else write the greenfield note
   and skip.
4. **Out-of-scope register** — bound the appetite; build the register, listing
   each excluded capability with its appetite reason.
5. **Resolve each write path** (three tiers) → create the directory lazily →
   write `domain-framing.md` and `scope-boundary.md`, each carrying its marker.
   Surface ambiguity rather than guess.

## Anti-patterns to refuse

- **Treating the `research` survey as the Domain Framing artifact.** The survey
  is an *input* to shape, not the output. Consume its findings; write the typed
  artifact.
- **Asserting an ungrounded domain claim as fact.** If the wrapped research could
  not ground it, it is a *residual assumption*, never a stated fact.
- **Inventing a current system in greenfield.** No current system → omit the half
  and note it; do not reverse-engineer a system that does not exist.
- **A bare out-of-scope list.** Each exclusion carries its *appetite reason*, or
  the scope-creep guard has nothing to reason against.
- **Hardcoding a write path.** Always run the three-tier resolve and surface
  ambiguity; never write to a literal path.
- **Promoting this skill to a mandatory gate.** It produces standalone; the
  non-skippable enforcement is the coordinator's.
