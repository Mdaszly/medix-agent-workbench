from __future__ import annotations

import time
import uuid

from fastapi import APIRouter

from app.core.database import clear_all, clear_session, list_messages, list_sessions
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_orchestrator import MedicalAgentOrchestrator
from app.services.langgraph_workflow import run_workflow
from app.services.dify_client import dify_integration

router = APIRouter(prefix="/api", tags=["chat"])
orchestrator = MedicalAgentOrchestrator()

# 免责声明
DISCLAIMER = "以上内容仅用于健康科普、预问诊和就医参考，不能替代医生诊断、处方或治疗。"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await orchestrator.handle(req)


@router.post("/chat/langgraph", response_model=ChatResponse)
async def chat_langgraph(req: ChatRequest):
    """使用LangGraph工作流处理问诊请求"""
    session_id = req.session_id or str(uuid.uuid4())
    
    # 执行LangGraph工作流
    result = run_workflow(
        message=req.message,
        patient=req.patient_context.model_dump(),
        history=[]
    )
    
    return ChatResponse(
        session_id=session_id,
        answer=result.get("answer", ""),
        risk_level=result.get("risk_level", "低风险"),
        suggestions=[],
        recommended_department=result.get("department", "内科"),
        thinking_steps=[],
        disclaimer=DISCLAIMER,
        evidence=[],
        agent_trace=[],
        metrics={}
    )


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
