"""
LangGraph工作流实现 - 医疗问诊工作流

设计模式应用：
1. 状态模式 (State Pattern): MedicalState定义工作流状态
2. 策略模式 (Strategy Pattern): 路由决策策略
3. 适配器模式 (Adapter Pattern): 现有Skills集成
"""

from typing import TypedDict, List, Dict, Any, Callable
from langgraph.graph import StateGraph, START, END

# ========== 状态模式：定义工作流状态 ==========
class MedicalState(TypedDict):
    """医疗问诊状态定义"""
    message: str                    # 用户输入消息
    patient: Dict[str, Any]         # 患者信息
    history: List[Dict[str, Any]]   # 对话历史
    symptom_profile: Dict[str, Any] # 症状分析结果
    risk_hint: Dict[str, Any]       # 风险评估结果
    risk_level: str                 # 风险等级（低/中/高）
    evidence: List[Any]             # RAG证据列表
    structured: Dict[str, Any]      # LLM结构化输出
    answer: str                     # 最终回答
    department: str                 # 推荐科室


# ========== 适配器模式：Skills集成 ==========
class SkillsAdapter:
    """技能适配器 - 将现有Skills适配为LangGraph节点格式"""
    
    @staticmethod
    def adapt_analyze_symptoms(func: Callable) -> Callable:
        """适配症状分析函数"""
        def wrapper(state: MedicalState) -> MedicalState:
            symptom_profile = func(state["message"])
            return {**state, "symptom_profile": symptom_profile}
        return wrapper
    
    @staticmethod
    def adapt_assess_risk(func: Callable) -> Callable:
        """适配风险评估函数"""
        def wrapper(state: MedicalState) -> MedicalState:
            risk_hint = func(state["message"])
            return {**state, "risk_hint": risk_hint, "risk_level": risk_hint["risk_level"]}
        return wrapper
    
    @staticmethod
    def adapt_compliance_guard(func: Callable) -> Callable:
        """适配合规检查函数"""
        def wrapper(state: MedicalState) -> MedicalState:
            answer = func(state["answer"])
            return {**state, "answer": answer}
        return wrapper


# ========== 策略模式：路由决策 ==========
class RiskRouteStrategy:
    """基于风险等级的路由策略"""
    def decide(self, state: MedicalState) -> str:
        risk_level = state.get("risk_level", "低风险")
        return "emergency" if risk_level == "高风险" else "normal"


# ========== 工作流节点实现 ==========
def symptom_analysis_node(state: MedicalState) -> MedicalState:
    """症状分析节点"""
    from app.services.skills import analyze_symptoms
    symptom_profile = analyze_symptoms(state["message"])
    return {**state, "symptom_profile": symptom_profile}


def risk_assessment_node(state: MedicalState) -> MedicalState:
    """风险评估节点"""
    from app.services.skills import assess_risk
    risk_hint = assess_risk(state["message"])
    return {**state, "risk_hint": risk_hint, "risk_level": risk_hint["risk_level"]}


def rag_retrieval_node(state: MedicalState) -> MedicalState:
    """RAG检索节点"""
    from app.services.rag_service import RAGService
    rag = RAGService()
    query = f"{state['message']} {state['patient'].get('age', '')} {state['patient'].get('gender', '')}"
    evidence = rag.search(query, top_k=6)
    return {**state, "evidence": evidence}


def llm_reasoning_node(state: MedicalState) -> MedicalState:
    """LLM推理节点（带降级策略）"""
    from app.services.llm_client import LLMClient
    from app.services.medical_business import build_system_prompt, build_user_prompt, parse_json_object, parse_narrative_answer
    
    llm = LLMClient()
    
    if not llm.enabled:
        # 降级到本地规则
        structured = {
            "risk_level": state["risk_level"],
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
            state["history"],
            state["symptom_profile"],
            state["risk_hint"],
            state["evidence"],
            []
        )
        
        raw = llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        structured = parse_json_object(raw)
        if not structured:
            structured = parse_narrative_answer(raw, "consultation")
        
        department = structured.get("recommended_department", "内科")
        return {**state, "structured": structured, "department": department}
    
    except Exception:
        # 降级处理
        structured = {
            "risk_level": state["risk_level"],
            "recommended_department": "内科",
            "conclusion": "AI推理异常，建议线下就医咨询。",
            "reasoning": "推理异常降级",
            "care_advice": ["请及时就医"],
        }
        return {**state, "structured": structured, "department": "内科"}


def emergency_response_node(state: MedicalState) -> MedicalState:
    """紧急响应节点"""
    answer = f"""
紧急提醒：您的症状属于高风险，请立即前往医院急诊科就诊！

风险等级：高风险
推荐科室：急诊科
建议：
- 立即拨打120或前往附近医院急诊
- 保持镇静，避免剧烈活动
- 如有同行人员，请告知症状情况
- 准备好既往病史和用药信息

免责声明：以上内容仅用于健康科普，不能替代医生诊断。
"""
    return {**state, "answer": answer, "department": "急诊科"}


def normal_response_node(state: MedicalState) -> MedicalState:
    """正常响应节点"""
    from app.services.medical_business import render_answer, normalize_department, normalize_risk
    from app.services.skills import compliance_guard
    
    structured = state.get("structured", {})
    department = normalize_department(structured.get("recommended_department"), "consultation")
    risk_level = normalize_risk(structured.get("risk_level"))
    
    answer = render_answer("consultation", structured, department, risk_level)
    answer = compliance_guard(answer)
    
    return {**state, "answer": answer, "department": department, "risk_level": risk_level}


# ========== 路由函数 ==========
def route_by_risk(state: MedicalState) -> str:
    """基于风险等级的路由"""
    strategy = RiskRouteStrategy()
    return strategy.decide(state)


# ========== 构建工作流图 ==========
def build_medical_graph():
    """构建医疗问诊工作流图"""
    graph = StateGraph(MedicalState)
    
    # 添加节点
    graph.add_node("symptom_analysis", symptom_analysis_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("llm_reasoning", llm_reasoning_node)
    graph.add_node("emergency_response", emergency_response_node)
    graph.add_node("normal_response", normal_response_node)
    
    # 添加边
    graph.add_edge(START, "symptom_analysis")
    graph.add_edge("symptom_analysis", "risk_assessment")
    
    # 条件路由：高风险直接进入紧急响应
    graph.add_conditional_edges(
        "risk_assessment",
        route_by_risk,
        {
            "emergency": "emergency_response",
            "normal": "rag_retrieval"
        }
    )
    
    # 正常流程
    graph.add_edge("rag_retrieval", "llm_reasoning")
    graph.add_edge("llm_reasoning", "normal_response")
    
    # 结束节点
    graph.add_edge("emergency_response", END)
    graph.add_edge("normal_response", END)
    
    return graph.compile()


# ========== 工作流执行入口 ==========
def run_workflow(message: str, patient: Dict[str, Any], history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """执行医疗问诊工作流"""
    graph = build_medical_graph()
    
    initial_state: MedicalState = {
        "message": message,
        "patient": patient,
        "history": history or [],
        "symptom_profile": {},
        "risk_hint": {},
        "risk_level": "",
        "evidence": [],
        "structured": {},
        "answer": "",
        "department": ""
    }
    
    result = graph.invoke(initial_state)
    return result
