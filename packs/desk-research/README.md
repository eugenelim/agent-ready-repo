# desk-research

evidence-grounded desk research — portable across every repo.

---

## Start here

Type `desk-research` and describe what you're trying to find out.

```text
  ● evidence-retriever   running  DORA 2023 State of DevOps
  ✓ source-extractor     done     accelerate.io — 3 findings extracted
  ✓ synthesis            done     8 claims graded · 2 gaps named
```

On any session return, type `desk-research-project-status` to orient to an active project.

```text
  Project    2026-07-15-deployment-frequency
  Phase      digest
  Hypothesis  Trunk-based development is the primary predictor
  Next        desk-research-project-digest
```

---

## Entry points

| Say this | What happens |
|----------|--------------|
| `desk-research` | Single-session research — scoping, retrieval, synthesis in one pass |
| `source-map` | Map canonical sources before retrieval begins |
| `build-outline` | Build a research outline from the source map |
| `identify-perspectives` | Map stakeholder perspectives before synthesis |
| `compare-hypotheses` | Competing-hypotheses pipeline — scored matrix |
| `devils-advocate` | Steelman the opposing case |
| `decision-archaeology` | Reconstruct why a prior decision was made |
| `desk-research-project-start` | Initialize a sustained multi-week research project |
| `desk-research-project-status` | Orient to an active project — phase, hypothesis, what's next |
| `desk-research-project-check` | Snapshot progress — sources captured, coverage, gaps |
| `desk-research-project-digest` | Summarize corpus into a synthesis matrix |
| `desk-research-project-synthesize` | Synthesize digest into a confidence-graded brief |

`evidence-retriever` and `source-extractor` are read-only retrieval subagents dispatched automatically by `desk-research` — they are not invoked directly.

---

## How a session runs

```text
desk-research "What drives deployment frequency in platform engineering teams?"

  ● evidence-retriever   running  DORA 2023 State of DevOps
  ✓ source-extractor     done     accelerate.io — 3 findings extracted
  ● evidence-retriever   running  Google Cloud DevOps metrics
  ○ synthesis            idle
```

```text
desk-research-project-start "competitive landscape for platform tooling"

  project  docs/product/research/2026-07-27-platform-tooling/

  ├─ overview.md          phase: capture
  └─ sources/

  Question    Competitive landscape for platform tooling
  Hypothesis  (none yet — to be formed as evidence accumulates)
  Next        desk-research to fill sources/, then desk-research-project-digest
```

```text
desk-research-project-synthesize

  brief  platform-tooling-brief.md

  Bottom line:  Build-vs-buy splits sharply at team size 50; below that, buy dominates.

    Claim                                              Grade      Sources
    Team-size 50 as buy/build threshold               [high]      4 independent
    TCO advantage erodes above 200 engineers          [moderate]  3; downgrade: vendor-sourced
    OSS viable only with dedicated maintainer         [moderate]  3; downgrade: survivorship bias

  Known unknowns
    Known-unknown: data at 50–200 engineer range. Would close by: mid-size org survey.
```

---

## Cross-pack

**Downstream — `product-strategy`:** `synthesize-stakeholder-research` in the product-strategy pack consumes `desk-research` survey artifacts as a primary evidence source.

**Downstream — `architect`:** design decisions grounded in a `desk-research` brief carry a cited rationale chain that `architect-design` can reference in ADRs.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the [`desk-research` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/desk-research/).
