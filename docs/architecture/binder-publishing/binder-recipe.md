# The binder recipe

> `binder.toml` — the authored contract and how it evolves.
> Written against D-A (strict-only, no policy file) and D-B (Zensical).
> Part of [binder publishing architecture](README.md).

## Binder recipe schema

Versioned, sparse, TOML-authored, human-writable. Every key except
`schema-version`, `id`, `title`, and at least one section is optional.

**Phase column:** `1` = implemented in v1 (Phases 0–1). `2`/`3` = defined in
schema v1, validated, and **rejected at runtime with a "requires a later
publish-binder" message** until that phase ships — never silently ignored. See
*Not-yet-implemented keys*.

### Complete surface

Every key used anywhere in this document appears here. For a schema published as
a versioned public contract whose validator hard-errors on unknown keys,
"complete" is itself a contract statement.

| Key | Phase | Notes |
|---|---|---|
| `schema-version` | 1 | required; string |
| `id` | 1 | required; `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`; unique per content root |
| `title`, `subtitle`, `purpose`, `audience`, `subject`, `status` | 1 | binder identity |
| `renderer` | 1 | default `"zensical"`. The only value v1 accepts; the key exists so a second adapter is additive rather than a schema change |
| `source-roots` | 2 | array; confined beneath the content root. Bounds **selector scanning only** (D33), and selectors are Phase 2 — so a v1 recipe declaring it gets a validator **warning**: *"`source-roots` has no effect until selectors ship (Phase 2). It never was a confinement boundary — control 1 confines every path to the content root regardless — so narrowing it does not narrow what can be read."* The wording matters: an author who set it expecting a security narrowing must be told plainly that they did not get one. Warned rather than errored, because a recipe written for Phase 2 should still build at Phase 1. |
| `extends` | 3 | overlay base |
| `[params]` | 1 | Parameter definitions — every key here is a parameter *name*. Substitution is permitted only into the closed set of **target** keys enumerated in *Parameter substitution*; the two lists are different things. |
| `required-params` | 1 | top-level array of parameter names that must be supplied at invocation. A name listed here is **not** satisfied by a default in `[params]` — the point is to force the caller to state it; a key that wanted a default should not be in this list. Deliberately **not** inside `[params]` — a `required` key there would make a parameter named `required` unrepresentable, which is the same flaw as the `"REQUIRED"` sentinel it replaced, one level down. |
| `[status-map]` | 2 | `current` / `draft` / `retired` → arrays of producer vocabularies |
| `[policy] on-missing-required` | 1 | `error` (default) \| `warn` |
| `[policy] on-ambiguous` | 2 | `error` (default) \| `first` \| `all` |
| `[policy] on-unknown-status` | 2 | `warn` (default) \| `error` \| `ignore` |
| `[policy] include-drafts` | 2 | default `false` |
| `[policy] allow-cross-section-duplicates` | 1 | default `true` (warns) |
| `[policy] scan-exclusions-override` | 2 | array of paths re-admitted to a `select` scan; never the workspace or publication directory |
| `[policy] keep-superseded` | 2 | default `false` |
| `[output] publication-dir`, `workspace-dir` | 1 | **relative to the content root, with no exception.** An absolute or `..`-escaping value is **exit 6** — D-A removed the grant that used to admit one. This is the single statement; the cross-device `EXDEV` path still exists, because a mount point beneath the content root is a normal configuration. |
| `[renderers.<name>]` | 1 | opaque to the core; adapter-allowlisted |
| `[x-<vendor>]` | 1 | reserved third-party namespace; copied verbatim to `extensions`. Same shape constraint as `[renderers.*]` — scalars or arrays of scalars only, 8 KB per table — because the index is a published artifact and an unbounded opaque blob in it is an unbounded opaque blob in everyone's publication. |
| `[[sections]] id`, `title` | 1 | required per section |
| `[[sections]] kind` | 1 | `source` (default) \| `editorial` \| `generated` |
| `[[sections]] numbered` | 1 | **default depends on `kind`** — `true` for `source`, `false` for `editorial` and `generated`. **Numbering is compiler-emitted and presentational** (D44): Z2h verified Zensical numbers nothing, so `true` makes the adapter emit a `data-ordinal` attribute the theme renders with CSS — **never text inside the title**, so the number stays out of the search index and the browser tab. Appendices are lettered by the same mechanism, and `numbered` on an appendix-reached section is therefore meaningful rather than ignored — see `[[appendices]] sections`. |
| `[[sections]] intro` | 1 | path to an editorial section introduction |
| `[[sections]] position` | 3 | `first` \| `last`; overlay-only placement hint |
| `[[sections.items]] path` | 1 | explicit reference |
| `[[sections.items]] content-id` | 2 | explicit reference by declared identity |
| `[[sections.items]] label` | 1 | per-binder display override |
| `[[sections.items]] role` | 1 | `executive-summary` \| `decision` \| `risk` \| `open-question`. **Display-only** — it selects a callout style and a badge, and never relocates a node. `appendix` is deliberately *not* in the enum: placement is `[[appendices]]`'s job, and a role that silently moved a chapter would be two mechanisms for one outcome. |
| `[[sections.items]] required` | 1 | default `false`; may not co-occur with `select` |
| `[[sections.items]] weight` | 1 | integer, default 0 |
| `[[sections.items]] before`, `after` | 1 | same-section content-ids only |
| `[[sections.items]] numbered` | 1 | per-item override |
| `[[sections.items]] select` | 2 | `{ kind, subject, status, producer }` |
| `[[sections.items]] pick` | 2 | `all` (default) \| `one` \| `latest` (`latest` is Phase 3) |
| `[[sections.items]] choose` | 2 | disambiguator for `pick = "one"` |
| `[[sections.items]] order` | 2 | `path` (default) \| `date` |
| `[[sections.items.figures]]` | 2 | `ordinal` + `caption` + optional `fence-sha256` — see *Caption binding*. Moved out of v1: captions are the sole reason the hash-verification protocol exists, and Level-0 diagrams render fine without them. |
| `[[sections.overrides]]` | 3 | overlay-only; `section` + replacement `items` |
| `[[parts]] id`, `title`, `sections` | 1 | one nesting level. Z2a verified the nested `nav` form renders as a titled sidebar group; deeper nesting is a validation error with a clear message, never a silent flattening |
| `[[appendices]] id`, `title`, `kind` | 1 | `kind = "generated"` (compiler output) or `"source"` |
| `[[appendices]] generator` | 1 | closed enum, currently `source-inventory`. Required when `kind = "generated"`; this is what makes the provenance appendix opt-in. |
| `[[sections.items]] review-state` | 1 | `unreviewed` (default) \| `reviewed`. Editorial items only; the one field a human sets by hand. |
| `<recipe>` format | 1 | inferred from suffix: `.json` parsed as JSON, everything else as TOML. A parse failure against the inferred format is exit 4 naming both the inferred format and the suffix, rather than silently retrying the other. |
| `[[appendices]] sections` | 1 | array of section ids, mirroring `[[parts]]`. This is how **source artifacts reach an appendix**; without it the only possible appendix would be compiler-generated, and `keep-superseded`'s promised *Superseded material* appendix would have no way to exist. `numbered` **is** honoured here, unlike under the Quarto adapter where Q17's automatic lettering made it a no-op: since Z2h established that the compiler emits every ordinal itself, an unlettered appendix is now expressible. |
| `[[exclude]] path` / `select` / `reason` | 1 (`path`) / 2 (`select`) | evaluated last; always wins |
| `[[include-binder]]` | 3 | child binders |

### What `[policy]` no longer contains

D-A removed `[policy] profile` and D-B removed `[policy] shortcodes`. Neither is
deprecated: both are **unknown keys**, and a recipe carrying either is exit 4 with
the ordinary unknown-field message.

That is deliberate rather than harsh. A deprecation warning implies the key once
did something the author might still want; these two named a trust relaxation that
no longer exists and a renderer behaviour that no longer exists. Warning would
suggest a migration path where there is none — the honest message is "this key is
not in the schema", plus the nearest-valid-key suggestion the validator already
emits.

**`[policy]` is now purely resolution semantics** — what to do about a missing
required artifact, an ambiguous selector, an unknown status, a draft, a
cross-section duplicate. Nothing in it reaches trust, and nothing in it reaches a
path. That is what makes the substitution rule below simple enough to state in one
line.

### Parameter substitution — a closed surface

`--param=K=V` is part of the invocation string, which the threat model treats as
untrusted, so an undefined substitution surface is an undefined injection surface.
Substitution is therefore restricted:

- **Substitutable:** `title`, `subtitle`, `purpose`, `subject`, `audience[]`,
  `[[sections]] title`, `[[parts]] title`, `[[appendices]] title`,
  `[[sections.items]] label`, and the values inside `select = { … }`.
- **Substitutable *under slug validation*:** `id` and `[output] publication-dir`.
  Without this, `--param=subject=A` and `--param=subject=B` — the design's headline
  parameterization — produce different content-keys (different workspaces, no lock
  contention) that publish to the *same* directory, and the last writer silently
  wins; the duplicate-publication-dir validation does not fire because it is one
  recipe. Substituted values in these two keys must match `^[a-z0-9-]+$` **after**
  substitution, which keeps the path-injection ban intact — a slug cannot contain
  a separator or a `..`.
- **Not substitutable:** every other path-valued key (`path`, `source-roots`,
  `extends`, `intro`), every `[renderers.*]` value, and every `[policy]` value. A
  parameter that could name a path would turn `--param` into a file selector; one
  that could reach `[policy]` would turn it into a resolution-semantics knob
  settable from the invocation string. The second is a weaker objection than it
  was — D-A left no trust value in `[policy]` for a parameter to reach — but the
  rule stays, because "`--param` substitutes into display strings and selector
  values" is a smaller thing to specify and to test than any partial exception.
- **Single-pass and non-recursive.** `${a}` expanding to a string containing
  `${b}` leaves `${b}` literal. No recursion means no expansion bombs and no
  order-dependence.
- An unresolved `${name}` with no matching param is a validation error naming the
  key, never an empty string.
- Substituted values are strings and pass the same control-character validation as
  authored strings (see *String emission*).

### Worked recipe

> **Abridged.** This prints three of the twelve sections the payments-review
> fixture carries, chosen to exercise every *key shape* — an editorial section, a
> section with an `intro` and ordering constraints, a required item, a part, a
> generated appendix, an exclusion. The full fixture is the one the node counts in
> [`examples.md`](examples.md), [`resolution.md`](resolution.md), and
> [`editorial-model.md`](editorial-model.md) refer to: **12 nodes — 9 source, 2
> editorial, 1 generated.** Do not count items here and expect them to match.

```toml
schema-version = "1"

id       = "payments-review"
title    = "Payments Migration Review"
subtitle = "Architecture review board packet"
purpose  = "Decide whether to approve the payments migration for build."
audience = ["architecture review board", "engineering leads", "security reviewer"]
subject  = "payments-migration"
status   = "for-review"
renderer = "zensical"

source-roots = ["docs", "notes"]

[params]
subject = "payments-migration"

[policy]
on-missing-required = "error"

[output]
publication-dir = "build/binders/payments-review"
workspace-dir   = ".binder-work"

[renderers.zensical]
mermaid-theme = "neutral"
toc-depth     = 3

[[sections]]
id       = "summary"
title    = "Executive summary"
kind     = "editorial"
numbered = false

[[sections.items]]
path = "binders/editorial/payments-exec-summary.md"
role = "executive-summary"

[[sections]]
id    = "context"
title = "Context and evidence"
intro = "binders/editorial/context-intro.md"

[[sections.items]]
path   = "docs/product/research/payments-landscape-survey.md"
label  = "Payments landscape survey"
weight = 10

[[sections.items]]
path   = "notes/vendor-comparison.md"
weight = 20
after  = "docs/product/research/payments-landscape-survey.md"   # same section

[[sections]]
id    = "proposal"
title = "Proposal"

[[sections.items]]
path     = "docs/rfc/0091-payments-migration.md"
required = true

[[parts]]
id       = "evidence"
title    = "Part I — Evidence"
sections = ["context"]

[[appendices]]
id    = "provenance"
kind  = "generated"
title = "Source inventory and provenance"

[[exclude]]
path   = "docs/rfc/0088-payments-migration-draft.md"
reason = "superseded by RFC-0091"
```

Note the `after` constraint names an item **in the same section**. Cross-section
`before`/`after` is a validation error — see *Ordering*.

### Where semantic queries are acceptable, and where they are not

| Context | Rule |
|---|---|
| A **required** item in a decision-bearing section | Exact `path` or `content-id` only. `select` with `required = true` is a **validation error**: "a required artifact must be named, not queried." A query silently resolving to the wrong document in a packet a board approves is the highest-consequence failure this system can have. |
| An optional supporting item | `select` permitted. |
| Exclusions | `select` permitted and encouraged — over-exclusion fails safe (absent, and in diagnostics); over-inclusion does not. |
| `pick = "one"` | Requires exactly one match, or an explicit `choose`. Zero or 2+ without `choose` is an ambiguity error. |
| Overlays | May add exclusions and exact references. May **not** convert an exact reference into a selector. (An earlier version also barred an overlay from loosening `[policy] profile`; D-A removed the key, so there is nothing left to loosen.) |

### Schema evolution

- **`schema-version` is a string**, `"1"`, `"2"`, … A minor evolution does not
  bump it; only a change that would make an older validator wrong does.
- **Additive-only within a major version.** New optional keys may be added; no
  key changes meaning, type, or default.
- **Unknown fields are a hard error by default** (exit 4), not a silent ignore. A
  typo'd `weigth = 10` that silently does nothing is worse than a failed build.
  The message names the unknown key, the containing table, and the nearest valid
  key by edit distance.
- **Two escape hatches:** `[x-<vendor>]` tables at any level are reserved for
  third parties, ignored by the core, and copied verbatim into the index under
  `extensions`; `--allow-unknown-fields` downgrades the *unknown-field* error to a
  warning for forward compatibility with a newer producer. **It never applies
  inside `[policy]`** — an unknown key there is exit 4 at every level, because a
  v2-only key that *tightens* resolution behaviour, silently discarded by a v1
  binary, is a relaxation performed by a flag reachable from a committed
  `Makefile`. (There is no `[trust]` table; D-A deleted it with the lattice that
  read it.) It
  also **does not downgrade the not-yet-implemented class** — a `select` that silently does nothing is the
  failure D15 exists to prevent, and a flag that re-enables it would undo the
  decision.
- **A recipe declaring a `schema-version` newer than the validator** fails with
  "recipe requires schema-version N; this build of publish-binder supports up to
  M — upgrade the pack", never a best-effort parse.
- **Deprecation:** a key marked deprecated in version *N* warns in *N*, and may
  be removed only in *N+1*. The warning names the replacement.
- **Serialization:** TOML is the only **human**-authored form; an equivalent JSON
  document against the same schema is an accepted **machine-producer** input; the
  skill writes only TOML. (Rationale: `json` is stdlib everywhere, a TOML
  *writer* is not, and one human format keeps documentation and examples single.)

### Not-yet-implemented keys

A key that is valid in schema v1 but whose *behaviour* arrives in a later phase
gets its own validator class and its own message — never an unknown-field error
(misleading) and never a silent ignore (dangerous):

```
ERROR  Key requires a later publish-binder (exit 4)

  binders/architecture-review.binder.toml:31
    select = { kind = "research", subject = "${subject}" }

  `select` is valid in schema-version 1 but is implemented from Phase 2.
  This build implements Level 0 (explicit paths).

  Phase-2 keys not yet implemented:  select · pick · choose · order ·
                                     content-id · [status-map] ·
                                     [policy] on-ambiguous / on-unknown-status /
                                     include-drafts / keep-superseded ·
                                     [[exclude]].select
  Phase-3 keys not yet implemented:  extends · [[sections.overrides]] ·
                                     [[sections]].position · [[include-binder]] ·
                                     pick = "latest"

  Replace the selector with explicit `path` references, or upgrade the pack.
```

The phase lists are generated from a single table in `binder.py`, so they cannot
drift from what the build actually implements.

---

## Metadata adoption levels

Each level is independently useful; none is a prerequisite for the one below it
being valuable.

**Level 0 — explicit files.** A recipe lists paths. No metadata anywhere. Primary
path, sufficient permanently. **v1.**

**Level 1 — semantic metadata.** Optional, from frontmatter or a sidecar, over a
closed allowlist:

| Field | Type | Meaning |
|---|---|---|
| `kind` | string | artifact kind — free-form, lowercased; suggested vocabulary shipped, not enforced |
| `subject` | string or array | what it is about; the primary selector axis |
| `status` | string | producer's own vocabulary; normalized via `[status-map]` |
| `producer` | string | which pack/skill/workflow produced it |
| `canonical-id` | string | stable identity |
| `supersedes` | array of ids | conflict resolution input |
| `related` | array of ids | cross-link display only |
| `binder-role` | string | hint: `executive-summary`, `appendix`, `decision`, … |
| `date` | ISO-8601 date | ordering input for `pick = "latest"` |
| `title` | string | display label if the recipe does not override |

Anything else in frontmatter is **discarded**, not passed through. **Phase 2.**

**Level 2 — producer conventions.** A pack may document what it emits, optionally
declaring it under `[pack.metadata.binder]`. **No central registry, no shared
file any pack must edit.** A pack that declares nothing is fully usable at Levels
0 and 1. **Phase 3, and optional forever.**

**Level 3 — generated binders.** A workflow, editor, script, or CI job generates
a complete recipe or overlay. Same schema, validator, resolver, renderer.
**Phase 3.**

**Level 4 — multiple consumers.** A second renderer, or the docs site, consumes
the same `binder-index.json`. **Phase 4+, contract-ready from v1.**

---
