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
python scripts/binder.py outline <dir>... --root=DIR [--out=PATH] [--depth=N]
```

**Read-only.** It writes nothing unless `--out` is given, and even then it writes
a *draft recipe*, never a publication.

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
- **Never write over an existing recipe.** `--out` refuses an existing path.

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

### The convention

A pack ships recipe templates in its own skill assets:

```
packs/<pack>/.apm/skills/<skill>/assets/binders/<name>.binder.toml
```

Nothing more. **No registry, no manifest key, no install-time copy, no code
import** — which is what keeps the seam a file convention rather than a coupling.

### How they are found

```
python scripts/binder.py templates            # list what is discoverable
python scripts/binder.py templates <name> --out=binders/<name>.binder.toml
```

Discovery walks the **installed skill roots for the active adapter** — the same
per-adapter paths `references/invocation.md` documents — for
`*/assets/binders/*.binder.toml`. A template is identified as
`<pack>/<name>`, so two packs may ship a template with the same name without
collision.

**Templates are copied, never referenced.** `templates <name> --out=` writes a
copy into the caller's `recipes_dir` with a provenance comment naming the source
pack and version. From that moment it is the adopter's file: they edit it, commit
it, and it never changes under them when the pack upgrades. A referenced template
would make every build depend on which pack version happened to be installed,
which is the coupling the interop requirement forbids.

### What a template may and may not contain

- **May:** sections, parts, appendices, `required-params`, ordering, exclusions,
  labels, `[renderers.*]` options, and TODO comments.
- **May not:** absolute paths, a `[policy] profile` other than the default, or
  anything the trust model classifies as a grant. A template is repository content
  once copied, so it inherits exactly the authority repository content has —
  none.
- **Should:** use `required-params` for the subject rather than hard-coding one,
  which is what makes *architecture review* reusable rather than a single binder.

### Why not a manifest key

`[pack.integrations]` exists and could declare a binder-template seam. It is not
used, for the reason the seam exists at all: **a producing pack must be able to
participate with `tomllib` and nothing else.** A manifest key would mean a pack
that wants to ship a template must know this pack's schema for declaring it. A
directory convention means it must know only where to put a file.

The cost is that discovery is a filesystem walk rather than a manifest read, and
that a malformed template is found at `templates` time rather than at pack-lint
time. Both are acceptable: the walk is bounded to installed skill roots, and
`templates <name>` validates before copying.

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
