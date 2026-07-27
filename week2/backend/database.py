from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

# 数据库文件路径（会在 backend 目录下生成 chat.db）
DATABASE_URL = "sqlite+aiosqlite:///./chat.db"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建会话工厂
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 基类
class Base(DeclarativeBase):
    pass

# 对话记录表
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(10))       # user 或 assistant
    content = Column(Text)
    session_id = Column(String(36)) # 会话ID，用于区分不同对话
    created_at = Column(DateTime, default=datetime.now)

# 初始化数据库（建表）
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)