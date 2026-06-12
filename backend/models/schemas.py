from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ===== 请求模型 =====

class AnalysisRequest(BaseModel):
    """股票分析请求"""
    symbol: str = Field(..., description="股票代码，如 600519")
    analysis_type: str = Field("comprehensive", description="分析类型: comprehensive/quick/technical/fundamental")
    include_news: bool = True
    include_risk: bool = True
    include_strategy: bool = False


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class PortfolioRequest(BaseModel):
    """组合分析请求"""
    holdings: List[Dict[str, Any]] = Field(..., description="持仓列表")
    risk_tolerance: str = Field("moderate", description="风险偏好: conservative/moderate/aggressive")


class ScheduledTaskRequest(BaseModel):
    """定时任务请求"""
    task_type: str = Field(..., description="任务类型: morning_report/evening_report/risk_scan")
    cron_expression: str = Field(..., description="Cron表达式")
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True


# ===== 响应模型 =====

class AgentStep(BaseModel):
    """智能体推理步骤"""
    thought: str
    action: str
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResult(BaseModel):
    """智能体分析结果"""
    agent_name: str
    agent_type: str
    status: str = "success"
    signal: SignalType = SignalType.HOLD
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    analysis: str = ""
    key_findings: List[str] = []
    risk_factors: List[str] = []
    reasoning_steps: List[AgentStep] = []
    execution_time: float = 0.0
    llm_enhanced: bool = False
    metadata: Dict[str, Any] = {}


class RiskAssessment(BaseModel):
    """风险评估"""
    overall_risk: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    volatility_risk: float = 0.0
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0
    compliance_risk: float = 0.0
    risk_warnings: List[str] = []
    risk_mitigations: List[str] = []


class InvestmentRecommendation(BaseModel):
    """投资建议"""
    symbol: str
    company_name: str = ""
    signal: SignalType
    confidence: float = Field(ge=0.0, le=1.0)
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str = ""
    key_points: List[str] = []
    risk_assessment: Optional[RiskAssessment] = None
    compliance_check: Optional[Dict[str, Any]] = None
    agent_analyses: List[AgentResult] = []


class AnalysisResponse(BaseModel):
    """分析响应"""
    request_id: str
    symbol: str
    company_name: str = ""
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    recommendation: Optional[InvestmentRecommendation] = None
    agent_results: Dict[str, AgentResult] = {}
    processing_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    agent_steps: List[AgentStep] = []
    related_stocks: List[str] = []
    suggestions: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class AlertInfo(BaseModel):
    """预警信息"""
    alert_id: str
    alert_type: str  # price/risk/news/compliance
    severity: str = "medium"  # 改为str，避免枚举验证问题
    title: str
    message: str = ""  # 添加默认值
    symbol: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    action_suggested: Optional[str] = None


class ReportInfo(BaseModel):
    """报告信息"""
    report_id: str
    report_type: str  # morning_daily/stock_research/risk_weekly/portfolio_monthly/event_flash
    title: str
    content: str
    summary: str = ""
    symbols: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.now)


class ScheduledTaskInfo(BaseModel):
    """定时任务信息"""
    task_id: str
    task_type: str
    cron_expression: str
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
