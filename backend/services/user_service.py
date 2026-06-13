"""
用户服务 - 注册、登录、使用次数管理、计划升级、LLM配置、管理员功能
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import sqlalchemy as sa
from jose import jwt, JWTError

from models.user import users_table, user_actions_table, metadata as user_metadata
from config import DATABASE_URL, SECRET_KEY

logger = logging.getLogger(__name__)

JWT_SECRET = SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72
FREE_USAGE_LIMIT = 1

# 超级管理员内置账户
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "FinAgent@2026"
ADMIN_EMAIL = "admin@finagent.pro"


def _hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _create_token(user_id: int, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> Optional[Dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


class UserService:
    """用户服务"""

    def __init__(self):
        self._engine = None
        self._initialized = False
        self._admin_seeded = False

    async def _ensure_init(self):
        if not self._initialized:
            await self._init_db()
            self._initialized = True
            await self._seed_admin()

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

    async def _seed_admin(self):
        """内置超级管理员账户"""
        if self._admin_seeded:
            return
        self._admin_seeded = True
        try:
            existing = await self._fetchone(
                sa.select(users_table).where(users_table.c.username == ADMIN_USERNAME)
            )
            if existing is None:
                password_hash = _hash_password(ADMIN_PASSWORD)
                await self._execute(
                    sa.insert(users_table).values(
                        username=ADMIN_USERNAME,
                        email=ADMIN_EMAIL,
                        password_hash=password_hash,
                        role="superadmin",
                        plan="enterprise",
                        free_usage_count=999999,
                        total_analyses=0,
                        total_chats=0,
                        total_exports=0,
                        created_at=datetime.now(),
                    )
                )
                logger.info(f"超级管理员账户已创建: {ADMIN_USERNAME}")
        except Exception as e:
            logger.warning(f"创建管理员账户失败: {e}")

    async def _execute(self, stmt):
        await self._ensure_init()
        if self._engine is None:
            return None
        if isinstance(self._engine, sa.engine.Engine):
            with self._engine.connect() as conn:
                result = conn.execute(stmt)
                conn.commit()
                return result
        else:
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

    async def _fetchall(self, stmt):
        await self._ensure_init()
        if self._engine is None:
            return []
        if isinstance(self._engine, sa.engine.Engine):
            with self._engine.connect() as conn:
                rows = conn.execute(stmt).fetchall()
                return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in rows]
        else:
            async with self._engine.begin() as conn:
                result = await conn.execute(stmt)
                rows = result.fetchall()
                return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in rows]

    async def log_action(self, user_id: int, username: str, action: str, detail: str = "", client_ip: str = ""):
        """记录用户行为"""
        try:
            await self._execute(
                sa.insert(user_actions_table).values(
                    user_id=user_id, username=username, action=action,
                    detail=detail, client_ip=client_ip, created_at=datetime.now(),
                )
            )
        except Exception as e:
            logger.warning(f"行为记录失败: {e}")

    async def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户"""
        existing = await self._fetchone(
            sa.select(users_table).where(users_table.c.username == username)
        )
        if existing:
            raise ValueError("用户名已存在")

        existing = await self._fetchone(
            sa.select(users_table).where(users_table.c.email == email)
        )
        if existing:
            raise ValueError("邮箱已被注册")

        password_hash = _hash_password(password)
        result = await self._execute(
            sa.insert(users_table).values(
                username=username, email=email, password_hash=password_hash,
                role="user", plan="free", free_usage_count=0,
                total_analyses=0, total_chats=0, total_exports=0,
                created_at=datetime.now(),
            )
        )
        if result is None:
            user_id = len(self._memory_users) + 1
            self._memory_users.append({
                "id": user_id, "username": username, "email": email,
                "password_hash": password_hash, "role": "user", "plan": "free",
                "free_usage_count": 0, "total_analyses": 0, "total_chats": 0,
                "total_exports": 0, "created_at": datetime.now().isoformat(),
            })
        else:
            user_id = result.lastrowid if hasattr(result, 'lastrowid') else 1

        # 注册成功不返回token，需登录
        return {"message": "注册成功，请登录", "username": username}

    async def login(self, username: str, password: str, client_ip: str = "") -> Dict[str, Any]:
        """用户登录"""
        row = await self._fetchone(
            sa.select(users_table).where(users_table.c.username == username)
        )

        if row is None and self._engine is None:
            for u in self._memory_users:
                if u["username"] == username and _verify_password(password, u["password_hash"]):
                    token = _create_token(u["id"], u.get("role", "user"))
                    return {"token": token, "user": {k: v for k, v in u.items() if k != "password_hash"}}
            raise ValueError("用户名或密码错误")

        if row is None:
            raise ValueError("用户名或密码错误")

        row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
        if not _verify_password(password, row_dict["password_hash"]):
            raise ValueError("用户名或密码错误")

        user_id = row_dict["id"]
        role = row_dict.get("role", "user")
        token = _create_token(user_id, role)
        user = await self.get_user(user_id)

        # 更新登录信息
        await self._execute(
            sa.update(users_table).where(users_table.c.id == user_id).values(
                last_login_at=datetime.now(), last_login_ip=client_ip
            )
        )
        await self.log_action(user_id, username, "login", client_ip=client_ip)

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

    def is_admin(self, user: Dict) -> bool:
        """判断是否管理员"""
        return user.get("role") in ("admin", "superadmin")

    def is_unlimited(self, user: Dict) -> bool:
        """判断是否无限制使用"""
        return user.get("role") in ("admin", "superadmin") or user.get("plan") in ("pro", "enterprise")

    async def check_usage(self, user_id: int) -> bool:
        """检查免费用户是否还有使用次数"""
        user = await self.get_user(user_id)
        if not user:
            return False
        if self.is_unlimited(user):
            return True
        return user["free_usage_count"] < FREE_USAGE_LIMIT

    async def increment_usage(self, user_id: int, action_type: str = "analyze"):
        """增加使用次数和行为计数"""
        user = await self.get_user(user_id)
        if not user:
            return
        updates = {"free_usage_count": users_table.c.free_usage_count + 1}
        if action_type == "analyze":
            updates["total_analyses"] = users_table.c.total_analyses + 1
        elif action_type == "chat":
            updates["total_chats"] = users_table.c.total_chats + 1
        elif action_type == "export":
            updates["total_exports"] = users_table.c.total_exports + 1
        await self._execute(sa.update(users_table).where(users_table.c.id == user_id).values(**updates))
        await self.log_action(user_id, user.get("username", ""), action_type)

    async def update_plan(self, user_id: int, plan: str):
        if plan not in ("free", "pro", "enterprise"):
            raise ValueError("无效的计划类型")
        await self._execute(sa.update(users_table).where(users_table.c.id == user_id).values(plan=plan))
        user = await self.get_user(user_id)
        if user:
            await self.log_action(user_id, user.get("username", ""), "upgrade", detail=plan)

    async def update_llm_config(self, user_id: int, config: Dict[str, Any]):
        config_json = json.dumps(config, ensure_ascii=False)
        api_key = config.get("api_key", "")
        await self._execute(
            sa.update(users_table).where(users_table.c.id == user_id)
            .values(llm_config=config_json, api_key_custom=api_key)
        )

    async def get_usage(self, user_id: int) -> Dict[str, Any]:
        user = await self.get_user(user_id)
        if not user:
            return {"used": 0, "limit": FREE_USAGE_LIMIT, "plan": "free", "remaining": FREE_USAGE_LIMIT}
        if self.is_unlimited(user):
            return {"used": user.get("free_usage_count", 0), "limit": -1, "plan": user["plan"], "remaining": -1}
        used = user["free_usage_count"]
        limit = FREE_USAGE_LIMIT
        return {"used": used, "limit": limit, "plan": user["plan"], "remaining": max(0, limit - used)}

    # ===== 管理员功能 =====

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有用户列表（管理员）"""
        rows = await self._fetchall(
            sa.select(users_table).order_by(users_table.c.id.desc()).limit(limit).offset(offset)
        )
        return [{k: v for k, v in r.items() if k != "password_hash"} for r in rows]

    async def get_user_count(self) -> int:
        """获取用户总数"""
        try:
            rows = await self._fetchall(sa.select(sa.func.count()).select_from(users_table))
            return rows[0].get("count_1", 0) if rows else 0
        except Exception:
            return 0

    async def get_user_actions(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """获取用户行为日志"""
        if user_id:
            return await self._fetchall(
                sa.select(user_actions_table).where(user_actions_table.c.user_id == user_id)
                .order_by(user_actions_table.c.id.desc()).limit(limit)
            )
        return await self._fetchall(
            sa.select(user_actions_table).order_by(user_actions_table.c.id.desc()).limit(limit)
        )

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """管理后台统计数据"""
        total_users = await self.get_user_count()
        all_users = await self.get_all_users(limit=1000)

        plan_dist = {"free": 0, "pro": 0, "enterprise": 0}
        total_analyses = 0
        total_chats = 0
        total_exports = 0
        active_24h = 0
        now = datetime.now()

        for u in all_users:
            plan_dist[u.get("plan", "free")] = plan_dist.get(u.get("plan", "free"), 0) + 1
            total_analyses += u.get("total_analyses", 0)
            total_chats += u.get("total_chats", 0)
            total_exports += u.get("total_exports", 0)
            last_login = u.get("last_login_at")
            if last_login:
                try:
                    if isinstance(last_login, str):
                        last_login = datetime.fromisoformat(last_login)
                    if (now - last_login).total_seconds() < 86400:
                        active_24h += 1
                except Exception:
                    pass

        # 转化漏斗
        registered = total_users
        used_once = sum(1 for u in all_users if u.get("free_usage_count", 0) > 0)
        paid = sum(1 for u in all_users if u.get("plan") in ("pro", "enterprise"))

        return {
            "total_users": total_users,
            "plan_distribution": plan_dist,
            "total_analyses": total_analyses,
            "total_chats": total_chats,
            "total_exports": total_exports,
            "active_24h": active_24h,
            "conversion_funnel": {
                "registered": registered,
                "used_once": used_once,
                "paid": paid,
                "conversion_rate": round(paid / registered * 100, 1) if registered > 0 else 0,
            },
            "top_users": sorted(all_users, key=lambda u: u.get("total_analyses", 0), reverse=True)[:10],
        }

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户画像"""
        user = await self.get_user(user_id)
        if not user:
            return {}
        actions = await self.get_user_actions(user_id, limit=200)

        # 行为偏好
        action_counts = {}
        for a in actions:
            act = a.get("action", "")
            action_counts[act] = action_counts.get(act, 0) + 1

        # 活跃时段
        hour_dist = [0] * 24
        for a in actions:
            ts = a.get("created_at")
            if ts:
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts)
                    hour_dist[ts.hour] += 1
                except Exception:
                    pass

        # 活跃天数
        active_days = set()
        for a in actions:
            ts = a.get("created_at")
            if ts:
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts)
                    active_days.add(ts.strftime("%Y-%m-%d"))
                except Exception:
                    pass

        return {
            "user": user,
            "action_counts": action_counts,
            "hour_distribution": hour_dist,
            "active_days": len(active_days),
            "engagement_score": min(100, len(actions) * 2),
            "is_new_user": (datetime.now() - (user.get("created_at") or datetime.now())).total_seconds() < 86400 * 7 if user.get("created_at") else True,
        }

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """验证token并返回payload"""
        payload = _decode_token(token)
        if payload is None:
            return None
        return payload

    # 内存降级存储
    _memory_users = []


# 单例
user_service = UserService()
