# Append-log fragmentation — applied survey

> Discipline: applied (practitioner-pattern survey)

- **Run date:** 2026-09-13
- **Repository evidence observed at:** `cba66a416`. In-repository citations are
  written as relative paths, so they resolve against the working tree rather than
  that revision; where the tree has since moved, the spike below is the current
  measurement.
- **Tested by:** [Changelog fragmentation — feasibility spike](changelog-fragmentation-spike.md).
  It **partially** answers this survey's third known-unknown — it demonstrates a
  canonicalized round-trip and `/now/` projection parity in source order, but not
  byte-identity with the current file (8 lines differ, all of them pre-existing
  separator defects) and not determinism under randomized fragment enumeration.
  It also **corrects one assumption below**: the ordering-schemes section treats
  presentation order as derivable from typed fields for a changelog; measured
  against this repository's own file, the two derivations tested do not reproduce
  it — 98% of entries share a release date, and a date-plus-artifact total order
  moves 82% of them. Read the spike's
  ordering result alongside that section.

## Question

Does one-file-per-entry fragmentation, followed by deterministic assembly, remove the recurring merge-conflict surface of this repository's human-facing changelogs and typed `workspace.toml` registry without losing their ordering and formatting invariants? The survey tests the hypothesis separately for a presentational release document and a structured registry, compares ordering schemes that do not require a shared positional index, and identifies where fragmentation only relocates contention. [synthesis]

Repository grounding is mixed. The current changelog contract makes every released section a top-level, newest-first section immediately below `[Unreleased]`; the heading level is explicitly load-bearing for the `/now/` projection. The package also has a separate `packages/agentbundle/CHANGELOG.md` for package consumers ([repository changelog](../../../docs/product/changelog.md), [conventions](../../../docs/CONVENTIONS.md), [package changelog](../../../packages/agentbundle/CHANGELOG.md)). The root registry says comments, summaries, and *list order* are non-semantic, but its closeout projection nevertheless keys duplicate-valued membership by `(collection, entry_index)`; therefore “position is identity in one reconciliation path” is supported, while “array order carries routing priority” is contradicted by the file's own contract ([workspace contract](../../../workspace.toml), [closeout implementation](../../../packs/core/.apm/skills/workspace-status/scripts/workspace_status.py)). [synthesis]

## Prior-art matrix

| system | fragment unit | ordering mechanism | assembly | fragments deleted? | conflict actually removed |
| --- | --- | --- | --- | --- | --- |
| Towncrier [low] — single-source, vendor-authored | `<issue-or-unique-id>.<type>[.<suffix>]`; random `+…` orphan IDs are supported | configured fragment-type order, then fragment key/issue behavior; templates render the release | `towncrier build` inserts a rendered release at a marker in `NEWS`/`CHANGELOG` | yes by default; `--keep` opts out | removes ordinary PRs' concurrent writes to the monolith; the release commit still edits the monolith and deletes the pending files ([tutorial](https://towncrier.readthedocs.io/en/stable/tutorial.html), [CLI](https://towncrier.readthedocs.io/en/stable/cli.html)) |
| Reno / OpenStack [low] — single-source, vendor-authored | YAML note named `<human-slug>-<random-suffix>.yaml` | notes are discovered by topological traversal of Git history; configured section order shapes the report | Sphinx directive or `reno report`; notes remain first-class inputs | no; notes are durable and version attribution comes from Git history/tags | removes shared release-note-file edits, but couples output to branch topology and tag/branch discovery; the docs call order deterministic but not necessarily predictable or mutable ([usage](https://docs.openstack.org/reno/latest/user/usage.html), [design](https://files.openstack.org/docs/developer/reno/user/design.html)) |
| Changesets (JS) [low] — single-source, vendor-authored | Markdown plus YAML frontmatter in `.changeset/`; default filename is random human-readable words | package and bump metadata determine grouping; multiple bumps flatten to the highest required SemVer bump | `changeset version` updates package versions and changelogs | yes, when versioning | removes concurrent changelog/version-intent edits during feature work; contention moves to the generated release PR and version/package files ([FAQ](https://changesets.dev/faq), [technical decisions](https://changesets.dev/guide/technical-decisions)) |
| Scriv [low] — single-source, vendor-authored | Markdown or reStructuredText file; default name uses creation timestamp, author, and branch | filename begins with time for chronological collection; parser groups configured categories | `scriv collect` parses fragments, normalizes headings, and inserts an entry at a marker | yes by default; `--keep` opts out | removes feature-branch writes to the changelog, while the collect commit still edits it and deletes fragments ([commands](https://scriv.readthedocs.io/en/latest/commands.html), [configuration](https://scriv.readthedocs.io/en/latest/configuration.html)) |
| Changie [low] — single-source, vendor-authored | YAML change in `.changes/unreleased`; filename is configurable and fragment data includes timestamp, component, kind, and custom fields | component config order, then kind config order, then timestamp oldest-first | `changie batch` makes a version file; `changie merge` regenerates the parent changelog with a newline between versions | batch deletes by default; `--keep` opts out; version files remain | removes per-change collision and retains one file per release, but batch/merge still writes a shared version/changelog artifact ([batch](https://changie.dev/cli/changie_batch/), [merge](https://changie.dev/cli/changie_merge/), [configuration](https://changie.dev/config/)) |
| CPython blurb [low] — single-project primary source | reStructuredText at `Misc/NEWS.d/next/<category>/<UTC-datetime>.gh-issue-<n>.<nonce>.rst` | category directory, timestamp, issue ID, and content-derived nonce; hard-coded category order on merge | `blurb release` rolls pending entries into one version file; `blurb merge` renders `Misc/NEWS` | individual pending files are replaced by a per-version file at release | directly targets `Misc/NEWS` conflicts; it also changes blame granularity and its first split/remerge cannot byte-reproduce inconsistent legacy ordering/wrapping ([blurb README](https://github.com/python/blurb), [CPython guide](https://devguide.python.org/contrib/code/pull-request-lifecycle/)) |
| cargo-release [low] — single-source, vendor-authored | none supplied by cargo-release; changelog generation is delegated to a pre-release hook or regex replacement | whatever the invoked generator defines | release pipeline validates, bumps, tags, publishes, and may call a custom changelog generator | not applicable | does not itself remove append-log conflicts; it is an orchestration point, not fragment prior art ([project README](https://github.com/crate-ci/cargo-release)) |
| Debian `debian/changelog` [low] — Debian-authored but monolithic practice | one formal release stanza appended at the top of one required file; more bullets may be added to the current stanza | newest stanza first; package version and explicit stanza position | `dch`/`debchange` edits the file; `dpkg-parsechangelog` consumes its typed fields | no | removes nothing: it preserves a single ordered, tool-parsed file and therefore demonstrates that strong build semantics can justify retaining a monolith ([maintainer guide](https://www.debian.org/doc/manuals/maint-guide/update), [policy](https://www.debian.org/doc/debian-policy/policy.pdf)) |
| Kubernetes release notes [low] — single-project primary source | release-note block and labels on each pull request, not a repository fragment | release tooling selects merged PR metadata for the release; editorial categorization occurs later | release tooling produces version changelogs and the searchable release-note site | PR metadata persists; no fragment deletion | avoids the changelog hot file during feature work, but moves authority to mutable hosting metadata and extraction/editorial tooling ([contributor guide](https://www.kubernetes.dev/docs/guide/release-notes/), [published notes](https://kubernetes.io/releases/notes/)) |

## Findings

### Finding 1 — Unique per-change files reliably remove the ordinary append hot spot

[moderate]

Towncrier explicitly contrasts fragments with a single file that all developers edit; Changie describes its goal as conflict-free file-based changelog management; Changesets uses random human-readable filenames to avoid collisions; and CPython's blurb states that it was designed to eliminate `Misc/NEWS` conflicts with unlikely-to-collide filenames ([Towncrier](https://towncrier.readthedocs.io/en/stable/), [Changie](https://github.com/miniscruff/changie), [Changesets](https://changesets.dev/faq), [blurb](https://github.com/python/blurb)). These are four independent project families and agree on the mechanism: Git merges distinct paths without competing hunks. The evidence is strong about *syntactic* conflict reduction, but does not measure end-to-end conflict rates or semantic mistakes, so the rating is moderate rather than high. [synthesis]

So what for this repo: a collision-resistant path per changelog entry should remove the recurrent “insert immediately below the same heading” conflict during normal feature PRs; it does not by itself validate heading levels, blank lines, version consistency, or prose. [synthesis]

### Finding 2 — Successful fragment systems separate uniqueness from presentation order

[moderate]

CPython uses time plus issue and nonce for uniqueness and chronological sorting; Scriv uses time plus author and branch; Changie sorts by configured component, configured kind, then timestamp; Reno uses a random suffix for filename uniqueness but derives display order from the Git DAG ([blurb](https://github.com/python/blurb), [Scriv commands](https://scriv.readthedocs.io/en/latest/commands.html), [Changie batch](https://changie.dev/cli/changie_batch/), [Reno usage](https://docs.openstack.org/reno/latest/user/usage.html)). Across four independent implementations, no shared incrementing ordinal is required. Timestamp-derived display is only approximate under clock skew, and Reno explicitly calls its order unpredictable, so the evidence supports determinism more strongly than human-intended priority. [synthesis]

So what for this repo: filename uniqueness can be coordination-free, and display order must be a separate concern from it. **The spike measured that neither of two field-derived orderings reproduces this repository's changelog order** — 209 of 214 entries share a release date and a fields-only order moves 176 of them — so for released entries the order has to be stored at assembly time rather than derived. Category, dependency edges, or a stable tie-break key remain available for a design that proves them sufficient on its own corpus, which this one does not. Conflating “unique ID” with “business priority” would recreate hidden semantics. [synthesis]

### Finding 3 — Release-time assembly is a smaller but real serialization point

[moderate]

Towncrier and Scriv both update the monolithic changelog and delete fragments during collection; Changesets deletes consumed changeset files while updating changelogs and package versions; Changie batches fragments into a shared version file and then merges all versions into the parent changelog ([Towncrier CLI](https://towncrier.readthedocs.io/en/stable/cli.html), [Scriv commands](https://scriv.readthedocs.io/en/latest/commands.html), [Changesets FAQ](https://changesets.dev/faq), [Changie quick start](https://changie.dev/guide/quick_start/)). Thus fragmentation eliminates the high-frequency writer collision but not two concurrent release preparations. [synthesis]

So what for this repo: if assembled Markdown remains checked in, normal PRs can be conflict-free but release or regeneration PRs still need a single owner, merge queue, or “regenerate after rebase” rule. If the canonical artifact is not checked in, consumers must be able to build it everywhere they need it. [synthesis]

### Finding 4 — Presentational invariants are commonly enforced by construction

[moderate]

Scriv reparses fragments and adjusts heading syntax during collection; Changie templates headers, change lines, version files, and explicitly inserts a newline between version files; Towncrier renders through templates and has a configuration switch ensuring created fragments end with an empty line; blurb applies a hard-coded section order and reflows paragraphs during merge ([Scriv](https://scriv.readthedocs.io/en/latest/commands.html), [Changie merge](https://changie.dev/cli/changie_merge/), [Towncrier configuration](https://towncrier.readthedocs.io/en/24.8.0/configuration.html), [blurb](https://github.com/python/blurb)). These are independent implementations of formatter/template enforcement, not merely semantic record aggregation. [synthesis]

So what for this repo: the changelog's free-standing-section and blank-line rules fit the prior art if assembly owns all separators and heading levels. A raw concatenation loop would leave the exact historical failure mode intact; a typed fragment schema plus one renderer can make it unrepresentable. [synthesis]

### Finding 5 — Configuration directories work only when they define a composition algebra

[high]

Systemd processes distinct drop-ins lexicographically and applies precedence by directory and filename; APT processes source-list files lexicographically; Terraform treats ordinary files as one declarative document but handles special override files last and lexicographically; Nix modules merge typed option definitions with explicit override and ordering priorities; Zuul recursively loads `.yaml` files in sorted path order and recommends numeric prefixes when variants must follow base jobs ([systemd](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml), [APT](https://manpages.debian.org/testing/apt/sources.list.5.en.html), [Terraform files](https://docs.hashicorp.com/terraform/language/files), [Terraform overrides](https://docs.hashicorp.com/terraform/language/files/override), [NixOS modules](https://nixos.org/manual/nixos/stable/), [Zuul](https://www.zuul-ci.org/docs/zuul/3.7.1/user/config.html)). Cargo instead avoids enumerating each member by allowing workspace-member globs, while Kustomize retains an explicit positional list for resources and order-sensitive patches ([Cargo](https://doc.rust-lang.org/cargo/reference/workspaces.html), [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)). The convergence across more than three independent ecosystems supports the finding strongly. [synthesis]

The remaining surveyed configuration patterns are contrasts, not additional evidence for arbitrary per-entry fragments. Helm collects templates from a directory but resolves configurable values through an explicit precedence stack; Gerrit partitions repository configuration by role into `project.config`, `groups`, and plugin configuration rather than deriving a general record order from filenames; Debian keeps `debian/control` as typed stanzas in one ordered control file rather than a standard fragment directory ([Helm](https://docs.helm.sh/docs/v3/chart_template_guide/values_files/), [Gerrit](https://gerrit-review.googlesource.com/Documentation/config-project-config.html), [Debian Policy](https://www.debian.org/doc/debian-policy/policy.pdf)). [synthesis] These patterns recover semantics through merge rules, precedence layers, explicit references, or retained monoliths—not directory membership alone. [synthesis]

So what for this repo: “read every fragment” is incomplete. A workspace-fragment design must specify identity, duplicate handling, lifecycle collection, precedence, dependency validation, stable tie-breaking, and whether order is semantic. Otherwise it moves ambiguity from TOML array position into filesystem enumeration. [synthesis]

### Finding 6 — Numeric filename prefixes are coordination, not conflict freedom

[moderate]

Systemd and APT make lexicographic filename order semantically visible, and Zuul's own example uses `01_` and `02_` prefixes for base/variant ordering ([systemd](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml), [APT](https://manpages.debian.org/testing/apt/sources.list.5.en.html), [Zuul](https://www.zuul-ci.org/docs/zuul/3.7.1/user/config.html)). In an independently edited Git directory, two branches can therefore reserve the same ordinal or both choose a gap such as `10-`; add/add then collides if the rest of the name is identical, while distinct names still create an unintended tie requiring another rule. [inference] A distributed-database analogue documents the same coordination failure: node-local auto-increment sequences generate duplicate values under concurrent writes ([EDB](https://www.enterprisedb.com/docs/pgd/latest/geo-replication-dev/conflict-resolution/)).

So what for this repo: reserved/sequential ordinals should not be entry identity. If numeric priority is required, it should be a validated field with a deterministic secondary key and an explicit policy for equal priorities; renumbering should never be required merely to insert between records. [synthesis]

### Finding 7 — Git-history generation removes the file but changes the authoring contract

[moderate]

Git-cliff derives customizable changelogs from commit history and recommends history-preserving merge discipline; release-please parses Conventional Commits and maintains a release PR that updates the changelog and version files; Kubernetes stores release-note prose in PR metadata and requires a dedicated review step ([git-cliff](https://git-cliff.org/docs/), [release-please](https://github.com/googleapis/release-please), [Kubernetes](https://www.kubernetes.dev/docs/guide/release-notes/)). The Conventional Commits specification supplies machine-readable commit structure, but it does not itself guarantee user-facing editorial quality ([specification](https://www.conventionalcommits.org/en/v1.0.0/)). [synthesis]

So what for this repo: history generation is attractive only if commit/PR metadata can become the durable editorial source and survives squash, backport, and rewrite policies. The repository's own changelog currently says conventional commits are merely a starting point, which is a material contract mismatch rather than an implementation detail ([repository changelog](../../../docs/product/changelog.md)).

### Finding 8 — Migration should preserve old history as an opaque baseline unless exact round-tripping is proved

[moderate]

Changie's migration guide puts the existing changelog into one version file and explicitly says old versions need not be recreated; Towncrier inserts generated material after a marker, allowing an existing preamble/history to remain; blurb warns that splitting and recombining legacy `Misc/NEWS` does not reproduce the old file exactly because old section ordering and wrapping were inconsistent ([Changie backup](https://changie.dev/guide/backup/), [Towncrier tutorial](https://towncrier.readthedocs.io/en/stable/tutorial.html), [blurb](https://github.com/python/blurb)). These three independent systems favor a boundary migration or expose why full historical fragmentation is risky. [synthesis]

So what for this repo: a migration experiment should compare “one frozen legacy-history fragment plus new typed entries” with “split every historical release,” measuring byte stability, link preservation, and `/now/` output. The evidence does not justify rewriting thousands of historical lines merely for structural purity. [synthesis]

### Finding 9 — Fragmentation changes review and blame rather than simply improving them

[moderate]

Reno deliberately keeps notes peer-reviewed beside code and uses Git history for release attribution; Changesets keeps intent in editable files so squash and commit rewriting do not lose it; CPython release automation rolls many individual entries into one release file and deletes the originals in the release commit ([Reno design](https://files.openstack.org/docs/developer/reno/user/design.html), [Changesets technical decisions](https://changesets.dev/guide/technical-decisions), [CPython release discussion](https://discuss.python.org/t/reverting-changes-with-news-entries/96472)). This makes per-entry review and pre-release blame direct, but the assembled release file's blame points primarily to the release aggregation commit unless history is followed back through deleted files. [inference]

So what for this repo: reviewers gain small, local diffs during feature work but lose the single-page “whole release” view unless CI posts a rendered preview or the release PR includes the complete assembly diff. Both views are needed for the existing editorial obligation. [synthesis]

### Finding 10 — Published regret evidence is insufficient

[uncertain] — survivorship bias and no independently documented adoption-and-reversal case found.

The survey found active use, operational bugs, and partial adaptations: CPython excludes `NEWS.d` from release tarballs after generating `Misc/NEWS`, and an early docs-build issue showed that assuming fragment inputs existed in tarballs broke downstream builds ([release automation](https://github.com/python/release-tools/blob/main/release.py), [CPython issue](https://bugs.python.org/issue31036)). It did not find a credible project post-mortem saying the fragment model itself was abandoned because its costs exceeded its benefit. Absence from search is not evidence that regret does not exist. [synthesis]

So what for this repo: treat success stories as survivorship-biased. A time-boxed repository-local prototype and conflict/review measurements would be more decision-relevant than another adoption list. [synthesis]

## Ordering schemes compared

| scheme | concurrent-branch collision behavior | deterministic total order? | principal failure mode |
| --- | --- | --- | --- |
| random UUID/content hash only | conflict-free for practical purposes when IDs are sufficiently collision-resistant; content-identical fragments intentionally share a hash unless salted [synthesis] | yes lexicographically, but the order has no temporal or business meaning [synthesis] | unreadable order; content edits rename hash-addressed files unless identity is separated from content [inference] |
| timestamp + random nonce | conflict-free without coordination; used by Scriv and blurb ([Scriv](https://scriv.readthedocs.io/en/latest/commands.html), [blurb](https://github.com/python/blurb)) | yes with nonce as tie-break, but only approximates creation chronology | clock skew; timestamp edits can reorder published history [synthesis] |
| ULID / UUIDv7 / KSUID | coordination-free uniqueness with lexicographic time locality; KSUID calls its time order loose rather than invariant, and UUIDv7 permits monotonic subfields within a millisecond ([KSUID](https://github.com/segmentio/ksuid), [RFC 9562](https://datatracker.ietf.org/doc/html/rfc9562)) | yes as bytes/text when canonical encoding is used; same-time order depends on entropy/monotonic implementation | wall-clock rollback/skew; identifier order should not be treated as causal or editorial priority [synthesis] |
| issue/PR number + category | conflict-free if the external ID is unique; Towncrier adds a suffix if a filename already exists ([Towncrier CLI](https://towncrier.readthedocs.io/en/stable/cli.html)) | yes by category then numeric/lexical key | one change may need multiple entries; offline or cross-tracker work lacks a natural ID [synthesis] |
| category then stable unique key | conflict-free when the key is collision-resistant; common in Towncrier, Changie, and blurb ([Towncrier](https://towncrier.readthedocs.io/en/stable/tutorial.html), [Changie](https://changie.dev/cli/changie_batch/), [blurb](https://github.com/python/blurb)) | yes | category order becomes policy and needs versioned configuration; within-category order may be arbitrary [synthesis] |
| explicit `after:` / `depends_on` edges + topological sort | independent fragments can add disjoint edges without file collision | only after adding a deterministic tie-break for unrelated nodes; topological order is otherwise non-unique ([GNU `tsort`](https://www.gnu.org/software/coreutils/manual/html_node/tsort-invocation.html), [Python `graphlib`](https://docs.python.org/3.10/library/graphlib.html)) | cycles, missing targets, and unstable tie order unless all are linted [synthesis] |
| explicit scalar priority + stable unique tie-break | independent files do not collide; equal priorities are safe if documented as peers [synthesis] | yes | people may infer stronger precedence than intended; priority edits reshuffle output [inference] |
| reserved/sequential ordinal (`010`, `020`, next counter) | not conflict-free: branches can reserve the same value; same filename creates add/add, distinct suffixes create equal-rank ambiguity [inference] | only if allocation is globally serialized | concurrency slips, gap exhaustion, and renumbering churn; distributed node-local sequences exhibit the same duplicate-allocation shape ([EDB](https://www.enterprisedb.com/docs/pgd/latest/geo-replication-dev/conflict-resolution/)) |
| filesystem enumeration with no specified sort | path additions do not collide, but output is not portable or contractually deterministic [synthesis] | no | platform/runtime-dependent order; silent presentation drift [inference] |

For an ordered registry, dependency edges encode only real prerequisites. A deterministic renderer still needs a stable tie-break for unrelated ready nodes because standard topological sorting permits several valid total orders ([GNU `tsort`](https://www.gnu.org/software/coreutils/manual/html_node/tsort-invocation.html), [Python `graphlib`](https://docs.python.org/3.10/library/graphlib.html)). For a changelog, release version/date and category usually carry more reader meaning than creation order; timestamp/ULID is best treated as a tie-break, not editorial truth. [synthesis]

## Anti-patterns and regrets

- **Checking in both editable fragments and an editable generated monolith without a drift gate.** CPython explicitly argued that leaving generated `Misc/NEWS` in the source tree invites hand edits that will be lost on regeneration, while its release tarballs still ship the generated file ([CPython issue](https://bugs.python.org/issue31036), [release automation](https://github.com/python/release-tools/blob/main/release.py)). One representation must be authoritative; if both are tracked, CI must regenerate and demand a clean diff. [synthesis]
- **Raw concatenation for a presentational contract.** Scriv reparses headings, Changie inserts version separators, and blurb normalizes order and wrapping; these are evidence that syntax-aware rendering is part of the product, not polish ([Scriv](https://scriv.readthedocs.io/en/latest/commands.html), [Changie](https://changie.dev/cli/changie_merge/), [blurb](https://github.com/python/blurb)).
- **Numeric-prefix allocation as an informal shared counter.** Prefixes are appropriate when precedence is deliberately small and curated, as in systemd and Zuul, but per-entry “take the next number” recreates a shared allocation point ([systemd](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml), [Zuul](https://www.zuul-ci.org/docs/zuul/3.7.1/user/config.html)). [synthesis]
- **One fragment per historical line during migration.** Changie preserves legacy history as one version file, while blurb documents non-byte-identical legacy round trips ([Changie backup](https://changie.dev/guide/backup/), [blurb](https://github.com/python/blurb)). Full backfill increases file count and diff noise without reducing future hot-spot writes. [synthesis]
- **Assuming fragments eliminate editorial review.** Kubernetes requires a dedicated release-note review step, Reno requires peer review, and release-note research reports missing information and layout problems as common issue types ([Kubernetes](https://www.kubernetes.dev/docs/guide/release-notes/), [Reno design](https://files.openstack.org/docs/developer/reno/user/design.html), [release-note issue study](https://arxiv.org/abs/2203.15592)). Fragments move review earlier; they do not make prose complete. [synthesis]
- **Using directory membership when the real contract is a positional patch series.** Kustomize keeps order-sensitive patches in an explicit list, while Terraform makes ordinary multi-file declarations order-insensitive and isolates overrides with explicit precedence ([Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/), [Terraform](https://docs.hashicorp.com/terraform/language/files/override)). If arbitrary reorder changes meaning, a directory alone is the wrong abstraction. [synthesis]
- **Treating Mergiraf as a TOML/Markdown semantic merger.** Mergiraf is syntax-aware for its supported language profiles and explicitly assumes some syntax-element order is independent; that assumption is unsafe where Markdown layout or TOML array position is load-bearing ([Mergiraf overview](https://docs.rs/mergiraf/latest/mergiraf/), [conflict model](https://docs.rs/crate/mergiraf/latest/source/doc/src/conflicts.md)). A domain-specific merge driver such as GNU `git-merge-changelog` can parse blank-line-delimited changelog entries, but it still needs the repository's exact entry grammar ([manual](https://manpages.ubuntu.com/manpages/noble/en/man1/git-merge-changelog.1.html)).
- **Calling `git-hist` a semantic merge alternative.** The located `git-hist` project is a terminal history browser, not a merge driver ([project](https://github.com/arkark/git-hist)). If a different tool was intended, its identity is a known unknown.

No well-evidenced wholesale regret/reversal case was found. The closest evidence is partial boundary correction: CPython kept fragments in development source, generated a monolith for distribution, and fixed docs/release automation that had assumed both representations were always present ([CPython issue](https://bugs.python.org/issue31036), [release automation](https://github.com/python/release-tools/blob/main/release.py)). [uncertain — survivorship bias and single-project evidence]

## Applicability to this repository

### `docs/product/changelog.md` and `packages/agentbundle/CHANGELOG.md`

The evidence matches this problem closely: Towncrier, Scriv, Changie, and blurb all turn independently reviewed entry files into a formatted human-facing release document, and several own heading/category/separator formatting by construction ([Towncrier](https://towncrier.readthedocs.io/en/stable/), [Scriv](https://scriv.readthedocs.io/en/latest/commands.html), [Changie](https://changie.dev/cli/changie_batch/), [blurb](https://github.com/python/blurb)). [synthesis] The repository has two audiences and two changelog artifacts, so a repo-local design would need to decide whether one typed fragment can project to both, whether package-only changes create one or two entries, and which artifact owns wording and version identity. External prior art does not settle that mapping. [synthesis]

The presentational invariant is not an objection to fragmentation; it is a reason to require a real renderer. A fragment schema could carry artifact, version, date, optional `Highlights`, and categorized Markdown bodies, while the renderer exclusively emits `##`/`###` levels and blank-line separators. [inference] Required gates would include schema validation; a **collision-resistant entry identity that is not `(artifact, version)`** — the spike measured three duplicate `(artifact, version)` keys in the current file — `[core][2.3.0]` (two free-standing entries, both 2026-08-07), `[core][2.5.5]` (2026-08-10 twice), and `[core][2.5.1]` (2026-08-09 and 2026-08-08) — so a uniqueness gate on that pair would reject the existing corpus; newest-first deterministic ordering; exact rendered-section separation; `/now/` projection parity; and “regenerate then clean diff” if the assembled Markdown is committed. [synthesis] Whether the canonical Markdown remains in Git is a repository-local product/distribution decision: Towncrier commonly commits it, Reno can render from durable notes, and CPython omits fragments but ships generated `NEWS` in release archives ([Towncrier CLI](https://towncrier.readthedocs.io/en/stable/cli.html), [Reno usage](https://docs.openstack.org/reno/latest/user/usage.html), [CPython release automation](https://github.com/python/release-tools/blob/main/release.py)).

Migration evidence favors leaving all released history intact as an opaque baseline and fragmenting only subsequent entries, unless a byte-for-byte round-trip plus `/now/` parity is demonstrated ([Changie backup](https://changie.dev/guide/backup/), [blurb](https://github.com/python/blurb)). This preserves existing blame for old releases; new entries get per-fragment blame, while generated release sections acquire release-commit blame. [synthesis]

### `workspace.toml`

The analogy is weaker. `.d` conventions work when records are commutative declarations, have unique semantic keys, or carry explicit precedence/ordering metadata; Kustomize retains a positional index where patch order itself matters ([Terraform files](https://docs.hashicorp.com/terraform/language/files), [NixOS modules](https://nixos.org/manual/nixos/stable/), [systemd](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml), [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)). [synthesis] The repository's own contract says list order is non-semantic for routing, but closeout reconciliation uses array index to distinguish duplicate-valued entries ([workspace contract](../../../workspace.toml), [implementation](../../../packs/core/.apm/skills/workspace-status/scripts/workspace_status.py)). That distinction must be resolved before choosing a fragment model. [synthesis]

If membership identity can become a required stable entry ID/path and collection/lifecycle becomes an explicit field or directory component, independently named records could be assembled deterministically without using position as identity. [inference] If duplicate records with identical values must remain independently addressable, each fragment needs its own collision-resistant ID. [inference] If “first ready entry” is an intended priority contract, then priority must be made explicit—priority field plus stable key, or dependency DAG plus stable tie-break—because filesystem order and implicit array position are not safe substitutes. [synthesis] Required gates would include schema/type validation, unique IDs and paths as appropriate, referential integrity for `needs`, cycle detection, lifecycle/collection validity, deterministic assembly under randomized input enumeration, duplicate policy, and exact consumer parity against the current engine. [synthesis]

The evidence does not decide whether `workspace.toml` should be assembled into a checked-in compatibility file, loaded directly from fragments, or replaced by a non-positional registry API. Terraform demonstrates direct directory loading; Cargo demonstrates glob-based membership; Zuul demonstrates sorted recursive directory loading; each makes different semantic commitments ([Terraform](https://docs.hashicorp.com/terraform/language/files), [Cargo](https://doc.rust-lang.org/cargo/reference/workspaces.html), [Zuul](https://www.zuul-ci.org/docs/zuul/3.7.1/user/config.html)). A repository-local compatibility inventory of every reader/writer and an equivalence test corpus is required before any decision. [synthesis]

### Alternatives and wrong-answer conditions

- **Union driver:** Git warns that union takes both sides in random order and requires verification, which is incompatible with load-bearing presentation or positional identity ([Git attributes](https://git-scm.com/docs/gitattributes)).
- **Domain-specific merge driver:** GNU `git-merge-changelog` shows that entry-aware three-way merge can solve concurrent top insertions without fragment files ([manual](https://manpages.ubuntu.com/manpages/noble/en/man1/git-merge-changelog.1.html)). It is a plausible smaller answer when the grammar is stable, every environment can install the driver, and semantic validation follows. [synthesis]
- **AST/structured merge:** Mergiraf improves syntax-element merges but is not evidence for this repository's Markdown/TOML domain contract; a schema-aware TOML merger could work only if it understands lifecycle collections, duplicate identity, and order semantics ([Mergiraf](https://docs.rs/mergiraf/latest/mergiraf/)). [synthesis]
- **Merge queue:** GitHub's queue retests merge groups against the busy protected branch and removes changes that fail checks, reducing stale-base integration races but not making two conflicting append edits semantically mergeable ([GitHub](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue)). It serializes pain rather than removing the hot file. [synthesis]
- **Generate from Git history:** git-cliff, release-please, semantic-release, and Kubernetes-style PR metadata remove fragment files, but require durable metadata discipline and still commonly create a shared release PR/changelog ([git-cliff](https://git-cliff.org/docs/), [release-please](https://github.com/googleapis/release-please), [semantic-release changelog plugin](https://github.com/semantic-release/changelog), [Kubernetes](https://www.kubernetes.dev/docs/guide/release-notes/)). This is wrong where the curated prose intentionally differs from commit history. [synthesis]
- **Do not store order:** this is strongest when consumers need a set/DAG rather than a human sequence. Terraform ordinary files and Cargo workspace globs demonstrate order-insensitive composition ([Terraform](https://docs.hashicorp.com/terraform/language/files), [Cargo](https://doc.rust-lang.org/cargo/reference/workspaces.html)). It is wrong for newest-first release presentation unless order is derived from typed version/date fields. [synthesis]

Fragmentation is the wrong answer when edit concurrency is low; when no build/render step can be guaranteed at consumption time; when the file's meaning is an intentionally hand-curated total order that cannot be derived from fields or edges; when consumers require the exact monolithic source bytes; or when a domain-specific merge driver plus validation removes the measured conflicts at materially lower operational cost. [synthesis] Its costs are proportional to entry volume: more paths in reviews and checkouts, cross-file searches for a whole release/queue, release aggregation diffs, migration/blame discontinuity, and permanent tooling ownership. [synthesis] None of the surveyed sources provides a transferable break-even threshold for those costs.

## Known unknowns

- **Known-unknown:** How many actual merge conflicts, rebases, and incorrect manual resolutions do the three target files cause per month, rather than merely how often they are touched? Would be closed by: a repository-local conflict/rebase audit over merged and abandoned branches.
- **Known-unknown:** Is `workspace.toml` array order intentionally a priority anywhere beyond index-based duplicate identity and the `next_queue` projection? Would be closed by: an inventory of every parser, writer, projection, fixture, and external adopter, plus permutation/metamorphic tests.
- **Partly answered** by the spike: a typed renderer reproduces the current changelog except at 8 pre-existing separator defects, and `/now/` projection parity is exact. Byte-identity with the current file is therefore **No**. What remains open: does assembly stay deterministic under randomized fragment enumeration? Would be closed by: a shuffled-input golden-output test.
- **Known-unknown:** Must the assembled changelogs and workspace file be present in source checkouts, package archives, documentation builds, or third-party tooling that cannot run the assembler? Would be closed by: a consumer/distribution inventory and clean-checkout build matrix.
- **Known-unknown:** Which tool was meant by “git-hist” as a semantic-merge alternative? Would be closed by: the intended project URL; the located `git-hist` is only a history browser ([located project](https://github.com/arkark/git-hist)).
- **Known-unknown:** Did any substantial project abandon changelog fragmentation because of file count, review, or release burden? Would be closed by: a maintainer post-mortem, removal PR with rationale, or comparative conflict/review metrics; targeted searches found no dependable case.
- **Known-unknown:** What naming cardinality is needed to make collisions acceptably improbable for this repository's branch concurrency? Would be closed by: measured creation rate and an explicit collision-budget calculation for the chosen random/ULID scheme.
- **Unknowable:** Which total order two genuinely concurrent, causally unrelated entries “really” had? Why not: neither wall clocks nor Git topology establish a unique human/editorial order without an additional policy.
- **Unknowable:** Whether fragmentation will remain cheaper than a semantic merge driver as future concurrency and tooling evolve. Why not: it is a future operational counterfactual; only ongoing repository metrics can inform it.

## Sources

1. [Towncrier documentation](https://towncrier.readthedocs.io/en/stable/) — primary, project documentation.
2. [Towncrier tutorial](https://towncrier.readthedocs.io/en/stable/tutorial.html) — primary, project documentation.
3. [Towncrier CLI reference](https://towncrier.readthedocs.io/en/stable/cli.html) — primary, project documentation.
4. [Towncrier configuration reference](https://towncrier.readthedocs.io/en/24.8.0/configuration.html) — primary, project documentation.
5. [Reno usage](https://docs.openstack.org/reno/latest/user/usage.html) — primary, OpenStack project documentation.
6. [Reno design constraints](https://files.openstack.org/docs/developer/reno/user/design.html) — primary, OpenStack project documentation.
7. [Changesets FAQ](https://changesets.dev/faq) — primary, project documentation.
8. [Changesets technical decisions](https://changesets.dev/guide/technical-decisions) — primary, project documentation.
9. [Scriv commands](https://scriv.readthedocs.io/en/latest/commands.html) — primary, project documentation.
10. [Scriv configuration](https://scriv.readthedocs.io/en/latest/configuration.html) — primary, project documentation.
11. [Changie configuration](https://changie.dev/config/) — primary, project documentation.
12. [Changie batch](https://changie.dev/cli/changie_batch/) — primary, project documentation.
13. [Changie merge](https://changie.dev/cli/changie_merge/) — primary, project documentation.
14. [Changie migration/backup](https://changie.dev/guide/backup/) — primary, project documentation.
15. [CPython blurb](https://github.com/python/blurb) — primary, project repository documentation.
16. [CPython pull-request lifecycle](https://devguide.python.org/contrib/code/pull-request-lifecycle/) — primary, adopter documentation.
17. [CPython release automation](https://github.com/python/release-tools/blob/main/release.py) — primary, adopter implementation.
18. [CPython docs-build issue 31036](https://bugs.python.org/issue31036) — primary, adopter issue tracker.
19. [CPython revert/release discussion](https://discuss.python.org/t/reverting-changes-with-news-entries/96472) — primary, practitioner discussion.
20. [cargo-release](https://github.com/crate-ci/cargo-release) — primary, project repository documentation.
21. [Debian maintainer guide: updating a package](https://www.debian.org/doc/manuals/maint-guide/update) — primary, distribution documentation.
22. [Debian Policy Manual](https://www.debian.org/doc/debian-policy/policy.pdf) — primary, normative documentation.
23. [Kubernetes release-note contributor guide](https://www.kubernetes.dev/docs/guide/release-notes/) — primary, project documentation.
24. [Kubernetes published release notes](https://kubernetes.io/releases/notes/) — primary, project publication.
25. [systemd unit/drop-in documentation source](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml) — primary, project documentation source.
26. [APT `sources.list(5)`](https://manpages.debian.org/testing/apt/sources.list.5.en.html) — primary, tool manual.
27. [Terraform files and configuration structure](https://docs.hashicorp.com/terraform/language/files) — primary, vendor/project documentation.
28. [Terraform override files](https://docs.hashicorp.com/terraform/language/files/override) — primary, vendor/project documentation.
29. [NixOS module system manual](https://nixos.org/manual/nixos/stable/) — primary, project documentation.
30. [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html) — primary, project documentation.
31. [Kustomize task documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/) — primary, project documentation.
32. [Helm values precedence](https://docs.helm.sh/docs/v3/chart_template_guide/values_files/) — primary, project documentation.
33. [Zuul project configuration](https://www.zuul-ci.org/docs/zuul/3.7.1/user/config.html) — primary, project documentation; older version page, so exact current syntax should be rechecked before adoption.
34. [Gerrit project configuration](https://gerrit-review.googlesource.com/Documentation/config-project-config.html) — primary, project documentation.
35. [Git attributes and merge drivers](https://git-scm.com/docs/gitattributes) — primary, Git documentation.
36. [GNU `git-merge-changelog` manual](https://manpages.ubuntu.com/manpages/noble/en/man1/git-merge-changelog.1.html) — primary, packaged tool manual.
37. [Mergiraf overview](https://docs.rs/mergiraf/latest/mergiraf/) — primary, generated project API documentation.
38. [Mergiraf conflict model](https://docs.rs/crate/mergiraf/latest/source/doc/src/conflicts.md) — primary, project documentation source.
39. [GitHub merge queue](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue) — primary, vendor documentation.
40. [git-cliff](https://git-cliff.org/docs/) — primary, project documentation.
41. [release-please](https://github.com/googleapis/release-please) — primary, project repository documentation.
42. [semantic-release changelog plugin](https://github.com/semantic-release/changelog) — primary, project repository documentation.
43. [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) — primary, specification.
44. [KSUID reference implementation](https://github.com/segmentio/ksuid) — primary, project repository documentation; vendor-authored performance claims were not used as independent validation.
45. [RFC 9562: UUIDs](https://datatracker.ietf.org/doc/html/rfc9562) — primary, standards document.
46. [GNU `tsort`](https://www.gnu.org/software/coreutils/manual/html_node/tsort-invocation.html) — primary, project manual.
47. [Python `graphlib.TopologicalSorter`](https://docs.python.org/3.10/library/graphlib.html) — primary, language documentation.
48. [EDB distributed sequence conflict guidance](https://www.enterprisedb.com/docs/pgd/latest/geo-replication-dev/conflict-resolution/) — primary vendor documentation; used only as a concurrency-shape analogue.
49. [Demystifying Software Release Note Issues on GitHub](https://arxiv.org/abs/2203.15592) — primary research paper.
50. [Repository `docs/product/changelog.md`](../../../docs/product/changelog.md) — primary, repository contract at investigated revision.
51. [Repository `workspace.toml`](../../../workspace.toml) — primary, repository data contract at investigated revision.
52. [Repository closeout projection](../../../packs/core/.apm/skills/workspace-status/scripts/workspace_status.py) — primary, repository implementation at investigated revision.
53. [Repository conventions](../../../docs/CONVENTIONS.md) — primary, repository policy at investigated revision.
54. [`git-hist`](https://github.com/arkark/git-hist) — primary, project repository documentation; establishes that the located project is a history browser, not a merge tool.
