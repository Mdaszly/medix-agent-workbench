"""
Dify集成测试

测试内容：
1. Dify工具端点测试
2. Dify客户端测试
"""

import pytest
from unittest.mock import Mock, patch
from app.services.dify_client import DifyClient, DifyIntegration
from app.services.dify_tools import DifyToolResponse


class TestDifyTools:
    """Dify工具响应格式测试"""
    
    def test_success_response(self):
        """测试成功响应格式"""
        result = DifyToolResponse.success({"data": "test"})
        assert result["status"] == "success"
        assert result["result"]["data"] == "test"
    
    def test_error_response(self):
        """测试错误响应格式"""
        result = DifyToolResponse.error("error message")
        assert result["status"] == "error"
        assert result["message"] == "error message"


class TestDifyClient:
    """Dify客户端测试"""
    
    @patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"})
    def test_client_initialization(self):
        """测试客户端初始化"""
        client = DifyClient()
        assert client.api_key == "test-key"
        assert client.app_id == "test-app-id"
    
    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_client_missing_config(self):
        """测试缺少配置时的错误"""
        with pytest.raises(ValueError, match="DIFY_API_KEY 未设置"):
            DifyClient()
    
    @patch("requests.post")
    def test_run_workflow_success(self, mock_post):
        """测试工作流调用成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "outputs": {"answer": "test"}}
        mock_post.return_value = mock_response
        
        with patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"}):
            client = DifyClient()
            result = client.run_workflow({"message": "test"})
            
            assert result["status"] == "success"
            assert result["outputs"]["answer"] == "test"
    
    @patch("requests.post")
    def test_run_workflow_failure(self, mock_post):
        """测试工作流调用失败"""
        mock_post.side_effect = Exception("Connection error")
        
        with patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"}):
            client = DifyClient()
            result = client.run_workflow({"message": "test"})
            
            assert result["status"] == "error"
            assert "Dify调用失败" in result["message"]


class TestDifyIntegration:
    """Dify集成服务测试"""
    
    @patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"})
    def test_integration_enabled(self):
        """测试集成已启用"""
        integration = DifyIntegration()
        assert integration.enabled is True
    
    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_integration_disabled(self):
        """测试集成未启用"""
        integration = DifyIntegration()
        assert integration.enabled is False
    
    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_run_medical_workflow_disabled(self):
        """测试Dify未配置时的响应"""
        integration = DifyIntegration()
        result = integration.run_medical_workflow("test", {})
        
        assert result["status"] == "error"
        assert "Dify未配置" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
