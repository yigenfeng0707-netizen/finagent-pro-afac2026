"""
用户服务 - 注册、登录、使用次数管理、计划升级、LLM配置
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import sqlalchemy as sa
from jose import jwt, JWTError

from models.user import users_table, metadata as user_metadata
from config import DATABASE_URL, SECRET_KEY

logger = logging.getLogger(__name__)

JWT_SECRET = SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72
FREE_USAGE_LIMIT = 1


def _hash_password(password: str) -> str:
    """使用bcrypt哈希密码"""
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    import bcrypt
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _create_token(user_id: int) -> str:
    """创建JWT token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> Optional[Dict]:
    """解码JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


class UserService:
    """用户服务"""

    def __init__(self):
        self._engine = None
        self._initialized = False

    async def _ensure_init(self):
        if not self._initialized:
            await self._init_db()
            self._initialized = True

    async def _init_db(self):
        try:
            url = DATABASE_URL
            if url.startswith("sqlite:///") and "+aiosqlite" not in url:
                url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            try:
                engine = sa.create_async_engine(url)
                async with engine.begin() as conn:
                    await conn.run_sync(user_metadata.create_all)
                self._engine = engine
                logger.info("用户数据库初始化完成")
            except Exception:
                sync_url = DATABASE_URL.replace("+aiosqlite", "")
                engine = sa.create_engine(sync_url)
                user_metadata.create_all(engine)
                self._engine = engine
                logger.info("用户数据库初始化完成(同步模式)")
        except Exception as e:
            logger.warning(f"用户数据库初始化失败: {e}，将使用内存存储")
            self._engine = None

    async def _execute(self, stmt):
        await self._ensure_init()
        if self._engine is None:
            return None
        if isinstance(self._engine, sa.engine.Engine):
            # 同步引擎
            with self._engine.connect() as conn:
                result = conn.execute(stmt)
                conn.commit()
                return result
        else:
            # 异步引擎
            async with self._engine.begin() as conn:
                return await conn.execute(stmt)

    async def _fetchone(self, stmt):
        await self._ensure_init()
        if self._engine is None:
            return None
        if isinstance(self._engine, sa.engine.Engine):
            with self._engine.connect() as conn:
                return conn.execute(stmt).fetchone()
        else:
            async with self._engine.begin() as conn:
                result = await conn.execute(stmt)
                return result.fetchone()

    async def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户"""
        # 检查用户名是否已存在
        existing = await self._fetchone(
            sa.select(users_table).where(users_table.c.username == username)
        )
        if existing:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        existing = await self._fetchone(
            sa.select(users_table).where(users_table.c.email == email)
        )
        if existing:
            raise ValueError("邮箱已被注册")

        password_hash = _hash_password(password)
        result = await self._execute(
            sa.insert(users_table).values(
                username=username,
                email=email,
                password_hash=password_hash,
                plan="free",
                free_usage_count=0,
                created_at=datetime.now(),
            )
        )

        if result is None:
            # 内存降级模式
            user_id = len(self._memory_users) + 1
            self._memory_users.append({
                "id": user_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "plan": "free",
                "free_usage_count": 0,
                "api_key_custom": None,
                "llm_config": None,
                "created_at": datetime.now().isoformat(),
            })
        else:
            user_id = result.lastrowid if hasattr(result, 'lastrowid') else result.inserted_primary_key[0]

        token = _create_token(user_id)
        user = await self.get_user(user_id)
        return {"token": token, "user": user}

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        row = await self._fetchone(
            sa.select(users_table).where(users_table.c.username == username)
        )

        if row is None and self._engine is None:
            # 内存降级
            for u in self._memory_users:
                if u["username"] == username and _verify_password(password, u["password_hash"]):
                    token = _create_token(u["id"])
                    return {"token": token, "user": u}
            raise ValueError("用户名或密码错误")

        if row is None:
            raise ValueError("用户名或密码错误")

        row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
        if not _verify_password(password, row_dict["password_hash"]):
            raise ValueError("用户名或密码错误")

        user_id = row_dict["id"]
        token = _create_token(user_id)
        user = await self.get_user(user_id)
        return {"token": token, "user": user}

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        row = await self._fetchone(
            sa.select(users_table).where(users_table.c.id == user_id)
        )

        if row is None and self._engine is None:
            for u in self._memory_users:
                if u["id"] == user_id:
                    return {k: v for k, v in u.items() if k != "password_hash"}
            return None

        if row is None:
            return None

        row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
        return {k: v for k, v in row_dict.items() if k != "password_hash"}

    async def check_usage(self, user_id: int) -> bool:
        """检查免费用户是否还有使用次数"""
        user = await self.get_user(user_id)
        if not user:
            return False
        if user["plan"] != "free":
            return True
        return user["free_usage_count"] < FREE_USAGE_LIMIT

    async def increment_usage(self, user_id: int):
        """增加使用次数"""
        await self._execute(
            sa.update(users_table)
            .where(users_table.c.id == user_id)
            .values(free_usage_count=users_table.c.free_usage_count + 1)
        )
        if self._engine is None:
            for u in self._memory_users:
                if u["id"] == user_id:
                    u["free_usage_count"] += 1

    async def update_plan(self, user_id: int, plan: str):
        """升级付费计划"""
        if plan not in ("free", "pro", "enterprise"):
            raise ValueError("无效的计划类型")
        await self._execute(
            sa.update(users_table)
            .where(users_table.c.id == user_id)
            .values(plan=plan)
        )
        if self._engine is None:
            for u in self._memory_users:
                if u["id"] == user_id:
                    u["plan"] = plan

    async def update_llm_config(self, user_id: int, config: Dict[str, Any]):
        """保存自定义LLM配置"""
        config_json = json.dumps(config, ensure_ascii=False)
        api_key = config.get("api_key", "")
        await self._execute(
            sa.update(users_table)
            .where(users_table.c.id == user_id)
            .values(llm_config=config_json, api_key_custom=api_key)
        )
        if self._engine is None:
            for u in self._memory_users:
                if u["id"] == user_id:
                    u["llm_config"] = config_json
                    u["api_key_custom"] = api_key

    async def get_usage(self, user_id: int) -> Dict[str, Any]:
        """获取使用情况"""
        user = await self.get_user(user_id)
        if not user:
            return {"used": 0, "limit": FREE_USAGE_LIMIT, "plan": "free", "remaining": FREE_USAGE_LIMIT}
        used = user["free_usage_count"]
        limit = FREE_USAGE_LIMIT if user["plan"] == "free" else -1  # -1 表示无限
        remaining = max(0, limit - used) if limit > 0 else -1
        return {
            "used": used,
            "limit": limit,
            "plan": user["plan"],
            "remaining": remaining,
        }

    @staticmethod
    def verify_token(token: str) -> Optional[int]:
        """验证token并返回user_id"""
        payload = _decode_token(token)
        if payload is None:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None

    # 内存降级存储
    _memory_users = []


# 单例
user_service = UserService()
