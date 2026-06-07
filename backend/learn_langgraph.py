"""
LangGraph最简单的学习例子
跟着这个文件一步步学，就能理解LangGraph了
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# 1. 定义State（状态）：每个节点之间传递的数据
class AgentState(TypedDict):
    # 用户输入的症状
    symptom: str
    # 风险等级：低/中/高
    risk_level: str
    # 推荐科室
    department: str
    # 结论
    conclusion: str


# 2. 定义节点1：症状分析节点
def symptom_analysis_node(state: AgentState) -> AgentState:
    """
    分析用户症状，先做简单的关键词分析
    """
    symptom = state["symptom"]
    
    # 简单的关键词匹配（实际项目会用LLM）
    if "胸痛" in symptom or "呼吸困难" in symptom:
        risk_level = "高风险"
        department = "心内科"
        conclusion = "建议立即心内科就诊"
    elif "发热" in symptom or "咳嗽" in symptom:
        risk_level = "中风险"
        department = "呼吸科"
        conclusion = "可能是呼吸道感染"
    else:
        risk_level = "低风险"
        department = "内科"
        conclusion = "建议内科进一步检查"
    
    return {
        **state,
        "risk_level": risk_level,
        "department": department,
        "conclusion": conclusion
    }


# 3. 定义节点2：建议生成节点
def suggestion_node(state: AgentState) -> AgentState:
    """
    根据风险等级生成建议
    """
    conclusion = state["conclusion"]
    
    if state["risk_level"] == "高风险":
        suggestion = "⚠️ 紧急！请立即前往附近医院急诊科就诊"
    elif state["risk_level"] == "中风险":
        suggestion = "📋 请尽快预约相关科室门诊"
    else:
        suggestion = "💊 可以先观察，有加重及时就医"
    
    return {
        **state,
        "conclusion": conclusion + "\n" + suggestion
    }


# 4. 定义条件路由：根据风险等级决定下一步
def route_after_analysis(state: AgentState) -> str:
    """
    如果是高风险，直接结束；否则再给建议
    """
    if state["risk_level"] == "高风险":
        return "end"
    return "suggestion"


# 5. 构建图
def build_graph():
    # 创建StateGraph
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("symptom_analysis", symptom_analysis_node)
    graph.add_node("suggestion", suggestion_node)
    
    # 添加边：从START到症状分析
    graph.add_edge(START, "symptom_analysis")
    
    # 添加条件边
    graph.add_conditional_edges(
        "symptom_analysis",
        route_after_analysis,
        {
            "suggestion": "suggestion",
            "end": END
        }
    )
    
    # 添加边：从建议到END
    graph.add_edge("suggestion", END)
    
    # 编译图
    return graph.compile()


# 6. 运行测试
if __name__ == "__main__":
    print("=" * 50)
    print("LangGraph学习例子")
    print("=" * 50)
    
    # 构建图
    app = build_graph()
    
    # 测试1：高风险症状
    print("\n【测试1】胸痛+呼吸困难")
    result = app.invoke({"symptom": "我胸痛，还呼吸困难"})
    print(f"风险等级: {result['risk_level']}")
    print(f"推荐科室: {result['department']}")
    print(f"结论: {result['conclusion']}")
    
    # 测试2：中风险症状
    print("\n【测试2】发热咳嗽")
    result = app.invoke({"symptom": "我发热38度，还有咳嗽"})
    print(f"风险等级: {result['risk_level']}")
    print(f"推荐科室: {result['department']}")
    print(f"结论: {result['conclusion']}")
    
    # 测试3：低风险症状
    print("\n【测试3】普通不适")
    result = app.invoke({"symptom": "我最近有点失眠"})
    print(f"风险等级: {result['risk_level']}")
    print(f"推荐科室: {result['department']}")
    print(f"结论: {result['conclusion']}")
    
    print("\n" + "=" * 50)
    print("恭喜！你已经运行了第一个LangGraph程序！")
    print("=" * 50)
