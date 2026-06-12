# FinAgent Pro - 金融自主智能体平台

> 基于大语言模型与多智能体协同技术，打造能够自主规划、决策并执行复杂金融任务的"数字员工"，推动金融服务从被动响应迈向主动智能。

## 核心创新

1. **ReAct推理引擎** - 每个智能体具备"思考→行动→观察"循环，不是简单工具调用
2. **持久记忆系统** - 工作记忆+情节记忆+语义记忆，让数字员工"记住"上下文
3. **主动智能** - 定时巡检+事件驱动+阈值预警，从被动回答到主动工作
4. **合规内嵌** - 监管规则引擎，每步操作可审计可追溯
5. **多智能体协商** - 6大专业智能体协同分析，加权协商生成最终建议
6. **思维链可视化** - 实时展示AI推理过程，让决策"看得见"

## 系统架构

```
用户交互层:  Vue3 + TailwindCSS (暗色主题)
    ↕
API网关层:   FastAPI + WebSocket + SSE
    ↕
智能体层:    6大专业智能体 + Master Orchestrator
    ├── 市场分析智能体 (技术指标+基本面+资金流向)
    ├── 新闻舆情智能体 (中文新闻+社交情绪+事件提取)
    ├── 风控合规智能体 (多维风控+合规规则引擎)
    ├── 投资策略智能体 (资产配置+组合构建+策略回测)
    ├── 报告生成智能体 (研报/晨报/风控周报/事件快报)
    └── 执行监控智能体 (定时巡检+实时监控+主动预警)
    ↕
推理框架层:  ReAct引擎 + Tool系统 + Memory系统
    ↕
基础服务层:  LLM服务(通义千问/DeepSeek/OpenAI) + AKShare + 数据库
```

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- 可选: Redis, Docker

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑.env填入API密钥
python main.py
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### Docker部署

```bash
docker-compose up -d
```

## API文档

启动后端后访问: http://localhost:8000/docs

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/analyze` | POST | 综合分析股票 |
| `/api/chat` | POST | 与数字员工对话 |
| `/api/market/overview` | GET | 市场概览 |
| `/api/stock/{symbol}` | GET | 股票数据 |
| `/api/alerts` | GET | 预警列表 |
| `/api/reports` | GET | 报告列表 |
| `/api/reports/generate` | POST | 生成报告 |
| `/api/agents/status` | GET | 智能体状态 |
| `/api/tasks` | GET/POST | 定时任务管理 |
| `/api/ws` | WebSocket | 实时推送 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI + LangChain |
| 智能体 | ReAct推理 + Tool调用 + 持久记忆 |
| LLM | 通义千问(Qwen) / DeepSeek / OpenAI |
| 数据源 | AKShare + Tushare + 东方财富 |
| 前端 | Vue3 + TailwindCSS + TradingView |
| 数据库 | SQLite / PostgreSQL |
| 部署 | Docker + Vercel |

## 测试

```bash
cd backend
pytest -v
```

## 项目结构

```
FinAgent-Pro/
├── backend/
│   ├── agents/           # 6大智能体 + Orchestrator
│   ├── api/              # FastAPI路由
│   ├── middleware/        # 速率限制 + 合规审计
│   ├── models/           # Pydantic数据模型
│   ├── services/         # LLM/数据/新闻/风控/调度服务
│   ├── tests/            # 单元测试+集成测试
│   ├── config.py         # 配置系统
│   └── main.py           # 应用入口
├── frontend/
│   ├── src/
│   │   ├── components/   # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia状态管理
│   │   └── api.js        # API封装
│   └── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## License

MIT License © 2026 FinAgent Pro Team
