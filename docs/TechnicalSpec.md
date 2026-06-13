# FinAgent Pro 技术规格说明书

> AFAC2026金融智能创新大赛 · 初创组参赛项目
> 版本: 2.0.0 | 最后更新: 2026-06-13

---

## 目录

1. [技术架构](#1-技术架构)
2. [核心技术](#2-核心技术)
3. [智能体设计](#3-智能体设计)
4. [多智能体协同](#4-多智能体协同)
5. [主动智能实现](#5-主动智能实现)
6. [合规引擎](#6-合规引擎)
7. [数据安全](#7-数据安全)
8. [技术选型对比](#8-技术选型对比)
9. [性能指标](#9-性能指标)
10. [可扩展性](#10-可扩展性)
11. [数据适配层](#11-数据适配层)
12. [用户认证与授权](#12-用户认证与授权)
13. [报告导出](#13-报告导出)

---

## 1. 技术架构

### 1.1 六层架构总览

FinAgent Pro 采用六层解耦架构，自上而下分别为交互层、API网关层、智能体层、推理框架层、基础服务层和基础设施层，各层职责清晰、独立可扩展。

```
┌─────────────────────────────────────────────────────────────────────┐
│                          交互层 (Interaction)                       │
│   Vue3 + Vite · Dashboard · Chat · Analyze · Alerts · Reports      │
│   WebSocket实时推送 · ThinkingChain推理可视化 · SignalBadge信号徽章  │
├─────────────────────────────────────────────────────────────────────┤
│                        API网关层 (Gateway)                          │
│   FastAPI + Uvicorn · CORS · RateLimiter · ComplianceAudit         │
│   RESTful API · WebSocket /ws · /api/analyze /chat /alerts /tasks  │
├─────────────────────────────────────────────────────────────────────┤
│                         智能体层 (Agents)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  市场    │ │  新闻    │ │  风控    │ │  策略    │ │  报告    │ │
│  │  分析    │ │  舆情    │ │  合规    │ │  投资    │ │  生成    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│              ┌──────────┐     ┌──────────────────┐                 │
│              │  执行    │     │  Orchestrator    │                 │
│              │  监控    │     │  总调度智能体     │                 │
│              └──────────┘     └──────────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│                       推理框架层 (Reasoning)                         │
│   ReAct引擎 (Thought→Action→Observation) · Tool注册/调度           │
│   Memory系统 (Working/Episodic/Semantic) · LLM多模型降级           │
│   DashScope(qwen-plus) → GLM-5.1 → DeepSeek-v4-pro → SenseNova   │
├─────────────────────────────────────────────────────────────────────┤
│                       基础服务层 (Services)                          │
│   MarketData · NewsService · RiskService · ComplianceService       │
│   SchedulerService · DatabaseService · WSManager · LLMService     │
├─────────────────────────────────────────────────────────────────────┤
│                       基础设施层 (Infrastructure)                    │
│   AKShare(A股)+yfinance(美股)+Finnhub(全球)+OpenBB(基本面) · SQLite+Redis · Render+Vercel│
│   APScheduler(调度) · WebSocket(推送) · Pydantic(校验)             │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 各层职责说明

| 层级 | 核心职责 | 关键技术 |
|------|---------|---------|
| 交互层 | 用户交互、数据可视化、实时推送 | Vue3、Vite、TailwindCSS、WebSocket |
| API网关层 | 请求路由、限流、合规审计、CORS | FastAPI、Uvicorn、Starlette中间件 |
| 智能体层 | 专业分析、任务执行、多智能体协同 | 6大专业智能体、Orchestrator |
| 推理框架层 | ReAct推理、工具调度、记忆管理、LLM调用 | BaseAgent、Tool Registry、AgentMemory |
| 基础服务层 | 数据获取、风险计算、合规检查、调度 | AKShare、ta-lib、APScheduler |
| 基础设施层 | 数据存储、缓存、容器化部署 | AKShare、yfinance、Finnhub、OpenBB、SQLite、Redis、Render、Vercel |

---

## 2. 核心技术

### 2.1 ReAct推理引擎

ReAct（Reasoning + Acting）是FinAgent Pro智能体的核心推理范式，通过Thought→Action→Observation的迭代循环实现自主决策。

```
┌─────────────────────────────────────────────────┐
│              ReAct 推理循环                       │
│                                                  │
│   ┌─────────┐    ┌─────────┐    ┌───────────┐  │
│   │ Thought │───▶│ Action  │───▶│Observation│  │
│   │  思考   │    │  行动   │    │   观察    │  │
│   └─────────┘    └─────────┘    └───────────┘  │
│        ▲                              │          │
│        └──────────────────────────────┘          │
│                                                  │
│   终止条件: action='finish' 或 达到max_steps    │
└─────────────────────────────────────────────────┘
```

**核心实现（`base_agent.py`）：**

```python
async def react_loop(self, task_description: str, initial_data: Dict) -> Dict:
    """ReAct推理循环 - 每步由LLM决定下一步行动"""
    steps: List[AgentStep] = []
    current_context = json.dumps(initial_data, ensure_ascii=False)[:2000]

    for step_num in range(self.max_steps):
        # Thought: LLM推理下一步
        llm_response = await llm_service.generate_structured(
            system_prompt=f"你是{self.name}，{self.description}",
            user_prompt=f"任务: {task_description}\n可用工具: {self.get_tool_descriptions()}\n已知信息: {current_context}",
            output_schema={
                "type": "object",
                "properties": {
                    "thought": {"type": "string"},
                    "action": {"type": "string"},
                    "action_input": {"type": "object"}
                }
            }
        )

        thought = llm_response.get("thought", "")
        action = llm_response.get("action", "finish")
        action_input = llm_response.get("action_input", {})

        if action == "finish":
            break  # 任务完成

        # Action: 调用工具
        observation = await self.execute_tool(action, **action_input)

        # Observation: 更新上下文
        current_context += f"\n[步骤{step_num+1}] 思考:{thought}\n行动:{action}\n观察:{observation}"
        if len(current_context) > 6000:
            current_context = current_context[-4000:]  # 滑动窗口
```

**关键设计决策：**
- 上下文滑动窗口：限制6000字符，超出时保留最近4000字符，防止Token溢出
- 最大步数限制：`max_steps`默认10步，防止无限循环
- 规则引擎兜底：LLM不可用时自动降级到规则引擎模式

### 2.2 Tool系统

工具系统采用注册-发现模式，每个智能体按需注册专业工具，LLM通过工具描述自主选择调用。

```python
# 工具注册
agent.register_tool(
    name="calc_technical_indicators",
    description="计算技术指标：RSI、MACD、KDJ、布林带、ATR等",
    func=calc_technical_indicators,
    parameters={"symbol": {"type": "string", "description": "股票代码"}}
)

# 工具描述自动生成（供LLM选择）
def get_tool_descriptions(self) -> str:
    descriptions = []
    for tool in self._tools.values():
        params_str = json.dumps(tool.parameters, ensure_ascii=False)
        descriptions.append(f"- {tool.name}: {tool.description} 参数: {params_str}")
    return "\n".join(descriptions)
```

**工具分类体系：**

| 类别 | 工具 | 数据源 |
|------|------|--------|
| 市场数据 | get_stock_quote, calc_technical_indicators, get_capital_flow, get_financial_data, get_sector_comparison | AKShare+yfinance+Finnhub |
| 新闻舆情 | fetch_financial_news, fetch_announcements, analyze_sentiment, fetch_social_sentiment | Finnhub+东方财富+AKShare |
| 风控合规 | check_compliance, calc_var, check_concentration | 规则引擎+历史数据 |

### 2.3 Memory系统

Memory系统模拟人类认知的三层记忆架构，为智能体提供上下文感知和经验积累能力。

```
┌──────────────────────────────────────────────────────┐
│                  AgentMemory                         │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ WorkingMemory (工作记忆)                      │   │
│  │ · 当前对话/任务的临时上下文                    │   │
│  │ · 容量: 50条，LRU淘汰                         │   │
│  │ · 用途: ReAct循环中的上下文传递               │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ EpisodicMemory (情节记忆)                     │   │
│  │ · 历史任务执行记录                            │   │
│  │ · 容量: 100条，按类型检索                      │   │
│  │ · 用途: 相似任务经验复用                       │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ SemanticMemory (语义记忆)                     │   │
│  │ · 金融知识库（技术指标/风险指标/合规规则）    │   │
│  │ · 行业分类映射                                │   │
│  │ · 用途: 领域知识检索                          │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**语义记忆内置知识示例：**

```python
self.knowledge = {
    "技术指标": {
        "RSI": "相对强弱指标，>70超买，<30超卖",
        "MACD": "指数平滑异同移动平均线，金叉看多，死叉看空",
        "布林带": "价格触及上轨超买，触及下轨超卖",
        "ATR": "真实波动幅度，衡量市场波动性"
    },
    "合规规则": {
        "单股集中度": "单一标的不超过组合10%",
        "行业集中度": "单一行业不超过组合30%",
        "创业板限制": "创业板标的合计不超过20%",
        "ST股限制": "禁止买入ST/*ST股"
    }
}
```

---

## 3. 智能体设计

### 3.1 智能体总览

| 智能体 | 类型标识 | 最大步数 | 核心工具 | 信号类型 |
|--------|---------|---------|---------|---------|
| 市场分析智能体 | market | 8 | 市场数据5个 | strong_buy/buy/hold/sell/strong_sell |
| 新闻舆情智能体 | news | 6 | 新闻舆情4个 | 基于情绪分数映射 |
| 风控合规智能体 | risk | 6 | 风控合规3个 | 基于风险等级映射 |
| 投资策略智能体 | strategy | 8 | 市场+风控8个 | 市场信号×风险调整 |
| 报告生成智能体 | report | 5 | LLM生成 | hold(报告不产生信号) |
| 执行监控智能体 | execution | 5 | 市场数据 | 基于预警触发 |

### 3.2 市场分析智能体

**职责：** A股技术分析+基本面分析+资金流向+行业对比，输出多维度市场信号。

**工具列表：**
- `get_stock_quote` — 获取A股实时行情（价格、涨跌幅、成交量）
- `calc_technical_indicators` — 计算RSI/MACD/KDJ/布林带/ATR/SMA
- `get_capital_flow` — 获取主力/散户资金流向
- `get_financial_data` — 获取PE/PB/ROE等估值指标
- `get_sector_comparison` — 获取同行业估值排名对比

**ReAct推理示例：**

```
用户输入: 分析600519

Step 1:
  Thought: 需要先获取贵州茅台的实时行情和基本数据
  Action: get_stock_quote
  Action Input: {"symbol": "600519"}
  Observation: {name:"贵州茅台", current_price:1856.00, change_percent:+1.23, pe_ratio:32.5}

Step 2:
  Thought: 行情已获取，接下来计算技术指标判断趋势
  Action: calc_technical_indicators
  Action Input: {"symbol": "600519"}
  Observation: {rsi_14:68.5, macd:2.34, macd_signal:1.89, sma_20:1830, atr_14:28.5}

Step 3:
  Thought: RSI接近超买区，MACD金叉，SMA20上方，需要查看资金流向确认
  Action: get_capital_flow
  Action Input: {"symbol": "600519"}
  Observation: {main_net_inflow: +2.3亿, retail_net_inflow: -0.8亿}

Step 4:
  Thought: 主力资金净流入，技术面偏多但RSI偏高，信息已足够
  Action: finish
  Action Input: {"answer": "买入信号，置信度0.72。RSI=68.5偏强，MACD金叉，主力净流入2.3亿"}
```

**信号合成算法：**

```python
def _determine_signal(self, signals: List[Dict]) -> str:
    bullish = sum(1 for s in signals if s["signal"] in ["bullish", "oversold"])
    bearish = sum(1 for s in signals if s["signal"] in ["bearish", "overbought"])
    ratio = bullish / len(signals)
    if ratio > 0.7: return "strong_buy"
    if ratio > 0.55: return "buy"
    if ratio < 0.3: return "strong_sell"
    if ratio < 0.45: return "sell"
    return "hold"
```

### 3.3 新闻舆情智能体

**职责：** 中文金融新闻抓取+情感分析+事件提取+社交媒体情绪监控。

**工具列表：**
- `fetch_financial_news` — 获取金融新闻（支持按股票代码筛选）
- `fetch_announcements` — 获取上市公司公告
- `analyze_sentiment` — 中文文本情感分析（正面/负面/中性）
- `fetch_social_sentiment` — 获取雪球/股吧社交情绪数据

**信号映射：**

```python
def _determine_signal(self, avg_sentiment: float, dist: Dict) -> str:
    if avg_sentiment > 0.4:  return "buy"
    if avg_sentiment > 0.15: return "hold"
    if avg_sentiment < -0.4: return "sell"
    if avg_sentiment < -0.15: return "hold"
    return "hold"
```

**置信度计算：** `confidence = min(0.5 + news_count × 0.05, 0.9)`，新闻越多置信度越高，上限0.9。

### 3.4 风控合规智能体

**职责：** 多维风险评估（波动率/市场/舆情/流动性）+合规规则引擎+预警生成。

**工具列表：**
- `check_compliance` — 合规检查（单股集中度/行业集中度/创业板/ST股）
- `calc_var` — 计算VaR风险价值（历史模拟法）
- `check_concentration` — 检查持仓集中度风险

**四维风险评分模型：**

```python
overall_score = (
    volatility_risk  * 0.35 +   # 波动率风险（权重最高）
    market_risk      * 0.25 +   # 市场风险（Beta系数）
    news_risk        * 0.25 +   # 舆情风险（情绪分数）
    liquidity_risk   * 0.15     # 流动性风险（成交量）
)
```

**风险等级映射：**

| 评分范围 | 风险等级 | 对应信号 |
|---------|---------|---------|
| ≥0.75 | critical | strong_sell |
| ≥0.60 | high | sell |
| ≥0.40 | medium | hold |
| <0.40 | low | hold |

### 3.5 投资策略智能体

**职责：** 综合市场信号和风险评估，输出仓位建议、目标价、止损价。

**工具列表：** 市场数据5个 + 风控合规3个（共8个工具）

**仓位计算模型：**

```python
def _calc_position(self, market_signal: str, risk_level: str) -> float:
    base = {"strong_buy": 0.8, "buy": 0.6, "hold": 0.4, "sell": 0.2, "strong_sell": 0.1}
    risk_adj = {"low": 1.0, "medium": 0.8, "high": 0.5, "critical": 0.2}
    return base[market_signal] * risk_adj[risk_level]
```

**目标价/止损价计算：**

```python
up_ratio   = {"strong_buy": 15%, "buy": 10%, "hold": 5%, "sell": 2%, "strong_sell": 1%}
down_ratio = {"low": 5%, "medium": 7%, "high": 10%, "critical": 15%}
target_price = current_price × (1 + up_ratio)
stop_loss    = current_price × (1 - down_ratio)
```

### 3.6 报告生成智能体

**职责：** 自动生成5类金融报告——晨报、个股研报、风控周报、组合月报、事件快报。

**报告模板体系：**

| 报告类型 | 模板标识 | 包含章节 |
|---------|---------|---------|
| 金融晨报 | morning_daily | 隔夜市场、今日关注、持仓变动、风险提示 |
| 个股研报 | stock_research | 公司概况、财务分析、估值分析、投资建议、风险提示 |
| 风控周报 | risk_weekly | 风险指标、预警事件、合规检查、下周关注 |
| 组合月报 | portfolio_monthly | 业绩回顾、持仓分析、调仓建议、下月展望 |
| 事件快报 | event_flash | 事件概述、影响分析、操作建议 |

### 3.7 执行监控智能体

**职责：** 定时巡检、实时监控、主动预警、自主任务执行，推动系统从被动响应迈向主动智能。

**任务类型：**
- `morning_scan` — 晨间巡检，扫描市场指数和持仓状态
- `risk_scan` — 风险扫描，检查持仓中跌幅超5%的标的
- `price_alert` — 价格预警，监控涨跌幅超过阈值的标的

---

## 4. 多智能体协同

### 4.1 Orchestrator调度策略

Orchestrator作为总调度智能体，负责意图理解、任务分解、智能体调度和结果协商。

```
┌──────────────────────────────────────────────────────────┐
│                    Orchestrator                           │
│                                                          │
│  1. 接收请求 → 意图分类(analyze_stock/risk_check/...)    │
│  2. 任务分解 → 确定需要调度的智能体                      │
│  3. 三阶段流水线调度                                     │
│  4. 加权协商 → 生成最终建议                              │
│  5. LLM增强推理 → 补充催化剂/风险/持有周期              │
│  6. 合规检查 → 确保建议合规                              │
│  7. 推送结果 + 保存记录                                  │
└──────────────────────────────────────────────────────────┘
```

### 4.2 三阶段流水线

```
Phase 1: 并行执行（市场+新闻）
    ┌──────────────┐  ┌──────────────┐
    │ 市场分析智能体│  │ 新闻舆情智能体│   ← asyncio.gather并行
    └──────┬───────┘  └──────┬───────┘
           │                 │
           ▼                 ▼
Phase 2: 串行执行（风控，依赖Phase1结果）
    ┌──────────────────────────────┐
    │      风控合规智能体           │   ← 接收市场+新闻结果
    └──────────────┬───────────────┘
                   │
                   ▼
Phase 3: 串行执行（策略，依赖所有结果）
    ┌──────────────────────────────┐
    │      投资策略智能体           │   ← 接收市场+新闻+风控结果
    └──────────────┬───────────────┘
                   │
                   ▼
            最终建议生成
```

**实现代码：**

```python
# Phase 1: 并行
tasks = [
    self.agents["market"].execute({"symbol": symbol, "stock_data": stock_data}),
    self.agents["news"].execute({"symbol": symbol, "company_name": stock_data.get("name", "")}),
]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Phase 2: 风控（依赖Phase 1）
risk_input = {"symbol": symbol, "stock_data": stock_data,
              "technical_data": agent_results["market"], "sentiment_data": agent_results["news"]}
risk_result = await self.agents["risk"].execute(risk_input)

# Phase 3: 策略（依赖所有结果）
strategy_input = {"symbol": symbol, "stock_data": stock_data,
                  "market_result": agent_results["market"], "risk_result": agent_results["risk"]}
strategy_result = await self.agents["strategy"].execute(strategy_input)
```

### 4.3 加权协商算法

多智能体结果通过加权置信度协商，生成最终投资信号。

```python
def _generate_recommendation(self, symbol, stock_data, agent_results):
    signals = []
    confidences = []

    for name, result in agent_results.items():
        signals.append(self._signal_to_numeric(result.signal))    # 信号数值化
        confidences.append(result.confidence)                      # 置信度作为权重

    # 加权平均: Σ(signal × confidence) / Σ(confidence)
    weighted_signal = sum(s * c for s, c in zip(signals, confidences)) / sum(confidences)
    avg_confidence = sum(confidences) / len(confidences)

    # 数值→信号映射
    if weighted_signal > 0.5:  return STRONG_BUY
    if weighted_signal > 0.2:  return BUY
    if weighted_signal < -0.5: return STRONG_SELL
    if weighted_signal < -0.2: return SELL
    return HOLD
```

**信号数值化映射：**

| 信号 | 数值 |
|------|------|
| strong_buy | +1.0 |
| buy | +0.5 |
| hold | 0 |
| sell | -0.5 |
| strong_sell | -1.0 |

### 4.4 LLM增强推理

在规则引擎协商之后，Orchestrator可选调用LLM进行增强推理，补充关键催化剂、风险和持有周期建议。

```python
async def _llm_negotiate(self, symbol, stock_data, agent_results, recommendation):
    """LLM多智能体协商增强"""
    context = f"股票: {symbol}\n"
    for name, result in agent_results.items():
        context += f"{name}智能体: 信号={result.signal}, 置信度={result.confidence}\n"

    result = await llm_service.generate_structured(
        system_prompt="你是资深金融分析师，综合多个AI智能体的分析结果，生成专业投资建议。",
        user_prompt=context,
        output_schema={
            "properties": {
                "reasoning": {"type": "string"},
                "key_catalysts": {"type": "array", "items": {"type": "string"}},
                "key_risks": {"type": "array", "items": {"type": "string"}},
                "time_horizon": {"type": "string"}
            }
        }
    )
    return result.get("reasoning", "")
```

---

## 5. 主动智能实现

FinAgent Pro 的核心差异化在于"主动智能"——系统不等待用户提问，而是主动巡检、预警和执行任务。

### 5.1 定时巡检

基于APScheduler实现Cron定时任务，在交易时间自动执行巡检。

```python
# 默认定时任务
"morning_report":  cron="30 8 * * 1-5"     # 工作日08:30 晨报
"evening_report":  cron="0 17 * * 1-5"     # 工作日17:00 收盘总结
"risk_scan":       cron="*/30 9-15 * * 1-5" # 交易时间每30分钟风险扫描
```

### 5.2 事件驱动

通过WebSocket实时推送机制，当智能体完成分析或触发预警时，主动推送至前端。

```python
# 智能体完成时推送进度
await ws_manager.send_agent_progress(symbol, agent_name, "completed", {})

# 预警触发时推送
await ws_manager.send_alert({
    "alert_id": "a1b2c3d4",
    "alert_type": "price",
    "severity": "high",
    "title": "600519大跌-5.23%"
})
```

### 5.3 阈值预警

执行监控智能体内置阈值预警机制：

```python
async def _price_alert(self, symbol: str, threshold: float = 0.05):
    stock = await market_data_service.get_stock_data(symbol)
    change = abs(stock.get("change_percent", 0))
    triggered = change >= threshold * 100  # 默认5%阈值

    if triggered:
        alert = {"alert_type": "price", "severity": "high",
                 "title": f"{symbol}价格波动{change:.2f}%"}
        await db_service.save_alert(alert)
        await ws_manager.send_alert(alert)  # 实时推送
```

### 5.4 计划执行

支持用户自定义定时任务，通过API创建和管理：

```
POST /api/tasks
{
    "task_type": "risk_scan",
    "cron_expression": "0 10 * * 1-5",
    "params": {"portfolio": {...}},
    "enabled": true
}
```

---

## 6. 合规引擎

### 6.1 监管规则

合规引擎内置4条核心监管规则，确保投资建议符合中国证券监管要求：

| 规则 | 限制 | 配置项 | 默认值 |
|------|------|--------|--------|
| 单股集中度 | 单一标的不超过组合10% | MAX_SINGLE_STOCK_RATIO | 0.10 |
| 行业集中度 | 单一行业不超过组合30% | MAX_SECTOR_RATIO | 0.30 |
| 创业板限制 | 创业板标的合计不超过20% | MAX_GEM_RATIO | 0.20 |
| ST股禁止 | 禁止买入ST/\*ST股 | 硬编码规则 | 0（禁止） |

**合规检查实现：**

```python
class ComplianceService:
    async def check(self, symbol: str, action: str = "buy", portfolio: Dict = None) -> Dict:
        result = {"passed": True, "violations": [], "warnings": []}

        # ST股检查 - 买入时触发
        if action == "buy":
            name = portfolio.get("name", "") if portfolio else ""
            if "ST" in symbol or "ST" in name:
                result["passed"] = False
                result["violations"].append("禁止买入ST/*ST股")

        # 创业板检查 - 300开头
        if symbol.startswith("300"):
            result["warnings"].append(f"创业板股票，仓位不超过{MAX_GEM_RATIO:.0%}")

        # 科创板检查 - 688开头
        if symbol.startswith("688"):
            result["warnings"].append("科创板涨跌幅限制20%")

        # 集中度检查
        if portfolio and action == "buy":
            total = portfolio.get("total_value", 0)
            for h in portfolio.get("holdings", []):
                ratio = h.get("value", 0) / total
                if ratio > MAX_SINGLE_STOCK_RATIO:
                    result["warnings"].append(f"{h['symbol']}集中度{ratio:.0%}超标")

        return result
```

### 6.2 审计日志

通过`ComplianceAuditMiddleware`中间件，自动记录所有涉及投资建议的API调用：

```python
class ComplianceAuditMiddleware(BaseHTTPMiddleware):
    AUDITED_PATHS = ["/api/analyze", "/api/chat", "/api/portfolio"]

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if any(request.url.path.startswith(p) for p in self.AUDITED_PATHS):
            audit_record = {
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host,
                "status_code": response.status_code,
                "processing_time": round(time.time() - start_time, 3)
            }
            await db_service.save_audit_log(audit_record)
        return response
```

---

## 7. 数据安全

### 7.1 敏感信息脱敏

- API Key通过环境变量注入，不硬编码在源码中（`.env` + `python-dotenv`）
- 日志输出中自动截断敏感数据（上下文限制6000字符，观察结果限制1000字符）
- LLM请求中股票代码和公司名称为公开信息，不涉及个人隐私

### 7.2 数据不出境

- LLM推理使用国产模型：DashScope/通义千问（阿里云百炼，主LLM）、GLM-5.1（智谱AI）、DeepSeek-v4-pro、SenseNova（商汤日日新）
- 所有模型API端点均为国内服务，数据不出境
- 市场数据通过AKShare/yfinance/Finnhub获取，AKShare为国内源，Finnhub/yfinance为海外公开市场数据，不涉及个人隐私

```python
# 国产LLM模型配置
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里云百炼 DashScope
GLM_BASE_URL = "https://api.edgefn.net/v1"          # 智谱AI
DEEPSEEK_BASE_URL = "https://api.deepseek.com"       # DeepSeek
SENSENOVA_BASE_URL = "https://token.sensenova.cn/v1" # 商汤日日新
```

### 7.3 操作可追溯

- 合规审计中间件记录所有投资建议API调用（时间、路径、IP、响应状态）
- 智能体每次执行记录到情节记忆（EpisodicMemory）
- 分析结果持久化到数据库（`db_service.save_analysis`）
- 预警事件持久化（`db_service.save_alert`）

---

## 8. 技术选型对比

### 8.1 后端框架：FastAPI vs Flask vs Django

| 维度 | FastAPI ✅ | Flask | Django |
|------|-----------|-------|--------|
| 异步支持 | 原生async/await | 需扩展 | 有限 |
| 性能 | 高（基于Starlette） | 中 | 中低 |
| 类型校验 | Pydantic自动校验 | 手动 | Form/Serializer |
| WebSocket | 原生支持 | 需扩展 | 需Channels |
| API文档 | 自动生成OpenAPI | 需Flask-RESTful | 需DRF |
| 适合场景 | 高并发API服务 | 小型项目 | 全栈CMS |

**选择理由：** FastAPI原生异步支持完美匹配智能体并发调度需求，Pydantic自动校验确保数据模型一致性，WebSocket原生支持实现实时推送。

### 8.2 LLM框架：LangChain vs 自研

| 维度 | LangChain ✅ | 自研 | LlamaIndex |
|------|-------------|------|------------|
| 工具调用 | Tool抽象成熟 | 需从零实现 | 偏RAG |
| Prompt管理 | 模板化 | 硬编码 | 有限 |
| 生态 | 丰富 | 无 | 中等 |
| 灵活性 | 中等 | 最高 | 低 |
| 维护成本 | 低 | 高 | 中 |

**选择理由：** LangChain提供成熟的Tool/Agent抽象，降低开发成本；同时自研ReAct引擎（`BaseAgent.react_loop`）保留灵活性，实现"框架+自研"混合模式。

### 8.3 数据源：AKShare vs Tushare vs Wind

| 维度 | AKShare ✅ | Tushare | Wind |
|------|-----------|---------|------|
| 费用 | 免费 | 积分制 | 昂贵 |
| 数据覆盖 | A股全面 | A股全面 | 全球 |
| 实时性 | 接近实时 | 延迟 | 实时 |
| 安装 | pip install | pip install | 专有客户端 |
| 适合场景 | 初创/竞赛 | 研究 | 机构 |

**选择理由：** AKShare免费开源、数据覆盖全面、安装简单，完美适配竞赛场景；同时保留Tushare作为备用数据源。

### 8.4 前端框架：Vue3 vs React

| 维度 | Vue3 ✅ | React |
|------|--------|-------|
| 学习曲线 | 低 | 中 |
| 模板语法 | 直观 | JSX |
| 状态管理 | Pinia | Redux/Zustand |
| 构建工具 | Vite | CRA/Vite |
| 生态 | Element Plus | Ant Design |

**选择理由：** Vue3组合式API+Vite快速构建+TailwindCSS原子化CSS，开发效率高，适合小团队快速迭代。

---

## 9. 性能指标

### 9.1 目标指标

| 指标 | 目标值 | 实现方式 |
|------|--------|---------|
| 单次分析响应时间 | < 5s | 并行调度+缓存+规则引擎兜底 |
| 并发处理能力 | 100+ QPS | FastAPI异步+Uvicorn多Worker |
| 系统可用性 | 99.9% | Docker自动重启+LLM多模型降级 |
| LLM降级切换 | < 2s | 四模型自动降级链 |
| WebSocket推送延迟 | < 500ms | 异步推送+连接池管理 |

### 9.2 性能优化策略

**1. 并行调度：** Phase 1中市场分析和新闻舆情通过`asyncio.gather`并行执行，响应时间从串行的T1+T2降低到max(T1, T2)。

**2. 数据缓存：** MarketDataService内置5分钟TTL缓存，避免重复请求AKShare。

```python
class MarketDataService:
    def __init__(self):
        self.cache = {}
        self.cache_ts = {}
        self.cache_ttl = 300  # 5分钟缓存

    def _get_cached(self, key):
        if key in self.cache and time.time() - self.cache_ts[key] < self.cache_ttl:
            return self.cache[key]
        return None
```

**3. 规则引擎兜底：** LLM不可用时自动降级到规则引擎，确保系统始终可用。

```python
if llm_service.is_available():
    llm_result = await self._llm_analyze(...)  # LLM增强
    if llm_result:
        result.update(llm_result)
# 否则使用规则引擎结果，不阻塞
```

**4. LLM四模型降级链：** DashScope(qwen-plus) → GLM-5.1 → DeepSeek-v4-pro → SenseNova，指数退避重试。

```python
async def _retry_request(self, func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception:
            delay = min(base_delay * (2 ** attempt), 10.0)
            await asyncio.sleep(delay)
    # 主模型失败后降级
    return await self._try_fallback(...)
```

**5. 上下文窗口控制：** ReAct循环中滑动窗口限制6000字符，防止Token溢出和成本失控。

---

## 10. 可扩展性

### 10.1 水平扩展方案

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  负载均衡    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │ FastAPI   │ │ FastAPI   │ │ FastAPI   │
        │ Worker 1  │ │ Worker 2  │ │ Worker N  │
        └─────┬────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │  共享缓存    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   SQLite    │
                    │  → PostgreSQL│  (生产升级)
                    └─────────────┘
```

**扩展路径：**
- **单机→多Worker：** Uvicorn `--workers N` 启动多进程
- **单机→集群：** Nginx反向代理+多实例+Redis共享缓存
- **SQLite→PostgreSQL：** 切换`DATABASE_URL`，SQLAlchemy ORM无感迁移
- **本地缓存→Redis：** MarketDataService缓存层切换到Redis

### 10.2 新智能体接入流程

接入新智能体仅需4步，遵循开闭原则：

**Step 1: 创建智能体类**

```python
# backend/agents/new_agent.py
from .base_agent import BaseAgent
from .tools import register_market_tools  # 按需注册工具
from .memory import get_agent_memory

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="新智能体",
            agent_type="new_type",
            description="智能体描述，供LLM理解职责",
            max_steps=6,
        )
        # 注册工具
        register_market_tools(self)
        self.memory = get_agent_memory("new_type")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # 实现分析逻辑
        # 必须返回: signal, confidence, analysis, key_findings, risk_factors
        return {
            "signal": "hold",
            "confidence": 0.5,
            "analysis": "...",
            "key_findings": [],
            "risk_factors": [],
        }
```

**Step 2: 注册到Orchestrator**

```python
# backend/agents/orchestrator.py
from agents.new_agent import NewAgent

self._agents = {
    "market": MarketAnalysisAgent(),
    "news": NewsSentimentAgent(),
    "risk": RiskComplianceAgent(),
    "strategy": StrategyAgent(),
    "report": ReportAgent(),
    "execution": ExecutionAgent(),
    "new_type": NewAgent(),  # ← 新增
}
```

**Step 3: 添加专属工具（可选）**

```python
# backend/agents/tools.py
async def new_tool(param: str) -> Dict:
    """新工具实现"""
    return {"result": "..."}

def register_new_tools(agent):
    agent.register_tool(name="new_tool", description="...", func=new_tool, parameters={...})
```

**Step 4: 添加API路由（可选）**

```python
# backend/api/routes.py
@router.post("/new-feature", summary="新功能")
async def new_feature(request: NewRequest):
    from agents.new_agent import NewAgent
    agent = NewAgent()
    return await agent.execute(request.dict())
```

### 10.3 扩展性设计原则

| 原则 | 实现 |
|------|------|
| 开闭原则 | 新智能体继承BaseAgent，无需修改基类 |
| 单一职责 | 每个智能体专注一个领域，工具按类别注册 |
| 依赖倒置 | 智能体依赖Tool抽象，不依赖具体数据源实现 |
| 接口隔离 | 智能体只注册自己需要的工具，不加载无关工具 |
| 最少知识 | 智能体之间通过Orchestrator通信，不直接依赖 |

---

## 11. 数据适配层

### 11.1 DataAdapter设计

DataAdapter作为统一数据访问层，屏蔽底层多数据源差异，为上层智能体提供一致的股票数据接口。

```
┌──────────────────────────────────────────────────────┐
│                  DataAdapter                         │
│                                                      │
│  统一对外接口: get_stock_quote(symbol)               │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 自动路由                                      │   │
│  │ · 6位数字代码 → A股(AKShare)                  │   │
│  │ · 其他代码    → 海外(yfinance + Finnhub)      │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 三层降级                                      │   │
│  │ 1. 真实数据 (AKShare/yfinance/Finnhub)        │   │
│  │ 2. 缓存数据 (内存缓存, 10s TTL)               │   │
│  │ 3. Mock数据 (兜底返回)                        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 缓存机制                                      │   │
│  │ · 内存缓存 + 自动过期清理                      │   │
│  │ · TTL: 10秒 (行情数据)                        │   │
│  │ · 过期自动清理，防止内存泄漏                    │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 11.2 统一对外接口

所有智能体通过 `get_stock_quote(symbol)` 获取股票行情，无需关心数据来源：

```python
class DataAdapter:
    async def get_stock_quote(self, symbol: str) -> Dict:
        """统一股票行情接口"""
        # 1. 检查缓存
        cached = self._get_cached(symbol)
        if cached:
            return cached

        # 2. 自动路由到对应数据源
        if self._is_a_stock(symbol):  # 6位数字 → A股
            data = await self._fetch_from_akshare(symbol)
        else:  # 其他 → 海外
            data = await self._fetch_from_yfinance_finnhub(symbol)

        # 3. 缓存结果
        if data:
            self._set_cache(symbol, data)
            return data

        # 4. 降级到Mock
        return self._get_mock_data(symbol)
```

### 11.3 自动路由规则

| 代码格式 | 判定 | 数据源 | 示例 |
|---------|------|--------|------|
| 6位数字 | A股 | AKShare | 600519, 000001, 300750 |
| 字母代码 | 海外 | yfinance + Finnhub | AAPL, TSLA, 7203.T |

### 11.4 三层降级策略

```
请求 → 真实数据获取
         │
         ├─ 成功 → 缓存(10s TTL) → 返回
         │
         └─ 失败 → 检查缓存
                    │
                    ├─ 缓存命中 → 返回(标记为缓存数据)
                    │
                    └─ 缓存过期 → 返回Mock数据(标记为模拟数据)
```

### 11.5 缓存机制

```python
class DataAdapter:
    def __init__(self):
        self._cache: Dict[str, Tuple[Dict, float]] = {}  # symbol → (data, timestamp)
        self._cache_ttl = 10  # 10秒TTL

    def _get_cached(self, symbol: str) -> Optional[Dict]:
        if symbol in self._cache:
            data, ts = self._cache[symbol]
            if time.time() - ts < self._cache_ttl:
                return data
            else:
                del self._cache[symbol]  # 自动过期清理
        return None

    def _set_cache(self, symbol: str, data: Dict):
        self._cache[symbol] = (data, time.time())
```

---

## 12. 用户认证与授权

### 12.1 JWT Token认证

系统采用JWT（JSON Web Token）进行用户认证，所有需认证的接口通过 `Authorization: Bearer <token>` 头部传递Token。

```python
# 认证中间件
class AuthMiddleware:
    async def verify_token(self, token: str) -> Dict:
        """验证JWT Token，返回用户信息"""
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload["sub"], "plan": payload["plan"]}
```

### 12.2 使用限制

| 计划 | 免费额度 | 功能范围 | LLM配置 |
|------|---------|---------|---------|
| 免费版 | 1次分析 | 基础分析+对话 | 默认模型 |
| 专业版 | 无限制 | 全部功能+导出 | 可自定义LLM |
| 企业版 | 无限制 | 全部功能+API+定制 | 可自定义LLM+私有部署 |

### 12.3 付费升级流程

```
用户点击升级 → 选择计划(专业版/企业版) → /api/auth/upgrade
     │
     ├─ 升级成功 → 更新JWT Token中的plan字段
     │
     └─ 升级失败 → 返回错误信息，保持原计划
```

### 12.4 自定义LLM配置

专业版及以上用户可配置自己的LLM API Key，实现模型自定义：

```python
# 用户自定义LLM配置
@router.post("/auth/llm-config")
async def update_llm_config(config: LLMConfigRequest, user=Depends(get_current_user)):
    if user.plan == "free":
        raise HTTPException(403, "免费版不支持自定义LLM配置")
    # 保存用户自定义LLM配置
    await db_service.save_user_llm_config(user.id, config)
```

---

## 13. 报告导出

### 13.1 Word文档生成

系统使用 `python-docx` 库生成专业格式的Word文档，支持分析结果、研究报告和对话记录三种导出类型。

```python
from docx import Document
from docx.shared import Inches, Pt
from fastapi.responses import StreamingResponse

class ExportService:
    async def export_analysis_word(self, analysis_data: Dict) -> StreamingResponse:
        """导出分析结果为Word文档"""
        doc = Document()
        doc.add_heading("金融分析报告", level=0)
        doc.add_heading(f"股票: {analysis_data['symbol']}", level=1)

        # 添加分析内容
        for section in analysis_data["sections"]:
            doc.add_heading(section["title"], level=2)
            doc.add_paragraph(section["content"])

        # 流式返回
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_data['symbol']}.docx"}
        )
```

### 13.2 导出类型

| 导出类型 | 接口 | 文档内容 |
|---------|------|---------|
| 分析结果 | /api/export/analysis | 股票分析信号、技术指标、风险评估、投资建议 |
| 研究报告 | /api/export/report | 完整研究报告（晨报/研报/风控周报等） |
| 对话记录 | /api/export/chat | 用户与数字员工的对话历史记录 |

### 13.3 StreamingResponse流式下载

所有导出接口采用 `StreamingResponse` 实现流式下载，避免大文档占用内存：

```python
@router.post("/export/analysis")
async def export_analysis(request: ExportRequest, user=Depends(get_current_user)):
    """流式导出分析Word文档"""
    analysis_data = await orchestrator.get_analysis(request.symbol)
    return await export_service.export_analysis_word(analysis_data)
```

---

## 附录A: API接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/analyze | 综合分析股票 |
| POST | /api/chat | 与数字员工对话 |
| GET | /api/market/overview | 市场概览 |
| GET | /api/stock/{symbol} | 获取股票数据 |
| GET | /api/stock/{symbol}/chart | K线图数据 |
| POST | /api/portfolio/analyze | 组合分析 |
| GET | /api/alerts | 预警列表 |
| GET | /api/reports | 报告列表 |
| POST | /api/reports/generate | 生成报告 |
| GET | /api/tasks | 定时任务列表 |
| POST | /api/tasks | 创建定时任务 |
| DELETE | /api/tasks/{task_id} | 删除定时任务 |
| GET | /api/agents/status | 智能体状态 |
| GET | /api/audit/log | 合规审计日志 |
| GET | /api/health | 健康检查 |
| WS | /api/ws | WebSocket实时推送 |
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |
| POST | /api/auth/upgrade | 升级订阅计划 |
| POST | /api/auth/refresh | 刷新JWT Token |
| GET | /api/auth/llm-config | 获取用户LLM配置 |
| POST | /api/auth/llm-config | 更新用户LLM配置 |
| POST | /api/export/analysis | 导出分析结果Word |
| POST | /api/export/report | 导出研究报告Word |
| POST | /api/export/chat | 导出对话记录Word |

## 附录B: 数据模型

```
SignalType: strong_buy | buy | hold | sell | strong_sell
RiskLevel:  low | medium | high | critical

AnalysisRequest  → AnalysisResponse
ChatRequest      → ChatResponse
PortfolioRequest → PortfolioAnalysis
ScheduledTaskRequest → ScheduledTaskInfo

AgentStep:    thought + action + action_input + observation
AgentResult:  signal + confidence + analysis + key_findings + risk_factors
InvestmentRecommendation: signal + confidence + target_price + stop_loss + reasoning
RiskAssessment: overall_risk + risk_score + risk_warnings + risk_mitigations
```
