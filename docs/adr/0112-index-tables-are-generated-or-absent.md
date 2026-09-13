# ADR-0112: Index tables over a document corpus are generated or absent, never hand-maintained

- **Status:** Accepted <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-09-13
- **Decision-makers:** eugenelim
- **Consulted:** applied prior-art survey across six proposal processes, five spec-driven-development frameworks, thirteen ADR tools, and four changelog-fragment tools — [`docs/product/research/document-index-patterns-survey.md`](../product/research/document-index-patterns-survey.md)
- **Supersedes:** none
- **Related:** [RFC-0002](../rfc/0002-self-hosting.md) (its `Manual` classification of the three index files is corrected by that RFC's 2026-09-13 erratum, not by this ADR); [ADR-0001](0001-adopt-agents-md-and-doc-hierarchy.md); [ADR-0006](0006-doc-drift-construction-and-judgment.md); [ADR-0007](0007-ship-doc-drift-lint-as-work-loop-skill-script.md); [RFC-0016](../rfc/0016-doc-drift-mechanical-gate.md); [RFC-0096](../rfc/0096-portable-delivery-artifact-lifecycle.md) § Wave 7d

## Decision summary

- **Decision:** An index table over a document corpus is generated from that corpus or it does not exist; hand-maintenance is not a third option.
- **Because:** a hand-maintained index drifts silently, and every write to it is a merge conflict against every parallel branch.
- **Applies to:** `docs/specs/README.md`, `docs/adr/README.md`, `docs/rfc/README.md`, their three adopter seeds, and the skills that write them.
- **Tradeoff accepted:** sixteen ticked acceptance criteria on frozen specs assert an index row that will no longer exist; this ADR is their disposition.
- **Revisit if:** anything begins reading the spec corpus by index rather than by directory, or a generated flat table outgrows scanning.

## Context

This repository keeps three hand-maintained index tables. Measured 2026-09-13 at
merge-base `aa176ee2c`:

| Index | Documents | Indexed | Absent | Stale | Touches/30d | Size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `docs/specs/README.md` | 446 | 231 | 215 | 5 statuses | 120 | 236 KB |
| `docs/rfc/README.md` | 101 | 97 | 4 | not measured | 17 | 59 KB |
| `docs/adr/README.md` | 111 | 111 | 0 | 1 status | 28 | 20 KB |

The counts move under any month of activity — an earlier measurement eight days
prior read 444 / 230 / 214 for the spec index — which is the point: only the
drift direction is stable. The one stale ADR status is ADR-0050, whose file
reads `Superseded by ADR-0055` while its row reads `Accepted`; the other
apparent disagreements are the table correctly normalising a qualified status
line down to its lifecycle token.

The spec index has drifted to 52% coverage. RFC-0096 § Wave 7d already recorded
the harm in its own terms — "211 of its 426 directories (49%) appear in no row …
That volume degrades the loops that read it."

**Nothing reads the spec index.** An exhaustive consumer sweep across `packs/`,
projected skills, `guides/`, `tools/`, `tests/`, `web/`, `docs-site/`, workflows,
`Makefile` and `llms.txt`, over twelve reference spellings, found 216
instructions to *write* it and zero instructions to read it. It is absent from
`llms.txt`, which lists the RFC and ADR indexes as agent-facing surfaces.
`build-site.py:1039` routes `../specs/...` to a GitHub URL, "not in site". Its
only two mechanical readers are tests inside a spec's own delivery asserting that
spec's own row — the index verifying itself, not being consumed.

The ADR and RFC indexes differ: both are linked from `llms.txt`, the governance
tutorial reads the ADR index with `cat`, and a roster test parses the RFC-0028
row.

Prior art agrees on all three points. No file-based spec-driven-development
framework — GitHub Spec Kit, AWS Kiro, BMAD, agent-os, OpenSpec — maintains any
index over its spec corpus; all five discover specs by filesystem convention.
agent-os is the sharpest case: it ships a generated `index.yml` for `standards/`
and deliberately does not extend it to specs. Among long-running proposal
processes, the ones that survived at scale generate their index (PEP 0,
Kubernetes KEPs, IETF) while the hand-maintained ones carry documented strain
(TC39 volume issues, Ember's abandoned tracker). Generation alone is not
sufficient: Rust's RFC book *is* generated, but flat from filenames, and it is
the process with the "not easily searchable and indexable" complaints and a
third-party index built as a workaround. Among ADR tools, `adr-tools` and
`adr-log` both generate, both emitting only number, title and link — less than
this repository's table already carries.

The write-contention has a solved shape. towncrier, scriv, reno and changesets
were each built for one stated reason: one shared file that every change writes
to produces merge conflicts. The remedy is one file per unit, assembled at build
time.

Two constraints bound the delivery. ADR-0006 establishes that adopters cannot be
given a fail-closed documentation gate — no guaranteed runtime, no pre-PR hook
event — and that prevention must travel on surfaces that project. ADR-0007
corrects the packaging premise and establishes the working route: ship the check
as a skill script, agent-invoked. That route is in production today —
`tools/repo/build_gate_chain.py:255` invokes
`.claude/skills/work-loop/scripts/lint-spec-status.py`, the self-hosted
projection of the pack source, not a copy.

## Decision

**We will treat an index table over a document corpus as generated from that
corpus or absent, and never hand-maintained.** Applying that rule to the three
indexes:

1. **The spec index is retired.** `docs/specs/README.md` keeps its explanation of
   the `docs/specs/<feature>/` convention and loses both tables. Specs are
   discovered by listing the directory, as every surveyed framework does.
   `new-spec` drops its step 8 index write and states the rationale in its place.
   The `core` seed loses its two placeholder tables and its
   `<!-- Update this list as features are added. -->` comment.
2. **The ADR and RFC indexes are generated flat**, from the `# ADR-NNNN: Title` /
   `# RFC-NNNN: Title` heading and the `- **Status:**`, `- **Date opened:**`,
   `- **Date closed:**` metadata lines already present in every document. Flat is
   correct at 110 and 101 documents; PEP 0 does not group until roughly ten times
   that.
3. **One generator per index type ships as a script in the pack that owns that
   index** — `governance-extras`, alongside the `next-ordinal.py` those skills
   already carry. `new-adr` and `new-rfc` invoke it in place of their hand-edit
   step. Repo tooling invokes **the same script through its self-hosted
   projection**, never a duplicate, following `lint-spec-status.py` exactly. The
   generator carries `--check` for the gate chain and `--write` for the authoring
   step.

## Decision drivers

- **Does anything read it?** The discriminator between retiring an index and
  generating one.
- **Does generating it make it usable?** Rust proves generation alone does not.
- **Can the mechanism reach adopters?** ADR-0006 bounds this to agent-invoked.
- **Does it remove the write-contention**, not merely the staleness?
- **Is there one source of truth for the generator**, or two that can drift?

## Consequences

**Positive:**

- 215 absent specs, 4 absent RFCs, and every stale status value stop being
  possible: an index that cannot disagree with its corpus, or is not there.
- The largest write-contention surface in the repository — 120 commits per 30
  days against one 236 KB file — disappears rather than being reduced.
- Adopters get the same generator this repository runs, on the route ADR-0007
  proved, with no new guarantee ADR-0006 forbids.
- `new-spec` loses a step; `new-adr` and `new-rfc` each trade a hand-edit for a
  command.

**Negative:**

- **Sixteen ticked acceptance criteria on frozen specs assert that
  `docs/specs/README.md` carries their row** (for example
  `agent-skill-engineering-composition-floors` AC30,
  `workspace-journey-guides-and-planning-doctrine` AC13). Frozen bodies take only
  a `Status`-line edit, so they cannot be corrected in place. They were satisfied
  when they shipped; this ADR is the record that the surface they name has since
  been retired, and no further correction is owed.
- Two tests that assert a spec's own index row
  (`tools/test_guide_typed_asides.py`,
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`) lose
  their subject and must be re-pointed at the spec file itself.
- The curated Notes prose in the retired table — 152 cells over 500 characters,
  up to 3,200 — exists nowhere else and is not recoverable from any spec body. It
  is being dropped, not relocated. Git history retains it.
- A generator is a new maintained surface with a version-pinning obligation: a
  floating tool version makes `--check` fail on a correct index.
- Adopters need `python3` to run the generator, as they already do for
  `next-ordinal.py`. Absent it, the index simply is not generated — the failure
  is clean, not silent.
- RFC-0002 takes an erratum narrowing its `Manual` classification for the three
  index rows.
- Three pack seeds change, so `core` and `governance-extras` both take version
  bumps.

**Revisit if:** anything begins reading the spec corpus by index rather than by
directory — a published site route, an `llms.txt` entry, or an agent instruction
to consult it — or either generated flat table outgrows scanning, at which point
PEP 0's status-grouped shape is the established next step.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the generator's `--check` mode, wired into `build_gate_chain.py`,
  fails when a generated index diverges from its corpus; a separate assertion
  holds that `docs/specs/README.md` contains no table.
- **Owner:** the `build-check` gate. Adopters get the same script, agent-invoked,
  with no gate — the downgrade ADR-0006 already accepted.

## Alternatives considered

- **Generate the spec index, grouped by status (the PEP 0 shape).** Rejected
  against *does anything read it* — grouping optimises the legibility of an
  artifact with zero measured readers, and keeps a 444-row generated file
  churning in every branch. This was the leading option until the consumer sweep
  returned 216 writes and 0 reads.
- **Delete all three indexes.** Rejected against *does anything read it* — the
  ADR and RFC indexes have real consumers: `llms.txt` publishes both, the
  governance tutorial reads one, a roster test parses the other.
- **Keep all three hand-maintained and add a drift lint.** Rejected against *does
  it remove the write-contention* — a lint catches staleness while leaving 216
  write instructions and the conflict surface exactly as they are.
- **Keep the spec index and move its Notes prose to per-spec sibling files** (the
  towncrier pattern). Rejected against *does anything read it*: correct machinery
  aimed at an artifact nobody opens. The pattern stays available if the Revisit
  trigger fires.
- **A `.gitattributes` `merge=union` driver on the index files.** Rejected on
  correctness — union merge silently keeps both versions of a mutated row,
  producing a file that parses cleanly and is wrong; Git's own documentation says
  the result needs manual verification, and neither GitHub nor GitLab honours it
  in web merges.
- **Duplicate the generator into `tools/`.** Rejected against *one source of
  truth* — two copies drift, and `lint-spec-status.py` already demonstrates that
  the projection route works.

## References

- [`docs/product/research/document-index-patterns-survey.md`](../product/research/document-index-patterns-survey.md)
  — the applied prior-art survey: twelve confidence-rated findings across six
  proposal processes, five SDD frameworks, thirteen ADR tools, and four
  changelog-fragment tools.
- Consumer measurement: exhaustive sweep of all three indexes across the tree,
  2026-09-12. Recorded in this ADR's Context rather than a separate artifact.
- `tools/repo/build_gate_chain.py:255` — the skill-script-through-projection
  precedent this decision follows.
