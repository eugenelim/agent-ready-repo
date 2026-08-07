# Dependency contract

> **This file used to be 211 lines.** It described an install ladder, consent
> tokens, digest verification, PEP 668 handling, a toolchain cache with its own
> lock, and gate V4 — all of it machinery for managing a 236 MB external CLI.
> [`open-decisions.md`](open-decisions.md) D-B deleted the CLI, so it deleted the
> machinery.

## The contract

```toml
[[pack.runtime-dependencies]]
ecosystem = "pypi"
package   = "zensical"
version   = "==0.0.53"          # exact pin; alpha upstream
optional  = false                # required to render; see note
skills    = ["publish-binder"]
install   = "python -m pip install zensical==0.0.53"
note      = "Required only by `build`. `outline`, `resolve`, `explain`, `inventory`, `check` and `templates` all work without it."
```

Python floor: **3.11** (`tomllib`), checked as `binder.py`'s first action, exiting
2 with the version found rather than dying on the import. Zensical itself requires
3.10, so ours is the binding constraint.

## Detection and install

**Detect** with `importlib.util.find_spec("zensical")`, and compare
`zensical.__version__` against the pin. Absent or mismatched is exit 2 or 3.

**Install** is Tier 2 exactly as `author-a-skill.md` describes it — a single
deterministic command, no elevation, using a package manager the user
demonstrably already has. `author-a-skill.md` § *What counts as a dependency*
settles the manager question directly: *"`pip`/`uv` ship with a Python install, so
a pip-based Tier-2 install is low-risk."*

```
python -m pip install zensical==0.0.53
```

The skill detects, asks, installs on consent, and re-verifies. That is the whole
ladder.

## Why the old machinery is gone

Each piece existed for a property of the Quarto dependency that a 12.2 MB pip
wheel does not have:

| Deleted | Existed because |
|---|---|
| Rungs, ordering, and the integrity argument between them | The official PyPI route downloaded a binary with no checksum verification (Q13), making the policy-conforming option the less safe one |
| Digest verification against a shipped checksum file | We were fetching a 236 MB tarball ourselves |
| Consent tokens, `--consent=install-quarto-<version>` | A 236 MB third-party download deserved an explicit affirmation |
| PEP 668 handling and its fallback | `pip --user` is refused on externally-managed interpreters, and the fallback was the digest-verified fetch |
| The toolchain cache, its location decision, and its lock | A 236 MB binary is not a pip package and needed somewhere to live |
| Gate V4 and its platform matrix | The printed install command had to be proven to work verbatim |
| The 236 MB-per-CI-job provisioning cost | Quarto is not installable as a library |

None of it is a loss. All of it was overhead on a decision we reversed.

## Offline, restricted-network, and CI

| Situation | Behaviour |
|---|---|
| Offline, `zensical` present | Full function — **subject to the offline hardening** in [`zensical-adapter.md`](zensical-adapter.md), without which the *output* fetches fonts and scripts at read time |
| Offline, absent | `outline`, `resolve`, `explain`, `inventory`, `check --published` all work. `build` exits 2 with the install command and attempts nothing |
| Restricted network | The install fails cleanly naming the unreachable index; `pip`'s own error surfaces verbatim, and no `--trusted-host` or certificate relaxation is ever offered |
| CI | `pip install zensical==0.0.53` as an ordinary pipeline step. The skill never installs in CI: consent is refused when `CI` is set — **a guard against an accidental install, not a control against a hostile pipeline**, which could unset the variable |

## Python dependencies of our own

**None.** `binder.py` is standard library only — `tomllib`, `json`, `pathlib`,
`hashlib`, `re`, `shutil`, `subprocess`, `argparse`, `unicodedata`. Zensical is a
runtime dependency of the *render* step, not an import of the resolver, which is
what keeps `resolve` renderer-free and the index genuinely neutral.

Zensical brings its own tree — `click`, `jinja2`, `markdown`, `pygments`,
`pymdown-extensions`, `pyyaml`, `deepmerge`, `tomli` — all small, all common. Its
compiled `zensical.abi3.so` ships as a platform wheel across 12 targets including
Windows, musl, and armv7, so there is no source build on any supported platform.

## Missing-dependency error

```
Binder resolution succeeded, but rendering could not begin because the
renderer is not installed.

  Required   zensical==0.0.53

  Resolved   .binder-work/payments-review/8f3a91c2/binder-index.json
             12 nodes, 1 optional gap — complete, and renderable on any
             machine that has the renderer.

  To install (nothing has been installed or modified):
    python -m pip install zensical==0.0.53

No dependencies were installed or modified.
```
