from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.database import clear_all, clear_session, list_messages, list_sessions
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_orchestrator import MedicalAgentOrchestrator
from app.services.langgraph_workflow import run_workflow

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
