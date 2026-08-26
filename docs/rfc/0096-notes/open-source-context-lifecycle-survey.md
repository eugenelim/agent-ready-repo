# Open-source context lifecycle survey

> Discipline: applied (practitioner-pattern survey)

## Scope

This survey asks how mature open-source projects keep repositories useful after
delivery: which intent, design, documentation, release, and test records persist;
which delivery fragments are consolidated and removed; and whether tests alone are
treated as sufficient residual evidence. It samples primary process and repository
sources from Kubernetes, Python/CPython, Rust, Git, Twisted, and pytest. It does not
rank overall project quality or claim that one project's governance transfers
unchanged to another.

## Findings

- **Substantial decisions earn durable records; routine delivery does not.**
  Kubernetes requires KEPs for most non-trivial changes and keeps rejected work as
  history; Python uses PEPs for major features and durable design decisions; Rust
  reserves RFCs for substantial changes while ordinary fixes and documentation use
  the pull-request path. The convergent pattern is thresholded persistence rather
  than either "archive every task" or "code is the only record." **[high]**
  Sources: [Kubernetes KEP process](https://github.com/kubernetes/enhancements/blob/master/keps/sig-architecture/0000-kep-process/README.md),
  [Python PEP 1](https://peps.python.org/pep-0001/),
  [Rust RFC process](https://rust-lang.github.io/rfcs/).

- **Historical rationale and current truth have different owners.** Python treats
  resolved PEPs as historical documents and directs current behavioral truth to the
  language/library references or PyPA specifications. Rust requires language and
  public-library features to reach user/reference documentation before stabilization
  because RFCs and discussion threads are poor user-facing current documentation.
  Kubernetes requires feature documentation in the website repository for release
  and may remove an enhancement from a milestone when required docs are absent.
  **[high]**
  Sources: [Python PEP maintenance](https://peps.python.org/pep-0001/#pep-maintenance),
  [Rust RFC 1636](https://rust-lang.github.io/rfcs/1636-document_all_features.html),
  [Kubernetes feature documentation](https://kubernetes.io/docs/contribute/new-content/new-features/).

- **Tests are linked capability evidence, not a substitute for intent or user
  meaning.** Kubernetes KEPs keep goals, non-goals, design, risks, graduation
  criteria, and linked e2e stability evidence together; the test links do not replace
  the other sections. Rust's compiler test guidance asks tests to document their
  intent and link relevant issues or discussions so a future contributor can
  understand a failure. CPython's contribution process separately expects tests,
  documentation, NEWS entries, and—when user-significant—What's New content.
  **[high]**
  Sources: [Kubernetes KEP template](https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md),
  [Rust compiler test guidance](https://rustc-dev-guide.rust-lang.org/tests/best-practices.html),
  [CPython pull-request lifecycle](https://devguide.python.org/getting-started/pull-request-lifecycle/).

- **Extract-then-delete is established for merge-conflict-prone delivery
  fragments.** CPython creates one `Misc/NEWS.d/next` fragment per change and
  consolidates those fragments into a versioned release record; Twisted aggregates
  per-change fragments into `NEWS.rst` and explicitly removes the fragments during
  release; pytest requires per-change changelog fragments and publishes a consolidated
  changelog. This supports deleting a temporary coordination unit only after its
  durable destination has been produced and checked. **[moderate]**
  Downgrade: `heterogeneity` — CPython uses `blurb`, while Twisted and pytest use
  towncrier-family flows and pytest's contributor page does not itself spell out the
  deletion step.
  Sources: [CPython blurb](https://github.com/python/blurb),
  [Twisted release process](https://docs.twisted.org/en/twisted-20.3.0/core/development/policy/release-process.html),
  [pytest contributing guide](https://docs.pytest.org/en/stable/contributing.html).

- **Auditability is layered across stable IDs, status, links, history, and current
  owners.** Kubernetes KEP metadata, tracking issues, implementation history, and
  test/documentation links preserve chain of custody; Python PEP numbers, statuses,
  resolution links, supersession fields, and Git history preserve proposal history;
  Git's own review guidance requires commit messages to fully explain the code change
  in addition to reviewing the diff and tests. No single layer is treated as the
  complete audit record. **[high]**
  Sources: [Kubernetes KEP process](https://github.com/kubernetes/enhancements/blob/master/keps/sig-architecture/0000-kep-process/README.md),
  [Python PEP 1](https://peps.python.org/pep-0001/),
  [Git reviewing guidelines](https://git-scm.com/docs/ReviewingGuidelines).

- **Synthesis: pruning is safest when it removes a delivery container, not the last
  copy of a semantic fact.** Across the sampled projects, durable rationale, current
  documentation, release history, and tests occupy different surfaces. Temporary
  fragments are removed only after consolidation; historical proposals are retained
  when they remain the decision record; and current behavioral documentation is not
  delegated to old proposals or tests. **[high]**
  Sources: the five convergent findings above. `[synthesis]`

## Implications for RFC-0096 Wave 4

- A spec's up-front durable-output plan is the extraction manifest: semantic role,
  destination, owner, expected evidence, and closeout condition.
- Shaping must read applicable current owners as complete human-facing surfaces,
  not mine isolated snippets; otherwise the new contract can inherit stale context
  even when it names the right files.
- `close-work` verifies the final destination after implementation, including
  findings that changed the solution, and serves as a second whole-surface audit
  rather than trusting the planning-time promise or a mechanical touch.
- Tests and implementation remain residual capability evidence, but cannot discharge
  non-code obligations for product intent, rationale, user documentation,
  architecture, interfaces, operations, ownership, or authority.
- A temporary artifact is disposable only when each lasting fact has an owning
  durable surface or the whole artifact is explicitly reclassified/retained.
- Proposal lineage can itself be a durable navigation/history anchor: an RFC and
  its implementation waves may remain useful as a coherent family even after live
  workspace coordination is compacted. Initiative membership alone is weaker
  evidence because it describes scheduling/coordination, not semantic lineage.
- The RFC's exact, drift-sensitive deletion confirmation is stricter than the sampled
  release-fragment tools and is warranted because Wave 4 disposes arbitrary delivery
  artifacts rather than one tool-owned fragment class.

## Known unknowns

- **Known-unknown:** Whether retaining every accepted KEP/RFC/PEP produces a measurable
  orientation cost compared with extracting and retiring delivery records. Would be
  closed by: repository-specific search/context telemetry and maintainer studies that
  compare retrieval quality and upkeep cost over time.
- **Known-unknown:** How often release-fragment deletion loses information that should
  have reached user documentation or rationale records. Would be closed by: incident
  reviews or audits comparing deleted fragments with released documentation.
- **Known-unknown:** Which projects safely prune substantial design documents after
  extracting their content, rather than retaining them as frozen history. Would be
  closed by: explicit primary-source retention policies and worked deletion audits;
  the sampled proposal systems mostly retain substantial decisions.
- **Unknowable:** Whether Wave 4's exact lifecycle produces lower long-term context cost
  before Waves 5–7 ship. Why not: that outcome depends on future implementation,
  migration, repository adoption, and measured use that do not yet exist.
