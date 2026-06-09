"""Shared pytest fixtures for deterministic LangGraph tests."""

from __future__ import annotations

import os

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


@pytest.fixture(autouse=True)
def stabilize_ci_dependencies(monkeypatch):
    """Keep CI deterministic: no outbound web search/retries."""
    if not os.getenv("CI"):
        return

    async def _offline_web_search(query: str, limit: int = 2, timeout: float = 8.0):
        from app.schemas.chat import Evidence

        return [
            Evidence(
                source="ci-offline",
                title="CI offline stub",
                score=0.0,
                content="Offline CI mode: skip external web search.",
            )
        ]

    monkeypatch.setattr("app.services.medical_business.web_search", _offline_web_search)
    monkeypatch.setattr("app.services.deep_search.web_search", _offline_web_search)
    monkeypatch.setattr("app.services.dify_client.time.sleep", lambda *_args, **_kwargs: None)
