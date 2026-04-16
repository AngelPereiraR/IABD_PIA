# Platform Redesign: Dual-Mode Job Offer Analysis System

**Date:** 2026-04-16  
**Author:** Angel Pereira  
**Status:** Design Approved

---

## Executive Summary

Redesign the platform from a **passive automatic monitoring system** (Gmail → Telegram alerts) to a **dual-mode architecture**:

1. **Automatic Backend Daemon** (private): Monitors Gmail for job offers, analyzes them, sends alerts via Telegram (existing functionality preserved)
2. **Interactive Web Platform** (public): Multi-user SaaS where users upload CVs, submit job offers (text or URL), receive analysis and CV adaptations

Both modes share the same core analysis engine (DeepSeek AI) and leverage existing modules (`brain.py`, `scraper.py`, `loader.py`).

---

## 1. Architecture Overview

### 1.1 High-Level Design

**Approach: Option 2 (Monolithic FastAPI with Shared Modules)**

Single FastAPI application serving both:
- **Private daemon thread**: Automatic Gmail monitoring loop (10 min intervals)
- **Public HTTP endpoints**: User-facing web API with authentication

**Future Evolution: Option 3 (Task Queue)**
- Planned migration to Celery + Redis for scalability
- Non-blocking analysis with progress tracking
- Documented as Phase 2 roadmap

### 1.2 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn |
| **Authentication** | JWT + OAuth2 (Google primary, email fallback) |
| **Database** | PostgreSQL (Neon) |
| **File Storage** | Cloudinary (CVs, adapted PDFs) |
| **AI Engine** | DeepSeek API + LangChain |
| **Web Scraping** | Jina AI → FireCrawl → fallback |
| **PDF Generation** | reportlab |
| **Frontend** | React + Tailwind (existing) |

---

## 2. Data Model

### 2.1 Database Schema

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  auth_provider ENUM('google', 'email') NOT NULL,
  password_hash VARCHAR(255), -- NULL if OAuth
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- CVs table (one current per user, historical preserved)
CREATE TABLE cvs (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_url VARCHAR(255) NOT NULL, -- Cloudinary URL
  uploaded_at TIMESTAMP DEFAULT NOW(),
  is_current BOOLEAN DEFAULT TRUE
);

-- Job offer analyses
CREATE TABLE analyses (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  offer_text TEXT,
  offer_url VARCHAR(255),
  extracted_title VARCHAR(255),
  extracted_company VARCHAR(255),
  score INTEGER CHECK (score >= 0 AND score <= 100), -- 0-100
  scoring_details JSONB, -- Breakdown: ATS score, recruiter score, reasoning
  is_valid BOOLEAN, -- TRUE if score >= threshold (60)
  analysis_result JSONB, -- Full DeepSeek response
  created_at TIMESTAMP DEFAULT NOW()
);

-- CV adaptations (results of confirmed analyses)
CREATE TABLE cv_adaptations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  adapted_cv_html TEXT, -- HTML preview
  adapted_cv_url VARCHAR(255), -- Cloudinary PDF URL
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 Key Constraints

- Each user can have multiple CVs (historical), but only one marked as `is_current`
- Each analysis links to one user and one CV (implicit via user_id)
- CV adaptations are immutable once created (audit trail)

---

## 3. API Specification

### 3.1 Authentication Endpoints

```
POST /auth/register
  Body: { email, password?, auth_provider }
  Response: { user_id, token }
  
POST /auth/login
  Body: { email, password }
  Response: { user_id, token }
  
POST /auth/google-callback
  Query: code
  Response: { user_id, token }
  
GET /auth/me
  Headers: Authorization: Bearer <token>
  Response: { user_id, email, auth_provider }
```

### 3.2 CV Management Endpoints

```
POST /cv/upload
  Headers: Authorization
  Body: FormData { cv_file: PDF }
  Response: { cv_id, file_url, is_current }
  
GET /cv/current
  Headers: Authorization
  Response: { cv_id, file_url, uploaded_at }
  
GET /cv/history
  Headers: Authorization
  Response: [ { cv_id, file_url, uploaded_at, is_current } ]
```

### 3.3 Analysis Endpoints

```
POST /analysis/create
  Headers: Authorization
  Body: { offer_text? OR offer_url? }
  Response: { analysis_id, score, is_valid, scoring_details }
  
GET /analysis/{id}
  Headers: Authorization
  Response: { analysis_id, score, is_valid, extracted_title, 
              extracted_company, scoring_details, analysis_result }
  
GET /analysis/list
  Headers: Authorization
  Query: limit=10, offset=0
  Response: [ { analysis_id, score, is_valid, created_at } ]
```

### 3.4 CV Adaptation Endpoints

```
POST /adaptation/create
  Headers: Authorization
  Body: { analysis_id }
  Precondition: analysis.is_valid == TRUE
  Response: { adaptation_id, adapted_cv_html, download_url }
  
GET /adaptation/{id}
  Headers: Authorization
  Response: { adaptation_id, adapted_cv_html, adapted_cv_url, 
              download_url, copy_html_payload }
  
GET /adaptation/list
  Headers: Authorization
  Response: [ { adaptation_id, created_at, download_url } ]
  
GET /adaptation/{id}/download
  Headers: Authorization
  Response: PDF file (application/pdf)
```

### 3.5 Health & Admin Endpoints (Private)

```
GET /health
  Response: "OK"
  
GET /bot/status
  Response: { bot_running, last_analysis_time, next_run }
  
POST /bot/trigger
  Body: { force: boolean }
  Response: { queued, job_id }
```

---

## 4. User Workflows

### 4.1 Web User Flow (Public)

1. **Registration/Login**
   - User signs up via email + password OR Google OAuth
   - System creates user record, issues JWT token

2. **Profile Setup**
   - User navigates to Profile
   - Uploads PDF (CV)
   - System stores in Cloudinary, marks as `is_current`

3. **Job Analysis**
   - User goes to Analyzer
   - Pastes job offer (text OR URL)
   - System extracts text (scrapes if URL), sends to DeepSeek
   - DeepSeek returns score (0-100) + detailed breakdown
   - UI shows:
     - If score ≥ 60 (valid): "Offer matches your profile" + details + **"Adapt CV" button**
     - If score < 60 (invalid): "Not a good fit" + reasoning + **no adaptation button**

4. **CV Adaptation (if valid)**
   - User clicks "Adapt CV"
   - System renders CV with targeted modifications (skills, experience emphasis, keywords)
   - UI shows three options:
     - **Preview**: Interactive HTML editor
     - **Download PDF**: Generates PDF via reportlab
     - **Copy to Clipboard**: Copies HTML as text

5. **Histor**
   - User views all previous analyses
   - Can re-download any adapted CV
   - Can filter by date, company, score

### 4.2 Automatic Daemon Flow (Private - Ángel only)

Runs as daemon thread in FastAPI process:

1. Every 10 minutes:
   - Connect to Gmail (OAuth)
   - Fetch unread job alerts from LinkedIn/InfoJobs
   
2. For each offer:
   - Scrape full text (Jina → FireCrawl → HTTP fallback)
   - Send to DeepSeek for analysis
   - If score ≥ 70: send Telegram alert with details
   - Clean up old emails (>14 days)

3. Error handling:
   - Exponential backoff on failures
   - Recreate Gmail agent each loop (credential refresh)
   - Log errors but don't crash daemon

---

## 5. Analysis Engine (brain.py Shared)

### 5.1 Scoring Logic

DeepSeek performs **dual-phase analysis**:

1. **ATS Scoring** (0-100): Keyword matching against job description
   - Hard skills match (required tech stack)
   - Experience level alignment
   - Location/visa compatibility

2. **Recruiter Scoring** (0-100): Human factors
   - Cultural fit indicators
   - Growth opportunity alignment
   - Compensation expectation match

3. **Final Score**: Weighted average or max(both) depending on analysis type

4. **Grounding Principle**: DeepSeek never invents details not in original offer or CV

### 5.2 Extraction

For each offer, extract and structure:
- Job title
- Company name
- Location
- Salary range (if present)
- Key benefits
- Required skills
- Nice-to-have skills
- Experience level needed

---

## 6. Frontend Integration Points

### 6.1 New Pages

- `/auth/login` — Email/password + Google OAuth button
- `/auth/register` — Email registration form
- `/profile` — CV upload, current CV display
- `/analyzer` — Offer input (text area + URL), analysis results
- `/history` — Past analyses, download adapted CVs
- `/adaptation/{id}` — HTML preview, download/copy buttons

### 6.2 Existing Components to Reuse

- Tailwind styling (existing)
- Navigation layout
- Loading states, error handling

---

## 7. Implementation Phases

### Phase 1: MVP (Monolithic, Option 2)
- Single FastAPI app with both daemon + public endpoints
- JWT auth + OAuth Google integration
- CV upload to Cloudinary
- Analysis endpoint (DeepSeek)
- CV adaptation with HTML + PDF generation
- User history

### Phase 2: Scalability (Future - Option 3)
- Extract analysis jobs → Celery queue
- Add Redis for job tracking
- Implement WebSocket progress updates
- Horizontal scaling for multiple workers

### Phase 3: Enhancements
- Email digest of weekly top matches
- CV version comparison UI
- Advanced filtering (salary range, tech stack)
- User analytics dashboard

---

## 8. Key Design Decisions & Rationale

| Decision | Option Chosen | Why |
|----------|---------------|-----|
| Architecture | Monolith (Option 2) | Fast MVP, shared code, simple deployment. Scale later with Option 3. |
| Auth | OAuth (Google) + Email | Lower friction for signup, fallback for non-Google users. |
| CV Input | Upload PDF + Auto-extract | Easier for users than manual entry. |
| Offer Input | Text OR URL | Flexibility; users can paste offer directly or share link. |
| Offer Analysis | Sync (blocking) | Simple MVP. Async queue for future (Option 3). |
| Adaptation Output | HTML + PDF + Copy | Maximum flexibility for users. |
| Data Persistence | Full history | Allows users to review past analyses and re-use adaptations. |
| CV Storage | Cloudinary | Reliable, handles scaling, simple integation. |
| DeepSeek Calls | Batched per analysis | Cost-effective; one call per offer submitted. |

---

## 9. Error Handling & Edge Cases

### 9.1 Analysis Failures

- **URL scrape fails**: Show error, suggest manual text input
- **DeepSeek API timeout**: Retry with exponential backoff, show user "try again"
- **Invalid PDF upload**: Return validation error, suggest format

### 9.2 Auth Failures

- **Google OAuth failure**: Fall back to email login form
- **JWT expired**: Refresh token endpoint
- **User already exists**: Redirect to login

### 9.3 CV Adaptation Failures

- **PDF generation fails**: Show HTML fallback, offer copy-to-clipboard
- **Cloudinary upload fails**: Retry 3 times, then return in-memory PDF

---

## 10. Testing Strategy

### 10.1 Unit Tests (pytest)

- Auth flows (registration, login, token validation)
- CV upload validation
- Analysis scoring logic
- CV adaptation generation
- Daemon scheduling

### 10.2 Integration Tests

- Full flow: login → upload CV → analyze offer → adapt
- OAuth callback flow
- Scraper cascade (Jina → FireCrawl)
- Database persistence

### 10.3 Manual Testing

- Real OAuth flow with Google
- Real DeepSeek API calls
- PDF generation quality
- UI responsiveness

---

## 11. Deployment

### 11.1 Local Development

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python main.py  # Runs FastAPI + daemon thread
```

### 11.2 Production (HF Spaces / Render)

```bash
# Docker container
uvicorn main:app --host 0.0.0.0 --port $PORT

# Environment variables injected at runtime
# Daemon thread auto-starts (thread-safe flag prevents duplicates)
```

### 11.3 Database Migrations

- Use Alembic for schema versioning
- Store migrations in `alembic/versions/`

---

## 12. Security Considerations

- **JWT Secret**: Stored in env vars, never in code
- **OAuth Secrets**: Google credentials in env vars
- **Password Storage**: bcrypt hashing (if email auth used)
- **SQL Injection**: ORM-based (SQLAlchemy) prevents injection
- **CSRF**: Token-based for state-changing operations
- **Rate Limiting**: 100 requests/min per user (built-in or via middleware)
- **File Upload**: Validate PDF only, scan for malware (ClamAV optional)

---

## 13. Monitoring & Observability

### 13.1 Daemon Health

- Log each analysis cycle: start time, duration, success/failure
- Alert if daemon misses 2 consecutive cycles
- Endpoint `/bot/status` shows last run and next scheduled run

### 13.2 API Metrics

- Request latency (analysis endpoint ~2-5s due to DeepSeek)
- Error rates by endpoint
- User signup/login trends

### 13.3 Logging

- Structured logs (JSON) with timestamps
- Log levels: INFO (analysis start/end), ERROR (failures), DEBUG (detailed steps)

---

## 14. Future Considerations

### Option 3: Async Architecture (Phase 2)

When traffic grows, migrate to:

```
Frontend submits offer → FastAPI enqueues to Redis
                      ↓
                   Celery Worker pool analyzes
                      ↓
                   WebSocket pushes progress to user
                      ↓
                   User sees "Analysis 45% complete"
```

Benefits:
- Non-blocking user experience
- Horizontal scaling (add more workers)
- Better handling of slow DeepSeek calls

### Potential Integrations

- **LinkedIn Direct**: Fetch offer links directly from LinkedIn messages
- **Email Forwarding**: Users forward offers to a bot email address
- **Slack Bot**: Analyze offers from Slack
- **CV Versioning**: Track CV evolution over time, compare versions

---

## 15. Success Criteria

| Criterion | Acceptance |
|-----------|-----------|
| **User Registration** | OAuth Google + email signup working |
| **CV Upload** | PDF stored in Cloudinary, retrievable |
| **Job Analysis** | DeepSeek returns valid scores 0-100, <5s response |
| **CV Adaptation** | HTML + PDF generated, matches offer keywords |
| **Daemon** | Runs 10-min loop, processes Gmail, sends Telegram alerts |
| **Data Persistence** | User history visible after logout/login |
| **Error Handling** | Graceful failures, user-friendly messages |
| **Performance** | Analysis endpoint <5s, page loads <2s |
| **Security** | No SQL injection, JWT validated, auth flows secure |

---

## 16. Rollout Plan

1. **Week 1-2**: Database schema + FastAPI skeleton + shared modules refactoring
2. **Week 3**: Auth (JWT + OAuth Google)
3. **Week 4**: CV upload + storage (Cloudinary)
4. **Week 5**: Analysis endpoint (DeepSeek integration)
5. **Week 6**: CV adaptation (HTML + PDF)
6. **Week 7**: Frontend pages + integration
7. **Week 8**: Testing + bug fixes
8. **Week 9**: Daemon integration + Telegram alerts
9. **Week 10**: Deployment + monitoring setup

---

## Document Review Checklist

- [x] Placeholders removed (no TBD/TODO)
- [x] Architecture consistent with all sections
- [x] Scope clear (MVP focus, future roadmap separate)
- [x] No contradictions between sections
- [x] All requirements addressed
- [x] Success criteria measurable

---

**Spec Status: READY FOR IMPLEMENTATION**
