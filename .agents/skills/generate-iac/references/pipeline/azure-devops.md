# Azure DevOps pipeline reference — experimental

> **experimental** — the shape below follows the same plan → policy gate →
> apply pattern as `github-actions.md`, adapted for Azure Pipelines YAML.
> Validate against your ADO environment before use.

## Pipeline shape

```
PR trigger
  └── plan stage
        ├── static preflight (fmt -check, validate, Trivy)
        ├── terraform plan -out=tfplan
        ├── conftest test tfplan.json   ← policy gate
        └── publish artifact

Manual / merge trigger
  └── apply stage (environment: production — requires ADO approval gate)
        ├── download artifact
        └── terraform apply tfplan
```

## Workload identity federation (OIDC for Azure)

Azure DevOps supports OIDC via service connections — set up an ARM service
connection with Workload Identity Federation in ADO project settings.
Reference it via `AzureRMServiceConnection` in pipeline steps.

## Worked YAML sketch

```yaml
trigger:
  branches:
    include: [main]
  paths:
    include: [infra/**]

pr:
  paths:
    include: [infra/**]

variables:
  ENGINE: terraform
  TF_DIR: infra/

stages:
  - stage: Plan
    jobs:
      - job: plan
        pool:
          vmImage: ubuntu-latest
        steps:
          - checkout: self

          - task: TerraformInstaller@1
            inputs:
              terraformVersion: 'latest'

          - script: |
              $(ENGINE) fmt -check
              $(ENGINE) validate
            workingDirectory: $(TF_DIR)
            displayName: Static preflight

          - task: trivy@1
            inputs:
              version: latest
              type: config
              path: $(TF_DIR)
              exitCode: 1
            displayName: Security scan (Trivy)

          - task: AzureCLI@2
            displayName: Init + Plan
            inputs:
              azureSubscription: 'AzureRMServiceConnection'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                $(ENGINE) init -backend-config=backend.hcl
                $(ENGINE) plan -out=tfplan
                $(ENGINE) show -json tfplan > tfplan.json
              workingDirectory: $(TF_DIR)
              addSpnToEnvironment: true

          - script: |
              conftest test tfplan.json \
                --policy policy/ \
                --namespace terraform \
                --output table
            workingDirectory: $(TF_DIR)
            displayName: Policy gate (Conftest)

          - publish: $(TF_DIR)/tfplan
            artifact: tfplan

  - stage: Apply
    dependsOn: Plan
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: apply
        environment: production    # ← ADO environment with approval gate configured
        pool:
          vmImage: ubuntu-latest
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: tfplan

                - task: AzureCLI@2
                  displayName: Apply
                  inputs:
                    azureSubscription: 'AzureRMServiceConnection'
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      $(ENGINE) init -backend-config=backend.hcl
                      $(ENGINE) apply $(Pipeline.Workspace)/tfplan/tfplan
                    workingDirectory: $(TF_DIR)
                    addSpnToEnvironment: true
```

## Approval gate

The `environment: production` + approval in ADO is the equivalent of GitHub's
environment protection rules. Configure it in **Project Settings → Environments
→ production → Approvals and checks**.
