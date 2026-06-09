"""
LangGraph 工作流 — 医疗问诊（阶段 1 深化）

设计模式：
1. 状态模式：MedicalState 承载全流程上下文
2. 策略模式：RiskRouteStrategy 条件路由
3. 适配器模式：SkillsAdapter 集成现有 Skills

阶段 1 能力：
- agent_trace / thinking_steps（对齐 MedicalSwarm 可观测性）
- MemorySaver Checkpointer（同 session 多轮 + interrupt 恢复）
- Human-in-the-loop：高风险 interrupt 等待确认后再输出紧急响应

Swarm vs LangGraph 三点差异：
1. Swarm 用 step() 隐式记录；LangGraph 在节点内写 state.agent_trace，可持久化回放
2. Swarm 流程嵌在 async run()；LangGraph 用条件边显式声明 emergency/normal 分支
3. Swarm 无暂停；LangGraph interrupt 可在高风险时暂停，API 确认后 Command(resume) 继续
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# ========== 状态模式 ==========
class MedicalState(TypedDict, total=False):
    message: str
    patient: Dict[str, Any]
    history: List[Dict[str, Any]]
    symptom_profile: Dict[str, Any]
    risk_hint: Dict[str, Any]
    risk_level: str
    evidence: List[Dict[str, Any]]
    structured: Dict[str, Any]
    answer: str
    department: str
    agent_trace: List[Dict[str, Any]]
    thinking_steps: List[str]
    human_confirmed: bool


_compiled_graph = None
_checkpointer = MemorySaver()


def _trace(
    state: MedicalState,
    agent: str,
    action: str,
    detail: str,
    duration_ms: int = 0,
) -> Dict[str, Any]:
    """追加 agent 轨迹，对齐 MedicalSwarm.step() 语义。"""
    trace = list(state.get("agent_trace") or [])
    steps = list(state.get("thinking_steps") or [])
    trace.append(
        {"agent": agent, "action": action, "detail": detail, "duration_ms": duration_ms}
    )
    steps.append(f"{agent}: {detail}")
    return {"agent_trace": trace, "thinking_steps": steps}


def _timed_node(agent: str, action: str, detail_fn: Callable[[MedicalState], str], fn: Callable):
    """包装节点：自动记录耗时与 trace。"""

    def wrapper(state: MedicalState) -> MedicalState:
        t0 = time.time()
        result = fn(state)
        ms = int((time.time() - t0) * 1000)
        detail = detail_fn(result if isinstance(result, dict) else state)
        traced = _trace(result, agent, action, detail, ms)
        return {**result, **traced}

    return wrapper


def build_initial_state(
    message: str,
    patient: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
) -> MedicalState:
    return {
        "message": message,
        "patient": patient,
        "history": history or [],
        "symptom_profile": {},
        "risk_hint": {},
        "risk_level": "",
        "evidence": [],
        "structured": {},
        "answer": "",
        "department": "",
        "agent_trace": [],
        "thinking_steps": [],
        "human_confirmed": False,
    }


# ========== 适配器模式 ==========
class SkillsAdapter:
    @staticmethod
    def adapt_analyze_symptoms(func: Callable) -> Callable:
        def wrapper(state: MedicalState) -> MedicalState:
            symptom_profile = func(state["message"])
            return {**state, "symptom_profile": symptom_profile}

        return wrapper

    @staticmethod
    def adapt_assess_risk(func: Callable) -> Callable:
        def wrapper(state: MedicalState) -> MedicalState:
            risk_hint = func(state["message"])
            return {**state, "risk_hint": risk_hint, "risk_level": risk_hint["risk_level"]}

        return wrapper


# ========== 策略模式 ==========
class RiskRouteStrategy:
    def decide(self, state: MedicalState) -> str:
        return "emergency" if state.get("risk_level") == "高风险" else "normal"


# ========== 节点实现 ==========
def symptom_analysis_node(state: MedicalState) -> MedicalState:
    from app.services.skills import analyze_symptoms

    symptom_profile = analyze_symptoms(state["message"])
    return {**state, "symptom_profile": symptom_profile}


def risk_assessment_node(state: MedicalState) -> MedicalState:
    from app.services.skills import assess_risk

    risk_hint = assess_risk(state["message"])
    return {**state, "risk_hint": risk_hint, "risk_level": risk_hint["risk_level"]}


def human_confirm_node(state: MedicalState) -> MedicalState:
    """Human-in-the-loop：高风险暂停，等待 API resume 确认。"""
    confirmed = interrupt(
        {
            "type": "high_risk_confirmation",
            "risk_level": state.get("risk_level", "高风险"),
            "message": state.get("message", ""),
            "prompt": "检测到高风险症状，请确认已了解需立即就医。回复 confirmed=true 继续。",
        }
    )
    return {**state, "human_confirmed": bool(confirmed)}


def rag_retrieval_node(state: MedicalState) -> MedicalState:
    from app.services.rag_service import RAGService

    rag = RAGService()
    query = (
        f"{state['message']} {state['patient'].get('age', '')} "
        f"{state['patient'].get('gender', '')}"
    )
    raw = rag.search(query, top_k=6)
    evidence = [e.model_dump() if hasattr(e, "model_dump") else dict(e) for e in raw]
    return {**state, "evidence": evidence}


def llm_reasoning_node(state: MedicalState) -> MedicalState:
    from app.services.llm_client import LLMClient
    from app.services.medical_business import (
        build_system_prompt,
        build_user_prompt,
        parse_json_object,
        parse_narrative_answer,
    )

    llm = LLMClient()

    if not llm.enabled:
        structured = {
            "risk_level": state.get("risk_level", "低风险"),
            "recommended_department": "内科",
            "conclusion": "当前AI模型不可用，建议线下就医咨询。",
            "reasoning": "基于本地规则分析",
            "care_advice": ["请及时就医", "注意休息"],
        }
        return {**state, "structured": structured, "department": "内科"}

    try:
        system_prompt = build_system_prompt("consultation")
        user_prompt = build_user_prompt(
            "consultation",
            state["message"],
            state["patient"],
            state.get("history") or [],
            state.get("symptom_profile") or {},
            state.get("risk_hint") or {},
            state.get("evidence") or [],
            [],
        )
        raw = llm.chat_sync(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        structured = parse_json_object(raw) or parse_narrative_answer(raw, "consultation")
        department = structured.get("recommended_department", "内科")
        return {**state, "structured": structured, "department": department}
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("llm_reasoning_node failed: %s", exc, exc_info=True)
        structured = {
            "risk_level": state.get("risk_level", "低风险"),
            "recommended_department": "内科",
            "conclusion": "AI推理异常，建议线下就医咨询。",
            "reasoning": "推理异常降级",
            "care_advice": ["请及时就医"],
        }
        return {**state, "structured": structured, "department": "内科"}


def emergency_response_node(state: MedicalState) -> MedicalState:
    answer = """
紧急提醒：您的症状属于高风险，请立即前往医院急诊科就诊！

风险等级：高风险
推荐科室：急诊科
建议：
- 立即拨打120或前往附近医院急诊
- 保持镇静，避免剧烈活动
- 如有同行人员，请告知症状情况
- 准备好既往病史和用药信息

免责声明：以上内容仅用于健康科普，不能替代医生诊断。
""".strip()
    return {**state, "answer": answer, "department": "急诊科", "risk_level": "高风险"}


def normal_response_node(state: MedicalState) -> MedicalState:
    from app.services.medical_business import normalize_department, normalize_risk, render_answer
    from app.services.skills import compliance_guard

    structured = state.get("structured") or {}
    department = normalize_department(structured.get("recommended_department"), "consultation")
    risk_level = normalize_risk(structured.get("risk_level"))
    answer = compliance_guard(
        render_answer("consultation", structured, department, risk_level, state.get("message", ""))
    )
    return {**state, "answer": answer, "department": department, "risk_level": risk_level}


def route_by_risk(state: MedicalState) -> str:
    return RiskRouteStrategy().decide(state)


# ========== 构图 ==========
def build_medical_graph(checkpointer=None):
    graph = StateGraph(MedicalState)

    graph.add_node(
        "symptom_analysis",
        _timed_node(
            "ContextAgent",
            "symptom_analysis",
            lambda s: f"症状分析完成，识别 {len((s.get('symptom_profile') or {}).get('symptoms', []))} 个症状线索",
            symptom_analysis_node,
        ),
    )
    graph.add_node(
        "risk_assessment",
        _timed_node(
            "ContextAgent",
            "risk_assessment",
            lambda s: f"风险评估：{s.get('risk_level', '未知')}",
            risk_assessment_node,
        ),
    )
    graph.add_node(
        "human_confirm",
        _timed_node(
            "SafetyAgent",
            "human_confirm",
            lambda s: "已确认高风险" if s.get("human_confirmed") else "等待或跳过确认",
            human_confirm_node,
        ),
    )
    graph.add_node(
        "rag_retrieval",
        _timed_node(
            "RAGAgent",
            "retrieve",
            lambda s: f"本地知识库召回 {len(s.get('evidence') or [])} 条证据",
            rag_retrieval_node,
        ),
    )
    graph.add_node(
        "llm_reasoning",
        _timed_node(
            "ReasoningAgent",
            "llm_reasoning",
            lambda s: (
                "LLM 结构化推理完成"
                if s.get("structured") and s["structured"].get("reasoning") != "推理异常降级"
                else "LLM 推理失败，已使用降级模板"
            ),
            llm_reasoning_node,
        ),
    )
    graph.add_node(
        "emergency_response",
        _timed_node(
            "SafetyAgent",
            "emergency",
            lambda _: "输出高风险紧急响应",
            emergency_response_node,
        ),
    )
    graph.add_node(
        "normal_response",
        _timed_node(
            "FormatterAgent",
            "render",
            lambda s: f"生成回答，推荐科室 {s.get('department', '内科')}",
            normal_response_node,
        ),
    )

    graph.add_edge(START, "symptom_analysis")
    graph.add_edge("symptom_analysis", "risk_assessment")
    graph.add_conditional_edges(
        "risk_assessment",
        route_by_risk,
        {"emergency": "human_confirm", "normal": "rag_retrieval"},
    )
    graph.add_edge("human_confirm", "emergency_response")
    graph.add_edge("rag_retrieval", "llm_reasoning")
    graph.add_edge("llm_reasoning", "normal_response")
    graph.add_edge("emergency_response", END)
    graph.add_edge("normal_response", END)

    return graph.compile(checkpointer=checkpointer)


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_medical_graph(checkpointer=_checkpointer)
    return _compiled_graph


def _format_result(
    result: Dict[str, Any],
    session_id: str,
    pending_next: tuple = (),
) -> Dict[str, Any]:
    interrupted = bool(result.get("__interrupt__")) or bool(pending_next)
    if (
        not interrupted
        and result.get("risk_level") == "高风险"
        and not (result.get("answer") or "").strip()
    ):
        interrupted = True
    out = {k: v for k, v in result.items() if not k.startswith("__")}
    out["session_id"] = session_id
    out["interrupted"] = interrupted
    if interrupted:
        if result.get("__interrupt__"):
            out["interrupt_payload"] = result["__interrupt__"]
        elif pending_next:
            out["interrupt_payload"] = [{"next": list(pending_next)}]
    return out


def run_workflow(
    message: str,
    patient: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """执行工作流；高风险时可能在 human_confirm 处 interrupt。"""
    graph = get_compiled_graph()
    sid = session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": sid}}

    pending = graph.get_state(config)
    if pending.next:
        return {
            "session_id": sid,
            "interrupted": True,
            "answer": "",
            "risk_level": "",
            "department": "",
            "agent_trace": [],
            "thinking_steps": [],
            "pending_interrupt": True,
            "message": "该会话有待确认的高风险 interrupt，请调用 resume_workflow",
        }

    initial = build_initial_state(message, patient, history)
    # RouterAgent 入口 trace
    initial.update(
        _trace(initial, "RouterAgent", "route", "进入 LangGraph 医疗问诊工作流")
    )

    result = graph.invoke(initial, config)
    snap = graph.get_state(config)
    return _format_result(result, sid, pending_next=tuple(snap.next or ()))


def resume_workflow(session_id: str, confirmed: bool = True) -> Dict[str, Any]:
    """恢复被 interrupt 的高风险工作流。"""
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}

    pending = graph.get_state(config)
    if not pending.next:
        return {
            "session_id": session_id,
            "interrupted": False,
            "answer": "",
            "risk_level": "",
            "department": "",
            "agent_trace": [],
            "thinking_steps": [],
            "error": "no_pending_interrupt",
            "message": "该会话没有待恢复的中断",
        }

    result = graph.invoke(Command(resume=confirmed), config)
    snap = graph.get_state(config)
    formatted = _format_result(result, session_id, pending_next=tuple(snap.next or ()))
    if not formatted.get("interrupted"):
        formatted.update(
            _trace(
                formatted,
                "SafetyAgent",
                "confirmed" if confirmed else "declined",
                "用户确认高风险响应" if confirmed else "用户拒绝，仍输出紧急提醒",
            )
        )
    return formatted


def get_session_state(session_id: str) -> Dict[str, Any]:
    """查看 checkpoint 状态（调试 / 前端展示）。"""
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}
    snap = graph.get_state(config)
    return {
        "session_id": session_id,
        "next_nodes": list(snap.next or ()),
        "values": snap.values,
        "interrupted": bool(snap.next),
    }
