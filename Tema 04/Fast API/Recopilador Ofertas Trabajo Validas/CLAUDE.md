# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Recopilador Inteligente de Ofertas de Trabajo** is an automated job offer monitoring and analysis system. It monitors Gmail for job alerts from LinkedIn and InfoJobs, scrapes the offer details, analyzes them against a user's CV using DeepSeek AI via LangChain, and sends filtered alerts via Telegram.

Core value: Intelligent filtering that simulates both ATS (Applicant Tracking System) and human recruiter evaluation, returning only truly relevant opportunities.

## Architecture

**Dual-Process Design:**

1. **FastAPI Web Server** (`main.py`)
   - Two health-check endpoints: `GET /` and `GET /health`
   - Runs on port from `PORT` env var (default 7860 for HF Spaces)
   - Required to keep the process alive and respond to health checks
   - No business logic here—just a keep-alive endpoint

2. **Background Bot Thread** (async infinite loop in `main.py`)
   - Runs daemon thread on import
   - Main logic flow: Gmail → Scraper → Brain (DeepSeek AI) → Telegram
   - Polling interval: 600 seconds (10 minutes)
   - Uses exponential backoff on errors

**Module Organization** (`src/`):

- **mail_agent.py**: Gmail OAuth integration. Fetches unread job alerts, auto-cleans old emails (>14 days)
- **scraper.py**: Web scraping with cascading strategy—Jina AI → FireCrawl → direct HTTP. Handles platform-specific CSS selectors (LinkedIn, InfoJobs)
- **brain.py**: DeepSeek integration via LangChain. Implements dual-phase filtering (ATS + recruiter evaluation), scoring 0-100, structured extraction (title, company, salary, benefits)
- **bot.py**: Telegram notifier. Sends alerts with visual formatting (icons, progress bars)
- **loader.py**: Loads user's CV from PDF file into context for analysis
- **setup_auth.py**: OAuth helper for Gmail initial setup

## Development

**Environment Setup:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Local Execution:**
```bash
# Run the server + bot thread
python main.py
```

**Git Policy:**
- ⛔ NO git commands in Claude Code conversations
- Files are created/modified with Read/Edit/Write tools only
- Commits are handled outside of Claude Code
- Branch management is handled outside of Claude Code

**Required Environment Variables** (see `.env.template`):
- `DATABASE_URL`: PostgreSQL connection (Neon)
- `CLOUDINARY_*`: Storage credentials (3 vars)
- `DEEPSEEK_API_KEY`: DeepSeek AI analysis
- `GOOGLE_CREDENTIALS_JSON`: Gmail API service account JSON
- `GOOGLE_TOKEN_JSON`: Gmail OAuth token
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Target chat for notifications
- `JINA_API_KEY`: Jina AI scraping
- `FIRECRAWL_API_KEY`: FireCrawl scraping (backup)
- `PORT`: Server port (default 7860)

**Production Deployment** (HF Spaces / Render):
```bash
# Docker builds using entrypoint.sh, which:
# 1. Injects secrets from env vars into credentials.json, token.json
# 2. Runs: uvicorn main:app --host 0.0.0.0 --port $PORT (7860 for HF Spaces)
```

## Key Implementation Details

**Thread Safety:**
- Bot thread flag `_bot_started` prevents duplicate threads if uvicorn restarts workers
- Thread is daemon (won't block shutdown)

**Error Resilience:**
- Gmail agent recreated each loop (forces credential refresh, avoids session timeout)
- Exponential backoff on connection failures
- Cascade scraper strategy ensures redundancy

**FastAPI Migration** (recent):
- Changed from Flask/Gunicorn to FastAPI/Uvicorn
- No functional changes—same endpoints, same bot logic
- Updated `requirements.txt` and `entrypoint.sh` accordingly

## Important Notes

- **CV Path**: `data/cv_usuario.pdf` must exist for the bot to run (checked on startup)
- **Polling**: 10-minute intervals to be respectful of APIs and reduce costs
- **Email Cleanup**: Automatically removes job alerts older than 14 days
- **Anti-Alucinination**: Brain uses "grounding"—avoids making up details not in the original offer text
- **Health Checks**: `/health` endpoint returns "OK" for Render uptime monitoring

## Testing

**Framework:** unittest (NO pytest)

**Test Execution:**
```bash
# Plan 01 Tests (10 tests)
python tests/test_plan_01_simple.py

# Plan 02 Tests (29 tests)
python tests/test_plan_02_apis.py
```

**Test Location:** All tests in `tests/` directory with naming pattern `test_plan_XX_*.py`

**Guidelines:**
- ✅ Use unittest only (no pytest)
- ✅ Create tests in `tests/` folder
- ✅ No git commands in any conversation
- ✅ Tests should validate: imports, endpoints, schemas, dependencies, file structure
- ✅ Generate detailed markdown reports in `tests/TEST_RESULTS_*.md`

**Testing Checklist** (for core module changes):
1. Verify email filtering logic works (test with real/mock Gmail responses)
2. Check scraper cascade strategy (Jina → FireCrawl → fallback)
3. Validate DeepSeek analysis returns valid JSON and scoring logic
4. Ensure Telegram formatting preserves emojis and newlines
5. Confirm bot thread starts cleanly and doesn't duplicate on restart
6. Test LaTeX compilation and PDF generation from engine.py
7. Run appropriate test suite to validate changes
8. Check test results in `tests/TEST_RESULTS_*.md` reports
