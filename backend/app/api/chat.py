from __future__ import annotations

import time
import uuid

from fastapi import APIRouter

from app.core.database import clear_all, clear_session, list_messages, list_sessions, add_message, upsert_session
from app.schemas.chat import AgentTrace, ChatRequest, ChatResponse, Evidence, LangGraphResumeRequest
from app.services.agent_orchestrator import MedicalAgentOrchestrator
from app.services.langgraph_workflow import run_workflow, resume_workflow, get_session_state
from app.services.dify_client import dify_integration

router = APIRouter(prefix="/api", tags=["chat"])
orchestrator = MedicalAgentOrchestrator()

# 免责声明
DISCLAIMER = "以上内容仅用于健康科普、预问诊和就医参考，不能替代医生诊断、处方或治疗。"


def _load_history(session_id: str) -> list:
    rows = list_messages(session_id, limit=20)
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def _langgraph_response(session_id: str, result: dict) -> ChatResponse:
    traces = [
        AgentTrace(
            agent=t.get("agent", ""),
            action=t.get("action", ""),
            detail=t.get("detail", ""),
            duration_ms=t.get("duration_ms", 0),
        )
        for t in result.get("agent_trace") or []
    ]
    evidence = []
    for item in result.get("evidence") or []:
        if isinstance(item, dict):
            evidence.append(
                Evidence(
                    source=item.get("source", ""),
                    title=item.get("title", ""),
                    score=float(item.get("score", 0)),
                    content=item.get("content", ""),
                )
            )

    answer = result.get("answer") or ""
    if result.get("interrupted"):
        payload = result.get("interrupt_payload") or []
        if payload:
            val = getattr(payload[0], "value", None) or {}
            answer = val.get("prompt", "检测到高风险症状，请确认已了解需立即就医。")

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        risk_level=result.get("risk_level") or "低风险",
        suggestions=[],
        recommended_department=result.get("department") or "内科",
        thinking_steps=result.get("thinking_steps") or [],
        disclaimer=DISCLAIMER,
        evidence=evidence,
        agent_trace=traces,
        metrics={
            "orchestrator": "langgraph",
            "interrupted": bool(result.get("interrupted")),
            "human_confirmed": result.get("human_confirmed"),
            "trace_count": len(traces),
        },
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await orchestrator.handle(req)


@router.post("/chat/langgraph", response_model=ChatResponse)
async def chat_langgraph(req: ChatRequest):
    """LangGraph 工作流：含 agent_trace、多轮 history、高风险 interrupt。"""
    session_id = req.session_id or str(uuid.uuid4())
    upsert_session(session_id, title=req.message[:40])

    history = _load_history(session_id) if req.session_id else []
    result = run_workflow(
        message=req.message,
        patient=req.patient_context.model_dump(),
        history=history,
        session_id=session_id,
    )

    add_message(session_id, "user", req.message)
    if not result.get("interrupted"):
        add_message(session_id, "assistant", result.get("answer", ""))

    return _langgraph_response(session_id, result)


@router.post("/chat/langgraph/resume", response_model=ChatResponse)
async def chat_langgraph_resume(req: LangGraphResumeRequest):
    """恢复高风险 interrupt 后继续执行 emergency 分支。"""
    result = resume_workflow(session_id=req.session_id, confirmed=req.confirmed)
    if not result.get("interrupted") and result.get("answer"):
        add_message(req.session_id, "assistant", result.get("answer", ""))
    return _langgraph_response(req.session_id, result)


@router.get("/chat/langgraph/state/{session_id}")
async def chat_langgraph_state(session_id: str):
    """查看 LangGraph checkpoint 状态（调试）。"""
    return get_session_state(session_id)


@router.post("/chat/dify", response_model=ChatResponse)
async def chat_dify(req: ChatRequest):
    """使用Dify工作流处理问诊请求"""
    session_id = req.session_id or str(uuid.uuid4())
    
    # 检查Dify是否配置
    if not dify_integration.enabled:
        return ChatResponse(
            session_id=session_id,
            answer="Dify服务未配置，请联系管理员配置DIFY_API_KEY和DIFY_APP_ID环境变量。",
            risk_level="低风险",
            suggestions=[],
            recommended_department="内科",
            thinking_steps=[],
            disclaimer=DISCLAIMER,
            evidence=[],
            agent_trace=[],
            metrics={"dify_enabled": False}
        )
    
    # 对话型 Chatflow 使用 chat-messages 接口（非 workflows/run）
    t0 = time.time()
    result = dify_integration.get_client().send_message(
        message=req.message,
        user_id=req.user_id,
    )
    elapsed_ms = int((time.time() - t0) * 1000)
    
    # 处理Dify响应
    if result.get("status") == "error":
        # Dify调用失败，降级到LangGraph
        fallback_result = run_workflow(
            message=req.message,
            patient=req.patient_context.model_dump(),
            history=[]
        )
        return ChatResponse(
            session_id=session_id,
            answer=fallback_result.get("answer", ""),
            risk_level=fallback_result.get("risk_level", "低风险"),
            suggestions=[],
            recommended_department=fallback_result.get("department", "内科"),
            thinking_steps=[],
            disclaimer=DISCLAIMER,
            evidence=[],
            agent_trace=[],
            metrics={
                "dify_enabled": True,
                "dify_used": False,
                "fallback": True,
                "orchestrator": "langgraph",
                "elapsed_ms": elapsed_ms,
            }
        )
    
    # 解析Dify工作流输出
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
            "orchestrator": "dify",
            "elapsed_ms": elapsed_ms,
        }
    )


@router.get("/sessions")
async def sessions():
    return {"sessions": list_sessions()}


@router.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str):
    return {"messages": list_messages(session_id, limit=100)}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    clear_session(session_id)
    return {"ok": True}


@router.delete("/sessions")
async def delete_all_sessions():
    clear_all()
    return {"ok": True}
