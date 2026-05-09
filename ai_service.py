"""
AI Generation Services
Handles all AI API calls: Claude, OpenAI, ElevenLabs, Stability AI
"""
import anthropic
import openai
import httpx
import base64
import os
import json
from typing import Optional

# ── Clients ──
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
STABILITY_KEY  = os.getenv("STABILITY_API_KEY")

# ═══════════════════════════════════════════════
# CLAUDE — TEXT GENERATION
# ═══════════════════════════════════════════════

async def claude_generate(prompt: str, system: str = "", max_tokens: int = 4096) -> str:
    """Generate text with Claude claude-sonnet-4-20250514"""
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"model": "claude-sonnet-4-20250514", "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system
    response = claude_client.messages.create(**kwargs)
    return response.content[0].text

async def generate_ebook(topic: str, chapters: int = 10, audience: str = "general") -> dict:
    system = "You are an expert author and educator. Write comprehensive, engaging content."
    prompt = f"""Write a complete ebook outline and first chapter on: "{topic}"
Audience: {audience}
Chapters: {chapters}

Return JSON with:
{{
  "title": "...",
  "subtitle": "...",
  "author": "ProductAI",
  "description": "...",
  "chapters": [
    {{"number": 1, "title": "...", "summary": "...", "content": "full content here, at least 500 words"}},
    ...
  ],
  "resources": ["url1", "url2"],
  "affiliate_keywords": ["keyword1", "keyword2"]
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_video_script(topic: str, length: str = "medium", style: str = "educational", platform: str = "youtube") -> dict:
    system = "You are a viral video scriptwriter. Write engaging, hook-driven scripts."
    durations = {"short": "60 seconds", "medium": "5 minutes", "long": "15 minutes"}
    prompt = f"""Write a complete video script for: "{topic}"
Platform: {platform} | Style: {style} | Length: {durations.get(length,'5 minutes')}

Return JSON:
{{
  "title": "...",
  "hook": "opening 5-second hook line",
  "description": "video description with SEO keywords",
  "script": [
    {{"timestamp": "0:00", "speaker": "narrator", "text": "...", "visual": "what to show on screen"}},
    ...
  ],
  "captions_srt": "1\\n00:00:00,000 --> 00:00:05,000\\nOpening line here\\n\\n2\\n...",
  "hashtags": ["#tag1","#tag2"],
  "affiliate_products": ["product name: affiliate angle"],
  "thumbnail_prompt": "DALL-E prompt for thumbnail image"
}}"""
    raw = await claude_generate(prompt, system, max_tokens=6000)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_website(business_name: str, niche: str, style: str = "modern") -> dict:
    system = "You are an expert web developer and copywriter. Generate complete, production-ready websites."
    prompt = f"""Generate a complete single-page website for:
Business: "{business_name}" | Niche: {niche} | Style: {style}

Return JSON:
{{
  "html": "COMPLETE full HTML file with embedded CSS and JS, no external deps except Google Fonts",
  "meta_title": "...",
  "meta_description": "...",
  "sections": ["hero","features","pricing","testimonials","cta","footer"]
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_content_pack(topic: str, pack_type: str = "social") -> dict:
    system = "You are a viral content strategist and copywriter."
    templates = {
        "social": "30 social media posts (mix of Twitter/X, Instagram, LinkedIn, TikTok captions)",
        "email": "7-part email sequence (welcome, nurture, pitch, follow-up)",
        "blog": "5 complete SEO blog posts (800+ words each)",
        "ads": "20 ad copy variations (headlines + body + CTA for Facebook, Google, TikTok)",
        "podcast": "8-episode podcast outline with show notes and episode scripts"
    }
    prompt = f"""Create a {pack_type} content pack for topic: "{topic}"
Generate: {templates.get(pack_type, templates['social'])}

Return JSON:
{{
  "pack_type": "{pack_type}",
  "topic": "{topic}",
  "pieces": [
    {{"type": "...", "platform": "...", "title": "...", "content": "...", "notes": "..."}},
    ...
  ],
  "strategy_tips": ["tip1","tip2"],
  "affiliate_angles": ["angle1","angle2"]
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_audiobook(topic: str, chapters: int = 8) -> dict:
    system = "You are a professional audiobook narrator and author."
    prompt = f"""Write a complete professional audiobook on: "{topic}"
Chapters: {chapters}

Return JSON:
{{
  "title": "...",
  "subtitle": "...",
  "total_runtime_estimate": "X hours Y minutes",
  "chapters": [
    {{
      "number": 1,
      "title": "...",
      "runtime_estimate": "X minutes",
      "narrator_notes": "tone, pace, emphasis notes",
      "content": "Full chapter text (1000+ words, written for audio, natural speech patterns)",
      "chapter_summary": "...",
      "key_takeaways": ["..."]
    }}
  ],
  "introduction": "...",
  "conclusion": "...",
  "bibliography": ["source1","source2"],
  "affiliate_resources": ["resource + link angle"]
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_prompt_pack(category: str, count: int = 50) -> dict:
    system = "You are an expert AI prompt engineer."
    prompt = f"""Create {count} professional AI prompts for category: "{category}"

Return JSON:
{{
  "category": "{category}",
  "prompts": [
    {{
      "id": 1,
      "title": "...",
      "prompt": "full prompt text",
      "model": "ChatGPT/Claude/Midjourney/DALL-E",
      "use_case": "...",
      "example_output": "brief example"
    }}
  ],
  "usage_guide": "how to use this pack",
  "bonus_tips": ["tip1","tip2"]
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_coloring_book(theme: str, pages: int = 15, age_group: str = "kids") -> dict:
    """Generate image prompts + descriptions for each coloring page"""
    system = "You are a children's book illustrator and art director."
    prompt = f"""Design a {pages}-page coloring book on theme: "{theme}"
Age group: {age_group}

Return JSON:
{{
  "title": "...",
  "subtitle": "...",
  "age_range": "...",
  "pages": [
    {{
      "page_number": 1,
      "scene_title": "...",
      "description": "What to color and where",
      "image_generation_prompt": "Detailed black and white line art prompt for DALL-E/Stability AI, coloring book style, thick outlines, simple...",
      "fun_fact": "Educational fact for this page",
      "difficulty": "easy/medium/hard"
    }}
  ],
  "cover_prompt": "DALL-E prompt for cover page"
}}"""
    raw = await claude_generate(prompt, system, max_tokens=4096)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

async def generate_course(topic: str, level: str = "beginner") -> dict:
    system = "You are an expert online course creator and instructional designer."
    prompt = f"""Design a complete online course on: "{topic}"
Level: {level}

Return JSON:
{{
  "title": "...",
  "subtitle": "...",
  "description": "...",
  "outcomes": ["outcome1","outcome2"],
  "modules": [
    {{
      "number": 1,
      "title": "...",
      "lessons": [
        {{
          "number": "1.1",
          "title": "...",
          "type": "video/reading/exercise/quiz",
          "duration": "X min",
          "script": "Full lesson script/content",
          "resources": ["resource1"]
        }}
      ]
    }}
  ],
  "quizzes": [{{"module": 1, "questions": [{{"q":"...","options":["a","b","c","d"],"answer":"a"}}]}}],
  "certificate_template": "description of certificate design"
}}"""
    raw = await claude_generate(prompt, system, max_tokens=8192)
    return json.loads(raw.strip().lstrip("```json").rstrip("```").strip())

# ═══════════════════════════════════════════════
# OPENAI — IMAGE GENERATION
# ═══════════════════════════════════════════════

async def generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> dict:
    """Generate image with DALL-E 3"""
    response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=1
    )
    return {
        "url": response.data[0].url,
        "revised_prompt": response.data[0].revised_prompt
    }

async def generate_image_pack(theme: str, count: int = 10, style: str = "digital art") -> list[dict]:
    """Generate multiple images for a pack"""
    # Generate prompts first
    prompt_plan = await claude_generate(
        f"Generate {count} unique image prompts for theme '{theme}' in style '{style}'. "
        f"Return JSON array: [{{\"title\": \"...\", \"prompt\": \"detailed DALL-E 3 prompt\"}}]",
        max_tokens=2000
    )
    prompts = json.loads(prompt_plan.strip().lstrip("```json").rstrip("```").strip())

    images = []
    for p in prompts[:count]:
        img = await generate_image(p["prompt"])
        images.append({"title": p["title"], "prompt": p["prompt"], "url": img["url"]})
    return images

# ═══════════════════════════════════════════════
# ELEVENLABS — VOICE / AUDIO
# ═══════════════════════════════════════════════

VOICE_IDS = {
    "narrator_male":    "pNInz6obpgDQGcFmaJgB",
    "narrator_female":  "EXAVITQu4vr4xnSDxMaL",
    "child_friendly":   "jBpfuIE2acCo8z3wKNLl",
    "professional":     "VR6AewLTigWG4xSOukaG",
    "energetic":        "yoZ06aMxZJJ28mfd3POQ",
    "calm":             "nPczCjzI2devNBz1zQrb",
}

async def text_to_speech(text: str, voice: str = "narrator_female", model: str = "eleven_multilingual_v2") -> bytes:
    """Convert text to speech with ElevenLabs"""
    voice_id = VOICE_IDS.get(voice, VOICE_IDS["narrator_female"])
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": model,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5}
            },
            timeout=60.0
        )
        response.raise_for_status()
        return response.content

async def generate_voiceover_chapters(chapters: list[dict], voice: str = "narrator_female") -> list[dict]:
    """Generate audio for each chapter"""
    results = []
    for ch in chapters:
        audio_bytes = await text_to_speech(ch.get("content", ch.get("text", "")), voice)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        results.append({**ch, "audio_b64": audio_b64, "audio_size_kb": len(audio_bytes) // 1024})
    return results

# ═══════════════════════════════════════════════
# STABILITY AI — IMAGE GENERATION (alternative)
# ═══════════════════════════════════════════════

async def stability_generate(prompt: str, negative_prompt: str = "", steps: int = 30) -> bytes:
    """Generate image with Stability AI"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={"Authorization": f"Bearer {STABILITY_KEY}", "Accept": "application/json"},
            json={
                "text_prompts": [
                    {"text": prompt, "weight": 1},
                    {"text": negative_prompt, "weight": -1}
                ],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "steps": steps,
                "samples": 1,
            },
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["artifacts"][0]["base64"])
