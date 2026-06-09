from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, status


def _verify_optional_token(configured: str, provided: Optional[str], header_name: str) -> None:
    """Allow local demo by default, but enforce shared token when configured."""
    if not configured:
        return
    if not provided or not hmac.compare_digest(configured, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing or invalid {header_name}",
        )


def verify_admin_token(x_admin_token: Optional[str] = Header(default=None)) -> None:
    _verify_optional_token(os.getenv("ADMIN_API_TOKEN", ""), x_admin_token, "X-Admin-Token")


def verify_dify_tool_token(x_dify_tool_token: Optional[str] = Header(default=None)) -> None:
    _verify_optional_token(os.getenv("DIFY_TOOL_TOKEN", ""), x_dify_tool_token, "X-Dify-Tool-Token")
