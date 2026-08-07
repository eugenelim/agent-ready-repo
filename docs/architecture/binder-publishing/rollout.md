# Rollout, testing, and open questions

> Phases, test strategy, CI wiring, unresolved decisions.
> Part of [binder publishing architecture](README.md).

## Testing and eval strategy

Tests live at `packs/binder-publishing/tests/skills/publish-binder/`, outside the
`.apm/` runtime boundary. Evals live at `.apm/skills/publish-binder/evals/`.

### Unit

Schema parsing · `schema-version` behaviour · unknown-field error and
`--allow-unknown-fields` · **`[policy] profile` and `[policy] shortcodes` are
unknown fields (exit 4), not deprecated keys** · **not-yet-implemented key class,
per phase** · `[x-vendor]` passthrough · content-root resolution in all four
branches · **content-root refusal list — home, filesystem root, an ancestor of
`~/.agentbundle/` or of the pack itself, each exit 6** · **every node read is
extension-checked, explicit `path` included** · configuration precedence ·
identity normalization and case collision ·
status-map normalization and unknown status · stable ordering · weight sorting ·
`before`/`after` topological order · **cross-section constraint is exit 4** ·
cycle detection · ambiguity · missing required vs optional · duplicate handling ·
supersession · exclusion beating inclusion · excluded-required erroring ·
**duplicate `id` and colliding publication dir** · child-binder cycle detection ·
frontmatter discard-and-rebuild · **executable-cell fence neutralization, with a
` ```mermaid ` fence asserted byte-identical to its source** · Mermaid
directive/click/callback rejection and the `<br>`/`<|--`/`<-->` label allowlist ·
link rewriting to staged `.md` filenames · **`line-offset` accuracy, property-tested
against randomly generated sources, including the CRLF and BOM cases** ·
staged-name determinism and hash disambiguation · **`emitted-ordinal` numbering,
including that an unnumbered chapter emits `null` and that the ordinal appears as
a `data-ordinal` attribute and never inside a title string or the search index** · path traversal · absolute
paths · symlink escape · asset allowlist · resource ceilings · self-path write
refusal · **argv construction — a list, never a shell string, `-f` the only path
element, `--strict` always present** · **environment allowlist construction —
assert a planted `AWS_SECRET_ACCESS_KEY` is absent from the child env** · **TOML
injection — a recipe `title` containing `"` and a newline is rejected at
validation, and with the validator stubbed out the emitter still yields a
`zensical.toml` whose parsed form has no injected sibling key** · **renderer-
interpretable syntax in an emitted string — a recipe `title` of `"{{< env HOME >}}"`
is exit 4, the same as a source H1 is exit 6 with fallback to the file stem** ·
**label resolution across all four rules, including a source H1 carrying a control
character falling through to the file stem** · **parameter substitution confined
to the closed key list, single-pass, erroring on an unresolved `${name}`** ·
**publication-ownership check — a foreign directory is exit 4 and is not renamed**
· **`publication-dir` absolute or `..`-escaping is exit 6** · **heading shift
clamps at H6 and warns** · **scan exclusions warned,
`scan-exclusions-override` re-admits** · **invariant 22 — a golden index from
`resolve` is byte-identical to the index after `build`** · **the index carries no
`profile` key** · **cross-device publication detected at validation** ·
**version probe — `importlib.metadata.version` is used and a stubbed
`zensical.__version__` is never read (Z1c)** · exit-code mapping including 9 and 130.

**Deleted from this list, and worth naming rather than silently shortening:** the
trust-lattice suite (recipe cannot grant, repo policy cannot grant,
`--profile trusted` exits 6, grant matching resists a planted symlink), the
`--quarto`-beneath-the-content-root test, the shortcode
reject/escape/idempotence tests, the `--out` confinement test, and the
`_quarto.yml` two-profile golden files. Each tested a mechanism D-A or D-B
removed. **A test suite that outlives its mechanism is how a design keeps paying
for a decision it already reversed.**

### Integration

**Gates Z1–Z4 against the single shared fixture** (all required in CI as
regression assertions) · **Z4's zero-remote-*subresource* assertion over the built
tree — no `src=`, stylesheet or preconnect `href=`, `@import`, or off-host `url()`;
NOT a zero-`https://` string match, which Z4d showed unsatisfiable** · renderer
detection present/absent/wrong-version, **including that the probe is
`importlib.metadata.version`** · generated `zensical.toml` against a golden file
(**one file — there is no second profile to differ from**) · successful HTML render
· parts render as nested nav groups · search index generated and local · prev/next
present · **Mermaid renders from an untransformed portable fence, and the vendored
`mermaid.min.js` is referenced from `<head>` ahead of the theme bundle** · invalid
Mermaid mapped to the source line through `line-offset`, **with ANSI stripped
first (Z1f)** · **a `nav` entry with no staged file is exit 7 before the renderer
is invoked (Z2g)** · **a `--strict` build reporting issues is exit 7, and a build
without `--strict` is never trusted to have succeeded (Z1b)** · idempotent rebuild
produces a byte-identical index · `check --published` returns 0 fresh / 9 stale /
10 on a pack-version change · interrupted build leaves no corrupt state · **two
concurrent different binders both succeed** · two concurrent identical builds
serialize on the workspace lock · **two different recipes targeting the same
publication dir are rejected at validation, and the publication lock serializes
the case that slips through** · near-atomic publication replacement, **including
the cross-device copy path** · **`binder-stamp.json` present in the published tree
while `binder-index.json` is absent from it, the stamp carrying no `diagnostics`
key, and `check --published` returning 9 after a source edit** · **nothing is
written outside `stage/`, the publication, and its three named siblings — asserted
by a recursive hash of the content root before and after, which is what catches
`site/` or `.cache/` landing somewhere unexpected** · `clean` confinement.

Renderer-dependent tests skip with a clear reason when `zensical` is absent and
are **required** in CI, where the pipeline installs it.

### CI provisioning — the wiring this needs, named

This repository wires pack tests by **explicit enumeration** —
`.github/workflows/catalogue-tooling-ci-gates.yml` runs
`python -m pytest packs/core/tests/ packs/product-documentation/tests/ -q` — so a
new pack's tests do not run until someone adds them. "Required in CI" is a change
to a file, not a property that arrives by itself:

| Change | Where |
|---|---|
| Add `packs/binder-publishing/tests/` to the pytest invocation | `catalogue-tooling-ci-gates.yml` |
| Add `python -m pip install zensical==0.0.53` as an ordinary step | same workflow |

**Two rows, where the previous version had three and an argument.** Quarto
provisioning was a ~236 MB download per job, which forced the render gates behind
a path filter, split the suite into "runs always" and "runs when the pack
changes", and needed a separate V4 platform-matrix job to prove an install command
worked verbatim on three operating systems.

**All of that is gone.** A 12.2 MB wheel with 12 platform wheels — including
Windows, musl, and armv7 — is an ordinary pipeline dependency. The Z-gates run on
**every PR**, alongside the unit tests, because there is no longer a cost worth
optimising against. The path filter was never a good property; it meant the render
gates did not run when a *shared* change broke them, and it existed only because
the renderer was expensive.

### The portability acceptance test — the most important one

1. Create a clean temp directory. **No Git, no `pack.toml`, no `site.toml`, no
   agent-ready-repo files, no docs site.**
2. Write four ordinary Markdown files, one containing a portable ` ```mermaid `
   fence, plus a `binder.toml` referencing them by explicit path.
3. Expose the pack from a read-only copy of its projected form.
4. `resolve` → assert `binder-index.json` exists and matches a golden file byte
   for byte.
5. `build` → assert `index.html`, per-chapter HTML, a local `search.json`, and a
   `<pre class="mermaid">` block whose content is byte-identical to the source
   fence all exist.
6. **Assert every source file's SHA-256 is unchanged.**
7. **Assert the pack directory tree is unchanged** — recursive hash before and
   after.
8. **Assert nothing was written outside the temp directory at all.** The previous
   version said "outside the temp directory *and the toolchain cache*"; D-B
   deleted the cache, so the assertion is now unqualified — which is a strictly
   stronger test and a better headline for the acceptance case.
9. **Assert the built tree makes no remote subresource request** — the Z4
   assertion, run here too, because an air-gapped adopter is exactly the person
   the clean-directory case is for.

### The multi-pack fixture

A fixture repository combining: a `desk-research`-shaped `<slug>-survey.md` with
YAML frontmatter; an RFC and an ADR in this repository's **frontmatter-free**
bold-marker style, each with a `.binder.toml` sidecar; an `architect-design`
design doc containing Mermaid; a `new-spec` spec and plan; and two hand-written
Markdown files with no metadata at all. A producing pack **writes** a recipe
template into the fixture's `recipes_dir`, and `binder build` resolves it as an
ordinary recipe — **importing nothing from it and reading nothing inside its skill
directory**, which is the seam as redesigned in
[`outline-and-templates.md`](outline-and-templates.md). Level-0, Level-1, and
sidecar items resolve in the same run.

**One assertion is added and it is the point of the fixture:** that
`binder.py` opens no path beneath any other skill's directory during the whole
run. Without it, the self-containment property is a claim the fixture illustrates
rather than tests — and the previous seam is proof that the claim can drift.

### Accessibility smoke checks

Parsed from the rendered HTML: every `<img>` carries an `alt` attribute — **present, possibly empty**, since a source `![](x.png)` gives the compiler nothing to invent and a fabricated description is worse than an explicit null; a missing attribute is a failure, an empty one is recorded in diagnostics; heading levels never skip
**except where a clamped H6 shift was warned, which the check reads from
`renderer-plan.json` — the clamp is transformation step 3, so recording it in the
index would violate invariant 22**; `<html lang>` present; skip-link present;
focus-visible styling present in the theme CSS. Not a full audit — a regression
net for the theme.

**The Mermaid accessible-name check moves out of the HTML parse, because there is
no SVG to parse.** Quarto rendered diagrams server-side into the output; Zensical
emits `<pre class="mermaid"><code>…` and the vendored bundle renders it in the
reader's browser (Z3a, Z3c). A static check over the built tree therefore cannot
see an `<svg>` at all, and a check asserting one would have failed on every build
— or worse, been quietly deleted.

Two checks replace it, and between them they cover the same concern honestly:

- **Static:** every `<pre class="mermaid">` block carries an accessible name in
  its `attr_list` attributes, emitted by the compiler from the node label and
  diagram ordinal. This is assertable over the built HTML and is the part the
  compiler actually controls.
- **Z6, not yet run:** that the rendered SVG carries the name through. This needs
  a headless browser, which the design does not otherwise require, so it is a
  gate rather than a smoke check.

The graceful-degradation property is worth stating because it is unusually good
here: if the vendored bundle fails to load, the reader sees the diagram's own
Mermaid source as preformatted text rather than a blank space.

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
**the trust scanner's core floor *and the Zensical rule table*** — both belong
here, not in Phase 1: D34 makes the rule set declarative so registering a
renderer's rules needs no adapter, and Phase 0 ships `resolve` and `inventory`,
which read source bodies. Shipping the floor alone would let a Phase-0 `resolve`
admit content Phase 1 then rejects · Level-0 resolver (explicit paths, sections,
parts, weight, before/after, exclusions, dedup) · `binder-index.json` v1 ·
`outline`, `templates`, `check`, `resolve`, `explain`, `inventory` ·
configuration precedence · path confinement and the content-root refusal list ·
unit tests.

*Ships nothing a user can read — and establishes every contract that is expensive
to change later.* Independently valuable: the index is consumable by anyone who
wants to write a renderer.

**The Zensical rule table is three rows**, against Quarto's much longer one: the
`%%{init:}%%` directive, `click … callback`/`call`, and the Mermaid node-label
allowlist. Everything the Quarto table carried about shortcodes and raw pandoc
blocks has no subject here.

**Phase 1 — v1 completes. First readable binder.**
The remaining gates (**Z5, Z6**, and the renderer-independent **V6**) · Zensical
staging adapter · the strict scanner · Mermaid constraints and the vendored
bundle · theme assets and the offline hardening · compiler-emitted numbering ·
cover, part pages, source inventory, provenance · link rewriting and asset
copying · diagnostics mapping · `build`, `recipe write`, `clean`,
`check --published` · **two** locks, concurrency, near-atomic publication ·
**the clean-directory portability fixture and the multi-pack fixture** ·
activation evals · guides.

**Phase 0 + Phase 1 = v1.**

Z1–Z4 are already run, so Phase 1 opens with its renderer questions settled rather
than gated — which is the difference between the two decisions being made and
being merely written down.

**Phase 2 — metadata and refinement.** Frontmatter and sidecar ingestion ·
**`sidecar init`** · `select` queries · status maps · `pick = "one"`
disambiguation · richer conflict presentation · **Mermaid captions and
`fence-sha256` binding** · **`--if-stale`**.

**Phase 3 — composition.** Overlays and `extends` · child binders ·
`pick = "latest"` · producer conventions (`[pack.metadata.binder]`) · the named
`binder-editor` subagent if measurement justifies it · recipe-template libraries.

**Phase 4 — more consumers.** A second renderer · site mounting or index
consumption · PDF/Typst.

### Decisions required before implementation

**U1 is resolved (D45), so nothing on this list is a stop-or-go.** Everything
below is a shaping decision for the RFC.

Domain fit and pack placement (U2, U3) · **`binders/` and
`.binder-work/` as new top-level directories in this repository, which
`AGENTS.md` § *Check before acting* requires be proposed via RFC** · **taking a
runtime dependency on an alpha-versioned package (`zensical==0.0.53`), which
`AGENTS.md` § *Check before acting* requires be recorded in the pack's `AGENTS.md`
or an ADR before it is added** · pack and skill names · the `binder.toml` schema
and its version-1 surface · the index schema and its stability guarantee ·
identity rules · the security control set and which are mechanical · the renderer
pin and its upgrade procedure · configuration precedence · workspace and
publication layout · the two-lock concurrency model · exit codes · the outcome of
Z5, Z6, and V6.

**Three items left this list, and one joined it.** The Tier-2 policy amendment
(U5), the Quarto version range, and the install-ladder ordering all went with D-B.
The alpha-dependency record is new: `zensical` at `0.0.53` is a dependency the
repository's own rules say must be argued for before it is added, and burying that
in a rollout list would be exactly the omission those rules exist to prevent.

### Safe as extension points

Additional renderers · additional output formats · selector expressiveness ·
overlay semantics beyond exclusion and addition · child binders · artifact-kind
and status vocabularies · producer declarations · site integration depth · theme
customization surface.

---

## Unresolved questions

**U1 — RESOLVED (D45): the pack clears Charter Principle 3.** Its *subject* is a
habit — assembling a decision dossier for a review forum; the machinery makes that
habit reproducible and reviewable. The reasoning, including the counter-reading
that was weighed and the accelerator-pack carve-out that does **not** apply, is in
[`overview.md`](overview.md#principle-3-resolved).

Note that D-A and D-B did not decide this. They make the pack materially smaller,
but "smaller infrastructure" is still infrastructure and Principle 3 is about
*kind*, not size. The decision turns on which one the pack is *about*.

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
read it the other way, D45's Principle-3 argument does not save the placement —
a pack outside the Domain anchor fails regardless of which principle it clears.

**U3 — new pack versus a ninth `converters` skill.** Argued in *Pack placement*;
the fallback costs nothing but the pack boundary. Named separately from U1 because
a "yes" to U1 and a "no" to U3 is a coherent outcome.
**Recommendation: new pack.**

**U4 — pack name.** `binder-publishing` versus `publishing` versus `binder`.
**Recommendation: `binder-publishing`** — `publishing` is too broad for a
catalogue that may later publish other things, and `binder` names the noun rather
than the capability. The skill name `publish-binder` follows the verb-noun
convention and is not in the banned label set.

**U5 — WITHDRAWN by D-B.** *Was: the Tier-2 policy amendment for the
digest-verified Quarto install.* It asked the catalogue to sanction a pack
fetching and extracting a 236 MB third-party binary, and round 6 escalated it to
"a blocking dependency for a named platform segment" because PEP 668
externally-managed interpreters refuse `pip install --user` and the managed
install was that population's only in-pack route.

**There is no longer anything to amend.** `zensical` is an ordinary pip package
that `author-a-skill.md` § *What counts as a dependency* already sanctions in its
own words. PEP 668 does not bite: a system-Python user creates a virtualenv or
uses `pipx`/`uv`, which is the normal answer for any pip dependency and needs no
policy change. Withdrawn, not deferred — the amendment is not wanted later either.

**U6 — WITHDRAWN by D-B.** *Was: gate V1, Mermaid under execution-off.* A Quarto
question. Zensical executes nothing, and Z3a settles diagram rendering directly.

**U7 — SUPERSEDED by Z5.** *Was: gate V2, render-time network access.* The
question is renderer-independent and still open; it is now tracked as **Z5**
against `zensical build` rather than against `quarto render`.

**U8 — WITHDRAWN by D-B.** *Was: gate V3, fenced divs under `-raw_attribute`.* A
pandoc reader-toggle question with no counterpart here. The badge and editorial-
marker mechanism is `admonition` plus `attr_list`, verified by Z2b, and its
plain-label fallback is retired with the gate.

> **Four questions closed by one decision, and none by argument.** U5–U8 were each
> live enough to need a gate or a policy amendment; all four turned out to be
> questions *about Quarto* rather than about binder publishing. That is the
> clearest measure available of how much of the design was renderer management
> wearing the shape of architecture.

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

**U13 — alpha dependency, newly raised.** `zensical` is
`Development Status :: 3 - Alpha` at `0.0.53`, and the pack would ship a
*published, versioned* binder contract on top of it. Three things bound the risk
and one does not.

Bounded: the dependency surface is narrow (`nav`, theme, `superfences`, search —
not the plugin API); invariant 22 makes swapping renderers a one-file change; and
Z1–Z4 are CI regression assertions, so an upgrade that changes any of the four
behaviours the adapter relies on fails loudly rather than silently.

Not bounded: **the Z-gates found three wrong assertions in one afternoon**, two of
them about behaviour that looked settled (the version attribute, the font key).
That is what an alpha renderer feels like, and it is an argument for the pin being
exact and for the gates being required rather than for the choice being wrong.
**The recording obligation is discharged:
[ADR-0073](../../adr/0073-zensical-as-the-v1-binder-renderer.md) is Accepted and
records the dependency**, per `AGENTS.md` § *Check before acting*. What remains
for the RFC is ratifying the alpha pin itself — and the ADR carries a standing
revisit cadence rather than a one-off condition, because a project shipping three
releases a month is not a decision that stays made.

**U12 — `[pack.layout]` schema versus installer behaviour, and a data-loss half.**
The schema accepts `output_dir`; `_append_layout_section` reads only `parent`, so
five shipped packs declare `output_dir` and get a silent no-op. **Worse than a
no-op:** when the appender *does* fire — the moment any pack declares
`[pack.layout.<scope>].parent` — it re-emits `agentbundle-layout.toml` preserving
only `parent` per section and dropping every off-schema key, which would silently
delete an adopter's hand-written `[binder] output_dir / workspace_dir /
recipes_dir` block. Pre-existing and out of scope to fix here, but it bears
directly on this design: either binder paths move to a
dedicated adopter-owned config file (**not** a policy file — D39 removed that concept), or the pack's guide must tell adopters to re-add `[binder]` after
such an upgrade. **Recommendation: raise it with the RFC** rather than design
around a bug.

---
