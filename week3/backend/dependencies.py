from database import async_session

# 依赖注入：获取数据库会话
async def get_db():
    async with async_session() as session:
        yield session