"""Shared pytest fixtures for deterministic LangGraph tests."""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture(autouse=True)
def reset_langgraph_runtime():
    """Avoid checkpoint/session leakage between tests."""
    import app.services.langgraph_workflow as workflow

    workflow._checkpointer = MemorySaver()
    workflow._compiled_graph = None
    yield
    workflow._compiled_graph = None
    workflow._checkpointer = MemorySaver()
