# 本地 Demo 录屏环境（Windows）

> 公网未部署时的离线备份方案 · Todo P2-4

## 一键启动

```powershell
cd D:\AFAC2026金融智能创新大赛\FinAgent-Pro
.\scripts\start-demo.ps1
```

浏览器打开：**http://localhost:3000**

## 手动启动

**终端 1 - 后端**
```powershell
cd backend
pip install -r requirements.txt
$env:DEMO_MODE="false"   # 本地可用 Mock 降级
python main.py
```

**终端 2 - 前端**
```powershell
cd frontend
npm install
npm run dev
```

## 录屏检查清单

- [ ] Dashboard 显示统计卡片
- [ ] Analyze → 600519 → 思维链展开
- [ ] Chat →「帮我做养老稳健配置」
- [ ] Cases → 试点案例 Before/After
- [ ] Audit → 审计日志

## 录屏完成后

参考 `docs/RecordingGuide.md` 导出 3 分钟 MP4。
