#!/usr/bin/env bash
# 启动 Cloudflare Quick Tunnel
# 用法: ./scripts/start_tunnel.sh [port]
set -euo pipefail

PORT="${1:-8012}"
BACKEND_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL_FILE="$BACKEND_ROOT/.tunnel_url"

echo "正在启动 cloudflared 隧道，映射本地端口 $PORT ..."
echo "请保持此进程运行。"
echo ""

if ! command -v cloudflared &>/dev/null; then
  echo "错误: 未找到 cloudflared" >&2
  exit 1
fi

cloudflared tunnel --url "http://127.0.0.1:$PORT" 2>&1 | tee "$BACKEND_ROOT/.tunnel_log" | while IFS= read -r line; do
  echo "$line"
  if [[ "$line" =~ (https://[a-z0-9-]+\.trycloudflare\.com) ]]; then
    echo "${BASH_REMATCH[1]}" > "$URL_FILE"
    echo ""
    echo "隧道 URL 已写入 $URL_FILE"
    echo "Dify HTTP 节点:"
    echo "  ${BASH_REMATCH[1]}/tools/symptom_analysis"
    echo "  ${BASH_REMATCH[1]}/tools/risk_assessment"
    echo "  ${BASH_REMATCH[1]}/tools/compliance_guard"
  fi
done
