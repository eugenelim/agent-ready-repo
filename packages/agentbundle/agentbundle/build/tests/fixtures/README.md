# Test fixtures for `agentbundle.build`

Fixture layout convention — one pack per subdirectory under
`packs/`, named for the test it serves. Adapters draw their input
from these; the end-to-end pipeline test (T8) drives `make build`
against the four named reference packs.

Layout:

```
fixtures/
├── packs/                                 # T8 end-to-end + adapter unit tests
│   ├── core/
│   │   ├── pack.toml
│   │   ├── .claude-plugin/plugin.json
│   │   └── .apm/
│   │       ├── skills/<name>/
│   │       ├── agents/<name>.md
│   │       ├── hooks/<name>.{sh,py}
│   │       ├── hook-wiring/<name>.toml
│   │       └── commands/<name>.md
│   ├── governance-extras/
│   ├── user-guide-diataxis/
│   └── monorepo-extras/
└── recipes/                               # T6 negative-path tests
    └── bogus-target.toml                  # unknown-adapter-target negative test
```

Fixtures are test data and the `stdlib-only` rule does **not** bind
them — a fixture hook may import third-party packages to simulate a
real-world payload. The lint audit at `tools/lint-build.sh`
explicitly excludes this directory.

Production-pack migration (a top-level `packs/` directory holding
this repo's catalogue content) is **out of scope** for this spec
per AC #7. When that lands (RFC-0001 F-dist follow-on), `make
build` will pick up both `packs/` and these fixtures without code
change — pack discovery is a glob.
