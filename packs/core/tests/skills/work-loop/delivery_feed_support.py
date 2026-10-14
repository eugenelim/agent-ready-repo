"""Fixture builders for the delivery fact feed suites.

Builds repositories whose evidence logs are written by the shipped Slice 1 and
Slice 2 writers (``EvidenceStore`` and the review bridge), so the feed is tested
against real frames rather than hand-made bytes.  Standard library only, no
pytest import: this is support code that no runner collects.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS = (
    Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
)
SHADOW_SUBDIR = ".shadow-acceptance"
LOG_NAME = "shadow-evidence.log"
MARKER = b"*\n"


def load_script(alias: str, filename: str) -> ModuleType:
    """Load a work-loop script by literal path under a unique module name."""
    assert "/" not in filename and filename not in {"", ".", ".."}, filename
    path = Path(os.path.join(SCRIPTS, filename))  # noqa: PTH118 — the pack-boundary lint traces this form
    assert stat.S_ISREG(os.lstat(path).st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(alias, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


def null_sink(event: object) -> None:
    """Accept security events without persisting them."""


class FeedRepo:
    """A temporary repository with spec directories and shadow evidence logs."""

    def __init__(self, base: Path) -> None:
        self.root = base / "repo"
        (self.root / ".git").mkdir(parents=True)
        (self.root / "docs" / "specs").mkdir(parents=True)
        self.es = load_script("dfp_evidence_store", "_evidence_store.py")
        self.sc = load_script("dfp_security_capability", "_security_capability.py")
        self.persistence = load_script("dfp_review_persistence", "_review_persistence.py")
        self.bridge = load_script("dfp_review_bridge", "_review_bridge.py")
        issuer = self.sc.CapabilityIssuer()
        self._issuer = issuer
        self._grant = issuer.issue_root_grant(
            roots=["evidence"],
            operations=["append"],
            trust_class="trusted",
            writes_allowed_roots=["evidence"],
            control_denies=[],
        )
        self._counter = 0
        # slug -> tag -> (finding, report, subject, receipt ids, criteria)
        self.facts: dict[str, dict[str, dict[str, Any]]] = {}

    # ── Layout ──────────────────────────────────────────────────────────────

    def spec_dir(self, slug: str) -> Path:
        """Return (creating it) the spec directory for *slug*."""
        path = self.root / "docs" / "specs" / slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def shadow_dir(self, slug: str) -> Path:
        """Return the shadow directory path for *slug* without creating it."""
        return self.spec_dir(slug) / SHADOW_SUBDIR

    def log_path(self, slug: str) -> Path:
        """Return the evidence log path for *slug*."""
        return self.shadow_dir(slug) / LOG_NAME

    def ensure_shadow(self, slug: str, *, marker: bytes | None = MARKER) -> Path:
        """Create the shadow directory with the writer's marker (or another, or none)."""
        directory = self.shadow_dir(slug)
        directory.mkdir(exist_ok=True)
        if marker is not None:
            (directory / ".gitignore").write_bytes(marker)
        return directory

    def log_bytes(self, slug: str) -> bytes:
        """Return the raw log bytes for *slug*."""
        return self.log_path(slug).read_bytes()

    def tree_state(self) -> dict[str, tuple[bytes, int, int]]:
        """Return (bytes, mtime_ns, inode) for every regular file, keyed by relative path."""
        found: dict[str, tuple[bytes, int, int]] = {}
        for current, _dirs, files in os.walk(self.root):
            for name in files:
                path = Path(current) / name
                if path.is_symlink():
                    continue
                info = path.stat()
                found[path.relative_to(self.root).as_posix()] = (
                    path.read_bytes(), info.st_mtime_ns, info.st_ino,
                )
        return found

    def tree_bytes(self) -> dict[str, bytes]:
        """Return every regular file under the repository, keyed by relative path."""
        found: dict[str, bytes] = {}
        for current, _dirs, files in os.walk(self.root):
            for name in files:
                path = Path(current) / name
                if path.is_symlink():
                    continue
                found[path.relative_to(self.root).as_posix()] = path.read_bytes()
        return found

    # ── Writers ─────────────────────────────────────────────────────────────

    def open_store(self, slug: str) -> Any:
        """Open the production evidence store for *slug*, with the marker in place."""
        self.ensure_shadow(slug)
        store = self.es.EvidenceStore(self.log_path(slug))
        store.open()
        return store

    def _tx(self, label: str) -> str:
        self._counter += 1
        return f"tx-{label}-{self._counter}"

    def add_engine_transition(self, slug: str, store: Any, name: str = "plan-locked") -> str:
        """Append one contentless engine-transition receipt, as a production run writes it."""
        self._counter += 1
        receipt_id = f"shadow-{self._counter:032x}"
        store.append_receipt(
            {
                "schema_version": 1,
                "receipt_id": receipt_id,
                "acceptance_fingerprint": f"acceptance-fp-{slug}",
                "lineage": {"criterion_ref": "shadow:legacy-plan-locked"},
                "selector": {"term": f"engine-transition:{name}"},
                "freshness_mode": "exact-subject",
                "observation": {"type": "engine-transition"},
                "outcome": "observed",
                "producer": {"class": "shadow-compat-facade", "identity": "shadow-compat-facade"},
            },
            transaction_id=self._tx("engine"),
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )
        return receipt_id

    def add_review_failure(
        self,
        slug: str,
        store: Any,
        tag: str,
        *,
        criteria: tuple[str, ...] = ("AC-0014",),
        finding_text: dict[str, str] | None = None,
        evidence_refs: tuple[str, ...] = ("packs/core/example/module.py",),
        policy_fingerprint: str | None = None,
    ) -> list[str]:
        """Persist a findings report and a supported assessment; return the receipt IDs."""
        acceptance_fp = f"acceptance-fp-{slug}"
        policy_fp = policy_fingerprint or f"review-policy-{tag}"
        subject = {
            "schema_version": 1,
            "review_subject_id": f"review-subject-{tag}",
            "review_subject_fingerprint": f"review-subject-fp-{tag}",
            "delivery_subject_ref": {
                "subject_id": f"delivery-subject-{slug}",
                "acceptance_fingerprint": acceptance_fp,
            },
            "normalized_paths": ["packs/core/example/module.py"],
            "normalized_statuses": ["modified"],
            "review_policy_fingerprint": policy_fp,
            "lineage": {"provider": "feed-fixture", "projection_version": "1.0"},
        }
        text = {
            "rule_ref": "AC-0014",
            "observation": f"The writer accepts input {tag} without validation.",
            "reachable_path": "A caller reaches the writer through the public entry point.",
            "actual_failure": "Invalid input is persisted and later read back as trusted.",
            **(finding_text or {}),
        }
        finding = {
            "schema_version": 1,
            "finding_id": f"finding-{tag}",
            "rule_ref": text["rule_ref"],
            "observation": text["observation"],
            "reachable_path": text["reachable_path"],
            "actual_failure": text["actual_failure"],
            "affected_acceptance_criteria": list(criteria),
            "evidence_refs": list(evidence_refs),
            "material": True,
        }
        report = {
            "schema_version": 1,
            "report_id": f"report-{tag}",
            "role": "quality-engineer",
            "subject": copy.deepcopy(subject),
            "terminal_status": "findings",
            "lineage": {
                "sequence": 1,
                "review_policy_fingerprint": policy_fp,
                "source_event_id": f"source-event-{tag}",
                "producer": "synthetic-reviewer",
            },
            "findings": [copy.deepcopy(finding)],
        }
        self.persistence.append_current_review_report(
            store,
            report,
            transaction_id=self._tx(f"report-{tag}"),
            expected_subject=subject,
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )
        tx = self.bridge.append_finding_assessment_bridge(
            store,
            self._assessment(tag, subject, "supported"),
            report_id=report["report_id"],
            finding=finding,
            affected_criteria=list(criteria),
            transaction_id=self._tx(f"supported-{tag}"),
            acceptance_fingerprint=acceptance_fp,
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )
        receipt_ids = list(tx["ordered_record_ids"][1:])
        self.facts.setdefault(slug, {})[tag] = {
            "finding": finding,
            "report": report,
            "subject": subject,
            "criteria": criteria,
            "receipt_ids": receipt_ids,
        }
        return receipt_ids

    def _assessment(self, tag: str, subject: dict, outcome: str) -> dict:
        return {
            "schema_version": 1,
            "assessment_id": f"assessment-{tag}-{outcome}",
            "finding_id": f"finding-{tag}",
            "report_id": f"report-{tag}",
            "review_subject_fingerprint": subject["review_subject_fingerprint"],
            "assessment": outcome,
            "evidence_refs": ["evidence:observation", "evidence:reachable-path"],
            "lineage": {"predicate_version": "feed-fixture-v1"},
        }

    def supersede_by_assessment(self, slug: str, store: Any, tag: str) -> None:
        """Replace a supported assessment with an unsupported one (Slice 2 supersession)."""
        fact = self.facts[slug][tag]
        self.bridge.append_finding_assessment_bridge(
            store,
            self._assessment(tag, fact["subject"], "unsupported-opinion"),
            report_id=fact["report"]["report_id"],
            finding=fact["finding"],
            affected_criteria=list(fact["criteria"]),
            transaction_id=self._tx(f"unsupported-{tag}"),
            acceptance_fingerprint=f"acceptance-fp-{slug}",
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )

    def supersede_by_report_replacement(self, slug: str, store: Any, tag: str) -> None:
        """Persist a replacement report for the same subject (the store retires old receipts)."""
        fact = self.facts[slug][tag]
        replacement = copy.deepcopy(fact["report"])
        replacement["report_id"] = f"report-{tag}-replacement"
        self.persistence.append_current_review_report(
            store,
            replacement,
            transaction_id=self._tx(f"replace-{tag}"),
            expected_subject=fact["subject"],
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )

    def supersede_by_source_invalidation(self, slug: str, store: Any, tag: str) -> None:
        """Invalidate the source against a changed review subject."""
        fact = self.facts[slug][tag]
        new_subject = copy.deepcopy(fact["subject"])
        new_subject["review_subject_id"] = f"review-subject-{tag}-new"
        new_subject["review_subject_fingerprint"] = f"review-subject-fp-{tag}-new"
        new_subject["review_policy_fingerprint"] = f"review-policy-{tag}-new"
        self.bridge.append_finding_assessment_replacement(
            store,
            old_report_id=fact["report"]["report_id"],
            old_finding_id=fact["finding"]["finding_id"],
            new_assessment=None,
            current_subject=new_subject,
            transaction_id=self._tx(f"invalidate-{tag}"),
            acceptance_fingerprint=f"acceptance-fp-{slug}",
            issuer=self._issuer,
            grant=self._grant,
            audit_sink=null_sink,
        )
