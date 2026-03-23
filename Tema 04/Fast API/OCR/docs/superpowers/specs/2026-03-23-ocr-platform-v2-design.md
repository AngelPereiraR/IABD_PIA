# OCR Platform v2 - Design Document

**Date:** March 23, 2026
**Status:** Design Approved
**Scope:** Full-stack platform (Backend + Frontend + Infrastructure)

---

## 1. EXECUTIVE SUMMARY

Transform the OCR research project into a production-ready SaaS platform for document digitization. Users can upload images of printed/scanned documents, extract text with 91% accuracy, edit results, and export as TXT/PDF. Backend deploys on HF Spaces (free tier), frontend on Vercel.

**Key Decision:** Use Tesseract + opencv_mg10 (best balance of speed/accuracy for CPU-only environment)

---

## 2. PROBLEM & GOALS

**Current State:**
- Experimental OCR research with 40 configurations tested
- Best result: opencv_mg10 + deepseek (95.35% accuracy, 65s processing)
- Problem: Deepseek requires GPU, not viable on HF Spaces free tier

**Goals:**
- ✅ Choose best combination for serverless deployment (CPU-only)
- ✅ Build full-stack platform (no monolith)
- ✅ Require authentication to prevent bot spam
- ✅ Persist OCRs + metadata in PostgreSQL
- ✅ Store images in Cloudinary
- ✅ Deploy backend on HF Spaces free tier
- ✅ Deploy frontend on Vercel
- ✅ GDPR compliance (export/delete user data)

**Success Criteria:**
- Platform is live and accessible
- Users can authenticate, upload, process, edit, and export OCRs
- Processing completes in <15s on HF Spaces
- 100% uptime via /health endpoint + Cron keep-alive
- All user data compliant with GDPR

---

## 3. SELECTED TECHNOLOGY STACK

### 3.1 OCR Engine Choice

| Option | Accuracy | Speed | Resources | Viable? |
|--------|----------|-------|-----------|---------|
| Deepseek | 95.35% | 65s | High (GPU) | ❌ No GPU on HF Spaces free |
| Paddle | 94.25% | 10s | Medium (GPU) | ❌ No GPU on HF Spaces free |
| **Tesseract** | **91.34%** | **~5-10s** | **Low (CPU)** | **✅ Viable** |

**Decision:** Use **Tesseract + opencv_mg10**
- 91.34% content accuracy is acceptable for digitization use case
- CPU-only, scales to 5-10s on HF Spaces without GPU
- Can always upgrade to GPU-enabled option later

### 3.2 Backend Stack

```
FastAPI (Python 3.11+)
├─ Async request handling with uvicorn
├─ SQLAlchemy ORM for PostgreSQL
├─ Pydantic for validation
├─ PyJWT for authentication
├─ python-multipart for file uploads
├─ cloudinary SDK for image storage
└─ sendgrid SDK for email notifications

Deployment: HuggingFace Spaces (free tier, CPU)
├─ Container: Python 3.11 + Tesseract + OpenCV
├─ Port: 7860 (HF Spaces standard)
└─ Restart policy: manual + /health endpoint for keep-alive
```

### 3.3 Frontend Stack

```
React 18 + TypeScript (optional but recommended)
├─ react-router-dom for navigation
├─ axios for API calls
├─ tailwindcss for styling
├─ react-markdown for rendering OCR text
├─ jsPDF + html2pdf for PDF export
└─ localStorage for JWT token storage

Deployment: Vercel
├─ Auto-deploy from GitHub on push
├─ Environment variables per environment
└─ CDN + edge functions for performance
```

### 3.4 Database & Storage

```
PostgreSQL (Neon.tech free tier)
├─ 1GB storage (sufficient for metadata + text)
├─ Managed backups
└─ Connection pooling included

Cloudinary (free tier)
├─ Image uploads and transformations
├─ CDN for image delivery
└─ 25GB monthly quota
```

### 3.5 Email Service

```
SendGrid (free tier)
├─ 100 emails/day
├─ Transactional email for contact form + password resets
└─ Email verification (optional, not required for v1)
```

---

## 4. ARCHITECTURE

### 4.1 System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (Vercel)                         │
│  Landing | Auth | OCR | History | Profile | Contact         │
└──────────────────────┬──────────────────────────────────────┘
                       │ API REST + JWT
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            FastAPI Backend (HF Spaces)                       │
│  /auth | /ocr | /history | /user | /contact | /health       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   PostgreSQL    Cloudinary       SendGrid
   (Neon)        (images)         (email)
```

### 4.2 Backend Modules

```
backend/
├─ app.py                    # FastAPI app initialization
├─ config.py               # Environment variables
├─ requirements.txt        # Python dependencies
├─ Dockerfile              # Container for HF Spaces
├─
├─ auth/
│  ├─ routes.py           # POST /auth/register, /login, /logout
│  ├─ schemas.py          # Pydantic models (UserRegister, UserLogin)
│  ├─ service.py          # Password hashing, JWT generation
│  └─ middleware.py       # JWT validation middleware
├─
├─ ocr/
│  ├─ routes.py           # POST /ocr/upload, GET /ocr/{id}/status, GET /ocr/{id}/result
│  ├─ schemas.py          # OCRRequest, OCRResponse
│  ├─ service.py          # Tesseract integration, opencv_mg10 layout detection
│  ├─ processor.py        # Background thread for OCR processing
│  └─ storage.py          # Cloudinary upload/download
├─
├─ history/
│  ├─ routes.py           # GET /ocr/list, DELETE /ocr/{id}
│  ├─ schemas.py          # OCRListItem, OCRDetail
│  └─ exports.py          # TXT/PDF export logic
├─
├─ user/
│  ├─ routes.py           # GET /user/profile, PUT /user/profile, POST /user/export-gdpr, DELETE /user/account
│  ├─ schemas.py          # UserProfile, UserUpdate
│  └─ gdpr.py             # GDPR export (ZIP), account deletion
├─
├─ contact/
│  ├─ routes.py           # POST /contact
│  ├─ schemas.py          # ContactMessage
│  └─ service.py          # SendGrid integration
├─
├─ health/
│  └─ routes.py           # GET /health
├─
├─ database/
│  ├─ models.py           # SQLAlchemy models (User, OCR, ContactMessage)
│  ├─ connection.py       # Database session
│  └─ migrations/         # Alembic migration files
├─
├─ utils/
│  ├─ validators.py       # Email, password, image validation
│  ├─ logger.py          # Logging configuration
│  └─ errors.py          # Custom exception classes
└─
└─ logs/                   # Application logs (rotated daily)
```

### 4.3 Frontend Structure

```
frontend/
├─ public/
│  ├─ index.html
│  └─ favicon.ico
├─
├─ src/
│  ├─ index.tsx
│  ├─ App.tsx             # Router setup
│  ├─ config.ts           # API_URL, constants
│  │
│  ├─ pages/
│  │  ├─ Landing.tsx      # Hero + features + FAQ
│  │  ├─ Register.tsx     # Email/password form
│  │  ├─ Login.tsx        # Email/password form
│  │  ├─ OCR.tsx          # Upload + editor + export
│  │  ├─ History.tsx      # List + search + delete
│  │  ├─ Profile.tsx      # Settings + GDPR + logout
│  │  ├─ Contact.tsx      # Contact form
│  │  ├─ Privacy.tsx      # Privacy policy
│  │  └─ Terms.tsx        # Terms of service
│  │
│  ├─ components/
│  │  ├─ Header.tsx       # Navigation + dark mode toggle
│  │  ├─ Footer.tsx       # Links + copyright
│  │  ├─ ImageUpload.tsx  # File input + preview + validation
│  │  ├─ TextEditor.tsx   # Editable textarea with toolbar
│  │  ├─ ProcessingSpinner.tsx  # Show progress during OCR
│  │  ├─ ExportModal.tsx  # TXT/PDF export options
│  │  └─ ConfirmDialog.tsx # Delete/logout confirmation
│  │
│  ├─ hooks/
│  │  ├─ useAuth.ts       # Login/logout/register logic
│  │  ├─ useOCR.ts        # Upload, poll, fetch result
│  │  └─ useDarkMode.ts   # Dark mode state
│  │
│  ├─ services/
│  │  ├─ api.ts           # Axios client with JWT interceptor
│  │  ├─ auth.ts          # /auth/* endpoints
│  │  ├─ ocr.ts           # /ocr/* endpoints
│  │  ├─ user.ts          # /user/* endpoints
│  │  └─ contact.ts       # /contact endpoint
│  │
│  ├─ utils/
│  │  ├─ validation.ts    # Email, image validation
│  │  ├─ formatting.ts    # Date formatting, text truncate
│  │  └─ storage.ts       # localStorage token helpers
│  │
│  ├─ styles/
│  │  ├─ globals.css      # Tailwind + global styles
│  │  └─ theme.css        # Dark mode variables
│  │
│  └─ types/
│     └─ index.ts         # TypeScript interfaces
│
├─ .env.production        # API_URL for prod
├─ .env.local            # API_URL for dev
└─ package.json
```

---

## 5. DATA MODEL

### 5.1 Database Schema

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP NULL  -- GDPR soft delete
);

-- OCRs table
CREATE TABLE ocrs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Image storage
  image_url VARCHAR(500) NOT NULL,  -- Cloudinary URL
  image_metadata JSONB,  -- {width, height, format, size_bytes}

  -- OCR results
  ocr_text TEXT NOT NULL,  -- Raw Tesseract output
  ocr_text_edited TEXT,    -- User-edited version
  processing_time_ms INTEGER,  -- Time to extract text
  status VARCHAR(20) NOT NULL,  -- 'processing', 'completed', 'error'
  error_message TEXT,      -- If status = 'error'
  progress INTEGER DEFAULT 0,  -- 0-100 during processing

  -- User notes
  user_notes TEXT,

  -- Timestamps
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP NULL  -- GDPR soft delete
);

-- Contact messages table
CREATE TABLE contact_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'new',  -- 'new', 'read', 'responded'
  created_at TIMESTAMP DEFAULT now()
);

-- Indices for performance
CREATE INDEX idx_ocrs_user_id ON ocrs(user_id);
CREATE INDEX idx_ocrs_created_at ON ocrs(created_at);
CREATE INDEX idx_ocrs_deleted_at ON ocrs(deleted_at);
CREATE INDEX idx_users_email ON users(email);
```

### 5.2 API Request/Response Examples

#### Register
```json
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 201:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

#### Upload Image
```json
POST /ocr/upload (multipart/form-data)
{
  "file": <binary>,
  "user_notes": "Contract page 1"  // optional
}

Response 202:
{
  "ocr_id": "uuid",
  "status": "processing",
  "cloudinary_url": "https://res.cloudinary.com/...",
  "progress": 0
}
```

#### Poll Status
```json
GET /ocr/{ocr_id}/status

Response 200:
{
  "status": "processing",  // or "completed", "error"
  "progress": 45
}
```

#### Get Result
```json
GET /ocr/{ocr_id}/result

Response 200:
{
  "id": "uuid",
  "ocr_text": "Extracted text...",
  "ocr_text_edited": null,
  "processing_time_ms": 8500,
  "image_metadata": {
    "width": 1920,
    "height": 1080,
    "format": "jpeg",
    "size_bytes": 450000
  },
  "user_notes": "Contract page 1",
  "created_at": "2026-03-23T10:30:00Z"
}
```

#### Export to TXT
```
GET /ocr/{ocr_id}/export/txt

Response 200 (file download):
Content-Type: text/plain
Content-Disposition: attachment; filename="ocr_uuid.txt"

Extracted text with user edits (if any)...
```

#### List OCRs
```json
GET /ocr/list?limit=20&offset=0&search=contract

Response 200:
{
  "total": 45,
  "items": [
    {
      "id": "uuid",
      "text_preview": "Extracted text preview...",
      "user_notes": "Contract page 1",
      "created_at": "2026-03-23T10:30:00Z"
    }
  ]
}
```

---

## 6. AUTHENTICATION & SECURITY

### 6.1 JWT Flow

```
1. User registers → password hashed with bcrypt → create user in DB
2. User logs in → verify email/password → generate JWT
3. JWT tokens (in localStorage):
   - Access token: 15 minutes validity
   - Refresh token: 7 days validity (stored in DB)
4. Frontend sends: Authorization: Bearer <access_token>
5. Backend validates JWT on every protected request
6. If access token expired, use refresh token to get new access token
7. On logout, invalidate refresh token in DB
```

### 6.2 CORS Configuration

```python
# Allow requests from:
origins = [
    "https://yourdomain.vercel.app",  # Production frontend
    "http://localhost:3000",           # Development frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

### 6.3 Rate Limiting

```
Global: 100 requests/minute per IP
Public endpoints (/auth/register, /contact): 10 requests/minute per IP
OCR upload (/ocr/upload): 5 requests/minute per IP

Response on limit exceeded:
429 Too Many Requests
{
  "error": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

### 6.4 Input Validation

```
Email: RFC 5322 standard validation
Password: minimum 8 characters
Image: MIME type check (image/jpeg, image/png), max 5MB
OCR text: sanitize to prevent XSS if displayed elsewhere
```

### 6.5 Error Responses

```json
400 Bad Request:
{ "error": "Email format invalid", "code": "INVALID_EMAIL" }

401 Unauthorized:
{ "error": "JWT token expired", "code": "TOKEN_EXPIRED" }

403 Forbidden:
{ "error": "You don't have access to this OCR", "code": "ACCESS_DENIED" }

404 Not Found:
{ "error": "OCR not found", "code": "NOT_FOUND" }

409 Conflict:
{ "error": "Email already registered", "code": "EMAIL_EXISTS" }

413 Payload Too Large:
{ "error": "Image exceeds 5MB limit", "code": "FILE_TOO_LARGE" }

500 Internal Server Error:
{ "error": "Tesseract processing failed", "code": "PROCESSING_ERROR" }
```

---

## 7. OCR PROCESSING FLOW

### 7.1 Async Processing with Polling

```
1. Frontend POST /ocr/upload → Backend creates OCR record with status='processing'
2. Backend saves image to Cloudinary (sync)
3. Backend starts Tesseract in background thread
4. Response 202 Accepted: { ocr_id, status: 'processing' }

5. Frontend polls GET /ocr/{ocr_id}/status every 2 seconds
6. Backend returns current status and progress (0-100)
7. Frontend shows spinner with progress

8. Tesseract completes → Backend updates OCR record:
   - status = 'completed'
   - ocr_text = extracted text
   - processing_time_ms = elapsed time

9. Frontend detects status='completed' → GET /ocr/{ocr_id}/result
10. Frontend displays text in editor, metadata, export options
11. User can edit text (PUT /ocr/{ocr_id}) and export
```

### 7.2 Image Validation

```
1. MIME type check: only image/jpeg, image/png
2. File size check: max 5MB
3. Dimension check: width >= 200px, height >= 200px (minimum readability)
4. Manuscript detection:
   - Use OpenCV to detect text-like patterns
   - If appears handwritten, show warning: "This appears handwritten. OCR may not work well."
   - Allow user to proceed anyway
5. Pre-process image before Tesseract:
   - Grayscale conversion
   - Contrast enhancement
   - Noise reduction
```

### 7.3 Tesseract + opencv_mg10 Integration

```
Pipeline:
1. Load image with OpenCV
2. Apply layout detection (opencv_mg10 method)
3. Extract regions of interest (text areas)
4. For each region: enhance contrast, threshold, denoise
5. Pass to Tesseract with config:
   - --psm 6 (assume single uniform block of text)
   - --oem 3 (use both legacy and LSTM)
   - Language: eng (English)
6. Post-process Tesseract output:
   - Remove extra whitespace
   - Correct common OCR mistakes (optional)
7. Store result with metadata
```

---

## 8. FRONTEND FEATURES

### 8.1 Pages Overview

| Page | Authentication | Purpose |
|------|---|---|
| Landing | Public | Hero, features, FAQ, CTA to register |
| Register | Public | Email/password registration form |
| Login | Public | Email/password login form |
| OCR | Protected | Upload image, view/edit result, export |
| History | Protected | List all OCRs, search, download, delete |
| Profile | Protected | Account settings, GDPR export/delete, dark mode |
| Contact | Public | Send message to admin |
| Privacy | Public | Privacy policy |
| Terms | Public | Terms of service |

### 8.2 OCR Page Features

```
1. Upload section:
   - Drag-and-drop or click to select image
   - Preview of selected image
   - File size display
   - Format validation (JPG/PNG only)

2. Processing:
   - Show spinner with "Processing... 35%"
   - Poll status every 2 seconds
   - Estimated time remaining (if available)

3. Results:
   - Display extracted text in textarea
   - Highlight user-edited portions (optional)
   - Metadata panel: dimensions, file size, processing time
   - Warning: "Text may be out of order. Please review."
   - User notes section (textarea)

4. Actions:
   - Copy text to clipboard (button)
   - Save edits (auto-save on blur)
   - Export to TXT (download)
   - Export to PDF (download with image + text + metadata)
   - Save notes (auto-save)
   - Back to upload (start new OCR)
```

### 8.3 History Page Features

```
1. List:
   - Show all OCRs in reverse chronological order
   - Text preview (first 150 chars)
   - User notes
   - Date created
   - Processing time

2. Search:
   - Filter by text content (ocr_text or user_notes)
   - Real-time search as user types
   - Show match count

3. Actions per OCR:
   - View full result
   - Download original image
   - Download as TXT/PDF
   - Edit notes
   - Delete (soft delete)

4. Pagination:
   - Show 20 items per page
   - Load more / next/previous buttons
```

### 8.4 Profile Page Features

```
1. Account Info:
   - Email (read-only)
   - Account created date
   - Total OCRs count

2. Settings:
   - Change password (optional for v1)
   - Dark mode toggle (persisted to localStorage)
   - Language selection (Spanish only for now)

3. GDPR Compliance:
   - "Download my data" button
     → Generates ZIP with all OCRs, images, metadata
     → Auto-downloads
   - "Delete my account" button
     → Shows warning: "This cannot be undone"
     → Requires password confirmation
     → Deletes all user data
     → Redirects to landing page

4. Logout:
   - Logout button
   - Clears localStorage tokens
   - Redirects to landing page
```

### 8.5 Landing Page Sections

```
1. Hero Section:
   - Bold title: "OCR for Printed Documents"
   - Subtitle: "Extract text from digital images and scanned documents"
   - CTA: "Get Started" button → /register
   - Hero image/screenshot

2. Features Section:
   - "High Accuracy" (91%+ accuracy with Tesseract)
   - "Fast Processing" (~5-10 seconds per image)
   - "Live Editor" (edit extracted text directly)
   - "Export Options" (TXT and PDF formats)
   - "Full History" (access all your OCRs anytime)
   - "Completely Private" (your images are only visible to you)

3. FAQ Section:
   - "What document types are supported?"
     → Answer: Printed/scanned documents, not handwritten
   - "What's the maximum image size?"
     → Answer: 5MB
   - "Are my images private?"
     → Answer: Yes, completely. Only you can see them.
   - "How do I edit the extracted text?"
     → Answer: Click the text area and edit directly in the browser.
   - "Can I download my data?"
     → Answer: Yes, anytime from your profile (GDPR compliant).

4. Footer:
   - Links: About | Contact | Privacy Policy | Terms of Service
   - Social media links (if any)
   - Copyright notice
```

---

## 9. DEPLOYMENT & INFRASTRUCTURE

### 9.1 Environment Variables

**Backend (.env.production):**
```
# Database
DATABASE_URL=postgresql://user:password@neon.tech/database_name

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# SendGrid
SENDGRID_API_KEY=your-sendgrid-key
ADMIN_EMAIL=ampr2003@gmail.com

# JWT
JWT_SECRET=your-super-secret-random-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend
FRONTEND_URL=https://yourdomain.vercel.app

# Tesseract
TESSERACT_PATH=/usr/bin/tesseract

# Logging
LOG_LEVEL=INFO
```

**Frontend (.env.production):**
```
REACT_APP_API_URL=https://your-backend.hf.space
```

### 9.2 Backend Dependencies (requirements.txt)

```
fastapi==0.104.0
uvicorn==0.24.0
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
python-multipart==0.0.6
pyjwt==2.8.1
cloudinary==1.36.0
sendgrid==6.10.0
pillow==10.0.0
opencv-python==4.8.0.76
pytesseract==0.3.10
python-dotenv==1.0.0
sqlalchemy==2.0.21
alembic==1.12.0
pydantic==2.4.2
bcrypt==4.1.0
```

### 9.3 Frontend Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "axios": "^1.5.0",
    "tailwindcss": "^3.3.0",
    "react-markdown": "^8.0.7",
    "jspdf": "^2.5.1",
    "html2pdf.js": "^0.10.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0"
  }
}
```

### 9.4 Docker Configuration (for HF Spaces)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run database migrations
RUN python -m alembic upgrade head

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 9.5 Keep-Alive Strategy

```
Problem: HF Spaces suspends inactive apps after 48 hours
Solution: Cron job to call /health endpoint every 5 minutes

Setup:
1. Use cron.jobs service (free)
2. Configure job: GET https://your-backend.hf.space/health
3. Run every 5 minutes
4. Backend /health returns: { status: 'healthy', uptime_seconds: X }
5. No auth required (public endpoint)
```

---

## 10. TESTING STRATEGY

### 10.1 Unit Tests

```
Backend:
├─ auth/test_service.py       # JWT generation, password hashing
├─ ocr/test_service.py        # Tesseract integration, image validation
├─ user/test_gdpr.py          # GDPR export, account deletion
└─ utils/test_validators.py   # Email, image validation

Frontend:
├─ hooks/test_useAuth.ts      # Login/logout logic
├─ hooks/test_useOCR.ts       # Upload, polling logic
├─ services/test_api.ts       # API client, JWT interceptor
└─ utils/test_validation.ts   # Email, image validation
```

### 10.2 Integration Tests

```
Backend:
├─ Full flow: register → login → upload → process → export → delete
├─ GDPR: export data → verify ZIP contents → delete account
└─ Error cases: invalid auth, file too large, concurrent uploads

Frontend:
├─ Full flow: register → upload → editor → export
├─ Dark mode toggle persistence
└─ Error handling: network errors, validation errors
```

### 10.3 Manual Testing Checklist

```
Before production launch:
☐ Register new account → verify email works (optional)
☐ Login → verify JWT stored correctly
☐ Upload image (JPG/PNG) → verify async processing
☐ Poll status → verify progress updates
☐ View result → verify text displayed correctly
☐ Edit text → verify changes saved
☐ Export TXT → verify file downloads
☐ Export PDF → verify image + text + metadata
☐ Search history → verify filtering works
☐ Download original image → verify from Cloudinary
☐ Delete OCR → verify soft delete
☐ Dark mode toggle → verify persistence
☐ GDPR export → verify ZIP contains all data
☐ Delete account → verify all user data removed
☐ /health endpoint → verify response
☐ Test on mobile → responsive design
☐ CORS testing → requests from different origins
```

---

## 11. DEPLOYMENT CHECKLIST

```
Before Launch:
☐ Create PostgreSQL database on Neon
☐ Create Cloudinary account + get API credentials
☐ Create SendGrid account + get API key
☐ Generate JWT_SECRET (use `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
☐ Create HF Spaces project
☐ Create Vercel project + connect GitHub repo
☐ Set environment variables on HF Spaces
☐ Set environment variables on Vercel
☐ Build + test backend locally
☐ Build + test frontend locally
☐ Deploy backend to HF Spaces
☐ Deploy frontend to Vercel
☐ Test full flow in production
☐ Set up Cron job for /health endpoint
☐ Monitor logs for errors
☐ Create monitoring dashboard (optional)
```

---

## 12. FUTURE ENHANCEMENTS

```
v2 Features (out of scope for v1):
- Multi-language OCR (Spanish, French, German, etc.)
- GPU-accelerated option (upgrade to Paddle or Deepseek)
- Batch OCR (process multiple images at once)
- OCR result API (let other apps consume results)
- Collaboration (share OCRs with other users)
- Premium subscription (higher limits, faster processing)
- Mobile app (React Native)
- Document type detection (invoice, contract, etc.)
- Auto-correction (ML model to fix common OCR mistakes)
- Team workspaces
```

---

## 13. ROLLBACK PLAN

```
If something goes wrong in production:

1. Frontend Issue:
   - Revert to previous commit on GitHub
   - Vercel auto-redeploys
   - No data loss

2. Backend Issue:
   - Revert to previous Docker image on HF Spaces
   - Database backups available on Neon (automatic)
   - Restart space

3. Database Issue:
   - Neon provides automatic backups
   - Can restore from point-in-time
   - Contact Neon support

4. Cloudinary Issue:
   - Images cached on CDN
   - Full backup in Cloudinary buckets
   - Re-upload if needed

5. Full Rollback:
   - Downtime: <5 minutes
   - Restore from database backup
   - Re-deploy previous version
   - Verify /health endpoint
```

---

## 14. SUCCESS METRICS

Track these KPIs after launch:

```
Performance:
- OCR processing time (target: <15s on HF Spaces)
- API response time (target: <2s for non-OCR requests)
- Frontend page load time (target: <3s)
- Uptime (target: 99%+)

Usage:
- Active users per day
- OCRs processed per day
- Average OCRs per user
- Return user rate

Quality:
- User satisfaction (feedback form rating)
- Error rate (target: <1%)
- Support tickets per 1000 users
- Feature requests (for future versions)
```

---

## 15. APPROVAL

**Design Status:** ✅ APPROVED

**Next Step:** Write implementation plan (superpowers:writing-plans skill)

---

**Document Version:** 1.0
**Last Updated:** March 23, 2026
**Author:** Claude Code
