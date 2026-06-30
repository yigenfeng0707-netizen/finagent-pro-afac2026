# 阿里云安全组配置

> SSH 连接超时 = 安全组未放行 22 端口

## 必须放行的端口

| 端口 | 协议 | 授权对象 | 用途 |
|------|------|---------|------|
| **22** | TCP | 你的办公 IP/32 | SSH 部署 |
| **80** | TCP | 0.0.0.0/0 | HTTP Demo |
| **443** | TCP | 0.0.0.0/0 | HTTPS（可选） |

## 操作路径

阿里云控制台 → ECS → 实例 → **安全组** → 配置规则 → **入方向** → 手动添加

## 验证

```bash
# 本地 Windows PowerShell
ssh -i "LogiBrain_SSH.pem" root@47.103.35.132 "echo ok"
```

成功后执行：

```bash
# 上传 .env（在本地项目目录）
scp -i "LogiBrain_SSH.pem" FinAgent-Pro/.env.production.local root@47.103.35.132:/opt/finagent-pro/.env

# 或登录后手动创建 /opt/finagent-pro/.env
```

## 域名解析

阿里云 DNS → `yunliyuan.cn` → A 记录 → `47.103.35.132`
