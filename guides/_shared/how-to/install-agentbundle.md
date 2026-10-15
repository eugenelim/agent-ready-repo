---
title: "Install agentbundle"
summary: "Install the agentbundle command line from pip, a local clone, or APM, and fix TLS and proxy problems on a corporate network."
pack: _shared
kind: how-to
aliases:
  - guides/_shared/how-to/install-agentbundle-from-clone
---

# Install agentbundle

Install the `agentbundle` command so you can install, preview, and upgrade packs. It needs Python 3.11 or newer.

## Install with pip

```bash
python -m pip install agentbundle
```

Run it inside a virtual environment you control:

```bash
python3 -m venv .venv && source .venv/bin/activate
```

If pip stops with `error: externally-managed-environment`, your system Python follows [PEP 668](https://peps.python.org/pep-0668/). Create a virtual environment and install there. Avoid `--break-system-packages`.

Pip, uv, or Poetry sign in to your package index. AgentBundle does not reuse that sign-in when it reads a protected catalogue. See [Configure agentbundle](configure-agentbundle.md#protected-catalogue-sign-in).

Skill scripts start with `#!/usr/bin/env python3`. The first `python3` on `PATH` when your agent runs a script must be able to import `agentbundle`. `pipx` and `uv tool` keep the package private, so use a virtual environment or the system Python for credentialed skills.

## Install from a clone

Use a clone when you develop packs, run an org fork, or cannot reach PyPI.

```bash
git clone https://github.com/<owner>/<catalogue>
cd <catalogue>
python -m pip install -e packages/agentbundle/
```

The editable install links your interpreter to the clone. A `git pull` updates both the CLI and the pack content with no reinstall. With an editable install, `agentbundle` uses the clone as its catalogue source, so `list-packs` shows your working tree.

Install a pack from the clone:

```bash
agentbundle install --pack <name> . --output <target>
```

Credentialed skills read credentials through the separate `credbroker` library. Install it from the clone too:

```bash
python -m pip install -e ./packages/credbroker
```

:::caution
`python -m pip install ./packages/agentbundle` without `-e` copies the package once. A `git pull` does not reach it until you run the command again. Use it only for a pinned tag you never edit.
:::

If pip is blocked, build a single-file archive instead:

```bash
make zipapp
./dist/agentbundle.pyz install --pack core . --output /path/to/your/project
```

The archive runs the CLI but does not put `agentbundle` on `sys.path`. Credentialed skills fail with `ModuleNotFoundError` on a host that has only the archive.

## Install with APM

Use [APM](https://github.com/agent-package-manager) when your agent tool is not Claude Code and you do not want the Python CLI.

```bash
apm install <owner>/<catalogue>/<pack>
```

APM installs pack content only. It does not install `agentbundle`. Run `agentbundle init-state` once after an APM install so upgrades have a baseline. See [Upgrade packs](upgrade-packs.md).

## Behind a corporate network

A proxy that inspects TLS re-signs traffic with a private root. Python reads its own certificate file, not the operating system store, so a fetch fails with:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

What to do depends on the platform:

| Platform | What happens | What you do |
| --- | --- | --- |
| macOS | `agentbundle` retries once with the administrator keychain and says so on stderr. | Nothing. Set `AGENTBUNDLE_NO_SYSTEM_TRUST=1` to turn the retry off. |
| Windows | Python already trusts the Windows stores. | Nothing for a root pushed by Group Policy or Intune. |
| Linux | OpenSSL reads `/etc/ssl/certs`. | Install the root there with `update-ca-certificates`. |
| WSL | The distribution does not inherit the Windows store. | Install the root in the distribution, or set `AGENTBUNDLE_CA_BUNDLE`. |

Install a root inside a Debian or Ubuntu WSL distribution:

```bash
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

Export the root from Windows first: Certificate Manager, Trusted Root Certification Authorities, Export as Base-64 X.509.

Point at a CA bundle for one run:

```bash
AGENTBUNDLE_CA_BUNDLE=/etc/ssl/corp-ca.pem agentbundle install --pack core
```

Send traffic through a proxy:

```bash
HTTPS_PROXY=http://proxy.example.com:3128 agentbundle install --pack core
```

A GitHub archive fetch redirects from `github.com` to `codeload.github.com`. Your proxy must allow both hosts.

If every HTTPS request fails on a python.org macOS build, the interpreter has no certificate store. Check it:

```bash
python3 -c "import ssl; print(ssl.get_default_verify_paths())"
```

`cafile=None` with no `capath` means the store is empty. Run the `Install Certificates.command` in the Python folder, or set `SSL_CERT_FILE=/etc/ssl/cert.pem`.

The [command reference](../reference/agentbundle.md#corporate-networks) covers each variable and the trust rules in full.

## Check it works

```bash
agentbundle --help
python -c "from agentbundle.cli import main"
```

The import prints nothing on success. If it ends with `ModuleNotFoundError: No module named 'agentbundle'`, run it again from the shell that launches your agent. A pass in one shell and a fail in another means two Python interpreters on `PATH`. Compare `python3 -c "import sys; print(sys.executable)"` with the interpreter that `pip -V` reports.

Next, [install packs for your agent](install-packs.md).
