import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from database import async_session, User, Base, engine
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def db():
    # 使用独立的内存数据库进行测试
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    # 测试后清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_register_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 注册
        resp = await ac.post("/register", data={"username": "testuser", "password": "test123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

        # 使用同一token登录
        resp = await ac.post("/token", data={"username": "testuser", "password": "test123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()