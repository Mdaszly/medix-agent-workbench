"""
LangGraph工作流测试

测试内容：
1. 状态模式：验证状态流转正确性
2. 策略模式：验证路由决策正确性
3. 适配器模式：验证Skills集成正确性
4. 工作流整体测试
"""

import pytest
from app.services.langgraph_workflow import (
    MedicalState,
    RiskRouteStrategy,
    symptom_analysis_node,
    risk_assessment_node,
    build_medical_graph,
    run_workflow
)


class TestStatePattern:
    """状态模式测试"""
    
    def test_state_initialization(self):
        """测试状态初始化"""
        state: MedicalState = {
            "message": "test",
            "patient": {"age": "30", "gender": "男"},
            "history": [],
            "symptom_profile": {},
            "risk_hint": {},
            "risk_level": "",
            "evidence": [],
            "structured": {},
            "answer": "",
            "department": ""
        }
        
        assert state["message"] == "test"
        assert state["patient"]["age"] == "30"
        assert state["risk_level"] == ""
    
    def test_state_update(self):
        """测试状态更新"""
        state: MedicalState = {
            "message": "test",
            "patient": {},
            "history": [],
            "symptom_profile": {},
            "risk_hint": {},
            "risk_level": "",
            "evidence": [],
            "structured": {},
            "answer": "",
            "department": ""
        }
        
        # 更新状态
        updated = {**state, "risk_level": "高风险", "department": "急诊科"}
        
        assert updated["risk_level"] == "高风险"
        assert updated["department"] == "急诊科"


class TestStrategyPattern:
    """策略模式测试"""
    
    def test_risk_strategy_high_risk(self):
        """测试高风险路由"""
        strategy = RiskRouteStrategy()
        state = {"risk_level": "高风险"}
        assert strategy.decide(state) == "emergency"
    
    def test_risk_strategy_normal(self):
        """测试正常路由"""
        strategy = RiskRouteStrategy()
        state = {"risk_level": "低风险"}
        assert strategy.decide(state) == "normal"
        
        state = {"risk_level": "中风险"}
        assert strategy.decide(state) == "normal"
    
    def test_risk_strategy_default(self):
        """测试默认路由"""
        strategy = RiskRouteStrategy()
        state = {"risk_level": ""}
        assert strategy.decide(state) == "normal"


class TestAdapterPattern:
    """适配器模式测试"""
    
    def test_symptom_analysis_adapter(self):
        """测试症状分析节点"""
        state: MedicalState = {
            "message": "我头痛",
            "patient": {},
            "history": [],
            "symptom_profile": {},
            "risk_hint": {},
            "risk_level": "",
            "evidence": [],
            "structured": {},
            "answer": "",
            "department": ""
        }
        
        result = symptom_analysis_node(state)
        
        assert "symptom_profile" in result
        assert isinstance(result["symptom_profile"], dict)
        assert "symptoms" in result["symptom_profile"]
    
    def test_risk_assessment_adapter(self):
        """测试风险评估节点"""
        state: MedicalState = {
            "message": "我胸痛，呼吸困难",
            "patient": {},
            "history": [],
            "symptom_profile": {},
            "risk_hint": {},
            "risk_level": "",
            "evidence": [],
            "structured": {},
            "answer": "",
            "department": ""
        }
        
        result = risk_assessment_node(state)
        
        assert "risk_level" in result
        assert result["risk_level"] == "高风险"
        assert "risk_hint" in result


class TestWorkflow:
    """工作流整体测试"""
    
    def test_workflow_graph_build(self):
        """测试工作流图构建"""
        graph = build_medical_graph()
        assert graph is not None
    
    def test_workflow_high_risk(self):
        """测试高风险症状路由"""
        result = run_workflow(
            message="我胸痛，呼吸困难",
            patient={"age": "45", "gender": "男"}
        )
        
        assert result["risk_level"] == "高风险"
        assert result["department"] == "急诊科"
        assert "紧急提醒" in result["answer"]
    
    def test_workflow_normal(self):
        """测试正常症状路由"""
        result = run_workflow(
            message="我有点咳嗽",
            patient={"age": "30", "gender": "女"}
        )
        
        assert result["risk_level"] in ["低风险", "中风险"]
        assert result["department"] is not None
        assert result["answer"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
