"""Agent run API fixture."""

from runtime.run import run_agent


def start(tenant_id: str, question: str) -> None:
    """Start an in-process run."""

    run_agent(tenant_id, question)
