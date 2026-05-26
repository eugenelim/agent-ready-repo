# agentbundle

Runtime library and reference CLI for the
[agent-ready-repo](https://github.com/eugenelim/agent-ready-repo) adapter
contract. Ships the `agentbundle` console script — install, validate,
adapt, and inspect packs — plus the build pipeline (`agentbundle.build`)
that projects pack sources into adapter-shaped trees.

As of 0.2.0, credential resolution lives in the build-projected
`credentials_shim` sibling that the `credential-brokers` pack drops
alongside each `auth: creds` consumer skill's `scripts/`. The
`agentbundle.credentials` module that previous releases (0.1.x)
exposed has been removed; consumers import `from .credentials_shim
import …` against the projected sibling instead. See the
`credential-broker-contract` spec and this package's `CHANGELOG.md`
for the migration recipe.

See the [top-level README](https://github.com/eugenelim/agent-ready-repo#readme)
for install routes, the pack catalogue, and the adapter contract.
