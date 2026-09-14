# Index patterns over a large document corpus

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-12 to ground ADR-0109: how leading spec-driven-development
frameworks, ADR/RFC tooling, and large docs-as-code repositories handle an index
over a large document corpus — generated or hand-maintained — and what shape an
index over 400+ documents must take to stay usable. Independent desk research;
every finding is cited and carries a confidence rating. Retained so decisions and
specs can cite it rather than restate it.

The decision it grounds: this repository hand-maintains three index tables
(`docs/specs/README.md`, `docs/rfc/README.md`, `docs/adr/README.md`). The spec
index is 233 KB, covers 230 of 444 spec directories, and was touched 115 times
in 30 days.

---

## Findings

### F1. No file-based SDD framework maintains a spec index at all `[high]`

Five independently-owned frameworks were checked. None ships a roster, registry,
or index file over its spec corpus.

| Framework | Owner | Index file | Discovery mechanism instead |
| --- | --- | --- | --- |
| Spec Kit | GitHub | none | filesystem scan; `NNN-` prefix sort |
| Kiro | AWS | none | `.kiro/specs/*/` glob |
| BMAD-METHOD | BMad community | none (`docs/index.md` is a nav hub) | `EPIC.STORY` filename sort |
| agent-os | Builder Methods | none for specs | dated folder slug |
| OpenSpec | Fission-AI | none | directory traversal, load-on-demand |

Spec Kit's `.specify/feature.json` is a *single-active-feature pointer*, not a
roster. agent-os is the sharpest evidence: it has a generated `index.yml` — for
`standards/`, produced by an `/index-standards` command — and deliberately does
not extend it to specs. There is no `/index-specs`.

Tessl is the sole exception and proves the rule differently: it externalises the
index to a hosted registry with per-spec eval scores, i.e. a package manager, not
a file.

*Independence:* five distinct vendors (GitHub, AWS, BMad, Builder Methods,
Fission-AI). Verified by direct repo/doc reads, including a directory listing of
OpenSpec's 43 spec folders showing no index file.

*Caveat:* absence of an index may reflect the youth of these frameworks rather
than a considered choice. None documents guidance for a corpus past a few dozen
specs — that silence is itself a gap, not an endorsement.

### F2. Long-running proposal processes generate their index; the hand-maintained ones show documented strain `[high]`

| Process | Corpus | Index | Generated? |
| --- | ---: | --- | --- |
| Python PEPs | ~1,000 | PEP 0 | yes — `pep_sphinx_extensions` from RFC-2822 headers |
| Kubernetes KEPs | ~1,000 | keps.k8s.io | yes — from per-KEP `kep.yaml` |
| IETF RFCs | ~9,000 | `rfc-index.xml` + Datatracker | yes — from the RFC Editor database |
| Rust RFCs | ~3,500 | RFC Book `SUMMARY.md` | yes — `generate-book.py`, filenames only |
| TC39 proposals | ~400 | README + per-stage files | **no** — hand-edited |
| Ember RFCs | ~900 | frontmatter; dashboard aspirational | partial; tracker abandoned 2022 |

The two hand-maintained cases carry the documented friction. TC39 has open issues
about volume (Stage 1 excluded from the README because there are too many; a
request to re-sort by most-recently-discussed). Ember's RFC 0617 was motivated by
the status transition being "completely opaque," and the `emberjs/rfc-tracking`
repo built to fix it was archived unmaintained in 2022.

*Independence:* six separate foundations/orgs.

### F3. The generated indexes that work are grouped and faceted, never flat `[high]`

**PEP 0 is the strongest positive prior art for a 400+ corpus.** It is not one
table. It is nine status-grouped tables — Process/Meta, Informational,
Provisional, Accepted, Open, Finished, Historical, Deferred, and
Rejected/Superseded/Withdrawn — *plus* a separate numerical index *plus* an index
by `Topic` (Governance, Packaging, Release, Typing). Three views over one corpus,
all generated from headers in each PEP.

Kubernetes KEPs facet on SIG, stage (alpha/beta/stable) and release milestone.
TC39, despite being hand-maintained, split into per-stage files for the same
reason.

### F4. Generation alone does not produce usability — Rust is the counterexample `[moderate]`

Rust's RFC book **is** generated, by `generate-book.py`. But it generates a *flat
list from filenames only*, parsing no metadata. It is also the process with the
most documented discoverability complaints: a 2014 internals thread stating RFCs
are "not easily searchable and indexable," a follow-on 2017 thread, and a
third-party categorised index (nrc's) built as a workaround because the official
one lacks topic tagging.

This is the load-bearing finding for the question as posed. Auto-generating a
flat table over 444 rows reproduces the Rust outcome, not the PEP 0 outcome. The
variable that matters is **grouping and metadata**, not generated-vs-hand.

*Downgraded to `[moderate]`:* the complaints are real and primary, but no one
states the causal claim "because it is flat" — that step is inference.

### F5. ADR index generation is near-universal and deliberately shallow `[high]`

Of 13 ADR tools surveyed, 10 generate an index. The committed-markdown generators
emit strikingly little:

- `adr-tools` (`adr generate toc`) → a bullet list of number + title + link. No
  status, no date.
- `adr-log` → same, with an `ADR-NNNN` identifier prefix.

**Status almost never appears in a generated markdown index.** It appears only in
the rendered tools — log4brains (status badge + search), Backstage (status chip +
cross-repo search), Structurizr (decision log + relationship graph), adr-viewer
(colour-coded status). Superseded ADRs are listed in all of them, marked, never
hidden.

MADR prescribes no index at all; its own site uses a Just the Docs theme sidebar.
Its scale guidance is subdirectories by domain, accepting non-unique numbering.
JabRef at 74 ADRs likewise uses theme-generated navigation rather than a table.

*Implication:* the ambitious `| # | Title | Status |` markdown table is *above*
the industry norm for a committed ADR index, not below it.

### F6. The shared-index merge conflict has a canonical solution, invented four times `[high]`

One file per change in a staging directory, assembled at build/release time.
Four independent tools state the merge-conflict motivation explicitly:

- **towncrier** — "rather than … having one single file which developers all
  write to and produce merge conflicts, towncrier reads 'news fragments.'"
- **scriv** — the pitch is literally "avoid merge conflicts on your CHANGELOG."
- **reno** (OpenStack) — "stores each release note in a separate file to enable a
  large number of developers to work on multiple patches simultaneously … without
  worrying about merge conflicts."
- **changesets** (JS) — same pattern, driven by the same complaint.

*Independence:* four ecosystems (Python ×2 but different authors, OpenStack, JS).

The `.gitattributes` `merge=union` alternative works only for append-only,
one-record-per-line, order-independent files. It silently corrupts structured
content — a mutated record plus an adjacent append yields *both* versions, with
no error. Git's own docs warn the result needs manual verification. GitHub and
GitLab do not honour it in web merges.

### F7. Committing a generated index keeps the conflict and removes the fix `[moderate]`

If the generated file stays in git, every branch touching an indexed document
still conflicts on it — but now no one can meaningfully hand-resolve it. The
standard mitigation is a `--check` mode run in CI (regenerate, fail if `git
status` is dirty), which is widely practised. Its own failure mode: the check
must pin the generator's version, or a floating version fails CI on a correct
index.

### F8. Large always-loaded index files carry a measured agent cost `[moderate]`

- A 331 KB `AGENTS.md` (~83K tokens) consumed 81% of a 128K context window and
  put the session into a compaction loop that never progressed. Filed as a bug.
- Codex CLI silently truncates `AGENTS.md` over 32 KiB.
- Controlled study (ETH Zurich / LogicStar.ai): *uncurated auto-generated*
  context reduced task success in five of eight settings, cost 2.45–3.92 extra
  steps per task and 20–23% more spend. Human-curated context gained ~4 points;
  auto-generated lost 3%.

*Downgraded to `[moderate]`:* this research measures *instruction* files, not
navigation indexes. The transfer is an inference — though a 233 KB index file is
well past every threshold named above.

### F9. Comprehensive is not the goal; curated-and-partial may beat it `[low]`

The same study found that *even good* human-curated context files "increased
costs by up to 19% and added more steps to every task." The recommended posture
is start empty, add only what addresses an observed repeated failure; one
experiment improved performance 2.7% by *deleting* documentation.

The two-layer idea — a generated complete listing plus a small curated entry
point — is independently described in the agent-context and docs-tooling
literatures, but **no named repository was found doing it as a documented
architectural choice.** MkDocs' `nav:` is an accidental instance: the filesystem
is the complete listing, `nav:` is the curated view, and pages missing from `nav:`
silently vanish from navigation.

*Rated `[low]`:* the principle is coherent and doubly-sourced; the concrete
practice is unattested.

### F10. No IA source recommends a flat index over hundreds of items `[moderate]`

Material for MkDocs explicitly recommends **navigation pruning** for "100+ or even
1,000+ page" sites, claiming a 33%+ reduction in built-site size. Diátaxis,
Write the Docs, and progressive-disclosure guidance all route to grouping,
category landing pages, and secondary navigation levels. Hugo taxonomies and the
Material tags plugin auto-generate per-tag index pages — the faceting that
PEP 0's Topic index does by hand-rolled equivalent.

*Folklore flag:* the "7±2 nav items" rule cited throughout docs-IA writing is
not evidenced for navigation. Miller studied recall, not recognition; he called
the number "only a pernicious, Pythagorean coincidence." The transferable part of
his work is **chunking** — grouping — which does apply.

*Downgraded to `[moderate]`:* all of this is practitioner grey literature. No
peer-reviewed study of flat-vs-hierarchical index usability was found.

### F11. Hand-maintained indexes decay, but the rate is unmeasured `[moderate]`

Decay is well-attested in real repo issues — stale hard-coded counts in a README,
generated test READMEs drifting "with nothing noticing," a runbooks directory with
no index forcing on-call staff to read every file's H1 during incidents. The
mechanism is always the same: nothing fails, so decay is silent.

No published drift-rate measurement exists for code-indexed files. The nearest
proxy is link rot (~11%/year, ~50% at seven years), which measures a different
thing.

*Survivorship bias, explicitly:* stale indexes nobody notices are never filed as
issues. Only caught drift is published, so the literature systematically
understates the problem.

### F12. The inverse failure is real too `[moderate]`

A missing index is also a documented failure (the runbooks case). The choice is
not "good index vs no index" — it is between several failure modes: stale index,
flat-but-fresh index, no index, and context-tax index.

---

## What this means for a 444-spec corpus

`[synthesis]` — Four constraints fall out of the findings, in priority order:

1. **Do not generate a flat 444-row table.** F4 is the direct warning; F10 and F8
   are the corroboration. Generation fixes staleness and leaves unusability
   untouched.
2. **Group by lifecycle status.** F3. PEP 0's nine sections are the pattern, and
   this repo's own seed already specifies the two-table version of it ("Once a
   feature is shipped, move its row here") — a design chosen and then not
   followed. With 434 Shipped / 4 Draft / 6 Archived, a status-grouped index
   makes the *active* set a handful of rows.
3. **Put per-document prose in per-document files.** F6. Four tools converged on
   this for exactly the write-contention problem here (115 touches/30 days on one
   file). A sibling file per spec, assembled at build, removes the conflict
   without losing the prose.
4. **Keep the curated entry point small and separate from the complete listing.**
   F9, F8. The complete listing is for lookup; the curated view is what gets read.

The ADR and RFC tables are a different case: fully derivable, already
complete-or-near, and already richer than the ADR-tooling norm (F5). They are
straightforward generation targets with no content decision attached.

---

## Known unknowns

- **Known-unknown:** the drift rate of hand-maintained code-adjacent indexes.
  Would be closed by: a longitudinal study, or an in-repo measurement of how long
  a row stays stale here (this repo's own git history could answer it — five
  stale spec statuses and one stale ADR status are already observable).
- **Known-unknown:** whether any repository deliberately runs the two-layer
  pattern (generated complete listing + curated entry point). Would be closed by:
  a targeted search of large docs monorepos, which this survey did not exhaust.
- **Known-unknown:** what PEP 0's generator costs to maintain. Would be closed by:
  reading `pep_sphinx_extensions` issue history for maintenance burden.
- **Unknowable:** whether the five SDD frameworks omit a spec index by considered
  choice or because none has yet run a 400-spec corpus. None has published a
  rationale, and the counterfactual — what they would do at scale — has not
  happened yet.
- **Unknowable from this survey:** whether agents in *this* repository actually
  read the spec index. The context-cost research (F8) measures instruction files
  on other codebases; only local instrumentation could answer it here.

---

## Source independence note

Where several sources shared a vendor or author they were counted once. Tessl's
commentary on Spec Kit is vendor-on-competitor and was treated as secondary. The
Upsun post and the ETH Zurich / LogicStar.ai study it cites count as one source,
not two — the study is the primary. towncrier and scriv are both Python-ecosystem
but separately authored, and were counted separately.
