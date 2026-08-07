# Outline drafting and pack-supplied recipes

> Two capabilities folded in after the review rounds. Both address the same gap:
> **the first recipe is the hardest one to write**, and the design previously
> assumed one arrived from somewhere.

---

## 1. `binder outline` — draft a recipe from a folder

A user pointing the pack at a directory of Markdown should not have to hand-author
their first `binder.toml`. The skill reads the tree, proposes a binder, and the
human edits or accepts it.

### The verb

```
python scripts/binder.py outline <dir>... --root=DIR [--depth=N]
```

**Read-only, with no exception.** It prints a draft recipe to stdout and writes
nothing at all. The caller decides where it lands — an agent with `Write`, a human
with a shell redirect.

> An earlier version gave it `--out=PATH`. D-A cut that flag along with every
> other caller-named write destination, and the verb is better for it: "read-only"
> was already what this section claimed, and `--out` was the exception that made
> the claim need a qualifier.

### What it does

1. **Walk** the given directories under the same bounded, deterministic scan the
   resolver uses — `*.md`, `*.markdown`, `*.mmd`, symlinks not followed, hidden
   directories skipped, the same caps and the same warned exclusions.
2. **Scan** every candidate under the trust profile, exactly as `resolve` does.
   An unsafe file is reported with `unsafe: true` and kept out of the draft rather
   than failing the verb — an outline that dies on one bad file is useless for
   the triage it exists to support.
3. **Read structure, not prose** — each file's first H1, its heading skeleton,
   its diagram count, its size, and its directory position.
4. **Propose sections from the directory tree**, because in practice the tree
   already encodes intent: `docs/rfc/` becomes a section, `docs/adr/` becomes a
   section, a flat folder becomes one section. Directory depth beyond `--depth`
   (default 2) collapses into the parent.
5. **Order within a section** by filename, which is why `0091-` prefixes and dated
   filenames sort usefully. Numeric prefixes are detected and sorted numerically,
   so `0009` precedes `0010`.
6. **Emit a draft recipe** with every item as an **explicit `path`** — Level 0,
   no selectors, no metadata required — plus a commented block naming what it
   noticed but did not decide.

### What it must not do

- **Never guess a title, purpose, or audience.** Those are editorial and the
  binder's whole value is that a human chose them. The draft leaves them as
  `TODO` comments, and validation refuses a recipe that still contains one.
- **Never silently drop a file.** Anything walked but not included appears in the
  draft as a commented `# skipped: <path> — <reason>` line, so the human sees the
  whole tree and decides. Silent omission is precisely what makes a generated
  outline untrustworthy.
- **Never write.** There is nothing to overwrite, because the verb has no
  destination.

### Worked shape

```toml
# Drafted by `binder outline docs/` on 12 files across 3 directories.
# Review every TODO before building — the outline proposes structure, not intent.

schema-version = "1"
id    = "TODO-binder-id"          # kebab-case, unique per content root
title = "TODO — what a reader should call this"
# purpose  = "TODO — what decision this binder supports"
# audience = ["TODO"]

[[sections]]
id    = "rfc"
title = "RFC"                      # from directory name — rename freely

[[sections.items]]
path  = "docs/rfc/0091-payments-migration.md"
label = "RFC-0091: Payments migration to the ledger service"   # from first H1

[[sections.items]]
path  = "docs/rfc/0093-payments-strangler.md"
label = "RFC-0093: Strangler migration"

[[sections]]
id    = "adr"
title = "ADR"

[[sections.items]]
path  = "docs/adr/0044-ledger-boundary.md"
label = "ADR-0044: Ledger boundary"

# skipped: docs/rfc/README.md — index page, rarely wanted in a binder
# skipped: notes/vendor-pitch.md — unsafe: raw HTML at line 31
# noticed: 4 documents contain Mermaid diagrams
# noticed: docs/specs/ has 2 files but was below --depth; pass --depth=3 to expand
```

### Where it sits in the flow

```
outline  →  human edits  →  check  →  resolve  →  build
```

`outline` is deliberately **outside** the compilation path — it produces an
input to it, and every downstream verb treats its output as an ordinary
hand-written recipe. There is no privileged "generated recipe" path, which is the
same rule the editorial pass follows.

### Relationship to the editorial pass

They are different jobs and both should exist:

| | `outline` | Editorial pass |
|---|---|---|
| Runs | Deterministic script | A model |
| Reads | Structure — headings, names, counts | Content, in full |
| Decides | Nothing editorial | Selection, ordering, prose |
| Output | A draft skeleton with TODOs | A complete recipe plus editorial Markdown |
| Cost | Milliseconds | A model pass over the corpus |

`outline` is the honest default for "I have a folder"; the editorial pass is for
"I have a purpose and an audience." **`outline` is also the editorial pass's
cheapest input** — the pass can start from a draft rather than a bare directory
listing, which is a better use of the model's attention than filename triage.

---

## 2. Pack-supplied recipe templates

The design already assumed reusable recipes exist — *architecture review*,
*implementation handoff*, *release readiness*. It never said how a pack ships one,
which left the ecosystem seam asserted rather than specified.

### The design this replaces, and why it could not ship

The previous version had `binder.py` **walk the installed skill roots for the
active adapter**, globbing `*/assets/binders/*.binder.toml` across every pack the
adopter had installed, and identifying each hit as `<pack>/<name>`.

**That violates `author-a-skill.md` § *Three rules to get right the first time*,
third bullet**, which is unambiguous:

> *"Each skill is self-contained. Never read from, import from, or **assume the
> presence of files in another skill's directory** — including sibling skills in
> the same pack. Skills are projected independently to each adapter; cross-skill
> paths that look valid in the source tree do not survive projection."*

This is not a technicality, and it is not a rule the design can weigh against
convenience — it is the **same rule [`editorial-model.md`](editorial-model.md)
cites, from the same paragraph, to justify the one-skill pack shape.** A design
that invokes self-containment to reject the two-skill option and then walks other
skills' directories for templates is applying one rule in two directions.

The rule's own stated reason is also the operational one. Skills are projected
independently, per adapter, at whichever scope the adopter chose. A walk over
"installed skill roots" would have to know seven adapters × three scopes of layout
— exactly the knowledge `references/invocation.md` exists to keep out of the skill
body — and would still miss a producing pack installed at a different scope, find
nothing on a fresh machine, and silently return a different list per adapter. **A
discovery mechanism whose results depend on the adapter is not a seam.**

### Discovery, restricted

**`templates` discovers exactly one directory: this skill's own `assets/binders/`.**

```
python scripts/binder.py templates            # list this pack's templates
python scripts/binder.py templates <name>     # copy one into recipes_dir
```

- The lookup is **skill-relative** — `assets/binders/<name>.binder.toml` — which
  is the form the path-discipline rule requires and the only form that survives
  projection unchanged.
- There is **no walk**, no glob outside the skill directory, and no adapter-layout
  knowledge anywhere in the verb.
- **The destination is derived, not supplied:** `<recipes_dir>/<name>.binder.toml`,
  refusing an existing path. `--out` went with D-A along with every other
  caller-named write target.
- The copy carries a provenance comment naming the pack and version. From that
  moment it is the adopter's file: they edit it, commit it, and it never changes
  under them when the pack upgrades.

Names are now flat rather than `<pack>/<name>`, because there is one source and
therefore nothing to disambiguate.

### The cross-pack seam: the producer copies, the consumer does not discover

A pack that wants to ship a binder template **writes it into the adopter's
`recipes_dir`** — at install time, at first run, or from one of its own skills.
That is all.

```
producing pack  ──writes──▶  <content-root>/binders/<name>.binder.toml
                                          │
                                          ▼
                          an ordinary recipe. `binder build` reads it
                          with no knowledge that a pack put it there.
```

**The direction is what matters.** The old seam had the consumer reach into the
producer's directory; this one has the producer place a file in a location both
already agree on. It costs the producing pack one file write and gives up nothing
the walk provided:

| | Old — consumer discovers | New — producer copies |
|---|---|---|
| Self-containment | **Violated** | Held — no skill reads another skill's directory |
| Survives projection | No — layout differs per adapter and scope | Yes — `recipes_dir` is adopter configuration, not an install path |
| What the producer must know | where its own assets land after projection | where `recipes_dir` is |
| What the consumer must know | seven adapter layouts × three scopes | nothing |
| When a malformed template surfaces | at `templates` time, in the consumer | at author time, in the producer, where it can be fixed |
| Coupling | a shared directory *convention* inside installed packs | none — the artifact is a plain recipe |

The interop requirement is preserved exactly: **a producing pack participates with
`tomllib` and nothing else.** It writes a TOML file to a path the adopter already
configured. It imports nothing, reads nothing of this pack, and does not need this
pack installed to write one.

**What is genuinely lost:** an adopter can no longer run one command and see every
template every installed pack ships. That was the walk's only real benefit, and it
was never reliable — the list depended on the adapter. The replacement is that a
producing pack documents its templates in its own README, which is where an
adopter looks for what a pack offers anyway.

### Why not a manifest key

`[pack.integrations]` exists and could declare a binder-template seam. It is still
not used, and the reason survives the redesign: **a producing pack must be able to
participate with `tomllib` and nothing else.** A manifest key would mean a pack
shipping a template must know *this* pack's schema for declaring it — and it would
reintroduce the discovery step, since something would then have to read those
manifests.

Writing a file to `recipes_dir` requires knowing one path and one format, both of
which the producing pack must know anyway to author the template at all.

### What a template may and may not contain

- **May:** sections, parts, appendices, `required-params`, ordering, exclusions,
  labels, `[renderers.*]` options, and TODO comments.
- **May not:** absolute paths, or a `publication-dir` outside the content root. A
  template is repository content the moment it lands, so it has exactly the
  authority repository content has — none. (An earlier version also barred a
  `[policy] profile` other than the default; D-A removed the key, so there is
  nothing left to bar.)
- **Should:** use `required-params` for the subject rather than hard-coding one,
  which is what makes *architecture review* reusable rather than a single binder.

**Validation runs before the copy**, not after — a template that fails the recipe
validator is reported and not written, whether it came from this pack's assets or
from a producing pack's own write path. Where it came from changes nothing about
how much it is trusted.

---

## 3. `recipe write` — the editorial write path

The editorial pass returns a recipe and its prose as a *value*; `recipe write` is
what puts them on disk. It is specified here rather than left implicit because
[`security-profile.md`](security-profile.md) names it as the mechanism that brings
the editorial pass under the write set — a control resting on an unspecified verb
is not a control.

```
python scripts/binder.py recipe write <name> [--root=DIR]
```

- **Input arrives on stdin**, as a JSON document holding the recipe and zero or
  more editorial documents. Not a path: a path argument would be a read the
  editor chose, and the whole point is that the editor hands over content rather
  than pointing at it.
- **Both destinations are derived**, per D41:
  - the recipe → `<recipes_dir>/<name>.binder.toml`
  - each editorial document → `<recipes_dir>/editorial/<slug>.md`, where `<slug>`
    is derived from the document's declared role and title by the same
    slugification the staged filenames use.
- **`<name>` and every `<slug>` must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`**
  after derivation. A separator, a `..`, or a leading dot is exit 4. This is what
  stops a returned title from becoming a path.
- **An existing path is refused**, exactly as `templates <name>` refuses one —
  exit 4 naming the file. The editor never overwrites; a human who wants to
  replace an approved recipe deletes it first.
- **The recipe is validated before either write**, and a validation failure writes
  nothing at all — not the recipe, not the prose. A half-written editorial set
  beside no recipe is worse than a clean failure.
- **Nothing else is written**, and the write set is what enforces it. The verb has
  no route to a source, to the publication, or to the pack.

`--editorial=DIR` used to let the caller name where the prose landed. It is cut
(D41): the write set admitted only one directory anyway, so the flag could only
ever name the value the verb now derives.

### The catalogue's own templates

`binder-publishing` ships three in its own `assets/binders/`, which double as the
worked examples and as the multi-pack fixture's input:

| Template | Shape |
|---|---|
| `architecture-review` | Evidence → proposals → decisions → architecture → risks, parameterized by subject |
| `implementation-handoff` | Decision → spec → plan → verification |
| `release-readiness` | Changelog → verification → risks → rollback |

Shipping them from the owning pack rather than from `core` is deliberate: they
are examples of the format, not governance seeds, and a pack that ships the
format should ship its own reference uses of it.

**The multi-pack fixture needs one adjustment.** It previously asserted that "one
producing pack ships the recipe template; the publication pack consumes it without
importing anything from it" — which under the old seam meant the consumer walked
and found it. It now asserts the producer **writes** its template into the
fixture's `recipes_dir` and that `binder build` resolves it as an ordinary recipe.
The property under test is unchanged and the mechanism is one the rule permits.
