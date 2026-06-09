# Frontend

Vue3 + Vite + Element Plus medical workbench for the doctor-Agent backend.

## Setup

```bash
npm install
npm run dev
```

Default URL:

```text
http://127.0.0.1:5178
```

## Environment

Create `frontend/.env.local` when the backend is not running on the default port:

```env
VITE_API_BASE=http://127.0.0.1:8012
VITE_ADMIN_API_TOKEN=
```

`VITE_ADMIN_API_TOKEN` is optional and is only needed when the backend sets `ADMIN_API_TOKEN` for destructive demo-management endpoints.

## Scripts

```bash
npm run dev
npm run build
npm run preview
```

The UI supports three orchestrators:

- Swarm: legacy local multi-agent flow.
- LangGraph: local graph workflow with trace and high-risk interrupt/resume.
- Dify: optional cloud workflow, with backend fallback to LangGraph.

For public demos, start the backend first and keep Dify optional unless the Dify API key and HTTP tool tunnel are configured.
