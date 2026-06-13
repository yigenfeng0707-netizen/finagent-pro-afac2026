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
    sa.Column("plan", sa.String(20), default="free"),  # free / pro / enterprise
    sa.Column("free_usage_count", sa.Integer, default=0),
    sa.Column("api_key_custom", sa.String(256), nullable=True),
    sa.Column("llm_config", sa.Text, nullable=True),  # JSON string
    sa.Column("created_at", sa.DateTime, default=datetime.now),
)
