from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError # type: ignore
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")