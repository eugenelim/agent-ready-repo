# Rollout, testing, and open questions

> Phases, test strategy, CI wiring, unresolved decisions.
> Part of [binder publishing architecture](README.md).

## Testing and eval strategy

Tests live at `packs/binder-publishing/tests/skills/publish-binder/`, outside the
`.apm/` runtime boundary. Evals live at `.apm/skills/publish-binder/evals/`.

### Unit

Schema parsing · `schema-version` behaviour · unknown-field error and
`--allow-unknown-fields` · **not-yet-implemented key class, per phase** ·
`[x-vendor]` passthrough · content-root resolution in all four branches ·
configuration precedence · **the trust lattice** (recipe cannot grant; repo policy
cannot grant; `--profile trusted` without a grant exits 6; a `--quarto` path
beneath the content root is refused; grant matching is realpath-containment and
resists a planted symlink) · identity normalization and case collision ·
status-map normalization and unknown status · stable ordering · weight sorting ·
`before`/`after` topological order · **cross-section constraint is exit 4** ·
cycle detection · ambiguity · missing required vs optional · duplicate handling ·
supersession · exclusion beating inclusion · excluded-required erroring ·
**duplicate `id` and colliding publication dir** · child-binder cycle detection ·
frontmatter discard-and-rebuild · fence transformation (mermaid and non-mermaid) ·
**shortcode reject and escape modes, including that `escape` emits the
brace-tripled form** · Mermaid directive/click/callback/label rejection at both
profiles · link rewriting · **`line-map` accuracy across all five
length-changing steps, property-tested against randomly generated sources** ·
staged-name determinism and hash disambiguation · path traversal · absolute paths
· symlink escape · asset allowlist · resource ceilings · self-path write refusal ·
argv construction (never a shell string, never `publish`) · **environment
allowlist construction — assert a planted `AWS_SECRET_ACCESS_KEY` is absent from
the child env** · **`--quarto` beneath the content root is refused (control 25a)** ·
**YAML injection — a recipe `title` of `"X\nfilters:\n  - evil.lua"` is rejected at
validation, and with the validator stubbed out the emitter still yields a
`_quarto.yml` whose parsed form has no `filters` key** · **shortcode syntax in an
emitted string — a recipe `title` of `"{{< env HOME >}}"` is exit 4, the same as a
source H1 is exit 6 with fallback to the file stem** · **label resolution across
all four rules, including a source H1 carrying a control character falling through
to the file stem** · **parameter substitution confined to the closed key list,
single-pass, erroring on an unresolved `${name}`** · **`escape` mode idempotent on
already-escaped shortcodes** · **publication-ownership check — a foreign directory is exit 4 and is not
renamed** · **`--out` outside workspace/publication/temp is exit 6** · **heading shift clamps at H6 and warns** ·
**scan exclusions warned, `scan-exclusions-override` re-admits** · **invariant 22 —
a golden index from `resolve` is byte-identical to the index after `build`** ·
**cross-device publication detected at validation** · exit-code mapping including
9 and 130.

### Integration

**Gates V1, V2, V2b, V3, V5 against the single shared fixture, and V4 on the
platform matrix** (all required in CI as regression assertions once passed) ·
**V2b's zero-`https://`-in-`_output/` assertion, CSS included** · Quarto detection
present/absent/wrong-version · generated `_quarto.yml` against golden files **for both profiles** (they differ only in the `from:` string) ·
successful HTML render · parts and chapters present · search index generated ·
previous/next present · Mermaid rendered as SVG · invalid Mermaid mapped to the
source line · idempotent rebuild produces a byte-identical index · `check --published` returns 0 fresh / 9 stale · interrupted
build leaves no corrupt state · **two concurrent different binders both succeed**
· two concurrent identical builds serialize on the workspace lock · **two
different recipes targeting the same publication dir are rejected at validation,
and the publication lock serializes the case that slips through** · near-atomic
publication replacement, **including the cross-device copy path** ·
**`binder-stamp.json` present in the published tree while `binder-index.json` is
absent from it, the stamp carrying no `diagnostics` key, and `check --published`
returning 9 after a source edit** · **two concurrent `install-quarto` runs
serializing on the toolchain lock** · `clean` confinement.

Renderer-dependent tests skip with a clear reason when Quarto is absent and are
**required** in CI, where Quarto is provisioned by the pipeline.

### CI provisioning — the wiring this needs, named

This repository wires pack tests by **explicit enumeration** —
`.github/workflows/catalogue-tooling-ci-gates.yml` runs
`python -m pytest packs/core/tests/ packs/product-documentation/tests/ -q` — so a
new pack's tests do not run until someone adds them. "Required in CI" is a change
to a file, not a property that arrives by itself:

| Change | Where |
|---|---|
| Add `packs/binder-publishing/tests/` to the pytest invocation | `catalogue-tooling-ci-gates.yml` |
| Add a Quarto provisioning step (`quarto-dev/quarto-actions/setup`, pinned to 1.10.18) gated on a path filter for `packs/binder-publishing/**` | same workflow |
| Add the V4 platform matrix — macOS, Linux with an externally-managed interpreter, Windows | a separate job; it needs no Quarto |

**Cost, stated rather than discovered:** Quarto provisioning is a ~236 MB download
per job, so the render gates (V1, V2, V2b, V3, V5) run **on a path filter**, not on every PR. Unit tests — which
are the bulk of the suite and need no renderer — run always. V4 runs on the path
filter too, since an install-command regression only matters when the pack
changes.

### The portability acceptance test — the most important one

1. Create a clean temp directory. **No Git, no `pack.toml`, no `site.toml`, no
   agent-ready-repo files, no docs site.**
2. Write four ordinary Markdown files, one containing a portable ` ```mermaid `
   fence, plus a `binder.toml` referencing them by explicit path.
3. Expose the pack from a read-only copy of its projected form.
4. `resolve` → assert `binder-index.json` exists and matches a golden file byte
   for byte.
5. `build` → assert `index.html`, per-chapter HTML, a search index, and an SVG
   Mermaid diagram exist.
6. **Assert every source file's SHA-256 is unchanged.**
7. **Assert the pack directory tree is unchanged** — recursive hash before and
   after.
8. Assert nothing was written outside the temp directory and the toolchain cache.

### The multi-pack fixture

A fixture repository combining: a `desk-research`-shaped `<slug>-survey.md` with
YAML frontmatter; an RFC and an ADR in this repository's **frontmatter-free**
bold-marker style, each with a `.binder.toml` sidecar; an `architect-design`
design doc containing Mermaid; a `new-spec` spec and plan; and two hand-written
Markdown files with no metadata at all. One producing pack ships the recipe
template; the publication pack consumes it **without importing anything from it**.
Level-0, Level-1, and sidecar items resolve in the same run.

### Accessibility smoke checks

Parsed from the rendered HTML: every `<img>` carries an `alt` attribute — **present, possibly empty**, since a source `![](x.png)` gives the compiler nothing to invent and a fabricated description is worse than an explicit null; a missing attribute is a failure, an empty one is recorded in diagnostics; heading levels never skip
**except where a clamped H6 shift was warned, which the check reads from
`renderer-plan.json` — the clamp is transformation step 3, so recording it in the
index would violate invariant 22**; `<html lang>` present; **each Mermaid SVG has an
accessible name** — satisfiable by construction because the compiler emits a
fallback name from the node label and diagram ordinal when no caption exists; skip-link present; focus-visible
styling present in the theme CSS. Not a full audit — a regression net for the
theme.

### Activation evals

`evals/eval_queries.json` covers positive triggers ("publish these documents as a
binder", "build the architecture review packet", "compile these into one
navigable document") and near-miss negatives that must **not** trigger — "convert
this Markdown to HTML" (→ `markdown-to-html`), "render this for review" (→
`render-proof`), "render these Mermaid diagrams to PNG" (→ `mermaid-renderer`),
"write a design doc" (→ `architect-design`). The negatives matter more than the
positives, because three neighbouring skills already exist in `converters`.

---

## Phased rollout

**Phase 0 — the architectural seam. No renderer.**
Schema v1 + JSON Schema files (in the skill's `assets/`; **not** mirrored to `contracts/` — see *Canonical schema publication*) ·
validator including the unknown-field and not-yet-implemented classes ·
**the trust scanner's core floor *and the Quarto rule table*** — both belong here,
not in Phase 1: D34 makes the rule set declarative so registering Quarto's rules
needs no adapter, and Phase 0 ships `resolve` and `inventory`, which read source
bodies. Shipping the floor alone would let a Phase-0 `resolve` of a
`renderer = "quarto"` recipe admit content Phase 1 then rejects · Level-0
resolver (explicit paths, sections, parts, weight, before/after, exclusions,
dedup) · `binder-index.json` v1 · `check`, `resolve`, `explain`, `inventory` ·
configuration precedence and the trust lattice · path confinement · unit tests.

*Ships nothing a user can read — and establishes every contract that is expensive
to change later.* Independently valuable: the index is consumable by anyone who
wants to write a renderer.

**Phase 1 — v1 completes. First readable binder.**
The remaining gates (V2, V2b, V4-other-platforms, V5, V6) · Quarto staging adapter · the strict-profile scanner · Mermaid
normalization and constraints · theme and brand assets · cover, part pages, source
inventory, provenance · link rewriting and asset copying · diagnostics mapping ·
`build`, `clean`, `install-quarto`, `check --published` · the dependency ladder ·
three locks, concurrency, near-atomic publication · **the clean-directory
portability fixture and the multi-pack fixture** · activation evals · guides.

**Phase 0 + Phase 1 = v1.**

**Phase 2 — metadata and refinement.** Frontmatter and sidecar ingestion ·
**`sidecar init`** · `select` queries · status maps · `pick = "one"`
disambiguation · richer conflict presentation · **Mermaid captions and
`fence-sha256` binding** · **`--if-stale`**.

**Phase 3 — composition.** Overlays and `extends` · child binders ·
`pick = "latest"` · producer conventions (`[pack.metadata.binder]`) · the named
`binder-editor` subagent if measurement justifies it · profile libraries.

**Phase 4 — more consumers.** A second renderer · site mounting or index
consumption · PDF/Typst.

### Decisions required before implementation

Charter fit, domain fit, and pack placement (U1, U2, U3) · the Tier-2 policy
amendment (U5) · **`binders/` and `.binder-work/` as new top-level directories in
this repository, which `AGENTS.md` § *Check before acting* requires be proposed
via RFC** · pack
and skill names · the `binder.toml` schema and its version-1 surface · the index
schema and its stability guarantee · identity rules · the trust lattice and its CI
mechanism · the security control set and which are mechanical · Quarto version
range and the install ladder ordering · configuration precedence · workspace and
publication layout · the three-lock concurrency model · exit codes · the outcome
of the remaining gates V2, V2b, V4-on-other-platforms, V5, and V6.

### Safe as extension points

Additional renderers · additional output formats · selector expressiveness ·
overlay semantics beyond exclusion and addition · child binders · artifact-kind
and status vocabularies · producer declarations · site integration depth · theme
customization surface.

---

## Unresolved questions

**U1 — Charter Principle 3: is this a habit or a tool?** *"A habit, not a tool.
Captures a way of working, not a piece of infrastructure."* The habit case:
publishing a dossier for a decision forum is a recurring SDLC act, and the
compiler stands to that habit as `work-loop`'s scripts stand to the work loop. The
tool case: a document compiler with two schemas, a resolver, and a renderer
adapter is infrastructure by any ordinary reading, and this catalogue has declined
additions on exactly this ground before. Principles 1, 2, and 4 are assessed in
*Pack placement and charter fit* and clear. **This one is the RFC's decision, and
it is a stop-or-go rather than a reshape.**

**U2 — does the pack sit inside the Charter's Domain?** Distinct from U1 and
decided on different evidence. `docs/CHARTER.md` § Domain is the *"machine-readable
scope anchor"* — "software engineering / SDLC… code quality, architecture,
testing, CI/CD, project governance, and engineering process", explicitly excluding
personal productivity and PKM. **Recommendation: in scope.** Every binder this
design targets is an SDLC governance artifact bundle — architecture review,
release readiness, incident review, implementation handoff — and none of the
excluded categories is served. The reason to name it separately is that a generic
"compile Markdown into a publication" framing would read as PKM, and the pack must
be positioned against project governance to stay inside the anchor. If reviewers
read it the other way, that decides U1 without needing the Principle-3 argument.

**U3 — new pack versus a ninth `converters` skill.** Argued in *Pack placement*;
the fallback costs nothing but the pack boundary. Named separately from U1 because
a "yes" to U1 and a "no" to U3 is a coherent outcome.
**Recommendation: new pack.**

**U4 — pack name.** `binder-publishing` versus `publishing` versus `binder`.
**Recommendation: `binder-publishing`** — `publishing` is too broad for a
catalogue that may later publish other things, and `binder` names the noun rather
than the capability. The skill name `publish-binder` follows the verb-noun
convention and is not in the banned label set.

**U5 — the Tier-2 policy amendment for rung 2.** Rung 1 (`pip`) is already
sanctioned by `author-a-skill.md` § *What counts as a dependency*, so the ordinary
case is not blocked. **But the consequence of refusal is larger than an earlier
draft claimed.** PEP 668 externally-managed interpreters — Debian/Ubuntu system
Python, Homebrew Python — refuse `pip install --user`, and rung 2 is the only
remaining *in-pack* route for that population. If the amendment is refused, those
users have no in-pack install path and must use the official installer or build a
virtualenv themselves.

That makes U5 **a blocking dependency for a named platform segment**, not a
nice-to-have. **Recommendation: seek it**, and if refused, say so in the pack's
prerequisites rather than letting a Debian user discover it at first run.

**U6 (gate V1) — Mermaid under execution-off.** Empirically gated; fallback named.

**U7 (gate V2) — render-time network access.** Empirically gated.

**U8 (gate V3) — fenced divs under `-raw_attribute`.** Empirically gated; cosmetic
fallback.

**U9 — default publication directory.** `build/binders` collides with the generic
`build/` gitignore in many repositories, which is convenient (ignored by default)
and confusing (mixed with compiler output). **Recommendation: keep
`build/binders`** — being ignored by default is the property that matters most for
a directory regenerated on every build; `docs/binders/` invites accidental commits
of rendered HTML. Low-stakes, but hard to change once adopters have it.

**U10 — should `binder.toml` at the content root be special?** The design treats
it as a conventional default for `build` with no argument.
**Recommendation: keep it** — the two-file quick start is what makes the clean-
directory case a two-minute demonstration, and the alternative buys explicitness
nobody asked for.

**U11 — guides drift on `.apm/shared-libs/`.** `skill-script-conventions.md` and
`author-a-skill.md` contradict each other. Out of scope; flagged for a separate
fix. If it resolves the *other* way, the two-skill shape becomes viable and this
pack shape should be revisited.

**U12 — `[pack.layout]` schema versus installer behaviour, and a data-loss half.**
The schema accepts `output_dir`; `_append_layout_section` reads only `parent`, so
five shipped packs declare `output_dir` and get a silent no-op. **Worse than a
no-op:** when the appender *does* fire — the moment any pack declares
`[pack.layout.<scope>].parent` — it re-emits `agentbundle-layout.toml` preserving
only `parent` per section and dropping every off-schema key, which would silently
delete an adopter's hand-written `[binder] output_dir / workspace_dir /
recipes_dir` block. Pre-existing and out of scope to fix here, but it bears
directly on this design: either binder paths move to `binder-policy.toml` or a
dedicated file, or the pack's guide must tell adopters to re-add `[binder]` after
such an upgrade. **Recommendation: raise it with the RFC** rather than design
around a bug.

---
