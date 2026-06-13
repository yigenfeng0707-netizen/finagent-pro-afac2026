"""
用户认证API路由
"""
import logging
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])

# 注册限流：同一IP每分钟最多3次注册
_register_rate_limit: Dict[str, list] = {}


def _check_register_rate(client_ip: str):
    """检查注册频率限制"""
    now = time.time()
    if client_ip not in _register_rate_limit:
        _register_rate_limit[client_ip] = []
    # 清理60秒前的记录
    _register_rate_limit[client_ip] = [t for t in _register_rate_limit[client_ip] if now - t < 60]
    if len(_register_rate_limit[client_ip]) >= 3:
        raise HTTPException(status_code=429, detail="注册频率过高，请1分钟后再试")
    _register_rate_limit[client_ip].append(now)


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
async def register(request: Request, body: RegisterRequest):
    """注册新用户（限流：同IP每分钟3次）"""
    client_ip = request.client.host if request.client else "unknown"
    _check_register_rate(client_ip)
    from services.user_service import user_service
    try:
        result = await user_service.register(body.username, body.email, body.password)
        # 注册成功不返回token，需登录获取
        return {"message": "注册成功，请登录", "username": body.username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", summary="用户登录")
async def login(request: Request, body: LoginRequest):
    """用户登录，返回JWT token"""
    client_ip = request.client.host if request.client else ""
    from services.user_service import user_service
    try:
        result = await user_service.login(body.username, body.password, client_ip)
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


# ===== 管理员API =====

def _require_admin(request: Request):
    """检查管理员权限"""
    role = getattr(request.state, "user_role", None)
    if role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/admin/users", summary="获取所有用户列表")
async def admin_get_users(request: Request, limit: int = 100, offset: int = 0):
    """管理员：获取所有用户列表"""
    _require_admin(request)
    from services.user_service import user_service
    users = await user_service.get_all_users(limit, offset)
    return {"users": users, "total": len(users)}


@router.get("/admin/stats", summary="管理后台统计数据")
async def admin_get_stats(request: Request):
    """管理员：获取仪表盘统计数据"""
    _require_admin(request)
    from services.user_service import user_service
    return await user_service.get_dashboard_stats()


@router.get("/admin/user/{user_id}/profile", summary="获取用户画像")
async def admin_get_user_profile(request: Request, user_id: int):
    """管理员：获取用户画像和行为分析"""
    _require_admin(request)
    from services.user_service import user_service
    profile = await user_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile


@router.get("/admin/actions", summary="获取用户行为日志")
async def admin_get_actions(request: Request, user_id: int = None, limit: int = 100):
    """管理员：获取用户行为日志"""
    _require_admin(request)
    from services.user_service import user_service
    return {"actions": await user_service.get_user_actions(user_id, limit)}


@router.post("/admin/user/{user_id}/plan", summary="修改用户计划")
async def admin_update_user_plan(request: Request, user_id: int, body: UpgradeRequest):
    """管理员：修改用户付费计划"""
    _require_admin(request)
    from services.user_service import user_service
    await user_service.update_plan(user_id, body.plan)
    user = await user_service.get_user(user_id)
    return {"message": "用户计划修改成功", "user": user}
