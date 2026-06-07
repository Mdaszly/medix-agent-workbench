"""
Dify客户端 - 用于本地系统调用Dify工作流

设计模式：代理模式（Proxy Pattern）
- 封装Dify API调用逻辑
- 提供统一的接口供本地系统使用
"""

import os
import time
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class DifyClient:
    """Dify API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, app_id: Optional[str] = None):
        """
        初始化Dify客户端
        
        :param api_key: Dify API密钥（可选，默认从环境变量读取）
        :param app_id: Dify应用ID（可选，默认从环境变量读取）
        """
        self.api_key = api_key or os.getenv("DIFY_API_KEY", "")
        self.app_id = app_id or os.getenv("DIFY_APP_ID", "")
        self.base_url = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
        
        if not self.api_key:
            raise ValueError("DIFY_API_KEY 未设置")
        if not self.app_id:
            raise ValueError("DIFY_APP_ID 未设置")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def run_workflow(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行Dify工作流
        
        :param inputs: 工作流输入参数
        :return: 工作流执行结果
        """
        url = f"{self.base_url}/workflows/{self.app_id}/run"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"inputs": inputs},
                timeout=10,
            )
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            # 降级处理：返回错误信息，调用方可以选择使用本地工作流
            return {
                "status": "error",
                "message": f"Dify调用失败: {str(e)}",
                "error_type": "dify_connection_error"
            }
    
    def send_message(self, message: str, user_id: str = "default", inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送消息到Dify应用（支持Chatflow）
        
        :param message: 用户消息/问题
        :param user_id: 用户ID
        :param inputs: 额外输入参数（可选）
        :return: 消息响应
        """
        url = f"{self.base_url}/chat-messages"
        
        payload = {
            "inputs": inputs or {},
            "query": message,
            "response_mode": "blocking",
            "user": user_id,
            "conversation_id": ""
        }

        timeout = int(os.getenv("DIFY_TIMEOUT", "90"))
        last_error: Optional[Exception] = None
        for attempt in range(2):
            try:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                result = response.json()

                if "answer" in result:
                    return result
                if "output" in result:
                    return {"answer": result["output"]}
                return result
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < 1:
                    time.sleep(1.0)

        return {
            "status": "error",
            "message": f"Dify调用失败: {last_error}",
            "error_type": "dify_connection_error",
        }
    
    def get_workflow_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取工作流执行状态
        
        :param task_id: 任务ID
        :return: 任务状态
        """
        url = f"{self.base_url}/workflows/{self.app_id}/tasks/{task_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Dify调用失败: {str(e)}",
                "error_type": "dify_connection_error"
            }


class DifyIntegration:
    """Dify集成服务 - 提供统一的Dify调用接口，支持降级"""
    
    def __init__(self):
        self._client: Optional[DifyClient] = None
        self._enabled = self._check_dify_config()
    
    def _check_dify_config(self) -> bool:
        """检查Dify配置是否完整"""
        return bool(os.getenv("DIFY_API_KEY") and os.getenv("DIFY_APP_ID"))
    
    @property
    def enabled(self) -> bool:
        """Dify是否可用"""
        return self._enabled
    
    def get_client(self) -> DifyClient:
        """获取Dify客户端实例"""
        if not self._client:
            self._client = DifyClient()
        return self._client
    
    def run_medical_workflow(self, message: str, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行医疗问诊工作流
        
        :param message: 用户症状描述
        :param patient: 患者信息
        :return: 工作流执行结果
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Dify未配置",
                "error_type": "dify_not_configured"
            }
        
        inputs = {
            "message": message,
            "patient": patient
        }
        
        return self.get_client().run_workflow(inputs)
    
    def process_chat(self, message: str, patient: Dict[str, Any], user_id: str = "default") -> Dict[str, Any]:
        """
        处理聊天消息
        
        :param message: 用户消息
        :param patient: 患者信息
        :param user_id: 用户ID
        :return: 聊天响应
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Dify未配置",
                "error_type": "dify_not_configured"
            }
        
        # 尝试使用工作流
        workflow_result = self.run_medical_workflow(message, patient)
        
        if workflow_result.get("status") == "error":
            # 降级到消息接口
            return self.get_client().send_message(message, user_id)
        
        return workflow_result


# 全局实例
dify_integration = DifyIntegration()
