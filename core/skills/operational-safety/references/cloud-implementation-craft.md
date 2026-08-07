# cloud-implementation-craft — least-privilege-but-sufficient, timing, packaging, externalized config

> **Loaded when:** the change authors infrastructure, a managed-runtime
> deployment, or live-environment interaction — i.e. infra-flavored work. This
> module is the **one `operational-safety` module consumed at EXECUTE**: the
> orchestrator inlines it into the **implementer's EXECUTE brief** (not only the
> reviewer's REVIEW brief), the deliberate EXECUTE-consumer extension of the
> depth-library pattern. `quality-engineer` also loads it at REVIEW to check the
> craft against deployed reality.
> **Grounded in:** a production field report — the **Author · behavioral** family
> (permissions iterated reactively, undesigned propagation waits, escalating
> timeouts and sprinkled `sleep`s, no client cold-start tolerance, dependency
> cycles fixed by trial) and the **packaging gap** from Author · structural (a
> flat-package-root relative-import `ModuleNotFoundError` that passed locally and
> failed on the managed runtime). Operational taxonomy: AWS Well-Architected
> (least privilege; design for failure), Google SRE (handle overload, backoff).
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

> **The four-way carve — this module's lane.** `cloud-implementation-craft`
> owns ***will the call path even succeed?*** — **under**-permissioning + timing
> / retry. The other three lanes:
> - **`security-checklists`** owns *over-permissioning + security config* (is
>   this too open?) — over-broad IAM, public exposure, secrets in state.
> - **the policy-as-code / CSPM scanner** owns *config-against-policy* —
>   per-provider secure-config baselines.
> - **[`contract-acquisition`](../../contract-acquisition/SKILL.md)**
>   owns *IaC-against-the-platform's-structural-contract* — does this flag /
>   field / name / immutable-property exist and accept this value?
>
> Four distinct questions. A role too **narrow** to make the call is *this
> module*; a role too **broad** is `security-checklists`. Keep the lines clean
> both ways — do not migrate security config into this module.

A provisioned resource that is correctly *shaped* (the contract grounding) can
still **fail to work** — the call is denied, the dependency isn't ready, the
timeout fires before a cold start finishes, the entrypoint won't import. This
module is the behavioural craft that the contract grounding does not cover:
derive it in one pass from the contract, don't iterate it reactively against
the live environment.

## Implementation checks (author at EXECUTE; verify at REVIEW)

- `reason` **Least-privilege-but-sufficient permissions, derived in one pass.**
  Read the permissions the call path needs **from the acquired contract** and
  grant exactly those — once, up front. The field-report anti-pattern is
  *reactive iteration*: deploy → denied → widen → repeat, which converges on
  either over-broad grants or wasted loops. Sufficient *and* minimal is a
  one-pass derivation from the contract, not a search. (Over-broad is
  `security-checklists`' lane; under-broad that makes the call fail is this
  module's.)
- `reason` **Eventual-consistency / propagation readiness waits.** When a
  resource (an IAM role, a DNS record, a distribution, a bucket policy) is
  *eventually* consistent, design an explicit **readiness wait** — poll until
  ready — rather than assuming the next call sees it. A create that "succeeds"
  then a dependent call that fails intermittently is an undesigned propagation
  window, not a flake.
- `reason` **Timeouts to real latency; bounded backoff; client cold-start
  tolerance.** Set each timeout to the dependency's **actual** latency
  distribution, not a guessed round number escalated under pressure. Retries use
  **bounded exponential backoff**, not a sprinkled `sleep`. And the **client /
  frontend tolerates cold starts** — the first request after idle is slow by
  design; surface a retry/loading path, never a raw cold-start timeout to the
  user.
- `reason` **Dependency ordering is designed, not discovered.** Order
  creation/teardown by the real dependency graph (e.g. the network before the
  thing in it; the role before the principal that assumes it). A dependency
  cycle fixed by trial-and-error re-runs is the signal this was skipped.
- `hybrid` **Terminal-failed-state handling.** Author around states a normal
  update cannot leave (e.g. a `ROLLBACK_COMPLETE` stack must be **deleted and
  recreated**, not updated). *Carve note:* this module owns **how to author
  around** a terminal-failed state at EXECUTE; the sibling
  [`state-and-idempotency`](state-and-idempotency.md) module names the same
  state as a **destroy-recreate convergence case** for the reviewer — the two
  placements are deliberate (authoring craft vs. convergence-case naming), not
  duplication.
- `reason` **Deployment-artifact packaging & entrypoint / module-resolution
  model — confirm before writing imports.** Confirm **how the managed runtime
  packages the artifact and imports the entrypoint** *before* writing the
  imports. A local package-relative or project-root import assumption that
  passes on the dev machine **fails in a flat package root or a script-invoked
  entrypoint** (the field-report `ModuleNotFoundError`). The platform specifics
  — the package layout, the handler signature, the module search path — defer to
  the **T2 curated platform skill** (`contract-acquisition`), never to
  bundled per-vendor data.
- `reason` **Externalized script configuration — never hardcoded inline.** Infra
  build scripts and the verify / probe / teardown scripts take **resource name
  prefixes, region / account, tags, stage, and naming-convention tokens from
  external config** — not literals in the script body. *Illustrative mechanisms
  (never normative, Principle 1):* `*.tfvars` / `TF_VAR_*`, CDK context or env,
  a parameters or `.env` file. Externalizing them lets a build **honour the
  organization's naming + tagging conventions** without editing script bodies,
  and lets the reusable harness **port across accounts to stand up like-for-like
  environments** — the property the V2 ephemeral, uniquely-named probe target
  and `environment-isolation`'s per-PR harness both rest on.

## Established-pattern bypass

Resolve the repo's sanctioned mechanisms — the IAM-policy module that already
encodes least-privilege per service, the readiness-wait / retry helper the
deploy pipeline ships, the `*.tfvars` / context convention that parameterizes
environments — and flag a change that hand-rolls reactive permission-widening,
ad-hoc `sleep`s, or hardcoded resource names inline instead of extending them.

*Illustrative only (never normative):* a deploy that derives its execution-role
policy from the resources it touches, waits on a readiness signal before the
dependent call, and reads its name prefix from `TF_VAR_name_prefix`, exhibits
this shape — but the check is the *property* (sufficient-and-minimal,
readiness-designed, externally parameterized), not any one tool.
