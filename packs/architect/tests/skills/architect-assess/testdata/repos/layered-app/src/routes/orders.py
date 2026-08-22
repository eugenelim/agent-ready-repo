"""HTTP-shaped fixture route."""

from data.queries import save_order


def create_order(tenant_id: str, order_id: str) -> None:
    """Create an order through a direct query-layer dependency."""

    save_order(tenant_id, order_id)
