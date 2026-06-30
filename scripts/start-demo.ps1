# FinAgent Pro 本地 Demo 启动脚本
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "FinAgent Pro Demo 启动中..." -ForegroundColor Cyan

# 后端
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root\backend'; `$env:DEMO_MODE='false'; python main.py"
)

Start-Sleep -Seconds 3

# 前端
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$Root\frontend'; npm run dev"
)

Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"

Write-Host "已打开 http://localhost:3000" -ForegroundColor Green
Write-Host "录屏请参考 docs/RecordingGuide.md"
