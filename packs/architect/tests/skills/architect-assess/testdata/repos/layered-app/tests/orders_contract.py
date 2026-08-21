"""Route-only test fixture (not collected by the catalogue suite)."""

from routes.orders import create_order


def check_create_order() -> None:
    create_order("tenant-a", "order-1")
