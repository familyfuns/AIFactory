"""User profile routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from supabase import create_client
import os

router = APIRouter()
security = HTTPBearer()

def sb():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(creds.credentials, os.getenv("SECRET_KEY","change-me"), algorithms=["HS256"])
    except JWTError:
        raise HTTPException(401, "Invalid token")

class UpdateProfileIn(BaseModel):
    name: str = None

@router.get("/stats")
async def user_stats(user: dict = Depends(get_user)):
    uid = user["sub"]
    products = sb().table("products").select("type").eq("user_id", uid).execute()
    profile = sb().table("users").select("credits,plan,name,email").eq("id", uid).execute()
    type_counts = {}
    for p in (products.data or []):
        type_counts[p["type"]] = type_counts.get(p["type"], 0) + 1
    return {
        "profile": profile.data[0] if profile.data else {},
        "total_products": len(products.data or []),
        "by_type": type_counts,
    }

@router.patch("/profile")
async def update_profile(body: UpdateProfileIn, user: dict = Depends(get_user)):
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nothing to update")
    sb().table("users").update(updates).eq("id", user["sub"]).execute()
    return {"updated": True}
