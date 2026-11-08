# Service documentation

Evidence narrow: Kubernetes, PostgreSQL, GitLab, Elasticsearch, Nextcloud, and Grafana upgrade pages, read through a summarising fetch. Two are community projects and one is a vendor. Reference shape, first task, and limits pages rest on one or two projects. Read each rule as a default plus its condition.

Load this file only when surface discovery names a service (something a user deploys, configures, or operates).

## First screen

**Option:** goal-named blocks with a one-line promise each (Kubernetes), or a plain numbered contents list by part (PostgreSQL). Both work; the choice follows product size. Do not resolve between them.[^1][^2]

## First reader action

**Option:** a short runnable sequence that gets the service running and shows it respond, with real output for read commands (Kubernetes "Hello Minikube").[^3] Judgement: do not start with a full configuration tour.

## Sample style

Show real command output for read commands and omit it where it is long or variable. Use one small manifest or config rather than a screenshot to illustrate a concept.[^3][^4] Judgement, one source.

## Reference shape

**Option, judgement:** a configuration reference with every setting's type, default, and effect. Add a field for whether a change needs a restart, because both a hand-written and a generated reference sampled left defaults or restart rules unstated in places.[^5][^6]

## Troubleshooting

**Option:** symptom-first headings, each with a likely cause, a command, and an exit link, as Kubernetes' debug page does.[^7] The cost is that symptom-only indexes miss readers who search by goal, so add a goal-based entry point.

## Failures to refuse

**Default rule: a dedicated upgrade page, separate from install.** It states:
- the supported paths and the version-skip rule (kubeadm: skipping minor versions is unsupported);[^8]
- a route by install method;
- what to back up;
- whether rollback is supported. Say so plainly either way: GitLab gives a rollback plan, Nextcloud states "Downgrading is not supported" and points to a backup restore.[^9][^10] Rollback is not common, so do not imply it exists;
- which areas are unsupported or unfinished, labelled as such.

Refuse these:
- **Named example:** the GitLab administration troubleshooting page is a link directory with no symptom entries, and warns that some commands "might result in data loss".[^11]
- Install-only docs that omit upgrade for a supported install path. One user reported that Ghost's Docker docs did not cover upgrading a 5.x install to 6.x; this is a user's claim in a forum thread, not a documentation study.[^12] Confidence: low.
- A silent gap. Label unfinished or unsupported status instead.

## Sources

[^1]: Kubernetes Documentation home, https://kubernetes.io/docs/home/, accessed 2026-11-06. Confidence: medium.
[^2]: PostgreSQL 18 Documentation index, https://www.postgresql.org/docs/current/index.html, accessed 2026-11-06. Confidence: medium.
[^3]: Hello Minikube, https://kubernetes.io/docs/tutorials/hello-minikube/, accessed 2026-11-06 (page truncated on read). Confidence: medium.
[^4]: Pods, https://kubernetes.io/docs/concepts/workloads/pods/, accessed 2026-11-06. Confidence: low.
[^5]: PostgreSQL 18, Connections and Authentication settings, https://www.postgresql.org/docs/current/runtime-config-connection.html, accessed 2026-11-06. Confidence: low (some entries state no restart rule).
[^6]: Kubelet Configuration (v1beta1), https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/, accessed 2026-11-06. Confidence: low.
[^7]: Debug Pods, https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/, accessed 2026-11-06 and re-opened. Confidence: medium.
[^8]: Upgrade a kubeadm cluster, https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/, accessed 2026-11-06 and re-opened. Confidence: high for the version-skip rule and failure-recovery section.
[^9]: GitLab, Plan your upgrade, https://docs.gitlab.com/update/plan_your_upgrade/, accessed 2026-11-06 and re-opened. Confidence: high.
[^10]: Nextcloud, Upgrade, https://docs.nextcloud.com/server/latest/admin_manual/maintenance/upgrade.html, accessed 2026-11-06 and re-opened. Confidence: high for the quoted line.
[^11]: GitLab, Administration troubleshooting, https://docs.gitlab.com/administration/troubleshooting/, accessed 2026-11-06 and re-opened. Confidence: high.
[^12]: Ghost forum, Upgrading from a 5.x Docker image to 6.x, https://forum.ghost.org/t/upgrading-from-a-5-x-docker-image-to-6-x-docker-image/59617, accessed 2026-11-06. Confidence: low (one user's claim).
