# 公网 Demo 部署指南

> Todo P2-4 · **决赛推荐阿里云，初筛可用 Render/Vercel**

## 部署方案选择

| 方案 | 文档 | 说明 |
|------|------|------|
| **阿里云 ECS** | [`AliyunDeployGuide.md`](AliyunDeployGuide.md) | 国内访问快、AKShare 稳定、合规叙事强 |
| Render + Vercel | 方案 B | 免费快速、适合初筛 |
| 本地录屏 | [`LocalDemoGuide.md`](LocalDemoGuide.md) | 视频录制备份 |

---

## 快速部署（推荐：原生 Nginx，替换默认欢迎页）

服务器已有 Nginx 时，用 **setup-native.sh**（不占用 Docker 80 端口冲突）：

```bash
# 1. 安全组放行 22 端口后 SSH 登录
ssh -i LogiBrain_SSH.pem root@47.103.35.132

# 2. 一键部署
curl -fsSL https://raw.githubusercontent.com/yigenfeng0707-netizen/finagent-pro-afac2026/master/deploy/aliyun/setup-native.sh | bash
# 或克隆后: bash deploy/aliyun/setup-native.sh
```

**Windows 一键：** `.\scripts\deploy-to-aliyun.ps1`

安全组配置见 [`deploy/aliyun/SECURITY_GROUP.md`](../deploy/aliyun/SECURITY_GROUP.md)

---

## 方案 A：Docker Compose

### 后端 Render

1. 推送代码到 GitHub
2. Render 读取 `render.yaml`（已设 `DEMO_MODE=true`）
3. Dashboard 配置 Secret：`DASHSCOPE_API_KEY`、`SECRET_KEY`、`JWT_SECRET`

### 前端 Vercel

```bash
cd frontend
npm run build
vercel --prod
```

`vercel.json` 中 API 地址可改为阿里云域名。

---

## 方案 C：本地录屏

```powershell
.\scripts\start-demo.ps1
```

浏览器：http://localhost:3000

---

## 部署后检查清单

- [ ] `/api/health` 返回 `demo_mode: true`
- [ ] `/cases` 试点案例页正常
- [ ] `/analyze` 分析 600519 成功
- [ ] `/chat`「养老稳健配置」有回复
- [ ] `/audit` 审计日志有记录

## Benchmark 重跑（提交前）

```bash
cd backend
python -c "import asyncio; from benchmark.run_benchmark import run_benchmark; asyncio.run(run_benchmark(max_stocks=30, quick=True))"
```

结果写入 `backend/data/benchmark_results.json`。
