"""Tool fixture with no declared approval boundary."""


def execute(tenant_id: str, action: str) -> None:
    """Execute one fixture action."""

    _ = (tenant_id, action)
