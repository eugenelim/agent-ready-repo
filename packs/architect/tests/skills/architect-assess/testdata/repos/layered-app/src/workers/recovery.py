"""Deliberately incomplete recovery fixture."""

from data.queries import save_order


def recover(order_id: str) -> None:
    """Recover without the required tenant context."""

    save_order("", order_id)
