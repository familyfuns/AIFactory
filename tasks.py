"""
Celery Workers — Async AI Generation Tasks
Run with: celery -A workers.tasks worker --loglevel=info
"""
from celery import Celery
import asyncio, os
from dotenv import load_dotenv
load_dotenv()

celery_app = Celery(
    "productai",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ── EBOOK ──
@celery_app.task(bind=True, name="generate_ebook_task", max_retries=3)
def generate_ebook_task(self, user_id: str, topic: str, chapters: int, audience: str):
    from services.ai_service import generate_ebook
    from services.pdf_service import build_ebook_pdf
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    try:
        self.update_state(state="PROGRESS", meta={"step": "Generating content...", "pct": 20})
        data = run_async(generate_ebook(topic, chapters, audience))
        self.update_state(state="PROGRESS", meta={"step": "Building PDF...", "pct": 60})
        pdf_bytes = build_ebook_pdf(data)
        self.update_state(state="PROGRESS", meta={"step": "Uploading...", "pct": 85})
        stored = upload_file(pdf_bytes, f"{data['title'].replace(' ','_')}.pdf", "application/pdf", user_id)
        record = save_product_to_db(user_id, "ebook", data["title"], stored["url"], stored["path"], {"chapters": chapters, "topic": topic, "audience": audience})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "url": stored["url"], "title": data["title"]}
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

# ── AUDIOBOOK ──
@celery_app.task(bind=True, name="generate_audiobook_task", max_retries=3)
def generate_audiobook_task(self, user_id: str, topic: str, chapters: int, voice: str):
    from services.ai_service import generate_audiobook, generate_voiceover_chapters
    from services.pdf_service import build_audiobook_pdf
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    try:
        self.update_state(state="PROGRESS", meta={"step": "Writing audiobook...", "pct": 15})
        data = run_async(generate_audiobook(topic, chapters))
        self.update_state(state="PROGRESS", meta={"step": "Building PDF...", "pct": 40})
        pdf_bytes = build_audiobook_pdf(data)
        stored_pdf = upload_file(pdf_bytes, f"{data['title'].replace(' ','_')}_audiobook.pdf", "application/pdf", user_id)
        self.update_state(state="PROGRESS", meta={"step": "Generating voiceover...", "pct": 60})
        chapters_with_audio = run_async(generate_voiceover_chapters(data["chapters"][:3], voice))
        self.update_state(state="PROGRESS", meta={"step": "Uploading audio...", "pct": 85})
        audio_urls = []
        for i, ch in enumerate(chapters_with_audio):
            audio_bytes = bytes.__new__(bytes, bytes.fromhex("")) # placeholder
            if ch.get("audio_b64"):
                import base64
                audio_bytes = base64.b64decode(ch["audio_b64"])
                a = upload_file(audio_bytes, f"ch{i+1}.mp3", "audio/mpeg", user_id)
                audio_urls.append(a["url"])
        record = save_product_to_db(user_id, "audiobook", data["title"], stored_pdf["url"], stored_pdf["path"],
            {"topic": topic, "chapters": chapters, "audio_urls": audio_urls})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "pdf_url": stored_pdf["url"], "audio_urls": audio_urls}
    except Exception as e:
        raise self.retry(exc=e, countdown=15)

# ── VIDEO SCRIPT ──
@celery_app.task(bind=True, name="generate_video_task", max_retries=3)
def generate_video_task(self, user_id: str, topic: str, length: str, style: str, platform: str, voice: str):
    from services.ai_service import generate_video_script, text_to_speech
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    try:
        self.update_state(state="PROGRESS", meta={"step": "Writing script...", "pct": 20})
        data = run_async(generate_video_script(topic, length, style, platform))
        self.update_state(state="PROGRESS", meta={"step": "Generating voiceover...", "pct": 50})
        full_script = " ".join([s["text"] for s in data.get("script",[])])
        audio_bytes = run_async(text_to_speech(full_script[:5000], voice))
        self.update_state(state="PROGRESS", meta={"step": "Uploading...", "pct": 80})
        audio_stored = upload_file(audio_bytes, f"{data['title'][:40].replace(' ','_')}_voiceover.mp3", "audio/mpeg", user_id)
        srt_bytes = data.get("captions_srt","").encode()
        srt_stored = upload_file(srt_bytes, f"{data['title'][:40].replace(' ','_')}_captions.srt", "text/plain", user_id)
        record = save_product_to_db(user_id, "video_script", data["title"], audio_stored["url"], audio_stored["path"],
            {"platform": platform, "style": style, "length": length,
             "script": data.get("script"), "hashtags": data.get("hashtags"),
             "srt_url": srt_stored["url"], "thumbnail_prompt": data.get("thumbnail_prompt")})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "audio_url": audio_stored["url"],
                "srt_url": srt_stored["url"], "script": data}
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

# ── IMAGE PACK ──
@celery_app.task(bind=True, name="generate_image_pack_task", max_retries=2)
def generate_image_pack_task(self, user_id: str, theme: str, count: int, style: str):
    from services.ai_service import generate_image_pack
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    import httpx
    try:
        self.update_state(state="PROGRESS", meta={"step": "Generating images...", "pct": 10})
        images = run_async(generate_image_pack(theme, count, style))
        results = []
        for i, img in enumerate(images):
            self.update_state(state="PROGRESS", meta={"step": f"Downloading image {i+1}/{count}...", "pct": 10 + (i/count*70)})
            resp = httpx.get(img["url"], timeout=30)
            stored = upload_file(resp.content, f"img_{i+1}.png", "image/png", user_id)
            results.append({**img, "stored_url": stored["url"]})
        record = save_product_to_db(user_id, "image_pack", f"{theme} Image Pack",
            results[0]["stored_url"] if results else "", "",
            {"theme": theme, "style": style, "images": results})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "images": results}
    except Exception as e:
        raise self.retry(exc=e, countdown=20)

# ── WEBSITE ──
@celery_app.task(bind=True, name="generate_website_task", max_retries=3)
def generate_website_task(self, user_id: str, business_name: str, niche: str, style: str):
    from services.ai_service import generate_website
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    try:
        self.update_state(state="PROGRESS", meta={"step": "Building website...", "pct": 20})
        data = run_async(generate_website(business_name, niche, style))
        html_bytes = data.get("html","").encode()
        self.update_state(state="PROGRESS", meta={"step": "Uploading...", "pct": 80})
        stored = upload_file(html_bytes, f"{business_name.replace(' ','_')}_website.html", "text/html", user_id)
        record = save_product_to_db(user_id, "website", f"{business_name} Website",
            stored["url"], stored["path"],
            {"niche": niche, "style": style, "sections": data.get("sections")})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "url": stored["url"], "preview_html": data.get("html","")}
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

# ── CONTENT PACK ──
@celery_app.task(bind=True, name="generate_content_pack_task", max_retries=3)
def generate_content_pack_task(self, user_id: str, topic: str, pack_type: str):
    from services.ai_service import generate_content_pack
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    import json
    try:
        self.update_state(state="PROGRESS", meta={"step": "Writing content...", "pct": 30})
        data = run_async(generate_content_pack(topic, pack_type))
        json_bytes = json.dumps(data, indent=2).encode()
        stored = upload_file(json_bytes, f"{topic[:30].replace(' ','_')}_{pack_type}_pack.json", "application/json", user_id)
        record = save_product_to_db(user_id, "content_pack", f"{topic} — {pack_type.title()} Pack",
            stored["url"], stored["path"], {"pack_type": pack_type, "count": len(data.get("pieces",[]))})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "data": data}
    except Exception as e:
        raise self.retry(exc=e, countdown=10)

# ── PROMPT PACK ──
@celery_app.task(bind=True, name="generate_prompt_pack_task", max_retries=3)
def generate_prompt_pack_task(self, user_id: str, category: str, count: int):
    from services.ai_service import generate_prompt_pack
    from services.storage_service import upload_file, save_product_to_db, deduct_credit
    import json
    try:
        self.update_state(state="PROGRESS", meta={"step": "Engineering prompts...", "pct": 30})
        data = run_async(generate_prompt_pack(category, count))
        json_bytes = json.dumps(data, indent=2).encode()
        stored = upload_file(json_bytes, f"{category.replace(' ','_')}_prompt_pack.json", "application/json", user_id)
        record = save_product_to_db(user_id, "prompt_pack", f"{category} Prompt Pack ({count} prompts)",
            stored["url"], stored["path"], {"category": category, "count": count})
        deduct_credit(user_id)
        return {"status": "done", "product": record, "data": data}
    except Exception as e:
        raise self.retry(exc=e, countdown=10)
