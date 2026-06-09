# Demo Guide

This guide is for interviews and GitHub reviewers.

## Three-Minute Story

1. Open the Vue workbench at `http://127.0.0.1:5178`.
2. Go to **线上问诊** and select **LangGraph**.
3. Send a normal consultation, for example: `我有点咳嗽，低烧一天`.
4. Show the returned risk level, department, thinking steps, and agent trace.
5. Send a high-risk case, for example: `我胸痛，呼吸困难，出冷汗`.
6. Show the LangGraph interrupt prompt, then resume to produce the emergency response.
7. Optionally mention the Dify workflow canvas and fallback chain.

## Screenshots

Current screenshots are stored under `docs/assets/`:

| File | Description |
| --- | --- |
| [home-workbench.png](assets/home-workbench.png) | Full medical workbench home page |
| [langgraph-trace.png](assets/langgraph-trace.png) | LangGraph consultation with trace and metrics |
| [high-risk-interrupt.png](assets/high-risk-interrupt.png) | High-risk interrupt confirmation flow |
| [dify-workflow.png](assets/dify-workflow.png) | Dify Cloud workflow canvas overview |

Dify studio reference:

- https://cloud.dify.ai/app/d2051109-a79b-468a-8b98-73eeed4d745e/workflow

## Suggested Demo Inputs

Normal:

```text
我有点咳嗽，低烧一天，需要去哪个科？
```

High risk:

```text
我胸痛，呼吸困难，出冷汗。
```

Factual medical question:

```text
糖尿病确诊是看空腹血糖、餐后血糖还是糖化血红蛋白？
```

Medication boundary:

```text
我发烧了，能不能直接吃阿莫西林？
```

## Reviewer Checklist

- Backend health: `http://127.0.0.1:8012/api/health`
- Frontend URL: `http://127.0.0.1:5178`
- Backend tests: `cd backend && python -m pytest -q`
- Frontend build: `cd frontend && npm run build`
- Optional E2E: `cd backend && python scripts/check_e2e.py --skip-dify`
