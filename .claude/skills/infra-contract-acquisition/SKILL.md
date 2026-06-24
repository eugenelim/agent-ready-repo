---
name: infra-contract-acquisition
description: Acquire a stack's real contract from its own toolchain oracles before authoring infrastructure, a CLI invocation, or code that runs on a managed runtime against an unfamiliar platform. Triggers on "deploy to", "write the Terraform / Pulumi / CDK / CloudFormation for", "provision", "what's the right resource shape", "why does this apply fail", and any infra-authoring prompt on a platform you don't know cold. Runs a tiered, tool-keyed protocol — detect the stack, run the toolchain's validate / plan / synth oracle plus a machine-readable schema slice, consult a curated platform skill, retrieve official docs, then a runtime data-plane probe — declares its oracle tier and confidence, and degrades honestly to the runtime probe when the toolchain ships no strong static oracle. Do NOT use for application-only code with no managed-runtime contract (use work-loop directly), and do NOT use to review a finished diff (that rides quality-engineer).
---

# Skill: infra-contract-acquisition

This skill answers one question before you author anything against a platform
you don't know cold: **what is this platform's real contract — its flag set,
its resource schema, its naming and immutability rules, its packaging and
entrypoint model — and where does that contract come from?** The field-report
failures this closes were not reasoning failures; they were *contract*
failures: invented CLI flags, a violated naming regex, a wrong tool-schema
shape, an immutable-field collision, a managed-runtime import model guessed
wrong. The fix is not to memorize more clouds. It is to **drive the
toolchain's own deterministic oracles** — the ones that ship with the stack —
and to ground authoring in what they return, declaring honestly how strong
that oracle is.

This is the **infra generalization of AGENTS.md's "grep to verify a function
exists before importing it"**: don't guess a flag, a schema field, a
constraint, or a packaging assumption when the toolchain can tell you the
truth deterministically.

> **The four-way carve — who owns which infra question.** Four distinct
> questions, four owners; keep the lines clean both ways.
> - **`infra-contract-acquisition` (this skill)** — *is the IaC / invocation
>   correct against the platform's **structural** contract?* (Does this flag
>   exist, this field accept this value, this resource name match the regex,
>   this property is immutable?)
> - **`cloud-implementation-craft`** (an `operational-safety` module) — *will
>   the call path even **succeed**?* under-permissioning, timing /
>   eventual-consistency, retry / cold-start, dependency ordering, packaging.
> - **`security-checklists`** — *is this too **open**?* over-permissioning and
>   security config (IAM blast radius, public exposure, secrets in state).
> - **the policy-as-code / CSPM scanner** — *is the config **against
>   policy**?* per-provider secure-config baselines from vendor-maintained
>   rulesets.
>
> A leaked credential is `security-checklists`; an under-scoped role that makes
> the call fail is `cloud-implementation-craft`; a non-existent flag or an
> immutable-field collision is *this skill*.

## When it fires

This skill is **user- and agent-invoked** (it has an activation surface, unlike
the reviewer-internal depth libraries). It fires when the agent is about to
author against a platform it doesn't already know cold — at `work-loop`'s
**EXECUTE contract-grounding gate**: before generating a CLI invocation, an IaC
resource, or application code that runs on a managed runtime (a function
handler whose packaging / import model the platform dictates) against an
**unfamiliar** platform. Acquire the contract first; never guess a flag, schema
shape, field constraint, or packaging / entrypoint assumption. It is universal
across light and full mode — grounding is the cheap part, and a guessed
contract is the expensive part.

## The protocol (tiered, tool-keyed, increasing cost)

Run the tiers in order, stopping when you have the contract slice the change
needs. Each tier is **keyed to the tool the stack already uses**, never to a
vendor. Concrete per-tool commands live in
[`references/oracle-table.md`](references/oracle-table.md) — that table is the
**reference instance**; the protocol prose stays tool-neutral.

- **T0 — detect the stack from the diff.** Identify the toolchain in play
  (declarative IaC, a cloud CLI, a Kubernetes manifest, a hand-rolled script)
  and the specific resources / commands the change touches. The tool you detect
  decides which oracle tier you can reach (see *Oracle-tier honesty* below).

- **T1 — run the toolchain's own oracle + take a machine-readable schema
  slice.** Run the deterministic static oracle the stack ships
  (`terraform validate` + `plan`, `cdk synth`, `pulumi preview`, a
  CloudFormation change set, `kubectl --dry-run=server`) **and** pull a
  machine-readable **schema slice** for exactly the resources the diff touches —
  field names, types, required/optional, and the immutable (replace-on-change)
  set. This is the strongest deterministic source; it grounds flags, field
  shapes, and naming before a single resource is authored. Read **only the
  slice the change needs**, not the whole provider schema — the contract is
  fetched in slices so it does not flood the window.

- **T2 — consult a curated platform skill for the behavioural contract no
  schema encodes** (managed-surface naming conventions, quotas, propagation
  semantics, the deployment-artifact packaging / entrypoint-import model). This
  is the load-bearing tier for an unfamiliar *managed* surface, and the one the
  repo deliberately does **not** bundle (Principle 1 — no per-vendor data).
  Apply the **3-tier dependency policy**: **detect** whether such a skill is
  installed; if present, read it; **if absent on an unfamiliar managed surface,
  recommend authoring or installing one and surface it as a decision** — do not
  silently proceed on guessed behavioural contract. The detect-and-recommend
  step makes the gap *visible* and routes it to a human; it does not pretend the
  gap is closed.

- **T3 — retrieve the official platform docs** for the specific resource /
  command / constraint when T1's schema and any T2 skill don't settle it. Cite
  the doc in the contract slice; provider docs are the authority for the
  behavioural rules (and, for one tool, the immutability signal — see *Schema
  heterogeneity*).

- **Final oracle — the runtime data-plane probe.** The contract is only
  *fully* confirmed by deploying to an ephemeral target and exercising the data
  plane (the V2 probe `work-loop` defines — in-network-if-private, write →
  read-back, readiness-aware poll, self-teardown). On a **weak-oracle stack**
  (below) this is not the last tier but the **primary** one: when the toolchain
  ships no strong static oracle, weight shifts here rather than to a faked
  static check.

## Oracle-tier honesty (the generality mechanism)

Coverage is **not uniform across stacks** — it is a capability spectrum keyed
to the tool. State your tier and confidence explicitly in the contract slice,
and never fake static coverage a weak oracle can't give:

| Tier | Tools (illustrative, not exhaustive) | What the static oracle gives | Posture |
| --- | --- | --- | --- |
| **strong** | Terraform / OpenTofu, Pulumi, AWS CDK / CloudFormation, Kubernetes / Helm — and **any provider they address**, including Hetzner, Proxmox, vSphere, OpenStack, on-prem Kubernetes | full validate + plan/preview diff + a machine-readable resource schema slice | ground authoring on T1; the probe confirms |
| **medium** | Ansible (`--check --diff`), Bicep, cloud-init | a dry-run / what-if diff, partial or no machine-readable schema | ground what T1 gives; lean harder on T3 docs + the probe |
| **weak / none** | bespoke REST + `curl`, hand-rolled bare-metal provisioning, an undocumented internal API | no trustworthy static oracle | **declare weak; shift weight to the runtime probe** — do not invent static coverage |

**The weak-oracle row and the runtime-probe fallback are mandatory, not
optional.** On a weak oracle the honest output is *"oracle tier — weak;
confidence — low on static contract; grounding the contract at the runtime
probe instead"*, not a confident-looking but ungrounded resource. Declaring the
tier is what keeps the long tail (on-prem / bespoke) honest rather than
silently faked.

## Schema heterogeneity (the immutability signal is not uniform)

The riskiest assumption is *"the toolchain exposes the immutable-field contract
machine-readably."* It is **true but heterogeneous**, and you must read the
replace-on-change signal from the right place per tool:

- **CloudFormation** — `createOnlyProperties` is in the resource-type schema;
  read it from the schema slice.
- **Pulumi** — `replaceOnChanges` is in the schema; read it from the slice.
- **Terraform / OpenTofu** — `terraform providers schema -json` exposes only
  `type` / `description` / `required` / `optional` / `computed` / `sensitive`;
  it does **not** expose force-new. Read the replace signal from a `terraform
  plan` (it annotates `# forces replacement`) **plus the provider docs**, not
  from the schema JSON.

## Output — a cited contract slice, not "contract acquired: yes"

The protocol's deliverable is a **short, cited contract slice** the build then
references — the exact flags, the field shapes, the naming rule, the
immutable-field set, the packaging model, each tagged with the tier and the
source (T1 schema, T2 skill, T3 doc, or the probe). A bare "contract acquired"
is box-ticking; the cited slice is what lets `quality-engineer` later
**re-derive the contract independently** from the same oracles and catch a
build that authored against model memory anyway.
