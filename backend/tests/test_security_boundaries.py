from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.skills import assess_risk, compliance_guard


def test_destructive_session_api_requires_admin_token_when_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-admin")
    from main import app

    client = TestClient(app)
    resp = client.delete("/api/sessions")

    assert resp.status_code == 401


def test_destructive_session_api_accepts_admin_token_when_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-admin")
    from main import app

    client = TestClient(app)
    resp = client.delete("/api/sessions", headers={"X-Admin-Token": "secret-admin"})

    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_dify_tools_require_shared_token_when_configured(monkeypatch):
    monkeypatch.setenv("DIFY_TOOL_TOKEN", "secret-tool")
    from main import app

    client = TestClient(app)
    resp = client.post("/tools/risk_assessment", json={"input": "胸痛呼吸困难"})

    assert resp.status_code == 401


def test_dify_tools_accept_shared_token_when_configured(monkeypatch):
    monkeypatch.setenv("DIFY_TOOL_TOKEN", "secret-tool")
    from main import app

    client = TestClient(app)
    resp = client.post(
        "/tools/risk_assessment",
        json={"input": "胸痛呼吸困难"},
        headers={"X-Dify-Tool-Token": "secret-tool"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert resp.json()["result"]["risk_level"] == "高风险"


def test_high_risk_symptoms_are_not_routed_to_normal_advice():
    risk = assess_risk("我胸痛，呼吸困难，还出冷汗")

    assert risk["risk_level"] == "高风险"
    assert "急救" in risk["advice"] or "线下就医" in risk["advice"]


def test_compliance_guard_removes_diagnostic_and_prescription_language():
    unsafe = "你确诊为肺炎，必须服用阿莫西林，剂量是每天三次。"
    guarded = compliance_guard(unsafe)

    assert "确诊为" not in guarded
    assert "必须服用" not in guarded
    assert "剂量是" not in guarded
    assert "不能替代医生诊断" in guarded
