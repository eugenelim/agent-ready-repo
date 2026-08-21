"""Deliberately thin agent loop fixture."""

from knowledge.retrieval import retrieve
from model.client import complete
from tools.executor import execute


def run_agent(tenant_id: str, question: str) -> None:
    """Retrieve, call the model, and execute the returned action."""

    context = retrieve(question)
    action = complete(question, context)
    execute(tenant_id, action)
