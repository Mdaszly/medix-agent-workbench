"""
Dify集成测试

测试内容：
1. Dify工具端点测试
2. Dify客户端测试
3. /api/chat/dify 端点测试（mock）
4. Dify工具 HTTP 端点测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.services.dify_client import DifyClient, DifyIntegration
from app.services.dify_tools import DifyToolResponse


class TestDifyTools:
    """Dify工具响应格式测试"""

    def test_success_response(self):
        result = DifyToolResponse.success({"data": "test"})
        assert result["status"] == "success"
        assert result["result"]["data"] == "test"

    def test_error_response(self):
        result = DifyToolResponse.error("error message")
        assert result["status"] == "error"
        assert result["message"] == "error message"


class TestDifyClient:
    """Dify客户端测试"""

    @patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"})
    def test_client_initialization(self):
        client = DifyClient()
        assert client.api_key == "test-key"
        assert client.app_id == "test-app-id"

    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_client_missing_config(self):
        with pytest.raises(ValueError, match="DIFY_API_KEY 未设置"):
            DifyClient()

    @patch("requests.post")
    def test_run_workflow_success(self, mock_post):
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
        mock_post.side_effect = Exception("Connection error")

        with patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"}):
            client = DifyClient()
            result = client.run_workflow({"message": "test"})
            assert result["status"] == "error"
            assert "Dify调用失败" in result["message"]

    @patch("requests.post")
    def test_send_message_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"answer": "Dify回复内容", "conversation_id": "abc"}
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id", "DIFY_TIMEOUT": "30"}):
            client = DifyClient()
            result = client.send_message("你好")
            assert result["answer"] == "Dify回复内容"

    @patch("requests.post")
    def test_send_message_failure_returns_error(self, mock_post):
        import requests as req_lib
        mock_post.side_effect = req_lib.exceptions.Timeout("timeout")

        with patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id", "DIFY_TIMEOUT": "5"}):
            client = DifyClient()
            result = client.send_message("你好")
            assert result["status"] == "error"
            assert mock_post.call_count == 2


class TestDifyIntegration:
    """Dify集成服务测试"""

    @patch.dict("os.environ", {"DIFY_API_KEY": "test-key", "DIFY_APP_ID": "test-app-id"})
    def test_integration_enabled(self):
        integration = DifyIntegration()
        assert integration.enabled is True

    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_integration_disabled(self):
        integration = DifyIntegration()
        assert integration.enabled is False

    @patch.dict("os.environ", {"DIFY_API_KEY": "", "DIFY_APP_ID": ""})
    def test_run_medical_workflow_disabled(self):
        integration = DifyIntegration()
        result = integration.run_medical_workflow("test", {})
        assert result["status"] == "error"
        assert "Dify未配置" in result["message"]


class TestChatDifyEndpoint:
    """/api/chat/dify 端点测试"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_dify_not_configured(self, client):
        with patch("app.api.chat.dify_integration") as mock_int:
            mock_int.enabled = False
            resp = client.post("/api/chat/dify", json={"message": "我发烧了"})
            assert resp.status_code == 200
            body = resp.json()
            assert body["metrics"]["dify_enabled"] is False
            assert "未配置" in body["answer"]

    def test_dify_success(self, client):
        mock_client = MagicMock()
        mock_client.send_message.return_value = {
            "answer": "请多喝水休息",
            "outputs": {"risk_level": "低风险", "department": "内科"},
        }

        with patch("app.api.chat.dify_integration") as mock_int:
            mock_int.enabled = True
            mock_int.get_client.return_value = mock_client
            resp = client.post(
                "/api/chat/dify",
                json={"message": "我发烧了", "patient_context": {"age": 30}},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["metrics"]["dify_used"] is True
            assert body["metrics"]["orchestrator"] == "dify"
            assert "多喝水" in body["answer"]

    def test_dify_fallback_to_langgraph(self, client):
        mock_client = MagicMock()
        mock_client.send_message.return_value = {
            "status": "error",
            "message": "Dify调用失败: timeout",
        }

        with patch("app.api.chat.dify_integration") as mock_int:
            mock_int.enabled = True
            mock_int.get_client.return_value = mock_client
            with patch("app.api.chat.run_workflow") as mock_wf:
                mock_wf.return_value = {
                    "answer": "降级回答",
                    "risk_level": "低风险",
                    "department": "内科",
                }
                resp = client.post("/api/chat/dify", json={"message": "胸痛"})
                assert resp.status_code == 200
                body = resp.json()
                assert body["metrics"]["fallback"] is True
                assert body["metrics"]["dify_used"] is False
                assert body["metrics"]["orchestrator"] == "langgraph"


class TestDifyToolEndpoints:
    """Dify 工具 HTTP 端点测试"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_symptom_analysis_tool(self, client):
        resp = client.post("/tools/symptom_analysis", json={"input": "我发烧咳嗽"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "result" in body

    def test_risk_assessment_tool(self, client):
        resp = client.post("/tools/risk_assessment", json={"input": "胸痛呼吸困难"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

    def test_compliance_guard_tool(self, client):
        resp = client.post(
            "/tools/compliance_guard",
            json={"input": "你必须立即服用阿莫西林"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
