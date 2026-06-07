from __future__ import annotations

from fastapi import APIRouter

from app.core.database import clear_all, clear_session, list_messages, list_sessions
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_orchestrator import MedicalAgentOrchestrator

router = APIRouter(prefix="/api", tags=["chat"])
orchestrator = MedicalAgentOrchestrator()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await orchestrator.handle(req)


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
