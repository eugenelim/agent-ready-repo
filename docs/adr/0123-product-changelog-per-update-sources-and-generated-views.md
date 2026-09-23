# ADR-0123: Product changelog uses per-update sources and generated views

- **Status:** Accepted
- **Date:** 2026-09-22
- **Areas:** documentation, tooling
- **Reversibility:** high
- **Decision-makers:** Platform Core maintainers
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0112 (establishes the repository pattern that shared corpus views are generated or absent rather than hand-maintained)

## Decision summary

- **Decision:** New product changelog updates are authored as independent reviewed fragments; complete changelog views are generated from those fragments and the frozen historical file.
- **Because:** independent source paths remove the same-anchor conflicts that prevent concurrent updates and obstruct a merge queue.
- **Applies to:** `docs/product/changelog.md`, new records under `docs/product/changelog.d/`, the complete local changelog, `/now/`, release validation, and documentation publication.
- **Tradeoff accepted:** the tracked `docs/product/changelog.md` stops at the cutover and readers use the published site or generated build output for the complete current view.
- **Revisit if:** an always-current tracked aggregate becomes a firm product requirement and the hosting platform can regenerate it inside merge-group commits without a privileged post-merge writer.

## Context

`docs/product/changelog.md` currently serves three roles: contributors edit it,
it preserves release history, and documentation tooling reads it to produce the
complete changelog and `/now/`. Concurrent changes prepend sections at the same
top-of-file anchor.

The changelog fragmentation spike reproduced conflicts in 39 of 43 exposed
rebases. All 39 were same-anchor insertions. A merge queue can retest compatible
changes against a temporary combined commit, but it cannot make independently
authored changes merge when they conflict before checks run.

Generating changelog content from commits is not an adequate replacement for
reviewed source. The generator-quality spike found only 39 of 245 candidate
commit pairs clean enough for combined generation. Changelog text carries
editorial intent that commit metadata does not preserve.

Highlights remain per update. An LLM may help draft an update inside its
implementation pull request, but a human reviewer approves the final text. The
assembler orders and copies those records; it does not combine, summarize, or
rewrite their Highlights.

The current `merge=regen` convention is not a sufficient merge-queue contract.
The configured driver keeps one side and leaves a stale projection for a
maintainer to regenerate and commit-amend. Git also defines custom merge-driver
commands in clone-local configuration, while GitHub merge queues test
GitHub-created temporary branches. A queue check can detect a stale tracked
aggregate, but it cannot amend that temporary commit.

Historical compatibility also matters. Existing repository links target
headings inside `docs/product/changelog.md`. Removing or renaming that path
would break durable links in GitHub and older documentation.

## Decision

**We will author new product changelog updates as independent reviewed
fragments, retain `docs/product/changelog.md` as frozen historical source, and
generate complete changelog views from both.**

- **D1:** `docs/product/changelog.md` remains tracked at its current path as the
  read-only source for pre-cutover history. A migration notice may be added,
  but historical release sections and anchor-producing headings do not change.
- **D2:** Every post-cutover update is authored at
  `docs/product/changelog.d/<id>.md`, where `<id>` is a lowercase UUIDv4
  created by repository tooling and matches the fragment envelope identity.
- **D3:** Each fragment owns one update's final, human-reviewed Highlights and
  detailed sections. Assembly preserves that update as an atomic record and
  never combines, summarizes, or rewrites its Highlights.
- **D4:** One deterministic, offline assembler reads the frozen history and
  validated fragments. It uses canonical ordering and has no LLM, network,
  clock, or Git-history dependency.
- **D5:** The complete local changelog is generated at
  `build/product-changelog.md`. The documentation site and `/now/` are generated
  from the same parsed model. Generated views are never authoring inputs.
- **D6:** No tracked combined changelog, custom merge driver, post-merge bot
  commit, or protected-branch bypass is part of the merge-queue-critical path.
- **D7:** Release validation, release-impact detection, the documentation
  build, and `/now/` consume the shared changelog model rather than reparsing or
  editing a generated aggregate.

## Decision drivers

- **Merge independence.** Concurrent updates must modify different tracked
  paths.
- **Editorial fidelity.** Reviewed update text must remain the publication
  source.
- **Merge-queue compatibility.** Validation must not require amending a
  GitHub-created merge-group commit.
- **Historical compatibility.** Existing repository links and release headings
  must remain valid.
- **Determinism.** The same sources must produce byte-identical output for each
  consumer across repeated runs.
- **Operational restraint.** The design must not introduce a service, bot
  writer, protected-branch bypass, or runtime model dependency.

## Consequences

**Positive:**

- Concurrent updates no longer contend for one top-of-file insertion point.
- Merge-group commits contain only independent fragment sources and do not need
  regeneration amendments.
- Each update's Highlights remains reviewable beside its implementation.
- The public changelog and `/now/` share parsing, ordering, and identity rules.
- Historical links remain valid at `docs/product/changelog.md`.
- Publication remains offline, deterministic, and contained in the existing
  repository build.

**Negative:**

- `docs/product/changelog.md` on GitHub contains history only through the
  cutover. Readers need the published `/changelog/` page or
  `build/product-changelog.md` for the complete current view.
- The repository gains a fragment schema, assembler, validation rules, and
  migration gate that require maintenance.
- Many small source files replace one append-only document.
- In-flight branches that edit the shared changelog must convert their new
  entry into a fragment before merging.
- Stable identity and rendering contracts become mechanically enforced rather
  than implicit in heading order.

**Revisit if:** an always-current tracked aggregate becomes a firm product requirement and the hosting platform can regenerate it inside merge-group commits without a privileged post-merge writer.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** synthetic concurrent branches with distinct fragment IDs merge without a changelog-path conflict; shuffled and repeated assembly is byte-identical; every fragment and Highlights item appears exactly once without rewriting; historical repository anchors remain valid; regeneration leaves no tracked diff.
- **Owner:** the `build-check` gate and Platform Core maintainers.

## Alternatives considered

- **Keep editing the monolithic changelog.** Rejected against merge
  independence: every update continues to insert at the same shared anchor.
- **Track the generated aggregate with `merge=regen`.** Rejected against
  merge-queue compatibility: the driver keeps a stale side and requires local
  regeneration plus commit amendment, which a queue check cannot apply to its
  temporary commit.
- **Regenerate and commit the aggregate after merge with a bot.** Rejected
  against operational restraint: it creates an eventually consistent main
  branch and requires a writer with protected-branch authority.
- **Generate the aggregate in every pull request and require freshness.**
  Rejected against merge independence: concurrent pull requests still modify
  the same tracked output, and the merge-group commit cannot repair drift.
- **Store fragments without producing a complete view.** Rejected because the
  documentation site, `/now/`, release checks, and maintainers still need a
  coherent chronological view.
- **Split all historical entries into fragments.** Rejected against historical
  compatibility: duplicate historical package/version combinations and
  non-reconstructible same-date ordering make a backfill invent identity and
  sequence.

## References

- [`docs/architecture/changelog-fragment-source.md`](../architecture/changelog-fragment-source.md)
  — the proposed architecture and implementation boundaries.
- [`docs/product/research/append-log-fragmentation-survey.md`](../product/research/append-log-fragmentation-survey.md)
  — prior-art and repository evidence.
- [`docs/product/research/changelog-fragmentation-spike.md`](../product/research/changelog-fragmentation-spike.md)
  — measured conflict reproduction and migration findings.
- [`docs/product/research/changelog-generator-quality-spike.md`](../product/research/changelog-generator-quality-spike.md)
  — evidence that commit-derived generation loses reviewed intent.
- [Git attributes: defining a custom merge driver](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver).
- [GitHub: managing a merge queue](https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue).
- ADR-0112 — generated corpus-view precedent.
