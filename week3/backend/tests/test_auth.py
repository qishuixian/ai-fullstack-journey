import pytest
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt

def test_password_hashing():
    password = "test123456"
    hashed = hash_password(password)
    assert hashed != password  # 哈希值不应等于原文
    assert verify_password(password, hashed)  # 验证应通过
    assert not verify_password("wrong", hashed)  # 错误密码应失败

def test_jwt_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload  # 应有过期时间