# auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from jose import jwt, JWTError  # type: ignore
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext  # type: ignore
from ..database import SessionLocal
from ..models import User
import os
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    logger.critical("SECRET_KEY not set in .env — using insecure fallback. Set it immediately!")
    SECRET_KEY = "supersecretkey-CHANGE-THIS-IN-PRODUCTION"

ALGORITHM                  = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS  = 2

router      = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
# Database Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Request Models
# -----------------------------
class AuthRequest(BaseModel):
    username: str
    password: str

    #input validation — prevent empty or excessively long inputs
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username too long")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


# -----------------------------
# Signup
# -----------------------------
@router.post("/signup")
def signup(user: AuthRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Bcrypt has a 72-byte limit — truncate safely
    hashed_password = pwd_context.hash(user.password[:72])

    new_user = User(
        username=user.username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()

    logger.info(f"New user registered: {user.username}")
    return {"message": "User created successfully"}


# -----------------------------
# Login
# -----------------------------

@router.post("/login")
def login(user: AuthRequest, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(user.password[:72], db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    access_token = jwt.encode(
        {"sub": db_user.username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "expires_in":   ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "user_id":      db_user.id,  
    }