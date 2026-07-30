import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

# 数据库文件路径（会在 backend 目录下生成 chat.db）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chat.db")

# 创建异步引擎  echo=True 会打印所有 SQL 语句，便于调试
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建会话工厂 expire_on_commit=False 避免提交后对象过期，方便后续访问属性
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 基类
class Base(DeclarativeBase):
    pass

# 对话记录表
class ChatMessage(Base):
    __tablename__ = "chat_messages"  # 告诉数据库，这张表叫 chat_messages
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # 主键ID，自增
    role = Column(String(10))  # 角色：user 或 assistant
    content = Column(Text)     # 消息内容（长文本）
    session_id = Column(String(36), ForeignKey("sessions.id"))  # 外键：关联到 sessions 表
    user_id = Column(Integer, ForeignKey("users.id"))          # 外键：关联到 users 表
    created_at = Column(DateTime, default=datetime.now)        # 创建时间，默认当前时间
# 会话表
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    name = Column(String(100),default="新对话")
    user_id = Column(Integer, ForeignKey("users.id"))
    pinned = Column(Integer, default=0)  # 0=未置顶，1=已置顶
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(128))
    created_at = Column(DateTime, default=datetime.now)


# 初始化数据库（建表）
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)