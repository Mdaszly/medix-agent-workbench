"""阶段 2：Agent 网关与统一路由测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.chat import ChatResponse
from app.services.agent_gateway import dispatch_dify, dispatch_swarm


class TestAgentGateway:
    def test_dispatch_swarm_sets_metrics(self):
        mock_resp = ChatResponse(
            session_id="s1",
            answer="ok",
            risk_level="低风险",
            suggestions=[],
            recommended_department="内科",
            disclaimer="d",
            evidence=[],
            agent_trace=[],
            metrics={},
        )
        with patch("app.services.agent_gateway._orchestrator") as mock_orch:
            mock_orch.handle = AsyncMock(return_value=mock_resp)
            from app.schemas.chat import ChatRequest

            req = ChatRequest(message="我头痛")
            resp = asyncio.run(dispatch_swarm(req))
            assert resp.metrics["orchestrator"] == "swarm"
            assert resp.metrics["fallback"] is False

    def test_dispatch_dify_fallback_to_langgraph(self):
        from app.schemas.chat import ChatRequest, PatientContext

        req = ChatRequest(message="我头痛", patient_context=PatientContext(age=30))
        mock_dify = MagicMock()
        mock_dify.enabled = True
        mock_dify.get_client.return_value.send_message.return_value = {
            "status": "error",
            "message": "timeout",
        }

        lg_resp = ChatResponse(
            session_id="sid-1",
            answer="降级回答",
            risk_level="低风险",
            suggestions=[],
            recommended_department="内科",
            disclaimer="d",
            evidence=[],
            agent_trace=[],
            metrics={"interrupted": False},
        )

        with patch("app.services.agent_gateway.dispatch_langgraph", return_value=lg_resp):
            resp = asyncio.run(dispatch_dify(req, [], "sid-1", mock_dify))
            assert resp.metrics["fallback"] is True
            assert resp.metrics["fallback_chain"] == ["dify", "langgraph"]
            assert resp.metrics["orchestrator"] == "langgraph"


class TestChatRouteAPI:
    @pytest.fixture
    def client(self):
        from main import app

        return TestClient(app)

    def test_chat_route_swarm(self, client):
        resp = client.post(
            "/api/chat/route",
            json={"message": "我有点咳嗽", "orchestrator": "swarm"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["metrics"]["orchestrator"] == "swarm"

    def test_chat_route_langgraph(self, client):
        resp = client.post(
            "/api/chat/route",
            json={"message": "我有点咳嗽", "orchestrator": "langgraph"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["metrics"]["orchestrator"] == "langgraph"
        assert len(body.get("agent_trace") or []) >= 1

    def test_chat_route_dify_mock_success(self, client):
        mock_client = MagicMock()
        mock_client.send_message.return_value = {"answer": "Dify 回复", "outputs": {}}
        with patch("app.api.chat.dify_integration") as mock_int:
            mock_int.enabled = True
            mock_int.get_client.return_value = mock_client
            resp = client.post(
                "/api/chat/route",
                json={"message": "你好", "orchestrator": "dify"},
            )
            assert resp.status_code == 200
            assert resp.json()["metrics"]["dify_used"] is True
