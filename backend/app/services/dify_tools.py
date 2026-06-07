"""
Dify工具服务 - 将现有Skills暴露为Dify可调用的HTTP工具

设计模式：适配器模式（Adapter Pattern）
- 将现有Skills适配为Dify工具格式
- 统一处理请求格式和响应格式
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from app.services.skills import (
    analyze_symptoms,
    assess_risk,
    compliance_guard,
    lifestyle_recommendations
)

router = APIRouter(prefix="/tools", tags=["dify-tools"])


class DifyToolResponse:
    """Dify工具响应格式"""
    
    @staticmethod
    def success(data: Any) -> Dict[str, Any]:
        """成功响应"""
        return {
            "result": data,
            "status": "success"
        }
    
    @staticmethod
    def error(message: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            "result": None,
            "status": "error",
            "message": message
        }


@router.post("/symptom_analysis")
async def tool_symptom_analysis(request: Dict[str, Any]):
    """
    症状分析工具 - 分析用户描述的症状
    
    Dify工具参数：
    - input: 用户症状描述
    
    返回：
    - symptoms: 识别到的症状列表
    - severity: 症状严重程度
    - possible_diseases: 可能的疾病
    """
    try:
        message = request.get("input", "") or request.get("query", "")
        if not message:
            raise ValueError("缺少输入参数")
        
        result = analyze_symptoms(message)
        return DifyToolResponse.success(result)
    
    except Exception as e:
        return DifyToolResponse.error(str(e))


@router.post("/risk_assessment")
async def tool_risk_assessment(request: Dict[str, Any]):
    """
    风险评估工具 - 评估症状的风险等级
    
    Dify工具参数：
    - input: 用户症状描述
    
    返回：
    - risk_level: 风险等级（低/中/高）
    - risk_factors: 风险因素
    - recommendations: 建议
    """
    try:
        message = request.get("input", "") or request.get("query", "")
        if not message:
            raise ValueError("缺少输入参数")
        
        result = assess_risk(message)
        return DifyToolResponse.success(result)
    
    except Exception as e:
        return DifyToolResponse.error(str(e))


@router.post("/compliance_guard")
async def tool_compliance_guard(request: Dict[str, Any]):
    """
    合规检查工具 - 确保回答符合医疗合规要求
    
    Dify工具参数：
    - input: 待检查的回答文本
    
    返回：
    - cleaned_text: 合规处理后的文本
    - warnings: 警告信息列表
    """
    try:
        text = request.get("input", "") or request.get("text", "")
        if not text:
            raise ValueError("缺少输入参数")
        
        result = compliance_guard(text)
        return DifyToolResponse.success({
            "cleaned_text": result,
            "warnings": []
        })
    
    except Exception as e:
        return DifyToolResponse.error(str(e))


@router.post("/lifestyle_recommendations")
async def tool_lifestyle_recommendations(request: Dict[str, Any]):
    """
    生活方式建议工具 - 根据症状提供生活方式建议
    
    Dify工具参数：
    - input: 用户症状或健康状况描述
    - patient_info: 患者基本信息（可选）
    
    返回：
    - recommendations: 建议列表
    - diet: 饮食建议
    - exercise: 运动建议
    - sleep: 睡眠建议
    """
    try:
        message = request.get("input", "") or request.get("query", "")
        patient_info = request.get("patient_info", {})
        
        if not message:
            raise ValueError("缺少输入参数")
        
        result = lifestyle_recommendations(message, patient_info)
        return DifyToolResponse.success(result)
    
    except Exception as e:
        return DifyToolResponse.error(str(e))


# Dify工具元数据注册
def get_tool_metadata() -> Dict[str, Dict[str, Any]]:
    """获取所有工具的元数据，用于Dify注册"""
    return {
        "symptom_analysis": {
            "name": "symptom_analysis",
            "description": "分析用户描述的症状，识别症状类型和可能的疾病",
            "parameters": [
                {"name": "input", "type": "string", "required": True, "description": "用户症状描述"}
            ]
        },
        "risk_assessment": {
            "name": "risk_assessment",
            "description": "评估症状的风险等级，判断是否需要紧急处理",
            "parameters": [
                {"name": "input", "type": "string", "required": True, "description": "用户症状描述"}
            ]
        },
        "compliance_guard": {
            "name": "compliance_guard",
            "description": "检查医疗回答是否符合合规要求，添加免责声明",
            "parameters": [
                {"name": "input", "type": "string", "required": True, "description": "待检查的回答文本"}
            ]
        },
        "lifestyle_recommendations": {
            "name": "lifestyle_recommendations",
            "description": "根据用户症状提供生活方式建议，包括饮食、运动、睡眠等",
            "parameters": [
                {"name": "input", "type": "string", "required": True, "description": "用户症状描述"},
                {"name": "patient_info", "type": "object", "required": False, "description": "患者基本信息"}
            ]
        }
    }
