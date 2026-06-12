import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys
GLM_API_KEY = os.getenv("GLM_API_KEY", "")  # GLM-5.1
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
SENSENOVA_API_KEY = os.getenv("SENSENOVA_API_KEY", "")  # 商汤日日新
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")  # 阿里云DashScope
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "glm")  # glm, deepseek, sensenova
LLM_MODEL = os.getenv("LLM_MODEL", "GLM-5.1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"

# GLM-5.1 specific (智谱AI，主力模型)
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.edgefn.net/v1")
GLM_MODEL = os.getenv("GLM_MODEL", "GLM-5.1")

# DeepSeek specific (深度推理，备选模型)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# SenseNova specific (商汤日日新，轻量快速模型)
SENSENOVA_API_KEY = os.getenv("SENSENOVA_API_KEY", "")
SENSENOVA_BASE_URL = os.getenv("SENSENOVA_BASE_URL", "https://token.sensenova.cn/v1")
SENSENOVA_MODEL = os.getenv("SENSENOVA_MODEL", "sensenova-6.7-flash-lite")

# DashScope (阿里云百炼，Primary Model)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")  # 使用标准模型名称

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/finagent.db")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Application
APP_NAME = os.getenv("APP_NAME", "FinAgent Pro")
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "") or os.urandom(32).hex()

# Data Sources
AKSHARE_ENABLED = True
TUSHARE_ENABLED = bool(TUSHARE_TOKEN)

# Agent Configuration
MAX_CONCURRENT_AGENTS = 6
AGENT_TIMEOUT = 60  # seconds
AGENT_MAX_STEPS = 10  # ReAct max steps
ANALYSIS_CACHE_TTL = 300  # 5 minutes

# Compliance Rules
COMPLIANCE_ENABLED = os.getenv("COMPLIANCE_ENABLED", "true").lower() == "true"
MAX_SINGLE_STOCK_RATIO = float(os.getenv("MAX_SINGLE_STOCK_RATIO", "0.10"))
MAX_SECTOR_RATIO = float(os.getenv("MAX_SECTOR_RATIO", "0.30"))
MAX_GEM_RATIO = float(os.getenv("MAX_GEM_RATIO", "0.20"))

# Scheduled Tasks
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
MORNING_REPORT_TIME = os.getenv("MORNING_REPORT_TIME", "08:30")
EVENING_REPORT_TIME = os.getenv("EVENING_REPORT_TIME", "17:00")

# API Access Control
API_ACCESS_KEY = os.getenv("API_ACCESS_KEY", "")
API_ACCESS_ENABLED = os.getenv("API_ACCESS_ENABLED", "false").lower() == "true"
