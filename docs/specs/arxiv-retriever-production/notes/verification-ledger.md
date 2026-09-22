# Verification ledger — arXiv retriever, production grade

Execution observations for `docs/specs/arxiv-retriever-production/spec.md`.
The plan is frozen; this file is where its execution evidence lands.

## T9 — live end-to-end pass (AC-0035)

Ran 2026-09-22 against the live arXiv API from the repository root, on
`eugenelim/arxiv-upgrade`. Every invocation is the shipped script, not a test
double. Command shown without the interpreter and script path.

| Case | Arguments | Exit | Observed |
| --- | --- | --- | --- |
| search, free text through the tier ladder | `instruction adherence in agent config files` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 10 citation(s), 18049 content chars. First line: `Query: tier 3 of 4; arXiv reported 97 matches.` |
| search, --title + --category | `--title attention is all you need --category cs.CL` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 10 citation(s), 13292 content chars. First line: `Query: fielded; arXiv reported 10 matches.` |
| search, --search-query raw passthrough | `--search-query ti:"attention is all you need" ANDNOT c` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 10 citation(s), 13964 content chars. First line: `Query: caller-composed; arXiv reported 28 matches.` |
| search, --author | `--author Vaswani --max-results 3` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 3 citation(s), 4100 content chars. First line: `Query: fielded; arXiv reported 159 matches.` |
| search, --abstract | `--abstract retrieval augmented generation --max-result` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 3 citation(s), 4879 content chars. First line: `Query: fielded; arXiv reported 5834 matches.` |
| search, --sort submitted | `--category cs.CL --sort submitted --max-results 3` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 3 citation(s), 5520 content chars. First line: `Query: fielded; arXiv reported 119681 matches.` |
| search, --from/--to date window | `--category cs.LG --from 202401010000 --to 202401020000` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 3 citation(s), 5287 content chars. First line: `Query: fielded; arXiv reported 47 matches.` |
| get, modern five-digit identifier | `--mode get 1706.03762` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 1427 content chars. First line: `# Attention Is All You Need` |
| get, modern four-digit identifier carrying a DOI | `--mode get 0710.4003` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 852 content chars. First line: `# YREC: The Yale Rotating Stellar Evolution Code` |
| get, legacy slashed identifier via an abs URL | `--mode get https://arxiv.org/abs/quant-ph/0201082` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 562 content chars. First line: `# Quantum Computers and Quantum Computer Languages: Quantum Assemb` |
| get, --full-text at the default budget | `--mode get 1706.03762 --full-text` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 5878 content chars. First line: `# Attention Is All You Need` |
| get, --full-text --sections conclusion | `--mode get 1706.03762 --full-text --sections conclusio` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 2765 content chars. First line: `# Attention Is All You Need` |
| get, malformed identifier refuses | `--mode get 1706.0376x` | 2 | stderr `arxiv-retriever: '1706.0376x' is not a well-formed arXiv identifier`; stdout empty: True |
| enrich | `--mode enrich 1706.03762` | 0 | keys=['citations', 'content', 'shape'], shape=raw, 1 citation(s), 451 content chars. First line: `# Attention Is All You Need` |

**What this establishes.** All three modes answer over the live API. The
free-text case selects tier 3 of 4 and reports it, with 97 matches and the
correct paper first — the same query the previous retriever sent as
`all:instruction adherence in agent config files`, which matched 124,103 papers
with an unrelated top hit. Every successful result carries exactly the three
contracted keys with `shape: raw`. The malformed identifier exits non-zero with
a diagnostic on stderr and nothing on stdout, so a caller parsing stdout cannot
read a refusal as a result.

**Session boundary.** This session verifies the three modes and every documented
search-control flag end to end, and stops there. It does not exercise the retry,
throttle, byte, elapsed-budget, redirect, resolved-address or parser-refusal
paths: those are driven by the unit cases in
`packs/desk-research/tests/skills/desk-research/test_research_retrievers_conformance.py`
against injected seams, because provoking them against the live service is
neither reliable nor courteous.

## Mutation evidence

Each control added for a sustained review finding was checked by reverting the
fix and confirming the suite fails. All of the following failed when reverted,
so none is a control that cannot fail:

| Reverted control | Result |
| --- | --- |
| quote stripped from every query literal | suite fails |
| accepted-keyword filter on the search branch | suite fails |
| empty-page retry wired at all three call sites | suite fails |
| whole-document doctype scan (vs a 4 KiB prefix) | suite fails |
| named-section selection without a widen-to-everything fallback | suite fails |
| full-text ceiling clamped against a caller override | suite fails |
| cap measured over the serialized result, not `content` alone | suite fails |
| query-term de-duplication | suite fails |
| returned entry matched against the requested identifier | suite fails |
| budget checked before resolution | suite fails |
| budget checked after resolution | suite fails |
| redirect target re-checked by its own guard | suite fails |
| `URLError`-wrapped timeout mapped to the limit error | suite fails |
| bare timeout mapped to the limit error | suite fails |

## Suites and gates

| Gate | Result |
| --- | --- |
| `make lint-ruff` | clean |
| `make lint-mypy` | clean, 148 source files |
| `tests/skills/desk-research/` (floor 9) | 71 passed |
| `tests/skills/desk-research-project-start/` (floor 7) | 8 passed |
| `tests/pack/` + five project suites + devils-advocate, `--import-mode=importlib` | 17 passed |
| `agentbundle catalogue lint --deep` | no errors |
| `agentbundle catalogue verify` | no drift |

The third pack suite needs `--import-mode=importlib`: six suites ship a file
named `test_project_knowledge_boundary.py`, and without that mode collection
fails on the basename collision. The Makefile passes it; a hand-run invocation
that omits it reports four collection errors that are not defects.

## Review lanes and their results

Every reviewer ran as an isolated `codex exec` session over a supplied evidence
packet, read-only, with the role definition inlined because `codex exec` cannot
dispatch a projected agent. Raw reports and paired adjudications are retained
under the session's ignored `.context/reviews/` path.

### Spec stage

| Round | Reviewer | Findings | Disposition |
| --- | --- | --- | --- |
| shaping | shaping-reviewer, spec mode | 1 High | sustained; obligations retargeted to cite their owning clauses |
| 1 | adversarial-reviewer | 12 (9 blocker, 3 concern) | 6 sustained, 1 refuted, 5 owner-directed after an indeterminate |
| 2 | adversarial-reviewer, delta | 7 | 6 adjudicated, 1 refuted |
| 3 | adversarial-reviewer, delta | 0 | byte-exact `Clean — ready to commit.` |
| secure-design | security-reviewer, spec stage | 1 blocker, 4 concern | 4 sustained, archive blocker refuted on reachability |
| 4 | adversarial + security, paired | 12 | applied; AC-0042 narrowed to its reachable claim |
| 5 | adversarial-reviewer, delta | 8 | applied; two corrected author errors |
| 6 | adversarial-reviewer, delta | 5 | applied |
| 7 | adversarial-reviewer, delta | 1 | applied |
| 8 | adversarial-reviewer, delta | 0 | byte-exact clean |
| secure-design, round 3 | security-reviewer, delta | clean with a `## Not checked` footer | adjudicated clean; all three footer items refuted |

Round 5's most consequential finding corrected this author rather than the
code: the identifier grammar had excluded four-digit modern identifiers, which
would have rejected `0710.4003` — the very record used to verify DOI handling.

### Implementation stage

| Reviewer | Findings | Disposition |
| --- | --- | --- |
| adversarial-reviewer, diff | 13 (10 blocker, 3 concern) | see below |
| security-reviewer, diff | 6 (1 blocker, 5 concern) | see below |

Both lanes independently converged on one root cause: network-security criteria
written without first establishing what `urllib` enforces. Two defects they
found were severe and had passed an earlier live pass that exercised only four
invocations: every fielded flag raised `TypeError` before sending a request,
and a caller's double quote escaped the phrase literal into live arXiv boolean
syntax — the same defect class this delivery exists to remove.

### Security re-review on the delta

| Finding | Disposition |
| --- | --- |
| Structured flags still permitted query-language injection: a category such as `cs.CL OR ti:attention`, and interpolated date bounds | sustained. Category and date bounds now match declared value grammars and are refused otherwise; only the raw passthrough carries arXiv syntax |
| DNS resolution remained outside the enforceable deadline, because `getaddrinfo` takes no timeout and bracketing it cannot bound it | sustained. Resolution runs on a daemon thread the caller stops waiting on, following the bounded resolver in the repository's credential broker |
| The captured fixtures committed real author names and contact addresses, against the repository's prohibition on personal information in fixtures | sustained. See below |

The fixtures took three attempts and each failure taught something:

1. Sections were regex-extracted non-greedily, which truncated every section
   containing a subsection and left unbalanced markup. The section-count oracle
   caught it: the parser reported 3 of 8.
2. Whole real documents fixed the structure but carried ten real email
   addresses and author names, which the security lane caught.
3. Sanitising a real paper's prose is not winnable — a paper's body cites real
   people. The fixtures are now arXiv's own structural skeleton: every tag,
   class and nesting level as arXiv emits it, section headings kept because
   name-based selection is what they exercise, and every other text node
   replaced. No name or address remains, and the oracle still holds at 8 of 8
   and 5 of 5.

Refusing a category or a date bound also escaped `main()` as a traceback, the
same class as the earlier `TypeError`: a caller-input error is now a message
and exit code 2 with nothing on stdout.

## Accepted residuals

Two findings are accepted as proportionate rather than repaired, because each
repair would require a controlled amendment and fresh approval of a frozen plan
to correct a rationale clause that binds no check:

- The plan's declined-additions rationale says the LaTeXML and LaTeX-source
  routes satisfy the outcome, while the spec states that nothing in this
  release reads the LaTeX source archive. The spec governs, and no criterion or
  task reads that archive; the security finding about archive confinement was
  refuted on exactly that reachability ground.
- The plan repeats the literal version `1.1.9` that AC-0027 owns. The two agree
  today, and AC-0027 is the checked home.

## Known limits carried into the release

- Resolved-address checking is a preflight refusal and does not close DNS
  rebinding. `urllib` connects by hostname with no way to pin the connection to
  the address that passed, and pinning would mean replacing it with a
  hand-built HTTPS client. The same limit is recorded at
  `packages/credbroker/credbroker/_sso.py`.
- The 3.0s inter-request interval is adopted from the reference client's
  default, not measured against a failure threshold: the HTTP 429 that
  motivated it did not reproduce across eight probes. It is the first value to
  raise if 429s recur.
- Tier selection's 2,000-match ceiling is a judgement calibrated on six
  measured queries. A caller wanting broader recall uses the raw passthrough.
