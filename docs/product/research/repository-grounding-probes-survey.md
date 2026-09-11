# Mechanical probes for discovering the constraints on a change

> Discipline: applied (practitioner-pattern survey)

- **Commissioned:** 2026-09-10
- **Decision:** which cheap, script-level probes should a grounding step run
  before a spec or plan is authored, so the author discovers the repository's
  existing constraints rather than colliding with them at review?
- **Occasion:** one slice's pre-EXECUTE review sustained seven blockers across
  two rounds. Every one was the same shape — *this repository already has a rule
  you did not know about* — and none was reachable by reasoning about the
  artifact. Twenty-four earlier rounds of artifact-only review, on the same
  contract, produced one blocker.
- **Related:** [Code-graph review benchmark](../intents/code-graph-review-benchmark.md),
  which asks the adjacent question for *review* rather than authoring, and
  already holds the position that a repository graph is unproven. This survey
  supplies the authoring-side evidence for the same position.

## The pick

**Five probes, seeded by the paths a change will touch, all returning evidence
rather than verdicts.** Named by what they answer, not by how they are built:

| Probe | Question | Found, here |
| --- | --- | --- |
| Path references | which files name a seed path? | two roster modules pinning prose in the step being rewritten |
| Co-change | which files historically move with a seed path? | a second template file the convention had to cover, which no reference could reach |
| Gate reachability | what actually *runs* a seed path? | no required remote gate runs the suite five tasks close on |
| Content pins | which files quote a distinctive line from a seed file? | the discipline suite's exact-phrase pins |
| Scoped guidance | which governing files sit above a seed path? | the directory walk, already required elsewhere |

Three more are recommended and unbuilt; they are ranked in *What to build next*.

**Cost is the argument.** One review round on this material costs roughly 200,000
subagent tokens — a reviewer pass plus adjudication — followed by a repair cycle
and a re-review. The five probes together cost a few hundred tokens of output and
run in seconds, because they are seeded by the touched paths rather than by the
repository. `[high]` — measured on this repository's own rounds, not estimated.

**The reframing that matters is not "fewer findings" but "findings move to where
they are cheap."** A stale path reference costs nothing to find by search and
three orders of magnitude more to find by review. The finding count may even
rise, as it did here, because grounded review reaches further.

## Why not a repository map

Aider's repo map — tree-sitter across the repository, ranked by PageRank,
truncated to a token budget — is the best-known approach and the wrong shape for
this job. It is **global**: cost scales with repository size, and the truncation
drops exactly the rare edge the author needed. A grounding probe is
**seed-bounded**: it asks "what governs *these* paths", so its cost is
proportional to the seed set and its references. `[high]` — structural, and
independent of any measurement.

The benchmark literature is harsher than the tooling market. SWE-Explore finds
that BM25, TF-IDF and embedding retrieval "remain close to Random on most
metrics" for repository exploration, with agentic multi-step exploration a clear
step above. `[moderate]` — one systematic benchmark. A separate ablation over 17
real tasks found agent context files produced pass rates statistically
indistinguishable from no context files (p=1.00 and p=0.66 for two agents), with
the only measured benefit a narrow token-efficiency gain. `[moderate]` — small n,
three Python repositories, and it measures *correctness* rather than *constraint
discovery*, which is the claim made here.

That distinction is the honest limit of this survey: **no study measures whether
constraint-discovery probes improve authoring outcomes.** The case rests on the
cost arithmetic above and on one slice's defect history.

## Calibration is the difference between a probe and noise

Every probe here needed a cutoff before it was usable, and this is the most
transferable finding in the survey.

- **Content pins** returned 40+ false positives until any phrase appearing in
  more than three files was dropped. The matches were the shipped
  output-rendering block every skill carries. `[high]` — measured here.
- **Co-change** needs three literature-derived filters this repository's first
  implementation lacked: exclude commits touching more than ~30 files
  (formatting sweeps and dependency bumps carry high co-occurrence and zero
  coupling), require at least three co-occurrences, and report
  `co_changes / total_changes` as a confidence ratio rather than a raw count.
  Without them the top results here were `changelog.md` and `pack.toml` — true,
  and useless. `[moderate]` — consistent across several MSR sources, but the
  literature does not converge on universal thresholds, and the right values are
  repository-dependent.
- **Glob ownership** was built, measured and cut: bare `*` patterns matched
  twenty unrelated files and it never found a real owner. Recorded so its
  absence reads as a decision. `[high]` — measured here.

**A probe that floods its caller is worse than no probe**, because the real
finding sinks below the fold. Precision over recall is also how Cognition
describes training SWE-grep, whose reward weighted precision higher on the stated
grounds that context pollution is more harmful than a missed line. `[moderate]` —
vendor blog, no disclosed weighting.

## What to build next, ranked

Ranked by defects-it-would-have-caught over implementation cost, using this
repository's own recorded defect classes as the denominator.

1. **Live-reference and premise check.** Extract literal repository paths,
   anchors, versions and identifiers from a seed document; resolve existence, the
   current defining location, and whether the target changed after the referring
   record was written. This repository records nine distinct instances of a
   stale-premise defect — prose capturing a one-time inference about existence,
   ownership or blockage, later treated as live fact. Calibration is already
   recorded here: require a rooted path containing `/`, strip line and anchor
   locators, exclude placeholders, globs, braces and bare basenames. Hard-fail
   literal links only; report symbols and prose claims as suspects. `[high]`

2. **Authority and projection closure.** For each seed, return the role graph:
   authoritative source, generated mirrors, manifest and version surfaces,
   register and release surfaces, and the regeneration or check command. Eight
   recorded defects are a plan seeing the intended edit but not the
   source-to-projection or manifest-to-release closure around it. Require two
   signals before asserting a role — a generator edge plus a matching relative
   path, or a manifest declaration plus content parity — because phrase
   similarity alone is a hint. `[high]`

3. **Executable document-contract check.** Machine-consumed documents are parser
   interfaces, and four recorded defects come from treating them as free prose —
   in one case a task-heading pattern discovered only after the plan was
   hash-pinned. Take the direct consumers already found by the reference and
   reachability probes, extract their heading or section patterns, and where a
   parse-only mode exists, run it against the seed before any pin or transition.
   A hard result needs an actual parser rejection or a uniquely bound parser
   constant; anything else is informational. `[moderate]`

**Considered and not recommended.** A regex import graph: strong for code
(RefExpo reports 92% recall on Python), irrelevant where the seeds are prose
artifacts. Coverage-derived test impact analysis: the precision standard, but it
needs an instrumented baseline run and is not a stdlib script. Predictive test
selection: needs training data. Bazel reverse-dependency queries: not
seed-bounded without a scoped universe, and absent here. CODEOWNERS resolution:
valuable where the file exists; this repository has none.

## Anti-patterns, with the evidence

Five recorded here, each with a source. These are the ones to not rebuild.

- **Hand-maintained verification maps and trigger hashes.** A proposed gate
  inventory was rejected because *runs*, *reports* and *blocks* differ; hashing a
  workflow's `on:` block stayed green when job conditions, path filters, called
  workflows and commands changed.
- **Global prose-contradiction detection.** Five shipped guard defects, three
  introduced by the previous repair. The redesign abandoned global detection and
  narrowed to bounded regions.
- **Exact-phrase single-homing.** Misses unpinned sentences, paraphrases and
  repeated copies inside one file. Its proposed fingerprint successor explicitly
  cannot detect paraphrase either.
- **Source-substring control pins.** Two gates stayed green after the protected
  method was deleted. Textual presence was replaced by production-path
  observation and mutation.
- **Blocking on an uncalibrated predicate.** An emphasis-density rule would have
  blocked 405 of 1,477 files against a 0.4% budget, with precision never
  measured. The recorded conclusion is to advise until precision is known.

The shared lesson: **a probe reports; it never decides.** Blocking on a heuristic
is the consequence-bound blocking this repository built, measured and killed for
missing protected-class findings.

## Known unknowns

- **Known-unknown:** whether these probes reduce total review rounds. One clean
  pre-emption was observed — a defect caught by co-change before any reviewer saw
  it — which is an anecdote. Closing this needs several slices measured with the
  probes on and off.
- **Known-unknown:** the right co-change thresholds for this repository. The
  literature's values come from other projects' histories and the sources do not
  converge.
- **Unknowable, as posed:** whether an acceptance criterion is satisfiable or
  observable. Six recorded defects are unfalsifiable or one-sided criteria, and
  no deterministic probe decides this. Lexical detectors stay advisory here
  because, as this repository already measured, false positives dominate.
- **Unknowable:** whether a plan is over-specified. It depends on intent, not on
  repository state. After review begins a ledger query can compute
  prior-round-repairs over sustained findings, but that is a review-health
  signal, not grounding.

## Citations

**Benchmarks and studies.** [SWE-Explore: benchmarking how coding agents explore repositories](https://arxiv.org/html/2606.07297v1) · [Exploration structure in LLM agents for multi-file change localization](https://arxiv.org/html/2606.11976) · [Do context files help coding agents? A two-agent ablation](https://arxiv.org/html/2607.27250v1) · [Agent READMEs: an empirical study of context files](https://arxiv.org/html/2511.12884v1) · [Codified context: infrastructure for AI agents in a complex codebase](https://arxiv.org/html/2602.20478v1) · [RefExpo: dependency graph extraction](https://arxiv.org/pdf/2407.02620)

**Change coupling.** [Integrating conceptual and logical couplings for change impact analysis](https://link.springer.com/article/10.1007/s10664-012-9233-9) · [Is code co-committal an indicator of evolutionary coupling?](https://www.mdpi.com/2674-113X/5/1/11) · [Co-evolution of logical couplings and commits for defect estimation](https://www.researchgate.net/publication/254040767_Co-evolution_of_logical_couplings_and_commits_for_defect_estimation)

**Test impact analysis.** [The rise of test impact analysis (Fowler)](https://martinfowler.com/articles/rise-test-impact-analysis.html) · [Microsoft test impact analysis](https://devblogs.microsoft.com/devops/accelerated-continuous-testing-with-test-impact-analysis-part-1/) · [Meta predictive test selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/)

**Tooling.** [Cognition: SWE-grep](https://cognition.com/blog/swe-grep) · [Bazel query guide](https://bazel.build/query/guide) · [Turborepo `--affected` false positive](https://github.com/vercel/turborepo/issues/11144) · [SWE-agent AST exploration issue](https://github.com/SWE-agent/SWE-agent/issues/38)
