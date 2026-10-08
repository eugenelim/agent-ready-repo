# Plan: Graph well-formed authoring

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)
- **Constrained by:** RFC-0103; ADR-0007; ADR-0074
- **Repository anchors:** `ARCHITECTURE.md` owns pack-source boundaries; work-loop's `scripts/lint-spec-status.py` is the portable-linter precedent; `tools/repo/build_gate_chain.py` owns repository CI invocation; the grammar migration's surface inventory owns writer discovery.
- **Retention:** repository-durable spec and plan; fingerprints recorded at approval. Required readers are implementers, reviewers, resuming agents, and CI. Guides, source tests, and the release entry own current truth after closeout.

## Constraints

- One slice PR targets the default branch. T1–T3 are ordered commits within it, not separate PRs.
- Spec authoring starts at the prerequisite brief branch's head while its PR is unmerged. Build starts only after rebasing onto current `main` with those prerequisites present.
- No commit or push occurs without owner approval. Do not use bare `git stash`.
- Run only a task's own tests at its completion. Run `make lint-ruff lint-mypy` and the combined targeted suites before final review; dispatch full gates once on the slice PR.
- Expected review shape: DEEP for the check and invocation wiring; WIDE for inventory-driven authoring edits. Each task has its own proof, and all remain one bounded slice PR.

## Durable-output map

| Output | Task |
| --- | --- |
| Shared check and construction suite | T1 |
| Writer gaps, template and example meaning, field guide and contract guide | T2 |
| Portable invocation, repository gate, versions, release entry, projections, ledger | T3 |

## Design (LLD)

### Ownership and selection

**Owned by:** T1, T3

`packs/core/.apm/skills/work-loop/scripts/lint-graph-pointers.py` is the single shared check. Slice 5 creates its `Parent intent` and `Brief` rules; slice 7 adds a field rule to that source. If slice 7 has already created the source at landing time, reuse it and add only these two rules. There is no dependency on navigator delivery.

The script uses only the standard library and the existing co-located `_file_safety.py`. The adapter-root confinement source and its copy pin own that helper. The check adds no helper copy or adapter-root command.

The CLI takes `--root` and `--base-ref`. Git diff against that base supplies committed, index, and worktree changes; untracked artifact additions are included separately. NUL-delimited path records prevent filename text from becoming command syntax. Selection cannot silently return an empty change set when Git or the base is unavailable. Target inventory reads canonical intent and brief collections through the helper; it does not validate untouched artifacts' pointer values.

The node index stores typed intent and brief identities. It applies RFC-0103 D2's kind rule and `Slug:` identity without global suffix matching. Duplicate identities remain unresolved rather than being overwritten. This is local authoring validation; no parity check or change to another reader is part of it.

Source code, CLI help, and construction tests own selection and field dispatch after delivery. The field guide owns authoring versus legacy-reading behavior.

### Writer discovery

**Owned by:** T2

The shipped grammar migration's `notes/derive-surfaces.py` and `surface-inventory.md` establish source-surface classification. The bounded candidate universe is current Markdown under `packs/core/`, `packs/product-engineering/`, `docs/guides/`, and `guides/` that stamps either governed preamble header or mentions `Parent intent:` or `Brief:` in authoring instructions. Include shipped seeds and examples. Exclude test, fixture, eval, build, dependency, cache, and repository-metadata directories; artifact instances and decision records are not writers. Identify generated copies by the existing derivation's source/digest grouping and verify their projection through T3 rather than editing them.

Record every matching candidate with its authoring region and instruction, template, example, generated-copy, or excluded role. Give each exclusion its reason. An unclassified match or a source that still stamps or instructs an untyped populated governed field fails T2. Pin the complete candidate set and classification as well as each changed source's typed emission; do not copy historical counts. The discovery predicate is an author-facing surface that still stamps or instructs an untyped populated value. Kill condition: a gap needs a reader change, new grammar rule, or work outside these two fields; stop and bring that decision to the owner.

The seeded brief template and `author-delivery-brief/examples/shape-a-outcome-brief.md` already emit typed values. Their remaining change is the parent-meaning comment. They are not writer-form migrations.

### User-documentation draft

**Owned by:** T2

For the field guide: “Write a brief's `Parent intent:` as the target intent's registered kind and `Slug:`, such as `outcome:service-reliability` or `intent:account-self-service`. Write a spec's `Brief:` as `brief:<slug>`. New and changed artifacts are checked; readers keep accepting legacy repository paths in untouched artifacts. An absent value or a value beginning with the word `none` records no pointer.”

For the contract guide: “Before completing a change, the work-loop checks all active `Parent intent:` and `Brief:` fields in each artifact the change adds or modifies. A typed pointer must name an existing target of the field's type. A body-only edit still selects that artifact for checking.”

## Tasks

### T1: Changed-artifact pointer fixtures pass

**Depends on:** none

**Verification mode:** TDD

**Tests:**
- **VI-1001.** New suite `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py` drives the production CLI in disposable Git repositories, with an explicit base and separately created committed, staged, unstaged, untracked, renamed, deleted, and untouched files (AC-0001, AC-0002).
- **VI-1002.** The same suite compares exit codes and parsed diagnostics over typed, wrong-kind, missing, retired, and duplicate targets; selected-artifact `Parent intent:` values expressed as a bare slug, repository path, markdown link, or malformed typed reference; untyped and malformed `Brief:` values; repeated active fields; absent/blank/comment-only fields; leading `none`; and body/comment decoys (AC-0003, AC-0004, AC-0005, AC-0006, AC-0008, AC-0011).
- **VI-1003.** Boundary fixtures cover unavailable bases, unsafe corpus entries and reads, invalid UTF-8, a no-change repository, diagnostic sanitization, and a repository-byte snapshot before and after invocation (AC-0007, AC-0011, AC-0012).

**Approach:** The callable seam is implementation-discovered; `no stub (implementation-discovered)`. Begin with the observable CLI contract. Stop if confined selection or target reads require changing the existing helper contract.

**Done when:** T1 cases in the new suite pass. Record their count and runtime in the ledger.

### T2: Authoring sources and guidance agree on typed emission

**Depends on:** T1

**Verification mode:** goal-based check

**Tests:**
- **VI-2001.** Re-derive the complete bounded two-field candidate universe and classify every match using the design above. New construction pins in `test_graph_pointer_authoring.py` under the owning Core work-loop test directory fail on a missing or unclassified candidate and any remaining untyped populated writer or instruction. Record the candidate/classification manifest and remaining-gap result in the ledger; inspect each changed instruction, template, and example in its authoring region (AC-0009).
- **VI-2002.** Content pins cover the two parent-meaning comments and the guide passages drafted above. Run `tools/validate_guides.py`, `tools/lint-guide-titles.py`, and `tools/lint-guides-no-repo-only-refs.py` for the edited guide surface. These prove guide structure and portable references, not reader behavior (AC-0009; Durable Outputs).

**Approach:** Apply only inventory-proven gaps. If product-engineering source changes, its version and plugin version also change in T3.

**Done when:** T2 construction pins and the named guide checks pass.

### T3: Shipped and repository invocation paths reject a bad pointer

**Depends on:** T1, T2

**Verification mode:** goal-based integration

**Tests:**
- **VI-3001.** Project Core through the supported self-host path and invoke the projected check on T1's invalid-pointer fixture. Invocation pins cover the work-loop finish step and registration in `tools/repo/build_gate_chain.py`; extend that gate's existing construction tests where its registration changes (AC-0010).
- **VI-3002.** Every pack whose shipped source changes has a bumped, matching pack/plugin version pair, including product-engineering when T2 changes its sources, and the changelog contains a free-standing release entry with outcome-led Highlights. Run `agentbundle catalogue self-host --root . --write`, then `agentbundle catalogue verify --root .`, using live worktree source. Scan changed shipped pack text with the portable-citation grep from `packs/AGENTS.local.md` (AC-0010; Durable Outputs).

**Done when:** T3 integration and release checks pass, including the version pair for every changed pack, with evidence in the ledger.

## Slice verification

Run the required local lint gate and the affected targeted suites once before final review. Dispatch the full gates once on the slice PR, and record their run identifiers and results in the ledger. Do not run `make ci` as a push precheck. This slice-level evidence is separate from each task's own completion tests.

## Rollout

The check ships in a Core patch release and the slice PR merges straight to the default branch. The other slice adds its field rule to this source when it lands. Rollback reverts this slice's source, invocation wiring, and release changes; no stored index or corpus migration exists.

## Risks

- Whole-artifact selection can expose a legacy pointer during an unrelated body edit. The forward-only contract requires correcting that selected artifact; it does not widen the sweep.
- A writer search can confuse generic parsers or generated copies with authors. Role labels and source ownership bound the changes.
- Slice branch creation and the pre-build rebase require Git metadata write access.

## Changelog

- 2026-10-08: spec and plan approved together by the repository owner, conditional on the final alignment check passing; that check passed with zero findings across both slices. Shaping round 2 and adversarial round 2 are clean; reports are under `.context/reviews/a6209001-f5a1-4c22-8754-a1108e54f566/`.
- Approved reviewed revisions, before lifecycle-only approval annotations: spec SHA-256 `007228d76b69d0a9464dc39b92b6048fff2ce24e35ff29e1f6bd34268019c37e`; plan SHA-256 `40aa55052e37d72f574fd3863a040f9564f54b3fa639dd1be7c48d941322c1b1`.
