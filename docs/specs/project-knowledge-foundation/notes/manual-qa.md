# Manual QA — project knowledge foundation

Date: 2026-08-15

## Explicit enquiry CLI

The built `project_knowledge.py --enquire` CLI was exercised in a disposable
Git repository by
`test_enquiry_cli_returns_receipt_without_journal_or_worktree_bodies`. The
fixture committed one coherent topic/map snapshot, then changed the working
tree topic before invoking the CLI with a strict JSON query on stdin.

Observed result:

- exit status `0`;
- receipt selected `contracts/public-contracts` from the committed snapshot;
- rendered evidence excluded the working-tree-only body;
- receipt exposed no mutation path and the enquiry opened no journals.

## Consequential abstention

The same built path was exercised with a consequential query whose committed
topic named a missing owning source. The result was a bounded evidence envelope
with `abstained: true`, an empty selected-topic list, and no topic body. The
receipt retained the resolved commit and risk classification so the abstention
is attributable without disclosing candidate observations.

Verification command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  packs/core/tests/skills/project-knowledge/test_enquiry.py \
  -q -p no:cacheprovider
```

Result: covered by the final combined `179 passed` suite recorded below.

## Work-loop public capture seam

The projected work-loop skill was checked for the T7 handoff journey with core
present and absent.

Observed result:

- the closeout question bytes remain pinned to the core 2.5.9 text;
- capture uses the public `project-knowledge --capture` seam after semantic
  gate triage;
- terminal distillation uses `project-knowledge --distill` with
  `selection_mode: workflow-receipts` and only that gate's capture receipts;
- unresolved observations remain pending and do not invalidate capture;
- missing core is the named skip `project-knowledge unavailable` and creates no
  fallback file.

Verification command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  packs/core/tests/skills/work-loop/test_project_knowledge_handoff.py \
  -q
```

Result: covered by the final combined `179 passed` suite recorded below.

## Complete disposable-repository journey

`test_ac34_disposable_repository_foundation_journey` exercises the foundation
as one connected flow in an isolated Git repository. It verifies legacy
migration and activation, semantic-gate-shaped capture, byte-idempotent replay,
terminal promotion and rejection, topic/map publication, committed-only
`CQ-VERIFY` enquiry, source-drift abstention, retirement after contract
enforcement, and exact interruption recovery.

Negative evidence in the same journey proves that enquiry excludes observation
journals, rejected bodies, and a working-tree-only topic edit. The test also
found and fixed a lifecycle validation defect: committed retired map entries
must validate as `retired` before the enquiry filter can exclude them.

`test_ac33_closed_partitions_are_immutable_and_have_no_event_deletion_api`
then writes a later monthly partition and terminal disposition while pinning an
earlier partition's exact bytes. The earlier bytes remain identical, and the
runtime exposes no retention, compaction, per-event deletion, or partition
deletion command. Whole-partition retention remains deferred.

Result: `2 passed` for the two delivery goal tests; `179 passed` for the final
combined project-knowledge, work-loop handoff, legacy shim, and contract-parity
suite.

## Delivery and privacy checks

- Private comparison-name scan of all changed and new implementation bytes:
  **pass**. Only the result is recorded.
- Core version authorities: **pass**, aligned at `2.6.0` for the new primitive.
- AgentBundle public-contract version authorities: **pass**, aligned at
  `0.35.4` with matching package changelog and package README.
- Public source/bundled schema parity: **pass**, 13 contracts byte-identical.
- Progressive skill roster, activation/near-miss evals, and semantic-judge
  distillation/enquiry evals: **pass**.
- Self-hosted `.agents` and `.claude` projections: **pass** after forced
  dirty-tree regeneration; source/projection bytes match.
- Catalogue verification, build/policy gates, and Bandit: **pass**. The chained
  dependency audit was attempted once in the default environment and once with
  its temporary files confined to the approved temp root; both attempts were
  environment-blocked because this Python installation cannot run `ensurepip`
  in a fresh virtual environment. No dependency or audit bypass was added.
- Ruff and mypy: **pass**.
- Architecture/adversarial review: **clean**.
- Security review: **clean**.
- Quality review: **clean**.

The workspace cannot commit or update Git refs, so delivery stops at the
approval boundary.
