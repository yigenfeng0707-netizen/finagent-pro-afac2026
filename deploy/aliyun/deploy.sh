#!/usr/bin/env bash
# FinAgent Pro · 阿里云 ECS 部署脚本
# 适用：Ubuntu 22.04 / Alibaba Cloud Linux 3
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> FinAgent Pro 阿里云部署"
echo "    项目目录: $ROOT"

# 1. 检查 Docker
if ! command -v docker &>/dev/null; then
  echo "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
  exit 1
fi

# 2. 环境变量
if [ ! -f .env ]; then
  cp .env.production.example .env
  echo "已创建 .env，请编辑填入 API Key 后重新运行"
  exit 1
fi

# 3. 构建前端
echo "==> 构建前端..."
cd frontend
if [ ! -d node_modules ]; then
  npm ci || npm install
fi
# 生产环境 API 走同域 nginx 代理，无需 VITE_API_URL
npm run build
cd "$ROOT"

# 4. 启动服务
echo "==> 启动 Docker Compose..."
docker compose -f docker-compose.prod.yml up -d --build

# 5. 健康检查
echo "==> 等待服务就绪..."
sleep 8
curl -sf http://127.0.0.1/api/health && echo "" || echo "健康检查失败，请查看日志: docker compose -f docker-compose.prod.yml logs"

echo ""
echo "部署完成！"
echo "  本地访问: http://YOUR_ECS_IP/"
echo "  健康检查: http://YOUR_ECS_IP/api/health"
echo "  查看日志: docker compose -f docker-compose.prod.yml logs -f api"
echo ""
echo "HTTPS: 在阿里云申请 SSL 证书后，可配置 SLB 或 certbot。"
