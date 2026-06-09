# Deployment

This project is designed for local demos and interviews. Production medical deployment is out of scope.

## Local Docker Compose

```bash
docker compose up --build
```

URLs:

- Frontend: `http://127.0.0.1:5178`
- Backend health: `http://127.0.0.1:8012/api/health`

By default Docker Compose disables real LLM calls and runs the local rule/RAG path.

## Optional Environment Variables

Backend:

```env
MEDIX_API_KEY=
MEDIX_ENABLE_LLM=false
DIFY_API_KEY=
DIFY_APP_ID=
DIFY_TIMEOUT=90
CORS_ORIGINS=http://127.0.0.1:5178,http://localhost:5178
ADMIN_API_TOKEN=
DIFY_TOOL_TOKEN=
```

Frontend:

```env
VITE_API_BASE=http://127.0.0.1:8012
VITE_ADMIN_API_TOKEN=
```

## Public Hosting Notes

Before exposing the app publicly:

- Set strict `CORS_ORIGINS`.
- Put the backend behind HTTPS and a reverse proxy.
- Set `ADMIN_API_TOKEN` for destructive demo-management routes.
- Set `DIFY_TOOL_TOKEN` when `/tools/*` is reachable from the internet.
- Add rate limiting at the proxy layer.
- Replace LangGraph `MemorySaver` with a persistent checkpoint store if interrupt state must survive restarts.
- Review all medical answer behavior with qualified professionals before any real-world use.
