# 启动 Cloudflare Quick Tunnel，将本地后端暴露给 Dify HTTP 工具节点
# 用法: .\scripts\start_tunnel.ps1 [-Port 8012]
param([int]$Port = 8012)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path $PSScriptRoot -Parent
$urlFile = Join-Path $backendRoot ".tunnel_url"

Write-Host "正在启动 cloudflared 隧道，映射本地端口 $Port ..."
Write-Host "请保持此窗口运行，关闭后 Dify HTTP 节点将无法访问本地服务。"
Write-Host ""

# 检查 cloudflared
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 cloudflared。请安装: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
}

# 启动并捕获 URL
$proc = Start-Process -FilePath "cloudflared" `
    -ArgumentList "tunnel", "--url", "http://127.0.0.1:$Port" `
    -RedirectStandardOutput $urlFile `
    -RedirectStandardError (Join-Path $backendRoot ".tunnel_log") `
    -PassThru -NoNewWindow

Write-Host "cloudflared PID: $($proc.Id)"
Write-Host "等待隧道 URL（约 5-15 秒）..."

$tunnelUrl = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $urlFile) {
        $content = Get-Content $urlFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "(https://[a-z0-9-]+\.trycloudflare\.com)") {
            $tunnelUrl = $Matches[1]
            break
        }
    }
}

if ($tunnelUrl) {
    $tunnelUrl | Set-Content $urlFile -Encoding UTF8
    Write-Host ""
    Write-Host "隧道已就绪: $tunnelUrl"
    Write-Host ""
    Write-Host "请在 Dify 工作流中更新以下 HTTP 节点 URL:"
    Write-Host "  $tunnelUrl/tools/symptom_analysis"
    Write-Host "  $tunnelUrl/tools/risk_assessment"
    Write-Host "  $tunnelUrl/tools/compliance_guard"
    Write-Host ""
    Write-Host "并将 PUBLIC_TUNNEL_URL=$tunnelUrl 写入 backend/.env"
} else {
    Write-Host "未能自动捕获 URL，请查看 $urlFile 或 .tunnel_log"
}

Write-Host "按 Ctrl+C 停止隧道..."
Wait-Process -Id $proc.Id
