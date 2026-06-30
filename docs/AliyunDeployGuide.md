# FinAgent Pro · 阿里云部署指南

> 推荐用于 AFAC 决赛 Demo 与国内评委访问（低延迟、数据合规）

## 一、架构

```
Internet → 阿里云 ECS (80/443)
              └── Nginx
                    ├── /        → frontend/dist (Vue3)
                    └── /api/*   → FastAPI (8000)
              └── Redis (缓存)
              └── SQLite (数据)
```

**优势 vs Render/Vercel：**
- 国内访问快，AKShare 数据源稳定
- 数据留境内，符合金融合规叙事
- 单台 ECS 成本可控（约 ¥50-100/月）

## 二、资源准备

| 资源 | 建议规格 |
|------|---------|
| ECS | 2核4G，Ubuntu 22.04，带宽 3Mbps+ |
| 安全组 | 入站 80、443、22 |
| 域名 | 可选，阿里云备案后绑定 |
| LLM Key | DashScope / GLM（国内 API） |

## 三、快速部署（Docker Compose）

### 1. 登录 ECS 并安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 重新登录后
docker compose version
```

### 2. 上传代码

```bash
git clone YOUR_REPO finagent-pro
cd finagent-pro
```

### 3. 配置环境变量

```bash
cp .env.production.example .env
vim .env   # 填入 DASHSCOPE_API_KEY、SECRET_KEY、JWT_SECRET
```

### 4. 一键部署

```bash
chmod +x deploy/aliyun/deploy.sh
./deploy/aliyun/deploy.sh
```

### 5. 验证

```bash
curl http://127.0.0.1/api/health
# 浏览器访问 http://YOUR_ECS_PUBLIC_IP/
```

## 四、HTTPS（可选）

**方案 A：阿里云 SLB + 免费证书**  
在 SLB 监听 443，后端指向 ECS:80。

**方案 B：Certbot**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d demo.yourdomain.com
```

## 五、安全组与防火墙

```
22   TCP  你的 IP（SSH）
80   TCP  0.0.0.0/0
443  TCP  0.0.0.0/0
```

## 六、运维命令

```bash
# 查看日志
docker compose -f docker-compose.prod.yml logs -f api

# 重启
docker compose -f docker-compose.prod.yml restart

# 更新代码
git pull && ./deploy/aliyun/deploy.sh

# Benchmark 重跑（网络稳定时）
docker compose -f docker-compose.prod.yml exec api \
  python -c "import asyncio; from benchmark.run_benchmark import run_benchmark; asyncio.run(run_benchmark(30, True))"
```

## 七、AFAC 提交填写

| 字段 | 值 |
|------|-----|
| Demo URL | `http://YOUR_IP/` 或 `https://demo.yourdomain.com` |
| 部署说明 | 阿里云 ECS + Docker + Nginx |
| 数据合规 | 国产 LLM + 境内服务器 |

## 八、与 Render/Vercel 的关系

| 阶段 | 方案 |
|------|------|
| 初筛提交（7/15前） | Render/Vercel 可先上线，或直接用阿里云 |
| 决赛路演 | **推荐阿里云**（国内评委访问稳定） |

`vercel.json` 中的 API 地址可在部署阿里云后改为你的域名。

## 九、故障排查

| 问题 | 处理 |
|------|------|
| AKShare 超时 | 阿里云国内网络通常正常；检查安全组出站 |
| 502 Bad Gateway | `docker compose logs api`，等待 healthcheck 通过 |
| 前端空白 | 确认 `frontend/dist` 已 build |
| Mock 数据 | 设置 `DEMO_MODE=true` 且 `USE_REAL_DATA=true` |
