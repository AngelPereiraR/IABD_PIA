# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Recopilador Inteligente de Ofertas de Trabajo** is an automated job offer monitoring and analysis system. It monitors Gmail for job alerts from LinkedIn and InfoJobs, scrapes the offer details, analyzes them against a user's CV using Gemini AI, and sends filtered alerts via Telegram.

Core value: Intelligent filtering that simulates both ATS (Applicant Tracking System) and human recruiter evaluation, returning only truly relevant opportunities.

## Architecture

**Dual-Process Design:**

1. **FastAPI Web Server** (`main.py`)
   - Two health-check endpoints: `GET /` and `GET /health`
   - Runs on port from `PORT` env var (default 10000)
   - Required by Render to keep the process alive
   - No business logic here—just a keep-alive endpoint

2. **Background Bot Thread** (async infinite loop in `main.py`)
   - Runs daemon thread on import
   - Main logic flow: Gmail → Scraper → Brain (Gemini AI) → Telegram
   - Polling interval: 600 seconds (10 minutes)
   - Uses exponential backoff on errors

**Module Organization** (`src/`):

- **mail_agent.py**: Gmail OAuth integration. Fetches unread job alerts, auto-cleans old emails (>14 days)
- **scraper.py**: Web scraping with cascading strategy—Jina AI → FireCrawl → direct HTTP. Handles platform-specific CSS selectors (LinkedIn, InfoJobs)
- **brain.py**: Gemini 2.5 Flash integration. Implements dual-phase filtering (ATS + recruiter evaluation), scoring 0-100, structured extraction (title, company, salary, benefits)
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

**Required Environment Variables** (see `.env.template`):
- `GOOGLE_CREDENTIALS_JSON`: Gmail API service account JSON
- `GOOGLE_TOKEN_JSON`: Gmail OAuth token
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Target chat for notifications
- `GEMINI_API_KEY`: Google Gemini API key
- `JINA_API_KEY`: Jina AI API key
- `FIRECRAWL_API_KEY`: FireCrawl API key
- `PORT`: Server port (default 10000)

**Production Deployment** (Render):
```bash
# Docker builds using entrypoint.sh, which:
# 1. Injects secrets from env vars into credentials.json, token.json, .env
# 2. Runs: uvicorn main:app --host 0.0.0.0 --port $PORT
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

## Testing Checklist

When making changes to core modules:
1. Verify email filtering logic works (test with real/mock Gmail responses)
2. Check scraper cascade strategy (Jina → FireCrawl → fallback)
3. Validate Gemini prompt returns valid JSON and scoring logic
4. Ensure Telegram formatting preserves emojis and newlines
5. Confirm bot thread starts cleanly and doesn't duplicate on restart
