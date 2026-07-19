# GitHub Actions pipeline reference

> **Load this when `ci = github-actions`.** This reference covers the
> standard two-job pipeline shape (plan → apply) with environment protection
> gates and the OPA/Conftest policy gate.

## Pipeline shape

```
PR opened / pushed
  └── plan job
        ├── static preflight (fmt -check, validate, Trivy/Checkov, OPA/Conftest)
        ├── terraform plan -out=tfplan
        ├── terraform show -json tfplan > tfplan.json
        ├── conftest test tfplan.json          ← policy gate
        └── upload tfplan as artifact

Merge to main (or manual trigger)
  └── apply job (environment: production — requires manual approval)
        ├── download tfplan artifact
        └── terraform apply tfplan
```

## Dual-engine matrix

The `ENGINE` variable drives both jobs. Set `ENGINE: terraform` for the
primary run; add a second matrix entry `ENGINE: tofu` for the AWS worked
example (D5 — AWS must pass on both).

## Worked YAML

```yaml
name: terraform

on:
  pull_request:
    paths:
      - 'infra/**'
  push:
    branches: [main]
    paths:
      - 'infra/**'
  workflow_dispatch:

permissions:
  contents: read
  id-token: write   # required for OIDC

env:
  ENGINE: terraform  # or tofu; override per matrix entry
  TF_DIR: infra/

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # -- OIDC credentials (AWS example) --
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.CI_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      # -- Install tools --
      - name: Install terraform / tofu
        run: |
          if [ "$ENGINE" = "tofu" ]; then
            curl -sL https://get.opentofu.org/install-opentofu.sh | bash -s -- --install-method standalone
          else
            # hashicorp/setup-terraform action recommended in CI
            echo "Use hashicorp/setup-terraform action"
          fi

      - name: Static preflight
        working-directory: ${{ env.TF_DIR }}
        run: |
          $ENGINE fmt -check
          $ENGINE validate

      - name: Security scan (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: ${{ env.TF_DIR }}
          exit-code: 1
          severity: CRITICAL,HIGH

      - name: Init
        working-directory: ${{ env.TF_DIR }}
        run: $ENGINE init -backend-config=backend.hcl

      - name: Plan
        working-directory: ${{ env.TF_DIR }}
        run: $ENGINE plan -out=tfplan

      - name: Show plan as JSON
        working-directory: ${{ env.TF_DIR }}
        run: $ENGINE show -json tfplan > tfplan.json

      - name: Policy gate (Conftest)
        working-directory: ${{ env.TF_DIR }}
        run: |
          conftest test tfplan.json \
            --policy policy/ \
            --namespace terraform \
            --output table

      - name: Upload plan artifact
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-${{ github.sha }}
          path: |
            ${{ env.TF_DIR }}/tfplan
            ${{ env.TF_DIR }}/tfplan.json

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production   # ← requires manual approval in GitHub env settings
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Download plan artifact
        uses: actions/download-artifact@v4
        with:
          name: tfplan-${{ github.sha }}
          path: ${{ env.TF_DIR }}

      - name: Init
        working-directory: ${{ env.TF_DIR }}
        run: $ENGINE init -backend-config=backend.hcl

      - name: Apply
        working-directory: ${{ env.TF_DIR }}
        run: $ENGINE apply tfplan
```

## Environment protection gate

The `environment: production` key on the `apply` job requires a GitHub
environment named `production` with protection rules set:
- Required reviewers (at least one human approval before apply runs)
- Optionally: deployment branches limited to `main`

This is the primary mechanism preventing autonomous apply — a Blocker if
missing (see `generate-iac/SKILL.md` hard rules).

## OIDC sub format note (2026-07-15)

GitHub changed the OIDC `sub` claim for repos created on or after 2026-07-15.
For CI role trust policies, verify the `sub` format against the actual token
claim in a test run — see `providers/aws.md` for details.

## Infracost delta (optional)

Add an `infracost diff` step after `Plan` to post a cost estimate comment on
the PR:

```yaml
- name: Infracost diff
  uses: infracost/actions/setup@v3
  with:
    api-key: ${{ secrets.INFRACOST_API_KEY }}
- run: |
    infracost diff --path=${{ env.TF_DIR }}/tfplan.json \
      --format=github-comment \
      --out-file=/tmp/infracost.md
    gh pr comment ${{ github.event.pull_request.number }} \
      --body-file /tmp/infracost.md
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
