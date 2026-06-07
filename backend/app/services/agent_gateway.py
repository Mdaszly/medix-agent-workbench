"""
Agent 网关 — 阶段 2 统一编排路由

路由策略：
- swarm    → MedicalSwarm（默认生产链路）
- langgraph → LangGraph 状态机（含 interrupt）
- dify     → Dify 云端工作流，失败时降级 langgraph → swarm
"""

from __future__ import annotations

import time
from typing import Literal, Optional

from app.schemas.chat import ChatRequest, ChatResponse, LangGraphResumeRequest
from app.services.agent_orchestrator import MedicalAgentOrchestrator
from app.services.chat_helpers import DISCLAIMER, langgraph_to_response
from app.services.langgraph_workflow import resume_workflow, run_workflow

OrchestratorMode = Literal["swarm", "langgraph", "dify"]

_orchestrator = MedicalAgentOrchestrator()


async def dispatch_swarm(req: ChatRequest) -> ChatResponse:
    resp = await _orchestrator.handle(req)
    metrics = dict(resp.metrics or {})
    metrics.setdefault("orchestrator", "swarm")
    metrics.setdefault("fallback", False)
    resp.metrics = metrics
    return resp


def dispatch_langgraph(req: ChatRequest, history: list, session_id: str) -> ChatResponse:
    result = run_workflow(
        message=req.message,
        patient=req.patient_context.model_dump(),
        history=history,
        session_id=session_id,
    )
    return langgraph_to_response(session_id, result)


async def dispatch_dify(
    req: ChatRequest,
    history: list,
    session_id: str,
    dify_integration,
) -> ChatResponse:
    if not dify_integration.enabled:
        lg = dispatch_langgraph(req, history, session_id)
        lg.metrics = {
            **(lg.metrics or {}),
            "dify_enabled": False,
            "dify_used": False,
            "fallback": True,
            "fallback_chain": ["dify", "langgraph"],
            "orchestrator": "langgraph",
        }
        return lg

    t0 = time.time()
    result = dify_integration.get_client().send_message(
        message=req.message,
        user_id=req.user_id,
    )
    elapsed_ms = int((time.time() - t0) * 1000)

    if result.get("status") != "error":
        outputs = result.get("outputs", {})
        return ChatResponse(
            session_id=session_id,
            answer=outputs.get("answer", "") or result.get("answer", ""),
            risk_level=outputs.get("risk_level", "低风险"),
            suggestions=[],
            recommended_department=outputs.get("department", "内科"),
            thinking_steps=[],
            disclaimer=DISCLAIMER,
            evidence=[],
            agent_trace=[],
            metrics={
                "dify_enabled": True,
                "dify_used": True,
                "fallback": False,
                "orchestrator": "dify",
                "elapsed_ms": elapsed_ms,
            },
        )

    try:
        lg = dispatch_langgraph(req, history, session_id)
        if lg.answer or lg.metrics.get("interrupted"):
            lg.metrics = {
                **(lg.metrics or {}),
                "dify_enabled": True,
                "dify_used": False,
                "fallback": True,
                "fallback_chain": ["dify", "langgraph"],
                "orchestrator": "langgraph",
                "elapsed_ms": elapsed_ms,
            }
            return lg
    except Exception:
        pass

    swarm = await dispatch_swarm(req)
    swarm.metrics = {
        **(swarm.metrics or {}),
        "dify_enabled": True,
        "dify_used": False,
        "fallback": True,
        "fallback_chain": ["dify", "langgraph", "swarm"],
        "orchestrator": "swarm",
        "elapsed_ms": elapsed_ms,
    }
    return swarm


async def dispatch(
    req: ChatRequest,
    mode: OrchestratorMode,
    history: list,
    session_id: str,
    dify_integration,
) -> ChatResponse:
    if mode == "swarm":
        return await dispatch_swarm(req)
    if mode == "langgraph":
        return dispatch_langgraph(req, history, session_id)
    if mode == "dify":
        return await dispatch_dify(req, history, session_id, dify_integration)
    raise ValueError(f"未知编排模式: {mode}")


def resume_langgraph(req: LangGraphResumeRequest) -> ChatResponse:
    result = resume_workflow(session_id=req.session_id, confirmed=req.confirmed)
    return langgraph_to_response(req.session_id, result)
