---
name: deploy-microservice
description: Deploy a containerized microservice to the production Kubernetes cluster. Covers pre-deployment validation, image build and push, rolling deployment, health verification, and rollback. Use when you want to deploy a service to production.
metadata:
  boundaries: [shell_exec, network_call, filesystem_write]
---

# Skill: deploy-microservice

This skill deploys a microservice to production. It is important that all steps
are followed in order. Do not skip any step. Every step is mandatory. If a step
fails, stop and notify the operator. Do not proceed past a failing step.

## IMPORTANT: Read this before starting

Before you begin, make sure you have read all steps below completely. It is
essential that you understand the entire process before taking any action. Do
not start until you have read everything. This is important.

## Step 1: Pre-deployment validation

Pre-deployment validation is mandatory. Do not skip pre-deployment validation.
Pre-deployment validation must complete successfully before any other step.

### Environment variable validation

Check that every one of the following environment variables is set. If any
variable is missing or empty, stop immediately and tell the operator which
variable is missing. Do not proceed if any variable is missing.

- `SERVICE_NAME` — the name of the microservice being deployed. This is the
  name used in Kubernetes. It must match the name in the Helm chart. It must
  not contain spaces. It must be lowercase.
- `IMAGE_TAG` — the Docker image tag to deploy. This must be a specific tag,
  not `latest`. Using `latest` is forbidden. The tag must match the tag built
  by CI.
- `KUBE_CONTEXT` — the kubectl context to use. Must be the production context.
  Do not deploy to staging using this skill. Only production. Not staging.
- `KUBE_NAMESPACE` — the Kubernetes namespace. Must exist before deployment.
  The skill will not create namespaces. Do not expect namespace creation.
- `DOCKER_REGISTRY` — the Docker registry URL. Must be reachable from the
  deploy host. Verify network connectivity before deploying.
- `ROLLBACK_VERSION` — the image tag to roll back to if deployment fails.
  Must be set before deployment. If you don't know the rollback version,
  check the last successful deployment before proceeding.
- `MAX_SURGE` — maximum number of pods that can exceed the desired count
  during a rolling update. Default is 1. Set this before deploying.
- `MAX_UNAVAILABLE` — maximum number of pods that can be unavailable during
  a rolling update. Default is 0. Set this before deploying.
- `READINESS_PROBE_TIMEOUT` — timeout in seconds for the readiness probe.
  Default is 30. Increase for slow-starting services.
- `SLACK_WEBHOOK_URL` — Slack webhook URL for deployment notifications.
  Must be valid. Notifications will fail silently if this is not set.

### Git state validation

Before deploying, check that the Git repository is in a clean state:

- Run `git status` and confirm there are no uncommitted changes. If there
  are uncommitted changes, stop and tell the operator. Do not deploy from
  a dirty working tree.
- Run `git log --oneline -1` and note the commit SHA for audit logging.
- Run `git branch --show-current` to confirm you are on the correct branch.
  The branch must be `main` or a release branch. Do not deploy from a feature
  branch. If you are on a feature branch, stop and tell the operator immediately.
- Run `git fetch origin` and confirm the local branch is up to date with
  origin. If the branch is behind, stop and pull first.

### Service health check

Check the current health of the service before deploying:

- Run `kubectl get deployment $SERVICE_NAME -n $KUBE_NAMESPACE` to confirm
  the deployment exists and note the current replica count.
- Run `kubectl get pods -l app=$SERVICE_NAME -n $KUBE_NAMESPACE` to check
  current pod status. If any pod is not in `Running` state before the
  deployment starts, the pre-deployment health check fails. Stop and notify
  the operator. Do not proceed.
- Run `kubectl describe deployment $SERVICE_NAME -n $KUBE_NAMESPACE` and
  review the recent events section for any warning events. If warning events
  are present, surface them to the operator before proceeding.

## Step 2: Build and push

Build the Docker image using the Dockerfile in the current directory:

Run `docker build -t $DOCKER_REGISTRY/$SERVICE_NAME:$IMAGE_TAG .`

This may take several minutes. Do not interrupt the build. If the build fails,
stop and report the full error output to the operator. Do not proceed to push
if the build fails.

After a successful build, push the image to the registry:

Run `docker push $DOCKER_REGISTRY/$SERVICE_NAME:$IMAGE_TAG`

This may take several minutes depending on image size. Do not interrupt the
push. If the push fails, stop and report the error. Verify the push succeeded:

Run `docker manifest inspect $DOCKER_REGISTRY/$SERVICE_NAME:$IMAGE_TAG`

If the manifest is not found, the push failed. Do not proceed to deployment.

## Step 3: Deploy

Apply the new image to the Kubernetes deployment using a rolling update:

Run `kubectl set image deployment/$SERVICE_NAME $SERVICE_NAME=$DOCKER_REGISTRY/$SERVICE_NAME:$IMAGE_TAG -n $KUBE_NAMESPACE --record`

Wait for the rollout to complete:

Run `kubectl rollout status deployment/$SERVICE_NAME -n $KUBE_NAMESPACE --timeout=300s`

If the rollout does not complete within 300 seconds, it has timed out and
should be considered failed. Trigger rollback immediately if the rollout fails.
Do not wait longer than 300 seconds. 300 seconds is the maximum wait time.

## Step 4: Health verification

After the rollout completes, verify that the service is healthy:

- Run `kubectl get pods -l app=$SERVICE_NAME -n $KUBE_NAMESPACE` and confirm
  all pods are in `Running` state. If any pod is in `CrashLoopBackOff`,
  `Error`, `OOMKilled`, or `Pending` state, the deployment has failed.
  Trigger rollback immediately.
- Run `kubectl logs -l app=$SERVICE_NAME -n $KUBE_NAMESPACE --tail=50` and
  scan for ERROR-level log entries. Surface any errors to the operator.
- Run the HTTP health check: `curl -sf https://$SERVICE_NAME.internal/health`
  If the health check returns a non-200 status, the deployment has failed.
  Trigger rollback immediately.
- Wait 30 seconds after all pods are Running before declaring success.
  Early health check failures are common in the first 30 seconds. Wait the
  full 30 seconds. Do not declare success before 30 seconds have elapsed.

## Step 5: Rollback

If any step in deployment or health verification fails, roll back immediately:

Run `kubectl set image deployment/$SERVICE_NAME $SERVICE_NAME=$DOCKER_REGISTRY/$SERVICE_NAME:$ROLLBACK_VERSION -n $KUBE_NAMESPACE --record`

Wait for rollback to complete:

Run `kubectl rollout status deployment/$SERVICE_NAME -n $KUBE_NAMESPACE --timeout=300s`

After rollback, re-run the health verification steps to confirm the previous
version is healthy. Notify the operator that rollback was triggered and whether
rollback succeeded.

## REMINDER: Important notes

Remember: do not skip pre-deployment validation. Remember: do not deploy from
a feature branch. Remember: do not use the `latest` tag. Remember: always set
`ROLLBACK_VERSION` before deploying. Remember: always verify health after
deployment. Remember: if any step fails, stop and notify the operator
immediately. Remember: this skill is for production only. Remember: do not
interrupt a build or push in progress. Remember: wait 30 seconds before
declaring health verification success.
