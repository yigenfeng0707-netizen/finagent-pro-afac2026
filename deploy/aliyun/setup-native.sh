#!/usr/bin/env bash
# FinAgent Pro · 阿里云 ECS 原生部署（系统 Nginx + Python venv）
# 在服务器上以 root 执行: bash setup-native.sh
set -euo pipefail

APP_DIR=/opt/finagent-pro
REPO="${REPO:-https://github.com/yigenfeng0707-netizen/finagent-pro-afac2026.git}"

echo "==> [1/8] 安装依赖..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl nginx python3 python3-venv python3-pip nodejs npm

echo "==> [2/8] 克隆/更新代码..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR" && git pull
else
  git clone "$REPO" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> [3/8] 环境变量..."
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.production.example" "$APP_DIR/.env"
  echo "!!! 请编辑 $APP_DIR/.env 填入 DASHSCOPE_API_KEY 后重新运行本脚本"
  exit 1
fi
# 同步 backend 读取根目录 .env
cp "$APP_DIR/.env" "$APP_DIR/backend/.env"

echo "==> [4/8] Python 虚拟环境..."
cd "$APP_DIR/backend"
python3 -m venv venv
./venv/bin/pip install -q -U pip
./venv/bin/pip install -q -r requirements.txt

echo "==> [5/8] 构建前端..."
cd "$APP_DIR/frontend"
npm ci --silent 2>/dev/null || npm install --silent
npm run build

echo "==> [6/8] 配置 Nginx..."
cp "$APP_DIR/deploy/aliyun/nginx-host.conf" /etc/nginx/sites-available/finagent
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/finagent /etc/nginx/sites-enabled/finagent
nginx -t && systemctl reload nginx

echo "==> [7/8] 配置 systemd 服务..."
cp "$APP_DIR/deploy/aliyun/finagent.service" /etc/systemd/system/finagent.service
systemctl daemon-reload
systemctl enable finagent
systemctl restart finagent

echo "==> [8/8] 健康检查..."
sleep 3
curl -sf http://127.0.0.1:8000/api/health | head -c 200 && echo ""
curl -sf http://127.0.0.1/api/health | head -c 200 && echo ""

echo ""
echo "✅ 部署完成!"
echo "   访问: http://47.103.35.132/ 或 http://yunliyuan.cn/"
echo "   日志: journalctl -u finagent -f"
