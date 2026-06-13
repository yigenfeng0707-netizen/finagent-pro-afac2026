"""
用户模型
"""
import sqlalchemy as sa
from datetime import datetime

metadata = sa.MetaData()

users_table = sa.Table("users", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("username", sa.String(50), unique=True, nullable=False),
    sa.Column("email", sa.String(120), unique=True, nullable=False),
    sa.Column("password_hash", sa.String(128), nullable=False),
    sa.Column("role", sa.String(20), default="user"),  # user / admin / superadmin
    sa.Column("plan", sa.String(20), default="free"),  # free / pro / enterprise
    sa.Column("free_usage_count", sa.Integer, default=0),
    sa.Column("total_analyses", sa.Integer, default=0),
    sa.Column("total_chats", sa.Integer, default=0),
    sa.Column("total_exports", sa.Integer, default=0),
    sa.Column("api_key_custom", sa.String(256), nullable=True),
    sa.Column("llm_config", sa.Text, nullable=True),
    sa.Column("last_login_at", sa.DateTime, nullable=True),
    sa.Column("last_login_ip", sa.String(50), nullable=True),
    sa.Column("created_at", sa.DateTime, default=datetime.now),
)

# 用户行为日志表
user_actions_table = sa.Table("user_actions", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, nullable=False),
    sa.Column("username", sa.String(50), nullable=False),
    sa.Column("action", sa.String(50), nullable=False),  # login/analyze/chat/export/upgrade
    sa.Column("detail", sa.Text, nullable=True),
    sa.Column("client_ip", sa.String(50), nullable=True),
    sa.Column("created_at", sa.DateTime, default=datetime.now),
)
