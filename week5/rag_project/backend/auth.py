import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import User
from dependencies import get_db


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    # JWT 中只存最小身份信息，服务端再用 sub 回查用户。
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def register_user(username: str, password: str, db: AsyncSession) -> User:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(username: str, password: str, db: AsyncSession) -> User:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # 所有受保护接口都复用这个依赖，统一完成 token 解码和用户鉴权。
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user
