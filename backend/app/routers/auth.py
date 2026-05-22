from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_user
from app.models.user import User
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "用户名已存在")
    user = User(username=req.username, hashed_password=hash_password(req.password))
    db.add(user)
    await db.commit()
    token = create_access_token(user.id)
    return {"user": {"id": user.id, "username": user.username}, "token": token}


@router.post("/login")
async def login(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "用户名或密码错误")
    token = create_access_token(user.id)
    return {"user": {"id": user.id, "username": user.username}, "token": token}


@router.get("/me")
async def me(user: User = Depends(require_user)):
    return {"id": user.id, "username": user.username}
