# -*- coding: utf-8 -*-
"""
阶段 0 端到端检查脚本

检查项：
1. 本地后端健康
2. 公网隧道可达（若已配置 PUBLIC_TUNNEL_URL）
3. Dify API 连通
4. /api/chat/dify 是否真正走 Dify（dify_used: true）

用法:
  cd backend
  python scripts/check_e2e.py
  python scripts/check_e2e.py --skip-dify   # 跳过慢速 Dify 全链路测试
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")

PORT = int(os.getenv("BACKEND_PORT", "8012"))
BASE = f"http://127.0.0.1:{PORT}"


def _resolve_tunnel_url() -> str:
    """优先 .tunnel_url 文件，其次 PUBLIC_TUNNEL_URL 环境变量。"""
    tunnel_file = BACKEND_ROOT / ".tunnel_url"
    if tunnel_file.exists():
        from_file = tunnel_file.read_text(encoding="utf-8").strip()
        if from_file.startswith("http"):
            return from_file.rstrip("/")
    return os.getenv("PUBLIC_TUNNEL_URL", "").rstrip("/")


TUNNEL = _resolve_tunnel_url()


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def check_backend() -> bool:
    print("\n[1/4] 本地后端")
    try:
        r = requests.get(f"{BASE}/api/health", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ok":
            _ok(f"后端运行中 {BASE}")
            return True
        _fail(f"健康检查异常: {r.status_code}")
    except Exception as e:
        _fail(f"无法连接 {BASE}: {e}")
    return False


def check_tunnel() -> bool:
    print("\n[2/4] 公网隧道")
    if not TUNNEL:
        print("  [SKIP] 未设置 PUBLIC_TUNNEL_URL（见 .env.example）")
        return False

    try:
        r = requests.get(f"{TUNNEL}/api/health", timeout=15)
        if r.status_code == 200:
            _ok(f"隧道可达 {TUNNEL}")
            body = json.dumps({"input": "我发烧了"})
            r2 = requests.post(
                f"{TUNNEL}/tools/symptom_analysis",
                data=body,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            if r2.status_code == 200:
                _ok("symptom_analysis 工具可达")
                return True
            _fail(f"symptom_analysis 返回 {r2.status_code}")
        else:
            _fail(f"隧道健康检查 {r.status_code}")
    except Exception as e:
        _fail(f"隧道不可达: {e}")
        print(f"  提示: 运行 scripts/start_tunnel.ps1 并更新 Dify HTTP 节点")
    return False


def check_dify_api() -> bool:
    print("\n[3/4] Dify API")
    api_key = os.getenv("DIFY_API_KEY", "")
    if not api_key:
        _fail("DIFY_API_KEY 未配置")
        return False

    url = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1") + "/chat-messages"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"inputs": {}, "query": "ping", "response_mode": "blocking", "user": "e2e-check"},
            timeout=30,
        )
        if r.status_code == 200:
            _ok("Dify chat-messages 接口正常")
            return True
        _fail(f"状态码 {r.status_code}: {r.text[:120]}")
    except Exception as e:
        _fail(str(e))
    return False


def check_chat_dify(skip: bool = False) -> bool:
    print("\n[4/4] /api/chat/dify 全链路")
    if skip:
        print("  [SKIP] --skip-dify")
        return False

    payload = {
        "message": "你好，我发烧了",
        "patient_context": {"age": 30, "gender": "男"},
    }
    # Dify 工作流含 3 个 HTTP 节点 + LLM，正常约 60-90s，留足重试余量
    dify_timeout = int(os.getenv("DIFY_TIMEOUT", "90"))
    timeout = dify_timeout * 2 + 60
    print(f"  请求中（Dify 正常 60-90s，最长等待 {timeout}s）...")
    t0 = time.time()
    try:
        r = requests.post(f"{BASE}/api/chat/dify", json=payload, timeout=timeout)
        elapsed = round(time.time() - t0, 1)
        body = r.json()
        metrics = body.get("metrics", {})
        dify_used = metrics.get("dify_used", False)
        fallback = metrics.get("fallback", False)

        if dify_used and not fallback:
            _ok(f"dify_used=true，耗时 {elapsed}s，风险={body.get('risk_level')}")
            print(f"  回答预览: {body.get('answer', '')[:120]}...")
            return True

        if fallback:
            _fail(f"走了 LangGraph 降级（耗时 {elapsed}s）")
            print("  常见原因: Dify 工作流 HTTP 节点 URL 与当前隧道不一致")
        else:
            _fail(f"metrics={metrics}")
    except requests.exceptions.Timeout:
        _fail(f"请求超时（>{timeout}s），Dify 工作流可能卡在 HTTP 节点")
        print("  请确认 Dify 中 3 个 HTTP 节点指向当前 PUBLIC_TUNNEL_URL")
    except Exception as e:
        _fail(str(e))
    return False


def print_tunnel_hints() -> None:
    url = TUNNEL
    if url:
        print("\n--- Dify HTTP 节点 URL（复制到工作流）---")
        for path in (
            "symptom_analysis",
            "risk_assessment",
            "knowledge_retrieval",
            "compliance_guard",
            "lifestyle_recommendations",
        ):
            print(f"  {url}/tools/{path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="阶段 0 E2E 检查")
    parser.add_argument("--skip-dify", action="store_true", help="跳过慢速 Dify 全链路")
    args = parser.parse_args()

    print("=" * 60)
    print("doctor-Agent 阶段 0 E2E 检查")
    print("=" * 60)

    results = [
        check_backend(),
        check_tunnel(),
        check_dify_api(),
        check_chat_dify(skip=args.skip_dify),
    ]
    print_tunnel_hints()

    passed = sum(results)
    print(f"\n通过 {passed}/{len(results)} 项")
    print("=" * 60)
    return 0 if all(results[:3]) and (args.skip_dify or results[3]) else 1


if __name__ == "__main__":
    sys.exit(main())
