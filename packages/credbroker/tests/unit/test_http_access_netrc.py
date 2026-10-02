# STUB: AC-0009 — an exact machine record returns origin-bound netrc access
import os
from pathlib import Path

import pytest

from credbroker import NetrcHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX permission bits")
def test_netrc_exact_host_returns_origin_bound_access(
    tmp_path: Path,
) -> None:
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login test-user password test-secret\n",
        encoding="utf-8",
    )
    netrc_file.chmod(0o600)

    result = resolve_http_access(
        "https://catalogue.example.test/root/catalogue.toml",
        env={"HOME": str(tmp_path)},
    )

    assert isinstance(result, NetrcHttpAccess)
    assert result.origin == "https://catalogue.example.test"
