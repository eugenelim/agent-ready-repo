# agentbundle

Runtime library and reference CLI for the
[agent-ready-repo](https://github.com/eugenelim/agent-ready-repo) adapter
contract. Ships the `agentbundle` console script — install, validate,
adapt, and inspect packs — plus the build pipeline (`agentbundle.build`)
that projects pack sources into adapter-shaped trees.

As of 0.2.0 the `agentbundle.credentials` module that earlier releases
(0.1.x) exposed has been removed — `agentbundle` no longer ships a
credential-resolution module. Since RFC-0023, `auth: creds` consumers
resolve credentials through the standalone, pip-installable `credbroker`
library, imported in-process (`from credbroker import …`); it replaced the
build-projected `credentials_shim` sibling, which now survives only as the
`sso-broker` companion. See the `credbroker` package, RFC-0023, and this
package's `CHANGELOG.md` for the migration history.

See the [top-level README](https://github.com/eugenelim/agent-ready-repo#readme)
for install routes, the pack catalogue, and the adapter contract.
