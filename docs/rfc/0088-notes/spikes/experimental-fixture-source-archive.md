# Experimental fixture source archive

This note preserves the bounded, synthetic source inputs used by RFC-0088
spikes S1, S2, S3, S5, and S6 without promoting executable prototype files
into a production or pack path. S4 used public primary-source research and has
no executable fixture.

- Archive media type: `application/gzip` containing a tar archive
- Archive size: 16,739 bytes
- Archive SHA-256: `39cb9ff5935f67ebfa8f53bc240e0cfba170bb768fc86b762721948dcdea9847`
- Excluded deliberately: browser binaries, npm tarballs, generated profiles,
  raw logs, installed/rendered trees, result JSON, and all transient runtime
  state other than the synthetic S5 grant/provenance inputs

The archive contains the exact fixture source at the close of the 2026-08-15
review pass. Reconstruct it in an approved temporary path with the following
copy-paste-safe procedure. The Python decoder is used because the `base64`
decode flag differs between macOS and GNU implementations.

```bash
SPIKE_ROOT=$(mktemp -d /private/tmp/rfc0087-web-pilot-replay.XXXXXX)
python3 - "$SPIKE_ROOT/fixture-source.tgz" <<'PY'
import base64
import pathlib
import sys

payload = """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"""
pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(payload))
PY
python3 - \
  "$SPIKE_ROOT/fixture-source.tgz" \
  "$SPIKE_ROOT" \
  "39cb9ff5935f67ebfa8f53bc240e0cfba170bb768fc86b762721948dcdea9847" <<'PY'
import hashlib
import pathlib
import sys
import tarfile

archive = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2]).resolve(strict=True)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != sys.argv[3]:
    raise SystemExit(f"fixture archive digest mismatch: {actual}")

with tarfile.open(archive, "r:gz") as bundle:
    members = bundle.getmembers()
    if len(members) > 500:
        raise SystemExit("fixture archive has too many members")
    if len({member.name for member in members}) != len(members):
        raise SystemExit("fixture archive contains duplicate paths")
    if sum(member.size for member in members) > 10 * 1024 * 1024:
        raise SystemExit("fixture archive exceeds the total size limit")

    validated = []
    for member in members:
        relative = pathlib.PurePosixPath(member.name)
        if relative.is_absolute() or not relative.parts:
            raise SystemExit(f"unsafe fixture path: {member.name!r}")
        if any(part in {"", ".", ".."} for part in relative.parts):
            raise SystemExit(f"unsafe fixture path: {member.name!r}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(f"unsupported fixture member type: {member.name!r}")
        if member.mode & 0o7000:
            raise SystemExit(f"unsafe fixture mode: {member.name!r}")
        if member.size > 1024 * 1024:
            raise SystemExit(f"fixture member exceeds size limit: {member.name!r}")
        target = root.joinpath(*relative.parts).resolve(strict=False)
        if target != root and root not in target.parents:
            raise SystemExit(f"fixture path escapes replay root: {member.name!r}")
        validated.append((member, target))

    for member, target in validated:
        if member.isdir():
            target.mkdir(mode=0o700, parents=True, exist_ok=False)
            continue
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        source = bundle.extractfile(member)
        if source is None:
            raise SystemExit(f"fixture member has no data: {member.name!r}")
        with target.open("xb") as destination:
            destination.write(source.read())
PY
printf 'Validated fixture replay root: %s\n' "$SPIKE_ROOT"
```

Use the printed fresh root in place of
`/private/tmp/rfc0087-web-pilot-replay` in the individual spike commands. The
validator admits only bounded regular files and directories: absolute paths,
traversal, duplicate paths, links, devices, special permission bits, and
oversized archives or members fail before extraction.

S1/S2 additionally require the exact `playwright@1.62.0` and
`playwright-core@1.62.0` packages named by their lockfile and an admitted
browser binary. A rerun may resolve them from the official npm registry or a
verified local cache, but must record the resulting tarball integrity and
browser channel/version. S5 requires the destination repository at the recorded
ref and uses the install commands in its spike note to create rendered and
isolated user-install trees. None of these setup steps authorizes use of a real
profile or credential.

The archive is evidence support, not a production deliverable. Any changed
fixture produces a new archive digest and a new run; prior results must not be
attributed to modified source.
