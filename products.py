"""Products + Marketplace routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
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

@router.get("/my")
async def my_products(user: dict = Depends(get_user)):
    result = sb().table("products").select("*").eq("user_id", user["sub"]).order("created_at", desc=True).execute()
    return result.data

@router.delete("/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_user)):
    from services.storage_service import delete_file
    result = sb().table("products").select("*").eq("id", product_id).eq("user_id", user["sub"]).execute()
    if not result.data:
        raise HTTPException(404, "Product not found")
    p = result.data[0]
    if p.get("file_path"):
        delete_file(p["file_path"])
    sb().table("products").delete().eq("id", product_id).execute()
    return {"deleted": True}
