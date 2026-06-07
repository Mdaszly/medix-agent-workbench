from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os

import yaml


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


def load_config() -> Dict[str, Any]:
    config_path = BACKEND_ROOT / "config" / "config.yaml"
    if not config_path.exists():
        config_path = BACKEND_ROOT / "config.example.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    llm = data.setdefault("llm", {})
    llm["api_key"] = os.getenv("MEDIX_API_KEY", llm.get("api_key", ""))
    llm["base_url"] = os.getenv("MEDIX_BASE_URL", llm.get("base_url", ""))
    llm["model_name"] = os.getenv("MEDIX_MODEL_NAME", llm.get("model_name", ""))
    if os.getenv("MEDIX_ENABLE_LLM"):
        data.setdefault("features", {})["enable_llm"] = os.getenv("MEDIX_ENABLE_LLM", "").lower() in {"1", "true", "yes", "on"}
    data["rag"]["knowledge_dir"] = str(resolve_project_path(data["rag"]["knowledge_dir"]))
    data["database"]["sqlite_path"] = str(resolve_project_path(data["database"]["sqlite_path"]))
    return data


SETTINGS = load_config()
