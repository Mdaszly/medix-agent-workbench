from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.metrics import router as metrics_router
from app.api.platform import router as platform_router
from app.services.dify_tools import router as dify_tools_router
from app.core.database import init_db

app = FastAPI(title="医路通 AI 互联网医院智能服务平台", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(metrics_router)
app.include_router(platform_router)
app.include_router(dify_tools_router)


if __name__ == "__main__":
    import uvicorn

    from app.core.config import SETTINGS

    uvicorn.run(app, host=SETTINGS["server"]["host"], port=int(SETTINGS["server"]["port"]))
