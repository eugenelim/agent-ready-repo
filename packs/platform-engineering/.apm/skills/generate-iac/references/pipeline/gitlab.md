# GitLab CI pipeline reference — experimental

> **experimental** — the shape below follows the same plan → policy gate →
> apply pattern as `github-actions.md`, adapted for GitLab CI YAML.
> Validate against your GitLab environment before use.

## Pipeline shape

```
MR trigger
  └── plan job
        ├── static preflight (fmt -check, validate, Trivy)
        ├── terraform plan -out=tfplan
        ├── conftest test tfplan.json   ← policy gate
        └── save artifact

Merge to main (manual trigger or auto)
  └── apply job (manual — requires human action to trigger)
        └── terraform apply tfplan
```

## GitLab CI OIDC (JWT)

GitLab 15.7+ supports OIDC via `id_tokens` — configure the cloud provider to
trust the GitLab OIDC issuer (`https://gitlab.com`) and use the `CI_JOB_JWT_V2`
token. For AWS, this means an IAM OIDC provider with the GitLab issuer and a
trust policy matching the `sub` claim format
(`project_path:<org>/<repo>:ref_type:branch:ref:<branch>`).

## Worked YAML sketch

```yaml
variables:
  ENGINE: terraform
  TF_DIR: infra/

stages:
  - validate
  - plan
  - apply

.base:
  image: hashicorp/terraform:latest  # pin to a specific version

preflight:
  extends: .base
  stage: validate
  script:
    - cd $TF_DIR
    - $ENGINE fmt -check
    - $ENGINE validate

security-scan:
  stage: validate
  image: aquasec/trivy:latest
  script:
    - trivy config $TF_DIR --exit-code 1 --severity CRITICAL,HIGH

plan:
  extends: .base
  stage: plan
  id_tokens:
    AWS_OIDC_TOKEN:
      aud: sts.amazonaws.com  # adjust per cloud
  script:
    - cd $TF_DIR
    - $ENGINE init -backend-config=backend.hcl
    - $ENGINE plan -out=tfplan
    - $ENGINE show -json tfplan > tfplan.json
    - conftest test tfplan.json --policy policy/ --namespace terraform --output table
  artifacts:
    paths:
      - $TF_DIR/tfplan
      - $TF_DIR/tfplan.json
    expire_in: 1 day

apply:
  extends: .base
  stage: apply
  when: manual         # ← requires human click to trigger
  only:
    - main
  id_tokens:
    AWS_OIDC_TOKEN:
      aud: sts.amazonaws.com
  needs:
    - plan
  script:
    - cd $TF_DIR
    - $ENGINE init -backend-config=backend.hcl
    - $ENGINE apply tfplan
  environment:
    name: production
```

## Protected environments

Set up a **protected environment** in GitLab (Settings → CI/CD → Environments →
production → Protected) to restrict who can trigger the manual `apply` job.
This is the primary mechanism preventing autonomous apply.
