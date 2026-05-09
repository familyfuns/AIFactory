"""Auth routes — register, login, logout, JWT"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from supabase import create_client
import os

router = APIRouter()
security = HTTPBearer()
pwd = CryptContext(schemes=["bcrypt"])

SECRET = os.getenv("SECRET_KEY", "change-me")
ALGO = "HS256"
EXPIRE_HOURS = 24 * 7  # 7 days

def supabase():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def make_token(user_id: str, email: str, plan: str = "free") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "plan": plan,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    return decode_token(creds.credentials)

# ── Models ──
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# ── Routes ──
@router.post("/register")
async def register(body: RegisterIn):
    sb = supabase()
    # Check existing
    existing = sb.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(400, "Email already registered")

    hashed = pwd.hash(body.password)
    result = sb.table("users").insert({
        "email": body.email,
        "name": body.name,
        "password_hash": hashed,
        "plan": "free",
        "credits": 3,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    user = result.data[0]
    token = make_token(user["id"], user["email"], user["plan"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "plan": user["plan"], "credits": user["credits"]}}

@router.post("/login")
async def login(body: LoginIn):
    sb = supabase()
    result = sb.table("users").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(401, "Invalid credentials")

    user = result.data[0]
    if not pwd.verify(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    token = make_token(user["id"], user["email"], user["plan"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "plan": user["plan"], "credits": user["credits"]}}

@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    sb = supabase()
    result = sb.table("users").select("id,email,name,plan,credits").eq("id", current_user["sub"]).execute()
    if not result.data:
        raise HTTPException(404, "User not found")
    return result.data[0]
