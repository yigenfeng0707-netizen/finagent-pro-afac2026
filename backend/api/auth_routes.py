"""
用户认证API路由
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])


# ===== 请求模型 =====

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UpgradeRequest(BaseModel):
    plan: str = Field(..., description="计划类型: pro / enterprise")


class LLMConfigRequest(BaseModel):
    api_key: str = Field("", description="自定义API Key")
    base_url: str = Field("", description="自定义Base URL")
    model: str = Field("", description="模型名称")
    provider: str = Field("custom", description="提供商标识")


# ===== 路由 =====

@router.post("/register", summary="用户注册")
async def register(request: RegisterRequest):
    """注册新用户"""
    from services.user_service import user_service
    try:
        result = await user_service.register(request.username, request.email, request.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", summary="用户登录")
async def login(request: LoginRequest):
    """用户登录，返回JWT token"""
    from services.user_service import user_service
    try:
        result = await user_service.login(request.username, request.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", summary="获取当前用户信息")
async def get_me(request: Request):
    """获取当前登录用户信息"""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="未登录")
    from services.user_service import user_service
    user = await user_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/upgrade", summary="升级付费计划")
async def upgrade_plan(request: Request, body: UpgradeRequest):
    """升级用户付费计划"""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="未登录")
    if body.plan not in ("pro", "enterprise"):
        raise HTTPException(status_code=400, detail="无效的计划类型，可选: pro, enterprise")
    from services.user_service import user_service
    await user_service.update_plan(user_id, body.plan)
    user = await user_service.get_user(user_id)
    return {"message": "计划升级成功", "user": user}


@router.post("/llm-config", summary="保存自定义LLM配置")
async def save_llm_config(request: Request, body: LLMConfigRequest):
    """保存用户自定义LLM配置（API Key、Base URL、Model）"""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="未登录")
    from services.user_service import user_service
    config = {
        "api_key": body.api_key,
        "base_url": body.base_url,
        "model": body.model,
        "provider": body.provider,
    }
    await user_service.update_llm_config(user_id, config)
    return {"message": "LLM配置保存成功"}


@router.get("/usage", summary="获取使用情况")
async def get_usage(request: Request):
    """获取当前用户的使用次数和限制"""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="未登录")
    from services.user_service import user_service
    return await user_service.get_usage(user_id)
