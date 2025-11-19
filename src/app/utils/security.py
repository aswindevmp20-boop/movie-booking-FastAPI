import os
from datetime import datetime, timedelta
from argon2 import PasswordHasher
from jose import jwt

ph = PasswordHasher()

ACCESS_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
REFRESH_SECRET = os.getenv("REFRESH_TOKEN_SECRET")

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except Exception:
        return False

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    return jwt.encode({"sub": str(user_id), "exp": expire}, ACCESS_SECRET, algorithm="HS256")

def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expire}, REFRESH_SECRET, algorithm="HS256")
