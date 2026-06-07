# -*- coding: utf-8 -*-
"""
三链路性能对比基准测试

对比 /api/chat (Swarm)、/api/chat/langgraph、/api/chat/dify
在固定 10 个问诊 case 上的延迟与风险等级。

用法:
  cd backend
  python scripts/benchmark_compare.py
  python scripts/benchmark_compare.py --endpoints swarm,langgraph
  python scripts/benchmark_compare.py --output reports/benchmark.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")

PORT = int(os.getenv("BACKEND_PORT", "8012"))
BASE = f"http://127.0.0.1:{PORT}"

ENDPOINTS = {
    "swarm": "/api/chat",
    "langgraph": "/api/chat/langgraph",
    "dify": "/api/chat/dify",
}

# 10 个固定问诊 case
CASES: List[Dict[str, Any]] = [
    {"id": 1, "message": "你好，我发烧了", "patient_context": {"age": 30, "gender": "男"}},
    {"id": 2, "message": "胸痛伴有呼吸困难", "patient_context": {"age": 55, "gender": "男"}},
    {"id": 3, "message": "肚子疼腹泻两天了", "patient_context": {"age": 25, "gender": "女"}},
    {"id": 4, "message": "头痛持续三天", "patient_context": {"age": 40, "gender": "女"}},
    {"id": 5, "message": "血糖偏高需要注意什么", "patient_context": {"age": 50, "gender": "男", "chronic_diseases": "糖尿病"}},
    {"id": 6, "message": "腰痛一周，弯腰加重", "patient_context": {"age": 35, "gender": "男"}},
    {"id": 7, "message": "月经不准，最近两个月没来", "patient_context": {"age": 28, "gender": "女"}},
    {"id": 8, "message": "感冒了能吃感冒药吗", "patient_context": {"age": 22, "gender": "女"}},
    {"id": 9, "message": "高血压一直在吃药，最近头晕", "patient_context": {"age": 60, "gender": "男", "chronic_diseases": "高血压"}},
    {"id": 10, "message": "皮肤起红疹很痒", "patient_context": {"age": 8, "gender": "男"}},
]


def call_endpoint(path: str, case: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    payload = {
        "message": case["message"],
        "patient_context": case.get("patient_context", {}),
        "enable_deep_search": False,
    }
    t0 = time.time()
    try:
        r = requests.post(f"{BASE}{path}", json=payload, timeout=timeout)
        elapsed = round(time.time() - t0, 2)
        body = r.json()
        metrics = body.get("metrics", {})
        return {
            "status_code": r.status_code,
            "elapsed_sec": elapsed,
            "risk_level": body.get("risk_level", ""),
            "department": body.get("recommended_department", ""),
            "answer_len": len(body.get("answer", "")),
            "dify_used": metrics.get("dify_used"),
            "fallback": metrics.get("fallback"),
            "error": None,
        }
    except Exception as e:
        return {
            "status_code": 0,
            "elapsed_sec": round(time.time() - t0, 2),
            "risk_level": "",
            "department": "",
            "answer_len": 0,
            "dify_used": None,
            "fallback": None,
            "error": str(e)[:200],
        }


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    ok = [r for r in rows if r["status_code"] == 200 and not r["error"]]
    times = [r["elapsed_sec"] for r in ok]
    fallbacks = sum(1 for r in ok if r.get("fallback"))
    return {
        "total": len(rows),
        "success": len(ok),
        "fallback_count": fallbacks,
        "p50_sec": round(statistics.median(times), 2) if times else None,
        "p95_sec": round(sorted(times)[int(len(times) * 0.95)] if times else 0, 2),
        "avg_sec": round(statistics.mean(times), 2) if times else None,
    }


def run_benchmark(endpoints: List[str], dify_timeout: int) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "cases": len(CASES),
        "results": {},
    }

    for name in endpoints:
        path = ENDPOINTS[name]
        timeout = dify_timeout + 30 if name == "dify" else 60
        print(f"\n>>> 测试 {name} ({path})")
        rows = []
        for case in CASES:
            print(f"  case {case['id']:02d}: {case['message'][:20]}...", end=" ", flush=True)
            row = call_endpoint(path, case, timeout=timeout)
            row["case_id"] = case["id"]
            row["message"] = case["message"]
            rows.append(row)
            status = "OK" if row["status_code"] == 200 and not row["error"] else "ERR"
            extra = ""
            if row.get("fallback"):
                extra = " [fallback]"
            elif row.get("dify_used"):
                extra = " [dify]"
            print(f"{status} {row['elapsed_sec']}s {row['risk_level']}{extra}")

        report["results"][name] = {"rows": rows, "summary": summarize(rows)}

    return report


def print_summary(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("对比摘要")
    print("=" * 70)
    print(f"{'链路':<12} {'成功':<8} {'P50(s)':<10} {'P95(s)':<10} {'降级':<8}")
    print("-" * 70)
    for name, data in report["results"].items():
        s = data["summary"]
        print(
            f"{name:<12} {s['success']}/{s['total']:<5} "
            f"{s['p50_sec'] or '-':<10} {s['p95_sec'] or '-':<10} {s['fallback_count']:<8}"
        )
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(description="三链路基准对比")
    parser.add_argument(
        "--endpoints",
        default="swarm,langgraph,dify",
        help="逗号分隔: swarm,langgraph,dify",
    )
    parser.add_argument("--output", default="", help="JSON 报告输出路径")
    parser.add_argument("--dify-timeout", type=int, default=int(os.getenv("DIFY_TIMEOUT", "90")))
    args = parser.parse_args()

    endpoints = [e.strip() for e in args.endpoints.split(",") if e.strip()]
    for e in endpoints:
        if e not in ENDPOINTS:
            print(f"未知 endpoint: {e}")
            return 1

    # 健康检查
    try:
        requests.get(f"{BASE}/api/health", timeout=5).raise_for_status()
    except Exception as e:
        print(f"后端未运行 ({BASE}): {e}")
        return 1

    report = run_benchmark(endpoints, args.dify_timeout)
    print_summary(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n报告已保存: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
