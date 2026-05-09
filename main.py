"""
ProductAI — FastAPI Backend
Full AI Digital Product Factory
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

load_dotenv()

from routes.auth import router as auth_router
from routes.generate import router as generate_router
from routes.products import router as products_router
from routes.payments import router as payments_router
from routes.marketplace import router as marketplace_router
from routes.user import router as user_router

# ── Rate limiter ──
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ProductAI API",
    description="AI Digital Product Factory — Generate videos, PDFs, images, websites & more",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "*"),
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(auth_router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(generate_router,    prefix="/api/generate",    tags=["Generate"])
app.include_router(products_router,    prefix="/api/products",    tags=["Products"])
app.include_router(payments_router,    prefix="/api/payments",    tags=["Payments"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["Marketplace"])
app.include_router(user_router,        prefix="/api/user",        tags=["User"])

@app.get("/")
async def root():
    return {"status": "ProductAI API running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
