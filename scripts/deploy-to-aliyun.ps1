# FinAgent Pro 一键部署到阿里云（Windows 本地执行）
# 前置: 安全组已放行 22 端口（见 deploy/aliyun/SECURITY_GROUP.md）

$ErrorActionPreference = "Stop"
$Key = "D:\AFAC2026金融智能创新大赛\LogiBrain_SSH.pem"
$Host_ = "root@47.103.35.132"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> 测试 SSH 连接..." -ForegroundColor Cyan
ssh -i $Key -o ConnectTimeout=10 -o StrictHostKeyChecking=no $Host_ "echo SSH_OK"
if ($LASTEXITCODE -ne 0) {
    Write-Host "SSH 失败! 请先在阿里云安全组放行 22 端口。" -ForegroundColor Red
    Write-Host "参考: deploy/aliyun/SECURITY_GROUP.md"
    exit 1
}

# 准备生产 .env
$EnvSrc = Join-Path $Root "backend\.env"
$EnvDst = Join-Path $Root ".env.production.local"
if (-not (Test-Path $EnvDst)) {
    if (Test-Path $EnvSrc) {
        Copy-Item $EnvSrc $EnvDst
        Add-Content $EnvDst "`nDEBUG=false`nDEMO_MODE=true"
        Write-Host "已创建 .env.production.local" -ForegroundColor Yellow
    } else {
        Write-Host "缺少 backend\.env，请先配置 LLM Key" -ForegroundColor Red
        exit 1
    }
}

Write-Host "==> 推送代码到 GitHub（需先 commit）..." -ForegroundColor Cyan
Set-Location $Root
git status -sb

Write-Host "==> 上传 .env 到服务器..." -ForegroundColor Cyan
ssh -i $Key $Host_ "mkdir -p /opt/finagent-pro"
scp -i $Key $EnvDst "${Host_}:/opt/finagent-pro/.env"

Write-Host "==> 远程执行部署脚本..." -ForegroundColor Cyan
scp -i $Key "$Root\deploy\aliyun\setup-native.sh" "${Host_}:/tmp/setup-native.sh"
ssh -i $Key $Host_ "chmod +x /tmp/setup-native.sh && bash /tmp/setup-native.sh"

Write-Host "==> 验证..." -ForegroundColor Cyan
curl.exe -s "http://47.103.35.132/api/health"
Write-Host ""
Write-Host "Demo: http://47.103.35.132/  |  http://yunliyuan.cn/" -ForegroundColor Green
