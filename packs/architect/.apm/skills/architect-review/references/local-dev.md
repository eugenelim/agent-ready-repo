# Local-first — the founder on-ramp as a legitimate starting topology

A founder often starts on their own machine: everything on localhost, a single
process, a local database, files on disk. That is a legitimate *starting
topology*, not a mistake to correct — but it fakes things production must supply
for real. The design's job at the concept stage is to treat local-first
honestly: name the **local→production delta** and a **graduation path** to a
chosen provider class.

> Note: this reference is intentionally duplicated from `architect-design`'s
> `references/local-dev.md`. Skill autonomy beats DRY at this scale — each skill
> stands alone. See the pack README.

## Stay at architecture altitude — no toolchain

This reference reasons about *what local fakes and what production must supply*.
It does **not** prescribe a local toolchain: no docker-compose recipes, no
specific images, no named dev dependency. The graduation path names a provider
*class* (hyperscaler / primitives) and the capability that has to become real —
how you run it locally is out of scope.

## The local→production delta

What localhost fakes that production must make real:

| Local fake | What production must supply |
|---|---|
| `http://localhost`, no certs | real **TLS** + a real domain + cert lifecycle |
| secrets in `.env` / hardcoded | a real **secrets store** + rotation, no secrets in the image or repo |
| single local DB, no backups | a **durable data tier**: backups, a tested restore, and HA if the SLO needs it |
| files on local disk | **object storage** (durable, off-box), or a deliberate decision the data is ephemeral |
| serve assets from the app | **CDN / edge** for static + cacheable content (when latency/scale need it) |
| `print` / local logs | real **observability**: metrics, logs, traces, alerting someone is on call for |
| one process, one machine | a **scaling + availability** story: more than one instance, a balancer, blast-radius thinking |

## The graduation path

A local-first concept names *where it graduates to* and *what becomes real
first*. The shape:

1. **Pick the target provider class** — hyperscaler (managed services carry the
   delta) or primitives (you build the delta yourself; load `cloud-primitives.md`).
2. **Order the delta by what blocks the first real users** — usually TLS + real
   secrets + a durable data tier come before CDN and multi-region.
3. **Name what stays faked deliberately** — not every local convenience must
   graduate at once; say which are accepted-for-now and why.

The graduation order is itself often a **judgment** call (how much availability
is worth before launch); surface it as a decision, don't bake in a number.

## Use, don't recite

Name the deltas this system actually has and the first few that must become
real. A generic "you'll need TLS and backups" with no graduation order doesn't
help the founder decide what to do Monday.
