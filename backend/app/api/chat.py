from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.database import (
    add_message,
    clear_all,
    clear_session,
    list_messages,
    list_sessions,
    upsert_session,
)
from app.schemas.chat import ChatRequest, ChatResponse, LangGraphResumeRequest
from app.services.agent_gateway import dispatch, resume_langgraph
from app.services.chat_helpers import load_history
from app.services.dify_client import dify_integration
from app.services.langgraph_workflow import get_session_state

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Swarm 多 Agent 链路（兼容旧端点）。"""
    req.orchestrator = "swarm"
    return await chat_route(req)


@router.post("/chat/route", response_model=ChatResponse)
async def chat_route(req: ChatRequest):
    """统一编排入口：按 orchestrator 字段路由到 Swarm / LangGraph / Dify。"""
    session_id = req.session_id or str(uuid.uuid4())
    upsert_session(session_id, title=req.message[:40])
    history = load_history(session_id) if req.session_id else []

    resp = await dispatch(
        req=req,
        mode=req.orchestrator,
        history=history,
        session_id=session_id,
        dify_integration=dify_integration,
    )

    add_message(session_id, "user", req.message)
    if not resp.metrics.get("interrupted"):
        add_message(session_id, "assistant", resp.answer)

    return resp


@router.post("/chat/langgraph", response_model=ChatResponse)
async def chat_langgraph(req: ChatRequest):
    req.orchestrator = "langgraph"
    return await chat_route(req)


@router.post("/chat/langgraph/resume", response_model=ChatResponse)
async def chat_langgraph_resume(req: LangGraphResumeRequest):
    result = resume_langgraph(req)
    if not result.metrics.get("interrupted") and result.answer:
        add_message(req.session_id, "assistant", result.answer)
    return result


@router.get("/chat/langgraph/state/{session_id}")
async def chat_langgraph_state(session_id: str):
    return get_session_state(session_id)


@router.post("/chat/dify", response_model=ChatResponse)
async def chat_dify(req: ChatRequest):
    req.orchestrator = "dify"
    return await chat_route(req)


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
