"""聊天响应构建辅助 — 供 API 与 Agent 网关共用。"""

from __future__ import annotations

from app.core.database import list_messages
from app.schemas.chat import AgentTrace, ChatResponse, Evidence

DISCLAIMER = "以上内容仅用于健康科普、预问诊和就医参考，不能替代医生诊断、处方或治疗。"


def load_history(session_id: str) -> list:
    rows = list_messages(session_id, limit=20)
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def langgraph_to_response(session_id: str, result: dict) -> ChatResponse:
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
