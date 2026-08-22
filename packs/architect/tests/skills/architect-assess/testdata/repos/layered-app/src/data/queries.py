"""Store fixture with an explicit tenant argument."""


def save_order(tenant_id: str, order_id: str) -> None:
    """Persist one tenant-owned order in the fixture."""

    _ = (tenant_id, order_id)
