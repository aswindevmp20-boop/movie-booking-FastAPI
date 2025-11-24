# from fastapi import Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer,HTTPBearer, HTTPAuthorizationCredentials
# from jose import jwt, JWTError
# import os

# security = HTTPBearer()

# ACCESS_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials

#     try:
#         payload = jwt.decode(token, ACCESS_SECRET, algorithms=["HS256"])
#         user_id = payload.get("sub")

#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         return {"id": int(user_id)}

#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")


# src/app/dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

security = HTTPBearer()
ACCESS_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials.replace("Bearer ", "").strip()

    try:
        payload = jwt.decode(token, ACCESS_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {"id": int(user_id), "role": role}

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

# ✅ Role validation dependency
def require_role(required_role: str):
    async def role_checker(user=Depends(get_current_user)):
        if user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Access forbidden: Admins only")
        return user
    return role_checker