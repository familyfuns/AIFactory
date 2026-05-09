"""Generate Routes — kick off AI generation tasks"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import os

router = APIRouter()
security = HTTPBearer()

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(creds.credentials, os.getenv("SECRET_KEY","change-me"), algorithms=["HS256"])
    except JWTError:
        raise HTTPException(401, "Invalid token")

# ── Input Models ──
class EbookIn(BaseModel):
    topic: str
    chapters: int = 10
    audience: str = "general"

class AudiobookIn(BaseModel):
    topic: str
    chapters: int = 8
    voice: str = "narrator_female"

class VideoIn(BaseModel):
    topic: str
    length: str = "medium"
    style: str = "educational"
    platform: str = "youtube"
    voice: str = "narrator_female"

class ImagePackIn(BaseModel):
    theme: str
    count: int = 10
    style: str = "digital art"

class WebsiteIn(BaseModel):
    business_name: str
    niche: str
    style: str = "modern"

class ContentPackIn(BaseModel):
    topic: str
    pack_type: str = "social"  # social|email|blog|ads|podcast

class PromptPackIn(BaseModel):
    category: str
    count: int = 50

class CourseIn(BaseModel):
    topic: str
    level: str = "beginner"

class ColoringIn(BaseModel):
    theme: str
    pages: int = 15
    age_group: str = "kids"

# ── Endpoints ──
@router.post("/ebook")
async def gen_ebook(body: EbookIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_ebook_task
    task = generate_ebook_task.delay(user["sub"], body.topic, body.chapters, body.audience)
    return {"task_id": task.id, "status": "queued", "type": "ebook"}

@router.post("/audiobook")
async def gen_audiobook(body: AudiobookIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_audiobook_task
    task = generate_audiobook_task.delay(user["sub"], body.topic, body.chapters, body.voice)
    return {"task_id": task.id, "status": "queued", "type": "audiobook"}

@router.post("/video")
async def gen_video(body: VideoIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_video_task
    task = generate_video_task.delay(user["sub"], body.topic, body.length, body.style, body.platform, body.voice)
    return {"task_id": task.id, "status": "queued", "type": "video"}

@router.post("/images")
async def gen_images(body: ImagePackIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_image_pack_task
    task = generate_image_pack_task.delay(user["sub"], body.theme, body.count, body.style)
    return {"task_id": task.id, "status": "queued", "type": "image_pack"}

@router.post("/website")
async def gen_website(body: WebsiteIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_website_task
    task = generate_website_task.delay(user["sub"], body.business_name, body.niche, body.style)
    return {"task_id": task.id, "status": "queued", "type": "website"}

@router.post("/content")
async def gen_content(body: ContentPackIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_content_pack_task
    task = generate_content_pack_task.delay(user["sub"], body.topic, body.pack_type)
    return {"task_id": task.id, "status": "queued", "type": "content_pack"}

@router.post("/prompts")
async def gen_prompts(body: PromptPackIn, user: dict = Depends(get_user)):
    from workers.tasks import generate_prompt_pack_task
    task = generate_prompt_pack_task.delay(user["sub"], body.category, body.count)
    return {"task_id": task.id, "status": "queued", "type": "prompt_pack"}

@router.post("/coloring-book")
async def gen_coloring(body: ColoringIn, user: dict = Depends(get_user)):
    from services.ai_service import generate_coloring_book
    data = await generate_coloring_book(body.theme, body.pages, body.age_group)
    return {"status": "done", "data": data, "type": "coloring_book"}

@router.post("/course")
async def gen_course(body: CourseIn, user: dict = Depends(get_user)):
    from services.ai_service import generate_course
    data = await generate_course(body.topic, body.level)
    return {"status": "done", "data": data, "type": "course"}

# ── Poll task status ──
@router.get("/status/{task_id}")
async def task_status(task_id: str, user: dict = Depends(get_user)):
    from workers.tasks import celery_app
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending", "pct": 0}
    if result.state == "PROGRESS":
        meta = result.info or {}
        return {"task_id": task_id, "status": "progress", "step": meta.get("step","Working..."), "pct": meta.get("pct",0)}
    if result.state == "SUCCESS":
        return {"task_id": task_id, "status": "done", "pct": 100, "result": result.result}
    if result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.info)}
    return {"task_id": task_id, "status": result.state.lower()}
