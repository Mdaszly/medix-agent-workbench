"""
LangGraph 工作流测试（阶段 1）

覆盖：状态/trace、策略路由、Checkpointer、Human-in-the-loop interrupt
"""

import pytest
from langgraph.types import Command

from app.services.langgraph_workflow import (
    MedicalState,
    RiskRouteStrategy,
    build_initial_state,
    build_medical_graph,
    get_compiled_graph,
    resume_workflow,
    run_workflow,
    risk_assessment_node,
    symptom_analysis_node,
)


class TestStatePattern:
    def test_build_initial_state(self):
        state = build_initial_state("我头痛", {"age": 30})
        assert state["message"] == "我头痛"
        assert state["agent_trace"] == []
        assert state["thinking_steps"] == []

    def test_state_update(self):
        state = build_initial_state("test", {})
        updated = {**state, "risk_level": "高风险", "department": "急诊科"}
        assert updated["risk_level"] == "高风险"


class TestStrategyPattern:
    def test_risk_strategy_high_risk(self):
        assert RiskRouteStrategy().decide({"risk_level": "高风险"}) == "emergency"

    def test_risk_strategy_normal(self):
        assert RiskRouteStrategy().decide({"risk_level": "低风险"}) == "normal"
        assert RiskRouteStrategy().decide({"risk_level": "中风险"}) == "normal"


class TestAdapterPattern:
    def test_symptom_analysis_node(self):
        state = build_initial_state("我头痛", {})
        result = symptom_analysis_node(state)
        assert "symptoms" in result["symptom_profile"]

    def test_risk_assessment_high_risk(self):
        state = build_initial_state("我胸痛，呼吸困难", {})
        result = risk_assessment_node(state)
        assert result["risk_level"] == "高风险"


class TestWorkflow:
    def test_workflow_graph_build(self):
        graph = build_medical_graph()
        assert graph is not None

    def test_workflow_normal_has_trace(self):
        result = run_workflow(message="我有点咳嗽", patient={"age": 30, "gender": "女"})
        assert result["risk_level"] in ["低风险", "中风险"]
        assert result["answer"]
        assert len(result.get("agent_trace") or []) >= 3
        agents = {t["agent"] for t in result["agent_trace"]}
        assert "RouterAgent" in agents
        assert "RAGAgent" in agents

    def test_workflow_high_risk_interrupts(self):
        sid = "test-high-risk-session"
        result = run_workflow(
            message="我胸痛，呼吸困难",
            patient={"age": 45, "gender": "男"},
            session_id=sid,
        )
        assert result["interrupted"] is True
        assert result.get("risk_level") in ("", "高风险") or result["interrupted"]

    def test_workflow_high_risk_resume(self):
        sid = "test-resume-session"
        first = run_workflow(
            message="我胸痛，呼吸困难",
            patient={"age": 45, "gender": "男"},
            session_id=sid,
        )
        assert first["interrupted"] is True

        second = resume_workflow(session_id=sid, confirmed=True)
        assert second["interrupted"] is False
        assert second["risk_level"] == "高风险"
        assert "紧急提醒" in second["answer"]
        assert any(t["agent"] == "SafetyAgent" for t in second.get("agent_trace") or [])

    def test_checkpointer_multi_turn_same_session(self):
        sid = "test-multi-turn"
        r1 = run_workflow(message="我有点咳嗽", patient={"age": 30}, session_id=sid)
        assert not r1["interrupted"]

        r2 = run_workflow(
            message="咳嗽三天了",
            patient={"age": 30},
            history=[{"role": "user", "content": "我有点咳嗽"}],
            session_id=sid,
        )
        assert not r2["interrupted"]
        assert r2["answer"]


class TestChatLangGraphAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app

        return TestClient(app)

    def test_langgraph_endpoint_returns_trace(self, client):
        resp = client.post(
            "/api/chat/langgraph",
            json={"message": "我有点咳嗽", "patient_context": {"age": 30}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["metrics"]["orchestrator"] == "langgraph"
        assert len(body["agent_trace"]) >= 1

    def test_langgraph_high_risk_interrupt_flow(self, client):
        resp = client.post(
            "/api/chat/langgraph",
            json={"message": "我胸痛，呼吸困难", "session_id": "api-hr-test"},
        )
        assert resp.status_code == 200
        body = resp.json()
        if body["metrics"].get("interrupted"):
            resume = client.post(
                "/api/chat/langgraph/resume",
                json={"session_id": "api-hr-test", "confirmed": True},
            )
            assert resume.status_code == 200
            assert "紧急提醒" in resume.json()["answer"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
