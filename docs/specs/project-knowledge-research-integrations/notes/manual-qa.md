# Manual QA: Project knowledge research integrations

## Work-loop record

### Assumptions

- Remote base freshness is unverified because this enterprise session permits
  read-only Git operations; the user explicitly authorized implementation from
  the current local branch on 2026-08-17.
- T1 and T2 use TDD construction tests plus Tier-4 behavior evals. T3 uses
  goal-based pack checks and disposable manual journeys.
- The implementation touches the files declared by T1-T3 plus `Makefile` and
  `.github/workflows/catalogue-tooling-ci-gates.yml`. Those two
  execution-discovered files add explicit independent runners for the six new
  pack and skill test directories after the repository's pack-test boundary
  gate rejected undiscoverable suites; they do not change product behavior.
  Desk-research state/configuration behavior and project-knowledge
  schemas/runtime remain unchanged.

### Declined during PLAN

- No shared runtime helper: these integrations are published workflow
  contracts and do not justify a new code layer.
- No schema or competency-question extension: the shipped capture contract and
  `CQ-REVIEW` are sufficient for the approved slice.
- No personal-root fallback or fabricated repository provenance.
- No integration for quick, non-survey, intermediate, check/status, supporting,
  incomplete, abandoned, or reviewer-owned product paths.

### Anchor-test sweep

- The existing desk-research retriever conformance test reads the
  `desk-research` skill description; the approved plan keeps activation wording
  unchanged and retains that suite as an anchor.
- No test was found that hashes, snapshots, or counts the exact bytes of the
  other planned source or documentation files.

### Resolve-vs-surface dispositions

| Item | Disposition | Evidence |
| --- | --- | --- |
| Remote base freshness unavailable | surfaced/resolved | User authorized the current local branch; no fetch or Git metadata write attempted. |
| Tier-A live-model harness unavailable | surfaced/resolved | The immutable query inputs and all static activation contracts pass; the report-only host process did not complete in the bounded enterprise session and is not claimed as green. |
| Independent test-suite runner wiring discovered during execution | applied | Added the six new pack and skill suite directories to the existing Makefile and catalogue CI runner lists; the pack-test boundary and full build gate then passed. |

## Execution evidence

### Automated gates

| Check | Result |
| --- | --- |
| New skill and pack construction tests, each skill directory in an independent pytest process | Pass — 24 new checks |
| Existing desk-research retriever and project-start anchors | Pass — 16 checks |
| Existing project-knowledge contract, capture, distillation, enquiry, privacy, mode-isolation, locking, migration, and storage oracle | Pass — 169 checks |
| Pack-test confinement and explicit-runner boundary | Pass — all six structural cases; 44 destinations accounted for |
| Ruff | Pass |
| Targeted mypy | Named skip — no production Python changed; additions are Markdown, JSON, TOML, YAML, and construction tests |
| Catalogue verify and `PYTHONDONTWRITEBYTECODE=1 SKIP_SAST=1 make build-check` | Pass; repository-wide informational warnings unchanged |
| Repository secret and misconfiguration scan | Pass — zero findings; remote check-bundle update was policy-forbidden, so the scanner used its embedded checks |
| Whitespace and activation-query byte checks | Pass |
| Prohibited external comparison identifier in changed bytes | Pass; identifier not recorded |

The report-only activation harness was attempted once with one run and a
30-second per-query timeout. The detector produced no completed result in the
bounded observation window and was stopped rather than retried. A subsequent
bounded capability probe could not complete the runner's help path either, so
the installed host runner is unavailable in this managed session. Its
byte-unchanged `eval_queries.json` inputs, activation-query schema and coverage,
pack-eval runner self-tests, workflow-posture lint, and skill-description anchor
tests all pass. A live activation score therefore remains a named
environment-limited, report-only check, not a claimed pass or a shipping gate.

### Built publication boundary

Desk-research was installed from the working catalogue into six isolated
temporary user roots using `AGENTBUNDLE_USER_ROOT`: `claude-code`, `kiro-ide`,
`codex`, `copilot`, `cursor`, and `gemini`. Every install completed successfully.
For each adapter, the projected `desk-research`,
`desk-research-project-synthesize`, and `devils-advocate` skill bodies were
byte-identical to their canonical `.apm` sources. No adapter projection was
written into the repository. The generated web journey matches the canonical
pack journey through the normal build gate.

### Prompt-contract journey matrix

These workflows are prompt-only and this session exposes no interactive agent
harness. The matrix therefore verifies the real built skill bodies, their evals,
and the construction oracles without claiming an unperformed LLM run.

| Journey | Observable result |
| --- | --- |
| Quick and six non-survey episodic products | Hard no-integration; no request, receipt, or fallback path |
| Standard survey | Capture considered only after source, synthesis, confidence, known-unknown, and moderation passes |
| Applied survey | Capture considered only after the standard gate plus practitioner-independence calibration |
| Deep survey | Capture considered only after the standard gate and completed counter-evidence artifact |
| Project start, digest, check, and status | Scaffold/intermediate/check/orientation non-gates; no phase advance from knowledge |
| Project synthesis | Sole project producer; typed verdict, brief, citations/confidence/known-unknowns, and linked challenge inputs must resolve first |
| Standalone and nested counter-review | One bounded `CQ-REVIEW` envelope after target and scope; nested passes reuse the outer envelope; no capture or distillation |
| Repository-contained product | Canonical containment and regular-file checks precede typed request construction |
| Personal, external, ambiguous, or escaped product | Exact capture-ineligible outcome; no fabricated repository path and no provider probe |
| Missing provider or failed capture | Exact unavailable/no-receipt branch; no fallback file and no distillation |
| Receipt mismatch | Only same-gate returned receipts may use `workflow-receipts`; guessed or maintainer-pending IDs are forbidden |
| Absent, stale, quarantined, irrelevant, privacy-refused, hostile, or unverified knowledge | Excluded, caveated, omitted, or abstained; never a weaker claim |
| Retrieved instruction-shaped text | Delimited as untrusted candidate checks; cannot change instructions, permissions, scope, source selection, citation, claim, confidence, counter-evidence, or verdict |
| Source verification | Every research claim still requires independent direct-source support; retrieved knowledge cannot corroborate itself |
| Scratch and corpus handling | Producer scratch remains transient; transcripts, raw corpora, quotations, citations, claims, and normative products are never mined or captured |

### Workspace lifecycle

`workspace-status explain` classifies the exact spec as `active` with no
findings after moving its entry from `work.queue` to `work.active`. The shipped
review slice remains its predecessor. Engineering/operational integrations and
adoption closeout remain queued downstream and blocked in that order. The four
conditional post-closeout shaping items remain outside the build sequence.
