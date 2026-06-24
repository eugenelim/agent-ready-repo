# oracle-table — per-tool concrete acquisition commands (the reference instance)

> **Loaded when:** the agent has detected the stack (protocol T0) and needs the
> concrete validate / plan / schema commands for that toolchain.
> **Status:** this table is the **reference instance** — concrete commands for
> the strong-tier stacks so they are runnable without guessing. The normative
> protocol in `SKILL.md` stays tool-neutral; nothing here is normative, and a
> tool's absence from this table is not a statement that it is unsupported (the
> tier spectrum, not this table, is the authority on coverage).

Each row gives, per tool: the **T1 static oracle** (validate + plan/preview),
the **schema slice** command (what to pull for the diff's resources), and
**what the schema exposes vs. what it does not** — so the immutability signal
is read from the right place (see `SKILL.md` § Schema heterogeneity).

## Strong tier

| Tool | T1 oracle (validate + plan/preview) | Schema slice | Immutable / replace signal |
| --- | --- | --- | --- |
| **Terraform / OpenTofu** | `terraform validate` then `terraform plan -out=tfplan` (review the diff); `terraform show -json tfplan` for a machine-readable plan | `terraform providers schema -json` (fields: `type` / `description` / `required` / `optional` / `computed` / `sensitive` only) | **Not in schema JSON.** Read `# forces replacement` from `terraform plan` **+ provider docs** |
| **Pulumi** | `pulumi preview --diff` (per-resource diff); `pulumi preview --json` for machine-readable | `pulumi package get-schema <provider>` → the resource's `properties` + `inputProperties` | `replaceOnChanges` **in schema** — read it from the slice |
| **AWS CDK** | `cdk synth` (emits the CloudFormation template); `cdk diff` against the deployed stack | the synthesized template + the underlying CFN resource-type schema (below) | via the CFN resource schema (below) |
| **AWS CloudFormation** | a **change set** (`create-change-set` → `describe-change-set`) — the dry-run diff before execute | `aws cloudformation describe-type --type RESOURCE --type-name AWS::Svc::Res` → the resource-type schema | `createOnlyProperties` **in schema** — read it from the slice |
| **Kubernetes / Helm** | `kubectl apply --dry-run=server` (server-side validation against the live API); `helm template` then the same dry-run | `kubectl explain <resource>.<path> --recursive` (OpenAPI schema from the cluster) | immutability is per-resource (e.g. many `spec` fields); read `kubectl explain` notes + the resource's API reference |

## Medium tier

| Tool | T1 oracle | Schema slice | Notes |
| --- | --- | --- | --- |
| **Ansible** | `ansible-playbook --check --diff` (what-if; module-dependent fidelity) | module docs (`ansible-doc <module>`) — no uniform machine-readable resource schema | lean on T3 docs + the runtime probe; `--check` fidelity varies by module |
| **Bicep** | `az deployment ... what-if` (ARM what-if diff) | the underlying ARM resource-provider schema | what-if is the diff oracle; schema is ARM-template-shaped |
| **cloud-init** | YAML schema validation (`cloud-init schema --config-file`) | the cloud-init module schema | validates config shape, not runtime effect — the probe confirms |

## Weak / none tier

| Surface | Why no strong static oracle | Posture |
| --- | --- | --- |
| **bespoke REST + `curl`** | no validate / plan / schema; the API is the only source of truth | **declare weak**, retrieve the API's own docs/OpenAPI if any (T3), and ground the contract at the **runtime probe** |
| **hand-rolled bare-metal provisioning** | imperative scripts have no declarative oracle | same — declare weak, lean on the probe; consider whether the step can be made declarative (`state-and-idempotency`) |

On a weak surface the static contract is *low-confidence by construction*. The
honest move is to **say so and shift weight to the runtime data-plane probe**
(`SKILL.md` § the Final oracle), never to manufacture a static check the tool
cannot back.
