from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO")
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", "1440"))
def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> int:
    token = creds.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def create_access_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
