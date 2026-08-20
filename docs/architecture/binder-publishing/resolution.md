# Resolution

> Discovery, identity, ordering, conflicts, diagnostics.
> Part of [binder publishing architecture](README.md).

## Artifact discovery and identity

### Discovery mechanisms, in precedence order

1. **Explicit `path`** — relative to the **content root**, confined beneath it.
   Always available, needs nothing, and **does not require `source-roots`**.
   *(Phase 1)*
2. **Explicit `content-id`** — resolved against the normalized-identity map.
   *(Phase 2)*
3. **Sidecar metadata** — `<file>.binder.toml` beside a source file supplies
   metadata **without modifying the source**. This is how a repository whose
   artifacts carry no YAML frontmatter (including this one) reaches Level 1.
   *(Phase 2)*

   Hand-writing one sidecar per artifact is not a migration path, so Phase 2 also
   ships **`binder sidecar init <path>...`**: it writes a stub sidecar per file
   with `kind` and `producer` inferred from the path (`docs/rfc/` → `kind = "rfc"`,
   `producer = "governance-extras"`), the source H1 as `title`, and `status` and
   `subject` left blank for a human. It never overwrites an existing sidecar and
   never touches the source. Without it, the honest answer to "how is richer
   metadata adopted" would be "by hand, per file, forever."
4. **YAML frontmatter** — an allowlisted field set, when present. *(Phase 2)*
5. **`select` queries over source roots.** *(Phase 2)*

**`pack.toml` is never required.** Where one exists in a scanned root, the
resolver may read `[pack] name` and `display_name` to populate a `producer`
label for provenance display, and nothing else. It cannot affect selection,
ordering, or inclusion.

### No prose-parsing of status markers

This repository's RFCs, ADRs, and specs record status as
`- **Status:** Accepted` in the document body. Parsing that would be immediately
useful and is deliberately **not** done. A Markdown-prose parser is a schema
without a specification: it would break on a status inside a quoted example, a
table cell, or a nested list, and every producer would then be constrained by a
format nobody wrote down. The sidecar supplies the same metadata explicitly, in a
validated format, without touching the source.

### Identity

**Default identity is the normalized relative path** from the content root:
POSIX separators; Unicode NFC normalization; case preserved. Two paths differing
only by case are a **collision error**, not a silent merge — the same recipe must
resolve identically on case-sensitive and case-insensitive filesystems. `..`
segments are rejected before normalization.

A document may declare `canonical-id` (frontmatter or sidecar) to become
path-independent, so a file can move without breaking recipes. Two documents
declaring the same `canonical-id` is a hard error naming both paths.

**Staged filename** is `NNN-<slug>.md` — **three digits throughout**, so a
chapter and an appendix never differ in width, where `<slug>` derives from the content-id
(lowercased, non-alphanumerics to `-`, truncated to 48 characters,
`-<6-hex-of-sha256(content-id)>` appended on collision). Deterministic,
human-readable in a diagnostic, stable across runs with the same inputs. It lives
in `renderer-plan.json`, not the index (invariant 16).

`NNN` — an **adapter-owned** number recorded in `renderer-plan.json`, unrelated to `node-id` — numbers **every staged file in final reading order**, not just resolved
nodes — part pages and generated appendices are interleaved at the position they
occupy in the book, so a directory listing reads in the order a reader
encounters it. Two fixed points: `index.md` carries no prefix, because it is the
site root; and appendices are numbered from `900`. Chapters therefore occupy
`001`–`899`, and **more than 899 chapters is an adapter-stage error (exit 7)**
naming the count — not a *resolution* error, because a numbering ceiling is a
staged-filename convention of this adapter and a second renderer has no reason to
inherit it — a bound worth stating, since the scan cap is 5000 files and nothing
else would have caught the collision.

**Do not confuse `NNN` with the number a reader sees.** `NNN` orders files on
disk; the chapter number in the rendered output is `emitted-ordinal`, written by
the adapter because Z2h found Zensical numbers nothing. They coincide only by
accident — `NNN` counts part pages and appendices, and the reader-facing sequence
does not.

### Scan boundaries

A `select` query scans only declared `source-roots`, bounded and deterministic:

| Rule | Value |
|---|---|
| Roots | only those in `source-roots`, each confined beneath the content root. **When `source-roots` is absent it defaults to `["."]`** — the content root itself — so a recipe that uses selectors without declaring roots scans the whole content root rather than nothing. |
| Included | `*.md`, `*.markdown`, `*.mmd` |
| Excluded by default | `.git/`, `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, the resolved workspace dir, the resolved publication dir — **and every skip beneath a declared source root is recorded in `diagnostics.warnings`** |
| Overriding an exclusion | `[policy] scan-exclusions-override = ["build/docs"]` re-admits a named path. The workspace and publication directories are **not** overridable — a binder that ingests its own output is a rebuild that changes every time. |
| Hidden directories | **not traversed** unless named explicitly in `source-roots`; a skipped hidden directory beneath a source root is warned like any other |
| Symlinks | **never followed** during the walk (`os.walk(followlinks=False)`); a symlinked file encountered as an entry is resolved and confined, and rejected if it escapes |
| Depth cap | 12 levels below a root |
| File count cap | 5000 per run; exceeding it is an error naming the root, not a silent truncation |
| Order | `sorted()` on the normalized relative path — walk order never reaches the output |

A validation error is raised if the publication or workspace directory resolves
inside a `source-root`, because a binder that ingests its own output is a rebuild
that changes every time.

The default exclusion set is a convenience, not a policy: this repository's own
`.gitignore` carries `!packages/agentbundle/agentbundle/build/` precisely because
a blanket `build/` rule *"is silent"*, and a resolver that quietly returned fewer
artifacts than the author expected would fail the same standard the rest of this
section holds ("exceeding it is an error naming the root, not a silent
truncation"). Hence: warn on every skip, and give the author a key to override.

---

## Deterministic resolution

### Algorithm

1. **Load and validate** the recipe against `binder.schema.json`; apply `extends`
   overlay if present; substitute `[params]`.
2. **Resolve the content root** and confine every `source-root`.
3. **Discover** — build the candidate set from explicit references plus, where
   selectors are used, the bounded scan. Normalize identity and metadata.
4. **Select, per section, in authored order.** Explicit references first, then
   selectors. Record a `reason` for every inclusion.
5. **Apply exclusions last.** Exclusions always win over inclusions — but an
   excluded *required* item is an **error**, not a silent drop, naming both the
   requirement and the exclusion rule.
6. **Deduplicate.** The same content-id twice in one section keeps the first and
   records the second. Across sections, a repeat is permitted by default (a
   document can legitimately appear twice) and warns;
   `allow-cross-section-duplicates = false` makes it an error.
7. **Order** — see below.
8. **Resolve supersession.** If A declares `supersedes = ["B"]` and both are
   selected, B is dropped with reason `superseded-by:A` unless
   `keep-superseded = true`, which retains it in a *Superseded material*
   appendix rather than inline.
9. **Emit** `binder-index.json`.

### Text encoding, line endings, and hashing

Four normative guarantees — invariant 15's byte-reproducible index, byte-identical
staged files, `line-offset` accuracy, and `check --published`'s staleness contract —
all change answer on a CRLF source, a BOM, or a non-UTF-8 file. So the rules are
stated rather than inherited:

- **Sources are read as UTF-8 with `errors="strict"`.** A decode failure is exit 4
  naming the file and the byte offset — not a mojibake chapter. (`author-a-skill.md`
  makes `encoding="utf-8"` mandatory precisely because Windows defaults to CP1252.)
- **A leading BOM is stripped** before hashing, before line counting, and before
  staging.
- **Line endings are normalized to LF** for hashing, for staging, and for
  `line-offset` computation. A CRLF source and its LF equivalent therefore produce
  the same `sha256`, the same staged bytes, and the same offset — which is what
  makes a Windows contributor's commit not register as a stale publication.
- **Everything written is LF-only and UTF-8**: staged `.md`, `zensical.toml`,
  `binder-index.json`, `renderer-plan.json`, `binder-stamp.json`.

A unit test asserts a CRLF copy and an LF copy of one file yield identical hashes
and identical staged bytes.

The `line-offset` guarantee is easier to hold than the `line-map` one it replaced:
with the fence *body* transformation gone (Z3a) and the D46 delimiter annotation
changing no line count, only the frontmatter rebuild and the
duplicate-H1 drop shift lines, and both happen at the top of the file. Normalized
line endings are still what makes the offset correct on a Windows contributor's
commit.

### Ordering

Within a section, a total order is produced by:

1. The authored `items` array order forms the **base sequence** (index 0..n-1).
2. Stable sort by `weight` (integer, default 0, ascending). Stability means equal
   weights preserve base order.
3. `before` / `after` constraints form a DAG over the section's items. A
   **deterministic Kahn topological sort** runs over it, and whenever more than
   one node is ready, the one with the lowest current sequence index is chosen —
   yielding the unique order closest to the author's stated sequence that
   satisfies all constraints.
4. Remaining ties break on content-id, ordered by Unicode code point on the NFC
   form.

A cycle is a **hard error** printing the cycle as a path (`A → B → C → A`).

**Constraints are section-scoped. A `before`/`after` naming an item in another
section is a validation error (exit 4)**, because cross-section ordering is what
`[[parts]]` and section order are for. There is no warn-and-ignore path — a
silently dropped ordering constraint is exactly the kind of quiet wrongness this
resolver exists to eliminate.

Sections themselves are ordered exactly as authored. Parts group already-ordered
sections and may not reorder them.

### Behaviours specified

| Situation | Behaviour |
|---|---|
| Missing **required** artifact | Error (exit 5), naming path and section. `on-missing-required = "warn"` downgrades it and records an unresolved gap. |
| Missing **optional** artifact | Recorded in `diagnostics.gaps` and printed in the build summary. **Not rendered into the publication** — see *The provenance appendix is opt-in and closed-field*. Never silent to the builder; never disclosed to the reader by default. |
| Ambiguity (`pick = "one"`, ≠1 match) | Error (exit 5) listing every candidate with its content-id, so the fix is copy-pasteable into `choose`. |
| Duplicate within a section | First wins; second recorded. |
| Content-id collision | Error. Both paths named. |
| Cross-section `before`/`after` | Validation error (exit 4). |
| Route collision (two items → same staged name) | Impossible by construction — the staged name embeds the order index and disambiguates on hash. |
| Unknown status | Normalized to `unknown`, recorded, item retained. `on-unknown-status = "error"` for closed-vocabulary repositories. |
| Drafts | Excluded when `include-drafts = false`, listed in diagnostics as excluded-by-policy with the normalized status that caused it. |
| Conflicting recommendations across artifacts | **Not the resolver's job.** Detecting that two documents disagree is editorial judgment; the resolver surfaces both and the editorial pass may add a note. Claiming otherwise would be a semantic-analysis promise the resolver cannot keep. |
| Child binder inclusion | Phase 3. Contract defined now: an included child contributes its resolved sections as a part; its own `output` and `[renderers.*]` are ignored. |
| Recursive binder cycle | Detected by realpath on the recipe chain; error naming the cycle. Depth cap 5 regardless. |

### Explainability

```
binder explain <recipe-or-index> <content-id-or-path>
```

Output for one artifact — and nothing more, because every line answers a question
someone actually asked:

```
docs/rfc/0091-payments-migration.md
  content-id     docs/rfc/0091-payments-migration.md
  included       yes
  section        proposal (3 of 7)
  position       1 of 1
  selected by    explicit path (binders/payments-review.binder.toml:78)
  required       yes
  label          "RFC-0091: Payments migration"  (from recipe; source title was
                 "RFC-0091: Payments migration to the ledger service")
  metadata       kind=rfc  status=Accepted → current  producer=governance-extras
                 (source: sidecar docs/rfc/0091-payments-migration.md.binder.toml)
  order          base index 0; weight 0; no constraints; final position 1
  staged as      docs/008-docs-rfc-0091-payments-migration.md   (chapter 8)
                 (shown only when a renderer-plan.json for this index-sha256 is in
                  the workspace; the index carries no staged path — invariant 16)
  not selected instead:
    docs/rfc/0088-payments-migration-draft.md
      excluded by [[exclude]] path rule (recipe:104) — "superseded by RFC-0091"
```

### What is deliberately not recorded

No build timestamps, no run IDs, no host names, no user names, no operation log
in the index. **Source SHA-256 *is* recorded**, because one concrete consumer
exists, and it is the CI contract: `binder check --published=<dir>` tells a
pipeline whether a committed publication is stale relative to its sources. That
one consumer justifies the field; nothing else in v1 reads it. (Phase 2's
`--if-stale` will be a second reader, but a field is not justified by a feature
added to justify it.)

---

## Diagnostics, failure modes, and explainability

### Ambiguity error

```
ERROR  Ambiguous selection (exit 5)

  Section "proposal", item 1 declares pick = "one" but 2 artifacts matched
  select = { kind = "rfc", subject = "payments-migration" }:

    docs/rfc/0088-payments-migration-draft.md   status Draft    → draft
    docs/rfc/0091-payments-migration.md         status Accepted → current

  Resolve by one of:
    choose = "docs/rfc/0091-payments-migration.md"      # pick this one
    select = { kind = "rfc", subject = "…", status = "current" }
    [[exclude]] path = "docs/rfc/0088-payments-migration-draft.md"

  Nothing was written.
```

### Path-security rejection

```
ERROR  Path outside approved roots (exit 6)

  Requested  ../../../../etc/passwd
  From       binders/payments-review.binder.toml:52  (section "appendices")
  Resolved   /etc/passwd
  Content root
             /Users/dev/proj

  Every source file must resolve beneath the content root, whether it was
  named by an explicit path or matched by a selector.
  Nothing was read, staged, or written.
```

### Unsafe-Markdown rejection

```
ERROR  Unsafe constructs in source (exit 6)

  notes/vendor-pitch.md:31   raw HTML block <script src="https://…">
      Raw HTML is rendered by the renderer and would execute in the
      reader's browser.
  docs/design/payments/design.md:96   mermaid %%{init: …}%% directive
      Diagram directives can alter renderer configuration.
  docs/design/payments/design.md:214  mermaid click callback
      Diagram callbacks execute code in the reader's browser.

  3 constructs in 2 files. Nothing was staged.

  Options
    remove the constructs (recommended)
    exclude the file:   [[exclude]] path = "notes/vendor-pitch.md"

  There is no profile that permits these. The scan is strict, it is the only
  profile, and nothing relaxes it — see the trust model.
```

**That last paragraph is the whole of D-A, rendered.** The previous version of
this error offered two escape routes — `[policy] shortcodes = "escape"` and a
`trusted` grant in a user policy file, with the exact TOML to paste. Both are
gone: the first had no subject once D-B removed shortcode interpretation, and the
second was the relaxation D-A cut.

An error that names no way out is a real cost and the design does not pretend
otherwise; it is the cost recorded in [`security-profile.md`](security-profile.md) § *The
cost, stated*. What it buys is that the message is true. The old message told an
operator to edit a file that grants trust, which is precisely the instruction an
attacker most wants a frustrated operator to follow.

### Invalid-Mermaid error

```
ERROR  Renderer reported a diagram failure (exit 7)

  source   docs/design/payments/design.md:118  (section "architecture", node n009)
  staged   docs/011-docs-design-payments-design.md:114   (line-offset -4)
  detail   Parse error on line 3: expected 'graph', 'flowchart', 'sequenceDiagram'…
             got 'flowchrt LR'

  Staging retained for inspection:
    .binder-work/payments-review/8f3a91c2/stage/

```

### Successful build summary

```
Binder built.

  Payments Migration Review — payments-review
  Audience  architecture review board · engineering leads · security reviewer
  Renderer  zensical 0.0.53

  12 nodes   9 source · 2 editorial · 1 generated
   7 sections in 3 parts, 1 appendix
   4 mermaid diagrams   6 internal links rewritten   3 assets copied

  Unresolved gaps (1)
    optional  security assessment for payments-migration
              section "risks" — no artifact matched

  Unreviewed editorial content (1)
    binders/editorial/payments-exec-summary.md   review-state: unreviewed

  Published   build/binders/payments-review/index.html
  Index       .binder-work/payments-review/8f3a91c2/binder-index.json
```

Gaps and unreviewed-editorial lines appear on a **successful** build on purpose:
the failure mode this system most needs to prevent is a review board reading a
confident-looking binder that quietly omitted the security assessment.

### Failure-mode table

| Failure | Detection | Behaviour | Exit |
|---|---|---|---|
| Recipe not found / unparseable TOML | load | line and column | 4 |
| Unknown field | validation | names field, table, nearest valid key | 4 |
| Not-yet-implemented key | validation | names the key and its phase | 4 |
| `schema-version` too new | validation | states required and supported | 4 |
| Cross-section `before`/`after` | validation | names both items and their sections | 4 |
| Duplicate `id` or colliding publication dir | validation | names both recipes | 4 |
| Publication directory exists and is not ours | validation | names the path and what was found; the caller empties it themselves | 4 |
| `publication-dir` absolute or escaping the content root | validation | names the resolved path and the content root | 6 |
| Publication parent unwritable, or cross-device without a usable parent | validation | names the path, alongside the `st_dev` check | 6 |
| Caption `fence-sha256` mismatch (Phase 2) | staging | names the caption, both hashes, both first lines | 7 |
| Required artifact missing | resolution | names path and section | 5 |
| Ambiguity | resolution | lists candidates + fixes | 5 |
| Ordering cycle | resolution | prints cycle path | 5 |
| Content-id collision | resolution | names both paths | 5 |
| Recursive binder | resolution | prints recipe chain | 5 |
| Path escape / symlink escape | any read | names requested, resolved, roots | 6 |
| Refused content root (home, filesystem root, ancestor of `~/.agentbundle/` or the pack) | validation | names the resolved root and why it is refused | 6 |
| Node read with a non-Markdown extension | any read | names the file and the three permitted extensions | 6 |
| Unsafe construct | scan | all violations across all files at once; no relaxation offered. **Except under `inventory` and `outline`**, which report the candidate with `unsafe: true` and skip it — a triage verb that dies on one bad file is useless for triage (D29) | 6 |
| Write into installed pack | any write | refuses, names the path | 6 |
| Renderer absent | check | full missing-dependency error; index retained | 2 |
| Renderer present but not the pinned version | check | found + pinned | 3 |
| `nav` target never staged | staging | names the node and the expected staged path (Z2g — the renderer will not catch it) | 7 |
| Render failure, or a `--strict` build reporting issues | invoke | mapped diagnostics with ANSI stripped; staging retained | 7 |
| Lock contention (either lock) | build | waits, then names holder PID and age | 8 |
| Published output stale | `check --published <recipe>` | lists changed sources, and any node added to or removed from the resolved set | 9 |
| Published output built by a different pack version | `check --published <recipe>` | `rebuild-recommended`; compared **before** the index hash, so a pack upgrade does not read as source drift | 10 |
| Python older than 3.11 | first action | names the version found | 11 |
| `check --published` without a recipe | argv parse | names the missing argument and why it is required | 4 |
| Disk full mid-render | invoke | staging retained; publication untouched | 7 |
| Interrupted (SIGINT) | signal | locks released; staging retained; publication untouched | 130 |

---
