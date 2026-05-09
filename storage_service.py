"""Storage Service — Supabase Storage"""
from supabase import create_client
import os, uuid, mimetypes

BUCKET = os.getenv("STORAGE_BUCKET", "productai-outputs")

def _sb():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def upload_file(data: bytes, filename: str, content_type: str = None, user_id: str = "public") -> dict:
    """Upload file to Supabase storage, return public URL"""
    if not content_type:
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

    path = f"{user_id}/{uuid.uuid4()}_{filename}"
    sb = _sb()
    sb.storage.from_(BUCKET).upload(path, data, {"content-type": content_type, "upsert": "false"})
    public_url = sb.storage.from_(BUCKET).get_public_url(path)
    return {"path": path, "url": public_url, "filename": filename, "size_bytes": len(data)}

def delete_file(path: str):
    _sb().storage.from_(BUCKET).remove([path])

def save_product_to_db(user_id: str, product_type: str, title: str,
                        file_url: str, file_path: str, metadata: dict = None) -> dict:
    """Save generated product record to database"""
    sb = _sb()
    result = sb.table("products").insert({
        "user_id": user_id,
        "type": product_type,
        "title": title,
        "file_url": file_url,
        "file_path": file_path,
        "metadata": metadata or {},
        "status": "ready",
        "watermarked": False,
    }).execute()
    return result.data[0] if result.data else {}

def deduct_credit(user_id: str) -> bool:
    """Deduct 1 credit from user. Returns False if insufficient credits."""
    sb = _sb()
    user = sb.table("users").select("credits,plan").eq("id", user_id).execute()
    if not user.data:
        return False
    u = user.data[0]
    if u["plan"] == "agency":
        return True  # unlimited
    if u["credits"] <= 0:
        return False
    sb.table("users").update({"credits": u["credits"] - 1}).eq("id", user_id).execute()
    return True
