"""Marketplace public routes"""
from fastapi import APIRouter, Query
from supabase import create_client
import os

router = APIRouter()

def sb():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

@router.get("/")
async def list_marketplace(
    category: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50)
):
    query = sb().table("marketplace_listings").select("*").eq("active", True)
    if category:
        query = query.eq("category", category)
    result = query.order("created_at", desc=True).range((page-1)*limit, page*limit-1).execute()
    return {"items": result.data, "page": page}
