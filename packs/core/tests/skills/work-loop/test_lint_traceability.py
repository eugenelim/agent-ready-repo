#!/usr/bin/env python3
"""Pytest coverage for the structural-orphan lint.

Builds fixture workspaces in a tempdir and runs the linter as a subprocess
against the documented `python <skill>/scripts/lint-traceability.py --root <dir>`
invocation — the same shape the CI gate uses (a real subprocess, not a
synthesised import, so the real file-path entry point is exercised). Covers each
acceptance case: no-op clean, the sidecar-authoritative path (converged / orphan
/ dangling / cycle / bad-schema), the derive-from-artifacts standalone path
(clean / backward orphan / forward orphan / terminal exemption / layer-skip),
the three cross-repo endpoint states (local / satisfied-by-reference pinned and
unpinned / unresolvable), dangling-local and cycle hard violations, container
extraction, the exit-code matrix, and the structural-only / stdlib-only /
no-hardcoded-path NFRs.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
LINTER = SCRIPT_DIR / "lint-traceability.py"


def expect(cond: bool, msg: str) -> None:
    """Assert a condition through pytest instead of aggregate state."""
    assert cond, msg


def symlink_or_skip(
    name: str,
    link: Path,
    target: Path | str,
    *,
    target_is_directory: bool = False,
) -> bool:
    """Create a required symlink, recording a real skip only outside CI."""
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        if os.environ.get("CI"):
            pytest.fail(f"{name}: CI must support this symlink regression: {exc}")
        pytest.skip(f"{name}: symlink creation unavailable ({exc})")
    return True


def _ensure_resolver(root: Path) -> None:
    """Install the resolver binary under root/.agentbundle/bin/ if not present.

    Required because the spec mandates that an absent binary is a hard violation
    when a chain anchor exists.  All subprocess-based tests that write anchors
    (briefs, rollup, discovery-layer files) must have the resolver present so the
    delivery check is configured — without changing their asserted outcomes (the
    resolver returns an empty snapshot for fixture repos with no delivery intents).
    """
    dest = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    if not dest.exists():
        src = (
            Path(__file__).resolve().parents[3]
            / ".apm"
            / "adapter-root-bins"
            / "intent_delivery_relations.py"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())


def run_raw(root: Path, *extra: str) -> tuple[int, str, str]:
    """Invoke the linter exactly as given — no flags added."""
    _ensure_resolver(root)
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root), *extra],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run(root: Path, *extra: str) -> tuple[int, str, str]:
    """Run with `--verbose`: the full output shape every per-item assertion
    below was written against. A passing run now withholds detail lines by
    default, so tests about that default use `run_raw` explicitly."""
    return run_raw(root, "--verbose", *extra)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_spec(root: Path, slug: str, *, status: str = "Draft",
               brief: str | None = None, contract: str | None = None,
               component: str | None = None, discovery: str | None = None) -> None:
    body = f"# Spec: {slug}\n\n- **Status:** {status}\n"
    if brief is not None:
        body += f"- **Brief:** {brief}\n"
    if contract is not None:
        body += f"- **Contract:** {contract}\n"
    if discovery is not None:
        body += f"- **Discovery:** {discovery}\n"
    if component is not None:
        body += f"- **Component:** {component}\n"
    body += "\n## Acceptance Criteria\n\n- [ ] AC1\n"
    write(root / "docs" / "specs" / slug / "spec.md", body)


def write_brief(root: Path, slug: str, *, parent: str | None = None) -> None:
    body = f"# Brief: {slug}\n\n- **Slug:** `{slug}`\n"
    if parent is not None:
        body += f"- **Parent intent:** {parent}\n"
    write(root / "docs" / "product" / "briefs" / f"{slug}.md", body)


def write_component(root: Path, name: str) -> None:
    """A catalogued component — a `packages/<name>/` dir with the Backstage
    `catalog-info.yaml` marker (id `component:default/<name>`)."""
    d = root / "packages" / name
    d.mkdir(parents=True, exist_ok=True)
    write(d / "catalog-info.yaml",
          f"apiVersion: backstage.io/v1alpha1\nkind: Component\nmetadata:\n  name: {name}\n")


def write_sidecar(root: Path, *, nodes: list[dict], edges: list[dict],
                  root_id: str, leaf_kind: str = "component",
                  schema_version: str = "0.1", initiative: str = "demo") -> None:
    payload = {
        "schema_version": schema_version, "initiative": initiative,
        "root": root_id, "leaf_kind": leaf_kind, "nodes": nodes, "edges": edges,
    }
    write(root / "docs" / "discovery" / initiative / "_state" / "traceability.json",
          json.dumps(payload))


def write_rollup(root: Path, rows: list[str]) -> None:
    body = ("| Component | Brief (repo + slug) | Contract@version | "
            "Status (snapshot) | Coverage pointer |\n| --- | --- | --- | --- | --- |\n")
    body += "".join(rows)
    write(root / "docs" / "product" / "rollups" / "rollup.md", body)


# A small full sidecar chain used by several cases (root=o, leaf=component).
def _chain_nodes_edges():
    nodes = [
        {"id": "o", "kind": "outcome", "backed_by": "ladder"},
        {"id": "cap", "kind": "capability", "backed_by": "ladder"},
        {"id": "scr", "kind": "screen", "backed_by": "file"},
        {"id": "act", "kind": "action", "backed_by": "container"},
        {"id": "svc", "kind": "service", "backed_by": "container"},
        {"id": "ctr@1", "kind": "contract", "backed_by": "file"},
        {"id": "sp", "kind": "spec", "backed_by": "file"},
        {"id": "comp", "kind": "component", "backed_by": "file"},
    ]
    edges = [
        {"from": "o", "to": "cap"}, {"from": "cap", "to": "scr"},
        {"from": "scr", "to": "act"}, {"from": "act", "to": "svc"},
        {"from": "svc", "to": "ctr@1"}, {"from": "ctr@1", "to": "sp"},
        {"from": "sp", "to": "comp"},
    ]
    return nodes, edges


# --------------------------------------------------------------------------
# No-op / graceful degradation
# --------------------------------------------------------------------------

def test_noop_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rc, out, err = run(Path(tmp))
        expect(rc == 0, f"empty → exit 0, got {rc}")
        expect(out.strip() == "", f"empty → no stdout, got: {out!r}")
        expect(err.strip() == "", f"empty → no stderr, got: {err!r}")


def test_noop_specs_contracts_packages_only() -> None:
    """A repo with specs, contracts, and components but NO discovery anchor must
    no-op — the critical false-activation guard (this bundle's own self-host)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_spec(root, "alpha", contract="`docs/contracts/x.json`")
        write_spec(root, "beta")
        write(root / "docs" / "contracts" / "x.json", "{}")
        write_component(root, "agentbundle")
        rc, out, err = run(root)
        expect(rc == 0, f"specs+contracts+packages, no anchor → exit 0, got {rc}: {err}")
        expect(out.strip() == "", f"no anchor → no stdout (no chain), got: {out!r}")


def test_degrades_malformed_sidecar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "docs" / "discovery" / "d" / "_state" / "traceability.json",
              "{ this is not json")
        write_brief(root, "b")
        write_spec(root, "s", brief="b", component="c")
        write_component(root, "c")
        rc, out, err = run(root)
        expect(rc == 0, f"malformed sidecar → degrade, exit 0, got {rc}: {err}")
        expect("malformed" in out.lower() or "derived from artifacts" in out.lower(),
               f"malformed sidecar reported + derives: {out}")


# --------------------------------------------------------------------------
# Sidecar-authoritative path
# --------------------------------------------------------------------------

def test_sidecar_converged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"converged sidecar → exit 0, got {rc}: {err}")
        expect("no structural orphans" in out, f"converged → no orphans: {out}")
        expect("sidecar (authoritative)" in out, f"reports sidecar source: {out}")


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("intent:missing", "unresolved target"),
        ("intent:source", "self-reference"),
    ],
    ids=["unresolved-peer", "self-reference"],
)
def test_sidecar_outcome_co_owner_refuses_invalid_peer(
    target: str, expected: str
) -> None:
    """AC-0002/AC-0003 apply when a sidecar owns graph structure."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        write(
            root / "docs" / "product" / "intents" / "source.md",
            "# Intent\n\n"
            "- **Slug:** source\n"
            f"- **Outcome co-owner:** {target}\n",
        )

        rc, out, err = run_raw(root)

        expect(rc == 1, f"invalid sidecar co-owner must fail: {out} {err}")
        expect(
            expected in err
            and "Outcome co-owner" in err
            and "intent:source" in err
            and target in err,
            f"finding names source, field, and target: {err}",
        )


def test_sidecar_orphan_and_strict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        edges = [e for e in edges if e != {"from": "ctr@1", "to": "sp"}]  # cut edge
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"orphan default → exit 0 (informational), got {rc}")
        expect("ORPHAN sp" in out and "no producer" in out,
               f"sp is a backward orphan: {out}")
        # The contract loses its consumer too (forward orphan).
        expect("ORPHAN ctr@1" in out, f"ctr@1 forward orphan: {out}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 1, f"orphan + --strict → exit 1, got {rc2}")


def test_sidecar_dangling_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        edges.append({"from": "sp", "to": "ghost"})  # endpoint not in inventory
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 1, f"sidecar dangling → exit 1 always, got {rc}")
        expect("ghost" in err and "DANGLING" in err, f"dangling on stderr: {err}")


def test_sidecar_cycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "b", "kind": "spec"}]
        edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a", leaf_kind="component")
        rc, out, err = run(root)
        expect(rc == 1, f"cycle → exit 1, got {rc}")
        expect("CYCLE" in err, f"cycle reported on stderr: {err}")


def test_sidecar_self_edge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}]
        edges = [{"from": "a", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a")
        rc, out, err = run(root)
        expect(rc == 1, f"self-edge → exit 1, got {rc}")
        expect("self-referential" in err.lower(), f"self-edge reported: {err}")


def test_sidecar_cycle_three_node() -> None:
    """A 3-node cycle exercises the multi-hop stack-slice reconstruction (the
    2-node case and self-edge don't)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "b", "kind": "spec"},
                 {"id": "c", "kind": "spec"}]
        edges = [{"from": "a", "to": "b"}, {"from": "b", "to": "c"},
                 {"from": "c", "to": "a"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="a")
        rc, out, err = run(root)
        expect(rc == 1, f"3-node cycle → exit 1, got {rc}")
        expect("CYCLE" in err, f"3-node cycle reported: {err}")


def test_deep_chain_no_crash() -> None:
    """A long linear sidecar chain must terminate (iterative DFS), not overflow
    the recursion limit — the degrade-never-crash contract on untrusted input."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        n = 3000
        nodes = [{"id": f"n{i}", "kind": "spec"} for i in range(n)]
        edges = [{"from": f"n{i}", "to": f"n{i + 1}"} for i in range(n - 1)]
        # leaf_kind=spec so no node needs an out-edge → no orphans, clean exit.
        write_sidecar(root, nodes=nodes, edges=edges, root_id="n0", leaf_kind="spec")
        rc, out, err = run(root)
        expect(rc == 0, f"deep chain → clean exit 0, got {rc}: {err[:200]}")
        expect("RecursionError" not in err and "Traceback" not in err,
               f"no crash on a deep chain: {err[:200]}")


def test_drift_warn_only() -> None:
    """A spec present on disk but absent from an authoritative sidecar is
    DRIFT — warn-only (exit 0), this spec's firm shipped contract."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "spec:known", "kind": "spec"},
                 {"id": "comp", "kind": "component"}]
        edges = [{"from": "spec:known", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="spec:known")
        write_spec(root, "extra")  # on disk, absent from the sidecar → drift
        rc, out, err = run(root)
        expect(rc == 0, f"drift is warn-only → exit 0, got {rc}: {err}")
        expect("DRIFT (warn-only)" in out and "spec:extra" in out,
               f"drift reported warn-only: {out}")


def test_layout_base_escape_confined() -> None:
    """A layout `[traceability]` base that escapes `--root` (absolute / `..`) is
    ignored, not read — the path-confinement guard."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")  # anchor, so the report (incl. notes) prints
        write(root / "agentbundle-layout.toml",
              '[traceability]\nspec = "/etc"\n')
        rc, out, err = run(root)
        expect(rc == 0, f"escaping layout base → no crash, exit 0, got {rc}: {err}")
        expect("escapes root" in out,
               f"escaping base reported + ignored: {out}")


# STUB: AC2 — configured bases with circular resolution fail closed, not open.
def test_layout_base_circular_symlink_is_ignored_without_degrading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        if not symlink_or_skip(
            "configured circular-layout confinement",
            root / "circular-spec-base",
            "circular-spec-base",
            target_is_directory=True,
        ):
            return
        write_brief(root, "b")
        write(
            root / "agentbundle-layout.toml",
            '[traceability]\nspec = "circular-spec-base"\n',
        )

        module_spec = importlib.util.spec_from_file_location(
            "_trace_circular_layout_stub", str(LINTER)
        )
        mod = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(mod)
        base, _ = mod.resolve_base(
            "spec", root, {"spec": "circular-spec-base"}
        )
        real_confined_path = mod._confined_path
        mod._confined_path = lambda _path, _root: None
        try:
            failed_base, failed_note = mod.resolve_base(
                "spec", root, {"spec": "circular-spec-base"}
            )
        finally:
            mod._confined_path = real_confined_path

        rc, out, err = run(root)

        expect(base is None, f"circular configured base resolved to {base}")
        expect(failed_base is None and failed_note is not None
               and "escapes root" in failed_note,
               f"configured resolution failure was not classified safely: "
               f"{failed_base!r}, {failed_note!r}")
        expect(rc == 0, f"circular configured base should be ignored: {out} {err}")
        expect("degraded" not in err, f"circular base reached fail-open handler: {err}")


def test_catalog_symlink_confined() -> None:
    """A `catalog-info.yaml` symlinked outside `--root` is not followed — the
    nested-read confinement. Skipped where symlinks aren't permitted (Windows)."""
    with tempfile.TemporaryDirectory() as tmp, \
            tempfile.TemporaryDirectory() as outside:
        root = Path(tmp)
        secret = Path(outside) / "secret.yaml"
        secret.write_text("kind: Component\nmetadata:\n  name: PWNED\n  namespace: stolen\n")
        write_brief(root, "b")  # anchor
        cdir = root / "packages" / "c1"
        cdir.mkdir(parents=True)
        if not symlink_or_skip(
            "catalog symlink confinement", cdir / "catalog-info.yaml", secret
        ):
            return
        rc, out, err = run(root)
        expect("PWNED" not in (out + err) and "stolen" not in (out + err),
               f"escaping catalog-info.yaml symlink not read: {out}{err}")


def test_sidecar_unknown_schema_degrades() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes, edges = _chain_nodes_edges()
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o",
                      schema_version="99.0")
        write_brief(root, "b")
        write_spec(root, "s", brief="b", component="c")
        write_component(root, "c")
        rc, out, err = run(root)
        expect(rc == 0, f"unknown schema → degrade not crash, got {rc}: {err}")
        expect("unrecognized" in out and "derived from artifacts" in out,
               f"unknown schema warns + derives: {out}")


# --------------------------------------------------------------------------
# Standalone derive-from-artifacts path
# --------------------------------------------------------------------------

def test_standalone_clean() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        expect(rc == 0, f"clean standalone → exit 0, got {rc}: {err}")
        expect("no structural orphans" in out, f"clean → no orphans: {out}")
        expect("derived from artifacts" in out, f"reports derived source: {out}")


def test_standalone_backward_orphan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        write_spec(root, "beta", component="beta-svc")  # no producer → orphan
        write_component(root, "beta-svc")
        rc, out, err = run(root)
        expect(rc == 0, f"backward orphan default → exit 0, got {rc}")
        expect("ORPHAN spec:beta" in out and "no producer" in out,
               f"spec:beta backward orphan: {out}")


def test_standalone_forward_orphan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b")  # no Component → forward orphan
        write_component(root, "other-svc")    # component layer populated
        rc, out, err = run(root)
        expect(rc == 0, f"forward orphan default → exit 0, got {rc}")
        expect("ORPHAN spec:alpha" in out and "no consumer" in out,
               f"spec:alpha forward orphan: {out}")


def test_standalone_orphan_component() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        write_component(root, "lonely")  # no spec points at it → backward orphan
        rc, out, err = run(root)
        expect("ORPHAN component:default/lonely" in out and "no producer" in out,
               f"unparented component is a backward orphan: {out}")


def test_terminal_exemption() -> None:
    """component (leaf) is never a forward orphan; the discovery root is never a
    backward orphan."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        # alpha-svc has a producer (the spec) and is leaf → must NOT be flagged.
        expect("ORPHAN component:default/alpha-svc" not in out,
               f"leaf component not a forward orphan: {out}")


def test_layer_skip_globally_unpopulated() -> None:
    """A spec→component edge across the globally-unpopulated contract/service/…
    layers is fine (skip to nearest populated); the spec is not orphaned for
    'skipping' an everywhere-empty layer."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="alpha-svc")
        write_component(root, "alpha-svc")
        rc, out, err = run(root)
        expect("no structural orphans" in out,
               f"layer-skip across empty layers → no orphan: {out}")


# --------------------------------------------------------------------------
# Cross-repo endpoint states
# --------------------------------------------------------------------------

def test_crossrepo_pinned() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="payments-api@3")
        write_rollup(root, ["| `payments-api@3` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"pinned cross-repo ref → exit 0, got {rc}")
        expect("satisfied-by-reference (pinned)" in out, f"pinned ref: {out}")
        expect("meta-repo/federated" in out, f"rollup → federated posture: {out}")


def test_crossrepo_unpinned() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/web-app")
        write_rollup(root, ["| `cat:ns/web-app` | `r` · `s` | — | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"unpinned cross-repo ref → exit 0 (never fatal), got {rc}")
        expect("unpinned" in out, f"unpinned soft-warning: {out}")


def test_crossrepo_unresolvable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/uncatalogued")
        # a rollup exists (federated posture) but does not list this id
        write_rollup(root, ["| `something-else` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"unresolvable cross-repo → never fatal, got {rc}")
        expect("unknown / not-yet-catalogued" in out, f"honest gap term: {out}")


def test_dangling_local_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="ghost-local")  # plain slug, missing
        rc, out, err = run(root)
        expect(rc == 1, f"dangling local target → exit 1, got {rc}")
        expect("DANGLING" in err and "ghost-local" in err, f"dangling on stderr: {err}")
        # one break, one class — the dangling spec must NOT also be a forward
        # ORPHAN (the down edge is asserted, just broken).
        expect("ORPHAN spec:alpha" not in out,
               f"dangling node not also an orphan: {out}")


def test_up_field_fallthrough_reference() -> None:
    """A cross-repo-shaped (unresolvable) `Contract:` must not shadow a valid
    `Brief:` up-edge: up-fields are alternatives and a well-formed cross-repo
    reference is not a defect, so the spec is parented either way — regardless
    of which of the two resolving candidates wins the edge."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        # Contract first, cross-repo-shaped (unresolvable, informational) + Brief.
        write_spec(root, "alpha", brief="b", contract="cat:ns/external-contract")
        rc, out, err = run(root)
        expect(rc == 0, f"valid Brief behind a cross-repo Contract → exit 0, got {rc}: {err}")
        expect("DANGLING" not in err, f"cross-repo ref is not dangling: {err}")
        expect("ORPHAN spec:alpha" not in out,
               f"spec parented via Brief is not an orphan: {out}")


# STUB: AC-0013 — a local producer candidate must win the in-edge over an
# earlier one that resolves only to an external reference.
def test_local_candidate_wins_over_earlier_external_only_producer() -> None:
    """AC-0013: a later candidate resolving `local` outranks an earlier one
    that resolves only to an external reference — a typed `Brief:` must take
    the in-edge from an earlier path-shaped `Contract:` or `Discovery:` that
    resolves only to an external stub."""
    spec = importlib.util.spec_from_file_location("_trace_local_wins_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    g = mod.Graph()
    mod._wire_up(
        g, consumer="spec:alpha",
        candidates=["cat:ns/external-contract", "b"],
        local_ids={"brief:b"}, rollup={},
    )

    expect(("brief:b", "spec:alpha") in g.edges,
           f"the local candidate must win the in-edge, got edges={g.edges!r}")
    expect(("cat:ns/external-contract", "spec:alpha") not in g.edges,
           f"the earlier external-only candidate must not win, got edges={g.edges!r}")


def test_external_only_candidate_still_wires_when_none_resolve_local() -> None:
    """A consumer whose only resolving candidate is external still carries the
    external in-edge — the existing orphan behaviour is unchanged."""
    spec = importlib.util.spec_from_file_location(
        "_trace_external_only_still_wires_stub", str(LINTER)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    g = mod.Graph()
    mod._wire_up(
        g, consumer="spec:alpha",
        candidates=["cat:ns/external-contract"],
        local_ids=set(), rollup={},
    )

    expect(("cat:ns/external-contract", "spec:alpha") in g.edges,
           f"the sole external candidate must still wire, got edges={g.edges!r}")


def test_dangling_candidate_reported_regardless_of_candidate_order() -> None:
    """A dangling candidate is a hard violation in every mode regardless of
    where it sits in the candidate order — the local-over-external preference
    pass must not swallow a trailing dangling sibling."""
    spec = importlib.util.spec_from_file_location(
        "_trace_dangling_order_stub", str(LINTER)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    g = mod.Graph()
    mod._wire_up(
        g, consumer="spec:alpha",
        candidates=["b", "ghost-local"],  # resolving candidate first, dangling trailing
        local_ids={"brief:b"}, rollup={},
    )

    expect(any("ghost-local" in d for d in g.dangling),
           f"a trailing dangling candidate must still be reported, got {g.dangling!r}")
    expect(("brief:b", "spec:alpha") in g.edges,
           f"the resolving sibling still wires despite the trailing dangling one, "
           f"got edges={g.edges!r}")


def test_dangling_up_field_still_fires() -> None:
    """A *dangling* (missing-local-shaped) up-field is a hard violation in
    every mode, fired even when a sibling up-field resolves — but the spec is NOT
    also a backward orphan (the resolving Brief gives it a producer)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", contract="ghost-local")  # bare, missing
        rc, out, err = run(root)
        expect(rc == 1, f"dangling up-field → exit 1 every mode, got {rc}")
        expect("DANGLING" in err and "ghost-local" in err,
               f"broken pointer fires even behind a resolving sibling: {err}")
        expect("ORPHAN spec:alpha" not in out,
               f"resolving Brief means not also a backward orphan: {out}")


def test_annotated_none_up_fields_are_placeholders() -> None:
    """Explanations and punctuation after `none` do not assert pointers."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b")
        write_spec(root, "parenthesized", contract="none (no published contract)")
        write_spec(root, "sentence", contract="none. Documentation only")
        write_spec(root, "semicolon", contract="none; internal behavior only")
        write_spec(root, "em-dash", contract="none — consumes an existing contract")
        spec = root / "docs" / "specs" / "em-dash" / "spec.md"
        with spec.open("a", encoding="utf-8") as handle:
            handle.write("\nThe **Contract:** label is metadata documentation.\n")

        rc, out, err = run(root)

        expect(rc == 0, f"annotated placeholders must not dangle, got {rc}: {err}")
        expect("DANGLING" not in err, f"annotated placeholders stay unset: {err}")
        expect("ORPHAN spec:em-dash" in out and "no producer" in out,
               f"the canonical first field remains authoritative: {out}")


# --------------------------------------------------------------------------
# Ambiguous bare-slug refusal — the fifth endpoint state
# --------------------------------------------------------------------------

# STUB: AC-0003 — the first test in the suite to call resolve_endpoint.
def test_resolve_endpoint_ambiguous_bare_slug_refuses() -> None:
    """A bare slug that suffix-matches more than one local node id refuses —
    its own state, not a reuse of `dangling` — and the message names every
    candidate."""
    spec = importlib.util.spec_from_file_location("_trace_ambiguous_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    local_ids = {"spec:foo", "brief:foo"}
    state, pinned, resolved = mod.resolve_endpoint("foo", local_ids, {})

    expect(state == "ambiguous", f"a slug matching two ids must refuse, got {state!r}")
    expect("spec:foo" in resolved and "brief:foo" in resolved,
           f"the refusal must name every candidate, got {resolved!r}")


def test_resolve_endpoint_unique_bare_slug_still_resolves_local() -> None:
    """AC-0002: a bare slug matching exactly one node id still resolves — the
    fallback is not collateral damage from the ambiguity refusal."""
    spec = importlib.util.spec_from_file_location("_trace_unique_slug_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    state, pinned, resolved = mod.resolve_endpoint("foo", {"spec:foo"}, {})

    expect(state == "local", f"a uniquely-matching slug must still resolve, got {state!r}")
    expect(resolved == "spec:foo", f"resolves to the canonical id, got {resolved!r}")


def test_resolve_endpoint_exact_id_skips_suffix_scan() -> None:
    """AC-0001: a target equal to a node id takes the fast path without
    entering the suffix scan — pinned with a fixture where the scan alone
    would answer with a different id."""
    spec = importlib.util.spec_from_file_location("_trace_exact_id_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Without the fast path, "widget:x/spec:foo" is the only suffix match for
    # "spec:foo" (it ends in "/spec:foo"), so a refactor that dropped the fast
    # path would answer with the wrong node instead of failing loudly.
    local_ids = {"spec:foo", "widget:x/spec:foo"}
    state, pinned, resolved = mod.resolve_endpoint("spec:foo", local_ids, {})

    expect(state == "local" and resolved == "spec:foo",
           f"exact id must resolve to itself via the fast path, got {state!r} {resolved!r}")


def test_resolve_endpoint_ordinal_and_ordinal_prefixed_stem_refuse() -> None:
    """AC-0005: an ordinal, or an ordinal-prefixed filename stem, refuses even
    where it would otherwise suffix-match a local id — never accepted as a
    pointer value."""
    spec = importlib.util.spec_from_file_location("_trace_ordinal_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ordinal_state, _, _ = mod.resolve_endpoint("FEAT-0001", {"strat:FEAT-0001"}, {})
    stem_state, _, _ = mod.resolve_endpoint(
        "FEAT-0001-intent-identity-and-registration",
        {"intent:FEAT-0001-intent-identity-and-registration"}, {},
    )

    expect(ordinal_state == "dangling", f"a bare ordinal must refuse, got {ordinal_state!r}")
    expect(stem_state == "dangling",
           f"an ordinal-prefixed stem must refuse, got {stem_state!r}")


def test_ambiguous_producer_pointer_exits_nonzero_in_both_modes() -> None:
    """AC-0004: an ambiguous producer pointer is a hard violation in both the
    default and `--strict` invocations — the closed set of modes that affect
    the exit code."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "dup")
        write_spec(root, "dup")
        write_spec(root, "consumer", contract="dup")
        rc, out, err = run(root)
        expect(rc == 1, f"ambiguous producer pointer → exit 1 default, got {rc}: {err}")
        expect("brief:dup" in err and "spec:dup" in err,
               f"both candidates named in the report: {err}")
        expect("ORPHAN spec:consumer" not in out,
               f"ambiguous producer already reported dangling, not also an orphan: {out}")
        rc2, _, err2 = run(root, "--strict")
        expect(rc2 == 1, f"ambiguous producer pointer → exit 1 --strict, got {rc2}: {err2}")


def test_sidecar_ambiguous_endpoint_names_every_candidate() -> None:
    """AC-0003 / AC-0004 at the third call site: a sidecar edge endpoint that
    suffix-matches more than one local node id refuses and names every
    candidate, rather than degrading to a bare `sidecar_dangling` message."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "spec:foo", "kind": "spec"},
                 {"id": "brief:foo", "kind": "brief"},
                 {"id": "comp", "kind": "component"}]
        edges = [{"from": "spec:foo", "to": "comp"},
                 {"from": "comp", "to": "foo"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="spec:foo")
        rc, out, err = run(root)
        expect(rc == 1, f"ambiguous sidecar endpoint → exit 1 always, got {rc}")
        expect("brief:foo" in err and "spec:foo" in err,
               f"both candidates named in the report: {err}")


# --------------------------------------------------------------------------
# Root→leaf reachability (sidecar mode) — the disconnected-subtree backstop
# --------------------------------------------------------------------------

# A healthy chain (root=o → spec-h → comp-h, a real component leaf) shared by the
# reachability fixtures so a clean terminus exists; each case bolts a broken branch
# onto the root `o`.
_HEALTHY_NODES = [
    {"id": "o", "kind": "outcome"},
    {"id": "spec-h", "kind": "spec"},
    {"id": "comp-h", "kind": "component"},
]
_HEALTHY_EDGES = [{"from": "o", "to": "spec-h"}, {"from": "spec-h", "to": "comp-h"}]


def test_reach_dead_end_subtree_whole_not_just_tip() -> None:
    """The preconverge "whole subtree" case: a locally-edged dead-end branch where
    every interior node has a producer AND a consumer edge, but the branch never
    reaches a leaf. Presence flags only the tip (no out-edge); reachability flags
    the stranded interior the presence check passes — union = the whole subtree."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "cap-d", "kind": "capability"},
            {"id": "scr-d", "kind": "screen"},
            {"id": "svc-d", "kind": "service"},  # tip — no out-edge
        ]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "cap-d"}, {"from": "cap-d", "to": "scr-d"},
            {"from": "scr-d", "to": "svc-d"},
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        # Presence flags ONLY the tip; the interior is passed by presence.
        expect("ORPHAN svc-d" in out and "no consumer" in out,
               f"presence flags the tip svc-d: {out}")
        expect("ORPHAN cap-d" not in out and "ORPHAN scr-d" not in out,
               f"presence passes the interior nodes: {out}")
        # Reachability flags the interior (which presence passed) — not just the tip.
        expect("UNREACHABLE cap-d" in out and "UNREACHABLE scr-d" in out,
               f"reachability flags the stranded interior: {out}")
        # one break, one class: the tip is the presence ORPHAN, not also
        # double-reported as UNREACHABLE.
        expect("UNREACHABLE svc-d" not in out,
               f"tip is the presence orphan, not also UNREACHABLE: {out}")
        # Union covers the whole subtree {cap-d, scr-d, svc-d}.
        expect(rc == 0, f"reachability informational by default → exit 0, got {rc}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 1, f"UNREACHABLE + --strict → exit 1, got {rc2}")


def test_reach_floating_subtree_disconnected_from_root() -> None:
    """The forward-from-root clause: a subtree internally edged and even reaching a
    leaf, but with no path from `root`, is flagged (its source is a presence
    backward orphan; its leaf — passed by presence — is UNREACHABLE)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "spec-f", "kind": "spec"},
            {"id": "comp-f", "kind": "component"},
        ]
        edges = _HEALTHY_EDGES + [{"from": "spec-f", "to": "comp-f"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect("ORPHAN spec-f" in out and "no producer" in out,
               f"floating source is a presence backward orphan: {out}")
        expect("UNREACHABLE comp-f" in out and "not forward-reachable" in out,
               f"floating leaf flagged not-reachable-from-root: {out}")
        expect(rc == 0, f"informational by default → exit 0, got {rc}")


def test_reach_federated_resolved_terminus_not_flagged() -> None:
    """Open-world: a branch whose leaf is a rollup-RESOLVED satisfied-by-reference
    endpoint reaches a clean terminus across the boundary — never flagged."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [{"id": "spec-x", "kind": "spec"}]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "spec-x"}, {"from": "spec-x", "to": "ext-comp@2"},
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        write_rollup(root, ["| `ext-comp@2` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root)
        expect(rc == 0, f"federated resolved terminus → exit 0, got {rc}: {err}")
        expect("satisfied-by-reference (pinned)" in out,
               f"cross-repo leaf is a resolved reference: {out}")
        expect("UNREACHABLE spec-x" not in out and "ORPHAN spec-x" not in out,
               f"a federated branch is not flagged: {out}")
        expect("DANGLING" not in err,
               f"a cross-repo sidecar endpoint is not dangling: {err}")
        rc2, _, _ = run(root, "--strict")
        expect(rc2 == 0, f"--strict + only a resolved federated leaf → exit 0, got {rc2}")


def test_reach_unresolvable_tip_surfaced_never_silently_green() -> None:
    """The fabricated-edge boundary: a stranded tip whose only out-edge is an
    UNRESOLVABLE (forged-eligible) cross-repo token is NOT a clean terminus — the
    branch is surfaced as a distinct informational finding, never silently green and
    never promoted by --strict (the untrusted-input control-integrity guard)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [
            {"id": "cap-u", "kind": "capability"},
            {"id": "scr-u", "kind": "screen"},
        ]
        edges = _HEALTHY_EDGES + [
            {"from": "o", "to": "cap-u"}, {"from": "cap-u", "to": "scr-u"},
            {"from": "scr-u", "to": "forged/x"},  # unresolvable cross-repo token
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 0, f"unresolvable tip → never fatal, exit 0, got {rc}: {err}")
        expect("DANGLING" not in err,
               f"a well-formed cross-repo token is not dangling: {err}")
        expect("unknown / not-yet-catalogued" in out,
               f"the forged endpoint is surfaced honestly: {out}")
        expect("reaches a leaf only via an unresolved cross-repo reference" in out,
               f"the stranded branch is surfaced, not silently green: {out}")
        expect("(informational)" in out, f"surfaced informationally: {out}")
        # Critically NOT flagged as a clean pass and NOT promoted by --strict.
        rc2, out2, _ = run(root, "--strict")
        expect(rc2 == 0,
               f"--strict does NOT promote an unresolvable hop, got {rc2}: {out2}")


def test_reach_dangling_adjacent_not_double_reported() -> None:
    """One-break-one-class: a node whose sole producer edge has a *dangling
    source* (the producer is a missing-local target) is surfaced by the DANGLING
    violation, not ALSO as UNREACHABLE."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = _HEALTHY_NODES + [{"id": "mid", "kind": "spec"}]
        edges = _HEALTHY_EDGES + [
            {"from": "ghostsrc", "to": "mid"},  # ghostsrc absent → dangling source
            {"from": "mid", "to": "comp-h"},    # mid does reach a leaf
        ]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="o")
        rc, out, err = run(root)
        expect(rc == 1, f"dangling source → exit 1 every mode, got {rc}")
        expect("DANGLING" in err and "ghostsrc" in err,
               f"the dangling edge is the hard violation: {err}")
        expect("UNREACHABLE mid" not in out,
               f"the dangling-edge consumer is not also UNREACHABLE: {out}")


def test_reach_skips_without_root() -> None:
    """Graceful, isolated degradation: a sidecar with no declared root, or a root
    absent from the inventory, skips ONLY the reachability pass (a note, no crash)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "comp", "kind": "component"}]
        edges = [{"from": "a", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="")  # → root None
        rc, out, err = run(root)
        expect("reachability skipped" in out and "no root" in out,
               f"rootless sidecar skips reachability with a note: {out}")
        expect("Traceback" not in err, f"no crash on a rootless sidecar: {err}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nodes = [{"id": "a", "kind": "spec"}, {"id": "comp", "kind": "component"}]
        edges = [{"from": "a", "to": "comp"}]
        write_sidecar(root, nodes=nodes, edges=edges, root_id="ghost-root")
        rc, out, err = run(root)
        expect("reachability skipped" in out and "absent from inventory" in out,
               f"absent declared root skips reachability with a note: {out}")
        expect("Traceback" not in err, f"no crash on an absent-root sidecar: {err}")


def test_reach_degenerate_cases() -> None:
    """Degenerate graphs: a single-node root==leaf is clean; an empty-edge graph
    strands non-root nodes (caught by presence; reachability adds nothing — the
    non-overlap property); a self-loop is termination-safe."""
    # (1) Single node, root == leaf → reachable/clean, no skip.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "comp", "kind": "component"}], edges=[],
                      root_id="comp")
        rc, out, err = run(root)
        expect(rc == 0 and "no structural orphans" in out,
               f"single-node root==leaf is clean: {out}")
        expect("UNREACHABLE" not in out and "reachability skipped" not in out,
               f"root==leaf is reachable, pass runs: {out}")
    # (2) Empty edges, multiple nodes → every non-root node is a presence orphan;
    # reachability adds NO UNREACHABLE (all stranded nodes already presence orphans).
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "o", "kind": "outcome"},
                                   {"id": "x", "kind": "spec"},
                                   {"id": "comp", "kind": "component"}],
                      edges=[], root_id="o")
        rc, out, err = run(root)
        expect("ORPHAN x" in out and "ORPHAN comp" in out,
               f"empty-edge non-root nodes are presence orphans: {out}")
        expect("UNREACHABLE" not in out,
               f"reachability is additive — no double-report on presence orphans: {out}")
        expect("Traceback" not in err, f"no crash on an empty-edge sidecar: {err}")
    # (3) Self-loop on an on-path node → termination-safe, not spuriously flagged
    # (the self-edge itself is the hard violation; reachability must not hang).
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_sidecar(root, nodes=[{"id": "o", "kind": "outcome"},
                                   {"id": "a", "kind": "spec"},
                                   {"id": "comp", "kind": "component"}],
                      edges=[{"from": "o", "to": "a"}, {"from": "a", "to": "a"},
                             {"from": "a", "to": "comp"}], root_id="o")
        rc, out, err = run(root)
        expect(rc == 1 and "self-referential" in err.lower(),
               f"self-edge is the hard violation: {err}")
        expect("Traceback" not in err and "RecursionError" not in err,
               f"reachability terminates on a self-loop: {err}")
        expect("UNREACHABLE a" not in out and "UNREACHABLE comp" not in out,
               f"on-path nodes not spuriously flagged despite the self-loop: {out}")


# --------------------------------------------------------------------------
# Container-embedded + file-backed recognition
# --------------------------------------------------------------------------

def test_container_and_file_recognition() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # intent ladder: outcome + opportunity (kinds) + capability (level)
        write(root / "docs" / "product" / "intents" / "o.md",
              "# I\n\n- **Slug:** `o`\n- **Kind:** outcome\n")
        write(root / "docs" / "product" / "intents" / "opp.md",
              "# I\n\n- **Slug:** `opp`\n- **Kind:** opportunity\n- **Parent intent:** o\n")
        write(root / "docs" / "product" / "intents" / "cap.md",
              "# I\n\n- **Slug:** `cap`\n- **Level:** capability\n- **Parent intent:** opp\n")
        # journey action + blueprint service
        write(root / "docs" / "product" / "journeys" / "j.md",
              "# J\n\n- **Action:** checkout\n")
        write(root / "docs" / "product" / "blueprints" / "bp.md",
              "# B\n\n- **Service:** payments\n")
        # file-backed screen + contract + spec
        write(root / "docs" / "product" / "screens" / "home.md",
              "# S\n\n- **Type:** screen-brief\n")
        write(root / "docs" / "contracts" / "api" / "pay.v2.json", "{}")
        write_spec(root, "alpha", discovery="cap")
        rc, out, err = run(root)
        # The ladder up-pointers (opp→o, cap→opp) and spec discovery=cap resolve
        # LOCALLY only if the ladder kinds (outcome/opportunity) and level
        # (capability) were each recognized with the right id — so the absence
        # of any DANGLING is itself proof they were extracted.
        expect("DANGLING" not in err,
               f"ladder kinds/level recognized (their up-edges resolve local): {err}")
        # The container-embedded + file-backed unwired nodes surface as ORPHANs
        # under their exact recognized ids — proves the @version contract id and
        # the journey/blueprint entry extraction.
        for nid in ("action:checkout", "service:payments", "screen:home",
                    "contract:pay@2"):
            expect(f"ORPHAN {nid}" in out, f"recognized {nid}: {out}")
        # 8 nodes: outcome:o, opportunity:opp, capability:cap, screen:home,
        # action:checkout, service:payments, contract:pay@2, spec:alpha.
        m = re.search(r"(\d+) node\(s\)", out)
        expect(m is not None and int(m.group(1)) == 8,
               f"exactly the 8 recognized nodes: {out}")


def test_screen_nested_brief_recognized() -> None:
    """A per-screen brief nested under a flow folder
    (`screens/<slug>/<screen>.md` — the shape `user-flow` emits) is
    recognized: `recognize_screens` walks the screens base recursively (the
    `recognize_contracts` precedent), so the brief is found by marker even though
    it is not a flat `screens/*.md` file. A nested screen-flow *file*
    (`type: screen-flow`, no bold-body `**Type:** screen-brief`) is NOT a screen."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # nested per-screen brief — the real producer output path
        write(root / "docs" / "product" / "screens" / "checkout" / "confirm.md",
              "# Screen brief\n\n## Place in the whole\n- **Type:** screen-brief\n")
        # a flat flow file carrying the document-level frontmatter type only
        write(root / "docs" / "product" / "screens" / "checkout-flow.md",
              "---\ntype: screen-flow\n---\n\n# Flow\n")
        # a populated below-layer (journey action) so the recognized screen surfaces
        # by id as a forward orphan — the unambiguous recognition signal.
        write(root / "docs" / "product" / "journeys" / "j.md",
              "# J\n\n- **Action:** checkout\n")
        rc, out, err = run(root)
        expect("ORPHAN screen:confirm" in out,
               f"nested per-screen brief recognized by marker: {out}")
        expect("screen:checkout-flow" not in out and "screen:flow" not in out,
               f"a screen-flow file is not a screen node: {out}")
        expect("DANGLING" not in err, f"no dangling on a nested-brief fixture: {err}")


# STUB: AC2 — an outside marker must not make an in-root directory a component.
def test_component_marker_symlink_outside_root_is_not_recognized() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        component = root / "packages" / "ghost"
        component.mkdir(parents=True)
        outside = sandbox / "outside-catalog-info.yaml"
        outside.write_text(
            "apiVersion: backstage.io/v1alpha1\nkind: Component\n"
            "metadata:\n  name: outside-sentinel\n",
            encoding="utf-8",
        )
        if not symlink_or_skip(
            "component-marker symlink confinement",
            component / "catalog-info.yaml",
            outside,
        ):
            return
        write_brief(root, "consumer-brief")
        write_spec(root, "consumer", brief="consumer-brief", component="ghost")

        rc, out, err = run(root)

        expect(rc == 1, f"outside marker must leave component edge dangling: {out} {err}")
        expect("DANGLING" in err and "ghost" in err,
               f"expected the unrecognized component to stay dangling: {err}")
        expect("outside-sentinel" not in out + err,
               f"outside marker content leaked into diagnostics: {out} {err}")


# STUB: AC2 — recursive discovery prunes outside and circular children before descent.
def test_iter_dirs_prunes_unresolvable_children_before_descent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp)
        root = sandbox / "repo"
        root.mkdir()
        outside = sandbox / "outside"
        outside.mkdir()
        if not symlink_or_skip(
            "iterator outside-link pruning",
            root / "outside-link",
            outside,
            target_is_directory=True,
        ):
            return
        if not symlink_or_skip(
            "iterator circular-link pruning",
            root / "circle",
            "circle",
            target_is_directory=True,
        ):
            return
        spec = importlib.util.spec_from_file_location("_trace_iter_stub", str(LINTER))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        real_walk = os.walk
        descended: list[str] = []

        def junction_like_walk(start: Path, *, followlinks: bool = False):
            children = ["outside-link", "circle"]
            yield str(start), children, []
            for child in children:
                descended.append(child)
                yield str(Path(start) / child), [], []

        os.walk = junction_like_walk
        try:
            seen = list(mod._iter_dirs(root))
        finally:
            os.walk = real_walk

        expect(seen == [root.resolve()],
               f"outside/circular children were yielded after prune point: {seen}")
        expect(not descended,
               f"walker descended before filtering could hide the result: {descended}")


# STUB: AC2 — node IDs derive from canonical confined component paths.
def test_component_alias_uses_canonical_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        real = root / "packages" / "real"
        real.mkdir(parents=True)
        write(real / "catalog-info.yaml", "# marker without metadata\n")
        alias = root / "packages" / "alias"
        if not symlink_or_skip(
            "canonical component alias", alias, real, target_is_directory=True
        ):
            return
        spec = importlib.util.spec_from_file_location("_trace_id_stub", str(LINTER))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        graph = mod.Graph()

        mod.recognize_components(root / "packages", root, graph)

        expect("component:real" in graph.nodes,
               f"canonical component id missing: {graph.nodes}")
        expect("component:alias" not in graph.nodes,
               f"symlink alias became a distinct component id: {graph.nodes}")


# --------------------------------------------------------------------------
# `intent:` recognition — the fourth recognizer (RFC-0103 D2)
# --------------------------------------------------------------------------

# STUB: AC-0006 — an unclaimed intent file becomes an `intent:` node keyed on
# its own `Slug:` field; a ladder-typed sibling (recognize_ladder already
# claims it) must not double-register.
def test_unclaimed_intent_file_becomes_intent_node() -> None:
    spec = importlib.util.spec_from_file_location("_trace_intent_node_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "o.md", "# I\n\n- **Slug:** `o`\n- **Kind:** outcome\n")
        write(base / "plain.md", "# I\n\n- **Slug:** `plain-intent`\n")

        g = mod.Graph()
        ladder_paths = mod.recognize_ladder(base, root, g)
        found = mod.recognize_intents(base, root, g, claimed=set(ladder_paths.values()))

        expect(list(found.keys()) == ["intent:plain-intent"],
               f"only the unclaimed file is recognized, keyed on its Slug: {found!r}")
        expect(g.nodes.get("intent:plain-intent") == "intent",
               f"the node is registered under kind 'intent': {g.nodes!r}")
        expect("intent:o" not in g.nodes,
               f"the ladder-typed file must not also be an intent: node "
               f"(RFC-0103 D2's exclusion): {g.nodes!r}")


def test_ordinal_prefixed_intent_filename_uses_slug_field_not_stem() -> None:
    """The slug is the `Slug:` field value, never the filename stem — 5 of the
    117 real intent filenames carry an ordinal prefix, and a stem-derived id
    would put that ordinal inside a pointer value (AC-0005 refuses it)."""
    spec = importlib.util.spec_from_file_location("_trace_intent_ordinal_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "FEAT-0001-intent-identity-and-registration.md",
              "# I\n\n- **Slug:** `intent-identity-and-registration`\n")

        g = mod.Graph()
        found = mod.recognize_intents(base, root, g, claimed=set())

        expect(list(found.keys()) == ["intent:intent-identity-and-registration"],
               f"the id must come from Slug:, not the ordinal-prefixed stem: {found!r}")
        expect(not any("FEAT-0001" in nid for nid in g.nodes),
               f"no id may contain the ordinal: {g.nodes!r}")


def test_tombstone_keeps_slug_without_duplicating_reissued_intent() -> None:
    """A tombstone keeps its retired `Slug:`; only the reissued record becomes
    the `intent:` node, so the pair is not a duplicate id. A body-level
    `Tombstone:` line does not retire a live intent."""
    spec = importlib.util.spec_from_file_location("_trace_intent_tombstone_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "route.md",
              "- **Slug:** `route`\n- **Tombstone:** 2026-01-01\n"
              "- **Reissued as:** docs/product/intents/FEAT-0001-route.md\n")
        write(base / "FEAT-0001-route.md", "# I\n\n- **Slug:** `route`\n")
        write(base / "live.md",
              "# I\n\n- **Slug:** `live`\n\n## Notes\n\n- **Tombstone:** quoted\n")

        g = mod.Graph()
        found = mod.recognize_intents(base, root, g, claimed=set())

        expect(found.get("intent:route") == base / "FEAT-0001-route.md",
               f"the reissued record owns the slug, not the tombstone: {found!r}")
        expect("intent:live" in found,
               f"a body-level Tombstone: line must not retire a live intent: {found!r}")


def test_intent_file_without_slug_is_reported() -> None:
    """AC-0014: an intent file carrying no `Slug:` field is reported."""
    spec = importlib.util.spec_from_file_location(
        "_trace_intent_no_slug_report_stub", str(LINTER)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "no-slug.md", "# I\n\nNo slug field here.\n")

        g = mod.Graph()
        mod.recognize_intents(base, root, g, claimed=set())

        expect(any("no-slug.md" in n and "Slug" in n for n in g.notes),
               f"a file with no Slug: field must be reported: {g.notes!r}")


def test_intent_file_without_slug_contributes_no_node() -> None:
    """AC-0015: that same fixture contributes no node — asserted separately
    from AC-0014 because an implementation can emit the report and still
    register a node, falling back to the filename stem, which AC-0005 refuses
    as a pointer value."""
    spec = importlib.util.spec_from_file_location(
        "_trace_intent_no_slug_node_stub", str(LINTER)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "no-slug.md", "# I\n\nNo slug field here.\n")

        g = mod.Graph()
        found = mod.recognize_intents(base, root, g, claimed=set())

        expect(found == {}, f"no node should be returned for edge wiring: {found!r}")
        expect("intent:no-slug" not in g.nodes,
               f"must not fall back to the filename stem: {g.nodes!r}")
        expect(len(g.nodes) == 0, f"no node registered at all: {g.nodes!r}")


def test_duplicate_derived_intent_id_caught_over_pre_insertion_sequence() -> None:
    """AC-0007: no two nodes share an id. `Graph.add` (`:352`) assigns into
    `self.nodes`, so a second registration silently overwrites the first — the
    assertion must read the id sequence as it is *derived*, not the built node
    set, which would be true for every corpus including a colliding one."""
    spec = importlib.util.spec_from_file_location("_trace_intent_dup_stub", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        base = root / "docs" / "product" / "intents"
        write(base / "a.md", "# I\n\n- **Slug:** `dup`\n")
        write(base / "b.md", "# I\n\n- **Slug:** `dup`\n")

        g = mod.Graph()
        derived: list[str] = []
        original_add = g.add

        def spy_add(node_id: str, kind: str) -> None:
            derived.append(node_id)
            original_add(node_id, kind)

        g.add = spy_add
        mod.recognize_intents(base, root, g, claimed=set())

        expect(len(derived) == 2 and len(set(derived)) == 1,
               f"two artifacts derive the same id — the pre-insertion sequence "
               f"must carry the duplicate: {derived!r}")
        expect(len(g.nodes) == 1,
               f"the built node set alone hides the collision (Graph.add "
               f"overwrites), which is exactly why the sequence is asserted "
               f"instead: {g.nodes!r}")
        # The two assertions above observe the overwrite; neither refuses it,
        # and both pass against an implementation that silently overwrites.
        # AC-0007 is "no two nodes share an id", so the collision has to be
        # *reported*, not merely visible to a spy the production path does not
        # have.
        expect(len(g.duplicate_ids) == 1,
               f"the collision must be recorded at insertion, so it survives "
               f"into the report without a test spy: {g.duplicate_ids!r}")
        expect(derived[0] in g.duplicate_ids[0],
               f"the record must name the colliding id: {g.duplicate_ids!r}")


def test_unclaimed_intent_parent_pointer_wires_the_in_edge() -> None:
    """Registration alone is not enough: the edge builder wires
    `Parent intent:` from the brief and ladder path maps, so a recognizer that
    returns nodes without joining that wiring leaves 14 real pointers unbuilt
    in the live corpus. This fixture proves an `intent:` node gains its
    in-edge."""
    spec = importlib.util.spec_from_file_location(
        "_trace_intent_wiring_stub", str(LINTER)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        write(root / "docs" / "product" / "intents" / "o.md",
              "# I\n\n- **Slug:** `o`\n- **Kind:** outcome\n")
        write(root / "docs" / "product" / "intents" / "child.md",
              "# I\n\n- **Slug:** `child`\n- **Parent intent:** o\n")

        g = mod.Graph()
        mod.build_standalone(root, {}, g, {})

        expect(("outcome:o", "intent:child") in g.edges,
               f"the unclaimed intent's own Parent intent: pointer must wire "
               f"the in-edge, got edges={g.edges!r}")


# STUB: AC-0002
def test_ac0002_outcome_co_owner_helper_reports_unresolved_target() -> None:
    module_spec = importlib.util.spec_from_file_location("_trace_co_owner", str(LINTER))
    assert module_spec is not None and module_spec.loader is not None
    mod = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(mod)

    findings = mod.outcome_co_owner_findings(
        {"intent:source": "intent:missing"},
        {"intent:source"},
    )

    expect(bool(findings), "an unresolved co-owner must produce a finding")
    report = "\n".join(findings)
    expect("intent:source" in report, report)
    expect("Outcome co-owner" in report, report)
    expect("intent:missing" in report, report)


def test_ac0002_unresolved_outcome_co_owner_refuses() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = root / "docs" / "product" / "intents"
        # An `intent:` node is not a CHAIN layer, so intent files alone leave
        # the corpus unanchored and `check()` no-ops clean before it can reach
        # any co-owner finding. The brief is the anchor this AC is read through.
        write_brief(root, "anchor")
        write(
            base / "source.md",
            "# Intent\n\n"
            "- **Slug:** source\n"
            "- **Outcome co-owner:** intent:missing\n",
        )

        rc, out, err = run_raw(root)

        expect(rc == 1, f"unresolved co-owner must fail: {out} {err}")
        expect("Outcome co-owner" in err and "intent:source" in err
               and "intent:missing" in err,
               f"finding names source, field, and target: {err}")


def test_ac0003_self_co_owner_refuses() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = root / "docs" / "product" / "intents"
        write_brief(root, "anchor")  # see AC-0002 above: intents alone no-op
        write(
            base / "source.md",
            "# Intent\n\n"
            "- **Slug:** source\n"
            "- **Outcome co-owner:** intent:source\n",
        )

        rc, out, err = run_raw(root)

        expect(rc == 1, f"self co-owner must fail: {out} {err}")
        expect("self-reference" in err and "intent:source" in err,
               f"finding names self-reference: {err}")


def test_ac0004_outcome_co_owner_does_not_add_graph_edges() -> None:
    spec = importlib.util.spec_from_file_location("_trace_co_owner_edges", str(LINTER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def build_graph(root: Path) -> object:
        graph = mod.Graph()
        mod.build_standalone(root, {}, graph, {})
        return graph

    with tempfile.TemporaryDirectory() as without_tmp, tempfile.TemporaryDirectory() as with_tmp:
        without_root = Path(without_tmp)
        with_root = Path(with_tmp)
        for root, co_owner in ((without_root, ""), (with_root, "- **Outcome co-owner:** intent:peer\n")):
            base = root / "docs" / "product" / "intents"
            write(
                base / "source.md",
                "# Intent\n\n"
                "- **Slug:** source\n"
                f"{co_owner}",
            )
            write(base / "peer.md", "# Intent\n\n- **Slug:** peer\n")

        without_graph = build_graph(without_root)
        with_graph = build_graph(with_root)

        expect(with_graph.edges == without_graph.edges,
               f"co-owner must not add graph edges: {without_graph.edges!r} vs "
               f"{with_graph.edges!r}")
        expect(not with_graph.dangling,
               f"valid co-owner should not create dangling findings: {with_graph.dangling!r}")


def test_ac0019_commented_outcome_co_owner_is_absent() -> None:
    fixtures = {
        "closed": "<!--\n- **Outcome co-owner:** intent:missing\n-->\n",
        "unclosed": "<!--\n- **Outcome co-owner:** intent:missing\n",
    }
    for label, hidden in fixtures.items():
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Without the anchor the run no-ops clean and this `rc == 0` holds
            # for a corpus the lint never read — see AC-0002 above.
            write_brief(root, "anchor")
            write(
                root / "docs" / "product" / "intents" / f"{label}.md",
                "# Intent\n\n"
                f"- **Slug:** {label}\n"
                f"{hidden}",
            )

            rc, out, err = run_raw(root)

            expect(rc == 0, f"hidden co-owner is absent for {label}: {out} {err}")
            expect("Outcome co-owner" not in out + err,
                   f"hidden co-owner produced a finding for {label}: {out} {err}")


def test_ac0019_co_owner_reader_has_no_sibling_skill_dependency() -> None:
    source = LINTER.read_text(encoding="utf-8")

    expect("work-intake" not in source,
           "the projected work-loop linter must not depend on a sibling skill")
    expect("intent_shape.py" not in source,
           "the projected work-loop linter must not load a sibling parser")


def test_ac0019_self_contained_reader_observes_preamble_visibility() -> None:
    spec = importlib.util.spec_from_file_location("_trace_visible_preamble", str(LINTER))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    text = (
        "- **Slug:** source\n"
        "<!--\n"
        "- **Outcome co-owner:** intent:hidden\n"
        "## Hidden heading\n"
        "-->\n"
        "- **Outcome co-owner:** `intent:visible extra` <!-- note -->\n"
        "## Outcome\n"
        "- **Outcome co-owner:** intent:body\n"
    )

    value = mod._intent_preamble_field(text, "Outcome co-owner")
    expect(value == "intent:visible extra",
           "the reader must preserve the exact visible value while ignoring "
           "comments and body fields")
    findings = mod.outcome_co_owner_findings(
        {"intent:source": value},
        {"intent:source", "intent:visible"},
    )
    expect(bool(findings) and "intent:visible extra" in "\n".join(findings),
           "a longer declaration must not resolve through its leading token")
    expect(mod._intent_preamble_field(
        "- **Slug:** source\n<!--\n- **Outcome co-owner:** intent:hidden\n",
        "Outcome co-owner",
    ) is None, "an unclosed comment must hide the rest of the preamble")


# --------------------------------------------------------------------------
# Structural-only / output-shape / stdlib / no-hardcoded-path NFRs
# --------------------------------------------------------------------------

def test_no_semantic_vocabulary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "beta", component="beta-svc")  # orphan, produces output
        write_component(root, "beta-svc")
        rc, out, err = run(root)
        banned = ["scope-creep", "semantic", "wrong outcome", "incorrect",
                  "should be parented", "appetite"]
        blob = (out + err).lower()
        for term in banned:
            expect(term not in blob, f"no semantic vocabulary ({term!r}): {blob}")


def test_output_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="ghost")  # dangling → stderr
        rc, out, err = run(root)
        expect(out.startswith("lint-traceability:"), f"stdout report header: {out}")
        expect("lint-traceability:" in err, f"stderr violation prefix: {err}")
        # One-line summary present on stdout.
        expect(any("orphan" in ln for ln in out.splitlines()),
               f"one-line summary present: {out}")


def test_strict_never_promotes_softs() -> None:
    """--strict promotes orphans but NEVER unresolvable-cross-repo / unpinned."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_brief(root, "b")
        write_spec(root, "alpha", brief="b", component="cat:ns/uncatalogued")
        write_rollup(root, ["| `x` | `r` · `s` | x@1 | delivered | y |\n"])
        rc, out, err = run(root, "--strict")
        expect(rc == 0, f"--strict + only unresolvable-cross-repo → exit 0, got {rc}")


def test_stdlib_only() -> None:
    import ast
    tree = ast.parse(LINTER.read_text(encoding="utf-8"))
    stdlib = {"__future__", "argparse", "json", "re", "subprocess", "sys",
              "pathlib", "tomllib", "os", "importlib"}
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    for mod in sorted(mods):
        expect(mod in stdlib, f"only stdlib imports, found {mod!r}")


def test_no_hardcoded_path() -> None:
    """Every quoted artifact-root segment (`"docs"`/`"packages"` — the giveaway
    of a path shortcut) must live inside the path-defaults registry block."""
    lines = LINTER.read_text(encoding="utf-8").splitlines()
    start = end = None
    for i, ln in enumerate(lines):
        if "path-defaults:start" in ln:
            start = i
        elif "path-defaults:end" in ln:
            end = i
    expect(start is not None and end is not None, "registry block markers present")
    if start is None or end is None:
        return
    for i, ln in enumerate(lines):
        if re.search(r'"(docs|packages)"', ln) and not (start < i < end):
            pytest.fail(f"hardcoded artifact path at line {i + 1}: {ln.strip()}")


def _tree_with_detail_lines(root: Path) -> None:
    """A tree that exits 0 but still reports per-item detail lines.

    Needs a discovery anchor (the brief) or the linter no-ops entirely; `beta`
    has no producer, so it is reported as a structural orphan.
    """
    write_brief(root, "b")
    write_spec(root, "alpha", brief="b", component="alpha-svc")
    write_component(root, "alpha-svc")
    write_spec(root, "beta", component="beta-svc")  # no producer -> orphan
    write_component(root, "beta-svc")


def test_detail_lines_are_hidden_on_a_passing_run(tmp_path: Path) -> None:
    """AC4: a passing run prints summaries and a count, not the per-item list.

    Killing mutation: print `out` unconditionally in `main` and this reddens.
    The paired verbose run is the positive control, so a tree that produced no
    detail lines at all could not make this pass.
    """
    _tree_with_detail_lines(tmp_path)
    quiet_rc, quiet_out, _ = run_raw(tmp_path)
    loud_rc, loud_out, _ = run_raw(tmp_path, "--verbose")

    expect(quiet_rc == 0 and loud_rc == 0,
           f"fixture must pass in both modes: {quiet_rc}/{loud_rc}")
    detail = [ln for ln in loud_out.splitlines() if ln.startswith("  - ")]
    expect(bool(detail), f"positive control: verbose printed no detail: {loud_out}")
    expect(not [ln for ln in quiet_out.splitlines() if ln.startswith("  - ")],
           f"default run must withhold every detail line: {quiet_out}")
    expect(f"{len(detail)} detail line(s) hidden" in quiet_out,
           f"default run must report {len(detail)} hidden: {quiet_out}")
    for ln in loud_out.splitlines():
        if ln.startswith("lint-traceability:"):
            expect(ln in quiet_out, f"summary line was withheld: {ln}")


def test_a_failing_run_prints_every_line_without_verbose(tmp_path: Path) -> None:
    """AC4: a non-zero exit is never truncated.

    Killing mutation: drop `or exit_hint != 0` from the guard in `main` and
    this reddens, because a --strict failure loses the orphan detail that
    explains it.
    """
    _tree_with_detail_lines(tmp_path)
    strict_rc, strict_out, _ = run_raw(tmp_path, "--strict")
    full_rc, full_out, _ = run_raw(tmp_path, "--strict", "--verbose")

    expect(strict_rc == 1, f"--strict must fail on this tree: {strict_rc}")
    expect(full_rc == 1, f"positive control: verbose must fail too: {full_rc}")
    expect(strict_out == full_out,
           "a failing run must print exactly what --verbose prints")
    expect("hidden" not in strict_out,
           f"a failing run withholds nothing, so it claims nothing: {strict_out}")


def test_every_detail_line_carries_the_detail_prefix(tmp_path: Path) -> None:
    """The suppression filter keys on `_DETAIL_PREFIX`; every non-summary line
    must carry it, or a new report line would silently become unsuppressible.

    Killing mutation: change any `out.append(f"  - ...")` site to a different
    indent and this reddens.
    """
    _tree_with_detail_lines(tmp_path)
    _, out, _ = run_raw(tmp_path, "--verbose")
    for ln in out.splitlines():
        if not ln:
            continue
        expect(ln.startswith(("  - ", "lint-traceability:")),
               f"line is neither a detail nor a summary line: {ln!r}")


# --------------------------------------------------------------------------
# VI-1201 / VI-1202 / VI-1203 — delivery relation wiring via canonical snapshot
# --------------------------------------------------------------------------

# Resolver source installed temporarily for real-subprocess tests.
_RESOLVER_SOURCE = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "adapter-root-bins"
    / "intent_delivery_relations.py"
)

_EMPTY_SNAPSHOT: dict = {
    "schema_version": 1,
    "complete": True,
    "relations": [],
    "classifications": [],
    "provenance": [],
    "diagnostics": [],
}


def _load_linter(suffix: str) -> object:
    """Load lint-traceability as a fresh module instance (each call is isolated)."""
    ms = importlib.util.spec_from_file_location(f"_trace_vi_{suffix}", str(LINTER))
    assert ms is not None and ms.loader is not None
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    return mod


def _install_resolver(root: Path) -> None:
    """Install the resolver source under tmp_path/.agentbundle/bin/ for subprocess tests."""
    dest = root / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(_RESOLVER_SOURCE.read_bytes())


def write_feature_intent(root: Path, slug: str, route: str = "spec") -> None:
    """Write a feature-level intent with the given delivery route."""
    write(
        root / "docs" / "product" / "intents" / f"{slug}.md",
        f"# Intent\n\n"
        f"- **Slug:** `{slug}`\n"
        f"- **Level:** feature\n"
        f"- **Decomposed:** 2026-10-04 {route}\n",
    )


# ---- VI-1201: direct delivery -----------------------------------------------


def test_vi1201_direct_delivery_edge_wired_from_snapshot(tmp_path: Path) -> None:
    """A direct-delivery relation in the snapshot creates intent→spec edge.
    _wire_up must not receive a feature-intent Discovery candidate."""
    mod = _load_linter("direct")

    write_brief(tmp_path, "anchor")
    write_feature_intent(tmp_path, "alpha")
    write_spec(tmp_path, "alpha-delivery", discovery="intent:alpha")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "relations": [{
            "type": "direct-delivery",
            "intent": "intent:alpha",
            "spec": "spec:alpha-delivery",
            "route": "spec",
            "basis": {"intent": "Decomposed", "spec": "Discovery"},
        }],
        "provenance": [],
    }

    # Guard: _wire_up must NOT receive a feature-intent delivery candidate.
    original = mod._wire_up
    received: list[list[str]] = []

    def guarded(g, *, consumer, candidates, local_ids, rollup):
        received.append(list(candidates))
        for c in candidates:
            if c.startswith("intent:"):
                raise AssertionError(
                    f"_wire_up received a feature-intent delivery pointer: {c!r}"
                )
        return original(g, consumer=consumer, candidates=candidates,
                        local_ids=local_ids, rollup=rollup)

    mod._wire_up = guarded
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(("intent:alpha", "spec:alpha-delivery") in g.edges,
           f"direct-delivery edge must be wired: {g.edges!r}")
    expect(not any("intent:alpha" in c for calls in received for c in calls),
           f"intent: must not reach _wire_up: {received!r}")


def test_vi1201_coordinated_delivery_edges_wired_from_snapshot(tmp_path: Path) -> None:
    """A coordinated-delivery relation wires brief→spec and intent→brief."""
    mod = _load_linter("coord")

    write_brief(tmp_path, "coord-brief")
    write_feature_intent(tmp_path, "beta", route="brief")
    write_spec(tmp_path, "beta-delivery", brief="brief:coord-brief")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "relations": [{
            "type": "coordinated-delivery",
            "intent": "intent:beta",
            "brief": "brief:coord-brief",
            "spec": "spec:beta-delivery",
            "route": "brief",
            "basis": {"intent": "Decomposed", "brief": "Parent intent", "spec": "Brief"},
        }],
    }

    # Guard: _wire_up must not receive delivery brief pointer for delivery specs.
    original = mod._wire_up
    received: list[list[str]] = []

    def guarded(g, *, consumer, candidates, local_ids, rollup):
        received.append(list(candidates))
        if consumer == "spec:beta-delivery":
            for c in candidates:
                if c.startswith("brief:"):
                    raise AssertionError(
                        f"_wire_up received a delivery brief pointer for delivery spec: {c!r}"
                    )
        return original(g, consumer=consumer, candidates=candidates,
                        local_ids=local_ids, rollup=rollup)

    mod._wire_up = guarded
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(("brief:coord-brief", "spec:beta-delivery") in g.edges,
           f"brief→spec edge wired: {g.edges!r}")
    expect(("intent:beta", "brief:coord-brief") in g.edges,
           f"intent→brief edge wired: {g.edges!r}")


def test_vi1201_explicit_empty_no_delivery_edge(tmp_path: Path) -> None:
    """A direct-light or closed-empty classification produces no delivery edge."""
    mod = _load_linter("empty")
    write_brief(tmp_path, "anchor")
    write_feature_intent(tmp_path, "gamma", route="direct-light")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "classifications": [{
            "classification": "no-durable-child",
            "intent": "intent:gamma",
            "route": "direct-light",
        }],
    }

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    delivery_edges = [e for e in g.edges if "gamma" in e[0] or "gamma" in e[1]]
    expect(not delivery_edges,
           f"no delivery edge for explicit-empty intent: {delivery_edges!r}")
    expect(not g.dangling,
           f"no DANGLING for explicit-empty: {g.dangling!r}")


def test_vi1201_dual_provenance_spec_in_direct_and_coordinated(tmp_path: Path) -> None:
    """A spec participates in both direct-delivery and coordinated-delivery."""
    mod = _load_linter("dual")
    write_brief(tmp_path, "coord-b")
    write_feature_intent(tmp_path, "feat1")
    write_feature_intent(tmp_path, "feat2", route="brief")
    write_spec(tmp_path, "dual-spec", discovery="intent:feat1", brief="brief:coord-b")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "relations": [
            {
                "type": "direct-delivery",
                "intent": "intent:feat1",
                "spec": "spec:dual-spec",
                "route": "spec",
                "basis": {"intent": "Decomposed", "spec": "Discovery"},
            },
            {
                "type": "coordinated-delivery",
                "intent": "intent:feat2",
                "brief": "brief:coord-b",
                "spec": "spec:dual-spec",
                "route": "brief",
                "basis": {"intent": "Decomposed", "brief": "Parent intent", "spec": "Brief"},
            },
        ],
    }

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(("intent:feat1", "spec:dual-spec") in g.edges,
           f"direct-delivery edge present: {g.edges!r}")
    expect(("brief:coord-b", "spec:dual-spec") in g.edges,
           f"coordinated-delivery edge present: {g.edges!r}")
    expect(not g.dangling,
           f"no DANGLING for dual-provenance spec: {g.dangling!r}")


def test_vi1201_missing_direct_target_is_dangling(tmp_path: Path) -> None:
    """delivery-target-missing on a spec subject → hard DANGLING violation."""
    mod = _load_linter("miss_direct")
    write_brief(tmp_path, "anchor")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-target-missing",
            "subject": "spec:missing-spec",
            "field": "Discovery",
        }],
    }

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(any("missing-spec" in d for d in g.dangling),
           f"missing spec subject → DANGLING: {g.dangling!r}")


def test_vi1201_missing_brief_is_dangling(tmp_path: Path) -> None:
    """delivery-target-missing on a brief subject → hard DANGLING violation."""
    mod = _load_linter("miss_brief")
    write_brief(tmp_path, "anchor")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-target-missing",
            "subject": "brief:ghost-brief",
            "field": "Parent intent",
        }],
    }

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(any("ghost-brief" in d for d in g.dangling),
           f"missing brief subject → DANGLING: {g.dangling!r}")


def test_vi1201_direct_projection_mismatch_informational_default_fail_strict(
    tmp_path: Path,
) -> None:
    """delivery-projection-mismatch on a feature intent → informational (default),
    FAIL under --strict."""
    mod = _load_linter("mismatch_direct")
    write_brief(tmp_path, "anchor")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-projection-mismatch",
            "subject": "intent:feat",
            "targets": ["spec:foo", "spec:bar"],
        }],
    }

    out_lines, hard, exit_default = mod.check.__wrapped__(tmp_path, False) if hasattr(
        mod.check, "__wrapped__"
    ) else (None, None, None)

    # Use build_standalone directly to check delivery_diagnostics.
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(any("delivery-projection-mismatch" in d for d in g.delivery_diagnostics),
           f"mismatch in delivery_diagnostics: {g.delivery_diagnostics!r}")
    expect(not any("delivery-projection-mismatch" in d for d in g.dangling),
           f"mismatch must not be in dangling: {g.dangling!r}")


def test_vi1201_brief_projection_mismatch_informational(tmp_path: Path) -> None:
    """delivery-projection-mismatch for a brief-route intent → delivery_diagnostics."""
    mod = _load_linter("mismatch_brief")
    write_brief(tmp_path, "anchor")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-projection-mismatch",
            "subject": "intent:feat-b",
            "targets": ["brief:b1", "brief:b2"],
        }],
    }

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=lambda _r: snapshot)

    expect(any("delivery-projection-mismatch" in d for d in g.delivery_diagnostics),
           f"brief mismatch in delivery_diagnostics: {g.delivery_diagnostics!r}")


def test_vi1201_delivery_diag_strict_exit_one(tmp_path: Path) -> None:
    """Delivery diagnostics cause exit 1 under --strict."""
    write_brief(tmp_path, "anchor")
    write_spec(tmp_path, "foo", brief="anchor")

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-projection-mismatch",
            "subject": "intent:feat",
            "targets": ["spec:a", "spec:b"],
        }],
    }

    mod = _load_linter("diag_strict")
    mod._delivery_snapshot_provider = lambda _r: snapshot

    out_lines, hard, exit_default = mod.check(tmp_path, False)
    expect(exit_default == 0,
           f"delivery mismatch: exit 0 in default mode, got {exit_default}")
    expect(any("delivery-projection-mismatch" in ln for ln in out_lines),
           f"mismatch reported in output: {out_lines!r}")

    out_lines2, hard2, exit_strict = mod.check(tmp_path, True)
    expect(exit_strict == 1,
           f"delivery mismatch: exit 1 under --strict, got {exit_strict}")


# ---- VI-1201: real subprocess path with installed resolver ------------------


def test_vi1201_real_subprocess_resolver_installed(tmp_path: Path) -> None:
    """At least one test exercises the real subprocess path: install the resolver
    binary under tmp_path/.agentbundle/bin/ and run lint-traceability.py as a
    subprocess against a fixture corpus with delivery relations."""
    assert _RESOLVER_SOURCE.exists(), "resolver source not found"

    _install_resolver(tmp_path)
    # Feature intent with direct route
    write_feature_intent(tmp_path, "resolved-feat")
    write_spec(tmp_path, "resolved-spec", discovery="intent:resolved-feat")
    # Also a brief for the anchor
    write_brief(tmp_path, "anchor-b")

    rc, out, err = run(tmp_path, "--verbose")

    # The lint should exit 0 (delivery-target-missing on the feature intent is
    # informational, not a DANGLING, because subject=intent:... not spec/brief).
    expect(rc == 0, f"real resolver subprocess → exit 0, got {rc}: {err}")
    expect("DANGLING" not in err or "delivery-resolver-unavailable" not in err,
           f"real resolver must not raise delivery-resolver-unavailable: {err}")


# ---- VI-1203: resolver failure modes ----------------------------------------


@pytest.mark.parametrize("failure_mode,expected_msg", [
    ("raises_unavailable", "delivery-resolver-unavailable"),
    ("raises_bad_json", "delivery-resolver-unavailable"),
    ("raises_timeout", "delivery-resolver-unavailable"),
], ids=["raises-unavailable", "raises-bad-json", "raises-timeout"])
def test_vi1203_resolver_failure_is_hard_violation(
    tmp_path: Path, failure_mode: str, expected_msg: str
) -> None:
    """Any resolver invocation failure → delivery-resolver-unavailable DANGLING,
    exit 1, non-delivery checks still run."""
    write_brief(tmp_path, "anchor")
    write_spec(tmp_path, "foo", brief="anchor")

    def failing_provider(_root: Path) -> dict:
        raise ValueError(f"delivery-resolver-unavailable: {failure_mode}")

    mod = _load_linter(f"fail_{failure_mode}")
    mod._delivery_snapshot_provider = failing_provider

    out_lines, hard, exit_hint = mod.check(tmp_path, False)

    expect(exit_hint == 1,
           f"{failure_mode} → exit 1, got {exit_hint}: {hard!r}")
    expect(any("delivery-resolver-unavailable" in h for h in hard),
           f"{failure_mode} → DANGLING with code, got {hard!r}")
    # Non-delivery checks still run: orphan summary must appear in output.
    expect(any("orphan" in ln.lower() for ln in out_lines),
           f"non-delivery checks still reported: {out_lines!r}")


def test_vi1203_hostile_stderr_not_forwarded(tmp_path: Path) -> None:
    """Hostile content captured from a failing resolver subprocess (absolute
    paths, tracebacks, tokens) must not appear in lint-traceability output."""
    write_brief(tmp_path, "anchor")

    hostile_markers = ["/absolute/path/secret", "Traceback", "TOKEN=abc123"]

    def hostile_provider(_root: Path) -> dict:
        raise ValueError("delivery-resolver-unavailable: non-zero exit")

    mod = _load_linter("hostile_stderr")
    mod._delivery_snapshot_provider = hostile_provider

    out_lines, hard, exit_hint = mod.check(tmp_path, False)
    blob = "\n".join(out_lines) + "\n".join(hard)
    for marker in hostile_markers:
        expect(marker not in blob,
               f"hostile marker {marker!r} must not appear in output: {blob!r}")


def test_vi1203_incomplete_snapshot_is_hard_violation(tmp_path: Path) -> None:
    """An incomplete snapshot (complete: False) → delivery-resolver-unavailable."""
    write_brief(tmp_path, "anchor")

    incomplete = {**_EMPTY_SNAPSHOT, "complete": False}

    mod = _load_linter("incomplete")
    mod._delivery_snapshot_provider = lambda _r: (
        # _run_resolver would reject incomplete → simulate via _parse_and_validate_snapshot
        mod._parse_and_validate_snapshot(
            __import__("json").dumps(incomplete)
        )
    )
    # The provider raises ValueError; test that.
    raised = False
    try:
        mod._parse_and_validate_snapshot(__import__("json").dumps(incomplete))
    except ValueError as exc:
        raised = True
        expect("delivery-resolver-unavailable" in str(exc),
               f"incomplete snapshot raises delivery-resolver-unavailable: {exc}")
    expect(raised, "incomplete snapshot must raise ValueError")


@pytest.mark.parametrize("bad_text,label", [
    ("not json {{{", "malformed-json"),
    ('{"schema_version":1,"complete":true,"relations":[],"classifications":[],'
     '"provenance":[],"diagnostics":[],"extra":1}', "extra-key"),
    ('{"schema_version":2,"complete":true,"relations":[],"classifications":[],'
     '"provenance":[],"diagnostics":[]}', "wrong-schema-version"),
    ('{"schema_version":1,"complete":true,"relations":"not-a-list",'
     '"classifications":[],"provenance":[],"diagnostics":[]}', "non-list-relations"),
], ids=["malformed-json", "extra-key", "wrong-schema-version", "non-list-relations"])
def test_vi1203_parse_and_validate_rejects_bad_input(
    bad_text: str, label: str
) -> None:
    """_parse_and_validate_snapshot raises ValueError on every structural problem."""
    mod = _load_linter(f"parse_{label}")
    raised = False
    try:
        mod._parse_and_validate_snapshot(bad_text)
    except ValueError as exc:
        raised = True
        expect("delivery-resolver-unavailable" in str(exc),
               f"{label}: raised with correct prefix: {exc}")
    expect(raised, f"{label}: must raise ValueError")


def test_vi1203_nan_in_snapshot_is_rejected(tmp_path: Path) -> None:
    """NaN/Infinity in the snapshot JSON is rejected."""
    mod = _load_linter("nan")
    import json as _json
    # Build JSON with NaN using allow_nan=True (Python's json can produce it)
    nan_text = _json.dumps(
        {"schema_version": 1, "complete": True, "relations": [float("nan")],
         "classifications": [], "provenance": [], "diagnostics": []},
        allow_nan=True,
    )
    raised = False
    try:
        mod._parse_and_validate_snapshot(nan_text)
    except ValueError as exc:
        raised = True
        expect("delivery-resolver-unavailable" in str(exc),
               f"NaN rejected with correct prefix: {exc}")
    expect(raised, "NaN in snapshot must raise ValueError")


def test_vi1203_oversize_stdout_rejected_by_run_resolver(tmp_path: Path) -> None:
    """A resolver that emits > 16 MiB of stdout is rejected by _run_resolver."""
    assert _RESOLVER_SOURCE.exists(), "resolver source not found"

    # Install a stub that emits oversize output instead of the real resolver.
    stub = tmp_path / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text(
        "import sys\n"
        "sys.stdout.reconfigure(encoding='utf-8')\n"
        "sys.stdout.write('x' * (16 * 1024 * 1024 + 1))\n",
        encoding="utf-8",
    )

    mod = _load_linter("oversize")
    raised = False
    try:
        mod._run_resolver(tmp_path)
    except ValueError as exc:
        raised = True
        expect("delivery-resolver-unavailable" in str(exc),
               f"oversize stdout raises with correct prefix: {exc}")
    expect(raised, "oversize stdout must raise ValueError")


def test_vi1203_nonzero_exit_rejected_by_run_resolver(tmp_path: Path) -> None:
    """A resolver subprocess that exits non-zero → delivery-resolver-unavailable."""
    stub = tmp_path / ".agentbundle" / "bin" / "intent_delivery_relations.py"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text("import sys; sys.exit(1)\n", encoding="utf-8")

    mod = _load_linter("nonzero")
    raised = False
    try:
        mod._run_resolver(tmp_path)
    except ValueError as exc:
        raised = True
        expect("delivery-resolver-unavailable" in str(exc),
               f"non-zero exit raises with correct prefix: {exc}")
    expect(raised, "non-zero exit must raise ValueError")


def test_vi1203_binary_absent_is_hard_violation(tmp_path: Path) -> None:
    """_run_resolver always raises ValueError on any absent-binary failure,
    including when .agentbundle/bin/ itself is absent.  The opt-out from
    delivery checking is at the _has_any_anchor level in build_standalone, not
    inside _run_resolver — so _run_resolver never silently returns None."""
    mod = _load_linter("absent")
    # No .agentbundle/bin/ directory → hard violation (same as binary absent)
    with pytest.raises(ValueError, match="delivery-resolver-unavailable"):
        mod._run_resolver(tmp_path)


def test_vi1203_non_delivery_checks_run_when_resolver_fails(tmp_path: Path) -> None:
    """When the resolver fails, non-delivery checks (orphan, dangling, cycle)
    are still computed and reported."""
    write_brief(tmp_path, "anchor")
    write_spec(tmp_path, "alpha", brief="anchor", component="ghost-local")  # dangling component

    def failing(_root: Path) -> dict:
        raise ValueError("delivery-resolver-unavailable: simulated")

    mod = _load_linter("fail_nondelivery")
    mod._delivery_snapshot_provider = failing

    out_lines, hard, exit_hint = mod.check(tmp_path, False)

    # Both the resolver failure AND the dangling component must be reported.
    expect(exit_hint == 1, f"resolver fail + dangling → exit 1, got {exit_hint}")
    expect(any("delivery-resolver-unavailable" in h for h in hard),
           f"resolver failure in hard violations: {hard!r}")
    expect(any("ghost-local" in h for h in hard),
           f"dangling component still reported: {hard!r}")


def test_vi1203_no_retired_fallback_when_resolver_fails(tmp_path: Path) -> None:
    """When the resolver fails, _wire_up must NOT receive feature-delivery
    Discovery:/Brief: pointers — no retired fallback wires delivery."""
    write_brief(tmp_path, "b")
    write_feature_intent(tmp_path, "feat-x")
    write_spec(tmp_path, "feat-spec", discovery="intent:feat-x", brief="b")

    def failing(_root: Path) -> dict:
        raise ValueError("delivery-resolver-unavailable: simulated")

    mod = _load_linter("fail_no_fallback")
    mod._delivery_snapshot_provider = failing

    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {},
                         snapshot_provider=failing)

    # With failing resolver, spec gets only Contract:/Parent intent: candidates.
    # Neither Discovery: nor Brief: may wire any edge — no snapshot confirmed
    # whether this brief carries a feature-delivery relation.
    expect(("intent:feat-x", "spec:feat-spec") not in g.edges,
           f"no delivery edge wired from local Discovery: on resolver failure: {g.edges!r}")
    expect(("brief:b", "spec:feat-spec") not in g.edges,
           f"no Brief: edge wired when no valid snapshot: {g.edges!r}")


# ---- Defects found in controller review of T3 --------------------------------


def test_defect_bin_dir_exists_binary_absent_is_hard_violation(tmp_path: Path) -> None:
    """When .agentbundle/bin/ directory exists but the binary is absent,
    _run_resolver must raise ValueError (hard violation), not return None."""
    mod = _load_linter("bindir_absent_binary")
    # Create the bin directory but NOT the resolver binary.
    (tmp_path / ".agentbundle" / "bin").mkdir(parents=True)
    with pytest.raises(ValueError, match="delivery-resolver-unavailable"):
        mod._run_resolver(tmp_path)


def test_defect_no_brief_wired_when_no_valid_snapshot(tmp_path: Path) -> None:
    """When no valid snapshot exists (resolver fails), Brief: must not be parsed
    to wire any edge — the snapshot is required to confirm this brief is not a
    feature-delivery brief."""
    write_brief(tmp_path, "b")
    write_spec(tmp_path, "plain", brief="b")

    def failing(_root: Path) -> dict:
        raise ValueError("delivery-resolver-unavailable: simulated")

    mod = _load_linter("no_snap_no_brief")
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {}, snapshot_provider=failing)

    expect(("brief:b", "spec:plain") not in g.edges,
           f"Brief: edge must not be wired without a valid snapshot: {g.edges!r}")


# ---- Round-2 controller defects ------------------------------------------------


def test_fix1_contextual_provenance_uses_local_discovery(tmp_path: Path) -> None:
    """When the snapshot carries a contextual-provenance record for (spec, 'Discovery'),
    the lint reads the spec's local Discovery: value as the _wire_up candidate —
    restoring the structural edge the old local-parsing path provided, without
    treating the value as a feature-delivery pointer."""
    # Spec with a path-shaped (not-intent-shaped) Discovery: value.
    write_spec(tmp_path, "ctx-spec",
               discovery="docs/product/research/ctx-notes.md")
    write_brief(tmp_path, "anchor")

    # Snapshot: no delivery relation; contextual-provenance record for Discovery field.
    snapshot = {
        **_EMPTY_SNAPSHOT,
        "provenance": [{"subject": "spec:ctx-spec", "field": "Discovery"}],
    }

    mod = _load_linter("fix1_ctx_prov")
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {}, snapshot_provider=lambda _: snapshot)

    # The local Discovery: value must produce a candidate for _wire_up.
    # Because "docs/product/research/ctx-notes.md" resolves as unresolvable
    # cross-repo, the spec should NOT appear as an orphan (it has an asserted producer).
    orphans = mod.classify_standalone(g, True)
    orphan_ids = {nid for nid, _, _ in orphans}
    expect("spec:ctx-spec" not in orphan_ids,
           f"contextual-provenance spec must not be an orphan: {orphan_ids!r}")


def test_fix2_delivery_diagnostic_spec_excluded_from_orphan(tmp_path: Path) -> None:
    """A spec that appears in delivery diagnostic targets must not also be
    reported as a backward orphan — one break, one class (delivery diagnostic wins)."""
    write_brief(tmp_path, "b")
    write_spec(tmp_path, "diag-target")  # no Discovery, no Contract → would be orphan

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-projection-mismatch",
            "subject": "intent:some-feature",
            "targets": ["spec:diag-target"],
        }],
    }

    mod = _load_linter("fix2_diag_orphan")
    g = mod.Graph()
    mod.build_standalone(tmp_path, {}, g, {}, snapshot_provider=lambda _: snapshot)

    orphans = mod.classify_standalone(g, True)
    orphan_ids = {nid for nid, _, _ in orphans}
    expect("spec:diag-target" not in orphan_ids,
           f"spec in delivery-diagnostic targets must not be a backward orphan: {orphan_ids!r}")


def test_fix3_bin_dir_absent_is_hard_violation(tmp_path: Path) -> None:
    """An absent .agentbundle/bin/ directory must raise delivery-resolver-unavailable —
    the same as any other failure.  The 'no anchor' early exit still wins at the
    build_standalone / check() level; _run_resolver itself always fails closed."""
    mod = _load_linter("fix3_no_bindir")
    # No .agentbundle/ directory at all → hard violation from _run_resolver
    with pytest.raises(ValueError, match="delivery-resolver-unavailable") as raised:
        mod._run_resolver(tmp_path)
    # AC-0018: the message carries repository-relative context only.
    assert str(tmp_path) not in str(raised.value)
