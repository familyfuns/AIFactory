# 🏭 ProductAI — Full AI Digital Product Factory SaaS

A complete, production-ready SaaS that generates and sells:
- 📄 PDFs, Ebooks, Audiobooks, Coloring Books
- 🎬 Videos (TikTok, YouTube, Shorts)
- 🖼️ AI Images & Art Packs
- 🌐 Full Websites & Landing Pages
- ✍️ Content (blogs, emails, social, copy)
- 🎵 Music & Podcast Scripts
- 📊 Templates, Planners, Trackers
- 💡 Prompt Packs & AI Tools

## Tech Stack
- **Frontend**: Vanilla HTML/CSS/JS (GitHub Pages hostable)
- **Backend**: FastAPI + Python
- **Queue**: Celery + Redis
- **Database**: Supabase (PostgreSQL)
- **Payments**: Stripe
- **AI**: Claude API, OpenAI, ElevenLabs, Stability AI
- **Storage**: Supabase Storage (S3-compatible)
- **Deploy**: GitHub Pages (frontend) + Railway (backend)

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/productai.git
cd productai
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
uvicorn main:app --reload
```

### 3. Frontend
Open `frontend/index.html` in browser, or serve with:
```bash
cd frontend
python -m http.server 8080
```

### 4. Deploy Frontend to GitHub Pages
```bash
git add .
git commit -m "deploy"
git push origin main
# Enable Pages in repo Settings → Pages → main branch
```

### 5. Deploy Backend to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

## Environment Variables
See `backend/.env.example` for all required keys.

## Revenue Model
- Free tier: 3 products/month (watermarked)
- Starter $19/mo: 50 products
- Pro $49/mo: 500 products  
- Agency $149/mo: unlimited + white-label
- Marketplace: 15% commission on sales
